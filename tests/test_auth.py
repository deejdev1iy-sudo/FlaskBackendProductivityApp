from app.models import User


def test_signup_creates_user_and_hides_password(client):
    resp = client.post("/api/auth/signup", json={"username": "Carol", "password": "password123"})
    assert resp.status_code == 201
    user = resp.get_json()["user"]
    assert user["username"] == "carol"  # normalised to lowercase
    assert "password" not in user and "password_hash" not in user


def test_signup_rejects_duplicate_username_case_insensitively(client):
    client.post("/api/auth/signup", json={"username": "alice", "password": "password123"})
    resp = client.post("/api/auth/signup", json={"username": "ALICE", "password": "password123"})
    assert resp.status_code == 409


def test_signup_validation_errors(client):
    short_pw = client.post("/api/auth/signup", json={"username": "dave", "password": "short"})
    bad_name = client.post("/api/auth/signup", json={"username": "da ve!", "password": "password123"})
    assert short_pw.status_code == 422
    assert bad_name.status_code == 422


def test_signup_requires_json(client):
    resp = client.post("/api/auth/signup", data="username=x", content_type="text/plain")
    assert resp.status_code == 415


def test_password_is_hashed_in_database(app, client):
    client.post("/api/auth/signup", json={"username": "erin", "password": "password123"})
    user = User.query.filter_by(username="erin").one()
    assert user.password_hash != "password123"
    assert user.password_hash.startswith("$2")  # bcrypt
    assert user.check_password("password123")
    assert not user.check_password("wrong-password")


def test_login_success_sets_session(client):
    client.post("/api/auth/signup", json={"username": "alice", "password": "password123"})
    resp = client.post("/api/auth/login", json={"username": "alice", "password": "password123"})
    assert resp.status_code == 200
    assert resp.get_json()["user"]["username"] == "alice"


def test_login_failures_return_401_with_same_message(client):
    client.post("/api/auth/signup", json={"username": "alice", "password": "password123"})
    wrong_pw = client.post("/api/auth/login", json={"username": "alice", "password": "nope-nope"})
    no_user = client.post("/api/auth/login", json={"username": "ghost", "password": "password123"})
    assert wrong_pw.status_code == 401
    assert no_user.status_code == 401
    assert wrong_pw.get_json() == no_user.get_json()


def test_session_check_before_and_after_login(client):
    assert client.get("/api/auth/session").status_code == 401
    client.post("/api/auth/signup", json={"username": "alice", "password": "password123"})
    client.post("/api/auth/login", json={"username": "alice", "password": "password123"})
    resp = client.get("/api/auth/session")
    assert resp.status_code == 200
    assert resp.get_json()["authenticated"] is True


def test_user_stays_logged_in_across_refreshes(client):
    client.post("/api/auth/signup", json={"username": "alice", "password": "password123"})
    client.post("/api/auth/login", json={"username": "alice", "password": "password123"})
    for _ in range(3):  # simulate page refreshes
        assert client.get("/api/auth/session").status_code == 200
        assert client.get("/api/tasks").status_code == 200


def test_logout_ends_session(client):
    client.post("/api/auth/signup", json={"username": "alice", "password": "password123"})
    client.post("/api/auth/login", json={"username": "alice", "password": "password123"})
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/session").status_code == 401
    assert client.get("/api/tasks").status_code == 401


def test_logout_without_session_is_unauthorized(client):
    assert client.post("/api/auth/logout").status_code == 401

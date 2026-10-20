from app import db
from app.models import Task


def _create(client, **overrides):
    body = {"title": "Write report", "priority": "high"}
    body.update(overrides)
    return client.post("/api/tasks", json=body)


def test_protected_routes_require_login(client):
    assert client.get("/api/tasks").status_code == 401
    assert client.post("/api/tasks", json={"title": "x"}).status_code == 401
    assert client.get("/api/tasks/1").status_code == 401
    assert client.put("/api/tasks/1", json={"title": "x"}).status_code == 401
    assert client.patch("/api/tasks/1", json={"title": "x"}).status_code == 401
    assert client.delete("/api/tasks/1").status_code == 401


def test_create_and_read_task_with_custom_fields(alice_client):
    resp = _create(alice_client, due_date="2026-11-01", description="Q4 numbers")
    assert resp.status_code == 201
    task = resp.get_json()
    assert task["priority"] == "high"
    assert task["due_date"] == "2026-11-01"
    assert task["completed"] is False

    got = alice_client.get(f"/api/tasks/{task['id']}")
    assert got.status_code == 200
    assert got.get_json()["title"] == "Write report"


def test_create_validation(alice_client):
    assert alice_client.post("/api/tasks", json={}).status_code == 422
    assert _create(alice_client, priority="urgent").status_code == 422
    assert _create(alice_client, title="   ").status_code == 422


def test_non_json_body_rejected(alice_client):
    resp = alice_client.post("/api/tasks", data="title=x", content_type="text/plain")
    assert resp.status_code == 415


def test_pagination(alice_client):
    for i in range(25):
        _create(alice_client, title=f"Task {i}")
    page1 = alice_client.get("/api/tasks?page=1&per_page=10").get_json()
    page3 = alice_client.get("/api/tasks?page=3&per_page=10").get_json()
    assert len(page1["items"]) == 10
    assert page1["total"] == 25 and page1["pages"] == 3
    assert page1["has_next"] is True and page1["has_prev"] is False
    assert len(page3["items"]) == 5
    assert page3["has_next"] is False and page3["has_prev"] is True


def test_per_page_is_capped_and_bad_params_rejected(alice_client):
    body = alice_client.get("/api/tasks?per_page=5000").get_json()
    assert body["per_page"] == 100
    assert alice_client.get("/api/tasks?page=abc").status_code == 400
    assert alice_client.get("/api/tasks?page=0").status_code == 400


def test_completed_filter(alice_client):
    _create(alice_client, title="Done", completed=True)
    _create(alice_client, title="Open", completed=False)
    done = alice_client.get("/api/tasks?completed=true").get_json()["items"]
    assert [t["title"] for t in done] == ["Done"]
    assert alice_client.get("/api/tasks?completed=maybe").status_code == 400


def test_put_and_patch_update_task(alice_client):
    task_id = _create(alice_client).get_json()["id"]
    patched = alice_client.patch(f"/api/tasks/{task_id}", json={"completed": True})
    assert patched.status_code == 200
    assert patched.get_json()["completed"] is True
    assert patched.get_json()["priority"] == "high"  # untouched field preserved

    put = alice_client.put(f"/api/tasks/{task_id}", json={"title": "Renamed"})
    assert put.status_code == 200
    assert put.get_json()["title"] == "Renamed"


def test_delete_task(alice_client):
    task_id = _create(alice_client).get_json()["id"]
    assert alice_client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert alice_client.get(f"/api/tasks/{task_id}").status_code == 404


def test_missing_task_returns_404(alice_client):
    assert alice_client.get("/api/tasks/9999").status_code == 404


def test_users_cannot_see_each_others_tasks(alice_client, bob_client):
    task_id = _create(alice_client).get_json()["id"]

    assert bob_client.get("/api/tasks").get_json()["total"] == 0
    assert bob_client.get(f"/api/tasks/{task_id}").status_code == 404


def test_users_cannot_edit_or_delete_each_others_tasks(app, alice_client, bob_client):
    task_id = _create(alice_client).get_json()["id"]

    assert bob_client.patch(f"/api/tasks/{task_id}", json={"title": "hacked"}).status_code == 404
    assert bob_client.put(f"/api/tasks/{task_id}", json={"title": "hacked"}).status_code == 404
    assert bob_client.delete(f"/api/tasks/{task_id}").status_code == 404

    # Alice's task is untouched
    task = db.session.get(Task, task_id)
    assert task is not None and task.title == "Write report"


def test_client_cannot_reassign_task_owner(alice_client, bob_client):
    resp = _create(alice_client, user_id=2)  # bob's id
    assert resp.status_code == 201
    assert bob_client.get("/api/tasks").get_json()["total"] == 0
    assert alice_client.get("/api/tasks").get_json()["total"] == 1

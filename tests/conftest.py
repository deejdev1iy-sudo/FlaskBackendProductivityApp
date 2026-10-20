import pytest

from app import create_app, db
from config import TestingConfig


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """An anonymous client (its own cookie jar)."""
    return app.test_client()


def _signup_and_login(client, username, password="password123"):
    resp = client.post("/api/auth/signup", json={"username": username, "password": password})
    assert resp.status_code == 201, resp.get_json()
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.get_json()
    return client


@pytest.fixture
def alice_client(app):
    return _signup_and_login(app.test_client(), "alice")


@pytest.fixture
def bob_client(app):
    return _signup_and_login(app.test_client(), "bob")

import os
import secrets
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


class Config:
    # Signs the session cookie. Set SECRET_KEY in production so sessions survive restarts.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "productivity.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session cookie hardening
    SESSION_COOKIE_NAME = "session"
    SESSION_COOKIE_HTTPONLY = True   # JavaScript cannot read the cookie
    SESSION_COOKIE_SAMESITE = "Lax"  # blocks most cross-site request forgery
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)  # enable under HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.environ.get("SESSION_HOURS", "12")))

    # Front-end origins allowed to call the API with cookies
    CORS_ORIGINS = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
        if o.strip()
    ]

    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SESSION_COOKIE_SECURE = False

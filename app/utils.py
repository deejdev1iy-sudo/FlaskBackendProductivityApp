from functools import wraps

from flask import g, request, session

from app import db
from app.models import User


def get_json_body():
    """Return (data, None) for a JSON object body, or (None, error_response).

    Requiring application/json also protects cookie sessions from cross-site
    form submissions: browsers cannot send JSON cross-site without a CORS
    preflight, which this API only approves for configured front-end origins.
    """
    if not request.is_json:
        return None, ({"error": "Content-Type must be application/json"}, 415)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, ({"error": "Request body must be a JSON object"}, 400)
    return data, None


def load_current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    user = db.session.get(User, user_id)
    if user is None:  # account was removed while the session was still alive
        session.clear()
    return user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = load_current_user()
        if user is None:
            return {"error": "Authentication required"}, 401
        g.current_user = user
        return view(*args, **kwargs)

    return wrapper

from flask import Blueprint, session
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import User
from app.schemas import LoginSchema, SignupSchema
from app.utils import get_json_body, load_current_user, login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/signup")
def signup():
    data, error = get_json_body()
    if error:
        return error
    try:
        payload = SignupSchema().load(data)
    except ValidationError as err:
        return {"errors": err.messages}, 422

    username = payload["username"]
    if User.query.filter_by(username=username).first():
        return {"error": "Username is already taken"}, 409

    user = User(username=username)
    user.set_password(payload["password"])
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:  # two signups racing for the same username
        db.session.rollback()
        return {"error": "Username is already taken"}, 409

    return {"message": "Account created", "user": _user_dict(user)}, 201


@auth_bp.post("/login")
def login():
    data, error = get_json_body()
    if error:
        return error
    try:
        payload = LoginSchema().load(data)
    except ValidationError as err:
        return {"errors": err.messages}, 422

    user = User.query.filter_by(username=payload["username"]).first()
    # Same message for unknown user and wrong password, so usernames can't be enumerated
    if user is None or not user.check_password(payload["password"]):
        return {"error": "Invalid username or password"}, 401

    # Clearing first prevents session fixation: a fresh cookie is issued on login
    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return {"message": "Logged in", "user": _user_dict(user)}, 200


@auth_bp.post("/logout")
@login_required
def logout():
    session.clear()
    return {"message": "Logged out"}, 200


@auth_bp.get("/session")
def check_session():
    """Front-end calls this on page load to restore login state after a refresh."""
    user = load_current_user()
    if user is None:
        return {"authenticated": False, "error": "No active session"}, 401
    return {"authenticated": True, "user": _user_dict(user)}, 200


def _user_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat(),
    }

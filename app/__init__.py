from flask import Flask, request
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()


def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object(config_class or Config)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # Import models so Flask-Migrate can detect them
    from app import models  # noqa: F401
    from app.auth import auth_bp
    from app.resources import TaskListResource, TaskResource

    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    api = Api(app, prefix="/api")
    api.add_resource(TaskListResource, "/tasks")
    api.add_resource(TaskResource, "/tasks/<int:task_id>")

    register_cors(app)
    register_error_handlers(app)
    return app


def register_error_handlers(app):
    """Keep error responses JSON for API clients."""
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(404)
    def not_found(_err):
        return {"error": "Resource not found"}, 404

    @app.errorhandler(405)
    def method_not_allowed(_err):
        return {"error": "Method not allowed"}, 405

    @app.errorhandler(500)
    def server_error(_err):
        return {"error": "Internal server error"}, 500



def register_cors(app):
    """Allow only configured front-end origins to call the API with credentials."""

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin and origin in app.config["CORS_ORIGINS"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers.add("Vary", "Origin")
        return response

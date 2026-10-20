from flask import current_app, g, request
from flask_restful import Resource
from marshmallow import ValidationError

from app import db
from app.models import Task
from app.schemas import TaskSchema
from app.utils import get_json_body, login_required

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)


def _owned_task(task_id):
    """Return the task only if the logged-in user owns it.

    Other users' tasks are reported as not found (404) rather than forbidden,
    so the API doesn't reveal which task IDs exist.
    """
    return Task.query.filter_by(id=task_id, user_id=g.current_user.id).first()


class TaskListResource(Resource):
    method_decorators = [login_required]

    def get(self):
        try:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", current_app.config["DEFAULT_PAGE_SIZE"]))
        except ValueError:
            return {"error": "page and per_page must be integers"}, 400
        if page < 1 or per_page < 1:
            return {"error": "page and per_page must be positive"}, 400
        per_page = min(per_page, current_app.config["MAX_PAGE_SIZE"])

        query = Task.query.filter_by(user_id=g.current_user.id)
        completed = request.args.get("completed")
        if completed is not None:
            if completed.lower() not in ("true", "false"):
                return {"error": "completed must be 'true' or 'false'"}, 400
            query = query.filter_by(completed=(completed.lower() == "true"))

        pagination = (
            query.order_by(Task.created_at.desc(), Task.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return {
            "items": tasks_schema.dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }, 200

    def post(self):
        data, error = get_json_body()
        if error:
            return error
        try:
            payload = task_schema.load(data)
        except ValidationError as err:
            return {"errors": err.messages}, 422

        task = Task(user_id=g.current_user.id, **payload)
        db.session.add(task)
        db.session.commit()
        return task_schema.dump(task), 201


class TaskResource(Resource):
    method_decorators = [login_required]

    def get(self, task_id):
        task = _owned_task(task_id)
        if task is None:
            return {"error": "Task not found"}, 404
        return task_schema.dump(task), 200

    def put(self, task_id):
        return self._update(task_id, partial=False)

    def patch(self, task_id):
        return self._update(task_id, partial=True)

    def _update(self, task_id, partial):
        task = _owned_task(task_id)
        if task is None:
            return {"error": "Task not found"}, 404
        data, error = get_json_body()
        if error:
            return error
        try:
            payload = TaskSchema(partial=partial).load(data)
        except ValidationError as err:
            return {"errors": err.messages}, 422

        for field, value in payload.items():
            setattr(task, field, value)
        db.session.commit()
        return task_schema.dump(task), 200

    def delete(self, task_id):
        task = _owned_task(task_id)
        if task is None:
            return {"error": "Task not found"}, 404
        db.session.delete(task)
        db.session.commit()
        return "", 204

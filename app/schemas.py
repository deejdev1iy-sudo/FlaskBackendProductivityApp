from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

PRIORITIES = ("low", "medium", "high")
USERNAME_RULE = validate.Regexp(r"^[A-Za-z0-9_]+$", error="Use letters, numbers and underscores only")


class SignupSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    username = fields.Str(required=True, validate=[validate.Length(min=3, max=80), USERNAME_RULE])
    password = fields.Str(
        required=True, load_only=True, validate=validate.Length(min=8, max=72)
    )

    @pre_load
    def normalize_username(self, data, **kwargs):
        if isinstance(data.get("username"), str):
            data = {**data, "username": data["username"].strip().lower()}
        return data


class LoginSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

    @pre_load
    def normalize_username(self, data, **kwargs):
        if isinstance(data.get("username"), str):
            data = {**data, "username": data["username"].strip().lower()}
        return data


class TaskSchema(Schema):
    class Meta:
        # Unknown keys (including user_id) are dropped, so a client can never
        # assign a task to another user.
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    title = fields.Str(
        required=True,
        validate=[validate.Length(min=1, max=120), validate.Regexp(r"\S", error="Title cannot be blank")],
    )
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    priority = fields.Str(load_default="medium", validate=validate.OneOf(PRIORITIES))
    due_date = fields.Date(allow_none=True)
    completed = fields.Bool(load_default=False)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

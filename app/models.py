from datetime import datetime

from app import bcrypt, db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    tasks = db.relationship(
        "Task", back_populates="owner", cascade="all, delete-orphan", lazy="dynamic"
    )

    def set_password(self, password):
        """Store a bcrypt hash. The plaintext password is never saved."""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Task(db.Model):
    """A personal productivity item owned by exactly one user."""

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # Custom field 1
    priority = db.Column(db.String(10), nullable=False, default="medium")
    # Custom field 2
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    owner = db.relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.id} '{self.title}' user={self.user_id}>"

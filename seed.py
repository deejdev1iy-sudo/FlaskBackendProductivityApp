"""Populate the database with starter users and tasks.

Run after migrations:  python seed.py
Safe to run repeatedly: users that already exist are skipped.
"""
from faker import Faker

from app import create_app, db
from app.models import Task, User

DEMO_USERS = [("alice", "password123"), ("bob", "password123")]
TASKS_PER_USER = 5


def seed(app=None):
    app = app or create_app()
    Faker.seed(42)
    fake = Faker()
    summary = {"users": 0, "tasks": 0}

    with app.app_context():
        for username, password in DEMO_USERS:
            if User.query.filter_by(username=username).first():
                continue
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # assigns user.id
            summary["users"] += 1

            for _ in range(TASKS_PER_USER):
                db.session.add(
                    Task(
                        user_id=user.id,
                        title=fake.sentence(nb_words=4).rstrip("."),
                        description=fake.paragraph(nb_sentences=2),
                        priority=fake.random_element(["low", "medium", "high"]),
                        due_date=fake.future_date(end_date="+30d"),
                        completed=fake.boolean(chance_of_getting_true=30),
                    )
                )
                summary["tasks"] += 1

        db.session.commit()

    print(f"Seed complete: {summary['users']} users and {summary['tasks']} tasks created.")
    return summary


if __name__ == "__main__":
    seed()

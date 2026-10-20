# Productivity API

A secure Flask REST API backend for a personal productivity tool. Users sign up, log in with a password, and manage their own **tasks** (title, description, priority, due date, completed status). Session-based authentication keeps users logged in across page refreshes, and every task endpoint is restricted to the owner.

## Features

- **Authentication:** signup, login, logout, and a session-check endpoint for front-end refresh handling. Login uses an HTTP-only, SameSite session cookie.
- **Secure passwords:** bcrypt hashing via Flask-Bcrypt. Plaintext passwords are never stored or returned.
- **Unique usernames:** enforced by a unique database index. Usernames are case-insensitive.
- **User-owned resource:** tasks belong to one user. Each user sees only their own data.
- **CRUD and pagination:** create, read, update (PUT and PATCH), delete, with paginated, filterable listing.
- **Access control:** every task route requires login. Users cannot view, edit, or delete each other's tasks.
- **Consistent JSON errors** with correct status codes.

## Tech Stack

Flask 2.2.2, Flask-SQLAlchemy 3.0.3, Flask-Migrate 4.0.0, Flask-RESTful 0.3.9, Flask-Bcrypt 1.0.1, Marshmallow 3.20.1, Faker 15.3.2, Pytest 7.2.0. Python 3.12 (see Pipfile).

## Installation

Requires Python 3.12 and [pipenv](https://pipenv.pypa.io/).

```bash
pip install pipenv
cd flask-productivity-api
pipenv install --dev          # installs all pinned dependencies from Pipfile.lock
```

### Configuration (environment variables, all optional for local development)

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Signs session cookies. **Set this in production.** | random per process |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///productivity.db` |
| `SESSION_COOKIE_SECURE` | `1` to send cookies only over HTTPS | `0` |
| `SESSION_HOURS` | Session lifetime in hours | `12` |
| `CORS_ORIGINS` | Comma-separated front-end origins allowed to call the API | `http://localhost:3000,http://localhost:5173` |

### Migrating the database

The migration files are included in `migrations/`. Apply them to create the tables:

```bash
export FLASK_APP=run.py
pipenv run flask db upgrade
```

When you change `app/models.py` later, generate and apply a new migration:

```bash
pipenv run flask db migrate -m "describe the change"
pipenv run flask db upgrade
```

### Seeding the database

```bash
pipenv run python seed.py
```

This creates two demo accounts, each with five tasks:

| Username | Password |
|---|---|
| `alice` | `password123` |
| `bob` | `password123` |

Running the seed again is safe. Existing users are skipped.

## Running the API

```bash
pipenv run flask --app run run --port 5000
```

The API is served at `http://localhost:5000/api`.

## Running the Tests

```bash
pipenv run pytest -v
```

The suite uses an in-memory SQLite database, so it doesn't touch your data. It has 24 tests covering authentication, session persistence, password hashing, pagination, validation, and cross-user access control.

## Authentication Flow (for the front-end)

1. `POST /api/auth/signup` to create an account (no login is created automatically).
2. `POST /api/auth/login` to start a session. The server sets an HTTP-only `session` cookie.
3. On every page load or refresh, call `GET /api/auth/session`. A `200` means the user is still logged in. A `401` means they must log in again.
4. `POST /api/auth/logout` to end the session.

Every request from the front-end must send cookies. Use `credentials: "include"` with `fetch`, or `withCredentials: true` with Axios. Send JSON bodies with `Content-Type: application/json`.

```javascript
await fetch("http://localhost:5000/api/auth/login", {
  method: "POST",
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "alice", password: "password123" }),
});
```

## API Endpoints

All responses are JSON. Protected endpoints return `401` when there is no valid session.

### Authentication

| Method | Endpoint | Auth | Description | Status codes |
|---|---|---|---|---|
| POST | `/api/auth/signup` | No | Create a user account. Body: `username` (3–80 chars, letters, numbers, underscores), `password` (8–72 chars). | `201` created, `409` username taken, `422` validation error, `415` not JSON |
| POST | `/api/auth/login` | No | Log in and start a session. Body: `username`, `password`. | `200` success, `401` invalid credentials, `422` missing fields, `415` not JSON |
| POST | `/api/auth/logout` | Yes | End the current session. | `200` logged out, `401` not logged in |
| GET | `/api/auth/session` | No | Check whether the session is active. Returns the current user when logged in. Use this on page refresh. | `200` active, `401` no session |

### Tasks (user-owned resource)

| Method | Endpoint | Auth | Description | Status codes |
|---|---|---|---|---|
| GET | `/api/tasks` | Yes | List the current user's tasks, newest first, paginated. Query params: `page` (default 1), `per_page` (default 10, max 100), `completed` (`true` or `false`, optional). | `200` OK, `400` bad query params, `401` not logged in |
| POST | `/api/tasks` | Yes | Create a task. Body: `title` (required, up to 120 chars), `description`, `priority` (`low`, `medium`, `high`; default `medium`), `due_date` (`YYYY-MM-DD`), `completed` (bool). | `201` created, `401`, `415`, `422` |
| GET | `/api/tasks/<id>` | Yes | Get one of your tasks. | `200`, `401`, `404` not found or not yours |
| PUT | `/api/tasks/<id>` | Yes | Replace one of your tasks. `title` is required. | `200`, `401`, `404`, `415`, `422` |
| PATCH | `/api/tasks/<id>` | Yes | Partially update one of your tasks. Send only the fields to change. | `200`, `401`, `404`, `415`, `422` |
| DELETE | `/api/tasks/<id>` | Yes | Delete one of your tasks. | `204` deleted, `401`, `404` |

Pagination response for `GET /api/tasks`:

```json
{
  "items": [ { "id": 1, "title": "...", "priority": "medium", "due_date": "2026-11-01", "completed": false, "created_at": "...", "updated_at": "..." } ],
  "page": 1,
  "per_page": 10,
  "total": 25,
  "pages": 3,
  "has_next": true,
  "has_prev": false
}
```

### Access control

A task owned by another user returns `404 Not Found`, the same response as a task that doesn't exist. This is intentional. It stops users from discovering which IDs belong to other accounts. Protected routes return `401` when there is no session.

## Project Structure

```
flask-productivity-api/
├── app/
│   ├── __init__.py      # app factory, extensions, CORS, error handlers
│   ├── models.py        # User and Task models (bcrypt password helpers)
│   ├── schemas.py       # Marshmallow input validation and output shaping
│   ├── auth.py          # /api/auth blueprint: signup, login, logout, session
│   ├── resources.py     # Flask-RESTful task CRUD with ownership checks
│   └── utils.py         # login_required decorator, JSON body guard
├── migrations/          # Flask-Migrate (Alembic) migration scripts
├── tests/
│   ├── conftest.py      # fixtures: app, client, alice_client, bob_client
│   ├── test_auth.py     # authentication tests
│   └── test_tasks.py    # CRUD, pagination, and access-control tests
├── config.py
├── run.py               # entry point (flask --app run)
├── seed.py              # starter users and tasks
├── Pipfile
├── Pipfile.lock
└── README.md
```

## Security Notes

- Session cookies are HTTP-only and SameSite=Lax. Set `SESSION_COOKIE_SECURE=1` when serving over HTTPS.
- The session is cleared on login to prevent session fixation.
- JSON-only request bodies, combined with the CORS allow-list, block cross-site form submissions (CSRF).
- Login errors are generic, so usernames can't be enumerated.
- Mass assignment is blocked. The client cannot set `user_id`, and unknown fields are ignored.
- For production, also add rate limiting on `/api/auth/login` and serve the API behind HTTPS.

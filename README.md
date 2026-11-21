# Taskflow — Task Management Web Application

A lightweight task dashboard built with a vanilla HTML/CSS/JavaScript frontend and a Python Flask REST API. Tasks are stored in SQLite and remain available after restarting the backend.

## Architecture

```text
python-task-manager/
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── models.py
│   └── requirements.txt
└── tests/
    └── test_api.py
```

- `frontend/` contains the responsive dashboard and calls the API at `http://127.0.0.1:5000/api/tasks`.
- `backend/app.py` defines and validates the REST endpoints.
- `backend/database.py` creates and manages the SQLite database. By default, the database is written to the Flask instance directory as `tasks.sqlite3`.
- `backend/models.py` contains task data-access functions.
- `tests/test_api.py` exercises the API using an isolated temporary database.

## Requirements

- Python 3.9 or newer
- pip

## Installation

Run these commands from the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r backend\requirements.txt
```

If PowerShell prevents virtual-environment activation, run `py -m pip install -r backend\requirements.txt` directly instead.

## Start the backend

From the project root, run:

```powershell
py -m backend.app
```

The API listens on `http://127.0.0.1:5000`. The SQLite database and table are created automatically on startup.

## Launch the frontend

With the backend running, open `frontend\index.html` in a browser. The frontend calls the local API directly; no frontend build step or web server is required. Keep the backend running while using the dashboard.

## API

All request and response bodies use JSON. New tasks default to `status: "todo"` and an empty description. Valid statuses are `todo`, `in_progress`, and `done`. Titles are limited to 200 characters; descriptions are limited to 2,000 characters.

| Method | Endpoint | Description | Success |
| --- | --- | --- | --- |
| `GET` | `/api/tasks` | List tasks, newest first | `200` with a JSON array |
| `POST` | `/api/tasks` | Create a task (`title` required; `description` and `status` optional) | `201` with the created task |
| `PUT` | `/api/tasks/<id>` | Update one or more of `title`, `description`, and `status` | `200` with the updated task |
| `DELETE` | `/api/tasks/<id>` | Delete a task | `200` with a confirmation message |

Invalid input returns `400` with a JSON `error`. Updating or deleting an unknown task returns `404`. Database errors return `500` with a JSON error response.

Example:

```json
{
  "title": "Prepare project update",
  "description": "Collect the latest milestones",
  "status": "in_progress"
}
```

## Run tests

From the project root:

```powershell
py -m pytest
```

Tests use a temporary SQLite database and do not alter the local application database.

## Optional learner exercise: intentional-bug prompt

Keep the working application unchanged. To create a separate learner exercise, use the following as a separate Copilot prompt after generating the project:

> Introduce a small, deliberate set of bugs into this task-management application for learners to find and fix. Make the bugs realistic and distributed across the frontend and backend, but do not add security vulnerabilities, destructive behavior, or obscure failures. Keep the app runnable, do not reveal the bugs or their fixes in code comments or documentation, and do not alter the project requirements. Summarize the affected files and expected learner-facing symptoms separately, without changing unrelated code.

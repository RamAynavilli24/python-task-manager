"""Tests for the Taskflow REST API."""

import pytest

from backend.app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite3")})
    with app.test_client() as test_client:
        yield test_client


def test_get_tasks_starts_empty(client):
    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_and_retrieve_task(client):
    created = client.post(
        "/api/tasks",
        json={
            "title": "Plan launch",
            "description": "Prepare the checklist",
            "status": "in_progress",
        },
    )

    assert created.status_code == 201
    task = created.get_json()
    assert task["id"] == 1
    assert task["title"] == "Plan launch"
    assert task["description"] == "Prepare the checklist"
    assert task["status"] == "in_progress"
    assert task["created_at"]

    retrieved = client.get("/api/tasks")
    assert retrieved.status_code == 200
    assert retrieved.get_json() == [task]


def test_create_task_uses_defaults_and_trims_title(client):
    response = client.post("/api/tasks", json={"title": "  Write docs  "})

    assert response.status_code == 201
    assert response.get_json()["title"] == "Write docs"
    assert response.get_json()["description"] == ""
    assert response.get_json()["status"] == "todo"


def test_update_task_fields(client):
    task_id = client.post("/api/tasks", json={"title": "Draft"}).get_json()["id"]

    response = client.put(
        f"/api/tasks/{task_id}",
        json={"title": "Review draft", "status": "done"},
    )

    assert response.status_code == 200
    assert response.get_json()["title"] == "Review draft"
    assert response.get_json()["status"] == "done"
    assert response.get_json()["description"] == ""


def test_delete_task(client):
    task_id = client.post("/api/tasks", json={"title": "Remove me"}).get_json()["id"]

    response = client.delete(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    assert response.get_json()["message"] == "Task deleted successfully."
    assert client.get("/api/tasks").get_json() == []


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "Title is required."),
        ({"title": "   "}, "Title cannot be empty."),
        ({"title": 42}, "Title must be a string."),
        ({"title": "Valid", "status": "blocked"}, "Status must be one of: todo, in_progress, done."),
        ({"title": "Valid", "extra": True}, "Unknown field(s): extra."),
        ({"title": "x" * 201}, "Title cannot exceed 200 characters."),
    ],
)
def test_create_task_rejects_invalid_input(client, payload, message):
    response = client.post("/api/tasks", json=payload)

    assert response.status_code == 400
    assert response.get_json()["error"] == message


def test_update_rejects_invalid_input(client):
    response = client.put("/api/tasks/1", json={"status": "blocked"})

    assert response.status_code == 400
    assert "Status must be one of" in response.get_json()["error"]


def test_non_json_body_is_rejected(client):
    response = client.post(
        "/api/tasks",
        data="title=Task",
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Content-Type must be application/json."


@pytest.mark.parametrize("method", ["put", "delete"])
def test_missing_task_id_returns_404(client, method):
    response = getattr(client, method)("/api/tasks/999", json={}) if method == "put" else getattr(client, method)("/api/tasks/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Task not found."

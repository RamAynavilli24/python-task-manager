"""Flask REST API for the Taskflow application."""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Dict, Optional, Tuple

from flask import Flask, jsonify, request

from backend import models
from backend.database import get_db_connection, initialize_database


MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
ALLOWED_TASK_FIELDS = {"title", "description", "status"}


def _validate_payload(
    payload: object,
    *,
    creating: bool,
) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    unknown_fields = set(payload) - ALLOWED_TASK_FIELDS
    if unknown_fields:
        return None, f"Unknown field(s): {', '.join(sorted(unknown_fields))}."

    if creating and "title" not in payload:
        return None, "Title is required."
    if not creating and not payload:
        return None, "Provide at least one field to update."

    changes: Dict[str, str] = {}
    if "title" in payload:
        title = payload["title"]
        if not isinstance(title, str):
            return None, "Title must be a string."
        title = title.strip()
        if not title:
            return None, "Title cannot be empty."
        if len(title) > MAX_TITLE_LENGTH:
            return None, f"Title cannot exceed {MAX_TITLE_LENGTH} characters."
        changes["title"] = title

    if "description" in payload:
        description = payload["description"]
        if not isinstance(description, str):
            return None, "Description must be a string."
        if len(description) > MAX_DESCRIPTION_LENGTH:
            return None, (
                f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters."
            )
        changes["description"] = description.strip()

    if "status" in payload:
        status = payload["status"]
        if not isinstance(status, str) or status not in models.TASK_STATUSES:
            return None, "Status must be one of: todo, in_progress, done."
        changes["status"] = status

    if creating:
        changes.setdefault("description", "")
        changes.setdefault("status", "todo")
    return changes, None


def _read_json_payload() -> Tuple[Optional[object], Optional[str]]:
    if not request.is_json:
        return None, "Content-Type must be application/json."
    payload = request.get_json(silent=True)
    if payload is None:
        return None, "Request body must contain valid JSON."
    return payload, None


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, "tasks.sqlite3"),
        DATABASE_URI=False,
    )
    if test_config:
        app.config.update(test_config)

    database_path = app.config["DATABASE"]
    if database_path == ":memory:":
        database_path = f"file:task-manager-{id(app)}?mode=memory&cache=shared"
        app.config.update(DATABASE=database_path, DATABASE_URI=True)
        app.extensions["database_keeper"] = sqlite3.connect(
            database_path,
            uri=True,
        )
    else:
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    initialize_database()

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        return response

    @app.errorhandler(sqlite3.Error)
    def handle_database_error(error):
        app.logger.exception("Database operation failed: %s", error)
        return jsonify(error="A database error occurred."), 500

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify(error="The requested resource was not found."), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_error):
        return jsonify(error="The requested method is not allowed."), 405

    @app.get("/api/tasks")
    def list_tasks():
        with get_db_connection() as connection:
            return jsonify(models.list_tasks(connection)), 200

    @app.post("/api/tasks")
    def create_task():
        payload, error = _read_json_payload()
        if error:
            return jsonify(error=error), 400
        changes, error = _validate_payload(payload, creating=True)
        if error:
            return jsonify(error=error), 400

        with get_db_connection() as connection:
            task = models.create_task(
                connection,
                title=changes["title"],
                description=changes["description"],
                status=changes["status"],
            )
        return jsonify(task), 201

    @app.put("/api/tasks/<int:task_id>")
    def update_task(task_id: int):
        payload, error = _read_json_payload()
        if error:
            return jsonify(error=error), 400
        changes, error = _validate_payload(payload, creating=False)
        if error:
            return jsonify(error=error), 400

        with get_db_connection() as connection:
            task = models.update_task(connection, task_id, changes)
        if task is None:
            return jsonify(error="Task not found."), 404
        return jsonify(task), 200

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id: int):
        with get_db_connection() as connection:
            deleted = models.delete_task(connection, task_id)
        if not deleted:
            return jsonify(error="Task not found."), 404
        return jsonify(message="Task deleted successfully."), 200

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=False)

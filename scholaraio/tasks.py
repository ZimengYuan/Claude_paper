"""Task management module for async generation operations.

Stores task state in ``data/.tasks`` under the active ScholarAIO root.
The location can also be overridden with ``SCHOLARAIO_TASKS_DIR``.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

TaskStatus = Literal["pending", "running", "completed", "failed"]


def _resolve_tasks_dir() -> Path:
    """Resolve the active tasks directory.

    Resolution order:
    1. ``SCHOLARAIO_TASKS_DIR``
    2. sibling of ``SCHOLARAIO_CONFIG`` -> ``data/.tasks``
    3. nearest cwd ``config.yaml`` root -> ``data/.tasks``
    4. repository default ``data/.tasks``
    """
    env_dir = os.environ.get("SCHOLARAIO_TASKS_DIR")
    if env_dir:
        return Path(env_dir).expanduser()

    env_cfg = os.environ.get("SCHOLARAIO_CONFIG")
    if env_cfg:
        return Path(env_cfg).expanduser().resolve().parent / "data" / ".tasks"

    current = Path.cwd()
    for _ in range(6):
        if (current / "config.yaml").exists():
            return current / "data" / ".tasks"
        parent = current.parent
        if parent == current:
            break
        current = parent

    return Path(__file__).parent.parent / "data" / ".tasks"


def _ensure_tasks_dir() -> Path:
    """Ensure tasks directory exists."""
    tasks_dir = _resolve_tasks_dir()
    tasks_dir.mkdir(parents=True, exist_ok=True)
    return tasks_dir


def _task_path(task_id: str) -> Path:
    """Return path to task JSON file."""
    return _ensure_tasks_dir() / f"{task_id}.json"


def create_task(task_type: str, description: str = "", **metadata) -> dict:
    """Create a new task and return task info.

    Args:
        task_type: Type of task (e.g., 'generate', 'batch_generate')
        description: Human-readable description
        **metadata: Additional metadata to store

    Returns:
        Dict with task_id, status, created_at, etc.
    """
    task_id = str(uuid.uuid4())[:8]
    task = {
        "task_id": task_id,
        "type": task_type,
        "description": description,
        "status": "pending",
        "progress": 0,
        "total": 1,
        "completed": 0,
        "failed": 0,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "metadata": metadata,
    }
    _task_path(task_id).write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
    return task


def get_task(task_id: str) -> dict | None:
    """Get task by ID."""
    path = _task_path(task_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def update_task(
    task_id: str,
    status: TaskStatus | None = None,
    progress: int | None = None,
    total: int | None = None,
    completed: int | None = None,
    failed: int | None = None,
    error: str | None = None,
    **metadata,
) -> dict | None:
    """Update task fields."""
    task = get_task(task_id)
    if task is None:
        return None

    if status is not None:
        task["status"] = status
    if progress is not None:
        task["progress"] = progress
    if total is not None:
        task["total"] = total
    if completed is not None:
        task["completed"] = completed
    if failed is not None:
        task["failed"] = failed
    if error is not None:
        task["error"] = error
    if metadata:
        task["metadata"].update(metadata)

    task["updated_at"] = datetime.now().isoformat()
    _task_path(task_id).write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
    return task


def delete_task(task_id: str) -> bool:
    """Delete a task."""
    path = _task_path(task_id)
    if path.exists():
        path.unlink()
        return True
    return False


def list_tasks(status: TaskStatus | None = None, limit: int = 50) -> list[dict]:
    """List tasks, optionally filtered by status."""
    tasks_dir = _ensure_tasks_dir()
    tasks = []
    for path in sorted(tasks_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            task = json.loads(path.read_text(encoding="utf-8"))
            if status is None or task["status"] == status:
                tasks.append(task)
            if len(tasks) >= limit:
                break
        except (json.JSONDecodeError, OSError):
            continue
    return tasks

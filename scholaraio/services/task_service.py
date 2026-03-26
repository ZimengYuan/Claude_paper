from __future__ import annotations

from scholaraio.services.common import ServiceError
from scholaraio.tasks import get_task as _get_task


def get_task(task_id: str) -> dict:
    task = _get_task(task_id)
    if task is None:
        raise ServiceError("Task not found", status_code=404)
    return task

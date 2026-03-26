from __future__ import annotations

import argparse
import logging

from scholaraio.config import load_config
from scholaraio.generate import (
    generate_method,
    generate_rating,
    generate_reflection,
    generate_sensemaking,
    generate_summary,
    generate_user_notes,
)
from scholaraio.services.common import ServiceError, resolve_paper_dir
from scholaraio.services.generation_service import normalize_generation_types
from scholaraio.tasks import get_task, update_task

_log = logging.getLogger(__name__)

_GENERATORS = {
    "summary": generate_summary,
    "method": generate_method,
    "reflection": generate_reflection,
    "user_notes": generate_user_notes,
    "rating": generate_rating,
    "sensemaking": generate_sensemaking,
}


def _finish_task(task_id: str) -> None:
    task = get_task(task_id) or {}
    status = "failed" if task.get("completed", 0) == 0 and task.get("failed", 0) > 0 else "completed"
    update_task(task_id, status=status, progress=100)


def _run_generator(task_id: str, paper_dir, cfg, gen_type: str) -> None:
    fn = _GENERATORS.get(gen_type)
    if fn is None:
        raise ServiceError(f"Unsupported generation type: {gen_type}", status_code=400)
    fn(paper_dir, cfg, force=True)
    _log.debug("task %s generated %s for %s", task_id, gen_type, paper_dir.name)


def _run_single_task(task_id: str, cfg, metadata: dict) -> None:
    paper_ref = metadata.get("paper_ref") or metadata.get("paper_id")
    types = normalize_generation_types(metadata.get("types"))

    update_task(task_id, status="running", total=len(types), completed=0, failed=0, progress=0, error=None)

    if not paper_ref:
        update_task(task_id, status="failed", progress=100, error="paper_ref is required")
        return

    try:
        paper_dir = resolve_paper_dir(cfg, str(paper_ref))
    except ServiceError as exc:
        update_task(task_id, status="failed", progress=100, error=exc.message)
        return

    for index, gen_type in enumerate(types, start=1):
        progress = int(index / len(types) * 100)
        try:
            _run_generator(task_id, paper_dir, cfg, gen_type)
            current = get_task(task_id) or {}
            update_task(
                task_id,
                completed=current.get("completed", 0) + 1,
                progress=progress,
                error=None,
            )
        except Exception as exc:
            current = get_task(task_id) or {}
            update_task(
                task_id,
                failed=current.get("failed", 0) + 1,
                progress=progress,
                error=str(exc),
            )

    _finish_task(task_id)


def _run_batch_task(task_id: str, cfg, metadata: dict) -> None:
    paper_refs = metadata.get("paper_refs") or metadata.get("paper_ids") or []
    types = normalize_generation_types(metadata.get("types"))

    if not paper_refs:
        update_task(task_id, status="failed", progress=100, error="paper_ids is required and must be non-empty")
        return

    update_task(task_id, status="running", total=len(paper_refs), completed=0, failed=0, progress=0, error=None)

    for index, paper_ref in enumerate(paper_refs, start=1):
        progress = int(index / len(paper_refs) * 100)
        try:
            paper_dir = resolve_paper_dir(cfg, str(paper_ref))
        except ServiceError as exc:
            current = get_task(task_id) or {}
            update_task(
                task_id,
                failed=current.get("failed", 0) + 1,
                progress=progress,
                error=exc.message,
            )
            continue

        paper_failed = 0
        last_error = None
        for gen_type in types:
            try:
                _run_generator(task_id, paper_dir, cfg, gen_type)
            except Exception as exc:
                paper_failed += 1
                last_error = str(exc)

        current = get_task(task_id) or {}
        update_task(
            task_id,
            completed=current.get("completed", 0) + 1,
            failed=current.get("failed", 0) + paper_failed,
            progress=progress,
            error=last_error,
        )

    _finish_task(task_id)


def process_task(task_id: str, cfg=None) -> None:
    """Process a generation task synchronously."""
    task = get_task(task_id)
    if task is None:
        raise ServiceError("Task not found", status_code=404)

    cfg = cfg or load_config()
    metadata = task.get("metadata") or {}

    if task.get("type") == "generate":
        _run_single_task(task_id, cfg, metadata)
        return
    if task.get("type") == "batch_generate":
        _run_batch_task(task_id, cfg, metadata)
        return

    raise ServiceError(f"Unsupported task type: {task.get('type')}", status_code=400)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ScholarAIO generation tasks")
    parser.add_argument("task_id", help="Task ID to process")
    args = parser.parse_args()
    process_task(args.task_id)


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from scholaraio.services.common import ServiceError, resolve_paper_dir
from scholaraio.tasks import create_task

DEFAULT_GENERATION_TYPES = ("summary", "rating")
VALID_GENERATION_TYPES = {
    "summary",
    "method",
    "reflection",
    "user_notes",
    "rating",
    "sensemaking",
}


def normalize_generation_types(types: list[str] | None) -> list[str]:
    """Validate, deduplicate, and normalize requested generation types."""
    if not types:
        return list(DEFAULT_GENERATION_TYPES)

    normalized: list[str] = []
    seen: set[str] = set()
    for value in types:
        if not isinstance(value, str):
            continue
        item = value.strip()
        if not item:
            continue
        if item not in VALID_GENERATION_TYPES:
            raise ServiceError(f"Unsupported generation type: {item}", status_code=400)
        if item in seen:
            continue
        normalized.append(item)
        seen.add(item)

    return normalized or list(DEFAULT_GENERATION_TYPES)


def _normalize_paper_refs(paper_refs: list[str] | None) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in paper_refs or []:
        if not isinstance(value, str):
            continue
        item = value.strip()
        if not item or item in seen:
            continue
        refs.append(item)
        seen.add(item)
    return refs


def _worker_env(cfg) -> dict[str, str]:
    env = os.environ.copy()
    cfg_path = cfg._root / "config.yaml"
    if cfg_path.exists():
        env["SCHOLARAIO_CONFIG"] = str(cfg_path)
    env["SCHOLARAIO_TASKS_DIR"] = str(cfg._root / "data" / ".tasks")
    env["PYTHONUTF8"] = "1"
    return env


def _spawn_generation_worker(cfg, task_id: str) -> None:
    subprocess.Popen(
        [sys.executable, "-m", "scholaraio.generation_worker", task_id],
        cwd=str(cfg._root),
        env=_worker_env(cfg),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def enqueue_generation_task(cfg, paper_ref: str, types: list[str] | None = None) -> dict:
    """Create a single-paper generation task and start the background worker."""
    paper_dir = resolve_paper_dir(cfg, paper_ref)
    normalized_types = normalize_generation_types(types)

    task = create_task(
        task_type="generate",
        description=f"Generate materials for paper {paper_dir.name}",
        paper_ref=paper_dir.name,
        types=normalized_types,
    )
    _spawn_generation_worker(cfg, task["task_id"])
    return {"task_id": task["task_id"]}


def enqueue_batch_generation_task(cfg, paper_refs: list[str] | None, types: list[str] | None = None) -> dict:
    """Create a batch generation task and start the background worker."""
    normalized_refs = _normalize_paper_refs(paper_refs)
    if not normalized_refs:
        raise ServiceError("paper_ids is required and must be non-empty", status_code=400)

    normalized_types = normalize_generation_types(types)
    task = create_task(
        task_type="batch_generate",
        description=f"Batch generate materials for {len(normalized_refs)} papers",
        paper_refs=normalized_refs,
        types=normalized_types,
        total_papers=len(normalized_refs),
    )
    _spawn_generation_worker(cfg, task["task_id"])
    return {"task_id": task["task_id"]}

from __future__ import annotations

from pathlib import Path

from scholaraio.papers import (
    best_citation,
    read_meta,
    read_method,
    read_readable_report,
    read_score_report,
    read_sensemaking,
    read_summary,
    set_read_status,
    set_tags,
)
from scholaraio.services.common import ServiceError, resolve_paper_dir


CLOSE_READ_TAG = '精读'
CLOSE_READ_GENERATION_TYPES = ['sensemaking']


def _normalize_read_status(status: str | None) -> str:
    return status if status in {"unread", "read"} else "unread"


def _clean_tags(tags: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        if not isinstance(tag, str):
            continue
        value = tag.strip()
        if not value or value in seen:
            continue
        cleaned.append(value)
        seen.add(value)
    return cleaned


def _count_headings(markdown: str) -> int:
    return sum(1 for line in markdown.splitlines() if line.lstrip().startswith("#"))


def _word_count(markdown: str) -> int:
    return len(markdown.split())


def _recognized_fields(meta: dict) -> dict:
    fields: dict[str, object] = {}
    for key in (
        "title",
        "authors",
        "year",
        "journal",
        "doi",
        "paper_type",
        "publisher",
        "issn",
        "volume",
        "issue",
        "pages",
        "abstract",
    ):
        value = meta.get(key)
        if value in (None, "", [], {}):
            continue
        fields[key] = value
    return fields


def _parsed_source_payload(paper_dir: Path, meta: dict, markdown: str) -> dict:
    images_dir = paper_dir / "images"
    content_lists = sorted(path.name for path in paper_dir.glob("*_content_list.json"))

    return {
        "files": [
            {"name": "meta.json", "kind": "structured_metadata", "exists": True},
            {"name": "paper.md", "kind": "parsed_markdown", "exists": bool(markdown.strip())},
        ],
        "recognized_fields": _recognized_fields(meta),
        "markdown_stats": {
            "lines": len(markdown.splitlines()),
            "words": _word_count(markdown),
            "headings": _count_headings(markdown),
        },
        "assets": {
            "images": len(list(images_dir.glob("*"))) if images_dir.exists() else 0,
            "has_layout": (paper_dir / "layout.json").exists(),
            "content_lists": content_lists,
        },
        "generator_input": {
            "file": "paper.md",
            "mode": "parsed_markdown",
            "note": "Generated materials use the parsed paper.md content as source input.",
        },
    }


def get_paper_detail(cfg, paper_ref: str) -> dict:
    """Return the current web paper detail payload."""
    paper_dir = resolve_paper_dir(cfg, paper_ref)
    meta = read_meta(paper_dir)
    markdown = get_paper_markdown(cfg, paper_ref)

    summary = read_summary(paper_dir) or meta.get("summary") or ""
    method_summary = read_method(paper_dir) or meta.get("method_summary") or ""
    score_report = read_score_report(paper_dir) or ""
    readable_report = read_readable_report(paper_dir) or ""
    sensemaking = read_sensemaking(paper_dir)

    tags = meta.get("tags") or []

    return {
        "dir_name": paper_dir.name,
        "title": meta.get("title") or "",
        "authors": meta.get("authors") or [],
        "year": meta.get("year"),
        "journal": meta.get("journal") or "",
        "doi": meta.get("doi") or "",
        "abstract": meta.get("abstract") or "",
        "paper_type": meta.get("paper_type") or "",
        "publisher": meta.get("publisher") or "",
        "issn": meta.get("issn") or "",
        "volume": meta.get("volume") or "",
        "issue": meta.get("issue") or "",
        "pages": meta.get("pages") or "",
        "tags": tags,
        "is_close_read": CLOSE_READ_TAG in tags,
        "read_status": _normalize_read_status(meta.get("read_status")),
        "read_at": meta.get("read_at"),
        "citation_count": best_citation(meta),
        "summary": summary,
        "method_summary": method_summary,
        "score_report": score_report,
        "readable_report": readable_report,
        "sensemaking": sensemaking,
        "rating": meta.get("rating") or None,
        "parsed_source": _parsed_source_payload(paper_dir, meta, markdown),
    }


def get_paper_markdown(cfg, paper_ref: str) -> str:
    """Return raw paper markdown content, if present."""
    paper_dir = resolve_paper_dir(cfg, paper_ref)
    md_path = paper_dir / "paper.md"
    if not md_path.exists():
        return ""
    return md_path.read_text(encoding="utf-8", errors="replace")


def update_paper_read_status(cfg, paper_ref: str, status: str) -> dict:
    paper_dir = resolve_paper_dir(cfg, paper_ref)
    try:
        read_status = set_read_status(paper_dir, status)
    except ValueError as exc:
        raise ServiceError(str(exc), status_code=400) from exc
    return {"success": True, "read_status": _normalize_read_status(read_status)}


def update_paper_tags(cfg, paper_ref: str, tags: list[str]) -> dict:
    paper_dir = resolve_paper_dir(cfg, paper_ref)

    old_meta = read_meta(paper_dir)
    old_tags = old_meta.get("tags") or []
    cleaned = _clean_tags(tags)
    is_adding_close_read = CLOSE_READ_TAG in cleaned and CLOSE_READ_TAG not in old_tags

    updated = set_tags(paper_dir, cleaned)
    result = {
        "success": True,
        "tags": updated,
        "is_close_read": CLOSE_READ_TAG in updated,
    }

    if is_adding_close_read:
        from scholaraio.services.generation_service import enqueue_generation_task

        try:
            task = enqueue_generation_task(cfg, paper_ref, types=CLOSE_READ_GENERATION_TYPES)
            result["task_id"] = task.get("task_id")
            result["queued_types"] = list(CLOSE_READ_GENERATION_TYPES)
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Failed to enqueue generation task: {e}")

    return result


def set_paper_close_read(cfg, paper_ref: str, enabled: bool = True) -> dict:
    paper_dir = resolve_paper_dir(cfg, paper_ref)
    meta = read_meta(paper_dir)
    current_tags = _clean_tags(meta.get("tags") or [])

    if enabled:
        next_tags = current_tags if CLOSE_READ_TAG in current_tags else [*current_tags, CLOSE_READ_TAG]
    else:
        next_tags = [tag for tag in current_tags if tag != CLOSE_READ_TAG]

    result = update_paper_tags(cfg, paper_ref, next_tags)
    result["close_read"] = bool(enabled)
    return result

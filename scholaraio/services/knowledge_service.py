from __future__ import annotations

from collections import Counter

from scholaraio.knowledge import append_knowledge, read_knowledge, read_tags_registry, search_knowledge
from scholaraio.papers import iter_paper_dirs, read_meta
from scholaraio.services.common import ServiceError


def get_knowledge(cfg) -> str:
    return read_knowledge(cfg._root)


def add_knowledge_note(cfg, note: str, category: str = "general") -> dict:
    note = (note or "").strip()
    if not note:
        raise ServiceError("note is required", status_code=400)
    append_knowledge(cfg._root, note, category or "general")
    return {"success": True}


def add_paper_summary_note(cfg, *, title: str = "", summary: str, category: str = "paper-summary") -> dict:
    summary = (summary or "").strip()
    if not summary:
        raise ServiceError("summary is required", status_code=400)
    label = category or "paper-summary"
    if title:
        label = f"{label} | {title}"
    append_knowledge(cfg._root, summary, label)
    return {"success": True}


def search_knowledge_notes(cfg, query: str) -> dict:
    return {"results": search_knowledge(cfg._root, query.strip()) if query.strip() else []}


def list_tags(cfg) -> list[dict]:
    registry = read_tags_registry(cfg._root)
    counts: Counter[str] = Counter()

    for paper_dir in iter_paper_dirs(cfg.papers_dir):
        try:
            meta = read_meta(paper_dir)
        except (ValueError, FileNotFoundError):
            continue
        for tag in meta.get("tags") or []:
            if isinstance(tag, str) and tag.strip():
                counts[tag.strip()] += 1

    all_tags = sorted(set(counts) | set(registry))
    return [
        {
            "tag": tag,
            "paper_count": counts.get(tag, registry.get(tag, {}).get("paper_count", 0)),
            "description": registry.get(tag, {}).get("description", ""),
            "color": registry.get(tag, {}).get("color", ""),
        }
        for tag in all_tags
    ]

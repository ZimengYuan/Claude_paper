from __future__ import annotations

from scholaraio.index import unified_search
from scholaraio.papers import (
    best_citation,
    iter_paper_dirs,
    read_meta,
    read_method,
    read_readable_report,
    read_score_report,
    read_sensemaking,
    read_summary,
)
from scholaraio.services.common import ServiceError
from scholaraio.workspace import read_paper_ids


def _normalize_read_status(status: str | None) -> str:
    return status if status in {"unread", "read"} else "unread"


def _has_text(value: str | None) -> bool:
    return bool((value or "").strip())


def _resolve_project_paper_ids(cfg, project: str = "") -> set[str] | None:
    project = (project or "").strip()
    if not project:
        return None

    ws_dir = cfg._root / "workspace" / project
    if not (ws_dir / "papers.json").exists():
        raise ServiceError(f"Project not found: {project}", status_code=404)
    return read_paper_ids(ws_dir)


def _material_flags(paper_dir, meta: dict) -> dict[str, bool]:
    return {
        "summary": _has_text(read_summary(paper_dir) or meta.get("summary")),
        "method": _has_text(read_method(paper_dir) or meta.get("method_summary")),
        "score_report": _has_text(read_score_report(paper_dir)),
        "report": _has_text(read_readable_report(paper_dir)),
        "rating": bool(meta.get("rating")),
        "sensemaking": bool(read_sensemaking(paper_dir)),
    }


def _has_library_materials(materials: dict[str, bool]) -> bool:
    return bool(materials.get("summary")) and bool(materials.get("method"))


def _to_card(paper_dir, meta: dict) -> dict:
    materials = _material_flags(paper_dir, meta)
    return {
        "dir_name": paper_dir.name,
        "paper_id": meta.get("id") or "",
        "title": meta.get("title") or "",
        "authors": meta.get("authors") or [],
        "year": meta.get("year"),
        "journal": meta.get("journal") or "",
        "doi": meta.get("doi") or "",
        "abstract": meta.get("abstract") or "",
        "tags": meta.get("tags") or [],
        "read_status": _normalize_read_status(meta.get("read_status")),
        "has_summary": materials["summary"],
        "has_materials": _has_library_materials(materials),
        "materials": materials,
        "citation_count": best_citation(meta),
        "rating": meta.get("rating") or None,
    }


def _fallback_match(card: dict, query: str) -> bool:
    q = query.lower()
    return (
        q in (card.get("title") or "").lower()
        or q in (card.get("abstract") or "").lower()
        or any(q in author.lower() for author in (card.get("authors") or []))
    )


def list_papers(cfg, *, query: str = "", show_all: bool = False, project: str = "") -> list[dict]:
    """Return paper cards for the current web library page.

    Uses unified search when a query is provided and the search index exists;
    otherwise falls back to filesystem scanning so the web app still works
    before indexes are built.
    """
    query = query.strip()
    project_paper_ids = _resolve_project_paper_ids(cfg, project)

    if query:
        try:
            results = unified_search(query, cfg.index_db, cfg=cfg, paper_ids=project_paper_ids)
            cards: list[dict] = []
            for row in results:
                dir_name = row.get("dir_name")
                if not dir_name:
                    continue
                paper_dir = cfg.papers_dir / dir_name
                if not (paper_dir / "meta.json").exists():
                    continue
                cards.append(_to_card(paper_dir, read_meta(paper_dir)))
        except FileNotFoundError:
            cards = []
        if cards:
            if show_all is False:
                cards = [card for card in cards if card["has_materials"]]
            return cards

    cards = []
    for paper_dir in iter_paper_dirs(cfg.papers_dir):
        try:
            meta = read_meta(paper_dir)
        except (ValueError, FileNotFoundError):
            continue
        if project_paper_ids is not None and meta.get("id") not in project_paper_ids:
            continue
        card = _to_card(paper_dir, meta)
        if query and _fallback_match(card, query) is False:
            continue
        if show_all is False and card["has_materials"] is False:
            continue
        cards.append(card)
    return cards

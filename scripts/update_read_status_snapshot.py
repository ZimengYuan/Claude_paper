from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


VALID_STATUSES = {"read", "unread"}
DEFAULT_SITE_DATA_DIR = Path("scholaraio/web/public/site-data")
DEFAULT_PAPERS_DIR = Path("data/papers")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean(value: object) -> str:
    return str(value or "").strip()


def _normalize_ref(value: object) -> str:
    text = _clean(value)
    if not text:
        return ""

    if text.startswith(("http://", "https://")):
        parsed = urlparse(text)
        text = parsed.path or text

    marker = "/paper/"
    if marker in text:
        text = text.split(marker, 1)[1]

    return text.strip().strip("/")


def _normalize_doi(value: object) -> str:
    text = _clean(value).lower()
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text).strip()


def _slug_key(value: object) -> str:
    text = _normalize_doi(value) or _clean(value).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _candidate_keys(record: dict, *, route_hint: str = "") -> set[str]:
    keys: set[str] = set()
    for value in (
        route_hint,
        record.get("route_id"),
        record.get("paper_route_id"),
        record.get("paper_id"),
        record.get("id"),
        record.get("dir_name"),
        record.get("doi"),
        record.get("title"),
    ):
        normalized = _normalize_ref(value)
        if normalized:
            keys.add(normalized)
            keys.add(normalized.lower())
            slug = _slug_key(normalized)
            if slug:
                keys.add(slug)

        doi = _normalize_doi(value)
        if doi:
            keys.add(doi)
            doi_slug = _slug_key(doi)
            if doi_slug:
                keys.add(doi_slug)

    return {key for key in keys if key}


def _matches(record: dict, paper_ref: str, *, route_hint: str = "") -> bool:
    normalized = _normalize_ref(paper_ref)
    if not normalized:
        return False

    keys = _candidate_keys(record, route_hint=route_hint)
    return normalized in keys or normalized.lower() in keys or _slug_key(normalized) in keys


def _matches_any(record: dict, paper_refs: set[str], *, route_hint: str = "") -> bool:
    return any(_matches(record, paper_ref, route_hint=route_hint) for paper_ref in paper_refs)


def _collect_static_aliases(site_data_dir: Path, paper_ref: str) -> set[str]:
    aliases = {_normalize_ref(paper_ref)}

    library_path = site_data_dir / "library.json"
    if library_path.exists():
        payload = _read_json(library_path)
        for paper in payload.get("papers") or []:
            if isinstance(paper, dict) and _matches(paper, paper_ref):
                aliases.update(_candidate_keys(paper))

    details_dir = site_data_dir / "papers"
    if details_dir.exists():
        for path in sorted(details_dir.glob("*.json")):
            payload = _read_json(path)
            if _matches(payload, paper_ref, route_hint=path.stem):
                aliases.update(_candidate_keys(payload, route_hint=path.stem))

    todo_path = site_data_dir / "todo-cards.json"
    if todo_path.exists():
        payload = _read_json(todo_path)
        for card in payload.get("cards") or []:
            if isinstance(card, dict) and _matches(card, paper_ref):
                aliases.update(_candidate_keys(card))

    return {alias for alias in aliases if alias}


def _apply_read_status(record: dict, status: str, timestamp: str, *, include_read_at: bool = True) -> bool:
    before = dict(record)
    record["read_status"] = status
    if include_read_at:
        record["read_at"] = timestamp
    return record != before


def _update_library(site_data_dir: Path, paper_ref: str, status: str, timestamp: str) -> tuple[int, list[Path]]:
    path = site_data_dir / "library.json"
    if not path.exists():
        return 0, []

    payload = _read_json(path)
    changed = 0
    for paper in payload.get("papers") or []:
        if isinstance(paper, dict) and _matches(paper, paper_ref):
            if _apply_read_status(paper, status, timestamp):
                changed += 1

    if changed:
        _write_json(path, payload)
    return changed, [path] if changed else []


def _update_paper_details(site_data_dir: Path, paper_ref: str, status: str, timestamp: str) -> tuple[int, list[Path]]:
    papers_dir = site_data_dir / "papers"
    if not papers_dir.exists():
        return 0, []

    changed = 0
    changed_paths: list[Path] = []
    for path in sorted(papers_dir.glob("*.json")):
        payload = _read_json(path)
        if not _matches(payload, paper_ref, route_hint=path.stem):
            continue
        if _apply_read_status(payload, status, timestamp):
            _write_json(path, payload)
            changed += 1
            changed_paths.append(path)

    return changed, changed_paths


def _update_todo_cards(site_data_dir: Path, paper_ref: str, status: str) -> tuple[int, list[Path]]:
    path = site_data_dir / "todo-cards.json"
    if not path.exists():
        return 0, []

    payload = _read_json(path)
    changed = 0
    for card in payload.get("cards") or []:
        if isinstance(card, dict) and _matches(card, paper_ref):
            before = dict(card)
            card["read_status"] = status
            if card != before:
                changed += 1

    if changed:
        _write_json(path, payload)
    return changed, [path] if changed else []


def _update_paper_meta(papers_dir: Path, paper_refs: set[str], status: str, timestamp: str) -> tuple[int, list[Path]]:
    if not papers_dir.exists():
        return 0, []

    changed = 0
    changed_paths: list[Path] = []
    for meta_path in sorted(papers_dir.glob("*/meta.json")):
        payload = _read_json(meta_path)
        if not _matches_any(payload, paper_refs, route_hint=meta_path.parent.name):
            continue
        if _apply_read_status(payload, status, timestamp):
            _write_json(meta_path, payload)
            changed += 1
            changed_paths.append(meta_path)

    return changed, changed_paths


def update_read_status_snapshot(
    *,
    root: Path,
    paper_ref: str,
    status: str,
    site_data_dir: Path | None = None,
    papers_dir: Path | None = None,
) -> dict:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid read status: {status}")

    normalized_ref = _normalize_ref(paper_ref)
    if not normalized_ref:
        raise ValueError("paper_ref is required")

    root = root.resolve()
    site_data_dir = (site_data_dir or root / DEFAULT_SITE_DATA_DIR).resolve()
    papers_dir = (papers_dir or root / DEFAULT_PAPERS_DIR).resolve()
    timestamp = _timestamp()
    aliases = _collect_static_aliases(site_data_dir, normalized_ref)

    library_count, library_paths = _update_library(site_data_dir, normalized_ref, status, timestamp)
    detail_count, detail_paths = _update_paper_details(site_data_dir, normalized_ref, status, timestamp)
    todo_count, todo_paths = _update_todo_cards(site_data_dir, normalized_ref, status)
    meta_count, meta_paths = _update_paper_meta(papers_dir, aliases, status, timestamp)

    changed_paths = []
    seen: set[Path] = set()
    for path in [*library_paths, *detail_paths, *todo_paths, *meta_paths]:
        if path not in seen:
            changed_paths.append(path)
            seen.add(path)

    total = library_count + detail_count + todo_count + meta_count
    if total == 0:
        raise FileNotFoundError(f"No matching paper found for {normalized_ref}")

    return {
        "paper_ref": normalized_ref,
        "read_status": status,
        "changed": {
            "library": library_count,
            "paper_details": detail_count,
            "todo_cards": todo_count,
            "paper_meta": meta_count,
        },
        "changed_paths": [str(path.relative_to(root)) if path.is_relative_to(root) else str(path) for path in changed_paths],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Update static ScholarAIO read-status snapshots.")
    parser.add_argument("--paper-ref", required=True, help="Paper route id, paper id, DOI, directory name, or /paper/<id> path")
    parser.add_argument("--status", required=True, choices=sorted(VALID_STATUSES), help="Read status to write")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--site-data-dir", default=None, help="Path to scholaraio/web/public/site-data")
    parser.add_argument("--papers-dir", default=None, help="Path to data/papers if present")
    args = parser.parse_args()

    root = Path(args.root)
    site_data_dir = Path(args.site_data_dir) if args.site_data_dir else None
    papers_dir = Path(args.papers_dir) if args.papers_dir else None
    result = update_read_status_snapshot(
        root=root,
        paper_ref=args.paper_ref,
        status=args.status,
        site_data_dir=site_data_dir,
        papers_dir=papers_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

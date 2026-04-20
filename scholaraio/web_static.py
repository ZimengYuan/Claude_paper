from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scholaraio.config import load_config
from scholaraio.papers import iter_paper_dirs, read_meta
from scholaraio.services.common import ServiceError
from scholaraio.services.explore_service import get_explore_library, list_explore_libraries
from scholaraio.services.graph_service import get_graph
from scholaraio.services.knowledge_service import get_knowledge, list_tags
from scholaraio.services.library_service import list_papers
from scholaraio.services.paper_service import get_paper_detail
from scholaraio.services.project_service import list_projects
from scholaraio.workspace import read_paper_ids


STATIC_SITE_VERSION = 1
GRAPH_MODES = ("citation", "structure", "topic")
GRAPH_MAX_NODES = 120
GRAPH_MIN_SHARED = 2
TODO_SNAPSHOT_FILENAME = "todo-cards.json"


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_slug(value: str, *, prefix: str, used: set[str]) -> str:
    base = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value or "").strip()).strip("._-").lower()
    if not base:
        digest = hashlib.sha1(str(value or prefix).encode("utf-8")).hexdigest()[:10]
        base = f"{prefix}-{digest}"

    slug = base
    counter = 2
    while slug in used:
        slug = f"{base}-{counter}"
        counter += 1
    used.add(slug)
    return slug


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _primary_paper_ref(meta: dict[str, Any], paper_dir: Path) -> str:
    for candidate in (meta.get("id"), paper_dir.name, meta.get("doi")):
        value = str(candidate or "").strip()
        if value:
            return value
    return paper_dir.name


def _build_route_map(cfg) -> tuple[dict[str, str], list[dict[str, str]]]:
    used: set[str] = set()
    route_map: dict[str, str] = {}
    manifest_rows: list[dict[str, str]] = []

    for paper_dir in iter_paper_dirs(cfg.papers_dir):
        try:
            meta = read_meta(paper_dir)
        except (ValueError, FileNotFoundError):
            continue

        primary_ref = _primary_paper_ref(meta, paper_dir)
        route_id = _safe_slug(primary_ref, prefix="paper", used=used)

        for candidate in (
            meta.get("id"),
            paper_dir.name,
            meta.get("doi"),
            str(meta.get("doi") or "").lower(),
        ):
            value = str(candidate or "").strip()
            if value:
                route_map[value] = route_id

        manifest_rows.append(
            {
                "route_id": route_id,
                "paper_ref": primary_ref,
                "paper_id": str(meta.get("id") or "").strip(),
                "dir_name": paper_dir.name,
                "title": str(meta.get("title") or "").strip(),
            }
        )

    manifest_rows.sort(key=lambda item: (item["title"] or item["dir_name"] or item["route_id"]).lower())
    return route_map, manifest_rows


def _resolve_route_id(record: dict[str, Any], route_map: dict[str, str]) -> str:
    for key in ("route_id", "paper_id", "paper_ref", "dir_name", "doi"):
        value = str(record.get(key) or "").strip()
        if not value:
            continue
        if key == "doi":
            value = value.lower()
        route_id = route_map.get(value)
        if route_id:
            return route_id
    return ""


def _inject_route_ids(value: Any, route_map: dict[str, str]) -> Any:
    if isinstance(value, list):
        return [_inject_route_ids(item, route_map) for item in value]

    if isinstance(value, dict):
        result = {key: _inject_route_ids(item, route_map) for key, item in value.items()}
        route_id = _resolve_route_id(result, route_map)
        if route_id and "route_id" not in result:
            result["route_id"] = route_id
        return result

    return value


def _project_payloads(cfg) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    projects = list_projects(cfg)
    slug_used: set[str] = set()
    project_memberships: dict[str, list[str]] = {}
    enriched: list[dict[str, Any]] = []

    for project in projects:
        name = str(project.get("name") or "").strip()
        if not name:
            continue
        ws_dir = cfg._root / "workspace" / name
        paper_ids = sorted(read_paper_ids(ws_dir))
        project_memberships[name] = paper_ids
        enriched.append(
            {
                **project,
                "slug": _safe_slug(name, prefix="project", used=slug_used),
            }
        )

    enriched.sort(key=lambda item: item["name"].lower())
    return enriched, project_memberships


def _empty_graph(mode: str, scope: str, *, project: str = "", message: str = "") -> dict[str, Any]:
    payload = {
        "mode": mode,
        "scope": scope,
        "nodes": [],
        "edges": [],
        "stats": {
            "nodes": 0,
            "edges": 0,
            "papers": 0,
            "external": 0,
            "topics": 0,
            "concepts": 0,
            "edge_types": {},
        },
        "truncated": False,
        "hidden_nodes": 0,
        "message": message,
    }
    if project:
        payload["project"] = project
    return payload


def _safe_graph(cfg, *, mode: str, scope: str, project: str = "") -> dict[str, Any]:
    try:
        payload = get_graph(
            cfg,
            mode=mode,
            scope=scope,
            project=project,
            min_shared=GRAPH_MIN_SHARED,
            max_nodes=GRAPH_MAX_NODES,
        )
    except ServiceError as exc:
        payload = _empty_graph(mode, scope, project=project, message=exc.message)
    except Exception as exc:  # pragma: no cover - defensive
        payload = _empty_graph(mode, scope, project=project, message=str(exc))

    if project:
        payload["project"] = project
    return payload


def _load_preserved_todo_snapshot(output_dir: Path) -> tuple[str | None, int]:
    """Load an existing Todo snapshot so export can restore it after clearing site-data."""
    candidates = [Path(output_dir) / TODO_SNAPSHOT_FILENAME]
    canonical = Path(__file__).resolve().parent / "web" / "public" / "site-data" / TODO_SNAPSHOT_FILENAME
    if canonical not in candidates:
        candidates.append(canonical)

    for path in candidates:
        if not path.exists():
            continue
        try:
            raw = path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            continue
        cards = payload.get("cards") or []
        if not isinstance(cards, list):
            continue
        return raw, len(cards)
    return None, 0


def export_static_site_data(cfg, output_dir: Path) -> dict[str, Any]:
    """Export a read-only ScholarAIO web snapshot for static hosting.

    Args:
        cfg: Loaded ScholarAIO config object.
        output_dir: Directory where ``site-data`` JSON files will be written.

    Returns:
        Summary information about the exported snapshot.
    """
    output_dir = Path(output_dir)
    preserved_todo_raw, preserved_todo_count = _load_preserved_todo_snapshot(output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_at = _timestamp()
    route_map, paper_manifest = _build_route_map(cfg)
    projects, project_memberships = _project_payloads(cfg)

    library_cards = _inject_route_ids(list_papers(cfg, show_all=False), route_map)
    library_payload = {
        "version": STATIC_SITE_VERSION,
        "generated_at": generated_at,
        "read_only": True,
        "snapshot_notice": "This GitHub Pages deployment is a read-only snapshot. Write actions are removed.",
        "papers": library_cards,
        "projects": projects,
        "project_memberships": project_memberships,
        "tags": list_tags(cfg),
    }
    _write_json(output_dir / "library.json", library_payload)

    paper_dir = output_dir / "papers"
    exported_papers = 0
    for row in paper_manifest:
        detail = get_paper_detail(cfg, row["paper_ref"])
        detail["route_id"] = row["route_id"]
        detail["paper_ref"] = row["paper_ref"]
        detail["read_only"] = True
        detail["snapshot_generated_at"] = generated_at
        _write_json(paper_dir / f"{row['route_id']}.json", _inject_route_ids(detail, route_map))
        exported_papers += 1

    knowledge_payload = {
        "version": STATIC_SITE_VERSION,
        "generated_at": generated_at,
        "read_only": True,
        "content": get_knowledge(cfg),
        "tags": list_tags(cfg),
    }
    _write_json(output_dir / "knowledge.json", knowledge_payload)

    explore_index = _inject_route_ids(list_explore_libraries(cfg), route_map)
    explore_detail = _inject_route_ids(get_explore_library(cfg, "current-library"), route_map)
    roadmap_path = cfg.topics_model_dir / "roadmap.md"
    explore_detail["roadmap"] = roadmap_path.read_text(encoding="utf-8") if roadmap_path.exists() else ""
    explore_detail["read_only"] = True
    explore_detail["snapshot_generated_at"] = generated_at
    _write_json(output_dir / "explore" / "index.json", explore_index)
    _write_json(output_dir / "explore" / "current-library.json", explore_detail)

    graph_index = {
        "version": STATIC_SITE_VERSION,
        "generated_at": generated_at,
        "read_only": True,
        "library": {},
        "projects": [],
    }

    for mode in GRAPH_MODES:
        graph_payload = _inject_route_ids(_safe_graph(cfg, mode=mode, scope="library"), route_map)
        rel_path = f"graphs/library/{mode}.json"
        _write_json(output_dir / rel_path, graph_payload)
        graph_index["library"][mode] = rel_path

    for project in projects:
        project_entry = {
            "name": project["name"],
            "slug": project["slug"],
            "paper_count": project["paper_count"],
            "files": {},
        }
        for mode in GRAPH_MODES:
            graph_payload = _inject_route_ids(
                _safe_graph(cfg, mode=mode, scope="project", project=project["name"]),
                route_map,
            )
            rel_path = f"graphs/projects/{project['slug']}/{mode}.json"
            _write_json(output_dir / rel_path, graph_payload)
            project_entry["files"][mode] = rel_path
        graph_index["projects"].append(project_entry)

    _write_json(output_dir / "graphs" / "index.json", graph_index)

    manifest = {
        "version": STATIC_SITE_VERSION,
        "generated_at": generated_at,
        "paper_routes": [f"/paper/{row['route_id']}" for row in paper_manifest],
        "papers": paper_manifest,
        "projects": projects,
    }
    _write_json(output_dir / "manifest.json", manifest)
    if preserved_todo_raw:
        _write_text(output_dir / TODO_SNAPSHOT_FILENAME, preserved_todo_raw)
    _write_text(output_dir / ".generated", generated_at + "\n")

    return {
        "generated_at": generated_at,
        "papers_exported": exported_papers,
        "library_cards": len(library_cards),
        "projects": len(projects),
        "todo_cards": preserved_todo_count,
        "output_dir": str(output_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export ScholarAIO static web snapshot")
    parser.add_argument("--output", required=True, help="Output directory for static site data")
    parser.add_argument("--config", default=None, help="Optional config path")
    args = parser.parse_args()

    cfg = load_config(args.config)
    cfg.ensure_dirs()
    result = export_static_site_data(cfg, Path(args.output))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

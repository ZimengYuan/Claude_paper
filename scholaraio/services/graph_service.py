from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scholaraio.papers import best_citation, iter_paper_dirs, read_meta
from scholaraio.services.common import ServiceError, resolve_paper_dir
from scholaraio.workspace import read_paper_ids


_GRAPH_MODES = {"citation", "structure", "topic"}
_GRAPH_SCOPES = {"library", "project", "paper"}
_ROLE_ORDER = {"center": 0, "topic": 1, "reference": 2, "citer": 3, "shared": 4, "paper": 5, "external": 6}


def _normalize_mode(mode: str) -> str:
    value = (mode or "citation").strip().lower()
    if value not in _GRAPH_MODES:
        raise ServiceError(f"Unsupported graph mode: {mode}", status_code=400)
    return value


def _normalize_scope(scope: str) -> str:
    value = (scope or "library").strip().lower()
    if value not in _GRAPH_SCOPES:
        raise ServiceError(f"Unsupported graph scope: {scope}", status_code=400)
    return value


def _safe_int(value: Any, default: int, *, minimum: int = 0, maximum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def _first_author(meta: dict) -> str:
    value = str(meta.get("first_author_lastname") or "").strip()
    if value:
        return value
    authors = meta.get("authors") or []
    if authors:
        return str(authors[0]).split()[-1]
    return ""


def _best_citation_value(value: Any) -> int:
    if isinstance(value, dict):
        vals = [item for item in value.values() if isinstance(item, (int, float))]
        return int(max(vals)) if vals else 0
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def _paper_record_from_meta(paper_dir: Path, meta: dict) -> dict[str, Any]:
    return {
        "id": str(meta.get("id") or "").strip(),
        "dir_name": paper_dir.name,
        "paper_ref": paper_dir.name,
        "title": meta.get("title") or paper_dir.name,
        "label": meta.get("title") or paper_dir.name,
        "doi": meta.get("doi") or "",
        "authors": meta.get("authors") or [],
        "first_author": _first_author(meta),
        "year": meta.get("year"),
        "journal": meta.get("journal") or "",
        "tags": meta.get("tags") or [],
        "citation_count": best_citation(meta),
        "read_status": meta.get("read_status") or "unread",
        "type": "paper",
    }


def _load_local_papers(cfg) -> dict[str, dict[str, Any]]:
    papers: dict[str, dict[str, Any]] = {}
    for paper_dir in iter_paper_dirs(cfg.papers_dir):
        try:
            meta = read_meta(paper_dir)
        except (ValueError, FileNotFoundError):
            continue
        paper_id = str(meta.get("id") or "").strip()
        if not paper_id:
            continue
        papers[paper_id] = _paper_record_from_meta(paper_dir, meta)
    return papers


def _resolve_project_paper_ids(cfg, project: str) -> set[str]:
    project_name = (project or "").strip()
    if not project_name:
        raise ServiceError("project is required for project scope", status_code=400)
    ws_dir = cfg._root / "workspace" / project_name
    if not (ws_dir / "papers.json").exists():
        raise ServiceError(f"Project not found: {project_name}", status_code=404)
    return read_paper_ids(ws_dir)


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _empty_graph(*, mode: str, scope: str, message: str = "") -> dict[str, Any]:
    return {
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


def _fetch_local_citations(db_path: Path, paper_ids: set[str]) -> list[dict[str, Any]]:
    if not db_path.exists() or not paper_ids:
        return []
    ids = sorted(paper_ids)
    placeholders = ",".join("?" for _ in ids)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            f"""SELECT source_id, target_id
                  FROM citations
                  WHERE source_id IN ({placeholders})
                    AND target_id IN ({placeholders})
                    AND target_id IS NOT NULL
                  ORDER BY source_id, target_id""",
            [*ids, *ids],
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def _fetch_shared_edges(db_path: Path, paper_ids: set[str], min_shared: int) -> list[dict[str, Any]]:
    if not db_path.exists() or len(paper_ids) < 2:
        return []
    ids = sorted(paper_ids)
    placeholders = ",".join("?" for _ in ids)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            f"""SELECT c1.source_id AS source_id,
                         c2.source_id AS target_id,
                         COUNT(*) AS shared_refs
                  FROM citations c1
                  JOIN citations c2
                    ON LOWER(c1.target_doi) = LOWER(c2.target_doi)
                   AND c1.source_id < c2.source_id
                  WHERE c1.source_id IN ({placeholders})
                    AND c2.source_id IN ({placeholders})
                  GROUP BY c1.source_id, c2.source_id
                  HAVING COUNT(*) >= ?
                  ORDER BY shared_refs DESC, c1.source_id, c2.source_id""",
            [*ids, *ids, min_shared],
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def _fetch_shared_neighbors(db_path: Path, center_id: str, allowed_ids: set[str], min_shared: int) -> list[dict[str, Any]]:
    if not db_path.exists() or not center_id:
        return []
    allowed = sorted(pid for pid in allowed_ids if pid != center_id)
    if not allowed:
        return []
    placeholders = ",".join("?" for _ in allowed)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            f"""SELECT other.source_id AS paper_id,
                         COUNT(*) AS shared_refs
                  FROM citations base
                  JOIN citations other
                    ON LOWER(base.target_doi) = LOWER(other.target_doi)
                   AND other.source_id != base.source_id
                  WHERE base.source_id = ?
                    AND other.source_id IN ({placeholders})
                  GROUP BY other.source_id
                  HAVING COUNT(*) >= ?
                  ORDER BY shared_refs DESC, other.source_id""",
            [center_id, *allowed, min_shared],
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def _ensure_node(graph_nodes: dict[str, dict[str, Any]], node: dict[str, Any], role: str) -> None:
    existing = graph_nodes.get(node["id"])
    if existing is None:
        entry = dict(node)
        entry["roles"] = [role]
        entry["role"] = role
        entry["degree"] = 0
        graph_nodes[node["id"]] = entry
        return
    roles = set(existing.get("roles") or [])
    roles.add(role)
    ordered_roles = sorted(roles, key=lambda item: _ROLE_ORDER.get(item, 99))
    existing["roles"] = ordered_roles
    existing["role"] = ordered_roles[0]


def _paper_node(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "type": "paper",
        "paper_ref": record.get("paper_ref") or record.get("dir_name") or record["id"],
        "dir_name": record.get("dir_name") or "",
        "label": record.get("title") or record.get("dir_name") or record["id"],
        "title": record.get("title") or "",
        "doi": record.get("doi") or "",
        "year": record.get("year"),
        "first_author": record.get("first_author") or "",
        "journal": record.get("journal") or "",
        "citation_count": int(record.get("citation_count") or 0),
        "tags": record.get("tags") or [],
        "read_status": record.get("read_status") or "unread",
    }


def _external_node(doi: str) -> dict[str, Any]:
    clean = (doi or "").strip()
    label = clean or "External reference"
    return {
        "id": f"doi:{clean}",
        "type": "external",
        "paper_ref": "",
        "dir_name": "",
        "label": label,
        "title": label,
        "doi": clean,
        "year": None,
        "first_author": "",
        "journal": "",
        "citation_count": 0,
        "tags": [],
        "read_status": "",
    }


def _topic_paper_brief(meta: dict[str, Any], local_papers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    paper_id = str(meta.get("paper_id") or meta.get("id") or "").strip()
    local = local_papers.get(paper_id, {})
    title = meta.get("title") or local.get("title") or paper_id
    first_author = local.get("first_author") or str(meta.get("authors") or "").split(",")[0].strip()
    return {
        "paper_id": paper_id,
        "paper_ref": local.get("paper_ref") or local.get("dir_name") or paper_id,
        "title": title,
        "year": meta.get("year") or local.get("year"),
        "first_author": first_author,
        "citation_count": max(_best_citation_value(meta.get("citation_count")), int(local.get("citation_count") or 0)),
    }


def _topic_node(topic_id: int, *, keywords: list[str], papers: list[dict[str, Any]], center: bool = False) -> dict[str, Any]:
    title = ", ".join(keywords[:4]) if keywords else f"Topic {topic_id}"
    return {
        "id": f"topic:{topic_id}",
        "type": "topic",
        "paper_ref": "",
        "dir_name": "",
        "label": f"Topic {topic_id}",
        "title": title,
        "topic_id": topic_id,
        "topic_label": f"Topic {topic_id}",
        "keywords": keywords,
        "paper_count": len(papers),
        "representative_papers": papers[:6],
        "citation_count": max((int(paper.get("citation_count") or 0) for paper in papers), default=0),
        "tags": [],
        "read_status": "",
        "year": None,
        "first_author": "",
        "journal": "",
        "role": "center" if center else "topic",
        "roles": ["center"] if center else ["topic"],
    }


def _edge_id(source: str, target: str, edge_type: str) -> str:
    return f"{edge_type}:{source}->{target}"


def _truncate_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    max_nodes: int,
    center_id: str = "",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool, int]:
    if len(nodes) <= max_nodes:
        return nodes, edges, False, 0

    degree = Counter()
    for edge in edges:
        degree[edge["source"]] += 1
        degree[edge["target"]] += 1

    def _sort_key(node: dict[str, Any]) -> tuple:
        return (
            0 if node["id"] == center_id else 1,
            0 if node.get("type") == "paper" else 1,
            -degree.get(node["id"], 0),
            -(int(node.get("paper_count") or 0)),
            -(int(node.get("citation_count") or 0)),
            -(int(node.get("year") or 0)),
            node.get("label") or node.get("id") or "",
        )

    keep_ids = {node["id"] for node in sorted(nodes, key=_sort_key)[:max_nodes]}
    pruned_nodes = [node for node in nodes if node["id"] in keep_ids]
    pruned_edges = [edge for edge in edges if edge["source"] in keep_ids and edge["target"] in keep_ids]
    return pruned_nodes, pruned_edges, True, len(nodes) - len(pruned_nodes)


def _annotate_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    mode: str,
    scope: str,
    message: str,
    truncated: bool,
    hidden_nodes: int,
) -> dict[str, Any]:
    degree = Counter()
    edge_types = Counter()
    for edge in edges:
        degree[edge["source"]] += 1
        degree[edge["target"]] += 1
        if edge.get("type") == "structure":
            relations = edge.get("relations") or []
            if relations:
                for relation in relations:
                    edge_types[relation] += 1
            else:
                edge_types["structure"] += 1
        else:
            edge_types[edge.get("type") or "edge"] += 1
    for node in nodes:
        node["degree"] = degree.get(node["id"], 0)

    if mode == "topic":
        represented_papers = sum(int(node.get("paper_count") or 0) for node in nodes if node.get("type") == "topic")
    else:
        represented_papers = sum(1 for node in nodes if node.get("type") == "paper")

    stats = {
        "nodes": len(nodes),
        "edges": len(edges),
        "papers": represented_papers,
        "external": sum(1 for node in nodes if node.get("type") == "external"),
        "topics": sum(1 for node in nodes if node.get("type") == "topic"),
        "concepts": 0,
        "edge_types": dict(edge_types),
    }
    return {
        "mode": mode,
        "scope": scope,
        "nodes": nodes,
        "edges": edges,
        "stats": stats,
        "truncated": truncated,
        "hidden_nodes": hidden_nodes,
        "message": message,
    }


def _project_or_library_candidates(
    cfg,
    local_papers: dict[str, dict[str, Any]],
    *,
    scope: str,
    project: str,
    max_nodes: int,
) -> tuple[set[str], bool, int]:
    if scope == "project":
        allowed = _resolve_project_paper_ids(cfg, project)
        papers = [record for paper_id, record in local_papers.items() if paper_id in allowed]
    else:
        papers = list(local_papers.values())

    papers.sort(
        key=lambda record: (
            -(int(record.get("citation_count") or 0)),
            -(int(record.get("year") or 0)),
            record.get("title") or record.get("dir_name") or record["id"],
        )
    )

    seed_limit = max(max_nodes * 2, max_nodes)
    if len(papers) > seed_limit:
        hidden = len(papers) - seed_limit
        papers = papers[:seed_limit]
        return {record["id"] for record in papers}, True, hidden
    return {record["id"] for record in papers}, False, 0


def _build_citation_graph(
    cfg,
    local_papers: dict[str, dict[str, Any]],
    *,
    scope: str,
    project: str,
    paper_ref: str,
    max_nodes: int,
) -> dict[str, Any]:
    if not cfg.index_db.exists():
        return _empty_graph(mode="citation", scope=scope, message="Citation index not found. Run index --rebuild first.")

    graph_nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    truncated = False
    hidden_nodes = 0
    message = ""
    center_id = ""

    if scope == "paper":
        if not (paper_ref or "").strip():
            raise ServiceError("paper_ref is required for paper scope", status_code=400)
        center_dir = resolve_paper_dir(cfg, paper_ref)
        center_meta = read_meta(center_dir)
        center_id = str(center_meta.get("id") or "").strip()
        if not center_id:
            raise ServiceError("Paper id is missing in meta.json", status_code=400)
        center_record = local_papers.get(center_id) or _paper_record_from_meta(center_dir, center_meta)
        local_papers[center_id] = center_record
        _ensure_node(graph_nodes, _paper_node(center_record), "center")

        neighbor_ids: set[str] = {center_id}
        references = []
        citers = []
        try:
            from scholaraio.index import get_citing_papers, get_references

            references = get_references(center_id, cfg.index_db)
            citers = get_citing_papers(center_id, cfg.index_db)
        except FileNotFoundError:
            references = []
            citers = []

        ranked_neighbors: list[tuple[float, str]] = []

        for ref in references:
            target_id = ref.get("target_id")
            if target_id and target_id in local_papers:
                target = local_papers[target_id]
                ranked_neighbors.append((1000 + int(target.get("citation_count") or 0), target_id))
            elif ref.get("target_doi"):
                doi = str(ref.get("target_doi") or "").strip()
                ranked_neighbors.append((100, f"doi:{doi}"))

        for citer in citers:
            source_id = str(citer.get("source_id") or "").strip()
            if source_id and source_id in local_papers:
                source = local_papers[source_id]
                ranked_neighbors.append((1200 + int(source.get("citation_count") or 0), source_id))

        seen_neighbor_ids: set[str] = set()
        keep_budget = max(max_nodes - 1, 0)
        for _, neighbor_id in sorted(ranked_neighbors, key=lambda item: (-item[0], item[1])):
            if neighbor_id in seen_neighbor_ids:
                continue
            seen_neighbor_ids.add(neighbor_id)
            if keep_budget and len(neighbor_ids) - 1 >= keep_budget:
                hidden_nodes += 1
                truncated = True
                continue
            neighbor_ids.add(neighbor_id)

        for ref in references:
            target_id = ref.get("target_id")
            if target_id and target_id in neighbor_ids and target_id in local_papers:
                _ensure_node(graph_nodes, _paper_node(local_papers[target_id]), "reference")
                edges.append(
                    {
                        "id": _edge_id(center_id, target_id, "cites"),
                        "source": center_id,
                        "target": target_id,
                        "type": "cites",
                        "label": "cites",
                        "weight": 1.0,
                        "directed": True,
                    }
                )
            elif ref.get("target_doi"):
                ext_id = f"doi:{str(ref.get('target_doi') or '').strip()}"
                if ext_id not in neighbor_ids:
                    continue
                _ensure_node(graph_nodes, _external_node(str(ref.get("target_doi") or "")), "reference")
                edges.append(
                    {
                        "id": _edge_id(center_id, ext_id, "cites"),
                        "source": center_id,
                        "target": ext_id,
                        "type": "cites",
                        "label": "cites",
                        "weight": 1.0,
                        "directed": True,
                    }
                )

        for citer in citers:
            source_id = str(citer.get("source_id") or "").strip()
            if source_id not in neighbor_ids or source_id not in local_papers:
                continue
            _ensure_node(graph_nodes, _paper_node(local_papers[source_id]), "citer")
            edges.append(
                {
                    "id": _edge_id(source_id, center_id, "cites"),
                    "source": source_id,
                    "target": center_id,
                    "type": "cites",
                    "label": "cites",
                    "weight": 1.0,
                    "directed": True,
                }
            )

        if len(graph_nodes) == 1 and not edges:
            message = "No citation neighbors found for this paper yet."
    else:
        candidate_ids, seed_truncated, seed_hidden = _project_or_library_candidates(
            cfg,
            local_papers,
            scope=scope,
            project=project,
            max_nodes=max_nodes,
        )
        truncated = seed_truncated
        hidden_nodes += seed_hidden
        if not candidate_ids:
            return _empty_graph(mode="citation", scope=scope, message="No papers available in this scope.")

        for paper_id in candidate_ids:
            if paper_id in local_papers:
                _ensure_node(graph_nodes, _paper_node(local_papers[paper_id]), "paper")

        for row in _fetch_local_citations(cfg.index_db, candidate_ids):
            source_id = row["source_id"]
            target_id = row["target_id"]
            if source_id not in graph_nodes or target_id not in graph_nodes:
                continue
            edges.append(
                {
                    "id": _edge_id(source_id, target_id, "cites"),
                    "source": source_id,
                    "target": target_id,
                    "type": "cites",
                    "label": "cites",
                    "weight": 1.0,
                    "directed": True,
                }
            )

        if not edges:
            message = "No local citation edges found in this scope."

    nodes = list(graph_nodes.values())
    nodes, edges, extra_truncated, extra_hidden = _truncate_graph(nodes, edges, max_nodes=max_nodes, center_id=center_id)
    truncated = truncated or extra_truncated
    hidden_nodes += extra_hidden
    return _annotate_graph(
        nodes,
        edges,
        mode="citation",
        scope=scope,
        message=message,
        truncated=truncated,
        hidden_nodes=hidden_nodes,
    )


def _build_structure_graph(
    cfg,
    local_papers: dict[str, dict[str, Any]],
    *,
    scope: str,
    project: str,
    paper_ref: str,
    min_shared: int,
    max_nodes: int,
) -> dict[str, Any]:
    if not cfg.index_db.exists():
        return _empty_graph(mode="structure", scope=scope, message="Citation index not found. Run index --rebuild first.")

    candidate_ids: set[str]
    center_id = ""
    truncated = False
    hidden_nodes = 0
    message = ""

    if scope == "paper":
        if not (paper_ref or "").strip():
            raise ServiceError("paper_ref is required for paper scope", status_code=400)
        center_dir = resolve_paper_dir(cfg, paper_ref)
        center_meta = read_meta(center_dir)
        center_id = str(center_meta.get("id") or "").strip()
        if not center_id:
            raise ServiceError("Paper id is missing in meta.json", status_code=400)
        center_record = local_papers.get(center_id) or _paper_record_from_meta(center_dir, center_meta)
        local_papers[center_id] = center_record

        try:
            from scholaraio.index import get_citing_papers, get_references

            local_refs = {
                str(row.get("target_id") or "").strip()
                for row in get_references(center_id, cfg.index_db)
                if row.get("target_id")
            }
            citers = {
                str(row.get("source_id") or "").strip()
                for row in get_citing_papers(center_id, cfg.index_db)
                if row.get("source_id")
            }
        except FileNotFoundError:
            local_refs = set()
            citers = set()

        seed_ids = {center_id, *[pid for pid in local_refs if pid in local_papers], *[pid for pid in citers if pid in local_papers]}
        shared_neighbors = _fetch_shared_neighbors(cfg.index_db, center_id, set(local_papers.keys()), min_shared)
        ranking = defaultdict(float)
        for paper_id in seed_ids:
            if paper_id != center_id:
                ranking[paper_id] += 1000
        for row in shared_neighbors:
            paper_id = str(row.get("paper_id") or "").strip()
            if paper_id not in local_papers:
                continue
            ranking[paper_id] += float(row.get("shared_refs") or 0) * 100.0
            seed_ids.add(paper_id)

        keep_budget = max(max_nodes - 1, 0)
        ordered_neighbors = sorted(
            (paper_id for paper_id in seed_ids if paper_id != center_id),
            key=lambda paper_id: (
                -ranking.get(paper_id, 0.0),
                -(int(local_papers[paper_id].get("citation_count") or 0)),
                -(int(local_papers[paper_id].get("year") or 0)),
                local_papers[paper_id].get("title") or local_papers[paper_id].get("dir_name") or paper_id,
            ),
        )
        candidate_ids = {center_id}
        for paper_id in ordered_neighbors:
            if keep_budget and len(candidate_ids) - 1 >= keep_budget:
                hidden_nodes += 1
                truncated = True
                continue
            candidate_ids.add(paper_id)
    else:
        candidate_ids, seed_truncated, seed_hidden = _project_or_library_candidates(
            cfg,
            local_papers,
            scope=scope,
            project=project,
            max_nodes=max_nodes,
        )
        truncated = seed_truncated
        hidden_nodes += seed_hidden

    if not candidate_ids:
        return _empty_graph(mode="structure", scope=scope, message="No papers available in this scope.")

    nodes_map: dict[str, dict[str, Any]] = {}
    for paper_id in candidate_ids:
        if paper_id not in local_papers:
            continue
        node = _paper_node(local_papers[paper_id])
        node["roles"] = ["paper"]
        node["role"] = "paper"
        nodes_map[paper_id] = node
    if center_id and center_id in nodes_map:
        nodes_map[center_id]["roles"] = ["center"]
        nodes_map[center_id]["role"] = "center"

    pair_data: dict[tuple[str, str], dict[str, Any]] = {}
    for row in _fetch_local_citations(cfg.index_db, candidate_ids):
        source_id = row["source_id"]
        target_id = row["target_id"]
        if source_id == target_id:
            continue
        pair = tuple(sorted((source_id, target_id)))
        data = pair_data.setdefault(
            pair,
            {
                "source": pair[0],
                "target": pair[1],
                "direct_count": 0,
                "shared_refs": 0,
            },
        )
        data["direct_count"] += 1

    for row in _fetch_shared_edges(cfg.index_db, candidate_ids, min_shared):
        pair = tuple(sorted((row["source_id"], row["target_id"])))
        data = pair_data.setdefault(
            pair,
            {
                "source": pair[0],
                "target": pair[1],
                "direct_count": 0,
                "shared_refs": 0,
            },
        )
        data["shared_refs"] = int(row.get("shared_refs") or 0)

    edges: list[dict[str, Any]] = []
    for pair in sorted(pair_data):
        data = pair_data[pair]
        direct_count = int(data.get("direct_count") or 0)
        shared_refs = int(data.get("shared_refs") or 0)
        if direct_count <= 0 and shared_refs < min_shared:
            continue
        relations: list[str] = []
        if direct_count > 0:
            relations.append("direct_citation")
        if shared_refs >= min_shared:
            relations.append("shared_refs")
        weight = direct_count * 1.5 + shared_refs * 1.0
        edges.append(
            {
                "id": _edge_id(data["source"], data["target"], "structure"),
                "source": data["source"],
                "target": data["target"],
                "type": "structure",
                "label": " + ".join(relations) if relations else "structure",
                "relations": relations,
                "direct_count": direct_count,
                "shared_refs": shared_refs,
                "weight": weight,
                "directed": False,
            }
        )

    if not edges:
        message = "No structure edges found in this scope."

    nodes = list(nodes_map.values())
    nodes, edges, extra_truncated, extra_hidden = _truncate_graph(nodes, edges, max_nodes=max_nodes, center_id=center_id)
    truncated = truncated or extra_truncated
    hidden_nodes += extra_hidden
    return _annotate_graph(
        nodes,
        edges,
        mode="structure",
        scope=scope,
        message=message,
        truncated=truncated,
        hidden_nodes=hidden_nodes,
    )


def _topic_model_exists(cfg) -> bool:
    model_dir = cfg.topics_model_dir
    return (model_dir / "bertopic_model.pkl").exists() or (model_dir / "model.pkl").exists()


def _load_topic_model(cfg):
    if not _topic_model_exists(cfg):
        return None
    try:
        from scholaraio.topics import load_model
    except ImportError as exc:
        raise ServiceError(f"Topic model dependencies unavailable: {exc}", status_code=503) from exc
    try:
        return load_model(cfg.topics_model_dir)
    except FileNotFoundError:
        return None


def _build_topic_model(cfg):
    if not cfg.index_db.exists():
        raise ServiceError("Index database not found. Build vectors before creating topic clusters.", status_code=400)
    try:
        from scholaraio.topics import build_topics
    except ImportError as exc:
        raise ServiceError(f"Topic model dependencies unavailable: {exc}", status_code=503) from exc
    return build_topics(cfg.index_db, cfg.papers_dir, save_path=cfg.topics_model_dir, cfg=cfg)


def _topic_keywords(model, topic_id: int, *, limit: int = 6) -> list[str]:
    topic_words = model.get_topic(topic_id)
    if not topic_words:
        return []
    return [word for word, _ in topic_words[:limit]]


def _topic_similarity_scores(model, topic_id: int, allowed_topic_ids: set[int]) -> list[tuple[int, float]]:
    topic_ids = sorted(set(getattr(model, "_topics", [])) - {-1})
    if topic_id not in topic_ids:
        return []

    try:
        sim_matrix = model.topic_similarities_
    except AttributeError:
        try:
            from sklearn.metrics.pairwise import cosine_similarity

            sim_matrix = cosine_similarity(model.c_tf_idf_.toarray())
        except Exception:
            return []

    tid_to_idx = {tid: index for index, tid in enumerate(topic_ids)}
    current_idx = tid_to_idx[topic_id]

    related: list[tuple[int, float]] = []
    for other in topic_ids:
        if other == topic_id or other not in allowed_topic_ids:
            continue
        similarity = float(sim_matrix[current_idx][tid_to_idx[other]])
        if similarity <= 0:
            continue
        related.append((other, similarity))
    related.sort(key=lambda item: (-item[1], item[0]))
    return related


def _topic_similarity_edges(model, topic_ids: set[int]) -> list[dict[str, Any]]:
    selected = sorted(topic_ids)
    if len(selected) < 2:
        return []

    edges: dict[tuple[int, int], dict[str, Any]] = {}
    for topic_id in selected:
        for other_id, similarity in _topic_similarity_scores(model, topic_id, set(selected))[:3]:
            if similarity < 0.08:
                continue
            pair = tuple(sorted((topic_id, other_id)))
            current = edges.get(pair)
            if current and float(current.get("similarity") or 0.0) >= similarity:
                continue
            edges[pair] = {
                "id": _edge_id(f"topic:{pair[0]}", f"topic:{pair[1]}", "topic_similarity"),
                "source": f"topic:{pair[0]}",
                "target": f"topic:{pair[1]}",
                "type": "topic_similarity",
                "label": "topic similarity",
                "weight": round(similarity, 3),
                "similarity": round(similarity, 3),
                "directed": False,
            }
    return list(edges.values())


def _build_topic_graph(
    cfg,
    local_papers: dict[str, dict[str, Any]],
    *,
    scope: str,
    project: str,
    paper_ref: str,
    max_nodes: int,
) -> dict[str, Any]:
    model = _load_topic_model(cfg)
    if model is None:
        return _empty_graph(mode="topic", scope=scope, message="Topic model not found. Build topics to view clustering in Graph.")

    paper_ids = getattr(model, "_paper_ids", [])
    topics_list = getattr(model, "_topics", [])
    metas = getattr(model, "_metas", [])
    topic_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    paper_to_topic: dict[str, int] = {}

    allowed_ids = set(local_papers.keys())
    if scope == "project":
        allowed_ids = _resolve_project_paper_ids(cfg, project)
    center_paper_id = ""
    center_topic_id: int | None = None
    center_topic_node_id = ""
    truncated = False
    hidden_nodes = 0
    message = ""

    if scope == "paper":
        if not (paper_ref or "").strip():
            raise ServiceError("paper_ref is required for paper scope", status_code=400)
        center_dir = resolve_paper_dir(cfg, paper_ref)
        center_meta = read_meta(center_dir)
        center_paper_id = str(center_meta.get("id") or "").strip()
        if not center_paper_id:
            raise ServiceError("Paper id is missing in meta.json", status_code=400)

    for index, paper_id in enumerate(paper_ids):
        if index >= len(topics_list) or index >= len(metas):
            continue
        topic_id = topics_list[index]
        if topic_id == -1:
            continue
        if paper_id not in local_papers:
            continue
        if scope != "paper" and paper_id not in allowed_ids:
            continue
        meta = metas[index]
        topic_groups[int(topic_id)].append(_topic_paper_brief(meta, local_papers))
        paper_to_topic[paper_id] = int(topic_id)

    if scope == "paper":
        center_topic_id = paper_to_topic.get(center_paper_id)
        if center_topic_id is None:
            return _empty_graph(mode="topic", scope=scope, message="This paper is not assigned to any saved topic cluster yet.")
        selected_topic_ids = {center_topic_id}
        for other_id, similarity in _topic_similarity_scores(model, center_topic_id, set(topic_groups)):
            if similarity < 0.08:
                continue
            if len(selected_topic_ids) >= max_nodes:
                hidden_nodes += 1
                truncated = True
                continue
            selected_topic_ids.add(other_id)
        center_topic_node_id = f"topic:{center_topic_id}"
    else:
        ordered_topics = sorted(
            topic_groups.items(),
            key=lambda item: (
                -len(item[1]),
                -max((int(paper.get("citation_count") or 0) for paper in item[1]), default=0),
                item[0],
            ),
        )
        selected_topic_ids = {topic_id for topic_id, _ in ordered_topics[:max_nodes]}
        if len(ordered_topics) > len(selected_topic_ids):
            truncated = True
            hidden_nodes += len(ordered_topics) - len(selected_topic_ids)

    if not selected_topic_ids:
        return _empty_graph(mode="topic", scope=scope, message="No clustered papers available in this scope yet.")

    nodes: list[dict[str, Any]] = []
    for topic_id in sorted(selected_topic_ids):
        papers = topic_groups.get(topic_id, [])
        papers.sort(
            key=lambda paper: (
                -(int(paper.get("citation_count") or 0)),
                -(int(paper.get("year") or 0)),
                paper.get("title") or paper.get("paper_ref") or "",
            )
        )
        center = topic_id == center_topic_id if center_topic_id is not None else False
        nodes.append(_topic_node(topic_id, keywords=_topic_keywords(model, topic_id), papers=papers, center=center))

    edges = _topic_similarity_edges(model, selected_topic_ids)
    if not edges and len(nodes) == 1 and center_topic_id is not None:
        message = "This paper maps to a single saved topic with no related-topic edges above the display threshold."
    elif not edges:
        message = "Topic graph has no related-topic edges above the display threshold yet."

    nodes, edges, extra_truncated, extra_hidden = _truncate_graph(nodes, edges, max_nodes=max_nodes, center_id=center_topic_node_id)
    truncated = truncated or extra_truncated
    hidden_nodes += extra_hidden
    return _annotate_graph(
        nodes,
        edges,
        mode="topic",
        scope=scope,
        message=message,
        truncated=truncated,
        hidden_nodes=hidden_nodes,
    )


def get_graph(
    cfg,
    *,
    mode: str = "citation",
    scope: str = "library",
    project: str = "",
    paper_ref: str = "",
    min_shared: int = 2,
    max_nodes: int = 80,
) -> dict[str, Any]:
    """Return a dynamic graph payload for the web UI."""
    normalized_mode = _normalize_mode(mode)
    normalized_scope = _normalize_scope(scope)
    min_shared = _safe_int(min_shared, 2, minimum=1, maximum=20)
    max_nodes = _safe_int(max_nodes, 80, minimum=5, maximum=300)

    local_papers = _load_local_papers(cfg)
    if normalized_mode == "citation":
        return _build_citation_graph(
            cfg,
            local_papers,
            scope=normalized_scope,
            project=project,
            paper_ref=paper_ref,
            max_nodes=max_nodes,
        )
    if normalized_mode == "structure":
        return _build_structure_graph(
            cfg,
            local_papers,
            scope=normalized_scope,
            project=project,
            paper_ref=paper_ref,
            min_shared=min_shared,
            max_nodes=max_nodes,
        )
    return _build_topic_graph(
        cfg,
        local_papers,
        scope=normalized_scope,
        project=project,
        paper_ref=paper_ref,
        max_nodes=max_nodes,
    )


def build_graph(
    cfg,
    *,
    mode: str = "citation",
    scope: str = "library",
    project: str = "",
    paper_ref: str = "",
    min_shared: int = 2,
    max_nodes: int = 80,
) -> dict[str, Any]:
    """Return graph data and summary counts for compatibility with the old rebuild route."""
    normalized_mode = _normalize_mode(mode)
    if normalized_mode == "topic":
        _build_topic_model(cfg)
    graph = get_graph(
        cfg,
        mode=normalized_mode,
        scope=scope,
        project=project,
        paper_ref=paper_ref,
        min_shared=min_shared,
        max_nodes=max_nodes,
    )
    return {
        "success": True,
        "nodes": len(graph.get("nodes", [])),
        "edges": len(graph.get("edges", [])),
        "graph": graph,
    }

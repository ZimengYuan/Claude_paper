"""Knowledge base management for cross-paper notes and knowledge graph.

This module provides:
- Global knowledge base (knowledge.md)
- Tag registry (tags.json)
- Knowledge graph (knowledge_graph.json)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

_log = logging.getLogger(__name__)


# ============================================================================
#  Knowledge Base
# ============================================================================


def knowledge_file(root: Path) -> Path:
    """Return the knowledge.md path."""
    return root / "data" / "knowledge.md"


def tags_file(root: Path) -> Path:
    """Return the tags.json path."""
    return root / "data" / "tags.json"


def knowledge_graph_file(root: Path) -> Path:
    """Return the knowledge_graph.json path."""
    return root / "data" / "knowledge_graph.json"


def read_knowledge(root: Path) -> str:
    """Read the global knowledge base.

    Args:
        root: Project root directory.

    Returns:
        Knowledge base content, empty string if not exists.
    """
    p = knowledge_file(root)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""


def write_knowledge(root: Path, content: str) -> None:
    """Write the global knowledge base.

    Args:
        root: Project root directory.
        content: Knowledge base content.
    """
    p = knowledge_file(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def append_knowledge(root: Path, note: str, category: str = "general") -> None:
    """Append a note to the knowledge base.

    Args:
        root: Project root directory.
        note: Note content to append.
        category: Category for organization (default: "general").
    """
    import datetime

    content = read_knowledge(root)

    # Add new note with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    new_section = f"\n## {timestamp} | {category}\n\n{note}\n"

    if content:
        content += new_section
    else:
        content = f"# Knowledge Base\n{new_section}"

    write_knowledge(root, content)
    _log.info("Added note to knowledge base")


def search_knowledge(root: Path, query: str) -> list[dict]:
    """Search the knowledge base.

    Args:
        root: Project root directory.
        query: Search query.

    Returns:
        List of matching notes with context.
    """
    content = read_knowledge(root)
    if not content:
        return []

    query_lower = query.lower()
    lines = content.split("\n")
    results = []
    current_section = ""
    current_content = []

    for line in lines:
        if line.startswith("## "):
            # Save previous section
            if current_content:
                section_text = " ".join(current_content)
                if query_lower in section_text.lower():
                    results.append({
                        "section": current_section,
                        "content": section_text,
                    })
            current_section = line[3:].strip()
            current_content = []
        elif line.strip():
            current_content.append(line.strip())

    # Check last section
    if current_content:
        section_text = " ".join(current_content)
        if query_lower in section_text.lower():
            results.append({
                "section": current_section,
                "content": section_text,
            })

    return results


# ============================================================================
#  Tag Registry
# ============================================================================


def read_tags_registry(root: Path) -> dict:
    """Read the tag registry.

    Args:
        root: Project root directory.

    Returns:
        Tag registry dict with tag metadata.
    """
    p = tags_file(root)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def write_tags_registry(root: Path, data: dict) -> None:
    """Write the tag registry.

    Args:
        root: Project root directory.
        data: Tag registry data.
    """
    p = tags_file(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def register_tag(root: Path, tag: str, description: str = "", color: str = "") -> None:
    """Register a new tag in the global registry.

    Args:
        root: Project root directory.
        tag: Tag name.
        description: Tag description.
        color: Optional color hex code.
    """
    registry = read_tags_registry(root)

    if tag not in registry:
        registry[tag] = {
            "description": description,
            "color": color,
            "paper_count": 0,
        }
    else:
        registry[tag]["description"] = description or registry[tag].get("description", "")
        registry[tag]["color"] = color or registry[tag].get("color", "")

    write_tags_registry(root, registry)
    _log.info("Registered tag: %s", tag)


def update_tag_counts(root: Path, tag_counts: dict[str, int]) -> None:
    """Update paper counts for all tags.

    Args:
        root: Project root directory.
        tag_counts: Dict of tag -> paper count.
    """
    registry = read_tags_registry(root)

    for tag, count in tag_counts.items():
        if tag in registry:
            registry[tag]["paper_count"] = count
        else:
            registry[tag] = {
                "description": "",
                "color": "",
                "paper_count": count,
            }

    write_tags_registry(root, registry)


def list_tags(root: Path) -> list[dict]:
    """List all registered tags.

    Args:
        root: Project root directory.

    Returns:
        List of tag info dicts.
    """
    registry = read_tags_registry(root)
    return [
        {"tag": tag, **info}
        for tag, info in registry.items()
    ]


# ============================================================================
#  Knowledge Graph
# ============================================================================


def read_knowledge_graph(root: Path) -> dict:
    """Read the knowledge graph.

    Args:
        root: Project root directory.

    Returns:
        Knowledge graph data.
    """
    p = knowledge_graph_file(root)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"nodes": [], "edges": []}
    return {"nodes": [], "edges": []}


def write_knowledge_graph(root: Path, data: dict) -> None:
    """Write the knowledge graph.

    Args:
        root: Project root directory.
        data: Knowledge graph data.
    """
    p = knowledge_graph_file(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_paper_to_graph(root: Path, paper_id: str, title: str, concepts: list[str] = None) -> None:
    """Add a paper node to the knowledge graph.

    Args:
        root: Project root directory.
        paper_id: Paper UUID or directory name.
        title: Paper title.
        concepts: List of concept tags.
    """
    graph = read_knowledge_graph(root)

    # Check if node already exists
    nodes = graph.get("nodes", [])
    for node in nodes:
        if node.get("id") == paper_id:
            node["title"] = title
            node["concepts"] = concepts or []
            break
    else:
        nodes.append({
            "id": paper_id,
            "title": title,
            "type": "paper",
            "concepts": concepts or [],
        })

    graph["nodes"] = nodes
    write_knowledge_graph(root, graph)


def add_relation(root: Path, source: str, target: str, relation_type: str) -> None:
    """Add a relation edge to the knowledge graph.

    Args:
        root: Project root directory.
        source: Source node ID.
        target: Target node ID.
        relation_type: Type of relation (e.g., "cites", "related", "builds_on").
    """
    graph = read_knowledge_graph(root)

    edges = graph.get("edges", [])
    edges.append({
        "source": source,
        "target": target,
        "type": relation_type,
    })

    graph["edges"] = edges
    write_knowledge_graph(root, graph)


def add_concept(root: Path, concept: str, description: str = "") -> None:
    """Add a concept node to the knowledge graph.

    Args:
        root: Project root directory.
        concept: Concept name.
        description: Concept description.
    """
    graph = read_knowledge_graph(root)

    nodes = graph.get("nodes", [])
    for node in nodes:
        if node.get("id") == f"concept:{concept}":
            node["description"] = description
            break
    else:
        nodes.append({
            "id": f"concept:{concept}",
            "name": concept,
            "type": "concept",
            "description": description,
        })

    graph["nodes"] = nodes
    write_knowledge_graph(root, graph)


def link_paper_concept(root: Path, paper_id: str, concept: str) -> None:
    """Link a paper to a concept.

    Args:
        root: Project root directory.
        paper_id: Paper ID.
        concept: Concept name.
    """
    # Ensure concept exists
    add_concept(root, concept)

    # Add relation
    add_relation(root, paper_id, f"concept:{concept}", "has_concept")


def get_knowledge_graph(root: Path) -> dict:
    """Get the complete knowledge graph.

    Args:
        root: Project root directory.

    Returns:
        Knowledge graph with nodes and edges.
    """
    return read_knowledge_graph(root)


def build_paper_graph(root: Path) -> dict:
    """Build knowledge graph from all papers.

    Args:
        root: Project root directory.

    Returns:
        Knowledge graph with all papers and their tags/concepts.
    """
    from .papers import iter_paper_dirs, read_meta, get_tags

    papers_dir = root / "data" / "papers"
    if not papers_dir.exists():
        return {"nodes": [], "edges": []}

    graph = {"nodes": [], "edges": []}

    for paper_d in iter_paper_dirs(papers_dir):
        meta = read_meta(paper_d)
        paper_id = meta.get("id", paper_d.name)
        title = meta.get("title", paper_d.name)
        tags = get_tags(paper_d)

        # Add paper node
        graph["nodes"].append({
            "id": paper_id,
            "title": title,
            "type": "paper",
            "tags": tags,
        })

        # Link to concepts (tags)
        for tag in tags:
            concept_id = f"concept:{tag}"
            # Ensure concept exists
            concept_exists = any(n.get("id") == concept_id for n in graph["nodes"])
            if not concept_exists:
                graph["nodes"].append({
                    "id": concept_id,
                    "name": tag,
                    "type": "concept",
                })

            # Add edge
            graph["edges"].append({
                "source": paper_id,
                "target": concept_id,
                "type": "has_tag",
            })

    write_knowledge_graph(root, graph)
    return graph

from __future__ import annotations

from scholaraio.workspace import list_workspaces, read_paper_ids


def list_projects(cfg) -> list[dict]:
    """Return read-only project scopes derived from workspace subsets."""
    ws_root = cfg._root / "workspace"
    projects: list[dict] = []
    for name in list_workspaces(ws_root):
        ws_dir = ws_root / name
        paper_count = len(read_paper_ids(ws_dir))
        if paper_count == 0:
            continue
        projects.append({"name": name, "paper_count": paper_count})
    return projects

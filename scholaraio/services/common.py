from __future__ import annotations

from pathlib import Path

from scholaraio.index import lookup_paper
from scholaraio.papers import iter_paper_dirs, read_meta


class ServiceError(RuntimeError):
    """Application-level error with an HTTP-friendly status code."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def resolve_paper_dir(cfg, paper_ref: str) -> Path:
    """Resolve dir_name, UUID, or DOI to a paper directory.

    Args:
        cfg: Loaded ScholarAIO config.
        paper_ref: Human-entered paper reference.

    Returns:
        Resolved paper directory path.

    Raises:
        ServiceError: If the paper cannot be found.
    """
    papers_dir = cfg.papers_dir

    direct = papers_dir / paper_ref
    if (direct / "meta.json").exists():
        return direct

    try:
        reg = lookup_paper(cfg.index_db, paper_ref)
    except FileNotFoundError:
        reg = None
    if reg:
        resolved = papers_dir / reg["dir_name"]
        if (resolved / "meta.json").exists():
            return resolved

    for pdir in iter_paper_dirs(papers_dir):
        try:
            data = read_meta(pdir)
        except (ValueError, FileNotFoundError):
            continue
        if data.get("id") == paper_ref or data.get("doi") == paper_ref:
            return pdir

    raise ServiceError(f"Paper not found: {paper_ref}", status_code=404)

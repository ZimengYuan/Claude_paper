from __future__ import annotations

import json
from pathlib import Path

from scholaraio.config import Config
from scholaraio.ingest.metadata import PaperMetadata
from scholaraio.ingest.pipeline import (
    InboxCtx,
    StepResult,
    _collect_existing_dois,
    _collect_existing_titles,
    step_ingest,
)


def _make_cfg(tmp_path: Path) -> Config:
    cfg = Config()
    cfg._root = tmp_path
    cfg.paths.papers_dir = "papers"
    cfg.paths.index_db = "index.db"
    return cfg


def test_step_ingest_moves_duplicate_title_to_pending(tmp_path: Path, tmp_papers: Path) -> None:
    cfg = _make_cfg(tmp_path)
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir()
    pending_dir = tmp_path / "pending"

    md_path = inbox_dir / "duplicate.md"
    md_path.write_text("# Turbulence modeling in boundary layers\n\nnew content", encoding="utf-8")

    meta = PaperMetadata(
        title="Turbulence modeling in boundary layers",
        authors=["Jane Duplicate"],
        first_author="Jane Duplicate",
        first_author_lastname="Duplicate",
        year=2025,
        doi="10.9999/new-paper",
    )
    ctx = InboxCtx(
        pdf_path=None,
        inbox_dir=inbox_dir,
        papers_dir=tmp_papers,
        existing_dois=_collect_existing_dois(tmp_papers),
        existing_titles=_collect_existing_titles(tmp_papers),
        cfg=cfg,
        opts={},
        pending_dir=pending_dir,
        md_path=md_path,
        meta=meta,
    )

    result = step_ingest(ctx)

    assert result == StepResult.FAIL
    assert ctx.status == "needs_review"
    pending_json = pending_dir / "duplicate" / "pending.json"
    assert pending_json.exists()
    data = json.loads(pending_json.read_text(encoding="utf-8"))
    assert data["issue"] == "duplicate_title"
    assert "Smith-2023-Turbulence" in data["duplicate_title_of"]


def test_step_ingest_moves_section_heading_title_to_pending(tmp_path: Path) -> None:
    cfg = _make_cfg(tmp_path)
    papers_dir = tmp_path / "papers"
    papers_dir.mkdir()
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir()
    pending_dir = tmp_path / "pending"

    md_path = inbox_dir / "intro.md"
    md_path.write_text("# 1Introduction\n\nbad extraction", encoding="utf-8")

    meta = PaperMetadata(
        title="1Introduction",
        authors=["Humanoid Parkour Learning"],
        first_author="Humanoid Parkour Learning",
        first_author_lastname="Learning",
        year=2026,
        doi="10.1515/9783112218655-001",
    )
    ctx = InboxCtx(
        pdf_path=None,
        inbox_dir=inbox_dir,
        papers_dir=papers_dir,
        existing_dois={},
        existing_titles={},
        cfg=cfg,
        opts={},
        pending_dir=pending_dir,
        md_path=md_path,
        meta=meta,
    )

    result = step_ingest(ctx)

    assert result == StepResult.FAIL
    assert ctx.status == "needs_review"
    pending_json = pending_dir / "intro" / "pending.json"
    assert pending_json.exists()
    data = json.loads(pending_json.read_text(encoding="utf-8"))
    assert data["issue"] == "metadata_quality"
    assert "section_heading_title" in data["quality_rules"]

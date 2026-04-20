from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.update_read_status_snapshot import update_read_status_snapshot


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "scholaraio" / "web"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_update_read_status_snapshot_updates_static_and_meta(tmp_path: Path) -> None:
    site_data = tmp_path / "scholaraio" / "web" / "public" / "site-data"
    papers_dir = tmp_path / "data" / "papers"

    _write_json(
        site_data / "library.json",
        {
            "papers": [
                {
                    "route_id": "paper-1",
                    "paper_id": "uuid-1",
                    "dir_name": "Smith-2026-Example",
                    "title": "Example Paper",
                    "read_status": "unread",
                }
            ]
        },
    )
    _write_json(
        site_data / "papers" / "paper-1.json",
        {
            "dir_name": "Smith-2026-Example",
            "title": "Example Paper",
            "read_status": "unread",
        },
    )
    _write_json(
        site_data / "todo-cards.json",
        {
            "cards": [
                {
                    "route_id": "todo-1",
                    "paper_route_id": "paper-1",
                    "title": "Example Paper",
                    "read_status": "unread",
                }
            ]
        },
    )
    _write_json(
        papers_dir / "Smith-2026-Example" / "meta.json",
        {
            "id": "uuid-1",
            "title": "Example Paper",
            "read_status": "unread",
        },
    )

    result = update_read_status_snapshot(root=tmp_path, paper_ref="/paper/paper-1", status="read")

    assert result["changed"] == {
        "library": 1,
        "paper_details": 1,
        "todo_cards": 1,
        "paper_meta": 1,
    }
    assert _read_json(site_data / "library.json")["papers"][0]["read_status"] == "read"
    assert _read_json(site_data / "papers" / "paper-1.json")["read_status"] == "read"
    assert _read_json(site_data / "todo-cards.json")["cards"][0]["read_status"] == "read"
    assert _read_json(papers_dir / "Smith-2026-Example" / "meta.json")["read_status"] == "read"


def test_update_read_status_snapshot_matches_doi_slug(tmp_path: Path) -> None:
    site_data = tmp_path / "scholaraio" / "web" / "public" / "site-data"
    _write_json(
        site_data / "library.json",
        {
            "papers": [
                {
                    "route_id": "10.1126-scirobotics.adv3604",
                    "doi": "10.1126/scirobotics.adv3604",
                    "read_status": "unread",
                }
            ]
        },
    )

    result = update_read_status_snapshot(
        root=tmp_path,
        paper_ref="10.1126-scirobotics.adv3604",
        status="read",
    )

    assert result["changed"]["library"] == 1
    assert _read_json(site_data / "library.json")["papers"][0]["read_status"] == "read"


def test_read_status_workflow_is_static_pages_compatible() -> None:
    workflow = (ROOT / ".github" / "workflows" / "read-status.yml").read_text(encoding="utf-8")
    pages = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch" in workflow
    assert "scripts/update_read_status_snapshot.py" in workflow
    assert "actions/deploy-pages@v4" in workflow
    assert "NUXT_PUBLIC_GITHUB_READ_STATUS_WORKFLOW" in pages


def test_static_page_uses_github_workflow_writeback() -> None:
    index_page = (WEB_ROOT / "pages" / "index.vue").read_text(encoding="utf-8")
    paper_page = (WEB_ROOT / "pages" / "paper" / "[id].vue").read_text(encoding="utf-8")
    todo_page = (WEB_ROOT / "pages" / "todo" / "[id].vue").read_text(encoding="utf-8")
    composable = (WEB_ROOT / "composables" / "useStaticSiteData.js").read_text(encoding="utf-8")

    assert "api.github.com/repos" in index_page
    assert "toggleCardReadStatus" in index_page
    assert '@click.stop.prevent="toggleCardReadStatus(card)"' in index_page
    assert "api.github.com/repos" in paper_page
    assert "workflow_dispatch" in paper_page
    assert "setReadStatusOverride" in paper_page
    assert "api.github.com/repos" in todo_page
    assert "workflow_dispatch" in todo_page
    assert "setReadStatusOverride" in todo_page
    assert "paper_ref: routeId.value" in todo_page
    assert "标记已读" in todo_page
    assert "READ_STATUS_OVERRIDES_KEY" in composable


def test_static_site_data_composable_is_valid_js() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    subprocess.run(
        [node, "--check", str(WEB_ROOT / "composables" / "useStaticSiteData.js")],
        cwd=WEB_ROOT,
        check=True,
    )

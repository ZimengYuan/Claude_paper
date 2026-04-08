from __future__ import annotations

import json
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def test_library_snapshot_not_empty() -> None:
    root = _root()
    library_path = root / 'scholaraio' / 'web' / 'public' / 'site-data' / 'library.json'
    payload = _read_json(library_path)

    papers = payload.get('papers') or []
    assert isinstance(papers, list)
    assert len(papers) > 0


def test_graph_manifest_and_files_exist() -> None:
    root = _root()
    graph_index = root / 'scholaraio' / 'web' / 'public' / 'site-data' / 'graphs' / 'index.json'
    payload = _read_json(graph_index)

    library = payload.get('library') or {}
    for key in ('citation', 'structure', 'topic'):
        rel = library.get(key)
        assert isinstance(rel, str) and rel.strip(), f'missing graph path for {key}'
        fp = root / 'scholaraio' / 'web' / 'public' / 'site-data' / rel
        assert fp.exists(), f'graph file not found: {rel}'
        graph_payload = _read_json(fp)
        assert isinstance(graph_payload.get('nodes'), list)
        assert isinstance(graph_payload.get('edges'), list)


def test_navigation_no_knowledge_entry() -> None:
    root = _root()
    app_vue = (root / 'scholaraio' / 'web' / 'app.vue').read_text(encoding='utf-8')
    assert '/knowledge' not in app_vue


def test_nuxt_prerender_without_knowledge_base_route() -> None:
    root = _root()
    config = (root / 'scholaraio' / 'web' / 'nuxt.config.ts').read_text(encoding='utf-8')
    assert "'/knowledge'" not in config

from __future__ import annotations

import json
import re
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def _site_data_root(root: Path) -> Path:
    return root / 'scholaraio' / 'web' / 'public' / 'site-data'


def test_library_snapshot_not_empty() -> None:
    root = _root()
    library_path = root / 'scholaraio' / 'web' / 'public' / 'site-data' / 'library.json'
    payload = _read_json(library_path)

    papers = payload.get('papers') or []
    assert isinstance(papers, list)
    assert len(papers) > 0


def test_graph_manifest_and_files_exist() -> None:
    root = _root()
    graph_index = _site_data_root(root) / 'graphs' / 'index.json'
    payload = _read_json(graph_index)

    library = payload.get('library') or {}
    for key in ('citation', 'structure', 'topic'):
        rel = library.get(key)
        assert isinstance(rel, str) and rel.strip(), f'missing graph path for {key}'
        fp = _site_data_root(root) / rel
        assert fp.exists(), f'graph file not found: {rel}'
        graph_payload = _read_json(fp)
        assert isinstance(graph_payload.get('nodes'), list)
        assert isinstance(graph_payload.get('edges'), list)


def test_todo_cards_schema_and_id_quality() -> None:
    root = _root()
    todo_cards = _site_data_root(root) / 'todo-cards.json'
    payload = _read_json(todo_cards)

    cards = payload.get('cards') or []
    assert isinstance(cards, list) and cards, 'todo cards must be a non-empty list'

    route_ids = []
    doi_re = re.compile(r'^(10\.[^\s]+|https?://doi\.org/.+)$', re.IGNORECASE)

    for card in cards:
        route_id = str(card.get('route_id') or '').strip()
        title = str(card.get('title') or '').strip()
        read_status = str(card.get('read_status') or '').strip()

        assert route_id, 'route_id is required'
        assert title, f'title is required for {route_id}'
        assert read_status in {'unread', 'reading', 'done'}, f'invalid read_status for {route_id}: {read_status}'

        doi = str(card.get('doi') or '').strip()
        if doi:
            assert doi_re.match(doi), f'invalid DOI format for {route_id}: {doi}'

        route_ids.append(route_id)

    assert len(route_ids) == len(set(route_ids)), 'duplicate route_id in todo cards'


def test_graph_edges_reference_existing_nodes() -> None:
    root = _root()
    graph_index = _site_data_root(root) / 'graphs' / 'index.json'
    payload = _read_json(graph_index)
    library = payload.get('library') or {}

    for key in ('citation', 'structure', 'topic'):
        rel = library.get(key)
        if not rel:
            continue
        fp = _site_data_root(root) / rel
        graph_payload = _read_json(fp)
        nodes = graph_payload.get('nodes') or []
        edges = graph_payload.get('edges') or []

        node_ids = {str(node.get('id') or '').strip() for node in nodes if str(node.get('id') or '').strip()}
        assert len(node_ids) == len(nodes), f'duplicate/empty node id found in {rel}'

        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            source_id = str(source.get('id') if isinstance(source, dict) else source or '').strip()
            target_id = str(target.get('id') if isinstance(target, dict) else target or '').strip()
            assert source_id in node_ids, f'edge source not found in nodes for {rel}: {source_id}'
            assert target_id in node_ids, f'edge target not found in nodes for {rel}: {target_id}'


def test_navigation_no_knowledge_entry() -> None:
    root = _root()
    app_vue = (root / 'scholaraio' / 'web' / 'app.vue').read_text(encoding='utf-8')
    assert '/knowledge' not in app_vue


def test_nuxt_prerender_without_knowledge_base_route() -> None:
    root = _root()
    config = (root / 'scholaraio' / 'web' / 'nuxt.config.ts').read_text(encoding='utf-8')
    assert "'/knowledge'" not in config

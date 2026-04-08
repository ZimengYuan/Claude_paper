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


def test_navigation_no_knowledge_entry() -> None:
    root = _root()
    app_vue = (root / 'scholaraio' / 'web' / 'app.vue').read_text(encoding='utf-8')
    assert '/knowledge' not in app_vue
    assert '/graph' not in app_vue


def test_nuxt_prerender_without_knowledge_base_route() -> None:
    root = _root()
    config = (root / 'scholaraio' / 'web' / 'nuxt.config.ts').read_text(encoding='utf-8')
    assert "'/knowledge'" not in config
    assert "const baseRoutes = ['/', '/explore']" in config


def test_graph_route_redirected_to_explore() -> None:
    root = _root()
    config = (root / 'scholaraio' / 'web' / 'nuxt.config.ts').read_text(encoding='utf-8')
    assert "'/graph': { redirect: '/explore' }" in config
    assert "'/graph/**': { redirect: '/explore' }" in config

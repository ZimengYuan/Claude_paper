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
        assert read_status in {'unread', 'read'}, f'invalid read_status for {route_id}: {read_status}'

        doi = str(card.get('doi') or '').strip()
        if doi:
            assert doi_re.match(doi), f'invalid DOI format for {route_id}: {doi}'

        route_ids.append(route_id)

    assert len(route_ids) == len(set(route_ids)), 'duplicate route_id in todo cards'
    assert (payload.get('collection') or {}).get('count') == len(cards), 'todo collection count mismatch'


def test_navigation_no_knowledge_entry() -> None:
    root = _root()
    app_vue = (root / 'scholaraio' / 'web' / 'app.vue').read_text(encoding='utf-8')
    assert '/knowledge' not in app_vue
    assert '/graph' not in app_vue


def test_nuxt_prerender_without_knowledge_base_route() -> None:
    root = _root()
    config = (root / 'scholaraio' / 'web' / 'nuxt.config.ts').read_text(encoding='utf-8')
    assert "'/knowledge'" not in config
    assert "const baseRoutes = ['/', '/explore', '/graph']" in config


def test_graph_route_redirected_to_explore() -> None:
    root = _root()
    config = (root / 'scholaraio' / 'web' / 'nuxt.config.ts').read_text(encoding='utf-8')
    graph_page = (root / 'scholaraio' / 'web' / 'pages' / 'graph.vue').read_text(encoding='utf-8')
    assert "'/graph': { redirect: '/explore' }" in config
    assert "'/graph/**': { redirect: '/explore' }" in config
    assert "navigateTo('/explore'" in graph_page


def test_todo_card_layout_avoids_stretched_blank_cards() -> None:
    root = _root()
    app_vue = (root / 'scholaraio' / 'web' / 'app.vue').read_text(encoding='utf-8')

    card_grid = re.search(r'\.aio-card-grid\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    card_block = re.search(r'\.aio-card\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    card_footer = re.search(r'\.aio-card-footer\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    accent_bar = re.search(r'\.aio-card::before\s*\{(?P<body>.*?)\n\}', app_vue, re.S)

    assert card_grid and 'align-items: start;' in card_grid.group('body')
    assert card_block and 'min-height:' not in card_block.group('body')
    assert card_footer and 'margin-top: auto;' not in card_footer.group('body')
    assert accent_bar and 'inset: 0 auto 0 0;' in accent_bar.group('body')
    assert '18px auto 18px' not in accent_bar.group('body')


def test_todo_compass_routes_use_internal_paths() -> None:
    root = _root()
    todo_page = (root / 'scholaraio' / 'web' / 'pages' / 'todo' / '[id].vue').read_text(encoding='utf-8')
    compass_page = (root / 'scholaraio' / 'web' / 'pages' / 'compass' / '[id].vue').read_text(encoding='utf-8')

    assert "const compassDetailLink = computed(() => '/compass/' + routeId.value)" in todo_page
    assert '<NuxtLink class="aio-button" :to="compassDetailLink">打开完整 Compass</NuxtLink>' in todo_page
    assert "const goBack = () => navigateTo('/')" in todo_page
    assert "runtimeConfig.app.baseURL" not in todo_page

    assert "const todoDetailPath = computed(() => '/todo/' + routeId.value)" in compass_page
    assert 'const goBackToTodo = () => navigateTo(todoDetailPath.value)' in compass_page
    assert "runtimeConfig.app.baseURL" not in compass_page


def test_compass_page_uses_todo_design_system() -> None:
    root = _root()
    compass_page = (root / 'scholaraio' / 'web' / 'pages' / 'compass' / '[id].vue').read_text(encoding='utf-8')
    config = (root / 'scholaraio' / 'web' / 'nuxt.config.ts').read_text(encoding='utf-8')

    assert 'class="aio-detail-page aio-compass-detail-page"' in compass_page
    assert 'class="aio-paper-header"' in compass_page
    assert 'class="aio-compass-card"' in compass_page
    assert 'class="aio-note-section"' in compass_page
    assert 'rounded-[32px]' not in compass_page
    assert 'bg-[linear-gradient' not in compass_page
    assert 'text-slate-' not in compass_page
    assert 'todoRouteIds.map((routeId: string) => `/todo/${routeId}`)' in config
    assert 'todoRouteIds.map((routeId: string) => `/compass/${routeId}`)' in config

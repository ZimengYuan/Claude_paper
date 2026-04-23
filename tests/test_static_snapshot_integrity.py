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


def test_graph_route_redirected_to_explore_without_page() -> None:
    root = _root()
    config = (root / 'scholaraio' / 'web' / 'nuxt.config.ts').read_text(encoding='utf-8')
    graph_page = root / 'scholaraio' / 'web' / 'pages' / 'graph.vue'
    assert "'/graph': { redirect: '/explore' }" in config
    assert "'/graph/**': { redirect: '/explore' }" in config
    assert not graph_page.exists()


def test_static_snapshot_omits_unused_legacy_payloads() -> None:
    site_data = _site_data_root(_root())
    assert not (site_data / '.generated').exists()
    assert not (site_data / 'knowledge.json').exists()
    assert not (site_data / 'explore' / 'index.json').exists()
    assert not (site_data / 'graphs').exists()


def test_todo_card_layout_keeps_queue_cards_aligned() -> None:
    root = _root()
    app_vue = (root / 'scholaraio' / 'web' / 'app.vue').read_text(encoding='utf-8')

    card_grid = re.search(r'\.aio-card-grid\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    card_block = re.search(r'\.aio-card\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    todo_card = re.search(r'\.aio-todo-card\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    todo_title = re.search(r'\.aio-todo-card \.aio-card-title\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    todo_summary = re.search(r'\.aio-todo-card \.aio-card-summary\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    todo_footer = re.search(r'\.aio-todo-card \.aio-card-footer\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    card_footer = re.search(r'^\.aio-card-footer\s*\{(?P<body>.*?)\n\}', app_vue, re.S | re.M)
    accent_bar = re.search(r'\.aio-card::before\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    hero = re.search(r'\.aio-hero\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    hero_stats = re.search(r'\.aio-hero-stats\s*\{(?P<body>.*?)\n\}', app_vue, re.S)

    assert card_grid and 'align-items: stretch;' in card_grid.group('body')
    assert card_block and 'min-height:' not in card_block.group('body')
    assert todo_card and 'min-height: 418px;' in todo_card.group('body')
    assert todo_title and '-webkit-line-clamp: 3;' in todo_title.group('body')
    assert todo_summary and 'min-height: 130px;' in todo_summary.group('body')
    assert todo_footer and 'margin-top: auto;' in todo_footer.group('body')
    assert card_footer and 'margin-top: 18px;' in card_footer.group('body')
    assert accent_bar and 'inset: 0 auto 0 0;' in accent_bar.group('body')
    assert '18px auto 18px' not in accent_bar.group('body')
    assert hero and 'flex-direction: column;' in hero.group('body')
    assert hero and 'grid-template-columns: minmax(0, 1fr) auto;' not in hero.group('body')
    assert hero_stats and 'grid-template-columns: repeat(3, minmax(0, 1fr));' in hero_stats.group('body')


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
    assert 'class="aio-metric-panel"' in compass_page
    assert 'class="aio-rating-grid"' not in compass_page
    assert 'rounded-[32px]' not in compass_page
    assert 'bg-[linear-gradient' not in compass_page
    assert 'text-slate-' not in compass_page
    assert 'todoRouteIds.map((routeId: string) => `/todo/${routeId}`)' in config
    assert 'todoRouteIds.map((routeId: string) => `/compass/${routeId}`)' in config


def test_compass_page_hides_duplicate_and_empty_material() -> None:
    root = _root()
    compass_page = (root / 'scholaraio' / 'web' / 'pages' / 'compass' / '[id].vue').read_text(encoding='utf-8')
    app_vue = (root / 'scholaraio' / 'web' / 'app.vue').read_text(encoding='utf-8')
    template = compass_page.split('<script setup>')[0]

    assert 'showTodoSummarySnippet' not in compass_page
    assert 'heroMaterialEntries' not in compass_page
    assert 'heroStatusText' not in compass_page
    assert '查看原始 Score Report 文本' not in compass_page
    assert '当前静态快照里还没有这篇论文的评分报告' not in compass_page
    assert '当前静态快照里还没有这篇论文的可读报告' not in compass_page
    assert '材料缺失' not in compass_page
    assert 'structuredScore.snapshot' not in template
    assert 'structuredReport.snapshot' not in template
    assert 'class="aio-empty-note"' not in template
    assert 'class="aio-compass-empty"' in compass_page
    assert 'border: 1px dashed' not in app_vue.split('.aio-compass-empty')[1].split('.aio-compass-empty h2')[0]
    assert 'v-if="hasVisibleScoreContent"' in compass_page
    assert 'v-if="hasVisibleReadableContent"' in compass_page
    assert 'visiblePeers' in compass_page
    assert 'visibleResources' in compass_page
    assert '目前还没有足够证据支持其具备奠基性影响' in compass_page
    assert '低优先级，除非你正好关注这条技术线' in compass_page


def test_dynamic_content_grids_do_not_render_empty_gray_slots() -> None:
    root = _root()
    app_vue = (root / 'scholaraio' / 'web' / 'app.vue').read_text(encoding='utf-8')

    dynamic_grid = re.search(r'\.aio-two-col,\n\.aio-three-col\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    two_cell = re.search(r'\.aio-two-col > \.aio-cell\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    three_cell = re.search(r'\.aio-three-col > \.aio-cell\s*\{(?P<body>.*?)\n\}', app_vue, re.S)
    cell = re.search(r'^\.aio-cell\s*\{(?P<body>.*?)\n\}', app_vue, re.S | re.M)
    compass_card = re.search(r'\.aio-compass-card\s*\{(?P<body>.*?)\n\}', app_vue, re.S)

    assert dynamic_grid
    assert 'display: flex;' in dynamic_grid.group('body')
    assert 'flex-wrap: wrap;' in dynamic_grid.group('body')
    assert 'background: transparent;' in dynamic_grid.group('body')
    assert 'background: var(--aio-border);' not in dynamic_grid.group('body')
    assert 'gap: 1px;' not in dynamic_grid.group('body')
    assert two_cell and 'flex: 1 1 calc(50% - 7px);' in two_cell.group('body')
    assert three_cell and 'flex: 1 1 calc(33.333% - 10px);' in three_cell.group('body')
    assert cell and 'border: 1px solid var(--aio-border);' in cell.group('body')
    assert compass_card and 'background: var(--aio-border);' in compass_card.group('body')


def test_todo_detail_uses_dynamic_compass_metrics() -> None:
    root = _root()
    todo_page = (root / 'scholaraio' / 'web' / 'pages' / 'todo' / '[id].vue').read_text(encoding='utf-8')

    assert 'class="aio-metric-panel"' in todo_page
    assert 'todoMetricEntries.length' in todo_page
    assert "entries.push({ label: '综合评分'" in todo_page
    assert "entry.fullMark ? formatScore(entry.fullMark) : '10'" in todo_page
    assert "formatScore(entry.value) + '/' + fullMark" in todo_page
    assert 'Overall Score' not in todo_page
    assert 'Quick Verdict' not in todo_page
    assert 'class="aio-rating-grid"' not in todo_page
    assert "'is-single': !todoMetricEntries.length" in todo_page


def test_homepage_filters_default_to_title_and_read_status() -> None:
    root = _root()
    index_page = (root / 'scholaraio' / 'web' / 'pages' / 'index.vue').read_text(encoding='utf-8')

    assert "const sortBy = ref('title')" in index_page
    assert "sortBy.value = 'title'" in index_page
    assert '<span>阅读状态</span>' in index_page
    assert '<option value="unread">仅未读</option>' in index_page
    assert '<option value="read">仅已读</option>' in index_page
    assert "readStatusFilter.value === 'read'" in index_page
    assert "readStatusFilter.value === 'unread'" in index_page
    assert 'authorFilter' not in index_page
    assert 'normalizedAuthorFilter' not in index_page
    assert '搜索标题、作者' not in index_page
    assert '...(card.authors || [])' not in index_page

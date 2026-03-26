from __future__ import annotations

from scholaraio.config import Config, PathsConfig
from scholaraio.index import build_index
from scholaraio.papers import read_meta, write_meta
from scholaraio.services.graph_service import build_graph, get_graph
from scholaraio.workspace import add as add_to_workspace, create as create_workspace


def _make_cfg(tmp_path):
    return Config(
        paths=PathsConfig(papers_dir='papers', index_db='index.db'),
        _root=tmp_path,
    )


def _write_paper(papers_dir, dir_name: str, meta: dict, markdown: str = '# Paper\n\nBody.'):
    paper_dir = papers_dir / dir_name
    paper_dir.mkdir(exist_ok=True)
    write_meta(paper_dir, meta)
    (paper_dir / 'paper.md').write_text(markdown, encoding='utf-8')
    return paper_dir


def test_citation_graph_for_single_paper_includes_local_and_external_neighbors(tmp_path, tmp_papers, tmp_db):
    cfg = _make_cfg(tmp_path)

    paper_a = tmp_papers / 'Smith-2023-Turbulence'
    meta_a = read_meta(paper_a)
    meta_a['references'] = [
        '10.5678/fluid.2024.002',
        '10.9999/outside.1',
    ]
    write_meta(paper_a, meta_a)

    paper_b = tmp_papers / 'Wang-2024-DeepLearning'
    meta_b = read_meta(paper_b)
    meta_b['doi'] = '10.5678/fluid.2024.002'
    meta_b['journal'] = 'PhD Thesis Archive'
    write_meta(paper_b, meta_b)

    _write_paper(
        tmp_papers,
        'Lee-2025-WallModels',
        {
            'id': 'cccc-3333',
            'title': 'Wall models for turbulent flow prediction',
            'authors': ['Chris Lee'],
            'first_author_lastname': 'Lee',
            'year': 2025,
            'journal': 'Flow Letters',
            'doi': '10.8888/flow.2025.003',
            'abstract': 'A short paper.',
            'paper_type': 'journal-article',
            'citation_count': {'crossref': 4},
            'references': ['10.1234/jfm.2023.001'],
        },
    )

    build_index(tmp_papers, tmp_db, rebuild=True)
    graph = get_graph(cfg, mode='citation', scope='paper', paper_ref='Smith-2023-Turbulence', max_nodes=10)

    node_ids = {node['id'] for node in graph['nodes']}
    edge_pairs = {(edge['source'], edge['target']) for edge in graph['edges']}

    assert graph['mode'] == 'citation'
    assert graph['scope'] == 'paper'
    assert 'aaaa-1111' in node_ids
    assert 'bbbb-2222' in node_ids
    assert 'cccc-3333' in node_ids
    assert 'doi:10.9999/outside.1' in node_ids
    assert ('aaaa-1111', 'bbbb-2222') in edge_pairs
    assert ('aaaa-1111', 'doi:10.9999/outside.1') in edge_pairs
    assert ('cccc-3333', 'aaaa-1111') in edge_pairs


def test_structure_graph_for_project_combines_direct_and_shared_relations(tmp_path, tmp_papers, tmp_db):
    cfg = _make_cfg(tmp_path)

    meta_a = read_meta(tmp_papers / 'Smith-2023-Turbulence')
    meta_a['references'] = [
        '10.5678/fluid.2024.002',
        '10.2000/shared.x',
        '10.2000/shared.y',
    ]
    write_meta(tmp_papers / 'Smith-2023-Turbulence', meta_a)

    meta_b = read_meta(tmp_papers / 'Wang-2024-DeepLearning')
    meta_b['doi'] = '10.5678/fluid.2024.002'
    meta_b['journal'] = 'Fluid AI Review'
    meta_b['references'] = [
        '10.2000/shared.x',
        '10.2000/shared.y',
    ]
    write_meta(tmp_papers / 'Wang-2024-DeepLearning', meta_b)

    _write_paper(
        tmp_papers,
        'Kim-2022-Laminar',
        {
            'id': 'dddd-4444',
            'title': 'Laminar baselines for comparison',
            'authors': ['Mina Kim'],
            'first_author_lastname': 'Kim',
            'year': 2022,
            'journal': 'Baseline Notes',
            'doi': '10.7000/base.2022.004',
            'abstract': 'Baseline study.',
            'paper_type': 'journal-article',
            'citation_count': {'crossref': 2},
            'references': ['10.3000/unshared.z'],
        },
    )

    build_index(tmp_papers, tmp_db, rebuild=True)

    ws_dir = tmp_path / 'workspace' / 'alpha'
    create_workspace(ws_dir)
    add_to_workspace(
        ws_dir,
        [],
        tmp_db,
        resolved=[
            {'id': 'aaaa-1111', 'dir_name': 'Smith-2023-Turbulence'},
            {'id': 'bbbb-2222', 'dir_name': 'Wang-2024-DeepLearning'},
            {'id': 'dddd-4444', 'dir_name': 'Kim-2022-Laminar'},
        ],
    )

    graph = get_graph(cfg, mode='structure', scope='project', project='alpha', min_shared=2, max_nodes=20)

    edge = next(
        edge for edge in graph['edges']
        if {edge['source'], edge['target']} == {'aaaa-1111', 'bbbb-2222'}
    )

    assert graph['mode'] == 'structure'
    assert graph['scope'] == 'project'
    assert set(edge['relations']) == {'direct_citation', 'shared_refs'}
    assert edge['direct_count'] == 1
    assert edge['shared_refs'] == 2
    assert edge['weight'] > 2.0



def test_topic_graph_uses_saved_topic_assignments(monkeypatch, tmp_path, tmp_papers, tmp_db):
    cfg = _make_cfg(tmp_path)

    class FakeTopicModel:
        def __init__(self):
            self._paper_ids = ['aaaa-1111', 'bbbb-2222']
            self._topics = [0, 1]
            self._metas = [
                {
                    'paper_id': 'aaaa-1111',
                    'title': 'Turbulence modeling in boundary layers',
                    'authors': 'John Smith, Jane Doe',
                    'year': 2023,
                    'citation_count': {'crossref': 10, 's2': 12},
                },
                {
                    'paper_id': 'bbbb-2222',
                    'title': 'Deep learning for fluid dynamics',
                    'authors': 'Wei Wang',
                    'year': 2024,
                    'citation_count': {},
                },
            ]
            self.topic_similarities_ = [
                [1.0, 0.42],
                [0.42, 1.0],
            ]

        def get_topic(self, topic_id):
            if topic_id == 0:
                return [('turbulence', 0.4), ('boundary', 0.3)]
            if topic_id == 1:
                return [('deep-learning', 0.4), ('fluid', 0.3)]
            return []

    monkeypatch.setattr('scholaraio.services.graph_service._load_topic_model', lambda cfg: FakeTopicModel())

    graph = get_graph(cfg, mode='topic', scope='library', max_nodes=10)

    assert graph['mode'] == 'topic'
    assert graph['stats']['topics'] == 2
    assert graph['stats']['papers'] == 2
    assert {node['id'] for node in graph['nodes']} == {'topic:0', 'topic:1'}
    assert graph['edges'][0]['type'] == 'topic_similarity'
    first_topic = next(node for node in graph['nodes'] if node['id'] == 'topic:0')
    assert first_topic['keywords'] == ['turbulence', 'boundary']
    assert first_topic['representative_papers'][0]['paper_ref'] == 'Smith-2023-Turbulence'


def test_build_graph_returns_dynamic_graph_summary(tmp_path, tmp_papers, tmp_db):
    cfg = _make_cfg(tmp_path)

    meta_a = read_meta(tmp_papers / 'Smith-2023-Turbulence')
    meta_a['references'] = ['10.5678/fluid.2024.002']
    write_meta(tmp_papers / 'Smith-2023-Turbulence', meta_a)

    meta_b = read_meta(tmp_papers / 'Wang-2024-DeepLearning')
    meta_b['doi'] = '10.5678/fluid.2024.002'
    write_meta(tmp_papers / 'Wang-2024-DeepLearning', meta_b)

    build_index(tmp_papers, tmp_db, rebuild=True)
    result = build_graph(cfg, mode='citation', scope='library', max_nodes=10)

    assert result['success'] is True
    assert result['nodes'] == len(result['graph']['nodes'])
    assert result['edges'] == len(result['graph']['edges'])
    assert result['graph']['mode'] == 'citation'
    assert result['graph']['stats']['papers'] == 2

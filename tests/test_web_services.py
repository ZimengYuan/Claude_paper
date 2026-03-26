from __future__ import annotations

import json
import builtins
import importlib
import sys

from scholaraio.config import Config, PathsConfig
from scholaraio.index import build_index
from scholaraio.papers import read_meta, write_meta, write_method, write_summary
from scholaraio.services.knowledge_service import add_knowledge_note, add_paper_summary_note, list_tags, search_knowledge_notes
from scholaraio.services.library_service import list_papers
from scholaraio.services.paper_service import get_paper_detail, update_paper_read_status, update_paper_tags
from scholaraio.services.project_service import list_projects
from scholaraio.workspace import add as add_to_workspace, create as create_workspace


def _make_cfg(tmp_path, tmp_papers, tmp_db):
    return Config(
        paths=PathsConfig(papers_dir='papers', index_db='index.db'),
        _root=tmp_path,
    )


class TestLibraryService:
    def test_list_papers_uses_indexed_search_when_available(self, tmp_path, tmp_papers, tmp_db):
        cfg = _make_cfg(tmp_path, tmp_papers, tmp_db)
        build_index(tmp_papers, tmp_db)
        write_summary(tmp_papers / 'Smith-2023-Turbulence', 'summary body')

        results = list_papers(cfg, query='boundary layers', show_all=False)

        assert len(results) == 1
        assert results[0]['dir_name'] == 'Smith-2023-Turbulence'
        assert results[0]['citation_count'] == 12
        assert results[0]['has_summary'] is True
        assert results[0]['materials']['summary'] is True

    def test_list_papers_can_be_scoped_to_project_subset(self, tmp_path, tmp_papers, tmp_db):
        cfg = _make_cfg(tmp_path, tmp_papers, tmp_db)
        build_index(tmp_papers, tmp_db)
        write_summary(tmp_papers / 'Smith-2023-Turbulence', 'summary body')
        write_summary(tmp_papers / 'Wang-2024-DeepLearning', 'summary body')

        ws_dir = tmp_path / 'workspace' / 'fluid-project'
        create_workspace(ws_dir)
        add_to_workspace(
            ws_dir,
            [],
            tmp_db,
            resolved=[{'id': 'aaaa-1111', 'dir_name': 'Smith-2023-Turbulence'}],
        )

        results = list_papers(cfg, show_all=False, project='fluid-project')

        assert [row['dir_name'] for row in results] == ['Smith-2023-Turbulence']

    def test_library_excludes_rating_only_papers(self, tmp_path, tmp_papers, tmp_db):
        cfg = _make_cfg(tmp_path, tmp_papers, tmp_db)
        paper_dir = tmp_papers / 'Wang-2024-DeepLearning'
        meta = read_meta(paper_dir)
        meta['rating'] = {
            'innovation': 8,
            'technical_quality': 7,
            'experimental_validation': 6,
            'writing_quality': 7,
            'relevance': 8,
            'overall_score': 7.3,
            'notes': 'strong thesis',
        }
        write_meta(paper_dir, meta)

        results = list_papers(cfg, show_all=False)

        assert all(row['dir_name'] != 'Wang-2024-DeepLearning' for row in results)


class TestPaperService:
    def test_get_paper_detail_reads_generated_material_files(self, tmp_path, tmp_papers, tmp_db):
        cfg = _make_cfg(tmp_path, tmp_papers, tmp_db)
        paper_dir = tmp_papers / 'Smith-2023-Turbulence'
        write_summary(paper_dir, 'summary body')
        write_method(paper_dir, 'method body')

        detail = get_paper_detail(cfg, 'Smith-2023-Turbulence')

        assert detail['summary'] == 'summary body'
        assert detail['method_summary'] == 'method body'
        assert detail['citation_count'] == 12
        assert detail['read_status'] == 'unread'
        assert 'reflection' not in detail
        assert 'user_notes' not in detail


    def test_get_paper_detail_includes_parsed_source_payload(self, tmp_path, tmp_papers, tmp_db):
        cfg = _make_cfg(tmp_path, tmp_papers, tmp_db)
        paper_dir = tmp_papers / 'Smith-2023-Turbulence'
        images_dir = paper_dir / 'images'
        images_dir.mkdir()
        (images_dir / 'figure-1.png').write_bytes(b'img')
        (paper_dir / 'layout.json').write_text('{}', encoding='utf-8')
        (paper_dir / 'body_content_list.json').write_text('[]', encoding='utf-8')

        detail = get_paper_detail(cfg, 'Smith-2023-Turbulence')

        assert detail['parsed_source']['files'] == [
            {'name': 'meta.json', 'kind': 'structured_metadata', 'exists': True},
            {'name': 'paper.md', 'kind': 'parsed_markdown', 'exists': True},
        ]
        assert detail['parsed_source']['assets']['images'] == 1
        assert detail['parsed_source']['assets']['has_layout'] is True
        assert detail['parsed_source']['assets']['content_lists'] == ['body_content_list.json']
        assert detail['parsed_source']['generator_input']['file'] == 'paper.md'
        assert detail['parsed_source']['markdown_stats']['words'] > 0

    def test_update_status_and_tags_write_back_meta(self, tmp_path, tmp_papers, tmp_db):
        cfg = _make_cfg(tmp_path, tmp_papers, tmp_db)
        paper_dir = tmp_papers / 'Smith-2023-Turbulence'

        status_result = update_paper_read_status(cfg, 'Smith-2023-Turbulence', 'read')
        tags_result = update_paper_tags(cfg, 'Smith-2023-Turbulence', ['ml', 'ml', 'physics', ''])
        meta = read_meta(paper_dir)

        assert status_result == {'success': True, 'read_status': 'read'}
        assert tags_result == {'success': True, 'tags': ['ml', 'physics']}
        assert meta['read_status'] == 'read'
        assert meta['tags'] == ['ml', 'physics']


class TestProjectService:
    def test_list_projects_reads_non_empty_workspace_scopes(self, tmp_path, tmp_papers, tmp_db):
        cfg = _make_cfg(tmp_path, tmp_papers, tmp_db)
        ws_root = tmp_path / 'workspace'
        alpha = ws_root / 'alpha'
        empty = ws_root / 'empty'
        create_workspace(alpha)
        create_workspace(empty)
        add_to_workspace(
            alpha,
            [],
            tmp_db,
            resolved=[{'id': 'aaaa-1111', 'dir_name': 'Smith-2023-Turbulence'}],
        )

        projects = list_projects(cfg)

        assert projects == [{'name': 'alpha', 'paper_count': 1}]


class TestKnowledgeService:
    def test_list_tags_and_knowledge_notes_share_python_logic(self, tmp_path, tmp_papers, tmp_db):
        cfg = _make_cfg(tmp_path, tmp_papers, tmp_db)
        paper_dir = tmp_papers / 'Smith-2023-Turbulence'
        meta = read_meta(paper_dir)
        meta['tags'] = ['turbulence', 'boundary-layer']
        (tmp_path / 'data').mkdir(exist_ok=True)
        (tmp_path / 'data' / 'tags.json').write_text(
            json.dumps({'turbulence': {'description': 'flow tag', 'color': '#3366ff', 'paper_count': 99}}),
            encoding='utf-8',
        )
        write_summary(paper_dir, 'summary body')
        write_meta(paper_dir, meta)

        add_knowledge_note(cfg, 'cross-paper note', 'research')
        add_paper_summary_note(cfg, title='A Paper', summary='short summary')
        tags = list_tags(cfg)
        search = search_knowledge_notes(cfg, 'summary')

        assert tags == [
            {'tag': 'boundary-layer', 'paper_count': 1, 'description': '', 'color': ''},
            {'tag': 'turbulence', 'paper_count': 1, 'description': 'flow tag', 'color': '#3366ff'},
        ]
        assert len(search['results']) == 1
        assert 'paper-summary | A Paper' in search['results'][0]['section']


class TestWebBridge:
    def test_library_action_does_not_import_explore_service(self, monkeypatch):
        real_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'scholaraio.services.explore_service':
                raise ImportError('explore import should not be needed for library actions')
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, '__import__', guarded_import)
        sys.modules.pop('scholaraio.web_bridge', None)
        sys.modules.pop('scholaraio.services.explore_service', None)

        web_bridge = importlib.import_module('scholaraio.web_bridge')
        library_service = importlib.import_module('scholaraio.services.library_service')

        def fake_list_papers(cfg, *, query='', show_all=False, project=''):
            return [{
                'dir_name': 'Smith-2023-Turbulence',
                'query': query,
                'show_all': show_all,
                'project': project,
            }]

        monkeypatch.setattr(library_service, 'list_papers', fake_list_papers)

        result = web_bridge._ACTIONS['list_papers'](
            {'query': 'boundary layers', 'show_all': True, 'project': 'alpha'},
            object(),
        )

        assert result == [{
            'dir_name': 'Smith-2023-Turbulence',
            'query': 'boundary layers',
            'show_all': True,
            'project': 'alpha',
        }]


    def test_explore_bridge_only_exposes_local_analysis_actions(self):
        sys.modules.pop('scholaraio.web_bridge', None)

        web_bridge = importlib.import_module('scholaraio.web_bridge')

        assert 'list_explores' in web_bridge._ACTIONS
        assert 'get_explore' in web_bridge._ACTIONS
        assert 'generate_explore_roadmap' in web_bridge._ACTIONS
        assert 'fetch_explore' not in web_bridge._ACTIONS
        assert 'search_explore' not in web_bridge._ACTIONS
        assert 'build_explore_embeddings' not in web_bridge._ACTIONS
        assert 'build_explore_topics' not in web_bridge._ACTIONS

    def test_local_explore_actions_analyze_current_library(self, tmp_path, tmp_papers, tmp_db):
        cfg = _make_cfg(tmp_path, tmp_papers, tmp_db)
        topic_dir = cfg.topics_model_dir
        topic_dir.mkdir(parents=True, exist_ok=True)
        (topic_dir / 'info.json').write_text(json.dumps({'n_topics': 2, 'n_papers': 2}), encoding='utf-8')

        sys.modules.pop('scholaraio.web_bridge', None)
        web_bridge = importlib.import_module('scholaraio.web_bridge')

        libraries = web_bridge._ACTIONS['list_explores']({}, cfg)
        detail = web_bridge._ACTIONS['get_explore']({'name': 'current-library'}, cfg)

        assert len(libraries) == 1
        assert libraries[0]['name'] == 'current-library'
        assert libraries[0]['source'] == 'local-library'
        assert libraries[0]['count'] == 2
        assert detail['name'] == 'current-library'
        assert detail['count'] == 2
        assert detail['query']['scope'] == 'main library'
        assert detail['topic_info'] == {'n_topics': 2, 'n_papers': 2}
        assert detail['papers_sample'][0]['title'] == 'Turbulence modeling in boundary layers'
        assert detail['trend_overview']['top_journals'][0]['name'] == 'Journal of Fluid Mechanics'

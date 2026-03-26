from __future__ import annotations

import os
from pathlib import Path

from scholaraio.config import Config, PathsConfig
from scholaraio.generation_worker import process_task
from scholaraio.papers import read_meta, read_summary, write_meta
from scholaraio.services.generation_service import enqueue_batch_generation_task, enqueue_generation_task, normalize_generation_types
from scholaraio.tasks import get_task


def _make_cfg(tmp_path):
    return Config(
        paths=PathsConfig(papers_dir='data/papers', index_db='data/index.db'),
        _root=tmp_path,
    )


def test_normalize_generation_types_defaults_and_deduplicates():
    assert normalize_generation_types(None) == ['summary', 'rating']
    assert normalize_generation_types(['summary', 'summary', 'rating']) == ['summary', 'rating']


def test_generation_task_creation_and_worker_processing(tmp_path, monkeypatch):
    cfg = _make_cfg(tmp_path)
    paper_dir = tmp_path / 'data' / 'papers' / 'Smith-2023-Turbulence'
    paper_dir.mkdir(parents=True)
    write_meta(paper_dir, {
        'id': 'aaaa-1111',
        'title': 'Turbulence modeling in boundary layers',
        'authors': ['John Smith'],
        'first_author_lastname': 'Smith',
        'year': 2023,
        'journal': 'Journal of Fluid Mechanics',
        'doi': '10.1234/jfm.2023.001',
        'abstract': 'Boundary-layer turbulence model.',
    })
    monkeypatch.setenv('SCHOLARAIO_TASKS_DIR', str(tmp_path / 'data' / '.tasks'))
    monkeypatch.setattr('scholaraio.services.generation_service._spawn_generation_worker', lambda cfg, task_id: None)

    def fake_summary(target_dir, cfg, force=True):
        (target_dir / 'summary.md').write_text('generated summary', encoding='utf-8')
        meta = read_meta(target_dir)
        meta['summary'] = 'generated summary'
        write_meta(target_dir, meta)

    def fake_rating(target_dir, cfg, force=True):
        meta = read_meta(target_dir)
        meta['rating'] = {'overall_score': 8.5}
        write_meta(target_dir, meta)

    monkeypatch.setitem(__import__('scholaraio.generation_worker', fromlist=['_GENERATORS'])._GENERATORS, 'summary', fake_summary)
    monkeypatch.setitem(__import__('scholaraio.generation_worker', fromlist=['_GENERATORS'])._GENERATORS, 'rating', fake_rating)

    task_info = enqueue_generation_task(cfg, 'Smith-2023-Turbulence', ['summary', 'rating'])
    process_task(task_info['task_id'], cfg)

    task = get_task(task_info['task_id'])
    meta = read_meta(paper_dir)

    assert task['status'] == 'completed'
    assert task['completed'] == 2
    assert task['failed'] == 0
    assert read_summary(paper_dir) == 'generated summary'
    assert meta['rating'] == {'overall_score': 8.5}


def test_batch_generation_task_creation(tmp_path, monkeypatch):
    cfg = _make_cfg(tmp_path)
    monkeypatch.setenv('SCHOLARAIO_TASKS_DIR', str(tmp_path / 'data' / '.tasks'))
    monkeypatch.setattr('scholaraio.services.generation_service._spawn_generation_worker', lambda cfg, task_id: None)

    result = enqueue_batch_generation_task(cfg, ['A', 'A', 'B'], ['summary'])
    task = get_task(result['task_id'])

    assert task['type'] == 'batch_generate'
    assert task['metadata']['paper_refs'] == ['A', 'B']
    assert task['metadata']['types'] == ['summary']

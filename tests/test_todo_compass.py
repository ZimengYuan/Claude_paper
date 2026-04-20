from __future__ import annotations

import json

from scholaraio.config import Config, PathsConfig
from scholaraio.papers import read_meta, write_summary
from scholaraio.todo_compass import (
    ensure_todo_placeholder_paper,
    generate_compass_readable_report,
    generate_compass_score_report,
    parse_compass_score_report,
)


def _make_cfg(tmp_path):
    return Config(paths=PathsConfig(papers_dir='papers', index_db='index.db'), _root=tmp_path)


def test_parse_compass_score_report_extracts_dimension_scores():
    markdown = """# 论文价值分析报告

## 1. 最终结论

- 总分: 7.4/10.0
- 等级: solid and worth reading
- 阅读优先级: 高
- 奠基潜力判断: early promise, not yet established
- 一句话判断: 值得优先扫读，但不是显然的奠基性工作

## 2. 分项评分

| 维度 | 满分 | 得分 | 评分依据 | 关键证据 |
|---|---:|---:|---|---|
| 发表与 Venue 信号 | 1.5 | 1.2 | verified strong venue | [API:CR] venue=ICRA |
| 作者与机构信号 | 1.0 | 0.8 | credible author group | [API:OA] authors=2 |
| 引用量与引用增速 | 2.0 | 1.4 | above median | [API:OA] cited_by_count=42 |
| 被引论文质量 | 1.5 | 0.9 | mixed follow-up quality | [Peer P1] sample |
| 技术增量与新颖性 | 2.0 | 1.6 | clear method delta | [Method] "new planner" |
| 业界贡献 / 开源 / 产品信号 | 1.0 | 0.5 | limited external uptake | 信息不足 |
| 奠基潜力 / 方向性影响 | 1.0 | 1.0 | multiple signals | [Peer P2] reuse |
"""

    rating = parse_compass_score_report(markdown)

    assert rating['scheme'] == 'paper_compass_score'
    assert rating['publication_signal'] == 1.2
    assert rating['author_signal'] == 0.8
    assert rating['citation_traction'] == 1.4
    assert rating['citation_quality'] == 0.9
    assert rating['novelty'] == 1.6
    assert rating['industry_signal'] == 0.5
    assert rating['field_shaping'] == 1.0
    assert rating['overall_score'] == 7.4
    assert rating['priority'] == '高'


def test_ensure_todo_placeholder_paper_creates_local_paper_dir(tmp_path):
    cfg = _make_cfg(tmp_path)
    papers_dir = tmp_path / 'papers'
    papers_dir.mkdir()

    paper_dir = ensure_todo_placeholder_paper(
        cfg,
        title='Human-Robot Copilot',
        authors=['Ada Lovelace'],
        year=2026,
        journal='arXiv',
        doi='10.48550/arXiv.2601.12345',
        abstract='A conservative placeholder abstract.',
    )

    meta = read_meta(paper_dir)

    assert paper_dir.exists()
    assert (paper_dir / 'paper.md').exists()
    assert meta['todo_placeholder'] is True
    assert meta['paper_type'] == 'todo-placeholder'
    assert meta['title'] == 'Human-Robot Copilot'
    assert 'Todo占位' in meta['tags']


def test_generate_compass_reports_with_fallback(tmp_path):
    cfg = _make_cfg(tmp_path)
    papers_dir = tmp_path / 'papers'
    papers_dir.mkdir()
    paper_dir = papers_dir / 'Smith-2024-TestPaper'
    paper_dir.mkdir()
    (paper_dir / 'meta.json').write_text(
        json.dumps(
            {
                'id': 'paper-1',
                'title': 'Residual Koopman Control for Humanoid Locomotion',
                'authors': ['Ada Lovelace', 'Grace Hopper'],
                'first_author_lastname': 'Lovelace',
                'year': 2024,
                'journal': 'Science Robotics',
                'doi': '10.1234/example.2024.1',
                'abstract': 'We combine Koopman dynamics, reinforcement learning, and whole-body control for humanoid locomotion.',
                'paper_type': 'journal-article',
                'citation_count': {'local': 24},
            },
            ensure_ascii=False,
        ),
        encoding='utf-8',
    )
    (paper_dir / 'paper.md').write_text(
        '# Residual Koopman Control for Humanoid Locomotion\n\nThis paper studies humanoid locomotion with Koopman dynamics and policy optimization.\n',
        encoding='utf-8',
    )
    write_summary(
        paper_dir,
        '## 1. 核心创新点\n论文把 Koopman 动力学、强化学习和全身控制串成统一闭环。\n\n## 2. 实验结果\n在 humanoid locomotion 任务上表现稳定。\n',
    )

    score_md, rating = generate_compass_score_report(cfg, paper_dir, model='fallback')
    report_md = generate_compass_readable_report(cfg, paper_dir, score_report=score_md, model='fallback')

    assert '## 2. 分项评分' in score_md
    assert rating['scheme'] == 'paper_compass_score'
    assert rating['overall_score'] <= 10.0
    assert '## 1. 必学先修知识（按顺序）' in report_md
    assert '强化学习与策略优化' in report_md

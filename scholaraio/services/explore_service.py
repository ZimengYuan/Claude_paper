from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

from scholaraio.papers import best_citation, iter_paper_dirs, read_meta
from scholaraio.services.common import ServiceError


LOCAL_LIBRARY_NAME = "current-library"
LOCAL_LIBRARY_TITLE = "Current Library"
LOCAL_LIBRARY_ALIASES = {"", LOCAL_LIBRARY_NAME, "main", "library", "current", "local"}


DIRECTION_SYSTEM_PROMPT = """你是一位学术领域规划专家。
你的任务是将一系列细碎的研究主题（Topic）聚合成不超过 10 个宏观的研究方向（Mega Directions）。

输入：
每个主题包含 ID、关键词和简短描述。

输出：
仅返回一个 JSON 对象，格式如下：
{
  "directions": [
    {
      "name": "方向名称（专业且简洁，如：足式机器人控制）",
      "topics": [1, 5, 12],
      "summary": "该方向的核心研究目标简述"
    }
  ]
}
"""

ROADMAP_SYSTEM_PROMPT = """你是一位资深学术研究员，擅长分析技术演进和预测未来趋势。
你的任务是根据提供的论文列表，为一个宏观研究方向生成一份“方法进化图谱”。

输出要求：
1. 仅返回 Markdown 正文，不要写“我来为你生成一份……”“首先让我……”这类前言，也不要解释你的分析过程。
2. 不要输出整篇文档总标题；调用方会在外层提供方向标题。
3. 统一使用如下层级：
   - `### 研究脉络概览`
   - `### 阶段一：...`、`### 阶段二：...`
   - `#### 核心挑战`
   - `#### 关键技术突破`
   - `#### 代表论文`
   - `### 未来趋势预测`
4. **进化阶段分析**：将该方向的发展划分为 3-4 个阶段，必须说明每个阶段相对上一阶段解决了什么痛点。
5. **论文直达引用**：提到的核心方法或论文，必须使用 `[方法名或标题](paper_id:ID)` 格式，严禁发明 ID。
6. **未来趋势预测**：基于现有方法的局限性，给出 2-3 个具体预测，并解释为什么这是下一步演化方向。
7. 使用专业、技术化的简体中文，避免空话，避免聊天口吻。
"""


def _normalize_library_name(name: str | None) -> str:
    candidate = str(name or '').strip().lower()
    if candidate in LOCAL_LIBRARY_ALIASES:
        return LOCAL_LIBRARY_NAME
    raise ServiceError('Explore 现在只分析当前本地主库，不再支持外部 explore 库。', status_code=404)


def _topic_model_exists(cfg) -> bool:
    model_dir = cfg.topics_model_dir
    return (model_dir / 'bertopic_model.pkl').exists() or (model_dir / 'model.pkl').exists()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def _normalize_authors(authors: Any) -> list[str]:
    if isinstance(authors, list):
        return [str(author).strip() for author in authors if str(author).strip()]
    if isinstance(authors, str):
        return [part.strip() for part in authors.split(',') if part.strip()]
    return []


def _best_citation(value: Any) -> int:
    if isinstance(value, dict):
        vals = [item for item in value.values() if isinstance(item, (int, float))]
        return int(max(vals)) if vals else 0
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def _safe_year(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _paper_brief_from_meta(paper_dir: Path, meta: dict[str, Any]) -> dict[str, Any]:
    paper_ref = str(meta.get('id') or paper_dir.name)
    return {
        'paper_ref': paper_ref,
        'paper_id': str(meta.get('id') or ''),
        'dir_name': paper_dir.name,
        'doi': meta.get('doi') or '',
        'title': meta.get('title') or '',
        'authors': _normalize_authors(meta.get('authors')),
        'year': meta.get('year'),
        'journal': meta.get('journal') or '',
        'type': meta.get('paper_type') or '',
        'cited_by_count': best_citation(meta),
        'abstract': meta.get('abstract') or '',
    }


ROADMAP_DIRECTION_MAX_PAPERS = 20
ROADMAP_DIRECTION_TIMEOUT_SECONDS = 240
ROADMAP_DIRECTION_RETRY_MAX_PAPERS = 12


def _clean_roadmap_section_markdown(content: str) -> str:
    text = str(content or '').strip()
    if not text:
        return ''

    patterns = [
        r'^我来为你生成.*?(?:\n|$)',
        r'^我将基于.*?(?:\n|$)',
        r'^我已经分析.*?(?:\n|$)',
        r'^首先[，,：:].*?(?:\n|$)',
        r'^根据论文发表时间和技术特征.*?(?:\n|$)',
        r'^以下是详细的进化图谱。*?(?:\n|$)',
        r'^现在开始撰写.*?(?:\n|$)',
        r'^#\s+[^\n]*\n*',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, count=1, flags=re.MULTILINE)

    text = re.sub(r'^(?:---\s*\n+)+', '', text)
    text = re.sub(r'(?:\n+---\s*)+$', '', text)
    text = re.sub(r'^##\s+(.*)$', r'### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^###\s+(核心挑战|关键技术突破|代表论文)$', r'#### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^###\s+(趋势\s*\d+[^\n]*)$', r'#### \1', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    if text and not re.match(r'^(###|####|>|\-|\*\*|\|)', text):
        text = '### 研究脉络概览\n\n' + text
    return text.strip()


def _roadmap_direction_timeout(cfg) -> int:
    base = int(getattr(cfg.llm, 'timeout_clean', 120) or 120)
    return max(base, ROADMAP_DIRECTION_TIMEOUT_SECONDS)


def _roadmap_direction_failure_markdown(message: str) -> str:
    text = str(message or 'unknown error').strip() or 'unknown error'
    return (
        '### 研究脉络概览\n'
        f'> 当前方向的自动总结生成失败：{text}\n\n'
        '> 你仍然可以先结合上方的 Topic Readiness 与 Representative Papers 做人工判断。'
    )


def _build_roadmap_prompt(dir_name: str, summary: str, papers: list[dict[str, Any]], *, limit: int) -> str:
    papers_for_prompt = []
    for paper in papers[:limit]:
        ref = str(paper.get('paper_id') or '')
        year = paper.get('year') or '?'
        title = paper.get('title') or 'Untitled'
        abstract = paper.get('abstract') or ''
        papers_for_prompt.append(f'- [{ref}] ({year}) {title}\n摘要: {abstract}')

    papers_block = '\n'.join(papers_for_prompt)
    return (
        f'研究方向：{dir_name}\n'
        f'摘要：{summary}\n\n'
        f'相关论文列表（按时间排序）：\n{papers_block}\n\n'
        '请基于以上论文生成该方向的方法进化图谱。'
    )


def _generate_direction_roadmap_markdown(
    *,
    cfg,
    call_llm,
    dir_name: str,
    summary: str,
    papers: list[dict[str, Any]],
) -> str:
    prompt = _build_roadmap_prompt(dir_name, summary, papers, limit=ROADMAP_DIRECTION_MAX_PAPERS)
    try:
        result = call_llm(
            prompt=prompt,
            config=cfg,
            system=ROADMAP_SYSTEM_PROMPT,
            json_mode=False,
            max_tokens=4000,
            timeout=_roadmap_direction_timeout(cfg),
            purpose='explore.roadmap_direction',
        )
        section = _clean_roadmap_section_markdown(result.content)
        if section:
            return section
    except Exception as exc:
        error_message = str(exc)
        if 'timed out' not in error_message.lower():
            return _roadmap_direction_failure_markdown(error_message)

    retry_prompt = _build_roadmap_prompt(
        dir_name,
        summary,
        papers,
        limit=min(ROADMAP_DIRECTION_RETRY_MAX_PAPERS, len(papers)),
    ) + '\n\n请进一步压缩代表论文数量，优先保留最关键的 8-12 篇。'
    try:
        retry_result = call_llm(
            prompt=retry_prompt,
            config=cfg,
            system=ROADMAP_SYSTEM_PROMPT,
            json_mode=False,
            max_tokens=2600,
            timeout=_roadmap_direction_timeout(cfg),
            purpose='explore.roadmap_direction_retry',
        )
        section = _clean_roadmap_section_markdown(retry_result.content)
        if section:
            return section
        return _roadmap_direction_failure_markdown('LLM returned empty roadmap content.')
    except Exception as exc:
        return _roadmap_direction_failure_markdown(str(exc))


def _paper_brief_from_topic_meta(paper: dict[str, Any]) -> dict[str, Any]:
    paper_ref = str(paper.get('paper_id') or paper.get('doi') or '')
    return {
        'paper_ref': paper_ref,
        'paper_id': str(paper.get('paper_id') or ''),
        'dir_name': '',
        'doi': paper.get('doi') or '',
        'title': paper.get('title') or '',
        'authors': _normalize_authors(paper.get('authors')),
        'year': paper.get('year'),
        'journal': paper.get('journal') or '',
        'type': paper.get('paper_type') or paper.get('type') or '',
        'cited_by_count': max(int(paper.get('cited_by_count') or 0), _best_citation(paper.get('citation_count'))),
        'abstract': paper.get('abstract') or '',
    }


def _iter_library_cards(cfg) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for paper_dir in iter_paper_dirs(cfg.papers_dir):
        try:
            meta = read_meta(paper_dir)
        except (ValueError, FileNotFoundError):
            continue
        cards.append(_paper_brief_from_meta(paper_dir, meta))
    return cards


def _sample_papers(cards: list[dict[str, Any]], *, limit: int = 12) -> list[dict[str, Any]]:
    ranked = sorted(
        cards,
        key=lambda paper: (
            -(int(paper.get('cited_by_count') or 0)),
            -_safe_year(paper.get('year')),
            paper.get('title') or paper.get('paper_ref') or '',
        ),
    )
    return ranked[:limit]


def _recent_papers_sample(cards: list[dict[str, Any]], *, limit: int = 8) -> list[dict[str, Any]]:
    ranked = sorted(
        cards,
        key=lambda paper: (
            -_safe_year(paper.get('year')),
            -(int(paper.get('cited_by_count') or 0)),
            paper.get('title') or paper.get('paper_ref') or '',
        ),
    )
    return ranked[:limit]


def _counter_rows(counter: Counter[str], total: int, *, limit: int) -> list[dict[str, Any]]:
    if total <= 0:
        return []
    rows: list[dict[str, Any]] = []
    for name, count in counter.most_common(limit):
        rows.append(
            {
                'name': name,
                'count': int(count),
                'share': float(count) / float(total),
            }
        )
    return rows


def _year_distribution(year_counter: Counter[int], *, limit: int = 12) -> list[dict[str, int]]:
    if not year_counter:
        return []
    years = sorted(year_counter)
    if len(years) > limit:
        years = years[-limit:]
    return [{'year': year, 'count': int(year_counter[year])} for year in years]


def _trend_highlights(
    *,
    total: int,
    earliest_year: int | None,
    latest_year: int | None,
    recent_count: int,
    avg_citations: float,
    cited_papers: int,
    max_citations: int,
    top_journals: list[dict[str, Any]],
    top_authors: list[dict[str, Any]],
) -> list[str]:
    highlights: list[str] = []
    if total <= 0:
        return highlights

    if earliest_year is not None and latest_year is not None:
        if earliest_year == latest_year:
            highlights.append(f'当前主库的时间分布高度集中在 {latest_year} 年，整体更偏最新跟踪。')
        else:
            recent_share = recent_count / total
            highlights.append(
                f'当前主库覆盖 {earliest_year}-{latest_year}，最近 3 年论文占 {recent_count}/{total}（{recent_share:.0%}）。'
            )

    if top_journals:
        top_journal = top_journals[0]
        highlights.append(f'收录最集中的期刊/来源是 {top_journal["name"]}，占当前主库的 {top_journal["share"]:.0%}。')

    if top_authors:
        top_author = top_authors[0]
        highlights.append(f'当前主库中出现最频繁的作者是 {top_author["name"]}，共出现 {top_author["count"]} 次。')

    if max_citations > 0:
        cited_share = cited_papers / total
        highlights.append(
            f'引用分布存在明显头部论文，最高引用 {max_citations}，平均引用 {avg_citations:.1f}，有引用记录的论文占 {cited_share:.0%}。'
        )
    else:
        highlights.append('当前主库的引用信息还不够完整，更适合先看时间和主题结构。')

    return highlights[:4]


def _build_trend_overview(cards: list[dict[str, Any]]) -> dict[str, Any]:
    year_counter: Counter[int] = Counter()
    type_counter: Counter[str] = Counter()
    author_counter: Counter[str] = Counter()
    journal_counter: Counter[str] = Counter()
    citation_values: list[int] = []

    total = len(cards)
    if total == 0:
        return {
            'year_summary': {},
            'citation_summary': {},
            'year_distribution': [],
            'type_breakdown': [],
            'top_authors': [],
            'top_journals': [],
            'recent_papers_sample': [],
            'trend_highlights': [],
        }

    for paper in cards:
        year = paper.get('year')
        if isinstance(year, int):
            year_counter[year] += 1

        paper_type = str(paper.get('type') or 'unknown').strip() or 'unknown'
        type_counter[paper_type] += 1

        journal = str(paper.get('journal') or 'Unknown venue').strip() or 'Unknown venue'
        journal_counter[journal] += 1

        for author in paper.get('authors') or []:
            author_counter[str(author)] += 1

        citation_values.append(int(paper.get('cited_by_count') or 0))

    earliest_year = min(year_counter) if year_counter else None
    latest_year = max(year_counter) if year_counter else None
    recent_threshold = latest_year - 2 if latest_year is not None else None
    recent_count = 0
    if recent_threshold is not None:
        recent_count = sum(count for year, count in year_counter.items() if year >= recent_threshold)

    total_citations = sum(citation_values)
    cited_papers = sum(1 for value in citation_values if value > 0)
    avg_citations = round(total_citations / total, 1)
    median_citations = float(median(citation_values)) if citation_values else 0.0
    max_citations = max(citation_values, default=0)

    top_types = _counter_rows(type_counter, total, limit=6)
    top_authors = _counter_rows(author_counter, total, limit=8)
    top_journals = _counter_rows(journal_counter, total, limit=6)

    return {
        'year_summary': {
            'earliest': earliest_year,
            'latest': latest_year,
            'active_years': len(year_counter),
            'recent_window_start': recent_threshold,
            'recent_count': recent_count,
            'recent_share': (recent_count / total) if total else 0.0,
        },
        'citation_summary': {
            'average': avg_citations,
            'median': median_citations,
            'max': max_citations,
            'with_citations': cited_papers,
            'with_citations_share': (cited_papers / total) if total else 0.0,
        },
        'year_distribution': _year_distribution(year_counter, limit=12),
        'type_breakdown': top_types,
        'top_authors': top_authors,
        'top_journals': top_journals,
        'recent_papers_sample': _recent_papers_sample(cards, limit=8),
        'trend_highlights': _trend_highlights(
            total=total,
            earliest_year=earliest_year,
            latest_year=latest_year,
            recent_count=recent_count,
            avg_citations=avg_citations,
            cited_papers=cited_papers,
            max_citations=max_citations,
            top_journals=top_journals,
            top_authors=top_authors,
        ),
    }


def _load_topic_info(cfg) -> dict[str, Any]:
    info_path = cfg.topics_model_dir / 'info.json'
    if info_path.exists():
        return _load_json(info_path)
    if not _topic_model_exists(cfg):
        return {}
    try:
        from scholaraio.topics import get_topic_overview, load_model

        overview = get_topic_overview(load_model(cfg.topics_model_dir))
    except Exception:
        return {}
    return {
        'n_topics': len(overview),
        'n_papers': sum(int(item.get('count') or 0) for item in overview),
    }


def _topic_overview(cfg, *, limit: int = 8) -> list[dict[str, Any]]:
    if not _topic_model_exists(cfg):
        return []
    try:
        from scholaraio.topics import get_topic_overview, load_model

        overview = get_topic_overview(load_model(cfg.topics_model_dir))
    except Exception:
        return []

    items: list[dict[str, Any]] = []
    for topic in overview[:limit]:
        items.append(
            {
                'topic_id': int(topic.get('topic_id') or 0),
                'count': int(topic.get('count') or 0),
                'name': topic.get('name') or '',
                'keywords': topic.get('keywords') or [],
                'representative_papers': [_paper_brief_from_topic_meta(paper) for paper in topic.get('representative_papers') or []],
            }
        )
    return items


def _latest_library_timestamp(cfg) -> str:
    latest = 0.0
    for paper_dir in iter_paper_dirs(cfg.papers_dir):
        meta_path = paper_dir / 'meta.json'
        if meta_path.exists():
            latest = max(latest, meta_path.stat().st_mtime)
    if latest <= 0:
        return ''
    return datetime.fromtimestamp(latest).isoformat(timespec='seconds')


def _has_index_table(cfg, table_name: str) -> bool:
    if not cfg.index_db.exists():
        return False
    try:
        with sqlite3.connect(cfg.index_db) as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                (table_name,),
            ).fetchone()
        return row is not None
    except sqlite3.Error:
        return False


def list_explore_libraries(cfg) -> list[dict[str, Any]]:
    cards = _iter_library_cards(cfg)
    return [
        {
            'name': LOCAL_LIBRARY_NAME,
            'title': LOCAL_LIBRARY_TITLE,
            'count': len(cards),
            'query': {
                'scope': 'main library',
                'papers_dir': str(cfg.papers_dir.relative_to(cfg._root)),
                'topic_model': str(cfg.topics_model_dir.relative_to(cfg._root)),
            },
            'source': 'local-library',
            'fetched_at': _latest_library_timestamp(cfg),
            'has_search_index': _has_index_table(cfg, 'papers'),
            'has_semantic_index': _has_index_table(cfg, 'paper_vectors'),
            'has_topics': _topic_model_exists(cfg),
            'roadmap_exists': (cfg.topics_model_dir / 'roadmap.md').exists(),
            'topic_info': _load_topic_info(cfg),
        }
    ]


def get_explore_library(cfg, name: str) -> dict[str, Any]:
    _normalize_library_name(name)
    cards = _iter_library_cards(cfg)
    return {
        'name': LOCAL_LIBRARY_NAME,
        'title': LOCAL_LIBRARY_TITLE,
        'count': len(cards),
        'query': {
            'scope': 'main library',
            'papers_dir': str(cfg.papers_dir.relative_to(cfg._root)),
            'topic_model': str(cfg.topics_model_dir.relative_to(cfg._root)),
        },
        'source': 'local-library',
        'fetched_at': _latest_library_timestamp(cfg),
        'has_search_index': _has_index_table(cfg, 'papers'),
        'has_semantic_index': _has_index_table(cfg, 'paper_vectors'),
        'has_topics': _topic_model_exists(cfg),
        'topic_info': _load_topic_info(cfg),
        'papers_sample': _sample_papers(cards, limit=12),
        'topic_overview': _topic_overview(cfg, limit=8),
        'trend_overview': _build_trend_overview(cards),
        'roadmap_exists': (cfg.topics_model_dir / 'roadmap.md').exists(),
    }


def generate_explore_roadmap_service(cfg, name: str, *, force: bool = False) -> dict[str, Any]:
    from scholaraio.metrics import call_llm
    from scholaraio.topics import get_topic_papers, load_model

    _normalize_library_name(name)
    roadmap_path = cfg.topics_model_dir / 'roadmap.md'

    if roadmap_path.exists() and not force:
        return {
            'success': True,
            'roadmap': roadmap_path.read_text(encoding='utf-8'),
            'cached': True,
        }

    if not _topic_model_exists(cfg):
        raise ServiceError('Main topic model not found. Please build topics first.', status_code=400)

    model = load_model(cfg.topics_model_dir)
    all_topics = _topic_overview(cfg, limit=50)
    if not all_topics:
        raise ServiceError('No topics found in the main library model.', status_code=400)

    topic_list_for_agg = []
    for topic in all_topics:
        topic_list_for_agg.append(
            {
                'id': topic['topic_id'],
                'name': topic['name'],
                'keywords': topic['keywords'][:10],
            }
        )

    agg_prompt = (
        '请将以下研究主题聚合成不超过 10 个宏观方向：\n'
        + json.dumps(topic_list_for_agg, ensure_ascii=False, indent=2)
    )

    try:
        agg_result = call_llm(
            prompt=agg_prompt,
            config=cfg,
            system=DIRECTION_SYSTEM_PROMPT,
            json_mode=True,
            max_tokens=2000,
            purpose='explore.aggregate_directions',
        )
        directions_data = json.loads(agg_result.content)
        directions = directions_data.get('directions', [])
    except Exception:
        directions = [{'name': topic['name'], 'topics': [topic['topic_id']], 'summary': ''} for topic in all_topics[:8]]

    full_roadmap = ['# 当前文献库领域进化图谱与技术预测\n']
    full_roadmap.append(f'当前主库已被自动划分为 {len(directions)} 个核心研究方向。\n')

    for dir_info in directions:
        dir_name = dir_info['name']
        topic_ids = dir_info['topics']

        all_papers_in_dir = []
        for topic_id in topic_ids:
            all_papers_in_dir.extend(get_topic_papers(model, topic_id))

        seen_refs = set()
        unique_papers = []
        for paper in all_papers_in_dir:
            ref = str(paper.get('paper_id') or paper.get('doi') or '')
            if ref and ref not in seen_refs:
                unique_papers.append(paper)
                seen_refs.add(ref)

        unique_papers.sort(key=lambda item: (int(item.get('year') or 0), -_best_citation(item.get('citation_count'))))

        section = _generate_direction_roadmap_markdown(
            cfg=cfg,
            call_llm=call_llm,
            dir_name=dir_name,
            summary=str(dir_info.get('summary', '') or ''),
            papers=unique_papers,
        )
        full_roadmap.append(f'## {dir_name}\n')
        full_roadmap.append(section)
        full_roadmap.append('\n---\n')

    combined_roadmap = '\n'.join(full_roadmap)
    roadmap_path.write_text(combined_roadmap, encoding='utf-8')

    return {
        'success': True,
        'roadmap': combined_roadmap,
        'cached': False,
    }

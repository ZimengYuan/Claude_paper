#!/usr/bin/env python3
"""Generate Todo summary cards for the static Library page."""

from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from difflib import SequenceMatcher
from html import unescape
from pathlib import Path
from threading import Lock
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scholaraio.config import load_config
from scholaraio.generate import _get_paper_content
from scholaraio.metrics import call_llm
from scholaraio.papers import read_meta
from scholaraio.sources.zotero import parse_zotero_local


TODO_COLLECTION_KEY = "RECF7KND"
TODO_COLLECTION_NAME = "Todo"
OUTPUT_PATH = ROOT / "scholaraio/web/public/site-data/todo-cards.json"
MANIFEST_PATH = ROOT / "scholaraio/web/public/site-data/manifest.json"
PAPER_DETAIL_DIR = ROOT / "scholaraio/web/public/site-data/papers"

CARD_SYSTEM_PROMPT = """请以顶级AI研究者的视角,对这篇论文进行快速泛读分析,提取最核心的创新点。请按以下结构输出:
(注意排版，不同点之间区分清楚！)

1. 核心创新点 (Core Innovation)

用1-2句话概括本文最关键的创新

这篇论文解决了什么之前没解决的问题?
或者用什么新方法解决了已有问题?

2. 技术创新拆解 (Technical Contributions)

列出 2-4 个具体的技术创新点:

创新点 1: [简述] - 为什么这个创新重要?
创新点 2: [简述] - 解决了什么限制?
创新点 3: [简述] - 带来了什么提升?

3. 方法论突破 (Methodological Breakthrough)

新颖性: 与现有方法(SOTA)的本质区别是什么?
关键技术: 实现创新的核心技术手段(算法/架构/机制)
理论支撑: 是否有新的理论分析或证明?

4. 实验验证 (Key Results)

主要数据集: 在哪些benchmark上验证?
性能提升: 相比baseline的关键指标提升(用数字说话)
消融实验: 哪个组件贡献最大?

5. 局限与启发 (Limitations & Insights)

当前局限: 作者承认或隐含的limitation
未来方向: 这个工作开启了什么新的研究方向?
可迁移性: 这个创新能否应用到其他领域?

6. 一句话总结

如果只能记住一件事,那就是: [用一句话总结这篇论文为什么值得关注]。对于这一句话尽量地技术化，不要有太多虚内容！！

最后几个注意事项：
1. 输出必须以中文为主，术语可保留英文；
2. 不要照抄摘要首句或结论首句；
3. 不同字段不要重复同一句话；
4. 优先写“方法机制”和“为什么有效”，少写空泛评价；
5. 如果正文没有明确给出 benchmark、数值、消融或理论证明，要明确写“文中未清楚披露”，不要脑补。

严格按下面 JSON schema 输出，不要输出 markdown，不要输出代码块，也不要补充额外解释：
{
  "core_innovation": "string",
  "technical_contributions": [
    {"title": "string", "body": "string"},
    {"title": "string", "body": "string"}
  ],
  "methodological_breakthrough": {
    "novelty": "string",
    "key_technique": "string",
    "theory": "string"
  },
  "key_results": {
    "benchmarks": "string",
    "improvements": "string",
    "ablation": "string"
  },
  "limitations": {
    "current": "string",
    "future": "string",
    "transferability": "string"
  },
  "one_line_summary": "string"
}"""

CARD_METADATA_SYSTEM_PROMPT = """你现在拿到的不是论文全文，而是有限的公开元数据（标题、作者、年份、期刊/会议、DOI、摘要）。

你的任务仍然是生成同样结构的 JSON 卡片，但必须遵守以下约束：
1. 严禁臆造全文中不存在的信息。
2. 如果摘要没有给出 benchmark、数值、消融、理论证明，请明确写“摘要未披露具体 benchmark/数值/消融细节/理论证明”。
3. 允许做高层次概括，但不要编造具体实验结论、提升百分比、模块名称或理论定理。
4. 输出语言以中文为主；术语名可保留英文。
5. 不要直接复述摘要首句，不同字段避免重复同一句话。
6. 输出必须是严格 JSON，字段完全匹配下面 schema，不要输出 markdown、代码块或额外说明。

{
  "core_innovation": "string",
  "technical_contributions": [
    {"title": "string", "body": "string"},
    {"title": "string", "body": "string"}
  ],
  "methodological_breakthrough": {
    "novelty": "string",
    "key_technique": "string",
    "theory": "string"
  },
  "key_results": {
    "benchmarks": "string",
    "improvements": "string",
    "ablation": "string"
  },
  "limitations": {
    "current": "string",
    "future": "string",
    "transferability": "string"
  },
  "one_line_summary": "string"
}"""

FALLBACK_MARKERS = (
    "自动兜底生成",
    "详见论文实验章节。",
    "详见论文指标对比表。",
    "详见论文消融实验。",
)


@dataclass
class MatchedTodoPaper:
    collection_index: int
    zotero_title: str
    zotero_doi: str
    route_id: str
    paper_route_id: str
    dir_name: str
    paper_id: str
    title: str
    authors: list[str]
    year: int | None
    journal: str
    doi: str
    read_status: str
    abstract: str


@dataclass
class ExistingCardIndex:
    by_route_id: dict[str, dict[str, Any]]
    by_alias: dict[tuple[str, str], dict[str, Any]]


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _norm(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text or "").lower())


def _clean_doi(text: str | None) -> str:
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", str(text or "").strip(), flags=re.IGNORECASE).lower()


def _read_zotcli_storage_dir() -> Path | None:
    config_path = Path.home() / ".config/zotcli/config.ini"
    if not config_path.exists():
        return None

    parser = configparser.ConfigParser()
    parser.read(config_path)
    value = parser.get("zotcli", "storage_dir", fallback="").strip()
    return Path(value) if value else None


def _resolve_zotero_db_and_storage() -> tuple[Path, Path]:
    storage_candidates: list[Path] = []
    configured_storage = _read_zotcli_storage_dir()
    if configured_storage:
        storage_candidates.append(configured_storage)
    storage_candidates.extend(
        [
            Path.home() / "Zotero/storage",
            Path.home() / ".zotero/zotero/storage",
        ]
    )

    db_candidates: list[Path] = []
    if configured_storage:
        db_candidates.append(configured_storage.parent / "zotero.sqlite")
    db_candidates.extend(
        [
            Path.home() / "Zotero/zotero.sqlite",
            Path.home() / ".zotero/zotero/zotero.sqlite",
        ]
    )

    storage_dir = next((path for path in storage_candidates if path.exists()), None)
    db_path = next((path for path in db_candidates if path.exists()), None)

    if storage_dir is None or db_path is None:
        raise FileNotFoundError("未找到本地 Zotero 数据库或 storage 目录。")
    return db_path, storage_dir


def _load_manifest_rows() -> list[dict[str, Any]]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return payload.get("papers") or []


def _load_detail(route_id: str) -> dict[str, Any]:
    return json.loads((PAPER_DETAIL_DIR / f"{route_id}.json").read_text(encoding="utf-8"))


def _build_unmatched_route_id(
    title: str,
    *,
    doi: str = "",
    year: int | None = None,
    authors: list[str] | None = None,
) -> str:
    clean_doi = _clean_doi(doi)
    if clean_doi:
        seed = f"doi:{clean_doi}"
    else:
        seed_parts = ["title", _norm(title)]
        if year is not None:
            seed_parts.append(str(year))
        if authors:
            seed_parts.append(_norm(authors[0]))
        seed = ":".join(part for part in seed_parts if part)
    key = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]
    return f"todo-unmatched-{key}"


def _strip_html(text: str) -> str:
    t = unescape(text or "")
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _extract_arxiv_id_from_doi(doi: str) -> str:
    m = re.match(r"^10\.48550/arxiv\.(.+)$", _clean_doi(doi), flags=re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _fetch_arxiv_abstract(arxiv_id: str) -> str:
    if not arxiv_id:
        return ""
    try:
        resp = requests.get(
            "https://export.arxiv.org/api/query",
            params={"id_list": arxiv_id},
            timeout=20,
        )
        if not resp.ok:
            return ""
        match = re.search(r"<summary>(.*?)</summary>", resp.text, flags=re.DOTALL | re.IGNORECASE)
        if not match:
            return ""
        return _strip_html(match.group(1))
    except Exception:
        return ""


def _fetch_online_abstract(doi: str, title: str) -> str:
    arxiv_id = _extract_arxiv_id_from_doi(doi)
    if arxiv_id:
        abstract = _fetch_arxiv_abstract(arxiv_id)
        if abstract:
            return abstract

    if doi:
        try:
            resp = requests.get(f"https://api.crossref.org/works/{doi}", timeout=20)
            if resp.ok:
                message = (resp.json() or {}).get("message") or {}
                abstract = _strip_html(str(message.get("abstract") or ""))
                if abstract:
                    return abstract
        except Exception:
            pass

    if title:
        try:
            resp = requests.get(
                "https://api.crossref.org/works",
                params={"query.title": title, "rows": 1},
                timeout=20,
            )
            if resp.ok:
                items = ((resp.json() or {}).get("message") or {}).get("items") or []
                if items:
                    abstract = _strip_html(str(items[0].get("abstract") or ""))
                    if abstract:
                        return abstract
        except Exception:
            pass

    return ""


def _identity_aliases(
    *,
    route_id: str = "",
    paper_route_id: str = "",
    paper_id: str = "",
    dir_name: str = "",
    doi: str = "",
    title: str = "",
    zotero_title: str = "",
    year: int | None = None,
    authors: list[str] | None = None,
) -> list[tuple[str, str]]:
    aliases: list[tuple[str, str]] = []

    if route_id:
        aliases.append(("route_id", route_id.strip()))
    if paper_route_id:
        aliases.append(("paper_route_id", paper_route_id.strip()))
    if paper_id:
        aliases.append(("paper_id", paper_id.strip().lower()))
    if dir_name:
        aliases.append(("dir_name", dir_name.strip().lower()))

    clean_doi = _clean_doi(doi)
    if clean_doi:
        aliases.append(("doi", clean_doi))

    first_author = _norm((authors or [""])[0]) if authors else ""
    for candidate in (title, zotero_title):
        title_key = _norm(candidate)
        if not title_key:
            continue
        aliases.append(("title", title_key))
        if year is not None:
            aliases.append(("title_year", f"{title_key}:{year}"))
        if first_author:
            aliases.append(("title_author", f"{title_key}:{first_author}"))

    deduped: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for alias in aliases:
        if alias in seen:
            continue
        seen.add(alias)
        deduped.append(alias)
    return deduped


def _aliases_for_item(item: MatchedTodoPaper) -> list[tuple[str, str]]:
    return _identity_aliases(
        route_id=item.route_id,
        paper_route_id=item.paper_route_id,
        paper_id=item.paper_id,
        dir_name=item.dir_name,
        doi=item.doi or item.zotero_doi,
        title=item.title,
        zotero_title=item.zotero_title,
        year=item.year,
        authors=item.authors,
    )


def _aliases_for_card(card: dict[str, Any]) -> list[tuple[str, str]]:
    return _identity_aliases(
        route_id=str(card.get("route_id") or ""),
        paper_route_id=str(card.get("paper_route_id") or ""),
        paper_id=str(card.get("paper_id") or ""),
        dir_name=str(card.get("dir_name") or ""),
        doi=str(card.get("doi") or ""),
        title=str(card.get("title") or ""),
        zotero_title=str(card.get("zotero_title") or ""),
        year=card.get("year"),
        authors=card.get("authors") or [],
    )


def _build_existing_card_index(cards: list[dict[str, Any]]) -> ExistingCardIndex:
    by_route_id: dict[str, dict[str, Any]] = {}
    alias_candidates: dict[tuple[str, str], dict[str, Any]] = {}
    duplicated_aliases: set[tuple[str, str]] = set()

    for card in cards:
        route_id = str(card.get("route_id") or "").strip()
        if route_id:
            by_route_id[route_id] = card
        for alias in _aliases_for_card(card):
            existing = alias_candidates.get(alias)
            if existing is None:
                alias_candidates[alias] = card
                continue
            if existing is not card:
                duplicated_aliases.add(alias)

    for alias in duplicated_aliases:
        alias_candidates.pop(alias, None)

    return ExistingCardIndex(by_route_id=by_route_id, by_alias=alias_candidates)


def _find_existing_card(item: MatchedTodoPaper, index: ExistingCardIndex) -> dict[str, Any] | None:
    if item.route_id in index.by_route_id:
        return index.by_route_id[item.route_id]
    for alias in _aliases_for_item(item):
        card = index.by_alias.get(alias)
        if card is not None:
            return card
    return None


def _match_todo_papers() -> list[MatchedTodoPaper]:
    db_path, storage_dir = _resolve_zotero_db_and_storage()
    records, _ = parse_zotero_local(db_path, storage_dir=storage_dir, collection_key=TODO_COLLECTION_KEY)

    manifest_rows = _load_manifest_rows()
    doi_map: dict[str, dict[str, Any]] = {}
    title_map: dict[str, list[dict[str, Any]]] = {}
    detail_cache: dict[str, dict[str, Any]] = {}

    for row in manifest_rows:
        route_id = row["route_id"]
        detail = _load_detail(route_id)
        detail_cache[route_id] = detail
        doi_key = _norm(detail.get("doi"))
        if doi_key:
            doi_map[doi_key] = row
        title_key = _norm(row.get("title"))
        if title_key:
            title_map.setdefault(title_key, []).append(row)

    matched: list[MatchedTodoPaper] = []
    unmatched_titles: list[str] = []
    for index, record in enumerate(records):
        row: dict[str, Any] | None = None
        doi_key = _norm(record.doi)
        if doi_key:
            row = doi_map.get(doi_key)

        if row is None:
            title_key = _norm(record.title)
            exact = title_map.get(title_key)
            if exact:
                row = exact[0]

        if row is None:
            title_key = _norm(record.title)
            best_row = None
            best_score = 0.0
            for candidate in manifest_rows:
                score = SequenceMatcher(None, title_key, _norm(candidate.get("title"))).ratio()
                if score > best_score:
                    best_row = candidate
                    best_score = score
            if best_row is not None and best_score >= 0.92:
                row = best_row

        if row is None:
            unmatched_titles.append(record.title)
            abstract = (record.abstract or "").strip() or _fetch_online_abstract(record.doi or "", record.title or "")
            matched.append(
                MatchedTodoPaper(
                    collection_index=index,
                    zotero_title=record.title,
                    zotero_doi=record.doi,
                    route_id=_build_unmatched_route_id(
                        record.title or "untitled",
                        doi=record.doi or "",
                        year=record.year,
                        authors=record.authors or [],
                    ),
                    paper_route_id="",
                    dir_name="",
                    paper_id="",
                    title=record.title or "Untitled",
                    authors=record.authors or [],
                    year=record.year,
                    journal=record.journal or "",
                    doi=record.doi or "",
                    read_status="unread",
                    abstract=abstract,
                )
            )
            continue

        detail = detail_cache[row["route_id"]]
        paper_dir = ROOT / "data/papers" / row["dir_name"]
        if not paper_dir.exists() or not (paper_dir / "meta.json").exists():
            unmatched_titles.append(f"{record.title} [missing local dir: {row['dir_name']}]")
            matched.append(
                MatchedTodoPaper(
                    collection_index=index,
                    zotero_title=record.title,
                    zotero_doi=record.doi,
                    route_id=row["route_id"],
                    paper_route_id=row["route_id"],
                    dir_name="",
                    paper_id=row.get("paper_id") or "",
                    title=detail.get("title") or row.get("title") or record.title,
                    authors=detail.get("authors") or record.authors or [],
                    year=detail.get("year") or record.year,
                    journal=detail.get("journal") or record.journal or "",
                    doi=detail.get("doi") or record.doi or "",
                    read_status=detail.get("read_status") or "unread",
                    abstract=(detail.get("abstract") or record.abstract or "").strip(),
                )
            )
            continue

        meta = read_meta(paper_dir)
        matched.append(
            MatchedTodoPaper(
                collection_index=index,
                zotero_title=record.title,
                zotero_doi=record.doi,
                route_id=row["route_id"],
                paper_route_id=row["route_id"],
                dir_name=row["dir_name"],
                paper_id=row.get("paper_id") or "",
                title=meta.get("title") or detail.get("title") or row.get("title") or record.title,
                authors=meta.get("authors") or detail.get("authors") or [],
                year=meta.get("year") or detail.get("year"),
                journal=meta.get("journal") or detail.get("journal") or "",
                doi=meta.get("doi") or detail.get("doi") or record.doi or "",
                read_status=meta.get("read_status") or detail.get("read_status") or "unread",
                abstract=(meta.get("abstract") or detail.get("abstract") or record.abstract or "").strip(),
            )
        )

    if unmatched_titles:
        print(
            f"[WARN] {len(unmatched_titles)} 条 Todo 未匹配到本地论文，已纳入兜底卡片。",
            flush=True,
        )
        for title in unmatched_titles[:10]:
            print(f"  - {title}", flush=True)
        if len(unmatched_titles) > 10:
            print(f"  ... 其余 {len(unmatched_titles) - 10} 条省略", flush=True)

    return matched


def _build_prompt(paper_dir: Path) -> str:
    content = _get_paper_content(paper_dir, max_l4_chars=10**9)
    return (
        "以下是论文的完整输入，请基于完整输入进行快速泛读分析。\n\n"
        f"标题: {content['l1'].get('title', '')}\n"
        f"作者: {', '.join(content['l1'].get('authors', []))}\n"
        f"年份: {content['l1'].get('year', '')}\n"
        f"期刊/会议: {content['l1'].get('journal', '')}\n"
        f"DOI: {content['l1'].get('doi', '')}\n\n"
        f"摘要:\n{content['l2']}\n\n"
        f"结论:\n{content['l3']}\n\n"
        f"正文全文:\n{content['l4']}\n"
    )


def _truncate(text: str, n: int = 280) -> str:
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip() + "…"


def _split_sentences(text: str) -> list[str]:
    raw = re.split(r"(?<=[。！？.!?])\s+|\n+", str(text or ""))
    return [re.sub(r"\s+", " ", t).strip() for t in raw if t and t.strip()]


def _build_fallback_body(content: dict[str, Any], *, err: Exception | None = None) -> dict[str, Any]:
    abstract = str(content.get("l2") or "").strip()
    conclusion = str(content.get("l3") or "").strip()

    abs_sents = _split_sentences(abstract)
    con_sents = _split_sentences(conclusion)

    core = abs_sents[0] if abs_sents else _truncate(abstract, 220)
    c1 = con_sents[0] if con_sents else (abs_sents[1] if len(abs_sents) > 1 else _truncate(abstract, 180))
    c2 = con_sents[1] if len(con_sents) > 1 else (abs_sents[2] if len(abs_sents) > 2 else _truncate(conclusion or abstract, 180))

    marker = "（自动兜底生成：模型调用失败）"
    if err is not None:
        marker = f"（自动兜底生成：{_truncate(str(err), 80)}）"

    return _normalize_card_body(
        {
            "core_innovation": _truncate(core, 280),
            "technical_contributions": [
                {"title": "创新点 1", "body": _truncate(c1, 240)},
                {"title": "创新点 2", "body": _truncate(c2, 240)},
            ],
            "methodological_breakthrough": {
                "novelty": _truncate(con_sents[0] if con_sents else abstract, 240),
                "key_technique": _truncate(abs_sents[0] if abs_sents else abstract, 240),
                "theory": _truncate((con_sents[2] if len(con_sents) > 2 else "论文正文未提供明确理论证明细节。"), 240),
            },
            "key_results": {
                "benchmarks": _truncate((con_sents[0] if con_sents else "详见论文实验章节。"), 220),
                "improvements": _truncate((con_sents[1] if len(con_sents) > 1 else "详见论文指标对比表。"), 220),
                "ablation": _truncate((con_sents[2] if len(con_sents) > 2 else "详见论文消融实验。"), 220),
            },
            "limitations": {
                "current": _truncate((con_sents[-2] if len(con_sents) >= 2 else "局限性需结合全文进一步验证。"), 220),
                "future": _truncate((con_sents[-1] if con_sents else "未来工作方向需结合作者讨论章节。"), 220),
                "transferability": "该方法在相近机器人控制/策略学习任务中具备潜在迁移性，需按任务重新验证。",
            },
            "one_line_summary": _truncate(f"{core} {marker}", 260),
        }
    )


def _build_fallback_from_metadata(item: MatchedTodoPaper) -> dict[str, Any]:
    abstract = _strip_html(item.abstract or "")
    sents = _split_sentences(abstract)
    core = sents[0] if sents else f"基于公开元数据，本文围绕《{item.title}》提出了面向目标任务的方法。"
    c1 = sents[1] if len(sents) > 1 else "摘要主要强调了方法设计与目标场景，但未给出全文级别的技术展开。"
    c2 = sents[2] if len(sents) > 2 else "公开摘要可用于判断研究方向与方法轮廓，但不足以支持更细的实验归因。"
    abstract_hint = "摘要未披露具体 benchmark、数值或消融细节。"

    return _normalize_card_body(
        {
            "core_innovation": _truncate(f"从公开摘要看，本文的核心在于：{core}", 280),
            "technical_contributions": [
                {"title": "创新点 1", "body": _truncate(c1, 240)},
                {"title": "创新点 2", "body": _truncate(c2, 240)},
            ],
            "methodological_breakthrough": {
                "novelty": _truncate(f"摘要显示该工作试图在《{item.title}》对应问题上提出新的方法路径。", 240),
                "key_technique": _truncate(c1, 240),
                "theory": "仅凭公开元数据无法确认是否提供新的理论证明；如有需要应回看正文。",
            },
            "key_results": {
                "benchmarks": item.journal or abstract_hint,
                "improvements": abstract_hint,
                "ablation": "摘要通常不会完整覆盖消融实验，关键模块贡献需以正文为准。",
            },
            "limitations": {
                "current": "当前判断只基于公开元数据与摘要，边界条件、失败案例与训练细节都不充分。",
                "future": "若正文成立，可进一步考察它在更复杂任务与更强泛化设定下的可扩展性。",
                "transferability": "方法思想可能迁移到相近控制任务，但是否成立取决于正文中的实现细节与实验设置。",
            },
            "one_line_summary": _truncate(f"基于公开摘要，这篇工作值得关注的点是：{core}", 240),
        }
    )


def _parse_model_json(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", candidate)
        candidate = re.sub(r"\n```$", "", candidate)
        candidate = candidate.strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start >= 0 and end > start:
            return json.loads(candidate[start : end + 1])
        raise


def _normalize_card_body(payload: dict[str, Any]) -> dict[str, Any]:
    contributions = payload.get("technical_contributions") or []
    normalized_contributions = []
    for item in contributions[:4]:
        if isinstance(item, dict):
            title = str(item.get("title") or "").strip()
            body = str(item.get("body") or "").strip()
        else:
            title = ""
            body = str(item or "").strip()
        if title or body:
            normalized_contributions.append({"title": title, "body": body})

    while len(normalized_contributions) < 2:
        normalized_contributions.append({"title": f"创新点 {len(normalized_contributions) + 1}", "body": ""})

    method = payload.get("methodological_breakthrough") or {}
    results = payload.get("key_results") or {}
    limitations = payload.get("limitations") or {}

    return {
        "core_innovation": str(payload.get("core_innovation") or "").strip(),
        "technical_contributions": normalized_contributions,
        "methodological_breakthrough": {
            "novelty": str(method.get("novelty") or "").strip(),
            "key_technique": str(method.get("key_technique") or "").strip(),
            "theory": str(method.get("theory") or "").strip(),
        },
        "key_results": {
            "benchmarks": str(results.get("benchmarks") or "").strip(),
            "improvements": str(results.get("improvements") or "").strip(),
            "ablation": str(results.get("ablation") or "").strip(),
        },
        "limitations": {
            "current": str(limitations.get("current") or "").strip(),
            "future": str(limitations.get("future") or "").strip(),
            "transferability": str(limitations.get("transferability") or "").strip(),
        },
        "one_line_summary": str(payload.get("one_line_summary") or "").strip(),
    }


def _iter_card_texts(card: dict[str, Any]) -> list[str]:
    texts = [
        str(card.get("core_innovation") or ""),
        str(card.get("one_line_summary") or ""),
    ]
    for item in card.get("technical_contributions") or []:
        if isinstance(item, dict):
            texts.append(str(item.get("title") or ""))
            texts.append(str(item.get("body") or ""))
    for block_name in ("methodological_breakthrough", "key_results", "limitations"):
        block = card.get(block_name) or {}
        if isinstance(block, dict):
            texts.extend(str(value or "") for value in block.values())
    return texts


def _card_needs_quality_refresh(card: dict[str, Any]) -> bool:
    generation_mode = str(card.get("generation_mode") or "").strip().lower()
    if generation_mode == "fallback":
        return True

    texts = _iter_card_texts(card)
    if any(marker in text for marker in FALLBACK_MARKERS for text in texts):
        return True

    results = card.get("key_results") or {}
    return (
        str(results.get("benchmarks") or "").strip() == "详见论文实验章节。"
        and str(results.get("improvements") or "").strip() == "详见论文指标对比表。"
        and str(results.get("ablation") or "").strip() == "详见论文消融实验。"
    )


def _resolve_llm_config(cfg, model: str) -> tuple[Any, str]:
    model_name = (model or "").strip()
    normalized = model_name.lower()
    backend = str(getattr(cfg.llm, "backend", "") or "").lower()

    if normalized.startswith("gpt-") or normalized.startswith(("o1", "o3", "o4")) or "codex" in normalized:
        backend = "codex-mcp"
    elif normalized.startswith("gemini-"):
        backend = "gemini-mcp"

    llm_cfg = replace(cfg.llm, backend=backend, model=model_name or cfg.llm.model)
    resolved_key = "" if backend in {"gemini-mcp", "codex-mcp"} else cfg.resolved_api_key()
    return llm_cfg, resolved_key


def _run_model(prompt: str, cfg, *, model: str, timeout: int, system: str = CARD_SYSTEM_PROMPT) -> dict[str, Any]:
    llm_cfg, api_key = _resolve_llm_config(cfg, model)
    result = call_llm(
        prompt=prompt,
        config=llm_cfg,
        api_key=api_key,
        system=system,
        json_mode=True,
        max_tokens=4000,
        timeout=timeout,
        purpose="todo.cards",
    )
    return _normalize_card_body(_parse_model_json(result.content))


def _load_existing_cards() -> ExistingCardIndex:
    if not OUTPUT_PATH.exists():
        return ExistingCardIndex(by_route_id={}, by_alias={})

    payload = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    cards = payload.get("cards") or []
    return _build_existing_card_index([card for card in cards if card.get("route_id")])


def _search_text(card: dict[str, Any]) -> str:
    pieces = [
        card.get("title", ""),
        " ".join(card.get("authors") or []),
        str(card.get("year") or ""),
        card.get("journal", ""),
        card.get("doi", ""),
        card.get("core_innovation", ""),
        " ".join(item.get("title", "") for item in card.get("technical_contributions") or []),
        " ".join(item.get("body", "") for item in card.get("technical_contributions") or []),
        card.get("methodological_breakthrough", {}).get("novelty", ""),
        card.get("methodological_breakthrough", {}).get("key_technique", ""),
        card.get("methodological_breakthrough", {}).get("theory", ""),
        card.get("key_results", {}).get("benchmarks", ""),
        card.get("key_results", {}).get("improvements", ""),
        card.get("key_results", {}).get("ablation", ""),
        card.get("limitations", {}).get("current", ""),
        card.get("limitations", {}).get("future", ""),
        card.get("limitations", {}).get("transferability", ""),
        card.get("one_line_summary", ""),
    ]
    return "\n".join(piece for piece in pieces if piece).strip()


def _merge_card_metadata(card: dict[str, Any], item: MatchedTodoPaper, *, model: str) -> dict[str, Any]:
    merged = {
        **card,
        "route_id": item.route_id,
        "paper_route_id": item.paper_route_id,
        "paper_id": item.paper_id,
        "dir_name": item.dir_name,
        "title": item.title,
        "zotero_title": item.zotero_title,
        "authors": item.authors,
        "year": item.year,
        "journal": item.journal,
        "venue": item.journal,
        "doi": item.doi,
        "read_status": "unread",
        "collection_name": TODO_COLLECTION_NAME,
        "collection_key": TODO_COLLECTION_KEY,
        "collection_index": item.collection_index,
        "analysis_source": card.get("analysis_source") or ("fulltext" if item.dir_name else "metadata"),
        "source_confidence": card.get("source_confidence") or ("high" if item.dir_name else "limited"),
        "generation_mode": card.get("generation_mode") or ("fallback" if _card_needs_quality_refresh(card) else "llm"),
        "generated_with_model": card.get("generated_with_model") or model,
        "generated_at": card.get("generated_at") or _utc_timestamp(),
    }
    merged["search_text"] = _search_text(merged)
    return merged


def _render_payload(items: list[MatchedTodoPaper], cards_by_route: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cards = [cards_by_route[item.route_id] for item in items if item.route_id in cards_by_route]
    return {
        "version": 1,
        "generated_at": _utc_timestamp(),
        "collection": {
            "key": TODO_COLLECTION_KEY,
            "name": TODO_COLLECTION_NAME,
            "count": len(cards),
        },
        "cards": cards,
    }


def _write_payload(items: list[MatchedTodoPaper], cards_by_route: dict[str, dict[str, Any]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(_render_payload(items, cards_by_route), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _generate_one(item: MatchedTodoPaper, cfg, *, model: str, timeout: int) -> dict[str, Any]:
    if not item.dir_name:
        metadata_prompt = (
            "以下内容仅来自论文基础元数据与摘要，不包含正文全文。请做谨慎分析，绝不要臆造实验数字、消融结论或理论证明。\n\n"
            f"标题: {item.title}\n"
            f"作者: {', '.join(item.authors)}\n"
            f"年份: {item.year or ''}\n"
            f"期刊/会议: {item.journal}\n"
            f"DOI: {item.doi or item.zotero_doi}\n\n"
            f"摘要:\n{_strip_html(item.abstract or '') or '摘要缺失'}\n"
        )
        try:
            generated = _run_model(
                metadata_prompt,
                cfg,
                model=model,
                timeout=timeout,
                system=CARD_METADATA_SYSTEM_PROMPT,
            )
            generation_mode = "llm"
        except Exception as exc:
            print(f"[WARN] 元数据卡片模型调用失败，改用本地兜底生成: {item.route_id} :: {exc}", flush=True)
            generated = _build_fallback_from_metadata(item)
            generation_mode = "fallback"
        return {
            "route_id": item.route_id,
            "paper_route_id": item.paper_route_id,
            "paper_id": item.paper_id,
            "dir_name": item.dir_name,
            "title": item.title,
            "authors": item.authors,
            "year": item.year,
            "journal": item.journal,
            "venue": item.journal,
            "doi": item.doi,
            "read_status": item.read_status,
            "collection_name": TODO_COLLECTION_NAME,
            "collection_key": TODO_COLLECTION_KEY,
            "collection_index": item.collection_index,
            "analysis_source": "metadata",
            "source_confidence": "limited",
            "generation_mode": generation_mode,
            "generated_with_model": model,
            "generated_at": _utc_timestamp(),
            **generated,
            "search_text": "",
        }

    paper_dir = cfg.papers_dir / item.dir_name
    content = _get_paper_content(paper_dir, max_l4_chars=10**9)
    prompt = (
        "以下是论文的完整输入，请基于完整输入进行快速泛读分析。\n\n"
        f"标题: {content['l1'].get('title', '')}\n"
        f"作者: {', '.join(content['l1'].get('authors', []))}\n"
        f"年份: {content['l1'].get('year', '')}\n"
        f"期刊/会议: {content['l1'].get('journal', '')}\n"
        f"DOI: {content['l1'].get('doi', '')}\n\n"
        f"摘要:\n{content['l2']}\n\n"
        f"结论:\n{content['l3']}\n\n"
        f"正文全文:\n{content['l4']}\n"
    )

    try:
        generated = _run_model(prompt, cfg, model=model, timeout=timeout)
        generation_mode = "llm"
    except Exception as exc:
        print(f"[WARN] 模型调用失败，改用本地兜底生成: {item.route_id} :: {exc}", flush=True)
        generated = _build_fallback_body(content, err=exc)
        generation_mode = "fallback"

    return {
        "route_id": item.route_id,
        "paper_route_id": item.paper_route_id,
        "paper_id": item.paper_id,
        "dir_name": item.dir_name,
        "title": item.title,
        "authors": item.authors,
        "year": item.year,
        "journal": item.journal,
        "venue": item.journal,
        "doi": item.doi,
        "read_status": item.read_status,
        "collection_name": TODO_COLLECTION_NAME,
        "collection_key": TODO_COLLECTION_KEY,
        "collection_index": item.collection_index,
        "analysis_source": "fulltext",
        "source_confidence": "high",
        "generation_mode": generation_mode,
        "generated_with_model": model,
        "generated_at": _utc_timestamp(),
        **generated,
        "search_text": "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Todo summary cards for the static Library page.")
    parser.add_argument("--force", action="store_true", help="Regenerate existing cards instead of reusing them.")
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N Todo papers (0 means all).")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent generations.")
    parser.add_argument("--model", default="gpt-5.4-mini", help="Model name.")
    parser.add_argument(
        "--metadata-model",
        default="",
        help="Optional model override for metadata-only cards (unmatched or missing local full text).",
    )
    parser.add_argument(
        "--refresh-metadata-only",
        action="store_true",
        help="Regenerate metadata-only cards even if a previous snapshot card can be reused.",
    )
    parser.add_argument(
        "--refresh-fallback-only",
        action="store_true",
        help="Regenerate cards that still carry fallback markers or placeholder result fields.",
    )
    parser.add_argument("--timeout", type=int, default=900, help="Per-paper generation timeout in seconds.")
    args = parser.parse_args()

    cfg = load_config()
    items = _match_todo_papers()
    if args.limit > 0:
        items = items[: args.limit]

    existing = _load_existing_cards()
    cards_by_route: dict[str, dict[str, Any]] = {}
    pending: list[MatchedTodoPaper] = []
    metadata_model = args.metadata_model or args.model
    refreshed_quality_issues = 0

    for item in items:
        existing_card = None if args.force else _find_existing_card(item, existing)
        should_refresh_metadata = args.refresh_metadata_only and not item.dir_name
        should_refresh_quality = bool(existing_card) and args.refresh_fallback_only and _card_needs_quality_refresh(existing_card)
        if should_refresh_quality:
            refreshed_quality_issues += 1
        if existing_card is not None and not should_refresh_metadata and not should_refresh_quality:
            cards_by_route[item.route_id] = _merge_card_metadata(existing_card, item, model=args.model)
        else:
            pending.append(item)

    print(f"Matched Todo papers: {len(items)}", flush=True)
    print(f"Reusing existing cards: {len(cards_by_route)}", flush=True)
    if args.refresh_fallback_only:
        print(f"Fallback-like cards scheduled for refresh: {refreshed_quality_issues}", flush=True)
    print(f"Pending generation: {len(pending)}", flush=True)

    _write_payload(items, cards_by_route)

    if not pending:
        print(f"Up to date: {OUTPUT_PATH}", flush=True)
        return

    lock = Lock()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {
            executor.submit(
                _generate_one,
                item,
                cfg,
                model=(metadata_model if not item.dir_name else args.model),
                timeout=args.timeout,
            ): item
            for item in pending
        }
        completed = 0
        total = len(pending)
        for future in as_completed(future_map):
            item = future_map[future]
            try:
                card = future.result()
                card = _merge_card_metadata(card, item, model=args.model)
                with lock:
                    cards_by_route[item.route_id] = card
                    _write_payload(items, cards_by_route)
                completed += 1
                print(f"[{completed}/{total}] generated {item.route_id} :: {item.title}", flush=True)
            except Exception as exc:
                print(f"[ERROR] {item.title}: {exc}", file=sys.stderr, flush=True)
                raise

    print(f"Wrote {len(cards_by_route)} cards to {OUTPUT_PATH}", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate Todo summary cards for the static Library page."""

from __future__ import annotations

import argparse
import configparser
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from threading import Lock
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scholaraio.config import load_config
from scholaraio.generate import _get_paper_content
from scholaraio.papers import read_meta
from scholaraio.sources.zotero import parse_zotero_local


TODO_COLLECTION_KEY = "RECF7KND"
TODO_COLLECTION_NAME = "Todo"
OUTPUT_PATH = ROOT / "scholaraio/web/public/site-data/todo-cards.json"
MANIFEST_PATH = ROOT / "scholaraio/web/public/site-data/manifest.json"
PAPER_DETAIL_DIR = ROOT / "scholaraio/web/public/site-data/papers"
SCHEMA_PATH = ROOT / "scripts/todo_card.schema.json"

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

最后几个注意事项：生成内容不要带有来源链接；不要带有不必要的英文注释！专有名词或者重要术语带一下可以！

现在请把上面结构转换成严格 JSON 输出，不要输出 markdown，不要输出代码块，也不要补充额外解释。JSON 字段必须严格匹配给定 schema。"""


@dataclass
class MatchedTodoPaper:
    collection_index: int
    zotero_title: str
    zotero_doi: str
    route_id: str
    dir_name: str
    paper_id: str
    title: str
    authors: list[str]
    year: int | None
    journal: str
    doi: str
    read_status: str


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _norm(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text or "").lower())


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
            raise RuntimeError(f"未能为 Todo 条目匹配本地论文: {record.title}")

        detail = detail_cache[row["route_id"]]
        paper_dir = ROOT / "data/papers" / row["dir_name"]
        meta = read_meta(paper_dir)
        matched.append(
            MatchedTodoPaper(
                collection_index=index,
                zotero_title=record.title,
                zotero_doi=record.doi,
                route_id=row["route_id"],
                dir_name=row["dir_name"],
                paper_id=row.get("paper_id") or "",
                title=meta.get("title") or detail.get("title") or row.get("title") or record.title,
                authors=meta.get("authors") or detail.get("authors") or [],
                year=meta.get("year") or detail.get("year"),
                journal=meta.get("journal") or detail.get("journal") or "",
                doi=meta.get("doi") or detail.get("doi") or record.doi or "",
                read_status=meta.get("read_status") or detail.get("read_status") or "unread",
            )
        )

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


def _parse_codex_json(text: str) -> dict[str, Any]:
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


def _run_codex(prompt: str, *, model: str, timeout: int) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as output_file:
        output_path = Path(output_file.name)

    cmd = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "--output-schema",
        str(SCHEMA_PATH),
        "-o",
        str(output_path),
        "-",
    ]

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"codex exec failed (exit={result.returncode}):\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        raw = output_path.read_text(encoding="utf-8")
        return _normalize_card_body(_parse_codex_json(raw))
    finally:
        output_path.unlink(missing_ok=True)


def _load_existing_cards() -> dict[str, dict[str, Any]]:
    if not OUTPUT_PATH.exists():
        return {}

    payload = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    cards = payload.get("cards") or []
    return {str(card.get("route_id") or ""): card for card in cards if card.get("route_id")}


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
        "paper_id": item.paper_id,
        "dir_name": item.dir_name,
        "title": item.title,
        "authors": item.authors,
        "year": item.year,
        "journal": item.journal,
        "venue": item.journal,
        "doi": item.doi,
        "read_status": card.get("read_status") or item.read_status,
        "collection_name": TODO_COLLECTION_NAME,
        "collection_key": TODO_COLLECTION_KEY,
        "collection_index": item.collection_index,
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
    paper_dir = cfg.papers_dir / item.dir_name
    prompt = _build_prompt(paper_dir)
    generated = _run_codex(prompt, model=model, timeout=timeout)
    return {
        "route_id": item.route_id,
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
        "generated_with_model": model,
        "generated_at": _utc_timestamp(),
        **generated,
        "search_text": "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Todo summary cards for the static Library page.")
    parser.add_argument("--force", action="store_true", help="Regenerate existing cards instead of reusing them.")
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N Todo papers (0 means all).")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent codex generations.")
    parser.add_argument("--model", default="gpt-5.4-mini", help="Codex model name.")
    parser.add_argument("--timeout", type=int, default=900, help="Per-paper codex timeout in seconds.")
    args = parser.parse_args()

    cfg = load_config()
    items = _match_todo_papers()
    if args.limit > 0:
        items = items[: args.limit]

    existing = _load_existing_cards()
    cards_by_route: dict[str, dict[str, Any]] = {}
    pending: list[MatchedTodoPaper] = []

    for item in items:
        if not args.force and item.route_id in existing:
            cards_by_route[item.route_id] = _merge_card_metadata(existing[item.route_id], item, model=args.model)
        else:
            pending.append(item)

    print(f"Matched Todo papers: {len(items)}", flush=True)
    print(f"Reusing existing cards: {len(cards_by_route)}", flush=True)
    print(f"Pending generation: {len(pending)}", flush=True)

    _write_payload(items, cards_by_route)

    if not pending:
        print(f"Up to date: {OUTPUT_PATH}", flush=True)
        return

    lock = Lock()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {
            executor.submit(_generate_one, item, cfg, model=args.model, timeout=args.timeout): item
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

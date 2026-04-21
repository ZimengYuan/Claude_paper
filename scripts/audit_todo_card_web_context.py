#!/usr/bin/env python3
"""Audit Todo cards for cases that likely need web-context supplementation."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TODO_CARDS = ROOT / "scholaraio/web/public/site-data/todo-cards.json"

GENERIC_MARKERS = (
    "摘要未披露",
    "未披露",
    "文中未清楚披露",
    "正文未提供",
    "仅凭公开元数据",
    "公开元数据",
    "无法确认",
    "详见论文",
    "待进一步",
    "需结合全文",
    "局限性需结合",
    "自动兜底生成",
)

RESULT_SIGNAL_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:%|×|x|cm|m/s|points?|分|倍|hours?|h|ms|s\b|k\b|M\b|B\b)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AuditFinding:
    priority: int
    collection_index: int | None
    route_id: str
    title: str
    analysis_source: str
    source_confidence: str
    generation_mode: str
    reasons: tuple[str, ...]


def _iter_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        texts: list[str] = []
        for item in value.values():
            texts.extend(_iter_text(item))
        return texts
    if isinstance(value, list):
        texts = []
        for item in value:
            texts.extend(_iter_text(item))
        return texts
    return []


def _card_text(card: dict[str, Any]) -> str:
    fields = [
        "core_innovation",
        "technical_contributions",
        "methodological_breakthrough",
        "key_results",
        "limitations",
        "one_line_summary",
    ]
    texts: list[str] = []
    for field in fields:
        texts.extend(_iter_text(card.get(field)))
    return "\n".join(text for text in texts if text).strip()


def audit_card(card: dict[str, Any]) -> AuditFinding | None:
    reasons: list[str] = []
    analysis_source = str(card.get("analysis_source") or "").strip()
    source_confidence = str(card.get("source_confidence") or "").strip()
    generation_mode = str(card.get("generation_mode") or "").strip()

    if analysis_source != "fulltext" or source_confidence != "high":
        reasons.append("metadata-only or limited source")
    if generation_mode == "fallback":
        reasons.append("fallback generation")

    text = _card_text(card)
    generic_hits = [marker for marker in GENERIC_MARKERS if marker in text]
    if generic_hits:
        reasons.append("generic uncertainty markers: " + ", ".join(generic_hits[:3]))

    key_results = card.get("key_results") or {}
    key_result_text = " ".join(
        str(key_results.get(key) or "")
        for key in ("benchmarks", "improvements", "ablation")
    )
    if not RESULT_SIGNAL_RE.search(key_result_text):
        reasons.append("no clear numeric result signal")

    if not reasons:
        return None

    priority = 3
    if analysis_source != "fulltext" or source_confidence != "high" or generation_mode == "fallback":
        priority = 1
    elif generic_hits:
        priority = 2

    return AuditFinding(
        priority=priority,
        collection_index=card.get("collection_index"),
        route_id=str(card.get("route_id") or ""),
        title=str(card.get("title") or ""),
        analysis_source=analysis_source,
        source_confidence=source_confidence,
        generation_mode=generation_mode,
        reasons=tuple(reasons),
    )


def audit_cards(cards: list[dict[str, Any]]) -> list[AuditFinding]:
    findings = [finding for card in cards if (finding := audit_card(card))]
    return sorted(findings, key=lambda item: (item.priority, item.collection_index if item.collection_index is not None else 10**9, item.title))


def render_markdown(findings: list[AuditFinding], *, total_cards: int, snapshot_path: Path) -> str:
    counts = Counter(finding.priority for finding in findings)
    lines = [
        "# Todo Card Web Context Audit",
        "",
        f"- Snapshot: `{snapshot_path}`",
        f"- Total cards: {total_cards}",
        f"- Flagged cards: {len(findings)}",
        f"- Priority 1: {counts.get(1, 0)}",
        f"- Priority 2: {counts.get(2, 0)}",
        f"- Priority 3: {counts.get(3, 0)}",
        "",
        "Priority meaning:",
        "",
        "- P1: metadata-only, limited-source, or fallback cards. These should be regenerated first with web search.",
        "- P2: full-text cards that still contain generic uncertainty markers; web search may fill benchmark, venue, project, or comparison context.",
        "- P3: cards with no clear numeric result signal; web search is optional and should be used only if it improves reading value.",
        "",
        "| Priority | Index | Route | Title | Source | Reasons |",
        "|---|---:|---|---|---|---|",
    ]
    for finding in findings:
        source = f"{finding.analysis_source}/{finding.source_confidence}/{finding.generation_mode}"
        reasons = "; ".join(finding.reasons)
        title = finding.title.replace("|", "\\|")
        lines.append(
            f"| P{finding.priority} | {finding.collection_index if finding.collection_index is not None else ''} "
            f"| `{finding.route_id}` | {title} | {source} | {reasons} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Todo cards that likely need web-context supplementation.")
    parser.add_argument("--todo-cards", default=str(DEFAULT_TODO_CARDS), help="Path to todo-cards.json")
    parser.add_argument("--output", default="", help="Optional Markdown report path")
    args = parser.parse_args()

    todo_path = Path(args.todo_cards)
    payload = json.loads(todo_path.read_text(encoding="utf-8"))
    cards = payload.get("cards") or []
    findings = audit_cards(cards)
    report = render_markdown(findings, total_cards=len(cards), snapshot_path=todo_path)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")

    print(report)


if __name__ == "__main__":
    main()

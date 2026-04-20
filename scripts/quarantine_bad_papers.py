#!/usr/bin/env python3
"""Conservatively quarantine obviously broken or shadow duplicate paper entries."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from scholaraio.metadata_quality import collect_metadata_issues, normalize_title_key, normalize_year_value

ROOT = Path(__file__).resolve().parents[1]
PAPERS_DIR = ROOT / "data" / "papers"
WORKSPACE_DIR = ROOT / "workspace"

_UUID_DIR_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


@dataclass
class Record:
    path: Path
    meta: dict
    title_key: str
    doi: str
    has_authors: bool
    has_materials: bool
    paper_md_size: int
    issues: list[str]
    quality_score: int
    is_uuid_dir: bool


def load_records(papers_dir: Path) -> list[Record]:
    records: list[Record] = []
    for meta_path in sorted(papers_dir.glob("*/meta.json")):
        paper_dir = meta_path.parent
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        title_key = normalize_title_key(str(meta.get("title") or ""))
        doi = str(meta.get("doi") or "").strip()
        authors = meta.get("authors")
        has_authors = isinstance(authors, list) and any(str(author).strip() for author in authors)
        has_materials = (paper_dir / "summary.md").exists() or (paper_dir / "method.md").exists()
        paper_md = paper_dir / "paper.md"
        paper_md_size = paper_md.stat().st_size if paper_md.exists() else 0
        issues = [issue.rule for issue in collect_metadata_issues(meta)]
        records.append(
            Record(
                path=paper_dir,
                meta=meta,
                title_key=title_key,
                doi=doi,
                has_authors=has_authors,
                has_materials=has_materials,
                paper_md_size=paper_md_size,
                issues=issues,
                quality_score=quality_score(meta, paper_dir, has_authors, paper_md_size, has_materials),
                is_uuid_dir=bool(_UUID_DIR_RE.fullmatch(paper_dir.name)),
            )
        )
    return records


def quality_score(meta: dict, paper_dir: Path, has_authors: bool, paper_md_size: int, has_materials: bool) -> int:
    score = 0
    if str(meta.get("doi") or "").strip():
        score += 2
    if has_authors:
        score += 1
    if str(meta.get("first_author_lastname") or "").strip():
        score += 1
    if normalize_year_value(meta.get("year")) is not None:
        score += 1
    if str(meta.get("journal") or "").strip():
        score += 1
    if paper_md_size >= 1000:
        score += 1
    if has_materials:
        score += 2
    if (paper_dir / "notes.md").exists():
        score += 1
    return score


def build_candidates(records: list[Record]) -> list[dict]:
    by_title: dict[str, list[Record]] = {}
    for record in records:
        if record.title_key:
            by_title.setdefault(record.title_key, []).append(record)

    candidates: dict[str, dict] = {}
    for record in records:
        if {"invalid_title", "missing_author_identity"} <= set(record.issues) and not record.doi:
            candidates[record.path.name] = {
                "dir_name": record.path.name,
                "title": record.meta.get("title") or "",
                "reason": "placeholder_entry",
                "details": "标题/作者信息均损坏，且无 DOI，可判定为无效残留",
            }
            continue
        if "section_heading_title" in record.issues:
            candidates[record.path.name] = {
                "dir_name": record.path.name,
                "title": record.meta.get("title") or "",
                "reason": "section_heading_title",
                "details": "标题疑似章节标题，属于明显错误抽取结果",
            }

    for group in by_title.values():
        if len(group) < 2:
            continue
        best = max(group, key=lambda rec: (rec.quality_score, bool(rec.doi), not rec.is_uuid_dir, rec.paper_md_size))
        for record in group:
            if record.path == best.path or record.path.name in candidates:
                continue
            if record.has_materials or record.doi or not best.doi:
                continue
            shadow_marker = (
                record.is_uuid_dir
                or "-None" in record.path.name
                or record.paper_md_size < 1000
                or not record.has_authors
            )
            if not shadow_marker:
                continue
            if best.quality_score < record.quality_score + 3:
                continue
            candidates[record.path.name] = {
                "dir_name": record.path.name,
                "title": record.meta.get("title") or "",
                "reason": "shadow_duplicate",
                "details": f"被更完整条目 {best.path.name} 遮蔽",
                "shadowed_by": best.path.name,
            }

    return sorted(candidates.values(), key=lambda item: item["dir_name"])


def write_report(report_dir: Path, candidates: list[dict], *, applied: bool) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    report_json = report_dir / "quarantine_report.json"
    report_md = report_dir / "README.md"
    payload = {
        "generated_at": str(date.today()),
        "applied": applied,
        "count": len(candidates),
        "entries": candidates,
    }
    report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Suspicious Paper Quarantine",
        "",
        f"- Generated: {date.today()}",
        f"- Applied: {'yes' if applied else 'no'}",
        f"- Count: {len(candidates)}",
        "",
    ]
    for idx, item in enumerate(candidates, 1):
        shadow = f" | shadowed_by: `{item['shadowed_by']}`" if item.get("shadowed_by") else ""
        lines.append(
            f"{idx}. `{item['dir_name']}` | {item['reason']} | {item['title'] or 'N/A'}{shadow} | {item['details']}"
        )
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_md, report_json


def move_candidates(candidates: list[dict], papers_dir: Path, archive_dir: Path) -> None:
    archive_dir.mkdir(parents=True, exist_ok=True)
    for item in candidates:
        source = papers_dir / item["dir_name"]
        if not source.exists():
            continue
        target = archive_dir / item["dir_name"]
        suffix = 2
        while target.exists():
            target = archive_dir / f"{item['dir_name']}-{suffix}"
            suffix += 1
        shutil.move(str(source), str(target))


def main() -> None:
    parser = argparse.ArgumentParser(description="安全隔离明显损坏或被遮蔽的本地论文目录")
    parser.add_argument("--papers-dir", type=Path, default=PAPERS_DIR, help="默认 data/papers")
    parser.add_argument("--apply", action="store_true", help="实际移动到 workspace/merge_archive")
    args = parser.parse_args()

    records = load_records(args.papers_dir)
    candidates = build_candidates(records)
    archive_dir = WORKSPACE_DIR / "merge_archive" / f"suspicious_entries_{date.today()}"

    if args.apply:
        move_candidates(candidates, args.papers_dir, archive_dir)
        report_dir = archive_dir
    else:
        report_dir = WORKSPACE_DIR / f"suspicious_entries_preview_{date.today()}"
    report_md, report_json = write_report(report_dir, candidates, applied=args.apply)

    print(f"Candidates: {len(candidates)}")
    print(f"Markdown: {report_md}")
    print(f"JSON: {report_json}")


if __name__ == "__main__":
    main()

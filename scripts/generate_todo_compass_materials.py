#!/usr/bin/env python3
"""Generate Todo score.md and report.md materials with Paper Compass skills."""

from __future__ import annotations

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scholaraio.config import load_config
from scholaraio.papers import (
    read_meta,
    read_readable_report,
    read_score_report,
    update_meta,
    write_readable_report,
    write_score_report,
)
from scholaraio.todo_compass import (
    build_compass_context,
    ensure_todo_placeholder_paper,
    generate_compass_readable_report,
    generate_compass_score_report,
    parse_compass_score_report,
)
from scholaraio.web_static import export_static_site_data
from scripts.generate_todo_cards import _match_todo_papers


SITE_DATA_DIR = ROOT / "scholaraio/web/public/site-data"


def _run_python_script(relative_path: str, *args: str) -> None:
    cmd = [sys.executable, str(ROOT / relative_path), *args]
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def _ensure_todo_placeholders(cfg) -> tuple[int, int]:
    created = 0
    updated = 0
    for item in _match_todo_papers():
        if item.dir_name:
            continue
        paper_dir = ensure_todo_placeholder_paper(
            cfg,
            title=item.title,
            authors=item.authors,
            year=item.year,
            journal=item.journal,
            doi=item.doi or item.zotero_doi,
            abstract=item.abstract,
            read_status=item.read_status,
        )
        if (paper_dir / "summary.md").exists() or (paper_dir / "score.md").exists() or (paper_dir / "report.md").exists():
            updated += 1
        else:
            created += 1
    return created, updated


def _refresh_todo_snapshot(cfg, *, todo_model: str, todo_workers: int, timeout: int) -> None:
    export_static_site_data(cfg, SITE_DATA_DIR)
    _run_python_script(
        "scripts/generate_todo_cards.py",
        "--workers", str(max(1, todo_workers)),
        "--model", todo_model,
        "--metadata-model", todo_model,
        "--refresh-metadata-only",
        "--refresh-fallback-only",
        "--timeout", str(timeout),
    )
    _run_python_script("scripts/sync_todo_summaries.py")


def _needs_score_generation(paper_dir: Path, *, force: bool) -> bool:
    if force:
        return True
    report = read_score_report(paper_dir)
    if not report:
        return True
    parsed = parse_compass_score_report(report)
    return "overall_score" not in parsed


def _needs_readable_report_generation(paper_dir: Path, *, force: bool) -> bool:
    if force:
        return True
    report = read_readable_report(paper_dir)
    return not bool((report or "").strip())


def _update_meta_from_score(paper_dir: Path, rating: dict[str, Any], *, generated_at: str | None = None) -> None:
    meta = read_meta(paper_dir)
    update_meta(
        paper_dir,
        rating=rating,
        score_source="paper_compass_score",
        score_generated_at=generated_at or meta.get("score_generated_at") or "",
    )


def _generate_for_item(item, cfg, args) -> dict[str, Any]:
    paper_dir = cfg.papers_dir / item.dir_name
    context: dict[str, Any] | None = None
    score_generated = False
    report_generated = False

    score_markdown = read_score_report(paper_dir)
    rating: dict[str, Any] | None = None
    if _needs_score_generation(paper_dir, force=args.force):
        context = build_compass_context(paper_dir, memory_path=args.memory_path)
        score_markdown, rating = generate_compass_score_report(
            cfg,
            paper_dir,
            context=context,
            model=args.score_model,
            timeout=args.timeout,
        )
        write_score_report(paper_dir, score_markdown)
        score_generated = True
    elif score_markdown:
        rating = parse_compass_score_report(score_markdown)

    if rating is None or "overall_score" not in rating:
        raise ValueError(f"Unable to parse score report for {paper_dir.name}")

    _update_meta_from_score(paper_dir, rating, generated_at=args.generated_at)

    if _needs_readable_report_generation(paper_dir, force=args.force):
        if context is None:
            context = build_compass_context(paper_dir, memory_path=args.memory_path)
        readable_report = generate_compass_readable_report(
            cfg,
            paper_dir,
            score_report=score_markdown or "",
            context=context,
            model=args.report_model,
            timeout=args.timeout,
        )
        write_readable_report(paper_dir, readable_report)
        report_generated = True
        update_meta(
            paper_dir,
            report_source="paper_compass_learnpath",
            report_generated_at=args.generated_at,
        )

    return {
        "title": item.title,
        "dir_name": item.dir_name,
        "score_generated": score_generated,
        "report_generated": report_generated,
        "overall_score": rating.get("overall_score"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Todo score/report materials with Paper Compass skills")
    parser.add_argument("--force", action="store_true", help="Regenerate score.md and report.md even if they already exist")
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N Todo papers after placeholder sync")
    parser.add_argument("--workers", type=int, default=2, help="Number of concurrent Todo material generations")
    parser.add_argument("--todo-workers", type=int, default=2, help="Concurrency for Todo card regeneration")
    parser.add_argument("--todo-model", default="gpt-5.4", help="Model used when refreshing Todo cards before summary sync")
    parser.add_argument("--score-model", default="fallback", help="Model used for score.md generation; use fallback for deterministic local generation")
    parser.add_argument("--report-model", default="fallback", help="Model used for report.md generation; use fallback for deterministic local generation")
    parser.add_argument("--timeout", type=int, default=900, help="Per-paper timeout in seconds")
    parser.add_argument("--progress-step", type=int, default=10, help="Print a progress summary every N completed Todo papers")
    parser.add_argument("--memory-path", default="", help="Optional memory.md path for learnpath personalization")
    args = parser.parse_args()

    cfg = load_config()
    args.generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    created, updated = _ensure_todo_placeholders(cfg)
    print(f"Placeholder Todo papers created: {created}", flush=True)
    print(f"Placeholder Todo papers updated: {updated}", flush=True)

    _refresh_todo_snapshot(cfg, todo_model=args.todo_model, todo_workers=args.todo_workers, timeout=args.timeout)

    items = [item for item in _match_todo_papers() if item.dir_name]
    if args.limit > 0:
        items = items[:args.limit]

    pending = []
    for item in items:
        paper_dir = cfg.papers_dir / item.dir_name
        if _needs_score_generation(paper_dir, force=args.force) or _needs_readable_report_generation(paper_dir, force=args.force):
            pending.append(item)
        else:
            score_markdown = read_score_report(paper_dir)
            if score_markdown:
                rating = parse_compass_score_report(score_markdown)
                if rating.get("overall_score") is not None:
                    _update_meta_from_score(paper_dir, rating)

    print(f"Matched local Todo papers after placeholder sync: {len(items)}", flush=True)
    print(f"Pending Todo score/report generations: {len(pending)}", flush=True)

    completed = 0
    failures: list[str] = []
    if pending:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            future_map = {executor.submit(_generate_for_item, item, cfg, args): item for item in pending}
            for future in as_completed(future_map):
                item = future_map[future]
                try:
                    result = future.result()
                    completed += 1
                    print(
                        f"[{completed}/{len(pending)}] compass generated :: {result['dir_name']} :: score={result['overall_score']}",
                        flush=True,
                    )
                    if completed % max(1, args.progress_step) == 0:
                        print(
                            f"[progress] completed {completed}/{len(pending)} Todo papers with score+report generation.",
                            flush=True,
                        )
                except Exception as exc:
                    failures.append(f"{item.dir_name or item.title}: {exc}")
                    print(f"[WARN] compass generation failed :: {item.title} :: {exc}", flush=True)

    export_static_site_data(cfg, SITE_DATA_DIR)

    print(f"Todo score/report completed: {completed}", flush=True)
    print(f"Todo score/report failures: {len(failures)}", flush=True)
    if failures:
        for entry in failures[:20]:
            print(f"  - {entry}", flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

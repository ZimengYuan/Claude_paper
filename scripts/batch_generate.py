#!/usr/bin/env python3
"""Batch generate learning materials for all papers."""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scholaraio.generate import generate_summary, generate_method
from scholaraio.papers import iter_paper_dirs, summary_path, method_path
from scholaraio.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
_log = logging.getLogger(__name__)


def needs_generation(paper_d: Path, file_path_fn) -> bool:
    """Check if a paper needs generation for a specific file type."""
    return not file_path_fn(paper_d).exists()


def generate_all_materials(force: bool = False):
    """Generate all missing materials for all papers."""
    cfg = load_config()
    papers_dir = cfg.papers_dir

    summary_ok = summary_fail = summary_skip = 0
    method_ok = method_fail = method_skip = 0

    papers = list(iter_paper_dirs(papers_dir))
    total = len(papers)
    print(f"\nTotal papers: {total}")

    # Count missing first
    summary_missing = sum(1 for p in papers if needs_generation(p, summary_path))
    method_missing = sum(1 for p in papers if needs_generation(p, method_path))
    print(f"Missing - summary: {summary_missing}, method: {method_missing}\n")

    for i, paper_d in enumerate(papers, 1):
        print(f"[{i}/{total}] {paper_d.name}")

        # Generate summary
        if needs_generation(paper_d, summary_path):
            try:
                generate_summary(paper_d, cfg, force=False)
                summary_ok += 1
                print(f"  + summary generated")
            except Exception as e:
                summary_fail += 1
                print(f"  x summary failed: {e}")

        else:
            summary_skip += 1

        # Generate method
        if needs_generation(paper_d, method_path):
            try:
                generate_method(paper_d, cfg, force=False)
                method_ok += 1
                print(f"  + method generated")
            except Exception as e:
                method_fail += 1
                print(f"  x method failed: {e}")
        else:
            method_skip += 1

    print(f"\n{'='*50}")
    print(f"SUMMARY:")
    print(f"  summary: {summary_ok} ok | {summary_fail} fail | {summary_skip} skip")
    print(f"  method:  {method_ok} ok | {method_fail} fail | {method_skip} skip")
    print(f"{'='*50}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch generate learning materials")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    print("Starting batch generation...")
    print("=" * 50)
    generate_all_materials(force=args.force)
#!/usr/bin/env python3
"""只读检查：网页快照数量与本地库/Zotero 数量对齐情况。"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT_DIR = ROOT / "scholaraio" / "web" / "public" / "site-data"
DEFAULT_PAPERS_DIR = ROOT / "data" / "papers"
DEFAULT_ZOTERO_DB_CANDIDATES = [
    Path.home() / "Zotero" / "zotero.sqlite",
    Path.home() / ".zotero" / "zotero" / "zotero.sqlite",
]


@dataclass
class DiffRow:
    name: str
    left_name: str
    left: int | None
    right_name: str
    right: int | None

    @property
    def delta(self) -> int | None:
        if self.left is None or self.right is None:
            return None
        return self.left - self.right

    @property
    def ok(self) -> bool:
        if self.left is None or self.right is None:
            return False
        return self.left == self.right


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_local_papers(papers_dir: Path) -> int:
    return sum(1 for d in papers_dir.iterdir() if d.is_dir() and (d / "meta.json").exists())


def _count_local_papers_with_materials(papers_dir: Path) -> int:
    count = 0
    for paper_dir in papers_dir.iterdir():
        if not paper_dir.is_dir():
            continue
        meta_path = paper_dir / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = _read_json(meta_path)
        except json.JSONDecodeError:
            continue

        summary_ready = False
        summary_path = paper_dir / "summary.md"
        if summary_path.exists():
            summary_ready = bool(summary_path.read_text(encoding="utf-8").strip())
        if not summary_ready:
            summary_ready = bool(str(meta.get("summary") or "").strip())

        method_ready = False
        method_path = paper_dir / "method.md"
        if method_path.exists():
            method_ready = bool(method_path.read_text(encoding="utf-8").strip())
        if not method_ready:
            method_ready = bool(str(meta.get("method_summary") or "").strip())

        if summary_ready and method_ready:
            count += 1
    return count


def _resolve_zotero_db(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    for p in DEFAULT_ZOTERO_DB_CANDIDATES:
        if p.exists():
            return p
    return None


def _query_zotero_counts(db_path: Path, todo_collection_key: str) -> dict[str, int]:
    conn = sqlite3.connect(f"file:{db_path}?immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        all_items = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM items i
            JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
            WHERE it.typeName NOT IN ('attachment', 'note')
              AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
            """
        ).fetchone()["n"]

        todo_items = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM items i
            JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
            JOIN collectionItems ci ON ci.itemID = i.itemID
            JOIN collections c ON c.collectionID = ci.collectionID
            WHERE it.typeName NOT IN ('attachment', 'note')
              AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
              AND c.key = ?
            """,
            (todo_collection_key,),
        ).fetchone()["n"]

        todo_items_with_pdf_attachment = conn.execute(
            """
            SELECT COUNT(DISTINCT p.itemID) AS n
            FROM items p
            JOIN itemTypes it ON p.itemTypeID = it.itemTypeID
            JOIN collectionItems ci ON ci.itemID = p.itemID
            JOIN collections c ON c.collectionID = ci.collectionID
            JOIN itemAttachments ia ON ia.parentItemID = p.itemID
            WHERE it.typeName NOT IN ('attachment', 'note')
              AND p.itemID NOT IN (SELECT itemID FROM deletedItems)
              AND ia.contentType = 'application/pdf'
              AND c.key = ?
            """,
            (todo_collection_key,),
        ).fetchone()["n"]

        return {
            "zotero_all_items": int(all_items),
            "zotero_todo_items": int(todo_items),
            "zotero_todo_items_with_pdf_attachment": int(todo_items_with_pdf_attachment),
        }
    finally:
        conn.close()


def _print_human_report(snapshot: dict[str, Any], diff_rows: list[DiffRow]) -> None:
    print("=== Snapshot 对齐检查（只读）===")
    print(f"todo_snapshot_generated_at: {snapshot.get('todo_snapshot_generated_at')}")
    print(f"library_snapshot_generated_at: {snapshot.get('library_snapshot_generated_at')}")
    print("")
    for row in diff_rows:
        status = "OK" if row.ok else "DIFF"
        delta = row.delta
        delta_text = "N/A" if delta is None else f"{delta:+d}"
        print(
            f"[{status}] {row.name}: "
            f"{row.left_name}={row.left} | {row.right_name}={row.right} | delta={delta_text}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="检查网页快照数量与本地库/Zotero 的对齐情况（只读）")
    parser.add_argument("--snapshot-dir", default=str(DEFAULT_SNAPSHOT_DIR), help="site-data 目录")
    parser.add_argument("--papers-dir", default=str(DEFAULT_PAPERS_DIR), help="本地 data/papers 目录")
    parser.add_argument("--zotero-db", default=None, help="zotero.sqlite 路径（可选，默认自动探测）")
    parser.add_argument("--todo-collection-key", default="RECF7KND", help="Zotero Todo collection key")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--strict", action="store_true", help="有差异时返回非 0")
    args = parser.parse_args()

    snapshot_dir = Path(args.snapshot_dir)
    papers_dir = Path(args.papers_dir)

    todo_path = snapshot_dir / "todo-cards.json"
    library_path = snapshot_dir / "library.json"
    manifest_path = snapshot_dir / "manifest.json"
    explore_current_path = snapshot_dir / "explore" / "current-library.json"

    todo_payload = _read_json(todo_path) if todo_path.exists() else {}
    library_payload = _read_json(library_path) if library_path.exists() else {}
    manifest_payload = _read_json(manifest_path) if manifest_path.exists() else {}
    explore_current_payload = _read_json(explore_current_path) if explore_current_path.exists() else {}

    summary: dict[str, Any] = {
        "todo_snapshot_collection_count": (todo_payload.get("collection") or {}).get("count"),
        "todo_snapshot_cards_len": len(todo_payload.get("cards") or []),
        "todo_snapshot_generated_at": todo_payload.get("generated_at"),
        "library_snapshot_cards_len": len(library_payload.get("papers") or []),
        "library_snapshot_generated_at": library_payload.get("generated_at"),
        "manifest_snapshot_papers_len": len(manifest_payload.get("papers") or []),
        "manifest_snapshot_generated_at": manifest_payload.get("generated_at"),
        "explore_snapshot_count": explore_current_payload.get("count"),
        "explore_snapshot_generated_at": (
            explore_current_payload.get("snapshot_generated_at") or explore_current_payload.get("generated_at")
        ),
        "local_papers_with_meta": _count_local_papers(papers_dir) if papers_dir.exists() else None,
        "local_papers_with_materials": (
            _count_local_papers_with_materials(papers_dir) if papers_dir.exists() else None
        ),
    }

    zotero_db = _resolve_zotero_db(args.zotero_db)
    if zotero_db is not None:
        summary["zotero_db"] = str(zotero_db)
        summary.update(_query_zotero_counts(zotero_db, args.todo_collection_key))
    else:
        summary["zotero_db"] = None
        summary["zotero_all_items"] = None
        summary["zotero_todo_items"] = None
        summary["zotero_todo_items_with_pdf_attachment"] = None

    diff_rows = [
        DiffRow(
            name="Todo 卡片数 vs Zotero Todo 总条目",
            left_name="todo_snapshot_cards_len",
            left=summary.get("todo_snapshot_cards_len"),
            right_name="zotero_todo_items",
            right=summary.get("zotero_todo_items"),
        ),
        DiffRow(
            name="Todo collection.count vs cards.length",
            left_name="todo_snapshot_collection_count",
            left=summary.get("todo_snapshot_collection_count"),
            right_name="todo_snapshot_cards_len",
            right=summary.get("todo_snapshot_cards_len"),
        ),
        DiffRow(
            name="Library 卡片快照数 vs 本地有阅读材料论文",
            left_name="library_snapshot_cards_len",
            left=summary.get("library_snapshot_cards_len"),
            right_name="local_papers_with_materials",
            right=summary.get("local_papers_with_materials"),
        ),
        DiffRow(
            name="Manifest 全量论文数 vs 本地 data/papers",
            left_name="manifest_snapshot_papers_len",
            left=summary.get("manifest_snapshot_papers_len"),
            right_name="local_papers_with_meta",
            right=summary.get("local_papers_with_meta"),
        ),
        DiffRow(
            name="Explore current-library count vs 本地 data/papers",
            left_name="explore_snapshot_count",
            left=summary.get("explore_snapshot_count"),
            right_name="local_papers_with_meta",
            right=summary.get("local_papers_with_meta"),
        ),
        DiffRow(
            name="本地 data/papers vs Zotero 全库条目",
            left_name="local_papers_with_meta",
            left=summary.get("local_papers_with_meta"),
            right_name="zotero_all_items",
            right=summary.get("zotero_all_items"),
        ),
    ]

    summary["checks"] = [
        {
            "name": row.name,
            "left_name": row.left_name,
            "left": row.left,
            "right_name": row.right_name,
            "right": row.right,
            "delta": row.delta,
            "ok": row.ok,
        }
        for row in diff_rows
    ]
    summary["all_ok"] = all(row.ok for row in diff_rows)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        _print_human_report(summary, diff_rows)

    if args.strict and not summary["all_ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

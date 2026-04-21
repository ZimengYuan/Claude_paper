#!/usr/bin/env python3
"""Create or update the global ScholarAIO learning memory."""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path


DEFAULT_MEMORY_PATH = Path.home() / "Documents/know/memory.md"
VALID_LEVELS = ("mastered", "familiar", "basic", "unknown")

HEADER = """# ScholarAIO Learning Memory

This file is the global learning profile used by Todo Compass.

Supported entry format:

- Concept: mastered
- Concept: familiar
- Concept: basic
- Concept: unknown

Only `mastered` and `familiar` are used to skip or compress prerequisites.
Avoid adding topics you have not actually learned yet.

## Learned Concepts
"""


def _normalize_topic(topic: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(topic or "").lower())


def _entry_pattern() -> re.Pattern[str]:
    return re.compile(r"^([-*]\s+)(.+?)(\s*[:：]\s*)(mastered|familiar|basic|unknown)(?:\s+#.*)?\s*$", re.IGNORECASE)


def upsert_memory_entry(memory_path: Path, topic: str, level: str, note: str = "") -> bool:
    if level not in VALID_LEVELS:
        raise ValueError(f"Invalid level: {level}")
    memory_path = memory_path.expanduser()
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    if memory_path.exists():
        text = memory_path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            text = HEADER
    else:
        text = HEADER

    target = _normalize_topic(topic)
    lines = [
        line
        for line in text.splitlines()
        if not line.strip().startswith("<!-- updated:")
    ]
    pattern = _entry_pattern()
    replacement = f"- {topic}: {level}"
    if note.strip():
        replacement += f"  # {note.strip()}"

    for index, line in enumerate(lines):
        match = pattern.match(line.strip())
        if not match:
            continue
        if _normalize_topic(match.group(2)) == target:
            if lines[index] == replacement:
                return False
            lines[index] = replacement
            break
    else:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(replacement)

    lines.append(f"<!-- updated: {datetime.now().isoformat(timespec='seconds')} -->")
    memory_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return True


def ensure_memory_file(memory_path: Path) -> bool:
    memory_path = memory_path.expanduser()
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    if memory_path.exists() and memory_path.read_text(encoding="utf-8", errors="replace").strip():
        return False
    memory_path.write_text(HEADER.rstrip() + "\n", encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Update the global ScholarAIO learning memory.")
    parser.add_argument("--memory-path", default=str(DEFAULT_MEMORY_PATH), help="Path to memory.md")
    parser.add_argument("--init", action="store_true", help="Create the memory file if it does not exist")
    parser.add_argument("--topic", default="", help="Concept or skill to record")
    parser.add_argument("--level", choices=VALID_LEVELS, default="familiar", help="Knowledge level")
    parser.add_argument("--note", default="", help="Optional short note")
    args = parser.parse_args()

    memory_path = Path(args.memory_path).expanduser()
    if args.init and not args.topic:
        changed = ensure_memory_file(memory_path)
    elif args.topic:
        changed = upsert_memory_entry(memory_path, args.topic.strip(), args.level, args.note)
    else:
        parser.error("Use --init or provide --topic")

    action = "updated" if changed else "unchanged"
    print(f"{action}: {memory_path}")


if __name__ == "__main__":
    main()

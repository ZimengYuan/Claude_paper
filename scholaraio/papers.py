"""
papers.py — 论文目录结构的唯一真相源
======================================

所有模块通过此模块访问论文路径，不自行拼路径。

目录结构：
    data/papers/<dir_name>/
    ├── meta.json    # 含 "id": "<uuid>" 字段
    └── paper.md
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterator
from pathlib import Path


def paper_dir(papers_dir: Path, dir_name: str) -> Path:
    """Return the directory path for a paper."""
    return papers_dir / dir_name


def meta_path(papers_dir: Path, dir_name: str) -> Path:
    """Return the meta.json path for a paper."""
    return papers_dir / dir_name / "meta.json"


def md_path(papers_dir: Path, dir_name: str) -> Path:
    """Return the paper.md path for a paper."""
    return papers_dir / dir_name / "paper.md"


def iter_paper_dirs(papers_dir: Path) -> Iterator[Path]:
    """Yield sorted subdirectories containing meta.json.

    Args:
        papers_dir: Root papers directory.

    Yields:
        Path to each paper subdirectory that contains a ``meta.json``.
    """
    if not papers_dir.exists():
        return
    for d in sorted(papers_dir.iterdir()):
        if d.is_dir() and (d / "meta.json").exists():
            yield d


def generate_uuid() -> str:
    """Generate a new UUID string for a paper."""
    return str(uuid.uuid4())


def best_citation(meta: dict) -> int:
    """从 ``citation_count`` 字典中取最大值。

    Args:
        meta: 论文元数据字典。

    Returns:
        最大引用数，无数据时返回 0。
    """
    cc = meta.get("citation_count")
    if not cc or not isinstance(cc, dict):
        return 0
    vals = [v for v in cc.values() if isinstance(v, (int, float))]
    return int(max(vals)) if vals else 0


def parse_year_range(year: str) -> tuple[int | None, int | None]:
    """解析年份过滤表达式，返回 ``(start, end)``。

    支持格式: ``"2023"`` (单年), ``"2020-2024"`` (范围),
    ``"2020-"`` (起始年至今), ``"-2024"`` (截至某年)。

    Args:
        year: 年份过滤表达式。

    Returns:
        ``(start, end)`` 二元组，缺失端为 ``None``。
        单年返回 ``(2023, 2023)``。
    """
    year = year.strip()
    if "-" in year:
        parts = year.split("-", 1)
        start, end = parts[0].strip(), parts[1].strip()
        try:
            return (int(start) if start else None, int(end) if end else None)
        except ValueError as e:
            raise ValueError(f"无法解析年份范围: {year!r}（格式: 2020, 2020-2024, 2020-, -2024）") from e
    try:
        y = int(year)
    except ValueError as e:
        raise ValueError(f"无法解析年份: {year!r}（格式: 2020, 2020-2024, 2020-, -2024）") from e
    return (y, y)


def read_meta(paper_d: Path) -> dict:
    """Read and parse meta.json from a paper directory.

    Args:
        paper_d: Paper directory path.

    Returns:
        Parsed JSON dict.

    Raises:
        ValueError: If the JSON file is malformed (wraps ``json.JSONDecodeError``
            with the file path for context).
        FileNotFoundError: If meta.json does not exist.
    """
    p = paper_d / "meta.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {p}: {e}") from e


def write_meta(paper_d: Path, data: dict) -> None:
    """Atomically write meta.json to a paper directory.

    Writes to a temporary file first, then renames to avoid corruption
    if the process is interrupted mid-write.

    Args:
        paper_d: Paper directory path.
        data: Metadata dict to serialize.
    """
    p = paper_d / "meta.json"
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(p)


def update_meta(paper_d: Path, **fields) -> dict:
    """Read meta.json, merge fields, and atomically write back.

    Args:
        paper_d: Paper directory path.
        **fields: Key-value pairs to merge into the metadata dict.

    Returns:
        The updated metadata dict.
    """
    data = read_meta(paper_d)
    data.update(fields)
    write_meta(paper_d, data)
    return data


# ============================================================================
#  Tags and Read Status
# ============================================================================


def get_tags(paper_d: Path) -> list[str]:
    """Get tags for a paper.

    Args:
        paper_d: Paper directory path.

    Returns:
        List of tags, empty list if none.
    """
    meta = read_meta(paper_d)
    return meta.get("tags", []) or []


def set_tags(paper_d: Path, tags: list[str]) -> list[str]:
    """Set tags for a paper.

    Args:
        paper_d: Paper directory path.
        tags: List of tags to set.

    Returns:
        The updated list of tags.
    """
    return update_meta(paper_d, tags=tags).get("tags", []) or []


def add_tag(paper_d: Path, tag: str) -> list[str]:
    """Add a tag to a paper.

    Args:
        paper_d: Paper directory path.
        tag: Tag to add.

    Returns:
        Updated list of tags.
    """
    tags = get_tags(paper_d)
    if tag not in tags:
        tags.append(tag)
        set_tags(paper_d, tags)
    return tags


def remove_tag(paper_d: Path, tag: str) -> list[str]:
    """Remove a tag from a paper.

    Args:
        paper_d: Paper directory path.
        tag: Tag to remove.

    Returns:
        Updated list of tags.
    """
    tags = get_tags(paper_d)
    if tag in tags:
        tags.remove(tag)
        set_tags(paper_d, tags)
    return tags


def get_read_status(paper_d: Path) -> str:
    """Get read status for a paper.

    Args:
        paper_d: Paper directory path.

    Returns:
        Read status: "unread", "reading", "read", or "skipped".
    """
    meta = read_meta(paper_d)
    return meta.get("read_status", "unread")


def set_read_status(paper_d: Path, status: str) -> str:
    """Set read status for a paper.

    Args:
        paper_d: Paper directory path.
        status: Read status: "unread", "reading", "read", or "skipped".

    Returns:
        The updated read status.
    """
    valid_statuses = {"unread", "reading", "read", "skipped"}
    if status not in valid_statuses:
        raise ValueError(f"Invalid read status: {status}. Must be one of: {valid_statuses}")

    import datetime
    return update_meta(paper_d, read_status=status, read_at=datetime.datetime.now().isoformat()).get("read_status", status)


# ============================================================================
#  Learning Materials
# ============================================================================


def summary_path(paper_d: Path) -> Path:
    """Return the summary.md path for a paper."""
    return paper_d / "summary.md"


def method_path(paper_d: Path) -> Path:
    """Return the method.md path for a paper."""
    return paper_d / "method.md"


def sensemaking_path(paper_d: Path) -> Path:
    """Return the sensemaking.json path for a paper."""
    return paper_d / "sensemaking.json"


def reflection_path(paper_d: Path) -> Path:
    """Return the reflection.md path for a paper."""
    return paper_d / "reflection.md"


def user_notes_path(paper_d: Path) -> Path:
    """Return the user.md path for a paper."""
    return paper_d / "user.md"


def score_report_path(paper_d: Path) -> Path:
    """Return the score.md path for a paper."""
    return paper_d / "score.md"


def readable_report_path(paper_d: Path) -> Path:
    """Return the report.md path for a paper."""
    return paper_d / "report.md"


def read_summary(paper_d: Path) -> str | None:
    """Read summary.md from a paper directory.

    Args:
        paper_d: Paper directory path.

    Returns:
        Content of summary.md, or None if not exists.
    """
    p = summary_path(paper_d)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


def write_summary(paper_d: Path, content: str) -> None:
    """Write summary.md to a paper directory.

    Args:
        paper_d: Paper directory path.
        content: Summary content to write.
    """
    # Strip title line if it starts with # Summary: or similar
    lines = content.split('\n')
    # Remove first line if it's a title header with paper name
    if lines and lines[0].strip().startswith('# Summary:'):
        lines = lines[1:]
    # Also strip any subsequent lines that look like "Title: ..." or "Authors: ..."
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith('Title:') or line.strip().startswith('Authors:'):
            continue
        cleaned_lines.append(line)
    content = '\n'.join(cleaned_lines).strip()

    p = summary_path(paper_d)
    p.write_text(content, encoding="utf-8")


def read_method(paper_d: Path) -> str | None:
    """Read method.md from a paper directory.

    Args:
        paper_d: Paper directory path.

    Returns:
        Content of method.md, or None if not exists.
    """
    p = method_path(paper_d)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


def write_method(paper_d: Path, content: str) -> None:
    """Write method.md to a paper directory.

    Args:
        paper_d: Paper directory path.
        content: Method content to write.
    """
    # Strip title line if it starts with # Method or similar
    lines = content.split('\n')
    # Remove first line if it's a title header with paper name
    if lines and lines[0].strip().startswith('# Method'):
        lines = lines[1:]
    # Also strip any subsequent lines that look like "Title: ..." or "Authors: ..."
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith('Title:') or line.strip().startswith('Authors:'):
            continue
        cleaned_lines.append(line)
    content = '\n'.join(cleaned_lines).strip()

    p = method_path(paper_d)
    p.write_text(content, encoding="utf-8")


def read_score_report(paper_d: Path) -> str | None:
    """Read score.md from a paper directory.

    Args:
        paper_d: Paper directory path.

    Returns:
        Content of score.md, or None if not exists.
    """
    p = score_report_path(paper_d)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


def write_score_report(paper_d: Path, content: str) -> None:
    """Write score.md to a paper directory.

    Args:
        paper_d: Paper directory path.
        content: Score report content to write.
    """
    p = score_report_path(paper_d)
    p.write_text(content.strip() + "\n", encoding="utf-8")


def read_readable_report(paper_d: Path) -> str | None:
    """Read report.md from a paper directory.

    Args:
        paper_d: Paper directory path.

    Returns:
        Content of report.md, or None if not exists.
    """
    p = readable_report_path(paper_d)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


def write_readable_report(paper_d: Path, content: str) -> None:
    """Write report.md to a paper directory.

    Args:
        paper_d: Paper directory path.
        content: Readable report content to write.
    """
    p = readable_report_path(paper_d)
    p.write_text(content.strip() + "\n", encoding="utf-8")


def read_sensemaking(paper_d: Path) -> dict | None:
    """Read sensemaking.json from a paper directory.

    Args:
        paper_d: Paper directory path.

    Returns:
        Parsed JSON dict, or None if not exists.
    """
    p = sensemaking_path(paper_d)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def write_sensemaking(paper_d: Path, data: dict) -> None:
    """Write sensemaking.json to a paper directory.

    Args:
        paper_d: Paper directory path.
        data: Sensemaking data to write.
    """
    p = sensemaking_path(paper_d)
    p.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def read_reflection(paper_d: Path) -> str | None:
    """Read reflection.md from a paper directory.

    Args:
        paper_d: Paper directory path.

    Returns:
        Content of reflection.md, or None if not exists.
    """
    p = reflection_path(paper_d)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


def write_reflection(paper_d: Path, content: str) -> None:
    """Write reflection.md to a paper directory.

    Args:
        paper_d: Paper directory path.
        content: Reflection content to write.
    """
    p = reflection_path(paper_d)
    p.write_text(content, encoding="utf-8")


def read_user_notes(paper_d: Path) -> str | None:
    """Read user.md from a paper directory.

    Args:
        paper_d: Paper directory path.

    Returns:
        Content of user.md, or None if not exists.
    """
    p = user_notes_path(paper_d)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


def write_user_notes(paper_d: Path, content: str) -> None:
    """Write user.md to a paper directory.

    Args:
        paper_d: Paper directory path.
        content: User notes content to write.
    """
    p = user_notes_path(paper_d)
    p.write_text(content, encoding="utf-8")


# ============================================================================
#  AlphaXiv Summary
# ============================================================================


def get_alphaxiv_summary(paper_d: Path) -> str | None:
    """Get AlphaXiv summary from meta.json.

    Args:
        paper_d: Paper directory path.

    Returns:
        AlphaXiv summary, or None if not exists.
    """
    meta = read_meta(paper_d)
    return meta.get("alphaxiv_summary")


def set_alphaxiv_summary(paper_d: Path, summary: str) -> str:
    """Set AlphaXiv summary in meta.json.

    Args:
        paper_d: Paper directory path.
        summary: AlphaXiv summary to set.

    Returns:
        The updated summary.
    """
    import datetime
    return update_meta(paper_d, alphaxiv_summary=summary, generated_at=datetime.datetime.now().isoformat()).get("alphaxiv_summary", summary)

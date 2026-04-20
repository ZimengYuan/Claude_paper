"""Shared metadata normalization and validation helpers."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Any

_PLACEHOLDER_TITLES = {"", "none", "null", "untitled", "unknown"}
_PLACEHOLDER_YEAR_STRINGS = {"", "none", "null", "xxxx", "n/a", "na", "?"}
_SECTION_TITLES = {
    "abstract",
    "introduction",
    "background",
    "related work",
    "method",
    "methods",
    "approach",
    "results",
    "discussion",
    "conclusion",
    "conclusions",
    "references",
    "appendix",
    "supplementary",
    "acknowledgments",
    "acknowledgements",
}
_SECTION_HEADING_RE = re.compile(
    r"^\d+(?:\.\d+)*\s*[-:.)]?\s*"
    r"(abstract|introduction|background|related\s+work|method(?:s)?|approach|results?|discussion|"
    r"conclusions?|references?|appendix|supplement(?:ary)?|acknowledg(?:e)?ments?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MetadataIssue:
    """A normalized metadata quality finding."""

    rule: str
    severity: str
    message: str
    blocks_ingest: bool = False


def normalize_title_key(title: str) -> str:
    """Return a filesystem/search friendly title key for duplicate checks."""
    text = _strip_diacritics(title or "").lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text)
    return " ".join(text.split())


def normalize_year_value(year: Any) -> int | None:
    """Coerce a year-like value to ``int`` when possible."""
    if year is None:
        return None
    if isinstance(year, int):
        return year
    text = str(year).strip()
    if not text or text.lower() in _PLACEHOLDER_YEAR_STRINGS:
        return None
    if re.fullmatch(r"\d{4}", text):
        return int(text)
    return None


def normalize_meta_for_ingest(meta: Any) -> Any:
    """Best-effort cleanup before filename generation and validation."""
    from scholaraio.ingest.metadata import _extract_lastname

    title = str(_meta_get(meta, "title") or "").strip()
    if title:
        _meta_set(meta, "title", re.sub(r"\s+", " ", title))

    doi = str(_meta_get(meta, "doi") or "").strip()
    if doi.lower() in {"null", "none", "n/a"}:
        doi = ""
    _meta_set(meta, "doi", doi)

    year = normalize_year_value(_meta_get(meta, "year"))
    if year is not None:
        _meta_set(meta, "year", year)

    authors = _meta_get(meta, "authors")
    if isinstance(authors, list):
        cleaned_authors = [str(a).replace("\x00", "").strip() for a in authors if str(a).replace("\x00", "").strip()]
        _meta_set(meta, "authors", cleaned_authors)
        if cleaned_authors and not str(_meta_get(meta, "first_author") or "").strip():
            _meta_set(meta, "first_author", cleaned_authors[0])

    first_author = str(_meta_get(meta, "first_author") or "").strip()
    if first_author and not str(_meta_get(meta, "first_author_lastname") or "").strip():
        _meta_set(meta, "first_author_lastname", _extract_lastname(first_author))
    return meta


def collect_metadata_issues(meta: Any, *, current_year: int | None = None) -> list[MetadataIssue]:
    """Return reusable metadata quality findings for ingest and audits."""
    issues: list[MetadataIssue] = []
    title = str(_meta_get(meta, "title") or "").strip()
    title_key = normalize_title_key(title)

    if not title:
        issues.append(MetadataIssue("invalid_title", "error", "标题为空", blocks_ingest=True))
    elif title_key in _PLACEHOLDER_TITLES:
        issues.append(MetadataIssue("invalid_title", "error", f"标题异常: {title}", blocks_ingest=True))
    elif title_key in _SECTION_TITLES or _SECTION_HEADING_RE.match(title):
        issues.append(MetadataIssue("section_heading_title", "error", f"标题疑似章节标题: {title}", blocks_ingest=True))

    year_value = _meta_get(meta, "year")
    if year_value in (None, ""):
        issues.append(MetadataIssue("missing_year", "warning", "缺少年份"))
    else:
        normalized_year = normalize_year_value(year_value)
        if normalized_year is None:
            issues.append(MetadataIssue("invalid_year", "error", f"年份异常: {year_value}", blocks_ingest=True))
        else:
            max_year = current_year or date.today().year
            if normalized_year < 1900 or normalized_year > max_year + 1:
                issues.append(MetadataIssue("invalid_year", "error", f"年份超出合理范围: {normalized_year}", blocks_ingest=True))

    authors = _meta_get(meta, "authors")
    first_author = str(_meta_get(meta, "first_author") or "").strip()
    first_author_lastname = str(_meta_get(meta, "first_author_lastname") or "").strip()
    has_authors = isinstance(authors, list) and any(str(a).strip() for a in authors)
    if not has_authors and not first_author and not first_author_lastname:
        issues.append(
            MetadataIssue("missing_author_identity", "warning", "缺少可用于命名/识别的作者信息", blocks_ingest=True)
        )

    return issues


def _meta_get(meta: Any, key: str) -> Any:
    if isinstance(meta, dict):
        return meta.get(key)
    return getattr(meta, key, None)


def _meta_set(meta: Any, key: str, value: Any) -> None:
    if isinstance(meta, dict):
        meta[key] = value
    else:
        setattr(meta, key, value)


def _strip_diacritics(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(char for char in nfkd if not unicodedata.combining(char))

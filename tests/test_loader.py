"""Contract tests for the L1-L2 layer loading system.

Verifies: each layer returns the documented fields from well-formed data.
Does NOT test: internal JSON parsing details, LLM enrichment paths, or L3/L4
layers that require LLM enrichment or full-text paper files.
"""

from __future__ import annotations

import json
from typing import cast

from scholaraio.config import Config
from scholaraio.loader import L3_SKIP_TYPES, append_notes, enrich_l3, load_l1, load_l2, load_notes

# enrich_l3 requires a Config argument but the skip-by-type branch
# returns before it is used.  We use a typed sentinel so mypy is happy.
_UNUSED_CONFIG = cast(Config, None)


class TestLoadL1:
    """L1 contract: returns metadata dict with documented keys."""

    def test_returns_expected_keys(self, tmp_papers):
        json_path = tmp_papers / "Smith-2023-Turbulence" / "meta.json"
        result = load_l1(json_path)

        assert result["paper_id"] == "aaaa-1111"
        assert result["title"] == "Turbulence modeling in boundary layers"
        assert isinstance(result["authors"], list)
        assert result["year"] == 2023
        assert result["journal"] == "Journal of Fluid Mechanics"
        assert result["doi"] == "10.1234/jfm.2023.001"

    def test_missing_fields_have_safe_defaults(self, tmp_path):
        """Minimal JSON should not crash — missing fields get defaults."""
        d = tmp_path / "Bare-2000-Minimal"
        d.mkdir(parents=True)
        (d / "meta.json").write_text(json.dumps({"id": "min-id"}))

        result = load_l1(d / "meta.json")
        assert result["paper_id"] == "min-id"
        assert result["title"] == ""
        assert result["authors"] == []
        assert result["year"] is None


class TestLoadL2:
    """L2 contract: returns abstract string."""

    def test_returns_abstract(self, tmp_papers):
        json_path = tmp_papers / "Smith-2023-Turbulence" / "meta.json"
        assert "novel turbulence model" in load_l2(json_path)

    def test_missing_abstract_returns_placeholder(self, tmp_path):
        d = tmp_path / "NoAbstract"
        d.mkdir()
        (d / "meta.json").write_text(json.dumps({"id": "x"}))

        result = load_l2(d / "meta.json")
        assert "No abstract" in result


class TestEnrichL3Skip:
    """enrich_l3 skips non-article paper types and writes a marker."""

    def test_skips_thesis(self, tmp_papers):
        """Thesis paper_type should be skipped without any LLM call."""
        json_path = tmp_papers / "Wang-2024-DeepLearning" / "meta.json"
        md_path = json_path.parent / "paper.md"

        # config=_UNUSED_CONFIG is fine because the skip happens before config is used
        result = enrich_l3(json_path, md_path, config=_UNUSED_CONFIG)

        assert result is True
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["l3_extraction_method"] == "skipped"
        assert "l3_extracted_at" in data
        assert "l3_conclusion" not in data

    def test_skips_book(self, tmp_path):
        """Book paper_type should be skipped."""
        d = tmp_path / "Author-2020-Handbook"
        d.mkdir(parents=True)
        (d / "meta.json").write_text(
            json.dumps({"id": "book-1", "paper_type": "book"}),
            encoding="utf-8",
        )
        (d / "paper.md").write_text("# Handbook\n\nContent.", encoding="utf-8")

        result = enrich_l3(d / "meta.json", d / "paper.md", config=_UNUSED_CONFIG)

        assert result is True
        data = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        assert data["l3_extraction_method"] == "skipped"

    def test_skip_types_coverage(self):
        """All documented skip types are present in the set."""
        for t in ("thesis", "book", "monograph", "document", "dissertation"):
            assert t in L3_SKIP_TYPES


class TestLoadNotes:
    """load_notes contract: returns notes text or None."""

    def test_no_notes_file_returns_none(self, tmp_path):
        d = tmp_path / "SomePaper"
        d.mkdir()
        assert load_notes(d) is None

    def test_empty_notes_file_returns_none(self, tmp_path):
        d = tmp_path / "SomePaper"
        d.mkdir()
        (d / "notes.md").write_text("", encoding="utf-8")
        assert load_notes(d) is None

    def test_whitespace_only_returns_none(self, tmp_path):
        d = tmp_path / "SomePaper"
        d.mkdir()
        (d / "notes.md").write_text("  \n\n  ", encoding="utf-8")
        assert load_notes(d) is None

    def test_returns_content(self, tmp_path):
        d = tmp_path / "SomePaper"
        d.mkdir()
        content = "## 2026-03-14 | ws-test | literature-review\n\nKey finding."
        (d / "notes.md").write_text(content, encoding="utf-8")
        assert load_notes(d) == content


class TestAppendNotes:
    """append_notes contract: creates or appends to notes.md."""

    def test_creates_notes_if_absent(self, tmp_path):
        d = tmp_path / "SomePaper"
        d.mkdir()
        append_notes(d, "## 2026-03-14 | ws | skill\n\nFirst note.")
        notes = load_notes(d)
        assert notes is not None
        assert "First note." in notes

    def test_appends_with_separator(self, tmp_path):
        d = tmp_path / "SomePaper"
        d.mkdir()
        append_notes(d, "## Section 1\n\nFirst.")
        append_notes(d, "## Section 2\n\nSecond.")
        content = (d / "notes.md").read_text(encoding="utf-8")
        assert "## Section 1" in content
        assert "## Section 2" in content
        # Two sections separated by blank line
        assert "\n\n## Section 2" in content

    def test_trailing_newlines_stripped(self, tmp_path):
        d = tmp_path / "SomePaper"
        d.mkdir()
        append_notes(d, "Note with trailing newlines\n\n\n")
        content = (d / "notes.md").read_text(encoding="utf-8")
        # Should end with exactly one newline
        assert content.endswith("newlines\n")
        assert not content.endswith("newlines\n\n")

"""Contract tests for the audit module.

Verifies: audit detects known data quality issues and returns structured reports.
Does NOT test: specific rule implementations or diagnostic messages.
"""

from __future__ import annotations

import json

from scholaraio.audit import Issue, audit_papers


class TestAuditDetection:
    """Audit contract: reports issues as structured Issue objects."""

    def test_clean_papers_produce_no_errors(self, tmp_papers):
        issues = audit_papers(tmp_papers)
        errors = [i for i in issues if i.severity == "error"]
        # Well-formed test data should have no errors
        assert len(errors) == 0

    def test_missing_doi_reported_for_non_thesis(self, tmp_papers):
        """Paper B is thesis (no DOI ok), but a journal-article without DOI should warn."""
        # Create a journal article without DOI
        d = tmp_papers / "NoDoi-2023-Test"
        d.mkdir()
        (d / "meta.json").write_text(
            json.dumps(
                {
                    "id": "cccc-3333",
                    "title": "Test Paper",
                    "authors": ["Author"],
                    "year": 2023,
                    "doi": "",
                    "paper_type": "journal-article",
                }
            ),
        )
        (d / "paper.md").write_text("# Test Paper\n\nSome content here for testing.")

        issues = audit_papers(tmp_papers)
        doi_issues = [i for i in issues if "doi" in i.rule.lower() or "doi" in i.message.lower()]
        assert len(doi_issues) >= 1

    def test_issue_has_required_fields(self, tmp_papers):
        # Create a problematic paper to guarantee at least one issue
        d = tmp_papers / "Bad-0000-Empty"
        d.mkdir()
        (d / "meta.json").write_text(json.dumps({"id": "bad"}))
        (d / "paper.md").write_text("")

        issues = audit_papers(tmp_papers)
        assert len(issues) > 0
        for issue in issues:
            assert isinstance(issue, Issue)
            assert issue.paper_id
            assert issue.severity in ("error", "warning", "info")
            assert issue.rule
            assert issue.message

    def test_audit_reports_duplicate_titles_and_invalid_year(self, tmp_papers):
        bad = tmp_papers / "Bad-XXXX-Intro"
        bad.mkdir()
        (bad / "meta.json").write_text(
            json.dumps(
                {
                    "id": "dddd-4444",
                    "title": "1Introduction",
                    "authors": ["Broken Parser"],
                    "first_author_lastname": "Broken",
                    "year": "XXXX",
                    "doi": "",
                    "paper_type": "journal-article",
                }
            ),
            encoding="utf-8",
        )
        (bad / "paper.md").write_text("# 1Introduction\n\nSome content", encoding="utf-8")

        dup = tmp_papers / "Jones-2025-Turbulence"
        dup.mkdir()
        (dup / "meta.json").write_text(
            json.dumps(
                {
                    "id": "eeee-5555",
                    "title": "Turbulence modeling in boundary layers",
                    "authors": ["Alice Jones"],
                    "first_author_lastname": "Jones",
                    "year": 2025,
                    "doi": "10.5555/jfm.2025.001",
                    "paper_type": "journal-article",
                }
            ),
            encoding="utf-8",
        )
        (dup / "paper.md").write_text("# Turbulence modeling in boundary layers\n\nMore content", encoding="utf-8")

        issues = audit_papers(tmp_papers)
        rules = {(issue.paper_id, issue.rule) for issue in issues}

        assert ("Bad-XXXX-Intro", "invalid_year") in rules
        assert ("Bad-XXXX-Intro", "section_heading_title") in rules
        assert ("Smith-2023-Turbulence", "duplicate_title") in rules
        assert ("Jones-2025-Turbulence", "duplicate_title") in rules

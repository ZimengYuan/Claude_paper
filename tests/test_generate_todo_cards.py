from __future__ import annotations

from scholaraio.config import Config, LLMConfig
from scripts.generate_todo_cards import (
    DUAL_PROFESSOR_PROTOCOL,
    DUAL_PROFESSOR_ROLES,
    MatchedTodoPaper,
    _build_existing_card_index,
    _build_fallback_from_metadata,
    _build_unmatched_route_id,
    _card_needs_quality_refresh,
    _find_existing_card,
    _merge_card_metadata,
    _resolve_llm_config,
)


def _sample_item(**overrides) -> MatchedTodoPaper:
    payload = {
        "collection_index": 0,
        "zotero_title": "OmniControl: Control Any Joint at Any Time for Human Motion Generation",
        "zotero_doi": "10.48550/arXiv.2310.08580",
        "route_id": "todo-unmatched-new",
        "paper_route_id": "",
        "dir_name": "",
        "paper_id": "",
        "title": "OmniControl: Control Any Joint at Any Time for Human Motion Generation",
        "authors": ["Alice Example", "Bob Example"],
        "year": 2023,
        "journal": "arXiv",
        "doi": "10.48550/arXiv.2310.08580",
        "read_status": "unread",
        "abstract": (
            "This paper presents a controllable human motion generation method. "
            "It supports per-joint control with a unified representation. "
            "Experiments validate flexible control under diverse prompts."
        ),
    }
    payload.update(overrides)
    return MatchedTodoPaper(**payload)


def test_unmatched_route_id_stable_for_same_identity() -> None:
    route_a = _build_unmatched_route_id(
        "OmniControl: Control Any Joint at Any Time for Human Motion Generation",
        doi="10.48550/arXiv.2310.08580",
        year=2023,
        authors=["Alice Example"],
    )
    route_b = _build_unmatched_route_id(
        "OmniControl: Control Any Joint at Any Time for Human Motion Generation",
        doi="10.48550/arXiv.2310.08580",
        year=2025,
        authors=["Another Author"],
    )

    assert route_a == route_b


def test_unmatched_route_id_uses_title_year_author_without_doi() -> None:
    route_a = _build_unmatched_route_id(
        "Dynamic Whole-Body Dancing with Humanoid Robots -- A Model-Based Control Approach",
        year=2024,
        authors=["Alice Example"],
    )
    route_b = _build_unmatched_route_id(
        "Dynamic Whole-Body Dancing with Humanoid Robots -- A Model-Based Control Approach",
        year=2025,
        authors=["Alice Example"],
    )

    assert route_a != route_b


def test_existing_card_lookup_reuses_card_when_route_changes() -> None:
    old_card = {
        "route_id": "todo-unmatched-old",
        "paper_route_id": "",
        "paper_id": "",
        "dir_name": "",
        "title": "OmniControl: Control Any Joint at Any Time for Human Motion Generation",
        "zotero_title": "OmniControl: Control Any Joint at Any Time for Human Motion Generation",
        "authors": ["Alice Example", "Bob Example"],
        "year": 2023,
        "journal": "arXiv",
        "doi": "10.48550/arXiv.2310.08580",
        "core_innovation": "old",
        "technical_contributions": [{"title": "a", "body": "b"}, {"title": "c", "body": "d"}],
        "methodological_breakthrough": {"novelty": "n", "key_technique": "k", "theory": "t"},
        "key_results": {"benchmarks": "b", "improvements": "i", "ablation": "a"},
        "limitations": {"current": "c", "future": "f", "transferability": "tr"},
        "one_line_summary": "summary",
    }
    index = _build_existing_card_index([old_card])

    item = _sample_item(route_id="todo-unmatched-stable")

    assert _find_existing_card(item, index) == old_card


def test_metadata_fallback_is_not_plain_abstract_echo() -> None:
    card = _build_fallback_from_metadata(_sample_item())

    assert card["core_innovation"].startswith("从公开摘要看")
    assert card["one_line_summary"].startswith("基于公开摘要")
    assert card["core_innovation"] != card["one_line_summary"]
    assert "摘要" in card["key_results"]["improvements"]


def test_merge_card_metadata_preserves_existing_card_read_status() -> None:
    existing_card = {
        "read_status": "unread",
        "generation_protocol": DUAL_PROFESSOR_PROTOCOL,
        "reviewer_count": 2,
        "reviewer_roles": list(DUAL_PROFESSOR_ROLES),
        "core_innovation": "old",
        "technical_contributions": [{"title": "a", "body": "b"}, {"title": "c", "body": "d"}],
        "methodological_breakthrough": {"novelty": "n", "key_technique": "k", "theory": "t"},
        "key_results": {"benchmarks": "b", "improvements": "i", "ablation": "a"},
        "limitations": {"current": "c", "future": "f", "transferability": "tr"},
        "one_line_summary": "summary",
    }

    merged = _merge_card_metadata(existing_card, _sample_item(read_status="read"), model="gpt-5.4-mini")

    assert merged["read_status"] == "unread"
    assert merged["generation_protocol"] == DUAL_PROFESSOR_PROTOCOL
    assert merged["reviewer_count"] == 2


def test_merge_card_metadata_uses_item_read_status_for_new_card() -> None:
    merged = _merge_card_metadata(
        {
            "generation_protocol": DUAL_PROFESSOR_PROTOCOL,
            "reviewer_count": 2,
            "reviewer_roles": list(DUAL_PROFESSOR_ROLES),
            "core_innovation": "old",
            "technical_contributions": [{"title": "a", "body": "b"}, {"title": "c", "body": "d"}],
            "methodological_breakthrough": {"novelty": "n", "key_technique": "k", "theory": "t"},
            "key_results": {"benchmarks": "b", "improvements": "i", "ablation": "a"},
            "limitations": {"current": "c", "future": "f", "transferability": "tr"},
            "one_line_summary": "summary",
        },
        _sample_item(read_status="read"),
        model="gpt-5.4-mini",
    )

    assert merged["read_status"] == "read"


def test_card_needs_quality_refresh_for_placeholder_results() -> None:
    card = {
        "generation_protocol": DUAL_PROFESSOR_PROTOCOL,
        "reviewer_count": 2,
        "core_innovation": "placeholder",
        "technical_contributions": [{"title": "a", "body": "b"}, {"title": "c", "body": "d"}],
        "methodological_breakthrough": {"novelty": "n", "key_technique": "k", "theory": "t"},
        "key_results": {
            "benchmarks": "详见论文实验章节。",
            "improvements": "详见论文指标对比表。",
            "ablation": "详见论文消融实验。",
        },
        "limitations": {"current": "c", "future": "f", "transferability": "tr"},
        "one_line_summary": "summary",
    }

    assert _card_needs_quality_refresh(card) is True


def test_card_needs_quality_refresh_for_legacy_single_agent_protocol() -> None:
    card = {
        "generation_mode": "llm",
        "core_innovation": "old",
        "technical_contributions": [{"title": "a", "body": "b"}, {"title": "c", "body": "d"}],
        "methodological_breakthrough": {"novelty": "n", "key_technique": "k", "theory": "t"},
        "key_results": {"benchmarks": "b", "improvements": "i", "ablation": "a"},
        "limitations": {"current": "c", "future": "f", "transferability": "tr"},
        "one_line_summary": "summary",
    }

    assert _card_needs_quality_refresh(card) is True


def test_resolve_llm_config_routes_gpt_models_to_codex_backend() -> None:
    cfg = Config(llm=LLMConfig(backend="gemini-mcp", model="gemini-3-flash-preview"))

    llm_cfg, api_key = _resolve_llm_config(cfg, "gpt-5.4-mini")

    assert llm_cfg.backend == "codex-mcp"
    assert llm_cfg.model == "gpt-5.4-mini"
    assert api_key == ""

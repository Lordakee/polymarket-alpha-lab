from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_packet_primary_source_confidence_ladder_v2"


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def ladder_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "packet_id": "packet-primary-source-confidence-ladder-v2",
        "official_source_count": d("1"),
        "primary_source_count": d("2"),
        "secondary_source_count": d("1"),
        "market_derived_source_count": d("1"),
        "social_source_count": d("1"),
        "fresh_source_count": d("4"),
        "stale_source_count": d("2"),
        "independent_source_count": d("4"),
        "contradicting_source_count": d("1"),
        "resolution_relevant_source_count": d("3"),
        "source_count": d("6"),
        "freshness_target_seconds": d("3600"),
        "maximum_source_age_seconds": d("5400"),
        "minimum_actionable_score": d("300.000000"),
        "reason_codes": ("research_packet_present",),
    }
    values.update(overrides)
    return module.ResearchPacketPrimarySourceConfidenceLadderV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_research_packet_primary_source_confidence_ladder_v2(
        ladder_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_confidence_ladder_ranks_primary_sources_with_all_adjustments() -> None:
    result = score()

    assert result.raw_source_confidence_score_bps == d("470.000000")
    assert result.recency_adjustment_bps == d("-30.000000")
    assert result.independence_adjustment_bps == d("60.000000")
    assert result.contradiction_adjustment_bps == d("-60.000000")
    assert result.resolution_rule_relevance_adjustment_bps == d("60.000000")
    assert result.paper_score_bps == d("500.000000")
    assert result.top_source_tier == "official"
    assert result.ladder_rank_summary == (
        "official",
        "primary",
        "secondary",
        "market_derived",
        "social",
    )
    assert result.score_status == "candidate"
    assert result.score_decision == "paper_candidate"
    assert result.reason_codes == (
        "research_packet_present",
        "research_packet_primary_source_confidence_ladder_v2",
        "score_candidate",
        "official_source_top_ranked",
        "recency_penalty_applied",
        "independence_boost_applied",
        "contradiction_penalty_applied",
        "resolution_rule_relevance_boost_applied",
        "minimum_actionable_score_met",
    )
    assert type(result.paper_score_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64


def test_social_only_stale_contradicted_packet_is_blocked() -> None:
    result = score(
        ladder_input(
            official_source_count=d("0"),
            primary_source_count=d("0"),
            secondary_source_count=d("0"),
            market_derived_source_count=d("0"),
            social_source_count=d("3"),
            fresh_source_count=d("0"),
            stale_source_count=d("3"),
            independent_source_count=d("1"),
            contradicting_source_count=d("3"),
            resolution_relevant_source_count=d("0"),
            source_count=d("3"),
            maximum_source_age_seconds=d("10800"),
            freshness_target_seconds=d("3600"),
            minimum_actionable_score=d("50.000000"),
            reason_codes=(),
        ),
    )

    assert result.raw_source_confidence_score_bps == d("90.000000")
    assert result.recency_adjustment_bps == d("-100.000000")
    assert result.independence_adjustment_bps == d("10.000000")
    assert result.contradiction_adjustment_bps == d("-180.000000")
    assert result.resolution_rule_relevance_adjustment_bps == d("0.000000")
    assert result.paper_score_bps == d("-180.000000")
    assert result.top_source_tier == "social"
    assert result.score_status == "blocked"
    assert result.score_decision == "reject"
    assert "social_source_top_ranked" in result.reason_codes
    assert "score_below_zero" in result.reason_codes


def test_watch_when_relevant_secondary_sources_are_positive_but_below_threshold() -> None:
    result = score(
        ladder_input(
            official_source_count=d("0"),
            primary_source_count=d("0"),
            secondary_source_count=d("3"),
            market_derived_source_count=d("1"),
            social_source_count=d("0"),
            fresh_source_count=d("4"),
            stale_source_count=d("0"),
            independent_source_count=d("2"),
            contradicting_source_count=d("0"),
            resolution_relevant_source_count=d("2"),
            source_count=d("4"),
            maximum_source_age_seconds=d("1200"),
            freshness_target_seconds=d("3600"),
            minimum_actionable_score=d("400.000000"),
            reason_codes=(),
        ),
    )

    assert result.paper_score_bps == d("370.000000")
    assert result.top_source_tier == "secondary"
    assert result.score_status == "watch"
    assert result.score_decision == "manual_review"
    assert "score_positive_below_minimum" in result.reason_codes


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.research_packet_primary_source_confidence_ladder_v2_payload(
        result,
    )
    assert payload["paper_score_bps"] == "500.000000"
    assert payload["source_count"] == "6"
    assert payload["ladder_rank_summary"] == [
        "official",
        "primary",
        "secondary",
        "market_derived",
        "social",
    ]
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_primary_source_confidence_ladder_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = ladder_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.ResearchPacketPrimarySourceConfidenceLadderV2Input.__dataclass_params__.frozen
    assert module.ResearchPacketPrimarySourceConfidenceLadderV2Result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.packet_id = "other-packet"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.score_status = "candidate"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        ladder_input(source_count=6)
    with pytest.raises(ValueError, match="packet_id must be a canonical"):
        ladder_input(packet_id=" packet-primary-source-confidence-ladder-v2")
    with pytest.raises(ValueError, match="source counts must classify every source"):
        ladder_input(social_source_count=d("0"))
    with pytest.raises(ValueError, match="fresh and stale counts must classify every source"):
        ladder_input(stale_source_count=d("1"))
    with pytest.raises(ValueError, match="independent_source_count must not exceed source_count"):
        ladder_input(independent_source_count=d("7"))
    with pytest.raises(ValueError, match="freshness_target_seconds must be positive"):
        ladder_input(freshness_target_seconds=d("0"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        ladder_input(reason_codes=["research_packet_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        ladder_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.ResearchPacketPrimarySourceConfidenceLadderV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchPacketPrimarySourceConfidenceLadderV2Result(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            ladder_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_research_packet_primary_source_confidence_ladder_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_research_packet_primary_source_confidence_ladder_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/research_packet_primary_source_confidence_ladder_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "live",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "wallet",
        " auth",
        "order",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.__all__ == (
        "SCORE_STATUSES",
        "SCORE_DECISIONS",
        "SOURCE_TIERS",
        "ResearchPacketPrimarySourceConfidenceLadderV2Input",
        "ResearchPacketPrimarySourceConfidenceLadderV2Result",
        "estimate_research_packet_primary_source_confidence_ladder_v2",
        "research_packet_primary_source_confidence_ladder_v2_payload",
        "reject_research_packet_primary_source_confidence_ladder_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "research_packet_primary_source_confidence_ladder_v2" not in getattr(
        root,
        "__all__",
        (),
    )

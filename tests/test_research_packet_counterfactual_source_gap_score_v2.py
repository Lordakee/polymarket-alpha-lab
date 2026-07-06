from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_packet_counterfactual_source_gap_score_v2"


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "packet_id": "packet-counterfactual-source-gap-v2",
        "base_case_source_count": d("6"),
        "counterfactual_source_count": d("2"),
        "independent_source_count": d("4"),
        "conflicting_source_count": d("1"),
        "bear_case_evidence_count": d("0"),
        "minimum_bear_case_evidence_count": d("2"),
        "minimum_source_diversity_count": d("3"),
        "minimum_actionable_score": d("100.000000"),
        "reason_codes": ("research_packet_present",),
    }
    values.update(overrides)
    return module.ResearchPacketCounterfactualSourceGapScoreV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_research_packet_counterfactual_source_gap_score_v2(
        score_input() if subject is None else subject,
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


def test_counterfactual_source_gap_score_penalizes_missing_evidence() -> None:
    result = score()

    assert result.source_gap_count == d("4")
    assert result.counterfactual_source_coverage_ratio == d("0.333333")
    assert result.source_gap_penalty_bps == d("100.000000")
    assert result.missing_bear_case_evidence_count == d("2")
    assert result.missing_bear_case_evidence_penalty_bps == d("150.000000")
    assert result.source_diversity_boost_bps == d("55.000000")
    assert result.raw_counterfactual_source_score_bps == d("100.000000")
    assert result.paper_score_bps == d("-95.000000")
    assert result.score_status == "blocked"
    assert result.score_decision == "reject"
    assert result.reason_codes == (
        "research_packet_present",
        "research_packet_counterfactual_source_gap_score_v2",
        "score_blocked",
        "counterfactual_source_gap_detected",
        "missing_bear_case_evidence_penalty_applied",
        "source_diversity_boost_applied",
        "score_below_zero",
    )
    assert type(result.paper_score_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64


def test_source_diversity_boost_can_lift_complete_counterfactual_packet() -> None:
    result = score(
        score_input(
            base_case_source_count=d("4"),
            counterfactual_source_count=d("4"),
            independent_source_count=d("5"),
            conflicting_source_count=d("2"),
            bear_case_evidence_count=d("2"),
            minimum_actionable_score=d("200.000000"),
            reason_codes=(),
        ),
    )

    assert result.source_gap_count == d("0")
    assert result.counterfactual_source_coverage_ratio == d("1.000000")
    assert result.source_gap_penalty_bps == d("0.000000")
    assert result.missing_bear_case_evidence_count == d("0")
    assert result.missing_bear_case_evidence_penalty_bps == d("0.000000")
    assert result.source_diversity_boost_bps == d("80.000000")
    assert result.raw_counterfactual_source_score_bps == d("200.000000")
    assert result.paper_score_bps == d("280.000000")
    assert result.score_status == "candidate"
    assert result.score_decision == "paper_candidate"
    assert result.reason_codes == (
        "research_packet_counterfactual_source_gap_score_v2",
        "score_candidate",
        "source_diversity_boost_applied",
        "minimum_actionable_score_met",
    )


def test_watch_when_gap_adjusted_score_is_positive_but_below_threshold() -> None:
    result = score(
        score_input(
            base_case_source_count=d("3"),
            counterfactual_source_count=d("3"),
            independent_source_count=d("2"),
            conflicting_source_count=d("0"),
            bear_case_evidence_count=d("1"),
            minimum_bear_case_evidence_count=d("1"),
            minimum_source_diversity_count=d("3"),
            minimum_actionable_score=d("200.000000"),
            reason_codes=(),
        ),
    )

    assert result.paper_score_bps == d("150.000000")
    assert result.score_status == "watch"
    assert result.score_decision == "manual_review"
    assert "score_positive_below_minimum" in result.reason_codes


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.research_packet_counterfactual_source_gap_score_v2_payload(
        result,
    )
    assert payload["paper_score_bps"] == "-95.000000"
    assert payload["source_gap_count"] == "4"
    assert payload["counterfactual_source_coverage_ratio"] == "0.333333"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_counterfactual_source_gap_score_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.ResearchPacketCounterfactualSourceGapScoreV2Input.__dataclass_params__.frozen
    assert module.ResearchPacketCounterfactualSourceGapScoreV2Result.__dataclass_params__.frozen

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

    with pytest.raises(ValueError, match="base_case_source_count must be a Decimal"):
        score_input(base_case_source_count=6)
    with pytest.raises(ValueError, match="packet_id must be a canonical"):
        score_input(packet_id=" packet-counterfactual-source-gap-v2")
    with pytest.raises(ValueError, match="counterfactual_source_count must be integral"):
        score_input(counterfactual_source_count=d("2.500000"))
    with pytest.raises(ValueError, match="minimum_actionable_score must be nonnegative"):
        score_input(minimum_actionable_score=d("-1.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["research_packet_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.ResearchPacketCounterfactualSourceGapScoreV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchPacketCounterfactualSourceGapScoreV2Result(
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
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_research_packet_counterfactual_source_gap_score_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_research_packet_counterfactual_source_gap_score_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/research_packet_counterfactual_source_gap_score_v2.py",
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
        "ResearchPacketCounterfactualSourceGapScoreV2Input",
        "ResearchPacketCounterfactualSourceGapScoreV2Result",
        "estimate_research_packet_counterfactual_source_gap_score_v2",
        "research_packet_counterfactual_source_gap_score_v2_payload",
        "reject_research_packet_counterfactual_source_gap_score_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "research_packet_counterfactual_source_gap_score_v2" not in getattr(
        root,
        "__all__",
        (),
    )

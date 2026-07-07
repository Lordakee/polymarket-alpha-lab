from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_probability_edge_decomposition as api
from polymarket_alpha_lab.research_probability_edge_decomposition import (
    ResearchProbabilityEdgeDecompositionConfig,
    ResearchProbabilityEdgeDecompositionReasonCodeCount,
    ResearchProbabilityEdgeDecompositionReport,
    ResearchProbabilityEdgeDecompositionRow,
    ResearchProbabilityEdgeInput,
    build_research_probability_edge_decomposition_report,
    research_probability_edge_decomposition_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def event(
    event_reference: str = "event_ref_alpha",
    *,
    baseline_probability: Decimal = d("0.450000"),
    evidence_adjustment: Decimal = d("0.080000"),
    cost_friction: Decimal = d("0.010000"),
    conflict_discount: Decimal = d("0.000000"),
    evidence_item_count: Decimal = d("3.000000"),
    conflict_item_count: Decimal = d("0.000000"),
) -> ResearchProbabilityEdgeInput:
    return ResearchProbabilityEdgeInput(
        event_reference=event_reference,
        baseline_probability=baseline_probability,
        evidence_adjustment=evidence_adjustment,
        cost_friction=cost_friction,
        conflict_discount=conflict_discount,
        evidence_item_count=evidence_item_count,
        conflict_item_count=conflict_item_count,
    )


def report(
    *events: ResearchProbabilityEdgeInput,
    generated_at: datetime = GENERATED_AT,
    config: ResearchProbabilityEdgeDecompositionConfig | None = None,
) -> ResearchProbabilityEdgeDecompositionReport:
    return build_research_probability_edge_decomposition_report(
        events,
        generated_at=generated_at,
        config=config,
    )


def test_rows_decompose_probability_components_and_roll_up_statuses() -> None:
    result = report(
        event(
            "event_ref_gamma",
            baseline_probability=d("0.400000"),
            evidence_adjustment=d("0.100000"),
            cost_friction=d("0.020000"),
            conflict_discount=d("0.120000"),
            evidence_item_count=d("1.000000"),
            conflict_item_count=d("2.000000"),
        ),
        event(),
        event(
            "event_ref_beta",
            baseline_probability=d("0.600000"),
            evidence_adjustment=d("-0.030000"),
            cost_friction=d("0.015000"),
            conflict_discount=d("0.010000"),
            evidence_item_count=d("2.000000"),
            conflict_item_count=d("1.000000"),
        ),
    )

    assert tuple(row.event_reference for row in result.rows) == (
        "event_ref_alpha",
        "event_ref_beta",
        "event_ref_gamma",
    )

    passed, watched, blocked = result.rows
    assert passed.evidence_adjusted_probability == d("0.530000")
    assert passed.decomposed_probability == d("0.520000")
    assert passed.net_probability_delta == d("0.070000")
    assert passed.absolute_net_probability_delta == d("0.070000")
    assert passed.status == "pass"
    assert passed.reason_codes == (
        "evidence_adjustment_positive",
        "material_probability_difference",
        "cost_friction_present",
        "research_probability_edge_pass",
    )

    assert watched.evidence_adjusted_probability == d("0.570000")
    assert watched.decomposed_probability == d("0.545000")
    assert watched.net_probability_delta == d("-0.055000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "evidence_adjustment_negative",
        "material_probability_difference",
        "cost_friction_present",
        "high_cost_friction",
        "conflict_discount_present",
        "research_probability_edge_watch",
    )

    assert blocked.evidence_adjusted_probability == d("0.500000")
    assert blocked.decomposed_probability == d("0.360000")
    assert blocked.net_probability_delta == d("-0.040000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "evidence_adjustment_positive",
        "modest_probability_difference",
        "cost_friction_present",
        "high_cost_friction",
        "conflict_discount_present",
        "high_conflict_discount",
        "research_probability_edge_block",
    )

    assert result.report_status == "block"
    assert result.event_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.average_absolute_net_probability_delta == d("0.055000")
    assert result.max_cost_friction == d("0.020000")
    assert result.max_conflict_discount == d("0.120000")
    assert result.reason_code_counts == (
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "evidence_adjustment_positive",
            d("2.000000"),
        ),
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "evidence_adjustment_negative",
            d("1.000000"),
        ),
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "material_probability_difference",
            d("2.000000"),
        ),
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "modest_probability_difference",
            d("1.000000"),
        ),
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "cost_friction_present",
            d("3.000000"),
        ),
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "high_cost_friction",
            d("2.000000"),
        ),
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "conflict_discount_present",
            d("2.000000"),
        ),
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "high_conflict_discount",
            d("1.000000"),
        ),
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "research_probability_edge_pass",
            d("1.000000"),
        ),
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "research_probability_edge_watch",
            d("1.000000"),
        ),
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "research_probability_edge_block",
            d("1.000000"),
        ),
    )


def test_empty_input_returns_block_report_with_decimal_zeroes() -> None:
    result = report()

    assert result.report_status == "block"
    assert result.rows == ()
    assert result.event_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.average_absolute_net_probability_delta == d("0.000000")
    assert result.max_cost_friction == d("0.000000")
    assert result.max_conflict_discount == d("0.000000")
    assert result.reason_codes == (
        "no_probability_events",
        "research_probability_edge_block",
    )
    assert result.reason_code_counts == (
        ResearchProbabilityEdgeDecompositionReasonCodeCount(
            "no_probability_events",
            d("1.000000"),
        ),
    )


def test_public_payload_is_deterministic_json_with_decimal_strings() -> None:
    result = report(event())
    same_result = report(event())

    payload = research_probability_edge_decomposition_payload(result)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == result.payload
    assert result.derived_validation_digest == same_result.derived_validation_digest
    assert len(result.derived_validation_digest) == 64
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["event_count"] == "1.000000"
    assert payload["rows"][0]["baseline_probability"] == "0.450000"
    assert payload["rows"][0]["evidence_adjusted_probability"] == "0.530000"
    assert payload["rows"][0]["decomposed_probability"] == "0.520000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert ": 0." not in encoded
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(result)


def test_frozen_dataclasses_strict_types_and_consistency_validation() -> None:
    result = report(event())

    for value in (
        ResearchProbabilityEdgeDecompositionConfig(),
        event(),
        result.rows[0],
        result.reason_code_counts[0],
        result,
    ):
        assert hasattr(value, "__dataclass_fields__")
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="baseline_probability"):
        event(baseline_probability=0.45)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="baseline_probability"):
        event(baseline_probability=_DecimalSubclass("0.450000"))
    with pytest.raises(ValueError, match="evidence_adjustment"):
        event(evidence_adjustment=d("0.0800004"))
    with pytest.raises(ValueError, match="evidence_item_count"):
        event(evidence_item_count=d("1.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(event(), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            event(),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="decomposed_probability"):
        replace(result.rows[0], decomposed_probability=d("0.510000"))
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=())


def test_config_thresholds_control_pass_watch_block_without_action_language() -> None:
    cfg = ResearchProbabilityEdgeDecompositionConfig(
        pass_net_delta_threshold=d("0.090000"),
        watch_net_delta_threshold=d("0.010000"),
        max_pass_cost_friction=d("0.010000"),
        max_pass_conflict_discount=d("0.020000"),
        block_conflict_discount=d("0.100000"),
        min_evidence_item_count=d("2.000000"),
    )

    result = report(
        event(
            evidence_item_count=d("1.000000"),
            evidence_adjustment=d("0.000000"),
            cost_friction=d("0.000000"),
        ),
        config=cfg,
    )

    assert result.rows[0].status == "block"
    assert result.rows[0].reason_codes == (
        "evidence_adjustment_neutral",
        "insufficient_evidence_items",
        "research_probability_edge_block",
    )


def test_unsafe_identifiers_surfaces_and_runtime_io_are_not_exposed() -> None:
    unsafe_public_terms = (
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "auth",
        "wallet",
        "order",
        "submit",
        "cancel",
        "replace",
        "position_sizing",
        "buy",
        "sell",
        "recommend",
        "live",
        "trade",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_public_terms)
    for cls in (
        ResearchProbabilityEdgeDecompositionConfig,
        ResearchProbabilityEdgeInput,
        ResearchProbabilityEdgeDecompositionRow,
        ResearchProbabilityEdgeDecompositionReasonCodeCount,
        ResearchProbabilityEdgeDecompositionReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_public_terms)

    with pytest.raises(ValueError, match="event_reference"):
        event(event_reference="candidate_id_raw")
    with pytest.raises(ValueError, match="unsafe public"):
        event(event_reference="event_ref_source_url")

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_probability_edge_decomposition.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_runtime_terms = (
        "requests",
        "httpx",
        "urllib",
        "aiohttp",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "subprocess",
        "open(",
        "connect(",
    )

    assert all(term not in source for term in forbidden_runtime_terms)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))

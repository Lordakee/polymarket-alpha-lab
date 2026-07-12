from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

import polymarket_alpha_lab.strategy_candidate_selection_cutline_report as subject
from polymarket_alpha_lab.strategy_candidate_selection_cutline_report import (
    DEFAULT_STRATEGY_CANDIDATE_SELECTION_CUTLINE_REPORT_CONFIG_VERSION,
    StrategyCandidateSelectionCutlineInputs,
    StrategyCandidateSelectionCutlineReport,
    build_strategy_candidate_selection_cutline_report,
    format_strategy_candidate_selection_cutline_digest,
    strategy_candidate_selection_cutline_public_payload,
)


GENERATED_AT = datetime(2026, 7, 11, 17, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def build(
    *,
    candidate_count: Decimal = d("12.000000"),
    quality_index_score: Decimal = d("0.840000"),
    edge_to_threshold_probability: Decimal = d("0.110000"),
    source_reliability_score: Decimal = d("0.780000"),
    memory_quality_score: Decimal = d("0.720000"),
    liquidity_exit_ready: bool = True,
    operator_safety_ready: bool = True,
    manual_review_capacity_ready: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
    generated_at: datetime = GENERATED_AT,
) -> StrategyCandidateSelectionCutlineReport:
    return build_strategy_candidate_selection_cutline_report(
        candidate_count=candidate_count,
        quality_index_score=quality_index_score,
        edge_to_threshold_probability=edge_to_threshold_probability,
        source_reliability_score=source_reliability_score,
        memory_quality_score=memory_quality_score,
        liquidity_exit_ready=liquidity_exit_ready,
        operator_safety_ready=operator_safety_ready,
        manual_review_capacity_ready=manual_review_capacity_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in walk_values(child))
    return (value,)


def assert_public_numbers_are_decimals(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {
            "liquidity_exit_ready",
            "operator_safety_ready",
            "manual_review_capacity_ready",
            "selection_cutline_ready",
            "paper_only",
            "report_only",
            "readonly",
        }:
            assert type(item) is bool
        elif field.name in {"blocked_reason_codes", "attention_reason_codes"}:
            assert type(item) is tuple
        elif field.name in {"generated_at", "config_version", "cutline_band", "public_digest"}:
            continue
        elif field.name.endswith(("_count", "_score", "_probability", "_ratio")):
            assert type(item) is Decimal, field.name


def test_strategy_candidate_selection_cutline_report_selects_ready_batch_cutline() -> None:
    report = build(generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))))

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_STRATEGY_CANDIDATE_SELECTION_CUTLINE_REPORT_CONFIG_VERSION
    )
    assert report.candidate_count == d("12.000000")
    assert report.quality_index_score == d("0.840000")
    assert report.edge_to_threshold_probability == d("0.110000")
    assert report.source_reliability_score == d("0.780000")
    assert report.memory_quality_score == d("0.720000")
    assert report.selection_cutline_ready is True
    assert report.cutline_band == "select"
    assert report.selected_candidate_count == d("12.000000")
    assert report.deferred_candidate_count == ZERO
    assert report.ready_ratio == d("1.000000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.public_digest.startswith("sha256:")
    assert_public_numbers_are_decimals(report)

    digest = format_strategy_candidate_selection_cutline_digest(report)
    assert "selection_cutline_ready=true" in digest
    assert "cutline_band=select" in digest
    assert "selected_candidate_count=12.000000" in digest
    assert f"public_digest={report.public_digest}" in digest


def test_strategy_candidate_selection_cutline_defers_attention_band_candidates() -> None:
    report = build(
        candidate_count=d("10.000000"),
        quality_index_score=d("0.680000"),
        edge_to_threshold_probability=d("0.040000"),
        source_reliability_score=d("0.660000"),
        memory_quality_score=d("0.610000"),
    )

    assert report.selection_cutline_ready is True
    assert report.cutline_band == "attention"
    assert report.selected_candidate_count == d("5.000000")
    assert report.deferred_candidate_count == d("5.000000")
    assert report.ready_ratio == d("0.500000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "edge_to_threshold_probability_attention",
        "memory_quality_score_attention",
        "quality_index_score_attention",
        "source_reliability_score_attention",
    )


def test_strategy_candidate_selection_cutline_blocks_failed_gates_and_metrics() -> None:
    report = build(
        candidate_count=d("8.000000"),
        quality_index_score=d("0.440000"),
        edge_to_threshold_probability=d("-0.020000"),
        source_reliability_score=d("0.520000"),
        memory_quality_score=d("0.700000"),
        liquidity_exit_ready=False,
        operator_safety_ready=False,
        manual_review_capacity_ready=False,
    )

    assert report.selection_cutline_ready is False
    assert report.cutline_band == "blocked"
    assert report.selected_candidate_count == ZERO
    assert report.deferred_candidate_count == d("8.000000")
    assert report.ready_ratio == ZERO
    assert report.blocked_reason_codes == (
        "edge_to_threshold_probability_below_cutline",
        "liquidity_exit_not_ready",
        "manual_review_capacity_not_ready",
        "operator_safety_not_ready",
        "quality_index_score_below_cutline",
        "source_reliability_score_below_cutline",
    )
    assert report.attention_reason_codes == ()


def test_strategy_candidate_selection_cutline_payload_and_digest_are_deterministic() -> None:
    first = build()
    second = build(generated_at=GENERATED_AT)

    assert first.public_payload == second.public_payload
    assert first.public_digest == second.public_digest

    payload = strategy_candidate_selection_cutline_public_payload(first)
    assert payload == first.public_payload
    assert payload["public_digest"] == first.public_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["candidate_count"] == "12.000000"
    assert all(type(value) is not Decimal for value in walk_values(payload))
    assert not any(isinstance(value, float) for value in walk_values(payload))
    json.dumps(payload, sort_keys=True)
    assert strategy_candidate_selection_cutline_public_payload(payload) == payload

    tampered = dict(payload)
    tampered["selected_candidate_count"] = "1.000000"
    with pytest.raises(ValueError, match="public_digest"):
        strategy_candidate_selection_cutline_public_payload(tampered)

    lowered = repr(payload).lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "sign",
        "trade",
        "live",
        "execution",
        "database",
        "network",
    ):
        assert forbidden not in lowered


def test_strategy_candidate_selection_cutline_rejects_mutating_or_unsafe_modes() -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        kwargs = {flag_name: False}
        with pytest.raises(ValueError, match=flag_name):
            build(**kwargs)

    with pytest.raises(ValueError, match="read-only/report-only/paper-only"):
        subject._reject_unsafe_public_payload("unsafe", {"auth": "wallet_order_execution"})

    report = build()
    with pytest.raises(FrozenInstanceError):
        report.selected_candidate_count = ZERO  # type: ignore[misc]


def test_strategy_candidate_selection_cutline_requires_decimal_only_public_numbers() -> None:
    with pytest.raises(TypeError, match="candidate_count must be Decimal"):
        build(candidate_count=12)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="quality_index_score must be exactly Decimal"):
        build(quality_index_score=_DecimalSubclass("0.840000"))

    with pytest.raises(ValueError, match="candidate_count must be nonnegative"):
        build(candidate_count=d("-1.000000"))

    with pytest.raises(ValueError, match="quality_index_score must be no greater than 1.000000"):
        build(quality_index_score=d("1.100000"))

    with pytest.raises(TypeError, match="liquidity_exit_ready must be bool"):
        build(liquidity_exit_ready=1)  # type: ignore[arg-type]


def test_strategy_candidate_selection_cutline_inputs_are_frozen_and_buildable() -> None:
    inputs = StrategyCandidateSelectionCutlineInputs(
        candidate_count=d("6.000000"),
        quality_index_score=d("0.810000"),
        edge_to_threshold_probability=d("0.080000"),
        source_reliability_score=d("0.760000"),
        memory_quality_score=d("0.740000"),
        liquidity_exit_ready=True,
        operator_safety_ready=True,
        manual_review_capacity_ready=True,
    )

    report = build_strategy_candidate_selection_cutline_report(inputs, generated_at=GENERATED_AT)

    assert report.selection_cutline_ready is True
    assert report.cutline_band == "select"
    assert report.selected_candidate_count == d("6.000000")
    assert report.public_payload["candidate_count"] == "6.000000"
    with pytest.raises(FrozenInstanceError):
        inputs.candidate_count = ZERO  # type: ignore[misc]


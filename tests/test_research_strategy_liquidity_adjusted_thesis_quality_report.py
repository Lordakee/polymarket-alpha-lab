from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_strategy_liquidity_adjusted_thesis_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def thesis_input(
    *,
    public_thesis_key: str = "thesis-alpha",
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=1800),
    evidence_strength_score: str = "0.820000",
    model_market_divergence_score: str = "0.100000",
    spread_quality_score: str = "0.850000",
    depth_quality_score: str = "0.830000",
    fee_drag_score: str = "0.010000",
    resolution_clarity_score: str = "0.800000",
    specialist_memory_confidence_score: str = "0.810000",
):
    report_api = api()
    return report_api.ResearchStrategyLiquidityAdjustedThesisQualityInput(
        public_thesis_key=public_thesis_key,
        source_observed_at=source_observed_at,
        evidence_strength_score=d(evidence_strength_score),
        model_market_divergence_score=d(model_market_divergence_score),
        spread_quality_score=d(spread_quality_score),
        depth_quality_score=d(depth_quality_score),
        fee_drag_score=d(fee_drag_score),
        resolution_clarity_score=d(resolution_clarity_score),
        specialist_memory_confidence_score=d(specialist_memory_confidence_score),
    )


def build_report(*items, generated_at: datetime = GENERATED_AT, config=None):
    report_api = api()
    return report_api.build_research_strategy_liquidity_adjusted_thesis_quality_report(
        items,
        config=config or report_api.ResearchStrategyLiquidityAdjustedThesisQualityConfig(),
        generated_at=generated_at,
    )


def test_scores_liquidity_adjusted_thesis_quality_without_action_surfaces():
    quality_report = build_report(
        thesis_input(),
        thesis_input(
            public_thesis_key="thesis-beta",
            source_observed_at=GENERATED_AT - timedelta(seconds=8000),
            evidence_strength_score="0.680000",
            model_market_divergence_score="0.350000",
            spread_quality_score="0.700000",
            depth_quality_score="0.600000",
            fee_drag_score="0.040000",
            resolution_clarity_score="0.650000",
            specialist_memory_confidence_score="0.660000",
        ),
        thesis_input(
            public_thesis_key="thesis-gamma",
            source_observed_at=GENERATED_AT - timedelta(seconds=30000),
            evidence_strength_score="0.400000",
            model_market_divergence_score="0.700000",
            spread_quality_score="0.400000",
            depth_quality_score="0.300000",
            fee_drag_score="0.070000",
            resolution_clarity_score="0.440000",
            specialist_memory_confidence_score="0.300000",
        ),
    )

    assert is_dataclass(quality_report)
    assert quality_report.generated_at == GENERATED_AT
    assert quality_report.config_version == (
        "research-strategy-liquidity-adjusted-thesis-quality-report-v0"
    )
    assert quality_report.input_count == d("3")
    assert quality_report.pass_count == d("1")
    assert quality_report.watch_count == d("1")
    assert quality_report.block_count == d("1")
    assert quality_report.status == "block"
    assert quality_report.average_source_backed_thesis_quality_score == d("0.597086")
    assert quality_report.average_liquidity_cost_quality_score == d("0.786667")
    assert quality_report.average_liquidity_adjusted_thesis_quality_score == d("0.495957")
    assert quality_report.average_liquidity_adjustment_drag == d("0.101130")
    assert quality_report.max_liquidity_adjustment_drag == d("0.127516")
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True

    assert tuple(row.status for row in quality_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    blocked, watched, passing = quality_report.rows
    assert blocked.rank == d("1")
    assert blocked.public_thesis_key == "thesis-gamma"
    assert blocked.source_freshness_score == d("0.000000")
    assert blocked.model_market_convergence_score == d("0.300000")
    assert blocked.spread_depth_quality_score == d("0.350000")
    assert blocked.liquidity_cost_quality_score == d("0.640000")
    assert blocked.source_backed_thesis_quality_score == d("0.288000")
    assert blocked.liquidity_adjusted_thesis_quality_score == d("0.184320")
    assert blocked.liquidity_adjustment_drag == d("0.103680")
    assert blocked.reason_codes == (
        "liquidity_adjusted_thesis_quality_block",
        "source_freshness_block",
        "evidence_strength_block",
        "model_market_divergence_block",
        "spread_depth_quality_block",
        "fee_drag_block",
        "resolution_clarity_block",
        "specialist_memory_confidence_block",
    )
    assert watched.reason_codes == (
        "liquidity_adjusted_thesis_quality_watch",
        "source_freshness_watch",
        "evidence_strength_watch",
        "model_market_divergence_watch",
        "spread_depth_quality_watch",
        "fee_drag_watch",
        "resolution_clarity_watch",
        "specialist_memory_confidence_watch",
    )
    assert passing.reason_codes == ("liquidity_adjusted_thesis_quality_pass",)

    reason_counts = {row.reason_code: row.count for row in quality_report.reason_code_counts}
    assert reason_counts["liquidity_adjusted_thesis_quality_block"] == d("1")
    assert reason_counts["liquidity_adjusted_thesis_quality_watch"] == d("1")
    assert reason_counts["liquidity_adjusted_thesis_quality_pass"] == d("1")

    payload = api().research_strategy_liquidity_adjusted_thesis_quality_report_payload(
        quality_report,
    )
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate_id",
        "candidate_slug",
        "market_id",
        "market_slug",
        "market_question",
        "question:",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "position",
        "sizing",
    ):
        assert forbidden not in encoded.lower()


def test_empty_report_is_blocked_report_only_boundary():
    quality_report = build_report()

    assert quality_report.status == "block"
    assert quality_report.input_count == d("0")
    assert quality_report.pass_count == d("0")
    assert quality_report.watch_count == d("0")
    assert quality_report.block_count == d("0")
    assert quality_report.reason_codes == (
        "no_liquidity_adjusted_thesis_quality_inputs",
    )
    assert quality_report.reason_code_counts == (
        api().ResearchStrategyLiquidityAdjustedThesisQualityReasonCodeCount(
            reason_code="no_liquidity_adjusted_thesis_quality_inputs",
            count=d("0"),
        ),
    )
    assert quality_report.rows == ()
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True


def test_payload_serializes_decimal_strings_and_validates_sha256_digest():
    report_api = api()
    quality_report = build_report(thesis_input())

    payload = report_api.research_strategy_liquidity_adjusted_thesis_quality_report_payload(
        quality_report,
    )

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["evidence_strength_score"] == "0.820000"
    assert payload["rows"][0]["source_age_seconds"] == "1800.000000"
    assert payload["rows"][0]["source_backed_thesis_quality_score"] == "0.849333"
    assert payload["rows"][0]["liquidity_adjusted_thesis_quality_score"] == "0.777140"
    assert len(payload["public_payload_digest"]) == 64
    assert payload["public_payload_digest"] == quality_report.public_payload_digest
    assert all(type(value) is not float for value in _walk(payload))
    assert all(type(value) is not int for value in _walk(payload))

    with pytest.raises(TypeError, match="immutable"):
        payload["status"] = "pass"
    with pytest.raises(TypeError, match="immutable"):
        payload["rows"].append({"unsafe": "value"})
    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(quality_report, public_payload_digest="0" * 64)

    tampered_report = replace(quality_report)
    object.__setattr__(tampered_report, "public_payload_digest", "0" * 64)
    with pytest.raises(ValueError, match="public_payload_digest"):
        report_api.research_strategy_liquidity_adjusted_thesis_quality_report_payload(
            tampered_report,
        )


def test_validation_rejects_floats_time_errors_flags_and_restricted_labels():
    report_api = api()

    with pytest.raises(ValueError, match="evidence_strength_score must be a Decimal"):
        report_api.ResearchStrategyLiquidityAdjustedThesisQualityInput(
            public_thesis_key="thesis-alpha",
            source_observed_at=GENERATED_AT,
            evidence_strength_score=0.5,
            model_market_divergence_score=d("0.100000"),
            spread_quality_score=d("0.800000"),
            depth_quality_score=d("0.800000"),
            fee_drag_score=d("0.010000"),
            resolution_clarity_score=d("0.800000"),
            specialist_memory_confidence_score=d("0.800000"),
        )
    with pytest.raises(ValueError, match="fee_drag_score must be finite"):
        thesis_input(fee_drag_score="NaN")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(thesis_input(), paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        report_api.ResearchStrategyLiquidityAdjustedThesisQualityConfig(readonly=False)
    with pytest.raises(ValueError, match="watch_quality_score"):
        report_api.ResearchStrategyLiquidityAdjustedThesisQualityConfig(
            watch_quality_score=d("0.400000"),
            block_quality_score=d("0.500000"),
        )
    with pytest.raises(ValueError, match="restricted references"):
        thesis_input(public_thesis_key="market_slug:raw-value")
    with pytest.raises(ValueError, match="public_thesis_key must be a sanitized"):
        thesis_input(public_thesis_key="will-fed-cut-rates-in-july")
    with pytest.raises(ValueError, match="public_thesis_key must not expose raw identifiers"):
        thesis_input(public_thesis_key="thesis-550e8400-e29b-41d4-a716-446655440000")
    with pytest.raises(ValueError, match="public_thesis_key must be a sanitized"):
        thesis_input(public_thesis_key="thesis-Will Fed cut rates?")

    class DateTimeSubclass(datetime):
        pass

    class NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    eastern = timezone(timedelta(hours=-4))
    quality_report = build_report(
        thesis_input(source_observed_at=datetime(2026, 7, 8, 7, 0, tzinfo=eastern)),
    )
    assert quality_report.rows[0].source_observed_at == datetime(
        2026,
        7,
        8,
        11,
        0,
        tzinfo=UTC,
    )
    assert quality_report.rows[0].source_age_seconds == d("3600.000000")

    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        thesis_input(source_observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(
            thesis_input(),
            generated_at=DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        thesis_input(
            source_observed_at=datetime(2026, 7, 8, 12, 0, tzinfo=NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="source_observed_at must not be after"):
        build_report(thesis_input(source_observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_public_dataclasses_are_frozen_and_sequences_are_deterministic():
    report_api = api()

    class DecimalSubclass(Decimal):
        pass

    row = thesis_input()
    with pytest.raises(FrozenInstanceError):
        row.evidence_strength_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="model_market_divergence_score must be a Decimal"):
        report_api.ResearchStrategyLiquidityAdjustedThesisQualityInput(
            public_thesis_key="thesis-alpha",
            source_observed_at=GENERATED_AT,
            evidence_strength_score=d("0.500000"),
            model_market_divergence_score=DecimalSubclass("0.100000"),
            spread_quality_score=d("0.800000"),
            depth_quality_score=d("0.800000"),
            fee_drag_score=d("0.010000"),
            resolution_clarity_score=d("0.800000"),
            specialist_memory_confidence_score=d("0.800000"),
        )

    quality_report = build_report(
        thesis_input(public_thesis_key="thesis-zeta"),
        thesis_input(public_thesis_key="thesis-alpha"),
    )
    assert tuple(row.public_thesis_key for row in quality_report.rows) == (
        "thesis-alpha",
        "thesis-zeta",
    )

    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(quality_report, rows=tuple(reversed(quality_report.rows)))
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        report_api.ResearchStrategyLiquidityAdjustedThesisQualityRow(
            rank=d("1"),
            public_thesis_key="thesis-beta",
            status="watch",
            source_observed_at=GENERATED_AT - timedelta(seconds=8000),
            source_age_seconds=d("8000.000000"),
            source_freshness_score=d("0.629630"),
            evidence_strength_score=d("0.680000"),
            model_market_divergence_score=d("0.350000"),
            model_market_convergence_score=d("0.650000"),
            spread_quality_score=d("0.700000"),
            depth_quality_score=d("0.600000"),
            spread_depth_quality_score=d("0.650000"),
            fee_drag_score=d("0.040000"),
            liquidity_cost_quality_score=d("0.805000"),
            resolution_clarity_score=d("0.650000"),
            specialist_memory_confidence_score=d("0.660000"),
            source_backed_thesis_quality_score=d("0.653926"),
            liquidity_adjusted_thesis_quality_score=d("0.526410"),
            liquidity_adjustment_drag=d("0.127516"),
            reason_codes=(
                "source_freshness_watch",
                "liquidity_adjusted_thesis_quality_watch",
            ),
        )


def _walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk(item)
    else:
        yield value

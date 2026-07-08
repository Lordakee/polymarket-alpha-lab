from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_source_liquidity_thesis_alignment_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    public_thesis_key: str = "thesis-alpha",
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=1800),
    evidence_strength_score: str = "0.820000",
    market_divergence_score: str = "0.100000",
    spread_quality_score: str = "0.850000",
    depth_quality_score: str = "0.830000",
    fee_drag_score: str = "0.010000",
    resolution_clarity_score: str = "0.800000",
    specialist_memory_confidence_score: str = "0.810000",
):
    report_api = api()
    return report_api.ResearchStrategySourceLiquidityThesisAlignmentInput(
        public_thesis_key=public_thesis_key,
        source_observed_at=source_observed_at,
        evidence_strength_score=d(evidence_strength_score),
        market_divergence_score=d(market_divergence_score),
        spread_quality_score=d(spread_quality_score),
        depth_quality_score=d(depth_quality_score),
        fee_drag_score=d(fee_drag_score),
        resolution_clarity_score=d(resolution_clarity_score),
        specialist_memory_confidence_score=d(specialist_memory_confidence_score),
    )


def build_report(*items, generated_at: datetime = GENERATED_AT, config=None):
    report_api = api()
    return report_api.build_research_strategy_source_liquidity_thesis_alignment_report(
        items,
        config=config
        or report_api.ResearchStrategySourceLiquidityThesisAlignmentConfig(),
        generated_at=generated_at,
    )


def test_report_scores_source_thesis_quality_against_liquidity_cost_conditions():
    alignment_report = build_report(
        observation(),
        observation(
            public_thesis_key="thesis-beta",
            source_observed_at=GENERATED_AT - timedelta(seconds=8000),
            evidence_strength_score="0.680000",
            market_divergence_score="0.350000",
            spread_quality_score="0.700000",
            depth_quality_score="0.600000",
            fee_drag_score="0.040000",
            resolution_clarity_score="0.650000",
            specialist_memory_confidence_score="0.660000",
        ),
        observation(
            public_thesis_key="thesis-gamma",
            source_observed_at=GENERATED_AT - timedelta(seconds=30000),
            evidence_strength_score="0.400000",
            market_divergence_score="0.700000",
            spread_quality_score="0.400000",
            depth_quality_score="0.300000",
            fee_drag_score="0.070000",
            resolution_clarity_score="0.440000",
            specialist_memory_confidence_score="0.300000",
        ),
    )

    assert is_dataclass(alignment_report)
    assert alignment_report.generated_at == GENERATED_AT
    assert alignment_report.config_version == (
        "research-strategy-source-liquidity-thesis-alignment-report-v0"
    )
    assert alignment_report.input_count == d("3")
    assert alignment_report.pass_count == d("1")
    assert alignment_report.watch_count == d("1")
    assert alignment_report.block_count == d("1")
    assert alignment_report.status == "block"
    assert alignment_report.average_source_backed_thesis_quality_score == d("0.592192")
    assert alignment_report.average_liquidity_cost_quality_score == d("0.786667")
    assert alignment_report.average_source_liquidity_alignment_gap == d("0.194475")
    assert alignment_report.average_alignment_pressure == d("0.523457")
    assert alignment_report.max_alignment_pressure == d("1.000000")
    assert alignment_report.paper_only is True
    assert alignment_report.report_only is True
    assert alignment_report.readonly is True

    assert tuple(row.status for row in alignment_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    blocked, watch, passing = alignment_report.rows
    assert blocked.rank == d("1")
    assert blocked.public_thesis_key == "thesis-gamma"
    assert blocked.source_freshness_score == d("0.000000")
    assert blocked.spread_depth_quality_score == d("0.350000")
    assert blocked.liquidity_cost_quality_score == d("0.640000")
    assert blocked.source_backed_thesis_quality_score == d("0.285000")
    assert blocked.source_liquidity_alignment_gap == d("0.355000")
    assert blocked.alignment_pressure == d("1.000000")
    assert blocked.reason_codes == (
        "source_liquidity_thesis_alignment_gap_block",
        "source_freshness_block",
        "evidence_strength_block",
        "market_divergence_block",
        "spread_depth_quality_block",
        "fee_drag_block",
        "resolution_clarity_block",
        "specialist_memory_confidence_block",
        "alignment_pressure_block",
    )
    assert watch.reason_codes == (
        "source_liquidity_thesis_alignment_gap_watch",
        "source_freshness_watch",
        "evidence_strength_watch",
        "market_divergence_watch",
        "spread_depth_quality_watch",
        "fee_drag_watch",
        "resolution_clarity_watch",
        "specialist_memory_confidence_watch",
        "alignment_pressure_watch",
    )
    assert passing.reason_codes == ("source_liquidity_thesis_alignment_gap_pass",)

    payload = api().research_strategy_source_liquidity_thesis_alignment_report_payload(
        alignment_report,
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
    ):
        assert forbidden not in encoded.lower()


def test_empty_report_is_blocked_report_only_boundary():
    alignment_report = build_report()

    assert alignment_report.input_count == d("0")
    assert alignment_report.pass_count == d("0")
    assert alignment_report.watch_count == d("0")
    assert alignment_report.block_count == d("0")
    assert alignment_report.status == "block"
    assert alignment_report.reason_codes == (
        "empty_source_liquidity_thesis_alignment_inputs",
    )
    assert alignment_report.reason_code_counts == ()
    assert alignment_report.rows == ()
    assert alignment_report.paper_only is True
    assert alignment_report.report_only is True
    assert alignment_report.readonly is True


def test_public_payload_serializes_decimal_strings_and_validates_sha256_digest():
    report_api = api()
    alignment_report = build_report(observation())

    payload = report_api.research_strategy_source_liquidity_thesis_alignment_report_payload(
        alignment_report,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["rows"][0]["evidence_strength_score"] == "0.820000"
    assert payload["rows"][0]["source_age_seconds"] == "1800.000000"
    assert payload["rows"][0]["source_backed_thesis_quality_score"] == "0.836667"
    assert len(payload["public_payload_digest"]) == 64
    assert payload["public_payload_digest"] == alignment_report.public_payload_digest
    assert all(type(value) is not float for value in _walk(payload))
    assert all(type(value) is not int for value in _walk(payload))

    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(alignment_report, public_payload_digest="0" * 64)

    tampered_report = replace(alignment_report)
    object.__setattr__(tampered_report, "public_payload_digest", "0" * 64)
    with pytest.raises(ValueError, match="public_payload_digest"):
        report_api.research_strategy_source_liquidity_thesis_alignment_report_payload(
            tampered_report,
        )


def test_datetimes_normalize_to_utc_and_reject_invalid_time_values():
    eastern = timezone(timedelta(hours=-4))
    alignment_report = build_report(
        observation(source_observed_at=datetime(2026, 7, 8, 7, 0, tzinfo=eastern)),
        generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
    )

    assert alignment_report.rows[0].source_observed_at == datetime(
        2026,
        7,
        8,
        11,
        0,
        tzinfo=UTC,
    )
    assert alignment_report.rows[0].source_age_seconds == d("3600.000000")

    class DateTimeSubclass(datetime):
        pass

    class NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        observation(source_observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(
            observation(),
            generated_at=DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        observation(
            source_observed_at=datetime(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=NoneOffsetTz(),
            ),
        )
    with pytest.raises(ValueError, match="source_observed_at must not be after"):
        build_report(
            observation(source_observed_at=GENERATED_AT + timedelta(seconds=1)),
        )


def test_validation_rejects_floats_nonfinite_decimals_flags_and_restricted_labels():
    report_api = api()

    with pytest.raises(ValueError, match="evidence_strength_score must be a Decimal"):
        report_api.ResearchStrategySourceLiquidityThesisAlignmentInput(
            public_thesis_key="thesis-alpha",
            source_observed_at=GENERATED_AT,
            evidence_strength_score=0.5,
            market_divergence_score=d("0.100000"),
            spread_quality_score=d("0.800000"),
            depth_quality_score=d("0.800000"),
            fee_drag_score=d("0.010000"),
            resolution_clarity_score=d("0.800000"),
            specialist_memory_confidence_score=d("0.800000"),
        )
    with pytest.raises(ValueError, match="fee_drag_score must be finite"):
        observation(fee_drag_score="NaN")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(observation(), paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        report_api.ResearchStrategySourceLiquidityThesisAlignmentConfig(readonly=False)
    with pytest.raises(ValueError, match="watch_alignment_gap"):
        report_api.ResearchStrategySourceLiquidityThesisAlignmentConfig(
            watch_alignment_gap=d("0.400000"),
            block_alignment_gap=d("0.300000"),
        )
    with pytest.raises(ValueError, match="restricted references"):
        observation(public_thesis_key="market_slug:raw-value")


def test_public_dataclasses_are_frozen_and_decimal_types_are_strict():
    report_api = api()

    class DecimalSubclass(Decimal):
        pass

    row = observation()
    with pytest.raises(FrozenInstanceError):
        row.evidence_strength_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="market_divergence_score must be a Decimal"):
        report_api.ResearchStrategySourceLiquidityThesisAlignmentInput(
            public_thesis_key="thesis-alpha",
            source_observed_at=GENERATED_AT,
            evidence_strength_score=d("0.500000"),
            market_divergence_score=DecimalSubclass("0.100000"),
            spread_quality_score=d("0.800000"),
            depth_quality_score=d("0.800000"),
            fee_drag_score=d("0.010000"),
            resolution_clarity_score=d("0.800000"),
            specialist_memory_confidence_score=d("0.800000"),
        )


def test_public_report_rejects_nondeterministic_row_sequence_and_reason_codes():
    report_api = api()
    alignment_report = build_report(
        observation(
            public_thesis_key="thesis-gamma",
            source_observed_at=GENERATED_AT - timedelta(seconds=30000),
            evidence_strength_score="0.400000",
            market_divergence_score="0.700000",
            spread_quality_score="0.400000",
            depth_quality_score="0.300000",
            fee_drag_score="0.070000",
            resolution_clarity_score="0.440000",
            specialist_memory_confidence_score="0.300000",
        ),
        observation(),
    )

    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(alignment_report, rows=tuple(reversed(alignment_report.rows)))
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        report_api.ResearchStrategySourceLiquidityThesisAlignmentRow(
            rank=d("1"),
            public_thesis_key="thesis-beta",
            status="watch",
            source_observed_at=GENERATED_AT - timedelta(seconds=8000),
            source_age_seconds=d("8000.000000"),
            source_freshness_score=d("0.629630"),
            evidence_strength_score=d("0.680000"),
            market_divergence_score=d("0.350000"),
            spread_quality_score=d("0.700000"),
            depth_quality_score=d("0.600000"),
            spread_depth_quality_score=d("0.650000"),
            fee_drag_score=d("0.040000"),
            liquidity_cost_quality_score=d("0.805000"),
            resolution_clarity_score=d("0.650000"),
            specialist_memory_confidence_score=d("0.660000"),
            source_backed_thesis_quality_score=d("0.654908"),
            source_liquidity_alignment_gap=d("0.150092"),
            alignment_pressure=d("0.370370"),
            reason_codes=(
                "alignment_pressure_watch",
                "source_liquidity_thesis_alignment_gap_watch",
                "source_freshness_watch",
                "evidence_strength_watch",
            ),
        )


def test_module_scope_has_no_forbidden_execution_surfaces_or_literal_float_constants():
    source_text = Path(
        "src/polymarket_alpha_lab/research_strategy_source_liquidity_thesis_alignment_report.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "account",
        "broker",
        "signing",
        "submit",
        "cancel",
        "database",
        "open(",
        "requests",
        "socket",
        "scrap",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value

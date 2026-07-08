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
        "polymarket_alpha_lab.research_strategy_probability_source_alignment_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    forecast_probability: str = "0.600000",
    evidence_strength_score: str = "0.610000",
    source_confidence: str = "0.900000",
    evidence_observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    contradiction_pressure: str = "0.050000",
    calibration_support_score: str = "0.850000",
):
    report_api = api()
    return report_api.ResearchStrategyProbabilitySourceAlignmentInput(
        forecast_probability=d(forecast_probability),
        evidence_strength_score=d(evidence_strength_score),
        source_confidence=d(source_confidence),
        evidence_observed_at=evidence_observed_at,
        contradiction_pressure=d(contradiction_pressure),
        calibration_support_score=d(calibration_support_score),
    )


def build_report(*items, generated_at: datetime = GENERATED_AT, config=None):
    report_api = api()
    return report_api.build_research_strategy_probability_source_alignment_report(
        items,
        config=config or report_api.ResearchStrategyProbabilitySourceAlignmentConfig(),
        generated_at=generated_at,
    )


def test_report_aggregates_pass_watch_and_block_alignment_without_raw_identifiers():
    alignment_report = build_report(
        observation(),
        observation(
            forecast_probability="0.700000",
            evidence_strength_score="0.550000",
            source_confidence="0.620000",
            evidence_observed_at=GENERATED_AT - timedelta(seconds=8000),
            contradiction_pressure="0.300000",
            calibration_support_score="0.550000",
        ),
        observation(
            forecast_probability="0.900000",
            evidence_strength_score="0.500000",
            source_confidence="0.350000",
            evidence_observed_at=GENERATED_AT - timedelta(seconds=30000),
            contradiction_pressure="0.650000",
            calibration_support_score="0.300000",
        ),
    )

    assert is_dataclass(alignment_report)
    assert alignment_report.generated_at == GENERATED_AT
    assert alignment_report.config_version == (
        "research-strategy-probability-source-alignment-report-v0"
    )
    assert alignment_report.observation_count == d("3")
    assert alignment_report.pass_count == d("1")
    assert alignment_report.watch_count == d("1")
    assert alignment_report.block_count == d("1")
    assert alignment_report.status == "block"
    assert alignment_report.average_forecast_probability == d("0.733333")
    assert alignment_report.average_evidence_strength_score == d("0.553333")
    assert alignment_report.average_source_confidence == d("0.623333")
    assert alignment_report.average_contradiction_pressure == d("0.333333")
    assert alignment_report.average_calibration_support_score == d("0.566667")
    assert alignment_report.average_manual_review_urgency == d("0.433333")
    assert alignment_report.max_manual_review_urgency == d("0.700000")
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
    assert blocked.alignment_gap == d("0.400000")
    assert blocked.evidence_age_seconds == d("30000")
    assert blocked.evidence_recency_score == d("0.000000")
    assert blocked.manual_review_urgency == d("0.700000")
    assert blocked.reason_codes == (
        "probability_evidence_gap_block",
        "source_confidence_low_block",
        "evidence_recency_block",
        "contradiction_pressure_block",
        "calibration_support_low_block",
        "manual_review_urgency_block",
    )
    assert watch.status == "watch"
    assert watch.reason_codes == (
        "probability_evidence_gap_watch",
        "source_confidence_low_watch",
        "evidence_recency_watch",
        "contradiction_pressure_watch",
        "calibration_support_low_watch",
        "manual_review_urgency_watch",
    )
    assert passing.status == "pass"
    assert passing.reason_codes == ("probability_evidence_aligned",)

    payload = api().research_strategy_probability_source_alignment_report_payload(
        alignment_report,
    )
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate_id",
        "candidate_slug",
        "market_id",
        "market_slug",
        "source_id",
        "source_reference",
        "buy",
        "sell",
        "recommend",
    ):
        assert forbidden not in encoded.lower()


def test_empty_report_is_blocked_readonly_manual_review_boundary():
    alignment_report = build_report()

    assert alignment_report.observation_count == d("0")
    assert alignment_report.pass_count == d("0")
    assert alignment_report.watch_count == d("0")
    assert alignment_report.block_count == d("0")
    assert alignment_report.status == "block"
    assert alignment_report.reason_codes == (
        "empty_probability_source_alignment_inputs",
    )
    assert alignment_report.reason_code_counts == ()
    assert alignment_report.rows == ()
    assert alignment_report.paper_only is True
    assert alignment_report.report_only is True
    assert alignment_report.readonly is True


def test_public_payload_serializes_decimal_strings_and_validates_sha256_digest():
    report_api = api()
    alignment_report = build_report(observation())

    payload = report_api.research_strategy_probability_source_alignment_report_payload(
        alignment_report,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["observation_count"] == "1"
    assert payload["rows"][0]["forecast_probability"] == "0.600000"
    assert len(payload["public_payload_digest"]) == 64
    assert payload["public_payload_digest"] == alignment_report.public_payload_digest
    assert all(type(value) is not float for value in _walk(payload))
    assert all(type(value) is not int for value in _walk(payload))

    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(alignment_report, public_payload_digest="0" * 64)

    tampered_report = replace(alignment_report)
    object.__setattr__(tampered_report, "public_payload_digest", "0" * 64)
    with pytest.raises(ValueError, match="public_payload_digest"):
        report_api.research_strategy_probability_source_alignment_report_payload(
            tampered_report,
        )


def test_datetimes_normalize_to_utc_and_reject_invalid_time_values():
    eastern = timezone(timedelta(hours=-4))
    alignment_report = build_report(
        observation(
            evidence_observed_at=datetime(2026, 7, 8, 7, 0, tzinfo=eastern),
        ),
        generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
    )

    assert alignment_report.rows[0].evidence_observed_at == datetime(
        2026,
        7,
        8,
        11,
        0,
        tzinfo=UTC,
    )
    assert alignment_report.rows[0].evidence_age_seconds == d("3600")

    class DateTimeSubclass(datetime):
        pass

    class NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="evidence_observed_at must be timezone-aware"):
        observation(evidence_observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(
            observation(),
            generated_at=DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must be timezone-aware"):
        observation(
            evidence_observed_at=datetime(2026, 7, 8, 12, 0, tzinfo=NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must not be after"):
        build_report(
            observation(evidence_observed_at=GENERATED_AT + timedelta(seconds=1)),
        )


def test_validation_rejects_floats_nonfinite_decimals_and_flag_downgrades():
    report_api = api()

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        report_api.ResearchStrategyProbabilitySourceAlignmentInput(
            forecast_probability=0.5,
            evidence_strength_score=d("0.500000"),
            source_confidence=d("0.900000"),
            evidence_observed_at=GENERATED_AT,
            contradiction_pressure=d("0.000000"),
            calibration_support_score=d("0.900000"),
        )
    with pytest.raises(ValueError, match="forecast_probability must be finite"):
        observation(forecast_probability="NaN")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(observation(), paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        report_api.ResearchStrategyProbabilitySourceAlignmentConfig(readonly=False)
    with pytest.raises(ValueError, match="watch_alignment_gap"):
        report_api.ResearchStrategyProbabilitySourceAlignmentConfig(
            watch_alignment_gap=d("0.300000"),
            block_alignment_gap=d("0.200000"),
        )


def test_public_dataclasses_are_frozen_and_decimal_types_are_strict():
    report_api = api()

    class DecimalSubclass(Decimal):
        pass

    row = observation()
    with pytest.raises(FrozenInstanceError):
        row.forecast_probability = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_confidence must be a Decimal"):
        report_api.ResearchStrategyProbabilitySourceAlignmentInput(
            forecast_probability=d("0.500000"),
            evidence_strength_score=d("0.500000"),
            source_confidence=DecimalSubclass("0.900000"),
            evidence_observed_at=GENERATED_AT,
            contradiction_pressure=d("0.000000"),
            calibration_support_score=d("0.900000"),
        )


def test_public_report_rejects_nondeterministic_row_sequence_and_reason_codes():
    report_api = api()
    alignment_report = build_report(
        observation(
            forecast_probability="0.900000",
            evidence_strength_score="0.500000",
            source_confidence="0.350000",
            evidence_observed_at=GENERATED_AT - timedelta(seconds=30000),
            contradiction_pressure="0.650000",
            calibration_support_score="0.300000",
        ),
        observation(),
    )

    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(alignment_report, rows=tuple(reversed(alignment_report.rows)))
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        report_api.ResearchStrategyProbabilitySourceAlignmentRow(
            rank=d("1"),
            status="watch",
            forecast_probability=d("0.700000"),
            evidence_strength_score=d("0.550000"),
            source_confidence=d("0.620000"),
            evidence_observed_at=GENERATED_AT - timedelta(seconds=8000),
            evidence_age_seconds=d("8000"),
            evidence_recency_score=d("0.629630"),
            contradiction_pressure=d("0.300000"),
            calibration_support_score=d("0.550000"),
            alignment_gap=d("0.150000"),
            manual_review_urgency=d("0.450000"),
            reason_codes=(
                "manual_review_urgency_watch",
                "probability_evidence_gap_watch",
                "source_confidence_low_watch",
                "evidence_recency_watch",
                "contradiction_pressure_watch",
                "calibration_support_low_watch",
            ),
        )


def test_module_scope_has_no_forbidden_surfaces_or_literal_float_constants():
    source_text = Path(
        "src/polymarket_alpha_lab/research_strategy_probability_source_alignment_report.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "broker",
        "signing",
        "submit",
        "cancel",
        "network",
        "database",
        "open(",
        "requests",
        "http",
        "socket",
        "fast",
        "live",
        "sizing",
        "recommendation",
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

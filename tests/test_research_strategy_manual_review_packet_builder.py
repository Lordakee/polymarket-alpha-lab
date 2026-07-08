from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_manual_review_packet_builder import (
    MANUAL_REVIEW_PACKET_PUBLIC_STATUSES,
    RESEARCH_STRATEGY_MANUAL_REVIEW_PACKET_REASON_CODES,
    ResearchStrategyManualReviewPacketConfig,
    ResearchStrategyManualReviewPacketInput,
    ResearchStrategyManualReviewPacketReport,
    build_research_strategy_manual_review_packet,
    research_strategy_manual_review_packet_digest,
    research_strategy_manual_review_packet_public_payload,
    validate_research_strategy_manual_review_packet_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def packet(**overrides: object) -> ResearchStrategyManualReviewPacketInput:
    values = {
        "packet_key": "review-alpha",
        "signal_strength": d("0.610000"),
        "signal_confidence": d("0.820000"),
        "evidence_gap_score": d("0.100000"),
        "cost_surface_score": d("0.120000"),
        "calibration_drift_score": d("0.050000"),
        "team_capacity_score": d("0.850000"),
        "team_disagreement_score": d("0.080000"),
        "hard_flag_count": d("0"),
        "assigned_team": "research-review",
    }
    values.update(overrides)
    return ResearchStrategyManualReviewPacketInput(**values)


def build_report(
    packets: tuple[ResearchStrategyManualReviewPacketInput, ...],
    *,
    config: ResearchStrategyManualReviewPacketConfig | None = None,
) -> ResearchStrategyManualReviewPacketReport:
    return build_research_strategy_manual_review_packet(
        packets,
        generated_at=GENERATED_AT,
        config=config,
    )


def test_pass_packet_builds_public_decimal_only_report_and_digest() -> None:
    report = build_report((packet(),))

    assert report.public_status == "pass"
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.packet_count == d("1")
    assert report.reason_codes == ("manual_review_packet_pass",)
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)

    row = report.review_rows[0]
    assert row.packet_key == "review-alpha"
    assert row.public_status == "pass"
    assert row.review_focus == "ready_for_human_review"
    assert row.reason_codes == ("manual_review_packet_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True

    payload = research_strategy_manual_review_packet_public_payload(report)
    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-08T12:30:00+00:00"
    assert payload["public_status"] == "pass"
    assert payload["packet_count"] == "1"
    assert payload["review_rows"][0]["signal_strength"] == "0.610000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert research_strategy_manual_review_packet_digest(report) == report.derived_validation_digest
    assert research_strategy_manual_review_packet_digest(payload) == report.derived_validation_digest
    assert validate_research_strategy_manual_review_packet_public_payload(payload)
    assert_no_public_numeric_scalars(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_watch_packet_summarizes_evidence_cost_drift_and_team_gaps() -> None:
    report = build_report(
        (
            packet(
                packet_key="review-watch",
                signal_confidence=d("0.580000"),
                evidence_gap_score=d("0.450000"),
                cost_surface_score=d("0.340000"),
                calibration_drift_score=d("0.220000"),
                team_capacity_score=d("0.420000"),
                team_disagreement_score=d("0.350000"),
            ),
        ),
    )

    assert report.public_status == "watch"
    assert report.watch_count == d("1")
    assert report.block_count == d("0")
    assert report.reason_codes == (
        "signal_confidence_below_floor",
        "evidence_gap_watch",
        "cost_surface_watch",
        "calibration_drift_watch",
        "team_capacity_watch",
        "team_disagreement_watch",
    )
    row = report.review_rows[0]
    assert row.public_status == "watch"
    assert row.review_focus == "refresh_manual_review_inputs"
    assert row.assigned_team == "research-review"


def test_block_packet_prioritizes_hard_flags_and_block_thresholds() -> None:
    report = build_report(
        (
            packet(
                packet_key="review-block",
                evidence_gap_score=d("0.800000"),
                cost_surface_score=d("0.810000"),
                calibration_drift_score=d("0.720000"),
                team_capacity_score=d("0.200000"),
                team_disagreement_score=d("0.750000"),
                hard_flag_count=d("2"),
                assigned_team="risk-review",
            ),
        ),
    )

    assert report.public_status == "block"
    assert report.block_count == d("1")
    assert report.reason_codes == (
        "evidence_gap_block",
        "cost_surface_block",
        "calibration_drift_block",
        "team_capacity_block",
        "team_disagreement_block",
        "hard_review_flag",
    )
    row = report.review_rows[0]
    assert row.public_status == "block"
    assert row.review_focus == "repair_before_manual_review"
    assert row.hard_flag_count == d("2")


def test_report_is_deterministic_for_input_order_and_payload_digest() -> None:
    alpha = packet(packet_key="review-alpha", assigned_team="research-review")
    beta = packet(
        packet_key="review-beta",
        evidence_gap_score=d("0.500000"),
        assigned_team="risk-review",
    )

    first = build_report((beta, alpha))
    second = build_report((alpha, beta))

    assert tuple(row.packet_key for row in first.review_rows) == (
        "review-alpha",
        "review-beta",
    )
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest

    tampered = dict(first.payload)
    tampered["public_status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        research_strategy_manual_review_packet_public_payload(tampered)

    missing_digest = dict(first.payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_manual_review_packet_public_payload(missing_digest)


def test_decimal_only_type_validation_flags_and_frozen_dataclasses() -> None:
    config = ResearchStrategyManualReviewPacketConfig()
    input_packet = packet()
    report = build_report((input_packet,))

    with pytest.raises(FrozenInstanceError):
        input_packet.packet_key = "other"
    with pytest.raises(FrozenInstanceError):
        report.public_status = "watch"
    with pytest.raises(ValueError, match="signal_strength must be a Decimal"):
        packet(signal_strength=1)
    with pytest.raises(ValueError, match="signal_confidence must be a Decimal"):
        packet(signal_confidence=0.5)
    with pytest.raises(ValueError, match="team_capacity_score must be between"):
        packet(team_capacity_score=d("1.000001"))
    with pytest.raises(ValueError, match="hard_flag_count must be a whole Decimal"):
        packet(hard_flag_count=d("1.500000"))
    with pytest.raises(ValueError, match="packet_key has unsafe public content"):
        packet(packet_key="raw-candidate-123")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(input_packet, paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="evidence_gap_watch_threshold must be below"):
        ResearchStrategyManualReviewPacketConfig(
            evidence_gap_watch_threshold=d("0.800000"),
            evidence_gap_block_threshold=d("0.700000"),
        )
    with pytest.raises(ValueError, match="config must be"):
        build_research_strategy_manual_review_packet(
            (input_packet,),
            generated_at=GENERATED_AT,
            config=object(),  # type: ignore[arg-type]
        )
    assert config.paper_only is True


def test_public_payload_rejects_leaky_keys_values_statuses_and_numerics() -> None:
    payload = research_strategy_manual_review_packet_public_payload(
        build_report((packet(),)),
    )

    unsafe_fragments = (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "auth",
    )
    for fragment in unsafe_fragments:
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{fragment}_field"] = "redacted"
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_strategy_manual_review_packet_public_payload(unsafe_key_payload)

        unsafe_value_payload = dict(payload)
        unsafe_value_payload["config_version"] = f"contains-{fragment}"
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_strategy_manual_review_packet_public_payload(unsafe_value_payload)

    numeric_payload = dict(payload)
    numeric_payload["packet_count"] = 1
    with pytest.raises(ValueError, match="Decimal strings"):
        research_strategy_manual_review_packet_public_payload(numeric_payload)

    false_flag_payload = dict(payload)
    false_flag_payload["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        research_strategy_manual_review_packet_public_payload(false_flag_payload)

    status_payload = dict(payload)
    status_payload["public_status"] = "review"
    with pytest.raises(ValueError, match="public_status"):
        research_strategy_manual_review_packet_public_payload(status_payload)


def test_report_consistency_rejects_manual_mismatches() -> None:
    report = build_report(
        (
            packet(packet_key="review-alpha"),
            packet(packet_key="review-watch", evidence_gap_score=d("0.300000")),
        ),
    )

    with pytest.raises(ValueError, match="packet_count"):
        replace(report, packet_count=d("3"))
    with pytest.raises(ValueError, match="public_status"):
        replace(report, public_status="pass")
    with pytest.raises(ValueError, match="highest_evidence_gap_score"):
        replace(report, highest_evidence_gap_score=d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("manual_review_packet_pass",))


def test_public_api_exposes_only_report_only_surfaces() -> None:
    assert MANUAL_REVIEW_PACKET_PUBLIC_STATUSES == ("pass", "watch", "block")
    assert "hard_review_flag" in RESEARCH_STRATEGY_MANUAL_REVIEW_PACKET_REASON_CODES


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, (int, float, Decimal)):
        raise AssertionError(f"public payload contains numeric scalar: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")

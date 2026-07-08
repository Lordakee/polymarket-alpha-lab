from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from typing import Any

import pytest

import polymarket_alpha_lab.research_event_source_consensus_latency_report as module
from polymarket_alpha_lab.research_event_source_consensus_latency_report import (
    ResearchEventSourceConsensusLatencyConfig,
    ResearchEventSourceConsensusLatencyObservation,
    ResearchEventSourceConsensusLatencyReport,
    build_research_event_source_consensus_latency_report,
    research_event_source_consensus_latency_report_payload,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
UNSAFE_TERMS = (
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
    "market",
    "source_id",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    event_label: str,
    source_class_label: str,
    *,
    first_evidence_seen_seconds: Decimal,
    quorum_reached_seconds: Decimal,
    expected_source_class_count: Decimal,
    observed_source_class_count: Decimal,
    stale_corroboration_seconds: Decimal,
    unresolved_disagreement_count: Decimal,
    manual_review_overdue_seconds: Decimal,
) -> ResearchEventSourceConsensusLatencyObservation:
    return ResearchEventSourceConsensusLatencyObservation(
        event_label=event_label,
        source_class_label=source_class_label,
        first_evidence_seen_seconds=first_evidence_seen_seconds,
        quorum_reached_seconds=quorum_reached_seconds,
        expected_source_class_count=expected_source_class_count,
        observed_source_class_count=observed_source_class_count,
        stale_corroboration_seconds=stale_corroboration_seconds,
        unresolved_disagreement_count=unresolved_disagreement_count,
        manual_review_overdue_seconds=manual_review_overdue_seconds,
    )


def sample_observations() -> tuple[ResearchEventSourceConsensusLatencyObservation, ...]:
    return (
        observation(
            "event_beta",
            "specialist",
            first_evidence_seen_seconds=d("100.000000"),
            quorum_reached_seconds=d("1300.000000"),
            expected_source_class_count=d("4.000000"),
            observed_source_class_count=d("3.000000"),
            stale_corroboration_seconds=d("2400.000000"),
            unresolved_disagreement_count=d("1.000000"),
            manual_review_overdue_seconds=d("600.000000"),
        ),
        observation(
            "event_alpha",
            "official",
            first_evidence_seen_seconds=d("100.000000"),
            quorum_reached_seconds=d("400.000000"),
            expected_source_class_count=d("2.000000"),
            observed_source_class_count=d("2.000000"),
            stale_corroboration_seconds=d("300.000000"),
            unresolved_disagreement_count=d("0.000000"),
            manual_review_overdue_seconds=d("0.000000"),
        ),
        observation(
            "event_gamma",
            "aggregate",
            first_evidence_seen_seconds=d("100.000000"),
            quorum_reached_seconds=d("4900.000000"),
            expected_source_class_count=d("4.000000"),
            observed_source_class_count=d("1.000000"),
            stale_corroboration_seconds=d("9000.000000"),
            unresolved_disagreement_count=d("3.000000"),
            manual_review_overdue_seconds=d("2400.000000"),
        ),
    )


def sample_report(
    observations: tuple[ResearchEventSourceConsensusLatencyObservation, ...] | None = None,
) -> ResearchEventSourceConsensusLatencyReport:
    if observations is None:
        observations = sample_observations()
    return build_research_event_source_consensus_latency_report(
        observations,
        generated_at=NOW,
        config=ResearchEventSourceConsensusLatencyConfig(),
    )


def assert_no_float_decimal_datetime_or_identifier_payload_values(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert "source_id" not in key.lower()
            assert_no_float_decimal_datetime_or_identifier_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_decimal_datetime_or_identifier_payload_values(item)
        return
    assert not isinstance(value, (Decimal, float, datetime))


def test_aggregate_consensus_latency_rows_status_and_scores() -> None:
    report = sample_report()

    assert [row.event_label for row in report.rows] == [
        "event_gamma",
        "event_beta",
        "event_alpha",
    ]
    assert [row.consensus_status for row in report.rows] == ["block", "watch", "pass"]
    assert report.consensus_status == "block"
    assert report.observation_count == d("3.000000")
    assert report.event_count == d("3.000000")
    assert report.source_class_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")

    blocked, watched, passed = report.rows
    assert blocked.time_to_quorum_seconds == d("4800.000000")
    assert watched.time_to_quorum_seconds == d("1200.000000")
    assert passed.time_to_quorum_seconds == d("300.000000")
    assert blocked.source_class_coverage_ratio == d("0.250000")
    assert watched.source_class_coverage_ratio == d("0.750000")
    assert passed.stale_corroboration_pressure == d("0.041667")
    assert blocked.unresolved_disagreement_pressure == d("1.000000")
    assert blocked.manual_escalation_urgency_score == d("1.000000")
    assert blocked.consensus_latency_score == d("0.950000")
    assert watched.consensus_latency_score == d("0.316666")
    assert passed.consensus_latency_score == d("0.025000")
    assert "source_class_coverage_block" in blocked.reason_codes
    assert "time_to_quorum_watch" in watched.reason_codes
    assert "consensus_latency_pass" in passed.reason_codes

    assert report.average_time_to_quorum_seconds == d("2100.000000")
    assert report.average_source_class_coverage_ratio == d("0.666667")
    assert report.max_stale_corroboration_pressure == d("1.000000")
    assert report.max_unresolved_disagreement_pressure == d("1.000000")
    assert report.max_manual_escalation_urgency_score == d("1.000000")
    assert report.average_consensus_latency_score == d("0.430555")


def test_payload_is_public_safe_deterministic_and_json_ready() -> None:
    report = sample_report()
    reversed_report = sample_report(tuple(reversed(sample_observations())))

    payload = research_event_source_consensus_latency_report_payload(report)
    reversed_payload = research_event_source_consensus_latency_report_payload(reversed_report)

    assert payload == reversed_payload
    assert json.dumps(payload, sort_keys=True)
    assert payload["config_version"] == "research-event-source-consensus-latency-report"
    assert payload["consensus_status"] == "block"
    assert payload["average_time_to_quorum_seconds"] == "2100.000000"
    assert payload["rows"][0]["consensus_latency_score"] == "0.950000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert "market_slug" not in json.dumps(payload, sort_keys=True).lower()
    assert "source_id" not in json.dumps(payload, sort_keys=True).lower()
    assert_no_float_decimal_datetime_or_identifier_payload_values(payload)
    assert research_event_source_consensus_latency_report_payload(payload) == payload


def test_dataclasses_are_frozen_and_decimal_only() -> None:
    report = sample_report()
    config = ResearchEventSourceConsensusLatencyConfig()
    sample = sample_observations()[0]

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_SOURCE_CONSENSUS_LATENCY_REPORT_CONFIG_VERSION",
        "ResearchEventSourceConsensusLatencyConfig",
        "ResearchEventSourceConsensusLatencyObservation",
        "ResearchEventSourceConsensusLatencyReport",
        "ResearchEventSourceConsensusLatencyRow",
        "build_research_event_source_consensus_latency_report",
        "research_event_source_consensus_latency_report_payload",
    )
    for public_name in module.__all__:
        public_value: Any = getattr(module, public_name)
        if isinstance(public_value, type):
            assert is_dataclass(public_value)

    for instance in (config, sample, report, *report.rows):
        assert is_dataclass(instance)
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert not isinstance(value, float)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].consensus_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        ResearchEventSourceConsensusLatencyObservation(
            event_label="event_bad",
            source_class_label="official",
            first_evidence_seen_seconds=1,  # type: ignore[arg-type]
            quorum_reached_seconds=d("1.000000"),
            expected_source_class_count=d("1.000000"),
            observed_source_class_count=d("1.000000"),
            stale_corroboration_seconds=d("1.000000"),
            unresolved_disagreement_count=d("0.000000"),
            manual_review_overdue_seconds=d("0.000000"),
        )


def test_hard_flags_digest_and_consistency_reject_tampering() -> None:
    report = sample_report()
    payload = research_event_source_consensus_latency_report_payload(report)

    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventSourceConsensusLatencyConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sample_observations()[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="quorum_reached_seconds"):
        observation(
            "event_bad",
            "official",
            first_evidence_seen_seconds=d("10.000000"),
            quorum_reached_seconds=d("9.000000"),
            expected_source_class_count=d("1.000000"),
            observed_source_class_count=d("1.000000"),
            stale_corroboration_seconds=d("1.000000"),
            unresolved_disagreement_count=d("0.000000"),
            manual_review_overdue_seconds=d("0.000000"),
        )
    with pytest.raises(ValueError, match="observed_source_class_count"):
        observation(
            "event_bad",
            "official",
            first_evidence_seen_seconds=d("1.000000"),
            quorum_reached_seconds=d("2.000000"),
            expected_source_class_count=d("1.000000"),
            observed_source_class_count=d("2.000000"),
            stale_corroboration_seconds=d("1.000000"),
            unresolved_disagreement_count=d("0.000000"),
            manual_review_overdue_seconds=d("0.000000"),
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report.rows[0], consensus_latency_score=d("0.123456"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, observation_count=d("4.000000"))

    tampered_payload = dict(payload)
    tampered_payload["watch_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_source_consensus_latency_report_payload(tampered_payload)


def test_unsafe_public_surfaces_and_raw_identifiers_are_rejected() -> None:
    payload = research_event_source_consensus_latency_report_payload(sample_report())

    for unsafe_term in UNSAFE_TERMS:
        with pytest.raises(ValueError, match="unsafe"):
            observation(
                f"{unsafe_term}_event",
                "official",
                first_evidence_seen_seconds=d("1.000000"),
                quorum_reached_seconds=d("2.000000"),
                expected_source_class_count=d("1.000000"),
                observed_source_class_count=d("1.000000"),
                stale_corroboration_seconds=d("1.000000"),
                unresolved_disagreement_count=d("0.000000"),
                manual_review_overdue_seconds=d("0.000000"),
            )

        unsafe_payload = dict(payload)
        unsafe_payload[f"{unsafe_term}_surface"] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            research_event_source_consensus_latency_report_payload(unsafe_payload)

    with pytest.raises(ValueError, match="unsafe"):
        observation(
            "event_url",
            "https://example.test/source",
            first_evidence_seen_seconds=d("1.000000"),
            quorum_reached_seconds=d("2.000000"),
            expected_source_class_count=d("1.000000"),
            observed_source_class_count=d("1.000000"),
            stale_corroboration_seconds=d("1.000000"),
            unresolved_disagreement_count=d("0.000000"),
            manual_review_overdue_seconds=d("0.000000"),
        )


def test_public_exports_and_fields_have_no_unsafe_surface_terms() -> None:
    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert not any(term in lowered_name for term in UNSAFE_TERMS)
        public_value: Any = getattr(module, public_name)
        if isinstance(public_value, type) and is_dataclass(public_value):
            for field in fields(public_value):
                lowered_field = field.name.lower()
                assert not any(term in lowered_field for term in UNSAFE_TERMS)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(module, forbidden_name)

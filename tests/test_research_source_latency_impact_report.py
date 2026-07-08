from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from typing import Any

import pytest

import polymarket_alpha_lab.research_source_latency_impact_report as module
from polymarket_alpha_lab.research_source_latency_impact_report import (
    ResearchSourceLatencyImpactConfig,
    ResearchSourceLatencyImpactObservation,
    ResearchSourceLatencyImpactReport,
    build_research_source_latency_impact_report,
    research_source_latency_impact_report_payload,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
UNSAFE_TERMS = (
    "live",
    "auth",
    "private_key",
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "source_text",
    "raw_text",
    "dsn",
    "table",
    "token",
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


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    decision_label: str,
    source_class_label: str,
    *,
    retrieval_delay_seconds: Decimal,
    evidence_age_seconds: Decimal,
    source_class_expected_count: Decimal,
    source_class_observed_count: Decimal,
    contradiction_lag_seconds: Decimal,
    recheck_overdue_seconds: Decimal,
) -> ResearchSourceLatencyImpactObservation:
    return ResearchSourceLatencyImpactObservation(
        decision_label=decision_label,
        source_class_label=source_class_label,
        retrieval_delay_seconds=retrieval_delay_seconds,
        evidence_age_seconds=evidence_age_seconds,
        source_class_expected_count=source_class_expected_count,
        source_class_observed_count=source_class_observed_count,
        contradiction_lag_seconds=contradiction_lag_seconds,
        recheck_overdue_seconds=recheck_overdue_seconds,
    )


def sample_observations() -> tuple[ResearchSourceLatencyImpactObservation, ...]:
    return (
        observation(
            "decision_beta",
            "specialist",
            retrieval_delay_seconds=d("900.000000"),
            evidence_age_seconds=d("2400.000000"),
            source_class_expected_count=d("4.000000"),
            source_class_observed_count=d("3.000000"),
            contradiction_lag_seconds=d("1000.000000"),
            recheck_overdue_seconds=d("400.000000"),
        ),
        observation(
            "decision_alpha",
            "official",
            retrieval_delay_seconds=d("120.000000"),
            evidence_age_seconds=d("600.000000"),
            source_class_expected_count=d("2.000000"),
            source_class_observed_count=d("2.000000"),
            contradiction_lag_seconds=d("60.000000"),
            recheck_overdue_seconds=d("0.000000"),
        ),
        observation(
            "decision_gamma",
            "aggregate",
            retrieval_delay_seconds=d("2100.000000"),
            evidence_age_seconds=d("9000.000000"),
            source_class_expected_count=d("4.000000"),
            source_class_observed_count=d("1.000000"),
            contradiction_lag_seconds=d("4000.000000"),
            recheck_overdue_seconds=d("2000.000000"),
        ),
    )


def sample_report(
    observations: tuple[ResearchSourceLatencyImpactObservation, ...] | None = None,
) -> ResearchSourceLatencyImpactReport:
    if observations is None:
        observations = sample_observations()
    return build_research_source_latency_impact_report(
        observations,
        generated_at=NOW,
        config=ResearchSourceLatencyImpactConfig(),
    )


def assert_no_float_decimal_or_datetime_payload_values(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_decimal_or_datetime_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_decimal_or_datetime_payload_values(item)
        return
    assert not isinstance(value, (Decimal, float, datetime))


def test_aggregate_latency_impact_rows_status_and_scores() -> None:
    report = sample_report()

    assert [row.decision_label for row in report.rows] == [
        "decision_gamma",
        "decision_beta",
        "decision_alpha",
    ]
    assert [row.impact_status for row in report.rows] == ["block", "watch", "pass"]
    assert report.impact_status == "block"
    assert report.observation_count == d("3.000000")
    assert report.decision_count == d("3.000000")
    assert report.source_class_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")

    blocked, watched, passed = report.rows
    assert blocked.latency_impact_score == d("0.950000")
    assert watched.latency_impact_score == d("0.316667")
    assert passed.latency_impact_score == d("0.033333")
    assert blocked.source_class_coverage_ratio == d("0.250000")
    assert watched.source_class_coverage_ratio == d("0.750000")
    assert passed.stale_evidence_pressure == d("0.083333")
    assert blocked.recheck_urgency_score == d("1.000000")
    assert "source_class_coverage_block" in blocked.reason_codes
    assert "retrieval_delay_watch" in watched.reason_codes
    assert "latency_impact_pass" in passed.reason_codes

    assert report.average_retrieval_delay_seconds == d("1040.000000")
    assert report.average_stale_evidence_pressure == d("0.472222")
    assert report.average_source_class_coverage_ratio == d("0.666667")
    assert report.max_contradiction_lag_seconds == d("4000.000000")
    assert report.max_recheck_urgency_score == d("1.000000")
    assert report.average_latency_impact_score == d("0.433333")


def test_payload_is_public_safe_deterministic_and_json_ready() -> None:
    report = sample_report()
    reversed_report = sample_report(tuple(reversed(sample_observations())))

    payload = research_source_latency_impact_report_payload(report)
    reversed_payload = research_source_latency_impact_report_payload(reversed_report)

    assert payload == reversed_payload
    assert json.dumps(payload, sort_keys=True)
    assert payload["config_version"] == "research-source-latency-impact-report"
    assert payload["impact_status"] == "block"
    assert payload["average_retrieval_delay_seconds"] == "1040.000000"
    assert payload["rows"][0]["latency_impact_score"] == "0.950000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert_no_float_decimal_or_datetime_payload_values(payload)
    assert research_source_latency_impact_report_payload(payload) == payload


def test_dataclasses_are_frozen_and_decimal_only() -> None:
    report = sample_report()
    config = ResearchSourceLatencyImpactConfig()
    sample = sample_observations()[0]

    for instance in (config, sample, report, *report.rows):
        assert is_dataclass(instance)
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert not isinstance(value, float)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].impact_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        ResearchSourceLatencyImpactObservation(
            decision_label="decision_bad",
            source_class_label="official",
            retrieval_delay_seconds=1,  # type: ignore[arg-type]
            evidence_age_seconds=d("1.000000"),
            source_class_expected_count=d("1.000000"),
            source_class_observed_count=d("1.000000"),
            contradiction_lag_seconds=d("0.000000"),
            recheck_overdue_seconds=d("0.000000"),
        )


def test_hard_flags_and_digest_reject_tampering() -> None:
    report = sample_report()
    payload = research_source_latency_impact_report_payload(report)

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceLatencyImpactConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sample_observations()[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report.rows[0], latency_impact_score=d("0.123456"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, observation_count=d("4.000000"))

    tampered_payload = dict(payload)
    tampered_payload["watch_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_latency_impact_report_payload(tampered_payload)


def test_unsafe_public_surfaces_are_rejected() -> None:
    payload = research_source_latency_impact_report_payload(sample_report())

    for unsafe_term in UNSAFE_TERMS:
        with pytest.raises(ValueError, match="unsafe"):
            observation(
                f"{unsafe_term}_decision",
                "official",
                retrieval_delay_seconds=d("1.000000"),
                evidence_age_seconds=d("1.000000"),
                source_class_expected_count=d("1.000000"),
                source_class_observed_count=d("1.000000"),
                contradiction_lag_seconds=d("0.000000"),
                recheck_overdue_seconds=d("0.000000"),
            )

        unsafe_payload = dict(payload)
        unsafe_payload[f"{unsafe_term}_surface"] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            research_source_latency_impact_report_payload(unsafe_payload)

    with pytest.raises(ValueError, match="unsafe"):
        observation(
            "decision_url",
            "https://example.test/path",
            retrieval_delay_seconds=d("1.000000"),
            evidence_age_seconds=d("1.000000"),
            source_class_expected_count=d("1.000000"),
            source_class_observed_count=d("1.000000"),
            contradiction_lag_seconds=d("0.000000"),
            recheck_overdue_seconds=d("0.000000"),
        )
    with pytest.raises(ValueError, match="unsafe"):
        observation(
            "decision_domain",
            "example.test",
            retrieval_delay_seconds=d("1.000000"),
            evidence_age_seconds=d("1.000000"),
            source_class_expected_count=d("1.000000"),
            source_class_observed_count=d("1.000000"),
            contradiction_lag_seconds=d("0.000000"),
            recheck_overdue_seconds=d("0.000000"),
        )
    with pytest.raises(ValueError, match="unsafe"):
        observation(
            "0x1234567890abcdef",
            "official",
            retrieval_delay_seconds=d("1.000000"),
            evidence_age_seconds=d("1.000000"),
            source_class_expected_count=d("1.000000"),
            source_class_observed_count=d("1.000000"),
            contradiction_lag_seconds=d("0.000000"),
            recheck_overdue_seconds=d("0.000000"),
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

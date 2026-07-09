from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any

import pytest

import polymarket_alpha_lab.research_event_source_latency_conflict_quorum_report as module
from polymarket_alpha_lab.research_event_source_latency_conflict_quorum_report import (
    ResearchEventSourceLatencyConflictQuorumConfig,
    ResearchEventSourceLatencyConflictQuorumObservation,
    ResearchEventSourceLatencyConflictQuorumReport,
    build_research_event_source_latency_conflict_quorum_report,
    research_event_source_latency_conflict_quorum_report_payload,
)


NOW = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
UNSAFE_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "auth",
    "network",
    "database",
    "sizing",
    "recommendation",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def observation(
    event_digest: str,
    evidence_group_digest: str,
    *,
    first_signal_seen_seconds: Decimal,
    quorum_confirmed_seconds: Decimal,
    supporting_evidence_count: Decimal,
    conflicting_evidence_count: Decimal,
) -> ResearchEventSourceLatencyConflictQuorumObservation:
    return ResearchEventSourceLatencyConflictQuorumObservation(
        event_digest=event_digest,
        evidence_group_digest=evidence_group_digest,
        first_signal_seen_seconds=first_signal_seen_seconds,
        quorum_confirmed_seconds=quorum_confirmed_seconds,
        supporting_evidence_count=supporting_evidence_count,
        conflicting_evidence_count=conflicting_evidence_count,
    )


def sample_observations() -> tuple[ResearchEventSourceLatencyConflictQuorumObservation, ...]:
    return (
        observation(
            digest("event_beta"),
            digest("specialist_group"),
            first_signal_seen_seconds=d("100.000000"),
            quorum_confirmed_seconds=d("1300.000000"),
            supporting_evidence_count=d("2.000000"),
            conflicting_evidence_count=d("1.000000"),
        ),
        observation(
            digest("event_alpha"),
            digest("official_group"),
            first_signal_seen_seconds=d("100.000000"),
            quorum_confirmed_seconds=d("400.000000"),
            supporting_evidence_count=d("3.000000"),
            conflicting_evidence_count=d("0.000000"),
        ),
        observation(
            digest("event_gamma"),
            digest("aggregate_group"),
            first_signal_seen_seconds=d("100.000000"),
            quorum_confirmed_seconds=d("4900.000000"),
            supporting_evidence_count=d("1.000000"),
            conflicting_evidence_count=d("3.000000"),
        ),
    )


def sample_report(
    observations: tuple[ResearchEventSourceLatencyConflictQuorumObservation, ...] | None = None,
) -> ResearchEventSourceLatencyConflictQuorumReport:
    if observations is None:
        observations = sample_observations()
    return build_research_event_source_latency_conflict_quorum_report(
        observations,
        generated_at=NOW,
        config=ResearchEventSourceLatencyConflictQuorumConfig(),
    )


def assert_json_ready_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            lowered = key.lower()
            assert "source_url" not in lowered
            assert "source_text" not in lowered
            assert "source_id" not in lowered
            assert "market_id" not in lowered
            assert "market_slug" not in lowered
            assert_json_ready_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_json_ready_public_payload(item)
        return
    assert not isinstance(value, (Decimal, float, datetime))


def test_latency_conflict_quorum_rows_statuses_and_scores() -> None:
    report = sample_report()

    assert [row.status for row in report.rows] == ["block", "watch", "pass"]
    assert report.status == "block"
    assert report.observation_count == d("3.000000")
    assert report.event_count == d("3.000000")
    assert report.evidence_group_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")

    blocked, watched, passed = report.rows
    assert blocked.latency_seconds == d("4800.000000")
    assert watched.latency_seconds == d("1200.000000")
    assert passed.latency_seconds == d("300.000000")
    assert blocked.latency_pressure == d("1.000000")
    assert blocked.quorum_ratio == d("0.333333")
    assert blocked.quorum_gap_pressure == d("0.666667")
    assert blocked.conflict_ratio == d("0.750000")
    assert blocked.latency_conflict_quorum_score == d("0.800000")
    assert watched.latency_conflict_quorum_score == d("0.333333")
    assert passed.latency_conflict_quorum_score == d("0.025000")
    assert "latency_block" in blocked.reason_codes
    assert "quorum_gap_watch" in watched.reason_codes
    assert "latency_conflict_quorum_pass" in passed.reason_codes

    assert report.average_latency_seconds == d("2100.000000")
    assert report.average_quorum_ratio == d("0.666667")
    assert report.max_latency_pressure == d("1.000000")
    assert report.max_quorum_gap_pressure == d("0.666667")
    assert report.max_conflict_ratio == d("0.750000")
    assert report.average_latency_conflict_quorum_score == d("0.386111")


def test_payload_is_deterministic_public_safe_json_ready_and_digest_checked() -> None:
    report = sample_report()
    reversed_report = sample_report(tuple(reversed(sample_observations())))

    payload = research_event_source_latency_conflict_quorum_report_payload(report)
    reversed_payload = research_event_source_latency_conflict_quorum_report_payload(
        reversed_report,
    )

    assert payload == reversed_payload
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["config_version"] == "research-event-source-latency-conflict-quorum-report"
    assert payload["status"] == "block"
    assert payload["average_latency_seconds"] == "2100.000000"
    assert payload["rows"][0]["latency_conflict_quorum_score"] == "0.800000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    rendered = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden not in rendered
    assert_json_ready_public_payload(payload)
    assert research_event_source_latency_conflict_quorum_report_payload(payload) == payload


def test_public_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    report = sample_report()
    config = ResearchEventSourceLatencyConflictQuorumConfig()
    sample = sample_observations()[0]

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_SOURCE_LATENCY_CONFLICT_QUORUM_CONFIG_VERSION",
        "ResearchEventSourceLatencyConflictQuorumConfig",
        "ResearchEventSourceLatencyConflictQuorumObservation",
        "ResearchEventSourceLatencyConflictQuorumReport",
        "ResearchEventSourceLatencyConflictQuorumRow",
        "build_research_event_source_latency_conflict_quorum_report",
        "research_event_source_latency_conflict_quorum_report_payload",
    )
    for public_name in module.__all__:
        public_value: Any = getattr(module, public_name)
        if isinstance(public_value, type):
            assert is_dataclass(public_value)

    for instance in (config, sample, report, *report.rows):
        assert is_dataclass(instance)
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert not isinstance(value, float)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        ResearchEventSourceLatencyConflictQuorumObservation(
            event_digest=digest("bad_event"),
            evidence_group_digest=digest("bad_group"),
            first_signal_seen_seconds=1,  # type: ignore[arg-type]
            quorum_confirmed_seconds=d("1.000000"),
            supporting_evidence_count=d("1.000000"),
            conflicting_evidence_count=d("0.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventSourceLatencyConflictQuorumConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sample, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_validation_rejects_inconsistent_rows_reports_and_payload_tampering() -> None:
    report = sample_report()
    payload = research_event_source_latency_conflict_quorum_report_payload(report)

    with pytest.raises(ValueError, match="quorum_confirmed_seconds"):
        observation(
            digest("bad_event"),
            digest("bad_group"),
            first_signal_seen_seconds=d("10.000000"),
            quorum_confirmed_seconds=d("9.000000"),
            supporting_evidence_count=d("1.000000"),
            conflicting_evidence_count=d("0.000000"),
        )
    with pytest.raises(ValueError, match="evidence count"):
        observation(
            digest("bad_event"),
            digest("bad_group"),
            first_signal_seen_seconds=d("1.000000"),
            quorum_confirmed_seconds=d("2.000000"),
            supporting_evidence_count=d("0.000000"),
            conflicting_evidence_count=d("0.000000"),
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report.rows[0], latency_conflict_quorum_score=d("0.123456"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, observation_count=d("4.000000"))

    tampered_payload = dict(payload)
    tampered_payload["watch_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_source_latency_conflict_quorum_report_payload(tampered_payload)


def test_unsafe_public_surfaces_and_raw_identifiers_are_rejected() -> None:
    payload = research_event_source_latency_conflict_quorum_report_payload(sample_report())

    for unsafe_term in UNSAFE_TERMS:
        unsafe_payload = dict(payload)
        unsafe_payload[f"{unsafe_term}_surface"] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            research_event_source_latency_conflict_quorum_report_payload(unsafe_payload)

        with pytest.raises(ValueError, match="sha256|unsafe"):
            observation(
                f"{unsafe_term}_raw_identifier",
                digest("safe_group"),
                first_signal_seen_seconds=d("1.000000"),
                quorum_confirmed_seconds=d("2.000000"),
                supporting_evidence_count=d("1.000000"),
                conflicting_evidence_count=d("0.000000"),
            )

    with pytest.raises(ValueError, match="unsafe"):
        research_event_source_latency_conflict_quorum_report_payload(
            {
                **payload,
                "rows": [
                    {
                        **payload["rows"][0],
                        "evidence_group_digest": "https://example.test/raw-source",
                    },
                    *payload["rows"][1:],
                ],
            },
        )


def test_module_scope_has_no_io_execution_or_action_surface() -> None:
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

    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert "wallet" not in lowered_name
        assert "order" not in lowered_name
        assert "trade" not in lowered_name
        public_value: Any = getattr(module, public_name)
        if isinstance(public_value, type) and is_dataclass(public_value):
            for field in fields(public_value):
                lowered_field = field.name.lower()
                for forbidden in (
                    "candidate",
                    "market",
                    "slug",
                    "question",
                    "source_url",
                    "source_text",
                    "dsn",
                    "table",
                    "token",
                    "wallet",
                    "order",
                    "trade",
                    "sizing",
                    "recommendation",
                ):
                    assert forbidden not in lowered_field

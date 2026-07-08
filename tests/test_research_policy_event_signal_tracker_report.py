from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_policy_event_signal_tracker_report import (
    ResearchPolicyEventSignalTrackerConfig,
    ResearchPolicyEventSignalTrackerEvidence,
    ResearchPolicyEventSignalTrackerReasonCodeCount,
    ResearchPolicyEventSignalTrackerReport,
    ResearchPolicyEventSignalTrackerRow,
    build_research_policy_event_signal_tracker_report,
    research_policy_event_signal_tracker_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchPolicyEventSignalTrackerConfig:
    values = {
        "config_version": "research-policy-event-signal-tracker-report-v0",
        "fresh_age_seconds": d("86400"),
        "stale_age_seconds": d("604800"),
        "min_independent_source_family_count": d("2"),
        "min_milestone_node_count": d("1"),
        "block_counter_evidence_count": d("2"),
        "pass_signal_score": d("0.750000"),
        "watch_signal_score": d("0.400000"),
        "official_schedule_weight": d("0.300000"),
        "milestone_node_weight": d("0.250000"),
        "source_independence_weight": d("0.250000"),
        "recency_weight": d("0.200000"),
        "counter_evidence_penalty": d("0.350000"),
        "settlement_ambiguity_penalty": d("0.500000"),
    }
    values.update(overrides)
    return ResearchPolicyEventSignalTrackerConfig(**values)


def evidence(
    index: int,
    *,
    signal_id: str = "policy-signal-alpha",
    source_family: str = "official",
    source_type: str = "official",
    node_type: str = "official_schedule",
    evidence_stance: str = "supporting",
    settlement_clarity: str = "clear",
    observed_at: datetime | None = None,
) -> ResearchPolicyEventSignalTrackerEvidence:
    return ResearchPolicyEventSignalTrackerEvidence(
        signal_id=signal_id,
        evidence_id=f"evidence-{index:03d}",
        source_id=f"source-{index:03d}",
        source_family=source_family,
        source_type=source_type,
        node_type=node_type,
        evidence_stance=evidence_stance,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(hours=2)
        ),
        scheduled_event_at=GENERATED_AT + timedelta(days=3),
        settlement_clarity=settlement_clarity,
    )


def report(
    rows: tuple[ResearchPolicyEventSignalTrackerEvidence, ...],
    *,
    cfg: ResearchPolicyEventSignalTrackerConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchPolicyEventSignalTrackerReport:
    return build_research_policy_event_signal_tracker_report(
        rows,
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_empty_input_returns_block_report_only_snapshot() -> None:
    signal_report = report(())

    assert type(signal_report) is ResearchPolicyEventSignalTrackerReport
    assert signal_report.generated_at == GENERATED_AT
    assert signal_report.signal_count == d("0")
    assert signal_report.evidence_count == d("0")
    assert signal_report.pass_count == d("0")
    assert signal_report.watch_count == d("0")
    assert signal_report.block_count == d("0")
    assert signal_report.average_signal_score == d("0.000000")
    assert signal_report.status == "block"
    assert signal_report.rows == ()
    assert signal_report.reason_codes == ("empty_evidence",)
    assert signal_report.reason_code_counts == (
        ResearchPolicyEventSignalTrackerReasonCodeCount(
            reason_code="empty_evidence",
            count=d("1"),
        ),
    )
    assert signal_report.paper_only is True
    assert signal_report.report_only is True
    assert signal_report.readonly is True


def test_official_schedule_milestones_independent_sources_pass() -> None:
    signal_report = report(
        (
            evidence(3, source_family="regulator", source_type="primary", node_type="regulatory"),
            evidence(1, source_family="official", source_type="official"),
            evidence(4, source_family="court", source_type="primary", node_type="court"),
            evidence(2, source_family="legislature", source_type="primary", node_type="vote"),
        ),
    )

    assert signal_report.status == "pass"
    assert signal_report.signal_count == d("1")
    assert signal_report.evidence_count == d("4")
    assert signal_report.pass_count == d("1")
    assert signal_report.watch_count == d("0")
    assert signal_report.block_count == d("0")
    assert signal_report.average_signal_score == d("1.000000")
    assert signal_report.reason_codes == ("policy_event_signal_pass",)

    row = signal_report.rows[0]
    assert type(row) is ResearchPolicyEventSignalTrackerRow
    assert row.signal_id == "policy-signal-alpha"
    assert row.evidence_count == d("4")
    assert row.source_count == d("4")
    assert row.source_family_count == d("4")
    assert row.official_schedule_count == d("1")
    assert row.milestone_node_count == d("3")
    assert row.vote_node_count == d("1")
    assert row.court_node_count == d("1")
    assert row.regulatory_node_count == d("1")
    assert row.counter_evidence_count == d("0")
    assert row.settlement_ambiguity_count == d("0")
    assert row.latest_source_age_seconds == d("7200.000000")
    assert row.recency_score == d("1.000000")
    assert row.official_schedule_score == d("1.000000")
    assert row.milestone_node_score == d("1.000000")
    assert row.source_independence_score == d("1.000000")
    assert row.signal_score == d("1.000000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "official_schedule_present",
        "vote_court_regulatory_node_present",
        "source_independence_met",
        "fresh_source_context",
        "no_counter_evidence",
        "settlement_terms_clear",
        "policy_event_signal_pass",
    )


def test_missing_milestone_and_independence_returns_watch() -> None:
    signal_report = report((evidence(1),))
    row = signal_report.rows[0]

    assert signal_report.status == "watch"
    assert signal_report.watch_count == d("1")
    assert signal_report.average_signal_score == d("0.625000")
    assert row.status == "watch"
    assert row.reason_codes == (
        "official_schedule_present",
        "missing_vote_court_regulatory_node",
        "insufficient_source_independence",
        "fresh_source_context",
        "no_counter_evidence",
        "settlement_terms_clear",
        "policy_event_signal_watch",
    )


def test_counter_evidence_and_settlement_ambiguity_block_signal() -> None:
    signal_report = report(
        (
            evidence(1, source_family="official", source_type="official"),
            evidence(2, source_family="legislature", source_type="primary", node_type="vote"),
            evidence(
                3,
                source_family="court",
                source_type="primary",
                node_type="court",
                evidence_stance="counter",
            ),
            evidence(
                4,
                source_family="regulator",
                source_type="primary",
                node_type="regulatory",
                evidence_stance="counter",
                settlement_clarity="ambiguous",
            ),
        ),
    )
    row = signal_report.rows[0]

    assert signal_report.status == "block"
    assert signal_report.block_count == d("1")
    assert row.counter_evidence_count == d("2")
    assert row.settlement_ambiguity_count == d("1")
    assert row.counter_evidence_penalty_score == d("0.700000")
    assert row.settlement_ambiguity_penalty_score == d("0.500000")
    assert row.signal_score == d("0.000000")
    assert row.status == "block"
    assert "counter_evidence_present" in row.reason_codes
    assert "settlement_ambiguity_present" in row.reason_codes
    assert "policy_event_signal_block" in row.reason_codes


def test_payload_serializes_decimals_as_strings_and_excludes_unsafe_material() -> None:
    signal_report = report(
        (
            evidence(2, source_family="legislature", source_type="primary", node_type="vote"),
            evidence(1),
        ),
    )

    payload = research_policy_event_signal_tracker_report_payload(signal_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["source_count"] == "2.000000"
    assert payload["rows"][0]["signal_score"] == str(signal_report.rows[0].signal_score)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert "source_url" not in encoded.lower()
    assert "source_text" not in encoded.lower()
    assert "raw_market_question" not in encoded.lower()
    assert "dsn" not in encoded.lower()
    assert "table" not in encoded.lower()
    assert "token" not in encoded.lower()


def test_validation_rejects_bad_types_unsafe_text_future_times_and_flags() -> None:
    with pytest.raises(ValueError, match="pass_signal_score"):
        config(pass_signal_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="counter_evidence_penalty"):
        config(counter_evidence_penalty=_DecimalSubclass("0.350000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="signal_id"):
        evidence(1, signal_id="Will this bill pass?")
    with pytest.raises(ValueError, match="source_id"):
        replace(evidence(1), source_id="https://official.example/calendar")
    with pytest.raises(ValueError, match="source_id"):
        replace(evidence(1), source_id="secret-token")
    with pytest.raises(ValueError, match="source_type"):
        evidence(1, source_type="blog")
    with pytest.raises(ValueError, match="node_type"):
        evidence(1, node_type="press")
    with pytest.raises(ValueError, match="evidence_stance"):
        evidence(1, evidence_stance="rumor")
    with pytest.raises(ValueError, match="settlement_clarity"):
        evidence(1, settlement_clarity="unclear")
    with pytest.raises(ValueError, match="observed_at"):
        evidence(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        evidence(1, observed_at=_DatetimeSubclass(2026, 7, 6, 10, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="after generated_at"):
        report((evidence(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_values_validate_consistency() -> None:
    signal_report = report((evidence(1),))

    with pytest.raises(FrozenInstanceError):
        signal_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        signal_report.rows[0].signal_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="row status"):
        replace(signal_report.rows[0], status="pass")
    with pytest.raises(ValueError, match="status"):
        replace(signal_report, status="pass")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(signal_report, derived_validation_digest="0" * 64)


def test_owned_module_has_no_filesystem_execution_or_trade_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_policy_event_signal_tracker_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "insert ",
        "update ",
        "delete ",
        "buy",
        "sell",
        "trade",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)

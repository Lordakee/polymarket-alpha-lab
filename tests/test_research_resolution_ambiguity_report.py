from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_ambiguity_report import (
    ResearchResolutionAmbiguityConfig,
    ResearchResolutionAmbiguityEvidence,
    ResearchResolutionAmbiguityReasonCodeCount,
    ResearchResolutionAmbiguityReport,
    ResearchResolutionAmbiguityRow,
    build_research_resolution_ambiguity_report,
    research_resolution_ambiguity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionAmbiguityConfig:
    values = {
        "config_version": "research-resolution-ambiguity-v0",
        "near_resolution_window_minutes": d("120.000000"),
        "pass_max_risk_score": d("0.250000"),
        "watch_max_risk_score": d("0.550000"),
        "rule_ambiguity_weight": d("0.350000"),
        "adjudication_dependency_weight": d("0.250000"),
        "evidence_conflict_weight": d("0.250000"),
        "near_resolution_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchResolutionAmbiguityConfig(**values)


def evidence(
    index: int,
    *,
    event_ref: str = "event-alpha",
    settlement_rule_clarity: Decimal = d("0.900000"),
    adjudication_dependency: Decimal = d("0.100000"),
    evidence_conflict: Decimal = d("0.000000"),
    observed_at: datetime | None = None,
    resolution_at: datetime | None = None,
    evidence_kind: str = "official_rules",
    market_question: str | None = None,
    market_slug: str | None = None,
    market_id: str | None = None,
    source_url: str | None = None,
    source_text: str | None = None,
) -> ResearchResolutionAmbiguityEvidence:
    return ResearchResolutionAmbiguityEvidence(
        event_ref=event_ref,
        evidence_ref=f"evidence-{index:03d}",
        evidence_kind=evidence_kind,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        resolution_at=resolution_at or GENERATED_AT + timedelta(days=1),
        settlement_rule_clarity=settlement_rule_clarity,
        adjudication_dependency=adjudication_dependency,
        evidence_conflict=evidence_conflict,
        market_question=market_question,
        market_slug=market_slug,
        market_id=market_id,
        source_url=source_url,
        source_text=source_text,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchResolutionAmbiguityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionAmbiguityReport:
    return build_research_resolution_ambiguity_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_clear_rules_low_adjudication_and_low_conflict_pass() -> None:
    ambiguity_report = report(
        (
            evidence(2, settlement_rule_clarity=d("0.800000"), adjudication_dependency=d("0.200000")),
            evidence(1, settlement_rule_clarity=d("0.900000"), adjudication_dependency=d("0.100000")),
        ),
    )

    assert type(ambiguity_report) is ResearchResolutionAmbiguityReport
    assert ambiguity_report.status == "pass"
    assert ambiguity_report.event_count == d("1")
    assert ambiguity_report.evidence_count == d("2")
    assert ambiguity_report.pass_count == d("1")
    assert ambiguity_report.watch_count == d("0")
    assert ambiguity_report.blocked_count == d("0")
    assert ambiguity_report.average_risk_score == d("0.102500")
    assert ambiguity_report.reason_codes == ("resolution_ambiguity_pass",)

    row = ambiguity_report.rows[0]
    assert type(row) is ResearchResolutionAmbiguityRow
    assert row.event_ref == "event-alpha"
    assert row.evidence_count == d("2")
    assert row.minutes_to_resolution == d("1440.000000")
    assert row.rule_ambiguity_score == d("0.150000")
    assert row.adjudication_dependency_score == d("0.200000")
    assert row.evidence_conflict_score == d("0.000000")
    assert row.near_resolution_score == d("0.000000")
    assert row.resolution_risk_score == d("0.102500")
    assert row.status == "pass"
    assert row.evidence_refs == ("evidence-001", "evidence-002")
    assert row.evidence_kinds == ("official_rules",)
    assert row.reason_codes == (
        "adjudication_dependency_low",
        "evidence_conflict_low",
        "outside_near_resolution_window",
        "resolution_ambiguity_pass",
        "settlement_rules_clear",
    )


def test_ambiguity_adjudication_conflict_and_near_resolution_block() -> None:
    ambiguity_report = report(
        (
            evidence(
                1,
                event_ref="event-risk",
                settlement_rule_clarity=d("0.200000"),
                adjudication_dependency=d("0.900000"),
                evidence_conflict=d("0.800000"),
                resolution_at=GENERATED_AT + timedelta(minutes=30),
            ),
        ),
    )

    row = ambiguity_report.rows[0]
    assert ambiguity_report.status == "blocked"
    assert ambiguity_report.blocked_count == d("1")
    assert ambiguity_report.average_risk_score == d("0.817500")
    assert row.event_ref == "event-risk"
    assert row.minutes_to_resolution == d("30.000000")
    assert row.rule_ambiguity_score == d("0.800000")
    assert row.adjudication_dependency_score == d("0.900000")
    assert row.evidence_conflict_score == d("0.800000")
    assert row.near_resolution_score == d("0.750000")
    assert row.resolution_risk_score == d("0.817500")
    assert row.status == "blocked"
    assert row.reason_codes == (
        "adjudication_dependency_high",
        "evidence_conflict_high",
        "near_resolution_window",
        "resolution_ambiguity_blocked",
        "settlement_rules_opaque",
    )


def test_rows_reason_counts_and_payload_are_deterministic_and_sanitized() -> None:
    ambiguity_report = report(
        (
            evidence(
                3,
                event_ref="z-event",
                settlement_rule_clarity=d("0.500000"),
                adjudication_dependency=d("0.500000"),
                evidence_conflict=d("0.300000"),
                resolution_at=GENERATED_AT + timedelta(minutes=60),
                market_question="Will this leaked question resolve yes?",
                market_slug="leaked-market-slug",
                market_id="market-123",
                source_url="https://example.invalid/leaked-source",
                source_text="leaked source text should stay private",
            ),
            evidence(1, event_ref="a-event"),
            evidence(2, event_ref="z-event", settlement_rule_clarity=d("0.700000")),
        ),
    )

    payload = research_resolution_ambiguity_report_payload(ambiguity_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.event_ref for row in ambiguity_report.rows) == ("a-event", "z-event")
    assert tuple(row.row_number for row in ambiguity_report.rows) == (d("1"), d("2"))
    assert ambiguity_report.reason_code_counts == (
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code="adjudication_dependency_low",
            count=d("1"),
        ),
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code="adjudication_dependency_watch",
            count=d("1"),
        ),
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code="evidence_conflict_low",
            count=d("1"),
        ),
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code="evidence_conflict_watch",
            count=d("1"),
        ),
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code="near_resolution_window",
            count=d("1"),
        ),
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code="outside_near_resolution_window",
            count=d("1"),
        ),
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code="resolution_ambiguity_pass",
            count=d("1"),
        ),
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code="resolution_ambiguity_watch",
            count=d("1"),
        ),
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code="settlement_rules_clear",
            count=d("1"),
        ),
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code="settlement_rules_watch",
            count=d("1"),
        ),
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["row_number"] == "1"
    assert payload["rows"][1]["resolution_risk_score"] == str(
        ambiguity_report.rows[1].resolution_risk_score,
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    for sensitive_value in (
        "Will this leaked question resolve yes?",
        "leaked-market-slug",
        "market-123",
        "https://example.invalid/leaked-source",
        "leaked source text should stay private",
        "a-event",
        "z-event",
        "evidence-001",
    ):
        assert sensitive_value not in encoded
    for sensitive_key in (
        "event_ref",
        "evidence_refs",
        "market_question",
        "market_slug",
        "market_id",
        "source_url",
        "source_text",
    ):
        assert sensitive_key not in encoded


def test_validation_rejects_bad_types_unknown_enums_future_times_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="rule_ambiguity_weight"):
        config(rule_ambiguity_weight=d("0.340000"))
    with pytest.raises(ValueError, match="pass_max_risk_score"):
        config(pass_max_risk_score=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_max_risk_score"):
        config(watch_max_risk_score=_DecimalSubclass("0.550000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="event_ref"):
        evidence(1, event_ref=" event-alpha")
    with pytest.raises(ValueError, match="evidence_kind"):
        evidence(1, evidence_kind="social_media")
    with pytest.raises(ValueError, match="settlement_rule_clarity"):
        evidence(1, settlement_rule_clarity=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        evidence(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((evidence(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="resolution_at"):
        report((evidence(1, resolution_at=GENERATED_AT - timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    ambiguity_report = report((evidence(1),))

    with pytest.raises(FrozenInstanceError):
        ambiguity_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ambiguity_report.rows[0].resolution_risk_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="resolution_risk_score"):
        replace(ambiguity_report.rows[0], resolution_risk_score=d("0.200000"))
    with pytest.raises(ValueError, match="status"):
        replace(ambiguity_report, status="blocked")


def test_owned_module_has_no_network_trading_filesystem_or_db_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_ambiguity_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "connect(",
        "open(",
        "create_order",
        "cancel_order",
        "post(",
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

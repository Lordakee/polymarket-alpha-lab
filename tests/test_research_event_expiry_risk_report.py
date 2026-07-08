from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_event_expiry_risk_report as expiry_risk_report_module
from polymarket_alpha_lab.research_event_expiry_risk_report import (
    ResearchEventExpiryRiskConfig,
    ResearchEventExpiryRiskInputRow,
    ResearchEventExpiryRiskReasonCodeCount,
    ResearchEventExpiryRiskReport,
    ResearchEventExpiryRiskRow,
    build_research_event_expiry_risk_report,
    research_event_expiry_risk_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
_DEFAULT_SETTLEMENT_EVIDENCE_AT = object()


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventExpiryRiskConfig:
    values = {
        "config_version": "research-event-expiry-risk-report-v0",
        "expiry_watch_window_seconds": d("86400"),
        "expiry_block_window_seconds": d("3600"),
        "fresh_information_max_age_seconds": d("1800"),
        "stale_information_block_age_seconds": d("7200"),
        "settlement_evidence_stale_age_seconds": d("14400"),
        "min_settlement_evidence_count": d("2"),
        "min_settlement_evidence_family_count": d("2"),
        "liquidity_pass_threshold": d("0.500000"),
        "liquidity_block_threshold": d("0.200000"),
        "rule_ambiguity_watch_threshold": d("0.250000"),
        "rule_ambiguity_block_threshold": d("0.600000"),
    }
    values.update(overrides)
    return ResearchEventExpiryRiskConfig(**values)


def input_row(
    index: int,
    *,
    research_key: str | None = None,
    condition_id: str | None = None,
    event_slug: str | None = None,
    event_expiry_at: datetime | None = None,
    settlement_expected_at: datetime | None = None,
    latest_information_observed_at: datetime | None = None,
    latest_settlement_evidence_at: datetime | None | object = _DEFAULT_SETTLEMENT_EVIDENCE_AT,
    settlement_evidence_count: Decimal = d("2"),
    settlement_evidence_family_count: Decimal = d("2"),
    liquidity_score: Decimal = d("0.750000"),
    rule_ambiguity_score: Decimal = d("0.050000"),
    public_resolution_reference: str | None = "https://example.test/resolution-note",
) -> ResearchEventExpiryRiskInputRow:
    return ResearchEventExpiryRiskInputRow(
        research_key=research_key or f"research-{index:03d}",
        condition_id=condition_id or f"condition-{index:03d}",
        event_slug=event_slug or f"event-{index:03d}",
        event_expiry_at=event_expiry_at or GENERATED_AT + timedelta(days=3),
        settlement_expected_at=settlement_expected_at,
        latest_information_observed_at=(
            latest_information_observed_at
            or GENERATED_AT - timedelta(minutes=15)
        ),
        latest_settlement_evidence_at=(
            GENERATED_AT - timedelta(minutes=20)
            if latest_settlement_evidence_at is _DEFAULT_SETTLEMENT_EVIDENCE_AT
            else latest_settlement_evidence_at
        ),
        settlement_evidence_count=settlement_evidence_count,
        settlement_evidence_family_count=settlement_evidence_family_count,
        liquidity_score=liquidity_score,
        rule_ambiguity_score=rule_ambiguity_score,
        public_resolution_reference=public_resolution_reference,
    )


def report(
    rows: tuple[ResearchEventExpiryRiskInputRow, ...],
    *,
    cfg: ResearchEventExpiryRiskConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventExpiryRiskReport:
    return build_research_event_expiry_risk_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_with_zero_counts() -> None:
    expiry_report = report(())

    assert type(expiry_report) is ResearchEventExpiryRiskReport
    assert expiry_report.generated_at == GENERATED_AT
    assert expiry_report.config_version == "research-event-expiry-risk-report-v0"
    assert expiry_report.status == "block"
    assert expiry_report.event_count == d("0")
    assert expiry_report.pass_count == d("0")
    assert expiry_report.watch_count == d("0")
    assert expiry_report.block_count == d("0")
    assert expiry_report.min_seconds_to_expiry == d("0")
    assert expiry_report.average_information_age_seconds == d("0")
    assert expiry_report.average_liquidity_score == d("0")
    assert expiry_report.max_rule_ambiguity_score == d("0")
    assert expiry_report.reason_codes == ("no_expiry_events",)
    assert expiry_report.reason_code_counts == (
        ResearchEventExpiryRiskReasonCodeCount(
            reason_code="no_expiry_events",
            count=d("1"),
            event_ratio=d("1.000000"),
        ),
    )
    assert expiry_report.rows == ()
    assert expiry_report.paper_only is True
    assert expiry_report.report_only is True
    assert expiry_report.readonly is True


def test_clear_event_passes_with_deterministic_metrics_and_safe_payload() -> None:
    expiry_report = report((input_row(1),))
    payload = research_event_expiry_risk_report_payload(expiry_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert expiry_report.status == "pass"
    assert expiry_report.event_count == d("1")
    assert expiry_report.pass_count == d("1")
    assert expiry_report.watch_count == d("0")
    assert expiry_report.block_count == d("0")
    assert expiry_report.min_seconds_to_expiry == d("259200")
    assert expiry_report.average_information_age_seconds == d("900")
    assert expiry_report.average_liquidity_score == d("0.750000")
    assert expiry_report.max_rule_ambiguity_score == d("0.050000")

    row = expiry_report.rows[0]
    assert type(row) is ResearchEventExpiryRiskRow
    assert row.research_key == "research-001"
    assert row.seconds_to_expiry == d("259200")
    assert row.information_age_seconds == d("900")
    assert row.settlement_evidence_age_seconds == d("1200")
    assert row.settlement_evidence_count == d("2")
    assert row.settlement_evidence_family_count == d("2")
    assert row.liquidity_score == d("0.750000")
    assert row.rule_ambiguity_score == d("0.050000")
    assert row.expiry_risk_status == "pass"
    assert row.redacted_resolution_reference == "reference_provided"
    assert row.reason_codes == (
        "expiry_risk_pass",
        "expiry_window_clear",
        "information_refresh_current",
        "liquidity_clear",
        "rules_clear",
        "settlement_evidence_current",
        "settlement_evidence_sufficient",
    )

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["seconds_to_expiry"] == "259200"
    assert payload["rows"][0]["redacted_resolution_reference"] == "reference_provided"
    assert "https://example.test/resolution-note" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded


def test_public_payload_omits_raw_market_and_candidate_identifiers() -> None:
    raw_research_key = "raw-research-key-123"
    raw_condition_id = "raw-condition-id-456"
    raw_event_slug = "raw-event-slug-789"
    expiry_report = report(
        (
            input_row(
                1,
                research_key=raw_research_key,
                condition_id=raw_condition_id,
                event_slug=raw_event_slug,
            ),
        ),
    )
    payload = research_event_expiry_risk_report_payload(expiry_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert "research_key" not in encoded
    assert "condition_id" not in encoded
    assert "event_slug" not in encoded
    for raw_identifier in (raw_research_key, raw_condition_id, raw_event_slug):
        assert raw_identifier not in encoded


def test_payload_rejects_raw_market_and_candidate_identifier_fields() -> None:
    for field_name in ("research_key", "condition_id", "event_slug"):
        with pytest.raises(ValueError, match=field_name):
            expiry_risk_report_module._reject_unsafe_payload(
                "payload",
                {"rows": [{field_name: "raw-identifier"}]},
            )


def test_near_expiry_stale_thin_low_liquidity_and_ambiguous_rules_block() -> None:
    expiry_report = report(
        (
            input_row(
                1,
                event_expiry_at=GENERATED_AT + timedelta(minutes=30),
                latest_information_observed_at=GENERATED_AT - timedelta(hours=3),
                latest_settlement_evidence_at=None,
                settlement_evidence_count=d("0"),
                settlement_evidence_family_count=d("0"),
                liquidity_score=d("0.100000"),
                rule_ambiguity_score=d("0.750000"),
                public_resolution_reference=None,
            ),
        ),
    )

    row = expiry_report.rows[0]
    assert expiry_report.status == "block"
    assert expiry_report.block_count == d("1")
    assert expiry_report.near_expiry_count == d("1")
    assert expiry_report.stale_information_count == d("1")
    assert expiry_report.thin_settlement_evidence_count == d("1")
    assert expiry_report.weak_liquidity_count == d("1")
    assert expiry_report.rule_ambiguity_count == d("1")
    assert row.seconds_to_expiry == d("1800")
    assert row.information_age_seconds == d("10800")
    assert row.settlement_evidence_age_seconds is None
    assert row.expiry_risk_status == "block"
    assert row.redacted_resolution_reference is None
    assert row.reason_codes == (
        "expiry_block_window",
        "expiry_risk_block",
        "information_refresh_block",
        "liquidity_block",
        "missing_settlement_evidence",
        "rules_ambiguous_block",
    )


def test_watch_event_summarizes_reason_counts() -> None:
    expiry_report = report(
        (
            input_row(
                2,
                research_key="z-risk",
                event_expiry_at=GENERATED_AT + timedelta(hours=12),
                latest_information_observed_at=GENERATED_AT - timedelta(hours=1),
                latest_settlement_evidence_at=GENERATED_AT - timedelta(hours=5),
                liquidity_score=d("0.350000"),
                rule_ambiguity_score=d("0.300000"),
            ),
            input_row(
                1,
                research_key="a-clear",
                event_expiry_at=GENERATED_AT + timedelta(days=4),
            ),
        ),
    )

    assert tuple(row.research_key for row in expiry_report.rows) == ("a-clear", "z-risk")
    assert expiry_report.status == "watch"
    assert expiry_report.pass_count == d("1")
    assert expiry_report.watch_count == d("1")
    assert expiry_report.block_count == d("0")
    assert expiry_report.reason_codes == (
        "expiry_risk_watch",
        "expiry_watch_window",
        "information_refresh_watch",
        "liquidity_watch",
        "rules_ambiguous_watch",
        "settlement_evidence_stale",
    )
    assert tuple(
        (count.reason_code, count.count, count.event_ratio)
        for count in expiry_report.reason_code_counts
        if count.reason_code.endswith("_watch")
    ) == (
        ("expiry_risk_watch", d("1"), d("0.500000")),
        ("information_refresh_watch", d("1"), d("0.500000")),
        ("liquidity_watch", d("1"), d("0.500000")),
        ("rules_ambiguous_watch", d("1"), d("0.500000")),
    )


def test_validation_rejects_bad_types_future_times_bad_counts_and_flags() -> None:
    with pytest.raises(ValueError, match="expiry_watch_window_seconds"):
        config(expiry_watch_window_seconds=d("100"))
    with pytest.raises(ValueError, match="liquidity_pass_threshold"):
        config(liquidity_pass_threshold=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_block_threshold"):
        config(liquidity_block_threshold=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((input_row(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (input_row(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_key"):
        input_row(1, research_key=" research-001")
    with pytest.raises(ValueError, match="event_expiry_at"):
        input_row(1, event_expiry_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="latest_information_observed_at"):
        report(
            (
                input_row(
                    1,
                    latest_information_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="latest_settlement_evidence_at"):
        input_row(
            1,
            settlement_evidence_count=d("1"),
            latest_settlement_evidence_at=None,
        )
    with pytest.raises(ValueError, match="settlement_evidence_family_count"):
        input_row(
            1,
            settlement_evidence_count=d("1"),
            settlement_evidence_family_count=d("2"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    expiry_report = report((input_row(1),))

    with pytest.raises(FrozenInstanceError):
        expiry_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        expiry_report.rows[0].liquidity_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="expiry_risk_status"):
        replace(expiry_report.rows[0], expiry_risk_status="watch")
    with pytest.raises(ValueError, match="status"):
        replace(expiry_report, status="watch")


def test_owned_module_has_no_network_db_file_mutation_or_action_language_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_expiry_risk_report.py"
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
        "sqlalchemy",
        "psycopg",
        "pymongo",
        "open(",
        ".write(",
        "execute(",
        "connect(",
        "buy",
        "sell",
        "position",
        "recommend",
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

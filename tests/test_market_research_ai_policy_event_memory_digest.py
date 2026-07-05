from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

import polymarket_alpha_lab.market_research_ai_policy_event_memory_digest as ai_policy_digest
from polymarket_alpha_lab.market_research_ai_policy_event_memory_digest import (
    DEFAULT_MARKET_RESEARCH_AI_POLICY_EVENT_MEMORY_DIGEST_CONFIG_VERSION,
    MarketResearchAIPolicyEventMemoryDigestConfig,
    MarketResearchAIPolicyEventMemoryDigestInputRow,
    MarketResearchAIPolicyEventMemoryDigestReasonCodeCount,
    MarketResearchAIPolicyEventMemoryDigestReport,
    MarketResearchAIPolicyEventMemoryDigestRow,
    build_market_research_ai_policy_event_memory_digest,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_DEFAULT_DATETIME = object()


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(child for item in value.values() for child in walk_values(item))
    if isinstance(value, list):
        return tuple(child for item in value for child in walk_values(item))
    return (value,)


def config(**overrides: object) -> MarketResearchAIPolicyEventMemoryDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_AI_POLICY_EVENT_MEMORY_DIGEST_CONFIG_VERSION
        ),
        "fresh_regulator_source_max_age_seconds": d("43200.000000"),
        "min_policy_draft_specificity_score": d("0.650000"),
        "legislative_calendar_window_seconds": d("604800.000000"),
        "min_company_agency_alignment_score": d("0.600000"),
        "min_source_family_count": d("2"),
        "stale_evidence_threshold": d("1"),
        "volatility_liquidity_gap_threshold": d("0.250000"),
        "confidence_decay_watch_threshold": d("0.150000"),
        "confidence_decay_block_threshold": d("0.350000"),
    }
    values.update(overrides)
    return MarketResearchAIPolicyEventMemoryDigestConfig(**values)


def policy_row(
    market_research_key: str = "research.alpha",
    *,
    ai_policy_event_key: str = "ai-policy.rulemaking",
    regulator_family: str = "us-agency",
    ai_policy_reference: str = "public-ai-policy-docket",
    regulator_source_observed_at: datetime | None | object = _DEFAULT_DATETIME,
    policy_draft_observed_at: datetime | None | object = _DEFAULT_DATETIME,
    legislative_calendar_at: datetime | None | object = _DEFAULT_DATETIME,
    company_signal_observed_at: datetime | None | object = _DEFAULT_DATETIME,
    agency_signal_observed_at: datetime | None | object = _DEFAULT_DATETIME,
    regulator_source_count: Decimal = d("3"),
    source_family_count: Decimal = d("3"),
    stale_evidence_count: Decimal = d("0"),
    policy_draft_specificity_score: Decimal = d("0.760000"),
    legislative_calendar_proximity_score: Decimal = d("0.880000"),
    company_agency_alignment_score: Decimal = d("0.740000"),
    volatility_score: Decimal = d("0.300000"),
    liquidity_score: Decimal = d("0.250000"),
    volatility_liquidity_gap_score: Decimal = d("0.050000"),
    starting_confidence_score: Decimal = d("0.800000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchAIPolicyEventMemoryDigestInputRow:
    return MarketResearchAIPolicyEventMemoryDigestInputRow(
        market_research_key=market_research_key,
        ai_policy_event_key=ai_policy_event_key,
        regulator_family=regulator_family,
        ai_policy_reference=ai_policy_reference,
        regulator_source_observed_at=(
            GENERATED_AT - timedelta(hours=2)
            if regulator_source_observed_at is _DEFAULT_DATETIME
            else regulator_source_observed_at
        ),
        policy_draft_observed_at=(
            GENERATED_AT - timedelta(hours=3)
            if policy_draft_observed_at is _DEFAULT_DATETIME
            else policy_draft_observed_at
        ),
        legislative_calendar_at=(
            GENERATED_AT + timedelta(days=3)
            if legislative_calendar_at is _DEFAULT_DATETIME
            else legislative_calendar_at
        ),
        company_signal_observed_at=(
            GENERATED_AT - timedelta(hours=4)
            if company_signal_observed_at is _DEFAULT_DATETIME
            else company_signal_observed_at
        ),
        agency_signal_observed_at=(
            GENERATED_AT - timedelta(hours=5)
            if agency_signal_observed_at is _DEFAULT_DATETIME
            else agency_signal_observed_at
        ),
        regulator_source_count=regulator_source_count,
        source_family_count=source_family_count,
        stale_evidence_count=stale_evidence_count,
        policy_draft_specificity_score=policy_draft_specificity_score,
        legislative_calendar_proximity_score=legislative_calendar_proximity_score,
        company_agency_alignment_score=company_agency_alignment_score,
        volatility_score=volatility_score,
        liquidity_score=liquidity_score,
        volatility_liquidity_gap_score=volatility_liquidity_gap_score,
        starting_confidence_score=starting_confidence_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchAIPolicyEventMemoryDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchAIPolicyEventMemoryDigestReport:
    return build_market_research_ai_policy_event_memory_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_ai_policy_event_memory_digest_reduces_policy_research_memory() -> None:
    summary = report(
        (
            policy_row(
                "research.ready",
                ai_policy_event_key="ai-policy.eu-code",
                regulator_family="eu-regulator",
                ai_policy_reference="public-eu-ai-code-calendar",
                regulator_source_observed_at=GENERATED_AT - timedelta(hours=1),
                legislative_calendar_at=GENERATED_AT + timedelta(days=2),
                source_family_count=d("3"),
                stale_evidence_count=ZERO,
                policy_draft_specificity_score=d("0.820000"),
                legislative_calendar_proximity_score=d("0.900000"),
                company_agency_alignment_score=d("0.760000"),
                volatility_liquidity_gap_score=d("0.050000"),
                starting_confidence_score=d("0.840000"),
            ),
            policy_row(
                "research.watch",
                ai_policy_event_key="ai-policy.us-senate",
                regulator_family="us-legislature",
                ai_policy_reference="https://vendor.example/ai-policy?token=secret-123",
                regulator_source_observed_at=GENERATED_AT - timedelta(hours=18),
                policy_draft_observed_at=GENERATED_AT - timedelta(days=4),
                legislative_calendar_at=GENERATED_AT + timedelta(days=14),
                company_signal_observed_at=GENERATED_AT - timedelta(hours=12),
                agency_signal_observed_at=GENERATED_AT - timedelta(hours=11),
                regulator_source_count=d("2"),
                source_family_count=d("1"),
                stale_evidence_count=d("1"),
                policy_draft_specificity_score=d("0.520000"),
                legislative_calendar_proximity_score=d("0.300000"),
                company_agency_alignment_score=d("0.540000"),
                volatility_score=d("0.760000"),
                liquidity_score=d("0.220000"),
                volatility_liquidity_gap_score=d("0.310000"),
                starting_confidence_score=d("0.680000"),
            ),
            policy_row(
                "research.blocked",
                ai_policy_event_key="ai-policy.state-ban",
                regulator_family="state-agency",
                ai_policy_reference="wallet://private/ai-policy-feed",
                regulator_source_observed_at=None,
                policy_draft_observed_at=GENERATED_AT - timedelta(days=11),
                legislative_calendar_at=GENERATED_AT + timedelta(days=45),
                company_signal_observed_at=None,
                agency_signal_observed_at=GENERATED_AT - timedelta(days=10),
                regulator_source_count=ZERO,
                source_family_count=ZERO,
                stale_evidence_count=d("3"),
                policy_draft_specificity_score=d("0.200000"),
                legislative_calendar_proximity_score=d("0.120000"),
                company_agency_alignment_score=d("0.180000"),
                volatility_score=d("0.910000"),
                liquidity_score=d("0.100000"),
                volatility_liquidity_gap_score=d("0.620000"),
                starting_confidence_score=d("0.720000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchAIPolicyEventMemoryDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_AI_POLICY_EVENT_MEMORY_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_ai_policy_event_memory_digest"
    )
    assert summary.ai_policy_event_count == d("3")
    assert summary.ready_event_count == d("1")
    assert summary.watch_event_count == ZERO
    assert summary.blocked_event_count == d("2")
    assert summary.fresh_regulator_source_event_count == d("1")
    assert summary.stale_regulator_source_event_count == d("1")
    assert summary.missing_regulator_source_event_count == d("1")
    assert summary.specific_policy_draft_event_count == d("1")
    assert summary.near_legislative_calendar_event_count == d("1")
    assert summary.aligned_company_agency_event_count == d("1")
    assert summary.diverse_source_family_event_count == d("1")
    assert summary.stale_evidence_event_count == d("2")
    assert summary.volatility_liquidity_gap_event_count == d("2")
    assert summary.total_stale_evidence_count == d("4")
    assert summary.average_starting_confidence_score == d("0.746667")
    assert summary.average_final_confidence_score == d("0.376000")
    assert summary.average_confidence_decay_score == d("0.370667")
    assert summary.max_regulator_source_age_seconds == d("64800.000000")
    assert summary.source_family_diversity_ratio == d("0.333333")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.ai_policy_event_key for row in summary.rows) == (
        "ai-policy.state-ban",
        "ai-policy.us-senate",
        "ai-policy.eu-code",
    )

    blocked = summary.rows[0]
    assert blocked.memory_status == "blocked"
    assert blocked.regulator_source_age_seconds is None
    assert blocked.legislative_calendar_seconds == d("3888000.000000")
    assert blocked.final_confidence_score == ZERO
    assert blocked.confidence_decay_score == d("0.720000")
    assert blocked.redacted_ai_policy_reference == "sha256:1237a8cb5c45"
    assert blocked.reason_codes == (
        "market_research_ai_policy_event_memory_digest_alignment_gap",
        "market_research_ai_policy_event_memory_digest_calendar_far",
        "market_research_ai_policy_event_memory_digest_confidence_decay_block",
        "market_research_ai_policy_event_memory_digest_missing_company_agency_signal",
        "market_research_ai_policy_event_memory_digest_missing_regulator_source",
        "market_research_ai_policy_event_memory_digest_policy_draft_underspecified",
        "market_research_ai_policy_event_memory_digest_source_family_thin",
        "market_research_ai_policy_event_memory_digest_stale_evidence",
        "market_research_ai_policy_event_memory_digest_volatility_liquidity_gap",
    )

    watch = summary.rows[1]
    assert watch.memory_status == "blocked"
    assert watch.regulator_source_age_seconds == d("64800.000000")
    assert watch.final_confidence_score == d("0.311333")
    assert watch.confidence_decay_score == d("0.368667")
    assert watch.redacted_ai_policy_reference == "sha256:172755c9a889"
    assert watch.reason_codes == (
        "market_research_ai_policy_event_memory_digest_alignment_gap",
        "market_research_ai_policy_event_memory_digest_calendar_far",
        "market_research_ai_policy_event_memory_digest_confidence_decay_block",
        "market_research_ai_policy_event_memory_digest_policy_draft_underspecified",
        "market_research_ai_policy_event_memory_digest_source_family_thin",
        "market_research_ai_policy_event_memory_digest_stale_evidence",
        "market_research_ai_policy_event_memory_digest_stale_regulator_source",
        "market_research_ai_policy_event_memory_digest_volatility_liquidity_gap",
    )

    ready = summary.rows[2]
    assert ready.memory_status == "ready"
    assert ready.regulator_source_age_seconds == d("3600.000000")
    assert ready.final_confidence_score == d("0.816667")
    assert ready.confidence_decay_score == d("0.023333")
    assert ready.redacted_ai_policy_reference == "public-eu-ai-code-calendar"
    assert ready.reason_codes == (
        "market_research_ai_policy_event_memory_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_alignment_gap",
            count=d("2"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_calendar_far",
            count=d("2"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_confidence_decay_block",
            count=d("2"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_missing_company_agency_signal",
            count=d("1"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_missing_regulator_source",
            count=d("1"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_policy_draft_underspecified",
            count=d("2"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_ready",
            count=d("1"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_source_family_thin",
            count=d("2"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_stale_evidence",
            count=d("2"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_stale_regulator_source",
            count=d("1"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_volatility_liquidity_gap",
            count=d("2"),
            event_ratio=d("0.666667"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "wallet://",
        "private/ai-policy-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_ai_policy_event_memory_digest_returns_blocked_empty_report() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_ai_policy_event_memory_digest"
    )
    assert summary.ai_policy_event_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_policy_event_memory_digest_no_inputs",
            count=d("1"),
            event_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_ai_policy_event_memory_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_ai_policy_event_memory_digest_uses_configured_source_family_threshold_for_confidence() -> None:
    summary = report(
        (
            policy_row(
                "research.custom-threshold",
                ai_policy_event_key="ai-policy.custom-threshold",
                ai_policy_reference="public-ai-policy-calendar",
                regulator_source_observed_at=GENERATED_AT - timedelta(hours=1),
                policy_draft_observed_at=GENERATED_AT - timedelta(days=1),
                legislative_calendar_at=GENERATED_AT + timedelta(days=2),
                company_signal_observed_at=GENERATED_AT - timedelta(hours=2),
                agency_signal_observed_at=GENERATED_AT - timedelta(hours=2),
                regulator_source_count=d("2"),
                source_family_count=d("1"),
                stale_evidence_count=ZERO,
                policy_draft_specificity_score=d("0.820000"),
                legislative_calendar_proximity_score=d("0.900000"),
                company_agency_alignment_score=d("0.760000"),
                volatility_score=d("0.200000"),
                liquidity_score=d("0.200000"),
                volatility_liquidity_gap_score=d("0.050000"),
                starting_confidence_score=d("0.840000"),
            ),
        ),
        cfg=config(min_source_family_count=d("1")),
    )

    row = summary.rows[0]
    assert row.memory_status == "ready"
    assert row.final_confidence_score == d("0.816667")
    assert row.confidence_decay_score == d("0.023333")
    assert row.reason_codes == (
        "market_research_ai_policy_event_memory_digest_ready",
    )
    assert summary.source_family_diversity_ratio == d("1.000000")


def test_ai_policy_event_memory_digest_payload_serializes_public_decimal_strings() -> None:
    summary = report(
        (
            policy_row(
                "research.json",
                ai_policy_event_key="ai-policy.json",
                ai_policy_reference="https://vendor.example/ai-policy?token=secret-123",
                regulator_source_observed_at=GENERATED_AT - timedelta(hours=1),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    payload_fn = getattr(
        ai_policy_digest,
        "market_research_ai_policy_event_memory_digest_payload",
        None,
    )
    assert callable(payload_fn)

    payload = payload_fn(summary)
    assert payload == payload_fn(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["ai_policy_event_count"] == "1.000000"
    assert payload["ready_event_count"] == "1.000000"
    assert payload["average_starting_confidence_score"] == "0.800000"
    assert payload["rows"][0]["regulator_source_age_seconds"] == "3600.000000"
    assert payload["rows"][0]["regulator_source_count"] == "3.000000"
    assert payload["rows"][0]["redacted_ai_policy_reference"] == (
        "sha256:172755c9a889"
    )
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["event_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    public = json.dumps(payload, sort_keys=True).lower()
    assert "secret-123" not in public
    assert "vendor.example" not in public
    assert "token" not in public
    assert not any(
        type(value) in (Decimal, float, int)
        for value in walk_values(payload)
    )


def test_ai_policy_event_memory_digest_validates_public_contracts() -> None:
    assert is_dataclass(MarketResearchAIPolicyEventMemoryDigestConfig)
    assert is_dataclass(MarketResearchAIPolicyEventMemoryDigestInputRow)
    assert is_dataclass(MarketResearchAIPolicyEventMemoryDigestRow)
    assert is_dataclass(MarketResearchAIPolicyEventMemoryDigestReasonCodeCount)
    assert is_dataclass(MarketResearchAIPolicyEventMemoryDigestReport)

    with pytest.raises(FrozenInstanceError):
        replace(policy_row(), source_family_count=d("4")).source_family_count = d("5")

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("ai-policy-event-memory-v0"))
    with pytest.raises(ValueError, match="fresh_regulator_source_max_age_seconds"):
        config(fresh_regulator_source_max_age_seconds=43200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_source_family_count"):
        config(min_source_family_count=d("1.5"))
    with pytest.raises(ValueError, match="volatility_liquidity_gap_threshold"):
        config(volatility_liquidity_gap_threshold=Decimal("NaN"))
    with pytest.raises(ValueError, match="confidence_decay"):
        config(
            confidence_decay_watch_threshold=d("0.500000"),
            confidence_decay_block_threshold=d("0.250000"),
        )
    with pytest.raises(ValueError, match="market_research_key"):
        policy_row(" bad")
    with pytest.raises(ValueError, match="regulator_family"):
        policy_row(regulator_family="broker_feed")
    with pytest.raises(ValueError, match="ai_policy_reference"):
        policy_row(ai_policy_reference="")
    with pytest.raises(ValueError, match="regulator_source_observed_at"):
        policy_row(regulator_source_observed_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="policy_draft_observed_at"):
        policy_row(policy_draft_observed_at=GENERATED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="legislative_calendar_at"):
        policy_row(
            legislative_calendar_at=_DatetimeSubclass(
                2026,
                7,
                3,
                12,
                0,
                tzinfo=UTC,
            ),
        )
    with pytest.raises(ValueError, match="regulator_source_count"):
        policy_row(regulator_source_count=2.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_family_count"):
        policy_row(source_family_count=_DecimalSubclass("2"))
    with pytest.raises(ValueError, match="stale_evidence_count"):
        policy_row(stale_evidence_count=d("-1"))
    with pytest.raises(ValueError, match="policy_draft_specificity_score"):
        policy_row(policy_draft_specificity_score=d("1.000001"))
    with pytest.raises(ValueError, match="volatility_score"):
        policy_row(volatility_score=d("-0.000001"))
    with pytest.raises(ValueError, match="starting_confidence_score"):
        policy_row(starting_confidence_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        policy_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        policy_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        policy_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_ai_policy_event_memory_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_ai_policy_event_memory_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_ai_policy_event_memory_digest_rejects_incoherent_manual_reports() -> None:
    valid_row = MarketResearchAIPolicyEventMemoryDigestRow(
        market_research_key="research.alpha",
        ai_policy_event_key="ai-policy.alpha",
        regulator_family="us-agency",
        memory_status="ready",
        regulator_source_observed_at=GENERATED_AT - timedelta(hours=1),
        policy_draft_observed_at=GENERATED_AT - timedelta(hours=2),
        legislative_calendar_at=GENERATED_AT + timedelta(days=2),
        company_signal_observed_at=GENERATED_AT - timedelta(hours=3),
        agency_signal_observed_at=GENERATED_AT - timedelta(hours=4),
        regulator_source_age_seconds=d("3600.000000"),
        policy_draft_age_seconds=d("7200.000000"),
        legislative_calendar_seconds=d("172800.000000"),
        company_signal_age_seconds=d("10800.000000"),
        agency_signal_age_seconds=d("14400.000000"),
        regulator_source_count=d("3"),
        source_family_count=d("2"),
        stale_evidence_count=ZERO,
        policy_draft_specificity_score=d("0.800000"),
        legislative_calendar_proximity_score=d("0.900000"),
        company_agency_alignment_score=d("0.700000"),
        volatility_score=d("0.200000"),
        liquidity_score=d("0.300000"),
        volatility_liquidity_gap_score=d("0.050000"),
        starting_confidence_score=d("0.800000"),
        final_confidence_score=d("0.891600"),
        confidence_decay_score=ZERO,
        redacted_ai_policy_reference="public-reference",
        reason_codes=("market_research_ai_policy_event_memory_digest_ready",),
    )
    assert valid_row.memory_status == "ready"

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            valid_row,
            reason_codes=(
                "market_research_ai_policy_event_memory_digest_stale_evidence",
                "market_research_ai_policy_event_memory_digest_ready",
            ),
        )
    with pytest.raises(ValueError, match="memory_status"):
        replace(valid_row, memory_status="blocked")
    with pytest.raises(ValueError, match="redacted_ai_policy_reference"):
        replace(valid_row, redacted_ai_policy_reference="https://host?token=secret")
    with pytest.raises(ValueError, match="confidence_decay_score"):
        replace(valid_row, confidence_decay_score=d("-0.000001"))

    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchAIPolicyEventMemoryDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_AI_POLICY_EVENT_MEMORY_DIGEST_CONFIG_VERSION
            ),
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_ai_policy_event_memory_digest"
            ),
            ai_policy_event_count=d("1"),
            ready_event_count=d("1"),
            watch_event_count=ZERO,
            blocked_event_count=ZERO,
            fresh_regulator_source_event_count=d("1"),
            stale_regulator_source_event_count=ZERO,
            missing_regulator_source_event_count=ZERO,
            specific_policy_draft_event_count=d("1"),
            near_legislative_calendar_event_count=d("1"),
            aligned_company_agency_event_count=d("1"),
            diverse_source_family_event_count=d("1"),
            stale_evidence_event_count=ZERO,
            volatility_liquidity_gap_event_count=ZERO,
            total_stale_evidence_count=ZERO,
            average_starting_confidence_score=d("0.800000"),
            average_final_confidence_score=d("0.891600"),
            average_confidence_decay_score=ZERO,
            max_regulator_source_age_seconds=d("3600.000000"),
            source_family_diversity_ratio=d("1.000000"),
            rows=(valid_row,),
            reason_code_counts=(
                MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
                    reason_code="market_research_ai_policy_event_memory_digest_ready",
                    count=d("1"),
                    event_ratio=d("1.000000"),
                ),
                MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
                    reason_code=(
                        "market_research_ai_policy_event_memory_digest_stale_evidence"
                    ),
                    count=d("1"),
                    event_ratio=d("1.000000"),
                ),
            ),
            reason_codes=(
                "market_research_ai_policy_event_memory_digest_ready",
                "market_research_ai_policy_event_memory_digest_stale_evidence",
            ),
        )


def test_module_has_no_live_io_or_trading_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_ai_policy_event_memory_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "replace",
        "rename",
        "submit",
        "cancel",
        "order",
        "trade",
        "wallet",
        "broker",
        "account",
        "sign",
        "auth",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(
        name == forbidden_name
        for name in lowered_surface
        for forbidden_name in forbidden_call_or_attribute_names
    )
    assert "persist" not in source.lower()
    assert "database" not in source.lower()
    assert "advice" not in source.lower()

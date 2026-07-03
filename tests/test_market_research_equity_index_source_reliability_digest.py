from __future__ import annotations

import dataclasses
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_equity_index_source_reliability_digest import (
    DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_SOURCE_RELIABILITY_DIGEST_CONFIG_VERSION,
    MarketResearchEquityIndexSourceReliabilityDigestConfig,
    MarketResearchEquityIndexSourceReliabilityObservation,
    MarketResearchEquityIndexSourceReliabilityReasonCodeCount,
    MarketResearchEquityIndexSourceReliabilityRow,
    build_market_research_equity_index_source_reliability_digest,
    market_research_equity_index_source_reliability_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


def test_scores_equity_index_sources_with_decimal_metrics_and_redacted_payload() -> None:
    report = build_market_research_equity_index_source_reliability_digest(
        (
            _observation(
                event_id="spx-cpi",
                source_ref="macro-calendar",
                source_family="official",
                macro_calendar_published_at=GENERATED_AT - timedelta(minutes=30),
                earnings_source_count=Decimal("3"),
                index_confirmation_count=Decimal("2"),
                futures_confirmation_count=Decimal("1"),
                volatility_regime_score=Decimal("0.300000"),
                contradiction_count=Decimal("0"),
                acknowledged_at=GENERATED_AT - timedelta(minutes=5),
            ),
            _observation(
                event_id="spx-cpi",
                source_ref="earnings-coverage",
                source_family="company_filings",
                macro_calendar_published_at=GENERATED_AT - timedelta(minutes=45),
                earnings_source_count=Decimal("4"),
                index_confirmation_count=Decimal("2"),
                futures_confirmation_count=Decimal("1"),
                volatility_regime_score=Decimal("0.350000"),
                contradiction_count=Decimal("0"),
                acknowledged_at=GENERATED_AT - timedelta(minutes=4),
            ),
            _observation(
                event_id="ndx-ai-earnings",
                index_symbol="ndx",
                source_ref="vendor-model",
                source_family="market_data",
                macro_calendar_published_at=GENERATED_AT - timedelta(hours=5),
                earnings_source_count=Decimal("1"),
                index_confirmation_count=Decimal("1"),
                futures_confirmation_count=Decimal("0"),
                volatility_regime_score=Decimal("0.650000"),
                contradiction_count=Decimal("0"),
                acknowledged_at=GENERATED_AT - timedelta(minutes=20),
            ),
        ),
        config=MarketResearchEquityIndexSourceReliabilityDigestConfig(
            max_macro_calendar_age_seconds=Decimal("7200.000000"),
            min_earnings_source_count=Decimal("2"),
            min_index_confirmation_count=Decimal("1"),
            min_futures_confirmation_count=Decimal("1"),
            max_volatility_regime_score=Decimal("0.700000"),
            min_source_family_diversity_ratio=Decimal("0.500000"),
            max_contradiction_rate=Decimal("0.250000"),
            max_acknowledgement_lag_seconds=Decimal("3600.000000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_SOURCE_RELIABILITY_DIGEST_CONFIG_VERSION
    )
    assert report.reliability_status == "watch"
    assert report.event_count == Decimal("2")
    assert report.source_count == Decimal("3")
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.blocked_count == Decimal("0")
    assert report.macro_calendar_freshness_age_seconds == Decimal("18000.000000")
    assert report.average_earnings_source_count == Decimal("4.000000")
    assert report.average_confirmation_count == Decimal("2.000000")
    assert report.max_volatility_regime_score == Decimal("0.650000")
    assert report.source_family_diversity_ratio == Decimal("1.000000")
    assert report.contradiction_rate == Decimal("0.000000")
    assert report.acknowledgement_lag_seconds == Decimal("1200.000000")
    assert report.reason_codes == (
        "market_research_equity_index_source_reliability_digest_macro_calendar_stale",
        "market_research_equity_index_source_reliability_digest_low_earnings_breadth",
        "market_research_equity_index_source_reliability_digest_missing_futures_confirmation",
    )
    assert report.reason_code_counts == (
        MarketResearchEquityIndexSourceReliabilityReasonCodeCount(
            reason_code=(
                "market_research_equity_index_source_reliability_digest_"
                "low_earnings_breadth"
            ),
            count=Decimal("1"),
        ),
        MarketResearchEquityIndexSourceReliabilityReasonCodeCount(
            reason_code=(
                "market_research_equity_index_source_reliability_digest_"
                "macro_calendar_stale"
            ),
            count=Decimal("1"),
        ),
        MarketResearchEquityIndexSourceReliabilityReasonCodeCount(
            reason_code=(
                "market_research_equity_index_source_reliability_digest_"
                "missing_futures_confirmation"
            ),
            count=Decimal("1"),
        ),
    )
    assert report.rows == (
        MarketResearchEquityIndexSourceReliabilityRow(
            event_id="ndx-ai-earnings",
            index_symbol="ndx",
            source_count=Decimal("1"),
            source_family_count=Decimal("1"),
            macro_calendar_freshness_age_seconds=Decimal("18000.000000"),
            earnings_source_count=Decimal("1"),
            index_confirmation_count=Decimal("1"),
            futures_confirmation_count=Decimal("0"),
            confirmation_count=Decimal("1"),
            volatility_regime_score=Decimal("0.650000"),
            source_family_diversity_ratio=Decimal("1.000000"),
            contradiction_count=Decimal("0"),
            contradiction_rate=Decimal("0.000000"),
            acknowledgement_lag_seconds=Decimal("1200.000000"),
            reliability_score=Decimal("0.620000"),
            reliability_status="watch",
            reason_codes=(
                "market_research_equity_index_source_reliability_digest_row_macro_calendar_stale",
                "market_research_equity_index_source_reliability_digest_row_low_earnings_breadth",
                "market_research_equity_index_source_reliability_digest_row_missing_futures_confirmation",
            ),
        ),
        MarketResearchEquityIndexSourceReliabilityRow(
            event_id="spx-cpi",
            index_symbol="spx",
            source_count=Decimal("2"),
            source_family_count=Decimal("2"),
            macro_calendar_freshness_age_seconds=Decimal("2700.000000"),
            earnings_source_count=Decimal("7"),
            index_confirmation_count=Decimal("4"),
            futures_confirmation_count=Decimal("2"),
            confirmation_count=Decimal("6"),
            volatility_regime_score=Decimal("0.350000"),
            source_family_diversity_ratio=Decimal("1.000000"),
            contradiction_count=Decimal("0"),
            contradiction_rate=Decimal("0.000000"),
            acknowledgement_lag_seconds=Decimal("300.000000"),
            reliability_score=Decimal("1.000000"),
            reliability_status="pass",
            reason_codes=(
                "market_research_equity_index_source_reliability_digest_row_passed",
            ),
        ),
    )

    payload = market_research_equity_index_source_reliability_digest_payload(report)
    payload_text = repr(payload)
    assert "spx-cpi" not in payload_text
    assert "ndx-ai-earnings" not in payload_text
    assert "macro-calendar" not in payload_text
    assert payload["rows"][0]["redacted_event_ref"] == "<redacted-event-001>"
    assert payload["rows"][0]["redacted_index_ref"] == "<redacted-index-001>"
    assert payload["rows"][0]["reliability_score"] == "0.620000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_floats(payload)
    _assert_public_numeric_fields_are_decimals(report)
    _assert_public_numeric_fields_are_decimals(report.rows[0])


def test_equity_index_digest_computes_age_and_ack_lag_from_decimal_microseconds() -> None:
    report = build_market_research_equity_index_source_reliability_digest(
        (
            _observation(
                event_id="spx-cpi",
                index_symbol="spx",
                source_ref="macro-calendar",
                source_family="calendar",
                observed_at=datetime(2026, 7, 3, 11, 59, 57, 1, tzinfo=UTC),
                macro_calendar_published_at=datetime(
                    2026,
                    7,
                    3,
                    11,
                    59,
                    58,
                    1,
                    tzinfo=UTC,
                ),
                resolved_at=datetime(2026, 7, 3, 11, 59, 57, 500000, tzinfo=UTC),
                acknowledged_at=datetime(2026, 7, 3, 11, 59, 59, 999999, tzinfo=UTC),
            ),
        ),
        config=MarketResearchEquityIndexSourceReliabilityDigestConfig(),
        generated_at=datetime(2026, 7, 3, 12, 0, 0, 234567, tzinfo=UTC),
    )

    assert report.macro_calendar_freshness_age_seconds == Decimal("2.234566")
    assert report.acknowledgement_lag_seconds == Decimal("2.499999")
    assert report.rows[0].macro_calendar_freshness_age_seconds == Decimal("2.234566")
    assert report.rows[0].acknowledgement_lag_seconds == Decimal("2.499999")


def test_blocks_contradictions_high_volatility_low_diversity_and_slow_acknowledgement() -> None:
    report = build_market_research_equity_index_source_reliability_digest(
        (
            _observation(
                source_ref="source-a",
                source_family="official",
                macro_calendar_published_at=GENERATED_AT - timedelta(hours=3),
                earnings_source_count=Decimal("1"),
                index_confirmation_count=Decimal("0"),
                futures_confirmation_count=Decimal("0"),
                volatility_regime_score=Decimal("0.900000"),
                resolved_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=GENERATED_AT - timedelta(minutes=10),
                contradiction_count=Decimal("1"),
            ),
            _observation(
                source_ref="source-b",
                source_family="official",
                macro_calendar_published_at=GENERATED_AT - timedelta(hours=4),
                earnings_source_count=Decimal("1"),
                index_confirmation_count=Decimal("0"),
                futures_confirmation_count=Decimal("0"),
                volatility_regime_score=Decimal("0.850000"),
                resolved_at=GENERATED_AT - timedelta(hours=5),
                acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                contradiction_count=Decimal("0"),
            ),
        ),
        config=MarketResearchEquityIndexSourceReliabilityDigestConfig(
            max_macro_calendar_age_seconds=Decimal("3600.000000"),
            min_earnings_source_count=Decimal("2"),
            min_index_confirmation_count=Decimal("1"),
            min_futures_confirmation_count=Decimal("1"),
            max_volatility_regime_score=Decimal("0.700000"),
            min_source_family_diversity_ratio=Decimal("0.750000"),
            max_contradiction_rate=Decimal("0.250000"),
            max_acknowledgement_lag_seconds=Decimal("3600.000000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.reliability_status == "blocked"
    assert report.reason_codes == (
        "market_research_equity_index_source_reliability_digest_macro_calendar_stale",
        "market_research_equity_index_source_reliability_digest_low_earnings_breadth",
        "market_research_equity_index_source_reliability_digest_missing_index_confirmation",
        "market_research_equity_index_source_reliability_digest_missing_futures_confirmation",
        "market_research_equity_index_source_reliability_digest_high_volatility_regime",
        "market_research_equity_index_source_reliability_digest_low_source_family_diversity",
        "market_research_equity_index_source_reliability_digest_high_contradiction_rate",
        "market_research_equity_index_source_reliability_digest_slow_acknowledgement",
    )
    assert report.rows[0].reliability_status == "blocked"
    assert report.rows[0].reason_codes == (
        "market_research_equity_index_source_reliability_digest_row_macro_calendar_stale",
        "market_research_equity_index_source_reliability_digest_row_low_earnings_breadth",
        "market_research_equity_index_source_reliability_digest_row_missing_index_confirmation",
        "market_research_equity_index_source_reliability_digest_row_missing_futures_confirmation",
        "market_research_equity_index_source_reliability_digest_row_high_volatility_regime",
        "market_research_equity_index_source_reliability_digest_row_low_source_family_diversity",
        "market_research_equity_index_source_reliability_digest_row_high_contradiction_rate",
        "market_research_equity_index_source_reliability_digest_row_slow_acknowledgement",
    )
    assert report.rows[0].reliability_score == Decimal("0.000000")


def test_empty_input_returns_blocked_report_only_digest() -> None:
    report = build_market_research_equity_index_source_reliability_digest(
        (),
        config=MarketResearchEquityIndexSourceReliabilityDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.reliability_status == "blocked"
    assert report.event_count == Decimal("0")
    assert report.source_count == Decimal("0")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_equity_index_source_reliability_digest_empty",
    )
    assert report.reason_code_counts == (
        MarketResearchEquityIndexSourceReliabilityReasonCodeCount(
            reason_code="market_research_equity_index_source_reliability_digest_empty",
            count=Decimal("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    _assert_public_numeric_fields_are_decimals(report)


def test_validation_guards_decimals_datetimes_flags_sensitive_refs_and_frozen_instances() -> None:
    report = build_market_research_equity_index_source_reliability_digest(
        (_observation(),),
        config=MarketResearchEquityIndexSourceReliabilityDigestConfig(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.rows[0].reliability_score = Decimal("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="earnings_source_count must be a Decimal"):
        _observation(earnings_source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _observation(observed_at=datetime(2026, 7, 3, 16, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_market_research_equity_index_source_reliability_digest(
            (_observation(),),
            config=MarketResearchEquityIndexSourceReliabilityDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        MarketResearchEquityIndexSourceReliabilityDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation readonly must be True"):
        _observation(readonly=False)
    for source_ref in (
        "0xabc",
        "user@example.com",
        "private-source",
        "token-source",
        "order-source",
    ):
        with pytest.raises(ValueError, match="source_ref must be a redacted identifier"):
            _observation(source_ref=source_ref)


def test_static_forbidden_surface_terms_are_absent() -> None:
    import polymarket_alpha_lab.market_research_equity_index_source_reliability_digest as module

    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    forbidden_terms = (
        ".total_seconds(",
        "decimal(str(",
        "value: float",
        "account",
        "api_key",
        "auth",
        "broker",
        "cancel",
        "investment_advice",
        "live_trading",
        "place_order",
        "postgres",
        "private_key",
        "requests",
        "secret",
        "sign",
        "signer",
        "signing",
        "socket",
        "sqlite",
        "submit",
        "trading_advice",
        "urlopen",
        "wallet",
        "web3",
    )

    assert [term for term in forbidden_terms if term in source] == []


def _observation(
    *,
    event_id: str = "spx-cpi",
    index_symbol: str = "spx",
    source_ref: str = "source-alpha",
    source_family: str = "official",
    observed_at: datetime | None = None,
    macro_calendar_published_at: datetime | None = None,
    resolved_at: datetime | None = None,
    acknowledged_at: datetime | None = None,
    earnings_source_count: Decimal = Decimal("3"),
    index_confirmation_count: Decimal = Decimal("1"),
    futures_confirmation_count: Decimal = Decimal("1"),
    volatility_regime_score: Decimal = Decimal("0.300000"),
    contradiction_count: Decimal = Decimal("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEquityIndexSourceReliabilityObservation:
    return MarketResearchEquityIndexSourceReliabilityObservation(
        event_id=event_id,
        index_symbol=index_symbol,
        source_ref=source_ref,
        source_family=source_family,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=10),
        macro_calendar_published_at=(
            macro_calendar_published_at or GENERATED_AT - timedelta(minutes=10)
        ),
        resolved_at=resolved_at or GENERATED_AT - timedelta(minutes=8),
        acknowledged_at=acknowledged_at or GENERATED_AT - timedelta(minutes=7),
        earnings_source_count=earnings_source_count,
        index_confirmation_count=index_confirmation_count,
        futures_confirmation_count=futures_confirmation_count,
        volatility_regime_score=volatility_regime_score,
        contradiction_count=contradiction_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float value leaked into payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _assert_public_numeric_fields_are_decimals(value: object) -> None:
    numeric_name_fragments = (
        "age",
        "count",
        "lag",
        "rate",
        "ratio",
        "score",
    )
    for field in dataclasses.fields(value):
        if any(fragment in field.name for fragment in numeric_name_fragments):
            field_value = getattr(value, field.name)
            if isinstance(field_value, datetime):
                continue
            if isinstance(field_value, tuple):
                continue
            assert isinstance(field_value, Decimal), field.name

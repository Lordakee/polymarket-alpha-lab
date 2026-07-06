from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import research_packet_market_event_source_refresh_plan_v2 as module


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def _source(
    *,
    event_slug: str = "fed-rate-cut-july",
    source_family: str = "official_calendar",
    source_label: str = "fomc-public-calendar",
    source_age_hours: Decimal = Decimal("12.000000"),
    confidence_score: Decimal = Decimal("0.920000"),
    has_primary_reference: bool = True,
    note: str = "public reference reviewed",
) -> module.MarketEventSourceRefreshInput:
    return module.MarketEventSourceRefreshInput(
        event_slug=event_slug,
        source_family=source_family,
        source_label=source_label,
        source_age_hours=source_age_hours,
        confidence_score=confidence_score,
        has_primary_reference=has_primary_reference,
        note=note,
    )


def _report(
    sources: tuple[module.MarketEventSourceRefreshInput, ...],
) -> module.ResearchPacketMarketEventSourceRefreshPlanV2Report:
    return module.build_research_packet_market_event_source_refresh_plan_v2(
        sources=sources,
        generated_at=GENERATED_AT,
    )


def _assert_no_decimal_or_binary_numeric(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"Decimal leaked into payload: {value}")
    if type(value) in (float, int):
        raise AssertionError(f"binary/public numeric leaked into payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_or_binary_numeric(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_or_binary_numeric(item)


def _walk_payload_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            strings.append(key)
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(_walk_payload_strings(item))
    return tuple(strings)


def test_refresh_priority_ranks_critical_stale_low_confidence_then_fresh() -> None:
    report = _report(
        (
            _source(
                source_family="official_calendar",
                source_label="fresh-official-calendar",
                source_age_hours=Decimal("6.000000"),
                confidence_score=Decimal("0.950000"),
            ),
            _source(
                source_family="news_context",
                source_label="critical-news-context",
                source_age_hours=Decimal("200.000000"),
                confidence_score=Decimal("0.990000"),
            ),
            _source(
                source_family="community_signal",
                source_label="thin-community-signal",
                source_age_hours=Decimal("18.000000"),
                confidence_score=Decimal("0.350000"),
            ),
            _source(
                source_family="resolution_rules",
                source_label="stale-resolution-rules",
                source_age_hours=Decimal("96.000000"),
                confidence_score=Decimal("0.900000"),
            ),
        ),
    )

    assert tuple(row.source_label for row in report.rows) == (
        "critical-news-context",
        "stale-resolution-rules",
        "thin-community-signal",
        "fresh-official-calendar",
    )
    assert tuple(row.refresh_priority for row in report.rows) == (
        "urgent_refresh",
        "high_refresh",
        "high_refresh",
        "low_watch",
    )
    assert tuple(row.refresh_rank for row in report.rows) == (
        Decimal("1.000000"),
        Decimal("2.000000"),
        Decimal("3.000000"),
        Decimal("4.000000"),
    )


def test_source_family_coverage_includes_all_required_families() -> None:
    report = _report((_source(source_family="official_calendar"),))

    assert tuple(summary.source_family for summary in report.family_summaries) == (
        module.REQUIRED_SOURCE_FAMILIES
    )
    missing = {
        summary.source_family: summary
        for summary in report.family_summaries
        if summary.coverage_status == "missing"
    }
    assert tuple(missing) == tuple(module.REQUIRED_SOURCE_FAMILIES[1:])
    assert all(summary.source_count == Decimal("0.000000") for summary in missing.values())
    assert report.coverage_status == "coverage_gap"


def test_stale_source_escalates_even_with_high_confidence() -> None:
    report = _report(
        (
            _source(
                source_family="venue_status",
                source_label="venue-event-status",
                source_age_hours=Decimal("180.000000"),
                confidence_score=Decimal("1.000000"),
            ),
        ),
    )

    row = report.rows[0]
    assert row.refresh_priority == "urgent_refresh"
    assert "stale_source_escalation" in row.reason_codes
    assert row.staleness_score == Decimal("1.000000")
    assert report.stale_source_count == Decimal("1.000000")


def test_payload_serializes_decimal_values_as_strings_and_round_trips_digest() -> None:
    report = _report(
        (
            _source(source_family="official_calendar"),
            _source(source_family="news_context", source_age_hours=Decimal("84.000000")),
        ),
    )

    payload = module.research_packet_market_event_source_refresh_plan_v2_payload(report)

    assert payload["reviewed_source_count"] == "2.000000"
    assert payload["stale_source_count"] == "1.000000"
    assert payload["rows"][0]["refresh_rank"] == "1.000000"
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_decimal_or_binary_numeric(payload)
    assert module.research_packet_market_event_source_refresh_plan_v2_payload(payload) == payload


def test_report_dataclasses_are_frozen() -> None:
    source = _source()
    report = _report((source,))
    row = report.rows[0]
    summary = report.family_summaries[0]

    with pytest.raises(FrozenInstanceError):
        source.note = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.refresh_priority = "high_refresh"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.coverage_status = "missing"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.coverage_status = "changed"  # type: ignore[misc]


def test_hard_flags_cannot_be_downgraded() -> None:
    report = _report((_source(),))

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.research_packet_market_event_source_refresh_plan_v2_payload(
            {**module.research_packet_market_event_source_refresh_plan_v2_payload(report), "readonly": False},
        )


def test_derived_validation_digest_tampering_is_rejected() -> None:
    report = _report((_source(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, stale_source_count=Decimal("9.000000"))

    payload = module.research_packet_market_event_source_refresh_plan_v2_payload(report)
    tampered_payload = {**payload, "reviewed_source_count": "3.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_market_event_source_refresh_plan_v2_payload(tampered_payload)


@pytest.mark.parametrize(
    ("unsafe_key", "unsafe_value"),
    (
        ("live_hint", "public reference reviewed"),
        ("source_label", "wallet reminder"),
        ("auth_context", "public reference reviewed"),
        ("source_label", "order status"),
        ("network_name", "public reference reviewed"),
        ("database_ref", "public reference reviewed"),
        ("persist_hint", "public reference reviewed"),
        ("signing_key", "public reference reviewed"),
        ("mutation_hint", "public reference reviewed"),
        ("source_label", "buy signal"),
        ("source_label", "sell signal"),
        ("source_label", "trade setup"),
    ),
)
def test_unsafe_public_payload_rejects_keys_and_values(
    unsafe_key: str,
    unsafe_value: str,
) -> None:
    payload: dict[str, Any] = {
        "generated_at": GENERATED_AT.isoformat(),
        "config_version": module.CONFIG_VERSION,
        "reviewed_source_count": "0.000000",
        "stale_source_count": "0.000000",
        "high_refresh_priority_count": "0.000000",
        "source_family_count": "0.000000",
        "coverage_status": "coverage_gap",
        "rows": [],
        "family_summaries": [],
        "reason_codes": [],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        unsafe_key: unsafe_value,
    }

    with pytest.raises(ValueError, match="unsafe"):
        module.research_packet_market_event_source_refresh_plan_v2_payload(payload)


def test_no_unsafe_public_surfaces_or_payload_terms() -> None:
    report = _report((_source(),))
    payload = module.research_packet_market_event_source_refresh_plan_v2_payload(report)
    unsafe_terms = {
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
    }

    public_names = tuple(name for name in dir(module) if not name.startswith("_"))
    assert not [
        name
        for name in public_names
        for term in unsafe_terms
        if term in name.lower()
    ]
    assert not [
        text
        for text in _walk_payload_strings(payload)
        for term in unsafe_terms
        if term in text.lower()
    ]
    assert not hasattr(module, "requests")
    assert not hasattr(module, "socket")
    assert not hasattr(module, "sqlalchemy")

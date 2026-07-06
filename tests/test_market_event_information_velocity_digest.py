from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_event_information_velocity_digest import (
    MarketEventInformationVelocityCategorySummary,
    MarketEventInformationVelocityConfig,
    MarketEventInformationVelocityInput,
    MarketEventInformationVelocityReasonCodeCount,
    MarketEventInformationVelocityReport,
    MarketEventInformationVelocityRow,
    build_market_event_information_velocity_digest,
    market_event_information_velocity_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "NONE"


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


@dataclass(frozen=True)
class SuppliedVelocityShape:
    market_id: str
    category: str
    source_reference: str
    last_market_update_at: datetime | None
    source_published_at: datetime | None
    evidence_refreshed_at: datetime | None
    previous_probability: Decimal
    current_probability: Decimal
    update_count_24h: Decimal
    evidence_refresh_count_24h: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketEventInformationVelocityConfig:
    values = {
        "config_version": "market-event-information-velocity-digest-v0",
        "high_update_frequency_24h": d("8"),
        "max_source_lag_seconds": d("1800"),
        "material_probability_move": d("0.075000"),
        "max_evidence_refresh_age_seconds": d("3600"),
        "low_evidence_refresh_count_24h": d("2"),
    }
    values.update(overrides)
    return MarketEventInformationVelocityConfig(**values)


def market(
    market_id: str = "market-alpha",
    *,
    category: str = "finance.crypto",
    source_reference: str = "official-calendar",
    last_market_update_at: datetime | None = GENERATED_AT - timedelta(minutes=20),
    source_published_at: datetime | None = GENERATED_AT - timedelta(minutes=35),
    evidence_refreshed_at: datetime | None = GENERATED_AT - timedelta(minutes=15),
    previous_probability: Decimal = d("0.480000"),
    current_probability: Decimal = d("0.500000"),
    update_count_24h: Decimal = d("3"),
    evidence_refresh_count_24h: Decimal = d("3"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketEventInformationVelocityInput:
    return MarketEventInformationVelocityInput(
        market_id=market_id,
        category=category,
        source_reference=source_reference,
        last_market_update_at=last_market_update_at,
        source_published_at=source_published_at,
        evidence_refreshed_at=evidence_refreshed_at,
        previous_probability=previous_probability,
        current_probability=current_probability,
        update_count_24h=update_count_24h,
        evidence_refresh_count_24h=evidence_refresh_count_24h,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    markets: tuple[object, ...],
    *,
    cfg: MarketEventInformationVelocityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketEventInformationVelocityReport:
    return build_market_event_information_velocity_digest(
        markets,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_with_decimal_zero_counts_and_no_rows() -> None:
    summary = report(())

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == "market-event-information-velocity-digest-v0"
    assert summary.market_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.blocked_count == ZERO
    assert summary.faster_review_count == ZERO
    assert summary.average_information_velocity_score == ZERO
    assert summary.velocity_status == "blocked"
    assert summary.rows == ()
    assert summary.category_summaries == ()
    assert summary.reason_code_counts == (
        MarketEventInformationVelocityReasonCodeCount(
            reason_code="no_market_event_velocity_inputs",
            count=d("1"),
        ),
    )
    assert summary.reason_codes == ("no_market_event_velocity_inputs",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_velocity_digest_flags_fast_review_and_sorts_deterministically() -> None:
    summary = report(
        (
            market(
                "market-zeta",
                category="sports",
                last_market_update_at=GENERATED_AT - timedelta(minutes=4),
                source_published_at=GENERATED_AT - timedelta(minutes=40),
                evidence_refreshed_at=GENERATED_AT - timedelta(minutes=70),
                previous_probability=d("0.400000"),
                current_probability=d("0.530000"),
                update_count_24h=d("11"),
                evidence_refresh_count_24h=d("1"),
            ),
            market(
                "market-alpha",
                category="finance.crypto",
                last_market_update_at=GENERATED_AT - timedelta(minutes=15),
                source_published_at=GENERATED_AT - timedelta(minutes=20),
                evidence_refreshed_at=GENERATED_AT - timedelta(minutes=20),
                previous_probability=d("0.480000"),
                current_probability=d("0.510000"),
                update_count_24h=d("4"),
                evidence_refresh_count_24h=d("4"),
            ),
            market(
                "market-beta",
                category="sports",
                last_market_update_at=GENERATED_AT - timedelta(minutes=8),
                source_published_at=GENERATED_AT - timedelta(minutes=50),
                evidence_refreshed_at=GENERATED_AT - timedelta(minutes=90),
                previous_probability=d("0.600000"),
                current_probability=d("0.500000"),
                update_count_24h=d("9"),
                evidence_refresh_count_24h=d("1"),
            ),
        ),
    )

    assert summary.market_count == d("3")
    assert summary.pass_count == d("1")
    assert summary.watch_count == d("2")
    assert summary.blocked_count == ZERO
    assert summary.faster_review_count == d("2")
    assert summary.average_information_velocity_score == d("7.333333")
    assert summary.velocity_status == "watch"
    assert tuple(row.market_id for row in summary.rows) == (
        "market-beta",
        "market-zeta",
        "market-alpha",
    )
    beta = summary.rows[0]
    assert beta.source_lag_seconds == d("2520")
    assert beta.evidence_refresh_age_seconds == d("5400")
    assert beta.probability_move == d("-0.100000")
    assert beta.absolute_probability_move == d("0.100000")
    assert beta.information_velocity_score == d("8.666667")
    assert beta.requires_faster_specialist_review is True
    assert beta.reason_codes == (
        "high_update_frequency",
        "source_lag_over_threshold",
        "material_probability_move",
        "evidence_refresh_stale",
        "evidence_refresh_cadence_low",
    )
    assert summary.category_summaries == (
        MarketEventInformationVelocityCategorySummary(
            category="sports",
            market_count=d("2"),
            faster_review_count=d("2"),
            max_information_velocity_score=d("9.000000"),
            average_information_velocity_score=d("8.833334"),
        ),
        MarketEventInformationVelocityCategorySummary(
            category="finance.crypto",
            market_count=d("1"),
            faster_review_count=ZERO,
            max_information_velocity_score=d("4.333333"),
            average_information_velocity_score=d("4.333333"),
        ),
    )
    assert summary.reason_code_counts == (
        MarketEventInformationVelocityReasonCodeCount(
            reason_code="evidence_refresh_cadence_low",
            count=d("2"),
        ),
        MarketEventInformationVelocityReasonCodeCount(
            reason_code="evidence_refresh_stale",
            count=d("2"),
        ),
        MarketEventInformationVelocityReasonCodeCount(
            reason_code="high_update_frequency",
            count=d("2"),
        ),
        MarketEventInformationVelocityReasonCodeCount(
            reason_code="material_probability_move",
            count=d("2"),
        ),
        MarketEventInformationVelocityReasonCodeCount(
            reason_code="source_lag_over_threshold",
            count=d("2"),
        ),
    )


def test_duplicate_market_ids_use_source_reference_tiebreaker_for_sorting() -> None:
    later_source_first = report(
        (
            market("market-duplicate", source_reference="z-specialist-note"),
            market("market-duplicate", source_reference="a-specialist-note"),
        ),
    )
    earlier_source_first = report(
        (
            market("market-duplicate", source_reference="a-specialist-note"),
            market("market-duplicate", source_reference="z-specialist-note"),
        ),
    )

    assert tuple(row.source_reference for row in later_source_first.rows) == (
        "a-specialist-note",
        "z-specialist-note",
    )
    assert tuple(row.source_reference for row in earlier_source_first.rows) == (
        "a-specialist-note",
        "z-specialist-note",
    )


def test_missing_timestamps_block_and_probability_cadence_reasons_are_independent() -> None:
    summary = report(
        (
            market(
                "market-missing",
                last_market_update_at=None,
                source_published_at=None,
                evidence_refreshed_at=None,
                previous_probability=d("0.500000"),
                current_probability=d("0.500000"),
                update_count_24h=d("0"),
                evidence_refresh_count_24h=d("0"),
            ),
        ),
    )

    row = summary.rows[0]
    assert row.velocity_status == "blocked"
    assert row.source_lag_seconds is None
    assert row.evidence_refresh_age_seconds is None
    assert row.information_velocity_score == d("0.000000")
    assert row.requires_faster_specialist_review is True
    assert row.reason_codes == (
        "missing_market_update_at",
        "missing_source_published_at",
        "missing_evidence_refreshed_at",
        "evidence_refresh_cadence_low",
    )
    assert summary.blocked_count == d("1")
    assert summary.velocity_status == "blocked"


def test_payload_redacts_sensitive_source_reference_and_keeps_decimal_strings() -> None:
    summary = report(
        (
            market(
                "market-redacted",
                source_reference="https://vendor.example/feed?token=secret-123&api_key=abc",
                previous_probability=d("0.300000"),
                current_probability=d("0.390000"),
                update_count_24h=d("8"),
                evidence_refresh_count_24h=d("1"),
            ),
        ),
    )

    row = summary.rows[0]
    payload = market_event_information_velocity_payload(summary)
    encoded = json.dumps(payload, sort_keys=True)

    assert row.source_reference == "[redacted]"
    assert payload["market_count"] == "1"
    assert payload["rows"][0]["source_reference"] == "[redacted]"
    assert payload["rows"][0]["probability_move"] == "0.090000"
    assert payload["rows"][0]["information_velocity_score"] == "7.333333"
    assert "secret-123" not in encoded
    assert "api_key" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_report_has_payload_bound_derived_validation_digest() -> None:
    summary = report((market("market-alpha"),))

    assert len(summary.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in summary.derived_validation_digest
    )

    payload = market_event_information_velocity_payload(summary)
    assert payload["derived_validation_digest"] == summary.derived_validation_digest

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_event_information_velocity_payload(missing_digest)

    tampered_payload = dict(payload)
    tampered_payload["market_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        market_event_information_velocity_payload(tampered_payload)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(summary, derived_validation_digest="0" * 64)


def test_public_payload_rejects_live_auth_wallet_order_network_database_persist_surface() -> None:
    payload = market_event_information_velocity_payload(report((market("market-alpha"),)))

    unsafe_keys = (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_client",
        "database_url",
        "persist_path",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            market_event_information_velocity_payload(unsafe_payload)

    unsafe_values = (
        "live mode enabled",
        "auth token configured",
        "wallet transfer configured",
        "submit order configured",
        "network request configured",
        "database writer configured",
        "persist report configured",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["config_version"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe"):
            market_event_information_velocity_payload(unsafe_payload)

    with pytest.raises(ValueError, match="unsafe"):
        market(source_reference="network-feed")


def test_public_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    summary = report((market("market-alpha"),))
    values = (
        config(),
        market("market-input"),
        summary.rows[0],
        summary.category_summaries[0],
        summary.reason_code_counts[0],
        summary,
    )

    for value in values:
        assert is_dataclass(value)
        _assert_decimal_only_public_numbers(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.rows[0], paper_only=False)

    with pytest.raises(ValueError, match="update_count_24h must be a Decimal"):
        market(update_count_24h=_DecimalSubclass("3"))


def test_validation_rejects_floats_nonfinite_bad_times_flags_and_inconsistent_reports() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" market-event-information-velocity-digest-v0")
    with pytest.raises(ValueError, match="high_update_frequency_24h"):
        config(high_update_frequency_24h=d("0"))
    with pytest.raises(ValueError, match="material_probability_move"):
        config(material_probability_move=d("1.000001"))
    with pytest.raises(ValueError, match="max_source_lag_seconds"):
        config(max_source_lag_seconds=_DecimalSubclass("1800"))
    with pytest.raises(ValueError, match="previous_probability"):
        market(previous_probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="current_probability"):
        market(current_probability=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        report((market(),), generated_at=_DatetimeSubclass(2026, 7, 2, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report((market(),), generated_at=datetime(2026, 7, 2, 15, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (market(),),
            generated_at=datetime(2026, 7, 2, 15, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="last_market_update_at"):
        report((market(last_market_update_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="source_published_at"):
        market(source_published_at=datetime(2026, 7, 2, 14, 0))
    with pytest.raises(ValueError, match="source_published_at"):
        market(
            source_published_at=datetime(
                2026,
                7,
                2,
                14,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        report((market(paper_only=False),))
    with pytest.raises(ValueError, match="report_only"):
        report((market(report_only=False),))
    with pytest.raises(ValueError, match="readonly"):
        report((market(readonly=False),))

    summary = report((market("market-alpha"), market("market-beta")))
    with pytest.raises(ValueError, match="market_count"):
        replace(summary, market_count=d("3"))
    with pytest.raises(ValueError, match="average_information_velocity_score"):
        replace(summary, average_information_velocity_score=d("1"))
    with pytest.raises(ValueError, match="velocity_status"):
        replace(summary, velocity_status="blocked")
    with pytest.raises(ValueError, match="count"):
        MarketEventInformationVelocityReasonCodeCount(
            reason_code="event_information_velocity_clear",
            count=_IntSubclass(1),
        )


def test_accepts_supplied_shape_converts_to_utc_and_freezes_public_dataclasses() -> None:
    summary = report(
        (
            SuppliedVelocityShape(
                market_id="market-supplied",
                category="finance.crypto",
                source_reference="specialist-note",
                last_market_update_at=datetime(
                    2026,
                    7,
                    2,
                    8,
                    40,
                    tzinfo=timezone(timedelta(hours=-6)),
                ),
                source_published_at=datetime(
                    2026,
                    7,
                    2,
                    8,
                    35,
                    tzinfo=timezone(timedelta(hours=-6)),
                ),
                evidence_refreshed_at=datetime(
                    2026,
                    7,
                    2,
                    8,
                    50,
                    tzinfo=timezone(timedelta(hours=-6)),
                ),
                previous_probability=d("0.480000"),
                current_probability=d("0.500000"),
                update_count_24h=d("3"),
                evidence_refresh_count_24h=d("3"),
            ),
        ),
    )

    row = summary.rows[0]
    assert row.last_market_update_at == datetime(2026, 7, 2, 14, 40, tzinfo=UTC)
    assert row.source_published_at == datetime(2026, 7, 2, 14, 35, tzinfo=UTC)
    assert row.evidence_refreshed_at == datetime(2026, 7, 2, 14, 50, tzinfo=UTC)
    assert row.source_lag_seconds == d("300")
    with pytest.raises(FrozenInstanceError):
        summary.velocity_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.velocity_status = "blocked"  # type: ignore[misc]


def test_static_forbidden_surface_terms_are_absent_from_owned_module() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_event_information_velocity_digest.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "psycopg",
        "postgres",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "network",
        "database",
        "persist",
        "wallet",
        "broker",
        "order",
        "signing",
        "auth",
        "trade",
        "advice",
        "account",
        "open(",
    )

    assert all(term not in source for term in forbidden_terms)


def _assert_decimal_only_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, tuple):
        for item in value:
            _assert_decimal_only_public_numbers(item)
        return
    if is_dataclass(value):
        for field_name in value.__dataclass_fields__:
            _assert_decimal_only_public_numbers(getattr(value, field_name))
        return
    assert not isinstance(value, (float, int))


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

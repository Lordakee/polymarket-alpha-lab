from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_event_update_freshness_digest import (
    MarketEventUpdateFreshnessConfig,
    MarketEventUpdateFreshnessEventInput,
    MarketEventUpdateFreshnessReasonCodeCount,
    MarketEventUpdateFreshnessReport,
    MarketEventUpdateFreshnessRow,
    MarketEventUpdateFreshnessStatusCount,
    build_market_event_update_freshness_digest,
    market_event_update_freshness_payload,
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


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


@dataclass(frozen=True)
class SuppliedEventShape:
    event_slug: str
    category: str
    update_family: str | None
    event_updated_at: datetime | None
    source_acknowledged_at: datetime | None
    probability_captured_at: datetime | None
    close_time: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketEventUpdateFreshnessConfig:
    values = {
        "config_version": "market-event-update-freshness-digest-v0",
        "max_event_update_age_seconds": d("3600"),
        "max_source_acknowledgement_age_seconds": d("7200"),
        "max_probability_context_age_seconds": d("1800"),
        "close_pressure_window_seconds": d("900"),
        "required_update_families": ("metadata", "probability", "resolution"),
    }
    values.update(overrides)
    return MarketEventUpdateFreshnessConfig(**values)


def event(
    event_slug: str = "event-alpha",
    *,
    category: str = "finance.crypto",
    update_family: str | None = "metadata",
    event_updated_at: datetime | None = GENERATED_AT - timedelta(minutes=20),
    source_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=25),
    probability_captured_at: datetime | None = GENERATED_AT - timedelta(minutes=10),
    close_time: datetime | None = GENERATED_AT + timedelta(hours=4),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketEventUpdateFreshnessEventInput:
    return MarketEventUpdateFreshnessEventInput(
        event_slug=event_slug,
        category=category,
        update_family=update_family,
        event_updated_at=event_updated_at,
        source_acknowledged_at=source_acknowledged_at,
        probability_captured_at=probability_captured_at,
        close_time=close_time,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    events: tuple[object, ...],
    *,
    cfg: MarketEventUpdateFreshnessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketEventUpdateFreshnessReport:
    return build_market_event_update_freshness_digest(
        events,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_with_zero_decimal_counts_and_no_rows() -> None:
    summary = report(())

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == "market-event-update-freshness-digest-v0"
    assert summary.event_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.blocked_count == ZERO
    assert summary.close_pressure_count == ZERO
    assert summary.missing_update_family_count == ZERO
    assert summary.stale_probability_context_count == ZERO
    assert summary.average_event_update_age_seconds is None
    assert summary.average_source_acknowledgement_age_seconds is None
    assert summary.freshness_status == "blocked"
    assert summary.rows == ()
    assert summary.category_status_counts == ()
    assert summary.reason_code_counts == (
        MarketEventUpdateFreshnessReasonCodeCount(
            reason_code="no_market_event_updates",
            count=d("1"),
        ),
    )
    assert summary.reason_codes == ("no_market_event_updates",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_fresh_updates_pass_and_summarize_decimal_ages_and_rollups() -> None:
    summary = report(
        (
            event(
                "event-beta",
                category="politics",
                update_family="probability",
                event_updated_at=GENERATED_AT - timedelta(minutes=30),
                source_acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                probability_captured_at=GENERATED_AT - timedelta(minutes=5),
            ),
            event(
                "event-alpha",
                category="finance.crypto",
                update_family="metadata",
                event_updated_at=GENERATED_AT - timedelta(minutes=10),
                source_acknowledged_at=GENERATED_AT - timedelta(minutes=40),
                probability_captured_at=GENERATED_AT - timedelta(minutes=15),
            ),
        ),
    )

    assert summary.event_count == d("2")
    assert summary.pass_count == d("2")
    assert summary.watch_count == ZERO
    assert summary.blocked_count == ZERO
    assert summary.close_pressure_count == ZERO
    assert summary.missing_update_family_count == ZERO
    assert summary.stale_probability_context_count == ZERO
    assert summary.average_event_update_age_seconds == d("1200")
    assert summary.average_source_acknowledgement_age_seconds == d("1800")
    assert summary.freshness_status == "pass"
    assert tuple(row.event_slug for row in summary.rows) == ("event-alpha", "event-beta")
    assert summary.rows[0].event_update_age_seconds == d("600")
    assert summary.rows[0].source_acknowledgement_age_seconds == d("2400")
    assert summary.rows[0].probability_context_age_seconds == d("900")
    assert summary.rows[0].close_time_pressure_seconds == d("14400")
    assert summary.category_status_counts == (
        MarketEventUpdateFreshnessStatusCount(
            category="finance.crypto",
            freshness_status="pass",
            count=d("1"),
        ),
        MarketEventUpdateFreshnessStatusCount(
            category="politics",
            freshness_status="pass",
            count=d("1"),
        ),
    )
    assert summary.reason_code_counts == (
        MarketEventUpdateFreshnessReasonCodeCount(
            reason_code="market_event_updates_fresh",
            count=d("1"),
        ),
    )


def test_stale_update_age_and_source_acknowledgement_watch_reasons() -> None:
    summary = report(
        (
            event(
                "event-stale",
                event_updated_at=GENERATED_AT - timedelta(hours=2),
                source_acknowledged_at=GENERATED_AT - timedelta(hours=3),
            ),
        ),
    )

    row = summary.rows[0]
    assert row.freshness_status == "watch"
    assert row.event_update_age_seconds == d("7200")
    assert row.source_acknowledgement_age_seconds == d("10800")
    assert row.reason_codes == (
        "stale_event_update_age",
        "stale_source_acknowledgement_age",
    )
    assert summary.watch_count == d("1")
    assert summary.freshness_status == "watch"
    assert summary.reason_code_counts == (
        MarketEventUpdateFreshnessReasonCodeCount(
            reason_code="stale_event_update_age",
            count=d("1"),
        ),
        MarketEventUpdateFreshnessReasonCodeCount(
            reason_code="stale_source_acknowledgement_age",
            count=d("1"),
        ),
    )


def test_missing_update_family_blocks_and_counts_required_family_gap() -> None:
    summary = report(
        (
            event("event-family", update_family=None),
        ),
    )

    row = summary.rows[0]
    assert row.freshness_status == "blocked"
    assert row.missing_required_update_families == (
        "probability",
        "resolution",
        "metadata",
    )
    assert "missing_update_family" in row.reason_codes
    assert summary.blocked_count == d("1")
    assert summary.missing_update_family_count == d("1")
    assert summary.freshness_status == "blocked"


def test_stale_probability_context_watches_independently() -> None:
    summary = report(
        (
            event(
                "event-context",
                probability_captured_at=GENERATED_AT - timedelta(minutes=45),
            ),
        ),
    )

    row = summary.rows[0]
    assert row.freshness_status == "watch"
    assert row.probability_context_age_seconds == d("2700")
    assert row.reason_codes == ("stale_probability_context",)
    assert summary.stale_probability_context_count == d("1")
    assert summary.freshness_status == "watch"


def test_close_time_pressure_watches_when_event_is_near_close() -> None:
    summary = report(
        (
            event(
                "event-close",
                close_time=GENERATED_AT + timedelta(minutes=10),
            ),
        ),
    )

    row = summary.rows[0]
    assert row.freshness_status == "watch"
    assert row.close_time_pressure_seconds == d("600")
    assert row.close_time_pressure is True
    assert row.reason_codes == ("close_time_pressure",)
    assert summary.close_pressure_count == d("1")
    assert summary.freshness_status == "watch"


def test_rows_rollups_and_reasons_sort_deterministically() -> None:
    summary = report(
        (
            event(
                "event-zeta",
                category="sports",
                event_updated_at=GENERATED_AT - timedelta(hours=2),
            ),
            event(
                "event-alpha",
                category="finance.crypto",
                probability_captured_at=GENERATED_AT - timedelta(minutes=45),
            ),
            event(
                "event-beta",
                category="finance.crypto",
                update_family=None,
            ),
            event(
                "event-gamma",
                category="sports",
                event_updated_at=GENERATED_AT - timedelta(hours=3),
            ),
        ),
    )

    assert tuple(row.event_slug for row in summary.rows) == (
        "event-beta",
        "event-alpha",
        "event-gamma",
        "event-zeta",
    )
    assert summary.category_status_counts == (
        MarketEventUpdateFreshnessStatusCount(
            category="finance.crypto",
            freshness_status="blocked",
            count=d("1"),
        ),
        MarketEventUpdateFreshnessStatusCount(
            category="finance.crypto",
            freshness_status="watch",
            count=d("1"),
        ),
        MarketEventUpdateFreshnessStatusCount(
            category="sports",
            freshness_status="watch",
            count=d("2"),
        ),
    )
    assert summary.reason_code_counts == (
        MarketEventUpdateFreshnessReasonCodeCount(
            reason_code="stale_event_update_age",
            count=d("2"),
        ),
        MarketEventUpdateFreshnessReasonCodeCount(
            reason_code="missing_update_family",
            count=d("1"),
        ),
        MarketEventUpdateFreshnessReasonCodeCount(
            reason_code="stale_probability_context",
            count=d("1"),
        ),
    )
    assert summary.reason_codes == (
        "missing_update_family",
        "stale_event_update_age",
        "stale_probability_context",
    )


def test_mixed_missing_and_stale_row_reasons_sort_canonically() -> None:
    summary = report(
        (
            event(
                "event-mixed",
                update_family=None,
                event_updated_at=GENERATED_AT - timedelta(hours=2),
                source_acknowledged_at=None,
                probability_captured_at=None,
            ),
        ),
    )

    row = summary.rows[0]
    assert row.freshness_status == "blocked"
    assert row.reason_codes == (
        "missing_update_family",
        "missing_source_acknowledgement_at",
        "missing_probability_context",
        "stale_event_update_age",
    )
    assert summary.reason_codes == row.reason_codes


def test_duplicate_slug_rows_sort_with_stable_field_tiebreakers() -> None:
    summary = report(
        (
            event(
                "event-duplicate",
                category="finance.crypto",
                update_family="resolution",
                event_updated_at=GENERATED_AT - timedelta(minutes=40),
            ),
            event(
                "event-duplicate",
                category="finance.crypto",
                update_family="metadata",
                event_updated_at=GENERATED_AT - timedelta(minutes=20),
            ),
            event(
                "event-duplicate",
                category="finance.crypto",
                update_family="probability",
                event_updated_at=GENERATED_AT - timedelta(minutes=30),
            ),
        ),
    )

    assert tuple(row.update_family for row in summary.rows) == (
        "metadata",
        "probability",
        "resolution",
    )
    assert tuple(row.event_update_age_seconds for row in summary.rows) == (
        d("1200"),
        d("1800"),
        d("2400"),
    )


def test_json_payload_uses_decimal_strings_and_no_float_values() -> None:
    summary = report(
        (
            event("event-alpha"),
            event(
                "event-close",
                close_time=GENERATED_AT + timedelta(minutes=10),
            ),
        ),
    )

    payload = market_event_update_freshness_payload(summary)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["event_count"] == "2"
    assert payload["average_event_update_age_seconds"] == "1200.000000"
    assert payload["rows"][0]["close_time_pressure_seconds"] == "600"
    assert payload["rows"][1]["event_update_age_seconds"] == "1200"
    assert "2.0" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_report_carries_derived_validation_digest_and_payload_serializes_it() -> None:
    summary = report(
        (
            event("event-alpha"),
            event(
                "event-close",
                close_time=GENERATED_AT + timedelta(minutes=10),
            ),
        ),
    )

    assert summary.derived_validation_digest == (
        (
            "blocked_count",
            "0",
        ),
        (
            "category_status_total",
            "2",
        ),
        (
            "close_pressure_count",
            "1",
        ),
        (
            "event_count",
            "2",
        ),
        (
            "hard_flags",
            "paper_only/report_only/readonly",
        ),
        (
            "reason_code_total",
            "1",
        ),
        (
            "row_count",
            "2",
        ),
        (
            "status_total",
            "2",
        ),
    )

    payload = market_event_update_freshness_payload(summary)

    assert payload["derived_validation_digest"] == [
        ["blocked_count", "0"],
        ["category_status_total", "2"],
        ["close_pressure_count", "1"],
        ["event_count", "2"],
        ["hard_flags", "paper_only/report_only/readonly"],
        ["reason_code_total", "1"],
        ["row_count", "2"],
        ["status_total", "2"],
    ]


def test_payload_rejects_unsafe_public_surface_keys_and_values() -> None:
    summary = report((event("event-alpha"),))
    payload = market_event_update_freshness_payload(summary)

    for unsafe_payload in (
        payload | {"live_mode": True},
        payload | {"operator_auth_token": "redacted"},
        payload | {"wallet_id": "0xabc"},
        payload | {"order_id": "123"},
        payload | {"network_endpoint": "http://example.test"},
        payload | {"database_row_id": "db-1"},
        payload | {"persist_target": "disk"},
        payload | {"rows": [payload["rows"][0] | {"note": "place live order"}]},
    ):
        with pytest.raises(ValueError, match="unsafe"):
            market_event_update_freshness_payload(unsafe_payload)


def test_validation_errors_reject_bad_types_times_flags_and_inconsistent_reports() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" market-event-update-freshness-digest-v0")
    with pytest.raises(ValueError, match="max_event_update_age_seconds"):
        config(max_event_update_age_seconds=d("0"))
    with pytest.raises(ValueError, match="max_event_update_age_seconds"):
        config(max_event_update_age_seconds=_DecimalSubclass("3600"))
    with pytest.raises(ValueError, match="required_update_families"):
        config(required_update_families=("metadata", "metadata"))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(),), generated_at=_DatetimeSubclass(2026, 7, 2, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(),), generated_at=datetime(2026, 7, 2, 15, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        report(
            (event(),),
            generated_at=datetime(2026, 7, 2, 15, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="event_slug"):
        event(event_slug=" event-alpha")
    with pytest.raises(ValueError, match="category"):
        event(category="")
    with pytest.raises(ValueError, match="event_updated_at"):
        report((event(event_updated_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="source_acknowledged_at"):
        event(source_acknowledged_at=datetime(2026, 7, 2, 14, 0))
    with pytest.raises(ValueError, match="paper_only"):
        report((event(paper_only=False),))
    with pytest.raises(ValueError, match="report_only"):
        report((event(report_only=False),))
    with pytest.raises(ValueError, match="readonly"):
        report((event(readonly=False),))

    summary = report((event("event-alpha"), event("event-beta")))
    with pytest.raises(ValueError, match="event_count"):
        replace(summary, event_count=d("3"))
    with pytest.raises(ValueError, match="average_event_update_age_seconds"):
        replace(summary, average_event_update_age_seconds=d("1"))
    with pytest.raises(ValueError, match="freshness_status"):
        replace(summary, freshness_status="blocked")


def test_accepts_supplied_shape_and_freezes_public_dataclasses() -> None:
    summary = report(
        (
            SuppliedEventShape(
                event_slug="event-supplied",
                category="finance.crypto",
                update_family="metadata",
                event_updated_at=datetime(
                    2026,
                    7,
                    2,
                    8,
                    40,
                    tzinfo=timezone(timedelta(hours=-6)),
                ),
                source_acknowledged_at=datetime(
                    2026,
                    7,
                    2,
                    8,
                    45,
                    tzinfo=timezone(timedelta(hours=-6)),
                ),
                probability_captured_at=datetime(
                    2026,
                    7,
                    2,
                    8,
                    50,
                    tzinfo=timezone(timedelta(hours=-6)),
                ),
                close_time=datetime(2026, 7, 2, 19, 0, tzinfo=UTC),
            ),
        ),
    )

    row = summary.rows[0]
    assert row.event_updated_at == datetime(2026, 7, 2, 14, 40, tzinfo=UTC)
    assert row.source_acknowledged_at == datetime(2026, 7, 2, 14, 45, tzinfo=UTC)
    assert row.probability_captured_at == datetime(2026, 7, 2, 14, 50, tzinfo=UTC)
    assert row.event_update_age_seconds == d("1200")
    with pytest.raises(FrozenInstanceError):
        summary.freshness_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.freshness_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="count"):
        MarketEventUpdateFreshnessReasonCodeCount(
            reason_code="market_event_updates_fresh",
            count=_IntSubclass(1),
        )


def test_static_forbidden_surface_terms_are_absent_from_owned_module() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_event_update_freshness_digest.py"
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
        "wallet",
        "broker",
        "order",
        "signing",
        "auth",
        "trade",
        "advice",
        "open(",
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

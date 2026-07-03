from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.market_outcome_freshness_recheck_exception_report import (
    MarketOutcomeFreshnessRecheckExceptionConfig,
    MarketOutcomeFreshnessRecheckExceptionInput,
    MarketOutcomeFreshnessRecheckExceptionReport,
    MarketOutcomeFreshnessRecheckExceptionRow,
    build_market_outcome_freshness_recheck_exception_report,
    market_outcome_freshness_recheck_exception_report_json_payload,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
CONFIG = MarketOutcomeFreshnessRecheckExceptionConfig(
    config_version="market-outcome-freshness-recheck-exception-report-v1",
    stale_outcome_after_seconds=Decimal("900"),
    category_gap_after_seconds=Decimal("1800"),
    overdue_recheck_after_seconds=Decimal("3600"),
    repeated_overdue_recheck_count=Decimal("2"),
    warning_exception_count=Decimal("1"),
    critical_exception_count=Decimal("3"),
)


def observation(**overrides: object) -> MarketOutcomeFreshnessRecheckExceptionInput:
    values: dict[str, object] = {
        "condition_id": "condition-alpha",
        "market_slug": "alpha-market",
        "category": "Politics",
        "outcome_timestamp": GENERATED_AT - timedelta(minutes=5),
        "official_source_url": "https://example.test/source",
        "queue_acknowledged_at": GENERATED_AT - timedelta(minutes=2),
        "category_freshness_checked_at": GENERATED_AT - timedelta(minutes=8),
        "latest_recheck_due_at": GENERATED_AT - timedelta(minutes=10),
        "recheck_completed_at": GENERATED_AT - timedelta(minutes=1),
        "overdue_recheck_count": Decimal("0"),
    }
    values.update(overrides)
    return MarketOutcomeFreshnessRecheckExceptionInput(**values)


def test_build_report_identifies_exception_focus_and_rollups() -> None:
    fresh = observation(condition_id="condition-fresh", market_slug="fresh-market")
    stale = observation(
        condition_id="condition-stale",
        market_slug="stale-market",
        outcome_timestamp=GENERATED_AT - timedelta(minutes=20),
    )
    missing_source = observation(
        condition_id="condition-source",
        market_slug="missing-source-market",
        official_source_url=None,
    )
    unacknowledged = observation(
        condition_id="condition-queue",
        market_slug="queue-market",
        queue_acknowledged_at=None,
    )
    category_gap = observation(
        condition_id="condition-category",
        market_slug="category-market",
        category_freshness_checked_at=GENERATED_AT - timedelta(hours=2),
    )
    repeated_overdue = observation(
        condition_id="condition-overdue",
        market_slug="overdue-market",
        outcome_timestamp=GENERATED_AT - timedelta(hours=2),
        latest_recheck_due_at=GENERATED_AT - timedelta(hours=2),
        recheck_completed_at=None,
        overdue_recheck_count=Decimal("2"),
    )

    report = build_market_outcome_freshness_recheck_exception_report(
        (fresh, stale, missing_source, unacknowledged, category_gap, repeated_overdue),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == GENERATED_AT
    assert report.market_count == Decimal("6")
    assert report.exception_market_count == Decimal("5")
    assert report.clean_market_count == Decimal("1")
    assert report.exception_market_ratio == Decimal("0.833333")
    assert report.highest_severity == "critical"
    assert report.severity_counts == {
        "none": Decimal("1"),
        "warning": Decimal("2"),
        "critical": Decimal("3"),
    }
    assert report.exception_type_counts == {
        "stale_outcome_timestamp": Decimal("2"),
        "missing_official_source": Decimal("1"),
        "unacknowledged_queue": Decimal("1"),
        "unresolved_category_freshness_gap": Decimal("1"),
        "repeated_overdue_recheck": Decimal("1"),
    }

    rows_by_condition = {row.condition_id: row for row in report.rows}
    assert rows_by_condition["condition-fresh"].exception_types == ()
    assert rows_by_condition["condition-fresh"].severity == "none"
    assert rows_by_condition["condition-stale"].exception_types == (
        "stale_outcome_timestamp",
    )
    assert rows_by_condition["condition-stale"].outcome_age_seconds == Decimal("1200")
    assert rows_by_condition["condition-source"].exception_types == (
        "missing_official_source",
    )
    assert rows_by_condition["condition-queue"].exception_types == (
        "unacknowledged_queue",
    )
    assert rows_by_condition["condition-category"].exception_types == (
        "unresolved_category_freshness_gap",
    )
    assert (
        rows_by_condition["condition-category"].category_freshness_gap_seconds
        == Decimal("7200")
    )
    assert rows_by_condition["condition-overdue"].exception_types == (
        "stale_outcome_timestamp",
        "repeated_overdue_recheck",
    )
    assert rows_by_condition["condition-overdue"].severity == "critical"
    assert rows_by_condition["condition-overdue"].recheck_overdue_seconds == Decimal(
        "7200",
    )


def test_report_rows_are_deterministically_sorted() -> None:
    report = build_market_outcome_freshness_recheck_exception_report(
        (
            observation(condition_id="condition-b", market_slug="same-slug"),
            observation(condition_id="condition-a", market_slug="same-slug"),
            observation(condition_id="condition-c", market_slug="alpha-slug"),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert tuple(row.condition_id for row in report.rows) == (
        "condition-c",
        "condition-a",
        "condition-b",
    )


@pytest.mark.parametrize(
    "public_dataclass",
    (
        MarketOutcomeFreshnessRecheckExceptionConfig,
        MarketOutcomeFreshnessRecheckExceptionInput,
        MarketOutcomeFreshnessRecheckExceptionRow,
        MarketOutcomeFreshnessRecheckExceptionReport,
    ),
)
def test_public_dataclasses_are_frozen(public_dataclass: type[object]) -> None:
    assert is_dataclass(public_dataclass)
    assert public_dataclass.__dataclass_params__.frozen is True

    report = build_market_outcome_freshness_recheck_exception_report(
        (observation(),),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.market_count = Decimal("99")  # type: ignore[misc]


def test_public_dataclasses_hard_validate_readonly_report_flags() -> None:
    obs = observation()
    report = build_market_outcome_freshness_recheck_exception_report(
        (obs,),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )
    row = report.rows[0]

    for value in (CONFIG, obs, row, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    for value in (CONFIG, obs, row, report):
        with pytest.raises(ValueError, match="paper_only"):
            replace(value, paper_only=False)
        with pytest.raises(ValueError, match="report_only"):
            replace(value, report_only=False)
        with pytest.raises(ValueError, match="readonly"):
            replace(value, readonly=False)


def test_public_numerics_are_decimal_not_float_or_int() -> None:
    report = build_market_outcome_freshness_recheck_exception_report(
        (
            observation(condition_id="condition-clean"),
            observation(
                condition_id="condition-stale",
                outcome_timestamp=GENERATED_AT - timedelta(hours=1),
            ),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    public_values = [
        report.market_count,
        report.exception_market_count,
        report.clean_market_count,
        report.exception_market_ratio,
        report.severity_counts["none"],
        report.exception_type_counts["stale_outcome_timestamp"],
        report.rows[0].outcome_age_seconds,
        report.rows[0].overdue_recheck_count,
        report.rows[1].outcome_age_seconds,
    ]
    assert public_values
    for value in public_values:
        assert type(value) is Decimal

    with pytest.raises(ValueError, match="Decimal"):
        MarketOutcomeFreshnessRecheckExceptionInput(
            condition_id="condition-float",
            market_slug="float-market",
            category="Politics",
            outcome_timestamp=GENERATED_AT,
            official_source_url="https://example.test/source",
            queue_acknowledged_at=GENERATED_AT,
            category_freshness_checked_at=GENERATED_AT,
            latest_recheck_due_at=GENERATED_AT,
            recheck_completed_at=GENERATED_AT,
            overdue_recheck_count=1.0,  # type: ignore[arg-type]
        )


def test_datetimes_are_normalized_to_utc_and_naive_datetimes_are_rejected() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_market_outcome_freshness_recheck_exception_report(
        (
            observation(
                outcome_timestamp=datetime(2026, 7, 1, 7, 55, tzinfo=eastern),
                queue_acknowledged_at=datetime(2026, 7, 1, 7, 58, tzinfo=eastern),
            ),
        ),
        config=CONFIG,
        generated_at=datetime(2026, 7, 1, 8, 0, tzinfo=eastern),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].outcome_timestamp == datetime(2026, 7, 1, 11, 55, tzinfo=UTC)
    assert report.rows[0].queue_acknowledged_at == datetime(
        2026,
        7,
        1,
        11,
        58,
        tzinfo=UTC,
    )

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(outcome_timestamp=datetime(2026, 7, 1, 12, 0))


def test_future_observation_times_are_rejected_deterministically() -> None:
    with pytest.raises(ValueError, match="outcome_age_seconds must be nonnegative"):
        build_market_outcome_freshness_recheck_exception_report(
            (observation(outcome_timestamp=GENERATED_AT + timedelta(seconds=1)),),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_json_payload_helper_serializes_decimals_as_strings_and_datetimes_as_iso() -> None:
    report = build_market_outcome_freshness_recheck_exception_report(
        (
            observation(
                condition_id="condition-json",
                outcome_timestamp=GENERATED_AT - timedelta(hours=1),
            ),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    payload = market_outcome_freshness_recheck_exception_report_json_payload(report)
    json.dumps(payload)

    numeric_strings = [
        payload["market_count"],
        payload["exception_market_ratio"],
        payload["severity_counts"]["warning"],
        payload["rows"][0]["outcome_age_seconds"],
        payload["rows"][0]["exception_count"],
    ]
    assert all(type(value) is str for value in numeric_strings)
    assert "3600.0" not in numeric_strings
    assert payload["generated_at"] == "2026-07-01T12:00:00+00:00"
    assert payload["market_count"] == "1"
    assert payload["exception_market_ratio"] == "1.000000"
    assert payload["rows"][0]["outcome_age_seconds"] == "3600"
    assert payload["rows"][0]["outcome_timestamp"] == "2026-07-01T11:00:00+00:00"
    assert payload["rows"][0]["exception_types"] == [
        "stale_outcome_timestamp",
    ]

    def assert_no_float(value: object) -> None:
        if isinstance(value, float):
            raise AssertionError(f"float leaked into payload: {value!r}")
        if isinstance(value, dict):
            for child in value.values():
                assert_no_float(child)
        elif isinstance(value, list):
            for child in value:
                assert_no_float(child)

    assert_no_float(payload)


def test_input_surface_excludes_io_and_trading_advice_capabilities() -> None:
    forbidden_terms = (
        "db",
        "database",
        "network",
        "file",
        "path",
        "wallet",
        "broker",
        "order",
        "submit",
        "cancel",
        "sign",
        "trade",
        "advice",
        "auth",
    )
    public_names = {
        name
        for obj in (
            MarketOutcomeFreshnessRecheckExceptionConfig,
            MarketOutcomeFreshnessRecheckExceptionInput,
            MarketOutcomeFreshnessRecheckExceptionRow,
            MarketOutcomeFreshnessRecheckExceptionReport,
        )
        for name in obj.__dataclass_fields__
    } | {
        build_market_outcome_freshness_recheck_exception_report.__name__,
        market_outcome_freshness_recheck_exception_report_json_payload.__name__,
    }

    assert not {
        name
        for name in public_names
        for forbidden_term in forbidden_terms
        if forbidden_term in name.lower()
    }

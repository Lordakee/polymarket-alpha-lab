from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_outcome_freshness_recheck_health_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config():
    report_module = module()
    return report_module.MarketOutcomeFreshnessRecheckHealthConfig(
        config_version="market-outcome-freshness-recheck-health-test-v0",
        stale_freshness_after_seconds=d("3600.000000"),
        max_unresolved_outcome_gap=d("0.000000"),
        close_time_pressure_within_seconds=d("1800.000000"),
    )


def row(
    market_id: str,
    *,
    market_slug: str = "market-alpha",
    outcome_id: str = "yes",
    recheck_requested_at: datetime = datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
    market_closes_at: datetime = datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
    freshness_checked_at: datetime | None = datetime(2026, 7, 2, 11, 30, tzinfo=UTC),
    expected_outcome_count: Decimal = d("1.000000"),
    resolved_outcome_count: Decimal = d("1.000000"),
):
    report_module = module()
    return report_module.MarketOutcomeFreshnessRecheckHealthInput(
        market_id=market_id,
        market_slug=market_slug,
        outcome_id=outcome_id,
        recheck_requested_at=recheck_requested_at,
        market_closes_at=market_closes_at,
        freshness_checked_at=freshness_checked_at,
        expected_outcome_count=expected_outcome_count,
        resolved_outcome_count=resolved_outcome_count,
    )


def build_report(*rows):
    report_module = module()
    return report_module.build_market_outcome_freshness_recheck_health_report(
        rows,
        config=config(),
        generated_at=GENERATED_AT,
    )


def assert_json_ready_without_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if isinstance(value, dict):
        for nested_value in value.values():
            assert_json_ready_without_floats(nested_value)
        return
    if isinstance(value, (list, tuple)):
        for nested_value in value:
            assert_json_ready_without_floats(nested_value)
        return
    assert value is None or isinstance(value, (str, bool))


def test_empty_input_builds_empty_health_report() -> None:
    report = build_report()

    assert report.health_status == "empty"
    assert report.row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.stale_freshness_ratio == d("0.000000")
    assert report.unresolved_outcome_gap_ratio == d("0.000000")
    assert report.close_time_pressure_ratio == d("0.000000")
    assert report.reason_codes == ("no_market_outcome_freshness_recheck_rows",)
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rows_are_classified_and_sorted_deterministically() -> None:
    report = build_report(
        row(
            "market-pass",
            market_slug="z-pass",
            market_closes_at=datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
        ),
        row(
            "market-stale",
            market_slug="b-stale",
            freshness_checked_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
        ),
        row(
            "market-gap",
            market_slug="a-gap",
            expected_outcome_count=d("2.000000"),
            resolved_outcome_count=d("1.000000"),
        ),
        row(
            "market-close",
            market_slug="c-close",
            market_closes_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
        ),
        row(
            "market-missing",
            market_slug="d-missing",
            freshness_checked_at=None,
        ),
    )

    assert report.health_status == "blocked"
    assert report.row_count == d("5.000000")
    assert report.blocked_count == d("1.000000")
    assert report.watch_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_freshness_count == d("2.000000")
    assert report.unresolved_outcome_gap_count == d("1.000000")
    assert report.close_time_pressure_count == d("1.000000")
    assert report.stale_freshness_ratio == d("0.400000")
    assert report.unresolved_outcome_gap_ratio == d("0.200000")
    assert report.close_time_pressure_ratio == d("0.200000")
    assert report.reason_codes == (
        "unresolved_outcome_gap",
        "freshness_age_missing",
        "freshness_age_stale",
        "close_time_pressure",
    )
    assert tuple(item.reason_code for item in report.reason_code_counts) == (
        "unresolved_outcome_gap",
        "freshness_age_missing",
        "freshness_age_stale",
        "close_time_pressure",
        "market_outcome_freshness_recheck_clear",
    )
    assert tuple(item.count for item in report.reason_code_counts) == (
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
    )
    assert tuple(item.market_id for item in report.rows) == (
        "market-gap",
        "market-missing",
        "market-stale",
        "market-close",
        "market-pass",
    )
    assert report.rows[0].health_status == "blocked"
    assert report.rows[0].unresolved_outcome_gap == d("1.000000")
    assert report.rows[0].reason_codes == ("unresolved_outcome_gap",)
    assert report.rows[1].freshness_status == "missing"
    assert report.rows[1].freshness_age_seconds is None
    assert report.rows[2].freshness_age_seconds == d("7200.000000")
    assert report.rows[3].close_time_delta_seconds == d("1800.000000")
    assert report.rows[3].close_time_status == "pressure"
    assert report.rows[4].reason_codes == (
        "market_outcome_freshness_recheck_clear",
    )


def test_threshold_statuses_are_deterministic_at_boundaries() -> None:
    report = build_report(
        row(
            "market-fresh-boundary",
            freshness_checked_at=datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
            market_closes_at=datetime(2026, 7, 2, 13, 0, 1, tzinfo=UTC),
        ),
        row(
            "market-stale-over",
            freshness_checked_at=datetime(2026, 7, 2, 10, 59, 59, 999999, tzinfo=UTC),
            market_closes_at=datetime(2026, 7, 2, 13, 0, 1, tzinfo=UTC),
        ),
        row(
            "market-close-boundary",
            freshness_checked_at=datetime(2026, 7, 2, 11, 30, tzinfo=UTC),
            market_closes_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
        ),
    )

    by_id = {item.market_id: item for item in report.rows}

    assert by_id["market-fresh-boundary"].freshness_age_seconds == d("3600.000000")
    assert by_id["market-fresh-boundary"].freshness_status == "fresh"
    assert by_id["market-stale-over"].freshness_age_seconds == d("3600.000001")
    assert by_id["market-stale-over"].freshness_status == "stale"
    assert by_id["market-close-boundary"].close_time_delta_seconds == d("1800.000000")
    assert by_id["market-close-boundary"].close_time_status == "pressure"


def test_nonzero_unresolved_gap_threshold_keeps_status_consistent() -> None:
    report_module = module()
    custom_config = report_module.MarketOutcomeFreshnessRecheckHealthConfig(
        config_version="market-outcome-freshness-recheck-health-test-v0",
        stale_freshness_after_seconds=d("3600.000000"),
        max_unresolved_outcome_gap=d("1.000000"),
        close_time_pressure_within_seconds=d("1800.000000"),
    )

    report = report_module.build_market_outcome_freshness_recheck_health_report(
        (
            row(
                "market-gap-within-threshold",
                expected_outcome_count=d("2.000000"),
                resolved_outcome_count=d("1.000000"),
                market_closes_at=datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
            ),
        ),
        config=custom_config,
        generated_at=GENERATED_AT,
    )

    assert report.health_status == "pass"
    assert report.unresolved_outcome_gap_count == d("0.000000")
    assert report.unresolved_outcome_gap_ratio == d("0.000000")
    assert report.rows[0].unresolved_outcome_gap == d("1.000000")
    assert report.rows[0].outcome_gap_status == "clear"
    assert report.rows[0].reason_codes == (
        "market_outcome_freshness_recheck_clear",
    )


def test_utc_datetimes_are_required_and_normalized() -> None:
    report_module = module()
    eastern = timezone(timedelta(hours=-4))
    report = report_module.build_market_outcome_freshness_recheck_health_report(
        (
            row(
                "market-timezone",
                recheck_requested_at=datetime(2026, 7, 2, 7, 0, tzinfo=eastern),
                market_closes_at=datetime(2026, 7, 2, 10, 0, tzinfo=eastern),
                freshness_checked_at=datetime(2026, 7, 2, 7, 30, tzinfo=eastern),
            ),
        ),
        config=config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=eastern),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].recheck_requested_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert report.rows[0].market_closes_at == datetime(2026, 7, 2, 14, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report_module.build_market_outcome_freshness_recheck_health_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="recheck_requested_at must be timezone-aware"):
        row("market-naive", recheck_requested_at=datetime(2026, 7, 2, 11, 0))


def test_dataclasses_are_frozen_and_public_numeric_fields_use_decimal() -> None:
    report_module = module()

    assert report_module.__all__ == (
        "DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_HEALTH_CONFIG_VERSION",
        "MarketOutcomeFreshnessRecheckHealthConfig",
        "MarketOutcomeFreshnessRecheckHealthInput",
        "MarketOutcomeFreshnessRecheckHealthReasonCodeCount",
        "MarketOutcomeFreshnessRecheckHealthReport",
        "MarketOutcomeFreshnessRecheckHealthRow",
        "build_market_outcome_freshness_recheck_health_report",
        "market_outcome_freshness_recheck_health_report_payload",
    )
    for exported_name in report_module.__all__:
        value = getattr(report_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(row("market-frozen"))
    with pytest.raises(FrozenInstanceError):
        report.rows[0].health_status = "blocked"  # type: ignore[misc]

    public_decimal_suffixes = ("count", "ratio", "seconds", "gap")
    for value in (config(), report, *report.rows, *report.reason_code_counts):
        for field in fields(value):
            if field.name.endswith(public_decimal_suffixes):
                assert type(getattr(value, field.name)) is Decimal

    with pytest.raises(ValueError, match="expected_outcome_count must be a Decimal"):
        row("market-float", expected_outcome_count=1.0)  # type: ignore[arg-type]


def test_json_payload_uses_decimal_strings_and_iso_datetimes() -> None:
    report_module = module()
    report = build_report(
        row(
            "market-json",
            market_closes_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
        ),
    )

    payload = report_module.market_outcome_freshness_recheck_health_report_payload(
        report,
    )

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["close_time_pressure_ratio"] == "1.000000"
    assert payload["rows"][0]["recheck_age_seconds"] == "3600.000000"
    assert payload["rows"][0]["close_time_delta_seconds"] == "1800.000000"
    assert payload["rows"][0]["market_closes_at"] == "2026-07-02T12:30:00+00:00"
    assert payload["paper_only"] is True
    assert_json_ready_without_floats(payload)
    json.dumps(payload, sort_keys=True)


def test_module_omits_forbidden_runtime_surfaces() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "persistence",
        "database",
        "network",
        "live",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
    ):
        assert forbidden not in lowered

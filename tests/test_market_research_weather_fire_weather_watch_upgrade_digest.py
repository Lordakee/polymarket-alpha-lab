from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_weather_fire_weather_watch_upgrade_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_weather_fire_weather_watch_upgrade_digest",
    )


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "fire-weather-watch-upgrade-digest-v1",
        "max_source_age_seconds": Decimal("1800.000000"),
        "watch_upgrade_pressure_threshold": Decimal("0.350000"),
        "blocked_upgrade_pressure_threshold": Decimal("0.700000"),
        "fire_weather_watch_pressure_bonus": Decimal("0.100000"),
        "red_flag_warning_pressure_bonus": Decimal("0.250000"),
        "wind_gust_watch_threshold_mph": Decimal("30.000000"),
        "relative_humidity_watch_threshold_pct": Decimal("20.000000"),
        "fuel_moisture_watch_threshold_pct": Decimal("8.000000"),
    }
    values.update(overrides)
    return module.FireWeatherWatchUpgradeDigestConfig(**values)


def observation(
    event_id: str = "ca-red-flag-upgrade",
    *,
    market_slug: str = "will-california-red-flag-warning-expand",
    market_category: str = "disaster",
    region_id: str = "california-north",
    weather_zone: str = "ca-z001",
    source_reference: str = "nws-fire-weather-watch-17",
    forecast_valid_at: datetime = GENERATED_AT + timedelta(minutes=15),
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    fire_weather_watch_active: bool = True,
    red_flag_warning_active: bool = True,
    wind_gust_mph: Decimal = Decimal("45.000000"),
    relative_humidity_pct: Decimal = Decimal("12.000000"),
    fuel_moisture_pct: Decimal = Decimal("6.000000"),
    affected_probability: Decimal = Decimal("0.820000"),
    market_relevance: Decimal = Decimal("0.900000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.FireWeatherWatchUpgradeObservation(
        event_id=event_id,
        market_slug=market_slug,
        market_category=market_category,
        region_id=region_id,
        weather_zone=weather_zone,
        source_reference=source_reference,
        forecast_valid_at=forecast_valid_at,
        source_observed_at=source_observed_at,
        fire_weather_watch_active=fire_weather_watch_active,
        red_flag_warning_active=red_flag_warning_active,
        wind_gust_mph=wind_gust_mph,
        relative_humidity_pct=relative_humidity_pct,
        fuel_moisture_pct=fuel_moisture_pct,
        affected_probability=affected_probability,
        market_relevance=market_relevance,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    observations: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: object | None = None,
) -> Any:
    module = api()
    return module.build_market_research_weather_fire_weather_watch_upgrade_digest(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_float_or_int(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        pytest.fail(f"public numeric payload must not contain float/int: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_float_or_int(item)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_builds_fire_weather_watch_upgrade_digest_with_threshold_sorting_and_counts() -> None:
    report = digest(
        (
            observation(
                "beta-watch",
                market_slug="will-oregon-wildfire-evacuation-expand",
                market_category="weather",
                region_id="oregon-cascades",
                weather_zone="or-z608",
                fire_weather_watch_active=True,
                red_flag_warning_active=False,
                wind_gust_mph=Decimal("35.000000"),
                relative_humidity_pct=Decimal("18.000000"),
                fuel_moisture_pct=Decimal("11.000000"),
                affected_probability=Decimal("0.480000"),
                market_relevance=Decimal("0.800000"),
                upstream_reason_codes=("incident_command_briefing",),
            ),
            observation(
                "alpha-blocked",
                forecast_valid_at=datetime(
                    2026,
                    7,
                    4,
                    8,
                    15,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                source_observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    58,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                upstream_reason_codes=("energy_grid_exposure", "nws_red_flag_warning"),
            ),
            observation(
                "gamma-stale",
                market_slug="will-statewide-burn-ban-be-announced",
                market_category="policy",
                region_id="new-mexico-central",
                weather_zone="nm-z104",
                fire_weather_watch_active=False,
                red_flag_warning_active=False,
                wind_gust_mph=Decimal("20.000000"),
                relative_humidity_pct=Decimal("35.000000"),
                fuel_moisture_pct=Decimal("14.000000"),
                affected_probability=Decimal("0.100000"),
                market_relevance=Decimal("0.400000"),
                source_observed_at=GENERATED_AT - timedelta(seconds=4500),
            ),
            observation(
                "delta-pass",
                market_slug="will-local-power-price-spike-on-heat-alert",
                market_category="energy",
                region_id="texas-panhandle",
                weather_zone="tx-z012",
                fire_weather_watch_active=False,
                red_flag_warning_active=False,
                wind_gust_mph=Decimal("25.000000"),
                relative_humidity_pct=Decimal("26.000000"),
                fuel_moisture_pct=Decimal("12.000000"),
                affected_probability=Decimal("0.200000"),
                market_relevance=Decimal("0.600000"),
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.input_count == Decimal("4.000000")
    assert report.row_count == Decimal("4.000000")
    assert report.blocked_count == Decimal("2.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.stale_source_count == Decimal("1.000000")
    assert report.fire_weather_watch_count == Decimal("2.000000")
    assert report.red_flag_warning_count == Decimal("1.000000")
    assert report.max_upgrade_pressure == Decimal("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.event_id, row.upgrade_status, row.upgrade_pressure)
        for row in report.rows
    ] == [
        ("alpha-blocked", "blocked", Decimal("1.000000")),
        ("gamma-stale", "blocked", Decimal("0.040000")),
        ("beta-watch", "watch", Decimal("0.484000")),
        ("delta-pass", "pass", Decimal("0.120000")),
    ]

    blocked = report.rows[0]
    assert blocked.forecast_valid_at == datetime(2026, 7, 4, 12, 15, tzinfo=UTC)
    assert blocked.source_observed_at == datetime(2026, 7, 4, 11, 58, tzinfo=UTC)
    assert blocked.source_age_seconds == Decimal("120.000000")
    assert blocked.redacted_source_reference == "nws-fire-weather-watch-17"
    assert blocked.reason_codes == (
        "energy_grid_exposure",
        "fire_weather_fuel_moisture_threshold_met",
        "fire_weather_market_category_disaster",
        "fire_weather_red_flag_warning_active",
        "fire_weather_relative_humidity_threshold_met",
        "fire_weather_source_fresh",
        "fire_weather_upgrade_pressure_blocked",
        "fire_weather_watch_active",
        "fire_weather_wind_gust_threshold_met",
        "nws_red_flag_warning",
    )

    stale = report.rows[1]
    assert stale.source_age_seconds == Decimal("4500.000000")
    assert stale.reason_codes == (
        "fire_weather_market_category_policy",
        "fire_weather_source_stale",
    )

    counts_by_code = {
        item.reason_code: item.count for item in report.reason_code_counts
    }
    assert counts_by_code["fire_weather_source_fresh"] == Decimal("3.000000")
    assert counts_by_code["fire_weather_watch_active"] == Decimal("2.000000")
    assert counts_by_code["fire_weather_source_stale"] == Decimal("1.000000")
    assert report.reason_code_counts == tuple(
        sorted(report.reason_code_counts, key=lambda item: (-item.count, item.reason_code)),
    )
    assert report.reason_codes == tuple(sorted(report.reason_codes))


def test_empty_digest_and_payload_are_report_only_readonly_decimal_strings() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_weather_fire_weather_watch_upgrade_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert report.input_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.reason_codes == ("fire_weather_watch_upgrade_digest_empty",)
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))


def test_rejects_float_inputs_naive_datetimes_subclasses_future_rows_and_bad_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="affected_probability"):
        observation(affected_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="affected_probability"):
        observation(affected_probability=_DecimalSubclass("0.700000"))

    with pytest.raises(ValueError, match="market_relevance"):
        observation(market_relevance=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_source_age_seconds"):
        config(max_source_age_seconds=1800)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="blocked_upgrade_pressure_threshold"):
        config(blocked_upgrade_pressure_threshold=Decimal("0.300000"))

    with pytest.raises(ValueError, match="market_category"):
        observation(market_category="sports")

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(source_observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        digest((), generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="source_observed_at"):
        digest((observation(source_observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        digest((observation(readonly=False),))

    with pytest.raises(ValueError, match="redacted_source_reference"):
        replace(
            digest((observation(source_reference="https://wx.example/?secret=123"),)).rows[
                0
            ],
            redacted_source_reference="https://wx.example/?secret=123",
        )

    report = digest((observation(),))
    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.market_research_weather_fire_weather_watch_upgrade_digest_payload(
            unsafe_report,
        )

    with pytest.raises(ValueError, match="report"):
        module.market_research_weather_fire_weather_watch_upgrade_digest_payload(
            {"bad": "value"},
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    report = digest((observation(),))

    for item in (config(), observation(), report, *report.reason_code_counts, *report.rows):
        assert is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        report.row_count = Decimal("2.000000")  # type: ignore[misc]

    public_classes = (
        module.FireWeatherWatchUpgradeDigestConfig,
        module.FireWeatherWatchUpgradeObservation,
        module.FireWeatherWatchUpgradeDigestRow,
        module.FireWeatherWatchUpgradeReasonCodeCount,
        module.FireWeatherWatchUpgradeDigestReport,
    )
    for klass in public_classes:
        assert all(
            field.type not in (int, float)
            for field in fields(klass)
            if field.name not in {"paper_only", "report_only", "readonly"}
        )


def test_payload_redacts_sensitive_references_and_rejects_unsafe_public_content() -> None:
    module = api()
    report = digest(
        (
            observation(
                source_reference="https://wx.example/red-flag?credential=secret-123",
            ),
        ),
    )
    payload = module.market_research_weather_fire_weather_watch_upgrade_digest_payload(
        report,
    )

    assert payload == module.market_research_weather_fire_weather_watch_upgrade_digest_payload(
        report,
    )
    assert payload["rows"][0]["redacted_source_reference"].startswith("sha256:")
    assert "secret-123" not in repr(payload).lower()
    assert "credential" not in repr(payload).lower()
    assert "wallet" not in repr(payload).lower()
    assert_no_public_float_or_int(payload)


def test_module_has_no_live_trading_auth_io_or_durable_surface() -> None:
    module_path = Path(__file__).resolve().parents[1] / MODULE_PATH
    tree = ast.parse(module_path.read_text())
    source = module_path.read_text().lower()

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "private_key",
        "api_key",
        "sqlite",
        "postgres",
        "psycopg",
        "supabase",
        "redis",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "socket",
        "open(",
        "write_text",
        "read_text",
        "unlink(",
        "remove(",
        "wallet",
    ):
        assert token not in source

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    exported = module_path.read_text().split("__all__ = (", 1)[1].split(")", 1)[0]
    assert "build_market_research_weather_fire_weather_watch_upgrade_digest" in exported
    assert (
        "market_research_weather_fire_weather_watch_upgrade_digest_payload" in exported
    )
    assert inspect.signature(
        api().build_market_research_weather_fire_weather_watch_upgrade_digest,
    ).parameters["config"].kind is inspect.Parameter.KEYWORD_ONLY

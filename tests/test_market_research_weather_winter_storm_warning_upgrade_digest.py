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
    "market_research_weather_winter_storm_warning_upgrade_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_weather_winter_storm_warning_upgrade_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "max_source_age_seconds": d("1800.000000"),
        "watch_upgrade_pressure_threshold": d("0.350000"),
        "blocked_upgrade_pressure_threshold": d("0.700000"),
        "watch_snowfall_forecast_delta_inches": d("2.000000"),
        "blocked_snowfall_forecast_delta_inches": d("6.000000"),
        "watch_ice_accretion_risk": d("0.300000"),
        "blocked_ice_accretion_risk": d("0.600000"),
        "watch_warning_lead_time_hours": d("12.000000"),
        "blocked_warning_lead_time_hours": d("6.000000"),
        "watch_model_consensus_score": d("0.500000"),
        "blocked_model_consensus_score": d("0.800000"),
        "watch_population_airport_impact_score": d("0.400000"),
        "blocked_population_airport_impact_score": d("0.700000"),
    }
    values.update(overrides)
    return module.WeatherWinterStormWarningUpgradeDigestConfig(**values)


def observation(
    event_id: str = "storm-alpha",
    *,
    region_id: str = "new-york-metro",
    forecast_office: str = "nws-okx",
    market_slug: str = "will-nyc-get-winter-storm-warning",
    source_id: str = "nws-public-grid",
    forecast_valid_at: datetime = GENERATED_AT + timedelta(hours=8),
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    snowfall_forecast_delta_inches: Decimal = d("7.000000"),
    ice_accretion_risk: Decimal = d("0.800000"),
    warning_lead_time_hours: Decimal = d("4.000000"),
    model_consensus_score: Decimal = d("0.900000"),
    population_airport_impact_score: Decimal = d("0.850000"),
    upstream_reason_codes: tuple[str, ...] = ("nws_watch_active",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.WeatherWinterStormWarningUpgradeObservation(
        event_id=event_id,
        region_id=region_id,
        forecast_office=forecast_office,
        market_slug=market_slug,
        source_id=source_id,
        forecast_valid_at=forecast_valid_at,
        source_observed_at=source_observed_at,
        snowfall_forecast_delta_inches=snowfall_forecast_delta_inches,
        ice_accretion_risk=ice_accretion_risk,
        warning_lead_time_hours=warning_lead_time_hours,
        model_consensus_score=model_consensus_score,
        population_airport_impact_score=population_airport_impact_score,
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
    return module.build_market_research_weather_winter_storm_warning_upgrade_digest(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_float_or_int(value: object) -> None:
    if isinstance(value, bool):
        return
    if type(value) in (float, int):
        pytest.fail(f"public numeric must not be float or int: {value!r}")
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


def test_builds_warning_upgrade_digest_with_sorted_rows_counts_and_risk() -> None:
    report = digest(
        (
            observation(
                "beta-watch",
                region_id="massachusetts-east",
                forecast_office="nws-box",
                market_slug="will-boston-get-winter-storm-warning",
                snowfall_forecast_delta_inches=d("3.000000"),
                ice_accretion_risk=d("0.400000"),
                warning_lead_time_hours=d("10.000000"),
                model_consensus_score=d("0.600000"),
                population_airport_impact_score=d("0.500000"),
                upstream_reason_codes=("ensemble_trend_higher",),
            ),
            observation(
                "alpha-blocked",
                forecast_valid_at=datetime(
                    2026,
                    7,
                    4,
                    9,
                    0,
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
                upstream_reason_codes=(
                    "airport_ops_exposure",
                    "nws_watch_active",
                ),
            ),
            observation(
                "gamma-stale",
                region_id="pennsylvania-east",
                forecast_office="nws-phi",
                market_slug="will-philadelphia-get-winter-storm-warning",
                snowfall_forecast_delta_inches=d("0.200000"),
                ice_accretion_risk=d("0.050000"),
                warning_lead_time_hours=d("24.000000"),
                model_consensus_score=d("0.100000"),
                population_airport_impact_score=d("0.050000"),
                source_observed_at=GENERATED_AT - timedelta(seconds=4200),
                upstream_reason_codes=("wpc_heavy_snow_discussion",),
            ),
            observation(
                "delta-pass",
                region_id="maine-coast",
                forecast_office="nws-gyx",
                market_slug="will-portland-maine-get-warning",
                snowfall_forecast_delta_inches=d("0.500000"),
                ice_accretion_risk=d("0.050000"),
                warning_lead_time_hours=d("24.000000"),
                model_consensus_score=d("0.200000"),
                population_airport_impact_score=d("0.100000"),
                upstream_reason_codes=(),
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-weather-winter-storm-warning-upgrade-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.next_step == (
        "block_report_only_weather_winter_storm_warning_upgrade_digest"
    )
    assert report.input_count == d("4.000000")
    assert report.row_count == d("4.000000")
    assert report.blocked_count == d("2.000000")
    assert report.watch_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.max_upgrade_pressure == d("0.843333")
    assert report.report_risk_score == d("0.352500")
    assert report.max_snowfall_forecast_delta_inches == d("7.000000")
    assert report.max_ice_accretion_risk == d("0.800000")
    assert report.min_warning_lead_time_hours == d("4.000000")
    assert report.max_model_consensus_score == d("0.900000")
    assert report.max_population_airport_impact_score == d("0.850000")
    assert report.max_source_age_seconds == d("1800.000000")
    assert report.max_source_age_observed_seconds == d("4200.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.event_id, row.upgrade_status, row.upgrade_pressure)
        for row in report.rows
    ] == [
        ("alpha-blocked", "blocked", d("0.843333")),
        ("gamma-stale", "blocked", d("0.046667")),
        ("beta-watch", "watch", d("0.433333")),
        ("delta-pass", "pass", d("0.086667")),
    ]

    blocked = report.rows[0]
    assert blocked.forecast_valid_at == datetime(2026, 7, 4, 13, 0, tzinfo=UTC)
    assert blocked.source_observed_at == datetime(2026, 7, 4, 11, 58, tzinfo=UTC)
    assert blocked.source_age_seconds == d("120.000000")
    assert blocked.source_freshness_status == "fresh"
    assert blocked.reason_codes == (
        "airport_ops_exposure",
        "nws_watch_active",
        "weather_winter_storm_warning_upgrade_ice_risk_blocked",
        "weather_winter_storm_warning_upgrade_impact_blocked",
        "weather_winter_storm_warning_upgrade_model_consensus_blocked",
        "weather_winter_storm_warning_upgrade_pressure_blocked",
        "weather_winter_storm_warning_upgrade_short_lead_time_blocked",
        "weather_winter_storm_warning_upgrade_snowfall_delta_blocked",
        "weather_winter_storm_warning_upgrade_source_fresh",
    )

    stale = report.rows[1]
    assert stale.source_age_seconds == d("4200.000000")
    assert stale.reason_codes == (
        "weather_winter_storm_warning_upgrade_source_stale",
        "wpc_heavy_snow_discussion",
    )

    counts_by_code = {
        item.reason_code: item.count for item in report.reason_code_counts
    }
    assert counts_by_code[
        "weather_winter_storm_warning_upgrade_source_fresh"
    ] == d("3.000000")
    assert counts_by_code[
        "weather_winter_storm_warning_upgrade_source_stale"
    ] == d("1.000000")
    assert counts_by_code[
        "weather_winter_storm_warning_upgrade_pressure_blocked"
    ] == d("1.000000")
    assert report.reason_code_counts == tuple(
        sorted(report.reason_code_counts, key=lambda item: (-item.count, item.reason_code)),
    )
    assert report.reason_codes == tuple(sorted(report.reason_codes))


def test_empty_digest_and_payload_are_report_only_readonly_decimal_strings() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_weather_winter_storm_warning_upgrade_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert report.digest_status == "blocked"
    assert report.next_step == (
        "block_report_only_weather_winter_storm_warning_upgrade_digest"
    )
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.report_risk_score == d("0.000000")
    assert report.reason_codes == (
        "weather_winter_storm_warning_upgrade_digest_empty",
    )
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["report_risk_score"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))


def test_rejects_nondecimal_naive_datetime_subclasses_future_rows_and_bad_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="ice_accretion_risk"):
        observation(ice_accretion_risk=Decimal("NaN"))

    with pytest.raises(ValueError, match="model_consensus_score"):
        observation(model_consensus_score=_DecimalSubclass("0.700000"))

    with pytest.raises(ValueError, match="population_airport_impact_score"):
        observation(population_airport_impact_score=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_source_age_seconds"):
        config(max_source_age_seconds=1800)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="blocked_upgrade_pressure_threshold"):
        config(blocked_upgrade_pressure_threshold=d("0.300000"))

    with pytest.raises(ValueError, match="blocked_warning_lead_time_hours"):
        config(blocked_warning_lead_time_hours=d("14.000000"))

    with pytest.raises(ValueError, match="source_observed_at"):
        observation(source_observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        digest((), generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="source_observed_at"):
        digest((observation(source_observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        digest((observation(readonly=False),))

    with pytest.raises(ValueError, match="duplicate"):
        digest((observation("same-event"), observation("same-event")))

    with pytest.raises(ValueError, match="canonical"):
        observation(forecast_office="NWS-OKX")

    row = digest((observation(),)).rows[0]
    with pytest.raises(ValueError, match="upgrade_status"):
        replace(row, upgrade_status="pass")

    report = digest((observation(),))
    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.market_research_weather_winter_storm_warning_upgrade_digest_payload(
            unsafe_report,
        )

    with pytest.raises(ValueError, match="report"):
        module.market_research_weather_winter_storm_warning_upgrade_digest_payload(
            {"bad": "value"},
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    report = digest((observation(),))

    for item in (config(), observation(), report, *report.reason_code_counts, *report.rows):
        assert is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        report.row_count = d("2.000000")  # type: ignore[misc]

    public_classes = (
        module.WeatherWinterStormWarningUpgradeDigestConfig,
        module.WeatherWinterStormWarningUpgradeObservation,
        module.WeatherWinterStormWarningUpgradeDigestRow,
        module.WeatherWinterStormWarningUpgradeReasonCodeCount,
        module.WeatherWinterStormWarningUpgradeDigestReport,
    )
    for klass in public_classes:
        for field in fields(klass):
            if field.name not in {"paper_only", "report_only", "readonly"}:
                assert field.type not in (int, float)
            if field.name != "reason_code_counts" and any(
                fragment in field.name
                for fragment in (
                    "count",
                    "score",
                    "seconds",
                    "hours",
                    "inches",
                    "risk",
                    "pressure",
                )
            ):
                assert field.type == "Decimal"


def test_payload_is_deterministic_and_has_canonical_decimal_strings() -> None:
    module = api()
    report = digest((observation(),))

    payload = module.market_research_weather_winter_storm_warning_upgrade_digest_payload(
        report,
    )

    assert payload == module.market_research_weather_winter_storm_warning_upgrade_digest_payload(
        report,
    )
    assert payload["rows"][0]["upgrade_pressure"] == "0.843333"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert all("." in value and len(value.rsplit(".", 1)[1]) == 6 for value in (
        payload["row_count"],
        payload["report_risk_score"],
        payload["rows"][0]["source_age_seconds"],
        payload["rows"][0]["snowfall_forecast_delta_inches"],
    ))
    assert_no_public_float_or_int(payload)


def test_module_has_no_mutating_io_or_external_surfaces() -> None:
    module_path = Path(__file__).resolve().parents[1] / MODULE_PATH
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()

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
        "urlopen",
        "subprocess",
        "socket",
        "open(",
        "write_text",
        "read_text",
        "unlink(",
        "remove(",
        "wallet",
        "environ",
        "getenv",
    ):
        assert token not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "httpx",
        "urllib",
        "psycopg",
    }
    forbidden_calls = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    exported = source.split("__all__ = (", 1)[1].split(")", 1)[0]
    assert "build_market_research_weather_winter_storm_warning_upgrade_digest" in exported
    assert (
        "market_research_weather_winter_storm_warning_upgrade_digest_payload"
        in exported
    )
    assert inspect.signature(
        api().build_market_research_weather_winter_storm_warning_upgrade_digest,
    ).parameters["config"].kind is inspect.Parameter.KEYWORD_ONLY

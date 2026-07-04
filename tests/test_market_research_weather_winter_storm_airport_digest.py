from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_weather_winter_storm_airport_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_weather_winter_storm_airport_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "max_source_age_seconds": d("3600.000000"),
        "watch_ground_stop_ratio": d("0.100000"),
        "blocked_ground_stop_ratio": d("0.400000"),
        "watch_delay_minutes": d("45.000000"),
        "blocked_delay_minutes": d("180.000000"),
        "heavy_snowfall_inches_12h": d("6.000000"),
        "ice_accretion_inches": d("0.150000"),
        "high_deicing_queue_minutes": d("45.000000"),
        "low_runway_clear_score": d("0.550000"),
    }
    values.update(overrides)
    return module.WeatherWinterStormAirportDigestConfig(**values)


def observation(
    airport_id: str = "kjfk",
    event_id: str = "storm-alpha",
    *,
    source_id: str = "airport_public_summary",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    ground_stop_ratio: Decimal = d("0.600000"),
    departure_delay_minutes: Decimal = d("240.000000"),
    arrival_delay_minutes: Decimal = d("210.000000"),
    snowfall_inches_12h: Decimal = d("8.000000"),
    ice_accretion_inches: Decimal = d("0.200000"),
    deicing_queue_minutes: Decimal = d("70.000000"),
    runway_clear_score: Decimal = d("0.400000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.WeatherWinterStormAirportObservation(
        airport_id=airport_id,
        event_id=event_id,
        source_id=source_id,
        observed_at=observed_at,
        ground_stop_ratio=ground_stop_ratio,
        departure_delay_minutes=departure_delay_minutes,
        arrival_delay_minutes=arrival_delay_minutes,
        snowfall_inches_12h=snowfall_inches_12h,
        ice_accretion_inches=ice_accretion_inches,
        deicing_queue_minutes=deicing_queue_minutes,
        runway_clear_score=runway_clear_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(*rows: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_weather_winter_storm_airport_digest(
        rows,
        config=config(),
        generated_at=generated_at,
    )


def assert_no_public_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        pytest.fail(f"public numeric must not be float or int: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_float_or_int(item)


def test_builds_report_only_weather_winter_storm_airport_digest_deterministically() -> None:
    module = api()

    report = digest(
        observation(
            "ksea",
            "clear-event",
            source_id="public_metar_summary",
            ground_stop_ratio=d("0.000000"),
            departure_delay_minutes=d("10.000000"),
            arrival_delay_minutes=d("8.000000"),
            snowfall_inches_12h=d("1.000000"),
            ice_accretion_inches=d("0.000000"),
            deicing_queue_minutes=d("5.000000"),
            runway_clear_score=d("0.900000"),
        ),
        observation(
            "kjfk",
            "blocked-event",
            source_id="airport_public_summary",
            observed_at=GENERATED_AT - timedelta(seconds=120),
            ground_stop_ratio=d("0.600000"),
            departure_delay_minutes=d("240.000000"),
            arrival_delay_minutes=d("210.000000"),
            snowfall_inches_12h=d("8.000000"),
            ice_accretion_inches=d("0.200000"),
            deicing_queue_minutes=d("70.000000"),
            runway_clear_score=d("0.400000"),
        ),
        observation(
            "kord",
            "watch-event",
            source_id="faa_public_summary",
            observed_at=datetime(
                2026,
                7,
                3,
                12,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            ground_stop_ratio=d("0.200000"),
            departure_delay_minutes=d("60.000000"),
            arrival_delay_minutes=d("50.000000"),
            snowfall_inches_12h=d("2.000000"),
            ice_accretion_inches=d("0.050000"),
            deicing_queue_minutes=d("20.000000"),
            runway_clear_score=d("0.800000"),
        ),
    )

    assert isinstance(report, module.WeatherWinterStormAirportDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-weather-winter-storm-airport-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.next_step == "block_report_only_weather_winter_storm_airport_digest"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_row_count == d("1.000000")
    assert report.watch_row_count == d("1.000000")
    assert report.pass_row_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.max_ground_stop_ratio == d("0.600000")
    assert report.max_departure_delay_minutes == d("240.000000")
    assert report.max_arrival_delay_minutes == d("210.000000")
    assert report.max_deicing_queue_minutes == d("70.000000")
    assert report.max_snowfall_inches_12h == d("8.000000")
    assert report.max_ice_accretion_inches == d("0.200000")
    assert report.max_source_age_seconds == d("3600.000000")
    assert report.max_source_age_observed_seconds == d("5400.000000")
    assert report.average_runway_clear_score == d("0.700000")
    assert report.reason_codes == (
        "weather_winter_storm_airport_source_stale",
        "weather_winter_storm_airport_ground_stop_spike",
        "weather_winter_storm_airport_departure_delay_surge",
        "weather_winter_storm_airport_arrival_delay_surge",
        "weather_winter_storm_airport_heavy_snowfall",
        "weather_winter_storm_airport_icing_risk",
        "weather_winter_storm_airport_deicing_queue_pressure",
        "weather_winter_storm_airport_ground_stop_watch",
        "weather_winter_storm_airport_departure_delay_watch",
        "weather_winter_storm_airport_arrival_delay_watch",
        "weather_winter_storm_airport_low_runway_clear_score",
    )
    assert tuple(
        (row.airport_id, row.event_id, row.row_status, row.source_age_seconds)
        for row in report.rows
    ) == (
        ("kjfk", "blocked-event", "blocked", d("120.000000")),
        ("kord", "watch-event", "watch", d("5400.000000")),
        ("ksea", "clear-event", "pass", d("120.000000")),
    )
    assert report.rows[0].reason_codes == (
        "weather_winter_storm_airport_ground_stop_spike",
        "weather_winter_storm_airport_departure_delay_surge",
        "weather_winter_storm_airport_arrival_delay_surge",
        "weather_winter_storm_airport_heavy_snowfall",
        "weather_winter_storm_airport_icing_risk",
        "weather_winter_storm_airport_deicing_queue_pressure",
        "weather_winter_storm_airport_low_runway_clear_score",
    )
    assert report.rows[1].observed_at == datetime(2026, 7, 3, 16, 30, tzinfo=UTC)
    assert report.rows[1].source_freshness_status == "stale"
    assert report.rows[1].reason_codes == (
        "weather_winter_storm_airport_source_stale",
        "weather_winter_storm_airport_ground_stop_watch",
        "weather_winter_storm_airport_departure_delay_watch",
        "weather_winter_storm_airport_arrival_delay_watch",
    )
    assert report.rows[2].reason_codes == ("weather_winter_storm_airport_row_clear",)
    assert tuple(
        (item.reason_code, item.count, item.row_ratio)
        for item in report.reason_code_counts
    ) == (
        (
            "weather_winter_storm_airport_source_stale",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_winter_storm_airport_ground_stop_spike",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_winter_storm_airport_departure_delay_surge",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_winter_storm_airport_arrival_delay_surge",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_winter_storm_airport_heavy_snowfall",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_winter_storm_airport_icing_risk",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_winter_storm_airport_deicing_queue_pressure",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_winter_storm_airport_ground_stop_watch",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_winter_storm_airport_departure_delay_watch",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_winter_storm_airport_arrival_delay_watch",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_winter_storm_airport_low_runway_clear_score",
            d("1.000000"),
            d("0.333333"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    public = asdict(report)
    assert_no_public_float_or_int(public)


def test_empty_and_clear_digest_are_decimal_stringed_report_only_values() -> None:
    module = api()

    empty = digest()
    empty_json = module.market_research_weather_winter_storm_airport_digest_json(empty)
    json.dumps(empty_json, sort_keys=True)

    assert empty.digest_status == "blocked"
    assert empty.next_step == "block_report_only_weather_winter_storm_airport_digest"
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.max_ground_stop_ratio == d("0.000000")
    assert empty.average_runway_clear_score == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("weather_winter_storm_airport_digest_empty",)
    assert empty.reason_code_counts == (
        module.WeatherWinterStormAirportReasonCodeCount(
            reason_code="weather_winter_storm_airport_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert empty_json["generated_at"] == "2026-07-03T18:00:00+00:00"
    assert empty_json["row_count"] == "0.000000"
    assert empty_json["reason_code_counts"][0]["count"] == "1.000000"
    assert empty_json["paper_only"] is True
    assert empty_json["report_only"] is True
    assert empty_json["readonly"] is True
    assert_no_public_float_or_int(empty_json)

    clear = digest(
        observation(
            "ksea",
            "clear-event",
            source_id="public_metar_summary",
            ground_stop_ratio=d("0.000000"),
            departure_delay_minutes=d("10.000000"),
            arrival_delay_minutes=d("8.000000"),
            snowfall_inches_12h=d("1.000000"),
            ice_accretion_inches=d("0.000000"),
            deicing_queue_minutes=d("5.000000"),
            runway_clear_score=d("0.900000"),
        ),
    )

    assert clear.digest_status == "pass"
    assert clear.next_step == "continue_report_only_weather_winter_storm_airport_digest"
    assert clear.reason_codes == ("weather_winter_storm_airport_digest_clear",)
    assert clear.reason_code_counts == (
        module.WeatherWinterStormAirportReasonCodeCount(
            reason_code="weather_winter_storm_airport_digest_clear",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_validates_decimal_datetime_flags_duplicates_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="deicing_queue_minutes"):
        observation(deicing_queue_minutes=Decimal("NaN"))

    with pytest.raises(ValueError, match="ground_stop_ratio"):
        observation(ground_stop_ratio=_DecimalSubclass("0.100000"))

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 3, 18, 0))

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="after generated_at"):
        digest(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unique"):
        digest(
            observation("kjfk", "same-event", source_id="a"),
            observation("kjfk", "same-event", source_id="b"),
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="canonical"):
        observation(airport_id="KJFK")

    with pytest.raises(ValueError, match="not allowed"):
        observation(source_id="api_token")

    row = digest(observation()).rows[0]
    with pytest.raises(ValueError, match="row_status"):
        replace(row, row_status="pass")

    sorted_report = digest(
        observation(
            "ksea",
            "clear-a",
            ground_stop_ratio=d("0.000000"),
            departure_delay_minutes=d("10.000000"),
            arrival_delay_minutes=d("8.000000"),
            snowfall_inches_12h=d("1.000000"),
            ice_accretion_inches=d("0.000000"),
            deicing_queue_minutes=d("5.000000"),
            runway_clear_score=d("0.900000"),
        ),
        observation(
            "ksfo",
            "clear-b",
            ground_stop_ratio=d("0.000000"),
            departure_delay_minutes=d("10.000000"),
            arrival_delay_minutes=d("8.000000"),
            snowfall_inches_12h=d("1.000000"),
            ice_accretion_inches=d("0.000000"),
            deicing_queue_minutes=d("5.000000"),
            runway_clear_score=d("0.900000"),
        ),
    )
    with pytest.raises(ValueError, match="deterministic"):
        replace(sorted_report, rows=tuple(reversed(sorted_report.rows)))


def test_dataclasses_are_frozen_and_public_numerics_are_decimal_typed() -> None:
    module = api()
    row = observation()

    with pytest.raises(FrozenInstanceError):
        row.airport_id = "other"  # type: ignore[misc]

    numeric_names = (
        "count",
        "ratio",
        "seconds",
        "minutes",
        "inches",
        "score",
    )
    nonnumeric_names = {"reason_code_counts"}
    for cls in (
        module.WeatherWinterStormAirportDigestConfig,
        module.WeatherWinterStormAirportObservation,
        module.WeatherWinterStormAirportDigestRow,
        module.WeatherWinterStormAirportReasonCodeCount,
        module.WeatherWinterStormAirportDigestReport,
    ):
        for field in fields(cls):
            if field.name not in nonnumeric_names and any(
                part in field.name for part in numeric_names
            ):
                assert field.type == "Decimal"


def test_static_source_has_no_forbidden_terms_or_io_calls() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    for term in (
        "live",
        "auth",
        "wallet",
        "account",
        "order",
        "cancel",
        "replace",
        "exchange",
        "secret",
        "token",
        "payload",
        "requests",
        "socket",
        "subprocess",
        "open(",
    ):
        assert term not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "httpx",
        "urllib",
    }
    forbidden_calls = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
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
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

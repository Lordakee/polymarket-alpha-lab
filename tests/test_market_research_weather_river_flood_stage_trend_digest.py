from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_weather_river_flood_stage_trend_digest.py",
)
SIX_DECIMAL_RE = re.compile(r"^-?\d+\.\d{6}$")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_weather_river_flood_stage_trend_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "max_observation_age_seconds": d("3600.000000"),
        "near_flood_stage_margin_ft": d("1.000000"),
        "stage_rise_watch_ft": d("0.500000"),
        "stage_rise_blocked_ft": d("2.000000"),
        "forecast_crest_revision_watch_ft": d("0.500000"),
        "forecast_crest_revision_blocked_ft": d("1.500000"),
        "low_confidence_ratio": d("0.550000"),
    }
    values.update(overrides)
    return module.WeatherRiverFloodStageTrendDigestConfig(**values)


def observation(
    gauge_id: str = "usgs_08074500",
    market_slug: str = "houston-river-flooding",
    *,
    river_id: str = "buffalo_bayou",
    source_id: str = "public_river_forecast",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    forecast_valid_at: datetime = GENERATED_AT + timedelta(hours=6),
    current_stage_ft: Decimal = d("37.500000"),
    previous_stage_ft: Decimal = d("35.000000"),
    flood_stage_ft: Decimal = d("36.000000"),
    forecast_crest_ft: Decimal = d("38.250000"),
    previous_forecast_crest_ft: Decimal = d("36.500000"),
    forecast_confidence_ratio: Decimal = d("0.500000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.WeatherRiverFloodStageTrendObservation(
        gauge_id=gauge_id,
        river_id=river_id,
        market_slug=market_slug,
        source_id=source_id,
        observed_at=observed_at,
        forecast_valid_at=forecast_valid_at,
        current_stage_ft=current_stage_ft,
        previous_stage_ft=previous_stage_ft,
        flood_stage_ft=flood_stage_ft,
        forecast_crest_ft=forecast_crest_ft,
        previous_forecast_crest_ft=previous_forecast_crest_ft,
        forecast_confidence_ratio=forecast_confidence_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(*rows: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_weather_river_flood_stage_trend_digest(
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


def assert_numeric_strings_are_six_decimal_places(value: object) -> None:
    numeric_name_parts = (
        "count",
        "ratio",
        "seconds",
        "ft",
    )
    if isinstance(value, dict):
        for item_name, item in value.items():
            if isinstance(item, str) and any(
                part in item_name for part in numeric_name_parts
            ):
                assert SIX_DECIMAL_RE.fullmatch(item), item
            assert_numeric_strings_are_six_decimal_places(item)
    elif isinstance(value, list):
        for item in value:
            assert_numeric_strings_are_six_decimal_places(item)


def test_builds_report_only_weather_river_flood_stage_trend_digest_deterministically() -> None:
    module = api()

    report = digest(
        observation(
            "usgs_14128870",
            "portland-river-flooding",
            river_id="willamette",
            source_id="public_gauge_summary",
            current_stage_ft=d("8.000000"),
            previous_stage_ft=d("8.100000"),
            flood_stage_ft=d("18.000000"),
            forecast_crest_ft=d("9.000000"),
            previous_forecast_crest_ft=d("9.200000"),
            forecast_confidence_ratio=d("0.950000"),
        ),
        observation(
            "usgs_08074500",
            "houston-river-flooding",
            river_id="buffalo_bayou",
            source_id="public_river_forecast",
            observed_at=GENERATED_AT - timedelta(seconds=120),
            current_stage_ft=d("37.500000"),
            previous_stage_ft=d("35.000000"),
            flood_stage_ft=d("36.000000"),
            forecast_crest_ft=d("38.250000"),
            previous_forecast_crest_ft=d("36.500000"),
            forecast_confidence_ratio=d("0.500000"),
        ),
        observation(
            "usgs_02358000",
            "florida-river-flooding",
            river_id="apalachicola",
            source_id="county_public_river_summary",
            observed_at=datetime(
                2026,
                7,
                3,
                12,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            current_stage_ft=d("19.300000"),
            previous_stage_ft=d("18.900000"),
            flood_stage_ft=d("20.000000"),
            forecast_crest_ft=d("19.400000"),
            previous_forecast_crest_ft=d("18.800000"),
            forecast_confidence_ratio=d("0.500000"),
        ),
    )

    assert isinstance(report, module.WeatherRiverFloodStageTrendDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-weather-river-flood-stage-trend-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.next_step == (
        "block_report_only_weather_river_flood_stage_trend_digest"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_row_count == d("1.000000")
    assert report.watch_row_count == d("1.000000")
    assert report.pass_row_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.flood_stage_exceedance_count == d("1.000000")
    assert report.crest_exceedance_count == d("1.000000")
    assert report.max_observation_age_seconds == d("3600.000000")
    assert report.max_observation_age_observed_seconds == d("5400.000000")
    assert report.max_current_stage_ft == d("37.500000")
    assert report.max_stage_vs_flood_ft == d("1.500000")
    assert report.max_forecast_crest_vs_flood_ft == d("2.250000")
    assert report.max_stage_delta_ft == d("2.500000")
    assert report.max_forecast_crest_revision_ft == d("1.750000")
    assert report.average_forecast_confidence_ratio == d("0.650000")
    assert report.reason_codes == (
        "weather_river_flood_stage_trend_observation_stale",
        "weather_river_flood_stage_trend_stage_exceeds_flood",
        "weather_river_flood_stage_trend_forecast_crest_exceeds_flood",
        "weather_river_flood_stage_trend_stage_rise_blocked",
        "weather_river_flood_stage_trend_crest_revision_blocked",
        "weather_river_flood_stage_trend_crest_revision_watch",
        "weather_river_flood_stage_trend_near_flood_stage",
        "weather_river_flood_stage_trend_low_confidence",
    )
    assert tuple(
        (row.gauge_id, row.market_slug, row.row_status, row.observation_age_seconds)
        for row in report.rows
    ) == (
        (
            "usgs_08074500",
            "houston-river-flooding",
            "blocked",
            d("120.000000"),
        ),
        (
            "usgs_02358000",
            "florida-river-flooding",
            "watch",
            d("5400.000000"),
        ),
        (
            "usgs_14128870",
            "portland-river-flooding",
            "pass",
            d("120.000000"),
        ),
    )
    assert report.rows[0].reason_codes == (
        "weather_river_flood_stage_trend_stage_exceeds_flood",
        "weather_river_flood_stage_trend_forecast_crest_exceeds_flood",
        "weather_river_flood_stage_trend_stage_rise_blocked",
        "weather_river_flood_stage_trend_crest_revision_blocked",
        "weather_river_flood_stage_trend_low_confidence",
    )
    assert report.rows[0].stage_delta_ft == d("2.500000")
    assert report.rows[0].stage_vs_flood_ft == d("1.500000")
    assert report.rows[0].forecast_crest_revision_ft == d("1.750000")
    assert report.rows[1].observed_at == datetime(2026, 7, 3, 16, 30, tzinfo=UTC)
    assert report.rows[1].observation_freshness_status == "stale"
    assert report.rows[1].reason_codes == (
        "weather_river_flood_stage_trend_observation_stale",
        "weather_river_flood_stage_trend_crest_revision_watch",
        "weather_river_flood_stage_trend_near_flood_stage",
        "weather_river_flood_stage_trend_low_confidence",
    )
    assert report.rows[2].reason_codes == (
        "weather_river_flood_stage_trend_row_clear",
    )
    assert tuple(
        (item.reason_code, item.count, item.row_ratio)
        for item in report.reason_code_counts
    ) == (
        (
            "weather_river_flood_stage_trend_observation_stale",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_stage_trend_stage_exceeds_flood",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_stage_trend_forecast_crest_exceeds_flood",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_stage_trend_stage_rise_blocked",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_stage_trend_crest_revision_blocked",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_stage_trend_crest_revision_watch",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_stage_trend_near_flood_stage",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_stage_trend_low_confidence",
            d("2.000000"),
            d("0.666667"),
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
    empty_json = module.market_research_weather_river_flood_stage_trend_digest_json(
        empty,
    )
    json.dumps(empty_json, sort_keys=True)

    assert empty.digest_status == "blocked"
    assert empty.next_step == (
        "block_report_only_weather_river_flood_stage_trend_digest"
    )
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.max_current_stage_ft == d("0.000000")
    assert empty.average_forecast_confidence_ratio == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "weather_river_flood_stage_trend_digest_empty",
    )
    assert empty.reason_code_counts == (
        module.WeatherRiverFloodStageTrendReasonCodeCount(
            reason_code="weather_river_flood_stage_trend_digest_empty",
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
    assert_numeric_strings_are_six_decimal_places(empty_json)

    clear = digest(
        observation(
            "usgs_14128870",
            "portland-river-flooding",
            river_id="willamette",
            source_id="public_gauge_summary",
            current_stage_ft=d("8.000000"),
            previous_stage_ft=d("8.100000"),
            flood_stage_ft=d("18.000000"),
            forecast_crest_ft=d("9.000000"),
            previous_forecast_crest_ft=d("9.200000"),
            forecast_confidence_ratio=d("0.950000"),
        ),
    )

    assert clear.digest_status == "pass"
    assert clear.next_step == (
        "continue_report_only_weather_river_flood_stage_trend_digest"
    )
    assert clear.reason_codes == (
        "weather_river_flood_stage_trend_digest_clear",
    )
    assert clear.reason_code_counts == (
        module.WeatherRiverFloodStageTrendReasonCodeCount(
            reason_code="weather_river_flood_stage_trend_digest_clear",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_validates_decimal_datetime_flags_duplicates_and_consistency() -> None:
    with pytest.raises(ValueError, match="current_stage_ft"):
        observation(current_stage_ft=Decimal("NaN"))

    with pytest.raises(ValueError, match="current_stage_ft"):
        observation(current_stage_ft=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 3, 18, 0))

    with pytest.raises(ValueError, match="forecast_valid_at"):
        observation(forecast_valid_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="after generated_at"):
        digest(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="forecast_valid_at"):
        observation(forecast_valid_at=GENERATED_AT - timedelta(hours=1))

    with pytest.raises(ValueError, match="unique"):
        digest(
            observation("usgs_08074500", "same-market"),
            observation("usgs_08074500", "same-market", source_id="public_summary_b"),
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="canonical"):
        observation(gauge_id="USGS_08074500")

    with pytest.raises(ValueError, match="not allowed"):
        observation(source_id="api_token")

    with pytest.raises(ValueError, match="stage_rise_blocked_ft"):
        config(
            stage_rise_watch_ft=d("2.000000"),
            stage_rise_blocked_ft=d("1.000000"),
        )

    row = digest(observation()).rows[0]
    with pytest.raises(ValueError, match="row_status"):
        replace(row, row_status="pass")

    sorted_report = digest(
        observation(
            "usgs_11111111",
            "alpha-river-flooding",
            river_id="alpha_river",
            current_stage_ft=d("1.000000"),
            previous_stage_ft=d("1.000000"),
            flood_stage_ft=d("10.000000"),
            forecast_crest_ft=d("2.000000"),
            previous_forecast_crest_ft=d("2.000000"),
            forecast_confidence_ratio=d("0.950000"),
        ),
        observation(
            "usgs_22222222",
            "beta-river-flooding",
            river_id="beta_river",
            current_stage_ft=d("1.000000"),
            previous_stage_ft=d("1.000000"),
            flood_stage_ft=d("10.000000"),
            forecast_crest_ft=d("2.000000"),
            previous_forecast_crest_ft=d("2.000000"),
            forecast_confidence_ratio=d("0.950000"),
        ),
    )
    with pytest.raises(ValueError, match="deterministic"):
        replace(sorted_report, rows=tuple(reversed(sorted_report.rows)))


def test_dataclasses_are_frozen_and_public_numerics_are_decimal_typed() -> None:
    module = api()
    row = observation()

    with pytest.raises(FrozenInstanceError):
        row.gauge_id = "other"  # type: ignore[misc]

    numeric_names = (
        "count",
        "ratio",
        "seconds",
        "ft",
    )
    for cls in (
        module.WeatherRiverFloodStageTrendDigestConfig,
        module.WeatherRiverFloodStageTrendObservation,
        module.WeatherRiverFloodStageTrendDigestRow,
        module.WeatherRiverFloodStageTrendReasonCodeCount,
        module.WeatherRiverFloodStageTrendDigestReport,
    ):
        for field in fields(cls):
            if field.name != "reason_code_counts" and any(
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
        "requests",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "http",
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
        "http",
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
        "post",
        "put",
        "patch",
        "delete",
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

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
    "src/polymarket_alpha_lab/"
    "market_research_weather_flash_flood_guidance_break_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_weather_flash_flood_guidance_break_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "max_source_age_seconds": d("1800.000000"),
        "watch_guidance_break_ratio": d("0.850000"),
        "blocked_guidance_break_ratio": d("1.000000"),
        "saturated_soil_ratio": d("0.800000"),
        "heavy_rainfall_inches_6h": d("3.000000"),
        "low_confidence_ratio": d("0.550000"),
    }
    values.update(overrides)
    return module.WeatherFlashFloodGuidanceBreakDigestConfig(**values)


def observation(
    basin_id: str = "texas_hill_country",
    event_id: str = "storm-alpha",
    *,
    source_id: str = "public_guidance_summary",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    rainfall_inches_6h: Decimal = d("3.200000"),
    flash_flood_guidance_inches_6h: Decimal = d("2.500000"),
    antecedent_soil_saturation_ratio: Decimal = d("0.900000"),
    forecast_confidence_ratio: Decimal = d("0.450000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.WeatherFlashFloodGuidanceBreakObservation(
        basin_id=basin_id,
        event_id=event_id,
        source_id=source_id,
        observed_at=observed_at,
        rainfall_inches_6h=rainfall_inches_6h,
        flash_flood_guidance_inches_6h=flash_flood_guidance_inches_6h,
        antecedent_soil_saturation_ratio=antecedent_soil_saturation_ratio,
        forecast_confidence_ratio=forecast_confidence_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(*rows: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_weather_flash_flood_guidance_break_digest(
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


def test_builds_report_only_guidance_break_digest_deterministically() -> None:
    module = api()

    report = digest(
        observation(
            "pacific_nw",
            "clear-event",
            source_id="public_qpf_summary",
            rainfall_inches_6h=d("0.500000"),
            flash_flood_guidance_inches_6h=d("2.000000"),
            antecedent_soil_saturation_ratio=d("0.300000"),
            forecast_confidence_ratio=d("0.950000"),
        ),
        observation(
            "texas_hill_country",
            "blocked-event",
            source_id="public_guidance_summary",
            observed_at=GENERATED_AT - timedelta(seconds=120),
            rainfall_inches_6h=d("3.200000"),
            flash_flood_guidance_inches_6h=d("2.500000"),
            antecedent_soil_saturation_ratio=d("0.900000"),
            forecast_confidence_ratio=d("0.450000"),
        ),
        observation(
            "appalachia",
            "watch-event",
            source_id="county_public_summary",
            observed_at=datetime(
                2026,
                7,
                3,
                12,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            rainfall_inches_6h=d("2.400000"),
            flash_flood_guidance_inches_6h=d("2.500000"),
            antecedent_soil_saturation_ratio=d("0.700000"),
            forecast_confidence_ratio=d("0.500000"),
        ),
    )

    assert isinstance(report, module.WeatherFlashFloodGuidanceBreakDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-weather-flash-flood-guidance-break-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.next_step == (
        "block_report_only_weather_flash_flood_guidance_break_digest"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_row_count == d("1.000000")
    assert report.watch_row_count == d("1.000000")
    assert report.pass_row_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.guidance_break_count == d("1.000000")
    assert report.guidance_watch_count == d("1.000000")
    assert report.max_source_age_seconds == d("1800.000000")
    assert report.max_source_age_observed_seconds == d("5400.000000")
    assert report.max_guidance_break_ratio == d("1.280000")
    assert report.max_rainfall_inches_6h == d("3.200000")
    assert report.min_flash_flood_guidance_inches_6h == d("2.000000")
    assert report.average_forecast_confidence_ratio == d("0.633333")
    assert report.reason_codes == (
        "weather_flash_flood_guidance_break_source_stale",
        "weather_flash_flood_guidance_break_threshold_exceeded",
        "weather_flash_flood_guidance_break_heavy_rainfall",
        "weather_flash_flood_guidance_break_saturated_soil",
        "weather_flash_flood_guidance_break_threshold_watch",
        "weather_flash_flood_guidance_break_low_confidence",
    )
    assert tuple(
        (row.basin_id, row.event_id, row.row_status, row.source_age_seconds)
        for row in report.rows
    ) == (
        ("texas_hill_country", "blocked-event", "blocked", d("120.000000")),
        ("appalachia", "watch-event", "watch", d("5400.000000")),
        ("pacific_nw", "clear-event", "pass", d("120.000000")),
    )
    assert report.rows[0].guidance_break_ratio == d("1.280000")
    assert report.rows[0].reason_codes == (
        "weather_flash_flood_guidance_break_threshold_exceeded",
        "weather_flash_flood_guidance_break_heavy_rainfall",
        "weather_flash_flood_guidance_break_saturated_soil",
        "weather_flash_flood_guidance_break_low_confidence",
    )
    assert report.rows[1].observed_at == datetime(2026, 7, 3, 16, 30, tzinfo=UTC)
    assert report.rows[1].source_freshness_status == "stale"
    assert report.rows[1].guidance_break_ratio == d("0.960000")
    assert report.rows[1].reason_codes == (
        "weather_flash_flood_guidance_break_source_stale",
        "weather_flash_flood_guidance_break_threshold_watch",
        "weather_flash_flood_guidance_break_low_confidence",
    )
    assert report.rows[2].reason_codes == (
        "weather_flash_flood_guidance_break_row_clear",
    )
    assert tuple(
        (item.reason_code, item.count, item.row_ratio)
        for item in report.reason_code_counts
    ) == (
        (
            "weather_flash_flood_guidance_break_source_stale",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_flash_flood_guidance_break_threshold_exceeded",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_flash_flood_guidance_break_heavy_rainfall",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_flash_flood_guidance_break_saturated_soil",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_flash_flood_guidance_break_threshold_watch",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_flash_flood_guidance_break_low_confidence",
            d("2.000000"),
            d("0.666667"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    public = asdict(report)
    assert_no_public_float_or_int(public)


def test_empty_clear_and_json_values_are_report_only_decimal_strings() -> None:
    module = api()

    empty = digest()
    empty_json = module.market_research_weather_flash_flood_guidance_break_digest_json(
        empty,
    )
    json.dumps(empty_json, sort_keys=True)

    assert empty.digest_status == "blocked"
    assert empty.next_step == (
        "block_report_only_weather_flash_flood_guidance_break_digest"
    )
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.max_guidance_break_ratio == d("0.000000")
    assert empty.average_forecast_confidence_ratio == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "weather_flash_flood_guidance_break_digest_empty",
    )
    assert empty.reason_code_counts == (
        module.WeatherFlashFloodGuidanceBreakReasonCodeCount(
            reason_code="weather_flash_flood_guidance_break_digest_empty",
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
            "pacific_nw",
            "clear-event",
            source_id="public_qpf_summary",
            rainfall_inches_6h=d("0.500000"),
            flash_flood_guidance_inches_6h=d("2.000000"),
            antecedent_soil_saturation_ratio=d("0.300000"),
            forecast_confidence_ratio=d("0.950000"),
        ),
    )

    assert clear.digest_status == "pass"
    assert clear.next_step == (
        "continue_report_only_weather_flash_flood_guidance_break_digest"
    )
    assert clear.reason_codes == (
        "weather_flash_flood_guidance_break_digest_clear",
    )
    assert clear.reason_code_counts == (
        module.WeatherFlashFloodGuidanceBreakReasonCodeCount(
            reason_code="weather_flash_flood_guidance_break_digest_clear",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_validates_decimal_datetime_flags_duplicates_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="rainfall_inches_6h"):
        observation(rainfall_inches_6h=Decimal("NaN"))

    with pytest.raises(ValueError, match="rainfall_inches_6h"):
        observation(rainfall_inches_6h=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 3, 18, 0))

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="after generated_at"):
        digest(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unique"):
        digest(
            observation("texas_hill_country", "same-event", source_id="a"),
            observation("texas_hill_country", "same-event", source_id="b"),
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="canonical"):
        observation(basin_id="Texas")

    with pytest.raises(ValueError, match="not allowed"):
        observation(source_id="api_token")

    row = digest(observation()).rows[0]
    with pytest.raises(ValueError, match="row_status"):
        replace(row, row_status="pass")

    sorted_report = digest(
        observation(
            "alpha",
            "clear-a",
            rainfall_inches_6h=d("0.500000"),
            flash_flood_guidance_inches_6h=d("2.000000"),
            antecedent_soil_saturation_ratio=d("0.300000"),
            forecast_confidence_ratio=d("0.950000"),
        ),
        observation(
            "beta",
            "clear-b",
            rainfall_inches_6h=d("0.500000"),
            flash_flood_guidance_inches_6h=d("2.000000"),
            antecedent_soil_saturation_ratio=d("0.300000"),
            forecast_confidence_ratio=d("0.950000"),
        ),
    )
    with pytest.raises(ValueError, match="deterministic"):
        replace(sorted_report, rows=tuple(reversed(sorted_report.rows)))

    with pytest.raises(ValueError, match="generated_at"):
        digest(generated_at=datetime(2026, 7, 3, 18, 0))

    shifted_report = digest(
        generated_at=datetime(2026, 7, 3, 14, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    assert shifted_report.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="config"):
        module.build_market_research_weather_flash_flood_guidance_break_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_dataclasses_are_frozen_and_public_numerics_are_decimal_typed() -> None:
    module = api()
    row = observation()

    with pytest.raises(FrozenInstanceError):
        row.basin_id = "other"  # type: ignore[misc]

    numeric_names = (
        "count",
        "ratio",
        "seconds",
        "rainfall",
        "guidance",
    )
    for cls in (
        module.WeatherFlashFloodGuidanceBreakDigestConfig,
        module.WeatherFlashFloodGuidanceBreakObservation,
        module.WeatherFlashFloodGuidanceBreakDigestRow,
        module.WeatherFlashFloodGuidanceBreakReasonCodeCount,
        module.WeatherFlashFloodGuidanceBreakDigestReport,
    ):
        for field in fields(cls):
            if field.name != "reason_code_counts" and any(
                part in field.name for part in numeric_names
            ):
                assert field.type == "Decimal"


def test_static_source_has_no_forbidden_runtime_surfaces_or_io_calls() -> None:
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

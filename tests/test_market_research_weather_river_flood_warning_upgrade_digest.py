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


GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_weather_river_flood_warning_upgrade_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_weather_river_flood_warning_upgrade_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "max_source_age_seconds": d("3600.000000"),
        "watch_upgrade_delta": d("1.000000"),
        "blocked_upgrade_delta": d("2.000000"),
        "near_flood_stage_ratio": d("0.900000"),
        "heavy_rainfall_inches_24h": d("3.000000"),
        "low_confidence_ratio": d("0.550000"),
    }
    values.update(overrides)
    return module.WeatherRiverFloodWarningUpgradeDigestConfig(**values)


def observation(
    station_id: str = "us.tx.trinity-dallas",
    event_id: str = "warning-upgrade-alpha",
    *,
    source_id: str = "public_river_gauge",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    prior_warning_level: Decimal = d("1.000000"),
    current_warning_level: Decimal = d("4.000000"),
    river_stage_feet: Decimal = d("31.200000"),
    flood_stage_feet: Decimal = d("30.000000"),
    forecast_crest_feet: Decimal = d("32.100000"),
    rainfall_inches_24h: Decimal = d("4.200000"),
    source_confidence_ratio: Decimal = d("0.490000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.WeatherRiverFloodWarningUpgradeObservation(
        station_id=station_id,
        event_id=event_id,
        source_id=source_id,
        observed_at=observed_at,
        prior_warning_level=prior_warning_level,
        current_warning_level=current_warning_level,
        river_stage_feet=river_stage_feet,
        flood_stage_feet=flood_stage_feet,
        forecast_crest_feet=forecast_crest_feet,
        rainfall_inches_24h=rainfall_inches_24h,
        source_confidence_ratio=source_confidence_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    *rows: object,
    generated_at: datetime = GENERATED_AT,
    cfg: object | None = None,
) -> Any:
    module = api()
    return module.build_market_research_weather_river_flood_warning_upgrade_digest(
        rows,
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


def test_builds_report_only_river_flood_warning_upgrade_digest_deterministically() -> None:
    module = api()

    report = digest(
        observation(
            "us.or.willamette-portland",
            "clear-event",
            source_id="public_stage_summary",
            prior_warning_level=d("1.000000"),
            current_warning_level=d("1.000000"),
            river_stage_feet=d("8.000000"),
            flood_stage_feet=d("18.000000"),
            forecast_crest_feet=d("10.000000"),
            rainfall_inches_24h=d("0.700000"),
            source_confidence_ratio=d("0.920000"),
        ),
        observation(
            "us.tx.trinity-dallas",
            "major-upgrade-event",
            source_id="public_river_gauge",
            observed_at=datetime(
                2026,
                7,
                4,
                9,
                58,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
            prior_warning_level=d("1.000000"),
            current_warning_level=d("4.000000"),
            river_stage_feet=d("31.200000"),
            flood_stage_feet=d("30.000000"),
            forecast_crest_feet=d("32.100000"),
            rainfall_inches_24h=d("4.200000"),
            source_confidence_ratio=d("0.490000"),
        ),
        observation(
            "us.ia.cedar-cedar-rapids",
            "minor-upgrade-event",
            source_id="public_river_report",
            observed_at=datetime(
                2026,
                7,
                4,
                8,
                30,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
            prior_warning_level=d("1.000000"),
            current_warning_level=d("2.000000"),
            river_stage_feet=d("19.000000"),
            flood_stage_feet=d("20.000000"),
            forecast_crest_feet=d("19.500000"),
            rainfall_inches_24h=d("2.000000"),
            source_confidence_ratio=d("0.600000"),
        ),
    )

    assert isinstance(report, module.WeatherRiverFloodWarningUpgradeDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-weather-river-flood-warning-upgrade-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.next_step == (
        "block_report_only_weather_river_flood_warning_upgrade_digest"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_row_count == d("1.000000")
    assert report.watch_row_count == d("1.000000")
    assert report.pass_row_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.upgrade_count == d("2.000000")
    assert report.major_upgrade_count == d("1.000000")
    assert report.current_above_flood_stage_count == d("1.000000")
    assert report.forecast_above_flood_stage_count == d("1.000000")
    assert report.max_source_age_seconds == d("3600.000000")
    assert report.max_source_age_observed_seconds == d("5400.000000")
    assert report.max_warning_level_delta == d("3.000000")
    assert report.max_river_stage_ratio == d("1.040000")
    assert report.max_forecast_crest_ratio == d("1.070000")
    assert report.max_rainfall_inches_24h == d("4.200000")
    assert report.average_source_confidence_ratio == d("0.670000")
    assert report.reason_codes == (
        "weather_river_flood_warning_upgrade_source_stale",
        "weather_river_flood_warning_upgrade_major_upgrade",
        "weather_river_flood_warning_upgrade_level_upgrade",
        "weather_river_flood_warning_upgrade_stage_above_flood_stage",
        "weather_river_flood_warning_upgrade_forecast_above_flood_stage",
        "weather_river_flood_warning_upgrade_stage_near_flood_stage",
        "weather_river_flood_warning_upgrade_forecast_near_flood_stage",
        "weather_river_flood_warning_upgrade_heavy_rainfall",
        "weather_river_flood_warning_upgrade_low_confidence",
    )
    assert tuple(
        (row.station_id, row.event_id, row.row_status, row.source_age_seconds)
        for row in report.rows
    ) == (
        ("us.tx.trinity-dallas", "major-upgrade-event", "blocked", d("120.000000")),
        ("us.ia.cedar-cedar-rapids", "minor-upgrade-event", "watch", d("5400.000000")),
        ("us.or.willamette-portland", "clear-event", "pass", d("120.000000")),
    )

    blocked = report.rows[0]
    assert blocked.observed_at == datetime(2026, 7, 4, 14, 58, tzinfo=UTC)
    assert blocked.warning_level_delta == d("3.000000")
    assert blocked.river_stage_ratio == d("1.040000")
    assert blocked.forecast_crest_ratio == d("1.070000")
    assert blocked.reason_codes == (
        "weather_river_flood_warning_upgrade_major_upgrade",
        "weather_river_flood_warning_upgrade_stage_above_flood_stage",
        "weather_river_flood_warning_upgrade_forecast_above_flood_stage",
        "weather_river_flood_warning_upgrade_heavy_rainfall",
        "weather_river_flood_warning_upgrade_low_confidence",
    )

    watch = report.rows[1]
    assert watch.source_freshness_status == "stale"
    assert watch.warning_level_delta == d("1.000000")
    assert watch.river_stage_ratio == d("0.950000")
    assert watch.forecast_crest_ratio == d("0.975000")
    assert watch.reason_codes == (
        "weather_river_flood_warning_upgrade_source_stale",
        "weather_river_flood_warning_upgrade_level_upgrade",
        "weather_river_flood_warning_upgrade_stage_near_flood_stage",
        "weather_river_flood_warning_upgrade_forecast_near_flood_stage",
    )
    assert report.rows[2].reason_codes == (
        "weather_river_flood_warning_upgrade_row_clear",
    )

    assert tuple(
        (item.reason_code, item.count, item.row_ratio)
        for item in report.reason_code_counts
    ) == (
        (
            "weather_river_flood_warning_upgrade_source_stale",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_warning_upgrade_major_upgrade",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_warning_upgrade_level_upgrade",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_warning_upgrade_stage_above_flood_stage",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_warning_upgrade_forecast_above_flood_stage",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_warning_upgrade_stage_near_flood_stage",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_warning_upgrade_forecast_near_flood_stage",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_warning_upgrade_heavy_rainfall",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "weather_river_flood_warning_upgrade_low_confidence",
            d("1.000000"),
            d("0.333333"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_no_public_float_or_int(asdict(report))


def test_empty_and_clear_digest_are_decimal_stringed_report_only_values() -> None:
    module = api()

    empty = digest()
    empty_json = module.market_research_weather_river_flood_warning_upgrade_digest_json(
        empty,
    )
    json.dumps(empty_json, sort_keys=True)

    assert empty.digest_status == "blocked"
    assert empty.next_step == (
        "block_report_only_weather_river_flood_warning_upgrade_digest"
    )
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.max_warning_level_delta == d("0.000000")
    assert empty.average_source_confidence_ratio == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "weather_river_flood_warning_upgrade_digest_empty",
    )
    assert empty.reason_code_counts == (
        module.WeatherRiverFloodWarningUpgradeReasonCodeCount(
            reason_code="weather_river_flood_warning_upgrade_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert empty_json["generated_at"] == "2026-07-04T15:00:00+00:00"
    assert empty_json["row_count"] == "0.000000"
    assert empty_json["reason_code_counts"][0]["count"] == "1.000000"
    assert empty_json["paper_only"] is True
    assert empty_json["report_only"] is True
    assert empty_json["readonly"] is True
    assert_no_public_float_or_int(empty_json)
    assert not any(isinstance(value, Decimal) for value in walk_values(empty_json))

    clear = digest(
        observation(
            "us.or.willamette-portland",
            "clear-event",
            source_id="public_stage_summary",
            prior_warning_level=d("1.000000"),
            current_warning_level=d("1.000000"),
            river_stage_feet=d("8.000000"),
            flood_stage_feet=d("18.000000"),
            forecast_crest_feet=d("10.000000"),
            rainfall_inches_24h=d("0.700000"),
            source_confidence_ratio=d("0.920000"),
        ),
    )

    assert clear.digest_status == "pass"
    assert clear.next_step == (
        "continue_report_only_weather_river_flood_warning_upgrade_digest"
    )
    assert clear.reason_codes == (
        "weather_river_flood_warning_upgrade_digest_clear",
    )
    assert clear.reason_code_counts == (
        module.WeatherRiverFloodWarningUpgradeReasonCodeCount(
            reason_code="weather_river_flood_warning_upgrade_digest_clear",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_validates_decimal_datetime_flags_duplicates_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="current_warning_level"):
        observation(current_warning_level=Decimal("NaN"))

    with pytest.raises(ValueError, match="rainfall_inches_24h"):
        observation(rainfall_inches_24h=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 4, 15, 0))

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="after generated_at"):
        digest(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unique"):
        digest(
            observation("us.tx.trinity-dallas", "same-event", source_id="a"),
            observation("us.tx.trinity-dallas", "same-event", source_id="b"),
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="canonical"):
        observation(station_id="US.TX")

    with pytest.raises(ValueError, match="not allowed"):
        observation(source_id="api_token")

    with pytest.raises(ValueError, match="flood_stage_feet"):
        observation(flood_stage_feet=d("0.000000"))

    with pytest.raises(ValueError, match="current_warning_level"):
        observation(
            prior_warning_level=d("3.000000"),
            current_warning_level=d("2.000000"),
        )

    row = digest(observation()).rows[0]
    with pytest.raises(ValueError, match="row_status"):
        replace(row, row_status="pass")

    sorted_report = digest(
        observation(
            "us.aa.alpha",
            "clear-a",
            prior_warning_level=d("1.000000"),
            current_warning_level=d("1.000000"),
            river_stage_feet=d("8.000000"),
            flood_stage_feet=d("18.000000"),
            forecast_crest_feet=d("10.000000"),
            rainfall_inches_24h=d("0.700000"),
            source_confidence_ratio=d("0.920000"),
        ),
        observation(
            "us.bb.beta",
            "clear-b",
            prior_warning_level=d("1.000000"),
            current_warning_level=d("1.000000"),
            river_stage_feet=d("8.000000"),
            flood_stage_feet=d("18.000000"),
            forecast_crest_feet=d("10.000000"),
            rainfall_inches_24h=d("0.700000"),
            source_confidence_ratio=d("0.920000"),
        ),
    )
    with pytest.raises(ValueError, match="deterministic"):
        replace(sorted_report, rows=tuple(reversed(sorted_report.rows)))


def test_dataclasses_are_frozen_and_public_numerics_are_decimal_typed() -> None:
    module = api()
    row = observation()

    with pytest.raises(FrozenInstanceError):
        row.station_id = "other"  # type: ignore[misc]

    numeric_names = (
        "count",
        "ratio",
        "seconds",
        "feet",
        "inches",
        "level",
        "delta",
    )
    for cls in (
        module.WeatherRiverFloodWarningUpgradeDigestConfig,
        module.WeatherRiverFloodWarningUpgradeObservation,
        module.WeatherRiverFloodWarningUpgradeDigestRow,
        module.WeatherRiverFloodWarningUpgradeReasonCodeCount,
        module.WeatherRiverFloodWarningUpgradeDigestReport,
    ):
        assert is_dataclass(cls)
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
        "trading",
        "auth",
        "wallet",
        "account",
        "order",
        "cancel",
        "replace",
        "exchange",
        "secret",
        "token",
        "private_key",
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

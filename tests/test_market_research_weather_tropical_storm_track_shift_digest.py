from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_weather_tropical_storm_track_shift_digest"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_weather_tropical_storm_track_shift_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_WEATHER_TROPICAL_STORM_TRACK_SHIFT_DIGEST_CONFIG_VERSION
        ),
        "watch_track_shift_km": Decimal("50.000000"),
        "blocked_track_shift_km": Decimal("100.000000"),
        "watch_landfall_probability_delta": Decimal("0.100000"),
        "blocked_landfall_probability_delta": Decimal("0.250000"),
        "max_forecast_age_seconds": Decimal("21600.000000"),
        "min_source_family_count": Decimal("2.000000"),
    }
    values.update(overrides)
    return module.WeatherTropicalStormTrackShiftConfig(**values)


def observation(
    observation_id: str,
    *,
    storm_id: str = "al052026",
    basin: str = "atlantic",
    source_family: str = "global_model",
    forecast_issued_at: datetime = GENERATED_AT - timedelta(hours=2),
    forecast_hour: Decimal = Decimal("72.000000"),
    track_shift_km: Decimal = Decimal("20.000000"),
    landfall_probability_delta: Decimal = Decimal("0.020000"),
    source_row_count: Decimal = Decimal("4.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.WeatherTropicalStormTrackShiftObservation(
        observation_id=observation_id,
        storm_id=storm_id,
        basin=basin,
        source_family=source_family,
        forecast_issued_at=forecast_issued_at,
        forecast_hour=forecast_hour,
        track_shift_km=track_shift_km,
        landfall_probability_delta=landfall_probability_delta,
        source_row_count=source_row_count,
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
    return module.build_market_research_weather_tropical_storm_track_shift_digest(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_builds_track_shift_digest_with_utc_decimal_sorting_and_reasons() -> None:
    report = digest(
        (
            observation(
                "stable_guidance",
                source_family="ensemble_blend",
                track_shift_km=Decimal("15.000000"),
                landfall_probability_delta=Decimal("0.010000"),
            ),
            observation(
                "watch_guidance",
                source_family="regional_model",
                forecast_issued_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    55,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                track_shift_km=Decimal("60.000000"),
                landfall_probability_delta=Decimal("0.050000"),
            ),
            observation(
                "blocked_guidance",
                forecast_issued_at=GENERATED_AT - timedelta(hours=7),
                track_shift_km=Decimal("125.000000"),
                landfall_probability_delta=Decimal("0.300000"),
                source_row_count=Decimal("8.000000"),
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.observation_count == Decimal("3.000000")
    assert report.source_row_count == Decimal("16.000000")
    assert report.blocked_observation_count == Decimal("1.000000")
    assert report.watch_observation_count == Decimal("1.000000")
    assert report.pass_observation_count == Decimal("1.000000")
    assert report.source_family_count == Decimal("3.000000")
    assert report.stale_forecast_count == Decimal("1.000000")
    assert report.max_track_shift_km == Decimal("125.000000")
    assert report.max_landfall_probability_delta == Decimal("0.300000")
    assert report.max_risk_score == Decimal("1.000000")
    assert report.average_risk_score == Decimal("0.533333")
    assert report.blocked_observation_ratio == Decimal("0.333333")
    assert report.digest_status == "blocked"
    assert report.screening_next_step == (
        "block_report_only_weather_tropical_storm_track_shift_screen"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.observation_id for row in report.shift_rows) == (
        "blocked_guidance",
        "watch_guidance",
        "stable_guidance",
    )

    blocked = report.shift_rows[0]
    assert blocked.forecast_age_seconds == Decimal("25200.000000")
    assert blocked.risk_status == "blocked"
    assert blocked.risk_score == Decimal("1.000000")
    assert blocked.reason_codes == (
        "weather_tropical_storm_track_shift_blocked_track_shift",
        "weather_tropical_storm_track_shift_blocked_landfall_probability_delta",
        "weather_tropical_storm_track_shift_stale_forecast",
    )

    watch = report.shift_rows[1]
    assert watch.forecast_issued_at == datetime(2026, 7, 4, 11, 55, tzinfo=UTC)
    assert watch.forecast_age_seconds == Decimal("300.000000")
    assert watch.risk_status == "watch"
    assert watch.risk_score == Decimal("0.600000")
    assert watch.reason_codes == (
        "weather_tropical_storm_track_shift_watch_track_shift",
    )

    assert report.reason_codes == (
        "weather_tropical_storm_track_shift_blocked_risk_present",
        "weather_tropical_storm_track_shift_watch_risk_present",
    )
    assert tuple((item.reason_code, item.count) for item in report.reason_code_counts) == (
        (
            "weather_tropical_storm_track_shift_blocked_track_shift",
            Decimal("1.000000"),
        ),
        (
            "weather_tropical_storm_track_shift_blocked_landfall_probability_delta",
            Decimal("1.000000"),
        ),
        (
            "weather_tropical_storm_track_shift_watch_track_shift",
            Decimal("1.000000"),
        ),
        (
            "weather_tropical_storm_track_shift_stale_forecast",
            Decimal("1.000000"),
        ),
        (
            "weather_tropical_storm_track_shift_observed_stable",
            Decimal("1.000000"),
        ),
    )
    _assert_public_numerics_are_decimals(report)


def test_empty_digest_payload_is_report_only_and_serializes_decimal_strings() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_weather_tropical_storm_track_shift_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert report.digest_status == "blocked"
    assert report.observation_count == Decimal("0.000000")
    assert report.source_row_count == Decimal("0.000000")
    assert report.max_track_shift_km == Decimal("0.000000")
    assert report.average_risk_score == Decimal("0.000000")
    assert report.reason_codes == (
        "weather_tropical_storm_track_shift_digest_empty",
    )
    assert tuple((item.reason_code, item.count) for item in report.reason_code_counts) == (
        ("weather_tropical_storm_track_shift_digest_empty", Decimal("1.000000")),
    )
    assert report.shift_rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["observation_count"] == "0.000000"
    assert payload["shift_rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_int_or_decimal(payload)


def test_input_order_does_not_affect_report_order_or_reason_codes() -> None:
    observations = (
        observation(
            "z_watch_delta",
            source_family="regional_model",
            landfall_probability_delta=Decimal("0.110000"),
        ),
        observation(
            "a_blocked_shift",
            track_shift_km=Decimal("120.000000"),
        ),
        observation(
            "m_pass",
            source_family="ensemble_blend",
        ),
    )

    first = digest(observations)
    second = digest(tuple(reversed(observations)))

    assert asdict(first) == asdict(second)
    assert tuple(row.observation_id for row in first.shift_rows) == (
        "a_blocked_shift",
        "z_watch_delta",
        "m_pass",
    )
    assert first.reason_codes == (
        "weather_tropical_storm_track_shift_blocked_risk_present",
        "weather_tropical_storm_track_shift_watch_risk_present",
    )


def test_validation_rejects_bad_numerics_times_duplicates_flags_and_unsafe_text() -> None:
    module = api()

    with pytest.raises(ValueError, match="watch_track_shift_km"):
        config(watch_track_shift_km=50)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="blocked_track_shift_km"):
        config(blocked_track_shift_km=_DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="blocked_track_shift_km"):
        config(
            watch_track_shift_km=Decimal("200.000000"),
            blocked_track_shift_km=Decimal("100.000000"),
        )
    with pytest.raises(ValueError, match="forecast_issued_at"):
        observation("naive_time", forecast_issued_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="forecast_issued_at"):
        observation(
            "datetime_subclass",
            forecast_issued_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="track_shift_km"):
        observation("bad_metric", track_shift_km=Decimal("nan"))
    with pytest.raises(ValueError, match="unsafe tropical storm track detail"):
        observation("contains_private_key")
    with pytest.raises(ValueError, match="future"):
        digest(
            (
                observation(
                    "future_forecast",
                    forecast_issued_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="duplicate observation_id"):
        digest(
            (
                observation("duplicate"),
                observation("duplicate", source_family="regional_model"),
            ),
        )
    with pytest.raises(ValueError, match="observations"):
        module.build_market_research_weather_tropical_storm_track_shift_digest(
            "not observations",  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report_only"):
        observation("bad_flag", report_only=False)

    report = digest((observation("stable_one"),))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.market_research_weather_tropical_storm_track_shift_digest_payload(
            unsafe_report,
        )
    with pytest.raises(ValueError, match="report"):
        module.market_research_weather_tropical_storm_track_shift_digest_payload(
            {"bad": "value"},
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_public_numerics() -> None:
    module = api()
    report = digest((observation("stable_one"),))

    for item in (config(), observation("sample"), report, *report.shift_rows):
        assert is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        report.observation_count = Decimal("2.000000")  # type: ignore[misc]

    public_classes = (
        module.WeatherTropicalStormTrackShiftConfig,
        module.WeatherTropicalStormTrackShiftObservation,
        module.WeatherTropicalStormTrackShiftRow,
        module.WeatherTropicalStormTrackShiftReasonCodeCount,
        module.WeatherTropicalStormTrackShiftReport,
    )
    for klass in public_classes:
        assert all(
            field.type not in (int, float)
            for field in fields(klass)
            if field.name not in {"paper_only", "report_only", "readonly"}
        )


def test_payload_redacts_numeric_types_and_rejects_mutated_unsafe_public_content() -> None:
    module = api()
    report = digest((observation("stable_one"),))
    payload = module.market_research_weather_tropical_storm_track_shift_digest_payload(
        report,
    )

    assert payload == module.market_research_weather_tropical_storm_track_shift_digest_payload(
        report,
    )
    assert payload["shift_rows"][0]["track_shift_km"] == "20.000000"
    assert_no_public_float_int_or_decimal(payload)

    bad_row = replace(report.shift_rows[0])
    object.__setattr__(bad_row, "observation_id", "private_key")
    with pytest.raises(ValueError, match="unsafe tropical storm track detail"):
        replace(report, shift_rows=(bad_row,))


def test_module_has_no_io_network_auth_trading_or_durable_surface() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)
    module_path = Path(__file__).resolve().parents[1] / MODULE_PATH
    disk_source = module_path.read_text()

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "private_key",
        "sqlite",
        "postgres",
        "redis",
        "requests.",
        "httpx.",
        "socket.",
        "open(",
        "write_text",
        "read_text",
        "unlink(",
        "remove(",
        "wallet",
        "fast_mode",
    ):
        assert token not in disk_source.lower()

    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "cancel",
        "connect",
        "execute",
        "open",
        "place_order",
        "read_text",
        "request",
        "submit",
        "write_text",
    }

    imports: list[str] = []
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                calls.append(call_name.rsplit(".", maxsplit=1)[-1])

    assert not (set(name.split(".", maxsplit=1)[0] for name in imports) & forbidden_import_roots)
    assert not (set(calls) & forbidden_calls)
    assert "market_slug" not in source
    assert "wallet" not in source
    assert "broker" not in source
    assert "signing" not in source


def assert_no_public_float_int_or_decimal(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (Decimal, float, int)):
        pytest.fail(f"public serialized numeric must be a string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_int_or_decimal(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_float_int_or_decimal(item)


def _assert_public_numerics_are_decimals(value: object) -> None:
    assert is_dataclass(value)
    for field in fields(value):
        field_value = getattr(value, field.name)
        if isinstance(field_value, bool):
            continue
        if isinstance(field_value, int):
            pytest.fail(f"{field.name} exposed int numeric instead of Decimal")
        if isinstance(field_value, tuple):
            for item in field_value:
                if is_dataclass(item):
                    _assert_public_numerics_are_decimals(item)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None

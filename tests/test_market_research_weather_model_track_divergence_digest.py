from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_weather_model_track_divergence_digest import (
    DEFAULT_WEATHER_MODEL_TRACK_DIVERGENCE_DIGEST_CONFIG_VERSION,
    WeatherModelTrackDivergenceConfig,
    WeatherModelTrackDivergenceObservation,
    WeatherModelTrackDivergenceReport,
    build_market_research_weather_model_track_divergence_digest,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def _config(**overrides: object) -> WeatherModelTrackDivergenceConfig:
    values = {
        "config_version": DEFAULT_WEATHER_MODEL_TRACK_DIVERGENCE_DIGEST_CONFIG_VERSION,
        "watch_track_spread_km": Decimal("75.000000"),
        "blocked_track_spread_km": Decimal("150.000000"),
        "watch_track_shift_km": Decimal("50.000000"),
        "blocked_track_shift_km": Decimal("100.000000"),
        "max_model_age_seconds": Decimal("21600.000000"),
        "min_source_family_count": Decimal("2.000000"),
    }
    values.update(overrides)
    return WeatherModelTrackDivergenceConfig(**values)


def _observation(
    observation_id: str,
    *,
    event_id: str = "atlantic_storm",
    source_family: str = "global_model",
    model_run_at: datetime = GENERATED_AT - timedelta(hours=2),
    forecast_hour: Decimal = Decimal("72.000000"),
    track_spread_km: Decimal = Decimal("20.000000"),
    track_shift_km: Decimal = Decimal("10.000000"),
    source_row_count: Decimal = Decimal("4.000000"),
) -> WeatherModelTrackDivergenceObservation:
    return WeatherModelTrackDivergenceObservation(
        observation_id=observation_id,
        event_id=event_id,
        source_family=source_family,
        model_run_at=model_run_at,
        forecast_hour=forecast_hour,
        track_spread_km=track_spread_km,
        track_shift_km=track_shift_km,
        source_row_count=source_row_count,
    )


def test_empty_digest_is_blocked_report_only_and_uses_decimals() -> None:
    report = build_market_research_weather_model_track_divergence_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, WeatherModelTrackDivergenceReport)
    assert report.generated_at == GENERATED_AT
    assert report.digest_status == "blocked"
    assert report.screening_next_step == (
        "block_report_only_weather_model_track_divergence_screen"
    )
    assert report.observation_count == Decimal("0.000000")
    assert report.source_row_count == Decimal("0.000000")
    assert report.source_family_count == Decimal("0.000000")
    assert report.max_track_spread_km == Decimal("0.000000")
    assert report.max_track_shift_km == Decimal("0.000000")
    assert report.max_risk_score == Decimal("0.000000")
    assert report.average_risk_score == Decimal("0.000000")
    assert report.blocked_observation_ratio == Decimal("0.000000")
    assert report.divergence_rows == ()
    assert report.reason_codes == (
        "weather_model_track_divergence_digest_empty",
    )
    assert tuple((item.reason_code, item.count) for item in report.reason_code_counts) == (
        ("weather_model_track_divergence_digest_empty", Decimal("1.000000")),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    _assert_public_numerics_are_decimals(report)


def test_high_risk_track_divergence_blocks_probability_event_screening() -> None:
    report = build_market_research_weather_model_track_divergence_digest(
        (
            _observation(
                "watch_guidance",
                event_id="atlantic_storm",
                source_family="regional_model",
                track_spread_km=Decimal("80.000000"),
                track_shift_km=Decimal("20.000000"),
            ),
            _observation(
                "blocked_guidance",
                event_id="atlantic_storm",
                source_family="global_model",
                model_run_at=GENERATED_AT - timedelta(hours=7),
                track_spread_km=Decimal("180.000000"),
                track_shift_km=Decimal("120.000000"),
                source_row_count=Decimal("8.000000"),
            ),
            _observation(
                "stable_guidance",
                event_id="atlantic_storm",
                source_family="ensemble_blend",
                track_spread_km=Decimal("15.000000"),
                track_shift_km=Decimal("5.000000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert report.screening_next_step == (
        "block_report_only_weather_model_track_divergence_screen"
    )
    assert report.observation_count == Decimal("3.000000")
    assert report.source_row_count == Decimal("16.000000")
    assert report.blocked_observation_count == Decimal("1.000000")
    assert report.watch_observation_count == Decimal("1.000000")
    assert report.pass_observation_count == Decimal("1.000000")
    assert report.stale_model_run_count == Decimal("1.000000")
    assert report.source_family_count == Decimal("3.000000")
    assert report.max_track_spread_km == Decimal("180.000000")
    assert report.max_track_shift_km == Decimal("120.000000")
    assert report.max_risk_score == Decimal("1.000000")
    assert report.blocked_observation_ratio == Decimal("0.333333")
    assert report.reason_codes == (
        "weather_model_track_divergence_blocked_risk_present",
        "weather_model_track_divergence_watch_risk_present",
    )
    assert tuple(row.observation_id for row in report.divergence_rows) == (
        "blocked_guidance",
        "watch_guidance",
        "stable_guidance",
    )
    assert report.divergence_rows[0].model_age_seconds == Decimal("25200.000000")
    assert report.divergence_rows[0].risk_status == "blocked"
    assert report.divergence_rows[0].reason_codes == (
        "weather_model_track_divergence_blocked_spread",
        "weather_model_track_divergence_blocked_shift",
        "weather_model_track_divergence_stale_model_run",
    )
    assert report.divergence_rows[1].risk_status == "watch"
    assert report.divergence_rows[1].reason_codes == (
        "weather_model_track_divergence_watch_spread",
    )
    assert tuple((item.reason_code, item.count) for item in report.reason_code_counts) == (
        ("weather_model_track_divergence_blocked_spread", Decimal("1.000000")),
        ("weather_model_track_divergence_blocked_shift", Decimal("1.000000")),
        ("weather_model_track_divergence_watch_spread", Decimal("1.000000")),
        ("weather_model_track_divergence_stale_model_run", Decimal("1.000000")),
        ("weather_model_track_divergence_observed_stable", Decimal("1.000000")),
    )
    _assert_public_numerics_are_decimals(report)


def test_input_order_does_not_affect_report_order_or_reason_codes() -> None:
    observations = (
        _observation(
            "z_watch_shift",
            event_id="event_b",
            source_family="regional_model",
            track_shift_km=Decimal("55.000000"),
        ),
        _observation(
            "a_blocked_spread",
            event_id="event_a",
            source_family="global_model",
            track_spread_km=Decimal("160.000000"),
        ),
        _observation(
            "m_pass",
            event_id="event_a",
            source_family="ensemble_blend",
        ),
    )

    first = build_market_research_weather_model_track_divergence_digest(
        observations,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    second = build_market_research_weather_model_track_divergence_digest(
        tuple(reversed(observations)),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert asdict(first) == asdict(second)
    assert tuple(row.observation_id for row in first.divergence_rows) == (
        "a_blocked_spread",
        "z_watch_shift",
        "m_pass",
    )
    assert first.reason_codes == (
        "weather_model_track_divergence_blocked_risk_present",
        "weather_model_track_divergence_watch_risk_present",
    )


def test_validation_rejects_non_decimal_naive_time_future_rows_duplicates_and_unsafe_text() -> None:
    with pytest.raises(ValueError, match="watch_track_spread_km"):
        _config(watch_track_spread_km=75)
    with pytest.raises(ValueError, match="blocked_track_spread_km"):
        _config(blocked_track_spread_km=_DecimalSubclass("150"))
    with pytest.raises(ValueError, match="blocked_track_spread_km"):
        _config(
            watch_track_spread_km=Decimal("200.000000"),
            blocked_track_spread_km=Decimal("150.000000"),
        )
    with pytest.raises(ValueError, match="model_run_at"):
        _observation("naive_time", model_run_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="model_run_at"):
        _observation(
            "datetime_subclass",
            model_run_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="track_spread_km"):
        _observation("float_metric", track_spread_km=Decimal("nan"))
    with pytest.raises(ValueError, match="unsafe weather model track detail"):
        _observation("contains_private_key")
    with pytest.raises(ValueError, match="future"):
        build_market_research_weather_model_track_divergence_digest(
            (
                _observation(
                    "future_run",
                    model_run_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate observation_id"):
        build_market_research_weather_model_track_divergence_digest(
            (
                _observation("duplicate"),
                _observation("duplicate", source_family="regional_model"),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations"):
        build_market_research_weather_model_track_divergence_digest(
            "not observations",  # type: ignore[arg-type]
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_frozen_hard_flags_are_enforced_on_config_rows_and_report() -> None:
    config = _config()
    with pytest.raises(FrozenInstanceError):
        config.max_model_age_seconds = Decimal("60.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        WeatherModelTrackDivergenceObservation(
            observation_id="bad_flag",
            event_id="atlantic_storm",
            source_family="global_model",
            model_run_at=GENERATED_AT,
            forecast_hour=Decimal("72.000000"),
            track_spread_km=Decimal("20.000000"),
            track_shift_km=Decimal("10.000000"),
            source_row_count=Decimal("4.000000"),
            report_only=False,
        )

    report = build_market_research_weather_model_track_divergence_digest(
        (_observation("stable_one"),),
        config=replace(config, min_source_family_count=Decimal("1.000000")),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_non_default_thresholds_change_screening_status() -> None:
    observation = _observation(
        "borderline_default_watch",
        source_family="global_model",
        track_spread_km=Decimal("80.000000"),
        track_shift_km=Decimal("45.000000"),
    )

    default_report = build_market_research_weather_model_track_divergence_digest(
        (observation,),
        config=replace(_config(), min_source_family_count=Decimal("1.000000")),
        generated_at=GENERATED_AT,
    )
    relaxed_report = build_market_research_weather_model_track_divergence_digest(
        (observation,),
        config=replace(
            _config(),
            watch_track_spread_km=Decimal("90.000000"),
            blocked_track_spread_km=Decimal("200.000000"),
            min_source_family_count=Decimal("1.000000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert default_report.digest_status == "watch"
    assert default_report.reason_codes == (
        "weather_model_track_divergence_watch_risk_present",
    )
    assert default_report.divergence_rows[0].risk_status == "watch"
    assert relaxed_report.digest_status == "pass"
    assert relaxed_report.reason_codes == (
        "weather_model_track_divergence_digest_clear",
    )
    assert relaxed_report.divergence_rows[0].risk_status == "pass"
    assert relaxed_report.watch_track_spread_km == Decimal("90.000000")
    assert relaxed_report.blocked_track_spread_km == Decimal("200.000000")


def test_module_uses_no_io_network_runtime_mutation_or_sensitive_payloads() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_weather_model_track_divergence_digest",
    )
    source = inspect.getsource(module)
    tree = ast.parse(source)
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
        "buy",
        "cancel",
        "connect",
        "execute",
        "open",
        "place_order",
        "read_text",
        "request",
        "sell",
        "sign",
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
    assert "question" not in source
    assert "wallet" not in source
    assert "broker" not in source
    assert "signing" not in source


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

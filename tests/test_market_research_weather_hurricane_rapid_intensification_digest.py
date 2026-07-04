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
    "market_research_weather_hurricane_rapid_intensification_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_weather_hurricane_rapid_intensification_digest",
    )


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "weather-hurricane-rapid-intensification-digest-v1",
        "max_source_age_seconds": Decimal("900.000000"),
        "rapid_intensification_24h_threshold_knots": Decimal("30.000000"),
        "watch_intensification_24h_threshold_knots": Decimal("15.000000"),
        "rapid_intensification_probability_threshold": Decimal("0.550000"),
        "watch_probability_threshold": Decimal("0.250000"),
        "min_watch_confidence": Decimal("0.600000"),
        "high_confidence_threshold": Decimal("0.800000"),
    }
    values.update(overrides)
    return module.WeatherHurricaneRapidIntensificationDigestConfig(**values)


def observation(
    event_id: str = "al05-2026-ri",
    *,
    storm_id: str = "al052026",
    basin: str = "atlantic",
    storm_name: str = "iris",
    forecast_region: str = "western-atlantic",
    source_reference: str = "nhc-public-advisory-12",
    forecast_valid_at: datetime = GENERATED_AT - timedelta(minutes=10),
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    current_max_sustained_wind_knots: Decimal = Decimal("65.000000"),
    forecast_24h_max_sustained_wind_knots: Decimal = Decimal("100.000000"),
    intensification_24h_knots: Decimal = Decimal("35.000000"),
    rapid_intensification_probability: Decimal = Decimal("0.680000"),
    forecast_confidence: Decimal = Decimal("0.860000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.WeatherHurricaneRapidIntensificationObservation(
        event_id=event_id,
        storm_id=storm_id,
        basin=basin,
        storm_name=storm_name,
        forecast_region=forecast_region,
        source_reference=source_reference,
        forecast_valid_at=forecast_valid_at,
        source_observed_at=source_observed_at,
        current_max_sustained_wind_knots=current_max_sustained_wind_knots,
        forecast_24h_max_sustained_wind_knots=forecast_24h_max_sustained_wind_knots,
        intensification_24h_knots=intensification_24h_knots,
        rapid_intensification_probability=rapid_intensification_probability,
        forecast_confidence=forecast_confidence,
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
    return module.build_market_research_weather_hurricane_rapid_intensification_digest(
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


def test_builds_high_risk_digest_with_utc_decimal_sorting_and_reasons() -> None:
    report = digest(
        (
            observation(
                "zeta-stale",
                storm_id="ep112026",
                basin="eastern-pacific",
                storm_name="kiko",
                forecast_region="baja-california",
                source_reference="https://weather.example/advisory?apikey=secret-123",
                source_observed_at=GENERATED_AT - timedelta(seconds=3600),
                current_max_sustained_wind_knots=Decimal("40.000000"),
                forecast_24h_max_sustained_wind_knots=Decimal("45.000000"),
                intensification_24h_knots=Decimal("5.000000"),
                rapid_intensification_probability=Decimal("0.120000"),
                forecast_confidence=Decimal("0.520000"),
                upstream_reason_codes=("official_advisory",),
            ),
            observation(
                "alpha-ri",
                forecast_valid_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    50,
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
                current_max_sustained_wind_knots=Decimal("70.000000"),
                forecast_24h_max_sustained_wind_knots=Decimal("105.000000"),
                intensification_24h_knots=Decimal("35.000000"),
                rapid_intensification_probability=Decimal("0.700000"),
                forecast_confidence=Decimal("0.910000"),
                upstream_reason_codes=("model_consensus",),
            ),
            observation(
                "beta-watch",
                storm_id="wp072026",
                basin="western-pacific",
                storm_name="mayari",
                forecast_region="luzon",
                current_max_sustained_wind_knots=Decimal("45.000000"),
                forecast_24h_max_sustained_wind_knots=Decimal("64.000000"),
                intensification_24h_knots=Decimal("19.000000"),
                rapid_intensification_probability=Decimal("0.310000"),
                forecast_confidence=Decimal("0.700000"),
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.input_count == Decimal("3.000000")
    assert report.row_count == Decimal("3.000000")
    assert report.rapid_intensification_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.low_signal_count == Decimal("1.000000")
    assert report.stale_source_count == Decimal("1.000000")
    assert report.max_rapid_intensification_probability == Decimal("0.700000")
    assert report.max_intensification_24h_knots == Decimal("35.000000")
    assert report.max_forecast_24h_max_sustained_wind_knots == Decimal("105.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.event_id, row.rapid_intensification_status)
        for row in report.rows
    ] == [
        ("alpha-ri", "rapid_intensification_signal"),
        ("beta-watch", "rapid_intensification_watch"),
        ("zeta-stale", "low_signal"),
    ]

    high_risk = report.rows[0]
    assert high_risk.forecast_valid_at == datetime(2026, 7, 4, 11, 50, tzinfo=UTC)
    assert high_risk.source_observed_at == datetime(2026, 7, 4, 11, 58, tzinfo=UTC)
    assert high_risk.source_age_seconds == Decimal("120.000000")
    assert high_risk.confidence_cap == Decimal("1.000000")
    assert high_risk.capped_confidence == Decimal("0.910000")
    assert high_risk.redacted_source_reference == "nhc-public-advisory-12"
    assert high_risk.reason_codes == (
        "hurricane_rapid_intensification_24h_threshold",
        "hurricane_rapid_intensification_high_confidence",
        "hurricane_rapid_intensification_probability_threshold",
        "hurricane_rapid_intensification_source_fresh",
        "model_consensus",
    )

    stale = report.rows[2]
    assert stale.source_age_seconds == Decimal("3600.000000")
    assert stale.confidence_cap == Decimal("0.500000")
    assert stale.capped_confidence == Decimal("0.500000")
    assert stale.redacted_source_reference.startswith("sha256:")
    assert stale.reason_codes == (
        "hurricane_rapid_intensification_low_signal",
        "hurricane_rapid_intensification_source_stale",
        "official_advisory",
    )

    assert report.reason_codes == (
        "hurricane_rapid_intensification_24h_threshold",
        "hurricane_rapid_intensification_high_confidence",
        "hurricane_rapid_intensification_low_signal",
        "hurricane_rapid_intensification_probability_threshold",
        "hurricane_rapid_intensification_source_fresh",
        "hurricane_rapid_intensification_source_stale",
        "hurricane_rapid_intensification_watch_24h_change",
        "hurricane_rapid_intensification_watch_probability",
        "model_consensus",
        "official_advisory",
    )


def test_empty_digest_and_payload_are_report_only_readonly_decimal_strings() -> None:
    module = api()
    report = digest(())
    payload = (
        module.market_research_weather_hurricane_rapid_intensification_digest_payload(
            report,
        )
    )
    json.dumps(payload, sort_keys=True)

    assert report.input_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.reason_codes == ("hurricane_rapid_intensification_digest_empty",)
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))


def test_digest_is_deterministic_for_input_order_reason_order_and_payload() -> None:
    module = api()
    first = observation(
        "same-b",
        intensification_24h_knots=Decimal("32.000000"),
        rapid_intensification_probability=Decimal("0.620000"),
        upstream_reason_codes=("z_source", "a_source", "z_source"),
    )
    second = observation(
        "same-a",
        intensification_24h_knots=Decimal("36.000000"),
        rapid_intensification_probability=Decimal("0.620000"),
        upstream_reason_codes=("model_consensus",),
    )
    third = observation(
        "same-watch",
        intensification_24h_knots=Decimal("17.000000"),
        rapid_intensification_probability=Decimal("0.300000"),
        forecast_confidence=Decimal("0.700000"),
    )

    report_a = digest((first, second, third))
    report_b = digest((third, first, second))

    assert module.market_research_weather_hurricane_rapid_intensification_digest_payload(
        report_a,
    ) == module.market_research_weather_hurricane_rapid_intensification_digest_payload(
        report_b,
    )
    assert [row.event_id for row in report_a.rows] == [
        "same-a",
        "same-b",
        "same-watch",
    ]
    assert report_a.rows[1].reason_codes == (
        "a_source",
        "hurricane_rapid_intensification_24h_threshold",
        "hurricane_rapid_intensification_high_confidence",
        "hurricane_rapid_intensification_probability_threshold",
        "hurricane_rapid_intensification_source_fresh",
        "z_source",
    )


def test_rejects_invalid_values_naive_datetimes_subclasses_future_rows_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="rapid_intensification_probability"):
        observation(rapid_intensification_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="rapid_intensification_probability"):
        observation(rapid_intensification_probability=_DecimalSubclass("0.700000"))

    with pytest.raises(ValueError, match="forecast_confidence"):
        observation(forecast_confidence=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_source_age_seconds"):
        config(max_source_age_seconds=900)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(source_observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        digest((), generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="source_observed_at"):
        digest((observation(source_observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="forecast_valid_at"):
        digest((observation(forecast_valid_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        digest((observation(readonly=False),))

    with pytest.raises(ValueError, match="redacted_source_reference"):
        replace(
            digest((observation(source_reference="https://x.example/?apikey=value"),)).rows[
                0
            ],
            redacted_source_reference="https://x.example/?apikey=value",
        )

    report = digest((observation(),))
    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.market_research_weather_hurricane_rapid_intensification_digest_payload(
            unsafe_report,
        )

    with pytest.raises(ValueError, match="report"):
        module.market_research_weather_hurricane_rapid_intensification_digest_payload(
            {"bad": "value"},
        )


def test_non_default_thresholds_change_screening_without_mutating_inputs() -> None:
    cfg = config(
        rapid_intensification_24h_threshold_knots=Decimal("40.000000"),
        watch_intensification_24h_threshold_knots=Decimal("10.000000"),
        rapid_intensification_probability_threshold=Decimal("0.800000"),
        watch_probability_threshold=Decimal("0.200000"),
        min_watch_confidence=Decimal("0.500000"),
    )
    value = observation(
        intensification_24h_knots=Decimal("35.000000"),
        rapid_intensification_probability=Decimal("0.750000"),
        forecast_confidence=Decimal("0.550000"),
    )

    report = digest((value,), cfg=cfg)

    assert report.rapid_intensification_count == Decimal("0.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.rows[0].rapid_intensification_status == "rapid_intensification_watch"
    assert report.rows[0].reason_codes == (
        "hurricane_rapid_intensification_source_fresh",
        "hurricane_rapid_intensification_watch_24h_change",
        "hurricane_rapid_intensification_watch_probability",
    )
    assert value.intensification_24h_knots == Decimal("35.000000")

    with pytest.raises(ValueError, match="watch_intensification"):
        config(
            rapid_intensification_24h_threshold_knots=Decimal("20.000000"),
            watch_intensification_24h_threshold_knots=Decimal("25.000000"),
        )

    with pytest.raises(ValueError, match="watch_probability"):
        config(
            rapid_intensification_probability_threshold=Decimal("0.400000"),
            watch_probability_threshold=Decimal("0.500000"),
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    report = digest((observation(),))

    for item in (config(), observation(), report, *report.rows):
        assert is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        report.row_count = Decimal("2.000000")  # type: ignore[misc]

    public_classes = (
        module.WeatherHurricaneRapidIntensificationDigestConfig,
        module.WeatherHurricaneRapidIntensificationObservation,
        module.WeatherHurricaneRapidIntensificationDigestRow,
        module.WeatherHurricaneRapidIntensificationDigestReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        for field in fields(klass):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type or "intensification" in public_type


def test_payload_redacts_sensitive_references_and_rejects_unsafe_public_content() -> None:
    module = api()
    report = digest(
        (
            observation(
                source_reference="https://weather.example/advisory?apikey=secret-123",
            ),
        ),
    )
    payload = (
        module.market_research_weather_hurricane_rapid_intensification_digest_payload(
            report,
        )
    )

    assert payload == (
        module.market_research_weather_hurricane_rapid_intensification_digest_payload(
            report,
        )
    )
    assert payload["rows"][0]["redacted_source_reference"].startswith("sha256:")
    assert "secret-123" not in repr(payload).lower()
    assert "apikey" not in repr(payload).lower()
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
        "auth",
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
        "replace_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    exported = {
        item.strip().strip('"')
        for item in module_path.read_text()
        .split("__all__ = (", 1)[1]
        .split(")", 1)[0]
        .split(",")
        if item.strip()
    }
    assert (
        "build_market_research_weather_hurricane_rapid_intensification_digest"
        in exported
    )
    assert (
        "market_research_weather_hurricane_rapid_intensification_digest_payload"
        in exported
    )
    assert inspect.signature(
        api().build_market_research_weather_hurricane_rapid_intensification_digest,
    ).parameters["config"].kind is inspect.Parameter.KEYWORD_ONLY

from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_weather_hurricane_landfall_digest.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_weather_hurricane_landfall_digest",
    )


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "weather-hurricane-landfall-digest-v1",
        "max_source_age_seconds": Decimal("900.000000"),
        "major_intensity_threshold": Decimal("3.000000"),
        "min_watch_confidence": Decimal("0.600000"),
        "high_confidence_threshold": Decimal("0.800000"),
    }
    values.update(overrides)
    return module.WeatherHurricaneLandfallDigestConfig(**values)


def forecast(
    event_id: str = "al05-2026",
    *,
    basin: str = "atlantic",
    storm_name: str = "iris",
    landfall_region: str = "us-gulf-coast",
    forecast_valid_at: datetime = GENERATED_AT - timedelta(minutes=10),
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    landfall_probability: Decimal = Decimal("0.720000"),
    expected_intensity_category: Decimal = Decimal("3.000000"),
    forecast_confidence: Decimal = Decimal("0.830000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.HurricaneLandfallForecastObservation(
        event_id=event_id,
        basin=basin,
        storm_name=storm_name,
        landfall_region=landfall_region,
        forecast_valid_at=forecast_valid_at,
        source_observed_at=source_observed_at,
        landfall_probability=landfall_probability,
        expected_intensity_category=expected_intensity_category,
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
    return module.build_market_research_weather_hurricane_landfall_digest(
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


def test_builds_landfall_digest_with_decimal_counts_utc_sorting_and_reason_codes() -> None:
    report = digest(
        (
            forecast(
                "zeta-stale",
                source_observed_at=GENERATED_AT - timedelta(seconds=3600),
                landfall_probability=Decimal("0.410000"),
                expected_intensity_category=Decimal("1.000000"),
                forecast_confidence=Decimal("0.520000"),
                upstream_reason_codes=("nhc_outlook",),
            ),
            forecast(
                "alpha-major",
                forecast_valid_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    52,
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
                landfall_probability=Decimal("0.760000"),
                expected_intensity_category=Decimal("4.000000"),
                forecast_confidence=Decimal("0.910000"),
                upstream_reason_codes=("model_consensus",),
            ),
            forecast(
                "beta-watch",
                landfall_probability=Decimal("0.650000"),
                expected_intensity_category=Decimal("2.000000"),
                forecast_confidence=Decimal("0.700000"),
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.input_count == Decimal("3.000000")
    assert report.row_count == Decimal("3.000000")
    assert report.major_landfall_count == Decimal("1.000000")
    assert report.watch_landfall_count == Decimal("1.000000")
    assert report.low_signal_count == Decimal("1.000000")
    assert report.stale_source_count == Decimal("1.000000")
    assert report.max_landfall_probability == Decimal("0.760000")
    assert report.max_expected_intensity_category == Decimal("4.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.event_id, row.landfall_status, row.landfall_probability)
        for row in report.rows
    ] == [
        ("alpha-major", "major_landfall_signal", Decimal("0.760000")),
        ("beta-watch", "landfall_watch", Decimal("0.650000")),
        ("zeta-stale", "low_signal", Decimal("0.410000")),
    ]

    major = report.rows[0]
    assert major.forecast_valid_at == datetime(2026, 7, 4, 11, 52, tzinfo=UTC)
    assert major.source_observed_at == datetime(2026, 7, 4, 11, 58, tzinfo=UTC)
    assert major.source_age_seconds == Decimal("120.000000")
    assert major.confidence_cap == Decimal("1.000000")
    assert major.capped_confidence == Decimal("0.910000")
    assert major.reason_codes == (
        "hurricane_landfall_high_confidence",
        "hurricane_landfall_major_intensity_signal",
        "hurricane_landfall_source_fresh",
        "hurricane_landfall_watch_probability",
        "model_consensus",
    )

    stale = report.rows[2]
    assert stale.source_age_seconds == Decimal("3600.000000")
    assert stale.confidence_cap == Decimal("0.500000")
    assert stale.capped_confidence == Decimal("0.500000")
    assert stale.reason_codes == (
        "hurricane_landfall_low_signal",
        "hurricane_landfall_source_stale",
        "nhc_outlook",
    )

    assert report.reason_codes == (
        "hurricane_landfall_high_confidence",
        "hurricane_landfall_low_signal",
        "hurricane_landfall_major_intensity_signal",
        "hurricane_landfall_source_fresh",
        "hurricane_landfall_source_stale",
        "hurricane_landfall_watch_probability",
        "model_consensus",
        "nhc_outlook",
    )


def test_empty_digest_and_payload_are_report_only_readonly_decimal_strings() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_weather_hurricane_landfall_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert report.input_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.reason_codes == ("hurricane_landfall_digest_empty",)
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)


def test_rejects_float_public_inputs_naive_datetimes_subclasses_future_rows_and_bad_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="landfall_probability"):
        forecast(landfall_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="landfall_probability"):
        forecast(landfall_probability=_DecimalSubclass("0.700000"))

    with pytest.raises(ValueError, match="forecast_confidence"):
        forecast(forecast_confidence=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_source_age_seconds"):
        config(max_source_age_seconds=900)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        forecast(source_observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        forecast(source_observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="source_observed_at must not be after generated_at"):
        digest((forecast(source_observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="forecast_valid_at must not be after generated_at"):
        digest((forecast(forecast_valid_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="paper_only"):
        forecast(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    report = digest((forecast(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.WeatherHurricaneLandfallDigestConfig,
        module.HurricaneLandfallForecastObservation,
        module.HurricaneLandfallDigestRow,
        module.WeatherHurricaneLandfallDigestReport,
    )
    for type_ in classes:
        assert is_dataclass(type_)
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type


def test_module_scope_is_pure_without_io_or_mutation_surface_terms() -> None:
    source = inspect.getsource(api()).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "open(",
        "path(",
        "connect(",
        "cursor(",
        "execute(",
        "web3",
        "wallet",
        "private_key",
        "place_order",
        "cancel_order",
        "replace_order",
        "auth",
        "secret",
        "token",
        "live trading",
        "trade",
        "position",
        "recommend",
    ):
        assert forbidden not in source

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}

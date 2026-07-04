from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_weather_temperature_extreme_digest import (
    DEFAULT_MARKET_RESEARCH_WEATHER_TEMPERATURE_EXTREME_DIGEST_CONFIG_VERSION,
    MarketResearchWeatherTemperatureExtremeDigestConfig,
    MarketResearchWeatherTemperatureExtremeDigestInputRow,
    MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount,
    MarketResearchWeatherTemperatureExtremeDigestReport,
    MarketResearchWeatherTemperatureExtremeDigestRow,
    build_market_research_weather_temperature_extreme_digest,
    market_research_weather_temperature_extreme_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchWeatherTemperatureExtremeDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_WEATHER_TEMPERATURE_EXTREME_DIGEST_CONFIG_VERSION
        ),
        "fresh_observation_max_age_seconds": d("3600.000000"),
        "min_source_count": d("2.000000"),
        "material_temperature_deviation_threshold_celsius": d("5.000000"),
        "high_forecast_confidence_threshold": d("0.750000"),
        "max_station_disagreement_score": d("0.600000"),
        "max_acknowledgement_lag_seconds": d("900.000000"),
    }
    values.update(overrides)
    return MarketResearchWeatherTemperatureExtremeDigestConfig(**values)


def input_row(
    research_key: str = "weather.temperature.ready",
    *,
    condition_id: str = "condition_chicago_high",
    weather_region_key: str = "us.il.chicago",
    public_temperature_reference: str = "noaa-public-temperature-note",
    observed_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    baseline_temperature_celsius: Decimal = d("30.000000"),
    observed_temperature_celsius: Decimal = d("32.000000"),
    forecast_confidence_score: Decimal = d("0.500000"),
    station_disagreement_score: Decimal = d("0.200000"),
    source_config_version: str = "temperature-extreme-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchWeatherTemperatureExtremeDigestInputRow:
    return MarketResearchWeatherTemperatureExtremeDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        weather_region_key=weather_region_key,
        public_temperature_reference=public_temperature_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=5)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        baseline_temperature_celsius=baseline_temperature_celsius,
        observed_temperature_celsius=observed_temperature_celsius,
        forecast_confidence_score=forecast_confidence_score,
        station_disagreement_score=station_disagreement_score,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchWeatherTemperatureExtremeDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchWeatherTemperatureExtremeDigestReport:
    return build_market_research_weather_temperature_extreme_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_temperature_extreme_digest_reduces_rows_redacts_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "weather.phoenix.watch",
                condition_id="condition_phoenix_record_high",
                weather_region_key="us.az.phoenix",
                public_temperature_reference=(
                    "https://vendor.example/phoenix?token=secret-123"
                ),
                observed_at=GENERATED_AT - timedelta(minutes=50),
                acknowledged_at=GENERATED_AT - timedelta(minutes=25),
                source_count=d("1.000000"),
                baseline_temperature_celsius=d("39.000000"),
                observed_temperature_celsius=d("46.000000"),
                forecast_confidence_score=d("0.920000"),
                station_disagreement_score=d("0.720000"),
            ),
            input_row(
                "weather.chicago.ready",
                condition_id="condition_chicago_high",
                weather_region_key="us.il.chicago",
                public_temperature_reference="noaa-public-temperature-note",
                observed_at=GENERATED_AT - timedelta(minutes=20),
                acknowledged_at=GENERATED_AT - timedelta(minutes=5),
                source_count=d("3.000000"),
                baseline_temperature_celsius=d("30.000000"),
                observed_temperature_celsius=d("32.000000"),
                forecast_confidence_score=d("0.500000"),
                station_disagreement_score=d("0.200000"),
            ),
            input_row(
                "weather.boston.blocked",
                condition_id="condition_boston_record_low",
                weather_region_key="us.ma.boston",
                public_temperature_reference="wallet://private/boston-feed",
                observed_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=None,
                source_count=d("2.000000"),
                baseline_temperature_celsius=d("-2.000000"),
                observed_temperature_celsius=d("-9.000000"),
                forecast_confidence_score=d("0.700000"),
                station_disagreement_score=d("0.300000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchWeatherTemperatureExtremeDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_WEATHER_TEMPERATURE_EXTREME_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_weather_temperature_extreme_digest"
    )
    assert summary.temperature_extreme_count == d("3.000000")
    assert summary.ready_extreme_count == d("1.000000")
    assert summary.watch_extreme_count == d("1.000000")
    assert summary.blocked_extreme_count == d("1.000000")
    assert summary.material_temperature_deviation_count == d("2.000000")
    assert summary.stale_observation_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.high_forecast_confidence_count == d("1.000000")
    assert summary.station_disagreement_count == d("1.000000")
    assert summary.average_abs_temperature_deviation_celsius == d("5.333333")
    assert summary.max_observation_age_seconds == d("14400.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.weather_region_key for row in summary.rows) == (
        "us.ma.boston",
        "us.az.phoenix",
        "us.il.chicago",
    )

    blocked = summary.rows[0]
    assert blocked.extreme_status == "blocked"
    assert blocked.observation_age_seconds == d("14400.000000")
    assert blocked.acknowledgement_lag_seconds is None
    assert blocked.temperature_deviation_celsius == d("-7.000000")
    assert blocked.absolute_temperature_deviation_celsius == d("7.000000")
    assert blocked.redacted_public_temperature_reference == "sha256:cc7c100749a4"
    assert blocked.reason_codes == (
        "market_research_weather_temperature_extreme_digest_material_temperature_deviation",
        "market_research_weather_temperature_extreme_digest_missing_acknowledgement",
        "market_research_weather_temperature_extreme_digest_stale_observation",
    )

    watched = summary.rows[1]
    assert watched.extreme_status == "watch"
    assert watched.observation_age_seconds == d("3000.000000")
    assert watched.acknowledgement_lag_seconds == d("1500.000000")
    assert watched.temperature_deviation_celsius == d("7.000000")
    assert watched.absolute_temperature_deviation_celsius == d("7.000000")
    assert watched.redacted_public_temperature_reference == "sha256:06dd03307b77"
    assert watched.reason_codes == (
        "market_research_weather_temperature_extreme_digest_material_temperature_deviation",
        "market_research_weather_temperature_extreme_digest_high_forecast_confidence",
        "market_research_weather_temperature_extreme_digest_station_disagreement",
        "market_research_weather_temperature_extreme_digest_slow_acknowledgement",
        "market_research_weather_temperature_extreme_digest_thin_sources",
    )

    ready = summary.rows[2]
    assert ready.extreme_status == "ready"
    assert ready.observation_age_seconds == d("1200.000000")
    assert ready.acknowledgement_lag_seconds == d("900.000000")
    assert ready.temperature_deviation_celsius == d("2.000000")
    assert ready.absolute_temperature_deviation_celsius == d("2.000000")
    assert ready.redacted_public_temperature_reference == "noaa-public-temperature-note"
    assert ready.reason_codes == (
        "market_research_weather_temperature_extreme_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
            reason_code=(
                "market_research_weather_temperature_extreme_digest_"
                "material_temperature_deviation"
            ),
            count=d("2.000000"),
            extreme_ratio=d("0.666667"),
        ),
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
            reason_code=(
                "market_research_weather_temperature_extreme_digest_"
                "high_forecast_confidence"
            ),
            count=d("1.000000"),
            extreme_ratio=d("0.333333"),
        ),
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
            reason_code=(
                "market_research_weather_temperature_extreme_digest_"
                "station_disagreement"
            ),
            count=d("1.000000"),
            extreme_ratio=d("0.333333"),
        ),
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
            reason_code=(
                "market_research_weather_temperature_extreme_digest_"
                "missing_acknowledgement"
            ),
            count=d("1.000000"),
            extreme_ratio=d("0.333333"),
        ),
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
            reason_code=(
                "market_research_weather_temperature_extreme_digest_"
                "slow_acknowledgement"
            ),
            count=d("1.000000"),
            extreme_ratio=d("0.333333"),
        ),
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
            reason_code=(
                "market_research_weather_temperature_extreme_digest_stale_observation"
            ),
            count=d("1.000000"),
            extreme_ratio=d("0.333333"),
        ),
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
            reason_code=(
                "market_research_weather_temperature_extreme_digest_thin_sources"
            ),
            count=d("1.000000"),
            extreme_ratio=d("0.333333"),
        ),
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
            reason_code="market_research_weather_temperature_extreme_digest_ready",
            count=d("1.000000"),
            extreme_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.source_config_versions == (
        ("us.az.phoenix", "temperature-extreme-source-v0"),
        ("us.il.chicago", "temperature-extreme-source-v0"),
        ("us.ma.boston", "temperature-extreme-source-v0"),
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "wallet://",
        "boston-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
        "order",
    ):
        assert token not in public


def test_empty_temperature_extreme_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_weather_temperature_extreme_digest"
    )
    assert summary.temperature_extreme_count == ZERO
    assert summary.ready_extreme_count == ZERO
    assert summary.watch_extreme_count == ZERO
    assert summary.blocked_extreme_count == ZERO
    assert summary.average_abs_temperature_deviation_celsius == ZERO
    assert summary.max_observation_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.source_config_versions == ()
    assert summary.reason_code_counts == (
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
            reason_code="market_research_weather_temperature_extreme_digest_no_inputs",
            count=d("1.000000"),
            extreme_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_weather_temperature_extreme_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_temperature_extreme_payload_uses_decimal_strings_and_redacted_refs() -> None:
    summary = report((input_row(),))
    payload = market_research_weather_temperature_extreme_digest_payload(summary)

    assert payload["temperature_extreme_count"] == "1.000000"
    assert payload["average_abs_temperature_deviation_celsius"] == "2.000000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["temperature_deviation_celsius"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_temperature_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_temperature_extreme_validates_frozen_contracts_decimals_and_flags() -> None:
    assert MarketResearchWeatherTemperatureExtremeDigestConfig.__dataclass_params__.frozen
    assert MarketResearchWeatherTemperatureExtremeDigestInputRow.__dataclass_params__.frozen
    assert MarketResearchWeatherTemperatureExtremeDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert MarketResearchWeatherTemperatureExtremeDigestReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        input_row().source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("temperature-extreme-v0"))
    with pytest.raises(ValueError, match="fresh_observation_max_age_seconds"):
        config(fresh_observation_max_age_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="material_temperature_deviation_threshold"):
        config(material_temperature_deviation_threshold_celsius=5.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_key"):
        input_row(_StringSubclass("weather.bad"))
    with pytest.raises(ValueError, match="weather_region_key"):
        input_row(weather_region_key="US AZ Phoenix")
    with pytest.raises(ValueError, match="public_temperature_reference"):
        input_row(public_temperature_reference=" ")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 3, 17, 0))
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(acknowledged_at=_DatetimeSubclass(2026, 7, 3, 17, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="baseline_temperature_celsius"):
        input_row(baseline_temperature_celsius=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_temperature_celsius"):
        input_row(observed_temperature_celsius=_DecimalSubclass("32.000000"))
    with pytest.raises(ValueError, match="forecast_confidence_score"):
        input_row(forecast_confidence_score=d("1.000001"))
    with pytest.raises(ValueError, match="station_disagreement_score"):
        input_row(station_disagreement_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_weather_temperature_extreme_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_weather_temperature_extreme_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 3, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_temperature_extreme_report_and_row_consistency_rejects_manual_drift() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_weather_temperature_extreme_digest_ready",
                "market_research_weather_temperature_extreme_digest_"
                "material_temperature_deviation",
            ),
        )
    with pytest.raises(ValueError, match="extreme_status"):
        replace(ready, extreme_status="blocked")
    with pytest.raises(ValueError, match="temperature_deviation_celsius"):
        replace(ready, temperature_deviation_celsius=d("9.000000"))
    with pytest.raises(ValueError, match="redacted_public_temperature_reference"):
        replace(ready, redacted_public_temperature_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="ready_extreme_count"):
        replace(report((input_row(),)), ready_extreme_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        replace(
            report(
                (
                    input_row(
                        "weather.z",
                        weather_region_key="z.region",
                    ),
                    input_row(),
                ),
            ),
            rows=tuple(
                reversed(
                    report(
                        (
                            input_row(
                                "weather.z",
                                weather_region_key="z.region",
                            ),
                            input_row(),
                        ),
                    ).rows,
                ),
            ),
        )


def test_public_numeric_count_ratio_second_score_and_temperature_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_public_numbers(summary)
    assert_decimal_public_numbers(summary.rows[0])
    assert_decimal_public_numbers(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_live_surfaces_or_forbidden_source_terms() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/"
        "market_research_weather_temperature_extreme_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "open",
        "read",
        "write",
        "send",
        "submit",
        "cancel",
        "trade",
        "order",
        "wallet",
        "auth",
        "sign",
        "session",
        "commit",
        "replace",
        "exchange",
    )
    forbidden_source_terms = (
        "wallet",
        "auth",
        "private_key",
        "secret",
        "token",
        "submit",
        "cancel",
        "exchange",
        "live trading",
    )

    assert not any(
        fragment in module_name
        for module_name in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert not any(term in lowered for term in forbidden_source_terms)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(child for item in value.values() for child in walk_values(item))
    if isinstance(value, (list, tuple)):
        return tuple(child for item in value for child in walk_values(item))
    return (value,)


def assert_decimal_public_numbers(obj: object) -> None:
    for field in fields(obj):
        value = getattr(obj, field.name)
        if _is_public_numeric_field(field.name):
            assert value is None or type(value) is Decimal


def _is_public_numeric_field(name: str) -> bool:
    if "reference" in name or name in ("rows", "reason_code_counts"):
        return False
    fragments = (
        "count",
        "ratio",
        "seconds",
        "temperature",
        "score",
        "threshold",
    )
    return any(fragment in name for fragment in fragments)

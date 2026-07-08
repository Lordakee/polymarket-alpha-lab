from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_weather_signal_memory_quality_report.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_domain_weather_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory_input(**overrides: object):
    module = api()
    values = {
        "weather_signal_bucket": "tropical_cyclone_handoff",
        "memory_scope_bucket": "forecast_alert_station_resolution",
        "forecast_memory_age_seconds": d("3600.000000"),
        "alert_memory_age_seconds": d("3600.000000"),
        "station_memory_age_seconds": d("3600.000000"),
        "resolution_rule_memory_age_seconds": d("3600.000000"),
        "forecast_conflict_count": d("0.000000"),
        "alert_conflict_count": d("0.000000"),
        "station_conflict_count": d("0.000000"),
        "resolution_rule_conflict_count": d("0.000000"),
        "forecast_missing_count": d("0.000000"),
        "alert_missing_count": d("0.000000"),
        "station_missing_count": d("0.000000"),
        "resolution_rule_missing_count": d("0.000000"),
        "observed_at": GENERATED_AT - timedelta(minutes=30),
    }
    values.update(overrides)
    return module.ResearchDomainWeatherSignalMemoryQualityInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_domain_weather_signal_memory_quality_report(
        items,
        config=cfg
        if cfg is not None
        else module.ResearchDomainWeatherSignalMemoryQualityConfig(),
        generated_at=generated_at,
    )


def test_weather_signal_memory_quality_identifies_stale_conflicting_missing_inputs() -> None:
    report = build_report(
        memory_input(),
        memory_input(
            weather_signal_bucket="convective_alert_watch",
            memory_scope_bucket="forecast_alert_station_resolution",
            forecast_memory_age_seconds=d("30000.000000"),
            alert_memory_age_seconds=d("30000.000000"),
            station_memory_age_seconds=d("30000.000000"),
            resolution_rule_memory_age_seconds=d("30000.000000"),
            forecast_conflict_count=d("1.000000"),
            alert_conflict_count=d("1.000000"),
            station_conflict_count=d("1.000000"),
            resolution_rule_conflict_count=d("1.000000"),
            forecast_missing_count=d("1.000000"),
            alert_missing_count=d("1.000000"),
            station_missing_count=d("1.000000"),
            resolution_rule_missing_count=d("1.000000"),
            observed_at=datetime(2026, 7, 8, 5, 45, tzinfo=timezone(timedelta(hours=-6))),
        ),
        memory_input(
            weather_signal_bucket="river_flood_block",
            memory_scope_bucket="forecast_alert_station_resolution",
            forecast_memory_age_seconds=d("100000.000000"),
            alert_memory_age_seconds=d("100000.000000"),
            station_memory_age_seconds=d("100000.000000"),
            resolution_rule_memory_age_seconds=d("100000.000000"),
            forecast_conflict_count=d("2.000000"),
            alert_conflict_count=d("2.000000"),
            station_conflict_count=d("2.000000"),
            resolution_rule_conflict_count=d("2.000000"),
            forecast_missing_count=d("2.000000"),
            alert_missing_count=d("2.000000"),
            station_missing_count=d("2.000000"),
            resolution_rule_missing_count=d("2.000000"),
        ),
    )

    assert type(report) is api().ResearchDomainWeatherSignalMemoryQualityReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.report_status == "block"
    assert report.staleness_status == "block"
    assert report.conflict_status == "block"
    assert report.completeness_status == "block"
    assert report.forecast_handoff_status == "block"
    assert report.memory_input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.stale_input_count == d("2.000000")
    assert report.conflicting_input_count == d("2.000000")
    assert report.missing_input_count == d("2.000000")
    assert report.total_conflict_count == d("12.000000")
    assert report.total_missing_count == d("12.000000")
    assert report.max_memory_age_seconds == d("100000.000000")
    assert report.average_memory_quality_score == d("0.512346")
    assert report.reason_codes == (
        "weather_signal_memory_quality_report_block",
        "forecast_memory_stale_block",
        "alert_memory_stale_block",
        "station_memory_stale_block",
        "resolution_rule_memory_stale_block",
        "forecast_memory_conflict_block",
        "alert_memory_conflict_block",
        "station_memory_conflict_block",
        "resolution_rule_memory_conflict_block",
        "forecast_memory_missing_block",
        "alert_memory_missing_block",
        "station_memory_missing_block",
        "resolution_rule_memory_missing_block",
        "forecast_memory_stale_watch",
        "alert_memory_stale_watch",
        "station_memory_stale_watch",
        "resolution_rule_memory_stale_watch",
        "forecast_memory_conflict_watch",
        "alert_memory_conflict_watch",
        "station_memory_conflict_watch",
        "resolution_rule_memory_conflict_watch",
        "forecast_memory_missing_watch",
        "alert_memory_missing_watch",
        "station_memory_missing_watch",
        "resolution_rule_memory_missing_watch",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.weather_signal_bucket == "river_flood_block"
    assert blocked.memory_quality_score == d("0.000000")
    assert blocked.max_memory_age_seconds == d("100000.000000")
    assert blocked.total_conflict_count == d("8.000000")
    assert blocked.total_missing_count == d("8.000000")
    assert blocked.reason_codes == (
        "forecast_memory_stale_block",
        "alert_memory_stale_block",
        "station_memory_stale_block",
        "resolution_rule_memory_stale_block",
        "forecast_memory_conflict_block",
        "alert_memory_conflict_block",
        "station_memory_conflict_block",
        "resolution_rule_memory_conflict_block",
        "forecast_memory_missing_block",
        "alert_memory_missing_block",
        "station_memory_missing_block",
        "resolution_rule_memory_missing_block",
    )
    assert watched.status == "watch"
    assert watched.observed_at == datetime(2026, 7, 8, 11, 45, tzinfo=UTC)
    assert watched.memory_quality_score == d("0.550926")
    assert watched.reason_codes == (
        "forecast_memory_stale_watch",
        "alert_memory_stale_watch",
        "station_memory_stale_watch",
        "resolution_rule_memory_stale_watch",
        "forecast_memory_conflict_watch",
        "alert_memory_conflict_watch",
        "station_memory_conflict_watch",
        "resolution_rule_memory_conflict_watch",
        "forecast_memory_missing_watch",
        "alert_memory_missing_watch",
        "station_memory_missing_watch",
        "resolution_rule_memory_missing_watch",
    )
    assert passed.status == "pass"
    assert passed.memory_quality_score == d("0.986111")
    assert passed.reason_codes == ("weather_signal_memory_quality_clear",)


def test_empty_payload_is_deterministic_public_safe_and_digest_validated() -> None:
    module = api()
    report = build_report()
    payload = module.research_domain_weather_signal_memory_quality_report_payload(report)
    encoded = json.dumps(
        {key: value for key, value in payload.items() if key != "derived_validation_digest"},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert report.report_status == "block"
    assert report.forecast_handoff_status == "block"
    assert report.memory_input_count == d("0.000000")
    assert report.average_memory_quality_score == d("0.000000")
    assert report.reason_codes == ("weather_signal_memory_quality_no_inputs",)
    assert report.rows == ()
    assert payload == report.payload
    assert payload["memory_input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == sha256(encoded.encode("utf-8")).hexdigest()
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert (
        module.research_domain_weather_signal_memory_quality_report_digest(report)
        == report.derived_validation_digest
    )
    assert_no_numeric_scalars(payload)
    assert_no_private_public_surface(payload)

    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_weather_signal_memory_quality_report_payload(tampered)

    unsafe_key = dict(payload)
    unsafe_key["market_id"] = "abc"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_domain_weather_signal_memory_quality_report_payload(unsafe_key)

    unsafe_value = dict(payload)
    unsafe_value["reason_codes"] = ["wallet"]
    with pytest.raises(ValueError, match="unsafe"):
        module.research_domain_weather_signal_memory_quality_report_payload(unsafe_value)


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    report = build_report(memory_input())

    assert module.WEATHER_SIGNAL_MEMORY_QUALITY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_WEATHER_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
        "WEATHER_SIGNAL_MEMORY_QUALITY_STATUSES",
        "WEATHER_SIGNAL_MEMORY_QUALITY_REASON_CODES",
        "ResearchDomainWeatherSignalMemoryQualityConfig",
        "ResearchDomainWeatherSignalMemoryQualityInput",
        "ResearchDomainWeatherSignalMemoryQualityReasonCodeCount",
        "ResearchDomainWeatherSignalMemoryQualityReport",
        "ResearchDomainWeatherSignalMemoryQualityRow",
        "build_research_domain_weather_signal_memory_quality_report",
        "research_domain_weather_signal_memory_quality_report_digest",
        "research_domain_weather_signal_memory_quality_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="forecast_memory_age_seconds must be a Decimal"):
        memory_input(forecast_memory_age_seconds=3600)
    with pytest.raises(ValueError, match="alert_conflict_count must be a whole Decimal"):
        memory_input(alert_conflict_count=d("1.500000"))
    with pytest.raises(ValueError, match="station_missing_count must be a Decimal"):
        memory_input(station_missing_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(observed_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="weather_signal_bucket"):
        memory_input(weather_signal_bucket=_StringSubclass("storm_cluster"))
    with pytest.raises(ValueError, match="public-safe"):
        memory_input(weather_signal_bucket="market_id")
    with pytest.raises(ValueError, match="generated_at"):
        build_report(memory_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.ResearchDomainWeatherSignalMemoryQualityConfig(), paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    assert_public_numerics_are_decimal(report)
    assert_no_private_public_surface(report.payload)


def test_module_scope_has_no_external_or_action_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "wallet",
        "account",
        "private_key",
        "api_key",
        "secret",
        "clob",
        "submit",
        "cancel",
        "signing",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "recommend",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(tree)
    )
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }


def assert_no_numeric_scalars(value: Any) -> None:
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"unexpected numeric payload scalar: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_scalars(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_scalars(item)


def assert_public_numerics_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal: {value!r}")
    if type(value) in (str, datetime):
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numerics_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numerics_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numerics_are_decimal(item)


def assert_no_private_public_surface(value: Any) -> None:
    forbidden = (
        "candidate_id",
        "candidate_slug",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "url",
        "://",
        "www.",
        "source_text",
        "raw_text",
        "dsn",
        "table_name",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "network",
        "recommendation",
        "sizing",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(term in lowered_key for term in forbidden), key
            assert_no_private_public_surface(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_private_public_surface(item)
    elif type(value) is str:
        lowered_value = value.lower()
        assert not any(term in lowered_value for term in forbidden), value

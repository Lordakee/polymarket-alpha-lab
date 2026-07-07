from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
EXPECTED_EXPORTS = (
    "ForecastConfidenceDriftForecast",
    "ForecastConfidenceDriftMonitorConfig",
    "ForecastConfidenceDriftMonitorReport",
    "ForecastConfidenceDriftRow",
    "build_forecast_confidence_drift_monitor_report",
    "forecast_confidence_drift_monitor_payload",
)
FORBIDDEN_IMPORT_PREFIXES = {
    "argparse",
    "os",
    "pathlib",
    "psycopg",
    "sqlite3",
    "sqlalchemy",
    "redis",
    "pymongo",
    "web3",
    "eth_account",
    "py_clob_client",
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "urllib",
    "http.client",
    "shelve",
    "pickle",
}


def _module() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.forecast_confidence_drift_monitor",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _forecast(
    index: int,
    *,
    condition_id: str = "condition-alpha",
    team_id: str = "crypto_btc",
    source_id: str = "source-a",
    confidence: Decimal = d("0.700000"),
    generated_at: datetime | None = None,
) -> Any:
    module = _module()
    return module.ForecastConfidenceDriftForecast(
        forecast_id=f"forecast-{index}",
        condition_id=condition_id,
        team_id=team_id,
        source_id=source_id,
        confidence=confidence,
        generated_at=generated_at or GENERATED_AT + timedelta(minutes=index),
    )


def _bypassed_row(row: object, **overrides: Any) -> object:
    malformed = object.__new__(type(row))
    for key, value in row.__dict__.items():
        object.__setattr__(malformed, key, value)
    for key, value in overrides.items():
        object.__setattr__(malformed, key, value)
    return malformed


def _assert_no_public_int_or_float_values(value: object) -> None:
    if type(value) in (float, int):
        pytest.fail("forecast confidence drift monitor must expose Decimal-only numbers")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_no_public_int_or_float_values(getattr(value, field.name))
    elif isinstance(value, dict):
        for key, item in value.items():
            _assert_no_public_int_or_float_values(key)
            _assert_no_public_int_or_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_public_int_or_float_values(item)


def _assert_public_payload_values(value: object) -> None:
    if isinstance(value, Decimal):
        pytest.fail("public payload must expose Decimal values as strings")
    if isinstance(value, datetime):
        pytest.fail("public payload must expose datetimes as strings")
    if type(value) in (float, int):
        pytest.fail("public payload must not expose numeric primitives")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            _assert_public_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            _assert_public_payload_values(item)
    elif isinstance(value, tuple):
        pytest.fail("public payload must expose arrays as lists")


def _is_sha256_hex(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def test_public_exports_are_exact_and_dataclasses_are_frozen() -> None:
    module = _module()

    assert module.__all__ == EXPECTED_EXPORTS

    config = module.ForecastConfidenceDriftMonitorConfig()
    forecast = _forecast(1, confidence=d("0.750000"))
    row = module.ForecastConfidenceDriftRow(
        condition_id="condition-alpha",
        forecast_count=d("2"),
        baseline_count=d("1"),
        latest_count=d("1"),
        baseline_mean_confidence=d("0.750000"),
        latest_mean_confidence=d("0.500000"),
        confidence_delta=d("-0.250000"),
        absolute_confidence_delta=d("0.250000"),
        status="confidence_drift_watch",
        reason_codes=("confidence_drift_detected",),
    )
    report = module.ForecastConfidenceDriftMonitorReport(
        generated_at=GENERATED_AT,
        config_version=config.config_version,
        forecast_count=d("2"),
        row_count=d("1"),
        watch_count=d("1"),
        block_count=d("0"),
        max_absolute_confidence_delta=d("0.250000"),
        status="confidence_drift_watch",
        reason_codes=("confidence_drift_detected",),
        rows=(row,),
    )

    assert config.paper_only is True
    assert forecast.report_only is True
    assert row.readonly is True
    assert report.paper_only is True
    assert _is_sha256_hex(row.derived_validation_digest)
    assert _is_sha256_hex(report.derived_validation_digest)
    _assert_no_public_int_or_float_values(report)

    with pytest.raises(FrozenInstanceError):
        config.config_version = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        forecast.confidence = d("0")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.status = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.row_count = d("0")  # type: ignore[misc]


def test_build_report_detects_confidence_drift_without_live_surfaces() -> None:
    module = _module()

    report = module.build_forecast_confidence_drift_monitor_report(
        (
            _forecast(
                5,
                condition_id="condition-beta",
                team_id="crypto_eth",
                source_id="source-c",
                confidence=d("0.650000"),
                generated_at=GENERATED_AT - timedelta(minutes=5),
            ),
            _forecast(1, confidence=d("0.800000"), generated_at=GENERATED_AT - timedelta(minutes=40)),
            _forecast(2, confidence=d("0.700000"), generated_at=GENERATED_AT - timedelta(minutes=30)),
            _forecast(3, confidence=d("0.400000"), generated_at=GENERATED_AT - timedelta(minutes=20)),
            _forecast(4, confidence=d("0.300000"), generated_at=GENERATED_AT - timedelta(minutes=10)),
            _forecast(
                6,
                condition_id="condition-beta",
                team_id="crypto_eth",
                source_id="source-d",
                confidence=d("0.640000"),
                generated_at=GENERATED_AT - timedelta(minutes=1),
            ),
        ),
        config=module.ForecastConfidenceDriftMonitorConfig(
            config_version="forecast-confidence-drift-monitor-test-v0",
            min_forecast_count=d("4"),
            min_baseline_count=d("2"),
            min_latest_count=d("2"),
            drift_watch_threshold=d("0.100000"),
            drift_block_threshold=d("0.500000"),
        ),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is module.ForecastConfidenceDriftMonitorReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "forecast-confidence-drift-monitor-test-v0"
    assert report.forecast_count == d("6")
    assert report.row_count == d("2")
    assert report.watch_count == d("1")
    assert report.block_count == d("0")
    assert report.max_absolute_confidence_delta == d("0.400000")
    assert report.status == "confidence_drift_watch"
    assert report.reason_codes == ("confidence_drift_detected",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    alpha, beta = report.rows
    assert alpha.condition_id == "condition-alpha"
    assert alpha.forecast_count == d("4")
    assert alpha.baseline_count == d("2")
    assert alpha.latest_count == d("2")
    assert alpha.baseline_mean_confidence == d("0.750000")
    assert alpha.latest_mean_confidence == d("0.350000")
    assert alpha.confidence_delta == d("-0.400000")
    assert alpha.absolute_confidence_delta == d("0.400000")
    assert alpha.status == "confidence_drift_watch"
    assert alpha.reason_codes == ("confidence_drift_detected",)

    assert beta.condition_id == "condition-beta"
    assert beta.forecast_count == d("2")
    assert beta.baseline_mean_confidence is None
    assert beta.status == "insufficient_forecast_history"
    assert beta.reason_codes == ("insufficient_forecast_history",)
    _assert_no_public_int_or_float_values(report)

    exposed_field_names = {
        field.name
        for dataclass_type in (
            module.ForecastConfidenceDriftForecast,
            module.ForecastConfidenceDriftRow,
            module.ForecastConfidenceDriftMonitorReport,
        )
        for field in fields(dataclass_type)
    }
    assert "market_slug" not in exposed_field_names
    assert "question" not in exposed_field_names
    assert "wallet" not in exposed_field_names
    assert "order" not in exposed_field_names


def test_empty_report_is_readonly_and_contains_no_synthetic_drift_metrics() -> None:
    module = _module()

    report = module.build_forecast_confidence_drift_monitor_report(
        (),
        config=module.ForecastConfidenceDriftMonitorConfig(
            config_version="forecast-confidence-drift-monitor-test-v0",
        ),
        generated_at=GENERATED_AT,
    )

    assert report.forecast_count == d("0")
    assert report.row_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.max_absolute_confidence_delta is None
    assert report.status == "empty_forecast_set"
    assert report.reason_codes == ("no_forecasts",)
    assert report.rows == ()


def test_dataclasses_validate_decimal_only_fields_and_hard_flags() -> None:
    module = _module()

    with pytest.raises(ValueError, match="min_forecast_count"):
        module.ForecastConfidenceDriftMonitorConfig(min_forecast_count=4)
    with pytest.raises(ValueError, match="drift_watch_threshold"):
        module.ForecastConfidenceDriftMonitorConfig(drift_watch_threshold=0.1)
    with pytest.raises(ValueError, match="paper_only"):
        module.ForecastConfidenceDriftMonitorConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        module.ForecastConfidenceDriftMonitorConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.ForecastConfidenceDriftMonitorConfig(readonly=False)
    with pytest.raises(ValueError, match="confidence"):
        _forecast(1, confidence=d("1.000001"))
    with pytest.raises(ValueError, match="confidence"):
        module.ForecastConfidenceDriftForecast(
            forecast_id="forecast-1",
            condition_id="condition-alpha",
            team_id="crypto_btc",
            source_id="source-a",
            confidence=0.25,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="forecast_count"):
        module.ForecastConfidenceDriftRow(
            condition_id="condition-alpha",
            forecast_count=d("0"),
            baseline_count=d("0"),
            latest_count=d("0"),
            baseline_mean_confidence=None,
            latest_mean_confidence=None,
            confidence_delta=None,
            absolute_confidence_delta=None,
            status="insufficient_forecast_history",
            reason_codes=("insufficient_forecast_history",),
        )


def test_build_report_rejects_bad_inputs_and_non_paper_forecasts() -> None:
    module = _module()
    config = module.ForecastConfidenceDriftMonitorConfig()
    forecast = _forecast(1)

    with pytest.raises(ValueError, match="forecasts"):
        module.build_forecast_confidence_drift_monitor_report(
            "not-forecasts",
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="ForecastConfidenceDriftForecast"):
        module.build_forecast_confidence_drift_monitor_report(
            [object()],
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.build_forecast_confidence_drift_monitor_report(
            [_bypassed_row(forecast, paper_only=False)],
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_forecast_confidence_drift_monitor_report(
            [],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_forecast_confidence_drift_monitor_report(
            [],
            config=config,
            generated_at=None,
        )


def test_public_payload_serializes_decimal_strings_and_validates_digest() -> None:
    module = _module()
    report = module.build_forecast_confidence_drift_monitor_report(
        (
            _forecast(1, confidence=d("0.800000"), generated_at=GENERATED_AT - timedelta(minutes=40)),
            _forecast(2, confidence=d("0.700000"), generated_at=GENERATED_AT - timedelta(minutes=30)),
            _forecast(3, confidence=d("0.400000"), generated_at=GENERATED_AT - timedelta(minutes=20)),
            _forecast(4, confidence=d("0.300000"), generated_at=GENERATED_AT - timedelta(minutes=10)),
        ),
        config=module.ForecastConfidenceDriftMonitorConfig(
            config_version="forecast-confidence-drift-monitor-test-v0",
            min_forecast_count=d("4"),
            min_baseline_count=d("2"),
            min_latest_count=d("2"),
            drift_watch_threshold=d("0.100000"),
            drift_block_threshold=d("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )

    payload = module.forecast_confidence_drift_monitor_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["forecast_count"] == "4"
    assert payload["row_count"] == "1"
    assert payload["watch_count"] == "1"
    assert payload["block_count"] == "0"
    assert payload["max_absolute_confidence_delta"] == "0.400000"
    assert _is_sha256_hex(payload["derived_validation_digest"])
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["forecast_count"] == "4"
    assert payload["rows"][0]["confidence_delta"] == "-0.400000"
    assert _is_sha256_hex(payload["rows"][0]["derived_validation_digest"])
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_public_payload_values(payload)
    assert module.forecast_confidence_drift_monitor_payload(payload) == payload

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["forecast_count"] = "99"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.forecast_confidence_drift_monitor_payload(tampered)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.forecast_confidence_drift_monitor_payload(missing_digest)

    with pytest.raises(ValueError, match="ForecastConfidenceDriftMonitorReport"):
        module.forecast_confidence_drift_monitor_payload(object())


def test_count_decimals_are_canonicalized_for_deterministic_payload_digest() -> None:
    module = _module()

    row = module.ForecastConfidenceDriftRow(
        condition_id="condition-alpha",
        forecast_count=d("4.000000"),
        baseline_count=d("2.000000"),
        latest_count=d("2.000000"),
        baseline_mean_confidence=d("0.700000"),
        latest_mean_confidence=d("0.600000"),
        confidence_delta=d("-0.100000"),
        absolute_confidence_delta=d("0.100000"),
        status="confidence_drift_watch",
        reason_codes=("confidence_drift_detected",),
    )
    report = module.ForecastConfidenceDriftMonitorReport(
        generated_at=GENERATED_AT,
        config_version="forecast-confidence-drift-monitor-test-v0",
        forecast_count=d("4.000000"),
        row_count=d("1.000000"),
        watch_count=d("1.000000"),
        block_count=d("0.000000"),
        max_absolute_confidence_delta=d("0.100000"),
        status="confidence_drift_watch",
        reason_codes=("confidence_drift_detected",),
        rows=(row,),
    )

    canonical_row = module.ForecastConfidenceDriftRow(
        condition_id="condition-alpha",
        forecast_count=d("4"),
        baseline_count=d("2"),
        latest_count=d("2"),
        baseline_mean_confidence=d("0.700000"),
        latest_mean_confidence=d("0.600000"),
        confidence_delta=d("-0.100000"),
        absolute_confidence_delta=d("0.100000"),
        status="confidence_drift_watch",
        reason_codes=("confidence_drift_detected",),
    )
    canonical_report = module.ForecastConfidenceDriftMonitorReport(
        generated_at=GENERATED_AT,
        config_version="forecast-confidence-drift-monitor-test-v0",
        forecast_count=d("4"),
        row_count=d("1"),
        watch_count=d("1"),
        block_count=d("0"),
        max_absolute_confidence_delta=d("0.100000"),
        status="confidence_drift_watch",
        reason_codes=("confidence_drift_detected",),
        rows=(canonical_row,),
    )

    payload = module.forecast_confidence_drift_monitor_payload(report)

    assert report.derived_validation_digest == canonical_report.derived_validation_digest
    assert row.derived_validation_digest == canonical_row.derived_validation_digest
    assert payload["forecast_count"] == "4"
    assert payload["row_count"] == "1"
    assert payload["rows"][0]["forecast_count"] == "4"
    assert payload["rows"][0]["baseline_count"] == "2"
    assert payload["rows"][0]["latest_count"] == "2"


def test_public_payload_rejects_unsafe_live_auth_wallet_order_network_database_and_persist_surfaces() -> None:
    module = _module()
    report = module.build_forecast_confidence_drift_monitor_report(
        [],
        config=module.ForecastConfidenceDriftMonitorConfig(
            config_version="forecast-confidence-drift-monitor-test-v0",
        ),
        generated_at=GENERATED_AT,
    )
    payload = module.forecast_confidence_drift_monitor_payload(report)

    unsafe_payloads = (
        {**payload, "live_trading": "disabled"},
        {**payload, "auth_token": "redacted"},
        {**payload, "wallet_address": "redacted"},
        {**payload, "order_id": "redacted"},
        {**payload, "network_url": "redacted"},
        {**payload, "database_dsn": "redacted"},
        {**payload, "persist_path": "redacted"},
        {**payload, "notes": "live wallet order network database persist surface"},
    )
    for unsafe_payload in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe live surface"):
            module.forecast_confidence_drift_monitor_payload(unsafe_payload)


def test_forbidden_imports_are_not_used_by_monitor_module() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "forecast_confidence_drift_monitor.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)

    assert not {
        module_name
        for module_name in imported
        for prefix in FORBIDDEN_IMPORT_PREFIXES
        if module_name == prefix or module_name.startswith(f"{prefix}.")
    }

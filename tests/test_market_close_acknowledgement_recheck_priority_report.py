from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_close_acknowledgement_recheck_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    values = {
        "close_time_lag_watch_seconds": d("600.000000"),
        "close_time_lag_critical_seconds": d("1800.000000"),
        "missing_ack_watch_ratio": d("0.250000"),
        "missing_ack_critical_ratio": d("0.500000"),
        "stale_recheck_watch_seconds": d("900.000000"),
        "stale_recheck_critical_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return module.MarketCloseAcknowledgementRecheckPriorityConfig(**values)


def _candidate(
    market_slug: str,
    *,
    closed_seconds_ago: int,
    expected_ack_count: Decimal = d("4"),
    acknowledged_count: Decimal = d("4"),
    acknowledged_after_seconds: int | None = 30,
    rechecked_seconds_ago: int | None = 30,
):
    module = api()
    closed_at = GENERATED_AT - timedelta(seconds=closed_seconds_ago)
    return module.MarketCloseAcknowledgementRecheckPriorityInput(
        market_slug=market_slug,
        closed_at=closed_at,
        acknowledged_at=(
            None
            if acknowledged_after_seconds is None
            else closed_at + timedelta(seconds=acknowledged_after_seconds)
        ),
        last_rechecked_at=(
            None
            if rechecked_seconds_ago is None
            else GENERATED_AT - timedelta(seconds=rechecked_seconds_ago)
        ),
        expected_ack_count=expected_ack_count,
        acknowledged_count=acknowledged_count,
    )


def _build_report(*candidates, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_close_acknowledgement_recheck_priority_report(
        candidates,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_empty_input_returns_decimal_safe_empty_priority_report() -> None:
    module = api()
    report = _build_report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "empty"
    assert report.reason_codes == ("market_close_ack_priority_empty",)
    assert report.market_count == d("0")
    assert report.critical_market_count == d("0")
    assert report.watch_market_count == d("0")
    assert report.clear_market_count == d("0")
    assert report.priority_market_count == d("0")
    assert report.close_time_lag_market_count == d("0")
    assert report.missing_ack_market_count == d("0")
    assert report.stale_recheck_market_count == d("0")
    assert report.max_close_time_lag_seconds == d("0.000000")
    assert report.max_missing_ack_pressure_ratio == d("0.000000")
    assert report.max_stale_recheck_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.market_close_acknowledgement_recheck_priority_report_to_payload(
        report,
    )
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "0"
    assert payload["max_close_time_lag_seconds"] == "0.000000"
    assert payload["rows"] == []
    assert _unsafe_json_numeric_paths(payload) == ()
    json.dumps(payload, sort_keys=True, allow_nan=False)


def test_ranking_uses_close_lag_missing_pressure_stale_age_then_slug() -> None:
    report = _build_report(
        _candidate(
            "beta-tie",
            closed_seconds_ago=7200,
            acknowledged_after_seconds=None,
            acknowledged_count=d("2"),
            rechecked_seconds_ago=3600,
        ),
        _candidate(
            "more-stale-lower-pressure",
            closed_seconds_ago=7200,
            acknowledged_after_seconds=None,
            acknowledged_count=d("3"),
            rechecked_seconds_ago=7200,
        ),
        _candidate(
            "older-close",
            closed_seconds_ago=10800,
            acknowledged_after_seconds=None,
            acknowledged_count=d("3"),
            rechecked_seconds_ago=30,
        ),
        _candidate(
            "alpha-tie",
            closed_seconds_ago=7200,
            acknowledged_after_seconds=None,
            acknowledged_count=d("2"),
            rechecked_seconds_ago=3600,
        ),
        _candidate("clear", closed_seconds_ago=300),
    )

    assert tuple(row.market_slug for row in report.rows) == (
        "older-close",
        "alpha-tie",
        "beta-tie",
        "more-stale-lower-pressure",
        "clear",
    )
    assert tuple(row.priority_rank for row in report.rows) == (
        d("1"),
        d("2"),
        d("3"),
        d("4"),
        d("5"),
    )
    assert tuple(row.close_time_lag_seconds for row in report.rows) == (
        d("10800.000000"),
        d("7200.000000"),
        d("7200.000000"),
        d("7200.000000"),
        d("30.000000"),
    )
    assert tuple(row.missing_ack_pressure_ratio for row in report.rows) == (
        d("0.250000"),
        d("0.500000"),
        d("0.500000"),
        d("0.250000"),
        d("0.000000"),
    )
    assert tuple(row.stale_recheck_age_seconds for row in report.rows) == (
        d("30.000000"),
        d("3600.000000"),
        d("3600.000000"),
        d("7200.000000"),
        d("30.000000"),
    )


def test_thresholds_drive_statuses_reason_codes_and_report_counts() -> None:
    report = _build_report(
        _candidate(
            "critical",
            closed_seconds_ago=1800,
            acknowledged_after_seconds=None,
            acknowledged_count=d("2"),
            rechecked_seconds_ago=3600,
        ),
        _candidate(
            "watch",
            closed_seconds_ago=600,
            acknowledged_after_seconds=None,
            acknowledged_count=d("3"),
            rechecked_seconds_ago=900,
        ),
        _candidate("clear", closed_seconds_ago=120),
    )
    rows = {row.market_slug: row for row in report.rows}

    assert report.status == "critical"
    assert report.critical_market_count == d("1")
    assert report.watch_market_count == d("1")
    assert report.clear_market_count == d("1")
    assert report.priority_market_count == d("2")
    assert report.close_time_lag_market_count == d("2")
    assert report.missing_ack_market_count == d("2")
    assert report.stale_recheck_market_count == d("2")
    assert report.reason_codes == (
        "market_close_ack_priority_close_time_lag_critical",
        "market_close_ack_priority_close_time_lag_watch",
        "market_close_ack_priority_missing_ack_pressure_critical",
        "market_close_ack_priority_missing_ack_pressure_watch",
        "market_close_ack_priority_stale_recheck_age_critical",
        "market_close_ack_priority_stale_recheck_age_watch",
    )
    assert rows["critical"].priority_status == "critical"
    assert rows["critical"].reason_codes == (
        "market_close_ack_priority_close_time_lag_critical",
        "market_close_ack_priority_missing_ack_pressure_critical",
        "market_close_ack_priority_stale_recheck_age_critical",
    )
    assert rows["watch"].priority_status == "watch"
    assert rows["watch"].reason_codes == (
        "market_close_ack_priority_close_time_lag_watch",
        "market_close_ack_priority_missing_ack_pressure_watch",
        "market_close_ack_priority_stale_recheck_age_watch",
    )
    assert rows["clear"].priority_status == "clear"
    assert rows["clear"].reason_codes == ("market_close_ack_priority_clear",)


def test_utc_datetimes_counts_and_duplicate_keys_are_validated() -> None:
    with pytest.raises(ValueError, match="generated_at must be UTC-aware"):
        _build_report(generated_at=datetime(2026, 7, 2, 12, 0))

    with pytest.raises(ValueError, match="closed_at must be UTC-aware"):
        _candidate(
            "offset-close",
            closed_seconds_ago=1,
        ).__class__(
            market_slug="offset-close",
            closed_at=datetime(
                2026,
                7,
                2,
                8,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            acknowledged_at=None,
            last_rechecked_at=None,
            expected_ack_count=d("1"),
            acknowledged_count=d("0"),
        )

    with pytest.raises(ValueError, match="expected_ack_count must be a Decimal"):
        _candidate(
            "float-count",
            closed_seconds_ago=1,
            expected_ack_count=1.0,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="acknowledged_count must not exceed"):
        _candidate(
            "too-many",
            closed_seconds_ago=1,
            expected_ack_count=d("1"),
            acknowledged_count=d("2"),
        )
    with pytest.raises(ValueError, match="market_slug values must be unique"):
        _build_report(
            _candidate("duplicate", closed_seconds_ago=60),
            _candidate("duplicate", closed_seconds_ago=120),
        )
    with pytest.raises(ValueError, match="last_rechecked_at must be <= generated_at"):
        _build_report(
            _candidate(
                "future-recheck",
                closed_seconds_ago=60,
                rechecked_seconds_ago=-1,
            ),
        )


def test_public_dataclasses_are_frozen_and_revalidate_hard_flags() -> None:
    module = api()
    candidate = _candidate("frozen", closed_seconds_ago=60)
    report = _build_report(candidate)

    with pytest.raises(FrozenInstanceError):
        candidate.market_slug = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_rank = d("2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "clear"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(candidate, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    assert module.__all__ == (
        "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_PRIORITY_CONFIG_VERSION",
        "MarketCloseAcknowledgementRecheckPriorityConfig",
        "MarketCloseAcknowledgementRecheckPriorityInput",
        "MarketCloseAcknowledgementRecheckPriorityReport",
        "MarketCloseAcknowledgementRecheckPriorityRow",
        "build_market_close_acknowledgement_recheck_priority_report",
        "market_close_acknowledgement_recheck_priority_report_to_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)


def test_json_payload_uses_decimal_strings_iso_datetimes_and_static_purity() -> None:
    module = api()
    report = _build_report(
        _candidate(
            "json-safe",
            closed_seconds_ago=7200,
            acknowledged_after_seconds=None,
            acknowledged_count=d("1"),
            rechecked_seconds_ago=None,
        ),
    )

    payload = module.market_close_acknowledgement_recheck_priority_report_to_payload(
        report,
    )

    assert payload["market_count"] == "1"
    assert payload["priority_market_count"] == "1"
    assert payload["max_close_time_lag_seconds"] == "7200.000000"
    assert payload["max_missing_ack_pressure_ratio"] == "0.750000"
    assert payload["max_stale_recheck_age_seconds"] == "7200.000000"
    assert payload["rows"][0]["priority_rank"] == "1"
    assert payload["rows"][0]["missing_ack_count"] == "3"
    assert payload["rows"][0]["missing_ack_pressure_ratio"] == "0.750000"
    assert payload["rows"][0]["closed_at"] == "2026-07-02T10:00:00+00:00"
    assert payload["rows"][0]["acknowledged_at"] is None
    assert payload["rows"][0]["last_rechecked_at"] is None
    assert _unsafe_json_numeric_paths(payload) == ()
    json.dumps(payload, sort_keys=True, allow_nan=False)

    with pytest.raises(ValueError, match="report must be"):
        module.market_close_acknowledgement_recheck_priority_report_to_payload(object())

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
        "private_key",
        "credential",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _unsafe_json_numeric_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, (float, Decimal, datetime)):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_unsafe_json_numeric_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_unsafe_json_numeric_paths(nested, child))
        return tuple(paths)
    return ()

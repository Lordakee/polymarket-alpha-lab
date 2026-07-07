from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 16, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.liquidity_capacity_alert_trend_monitor",
    )


def alerts_api():
    return importlib.import_module(
        "polymarket_alpha_lab.liquidity_rotation_capacity_alerts",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def assert_no_numeric_payload_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_payload_values(item)


def source_report(
    generated_at: datetime,
    *,
    status: str,
    pass_count: str = "0",
    watch_count: str = "0",
    blocked_count: str = "0",
    source_missing_count: str = "0",
):
    alerts = alerts_api()
    rows = []
    row_index = 1
    for alert_status, count in (
        ("blocked", int(blocked_count)),
        ("watch", int(watch_count)),
        ("pass", int(pass_count)),
    ):
        for _ in range(count):
            rows.append(
                alerts.LiquidityRotationCapacityAlertRow(
                    redacted_category_ref=f"<redacted-category-{row_index:03d}>",
                    redacted_team_ref=f"<redacted-team-{row_index:03d}>",
                    rotation_status=(
                        "rotating_in" if alert_status != "pass" else "stable"
                    ),
                    liquidity_share_ratio_delta=(
                        d("0.100000") if alert_status != "pass" else d("0.000000")
                    ),
                    ending_liquidity_share_ratio=d("0.300000"),
                    capacity_pressure_ratio=(
                        d("2.500000")
                        if alert_status == "blocked"
                        else d("1.200000")
                        if alert_status == "watch"
                        else d("0.000000")
                    ),
                    slot_coverage_ratio=(
                        d("0.300000") if alert_status == "blocked" else d("1.000000")
                    ),
                    capacity_gap_count=d("1") if alert_status == "blocked" else d("0"),
                    source_row_count=d("1"),
                    alert_status=alert_status,
                    reason_codes=(
                        ("rotating_in_capacity_blocked", "capacity_gap_present")
                        if alert_status == "blocked"
                        else ("rotating_in_capacity_watch", "capacity_pressure_watch")
                        if alert_status == "watch"
                        else ("liquidity_rotation_capacity_clear",)
                    ),
                ),
            )
            row_index += 1
    for _ in range(int(source_missing_count)):
        rows.append(
            alerts.LiquidityRotationCapacityAlertRow(
                redacted_category_ref=f"<redacted-category-{row_index:03d}>",
                redacted_team_ref=f"<redacted-team-{row_index:03d}>",
                rotation_status="stable",
                liquidity_share_ratio_delta=d("0.000000"),
                ending_liquidity_share_ratio=d("0.000000"),
                capacity_pressure_ratio=d("0.000000"),
                slot_coverage_ratio=d("0.000000"),
                capacity_gap_count=d("0"),
                source_row_count=d("0"),
                alert_status="watch",
                reason_codes=("liquidity_rotation_capacity_source_missing",),
            ),
        )
        row_index += 1

    return alerts.LiquidityRotationCapacityAlertsReport(
        generated_at=generated_at,
        config_version="liquidity-rotation-capacity-alerts-test-v0",
        source_summary_count=d(str(len(rows))),
        alert_row_count=d(str(len(rows))),
        pass_alert_count=d(pass_count),
        watch_alert_count=d(str(int(watch_count) + int(source_missing_count))),
        blocked_alert_count=d(blocked_count),
        source_missing_count=d(source_missing_count),
        status=status,
        reason_codes=(
            ("liquidity_rotation_capacity_clear",)
            if status == "pass"
            else (
                "liquidity_rotation_capacity_watch",
                "liquidity_rotation_capacity_source_missing",
            )
            if source_missing_count != "0"
            else (f"liquidity_rotation_capacity_{status}",)
        ),
        alert_rows=tuple(
            sorted(rows, key=lambda row: ({"blocked": 0, "watch": 1, "pass": 2}[row.alert_status], row.redacted_category_ref)),
        ),
    )


def build_report(*snapshots, persistent_window_count: str = "2"):
    monitor = api()
    return monitor.build_liquidity_capacity_alert_trend_monitor_report(
        snapshots,
        config=monitor.LiquidityCapacityAlertTrendMonitorConfig(
            config_version="liquidity-capacity-alert-trend-monitor-test-v0",
            persistent_pressure_window_count=d(persistent_window_count),
        ),
        generated_at=GENERATED_AT,
    )


def test_summarizes_alert_snapshots_into_decimal_severity_trend_and_rows() -> None:
    report = build_report(
        source_report(
            datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            status="pass",
            pass_count="4",
        ),
        source_report(
            datetime(2026, 7, 2, 13, 0, tzinfo=UTC),
            status="watch",
            pass_count="3",
            watch_count="1",
        ),
        source_report(
            datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
            status="blocked",
            pass_count="2",
            watch_count="1",
            blocked_count="1",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "liquidity-capacity-alert-trend-monitor-test-v0"
    assert report.source_snapshot_count == d("3")
    assert report.observed_snapshot_count == d("3")
    assert report.blocked_snapshot_count == d("1")
    assert report.first_snapshot_generated_at == datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    assert report.latest_snapshot_generated_at == datetime(2026, 7, 2, 14, 0, tzinfo=UTC)
    assert report.latest_alert_status == "blocked"
    assert report.latest_alert_severity_score == d("2.000000")
    assert report.first_alert_severity_score == d("0.000000")
    assert report.alert_severity_delta == d("2.000000")
    assert report.alert_severity_trend == "declining"
    assert report.persistent_capacity_pressure is True
    assert report.status == "blocked"
    assert report.reason_codes == (
        "latest_liquidity_capacity_alert_blocked",
        "capacity_pressure_persistent",
        "liquidity_capacity_alert_trend_declining",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.alert_status for row in report.rows) == ("pass", "watch", "blocked")
    assert tuple(row.alert_severity_score for row in report.rows) == (
        d("0.000000"),
        d("1.000000"),
        d("2.000000"),
    )
    assert tuple(row.pressure_status for row in report.rows) == (
        "clear",
        "pressured",
        "pressured",
    )
    assert tuple(row.severity_delta_from_previous for row in report.rows) == (
        d("0.000000"),
        d("1.000000"),
        d("1.000000"),
    )


def test_improving_trend_clears_persistent_pressure_when_latest_window_recovers() -> None:
    report = build_report(
        source_report(
            datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            status="blocked",
            watch_count="1",
            blocked_count="1",
        ),
        source_report(
            datetime(2026, 7, 2, 13, 0, tzinfo=UTC),
            status="watch",
            pass_count="1",
            watch_count="1",
        ),
        source_report(
            datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
            status="pass",
            pass_count="2",
        ),
    )

    assert report.latest_alert_status == "pass"
    assert report.alert_severity_delta == d("-2.000000")
    assert report.alert_severity_trend == "improving"
    assert report.persistent_capacity_pressure is False
    assert report.status == "pass"
    assert report.reason_codes == ("liquidity_capacity_alert_trend_improving",)


def test_missing_or_blocked_sources_are_report_only_blocked_without_dividing_by_zero() -> None:
    report = build_report()

    assert report.source_snapshot_count == d("0")
    assert report.observed_snapshot_count == d("0")
    assert report.blocked_snapshot_count == d("0")
    assert report.first_snapshot_generated_at is None
    assert report.latest_snapshot_generated_at is None
    assert report.latest_alert_status is None
    assert report.latest_alert_severity_score == d("0.000000")
    assert report.alert_severity_delta == d("0.000000")
    assert report.alert_severity_trend == "flat"
    assert report.persistent_capacity_pressure is False
    assert report.status == "blocked"
    assert report.reason_codes == ("missing_liquidity_capacity_alert_snapshots",)
    assert report.rows == ()

    blocked_source = source_report(
        datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        status="watch",
        watch_count="1",
    )
    object.__setattr__(blocked_source, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        build_report(blocked_source)


def test_source_missing_pressure_is_watch_and_counted_as_persistent() -> None:
    report = build_report(
        source_report(
            datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            status="watch",
            source_missing_count="1",
        ),
        source_report(
            datetime(2026, 7, 2, 13, 0, tzinfo=UTC),
            status="watch",
            source_missing_count="1",
        ),
    )

    assert report.status == "watch"
    assert report.latest_source_missing_count == d("1")
    assert report.persistent_capacity_pressure is True
    assert report.alert_severity_trend == "flat"
    assert report.reason_codes == (
        "latest_liquidity_capacity_alert_watch",
        "capacity_pressure_persistent",
    )
    assert tuple(row.source_missing_count for row in report.rows) == (d("1"), d("1"))
    assert tuple(row.pressure_status for row in report.rows) == (
        "pressured",
        "pressured",
    )


def test_dataclasses_validate_decimal_only_flags_and_frozen_instances() -> None:
    monitor = api()
    report = build_report(
        source_report(
            datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            status="pass",
            pass_count="1",
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.rows[0].alert_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="persistent_pressure_window_count must be a Decimal"):
        monitor.LiquidityCapacityAlertTrendMonitorConfig(
            persistent_pressure_window_count=2,
        )

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="persistent_pressure_window_count"):
        monitor.LiquidityCapacityAlertTrendMonitorConfig(
            persistent_pressure_window_count=DerivedDecimal("2"),
        )


def test_generated_at_is_normalized_to_utc_and_rejects_naive_datetime() -> None:
    monitor = api()

    report = monitor.build_liquidity_capacity_alert_trend_monitor_report(
        (),
        config=monitor.LiquidityCapacityAlertTrendMonitorConfig(),
        generated_at=datetime(2026, 7, 2, 9, 0, tzinfo=timezone.utc),
    )

    assert report.generated_at == datetime(2026, 7, 2, 9, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        monitor.build_liquidity_capacity_alert_trend_monitor_report(
            (),
            config=monitor.LiquidityCapacityAlertTrendMonitorConfig(),
            generated_at=datetime(2026, 7, 2, 9, 0),
        )


def test_validation_digest_is_deterministic_and_tamper_evident() -> None:
    monitor = api()
    snapshots = (
        source_report(
            datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
            status="blocked",
            blocked_count="1",
        ),
        source_report(
            datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            status="pass",
            pass_count="1",
        ),
    )

    left = build_report(*snapshots)
    right = build_report(*reversed(snapshots))

    assert left.validation_digest == right.validation_digest
    assert len(left.validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in left.validation_digest)

    with pytest.raises(ValueError, match="validation_digest"):
        replace(left, validation_digest="0" * 64)

    tampered_row = replace(left.rows[0], pass_alert_count=d("2"), alert_row_count=d("2"))
    with pytest.raises(ValueError, match="validation_digest"):
        replace(left, rows=(tampered_row, *left.rows[1:]))

    with pytest.raises(ValueError, match="validation_digest"):
        monitor.liquidity_capacity_alert_trend_monitor_payload(
            replace(left, validation_digest="0" * 64),
        )


def test_public_payload_serializes_decimal_strings_and_revalidates_safety() -> None:
    monitor = api()
    report = build_report(
        source_report(
            datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            status="watch",
            watch_count="1",
        ),
    )

    payload = monitor.liquidity_capacity_alert_trend_monitor_payload(report)

    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-02T16:00:00+00:00"
    assert payload["source_snapshot_count"] == "1"
    assert payload["latest_alert_severity_score"] == "1.000000"
    assert payload["rows"][0]["watch_alert_count"] == "1"
    assert payload["validation_digest"] == report.validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_payload_values(payload)

    with pytest.raises(ValueError, match="report must be"):
        monitor.liquidity_capacity_alert_trend_monitor_payload(object())

    with pytest.raises(ValueError, match="unsafe live surface field|unsafe payload"):
        unsafe_report = replace(report, config_version="wallet-surface-test-v0")
        monitor.liquidity_capacity_alert_trend_monitor_payload(unsafe_report)


def test_module_scope_is_pure_report_reducer_with_local_exports_only() -> None:
    monitor = api()
    source = inspect.getsource(monitor)
    tree = ast.parse(source)

    assert monitor.__all__ == (
        "DEFAULT_LIQUIDITY_CAPACITY_ALERT_TREND_MONITOR_CONFIG_VERSION",
        "ALERT_TREND_STATUSES",
        "ALERT_SEVERITY_TRENDS",
        "PRESSURE_STATUSES",
        "LiquidityCapacityAlertTrendMonitorConfig",
        "LiquidityCapacityAlertTrendMonitorRow",
        "LiquidityCapacityAlertTrendMonitorReport",
        "build_liquidity_capacity_alert_trend_monitor_report",
        "liquidity_capacity_alert_trend_monitor_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
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
        "polymarket_alpha_lab",
    }
    for term in (
        "requests",
        "httpx",
        "supabase",
        "postgres",
        "private_key",
        "wallet",
        "account",
        "order",
        "investment_advice",
        "recommend",
    ):
        assert term not in source.lower()

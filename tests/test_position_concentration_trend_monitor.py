from __future__ import annotations

import importlib
import inspect
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_position_concentration_guard import (
    PaperPositionConcentrationGuardConfig,
    PaperPositionConcentrationRecord,
    build_paper_position_concentration_guard_report,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 7, 2, 9, 0, tzinfo=UTC)


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.position_concentration_trend_monitor",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def guard_config():
    return PaperPositionConcentrationGuardConfig(
        config_version="paper-position-concentration-guard-v0",
        market_warn_share=d("0.500000"),
        category_warn_share=d("0.600000"),
        team_warn_share=d("0.700000"),
        outcome_side_warn_share=d("0.400000"),
    )


def record(
    market_slug: str,
    *,
    category_id: str = "crypto",
    team_id: str = "crypto-team",
    outcome_side: str = "yes",
    open_notional: str = "10.000000",
):
    return PaperPositionConcentrationRecord(
        market_slug=market_slug,
        category_id=category_id,
        team_id=team_id,
        outcome_side=outcome_side,
        open_notional=d(open_notional),
    )


def snapshot(generated_at: datetime, *records: PaperPositionConcentrationRecord):
    return build_paper_position_concentration_guard_report(
        list(records),
        config=guard_config(),
        generated_at=generated_at,
    )


def report(*snapshots, **config_overrides):
    monitor = api()
    values = {
        "config_version": "position-concentration-trend-monitor-v0",
        "persistent_pressure_periods": 2,
        "watch_trend_rate": d("0.100000"),
        "blocked_trend_rate": d("0.500000"),
    }
    values.update(config_overrides)
    return monitor.build_position_concentration_trend_monitor_report(
        list(snapshots),
        config=monitor.PositionConcentrationTrendMonitorConfig(**values),
        generated_at=GENERATED_AT,
    )


def test_monitor_summarizes_decimal_rates_pressure_flags_and_status_rows() -> None:
    first = snapshot(
        BASE_AT,
        record("btc-up", open_notional="30.000000"),
        record("btc-down", outcome_side="no", open_notional="30.000000"),
        record(
            "fed-cut",
            category_id="macro",
            team_id="macro-team",
            outcome_side="yes",
            open_notional="40.000000",
        ),
    )
    middle = snapshot(
        BASE_AT + timedelta(hours=1),
        record("btc-up", open_notional="60.000000"),
        record("btc-down", outcome_side="no", open_notional="10.000000"),
        record(
            "fed-cut",
            category_id="macro",
            team_id="macro-team",
            outcome_side="yes",
            open_notional="30.000000",
        ),
    )
    latest = snapshot(
        BASE_AT + timedelta(hours=2),
        record("btc-up", open_notional="80.000000"),
        record("btc-down", outcome_side="no", open_notional="5.000000"),
        record(
            "fed-cut",
            category_id="macro",
            team_id="macro-team",
            outcome_side="yes",
            open_notional="15.000000",
        ),
    )

    trend = report(latest, first, middle)

    assert type(trend) is api().PositionConcentrationTrendMonitorReport
    assert trend.generated_at == GENERATED_AT
    assert trend.config_version == "position-concentration-trend-monitor-v0"
    assert trend.source_snapshot_count == d("3")
    assert trend.group_count == d("9")
    assert trend.first_snapshot_generated_at == first.generated_at
    assert trend.latest_snapshot_generated_at == latest.generated_at
    assert trend.latest_watch_count == d("4")
    assert trend.watch_count_delta == d("2")
    assert trend.watch_trend_rate == d("1.000000")
    assert trend.latest_max_share == d("0.950000")
    assert trend.max_share_delta == d("0.250000")
    assert trend.max_share_trend_rate == d("0.357143")
    assert trend.persistent_pressure_count == d("4")
    assert trend.improving_count == d("5")
    assert trend.declining_count == d("4")
    assert trend.unchanged_count == d("0")
    assert trend.status == "blocked"
    assert trend.reason_codes == (
        "watch_trend_rate_blocked",
        "max_share_trend_rate_watch",
        "persistent_pressure_detected",
        "declining_concentration_detected",
    )
    assert trend.paper_only is True
    assert trend.report_only is True
    assert trend.readonly is True

    assert tuple((row.group_type, row.group_value) for row in trend.rows[:3]) == (
        ("market", "[REDACTED]"),
        ("category", "[REDACTED]"),
        ("team", "[REDACTED]"),
    )
    category = trend.rows[1]
    assert category.latest_share_of_total_open_notional == d("0.850000")
    assert category.share_delta == d("0.250000")
    assert category.concentration_trend_rate == d("0.416667")
    assert category.persistent_pressure_flag is True
    assert category.trend_status == "declining"
    assert category.status == "blocked"
    assert category.reason_codes == (
        "group_persistent_pressure",
        "group_concentration_declining",
    )

    improving = next(
        row
        for row in trend.rows
        if row.group_type == "outcome_side"
        and row.latest_share_of_total_open_notional == d("0.050000")
    )
    assert improving.latest_share_of_total_open_notional == d("0.050000")
    assert improving.share_delta == d("-0.250000")
    assert improving.concentration_trend_rate == d("-0.833333")
    assert improving.persistent_pressure_flag is False
    assert improving.trend_status == "improving"
    assert improving.status == "pass"


def test_empty_history_is_clear_decimal_only_report() -> None:
    trend = report()

    assert trend.source_snapshot_count == d("0")
    assert trend.group_count == d("0")
    assert trend.first_snapshot_generated_at is None
    assert trend.latest_snapshot_generated_at is None
    assert trend.latest_watch_count == d("0")
    assert trend.watch_count_delta == d("0")
    assert trend.watch_trend_rate is None
    assert trend.latest_max_share is None
    assert trend.max_share_delta is None
    assert trend.max_share_trend_rate is None
    assert trend.persistent_pressure_count == d("0")
    assert trend.improving_count == d("0")
    assert trend.declining_count == d("0")
    assert trend.unchanged_count == d("0")
    assert trend.status == "pass"
    assert trend.reason_codes == ("position_concentration_trend_clear",)
    assert trend.rows == ()


def test_single_snapshot_marks_new_groups_without_numeric_rate() -> None:
    latest = snapshot(
        BASE_AT,
        record("btc-up", open_notional="70.000000"),
        record(
            "fed-cut",
            category_id="macro",
            team_id="macro-team",
            outcome_side="no",
            open_notional="30.000000",
        ),
    )

    trend = report(latest)

    assert trend.source_snapshot_count == d("1")
    assert trend.watch_count_delta == d("4")
    assert trend.watch_trend_rate is None
    assert trend.latest_max_share == d("0.700000")
    assert trend.max_share_delta is None
    assert trend.max_share_trend_rate is None
    assert trend.status == "watch"
    assert trend.reason_codes == ("initial_watch_groups_present",)
    assert trend.persistent_pressure_count == d("0")
    assert {row.trend_status for row in trend.rows} == {"new"}
    assert all(row.concentration_trend_rate is None for row in trend.rows)


def test_monitor_normalizes_timezones_freezes_dataclasses_and_rejects_bad_inputs() -> None:
    monitor = api()
    eastern = timezone(timedelta(hours=-4))
    source = snapshot(
        datetime(2026, 7, 2, 8, 0, tzinfo=eastern),
        record("btc-up", open_notional="10.000000"),
    )
    trend = monitor.build_position_concentration_trend_monitor_report(
        (source,),
        config=monitor.PositionConcentrationTrendMonitorConfig(
            config_version="position-concentration-trend-monitor-v0",
            persistent_pressure_periods=2,
            watch_trend_rate=d("0.100000"),
            blocked_trend_rate=d("0.500000"),
        ),
        generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
    )

    assert trend.first_snapshot_generated_at == datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        trend.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="watch_trend_rate must be a Decimal"):
        monitor.PositionConcentrationTrendMonitorConfig(
            config_version="v1",
            watch_trend_rate=0.1,
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(trend, paper_only=False)
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        monitor.build_position_concentration_trend_monitor_report(
            (),
            config=monitor.PositionConcentrationTrendMonitorConfig(config_version="v1"),
            generated_at=DatetimeSubclass(2026, 7, 2, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        monitor.build_position_concentration_trend_monitor_report(
            (),
            config=monitor.PositionConcentrationTrendMonitorConfig(config_version="v1"),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="source snapshot generated_at must not be after"):
        report(snapshot(GENERATED_AT + timedelta(minutes=1), record("future")))


def test_monitor_reports_watch_rate_without_overstating_persistence() -> None:
    first = snapshot(
        BASE_AT,
        record("btc-up", open_notional="55.000000"),
        record("btc-down", outcome_side="no", open_notional="10.000000"),
        record(
            "fed-cut",
            category_id="macro",
            team_id="macro-team",
            open_notional="35.000000",
        ),
    )
    latest = snapshot(
        BASE_AT + timedelta(hours=1),
        record("btc-up", open_notional="80.000000"),
        record("btc-down", outcome_side="no", open_notional="5.000000"),
        record(
            "fed-cut",
            category_id="macro",
            team_id="macro-team",
            open_notional="15.000000",
        ),
    )

    trend = report(first, latest)

    assert trend.watch_trend_rate == d("0.333333")
    assert "watch_trend_rate_watch" in trend.reason_codes


def test_monitor_reports_blocked_max_share_rate() -> None:
    first = snapshot(
        BASE_AT,
        record("btc-up", open_notional="50.000000"),
        record(
            "fed-cut",
            category_id="macro",
            team_id="macro-team",
            outcome_side="no",
            open_notional="50.000000",
        ),
    )
    latest = snapshot(
        BASE_AT + timedelta(hours=1),
        record("btc-up", open_notional="80.000000"),
        record(
            "fed-cut",
            category_id="macro",
            team_id="macro-team",
            outcome_side="no",
            open_notional="20.000000",
        ),
    )

    trend = report(first, latest)

    assert trend.max_share_trend_rate == d("0.600000")
    assert "max_share_trend_rate_blocked" in trend.reason_codes


def test_payload_is_json_ready_redacted_and_has_no_live_trading_surface() -> None:
    latest = snapshot(
        BASE_AT,
        record("private-market-slug", category_id="private-category", team_id="private-team"),
    )
    trend = report(latest)

    payload = api().position_concentration_trend_monitor_payload(trend)
    payload_text = repr(payload)

    assert payload["source_snapshot_count"] == "1"
    assert payload["rows"][0]["group_value"] == "[REDACTED]"
    assert "private-market-slug" not in payload_text
    assert "private-category" not in payload_text
    assert "private-team" not in payload_text
    assert "recommendation" not in payload_text.lower()
    assert "wallet" not in payload_text.lower()
    assert "order" not in payload_text.lower()
    assert asdict(trend)["paper_only"] is True


def test_source_surface_has_no_file_backed_durable_write_or_live_trading_terms() -> None:
    monitor = api()
    source_path = Path(inspect.getsourcefile(monitor) or "")
    source_text = source_path.read_text().lower()

    forbidden_tokens = (
        "broker",
        "ledger",
        "execute",
        "open(",
        ".write(",
        "storage_path",
        "file-backed",
        "durable state",
        "durable write",
    )

    for token in forbidden_tokens:
        assert token not in source_text

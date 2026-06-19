from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.outcome_freshness import (
    OutcomeFreshnessReport,
    OutcomeFreshnessStatusRow,
)
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingLog, OutcomeTrackingReport
from polymarket_alpha_lab.positions import PaperNavLog, PaperNavSnapshot, PaperPositionMark
from polymarket_alpha_lab.strategy_cycle import (
    PaperStrategyCycleLog,
    PaperStrategyCycleReport,
)
from polymarket_alpha_lab.strategy_evidence_trend import (
    PaperStrategyEvidenceTrendGapRow,
    PaperStrategyEvidenceTrendReport,
    PaperStrategyEvidenceTrendStatusRow,
)


GENERATED_AT = datetime(2026, 6, 17, 18, 0, tzinfo=UTC)
HEX = "a" * 64
SNAPSHOT_STATUSES = (
    "no_local_evidence",
    "local_evidence_gaps",
    "local_risk_flags",
    "local_evidence_observed",
)
EVIDENCE_GAP_NAMES = (
    "missing_cycles",
    "missing_paper_trades",
    "missing_nav_snapshots",
    "missing_outcome_evidence",
    "missing_strategy_audit_history",
    "latest_strategy_audit_not_ready",
    "negative_cost_adjusted_edges",
    "unexecutable_open_positions",
)
OUTCOME_FRESHNESS_STATUSES = (
    "empty_outcome_history",
    "latest_outcomes_fresh",
    "latest_outcomes_pending",
    "latest_outcomes_stale",
)


def _runner_api() -> tuple[type[Any], type[Any], Any]:
    module = import_module("polymarket_alpha_lab.local_observability_trends")
    return (
        module.LocalObservabilityTrendsConfig,
        module.LocalObservabilityTrendsReport,
        module.run_local_observability_trends,
    )


def _config(**overrides: Any) -> Any:
    LocalObservabilityTrendsConfig, _Report, _runner = _runner_api()
    values = {
        "config_version": "local-observability-trends-v0",
        "outcome_stale_after_seconds": 10_000,
    }
    values.update(overrides)
    return LocalObservabilityTrendsConfig(**values)


def _run(
    *,
    cycle_log: Path,
    trade_log: Path,
    nav_log: Path,
    outcome_log: Path | None = None,
    strategy_audit_log: Path | None = None,
    config: Any | None = None,
):
    _Config, _Report, run_local_observability_trends = _runner_api()
    return run_local_observability_trends(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        outcome_log=outcome_log,
        strategy_audit_log=strategy_audit_log,
        config=_config() if config is None else config,
        generated_at=GENERATED_AT,
    )


def _write_empty_logs(tmp_path: Path) -> tuple[Path, Path, Path]:
    cycle_log = tmp_path / "cycle.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    for path in (cycle_log, trade_log, nav_log):
        path.write_bytes(b"")
    return cycle_log, trade_log, nav_log


def _preserved_bytes(paths: tuple[Path, ...]) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in paths}


def _assert_preserved_bytes(before: dict[Path, bytes]) -> None:
    assert {path: path.read_bytes() for path in before} == before


def _cycle(generated_at: datetime) -> PaperStrategyCycleReport:
    return PaperStrategyCycleReport(
        generated_at=generated_at,
        config_version="strategy-cycle-v1",
        scan_market_count=3,
        considered_count=3,
        snapshot_ready_count=0,
        cost_aware_report_count=0,
        blocked_counts=(("blocked_fetch_error", 3),),
        screening_report=None,
    )


def _trade(index: int, *, cost_adjusted_edge: Decimal = Decimal("0.040000")):
    return PaperTradeRecord(
        packet_id=f"pkt-{index}",
        packet_created_at=datetime(2026, 6, 17, 9, index, tzinfo=UTC),
        condition_id=f"0x{index:04x}",
        token_id=f"{index}",
        market_slug=f"market-{index}",
        market_url=f"https://polymarket.com/event/market-{index}",
        question=f"Will market {index} resolve yes?",
        outcome_name="YES",
        strategy_type="market_quality",
        source_score="80.000",
        market_raw_archive_path=f"data/raw/gamma/market-{index}.json",
        order_book_raw_archive_path=f"data/raw/clob/book-{index}.json",
        order_book_raw_payload_sha256=HEX,
        order_book_snapshot_sha256=HEX,
        risk_tags=("liquidity",),
        rule_text_hash=HEX,
        resolution_source="Official source",
        decision_timestamp_utc=datetime(2026, 6, 17, 9, index, 30, tzinfo=UTC),
        model_probability=Decimal("0.6000"),
        confidence=Decimal("0.8000"),
        research_bid=Decimal("0.5000"),
        research_ask=Decimal("0.5400"),
        research_midpoint=Decimal("0.5200"),
        research_expected_entry_price=Decimal("0.5400"),
        research_fair_value_estimate=Decimal("0.6000"),
        research_theoretical_edge=Decimal("0.060000"),
        research_spread=Decimal("0.0400"),
        research_slippage_estimate=Decimal("0.004000"),
        research_cost_adjusted_edge=cost_adjusted_edge,
        max_executable_size=Decimal("100"),
        order_side="buy",
        order_requested_size=Decimal("100"),
        fill_filled_size=Decimal("100"),
        fill_unfilled_size=Decimal("0"),
        fill_status="complete",
        fill_average_price=Decimal("0.5400"),
        fill_worst_price=Decimal("0.5500"),
        fill_best_bid=Decimal("0.5000"),
        fill_best_ask=Decimal("0.5400"),
        fill_midpoint=Decimal("0.5200"),
        fill_spread=Decimal("0.0400"),
        fill_slippage_estimate=Decimal("0.006000"),
        order_book_captured_at=datetime(2026, 6, 17, 9, index, 20, tzinfo=UTC),
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Hold to resolution.",
        thesis="Paper test thesis.",
        invalidating_conditions="Resolution source changes.",
    )


def _nav_snapshot(
    marked_at: datetime,
    exit_nav: Decimal,
    marks: tuple[PaperPositionMark, ...] = (),
) -> PaperNavSnapshot:
    mark_exit_value = sum((mark.exit_value for mark in marks), Decimal("0"))
    cash_balance = exit_nav - mark_exit_value
    total_cost_basis = sum((mark.cost_basis for mark in marks), Decimal("0"))
    unrealized_exit_pnl = sum(
        (mark.exit_value - mark.cost_basis for mark in marks),
        Decimal("0"),
    )
    midpoint_nav = (
        cash_balance
        + sum(
            (
                mark.midpoint_value
                for mark in marks
                if mark.midpoint_value is not None
            ),
            Decimal("0"),
        )
        if all(mark.midpoint_value is not None for mark in marks)
        else None
    )
    return PaperNavSnapshot(
        marked_at=marked_at,
        starting_cash=cash_balance + total_cost_basis,
        cash_balance=cash_balance,
        realized_pnl=Decimal("0"),
        exit_nav=exit_nav,
        midpoint_nav=midpoint_nav,
        total_cost_basis=total_cost_basis,
        unrealized_exit_pnl=unrealized_exit_pnl,
        marks=marks,
    )


def _no_exit_depth_mark(suffix: str) -> PaperPositionMark:
    return PaperPositionMark(
        condition_id=f"condition-{suffix}",
        token_id=f"token-{suffix}",
        market_slug=f"market-{suffix}",
        outcome_name="YES",
        open_size=Decimal("100.0000"),
        cost_basis=Decimal("70.0000"),
        average_entry_price=Decimal("0.7000"),
        order_book_captured_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        order_book_snapshot_sha256=HEX,
        exit_filled_size=Decimal("0.0000"),
        exit_unfilled_size=Decimal("100.0000"),
        exit_average_price=None,
        exit_worst_price=None,
        exit_value=Decimal("0.0000"),
        midpoint_price=None,
        midpoint_value=None,
        best_bid=None,
        best_ask=None,
        spread=None,
        slippage_estimate=None,
        mark_status="no_exit_depth",
    )


def _fully_executable_mark(suffix: str) -> PaperPositionMark:
    return PaperPositionMark(
        condition_id=f"condition-{suffix}",
        token_id=f"token-{suffix}",
        market_slug=f"market-{suffix}",
        outcome_name="YES",
        open_size=Decimal("150.0000"),
        cost_basis=Decimal("120.0000"),
        average_entry_price=Decimal("0.8000"),
        order_book_captured_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        order_book_snapshot_sha256=HEX,
        exit_filled_size=Decimal("150.0000"),
        exit_unfilled_size=Decimal("0.0000"),
        exit_average_price=Decimal("0.6000"),
        exit_worst_price=Decimal("0.6000"),
        exit_value=Decimal("90.0000"),
        midpoint_price=Decimal("0.6500"),
        midpoint_value=Decimal("97.5000"),
        best_bid=Decimal("0.6000"),
        best_ask=Decimal("0.7000"),
        spread=Decimal("0.1000"),
        slippage_estimate=Decimal("0.0000"),
        mark_status="fully_executable",
    )


def _observation(generated_at: datetime, suffix: str) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=generated_at,
        source_packet_id=f"pkt-{suffix}",
        condition_id=f"0x{suffix}",
        token_id=f"tok-{suffix}",
        market_slug=f"market-{suffix}",
        strategy_type="market_quality",
        risk_tags=("liquidity",),
        predicted_probability=Decimal("0.6000"),
        actual_outcome_value=Decimal("1"),
    )


def _outcome_report(
    *,
    generated_at: datetime,
    total_markets_checked: int,
    resolved_count: int,
    pending_count: int,
    suffix: str,
) -> OutcomeTrackingReport:
    observations = tuple(
        _observation(generated_at, f"{suffix}-{index}")
        for index in range(resolved_count)
    )
    evidence_report = (
        build_paper_forecast_evidence_report(
            observations,
            config=PaperForecastEvidenceConfig(config_version="outcome-tracker-v1"),
            generated_at=generated_at,
        )
        if observations
        else None
    )
    return OutcomeTrackingReport(
        generated_at=generated_at,
        config_version="outcome-tracker-v1",
        total_markets_checked=total_markets_checked,
        resolved_count=resolved_count,
        pending_count=pending_count,
        observations=observations,
        forecast_evidence_report=evidence_report,
    )


def _outcome_status_rows(
    counts: dict[str, int],
    total: int,
) -> tuple[OutcomeFreshnessStatusRow, ...]:
    return tuple(
        OutcomeFreshnessStatusRow(
            status=status,
            outcome_report_count=counts.get(status, 0),
            outcome_report_ratio=(
                None
                if total == 0
                else (Decimal(counts.get(status, 0)) / Decimal(total)).quantize(
                    Decimal("0.000001"),
                )
            ),
        )
        for status in OUTCOME_FRESHNESS_STATUSES
    )


def test_empty_required_logs_yield_empty_trend_states(tmp_path):
    cycle_log, trade_log, nav_log = _write_empty_logs(tmp_path)
    before = _preserved_bytes((cycle_log, trade_log, nav_log))
    _Config, LocalObservabilityTrendsReport, _runner = _runner_api()

    report = _run(cycle_log=cycle_log, trade_log=trade_log, nav_log=nav_log)

    assert isinstance(report, LocalObservabilityTrendsReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "local-observability-trends-v0"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    _assert_preserved_bytes(before)

    assert report.outcome_freshness.status == "empty_outcome_history"
    assert report.outcome_freshness.outcome_report_count == 0
    assert report.outcome_freshness.status_rows == _outcome_status_rows({}, 0)

    assert report.nav_risk_trend.status == "empty_nav_risk_history"
    assert report.nav_risk_trend.nav_risk_report_count == 0
    assert report.nav_risk_trend.latest_exit_nav is None

    assert report.paper_trade_cost_trend.status == "empty_cost_audit_history"
    assert report.paper_trade_cost_trend.cost_audit_report_count == 0
    assert report.paper_trade_cost_trend.latest_trade_count == 0

    assert isinstance(report.strategy_evidence_trend, PaperStrategyEvidenceTrendReport)
    assert report.strategy_evidence_trend.snapshot_report_count == 0
    assert report.strategy_evidence_trend.latest_status is None
    assert report.strategy_evidence_trend.latest_evidence_gap_names == ()
    assert report.strategy_evidence_trend.status_rows == tuple(
        PaperStrategyEvidenceTrendStatusRow(status, 0, None)
        for status in SNAPSHOT_STATUSES
    )
    assert report.strategy_evidence_trend.gap_rows == tuple(
        PaperStrategyEvidenceTrendGapRow(gap_name, 0, None)
        for gap_name in EVIDENCE_GAP_NAMES
    )


def test_config_version_requires_exact_string_type():
    class ConfigVersion(str):
        pass

    with pytest.raises(ValueError, match="config_version must be a string"):
        _config(config_version=ConfigVersion("local-observability-trends-v0"))


def test_report_direct_constructor_normalizes_generated_at_to_utc(tmp_path):
    cycle_log, trade_log, nav_log = _write_empty_logs(tmp_path)
    source_report = _run(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
    )
    _Config, LocalObservabilityTrendsReport, _runner = _runner_api()
    generated_at = datetime(
        2026,
        6,
        17,
        14,
        0,
        tzinfo=timezone(-timedelta(hours=4)),
    )

    report = LocalObservabilityTrendsReport(
        generated_at=generated_at,
        config_version=source_report.config_version,
        strategy_evidence_trend=source_report.strategy_evidence_trend,
        outcome_freshness=source_report.outcome_freshness,
        nav_risk_trend=source_report.nav_risk_trend,
        paper_trade_cost_trend=source_report.paper_trade_cost_trend,
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC


def test_absent_optional_logs_yield_empty_outcome_and_single_gap_snapshot(tmp_path):
    cycle_log, trade_log, nav_log = _write_empty_logs(tmp_path)
    PaperStrategyCycleLog(cycle_log).append(
        _cycle(datetime(2026, 6, 17, 12, 0, tzinfo=UTC)),
    )
    PaperTradeJournal(trade_log).append(_trade(1))
    PaperNavLog(nav_log).append(
        _nav_snapshot(datetime(2026, 6, 17, 12, 30, tzinfo=UTC), Decimal("10000.0000")),
    )
    before = _preserved_bytes((cycle_log, trade_log, nav_log))

    report = _run(cycle_log=cycle_log, trade_log=trade_log, nav_log=nav_log)

    _assert_preserved_bytes(before)
    assert report.outcome_freshness.status == "empty_outcome_history"
    assert report.outcome_freshness.outcome_report_count == 0
    assert report.nav_risk_trend.nav_risk_report_count == 1
    assert report.nav_risk_trend.latest_exit_nav == Decimal("10000.0000")
    assert report.paper_trade_cost_trend.cost_audit_report_count == 1
    assert report.paper_trade_cost_trend.latest_trade_count == 1
    assert report.strategy_evidence_trend.snapshot_report_count == 1
    assert report.strategy_evidence_trend.latest_status == "local_evidence_gaps"
    assert report.strategy_evidence_trend.latest_evidence_gap_names == (
        "missing_outcome_evidence",
        "missing_strategy_audit_history",
    )
    rows = {
        row.evidence_gap_name: row for row in report.strategy_evidence_trend.gap_rows
    }
    assert rows["missing_outcome_evidence"].gap_count == 1
    assert rows["missing_strategy_audit_history"].gap_count == 1
    assert rows["missing_cycles"].gap_count == 0
    assert rows["missing_paper_trades"].gap_count == 0
    assert rows["missing_nav_snapshots"].gap_count == 0


def test_strategy_evidence_trend_uses_max_required_append_prefixes(tmp_path):
    cycle_log, trade_log, nav_log = _write_empty_logs(tmp_path)
    for hour in (12, 13):
        PaperStrategyCycleLog(cycle_log).append(
            _cycle(datetime(2026, 6, 17, hour, 0, tzinfo=UTC)),
        )
    for index in (1, 2, 3):
        PaperTradeJournal(trade_log).append(_trade(index))
    older_risky_trade = replace(
        _trade(4, cost_adjusted_edge=Decimal("-0.010000")),
        packet_created_at=datetime(2026, 6, 17, 8, 0, tzinfo=UTC),
        decision_timestamp_utc=datetime(2026, 6, 17, 8, 0, 30, tzinfo=UTC),
        order_book_captured_at=datetime(2026, 6, 17, 8, 0, 20, tzinfo=UTC),
    )
    PaperTradeJournal(trade_log).append(older_risky_trade)
    for index, exit_nav in enumerate(
        (Decimal("10000.0000"), Decimal("10010.0000"), Decimal("10020.0000")),
        start=1,
    ):
        PaperNavLog(nav_log).append(
            _nav_snapshot(
                datetime(2026, 6, 17, 14, index, tzinfo=UTC),
                exit_nav,
            ),
        )
    before = _preserved_bytes((cycle_log, trade_log, nav_log))

    report = _run(cycle_log=cycle_log, trade_log=trade_log, nav_log=nav_log)

    _assert_preserved_bytes(before)
    trend = report.strategy_evidence_trend
    assert trend.snapshot_report_count == 4
    assert trend.latest_status == "local_risk_flags"
    assert trend.latest_evidence_gap_names == (
        "missing_outcome_evidence",
        "missing_strategy_audit_history",
        "negative_cost_adjusted_edges",
    )

    status_rows = {row.snapshot_status: row for row in trend.status_rows}
    assert status_rows["local_evidence_gaps"].snapshot_count == 3
    assert status_rows["local_evidence_gaps"].snapshot_ratio == Decimal("0.750000")
    assert status_rows["local_risk_flags"].snapshot_count == 1
    assert status_rows["local_risk_flags"].snapshot_ratio == Decimal("0.250000")
    assert status_rows["no_local_evidence"].snapshot_count == 0
    assert status_rows["local_evidence_observed"].snapshot_count == 0

    gap_rows = {row.evidence_gap_name: row for row in trend.gap_rows}
    assert gap_rows["missing_cycles"].gap_count == 0
    assert gap_rows["missing_paper_trades"].gap_count == 0
    assert gap_rows["missing_nav_snapshots"].gap_count == 0
    assert gap_rows["missing_outcome_evidence"].gap_count == 4
    assert gap_rows["missing_outcome_evidence"].gap_ratio == Decimal("1.000000")
    assert gap_rows["missing_strategy_audit_history"].gap_count == 4
    assert gap_rows["missing_strategy_audit_history"].gap_ratio == Decimal("1.000000")
    assert gap_rows["negative_cost_adjusted_edges"].gap_count == 1
    assert gap_rows["negative_cost_adjusted_edges"].gap_ratio == Decimal("0.250000")


def test_nav_risk_trend_child_prefixes_preserve_append_order_with_nonmonotonic_marked_at(
    tmp_path,
):
    cycle_log, trade_log, nav_log = _write_empty_logs(tmp_path)
    first_appended_unexecutable_nav = _nav_snapshot(
        datetime(2026, 6, 17, 17, 0, tzinfo=UTC),
        Decimal("10000.0000"),
        marks=(_no_exit_depth_mark("first"),),
    )
    older_second_appended_observed_nav = _nav_snapshot(
        datetime(2026, 6, 17, 16, 0, tzinfo=UTC),
        Decimal("10100.0000"),
    )
    latest_appended_observed_nav = _nav_snapshot(
        datetime(2026, 6, 17, 18, 0, tzinfo=UTC),
        Decimal("10200.0000"),
    )
    for snapshot in (
        first_appended_unexecutable_nav,
        older_second_appended_observed_nav,
        latest_appended_observed_nav,
    ):
        PaperNavLog(nav_log).append(snapshot)
    before = _preserved_bytes((cycle_log, trade_log, nav_log))

    report = _run(cycle_log=cycle_log, trade_log=trade_log, nav_log=nav_log)

    _assert_preserved_bytes(before)

    trend = report.nav_risk_trend
    assert trend.nav_risk_report_count == 3
    assert trend.status == "latest_nav_risk_observed"
    assert trend.latest_exit_nav == Decimal("10200.0000")
    assert trend.consecutive_unexecutable_open_position_count == 0

    status_rows = {row.status: row for row in trend.status_rows}
    assert status_rows["latest_nav_has_unexecutable_positions"].report_count == 1
    assert (
        status_rows["latest_nav_has_unexecutable_positions"].report_ratio
        == Decimal("0.333333")
    )
    assert status_rows["latest_nav_risk_observed"].report_count == 2
    assert status_rows["latest_nav_risk_observed"].report_ratio == Decimal("0.666667")

    evidence_trend = report.strategy_evidence_trend
    assert evidence_trend.snapshot_report_count == 3
    assert evidence_trend.latest_status == "local_evidence_gaps"
    assert evidence_trend.latest_evidence_gap_names == (
        "missing_cycles",
        "missing_paper_trades",
        "missing_outcome_evidence",
        "missing_strategy_audit_history",
    )

    evidence_status_rows = {
        row.snapshot_status: row for row in evidence_trend.status_rows
    }
    assert evidence_status_rows["local_risk_flags"].snapshot_count == 1
    assert evidence_status_rows["local_risk_flags"].snapshot_ratio == Decimal("0.333333")
    assert evidence_status_rows["local_evidence_gaps"].snapshot_count == 2
    assert (
        evidence_status_rows["local_evidence_gaps"].snapshot_ratio
        == Decimal("0.666667")
    )

    evidence_gap_rows = {
        row.evidence_gap_name: row for row in evidence_trend.gap_rows
    }
    assert evidence_gap_rows["unexecutable_open_positions"].gap_count == 1
    assert (
        evidence_gap_rows["unexecutable_open_positions"].gap_ratio
        == Decimal("0.333333")
    )


def test_local_nav_metrics_use_append_order_for_all_sequence_and_latest_fields():
    module = import_module("polymarket_alpha_lab.local_observability_trends")
    first_appended_timestamp_latest = _nav_snapshot(
        datetime(2026, 6, 17, 19, 0, tzinfo=UTC),
        Decimal("10000.0000"),
        marks=(_no_exit_depth_mark("first"),),
    )
    append_latest_fully_executable = _nav_snapshot(
        datetime(2026, 6, 17, 18, 0, tzinfo=UTC),
        Decimal("10150.0000"),
        marks=(_fully_executable_mark("latest"),),
    )

    report = module._build_append_order_nav_risk_metrics_report(
        (first_appended_timestamp_latest, append_latest_fully_executable),
        generated_at=GENERATED_AT,
    )

    assert report.nav_snapshot_count == 2
    assert report.first_marked_at == first_appended_timestamp_latest.marked_at
    assert report.last_marked_at == append_latest_fully_executable.marked_at
    assert report.latest_exit_nav == append_latest_fully_executable.exit_nav
    assert report.latest_starting_cash == append_latest_fully_executable.starting_cash
    assert report.latest_cash_balance == append_latest_fully_executable.cash_balance
    assert report.latest_total_cost_basis == Decimal("120.0000")
    assert report.latest_unrealized_exit_pnl == Decimal("-30.0000")
    assert report.pending_notional == Decimal("120.0000")
    assert report.open_position_count == 1
    assert report.fully_executable_count == 1
    assert report.partially_executable_count == 0
    assert report.no_exit_depth_count == 0
    assert report.largest_market_exposure_value == Decimal("90.0000")
    assert report.largest_market_exposure_share == Decimal("0.008867")
    assert tuple(row.market_slug for row in report.exposure_rows) == ("market-latest",)
    assert report.exposure_rows[0].open_size == Decimal("150.0000")
    assert report.exposure_rows[0].cost_basis == Decimal("120.0000")
    assert report.exposure_rows[0].exit_value == Decimal("90.0000")

    assert report.peak_exit_nav == Decimal("10150.0000")
    assert report.trough_exit_nav == Decimal("10000.0000")
    assert report.cumulative_return == Decimal("0.015000")
    assert report.max_drawdown == Decimal("0.0000")
    assert report.max_drawdown_pct == Decimal("0.000000")
    assert report.worst_nav_delta == Decimal("150.0000")
    assert report.nav_return_volatility == Decimal("0.000000")


def test_nav_prefixes_and_outcome_freshness_preserve_append_order(tmp_path):
    cycle_log, trade_log, nav_log = _write_empty_logs(tmp_path)
    outcome_log = tmp_path / "outcomes.jsonl"
    first_nav = _nav_snapshot(
        datetime(2026, 6, 17, 17, 0, tzinfo=UTC),
        Decimal("10100.0000"),
    )
    older_second_nav = _nav_snapshot(
        datetime(2026, 6, 17, 16, 0, tzinfo=UTC),
        Decimal("9900.0000"),
    )
    PaperNavLog(nav_log).append(first_nav)
    PaperNavLog(nav_log).append(older_second_nav)
    first_outcome = _outcome_report(
        generated_at=datetime(2026, 6, 17, 17, 0, tzinfo=UTC),
        total_markets_checked=1,
        resolved_count=1,
        pending_count=0,
        suffix="first",
    )
    older_second_outcome = _outcome_report(
        generated_at=datetime(2026, 6, 17, 16, 30, tzinfo=UTC),
        total_markets_checked=2,
        resolved_count=0,
        pending_count=2,
        suffix="second",
    )
    OutcomeTrackingLog(outcome_log).append(first_outcome)
    OutcomeTrackingLog(outcome_log).append(older_second_outcome)
    before = _preserved_bytes((cycle_log, trade_log, nav_log, outcome_log))

    report = _run(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        outcome_log=outcome_log,
    )

    _assert_preserved_bytes(before)

    assert report.nav_risk_trend.nav_risk_report_count == 2
    assert report.nav_risk_trend.latest_exit_nav == Decimal("9900.0000")
    assert report.nav_risk_trend.latest_cumulative_return == Decimal("-0.019802")
    assert report.nav_risk_trend.latest_max_drawdown == Decimal("200.0000")
    assert report.nav_risk_trend.latest_max_drawdown_pct == Decimal("0.019802")
    assert report.nav_risk_trend.latest_nav_return_volatility == Decimal("0.000000")
    assert report.nav_risk_trend.worst_observed_max_drawdown_pct == Decimal("0.019802")
    assert report.nav_risk_trend.status == "latest_nav_risk_observed"
    nav_status_rows = {row.status: row for row in report.nav_risk_trend.status_rows}
    assert nav_status_rows["latest_nav_risk_observed"].report_count == 2

    assert isinstance(report.outcome_freshness, OutcomeFreshnessReport)
    assert report.outcome_freshness.outcome_report_count == 2
    assert report.outcome_freshness.first_report_generated_at == first_outcome.generated_at
    assert (
        report.outcome_freshness.latest_report_generated_at
        == older_second_outcome.generated_at
    )
    assert report.outcome_freshness.latest_total_markets_checked == 2
    assert report.outcome_freshness.latest_resolved_count == 0
    assert report.outcome_freshness.latest_pending_count == 2
    assert report.outcome_freshness.latest_report_age_seconds == 5400
    assert report.outcome_freshness.status == "latest_outcomes_pending"
    assert report.outcome_freshness.status_rows == _outcome_status_rows(
        {
            "latest_outcomes_fresh": 1,
            "latest_outcomes_pending": 1,
        },
        2,
    )


def test_missing_and_invalid_local_logs_propagate_normal_exceptions(tmp_path):
    cycle_log, trade_log, nav_log = _write_empty_logs(tmp_path)
    missing_cycle_log = tmp_path / "missing-cycle.jsonl"

    with pytest.raises(FileNotFoundError):
        _run(cycle_log=missing_cycle_log, trade_log=trade_log, nav_log=nav_log)

    cycle_log.write_text("not json\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 1"):
        _run(cycle_log=cycle_log, trade_log=trade_log, nav_log=nav_log)

    cycle_log.write_text("", encoding="utf-8")
    outcome_log = tmp_path / "outcomes.jsonl"
    outcome_log.write_text("not json\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 1"):
        _run(
            cycle_log=cycle_log,
            trade_log=trade_log,
            nav_log=nav_log,
            outcome_log=outcome_log,
        )

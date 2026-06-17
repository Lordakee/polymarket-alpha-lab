from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsConfig,
    LocalObservabilityTrendsReport,
    run_local_observability_trends,
)
from polymarket_alpha_lab.outcome_tracker import (
    OutcomeTrackingLog,
    OutcomeTrackingReport,
)
from polymarket_alpha_lab.positions import PaperNavLog, PaperNavSnapshot
from polymarket_alpha_lab.strategy_cycle import (
    PaperStrategyCycleLog,
    PaperStrategyCycleReport,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)
from polymarket_alpha_lab.strategy_risk_audit_log import PaperStrategyRiskAuditLog


GENERATED_AT = datetime(2026, 6, 17, 12, 0, tzinfo=UTC)
HEX = "a" * 64


def _config(**overrides):
    values = {
        "config_version": "local-observability-trends-v0",
        "outcome_stale_after_seconds": 60,
    }
    values.update(overrides)
    return LocalObservabilityTrendsConfig(**values)


def _cycle_report(index: int) -> PaperStrategyCycleReport:
    return PaperStrategyCycleReport(
        generated_at=GENERATED_AT + timedelta(minutes=index),
        config_version="strategy-cycle-v1",
        scan_market_count=10,
        considered_count=0,
        snapshot_ready_count=0,
        cost_aware_report_count=0,
        blocked_counts=(),
        screening_report=None,
    )


def _nav_snapshot(index: int, *, exit_nav: Decimal) -> PaperNavSnapshot:
    return PaperNavSnapshot(
        marked_at=GENERATED_AT + timedelta(minutes=index),
        starting_cash=Decimal("10000"),
        cash_balance=exit_nav,
        realized_pnl=exit_nav - Decimal("10000"),
        exit_nav=exit_nav,
        midpoint_nav=exit_nav,
        total_cost_basis=Decimal("0"),
        unrealized_exit_pnl=Decimal("0"),
        marks=(),
    )


def _trade_record(index: int, *, cost_adjusted_edge: Decimal) -> PaperTradeRecord:
    return PaperTradeRecord(
        packet_id=f"pkt-{index}",
        packet_created_at=GENERATED_AT + timedelta(minutes=index),
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
        decision_timestamp_utc=GENERATED_AT + timedelta(minutes=index, seconds=30),
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
        order_book_captured_at=GENERATED_AT + timedelta(minutes=index, seconds=20),
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Hold to resolution.",
        thesis="Paper test thesis.",
        invalidating_conditions="Resolution source changes.",
    )


def _outcome_report(
    index: int,
    *,
    pending_count: int,
    resolved_count: int = 0,
) -> OutcomeTrackingReport:
    observations = tuple(
        PaperForecastEvidenceObservation(
            observed_at=GENERATED_AT
            - timedelta(seconds=index * 120, microseconds=offset),
            source_packet_id=f"outcome-pkt-{index}-{offset}",
            condition_id=f"0xoutcome{index}{offset}",
            token_id=f"outcome-token-{index}-{offset}",
            market_slug=f"outcome-market-{index}-{offset}",
            strategy_type="market_quality",
            risk_tags=("liquidity",),
            predicted_probability=Decimal("0.6000"),
            actual_outcome_value=Decimal("1"),
        )
        for offset in range(resolved_count)
    )
    forecast_evidence_report = (
        build_paper_forecast_evidence_report(
            observations,
            config=PaperForecastEvidenceConfig(config_version="outcome-tracker-v1"),
            generated_at=GENERATED_AT - timedelta(seconds=index * 120),
        )
        if observations
        else None
    )
    return OutcomeTrackingReport(
        generated_at=GENERATED_AT - timedelta(seconds=index * 120),
        config_version="outcome-tracker-v1",
        total_markets_checked=pending_count + resolved_count,
        resolved_count=resolved_count,
        pending_count=pending_count,
        observations=observations,
        forecast_evidence_report=forecast_evidence_report,
    )


def _strategy_audit_report(
    index: int,
    *,
    status: str,
) -> PaperStrategyRiskAuditReport:
    gate_status, pass_count, fail_count, incomplete_count = {
        "audit_ready": ("pass", 6, 0, 0),
        "insufficient_evidence": ("incomplete", 0, 0, 6),
        "blocked_by_risk": ("fail", 0, 6, 0),
    }[status]
    return PaperStrategyRiskAuditReport(
        generated_at=GENERATED_AT + timedelta(minutes=index, seconds=45),
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=6,
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=(
            PaperStrategyRiskAuditGateResult(
                "paper_history",
                gate_status,
                "paper history gate",
                observed_value="cycle_count=2",
                threshold="min_cycle_count=1",
            ),
            PaperStrategyRiskAuditGateResult(
                "settlement_evidence",
                gate_status,
                "settlement evidence gate",
                observed_value=2,
                threshold=1,
            ),
            PaperStrategyRiskAuditGateResult(
                "forecast_quality",
                gate_status,
                "forecast quality gate",
                observed_value="forecast_probability_quality_status=pass",
                threshold="forecast_probability_quality_status=pass",
            ),
            PaperStrategyRiskAuditGateResult(
                "cost_discipline",
                gate_status,
                "cost discipline gate",
                observed_value="trade_count=2",
                threshold="min_cost_audit_trade_count=1",
            ),
            PaperStrategyRiskAuditGateResult(
                "nav_drawdown",
                gate_status,
                "nav drawdown gate",
                observed_value=Decimal("0.000000"),
                threshold=Decimal("0.050000"),
            ),
            PaperStrategyRiskAuditGateResult(
                "open_exposure",
                gate_status,
                "open exposure gate",
                observed_value="open_position_count=0",
                threshold="max_no_exit_depth_count=0",
            ),
        ),
    )


def test_runner_reads_empty_required_logs_without_mutating_inputs(tmp_path):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    for path in (cycle_log, trade_log, nav_log):
        path.write_text("", encoding="utf-8")
    before = {path: path.read_bytes() for path in (cycle_log, trade_log, nav_log)}

    report = run_local_observability_trends(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        outcome_log=None,
        strategy_audit_log=None,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, LocalObservabilityTrendsReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.strategy_evidence_trend.snapshot_report_count == 0
    assert report.strategy_evidence_trend.latest_status is None
    assert report.outcome_freshness.status == "empty_outcome_history"
    assert report.outcome_freshness.outcome_report_count == 0
    assert report.nav_risk_trend.status == "empty_nav_risk_history"
    assert report.nav_risk_trend.nav_risk_report_count == 0
    assert report.paper_trade_cost_trend.status == "empty_cost_audit_history"
    assert report.paper_trade_cost_trend.cost_audit_report_count == 0
    assert {path: path.read_bytes() for path in before} == before


def test_runner_builds_append_order_prefix_trends_from_local_logs(tmp_path):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    outcome_log = tmp_path / "outcomes.jsonl"
    PaperStrategyCycleLog(cycle_log).append(_cycle_report(1))
    PaperStrategyCycleLog(cycle_log).append(_cycle_report(2))
    PaperTradeJournal(trade_log).append(
        _trade_record(1, cost_adjusted_edge=Decimal("0.040000")),
    )
    PaperTradeJournal(trade_log).append(
        _trade_record(2, cost_adjusted_edge=Decimal("-0.010000")),
    )
    PaperNavLog(nav_log).append(_nav_snapshot(1, exit_nav=Decimal("10000")))
    PaperNavLog(nav_log).append(_nav_snapshot(2, exit_nav=Decimal("9900")))
    OutcomeTrackingLog(outcome_log).append(_outcome_report(1, pending_count=1))
    OutcomeTrackingLog(outcome_log).append(_outcome_report(2, pending_count=1))
    before = {
        path: path.read_bytes()
        for path in (cycle_log, trade_log, nav_log, outcome_log)
    }

    report = run_local_observability_trends(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        outcome_log=outcome_log,
        strategy_audit_log=None,
        config=_config(outcome_stale_after_seconds=60),
        generated_at=GENERATED_AT,
    )

    assert report.strategy_evidence_trend.snapshot_report_count == 2
    assert report.strategy_evidence_trend.latest_status == "local_risk_flags"
    assert "negative_cost_adjusted_edges" in (
        report.strategy_evidence_trend.latest_evidence_gap_names
    )
    assert report.strategy_evidence_trend.consecutive_local_risk_flags_count == 1
    assert report.outcome_freshness.outcome_report_count == 2
    assert report.outcome_freshness.latest_report_age_seconds == 240
    assert report.outcome_freshness.status == "latest_outcomes_stale"
    assert report.nav_risk_trend.nav_risk_report_count == 2
    assert report.nav_risk_trend.latest_exit_nav == Decimal("9900")
    assert report.nav_risk_trend.worst_observed_max_drawdown_pct == Decimal("0.010000")
    assert report.paper_trade_cost_trend.cost_audit_report_count == 2
    assert report.paper_trade_cost_trend.latest_negative_cost_adjusted_edge_count == 1
    assert report.paper_trade_cost_trend.status == "latest_negative_cost_adjusted_edges"
    assert report.paper_trade_cost_trend.consecutive_negative_cost_adjusted_edge_count == 1
    assert {path: path.read_bytes() for path in before} == before


def test_runner_preserves_trade_journal_append_order_for_cost_trend_prefixes(
    tmp_path,
):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    cycle_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")
    later_negative = _trade_record(2, cost_adjusted_edge=Decimal("-0.010000"))
    earlier_positive = _trade_record(1, cost_adjusted_edge=Decimal("0.040000"))
    assert later_negative.decision_timestamp_utc > earlier_positive.decision_timestamp_utc
    PaperTradeJournal(trade_log).append(later_negative)
    PaperTradeJournal(trade_log).append(earlier_positive)
    before = {path: path.read_bytes() for path in (cycle_log, trade_log, nav_log)}

    report = run_local_observability_trends(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        outcome_log=None,
        strategy_audit_log=None,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    cost_trend = report.paper_trade_cost_trend
    status_counts = {row.status: row.status_count for row in cost_trend.status_rows}
    assert cost_trend.cost_audit_report_count == 2
    assert cost_trend.latest_trade_count == 2
    assert cost_trend.latest_negative_cost_adjusted_edge_count == 1
    assert cost_trend.status == "latest_negative_cost_adjusted_edges"
    # Sorting by trade timestamp first would make the first prefix cost-observed.
    assert cost_trend.consecutive_negative_cost_adjusted_edge_count == 2
    assert status_counts["latest_negative_cost_adjusted_edges"] == 2
    assert status_counts["latest_cost_observed"] == 0
    assert {path: path.read_bytes() for path in before} == before


def test_runner_uses_supplied_strategy_audit_log_in_prefix_evidence_trend(tmp_path):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    outcome_log = tmp_path / "outcomes.jsonl"
    strategy_audit_log = tmp_path / "strategy-audits.jsonl"
    PaperStrategyCycleLog(cycle_log).append(_cycle_report(1))
    PaperStrategyCycleLog(cycle_log).append(_cycle_report(2))
    PaperTradeJournal(trade_log).append(
        _trade_record(1, cost_adjusted_edge=Decimal("0.040000")),
    )
    PaperTradeJournal(trade_log).append(
        _trade_record(2, cost_adjusted_edge=Decimal("0.030000")),
    )
    PaperNavLog(nav_log).append(_nav_snapshot(1, exit_nav=Decimal("10000")))
    PaperNavLog(nav_log).append(_nav_snapshot(2, exit_nav=Decimal("10000")))
    OutcomeTrackingLog(outcome_log).append(
        _outcome_report(1, pending_count=0, resolved_count=1),
    )
    OutcomeTrackingLog(outcome_log).append(
        _outcome_report(2, pending_count=0, resolved_count=1),
    )
    PaperStrategyRiskAuditLog(strategy_audit_log).append(
        _strategy_audit_report(1, status="insufficient_evidence"),
    )
    PaperStrategyRiskAuditLog(strategy_audit_log).append(
        _strategy_audit_report(2, status="audit_ready"),
    )
    before = {
        path: path.read_bytes()
        for path in (cycle_log, trade_log, nav_log, outcome_log, strategy_audit_log)
    }

    omitted_history = run_local_observability_trends(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        outcome_log=outcome_log,
        strategy_audit_log=None,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    supplied_history = run_local_observability_trends(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        outcome_log=outcome_log,
        strategy_audit_log=strategy_audit_log,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    omitted_trend = omitted_history.strategy_evidence_trend
    supplied_trend = supplied_history.strategy_evidence_trend
    omitted_gap_counts = {
        row.evidence_gap_name: row.gap_count for row in omitted_trend.gap_rows
    }
    supplied_gap_counts = {
        row.evidence_gap_name: row.gap_count for row in supplied_trend.gap_rows
    }
    supplied_status_counts = {
        row.snapshot_status: row.snapshot_count for row in supplied_trend.status_rows
    }

    assert omitted_trend.snapshot_report_count == 2
    assert omitted_trend.latest_status == "local_evidence_gaps"
    assert omitted_trend.latest_evidence_gap_names == ("missing_strategy_audit_history",)
    assert omitted_trend.consecutive_non_observed_count == 2
    assert omitted_gap_counts["missing_strategy_audit_history"] == 2

    assert supplied_trend.snapshot_report_count == 2
    assert supplied_trend.latest_status == "local_evidence_observed"
    assert supplied_trend.latest_evidence_gap_names == ()
    assert supplied_trend.consecutive_non_observed_count == 0
    assert supplied_status_counts["local_evidence_gaps"] == 1
    assert supplied_status_counts["local_evidence_observed"] == 1
    assert supplied_gap_counts["missing_strategy_audit_history"] == 0
    assert supplied_gap_counts["latest_strategy_audit_not_ready"] == 1
    assert {path: path.read_bytes() for path in before} == before


def test_runner_uses_strategy_audit_append_order_not_max_generated_at_for_evidence_trend(
    tmp_path,
):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    outcome_log = tmp_path / "outcomes.jsonl"
    strategy_audit_log = tmp_path / "strategy-audits.jsonl"
    PaperStrategyCycleLog(cycle_log).append(_cycle_report(1))
    PaperStrategyCycleLog(cycle_log).append(_cycle_report(2))
    PaperTradeJournal(trade_log).append(
        _trade_record(1, cost_adjusted_edge=Decimal("0.040000")),
    )
    PaperTradeJournal(trade_log).append(
        _trade_record(2, cost_adjusted_edge=Decimal("0.030000")),
    )
    PaperNavLog(nav_log).append(_nav_snapshot(1, exit_nav=Decimal("10000")))
    PaperNavLog(nav_log).append(_nav_snapshot(2, exit_nav=Decimal("10000")))
    OutcomeTrackingLog(outcome_log).append(
        _outcome_report(1, pending_count=0, resolved_count=1),
    )
    OutcomeTrackingLog(outcome_log).append(
        _outcome_report(2, pending_count=0, resolved_count=1),
    )
    max_timestamp_ready_audit = _strategy_audit_report(2, status="audit_ready")
    appended_latest_non_ready_audit = _strategy_audit_report(
        1,
        status="insufficient_evidence",
    )
    assert (
        max_timestamp_ready_audit.generated_at
        > appended_latest_non_ready_audit.generated_at
    )
    PaperStrategyRiskAuditLog(strategy_audit_log).append(max_timestamp_ready_audit)
    PaperStrategyRiskAuditLog(strategy_audit_log).append(
        appended_latest_non_ready_audit,
    )
    before = {
        path: path.read_bytes()
        for path in (cycle_log, trade_log, nav_log, outcome_log, strategy_audit_log)
    }

    report = run_local_observability_trends(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        outcome_log=outcome_log,
        strategy_audit_log=strategy_audit_log,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    trend = report.strategy_evidence_trend
    status_counts = {row.snapshot_status: row.snapshot_count for row in trend.status_rows}
    gap_counts = {row.evidence_gap_name: row.gap_count for row in trend.gap_rows}

    assert trend.snapshot_report_count == 2
    assert trend.latest_status == "local_evidence_gaps"
    assert trend.latest_evidence_gap_names == ("latest_strategy_audit_not_ready",)
    assert trend.consecutive_non_observed_count == 1
    assert status_counts["local_evidence_observed"] == 1
    assert status_counts["local_evidence_gaps"] == 1
    assert gap_counts["latest_strategy_audit_not_ready"] == 1
    assert gap_counts["missing_strategy_audit_history"] == 0
    assert {path: path.read_bytes() for path in before} == before


def test_runner_rejects_invalid_config_and_missing_required_logs(tmp_path):
    cycle_log = tmp_path / "missing-cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    trade_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="LocalObservabilityTrendsConfig"):
        run_local_observability_trends(
            cycle_log=cycle_log,
            trade_log=trade_log,
            nav_log=nav_log,
            outcome_log=None,
            strategy_audit_log=None,
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(FileNotFoundError):
        run_local_observability_trends(
            cycle_log=cycle_log,
            trade_log=trade_log,
            nav_log=nav_log,
            outcome_log=None,
            strategy_audit_log=None,
            config=_config(),
            generated_at=GENERATED_AT,
        )

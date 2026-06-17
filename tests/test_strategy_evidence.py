from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.nav_risk_metrics import PaperNavRiskMetricsReport
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport
from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport
from polymarket_alpha_lab.performance_summary import PerformanceSummary
from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    build_paper_strategy_risk_audit_history_report,
)
from polymarket_alpha_lab.strategy_evidence import (
    PaperStrategyEvidenceSnapshotConfig,
    PaperStrategyEvidenceSnapshotReport,
    build_paper_strategy_evidence_snapshot_report,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)


GENERATED_AT = datetime(2026, 6, 17, 16, 0, tzinfo=UTC)
ALL_GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
)
DEFAULT = object()


def _config(**overrides):
    values = {"config_version": "strategy-evidence-snapshot-v0"}
    values.update(overrides)
    return PaperStrategyEvidenceSnapshotConfig(**values)


def _performance_summary(**overrides) -> PerformanceSummary:
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "performance-summary-v1",
        "cycle_count": 12,
        "total_scan_market_count": 240,
        "total_snapshot_ready_count": 48,
        "total_cost_aware_report_count": 48,
        "paper_trade_count": 18,
        "last_exit_nav": Decimal("10075.0000"),
        "last_starting_cash": Decimal("10000.0000"),
        "total_realized_pnl": Decimal("25.0000"),
        "nav_snapshot_count": 5,
        "first_cycle_at": datetime(2026, 6, 1, tzinfo=UTC),
        "last_cycle_at": datetime(2026, 6, 17, tzinfo=UTC),
    }
    values.update(overrides)
    return PerformanceSummary(**values)


def _nav_risk(**overrides) -> PaperNavRiskMetricsReport:
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "nav-risk-metrics-v0",
        "nav_snapshot_count": 5,
        "first_marked_at": datetime(2026, 6, 1, tzinfo=UTC),
        "last_marked_at": datetime(2026, 6, 17, tzinfo=UTC),
        "latest_exit_nav": Decimal("10075.0000"),
        "latest_starting_cash": Decimal("10000.0000"),
        "latest_cash_balance": Decimal("9975.0000"),
        "latest_total_cost_basis": Decimal("100.0000"),
        "latest_unrealized_exit_pnl": Decimal("50.0000"),
        "peak_exit_nav": Decimal("10100.0000"),
        "trough_exit_nav": Decimal("9900.0000"),
        "cumulative_return": Decimal("0.007500"),
        "max_drawdown": Decimal("200.0000"),
        "max_drawdown_pct": Decimal("0.019802"),
        "worst_nav_delta": Decimal("-100.0000"),
        "nav_return_volatility": Decimal("0.010000"),
        "pending_notional": Decimal("100.0000"),
        "open_position_count": 1,
        "fully_executable_count": 1,
        "partially_executable_count": 0,
        "no_exit_depth_count": 0,
        "largest_market_exposure_value": Decimal("100.0000"),
        "largest_market_exposure_share": Decimal("0.009926"),
        "exposure_rows": (),
    }
    values.update(overrides)
    return PaperNavRiskMetricsReport(**values)


def _cost_audit(**overrides) -> PaperTradeCostAuditReport:
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "paper-trade-cost-audit-v0",
        "trade_count": 18,
        "total_filled_size": Decimal("1800.0000"),
        "total_requested_size": Decimal("1800.0000"),
        "fill_rate": Decimal("1.000000"),
        "mean_theoretical_edge": Decimal("0.060000"),
        "mean_cost_adjusted_edge": Decimal("0.040000"),
        "mean_edge_cost_drag": Decimal("0.020000"),
        "total_edge_cost_drag": Decimal("36.000000"),
        "mean_research_slippage": Decimal("0.004000"),
        "mean_fill_slippage": Decimal("0.006000"),
        "partial_fill_count": 0,
        "negative_cost_adjusted_edge_count": 0,
        "largest_single_trade_cost_drag": Decimal("2.000000"),
    }
    values.update(overrides)
    return PaperTradeCostAuditReport(**values)


def _outcome_report(**overrides) -> OutcomeTrackingReport:
    total_markets_checked = overrides.pop("total_markets_checked", 18)
    resolved_count = overrides.pop("resolved_count", 10)
    pending_count = overrides.pop("pending_count", total_markets_checked - resolved_count)
    observations = tuple(_observation(index) for index in range(resolved_count))
    evidence_report = (
        build_paper_forecast_evidence_report(
            observations,
            config=PaperForecastEvidenceConfig(
                config_version="strategy-evidence-test",
                min_probability_observations=resolved_count,
                min_edge_observations=0,
                max_mean_probability_loss=Decimal("0.3000"),
                max_bucket_error=Decimal("0.5000"),
            ),
            generated_at=GENERATED_AT,
        )
        if observations
        else None
    )
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "outcome-tracker-v1",
        "total_markets_checked": total_markets_checked,
        "resolved_count": resolved_count,
        "pending_count": pending_count,
        "observations": observations,
        "forecast_evidence_report": evidence_report,
    }
    values.update(overrides)
    return OutcomeTrackingReport(**values)


def _observation(index: int) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=GENERATED_AT,
        source_packet_id=f"packet-{index}",
        condition_id=f"condition-{index}",
        token_id=f"token-{index}",
        market_slug=f"market-{index}",
        strategy_type="paper",
        risk_tags=("paper",),
        predicted_probability=Decimal("0.6000"),
        actual_outcome_value=Decimal("1"),
    )


def _strategy_audit_report(
    status: str = "audit_ready",
    *,
    generated_at: datetime = GENERATED_AT,
) -> PaperStrategyRiskAuditReport:
    status_map = {
        "audit_ready": ("pass", 6, 0, 0),
        "insufficient_evidence": ("incomplete", 0, 0, 6),
        "blocked_by_risk": ("fail", 0, 6, 0),
    }
    gate_status, pass_count, fail_count, incomplete_count = status_map[status]
    return PaperStrategyRiskAuditReport(
        generated_at=generated_at,
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=6,
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=tuple(
            PaperStrategyRiskAuditGateResult(gate_name, gate_status, "observed")
            for gate_name in ALL_GATE_NAMES
        ),
    )


def _audit_history(*statuses: str):
    reports = tuple(
        _strategy_audit_report(
            status,
            generated_at=datetime(2026, 6, 17, 12 + index, tzinfo=UTC),
        )
        for index, status in enumerate(statuses)
    )
    return build_paper_strategy_risk_audit_history_report(
        reports,
        config=PaperStrategyRiskAuditHistoryConfig(
            config_version="strategy-audit-history-v0",
        ),
        generated_at=GENERATED_AT,
    )


def _report(
    *,
    performance_summary=DEFAULT,
    nav_risk_report=DEFAULT,
    cost_audit_report=DEFAULT,
    outcome_report=DEFAULT,
    audit_history_report=DEFAULT,
    config=DEFAULT,
) -> PaperStrategyEvidenceSnapshotReport:
    return build_paper_strategy_evidence_snapshot_report(
        performance_summary=(
            _performance_summary()
            if performance_summary is DEFAULT
            else performance_summary
        ),
        nav_risk_report=_nav_risk() if nav_risk_report is DEFAULT else nav_risk_report,
        cost_audit_report=(
            _cost_audit()
            if cost_audit_report is DEFAULT
            else cost_audit_report
        ),
        outcome_report=_outcome_report() if outcome_report is DEFAULT else outcome_report,
        audit_history_report=(
            _audit_history("audit_ready")
            if audit_history_report is DEFAULT
            else audit_history_report
        ),
        config=_config() if config is DEFAULT else config,
        generated_at=GENERATED_AT,
    )


def test_strategy_evidence_snapshot_observes_complete_local_evidence():
    report = _report()

    assert isinstance(report, PaperStrategyEvidenceSnapshotReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-evidence-snapshot-v0"
    assert report.status == "local_evidence_observed"
    assert report.cycle_count == 12
    assert report.paper_trade_count == 18
    assert report.nav_snapshot_count == 5
    assert report.outcome_checked_count == 18
    assert report.outcome_resolved_count == 10
    assert report.outcome_pending_count == 8
    assert report.outcome_unresolved_count == 8
    assert report.audit_report_count == 1
    assert report.latest_audit_status == "audit_ready"
    assert report.negative_cost_adjusted_edge_count == 0
    assert report.unexecutable_open_position_count == 0
    assert report.evidence_gap_names == ()


def test_strategy_evidence_snapshot_reports_missing_inputs_in_deterministic_order():
    report = _report(
        performance_summary=_performance_summary(
            cycle_count=0,
            paper_trade_count=0,
            nav_snapshot_count=0,
            first_cycle_at=None,
            last_cycle_at=None,
        ),
        nav_risk_report=_nav_risk(
            nav_snapshot_count=0,
            first_marked_at=None,
            last_marked_at=None,
            latest_exit_nav=None,
            latest_starting_cash=None,
            latest_cash_balance=None,
            latest_total_cost_basis=None,
            latest_unrealized_exit_pnl=None,
            peak_exit_nav=None,
            trough_exit_nav=None,
            cumulative_return=None,
            max_drawdown=None,
            max_drawdown_pct=None,
            worst_nav_delta=None,
            nav_return_volatility=None,
            pending_notional=None,
            open_position_count=0,
            largest_market_exposure_value=None,
            largest_market_exposure_share=None,
        ),
        cost_audit_report=_cost_audit(
            trade_count=0,
            total_filled_size=Decimal("0"),
            total_requested_size=Decimal("0"),
            fill_rate=None,
            mean_theoretical_edge=None,
            mean_cost_adjusted_edge=None,
            mean_edge_cost_drag=None,
            total_edge_cost_drag=None,
            mean_research_slippage=None,
            mean_fill_slippage=None,
            largest_single_trade_cost_drag=None,
        ),
        outcome_report=None,
        audit_history_report=None,
    )

    assert report.status == "no_local_evidence"
    assert report.outcome_checked_count is None
    assert report.outcome_resolved_count is None
    assert report.outcome_pending_count is None
    assert report.outcome_unresolved_count is None
    assert report.audit_report_count is None
    assert report.latest_audit_status is None
    assert report.evidence_gap_names == (
        "missing_cycles",
        "missing_paper_trades",
        "missing_nav_snapshots",
        "missing_outcome_evidence",
        "missing_strategy_audit_history",
    )


def test_strategy_evidence_snapshot_marks_not_ready_audit_as_gap():
    report = _report(audit_history_report=_audit_history("insufficient_evidence"))

    assert report.status == "local_evidence_gaps"
    assert report.audit_report_count == 1
    assert report.latest_audit_status == "insufficient_evidence"
    assert report.evidence_gap_names == ("latest_strategy_audit_not_ready",)


def test_strategy_evidence_snapshot_requires_resolved_outcome_evidence():
    report = _report(outcome_report=_outcome_report(resolved_count=0))

    assert report.status == "local_evidence_gaps"
    assert report.outcome_checked_count == 18
    assert report.outcome_resolved_count == 0
    assert report.outcome_pending_count == 18
    assert report.evidence_gap_names == ("missing_outcome_evidence",)


def test_strategy_evidence_snapshot_ignores_pending_only_outcomes_for_any_evidence():
    report = _report(
        performance_summary=_performance_summary(
            cycle_count=0,
            paper_trade_count=0,
            nav_snapshot_count=0,
            first_cycle_at=None,
            last_cycle_at=None,
        ),
        nav_risk_report=_nav_risk(
            nav_snapshot_count=0,
            first_marked_at=None,
            last_marked_at=None,
            latest_exit_nav=None,
            latest_starting_cash=None,
            latest_cash_balance=None,
            latest_total_cost_basis=None,
            latest_unrealized_exit_pnl=None,
            peak_exit_nav=None,
            trough_exit_nav=None,
            cumulative_return=None,
            max_drawdown=None,
            max_drawdown_pct=None,
            worst_nav_delta=None,
            nav_return_volatility=None,
            pending_notional=None,
            open_position_count=0,
            largest_market_exposure_value=None,
            largest_market_exposure_share=None,
        ),
        cost_audit_report=_cost_audit(
            trade_count=0,
            total_filled_size=Decimal("0"),
            total_requested_size=Decimal("0"),
            fill_rate=None,
            mean_theoretical_edge=None,
            mean_cost_adjusted_edge=None,
            mean_edge_cost_drag=None,
            total_edge_cost_drag=None,
            mean_research_slippage=None,
            mean_fill_slippage=None,
            largest_single_trade_cost_drag=None,
        ),
        outcome_report=_outcome_report(resolved_count=0),
        audit_history_report=None,
    )

    assert report.status == "no_local_evidence"
    assert report.outcome_checked_count == 18
    assert report.outcome_resolved_count == 0
    assert report.evidence_gap_names == (
        "missing_cycles",
        "missing_paper_trades",
        "missing_nav_snapshots",
        "missing_outcome_evidence",
        "missing_strategy_audit_history",
    )


def test_strategy_evidence_snapshot_marks_risk_flags_with_precedence():
    report = _report(
        cost_audit_report=_cost_audit(negative_cost_adjusted_edge_count=2),
        nav_risk_report=_nav_risk(
            open_position_count=3,
            fully_executable_count=1,
            partially_executable_count=1,
            no_exit_depth_count=1,
        ),
        audit_history_report=_audit_history("insufficient_evidence"),
    )

    assert report.status == "local_risk_flags"
    assert report.negative_cost_adjusted_edge_count == 2
    assert report.unexecutable_open_position_count == 1
    assert report.evidence_gap_names == (
        "latest_strategy_audit_not_ready",
        "negative_cost_adjusted_edges",
        "unexecutable_open_positions",
    )


def test_strategy_evidence_snapshot_rejects_invalid_builder_inputs():
    with pytest.raises(ValueError, match="config"):
        build_paper_strategy_evidence_snapshot_report(
            performance_summary=_performance_summary(),
            nav_risk_report=_nav_risk(),
            cost_audit_report=_cost_audit(),
            outcome_report=_outcome_report(),
            audit_history_report=_audit_history("audit_ready"),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_strategy_evidence_snapshot_report(
            performance_summary=_performance_summary(),
            nav_risk_report=_nav_risk(),
            cost_audit_report=_cost_audit(),
            outcome_report=_outcome_report(),
            audit_history_report=_audit_history("audit_ready"),
            config=_config(),
            generated_at="now",
        )
    with pytest.raises(ValueError, match="performance_summary"):
        build_paper_strategy_evidence_snapshot_report(
            performance_summary={},
            nav_risk_report=_nav_risk(),
            cost_audit_report=_cost_audit(),
            outcome_report=_outcome_report(),
            audit_history_report=_audit_history("audit_ready"),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="nav_risk_report"):
        build_paper_strategy_evidence_snapshot_report(
            performance_summary=_performance_summary(),
            nav_risk_report="nav",
            cost_audit_report=_cost_audit(),
            outcome_report=_outcome_report(),
            audit_history_report=_audit_history("audit_ready"),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="cost_audit_report"):
        build_paper_strategy_evidence_snapshot_report(
            performance_summary=_performance_summary(),
            nav_risk_report=_nav_risk(),
            cost_audit_report=object(),
            outcome_report=_outcome_report(),
            audit_history_report=_audit_history("audit_ready"),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="outcome_report"):
        build_paper_strategy_evidence_snapshot_report(
            performance_summary=_performance_summary(),
            nav_risk_report=_nav_risk(),
            cost_audit_report=_cost_audit(),
            outcome_report=object(),
            audit_history_report=_audit_history("audit_ready"),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="outcome_report"):
        build_paper_strategy_evidence_snapshot_report(
            performance_summary=_performance_summary(),
            nav_risk_report=_nav_risk(),
            cost_audit_report=_cost_audit(),
            outcome_report=_nav_risk(),
            audit_history_report=_audit_history("audit_ready"),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="audit_history_report"):
        build_paper_strategy_evidence_snapshot_report(
            performance_summary=_performance_summary(),
            nav_risk_report=_nav_risk(),
            cost_audit_report=_cost_audit(),
            outcome_report=_outcome_report(),
            audit_history_report={"status": "audit_ready"},
            config=_config(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize(
    ("input_name", "mutator", "expected"),
    (
        (
            "performance_summary",
            lambda report: object.__setattr__(report, "paper_only", False),
            "performance_summary paper_only",
        ),
        (
            "nav_risk_report",
            lambda report: object.__setattr__(report, "report_only", False),
            "nav_risk_report report_only",
        ),
        (
            "cost_audit_report",
            lambda report: object.__setattr__(report, "paper_only", False),
            "cost_audit_report paper_only",
        ),
        (
            "outcome_report",
            lambda report: object.__setattr__(report, "report_only", False),
            "outcome_report report_only",
        ),
        (
            "audit_history_report",
            lambda report: object.__setattr__(report, "paper_only", False),
            "audit_history_report paper_only",
        ),
    ),
)
def test_strategy_evidence_snapshot_rejects_mutated_non_paper_inputs(
    input_name,
    mutator,
    expected,
):
    inputs = {
        "performance_summary": _performance_summary(),
        "nav_risk_report": _nav_risk(),
        "cost_audit_report": _cost_audit(),
        "outcome_report": _outcome_report(),
        "audit_history_report": _audit_history("audit_ready"),
    }
    mutator(inputs[input_name])

    with pytest.raises(ValueError, match=expected):
        build_paper_strategy_evidence_snapshot_report(
            **inputs,
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_strategy_evidence_snapshot_dataclasses_are_frozen_and_revalidate_flags():
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.status = "local_risk_flags"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version="")
    with pytest.raises(ValueError, match="status"):
        replace(report, status="unknown")
    with pytest.raises(ValueError, match="evidence_gap_names"):
        replace(report, evidence_gap_names=("unknown_gap",))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="no_local_evidence")
    with pytest.raises(ValueError, match="status"):
        PaperStrategyEvidenceSnapshotReport(
            generated_at=GENERATED_AT,
            config_version="strategy-evidence-snapshot-v0",
            status="local_evidence_observed",
            cycle_count=0,
            paper_trade_count=0,
            nav_snapshot_count=0,
            outcome_checked_count=None,
            outcome_pending_count=None,
            outcome_resolved_count=None,
            outcome_unresolved_count=None,
            audit_report_count=None,
            latest_audit_status=None,
            negative_cost_adjusted_edge_count=0,
            unexecutable_open_position_count=0,
            evidence_gap_names=(),
        )

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceReport,
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.nav_risk_metrics import PaperNavRiskMetricsReport
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport
from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport
from polymarket_alpha_lab.performance_summary import PerformanceSummary
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditConfig,
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
    build_paper_strategy_risk_audit_report,
)


GENERATED_AT = datetime(2026, 6, 16, 20, 0, tzinfo=UTC)


def _config(**overrides):
    values = {"config_version": "strategy-risk-audit-v0"}
    values.update(overrides)
    return PaperStrategyRiskAuditConfig(**values)


def _history(**overrides) -> PerformanceSummary:
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "performance-summary-v1",
        "cycle_count": 25,
        "total_scan_market_count": 500,
        "total_snapshot_ready_count": 80,
        "total_cost_aware_report_count": 80,
        "paper_trade_count": 30,
        "last_exit_nav": Decimal("10050.0000"),
        "last_starting_cash": Decimal("10000.0000"),
        "total_realized_pnl": Decimal("0.0000"),
        "nav_snapshot_count": 8,
        "first_cycle_at": datetime(2026, 6, 1, tzinfo=UTC),
        "last_cycle_at": datetime(2026, 6, 16, tzinfo=UTC),
    }
    values.update(overrides)
    return PerformanceSummary(**values)


def _nav_risk(**overrides) -> PaperNavRiskMetricsReport:
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "nav-risk-metrics-v0",
        "nav_snapshot_count": 8,
        "first_marked_at": datetime(2026, 6, 1, tzinfo=UTC),
        "last_marked_at": datetime(2026, 6, 16, tzinfo=UTC),
        "latest_exit_nav": Decimal("10050.0000"),
        "latest_starting_cash": Decimal("10000.0000"),
        "latest_cash_balance": Decimal("9950.0000"),
        "latest_total_cost_basis": Decimal("100.0000"),
        "latest_unrealized_exit_pnl": Decimal("50.0000"),
        "peak_exit_nav": Decimal("10100.0000"),
        "trough_exit_nav": Decimal("9900.0000"),
        "cumulative_return": Decimal("0.005000"),
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
        "largest_market_exposure_share": Decimal("0.009950"),
        "exposure_rows": (),
    }
    values.update(overrides)
    return PaperNavRiskMetricsReport(**values)


def _outcomes(**overrides) -> OutcomeTrackingReport:
    resolved_count = overrides.pop("resolved_count", 12)
    total_markets_checked = overrides.pop("total_markets_checked", 30)
    observations = tuple(_observation(index) for index in range(resolved_count))
    evidence = (
        build_paper_forecast_evidence_report(
            observations,
            config=PaperForecastEvidenceConfig(
                config_version="strategy-risk-audit-test",
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
        "pending_count": total_markets_checked - resolved_count,
        "observations": observations,
        "forecast_evidence_report": evidence,
    }
    values.update(overrides)
    return OutcomeTrackingReport(**values)


def _cost_audit(**overrides) -> PaperTradeCostAuditReport:
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "paper-trade-cost-audit-v0",
        "trade_count": 30,
        "total_filled_size": Decimal("3000.0000"),
        "total_requested_size": Decimal("3000.0000"),
        "fill_rate": Decimal("1.000000"),
        "mean_theoretical_edge": Decimal("0.060000"),
        "mean_cost_adjusted_edge": Decimal("0.040000"),
        "mean_edge_cost_drag": Decimal("0.020000"),
        "total_edge_cost_drag": Decimal("60.000000"),
        "mean_research_slippage": Decimal("0.004000"),
        "mean_fill_slippage": Decimal("0.006000"),
        "partial_fill_count": 0,
        "negative_cost_adjusted_edge_count": 0,
        "largest_single_trade_cost_drag": Decimal("2.000000"),
    }
    values.update(overrides)
    return PaperTradeCostAuditReport(**values)


def _evidence(
    *,
    max_mean_probability_loss=Decimal("0.3000"),
    max_bucket_error=Decimal("0.5000"),
    min_probability_observations=12,
    observations=None,
) -> PaperForecastEvidenceReport:
    observation_values = (
        tuple(_observation(index) for index in range(12))
        if observations is None
        else observations
    )
    return build_paper_forecast_evidence_report(
        observation_values,
        config=PaperForecastEvidenceConfig(
            config_version="strategy-risk-audit-test",
            min_probability_observations=min_probability_observations,
            min_edge_observations=0,
            max_mean_probability_loss=max_mean_probability_loss,
            max_bucket_error=max_bucket_error,
        ),
        generated_at=GENERATED_AT,
    )


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


def _report(history=None, nav_risk=None, outcomes=None, cost_audit=None, config=None):
    return build_paper_strategy_risk_audit_report(
        performance_summary=history if history is not None else _history(),
        nav_risk_report=nav_risk if nav_risk is not None else _nav_risk(),
        outcome_report=outcomes,
        cost_audit_report=cost_audit,
        config=config if config is not None else _config(),
        generated_at=GENERATED_AT,
    )


def test_strategy_risk_audit_ready_when_all_gates_pass():
    report = _report(outcomes=_outcomes(), cost_audit=_cost_audit())

    assert isinstance(report, PaperStrategyRiskAuditReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-risk-audit-v0"
    assert report.status == "audit_ready"
    assert report.gate_count == 6
    assert report.pass_count == 6
    assert report.fail_count == 0
    assert report.incomplete_count == 0
    assert tuple(gate.gate_name for gate in report.gate_results) == (
        "paper_history",
        "settlement_evidence",
        "forecast_quality",
        "cost_discipline",
        "nav_drawdown",
        "open_exposure",
    )
    assert all(isinstance(gate, PaperStrategyRiskAuditGateResult) for gate in report.gate_results)


def test_strategy_risk_audit_marks_immature_history_as_insufficient_evidence():
    report = _report(
        history=_history(cycle_count=3, paper_trade_count=2, nav_snapshot_count=1),
        cost_audit=_cost_audit(),
        outcomes=None,
    )

    assert report.status == "insufficient_evidence"
    assert report.pass_count == 3
    assert report.fail_count == 0
    assert report.incomplete_count == 3
    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["paper_history"].status == "incomplete"
    assert gates["settlement_evidence"].status == "incomplete"
    assert gates["forecast_quality"].status == "incomplete"
    assert gates["paper_history"].observed_value == (
        "cycle_count=3; paper_trade_count=2; nav_snapshot_count=1"
    )


def test_strategy_risk_audit_marks_missing_cost_audit_as_incomplete():
    report = _report(outcomes=_outcomes(), cost_audit=None)

    assert report.status == "insufficient_evidence"
    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["cost_discipline"].status == "incomplete"
    assert gates["cost_discipline"].observed_value is None


def test_strategy_risk_audit_marks_thin_cost_audit_as_incomplete():
    report = _report(
        outcomes=_outcomes(),
        cost_audit=_cost_audit(trade_count=3),
        config=_config(min_cost_audit_trade_count=20),
    )

    assert report.status == "insufficient_evidence"
    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["cost_discipline"].status == "incomplete"
    assert gates["cost_discipline"].observed_value == (
        "trade_count=3; mean_edge_cost_drag=0.020000; "
        "negative_cost_adjusted_edge_count=0"
    )


def test_strategy_risk_audit_marks_unavailable_cost_drag_as_incomplete():
    report = _report(
        outcomes=_outcomes(),
        cost_audit=_cost_audit(mean_edge_cost_drag=None),
    )

    assert report.status == "insufficient_evidence"
    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["cost_discipline"].status == "incomplete"
    assert gates["cost_discipline"].observed_value == (
        "trade_count=30; mean_edge_cost_drag=None; "
        "negative_cost_adjusted_edge_count=0"
    )


def test_strategy_risk_audit_blocks_on_cost_discipline_failure():
    report = _report(
        outcomes=_outcomes(),
        cost_audit=_cost_audit(
            mean_edge_cost_drag=Decimal("0.080000"),
            negative_cost_adjusted_edge_count=2,
        ),
    )

    assert report.status == "blocked_by_risk"
    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["cost_discipline"].status == "fail"
    assert gates["cost_discipline"].observed_value == (
        "trade_count=30; mean_edge_cost_drag=0.080000; "
        "negative_cost_adjusted_edge_count=2"
    )


def test_strategy_risk_audit_blocks_on_cost_drag_failure_only():
    report = _report(
        outcomes=_outcomes(),
        cost_audit=_cost_audit(
            mean_edge_cost_drag=Decimal("0.080000"),
            negative_cost_adjusted_edge_count=0,
        ),
    )

    assert report.status == "blocked_by_risk"
    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["cost_discipline"].status == "fail"
    assert gates["cost_discipline"].observed_value == (
        "trade_count=30; mean_edge_cost_drag=0.080000; "
        "negative_cost_adjusted_edge_count=0"
    )


def test_strategy_risk_audit_blocks_on_negative_cost_adjusted_edges_only():
    report = _report(
        outcomes=_outcomes(),
        cost_audit=_cost_audit(
            mean_edge_cost_drag=Decimal("0.020000"),
            negative_cost_adjusted_edge_count=1,
        ),
    )

    assert report.status == "blocked_by_risk"
    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["cost_discipline"].status == "fail"
    assert gates["cost_discipline"].observed_value == (
        "trade_count=30; mean_edge_cost_drag=0.020000; "
        "negative_cost_adjusted_edge_count=1"
    )


def test_strategy_risk_audit_blocks_on_nav_drawdown_and_open_exposure():
    report = _report(
        nav_risk=_nav_risk(
            max_drawdown_pct=Decimal("0.080000"),
            no_exit_depth_count=2,
            largest_market_exposure_share=Decimal("0.350000"),
        ),
        outcomes=_outcomes(),
        cost_audit=_cost_audit(),
    )

    assert report.status == "blocked_by_risk"
    assert report.fail_count == 2
    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["nav_drawdown"].status == "fail"
    assert gates["open_exposure"].status == "fail"
    assert gates["nav_drawdown"].observed_value == Decimal("0.080000")
    assert gates["open_exposure"].observed_value == (
        "open_position_count=1; no_exit_depth_count=2; "
        "largest_market_exposure_share=0.350000"
    )


def test_strategy_risk_audit_blocks_on_forecast_quality_failure():
    poor_evidence = _evidence(
        max_mean_probability_loss=Decimal("0.0100"),
        max_bucket_error=Decimal("0.0100"),
    )
    report = _report(
        outcomes=_outcomes(forecast_evidence_report=poor_evidence),
        cost_audit=_cost_audit(),
    )

    assert report.status == "blocked_by_risk"
    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["forecast_quality"].status == "fail"
    assert gates["forecast_quality"].observed_value == (
        "forecast_probability_quality_status=fail; "
        "mean_probability_loss=0.1600; worst_bucket_error=0.4000; "
        "probability_observation_count=12"
    )


def test_strategy_risk_audit_marks_incomplete_forecast_quality_as_insufficient_evidence():
    thin_evidence = _evidence()
    report = _report(
        outcomes=_outcomes(forecast_evidence_report=thin_evidence),
        cost_audit=_cost_audit(),
        config=_config(min_forecast_probability_observation_count=20),
    )

    assert report.status == "insufficient_evidence"
    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["forecast_quality"].status == "incomplete"
    assert gates["forecast_quality"].observed_value == (
        "forecast_probability_quality_status=pass; "
        "mean_probability_loss=0.1600; worst_bucket_error=0.4000; "
        "probability_observation_count=12"
    )


def test_strategy_risk_audit_rejects_non_paper_forecast_evidence_report():
    evidence = _evidence()
    object.__setattr__(evidence, "paper_only", False)

    with pytest.raises(ValueError, match="forecast_evidence_report paper_only"):
        _report(outcomes=_outcomes(forecast_evidence_report=evidence))


@pytest.mark.parametrize(
    ("field_name", "bad_value", "expected"),
    (
        ("min_cost_audit_trade_count", -1, "min_cost_audit_trade_count"),
        ("min_cost_audit_trade_count", True, "min_cost_audit_trade_count"),
        (
            "max_negative_cost_adjusted_edge_count",
            -1,
            "max_negative_cost_adjusted_edge_count",
        ),
        (
            "max_negative_cost_adjusted_edge_count",
            True,
            "max_negative_cost_adjusted_edge_count",
        ),
        (
            "max_mean_edge_cost_drag",
            Decimal("-0.000001"),
            "max_mean_edge_cost_drag",
        ),
        ("max_mean_edge_cost_drag", "0.050000", "max_mean_edge_cost_drag"),
        (
            "max_mean_edge_cost_drag",
            Decimal("NaN"),
            "max_mean_edge_cost_drag",
        ),
    ),
)
def test_strategy_risk_audit_rejects_invalid_cost_gate_config(
    field_name,
    bad_value,
    expected,
):
    with pytest.raises(ValueError, match=expected):
        _config(**{field_name: bad_value})


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only"))
def test_strategy_risk_audit_rejects_non_report_only_cost_audit(flag_name):
    cost_audit = _cost_audit()
    object.__setattr__(cost_audit, flag_name, False)

    with pytest.raises(ValueError, match=f"cost_audit_report {flag_name}"):
        _report(outcomes=_outcomes(), cost_audit=cost_audit)


def test_strategy_risk_audit_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version="")
    with pytest.raises(ValueError, match="performance_summary"):
        build_paper_strategy_risk_audit_report(
            performance_summary=object(),
            nav_risk_report=_nav_risk(),
            outcome_report=None,
            cost_audit_report=_cost_audit(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="nav_risk_report"):
        build_paper_strategy_risk_audit_report(
            performance_summary=_history(),
            nav_risk_report=object(),
            outcome_report=None,
            cost_audit_report=_cost_audit(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="outcome_report"):
        build_paper_strategy_risk_audit_report(
            performance_summary=_history(),
            nav_risk_report=_nav_risk(),
            outcome_report=object(),
            cost_audit_report=_cost_audit(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="cost_audit_report"):
        build_paper_strategy_risk_audit_report(
            performance_summary=_history(),
            nav_risk_report=_nav_risk(),
            outcome_report=None,
            cost_audit_report=object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_strategy_risk_audit_report(
            performance_summary=_history(),
            nav_risk_report=_nav_risk(),
            outcome_report=None,
            cost_audit_report=_cost_audit(),
            config=_config(),
            generated_at="now",
        )


def test_strategy_risk_audit_dataclasses_are_frozen_and_revalidate_flags():
    report = _report(outcomes=_outcomes(), cost_audit=_cost_audit())

    with pytest.raises(FrozenInstanceError):
        report.status = "blocked_by_risk"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)


def test_strategy_risk_audit_report_revalidates_status_counts():
    report = _report(outcomes=_outcomes(), cost_audit=_cost_audit())

    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked_by_risk")
    with pytest.raises(ValueError, match="gate_count"):
        replace(report, gate_count=3)
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=3)
    with pytest.raises(ValueError, match="fail_count"):
        replace(report, fail_count=1)
    with pytest.raises(ValueError, match="incomplete_count"):
        replace(report, incomplete_count=1)

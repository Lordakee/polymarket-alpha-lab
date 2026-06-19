"""Pure paper-only adapters from gate reports to readiness signals."""

from __future__ import annotations

from decimal import Decimal

from polymarket_alpha_lab.calibration_gate import PaperCalibrationGateReport
from polymarket_alpha_lab.cost_health_gate import (
    PaperCostHealthGateReport,
    PaperCostHealthGateRow,
)
from polymarket_alpha_lab.exposure_gate import PaperExposureGateReport
from polymarket_alpha_lab.liquidity_gate import PaperLiquidityGateReport
from polymarket_alpha_lab.market_context_freshness import (
    PaperMarketContextFreshnessReport,
)
from polymarket_alpha_lab.paper_nav_liquidity_risk import PaperNavLiquidityRiskReport
from polymarket_alpha_lab.settlement_freshness_gate import (
    PaperSettlementFreshnessGateReport,
)
from polymarket_alpha_lab.strategy_readiness_state import (
    PaperStrategyReadinessSignal,
)


SEVERITY_BY_STATUS = {
    "blocked": 100,
    "watch": 50,
    "pass": 0,
}


def signals_from_calibration_gate_report(
    report: PaperCalibrationGateReport,
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if type(report) is not PaperCalibrationGateReport:
        raise ValueError("report must be a PaperCalibrationGateReport")
    _require_report_flags(report)
    status = _map_status(report.gate_status)
    return (
        PaperStrategyReadinessSignal(
            source_name="calibration_gate",
            status=status,
            reason_codes=report.reason_codes,
            severity=SEVERITY_BY_STATUS[status],
            observed_value=report.blocked_gate_count,
            threshold=0,
        ),
    )


def signals_from_cost_health_gate_report(
    report: PaperCostHealthGateReport,
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if type(report) is not PaperCostHealthGateReport:
        raise ValueError("report must be a PaperCostHealthGateReport")
    _require_report_flags(report)
    status = _map_cost_health_status(report.status)
    return (
        PaperStrategyReadinessSignal(
            source_name="cost_health_gate",
            status=status,
            reason_codes=_reason_codes_or_passed(
                report.reason_codes,
                "cost_health_gate_passed",
            ),
            severity=SEVERITY_BY_STATUS[status],
            observed_value=_gate_row_count(report.gate_rows, status),
            threshold=0,
        ),
    )


def signals_from_liquidity_gate_report(
    report: PaperLiquidityGateReport,
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if type(report) is not PaperLiquidityGateReport:
        raise ValueError("report must be a PaperLiquidityGateReport")
    _require_report_flags(report)
    status = _map_status(report.status)
    return (
        PaperStrategyReadinessSignal(
            source_name="liquidity_gate",
            status=status,
            reason_codes=report.reason_codes,
            severity=SEVERITY_BY_STATUS[status],
            observed_value=report.depth_ready_count,
            threshold=None,
        ),
    )


def signals_from_nav_liquidity_risk_report(
    report: PaperNavLiquidityRiskReport,
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if type(report) is not PaperNavLiquidityRiskReport:
        raise ValueError("report must be a PaperNavLiquidityRiskReport")
    _require_report_flags(report)
    status = _map_nav_liquidity_risk_status(report.status)
    return (
        PaperStrategyReadinessSignal(
            source_name="nav_liquidity_risk",
            status=status,
            reason_codes=_nav_liquidity_risk_reason_codes(report.status),
            severity=SEVERITY_BY_STATUS[status],
            observed_value=_nav_liquidity_risk_observed_value(report),
            threshold=None,
        ),
    )


def signals_from_exposure_gate_report(
    report: PaperExposureGateReport,
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if type(report) is not PaperExposureGateReport:
        raise ValueError("report must be a PaperExposureGateReport")
    _require_report_flags(report)
    status = _map_status(report.status)
    return (
        PaperStrategyReadinessSignal(
            source_name="exposure_gate",
            status=status,
            reason_codes=_reason_codes_or_passed(
                report.reason_codes,
                "exposure_gate_passed",
            ),
            severity=SEVERITY_BY_STATUS[status],
            observed_value=report.total_exposure,
            threshold=None,
        ),
    )


def signals_from_market_context_freshness_report(
    report: PaperMarketContextFreshnessReport,
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if type(report) is not PaperMarketContextFreshnessReport:
        raise ValueError("report must be a PaperMarketContextFreshnessReport")
    _require_report_flags(report)
    status = _map_status(report.status)
    return (
        PaperStrategyReadinessSignal(
            source_name="market_context_freshness",
            status=status,
            reason_codes=report.reason_codes,
            severity=SEVERITY_BY_STATUS[status],
            observed_value=_max_report_age_seconds(report),
            threshold=report.max_report_age_seconds,
        ),
    )


def signals_from_settlement_freshness_gate_report(
    report: PaperSettlementFreshnessGateReport,
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if type(report) is not PaperSettlementFreshnessGateReport:
        raise ValueError("report must be a PaperSettlementFreshnessGateReport")
    _require_report_flags(report)
    status = _map_settlement_status(report.status)
    return (
        PaperStrategyReadinessSignal(
            source_name="settlement_freshness_gate",
            status=status,
            reason_codes=_settlement_reason_codes(report, status=status),
            severity=SEVERITY_BY_STATUS[status],
            observed_value=report.block_count + report.watch_count,
            threshold=0,
        ),
    )


def build_paper_strategy_readiness_signals(
    *reports: (
        PaperCalibrationGateReport
        | PaperCostHealthGateReport
        | PaperLiquidityGateReport
        | PaperNavLiquidityRiskReport
        | PaperExposureGateReport
        | PaperMarketContextFreshnessReport
        | PaperSettlementFreshnessGateReport
    ),
) -> tuple[PaperStrategyReadinessSignal, ...]:
    signals: list[PaperStrategyReadinessSignal] = []
    for report in reports:
        signals.extend(_signals_from_report(report))
    return _order_signals(tuple(signals))


def _signals_from_report(
    report: object,
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if type(report) is PaperCalibrationGateReport:
        return signals_from_calibration_gate_report(report)
    if type(report) is PaperCostHealthGateReport:
        return signals_from_cost_health_gate_report(report)
    if type(report) is PaperLiquidityGateReport:
        return signals_from_liquidity_gate_report(report)
    if type(report) is PaperNavLiquidityRiskReport:
        return signals_from_nav_liquidity_risk_report(report)
    if type(report) is PaperExposureGateReport:
        return signals_from_exposure_gate_report(report)
    if type(report) is PaperMarketContextFreshnessReport:
        return signals_from_market_context_freshness_report(report)
    if type(report) is PaperSettlementFreshnessGateReport:
        return signals_from_settlement_freshness_gate_report(report)
    raise ValueError("reports must contain supported paper gate report values")


def _require_report_flags(report: object) -> None:
    if getattr(report, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(report, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(report, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _order_signals(
    signals: tuple[PaperStrategyReadinessSignal, ...],
) -> tuple[PaperStrategyReadinessSignal, ...]:
    return tuple(
        sorted(
            signals,
            key=lambda signal: (-signal.severity, signal.source_name),
        ),
    )


def _map_cost_health_status(status: str) -> str:
    if status == "paper_cost_health_blocked":
        return "blocked"
    if status == "paper_cost_health_watch":
        return "watch"
    if status == "paper_cost_health_pass":
        return "pass"
    raise ValueError("status must be a known cost health report status")


def _map_status(status: str) -> str:
    if status in ("blocked", "watch"):
        return status
    if status in ("pass", "passed"):
        return "pass"
    raise ValueError("status must be blocked, watch, pass, or passed")


def _map_nav_liquidity_risk_status(status: str) -> str:
    if status == "empty_nav_liquidity_risk_history":
        return "watch"
    if status == "latest_nav_liquidity_observed":
        return "pass"
    if status == "latest_nav_has_unexecutable_liquidity":
        return "blocked"
    return _map_status(status)


def _map_settlement_status(status: str) -> str:
    if status == "block":
        return "blocked"
    return _map_status(status)


def _reason_codes_or_passed(
    reason_codes: tuple[str, ...],
    passed_code: str,
) -> tuple[str, ...]:
    if reason_codes:
        return reason_codes
    return (passed_code,)


def _gate_row_count(rows: tuple[PaperCostHealthGateRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _settlement_reason_codes(
    report: PaperSettlementFreshnessGateReport,
    *,
    status: str,
) -> tuple[str, ...]:
    if status == "blocked":
        return _reason_codes_or_passed(
            report.block_reasons,
            "settlement_freshness_gate_passed",
        )
    if status == "watch":
        return _reason_codes_or_passed(
            report.watch_reasons,
            "settlement_freshness_gate_passed",
        )
    return _reason_codes_or_passed(
        (),
        "settlement_freshness_gate_passed",
    )


def _nav_liquidity_risk_reason_codes(status: str) -> tuple[str, ...]:
    readiness_status = _map_nav_liquidity_risk_status(status)
    if status == "empty_nav_liquidity_risk_history":
        return ("nav_liquidity_risk_history_empty",)
    if readiness_status == "blocked":
        return ("nav_liquidity_risk_unexecutable_liquidity",)
    if readiness_status == "watch":
        return ("nav_liquidity_risk_watch",)
    return ("nav_liquidity_risk_passed",)


def _nav_liquidity_risk_observed_value(
    report: PaperNavLiquidityRiskReport,
) -> Decimal | None:
    if report.latest_unexecutable_cost_basis_share is not None:
        return report.latest_unexecutable_cost_basis_share
    return report.latest_unfilled_open_size_share


def _max_report_age_seconds(
    report: PaperMarketContextFreshnessReport,
) -> Decimal | None:
    if not report.rows:
        return None
    return max(row.report_age_seconds for row in report.rows)


__all__ = (
    "build_paper_strategy_readiness_signals",
    "signals_from_calibration_gate_report",
    "signals_from_cost_health_gate_report",
    "signals_from_exposure_gate_report",
    "signals_from_liquidity_gate_report",
    "signals_from_market_context_freshness_report",
    "signals_from_nav_liquidity_risk_report",
    "signals_from_settlement_freshness_gate_report",
)

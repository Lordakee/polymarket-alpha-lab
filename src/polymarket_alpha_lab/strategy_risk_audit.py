from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polymarket_alpha_lab.nav_risk_metrics import PaperNavRiskMetricsReport
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport
from polymarket_alpha_lab.performance_summary import PerformanceSummary


__all__ = (
    "PaperStrategyRiskAuditConfig",
    "PaperStrategyRiskAuditGateResult",
    "PaperStrategyRiskAuditReport",
    "build_paper_strategy_risk_audit_report",
)


GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "nav_drawdown",
    "open_exposure",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
REPORT_STATUSES = (
    "audit_ready",
    "blocked_by_risk",
    "insufficient_evidence",
)
ZERO = Decimal("0")


@dataclass(frozen=True)
class PaperStrategyRiskAuditConfig:
    config_version: str
    min_cycle_count: int = 20
    min_paper_trade_count: int = 20
    min_nav_snapshot_count: int = 5
    min_resolved_count: int = 10
    max_nav_drawdown_pct: Decimal = Decimal("0.050000")
    max_largest_market_exposure_share: Decimal = Decimal("0.200000")
    max_no_exit_depth_count: int = 0

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_cycle_count",
            "min_paper_trade_count",
            "min_nav_snapshot_count",
            "min_resolved_count",
            "max_no_exit_depth_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "max_nav_drawdown_pct",
            "max_largest_market_exposure_share",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class PaperStrategyRiskAuditGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        _require_canonical_string("gate_name", self.gate_name)
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known gate")
        _require_canonical_string("status", self.status)
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known gate status")
        _require_canonical_string("message", self.message)
        _require_audit_value("observed_value", self.observed_value)
        _require_audit_value("threshold", self.threshold)


@dataclass(frozen=True)
class PaperStrategyRiskAuditReport:
    generated_at: datetime
    config_version: str
    status: str
    gate_count: int
    pass_count: int
    fail_count: int
    incomplete_count: int
    gate_results: tuple[PaperStrategyRiskAuditGateResult, ...]
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at, datetime):
            raise ValueError("generated_at must be a datetime")
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("status", self.status)
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known audit status")
        for field_name in (
            "gate_count",
            "pass_count",
            "fail_count",
            "incomplete_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        normalized_results = _normalize_gate_results(self.gate_results)
        object.__setattr__(self, "gate_results", normalized_results)
        if tuple(gate.gate_name for gate in normalized_results) != GATE_NAMES:
            raise ValueError("gate_results must match the known gates")
        if self.gate_count != len(normalized_results):
            raise ValueError("gate_count must match gate_results")
        if self.pass_count != _count_gate_status(normalized_results, "pass"):
            raise ValueError("pass_count must match gate_results")
        if self.fail_count != _count_gate_status(normalized_results, "fail"):
            raise ValueError("fail_count must match gate_results")
        if self.incomplete_count != _count_gate_status(
            normalized_results,
            "incomplete",
        ):
            raise ValueError("incomplete_count must match gate_results")
        if self.status != _report_status(self.fail_count, self.incomplete_count):
            raise ValueError("status must match gate_results")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


def build_paper_strategy_risk_audit_report(
    *,
    performance_summary: PerformanceSummary,
    nav_risk_report: PaperNavRiskMetricsReport,
    outcome_report: OutcomeTrackingReport | None,
    config: PaperStrategyRiskAuditConfig,
    generated_at: datetime,
) -> PaperStrategyRiskAuditReport:
    if type(performance_summary) is not PerformanceSummary:
        raise ValueError("performance_summary must be a PerformanceSummary")
    if type(nav_risk_report) is not PaperNavRiskMetricsReport:
        raise ValueError("nav_risk_report must be a PaperNavRiskMetricsReport")
    if outcome_report is not None and type(outcome_report) is not OutcomeTrackingReport:
        raise ValueError("outcome_report must be an OutcomeTrackingReport or None")
    if type(config) is not PaperStrategyRiskAuditConfig:
        raise ValueError("config must be a PaperStrategyRiskAuditConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    _require_report_flags("performance_summary", performance_summary)
    _require_report_flags("nav_risk_report", nav_risk_report)
    if outcome_report is not None:
        _require_report_flags("outcome_report", outcome_report)

    gate_results = (
        _build_paper_history_gate(performance_summary, config),
        _build_settlement_evidence_gate(outcome_report, config),
        _build_nav_drawdown_gate(nav_risk_report, config),
        _build_open_exposure_gate(nav_risk_report, config),
    )
    pass_count = _count_gate_status(gate_results, "pass")
    fail_count = _count_gate_status(gate_results, "fail")
    incomplete_count = _count_gate_status(gate_results, "incomplete")

    return PaperStrategyRiskAuditReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(fail_count, incomplete_count),
        gate_count=len(gate_results),
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=gate_results,
    )


def _build_paper_history_gate(
    value: PerformanceSummary,
    config: PaperStrategyRiskAuditConfig,
) -> PaperStrategyRiskAuditGateResult:
    observed_value = (
        f"cycle_count={value.cycle_count}; "
        f"paper_trade_count={value.paper_trade_count}; "
        f"nav_snapshot_count={value.nav_snapshot_count}"
    )
    threshold = (
        f"min_cycle_count={config.min_cycle_count}; "
        f"min_paper_trade_count={config.min_paper_trade_count}; "
        f"min_nav_snapshot_count={config.min_nav_snapshot_count}"
    )
    if (
        value.cycle_count >= config.min_cycle_count
        and value.paper_trade_count >= config.min_paper_trade_count
        and value.nav_snapshot_count >= config.min_nav_snapshot_count
    ):
        status = "pass"
        message = "Paper history is mature enough for the audit."
    else:
        status = "incomplete"
        message = "Paper history has not reached the configured evidence floor."
    return PaperStrategyRiskAuditGateResult(
        gate_name="paper_history",
        status=status,
        message=message,
        observed_value=observed_value,
        threshold=threshold,
    )


def _build_settlement_evidence_gate(
    value: OutcomeTrackingReport | None,
    config: PaperStrategyRiskAuditConfig,
) -> PaperStrategyRiskAuditGateResult:
    threshold = f"min_resolved_count={config.min_resolved_count}"
    if value is None:
        return PaperStrategyRiskAuditGateResult(
            gate_name="settlement_evidence",
            status="incomplete",
            message="Outcome evidence has not been supplied.",
            observed_value=None,
            threshold=threshold,
        )

    observed_value = (
        f"resolved_count={value.resolved_count}; "
        f"total_markets_checked={value.total_markets_checked}"
    )
    if value.resolved_count >= config.min_resolved_count:
        status = "pass"
        message = "Settlement evidence is mature enough for the audit."
    else:
        status = "incomplete"
        message = "Settlement evidence has not reached the configured floor."
    return PaperStrategyRiskAuditGateResult(
        gate_name="settlement_evidence",
        status=status,
        message=message,
        observed_value=observed_value,
        threshold=threshold,
    )


def _build_nav_drawdown_gate(
    value: PaperNavRiskMetricsReport,
    config: PaperStrategyRiskAuditConfig,
) -> PaperStrategyRiskAuditGateResult:
    if value.max_drawdown_pct is None:
        return PaperStrategyRiskAuditGateResult(
            gate_name="nav_drawdown",
            status="incomplete",
            message="NAV drawdown is unavailable.",
            observed_value=None,
            threshold=config.max_nav_drawdown_pct,
        )
    if value.max_drawdown_pct > config.max_nav_drawdown_pct:
        status = "fail"
        message = "NAV drawdown exceeds the configured limit."
    else:
        status = "pass"
        message = "NAV drawdown is within the configured limit."
    return PaperStrategyRiskAuditGateResult(
        gate_name="nav_drawdown",
        status=status,
        message=message,
        observed_value=value.max_drawdown_pct,
        threshold=config.max_nav_drawdown_pct,
    )


def _build_open_exposure_gate(
    value: PaperNavRiskMetricsReport,
    config: PaperStrategyRiskAuditConfig,
) -> PaperStrategyRiskAuditGateResult:
    observed_value = (
        f"open_position_count={value.open_position_count}; "
        f"no_exit_depth_count={value.no_exit_depth_count}; "
        f"largest_market_exposure_share={value.largest_market_exposure_share}"
    )
    threshold = (
        f"max_no_exit_depth_count={config.max_no_exit_depth_count}; "
        f"max_largest_market_exposure_share={config.max_largest_market_exposure_share}"
    )
    has_excess_depth = value.no_exit_depth_count > config.max_no_exit_depth_count
    # A missing share means no exposure concentration was measurable; the count
    # and no-exit-depth fields still carry the open-exposure signal for this gate.
    has_excess_share = (
        value.largest_market_exposure_share is not None
        and value.largest_market_exposure_share
        > config.max_largest_market_exposure_share
    )
    if has_excess_depth or has_excess_share:
        status = "fail"
        message = "Open exposure exceeds the configured limit."
    else:
        status = "pass"
        message = "Open exposure is within the configured limit."
    return PaperStrategyRiskAuditGateResult(
        gate_name="open_exposure",
        status=status,
        message=message,
        observed_value=observed_value,
        threshold=threshold,
    )


def _report_status(fail_count: int, incomplete_count: int) -> str:
    if fail_count > 0:
        return "blocked_by_risk"
    if incomplete_count > 0:
        return "insufficient_evidence"
    return "audit_ready"


def _count_gate_status(
    gate_results: tuple[PaperStrategyRiskAuditGateResult, ...],
    status: str,
) -> int:
    return sum(1 for gate in gate_results if gate.status == status)


def _normalize_gate_results(
    value: tuple[PaperStrategyRiskAuditGateResult, ...],
) -> tuple[PaperStrategyRiskAuditGateResult, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("gate_results must be an iterable")
    try:
        results = tuple(value)
    except TypeError as exc:
        raise ValueError("gate_results must be an iterable") from exc
    for result in results:
        if type(result) is not PaperStrategyRiskAuditGateResult:
            raise ValueError(
                "gate_results must contain PaperStrategyRiskAuditGateResult values",
            )
    return results


def _require_report_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")


def _require_canonical_string(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_audit_value(field_name: str, value: object) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise ValueError(f"{field_name} must be a Decimal, int, string, or None")
    if isinstance(value, Decimal) and not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if isinstance(value, str) and (not value or value.strip() != value):
        raise ValueError(f"{field_name} must be canonical when supplied")

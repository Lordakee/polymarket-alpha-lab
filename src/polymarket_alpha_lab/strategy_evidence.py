"""Paper-only Strategy Evidence Snapshot reducer.

This module is pure report assembly over already-built typed reports. It does
not read files, fetch markets, construct clients, authenticate, inspect wallets,
place orders, rank markets, recommend trades, or provide financial advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from polymarket_alpha_lab.nav_risk_metrics import PaperNavRiskMetricsReport
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport
from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport
from polymarket_alpha_lab.performance_summary import PerformanceSummary
from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryReport,
)


__all__ = (
    "PaperStrategyEvidenceSnapshotConfig",
    "PaperStrategyEvidenceSnapshotReport",
    "build_paper_strategy_evidence_snapshot_report",
)


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
RISK_GAP_NAMES = (
    "negative_cost_adjusted_edges",
    "unexecutable_open_positions",
)
AUDIT_STATUSES = (
    "audit_ready",
    "insufficient_evidence",
    "blocked_by_risk",
)


@dataclass(frozen=True)
class PaperStrategyEvidenceSnapshotConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperStrategyEvidenceSnapshotReport:
    generated_at: datetime
    config_version: str
    status: str
    cycle_count: int
    paper_trade_count: int
    nav_snapshot_count: int
    outcome_checked_count: int | None
    outcome_pending_count: int | None
    outcome_resolved_count: int | None
    outcome_unresolved_count: int | None
    audit_report_count: int | None
    latest_audit_status: str | None
    negative_cost_adjusted_edge_count: int
    unexecutable_open_position_count: int
    evidence_gap_names: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at, datetime):
            raise ValueError("generated_at must be a datetime")
        _require_canonical_string("config_version", self.config_version)
        if self.status not in SNAPSHOT_STATUSES:
            raise ValueError("status must be a known evidence snapshot status")
        for field_name in (
            "cycle_count",
            "paper_trade_count",
            "nav_snapshot_count",
            "negative_cost_adjusted_edge_count",
            "unexecutable_open_position_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "outcome_checked_count",
            "outcome_pending_count",
            "outcome_resolved_count",
            "outcome_unresolved_count",
            "audit_report_count",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        _validate_outcome_counts(
            self.outcome_checked_count,
            self.outcome_pending_count,
            self.outcome_resolved_count,
            self.outcome_unresolved_count,
        )
        if self.latest_audit_status is not None and (
            self.latest_audit_status not in AUDIT_STATUSES
        ):
            raise ValueError("latest_audit_status must be a known audit status or None")
        object.__setattr__(
            self,
            "evidence_gap_names",
            _normalize_evidence_gap_names(self.evidence_gap_names),
        )
        expected_status = _snapshot_status_from_counts(
            cycle_count=self.cycle_count,
            paper_trade_count=self.paper_trade_count,
            nav_snapshot_count=self.nav_snapshot_count,
            outcome_resolved_count=self.outcome_resolved_count,
            audit_report_count=self.audit_report_count,
            negative_cost_adjusted_edge_count=self.negative_cost_adjusted_edge_count,
            unexecutable_open_position_count=self.unexecutable_open_position_count,
            evidence_gap_names=self.evidence_gap_names,
        )
        if self.status != expected_status:
            raise ValueError("status must match local evidence counts and gaps")
        _validate_status_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


def build_paper_strategy_evidence_snapshot_report(
    *,
    performance_summary: PerformanceSummary,
    nav_risk_report: PaperNavRiskMetricsReport,
    cost_audit_report: PaperTradeCostAuditReport,
    outcome_report: OutcomeTrackingReport | None,
    audit_history_report: PaperStrategyRiskAuditHistoryReport | None,
    config: PaperStrategyEvidenceSnapshotConfig,
    generated_at: datetime,
) -> PaperStrategyEvidenceSnapshotReport:
    """Summarize local paper evidence state from caller-supplied typed reports."""

    if type(performance_summary) is not PerformanceSummary:
        raise ValueError("performance_summary must be a PerformanceSummary")
    if type(nav_risk_report) is not PaperNavRiskMetricsReport:
        raise ValueError("nav_risk_report must be a PaperNavRiskMetricsReport")
    if type(cost_audit_report) is not PaperTradeCostAuditReport:
        raise ValueError("cost_audit_report must be a PaperTradeCostAuditReport")
    if outcome_report is not None and type(outcome_report) is not OutcomeTrackingReport:
        raise ValueError("outcome_report must be an OutcomeTrackingReport or None")
    if audit_history_report is not None and (
        type(audit_history_report) is not PaperStrategyRiskAuditHistoryReport
    ):
        raise ValueError(
            "audit_history_report must be a "
            "PaperStrategyRiskAuditHistoryReport or None",
        )
    if type(config) is not PaperStrategyEvidenceSnapshotConfig:
        raise ValueError("config must be a PaperStrategyEvidenceSnapshotConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    _require_report_flags("performance_summary", performance_summary)
    _require_report_flags("nav_risk_report", nav_risk_report)
    _require_report_flags("cost_audit_report", cost_audit_report)
    if outcome_report is not None:
        _require_report_flags("outcome_report", outcome_report)
    if audit_history_report is not None:
        _require_report_flags("audit_history_report", audit_history_report)

    evidence_gap_names = _build_evidence_gap_names(
        performance_summary=performance_summary,
        nav_risk_report=nav_risk_report,
        cost_audit_report=cost_audit_report,
        outcome_report=outcome_report,
        audit_history_report=audit_history_report,
    )
    outcome_checked_count = (
        None if outcome_report is None else outcome_report.total_markets_checked
    )
    outcome_pending_count = None if outcome_report is None else outcome_report.pending_count
    outcome_resolved_count = (
        None if outcome_report is None else outcome_report.resolved_count
    )
    audit_report_count = (
        None if audit_history_report is None else audit_history_report.audit_report_count
    )
    latest_audit_status = (
        None if audit_history_report is None else audit_history_report.latest_audit_status
    )
    unexecutable_open_position_count = _unexecutable_open_position_count(
        nav_risk_report,
    )
    status = _snapshot_status_from_counts(
        cycle_count=performance_summary.cycle_count,
        paper_trade_count=performance_summary.paper_trade_count,
        nav_snapshot_count=nav_risk_report.nav_snapshot_count,
        outcome_resolved_count=outcome_resolved_count,
        audit_report_count=audit_report_count,
        negative_cost_adjusted_edge_count=(
            cost_audit_report.negative_cost_adjusted_edge_count
        ),
        unexecutable_open_position_count=unexecutable_open_position_count,
        evidence_gap_names=evidence_gap_names,
    )

    return PaperStrategyEvidenceSnapshotReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=status,
        cycle_count=performance_summary.cycle_count,
        paper_trade_count=performance_summary.paper_trade_count,
        nav_snapshot_count=nav_risk_report.nav_snapshot_count,
        outcome_checked_count=outcome_checked_count,
        outcome_pending_count=outcome_pending_count,
        outcome_resolved_count=outcome_resolved_count,
        # OutcomeTrackingReport classifies every checked market as resolved or
        # pending, so unresolved local outcome evidence is the pending count.
        outcome_unresolved_count=outcome_pending_count,
        audit_report_count=audit_report_count,
        latest_audit_status=latest_audit_status,
        negative_cost_adjusted_edge_count=(
            cost_audit_report.negative_cost_adjusted_edge_count
        ),
        unexecutable_open_position_count=unexecutable_open_position_count,
        evidence_gap_names=evidence_gap_names,
    )


def _build_evidence_gap_names(
    *,
    performance_summary: PerformanceSummary,
    nav_risk_report: PaperNavRiskMetricsReport,
    cost_audit_report: PaperTradeCostAuditReport,
    outcome_report: OutcomeTrackingReport | None,
    audit_history_report: PaperStrategyRiskAuditHistoryReport | None,
) -> tuple[str, ...]:
    gaps: list[str] = []
    if performance_summary.cycle_count == 0:
        gaps.append("missing_cycles")
    if (
        performance_summary.paper_trade_count == 0
        and cost_audit_report.trade_count == 0
    ):
        gaps.append("missing_paper_trades")
    if (
        performance_summary.nav_snapshot_count == 0
        or nav_risk_report.nav_snapshot_count == 0
    ):
        gaps.append("missing_nav_snapshots")
    if outcome_report is None or outcome_report.resolved_count == 0:
        gaps.append("missing_outcome_evidence")
    if audit_history_report is None or audit_history_report.audit_report_count == 0:
        gaps.append("missing_strategy_audit_history")
    elif audit_history_report.latest_audit_status != "audit_ready":
        gaps.append("latest_strategy_audit_not_ready")
    if cost_audit_report.negative_cost_adjusted_edge_count > 0:
        gaps.append("negative_cost_adjusted_edges")
    if _unexecutable_open_position_count(nav_risk_report) > 0:
        gaps.append("unexecutable_open_positions")
    return tuple(gaps)


def _snapshot_status_from_counts(
    *,
    cycle_count: int,
    paper_trade_count: int,
    nav_snapshot_count: int,
    outcome_resolved_count: int | None,
    audit_report_count: int | None,
    negative_cost_adjusted_edge_count: int,
    unexecutable_open_position_count: int,
    evidence_gap_names: tuple[str, ...],
) -> str:
    if not _has_any_local_evidence(
        cycle_count=cycle_count,
        paper_trade_count=paper_trade_count,
        nav_snapshot_count=nav_snapshot_count,
        outcome_resolved_count=outcome_resolved_count,
        audit_report_count=audit_report_count,
        negative_cost_adjusted_edge_count=negative_cost_adjusted_edge_count,
        unexecutable_open_position_count=unexecutable_open_position_count,
    ):
        return "no_local_evidence"
    if any(gap_name in RISK_GAP_NAMES for gap_name in evidence_gap_names):
        return "local_risk_flags"
    if evidence_gap_names:
        return "local_evidence_gaps"
    return "local_evidence_observed"


def _has_any_local_evidence(
    *,
    cycle_count: int,
    paper_trade_count: int,
    nav_snapshot_count: int,
    outcome_resolved_count: int | None,
    audit_report_count: int | None,
    negative_cost_adjusted_edge_count: int,
    unexecutable_open_position_count: int,
) -> bool:
    return any(
        count > 0
        for count in (
            cycle_count,
            paper_trade_count,
            nav_snapshot_count,
            outcome_resolved_count or 0,
            audit_report_count or 0,
            negative_cost_adjusted_edge_count,
            unexecutable_open_position_count,
        )
    )


def _unexecutable_open_position_count(report: PaperNavRiskMetricsReport) -> int:
    derived_unexecutable_count = (
        report.open_position_count
        - report.fully_executable_count
        - report.partially_executable_count
    )
    return max(report.no_exit_depth_count, derived_unexecutable_count, 0)


def _validate_outcome_counts(
    checked_count: int | None,
    pending_count: int | None,
    resolved_count: int | None,
    unresolved_count: int | None,
) -> None:
    counts = (checked_count, pending_count, resolved_count, unresolved_count)
    present_count = sum(1 for count in counts if count is not None)
    if present_count not in (0, len(counts)):
        raise ValueError("outcome counts must be all present or all absent")
    if checked_count is None:
        return
    if pending_count + resolved_count != checked_count:
        raise ValueError("outcome pending and resolved counts must sum to checked count")
    if unresolved_count != pending_count:
        raise ValueError("outcome_unresolved_count must match outcome_pending_count")


def _validate_status_consistency(report: PaperStrategyEvidenceSnapshotReport) -> None:
    risk_gap_count = sum(
        1 for gap_name in report.evidence_gap_names if gap_name in RISK_GAP_NAMES
    )
    if report.status == "local_evidence_observed" and report.evidence_gap_names:
        raise ValueError("status must match evidence_gap_names")
    if report.status == "local_risk_flags" and risk_gap_count == 0:
        raise ValueError("status must match risk evidence_gap_names")
    if report.status == "local_evidence_gaps":
        if not report.evidence_gap_names or risk_gap_count > 0:
            raise ValueError("status must match non-risk evidence_gap_names")


def _normalize_evidence_gap_names(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("evidence_gap_names must be an iterable")
    try:
        gap_names = tuple(values)
    except TypeError as exc:
        raise ValueError("evidence_gap_names must be an iterable") from exc
    if len(set(gap_names)) != len(gap_names):
        raise ValueError("evidence_gap_names must not contain duplicates")
    for gap_name in gap_names:
        if gap_name not in EVIDENCE_GAP_NAMES:
            raise ValueError("evidence_gap_names must contain known gap names")
    expected_order = tuple(
        gap_name for gap_name in EVIDENCE_GAP_NAMES if gap_name in gap_names
    )
    if gap_names != expected_order:
        raise ValueError("evidence_gap_names must use deterministic ordering")
    return gap_names


def _require_report_flags(field_name: str, value: Any) -> None:
    if value.paper_only is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if value.report_only is not True:
        raise ValueError(f"{field_name} report_only must be True")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: Any) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)

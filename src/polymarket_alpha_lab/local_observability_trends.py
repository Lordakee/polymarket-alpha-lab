"""Read-only local observability trend orchestration.

This module reads caller-selected local paper JSONL artifacts and builds a
single report containing the four pure local trend reducers. It is Phase 1
observability only: no public market fetches, credentials, wallets, live
execution, ranking, recommendations, trade instructions, or financial advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.nav_risk_metrics import (
    PaperNavRiskMetricsConfig,
    PaperNavRiskMetricsReport,
    build_paper_nav_risk_metrics_report,
)
from polymarket_alpha_lab.nav_risk_trend import (
    PaperNavRiskTrendConfig,
    PaperNavRiskTrendReport,
    build_paper_nav_risk_trend_report,
)
from polymarket_alpha_lab.outcome_freshness import (
    OutcomeFreshnessConfig,
    OutcomeFreshnessReport,
    build_outcome_freshness_report,
)
from polymarket_alpha_lab.outcome_tracker import (
    OutcomeTrackingLog,
    OutcomeTrackingReport,
)
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    PaperTradeCostAuditReport,
    build_paper_trade_cost_audit_report,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendConfig,
    PaperTradeCostTrendReport,
    build_paper_trade_cost_trend_report,
)
from polymarket_alpha_lab.performance_summary import (
    PerformanceSummaryConfig,
    build_performance_summary,
)
from polymarket_alpha_lab.positions import PaperNavLog, PaperNavSnapshot
from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    PaperStrategyRiskAuditHistoryReport,
    build_paper_strategy_risk_audit_history_report,
)
from polymarket_alpha_lab.strategy_cycle import (
    PaperStrategyCycleLog,
    PaperStrategyCycleReport,
)
from polymarket_alpha_lab.strategy_evidence import (
    PaperStrategyEvidenceSnapshotConfig,
    PaperStrategyEvidenceSnapshotReport,
    build_paper_strategy_evidence_snapshot_report,
)
from polymarket_alpha_lab.strategy_evidence_trend import (
    PaperStrategyEvidenceTrendConfig,
    PaperStrategyEvidenceTrendReport,
    build_paper_strategy_evidence_trend_report,
)
from polymarket_alpha_lab.strategy_risk_audit import PaperStrategyRiskAuditReport
from polymarket_alpha_lab.strategy_risk_audit_log import PaperStrategyRiskAuditLog


__all__ = (
    "LocalObservabilityTrendsConfig",
    "LocalObservabilityTrendsReport",
    "run_local_observability_trends",
)


@dataclass(frozen=True)
class LocalObservabilityTrendsConfig:
    config_version: str
    outcome_stale_after_seconds: int = 86_400

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "outcome_stale_after_seconds",
            self.outcome_stale_after_seconds,
        )


@dataclass(frozen=True)
class LocalObservabilityTrendsReport:
    generated_at: datetime
    config_version: str
    strategy_evidence_trend: PaperStrategyEvidenceTrendReport
    outcome_freshness: OutcomeFreshnessReport
    nav_risk_trend: PaperNavRiskTrendReport
    paper_trade_cost_trend: PaperTradeCostTrendReport
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_exact_report(
            "strategy_evidence_trend",
            self.strategy_evidence_trend,
            PaperStrategyEvidenceTrendReport,
        )
        _require_exact_report(
            "outcome_freshness",
            self.outcome_freshness,
            OutcomeFreshnessReport,
        )
        _require_exact_report(
            "nav_risk_trend",
            self.nav_risk_trend,
            PaperNavRiskTrendReport,
        )
        _require_exact_report(
            "paper_trade_cost_trend",
            self.paper_trade_cost_trend,
            PaperTradeCostTrendReport,
        )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def run_local_observability_trends(
    *,
    cycle_log: Path | str,
    trade_log: Path | str,
    nav_log: Path | str,
    outcome_log: Path | str | None,
    strategy_audit_log: Path | str | None,
    config: LocalObservabilityTrendsConfig,
    generated_at: datetime,
) -> LocalObservabilityTrendsReport:
    """Build trend summaries from explicitly supplied local paper artifacts."""

    if type(config) is not LocalObservabilityTrendsConfig:
        raise ValueError("config must be a LocalObservabilityTrendsConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    cycle_reports = PaperStrategyCycleLog.read(cycle_log)
    trade_records = PaperTradeJournal.read(trade_log)
    nav_snapshots = PaperNavLog.read(nav_log)
    outcome_reports = (
        () if outcome_log is None else OutcomeTrackingLog.read(outcome_log)
    )
    strategy_audit_reports = (
        ()
        if strategy_audit_log is None
        else PaperStrategyRiskAuditLog.read(strategy_audit_log)
    )

    strategy_evidence_snapshots = _build_strategy_evidence_snapshot_history(
        cycle_reports=cycle_reports,
        trade_records=trade_records,
        nav_snapshots=nav_snapshots,
        outcome_reports=outcome_reports,
        strategy_audit_reports=strategy_audit_reports,
        generated_at=generated_at,
    )
    nav_risk_reports = _build_nav_risk_report_history(
        nav_snapshots,
        generated_at=generated_at,
    )
    cost_audit_reports = _build_cost_audit_report_history(
        trade_records,
        generated_at=generated_at,
    )

    return LocalObservabilityTrendsReport(
        generated_at=generated_at,
        config_version=config.config_version,
        strategy_evidence_trend=build_paper_strategy_evidence_trend_report(
            strategy_evidence_snapshots,
            config=PaperStrategyEvidenceTrendConfig(
                config_version="strategy-evidence-trend-v0",
            ),
            generated_at=generated_at,
        ),
        outcome_freshness=build_outcome_freshness_report(
            outcome_reports,
            config=OutcomeFreshnessConfig(
                config_version="outcome-freshness-v0",
                stale_after_seconds=config.outcome_stale_after_seconds,
            ),
            generated_at=generated_at,
        ),
        nav_risk_trend=build_paper_nav_risk_trend_report(
            nav_risk_reports,
            config=PaperNavRiskTrendConfig(config_version="nav-risk-trend-v0"),
            generated_at=generated_at,
        ),
        paper_trade_cost_trend=build_paper_trade_cost_trend_report(
            cost_audit_reports,
            config=PaperTradeCostTrendConfig(
                config_version="paper-trade-cost-trend-v0",
            ),
            generated_at=generated_at,
        ),
    )


def _build_strategy_evidence_snapshot_history(
    *,
    cycle_reports: tuple[PaperStrategyCycleReport, ...],
    trade_records: tuple[PaperTradeRecord, ...],
    nav_snapshots: tuple[PaperNavSnapshot, ...],
    outcome_reports: tuple[OutcomeTrackingReport, ...],
    strategy_audit_reports: tuple[PaperStrategyRiskAuditReport, ...],
    generated_at: datetime,
) -> tuple[PaperStrategyEvidenceSnapshotReport, ...]:
    snapshot_count = max(
        len(cycle_reports),
        len(trade_records),
        len(nav_snapshots),
    )
    return tuple(
        _build_strategy_evidence_snapshot_for_prefix(
            cycle_reports=cycle_reports[:prefix_size],
            trade_records=trade_records[:prefix_size],
            nav_snapshots=nav_snapshots[:prefix_size],
            outcome_reports=outcome_reports[:prefix_size],
            strategy_audit_reports=strategy_audit_reports[:prefix_size],
            generated_at=generated_at,
        )
        for prefix_size in range(1, snapshot_count + 1)
    )


def _build_strategy_evidence_snapshot_for_prefix(
    *,
    cycle_reports: tuple[PaperStrategyCycleReport, ...],
    trade_records: tuple[PaperTradeRecord, ...],
    nav_snapshots: tuple[PaperNavSnapshot, ...],
    outcome_reports: tuple[OutcomeTrackingReport, ...],
    strategy_audit_reports: tuple[PaperStrategyRiskAuditReport, ...],
    generated_at: datetime,
) -> PaperStrategyEvidenceSnapshotReport:
    performance_summary = build_performance_summary(
        cycle_reports,
        trade_records,
        nav_snapshots,
        config=PerformanceSummaryConfig(config_version="performance-summary-v1"),
        generated_at=generated_at,
    )
    nav_risk_report = _build_append_order_nav_risk_metrics_report(
        nav_snapshots,
        generated_at=generated_at,
    )
    cost_audit_report = build_paper_trade_cost_audit_report(
        trade_records,
        config=PaperTradeCostAuditConfig(
            config_version="paper-trade-cost-audit-v0",
        ),
        generated_at=generated_at,
    )
    return build_paper_strategy_evidence_snapshot_report(
        performance_summary=performance_summary,
        nav_risk_report=nav_risk_report,
        cost_audit_report=cost_audit_report,
        outcome_report=outcome_reports[-1] if outcome_reports else None,
        audit_history_report=_latest_strategy_audit_history_report(
            strategy_audit_reports,
            generated_at=generated_at,
        ),
        config=PaperStrategyEvidenceSnapshotConfig(
            config_version="strategy-evidence-snapshot-v0",
        ),
        generated_at=generated_at,
    )


def _build_nav_risk_report_history(
    nav_snapshots: tuple[PaperNavSnapshot, ...],
    *,
    generated_at: datetime,
) -> tuple[PaperNavRiskMetricsReport, ...]:
    return tuple(
        _build_append_order_nav_risk_metrics_report(
            nav_snapshots[:prefix_size],
            generated_at=generated_at,
        )
        for prefix_size in range(1, len(nav_snapshots) + 1)
    )


def _build_append_order_nav_risk_metrics_report(
    nav_snapshots: tuple[PaperNavSnapshot, ...],
    *,
    generated_at: datetime,
) -> PaperNavRiskMetricsReport:
    return build_paper_nav_risk_metrics_report(
        nav_snapshots,
        config=PaperNavRiskMetricsConfig(
            config_version="nav-risk-metrics-v0",
            preserve_input_order=True,
        ),
        generated_at=generated_at,
    )


def _build_cost_audit_report_history(
    trade_records: tuple[PaperTradeRecord, ...],
    *,
    generated_at: datetime,
) -> tuple[PaperTradeCostAuditReport, ...]:
    return tuple(
        build_paper_trade_cost_audit_report(
            trade_records[:prefix_size],
            config=PaperTradeCostAuditConfig(
                config_version="paper-trade-cost-audit-v0",
            ),
            generated_at=generated_at,
        )
        for prefix_size in range(1, len(trade_records) + 1)
    )


def _latest_strategy_audit_history_report(
    strategy_audit_reports: tuple[PaperStrategyRiskAuditReport, ...],
    *,
    generated_at: datetime,
) -> PaperStrategyRiskAuditHistoryReport | None:
    if not strategy_audit_reports:
        return None
    return build_paper_strategy_risk_audit_history_report(
        strategy_audit_reports,
        config=PaperStrategyRiskAuditHistoryConfig(
            config_version="strategy-audit-history-v0",
        ),
        generated_at=generated_at,
    )


def _require_exact_report(field_name: str, value: Any, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a nonnegative integer")
    if value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)

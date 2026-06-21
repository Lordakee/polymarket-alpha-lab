"""Pure reducer over loaded local observability trend reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsReport,
)
from polymarket_alpha_lab.nav_risk_trend import (
    NAV_RISK_TREND_STATUSES,
    PaperNavRiskTrendReport,
    PaperNavRiskTrendStatusRow,
)
from polymarket_alpha_lab.outcome_freshness import (
    OUTCOME_FRESHNESS_STATUSES,
    OutcomeFreshnessReport,
    OutcomeFreshnessStatusRow,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    COST_TREND_STATUSES,
    PaperTradeCostTrendReport,
    PaperTradeCostTrendStatusRow,
)
from polymarket_alpha_lab.strategy_evidence import SNAPSHOT_STATUSES
from polymarket_alpha_lab.strategy_evidence_trend import (
    PaperStrategyEvidenceTrendGapRow,
    PaperStrategyEvidenceTrendReport,
    PaperStrategyEvidenceTrendStatusRow,
)


__all__ = (
    "LocalObservabilityTrendsDbHistoryConfig",
    "LocalObservabilityTrendsDbHistoryReport",
    "LocalObservabilityTrendsDbHistoryStatusRow",
    "build_local_observability_trends_db_history_report",
)


RATIO_QUANTUM = Decimal("0.000001")
HISTORY_STATUSES = (
    "empty_local_observability_trends_db_history",
    "latest_local_observability_trends_observed",
    "latest_local_observability_trends_warning",
)
STATUS_KINDS = ("strategy_evidence", "outcome", "nav", "cost")


@dataclass(frozen=True)
class LocalObservabilityTrendsDbHistoryConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class LocalObservabilityTrendsDbHistoryStatusRow:
    status_kind: str
    status: str
    report_count: int
    report_ratio: Decimal | None

    def __post_init__(self) -> None:
        if type(self.status_kind) is not str or self.status_kind not in STATUS_KINDS:
            raise ValueError("status_kind must be a known status kind")
        if type(self.status) is not str or self.status not in _allowed_statuses(
            self.status_kind,
        ):
            raise ValueError("status must be known for status_kind")
        _require_nonnegative_int("report_count", self.report_count)
        _require_optional_probability_decimal("report_ratio", self.report_ratio)


@dataclass(frozen=True)
class LocalObservabilityTrendsDbHistoryReport:
    generated_at: datetime
    config_version: str
    status: str
    report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_strategy_evidence_status: str | None
    latest_outcome_status: str | None
    latest_nav_status: str | None
    latest_cost_status: str | None
    duplicate_generated_at_count: int
    consecutive_outcome_stale_count: int
    consecutive_nav_warning_or_high_risk_count: int
    consecutive_cost_warning_or_critical_count: int
    strategy_evidence_status_rows: tuple[LocalObservabilityTrendsDbHistoryStatusRow, ...]
    outcome_status_rows: tuple[LocalObservabilityTrendsDbHistoryStatusRow, ...]
    nav_status_rows: tuple[LocalObservabilityTrendsDbHistoryStatusRow, ...]
    cost_status_rows: tuple[LocalObservabilityTrendsDbHistoryStatusRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "first_report_generated_at",
            _as_optional_utc(
                "first_report_generated_at",
                self.first_report_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_report_generated_at",
            _as_optional_utc(
                "latest_report_generated_at",
                self.latest_report_generated_at,
            ),
        )
        _require_canonical_string("config_version", self.config_version)
        if type(self.status) is not str or self.status not in HISTORY_STATUSES:
            raise ValueError("status must be a known history status")
        _require_nonnegative_int("report_count", self.report_count)
        for field_name, value in (
            ("duplicate_generated_at_count", self.duplicate_generated_at_count),
            ("consecutive_outcome_stale_count", self.consecutive_outcome_stale_count),
            (
                "consecutive_nav_warning_or_high_risk_count",
                self.consecutive_nav_warning_or_high_risk_count,
            ),
            (
                "consecutive_cost_warning_or_critical_count",
                self.consecutive_cost_warning_or_critical_count,
            ),
        ):
            _require_nonnegative_int(field_name, value)
        _require_optional_member(
            "latest_strategy_evidence_status",
            self.latest_strategy_evidence_status,
            SNAPSHOT_STATUSES,
        )
        _require_optional_member(
            "latest_outcome_status",
            self.latest_outcome_status,
            OUTCOME_FRESHNESS_STATUSES,
        )
        _require_optional_member(
            "latest_nav_status",
            self.latest_nav_status,
            NAV_RISK_TREND_STATUSES,
        )
        _require_optional_member(
            "latest_cost_status",
            self.latest_cost_status,
            COST_TREND_STATUSES,
        )
        object.__setattr__(
            self,
            "strategy_evidence_status_rows",
            _normalize_status_rows(
                "strategy_evidence_status_rows",
                "strategy_evidence",
                self.strategy_evidence_status_rows,
            ),
        )
        object.__setattr__(
            self,
            "outcome_status_rows",
            _normalize_status_rows(
                "outcome_status_rows",
                "outcome",
                self.outcome_status_rows,
            ),
        )
        object.__setattr__(
            self,
            "nav_status_rows",
            _normalize_status_rows(
                "nav_status_rows",
                "nav",
                self.nav_status_rows,
            ),
        )
        object.__setattr__(
            self,
            "cost_status_rows",
            _normalize_status_rows(
                "cost_status_rows",
                "cost",
                self.cost_status_rows,
            ),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_local_observability_trends_db_history_report(
    reports: list[LocalObservabilityTrendsReport]
    | tuple[LocalObservabilityTrendsReport, ...],
    *,
    config: LocalObservabilityTrendsDbHistoryConfig,
    generated_at: datetime,
) -> LocalObservabilityTrendsDbHistoryReport:
    if type(config) is not LocalObservabilityTrendsDbHistoryConfig:
        raise ValueError("config must be a LocalObservabilityTrendsDbHistoryConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    report_items = _normalize_reports(reports)
    report_count = len(report_items)
    latest = report_items[-1] if report_items else None
    strategy_status_counts = _status_counts(
        report_items,
        "strategy_evidence",
    )
    outcome_status_counts = _status_counts(report_items, "outcome")
    nav_status_counts = _status_counts(report_items, "nav")
    cost_status_counts = _status_counts(report_items, "cost")

    return LocalObservabilityTrendsDbHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_history_status(latest),
        report_count=report_count,
        first_report_generated_at=(
            report_items[0].generated_at if report_items else None
        ),
        latest_report_generated_at=latest.generated_at if latest is not None else None,
        latest_strategy_evidence_status=(
            latest.strategy_evidence_trend.latest_status
            if latest is not None
            else None
        ),
        latest_outcome_status=latest.outcome_freshness.status if latest is not None else None,
        latest_nav_status=latest.nav_risk_trend.status if latest is not None else None,
        latest_cost_status=(
            latest.paper_trade_cost_trend.status if latest is not None else None
        ),
        duplicate_generated_at_count=_duplicate_generated_at_count(report_items),
        consecutive_outcome_stale_count=_consecutive_count(
            report_items,
            lambda report: report.outcome_freshness.status == "latest_outcomes_stale",
        ),
        consecutive_nav_warning_or_high_risk_count=_consecutive_count(
            report_items,
            lambda report: (
                report.nav_risk_trend.status
                == "latest_nav_has_unexecutable_positions"
            ),
        ),
        consecutive_cost_warning_or_critical_count=_consecutive_count(
            report_items,
            lambda report: (
                report.paper_trade_cost_trend.status
                == "latest_negative_cost_adjusted_edges"
            ),
        ),
        strategy_evidence_status_rows=_build_status_rows(
            "strategy_evidence",
            strategy_status_counts,
            report_count,
        ),
        outcome_status_rows=_build_status_rows(
            "outcome",
            outcome_status_counts,
            report_count,
        ),
        nav_status_rows=_build_status_rows("nav", nav_status_counts, report_count),
        cost_status_rows=_build_status_rows("cost", cost_status_counts, report_count),
    )


def _normalize_reports(
    reports: list[LocalObservabilityTrendsReport]
    | tuple[LocalObservabilityTrendsReport, ...],
) -> tuple[LocalObservabilityTrendsReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple")
    return tuple(_clone_report(report) for report in reports)


def _clone_report(report: LocalObservabilityTrendsReport) -> LocalObservabilityTrendsReport:
    if type(report) is not LocalObservabilityTrendsReport:
        raise ValueError("reports must contain LocalObservabilityTrendsReport values")
    return LocalObservabilityTrendsReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        strategy_evidence_trend=_clone_strategy_evidence_trend(
            report.strategy_evidence_trend,
        ),
        outcome_freshness=_clone_outcome_freshness(report.outcome_freshness),
        nav_risk_trend=_clone_nav_trend(report.nav_risk_trend),
        paper_trade_cost_trend=_clone_cost_trend(report.paper_trade_cost_trend),
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _clone_strategy_evidence_trend(
    report: PaperStrategyEvidenceTrendReport,
) -> PaperStrategyEvidenceTrendReport:
    if type(report) is not PaperStrategyEvidenceTrendReport:
        raise ValueError(
            "strategy_evidence_trend must be a PaperStrategyEvidenceTrendReport",
        )
    return PaperStrategyEvidenceTrendReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        snapshot_report_count=report.snapshot_report_count,
        first_report_generated_at=report.first_report_generated_at,
        latest_report_generated_at=report.latest_report_generated_at,
        latest_status=report.latest_status,
        latest_evidence_gap_names=report.latest_evidence_gap_names,
        consecutive_local_risk_flags_count=report.consecutive_local_risk_flags_count,
        consecutive_non_observed_count=report.consecutive_non_observed_count,
        status_rows=tuple(
            PaperStrategyEvidenceTrendStatusRow(
                snapshot_status=row.snapshot_status,
                snapshot_count=row.snapshot_count,
                snapshot_ratio=row.snapshot_ratio,
            )
            for row in report.status_rows
        ),
        gap_rows=tuple(
            PaperStrategyEvidenceTrendGapRow(
                evidence_gap_name=row.evidence_gap_name,
                gap_count=row.gap_count,
                gap_ratio=row.gap_ratio,
            )
            for row in report.gap_rows
        ),
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _clone_outcome_freshness(report: OutcomeFreshnessReport) -> OutcomeFreshnessReport:
    if type(report) is not OutcomeFreshnessReport:
        raise ValueError("outcome_freshness must be an OutcomeFreshnessReport")
    return OutcomeFreshnessReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        outcome_report_count=report.outcome_report_count,
        first_report_generated_at=report.first_report_generated_at,
        latest_report_generated_at=report.latest_report_generated_at,
        latest_total_markets_checked=report.latest_total_markets_checked,
        latest_resolved_count=report.latest_resolved_count,
        latest_pending_count=report.latest_pending_count,
        latest_resolved_ratio=report.latest_resolved_ratio,
        latest_pending_ratio=report.latest_pending_ratio,
        latest_report_age_seconds=report.latest_report_age_seconds,
        consecutive_pending_count=report.consecutive_pending_count,
        status=report.status,
        status_rows=tuple(
            OutcomeFreshnessStatusRow(
                status=row.status,
                outcome_report_count=row.outcome_report_count,
                outcome_report_ratio=row.outcome_report_ratio,
            )
            for row in report.status_rows
        ),
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _clone_nav_trend(report: PaperNavRiskTrendReport) -> PaperNavRiskTrendReport:
    if type(report) is not PaperNavRiskTrendReport:
        raise ValueError("nav_risk_trend must be a PaperNavRiskTrendReport")
    return PaperNavRiskTrendReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        nav_risk_report_count=report.nav_risk_report_count,
        first_report_generated_at=report.first_report_generated_at,
        latest_report_generated_at=report.latest_report_generated_at,
        latest_exit_nav=report.latest_exit_nav,
        latest_cumulative_return=report.latest_cumulative_return,
        latest_max_drawdown=report.latest_max_drawdown,
        latest_max_drawdown_pct=report.latest_max_drawdown_pct,
        latest_nav_return_volatility=report.latest_nav_return_volatility,
        latest_open_position_count=report.latest_open_position_count,
        latest_fully_executable_count=report.latest_fully_executable_count,
        latest_partially_executable_count=report.latest_partially_executable_count,
        latest_no_exit_depth_count=report.latest_no_exit_depth_count,
        latest_largest_market_exposure_value=(
            report.latest_largest_market_exposure_value
        ),
        latest_largest_market_exposure_share=(
            report.latest_largest_market_exposure_share
        ),
        worst_observed_max_drawdown_pct=report.worst_observed_max_drawdown_pct,
        consecutive_unexecutable_open_position_count=(
            report.consecutive_unexecutable_open_position_count
        ),
        status=report.status,
        status_rows=tuple(
            PaperNavRiskTrendStatusRow(
                status=row.status,
                report_count=row.report_count,
                report_ratio=row.report_ratio,
            )
            for row in report.status_rows
        ),
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _clone_cost_trend(
    report: PaperTradeCostTrendReport,
) -> PaperTradeCostTrendReport:
    if type(report) is not PaperTradeCostTrendReport:
        raise ValueError("paper_trade_cost_trend must be a PaperTradeCostTrendReport")
    return PaperTradeCostTrendReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        cost_audit_report_count=report.cost_audit_report_count,
        first_report_generated_at=report.first_report_generated_at,
        latest_report_generated_at=report.latest_report_generated_at,
        latest_trade_count=report.latest_trade_count,
        latest_fill_rate=report.latest_fill_rate,
        latest_mean_theoretical_edge=report.latest_mean_theoretical_edge,
        latest_mean_cost_adjusted_edge=report.latest_mean_cost_adjusted_edge,
        latest_mean_edge_cost_drag=report.latest_mean_edge_cost_drag,
        latest_total_edge_cost_drag=report.latest_total_edge_cost_drag,
        latest_partial_fill_count=report.latest_partial_fill_count,
        latest_negative_cost_adjusted_edge_count=(
            report.latest_negative_cost_adjusted_edge_count
        ),
        worst_observed_mean_edge_cost_drag=report.worst_observed_mean_edge_cost_drag,
        worst_observed_negative_cost_adjusted_edge_count=(
            report.worst_observed_negative_cost_adjusted_edge_count
        ),
        consecutive_negative_cost_adjusted_edge_count=(
            report.consecutive_negative_cost_adjusted_edge_count
        ),
        status=report.status,
        status_rows=tuple(
            PaperTradeCostTrendStatusRow(
                status=row.status,
                status_count=row.status_count,
                status_ratio=row.status_ratio,
            )
            for row in report.status_rows
        ),
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _status_counts(
    reports: tuple[LocalObservabilityTrendsReport, ...],
    status_kind: str,
) -> dict[str, int]:
    counts = {status: 0 for status in _allowed_statuses(status_kind)}
    for report in reports:
        status = _source_status(report, status_kind)
        if status is not None:
            counts[status] += 1
    return counts


def _source_status(
    report: LocalObservabilityTrendsReport,
    status_kind: str,
) -> str | None:
    if status_kind == "strategy_evidence":
        return report.strategy_evidence_trend.latest_status
    if status_kind == "outcome":
        return report.outcome_freshness.status
    if status_kind == "nav":
        return report.nav_risk_trend.status
    if status_kind == "cost":
        return report.paper_trade_cost_trend.status
    raise ValueError("status_kind must be known")


def _build_status_rows(
    status_kind: str,
    status_counts: dict[str, int],
    total: int,
) -> tuple[LocalObservabilityTrendsDbHistoryStatusRow, ...]:
    return tuple(
        LocalObservabilityTrendsDbHistoryStatusRow(
            status_kind=status_kind,
            status=status,
            report_count=status_counts[status],
            report_ratio=_ratio(status_counts[status], total),
        )
        for status in _allowed_statuses(status_kind)
    )


def _allowed_statuses(status_kind: str) -> tuple[str, ...]:
    if status_kind == "strategy_evidence":
        return SNAPSHOT_STATUSES
    if status_kind == "outcome":
        return OUTCOME_FRESHNESS_STATUSES
    if status_kind == "nav":
        return NAV_RISK_TREND_STATUSES
    if status_kind == "cost":
        return COST_TREND_STATUSES
    raise ValueError("status_kind must be known")


def _history_status(
    latest: LocalObservabilityTrendsReport | None,
) -> str:
    if latest is None:
        return "empty_local_observability_trends_db_history"
    if (
        latest.strategy_evidence_trend.latest_status == "local_risk_flags"
        or latest.outcome_freshness.status == "latest_outcomes_stale"
        or latest.nav_risk_trend.status == "latest_nav_has_unexecutable_positions"
        or latest.paper_trade_cost_trend.status
        == "latest_negative_cost_adjusted_edges"
    ):
        return "latest_local_observability_trends_warning"
    return "latest_local_observability_trends_observed"


def _duplicate_generated_at_count(
    reports: tuple[LocalObservabilityTrendsReport, ...],
) -> int:
    observed_times: set[datetime] = set()
    duplicate_count = 0
    for report in reports:
        if report.generated_at in observed_times:
            duplicate_count += 1
        else:
            observed_times.add(report.generated_at)
    return duplicate_count


def _consecutive_count(
    reports: tuple[LocalObservabilityTrendsReport, ...],
    predicate: Any,
) -> int:
    count = 0
    for report in reversed(reports):
        if not predicate(report):
            break
        count += 1
    return count


def _normalize_status_rows(
    field_name: str,
    status_kind: str,
    rows: tuple[LocalObservabilityTrendsDbHistoryStatusRow, ...],
) -> tuple[LocalObservabilityTrendsDbHistoryStatusRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    normalized = tuple(
        _clone_status_row(field_name, status_kind, row) for row in items
    )
    if tuple(row.status for row in normalized) != _allowed_statuses(status_kind):
        raise ValueError(f"{field_name} must cover known statuses")
    return normalized


def _clone_status_row(
    field_name: str,
    status_kind: str,
    row: LocalObservabilityTrendsDbHistoryStatusRow,
) -> LocalObservabilityTrendsDbHistoryStatusRow:
    if type(row) is not LocalObservabilityTrendsDbHistoryStatusRow:
        raise ValueError(f"{field_name} must contain history status rows")
    if row.status_kind != status_kind:
        raise ValueError(f"{field_name} rows must match status kind")
    return LocalObservabilityTrendsDbHistoryStatusRow(
        status_kind=row.status_kind,
        status=row.status,
        report_count=row.report_count,
        report_ratio=row.report_ratio,
    )


def _validate_report_consistency(
    report: LocalObservabilityTrendsDbHistoryReport,
) -> None:
    if report.report_count == 0:
        if report.status != "empty_local_observability_trends_db_history":
            raise ValueError("status must match report_count")
        if (
            report.first_report_generated_at is not None
            or report.latest_report_generated_at is not None
        ):
            raise ValueError("report timestamp bounds must be absent")
        if (
            report.latest_strategy_evidence_status is not None
            or report.latest_outcome_status is not None
            or report.latest_nav_status is not None
            or report.latest_cost_status is not None
        ):
            raise ValueError("latest statuses must be absent")
        if (
            report.duplicate_generated_at_count != 0
            or report.consecutive_outcome_stale_count != 0
            or report.consecutive_nav_warning_or_high_risk_count != 0
            or report.consecutive_cost_warning_or_critical_count != 0
        ):
            raise ValueError("empty history counts must be zero")
    else:
        if report.status == "empty_local_observability_trends_db_history":
            raise ValueError("status must match report_count")
        if (
            report.first_report_generated_at is None
            or report.latest_report_generated_at is None
        ):
            raise ValueError("report timestamp bounds are required")
        if (
            report.latest_outcome_status is None
            or report.latest_nav_status is None
            or report.latest_cost_status is None
        ):
            raise ValueError("latest component statuses are required")
        if report.status != _history_status_from_values(
            report.latest_strategy_evidence_status,
            report.latest_outcome_status,
            report.latest_nav_status,
            report.latest_cost_status,
        ):
            raise ValueError("status must match latest component statuses")
        _validate_streaks(report)
        _validate_latest_status_row_counts(report)

    _validate_status_row_group(
        report.strategy_evidence_status_rows,
        report.report_count,
        require_complete=False,
    )
    _validate_status_row_group(
        report.outcome_status_rows,
        report.report_count,
        require_complete=True,
    )
    _validate_status_row_group(
        report.nav_status_rows,
        report.report_count,
        require_complete=True,
    )
    _validate_status_row_group(
        report.cost_status_rows,
        report.report_count,
        require_complete=True,
    )


def _history_status_from_values(
    strategy_status: str | None,
    outcome_status: str | None,
    nav_status: str | None,
    cost_status: str | None,
) -> str:
    if (
        strategy_status == "local_risk_flags"
        or outcome_status == "latest_outcomes_stale"
        or nav_status == "latest_nav_has_unexecutable_positions"
        or cost_status == "latest_negative_cost_adjusted_edges"
    ):
        return "latest_local_observability_trends_warning"
    return "latest_local_observability_trends_observed"


def _validate_streaks(report: LocalObservabilityTrendsDbHistoryReport) -> None:
    if report.duplicate_generated_at_count >= report.report_count:
        raise ValueError("duplicate_generated_at_count must be below report_count")
    for field_name, value in (
        ("consecutive_outcome_stale_count", report.consecutive_outcome_stale_count),
        (
            "consecutive_nav_warning_or_high_risk_count",
            report.consecutive_nav_warning_or_high_risk_count,
        ),
        (
            "consecutive_cost_warning_or_critical_count",
            report.consecutive_cost_warning_or_critical_count,
        ),
    ):
        if value > report.report_count:
            raise ValueError(f"{field_name} must not exceed report_count")
    if report.latest_outcome_status == "latest_outcomes_stale":
        if report.consecutive_outcome_stale_count < 1:
            raise ValueError("stale latest outcome requires a streak")
    elif report.consecutive_outcome_stale_count != 0:
        raise ValueError("non-stale latest outcome must reset the streak")
    if report.latest_nav_status == "latest_nav_has_unexecutable_positions":
        if report.consecutive_nav_warning_or_high_risk_count < 1:
            raise ValueError("latest nav warning requires a streak")
    elif report.consecutive_nav_warning_or_high_risk_count != 0:
        raise ValueError("non-warning latest nav must reset the streak")
    if report.latest_cost_status == "latest_negative_cost_adjusted_edges":
        if report.consecutive_cost_warning_or_critical_count < 1:
            raise ValueError("latest cost warning requires a streak")
    elif report.consecutive_cost_warning_or_critical_count != 0:
        raise ValueError("non-warning latest cost must reset the streak")


def _validate_latest_status_row_counts(
    report: LocalObservabilityTrendsDbHistoryReport,
) -> None:
    for latest_status, rows in (
        (
            report.latest_strategy_evidence_status,
            report.strategy_evidence_status_rows,
        ),
        (report.latest_outcome_status, report.outcome_status_rows),
        (report.latest_nav_status, report.nav_status_rows),
        (report.latest_cost_status, report.cost_status_rows),
    ):
        if latest_status is None:
            continue
        row_count = next(
            row.report_count for row in rows if row.status == latest_status
        )
        if row_count < 1:
            raise ValueError("latest status must be represented by status rows")


def _validate_status_row_group(
    rows: tuple[LocalObservabilityTrendsDbHistoryStatusRow, ...],
    report_count: int,
    *,
    require_complete: bool,
) -> None:
    total = sum(row.report_count for row in rows)
    if require_complete and total != report_count:
        raise ValueError("status rows must sum to report_count")
    if not require_complete and total > report_count:
        raise ValueError("status rows must not exceed report_count")
    for row in rows:
        if row.report_ratio != _ratio(row.report_count, report_count):
            raise ValueError("status row ratios must match report_count")


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value is None:
        return
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known status")


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be between zero and one")
    if (
        value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)
        or value.as_tuple().exponent != RATIO_QUANTUM.as_tuple().exponent
    ):
        raise ValueError(f"{field_name} must align to ratio quantum")

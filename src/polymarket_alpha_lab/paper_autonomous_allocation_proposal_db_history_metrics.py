"""Pure metrics reducer for persisted paper allocation proposal reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext

from polymarket_alpha_lab.paper_autonomous_allocation_proposal import (
    PROPOSAL_STATUSES,
    PaperAutonomousAllocationProposalReport,
)


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_CONFIG_VERSION",
    "PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow",
    "PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow",
    "PaperAutonomousAllocationProposalDbHistoryMetricsConfig",
    "PaperAutonomousAllocationProposalDbHistoryMetricsReport",
    "PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary",
    "build_paper_autonomous_allocation_proposal_db_history_metrics_report",
)


DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-db-history-metrics-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
CAP_REASON_CODES = frozenset(
    (
        "capped",
        "correlation_cap",
        "event_cap",
        "market_cap",
        "no_budget",
        "theme_cap",
        "total_budget_cap",
    ),
)
GROUP_TYPES = ("correlation_group", "event", "market", "theme")


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsConfig:
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow:
    group_type: str
    group_id: str
    allocated_paper_notional: Decimal
    allocated_paper_notional_share: Decimal | None
    row_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if self.group_type not in GROUP_TYPES:
            raise ValueError("group_type must be known")
        _require_canonical_string("group_id", self.group_id)
        object.__setattr__(
            self,
            "allocated_paper_notional",
            _normalize_decimal(
                "allocated_paper_notional",
                self.allocated_paper_notional,
            ),
        )
        object.__setattr__(
            self,
            "allocated_paper_notional_share",
            _normalize_optional_decimal(
                "allocated_paper_notional_share",
                self.allocated_paper_notional_share,
            ),
        )
        _require_nonnegative_int("row_count", self.row_count)
        _require_hard_flags("concentration row", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow:
    reason_code: str
    row_count: int
    allocated_paper_notional: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if self.reason_code not in CAP_REASON_CODES:
            raise ValueError("reason_code must be a cap reason")
        _require_nonnegative_int("row_count", self.row_count)
        object.__setattr__(
            self,
            "allocated_paper_notional",
            _normalize_decimal(
                "allocated_paper_notional",
                self.allocated_paper_notional,
            ),
        )
        _require_hard_flags("cap reason row", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary:
    input_position: int
    generated_at: datetime
    proposal_status: str
    allocation_input_count: int
    allocation_row_count: int
    allocated_count: int
    capped_count: int
    no_budget_count: int
    non_recommend_count: int
    skipped_count: int
    total_requested_paper_notional: Decimal
    total_allocated_paper_notional: Decimal
    remaining_paper_budget: Decimal
    total_paper_budget: Decimal
    budget_utilization: Decimal | None
    requested_fill_ratio: Decimal | None
    allocated_row_share: Decimal | None
    capped_row_share: Decimal | None
    no_budget_row_share: Decimal | None
    non_recommend_row_share: Decimal | None
    skipped_row_share: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_nonnegative_int("input_position", self.input_position)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_proposal_status("proposal_status", self.proposal_status)
        for field_name in (
            "allocation_input_count",
            "allocation_row_count",
            "allocated_count",
            "capped_count",
            "no_budget_count",
            "non_recommend_count",
            "skipped_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "total_requested_paper_notional",
            "total_allocated_paper_notional",
            "remaining_paper_budget",
            "total_paper_budget",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "budget_utilization",
            "requested_fill_ratio",
            "allocated_row_share",
            "capped_row_share",
            "no_budget_row_share",
            "non_recommend_row_share",
            "skipped_row_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("snapshot summary", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_proposal_status: str | None
    latest_allocation_input_count: int | None
    latest_allocation_row_count: int | None
    latest_allocated_count: int | None
    latest_capped_count: int | None
    latest_no_budget_count: int | None
    latest_non_recommend_count: int | None
    latest_skipped_count: int | None
    first_allocated_count: int | None
    delta_allocated_count: int | None
    latest_total_requested_paper_notional: Decimal | None
    latest_total_allocated_paper_notional: Decimal | None
    latest_remaining_paper_budget: Decimal | None
    latest_total_paper_budget: Decimal | None
    latest_budget_utilization: Decimal | None
    latest_requested_fill_ratio: Decimal | None
    latest_allocated_row_share: Decimal | None
    latest_capped_row_share: Decimal | None
    latest_no_budget_row_share: Decimal | None
    latest_non_recommend_row_share: Decimal | None
    latest_skipped_row_share: Decimal | None
    first_total_requested_paper_notional: Decimal | None
    delta_total_requested_paper_notional: Decimal | None
    first_total_allocated_paper_notional: Decimal | None
    delta_total_allocated_paper_notional: Decimal | None
    first_budget_utilization: Decimal | None
    delta_budget_utilization: Decimal | None
    first_requested_fill_ratio: Decimal | None
    delta_requested_fill_ratio: Decimal | None
    latest_largest_concentration_rows: tuple[
        PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow,
        ...,
    ]
    latest_cap_reason_rows: tuple[
        PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow,
        ...,
    ]
    latest_added_market_side_count: int
    latest_removed_market_side_count: int
    latest_persisted_market_side_count: int
    latest_notional_turnover: Decimal
    latest_allocated_edge_count: int | None
    latest_allocated_edge_share: Decimal | None
    latest_expected_edge_notional: Decimal | None
    latest_expected_edge_notional_share: Decimal | None
    source_summaries: tuple[
        PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        for field_name in ("first_report_generated_at", "latest_report_generated_at"):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        if self.latest_proposal_status is not None:
            _require_proposal_status("latest_proposal_status", self.latest_proposal_status)
        for field_name in (
            "latest_allocation_input_count",
            "latest_allocation_row_count",
            "latest_allocated_count",
            "latest_capped_count",
            "latest_no_budget_count",
            "latest_non_recommend_count",
            "latest_skipped_count",
            "first_allocated_count",
            "latest_allocated_edge_count",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        if self.delta_allocated_count is not None:
            _require_int("delta_allocated_count", self.delta_allocated_count)
        for field_name in (
            "latest_total_requested_paper_notional",
            "latest_total_allocated_paper_notional",
            "latest_remaining_paper_budget",
            "latest_total_paper_budget",
            "latest_budget_utilization",
            "latest_requested_fill_ratio",
            "latest_allocated_row_share",
            "latest_capped_row_share",
            "latest_no_budget_row_share",
            "latest_non_recommend_row_share",
            "latest_skipped_row_share",
            "first_total_requested_paper_notional",
            "delta_total_requested_paper_notional",
            "first_total_allocated_paper_notional",
            "delta_total_allocated_paper_notional",
            "first_budget_utilization",
            "delta_budget_utilization",
            "first_requested_fill_ratio",
            "delta_requested_fill_ratio",
            "latest_allocated_edge_share",
            "latest_expected_edge_notional",
            "latest_expected_edge_notional_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_largest_concentration_rows",
            _normalize_concentration_rows(self.latest_largest_concentration_rows),
        )
        object.__setattr__(
            self,
            "latest_cap_reason_rows",
            _normalize_cap_reason_rows(self.latest_cap_reason_rows),
        )
        for field_name in (
            "latest_added_market_side_count",
            "latest_removed_market_side_count",
            "latest_persisted_market_side_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_notional_turnover",
            _normalize_decimal("latest_notional_turnover", self.latest_notional_turnover),
        )
        object.__setattr__(
            self,
            "source_summaries",
            _normalize_snapshot_summaries(self.source_summaries),
        )
        _require_hard_flags("metrics report", self)


def build_paper_autonomous_allocation_proposal_db_history_metrics_report(
    proposal_reports: object,
    *,
    config: PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsReport:
    if type(config) is not PaperAutonomousAllocationProposalDbHistoryMetricsConfig:
        raise ValueError(
            "config must be a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    reports = _chronological_reports(_normalize_proposal_reports(proposal_reports))
    summaries = tuple(
        _snapshot_summary(report=report, input_position=input_position)
        for input_position, report in reports
    )
    source_summaries = tuple(summary for _position, summary in summaries)

    if not source_summaries:
        return _empty_report(config=config, generated_at=generated_at_utc)

    first = source_summaries[0]
    latest = source_summaries[-1]
    latest_report = reports[-1][1]
    previous_report = reports[-2][1] if len(reports) >= 2 else None
    churn = _churn_metrics(previous_report, latest_report)
    edge = _edge_metrics(latest_report)

    return PaperAutonomousAllocationProposalDbHistoryMetricsReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_report_count=len(source_summaries),
        first_report_generated_at=first.generated_at,
        latest_report_generated_at=latest.generated_at,
        latest_proposal_status=latest.proposal_status,
        latest_allocation_input_count=latest.allocation_input_count,
        latest_allocation_row_count=latest.allocation_row_count,
        latest_allocated_count=latest.allocated_count,
        latest_capped_count=latest.capped_count,
        latest_no_budget_count=latest.no_budget_count,
        latest_non_recommend_count=latest.non_recommend_count,
        latest_skipped_count=latest.skipped_count,
        first_allocated_count=first.allocated_count,
        delta_allocated_count=latest.allocated_count - first.allocated_count,
        latest_total_requested_paper_notional=latest.total_requested_paper_notional,
        latest_total_allocated_paper_notional=latest.total_allocated_paper_notional,
        latest_remaining_paper_budget=latest.remaining_paper_budget,
        latest_total_paper_budget=latest.total_paper_budget,
        latest_budget_utilization=latest.budget_utilization,
        latest_requested_fill_ratio=latest.requested_fill_ratio,
        latest_allocated_row_share=latest.allocated_row_share,
        latest_capped_row_share=latest.capped_row_share,
        latest_no_budget_row_share=latest.no_budget_row_share,
        latest_non_recommend_row_share=latest.non_recommend_row_share,
        latest_skipped_row_share=latest.skipped_row_share,
        first_total_requested_paper_notional=first.total_requested_paper_notional,
        delta_total_requested_paper_notional=_decimal_delta(
            first.total_requested_paper_notional,
            latest.total_requested_paper_notional,
        ),
        first_total_allocated_paper_notional=first.total_allocated_paper_notional,
        delta_total_allocated_paper_notional=_decimal_delta(
            first.total_allocated_paper_notional,
            latest.total_allocated_paper_notional,
        ),
        first_budget_utilization=first.budget_utilization,
        delta_budget_utilization=_decimal_delta(
            first.budget_utilization,
            latest.budget_utilization,
        ),
        first_requested_fill_ratio=first.requested_fill_ratio,
        delta_requested_fill_ratio=_decimal_delta(
            first.requested_fill_ratio,
            latest.requested_fill_ratio,
        ),
        latest_largest_concentration_rows=_largest_concentration_rows(latest_report),
        latest_cap_reason_rows=_cap_reason_rows(latest_report),
        latest_added_market_side_count=churn[0],
        latest_removed_market_side_count=churn[1],
        latest_persisted_market_side_count=churn[2],
        latest_notional_turnover=churn[3],
        latest_allocated_edge_count=edge[0],
        latest_allocated_edge_share=edge[1],
        latest_expected_edge_notional=edge[2],
        latest_expected_edge_notional_share=edge[3],
        source_summaries=source_summaries,
    )


def _empty_report(
    *,
    config: PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsReport:
    return PaperAutonomousAllocationProposalDbHistoryMetricsReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_report_count=0,
        first_report_generated_at=None,
        latest_report_generated_at=None,
        latest_proposal_status=None,
        latest_allocation_input_count=None,
        latest_allocation_row_count=None,
        latest_allocated_count=None,
        latest_capped_count=None,
        latest_no_budget_count=None,
        latest_non_recommend_count=None,
        latest_skipped_count=None,
        first_allocated_count=None,
        delta_allocated_count=None,
        latest_total_requested_paper_notional=None,
        latest_total_allocated_paper_notional=None,
        latest_remaining_paper_budget=None,
        latest_total_paper_budget=None,
        latest_budget_utilization=None,
        latest_requested_fill_ratio=None,
        latest_allocated_row_share=None,
        latest_capped_row_share=None,
        latest_no_budget_row_share=None,
        latest_non_recommend_row_share=None,
        latest_skipped_row_share=None,
        first_total_requested_paper_notional=None,
        delta_total_requested_paper_notional=None,
        first_total_allocated_paper_notional=None,
        delta_total_allocated_paper_notional=None,
        first_budget_utilization=None,
        delta_budget_utilization=None,
        first_requested_fill_ratio=None,
        delta_requested_fill_ratio=None,
        latest_largest_concentration_rows=(),
        latest_cap_reason_rows=(),
        latest_added_market_side_count=0,
        latest_removed_market_side_count=0,
        latest_persisted_market_side_count=0,
        latest_notional_turnover=ZERO,
        latest_allocated_edge_count=None,
        latest_allocated_edge_share=None,
        latest_expected_edge_notional=None,
        latest_expected_edge_notional_share=None,
        source_summaries=(),
    )


def _normalize_proposal_reports(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalReport, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("proposal_reports must be an iterable")
    try:
        reports = tuple(value)
    except TypeError as exc:
        raise ValueError("proposal_reports must be an iterable") from exc
    for report in reports:
        if type(report) is not PaperAutonomousAllocationProposalReport:
            raise ValueError(
                "proposal_reports must contain "
                "PaperAutonomousAllocationProposalReport values",
            )
        _require_hard_flags("proposal report", report)
        _require_hard_flags("allocation report", report.allocation_report)
        for row in report.allocation_report.rows:
            _require_hard_flags("allocation row", row)
    return reports


def _chronological_reports(
    reports: tuple[PaperAutonomousAllocationProposalReport, ...],
) -> tuple[tuple[int, PaperAutonomousAllocationProposalReport], ...]:
    return tuple(
        sorted(
            enumerate(reports),
            key=lambda item: (_as_utc("report generated_at", item[1].generated_at), item[0]),
        ),
    )


def _snapshot_summary(
    *,
    report: PaperAutonomousAllocationProposalReport,
    input_position: int,
) -> tuple[int, PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary]:
    allocation_report = report.allocation_report
    row_count = allocation_report.row_count
    summary = PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary(
        input_position=input_position,
        generated_at=report.generated_at,
        proposal_status=report.proposal_status,
        allocation_input_count=report.allocation_input_count,
        allocation_row_count=row_count,
        allocated_count=allocation_report.allocated_count,
        capped_count=allocation_report.capped_count,
        no_budget_count=allocation_report.no_budget_count,
        non_recommend_count=allocation_report.non_recommend_count,
        skipped_count=allocation_report.skipped_count,
        total_requested_paper_notional=allocation_report.total_requested_paper_notional,
        total_allocated_paper_notional=allocation_report.total_allocated_paper_notional,
        remaining_paper_budget=allocation_report.remaining_paper_budget,
        total_paper_budget=allocation_report.total_paper_budget,
        budget_utilization=_optional_ratio(
            allocation_report.total_allocated_paper_notional,
            allocation_report.total_paper_budget,
        ),
        requested_fill_ratio=_optional_ratio(
            allocation_report.total_allocated_paper_notional,
            allocation_report.total_requested_paper_notional,
        ),
        allocated_row_share=_optional_ratio(
            _decimal_from_int(allocation_report.allocated_count),
            _decimal_from_int(row_count),
        ),
        capped_row_share=_optional_ratio(
            _decimal_from_int(allocation_report.capped_count),
            _decimal_from_int(row_count),
        ),
        no_budget_row_share=_optional_ratio(
            _decimal_from_int(allocation_report.no_budget_count),
            _decimal_from_int(row_count),
        ),
        non_recommend_row_share=_optional_ratio(
            _decimal_from_int(allocation_report.non_recommend_count),
            _decimal_from_int(row_count),
        ),
        skipped_row_share=_optional_ratio(
            _decimal_from_int(allocation_report.skipped_count),
            _decimal_from_int(row_count),
        ),
    )
    return input_position, summary


def _largest_concentration_rows(
    report: PaperAutonomousAllocationProposalReport,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow, ...]:
    total_allocated = report.allocation_report.total_allocated_paper_notional
    grouped: dict[tuple[str, str], tuple[Decimal, int]] = {}
    for row in report.allocation_report.rows:
        for group_type, group_id in _row_group_keys(row):
            key = (group_type, group_id)
            current_notional, current_count = grouped.get(key, (ZERO, 0))
            grouped[key] = (
                _add_decimal(current_notional, row.allocated_paper_notional),
                current_count + 1,
            )

    rows = tuple(
        PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow(
            group_type=group_type,
            group_id=group_id,
            allocated_paper_notional=allocated_paper_notional,
            allocated_paper_notional_share=_optional_ratio(
                allocated_paper_notional,
                total_allocated,
            ),
            row_count=row_count,
        )
        for (group_type, group_id), (allocated_paper_notional, row_count) in grouped.items()
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.group_type,
                -row.allocated_paper_notional,
                row.group_id,
            ),
        ),
    )
    largest_by_group: dict[str, PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow] = {}
    for row in sorted_rows:
        if row.group_type not in largest_by_group:
            largest_by_group[row.group_type] = row
    return tuple(largest_by_group[group_type] for group_type in GROUP_TYPES if group_type in largest_by_group)


def _row_group_keys(row: object) -> tuple[tuple[str, str], ...]:
    keys = (("market", row.market_slug),)
    if row.event_id is not None:
        keys = (*keys, ("event", row.event_id))
    if row.theme_id is not None:
        keys = (*keys, ("theme", row.theme_id))
    if row.correlation_group is not None:
        keys = (*keys, ("correlation_group", row.correlation_group))
    return keys


def _cap_reason_rows(
    report: PaperAutonomousAllocationProposalReport,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow, ...]:
    counts: dict[str, int] = {}
    notionals: dict[str, Decimal] = {}
    for row in report.allocation_report.rows:
        for reason_code in set(row.reason_codes):
            if reason_code not in CAP_REASON_CODES:
                continue
            counts[reason_code] = counts.get(reason_code, 0) + 1
            notionals[reason_code] = _add_decimal(
                notionals.get(reason_code, ZERO),
                row.allocated_paper_notional,
            )
    return tuple(
        PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow(
            reason_code=reason_code,
            row_count=row_count,
            allocated_paper_notional=notionals[reason_code],
        )
        for reason_code, row_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _churn_metrics(
    previous_report: PaperAutonomousAllocationProposalReport | None,
    latest_report: PaperAutonomousAllocationProposalReport,
) -> tuple[int, int, int, Decimal]:
    if previous_report is None:
        return 0, 0, 0, ZERO
    previous = _allocated_market_side_notional(previous_report)
    latest = _allocated_market_side_notional(latest_report)
    previous_keys = set(previous)
    latest_keys = set(latest)
    added = latest_keys - previous_keys
    removed = previous_keys - latest_keys
    persisted = previous_keys & latest_keys
    turnover = ZERO
    for key in previous_keys | latest_keys:
        turnover = _add_decimal(
            turnover,
            _abs_decimal_delta(previous.get(key, ZERO), latest.get(key, ZERO)),
        )
    return len(added), len(removed), len(persisted), turnover


def _allocated_market_side_notional(
    report: PaperAutonomousAllocationProposalReport,
) -> dict[tuple[str, str], Decimal]:
    values: dict[tuple[str, str], Decimal] = {}
    for row in report.allocation_report.rows:
        if row.allocated_paper_notional <= ZERO:
            continue
        key = (row.market_slug, row.side)
        values[key] = _add_decimal(values.get(key, ZERO), row.allocated_paper_notional)
    return values


def _edge_metrics(
    report: PaperAutonomousAllocationProposalReport,
) -> tuple[int, Decimal | None, Decimal | None, Decimal | None]:
    allocated_count = report.allocation_report.allocated_count
    edge_count = 0
    expected_notional = ZERO
    for row in report.allocation_report.rows:
        if row.cap_status != "allocated":
            continue
        if row.net_probability_edge is None:
            continue
        edge_count += 1
        expected_notional = _add_decimal(
            expected_notional,
            _multiply_decimal(row.allocated_paper_notional, row.net_probability_edge),
        )
    edge_share = _optional_ratio(_decimal_from_int(edge_count), _decimal_from_int(allocated_count))
    if edge_count == 0:
        return edge_count, edge_share, None, None
    expected_share = _optional_ratio(
        expected_notional,
        report.allocation_report.total_allocated_paper_notional,
    )
    return edge_count, edge_share, expected_notional, expected_share


def _decimal_delta(left: Decimal | None, right: Decimal | None) -> Decimal | None:
    if left is None or right is None:
        return None
    return _subtract_decimal(right, left)


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _abs_decimal_delta(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(left - right))


def _decimal_from_int(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_decimal(field_name, value)


def _normalize_concentration_rows(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow, ...]:
    rows = _tuple_from_iterable(value, "latest_largest_concentration_rows")
    for row in rows:
        if type(row) is not PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow:
            raise ValueError("latest_largest_concentration_rows must contain exact rows")
    return rows


def _normalize_cap_reason_rows(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow, ...]:
    rows = _tuple_from_iterable(value, "latest_cap_reason_rows")
    for row in rows:
        if type(row) is not PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow:
            raise ValueError("latest_cap_reason_rows must contain exact rows")
    return rows


def _normalize_snapshot_summaries(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary, ...]:
    summaries = _tuple_from_iterable(value, "source_summaries")
    for summary in summaries:
        if type(summary) is not PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary:
            raise ValueError("source_summaries must contain exact summaries")
    return summaries


def _tuple_from_iterable(value: object, field_name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        return tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone aware")
    return value.astimezone(UTC)


def _require_proposal_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PROPOSAL_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")

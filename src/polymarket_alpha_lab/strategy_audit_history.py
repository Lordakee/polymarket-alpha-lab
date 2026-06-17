"""Paper-only Strategy Risk Audit history summaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)

__all__ = (
    "PaperStrategyRiskAuditHistoryConfig",
    "PaperStrategyRiskAuditHistoryGateStatusSummary",
    "PaperStrategyRiskAuditHistoryReport",
    "PaperStrategyRiskAuditHistoryStatusRow",
    "build_paper_strategy_risk_audit_history_report",
)


RATIO_QUANTUM = Decimal("0.0001")
AUDIT_STATUSES = (
    "audit_ready",
    "insufficient_evidence",
    "blocked_by_risk",
)
GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
HISTORY_STATUSES = (
    "empty_audit_history",
    "latest_audit_ready",
    "latest_insufficient_evidence",
    "latest_blocked_by_risk",
)


@dataclass(frozen=True)
class PaperStrategyRiskAuditHistoryConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperStrategyRiskAuditHistoryStatusRow:
    audit_status: str
    audit_count: int
    audit_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.audit_status not in AUDIT_STATUSES:
            raise ValueError("audit_status must be a known audit status")
        _require_nonnegative_int("audit_count", self.audit_count)
        _require_optional_probability_decimal("audit_ratio", self.audit_ratio)


@dataclass(frozen=True)
class PaperStrategyRiskAuditHistoryGateStatusSummary:
    gate_name: str
    gate_status: str
    audit_count: int
    audit_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known audit gate")
        if self.gate_status not in GATE_STATUSES:
            raise ValueError("gate_status must be a known gate status")
        _require_nonnegative_int("audit_count", self.audit_count)
        _require_optional_probability_decimal("audit_ratio", self.audit_ratio)


@dataclass(frozen=True)
class PaperStrategyRiskAuditHistoryReport:
    generated_at: datetime
    config_version: str
    status: str
    audit_report_count: int
    audit_ready_count: int
    insufficient_evidence_count: int
    blocked_by_risk_count: int
    latest_audit_status: str | None
    first_audit_generated_at: datetime | None
    latest_audit_generated_at: datetime | None
    latest_pass_count: int
    latest_fail_count: int
    latest_incomplete_count: int
    consecutive_non_ready_count: int
    consecutive_blocked_by_risk_count: int
    consecutive_insufficient_evidence_count: int
    latest_failed_gate_names: tuple[str, ...]
    latest_incomplete_gate_names: tuple[str, ...]
    status_rows: tuple[PaperStrategyRiskAuditHistoryStatusRow, ...]
    gate_status_summaries: tuple[PaperStrategyRiskAuditHistoryGateStatusSummary, ...]
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_audit_generated_at",
            _as_optional_utc(self.first_audit_generated_at),
        )
        object.__setattr__(
            self,
            "latest_audit_generated_at",
            _as_optional_utc(self.latest_audit_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.status not in HISTORY_STATUSES:
            raise ValueError("status must be a known audit history status")
        if self.latest_audit_status is not None and (
            self.latest_audit_status not in AUDIT_STATUSES
        ):
            raise ValueError("latest_audit_status must be a known audit status")
        for field_name in (
            "audit_report_count",
            "audit_ready_count",
            "insufficient_evidence_count",
            "blocked_by_risk_count",
            "latest_pass_count",
            "latest_fail_count",
            "latest_incomplete_count",
            "consecutive_non_ready_count",
            "consecutive_blocked_by_risk_count",
            "consecutive_insufficient_evidence_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_failed_gate_names",
            _normalize_gate_name_tuple(
                "latest_failed_gate_names",
                self.latest_failed_gate_names,
            ),
        )
        object.__setattr__(
            self,
            "latest_incomplete_gate_names",
            _normalize_gate_name_tuple(
                "latest_incomplete_gate_names",
                self.latest_incomplete_gate_names,
            ),
        )
        object.__setattr__(
            self,
            "status_rows",
            _normalize_status_rows(self.status_rows),
        )
        object.__setattr__(
            self,
            "gate_status_summaries",
            _normalize_gate_status_summaries(self.gate_status_summaries),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


def build_paper_strategy_risk_audit_history_report(
    audit_reports: list[PaperStrategyRiskAuditReport]
    | tuple[PaperStrategyRiskAuditReport, ...],
    *,
    config: PaperStrategyRiskAuditHistoryConfig,
    generated_at: datetime,
) -> PaperStrategyRiskAuditHistoryReport:
    if type(config) is not PaperStrategyRiskAuditHistoryConfig:
        raise ValueError("config must be a PaperStrategyRiskAuditHistoryConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    reports = _normalize_audit_reports(audit_reports)
    report_count = len(reports)
    status_counts = _status_counts(reports)
    latest = reports[-1] if reports else None
    latest_status = latest.status if latest is not None else None

    return PaperStrategyRiskAuditHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_history_status(latest_status),
        audit_report_count=report_count,
        audit_ready_count=status_counts["audit_ready"],
        insufficient_evidence_count=status_counts["insufficient_evidence"],
        blocked_by_risk_count=status_counts["blocked_by_risk"],
        latest_audit_status=latest_status,
        first_audit_generated_at=reports[0].generated_at if reports else None,
        latest_audit_generated_at=latest.generated_at if latest is not None else None,
        latest_pass_count=latest.pass_count if latest is not None else 0,
        latest_fail_count=latest.fail_count if latest is not None else 0,
        latest_incomplete_count=latest.incomplete_count if latest is not None else 0,
        consecutive_non_ready_count=_consecutive_count(
            reports,
            lambda report: report.status != "audit_ready",
        ),
        consecutive_blocked_by_risk_count=_consecutive_count(
            reports,
            lambda report: report.status == "blocked_by_risk",
        ),
        consecutive_insufficient_evidence_count=_consecutive_count(
            reports,
            lambda report: report.status == "insufficient_evidence",
        ),
        latest_failed_gate_names=_latest_gate_names(latest, "fail"),
        latest_incomplete_gate_names=_latest_gate_names(latest, "incomplete"),
        status_rows=_build_status_rows(status_counts, report_count),
        gate_status_summaries=_build_gate_status_summaries(reports),
    )


def _normalize_audit_reports(
    audit_reports: list[PaperStrategyRiskAuditReport]
    | tuple[PaperStrategyRiskAuditReport, ...],
) -> tuple[PaperStrategyRiskAuditReport, ...]:
    if type(audit_reports) not in (list, tuple):
        raise ValueError("audit_reports must be a list or tuple")
    return tuple(_clone_audit_report(report) for report in audit_reports)


def _clone_audit_report(
    report: PaperStrategyRiskAuditReport,
) -> PaperStrategyRiskAuditReport:
    if type(report) is not PaperStrategyRiskAuditReport:
        raise ValueError("audit_reports must contain PaperStrategyRiskAuditReport values")
    gate_results = tuple(
        PaperStrategyRiskAuditGateResult(
            gate_name=gate.gate_name,
            status=gate.status,
            message=gate.message,
            observed_value=gate.observed_value,
            threshold=gate.threshold,
        )
        for gate in report.gate_results
    )
    return PaperStrategyRiskAuditReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        gate_count=report.gate_count,
        pass_count=report.pass_count,
        fail_count=report.fail_count,
        incomplete_count=report.incomplete_count,
        gate_results=gate_results,
        paper_only=report.paper_only,
        report_only=report.report_only,
    )


def _status_counts(
    reports: tuple[PaperStrategyRiskAuditReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in AUDIT_STATUSES}
    for report in reports:
        counts[report.status] += 1
    return counts


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[PaperStrategyRiskAuditHistoryStatusRow, ...]:
    return tuple(
        PaperStrategyRiskAuditHistoryStatusRow(
            audit_status=status,
            audit_count=status_counts[status],
            audit_ratio=_ratio(status_counts[status], total),
        )
        for status in AUDIT_STATUSES
    )


def _build_gate_status_summaries(
    reports: tuple[PaperStrategyRiskAuditReport, ...],
) -> tuple[PaperStrategyRiskAuditHistoryGateStatusSummary, ...]:
    counts = {
        (gate_name, gate_status): 0
        for gate_name in GATE_NAMES
        for gate_status in GATE_STATUSES
    }
    for report in reports:
        for gate in report.gate_results:
            counts[(gate.gate_name, gate.status)] += 1
    return tuple(
        PaperStrategyRiskAuditHistoryGateStatusSummary(
            gate_name=gate_name,
            gate_status=gate_status,
            audit_count=counts[(gate_name, gate_status)],
            audit_ratio=_ratio(counts[(gate_name, gate_status)], len(reports)),
        )
        for gate_name in GATE_NAMES
        for gate_status in GATE_STATUSES
    )


def _history_status(latest_status: str | None) -> str:
    if latest_status is None:
        return "empty_audit_history"
    if latest_status == "audit_ready":
        return "latest_audit_ready"
    if latest_status == "insufficient_evidence":
        return "latest_insufficient_evidence"
    if latest_status == "blocked_by_risk":
        return "latest_blocked_by_risk"
    raise ValueError("latest_status must be a known audit status")


def _latest_gate_names(
    latest: PaperStrategyRiskAuditReport | None,
    status: str,
) -> tuple[str, ...]:
    if latest is None:
        return ()
    return tuple(gate.gate_name for gate in latest.gate_results if gate.status == status)


def _consecutive_count(
    reports: tuple[PaperStrategyRiskAuditReport, ...],
    predicate: Any,
) -> int:
    count = 0
    for report in reversed(reports):
        if not predicate(report):
            break
        count += 1
    return count


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _validate_report_consistency(report: PaperStrategyRiskAuditHistoryReport) -> None:
    if report.status != _history_status(report.latest_audit_status):
        raise ValueError("status must match latest_audit_status")
    if (
        report.audit_ready_count
        + report.insufficient_evidence_count
        + report.blocked_by_risk_count
        != report.audit_report_count
    ):
        raise ValueError("audit status counts must sum to audit_report_count")
    if report.audit_report_count == 0:
        if report.latest_audit_status is not None:
            raise ValueError("latest_audit_status must be absent without reports")
        if (
            report.first_audit_generated_at is not None
            or report.latest_audit_generated_at is not None
        ):
            raise ValueError("audit timestamp bounds must be absent without reports")
        if (
            report.latest_pass_count != 0
            or report.latest_fail_count != 0
            or report.latest_incomplete_count != 0
        ):
            raise ValueError("latest gate counts must be zero without reports")
        if (
            report.consecutive_non_ready_count != 0
            or report.consecutive_blocked_by_risk_count != 0
            or report.consecutive_insufficient_evidence_count != 0
        ):
            raise ValueError("consecutive counts must be zero without reports")
        if report.latest_failed_gate_names or report.latest_incomplete_gate_names:
            raise ValueError("latest gate names must be absent without reports")
    else:
        if report.latest_audit_status is None:
            raise ValueError("latest_audit_status is required with reports")
        if (
            report.first_audit_generated_at is None
            or report.latest_audit_generated_at is None
        ):
            raise ValueError("audit timestamp bounds are required with reports")
        if (
            report.latest_pass_count
            + report.latest_fail_count
            + report.latest_incomplete_count
            != len(GATE_NAMES)
        ):
            raise ValueError("latest gate counts must cover all audit gates")
        if len(report.latest_failed_gate_names) != report.latest_fail_count:
            raise ValueError("latest_failed_gate_names must match latest_fail_count")
        if len(report.latest_incomplete_gate_names) != report.latest_incomplete_count:
            raise ValueError(
                "latest_incomplete_gate_names must match latest_incomplete_count",
            )
        if set(report.latest_failed_gate_names).intersection(
            report.latest_incomplete_gate_names,
        ):
            raise ValueError("latest failed and incomplete gate names must be disjoint")
        _validate_consecutive_counts(report)
    if tuple(row.audit_status for row in report.status_rows) != AUDIT_STATUSES:
        raise ValueError("status_rows must cover known audit statuses")
    row_counts = {row.audit_status: row.audit_count for row in report.status_rows}
    if row_counts != {
        "audit_ready": report.audit_ready_count,
        "insufficient_evidence": report.insufficient_evidence_count,
        "blocked_by_risk": report.blocked_by_risk_count,
    }:
        raise ValueError("status_rows must match audit counts")
    for row in report.status_rows:
        if row.audit_ratio != _ratio(row.audit_count, report.audit_report_count):
            raise ValueError("status_rows ratios must match audit counts")
    expected_gate_keys = tuple(
        (gate_name, gate_status)
        for gate_name in GATE_NAMES
        for gate_status in GATE_STATUSES
    )
    actual_gate_keys = tuple(
        (row.gate_name, row.gate_status) for row in report.gate_status_summaries
    )
    if actual_gate_keys != expected_gate_keys:
        raise ValueError("gate_status_summaries must cover all audit gate statuses")
    _validate_gate_status_summary_counts(report)


def _validate_consecutive_counts(
    report: PaperStrategyRiskAuditHistoryReport,
) -> None:
    if (
        report.consecutive_non_ready_count > report.audit_report_count
        or report.consecutive_blocked_by_risk_count > report.audit_report_count
        or report.consecutive_insufficient_evidence_count > report.audit_report_count
    ):
        raise ValueError("consecutive counts must not exceed audit_report_count")
    if report.latest_audit_status == "audit_ready":
        if (
            report.consecutive_non_ready_count != 0
            or report.consecutive_blocked_by_risk_count != 0
            or report.consecutive_insufficient_evidence_count != 0
        ):
            raise ValueError("ready audits must have zero non-ready streaks")
    elif report.latest_audit_status == "blocked_by_risk":
        if report.consecutive_blocked_by_risk_count < 1:
            raise ValueError("blocked latest audit requires blocked streak")
        if report.consecutive_insufficient_evidence_count != 0:
            raise ValueError("blocked latest audit cannot have incomplete streak")
        if (
            report.consecutive_non_ready_count
            < report.consecutive_blocked_by_risk_count
        ):
            raise ValueError("non-ready streak must cover blocked streak")
    elif report.latest_audit_status == "insufficient_evidence":
        if report.consecutive_insufficient_evidence_count < 1:
            raise ValueError("incomplete latest audit requires incomplete streak")
        if report.consecutive_blocked_by_risk_count != 0:
            raise ValueError("incomplete latest audit cannot have blocked streak")
        if (
            report.consecutive_non_ready_count
            < report.consecutive_insufficient_evidence_count
        ):
            raise ValueError("non-ready streak must cover incomplete streak")


def _validate_gate_status_summary_counts(
    report: PaperStrategyRiskAuditHistoryReport,
) -> None:
    rows_by_gate = {gate_name: [] for gate_name in GATE_NAMES}
    for row in report.gate_status_summaries:
        if row.audit_ratio != _ratio(row.audit_count, report.audit_report_count):
            raise ValueError("gate_status_summaries ratios must match audit counts")
        rows_by_gate[row.gate_name].append(row)
    for gate_name, rows in rows_by_gate.items():
        if sum(row.audit_count for row in rows) != report.audit_report_count:
            raise ValueError(
                f"gate_status_summaries counts must sum to audit_report_count "
                f"for {gate_name}",
            )


def _normalize_status_rows(
    rows: tuple[PaperStrategyRiskAuditHistoryStatusRow, ...],
) -> tuple[PaperStrategyRiskAuditHistoryStatusRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("status_rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("status_rows must be an iterable") from exc
    for row in items:
        if type(row) is not PaperStrategyRiskAuditHistoryStatusRow:
            raise ValueError("status_rows must contain history status rows")
    return items


def _normalize_gate_status_summaries(
    rows: tuple[PaperStrategyRiskAuditHistoryGateStatusSummary, ...],
) -> tuple[PaperStrategyRiskAuditHistoryGateStatusSummary, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("gate_status_summaries must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("gate_status_summaries must be an iterable") from exc
    for row in items:
        if type(row) is not PaperStrategyRiskAuditHistoryGateStatusSummary:
            raise ValueError("gate_status_summaries must contain gate status summaries")
    return items


def _normalize_gate_name_tuple(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for item in items:
        if item not in GATE_NAMES:
            raise ValueError(f"{field_name} must contain known gate names")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return items


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    return None if value is None else _as_utc(value)


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


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be between zero and one")

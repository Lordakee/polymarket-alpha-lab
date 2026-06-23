"""Pure DB readback reducer for paper operator-flow report history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polymarket_alpha_lab.paper_research_packet_operator_flow import (
    FLOW_STATUSES,
    PaperResearchPacketOperatorFlowReport,
)


__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_CONFIG_VERSION",
    "PaperResearchPacketOperatorFlowDbHistoryConfig",
    "PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow",
    "PaperResearchPacketOperatorFlowDbHistoryReport",
    "PaperResearchPacketOperatorFlowDbHistoryStatusRow",
    "build_paper_research_packet_operator_flow_db_history_report",
)


DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_CONFIG_VERSION = (
    "paper-research-packet-operator-flow-db-history-v0"
)


@dataclass(frozen=True)
class PaperResearchPacketOperatorFlowDbHistoryConfig:
    config_version: str = (
        DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_CONFIG_VERSION
    )
    min_report_count: int = 3
    max_blocked_flow_report_count: int = 0
    max_watch_flow_report_count: int = 0
    max_duplicate_generated_at_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_report_count", self.min_report_count)
        for field_name in (
            "max_blocked_flow_report_count",
            "max_watch_flow_report_count",
            "max_duplicate_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperResearchPacketOperatorFlowDbHistoryStatusRow:
    flow_status: str
    status_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_flow_status("flow_status", self.flow_status)
        _require_nonnegative_int("status_count", self.status_count)
        _validate_hard_flags("status row", self)


@dataclass(frozen=True)
class PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code row", self)


@dataclass(frozen=True)
class PaperResearchPacketOperatorFlowDbHistoryReport:
    generated_at: datetime
    config_version: str
    history_status: str
    report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_flow_status: str | None
    latest_packet_row_count: int | None
    latest_quality_status: str | None
    latest_history_status: str | None
    flow_status_rows: tuple[
        PaperResearchPacketOperatorFlowDbHistoryStatusRow,
        ...,
    ]
    duplicate_generated_at_count: int
    consecutive_latest_pass_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    latest_reason_codes: tuple[str, ...]
    reason_code_rows: tuple[
        PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_flow_status("history_status", self.history_status)
        _require_nonnegative_int("report_count", self.report_count)
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
        if self.latest_flow_status is not None:
            _require_flow_status("latest_flow_status", self.latest_flow_status)
        _require_optional_nonnegative_int(
            "latest_packet_row_count",
            self.latest_packet_row_count,
        )
        if self.latest_quality_status is not None:
            _require_flow_status("latest_quality_status", self.latest_quality_status)
        if self.latest_history_status is not None:
            _require_flow_status("latest_history_status", self.latest_history_status)
        object.__setattr__(
            self,
            "flow_status_rows",
            _normalize_status_rows(self.flow_status_rows),
        )
        _require_nonnegative_int(
            "duplicate_generated_at_count",
            self.duplicate_generated_at_count,
        )
        for field_name in (
            "consecutive_latest_pass_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_reason_codes",
            _normalize_reason_codes(
                "latest_reason_codes",
                self.latest_reason_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_rows",
            _normalize_reason_code_rows(self.reason_code_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_history_report(self)
        _validate_hard_flags("history report", self)


def build_paper_research_packet_operator_flow_db_history_report(
    operator_flow_reports: object,
    *,
    config: PaperResearchPacketOperatorFlowDbHistoryConfig,
    generated_at: datetime,
) -> PaperResearchPacketOperatorFlowDbHistoryReport:
    """Reduce paper operator-flow reports into deterministic history metrics."""

    if type(config) is not PaperResearchPacketOperatorFlowDbHistoryConfig:
        raise ValueError(
            "config must be a PaperResearchPacketOperatorFlowDbHistoryConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _validate_hard_flags("config", config)

    reports = _normalize_operator_flow_reports(operator_flow_reports)
    chronological_reports = _chronological_reports(reports)
    flow_status_rows = _flow_status_rows(chronological_reports)
    duplicate_generated_at_count = _duplicate_generated_at_count(
        chronological_reports,
    )
    latest = chronological_reports[-1] if chronological_reports else None

    return PaperResearchPacketOperatorFlowDbHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        history_status=_history_status(
            reports=chronological_reports,
            flow_status_rows=flow_status_rows,
            duplicate_generated_at_count=duplicate_generated_at_count,
            config=config,
        ),
        report_count=len(chronological_reports),
        first_report_generated_at=(
            _as_utc("report generated_at", chronological_reports[0].generated_at)
            if chronological_reports
            else None
        ),
        latest_report_generated_at=(
            _as_utc("report generated_at", latest.generated_at)
            if latest is not None
            else None
        ),
        latest_flow_status=latest.flow_status if latest is not None else None,
        latest_packet_row_count=latest.packet_row_count if latest is not None else None,
        latest_quality_status=latest.quality_status if latest is not None else None,
        latest_history_status=latest.history_status if latest is not None else None,
        flow_status_rows=flow_status_rows,
        duplicate_generated_at_count=duplicate_generated_at_count,
        consecutive_latest_pass_count=_consecutive_latest_status_count(
            chronological_reports,
            "pass",
        ),
        consecutive_latest_watch_count=_consecutive_latest_status_count(
            chronological_reports,
            "watch",
        ),
        consecutive_latest_blocked_count=_consecutive_latest_status_count(
            chronological_reports,
            "blocked",
        ),
        latest_reason_codes=latest.reason_codes if latest is not None else (),
        reason_code_rows=_reason_code_rows(chronological_reports),
        reason_codes=_history_reason_codes(
            reports=chronological_reports,
            flow_status_rows=flow_status_rows,
            duplicate_generated_at_count=duplicate_generated_at_count,
            config=config,
        ),
    )


def _normalize_operator_flow_reports(
    value: object,
) -> tuple[PaperResearchPacketOperatorFlowReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("operator_flow_reports must be a list or tuple")
    reports = tuple(value)
    for report in reports:
        if type(report) is not PaperResearchPacketOperatorFlowReport:
            raise ValueError(
                "operator_flow_reports must contain "
                "PaperResearchPacketOperatorFlowReport values",
            )
        _validate_operator_flow_report(report)
    return reports


def _chronological_reports(
    reports: tuple[PaperResearchPacketOperatorFlowReport, ...],
) -> tuple[PaperResearchPacketOperatorFlowReport, ...]:
    return tuple(
        report
        for _, report in sorted(
            enumerate(reports),
            key=lambda item: (_as_utc("report generated_at", item[1].generated_at), item[0]),
        )
    )


def _flow_status_rows(
    reports: tuple[PaperResearchPacketOperatorFlowReport, ...],
) -> tuple[PaperResearchPacketOperatorFlowDbHistoryStatusRow, ...]:
    return tuple(
        PaperResearchPacketOperatorFlowDbHistoryStatusRow(
            flow_status,
            sum(1 for report in reports if report.flow_status == flow_status),
        )
        for flow_status in FLOW_STATUSES
    )


def _duplicate_generated_at_count(
    reports: tuple[PaperResearchPacketOperatorFlowReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        generated_at = _as_utc("report generated_at", report.generated_at)
        counts[generated_at] = counts.get(generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _consecutive_latest_status_count(
    reports: tuple[PaperResearchPacketOperatorFlowReport, ...],
    flow_status: str,
) -> int:
    if not reports or reports[-1].flow_status != flow_status:
        return 0
    count = 0
    for report in reversed(reports):
        if report.flow_status != flow_status:
            break
        count += 1
    return count


def _reason_code_rows(
    reports: tuple[PaperResearchPacketOperatorFlowReport, ...],
) -> tuple[PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for reason_code in set(report.reason_codes):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow(
            reason_code,
            report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _history_status(
    *,
    reports: tuple[PaperResearchPacketOperatorFlowReport, ...],
    flow_status_rows: tuple[
        PaperResearchPacketOperatorFlowDbHistoryStatusRow,
        ...,
    ],
    duplicate_generated_at_count: int,
    config: PaperResearchPacketOperatorFlowDbHistoryConfig,
) -> str:
    if len(reports) < config.min_report_count:
        return "blocked"
    if _count_for_status(flow_status_rows, "blocked") > config.max_blocked_flow_report_count:
        return "blocked"
    if _count_for_status(flow_status_rows, "watch") > config.max_watch_flow_report_count:
        return "watch"
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        return "watch"
    return "pass"


def _history_reason_codes(
    *,
    reports: tuple[PaperResearchPacketOperatorFlowReport, ...],
    flow_status_rows: tuple[
        PaperResearchPacketOperatorFlowDbHistoryStatusRow,
        ...,
    ],
    duplicate_generated_at_count: int,
    config: PaperResearchPacketOperatorFlowDbHistoryConfig,
) -> tuple[str, ...]:
    if len(reports) < config.min_report_count:
        return ("insufficient_paper_research_packet_operator_flow_history",)
    reason_codes: list[str] = []
    if _count_for_status(flow_status_rows, "blocked") > config.max_blocked_flow_report_count:
        reason_codes.append("blocked_operator_flow_report_threshold_exceeded")
    if _count_for_status(flow_status_rows, "watch") > config.max_watch_flow_report_count:
        reason_codes.append("watch_operator_flow_report_threshold_exceeded")
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append("duplicate_generated_at_threshold_exceeded")
    if not reason_codes:
        reason_codes.append("paper_research_packet_operator_flow_db_history_passed")
    return tuple(sorted(set(reason_codes)))


def _count_for_status(
    rows: tuple[PaperResearchPacketOperatorFlowDbHistoryStatusRow, ...],
    flow_status: str,
) -> int:
    for row in rows:
        if row.flow_status == flow_status:
            return row.status_count
    return 0


def _validate_operator_flow_report(
    report: PaperResearchPacketOperatorFlowReport,
) -> None:
    _validate_hard_flags("operator flow report", report)
    generated_at = _as_utc("generated_at", report.generated_at)
    packet_generated_at = _as_utc("packet_generated_at", report.packet_generated_at)
    quality_generated_at = _as_utc("quality_generated_at", report.quality_generated_at)
    quality_source_generated_at = _as_utc(
        "quality_source_generated_at",
        report.quality_source_generated_at,
    )
    history_generated_at = _as_utc("history_generated_at", report.history_generated_at)
    for field_name in (
        "config_version",
        "packet_config_version",
        "quality_config_version",
        "quality_source_config_version",
        "history_config_version",
    ):
        _require_canonical_string(field_name, getattr(report, field_name))
    _require_flow_status("flow_status", report.flow_status)
    _require_bool("packet_persisted", report.packet_persisted)
    _require_bool("quality_persisted", report.quality_persisted)
    for field_name in (
        "packet_row_count",
        "included_count",
        "skipped_count",
        "quality_source_age_seconds",
        "quality_check_count",
        "quality_pass_count",
        "quality_watch_count",
        "quality_blocked_count",
        "history_source_report_count",
        "history_duplicate_generated_at_count",
    ):
        _require_nonnegative_int(field_name, getattr(report, field_name))
    _require_flow_status("quality_status", report.quality_status)
    _require_flow_status("history_status", report.history_status)
    if report.history_latest_quality_status is not None:
        _require_flow_status(
            "history_latest_quality_status",
            report.history_latest_quality_status,
        )
    if report.history_latest_source_age_seconds is not None:
        _require_nonnegative_int(
            "history_latest_source_age_seconds",
            report.history_latest_source_age_seconds,
        )
    for field_name in (
        "quality_included_share",
        "quality_skipped_share",
        "history_latest_included_share",
        "history_latest_skipped_share",
    ):
        _require_optional_decimal(field_name, getattr(report, field_name))
    _normalize_reason_codes("reason_codes", report.reason_codes)
    _validate_operator_flow_report_consistency(
        report=report,
        generated_at=generated_at,
        packet_generated_at=packet_generated_at,
        quality_generated_at=quality_generated_at,
        quality_source_generated_at=quality_source_generated_at,
        history_generated_at=history_generated_at,
    )


def _validate_operator_flow_report_consistency(
    *,
    report: PaperResearchPacketOperatorFlowReport,
    generated_at: datetime,
    packet_generated_at: datetime,
    quality_generated_at: datetime,
    quality_source_generated_at: datetime,
    history_generated_at: datetime,
) -> None:
    if report.packet_row_count != report.included_count + report.skipped_count:
        raise ValueError("packet_row_count must match included_count and skipped_count")
    if quality_source_generated_at != packet_generated_at:
        raise ValueError("quality_source_generated_at must match packet_generated_at")
    if report.quality_source_config_version != report.packet_config_version:
        raise ValueError("quality_source_config_version must match packet_config_version")
    if report.quality_source_age_seconds != _timedelta_seconds(
        quality_generated_at - quality_source_generated_at,
    ):
        raise ValueError("quality_source_age_seconds must match generated_at values")
    if packet_generated_at > quality_generated_at:
        raise ValueError("packet_generated_at must not be after quality_generated_at")
    if quality_generated_at > history_generated_at:
        raise ValueError("quality_generated_at must not be after history_generated_at")
    if history_generated_at > generated_at:
        raise ValueError("history_generated_at must not be after generated_at")
    if report.quality_check_count != (
        report.quality_pass_count
        + report.quality_watch_count
        + report.quality_blocked_count
    ):
        raise ValueError("quality_check_count must match status counts")
    if report.quality_status != _quality_status_from_counts(
        pass_count=report.quality_pass_count,
        watch_count=report.quality_watch_count,
        blocked_count=report.quality_blocked_count,
    ):
        raise ValueError("quality_status must match status counts")
    _validate_operator_flow_history_fields(report)
    if report.flow_status != _flow_status_from_source(report):
        raise ValueError("flow_status must match source statuses")
    if report.reason_codes != _reason_codes_from_source(report):
        raise ValueError("reason_codes must match source statuses")


def _validate_operator_flow_history_fields(
    report: PaperResearchPacketOperatorFlowReport,
) -> None:
    if report.history_source_report_count == 0:
        if report.history_first_source_generated_at is not None:
            raise ValueError("history_first_source_generated_at must be absent")
        if report.history_latest_source_generated_at is not None:
            raise ValueError("history_latest_source_generated_at must be absent")
        if report.history_latest_quality_status is not None:
            raise ValueError("history_latest_quality_status must be absent")
        if report.history_latest_source_age_seconds is not None:
            raise ValueError("history_latest_source_age_seconds must be absent")
        if report.history_latest_included_share is not None:
            raise ValueError("history_latest_included_share must be absent")
        if report.history_latest_skipped_share is not None:
            raise ValueError("history_latest_skipped_share must be absent")
        return

    first_source_generated_at = _as_optional_utc(
        "history_first_source_generated_at",
        report.history_first_source_generated_at,
    )
    latest_source_generated_at = _as_optional_utc(
        "history_latest_source_generated_at",
        report.history_latest_source_generated_at,
    )
    if first_source_generated_at is None:
        raise ValueError("history_first_source_generated_at must not be absent")
    if latest_source_generated_at is None:
        raise ValueError("history_latest_source_generated_at must not be absent")
    if report.history_latest_quality_status is None:
        raise ValueError("history_latest_quality_status must not be absent")
    if report.history_latest_source_age_seconds is None:
        raise ValueError("history_latest_source_age_seconds must not be absent")
    if report.history_latest_included_share is None:
        raise ValueError("history_latest_included_share must not be absent")
    if report.history_latest_skipped_share is None:
        raise ValueError("history_latest_skipped_share must not be absent")
    if first_source_generated_at > latest_source_generated_at:
        raise ValueError("history source bounds must be chronological")
    if latest_source_generated_at != _as_utc(
        "quality_generated_at",
        report.quality_generated_at,
    ):
        raise ValueError("history_latest_source_generated_at must match quality_generated_at")
    if report.history_latest_quality_status != report.quality_status:
        raise ValueError("history_latest_quality_status must match quality_status")
    if report.history_latest_source_age_seconds != report.quality_source_age_seconds:
        raise ValueError(
            "history_latest_source_age_seconds must match quality_source_age_seconds",
        )
    if report.history_latest_included_share != report.quality_included_share:
        raise ValueError("history_latest_included_share must match quality_included_share")
    if report.history_latest_skipped_share != report.quality_skipped_share:
        raise ValueError("history_latest_skipped_share must match quality_skipped_share")


def _validate_history_report(
    report: PaperResearchPacketOperatorFlowDbHistoryReport,
) -> None:
    if report.report_count == 0:
        _validate_empty_history_report(report)
    else:
        _validate_nonempty_history_report(report)
    if report.flow_status_rows != tuple(
        PaperResearchPacketOperatorFlowDbHistoryStatusRow(
            flow_status,
            _count_for_status(report.flow_status_rows, flow_status),
        )
        for flow_status in FLOW_STATUSES
    ):
        raise ValueError("flow_status_rows must be deterministic")
    if report.report_count != sum(row.status_count for row in report.flow_status_rows):
        raise ValueError("flow_status_rows must match report_count")
    if report.duplicate_generated_at_count >= max(report.report_count, 1):
        raise ValueError("duplicate_generated_at_count must be below report_count")
    for row in report.reason_code_rows:
        if row.report_count > report.report_count:
            raise ValueError("reason_code_rows report_count must not exceed report_count")
    if report.reason_code_rows != tuple(
        sorted(
            report.reason_code_rows,
            key=lambda row: (-row.report_count, row.reason_code),
        )
    ):
        raise ValueError("reason_code_rows must be deterministic")
    _validate_consecutive_latest_counts(report)


def _validate_empty_history_report(
    report: PaperResearchPacketOperatorFlowDbHistoryReport,
) -> None:
    if report.first_report_generated_at is not None:
        raise ValueError("first_report_generated_at must be absent without reports")
    if report.latest_report_generated_at is not None:
        raise ValueError("latest_report_generated_at must be absent without reports")
    if report.latest_flow_status is not None:
        raise ValueError("latest_flow_status must be absent without reports")
    if report.latest_packet_row_count is not None:
        raise ValueError("latest_packet_row_count must be absent without reports")
    if report.latest_quality_status is not None:
        raise ValueError("latest_quality_status must be absent without reports")
    if report.latest_history_status is not None:
        raise ValueError("latest_history_status must be absent without reports")
    if report.duplicate_generated_at_count != 0:
        raise ValueError("duplicate_generated_at_count must be zero without reports")
    if report.latest_reason_codes:
        raise ValueError("latest_reason_codes must be absent without reports")
    if report.reason_code_rows:
        raise ValueError("reason_code_rows must be absent without reports")
    for field_name in (
        "consecutive_latest_pass_count",
        "consecutive_latest_watch_count",
        "consecutive_latest_blocked_count",
    ):
        if getattr(report, field_name) != 0:
            raise ValueError(f"{field_name} must be zero without reports")


def _validate_nonempty_history_report(
    report: PaperResearchPacketOperatorFlowDbHistoryReport,
) -> None:
    if report.first_report_generated_at is None:
        raise ValueError("first_report_generated_at is required with reports")
    if report.latest_report_generated_at is None:
        raise ValueError("latest_report_generated_at is required with reports")
    if report.latest_report_generated_at < report.first_report_generated_at:
        raise ValueError("latest_report_generated_at must not precede first report")
    if report.latest_flow_status is None:
        raise ValueError("latest_flow_status is required with reports")
    if report.latest_packet_row_count is None:
        raise ValueError("latest_packet_row_count is required with reports")
    if report.latest_quality_status is None:
        raise ValueError("latest_quality_status is required with reports")
    if report.latest_history_status is None:
        raise ValueError("latest_history_status is required with reports")
    if not report.latest_reason_codes:
        raise ValueError("latest_reason_codes is required with reports")
    if _count_for_status(report.flow_status_rows, report.latest_flow_status) == 0:
        raise ValueError("flow_status_rows must cover latest_flow_status")
    if not report.reason_code_rows:
        raise ValueError("reason_code_rows is required with reports")


def _validate_consecutive_latest_counts(
    report: PaperResearchPacketOperatorFlowDbHistoryReport,
) -> None:
    fields_by_status = {
        "pass": "consecutive_latest_pass_count",
        "watch": "consecutive_latest_watch_count",
        "blocked": "consecutive_latest_blocked_count",
    }
    for flow_status, field_name in fields_by_status.items():
        count = getattr(report, field_name)
        if report.latest_flow_status == flow_status:
            if report.report_count > 0 and count == 0:
                raise ValueError(f"{field_name} must be positive for latest status")
            if count > report.report_count:
                raise ValueError(f"{field_name} must not exceed report_count")
            if count > _count_for_status(report.flow_status_rows, flow_status):
                raise ValueError(f"{field_name} must not exceed flow_status_rows count")
        elif count != 0:
            raise ValueError(f"{field_name} must be zero unless it is the latest status")


def _normalize_status_rows(
    rows: object,
) -> tuple[PaperResearchPacketOperatorFlowDbHistoryStatusRow, ...]:
    normalized = _normalize_tuple(rows, "flow_status_rows")
    for row in normalized:
        if type(row) is not PaperResearchPacketOperatorFlowDbHistoryStatusRow:
            raise ValueError(
                "flow_status_rows must contain "
                "PaperResearchPacketOperatorFlowDbHistoryStatusRow values",
            )
        _validate_hard_flags("status row", row)
    return normalized


def _normalize_reason_code_rows(
    rows: object,
) -> tuple[PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow, ...]:
    normalized = _normalize_tuple(rows, "reason_code_rows")
    for row in normalized:
        if type(row) is not PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow:
            raise ValueError(
                "reason_code_rows must contain "
                "PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow values",
            )
        _validate_hard_flags("reason code row", row)
    reason_codes = tuple(row.reason_code for row in normalized)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_rows must not contain duplicate reason codes")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    normalized = _normalize_tuple(value, field_name)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in normalized:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate values")
        seen.add(reason_code)
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be deterministic")
    return normalized


def _normalize_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        return tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc


def _flow_status_from_source(report: PaperResearchPacketOperatorFlowReport) -> str:
    if (
        not report.packet_persisted
        or not report.quality_persisted
        or report.quality_status == "blocked"
        or report.history_status == "blocked"
    ):
        return "blocked"
    if report.quality_status == "watch" or report.history_status == "watch":
        return "watch"
    return "pass"


def _reason_codes_from_source(
    report: PaperResearchPacketOperatorFlowReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not report.packet_persisted:
        reason_codes.append("packet_not_persisted")
    if not report.quality_persisted:
        reason_codes.append("quality_not_persisted")
    if report.quality_status == "blocked":
        reason_codes.append("packet_quality_blocked")
    elif report.quality_status == "watch":
        reason_codes.append("packet_quality_watch")
    if report.history_status == "blocked":
        reason_codes.append("packet_quality_history_blocked")
    elif report.history_status == "watch":
        reason_codes.append("packet_quality_history_watch")
    if not reason_codes:
        reason_codes.append("operator_flow_passed")
    return tuple(sorted(reason_codes))


def _quality_status_from_counts(
    *,
    pass_count: int,
    watch_count: int,
    blocked_count: int,
) -> str:
    if blocked_count > 0:
        return "blocked"
    if watch_count > 0:
        return "watch"
    return "pass"


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _timedelta_seconds(value: timedelta) -> int:
    if value < timedelta(0):
        raise ValueError("generated_at values must be chronological")
    return value.days * 86_400 + value.seconds


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_flow_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FLOW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _validate_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")

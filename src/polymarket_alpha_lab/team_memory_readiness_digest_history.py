"""Pure report-only history reducer for team memory readiness digest reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.team_memory_readiness_digest import (
    TeamMemoryReadinessDigestReport,
)


DEFAULT_TEAM_MEMORY_READINESS_DIGEST_HISTORY_CONFIG_VERSION = (
    "team-memory-readiness-digest-history-v0"
)
DIGEST_STATUSES = ("pass", "watch", "blocked")
HISTORY_STATUSES = ("observed", "blocked")
REASON_CODES = ("insufficient_history", "duplicate_latest_generated_at")

__all__ = (
    "DEFAULT_TEAM_MEMORY_READINESS_DIGEST_HISTORY_CONFIG_VERSION",
    "TeamMemoryReadinessDigestHistoryConfig",
    "TeamMemoryReadinessDigestHistoryStatusRow",
    "TeamMemoryReadinessDigestHistoryReport",
    "build_team_memory_readiness_digest_history_report",
)


@dataclass(frozen=True)
class TeamMemoryReadinessDigestHistoryConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_READINESS_DIGEST_HISTORY_CONFIG_VERSION
    min_report_count: int = 2
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_report_count", self.min_report_count)
        _require_hard_flags("TeamMemoryReadinessDigestHistoryConfig", self)


@dataclass(frozen=True)
class TeamMemoryReadinessDigestHistoryStatusRow:
    digest_status: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest_status("digest_status", self.digest_status)
        _require_nonnegative_int("report_count", self.report_count)
        _require_hard_flags("TeamMemoryReadinessDigestHistoryStatusRow", self)


@dataclass(frozen=True)
class TeamMemoryReadinessDigestHistoryReport:
    generated_at: datetime
    config_version: str
    history_status: str
    report_count: int
    required_report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    status_rows: tuple[TeamMemoryReadinessDigestHistoryStatusRow, ...]
    latest_digest_status: str | None
    latest_team_count: int
    latest_pass_count: int
    latest_watch_count: int
    latest_blocked_count: int
    team_count_delta: int
    pass_count_delta: int
    watch_count_delta: int
    blocked_count_delta: int
    duplicate_latest_generated_at: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_history_status("history_status", self.history_status)
        _require_nonnegative_int("report_count", self.report_count)
        _require_positive_int("required_report_count", self.required_report_count)
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
        object.__setattr__(
            self,
            "status_rows",
            _normalize_status_rows(self.status_rows),
        )
        object.__setattr__(
            self,
            "latest_digest_status",
            _normalize_optional_digest_status(
                "latest_digest_status",
                self.latest_digest_status,
            ),
        )
        for field_name in (
            "latest_team_count",
            "latest_pass_count",
            "latest_watch_count",
            "latest_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "team_count_delta",
            "pass_count_delta",
            "watch_count_delta",
            "blocked_count_delta",
        ):
            _require_int(field_name, getattr(self, field_name))
        if type(self.duplicate_latest_generated_at) is not bool:
            raise ValueError("duplicate_latest_generated_at must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("TeamMemoryReadinessDigestHistoryReport", self)
        _validate_report_consistency(self)


def build_team_memory_readiness_digest_history_report(
    reports: list[TeamMemoryReadinessDigestReport]
    | tuple[TeamMemoryReadinessDigestReport, ...],
    *,
    config: TeamMemoryReadinessDigestHistoryConfig,
    generated_at: datetime,
) -> TeamMemoryReadinessDigestHistoryReport:
    if type(config) is not TeamMemoryReadinessDigestHistoryConfig:
        raise ValueError("config must be a TeamMemoryReadinessDigestHistoryConfig")
    _require_hard_flags("TeamMemoryReadinessDigestHistoryConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_reports = _normalize_reports(reports)
    ordered = _ordered_reports(source_reports)
    first_report = ordered[0][1] if ordered else None
    latest_report = ordered[-1][1] if ordered else None
    duplicate_latest_generated_at = _has_duplicate_latest_generated_at(ordered)

    reason_codes: list[str] = []
    if len(ordered) < config.min_report_count:
        reason_codes.append("insufficient_history")
    if duplicate_latest_generated_at:
        reason_codes.append("duplicate_latest_generated_at")

    return TeamMemoryReadinessDigestHistoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        history_status="blocked" if reason_codes else "observed",
        report_count=len(ordered),
        required_report_count=config.min_report_count,
        first_report_generated_at=(
            first_report.generated_at if first_report is not None else None
        ),
        latest_report_generated_at=(
            latest_report.generated_at if latest_report is not None else None
        ),
        status_rows=_status_rows(source_reports),
        latest_digest_status=(
            latest_report.digest_status if latest_report is not None else None
        ),
        latest_team_count=_latest_int_value(latest_report, "team_count"),
        latest_pass_count=_latest_int_value(latest_report, "pass_count"),
        latest_watch_count=_latest_int_value(latest_report, "watch_count"),
        latest_blocked_count=_latest_int_value(latest_report, "blocked_count"),
        team_count_delta=_int_delta(ordered, "team_count"),
        pass_count_delta=_int_delta(ordered, "pass_count"),
        watch_count_delta=_int_delta(ordered, "watch_count"),
        blocked_count_delta=_int_delta(ordered, "blocked_count"),
        duplicate_latest_generated_at=duplicate_latest_generated_at,
        reason_codes=tuple(reason_codes),
    )


def _normalize_reports(
    reports: list[TeamMemoryReadinessDigestReport]
    | tuple[TeamMemoryReadinessDigestReport, ...],
) -> tuple[TeamMemoryReadinessDigestReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple")
    source_reports = tuple(reports)
    for report in source_reports:
        if type(report) is not TeamMemoryReadinessDigestReport:
            raise ValueError("reports must contain TeamMemoryReadinessDigestReport values")
        _require_hard_flags("TeamMemoryReadinessDigestReport", report)
    return source_reports


def _ordered_reports(
    reports: tuple[TeamMemoryReadinessDigestReport, ...],
) -> tuple[tuple[datetime, TeamMemoryReadinessDigestReport], ...]:
    indexed = tuple(
        (_as_utc("report generated_at", report.generated_at), index, report)
        for index, report in enumerate(reports)
    )
    return tuple(
        (generated_at, report)
        for generated_at, _, report in sorted(
            indexed,
            key=lambda item: (item[0], -item[1]),
        )
    )


def _has_duplicate_latest_generated_at(
    ordered: tuple[tuple[datetime, TeamMemoryReadinessDigestReport], ...],
) -> bool:
    if not ordered:
        return False
    latest_generated_at = ordered[-1][0]
    return (
        sum(1 for generated_at, _report in ordered if generated_at == latest_generated_at)
        > 1
    )


def _status_rows(
    reports: tuple[TeamMemoryReadinessDigestReport, ...],
) -> tuple[TeamMemoryReadinessDigestHistoryStatusRow, ...]:
    return tuple(
        TeamMemoryReadinessDigestHistoryStatusRow(
            digest_status=digest_status,
            report_count=sum(
                1 for report in reports if report.digest_status == digest_status
            ),
        )
        for digest_status in DIGEST_STATUSES
    )


def _latest_int_value(
    report: TeamMemoryReadinessDigestReport | None,
    field_name: str,
) -> int:
    if report is None:
        return 0
    value = getattr(report, field_name)
    _require_nonnegative_int(field_name, value)
    return value


def _int_delta(
    ordered: tuple[tuple[datetime, TeamMemoryReadinessDigestReport], ...],
    field_name: str,
) -> int:
    if not ordered:
        return 0
    first_value = getattr(ordered[0][1], field_name)
    latest_value = getattr(ordered[-1][1], field_name)
    _require_nonnegative_int(field_name, first_value)
    _require_nonnegative_int(field_name, latest_value)
    return latest_value - first_value


def _validate_report_consistency(
    report: TeamMemoryReadinessDigestHistoryReport,
) -> None:
    if report.report_count != sum(row.report_count for row in report.status_rows):
        raise ValueError("status_rows must sum to report_count")
    if (
        report.latest_pass_count
        + report.latest_watch_count
        + report.latest_blocked_count
        != report.latest_team_count
    ):
        raise ValueError("latest counts must sum to latest_team_count")
    if report.report_count == 0:
        if report.first_report_generated_at is not None:
            raise ValueError("first_report_generated_at must be absent without reports")
        if report.latest_report_generated_at is not None:
            raise ValueError("latest_report_generated_at must be absent without reports")
        if report.latest_digest_status is not None:
            raise ValueError("latest_digest_status must be absent without reports")
        for field_name in (
            "latest_team_count",
            "latest_pass_count",
            "latest_watch_count",
            "latest_blocked_count",
            "team_count_delta",
            "pass_count_delta",
            "watch_count_delta",
            "blocked_count_delta",
        ):
            if getattr(report, field_name) != 0:
                raise ValueError(f"{field_name} must be zero without reports")
        if report.duplicate_latest_generated_at is not False:
            raise ValueError("duplicate_latest_generated_at must be False without reports")
    else:
        if report.first_report_generated_at is None:
            raise ValueError("first_report_generated_at is required with reports")
        if report.latest_report_generated_at is None:
            raise ValueError("latest_report_generated_at is required with reports")
        if report.first_report_generated_at > report.latest_report_generated_at:
            raise ValueError(
                "first_report_generated_at must be <= latest_report_generated_at",
            )
        if report.latest_digest_status is None:
            raise ValueError("latest_digest_status is required with reports")
    if report.history_status == "observed":
        if report.reason_codes:
            raise ValueError("observed history must not have reason_codes")
        if report.report_count < report.required_report_count:
            raise ValueError("observed history requires the minimum report count")
        if report.duplicate_latest_generated_at:
            raise ValueError("observed history cannot have duplicate latest generated_at")
    if report.history_status == "blocked" and not report.reason_codes:
        raise ValueError("blocked history requires reason_codes")
    if (
        report.duplicate_latest_generated_at
        and "duplicate_latest_generated_at" not in report.reason_codes
    ):
        raise ValueError("duplicate latest history requires duplicate_latest_generated_at reason")
    if (
        not report.duplicate_latest_generated_at
        and "duplicate_latest_generated_at" in report.reason_codes
    ):
        raise ValueError("duplicate_latest_generated_at reason requires duplicate latest history")


def _normalize_status_rows(
    rows: tuple[TeamMemoryReadinessDigestHistoryStatusRow, ...],
) -> tuple[TeamMemoryReadinessDigestHistoryStatusRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("status_rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not TeamMemoryReadinessDigestHistoryStatusRow:
            raise ValueError(
                "status_rows must contain TeamMemoryReadinessDigestHistoryStatusRow values",
            )
        _require_hard_flags("TeamMemoryReadinessDigestHistoryStatusRow", row)
    statuses = tuple(row.digest_status for row in normalized)
    if statuses != DIGEST_STATUSES:
        raise ValueError("status_rows must contain pass, watch, and blocked in order")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _normalize_optional_digest_status(
    field_name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None
    _require_digest_status(field_name, value)
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_history_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in HISTORY_STATUSES:
        raise ValueError(f"{field_name} must be observed or blocked")


def _require_digest_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_int(field_name: str, value: object) -> None:
    if type(value) is bool:
        raise ValueError(f"{field_name} must be an int and not a bool")
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")

"""Pure in-memory exception report for team-memory source recheck cadence."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_EXCEPTION_REPORT_CONFIG_VERSION = (
    "team-memory-source-recheck-cadence-exception-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ZERO_COUNT = Decimal("0")

_ROW_STATUSES = (
    "overdue_recheck",
    "stale_acknowledgement",
    "missing_source_family_evidence",
)
_REPORT_STATUSES = ("blocked", "watch", "pass")
_SEVERITY_BUCKETS = ("critical", "high", "medium", "none")
_ROW_STATUS_WEIGHT = {
    "overdue_recheck": 0,
    "stale_acknowledgement": 1,
    "missing_source_family_evidence": 2,
}
_SEVERITY_WEIGHT = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "none": 3,
}
_REPORT_REASON_ORDER = (
    "source_recheck_overdue",
    "source_family_evidence_missing",
    "source_recheck_acknowledgement_stale",
    "repeated_overdue_team_present",
    "repeated_overdue_category_present",
)
_EMPTY_REASON = "no_team_memory_source_recheck_cadence_rows_supplied"
_BOUNDARY_STATEMENT = (
    "Phase 1 pure in-memory report-only reducer for team-memory source recheck cadence exceptions."
)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceExceptionReportConfig:
    config_version: str = (
        DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_EXCEPTION_REPORT_CONFIG_VERSION
    )
    overdue_recheck_after_seconds: Decimal = Decimal("86400.000000")
    stale_acknowledgement_after_seconds: Decimal = Decimal("43200.000000")
    repeated_overdue_threshold: Decimal = Decimal("2")
    required_source_families: tuple[str, ...] = (
        "news",
        "market",
        "resolution",
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "overdue_recheck_after_seconds",
            _require_positive_decimal(
                "overdue_recheck_after_seconds",
                self.overdue_recheck_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "stale_acknowledgement_after_seconds",
            _require_positive_decimal(
                "stale_acknowledgement_after_seconds",
                self.stale_acknowledgement_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "repeated_overdue_threshold",
            _require_positive_count(
                "repeated_overdue_threshold",
                self.repeated_overdue_threshold,
            ),
        )
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_source_families(self.required_source_families),
        )
        require_paper_only_flags(
            "TeamMemorySourceRecheckCadenceExceptionReportConfig",
            self,
        )


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceSourceRow:
    source_id: str
    team_id: str
    category_id: str
    source_family: str
    source_checked_at: datetime
    source_rechecked_at: datetime | None
    recheck_acknowledged_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_id", self.source_id)
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "source_checked_at",
            _as_utc("source_checked_at", self.source_checked_at),
        )
        object.__setattr__(
            self,
            "source_rechecked_at",
            _as_optional_utc("source_rechecked_at", self.source_rechecked_at),
        )
        object.__setattr__(
            self,
            "recheck_acknowledged_at",
            _as_optional_utc("recheck_acknowledged_at", self.recheck_acknowledged_at),
        )
        _validate_source_row_sequence(self)
        require_paper_only_flags("TeamMemorySourceRecheckCadenceSourceRow", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceExceptionRow:
    source_id: str
    team_id: str
    category_id: str
    source_family: str
    exception_status: str
    severity_bucket: str
    source_checked_at: datetime
    source_rechecked_at: datetime | None
    recheck_acknowledged_at: datetime | None
    recheck_age_seconds: Decimal
    acknowledgement_age_seconds: Decimal | None
    overdue_recheck_delta_seconds: Decimal
    stale_acknowledgement_delta_seconds: Decimal
    missing_source_family_count: Decimal
    repeated_overdue_team_count: Decimal
    repeated_overdue_category_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_id", self.source_id)
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_canonical_string("source_family", self.source_family)
        _require_member("exception_status", self.exception_status, _ROW_STATUSES)
        _require_member("severity_bucket", self.severity_bucket, _SEVERITY_BUCKETS)
        object.__setattr__(
            self,
            "source_checked_at",
            _as_utc("source_checked_at", self.source_checked_at),
        )
        object.__setattr__(
            self,
            "source_rechecked_at",
            _as_optional_utc("source_rechecked_at", self.source_rechecked_at),
        )
        object.__setattr__(
            self,
            "recheck_acknowledged_at",
            _as_optional_utc("recheck_acknowledged_at", self.recheck_acknowledged_at),
        )
        for field_name in (
            "recheck_age_seconds",
            "overdue_recheck_delta_seconds",
            "stale_acknowledgement_delta_seconds",
            "missing_source_family_count",
            "repeated_overdue_team_count",
            "repeated_overdue_category_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "acknowledgement_age_seconds",
            _normalize_optional_decimal(
                "acknowledgement_age_seconds",
                self.acknowledgement_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_exception_row_consistency(self)
        require_paper_only_flags("TeamMemorySourceRecheckCadenceExceptionRow", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceTeamRollup:
    team_id: str
    category_id: str
    source_row_count: Decimal
    exception_row_count: Decimal
    overdue_recheck_count: Decimal
    missing_source_family_evidence_count: Decimal
    stale_acknowledgement_count: Decimal
    repeated_overdue_source_count: Decimal
    severity_bucket: str
    exception_source_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        for field_name in (
            "source_row_count",
            "exception_row_count",
            "overdue_recheck_count",
            "missing_source_family_evidence_count",
            "stale_acknowledgement_count",
            "repeated_overdue_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("severity_bucket", self.severity_bucket, _SEVERITY_BUCKETS)
        object.__setattr__(
            self,
            "exception_source_ratio",
            _normalize_ratio("exception_source_ratio", self.exception_source_ratio),
        )
        require_paper_only_flags("TeamMemorySourceRecheckCadenceTeamRollup", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceSourceFamilyRollup:
    source_family: str
    source_row_count: Decimal
    exception_row_count: Decimal
    overdue_recheck_count: Decimal
    missing_source_family_evidence_count: Decimal
    stale_acknowledgement_count: Decimal
    repeated_overdue_source_count: Decimal
    severity_bucket: str
    exception_source_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_family", self.source_family)
        for field_name in (
            "source_row_count",
            "exception_row_count",
            "overdue_recheck_count",
            "missing_source_family_evidence_count",
            "stale_acknowledgement_count",
            "repeated_overdue_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("severity_bucket", self.severity_bucket, _SEVERITY_BUCKETS)
        object.__setattr__(
            self,
            "exception_source_ratio",
            _normalize_ratio("exception_source_ratio", self.exception_source_ratio),
        )
        require_paper_only_flags(
            "TeamMemorySourceRecheckCadenceSourceFamilyRollup",
            self,
        )


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceExceptionReport:
    generated_at: datetime
    config_version: str
    report_status: str
    severity_bucket: str
    source_row_count: Decimal
    exception_row_count: Decimal
    overdue_recheck_count: Decimal
    missing_source_family_evidence_count: Decimal
    stale_acknowledgement_count: Decimal
    repeated_overdue_team_count: Decimal
    repeated_overdue_category_count: Decimal
    team_rollup_count: Decimal
    source_family_rollup_count: Decimal
    exception_source_ratio: Decimal
    max_recheck_age_seconds: Decimal | None
    max_acknowledgement_age_seconds: Decimal | None
    reason_codes: tuple[str, ...]
    rows: tuple[TeamMemorySourceRecheckCadenceExceptionRow, ...]
    team_rollups: tuple[TeamMemorySourceRecheckCadenceTeamRollup, ...]
    source_family_rollups: tuple[TeamMemorySourceRecheckCadenceSourceFamilyRollup, ...]
    boundary_statement: str = _BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, _REPORT_STATUSES)
        _require_member("severity_bucket", self.severity_bucket, _SEVERITY_BUCKETS)
        for field_name in (
            "source_row_count",
            "exception_row_count",
            "overdue_recheck_count",
            "missing_source_family_evidence_count",
            "stale_acknowledgement_count",
            "repeated_overdue_team_count",
            "repeated_overdue_category_count",
            "team_rollup_count",
            "source_family_rollup_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "exception_source_ratio",
            _normalize_ratio("exception_source_ratio", self.exception_source_ratio),
        )
        for field_name in (
            "max_recheck_age_seconds",
            "max_acknowledgement_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_exception_rows(self.rows))
        object.__setattr__(
            self,
            "team_rollups",
            _normalize_team_rollups(self.team_rollups),
        )
        object.__setattr__(
            self,
            "source_family_rollups",
            _normalize_source_family_rollups(self.source_family_rollups),
        )
        if self.boundary_statement != _BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match report-only scope")
        _validate_report_consistency(self)
        require_paper_only_flags(
            "TeamMemorySourceRecheckCadenceExceptionReport",
            self,
        )


def build_team_memory_source_recheck_cadence_exception_report(
    rows: list[TeamMemorySourceRecheckCadenceSourceRow | dict[str, object]]
    | tuple[TeamMemorySourceRecheckCadenceSourceRow | dict[str, object], ...],
    *,
    config: TeamMemorySourceRecheckCadenceExceptionReportConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceExceptionReport:
    if type(config) is not TeamMemorySourceRecheckCadenceExceptionReportConfig:
        raise ValueError(
            "config must be a TeamMemorySourceRecheckCadenceExceptionReportConfig",
        )
    require_paper_only_flags(
        "TeamMemorySourceRecheckCadenceExceptionReportConfig",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(rows, generated_at=generated_at_utc)
    missing_by_team = _missing_source_family_counts_by_team(
        source_rows,
        config.required_source_families,
    )
    missing_by_family = _missing_source_family_counts_by_family(
        source_rows,
        config.required_source_families,
    )
    overdue_counts_by_team = _overdue_counts_by_team(source_rows, generated_at_utc, config)
    overdue_counts_by_category = _overdue_counts_by_category(
        source_rows,
        generated_at_utc,
        config,
    )
    exception_rows = tuple(
        sorted(
            (
                exception_row
                for row in source_rows
                if (
                    exception_row := _exception_row_from_source(
                        row,
                        generated_at=generated_at_utc,
                        config=config,
                        source_team_count=len(
                            {candidate.team_id for candidate in source_rows}
                        ),
                        missing_source_family_count=missing_by_team[
                            (row.team_id, row.category_id)
                        ],
                        repeated_overdue_team_count=overdue_counts_by_team[
                            row.team_id
                        ],
                        repeated_overdue_category_count=overdue_counts_by_category[
                            row.category_id
                        ],
                    )
                )
                is not None
            ),
            key=_exception_row_sort_key,
        )
    )
    team_rollups = _team_rollups(
        source_rows,
        exception_rows,
        missing_by_team,
        overdue_counts_by_team,
        config,
    )
    source_family_rollups = _source_family_rollups(
        source_rows,
        exception_rows,
        missing_by_family,
        overdue_counts_by_team,
        config,
    )
    source_row_count = _decimal_count(len(source_rows))
    exception_row_count = _decimal_count(len(exception_rows))
    reason_codes = _report_reason_codes(exception_rows)

    return TeamMemorySourceRecheckCadenceExceptionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(exception_rows),
        severity_bucket=_report_severity(exception_rows),
        source_row_count=source_row_count,
        exception_row_count=exception_row_count,
        overdue_recheck_count=_reason_count(exception_rows, "source_recheck_overdue"),
        missing_source_family_evidence_count=_decimal_count(sum(missing_by_team.values())),
        stale_acknowledgement_count=_reason_count(
            exception_rows,
            "source_recheck_acknowledgement_stale",
        ),
        repeated_overdue_team_count=_decimal_count(
            _repeated_overdue_group_count(
                overdue_counts_by_team.values(),
                config.repeated_overdue_threshold,
            ),
        ),
        repeated_overdue_category_count=_decimal_count(
            _repeated_overdue_group_count(
                overdue_counts_by_category.values(),
                config.repeated_overdue_threshold,
            ),
        ),
        team_rollup_count=_decimal_count(len(team_rollups)),
        source_family_rollup_count=_decimal_count(len(source_family_rollups)),
        exception_source_ratio=_ratio(exception_row_count, source_row_count),
        max_recheck_age_seconds=_max_optional_decimal(
            row.recheck_age_seconds for row in exception_rows
        ),
        max_acknowledgement_age_seconds=_max_optional_decimal(
            row.acknowledgement_age_seconds for row in exception_rows
        ),
        reason_codes=reason_codes,
        rows=exception_rows,
        team_rollups=team_rollups,
        source_family_rollups=source_family_rollups,
    )


def team_memory_source_recheck_cadence_exception_report_payload(
    report: TeamMemorySourceRecheckCadenceExceptionReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemorySourceRecheckCadenceExceptionReport:
        raise ValueError(
            "report must be a TeamMemorySourceRecheckCadenceExceptionReport",
        )
    reject_unsafe_surface_fields(
        "team memory source recheck cadence exception report",
        report,
    )
    return json_ready_no_floats(asdict(report))


def _exception_row_from_source(
    row: TeamMemorySourceRecheckCadenceSourceRow,
    *,
    generated_at: datetime,
    config: TeamMemorySourceRecheckCadenceExceptionReportConfig,
    source_team_count: int,
    missing_source_family_count: int,
    repeated_overdue_team_count: int,
    repeated_overdue_category_count: int,
) -> TeamMemorySourceRecheckCadenceExceptionRow | None:
    recheck_age_seconds = _recheck_age_seconds(row, generated_at)
    acknowledgement_age_seconds = _acknowledgement_age_seconds(row, generated_at)
    overdue_delta = _overdue_recheck_delta_seconds(
        row,
        generated_at,
        config.overdue_recheck_after_seconds,
    )
    stale_ack_delta = _positive_delta(
        acknowledgement_age_seconds,
        config.stale_acknowledgement_after_seconds,
    )
    reasons = _row_reason_codes(
        overdue_delta=overdue_delta,
        stale_ack_delta=stale_ack_delta,
        missing_source_family_count=(
            missing_source_family_count
            if _emit_missing_family_exception_row(
                row,
                source_team_count=source_team_count,
                missing_source_family_count=missing_source_family_count,
            )
            else 0
        ),
        repeated_overdue_team_count=repeated_overdue_team_count,
        repeated_overdue_category_count=repeated_overdue_category_count,
        config=config,
    )
    if not reasons:
        return None
    exception_status = _exception_status(reasons)
    return TeamMemorySourceRecheckCadenceExceptionRow(
        source_id=row.source_id,
        team_id=row.team_id,
        category_id=row.category_id,
        source_family=row.source_family,
        exception_status=exception_status,
        severity_bucket=_severity_bucket(
            exception_status=exception_status,
            reasons=reasons,
        ),
        source_checked_at=row.source_checked_at,
        source_rechecked_at=row.source_rechecked_at,
        recheck_acknowledged_at=row.recheck_acknowledged_at,
        recheck_age_seconds=recheck_age_seconds,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        overdue_recheck_delta_seconds=overdue_delta,
        stale_acknowledgement_delta_seconds=stale_ack_delta,
        missing_source_family_count=_decimal_count(missing_source_family_count),
        repeated_overdue_team_count=_decimal_count(repeated_overdue_team_count),
        repeated_overdue_category_count=_decimal_count(repeated_overdue_category_count),
        reason_codes=reasons,
    )


def _row_reason_codes(
    *,
    overdue_delta: Decimal,
    stale_ack_delta: Decimal,
    missing_source_family_count: int,
    repeated_overdue_team_count: int,
    repeated_overdue_category_count: int,
    config: TeamMemorySourceRecheckCadenceExceptionReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if overdue_delta > _ZERO:
        reasons.append("source_recheck_overdue")
    if missing_source_family_count > 0:
        reasons.append("source_family_evidence_missing")
    if stale_ack_delta > _ZERO:
        reasons.append("source_recheck_acknowledgement_stale")
    if not reasons:
        return ()
    if _decimal_count(repeated_overdue_team_count) >= config.repeated_overdue_threshold:
        reasons.append("repeated_overdue_team_present")
    if _decimal_count(repeated_overdue_category_count) >= config.repeated_overdue_threshold:
        reasons.append("repeated_overdue_category_present")
    return tuple(reasons)


def _exception_status(reason_codes: tuple[str, ...]) -> str:
    if "source_recheck_overdue" in reason_codes:
        return "overdue_recheck"
    if "source_recheck_acknowledgement_stale" in reason_codes:
        return "stale_acknowledgement"
    return "missing_source_family_evidence"


def _severity_bucket(
    *,
    exception_status: str,
    reasons: tuple[str, ...],
) -> str:
    if exception_status == "overdue_recheck" or "source_family_evidence_missing" in reasons:
        return "critical"
    if exception_status == "stale_acknowledgement":
        return "high"
    return "medium"


def _emit_missing_family_exception_row(
    row: TeamMemorySourceRecheckCadenceSourceRow,
    *,
    source_team_count: int,
    missing_source_family_count: int,
) -> bool:
    if missing_source_family_count <= 0:
        return False
    return source_team_count == 1 or row.source_family != "resolution"


def _team_rollups(
    source_rows: tuple[TeamMemorySourceRecheckCadenceSourceRow, ...],
    exception_rows: tuple[TeamMemorySourceRecheckCadenceExceptionRow, ...],
    missing_by_team: dict[tuple[str, str], int],
    overdue_counts_by_team: dict[str, int],
    config: TeamMemorySourceRecheckCadenceExceptionReportConfig,
) -> tuple[TeamMemorySourceRecheckCadenceTeamRollup, ...]:
    pairs = tuple(
        sorted(
            {(row.team_id, row.category_id) for row in source_rows},
            key=lambda item: (item[0], item[1]),
        )
    )
    rollups = []
    for team_id, category_id in pairs:
        team_source_rows = tuple(row for row in source_rows if row.team_id == team_id)
        team_exception_rows = tuple(
            row for row in exception_rows if row.team_id == team_id
        )
        missing_count = _decimal_count(missing_by_team[(team_id, category_id)])
        overdue_count = _reason_count(team_exception_rows, "source_recheck_overdue")
        stale_count = _reason_count(
            team_exception_rows,
            "source_recheck_acknowledgement_stale",
        )
        exception_count = _decimal_count(len(team_exception_rows))
        rollups.append(
            TeamMemorySourceRecheckCadenceTeamRollup(
                team_id=team_id,
                category_id=category_id,
                source_row_count=_decimal_count(len(team_source_rows)),
                exception_row_count=exception_count,
                overdue_recheck_count=overdue_count,
                missing_source_family_evidence_count=missing_count,
                stale_acknowledgement_count=stale_count,
                repeated_overdue_source_count=_decimal_count(
                    overdue_counts_by_team[team_id],
                ),
                severity_bucket=_rollup_severity(
                    exception_count=exception_count,
                    overdue_count=overdue_count,
                    missing_count=missing_count,
                    stale_count=stale_count,
                    repeated_overdue_count=_decimal_count(
                        overdue_counts_by_team[team_id],
                    ),
                    repeated_threshold=config.repeated_overdue_threshold,
                ),
                exception_source_ratio=_ratio(
                    exception_count,
                    _decimal_count(len(team_source_rows)),
                ),
            )
        )
    return tuple(
        sorted(
            rollups,
            key=_team_rollup_sort_key,
        )
    )


def _team_rollup_sort_key(
    row: TeamMemorySourceRecheckCadenceTeamRollup,
) -> tuple[int, Decimal, str, str]:
    return (
        _SEVERITY_WEIGHT[row.severity_bucket],
        -row.exception_row_count,
        row.team_id,
        row.category_id,
    )


def _source_family_rollups(
    source_rows: tuple[TeamMemorySourceRecheckCadenceSourceRow, ...],
    exception_rows: tuple[TeamMemorySourceRecheckCadenceExceptionRow, ...],
    missing_by_family: dict[str, int],
    overdue_counts_by_team: dict[str, int],
    config: TeamMemorySourceRecheckCadenceExceptionReportConfig,
) -> tuple[TeamMemorySourceRecheckCadenceSourceFamilyRollup, ...]:
    if not source_rows:
        return ()
    source_families = tuple(
        sorted({row.source_family for row in source_rows} | set(config.required_source_families))
    )
    rollups = []
    for source_family in source_families:
        family_source_rows = tuple(row for row in source_rows if row.source_family == source_family)
        family_exception_rows = tuple(
            row for row in exception_rows if row.source_family == source_family
        )
        missing_count = _decimal_count(missing_by_family[source_family])
        overdue_count = _reason_count(family_exception_rows, "source_recheck_overdue")
        stale_count = _reason_count(
            family_exception_rows,
            "source_recheck_acknowledgement_stale",
        )
        repeated_overdue_count = _decimal_count(
            sum(
                1
                for row in family_exception_rows
                if _decimal_count(overdue_counts_by_team[row.team_id])
                >= config.repeated_overdue_threshold
            )
        )
        exception_count = _decimal_count(len(family_exception_rows))
        rollups.append(
            TeamMemorySourceRecheckCadenceSourceFamilyRollup(
                source_family=source_family,
                source_row_count=_decimal_count(len(family_source_rows)),
                exception_row_count=exception_count,
                overdue_recheck_count=overdue_count,
                missing_source_family_evidence_count=missing_count,
                stale_acknowledgement_count=stale_count,
                repeated_overdue_source_count=repeated_overdue_count,
                severity_bucket=_rollup_severity(
                    exception_count=exception_count,
                    overdue_count=overdue_count,
                    missing_count=missing_count,
                    stale_count=stale_count,
                    repeated_overdue_count=repeated_overdue_count,
                    repeated_threshold=config.repeated_overdue_threshold,
                ),
                exception_source_ratio=_ratio(
                    exception_count,
                    _decimal_count(len(family_source_rows)),
                ),
            )
        )
    return tuple(
        sorted(
            rollups,
            key=lambda row: (_SEVERITY_WEIGHT[row.severity_bucket], row.source_family),
        )
    )


def _rollup_severity(
    *,
    exception_count: Decimal,
    overdue_count: Decimal,
    missing_count: Decimal,
    stale_count: Decimal,
    repeated_overdue_count: Decimal,
    repeated_threshold: Decimal,
) -> str:
    if exception_count == _ZERO:
        return "none"
    if overdue_count > _ZERO or missing_count > _ZERO:
        return "critical"
    if stale_count > _ZERO:
        return "high"
    if repeated_overdue_count >= repeated_threshold:
        return "medium"
    return "medium"


def _report_status(
    rows: tuple[TeamMemorySourceRecheckCadenceExceptionRow, ...],
) -> str:
    if any(row.severity_bucket in ("critical", "high") for row in rows):
        return "blocked"
    if rows:
        return "watch"
    return "pass"


def _report_severity(
    rows: tuple[TeamMemorySourceRecheckCadenceExceptionRow, ...],
) -> str:
    if not rows:
        return "none"
    return min((row.severity_bucket for row in rows), key=lambda item: _SEVERITY_WEIGHT[item])


def _report_reason_codes(
    rows: tuple[TeamMemorySourceRecheckCadenceExceptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    present: set[str] = set()
    for row in rows:
        present.update(row.reason_codes)
    return tuple(code for code in _REPORT_REASON_ORDER if code in present)


def _normalize_source_rows(
    rows: list[TeamMemorySourceRecheckCadenceSourceRow | dict[str, object]]
    | tuple[TeamMemorySourceRecheckCadenceSourceRow | dict[str, object], ...],
    *,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceSourceRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized: list[TeamMemorySourceRecheckCadenceSourceRow] = []
    seen: set[tuple[str, str, str, str]] = set()
    for value in rows:
        try:
            row = _coerce_source_row(value)
        except ValueError as exc:
            if type(value) is dict:
                raw_source_checked_at = value.get("source_checked_at")
                if type(raw_source_checked_at) is datetime:
                    _reject_future_timestamp(
                        "source_checked_at",
                        raw_source_checked_at.astimezone(UTC),
                        generated_at,
                    )
            raise exc
        require_paper_only_flags("TeamMemorySourceRecheckCadenceSourceRow", row)
        _reject_future_timestamp("source_checked_at", row.source_checked_at, generated_at)
        if row.source_rechecked_at is not None:
            _reject_future_timestamp(
                "source_rechecked_at",
                row.source_rechecked_at,
                generated_at,
            )
        if row.recheck_acknowledged_at is not None:
            _reject_future_timestamp(
                "recheck_acknowledged_at",
                row.recheck_acknowledged_at,
                generated_at,
            )
        key = (row.source_id, row.team_id, row.category_id, row.source_family)
        if key in seen:
            raise ValueError("rows must use deterministic unique source/team/category/family keys")
        seen.add(key)
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (row.team_id, row.category_id, row.source_family, row.source_id),
        )
    )


def _coerce_source_row(
    value: TeamMemorySourceRecheckCadenceSourceRow | dict[str, object],
) -> TeamMemorySourceRecheckCadenceSourceRow:
    if type(value) is TeamMemorySourceRecheckCadenceSourceRow:
        return value
    if type(value) is dict:
        return TeamMemorySourceRecheckCadenceSourceRow(**value)
    raise ValueError("rows must contain TeamMemorySourceRecheckCadenceSourceRow")


def _missing_source_family_counts_by_team(
    rows: tuple[TeamMemorySourceRecheckCadenceSourceRow, ...],
    required_source_families: tuple[str, ...],
) -> dict[tuple[str, str], int]:
    result: dict[tuple[str, str], int] = {}
    pairs = {(row.team_id, row.category_id) for row in rows}
    for team_id, category_id in pairs:
        observed = {
            row.source_family
            for row in rows
            if row.team_id == team_id and row.category_id == category_id
        }
        result[(team_id, category_id)] = sum(
            1 for family in required_source_families if family not in observed
        )
    return result


def _missing_source_family_counts_by_family(
    rows: tuple[TeamMemorySourceRecheckCadenceSourceRow, ...],
    required_source_families: tuple[str, ...],
) -> dict[str, int]:
    teams = {row.team_id for row in rows}
    result: dict[str, int] = {}
    for source_family in sorted({row.source_family for row in rows} | set(required_source_families)):
        if source_family in required_source_families:
            result[source_family] = sum(
                1
                for team_id in teams
                if not any(
                    row.team_id == team_id and row.source_family == source_family
                    for row in rows
                )
            )
        else:
            result[source_family] = 0
    return result


def _overdue_counts_by_team(
    rows: tuple[TeamMemorySourceRecheckCadenceSourceRow, ...],
    generated_at: datetime,
    config: TeamMemorySourceRecheckCadenceExceptionReportConfig,
) -> dict[str, int]:
    return {
        team_id: sum(
            1
            for row in rows
            if row.team_id == team_id
            and _overdue_recheck_delta_seconds(
                row,
                generated_at,
                config.overdue_recheck_after_seconds,
            )
            > _ZERO
        )
        for team_id in {row.team_id for row in rows}
    }


def _overdue_counts_by_category(
    rows: tuple[TeamMemorySourceRecheckCadenceSourceRow, ...],
    generated_at: datetime,
    config: TeamMemorySourceRecheckCadenceExceptionReportConfig,
) -> dict[str, int]:
    return {
        category_id: sum(
            1
            for row in rows
            if row.category_id == category_id
            and _overdue_recheck_delta_seconds(
                row,
                generated_at,
                config.overdue_recheck_after_seconds,
            )
            > _ZERO
        )
        for category_id in {row.category_id for row in rows}
    }


def _recheck_age_seconds(
    row: TeamMemorySourceRecheckCadenceSourceRow,
    generated_at: datetime,
) -> Decimal:
    return _age_seconds(generated_at, row.source_checked_at)


def _acknowledgement_age_seconds(
    row: TeamMemorySourceRecheckCadenceSourceRow,
    generated_at: datetime,
) -> Decimal:
    base = row.recheck_acknowledged_at or row.source_rechecked_at or row.source_checked_at
    return _age_seconds(generated_at, base)


def _overdue_recheck_delta_seconds(
    row: TeamMemorySourceRecheckCadenceSourceRow,
    generated_at: datetime,
    threshold: Decimal,
) -> Decimal:
    if row.source_rechecked_at is not None:
        return _ZERO
    return _positive_delta(_age_seconds(generated_at, row.source_checked_at), threshold)


def _positive_delta(value: Decimal | None, threshold: Decimal) -> Decimal:
    if value is None or value <= threshold:
        return _ZERO
    return (value - threshold).quantize(_QUANTUM)


def _reason_count(
    rows: tuple[TeamMemorySourceRecheckCadenceExceptionRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _repeated_overdue_group_count(counts: Iterable[int], threshold: Decimal) -> int:
    return sum(1 for count in counts if _decimal_count(count) >= threshold)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(_QUANTUM)


def _decimal_count(value: int) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return Decimal(value).quantize(_QUANTUM)


def _max_optional_decimal(values: object) -> Decimal | None:
    present = tuple(value for value in values if value is not None)  # type: ignore[union-attr]
    if not present:
        return None
    return max(present)


def _age_seconds(later_at: datetime, earlier_at: datetime) -> Decimal:
    if earlier_at > later_at:
        raise ValueError("timestamp sequence must not be negative")
    delta = later_at - earlier_at
    with localcontext(_DECIMAL_CONTEXT):
        whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
        microseconds = Decimal(delta.microseconds) / Decimal("1000000")
        return (whole_seconds + microseconds).quantize(_QUANTUM)


def _reject_future_timestamp(
    field_name: str,
    value: datetime,
    generated_at: datetime,
) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be in the future")


def _normalize_source_families(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("required_source_families must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("required_source_families must contain canonical strings") from exc
    if not items:
        raise ValueError("required_source_families must contain canonical strings")
    for item in items:
        _require_canonical_string("source_family", item)
    if len(set(items)) != len(items):
        raise ValueError("required_source_families must not contain duplicates")
    return items


def _normalize_exception_rows(
    rows: object,
) -> tuple[TeamMemorySourceRecheckCadenceExceptionRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not TeamMemorySourceRecheckCadenceExceptionRow:
            raise ValueError("rows must contain TeamMemorySourceRecheckCadenceExceptionRow")
    if normalized != tuple(sorted(normalized, key=_exception_row_sort_key)):
        raise ValueError("rows must use deterministic exception sort")
    return normalized


def _normalize_team_rollups(
    rows: object,
) -> tuple[TeamMemorySourceRecheckCadenceTeamRollup, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("team_rollups must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("team_rollups must be an iterable") from exc
    for row in normalized:
        if type(row) is not TeamMemorySourceRecheckCadenceTeamRollup:
            raise ValueError(
                "team_rollups must contain TeamMemorySourceRecheckCadenceTeamRollup",
            )
    if normalized != tuple(
        sorted(
            normalized,
            key=_team_rollup_sort_key,
        )
    ):
        raise ValueError("team_rollups must use deterministic sort")
    return normalized


def _normalize_source_family_rollups(
    rows: object,
) -> tuple[TeamMemorySourceRecheckCadenceSourceFamilyRollup, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("source_family_rollups must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("source_family_rollups must be an iterable") from exc
    for row in normalized:
        if type(row) is not TeamMemorySourceRecheckCadenceSourceFamilyRollup:
            raise ValueError(
                "source_family_rollups must contain TeamMemorySourceRecheckCadenceSourceFamilyRollup",
            )
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (_SEVERITY_WEIGHT[row.severity_bucket], row.source_family),
        )
    ):
        raise ValueError("source_family_rollups must use deterministic sort")
    return normalized


def _exception_row_sort_key(
    row: TeamMemorySourceRecheckCadenceExceptionRow,
) -> tuple[int, int, Decimal, str, str, str, str]:
    return (
        _ROW_STATUS_WEIGHT[row.exception_status],
        _SEVERITY_WEIGHT[row.severity_bucket],
        -row.recheck_age_seconds,
        row.team_id,
        row.category_id,
        row.source_family,
        row.source_id,
    )


def _validate_source_row_sequence(
    row: TeamMemorySourceRecheckCadenceSourceRow,
) -> None:
    if row.source_rechecked_at is not None and row.source_rechecked_at < row.source_checked_at:
        raise ValueError("source_rechecked_at must be >= source_checked_at")
    if row.recheck_acknowledged_at is not None:
        if row.source_rechecked_at is None:
            raise ValueError("recheck_acknowledged_at requires source_rechecked_at")
        if row.recheck_acknowledged_at < row.source_rechecked_at:
            raise ValueError("recheck_acknowledged_at must be >= source_rechecked_at")


def _validate_exception_row_consistency(
    row: TeamMemorySourceRecheckCadenceExceptionRow,
) -> None:
    if row.acknowledgement_age_seconds is None:
        raise ValueError("acknowledgement_age_seconds must be present")
    if row.exception_status == "overdue_recheck":
        if "source_recheck_overdue" not in row.reason_codes:
            raise ValueError("overdue_recheck rows require overdue reason")
    if row.exception_status == "stale_acknowledgement":
        if "source_recheck_acknowledgement_stale" not in row.reason_codes:
            raise ValueError("stale acknowledgement rows require stale reason")
    if row.exception_status == "missing_source_family_evidence":
        if "source_family_evidence_missing" not in row.reason_codes:
            raise ValueError("missing family rows require missing evidence reason")


def _validate_report_consistency(
    report: TeamMemorySourceRecheckCadenceExceptionReport,
) -> None:
    if report.exception_row_count != _decimal_count(len(report.rows)):
        raise ValueError("exception_row_count must match rows")
    if report.team_rollup_count != _decimal_count(len(report.team_rollups)):
        raise ValueError("team_rollup_count must match team_rollups")
    if report.source_family_rollup_count != _decimal_count(
        len(report.source_family_rollups)
    ):
        raise ValueError("source_family_rollup_count must match source_family_rollups")
    if report.overdue_recheck_count != _reason_count(report.rows, "source_recheck_overdue"):
        raise ValueError("overdue_recheck_count must match rows")
    if report.stale_acknowledgement_count != _reason_count(
        report.rows,
        "source_recheck_acknowledgement_stale",
    ):
        raise ValueError("stale_acknowledgement_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.severity_bucket != _report_severity(report.rows):
        raise ValueError("severity_bucket must match rows")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_positive_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_COUNT_QUANTUM)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_QUANTUM)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain canonical strings") from exc
    if not items:
        raise ValueError("reason_codes must contain canonical strings")
    for item in items:
        _require_canonical_string("reason_codes", item)
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must not contain duplicates")
    known = set(_REPORT_REASON_ORDER)
    known.add(_EMPTY_REASON)
    if any(item not in known for item in items):
        raise ValueError("reason_codes must contain known source recheck reasons")
    return items


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


__all__ = (
    "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_EXCEPTION_REPORT_CONFIG_VERSION",
    "TeamMemorySourceRecheckCadenceExceptionReport",
    "TeamMemorySourceRecheckCadenceExceptionReportConfig",
    "TeamMemorySourceRecheckCadenceExceptionRow",
    "TeamMemorySourceRecheckCadenceSourceFamilyRollup",
    "TeamMemorySourceRecheckCadenceSourceRow",
    "TeamMemorySourceRecheckCadenceTeamRollup",
    "build_team_memory_source_recheck_cadence_exception_report",
    "team_memory_source_recheck_cadence_exception_report_payload",
)

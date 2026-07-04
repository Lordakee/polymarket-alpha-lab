"""Pure in-memory team memory source recheck cadence readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_READINESS_CONFIG_VERSION = (
    "team-memory-source-recheck-cadence-readiness-v0"
)

EMPTY_REASON = "team_memory_source_recheck_cadence_readiness_empty_observations"
MISSING_EVIDENCE_REASON = (
    "team_memory_source_recheck_cadence_readiness_missing_evidence"
)
OVERDUE_RECHECK_REASON = "team_memory_source_recheck_cadence_readiness_overdue_recheck"
STALE_EVIDENCE_REASON = "team_memory_source_recheck_cadence_readiness_stale_evidence"
DUE_RECHECK_REASON = "team_memory_source_recheck_cadence_readiness_due_recheck"
FRESH_EVIDENCE_REASON = "team_memory_source_recheck_cadence_readiness_fresh_evidence"
READY_REASON = "team_memory_source_recheck_cadence_readiness_ready"

REASON_CODES = (
    EMPTY_REASON,
    MISSING_EVIDENCE_REASON,
    OVERDUE_RECHECK_REASON,
    STALE_EVIDENCE_REASON,
    DUE_RECHECK_REASON,
    FRESH_EVIDENCE_REASON,
    READY_REASON,
)
BLOCKING_REASONS = frozenset(
    (
        EMPTY_REASON,
        MISSING_EVIDENCE_REASON,
        OVERDUE_RECHECK_REASON,
        STALE_EVIDENCE_REASON,
    ),
)
WATCH_REASONS = frozenset((DUE_RECHECK_REASON,))
READINESS_STATUSES = ("ready", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "ready": 2}
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "li" "ve",
        "au" "th",
        "wal" "let",
        "ord" "er",
        "can" "cel",
        "rep" "lace",
        "tr" "ade",
        "bro" "ker",
        "cred" "ential",
        "sec" "ret",
        "private" "_" "key",
        "bal" "ance",
        "acc" "ount",
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceReadinessConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_READINESS_CONFIG_VERSION
    fresh_age_threshold_seconds: Decimal = Decimal("7200")
    stale_age_threshold_seconds: Decimal = Decimal("14400")
    due_soon_window_seconds: Decimal = Decimal("1800")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_age_threshold_seconds",
            _require_positive_decimal(
                "fresh_age_threshold_seconds",
                self.fresh_age_threshold_seconds,
            ),
        )
        object.__setattr__(
            self,
            "stale_age_threshold_seconds",
            _require_positive_decimal(
                "stale_age_threshold_seconds",
                self.stale_age_threshold_seconds,
            ),
        )
        object.__setattr__(
            self,
            "due_soon_window_seconds",
            _require_nonnegative_decimal(
                "due_soon_window_seconds",
                self.due_soon_window_seconds,
            ),
        )
        if self.fresh_age_threshold_seconds > self.stale_age_threshold_seconds:
            raise ValueError(
                "fresh_age_threshold_seconds must not exceed stale_age_threshold_seconds",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceReadinessInputRow:
    team_id: str
    category_id: str
    source_key: str
    source_family: str
    last_evidence_at: datetime | None
    next_recheck_due_at: datetime
    evidence_count: Decimal = ONE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("source_key", self.source_key)
        _require_public_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "last_evidence_at",
            _as_optional_utc("last_evidence_at", self.last_evidence_at),
        )
        object.__setattr__(
            self,
            "next_recheck_due_at",
            _as_utc("next_recheck_due_at", self.next_recheck_due_at),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_decimal("evidence_count", self.evidence_count),
        )
        require_paper_only_flags("input row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow:
    category_id: str
    team_id: str
    source_family: str
    readiness_status: str
    source_count: Decimal
    fresh_source_count: Decimal
    due_source_count: Decimal
    overdue_source_count: Decimal
    stale_source_count: Decimal
    missing_evidence_source_count: Decimal
    max_evidence_age_seconds: Decimal
    max_recheck_overdue_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("source_family", self.source_family)
        _require_readiness_status("readiness_status", self.readiness_status)
        for field_name in _SOURCE_METRIC_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_source_family_row(self)
        require_paper_only_flags("source family row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceReadinessTeamRow:
    category_id: str
    team_id: str
    readiness_status: str
    source_family_count: Decimal
    source_count: Decimal
    fresh_source_count: Decimal
    due_source_count: Decimal
    overdue_source_count: Decimal
    stale_source_count: Decimal
    missing_evidence_source_count: Decimal
    fresh_source_ratio: Decimal
    overdue_source_ratio: Decimal
    max_evidence_age_seconds: Decimal
    max_recheck_overdue_age_seconds: Decimal
    source_family_rows: tuple[TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_readiness_status("readiness_status", self.readiness_status)
        for field_name in ("source_family_count", *_SOURCE_METRIC_FIELDS):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("fresh_source_ratio", "overdue_source_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family_rows",
            _normalize_source_family_rows(self.source_family_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_team_row(self)
        require_paper_only_flags("team row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        require_paper_only_flags("reason count", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceReadinessReport:
    generated_at: datetime
    config_version: str
    readiness_status: str
    team_count: Decimal
    team_category_count: Decimal
    source_family_count: Decimal
    source_count: Decimal
    fresh_source_count: Decimal
    due_source_count: Decimal
    overdue_source_count: Decimal
    stale_source_count: Decimal
    missing_evidence_source_count: Decimal
    ready_team_count: Decimal
    watch_team_count: Decimal
    blocked_team_count: Decimal
    fresh_source_ratio: Decimal
    overdue_source_ratio: Decimal
    max_evidence_age_seconds: Decimal
    max_recheck_overdue_age_seconds: Decimal
    team_rows: tuple[TeamMemorySourceRecheckCadenceReadinessTeamRow, ...]
    reason_code_counts: tuple[TeamMemorySourceRecheckCadenceReadinessReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_readiness_status("readiness_status", self.readiness_status)
        for field_name in (
            "team_count",
            "team_category_count",
            "source_family_count",
            *_SOURCE_METRIC_FIELDS,
            "ready_team_count",
            "watch_team_count",
            "blocked_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("fresh_source_ratio", "overdue_source_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "team_rows", _normalize_team_rows(self.team_rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)


def build_team_memory_source_recheck_cadence_readiness_report(
    input_rows: list[TeamMemorySourceRecheckCadenceReadinessInputRow]
    | tuple[TeamMemorySourceRecheckCadenceReadinessInputRow, ...],
    *,
    config: TeamMemorySourceRecheckCadenceReadinessConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceReadinessReport:
    if type(config) is not TeamMemorySourceRecheckCadenceReadinessConfig:
        raise ValueError(
            "config must be a TeamMemorySourceRecheckCadenceReadinessConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    team_rows = _team_rows(rows, config=config, generated_at=generated_at_utc)
    reason_codes = _report_reason_codes(team_rows)
    return TeamMemorySourceRecheckCadenceReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        readiness_status=_status_from_reason_codes(reason_codes),
        team_count=_decimal_count(len({row.team_id for row in rows})),
        team_category_count=_decimal_count(len(team_rows)),
        source_family_count=_sum_decimal(team_rows, "source_family_count"),
        source_count=_sum_decimal(team_rows, "source_count"),
        fresh_source_count=_sum_decimal(team_rows, "fresh_source_count"),
        due_source_count=_sum_decimal(team_rows, "due_source_count"),
        overdue_source_count=_sum_decimal(team_rows, "overdue_source_count"),
        stale_source_count=_sum_decimal(team_rows, "stale_source_count"),
        missing_evidence_source_count=_sum_decimal(
            team_rows,
            "missing_evidence_source_count",
        ),
        ready_team_count=_team_status_count(team_rows, "ready"),
        watch_team_count=_team_status_count(team_rows, "watch"),
        blocked_team_count=_team_status_count(team_rows, "blocked"),
        fresh_source_ratio=_ratio(_sum_decimal(team_rows, "fresh_source_count"), _decimal_count(len(rows))),
        overdue_source_ratio=_ratio(
            _sum_decimal(team_rows, "overdue_source_count"),
            _decimal_count(len(rows)),
        ),
        max_evidence_age_seconds=_max_decimal(team_rows, "max_evidence_age_seconds"),
        max_recheck_overdue_age_seconds=_max_decimal(
            team_rows,
            "max_recheck_overdue_age_seconds",
        ),
        team_rows=team_rows,
        reason_code_counts=_reason_code_counts(team_rows, reason_codes),
        reason_codes=reason_codes,
    )


def team_memory_source_recheck_cadence_readiness_report_payload(
    report: TeamMemorySourceRecheckCadenceReadinessReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemorySourceRecheckCadenceReadinessReport:
        raise ValueError(
            "report must be a TeamMemorySourceRecheckCadenceReadinessReport",
        )
    require_paper_only_flags("report", report)
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report must reduce to a JSON object")
    sanitized = _without_source_keys(ready)
    reject_unsafe_surface_fields(
        "team_memory_source_recheck_cadence_readiness_report",
        sanitized,
    )
    return sanitized


_SOURCE_METRIC_FIELDS = (
    "source_count",
    "fresh_source_count",
    "due_source_count",
    "overdue_source_count",
    "stale_source_count",
    "missing_evidence_source_count",
    "max_evidence_age_seconds",
    "max_recheck_overdue_age_seconds",
)
_SOURCE_COUNT_FIELDS = (
    "source_count",
    "fresh_source_count",
    "due_source_count",
    "overdue_source_count",
    "stale_source_count",
    "missing_evidence_source_count",
)
_SOURCE_MAX_FIELDS = (
    "max_evidence_age_seconds",
    "max_recheck_overdue_age_seconds",
)


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceReadinessInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceReadinessInputRow:
            raise ValueError(
                "input rows must contain TeamMemorySourceRecheckCadenceReadinessInputRow",
            )
        require_paper_only_flags("input row", row)
        if row.last_evidence_at is not None and row.last_evidence_at > generated_at:
            raise ValueError("last_evidence_at must not be in the future")
        key = (row.category_id, row.team_id, row.source_key)
        if key in seen:
            raise ValueError("source_key values must be unique per team and category")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.category_id,
                row.team_id,
                row.source_family,
                row.source_key,
            ),
        ),
    )


def _team_rows(
    rows: tuple[TeamMemorySourceRecheckCadenceReadinessInputRow, ...],
    *,
    config: TeamMemorySourceRecheckCadenceReadinessConfig,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceReadinessTeamRow, ...]:
    groups: dict[tuple[str, str], list[TeamMemorySourceRecheckCadenceReadinessInputRow]] = {}
    for row in rows:
        groups.setdefault((row.category_id, row.team_id), []).append(row)
    team_rows = tuple(
        _team_row(
            category_id=category_id,
            team_id=team_id,
            rows=tuple(group_rows),
            config=config,
            generated_at=generated_at,
        )
        for (category_id, team_id), group_rows in sorted(groups.items())
    )
    return tuple(
        sorted(
            team_rows,
            key=lambda row: (
                STATUS_RANK[row.readiness_status],
                row.category_id,
                row.team_id,
            ),
        ),
    )


def _team_row(
    *,
    category_id: str,
    team_id: str,
    rows: tuple[TeamMemorySourceRecheckCadenceReadinessInputRow, ...],
    config: TeamMemorySourceRecheckCadenceReadinessConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceReadinessTeamRow:
    family_rows = _source_family_rows(
        category_id=category_id,
        team_id=team_id,
        rows=rows,
        config=config,
        generated_at=generated_at,
    )
    source_count = _decimal_count(len(rows))
    reason_codes = _aggregate_reason_codes(family_rows)
    return TeamMemorySourceRecheckCadenceReadinessTeamRow(
        category_id=category_id,
        team_id=team_id,
        readiness_status=_status_from_reason_codes(reason_codes),
        source_family_count=_decimal_count(len(family_rows)),
        source_count=source_count,
        fresh_source_count=_sum_decimal(family_rows, "fresh_source_count"),
        due_source_count=_sum_decimal(family_rows, "due_source_count"),
        overdue_source_count=_sum_decimal(family_rows, "overdue_source_count"),
        stale_source_count=_sum_decimal(family_rows, "stale_source_count"),
        missing_evidence_source_count=_sum_decimal(
            family_rows,
            "missing_evidence_source_count",
        ),
        fresh_source_ratio=_ratio(
            _sum_decimal(family_rows, "fresh_source_count"),
            source_count,
        ),
        overdue_source_ratio=_ratio(
            _sum_decimal(family_rows, "overdue_source_count"),
            source_count,
        ),
        max_evidence_age_seconds=_max_decimal(family_rows, "max_evidence_age_seconds"),
        max_recheck_overdue_age_seconds=_max_decimal(
            family_rows,
            "max_recheck_overdue_age_seconds",
        ),
        source_family_rows=family_rows,
        reason_codes=reason_codes,
    )


def _source_family_rows(
    *,
    category_id: str,
    team_id: str,
    rows: tuple[TeamMemorySourceRecheckCadenceReadinessInputRow, ...],
    config: TeamMemorySourceRecheckCadenceReadinessConfig,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow, ...]:
    groups: dict[str, list[TeamMemorySourceRecheckCadenceReadinessInputRow]] = {}
    for row in rows:
        groups.setdefault(row.source_family, []).append(row)
    family_rows = tuple(
        _source_family_row(
            category_id=category_id,
            team_id=team_id,
            source_family=source_family,
            rows=tuple(group_rows),
            config=config,
            generated_at=generated_at,
        )
        for source_family, group_rows in sorted(groups.items())
    )
    return tuple(
        sorted(
            family_rows,
            key=lambda row: (
                STATUS_RANK[row.readiness_status],
                row.source_family,
            ),
        ),
    )


def _source_family_row(
    *,
    category_id: str,
    team_id: str,
    source_family: str,
    rows: tuple[TeamMemorySourceRecheckCadenceReadinessInputRow, ...],
    config: TeamMemorySourceRecheckCadenceReadinessConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow:
    evidence_ages = tuple(_evidence_age_seconds(generated_at, row) for row in rows)
    overdue_ages = tuple(_overdue_age_seconds(generated_at, row) for row in rows)
    fresh_count = _decimal_count(
        sum(
            _has_evidence(row)
            and age <= config.fresh_age_threshold_seconds
            for row, age in zip(rows, evidence_ages, strict=True)
        ),
    )
    due_count = _decimal_count(
        sum(
            row.next_recheck_due_at >= generated_at
            and _age_seconds(row.next_recheck_due_at, generated_at)
            <= config.due_soon_window_seconds
            for row in rows
        ),
    )
    overdue_count = _decimal_count(sum(age > ZERO for age in overdue_ages))
    stale_count = _decimal_count(
        sum(
            _has_evidence(row)
            and age > config.stale_age_threshold_seconds
            for row, age in zip(rows, evidence_ages, strict=True)
        ),
    )
    missing_count = _decimal_count(
        sum(row.last_evidence_at is None or row.evidence_count == ZERO for row in rows),
    )
    reason_codes = _metric_reason_codes(
        fresh_source_count=fresh_count,
        due_source_count=due_count,
        overdue_source_count=overdue_count,
        stale_source_count=stale_count,
        missing_evidence_source_count=missing_count,
    )
    return TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow(
        category_id=category_id,
        team_id=team_id,
        source_family=source_family,
        readiness_status=_status_from_reason_codes(reason_codes),
        source_count=_decimal_count(len(rows)),
        fresh_source_count=fresh_count,
        due_source_count=due_count,
        overdue_source_count=overdue_count,
        stale_source_count=stale_count,
        missing_evidence_source_count=missing_count,
        max_evidence_age_seconds=max(evidence_ages, default=ZERO),
        max_recheck_overdue_age_seconds=max(overdue_ages, default=ZERO),
        reason_codes=reason_codes,
    )


def _metric_reason_codes(
    *,
    fresh_source_count: Decimal,
    due_source_count: Decimal,
    overdue_source_count: Decimal,
    stale_source_count: Decimal,
    missing_evidence_source_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if missing_evidence_source_count > ZERO:
        reason_codes.append(MISSING_EVIDENCE_REASON)
    if overdue_source_count > ZERO:
        reason_codes.append(OVERDUE_RECHECK_REASON)
    if stale_source_count > ZERO:
        reason_codes.append(STALE_EVIDENCE_REASON)
    if due_source_count > ZERO:
        reason_codes.append(DUE_RECHECK_REASON)
    if fresh_source_count > ZERO:
        reason_codes.append(FRESH_EVIDENCE_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return tuple(reason_codes)


def _aggregate_reason_codes(
    rows: tuple[
        TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow,
        ...,
    ]
    | tuple[TeamMemorySourceRecheckCadenceReadinessTeamRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)


def _report_reason_codes(
    team_rows: tuple[TeamMemorySourceRecheckCadenceReadinessTeamRow, ...],
) -> tuple[str, ...]:
    if not team_rows:
        return (EMPTY_REASON,)
    return _aggregate_reason_codes(team_rows)


def _reason_code_counts(
    team_rows: tuple[TeamMemorySourceRecheckCadenceReadinessTeamRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[TeamMemorySourceRecheckCadenceReadinessReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REASON,):
        return (
            TeamMemorySourceRecheckCadenceReadinessReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counts: list[TeamMemorySourceRecheckCadenceReadinessReasonCodeCount] = []
    for reason_code in reason_codes:
        if reason_code == READY_REASON:
            count = _team_reason_count(team_rows, reason_code)
        else:
            count = _sum_reason_source_count(team_rows, reason_code)
        if count > ZERO:
            counts.append(
                TeamMemorySourceRecheckCadenceReadinessReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _sum_reason_source_count(
    team_rows: tuple[TeamMemorySourceRecheckCadenceReadinessTeamRow, ...],
    reason_code: str,
) -> Decimal:
    field_name = {
        MISSING_EVIDENCE_REASON: "missing_evidence_source_count",
        OVERDUE_RECHECK_REASON: "overdue_source_count",
        STALE_EVIDENCE_REASON: "stale_source_count",
        DUE_RECHECK_REASON: "due_source_count",
        FRESH_EVIDENCE_REASON: "fresh_source_count",
    }.get(reason_code)
    if field_name is None:
        return ZERO
    return _sum_decimal(team_rows, field_name)


def _team_reason_count(
    team_rows: tuple[TeamMemorySourceRecheckCadenceReadinessTeamRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(reason_code in row.reason_codes for row in team_rows))


def _team_status_count(
    team_rows: tuple[TeamMemorySourceRecheckCadenceReadinessTeamRow, ...],
    readiness_status: str,
) -> Decimal:
    return _decimal_count(sum(row.readiness_status == readiness_status for row in team_rows))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASONS for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "ready"


def _overdue_age_seconds(
    generated_at: datetime,
    row: TeamMemorySourceRecheckCadenceReadinessInputRow,
) -> Decimal:
    if row.next_recheck_due_at >= generated_at:
        return ZERO
    return _age_seconds(generated_at, row.next_recheck_due_at)


def _evidence_age_seconds(
    generated_at: datetime,
    row: TeamMemorySourceRecheckCadenceReadinessInputRow,
) -> Decimal:
    if not _has_evidence(row):
        return ZERO
    return _age_seconds(generated_at, row.last_evidence_at)


def _has_evidence(row: TeamMemorySourceRecheckCadenceReadinessInputRow) -> bool:
    return row.last_evidence_at is not None and row.evidence_count > ZERO


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _sum_decimal(rows: tuple[object, ...], field_name: str) -> Decimal:
    total = ZERO
    for row in rows:
        value = getattr(row, field_name)
        if type(value) is not Decimal:
            raise ValueError(f"{field_name} must be a Decimal")
        total += value
    return _quantize(total)


def _max_decimal(rows: tuple[object, ...], field_name: str) -> Decimal:
    values = tuple(getattr(row, field_name) for row in rows)
    for value in values:
        if type(value) is not Decimal:
            raise ValueError(f"{field_name} must be a Decimal")
    return max(values, default=ZERO)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty string")
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} must be public")
    return value


def _require_readiness_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{field_name} must be a readiness status")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _normalize_source_family_rows(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("source_family_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow:
            raise ValueError(
                "source_family_rows must contain TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow",
            )
        require_paper_only_flags("source family row", row)
    return rows


def _normalize_team_rows(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceReadinessTeamRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceReadinessTeamRow:
            raise ValueError(
                "team_rows must contain TeamMemorySourceRecheckCadenceReadinessTeamRow",
            )
        require_paper_only_flags("team row", row)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceReadinessReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain TeamMemorySourceRecheckCadenceReadinessReasonCodeCount",
            )
        require_paper_only_flags("reason count", row)
    return rows


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _validate_source_family_row(
    row: TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow,
) -> None:
    if row.fresh_source_count > row.source_count:
        raise ValueError("fresh_source_count must not exceed source_count")
    if row.due_source_count > row.source_count:
        raise ValueError("due_source_count must not exceed source_count")
    if row.overdue_source_count > row.source_count:
        raise ValueError("overdue_source_count must not exceed source_count")
    if row.stale_source_count > row.source_count:
        raise ValueError("stale_source_count must not exceed source_count")
    if row.missing_evidence_source_count > row.source_count:
        raise ValueError("missing_evidence_source_count must not exceed source_count")
    if row.readiness_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("readiness_status must match reason_codes")


def _validate_team_row(row: TeamMemorySourceRecheckCadenceReadinessTeamRow) -> None:
    if row.source_family_count != _decimal_count(len(row.source_family_rows)):
        raise ValueError("source_family_count must match source_family_rows")
    for field_name in _SOURCE_COUNT_FIELDS:
        if getattr(row, field_name) != _sum_decimal(row.source_family_rows, field_name):
            raise ValueError(f"{field_name} must match source_family_rows")
    for field_name in _SOURCE_MAX_FIELDS:
        if getattr(row, field_name) != _max_decimal(row.source_family_rows, field_name):
            raise ValueError(f"{field_name} must match source_family_rows")
    if row.fresh_source_ratio != _ratio(row.fresh_source_count, row.source_count):
        raise ValueError("fresh_source_ratio must match source counts")
    if row.overdue_source_ratio != _ratio(row.overdue_source_count, row.source_count):
        raise ValueError("overdue_source_ratio must match source counts")
    if row.readiness_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("readiness_status must match reason_codes")


def _validate_report(report: TeamMemorySourceRecheckCadenceReadinessReport) -> None:
    if report.team_category_count != _decimal_count(len(report.team_rows)):
        raise ValueError("team_category_count must match team_rows")
    if report.team_count != _decimal_count(len({row.team_id for row in report.team_rows})):
        raise ValueError("team_count must match team_rows")
    for field_name in ("source_family_count", *_SOURCE_COUNT_FIELDS):
        if getattr(report, field_name) != _sum_decimal(report.team_rows, field_name):
            raise ValueError(f"{field_name} must match team_rows")
    for field_name in _SOURCE_MAX_FIELDS:
        if getattr(report, field_name) != _max_decimal(report.team_rows, field_name):
            raise ValueError(f"{field_name} must match team_rows")
    if report.ready_team_count != _team_status_count(report.team_rows, "ready"):
        raise ValueError("ready_team_count must match team_rows")
    if report.watch_team_count != _team_status_count(report.team_rows, "watch"):
        raise ValueError("watch_team_count must match team_rows")
    if report.blocked_team_count != _team_status_count(report.team_rows, "blocked"):
        raise ValueError("blocked_team_count must match team_rows")
    if report.fresh_source_ratio != _ratio(report.fresh_source_count, report.source_count):
        raise ValueError("fresh_source_ratio must match source counts")
    if report.overdue_source_ratio != _ratio(
        report.overdue_source_count,
        report.source_count,
    ):
        raise ValueError("overdue_source_ratio must match source counts")
    if report.readiness_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("readiness_status must match reason_codes")


def _without_source_keys(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _without_source_keys(item)
            for key, item in value.items()
            if key != "source_key"
        }
    if isinstance(value, list):
        return [_without_source_keys(item) for item in value]
    return value


__all__ = (
    "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_READINESS_CONFIG_VERSION",
    "TeamMemorySourceRecheckCadenceReadinessConfig",
    "TeamMemorySourceRecheckCadenceReadinessInputRow",
    "TeamMemorySourceRecheckCadenceReadinessReasonCodeCount",
    "TeamMemorySourceRecheckCadenceReadinessReport",
    "TeamMemorySourceRecheckCadenceReadinessSourceFamilyRow",
    "TeamMemorySourceRecheckCadenceReadinessTeamRow",
    "build_team_memory_source_recheck_cadence_readiness_report",
    "team_memory_source_recheck_cadence_readiness_report_payload",
)

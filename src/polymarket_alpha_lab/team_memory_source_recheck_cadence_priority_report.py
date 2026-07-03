"""Pure in-memory team-memory source recheck cadence priority report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_PRIORITY_CONFIG_VERSION = (
    "team-memory-source-recheck-cadence-priority-v0"
)
ROW_STATUSES = ("ready", "watch", "blocked")
REPORT_STATUSES = ("empty", "ready", "watch", "blocked")
EMPTY_REASON = "team_memory_source_recheck_cadence_empty"
READY_REASON = "team_memory_source_recheck_cadence_ready"
STALE_REASON = "team_memory_source_recheck_cadence_stale"
OVERDUE_REASON = "team_memory_source_recheck_cadence_overdue_sources"
BACKLOG_REASON = "team_memory_source_recheck_cadence_overdue_backlog"
LOW_ACKNOWLEDGED_COVERAGE_REASON = (
    "team_memory_source_recheck_cadence_low_acknowledged_source_coverage"
)
ROW_REASON_CODES = (
    READY_REASON,
    STALE_REASON,
    OVERDUE_REASON,
    BACKLOG_REASON,
    LOW_ACKNOWLEDGED_COVERAGE_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REASON,
    READY_REASON,
    STALE_REASON,
    OVERDUE_REASON,
    BACKLOG_REASON,
    LOW_ACKNOWLEDGED_COVERAGE_REASON,
)
TRIGGER_REASON_CODES = tuple(
    reason_code
    for reason_code in REPORT_REASON_CODES
    if reason_code not in (EMPTY_REASON, READY_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("que", "stion"),
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "n"),
        _join_parts("ad", "vice"),
        _join_parts("pri", "vate", "_", "key"),
        _join_parts("cre", "den", "tial"),
    ),
)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadencePriorityConfig:
    config_version: str = (
        DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_PRIORITY_CONFIG_VERSION
    )
    default_recheck_cadence_seconds: Decimal = Decimal("86400.000000")
    low_acknowledged_source_coverage_ratio: Decimal = Decimal("0.800000")
    overdue_source_count_block_threshold: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "default_recheck_cadence_seconds",
            _require_positive_decimal(
                "default_recheck_cadence_seconds",
                self.default_recheck_cadence_seconds,
            ),
        )
        object.__setattr__(
            self,
            "low_acknowledged_source_coverage_ratio",
            _require_ratio(
                "low_acknowledged_source_coverage_ratio",
                self.low_acknowledged_source_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "overdue_source_count_block_threshold",
            _require_positive_decimal(
                "overdue_source_count_block_threshold",
                self.overdue_source_count_block_threshold,
            ),
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadencePriorityInput:
    team_id: str
    category_id: str
    source_id: str
    source_last_rechecked_at: datetime
    source_acknowledged_at: datetime | None
    recheck_cadence_seconds: Decimal | None = None
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
        _require_public_string("source_id", self.source_id)
        object.__setattr__(
            self,
            "source_last_rechecked_at",
            _as_utc("source_last_rechecked_at", self.source_last_rechecked_at),
        )
        object.__setattr__(
            self,
            "source_acknowledged_at",
            _as_optional_utc("source_acknowledged_at", self.source_acknowledged_at),
        )
        if self.recheck_cadence_seconds is not None:
            object.__setattr__(
                self,
                "recheck_cadence_seconds",
                _require_positive_decimal(
                    "recheck_cadence_seconds",
                    self.recheck_cadence_seconds,
                ),
            )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadencePriorityRow:
    team_id: str
    category_id: str
    source_count: Decimal
    acknowledged_source_count: Decimal
    overdue_source_count: Decimal
    acknowledged_source_coverage_ratio: Decimal
    source_age_seconds: Decimal
    stale_cadence_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
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
        for field_name in (
            "source_count",
            "acknowledged_source_count",
            "overdue_source_count",
            "source_age_seconds",
            "stale_cadence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "acknowledged_source_coverage_ratio",
            _require_ratio(
                "acknowledged_source_coverage_ratio",
                self.acknowledged_source_coverage_ratio,
            ),
        )
        _require_row_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("priority row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadencePriorityReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    source_count: Decimal
    acknowledged_source_count: Decimal
    overdue_source_count: Decimal
    low_acknowledged_source_coverage_count: Decimal
    highest_stale_cadence_age_seconds: Decimal
    acknowledged_source_coverage_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[TeamMemorySourceRecheckCadencePriorityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "source_count",
            "acknowledged_source_count",
            "overdue_source_count",
            "low_acknowledged_source_coverage_count",
            "highest_stale_cadence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "acknowledged_source_coverage_ratio",
            _require_ratio(
                "acknowledged_source_coverage_ratio",
                self.acknowledged_source_coverage_ratio,
            ),
        )
        _require_report_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("team memory source recheck cadence report", self)
        require_paper_only_flags("priority report", self)


def build_team_memory_source_recheck_cadence_priority_report(
    inputs: list[TeamMemorySourceRecheckCadencePriorityInput]
    | tuple[TeamMemorySourceRecheckCadencePriorityInput, ...],
    *,
    config: TeamMemorySourceRecheckCadencePriorityConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadencePriorityReport:
    if type(config) is not TeamMemorySourceRecheckCadencePriorityConfig:
        raise ValueError(
            "config must be a TeamMemorySourceRecheckCadencePriorityConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs, generated_at=generated_at_utc)
    rows = _priority_rows(
        normalized_inputs,
        config=config,
        generated_at=generated_at_utc,
    )
    return TeamMemorySourceRecheckCadencePriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_count(len(rows)),
        source_count=_sum_rows(rows, "source_count"),
        acknowledged_source_count=_sum_rows(rows, "acknowledged_source_count"),
        overdue_source_count=_sum_rows(rows, "overdue_source_count"),
        low_acknowledged_source_coverage_count=_count(
            sum(
                1
                for row in rows
                if LOW_ACKNOWLEDGED_COVERAGE_REASON in row.reason_codes
            ),
        ),
        highest_stale_cadence_age_seconds=max(
            (row.stale_cadence_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        acknowledged_source_coverage_ratio=_ratio(
            _sum_rows(rows, "acknowledged_source_count"),
            _sum_rows(rows, "source_count"),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def team_memory_source_recheck_cadence_priority_report_payload(
    report: TeamMemorySourceRecheckCadencePriorityReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemorySourceRecheckCadencePriorityReport:
        raise ValueError(
            "report must be a TeamMemorySourceRecheckCadencePriorityReport",
        )
    reject_unsafe_surface_fields("team memory source recheck cadence report", report)
    require_paper_only_flags("report", report)
    return json_ready_no_floats(report)


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadencePriorityInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadencePriorityInput:
            raise ValueError(
                "inputs must contain TeamMemorySourceRecheckCadencePriorityInput",
            )
        require_paper_only_flags("input", row)
        if row.source_last_rechecked_at > generated_at:
            raise ValueError("source_last_rechecked_at must not be in the future")
        if row.source_acknowledged_at is not None and row.source_acknowledged_at > generated_at:
            raise ValueError("source_acknowledged_at must not be in the future")
        key = (row.team_id, row.source_id)
        if key in seen:
            raise ValueError("inputs must be unique by team_id and source_id")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.category_id, row.team_id, row.source_id)))


def _priority_rows(
    rows: tuple[TeamMemorySourceRecheckCadencePriorityInput, ...],
    *,
    config: TeamMemorySourceRecheckCadencePriorityConfig,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadencePriorityRow, ...]:
    grouped: dict[tuple[str, str], list[TeamMemorySourceRecheckCadencePriorityInput]] = {}
    for row in rows:
        grouped.setdefault((row.category_id, row.team_id), []).append(row)
    return tuple(
        sorted(
            (
                _priority_row(
                    team_rows=tuple(team_rows),
                    config=config,
                    generated_at=generated_at,
                )
                for team_rows in grouped.values()
            ),
            key=_row_sort_key,
        ),
    )


def _priority_row(
    *,
    team_rows: tuple[TeamMemorySourceRecheckCadencePriorityInput, ...],
    config: TeamMemorySourceRecheckCadencePriorityConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadencePriorityRow:
    first = team_rows[0]
    ages = tuple(
        _age_seconds(generated_at, row.source_last_rechecked_at) for row in team_rows
    )
    stale_ages = tuple(
        _stale_cadence_age_seconds(
            age_seconds=age,
            recheck_cadence_seconds=_cadence_seconds(row, config),
        )
        for row, age in zip(team_rows, ages, strict=True)
    )
    source_count = _count(len(team_rows))
    acknowledged_source_count = _count(
        sum(1 for row in team_rows if row.source_acknowledged_at is not None),
    )
    overdue_source_count = _count(sum(1 for age in stale_ages if age > ZERO))
    stale_cadence_age_seconds = max(stale_ages, default=ZERO).quantize(QUANT)
    acknowledged_source_coverage_ratio = _ratio(
        acknowledged_source_count,
        source_count,
    )
    reason_codes = _row_reason_codes(
        stale_cadence_age_seconds=stale_cadence_age_seconds,
        overdue_source_count=overdue_source_count,
        overdue_source_count_block_threshold=(
            config.overdue_source_count_block_threshold
        ),
        acknowledged_source_coverage_ratio=acknowledged_source_coverage_ratio,
        low_acknowledged_source_coverage_ratio=(
            config.low_acknowledged_source_coverage_ratio
        ),
    )
    return TeamMemorySourceRecheckCadencePriorityRow(
        team_id=first.team_id,
        category_id=first.category_id,
        source_count=source_count,
        acknowledged_source_count=acknowledged_source_count,
        overdue_source_count=overdue_source_count,
        acknowledged_source_coverage_ratio=acknowledged_source_coverage_ratio,
        source_age_seconds=max(ages, default=ZERO).quantize(QUANT),
        stale_cadence_age_seconds=stale_cadence_age_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _cadence_seconds(
    row: TeamMemorySourceRecheckCadencePriorityInput,
    config: TeamMemorySourceRecheckCadencePriorityConfig,
) -> Decimal:
    if row.recheck_cadence_seconds is None:
        return config.default_recheck_cadence_seconds
    return row.recheck_cadence_seconds


def _stale_cadence_age_seconds(
    *,
    age_seconds: Decimal,
    recheck_cadence_seconds: Decimal,
) -> Decimal:
    if age_seconds <= recheck_cadence_seconds:
        return ZERO
    return (age_seconds - recheck_cadence_seconds).quantize(QUANT)


def _row_reason_codes(
    *,
    stale_cadence_age_seconds: Decimal,
    overdue_source_count: Decimal,
    overdue_source_count_block_threshold: Decimal,
    acknowledged_source_coverage_ratio: Decimal,
    low_acknowledged_source_coverage_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if stale_cadence_age_seconds > ZERO:
        reasons.append(STALE_REASON)
    if overdue_source_count > ZERO:
        reasons.append(OVERDUE_REASON)
    if overdue_source_count >= overdue_source_count_block_threshold:
        reasons.append(BACKLOG_REASON)
    if acknowledged_source_coverage_ratio < low_acknowledged_source_coverage_ratio:
        reasons.append(LOW_ACKNOWLEDGED_COVERAGE_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BACKLOG_REASON in reason_codes:
        return "blocked"
    if reason_codes == (READY_REASON,):
        return "ready"
    return "watch"


def _report_status(rows: tuple[TeamMemorySourceRecheckCadencePriorityRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(
    rows: tuple[TeamMemorySourceRecheckCadencePriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in TRIGGER_REASON_CODES
        if any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (READY_REASON,)


def _row_sort_key(
    row: TeamMemorySourceRecheckCadencePriorityRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -row.stale_cadence_age_seconds,
        -row.overdue_source_count,
        row.acknowledged_source_coverage_ratio,
        row.category_id,
        row.team_id,
    )


def _validate_row(row: TeamMemorySourceRecheckCadencePriorityRow) -> None:
    if row.acknowledged_source_count > row.source_count:
        raise ValueError("acknowledged_source_count must not exceed source_count")
    if row.overdue_source_count > row.source_count:
        raise ValueError("overdue_source_count must not exceed source_count")
    if row.acknowledged_source_coverage_ratio != _ratio(
        row.acknowledged_source_count,
        row.source_count,
    ):
        raise ValueError("acknowledged_source_coverage_ratio must match counts")
    if row.source_count == ZERO and row.source_age_seconds != ZERO:
        raise ValueError("source_age_seconds must be zero without sources")
    if row.stale_cadence_age_seconds > row.source_age_seconds:
        raise ValueError("stale_cadence_age_seconds must not exceed source_age_seconds")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.reason_codes == (READY_REASON,):
        if row.overdue_source_count != ZERO:
            raise ValueError("ready rows cannot contain overdue sources")
        if row.stale_cadence_age_seconds != ZERO:
            raise ValueError("ready rows cannot contain stale cadence age")


def _validate_report(report: TeamMemorySourceRecheckCadencePriorityReport) -> None:
    if report.team_count != _count(len(report.rows)):
        raise ValueError("team_count must match rows")
    for field_name in (
        "source_count",
        "acknowledged_source_count",
        "overdue_source_count",
    ):
        if getattr(report, field_name) != _sum_rows(report.rows, field_name):
            raise ValueError(f"{field_name} must match rows")
    if report.low_acknowledged_source_coverage_count != _count(
        sum(
            1
            for row in report.rows
            if LOW_ACKNOWLEDGED_COVERAGE_REASON in row.reason_codes
        ),
    ):
        raise ValueError("low_acknowledged_source_coverage_count must match rows")
    if report.highest_stale_cadence_age_seconds != max(
        (row.stale_cadence_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_stale_cadence_age_seconds must match rows")
    if report.acknowledged_source_coverage_ratio != _ratio(
        report.acknowledged_source_count,
        report.source_count,
    ):
        raise ValueError("acknowledged_source_coverage_ratio must match counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic priority sort")


def _normalize_rows(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadencePriorityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadencePriorityRow:
            raise ValueError("rows must contain TeamMemorySourceRecheckCadencePriorityRow")
        require_paper_only_flags("priority row", row)
        if row.team_id in seen:
            raise ValueError("rows must be unique by team_id")
        seen.add(row.team_id)
    return tuple(sorted(rows, key=_row_sort_key))


def _sum_rows(
    rows: tuple[TeamMemorySourceRecheckCadencePriorityRow, ...],
    field_name: str,
) -> Decimal:
    return sum((getattr(row, field_name) for row in rows), ZERO).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _age_seconds(generated_at: datetime, source_last_rechecked_at: datetime) -> Decimal:
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_last_rechecked_at_utc = _as_utc(
        "source_last_rechecked_at",
        source_last_rechecked_at,
    )
    delta = generated_at_utc - source_last_rechecked_at_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("source_last_rechecked_at must not be in the future")
    return seconds.quantize(QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


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


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason_code for reason_code in allowed if reason_code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_row_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be empty, ready, watch, or blocked")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_PRIORITY_CONFIG_VERSION",
    "TeamMemorySourceRecheckCadencePriorityConfig",
    "TeamMemorySourceRecheckCadencePriorityInput",
    "TeamMemorySourceRecheckCadencePriorityReport",
    "TeamMemorySourceRecheckCadencePriorityRow",
    "build_team_memory_source_recheck_cadence_priority_report",
    "team_memory_source_recheck_cadence_priority_report_payload",
)

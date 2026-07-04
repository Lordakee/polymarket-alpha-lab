"""Pure in-memory team memory source recheck cadence health report."""

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
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_HEALTH_CONFIG_VERSION = (
    "team-memory-source-recheck-cadence-health-v0"
)

STATUSES = ("pass", "watch", "blocked")
SOURCE_REASON_CODES = (
    "source_stale_cadence_blocked",
    "source_stale_cadence_watch",
    "source_recheck_overdue",
    "source_not_acknowledged",
    "source_recheck_current",
)
REPORT_REASON_CODES = (
    "no_recheck_sources",
    "stale_cadence_age_blocked",
    "stale_cadence_age_watch",
    "overdue_sources_blocked",
    "overdue_sources_watch",
    "low_acknowledged_source_coverage_blocked",
    "low_acknowledged_source_coverage_watch",
    "source_recheck_cadence_clear",
)
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceHealthConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_HEALTH_CONFIG_VERSION
    watch_stale_age_seconds: Decimal = Decimal("86400.000000")
    blocked_stale_age_seconds: Decimal = Decimal("172800.000000")
    watch_overdue_source_count: Decimal = Decimal("1.000000")
    blocked_overdue_source_count: Decimal = Decimal("3.000000")
    min_acknowledged_source_coverage_ratio: Decimal = Decimal("0.800000")
    blocked_acknowledged_source_coverage_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_stale_age_seconds",
            "blocked_stale_age_seconds",
            "watch_overdue_source_count",
            "blocked_overdue_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_acknowledged_source_coverage_ratio",
            "blocked_acknowledged_source_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceInput:
    team_id: str
    source_id: str
    last_rechecked_at: datetime
    next_recheck_due_at: datetime
    acknowledged_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("source_id", self.source_id)
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "next_recheck_due_at",
            _as_utc("next_recheck_due_at", self.next_recheck_due_at),
        )
        if self.acknowledged_at is not None:
            object.__setattr__(
                self,
                "acknowledged_at",
                _as_utc("acknowledged_at", self.acknowledged_at),
            )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceSourceRow:
    team_id: str
    source_id: str
    last_rechecked_at: datetime
    next_recheck_due_at: datetime
    acknowledged_at: datetime | None
    acknowledged: bool
    source_age_seconds: Decimal
    overdue_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("source_id", self.source_id)
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "next_recheck_due_at",
            _as_utc("next_recheck_due_at", self.next_recheck_due_at),
        )
        if self.acknowledged_at is not None:
            object.__setattr__(
                self,
                "acknowledged_at",
                _as_utc("acknowledged_at", self.acknowledged_at),
            )
        if type(self.acknowledged) is not bool:
            raise ValueError("acknowledged must be a bool")
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "overdue_seconds",
            _require_nonnegative_decimal("overdue_seconds", self.overdue_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                SOURCE_REASON_CODES,
            ),
        )
        _validate_source_row(self)
        require_paper_only_flags("source row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceHealthReport:
    generated_at: datetime
    config_version: str
    status: str
    source_count: Decimal
    stale_source_count: Decimal
    overdue_source_count: Decimal
    acknowledged_source_count: Decimal
    acknowledged_source_coverage_ratio: Decimal
    stale_cadence_age_seconds: Decimal
    max_overdue_seconds: Decimal
    source_rows: tuple[TeamMemorySourceRecheckCadenceSourceRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "source_count",
            "stale_source_count",
            "overdue_source_count",
            "acknowledged_source_count",
            "acknowledged_source_coverage_ratio",
            "stale_cadence_age_seconds",
            "max_overdue_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.acknowledged_source_coverage_ratio > ONE:
            raise ValueError("acknowledged_source_coverage_ratio must be at most one")
        object.__setattr__(self, "source_rows", _normalize_source_rows(self.source_rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("source recheck cadence health report", self)
        require_paper_only_flags("report", self)


def build_team_memory_source_recheck_cadence_health_report(
    inputs: list[TeamMemorySourceRecheckCadenceInput]
    | tuple[TeamMemorySourceRecheckCadenceInput, ...],
    *,
    config: TeamMemorySourceRecheckCadenceHealthConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceHealthReport:
    if type(config) is not TeamMemorySourceRecheckCadenceHealthConfig:
        raise ValueError("config must be a TeamMemorySourceRecheckCadenceHealthConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _source_rows(
        _normalize_inputs(inputs, generated_at=generated_at_utc),
        config=config,
        generated_at=generated_at_utc,
    )
    reason_codes = _report_reason_codes(rows, config=config)
    return TeamMemorySourceRecheckCadenceHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(reason_codes),
        source_count=_decimal_count(len(rows)),
        stale_source_count=_decimal_count(
            sum(1 for row in rows if _is_stale(row, config)),
        ),
        overdue_source_count=_decimal_count(
            sum(1 for row in rows if row.overdue_seconds > ZERO),
        ),
        acknowledged_source_count=_decimal_count(sum(1 for row in rows if row.acknowledged)),
        acknowledged_source_coverage_ratio=_coverage_ratio(
            _decimal_count(sum(1 for row in rows if row.acknowledged)),
            _decimal_count(len(rows)),
        ),
        stale_cadence_age_seconds=_max_decimal(
            tuple(row.source_age_seconds for row in rows),
        ),
        max_overdue_seconds=_max_decimal(tuple(row.overdue_seconds for row in rows)),
        source_rows=rows,
        reason_codes=reason_codes,
    )


def team_memory_source_recheck_cadence_health_payload(
    report: TeamMemorySourceRecheckCadenceHealthReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemorySourceRecheckCadenceHealthReport:
        raise ValueError("report must be a TeamMemorySourceRecheckCadenceHealthReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("source recheck cadence health report", report)
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report must become a JSON object")
    return ready


def _source_rows(
    inputs: tuple[TeamMemorySourceRecheckCadenceInput, ...],
    *,
    config: TeamMemorySourceRecheckCadenceHealthConfig,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceSourceRow, ...]:
    return tuple(
        sorted(
            (
                _source_row(
                    row,
                    config=config,
                    generated_at=generated_at,
                )
                for row in inputs
            ),
            key=_source_row_sort_key,
        ),
    )


def _source_row(
    row: TeamMemorySourceRecheckCadenceInput,
    *,
    config: TeamMemorySourceRecheckCadenceHealthConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceSourceRow:
    age_seconds = _seconds_between(generated_at, row.last_rechecked_at)
    overdue_seconds = _overdue_seconds(generated_at, row.next_recheck_due_at)
    acknowledged = row.acknowledged_at is not None
    reason_codes = _source_reason_codes(
        age_seconds=age_seconds,
        overdue_seconds=overdue_seconds,
        acknowledged=acknowledged,
        config=config,
    )
    return TeamMemorySourceRecheckCadenceSourceRow(
        team_id=row.team_id,
        source_id=row.source_id,
        last_rechecked_at=row.last_rechecked_at,
        next_recheck_due_at=row.next_recheck_due_at,
        acknowledged_at=row.acknowledged_at,
        acknowledged=acknowledged,
        source_age_seconds=age_seconds,
        overdue_seconds=overdue_seconds,
        status=_source_status(reason_codes),
        reason_codes=reason_codes,
    )


def _source_reason_codes(
    *,
    age_seconds: Decimal,
    overdue_seconds: Decimal,
    acknowledged: bool,
    config: TeamMemorySourceRecheckCadenceHealthConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if age_seconds > config.blocked_stale_age_seconds:
        reason_codes.append("source_stale_cadence_blocked")
    elif age_seconds > config.watch_stale_age_seconds:
        reason_codes.append("source_stale_cadence_watch")
    if overdue_seconds > ZERO:
        reason_codes.append("source_recheck_overdue")
    if not acknowledged:
        reason_codes.append("source_not_acknowledged")
    if not reason_codes:
        reason_codes.append("source_recheck_current")
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[TeamMemorySourceRecheckCadenceSourceRow, ...],
    *,
    config: TeamMemorySourceRecheckCadenceHealthConfig,
) -> tuple[str, ...]:
    if not rows:
        return ("no_recheck_sources",)
    max_age = _max_decimal(tuple(row.source_age_seconds for row in rows))
    overdue_count = _decimal_count(sum(1 for row in rows if row.overdue_seconds > ZERO))
    coverage_ratio = _coverage_ratio(
        _decimal_count(sum(1 for row in rows if row.acknowledged)),
        _decimal_count(len(rows)),
    )
    reason_codes: list[str] = []
    if max_age > config.blocked_stale_age_seconds:
        reason_codes.append("stale_cadence_age_blocked")
    elif max_age > config.watch_stale_age_seconds:
        reason_codes.append("stale_cadence_age_watch")
    if overdue_count >= config.blocked_overdue_source_count:
        reason_codes.append("overdue_sources_blocked")
    elif overdue_count >= config.watch_overdue_source_count:
        reason_codes.append("overdue_sources_watch")
    if coverage_ratio < config.blocked_acknowledged_source_coverage_ratio:
        reason_codes.append("low_acknowledged_source_coverage_blocked")
    elif coverage_ratio < config.min_acknowledged_source_coverage_ratio:
        reason_codes.append("low_acknowledged_source_coverage_watch")
    if not reason_codes:
        reason_codes.append("source_recheck_cadence_clear")
    return tuple(reason_codes)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if reason_codes == ("source_recheck_cadence_clear",):
        return "pass"
    return "watch" if reason_codes != ("no_recheck_sources",) else "blocked"


def _source_status(reason_codes: tuple[str, ...]) -> str:
    if "source_stale_cadence_blocked" in reason_codes:
        return "blocked"
    if reason_codes == ("source_recheck_current",):
        return "pass"
    return "watch"


def _source_row_sort_key(
    row: TeamMemorySourceRecheckCadenceSourceRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.overdue_seconds,
        -row.source_age_seconds,
        row.team_id,
        row.source_id,
    )


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceInput:
            raise ValueError("inputs must contain TeamMemorySourceRecheckCadenceInput values")
        require_paper_only_flags("input", row)
        if row.last_rechecked_at > generated_at:
            raise ValueError("last_rechecked_at must not be after generated_at")
        if row.acknowledged_at is not None and row.acknowledged_at > generated_at:
            raise ValueError("acknowledged_at must not be after generated_at")
        key = (row.team_id, row.source_id)
        if key in seen_keys:
            raise ValueError("inputs must be unique by team_id and source_id")
        seen_keys.add(key)
    return rows


def _normalize_source_rows(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceSourceRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("source_rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceSourceRow:
            raise ValueError("source_rows must contain source row values")
        require_paper_only_flags("source row", row)
        key = (row.team_id, row.source_id)
        if key in seen_keys:
            raise ValueError("source_rows must be unique by team_id and source_id")
        seen_keys.add(key)
    return tuple(sorted(rows, key=_source_row_sort_key))


def _validate_config(config: TeamMemorySourceRecheckCadenceHealthConfig) -> None:
    if config.blocked_stale_age_seconds <= config.watch_stale_age_seconds:
        raise ValueError("blocked_stale_age_seconds must exceed watch_stale_age_seconds")
    if config.blocked_overdue_source_count < config.watch_overdue_source_count:
        raise ValueError("blocked_overdue_source_count must be at least watch value")
    if (
        config.blocked_acknowledged_source_coverage_ratio
        >= config.min_acknowledged_source_coverage_ratio
    ):
        raise ValueError("blocked acknowledged coverage must be below minimum coverage")


def _validate_source_row(row: TeamMemorySourceRecheckCadenceSourceRow) -> None:
    if row.acknowledged != (row.acknowledged_at is not None):
        raise ValueError("acknowledged must match acknowledged_at")
    if row.status != _source_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("source_recheck_current",):
        raise ValueError("pass rows require current reason")
    if row.status != "pass" and "source_recheck_current" in row.reason_codes:
        raise ValueError("current reason requires pass status")


def _validate_report(report: TeamMemorySourceRecheckCadenceHealthReport) -> None:
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if "no_recheck_sources" in report.reason_codes:
        if report.reason_codes != ("no_recheck_sources",):
            raise ValueError("no_recheck_sources must stand alone")
        if report.source_rows:
            raise ValueError("no_recheck_sources requires no source_rows")
    if (
        "source_recheck_cadence_clear" in report.reason_codes
        and report.reason_codes != ("source_recheck_cadence_clear",)
    ):
        raise ValueError("source_recheck_cadence_clear must stand alone")
    if report.source_count != _decimal_count(len(report.source_rows)):
        raise ValueError("source_count must match source_rows")
    if report.stale_source_count != _decimal_count(
        sum(
            1
            for row in report.source_rows
            if "source_stale_cadence_blocked" in row.reason_codes
            or "source_stale_cadence_watch" in row.reason_codes
        ),
    ):
        raise ValueError("stale_source_count must match source_rows")
    if report.stale_cadence_age_seconds != _max_decimal(
        tuple(row.source_age_seconds for row in report.source_rows),
    ):
        raise ValueError("stale_cadence_age_seconds must match source_rows")
    if report.max_overdue_seconds != _max_decimal(
        tuple(row.overdue_seconds for row in report.source_rows),
    ):
        raise ValueError("max_overdue_seconds must match source_rows")
    if report.overdue_source_count != _decimal_count(
        sum(1 for row in report.source_rows if row.overdue_seconds > ZERO),
    ):
        raise ValueError("overdue_source_count must match source_rows")
    if report.acknowledged_source_count != _decimal_count(
        sum(1 for row in report.source_rows if row.acknowledged),
    ):
        raise ValueError("acknowledged_source_count must match source_rows")
    if report.acknowledged_source_coverage_ratio != _coverage_ratio(
        report.acknowledged_source_count,
        report.source_count,
    ):
        raise ValueError("acknowledged_source_coverage_ratio must match counts")
    if report.source_rows != tuple(sorted(report.source_rows, key=_source_row_sort_key)):
        raise ValueError("source_rows must use deterministic order")


def _is_stale(
    row: TeamMemorySourceRecheckCadenceSourceRow,
    config: TeamMemorySourceRecheckCadenceHealthConfig,
) -> bool:
    return row.source_age_seconds > config.watch_stale_age_seconds


def _coverage_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _overdue_seconds(generated_at: datetime, due_at: datetime) -> Decimal:
    if due_at >= generated_at:
        return ZERO
    return _seconds_between(generated_at, due_at)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    later_utc = _as_utc("later", later)
    earlier_utc = _as_utc("earlier", earlier)
    delta = later_utc - earlier_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds).quantize(QUANT)
        + _microseconds_to_seconds(delta.microseconds)
    )
    if seconds < ZERO:
        raise ValueError("age seconds must be nonnegative")
    return seconds.quantize(QUANT)


def _microseconds_to_seconds(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(value) / MICROSECONDS_PER_SECOND).quantize(QUANT)


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
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return decimal_value


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
    with localcontext(DECIMAL_CONTEXT):
        decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use no more than six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value == ZERO:
        return ZERO
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_HEALTH_CONFIG_VERSION",
    "TeamMemorySourceRecheckCadenceHealthConfig",
    "TeamMemorySourceRecheckCadenceHealthReport",
    "TeamMemorySourceRecheckCadenceInput",
    "TeamMemorySourceRecheckCadenceSourceRow",
    "build_team_memory_source_recheck_cadence_health_report",
    "team_memory_source_recheck_cadence_health_payload",
)

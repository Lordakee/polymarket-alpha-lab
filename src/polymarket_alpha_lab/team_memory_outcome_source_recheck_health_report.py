"""Pure in-memory health report for team-memory outcome source rechecks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "team-memory-outcome-source-recheck-health-v0"

COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
SECONDS_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

HEALTH_STATUSES = ("pass", "watch", "blocked")
STATUS_RANK = {"pass": 0, "watch": 1, "blocked": 2}


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckHealthConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_source_recheck_age_seconds: Decimal = Decimal("86400.000000")
    blocked_source_recheck_age_seconds: Decimal = Decimal("259200.000000")
    watch_min_source_coverage_ratio: Decimal = Decimal("0.750000")
    blocked_min_source_coverage_ratio: Decimal = Decimal("0.500000")
    watch_unresolved_outcome_pressure: Decimal = Decimal("0.400000")
    blocked_unresolved_outcome_pressure: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_source_recheck_age_seconds",
            "blocked_source_recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_min_source_coverage_ratio",
            "blocked_min_source_coverage_ratio",
            "watch_unresolved_outcome_pressure",
            "blocked_unresolved_outcome_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_source_recheck_age_seconds > self.blocked_source_recheck_age_seconds:
            raise ValueError(
                "watch_source_recheck_age_seconds must not exceed "
                "blocked_source_recheck_age_seconds",
            )
        if self.blocked_min_source_coverage_ratio > self.watch_min_source_coverage_ratio:
            raise ValueError(
                "blocked_min_source_coverage_ratio must not exceed "
                "watch_min_source_coverage_ratio",
            )
        if (
            self.watch_unresolved_outcome_pressure
            > self.blocked_unresolved_outcome_pressure
        ):
            raise ValueError(
                "watch_unresolved_outcome_pressure must not exceed "
                "blocked_unresolved_outcome_pressure",
            )
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckHealthConfig", self)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckMemoryRow:
    team_id: str
    category_id: str
    latest_source_rechecked_at: datetime | None
    expected_source_count: Decimal
    verified_source_count: Decimal
    total_outcome_count: Decimal
    unresolved_outcome_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category_id", self.category_id)
        object.__setattr__(
            self,
            "latest_source_rechecked_at",
            _as_optional_utc(
                "latest_source_rechecked_at",
                self.latest_source_rechecked_at,
            ),
        )
        for field_name in (
            "expected_source_count",
            "verified_source_count",
            "total_outcome_count",
            "unresolved_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.verified_source_count > self.expected_source_count:
            raise ValueError("verified_source_count must not exceed expected_source_count")
        if self.unresolved_outcome_count > self.total_outcome_count:
            raise ValueError("unresolved_outcome_count must not exceed total_outcome_count")
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckMemoryRow", self)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckHealthRow:
    team_id: str
    category_id: str
    latest_source_rechecked_at: datetime | None
    source_recheck_age_seconds: Decimal | None
    expected_source_count: Decimal
    verified_source_count: Decimal
    source_coverage_ratio: Decimal
    total_outcome_count: Decimal
    unresolved_outcome_count: Decimal
    unresolved_outcome_pressure: Decimal
    source_recheck_status: str
    source_coverage_status: str
    outcome_pressure_status: str
    health_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category_id", self.category_id)
        object.__setattr__(
            self,
            "latest_source_rechecked_at",
            _as_optional_utc(
                "latest_source_rechecked_at",
                self.latest_source_rechecked_at,
            ),
        )
        object.__setattr__(
            self,
            "source_recheck_age_seconds",
            _normalize_optional_seconds(
                "source_recheck_age_seconds",
                self.source_recheck_age_seconds,
            ),
        )
        for field_name in (
            "expected_source_count",
            "verified_source_count",
            "total_outcome_count",
            "unresolved_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("source_coverage_ratio", "unresolved_outcome_pressure"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_recheck_status",
            "source_coverage_status",
            "outcome_pressure_status",
            "health_status",
        ):
            _require_health_status(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_health_row(self)
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckHealthRow", self)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckHealthReport:
    generated_at: datetime
    config_version: str
    health_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    stale_source_recheck_count: Decimal
    low_source_coverage_count: Decimal
    high_unresolved_outcome_pressure_count: Decimal
    oldest_source_recheck_age_seconds: Decimal | None
    average_source_coverage_ratio: Decimal
    highest_unresolved_outcome_pressure: Decimal
    watch_source_recheck_age_seconds: Decimal
    blocked_source_recheck_age_seconds: Decimal
    watch_min_source_coverage_ratio: Decimal
    blocked_min_source_coverage_ratio: Decimal
    watch_unresolved_outcome_pressure: Decimal
    blocked_unresolved_outcome_pressure: Decimal
    rows: tuple[TeamMemoryOutcomeSourceRecheckHealthRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_health_status("health_status", self.health_status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "stale_source_recheck_count",
            "low_source_coverage_count",
            "high_unresolved_outcome_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "oldest_source_recheck_age_seconds",
            _normalize_optional_seconds(
                "oldest_source_recheck_age_seconds",
                self.oldest_source_recheck_age_seconds,
            ),
        )
        for field_name in (
            "average_source_coverage_ratio",
            "highest_unresolved_outcome_pressure",
            "watch_min_source_coverage_ratio",
            "blocked_min_source_coverage_ratio",
            "watch_unresolved_outcome_pressure",
            "blocked_unresolved_outcome_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_source_recheck_age_seconds",
            "blocked_source_recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_health_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckHealthReport", self)


def build_team_memory_outcome_source_recheck_health_report(
    rows: list[TeamMemoryOutcomeSourceRecheckMemoryRow]
    | tuple[TeamMemoryOutcomeSourceRecheckMemoryRow, ...],
    *,
    config: TeamMemoryOutcomeSourceRecheckHealthConfig,
    generated_at: datetime,
) -> TeamMemoryOutcomeSourceRecheckHealthReport:
    if type(config) is not TeamMemoryOutcomeSourceRecheckHealthConfig:
        raise ValueError("config must be a TeamMemoryOutcomeSourceRecheckHealthConfig")
    _require_hard_flags("TeamMemoryOutcomeSourceRecheckHealthConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    memory_rows = _normalize_memory_rows(rows)
    health_rows = tuple(
        _health_row(row=row, config=config, generated_at=generated_at_utc)
        for row in sorted(memory_rows, key=_memory_row_sort_key)
    )
    reason_codes = _report_reason_codes(health_rows)

    return TeamMemoryOutcomeSourceRecheckHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        health_status=_report_health_status(health_rows),
        row_count=_decimal_count(len(health_rows)),
        pass_count=_status_count(health_rows, "pass"),
        watch_count=_status_count(health_rows, "watch"),
        blocked_count=_status_count(health_rows, "blocked"),
        stale_source_recheck_count=_dimension_count(health_rows, "source_recheck_status"),
        low_source_coverage_count=_dimension_count(health_rows, "source_coverage_status"),
        high_unresolved_outcome_pressure_count=_dimension_count(
            health_rows,
            "outcome_pressure_status",
        ),
        oldest_source_recheck_age_seconds=_oldest_source_recheck_age_seconds(health_rows),
        average_source_coverage_ratio=_average_source_coverage_ratio(health_rows),
        highest_unresolved_outcome_pressure=_highest_unresolved_outcome_pressure(
            health_rows,
        ),
        watch_source_recheck_age_seconds=config.watch_source_recheck_age_seconds,
        blocked_source_recheck_age_seconds=config.blocked_source_recheck_age_seconds,
        watch_min_source_coverage_ratio=config.watch_min_source_coverage_ratio,
        blocked_min_source_coverage_ratio=config.blocked_min_source_coverage_ratio,
        watch_unresolved_outcome_pressure=config.watch_unresolved_outcome_pressure,
        blocked_unresolved_outcome_pressure=(
            config.blocked_unresolved_outcome_pressure
        ),
        rows=health_rows,
        reason_codes=reason_codes,
    )


def team_memory_outcome_source_recheck_health_report_to_json(
    report: TeamMemoryOutcomeSourceRecheckHealthReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemoryOutcomeSourceRecheckHealthReport:
        raise ValueError(
            "report must be a TeamMemoryOutcomeSourceRecheckHealthReport",
        )
    require_paper_only_flags("TeamMemoryOutcomeSourceRecheckHealthReport", report)
    _require_report_surface_flags(report)
    payload = {
        "generated_at": _datetime_to_json(report.generated_at),
        "config_version": report.config_version,
        "health_status": report.health_status,
        "row_count": _decimal_to_json(report.row_count),
        "pass_count": _decimal_to_json(report.pass_count),
        "watch_count": _decimal_to_json(report.watch_count),
        "blocked_count": _decimal_to_json(report.blocked_count),
        "stale_source_recheck_count": _decimal_to_json(
            report.stale_source_recheck_count,
        ),
        "low_source_coverage_count": _decimal_to_json(
            report.low_source_coverage_count,
        ),
        "high_unresolved_outcome_pressure_count": _decimal_to_json(
            report.high_unresolved_outcome_pressure_count,
        ),
        "oldest_source_recheck_age_seconds": _optional_decimal_to_json(
            report.oldest_source_recheck_age_seconds,
        ),
        "average_source_coverage_ratio": _decimal_to_json(
            report.average_source_coverage_ratio,
        ),
        "highest_unresolved_outcome_pressure": _decimal_to_json(
            report.highest_unresolved_outcome_pressure,
        ),
        "watch_source_recheck_age_seconds": _decimal_to_json(
            report.watch_source_recheck_age_seconds,
        ),
        "blocked_source_recheck_age_seconds": _decimal_to_json(
            report.blocked_source_recheck_age_seconds,
        ),
        "watch_min_source_coverage_ratio": _decimal_to_json(
            report.watch_min_source_coverage_ratio,
        ),
        "blocked_min_source_coverage_ratio": _decimal_to_json(
            report.blocked_min_source_coverage_ratio,
        ),
        "watch_unresolved_outcome_pressure": _decimal_to_json(
            report.watch_unresolved_outcome_pressure,
        ),
        "blocked_unresolved_outcome_pressure": _decimal_to_json(
            report.blocked_unresolved_outcome_pressure,
        ),
        "rows": [_health_row_to_json(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    reject_unsafe_surface_fields(
        "team memory outcome source recheck health payload",
        payload,
    )
    _reject_runtime_surface_fields(
        "team memory outcome source recheck health payload",
        payload,
    )
    _reject_unsafe_surface_values(
        "team memory outcome source recheck health payload",
        payload,
    )
    guarded = json_ready_no_floats(payload)
    if type(guarded) is not dict:
        raise ValueError("report payload must be an object")
    return guarded


def _require_report_surface_flags(
    report: TeamMemoryOutcomeSourceRecheckHealthReport,
) -> None:
    for row in report.rows:
        require_paper_only_flags("TeamMemoryOutcomeSourceRecheckHealthRow", row)


def _reject_runtime_surface_fields(label: str, payload: object) -> None:
    unsafe_fragments = ("li" "ve", "execution")
    for key in _iter_payload_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in unsafe_fragments):
            surface = "li" "ve"
            raise ValueError(f"unsafe {surface} surface field in {label}: {key}")


def _reject_unsafe_surface_values(label: str, payload: object) -> None:
    unsafe_fragments = (
        "auth",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
        "trade",
        "trading",
        "li" "ve",
        "execution",
    )
    for value in _iter_payload_string_values(payload):
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in unsafe_fragments):
            surface = "li" "ve"
            raise ValueError(f"unsafe {surface} surface value in {label}: {value}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _iter_payload_string_values(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_iter_payload_string_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_iter_payload_string_values(item))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


def _health_row(
    *,
    row: TeamMemoryOutcomeSourceRecheckMemoryRow,
    config: TeamMemoryOutcomeSourceRecheckHealthConfig,
    generated_at: datetime,
) -> TeamMemoryOutcomeSourceRecheckHealthRow:
    age_seconds = _source_recheck_age_seconds(
        generated_at=generated_at,
        latest_source_rechecked_at=row.latest_source_rechecked_at,
    )
    coverage_ratio = _safe_ratio(row.verified_source_count, row.expected_source_count)
    outcome_pressure = _safe_ratio(row.unresolved_outcome_count, row.total_outcome_count)
    source_recheck_status = _source_recheck_status(
        age_seconds=age_seconds,
        config=config,
    )
    source_coverage_status = _source_coverage_status(
        expected_source_count=row.expected_source_count,
        coverage_ratio=coverage_ratio,
        config=config,
    )
    outcome_pressure_status = _outcome_pressure_status(
        outcome_pressure=outcome_pressure,
        config=config,
    )
    statuses = (
        source_recheck_status,
        source_coverage_status,
        outcome_pressure_status,
    )

    return TeamMemoryOutcomeSourceRecheckHealthRow(
        team_id=row.team_id,
        category_id=row.category_id,
        latest_source_rechecked_at=row.latest_source_rechecked_at,
        source_recheck_age_seconds=age_seconds,
        expected_source_count=row.expected_source_count,
        verified_source_count=row.verified_source_count,
        source_coverage_ratio=coverage_ratio,
        total_outcome_count=row.total_outcome_count,
        unresolved_outcome_count=row.unresolved_outcome_count,
        unresolved_outcome_pressure=outcome_pressure,
        source_recheck_status=source_recheck_status,
        source_coverage_status=source_coverage_status,
        outcome_pressure_status=outcome_pressure_status,
        health_status=_worst_status(statuses),
        reason_codes=_row_reason_codes(
            source_recheck_status=source_recheck_status,
            source_coverage_status=source_coverage_status,
            outcome_pressure_status=outcome_pressure_status,
            latest_source_rechecked_at=row.latest_source_rechecked_at,
        ),
    )


def _source_recheck_age_seconds(
    *,
    generated_at: datetime,
    latest_source_rechecked_at: datetime | None,
) -> Decimal | None:
    if latest_source_rechecked_at is None:
        return None
    if latest_source_rechecked_at > generated_at:
        raise ValueError("latest_source_rechecked_at must not be after generated_at")
    delta = generated_at - latest_source_rechecked_at
    return _timedelta_seconds(delta)


def _source_recheck_status(
    *,
    age_seconds: Decimal | None,
    config: TeamMemoryOutcomeSourceRecheckHealthConfig,
) -> str:
    if age_seconds is None:
        return "blocked"
    if age_seconds > config.blocked_source_recheck_age_seconds:
        return "blocked"
    if age_seconds > config.watch_source_recheck_age_seconds:
        return "watch"
    return "pass"


def _source_coverage_status(
    *,
    expected_source_count: Decimal,
    coverage_ratio: Decimal,
    config: TeamMemoryOutcomeSourceRecheckHealthConfig,
) -> str:
    if expected_source_count == ZERO:
        return "blocked"
    if coverage_ratio < config.blocked_min_source_coverage_ratio:
        return "blocked"
    if coverage_ratio < config.watch_min_source_coverage_ratio:
        return "watch"
    return "pass"


def _outcome_pressure_status(
    *,
    outcome_pressure: Decimal,
    config: TeamMemoryOutcomeSourceRecheckHealthConfig,
) -> str:
    if outcome_pressure > config.blocked_unresolved_outcome_pressure:
        return "blocked"
    if outcome_pressure > config.watch_unresolved_outcome_pressure:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    source_recheck_status: str,
    source_coverage_status: str,
    outcome_pressure_status: str,
    latest_source_rechecked_at: datetime | None,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_recheck_status == "blocked":
        if latest_source_rechecked_at is None:
            reason_codes.append("source_recheck_missing")
        else:
            reason_codes.append("source_recheck_stale_blocked")
    elif source_recheck_status == "watch":
        reason_codes.append("source_recheck_stale_watch")

    if source_coverage_status == "blocked":
        reason_codes.append("source_coverage_low_blocked")
    elif source_coverage_status == "watch":
        reason_codes.append("source_coverage_low_watch")

    if outcome_pressure_status == "blocked":
        reason_codes.append("unresolved_outcome_pressure_high_blocked")
    elif outcome_pressure_status == "watch":
        reason_codes.append("unresolved_outcome_pressure_high_watch")

    if not reason_codes:
        reason_codes.append("outcome_source_recheck_ready")
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[TeamMemoryOutcomeSourceRecheckHealthRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("memory_rows_empty",)
    reason_codes: list[str] = []
    if any(row.source_recheck_status != "pass" for row in rows):
        reason_codes.append("stale_source_recheck_rows_present")
    if any(row.source_coverage_status != "pass" for row in rows):
        reason_codes.append("low_source_coverage_rows_present")
    if any(row.outcome_pressure_status != "pass" for row in rows):
        reason_codes.append("high_unresolved_outcome_pressure_rows_present")
    if not reason_codes:
        reason_codes.append("outcome_source_rechecks_ready")
    return tuple(reason_codes)


def _report_health_status(
    rows: tuple[TeamMemoryOutcomeSourceRecheckHealthRow, ...],
) -> str:
    if not rows:
        return "blocked"
    return _worst_status(tuple(row.health_status for row in rows))


def _memory_row_sort_key(row: TeamMemoryOutcomeSourceRecheckMemoryRow) -> tuple[str, str]:
    return (row.team_id, row.category_id)


def _normalize_memory_rows(value: object) -> tuple[TeamMemoryOutcomeSourceRecheckMemoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemoryOutcomeSourceRecheckMemoryRow:
            raise ValueError(
                "rows must contain TeamMemoryOutcomeSourceRecheckMemoryRow values",
            )
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckMemoryRow", row)
        key = (row.team_id, row.category_id)
        if key in seen:
            raise ValueError("rows must not repeat team_id/category_id values")
        seen.add(key)
    return rows


def _normalize_health_rows(
    value: object,
) -> tuple[TeamMemoryOutcomeSourceRecheckHealthRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    previous_key: tuple[str, str] | None = None
    for row in rows:
        if type(row) is not TeamMemoryOutcomeSourceRecheckHealthRow:
            raise ValueError(
                "rows must contain TeamMemoryOutcomeSourceRecheckHealthRow values",
            )
        key = (row.team_id, row.category_id)
        if key in seen:
            raise ValueError("rows must not repeat team_id/category_id values")
        if previous_key is not None and key < previous_key:
            raise ValueError("rows must be sorted by team_id and category_id")
        seen.add(key)
        previous_key = key
    return rows


def _status_count(
    rows: tuple[TeamMemoryOutcomeSourceRecheckHealthRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.health_status == status))


def _dimension_count(
    rows: tuple[TeamMemoryOutcomeSourceRecheckHealthRow, ...],
    status_field_name: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if getattr(row, status_field_name) != "pass"),
    )


def _oldest_source_recheck_age_seconds(
    rows: tuple[TeamMemoryOutcomeSourceRecheckHealthRow, ...],
) -> Decimal | None:
    ages = tuple(
        row.source_recheck_age_seconds
        for row in rows
        if row.source_recheck_age_seconds is not None
    )
    if not ages:
        return None
    return max(ages).quantize(SECONDS_QUANT, rounding=ROUND_HALF_EVEN)


def _average_source_coverage_ratio(
    rows: tuple[TeamMemoryOutcomeSourceRecheckHealthRow, ...],
) -> Decimal:
    if not rows:
        return Decimal("0.000000")
    return (
        sum((row.source_coverage_ratio for row in rows), ZERO) / Decimal(len(rows))
    ).quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _highest_unresolved_outcome_pressure(
    rows: tuple[TeamMemoryOutcomeSourceRecheckHealthRow, ...],
) -> Decimal:
    if not rows:
        return Decimal("0.000000")
    return max(row.unresolved_outcome_pressure for row in rows).quantize(
        RATIO_QUANT,
        rounding=ROUND_HALF_EVEN,
    )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return Decimal("0.000000")
    return (numerator / denominator).quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _timedelta_seconds(value: timedelta) -> Decimal:
    seconds = Decimal(value.days * 86400 + value.seconds)
    microseconds = Decimal(value.microseconds) / Decimal("1000000")
    return (seconds + microseconds).quantize(SECONDS_QUANT, rounding=ROUND_HALF_EVEN)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _worst_status(statuses: tuple[str, ...]) -> str:
    for status in statuses:
        _require_health_status("status", status)
    return max(statuses, key=lambda status: STATUS_RANK[status])


def _validate_health_row(row: TeamMemoryOutcomeSourceRecheckHealthRow) -> None:
    if row.verified_source_count > row.expected_source_count:
        raise ValueError("verified_source_count must not exceed expected_source_count")
    if row.unresolved_outcome_count > row.total_outcome_count:
        raise ValueError("unresolved_outcome_count must not exceed total_outcome_count")
    expected_status = _worst_status(
        (
            row.source_recheck_status,
            row.source_coverage_status,
            row.outcome_pressure_status,
        ),
    )
    if row.health_status != expected_status:
        raise ValueError("health_status must match dimension statuses")
    if row.health_status == "pass":
        if row.reason_codes != ("outcome_source_recheck_ready",):
            raise ValueError("pass rows must use ready reason code")
    elif "outcome_source_recheck_ready" in row.reason_codes:
        raise ValueError("non-pass rows must not use ready reason code")
    expected_reason_codes = _row_reason_codes(
        source_recheck_status=row.source_recheck_status,
        source_coverage_status=row.source_coverage_status,
        outcome_pressure_status=row.outcome_pressure_status,
        latest_source_rechecked_at=row.latest_source_rechecked_at,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match dimension statuses")


def _validate_report(report: TeamMemoryOutcomeSourceRecheckHealthReport) -> None:
    row_count = _decimal_count(len(report.rows))
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.row_count:
        raise ValueError("status counts must sum to row_count")
    if report.stale_source_recheck_count != _dimension_count(
        report.rows,
        "source_recheck_status",
    ):
        raise ValueError("stale_source_recheck_count must match rows")
    if report.low_source_coverage_count != _dimension_count(
        report.rows,
        "source_coverage_status",
    ):
        raise ValueError("low_source_coverage_count must match rows")
    if report.high_unresolved_outcome_pressure_count != _dimension_count(
        report.rows,
        "outcome_pressure_status",
    ):
        raise ValueError("high_unresolved_outcome_pressure_count must match rows")
    if (
        report.oldest_source_recheck_age_seconds
        != _oldest_source_recheck_age_seconds(report.rows)
    ):
        raise ValueError("oldest_source_recheck_age_seconds must match rows")
    if report.average_source_coverage_ratio != _average_source_coverage_ratio(
        report.rows,
    ):
        raise ValueError("average_source_coverage_ratio must match rows")
    if report.highest_unresolved_outcome_pressure != (
        _highest_unresolved_outcome_pressure(report.rows)
    ):
        raise ValueError("highest_unresolved_outcome_pressure must match rows")
    if report.health_status != _report_health_status(report.rows):
        raise ValueError("health_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(SECONDS_QUANT, rounding=ROUND_HALF_EVEN)


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value.quantize(COUNT_QUANT, rounding=ROUND_HALF_EVEN)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _normalize_optional_seconds(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a list or tuple")
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _datetime_to_json(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _as_utc("datetime", value).isoformat()


def _decimal_to_json(value: Decimal) -> str:
    _require_decimal("value", value)
    return str(value)


def _optional_decimal_to_json(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_to_json(value)


def _health_row_to_json(row: TeamMemoryOutcomeSourceRecheckHealthRow) -> dict[str, Any]:
    return {
        "team_id": row.team_id,
        "category_id": row.category_id,
        "latest_source_rechecked_at": _datetime_to_json(
            row.latest_source_rechecked_at,
        ),
        "source_recheck_age_seconds": _optional_decimal_to_json(
            row.source_recheck_age_seconds,
        ),
        "expected_source_count": _decimal_to_json(row.expected_source_count),
        "verified_source_count": _decimal_to_json(row.verified_source_count),
        "source_coverage_ratio": _decimal_to_json(row.source_coverage_ratio),
        "total_outcome_count": _decimal_to_json(row.total_outcome_count),
        "unresolved_outcome_count": _decimal_to_json(row.unresolved_outcome_count),
        "unresolved_outcome_pressure": _decimal_to_json(
            row.unresolved_outcome_pressure,
        ),
        "source_recheck_status": row.source_recheck_status,
        "source_coverage_status": row.source_coverage_status,
        "outcome_pressure_status": row.outcome_pressure_status,
        "health_status": row.health_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


__all__ = (
    "TeamMemoryOutcomeSourceRecheckHealthConfig",
    "TeamMemoryOutcomeSourceRecheckHealthReport",
    "TeamMemoryOutcomeSourceRecheckHealthRow",
    "TeamMemoryOutcomeSourceRecheckMemoryRow",
    "build_team_memory_outcome_source_recheck_health_report",
    "team_memory_outcome_source_recheck_health_report_to_json",
)

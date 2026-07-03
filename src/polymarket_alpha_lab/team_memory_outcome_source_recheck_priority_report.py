"""Pure in-memory priority report for team-memory outcome source rechecks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_TEAM_MEMORY_OUTCOME_SOURCE_RECHECK_PRIORITY_CONFIG_VERSION = (
    "team-memory-outcome-source-recheck-priority-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

SOURCE_RECHECK_MISSING_REASON = "source_recheck_missing"
SOURCE_RECHECK_STALE_BLOCKED_REASON = "source_recheck_stale_blocked"
SOURCE_RECHECK_STALE_WATCH_REASON = "source_recheck_stale_watch"
SOURCE_COVERAGE_LOW_BLOCKED_REASON = "source_coverage_low_blocked"
SOURCE_COVERAGE_LOW_WATCH_REASON = "source_coverage_low_watch"
OUTCOME_PRESSURE_HIGH_BLOCKED_REASON = "unresolved_outcome_pressure_high_blocked"
OUTCOME_PRESSURE_HIGH_WATCH_REASON = "unresolved_outcome_pressure_high_watch"
ROW_REASON_CODES = (
    SOURCE_RECHECK_MISSING_REASON,
    SOURCE_RECHECK_STALE_BLOCKED_REASON,
    SOURCE_RECHECK_STALE_WATCH_REASON,
    SOURCE_COVERAGE_LOW_BLOCKED_REASON,
    SOURCE_COVERAGE_LOW_WATCH_REASON,
    OUTCOME_PRESSURE_HIGH_BLOCKED_REASON,
    OUTCOME_PRESSURE_HIGH_WATCH_REASON,
)
BLOCKING_ROW_REASON_CODES = (
    SOURCE_RECHECK_MISSING_REASON,
    SOURCE_RECHECK_STALE_BLOCKED_REASON,
    SOURCE_COVERAGE_LOW_BLOCKED_REASON,
    OUTCOME_PRESSURE_HIGH_BLOCKED_REASON,
)

CLEAR_REPORT_REASON = "team_memory_outcome_source_recheck_priority_clear"
WATCH_REPORT_REASON = "team_memory_outcome_source_recheck_priority_watch"
BLOCKED_REPORT_REASON = "team_memory_outcome_source_recheck_priority_blocked"
REPORT_REASON_BY_ROW_REASON = {
    SOURCE_RECHECK_MISSING_REASON: "source_recheck_missing_present",
    SOURCE_RECHECK_STALE_BLOCKED_REASON: "source_recheck_stale_blocked_present",
    SOURCE_RECHECK_STALE_WATCH_REASON: "source_recheck_stale_watch_present",
    SOURCE_COVERAGE_LOW_BLOCKED_REASON: "source_coverage_low_blocked_present",
    SOURCE_COVERAGE_LOW_WATCH_REASON: "source_coverage_low_watch_present",
    OUTCOME_PRESSURE_HIGH_BLOCKED_REASON: (
        "unresolved_outcome_pressure_high_blocked_present"
    ),
    OUTCOME_PRESSURE_HIGH_WATCH_REASON: (
        "unresolved_outcome_pressure_high_watch_present"
    ),
}
REPORT_REASON_CODES = (
    CLEAR_REPORT_REASON,
    WATCH_REPORT_REASON,
    BLOCKED_REPORT_REASON,
    *tuple(REPORT_REASON_BY_ROW_REASON[reason_code] for reason_code in ROW_REASON_CODES),
)

NUMERIC_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
UTC_OFFSET = timedelta(0)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckPriorityConfig:
    config_version: str = (
        DEFAULT_TEAM_MEMORY_OUTCOME_SOURCE_RECHECK_PRIORITY_CONFIG_VERSION
    )
    stale_source_recheck_watch_seconds: Decimal = Decimal("86400.000000")
    stale_source_recheck_blocked_seconds: Decimal = Decimal("259200.000000")
    source_coverage_watch_below_ratio: Decimal = Decimal("0.750000")
    source_coverage_blocked_below_ratio: Decimal = Decimal("0.500000")
    unresolved_outcome_pressure_watch_ratio: Decimal = Decimal("0.400000")
    unresolved_outcome_pressure_blocked_ratio: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "stale_source_recheck_watch_seconds",
            "stale_source_recheck_blocked_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_coverage_watch_below_ratio",
            "source_coverage_blocked_below_ratio",
            "unresolved_outcome_pressure_watch_ratio",
            "unresolved_outcome_pressure_blocked_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckPriorityConfig", self)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckPriorityInput:
    team_id: str
    category_id: str
    outcome_id: str
    latest_source_rechecked_at: datetime | None
    expected_source_count: Decimal
    verified_source_count: Decimal
    total_outcome_count: Decimal
    unresolved_outcome_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "category_id", "outcome_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
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
        _validate_input(self)
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckPriorityInput", self)


TeamMemoryOutcomeSourceRecheckPriorityInputRow = (
    TeamMemoryOutcomeSourceRecheckPriorityInput
)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckPriorityRow:
    priority_rank: Decimal
    team_id: str
    category_id: str
    outcome_id: str
    latest_source_rechecked_at: datetime | None
    source_recheck_age_seconds: Decimal | None
    expected_source_count: Decimal
    verified_source_count: Decimal
    source_coverage_ratio: Decimal
    source_coverage_shortfall_ratio: Decimal
    total_outcome_count: Decimal
    unresolved_outcome_count: Decimal
    unresolved_outcome_pressure: Decimal
    priority_reason_count: Decimal
    priority_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_decimal("priority_rank", self.priority_rank),
        )
        for field_name in ("team_id", "category_id", "outcome_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
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
            "priority_reason_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "source_coverage_ratio",
            "source_coverage_shortfall_ratio",
            "unresolved_outcome_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("priority_status", self.priority_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_priority_row(self)
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckPriorityRow", self)


@dataclass(frozen=True)
class TeamMemoryOutcomeSourceRecheckPriorityReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    prioritized_row_count: Decimal
    blocked_row_count: Decimal
    watch_row_count: Decimal
    pass_row_count: Decimal
    stale_source_recheck_row_count: Decimal
    missing_source_recheck_row_count: Decimal
    low_source_coverage_row_count: Decimal
    high_unresolved_outcome_pressure_row_count: Decimal
    max_source_recheck_age_seconds: Decimal
    min_source_coverage_ratio: Decimal
    max_unresolved_outcome_pressure: Decimal
    priority_ratio: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    priority_rows: tuple[TeamMemoryOutcomeSourceRecheckPriorityRow, ...]
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
        for field_name in (
            "input_row_count",
            "prioritized_row_count",
            "blocked_row_count",
            "watch_row_count",
            "pass_row_count",
            "stale_source_recheck_row_count",
            "missing_source_recheck_row_count",
            "low_source_coverage_row_count",
            "high_unresolved_outcome_pressure_row_count",
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
            "max_source_recheck_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_recheck_age_seconds",
                self.max_source_recheck_age_seconds,
            ),
        )
        for field_name in (
            "min_source_coverage_ratio",
            "max_unresolved_outcome_pressure",
            "priority_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "priority_rows",
            _normalize_priority_rows(self.priority_rows),
        )
        _validate_report(self)
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckPriorityReport", self)


def build_team_memory_outcome_source_recheck_priority_report(
    rows: list[TeamMemoryOutcomeSourceRecheckPriorityInput]
    | tuple[TeamMemoryOutcomeSourceRecheckPriorityInput, ...],
    *,
    config: TeamMemoryOutcomeSourceRecheckPriorityConfig,
    generated_at: datetime,
) -> TeamMemoryOutcomeSourceRecheckPriorityReport:
    if type(config) is not TeamMemoryOutcomeSourceRecheckPriorityConfig:
        raise ValueError(
            "config must be a TeamMemoryOutcomeSourceRecheckPriorityConfig",
        )
    _require_hard_flags("TeamMemoryOutcomeSourceRecheckPriorityConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows, generated_at_utc)
    drafts = tuple(
        draft
        for draft in (
            _priority_draft(row, config=config, generated_at=generated_at_utc)
            for row in input_rows
        )
        if draft[10]
    )
    priority_rows = tuple(
        _priority_row(rank, draft)
        for rank, draft in enumerate(sorted(drafts, key=_draft_sort_key), start=1)
    )
    input_row_count = _count_from_int(len(input_rows))
    prioritized_row_count = _count_from_int(len(priority_rows))

    return TeamMemoryOutcomeSourceRecheckPriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=input_row_count,
        prioritized_row_count=prioritized_row_count,
        blocked_row_count=_status_count(priority_rows, BLOCKED_STATUS),
        watch_row_count=_status_count(priority_rows, WATCH_STATUS),
        pass_row_count=input_row_count - prioritized_row_count,
        stale_source_recheck_row_count=_row_reason_family_count(
            priority_rows,
            (
                SOURCE_RECHECK_MISSING_REASON,
                SOURCE_RECHECK_STALE_BLOCKED_REASON,
                SOURCE_RECHECK_STALE_WATCH_REASON,
            ),
        ),
        missing_source_recheck_row_count=_row_reason_family_count(
            priority_rows,
            (SOURCE_RECHECK_MISSING_REASON,),
        ),
        low_source_coverage_row_count=_row_reason_family_count(
            priority_rows,
            (SOURCE_COVERAGE_LOW_BLOCKED_REASON, SOURCE_COVERAGE_LOW_WATCH_REASON),
        ),
        high_unresolved_outcome_pressure_row_count=_row_reason_family_count(
            priority_rows,
            (
                OUTCOME_PRESSURE_HIGH_BLOCKED_REASON,
                OUTCOME_PRESSURE_HIGH_WATCH_REASON,
            ),
        ),
        max_source_recheck_age_seconds=_max_optional_seconds(
            tuple(row.source_recheck_age_seconds for row in priority_rows),
        ),
        min_source_coverage_ratio=_min_ratio(
            tuple(row.source_coverage_ratio for row in priority_rows),
        ),
        max_unresolved_outcome_pressure=_max_ratio(
            tuple(row.unresolved_outcome_pressure for row in priority_rows),
        ),
        priority_ratio=_ratio(prioritized_row_count, input_row_count),
        report_status=_report_status(priority_rows),
        reason_codes=_report_reason_codes(priority_rows),
        priority_rows=priority_rows,
    )


def team_memory_outcome_source_recheck_priority_report_to_jsonable(
    report: TeamMemoryOutcomeSourceRecheckPriorityReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemoryOutcomeSourceRecheckPriorityReport:
        raise ValueError(
            "report must be a TeamMemoryOutcomeSourceRecheckPriorityReport",
        )
    require_paper_only_flags("TeamMemoryOutcomeSourceRecheckPriorityReport", report)
    _require_report_surface_flags(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    reject_unsafe_surface_fields(
        "team memory outcome source recheck priority payload",
        payload,
    )
    _reject_unsafe_surface_values(
        "team memory outcome source recheck priority payload",
        payload,
    )
    _reject_runtime_surface_fields(
        "team memory outcome source recheck priority payload",
        payload,
    )
    guarded = json_ready_no_floats(payload)
    if type(guarded) is not dict:
        raise ValueError("report payload must be an object")
    return guarded


def _require_report_surface_flags(
    report: TeamMemoryOutcomeSourceRecheckPriorityReport,
) -> None:
    for row in report.priority_rows:
        require_paper_only_flags("TeamMemoryOutcomeSourceRecheckPriorityRow", row)


def _reject_runtime_surface_fields(label: str, payload: object) -> None:
    unsafe_fragments = ("li" "ve", "execution")
    for key in _iter_payload_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in unsafe_fragments):
            surface = "li" "ve"
            raise ValueError(f"unsafe {surface} surface field in {label}: {key}")


def _reject_unsafe_surface_values(label: str, payload: object) -> None:
    unsafe_fragments = (*UNSAFE_SURFACE_FIELD_FRAGMENTS, "li" "ve", "execution")
    for value in _iter_payload_string_values(payload):
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in unsafe_fragments):
            surface = "li" "ve"
            raise ValueError(f"unsafe {surface} surface value in {label}")


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
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
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


def team_memory_outcome_source_recheck_priority_report_to_json(
    report: TeamMemoryOutcomeSourceRecheckPriorityReport,
) -> dict[str, Any]:
    return team_memory_outcome_source_recheck_priority_report_to_jsonable(report)


def _priority_draft(
    row: TeamMemoryOutcomeSourceRecheckPriorityInput,
    *,
    config: TeamMemoryOutcomeSourceRecheckPriorityConfig,
    generated_at: datetime,
) -> tuple[
    TeamMemoryOutcomeSourceRecheckPriorityInput,
    Decimal | None,
    Decimal,
    Decimal,
    Decimal,
    tuple[str, ...],
    str,
    str,
    str,
    str,
    bool,
]:
    source_age_seconds = _source_recheck_age_seconds(
        generated_at=generated_at,
        latest_source_rechecked_at=row.latest_source_rechecked_at,
    )
    source_coverage_ratio = _safe_ratio(row.verified_source_count, row.expected_source_count)
    source_coverage_shortfall_ratio = _normalize_ratio(
        "source_coverage_shortfall_ratio",
        ONE - source_coverage_ratio,
    )
    outcome_pressure = _safe_ratio(row.unresolved_outcome_count, row.total_outcome_count)
    reason_codes = _row_reason_codes(
        source_age_seconds=source_age_seconds,
        source_coverage_ratio=source_coverage_ratio,
        unresolved_outcome_pressure=outcome_pressure,
        config=config,
    )
    return (
        row,
        source_age_seconds,
        source_coverage_ratio,
        source_coverage_shortfall_ratio,
        outcome_pressure,
        reason_codes,
        _priority_status(reason_codes),
        row.team_id,
        row.category_id,
        row.outcome_id,
        bool(reason_codes),
    )


def _priority_row(
    rank: int,
    draft: tuple[
        TeamMemoryOutcomeSourceRecheckPriorityInput,
        Decimal | None,
        Decimal,
        Decimal,
        Decimal,
        tuple[str, ...],
        str,
        str,
        str,
        str,
        bool,
    ],
) -> TeamMemoryOutcomeSourceRecheckPriorityRow:
    (
        row,
        source_age_seconds,
        source_coverage_ratio,
        source_coverage_shortfall_ratio,
        outcome_pressure,
        reason_codes,
        priority_status,
        _team_id,
        _category_id,
        _outcome_id,
        _is_prioritized,
    ) = draft
    return TeamMemoryOutcomeSourceRecheckPriorityRow(
        priority_rank=_count_from_int(rank),
        team_id=row.team_id,
        category_id=row.category_id,
        outcome_id=row.outcome_id,
        latest_source_rechecked_at=row.latest_source_rechecked_at,
        source_recheck_age_seconds=source_age_seconds,
        expected_source_count=row.expected_source_count,
        verified_source_count=row.verified_source_count,
        source_coverage_ratio=source_coverage_ratio,
        source_coverage_shortfall_ratio=source_coverage_shortfall_ratio,
        total_outcome_count=row.total_outcome_count,
        unresolved_outcome_count=row.unresolved_outcome_count,
        unresolved_outcome_pressure=outcome_pressure,
        priority_reason_count=_count_from_int(len(reason_codes)),
        priority_status=priority_status,
        reason_codes=reason_codes,
    )


def _draft_sort_key(
    draft: tuple[
        TeamMemoryOutcomeSourceRecheckPriorityInput,
        Decimal | None,
        Decimal,
        Decimal,
        Decimal,
        tuple[str, ...],
        str,
        str,
        str,
        str,
        bool,
    ],
) -> tuple[int, Decimal, Decimal, Decimal, str, str, str]:
    (
        _row,
        source_age_seconds,
        source_coverage_ratio,
        _source_coverage_shortfall_ratio,
        outcome_pressure,
        _reason_codes,
        _priority_status,
        team_id,
        category_id,
        outcome_id,
        _is_prioritized,
    ) = draft
    return (
        0 if source_age_seconds is None else 1,
        ZERO if source_age_seconds is None else -source_age_seconds,
        source_coverage_ratio,
        -outcome_pressure,
        team_id,
        category_id,
        outcome_id,
    )


def _priority_row_sort_key(
    row: TeamMemoryOutcomeSourceRecheckPriorityRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str, str]:
    return (
        0 if row.source_recheck_age_seconds is None else 1,
        ZERO if row.source_recheck_age_seconds is None else -row.source_recheck_age_seconds,
        row.source_coverage_ratio,
        -row.unresolved_outcome_pressure,
        row.team_id,
        row.category_id,
        row.outcome_id,
    )


def _row_reason_codes(
    *,
    source_age_seconds: Decimal | None,
    source_coverage_ratio: Decimal,
    unresolved_outcome_pressure: Decimal,
    config: TeamMemoryOutcomeSourceRecheckPriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_age_seconds is None:
        reason_codes.append(SOURCE_RECHECK_MISSING_REASON)
    elif source_age_seconds >= config.stale_source_recheck_blocked_seconds:
        reason_codes.append(SOURCE_RECHECK_STALE_BLOCKED_REASON)
    elif source_age_seconds >= config.stale_source_recheck_watch_seconds:
        reason_codes.append(SOURCE_RECHECK_STALE_WATCH_REASON)

    if source_coverage_ratio < config.source_coverage_blocked_below_ratio:
        reason_codes.append(SOURCE_COVERAGE_LOW_BLOCKED_REASON)
    elif source_coverage_ratio < config.source_coverage_watch_below_ratio:
        reason_codes.append(SOURCE_COVERAGE_LOW_WATCH_REASON)

    if unresolved_outcome_pressure >= config.unresolved_outcome_pressure_blocked_ratio:
        reason_codes.append(OUTCOME_PRESSURE_HIGH_BLOCKED_REASON)
    elif unresolved_outcome_pressure >= config.unresolved_outcome_pressure_watch_ratio:
        reason_codes.append(OUTCOME_PRESSURE_HIGH_WATCH_REASON)

    return tuple(reason_codes)


def _priority_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_ROW_REASON_CODES for reason_code in reason_codes):
        return BLOCKED_STATUS
    if reason_codes:
        return WATCH_STATUS
    return PASS_STATUS


def _report_status(
    rows: tuple[TeamMemoryOutcomeSourceRecheckPriorityRow, ...],
) -> str:
    if any(row.priority_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if rows:
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[TeamMemoryOutcomeSourceRecheckPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (CLEAR_REPORT_REASON,)
    reason_codes: list[str] = [
        BLOCKED_REPORT_REASON
        if _report_status(rows) == BLOCKED_STATUS
        else WATCH_REPORT_REASON,
    ]
    row_reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    for reason_code in ROW_REASON_CODES:
        if reason_code in row_reason_codes:
            reason_codes.append(REPORT_REASON_BY_ROW_REASON[reason_code])
    return tuple(reason_codes)


def _normalize_inputs(
    value: object,
    generated_at: datetime,
) -> tuple[TeamMemoryOutcomeSourceRecheckPriorityInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemoryOutcomeSourceRecheckPriorityInput:
            raise ValueError(
                "rows must contain TeamMemoryOutcomeSourceRecheckPriorityInput values",
            )
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckPriorityInput", row)
        if row.latest_source_rechecked_at is not None and (
            row.latest_source_rechecked_at > generated_at
        ):
            raise ValueError("latest_source_rechecked_at must not be after generated_at")
        key = _input_key(row)
        if key in seen_keys:
            raise ValueError("rows must have unique team_id/category_id/outcome_id values")
        seen_keys.add(key)
    return rows


def _normalize_priority_rows(
    value: object,
) -> tuple[TeamMemoryOutcomeSourceRecheckPriorityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("priority_rows must be a tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for index, row in enumerate(rows, start=1):
        if type(row) is not TeamMemoryOutcomeSourceRecheckPriorityRow:
            raise ValueError(
                "priority_rows must contain TeamMemoryOutcomeSourceRecheckPriorityRow values",
            )
        _require_hard_flags("TeamMemoryOutcomeSourceRecheckPriorityRow", row)
        if row.priority_rank != _count_from_int(index):
            raise ValueError("priority_rank must match row sequence")
        key = (row.team_id, row.category_id, row.outcome_id)
        if key in seen_keys:
            raise ValueError("priority_rows must have unique team/category/outcome values")
        seen_keys.add(key)
    return rows


def _validate_config(config: TeamMemoryOutcomeSourceRecheckPriorityConfig) -> None:
    if config.stale_source_recheck_blocked_seconds < (
        config.stale_source_recheck_watch_seconds
    ):
        raise ValueError(
            "stale_source_recheck_blocked_seconds must be at least watch seconds",
        )
    if config.source_coverage_blocked_below_ratio > (
        config.source_coverage_watch_below_ratio
    ):
        raise ValueError(
            "source_coverage_blocked_below_ratio must not exceed watch ratio",
        )
    if config.unresolved_outcome_pressure_blocked_ratio < (
        config.unresolved_outcome_pressure_watch_ratio
    ):
        raise ValueError(
            "unresolved_outcome_pressure_blocked_ratio must be at least watch ratio",
        )


def _validate_input(row: TeamMemoryOutcomeSourceRecheckPriorityInput) -> None:
    if row.verified_source_count > row.expected_source_count:
        raise ValueError("verified_source_count must not exceed expected_source_count")
    if row.unresolved_outcome_count > row.total_outcome_count:
        raise ValueError("unresolved_outcome_count must not exceed total_outcome_count")


def _validate_priority_row(row: TeamMemoryOutcomeSourceRecheckPriorityRow) -> None:
    _validate_input(
        TeamMemoryOutcomeSourceRecheckPriorityInput(
            team_id=row.team_id,
            category_id=row.category_id,
            outcome_id=row.outcome_id,
            latest_source_rechecked_at=row.latest_source_rechecked_at,
            expected_source_count=row.expected_source_count,
            verified_source_count=row.verified_source_count,
            total_outcome_count=row.total_outcome_count,
            unresolved_outcome_count=row.unresolved_outcome_count,
        ),
    )
    if row.source_coverage_ratio != _safe_ratio(
        row.verified_source_count,
        row.expected_source_count,
    ):
        raise ValueError("source_coverage_ratio must match source counts")
    if row.source_coverage_shortfall_ratio != _normalize_ratio(
        "source_coverage_shortfall_ratio",
        ONE - row.source_coverage_ratio,
    ):
        raise ValueError("source_coverage_shortfall_ratio must match coverage")
    if row.unresolved_outcome_pressure != _safe_ratio(
        row.unresolved_outcome_count,
        row.total_outcome_count,
    ):
        raise ValueError("unresolved_outcome_pressure must match outcome counts")
    if row.priority_reason_count != _count_from_int(len(row.reason_codes)):
        raise ValueError("priority_reason_count must match reason_codes")
    if row.priority_status != _priority_status(row.reason_codes):
        raise ValueError("priority_status must match reason_codes")
    if row.priority_status == PASS_STATUS:
        raise ValueError("priority rows must not use pass status")
    canonical_reason_codes = _canonical_row_reason_code_sequence(row.reason_codes)
    if row.reason_codes != canonical_reason_codes:
        raise ValueError("reason_codes must use canonical reason code sequence")
    if row.reason_codes != _row_reason_codes_from_metrics(row):
        raise ValueError("reason_codes must match row metrics")


def _validate_report(report: TeamMemoryOutcomeSourceRecheckPriorityReport) -> None:
    if report.prioritized_row_count != _count_from_int(len(report.priority_rows)):
        raise ValueError("prioritized_row_count must match priority_rows")
    if report.prioritized_row_count > report.input_row_count:
        raise ValueError("prioritized_row_count must not exceed input_row_count")
    if report.blocked_row_count != _status_count(report.priority_rows, BLOCKED_STATUS):
        raise ValueError("blocked_row_count must match priority_rows")
    if report.watch_row_count != _status_count(report.priority_rows, WATCH_STATUS):
        raise ValueError("watch_row_count must match priority_rows")
    if report.pass_row_count != report.input_row_count - report.prioritized_row_count:
        raise ValueError("pass_row_count must match row counts")
    if report.stale_source_recheck_row_count != _row_reason_family_count(
        report.priority_rows,
        (
            SOURCE_RECHECK_MISSING_REASON,
            SOURCE_RECHECK_STALE_BLOCKED_REASON,
            SOURCE_RECHECK_STALE_WATCH_REASON,
        ),
    ):
        raise ValueError("stale_source_recheck_row_count must match priority_rows")
    if report.missing_source_recheck_row_count != _row_reason_family_count(
        report.priority_rows,
        (SOURCE_RECHECK_MISSING_REASON,),
    ):
        raise ValueError("missing_source_recheck_row_count must match priority_rows")
    if report.low_source_coverage_row_count != _row_reason_family_count(
        report.priority_rows,
        (SOURCE_COVERAGE_LOW_BLOCKED_REASON, SOURCE_COVERAGE_LOW_WATCH_REASON),
    ):
        raise ValueError("low_source_coverage_row_count must match priority_rows")
    if report.high_unresolved_outcome_pressure_row_count != _row_reason_family_count(
        report.priority_rows,
        (
            OUTCOME_PRESSURE_HIGH_BLOCKED_REASON,
            OUTCOME_PRESSURE_HIGH_WATCH_REASON,
        ),
    ):
        raise ValueError(
            "high_unresolved_outcome_pressure_row_count must match priority_rows",
        )
    if report.max_source_recheck_age_seconds != _max_optional_seconds(
        tuple(row.source_recheck_age_seconds for row in report.priority_rows),
    ):
        raise ValueError("max_source_recheck_age_seconds must match priority_rows")
    if report.min_source_coverage_ratio != _min_ratio(
        tuple(row.source_coverage_ratio for row in report.priority_rows),
    ):
        raise ValueError("min_source_coverage_ratio must match priority_rows")
    if report.max_unresolved_outcome_pressure != _max_ratio(
        tuple(row.unresolved_outcome_pressure for row in report.priority_rows),
    ):
        raise ValueError("max_unresolved_outcome_pressure must match priority_rows")
    if report.priority_ratio != _ratio(
        report.prioritized_row_count,
        report.input_row_count,
    ):
        raise ValueError("priority_ratio must match row counts")
    if report.report_status != _report_status(report.priority_rows):
        raise ValueError("report_status must match priority_rows")
    if report.reason_codes != _report_reason_codes(report.priority_rows):
        raise ValueError("reason_codes must match priority_rows")
    if report.priority_rows != tuple(
        sorted(report.priority_rows, key=_priority_row_sort_key),
    ):
        raise ValueError("priority_rows must use deterministic sorting")


def _canonical_row_reason_code_sequence(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in reason_codes)


def _row_reason_codes_from_metrics(
    row: TeamMemoryOutcomeSourceRecheckPriorityRow,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    source_reason_code = _source_recheck_reason_code_from_metrics(row)
    if source_reason_code is not None:
        reason_codes.append(source_reason_code)
    coverage_reason_code = _source_coverage_reason_code_from_metrics(row)
    if coverage_reason_code is not None:
        reason_codes.append(coverage_reason_code)
    pressure_reason_code = _unresolved_outcome_pressure_reason_code_from_metrics(row)
    if pressure_reason_code is not None:
        reason_codes.append(pressure_reason_code)
    return tuple(reason_codes)


def _source_recheck_reason_code_from_metrics(
    row: TeamMemoryOutcomeSourceRecheckPriorityRow,
) -> str | None:
    present = tuple(
        reason_code
        for reason_code in (
            SOURCE_RECHECK_MISSING_REASON,
            SOURCE_RECHECK_STALE_BLOCKED_REASON,
            SOURCE_RECHECK_STALE_WATCH_REASON,
        )
        if reason_code in row.reason_codes
    )
    if not present:
        if row.latest_source_rechecked_at is None or row.source_recheck_age_seconds is None:
            raise ValueError("reason_codes must match row metrics")
        return None
    if len(present) != 1:
        raise ValueError("reason_codes must match row metrics")
    reason_code = present[0]
    if reason_code == SOURCE_RECHECK_MISSING_REASON:
        if row.latest_source_rechecked_at is not None or (
            row.source_recheck_age_seconds is not None
        ):
            raise ValueError("reason_codes must match row metrics")
        return reason_code
    if row.latest_source_rechecked_at is None or row.source_recheck_age_seconds is None:
        raise ValueError("reason_codes must match row metrics")
    return reason_code


def _source_coverage_reason_code_from_metrics(
    row: TeamMemoryOutcomeSourceRecheckPriorityRow,
) -> str | None:
    present = tuple(
        reason_code
        for reason_code in (
            SOURCE_COVERAGE_LOW_BLOCKED_REASON,
            SOURCE_COVERAGE_LOW_WATCH_REASON,
        )
        if reason_code in row.reason_codes
    )
    if not present:
        return None
    if len(present) != 1:
        raise ValueError("reason_codes must match row metrics")
    if row.source_coverage_ratio == ONE:
        raise ValueError("reason_codes must match row metrics")
    return present[0]


def _unresolved_outcome_pressure_reason_code_from_metrics(
    row: TeamMemoryOutcomeSourceRecheckPriorityRow,
) -> str | None:
    present = tuple(
        reason_code
        for reason_code in (
            OUTCOME_PRESSURE_HIGH_BLOCKED_REASON,
            OUTCOME_PRESSURE_HIGH_WATCH_REASON,
        )
        if reason_code in row.reason_codes
    )
    if not present:
        return None
    if len(present) != 1:
        raise ValueError("reason_codes must match row metrics")
    return present[0]


def _input_key(row: TeamMemoryOutcomeSourceRecheckPriorityInput) -> tuple[str, str, str]:
    return (row.team_id, row.category_id, row.outcome_id)


def _source_recheck_age_seconds(
    *,
    generated_at: datetime,
    latest_source_rechecked_at: datetime | None,
) -> Decimal | None:
    if latest_source_rechecked_at is None:
        return None
    if latest_source_rechecked_at > generated_at:
        raise ValueError("latest_source_rechecked_at must not be after generated_at")
    return _duration_seconds(latest_source_rechecked_at, generated_at)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end time must be at least start time")
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        return seconds.quantize(NUMERIC_QUANTUM)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", numerator / denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", numerator / denominator)


def _status_count(
    rows: tuple[TeamMemoryOutcomeSourceRecheckPriorityRow, ...],
    status: str,
) -> Decimal:
    return _count_from_int(sum(1 for row in rows if row.priority_status == status))


def _row_reason_family_count(
    rows: tuple[TeamMemoryOutcomeSourceRecheckPriorityRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_from_int(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _max_optional_seconds(values: tuple[Decimal | None, ...]) -> Decimal:
    present_values = tuple(value for value in values if value is not None)
    if not present_values:
        return ZERO
    return _normalize_nonnegative_decimal("max_source_recheck_age_seconds", max(present_values))


def _min_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_ratio("min_ratio", min(values))


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_ratio("max_ratio", max(values))


def _count_from_int(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(NUMERIC_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(NUMERIC_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a Decimal with valid scale") from exc


def _normalize_optional_seconds(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(NUMERIC_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a ratio Decimal") from exc


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != UTC_OFFSET:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    return value


__all__ = (
    "DEFAULT_TEAM_MEMORY_OUTCOME_SOURCE_RECHECK_PRIORITY_CONFIG_VERSION",
    "TeamMemoryOutcomeSourceRecheckPriorityConfig",
    "TeamMemoryOutcomeSourceRecheckPriorityInput",
    "TeamMemoryOutcomeSourceRecheckPriorityInputRow",
    "TeamMemoryOutcomeSourceRecheckPriorityReport",
    "TeamMemoryOutcomeSourceRecheckPriorityRow",
    "build_team_memory_outcome_source_recheck_priority_report",
    "team_memory_outcome_source_recheck_priority_report_to_json",
    "team_memory_outcome_source_recheck_priority_report_to_jsonable",
)

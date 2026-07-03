"""Pure in-memory team memory source recheck cadence status report."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_STATUS_CONFIG_VERSION = (
    "team-memory-source-recheck-cadence-status-v0"
)

BLOCKED_OVERDUE_REASON = "team_memory_source_recheck_cadence_blocked_overdue"
MISSING_HISTORY_REASON = "team_memory_source_recheck_cadence_missing_history"
OVERDUE_REASON = "team_memory_source_recheck_cadence_overdue"
DUE_SOON_REASON = "team_memory_source_recheck_cadence_due_soon"
CURRENT_REASON = "team_memory_source_recheck_cadence_current"
NO_SOURCES_REASON = "team_memory_source_recheck_cadence_no_sources"

REASON_CODES = (
    BLOCKED_OVERDUE_REASON,
    MISSING_HISTORY_REASON,
    OVERDUE_REASON,
    DUE_SOON_REASON,
    CURRENT_REASON,
    NO_SOURCES_REASON,
)
ROW_REASON_CODES = REASON_CODES[:-1]
CADENCE_STATUSES = ("current", "due_soon", "overdue", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
STATUS_SORT_WEIGHT = {
    "blocked": 0,
    "overdue": 1,
    "due_soon": 2,
    "current": 3,
}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


EXTRA_UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("can", "cel"),
        _join_parts("li", "ve"),
        _join_parts("net", "work"),
        _join_parts("or", "der"),
        _join_parts("sign", "ing"),
        _join_parts("sub", "mit"),
        _join_parts("wal", "let"),
    ),
)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceStatusConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_STATUS_CONFIG_VERSION
    due_soon_window_seconds: Decimal = Decimal("3600.000000")
    blocked_overdue_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "due_soon_window_seconds",
            _require_positive_decimal(
                "due_soon_window_seconds",
                self.due_soon_window_seconds,
            ),
        )
        object.__setattr__(
            self,
            "blocked_overdue_age_seconds",
            _require_positive_decimal(
                "blocked_overdue_age_seconds",
                self.blocked_overdue_age_seconds,
            ),
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceSource:
    team_id: str
    source_id: str
    source_family: str
    last_rechecked_at: datetime | None
    next_recheck_due_at: datetime
    source_config_version: str = DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_STATUS_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_public_string("source_id", self.source_id)
        _require_public_string("source_family", self.source_family)
        if self.last_rechecked_at is not None:
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
        _require_canonical_string("source_config_version", self.source_config_version)
        _validate_source_shape(self)
        require_paper_only_flags("source", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceStatusRow:
    team_id: str
    source_id: str
    source_family: str
    cadence_status: str
    last_rechecked_at: datetime | None
    next_recheck_due_at: datetime
    due_delta_seconds: Decimal
    overdue_age_seconds: Decimal
    last_recheck_age_seconds: Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_public_string("source_id", self.source_id)
        _require_public_string("source_family", self.source_family)
        _require_cadence_status("cadence_status", self.cadence_status)
        if self.last_rechecked_at is not None:
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
        object.__setattr__(
            self,
            "due_delta_seconds",
            _require_decimal("due_delta_seconds", self.due_delta_seconds),
        )
        object.__setattr__(
            self,
            "overdue_age_seconds",
            _require_nonnegative_decimal(
                "overdue_age_seconds",
                self.overdue_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "last_recheck_age_seconds",
            _normalize_optional_decimal(
                "last_recheck_age_seconds",
                self.last_recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, row_scope=True),
        )
        _validate_row(self)
        require_paper_only_flags("status row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceStatusReasonCodeCount:
    reason_code: str
    source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "source_count",
            _require_count_decimal("source_count", self.source_count),
        )
        require_paper_only_flags("reason code count", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceStatusReport:
    generated_at: datetime
    config_version: str
    report_status: str
    source_count: Decimal
    current_source_count: Decimal
    due_soon_source_count: Decimal
    overdue_source_count: Decimal
    blocked_source_count: Decimal
    missing_history_source_count: Decimal
    watch_source_count: Decimal
    overdue_source_ratio: Decimal
    blocked_source_ratio: Decimal
    max_overdue_age_seconds: Decimal | None
    max_last_recheck_age_seconds: Decimal | None
    rows: tuple[TeamMemorySourceRecheckCadenceStatusRow, ...]
    reason_code_counts: tuple[TeamMemorySourceRecheckCadenceStatusReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "source_count",
            "current_source_count",
            "due_soon_source_count",
            "overdue_source_count",
            "blocked_source_count",
            "missing_history_source_count",
            "watch_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("overdue_source_ratio", "blocked_source_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_overdue_age_seconds",
            _normalize_optional_decimal(
                "max_overdue_age_seconds",
                self.max_overdue_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_last_recheck_age_seconds",
            _normalize_optional_decimal(
                "max_last_recheck_age_seconds",
                self.max_last_recheck_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, row_scope=False),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)


def build_team_memory_source_recheck_cadence_status_report(
    sources: list[TeamMemorySourceRecheckCadenceSource]
    | tuple[TeamMemorySourceRecheckCadenceSource, ...],
    *,
    config: TeamMemorySourceRecheckCadenceStatusConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceStatusReport:
    if type(config) is not TeamMemorySourceRecheckCadenceStatusConfig:
        raise ValueError("config must be a TeamMemorySourceRecheckCadenceStatusConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources, generated_at=generated_at_utc)
    rows = _status_rows(
        normalized_sources,
        config=config,
        generated_at=generated_at_utc,
    )

    return TeamMemorySourceRecheckCadenceStatusReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        source_count=_decimal_count(len(rows)),
        current_source_count=_decimal_count(
            sum(1 for row in rows if row.cadence_status == "current"),
        ),
        due_soon_source_count=_decimal_count(
            sum(1 for row in rows if row.cadence_status == "due_soon"),
        ),
        overdue_source_count=_decimal_count(
            _count_rows_with_reason(rows, OVERDUE_REASON),
        ),
        blocked_source_count=_decimal_count(
            sum(1 for row in rows if row.cadence_status == "blocked"),
        ),
        missing_history_source_count=_decimal_count(
            _count_rows_with_reason(rows, MISSING_HISTORY_REASON),
        ),
        watch_source_count=_decimal_count(
            sum(1 for row in rows if row.cadence_status in ("due_soon", "overdue")),
        ),
        overdue_source_ratio=_ratio(
            _decimal_count(_count_rows_with_reason(rows, OVERDUE_REASON)),
            _decimal_count(len(rows)),
        ),
        blocked_source_ratio=_ratio(
            _decimal_count(sum(1 for row in rows if row.cadence_status == "blocked")),
            _decimal_count(len(rows)),
        ),
        max_overdue_age_seconds=_max_row_decimal(rows, "overdue_age_seconds"),
        max_last_recheck_age_seconds=_max_optional_row_decimal(
            rows,
            "last_recheck_age_seconds",
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts_for_rows(rows),
        reason_codes=_report_reason_codes(rows),
    )


def team_memory_source_recheck_cadence_status_report_payload(
    report: TeamMemorySourceRecheckCadenceStatusReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemorySourceRecheckCadenceStatusReport:
        raise ValueError("report must be a TeamMemorySourceRecheckCadenceStatusReport")
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    reject_unsafe_surface_fields("team memory source recheck cadence status payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _status_rows(
    sources: tuple[TeamMemorySourceRecheckCadenceSource, ...],
    *,
    config: TeamMemorySourceRecheckCadenceStatusConfig,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceStatusRow, ...]:
    rows = tuple(
        _status_row(source, config=config, generated_at=generated_at)
        for source in sources
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _status_row(
    source: TeamMemorySourceRecheckCadenceSource,
    *,
    config: TeamMemorySourceRecheckCadenceStatusConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceStatusRow:
    due_delta_seconds = _seconds_between(generated_at, source.next_recheck_due_at)
    overdue_age_seconds = -due_delta_seconds if due_delta_seconds < ZERO else ZERO
    last_recheck_age_seconds = (
        None
        if source.last_rechecked_at is None
        else _elapsed_seconds(source.last_rechecked_at, generated_at)
    )
    reason_codes = _source_reason_codes(
        source=source,
        due_delta_seconds=due_delta_seconds,
        overdue_age_seconds=overdue_age_seconds,
        config=config,
    )

    return TeamMemorySourceRecheckCadenceStatusRow(
        team_id=source.team_id,
        source_id=source.source_id,
        source_family=source.source_family,
        cadence_status=_row_status(reason_codes),
        last_rechecked_at=source.last_rechecked_at,
        next_recheck_due_at=source.next_recheck_due_at,
        due_delta_seconds=due_delta_seconds,
        overdue_age_seconds=overdue_age_seconds,
        last_recheck_age_seconds=last_recheck_age_seconds,
        reason_codes=reason_codes,
    )


def _source_reason_codes(
    *,
    source: TeamMemorySourceRecheckCadenceSource,
    due_delta_seconds: Decimal,
    overdue_age_seconds: Decimal,
    config: TeamMemorySourceRecheckCadenceStatusConfig,
) -> tuple[str, ...]:
    if source.last_rechecked_at is None:
        return (MISSING_HISTORY_REASON,)
    if overdue_age_seconds > config.blocked_overdue_age_seconds:
        return (BLOCKED_OVERDUE_REASON, OVERDUE_REASON)
    if overdue_age_seconds > ZERO:
        return (OVERDUE_REASON,)
    if due_delta_seconds <= config.due_soon_window_seconds:
        return (DUE_SOON_REASON,)
    return (CURRENT_REASON,)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCKED_OVERDUE_REASON in reason_codes or MISSING_HISTORY_REASON in reason_codes:
        return "blocked"
    if OVERDUE_REASON in reason_codes:
        return "overdue"
    if DUE_SOON_REASON in reason_codes:
        return "due_soon"
    return "current"


def _row_sort_key(
    row: TeamMemorySourceRecheckCadenceStatusRow,
) -> tuple[int, int, Decimal, Decimal, str, str, str]:
    return (
        STATUS_SORT_WEIGHT[row.cadence_status],
        0 if BLOCKED_OVERDUE_REASON in row.reason_codes else 1,
        -row.overdue_age_seconds,
        row.due_delta_seconds,
        row.team_id,
        row.source_family,
        row.source_id,
    )


def _report_status(rows: tuple[TeamMemorySourceRecheckCadenceStatusRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.cadence_status == "blocked" for row in rows):
        return "blocked"
    if any(row.cadence_status in ("due_soon", "overdue") for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamMemorySourceRecheckCadenceStatusRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_SOURCES_REASON,)
    return _canonical_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
        row_scope=False,
    )


def _reason_code_counts_for_rows(
    rows: tuple[TeamMemorySourceRecheckCadenceStatusRow, ...],
) -> tuple[TeamMemorySourceRecheckCadenceStatusReasonCodeCount, ...]:
    if not rows:
        return (
            TeamMemorySourceRecheckCadenceStatusReasonCodeCount(
                reason_code=NO_SOURCES_REASON,
                source_count=ZERO,
            ),
        )
    flattened = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        TeamMemorySourceRecheckCadenceStatusReasonCodeCount(
            reason_code=reason_code,
            source_count=_decimal_count(
                sum(1 for item in flattened if item == reason_code),
            ),
        )
        for reason_code in REASON_CODES
        if reason_code in flattened
    )


def _normalize_sources(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceSource, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    sources = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for source in sources:
        if type(source) is not TeamMemorySourceRecheckCadenceSource:
            raise ValueError("sources must contain TeamMemorySourceRecheckCadenceSource")
        require_paper_only_flags("source", source)
        if source.last_rechecked_at is not None and source.last_rechecked_at > generated_at:
            raise ValueError("last_rechecked_at must not be in the future")
        key = (source.team_id, source.source_id)
        if key in seen_keys:
            raise ValueError("source_id values must be unique per team")
        seen_keys.add(key)
    return sources


def _normalize_rows(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceStatusRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceStatusRow:
            raise ValueError("rows must contain status row values")
        require_paper_only_flags("status row", row)
        key = (row.team_id, row.source_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by team and source")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceStatusReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not TeamMemorySourceRecheckCadenceStatusReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        require_paper_only_flags("reason code count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must be unique by reason code")
        seen_reason_codes.add(count.reason_code)
    if tuple(count.reason_code for count in counts) != _canonical_reason_codes(
        tuple(count.reason_code for count in counts),
        row_scope=False,
    ):
        raise ValueError("reason_code_counts must be deterministic")
    return counts


def _normalize_reason_codes(
    value: object,
    *,
    row_scope: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if NO_SOURCES_REASON in reason_codes and reason_codes != (NO_SOURCES_REASON,):
        raise ValueError("no sources reason cannot be combined")
    if row_scope and NO_SOURCES_REASON in reason_codes:
        raise ValueError("no sources reason is not valid for rows")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if reason_codes != _canonical_reason_codes(reason_codes, row_scope=row_scope):
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _canonical_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    row_scope: bool,
) -> tuple[str, ...]:
    allowed_codes = ROW_REASON_CODES if row_scope else REASON_CODES
    return tuple(reason_code for reason_code in allowed_codes if reason_code in reason_codes)


def _validate_source_shape(source: TeamMemorySourceRecheckCadenceSource) -> None:
    if (
        source.last_rechecked_at is not None
        and source.next_recheck_due_at < source.last_rechecked_at
    ):
        raise ValueError("next_recheck_due_at must not be before last_rechecked_at")


def _validate_row(row: TeamMemorySourceRecheckCadenceStatusRow) -> None:
    if row.cadence_status != _row_status(row.reason_codes):
        raise ValueError("cadence_status must match reason_codes")
    expected_overdue_age_seconds = (
        -row.due_delta_seconds if row.due_delta_seconds < ZERO else ZERO
    )
    if row.overdue_age_seconds != expected_overdue_age_seconds:
        raise ValueError("overdue_age_seconds must match due_delta_seconds")
    if row.last_rechecked_at is None:
        if row.last_recheck_age_seconds is not None:
            raise ValueError("missing last_rechecked_at requires empty age")
        if row.reason_codes != (MISSING_HISTORY_REASON,):
            raise ValueError("missing last_rechecked_at requires missing history reason")
    else:
        if row.last_recheck_age_seconds is None:
            raise ValueError("last_rechecked_at requires age")
        if MISSING_HISTORY_REASON in row.reason_codes:
            raise ValueError("missing history reason requires missing last_rechecked_at")
    if BLOCKED_OVERDUE_REASON in row.reason_codes and OVERDUE_REASON not in row.reason_codes:
        raise ValueError("blocked overdue reason requires overdue reason")
    if OVERDUE_REASON in row.reason_codes and row.overdue_age_seconds <= ZERO:
        raise ValueError("overdue reason requires positive overdue age")
    if DUE_SOON_REASON in row.reason_codes and row.due_delta_seconds < ZERO:
        raise ValueError("due soon reason requires nonnegative due delta")
    if CURRENT_REASON in row.reason_codes and row.reason_codes != (CURRENT_REASON,):
        raise ValueError("current reason cannot be combined")


def _validate_report(report: TeamMemorySourceRecheckCadenceStatusReport) -> None:
    if report.source_count != _decimal_count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.current_source_count != _decimal_count(
        sum(1 for row in report.rows if row.cadence_status == "current"),
    ):
        raise ValueError("current_source_count must match rows")
    if report.due_soon_source_count != _decimal_count(
        sum(1 for row in report.rows if row.cadence_status == "due_soon"),
    ):
        raise ValueError("due_soon_source_count must match rows")
    if report.overdue_source_count != _decimal_count(
        _count_rows_with_reason(report.rows, OVERDUE_REASON),
    ):
        raise ValueError("overdue_source_count must match rows")
    if report.blocked_source_count != _decimal_count(
        sum(1 for row in report.rows if row.cadence_status == "blocked"),
    ):
        raise ValueError("blocked_source_count must match rows")
    if report.missing_history_source_count != _decimal_count(
        _count_rows_with_reason(report.rows, MISSING_HISTORY_REASON),
    ):
        raise ValueError("missing_history_source_count must match rows")
    if report.watch_source_count != _decimal_count(
        sum(1 for row in report.rows if row.cadence_status in ("due_soon", "overdue")),
    ):
        raise ValueError("watch_source_count must match rows")
    if report.overdue_source_ratio != _ratio(report.overdue_source_count, report.source_count):
        raise ValueError("overdue_source_ratio must match rows")
    if report.blocked_source_ratio != _ratio(report.blocked_source_count, report.source_count):
        raise ValueError("blocked_source_ratio must match rows")
    if report.max_overdue_age_seconds != _max_row_decimal(
        report.rows,
        "overdue_age_seconds",
    ):
        raise ValueError("max_overdue_age_seconds must match rows")
    if report.max_last_recheck_age_seconds != _max_optional_row_decimal(
        report.rows,
        "last_recheck_age_seconds",
    ):
        raise ValueError("max_last_recheck_age_seconds must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_for_rows(report.rows):
        raise ValueError("reason_code_counts must summarize rows")


def _count_rows_with_reason(
    rows: tuple[TeamMemorySourceRecheckCadenceStatusRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _max_row_decimal(
    rows: tuple[TeamMemorySourceRecheckCadenceStatusRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return max(getattr(row, field_name) for row in rows)


def _max_optional_row_decimal(
    rows: tuple[TeamMemorySourceRecheckCadenceStatusRow, ...],
    field_name: str,
) -> Decimal | None:
    values = tuple(
        getattr(row, field_name)
        for row in rows
        if getattr(row, field_name) is not None
    )
    return max(values) if values else None


def _elapsed_seconds(start_at: datetime, end_at: datetime) -> Decimal:
    age_seconds = _seconds_between(start_at, end_at)
    if age_seconds < ZERO:
        raise ValueError("age seconds must be nonnegative")
    return age_seconds


def _seconds_between(start_at: datetime, end_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return seconds.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_cadence_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CADENCE_STATUSES:
        raise ValueError(f"{field_name} must be current, due_soon, overdue, or blocked")


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(
        fragment in lowered
        for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS | EXTRA_UNSAFE_TEXT_FRAGMENTS
    ):
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
    "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_STATUS_CONFIG_VERSION",
    "TeamMemorySourceRecheckCadenceSource",
    "TeamMemorySourceRecheckCadenceStatusConfig",
    "TeamMemorySourceRecheckCadenceStatusReasonCodeCount",
    "TeamMemorySourceRecheckCadenceStatusReport",
    "TeamMemorySourceRecheckCadenceStatusRow",
    "build_team_memory_source_recheck_cadence_status_report",
    "team_memory_source_recheck_cadence_status_report_payload",
)

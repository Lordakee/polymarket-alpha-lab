"""Pure report-only reducer for team memory replay gap queues."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_TEAM_MEMORY_REPLAY_GAP_QUEUE_CONFIG_VERSION = (
    "team-memory-replay-gap-queue-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
SECONDS_QUANTUM = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
SOURCE_RESPONSE_STATUSES = ("responded", "pending", "missing")
REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = (
    "missing_replay_validation",
    "stale_replay_coverage",
    "unresolved_postmortem_learnings",
    "pending_replay_response",
    "normal_replay_coverage",
)
REASON_CODES = (
    "no_team_memory_replay_rows_supplied",
    "missing_replay_validation",
    "stale_replay_coverage",
    "unresolved_postmortem_learnings",
    "pending_replay_response",
    "missing_replay_response",
    "normal_replay_coverage_observed",
)

__all__ = (
    "DEFAULT_TEAM_MEMORY_REPLAY_GAP_QUEUE_CONFIG_VERSION",
    "TeamMemoryReplayGapQueueConfig",
    "TeamMemoryReplayGapQueueReport",
    "TeamMemoryReplayGapQueueRow",
    "TeamMemoryReplayGapRow",
    "build_team_memory_replay_gap_queue_report",
    "team_memory_replay_gap_queue_payload",
)


@dataclass(frozen=True)
class TeamMemoryReplayGapQueueConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_REPLAY_GAP_QUEUE_CONFIG_VERSION
    stale_replay_after_seconds: Decimal = Decimal("86400.000000")
    unresolved_learning_pressure_threshold: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_replay_after_seconds",
            _normalize_positive_seconds(
                "stale_replay_after_seconds",
                self.stale_replay_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_learning_pressure_threshold",
            _normalize_positive_count(
                "unresolved_learning_pressure_threshold",
                self.unresolved_learning_pressure_threshold,
            ),
        )
        require_paper_only_flags("TeamMemoryReplayGapQueueConfig", self)


@dataclass(frozen=True)
class TeamMemoryReplayGapRow:
    team_id: str
    category_id: str
    latest_replay_validated_at: datetime | None
    latest_replay_coverage_ratio: Decimal
    unresolved_postmortem_learning_count: Decimal
    latest_response_status: str
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
        object.__setattr__(
            self,
            "latest_replay_validated_at",
            _as_optional_utc(
                "latest_replay_validated_at",
                self.latest_replay_validated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_replay_coverage_ratio",
            _normalize_nonnegative_ratio(
                "latest_replay_coverage_ratio",
                self.latest_replay_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_postmortem_learning_count",
            _normalize_nonnegative_count(
                "unresolved_postmortem_learning_count",
                self.unresolved_postmortem_learning_count,
            ),
        )
        _require_member(
            "latest_response_status",
            self.latest_response_status,
            SOURCE_RESPONSE_STATUSES,
        )
        reject_unsafe_surface_fields("team memory replay gap row", self)
        require_paper_only_flags("TeamMemoryReplayGapRow", self)


@dataclass(frozen=True)
class TeamMemoryReplayGapQueueRow:
    team_id: str
    category_id: str
    response_status: str
    latest_replay_validated_at: datetime | None
    replay_age_seconds: Decimal | None
    latest_replay_coverage_ratio: Decimal
    unresolved_postmortem_learning_count: Decimal
    latest_response_status: str
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
        _require_member("response_status", self.response_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "latest_replay_validated_at",
            _as_optional_utc(
                "latest_replay_validated_at",
                self.latest_replay_validated_at,
            ),
        )
        object.__setattr__(
            self,
            "replay_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "replay_age_seconds",
                self.replay_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "latest_replay_coverage_ratio",
            _normalize_nonnegative_ratio(
                "latest_replay_coverage_ratio",
                self.latest_replay_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_postmortem_learning_count",
            _normalize_nonnegative_count(
                "unresolved_postmortem_learning_count",
                self.unresolved_postmortem_learning_count,
            ),
        )
        _require_member(
            "latest_response_status",
            self.latest_response_status,
            SOURCE_RESPONSE_STATUSES,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        reject_unsafe_surface_fields("team memory replay gap queue row", self)
        require_paper_only_flags("TeamMemoryReplayGapQueueRow", self)
        _validate_queue_row(self)


@dataclass(frozen=True)
class TeamMemoryReplayGapQueueReport:
    generated_at: datetime
    config_version: str
    response_status: str
    source_row_count: Decimal
    row_count: Decimal
    missing_replay_validation_count: Decimal
    stale_replay_coverage_count: Decimal
    unresolved_postmortem_learning_count: Decimal
    pending_response_count: Decimal
    missing_response_count: Decimal
    normal_count: Decimal
    max_replay_age_seconds: Decimal | None
    max_unresolved_postmortem_learning_count: Decimal | None
    rows: tuple[TeamMemoryReplayGapQueueRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("response_status", self.response_status, REPORT_STATUSES)
        for field_name in (
            "source_row_count",
            "row_count",
            "missing_replay_validation_count",
            "stale_replay_coverage_count",
            "unresolved_postmortem_learning_count",
            "pending_response_count",
            "missing_response_count",
            "normal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_replay_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "max_replay_age_seconds",
                self.max_replay_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_unresolved_postmortem_learning_count",
            _normalize_optional_nonnegative_count(
                "max_unresolved_postmortem_learning_count",
                self.max_unresolved_postmortem_learning_count,
            ),
        )
        object.__setattr__(self, "rows", _normalize_queue_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        reject_unsafe_surface_fields("team memory replay gap queue report", self)
        require_paper_only_flags("TeamMemoryReplayGapQueueReport", self)
        _validate_report(self)


def build_team_memory_replay_gap_queue_report(
    rows: list[TeamMemoryReplayGapRow] | tuple[TeamMemoryReplayGapRow, ...],
    *,
    config: TeamMemoryReplayGapQueueConfig,
    generated_at: datetime,
) -> TeamMemoryReplayGapQueueReport:
    if type(config) is not TeamMemoryReplayGapQueueConfig:
        raise ValueError("config must be a TeamMemoryReplayGapQueueConfig")
    require_paper_only_flags("TeamMemoryReplayGapQueueConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(rows)
    queue_rows = tuple(
        sorted(
            (_queue_row(row, config, generated_at_utc) for row in source_rows),
            key=_queue_row_sort_key,
        ),
    )
    _reject_future_replay_times(queue_rows, generated_at_utc)
    reason_codes = _report_reason_codes(queue_rows, len(source_rows))

    return TeamMemoryReplayGapQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        response_status=_report_status(reason_codes),
        source_row_count=_count(len(source_rows)),
        row_count=_count(len(queue_rows)),
        missing_replay_validation_count=_status_count(
            queue_rows,
            "missing_replay_validation",
        ),
        stale_replay_coverage_count=_status_count(queue_rows, "stale_replay_coverage"),
        unresolved_postmortem_learning_count=_status_count(
            queue_rows,
            "unresolved_postmortem_learnings",
        ),
        pending_response_count=_pending_response_count(queue_rows),
        missing_response_count=_missing_response_count(queue_rows),
        normal_count=_status_count(queue_rows, "normal_replay_coverage"),
        max_replay_age_seconds=_max_optional_decimal(
            tuple(
                row.replay_age_seconds
                for row in queue_rows
                if row.replay_age_seconds is not None
            ),
        ),
        max_unresolved_postmortem_learning_count=_max_optional_decimal(
            tuple(row.unresolved_postmortem_learning_count for row in queue_rows),
        ),
        rows=queue_rows,
        reason_codes=reason_codes,
    )


def team_memory_replay_gap_queue_payload(
    report: TeamMemoryReplayGapQueueReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemoryReplayGapQueueReport:
        raise ValueError("report must be a TeamMemoryReplayGapQueueReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("team memory replay gap queue report", report)
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("team memory replay gap queue payload", ready)
    return ready


def _normalize_source_rows(value: object) -> tuple[TeamMemoryReplayGapRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(_coerce_source_row(row) for row in value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        require_paper_only_flags("TeamMemoryReplayGapRow", row)
        key = (row.team_id, row.category_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by team and category")
        seen_keys.add(key)
    return rows


def _coerce_source_row(value: object) -> TeamMemoryReplayGapRow:
    if type(value) is TeamMemoryReplayGapRow:
        return value
    if isinstance(value, Mapping):
        return TeamMemoryReplayGapRow(
            team_id=value.get("team_id"),
            category_id=value.get("category_id"),
            latest_replay_validated_at=value.get("latest_replay_validated_at"),
            latest_replay_coverage_ratio=value.get("latest_replay_coverage_ratio"),
            unresolved_postmortem_learning_count=value.get(
                "unresolved_postmortem_learning_count",
            ),
            latest_response_status=value.get("latest_response_status"),
            paper_only=value.get("paper_only", True),
            report_only=value.get("report_only", True),
            readonly=value.get("readonly", True),
        )
    raise ValueError("rows must contain TeamMemoryReplayGapRow values")


def _queue_row(
    row: TeamMemoryReplayGapRow,
    config: TeamMemoryReplayGapQueueConfig,
    generated_at: datetime,
) -> TeamMemoryReplayGapQueueRow:
    replay_age_seconds = _replay_age_seconds(row.latest_replay_validated_at, generated_at)
    status = _row_status(row, config, replay_age_seconds)
    return TeamMemoryReplayGapQueueRow(
        team_id=row.team_id,
        category_id=row.category_id,
        response_status=status,
        latest_replay_validated_at=row.latest_replay_validated_at,
        replay_age_seconds=replay_age_seconds,
        latest_replay_coverage_ratio=row.latest_replay_coverage_ratio,
        unresolved_postmortem_learning_count=row.unresolved_postmortem_learning_count,
        latest_response_status=row.latest_response_status,
        reason_codes=_row_reason_codes(status, row.latest_response_status),
    )


def _row_status(
    row: TeamMemoryReplayGapRow,
    config: TeamMemoryReplayGapQueueConfig,
    replay_age_seconds: Decimal | None,
) -> str:
    if row.latest_replay_validated_at is None:
        return "missing_replay_validation"
    if (
        replay_age_seconds is not None
        and replay_age_seconds > config.stale_replay_after_seconds
    ):
        return "stale_replay_coverage"
    if row.latest_replay_coverage_ratio < ONE_RATIO:
        return "stale_replay_coverage"
    if (
        row.unresolved_postmortem_learning_count
        >= config.unresolved_learning_pressure_threshold
    ):
        return "unresolved_postmortem_learnings"
    if row.latest_response_status == "pending":
        return "pending_replay_response"
    if row.latest_response_status == "missing":
        return "missing_replay_validation"
    return "normal_replay_coverage"


def _row_reason_codes(
    status: str,
    latest_response_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if status == "normal_replay_coverage":
        codes.append("normal_replay_coverage_observed")
    else:
        codes.append(status)
    if latest_response_status == "pending" and "pending_replay_response" not in codes:
        codes.append("pending_replay_response")
    if latest_response_status == "missing" and "missing_replay_response" not in codes:
        codes.append("missing_replay_response")
    return tuple(code for code in REASON_CODES if code in codes)


def _report_reason_codes(
    rows: tuple[TeamMemoryReplayGapQueueRow, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return ("no_team_memory_replay_rows_supplied",)
    codes: list[str] = []
    for code in REASON_CODES[1:]:
        if code == "normal_replay_coverage_observed":
            if any(row.response_status == "normal_replay_coverage" for row in rows):
                codes.append(code)
            continue
        if any(code in row.reason_codes for row in rows):
            codes.append(code)
    return tuple(codes)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes or reason_codes == ("no_team_memory_replay_rows_supplied",):
        return "pass"
    if any(code in reason_codes for code in REASON_CODES[1:4]):
        return "blocked"
    if "pending_replay_response" in reason_codes:
        return "watch"
    return "pass"


def _queue_row_sort_key(row: TeamMemoryReplayGapQueueRow) -> tuple[int, str, str]:
    return (ROW_STATUSES.index(row.response_status), row.team_id, row.category_id)


def _status_count(
    rows: tuple[TeamMemoryReplayGapQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.response_status == status))


def _pending_response_count(rows: tuple[TeamMemoryReplayGapQueueRow, ...]) -> Decimal:
    return _count(sum(1 for row in rows if row.latest_response_status == "pending"))


def _missing_response_count(rows: tuple[TeamMemoryReplayGapQueueRow, ...]) -> Decimal:
    return _count(sum(1 for row in rows if row.latest_response_status == "missing"))


def _normalize_queue_rows(value: object) -> tuple[TeamMemoryReplayGapQueueRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemoryReplayGapQueueRow:
            raise ValueError("rows must contain TeamMemoryReplayGapQueueRow values")
        require_paper_only_flags("TeamMemoryReplayGapQueueRow", row)
        key = (row.team_id, row.category_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by team and category")
        seen_keys.add(key)
    return tuple(sorted(rows, key=_queue_row_sort_key))


def _validate_queue_row(row: TeamMemoryReplayGapQueueRow) -> None:
    expected = _row_reason_codes(row.response_status, row.latest_response_status)
    if row.reason_codes != expected:
        raise ValueError("reason_codes must match response_status")
    if row.latest_replay_validated_at is None and row.replay_age_seconds is not None:
        raise ValueError("replay_age_seconds must be absent without replay validation")
    if row.latest_replay_validated_at is not None and row.replay_age_seconds is None:
        raise ValueError("replay_age_seconds is required with replay validation")


def _validate_report(report: TeamMemoryReplayGapQueueReport) -> None:
    if report.source_row_count != report.row_count:
        raise ValueError("source_row_count must match row_count")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    expected_counts = {
        "missing_replay_validation_count": _status_count(
            report.rows,
            "missing_replay_validation",
        ),
        "stale_replay_coverage_count": _status_count(
            report.rows,
            "stale_replay_coverage",
        ),
        "unresolved_postmortem_learning_count": _status_count(
            report.rows,
            "unresolved_postmortem_learnings",
        ),
        "pending_response_count": _pending_response_count(report.rows),
        "missing_response_count": _missing_response_count(report.rows),
        "normal_count": _status_count(report.rows, "normal_replay_coverage"),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.source_row_count)):
        raise ValueError("reason_codes must match rows")
    if report.response_status != _report_status(report.reason_codes):
        raise ValueError("response_status must match reason_codes")
    if report.max_replay_age_seconds != _max_optional_decimal(
        tuple(
            row.replay_age_seconds
            for row in report.rows
            if row.replay_age_seconds is not None
        ),
    ):
        raise ValueError("max_replay_age_seconds must match rows")
    if report.max_unresolved_postmortem_learning_count != _max_optional_decimal(
        tuple(row.unresolved_postmortem_learning_count for row in report.rows),
    ):
        raise ValueError("max_unresolved_postmortem_learning_count must match rows")


def _reject_future_replay_times(
    rows: tuple[TeamMemoryReplayGapQueueRow, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if (
            row.latest_replay_validated_at is not None
            and row.latest_replay_validated_at > generated_at
        ):
            raise ValueError("latest_replay_validated_at must not be in the future")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _max_optional_decimal(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return max(values)


def _replay_age_seconds(value: datetime | None, generated_at: datetime) -> Decimal | None:
    if value is None:
        return None
    if value > generated_at:
        raise ValueError("latest_replay_validated_at must not be in the future")
    return _timedelta_seconds_decimal(generated_at - value)


def _timedelta_seconds_decimal(value: timedelta) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total_microseconds = (
            (Decimal(value.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND)
            + (Decimal(value.seconds) * MICROSECONDS_PER_SECOND)
            + Decimal(value.microseconds)
        )
        return (total_microseconds / MICROSECONDS_PER_SECOND).quantize(SECONDS_QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != _require_decimal(field_name, value):
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _normalize_optional_nonnegative_count(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_count(field_name, value)


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {', '.join(members)}")

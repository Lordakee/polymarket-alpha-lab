"""Pure report-only reducer for team memory adjudication follow-up rows."""

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


DEFAULT_TEAM_MEMORY_ADJUDICATION_FOLLOWUP_QUEUE_CONFIG_VERSION = (
    "team-memory-adjudication-followup-queue-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
SOURCE_RESPONSE_STATUSES = ("responded", "pending", "missing")
REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = (
    "missing_adjudication_followup",
    "stale_reviewer_proof",
    "repeated_unresolved_disagreement_family",
    "pending_adjudication_response",
    "normal_adjudication_followup",
)
REASON_CODES = (
    "no_team_memory_adjudication_followup_rows_supplied",
    "missing_adjudication_followup_present",
    "stale_reviewer_proof_present",
    "repeated_unresolved_disagreement_family_present",
    "pending_adjudication_response",
    "missing_adjudication_response",
    "normal_adjudication_followup_observed",
)

__all__ = (
    "DEFAULT_TEAM_MEMORY_ADJUDICATION_FOLLOWUP_QUEUE_CONFIG_VERSION",
    "TeamMemoryAdjudicationFollowupQueueConfig",
    "TeamMemoryAdjudicationFollowupQueueReport",
    "TeamMemoryAdjudicationFollowupQueueRow",
    "TeamMemoryAdjudicationFollowupRow",
    "build_team_memory_adjudication_followup_queue_report",
    "team_memory_adjudication_followup_queue_payload",
)


@dataclass(frozen=True)
class TeamMemoryAdjudicationFollowupQueueConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_ADJUDICATION_FOLLOWUP_QUEUE_CONFIG_VERSION
    stale_reviewer_proof_after_seconds: Decimal = Decimal("86400.000000")
    repeated_unresolved_family_threshold: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_reviewer_proof_after_seconds",
            _normalize_positive_seconds(
                "stale_reviewer_proof_after_seconds",
                self.stale_reviewer_proof_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "repeated_unresolved_family_threshold",
            _normalize_positive_count(
                "repeated_unresolved_family_threshold",
                self.repeated_unresolved_family_threshold,
            ),
        )
        require_paper_only_flags("TeamMemoryAdjudicationFollowupQueueConfig", self)


@dataclass(frozen=True)
class TeamMemoryAdjudicationFollowupRow:
    team_id: str
    category_id: str
    disagreement_family_id: str
    unresolved_disagreement_count: Decimal
    latest_adjudicated_at: datetime | None
    latest_reviewer_proof_at: datetime | None
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
        _require_canonical_string("disagreement_family_id", self.disagreement_family_id)
        object.__setattr__(
            self,
            "unresolved_disagreement_count",
            _normalize_nonnegative_count(
                "unresolved_disagreement_count",
                self.unresolved_disagreement_count,
            ),
        )
        object.__setattr__(
            self,
            "latest_adjudicated_at",
            _as_optional_utc("latest_adjudicated_at", self.latest_adjudicated_at),
        )
        object.__setattr__(
            self,
            "latest_reviewer_proof_at",
            _as_optional_utc("latest_reviewer_proof_at", self.latest_reviewer_proof_at),
        )
        _require_member(
            "latest_response_status",
            self.latest_response_status,
            SOURCE_RESPONSE_STATUSES,
        )
        reject_unsafe_surface_fields("team memory adjudication follow-up row", self)
        require_paper_only_flags("TeamMemoryAdjudicationFollowupRow", self)
        _validate_source_row(self)


@dataclass(frozen=True)
class TeamMemoryAdjudicationFollowupQueueRow:
    team_id: str
    category_id: str
    disagreement_family_id: str
    response_status: str
    unresolved_disagreement_count: Decimal
    latest_adjudicated_at: datetime | None
    latest_reviewer_proof_at: datetime | None
    reviewer_proof_age_seconds: Decimal | None
    latest_response_status: str
    repeated_unresolved_family_count: Decimal
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
        _require_canonical_string("disagreement_family_id", self.disagreement_family_id)
        _require_member("response_status", self.response_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "unresolved_disagreement_count",
            _normalize_nonnegative_count(
                "unresolved_disagreement_count",
                self.unresolved_disagreement_count,
            ),
        )
        object.__setattr__(
            self,
            "latest_adjudicated_at",
            _as_optional_utc("latest_adjudicated_at", self.latest_adjudicated_at),
        )
        object.__setattr__(
            self,
            "latest_reviewer_proof_at",
            _as_optional_utc("latest_reviewer_proof_at", self.latest_reviewer_proof_at),
        )
        object.__setattr__(
            self,
            "reviewer_proof_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "reviewer_proof_age_seconds",
                self.reviewer_proof_age_seconds,
            ),
        )
        _require_member(
            "latest_response_status",
            self.latest_response_status,
            SOURCE_RESPONSE_STATUSES,
        )
        object.__setattr__(
            self,
            "repeated_unresolved_family_count",
            _normalize_nonnegative_count(
                "repeated_unresolved_family_count",
                self.repeated_unresolved_family_count,
            ),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        reject_unsafe_surface_fields(
            "team memory adjudication follow-up queue row",
            self,
        )
        require_paper_only_flags("TeamMemoryAdjudicationFollowupQueueRow", self)
        _validate_queue_row(self)


@dataclass(frozen=True)
class TeamMemoryAdjudicationFollowupQueueReport:
    generated_at: datetime
    config_version: str
    response_status: str
    source_row_count: Decimal
    row_count: Decimal
    missing_followup_count: Decimal
    stale_reviewer_proof_count: Decimal
    repeated_unresolved_family_count: Decimal
    pending_response_count: Decimal
    missing_response_count: Decimal
    normal_count: Decimal
    total_unresolved_disagreement_count: Decimal
    missing_followup_ratio: Decimal
    stale_reviewer_proof_ratio: Decimal
    repeated_unresolved_family_ratio: Decimal
    max_reviewer_proof_age_seconds: Decimal | None
    rows: tuple[TeamMemoryAdjudicationFollowupQueueRow, ...]
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
            "missing_followup_count",
            "stale_reviewer_proof_count",
            "repeated_unresolved_family_count",
            "pending_response_count",
            "missing_response_count",
            "normal_count",
            "total_unresolved_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "missing_followup_ratio",
            "stale_reviewer_proof_ratio",
            "repeated_unresolved_family_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_reviewer_proof_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "max_reviewer_proof_age_seconds",
                self.max_reviewer_proof_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_queue_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        reject_unsafe_surface_fields(
            "team memory adjudication follow-up queue report",
            self,
        )
        require_paper_only_flags("TeamMemoryAdjudicationFollowupQueueReport", self)
        _validate_report(self)


def build_team_memory_adjudication_followup_queue_report(
    rows: list[TeamMemoryAdjudicationFollowupRow]
    | tuple[TeamMemoryAdjudicationFollowupRow, ...],
    *,
    config: TeamMemoryAdjudicationFollowupQueueConfig,
    generated_at: datetime,
) -> TeamMemoryAdjudicationFollowupQueueReport:
    if type(config) is not TeamMemoryAdjudicationFollowupQueueConfig:
        raise ValueError("config must be a TeamMemoryAdjudicationFollowupQueueConfig")
    require_paper_only_flags("TeamMemoryAdjudicationFollowupQueueConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(rows)
    repeated_family_counts = _repeated_family_counts(
        source_rows,
        config.repeated_unresolved_family_threshold,
    )
    queue_rows = tuple(
        sorted(
            (
                _queue_row(
                    row,
                    config,
                    generated_at_utc,
                    repeated_family_counts.get(row.disagreement_family_id, ZERO_COUNT),
                )
                for row in source_rows
            ),
            key=_queue_row_sort_key,
        ),
    )
    _reject_future_times(queue_rows, generated_at_utc)
    reason_codes = _report_reason_codes(queue_rows, len(source_rows))

    return TeamMemoryAdjudicationFollowupQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        response_status=_report_status(reason_codes),
        source_row_count=_count(len(source_rows)),
        row_count=_count(len(queue_rows)),
        missing_followup_count=_status_count(queue_rows, "missing_adjudication_followup"),
        stale_reviewer_proof_count=_status_count(queue_rows, "stale_reviewer_proof"),
        repeated_unresolved_family_count=_repeated_unresolved_family_row_count(queue_rows),
        pending_response_count=_response_status_count(queue_rows, "pending"),
        missing_response_count=_response_status_count(queue_rows, "missing"),
        normal_count=_status_count(queue_rows, "normal_adjudication_followup"),
        total_unresolved_disagreement_count=sum(
            (row.unresolved_disagreement_count for row in queue_rows),
            ZERO_COUNT,
        ),
        missing_followup_ratio=_ratio(
            _status_count(queue_rows, "missing_adjudication_followup"),
            len(queue_rows),
        ),
        stale_reviewer_proof_ratio=_ratio(
            _status_count(queue_rows, "stale_reviewer_proof"),
            len(queue_rows),
        ),
        repeated_unresolved_family_ratio=_ratio(
            _repeated_unresolved_family_row_count(queue_rows),
            len(queue_rows),
        ),
        max_reviewer_proof_age_seconds=_max_optional_decimal(
            tuple(
                row.reviewer_proof_age_seconds
                for row in queue_rows
                if row.reviewer_proof_age_seconds is not None
            ),
        ),
        rows=queue_rows,
        reason_codes=reason_codes,
    )


def team_memory_adjudication_followup_queue_payload(
    report: TeamMemoryAdjudicationFollowupQueueReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemoryAdjudicationFollowupQueueReport:
        raise ValueError("report must be a TeamMemoryAdjudicationFollowupQueueReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("team memory adjudication follow-up queue report", report)
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("team memory adjudication follow-up queue payload", ready)
    return ready


def _normalize_source_rows(
    value: object,
) -> tuple[TeamMemoryAdjudicationFollowupRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(_coerce_source_row(row) for row in value)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        require_paper_only_flags("TeamMemoryAdjudicationFollowupRow", row)
        key = (row.team_id, row.category_id, row.disagreement_family_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by team, category, and disagreement family")
        seen_keys.add(key)
    return rows


def _coerce_source_row(value: object) -> TeamMemoryAdjudicationFollowupRow:
    if type(value) is TeamMemoryAdjudicationFollowupRow:
        return value
    if isinstance(value, Mapping):
        return TeamMemoryAdjudicationFollowupRow(
            team_id=value.get("team_id"),
            category_id=value.get("category_id"),
            disagreement_family_id=value.get("disagreement_family_id"),
            unresolved_disagreement_count=value.get("unresolved_disagreement_count"),
            latest_adjudicated_at=value.get("latest_adjudicated_at"),
            latest_reviewer_proof_at=value.get("latest_reviewer_proof_at"),
            latest_response_status=value.get("latest_response_status"),
            paper_only=value.get("paper_only", True),
            report_only=value.get("report_only", True),
            readonly=value.get("readonly", True),
        )
    raise ValueError("rows must contain TeamMemoryAdjudicationFollowupRow values")


def _repeated_family_counts(
    rows: tuple[TeamMemoryAdjudicationFollowupRow, ...],
    threshold: Decimal,
) -> dict[str, Decimal]:
    counts: dict[str, int] = {}
    for row in rows:
        if row.unresolved_disagreement_count > ZERO_COUNT:
            counts[row.disagreement_family_id] = counts.get(row.disagreement_family_id, 0) + 1
    return {
        family_id: _count(count)
        for family_id, count in counts.items()
        if _count(count) > ZERO_COUNT
    }


def _queue_row(
    row: TeamMemoryAdjudicationFollowupRow,
    config: TeamMemoryAdjudicationFollowupQueueConfig,
    generated_at: datetime,
    repeated_unresolved_family_count: Decimal,
) -> TeamMemoryAdjudicationFollowupQueueRow:
    reviewer_proof_age_seconds = _age_seconds(
        row.latest_reviewer_proof_at,
        generated_at,
        "latest_reviewer_proof_at",
    )
    status = _row_status(
        row,
        config,
        reviewer_proof_age_seconds,
        repeated_unresolved_family_count,
    )
    return TeamMemoryAdjudicationFollowupQueueRow(
        team_id=row.team_id,
        category_id=row.category_id,
        disagreement_family_id=row.disagreement_family_id,
        response_status=status,
        unresolved_disagreement_count=row.unresolved_disagreement_count,
        latest_adjudicated_at=row.latest_adjudicated_at,
        latest_reviewer_proof_at=row.latest_reviewer_proof_at,
        reviewer_proof_age_seconds=reviewer_proof_age_seconds,
        latest_response_status=row.latest_response_status,
        repeated_unresolved_family_count=repeated_unresolved_family_count,
        reason_codes=_row_reason_codes(
            status,
            row.latest_response_status,
        ),
    )


def _row_status(
    row: TeamMemoryAdjudicationFollowupRow,
    config: TeamMemoryAdjudicationFollowupQueueConfig,
    reviewer_proof_age_seconds: Decimal | None,
    repeated_unresolved_family_count: Decimal,
) -> str:
    if row.latest_adjudicated_at is None:
        return "missing_adjudication_followup"
    if (
        reviewer_proof_age_seconds is not None
        and reviewer_proof_age_seconds > config.stale_reviewer_proof_after_seconds
    ):
        return "stale_reviewer_proof"
    if repeated_unresolved_family_count >= config.repeated_unresolved_family_threshold:
        return "repeated_unresolved_disagreement_family"
    if row.latest_response_status == "pending":
        return "pending_adjudication_response"
    return "normal_adjudication_followup"


def _row_reason_codes(
    status: str,
    latest_response_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if status == "missing_adjudication_followup":
        codes.append("missing_adjudication_followup_present")
    elif status == "stale_reviewer_proof":
        codes.append("stale_reviewer_proof_present")
    elif status == "repeated_unresolved_disagreement_family":
        codes.append("repeated_unresolved_disagreement_family_present")
    elif status == "normal_adjudication_followup":
        codes.append("normal_adjudication_followup_observed")
    if latest_response_status == "pending":
        codes.append("pending_adjudication_response")
    if latest_response_status == "missing":
        codes.append("missing_adjudication_response")
    return tuple(code for code in REASON_CODES if code in codes)


def _report_reason_codes(
    rows: tuple[TeamMemoryAdjudicationFollowupQueueRow, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return ("no_team_memory_adjudication_followup_rows_supplied",)
    codes: list[str] = []
    for code in REASON_CODES[1:]:
        if code == "normal_adjudication_followup_observed":
            if any(row.response_status == "normal_adjudication_followup" for row in rows):
                codes.append(code)
            continue
        if any(code in row.reason_codes for row in rows):
            codes.append(code)
    return tuple(codes)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if (
        not reason_codes
        or reason_codes == ("no_team_memory_adjudication_followup_rows_supplied",)
    ):
        return "pass"
    if any(code in reason_codes for code in REASON_CODES[1:4]):
        return "blocked"
    if "pending_adjudication_response" in reason_codes:
        return "watch"
    return "pass"


def _queue_row_sort_key(
    row: TeamMemoryAdjudicationFollowupQueueRow,
) -> tuple[int, str, str, str]:
    return (
        ROW_STATUSES.index(row.response_status),
        row.team_id,
        row.category_id,
        row.disagreement_family_id,
    )


def _status_count(
    rows: tuple[TeamMemoryAdjudicationFollowupQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.response_status == status))


def _response_status_count(
    rows: tuple[TeamMemoryAdjudicationFollowupQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.latest_response_status == status))


def _repeated_unresolved_family_row_count(
    rows: tuple[TeamMemoryAdjudicationFollowupQueueRow, ...],
) -> Decimal:
    return _count(
        sum(1 for row in rows if row.repeated_unresolved_family_count > COUNT_QUANTUM),
    )


def _normalize_queue_rows(
    value: object,
) -> tuple[TeamMemoryAdjudicationFollowupQueueRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemoryAdjudicationFollowupQueueRow:
            raise ValueError(
                "rows must contain TeamMemoryAdjudicationFollowupQueueRow values",
            )
        require_paper_only_flags("TeamMemoryAdjudicationFollowupQueueRow", row)
        key = (row.team_id, row.category_id, row.disagreement_family_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by team, category, and disagreement family")
        seen_keys.add(key)
    return tuple(sorted(rows, key=_queue_row_sort_key))


def _validate_source_row(row: TeamMemoryAdjudicationFollowupRow) -> None:
    if row.latest_adjudicated_at is None and row.latest_reviewer_proof_at is not None:
        raise ValueError("latest_reviewer_proof_at requires latest_adjudicated_at")


def _validate_queue_row(row: TeamMemoryAdjudicationFollowupQueueRow) -> None:
    expected = _row_reason_codes(row.response_status, row.latest_response_status)
    if row.reason_codes != expected:
        raise ValueError("reason_codes must match response_status")
    if row.latest_adjudicated_at is None and row.latest_reviewer_proof_at is not None:
        raise ValueError("latest_reviewer_proof_at requires latest_adjudicated_at")
    if row.latest_reviewer_proof_at is None and row.reviewer_proof_age_seconds is not None:
        raise ValueError("reviewer_proof_age_seconds must be absent without reviewer proof")
    if row.latest_reviewer_proof_at is not None and row.reviewer_proof_age_seconds is None:
        raise ValueError("reviewer_proof_age_seconds is required with reviewer proof")
    if (
        row.response_status == "repeated_unresolved_disagreement_family"
        and row.repeated_unresolved_family_count <= ZERO_COUNT
    ):
        raise ValueError("repeated_unresolved_family_count is required for repeated families")


def _validate_report(report: TeamMemoryAdjudicationFollowupQueueReport) -> None:
    if report.source_row_count != report.row_count:
        raise ValueError("source_row_count must match row_count")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    expected_counts = {
        "missing_followup_count": _status_count(report.rows, "missing_adjudication_followup"),
        "stale_reviewer_proof_count": _status_count(report.rows, "stale_reviewer_proof"),
        "repeated_unresolved_family_count": _repeated_unresolved_family_row_count(
            report.rows,
        ),
        "pending_response_count": _response_status_count(report.rows, "pending"),
        "missing_response_count": _response_status_count(report.rows, "missing"),
        "normal_count": _status_count(report.rows, "normal_adjudication_followup"),
        "total_unresolved_disagreement_count": sum(
            (row.unresolved_disagreement_count for row in report.rows),
            ZERO_COUNT,
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.missing_followup_ratio != _ratio(
        report.missing_followup_count,
        len(report.rows),
    ):
        raise ValueError("missing_followup_ratio must match rows")
    if report.stale_reviewer_proof_ratio != _ratio(
        report.stale_reviewer_proof_count,
        len(report.rows),
    ):
        raise ValueError("stale_reviewer_proof_ratio must match rows")
    if report.repeated_unresolved_family_ratio != _ratio(
        _repeated_unresolved_family_row_count(report.rows),
        len(report.rows),
    ):
        raise ValueError("repeated_unresolved_family_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.source_row_count)):
        raise ValueError("reason_codes must match rows")
    if report.response_status != _report_status(report.reason_codes):
        raise ValueError("response_status must match reason_codes")
    if report.max_reviewer_proof_age_seconds != _max_optional_decimal(
        tuple(
            row.reviewer_proof_age_seconds
            for row in report.rows
            if row.reviewer_proof_age_seconds is not None
        ),
    ):
        raise ValueError("max_reviewer_proof_age_seconds must match rows")


def _reject_future_times(
    rows: tuple[TeamMemoryAdjudicationFollowupQueueRow, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.latest_adjudicated_at is not None and row.latest_adjudicated_at > generated_at:
            raise ValueError("latest_adjudicated_at must not be in the future")
        if (
            row.latest_reviewer_proof_at is not None
            and row.latest_reviewer_proof_at > generated_at
        ):
            raise ValueError("latest_reviewer_proof_at must not be in the future")


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


def _age_seconds(
    value: datetime | None,
    generated_at: datetime,
    field_name: str,
) -> Decimal | None:
    if value is None:
        return None
    if value > generated_at:
        raise ValueError(f"{field_name} must not be in the future")
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


def _ratio(numerator: Decimal, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / Decimal(denominator)).quantize(RATIO_QUANTUM)


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


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > Decimal("1").quantize(RATIO_QUANTUM):
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

"""Pure in-memory team memory recency decay readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_TEAM_MEMORY_RECENCY_DECAY_READINESS_CONFIG_VERSION = (
    "team-memory-recency-decay-readiness-v0"
)

NO_OBSERVATIONS_REASON = "team_memory_recency_decay_no_observations"
BLOCK_MEMORY_STALE_REASON = "team_memory_recency_decay_block_memory_stale"
BLOCK_LOW_CALIBRATION_REASON = (
    "team_memory_recency_decay_block_low_calibration_samples"
)
BLOCK_ERROR_RATE_REASON = "team_memory_recency_decay_block_error_rate"
BLOCK_SOURCE_FEEDBACK_STALE_REASON = (
    "team_memory_recency_decay_block_source_feedback_stale"
)
THROTTLE_MEMORY_AGING_REASON = "team_memory_recency_decay_throttle_memory_aging"
THROTTLE_ERROR_RATE_REASON = "team_memory_recency_decay_throttle_error_rate"
THROTTLE_SOURCE_FEEDBACK_AGING_REASON = (
    "team_memory_recency_decay_throttle_source_feedback_aging"
)
ALLOW_CURRENT_REASON = "team_memory_recency_decay_allow_current"

REASON_CODES = (
    NO_OBSERVATIONS_REASON,
    BLOCK_MEMORY_STALE_REASON,
    BLOCK_LOW_CALIBRATION_REASON,
    BLOCK_ERROR_RATE_REASON,
    BLOCK_SOURCE_FEEDBACK_STALE_REASON,
    THROTTLE_MEMORY_AGING_REASON,
    THROTTLE_ERROR_RATE_REASON,
    THROTTLE_SOURCE_FEEDBACK_AGING_REASON,
    ALLOW_CURRENT_REASON,
)
BLOCK_REASONS = frozenset(
    (
        NO_OBSERVATIONS_REASON,
        BLOCK_MEMORY_STALE_REASON,
        BLOCK_LOW_CALIBRATION_REASON,
        BLOCK_ERROR_RATE_REASON,
        BLOCK_SOURCE_FEEDBACK_STALE_REASON,
    ),
)
THROTTLE_REASONS = frozenset(
    (
        THROTTLE_MEMORY_AGING_REASON,
        THROTTLE_ERROR_RATE_REASON,
        THROTTLE_SOURCE_FEEDBACK_AGING_REASON,
    ),
)
MEMORY_RECENCY_STATUSES = ("allow", "throttle", "block")
STATUS_RANK = {"block": 0, "throttle": 1, "allow": 2}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("tr", "ade"),
        _join_parts("bro", "ker"),
        _join_parts("cred", "ential"),
        _join_parts("sec", "ret"),
        _join_parts("private", "_", "key"),
        _join_parts("bal", "ance"),
        _join_parts("acc", "ount"),
    ),
)


@dataclass(frozen=True)
class TeamMemoryRecencyDecayReadinessConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_RECENCY_DECAY_READINESS_CONFIG_VERSION
    allow_memory_age_days: Decimal = Decimal("7.000000")
    block_memory_age_days: Decimal = Decimal("30.000000")
    min_calibration_sample_count: Decimal = Decimal("20.000000")
    block_recent_error_rate: Decimal = Decimal("0.250000")
    throttle_recent_error_rate: Decimal = Decimal("0.100000")
    max_source_feedback_age_days: Decimal = Decimal("14.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "allow_memory_age_days",
            _require_nonnegative_decimal(
                "allow_memory_age_days",
                self.allow_memory_age_days,
            ),
        )
        object.__setattr__(
            self,
            "block_memory_age_days",
            _require_positive_decimal(
                "block_memory_age_days",
                self.block_memory_age_days,
            ),
        )
        object.__setattr__(
            self,
            "min_calibration_sample_count",
            _require_nonnegative_decimal(
                "min_calibration_sample_count",
                self.min_calibration_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "block_recent_error_rate",
            _require_ratio_decimal(
                "block_recent_error_rate",
                self.block_recent_error_rate,
            ),
        )
        object.__setattr__(
            self,
            "throttle_recent_error_rate",
            _require_ratio_decimal(
                "throttle_recent_error_rate",
                self.throttle_recent_error_rate,
            ),
        )
        object.__setattr__(
            self,
            "max_source_feedback_age_days",
            _require_positive_decimal(
                "max_source_feedback_age_days",
                self.max_source_feedback_age_days,
            ),
        )
        if self.allow_memory_age_days > self.block_memory_age_days:
            raise ValueError("allow_memory_age_days must not exceed block threshold")
        if self.throttle_recent_error_rate > self.block_recent_error_rate:
            raise ValueError("throttle_recent_error_rate must not exceed block threshold")
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class TeamMemoryRecencyDecayReadinessInputRow:
    team_id: str
    category_id: str
    memory_age_days: Decimal
    calibration_sample_count: Decimal
    recent_error_rate: Decimal
    source_feedback_age_days: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _require_public_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            _require_public_string("category_id", self.category_id),
        )
        for field_name in (
            "memory_age_days",
            "calibration_sample_count",
            "source_feedback_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recent_error_rate",
            _require_ratio_decimal("recent_error_rate", self.recent_error_rate),
        )
        require_paper_only_flags("input row", self)


@dataclass(frozen=True)
class TeamMemoryRecencyDecayReadinessRow:
    team_id: str
    category_id: str
    memory_recency_status: str
    memory_age_days: Decimal
    calibration_sample_count: Decimal
    recent_error_rate: Decimal
    source_feedback_age_days: Decimal
    manual_follow_up: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _require_public_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            _require_public_string("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "memory_recency_status",
            _require_memory_recency_status(
                "memory_recency_status",
                self.memory_recency_status,
            ),
        )
        for field_name in (
            "memory_age_days",
            "calibration_sample_count",
            "source_feedback_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recent_error_rate",
            _require_ratio_decimal("recent_error_rate", self.recent_error_rate),
        )
        if type(self.manual_follow_up) is not bool:
            raise ValueError("manual_follow_up must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class TeamMemoryRecencyDecayReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        require_paper_only_flags("reason count", self)


@dataclass(frozen=True)
class TeamMemoryRecencyDecayReadinessReport:
    config_version: str
    memory_recency_status: str
    team_count: Decimal
    allow_count: Decimal
    throttle_count: Decimal
    block_count: Decimal
    manual_follow_up_count: Decimal
    max_memory_age_days: Decimal
    max_recent_error_rate: Decimal
    max_source_feedback_age_days: Decimal
    rows: tuple[TeamMemoryRecencyDecayReadinessRow, ...]
    reason_code_counts: tuple[TeamMemoryRecencyDecayReadinessReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "memory_recency_status",
            _require_memory_recency_status(
                "memory_recency_status",
                self.memory_recency_status,
            ),
        )
        for field_name in (
            "team_count",
            "allow_count",
            "throttle_count",
            "block_count",
            "manual_follow_up_count",
            "max_memory_age_days",
            "max_source_feedback_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_recent_error_rate",
            _require_ratio_decimal("max_recent_error_rate", self.max_recent_error_rate),
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
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return team_memory_recency_decay_readiness_report_payload(self)


def build_team_memory_recency_decay_readiness_report(
    input_rows: list[TeamMemoryRecencyDecayReadinessInputRow]
    | tuple[TeamMemoryRecencyDecayReadinessInputRow, ...],
    *,
    config: TeamMemoryRecencyDecayReadinessConfig,
) -> TeamMemoryRecencyDecayReadinessReport:
    if type(config) is not TeamMemoryRecencyDecayReadinessConfig:
        raise ValueError("config must be a TeamMemoryRecencyDecayReadinessConfig")
    require_paper_only_flags("config", config)
    rows = _normalize_input_rows(input_rows)
    report_rows = tuple(
        sorted(
            (_build_row(row, config=config) for row in rows),
            key=lambda row: (
                STATUS_RANK[row.memory_recency_status],
                row.category_id,
                row.team_id,
            ),
        ),
    )
    reason_codes = _report_reason_codes(report_rows)
    return TeamMemoryRecencyDecayReadinessReport(
        config_version=config.config_version,
        memory_recency_status=_status_from_reason_codes(reason_codes),
        team_count=_decimal_count(len({(row.team_id, row.category_id) for row in rows})),
        allow_count=_status_count(report_rows, "allow"),
        throttle_count=_status_count(report_rows, "throttle"),
        block_count=_status_count(report_rows, "block"),
        manual_follow_up_count=_decimal_count(
            sum(row.manual_follow_up for row in report_rows),
        ),
        max_memory_age_days=max(
            (row.memory_age_days for row in report_rows),
            default=ZERO,
        ),
        max_recent_error_rate=max(
            (row.recent_error_rate for row in report_rows),
            default=ZERO,
        ),
        max_source_feedback_age_days=max(
            (row.source_feedback_age_days for row in report_rows),
            default=ZERO,
        ),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows, reason_codes),
        reason_codes=reason_codes,
    )


def team_memory_recency_decay_readiness_report_payload(
    report: TeamMemoryRecencyDecayReadinessReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemoryRecencyDecayReadinessReport:
        raise ValueError("report must be a TeamMemoryRecencyDecayReadinessReport")
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields(
        "team_memory_recency_decay_readiness_report",
        payload,
    )
    return payload


def _build_row(
    row: TeamMemoryRecencyDecayReadinessInputRow,
    *,
    config: TeamMemoryRecencyDecayReadinessConfig,
) -> TeamMemoryRecencyDecayReadinessRow:
    reason_codes = _row_reason_codes(row, config=config)
    status = _status_from_reason_codes(reason_codes)
    return TeamMemoryRecencyDecayReadinessRow(
        team_id=row.team_id,
        category_id=row.category_id,
        memory_recency_status=status,
        memory_age_days=row.memory_age_days,
        calibration_sample_count=row.calibration_sample_count,
        recent_error_rate=row.recent_error_rate,
        source_feedback_age_days=row.source_feedback_age_days,
        manual_follow_up=status != "allow",
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: TeamMemoryRecencyDecayReadinessInputRow,
    *,
    config: TeamMemoryRecencyDecayReadinessConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.memory_age_days > config.block_memory_age_days:
        reasons.append(BLOCK_MEMORY_STALE_REASON)
    elif row.memory_age_days > config.allow_memory_age_days:
        reasons.append(THROTTLE_MEMORY_AGING_REASON)

    if row.calibration_sample_count < config.min_calibration_sample_count:
        reasons.append(BLOCK_LOW_CALIBRATION_REASON)

    if row.recent_error_rate >= config.block_recent_error_rate:
        reasons.append(BLOCK_ERROR_RATE_REASON)
    elif row.recent_error_rate >= config.throttle_recent_error_rate:
        reasons.append(THROTTLE_ERROR_RATE_REASON)

    feedback_block_threshold = config.max_source_feedback_age_days * TWO
    if row.source_feedback_age_days > feedback_block_threshold:
        reasons.append(BLOCK_SOURCE_FEEDBACK_STALE_REASON)
    elif row.source_feedback_age_days > config.max_source_feedback_age_days:
        reasons.append(THROTTLE_SOURCE_FEEDBACK_AGING_REASON)

    if not reasons:
        reasons.append(ALLOW_CURRENT_REASON)
    return _normalize_reason_codes(tuple(reasons))


def _normalize_input_rows(
    value: object,
) -> tuple[TeamMemoryRecencyDecayReadinessInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemoryRecencyDecayReadinessInputRow:
            raise ValueError(
                "input rows must contain TeamMemoryRecencyDecayReadinessInputRow",
            )
        require_paper_only_flags("input row", row)
        key = (row.team_id, row.category_id)
        if key in seen:
            raise ValueError("team_id and category_id pairs must be unique")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.category_id, row.team_id)))


def _status_count(
    rows: tuple[TeamMemoryRecencyDecayReadinessRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(row.memory_recency_status == status for row in rows))


def _report_reason_codes(
    rows: tuple[TeamMemoryRecencyDecayReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)


def _reason_code_counts(
    rows: tuple[TeamMemoryRecencyDecayReadinessRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[TeamMemoryRecencyDecayReadinessReasonCodeCount, ...]:
    if reason_codes == (NO_OBSERVATIONS_REASON,):
        return (
            TeamMemoryRecencyDecayReadinessReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=ONE,
            ),
        )
    counts: list[TeamMemoryRecencyDecayReadinessReasonCodeCount] = []
    for reason_code in reason_codes:
        count = _decimal_count(sum(reason_code in row.reason_codes for row in rows))
        if count > ZERO:
            counts.append(
                TeamMemoryRecencyDecayReadinessReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in THROTTLE_REASONS for reason_code in reason_codes):
        return "throttle"
    return "allow"


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


def _require_memory_recency_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MEMORY_RECENCY_STATUSES:
        raise ValueError(f"{field_name} must be a memory recency status")
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
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)


def _normalize_rows(value: object) -> tuple[TeamMemoryRecencyDecayReadinessRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamMemoryRecencyDecayReadinessRow:
            raise ValueError("rows must contain TeamMemoryRecencyDecayReadinessRow")
        require_paper_only_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[TeamMemoryRecencyDecayReadinessReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    for count in counts:
        if type(count) is not TeamMemoryRecencyDecayReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain TeamMemoryRecencyDecayReadinessReasonCodeCount",
            )
        require_paper_only_flags("reason count", count)
    return counts


def _validate_row(row: TeamMemoryRecencyDecayReadinessRow) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.memory_recency_status != expected_status:
        raise ValueError("memory_recency_status must match reason_codes")
    if row.manual_follow_up is not (row.memory_recency_status != "allow"):
        raise ValueError("manual_follow_up must match memory_recency_status")


def _validate_report(report: TeamMemoryRecencyDecayReadinessReport) -> None:
    row_count = _decimal_count(len(report.rows))
    if report.team_count != row_count:
        raise ValueError("team_count must match rows")
    if report.allow_count != _status_count(report.rows, "allow"):
        raise ValueError("allow_count must match rows")
    if report.throttle_count != _status_count(report.rows, "throttle"):
        raise ValueError("throttle_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_follow_up_count = _decimal_count(
        sum(row.manual_follow_up for row in report.rows),
    )
    if report.manual_follow_up_count != expected_follow_up_count:
        raise ValueError("manual_follow_up_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.memory_recency_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("memory_recency_status must match reason_codes")


__all__ = (
    "DEFAULT_TEAM_MEMORY_RECENCY_DECAY_READINESS_CONFIG_VERSION",
    "TeamMemoryRecencyDecayReadinessConfig",
    "TeamMemoryRecencyDecayReadinessInputRow",
    "TeamMemoryRecencyDecayReadinessReasonCodeCount",
    "TeamMemoryRecencyDecayReadinessReport",
    "TeamMemoryRecencyDecayReadinessRow",
    "build_team_memory_recency_decay_readiness_report",
    "team_memory_recency_decay_readiness_report_payload",
)

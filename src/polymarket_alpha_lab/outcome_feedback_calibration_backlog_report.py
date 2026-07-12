"""Read-only outcome calibration learning backlog report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_OUTCOME_FEEDBACK_CALIBRATION_BACKLOG_CONFIG_VERSION = (
    "outcome-feedback-calibration-backlog-v0"
)
OUTCOME_FEEDBACK_CALIBRATION_BACKLOG_PRIORITIES = ("low", "medium", "high")
REPORT_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SETTLED_SAMPLE_BLOCK_REASON = "outcome_feedback_calibration_settled_sample_block"
SETTLED_SAMPLE_WATCH_REASON = "outcome_feedback_calibration_settled_sample_watch"
PENDING_BACKLOG_BLOCK_REASON = "outcome_feedback_calibration_pending_backlog_block"
PENDING_BACKLOG_WATCH_REASON = "outcome_feedback_calibration_pending_backlog_watch"
CALIBRATION_ERROR_BLOCK_REASON = "outcome_feedback_calibration_error_block"
CALIBRATION_ERROR_WATCH_REASON = "outcome_feedback_calibration_error_watch"
SOURCE_ERROR_BLOCK_REASON = (
    "outcome_feedback_calibration_source_error_pattern_block"
)
SOURCE_ERROR_WATCH_REASON = (
    "outcome_feedback_calibration_source_error_pattern_watch"
)
TEAM_MEMORY_REASON = "outcome_feedback_calibration_team_memory_update_needed"
CLEAR_REASON = "outcome_feedback_calibration_backlog_clear"
EMPTY_REASON = "outcome_feedback_calibration_backlog_empty"
REASON_CODES = (
    SETTLED_SAMPLE_BLOCK_REASON,
    PENDING_BACKLOG_BLOCK_REASON,
    CALIBRATION_ERROR_BLOCK_REASON,
    SOURCE_ERROR_BLOCK_REASON,
    SETTLED_SAMPLE_WATCH_REASON,
    PENDING_BACKLOG_WATCH_REASON,
    CALIBRATION_ERROR_WATCH_REASON,
    SOURCE_ERROR_WATCH_REASON,
    TEAM_MEMORY_REASON,
    CLEAR_REASON,
    EMPTY_REASON,
)
BLOCK_REASONS = frozenset(
    (
        SETTLED_SAMPLE_BLOCK_REASON,
        PENDING_BACKLOG_BLOCK_REASON,
        CALIBRATION_ERROR_BLOCK_REASON,
        SOURCE_ERROR_BLOCK_REASON,
    ),
)

LOW_NEXT_STEP = "continue_readonly_outcome_monitoring"
MEDIUM_MEMORY_NEXT_STEP = "queue_team_memory_update_review"
MEDIUM_REVIEW_NEXT_STEP = "schedule_manual_calibration_backlog_review"
HIGH_NEXT_STEP = "open_manual_calibration_review_packet"

MIN_SETTLED_WATCH_COUNT = Decimal("30.000000")
MIN_SETTLED_BLOCK_COUNT = Decimal("10.000000")
PENDING_WATCH_COUNT = Decimal("3.000000")
PENDING_BLOCK_COUNT = Decimal("10.000000")
CALIBRATION_ERROR_WATCH = Decimal("0.070000")
CALIBRATION_ERROR_BLOCK = Decimal("0.150000")
SOURCE_ERROR_WATCH_COUNT = Decimal("1.000000")
SOURCE_ERROR_BLOCK_COUNT = Decimal("3.000000")

PUBLIC_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
HEX_RE = re.compile(r"^[0-9a-f]{64}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_KEY_FRAGMENTS = frozenset(
    (
        "market",
        "event",
        "slug",
        "question",
        "raw",
        "url",
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("ord", "er"),
        _join_parts("li", "ve"),
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("per", "sist"),
        _join_parts("data", "base"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("ord", "er"),
        _join_parts("li", "ve"),
    ),
)

__all__ = (
    "DEFAULT_OUTCOME_FEEDBACK_CALIBRATION_BACKLOG_CONFIG_VERSION",
    "OUTCOME_FEEDBACK_CALIBRATION_BACKLOG_PRIORITIES",
    "OutcomeFeedbackCalibrationBacklogInput",
    "OutcomeFeedbackCalibrationBacklogItem",
    "OutcomeFeedbackCalibrationBacklogReasonCodeCount",
    "OutcomeFeedbackCalibrationBacklogReport",
    "build_outcome_feedback_calibration_backlog_report",
    "outcome_feedback_calibration_backlog_report_digest",
    "outcome_feedback_calibration_backlog_report_payload",
    "validate_outcome_feedback_calibration_backlog_public_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class OutcomeFeedbackCalibrationBacklogInput(_FinalDataclass):
    feedback_key: str
    settled_count: Decimal
    pending_count: Decimal
    calibration_error: Decimal
    source_error_pattern_count: Decimal
    team_memory_update_needed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "feedback_key",
            _require_public_key("feedback_key", self.feedback_key),
        )
        for field_name in (
            "settled_count",
            "pending_count",
            "source_error_pattern_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error",
            _require_ratio("calibration_error", self.calibration_error),
        )
        if type(self.team_memory_update_needed) is not bool:
            raise ValueError("team_memory_update_needed must be a bool")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class OutcomeFeedbackCalibrationBacklogItem(_FinalDataclass):
    feedback_key: str
    settled_count: Decimal
    pending_count: Decimal
    calibration_error: Decimal
    source_error_pattern_count: Decimal
    team_memory_update_needed: bool
    backlog_priority: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "feedback_key",
            _require_public_key("feedback_key", self.feedback_key),
        )
        for field_name in (
            "settled_count",
            "pending_count",
            "source_error_pattern_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error",
            _require_ratio("calibration_error", self.calibration_error),
        )
        if type(self.team_memory_update_needed) is not bool:
            raise ValueError("team_memory_update_needed must be a bool")
        _require_member(
            "backlog_priority",
            self.backlog_priority,
            OUTCOME_FEEDBACK_CALIBRATION_BACKLOG_PRIORITIES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, allow_repeats=False),
        )
        _require_member(
            "manual_next_step",
            self.manual_next_step,
            (LOW_NEXT_STEP, MEDIUM_MEMORY_NEXT_STEP, MEDIUM_REVIEW_NEXT_STEP, HIGH_NEXT_STEP),
        )
        _validate_item(self)
        _require_hard_flags("backlog item", self)


@dataclass(frozen=True)
class OutcomeFeedbackCalibrationBacklogReasonCodeCount(_FinalDataclass):
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
            _require_positive_count("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class OutcomeFeedbackCalibrationBacklogReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    learning_backlog_count: Decimal
    low_priority_count: Decimal
    medium_priority_count: Decimal
    high_priority_count: Decimal
    total_settled_count: Decimal
    total_pending_count: Decimal
    max_calibration_error: Decimal
    max_source_error_pattern_count: Decimal
    team_memory_update_needed_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[OutcomeFeedbackCalibrationBacklogReasonCodeCount, ...]
    backlog_items: tuple[OutcomeFeedbackCalibrationBacklogItem, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_OUTCOME_FEEDBACK_CALIBRATION_BACKLOG_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "input_count",
            "learning_backlog_count",
            "low_priority_count",
            "medium_priority_count",
            "high_priority_count",
            "total_settled_count",
            "total_pending_count",
            "max_source_error_pattern_count",
            "team_memory_update_needed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_calibration_error",
            _require_ratio("max_calibration_error", self.max_calibration_error),
        )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, allow_repeats=True),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "backlog_items",
            _require_backlog_items(self.backlog_items),
        )
        _validate_report(self)
        _require_or_set_digest(self)
        _require_hard_flags("report", self)


def build_outcome_feedback_calibration_backlog_report(
    inputs: Iterable[OutcomeFeedbackCalibrationBacklogInput],
    *,
    generated_at: datetime,
) -> OutcomeFeedbackCalibrationBacklogReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    backlog_items = tuple(sorted((_item_from_input(row) for row in input_rows), key=_item_key))
    reason_codes = _report_reason_codes(backlog_items)
    return OutcomeFeedbackCalibrationBacklogReport(
        generated_at=generated_at_utc,
        config_version=DEFAULT_OUTCOME_FEEDBACK_CALIBRATION_BACKLOG_CONFIG_VERSION,
        input_count=_count(len(backlog_items)),
        learning_backlog_count=_count(
            sum(item.backlog_priority != "low" for item in backlog_items),
        ),
        low_priority_count=_count(
            sum(item.backlog_priority == "low" for item in backlog_items),
        ),
        medium_priority_count=_count(
            sum(item.backlog_priority == "medium" for item in backlog_items),
        ),
        high_priority_count=_count(
            sum(item.backlog_priority == "high" for item in backlog_items),
        ),
        total_settled_count=_sum_decimal(item.settled_count for item in backlog_items),
        total_pending_count=_sum_decimal(item.pending_count for item in backlog_items),
        max_calibration_error=_max_decimal(
            (item.calibration_error for item in backlog_items),
            ratio=True,
        ),
        max_source_error_pattern_count=_max_decimal(
            (item.source_error_pattern_count for item in backlog_items),
            ratio=False,
        ),
        team_memory_update_needed_count=_count(
            sum(item.team_memory_update_needed for item in backlog_items),
        ),
        report_status=_report_status(backlog_items),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        backlog_items=backlog_items,
    )


def outcome_feedback_calibration_backlog_report_digest(
    report: OutcomeFeedbackCalibrationBacklogReport,
) -> str:
    _require_report(report)
    _validate_report(report)
    return _digest_from_values(_report_values_without_digest(report))


def outcome_feedback_calibration_backlog_report_payload(
    report: OutcomeFeedbackCalibrationBacklogReport,
) -> dict[str, Any]:
    _require_report(report)
    _validate_report(report)
    expected_digest = outcome_feedback_calibration_backlog_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return validate_outcome_feedback_calibration_backlog_public_payload(payload)


def validate_outcome_feedback_calibration_backlog_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    normalized = _json_ready(payload)
    if type(normalized) is not dict:
        raise ValueError("payload must be a dict")
    _reject_public_numeric_values(normalized)
    _reject_unsafe_public_payload(normalized)
    _require_payload_flags(normalized)
    supplied_digest = normalized.get("derived_validation_digest")
    if type(supplied_digest) is not str or HEX_RE.fullmatch(supplied_digest) is None:
        raise ValueError("derived_validation_digest is required")
    if supplied_digest != _digest_from_payload(normalized):
        raise ValueError("derived_validation_digest does not match report payload")
    return normalized


def _normalize_inputs(
    inputs: Iterable[OutcomeFeedbackCalibrationBacklogInput],
) -> tuple[OutcomeFeedbackCalibrationBacklogInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    normalized: list[OutcomeFeedbackCalibrationBacklogInput] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not OutcomeFeedbackCalibrationBacklogInput:
            raise ValueError("inputs must contain OutcomeFeedbackCalibrationBacklogInput")
        _require_hard_flags("input", row)
        if row.feedback_key in seen:
            raise ValueError("inputs must contain unique feedback_key values")
        seen.add(row.feedback_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.feedback_key))


def _item_from_input(row: OutcomeFeedbackCalibrationBacklogInput) -> OutcomeFeedbackCalibrationBacklogItem:
    reason_codes = _reason_codes_for_values(
        settled_count=row.settled_count,
        pending_count=row.pending_count,
        calibration_error=row.calibration_error,
        source_error_pattern_count=row.source_error_pattern_count,
        team_memory_update_needed=row.team_memory_update_needed,
    )
    priority = _priority_for_reason_codes(reason_codes)
    return OutcomeFeedbackCalibrationBacklogItem(
        feedback_key=row.feedback_key,
        settled_count=row.settled_count,
        pending_count=row.pending_count,
        calibration_error=row.calibration_error,
        source_error_pattern_count=row.source_error_pattern_count,
        team_memory_update_needed=row.team_memory_update_needed,
        backlog_priority=priority,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(priority, row.team_memory_update_needed),
    )


def _reason_codes_for_values(
    *,
    settled_count: Decimal,
    pending_count: Decimal,
    calibration_error: Decimal,
    source_error_pattern_count: Decimal,
    team_memory_update_needed: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if settled_count < MIN_SETTLED_BLOCK_COUNT:
        reasons.append(SETTLED_SAMPLE_BLOCK_REASON)
    elif settled_count < MIN_SETTLED_WATCH_COUNT:
        reasons.append(SETTLED_SAMPLE_WATCH_REASON)
    if pending_count >= PENDING_BLOCK_COUNT:
        reasons.append(PENDING_BACKLOG_BLOCK_REASON)
    elif pending_count >= PENDING_WATCH_COUNT:
        reasons.append(PENDING_BACKLOG_WATCH_REASON)
    if calibration_error >= CALIBRATION_ERROR_BLOCK:
        reasons.append(CALIBRATION_ERROR_BLOCK_REASON)
    elif calibration_error >= CALIBRATION_ERROR_WATCH:
        reasons.append(CALIBRATION_ERROR_WATCH_REASON)
    if source_error_pattern_count >= SOURCE_ERROR_BLOCK_COUNT:
        reasons.append(SOURCE_ERROR_BLOCK_REASON)
    elif source_error_pattern_count >= SOURCE_ERROR_WATCH_COUNT:
        reasons.append(SOURCE_ERROR_WATCH_REASON)
    if team_memory_update_needed:
        reasons.append(TEAM_MEMORY_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _priority_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "high"
    if reason_codes != (CLEAR_REASON,):
        return "medium"
    return "low"


def _manual_next_step(priority: str, team_memory_update_needed: bool) -> str:
    if priority == "high":
        return HIGH_NEXT_STEP
    if priority == "medium" and team_memory_update_needed:
        return MEDIUM_MEMORY_NEXT_STEP
    if priority == "medium":
        return MEDIUM_REVIEW_NEXT_STEP
    return LOW_NEXT_STEP


def _item_key(item: OutcomeFeedbackCalibrationBacklogItem) -> tuple[Decimal, Decimal, Decimal, str]:
    priority_value = {"high": ZERO, "medium": ONE, "low": TWO}[item.backlog_priority]
    return (
        priority_value,
        -item.calibration_error,
        -item.pending_count,
        item.feedback_key,
    )


def _report_reason_codes(
    items: tuple[OutcomeFeedbackCalibrationBacklogItem, ...],
) -> tuple[str, ...]:
    if not items:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason_code
        for item in items
        if item.reason_codes != (CLEAR_REASON,)
        for reason_code in item.reason_codes
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[OutcomeFeedbackCalibrationBacklogReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    first_seen: list[str] = []
    for reason_code in reason_codes:
        if reason_code not in counts:
            counts[reason_code] = ZERO
            first_seen.append(reason_code)
        counts[reason_code] = _q(counts[reason_code] + ONE)
    return tuple(
        OutcomeFeedbackCalibrationBacklogReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in first_seen
    )


def _report_status(items: tuple[OutcomeFeedbackCalibrationBacklogItem, ...]) -> str:
    if any(item.backlog_priority == "high" for item in items):
        return "block"
    if any(item.backlog_priority == "medium" for item in items):
        return "watch"
    return "pass"


def _validate_item(item: OutcomeFeedbackCalibrationBacklogItem) -> None:
    expected_reasons = _reason_codes_for_values(
        settled_count=item.settled_count,
        pending_count=item.pending_count,
        calibration_error=item.calibration_error,
        source_error_pattern_count=item.source_error_pattern_count,
        team_memory_update_needed=item.team_memory_update_needed,
    )
    if item.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match calibration backlog inputs")
    expected_priority = _priority_for_reason_codes(item.reason_codes)
    if item.backlog_priority != expected_priority:
        raise ValueError("backlog_priority must match reason_codes")
    expected_next_step = _manual_next_step(
        item.backlog_priority,
        item.team_memory_update_needed,
    )
    if item.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match backlog_priority")


def _validate_report(report: OutcomeFeedbackCalibrationBacklogReport) -> None:
    items = report.backlog_items
    expected: dict[str, Decimal | str | tuple[str, ...]] = {
        "input_count": _count(len(items)),
        "learning_backlog_count": _count(
            sum(item.backlog_priority != "low" for item in items),
        ),
        "low_priority_count": _count(
            sum(item.backlog_priority == "low" for item in items),
        ),
        "medium_priority_count": _count(
            sum(item.backlog_priority == "medium" for item in items),
        ),
        "high_priority_count": _count(
            sum(item.backlog_priority == "high" for item in items),
        ),
        "total_settled_count": _sum_decimal(item.settled_count for item in items),
        "total_pending_count": _sum_decimal(item.pending_count for item in items),
        "max_calibration_error": _max_decimal(
            (item.calibration_error for item in items),
            ratio=True,
        ),
        "max_source_error_pattern_count": _max_decimal(
            (item.source_error_pattern_count for item in items),
            ratio=False,
        ),
        "team_memory_update_needed_count": _count(
            sum(item.team_memory_update_needed for item in items),
        ),
        "report_status": _report_status(items),
        "reason_codes": _report_reason_codes(items),
    }
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match backlog_items")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if tuple(sorted(items, key=_item_key)) != items:
        raise ValueError("backlog_items must be sorted by priority")


def _require_report(report: object) -> OutcomeFeedbackCalibrationBacklogReport:
    if type(report) is not OutcomeFeedbackCalibrationBacklogReport:
        raise ValueError("report must be an OutcomeFeedbackCalibrationBacklogReport")
    _require_hard_flags("report", report)
    return report


def _require_backlog_items(
    items: object,
) -> tuple[OutcomeFeedbackCalibrationBacklogItem, ...]:
    if not isinstance(items, tuple):
        raise ValueError("backlog_items must be a tuple")
    for item in items:
        if type(item) is not OutcomeFeedbackCalibrationBacklogItem:
            raise ValueError("backlog_items must contain OutcomeFeedbackCalibrationBacklogItem")
        _require_hard_flags("backlog item", item)
    return items


def _require_reason_code_counts(
    counts: object,
) -> tuple[OutcomeFeedbackCalibrationBacklogReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not OutcomeFeedbackCalibrationBacklogReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain OutcomeFeedbackCalibrationBacklogReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    return counts


def _require_payload_flags(payload: Mapping[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_member(field_name: str, value: str, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_public_key(field_name: str, value: object) -> str:
    if type(value) is not str or PUBLIC_KEY_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public key")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or REASON_CODE_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a reason code")
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} is not supported")
    return value


def _require_reason_codes(
    reason_codes: object,
    *,
    allow_repeats: bool,
) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple) or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized = tuple(_require_reason_code("reason_code", item) for item in reason_codes)
    if not allow_repeats and len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not repeat")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return _q(decimal_value)


def _require_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be a ratio")
    return _q(decimal_value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return _q(Decimal(str(value)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _q(total + value)
    return total


def _max_decimal(values: Iterable[Decimal], *, ratio: bool) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    result = max(collected)
    if ratio:
        return _require_ratio("max_decimal", result)
    return _require_nonnegative_count("max_decimal", result)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_or_set_digest(report: OutcomeFeedbackCalibrationBacklogReport) -> None:
    expected_digest = _digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
    elif report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    elif HEX_RE.fullmatch(report.derived_validation_digest) is None:
        raise ValueError("derived_validation_digest is required")


def _report_values_without_digest(
    report: OutcomeFeedbackCalibrationBacklogReport,
) -> dict[str, Any]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _digest_from_values(values: Mapping[str, Any]) -> str:
    normalized = _json_ready(values)
    encoded = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return sha256(encoded).hexdigest()


def _digest_from_payload(payload: Mapping[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _digest_from_values(unsigned)


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _reject_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload contains non-string key")
            _reject_unsafe_public_text(key)
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif type(value) is str:
        _reject_unsafe_public_text(value)


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload contains restricted text")

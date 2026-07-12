"""Pure specialist team learning-loop readiness report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_SPECIALIST_TEAM_LEARNING_LOOP_READINESS_CONFIG_VERSION = (
    "specialist-team-learning-loop-readiness-v0"
)
SPECIALIST_TEAM_LEARNING_LOOP_PRIORITY_BANDS = ("ready", "attention", "blocked")

ALLOWED_TEAM_LABELS = ("politics", "finance", "sports")
READY_BAND = "ready"
ATTENTION_BAND = "attention"
BLOCKED_BAND = "blocked"

RESOLVED_MARKET_SAMPLE_GAP = "resolved_market_sample_gap"
PENDING_MARKET_BACKLOG = "pending_market_backlog"
CALIBRATION_ERROR_BACKLOG = "calibration_error_backlog"
MEMORY_EVENT_GAP = "memory_event_gap"
STALE_LEARNING_REVIEW = "stale_learning_review"
SUPABASE_PERSISTENCE_NOT_READY = "supabase_persistence_not_ready"

ATTENTION_REASON_CODES = (
    RESOLVED_MARKET_SAMPLE_GAP,
    PENDING_MARKET_BACKLOG,
    CALIBRATION_ERROR_BACKLOG,
    MEMORY_EVENT_GAP,
    STALE_LEARNING_REVIEW,
)
BLOCKER_REASON_CODES = (SUPABASE_PERSISTENCE_NOT_READY,)

DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
SIX_PLACES = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_LEARNING_LOOP_READINESS_CONFIG_VERSION",
    "SPECIALIST_TEAM_LEARNING_LOOP_PRIORITY_BANDS",
    "SpecialistTeamLearningLoopReadinessConfig",
    "SpecialistTeamLearningLoopReadinessInput",
    "SpecialistTeamLearningLoopReadinessRow",
    "SpecialistTeamLearningLoopReadinessReport",
    "build_specialist_team_learning_loop_readiness_report",
    "specialist_team_learning_loop_readiness_report_payload",
)


@dataclass(frozen=True)
class SpecialistTeamLearningLoopReadinessConfig:
    config_version: str = DEFAULT_SPECIALIST_TEAM_LEARNING_LOOP_READINESS_CONFIG_VERSION
    min_resolved_market_count: Decimal = Decimal("10")
    max_pending_market_count: Decimal = Decimal("5")
    max_calibration_error_count: Decimal = Decimal("2")
    min_memory_event_count: Decimal = Decimal("12")
    max_last_review_age_seconds: Decimal = Decimal("604800")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamLearningLoopReadinessConfig:
            raise ValueError("config must be exactly SpecialistTeamLearningLoopReadinessConfig")
        _require_config_version(self.config_version)
        for field_name in (
            "min_resolved_market_count",
            "max_pending_market_count",
            "max_calibration_error_count",
            "min_memory_event_count",
            "max_last_review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("specialist team learning loop readiness config", self)


@dataclass(frozen=True)
class SpecialistTeamLearningLoopReadinessInput:
    team_label: str
    resolved_market_count: Decimal
    pending_market_count: Decimal
    calibration_error_count: Decimal
    memory_event_count: Decimal
    last_review_age_seconds: Decimal
    supabase_persistence_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamLearningLoopReadinessInput:
            raise ValueError("input must be exactly SpecialistTeamLearningLoopReadinessInput")
        _require_team_label(self.team_label)
        for field_name in (
            "resolved_market_count",
            "pending_market_count",
            "calibration_error_count",
            "memory_event_count",
            "last_review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_bool("supabase_persistence_ready", self.supabase_persistence_ready)
        require_paper_only_flags("specialist team learning loop readiness input", self)


@dataclass(frozen=True)
class SpecialistTeamLearningLoopReadinessRow:
    team_label: str
    resolved_market_count: Decimal
    pending_market_count: Decimal
    calibration_error_count: Decimal
    memory_event_count: Decimal
    last_review_age_seconds: Decimal
    supabase_persistence_ready: bool
    ready_ratio: Decimal
    learning_loop_ready: bool
    priority_band: str
    blocker_reasons: tuple[str, ...]
    attention_reasons: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamLearningLoopReadinessRow:
            raise ValueError("row must be exactly SpecialistTeamLearningLoopReadinessRow")
        _require_team_label(self.team_label)
        for field_name in (
            "resolved_market_count",
            "pending_market_count",
            "calibration_error_count",
            "memory_event_count",
            "last_review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_bool("supabase_persistence_ready", self.supabase_persistence_ready)
        object.__setattr__(self, "ready_ratio", _normalize_ratio("ready_ratio", self.ready_ratio))
        _require_bool("learning_loop_ready", self.learning_loop_ready)
        _require_band("priority_band", self.priority_band)
        object.__setattr__(
            self,
            "blocker_reasons",
            _normalize_reasons("blocker_reasons", self.blocker_reasons, BLOCKER_REASON_CODES),
        )
        object.__setattr__(
            self,
            "attention_reasons",
            _normalize_reasons("attention_reasons", self.attention_reasons, ATTENTION_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("specialist team learning loop readiness row", self)


@dataclass(frozen=True)
class SpecialistTeamLearningLoopReadinessReport:
    config_version: str
    team_count: Decimal
    ready_team_count: Decimal
    attention_team_count: Decimal
    blocked_team_count: Decimal
    aggregate_ready_ratio: Decimal
    learning_loop_ready: bool
    priority_band: str
    blocker_reasons: tuple[str, ...]
    attention_reasons: tuple[str, ...]
    readiness_rows: tuple[SpecialistTeamLearningLoopReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamLearningLoopReadinessReport:
            raise ValueError("report must be exactly SpecialistTeamLearningLoopReadinessReport")
        _require_config_version(self.config_version)
        for field_name in (
            "team_count",
            "ready_team_count",
            "attention_team_count",
            "blocked_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "aggregate_ready_ratio",
            _normalize_ratio("aggregate_ready_ratio", self.aggregate_ready_ratio),
        )
        _require_bool("learning_loop_ready", self.learning_loop_ready)
        _require_band("priority_band", self.priority_band)
        object.__setattr__(
            self,
            "blocker_reasons",
            _normalize_reasons("blocker_reasons", self.blocker_reasons, BLOCKER_REASON_CODES),
        )
        object.__setattr__(
            self,
            "attention_reasons",
            _normalize_reasons("attention_reasons", self.attention_reasons, ATTENTION_REASON_CODES),
        )
        object.__setattr__(self, "readiness_rows", _normalize_rows(self.readiness_rows))
        _validate_report(self)
        require_paper_only_flags("specialist team learning loop readiness report", self)


def build_specialist_team_learning_loop_readiness_report(
    inputs: Iterable[SpecialistTeamLearningLoopReadinessInput],
    *,
    config: SpecialistTeamLearningLoopReadinessConfig,
) -> SpecialistTeamLearningLoopReadinessReport:
    if type(config) is not SpecialistTeamLearningLoopReadinessConfig:
        raise ValueError("config must be a SpecialistTeamLearningLoopReadinessConfig")
    require_paper_only_flags("config", config)
    input_rows = _normalize_inputs(inputs)
    readiness_rows = tuple(
        sorted(
            (_readiness_row(row, config) for row in input_rows),
            key=_row_sort_key,
        ),
    )
    report_parts = dict(
        config_version=config.config_version,
        team_count=_count(len(readiness_rows)),
        ready_team_count=_count(sum(1 for row in readiness_rows if row.priority_band == READY_BAND)),
        attention_team_count=_count(
            sum(1 for row in readiness_rows if row.priority_band == ATTENTION_BAND),
        ),
        blocked_team_count=_count(
            sum(1 for row in readiness_rows if row.priority_band == BLOCKED_BAND),
        ),
        aggregate_ready_ratio=_aggregate_ready_ratio(readiness_rows),
        learning_loop_ready=all(row.learning_loop_ready for row in readiness_rows),
        priority_band=_report_band(readiness_rows),
        blocker_reasons=_report_blocker_reasons(readiness_rows),
        attention_reasons=_report_attention_reasons(readiness_rows),
        readiness_rows=readiness_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return SpecialistTeamLearningLoopReadinessReport(**report_parts)


def specialist_team_learning_loop_readiness_report_payload(
    report: SpecialistTeamLearningLoopReadinessReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamLearningLoopReadinessReport:
        raise ValueError("report must be a SpecialistTeamLearningLoopReadinessReport")
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


def _readiness_row(
    row: SpecialistTeamLearningLoopReadinessInput,
    config: SpecialistTeamLearningLoopReadinessConfig,
) -> SpecialistTeamLearningLoopReadinessRow:
    blocker_reasons = _blocker_reasons(row)
    attention_reasons = _attention_reasons(row, config)
    priority_band = _priority_band(blocker_reasons, attention_reasons)
    row_parts = dict(
        team_label=row.team_label,
        resolved_market_count=row.resolved_market_count,
        pending_market_count=row.pending_market_count,
        calibration_error_count=row.calibration_error_count,
        memory_event_count=row.memory_event_count,
        last_review_age_seconds=row.last_review_age_seconds,
        supabase_persistence_ready=row.supabase_persistence_ready,
        ready_ratio=_ready_ratio(row, config),
        learning_loop_ready=priority_band == READY_BAND,
        priority_band=priority_band,
        blocker_reasons=blocker_reasons,
        attention_reasons=attention_reasons,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return SpecialistTeamLearningLoopReadinessRow(**row_parts)


def _ready_ratio(
    row: SpecialistTeamLearningLoopReadinessInput | SpecialistTeamLearningLoopReadinessRow,
    config: SpecialistTeamLearningLoopReadinessConfig,
) -> Decimal:
    blocker_penalty = Decimal(len(_blocker_reasons(row))) * Decimal("0.200000")
    attention_penalty = Decimal(len(_attention_reasons(row, config))) * Decimal("0.125000")
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ready_ratio", ONE_RATIO - blocker_penalty - attention_penalty)


def _blocker_reasons(
    row: SpecialistTeamLearningLoopReadinessInput | SpecialistTeamLearningLoopReadinessRow,
) -> tuple[str, ...]:
    if row.supabase_persistence_ready:
        return ()
    return (SUPABASE_PERSISTENCE_NOT_READY,)


def _attention_reasons(
    row: SpecialistTeamLearningLoopReadinessInput | SpecialistTeamLearningLoopReadinessRow,
    config: SpecialistTeamLearningLoopReadinessConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.resolved_market_count < config.min_resolved_market_count:
        reasons.append(RESOLVED_MARKET_SAMPLE_GAP)
    if row.pending_market_count > config.max_pending_market_count:
        reasons.append(PENDING_MARKET_BACKLOG)
    if row.calibration_error_count > config.max_calibration_error_count:
        reasons.append(CALIBRATION_ERROR_BACKLOG)
    if row.memory_event_count < config.min_memory_event_count:
        reasons.append(MEMORY_EVENT_GAP)
    if row.last_review_age_seconds > config.max_last_review_age_seconds:
        reasons.append(STALE_LEARNING_REVIEW)
    return tuple(reasons)


def _priority_band(blockers: tuple[str, ...], attention: tuple[str, ...]) -> str:
    if blockers:
        return BLOCKED_BAND
    if attention:
        return ATTENTION_BAND
    return READY_BAND


def _report_band(rows: tuple[SpecialistTeamLearningLoopReadinessRow, ...]) -> str:
    if any(row.priority_band == BLOCKED_BAND for row in rows):
        return BLOCKED_BAND
    if any(row.priority_band == ATTENTION_BAND for row in rows):
        return ATTENTION_BAND
    return READY_BAND


def _report_blocker_reasons(
    rows: tuple[SpecialistTeamLearningLoopReadinessRow, ...],
) -> tuple[str, ...]:
    requested = {reason for row in rows for reason in row.blocker_reasons}
    return tuple(reason for reason in BLOCKER_REASON_CODES if reason in requested)


def _report_attention_reasons(
    rows: tuple[SpecialistTeamLearningLoopReadinessRow, ...],
) -> tuple[str, ...]:
    requested = {reason for row in rows for reason in row.attention_reasons}
    return tuple(reason for reason in ATTENTION_REASON_CODES if reason in requested)


def _aggregate_ready_ratio(rows: tuple[SpecialistTeamLearningLoopReadinessRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    ready_count = Decimal(sum(1 for row in rows if row.learning_loop_ready))
    return _safe_ratio(ready_count, Decimal(len(rows)))


def _row_sort_key(row: SpecialistTeamLearningLoopReadinessRow) -> tuple[int, Decimal, str]:
    band_rank = {BLOCKED_BAND: 0, ATTENTION_BAND: 1, READY_BAND: 2}
    return (band_rank[row.priority_band], row.ready_ratio, row.team_label)


def _normalize_inputs(
    inputs: Iterable[SpecialistTeamLearningLoopReadinessInput],
) -> tuple[SpecialistTeamLearningLoopReadinessInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not SpecialistTeamLearningLoopReadinessInput:
            raise ValueError(
                "inputs must contain SpecialistTeamLearningLoopReadinessInput values",
            )
        require_paper_only_flags("input", row)
        if row.team_label in seen:
            raise ValueError("duplicate specialist team")
        seen.add(row.team_label)
    return rows


def _normalize_rows(
    values: Iterable[SpecialistTeamLearningLoopReadinessRow],
) -> tuple[SpecialistTeamLearningLoopReadinessRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("readiness_rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("readiness_rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not SpecialistTeamLearningLoopReadinessRow:
            raise ValueError(
                "readiness_rows must contain SpecialistTeamLearningLoopReadinessRow values",
            )
        require_paper_only_flags("row", row)
        if row.team_label in seen:
            raise ValueError("readiness_rows must be unique")
        seen.add(row.team_label)
    return rows


def _validate_row(row: SpecialistTeamLearningLoopReadinessRow) -> None:
    config = SpecialistTeamLearningLoopReadinessConfig()
    expected_blockers = _blocker_reasons(row)
    expected_attention = _attention_reasons(row, config)
    expected_band = _priority_band(expected_blockers, expected_attention)
    if row.ready_ratio != _ready_ratio(row, config):
        raise ValueError("ready_ratio must match readiness components")
    if row.blocker_reasons != expected_blockers:
        raise ValueError("blocker_reasons must match readiness components")
    if row.attention_reasons != expected_attention:
        raise ValueError("attention_reasons must match readiness components")
    if row.priority_band != expected_band:
        raise ValueError("priority_band must match readiness components")
    if row.learning_loop_ready != (expected_band == READY_BAND):
        raise ValueError("learning_loop_ready must match readiness components")


def _validate_report(report: SpecialistTeamLearningLoopReadinessReport) -> None:
    rows = report.readiness_rows
    if report.team_count != _count(len(rows)):
        raise ValueError("team_count must match readiness_rows")
    if report.ready_team_count != _count(sum(1 for row in rows if row.priority_band == READY_BAND)):
        raise ValueError("ready_team_count must match readiness_rows")
    if report.attention_team_count != _count(
        sum(1 for row in rows if row.priority_band == ATTENTION_BAND),
    ):
        raise ValueError("attention_team_count must match readiness_rows")
    if report.blocked_team_count != _count(
        sum(1 for row in rows if row.priority_band == BLOCKED_BAND),
    ):
        raise ValueError("blocked_team_count must match readiness_rows")
    if report.aggregate_ready_ratio != _aggregate_ready_ratio(rows):
        raise ValueError("aggregate_ready_ratio must match readiness_rows")
    if report.learning_loop_ready != all(row.learning_loop_ready for row in rows):
        raise ValueError("learning_loop_ready must match readiness_rows")
    if report.priority_band != _report_band(rows):
        raise ValueError("priority_band must match readiness_rows")
    if report.blocker_reasons != _report_blocker_reasons(rows):
        raise ValueError("blocker_reasons must match readiness_rows")
    if report.attention_reasons != _report_attention_reasons(rows):
        raise ValueError("attention_reasons must match readiness_rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("readiness_rows must use stable sort")


def _normalize_reasons(
    field_name: str,
    value: Iterable[str],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reasons = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if len(set(reasons)) != len(reasons):
        raise ValueError(f"{field_name} must be unique")
    allowed_ranks = {reason: index for index, reason in enumerate(allowed_values)}
    for reason in reasons:
        if type(reason) is not str or reason not in allowed_ranks:
            raise ValueError(f"{field_name} must contain known values")
    expected = tuple(reason for reason in allowed_values if reason in reasons)
    if reasons != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return reasons


def _require_config_version(value: object) -> None:
    if value != DEFAULT_SPECIALIST_TEAM_LEARNING_LOOP_READINESS_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_team_label(value: object) -> None:
    if type(value) is not str or value not in ALLOWED_TEAM_LABELS:
        raise ValueError("team_label must be one of politics, finance, or sports")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SPECIALIST_TEAM_LEARNING_LOOP_PRIORITY_BANDS:
        raise ValueError(f"{field_name} must be ready, attention, or blocked")


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize_ratio(value)
    if quantized < ZERO_RATIO or quantized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(numerator / denominator)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SIX_PLACES)


def _count(value: int) -> Decimal:
    return Decimal(value)


def _public_dict(value: object) -> dict[str, Any]:
    if not is_dataclass(value):
        raise ValueError("value must be a dataclass")
    return {field.name: getattr(value, field.name) for field in fields(value)}

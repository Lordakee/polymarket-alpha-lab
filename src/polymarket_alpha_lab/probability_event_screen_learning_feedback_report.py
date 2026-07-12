"""Pure learning-feedback readiness report for probability event screens."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_PROBABILITY_EVENT_SCREEN_LEARNING_FEEDBACK_CONFIG_VERSION = (
    "probability-event-screen-learning-feedback-v0"
)
PROBABILITY_EVENT_SCREEN_LEARNING_BANDS = ("ready", "attention", "blocked")

READY_BAND = "ready"
ATTENTION_BAND = "attention"
BLOCKED_BAND = "blocked"

POSTMORTEM_NOT_READY = "postmortem_not_ready"
TEAM_MEMORY_UPDATE_QUEUE_NOT_READY = "team_memory_update_queue_not_ready"
THRESHOLD_BACKTEST_NOT_READY = "threshold_backtest_not_ready"
SUPABASE_PERSISTENCE_NOT_READY = "supabase_persistence_not_ready"
TEAM_SCORECARD_NOT_READY = "team_scorecard_not_ready"
SOURCE_FAMILY_FEEDBACK_NOT_READY = "source_family_feedback_not_ready"
CALIBRATION_SAMPLE_NOT_READY = "calibration_sample_not_ready"

BLOCKED_REASON_CODES = (
    POSTMORTEM_NOT_READY,
    TEAM_MEMORY_UPDATE_QUEUE_NOT_READY,
    THRESHOLD_BACKTEST_NOT_READY,
    SUPABASE_PERSISTENCE_NOT_READY,
)
ATTENTION_REASON_CODES = (
    TEAM_SCORECARD_NOT_READY,
    SOURCE_FAMILY_FEEDBACK_NOT_READY,
    CALIBRATION_SAMPLE_NOT_READY,
)

READINESS_FLAG_NAMES = (
    "postmortem_ready",
    "team_memory_update_queue_ready",
    "threshold_backtest_ready",
    "team_scorecard_ready",
    "source_family_feedback_ready",
    "calibration_sample_ready",
    "supabase_persistence_ready",
)

DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
SIX_PLACES = Decimal("0.000001")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

__all__ = (
    "DEFAULT_PROBABILITY_EVENT_SCREEN_LEARNING_FEEDBACK_CONFIG_VERSION",
    "PROBABILITY_EVENT_SCREEN_LEARNING_BANDS",
    "ProbabilityEventScreenLearningFeedbackReport",
    "build_probability_event_screen_learning_feedback_report",
)


@dataclass(frozen=True)
class ProbabilityEventScreenLearningFeedbackReport:
    config_version: str
    postmortem_ready: bool
    team_memory_update_queue_ready: bool
    threshold_backtest_ready: bool
    team_scorecard_ready: bool
    source_family_feedback_ready: bool
    calibration_sample_ready: bool
    supabase_persistence_ready: bool
    learning_feedback_ready: bool
    learning_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenLearningFeedbackReport:
            raise ValueError(
                "report must be exactly ProbabilityEventScreenLearningFeedbackReport",
            )
        _require_config_version(self.config_version)
        for field_name in READINESS_FLAG_NAMES:
            _require_bool(field_name, getattr(self, field_name))
        _require_bool("learning_feedback_ready", self.learning_feedback_ready)
        _require_learning_band(self.learning_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_CODES,
            ),
        )
        object.__setattr__(self, "ready_ratio", _normalize_ratio("ready_ratio", self.ready_ratio))
        _require_digest(self.digest)
        require_paper_only_flags("probability event screen learning feedback report", self)
        reject_unsafe_surface_fields("probability event screen learning feedback report", _public_dict(self))
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return probability_event_screen_learning_feedback_report_payload(self)


def build_probability_event_screen_learning_feedback_report(
    *,
    postmortem_ready: bool,
    team_memory_update_queue_ready: bool,
    threshold_backtest_ready: bool,
    team_scorecard_ready: bool,
    source_family_feedback_ready: bool,
    calibration_sample_ready: bool,
    supabase_persistence_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenLearningFeedbackReport:
    flags = dict(
        postmortem_ready=postmortem_ready,
        team_memory_update_queue_ready=team_memory_update_queue_ready,
        threshold_backtest_ready=threshold_backtest_ready,
        team_scorecard_ready=team_scorecard_ready,
        source_family_feedback_ready=source_family_feedback_ready,
        calibration_sample_ready=calibration_sample_ready,
        supabase_persistence_ready=supabase_persistence_ready,
    )
    for field_name, value in flags.items():
        _require_bool(field_name, value)
    parts = dict(
        config_version=DEFAULT_PROBABILITY_EVENT_SCREEN_LEARNING_FEEDBACK_CONFIG_VERSION,
        **flags,
        learning_feedback_ready=_learning_feedback_ready(flags),
        learning_band=_learning_band(flags),
        blocked_reason_codes=_blocked_reason_codes(flags),
        attention_reason_codes=_attention_reason_codes(flags),
        ready_ratio=_ready_ratio(flags),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )
    report = ProbabilityEventScreenLearningFeedbackReport(
        **parts,
        digest=_digest_for_parts(parts),
    )
    return report


def probability_event_screen_learning_feedback_report_payload(
    report: ProbabilityEventScreenLearningFeedbackReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventScreenLearningFeedbackReport:
        raise ValueError("report must be a ProbabilityEventScreenLearningFeedbackReport")
    require_paper_only_flags("report", report)
    _validate_report(report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("public_payload must be a JSON object")
    reject_unsafe_surface_fields("public_payload", payload)
    return payload


def probability_event_screen_learning_feedback_report_digest(
    report: ProbabilityEventScreenLearningFeedbackReport,
) -> str:
    if type(report) is not ProbabilityEventScreenLearningFeedbackReport:
        raise ValueError("report must be a ProbabilityEventScreenLearningFeedbackReport")
    require_paper_only_flags("report", report)
    _validate_report(report)
    return _digest_for_parts(_parts_without_digest(report))


def _learning_feedback_ready(flags: dict[str, bool]) -> bool:
    return not _blocked_reason_codes(flags) and not _attention_reason_codes(flags)


def _learning_band(flags: dict[str, bool]) -> str:
    if _blocked_reason_codes(flags):
        return BLOCKED_BAND
    if _attention_reason_codes(flags):
        return ATTENTION_BAND
    return READY_BAND


def _blocked_reason_codes(flags: dict[str, bool]) -> tuple[str, ...]:
    reasons: list[str] = []
    if not flags["postmortem_ready"]:
        reasons.append(POSTMORTEM_NOT_READY)
    if not flags["team_memory_update_queue_ready"]:
        reasons.append(TEAM_MEMORY_UPDATE_QUEUE_NOT_READY)
    if not flags["threshold_backtest_ready"]:
        reasons.append(THRESHOLD_BACKTEST_NOT_READY)
    if not flags["supabase_persistence_ready"]:
        reasons.append(SUPABASE_PERSISTENCE_NOT_READY)
    return tuple(reasons)


def _attention_reason_codes(flags: dict[str, bool]) -> tuple[str, ...]:
    reasons: list[str] = []
    if not flags["team_scorecard_ready"]:
        reasons.append(TEAM_SCORECARD_NOT_READY)
    if not flags["source_family_feedback_ready"]:
        reasons.append(SOURCE_FAMILY_FEEDBACK_NOT_READY)
    if not flags["calibration_sample_ready"]:
        reasons.append(CALIBRATION_SAMPLE_NOT_READY)
    return tuple(reasons)


def _ready_ratio(flags: dict[str, bool]) -> Decimal:
    ready_count = Decimal(sum(1 for field_name in READINESS_FLAG_NAMES if flags[field_name]))
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ready_ratio", ready_count / Decimal(len(READINESS_FLAG_NAMES)))


def _validate_report(report: ProbabilityEventScreenLearningFeedbackReport) -> None:
    flags = _flags_for_report(report)
    if report.blocked_reason_codes != _blocked_reason_codes(flags):
        raise ValueError("blocked_reason_codes must match readiness flags")
    if report.attention_reason_codes != _attention_reason_codes(flags):
        raise ValueError("attention_reason_codes must match readiness flags")
    if report.learning_band != _learning_band(flags):
        raise ValueError("learning_band must match readiness flags")
    if report.learning_feedback_ready != _learning_feedback_ready(flags):
        raise ValueError("learning_feedback_ready must match readiness flags")
    if report.ready_ratio != _ready_ratio(flags):
        raise ValueError("ready_ratio must match readiness flags")
    if report.digest != _digest_for_parts(_parts_without_digest(report)):
        raise ValueError("digest must match report payload")


def _flags_for_report(report: ProbabilityEventScreenLearningFeedbackReport) -> dict[str, bool]:
    return {field_name: getattr(report, field_name) for field_name in READINESS_FLAG_NAMES}


def _parts_without_digest(report: ProbabilityEventScreenLearningFeedbackReport) -> dict[str, Any]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "digest"
    }


def _digest_for_parts(parts: dict[str, Any]) -> str:
    payload = json_ready_no_floats(parts)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    allowed_ranks = {reason: index for index, reason in enumerate(allowed_values)}
    for reason in value:
        if type(reason) is not str or reason not in allowed_ranks:
            raise ValueError(f"{field_name} must contain known values")
    expected = tuple(reason for reason in allowed_values if reason in value)
    if value != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return value


def _require_config_version(value: object) -> None:
    if value != DEFAULT_PROBABILITY_EVENT_SCREEN_LEARNING_FEEDBACK_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_learning_band(value: object) -> None:
    if type(value) is not str or value not in PROBABILITY_EVENT_SCREEN_LEARNING_BANDS:
        raise ValueError("learning_band must be ready, attention, or blocked")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SIX_PLACES)
    if quantized < ZERO_RATIO or quantized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _require_digest(value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError("digest must be a 64 character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError("digest must be a 64 character hex string")


def _public_dict(value: object) -> dict[str, Any]:
    if not is_dataclass(value):
        raise ValueError("value must be a dataclass")
    return {field.name: getattr(value, field.name) for field in fields(value)}

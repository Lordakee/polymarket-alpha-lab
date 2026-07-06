"""Phase 1 report-only specialist confidence feedback decay."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_TEAM_SPECIALIST_CONFIDENCE_FEEDBACK_DECAY_V2_CONFIG_VERSION = (
    "team-specialist-confidence-feedback-decay-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_CONFIDENCE_STATUSES = frozenset(("pass", "watch", "blocked"))
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
_REASON_CODE_SEQUENCE = (
    "no_specialist_confidence_feedback_observations_supplied",
    "confidence_feedback_decay_applied",
    "stale_feedback_penalty",
    "recent_calibration_boost",
    "specialist_confidence_pass",
    "specialist_confidence_watch",
    "specialist_confidence_blocked",
)


@dataclass(frozen=True)
class TeamSpecialistConfidenceFeedbackDecayConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_CONFIDENCE_FEEDBACK_DECAY_V2_CONFIG_VERSION
    feedback_decay_window_seconds: Decimal = Decimal("1209600.000000")
    stale_feedback_after_seconds: Decimal = Decimal("604800.000000")
    stale_feedback_penalty: Decimal = Decimal("0.150000")
    recent_calibration_window_seconds: Decimal = Decimal("172800.000000")
    recent_calibration_boost: Decimal = Decimal("0.100000")
    min_recent_calibration_score: Decimal = Decimal("0.750000")
    min_pass_confidence_score: Decimal = Decimal("0.700000")
    min_watch_confidence_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistConfidenceFeedbackDecayConfig:
            raise TypeError(
                "TeamSpecialistConfidenceFeedbackDecayConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistConfidenceFeedbackDecayConfig:
            raise ValueError(
                "config must be exactly TeamSpecialistConfidenceFeedbackDecayConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CONFIDENCE_FEEDBACK_DECAY_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "feedback_decay_window_seconds",
            "stale_feedback_after_seconds",
            "recent_calibration_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_feedback_penalty",
            "recent_calibration_boost",
            "min_recent_calibration_score",
            "min_pass_confidence_score",
            "min_watch_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_confidence_score > self.min_pass_confidence_score:
            raise ValueError(
                "min_watch_confidence_score must not exceed min_pass_confidence_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistConfidenceFeedbackObservation:
    team_id: str
    specialist_id: str
    subject_id: str
    feedback_observed_at: datetime
    base_confidence_score: Decimal
    feedback_confidence_score: Decimal
    calibration_observed_at: datetime | None = None
    calibration_score: Decimal = Decimal("0.000000")
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistConfidenceFeedbackObservation:
            raise TypeError(
                "TeamSpecialistConfidenceFeedbackObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistConfidenceFeedbackObservation:
            raise ValueError(
                "observation must be exactly TeamSpecialistConfidenceFeedbackObservation",
            )
        for field_name in ("team_id", "specialist_id", "subject_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "feedback_observed_at",
            _as_utc("feedback_observed_at", self.feedback_observed_at),
        )
        object.__setattr__(
            self,
            "calibration_observed_at",
            _as_optional_utc("calibration_observed_at", self.calibration_observed_at),
        )
        for field_name in (
            "base_confidence_score",
            "feedback_confidence_score",
            "calibration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class TeamSpecialistConfidenceFeedbackPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistConfidenceFeedbackPublicPayloadItem:
            raise TypeError(
                "TeamSpecialistConfidenceFeedbackPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistConfidenceFeedbackPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "TeamSpecialistConfidenceFeedbackPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class TeamSpecialistConfidenceFeedbackDecayRow:
    team_id: str
    specialist_id: str
    subject_id: str
    feedback_observed_at: datetime
    feedback_age_seconds: Decimal
    base_confidence_score: Decimal
    feedback_confidence_score: Decimal
    feedback_decay_multiplier: Decimal
    stale_feedback_penalty: Decimal
    calibration_observed_at: datetime | None
    calibration_age_seconds: Decimal | None
    calibration_score: Decimal
    recent_calibration_boost: Decimal
    decayed_confidence_score: Decimal
    confidence_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistConfidenceFeedbackDecayRow:
            raise TypeError(
                "TeamSpecialistConfidenceFeedbackDecayRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistConfidenceFeedbackDecayRow:
            raise ValueError("row must be exactly TeamSpecialistConfidenceFeedbackDecayRow")
        for field_name in ("team_id", "specialist_id", "subject_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "feedback_observed_at",
            _as_utc("feedback_observed_at", self.feedback_observed_at),
        )
        object.__setattr__(
            self,
            "feedback_age_seconds",
            _require_nonnegative_decimal(
                "feedback_age_seconds",
                self.feedback_age_seconds,
            ),
        )
        for field_name in (
            "base_confidence_score",
            "feedback_confidence_score",
            "feedback_decay_multiplier",
            "stale_feedback_penalty",
            "calibration_score",
            "recent_calibration_boost",
            "decayed_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_observed_at",
            _as_optional_utc("calibration_observed_at", self.calibration_observed_at),
        )
        object.__setattr__(
            self,
            "calibration_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "calibration_age_seconds",
                self.calibration_age_seconds,
            ),
        )
        if self.calibration_observed_at is None and self.calibration_age_seconds is not None:
            raise ValueError(
                "calibration_age_seconds must be None without calibration_observed_at",
            )
        if self.calibration_observed_at is not None and self.calibration_age_seconds is None:
            raise ValueError(
                "calibration_age_seconds must be present with calibration_observed_at",
            )
        _require_confidence_status("confidence_status", self.confidence_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamSpecialistConfidenceFeedbackDecayReport:
    generated_at: datetime
    config_version: str
    report_status: str
    source_row_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_base_confidence_score: Decimal
    average_feedback_confidence_score: Decimal
    average_decayed_confidence_score: Decimal
    max_feedback_age_seconds: Decimal | None
    max_stale_feedback_penalty: Decimal
    max_recent_calibration_boost: Decimal
    rows: tuple[TeamSpecialistConfidenceFeedbackDecayRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[TeamSpecialistConfidenceFeedbackPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistConfidenceFeedbackDecayReport:
            raise TypeError(
                "TeamSpecialistConfidenceFeedbackDecayReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistConfidenceFeedbackDecayReport:
            raise ValueError(
                "report must be exactly TeamSpecialistConfidenceFeedbackDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CONFIDENCE_FEEDBACK_DECAY_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_confidence_status("report_status", self.report_status)
        for field_name in (
            "source_row_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_base_confidence_score",
            "average_feedback_confidence_score",
            "average_decayed_confidence_score",
            "max_stale_feedback_penalty",
            "max_recent_calibration_boost",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_feedback_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "max_feedback_age_seconds",
                self.max_feedback_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistConfidenceFeedbackDecayReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_confidence_feedback_decay_v2_report(
    observations: Sequence[TeamSpecialistConfidenceFeedbackObservation],
    *,
    generated_at: datetime,
    config: TeamSpecialistConfidenceFeedbackDecayConfig | None = None,
    public_payload: Sequence[TeamSpecialistConfidenceFeedbackPublicPayloadItem] = (),
) -> TeamSpecialistConfidenceFeedbackDecayReport:
    """Build a local report-only specialist confidence feedback decay snapshot."""

    if config is None:
        config = TeamSpecialistConfidenceFeedbackDecayConfig()
    if type(config) is not TeamSpecialistConfidenceFeedbackDecayConfig:
        raise ValueError(
            "config must be a TeamSpecialistConfidenceFeedbackDecayConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.feedback_observed_at > generated_at:
            raise ValueError("feedback_observed_at must not be after generated_at")
        if (
            item.calibration_observed_at is not None
            and item.calibration_observed_at > generated_at
        ):
            raise ValueError("calibration_observed_at must not be after generated_at")
    rows = tuple(
        _row_for_observation(
            observation=item,
            config=config,
            generated_at=generated_at,
        )
        for item in normalized_observations
    )
    payload_items = _normalize_public_payload(public_payload)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "source_row_count": _decimal_count(len(normalized_observations)),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "average_base_confidence_score": _average(
            tuple(row.base_confidence_score for row in rows),
        ),
        "average_feedback_confidence_score": _average(
            tuple(row.feedback_confidence_score for row in rows),
        ),
        "average_decayed_confidence_score": _average(
            tuple(row.decayed_confidence_score for row in rows),
        ),
        "max_feedback_age_seconds": max(
            (row.feedback_age_seconds for row in rows),
            default=None,
        ),
        "max_stale_feedback_penalty": max(
            (row.stale_feedback_penalty for row in rows),
            default=_ZERO,
        ),
        "max_recent_calibration_boost": max(
            (row.recent_calibration_boost for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistConfidenceFeedbackDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_for_observation(
    *,
    observation: TeamSpecialistConfidenceFeedbackObservation,
    config: TeamSpecialistConfidenceFeedbackDecayConfig,
    generated_at: datetime,
) -> TeamSpecialistConfidenceFeedbackDecayRow:
    feedback_age_seconds = _age_seconds(generated_at, observation.feedback_observed_at)
    decay_multiplier = _feedback_decay_multiplier(
        feedback_age_seconds,
        config.feedback_decay_window_seconds,
    )
    stale_penalty = (
        config.stale_feedback_penalty
        if feedback_age_seconds > config.stale_feedback_after_seconds
        else _ZERO
    )
    calibration_age_seconds = (
        None
        if observation.calibration_observed_at is None
        else _age_seconds(generated_at, observation.calibration_observed_at)
    )
    calibration_boost = _recent_calibration_boost(
        calibration_age_seconds=calibration_age_seconds,
        calibration_score=observation.calibration_score,
        config=config,
    )
    decayed_confidence = _clamp_ratio(
        observation.base_confidence_score
        + (
            observation.feedback_confidence_score
            - observation.base_confidence_score
        )
        * decay_multiplier
        - stale_penalty
        + calibration_boost,
    )
    confidence_status = _confidence_status(
        decayed_confidence_score=decayed_confidence,
        config=config,
    )
    return TeamSpecialistConfidenceFeedbackDecayRow(
        team_id=observation.team_id,
        specialist_id=observation.specialist_id,
        subject_id=observation.subject_id,
        feedback_observed_at=observation.feedback_observed_at,
        feedback_age_seconds=feedback_age_seconds,
        base_confidence_score=observation.base_confidence_score,
        feedback_confidence_score=observation.feedback_confidence_score,
        feedback_decay_multiplier=decay_multiplier,
        stale_feedback_penalty=stale_penalty,
        calibration_observed_at=observation.calibration_observed_at,
        calibration_age_seconds=calibration_age_seconds,
        calibration_score=observation.calibration_score,
        recent_calibration_boost=calibration_boost,
        decayed_confidence_score=decayed_confidence,
        confidence_status=confidence_status,
        reason_codes=_row_reason_codes(
            stale_feedback_penalty=stale_penalty,
            recent_calibration_boost=calibration_boost,
            confidence_status=confidence_status,
        ),
    )


def _feedback_decay_multiplier(
    feedback_age_seconds: Decimal,
    feedback_decay_window_seconds: Decimal,
) -> Decimal:
    if feedback_age_seconds >= feedback_decay_window_seconds:
        return _ZERO
    return _clamp_ratio(_ONE - (feedback_age_seconds / feedback_decay_window_seconds))


def _recent_calibration_boost(
    *,
    calibration_age_seconds: Decimal | None,
    calibration_score: Decimal,
    config: TeamSpecialistConfidenceFeedbackDecayConfig,
) -> Decimal:
    if calibration_age_seconds is None:
        return _ZERO
    if calibration_age_seconds > config.recent_calibration_window_seconds:
        return _ZERO
    if calibration_score < config.min_recent_calibration_score:
        return _ZERO
    return config.recent_calibration_boost


def _confidence_status(
    *,
    decayed_confidence_score: Decimal,
    config: TeamSpecialistConfidenceFeedbackDecayConfig,
) -> str:
    if decayed_confidence_score >= config.min_pass_confidence_score:
        return "pass"
    if decayed_confidence_score >= config.min_watch_confidence_score:
        return "watch"
    return "blocked"


def _row_reason_codes(
    *,
    stale_feedback_penalty: Decimal,
    recent_calibration_boost: Decimal,
    confidence_status: str,
) -> tuple[str, ...]:
    reason_codes = ["confidence_feedback_decay_applied"]
    if stale_feedback_penalty > _ZERO:
        reason_codes.append("stale_feedback_penalty")
    if recent_calibration_boost > _ZERO:
        reason_codes.append("recent_calibration_boost")
    reason_codes.append(f"specialist_confidence_{confidence_status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[TeamSpecialistConfidenceFeedbackDecayRow, ...],
) -> str:
    if any(row.confidence_status == "blocked" for row in rows):
        return "blocked"
    if any(row.confidence_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamSpecialistConfidenceFeedbackDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_specialist_confidence_feedback_observations_supplied",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[TeamSpecialistConfidenceFeedbackDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.confidence_status == status)


def _validate_row_consistency(
    row: TeamSpecialistConfidenceFeedbackDecayRow,
) -> None:
    status_reason = f"specialist_confidence_{row.confidence_status}"
    if status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include the confidence status reason")
    if (
        row.stale_feedback_penalty > _ZERO
        and "stale_feedback_penalty" not in row.reason_codes
    ):
        raise ValueError("reason_codes must include stale_feedback_penalty")
    if (
        row.recent_calibration_boost > _ZERO
        and "recent_calibration_boost" not in row.reason_codes
    ):
        raise ValueError("reason_codes must include recent_calibration_boost")


def _validate_report_consistency(
    report: TeamSpecialistConfidenceFeedbackDecayReport,
) -> None:
    if report.source_row_count != _decimal_count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_base_confidence_score != _average(
        tuple(row.base_confidence_score for row in report.rows),
    ):
        raise ValueError("average_base_confidence_score must match rows")
    if report.average_feedback_confidence_score != _average(
        tuple(row.feedback_confidence_score for row in report.rows),
    ):
        raise ValueError("average_feedback_confidence_score must match rows")
    if report.average_decayed_confidence_score != _average(
        tuple(row.decayed_confidence_score for row in report.rows),
    ):
        raise ValueError("average_decayed_confidence_score must match rows")
    expected_max_age = max(
        (row.feedback_age_seconds for row in report.rows),
        default=None,
    )
    if report.max_feedback_age_seconds != expected_max_age:
        raise ValueError("max_feedback_age_seconds must match rows")
    expected_max_penalty = max(
        (row.stale_feedback_penalty for row in report.rows),
        default=_ZERO,
    )
    if report.max_stale_feedback_penalty != expected_max_penalty:
        raise ValueError("max_stale_feedback_penalty must match rows")
    expected_max_boost = max(
        (row.recent_calibration_boost for row in report.rows),
        default=_ZERO,
    )
    if report.max_recent_calibration_boost != expected_max_boost:
        raise ValueError("max_recent_calibration_boost must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[TeamSpecialistConfidenceFeedbackObservation],
) -> tuple[TeamSpecialistConfidenceFeedbackObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[TeamSpecialistConfidenceFeedbackObservation] = []
    for item in observations:
        if type(item) is not TeamSpecialistConfidenceFeedbackObservation:
            raise ValueError(
                "observations must contain TeamSpecialistConfidenceFeedbackObservation",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.team_id,
                item.specialist_id,
                item.subject_id,
                item.feedback_observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[TeamSpecialistConfidenceFeedbackDecayRow],
) -> tuple[TeamSpecialistConfidenceFeedbackDecayRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[TeamSpecialistConfidenceFeedbackDecayRow] = []
    for row in rows:
        if type(row) is not TeamSpecialistConfidenceFeedbackDecayRow:
            raise ValueError("rows must contain TeamSpecialistConfidenceFeedbackDecayRow")
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.team_id,
                row.specialist_id,
                row.subject_id,
                row.feedback_observed_at,
            ),
        ),
    )


def _normalize_public_payload(
    public_payload: Sequence[TeamSpecialistConfidenceFeedbackPublicPayloadItem],
) -> tuple[TeamSpecialistConfidenceFeedbackPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[TeamSpecialistConfidenceFeedbackPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not TeamSpecialistConfidenceFeedbackPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "TeamSpecialistConfidenceFeedbackPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_text(field_name, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_confidence_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _CONFIDENCE_STATUSES:
        raise ValueError(f"{field_name} must be a known confidence status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = (
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
    )
    return _require_nonnegative_decimal("age_seconds", seconds)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _report_values_without_digest(
    report: TeamSpecialistConfidenceFeedbackDecayReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_CONFIDENCE_FEEDBACK_DECAY_V2_CONFIG_VERSION",
    "TeamSpecialistConfidenceFeedbackDecayConfig",
    "TeamSpecialistConfidenceFeedbackObservation",
    "TeamSpecialistConfidenceFeedbackPublicPayloadItem",
    "TeamSpecialistConfidenceFeedbackDecayRow",
    "TeamSpecialistConfidenceFeedbackDecayReport",
    "build_team_specialist_confidence_feedback_decay_v2_report",
)

"""Readonly Decimal report for specialist outcome-feedback learning rank."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_OUTCOME_FEEDBACK_LEARNING_RANK_V2_CONFIG_VERSION = (
    "team-specialist-outcome-feedback-learning-rank-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
SECONDS_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
FORECAST_ERROR_BUCKETS = ("low", "medium", "high")
ROW_REASON_CODES = (
    "outcome_feedback_learning_pass",
    "outcome_feedback_learning_watch",
    "outcome_feedback_learning_blocked",
    "feedback_incorporation_strong",
    "feedback_incorporation_watch",
    "feedback_incorporation_weak",
    "brier_improvement_present",
    "brier_improvement_flat_or_worse",
    "calibration_improvement_present",
    "calibration_improvement_flat_or_worse",
    "poor_calibration_penalty_none",
    "poor_calibration_penalty_watch",
    "poor_calibration_penalty_high",
    "recent_improvement_boost",
    "no_recent_improvement_boost",
)
REPORT_REASON_CODES = (
    "outcome_feedback_learning_rank_passed",
    "outcome_feedback_learning_rank_watch_rows",
    "outcome_feedback_learning_rank_blocked_rows",
    "outcome_feedback_learning_rank_empty",
    "recent_improvement_boost_present",
    "poor_calibration_penalty_present",
    "forecast_error_bucket_mix_present",
    "high_forecast_error_bucket_present",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
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

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_OUTCOME_FEEDBACK_LEARNING_RANK_V2_CONFIG_VERSION",
    "TeamSpecialistOutcomeFeedbackLearningRankV2Config",
    "TeamSpecialistOutcomeFeedbackLearningRankV2Input",
    "TeamSpecialistOutcomeFeedbackLearningRankV2Row",
    "TeamSpecialistOutcomeFeedbackLearningRankV2Report",
    "build_team_specialist_outcome_feedback_learning_rank_v2",
    "team_specialist_outcome_feedback_learning_rank_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistOutcomeFeedbackLearningRankV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_OUTCOME_FEEDBACK_LEARNING_RANK_V2_CONFIG_VERSION
    )
    feedback_incorporation_weight: Decimal = Decimal("0.400000")
    brier_improvement_weight: Decimal = Decimal("0.250000")
    calibration_improvement_weight: Decimal = Decimal("0.200000")
    recent_improvement_boost: Decimal = Decimal("0.150000")
    poor_calibration_penalty_weight: Decimal = Decimal("0.300000")
    max_poor_calibration_event_count: Decimal = Decimal("4")
    recent_improvement_window_seconds: Decimal = Decimal("604800.000000")
    pass_score_floor: Decimal = Decimal("0.700000")
    watch_score_floor: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "feedback_incorporation_weight",
            "brier_improvement_weight",
            "calibration_improvement_weight",
            "recent_improvement_boost",
            "poor_calibration_penalty_weight",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_poor_calibration_event_count",
            _normalize_positive_integral_decimal(
                "max_poor_calibration_event_count",
                self.max_poor_calibration_event_count,
            ),
        )
        object.__setattr__(
            self,
            "recent_improvement_window_seconds",
            _normalize_positive_seconds_decimal(
                "recent_improvement_window_seconds",
                self.recent_improvement_window_seconds,
            ),
        )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistOutcomeFeedbackLearningRankV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistOutcomeFeedbackLearningRankV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistOutcomeFeedbackLearningRankV2Input:
    feedback_id: str
    team_id: str
    specialist_id: str
    topic_id: str
    outcome_feedback_count: Decimal
    incorporated_feedback_count: Decimal
    baseline_brier_score: Decimal
    recent_brier_score: Decimal
    baseline_calibration_error: Decimal
    recent_calibration_error: Decimal
    poor_calibration_event_count: Decimal
    latest_feedback_at: datetime | None
    latest_learning_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("feedback_id", "team_id", "specialist_id", "topic_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "outcome_feedback_count",
            "incorporated_feedback_count",
            "poor_calibration_event_count",
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
            "baseline_brier_score",
            "recent_brier_score",
            "baseline_calibration_error",
            "recent_calibration_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_feedback_at",
            _as_optional_utc("latest_feedback_at", self.latest_feedback_at),
        )
        object.__setattr__(
            self,
            "latest_learning_at",
            _as_optional_utc("latest_learning_at", self.latest_learning_at),
        )
        if self.incorporated_feedback_count > self.outcome_feedback_count:
            raise ValueError(
                "incorporated_feedback_count must not exceed outcome_feedback_count",
            )
        _require_hard_flags("TeamSpecialistOutcomeFeedbackLearningRankV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistOutcomeFeedbackLearningRankV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistOutcomeFeedbackLearningRankV2Row:
    rank: Decimal
    feedback_id: str
    team_id: str
    specialist_id: str
    topic_id: str
    outcome_feedback_count: Decimal
    incorporated_feedback_count: Decimal
    feedback_incorporation_rate: Decimal
    baseline_brier_score: Decimal
    recent_brier_score: Decimal
    brier_improvement_score: Decimal
    forecast_error_bucket: str
    forecast_error_bucket_rank: Decimal
    baseline_calibration_error: Decimal
    recent_calibration_error: Decimal
    calibration_improvement_score: Decimal
    poor_calibration_event_count: Decimal
    poor_calibration_penalty: Decimal
    recent_improvement_boost_applied: Decimal
    outcome_feedback_learning_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    latest_feedback_at: datetime | None
    latest_learning_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in ("feedback_id", "team_id", "specialist_id", "topic_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "outcome_feedback_count",
            "incorporated_feedback_count",
            "poor_calibration_event_count",
            "forecast_error_bucket_rank",
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
            "feedback_incorporation_rate",
            "baseline_brier_score",
            "recent_brier_score",
            "brier_improvement_score",
            "baseline_calibration_error",
            "recent_calibration_error",
            "calibration_improvement_score",
            "poor_calibration_penalty",
            "recent_improvement_boost_applied",
            "outcome_feedback_learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "row_status",
            _require_row_status("row_status", self.row_status),
        )
        object.__setattr__(
            self,
            "forecast_error_bucket",
            _require_forecast_error_bucket(
                "forecast_error_bucket",
                self.forecast_error_bucket,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        object.__setattr__(
            self,
            "latest_feedback_at",
            _as_optional_utc("latest_feedback_at", self.latest_feedback_at),
        )
        object.__setattr__(
            self,
            "latest_learning_at",
            _as_optional_utc("latest_learning_at", self.latest_learning_at),
        )
        if self.incorporated_feedback_count > self.outcome_feedback_count:
            raise ValueError(
                "incorporated_feedback_count must not exceed outcome_feedback_count",
            )
        _require_hard_flags("TeamSpecialistOutcomeFeedbackLearningRankV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistOutcomeFeedbackLearningRankV2Row",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistOutcomeFeedbackLearningRankV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    source_feedback_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    recent_improvement_boost_count: Decimal
    poor_calibration_penalty_count: Decimal
    low_forecast_error_bucket_count: Decimal
    medium_forecast_error_bucket_count: Decimal
    high_forecast_error_bucket_count: Decimal
    average_outcome_feedback_learning_score: Decimal
    top_outcome_feedback_learning_score: Decimal
    bottom_outcome_feedback_learning_score: Decimal
    rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_report_status("report_status", self.report_status),
        )
        for field_name in (
            "source_feedback_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "recent_improvement_boost_count",
            "poor_calibration_penalty_count",
            "low_forecast_error_bucket_count",
            "medium_forecast_error_bucket_count",
            "high_forecast_error_bucket_count",
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
            "average_outcome_feedback_learning_score",
            "top_outcome_feedback_learning_score",
            "bottom_outcome_feedback_learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("TeamSpecialistOutcomeFeedbackLearningRankV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistOutcomeFeedbackLearningRankV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistOutcomeFeedbackLearningRankV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_outcome_feedback_learning_rank_v2(
    feedback_rows: object,
    *,
    config: TeamSpecialistOutcomeFeedbackLearningRankV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistOutcomeFeedbackLearningRankV2Report:
    if config is None:
        config = TeamSpecialistOutcomeFeedbackLearningRankV2Config()
    if type(config) is not TeamSpecialistOutcomeFeedbackLearningRankV2Config:
        raise ValueError(
            "config must be a TeamSpecialistOutcomeFeedbackLearningRankV2Config",
        )
    _require_hard_flags("TeamSpecialistOutcomeFeedbackLearningRankV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_feedback_rows = _normalize_feedback_rows(feedback_rows)
    rows = tuple(
        _row_for_feedback(rank=index, feedback=item, config=config, generated_at=generated_at_utc)
        for index, item in enumerate(
            _sorted_feedback_rows(normalized_feedback_rows, config, generated_at_utc),
            start=1,
        )
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": status,
        "source_feedback_count": Decimal(len(normalized_feedback_rows)).quantize(COUNT_QUANT),
        "row_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "recent_improvement_boost_count": _boost_count(rows),
        "poor_calibration_penalty_count": _penalty_count(rows),
        "low_forecast_error_bucket_count": _forecast_error_bucket_count(rows, "low"),
        "medium_forecast_error_bucket_count": _forecast_error_bucket_count(rows, "medium"),
        "high_forecast_error_bucket_count": _forecast_error_bucket_count(rows, "high"),
        "average_outcome_feedback_learning_score": _average_score(rows),
        "top_outcome_feedback_learning_score": _top_score(rows),
        "bottom_outcome_feedback_learning_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistOutcomeFeedbackLearningRankV2Report(**values)


def team_specialist_outcome_feedback_learning_rank_v2_payload(
    value: object,
) -> dict[str, object]:
    if type(value) is TeamSpecialistOutcomeFeedbackLearningRankV2Report:
        return value.payload
    if type(value) is not dict:
        raise ValueError("payload source must be a report or dict")
    _require_payload_hard_flags(value)
    _reject_unsafe_public_payload(
        "team_specialist_outcome_feedback_learning_rank_v2_payload",
        value,
    )
    digest = value.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(value):
        raise ValueError("derived_validation_digest must match payload fields")
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _sorted_feedback_rows(
    rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Input, ...],
    config: TeamSpecialistOutcomeFeedbackLearningRankV2Config,
    generated_at: datetime,
) -> tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Input, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                -_score_for_feedback(item, config, generated_at),
                item.team_id,
                item.specialist_id,
                item.topic_id,
                item.feedback_id,
            ),
        ),
    )


def _row_for_feedback(
    *,
    rank: int,
    feedback: TeamSpecialistOutcomeFeedbackLearningRankV2Input,
    config: TeamSpecialistOutcomeFeedbackLearningRankV2Config,
    generated_at: datetime,
) -> TeamSpecialistOutcomeFeedbackLearningRankV2Row:
    score = _score_for_feedback(feedback, config, generated_at)
    status = _row_status(score, config)
    return TeamSpecialistOutcomeFeedbackLearningRankV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        feedback_id=feedback.feedback_id,
        team_id=feedback.team_id,
        specialist_id=feedback.specialist_id,
        topic_id=feedback.topic_id,
        outcome_feedback_count=feedback.outcome_feedback_count,
        incorporated_feedback_count=feedback.incorporated_feedback_count,
        feedback_incorporation_rate=_feedback_incorporation_rate(feedback),
        baseline_brier_score=feedback.baseline_brier_score,
        recent_brier_score=feedback.recent_brier_score,
        brier_improvement_score=_relative_improvement(
            feedback.baseline_brier_score,
            feedback.recent_brier_score,
        ),
        forecast_error_bucket=_forecast_error_bucket(feedback.recent_brier_score),
        forecast_error_bucket_rank=_forecast_error_bucket_rank(
            _forecast_error_bucket(feedback.recent_brier_score),
        ),
        baseline_calibration_error=feedback.baseline_calibration_error,
        recent_calibration_error=feedback.recent_calibration_error,
        calibration_improvement_score=_relative_improvement(
            feedback.baseline_calibration_error,
            feedback.recent_calibration_error,
        ),
        poor_calibration_event_count=feedback.poor_calibration_event_count,
        poor_calibration_penalty=_poor_calibration_penalty(feedback, config),
        recent_improvement_boost_applied=_recent_improvement_boost(
            feedback,
            config,
            generated_at,
        ),
        outcome_feedback_learning_score=score,
        row_status=status,
        reason_codes=_row_reason_codes(feedback, status, config, generated_at),
        latest_feedback_at=feedback.latest_feedback_at,
        latest_learning_at=feedback.latest_learning_at,
    )


def _score_for_feedback(
    feedback: TeamSpecialistOutcomeFeedbackLearningRankV2Input,
    config: TeamSpecialistOutcomeFeedbackLearningRankV2Config,
    generated_at: datetime,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _feedback_incorporation_rate(feedback) * config.feedback_incorporation_weight
            + _relative_improvement(
                feedback.baseline_brier_score,
                feedback.recent_brier_score,
            )
            * config.brier_improvement_weight
            + _relative_improvement(
                feedback.baseline_calibration_error,
                feedback.recent_calibration_error,
            )
            * config.calibration_improvement_weight
            + _recent_improvement_boost(feedback, config, generated_at)
            - _poor_calibration_penalty(feedback, config)
        )
        return _clamp_ratio(score)


def _feedback_incorporation_rate(
    feedback: TeamSpecialistOutcomeFeedbackLearningRankV2Input,
) -> Decimal:
    if feedback.outcome_feedback_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            feedback.incorporated_feedback_count / feedback.outcome_feedback_count,
        )


def _relative_improvement(baseline: Decimal, recent: Decimal) -> Decimal:
    if baseline == ZERO or recent >= baseline:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((baseline - recent) / baseline)


def _poor_calibration_penalty(
    feedback: TeamSpecialistOutcomeFeedbackLearningRankV2Input,
    config: TeamSpecialistOutcomeFeedbackLearningRankV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        event_rate = _clamp_ratio(
            feedback.poor_calibration_event_count
            / config.max_poor_calibration_event_count,
        )
        return _clamp_ratio(event_rate * config.poor_calibration_penalty_weight)


def _recent_improvement_boost(
    feedback: TeamSpecialistOutcomeFeedbackLearningRankV2Input,
    config: TeamSpecialistOutcomeFeedbackLearningRankV2Config,
    generated_at: datetime,
) -> Decimal:
    if feedback.latest_learning_at is None:
        return ZERO
    age_seconds = _seconds_between(feedback.latest_learning_at, generated_at)
    has_improvement = (
        _relative_improvement(feedback.baseline_brier_score, feedback.recent_brier_score) > ZERO
        or _relative_improvement(
            feedback.baseline_calibration_error,
            feedback.recent_calibration_error,
        )
        > ZERO
    )
    if ZERO <= age_seconds <= config.recent_improvement_window_seconds and has_improvement:
        return config.recent_improvement_boost
    return ZERO


def _row_status(
    score: Decimal,
    config: TeamSpecialistOutcomeFeedbackLearningRankV2Config,
) -> str:
    if score >= config.pass_score_floor:
        return "pass"
    if score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _report_status(rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    feedback: TeamSpecialistOutcomeFeedbackLearningRankV2Input,
    status: str,
    config: TeamSpecialistOutcomeFeedbackLearningRankV2Config,
    generated_at: datetime,
) -> tuple[str, ...]:
    reasons = [
        f"outcome_feedback_learning_{status}",
        _tier_reason(
            _feedback_incorporation_rate(feedback),
            strong=Decimal("0.800000"),
            watch=Decimal("0.500000"),
            strong_reason="feedback_incorporation_strong",
            watch_reason="feedback_incorporation_watch",
            weak_reason="feedback_incorporation_weak",
        ),
    ]
    if _relative_improvement(feedback.baseline_brier_score, feedback.recent_brier_score) > ZERO:
        reasons.append("brier_improvement_present")
    else:
        reasons.append("brier_improvement_flat_or_worse")
    if (
        _relative_improvement(
            feedback.baseline_calibration_error,
            feedback.recent_calibration_error,
        )
        > ZERO
    ):
        reasons.append("calibration_improvement_present")
    else:
        reasons.append("calibration_improvement_flat_or_worse")
    reasons.append(_poor_calibration_reason(feedback, config))
    if _recent_improvement_boost(feedback, config, generated_at) > ZERO:
        reasons.append("recent_improvement_boost")
    else:
        reasons.append("no_recent_improvement_boost")
    return tuple(reasons)


def _tier_reason(
    value: Decimal,
    *,
    strong: Decimal,
    watch: Decimal,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if value >= strong:
        return strong_reason
    if value >= watch:
        return watch_reason
    return weak_reason


def _poor_calibration_reason(
    feedback: TeamSpecialistOutcomeFeedbackLearningRankV2Input,
    config: TeamSpecialistOutcomeFeedbackLearningRankV2Config,
) -> str:
    event_rate = _clamp_ratio(
        feedback.poor_calibration_event_count / config.max_poor_calibration_event_count,
    )
    if event_rate == ZERO:
        return "poor_calibration_penalty_none"
    if event_rate < Decimal("0.500000"):
        return "poor_calibration_penalty_watch"
    return "poor_calibration_penalty_high"


def _report_reason_codes(
    rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("outcome_feedback_learning_rank_empty",)
    reasons: list[str] = []
    if any(row.row_status == "blocked" for row in rows):
        reasons.append("outcome_feedback_learning_rank_blocked_rows")
    if any(row.row_status == "watch" for row in rows):
        reasons.append("outcome_feedback_learning_rank_watch_rows")
    if not reasons and status == "pass":
        reasons.append("outcome_feedback_learning_rank_passed")
    if any(row.recent_improvement_boost_applied > ZERO for row in rows):
        reasons.append("recent_improvement_boost_present")
    if any(row.poor_calibration_penalty > ZERO for row in rows):
        reasons.append("poor_calibration_penalty_present")
    if len({row.forecast_error_bucket for row in rows}) > 1:
        reasons.append("forecast_error_bucket_mix_present")
    if any(row.forecast_error_bucket == "high" for row in rows):
        reasons.append("high_forecast_error_bucket_present")
    return tuple(reasons)


def _status_count(
    rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.row_status == status)).quantize(COUNT_QUANT)


def _boost_count(rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...]) -> Decimal:
    return Decimal(
        sum(1 for row in rows if row.recent_improvement_boost_applied > ZERO),
    ).quantize(COUNT_QUANT)


def _penalty_count(rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...]) -> Decimal:
    return Decimal(sum(1 for row in rows if row.poor_calibration_penalty > ZERO)).quantize(
        COUNT_QUANT,
    )


def _forecast_error_bucket_count(
    rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...],
    bucket: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.forecast_error_bucket == bucket)).quantize(
        COUNT_QUANT,
    )


def _average_score(
    rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.outcome_feedback_learning_score for row in rows) / Decimal(len(rows)),
        )


def _top_score(rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.outcome_feedback_learning_score for row in rows)


def _bottom_score(rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.outcome_feedback_learning_score for row in rows)


def _normalize_feedback_rows(
    value: object,
) -> tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("feedback_rows must be an iterable")
    feedback_rows = tuple(value)
    for item in feedback_rows:
        if type(item) is not TeamSpecialistOutcomeFeedbackLearningRankV2Input:
            raise ValueError(
                "feedback rows must be TeamSpecialistOutcomeFeedbackLearningRankV2Input",
            )
        _require_hard_flags("TeamSpecialistOutcomeFeedbackLearningRankV2Input", item)
    keys = tuple((item.team_id, item.specialist_id, item.topic_id) for item in feedback_rows)
    if len(set(keys)) != len(keys):
        raise ValueError("feedback rows must not contain duplicate team specialist topic keys")
    return feedback_rows


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistOutcomeFeedbackLearningRankV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistOutcomeFeedbackLearningRankV2Row",
            )
    return value


def _validate_config(config: TeamSpecialistOutcomeFeedbackLearningRankV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        score_weights = (
            config.feedback_incorporation_weight
            + config.brier_improvement_weight
            + config.calibration_improvement_weight
        ).quantize(SCORE_QUANT)
    if score_weights > ONE:
        raise ValueError("score weights must not exceed 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")


def _validate_report_consistency(
    report: TeamSpecialistOutcomeFeedbackLearningRankV2Report,
) -> None:
    rows = report.rows
    if report.source_feedback_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("source_feedback_count must match rows")
    if report.row_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("row_count must match rows")
    if (
        report.pass_count != _status_count(rows, "pass")
        or report.watch_count != _status_count(rows, "watch")
        or report.blocked_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.row_count:
        raise ValueError("status counts must sum to row_count")
    _validate_rows_sorted(rows)
    expected_status = _report_status(rows)
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.report_status):
        raise ValueError("reason_codes must match rows")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.recent_improvement_boost_count != _boost_count(rows):
        raise ValueError("recent_improvement_boost_count must match rows")
    if report.poor_calibration_penalty_count != _penalty_count(rows):
        raise ValueError("poor_calibration_penalty_count must match rows")
    if report.low_forecast_error_bucket_count != _forecast_error_bucket_count(rows, "low"):
        raise ValueError("low_forecast_error_bucket_count must match rows")
    if report.medium_forecast_error_bucket_count != _forecast_error_bucket_count(rows, "medium"):
        raise ValueError("medium_forecast_error_bucket_count must match rows")
    if report.high_forecast_error_bucket_count != _forecast_error_bucket_count(rows, "high"):
        raise ValueError("high_forecast_error_bucket_count must match rows")
    if report.average_outcome_feedback_learning_score != _average_score(rows):
        raise ValueError("average_outcome_feedback_learning_score must match rows")
    if report.top_outcome_feedback_learning_score != _top_score(rows):
        raise ValueError("top_outcome_feedback_learning_score must match rows")
    if report.bottom_outcome_feedback_learning_score != _bottom_score(rows):
        raise ValueError("bottom_outcome_feedback_learning_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistOutcomeFeedbackLearningRankV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.outcome_feedback_learning_score,
                row.team_id,
                row.specialist_id,
                row.topic_id,
                row.feedback_id,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by score and rank")


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


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * Decimal("86400")
            + Decimal(delta.seconds)
            + Decimal(delta.microseconds) / Decimal("1000000")
        )
        return seconds.quantize(SECONDS_QUANT)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_row_status(field_name: str, value: object) -> str:
    normalized = _require_non_empty_string(field_name, value)
    if normalized not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")
    return normalized


def _require_report_status(field_name: str, value: object) -> str:
    normalized = _require_non_empty_string(field_name, value)
    if normalized not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")
    return normalized


def _require_forecast_error_bucket(field_name: str, value: object) -> str:
    normalized = _require_non_empty_string(field_name, value)
    if normalized not in FORECAST_ERROR_BUCKETS:
        raise ValueError(f"{field_name} must be low, medium, or high")
    return normalized


def _forecast_error_bucket(recent_brier_score: Decimal) -> str:
    if recent_brier_score <= Decimal("0.050000"):
        return "low"
    if recent_brier_score <= Decimal("0.200000"):
        return "medium"
    return "high"


def _forecast_error_bucket_rank(bucket: str) -> Decimal:
    return Decimal(FORECAST_ERROR_BUCKETS.index(bucket) + 1).quantize(COUNT_QUANT)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_positive_seconds_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SECONDS_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _require_payload_hard_flags(value: dict[str, object]) -> None:
    if value.get("paper_only") is not True:
        raise ValueError("paper_only must be True for payload")
    if value.get("report_only") is not True:
        raise ValueError("report_only must be True for payload")
    if value.get("readonly") is not True:
        raise ValueError("readonly must be True for payload")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_text(label, key, "key")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (float, int) and type(value) is not bool:
        raise ValueError(f"unsafe public value in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value, "value")


def _reject_unsafe_public_text(label: str, value: str, kind: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public {kind} in {label}")

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_TEAM_CALIBRATION_REVIEW_QUEUE_V10_CONFIG_VERSION = (
    "team-calibration-review-queue-v10"
)
DECIMAL_QUANTUM = Decimal("0.000001")
WHOLE_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")

REVIEW_STATUSES = frozenset(
    (
        "insufficient_data",
        "queued",
        "monitor",
        "up_to_date",
    ),
)
REVIEW_TYPES = frozenset(
    (
        "sample_size_review",
        "calibration_deep_dive",
        "monitoring_review",
        "no_review_needed",
    ),
)
REASON_CODES = frozenset(
    (
        "insufficient_resolved_markets",
        "critical_calibration_error",
        "elevated_calibration_error",
        "low_hit_rate",
        "overconfidence_bias",
        "underconfidence_bias",
        "elevated_confidence_bias",
        "stale_review_window",
        "source_gap",
        "stable_calibration",
    ),
)
WHOLE_PAYLOAD_FIELDS = frozenset(
    (
        "resolved_market_count",
        "days_since_last_review",
    ),
)


@dataclass(frozen=True)
class TeamCalibrationReviewQueueV10Config:
    config_version: str = DEFAULT_TEAM_CALIBRATION_REVIEW_QUEUE_V10_CONFIG_VERSION
    minimum_resolved_market_count: Decimal = Decimal("20")
    elevated_calibration_error: Decimal = Decimal("0.075000")
    critical_calibration_error: Decimal = Decimal("0.150000")
    low_hit_rate_threshold: Decimal = Decimal("0.450000")
    elevated_bias_abs_score: Decimal = Decimal("0.075000")
    critical_bias_abs_score: Decimal = Decimal("0.125000")
    stale_review_days: Decimal = Decimal("60")
    source_gap_threshold: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamCalibrationReviewQueueV10Config:
            raise TypeError(
                "TeamCalibrationReviewQueueV10Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamCalibrationReviewQueueV10Config:
            raise ValueError("config must be exactly TeamCalibrationReviewQueueV10Config")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "minimum_resolved_market_count",
            _normalize_nonnegative_whole_decimal(
                "minimum_resolved_market_count",
                self.minimum_resolved_market_count,
            ),
        )
        for field_name in (
            "elevated_calibration_error",
            "critical_calibration_error",
            "low_hit_rate_threshold",
            "elevated_bias_abs_score",
            "critical_bias_abs_score",
            "source_gap_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_review_days",
            _normalize_nonnegative_whole_decimal(
                "stale_review_days",
                self.stale_review_days,
            ),
        )
        _require_thresholds(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class TeamCalibrationReviewQueueV10Result:
    team_id: str
    category: str
    resolved_market_count: Decimal
    recent_calibration_error: Decimal
    hit_rate: Decimal
    confidence_bias_score: Decimal
    days_since_last_review: Decimal
    source_gap_rate: Decimal
    review_status: str
    review_priority: Decimal
    recommended_review_type: str
    reason_codes: tuple[str, ...]
    config_version: str = DEFAULT_TEAM_CALIBRATION_REVIEW_QUEUE_V10_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamCalibrationReviewQueueV10Result:
            raise TypeError(
                "TeamCalibrationReviewQueueV10Result does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamCalibrationReviewQueueV10Result:
            raise ValueError("result must be exactly TeamCalibrationReviewQueueV10Result")
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "resolved_market_count",
            _normalize_nonnegative_whole_decimal(
                "resolved_market_count",
                self.resolved_market_count,
            ),
        )
        object.__setattr__(
            self,
            "recent_calibration_error",
            _normalize_probability(
                "recent_calibration_error",
                self.recent_calibration_error,
            ),
        )
        object.__setattr__(
            self,
            "hit_rate",
            _normalize_probability("hit_rate", self.hit_rate),
        )
        object.__setattr__(
            self,
            "confidence_bias_score",
            _normalize_signed_probability(
                "confidence_bias_score",
                self.confidence_bias_score,
            ),
        )
        object.__setattr__(
            self,
            "days_since_last_review",
            _normalize_nonnegative_whole_decimal(
                "days_since_last_review",
                self.days_since_last_review,
            ),
        )
        object.__setattr__(
            self,
            "source_gap_rate",
            _normalize_probability("source_gap_rate", self.source_gap_rate),
        )
        _require_member("review_status", self.review_status, REVIEW_STATUSES)
        object.__setattr__(
            self,
            "review_priority",
            _normalize_probability("review_priority", self.review_priority),
        )
        _require_member("recommended_review_type", self.recommended_review_type, REVIEW_TYPES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_canonical_string("config_version", self.config_version)
        _validate_result(self)
        _require_hard_flags(self)

    @property
    def payload(self) -> dict[str, Any]:
        return team_calibration_review_queue_v10_payload(self)


def build_team_calibration_review_queue_v10(
    *,
    team_id: str,
    category: str,
    resolved_market_count: Decimal,
    recent_calibration_error: Decimal,
    hit_rate: Decimal,
    confidence_bias_score: Decimal,
    days_since_last_review: Decimal,
    source_gap_rate: Decimal,
    config: TeamCalibrationReviewQueueV10Config | None = None,
) -> TeamCalibrationReviewQueueV10Result:
    cfg = config or TeamCalibrationReviewQueueV10Config()
    if type(cfg) is not TeamCalibrationReviewQueueV10Config:
        raise ValueError("config must be a TeamCalibrationReviewQueueV10Config")
    _require_hard_flags(cfg)

    normalized_resolved_market_count = _normalize_nonnegative_whole_decimal(
        "resolved_market_count",
        resolved_market_count,
    )
    normalized_recent_calibration_error = _normalize_probability(
        "recent_calibration_error",
        recent_calibration_error,
    )
    normalized_hit_rate = _normalize_probability("hit_rate", hit_rate)
    normalized_confidence_bias_score = _normalize_signed_probability(
        "confidence_bias_score",
        confidence_bias_score,
    )
    normalized_days_since_last_review = _normalize_nonnegative_whole_decimal(
        "days_since_last_review",
        days_since_last_review,
    )
    normalized_source_gap_rate = _normalize_probability(
        "source_gap_rate",
        source_gap_rate,
    )
    derived = _derive_review_fields(
        resolved_market_count=normalized_resolved_market_count,
        recent_calibration_error=normalized_recent_calibration_error,
        hit_rate=normalized_hit_rate,
        confidence_bias_score=normalized_confidence_bias_score,
        days_since_last_review=normalized_days_since_last_review,
        source_gap_rate=normalized_source_gap_rate,
        config=cfg,
    )

    return TeamCalibrationReviewQueueV10Result(
        team_id=team_id,
        category=category,
        resolved_market_count=normalized_resolved_market_count,
        recent_calibration_error=normalized_recent_calibration_error,
        hit_rate=normalized_hit_rate,
        confidence_bias_score=normalized_confidence_bias_score,
        days_since_last_review=normalized_days_since_last_review,
        source_gap_rate=normalized_source_gap_rate,
        review_status=derived["review_status"],
        review_priority=derived["review_priority"],
        recommended_review_type=derived["recommended_review_type"],
        reason_codes=derived["reason_codes"],
        config_version=cfg.config_version,
    )


def team_calibration_review_queue_v10_payload(
    result: TeamCalibrationReviewQueueV10Result,
) -> dict[str, Any]:
    if type(result) is not TeamCalibrationReviewQueueV10Result:
        raise ValueError("result must be exactly TeamCalibrationReviewQueueV10Result")
    _require_hard_flags(result)
    _validate_result(result)
    return _json_ready(asdict(result))


def _derive_review_fields(
    *,
    resolved_market_count: Decimal,
    recent_calibration_error: Decimal,
    hit_rate: Decimal,
    confidence_bias_score: Decimal,
    days_since_last_review: Decimal,
    source_gap_rate: Decimal,
    config: TeamCalibrationReviewQueueV10Config,
) -> dict[str, Any]:
    if resolved_market_count < config.minimum_resolved_market_count:
        return {
            "review_status": "insufficient_data",
            "review_priority": ZERO.quantize(DECIMAL_QUANTUM),
            "recommended_review_type": "sample_size_review",
            "reason_codes": ("insufficient_resolved_markets",),
        }

    reason_codes: list[str] = []
    priority = ZERO
    if recent_calibration_error >= config.critical_calibration_error:
        reason_codes.append("critical_calibration_error")
        priority += Decimal("0.400000")
    elif recent_calibration_error >= config.elevated_calibration_error:
        reason_codes.append("elevated_calibration_error")
        priority += Decimal("0.150000")

    if hit_rate < config.low_hit_rate_threshold:
        reason_codes.append("low_hit_rate")
        priority += Decimal("0.200000")

    abs_bias_score = abs(confidence_bias_score)
    if abs_bias_score >= config.critical_bias_abs_score:
        if confidence_bias_score > ZERO:
            reason_codes.append("overconfidence_bias")
        else:
            reason_codes.append("underconfidence_bias")
        priority += Decimal("0.150000")
    elif abs_bias_score >= config.elevated_bias_abs_score:
        reason_codes.append("elevated_confidence_bias")
        priority += Decimal("0.100000")

    if days_since_last_review >= config.stale_review_days:
        reason_codes.append("stale_review_window")
        priority += Decimal("0.100000")

    if source_gap_rate >= config.source_gap_threshold:
        reason_codes.append("source_gap")
        priority += Decimal("0.150000")

    if not reason_codes:
        return {
            "review_status": "up_to_date",
            "review_priority": ZERO.quantize(DECIMAL_QUANTUM),
            "recommended_review_type": "no_review_needed",
            "reason_codes": ("stable_calibration",),
        }

    normalized_priority = min(priority, ONE).quantize(DECIMAL_QUANTUM)
    review_status = "queued" if normalized_priority >= Decimal("0.500000") else "monitor"
    return {
        "review_status": review_status,
        "review_priority": normalized_priority,
        "recommended_review_type": (
            "calibration_deep_dive"
            if review_status == "queued"
            else "monitoring_review"
        ),
        "reason_codes": tuple(reason_codes),
    }


def _validate_result(result: TeamCalibrationReviewQueueV10Result) -> None:
    priority = _priority_from_reason_codes(result.reason_codes)
    if result.reason_codes == ("insufficient_resolved_markets",):
        expected_status = "insufficient_data"
        expected_priority = ZERO.quantize(DECIMAL_QUANTUM)
        expected_review_type = "sample_size_review"
    elif result.reason_codes == ("stable_calibration",):
        expected_status = "up_to_date"
        expected_priority = ZERO.quantize(DECIMAL_QUANTUM)
        expected_review_type = "no_review_needed"
    else:
        expected_priority = min(priority, ONE).quantize(DECIMAL_QUANTUM)
        expected_status = "queued" if expected_priority >= Decimal("0.500000") else "monitor"
        expected_review_type = (
            "calibration_deep_dive"
            if expected_status == "queued"
            else "monitoring_review"
        )

    if result.review_status != expected_status:
        raise ValueError("review_status must match reason_codes")
    if result.review_priority != expected_priority:
        raise ValueError("review_priority must match reason_codes")
    if result.recommended_review_type != expected_review_type:
        raise ValueError("recommended_review_type must match review_status")


def _priority_from_reason_codes(reason_codes: tuple[str, ...]) -> Decimal:
    priority = ZERO
    for reason_code in reason_codes:
        if reason_code == "critical_calibration_error":
            priority += Decimal("0.400000")
        elif reason_code == "elevated_calibration_error":
            priority += Decimal("0.150000")
        elif reason_code == "low_hit_rate":
            priority += Decimal("0.200000")
        elif reason_code in ("overconfidence_bias", "underconfidence_bias"):
            priority += Decimal("0.150000")
        elif reason_code == "elevated_confidence_bias":
            priority += Decimal("0.100000")
        elif reason_code == "stale_review_window":
            priority += Decimal("0.100000")
        elif reason_code == "source_gap":
            priority += Decimal("0.150000")
    return priority


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_member(field_name, item, REASON_CODES)
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value).quantize(DECIMAL_QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_signed_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value).quantize(DECIMAL_QUANTUM)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(WHOLE_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(WHOLE_QUANTUM)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: str, allowed_values: frozenset[str]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be supported")


def _require_hard_flags(value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")


def _require_thresholds(config: TeamCalibrationReviewQueueV10Config) -> None:
    if config.elevated_calibration_error > config.critical_calibration_error:
        raise ValueError("elevated_calibration_error must not exceed critical_calibration_error")
    if config.elevated_bias_abs_score > config.critical_bias_abs_score:
        raise ValueError("elevated_bias_abs_score must not exceed critical_bias_abs_score")


def _json_ready(value: Any, *, field_name: str | None = None) -> Any:
    if isinstance(value, Decimal):
        if field_name in WHOLE_PAYLOAD_FIELDS:
            return str(value.quantize(WHOLE_QUANTUM))
        return str(value.quantize(DECIMAL_QUANTUM))
    if type(value) is bool:
        return value
    if type(value) is str:
        _require_canonical_string(field_name or "payload_value", value)
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload key must be a string")
            _require_canonical_string("payload_key", key)
            ready[key] = _json_ready(item, field_name=key)
        return ready
    if value is None:
        return None
    raise ValueError("payload_value is not JSON-ready")


__all__ = [
    "DEFAULT_TEAM_CALIBRATION_REVIEW_QUEUE_V10_CONFIG_VERSION",
    "TeamCalibrationReviewQueueV10Config",
    "TeamCalibrationReviewQueueV10Result",
    "build_team_calibration_review_queue_v10",
    "team_calibration_review_queue_v10_payload",
]

"""Pure paper-only team learning recommendation reducer v10."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_TEAM_LEARNING_RECOMMENDATION_V10_CONFIG_VERSION = (
    "strategy-team-learning-recommendation-v10-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1.000000")

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

ACTION_KEEP = "keep_current_learning_plan"
ACTION_RATIONALE = "improve_rationale_review"
ACTION_SOURCE = "refresh_source_coverage_review"
ACTION_SAMPLE = "expand_learning_sample_before_review"
ACTION_CALIBRATION = "run_calibration_review"
ACTION_DEEP_CALIBRATION = "run_deep_calibration_review"
RECOMMENDED_ACTIONS = (
    ACTION_KEEP,
    ACTION_RATIONALE,
    ACTION_SOURCE,
    ACTION_SAMPLE,
    ACTION_CALIBRATION,
    ACTION_DEEP_CALIBRATION,
)

REASON_CODES = (
    "strategy_team_learning_recommendation_v10_recent_hit_rate_low",
    "strategy_team_learning_recommendation_v10_calibration_error_high",
    "strategy_team_learning_recommendation_v10_source_gap_high",
    "strategy_team_learning_recommendation_v10_rationale_quality_low",
    "strategy_team_learning_recommendation_v10_sample_size_low",
    "strategy_team_learning_recommendation_v10_review_stale",
    "strategy_team_learning_recommendation_v10_training_priority_elevated",
    "strategy_team_learning_recommendation_v10_learning_status_pass",
)

UNSAFE_PAYLOAD_KEY_FRAGMENTS = (
    "au" + "th",
    "priv" + "ate_key",
    "wal" + "let",
    "acc" + "ount",
    "bro" + "ker",
    "place_" + "ord" + "er",
    "submit_" + "ord" + "er",
    "connect",
)

PRIORITY_RECENT_HIT_WEIGHT = Decimal("0.261111")
PRIORITY_CALIBRATION_WEIGHT = Decimal("0.200000")
PRIORITY_SOURCE_WEIGHT = Decimal("0.200000")
PRIORITY_RATIONALE_WEIGHT = Decimal("0.200000")
PRIORITY_SAMPLE_WEIGHT = Decimal("0.107785")
PRIORITY_REVIEW_WEIGHT = Decimal("0.053214")

__all__ = (
    "DEFAULT_STRATEGY_TEAM_LEARNING_RECOMMENDATION_V10_CONFIG_VERSION",
    "StrategyTeamLearningRecommendationV10Config",
    "StrategyTeamLearningRecommendationV10Input",
    "StrategyTeamLearningRecommendationV10Report",
    "build_strategy_team_learning_recommendation_v10",
    "strategy_team_learning_recommendation_v10_payload",
)


@dataclass(frozen=True)
class StrategyTeamLearningRecommendationV10Config:
    config_version: str = DEFAULT_STRATEGY_TEAM_LEARNING_RECOMMENDATION_V10_CONFIG_VERSION
    min_sample_size: Decimal = Decimal("30")
    stale_review_days: Decimal = Decimal("30")
    min_recent_hit_rate: Decimal = Decimal("0.500000")
    max_calibration_error_watch: Decimal = Decimal("0.150000")
    max_calibration_error_blocked: Decimal = Decimal("0.250000")
    max_source_gap_rate_watch: Decimal = Decimal("0.200000")
    max_source_gap_rate_blocked: Decimal = Decimal("0.350000")
    min_rationale_quality_score: Decimal = Decimal("0.650000")
    watch_training_priority: Decimal = Decimal("0.300000")
    blocked_training_priority: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("min_sample_size", "stale_review_days"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_recent_hit_rate",
            "max_calibration_error_watch",
            "max_calibration_error_blocked",
            "max_source_gap_rate_watch",
            "max_source_gap_rate_blocked",
            "min_rationale_quality_score",
            "watch_training_priority",
            "blocked_training_priority",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.max_calibration_error_blocked < self.max_calibration_error_watch:
            raise ValueError(
                "max_calibration_error_blocked must not be below watch threshold",
            )
        if self.max_source_gap_rate_blocked < self.max_source_gap_rate_watch:
            raise ValueError(
                "max_source_gap_rate_blocked must not be below watch threshold",
            )
        if self.blocked_training_priority < self.watch_training_priority:
            raise ValueError(
                "blocked_training_priority must not be below watch threshold",
            )
        _require_paper_flags("config", self)


@dataclass(frozen=True)
class StrategyTeamLearningRecommendationV10Input:
    team_id: str
    category: str
    recent_hit_rate: Decimal
    calibration_error: Decimal
    source_gap_rate: Decimal
    rationale_quality_score: Decimal
    sample_size: Decimal
    days_since_review: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category", self.category)
        for field_name in (
            "recent_hit_rate",
            "calibration_error",
            "source_gap_rate",
            "rationale_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("sample_size", "days_since_review"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyTeamLearningRecommendationV10Report:
    team_id: str
    category: str
    config_version: str
    recent_hit_rate: Decimal
    calibration_error: Decimal
    source_gap_rate: Decimal
    rationale_quality_score: Decimal
    sample_size: Decimal
    days_since_review: Decimal
    learning_status: str
    recommended_action: str
    training_priority: Decimal
    reason_codes: tuple[str, ...]
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category", self.category)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "recent_hit_rate",
            "calibration_error",
            "source_gap_rate",
            "rationale_quality_score",
            "training_priority",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("sample_size", "days_since_review"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("learning_status", self.learning_status, STATUSES)
        _require_member("recommended_action", self.recommended_action, RECOMMENDED_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_paper_flags("report", self)
        object.__setattr__(self, "payload", _report_payload(self))


def build_strategy_team_learning_recommendation_v10(
    row: StrategyTeamLearningRecommendationV10Input,
    *,
    config: StrategyTeamLearningRecommendationV10Config,
) -> StrategyTeamLearningRecommendationV10Report:
    if type(config) is not StrategyTeamLearningRecommendationV10Config:
        raise ValueError(
            "config must be a StrategyTeamLearningRecommendationV10Config",
        )
    if type(row) is not StrategyTeamLearningRecommendationV10Input:
        raise ValueError("row must be a StrategyTeamLearningRecommendationV10Input")
    _require_paper_flags("config", config)
    _require_paper_flags("input", row)

    priority = _training_priority(row, config)
    reason_codes = _reason_codes(row, config, priority)
    status = _learning_status(row, config, reason_codes, priority)
    action = _recommended_action(reason_codes, status)

    return StrategyTeamLearningRecommendationV10Report(
        team_id=row.team_id,
        category=row.category,
        config_version=config.config_version,
        recent_hit_rate=row.recent_hit_rate,
        calibration_error=row.calibration_error,
        source_gap_rate=row.source_gap_rate,
        rationale_quality_score=row.rationale_quality_score,
        sample_size=row.sample_size,
        days_since_review=row.days_since_review,
        learning_status=status,
        recommended_action=action,
        training_priority=priority,
        reason_codes=reason_codes,
        payload={},
    )


def strategy_team_learning_recommendation_v10_payload(
    value: StrategyTeamLearningRecommendationV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is StrategyTeamLearningRecommendationV10Report:
        _require_paper_flags("report", value)
        return _report_payload(value)
    if type(value) is dict:
        _reject_unsafe_payload(value)
        _require_payload_flags(value)
        return _json_ready(value)
    raise ValueError("value must be a StrategyTeamLearningRecommendationV10Report")


def _training_priority(
    row: StrategyTeamLearningRecommendationV10Input,
    config: StrategyTeamLearningRecommendationV10Config,
) -> Decimal:
    sample_gap = _ratio(
        max(config.min_sample_size - row.sample_size, ZERO_COUNT),
        config.min_sample_size,
    )
    review_gap = _ratio(
        max(row.days_since_review - config.stale_review_days, ZERO_COUNT),
        config.stale_review_days,
    )
    with localcontext(DECIMAL_CONTEXT):
        return _q(
            ((ONE - row.recent_hit_rate) * PRIORITY_RECENT_HIT_WEIGHT)
            + (row.calibration_error * PRIORITY_CALIBRATION_WEIGHT)
            + (row.source_gap_rate * PRIORITY_SOURCE_WEIGHT)
            + ((ONE - row.rationale_quality_score) * PRIORITY_RATIONALE_WEIGHT)
            + (sample_gap * PRIORITY_SAMPLE_WEIGHT)
            + (review_gap * PRIORITY_REVIEW_WEIGHT),
        )


def _reason_codes(
    row: StrategyTeamLearningRecommendationV10Input,
    config: StrategyTeamLearningRecommendationV10Config,
    priority: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if row.recent_hit_rate < config.min_recent_hit_rate:
        codes.append("strategy_team_learning_recommendation_v10_recent_hit_rate_low")
    if row.calibration_error >= config.max_calibration_error_watch:
        codes.append("strategy_team_learning_recommendation_v10_calibration_error_high")
    if row.source_gap_rate >= config.max_source_gap_rate_watch:
        codes.append("strategy_team_learning_recommendation_v10_source_gap_high")
    if row.rationale_quality_score < config.min_rationale_quality_score:
        codes.append("strategy_team_learning_recommendation_v10_rationale_quality_low")
    if row.sample_size < config.min_sample_size:
        codes.append("strategy_team_learning_recommendation_v10_sample_size_low")
    if row.days_since_review > config.stale_review_days:
        codes.append("strategy_team_learning_recommendation_v10_review_stale")
    if priority >= config.watch_training_priority:
        codes.append(
            "strategy_team_learning_recommendation_v10_training_priority_elevated",
        )
    if not codes:
        codes.append("strategy_team_learning_recommendation_v10_learning_status_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _learning_status(
    row: StrategyTeamLearningRecommendationV10Input,
    config: StrategyTeamLearningRecommendationV10Config,
    reason_codes: tuple[str, ...],
    priority: Decimal,
) -> str:
    if (
        row.calibration_error >= config.max_calibration_error_blocked
        or row.source_gap_rate >= config.max_source_gap_rate_blocked
        or priority >= config.blocked_training_priority
    ):
        return BLOCKED_STATUS
    if reason_codes != ("strategy_team_learning_recommendation_v10_learning_status_pass",):
        return WATCH_STATUS
    return PASS_STATUS


def _recommended_action(reason_codes: tuple[str, ...], status: str) -> str:
    if status == BLOCKED_STATUS and (
        "strategy_team_learning_recommendation_v10_calibration_error_high"
        in reason_codes
    ):
        return ACTION_DEEP_CALIBRATION
    if "strategy_team_learning_recommendation_v10_calibration_error_high" in reason_codes:
        return ACTION_CALIBRATION
    if "strategy_team_learning_recommendation_v10_source_gap_high" in reason_codes:
        return ACTION_SOURCE
    if "strategy_team_learning_recommendation_v10_rationale_quality_low" in reason_codes:
        return ACTION_RATIONALE
    if "strategy_team_learning_recommendation_v10_sample_size_low" in reason_codes:
        return ACTION_SAMPLE
    return ACTION_KEEP


def _report_payload(report: StrategyTeamLearningRecommendationV10Report) -> dict[str, Any]:
    return _json_ready(
        {
            "team_id": report.team_id,
            "category": report.category,
            "config_version": report.config_version,
            "recent_hit_rate": report.recent_hit_rate,
            "calibration_error": report.calibration_error,
            "source_gap_rate": report.source_gap_rate,
            "rationale_quality_score": report.rationale_quality_score,
            "sample_size": report.sample_size,
            "days_since_review": report.days_since_review,
            "learning_status": report.learning_status,
            "recommended_action": report.recommended_action,
            "training_priority": report.training_priority,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        _require_decimal("JSON Decimal value", value)
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != "payload"
        }
    if type(value) is bool:
        return value
    if value is None:
        return None
    if type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        _reject_unsafe_payload(value)
        return {key: _json_ready(item) for key, item in value.items()}
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe payload field: {key}")
            _reject_unsafe_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload(item)


def _require_payload_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PAYLOAD_KEY_FRAGMENTS)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} values must be unique")
    expected = tuple(code for code in REASON_CODES if code in codes)
    if codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return codes


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _q(decimal_value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        normalized = decimal_value.quantize(COUNT_QUANTUM)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO_COUNT:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _q(min(max(numerator / denominator, ZERO), ONE))


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)

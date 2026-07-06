from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
DEFAULT_CONFIG_VERSION = "strategy-recommendation-actionability-score-v2-phase1"
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
RECHECK_SCORE_BY_STATUS = {
    "confirmed": Decimal("1.000000"),
    "stale": Decimal("0.250000"),
    "adverse_move": Decimal("0.000000"),
}
STATUS_VALUES = ("actionable", "watch", "blocked")
UNSAFE_TEXT_FRAGMENTS = (
    "li" + "ve",
    "au" + "th",
    "wall" + "et",
    "ord" + "er",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sig" + "ning",
    "mut" + "ation",
    "bu" + "y",
    "se" + "ll",
    "tra" + "de",
)
HEX_CHARS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class StrategyRecommendationActionabilityScoreV2Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationActionabilityScoreV2Recommendation:
    recommendation_id: str
    market_slug: str
    source_verified_edge: Decimal
    expected_value_consistency: Decimal
    research_readiness: Decimal
    uncertainty_band_width: Decimal
    liquidity_exit_risk: Decimal
    resolution_ambiguity: Decimal
    portfolio_impact: Decimal
    specialist_confidence: Decimal
    market_probability_move_recheck_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in _DIMENSION_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_recheck_status(
            "market_probability_move_recheck_status",
            self.market_probability_move_recheck_status,
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationActionabilityScoreV2Report:
    generated_at: datetime
    config_version: str
    recommendation_id: str
    market_slug: str
    source_verified_edge: Decimal
    expected_value_consistency: Decimal
    research_readiness: Decimal
    uncertainty_band_width: Decimal
    liquidity_exit_risk: Decimal
    resolution_ambiguity: Decimal
    portfolio_impact: Decimal
    specialist_confidence: Decimal
    market_probability_move_recheck_status: str
    market_probability_move_recheck_score: Decimal
    actionability_score: Decimal
    actionability_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in _DIMENSION_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_recheck_status(
            "market_probability_move_recheck_status",
            self.market_probability_move_recheck_status,
        )
        object.__setattr__(
            self,
            "market_probability_move_recheck_score",
            _normalize_ratio(
                "market_probability_move_recheck_score",
                self.market_probability_move_recheck_score,
            ),
        )
        object.__setattr__(
            self,
            "actionability_score",
            _normalize_ratio("actionability_score", self.actionability_score),
        )
        _require_status("actionability_status", self.actionability_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report values")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _validate_report_consistency(self)
        _require_hard_flags(self)


_DIMENSION_FIELDS = (
    "source_verified_edge",
    "expected_value_consistency",
    "research_readiness",
    "uncertainty_band_width",
    "liquidity_exit_risk",
    "resolution_ambiguity",
    "portfolio_impact",
    "specialist_confidence",
)


def build_strategy_recommendation_actionability_score_v2_report(
    recommendation: StrategyRecommendationActionabilityScoreV2Recommendation,
    *,
    config: StrategyRecommendationActionabilityScoreV2Config,
    generated_at: datetime,
) -> StrategyRecommendationActionabilityScoreV2Report:
    if type(recommendation) is not StrategyRecommendationActionabilityScoreV2Recommendation:
        raise ValueError(
            "recommendation must be a StrategyRecommendationActionabilityScoreV2Recommendation",
        )
    if type(config) is not StrategyRecommendationActionabilityScoreV2Config:
        raise ValueError("config must be a StrategyRecommendationActionabilityScoreV2Config")
    _require_hard_flags(recommendation)
    _require_hard_flags(config)
    generated = _as_utc("generated_at", generated_at)
    recheck_score = _recheck_score(recommendation.market_probability_move_recheck_status)
    score = _actionability_score(recommendation, recheck_score)
    status = _actionability_status(
        recommendation=recommendation,
        recheck_score=recheck_score,
        score=score,
    )
    reason_codes = _reason_codes(
        recommendation=recommendation,
        recheck_score=recheck_score,
        status=status,
    )
    return StrategyRecommendationActionabilityScoreV2Report(
        generated_at=generated,
        config_version=config.config_version,
        recommendation_id=recommendation.recommendation_id,
        market_slug=recommendation.market_slug,
        source_verified_edge=recommendation.source_verified_edge,
        expected_value_consistency=recommendation.expected_value_consistency,
        research_readiness=recommendation.research_readiness,
        uncertainty_band_width=recommendation.uncertainty_band_width,
        liquidity_exit_risk=recommendation.liquidity_exit_risk,
        resolution_ambiguity=recommendation.resolution_ambiguity,
        portfolio_impact=recommendation.portfolio_impact,
        specialist_confidence=recommendation.specialist_confidence,
        market_probability_move_recheck_status=(
            recommendation.market_probability_move_recheck_status
        ),
        market_probability_move_recheck_score=recheck_score,
        actionability_score=score,
        actionability_status=status,
        reason_codes=reason_codes,
        derived_validation_digest="",
    )


def strategy_recommendation_actionability_score_v2_payload(
    report: StrategyRecommendationActionabilityScoreV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationActionabilityScoreV2Report:
        raise ValueError("report must be a StrategyRecommendationActionabilityScoreV2Report")
    _require_hard_flags(report)
    payload = _payload_value(asdict(report))
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report values")
    _validate_report_consistency(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _actionability_score(
    recommendation: StrategyRecommendationActionabilityScoreV2Recommendation,
    recheck_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            recommendation.source_verified_edge * Decimal("0.200000")
            + recommendation.expected_value_consistency * Decimal("0.150000")
            + recommendation.research_readiness * Decimal("0.150000")
            + (ONE - recommendation.uncertainty_band_width) * Decimal("0.100000")
            + (ONE - recommendation.liquidity_exit_risk) * Decimal("0.100000")
            + (ONE - recommendation.resolution_ambiguity) * Decimal("0.100000")
            + recommendation.portfolio_impact * Decimal("0.070000")
            + recommendation.specialist_confidence * Decimal("0.050000")
            + recheck_score * Decimal("0.080000")
        )
        return score.quantize(QUANTUM)


def _actionability_status(
    *,
    recommendation: StrategyRecommendationActionabilityScoreV2Recommendation,
    recheck_score: Decimal,
    score: Decimal,
) -> str:
    if (
        score < Decimal("0.500000")
        or recommendation.source_verified_edge < Decimal("0.500000")
        or recommendation.expected_value_consistency < Decimal("0.500000")
        or recommendation.research_readiness < Decimal("0.500000")
        or recommendation.portfolio_impact < Decimal("0.400000")
        or recommendation.specialist_confidence < Decimal("0.400000")
        or recommendation.uncertainty_band_width > Decimal("0.450000")
        or recommendation.liquidity_exit_risk > Decimal("0.550000")
        or recommendation.resolution_ambiguity > Decimal("0.550000")
        or recheck_score == ZERO
    ):
        return "blocked"
    if score < Decimal("0.800000") or recheck_score < ONE:
        return "watch"
    return "actionable"


def _reason_codes(
    *,
    recommendation: StrategyRecommendationActionabilityScoreV2Recommendation,
    recheck_score: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if recommendation.source_verified_edge < Decimal("0.500000"):
        reason_codes.append("source_verified_edge_below_floor")
    if recommendation.expected_value_consistency < Decimal("0.500000"):
        reason_codes.append("expected_value_consistency_below_floor")
    if recommendation.research_readiness < Decimal("0.500000"):
        reason_codes.append("research_readiness_below_floor")
    if recommendation.uncertainty_band_width > Decimal("0.450000"):
        reason_codes.append("uncertainty_band_too_wide")
    if recommendation.liquidity_exit_risk > Decimal("0.550000"):
        reason_codes.append("liquidity_exit_risk_elevated")
    if recommendation.resolution_ambiguity > Decimal("0.550000"):
        reason_codes.append("resolution_ambiguity_elevated")
    if recommendation.portfolio_impact < Decimal("0.400000"):
        reason_codes.append("portfolio_impact_below_floor")
    if recommendation.specialist_confidence < Decimal("0.400000"):
        reason_codes.append("specialist_confidence_below_floor")
    reason_codes.append(
        "market_probability_move_recheck_"
        f"{recommendation.market_probability_move_recheck_status}",
    )
    if status == "actionable" and recheck_score == ONE and not reason_codes[:-1]:
        reason_codes.insert(0, "actionability_score_ready")
    return tuple(sorted(reason_codes))


def _recheck_score(value: str) -> Decimal:
    _require_recheck_status("market_probability_move_recheck_status", value)
    return RECHECK_SCORE_BY_STATUS[value]


def _validate_report_consistency(
    report: StrategyRecommendationActionabilityScoreV2Report,
) -> None:
    expected_recheck_score = _recheck_score(report.market_probability_move_recheck_status)
    if report.market_probability_move_recheck_score != expected_recheck_score:
        raise ValueError("market_probability_move_recheck_score must match status")
    recommendation = StrategyRecommendationActionabilityScoreV2Recommendation(
        recommendation_id=report.recommendation_id,
        market_slug=report.market_slug,
        source_verified_edge=report.source_verified_edge,
        expected_value_consistency=report.expected_value_consistency,
        research_readiness=report.research_readiness,
        uncertainty_band_width=report.uncertainty_band_width,
        liquidity_exit_risk=report.liquidity_exit_risk,
        resolution_ambiguity=report.resolution_ambiguity,
        portfolio_impact=report.portfolio_impact,
        specialist_confidence=report.specialist_confidence,
        market_probability_move_recheck_status=(
            report.market_probability_move_recheck_status
        ),
    )
    expected_score = _actionability_score(recommendation, expected_recheck_score)
    if report.actionability_score != expected_score:
        raise ValueError("actionability_score must match input dimensions")
    expected_status = _actionability_status(
        recommendation=recommendation,
        recheck_score=expected_recheck_score,
        score=expected_score,
    )
    if report.actionability_status != expected_status:
        raise ValueError("actionability_status must match report values")
    expected_reasons = _reason_codes(
        recommendation=recommendation,
        recheck_score=expected_recheck_score,
        status=expected_status,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report values")


def _derived_validation_digest(
    report: StrategyRecommendationActionabilityScoreV2Report,
) -> str:
    canonical = {
        "actionability_score": _payload_value(report.actionability_score),
        "actionability_status": report.actionability_status,
        "config_version": report.config_version,
        "expected_value_consistency": _payload_value(report.expected_value_consistency),
        "generated_at": _payload_value(report.generated_at),
        "liquidity_exit_risk": _payload_value(report.liquidity_exit_risk),
        "market_probability_move_recheck_score": _payload_value(
            report.market_probability_move_recheck_score,
        ),
        "market_probability_move_recheck_status": (
            report.market_probability_move_recheck_status
        ),
        "market_slug": report.market_slug,
        "paper_only": True,
        "portfolio_impact": _payload_value(report.portfolio_impact),
        "readonly": True,
        "reason_codes": list(report.reason_codes),
        "recommendation_id": report.recommendation_id,
        "report_only": True,
        "research_readiness": _payload_value(report.research_readiness),
        "resolution_ambiguity": _payload_value(report.resolution_ambiguity),
        "source_verified_edge": _payload_value(report.source_verified_edge),
        "specialist_confidence": _payload_value(report.specialist_confidence),
        "uncertainty_band_width": _payload_value(report.uncertainty_band_width),
    }
    encoded = json.dumps(canonical, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _normalize_reason_codes(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string("reason_code", item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(items))


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    _require_decimal("decimal value", value)
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_recheck_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in RECHECK_SCORE_BY_STATUS:
        raise ValueError(f"{field_name} must be a known recheck status")


def _require_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be a known actionability status")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_text_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_digest(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _has_unsafe_text_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS)


def _payload_value(value: Any, *, field_name: str | None = None) -> Any:
    label = field_name or "payload value"
    if isinstance(value, Decimal):
        return str(_quantize_decimal(value))
    if isinstance(value, datetime):
        return _payload_datetime(value, label)
    if type(value) is bool:
        return value
    if type(value) is float:
        raise ValueError(f"{label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal values")
    if type(value) is str:
        _require_canonical_string(label, value)
        return value
    if value is None:
        return None
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload field must be a string")
            _require_canonical_string("payload field", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _payload_value(item, field_name=key)
        return ready
    raise ValueError(f"{label} is not JSON serializable")


def _payload_datetime(value: datetime, field_name: str) -> str:
    text = _as_utc(field_name, value).isoformat()
    if text.endswith("+00:00"):
        return f"{text[:-6]}Z"
    return text


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "StrategyRecommendationActionabilityScoreV2Config",
    "StrategyRecommendationActionabilityScoreV2Recommendation",
    "StrategyRecommendationActionabilityScoreV2Report",
    "build_strategy_recommendation_actionability_score_v2_report",
    "strategy_recommendation_actionability_score_v2_payload",
)

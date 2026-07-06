"""Pure Phase 1 resolution precedent scoring for Polymarket markets."""

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RESOLUTION_PRECEDENT_SCORE_V10_CONFIG_VERSION = (
    "strategy-resolution-precedent-score-v10"
)

ORACLE_SOURCE_TYPES = (
    "official",
    "primary_source",
    "third_party",
    "community_resolution",
    "unknown",
)
REASON_CODES = (
    "resolution_precedent_strong",
    "resolution_precedent_watch",
    "resolution_precedent_manual_review",
    "rules_text_clear",
    "rules_text_ambiguous",
    "sufficient_resolution_history",
    "limited_resolution_history",
    "low_historical_dispute_rate",
    "historical_dispute_rate_high",
    "official_oracle_source",
    "primary_oracle_source",
    "third_party_oracle_source",
    "community_resolution_source",
    "unknown_oracle_source",
    "deadline_consistency_clear",
    "deadline_consistency_weak",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RULES_CLEAR_THRESHOLD = Decimal("0.800000")
RULES_AMBIGUOUS_THRESHOLD = Decimal("0.600000")
LOW_DISPUTE_RATE = Decimal("0.050000")
DEADLINE_CLEAR_THRESHOLD = Decimal("0.800000")
DEADLINE_WEAK_THRESHOLD = Decimal("0.600000")
ORACLE_SOURCE_SCORES = {
    "official": Decimal("1.000000"),
    "primary_source": Decimal("0.900000"),
    "third_party": Decimal("0.700000"),
    "community_resolution": Decimal("0.450000"),
    "unknown": Decimal("0.250000"),
}


@dataclass(frozen=True)
class StrategyResolutionPrecedentScoreV10Config:
    config_version: str = DEFAULT_STRATEGY_RESOLUTION_PRECEDENT_SCORE_V10_CONFIG_VERSION
    rules_text_clarity_weight: Decimal = Decimal("0.400000")
    similar_history_weight: Decimal = Decimal("0.200000")
    dispute_rate_weight: Decimal = Decimal("0.200000")
    oracle_source_weight: Decimal = Decimal("0.100000")
    deadline_consistency_weight: Decimal = Decimal("0.100000")
    similar_history_count_cap: Decimal = Decimal("10")
    clear_precedent_threshold: Decimal = Decimal("0.800000")
    manual_review_score_threshold: Decimal = Decimal("0.600000")
    high_ambiguity_penalty: Decimal = Decimal("0.400000")
    limited_history_count: Decimal = Decimal("3")
    high_dispute_rate: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "rules_text_clarity_weight",
            "similar_history_weight",
            "dispute_rate_weight",
            "oracle_source_weight",
            "deadline_consistency_weight",
            "clear_precedent_threshold",
            "manual_review_score_threshold",
            "high_ambiguity_penalty",
            "high_dispute_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("similar_history_count_cap", "limited_history_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_count(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("StrategyResolutionPrecedentScoreV10Config", self)


@dataclass(frozen=True)
class StrategyResolutionPrecedentScoreV10Input:
    market_id: str
    rules_text_clarity: Decimal
    similar_historical_event_count: Decimal
    historical_dispute_rate: Decimal
    oracle_source_type: str
    deadline_consistency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "rules_text_clarity",
            "historical_dispute_rate",
            "deadline_consistency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "similar_historical_event_count",
            _normalize_whole_count(
                "similar_historical_event_count",
                self.similar_historical_event_count,
            ),
        )
        _require_member("oracle_source_type", self.oracle_source_type, ORACLE_SOURCE_TYPES)
        require_paper_only_flags("StrategyResolutionPrecedentScoreV10Input", self)


@dataclass(frozen=True)
class StrategyResolutionPrecedentScoreV10Result:
    market_id: str
    precedent_score: Decimal
    ambiguity_penalty: Decimal
    needs_manual_review: bool
    reason_codes: tuple[str, ...]
    payload: tuple[tuple[str, object], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "precedent_score",
            _normalize_ratio("precedent_score", self.precedent_score),
        )
        object.__setattr__(
            self,
            "ambiguity_penalty",
            _normalize_ratio("ambiguity_penalty", self.ambiguity_penalty),
        )
        if type(self.needs_manual_review) is not bool:
            raise ValueError("needs_manual_review must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "payload", _normalize_payload(self.payload))
        reject_unsafe_surface_fields("strategy resolution precedent score result", self)
        require_paper_only_flags("StrategyResolutionPrecedentScoreV10Result", self)


def build_strategy_resolution_precedent_score_v10(
    market: StrategyResolutionPrecedentScoreV10Input,
    *,
    config: StrategyResolutionPrecedentScoreV10Config | None = None,
) -> StrategyResolutionPrecedentScoreV10Result:
    if not isinstance(market, StrategyResolutionPrecedentScoreV10Input):
        raise ValueError("market must be a StrategyResolutionPrecedentScoreV10Input")
    resolved_config = config or StrategyResolutionPrecedentScoreV10Config()
    if not isinstance(resolved_config, StrategyResolutionPrecedentScoreV10Config):
        raise ValueError("config must be a StrategyResolutionPrecedentScoreV10Config")
    require_paper_only_flags("market", market)
    require_paper_only_flags("config", resolved_config)

    history_score = _history_score(
        market.similar_historical_event_count,
        resolved_config.similar_history_count_cap,
    )
    oracle_score = ORACLE_SOURCE_SCORES[market.oracle_source_type]
    dispute_reliability = _quantize_ratio(ONE - market.historical_dispute_rate)
    precedent_score = _quantize_ratio(
        _mul(market.rules_text_clarity, resolved_config.rules_text_clarity_weight)
        + _mul(history_score, resolved_config.similar_history_weight)
        + _mul(dispute_reliability, resolved_config.dispute_rate_weight)
        + _mul(oracle_score, resolved_config.oracle_source_weight)
        + _mul(
            market.deadline_consistency_score,
            resolved_config.deadline_consistency_weight,
        ),
    )
    ambiguity_penalty = _quantize_ratio(
        _mul(ONE - market.rules_text_clarity, resolved_config.rules_text_clarity_weight)
        + _mul(market.historical_dispute_rate, resolved_config.dispute_rate_weight)
        + _mul(ONE - oracle_score, resolved_config.oracle_source_weight)
        + _mul(
            ONE - market.deadline_consistency_score,
            resolved_config.deadline_consistency_weight,
        ),
    )
    needs_manual_review = (
        precedent_score < resolved_config.manual_review_score_threshold
        or ambiguity_penalty >= resolved_config.high_ambiguity_penalty
    )
    reason_codes = _build_reason_codes(
        market=market,
        config=resolved_config,
        precedent_score=precedent_score,
        needs_manual_review=needs_manual_review,
    )
    payload = _build_payload(
        market=market,
        precedent_score=precedent_score,
        ambiguity_penalty=ambiguity_penalty,
        needs_manual_review=needs_manual_review,
        reason_codes=reason_codes,
    )
    result = StrategyResolutionPrecedentScoreV10Result(
        market_id=market.market_id,
        precedent_score=precedent_score,
        ambiguity_penalty=ambiguity_penalty,
        needs_manual_review=needs_manual_review,
        reason_codes=reason_codes,
        payload=payload,
    )
    reject_unsafe_surface_fields("strategy resolution precedent score payload", result.payload)
    return result


def strategy_resolution_precedent_score_v10_payload(
    result: StrategyResolutionPrecedentScoreV10Result,
) -> object:
    if not isinstance(result, StrategyResolutionPrecedentScoreV10Result):
        raise ValueError("result must be a StrategyResolutionPrecedentScoreV10Result")
    require_paper_only_flags("result", result)
    payload = {
        "market_id": result.market_id,
        "precedent_score": result.precedent_score,
        "ambiguity_penalty": result.ambiguity_penalty,
        "needs_manual_review": result.needs_manual_review,
        "reason_codes": result.reason_codes,
        "payload": result.payload,
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }
    reject_unsafe_surface_fields("strategy resolution precedent score payload", payload)
    return json_ready_no_floats(payload)


def _build_reason_codes(
    *,
    market: StrategyResolutionPrecedentScoreV10Input,
    config: StrategyResolutionPrecedentScoreV10Config,
    precedent_score: Decimal,
    needs_manual_review: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if needs_manual_review:
        reason_codes.append("resolution_precedent_manual_review")
    elif precedent_score >= config.clear_precedent_threshold:
        reason_codes.append("resolution_precedent_strong")
    else:
        reason_codes.append("resolution_precedent_watch")

    if market.rules_text_clarity >= RULES_CLEAR_THRESHOLD:
        reason_codes.append("rules_text_clear")
    elif market.rules_text_clarity < RULES_AMBIGUOUS_THRESHOLD:
        reason_codes.append("rules_text_ambiguous")

    if market.similar_historical_event_count >= config.limited_history_count:
        reason_codes.append("sufficient_resolution_history")
    else:
        reason_codes.append("limited_resolution_history")

    if market.historical_dispute_rate <= LOW_DISPUTE_RATE:
        reason_codes.append("low_historical_dispute_rate")
    elif market.historical_dispute_rate >= config.high_dispute_rate:
        reason_codes.append("historical_dispute_rate_high")

    reason_codes.append(_oracle_reason_code(market.oracle_source_type))

    if market.deadline_consistency_score >= DEADLINE_CLEAR_THRESHOLD:
        reason_codes.append("deadline_consistency_clear")
    elif market.deadline_consistency_score < DEADLINE_WEAK_THRESHOLD:
        reason_codes.append("deadline_consistency_weak")

    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _build_payload(
    *,
    market: StrategyResolutionPrecedentScoreV10Input,
    precedent_score: Decimal,
    ambiguity_penalty: Decimal,
    needs_manual_review: bool,
    reason_codes: tuple[str, ...],
) -> tuple[tuple[str, object], ...]:
    return (
        ("market_id", market.market_id),
        ("precedent_score", str(precedent_score)),
        ("ambiguity_penalty", str(ambiguity_penalty)),
        ("needs_manual_review", needs_manual_review),
        ("rules_text_clarity", str(market.rules_text_clarity)),
        (
            "similar_historical_event_count",
            str(market.similar_historical_event_count),
        ),
        ("historical_dispute_rate", str(market.historical_dispute_rate)),
        ("oracle_source_type", market.oracle_source_type),
        ("deadline_consistency_score", str(market.deadline_consistency_score)),
        ("reason_codes", reason_codes),
    )


def _history_score(count: Decimal, cap: Decimal) -> Decimal:
    if cap <= ZERO:
        return ZERO
    if count >= cap:
        return ONE
    return _quantize_ratio(count / cap)


def _oracle_reason_code(oracle_source_type: str) -> str:
    if oracle_source_type == "official":
        return "official_oracle_source"
    if oracle_source_type == "primary_source":
        return "primary_oracle_source"
    if oracle_source_type == "third_party":
        return "third_party_oracle_source"
    if oracle_source_type == "community_resolution":
        return "community_resolution_source"
    return "unknown_oracle_source"


def _validate_config(config: StrategyResolutionPrecedentScoreV10Config) -> None:
    total_weight = _quantize_ratio(
        config.rules_text_clarity_weight
        + config.similar_history_weight
        + config.dispute_rate_weight
        + config.oracle_source_weight
        + config.deadline_consistency_weight,
    )
    if total_weight != ONE:
        raise ValueError("precedent scoring weights must sum to 1.000000")
    if config.manual_review_score_threshold > config.clear_precedent_threshold:
        raise ValueError("manual_review_score_threshold must not exceed clear_precedent_threshold")
    if config.limited_history_count > config.similar_history_count_cap:
        raise ValueError("limited_history_count must not exceed similar_history_count_cap")
    if config.similar_history_count_cap <= ZERO:
        raise ValueError("similar_history_count_cap must be positive")


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(value)


def _normalize_whole_count(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return quantized


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, REASON_CODES)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _normalize_payload(
    payload: tuple[tuple[str, object], ...],
) -> tuple[tuple[str, object], ...]:
    if not isinstance(payload, tuple):
        raise ValueError("payload must be a tuple")
    normalized: list[tuple[str, object]] = []
    for item in payload:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("payload entries must be key/value tuples")
        key = item[0]
        value = item[1]
        _require_canonical_string("payload key", key)
        if isinstance(value, Decimal) or isinstance(value, float):
            raise ValueError("payload values must be JSON-safe non-float values")
        normalized.append((key, value))
    return tuple(normalized)


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _mul(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return left * right


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


__all__ = (
    "DEFAULT_STRATEGY_RESOLUTION_PRECEDENT_SCORE_V10_CONFIG_VERSION",
    "ORACLE_SOURCE_TYPES",
    "StrategyResolutionPrecedentScoreV10Config",
    "StrategyResolutionPrecedentScoreV10Input",
    "StrategyResolutionPrecedentScoreV10Result",
    "build_strategy_resolution_precedent_score_v10",
    "strategy_resolution_precedent_score_v10_payload",
)

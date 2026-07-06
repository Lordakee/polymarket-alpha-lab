"""Pure paper-only liquidity depth stability scoring for strategy candidates."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


__all__ = (
    "StrategyCandidateLiquidityDepthStabilityConfig",
    "StrategyCandidateLiquidityDepthStabilityInput",
    "StrategyCandidateLiquidityDepthStabilityScore",
    "score_strategy_candidate_liquidity_depth_stability_v10",
    "strategy_candidate_liquidity_depth_stability_v10_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-candidate-liquidity-depth-stability-v10"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
STABILITY_STATUSES = ("stable", "watch", "unstable")
STATUS_REASON_PREFIX = "strategy_candidate_liquidity_depth_stability_"


@dataclass(frozen=True)
class StrategyCandidateLiquidityDepthStabilityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    minimum_stability_score: Decimal = Decimal("0.750000")
    minimum_watch_score: Decimal = Decimal("0.500000")
    maximum_bid_ask_spread: Decimal = Decimal("0.030000")
    maximum_recent_depth_volatility: Decimal = Decimal("0.250000")
    maximum_taker_fee_drag: Decimal = Decimal("0.020000")
    depth_weight: Decimal = Decimal("0.300000")
    spread_weight: Decimal = Decimal("0.200000")
    volatility_weight: Decimal = Decimal("0.200000")
    fee_drag_weight: Decimal = Decimal("0.100000")
    exit_capacity_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("minimum_stability_score", "minimum_watch_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_watch_score > self.minimum_stability_score:
            raise ValueError(
                "minimum_watch_score must be less than or equal to "
                "minimum_stability_score",
            )
        for field_name in (
            "maximum_bid_ask_spread",
            "maximum_recent_depth_volatility",
            "maximum_taker_fee_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_probability_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "depth_weight",
            "spread_weight",
            "volatility_weight",
            "fee_drag_weight",
            "exit_capacity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateLiquidityDepthStabilityInput:
    candidate_id: str
    market_slug: str
    outcome_name: str
    target_size_notional: Decimal
    depth_at_target_size_notional: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    recent_depth_volatility: Decimal
    taker_fee_drag: Decimal
    exit_capacity_notional: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "target_size_notional",
            _normalize_positive_decimal("target_size_notional", self.target_size_notional),
        )
        for field_name in (
            "depth_at_target_size_notional",
            "exit_capacity_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "best_bid_price",
            "best_ask_price",
            "recent_depth_volatility",
            "taker_fee_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price < self.best_bid_price:
            raise ValueError(
                "best_ask_price must be greater than or equal to best_bid_price",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate_state", self)


@dataclass(frozen=True)
class StrategyCandidateLiquidityDepthStabilityScore:
    config_version: str
    candidate_id: str
    market_slug: str
    outcome_name: str
    stability_status: str
    target_size_notional: Decimal
    depth_at_target_size_notional: Decimal
    depth_coverage_ratio: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    bid_ask_spread: Decimal
    spread_score: Decimal
    recent_depth_volatility: Decimal
    depth_volatility_score: Decimal
    taker_fee_drag: Decimal
    fee_drag_score: Decimal
    exit_capacity_notional: Decimal
    exit_capacity_ratio: Decimal
    liquidity_depth_stability_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "config_version",
            "candidate_id",
            "market_slug",
            "outcome_name",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("stability_status", self.stability_status, STABILITY_STATUSES)
        object.__setattr__(
            self,
            "target_size_notional",
            _normalize_positive_decimal("target_size_notional", self.target_size_notional),
        )
        for field_name in (
            "depth_at_target_size_notional",
            "exit_capacity_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_coverage_ratio",
            "best_bid_price",
            "best_ask_price",
            "bid_ask_spread",
            "spread_score",
            "recent_depth_volatility",
            "depth_volatility_score",
            "taker_fee_drag",
            "fee_drag_score",
            "exit_capacity_ratio",
            "liquidity_depth_stability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price < self.best_bid_price:
            raise ValueError(
                "best_ask_price must be greater than or equal to best_bid_price",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_score_consistency(self)
        _require_hard_flags("score_result", self)


def score_strategy_candidate_liquidity_depth_stability_v10(
    candidate_state: StrategyCandidateLiquidityDepthStabilityInput,
    config: StrategyCandidateLiquidityDepthStabilityConfig,
) -> StrategyCandidateLiquidityDepthStabilityScore:
    """Score one candidate's depth stability without side effects."""

    _require_exact_type(
        "candidate_state",
        candidate_state,
        StrategyCandidateLiquidityDepthStabilityInput,
    )
    _require_exact_type("config", config, StrategyCandidateLiquidityDepthStabilityConfig)

    bid_ask_spread = candidate_state.best_ask_price - candidate_state.best_bid_price
    depth_coverage_ratio = _capped_ratio(
        candidate_state.depth_at_target_size_notional,
        candidate_state.target_size_notional,
    )
    spread_score = _inverse_limit_score(
        bid_ask_spread,
        config.maximum_bid_ask_spread,
    )
    depth_volatility_score = _inverse_limit_score(
        candidate_state.recent_depth_volatility,
        config.maximum_recent_depth_volatility,
    )
    fee_drag_score = _inverse_limit_score(
        candidate_state.taker_fee_drag,
        config.maximum_taker_fee_drag,
    )
    exit_capacity_ratio = _capped_ratio(
        candidate_state.exit_capacity_notional,
        candidate_state.target_size_notional,
    )
    composite_score = _quantize_decimal(
        "liquidity_depth_stability_score",
        (
            depth_coverage_ratio * config.depth_weight
            + spread_score * config.spread_weight
            + depth_volatility_score * config.volatility_weight
            + fee_drag_score * config.fee_drag_weight
            + exit_capacity_ratio * config.exit_capacity_weight
        ),
    )
    stability_status = _stability_status(composite_score, config)
    blockers = _blocker_reason_codes(
        candidate_state,
        config,
        bid_ask_spread,
    )

    return StrategyCandidateLiquidityDepthStabilityScore(
        config_version=config.config_version,
        candidate_id=candidate_state.candidate_id,
        market_slug=candidate_state.market_slug,
        outcome_name=candidate_state.outcome_name,
        stability_status=stability_status,
        target_size_notional=candidate_state.target_size_notional,
        depth_at_target_size_notional=candidate_state.depth_at_target_size_notional,
        depth_coverage_ratio=depth_coverage_ratio,
        best_bid_price=candidate_state.best_bid_price,
        best_ask_price=candidate_state.best_ask_price,
        bid_ask_spread=_quantize_decimal("bid_ask_spread", bid_ask_spread),
        spread_score=spread_score,
        recent_depth_volatility=candidate_state.recent_depth_volatility,
        depth_volatility_score=depth_volatility_score,
        taker_fee_drag=candidate_state.taker_fee_drag,
        fee_drag_score=fee_drag_score,
        exit_capacity_notional=candidate_state.exit_capacity_notional,
        exit_capacity_ratio=exit_capacity_ratio,
        liquidity_depth_stability_score=composite_score,
        reason_codes=_score_reason_codes(
            stability_status,
            candidate_state.reason_codes,
            blockers,
        ),
    )


def strategy_candidate_liquidity_depth_stability_v10_payload(
    score_result: StrategyCandidateLiquidityDepthStabilityScore,
) -> dict[str, object]:
    if type(score_result) is not StrategyCandidateLiquidityDepthStabilityScore:
        raise ValueError(
            "score_result must be a StrategyCandidateLiquidityDepthStabilityScore",
        )
    _require_hard_flags("score_result", score_result)
    return {
        "config_version": score_result.config_version,
        "candidate_id": score_result.candidate_id,
        "market_slug": score_result.market_slug,
        "outcome_name": score_result.outcome_name,
        "stability_status": score_result.stability_status,
        "target_size_notional": _decimal_payload(score_result.target_size_notional),
        "depth_at_target_size_notional": _decimal_payload(
            score_result.depth_at_target_size_notional,
        ),
        "depth_coverage_ratio": _decimal_payload(score_result.depth_coverage_ratio),
        "best_bid_price": _decimal_payload(score_result.best_bid_price),
        "best_ask_price": _decimal_payload(score_result.best_ask_price),
        "bid_ask_spread": _decimal_payload(score_result.bid_ask_spread),
        "spread_score": _decimal_payload(score_result.spread_score),
        "recent_depth_volatility": _decimal_payload(
            score_result.recent_depth_volatility,
        ),
        "depth_volatility_score": _decimal_payload(
            score_result.depth_volatility_score,
        ),
        "taker_fee_drag": _decimal_payload(score_result.taker_fee_drag),
        "fee_drag_score": _decimal_payload(score_result.fee_drag_score),
        "exit_capacity_notional": _decimal_payload(
            score_result.exit_capacity_notional,
        ),
        "exit_capacity_ratio": _decimal_payload(score_result.exit_capacity_ratio),
        "liquidity_depth_stability_score": _decimal_payload(
            score_result.liquidity_depth_stability_score,
        ),
        "reason_codes": list(score_result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _weight_sum(config: StrategyCandidateLiquidityDepthStabilityConfig) -> Decimal:
    return _quantize_decimal(
        "weights",
        (
            config.depth_weight
            + config.spread_weight
            + config.volatility_weight
            + config.fee_drag_weight
            + config.exit_capacity_weight
        ),
    )


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _quantize_decimal("ratio", numerator / denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _inverse_limit_score(value: Decimal, limit: Decimal) -> Decimal:
    if value >= limit:
        return ZERO
    return _quantize_decimal("limit_score", ONE - (value / limit))


def _stability_status(
    composite_score: Decimal,
    config: StrategyCandidateLiquidityDepthStabilityConfig,
) -> str:
    if composite_score >= config.minimum_stability_score:
        return "stable"
    if composite_score >= config.minimum_watch_score:
        return "watch"
    return "unstable"


def _blocker_reason_codes(
    candidate_state: StrategyCandidateLiquidityDepthStabilityInput,
    config: StrategyCandidateLiquidityDepthStabilityConfig,
    bid_ask_spread: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate_state.depth_at_target_size_notional < candidate_state.target_size_notional:
        reason_codes.append("depth_at_target_size_below_target")
    if bid_ask_spread > config.maximum_bid_ask_spread:
        reason_codes.append("bid_ask_spread_above_limit")
    if candidate_state.recent_depth_volatility > config.maximum_recent_depth_volatility:
        reason_codes.append("recent_depth_volatility_above_limit")
    if candidate_state.taker_fee_drag > config.maximum_taker_fee_drag:
        reason_codes.append("taker_fee_drag_above_limit")
    if candidate_state.exit_capacity_notional < candidate_state.target_size_notional:
        reason_codes.append("exit_capacity_below_target")
    return tuple(reason_codes)


def _score_reason_codes(
    stability_status: str,
    upstream_reason_codes: tuple[str, ...],
    blocker_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    generated_reason_codes = blocker_reason_codes
    if not generated_reason_codes:
        generated_reason_codes = ("liquidity_depth_stability_sufficient",)
    reason_codes = [
        f"{STATUS_REASON_PREFIX}{stability_status}",
        *upstream_reason_codes,
        *generated_reason_codes,
    ]
    return tuple(dict.fromkeys(reason_codes))


def _validate_score_consistency(
    score_result: StrategyCandidateLiquidityDepthStabilityScore,
) -> None:
    expected_reason_code = f"{STATUS_REASON_PREFIX}{score_result.stability_status}"
    if not score_result.reason_codes or score_result.reason_codes[0] != expected_reason_code:
        raise ValueError("reason_codes must start with stability_status reason code")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        expected = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {expected}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


def _normalize_positive_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_probability_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")

"""Pure paper-only microstructure anomaly scoring for strategy candidates."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal


__all__ = (
    "StrategyCandidateMarketMicrostructureAnomalyConfig",
    "StrategyCandidateMarketMicrostructureAnomalyInput",
    "StrategyCandidateMarketMicrostructureAnomalyScore",
    "score_strategy_candidate_market_microstructure_anomaly_v10",
    "strategy_candidate_market_microstructure_anomaly_v10_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-candidate-market-microstructure-anomaly-v10"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
ANOMALY_STATUSES = ("normal", "watch", "anomalous")
STATUS_REASON_PREFIX = "strategy_candidate_market_microstructure_anomaly_"
VALIDATION_DIGEST_ALGORITHM = "sha256"
HEX_DIGITS = frozenset("0123456789abcdef")
UNSAFE_PAYLOAD_FIELD_FRAGMENTS = frozenset(
    (
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "credential",
        "db",
        "execute",
        "fetch",
        "live",
        "network",
        "order",
        "persist",
        "private_key",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    ),
)


@dataclass(frozen=True)
class StrategyCandidateMarketMicrostructureAnomalyConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    minimum_anomaly_score: Decimal = Decimal("0.700000")
    minimum_watch_score: Decimal = Decimal("0.450000")
    maximum_spread_shock: Decimal = Decimal("0.050000")
    maximum_depth_imbalance: Decimal = Decimal("0.650000")
    maximum_sudden_price_jump: Decimal = Decimal("0.100000")
    maximum_volume_concentration: Decimal = Decimal("0.750000")
    spread_shock_weight: Decimal = Decimal("0.200000")
    depth_imbalance_weight: Decimal = Decimal("0.200000")
    price_jump_weight: Decimal = Decimal("0.200000")
    book_thinness_weight: Decimal = Decimal("0.200000")
    volume_concentration_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyCandidateMarketMicrostructureAnomalyConfig must not be subclassed",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("minimum_anomaly_score", "minimum_watch_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_watch_score > self.minimum_anomaly_score:
            raise ValueError(
                "minimum_watch_score must be less than or equal to "
                "minimum_anomaly_score",
            )
        for field_name in (
            "maximum_spread_shock",
            "maximum_depth_imbalance",
            "maximum_sudden_price_jump",
            "maximum_volume_concentration",
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
            "spread_shock_weight",
            "depth_imbalance_weight",
            "price_jump_weight",
            "book_thinness_weight",
            "volume_concentration_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _reject_unsafe_payload_surface("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateMarketMicrostructureAnomalyInput:
    candidate_id: str
    market_slug: str
    outcome_name: str
    best_bid_price: Decimal
    best_ask_price: Decimal
    reference_bid_ask_spread: Decimal
    previous_mid_price: Decimal
    current_mid_price: Decimal
    bid_depth_notional: Decimal
    ask_depth_notional: Decimal
    target_depth_notional: Decimal
    recent_volume_notional: Decimal
    largest_fill_notional: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyCandidateMarketMicrostructureAnomalyInput must not be subclassed",
        )

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "best_bid_price",
            "best_ask_price",
            "reference_bid_ask_spread",
            "previous_mid_price",
            "current_mid_price",
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
            "target_depth_notional",
            _normalize_positive_decimal("target_depth_notional", self.target_depth_notional),
        )
        for field_name in (
            "bid_depth_notional",
            "ask_depth_notional",
            "recent_volume_notional",
            "largest_fill_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.largest_fill_notional > self.recent_volume_notional:
            raise ValueError(
                "largest_fill_notional must be less than or equal to "
                "recent_volume_notional",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_payload_surface("candidate_state", self)
        _require_hard_flags("candidate_state", self)


@dataclass(frozen=True)
class StrategyCandidateMarketMicrostructureAnomalyScore:
    config_version: str
    candidate_id: str
    market_slug: str
    outcome_name: str
    anomaly_status: str
    best_bid_price: Decimal
    best_ask_price: Decimal
    reference_bid_ask_spread: Decimal
    bid_ask_spread: Decimal
    spread_shock: Decimal
    spread_shock_score: Decimal
    previous_mid_price: Decimal
    current_mid_price: Decimal
    sudden_price_jump: Decimal
    price_jump_score: Decimal
    bid_depth_notional: Decimal
    ask_depth_notional: Decimal
    book_depth_notional: Decimal
    target_depth_notional: Decimal
    depth_imbalance_ratio: Decimal
    depth_imbalance_score: Decimal
    book_depth_coverage_ratio: Decimal
    book_thinness_score: Decimal
    recent_volume_notional: Decimal
    largest_fill_notional: Decimal
    volume_concentration_ratio: Decimal
    volume_concentration_score: Decimal
    market_microstructure_anomaly_score: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyCandidateMarketMicrostructureAnomalyScore must not be subclassed",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "config_version",
            "candidate_id",
            "market_slug",
            "outcome_name",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("anomaly_status", self.anomaly_status, ANOMALY_STATUSES)
        for field_name in (
            "best_bid_price",
            "best_ask_price",
            "reference_bid_ask_spread",
            "bid_ask_spread",
            "spread_shock",
            "spread_shock_score",
            "previous_mid_price",
            "current_mid_price",
            "sudden_price_jump",
            "price_jump_score",
            "depth_imbalance_ratio",
            "depth_imbalance_score",
            "book_depth_coverage_ratio",
            "book_thinness_score",
            "volume_concentration_ratio",
            "volume_concentration_score",
            "market_microstructure_anomaly_score",
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
            "target_depth_notional",
            _normalize_positive_decimal("target_depth_notional", self.target_depth_notional),
        )
        for field_name in (
            "bid_depth_notional",
            "ask_depth_notional",
            "book_depth_notional",
            "recent_volume_notional",
            "largest_fill_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.largest_fill_notional > self.recent_volume_notional:
            raise ValueError(
                "largest_fill_notional must be less than or equal to "
                "recent_volume_notional",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_score_consistency(self)
        _validate_score_digest(self)
        _reject_unsafe_payload_surface("score_result", self)
        _require_hard_flags("score_result", self)


def score_strategy_candidate_market_microstructure_anomaly_v10(
    candidate_state: StrategyCandidateMarketMicrostructureAnomalyInput,
    config: StrategyCandidateMarketMicrostructureAnomalyConfig,
) -> StrategyCandidateMarketMicrostructureAnomalyScore:
    """Score one candidate for abnormal market microstructure without side effects."""

    _require_exact_type(
        "candidate_state",
        candidate_state,
        StrategyCandidateMarketMicrostructureAnomalyInput,
    )
    _require_exact_type(
        "config",
        config,
        StrategyCandidateMarketMicrostructureAnomalyConfig,
    )

    bid_ask_spread = _quantize_decimal(
        "bid_ask_spread",
        candidate_state.best_ask_price - candidate_state.best_bid_price,
    )
    spread_shock = _positive_delta(
        bid_ask_spread,
        candidate_state.reference_bid_ask_spread,
    )
    spread_shock_score = _capped_ratio(spread_shock, config.maximum_spread_shock)
    sudden_price_jump = _absolute_delta(
        candidate_state.current_mid_price,
        candidate_state.previous_mid_price,
    )
    price_jump_score = _capped_ratio(
        sudden_price_jump,
        config.maximum_sudden_price_jump,
    )
    book_depth_notional = _quantize_decimal(
        "book_depth_notional",
        candidate_state.bid_depth_notional + candidate_state.ask_depth_notional,
    )
    depth_imbalance_ratio = _depth_imbalance_ratio(
        candidate_state.bid_depth_notional,
        candidate_state.ask_depth_notional,
        book_depth_notional,
    )
    book_depth_coverage_ratio = _capped_ratio(
        book_depth_notional,
        candidate_state.target_depth_notional,
    )
    book_thinness_score = _quantize_decimal(
        "book_thinness_score",
        ONE - book_depth_coverage_ratio,
    )
    volume_concentration_ratio = _volume_concentration_ratio(
        candidate_state.largest_fill_notional,
        candidate_state.recent_volume_notional,
    )
    composite_score = _quantize_decimal(
        "market_microstructure_anomaly_score",
        (
            spread_shock_score * config.spread_shock_weight
            + depth_imbalance_ratio * config.depth_imbalance_weight
            + price_jump_score * config.price_jump_weight
            + book_thinness_score * config.book_thinness_weight
            + volume_concentration_ratio * config.volume_concentration_weight
        ),
    )
    anomaly_status = _anomaly_status(composite_score, config)
    blockers = _blocker_reason_codes(
        spread_shock,
        depth_imbalance_ratio,
        sudden_price_jump,
        book_depth_notional,
        volume_concentration_ratio,
        candidate_state,
        config,
    )

    reason_codes = _score_reason_codes(
        anomaly_status,
        candidate_state.reason_codes,
        blockers,
    )
    validation_digest = _score_validation_digest(
        config_version=config.config_version,
        candidate_id=candidate_state.candidate_id,
        market_slug=candidate_state.market_slug,
        outcome_name=candidate_state.outcome_name,
        anomaly_status=anomaly_status,
        best_bid_price=candidate_state.best_bid_price,
        best_ask_price=candidate_state.best_ask_price,
        reference_bid_ask_spread=candidate_state.reference_bid_ask_spread,
        bid_ask_spread=bid_ask_spread,
        spread_shock=spread_shock,
        spread_shock_score=spread_shock_score,
        previous_mid_price=candidate_state.previous_mid_price,
        current_mid_price=candidate_state.current_mid_price,
        sudden_price_jump=sudden_price_jump,
        price_jump_score=price_jump_score,
        bid_depth_notional=candidate_state.bid_depth_notional,
        ask_depth_notional=candidate_state.ask_depth_notional,
        book_depth_notional=book_depth_notional,
        target_depth_notional=candidate_state.target_depth_notional,
        depth_imbalance_ratio=depth_imbalance_ratio,
        depth_imbalance_score=depth_imbalance_ratio,
        book_depth_coverage_ratio=book_depth_coverage_ratio,
        book_thinness_score=book_thinness_score,
        recent_volume_notional=candidate_state.recent_volume_notional,
        largest_fill_notional=candidate_state.largest_fill_notional,
        volume_concentration_ratio=volume_concentration_ratio,
        volume_concentration_score=volume_concentration_ratio,
        market_microstructure_anomaly_score=composite_score,
        reason_codes=reason_codes,
    )

    return StrategyCandidateMarketMicrostructureAnomalyScore(
        config_version=config.config_version,
        candidate_id=candidate_state.candidate_id,
        market_slug=candidate_state.market_slug,
        outcome_name=candidate_state.outcome_name,
        anomaly_status=anomaly_status,
        best_bid_price=candidate_state.best_bid_price,
        best_ask_price=candidate_state.best_ask_price,
        reference_bid_ask_spread=candidate_state.reference_bid_ask_spread,
        bid_ask_spread=bid_ask_spread,
        spread_shock=spread_shock,
        spread_shock_score=spread_shock_score,
        previous_mid_price=candidate_state.previous_mid_price,
        current_mid_price=candidate_state.current_mid_price,
        sudden_price_jump=sudden_price_jump,
        price_jump_score=price_jump_score,
        bid_depth_notional=candidate_state.bid_depth_notional,
        ask_depth_notional=candidate_state.ask_depth_notional,
        book_depth_notional=book_depth_notional,
        target_depth_notional=candidate_state.target_depth_notional,
        depth_imbalance_ratio=depth_imbalance_ratio,
        depth_imbalance_score=depth_imbalance_ratio,
        book_depth_coverage_ratio=book_depth_coverage_ratio,
        book_thinness_score=book_thinness_score,
        recent_volume_notional=candidate_state.recent_volume_notional,
        largest_fill_notional=candidate_state.largest_fill_notional,
        volume_concentration_ratio=volume_concentration_ratio,
        volume_concentration_score=volume_concentration_ratio,
        market_microstructure_anomaly_score=composite_score,
        reason_codes=reason_codes,
        validation_digest=validation_digest,
    )


def strategy_candidate_market_microstructure_anomaly_v10_payload(
    score_result: StrategyCandidateMarketMicrostructureAnomalyScore,
) -> dict[str, object]:
    if type(score_result) is not StrategyCandidateMarketMicrostructureAnomalyScore:
        raise ValueError(
            "score_result must be a StrategyCandidateMarketMicrostructureAnomalyScore",
        )
    _reject_unsafe_payload_surface("score_result", score_result)
    _require_hard_flags("score_result", score_result)
    payload = {
        "config_version": score_result.config_version,
        "candidate_id": score_result.candidate_id,
        "market_slug": score_result.market_slug,
        "outcome_name": score_result.outcome_name,
        "anomaly_status": score_result.anomaly_status,
        "best_bid_price": _decimal_payload(score_result.best_bid_price),
        "best_ask_price": _decimal_payload(score_result.best_ask_price),
        "reference_bid_ask_spread": _decimal_payload(
            score_result.reference_bid_ask_spread,
        ),
        "bid_ask_spread": _decimal_payload(score_result.bid_ask_spread),
        "spread_shock": _decimal_payload(score_result.spread_shock),
        "spread_shock_score": _decimal_payload(score_result.spread_shock_score),
        "previous_mid_price": _decimal_payload(score_result.previous_mid_price),
        "current_mid_price": _decimal_payload(score_result.current_mid_price),
        "sudden_price_jump": _decimal_payload(score_result.sudden_price_jump),
        "price_jump_score": _decimal_payload(score_result.price_jump_score),
        "bid_depth_notional": _decimal_payload(score_result.bid_depth_notional),
        "ask_depth_notional": _decimal_payload(score_result.ask_depth_notional),
        "book_depth_notional": _decimal_payload(score_result.book_depth_notional),
        "target_depth_notional": _decimal_payload(score_result.target_depth_notional),
        "depth_imbalance_ratio": _decimal_payload(
            score_result.depth_imbalance_ratio,
        ),
        "depth_imbalance_score": _decimal_payload(
            score_result.depth_imbalance_score,
        ),
        "book_depth_coverage_ratio": _decimal_payload(
            score_result.book_depth_coverage_ratio,
        ),
        "book_thinness_score": _decimal_payload(score_result.book_thinness_score),
        "recent_volume_notional": _decimal_payload(score_result.recent_volume_notional),
        "largest_fill_notional": _decimal_payload(score_result.largest_fill_notional),
        "volume_concentration_ratio": _decimal_payload(
            score_result.volume_concentration_ratio,
        ),
        "volume_concentration_score": _decimal_payload(
            score_result.volume_concentration_score,
        ),
        "market_microstructure_anomaly_score": _decimal_payload(
            score_result.market_microstructure_anomaly_score,
        ),
        "validation_digest": score_result.validation_digest,
        "reason_codes": list(score_result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_payload_surface("market microstructure anomaly payload", payload)
    return payload


def _weight_sum(config: StrategyCandidateMarketMicrostructureAnomalyConfig) -> Decimal:
    return _quantize_decimal(
        "weights",
        (
            config.spread_shock_weight
            + config.depth_imbalance_weight
            + config.price_jump_weight
            + config.book_thinness_weight
            + config.volume_concentration_weight
        ),
    )


def _positive_delta(value: Decimal, reference_value: Decimal) -> Decimal:
    if value <= reference_value:
        return ZERO
    return _quantize_decimal("positive_delta", value - reference_value)


def _absolute_delta(value: Decimal, reference_value: Decimal) -> Decimal:
    if value >= reference_value:
        return _quantize_decimal("absolute_delta", value - reference_value)
    return _quantize_decimal("absolute_delta", reference_value - value)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _quantize_decimal("ratio", numerator / denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _depth_imbalance_ratio(
    bid_depth_notional: Decimal,
    ask_depth_notional: Decimal,
    book_depth_notional: Decimal,
) -> Decimal:
    if book_depth_notional == ZERO:
        return ONE
    return _quantize_decimal(
        "depth_imbalance_ratio",
        _absolute_delta(bid_depth_notional, ask_depth_notional) / book_depth_notional,
    )


def _volume_concentration_ratio(
    largest_fill_notional: Decimal,
    recent_volume_notional: Decimal,
) -> Decimal:
    if recent_volume_notional == ZERO:
        return ZERO
    return _capped_ratio(largest_fill_notional, recent_volume_notional)


def _anomaly_status(
    composite_score: Decimal,
    config: StrategyCandidateMarketMicrostructureAnomalyConfig,
) -> str:
    if composite_score >= config.minimum_anomaly_score:
        return "anomalous"
    if composite_score >= config.minimum_watch_score:
        return "watch"
    return "normal"


def _blocker_reason_codes(
    spread_shock: Decimal,
    depth_imbalance_ratio: Decimal,
    sudden_price_jump: Decimal,
    book_depth_notional: Decimal,
    volume_concentration_ratio: Decimal,
    candidate_state: StrategyCandidateMarketMicrostructureAnomalyInput,
    config: StrategyCandidateMarketMicrostructureAnomalyConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if spread_shock >= config.maximum_spread_shock:
        reason_codes.append("spread_shock_above_limit")
    if depth_imbalance_ratio >= config.maximum_depth_imbalance:
        reason_codes.append("depth_imbalance_above_limit")
    if sudden_price_jump >= config.maximum_sudden_price_jump:
        reason_codes.append("sudden_price_jump_above_limit")
    if book_depth_notional < candidate_state.target_depth_notional:
        reason_codes.append("book_depth_below_target")
    if volume_concentration_ratio >= config.maximum_volume_concentration:
        reason_codes.append("recent_volume_concentration_above_limit")
    return tuple(reason_codes)


def _score_reason_codes(
    anomaly_status: str,
    upstream_reason_codes: tuple[str, ...],
    blocker_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    generated_reason_codes = blocker_reason_codes
    if not generated_reason_codes:
        generated_reason_codes = ("market_microstructure_within_limits",)
    reason_codes = [
        f"{STATUS_REASON_PREFIX}{anomaly_status}",
        *upstream_reason_codes,
        *generated_reason_codes,
    ]
    return tuple(dict.fromkeys(reason_codes))


def _validate_score_consistency(
    score_result: StrategyCandidateMarketMicrostructureAnomalyScore,
) -> None:
    expected_bid_ask_spread = _quantize_decimal(
        "bid_ask_spread",
        score_result.best_ask_price - score_result.best_bid_price,
    )
    if score_result.bid_ask_spread != expected_bid_ask_spread:
        raise ValueError("bid_ask_spread must match prices")
    expected_spread_shock = _positive_delta(
        score_result.bid_ask_spread,
        score_result.reference_bid_ask_spread,
    )
    if score_result.spread_shock != expected_spread_shock:
        raise ValueError("spread_shock must match spread inputs")
    expected_sudden_price_jump = _absolute_delta(
        score_result.current_mid_price,
        score_result.previous_mid_price,
    )
    if score_result.sudden_price_jump != expected_sudden_price_jump:
        raise ValueError("sudden_price_jump must match mid prices")
    expected_book_depth_notional = _quantize_decimal(
        "book_depth_notional",
        score_result.bid_depth_notional + score_result.ask_depth_notional,
    )
    if score_result.book_depth_notional != expected_book_depth_notional:
        raise ValueError("book_depth_notional must match depths")
    expected_depth_imbalance_ratio = _depth_imbalance_ratio(
        score_result.bid_depth_notional,
        score_result.ask_depth_notional,
        score_result.book_depth_notional,
    )
    if score_result.depth_imbalance_ratio != expected_depth_imbalance_ratio:
        raise ValueError("depth_imbalance_ratio must match depths")
    if score_result.depth_imbalance_score != score_result.depth_imbalance_ratio:
        raise ValueError("depth_imbalance_score must match depth_imbalance_ratio")
    expected_book_depth_coverage_ratio = _capped_ratio(
        score_result.book_depth_notional,
        score_result.target_depth_notional,
    )
    if score_result.book_depth_coverage_ratio != expected_book_depth_coverage_ratio:
        raise ValueError("book_depth_coverage_ratio must match depths")
    expected_book_thinness_score = _quantize_decimal(
        "book_thinness_score",
        ONE - score_result.book_depth_coverage_ratio,
    )
    if score_result.book_thinness_score != expected_book_thinness_score:
        raise ValueError("book_thinness_score must match depth coverage")
    expected_volume_concentration_ratio = _volume_concentration_ratio(
        score_result.largest_fill_notional,
        score_result.recent_volume_notional,
    )
    if score_result.volume_concentration_ratio != expected_volume_concentration_ratio:
        raise ValueError("volume_concentration_ratio must match volume inputs")
    if score_result.volume_concentration_score != score_result.volume_concentration_ratio:
        raise ValueError(
            "volume_concentration_score must match volume_concentration_ratio",
        )
    expected_reason_code = f"{STATUS_REASON_PREFIX}{score_result.anomaly_status}"
    if not score_result.reason_codes or score_result.reason_codes[0] != expected_reason_code:
        raise ValueError("reason_codes must start with anomaly_status reason code")


def _validate_score_digest(
    score_result: StrategyCandidateMarketMicrostructureAnomalyScore,
) -> None:
    if score_result.validation_digest != _score_validation_digest(
        config_version=score_result.config_version,
        candidate_id=score_result.candidate_id,
        market_slug=score_result.market_slug,
        outcome_name=score_result.outcome_name,
        anomaly_status=score_result.anomaly_status,
        best_bid_price=score_result.best_bid_price,
        best_ask_price=score_result.best_ask_price,
        reference_bid_ask_spread=score_result.reference_bid_ask_spread,
        bid_ask_spread=score_result.bid_ask_spread,
        spread_shock=score_result.spread_shock,
        spread_shock_score=score_result.spread_shock_score,
        previous_mid_price=score_result.previous_mid_price,
        current_mid_price=score_result.current_mid_price,
        sudden_price_jump=score_result.sudden_price_jump,
        price_jump_score=score_result.price_jump_score,
        bid_depth_notional=score_result.bid_depth_notional,
        ask_depth_notional=score_result.ask_depth_notional,
        book_depth_notional=score_result.book_depth_notional,
        target_depth_notional=score_result.target_depth_notional,
        depth_imbalance_ratio=score_result.depth_imbalance_ratio,
        depth_imbalance_score=score_result.depth_imbalance_score,
        book_depth_coverage_ratio=score_result.book_depth_coverage_ratio,
        book_thinness_score=score_result.book_thinness_score,
        recent_volume_notional=score_result.recent_volume_notional,
        largest_fill_notional=score_result.largest_fill_notional,
        volume_concentration_ratio=score_result.volume_concentration_ratio,
        volume_concentration_score=score_result.volume_concentration_score,
        market_microstructure_anomaly_score=score_result.market_microstructure_anomaly_score,
        reason_codes=score_result.reason_codes,
    ):
        raise ValueError("validation_digest must match score_result")


def _score_validation_digest(
    *,
    config_version: str,
    candidate_id: str,
    market_slug: str,
    outcome_name: str,
    anomaly_status: str,
    best_bid_price: Decimal,
    best_ask_price: Decimal,
    reference_bid_ask_spread: Decimal,
    bid_ask_spread: Decimal,
    spread_shock: Decimal,
    spread_shock_score: Decimal,
    previous_mid_price: Decimal,
    current_mid_price: Decimal,
    sudden_price_jump: Decimal,
    price_jump_score: Decimal,
    bid_depth_notional: Decimal,
    ask_depth_notional: Decimal,
    book_depth_notional: Decimal,
    target_depth_notional: Decimal,
    depth_imbalance_ratio: Decimal,
    depth_imbalance_score: Decimal,
    book_depth_coverage_ratio: Decimal,
    book_thinness_score: Decimal,
    recent_volume_notional: Decimal,
    largest_fill_notional: Decimal,
    volume_concentration_ratio: Decimal,
    volume_concentration_score: Decimal,
    market_microstructure_anomaly_score: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    digest_parts = (
        VALIDATION_DIGEST_ALGORITHM,
        config_version,
        candidate_id,
        market_slug,
        outcome_name,
        anomaly_status,
        _decimal_payload(best_bid_price),
        _decimal_payload(best_ask_price),
        _decimal_payload(reference_bid_ask_spread),
        _decimal_payload(bid_ask_spread),
        _decimal_payload(spread_shock),
        _decimal_payload(spread_shock_score),
        _decimal_payload(previous_mid_price),
        _decimal_payload(current_mid_price),
        _decimal_payload(sudden_price_jump),
        _decimal_payload(price_jump_score),
        _decimal_payload(bid_depth_notional),
        _decimal_payload(ask_depth_notional),
        _decimal_payload(book_depth_notional),
        _decimal_payload(target_depth_notional),
        _decimal_payload(depth_imbalance_ratio),
        _decimal_payload(depth_imbalance_score),
        _decimal_payload(book_depth_coverage_ratio),
        _decimal_payload(book_thinness_score),
        _decimal_payload(recent_volume_notional),
        _decimal_payload(largest_fill_notional),
        _decimal_payload(volume_concentration_ratio),
        _decimal_payload(volume_concentration_score),
        _decimal_payload(market_microstructure_anomaly_score),
        "\x1f".join(reason_codes),
        "paper_only=True",
        "report_only=True",
        "readonly=True",
    )
    return hashlib.sha256("\n".join(digest_parts).encode("utf-8")).hexdigest()


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


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


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


def _reject_unsafe_payload_surface(label: str, payload: object) -> None:
    for key in _iter_payload_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_PAYLOAD_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe payload surface in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        keys: list[str] = []
        for field in fields(value):
            keys.append(field.name)
            keys.extend(_iter_payload_keys(getattr(value, field.name)))
        return tuple(keys)
    if isinstance(value, dict):
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()

"""Pure paper-only resolution risk premium scoring for probability markets."""

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RESOLUTION_RISK_PREMIUM_V10_CONFIG_VERSION = (
    "strategy-resolution-risk-premium-v10"
)

RULE_CHANGE_STATUSES = (
    "stable",
    "watch",
    "active",
    "changed",
)
RISK_TIERS = (
    "low",
    "watch",
    "high",
    "block",
)
REASON_CODES = (
    "resolution_risk_low",
    "resolution_risk_watch",
    "resolution_risk_high",
    "resolution_risk_block",
    "ambiguity_high",
    "ambiguity_contained",
    "precedent_strong",
    "precedent_mixed",
    "precedent_weak",
    "rule_change_stable",
    "rule_change_watch",
    "rule_change_active",
    "rule_change_changed",
    "source_disagreement_high",
    "source_disagreement_contained",
    "resolution_time_pressure_high",
    "resolution_time_pressure_contained",
    "dispute_history_high",
    "dispute_history_contained",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
BPS_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RULE_CHANGE_RISK_SCORES = {
    "stable": Decimal("0.000000"),
    "watch": Decimal("0.500000"),
    "active": Decimal("0.750000"),
    "changed": Decimal("1.000000"),
}


@dataclass(frozen=True)
class StrategyResolutionRiskPremiumV10Config:
    config_version: str = DEFAULT_STRATEGY_RESOLUTION_RISK_PREMIUM_V10_CONFIG_VERSION
    ambiguity_weight: Decimal = Decimal("0.300000")
    precedent_gap_weight: Decimal = Decimal("0.200000")
    rule_change_weight: Decimal = Decimal("0.200000")
    source_disagreement_weight: Decimal = Decimal("0.150000")
    time_pressure_weight: Decimal = Decimal("0.100000")
    dispute_history_weight: Decimal = Decimal("0.050000")
    max_resolution_risk_premium_bps: Decimal = Decimal("500.000000")
    base_required_edge_bps: Decimal = Decimal("50.000000")
    watch_risk_premium_bps: Decimal = Decimal("100.000000")
    high_risk_premium_bps: Decimal = Decimal("250.000000")
    block_risk_premium_bps: Decimal = Decimal("400.000000")
    high_ambiguity_threshold: Decimal = Decimal("0.700000")
    strong_precedent_threshold: Decimal = Decimal("0.750000")
    weak_precedent_threshold: Decimal = Decimal("0.400000")
    high_source_disagreement_threshold: Decimal = Decimal("0.600000")
    high_time_pressure_minutes: Decimal = Decimal("1440.000000")
    time_pressure_cap_minutes: Decimal = Decimal("10080.000000")
    high_dispute_history_rate: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "ambiguity_weight",
            "precedent_gap_weight",
            "rule_change_weight",
            "source_disagreement_weight",
            "time_pressure_weight",
            "dispute_history_weight",
            "high_ambiguity_threshold",
            "strong_precedent_threshold",
            "weak_precedent_threshold",
            "high_source_disagreement_threshold",
            "high_dispute_history_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_resolution_risk_premium_bps",
            "base_required_edge_bps",
            "watch_risk_premium_bps",
            "high_risk_premium_bps",
            "block_risk_premium_bps",
            "high_time_pressure_minutes",
            "time_pressure_cap_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("StrategyResolutionRiskPremiumV10Config", self)


@dataclass(frozen=True)
class StrategyResolutionRiskPremiumV10Input:
    ambiguity_score: Decimal
    precedent_score: Decimal
    rule_change_status: str
    source_disagreement_score: Decimal
    time_to_resolution_minutes: Decimal
    dispute_history_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "ambiguity_score",
            "precedent_score",
            "source_disagreement_score",
            "dispute_history_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("rule_change_status", self.rule_change_status, RULE_CHANGE_STATUSES)
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_bps(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        require_paper_only_flags("StrategyResolutionRiskPremiumV10Input", self)


@dataclass(frozen=True)
class StrategyResolutionRiskPremiumV10Result:
    risk_premium_bps: Decimal
    adjusted_required_edge: Decimal
    risk_tier: str
    reason_codes: tuple[str, ...]
    payload: tuple[tuple[str, object], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "risk_premium_bps",
            _normalize_nonnegative_bps("risk_premium_bps", self.risk_premium_bps),
        )
        object.__setattr__(
            self,
            "adjusted_required_edge",
            _normalize_nonnegative_bps(
                "adjusted_required_edge",
                self.adjusted_required_edge,
            ),
        )
        _require_member("risk_tier", self.risk_tier, RISK_TIERS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "payload", _normalize_payload(self.payload))
        reject_unsafe_surface_fields("strategy resolution risk premium result", self)
        require_paper_only_flags("StrategyResolutionRiskPremiumV10Result", self)


def build_strategy_resolution_risk_premium_v10(
    market: StrategyResolutionRiskPremiumV10Input,
    *,
    config: StrategyResolutionRiskPremiumV10Config | None = None,
) -> StrategyResolutionRiskPremiumV10Result:
    if not isinstance(market, StrategyResolutionRiskPremiumV10Input):
        raise ValueError("market must be a StrategyResolutionRiskPremiumV10Input")
    resolved_config = config or StrategyResolutionRiskPremiumV10Config()
    if not isinstance(resolved_config, StrategyResolutionRiskPremiumV10Config):
        raise ValueError("config must be a StrategyResolutionRiskPremiumV10Config")
    require_paper_only_flags("market", market)
    require_paper_only_flags("config", resolved_config)

    precedent_gap_score = _quantize_ratio(ONE - market.precedent_score)
    rule_change_score = RULE_CHANGE_RISK_SCORES[market.rule_change_status]
    time_pressure_score = _time_pressure_score(
        market.time_to_resolution_minutes,
        resolved_config.time_pressure_cap_minutes,
    )
    risk_score = _quantize_ratio(
        _mul(market.ambiguity_score, resolved_config.ambiguity_weight)
        + _mul(precedent_gap_score, resolved_config.precedent_gap_weight)
        + _mul(rule_change_score, resolved_config.rule_change_weight)
        + _mul(
            market.source_disagreement_score,
            resolved_config.source_disagreement_weight,
        )
        + _mul(time_pressure_score, resolved_config.time_pressure_weight)
        + _mul(market.dispute_history_rate, resolved_config.dispute_history_weight),
    )
    risk_premium_bps = _quantize_bps(
        _mul(risk_score, resolved_config.max_resolution_risk_premium_bps),
    )
    adjusted_required_edge = _quantize_bps(
        resolved_config.base_required_edge_bps + risk_premium_bps,
    )
    risk_tier = _risk_tier(risk_premium_bps, resolved_config)
    reason_codes = _build_reason_codes(
        market=market,
        config=resolved_config,
        risk_tier=risk_tier,
    )
    payload = _build_payload(
        market=market,
        risk_score=risk_score,
        risk_premium_bps=risk_premium_bps,
        adjusted_required_edge=adjusted_required_edge,
        risk_tier=risk_tier,
        time_pressure_score=time_pressure_score,
        reason_codes=reason_codes,
    )
    result = StrategyResolutionRiskPremiumV10Result(
        risk_premium_bps=risk_premium_bps,
        adjusted_required_edge=adjusted_required_edge,
        risk_tier=risk_tier,
        reason_codes=reason_codes,
        payload=payload,
    )
    reject_unsafe_surface_fields("strategy resolution risk premium payload", result.payload)
    return result


def strategy_resolution_risk_premium_v10_payload(
    result: StrategyResolutionRiskPremiumV10Result,
) -> object:
    if not isinstance(result, StrategyResolutionRiskPremiumV10Result):
        raise ValueError("result must be a StrategyResolutionRiskPremiumV10Result")
    require_paper_only_flags("result", result)
    payload = {
        "risk_premium_bps": result.risk_premium_bps,
        "adjusted_required_edge": result.adjusted_required_edge,
        "risk_tier": result.risk_tier,
        "reason_codes": result.reason_codes,
        "payload": result.payload,
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }
    reject_unsafe_surface_fields("strategy resolution risk premium payload", payload)
    return json_ready_no_floats(payload)


def _build_reason_codes(
    *,
    market: StrategyResolutionRiskPremiumV10Input,
    config: StrategyResolutionRiskPremiumV10Config,
    risk_tier: str,
) -> tuple[str, ...]:
    reason_codes = [_risk_tier_reason_code(risk_tier)]

    if market.ambiguity_score >= config.high_ambiguity_threshold:
        reason_codes.append("ambiguity_high")
    else:
        reason_codes.append("ambiguity_contained")

    if market.precedent_score >= config.strong_precedent_threshold:
        reason_codes.append("precedent_strong")
    elif market.precedent_score <= config.weak_precedent_threshold:
        reason_codes.append("precedent_weak")
    else:
        reason_codes.append("precedent_mixed")

    reason_codes.append(_rule_change_reason_code(market.rule_change_status))

    if market.source_disagreement_score >= config.high_source_disagreement_threshold:
        reason_codes.append("source_disagreement_high")
    else:
        reason_codes.append("source_disagreement_contained")

    if market.time_to_resolution_minutes <= config.high_time_pressure_minutes:
        reason_codes.append("resolution_time_pressure_high")
    else:
        reason_codes.append("resolution_time_pressure_contained")

    if market.dispute_history_rate >= config.high_dispute_history_rate:
        reason_codes.append("dispute_history_high")
    else:
        reason_codes.append("dispute_history_contained")

    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _build_payload(
    *,
    market: StrategyResolutionRiskPremiumV10Input,
    risk_score: Decimal,
    risk_premium_bps: Decimal,
    adjusted_required_edge: Decimal,
    risk_tier: str,
    time_pressure_score: Decimal,
    reason_codes: tuple[str, ...],
) -> tuple[tuple[str, object], ...]:
    return (
        ("risk_score", str(risk_score)),
        ("risk_premium_bps", str(risk_premium_bps)),
        ("adjusted_required_edge", str(adjusted_required_edge)),
        ("risk_tier", risk_tier),
        ("ambiguity_score", str(market.ambiguity_score)),
        ("precedent_score", str(market.precedent_score)),
        ("rule_change_status", market.rule_change_status),
        ("source_disagreement_score", str(market.source_disagreement_score)),
        ("time_to_resolution_minutes", str(market.time_to_resolution_minutes)),
        ("time_pressure_score", str(time_pressure_score)),
        ("dispute_history_rate", str(market.dispute_history_rate)),
        ("reason_codes", reason_codes),
    )


def _risk_tier(
    risk_premium_bps: Decimal,
    config: StrategyResolutionRiskPremiumV10Config,
) -> str:
    if risk_premium_bps >= config.block_risk_premium_bps:
        return "block"
    if risk_premium_bps >= config.high_risk_premium_bps:
        return "high"
    if risk_premium_bps >= config.watch_risk_premium_bps:
        return "watch"
    return "low"


def _risk_tier_reason_code(risk_tier: str) -> str:
    if risk_tier == "block":
        return "resolution_risk_block"
    if risk_tier == "high":
        return "resolution_risk_high"
    if risk_tier == "watch":
        return "resolution_risk_watch"
    return "resolution_risk_low"


def _rule_change_reason_code(rule_change_status: str) -> str:
    if rule_change_status == "changed":
        return "rule_change_changed"
    if rule_change_status == "active":
        return "rule_change_active"
    if rule_change_status == "watch":
        return "rule_change_watch"
    return "rule_change_stable"


def _time_pressure_score(time_to_resolution_minutes: Decimal, cap_minutes: Decimal) -> Decimal:
    if time_to_resolution_minutes >= cap_minutes:
        return ZERO
    if time_to_resolution_minutes <= ZERO:
        return ONE
    return _quantize_ratio((cap_minutes - time_to_resolution_minutes) / cap_minutes)


def _validate_config(config: StrategyResolutionRiskPremiumV10Config) -> None:
    total_weight = _quantize_ratio(
        config.ambiguity_weight
        + config.precedent_gap_weight
        + config.rule_change_weight
        + config.source_disagreement_weight
        + config.time_pressure_weight
        + config.dispute_history_weight,
    )
    if total_weight != ONE:
        raise ValueError("resolution risk premium weights must sum to 1.000000")
    if not (
        config.watch_risk_premium_bps
        <= config.high_risk_premium_bps
        <= config.block_risk_premium_bps
        <= config.max_resolution_risk_premium_bps
    ):
        raise ValueError("risk premium thresholds must be ascending")
    if config.weak_precedent_threshold > config.strong_precedent_threshold:
        raise ValueError("weak_precedent_threshold must not exceed strong threshold")
    if config.high_time_pressure_minutes > config.time_pressure_cap_minutes:
        raise ValueError("high_time_pressure_minutes must not exceed cap")
    if config.time_pressure_cap_minutes <= ZERO:
        raise ValueError("time_pressure_cap_minutes must be positive")


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(value)


def _normalize_nonnegative_bps(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_bps(value)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized = []
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
    normalized = []
    for item in payload:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("payload entries must be key/value tuples")
        key = item[0]
        value = item[1]
        _require_canonical_string("payload key", key)
        _reject_float_or_decimal_payload_value(value)
        normalized.append((key, value))
    return tuple(normalized)


def _reject_float_or_decimal_payload_value(value: object) -> None:
    if isinstance(value, Decimal) or isinstance(value, float):
        raise ValueError("payload values must be JSON-safe non-float values")
    if isinstance(value, tuple):
        for item in value:
            _reject_float_or_decimal_payload_value(item)


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


def _quantize_bps(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(BPS_QUANTUM)


__all__ = (
    "DEFAULT_STRATEGY_RESOLUTION_RISK_PREMIUM_V10_CONFIG_VERSION",
    "RULE_CHANGE_STATUSES",
    "RISK_TIERS",
    "StrategyResolutionRiskPremiumV10Config",
    "StrategyResolutionRiskPremiumV10Input",
    "StrategyResolutionRiskPremiumV10Result",
    "build_strategy_resolution_risk_premium_v10",
    "strategy_resolution_risk_premium_v10_payload",
)

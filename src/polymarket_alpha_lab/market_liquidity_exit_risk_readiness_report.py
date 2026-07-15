"""Pure liquidity and exit-risk readiness report for probability screens."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "MarketLiquidityExitRiskReadinessReport",
    "build_market_liquidity_exit_risk_readiness_report",
    "market_liquidity_exit_risk_readiness_report_payload",
    "validate_market_liquidity_exit_risk_readiness_public_payload",
)


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

MAX_SPREAD_PROBABILITY = Decimal("0.020000")
MAX_SLIPPAGE_PROBABILITY = Decimal("0.015000")
MAX_SETTLEMENT_WINDOW_SECONDS = Decimal("172800.000000")
MIN_MARKET_AGE_SECONDS = Decimal("3600.000000")

COST_GATE_REASON = "market_liquidity_exit_cost_gate_not_ready"
BID_DEPTH_REASON = "market_liquidity_exit_bid_depth_below_position"
ASK_DEPTH_REASON = "market_liquidity_exit_ask_depth_below_position"
SPREAD_REASON = "market_liquidity_exit_spread_probability_watch"
SLIPPAGE_REASON = "market_liquidity_exit_slippage_probability_watch"
SETTLEMENT_REASON = "market_liquidity_exit_settlement_window_watch"
MARKET_AGE_REASON = "market_liquidity_exit_market_age_watch"
REASON_CODES = (
    COST_GATE_REASON,
    BID_DEPTH_REASON,
    ASK_DEPTH_REASON,
    SPREAD_REASON,
    SLIPPAGE_REASON,
    SETTLEMENT_REASON,
    MARKET_AGE_REASON,
)
CHECK_COUNT = Decimal("7.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    _join_parts("candidate", "_", "id"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("market", "_", "question"),
    _join_parts("ques", "tion"),
    _join_parts("source", "_", "id"),
    _join_parts("source", "_", "url"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "ref"),
    _join_parts("source", "_", "reference"),
    _join_parts("d", "s", "n"),
    _join_parts("table", "_", "name"),
    _join_parts("to", "ken"),
)


class _NoPublicSubclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if _NoPublicSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketLiquidityExitRiskReadinessReport(_NoPublicSubclass):
    bid_depth_usdc: Decimal
    ask_depth_usdc: Decimal
    spread_probability: Decimal
    estimated_slippage_probability: Decimal
    position_size_usdc: Decimal
    settlement_window_seconds: Decimal
    market_age_seconds: Decimal
    cost_gate_ready: bool
    liquidity_exit_ready: bool
    exit_risk_score: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquidityExitRiskReadinessReport, "report")
        for field_name in (
            "bid_depth_usdc",
            "ask_depth_usdc",
            "settlement_window_seconds",
            "market_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_probability",
            "estimated_slippage_probability",
            "exit_risk_score",
            "ready_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "position_size_usdc",
            _require_positive_decimal("position_size_usdc", self.position_size_usdc),
        )
        _require_bool("cost_gate_ready", self.cost_gate_ready)
        _require_bool("liquidity_exit_ready", self.liquidity_exit_ready)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes("blocked_reason_codes", self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def digest(self) -> str:
        return _canonical_digest(_base_public_payload(self))

    @property
    def public_payload(self) -> dict[str, Any]:
        return _public_payload(self)


def build_market_liquidity_exit_risk_readiness_report(
    *,
    bid_depth_usdc: Decimal,
    ask_depth_usdc: Decimal,
    spread_probability: Decimal,
    estimated_slippage_probability: Decimal,
    position_size_usdc: Decimal,
    settlement_window_seconds: Decimal,
    market_age_seconds: Decimal,
    cost_gate_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketLiquidityExitRiskReadinessReport:
    bid_depth = _require_nonnegative_decimal("bid_depth_usdc", bid_depth_usdc)
    ask_depth = _require_nonnegative_decimal("ask_depth_usdc", ask_depth_usdc)
    spread = _require_ratio("spread_probability", spread_probability)
    slippage = _require_ratio(
        "estimated_slippage_probability",
        estimated_slippage_probability,
    )
    position_size = _require_positive_decimal("position_size_usdc", position_size_usdc)
    settlement_window = _require_nonnegative_decimal(
        "settlement_window_seconds",
        settlement_window_seconds,
    )
    market_age = _require_nonnegative_decimal("market_age_seconds", market_age_seconds)
    _require_bool("cost_gate_ready", cost_gate_ready)
    report = _evaluate(
        bid_depth_usdc=bid_depth,
        ask_depth_usdc=ask_depth,
        spread_probability=spread,
        estimated_slippage_probability=slippage,
        position_size_usdc=position_size,
        settlement_window_seconds=settlement_window,
        market_age_seconds=market_age,
        cost_gate_ready=cost_gate_ready,
    )
    return MarketLiquidityExitRiskReadinessReport(
        bid_depth_usdc=bid_depth,
        ask_depth_usdc=ask_depth,
        spread_probability=spread,
        estimated_slippage_probability=slippage,
        position_size_usdc=position_size,
        settlement_window_seconds=settlement_window,
        market_age_seconds=market_age,
        cost_gate_ready=cost_gate_ready,
        liquidity_exit_ready=report["liquidity_exit_ready"],
        exit_risk_score=report["exit_risk_score"],
        blocked_reason_codes=report["blocked_reason_codes"],
        attention_reason_codes=report["attention_reason_codes"],
        ready_ratio=report["ready_ratio"],
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def market_liquidity_exit_risk_readiness_report_payload(
    report: MarketLiquidityExitRiskReadinessReport,
) -> dict[str, Any]:
    if type(report) is not MarketLiquidityExitRiskReadinessReport:
        raise ValueError("report must be a MarketLiquidityExitRiskReadinessReport")
    return _public_payload(report)


def validate_market_liquidity_exit_risk_readiness_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_values(payload)
    _require_payload_hard_flags(payload)
    digest = payload.get("digest")
    if type(digest) is not str:
        raise ValueError("digest must be a string")
    if len(digest) != 64:
        raise ValueError("digest must be a sha256 hex string")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError("digest must be a sha256 hex string") from exc
    unsigned = dict(payload)
    unsigned.pop("digest")
    if digest != _canonical_digest(unsigned):
        raise ValueError("digest does not match public payload")
    return True


def _evaluate(
    *,
    bid_depth_usdc: Decimal,
    ask_depth_usdc: Decimal,
    spread_probability: Decimal,
    estimated_slippage_probability: Decimal,
    position_size_usdc: Decimal,
    settlement_window_seconds: Decimal,
    market_age_seconds: Decimal,
    cost_gate_ready: bool,
) -> dict[str, Any]:
    blocked: list[str] = []
    attention: list[str] = []
    ready_checks = 0

    if cost_gate_ready:
        ready_checks += 1
    else:
        blocked.append(COST_GATE_REASON)

    if bid_depth_usdc >= position_size_usdc:
        ready_checks += 1
    else:
        blocked.append(BID_DEPTH_REASON)

    if ask_depth_usdc >= position_size_usdc:
        ready_checks += 1
    else:
        attention.append(ASK_DEPTH_REASON)

    if spread_probability <= MAX_SPREAD_PROBABILITY:
        ready_checks += 1
    else:
        attention.append(SPREAD_REASON)

    if estimated_slippage_probability <= MAX_SLIPPAGE_PROBABILITY:
        ready_checks += 1
    else:
        attention.append(SLIPPAGE_REASON)

    if settlement_window_seconds <= MAX_SETTLEMENT_WINDOW_SECONDS:
        ready_checks += 1
    else:
        attention.append(SETTLEMENT_REASON)

    if market_age_seconds >= MIN_MARKET_AGE_SECONDS:
        ready_checks += 1
    else:
        attention.append(MARKET_AGE_REASON)

    ready_ratio = _ratio(_count(ready_checks), CHECK_COUNT)
    with localcontext(DECIMAL_CONTEXT):
        exit_risk_score = (ONE - ready_ratio).quantize(QUANT)
    return {
        "liquidity_exit_ready": ready_ratio == ONE,
        "exit_risk_score": exit_risk_score,
        "blocked_reason_codes": tuple(blocked),
        "attention_reason_codes": tuple(attention),
        "ready_ratio": ready_ratio,
    }


def _validate_report(report: MarketLiquidityExitRiskReadinessReport) -> None:
    expected = _evaluate(
        bid_depth_usdc=report.bid_depth_usdc,
        ask_depth_usdc=report.ask_depth_usdc,
        spread_probability=report.spread_probability,
        estimated_slippage_probability=report.estimated_slippage_probability,
        position_size_usdc=report.position_size_usdc,
        settlement_window_seconds=report.settlement_window_seconds,
        market_age_seconds=report.market_age_seconds,
        cost_gate_ready=report.cost_gate_ready,
    )
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match liquidity exit checks")
    if set(report.blocked_reason_codes) & set(report.attention_reason_codes):
        raise ValueError("reason code groups must not overlap")


def _base_public_payload(
    report: MarketLiquidityExitRiskReadinessReport,
) -> dict[str, Any]:
    _require_exact_type(report, MarketLiquidityExitRiskReadinessReport, "report")
    _require_hard_flags("report", report)
    _validate_report(report)
    return {
        "bid_depth_usdc": _public_decimal(report.bid_depth_usdc),
        "ask_depth_usdc": _public_decimal(report.ask_depth_usdc),
        "spread_probability": _public_decimal(report.spread_probability),
        "estimated_slippage_probability": _public_decimal(
            report.estimated_slippage_probability,
        ),
        "position_size_usdc": _public_decimal(report.position_size_usdc),
        "settlement_window_seconds": _public_decimal(report.settlement_window_seconds),
        "market_age_seconds": _public_decimal(report.market_age_seconds),
        "cost_gate_ready": report.cost_gate_ready,
        "liquidity_exit_ready": report.liquidity_exit_ready,
        "exit_risk_score": _public_decimal(report.exit_risk_score),
        "blocked_reason_codes": list(report.blocked_reason_codes),
        "attention_reason_codes": list(report.attention_reason_codes),
        "ready_ratio": _public_decimal(report.ready_ratio),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _public_payload(report: MarketLiquidityExitRiskReadinessReport) -> dict[str, Any]:
    payload = _base_public_payload(report)
    payload["digest"] = _canonical_digest(payload)
    validate_market_liquidity_exit_risk_readiness_public_payload(payload)
    return payload


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _public_decimal(value: Decimal) -> str:
    return format(_require_nonnegative_decimal("public decimal", value), "f")


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANT)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be known")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be an exact {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must have {field_name}=True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload must have {field_name}=True")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("payload contains unsafe public key")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)


def _reject_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)
    elif type(value) in (Decimal, float, int):
        raise ValueError("public payload numeric values must be strings")

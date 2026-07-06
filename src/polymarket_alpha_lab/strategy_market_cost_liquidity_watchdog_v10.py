"""Pure paper-only market cost and liquidity watchdog for strategy candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any


__all__ = (
    "StrategyMarketCostLiquidityWatchdogConfig",
    "StrategyMarketCostLiquidityWatchdogInput",
    "StrategyMarketCostLiquidityWatchdogReport",
    "evaluate_strategy_market_cost_liquidity_watchdog_v10",
    "strategy_market_cost_liquidity_watchdog_v10_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-market-cost-liquidity-watchdog-v10"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
WATCHDOG_STATUSES = ("attractive", "watch", "unattractive")
STATUS_REASON_PREFIX = "strategy_market_cost_liquidity_watchdog_"
PROFILE_REASON_ATTRACTIVE = "cost_liquidity_profile_attractive"
PROFILE_REASON_WATCH = "cost_liquidity_profile_watch"
PROFILE_REASON_UNATTRACTIVE = "cost_liquidity_profile_unattractive"
BLOCKER_REASON_CODES = (
    "fee_drag_above_limit",
    "bid_ask_spread_above_limit",
    "expected_slippage_above_limit",
    "exit_depth_below_target",
    "liquidity_volatility_above_limit",
)
GENERATED_REASON_CODES = (
    PROFILE_REASON_ATTRACTIVE,
    PROFILE_REASON_WATCH,
    PROFILE_REASON_UNATTRACTIVE,
    *BLOCKER_REASON_CODES,
)
UNSAFE_SURFACE_FRAGMENTS = (
    "auth",
    "broker",
    "cancel",
    "client",
    "connect",
    "database",
    "execute",
    "fetch",
    "network",
    "order",
    "persist",
    "request",
    "secret",
    "sign",
    "submit",
    "token",
    "trade",
    "wallet",
)


@dataclass(frozen=True)
class StrategyMarketCostLiquidityWatchdogConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    minimum_attractive_score: Decimal = Decimal("0.750000")
    minimum_watch_score: Decimal = Decimal("0.500000")
    maximum_fee_drag: Decimal = Decimal("0.015000")
    maximum_bid_ask_spread: Decimal = Decimal("0.030000")
    maximum_expected_slippage: Decimal = Decimal("0.020000")
    minimum_exit_depth_ratio: Decimal = Decimal("1.000000")
    maximum_liquidity_volatility: Decimal = Decimal("0.250000")
    fee_drag_weight: Decimal = Decimal("0.200000")
    spread_weight: Decimal = Decimal("0.200000")
    slippage_weight: Decimal = Decimal("0.200000")
    exit_depth_weight: Decimal = Decimal("0.250000")
    liquidity_volatility_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("minimum_attractive_score", "minimum_watch_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_watch_score > self.minimum_attractive_score:
            raise ValueError(
                "minimum_watch_score must be less than or equal to "
                "minimum_attractive_score",
            )
        for field_name in (
            "maximum_fee_drag",
            "maximum_bid_ask_spread",
            "maximum_expected_slippage",
            "maximum_liquidity_volatility",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_probability_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "minimum_exit_depth_ratio",
            _normalize_positive_decimal(
                "minimum_exit_depth_ratio",
                self.minimum_exit_depth_ratio,
            ),
        )
        for field_name in (
            "fee_drag_weight",
            "spread_weight",
            "slippage_weight",
            "exit_depth_weight",
            "liquidity_volatility_weight",
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
class StrategyMarketCostLiquidityWatchdogInput:
    market_slug: str
    outcome_name: str
    paper_recommendation: str
    target_notional: Decimal
    fee_drag: Decimal
    bid_ask_spread: Decimal
    expected_slippage: Decimal
    exit_depth_notional: Decimal
    liquidity_volatility: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "outcome_name", "paper_recommendation"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "target_notional",
            _normalize_positive_decimal("target_notional", self.target_notional),
        )
        object.__setattr__(
            self,
            "exit_depth_notional",
            _normalize_nonnegative_decimal(
                "exit_depth_notional",
                self.exit_depth_notional,
            ),
        )
        for field_name in (
            "fee_drag",
            "bid_ask_spread",
            "expected_slippage",
            "liquidity_volatility",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("market_state", self)


@dataclass(frozen=True)
class StrategyMarketCostLiquidityWatchdogReport:
    config_version: str
    market_slug: str
    outcome_name: str
    paper_recommendation: str
    watchdog_status: str
    target_notional: Decimal
    fee_drag: Decimal
    fee_drag_score: Decimal
    bid_ask_spread: Decimal
    spread_score: Decimal
    expected_slippage: Decimal
    slippage_score: Decimal
    exit_depth_notional: Decimal
    exit_depth_ratio: Decimal
    exit_depth_score: Decimal
    liquidity_volatility: Decimal
    liquidity_volatility_score: Decimal
    cost_liquidity_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "config_version",
            "market_slug",
            "outcome_name",
            "paper_recommendation",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("watchdog_status", self.watchdog_status, WATCHDOG_STATUSES)
        object.__setattr__(
            self,
            "target_notional",
            _normalize_positive_decimal("target_notional", self.target_notional),
        )
        object.__setattr__(
            self,
            "exit_depth_notional",
            _normalize_nonnegative_decimal(
                "exit_depth_notional",
                self.exit_depth_notional,
            ),
        )
        for field_name in (
            "fee_drag",
            "fee_drag_score",
            "bid_ask_spread",
            "spread_score",
            "expected_slippage",
            "slippage_score",
            "exit_depth_ratio",
            "exit_depth_score",
            "liquidity_volatility",
            "liquidity_volatility_score",
            "cost_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def evaluate_strategy_market_cost_liquidity_watchdog_v10(
    market_state: StrategyMarketCostLiquidityWatchdogInput,
    config: StrategyMarketCostLiquidityWatchdogConfig,
) -> StrategyMarketCostLiquidityWatchdogReport:
    """Evaluate cost and liquidity drag without side effects or live execution."""

    _require_exact_type(
        "market_state",
        market_state,
        StrategyMarketCostLiquidityWatchdogInput,
    )
    _require_exact_type("config", config, StrategyMarketCostLiquidityWatchdogConfig)

    fee_drag_score = _inverse_limit_score(market_state.fee_drag, config.maximum_fee_drag)
    spread_score = _inverse_limit_score(
        market_state.bid_ask_spread,
        config.maximum_bid_ask_spread,
    )
    slippage_score = _inverse_limit_score(
        market_state.expected_slippage,
        config.maximum_expected_slippage,
    )
    exit_depth_ratio = _capped_ratio(
        market_state.exit_depth_notional,
        market_state.target_notional,
    )
    exit_depth_score = _capped_ratio(exit_depth_ratio, config.minimum_exit_depth_ratio)
    liquidity_volatility_score = _inverse_limit_score(
        market_state.liquidity_volatility,
        config.maximum_liquidity_volatility,
    )
    cost_liquidity_score = _quantize_decimal(
        "cost_liquidity_score",
        (
            fee_drag_score * config.fee_drag_weight
            + spread_score * config.spread_weight
            + slippage_score * config.slippage_weight
            + exit_depth_score * config.exit_depth_weight
            + liquidity_volatility_score * config.liquidity_volatility_weight
        ),
    )
    watchdog_status = _watchdog_status(cost_liquidity_score, config)
    blockers = _blocker_reason_codes(market_state, config, exit_depth_ratio)

    return StrategyMarketCostLiquidityWatchdogReport(
        config_version=config.config_version,
        market_slug=market_state.market_slug,
        outcome_name=market_state.outcome_name,
        paper_recommendation=market_state.paper_recommendation,
        watchdog_status=watchdog_status,
        target_notional=market_state.target_notional,
        fee_drag=market_state.fee_drag,
        fee_drag_score=fee_drag_score,
        bid_ask_spread=market_state.bid_ask_spread,
        spread_score=spread_score,
        expected_slippage=market_state.expected_slippage,
        slippage_score=slippage_score,
        exit_depth_notional=market_state.exit_depth_notional,
        exit_depth_ratio=exit_depth_ratio,
        exit_depth_score=exit_depth_score,
        liquidity_volatility=market_state.liquidity_volatility,
        liquidity_volatility_score=liquidity_volatility_score,
        cost_liquidity_score=cost_liquidity_score,
        reason_codes=_report_reason_codes(
            watchdog_status,
            market_state.reason_codes,
            blockers,
        ),
    )


def strategy_market_cost_liquidity_watchdog_v10_payload(
    report: StrategyMarketCostLiquidityWatchdogReport | dict[str, Any],
) -> dict[str, object]:
    if type(report) is StrategyMarketCostLiquidityWatchdogReport:
        _require_hard_flags("report", report)
        _reject_unsafe_payload("report", report)
        payload = _report_payload(report)
    elif type(report) is dict:
        _reject_unsafe_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a StrategyMarketCostLiquidityWatchdogReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _report_payload(
    report: StrategyMarketCostLiquidityWatchdogReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "market_slug": report.market_slug,
        "outcome_name": report.outcome_name,
        "paper_recommendation": report.paper_recommendation,
        "watchdog_status": report.watchdog_status,
        "target_notional": _decimal_payload(report.target_notional),
        "fee_drag": _decimal_payload(report.fee_drag),
        "fee_drag_score": _decimal_payload(report.fee_drag_score),
        "bid_ask_spread": _decimal_payload(report.bid_ask_spread),
        "spread_score": _decimal_payload(report.spread_score),
        "expected_slippage": _decimal_payload(report.expected_slippage),
        "slippage_score": _decimal_payload(report.slippage_score),
        "exit_depth_notional": _decimal_payload(report.exit_depth_notional),
        "exit_depth_ratio": _decimal_payload(report.exit_depth_ratio),
        "exit_depth_score": _decimal_payload(report.exit_depth_score),
        "liquidity_volatility": _decimal_payload(report.liquidity_volatility),
        "liquidity_volatility_score": _decimal_payload(
            report.liquidity_volatility_score,
        ),
        "cost_liquidity_score": _decimal_payload(report.cost_liquidity_score),
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _weight_sum(config: StrategyMarketCostLiquidityWatchdogConfig) -> Decimal:
    return _quantize_decimal(
        "weights",
        (
            config.fee_drag_weight
            + config.spread_weight
            + config.slippage_weight
            + config.exit_depth_weight
            + config.liquidity_volatility_weight
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


def _watchdog_status(
    cost_liquidity_score: Decimal,
    config: StrategyMarketCostLiquidityWatchdogConfig,
) -> str:
    if cost_liquidity_score >= config.minimum_attractive_score:
        return "attractive"
    if cost_liquidity_score >= config.minimum_watch_score:
        return "watch"
    return "unattractive"


def _blocker_reason_codes(
    market_state: StrategyMarketCostLiquidityWatchdogInput,
    config: StrategyMarketCostLiquidityWatchdogConfig,
    exit_depth_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if market_state.fee_drag > config.maximum_fee_drag:
        reason_codes.append("fee_drag_above_limit")
    if market_state.bid_ask_spread > config.maximum_bid_ask_spread:
        reason_codes.append("bid_ask_spread_above_limit")
    if market_state.expected_slippage > config.maximum_expected_slippage:
        reason_codes.append("expected_slippage_above_limit")
    if exit_depth_ratio < config.minimum_exit_depth_ratio:
        reason_codes.append("exit_depth_below_target")
    if market_state.liquidity_volatility > config.maximum_liquidity_volatility:
        reason_codes.append("liquidity_volatility_above_limit")
    return tuple(reason_codes)


def _report_reason_codes(
    watchdog_status: str,
    upstream_reason_codes: tuple[str, ...],
    blocker_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    generated_reason_codes = blocker_reason_codes
    if not generated_reason_codes:
        generated_reason_codes = (f"cost_liquidity_profile_{watchdog_status}",)
    reason_codes = [
        f"{STATUS_REASON_PREFIX}{watchdog_status}",
        *upstream_reason_codes,
        *generated_reason_codes,
    ]
    return tuple(dict.fromkeys(reason_codes))


def _validate_report_consistency(
    report: StrategyMarketCostLiquidityWatchdogReport,
) -> None:
    expected_reason_code = f"{STATUS_REASON_PREFIX}{report.watchdog_status}"
    if not report.reason_codes or report.reason_codes[0] != expected_reason_code:
        raise ValueError("reason_codes must start with watchdog_status reason code")
    if report.exit_depth_ratio != _capped_ratio(
        report.exit_depth_notional,
        report.target_notional,
    ):
        raise ValueError("exit_depth_ratio must match exit_depth_notional and target_notional")
    component_scores = (
        report.fee_drag_score,
        report.spread_score,
        report.slippage_score,
        report.exit_depth_score,
        report.liquidity_volatility_score,
    )
    if report.cost_liquidity_score < min(component_scores):
        raise ValueError("cost_liquidity_score must be within component score range")
    if report.cost_liquidity_score > max(component_scores):
        raise ValueError("cost_liquidity_score must be within component score range")
    generated_reason_codes = tuple(
        reason_code
        for reason_code in report.reason_codes[1:]
        if reason_code in GENERATED_REASON_CODES
    )
    if report.watchdog_status == "attractive":
        if PROFILE_REASON_ATTRACTIVE not in generated_reason_codes:
            raise ValueError("attractive report must include attractive profile reason")
        if any(reason_code in BLOCKER_REASON_CODES for reason_code in generated_reason_codes):
            raise ValueError("attractive report must not include blocker reason_codes")
    elif not generated_reason_codes:
        raise ValueError(f"{report.watchdog_status} report must include blocker reason")


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


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return _decimal_payload(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived string values")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(label: str, value: object) -> None:
    _reject_unsafe_payload_keys(label, value)
    _reject_unsafe_payload_values(label, value)


def _reject_unsafe_payload_keys(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload_keys(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_payload_keys(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload_keys(label, item)


def _reject_unsafe_payload_values(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload_values(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"unsafe live surface value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_payload_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload_values(label, item)


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_SURFACE_FRAGMENTS)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")

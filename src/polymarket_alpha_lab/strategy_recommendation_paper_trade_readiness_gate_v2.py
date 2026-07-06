"""Phase 1 paper-only readiness gate for strategy recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


__all__ = (
    "StrategyRecommendationPaperTradeReadinessConfig",
    "StrategyRecommendationPaperTradeReadinessDecision",
    "StrategyRecommendationPaperTradeReadinessInput",
    "evaluate_strategy_recommendation_paper_trade_readiness",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
SIDES = ("yes", "no")
READINESS_STATUSES = ("ready", "blocked")
READY_REASON_CODE = "paper_trade_ready"


@dataclass(frozen=True)
class StrategyRecommendationPaperTradeReadinessConfig:
    config_version: str
    max_evidence_age_seconds: int
    min_expected_value_after_costs: Decimal
    min_liquidity_usd: Decimal
    max_resolution_risk: Decimal
    min_team_approval_count: int
    required_manual_checks: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    live_trading_enabled: bool = False
    network_access_allowed: bool = False
    wallet_required: bool = False
    orders_allowed: bool = False
    db_writes_allowed: bool = False

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "max_evidence_age_seconds",
            self.max_evidence_age_seconds,
        )
        object.__setattr__(
            self,
            "min_expected_value_after_costs",
            _normalize_decimal(
                "min_expected_value_after_costs",
                self.min_expected_value_after_costs,
            ),
        )
        object.__setattr__(
            self,
            "min_liquidity_usd",
            _normalize_nonnegative_decimal("min_liquidity_usd", self.min_liquidity_usd),
        )
        object.__setattr__(
            self,
            "max_resolution_risk",
            _normalize_probability("max_resolution_risk", self.max_resolution_risk),
        )
        _require_nonnegative_int(
            "min_team_approval_count",
            self.min_team_approval_count,
        )
        object.__setattr__(
            self,
            "required_manual_checks",
            _normalize_canonical_string_tuple(
                "required_manual_checks",
                self.required_manual_checks,
                allow_empty=False,
            ),
        )
        _require_paper_report_readonly_flags(self)
        _require_no_live_capability_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationPaperTradeReadinessInput:
    recommendation_id: str
    market_slug: str
    side: str
    evidence_generated_at: datetime
    expected_value_before_costs: Decimal
    estimated_cost_per_share: Decimal
    available_liquidity_usd: Decimal
    resolution_risk: Decimal
    team_approval_count: int
    completed_manual_checks: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    live_trading_enabled: bool = False
    network_access_allowed: bool = False
    wallet_required: bool = False
    orders_allowed: bool = False
    db_writes_allowed: bool = False

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_side("side", self.side)
        object.__setattr__(
            self,
            "evidence_generated_at",
            _as_utc("evidence_generated_at", self.evidence_generated_at),
        )
        object.__setattr__(
            self,
            "expected_value_before_costs",
            _normalize_decimal(
                "expected_value_before_costs",
                self.expected_value_before_costs,
            ),
        )
        object.__setattr__(
            self,
            "estimated_cost_per_share",
            _normalize_nonnegative_decimal(
                "estimated_cost_per_share",
                self.estimated_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "available_liquidity_usd",
            _normalize_nonnegative_decimal(
                "available_liquidity_usd",
                self.available_liquidity_usd,
            ),
        )
        object.__setattr__(
            self,
            "resolution_risk",
            _normalize_probability("resolution_risk", self.resolution_risk),
        )
        _require_nonnegative_int("team_approval_count", self.team_approval_count)
        object.__setattr__(
            self,
            "completed_manual_checks",
            _normalize_canonical_string_tuple(
                "completed_manual_checks",
                self.completed_manual_checks,
                allow_empty=True,
            ),
        )
        _require_paper_report_readonly_flags(self)
        _require_no_live_capability_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationPaperTradeReadinessDecision:
    recommendation_id: str
    market_slug: str
    side: str
    readiness_status: str
    evidence_age_seconds: int
    expected_value_after_costs: Decimal
    missing_manual_checks: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    live_trading_enabled: bool = False
    network_access_allowed: bool = False
    wallet_required: bool = False
    orders_allowed: bool = False
    db_writes_allowed: bool = False

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_side("side", self.side)
        _require_readiness_status("readiness_status", self.readiness_status)
        _require_nonnegative_int("evidence_age_seconds", self.evidence_age_seconds)
        object.__setattr__(
            self,
            "expected_value_after_costs",
            _normalize_decimal(
                "expected_value_after_costs",
                self.expected_value_after_costs,
            ),
        )
        object.__setattr__(
            self,
            "missing_manual_checks",
            _normalize_canonical_string_tuple(
                "missing_manual_checks",
                self.missing_manual_checks,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_canonical_string_tuple(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _validate_decision_consistency(self)
        _require_paper_report_readonly_flags(self)
        _require_no_live_capability_flags(self)


def evaluate_strategy_recommendation_paper_trade_readiness(
    candidate: StrategyRecommendationPaperTradeReadinessInput,
    *,
    config: StrategyRecommendationPaperTradeReadinessConfig,
    evaluated_at: datetime,
) -> StrategyRecommendationPaperTradeReadinessDecision:
    if type(candidate) is not StrategyRecommendationPaperTradeReadinessInput:
        raise ValueError(
            "candidate must be a StrategyRecommendationPaperTradeReadinessInput",
        )
    if type(config) is not StrategyRecommendationPaperTradeReadinessConfig:
        raise ValueError(
            "config must be a StrategyRecommendationPaperTradeReadinessConfig",
        )
    _require_paper_report_readonly_flags(candidate)
    _require_paper_report_readonly_flags(config)
    _require_no_live_capability_flags(candidate)
    _require_no_live_capability_flags(config)

    evaluated_at_utc = _as_utc("evaluated_at", evaluated_at)
    evidence_age_seconds = _evidence_age_seconds(
        evidence_generated_at=candidate.evidence_generated_at,
        evaluated_at=evaluated_at_utc,
    )
    expected_value_after_costs = _subtract_decimal(
        candidate.expected_value_before_costs,
        candidate.estimated_cost_per_share,
    )
    missing_manual_checks = _missing_manual_checks(
        required_manual_checks=config.required_manual_checks,
        completed_manual_checks=candidate.completed_manual_checks,
    )
    reason_codes = _readiness_reason_codes(
        candidate=candidate,
        config=config,
        evidence_age_seconds=evidence_age_seconds,
        expected_value_after_costs=expected_value_after_costs,
        missing_manual_checks=missing_manual_checks,
        evaluated_at=evaluated_at_utc,
    )

    return StrategyRecommendationPaperTradeReadinessDecision(
        recommendation_id=candidate.recommendation_id,
        market_slug=candidate.market_slug,
        side=candidate.side,
        readiness_status="ready" if reason_codes == (READY_REASON_CODE,) else "blocked",
        evidence_age_seconds=evidence_age_seconds,
        expected_value_after_costs=expected_value_after_costs,
        missing_manual_checks=missing_manual_checks,
        reason_codes=reason_codes,
    )


def _readiness_reason_codes(
    *,
    candidate: StrategyRecommendationPaperTradeReadinessInput,
    config: StrategyRecommendationPaperTradeReadinessConfig,
    evidence_age_seconds: int,
    expected_value_after_costs: Decimal,
    missing_manual_checks: tuple[str, ...],
    evaluated_at: datetime,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.evidence_generated_at > evaluated_at:
        reason_codes.append("evidence_timestamp_after_evaluation")
    elif evidence_age_seconds > config.max_evidence_age_seconds:
        reason_codes.append("evidence_stale")
    if expected_value_after_costs < config.min_expected_value_after_costs:
        reason_codes.append("expected_value_after_costs_below_minimum")
    if candidate.available_liquidity_usd < config.min_liquidity_usd:
        reason_codes.append("liquidity_below_minimum")
    if candidate.resolution_risk > config.max_resolution_risk:
        reason_codes.append("resolution_risk_above_maximum")
    if candidate.team_approval_count < config.min_team_approval_count:
        reason_codes.append("team_quorum_not_met")
    if missing_manual_checks:
        reason_codes.append("manual_checks_missing")
    if not reason_codes:
        reason_codes.append(READY_REASON_CODE)
    return tuple(reason_codes)


def _evidence_age_seconds(
    *,
    evidence_generated_at: datetime,
    evaluated_at: datetime,
) -> int:
    if evidence_generated_at > evaluated_at:
        return 0
    delta = evaluated_at - evidence_generated_at
    return (delta.days * 86_400) + delta.seconds


def _missing_manual_checks(
    *,
    required_manual_checks: tuple[str, ...],
    completed_manual_checks: tuple[str, ...],
) -> tuple[str, ...]:
    completed = set(completed_manual_checks)
    return tuple(check for check in required_manual_checks if check not in completed)


def _validate_decision_consistency(
    decision: StrategyRecommendationPaperTradeReadinessDecision,
) -> None:
    if decision.readiness_status == "ready":
        if decision.missing_manual_checks:
            raise ValueError("missing_manual_checks must be empty for ready decisions")
        if decision.reason_codes != (READY_REASON_CODE,):
            raise ValueError("reason_codes must be paper_trade_ready for ready decisions")
    elif decision.reason_codes == (READY_REASON_CODE,):
        raise ValueError("reason_codes must not mark blocked decisions ready")


def _normalize_canonical_string_tuple(
    field_name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in normalized:
        _require_canonical_string(field_name, item)
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes or no")


def _require_readiness_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{field_name} must be ready or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_paper_report_readonly_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _require_no_live_capability_flags(value: object) -> None:
    if getattr(value, "live_trading_enabled", None) is not False:
        raise ValueError("live_trading_enabled must be False")
    if getattr(value, "network_access_allowed", None) is not False:
        raise ValueError("network_access_allowed must be False")
    if getattr(value, "wallet_required", None) is not False:
        raise ValueError("wallet_required must be False")
    if getattr(value, "orders_allowed", None) is not False:
        raise ValueError("orders_allowed must be False")
    if getattr(value, "db_writes_allowed", None) is not False:
        raise ValueError("db_writes_allowed must be False")

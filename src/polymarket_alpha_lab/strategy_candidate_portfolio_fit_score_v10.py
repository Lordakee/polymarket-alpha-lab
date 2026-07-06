"""Paper/report/readonly candidate portfolio-fit reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

FIT_STATUSES = ("fit", "watch", "blocked")
RESOLUTION_RISK_TIERS = ("low", "medium", "high", "critical")

EDGE_FULL_SCORE_BPS = Decimal("500.000000")
FIT_SCORE_FLOOR = Decimal("0.600000")

EDGE_WEIGHT = Decimal("0.350000")
CORRELATION_WEIGHT = Decimal("0.150000")
CATEGORY_EXPOSURE_WEIGHT = Decimal("0.100000")
LIQUIDITY_WEIGHT = Decimal("0.200000")
RESOLUTION_RISK_WEIGHT = Decimal("0.050000")
TEAM_FIT_WEIGHT = Decimal("0.150000")

CORRELATION_PENALTY_START = Decimal("0.700000")
CORRELATION_BLOCK_LIMIT = Decimal("0.900000")
CORRELATION_PENALTY_RATE = Decimal("0.500000")

CATEGORY_EXPOSURE_PENALTY_START = Decimal("0.300000")
CATEGORY_EXPOSURE_BLOCK_LIMIT = Decimal("0.750000")
CATEGORY_EXPOSURE_PENALTY_RATE = Decimal("0.400000")
CATEGORY_EXPOSURE_PENALTY_CAP = Decimal("0.200000")

LIQUIDITY_PENALTY_START = Decimal("0.500000")
LIQUIDITY_BLOCK_FLOOR = Decimal("0.300000")
LIQUIDITY_PENALTY_RATE = Decimal("0.300000")

TEAM_FIT_PENALTY_START = Decimal("0.500000")
TEAM_FIT_BLOCK_FLOOR = Decimal("0.300000")
TEAM_FIT_PENALTY_RATE = Decimal("0.300000")

EDGE_BLOCK_PENALTY = Decimal("0.240000")
RESOLUTION_RISK_QUALITY = {
    "low": Decimal("0.800000"),
    "medium": Decimal("0.420000"),
    "high": Decimal("0.200000"),
    "critical": ZERO,
}
RESOLUTION_RISK_PENALTIES = {
    "low": ZERO,
    "medium": Decimal("0.050000"),
    "high": Decimal("0.150000"),
    "critical": Decimal("0.300000"),
}

REASON_CODES = (
    "fit_score_meets_floor",
    "fit_score_below_fit_floor",
    "positive_cost_adjusted_edge",
    "cost_adjusted_edge_nonpositive_blocked",
    "cluster_correlation_within_limit",
    "cluster_correlation_penalty_applied",
    "cluster_correlation_above_block_limit",
    "category_exposure_within_limit",
    "category_exposure_penalty_applied",
    "category_exposure_above_block_limit",
    "liquidity_score_supported",
    "liquidity_penalty_applied",
    "liquidity_score_below_block_floor",
    "resolution_risk_low",
    "resolution_risk_medium_penalty_applied",
    "resolution_risk_high_penalty_applied",
    "resolution_risk_critical_blocked",
    "team_fit_supported",
    "team_fit_penalty_applied",
    "team_fit_below_block_floor",
    "portfolio_fit_clear",
)


@dataclass(frozen=True)
class StrategyCandidatePortfolioFitScoreV10Input:
    market_id: str
    category: str
    cost_adjusted_edge_bps: Decimal
    cluster_correlation_score: Decimal
    current_category_exposure: Decimal
    liquidity_score: Decimal
    resolution_risk_tier: str
    team_fit_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("market_id", self.market_id)
        _require_public_text("category", self.category)
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_decimal("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        for field_name in (
            "cluster_correlation_score",
            "current_category_exposure",
            "liquidity_score",
            "team_fit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member(
            "resolution_risk_tier",
            self.resolution_risk_tier,
            RESOLUTION_RISK_TIERS,
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyCandidatePortfolioFitScoreV10Penalties:
    edge_penalty: Decimal
    correlation_penalty: Decimal
    category_exposure_penalty: Decimal
    liquidity_penalty: Decimal
    resolution_risk_penalty: Decimal
    team_fit_penalty: Decimal

    def __post_init__(self) -> None:
        for field_name in (
            "edge_penalty",
            "correlation_penalty",
            "category_exposure_penalty",
            "liquidity_penalty",
            "resolution_risk_penalty",
            "team_fit_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )

    @property
    def total_penalty(self) -> Decimal:
        return _quantize(
            self.edge_penalty
            + self.correlation_penalty
            + self.category_exposure_penalty
            + self.liquidity_penalty
            + self.resolution_risk_penalty
            + self.team_fit_penalty,
        )


@dataclass(frozen=True)
class StrategyCandidatePortfolioFitScoreV10Result:
    market_id: str
    category: str
    cost_adjusted_edge_bps: Decimal
    cluster_correlation_score: Decimal
    current_category_exposure: Decimal
    liquidity_score: Decimal
    resolution_risk_tier: str
    team_fit_score: Decimal
    portfolio_fit_status: str
    fit_score: Decimal
    fit_penalties: StrategyCandidatePortfolioFitScoreV10Penalties
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("market_id", self.market_id)
        _require_public_text("category", self.category)
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_decimal("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        for field_name in (
            "cluster_correlation_score",
            "current_category_exposure",
            "liquidity_score",
            "team_fit_score",
            "fit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member(
            "resolution_risk_tier",
            self.resolution_risk_tier,
            RESOLUTION_RISK_TIERS,
        )
        _require_member(
            "portfolio_fit_status",
            self.portfolio_fit_status,
            FIT_STATUSES,
        )
        if type(self.fit_penalties) is not StrategyCandidatePortfolioFitScoreV10Penalties:
            raise ValueError("fit_penalties must be a StrategyCandidatePortfolioFitScoreV10Penalties")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("result", self)
        _require_derived_fields_match(self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_portfolio_fit_score_v10_payload(self)


def score_strategy_candidate_portfolio_fit_v10(
    candidate: StrategyCandidatePortfolioFitScoreV10Input,
) -> StrategyCandidatePortfolioFitScoreV10Result:
    if type(candidate) is not StrategyCandidatePortfolioFitScoreV10Input:
        raise ValueError("candidate must be a StrategyCandidatePortfolioFitScoreV10Input")
    _require_hard_flags("input", candidate)

    fit_penalties = _fit_penalties(candidate)
    fit_score = _fit_score(candidate, fit_penalties)
    hard_blockers = _hard_blockers(candidate)
    status = _portfolio_fit_status(fit_score, hard_blockers)
    reason_codes = _reason_codes(candidate, fit_score, hard_blockers)

    return StrategyCandidatePortfolioFitScoreV10Result(
        market_id=candidate.market_id,
        category=candidate.category,
        cost_adjusted_edge_bps=candidate.cost_adjusted_edge_bps,
        cluster_correlation_score=candidate.cluster_correlation_score,
        current_category_exposure=candidate.current_category_exposure,
        liquidity_score=candidate.liquidity_score,
        resolution_risk_tier=candidate.resolution_risk_tier,
        team_fit_score=candidate.team_fit_score,
        portfolio_fit_status=status,
        fit_score=fit_score,
        fit_penalties=fit_penalties,
        reason_codes=reason_codes,
    )


def strategy_candidate_portfolio_fit_score_v10_payload(
    result: StrategyCandidatePortfolioFitScoreV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidatePortfolioFitScoreV10Result:
        raise ValueError("result must be a StrategyCandidatePortfolioFitScoreV10Result")
    _require_hard_flags("result", result)
    payload = {
        "market_id": result.market_id,
        "category": result.category,
        "cost_adjusted_edge_bps": str(result.cost_adjusted_edge_bps),
        "cluster_correlation_score": str(result.cluster_correlation_score),
        "current_category_exposure": str(result.current_category_exposure),
        "liquidity_score": str(result.liquidity_score),
        "resolution_risk_tier": result.resolution_risk_tier,
        "team_fit_score": str(result.team_fit_score),
        "portfolio_fit_status": result.portfolio_fit_status,
        "fit_score": str(result.fit_score),
        "fit_penalties": _penalties_payload(result.fit_penalties),
        "reason_codes": list(result.reason_codes),
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }
    _require_safe_payload(payload)
    return payload


def _fit_score(
    candidate: StrategyCandidatePortfolioFitScoreV10Input,
    fit_penalties: StrategyCandidatePortfolioFitScoreV10Penalties,
) -> Decimal:
    base_score = _base_fit_score(candidate)
    penalized_score = base_score - fit_penalties.total_penalty
    if penalized_score < ZERO:
        return ZERO
    if penalized_score > ONE:
        return ONE
    return _quantize(penalized_score)


def _base_fit_score(candidate: StrategyCandidatePortfolioFitScoreV10Input) -> Decimal:
    edge_score = _edge_score(candidate.cost_adjusted_edge_bps)
    correlation_quality_score = _quantize(ONE - candidate.cluster_correlation_score)
    category_capacity_score = _quantize(ONE - candidate.current_category_exposure)
    resolution_quality_score = RESOLUTION_RISK_QUALITY[candidate.resolution_risk_tier]
    return _quantize(
        edge_score * EDGE_WEIGHT
        + correlation_quality_score * CORRELATION_WEIGHT
        + category_capacity_score * CATEGORY_EXPOSURE_WEIGHT
        + candidate.liquidity_score * LIQUIDITY_WEIGHT
        + resolution_quality_score * RESOLUTION_RISK_WEIGHT
        + candidate.team_fit_score * TEAM_FIT_WEIGHT,
    )


def _edge_score(cost_adjusted_edge_bps: Decimal) -> Decimal:
    if cost_adjusted_edge_bps <= ZERO:
        return ZERO
    edge_score = cost_adjusted_edge_bps / EDGE_FULL_SCORE_BPS
    if edge_score > ONE:
        return ONE
    return _quantize(edge_score)


def _fit_penalties(
    candidate: StrategyCandidatePortfolioFitScoreV10Input,
) -> StrategyCandidatePortfolioFitScoreV10Penalties:
    return StrategyCandidatePortfolioFitScoreV10Penalties(
        edge_penalty=EDGE_BLOCK_PENALTY
        if candidate.cost_adjusted_edge_bps <= ZERO
        else ZERO,
        correlation_penalty=_excess_penalty(
            candidate.cluster_correlation_score,
            CORRELATION_PENALTY_START,
            CORRELATION_PENALTY_RATE,
        ),
        category_exposure_penalty=_capped_excess_penalty(
            candidate.current_category_exposure,
            CATEGORY_EXPOSURE_PENALTY_START,
            CATEGORY_EXPOSURE_PENALTY_RATE,
            CATEGORY_EXPOSURE_PENALTY_CAP,
        ),
        liquidity_penalty=_shortfall_penalty(
            candidate.liquidity_score,
            LIQUIDITY_PENALTY_START,
            LIQUIDITY_PENALTY_RATE,
        ),
        resolution_risk_penalty=RESOLUTION_RISK_PENALTIES[candidate.resolution_risk_tier],
        team_fit_penalty=_shortfall_penalty(
            candidate.team_fit_score,
            TEAM_FIT_PENALTY_START,
            TEAM_FIT_PENALTY_RATE,
        ),
    )


def _hard_blockers(candidate: StrategyCandidatePortfolioFitScoreV10Input) -> tuple[str, ...]:
    blockers: list[str] = []
    if candidate.cost_adjusted_edge_bps <= ZERO:
        blockers.append("cost_adjusted_edge_nonpositive_blocked")
    if candidate.cluster_correlation_score > CORRELATION_BLOCK_LIMIT:
        blockers.append("cluster_correlation_above_block_limit")
    if candidate.current_category_exposure > CATEGORY_EXPOSURE_BLOCK_LIMIT:
        blockers.append("category_exposure_above_block_limit")
    if candidate.liquidity_score < LIQUIDITY_BLOCK_FLOOR:
        blockers.append("liquidity_score_below_block_floor")
    if candidate.resolution_risk_tier == "critical":
        blockers.append("resolution_risk_critical_blocked")
    if candidate.team_fit_score < TEAM_FIT_BLOCK_FLOOR:
        blockers.append("team_fit_below_block_floor")
    return tuple(blockers)


def _portfolio_fit_status(
    fit_score: Decimal,
    hard_blockers: tuple[str, ...],
) -> str:
    if hard_blockers:
        return "blocked"
    if fit_score >= FIT_SCORE_FLOOR:
        return "fit"
    return "watch"


def _reason_codes(
    candidate: StrategyCandidatePortfolioFitScoreV10Input,
    fit_score: Decimal,
    hard_blockers: tuple[str, ...],
) -> tuple[str, ...]:
    if hard_blockers:
        return hard_blockers

    codes: list[str] = [
        "fit_score_meets_floor"
        if fit_score >= FIT_SCORE_FLOOR
        else "fit_score_below_fit_floor",
    ]
    codes.append("positive_cost_adjusted_edge")
    codes.append(
        "cluster_correlation_penalty_applied"
        if candidate.cluster_correlation_score > CORRELATION_PENALTY_START
        else "cluster_correlation_within_limit",
    )
    codes.append(
        "category_exposure_penalty_applied"
        if candidate.current_category_exposure > CATEGORY_EXPOSURE_PENALTY_START
        else "category_exposure_within_limit",
    )
    codes.append(
        "liquidity_penalty_applied"
        if candidate.liquidity_score < LIQUIDITY_PENALTY_START
        else "liquidity_score_supported",
    )
    if candidate.resolution_risk_tier == "low":
        codes.append("resolution_risk_low")
    else:
        codes.append(f"resolution_risk_{candidate.resolution_risk_tier}_penalty_applied")
    codes.append(
        "team_fit_penalty_applied"
        if candidate.team_fit_score < TEAM_FIT_PENALTY_START
        else "team_fit_supported",
    )
    if fit_score >= FIT_SCORE_FLOOR:
        codes.append("portfolio_fit_clear")
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _excess_penalty(value: Decimal, start: Decimal, rate: Decimal) -> Decimal:
    if value <= start:
        return ZERO
    return _quantize((value - start) * rate)


def _capped_excess_penalty(
    value: Decimal,
    start: Decimal,
    rate: Decimal,
    cap: Decimal,
) -> Decimal:
    penalty = _excess_penalty(value, start, rate)
    if penalty > cap:
        return cap
    return penalty


def _shortfall_penalty(value: Decimal, floor: Decimal, rate: Decimal) -> Decimal:
    if value >= floor:
        return ZERO
    return _quantize((floor - value) * rate)


def _penalties_payload(
    penalties: StrategyCandidatePortfolioFitScoreV10Penalties,
) -> dict[str, str]:
    return {
        "edge_penalty": str(penalties.edge_penalty),
        "correlation_penalty": str(penalties.correlation_penalty),
        "category_exposure_penalty": str(penalties.category_exposure_penalty),
        "liquidity_penalty": str(penalties.liquidity_penalty),
        "resolution_risk_penalty": str(penalties.resolution_risk_penalty),
        "team_fit_penalty": str(penalties.team_fit_penalty),
        "total_penalty": str(penalties.total_penalty),
    }


def _require_derived_fields_match(result: StrategyCandidatePortfolioFitScoreV10Result) -> None:
    candidate = StrategyCandidatePortfolioFitScoreV10Input(
        market_id=result.market_id,
        category=result.category,
        cost_adjusted_edge_bps=result.cost_adjusted_edge_bps,
        cluster_correlation_score=result.cluster_correlation_score,
        current_category_exposure=result.current_category_exposure,
        liquidity_score=result.liquidity_score,
        resolution_risk_tier=result.resolution_risk_tier,
        team_fit_score=result.team_fit_score,
        paper_only=result.paper_only,
        report_only=result.report_only,
        readonly=result.readonly,
    )
    expected_penalties = _fit_penalties(candidate)
    if result.fit_penalties != expected_penalties:
        raise ValueError("fit_penalties must match portfolio-fit inputs")
    expected_fit_score = _fit_score(candidate, expected_penalties)
    if result.fit_score != expected_fit_score:
        raise ValueError("fit_score must match portfolio-fit inputs")
    hard_blockers = _hard_blockers(candidate)
    expected_status = _portfolio_fit_status(expected_fit_score, hard_blockers)
    if result.portfolio_fit_status != expected_status:
        raise ValueError("portfolio_fit_status must match portfolio-fit inputs")
    expected_reason_codes = _reason_codes(candidate, expected_fit_score, hard_blockers)
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match portfolio-fit inputs")


def _require_safe_payload(value: Any) -> None:
    if type(value) in (str, bool):
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_safe_payload(item)
        return
    if type(value) is list:
        for item in value:
            _require_safe_payload(item)
        return
    if type(value) is Decimal:
        raise ValueError("payload Decimal values must be rendered as strings")
    if type(value) is float:
        raise ValueError("payload float values are not supported")
    raise ValueError("payload contains unsupported value")


def _normalize_ratio(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_member(field_name, reason_code, REASON_CODES)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    return value


def _require_identifier(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_public_text(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty text")
    if any(character in "\r\n\t" for character in value):
        raise ValueError(f"{field_name} must be single-line text")


def _require_member(field_name: str, value: Any, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "StrategyCandidatePortfolioFitScoreV10Input",
    "StrategyCandidatePortfolioFitScoreV10Penalties",
    "StrategyCandidatePortfolioFitScoreV10Result",
    "score_strategy_candidate_portfolio_fit_v10",
    "strategy_candidate_portfolio_fit_score_v10_payload",
)

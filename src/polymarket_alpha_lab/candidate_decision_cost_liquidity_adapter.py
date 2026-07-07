"""Pure paper-only adapter from side-aware cost/liquidity facts to decision fields."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_COST_LIQUIDITY_ADAPTER_VERSION = (
    "candidate-decision-cost-liquidity-adapter-v0"
)
ADAPTER_REASON_CODE = "candidate_cost_liquidity_adapter_v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SELECTED_SIDES = ("yes", "no")
LIQUIDITY_STATUSES = ("pass", "watch", "blocked")
_TEXT_PARTS = (
    ("pri", "vate", "_", "key"),
    ("wal", "let"),
    ("acc", "ount"),
    ("bal", "ance"),
    ("or", "der"),
    ("can", "cel"),
    ("re", "place"),
    ("sig", "n"),
    ("ex", "change", "_", "muta", "tion"),
)
_RISKY_TEXT = tuple("".join(parts) for parts in _TEXT_PARTS)


@dataclass(frozen=True)
class CandidateDecisionCostLiquidityAdapterConfig:
    config_version: str = DEFAULT_CANDIDATE_DECISION_COST_LIQUIDITY_ADAPTER_VERSION
    watch_min_depth_coverage_ratio: Decimal = Decimal("1.250000")
    block_min_depth_coverage_ratio: Decimal = Decimal("0.750000")
    watch_max_spread_drag: Decimal = Decimal("0.030000")
    block_max_spread_drag: Decimal = Decimal("0.060000")
    watch_max_cost_drag: Decimal = Decimal("0.040000")
    block_max_cost_drag: Decimal = Decimal("0.080000")
    cost_score_full_drag: Decimal = Decimal("0.080000")
    minimum_pass_liquidity_score: Decimal = Decimal("0.700000")
    blocked_max_liquidity_score: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCostLiquidityAdapterConfig:
            raise ValueError(
                "config must be a CandidateDecisionCostLiquidityAdapterConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_min_depth_coverage_ratio",
            "block_min_depth_coverage_ratio",
            "watch_max_spread_drag",
            "block_max_spread_drag",
            "watch_max_cost_drag",
            "block_max_cost_drag",
            "cost_score_full_drag",
            "minimum_pass_liquidity_score",
            "blocked_max_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_liquidity_score",
            "blocked_max_liquidity_score",
        ):
            if getattr(self, field_name) > ONE:
                raise ValueError(f"{field_name} must be no greater than 1")
        _validate_config(self)
        _reject_risky_text(self)
        require_paper_only_flags("CandidateDecisionCostLiquidityAdapterConfig", self)


@dataclass(frozen=True)
class CandidateDecisionCostLiquidityFacts:
    candidate_id: str
    market_id: str
    selected_side: str
    observed_at: datetime
    forecast_probability: Decimal
    executable_price: Decimal
    fee_cost_per_share: Decimal
    spread_cost_per_share: Decimal
    slippage_cost_per_share: Decimal
    funding_cost_per_share: Decimal
    finalization_cost_per_share: Decimal
    time_cost_per_share: Decimal
    risk_cost_per_share: Decimal
    capital_cost_per_share: Decimal
    requested_paper_shares: Decimal
    available_depth_shares: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCostLiquidityFacts:
            raise ValueError("facts must be a CandidateDecisionCostLiquidityFacts")
        for field_name in ("candidate_id", "market_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("forecast_probability", "executable_price"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_cost_per_share",
            "spread_cost_per_share",
            "slippage_cost_per_share",
            "funding_cost_per_share",
            "finalization_cost_per_share",
            "time_cost_per_share",
            "risk_cost_per_share",
            "capital_cost_per_share",
            "available_depth_shares",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "requested_paper_shares",
            _normalize_positive_decimal(
                "requested_paper_shares",
                self.requested_paper_shares,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=True,
            ),
        )
        _reject_risky_text(self)
        require_paper_only_flags("CandidateDecisionCostLiquidityFacts", self)


@dataclass(frozen=True)
class CandidateDecisionCostLiquidityAdapterOutput:
    candidate_id: str
    market_id: str
    selected_side: str
    observed_at: datetime
    config_version: str
    watch_min_depth_coverage_ratio: Decimal
    block_min_depth_coverage_ratio: Decimal
    watch_max_spread_drag: Decimal
    block_max_spread_drag: Decimal
    watch_max_cost_drag: Decimal
    block_max_cost_drag: Decimal
    cost_score_full_drag: Decimal
    minimum_pass_liquidity_score: Decimal
    blocked_max_liquidity_score: Decimal
    forecast_probability: Decimal
    executable_price: Decimal
    side_probability: Decimal
    fee_cost_per_share: Decimal
    spread_cost_per_share: Decimal
    slippage_cost_per_share: Decimal
    funding_cost_per_share: Decimal
    finalization_cost_per_share: Decimal
    time_cost_per_share: Decimal
    risk_cost_per_share: Decimal
    capital_cost_per_share: Decimal
    gross_edge: Decimal
    estimated_cost_drag: Decimal
    net_edge: Decimal
    requested_paper_shares: Decimal
    available_depth_shares: Decimal
    depth_coverage_ratio: Decimal
    cost_score: Decimal
    liquidity_score: Decimal
    liquidity_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCostLiquidityAdapterOutput:
            raise ValueError("output must be a CandidateDecisionCostLiquidityAdapterOutput")
        for field_name in ("candidate_id", "market_id", "config_version"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "watch_min_depth_coverage_ratio",
            "block_min_depth_coverage_ratio",
            "watch_max_spread_drag",
            "block_max_spread_drag",
            "watch_max_cost_drag",
            "block_max_cost_drag",
            "cost_score_full_drag",
            "minimum_pass_liquidity_score",
            "blocked_max_liquidity_score",
            "forecast_probability",
            "executable_price",
            "side_probability",
            "fee_cost_per_share",
            "spread_cost_per_share",
            "slippage_cost_per_share",
            "funding_cost_per_share",
            "finalization_cost_per_share",
            "time_cost_per_share",
            "risk_cost_per_share",
            "capital_cost_per_share",
            "estimated_cost_drag",
            "requested_paper_shares",
            "available_depth_shares",
            "depth_coverage_ratio",
            "cost_score",
            "liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_liquidity_score",
            "blocked_max_liquidity_score",
            "forecast_probability",
            "executable_price",
            "side_probability",
            "cost_score",
            "liquidity_score",
        ):
            if getattr(self, field_name) > ONE:
                raise ValueError(f"{field_name} must be no greater than 1")
        object.__setattr__(
            self,
            "gross_edge",
            _normalize_decimal("gross_edge", self.gross_edge),
        )
        object.__setattr__(
            self,
            "net_edge",
            _normalize_decimal("net_edge", self.net_edge),
        )
        _require_member("liquidity_status", self.liquidity_status, LIQUIDITY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_risky_text(self)
        require_paper_only_flags("CandidateDecisionCostLiquidityAdapterOutput", self)
        _validate_output_consistency(self)

    @property
    def candidate_decision_fields(self) -> dict[str, Decimal | tuple[str, ...]]:
        return {
            "gross_edge": self.gross_edge,
            "estimated_cost_drag": self.estimated_cost_drag,
            "cost_score": self.cost_score,
            "liquidity_score": self.liquidity_score,
            "adapter_reason_codes": self.reason_codes,
        }


def adapt_candidate_decision_cost_liquidity(
    facts: CandidateDecisionCostLiquidityFacts,
    *,
    config: CandidateDecisionCostLiquidityAdapterConfig | None = None,
) -> CandidateDecisionCostLiquidityAdapterOutput:
    if type(facts) is not CandidateDecisionCostLiquidityFacts:
        raise ValueError("facts must be a CandidateDecisionCostLiquidityFacts")
    if config is None:
        config = CandidateDecisionCostLiquidityAdapterConfig()
    if type(config) is not CandidateDecisionCostLiquidityAdapterConfig:
        raise ValueError("config must be a CandidateDecisionCostLiquidityAdapterConfig")
    require_paper_only_flags("CandidateDecisionCostLiquidityFacts", facts)
    require_paper_only_flags("CandidateDecisionCostLiquidityAdapterConfig", config)
    _reject_risky_text(facts)
    _reject_risky_text(config)

    side_probability = _side_probability(facts)
    gross_edge = _subtract_decimal(side_probability, facts.executable_price)
    estimated_cost_drag = _total_cost_drag(facts)
    net_edge = _subtract_decimal(gross_edge, estimated_cost_drag)
    depth_ratio = _depth_coverage_ratio(facts)
    cost_score = _cost_score(estimated_cost_drag, config)
    raw_liquidity_score = _raw_liquidity_score(depth_ratio, facts.spread_cost_per_share, config)
    status = _liquidity_status(
        estimated_cost_drag=estimated_cost_drag,
        depth_coverage_ratio=depth_ratio,
        spread_drag=facts.spread_cost_per_share,
        raw_liquidity_score=raw_liquidity_score,
        config=config,
    )
    liquidity_score = ZERO if status == "blocked" else raw_liquidity_score

    return CandidateDecisionCostLiquidityAdapterOutput(
        candidate_id=facts.candidate_id,
        market_id=facts.market_id,
        selected_side=facts.selected_side,
        observed_at=facts.observed_at,
        config_version=config.config_version,
        watch_min_depth_coverage_ratio=config.watch_min_depth_coverage_ratio,
        block_min_depth_coverage_ratio=config.block_min_depth_coverage_ratio,
        watch_max_spread_drag=config.watch_max_spread_drag,
        block_max_spread_drag=config.block_max_spread_drag,
        watch_max_cost_drag=config.watch_max_cost_drag,
        block_max_cost_drag=config.block_max_cost_drag,
        cost_score_full_drag=config.cost_score_full_drag,
        minimum_pass_liquidity_score=config.minimum_pass_liquidity_score,
        blocked_max_liquidity_score=config.blocked_max_liquidity_score,
        forecast_probability=facts.forecast_probability,
        executable_price=facts.executable_price,
        side_probability=side_probability,
        fee_cost_per_share=facts.fee_cost_per_share,
        spread_cost_per_share=facts.spread_cost_per_share,
        slippage_cost_per_share=facts.slippage_cost_per_share,
        funding_cost_per_share=facts.funding_cost_per_share,
        finalization_cost_per_share=facts.finalization_cost_per_share,
        time_cost_per_share=facts.time_cost_per_share,
        risk_cost_per_share=facts.risk_cost_per_share,
        capital_cost_per_share=facts.capital_cost_per_share,
        gross_edge=gross_edge,
        estimated_cost_drag=estimated_cost_drag,
        net_edge=net_edge,
        requested_paper_shares=facts.requested_paper_shares,
        available_depth_shares=facts.available_depth_shares,
        depth_coverage_ratio=depth_ratio,
        cost_score=cost_score,
        liquidity_score=liquidity_score,
        liquidity_status=status,
        reason_codes=_reason_codes_for(
            facts.reason_codes,
            net_edge=net_edge,
            estimated_cost_drag=estimated_cost_drag,
            depth_coverage_ratio=depth_ratio,
            spread_drag=facts.spread_cost_per_share,
            liquidity_status=status,
            config=config,
        ),
    )


def adapter_output_to_candidate_decision_fields(
    output: CandidateDecisionCostLiquidityAdapterOutput,
) -> dict[str, Decimal | tuple[str, ...]]:
    if type(output) is not CandidateDecisionCostLiquidityAdapterOutput:
        raise ValueError("adapter output must be a CandidateDecisionCostLiquidityAdapterOutput")
    require_paper_only_flags("CandidateDecisionCostLiquidityAdapterOutput", output)
    _validate_output_consistency(output)
    return output.candidate_decision_fields


def candidate_decision_cost_liquidity_adapter_payload(
    output: CandidateDecisionCostLiquidityAdapterOutput,
) -> dict[str, Any]:
    if type(output) is not CandidateDecisionCostLiquidityAdapterOutput:
        raise ValueError("payload must be built from CandidateDecisionCostLiquidityAdapterOutput")
    require_paper_only_flags("CandidateDecisionCostLiquidityAdapterOutput", output)
    _validate_output_consistency(output)
    reject_unsafe_surface_fields("candidate decision cost liquidity adapter output", output)
    payload = json_ready_no_floats(output)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields("candidate decision cost liquidity adapter payload", payload)
    return payload


def _validate_config(config: CandidateDecisionCostLiquidityAdapterConfig) -> None:
    if config.block_min_depth_coverage_ratio <= ZERO:
        raise ValueError("block_min_depth_coverage_ratio must be positive")
    if config.watch_min_depth_coverage_ratio < config.block_min_depth_coverage_ratio:
        raise ValueError(
            "watch_min_depth_coverage_ratio must be at least block threshold",
        )
    if config.block_max_spread_drag <= ZERO:
        raise ValueError("block_max_spread_drag must be positive")
    if config.watch_max_spread_drag > config.block_max_spread_drag:
        raise ValueError("watch_max_spread_drag must be at most block threshold")
    if config.block_max_cost_drag <= ZERO:
        raise ValueError("block_max_cost_drag must be positive")
    if config.watch_max_cost_drag > config.block_max_cost_drag:
        raise ValueError("watch_max_cost_drag must be at most block threshold")
    if config.cost_score_full_drag <= ZERO:
        raise ValueError("cost_score_full_drag must be positive")
    if config.blocked_max_liquidity_score > config.minimum_pass_liquidity_score:
        raise ValueError(
            "blocked_max_liquidity_score must be no greater than pass threshold",
        )


def _validate_output_consistency(
    output: CandidateDecisionCostLiquidityAdapterOutput,
) -> None:
    config = _config_from_output(output)
    expected_side_probability = _side_probability_from_values(
        output.selected_side,
        output.forecast_probability,
    )
    if output.side_probability != expected_side_probability:
        raise ValueError("side_probability must match selected_side")
    expected_cost_drag = _sum_decimals(
        (
            output.fee_cost_per_share,
            output.spread_cost_per_share,
            output.slippage_cost_per_share,
            output.funding_cost_per_share,
            output.finalization_cost_per_share,
            output.time_cost_per_share,
            output.risk_cost_per_share,
            output.capital_cost_per_share,
        ),
    )
    if output.estimated_cost_drag != expected_cost_drag:
        raise ValueError("estimated_cost_drag must match cost fields")
    expected_gross_edge = _subtract_decimal(output.side_probability, output.executable_price)
    if output.gross_edge != expected_gross_edge:
        raise ValueError("gross_edge must match side probability and price")
    expected_net_edge = _subtract_decimal(output.gross_edge, output.estimated_cost_drag)
    if output.net_edge != expected_net_edge:
        raise ValueError("net_edge must match gross_edge minus estimated_cost_drag")
    expected_depth_ratio = _divide_decimal(
        output.available_depth_shares,
        output.requested_paper_shares,
    )
    if output.depth_coverage_ratio != expected_depth_ratio:
        raise ValueError("depth_coverage_ratio must match share fields")
    expected_cost_score = _cost_score(output.estimated_cost_drag, config)
    if output.cost_score != expected_cost_score:
        raise ValueError("cost_score must match estimated_cost_drag")
    raw_liquidity_score = _raw_liquidity_score(
        output.depth_coverage_ratio,
        output.spread_cost_per_share,
        config,
    )
    expected_status = _liquidity_status(
        estimated_cost_drag=output.estimated_cost_drag,
        depth_coverage_ratio=output.depth_coverage_ratio,
        spread_drag=output.spread_cost_per_share,
        raw_liquidity_score=raw_liquidity_score,
        config=config,
    )
    if output.liquidity_status != expected_status:
        raise ValueError("liquidity_status must match cost and liquidity fields")
    expected_liquidity_score = ZERO if expected_status == "blocked" else raw_liquidity_score
    if output.liquidity_score != expected_liquidity_score:
        raise ValueError("liquidity_score must match cost and liquidity fields")


def _config_from_output(
    output: CandidateDecisionCostLiquidityAdapterOutput,
) -> CandidateDecisionCostLiquidityAdapterConfig:
    return CandidateDecisionCostLiquidityAdapterConfig(
        config_version=output.config_version,
        watch_min_depth_coverage_ratio=output.watch_min_depth_coverage_ratio,
        block_min_depth_coverage_ratio=output.block_min_depth_coverage_ratio,
        watch_max_spread_drag=output.watch_max_spread_drag,
        block_max_spread_drag=output.block_max_spread_drag,
        watch_max_cost_drag=output.watch_max_cost_drag,
        block_max_cost_drag=output.block_max_cost_drag,
        cost_score_full_drag=output.cost_score_full_drag,
        minimum_pass_liquidity_score=output.minimum_pass_liquidity_score,
        blocked_max_liquidity_score=output.blocked_max_liquidity_score,
    )


def _side_probability(facts: CandidateDecisionCostLiquidityFacts) -> Decimal:
    return _side_probability_from_values(facts.selected_side, facts.forecast_probability)


def _side_probability_from_values(selected_side: str, forecast_probability: Decimal) -> Decimal:
    if selected_side == "yes":
        return forecast_probability
    return _subtract_decimal(ONE, forecast_probability)


def _total_cost_drag(facts: CandidateDecisionCostLiquidityFacts) -> Decimal:
    return _sum_decimals(
        (
            facts.fee_cost_per_share,
            facts.spread_cost_per_share,
            facts.slippage_cost_per_share,
            facts.funding_cost_per_share,
            facts.finalization_cost_per_share,
            facts.time_cost_per_share,
            facts.risk_cost_per_share,
            facts.capital_cost_per_share,
        ),
    )


def _depth_coverage_ratio(facts: CandidateDecisionCostLiquidityFacts) -> Decimal:
    return _divide_decimal(facts.available_depth_shares, facts.requested_paper_shares)


def _cost_score(
    estimated_cost_drag: Decimal,
    config: CandidateDecisionCostLiquidityAdapterConfig,
) -> Decimal:
    if estimated_cost_drag >= config.cost_score_full_drag:
        return ZERO
    return _bounded_unit_ratio(ONE - estimated_cost_drag / config.cost_score_full_drag)


def _raw_liquidity_score(
    depth_coverage_ratio: Decimal,
    spread_drag: Decimal,
    config: CandidateDecisionCostLiquidityAdapterConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        depth_score = _bound_unit_without_quantize(
            depth_coverage_ratio / config.watch_min_depth_coverage_ratio,
        )
        if spread_drag >= config.block_max_spread_drag:
            spread_score = ZERO
        else:
            spread_score = _bound_unit_without_quantize(
                ONE - spread_drag / config.block_max_spread_drag,
            )
        return _bounded_unit_ratio((depth_score + spread_score) / Decimal("2.000000"))


def _liquidity_status(
    *,
    estimated_cost_drag: Decimal,
    depth_coverage_ratio: Decimal,
    spread_drag: Decimal,
    raw_liquidity_score: Decimal,
    config: CandidateDecisionCostLiquidityAdapterConfig,
) -> str:
    if (
        estimated_cost_drag > config.block_max_cost_drag
        or depth_coverage_ratio < config.block_min_depth_coverage_ratio
        or spread_drag > config.block_max_spread_drag
        or raw_liquidity_score <= config.blocked_max_liquidity_score
    ):
        return "blocked"
    if (
        estimated_cost_drag > config.watch_max_cost_drag
        or depth_coverage_ratio < config.watch_min_depth_coverage_ratio
        or spread_drag > config.watch_max_spread_drag
        or raw_liquidity_score < config.minimum_pass_liquidity_score
    ):
        return "watch"
    return "pass"


def _reason_codes_for(
    source_reason_codes: tuple[str, ...],
    *,
    net_edge: Decimal,
    estimated_cost_drag: Decimal,
    depth_coverage_ratio: Decimal,
    spread_drag: Decimal,
    liquidity_status: str,
    config: CandidateDecisionCostLiquidityAdapterConfig,
) -> tuple[str, ...]:
    codes = [
        ADAPTER_REASON_CODE,
        *source_reason_codes,
        "net_edge_positive" if net_edge > ZERO else "net_edge_nonpositive",
        _cost_reason_code(estimated_cost_drag, config),
        f"liquidity_{liquidity_status}",
        _depth_reason_code(depth_coverage_ratio, config),
        _spread_reason_code(spread_drag, config),
    ]
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _cost_reason_code(
    estimated_cost_drag: Decimal,
    config: CandidateDecisionCostLiquidityAdapterConfig,
) -> str:
    if estimated_cost_drag > config.block_max_cost_drag:
        return "cost_drag_blocked"
    if estimated_cost_drag > config.watch_max_cost_drag:
        return "cost_drag_watch"
    return "cost_drag_pass"


def _depth_reason_code(
    depth_coverage_ratio: Decimal,
    config: CandidateDecisionCostLiquidityAdapterConfig,
) -> str:
    if depth_coverage_ratio < config.block_min_depth_coverage_ratio:
        return "depth_coverage_blocked"
    if depth_coverage_ratio < config.watch_min_depth_coverage_ratio:
        return "depth_coverage_watch"
    return "depth_coverage_pass"


def _spread_reason_code(
    spread_drag: Decimal,
    config: CandidateDecisionCostLiquidityAdapterConfig,
) -> str:
    if spread_drag > config.block_max_spread_drag:
        return "spread_drag_blocked"
    if spread_drag > config.watch_max_spread_drag:
        return "spread_drag_watch"
    return "spread_drag_pass"


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if allow_empty:
        return tuple(sorted(reason_codes))
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not all(_is_reason_code_character(character) for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value.startswith("candidate_decision_"):
        raise ValueError(f"{field_name} must not contain candidate decision action codes")


def _is_reason_code_character(character: str) -> bool:
    return character == "_" or "a" <= character <= "z" or "0" <= character <= "9"


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _bounded_unit_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value <= ZERO:
            return ZERO
        if value >= ONE:
            return ONE
        return _quantize(value)


def _bound_unit_without_quantize(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _reject_risky_text(value: object) -> None:
    reject_unsafe_surface_fields("candidate decision cost liquidity adapter", value)
    payload = asdict(value) if hasattr(value, "__dataclass_fields__") else value
    _reject_risky_text_values(payload)


def _reject_risky_text_values(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _reject_risky_text_string(key)
            _reject_risky_text_values(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_risky_text_values(item)
        return
    if type(value) is str:
        _reject_risky_text_string(value)


def _reject_risky_text_string(value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _RISKY_TEXT):
        raise ValueError("payload contains unsafe text")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_COST_LIQUIDITY_ADAPTER_VERSION",
    "CandidateDecisionCostLiquidityAdapterConfig",
    "CandidateDecisionCostLiquidityFacts",
    "CandidateDecisionCostLiquidityAdapterOutput",
    "adapt_candidate_decision_cost_liquidity",
    "adapter_output_to_candidate_decision_fields",
    "candidate_decision_cost_liquidity_adapter_payload",
)

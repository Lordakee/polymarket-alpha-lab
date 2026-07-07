"""Pure paper-only cost threshold guidance for candidate decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_COST_THRESHOLDS_VERSION = "candidate-cost-thresholds-v0"
BOUNDARY_STATEMENT = "Paper-only cost threshold guidance; no trading execution."
REASON_CODE = "candidate_cost_thresholds_v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SELECTED_SIDES = ("yes", "no")
ACTIONS = ("reject", "watch", "research_more", "paper_recommend")
HARD_SAFETY_FLAGS = (
    "paper_only",
    "report_only",
    "readonly",
    "execution_disabled",
)
_TEXT_PARTS = (
    ("pri", "vate", "_", "key"),
    ("wal", "let"),
    ("acc", "ount"),
    ("bal", "ance"),
    ("or", "der"),
    ("can", "cel"),
    ("re", "place"),
    ("si", "gn"),
    ("ex", "change"),
)
_RISKY_TEXT = tuple("".join(parts) for parts in _TEXT_PARTS)


@dataclass(frozen=True)
class CandidateDecisionCostThresholdConfig:
    config_version: str = DEFAULT_CANDIDATE_DECISION_COST_THRESHOLDS_VERSION
    min_net_edge_for_watch: Decimal = Decimal("0.000000")
    min_net_edge_for_research_more: Decimal = Decimal("0.005000")
    min_net_edge_for_paper_recommend: Decimal = Decimal("0.015000")
    transaction_cost_buffer: Decimal = Decimal("0.002000")
    settlement_cash_lockup_buffer: Decimal = Decimal("0.001000")
    model_uncertainty_buffer: Decimal = Decimal("0.002000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCostThresholdConfig:
            raise ValueError("config must be a CandidateDecisionCostThresholdConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_net_edge_for_watch",
            "min_net_edge_for_research_more",
            "min_net_edge_for_paper_recommend",
            "transaction_cost_buffer",
            "settlement_cash_lockup_buffer",
            "model_uncertainty_buffer",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _reject_risky_text(self)
        require_paper_only_flags("CandidateDecisionCostThresholdConfig", self)


@dataclass(frozen=True)
class CandidateDecisionCostThresholdInput:
    redacted_candidate_ref: str
    redacted_market_ref: str
    selected_side: str
    gross_edge: Decimal
    taker_fee_drag: Decimal
    spread_cost: Decimal
    slippage: Decimal
    settlement_cash_lockup_drag: Decimal
    source_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCostThresholdInput:
            raise ValueError("input_value must be a CandidateDecisionCostThresholdInput")
        for field_name in ("redacted_candidate_ref", "redacted_market_ref"):
            object.__setattr__(
                self,
                field_name,
                _normalize_redacted_ref(field_name, getattr(self, field_name)),
            )
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        object.__setattr__(self, "gross_edge", _normalize_decimal("gross_edge", self.gross_edge))
        for field_name in (
            "taker_fee_drag",
            "spread_cost",
            "slippage",
            "settlement_cash_lockup_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_source_reason_codes("source_reason_codes", self.source_reason_codes),
        )
        _reject_risky_text(self)
        require_paper_only_flags("CandidateDecisionCostThresholdInput", self)


@dataclass(frozen=True)
class CandidateDecisionCostThresholdOutput:
    redacted_candidate_ref: str
    redacted_market_ref: str
    selected_side: str
    config_version: str
    min_net_edge_for_watch: Decimal
    min_net_edge_for_research_more: Decimal
    min_net_edge_for_paper_recommend: Decimal
    transaction_cost_buffer: Decimal
    settlement_cash_lockup_buffer: Decimal
    model_uncertainty_buffer: Decimal
    gross_edge: Decimal
    taker_fee_drag: Decimal
    spread_cost: Decimal
    slippage: Decimal
    transaction_cost_drag: Decimal
    settlement_cash_lockup_drag: Decimal
    total_cost_drag: Decimal
    total_buffer_drag: Decimal
    net_edge_before_buffers: Decimal
    net_edge_after_buffers: Decimal
    required_gross_edge_for_watch: Decimal
    required_gross_edge_for_research_more: Decimal
    required_gross_edge_for_paper_recommend: Decimal
    action: str
    reason_codes: tuple[str, ...]
    source_reason_codes: tuple[str, ...]
    hard_safety_flags: tuple[str, ...]
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCostThresholdOutput:
            raise ValueError("output must be a CandidateDecisionCostThresholdOutput")
        for field_name in ("redacted_candidate_ref", "redacted_market_ref"):
            object.__setattr__(
                self,
                field_name,
                _normalize_redacted_ref(field_name, getattr(self, field_name)),
            )
        for field_name in ("config_version",):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        for field_name in (
            "min_net_edge_for_watch",
            "min_net_edge_for_research_more",
            "min_net_edge_for_paper_recommend",
            "transaction_cost_buffer",
            "settlement_cash_lockup_buffer",
            "model_uncertainty_buffer",
            "taker_fee_drag",
            "spread_cost",
            "slippage",
            "transaction_cost_drag",
            "settlement_cash_lockup_drag",
            "total_cost_drag",
            "total_buffer_drag",
            "required_gross_edge_for_watch",
            "required_gross_edge_for_research_more",
            "required_gross_edge_for_paper_recommend",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_edge",
            "net_edge_before_buffers",
            "net_edge_after_buffers",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("action", self.action, ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_output_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_source_reason_codes("source_reason_codes", self.source_reason_codes),
        )
        object.__setattr__(
            self,
            "hard_safety_flags",
            _normalize_hard_safety_flags(self.hard_safety_flags),
        )
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        _validate_config(_config_from_output(self))
        _reject_risky_text(self)
        require_paper_only_flags("CandidateDecisionCostThresholdOutput", self)
        _validate_output_consistency(self)

    @property
    def candidate_decision_fields(self) -> dict[str, Decimal | str | tuple[str, ...]]:
        return {
            "action": self.action,
            "gross_edge": self.gross_edge,
            "transaction_cost_drag": self.transaction_cost_drag,
            "settlement_cash_lockup_drag": self.settlement_cash_lockup_drag,
            "total_cost_drag": self.total_cost_drag,
            "total_buffer_drag": self.total_buffer_drag,
            "net_edge_before_buffers": self.net_edge_before_buffers,
            "net_edge_after_buffers": self.net_edge_after_buffers,
            "required_gross_edge_for_paper_recommend": (
                self.required_gross_edge_for_paper_recommend
            ),
            "reason_codes": self.reason_codes,
            "hard_safety_flags": self.hard_safety_flags,
        }


def evaluate_candidate_decision_cost_thresholds(
    input_value: CandidateDecisionCostThresholdInput,
    *,
    config: CandidateDecisionCostThresholdConfig | None = None,
) -> CandidateDecisionCostThresholdOutput:
    if type(input_value) is not CandidateDecisionCostThresholdInput:
        raise ValueError("input_value must be a CandidateDecisionCostThresholdInput")
    if config is None:
        config = CandidateDecisionCostThresholdConfig()
    if type(config) is not CandidateDecisionCostThresholdConfig:
        raise ValueError("config must be a CandidateDecisionCostThresholdConfig")
    require_paper_only_flags("CandidateDecisionCostThresholdInput", input_value)
    require_paper_only_flags("CandidateDecisionCostThresholdConfig", config)
    _reject_risky_text(input_value)
    _reject_risky_text(config)

    transaction_cost_drag = _sum_decimals(
        (
            input_value.taker_fee_drag,
            input_value.spread_cost,
            input_value.slippage,
        ),
    )
    total_cost_drag = _add_decimal(
        transaction_cost_drag,
        input_value.settlement_cash_lockup_drag,
    )
    total_buffer_drag = _sum_decimals(
        (
            config.transaction_cost_buffer,
            config.settlement_cash_lockup_buffer,
            config.model_uncertainty_buffer,
        ),
    )
    net_edge_before_buffers = _subtract_decimal(input_value.gross_edge, total_cost_drag)
    net_edge_after_buffers = _subtract_decimal(net_edge_before_buffers, total_buffer_drag)
    required_gross_edge_for_watch = _required_gross_edge(
        config.min_net_edge_for_watch,
        total_cost_drag,
        total_buffer_drag,
    )
    required_gross_edge_for_research_more = _required_gross_edge(
        config.min_net_edge_for_research_more,
        total_cost_drag,
        total_buffer_drag,
    )
    required_gross_edge_for_paper_recommend = _required_gross_edge(
        config.min_net_edge_for_paper_recommend,
        total_cost_drag,
        total_buffer_drag,
    )
    action = _action_for(net_edge_after_buffers, config)

    return CandidateDecisionCostThresholdOutput(
        redacted_candidate_ref=input_value.redacted_candidate_ref,
        redacted_market_ref=input_value.redacted_market_ref,
        selected_side=input_value.selected_side,
        config_version=config.config_version,
        min_net_edge_for_watch=config.min_net_edge_for_watch,
        min_net_edge_for_research_more=config.min_net_edge_for_research_more,
        min_net_edge_for_paper_recommend=config.min_net_edge_for_paper_recommend,
        transaction_cost_buffer=config.transaction_cost_buffer,
        settlement_cash_lockup_buffer=config.settlement_cash_lockup_buffer,
        model_uncertainty_buffer=config.model_uncertainty_buffer,
        gross_edge=input_value.gross_edge,
        taker_fee_drag=input_value.taker_fee_drag,
        spread_cost=input_value.spread_cost,
        slippage=input_value.slippage,
        transaction_cost_drag=transaction_cost_drag,
        settlement_cash_lockup_drag=input_value.settlement_cash_lockup_drag,
        total_cost_drag=total_cost_drag,
        total_buffer_drag=total_buffer_drag,
        net_edge_before_buffers=net_edge_before_buffers,
        net_edge_after_buffers=net_edge_after_buffers,
        required_gross_edge_for_watch=required_gross_edge_for_watch,
        required_gross_edge_for_research_more=required_gross_edge_for_research_more,
        required_gross_edge_for_paper_recommend=required_gross_edge_for_paper_recommend,
        action=action,
        reason_codes=_reason_codes_for(
            action=action,
            net_edge_after_buffers=net_edge_after_buffers,
            transaction_cost_drag=transaction_cost_drag,
            settlement_cash_lockup_drag=input_value.settlement_cash_lockup_drag,
            total_buffer_drag=total_buffer_drag,
            source_reason_codes=input_value.source_reason_codes,
        ),
        source_reason_codes=input_value.source_reason_codes,
        hard_safety_flags=HARD_SAFETY_FLAGS,
    )


def cost_thresholds_to_candidate_decision_fields(
    output: CandidateDecisionCostThresholdOutput,
) -> dict[str, Decimal | str | tuple[str, ...]]:
    if type(output) is not CandidateDecisionCostThresholdOutput:
        raise ValueError("output must be a CandidateDecisionCostThresholdOutput")
    require_paper_only_flags("CandidateDecisionCostThresholdOutput", output)
    _validate_output_consistency(output)
    return output.candidate_decision_fields


def candidate_decision_cost_threshold_payload(
    output: CandidateDecisionCostThresholdOutput,
) -> dict[str, Any]:
    if type(output) is not CandidateDecisionCostThresholdOutput:
        raise ValueError("payload must be built from CandidateDecisionCostThresholdOutput")
    require_paper_only_flags("CandidateDecisionCostThresholdOutput", output)
    _validate_output_consistency(output)
    reject_unsafe_surface_fields("candidate decision cost threshold output", output)
    payload = json_ready_no_floats(output)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields("candidate decision cost threshold payload", payload)
    return payload


def _validate_config(config: CandidateDecisionCostThresholdConfig) -> None:
    if config.min_net_edge_for_research_more < config.min_net_edge_for_watch:
        raise ValueError("min_net_edge_for_research_more must be at least watch threshold")
    if config.min_net_edge_for_paper_recommend < config.min_net_edge_for_research_more:
        raise ValueError(
            "min_net_edge_for_paper_recommend must be at least research threshold",
        )


def _validate_output_consistency(output: CandidateDecisionCostThresholdOutput) -> None:
    config = _config_from_output(output)
    transaction_cost_drag = _sum_decimals(
        (output.taker_fee_drag, output.spread_cost, output.slippage),
    )
    if output.transaction_cost_drag != transaction_cost_drag:
        raise ValueError("transaction_cost_drag must match transaction costs")
    total_cost_drag = _add_decimal(transaction_cost_drag, output.settlement_cash_lockup_drag)
    if output.total_cost_drag != total_cost_drag:
        raise ValueError("total_cost_drag must match costs")
    total_buffer_drag = _sum_decimals(
        (
            output.transaction_cost_buffer,
            output.settlement_cash_lockup_buffer,
            output.model_uncertainty_buffer,
        ),
    )
    if output.total_buffer_drag != total_buffer_drag:
        raise ValueError("total_buffer_drag must match buffers")
    net_edge_before_buffers = _subtract_decimal(output.gross_edge, total_cost_drag)
    if output.net_edge_before_buffers != net_edge_before_buffers:
        raise ValueError("net_edge_before_buffers must match gross edge and costs")
    net_edge_after_buffers = _subtract_decimal(net_edge_before_buffers, total_buffer_drag)
    if output.net_edge_after_buffers != net_edge_after_buffers:
        raise ValueError("net_edge_after_buffers must match net edge and buffers")
    if output.required_gross_edge_for_watch != _required_gross_edge(
        output.min_net_edge_for_watch,
        total_cost_drag,
        total_buffer_drag,
    ):
        raise ValueError("required_gross_edge_for_watch must match thresholds")
    if output.required_gross_edge_for_research_more != _required_gross_edge(
        output.min_net_edge_for_research_more,
        total_cost_drag,
        total_buffer_drag,
    ):
        raise ValueError("required_gross_edge_for_research_more must match thresholds")
    if output.required_gross_edge_for_paper_recommend != _required_gross_edge(
        output.min_net_edge_for_paper_recommend,
        total_cost_drag,
        total_buffer_drag,
    ):
        raise ValueError("required_gross_edge_for_paper_recommend must match thresholds")
    action = _action_for(net_edge_after_buffers, config)
    if output.action != action:
        raise ValueError("action must match net edge thresholds")
    reason_codes = _reason_codes_for(
        action=action,
        net_edge_after_buffers=net_edge_after_buffers,
        transaction_cost_drag=transaction_cost_drag,
        settlement_cash_lockup_drag=output.settlement_cash_lockup_drag,
        total_buffer_drag=total_buffer_drag,
        source_reason_codes=output.source_reason_codes,
    )
    if output.reason_codes != reason_codes:
        raise ValueError("reason_codes must match threshold outcome")
    if output.hard_safety_flags != HARD_SAFETY_FLAGS:
        raise ValueError("hard_safety_flags must match paper-only scope")


def _config_from_output(
    output: CandidateDecisionCostThresholdOutput,
) -> CandidateDecisionCostThresholdConfig:
    return CandidateDecisionCostThresholdConfig(
        config_version=output.config_version,
        min_net_edge_for_watch=output.min_net_edge_for_watch,
        min_net_edge_for_research_more=output.min_net_edge_for_research_more,
        min_net_edge_for_paper_recommend=output.min_net_edge_for_paper_recommend,
        transaction_cost_buffer=output.transaction_cost_buffer,
        settlement_cash_lockup_buffer=output.settlement_cash_lockup_buffer,
        model_uncertainty_buffer=output.model_uncertainty_buffer,
    )


def _required_gross_edge(
    min_net_edge: Decimal,
    total_cost_drag: Decimal,
    total_buffer_drag: Decimal,
) -> Decimal:
    return _sum_decimals((min_net_edge, total_cost_drag, total_buffer_drag))


def _action_for(
    net_edge_after_buffers: Decimal,
    config: CandidateDecisionCostThresholdConfig,
) -> str:
    if net_edge_after_buffers < config.min_net_edge_for_watch:
        return "reject"
    if net_edge_after_buffers < config.min_net_edge_for_research_more:
        return "watch"
    if net_edge_after_buffers < config.min_net_edge_for_paper_recommend:
        return "research_more"
    return "paper_recommend"


def _reason_codes_for(
    *,
    action: str,
    net_edge_after_buffers: Decimal,
    transaction_cost_drag: Decimal,
    settlement_cash_lockup_drag: Decimal,
    total_buffer_drag: Decimal,
    source_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    codes = [
        f"candidate_decision_cost_thresholds_{action}",
        REASON_CODE,
        _net_edge_reason_code(action),
        *source_reason_codes,
    ]
    if transaction_cost_drag > ZERO:
        codes.append("transaction_cost_drag_applied")
    if settlement_cash_lockup_drag > ZERO:
        codes.append("settlement_cash_lockup_drag_applied")
    if total_buffer_drag > ZERO:
        codes.append("buffer_drag_applied")
    if net_edge_after_buffers < ZERO:
        codes.append("net_edge_negative_after_costs")
    return _normalize_output_reason_codes(tuple(codes))


def _net_edge_reason_code(action: str) -> str:
    if action == "paper_recommend":
        return "net_edge_clears_paper_recommend_threshold"
    if action == "research_more":
        return "net_edge_clears_research_more_threshold"
    if action == "watch":
        return "net_edge_clears_watch_threshold"
    return "net_edge_below_watch_threshold"


def _normalize_source_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code.startswith("candidate_decision_"):
            raise ValueError(f"{field_name} must not contain action reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(reason_codes))


def _normalize_output_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    action_reasons = tuple(
        reason_code
        for reason_code in reason_codes
        if type(reason_code) is str
        and reason_code.startswith("candidate_decision_cost_thresholds_")
    )
    if len(action_reasons) != 1:
        raise ValueError("reason_codes must include one cost threshold action reason")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    other_reasons = tuple(sorted(code for code in reason_codes if code not in action_reasons))
    return action_reasons + other_reasons


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not all(_is_reason_code_character(character) for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")


def _is_reason_code_character(character: str) -> bool:
    return character == "_" or "a" <= character <= "z" or "0" <= character <= "9"


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


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_redacted_ref(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("redacted_"):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _normalize_hard_safety_flags(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("hard_safety_flags must be a list or tuple")
    flags = tuple(value)
    if flags != HARD_SAFETY_FLAGS:
        raise ValueError("hard_safety_flags must match paper-only scope")
    return flags


def _reject_risky_text(value: object) -> None:
    reject_unsafe_surface_fields("candidate decision cost threshold", value)
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
    "DEFAULT_CANDIDATE_DECISION_COST_THRESHOLDS_VERSION",
    "BOUNDARY_STATEMENT",
    "CandidateDecisionCostThresholdConfig",
    "CandidateDecisionCostThresholdInput",
    "CandidateDecisionCostThresholdOutput",
    "evaluate_candidate_decision_cost_thresholds",
    "cost_thresholds_to_candidate_decision_fields",
    "candidate_decision_cost_threshold_payload",
)

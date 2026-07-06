"""Paper-only fee adjusted position sizing gate v2."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
DEFAULT_CONFIG_VERSION = "strategy-fee-adjusted-position-sizing-gate-v2"
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
GATE_STATUSES = ("ready", "watch", "blocked")
RISK_LABELS = ("low_sizing_risk", "medium_sizing_risk", "high_sizing_risk")
STATUS_PRIORITY = {"ready": 0, "watch": 1, "blocked": 2}
RISK_PRIORITY = {
    "low_sizing_risk": 0,
    "medium_sizing_risk": 1,
    "high_sizing_risk": 2,
}
UNSAFE_PUBLIC_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sig" "ning",
    "muta" "tion",
    "b" "uy",
    "se" "ll",
    "tr" "ade",
)
EMPTY_REASON_CODE = "missing_position_sizing_inputs"


@dataclass(frozen=True)
class StrategyFeeAdjustedPositionSizingGateV2Config:
    config_version: str
    portfolio_nav_usdc: Decimal
    max_allocation_fraction_of_nav: Decimal
    edge_allocation_unit: Decimal
    min_cost_adjusted_edge: Decimal
    min_confidence_score: Decimal
    max_liquidity_take_share: Decimal
    max_depth_take_share: Decimal
    max_category_exposure_share: Decimal
    max_settlement_lockup_share: Decimal
    settlement_delay_penalty_rate: Decimal
    settlement_lockup_days_weight: Decimal
    min_position_size_usdc: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "portfolio_nav_usdc",
            _normalize_positive_decimal("portfolio_nav_usdc", self.portfolio_nav_usdc),
        )
        object.__setattr__(
            self,
            "edge_allocation_unit",
            _normalize_positive_decimal("edge_allocation_unit", self.edge_allocation_unit),
        )
        for field_name in (
            "max_allocation_fraction_of_nav",
            "min_cost_adjusted_edge",
            "min_confidence_score",
            "max_liquidity_take_share",
            "max_depth_take_share",
            "max_category_exposure_share",
            "max_settlement_lockup_share",
            "settlement_delay_penalty_rate",
            "settlement_lockup_days_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_position_size_usdc",
            _normalize_nonnegative_decimal(
                "min_position_size_usdc",
                self.min_position_size_usdc,
            ),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyFeeAdjustedPositionSizingGateV2Candidate:
    candidate_id: str
    market_slug: str
    category: str
    question: str
    outcome: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    taker_fee_rate: Decimal
    spread_probability: Decimal
    expected_slippage_probability: Decimal
    available_liquidity_usdc: Decimal
    available_depth_shares: Decimal
    confidence_score: Decimal
    current_category_exposure_usdc: Decimal
    settlement_delay_days: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_slug",
            "category",
            "question",
            "outcome",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "taker_fee_rate",
            "spread_probability",
            "expected_slippage_probability",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "available_liquidity_usdc",
            "available_depth_shares",
            "current_category_exposure_usdc",
            "settlement_delay_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyFeeAdjustedPositionSizingGateV2Row:
    candidate_id: str
    market_slug: str
    category: str
    question: str
    outcome: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    gross_probability_edge: Decimal
    taker_fee_rate: Decimal
    taker_fee_cost_probability: Decimal
    spread_cost_probability: Decimal
    expected_slippage_probability: Decimal
    settlement_delay_days: Decimal
    settlement_delay_penalty_rate: Decimal
    settlement_delay_cost_probability: Decimal
    total_cost_probability: Decimal
    cost_adjusted_edge: Decimal
    confidence_score: Decimal
    confidence_adjusted_edge: Decimal
    edge_budget_usdc: Decimal
    max_nav_allocation_usdc: Decimal
    available_liquidity_usdc: Decimal
    max_liquidity_take_share: Decimal
    liquidity_cap_usdc: Decimal
    available_depth_shares: Decimal
    max_depth_take_share: Decimal
    depth_cap_usdc: Decimal
    current_category_exposure_usdc: Decimal
    category_cap_usdc: Decimal
    category_remaining_capacity_usdc: Decimal
    max_settlement_lockup_share: Decimal
    settlement_lockup_cap_usdc: Decimal
    max_paper_allocation_usdc: Decimal
    gate_status: str
    risk_label: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_slug",
            "category",
            "question",
            "outcome",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "taker_fee_rate",
            "spread_cost_probability",
            "expected_slippage_probability",
            "settlement_delay_penalty_rate",
            "confidence_score",
            "max_liquidity_take_share",
            "max_depth_take_share",
            "max_settlement_lockup_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_probability_edge",
            "cost_adjusted_edge",
            "confidence_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "taker_fee_cost_probability",
            "settlement_delay_days",
            "settlement_delay_cost_probability",
            "total_cost_probability",
            "edge_budget_usdc",
            "max_nav_allocation_usdc",
            "available_liquidity_usdc",
            "liquidity_cap_usdc",
            "available_depth_shares",
            "depth_cap_usdc",
            "current_category_exposure_usdc",
            "category_cap_usdc",
            "category_remaining_capacity_usdc",
            "settlement_lockup_cap_usdc",
            "max_paper_allocation_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_member("risk_label", self.risk_label, RISK_LABELS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyFeeAdjustedPositionSizingGateV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    row_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_max_paper_allocation_usdc: Decimal
    rows: tuple[StrategyFeeAdjustedPositionSizingGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "row_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_max_paper_allocation_usdc",
            _normalize_nonnegative_decimal(
                "total_max_paper_allocation_usdc",
                self.total_max_paper_allocation_usdc,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_strategy_fee_adjusted_position_sizing_gate_v2_report(
    candidates: Iterable[StrategyFeeAdjustedPositionSizingGateV2Candidate],
    *,
    config: StrategyFeeAdjustedPositionSizingGateV2Config,
    generated_at: datetime,
) -> StrategyFeeAdjustedPositionSizingGateV2Report:
    if type(config) is not StrategyFeeAdjustedPositionSizingGateV2Config:
        raise ValueError("config must be a StrategyFeeAdjustedPositionSizingGateV2Config")
    _require_safety_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in source_candidates
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyFeeAdjustedPositionSizingGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(source_candidates)),
        row_count=_count(len(rows)),
        ready_count=_count(_status_count(rows, "ready")),
        watch_count=_count(_status_count(rows, "watch")),
        blocked_count=_count(_status_count(rows, "blocked")),
        total_max_paper_allocation_usdc=_sum_decimal(
            tuple(row.max_paper_allocation_usdc for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def strategy_fee_adjusted_position_sizing_gate_v2_payload(
    report: StrategyFeeAdjustedPositionSizingGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyFeeAdjustedPositionSizingGateV2Report:
        _require_safety_flags(report)
        _verify_report_integrity(report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyFeeAdjustedPositionSizingGateV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_safety_flags(_DictFlags(payload))
    _reject_unsafe_public_payload(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_candidate(
    value: StrategyFeeAdjustedPositionSizingGateV2Candidate,
    *,
    config: StrategyFeeAdjustedPositionSizingGateV2Config,
    generated_at: datetime,
) -> StrategyFeeAdjustedPositionSizingGateV2Row:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    gross_probability_edge = _subtract_decimal(
        value.forecast_probability,
        value.market_probability,
    )
    taker_fee_cost_probability = _multiply_decimal(
        value.market_probability,
        value.taker_fee_rate,
    )
    settlement_delay_cost_probability = _multiply_decimal(
        value.settlement_delay_days,
        config.settlement_delay_penalty_rate,
    )
    total_cost_probability = _sum_decimal(
        (
            taker_fee_cost_probability,
            value.spread_probability,
            value.expected_slippage_probability,
            settlement_delay_cost_probability,
        ),
    )
    cost_adjusted_edge = _subtract_decimal(gross_probability_edge, total_cost_probability)
    confidence_adjusted_edge = _multiply_decimal(
        cost_adjusted_edge,
        value.confidence_score,
    )
    max_nav_allocation_usdc = _multiply_decimal(
        config.portfolio_nav_usdc,
        config.max_allocation_fraction_of_nav,
    )
    edge_budget_usdc = _edge_budget(
        confidence_adjusted_edge=confidence_adjusted_edge,
        config=config,
    )
    liquidity_cap_usdc = _multiply_decimal(
        value.available_liquidity_usdc,
        config.max_liquidity_take_share,
    )
    depth_cap_usdc = _multiply_decimal(
        _multiply_decimal(value.available_depth_shares, value.market_probability),
        config.max_depth_take_share,
    )
    category_cap_usdc = _multiply_decimal(
        config.portfolio_nav_usdc,
        config.max_category_exposure_share,
    )
    category_remaining_capacity_usdc = _max_decimal(
        _subtract_decimal(category_cap_usdc, value.current_category_exposure_usdc),
        _zero(),
    )
    settlement_lockup_cap_usdc = _settlement_lockup_cap(
        settlement_delay_days=value.settlement_delay_days,
        config=config,
    )
    max_paper_allocation_usdc = _allocation_minimum(
        (
            max_nav_allocation_usdc,
            edge_budget_usdc,
            liquidity_cap_usdc,
            depth_cap_usdc,
            category_remaining_capacity_usdc,
            settlement_lockup_cap_usdc,
        ),
        cost_adjusted_edge=cost_adjusted_edge,
    )
    gate_status = _gate_status(
        cost_adjusted_edge=cost_adjusted_edge,
        confidence_score=value.confidence_score,
        max_paper_allocation_usdc=max_paper_allocation_usdc,
        config=config,
    )
    return StrategyFeeAdjustedPositionSizingGateV2Row(
        candidate_id=value.candidate_id,
        market_slug=value.market_slug,
        category=value.category,
        question=value.question,
        outcome=value.outcome,
        observed_at=observed_at,
        forecast_probability=value.forecast_probability,
        market_probability=value.market_probability,
        gross_probability_edge=gross_probability_edge,
        taker_fee_rate=value.taker_fee_rate,
        taker_fee_cost_probability=taker_fee_cost_probability,
        spread_cost_probability=value.spread_probability,
        expected_slippage_probability=value.expected_slippage_probability,
        settlement_delay_days=value.settlement_delay_days,
        settlement_delay_penalty_rate=config.settlement_delay_penalty_rate,
        settlement_delay_cost_probability=settlement_delay_cost_probability,
        total_cost_probability=total_cost_probability,
        cost_adjusted_edge=cost_adjusted_edge,
        confidence_score=value.confidence_score,
        confidence_adjusted_edge=confidence_adjusted_edge,
        edge_budget_usdc=edge_budget_usdc,
        max_nav_allocation_usdc=max_nav_allocation_usdc,
        available_liquidity_usdc=value.available_liquidity_usdc,
        max_liquidity_take_share=config.max_liquidity_take_share,
        liquidity_cap_usdc=liquidity_cap_usdc,
        available_depth_shares=value.available_depth_shares,
        max_depth_take_share=config.max_depth_take_share,
        depth_cap_usdc=depth_cap_usdc,
        current_category_exposure_usdc=value.current_category_exposure_usdc,
        category_cap_usdc=category_cap_usdc,
        category_remaining_capacity_usdc=category_remaining_capacity_usdc,
        max_settlement_lockup_share=config.max_settlement_lockup_share,
        settlement_lockup_cap_usdc=settlement_lockup_cap_usdc,
        max_paper_allocation_usdc=max_paper_allocation_usdc,
        gate_status=gate_status,
        risk_label=_risk_label(gate_status),
        reason_codes=_reason_codes(
            source_reason_codes=value.reason_codes,
            cost_adjusted_edge=cost_adjusted_edge,
            confidence_score=value.confidence_score,
            max_paper_allocation_usdc=max_paper_allocation_usdc,
            cap_values=(
                ("nav_allocation_limited", max_nav_allocation_usdc),
                ("edge_budget_limited", edge_budget_usdc),
                ("liquidity_capacity_limited", liquidity_cap_usdc),
                ("depth_capacity_limited", depth_cap_usdc),
                ("category_capacity_limited", category_remaining_capacity_usdc),
                ("settlement_lockup_limited", settlement_lockup_cap_usdc),
            ),
            config=config,
        ),
    )


def _edge_budget(
    *,
    confidence_adjusted_edge: Decimal,
    config: StrategyFeeAdjustedPositionSizingGateV2Config,
) -> Decimal:
    if confidence_adjusted_edge <= ZERO:
        return _zero()
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            config.portfolio_nav_usdc
            * config.max_allocation_fraction_of_nav
            * (confidence_adjusted_edge / config.edge_allocation_unit),
        )


def _settlement_lockup_cap(
    *,
    settlement_delay_days: Decimal,
    config: StrategyFeeAdjustedPositionSizingGateV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        denominator = ONE + (
            settlement_delay_days * config.settlement_lockup_days_weight
        )
        return _quantize(
            (
                config.portfolio_nav_usdc
                * config.max_settlement_lockup_share
            )
            / denominator,
        )


def _allocation_minimum(
    values: tuple[Decimal, ...],
    *,
    cost_adjusted_edge: Decimal,
) -> Decimal:
    if cost_adjusted_edge <= ZERO:
        return _zero()
    return min(values)


def _gate_status(
    *,
    cost_adjusted_edge: Decimal,
    confidence_score: Decimal,
    max_paper_allocation_usdc: Decimal,
    config: StrategyFeeAdjustedPositionSizingGateV2Config,
) -> str:
    if cost_adjusted_edge <= ZERO:
        return "blocked"
    if max_paper_allocation_usdc <= ZERO:
        return "blocked"
    if cost_adjusted_edge < config.min_cost_adjusted_edge:
        return "watch"
    if confidence_score < config.min_confidence_score:
        return "watch"
    if max_paper_allocation_usdc < config.min_position_size_usdc:
        return "watch"
    return "ready"


def _risk_label(gate_status: str) -> str:
    if gate_status == "blocked":
        return "high_sizing_risk"
    if gate_status == "watch":
        return "medium_sizing_risk"
    return "low_sizing_risk"


def _reason_codes(
    *,
    source_reason_codes: tuple[str, ...],
    cost_adjusted_edge: Decimal,
    confidence_score: Decimal,
    max_paper_allocation_usdc: Decimal,
    cap_values: tuple[tuple[str, Decimal], ...],
    config: StrategyFeeAdjustedPositionSizingGateV2Config,
) -> tuple[str, ...]:
    codes: list[str] = list(source_reason_codes)
    if cost_adjusted_edge <= ZERO:
        codes.append("edge_not_positive_after_costs")
    elif cost_adjusted_edge < config.min_cost_adjusted_edge:
        codes.append("edge_below_minimum")
    else:
        codes.append("cost_adjusted_edge_ready")
    if confidence_score < config.min_confidence_score:
        codes.append("confidence_below_minimum")
    else:
        codes.append("confidence_ready")
    if max_paper_allocation_usdc <= ZERO:
        codes.append("allocation_blocked")
    elif max_paper_allocation_usdc < config.min_position_size_usdc:
        codes.append("allocation_below_minimum")
    else:
        codes.append("allocation_ready")
    for reason_code, cap_value in cap_values:
        if cap_value == max_paper_allocation_usdc:
            codes.append(reason_code)
    return _normalize_reason_codes(tuple(codes))


def _report_reason_codes(
    rows: tuple[StrategyFeeAdjustedPositionSizingGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    return _normalize_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
    )


def _row_sort_key(
    row: StrategyFeeAdjustedPositionSizingGateV2Row,
) -> tuple[int, Decimal, int, Decimal, str, str, str]:
    return (
        STATUS_PRIORITY[row.gate_status],
        -row.max_paper_allocation_usdc,
        RISK_PRIORITY[row.risk_label],
        -row.cost_adjusted_edge,
        row.market_slug,
        row.candidate_id,
        row.outcome,
    )


def _status_count(
    rows: tuple[StrategyFeeAdjustedPositionSizingGateV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.gate_status == status)


def _normalize_candidates(
    candidates: Iterable[StrategyFeeAdjustedPositionSizingGateV2Candidate],
) -> tuple[StrategyFeeAdjustedPositionSizingGateV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError(
            "candidates must be an iterable of StrategyFeeAdjustedPositionSizingGateV2Candidate values",
        )
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError(
            "candidates must be an iterable of StrategyFeeAdjustedPositionSizingGateV2Candidate values",
        ) from exc
    for value in normalized:
        if type(value) is not StrategyFeeAdjustedPositionSizingGateV2Candidate:
            raise ValueError(
                "candidates must contain only StrategyFeeAdjustedPositionSizingGateV2Candidate values",
            )
        _require_safety_flags(value)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyFeeAdjustedPositionSizingGateV2Row, ...],
) -> tuple[StrategyFeeAdjustedPositionSizingGateV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyFeeAdjustedPositionSizingGateV2Row:
            raise ValueError("rows must contain StrategyFeeAdjustedPositionSizingGateV2Row values")
        _require_safety_flags(row)
        _verify_digest(row)
    return rows


def _validate_row_consistency(row: StrategyFeeAdjustedPositionSizingGateV2Row) -> None:
    if row.gross_probability_edge != _subtract_decimal(
        row.forecast_probability,
        row.market_probability,
    ):
        raise ValueError("gross_probability_edge must match probabilities")
    if row.taker_fee_cost_probability != _multiply_decimal(
        row.market_probability,
        row.taker_fee_rate,
    ):
        raise ValueError("taker_fee_cost_probability must match inputs")
    if row.settlement_delay_cost_probability != _multiply_decimal(
        row.settlement_delay_days,
        row.settlement_delay_penalty_rate,
    ):
        raise ValueError("settlement_delay_cost_probability must match inputs")
    if row.total_cost_probability != _sum_decimal(
        (
            row.taker_fee_cost_probability,
            row.spread_cost_probability,
            row.expected_slippage_probability,
            row.settlement_delay_cost_probability,
        ),
    ):
        raise ValueError("total_cost_probability must match costs")
    if row.cost_adjusted_edge != _subtract_decimal(
        row.gross_probability_edge,
        row.total_cost_probability,
    ):
        raise ValueError("cost_adjusted_edge must match costs")
    if row.confidence_adjusted_edge != _multiply_decimal(
        row.cost_adjusted_edge,
        row.confidence_score,
    ):
        raise ValueError("confidence_adjusted_edge must match inputs")
    expected_liquidity_cap = _multiply_decimal(
        row.available_liquidity_usdc,
        row.max_liquidity_take_share,
    )
    if row.liquidity_cap_usdc != expected_liquidity_cap:
        raise ValueError("liquidity_cap_usdc must match inputs")
    expected_depth_cap = _multiply_decimal(
        _multiply_decimal(row.available_depth_shares, row.market_probability),
        row.max_depth_take_share,
    )
    if row.depth_cap_usdc != expected_depth_cap:
        raise ValueError("depth_cap_usdc must match inputs")
    expected_remaining = _max_decimal(
        _subtract_decimal(row.category_cap_usdc, row.current_category_exposure_usdc),
        _zero(),
    )
    if row.category_remaining_capacity_usdc != expected_remaining:
        raise ValueError("category_remaining_capacity_usdc must match inputs")
    expected_allocation = _allocation_minimum(
        (
            row.max_nav_allocation_usdc,
            row.edge_budget_usdc,
            row.liquidity_cap_usdc,
            row.depth_cap_usdc,
            row.category_remaining_capacity_usdc,
            row.settlement_lockup_cap_usdc,
        ),
        cost_adjusted_edge=row.cost_adjusted_edge,
    )
    if row.max_paper_allocation_usdc != expected_allocation:
        raise ValueError("max_paper_allocation_usdc must match caps")
    if row.risk_label != _risk_label(row.gate_status):
        raise ValueError("risk_label must match gate_status")


def _validate_report_consistency(report: StrategyFeeAdjustedPositionSizingGateV2Report) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.ready_count != _count(_status_count(report.rows, "ready")):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.total_max_paper_allocation_usdc != _sum_decimal(
        tuple(row.max_paper_allocation_usdc for row in report.rows),
    ):
        raise ValueError("total_max_paper_allocation_usdc must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    for row in report.rows:
        _verify_digest(row)


def _verify_report_integrity(report: StrategyFeeAdjustedPositionSizingGateV2Report) -> None:
    _validate_report_consistency(report)
    _verify_digest(report)
    for row in report.rows:
        _verify_digest(row)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
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


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _max_decimal(left: Decimal, right: Decimal) -> Decimal:
    return left if left >= right else right


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
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


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_public_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _zero() -> Decimal:
    return ZERO.quantize(QUANTUM)


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _apply_or_verify_digest(
    value: StrategyFeeAdjustedPositionSizingGateV2Row
    | StrategyFeeAdjustedPositionSizingGateV2Report,
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: StrategyFeeAdjustedPositionSizingGateV2Row
    | StrategyFeeAdjustedPositionSizingGateV2Report,
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: StrategyFeeAdjustedPositionSizingGateV2Row
    | StrategyFeeAdjustedPositionSizingGateV2Report,
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    payload = _json_ready(digest_input)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _require_canonical_public_string("public_payload_key", key)
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError("public payload contains unsafe public content")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


__all__ = (
    "StrategyFeeAdjustedPositionSizingGateV2Candidate",
    "StrategyFeeAdjustedPositionSizingGateV2Config",
    "StrategyFeeAdjustedPositionSizingGateV2Report",
    "StrategyFeeAdjustedPositionSizingGateV2Row",
    "build_strategy_fee_adjusted_position_sizing_gate_v2_report",
    "strategy_fee_adjusted_position_sizing_gate_v2_payload",
)

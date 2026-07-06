"""Pure expected-value ranker for strategy research candidates.

Polymarket markets are probability events. This ranker evaluates candidate
markets from forecast probability versus market probability, then applies
explicit cost, resolution-risk, and liquidity-capacity adjustments before
assigning research-only ranks.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

RANK_STATUS_RANKED = "ranked"
RANK_STATUS_WATCH = "watch"
RANK_STATUS_BLOCKED = "blocked"
RANK_STATUSES = frozenset(
    (RANK_STATUS_RANKED, RANK_STATUS_WATCH, RANK_STATUS_BLOCKED),
)

REASON_EVENT_PAYOFF = "probability_event_payoff_model"
REASON_EDGE_RANKED = "ev_cost_adjusted_edge_ranked"
REASON_EDGE_WATCH = "ev_cost_adjusted_edge_watch"
REASON_RESOLUTION_ACCEPTED = "ev_resolution_risk_accepted"
REASON_RESOLUTION_BLOCKED = "ev_resolution_risk_blocked"
REASON_LIQUIDITY_ACCEPTED = "ev_liquidity_capacity_accepted"
REASON_LIQUIDITY_BLOCKED = "ev_liquidity_capacity_blocked"


@dataclass(frozen=True)
class StrategyExpectedValueRankerConfig:
    minimum_cost_adjusted_edge: Decimal = Decimal("0.020000")
    maximum_resolution_risk: Decimal = Decimal("0.300000")
    minimum_liquidity_capacity: Decimal = Decimal("10.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "minimum_cost_adjusted_edge",
            _require_quantized_nonnegative_decimal(
                "minimum_cost_adjusted_edge",
                self.minimum_cost_adjusted_edge,
            ),
        )
        object.__setattr__(
            self,
            "maximum_resolution_risk",
            _require_probability(
                "maximum_resolution_risk",
                self.maximum_resolution_risk,
            ),
        )
        object.__setattr__(
            self,
            "minimum_liquidity_capacity",
            _require_quantized_nonnegative_decimal(
                "minimum_liquidity_capacity",
                self.minimum_liquidity_capacity,
            ),
        )
        _require_paper_report_readonly("config", self)


@dataclass(frozen=True)
class StrategyExpectedValueRankerCandidate:
    candidate_id: str
    event_payoff: Decimal
    market_probability: Decimal
    forecast_probability: Decimal
    fee_drag: Decimal = ZERO
    slippage_buffer: Decimal = ZERO
    resolution_risk: Decimal = ZERO
    liquidity_capacity: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "event_payoff",
            _require_positive_decimal("event_payoff", self.event_payoff),
        )
        for field_name in ("market_probability", "forecast_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("fee_drag", "slippage_buffer", "liquidity_capacity"):
            object.__setattr__(
                self,
                field_name,
                _require_quantized_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "resolution_risk",
            _require_probability("resolution_risk", self.resolution_risk),
        )
        _require_paper_report_readonly("candidate", self)


@dataclass(frozen=True)
class StrategyExpectedValueRankerRow:
    rank: Decimal
    candidate_id: str
    event_payoff: Decimal
    market_probability: Decimal
    forecast_probability: Decimal
    fee_drag: Decimal
    slippage_buffer: Decimal
    resolution_risk: Decimal
    liquidity_capacity: Decimal
    forecast_expected_payoff: Decimal
    market_implied_cost: Decimal
    probability_edge: Decimal
    cost_adjustment: Decimal
    cost_adjusted_edge: Decimal
    resolution_risk_adjusted_edge: Decimal
    capacity_adjusted_expected_value: Decimal
    rank_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _require_positive_decimal("rank", self.rank),
        )
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "event_payoff",
            _require_positive_decimal("event_payoff", self.event_payoff),
        )
        for field_name in ("market_probability", "forecast_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_drag",
            "slippage_buffer",
            "liquidity_capacity",
            "forecast_expected_payoff",
            "market_implied_cost",
            "cost_adjustment",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_quantized_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "resolution_risk",
            _require_probability("resolution_risk", self.resolution_risk),
        )
        for field_name in (
            "probability_edge",
            "cost_adjusted_edge",
            "resolution_risk_adjusted_edge",
            "capacity_adjusted_expected_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_quantized_decimal(field_name, getattr(self, field_name)),
            )
        _require_rank_status("rank_status", self.rank_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        if self.rank_status != _rank_status_for_reason_codes(self.reason_codes):
            raise ValueError("rank_status must match reason_codes")
        _require_paper_report_readonly("row", self)


@dataclass(frozen=True)
class StrategyExpectedValueRankerReport:
    candidate_count: Decimal
    ranked_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    rows: tuple[StrategyExpectedValueRankerRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_count",
            "ranked_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_quantized_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_paper_report_readonly("report", self)


def rank_strategy_expected_value_candidates(
    candidates: Iterable[StrategyExpectedValueRankerCandidate],
    *,
    config: StrategyExpectedValueRankerConfig,
) -> StrategyExpectedValueRankerReport:
    """Rank strategy candidates by cost-, risk-, and capacity-adjusted EV."""

    if type(config) is not StrategyExpectedValueRankerConfig:
        raise ValueError("config must be a StrategyExpectedValueRankerConfig")
    _require_paper_report_readonly("config", config)

    input_rows = _normalize_candidates(candidates)
    ranked_rows = tuple(
        sorted(
            (_unranked_row(candidate, config=config) for candidate in input_rows),
            key=_row_sort_key,
        ),
    )
    rows = tuple(
        _row_with_rank(row, rank=_count(index))
        for index, row in enumerate(ranked_rows, start=1)
    )

    return StrategyExpectedValueRankerReport(
        candidate_count=_count(len(rows)),
        ranked_count=_status_count(rows, RANK_STATUS_RANKED),
        watch_count=_status_count(rows, RANK_STATUS_WATCH),
        blocked_count=_status_count(rows, RANK_STATUS_BLOCKED),
        rows=rows,
    )


def _unranked_row(
    candidate: StrategyExpectedValueRankerCandidate,
    *,
    config: StrategyExpectedValueRankerConfig,
) -> StrategyExpectedValueRankerRow:
    forecast_expected_payoff = _quantize_decimal(
        candidate.forecast_probability * candidate.event_payoff,
    )
    market_implied_cost = _quantize_decimal(
        candidate.market_probability * candidate.event_payoff,
    )
    probability_edge = _quantize_decimal(
        candidate.forecast_probability - candidate.market_probability,
    )
    cost_adjustment = _quantize_decimal(candidate.fee_drag + candidate.slippage_buffer)
    cost_adjusted_edge = _quantize_decimal(
        forecast_expected_payoff - market_implied_cost - cost_adjustment,
    )
    resolution_risk_adjusted_edge = _quantize_decimal(
        cost_adjusted_edge * (ONE - candidate.resolution_risk),
    )
    capacity_adjusted_expected_value = _quantize_decimal(
        resolution_risk_adjusted_edge * candidate.liquidity_capacity,
    )
    reason_codes = _reason_codes(
        cost_adjusted_edge=cost_adjusted_edge,
        resolution_risk=candidate.resolution_risk,
        liquidity_capacity=candidate.liquidity_capacity,
        config=config,
    )
    return StrategyExpectedValueRankerRow(
        rank=ONE,
        candidate_id=candidate.candidate_id,
        event_payoff=candidate.event_payoff,
        market_probability=candidate.market_probability,
        forecast_probability=candidate.forecast_probability,
        fee_drag=candidate.fee_drag,
        slippage_buffer=candidate.slippage_buffer,
        resolution_risk=candidate.resolution_risk,
        liquidity_capacity=candidate.liquidity_capacity,
        forecast_expected_payoff=forecast_expected_payoff,
        market_implied_cost=market_implied_cost,
        probability_edge=probability_edge,
        cost_adjustment=cost_adjustment,
        cost_adjusted_edge=cost_adjusted_edge,
        resolution_risk_adjusted_edge=resolution_risk_adjusted_edge,
        capacity_adjusted_expected_value=capacity_adjusted_expected_value,
        rank_status=_rank_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_with_rank(
    row: StrategyExpectedValueRankerRow,
    *,
    rank: Decimal,
) -> StrategyExpectedValueRankerRow:
    return StrategyExpectedValueRankerRow(
        rank=rank,
        candidate_id=row.candidate_id,
        event_payoff=row.event_payoff,
        market_probability=row.market_probability,
        forecast_probability=row.forecast_probability,
        fee_drag=row.fee_drag,
        slippage_buffer=row.slippage_buffer,
        resolution_risk=row.resolution_risk,
        liquidity_capacity=row.liquidity_capacity,
        forecast_expected_payoff=row.forecast_expected_payoff,
        market_implied_cost=row.market_implied_cost,
        probability_edge=row.probability_edge,
        cost_adjustment=row.cost_adjustment,
        cost_adjusted_edge=row.cost_adjusted_edge,
        resolution_risk_adjusted_edge=row.resolution_risk_adjusted_edge,
        capacity_adjusted_expected_value=row.capacity_adjusted_expected_value,
        rank_status=row.rank_status,
        reason_codes=row.reason_codes,
    )


def _reason_codes(
    *,
    cost_adjusted_edge: Decimal,
    resolution_risk: Decimal,
    liquidity_capacity: Decimal,
    config: StrategyExpectedValueRankerConfig,
) -> tuple[str, ...]:
    edge_reason = (
        REASON_EDGE_RANKED
        if cost_adjusted_edge >= config.minimum_cost_adjusted_edge
        else REASON_EDGE_WATCH
    )
    resolution_reason = (
        REASON_RESOLUTION_ACCEPTED
        if resolution_risk <= config.maximum_resolution_risk
        else REASON_RESOLUTION_BLOCKED
    )
    liquidity_reason = (
        REASON_LIQUIDITY_ACCEPTED
        if liquidity_capacity >= config.minimum_liquidity_capacity
        else REASON_LIQUIDITY_BLOCKED
    )
    return (REASON_EVENT_PAYOFF, edge_reason, resolution_reason, liquidity_reason)


def _rank_status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        REASON_RESOLUTION_BLOCKED in reason_codes
        or REASON_LIQUIDITY_BLOCKED in reason_codes
    ):
        return RANK_STATUS_BLOCKED
    if REASON_EDGE_RANKED in reason_codes:
        return RANK_STATUS_RANKED
    return RANK_STATUS_WATCH


def _row_sort_key(row: StrategyExpectedValueRankerRow) -> tuple[object, ...]:
    return (
        _status_sort_value(row.rank_status),
        -row.capacity_adjusted_expected_value,
        -row.cost_adjusted_edge,
        -row.probability_edge,
        row.resolution_risk,
        -row.liquidity_capacity,
        row.candidate_id,
    )


def _status_sort_value(rank_status: str) -> int:
    if rank_status == RANK_STATUS_RANKED:
        return 0
    if rank_status == RANK_STATUS_WATCH:
        return 1
    return 2


def _validate_row_consistency(row: StrategyExpectedValueRankerRow) -> None:
    if row.forecast_expected_payoff != _quantize_decimal(
        row.forecast_probability * row.event_payoff,
    ):
        raise ValueError("forecast_expected_payoff must match forecast probability")
    if row.market_implied_cost != _quantize_decimal(
        row.market_probability * row.event_payoff,
    ):
        raise ValueError("market_implied_cost must match market probability")
    if row.probability_edge != _quantize_decimal(
        row.forecast_probability - row.market_probability,
    ):
        raise ValueError("probability_edge must match forecast and market probabilities")
    if row.cost_adjustment != _quantize_decimal(row.fee_drag + row.slippage_buffer):
        raise ValueError("cost_adjustment must match fee and slippage buffers")
    if row.cost_adjusted_edge != _quantize_decimal(
        row.forecast_expected_payoff - row.market_implied_cost - row.cost_adjustment,
    ):
        raise ValueError("cost_adjusted_edge must match payoff less costs")
    if row.resolution_risk_adjusted_edge != _quantize_decimal(
        row.cost_adjusted_edge * (ONE - row.resolution_risk),
    ):
        raise ValueError("resolution_risk_adjusted_edge must match resolution risk")
    if row.capacity_adjusted_expected_value != _quantize_decimal(
        row.resolution_risk_adjusted_edge * row.liquidity_capacity,
    ):
        raise ValueError("capacity_adjusted_expected_value must match liquidity capacity")


def _validate_report_consistency(report: StrategyExpectedValueRankerReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.ranked_count != _status_count(report.rows, RANK_STATUS_RANKED):
        raise ValueError("ranked_count must match rows")
    if report.watch_count != _status_count(report.rows, RANK_STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, RANK_STATUS_BLOCKED):
        raise ValueError("blocked_count must match rows")
    expected_ranks = tuple(_count(index) for index in range(1, len(report.rows) + 1))
    if tuple(row.rank for row in report.rows) != expected_ranks:
        raise ValueError("row ranks must be sequential")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted by expected value rank")


def _normalize_candidates(
    value: Iterable[StrategyExpectedValueRankerCandidate],
) -> tuple[StrategyExpectedValueRankerCandidate, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    candidate_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyExpectedValueRankerCandidate:
            raise ValueError("candidates must contain exact candidate rows")
        _require_paper_report_readonly("candidate", row)
        if row.candidate_id in candidate_ids:
            raise ValueError("candidate_id values must be unique")
        candidate_ids.add(row.candidate_id)
    return rows


def _normalize_rows(
    value: Iterable[StrategyExpectedValueRankerRow],
) -> tuple[StrategyExpectedValueRankerRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    candidate_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyExpectedValueRankerRow:
            raise ValueError("rows must contain exact rank rows")
        _require_paper_report_readonly("row", row)
        if row.candidate_id in candidate_ids:
            raise ValueError("candidate_id values must be unique")
        candidate_ids.add(row.candidate_id)
    return rows


def _status_count(
    rows: tuple[StrategyExpectedValueRankerRow, ...],
    rank_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.rank_status == rank_status))


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_rank_status(field_name: str, value: str) -> None:
    if value not in RANK_STATUSES:
        raise ValueError(f"{field_name} must be a valid rank status")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _require_probability(field_name: str, value: Decimal) -> Decimal:
    value = _require_quantized_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_quantized_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_quantized_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_quantized_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_quantized_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_paper_report_readonly(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")

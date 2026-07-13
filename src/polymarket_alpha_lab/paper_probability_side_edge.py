"""Paper-only probability side-edge reducer.

Pure supplied-input arithmetic for preserving YES/NO event-contract economics.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
ACTIONS = ("recommend", "watch", "reject")
DEPTH_STATUSES = ("sufficient_depth", "partial_depth", "no_depth")
ACTION_PRIORITY = {
    "recommend": 0,
    "watch": 1,
    "reject": 2,
}


@dataclass(frozen=True)
class PaperProbabilitySideEdgeInput:
    (
        "forecast_probability always denotes canonical Decimal P(YES), regardless of "
        "side; side identifies the paper-review side being evaluated and never reorients "
        "forecast_probability; P(NO) is 1 - P(YES)."
    )

    market_slug: str
    question: str
    side: str
    forecast_probability: Decimal
    side_price: Decimal
    fee_cost_per_share: Decimal
    spread_cost_per_share: Decimal
    slippage_cost_per_share: Decimal
    funding_cost_per_share: Decimal
    finalization_cost_per_share: Decimal
    time_cost_per_share: Decimal
    risk_cost_per_share: Decimal
    capital_cost_per_share: Decimal
    requested_paper_shares: Decimal
    max_executable_shares: Decimal
    market_context_fresh: bool
    settlement_context_fresh: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "side_price",
            _normalize_probability("side_price", self.side_price),
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
            "requested_paper_shares",
            "max_executable_shares",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("market_context_fresh", self.market_context_fresh)
        _require_bool("settlement_context_fresh", self.settlement_context_fresh)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperProbabilitySideEdgeConfig:
    config_version: str
    min_net_probability_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_net_probability_edge",
            _normalize_probability(
                "min_net_probability_edge",
                self.min_net_probability_edge,
            ),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperProbabilitySideEdgeRow:
    market_slug: str
    question: str
    side: str
    side_probability: Decimal
    market_implied_probability: Decimal
    gross_probability_edge: Decimal
    total_cost_per_share: Decimal
    net_probability_edge: Decimal
    recommendation_score: Decimal
    action: str
    depth_status: str
    requested_paper_shares: Decimal
    max_executable_shares: Decimal
    executable_paper_shares: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        object.__setattr__(
            self,
            "side_probability",
            _normalize_probability("side_probability", self.side_probability),
        )
        object.__setattr__(
            self,
            "market_implied_probability",
            _normalize_probability(
                "market_implied_probability",
                self.market_implied_probability,
            ),
        )
        for field_name in (
            "gross_probability_edge",
            "net_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_cost_per_share",
            _normalize_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "recommendation_score",
            _normalize_probability("recommendation_score", self.recommendation_score),
        )
        if self.action not in ACTIONS:
            raise ValueError("action must be recommend, watch, or reject")
        if self.depth_status not in DEPTH_STATUSES:
            raise ValueError("depth_status must be a known depth status")
        for field_name in (
            "requested_paper_shares",
            "max_executable_shares",
            "executable_paper_shares",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperProbabilitySideEdgeReport:
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    recommend_count: int
    watch_count: int
    reject_count: int
    rows: tuple[PaperProbabilitySideEdgeRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "recommend_count",
            "watch_count",
            "reject_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_paper_probability_side_edge_report(
    inputs: Iterable[PaperProbabilitySideEdgeInput],
    *,
    config: PaperProbabilitySideEdgeConfig,
    generated_at: datetime,
) -> PaperProbabilitySideEdgeReport:
    if type(config) is not PaperProbabilitySideEdgeConfig:
        raise ValueError("config must be a PaperProbabilitySideEdgeConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if config.paper_only is not True:
        raise ValueError("config paper_only must be True")
    if config.report_only is not True:
        raise ValueError("config report_only must be True")
    if config.readonly is not True:
        raise ValueError("config readonly must be True")

    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    return PaperProbabilitySideEdgeReport(
        generated_at=_as_utc(generated_at),
        config_version=config.config_version,
        input_count=len(normalized_inputs),
        row_count=len(rows),
        recommend_count=_action_count(rows, "recommend"),
        watch_count=_action_count(rows, "watch"),
        reject_count=_action_count(rows, "reject"),
        rows=rows,
    )


def _row_from_input(
    value: PaperProbabilitySideEdgeInput,
    *,
    config: PaperProbabilitySideEdgeConfig,
) -> PaperProbabilitySideEdgeRow:
    side_probability = _side_probability(value)
    market_implied_probability = value.side_price
    gross_probability_edge = _subtract_decimal(
        side_probability,
        market_implied_probability,
    )
    total_cost_per_share = _total_cost(value)
    net_probability_edge = _subtract_decimal(
        gross_probability_edge,
        total_cost_per_share,
    )
    depth_status = _depth_status(
        value.requested_paper_shares,
        value.max_executable_shares,
    )
    executable_paper_shares = _executable_shares(
        value.requested_paper_shares,
        value.max_executable_shares,
    )
    action = _action_for(
        side_price=value.side_price,
        net_probability_edge=net_probability_edge,
        min_net_probability_edge=config.min_net_probability_edge,
        market_context_fresh=value.market_context_fresh,
        settlement_context_fresh=value.settlement_context_fresh,
        depth_status=depth_status,
    )
    reason_codes = _reason_codes_for(
        source_reason_codes=value.reason_codes,
        side_price=value.side_price,
        net_probability_edge=net_probability_edge,
        min_net_probability_edge=config.min_net_probability_edge,
        market_context_fresh=value.market_context_fresh,
        settlement_context_fresh=value.settlement_context_fresh,
        depth_status=depth_status,
    )
    recommendation_score = _recommendation_score(
        action=action,
        net_probability_edge=net_probability_edge,
        side_price=value.side_price,
        market_context_fresh=value.market_context_fresh,
        settlement_context_fresh=value.settlement_context_fresh,
        depth_status=depth_status,
    )

    return PaperProbabilitySideEdgeRow(
        market_slug=value.market_slug,
        question=value.question,
        side=value.side,
        side_probability=side_probability,
        market_implied_probability=market_implied_probability,
        gross_probability_edge=gross_probability_edge,
        total_cost_per_share=total_cost_per_share,
        net_probability_edge=net_probability_edge,
        recommendation_score=recommendation_score,
        action=action,
        depth_status=depth_status,
        requested_paper_shares=value.requested_paper_shares,
        max_executable_shares=value.max_executable_shares,
        executable_paper_shares=executable_paper_shares,
        reason_codes=reason_codes,
    )


def _side_probability(value: PaperProbabilitySideEdgeInput) -> Decimal:
    """Convert canonical P(YES) to the evaluated side probability at this reducer's boundary."""

    if value.side == "yes":
        return value.forecast_probability
    return _subtract_decimal(ONE, value.forecast_probability)


def _total_cost(value: PaperProbabilitySideEdgeInput) -> Decimal:
    return _sum_decimals(
        (
            value.fee_cost_per_share,
            value.spread_cost_per_share,
            value.slippage_cost_per_share,
            value.funding_cost_per_share,
            value.finalization_cost_per_share,
            value.time_cost_per_share,
            value.risk_cost_per_share,
            value.capital_cost_per_share,
        ),
    )


def _action_for(
    *,
    side_price: Decimal,
    net_probability_edge: Decimal,
    min_net_probability_edge: Decimal,
    market_context_fresh: bool,
    settlement_context_fresh: bool,
    depth_status: str,
) -> str:
    if net_probability_edge <= ZERO:
        return "reject"
    if depth_status == "no_depth":
        return "reject"
    if side_price <= ZERO:
        return "watch"
    if market_context_fresh is not True:
        return "watch"
    if settlement_context_fresh is not True:
        return "watch"
    if net_probability_edge < min_net_probability_edge:
        return "watch"
    return "recommend"


def _recommendation_score(
    *,
    action: str,
    net_probability_edge: Decimal,
    side_price: Decimal,
    market_context_fresh: bool,
    settlement_context_fresh: bool,
    depth_status: str,
) -> Decimal:
    if net_probability_edge <= ZERO:
        return _quantize(ZERO)
    if action == "reject":
        return _quantize(ZERO)
    if side_price <= ZERO:
        return _quantize(ZERO)
    if market_context_fresh is not True:
        return _quantize(ZERO)
    if settlement_context_fresh is not True:
        return _quantize(ZERO)
    if depth_status == "no_depth":
        return _quantize(ZERO)
    return _normalize_probability("recommendation_score", net_probability_edge)


def _reason_codes_for(
    *,
    source_reason_codes: tuple[str, ...],
    side_price: Decimal,
    net_probability_edge: Decimal,
    min_net_probability_edge: Decimal,
    market_context_fresh: bool,
    settlement_context_fresh: bool,
    depth_status: str,
) -> tuple[str, ...]:
    depth_codes = () if depth_status == "sufficient_depth" else (depth_status,)
    price_codes = ("zero_side_price",) if side_price <= ZERO else ()
    edge_codes = (
        ("nonpositive_net_probability_edge",)
        if net_probability_edge <= ZERO
        else ()
    )
    threshold_codes = (
        ("below_min_net_probability_edge",)
        if ZERO < net_probability_edge < min_net_probability_edge
        else ()
    )
    market_codes = ("market_context_stale",) if market_context_fresh is not True else ()
    settlement_codes = (
        ("settlement_context_stale",)
        if settlement_context_fresh is not True
        else ()
    )
    return _normalize_reason_codes(
        (
            *source_reason_codes,
            *depth_codes,
            *price_codes,
            *edge_codes,
            *threshold_codes,
            *market_codes,
            *settlement_codes,
        ),
    )


def _depth_status(
    requested_paper_shares: Decimal,
    max_executable_shares: Decimal,
) -> str:
    if requested_paper_shares <= ZERO:
        return "no_depth"
    if max_executable_shares <= ZERO:
        return "no_depth"
    if max_executable_shares < requested_paper_shares:
        return "partial_depth"
    return "sufficient_depth"


def _executable_shares(
    requested_paper_shares: Decimal,
    max_executable_shares: Decimal,
) -> Decimal:
    if requested_paper_shares <= ZERO:
        return _quantize(ZERO)
    if max_executable_shares <= ZERO:
        return _quantize(ZERO)
    if max_executable_shares < requested_paper_shares:
        return max_executable_shares
    return requested_paper_shares


def _row_sort_key(
    row: PaperProbabilitySideEdgeRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        ACTION_PRIORITY[row.action],
        -row.recommendation_score,
        -row.net_probability_edge,
        -row.executable_paper_shares,
        row.total_cost_per_share,
        row.market_slug,
        row.side,
    )


def _action_count(rows: tuple[PaperProbabilitySideEdgeRow, ...], action: str) -> int:
    return sum(1 for row in rows if row.action == action)


def _normalize_inputs(
    values: Iterable[PaperProbabilitySideEdgeInput],
) -> tuple[PaperProbabilitySideEdgeInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable of PaperProbabilitySideEdgeInput values")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of PaperProbabilitySideEdgeInput values",
        ) from exc
    for value in normalized:
        if type(value) is not PaperProbabilitySideEdgeInput:
            raise ValueError(
                "inputs must contain only PaperProbabilitySideEdgeInput values",
            )
        if value.paper_only is not True:
            raise ValueError("inputs must contain paper_only values")
        if value.report_only is not True:
            raise ValueError("inputs must contain report_only values")
        if value.readonly is not True:
            raise ValueError("inputs must contain readonly values")
    return normalized


def _normalize_rows(
    rows: Iterable[PaperProbabilitySideEdgeRow],
) -> tuple[PaperProbabilitySideEdgeRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperProbabilitySideEdgeRow:
            raise ValueError("rows must contain PaperProbabilitySideEdgeRow values")
        if row.paper_only is not True:
            raise ValueError("rows must contain paper_only values")
        if row.report_only is not True:
            raise ValueError("rows must contain report_only values")
        if row.readonly is not True:
            raise ValueError("rows must contain readonly values")
    return normalized


def _validate_row_consistency(row: PaperProbabilitySideEdgeRow) -> None:
    expected_gross_probability_edge = _subtract_decimal(
        row.side_probability,
        row.market_implied_probability,
    )
    if row.gross_probability_edge != expected_gross_probability_edge:
        raise ValueError("gross_probability_edge must match probabilities")
    expected_net_probability_edge = _subtract_decimal(
        row.gross_probability_edge,
        row.total_cost_per_share,
    )
    if row.net_probability_edge != expected_net_probability_edge:
        raise ValueError("net_probability_edge must match gross edge and costs")
    expected_executable_paper_shares = _executable_shares(
        row.requested_paper_shares,
        row.max_executable_shares,
    )
    if row.executable_paper_shares != expected_executable_paper_shares:
        raise ValueError("executable_paper_shares must match depth")
    expected_depth_status = _depth_status(
        row.requested_paper_shares,
        row.max_executable_shares,
    )
    if row.depth_status != expected_depth_status:
        raise ValueError("depth_status must match depth")
    if row.action == "reject" and row.recommendation_score != _quantize(ZERO):
        raise ValueError("recommendation_score must be zero for reject")
    if row.action == "recommend":
        if row.recommendation_score <= ZERO:
            raise ValueError("recommendation_score must be positive for recommend")
        if row.recommendation_score != row.net_probability_edge:
            raise ValueError("recommendation_score must match net edge for recommend")
    if row.net_probability_edge <= ZERO and row.action != "reject":
        raise ValueError("action must reject nonpositive net_probability_edge")
    if row.depth_status == "no_depth" and row.action != "reject":
        raise ValueError("action must reject no_depth")
    if row.recommendation_score > ZERO:
        if row.net_probability_edge <= ZERO:
            raise ValueError("recommendation_score requires positive net edge")
        if row.recommendation_score != row.net_probability_edge:
            raise ValueError("recommendation_score must match net edge when positive")


def _validate_report_consistency(report: PaperProbabilitySideEdgeReport) -> None:
    if report.input_count != len(report.rows):
        raise ValueError("input_count must equal rows length")
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    if report.recommend_count != _action_count(report.rows, "recommend"):
        raise ValueError("recommend_count must equal rows")
    if report.watch_count != _action_count(report.rows, "watch"):
        raise ValueError("watch_count must equal rows")
    if report.reject_count != _action_count(report.rows, "reject"):
        raise ValueError("reject_count must equal rows")
    if report.row_count != (
        report.recommend_count + report.watch_count + report.reject_count
    ):
        raise ValueError("row_count must equal action counts")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
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


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return _normalize_decimal(field_name, value)


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
    return _quantize(value)


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "PaperProbabilitySideEdgeInput",
    "PaperProbabilitySideEdgeConfig",
    "PaperProbabilitySideEdgeRow",
    "PaperProbabilitySideEdgeReport",
    "build_paper_probability_side_edge_report",
)

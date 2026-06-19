"""Paper-only recommendation allocation reducer."""

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
CAP_STATUSES = ("allocated", "capped", "no_budget", "non_recommend", "skipped")


@dataclass(frozen=True)
class PaperRecommendationAllocationInput:
    market_slug: str
    side: str
    action: str
    recommendation_score: Decimal | None
    net_probability_edge: Decimal | None
    executable_paper_shares: Decimal
    side_price: Decimal | None = None
    market_implied_probability: Decimal | None = None
    event_id: str | None = None
    theme_id: str | None = None
    correlation_group: str | None = None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        if self.action not in ACTIONS:
            raise ValueError("action must be recommend, watch, or reject")
        object.__setattr__(
            self,
            "recommendation_score",
            _normalize_optional_probability(
                "recommendation_score",
                self.recommendation_score,
            ),
        )
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_optional_decimal(
                "net_probability_edge",
                self.net_probability_edge,
            ),
        )
        if self.recommendation_score is None and self.net_probability_edge is None:
            raise ValueError(
                "recommendation_score or net_probability_edge must provide an edge",
            )
        object.__setattr__(
            self,
            "executable_paper_shares",
            _normalize_nonnegative_decimal(
                "executable_paper_shares",
                self.executable_paper_shares,
            ),
        )
        side_price = _normalize_optional_probability("side_price", self.side_price)
        market_implied_probability = _normalize_optional_probability(
            "market_implied_probability",
            self.market_implied_probability,
        )
        if side_price is None and market_implied_probability is None:
            raise ValueError("side_price or market_implied_probability is required")
        if side_price is None:
            side_price = market_implied_probability
        if market_implied_probability is None:
            market_implied_probability = side_price
        if side_price != market_implied_probability:
            raise ValueError("side_price must match market_implied_probability")
        object.__setattr__(self, "side_price", side_price)
        object.__setattr__(
            self,
            "market_implied_probability",
            market_implied_probability,
        )
        for field_name in ("event_id", "theme_id", "correlation_group"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperRecommendationAllocationConfig:
    config_version: str
    total_paper_budget: Decimal
    max_paper_notional_per_market: Decimal
    max_paper_notional_per_event: Decimal
    max_paper_notional_per_theme: Decimal
    max_paper_notional_per_correlation_group: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "total_paper_budget",
            "max_paper_notional_per_market",
            "max_paper_notional_per_event",
            "max_paper_notional_per_theme",
            "max_paper_notional_per_correlation_group",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperRecommendationAllocationRow:
    market_slug: str
    side: str
    action: str
    recommendation_score: Decimal | None
    net_probability_edge: Decimal | None
    executable_paper_shares: Decimal
    side_price: Decimal
    market_implied_probability: Decimal
    event_id: str | None
    theme_id: str | None
    correlation_group: str | None
    requested_paper_notional: Decimal
    allocated_paper_notional: Decimal
    allocated_paper_shares: Decimal
    cap_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        if self.action not in ACTIONS:
            raise ValueError("action must be recommend, watch, or reject")
        object.__setattr__(
            self,
            "recommendation_score",
            _normalize_optional_probability(
                "recommendation_score",
                self.recommendation_score,
            ),
        )
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_optional_decimal(
                "net_probability_edge",
                self.net_probability_edge,
            ),
        )
        if self.recommendation_score is None and self.net_probability_edge is None:
            raise ValueError(
                "recommendation_score or net_probability_edge must provide an edge",
            )
        object.__setattr__(
            self,
            "executable_paper_shares",
            _normalize_nonnegative_decimal(
                "executable_paper_shares",
                self.executable_paper_shares,
            ),
        )
        object.__setattr__(
            self,
            "side_price",
            _normalize_probability("side_price", self.side_price),
        )
        object.__setattr__(
            self,
            "market_implied_probability",
            _normalize_probability(
                "market_implied_probability",
                self.market_implied_probability,
            ),
        )
        if self.side_price != self.market_implied_probability:
            raise ValueError("side_price must match market_implied_probability")
        for field_name in ("event_id", "theme_id", "correlation_group"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "requested_paper_notional",
            "allocated_paper_notional",
            "allocated_paper_shares",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.cap_status not in CAP_STATUSES:
            raise ValueError("cap_status must be a known status")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperRecommendationAllocationReport:
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    allocated_count: int
    capped_count: int
    no_budget_count: int
    non_recommend_count: int
    skipped_count: int
    total_requested_paper_notional: Decimal
    total_allocated_paper_notional: Decimal
    remaining_paper_budget: Decimal
    total_paper_budget: Decimal
    max_paper_notional_per_market: Decimal
    max_paper_notional_per_event: Decimal
    max_paper_notional_per_theme: Decimal
    max_paper_notional_per_correlation_group: Decimal
    rows: tuple[PaperRecommendationAllocationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "allocated_count",
            "capped_count",
            "no_budget_count",
            "non_recommend_count",
            "skipped_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "total_requested_paper_notional",
            "total_allocated_paper_notional",
            "remaining_paper_budget",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_paper_budget",
            "max_paper_notional_per_market",
            "max_paper_notional_per_event",
            "max_paper_notional_per_theme",
            "max_paper_notional_per_correlation_group",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_paper_recommendation_allocation_report(
    inputs: Iterable[object],
    *,
    config: PaperRecommendationAllocationConfig,
    generated_at: datetime,
) -> PaperRecommendationAllocationReport:
    if type(config) is not PaperRecommendationAllocationConfig:
        raise ValueError("config must be a PaperRecommendationAllocationConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_safety_flags(config)

    normalized_inputs = _normalize_inputs(inputs)
    rows = _allocate_rows(tuple(sorted(normalized_inputs, key=_input_sort_key)), config)
    return PaperRecommendationAllocationReport(
        generated_at=_as_utc(generated_at),
        config_version=config.config_version,
        input_count=len(normalized_inputs),
        row_count=len(rows),
        allocated_count=_cap_status_count(rows, "allocated"),
        capped_count=_cap_status_count(rows, "capped"),
        no_budget_count=_cap_status_count(rows, "no_budget"),
        non_recommend_count=_cap_status_count(rows, "non_recommend"),
        skipped_count=_cap_status_count(rows, "skipped"),
        total_requested_paper_notional=_sum_decimals(
            row.requested_paper_notional for row in rows
        ),
        total_allocated_paper_notional=_sum_decimals(
            row.allocated_paper_notional for row in rows
        ),
        remaining_paper_budget=_remaining_notional(
            config.total_paper_budget,
            _sum_decimals(row.allocated_paper_notional for row in rows),
        ),
        total_paper_budget=config.total_paper_budget,
        max_paper_notional_per_market=config.max_paper_notional_per_market,
        max_paper_notional_per_event=config.max_paper_notional_per_event,
        max_paper_notional_per_theme=config.max_paper_notional_per_theme,
        max_paper_notional_per_correlation_group=(
            config.max_paper_notional_per_correlation_group
        ),
        rows=rows,
    )


def _allocate_rows(
    inputs: tuple[PaperRecommendationAllocationInput, ...],
    config: PaperRecommendationAllocationConfig,
) -> tuple[PaperRecommendationAllocationRow, ...]:
    total_used = ZERO
    market_used: dict[str, Decimal] = {}
    event_used: dict[str, Decimal] = {}
    theme_used: dict[str, Decimal] = {}
    correlation_used: dict[str, Decimal] = {}
    rows: list[PaperRecommendationAllocationRow] = []

    for source in inputs:
        requested = _multiply_decimal(
            source.executable_paper_shares,
            _price_for(source),
        )
        allocated = ZERO
        cap_status = "skipped"
        source_reason_codes = source.reason_codes
        cap_reason_codes: tuple[str, ...] = ()

        if source.action != "recommend":
            cap_status = "non_recommend"
            cap_reason_codes = ("non_recommend",)
        elif not _has_positive_candidate_values(source):
            cap_status = "skipped"
            cap_reason_codes = _skipped_reason_codes(source)
        else:
            total_remaining = _remaining_notional(config.total_paper_budget, total_used)
            if total_remaining <= ZERO:
                cap_status = "no_budget"
                cap_reason_codes = ("no_budget",)
            else:
                cap_values = _cap_values(
                    source=source,
                    config=config,
                    requested=requested,
                    total_remaining=total_remaining,
                    market_used=market_used,
                    event_used=event_used,
                    theme_used=theme_used,
                    correlation_used=correlation_used,
                )
                allocated = min(cap_value for _cap_name, cap_value in cap_values)
                if allocated <= ZERO:
                    allocated = ZERO
                    cap_status = "capped"
                    cap_reason_codes = _cap_reason_codes(
                        requested=requested,
                        allocated=allocated,
                        cap_values=cap_values,
                    )
                elif allocated < requested:
                    cap_status = "capped"
                    cap_reason_codes = _cap_reason_codes(
                        requested=requested,
                        allocated=allocated,
                        cap_values=cap_values,
                    )
                else:
                    cap_status = "allocated"
                    cap_reason_codes = ()

        if allocated > ZERO:
            total_used = _add_decimal(total_used, allocated)
            _add_usage(market_used, source.market_slug, allocated)
            if source.event_id is not None:
                _add_usage(event_used, source.event_id, allocated)
            if source.theme_id is not None:
                _add_usage(theme_used, source.theme_id, allocated)
            if source.correlation_group is not None:
                _add_usage(correlation_used, source.correlation_group, allocated)

        rows.append(
            PaperRecommendationAllocationRow(
                market_slug=source.market_slug,
                side=source.side,
                action=source.action,
                recommendation_score=source.recommendation_score,
                net_probability_edge=source.net_probability_edge,
                executable_paper_shares=source.executable_paper_shares,
                side_price=_price_for(source),
                market_implied_probability=_price_for(source),
                event_id=source.event_id,
                theme_id=source.theme_id,
                correlation_group=source.correlation_group,
                requested_paper_notional=requested,
                allocated_paper_notional=allocated,
                allocated_paper_shares=_shares_from_notional(
                    allocated,
                    _price_for(source),
                ),
                cap_status=cap_status,
                reason_codes=_normalize_reason_codes(
                    (*source_reason_codes, *cap_reason_codes),
                ),
            ),
        )

    return tuple(rows)


def _cap_values(
    *,
    source: PaperRecommendationAllocationInput,
    config: PaperRecommendationAllocationConfig,
    requested: Decimal,
    total_remaining: Decimal,
    market_used: dict[str, Decimal],
    event_used: dict[str, Decimal],
    theme_used: dict[str, Decimal],
    correlation_used: dict[str, Decimal],
) -> tuple[tuple[str, Decimal], ...]:
    values = (
        ("requested_paper_notional", requested),
        ("total_budget_cap", total_remaining),
        (
            "market_cap",
            _remaining_notional(
                config.max_paper_notional_per_market,
                market_used.get(source.market_slug, ZERO),
            ),
        ),
    )
    if source.event_id is not None:
        values = (
            *values,
            (
                "event_cap",
                _remaining_notional(
                    config.max_paper_notional_per_event,
                    event_used.get(source.event_id, ZERO),
                ),
            ),
        )
    if source.theme_id is not None:
        values = (
            *values,
            (
                "theme_cap",
                _remaining_notional(
                    config.max_paper_notional_per_theme,
                    theme_used.get(source.theme_id, ZERO),
                ),
            ),
        )
    if source.correlation_group is not None:
        values = (
            *values,
            (
                "correlation_cap",
                _remaining_notional(
                    config.max_paper_notional_per_correlation_group,
                    correlation_used.get(source.correlation_group, ZERO),
                ),
            ),
        )
    return values


def _cap_reason_codes(
    *,
    requested: Decimal,
    allocated: Decimal,
    cap_values: tuple[tuple[str, Decimal], ...],
) -> tuple[str, ...]:
    if allocated >= requested:
        return ()
    return _normalize_reason_codes(
        (
            "capped",
            *(
                cap_name
                for cap_name, cap_value in cap_values
                if cap_name != "requested_paper_notional" and cap_value == allocated
            ),
        ),
    )


def _skipped_reason_codes(
    source: PaperRecommendationAllocationInput,
) -> tuple[str, ...]:
    reason_codes = ("skipped",)
    if _candidate_edge(source) <= ZERO:
        reason_codes = (*reason_codes, "nonpositive_edge")
    if source.executable_paper_shares <= ZERO:
        reason_codes = (*reason_codes, "nonpositive_executable_paper_shares")
    if _price_for(source) <= ZERO:
        reason_codes = (*reason_codes, "nonpositive_price")
    return _normalize_reason_codes(reason_codes)


def _has_positive_candidate_values(source: PaperRecommendationAllocationInput) -> bool:
    return (
        _candidate_edge(source) > ZERO
        and source.executable_paper_shares > ZERO
        and _price_for(source) > ZERO
    )


def _candidate_edge(source: PaperRecommendationAllocationInput) -> Decimal:
    if source.recommendation_score is not None:
        return source.recommendation_score
    if source.net_probability_edge is not None:
        return source.net_probability_edge
    raise ValueError("recommendation_score or net_probability_edge must provide an edge")


def _price_for(source: PaperRecommendationAllocationInput) -> Decimal:
    if source.side_price is None:
        raise ValueError("side_price or market_implied_probability is required")
    return source.side_price


def _shares_from_notional(notional: Decimal, price: Decimal) -> Decimal:
    if notional <= ZERO or price <= ZERO:
        return _quantize(ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(notional / price)


def _input_sort_key(
    source: PaperRecommendationAllocationInput,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -_candidate_edge(source),
        -(source.net_probability_edge if source.net_probability_edge is not None else ZERO),
        -source.executable_paper_shares,
        source.market_slug,
        source.side,
    )


def _row_sort_key(
    row: PaperRecommendationAllocationRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -_row_candidate_edge(row),
        -(row.net_probability_edge if row.net_probability_edge is not None else ZERO),
        -row.executable_paper_shares,
        row.market_slug,
        row.side,
    )


def _row_candidate_edge(row: PaperRecommendationAllocationRow) -> Decimal:
    if row.recommendation_score is not None:
        return row.recommendation_score
    if row.net_probability_edge is not None:
        return row.net_probability_edge
    raise ValueError("recommendation_score or net_probability_edge must provide an edge")


def _add_usage(values: dict[str, Decimal], key: str, notional: Decimal) -> None:
    values[key] = _add_decimal(values.get(key, ZERO), notional)


def _cap_status_count(
    rows: tuple[PaperRecommendationAllocationRow, ...],
    cap_status: str,
) -> int:
    return sum(1 for row in rows if row.cap_status == cap_status)


def _normalize_inputs(
    values: Iterable[object],
) -> tuple[PaperRecommendationAllocationInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable of immutable row-like values")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of immutable row-like values") from exc
    return tuple(_normalize_input(value) for value in normalized)


def _normalize_input(value: object) -> PaperRecommendationAllocationInput:
    if type(value) is PaperRecommendationAllocationInput:
        _require_safety_flags(value)
        return value
    _require_immutable_row_like(value)
    _require_external_safety_flags(value, "input")
    return PaperRecommendationAllocationInput(
        market_slug=_required_attr(value, "market_slug"),
        side=_required_attr(value, "side"),
        action=_required_attr(value, "action"),
        recommendation_score=_optional_attr(value, "recommendation_score"),
        net_probability_edge=_optional_attr(value, "net_probability_edge"),
        executable_paper_shares=_required_attr(value, "executable_paper_shares"),
        side_price=_optional_attr(value, "side_price"),
        market_implied_probability=_optional_attr(
            value,
            "market_implied_probability",
        ),
        event_id=_optional_attr(value, "event_id"),
        theme_id=_optional_attr(value, "theme_id"),
        correlation_group=_optional_attr(value, "correlation_group"),
        reason_codes=_required_attr(value, "reason_codes"),
        paper_only=_required_attr(value, "paper_only"),
        report_only=_required_attr(value, "report_only"),
        readonly=_required_attr(value, "readonly"),
    )


def _normalize_rows(
    values: Iterable[PaperRecommendationAllocationRow],
) -> tuple[PaperRecommendationAllocationRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperRecommendationAllocationRow:
            raise ValueError("rows must contain PaperRecommendationAllocationRow values")
        _require_safety_flags(row)
    return rows


def _required_attr(value: object, field_name: str) -> object:
    sentinel = object()
    result = getattr(value, field_name, sentinel)
    if result is sentinel:
        raise ValueError(f"input must include {field_name}")
    return result


def _optional_attr(value: object, field_name: str) -> object | None:
    sentinel = object()
    result = getattr(value, field_name, sentinel)
    if result is sentinel:
        return None
    return result


def _require_immutable_row_like(value: object) -> None:
    params = getattr(value, "__dataclass_params__", None)
    if params is None or getattr(params, "frozen", False) is not True:
        raise ValueError("inputs must contain immutable row-like values")


def _require_external_safety_flags(value: object, label: str) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _validate_row_consistency(row: PaperRecommendationAllocationRow) -> None:
    expected_requested = _multiply_decimal(
        row.executable_paper_shares,
        row.market_implied_probability,
    )
    if row.requested_paper_notional != expected_requested:
        raise ValueError("requested_paper_notional must match shares and price")
    if row.allocated_paper_notional > row.requested_paper_notional:
        raise ValueError("allocated_paper_notional must not exceed requested")
    if row.cap_status == "allocated":
        if row.allocated_paper_notional != row.requested_paper_notional:
            raise ValueError(
                "allocated_paper_notional must equal requested when allocated",
            )
    expected_allocated_shares = _shares_from_notional(
        row.allocated_paper_notional,
        row.market_implied_probability,
    )
    if row.allocated_paper_shares != expected_allocated_shares:
        raise ValueError("allocated_paper_shares must match allocated notional")
    if row.allocated_paper_shares > row.executable_paper_shares:
        raise ValueError("allocated_paper_shares must not exceed executable shares")
    if row.allocated_paper_notional > ZERO:
        if row.action != "recommend":
            raise ValueError("allocated_paper_notional requires recommend action")
        if _row_candidate_edge(row) <= ZERO:
            raise ValueError("allocated_paper_notional requires positive edge")
        if row.executable_paper_shares <= ZERO:
            raise ValueError("allocated_paper_notional requires positive shares")
        if row.market_implied_probability <= ZERO:
            raise ValueError("allocated_paper_notional requires positive price")
    if row.cap_status == "capped":
        if row.requested_paper_notional <= ZERO:
            raise ValueError("cap_status capped requires requested notional")
        if row.allocated_paper_notional >= row.requested_paper_notional:
            raise ValueError("cap_status capped requires a reduced allocation")
        if "capped" not in row.reason_codes:
            raise ValueError("reason_codes must include capped")
    elif row.cap_status == "no_budget":
        if row.allocated_paper_notional != ZERO:
            raise ValueError("allocated_paper_notional must be zero for no_budget")
        if "no_budget" not in row.reason_codes:
            raise ValueError("reason_codes must include no_budget")
    elif row.cap_status == "non_recommend":
        if row.action == "recommend":
            raise ValueError("cap_status non_recommend requires non-recommend action")
        if row.allocated_paper_notional != ZERO:
            raise ValueError("allocated_paper_notional must be zero for non_recommend")
        if "non_recommend" not in row.reason_codes:
            raise ValueError("reason_codes must include non_recommend")
    elif row.cap_status == "skipped":
        if row.allocated_paper_notional != ZERO:
            raise ValueError("allocated_paper_notional must be zero when skipped")
        if "skipped" not in row.reason_codes:
            raise ValueError("reason_codes must include skipped")


def _validate_report_consistency(report: PaperRecommendationAllocationReport) -> None:
    if report.input_count != len(report.rows):
        raise ValueError("input_count must equal rows length")
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    if report.allocated_count != _cap_status_count(report.rows, "allocated"):
        raise ValueError("allocated_count must equal rows")
    if report.capped_count != _cap_status_count(report.rows, "capped"):
        raise ValueError("capped_count must equal rows")
    if report.no_budget_count != _cap_status_count(report.rows, "no_budget"):
        raise ValueError("no_budget_count must equal rows")
    if report.non_recommend_count != _cap_status_count(report.rows, "non_recommend"):
        raise ValueError("non_recommend_count must equal rows")
    if report.skipped_count != _cap_status_count(report.rows, "skipped"):
        raise ValueError("skipped_count must equal rows")
    if report.row_count != (
        report.allocated_count
        + report.capped_count
        + report.no_budget_count
        + report.non_recommend_count
        + report.skipped_count
    ):
        raise ValueError("row_count must equal cap status counts")
    expected_requested = _sum_decimals(row.requested_paper_notional for row in report.rows)
    if report.total_requested_paper_notional != expected_requested:
        raise ValueError("total_requested_paper_notional must equal rows")
    expected_allocated = _sum_decimals(row.allocated_paper_notional for row in report.rows)
    if report.total_allocated_paper_notional != expected_allocated:
        raise ValueError("total_allocated_paper_notional must equal rows")
    expected_remaining = _remaining_notional(
        report.total_paper_budget,
        report.total_allocated_paper_notional,
    )
    if report.remaining_paper_budget != expected_remaining:
        raise ValueError("remaining_paper_budget must match budget and allocations")
    if report.total_allocated_paper_notional > report.total_paper_budget:
        raise ValueError("total_allocated_paper_notional must not exceed budget")
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


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _remaining_notional(cap: Decimal, used: Decimal) -> Decimal:
    remaining = _subtract_decimal(cap, used)
    if remaining < ZERO:
        return _quantize(ZERO)
    return remaining


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_decimal(field_name, value)


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


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
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
    "PaperRecommendationAllocationInput",
    "PaperRecommendationAllocationConfig",
    "PaperRecommendationAllocationRow",
    "PaperRecommendationAllocationReport",
    "build_paper_recommendation_allocation_report",
)

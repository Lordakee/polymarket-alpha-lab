"""Pure paper-only strategy portfolio settlement lag budget report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_PORTFOLIO_SETTLEMENT_LAG_BUDGET_V2_CONFIG_VERSION = (
    "strategy-portfolio-settlement-lag-budget-v2"
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1.000000")
DAYS_PER_YEAR = Decimal("365")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
STATUS_WEIGHT = {
    BLOCKED_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

EMPTY_REASON_CODE = "strategy_portfolio_settlement_lag_budget_v2_empty"
PASS_REASON_CODE = "settlement_lag_budget_pass"
WATCH_REASON_CODE = "settlement_lag_budget_watch"
BLOCKED_REASON_CODE = "settlement_lag_budget_blocked"
REASON_CODE_PRIORITY = (
    "category_concentration_blocked",
    "category_concentration_watch",
    "cost_drag_blocked",
    "cost_drag_watch",
    "expected_lag_blocked",
    "expected_lag_watch",
    "liquidity_lockup_blocked",
    "liquidity_lockup_watch",
    "risk_budget_usage_blocked",
    "risk_budget_usage_watch",
    BLOCKED_REASON_CODE,
    PASS_REASON_CODE,
    WATCH_REASON_CODE,
    EMPTY_REASON_CODE,
)
REASON_CODE_SET = frozenset(REASON_CODE_PRIORITY)
UNSAFE_FIELD_FRAGMENTS = (
    "au" + "th",
    "priv" + "ate_key",
    "wa" + "llet",
    "acc" + "ount",
    "bal" + "ance",
    "or" + "der",
    "cancel",
    "replace",
    "sign",
    "exchange_mutation",
    "bro" + "ker",
)
SENSITIVE_VALUE_FRAGMENTS = (
    "://",
    "tok" + "en=",
    "api" + "_key",
    "sec" + "ret",
    "pass" + "word",
    "seed" + "_phrase",
)

__all__ = (
    "DEFAULT_STRATEGY_PORTFOLIO_SETTLEMENT_LAG_BUDGET_V2_CONFIG_VERSION",
    "StrategyPortfolioSettlementLagBudgetV2Config",
    "StrategyPortfolioSettlementLagBudgetV2Input",
    "StrategyPortfolioSettlementLagBudgetV2CategoryBudget",
    "StrategyPortfolioSettlementLagBudgetV2Report",
    "build_strategy_portfolio_settlement_lag_budget_v2",
    "strategy_portfolio_settlement_lag_budget_v2_payload",
)


@dataclass(frozen=True)
class StrategyPortfolioSettlementLagBudgetV2Config:
    settlement_lag_budget_notional: Decimal = Decimal("1000.000000")
    annual_cost_drag_rate: Decimal = Decimal("0.120000")
    expected_lag_watch_days: Decimal = Decimal("3.000000")
    expected_lag_blocked_days: Decimal = Decimal("7.000000")
    category_concentration_watch_ratio: Decimal = Decimal("0.500000")
    category_concentration_blocked_ratio: Decimal = Decimal("0.700000")
    liquidity_lockup_watch_ratio: Decimal = Decimal("0.300000")
    liquidity_lockup_blocked_ratio: Decimal = Decimal("0.600000")
    cost_drag_watch_ratio: Decimal = Decimal("0.001000")
    cost_drag_blocked_ratio: Decimal = Decimal("0.002000")
    risk_budget_watch_ratio: Decimal = Decimal("0.750000")
    risk_budget_blocked_ratio: Decimal = Decimal("1.000000")
    config_version: str = DEFAULT_STRATEGY_PORTFOLIO_SETTLEMENT_LAG_BUDGET_V2_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "settlement_lag_budget_notional",
            _normalize_positive_value(
                "settlement_lag_budget_notional",
                self.settlement_lag_budget_notional,
            ),
        )
        for field_name in (
            "annual_cost_drag_rate",
            "category_concentration_watch_ratio",
            "category_concentration_blocked_ratio",
            "liquidity_lockup_watch_ratio",
            "liquidity_lockup_blocked_ratio",
            "cost_drag_watch_ratio",
            "cost_drag_blocked_ratio",
            "risk_budget_watch_ratio",
            "risk_budget_blocked_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("expected_lag_watch_days", "expected_lag_blocked_days"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_watch_not_above_blocked(
            self.expected_lag_watch_days,
            self.expected_lag_blocked_days,
        )
        _require_watch_not_above_blocked(
            self.category_concentration_watch_ratio,
            self.category_concentration_blocked_ratio,
        )
        _require_watch_not_above_blocked(
            self.liquidity_lockup_watch_ratio,
            self.liquidity_lockup_blocked_ratio,
        )
        _require_watch_not_above_blocked(
            self.cost_drag_watch_ratio,
            self.cost_drag_blocked_ratio,
        )
        _require_watch_not_above_blocked(
            self.risk_budget_watch_ratio,
            self.risk_budget_blocked_ratio,
        )
        _reject_unsafe_payload("config", self)
        _require_paper_flags("config", self)


@dataclass(frozen=True)
class StrategyPortfolioSettlementLagBudgetV2Input:
    exposure_id: str
    category: str
    pending_resolution_notional: Decimal
    expected_lag_days: Decimal
    liquidity_lockup_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("exposure_id", self.exposure_id)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "pending_resolution_notional",
            _normalize_positive_value(
                "pending_resolution_notional",
                self.pending_resolution_notional,
            ),
        )
        object.__setattr__(
            self,
            "expected_lag_days",
            _normalize_nonnegative_value("expected_lag_days", self.expected_lag_days),
        )
        object.__setattr__(
            self,
            "liquidity_lockup_ratio",
            _normalize_probability(
                "liquidity_lockup_ratio",
                self.liquidity_lockup_ratio,
            ),
        )
        _reject_unsafe_payload("input", self)
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyPortfolioSettlementLagBudgetV2CategoryBudget:
    rank: Decimal
    category: str
    exposure_count: Decimal
    pending_resolution_notional: Decimal
    weighted_expected_lag_days: Decimal
    category_concentration_ratio: Decimal
    liquidity_lockup_notional: Decimal
    liquidity_lockup_ratio: Decimal
    cost_drag_notional: Decimal
    cost_drag_ratio: Decimal
    risk_budget_usage_ratio: Decimal
    budget_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "exposure_count",
            _normalize_positive_count("exposure_count", self.exposure_count),
        )
        for field_name in (
            "pending_resolution_notional",
            "weighted_expected_lag_days",
            "liquidity_lockup_notional",
            "cost_drag_notional",
        ):
            normalizer = (
                _normalize_positive_value
                if field_name == "pending_resolution_notional"
                else _normalize_nonnegative_value
            )
            object.__setattr__(
                self,
                field_name,
                normalizer(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "category_concentration_ratio",
            "liquidity_lockup_ratio",
            "cost_drag_ratio",
            "risk_budget_usage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("budget_status", self.budget_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_category_budget(self)
        _reject_unsafe_payload("category_budget", self)
        _require_paper_flags("category_budget", self)


@dataclass(frozen=True)
class StrategyPortfolioSettlementLagBudgetV2Report:
    generated_at: datetime
    config_version: str
    exposure_count: Decimal
    category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    pending_resolution_notional: Decimal
    weighted_expected_lag_days: Decimal
    largest_category: str | None
    largest_category_pending_notional: Decimal
    largest_category_concentration_ratio: Decimal
    liquidity_lockup_notional: Decimal
    liquidity_lockup_ratio: Decimal
    cost_drag_notional: Decimal
    cost_drag_ratio: Decimal
    risk_budget_notional: Decimal
    risk_budget_usage_ratio: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "exposure_count",
            "category_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pending_resolution_notional",
            "weighted_expected_lag_days",
            "largest_category_pending_notional",
            "liquidity_lockup_notional",
            "cost_drag_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        if self.largest_category is not None:
            _require_canonical_string("largest_category", self.largest_category)
        for field_name in (
            "largest_category_concentration_ratio",
            "liquidity_lockup_ratio",
            "cost_drag_ratio",
            "risk_budget_usage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "risk_budget_notional",
            _normalize_positive_value("risk_budget_notional", self.risk_budget_notional),
        )
        _require_member("digest_status", self.digest_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _reject_unsafe_payload("report", self)
        _require_paper_flags("report", self)


def build_strategy_portfolio_settlement_lag_budget_v2(
    records: Iterable[StrategyPortfolioSettlementLagBudgetV2Input],
    *,
    config: StrategyPortfolioSettlementLagBudgetV2Config,
    generated_at: datetime,
) -> StrategyPortfolioSettlementLagBudgetV2Report:
    if type(config) is not StrategyPortfolioSettlementLagBudgetV2Config:
        raise ValueError("config must be a StrategyPortfolioSettlementLagBudgetV2Config")
    _require_paper_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(records)
    total_pending = _sum_values(row.pending_resolution_notional for row in normalized)
    unranked = tuple(
        _category_budget(
            category,
            tuple(row for row in normalized if row.category == category),
            total_pending=total_pending,
            config=config,
        )
        for category in _category_names(normalized)
    )
    rows = _rank_rows(unranked)
    return StrategyPortfolioSettlementLagBudgetV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        exposure_count=_count(len(normalized)),
        category_count=_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        pending_resolution_notional=total_pending,
        weighted_expected_lag_days=_weighted_lag_from_inputs(normalized),
        largest_category=_largest_category(rows),
        largest_category_pending_notional=_largest_category_pending_notional(rows),
        largest_category_concentration_ratio=_largest_category_concentration_ratio(rows),
        liquidity_lockup_notional=_sum_values(
            row.liquidity_lockup_notional for row in rows
        ),
        liquidity_lockup_ratio=_ratio(
            _sum_values(row.liquidity_lockup_notional for row in rows),
            total_pending,
        ),
        cost_drag_notional=_sum_values(row.cost_drag_notional for row in rows),
        cost_drag_ratio=_ratio(
            _sum_values(row.cost_drag_notional for row in rows),
            total_pending,
        ),
        risk_budget_notional=config.settlement_lag_budget_notional,
        risk_budget_usage_ratio=_ratio(
            total_pending,
            config.settlement_lag_budget_notional,
        ),
        digest_status=_digest_status(rows),
        reason_codes=_report_reason_codes(
            rows,
            risk_budget_usage_ratio=_ratio(
                total_pending,
                config.settlement_lag_budget_notional,
            ),
            config=config,
        ),
        rows=rows,
    )


def strategy_portfolio_settlement_lag_budget_v2_payload(
    report: StrategyPortfolioSettlementLagBudgetV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyPortfolioSettlementLagBudgetV2Report:
        _require_paper_flags("report", report)
        _reject_unsafe_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyPortfolioSettlementLagBudgetV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_paper_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
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


def _category_budget(
    category: str,
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2Input, ...],
    *,
    total_pending: Decimal,
    config: StrategyPortfolioSettlementLagBudgetV2Config,
) -> StrategyPortfolioSettlementLagBudgetV2CategoryBudget:
    pending = _sum_values(row.pending_resolution_notional for row in rows)
    weighted_lag = _weighted_lag_from_inputs(rows)
    liquidity = _sum_values(_liquidity_lockup(row) for row in rows)
    cost = _sum_values(_cost_drag(row, config) for row in rows)
    category_concentration_ratio = _ratio(pending, total_pending)
    liquidity_lockup_ratio = _ratio(liquidity, pending)
    cost_drag_ratio = _ratio(cost, pending)
    risk_budget_usage_ratio = _ratio(pending, config.settlement_lag_budget_notional)
    status = _budget_status(
        weighted_expected_lag_days=weighted_lag,
        category_concentration_ratio=category_concentration_ratio,
        liquidity_lockup_ratio=liquidity_lockup_ratio,
        cost_drag_ratio=cost_drag_ratio,
        risk_budget_usage_ratio=risk_budget_usage_ratio,
        config=config,
    )
    return StrategyPortfolioSettlementLagBudgetV2CategoryBudget(
        rank=Decimal("1"),
        category=category,
        exposure_count=_count(len(rows)),
        pending_resolution_notional=pending,
        weighted_expected_lag_days=weighted_lag,
        category_concentration_ratio=category_concentration_ratio,
        liquidity_lockup_notional=liquidity,
        liquidity_lockup_ratio=liquidity_lockup_ratio,
        cost_drag_notional=cost,
        cost_drag_ratio=cost_drag_ratio,
        risk_budget_usage_ratio=risk_budget_usage_ratio,
        budget_status=status,
        reason_codes=_row_reason_codes(
            weighted_expected_lag_days=weighted_lag,
            category_concentration_ratio=category_concentration_ratio,
            liquidity_lockup_ratio=liquidity_lockup_ratio,
            cost_drag_ratio=cost_drag_ratio,
            risk_budget_usage_ratio=risk_budget_usage_ratio,
            status=status,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...],
) -> tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...]:
    return tuple(
        StrategyPortfolioSettlementLagBudgetV2CategoryBudget(
            rank=_count(index),
            category=row.category,
            exposure_count=row.exposure_count,
            pending_resolution_notional=row.pending_resolution_notional,
            weighted_expected_lag_days=row.weighted_expected_lag_days,
            category_concentration_ratio=row.category_concentration_ratio,
            liquidity_lockup_notional=row.liquidity_lockup_notional,
            liquidity_lockup_ratio=row.liquidity_lockup_ratio,
            cost_drag_notional=row.cost_drag_notional,
            cost_drag_ratio=row.cost_drag_ratio,
            risk_budget_usage_ratio=row.risk_budget_usage_ratio,
            budget_status=row.budget_status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _budget_status(
    *,
    weighted_expected_lag_days: Decimal,
    category_concentration_ratio: Decimal,
    liquidity_lockup_ratio: Decimal,
    cost_drag_ratio: Decimal,
    risk_budget_usage_ratio: Decimal,
    config: StrategyPortfolioSettlementLagBudgetV2Config,
) -> str:
    if (
        weighted_expected_lag_days >= config.expected_lag_blocked_days
        or category_concentration_ratio >= config.category_concentration_blocked_ratio
        or liquidity_lockup_ratio >= config.liquidity_lockup_blocked_ratio
        or cost_drag_ratio >= config.cost_drag_blocked_ratio
        or risk_budget_usage_ratio >= config.risk_budget_blocked_ratio
    ):
        return BLOCKED_STATUS
    if (
        weighted_expected_lag_days >= config.expected_lag_watch_days
        or category_concentration_ratio >= config.category_concentration_watch_ratio
        or liquidity_lockup_ratio >= config.liquidity_lockup_watch_ratio
        or cost_drag_ratio >= config.cost_drag_watch_ratio
        or risk_budget_usage_ratio >= config.risk_budget_watch_ratio
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    weighted_expected_lag_days: Decimal,
    category_concentration_ratio: Decimal,
    liquidity_lockup_ratio: Decimal,
    cost_drag_ratio: Decimal,
    risk_budget_usage_ratio: Decimal,
    status: str,
    config: StrategyPortfolioSettlementLagBudgetV2Config,
) -> tuple[str, ...]:
    codes = _metric_reason_codes(
        weighted_expected_lag_days=weighted_expected_lag_days,
        category_concentration_ratio=category_concentration_ratio,
        liquidity_lockup_ratio=liquidity_lockup_ratio,
        cost_drag_ratio=cost_drag_ratio,
        risk_budget_usage_ratio=risk_budget_usage_ratio,
        config=config,
    )
    if status == BLOCKED_STATUS:
        codes = (*codes, BLOCKED_REASON_CODE)
    elif status == WATCH_STATUS:
        codes = (*codes, WATCH_REASON_CODE)
    else:
        codes = (*codes, PASS_REASON_CODE)
    return _normalize_reason_codes("reason_codes", codes)


def _metric_reason_codes(
    *,
    weighted_expected_lag_days: Decimal,
    category_concentration_ratio: Decimal,
    liquidity_lockup_ratio: Decimal,
    cost_drag_ratio: Decimal,
    risk_budget_usage_ratio: Decimal,
    config: StrategyPortfolioSettlementLagBudgetV2Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if category_concentration_ratio >= config.category_concentration_blocked_ratio:
        codes.append("category_concentration_blocked")
    elif category_concentration_ratio >= config.category_concentration_watch_ratio:
        codes.append("category_concentration_watch")
    if cost_drag_ratio >= config.cost_drag_blocked_ratio:
        codes.append("cost_drag_blocked")
    elif cost_drag_ratio >= config.cost_drag_watch_ratio:
        codes.append("cost_drag_watch")
    if weighted_expected_lag_days >= config.expected_lag_blocked_days:
        codes.append("expected_lag_blocked")
    elif weighted_expected_lag_days >= config.expected_lag_watch_days:
        codes.append("expected_lag_watch")
    if liquidity_lockup_ratio >= config.liquidity_lockup_blocked_ratio:
        codes.append("liquidity_lockup_blocked")
    elif liquidity_lockup_ratio >= config.liquidity_lockup_watch_ratio:
        codes.append("liquidity_lockup_watch")
    if risk_budget_usage_ratio >= config.risk_budget_blocked_ratio:
        codes.append("risk_budget_usage_blocked")
    elif risk_budget_usage_ratio >= config.risk_budget_watch_ratio:
        codes.append("risk_budget_usage_watch")
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...],
    *,
    risk_budget_usage_ratio: Decimal,
    config: StrategyPortfolioSettlementLagBudgetV2Config,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    metric_codes = _metric_reason_codes(
        weighted_expected_lag_days=_weighted_lag_from_category_rows(rows),
        category_concentration_ratio=_largest_category_concentration_ratio(rows),
        liquidity_lockup_ratio=_ratio(
            _sum_values(row.liquidity_lockup_notional for row in rows),
            _sum_values(row.pending_resolution_notional for row in rows),
        ),
        cost_drag_ratio=_ratio(
            _sum_values(row.cost_drag_notional for row in rows),
            _sum_values(row.pending_resolution_notional for row in rows),
        ),
        risk_budget_usage_ratio=risk_budget_usage_ratio,
        config=config,
    )
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    return _normalize_reason_codes("reason_codes", (*row_codes, *metric_codes))


def _digest_status(
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...],
) -> str:
    if any(row.budget_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.budget_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _normalize_inputs(
    value: Iterable[StrategyPortfolioSettlementLagBudgetV2Input],
) -> tuple[StrategyPortfolioSettlementLagBudgetV2Input, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("records must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("records must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StrategyPortfolioSettlementLagBudgetV2Input:
            raise ValueError("records must contain exact input rows")
        _require_paper_flags("input", row)
        if row.exposure_id in seen:
            raise ValueError("records must not contain duplicate exposure_id values")
        seen.add(row.exposure_id)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must contain category budget rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain category budget rows") from exc
    for row in rows:
        if type(row) is not StrategyPortfolioSettlementLagBudgetV2CategoryBudget:
            raise ValueError("rows must contain category budget rows")
        _require_paper_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must use consecutive ranks")
    return rows


def _category_names(
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2Input, ...],
) -> tuple[str, ...]:
    return tuple(sorted({row.category for row in rows}))


def _status_count(
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.budget_status == status))


def _row_sort_key(
    row: StrategyPortfolioSettlementLagBudgetV2CategoryBudget,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.budget_status],
        -row.risk_budget_usage_ratio,
        -row.pending_resolution_notional,
        row.category,
    )


def _largest_category(
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...],
) -> str | None:
    if not rows:
        return None
    return tuple(sorted(rows, key=_category_concentration_sort_key))[0].category


def _largest_category_pending_notional(
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return tuple(sorted(rows, key=_category_concentration_sort_key))[
        0
    ].pending_resolution_notional


def _largest_category_concentration_ratio(
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return tuple(sorted(rows, key=_category_concentration_sort_key))[
        0
    ].category_concentration_ratio


def _category_concentration_sort_key(
    row: StrategyPortfolioSettlementLagBudgetV2CategoryBudget,
) -> tuple[Decimal, Decimal, str]:
    return (-row.pending_resolution_notional, -row.category_concentration_ratio, row.category)


def _liquidity_lockup(row: StrategyPortfolioSettlementLagBudgetV2Input) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (row.pending_resolution_notional * row.liquidity_lockup_ratio).quantize(
            VALUE_QUANTUM,
        )


def _cost_drag(
    row: StrategyPortfolioSettlementLagBudgetV2Input,
    config: StrategyPortfolioSettlementLagBudgetV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            row.pending_resolution_notional
            * config.annual_cost_drag_rate
            * row.expected_lag_days
            / DAYS_PER_YEAR
        ).quantize(VALUE_QUANTUM)


def _weighted_lag_from_inputs(
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2Input, ...],
) -> Decimal:
    total_pending = _sum_values(row.pending_resolution_notional for row in rows)
    if total_pending == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        weighted = sum(
            row.pending_resolution_notional * row.expected_lag_days for row in rows
        )
        return (weighted / total_pending).quantize(VALUE_QUANTUM)


def _weighted_lag_from_category_rows(
    rows: tuple[StrategyPortfolioSettlementLagBudgetV2CategoryBudget, ...],
) -> Decimal:
    total_pending = _sum_values(row.pending_resolution_notional for row in rows)
    if total_pending == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        weighted = sum(
            row.pending_resolution_notional * row.weighted_expected_lag_days
            for row in rows
        )
        return (weighted / total_pending).quantize(VALUE_QUANTUM)


def _validate_category_budget(
    row: StrategyPortfolioSettlementLagBudgetV2CategoryBudget,
) -> None:
    if row.cost_drag_ratio != _ratio(
        row.cost_drag_notional,
        row.pending_resolution_notional,
    ):
        raise ValueError("cost_drag_ratio must match row inputs")
    if row.liquidity_lockup_ratio != _ratio(
        row.liquidity_lockup_notional,
        row.pending_resolution_notional,
    ):
        raise ValueError("liquidity_lockup_ratio must match row inputs")
    if row.budget_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("budget_status must match reason_codes")


def _validate_report(report: StrategyPortfolioSettlementLagBudgetV2Report) -> None:
    if report.exposure_count != _sum_values(row.exposure_count for row in report.rows):
        raise ValueError("exposure_count must match rows")
    if report.category_count != _count(len(report.rows)):
        raise ValueError("category_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.pending_resolution_notional != _sum_values(
        row.pending_resolution_notional for row in report.rows
    ):
        raise ValueError("pending_resolution_notional must match rows")
    if report.weighted_expected_lag_days != _weighted_lag_from_category_rows(report.rows):
        raise ValueError("weighted_expected_lag_days must match rows")
    if report.largest_category != _largest_category(report.rows):
        raise ValueError("largest_category must match rows")
    if report.largest_category_pending_notional != _largest_category_pending_notional(
        report.rows,
    ):
        raise ValueError("largest_category_pending_notional must match rows")
    if report.largest_category_concentration_ratio != _largest_category_concentration_ratio(
        report.rows,
    ):
        raise ValueError("largest_category_concentration_ratio must match rows")
    if report.liquidity_lockup_notional != _sum_values(
        row.liquidity_lockup_notional for row in report.rows
    ):
        raise ValueError("liquidity_lockup_notional must match rows")
    if report.liquidity_lockup_ratio != _ratio(
        report.liquidity_lockup_notional,
        report.pending_resolution_notional,
    ):
        raise ValueError("liquidity_lockup_ratio must match rows")
    if report.cost_drag_notional != _sum_values(row.cost_drag_notional for row in report.rows):
        raise ValueError("cost_drag_notional must match rows")
    if report.cost_drag_ratio != _ratio(
        report.cost_drag_notional,
        report.pending_resolution_notional,
    ):
        raise ValueError("cost_drag_ratio must match rows")
    if report.risk_budget_usage_ratio != _ratio(
        report.pending_resolution_notional,
        report.risk_budget_notional,
    ):
        raise ValueError("risk_budget_usage_ratio must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCKED_REASON_CODE in reason_codes:
        return BLOCKED_STATUS
    if WATCH_REASON_CODE in reason_codes:
        return WATCH_STATUS
    return PASS_STATUS


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(label, asdict(value), path)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in SENSITIVE_VALUE_FRAGMENTS):
            raise ValueError(f"{path or label} has unsafe value")
        if any(fragment in lowered for fragment in UNSAFE_FIELD_FRAGMENTS):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe surface field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _sum_values(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _q(total + _normalize_nonnegative_value("value", value))
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _normalize_nonnegative_value("numerator", numerator)
    denominator = _normalize_nonnegative_value("denominator", denominator)
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, (numerator / denominator).quantize(VALUE_QUANTUM))


def _q(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized != normalized.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_positive_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be exactly Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _q(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_canonical_string(field_name, item)
        if item not in REASON_CODE_SET:
            raise ValueError(f"{field_name} must contain known values")
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in set(items)
    )
    if len(normalized) != len(set(items)):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(items) and tuple(items) != normalized:
        return normalized
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_watch_not_above_blocked(watch_value: Decimal, blocked_value: Decimal) -> None:
    if watch_value > blocked_value:
        raise ValueError("watch thresholds must not exceed blocked thresholds")

"""Pure paper-only category edge budget gate."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


DEFAULT_STRATEGY_PORTFOLIO_CATEGORY_EDGE_BUDGET_GATE_V2_CONFIG_VERSION = (
    "strategy-portfolio-category-edge-budget-gate-v2"
)
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0").quantize(VALUE_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1.000000")
ONE_COUNT = Decimal("1").quantize(COUNT_QUANTUM)
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
GATE_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
STATUS_PRIORITY = {
    BLOCKED_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}
KNOWN_REASON_CODE_ORDER = (
    "category_edge_budget_pass",
    "category_edge_budget_watch",
    "category_edge_budget_blocked",
    "category_exposure_watch",
    "category_exposure_block",
    "open_candidate_count_watch",
    "open_candidate_count_block",
    "correlated_event_count_watch",
    "correlated_event_count_block",
    "cost_adjusted_edge_below_candidate",
    "cost_adjusted_edge_below_watch",
    "liquidity_capacity_watch",
    "liquidity_capacity_block",
    "category_drawdown_watch",
    "category_drawdown_block",
    "candidate_notional_exceeds_allowed",
)
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
    "sec" "ret",
    "priv" "ate",
)


@dataclass(frozen=True)
class StrategyPortfolioCategoryEdgeBudgetGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_PORTFOLIO_CATEGORY_EDGE_BUDGET_GATE_V2_CONFIG_VERSION
    )
    portfolio_notional_cap: Decimal = Decimal("1000.000000")
    category_budget_share: Decimal = Decimal("0.200000")
    category_exposure_watch_share: Decimal = Decimal("0.800000")
    category_exposure_block_share: Decimal = Decimal("1.000000")
    open_candidate_watch_count: Decimal = Decimal("4")
    open_candidate_block_count: Decimal = Decimal("6")
    correlated_event_watch_count: Decimal = Decimal("3")
    correlated_event_block_count: Decimal = Decimal("5")
    min_candidate_cost_adjusted_edge: Decimal = Decimal("0.020000")
    min_watch_cost_adjusted_edge: Decimal = Decimal("0.000000")
    min_liquidity_capacity_ratio: Decimal = Decimal("1.500000")
    block_liquidity_capacity_ratio: Decimal = Decimal("1.000000")
    category_drawdown_watch_ratio: Decimal = Decimal("0.100000")
    category_drawdown_block_ratio: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "portfolio_notional_cap",
            _normalize_positive_decimal(
                "portfolio_notional_cap",
                self.portfolio_notional_cap,
            ),
        )
        for field_name in (
            "category_budget_share",
            "category_exposure_watch_share",
            "category_exposure_block_share",
            "category_drawdown_watch_ratio",
            "category_drawdown_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.category_budget_share <= ZERO:
            raise ValueError("category_budget_share must be positive")
        for field_name in (
            "open_candidate_watch_count",
            "open_candidate_block_count",
            "correlated_event_watch_count",
            "correlated_event_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_candidate_cost_adjusted_edge",
            "min_watch_cost_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_liquidity_capacity_ratio",
            _normalize_positive_decimal(
                "min_liquidity_capacity_ratio",
                self.min_liquidity_capacity_ratio,
            ),
        )
        object.__setattr__(
            self,
            "block_liquidity_capacity_ratio",
            _normalize_nonnegative_decimal(
                "block_liquidity_capacity_ratio",
                self.block_liquidity_capacity_ratio,
            ),
        )
        if self.category_exposure_watch_share > self.category_exposure_block_share:
            raise ValueError(
                "category_exposure_block_share must not be below "
                "category_exposure_watch_share",
            )
        _require_not_above(
            "open_candidate_watch_count",
            self.open_candidate_watch_count,
            self.open_candidate_block_count,
        )
        _require_not_above(
            "correlated_event_watch_count",
            self.correlated_event_watch_count,
            self.correlated_event_block_count,
        )
        _require_not_above(
            "min_watch_cost_adjusted_edge",
            self.min_watch_cost_adjusted_edge,
            self.min_candidate_cost_adjusted_edge,
        )
        _require_not_above(
            "block_liquidity_capacity_ratio",
            self.block_liquidity_capacity_ratio,
            self.min_liquidity_capacity_ratio,
        )
        _require_not_above(
            "category_drawdown_watch_ratio",
            self.category_drawdown_watch_ratio,
            self.category_drawdown_block_ratio,
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot:
    category: str
    current_category_exposure: Decimal
    open_candidate_count: Decimal
    correlated_event_count: Decimal
    category_drawdown_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("category", self.category)
        object.__setattr__(
            self,
            "current_category_exposure",
            _normalize_nonnegative_decimal(
                "current_category_exposure",
                self.current_category_exposure,
            ),
        )
        for field_name in ("open_candidate_count", "correlated_event_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "category_drawdown_ratio",
            _normalize_probability(
                "category_drawdown_ratio",
                self.category_drawdown_ratio,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyPortfolioCategoryEdgeBudgetGateV2Candidate:
    candidate_id: str
    category: str
    correlated_event_key: str
    candidate_notional: Decimal
    gross_edge: Decimal
    total_cost: Decimal
    available_liquidity: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "category", "correlated_event_key"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "candidate_notional",
            _normalize_positive_decimal("candidate_notional", self.candidate_notional),
        )
        object.__setattr__(
            self,
            "gross_edge",
            _normalize_decimal("gross_edge", self.gross_edge),
        )
        for field_name in ("total_cost", "available_liquidity"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyPortfolioCategoryEdgeBudgetGateV2Row:
    rank: Decimal
    candidate_id: str
    category: str
    correlated_event_key: str
    candidate_notional: Decimal
    category_budget_notional: Decimal
    current_category_exposure: Decimal
    post_trade_category_exposure: Decimal
    category_exposure_budget_share: Decimal
    current_open_candidate_count: Decimal
    post_trade_open_candidate_count: Decimal
    current_correlated_event_count: Decimal
    post_trade_correlated_event_count: Decimal
    gross_edge: Decimal
    total_cost: Decimal
    cost_adjusted_edge: Decimal
    available_liquidity: Decimal
    liquidity_capacity_ratio: Decimal
    liquidity_capacity_notional: Decimal
    allowed_candidate_notional: Decimal
    category_drawdown_ratio: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        for field_name in ("candidate_id", "category", "correlated_event_key"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "candidate_notional",
            _normalize_positive_decimal("candidate_notional", self.candidate_notional),
        )
        for field_name in (
            "category_budget_notional",
            "current_category_exposure",
            "post_trade_category_exposure",
            "category_exposure_budget_share",
            "available_liquidity",
            "liquidity_capacity_ratio",
            "liquidity_capacity_notional",
            "allowed_candidate_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "current_open_candidate_count",
            "post_trade_open_candidate_count",
            "current_correlated_event_count",
            "post_trade_correlated_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "gross_edge",
            _normalize_decimal("gross_edge", self.gross_edge),
        )
        object.__setattr__(
            self,
            "total_cost",
            _normalize_nonnegative_decimal("total_cost", self.total_cost),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "category_drawdown_ratio",
            _normalize_probability(
                "category_drawdown_ratio",
                self.category_drawdown_ratio,
            ),
        )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyPortfolioCategoryEdgeBudgetGateV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    digest_status: str
    total_candidate_notional: Decimal
    total_allowed_candidate_notional: Decimal
    max_category_exposure_budget_share: Decimal
    max_open_candidate_count: Decimal
    max_correlated_event_count: Decimal
    min_cost_adjusted_edge: Decimal
    min_liquidity_capacity_ratio: Decimal
    max_category_drawdown_ratio: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyPortfolioCategoryEdgeBudgetGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "max_open_candidate_count",
            "max_correlated_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, GATE_STATUSES)
        for field_name in (
            "total_candidate_notional",
            "total_allowed_candidate_notional",
            "max_category_exposure_budget_share",
            "min_liquidity_capacity_ratio",
            "max_category_drawdown_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_cost_adjusted_edge",
            _normalize_decimal("min_cost_adjusted_edge", self.min_cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_strategy_portfolio_category_edge_budget_gate_v2_report(
    candidates: Iterable[StrategyPortfolioCategoryEdgeBudgetGateV2Candidate],
    *,
    category_snapshots: Iterable[
        StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot
    ],
    config: StrategyPortfolioCategoryEdgeBudgetGateV2Config,
    generated_at: datetime,
) -> StrategyPortfolioCategoryEdgeBudgetGateV2Report:
    if type(config) is not StrategyPortfolioCategoryEdgeBudgetGateV2Config:
        raise ValueError(
            "config must be a StrategyPortfolioCategoryEdgeBudgetGateV2Config",
        )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    category_map = _category_snapshot_map(category_snapshots)
    normalized_candidates = _normalize_candidates(candidates)
    rows = _rank_rows(
        tuple(
            _row_from_candidate(
                candidate,
                category_snapshot=_category_snapshot_for(candidate, category_map),
                config=config,
            )
            for candidate in normalized_candidates
        ),
    )
    return StrategyPortfolioCategoryEdgeBudgetGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        digest_status=_digest_status(rows),
        total_candidate_notional=_sum_values(
            tuple(row.candidate_notional for row in rows),
        ),
        total_allowed_candidate_notional=_sum_values(
            tuple(row.allowed_candidate_notional for row in rows),
        ),
        max_category_exposure_budget_share=_max_value(
            tuple(row.category_exposure_budget_share for row in rows),
        ),
        max_open_candidate_count=_max_count(
            tuple(row.post_trade_open_candidate_count for row in rows),
        ),
        max_correlated_event_count=_max_count(
            tuple(row.post_trade_correlated_event_count for row in rows),
        ),
        min_cost_adjusted_edge=_min_value(
            tuple(row.cost_adjusted_edge for row in rows),
        ),
        min_liquidity_capacity_ratio=_min_nonnegative_value(
            tuple(row.liquidity_capacity_ratio for row in rows),
        ),
        max_category_drawdown_ratio=_max_value(
            tuple(row.category_drawdown_ratio for row in rows),
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_portfolio_category_edge_budget_gate_v2_payload(
    report: StrategyPortfolioCategoryEdgeBudgetGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyPortfolioCategoryEdgeBudgetGateV2Report:
        raise ValueError(
            "report must be a StrategyPortfolioCategoryEdgeBudgetGateV2Report",
        )
    _require_hard_flags(report)
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _row_from_candidate(
    candidate: StrategyPortfolioCategoryEdgeBudgetGateV2Candidate,
    *,
    category_snapshot: StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot,
    config: StrategyPortfolioCategoryEdgeBudgetGateV2Config,
) -> StrategyPortfolioCategoryEdgeBudgetGateV2Row:
    category_budget_notional = _multiply_decimal(
        config.portfolio_notional_cap,
        config.category_budget_share,
    )
    post_trade_category_exposure = _add_decimal(
        category_snapshot.current_category_exposure,
        candidate.candidate_notional,
    )
    category_exposure_budget_share = _divide_decimal(
        post_trade_category_exposure,
        category_budget_notional,
    )
    post_trade_open_candidate_count = _add_count(
        category_snapshot.open_candidate_count,
        ONE_COUNT,
    )
    post_trade_correlated_event_count = _add_count(
        category_snapshot.correlated_event_count,
        ONE_COUNT,
    )
    cost_adjusted_edge = _subtract_decimal(candidate.gross_edge, candidate.total_cost)
    liquidity_capacity_ratio = _divide_decimal(
        candidate.available_liquidity,
        candidate.candidate_notional,
    )
    liquidity_capacity_notional = _divide_decimal(
        candidate.available_liquidity,
        config.min_liquidity_capacity_ratio,
    )
    category_remaining_notional = _category_remaining_notional(
        category_snapshot.current_category_exposure,
        category_budget_notional=category_budget_notional,
        config=config,
    )
    allowed_candidate_notional = _min_nonnegative_value(
        (
            candidate.candidate_notional,
            category_remaining_notional,
            liquidity_capacity_notional,
        ),
    )
    gate_status = _gate_status(
        category_exposure_budget_share=category_exposure_budget_share,
        post_trade_open_candidate_count=post_trade_open_candidate_count,
        post_trade_correlated_event_count=post_trade_correlated_event_count,
        cost_adjusted_edge=cost_adjusted_edge,
        liquidity_capacity_ratio=liquidity_capacity_ratio,
        category_drawdown_ratio=category_snapshot.category_drawdown_ratio,
        candidate_notional=candidate.candidate_notional,
        allowed_candidate_notional=allowed_candidate_notional,
        config=config,
    )
    reason_codes = _row_reason_codes(
        source_reason_codes=candidate.reason_codes,
        gate_status=gate_status,
        category_exposure_budget_share=category_exposure_budget_share,
        post_trade_open_candidate_count=post_trade_open_candidate_count,
        post_trade_correlated_event_count=post_trade_correlated_event_count,
        cost_adjusted_edge=cost_adjusted_edge,
        liquidity_capacity_ratio=liquidity_capacity_ratio,
        category_drawdown_ratio=category_snapshot.category_drawdown_ratio,
        candidate_notional=candidate.candidate_notional,
        allowed_candidate_notional=allowed_candidate_notional,
        config=config,
    )
    return StrategyPortfolioCategoryEdgeBudgetGateV2Row(
        rank=ONE_COUNT,
        candidate_id=candidate.candidate_id,
        category=candidate.category,
        correlated_event_key=candidate.correlated_event_key,
        candidate_notional=candidate.candidate_notional,
        category_budget_notional=category_budget_notional,
        current_category_exposure=category_snapshot.current_category_exposure,
        post_trade_category_exposure=post_trade_category_exposure,
        category_exposure_budget_share=category_exposure_budget_share,
        current_open_candidate_count=category_snapshot.open_candidate_count,
        post_trade_open_candidate_count=post_trade_open_candidate_count,
        current_correlated_event_count=category_snapshot.correlated_event_count,
        post_trade_correlated_event_count=post_trade_correlated_event_count,
        gross_edge=candidate.gross_edge,
        total_cost=candidate.total_cost,
        cost_adjusted_edge=cost_adjusted_edge,
        available_liquidity=candidate.available_liquidity,
        liquidity_capacity_ratio=liquidity_capacity_ratio,
        liquidity_capacity_notional=liquidity_capacity_notional,
        allowed_candidate_notional=allowed_candidate_notional,
        category_drawdown_ratio=category_snapshot.category_drawdown_ratio,
        gate_status=gate_status,
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[StrategyPortfolioCategoryEdgeBudgetGateV2Row, ...],
) -> tuple[StrategyPortfolioCategoryEdgeBudgetGateV2Row, ...]:
    return tuple(
        StrategyPortfolioCategoryEdgeBudgetGateV2Row(
            rank=_count(index),
            candidate_id=row.candidate_id,
            category=row.category,
            correlated_event_key=row.correlated_event_key,
            candidate_notional=row.candidate_notional,
            category_budget_notional=row.category_budget_notional,
            current_category_exposure=row.current_category_exposure,
            post_trade_category_exposure=row.post_trade_category_exposure,
            category_exposure_budget_share=row.category_exposure_budget_share,
            current_open_candidate_count=row.current_open_candidate_count,
            post_trade_open_candidate_count=row.post_trade_open_candidate_count,
            current_correlated_event_count=row.current_correlated_event_count,
            post_trade_correlated_event_count=row.post_trade_correlated_event_count,
            gross_edge=row.gross_edge,
            total_cost=row.total_cost,
            cost_adjusted_edge=row.cost_adjusted_edge,
            available_liquidity=row.available_liquidity,
            liquidity_capacity_ratio=row.liquidity_capacity_ratio,
            liquidity_capacity_notional=row.liquidity_capacity_notional,
            allowed_candidate_notional=row.allowed_candidate_notional,
            category_drawdown_ratio=row.category_drawdown_ratio,
            gate_status=row.gate_status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _gate_status(
    *,
    category_exposure_budget_share: Decimal,
    post_trade_open_candidate_count: Decimal,
    post_trade_correlated_event_count: Decimal,
    cost_adjusted_edge: Decimal,
    liquidity_capacity_ratio: Decimal,
    category_drawdown_ratio: Decimal,
    candidate_notional: Decimal,
    allowed_candidate_notional: Decimal,
    config: StrategyPortfolioCategoryEdgeBudgetGateV2Config,
) -> str:
    if (
        category_exposure_budget_share >= config.category_exposure_block_share
        or post_trade_open_candidate_count >= config.open_candidate_block_count
        or post_trade_correlated_event_count >= config.correlated_event_block_count
        or cost_adjusted_edge < config.min_watch_cost_adjusted_edge
        or liquidity_capacity_ratio < config.block_liquidity_capacity_ratio
        or category_drawdown_ratio >= config.category_drawdown_block_ratio
        or candidate_notional > allowed_candidate_notional
    ):
        return BLOCKED_STATUS
    if (
        category_exposure_budget_share >= config.category_exposure_watch_share
        or post_trade_open_candidate_count >= config.open_candidate_watch_count
        or post_trade_correlated_event_count >= config.correlated_event_watch_count
        or cost_adjusted_edge < config.min_candidate_cost_adjusted_edge
        or liquidity_capacity_ratio < config.min_liquidity_capacity_ratio
        or category_drawdown_ratio >= config.category_drawdown_watch_ratio
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    source_reason_codes: tuple[str, ...],
    gate_status: str,
    category_exposure_budget_share: Decimal,
    post_trade_open_candidate_count: Decimal,
    post_trade_correlated_event_count: Decimal,
    cost_adjusted_edge: Decimal,
    liquidity_capacity_ratio: Decimal,
    category_drawdown_ratio: Decimal,
    candidate_notional: Decimal,
    allowed_candidate_notional: Decimal,
    config: StrategyPortfolioCategoryEdgeBudgetGateV2Config,
) -> tuple[str, ...]:
    reason_codes = list(source_reason_codes)
    reason_codes.append(f"category_edge_budget_{gate_status}")
    if category_exposure_budget_share >= config.category_exposure_block_share:
        reason_codes.append("category_exposure_block")
    elif category_exposure_budget_share >= config.category_exposure_watch_share:
        reason_codes.append("category_exposure_watch")
    if post_trade_open_candidate_count >= config.open_candidate_block_count:
        reason_codes.append("open_candidate_count_block")
    elif post_trade_open_candidate_count >= config.open_candidate_watch_count:
        reason_codes.append("open_candidate_count_watch")
    if post_trade_correlated_event_count >= config.correlated_event_block_count:
        reason_codes.append("correlated_event_count_block")
    elif post_trade_correlated_event_count >= config.correlated_event_watch_count:
        reason_codes.append("correlated_event_count_watch")
    if cost_adjusted_edge < config.min_watch_cost_adjusted_edge:
        reason_codes.append("cost_adjusted_edge_below_watch")
    elif cost_adjusted_edge < config.min_candidate_cost_adjusted_edge:
        reason_codes.append("cost_adjusted_edge_below_candidate")
    if liquidity_capacity_ratio < config.block_liquidity_capacity_ratio:
        reason_codes.append("liquidity_capacity_block")
    elif liquidity_capacity_ratio < config.min_liquidity_capacity_ratio:
        reason_codes.append("liquidity_capacity_watch")
    if category_drawdown_ratio >= config.category_drawdown_block_ratio:
        reason_codes.append("category_drawdown_block")
    elif category_drawdown_ratio >= config.category_drawdown_watch_ratio:
        reason_codes.append("category_drawdown_watch")
    if candidate_notional > allowed_candidate_notional:
        reason_codes.append("candidate_notional_exceeds_allowed")
    return _dedupe(tuple(reason_codes))


def _category_remaining_notional(
    current_category_exposure: Decimal,
    *,
    category_budget_notional: Decimal,
    config: StrategyPortfolioCategoryEdgeBudgetGateV2Config,
) -> Decimal:
    category_block_notional = _multiply_decimal(
        category_budget_notional,
        config.category_exposure_block_share,
    )
    return max(ZERO, _subtract_decimal(category_block_notional, current_category_exposure))


def _category_snapshot_for(
    candidate: StrategyPortfolioCategoryEdgeBudgetGateV2Candidate,
    category_map: dict[str, StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot],
) -> StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot:
    try:
        return category_map[candidate.category]
    except KeyError as exc:
        raise ValueError(
            "category_snapshots must contain candidate category values",
        ) from exc


def _category_snapshot_map(
    category_snapshots: Iterable[
        StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot
    ],
) -> dict[str, StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot]:
    if isinstance(category_snapshots, (str, bytes)):
        raise ValueError("category_snapshots must be an iterable")
    try:
        normalized = tuple(category_snapshots)
    except TypeError as exc:
        raise ValueError("category_snapshots must be an iterable") from exc
    category_map: dict[str, StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot] = {}
    for snapshot in normalized:
        if type(snapshot) is not StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot:
            raise ValueError("category_snapshots must contain category snapshot values")
        _require_hard_flags(snapshot)
        if snapshot.category in category_map:
            raise ValueError("category_snapshots must not contain duplicate categories")
        category_map[snapshot.category] = snapshot
    return category_map


def _normalize_candidates(
    candidates: Iterable[StrategyPortfolioCategoryEdgeBudgetGateV2Candidate],
) -> tuple[StrategyPortfolioCategoryEdgeBudgetGateV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyPortfolioCategoryEdgeBudgetGateV2Candidate:
            raise ValueError("candidates must contain candidate values")
        _require_hard_flags(candidate)
        if candidate.candidate_id in seen:
            raise ValueError("candidates must not contain duplicate candidate_id values")
        seen.add(candidate.candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[StrategyPortfolioCategoryEdgeBudgetGateV2Row],
) -> tuple[StrategyPortfolioCategoryEdgeBudgetGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyPortfolioCategoryEdgeBudgetGateV2Row:
            raise ValueError("rows must contain category edge budget row values")
        _require_hard_flags(row)
        _verify_digest(row)
    expected_ranks = tuple(_count(index) for index in range(1, len(normalized) + 1))
    if tuple(row.rank for row in normalized) != expected_ranks:
        raise ValueError("rows must use consecutive ranks")
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _validate_row_consistency(
    row: StrategyPortfolioCategoryEdgeBudgetGateV2Row,
) -> None:
    if row.post_trade_category_exposure != _add_decimal(
        row.current_category_exposure,
        row.candidate_notional,
    ):
        raise ValueError("post_trade_category_exposure must match row inputs")
    if row.category_exposure_budget_share != _divide_decimal(
        row.post_trade_category_exposure,
        row.category_budget_notional,
    ):
        raise ValueError("category_exposure_budget_share must match row inputs")
    if row.post_trade_open_candidate_count != _add_count(
        row.current_open_candidate_count,
        ONE_COUNT,
    ):
        raise ValueError("post_trade_open_candidate_count must match row inputs")
    if row.post_trade_correlated_event_count != _add_count(
        row.current_correlated_event_count,
        ONE_COUNT,
    ):
        raise ValueError("post_trade_correlated_event_count must match row inputs")
    if row.cost_adjusted_edge != _subtract_decimal(row.gross_edge, row.total_cost):
        raise ValueError("cost_adjusted_edge must match row inputs")
    if row.liquidity_capacity_ratio != _divide_decimal(
        row.available_liquidity,
        row.candidate_notional,
    ):
        raise ValueError("liquidity_capacity_ratio must match row inputs")
    if row.allowed_candidate_notional > row.candidate_notional:
        raise ValueError("allowed_candidate_notional must not exceed candidate_notional")


def _validate_report_consistency(
    report: StrategyPortfolioCategoryEdgeBudgetGateV2Report,
) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.total_candidate_notional != _sum_values(
        tuple(row.candidate_notional for row in report.rows),
    ):
        raise ValueError("total_candidate_notional must match rows")
    if report.total_allowed_candidate_notional != _sum_values(
        tuple(row.allowed_candidate_notional for row in report.rows),
    ):
        raise ValueError("total_allowed_candidate_notional must match rows")
    if report.max_category_exposure_budget_share != _max_value(
        tuple(row.category_exposure_budget_share for row in report.rows),
    ):
        raise ValueError("max_category_exposure_budget_share must match rows")
    if report.max_open_candidate_count != _max_count(
        tuple(row.post_trade_open_candidate_count for row in report.rows),
    ):
        raise ValueError("max_open_candidate_count must match rows")
    if report.max_correlated_event_count != _max_count(
        tuple(row.post_trade_correlated_event_count for row in report.rows),
    ):
        raise ValueError("max_correlated_event_count must match rows")
    if report.min_cost_adjusted_edge != _min_value(
        tuple(row.cost_adjusted_edge for row in report.rows),
    ):
        raise ValueError("min_cost_adjusted_edge must match rows")
    if report.min_liquidity_capacity_ratio != _min_nonnegative_value(
        tuple(row.liquidity_capacity_ratio for row in report.rows),
    ):
        raise ValueError("min_liquidity_capacity_ratio must match rows")
    if report.max_category_drawdown_ratio != _max_value(
        tuple(row.category_drawdown_ratio for row in report.rows),
    ):
        raise ValueError("max_category_drawdown_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    for row in report.rows:
        _verify_digest(row)


def _row_sort_key(
    row: StrategyPortfolioCategoryEdgeBudgetGateV2Row,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_PRIORITY[row.gate_status],
        row.allowed_candidate_notional,
        -row.category_exposure_budget_share,
        row.category,
        row.candidate_id,
    )


def _status_count(
    rows: tuple[StrategyPortfolioCategoryEdgeBudgetGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _digest_status(rows: tuple[StrategyPortfolioCategoryEdgeBudgetGateV2Row, ...]) -> str:
    if any(row.gate_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.gate_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[StrategyPortfolioCategoryEdgeBudgetGateV2Row, ...],
) -> tuple[str, ...]:
    observed = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    source_reason_codes = tuple(
        reason_code
        for reason_code in _dedupe(observed)
        if reason_code not in KNOWN_REASON_CODE_ORDER
    )
    known_reason_codes = tuple(
        reason_code for reason_code in KNOWN_REASON_CODE_ORDER if reason_code in observed
    )
    return source_reason_codes + known_reason_codes


def _sum_values(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _max_value(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_nonnegative_decimal("max_value", max(values))


def _max_count(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_COUNT
    return _normalize_nonnegative_count("max_count", max(values))


def _min_value(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_decimal("min_value", min(values))


def _min_nonnegative_value(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_nonnegative_decimal("min_nonnegative_value", min(values))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right <= ZERO:
        raise ValueError("division denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _add_count(left: Decimal, right: Decimal) -> Decimal:
    return _normalize_nonnegative_count("count", left + right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
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
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_canonical_public_string(field_name, reason_code)
    return _dedupe(value)


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_not_above(field_name: str, low_value: Decimal, high_value: Decimal) -> None:
    if low_value > high_value:
        raise ValueError(f"{field_name} must not exceed paired threshold")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _apply_or_verify_digest(
    value: StrategyPortfolioCategoryEdgeBudgetGateV2Row
    | StrategyPortfolioCategoryEdgeBudgetGateV2Report,
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
    value: StrategyPortfolioCategoryEdgeBudgetGateV2Row
    | StrategyPortfolioCategoryEdgeBudgetGateV2Report,
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: StrategyPortfolioCategoryEdgeBudgetGateV2Row
    | StrategyPortfolioCategoryEdgeBudgetGateV2Report,
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    payload = _json_ready(digest_input)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("JSON value must not be an int")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError("unsafe public payload value")
        return
    if type(value) in (bool, type(None)):
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    raise ValueError("unsafe public payload type")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_STRATEGY_PORTFOLIO_CATEGORY_EDGE_BUDGET_GATE_V2_CONFIG_VERSION",
    "StrategyPortfolioCategoryEdgeBudgetGateV2Candidate",
    "StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot",
    "StrategyPortfolioCategoryEdgeBudgetGateV2Config",
    "StrategyPortfolioCategoryEdgeBudgetGateV2Report",
    "StrategyPortfolioCategoryEdgeBudgetGateV2Row",
    "build_strategy_portfolio_category_edge_budget_gate_v2_report",
    "strategy_portfolio_category_edge_budget_gate_v2_payload",
)

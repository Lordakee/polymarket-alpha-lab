"""Paper-only analytics derived from paper portfolio and NAV artifacts."""

import json
from collections import defaultdict
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from pathlib import Path
from typing import Any, Iterator

from polymarket_alpha_lab.positions import (
    PaperNavSnapshot,
    PaperPortfolio,
    PaperPosition,
    PaperPositionMark,
)

__all__ = [
    "PaperAnalyticsBreach",
    "PaperAnalyticsBucket",
    "PaperAnalyticsConfig",
    "PaperAnalyticsLog",
    "PaperAnalyticsReport",
    "PaperDrawdownPoint",
    "PaperPerformanceSummary",
    "PaperPositionExposure",
    "build_paper_analytics_report",
    "build_paper_drawdown_points",
]


RATIO_QUANTUM = Decimal("0.0001")
MARK_STATUSES = frozenset(
    {
        "fully_executable",
        "partially_executable",
        "no_exit_depth",
    }
)
PORTFOLIO_MARK_STATUSES = frozenset(
    {
        "no_open_positions",
        "fully_executable",
        "partially_executable",
        "no_exit_depth",
    }
)
BUCKET_TYPES = frozenset(
    {
        "token_id",
        "condition_id",
        "market_slug",
        "strategy_type",
        "risk_tag",
        "resolution_source",
        "mark_status",
    }
)
BREACH_CODES = frozenset(
    {
        "open_cost_basis_limit",
        "single_position_cost_basis_limit",
        "strategy_cost_basis_limit",
        "market_cost_basis_limit",
        "risk_tag_cost_basis_limit",
        "no_exit_depth_limit",
        "low_cash_ratio",
    }
)


@dataclass(frozen=True)
class PaperAnalyticsConfig:
    config_version: str
    max_open_cost_basis_ratio: Decimal = Decimal("1.00")
    max_single_position_cost_basis_ratio: Decimal = Decimal("0.25")
    max_strategy_cost_basis_ratio: Decimal = Decimal("0.50")
    max_market_cost_basis_ratio: Decimal = Decimal("0.50")
    max_risk_tag_cost_basis_ratio: Decimal = Decimal("0.50")
    max_no_exit_depth_cost_basis_ratio: Decimal = Decimal("0.10")
    min_cash_ratio: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_open_cost_basis_ratio",
            "max_single_position_cost_basis_ratio",
            "max_strategy_cost_basis_ratio",
            "max_market_cost_basis_ratio",
            "max_risk_tag_cost_basis_ratio",
            "max_no_exit_depth_cost_basis_ratio",
            "min_cash_ratio",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class PaperAnalyticsBreach:
    code: str
    message: str
    field_name: str
    observed_value: Decimal | str | None = None
    threshold: Decimal | str | None = None

    def __post_init__(self) -> None:
        if self.code not in BREACH_CODES:
            raise ValueError("code must be a known analytics breach code")
        _require_canonical_string("message", self.message)
        _require_canonical_string("field_name", self.field_name)
        _require_breach_value("observed_value", self.observed_value)
        _require_breach_value("threshold", self.threshold)


@dataclass(frozen=True)
class PaperPerformanceSummary:
    starting_cash: Decimal
    cash_balance: Decimal
    realized_pnl: Decimal
    unrealized_exit_pnl: Decimal
    total_exit_pnl: Decimal
    exit_nav: Decimal
    midpoint_nav: Decimal | None
    total_cost_basis: Decimal
    exit_return_ratio: Decimal
    realized_return_ratio: Decimal
    unrealized_exit_return_ratio: Decimal
    cash_ratio: Decimal
    open_cost_basis_ratio: Decimal
    midpoint_nav_gap: Decimal | None
    midpoint_nav_gap_ratio: Decimal | None

    def __post_init__(self) -> None:
        _require_positive_decimal("starting_cash", self.starting_cash)
        _require_nonnegative_decimal("cash_balance", self.cash_balance)
        _require_finite_decimal("realized_pnl", self.realized_pnl)
        _require_finite_decimal("unrealized_exit_pnl", self.unrealized_exit_pnl)
        _require_finite_decimal("total_exit_pnl", self.total_exit_pnl)
        _require_nonnegative_decimal("exit_nav", self.exit_nav)
        _require_optional_nonnegative_decimal("midpoint_nav", self.midpoint_nav)
        _require_nonnegative_decimal("total_cost_basis", self.total_cost_basis)
        for field_name in (
            "exit_return_ratio",
            "realized_return_ratio",
            "unrealized_exit_return_ratio",
            "cash_ratio",
            "open_cost_basis_ratio",
        ):
            _require_finite_decimal(field_name, getattr(self, field_name))
        _require_optional_finite_decimal("midpoint_nav_gap", self.midpoint_nav_gap)
        _require_optional_finite_decimal("midpoint_nav_gap_ratio", self.midpoint_nav_gap_ratio)
        if _add(self.realized_pnl, self.unrealized_exit_pnl) != self.total_exit_pnl:
            raise ValueError("total_exit_pnl must equal realized plus unrealized exit PnL")
        if self.midpoint_nav is None:
            if self.midpoint_nav_gap is not None or self.midpoint_nav_gap_ratio is not None:
                raise ValueError("midpoint gap fields must be absent without midpoint_nav")
        elif self.midpoint_nav_gap is None:
            raise ValueError("midpoint_nav_gap is required when midpoint_nav is present")


@dataclass(frozen=True)
class PaperPositionExposure:
    source_packet_ids: tuple[str, ...]
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    risk_tags: tuple[str, ...]
    rule_text_hash: str
    resolution_source: str
    market_raw_archive_path: str
    last_order_book_raw_archive_path: str
    last_order_book_raw_payload_sha256: str
    last_order_book_snapshot_sha256: str
    opened_at: datetime
    updated_at: datetime
    open_size: Decimal
    cost_basis: Decimal
    average_entry_price: Decimal
    realized_pnl: Decimal
    entry_trade_count: int
    exit_trade_count: int
    max_loss_to_zero: Decimal
    max_profit_to_one: Decimal
    exit_value: Decimal
    midpoint_value: Decimal | None
    unrealized_exit_pnl: Decimal
    exit_filled_size: Decimal
    exit_unfilled_size: Decimal
    exit_coverage_ratio: Decimal
    exit_shortfall_ratio: Decimal
    cost_basis_ratio_to_starting_cash: Decimal
    cost_basis_ratio_to_total_open_basis: Decimal | None
    exit_value_ratio_to_exit_nav: Decimal | None
    mark_status: str
    order_book_captured_at: datetime
    order_book_snapshot_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_packet_ids",
            _normalize_string_tuple("source_packet_ids", self.source_packet_ids),
        )
        object.__setattr__(
            self,
            "risk_tags",
            _normalize_string_tuple("risk_tags", self.risk_tags),
        )
        object.__setattr__(self, "opened_at", _as_utc(self.opened_at))
        object.__setattr__(self, "updated_at", _as_utc(self.updated_at))
        object.__setattr__(
            self,
            "order_book_captured_at",
            _as_utc(self.order_book_captured_at),
        )

        if not self.source_packet_ids:
            raise ValueError("source_packet_ids must not be empty")
        for field_name in (
            "condition_id",
            "token_id",
            "market_slug",
            "market_url",
            "question",
            "outcome_name",
            "strategy_type",
            "rule_text_hash",
            "resolution_source",
            "market_raw_archive_path",
            "last_order_book_raw_archive_path",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_sha256(
            "last_order_book_raw_payload_sha256",
            self.last_order_book_raw_payload_sha256,
        )
        _require_sha256("last_order_book_snapshot_sha256", self.last_order_book_snapshot_sha256)
        _require_sha256("order_book_snapshot_sha256", self.order_book_snapshot_sha256)
        if self.opened_at > self.updated_at:
            raise ValueError("opened_at must not be after updated_at")
        _require_positive_decimal("open_size", self.open_size)
        _require_nonnegative_decimal("cost_basis", self.cost_basis)
        if self.cost_basis > self.open_size:
            raise ValueError("cost_basis must not exceed open_size")
        _require_price_domain("average_entry_price", self.average_entry_price)
        _require_finite_decimal("realized_pnl", self.realized_pnl)
        _require_positive_int("entry_trade_count", self.entry_trade_count)
        _require_nonnegative_int("exit_trade_count", self.exit_trade_count)
        _require_nonnegative_decimal("max_loss_to_zero", self.max_loss_to_zero)
        _require_nonnegative_decimal("max_profit_to_one", self.max_profit_to_one)
        _require_nonnegative_decimal("exit_value", self.exit_value)
        _require_optional_nonnegative_decimal("midpoint_value", self.midpoint_value)
        _require_finite_decimal("unrealized_exit_pnl", self.unrealized_exit_pnl)
        _require_nonnegative_decimal("exit_filled_size", self.exit_filled_size)
        _require_nonnegative_decimal("exit_unfilled_size", self.exit_unfilled_size)
        if _add(self.exit_filled_size, self.exit_unfilled_size) != self.open_size:
            raise ValueError("exit_filled_size plus exit_unfilled_size must equal open_size")
        for field_name in (
            "exit_coverage_ratio",
            "exit_shortfall_ratio",
            "cost_basis_ratio_to_starting_cash",
        ):
            _require_finite_decimal(field_name, getattr(self, field_name))
        _require_optional_finite_decimal(
            "cost_basis_ratio_to_total_open_basis",
            self.cost_basis_ratio_to_total_open_basis,
        )
        _require_optional_finite_decimal(
            "exit_value_ratio_to_exit_nav",
            self.exit_value_ratio_to_exit_nav,
        )
        if self.mark_status not in MARK_STATUSES:
            raise ValueError("mark_status must be a known mark status")


@dataclass(frozen=True)
class PaperAnalyticsBucket:
    bucket_type: str
    bucket_value: str
    additive: bool
    position_count: int
    token_ids: tuple[str, ...]
    open_size: Decimal
    cost_basis: Decimal
    max_loss_to_zero: Decimal
    exit_value: Decimal
    unrealized_exit_pnl: Decimal
    exit_unfilled_size: Decimal
    cost_basis_ratio_to_starting_cash: Decimal
    cost_basis_ratio_to_total_open_basis: Decimal | None
    exit_value_ratio_to_exit_nav: Decimal | None

    def __post_init__(self) -> None:
        if self.bucket_type not in BUCKET_TYPES:
            raise ValueError("bucket_type must be a known analytics bucket type")
        _require_canonical_string("bucket_value", self.bucket_value)
        _require_bool("additive", self.additive)
        if self.bucket_type == "risk_tag" and self.additive is not False:
            raise ValueError("risk_tag buckets must be non-additive")
        if self.bucket_type != "risk_tag" and self.additive is not True:
            raise ValueError("non-risk_tag buckets must be additive")
        _require_positive_int("position_count", self.position_count)
        object.__setattr__(
            self,
            "token_ids",
            _normalize_unique_string_tuple("token_ids", self.token_ids),
        )
        for field_name in (
            "open_size",
            "cost_basis",
            "max_loss_to_zero",
            "exit_value",
            "exit_unfilled_size",
            "cost_basis_ratio_to_starting_cash",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_finite_decimal("unrealized_exit_pnl", self.unrealized_exit_pnl)
        _require_optional_finite_decimal(
            "cost_basis_ratio_to_total_open_basis",
            self.cost_basis_ratio_to_total_open_basis,
        )
        _require_optional_finite_decimal(
            "exit_value_ratio_to_exit_nav",
            self.exit_value_ratio_to_exit_nav,
        )


@dataclass(frozen=True)
class PaperDrawdownPoint:
    marked_at: datetime
    exit_nav: Decimal
    high_watermark_nav: Decimal
    drawdown: Decimal
    drawdown_ratio: Decimal | None
    is_new_high: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "marked_at", _as_utc(self.marked_at))
        _require_nonnegative_decimal("exit_nav", self.exit_nav)
        _require_nonnegative_decimal("high_watermark_nav", self.high_watermark_nav)
        _require_nonnegative_decimal("drawdown", self.drawdown)
        _require_optional_finite_decimal("drawdown_ratio", self.drawdown_ratio)
        _require_bool("is_new_high", self.is_new_high)
        if _subtract(self.high_watermark_nav, self.exit_nav) != self.drawdown:
            raise ValueError("drawdown must equal high_watermark_nav minus exit_nav")
        if self.high_watermark_nav == 0:
            if self.drawdown_ratio is not None:
                raise ValueError("drawdown_ratio must be absent when high_watermark_nav is zero")
        elif self.drawdown_ratio is None:
            raise ValueError("drawdown_ratio is required when high_watermark_nav is positive")


@dataclass(frozen=True)
class PaperAnalyticsReport:
    generated_at: datetime
    config_version: str
    marked_at: datetime
    performance: PaperPerformanceSummary
    position_count: int
    portfolio_mark_status: str
    exit_depth_coverage_ratio: Decimal | None
    exit_depth_shortfall_ratio: Decimal | None
    no_exit_depth_cost_basis_ratio: Decimal | None
    oldest_order_book_captured_at: datetime | None
    newest_order_book_captured_at: datetime | None
    position_exposures: tuple[PaperPositionExposure, ...]
    buckets: tuple[PaperAnalyticsBucket, ...]
    drawdown_points: tuple[PaperDrawdownPoint, ...]
    breaches: tuple[PaperAnalyticsBreach, ...]
    paper_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(self, "marked_at", _as_utc(self.marked_at))
        _require_canonical_string("config_version", self.config_version)
        if not isinstance(self.performance, PaperPerformanceSummary):
            raise ValueError("performance must be a PaperPerformanceSummary")
        _require_nonnegative_int("position_count", self.position_count)
        if self.portfolio_mark_status not in PORTFOLIO_MARK_STATUSES:
            raise ValueError("portfolio_mark_status must be a known status")
        _require_optional_finite_decimal(
            "exit_depth_coverage_ratio",
            self.exit_depth_coverage_ratio,
        )
        _require_optional_finite_decimal(
            "exit_depth_shortfall_ratio",
            self.exit_depth_shortfall_ratio,
        )
        _require_optional_finite_decimal(
            "no_exit_depth_cost_basis_ratio",
            self.no_exit_depth_cost_basis_ratio,
        )
        object.__setattr__(
            self,
            "position_exposures",
            _normalize_typed_tuple(
                "position_exposures",
                self.position_exposures,
                PaperPositionExposure,
            ),
        )
        object.__setattr__(
            self,
            "buckets",
            _normalize_typed_tuple("buckets", self.buckets, PaperAnalyticsBucket),
        )
        object.__setattr__(
            self,
            "drawdown_points",
            _normalize_typed_tuple("drawdown_points", self.drawdown_points, PaperDrawdownPoint),
        )
        object.__setattr__(
            self,
            "breaches",
            _normalize_typed_tuple("breaches", self.breaches, PaperAnalyticsBreach),
        )
        if self.position_count != len(self.position_exposures):
            raise ValueError("position_count must equal position_exposures length")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.position_exposures:
            if self.oldest_order_book_captured_at is None:
                raise ValueError("oldest_order_book_captured_at is required")
            if self.newest_order_book_captured_at is None:
                raise ValueError("newest_order_book_captured_at is required")
            object.__setattr__(
                self,
                "oldest_order_book_captured_at",
                _as_utc(self.oldest_order_book_captured_at),
            )
            object.__setattr__(
                self,
                "newest_order_book_captured_at",
                _as_utc(self.newest_order_book_captured_at),
            )
            if self.oldest_order_book_captured_at > self.newest_order_book_captured_at:
                raise ValueError("oldest_order_book_captured_at must not be after newest")
        else:
            if self.oldest_order_book_captured_at is not None:
                raise ValueError("oldest_order_book_captured_at must be absent")
            if self.newest_order_book_captured_at is not None:
                raise ValueError("newest_order_book_captured_at must be absent")


@dataclass(frozen=True)
class PaperAnalyticsLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: PaperAnalyticsReport) -> None:
        if not isinstance(report, PaperAnalyticsReport):
            raise ValueError("report must be a PaperAnalyticsReport")
        _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_paper_analytics_report(
    portfolio: PaperPortfolio,
    snapshot: PaperNavSnapshot,
    *,
    config: PaperAnalyticsConfig,
    generated_at: datetime,
    drawdown_snapshots: Iterable[PaperNavSnapshot] = (),
) -> PaperAnalyticsReport:
    if not isinstance(portfolio, PaperPortfolio):
        raise ValueError("portfolio must be a PaperPortfolio")
    if not isinstance(snapshot, PaperNavSnapshot):
        raise ValueError("snapshot must be a PaperNavSnapshot")
    if not isinstance(config, PaperAnalyticsConfig):
        raise ValueError("config must be a PaperAnalyticsConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    if isinstance(drawdown_snapshots, (str, bytes)):
        raise ValueError("drawdown_snapshots must be an iterable of PaperNavSnapshot values")

    _validate_portfolio_snapshot_pair(portfolio, snapshot)
    starting_cash = portfolio.starting_cash
    _require_positive_decimal("starting_cash", starting_cash)
    _require_positive_decimal("snapshot starting_cash", snapshot.starting_cash)

    position_by_token = _items_by_token(portfolio.positions, "portfolio positions")
    mark_by_token = _items_by_token(snapshot.marks, "snapshot marks")
    exposures = tuple(
        _build_position_exposure(
            position,
            mark_by_token[position.token_id],
            starting_cash=starting_cash,
            total_cost_basis=snapshot.total_cost_basis,
            exit_nav=snapshot.exit_nav,
        )
        for position in position_by_token.values()
    )
    buckets = _build_buckets(
        exposures,
        starting_cash=starting_cash,
        total_cost_basis=snapshot.total_cost_basis,
        exit_nav=snapshot.exit_nav,
    )
    performance = _build_performance(portfolio, snapshot)
    portfolio_mark_status = _portfolio_mark_status(exposures)
    exit_depth_coverage_ratio, exit_depth_shortfall_ratio = _depth_ratios(exposures)
    no_exit_depth_cost_basis_ratio = _no_exit_depth_cost_basis_ratio(
        exposures,
        starting_cash=starting_cash,
    )
    if exposures:
        captured_values = tuple(exposure.order_book_captured_at for exposure in exposures)
        oldest_order_book_captured_at = min(captured_values)
        newest_order_book_captured_at = max(captured_values)
    else:
        oldest_order_book_captured_at = None
        newest_order_book_captured_at = None

    try:
        drawdown_items = tuple(drawdown_snapshots)
    except TypeError as exc:
        raise ValueError("drawdown_snapshots must be an iterable of PaperNavSnapshot values") from exc
    drawdown_points = build_paper_drawdown_points(drawdown_items or (snapshot,))
    breaches = _build_breaches(
        config,
        performance=performance,
        exposures=exposures,
        buckets=buckets,
        no_exit_depth_cost_basis_ratio=no_exit_depth_cost_basis_ratio,
    )

    return PaperAnalyticsReport(
        generated_at=generated_at,
        config_version=config.config_version,
        marked_at=snapshot.marked_at,
        performance=performance,
        position_count=len(exposures),
        portfolio_mark_status=portfolio_mark_status,
        exit_depth_coverage_ratio=exit_depth_coverage_ratio,
        exit_depth_shortfall_ratio=exit_depth_shortfall_ratio,
        no_exit_depth_cost_basis_ratio=no_exit_depth_cost_basis_ratio,
        oldest_order_book_captured_at=oldest_order_book_captured_at,
        newest_order_book_captured_at=newest_order_book_captured_at,
        position_exposures=exposures,
        buckets=buckets,
        drawdown_points=drawdown_points,
        breaches=breaches,
    )


def build_paper_drawdown_points(
    snapshots: Iterable[PaperNavSnapshot],
) -> tuple[PaperDrawdownPoint, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable of PaperNavSnapshot values")
    try:
        snapshot_items = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable of PaperNavSnapshot values") from exc
    for snapshot in snapshot_items:
        if not isinstance(snapshot, PaperNavSnapshot):
            raise ValueError("snapshots must contain PaperNavSnapshot values")

    sorted_items = tuple(sorted(snapshot_items, key=lambda item: item.marked_at))
    seen_marked_at: set[datetime] = set()
    points: list[PaperDrawdownPoint] = []
    high_watermark_nav: Decimal | None = None
    for snapshot in sorted_items:
        marked_at = _as_utc(snapshot.marked_at)
        if marked_at in seen_marked_at:
            raise ValueError("duplicate marked_at values are not allowed")
        seen_marked_at.add(marked_at)
        if high_watermark_nav is None or snapshot.exit_nav >= high_watermark_nav:
            high_watermark_nav = snapshot.exit_nav
            is_new_high = True
        else:
            is_new_high = False
        drawdown = _subtract(high_watermark_nav, snapshot.exit_nav)
        points.append(
            PaperDrawdownPoint(
                marked_at=marked_at,
                exit_nav=snapshot.exit_nav,
                high_watermark_nav=high_watermark_nav,
                drawdown=drawdown,
                drawdown_ratio=_ratio_or_none(drawdown, high_watermark_nav),
                is_new_high=is_new_high,
            )
        )
    return tuple(points)


def _build_performance(
    portfolio: PaperPortfolio,
    snapshot: PaperNavSnapshot,
) -> PaperPerformanceSummary:
    starting_cash = portfolio.starting_cash
    total_exit_pnl = _add(portfolio.realized_pnl, snapshot.unrealized_exit_pnl)
    exit_nav_delta = _subtract(snapshot.exit_nav, starting_cash)
    if snapshot.midpoint_nav is None:
        midpoint_nav_gap = None
        midpoint_nav_gap_ratio = None
    else:
        midpoint_nav_gap = _subtract(snapshot.midpoint_nav, snapshot.exit_nav)
        midpoint_nav_gap_ratio = _ratio_or_none(midpoint_nav_gap, snapshot.midpoint_nav)
    return PaperPerformanceSummary(
        starting_cash=starting_cash,
        cash_balance=portfolio.cash_balance,
        realized_pnl=portfolio.realized_pnl,
        unrealized_exit_pnl=snapshot.unrealized_exit_pnl,
        total_exit_pnl=total_exit_pnl,
        exit_nav=snapshot.exit_nav,
        midpoint_nav=snapshot.midpoint_nav,
        total_cost_basis=snapshot.total_cost_basis,
        exit_return_ratio=_ratio_or_none(exit_nav_delta, starting_cash),
        realized_return_ratio=_ratio_or_none(portfolio.realized_pnl, starting_cash),
        unrealized_exit_return_ratio=_ratio_or_none(snapshot.unrealized_exit_pnl, starting_cash),
        cash_ratio=_ratio_or_none(portfolio.cash_balance, starting_cash),
        open_cost_basis_ratio=_ratio_or_none(snapshot.total_cost_basis, starting_cash),
        midpoint_nav_gap=midpoint_nav_gap,
        midpoint_nav_gap_ratio=midpoint_nav_gap_ratio,
    )


def _build_position_exposure(
    position: PaperPosition,
    mark: PaperPositionMark,
    *,
    starting_cash: Decimal,
    total_cost_basis: Decimal,
    exit_nav: Decimal,
) -> PaperPositionExposure:
    unrealized_exit_pnl = _subtract(mark.exit_value, position.cost_basis)
    return PaperPositionExposure(
        source_packet_ids=position.source_packet_ids,
        condition_id=position.condition_id,
        token_id=position.token_id,
        market_slug=position.market_slug,
        market_url=position.market_url,
        question=position.question,
        outcome_name=position.outcome_name,
        strategy_type=position.strategy_type,
        risk_tags=position.risk_tags,
        rule_text_hash=position.rule_text_hash,
        resolution_source=position.resolution_source,
        market_raw_archive_path=position.market_raw_archive_path,
        last_order_book_raw_archive_path=position.last_order_book_raw_archive_path,
        last_order_book_raw_payload_sha256=position.last_order_book_raw_payload_sha256,
        last_order_book_snapshot_sha256=position.last_order_book_snapshot_sha256,
        opened_at=position.opened_at,
        updated_at=position.updated_at,
        open_size=position.open_size,
        cost_basis=position.cost_basis,
        average_entry_price=position.average_entry_price,
        realized_pnl=position.realized_pnl,
        entry_trade_count=position.entry_trade_count,
        exit_trade_count=position.exit_trade_count,
        max_loss_to_zero=position.cost_basis,
        max_profit_to_one=_subtract(position.open_size, position.cost_basis),
        exit_value=mark.exit_value,
        midpoint_value=mark.midpoint_value,
        unrealized_exit_pnl=unrealized_exit_pnl,
        exit_filled_size=mark.exit_filled_size,
        exit_unfilled_size=mark.exit_unfilled_size,
        exit_coverage_ratio=_ratio_or_none(mark.exit_filled_size, position.open_size),
        exit_shortfall_ratio=_ratio_or_none(mark.exit_unfilled_size, position.open_size),
        cost_basis_ratio_to_starting_cash=_ratio_or_none(position.cost_basis, starting_cash),
        cost_basis_ratio_to_total_open_basis=_ratio_or_none(position.cost_basis, total_cost_basis),
        exit_value_ratio_to_exit_nav=_ratio_or_none(mark.exit_value, exit_nav),
        mark_status=mark.mark_status,
        order_book_captured_at=mark.order_book_captured_at,
        order_book_snapshot_sha256=mark.order_book_snapshot_sha256,
    )


def _build_buckets(
    exposures: tuple[PaperPositionExposure, ...],
    *,
    starting_cash: Decimal,
    total_cost_basis: Decimal,
    exit_nav: Decimal,
) -> tuple[PaperAnalyticsBucket, ...]:
    grouped: dict[tuple[str, str], list[PaperPositionExposure]] = defaultdict(list)
    for exposure in exposures:
        grouped[("token_id", exposure.token_id)].append(exposure)
        grouped[("condition_id", exposure.condition_id)].append(exposure)
        grouped[("market_slug", exposure.market_slug)].append(exposure)
        grouped[("strategy_type", exposure.strategy_type)].append(exposure)
        grouped[("resolution_source", exposure.resolution_source)].append(exposure)
        grouped[("mark_status", exposure.mark_status)].append(exposure)
        for risk_tag in exposure.risk_tags:
            grouped[("risk_tag", risk_tag)].append(exposure)

    buckets: list[PaperAnalyticsBucket] = []
    for (bucket_type, bucket_value), rows in grouped.items():
        row_tuple = tuple(rows)
        open_size = _exact_sum(row.open_size for row in row_tuple)
        cost_basis = _exact_sum(row.cost_basis for row in row_tuple)
        max_loss_to_zero = _exact_sum(row.max_loss_to_zero for row in row_tuple)
        exit_value = _exact_sum(row.exit_value for row in row_tuple)
        unrealized_exit_pnl = _exact_sum(row.unrealized_exit_pnl for row in row_tuple)
        exit_unfilled_size = _exact_sum(row.exit_unfilled_size for row in row_tuple)
        buckets.append(
            PaperAnalyticsBucket(
                bucket_type=bucket_type,
                bucket_value=bucket_value,
                additive=bucket_type != "risk_tag",
                position_count=len(row_tuple),
                token_ids=_ordered_unique_strings(row.token_id for row in row_tuple),
                open_size=open_size,
                cost_basis=cost_basis,
                max_loss_to_zero=max_loss_to_zero,
                exit_value=exit_value,
                unrealized_exit_pnl=unrealized_exit_pnl,
                exit_unfilled_size=exit_unfilled_size,
                cost_basis_ratio_to_starting_cash=_ratio_or_none(cost_basis, starting_cash),
                cost_basis_ratio_to_total_open_basis=_ratio_or_none(cost_basis, total_cost_basis),
                exit_value_ratio_to_exit_nav=_ratio_or_none(exit_value, exit_nav),
            )
        )
    return tuple(sorted(buckets, key=lambda bucket: (bucket.bucket_type, bucket.bucket_value)))


def _build_breaches(
    config: PaperAnalyticsConfig,
    *,
    performance: PaperPerformanceSummary,
    exposures: tuple[PaperPositionExposure, ...],
    buckets: tuple[PaperAnalyticsBucket, ...],
    no_exit_depth_cost_basis_ratio: Decimal | None,
) -> tuple[PaperAnalyticsBreach, ...]:
    breaches: list[PaperAnalyticsBreach] = []
    if performance.open_cost_basis_ratio > config.max_open_cost_basis_ratio:
        breaches.append(
            _breach(
                "open_cost_basis_limit",
                "Open cost basis exceeds configured limit.",
                "performance.open_cost_basis_ratio",
                performance.open_cost_basis_ratio,
                config.max_open_cost_basis_ratio,
            )
        )
    for exposure in exposures:
        if exposure.cost_basis_ratio_to_starting_cash > config.max_single_position_cost_basis_ratio:
            breaches.append(
                _breach(
                    "single_position_cost_basis_limit",
                    "Position cost basis exceeds configured limit.",
                    f"position:{exposure.token_id}",
                    exposure.cost_basis_ratio_to_starting_cash,
                    config.max_single_position_cost_basis_ratio,
                )
            )
    for bucket in _buckets_of_type(buckets, "strategy_type"):
        if bucket.cost_basis_ratio_to_starting_cash > config.max_strategy_cost_basis_ratio:
            breaches.append(
                _breach(
                    "strategy_cost_basis_limit",
                    "Strategy cost basis exceeds configured limit.",
                    f"strategy_type:{bucket.bucket_value}",
                    bucket.cost_basis_ratio_to_starting_cash,
                    config.max_strategy_cost_basis_ratio,
                )
            )
    for bucket in _buckets_of_type(buckets, "market_slug"):
        if bucket.cost_basis_ratio_to_starting_cash > config.max_market_cost_basis_ratio:
            breaches.append(
                _breach(
                    "market_cost_basis_limit",
                    "Market cost basis exceeds configured limit.",
                    f"market_slug:{bucket.bucket_value}",
                    bucket.cost_basis_ratio_to_starting_cash,
                    config.max_market_cost_basis_ratio,
                )
            )
    for bucket in _buckets_of_type(buckets, "risk_tag"):
        if bucket.cost_basis_ratio_to_starting_cash > config.max_risk_tag_cost_basis_ratio:
            breaches.append(
                _breach(
                    "risk_tag_cost_basis_limit",
                    "Risk tag cost basis exceeds configured limit.",
                    f"risk_tag:{bucket.bucket_value}",
                    bucket.cost_basis_ratio_to_starting_cash,
                    config.max_risk_tag_cost_basis_ratio,
                )
            )
    if (
        no_exit_depth_cost_basis_ratio is not None
        and no_exit_depth_cost_basis_ratio > config.max_no_exit_depth_cost_basis_ratio
    ):
        breaches.append(
            _breach(
                "no_exit_depth_limit",
                "No-depth cost basis exceeds configured limit.",
                "no_exit_depth_cost_basis_ratio",
                no_exit_depth_cost_basis_ratio,
                config.max_no_exit_depth_cost_basis_ratio,
            )
        )
    if performance.cash_ratio < config.min_cash_ratio:
        breaches.append(
            _breach(
                "low_cash_ratio",
                "Cash ratio is below configured minimum.",
                "performance.cash_ratio",
                performance.cash_ratio,
                config.min_cash_ratio,
            )
        )
    return tuple(breaches)


def _breach(
    code: str,
    message: str,
    field_name: str,
    observed_value: Decimal,
    threshold: Decimal,
) -> PaperAnalyticsBreach:
    return PaperAnalyticsBreach(
        code=code,
        message=message,
        field_name=field_name,
        observed_value=observed_value,
        threshold=threshold,
    )


def _buckets_of_type(
    buckets: tuple[PaperAnalyticsBucket, ...],
    bucket_type: str,
) -> tuple[PaperAnalyticsBucket, ...]:
    return tuple(bucket for bucket in buckets if bucket.bucket_type == bucket_type)


def _portfolio_mark_status(exposures: tuple[PaperPositionExposure, ...]) -> str:
    if not exposures:
        return "no_open_positions"
    if all(exposure.mark_status == "fully_executable" for exposure in exposures):
        return "fully_executable"
    if all(exposure.mark_status == "no_exit_depth" for exposure in exposures):
        return "no_exit_depth"
    return "partially_executable"


def _depth_ratios(
    exposures: tuple[PaperPositionExposure, ...],
) -> tuple[Decimal | None, Decimal | None]:
    if not exposures:
        return None, None
    total_open_size = _exact_sum(exposure.open_size for exposure in exposures)
    total_filled_size = _exact_sum(exposure.exit_filled_size for exposure in exposures)
    total_unfilled_size = _exact_sum(exposure.exit_unfilled_size for exposure in exposures)
    return (
        _ratio_or_none(total_filled_size, total_open_size),
        _ratio_or_none(total_unfilled_size, total_open_size),
    )


def _no_exit_depth_cost_basis_ratio(
    exposures: tuple[PaperPositionExposure, ...],
    *,
    starting_cash: Decimal,
) -> Decimal | None:
    if not exposures:
        return None
    no_depth_cost_basis = _exact_sum(
        exposure.cost_basis for exposure in exposures if exposure.mark_status == "no_exit_depth"
    )
    return _ratio_or_none(no_depth_cost_basis, starting_cash)


def _validate_portfolio_snapshot_pair(
    portfolio: PaperPortfolio,
    snapshot: PaperNavSnapshot,
) -> None:
    if snapshot.paper_only is not True:
        raise ValueError("snapshot paper_only must be True")
    if portfolio.starting_cash != snapshot.starting_cash:
        raise ValueError("starting_cash must match between portfolio and snapshot")
    if portfolio.cash_balance != snapshot.cash_balance:
        raise ValueError("cash_balance must match between portfolio and snapshot")
    if portfolio.realized_pnl != snapshot.realized_pnl:
        raise ValueError("realized_pnl must match between portfolio and snapshot")
    position_by_token = _items_by_token(portfolio.positions, "portfolio positions")
    mark_by_token = _items_by_token(snapshot.marks, "snapshot marks")
    if set(position_by_token) != set(mark_by_token):
        raise ValueError("token ids must match between portfolio and snapshot")
    for token_id, position in position_by_token.items():
        mark = mark_by_token[token_id]
        for field_name in (
            "condition_id",
            "market_slug",
            "outcome_name",
            "open_size",
            "cost_basis",
            "average_entry_price",
        ):
            if getattr(position, field_name) != getattr(mark, field_name):
                raise ValueError(f"{field_name} must match between position and mark")


def _items_by_token(
    values: Iterable[PaperPosition] | Iterable[PaperPositionMark],
    field_name: str,
) -> dict[str, PaperPosition | PaperPositionMark]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    items = tuple(values)
    by_token: dict[str, PaperPosition | PaperPositionMark] = {}
    for item in items:
        if not isinstance(item, (PaperPosition, PaperPositionMark)):
            raise ValueError(f"{field_name} must contain paper position values")
        _require_canonical_string("token_id", item.token_id)
        if item.token_id in by_token:
            raise ValueError("token ids must be unique")
        by_token[item.token_id] = item
    return by_token


def _validate_report_tree(report: PaperAnalyticsReport) -> None:
    report.performance.__post_init__()
    for exposure in report.position_exposures:
        exposure.__post_init__()
    for bucket in report.buckets:
        bucket.__post_init__()
    for point in report.drawdown_points:
        point.__post_init__()
    for breach in report.breaches:
        breach.__post_init__()
    report.__post_init__()


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime values are required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a sequence of strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_unique_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    items = _normalize_string_tuple(field_name, value)
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must contain unique strings")
    return items


def _normalize_typed_tuple(
    field_name: str,
    value: Iterable[Any],
    item_type: type[Any],
) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a sequence") from exc
    for item in items:
        if not isinstance(item, item_type):
            raise ValueError(f"{field_name} contains invalid values")
    return items


def _ordered_unique_strings(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        _require_canonical_string("token_id", value)
        if value not in seen:
            seen.add(value)
            items.append(value)
    return tuple(items)


def _require_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")


def _require_canonical_string(field_name: str, value: str) -> None:
    _require_string(field_name, value)
    if not value.strip():
        raise ValueError(f"{field_name} is required")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a finite Decimal")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _require_price_domain(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be in [0, 1]")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: int) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_bool(field_name: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a bool")


def _require_breach_value(field_name: str, value: Decimal | str | None) -> None:
    if value is None:
        return
    if isinstance(value, Decimal):
        _require_finite_decimal(field_name, value)
        return
    if isinstance(value, str):
        _require_canonical_string(field_name, value)
        return
    raise ValueError(f"{field_name} must be a finite Decimal, string, or None")


def _is_sha256(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_sha256(field_name: str, value: str) -> None:
    if not _is_sha256(value):
        raise ValueError(f"{field_name} must be a lowercase 64-character SHA-256 digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("analytics log Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("analytics log float values must be finite Decimal values")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("analytics log object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("analytics log values must be JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return


def _add(left: Decimal, right: Decimal) -> Decimal:
    _require_finite_decimal("left", left)
    _require_finite_decimal("right", right)
    with _exact_decimal_context(left, right):
        return left + right


def _subtract(left: Decimal, right: Decimal) -> Decimal:
    _require_finite_decimal("left", left)
    _require_finite_decimal("right", right)
    with _exact_decimal_context(left, right):
        return left - right


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    _require_finite_decimal("left", left)
    _require_finite_decimal("right", right)
    with _exact_decimal_context(left, right):
        return left * right


def _divide(left: Decimal, right: Decimal) -> Decimal:
    _require_finite_decimal("left", left)
    _require_finite_decimal("right", right)
    if right == 0:
        raise ValueError("right must be nonzero")
    with _exact_decimal_context(left, right):
        return left / right


def _exact_sum(values: Iterable[Decimal]) -> Decimal:
    if isinstance(values, (str, bytes)):
        raise ValueError("values must be an iterable of Decimal values")
    items = tuple(values)
    for value in items:
        _require_finite_decimal("value", value)
    total = Decimal("0")
    for value in items:
        total = _add(total, value)
    return total


def _ratio_or_none(left: Decimal, right: Decimal) -> Decimal | None:
    _require_finite_decimal("left", left)
    _require_finite_decimal("right", right)
    if right == 0:
        return None
    return _quantize_ratio(_divide(left, right))


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_finite_decimal("value", value)
    with _exact_decimal_context(value, RATIO_QUANTUM):
        return value.quantize(RATIO_QUANTUM)


@contextmanager
def _exact_decimal_context(*values: Decimal) -> Iterator[None]:
    with localcontext(Context(prec=_exact_decimal_precision(values), rounding=ROUND_HALF_EVEN)):
        yield


def _exact_decimal_precision(values: tuple[Decimal, ...]) -> int:
    finite_values = [value for value in values if value.is_finite()]
    if not finite_values:
        return 28
    required_digits = sum(
        _integer_digit_count(value) + _fractional_digit_count(value)
        for value in finite_values
    )
    return max(28, required_digits + len(finite_values) + 2)


def _integer_digit_count(value: Decimal) -> int:
    if value.is_zero():
        return 1
    return max(value.adjusted() + 1, 0)


def _fractional_digit_count(value: Decimal) -> int:
    return max(-value.as_tuple().exponent, 0)

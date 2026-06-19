from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Context, Decimal, localcontext

from polymarket_alpha_lab.positions import PaperNavSnapshot, PaperPositionMark


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64)
LIQUIDITY_RISK_STATUSES = (
    "empty_nav_liquidity_risk_history",
    "latest_nav_liquidity_observed",
    "latest_nav_has_unexecutable_liquidity",
)


@dataclass(frozen=True)
class PaperNavLiquidityRiskConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperNavLiquidityRiskMarketRow:
    condition_id: str
    market_slug: str
    token_count: int
    open_size: Decimal
    cost_basis: Decimal
    exit_filled_size: Decimal
    exit_unfilled_size: Decimal
    exit_value: Decimal
    unfilled_open_size_share: Decimal | None
    unexecutable_cost_basis: Decimal
    unexecutable_cost_basis_share: Decimal | None
    weighted_slippage: Decimal | None
    widest_spread: Decimal | None
    fully_executable_count: int
    partially_executable_count: int
    no_exit_depth_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "open_size",
            "cost_basis",
            "exit_filled_size",
            "exit_unfilled_size",
            "exit_value",
            "unexecutable_cost_basis",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unfilled_open_size_share",
            "unexecutable_cost_basis_share",
            "weighted_slippage",
            "widest_spread",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_decimal(field_name, getattr(self, field_name)),
            )
        _require_positive_int("token_count", self.token_count)
        for field_name in (
            "fully_executable_count",
            "partially_executable_count",
            "no_exit_depth_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if (
            self.fully_executable_count
            + self.partially_executable_count
            + self.no_exit_depth_count
            != self.token_count
        ):
            raise ValueError("depth counts must sum to token_count")
        for field_name in (
            "open_size",
            "cost_basis",
            "exit_filled_size",
            "exit_unfilled_size",
            "exit_value",
            "unexecutable_cost_basis",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        if self.open_size <= ZERO:
            raise ValueError("open_size must be positive")
        if self.exit_filled_size + self.exit_unfilled_size != self.open_size:
            raise ValueError("filled and unfilled size must equal open_size")
        if self.unexecutable_cost_basis > self.cost_basis:
            raise ValueError("unexecutable_cost_basis must not exceed cost_basis")
        _require_optional_ratio_decimal(
            "unfilled_open_size_share",
            self.unfilled_open_size_share,
        )
        _require_optional_ratio_decimal(
            "unexecutable_cost_basis_share",
            self.unexecutable_cost_basis_share,
        )
        _require_optional_nonnegative_decimal(
            "weighted_slippage",
            self.weighted_slippage,
        )
        _require_optional_decimal("widest_spread", self.widest_spread)
        if self.cost_basis > self.open_size:
            raise ValueError("cost_basis must not exceed open_size")
        if self.exit_value > self.exit_filled_size:
            raise ValueError("exit_value must not exceed exit_filled_size")
        if self.unfilled_open_size_share != _optional_ratio(
            self.exit_unfilled_size,
            self.open_size,
        ):
            raise ValueError("unfilled_open_size_share must match row quantities")


@dataclass(frozen=True)
class PaperNavLiquidityRiskReport:
    generated_at: datetime
    config_version: str
    nav_snapshot_count: int
    first_marked_at: datetime | None
    last_marked_at: datetime | None
    latest_open_position_count: int
    latest_fully_executable_count: int
    latest_partially_executable_count: int
    latest_no_exit_depth_count: int
    latest_total_open_size: Decimal | None
    latest_total_cost_basis: Decimal | None
    latest_unfilled_size: Decimal | None
    latest_unfilled_open_size_share: Decimal | None
    latest_unexecutable_cost_basis: Decimal | None
    latest_unexecutable_cost_basis_share: Decimal | None
    latest_weighted_slippage: Decimal | None
    latest_widest_spread: Decimal | None
    largest_unexecutable_condition_id: str | None
    largest_unexecutable_market_slug: str | None
    largest_unexecutable_cost_basis: Decimal | None
    consecutive_unexecutable_snapshot_count: int
    worst_observed_unexecutable_cost_basis_share: Decimal | None
    status: str
    market_rows: tuple[PaperNavLiquidityRiskMarketRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.generated_at) is not datetime:
            raise ValueError("generated_at must be a datetime")
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("nav_snapshot_count", self.nav_snapshot_count)
        _require_optional_datetime("first_marked_at", self.first_marked_at)
        _require_optional_datetime("last_marked_at", self.last_marked_at)
        if (self.first_marked_at is None) != (self.last_marked_at is None):
            raise ValueError("marked_at fields must match presence")
        for field_name in (
            "latest_open_position_count",
            "latest_fully_executable_count",
            "latest_partially_executable_count",
            "latest_no_exit_depth_count",
            "consecutive_unexecutable_snapshot_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "latest_total_open_size",
            "latest_total_cost_basis",
            "latest_unfilled_size",
            "latest_unexecutable_cost_basis",
            "latest_weighted_slippage",
            "largest_unexecutable_cost_basis",
            "latest_widest_spread",
            "latest_unfilled_open_size_share",
            "latest_unexecutable_cost_basis_share",
            "worst_observed_unexecutable_cost_basis_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_total_open_size",
            "latest_total_cost_basis",
            "latest_unfilled_size",
            "latest_unexecutable_cost_basis",
            "latest_weighted_slippage",
            "largest_unexecutable_cost_basis",
        ):
            _require_optional_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_optional_decimal("latest_widest_spread", self.latest_widest_spread)
        _require_optional_ratio_decimal(
            "latest_unfilled_open_size_share",
            self.latest_unfilled_open_size_share,
        )
        _require_optional_ratio_decimal(
            "latest_unexecutable_cost_basis_share",
            self.latest_unexecutable_cost_basis_share,
        )
        _require_optional_ratio_decimal(
            "worst_observed_unexecutable_cost_basis_share",
            self.worst_observed_unexecutable_cost_basis_share,
        )
        _require_optional_canonical_string(
            "largest_unexecutable_condition_id",
            self.largest_unexecutable_condition_id,
        )
        _require_optional_canonical_string(
            "largest_unexecutable_market_slug",
            self.largest_unexecutable_market_slug,
        )
        if (
            self.largest_unexecutable_condition_id is None
            or self.largest_unexecutable_market_slug is None
            or self.largest_unexecutable_cost_basis is None
        ) and not (
            self.largest_unexecutable_condition_id is None
            and self.largest_unexecutable_market_slug is None
            and self.largest_unexecutable_cost_basis is None
        ):
            raise ValueError("largest unexecutable fields must match presence")
        if self.status not in LIQUIDITY_RISK_STATUSES:
            raise ValueError("status must be a known liquidity risk status")
        object.__setattr__(self, "market_rows", _normalize_market_rows(self.market_rows))
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")
        _validate_report_consistency(self)


def build_paper_nav_liquidity_risk_report(
    nav_snapshots: Iterable[PaperNavSnapshot],
    *,
    config: PaperNavLiquidityRiskConfig,
    generated_at: datetime,
) -> PaperNavLiquidityRiskReport:
    if type(config) is not PaperNavLiquidityRiskConfig:
        raise ValueError("config must be a PaperNavLiquidityRiskConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    snapshots = _normalize_nav_snapshots(nav_snapshots)
    if not snapshots:
        return PaperNavLiquidityRiskReport(
            generated_at=generated_at,
            config_version=config.config_version,
            nav_snapshot_count=0,
            first_marked_at=None,
            last_marked_at=None,
            latest_open_position_count=0,
            latest_fully_executable_count=0,
            latest_partially_executable_count=0,
            latest_no_exit_depth_count=0,
            latest_total_open_size=None,
            latest_total_cost_basis=None,
            latest_unfilled_size=None,
            latest_unfilled_open_size_share=None,
            latest_unexecutable_cost_basis=None,
            latest_unexecutable_cost_basis_share=None,
            latest_weighted_slippage=None,
            latest_widest_spread=None,
            largest_unexecutable_condition_id=None,
            largest_unexecutable_market_slug=None,
            largest_unexecutable_cost_basis=None,
            consecutive_unexecutable_snapshot_count=0,
            worst_observed_unexecutable_cost_basis_share=None,
            status="empty_nav_liquidity_risk_history",
            market_rows=(),
        )

    latest = snapshots[-1]
    market_rows = _build_market_rows(latest)
    largest_condition_id, largest_market_slug, largest_cost_basis = (
        _largest_unexecutable_market(market_rows)
    )
    latest_total_open_size = _total_open_size(latest)
    latest_unfilled_size = _total_unfilled_size(latest)
    latest_unexecutable_cost_basis = _snapshot_unexecutable_cost_basis(latest)

    return PaperNavLiquidityRiskReport(
        generated_at=generated_at,
        config_version=config.config_version,
        nav_snapshot_count=len(snapshots),
        first_marked_at=snapshots[0].marked_at,
        last_marked_at=latest.marked_at,
        latest_open_position_count=len(latest.marks),
        latest_fully_executable_count=_mark_status_count(latest, "fully_executable"),
        latest_partially_executable_count=_mark_status_count(
            latest,
            "partially_executable",
        ),
        latest_no_exit_depth_count=_mark_status_count(latest, "no_exit_depth"),
        latest_total_open_size=latest_total_open_size,
        latest_total_cost_basis=latest.total_cost_basis,
        latest_unfilled_size=latest_unfilled_size,
        latest_unfilled_open_size_share=_optional_ratio(
            latest_unfilled_size,
            latest_total_open_size,
        ),
        latest_unexecutable_cost_basis=latest_unexecutable_cost_basis,
        latest_unexecutable_cost_basis_share=_optional_ratio(
            latest_unexecutable_cost_basis,
            latest.total_cost_basis,
        ),
        latest_weighted_slippage=_weighted_slippage(latest.marks),
        latest_widest_spread=_widest_spread(latest.marks),
        largest_unexecutable_condition_id=largest_condition_id,
        largest_unexecutable_market_slug=largest_market_slug,
        largest_unexecutable_cost_basis=largest_cost_basis,
        consecutive_unexecutable_snapshot_count=_consecutive_unexecutable_count(
            snapshots,
        ),
        worst_observed_unexecutable_cost_basis_share=(
            _worst_observed_unexecutable_cost_basis_share(snapshots)
        ),
        status=_snapshot_status(latest),
        market_rows=market_rows,
    )


def _normalize_nav_snapshots(
    nav_snapshots: Iterable[PaperNavSnapshot],
) -> tuple[PaperNavSnapshot, ...]:
    if isinstance(nav_snapshots, (str, bytes)):
        raise ValueError("nav_snapshots must be an iterable of PaperNavSnapshot values")
    try:
        snapshots = tuple(nav_snapshots)
    except TypeError as exc:
        raise ValueError(
            "nav_snapshots must be an iterable of PaperNavSnapshot values",
        ) from exc
    for snapshot in snapshots:
        if type(snapshot) is not PaperNavSnapshot:
            raise ValueError("nav_snapshots must contain only PaperNavSnapshot values")
    return tuple(sorted(snapshots, key=lambda snapshot: snapshot.marked_at))


def _build_market_rows(
    snapshot: PaperNavSnapshot,
) -> tuple[PaperNavLiquidityRiskMarketRow, ...]:
    marks_by_market: dict[tuple[str, str], list[PaperPositionMark]] = {}
    for mark in snapshot.marks:
        condition_id = _canonicalize_string("condition_id", mark.condition_id)
        market_slug = _canonicalize_string("market_slug", mark.market_slug)
        marks_by_market.setdefault((condition_id, market_slug), []).append(mark)

    rows: list[PaperNavLiquidityRiskMarketRow] = []
    for condition_id, market_slug in sorted(marks_by_market):
        marks = tuple(marks_by_market[(condition_id, market_slug)])
        open_size = _sum_decimal(mark.open_size for mark in marks)
        cost_basis = _sum_decimal(mark.cost_basis for mark in marks)
        exit_filled_size = _sum_decimal(mark.exit_filled_size for mark in marks)
        exit_unfilled_size = _sum_decimal(mark.exit_unfilled_size for mark in marks)
        unexecutable_cost_basis = _marks_unexecutable_cost_basis(marks)
        rows.append(
            PaperNavLiquidityRiskMarketRow(
                condition_id=condition_id,
                market_slug=market_slug,
                token_count=len(marks),
                open_size=open_size,
                cost_basis=cost_basis,
                exit_filled_size=exit_filled_size,
                exit_unfilled_size=exit_unfilled_size,
                exit_value=_sum_decimal(mark.exit_value for mark in marks),
                unfilled_open_size_share=_optional_ratio(exit_unfilled_size, open_size),
                unexecutable_cost_basis=unexecutable_cost_basis,
                unexecutable_cost_basis_share=_optional_ratio(
                    unexecutable_cost_basis,
                    snapshot.total_cost_basis,
                ),
                weighted_slippage=_weighted_slippage(marks),
                widest_spread=_widest_spread(marks),
                fully_executable_count=_mark_count(marks, "fully_executable"),
                partially_executable_count=_mark_count(marks, "partially_executable"),
                no_exit_depth_count=_mark_count(marks, "no_exit_depth"),
            ),
        )
    return tuple(rows)


def _largest_unexecutable_market(
    rows: tuple[PaperNavLiquidityRiskMarketRow, ...],
) -> tuple[str | None, str | None, Decimal | None]:
    largest = _largest_unexecutable_row(rows)
    if largest is None:
        return None, None, None
    return (
        largest.condition_id,
        largest.market_slug,
        largest.unexecutable_cost_basis,
    )


def _largest_unexecutable_row(
    rows: tuple[PaperNavLiquidityRiskMarketRow, ...],
) -> PaperNavLiquidityRiskMarketRow | None:
    largest: PaperNavLiquidityRiskMarketRow | None = None
    for row in rows:
        if row.unexecutable_cost_basis <= ZERO:
            continue
        if largest is None or row.unexecutable_cost_basis > largest.unexecutable_cost_basis:
            largest = row
    return largest


def _mark_status_count(snapshot: PaperNavSnapshot, mark_status: str) -> int:
    return _mark_count(snapshot.marks, mark_status)


def _mark_count(marks: tuple[PaperPositionMark, ...], mark_status: str) -> int:
    return sum(1 for mark in marks if mark.mark_status == mark_status)


def _total_open_size(snapshot: PaperNavSnapshot) -> Decimal:
    return _sum_decimal(mark.open_size for mark in snapshot.marks)


def _total_unfilled_size(snapshot: PaperNavSnapshot) -> Decimal:
    return _sum_decimal(mark.exit_unfilled_size for mark in snapshot.marks)


def _snapshot_unexecutable_cost_basis(snapshot: PaperNavSnapshot) -> Decimal:
    return _marks_unexecutable_cost_basis(snapshot.marks)


def _marks_unexecutable_cost_basis(marks: tuple[PaperPositionMark, ...]) -> Decimal:
    return _sum_decimal(_mark_unexecutable_cost_basis(mark) for mark in marks)


def _mark_unexecutable_cost_basis(mark: PaperPositionMark) -> Decimal:
    if mark.exit_unfilled_size <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (mark.cost_basis * mark.exit_unfilled_size) / mark.open_size


def _weighted_slippage(marks: tuple[PaperPositionMark, ...]) -> Decimal | None:
    weighted_total = ZERO
    total_weight = ZERO
    for mark in marks:
        if mark.slippage_estimate is None or mark.exit_filled_size <= ZERO:
            continue
        weighted_total = _add_decimal(
            weighted_total,
            _multiply_decimal(mark.slippage_estimate, mark.exit_filled_size),
        )
        total_weight = _add_decimal(total_weight, mark.exit_filled_size)
    return _optional_ratio(weighted_total, total_weight)


def _widest_spread(marks: tuple[PaperPositionMark, ...]) -> Decimal | None:
    spreads = tuple(mark.spread for mark in marks if mark.spread is not None)
    return max(spreads) if spreads else None


def _consecutive_unexecutable_count(snapshots: tuple[PaperNavSnapshot, ...]) -> int:
    count = 0
    for snapshot in reversed(snapshots):
        if not _snapshot_has_unexecutable_liquidity(snapshot):
            break
        count += 1
    return count


def _worst_observed_unexecutable_cost_basis_share(
    snapshots: tuple[PaperNavSnapshot, ...],
) -> Decimal | None:
    shares = tuple(
        share
        for share in (
            _optional_ratio(
                _snapshot_unexecutable_cost_basis(snapshot),
                snapshot.total_cost_basis,
            )
            for snapshot in snapshots
        )
        if share is not None
    )
    return max(shares) if shares else None


def _snapshot_status(snapshot: PaperNavSnapshot) -> str:
    if _snapshot_has_unexecutable_liquidity(snapshot):
        return "latest_nav_has_unexecutable_liquidity"
    return "latest_nav_liquidity_observed"


def _snapshot_has_unexecutable_liquidity(snapshot: PaperNavSnapshot) -> bool:
    return any(mark.exit_unfilled_size > ZERO for mark in snapshot.marks)


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= ZERO:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return left + right


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return left * right


def _normalize_market_rows(
    rows: Iterable[PaperNavLiquidityRiskMarketRow],
) -> tuple[PaperNavLiquidityRiskMarketRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("market_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("market_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperNavLiquidityRiskMarketRow:
            raise ValueError(
                "market_rows must contain PaperNavLiquidityRiskMarketRow values",
            )
    return normalized


def _validate_report_consistency(report: PaperNavLiquidityRiskReport) -> None:
    if report.nav_snapshot_count == 0:
        if report.first_marked_at is not None or report.last_marked_at is not None:
            raise ValueError("empty report must not have marked_at values")
        if report.status != "empty_nav_liquidity_risk_history":
            raise ValueError("status must match liquidity risk observations")
        if report.market_rows:
            raise ValueError("empty report must not include market_rows")
        if report.consecutive_unexecutable_snapshot_count != 0:
            raise ValueError("empty report must have zero unexecutable streak")
        if any(
            getattr(report, field_name) != 0
            for field_name in (
                "latest_open_position_count",
                "latest_fully_executable_count",
                "latest_partially_executable_count",
                "latest_no_exit_depth_count",
            )
        ):
            raise ValueError("empty report must have zero latest counts")
        for field_name in (
            "latest_total_open_size",
            "latest_total_cost_basis",
            "latest_unfilled_size",
            "latest_unfilled_open_size_share",
            "latest_unexecutable_cost_basis",
            "latest_unexecutable_cost_basis_share",
            "latest_weighted_slippage",
            "latest_widest_spread",
            "largest_unexecutable_condition_id",
            "largest_unexecutable_market_slug",
            "largest_unexecutable_cost_basis",
            "worst_observed_unexecutable_cost_basis_share",
        ):
            if getattr(report, field_name) is not None:
                raise ValueError("empty report must not have latest aggregates")
        return
    if report.first_marked_at is None or report.last_marked_at is None:
        raise ValueError("nonempty report must include marked_at values")
    if report.latest_open_position_count != sum(row.token_count for row in report.market_rows):
        raise ValueError("latest_open_position_count must match market_rows")
    if report.latest_fully_executable_count != sum(
        row.fully_executable_count for row in report.market_rows
    ):
        raise ValueError("latest_fully_executable_count must match market_rows")
    if report.latest_partially_executable_count != sum(
        row.partially_executable_count for row in report.market_rows
    ):
        raise ValueError("latest_partially_executable_count must match market_rows")
    if report.latest_no_exit_depth_count != sum(
        row.no_exit_depth_count for row in report.market_rows
    ):
        raise ValueError("latest_no_exit_depth_count must match market_rows")
    if report.latest_total_open_size != _sum_decimal(
        row.open_size for row in report.market_rows
    ):
        raise ValueError("latest_total_open_size must match market_rows")
    if report.latest_total_cost_basis != _sum_decimal(
        row.cost_basis for row in report.market_rows
    ):
        raise ValueError("latest_total_cost_basis must match market_rows")
    if report.latest_unfilled_size != _sum_decimal(
        row.exit_unfilled_size for row in report.market_rows
    ):
        raise ValueError("latest_unfilled_size must match market_rows")
    if report.latest_unexecutable_cost_basis != _sum_decimal(
        row.unexecutable_cost_basis for row in report.market_rows
    ):
        raise ValueError("latest_unexecutable_cost_basis must match market_rows")
    if report.latest_unfilled_open_size_share != _optional_ratio(
        report.latest_unfilled_size or ZERO,
        report.latest_total_open_size or ZERO,
    ):
        raise ValueError("latest_unfilled_open_size_share must match market_rows")
    if report.latest_unexecutable_cost_basis_share != _optional_ratio(
        report.latest_unexecutable_cost_basis or ZERO,
        report.latest_total_cost_basis or ZERO,
    ):
        raise ValueError("latest_unexecutable_cost_basis_share must match market_rows")
    if report.worst_observed_unexecutable_cost_basis_share is not None:
        latest_share = _optional_ratio(
            report.latest_unexecutable_cost_basis or ZERO,
            report.latest_total_cost_basis or ZERO,
        )
        if latest_share is None or report.worst_observed_unexecutable_cost_basis_share < latest_share:
            raise ValueError(
                "worst_observed_unexecutable_cost_basis_share must match observations",
            )
    largest_row = _largest_unexecutable_row(report.market_rows)
    if largest_row is None:
        if (
            report.largest_unexecutable_condition_id is not None
            or report.largest_unexecutable_market_slug is not None
            or report.largest_unexecutable_cost_basis is not None
        ):
            raise ValueError("largest unexecutable fields must match market_rows")
    elif (
        report.largest_unexecutable_condition_id != largest_row.condition_id
        or report.largest_unexecutable_market_slug != largest_row.market_slug
        or report.largest_unexecutable_cost_basis
        != largest_row.unexecutable_cost_basis
    ):
        raise ValueError("largest unexecutable fields must match market_rows")
    if report.latest_unfilled_size is not None:
        has_unexecutable = report.latest_unfilled_size > ZERO
        expected_status = (
            "latest_nav_has_unexecutable_liquidity"
            if has_unexecutable
            else "latest_nav_liquidity_observed"
        )
        if report.status != expected_status:
            raise ValueError("status must match liquidity risk observations")


def _require_canonical_string(field_name: str, value: str) -> None:
    if _canonicalize_string(field_name, value) != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_optional_canonical_string(field_name: str, value: str | None) -> None:
    if value is not None:
        _require_canonical_string(field_name, value)


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: int) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


def _require_optional_datetime(field_name: str, value: datetime | None) -> None:
    if value is None:
        return
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime or None")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    normalized = Decimal(value)
    if not normalized.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return normalized


def _normalize_optional_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_decimal(field_name, value)


def _canonicalize_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    canonical = value.strip()
    if not canonical:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return canonical


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_decimal(field_name, value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _require_optional_ratio_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)
    if value > Decimal("1"):
        raise ValueError(f"{field_name} must be at most one")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(RATIO_QUANTUM)
    if value != quantized:
        raise ValueError(f"{field_name} must use ratio quantum")


__all__ = (
    "PaperNavLiquidityRiskConfig",
    "PaperNavLiquidityRiskMarketRow",
    "PaperNavLiquidityRiskReport",
    "build_paper_nav_liquidity_risk_report",
)

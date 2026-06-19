from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.positions import PaperNavSnapshot


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ZERO_NAV = Decimal("0.0000")


@dataclass(frozen=True)
class PaperNavRiskMetricsConfig:
    config_version: str
    preserve_input_order: bool = False

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_bool("preserve_input_order", self.preserve_input_order)


@dataclass(frozen=True)
class PaperNavRiskExposureRow:
    condition_id: str
    market_slug: str
    token_count: int
    open_size: Decimal
    cost_basis: Decimal
    exit_value: Decimal
    share_of_exit_nav: Decimal | None

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_positive_int("token_count", self.token_count)
        _require_positive_decimal("open_size", self.open_size)
        _require_nonnegative_decimal("cost_basis", self.cost_basis)
        _require_nonnegative_decimal("exit_value", self.exit_value)
        _require_optional_nonnegative_decimal(
            "share_of_exit_nav",
            self.share_of_exit_nav,
        )
        _require_optional_ratio_decimal("share_of_exit_nav", self.share_of_exit_nav)
        if self.cost_basis > self.open_size:
            raise ValueError("cost_basis must not exceed open_size")
        if self.exit_value > self.open_size:
            raise ValueError("exit_value must not exceed open_size")


@dataclass(frozen=True)
class PaperNavRiskMetricsReport:
    generated_at: datetime
    config_version: str
    nav_snapshot_count: int
    first_marked_at: datetime | None
    last_marked_at: datetime | None
    latest_exit_nav: Decimal | None
    latest_starting_cash: Decimal | None
    latest_cash_balance: Decimal | None
    latest_total_cost_basis: Decimal | None
    latest_unrealized_exit_pnl: Decimal | None
    peak_exit_nav: Decimal | None
    trough_exit_nav: Decimal | None
    cumulative_return: Decimal | None
    max_drawdown: Decimal | None
    max_drawdown_pct: Decimal | None
    worst_nav_delta: Decimal | None
    nav_return_volatility: Decimal | None
    pending_notional: Decimal | None
    open_position_count: int
    fully_executable_count: int
    partially_executable_count: int
    no_exit_depth_count: int
    largest_market_exposure_value: Decimal | None
    largest_market_exposure_share: Decimal | None
    exposure_rows: tuple[PaperNavRiskExposureRow, ...]
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("nav_snapshot_count", self.nav_snapshot_count)
        object.__setattr__(
            self,
            "first_marked_at",
            _as_optional_utc("first_marked_at", self.first_marked_at),
        )
        object.__setattr__(
            self,
            "last_marked_at",
            _as_optional_utc("last_marked_at", self.last_marked_at),
        )
        if (self.first_marked_at is None) != (self.last_marked_at is None):
            raise ValueError("first_marked_at and last_marked_at must match presence")
        for field_name in (
            "latest_exit_nav",
            "latest_starting_cash",
            "latest_cash_balance",
            "peak_exit_nav",
            "trough_exit_nav",
            "max_drawdown",
            "max_drawdown_pct",
            "nav_return_volatility",
            "latest_total_cost_basis",
            "pending_notional",
            "largest_market_exposure_value",
            "largest_market_exposure_share",
        ):
            _require_optional_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_optional_decimal(
            "latest_unrealized_exit_pnl",
            self.latest_unrealized_exit_pnl,
        )
        _require_optional_decimal("cumulative_return", self.cumulative_return)
        _require_optional_decimal("worst_nav_delta", self.worst_nav_delta)
        for field_name in (
            "open_position_count",
            "fully_executable_count",
            "partially_executable_count",
            "no_exit_depth_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "exposure_rows",
            _normalize_exposure_rows(self.exposure_rows),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


def build_paper_nav_risk_metrics_report(
    nav_snapshots: Iterable[PaperNavSnapshot],
    *,
    config: PaperNavRiskMetricsConfig,
    generated_at: datetime,
) -> PaperNavRiskMetricsReport:
    if type(config) is not PaperNavRiskMetricsConfig:
        raise ValueError("config must be a PaperNavRiskMetricsConfig")
    generated_at = _as_utc("generated_at", generated_at)

    snapshots = _normalize_nav_snapshots(
        nav_snapshots,
        preserve_input_order=config.preserve_input_order,
    )
    if not snapshots:
        return PaperNavRiskMetricsReport(
            generated_at=generated_at,
            config_version=config.config_version,
            nav_snapshot_count=0,
            first_marked_at=None,
            last_marked_at=None,
            latest_exit_nav=None,
            latest_starting_cash=None,
            latest_cash_balance=None,
            latest_total_cost_basis=None,
            latest_unrealized_exit_pnl=None,
            peak_exit_nav=None,
            trough_exit_nav=None,
            cumulative_return=None,
            max_drawdown=None,
            max_drawdown_pct=None,
            worst_nav_delta=None,
            nav_return_volatility=None,
            pending_notional=None,
            open_position_count=0,
            fully_executable_count=0,
            partially_executable_count=0,
            no_exit_depth_count=0,
            largest_market_exposure_value=None,
            largest_market_exposure_share=None,
            exposure_rows=(),
        )

    latest = snapshots[-1]
    exposure_rows = _build_exposure_rows(latest)
    largest_exposure_value, largest_exposure_share = _largest_exposure(exposure_rows)
    max_drawdown, max_drawdown_pct = _max_drawdown_metrics(snapshots)
    step_returns = _step_returns(snapshots)

    return PaperNavRiskMetricsReport(
        generated_at=generated_at,
        config_version=config.config_version,
        nav_snapshot_count=len(snapshots),
        first_marked_at=snapshots[0].marked_at,
        last_marked_at=latest.marked_at,
        latest_exit_nav=latest.exit_nav,
        latest_starting_cash=latest.starting_cash,
        latest_cash_balance=latest.cash_balance,
        latest_total_cost_basis=latest.total_cost_basis,
        latest_unrealized_exit_pnl=latest.unrealized_exit_pnl,
        peak_exit_nav=max(snapshot.exit_nav for snapshot in snapshots),
        trough_exit_nav=min(snapshot.exit_nav for snapshot in snapshots),
        cumulative_return=_cumulative_return(snapshots),
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
        worst_nav_delta=_worst_nav_delta(snapshots),
        nav_return_volatility=_population_volatility(step_returns),
        pending_notional=latest.total_cost_basis,
        open_position_count=len(latest.marks),
        fully_executable_count=_mark_status_count(latest, "fully_executable"),
        partially_executable_count=_mark_status_count(latest, "partially_executable"),
        no_exit_depth_count=_mark_status_count(latest, "no_exit_depth"),
        largest_market_exposure_value=largest_exposure_value,
        largest_market_exposure_share=largest_exposure_share,
        exposure_rows=exposure_rows,
    )


def _normalize_nav_snapshots(
    nav_snapshots: Iterable[PaperNavSnapshot],
    *,
    preserve_input_order: bool,
) -> tuple[PaperNavSnapshot, ...]:
    if isinstance(nav_snapshots, (str, bytes)):
        raise ValueError("nav_snapshots must be an iterable of PaperNavSnapshot values")
    try:
        raw_snapshots = tuple(nav_snapshots)
    except TypeError as exc:
        raise ValueError(
            "nav_snapshots must be an iterable of PaperNavSnapshot values",
        ) from exc

    for snapshot in raw_snapshots:
        if type(snapshot) is not PaperNavSnapshot:
            raise ValueError("nav_snapshots must contain only PaperNavSnapshot values")

    if preserve_input_order:
        return raw_snapshots
    return tuple(sorted(raw_snapshots, key=lambda snapshot: snapshot.marked_at))


def _cumulative_return(snapshots: tuple[PaperNavSnapshot, ...]) -> Decimal | None:
    first_exit_nav = snapshots[0].exit_nav
    if first_exit_nav <= ZERO:
        return None
    return _quantize_ratio((snapshots[-1].exit_nav - first_exit_nav) / first_exit_nav)


def _max_drawdown_metrics(
    snapshots: tuple[PaperNavSnapshot, ...],
) -> tuple[Decimal, Decimal]:
    running_peak = snapshots[0].exit_nav
    max_drawdown = ZERO_NAV
    max_drawdown_pct = _quantize_ratio(ZERO)

    for snapshot in snapshots:
        if snapshot.exit_nav > running_peak:
            running_peak = snapshot.exit_nav
        drawdown = running_peak - snapshot.exit_nav
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_drawdown_pct = _quantize_ratio(drawdown / running_peak)

    return max_drawdown, max_drawdown_pct


def _worst_nav_delta(snapshots: tuple[PaperNavSnapshot, ...]) -> Decimal | None:
    if len(snapshots) < 2:
        return None

    previous_exit_nav = snapshots[0].exit_nav
    worst_delta: Decimal | None = None
    for snapshot in snapshots[1:]:
        delta = snapshot.exit_nav - previous_exit_nav
        if worst_delta is None or delta < worst_delta:
            worst_delta = delta
        previous_exit_nav = snapshot.exit_nav
    return worst_delta


def _step_returns(
    snapshots: tuple[PaperNavSnapshot, ...],
) -> tuple[Decimal, ...] | None:
    if len(snapshots) < 2:
        return ()

    returns: list[Decimal] = []
    previous_exit_nav = snapshots[0].exit_nav
    for snapshot in snapshots[1:]:
        if previous_exit_nav <= ZERO:
            return None
        returns.append((snapshot.exit_nav - previous_exit_nav) / previous_exit_nav)
        previous_exit_nav = snapshot.exit_nav
    return tuple(returns)


def _population_volatility(step_returns: tuple[Decimal, ...] | None) -> Decimal | None:
    if not step_returns:
        return None

    count = Decimal(len(step_returns))
    mean_return = sum(step_returns, ZERO) / count
    variance = (
        sum(((step_return - mean_return) ** 2 for step_return in step_returns), ZERO)
        / count
    )
    return _quantize_ratio(variance.sqrt())


def _mark_status_count(snapshot: PaperNavSnapshot, mark_status: str) -> int:
    return sum(1 for mark in snapshot.marks if mark.mark_status == mark_status)


def _build_exposure_rows(
    snapshot: PaperNavSnapshot,
) -> tuple[PaperNavRiskExposureRow, ...]:
    token_ids_by_group: dict[tuple[str, str], set[str]] = {}
    open_size_by_group: dict[tuple[str, str], Decimal] = {}
    cost_basis_by_group: dict[tuple[str, str], Decimal] = {}
    exit_value_by_group: dict[tuple[str, str], Decimal] = {}

    for mark in snapshot.marks:
        key = (mark.condition_id, mark.market_slug)
        token_ids_by_group.setdefault(key, set()).add(mark.token_id)
        open_size_by_group[key] = open_size_by_group.get(key, ZERO) + mark.open_size
        cost_basis_by_group[key] = cost_basis_by_group.get(key, ZERO) + mark.cost_basis
        exit_value_by_group[key] = exit_value_by_group.get(key, ZERO) + mark.exit_value

    rows: list[PaperNavRiskExposureRow] = []
    for condition_id, market_slug in sorted(open_size_by_group):
        key = (condition_id, market_slug)
        exit_value = exit_value_by_group[key]
        rows.append(
            PaperNavRiskExposureRow(
                condition_id=condition_id,
                market_slug=market_slug,
                token_count=len(token_ids_by_group[key]),
                open_size=open_size_by_group[key],
                cost_basis=cost_basis_by_group[key],
                exit_value=exit_value,
                share_of_exit_nav=_optional_ratio(exit_value, snapshot.exit_nav),
            ),
        )
    return tuple(rows)


def _largest_exposure(
    exposure_rows: tuple[PaperNavRiskExposureRow, ...],
) -> tuple[Decimal | None, Decimal | None]:
    if not exposure_rows:
        return None, None

    largest = exposure_rows[0]
    for row in exposure_rows[1:]:
        if row.exit_value > largest.exit_value:
            largest = row
    return largest.exit_value, largest.share_of_exit_nav


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return sum(values, ZERO)


def _exposure_totals(
    exposure_rows: tuple[PaperNavRiskExposureRow, ...],
) -> tuple[int, Decimal, Decimal, Decimal]:
    return (
        sum(row.token_count for row in exposure_rows),
        _sum_decimal(row.open_size for row in exposure_rows),
        _sum_decimal(row.cost_basis for row in exposure_rows),
        _sum_decimal(row.exit_value for row in exposure_rows),
    )


def _validate_report_consistency(report: PaperNavRiskMetricsReport) -> None:
    if report.nav_snapshot_count == 0:
        _validate_empty_report(report)
        return

    if report.first_marked_at is None or report.last_marked_at is None:
        raise ValueError("marked_at fields are required when NAV snapshots exist")
    for field_name in (
        "latest_exit_nav",
        "latest_starting_cash",
        "latest_cash_balance",
        "latest_total_cost_basis",
        "latest_unrealized_exit_pnl",
        "peak_exit_nav",
        "trough_exit_nav",
        "max_drawdown",
        "max_drawdown_pct",
        "pending_notional",
    ):
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required when NAV snapshots exist")
    _require_positive_decimal("latest_starting_cash", report.latest_starting_cash)

    if report.open_position_count == 0:
        if report.exposure_rows:
            raise ValueError("exposure_rows must be empty when no positions are open")
        _require_zero_decimal("pending_notional", report.pending_notional)
        _require_zero_decimal("latest_total_cost_basis", report.latest_total_cost_basis)
        _require_zero_decimal(
            "latest_unrealized_exit_pnl",
            report.latest_unrealized_exit_pnl,
        )
        if report.latest_cash_balance != report.latest_exit_nav:
            raise ValueError("latest_exit_nav must equal cash balance plus exposure value")
        _require_none("largest_market_exposure_value", report.largest_market_exposure_value)
        _require_none("largest_market_exposure_share", report.largest_market_exposure_share)
        _require_zero("fully_executable_count", report.fully_executable_count)
        _require_zero("partially_executable_count", report.partially_executable_count)
        _require_zero("no_exit_depth_count", report.no_exit_depth_count)
        return

    token_count, open_size, cost_basis, exit_value = _exposure_totals(report.exposure_rows)
    if token_count != report.open_position_count:
        raise ValueError("open_position_count must match exposure row token counts")
    if (
        report.fully_executable_count
        + report.partially_executable_count
        + report.no_exit_depth_count
        != report.open_position_count
    ):
        raise ValueError("mark status counts must sum to open_position_count")
    if report.latest_total_cost_basis != cost_basis:
        raise ValueError("latest_total_cost_basis must match exposure row cost_basis")
    if report.pending_notional != cost_basis:
        raise ValueError("pending_notional must match latest_total_cost_basis")
    if report.latest_exit_nav is not None:
        for row in report.exposure_rows:
            if row.share_of_exit_nav != _optional_ratio(row.exit_value, report.latest_exit_nav):
                raise ValueError("share_of_exit_nav must match latest_exit_nav")
    if report.latest_cash_balance is not None and report.latest_exit_nav is not None:
        if report.latest_cash_balance + exit_value != report.latest_exit_nav:
            raise ValueError("latest_exit_nav must equal cash balance plus exposure value")
    if report.latest_unrealized_exit_pnl != exit_value - cost_basis:
        raise ValueError("latest_unrealized_exit_pnl must match exposure row exit PnL")
    if report.latest_starting_cash is not None and report.latest_cash_balance is not None:
        realized_pnl = (
            report.latest_exit_nav
            - report.latest_starting_cash
            - report.latest_unrealized_exit_pnl
        )
        if report.latest_cash_balance + report.latest_total_cost_basis - realized_pnl != (
            report.latest_starting_cash
        ):
            raise ValueError("latest_starting_cash must match report accounting identity")
    if open_size < exit_value:
        raise ValueError("exposure row open_size must cover exit value")

    largest_value, largest_share = _largest_exposure(report.exposure_rows)
    if report.largest_market_exposure_value != largest_value:
        raise ValueError("largest_market_exposure_value must match exposure rows")
    if report.largest_market_exposure_share != largest_share:
        raise ValueError("largest_market_exposure_share must match exposure rows")


def _validate_empty_report(report: PaperNavRiskMetricsReport) -> None:
    for field_name in (
        "first_marked_at",
        "last_marked_at",
        "latest_exit_nav",
        "latest_starting_cash",
        "latest_cash_balance",
        "latest_total_cost_basis",
        "latest_unrealized_exit_pnl",
        "peak_exit_nav",
        "trough_exit_nav",
        "cumulative_return",
        "max_drawdown",
        "max_drawdown_pct",
        "worst_nav_delta",
        "nav_return_volatility",
        "pending_notional",
        "largest_market_exposure_value",
        "largest_market_exposure_share",
    ):
        if getattr(report, field_name) is not None:
            raise ValueError("empty NAV risk metrics report cannot include populated metrics")
    for field_name in (
        "open_position_count",
        "fully_executable_count",
        "partially_executable_count",
        "no_exit_depth_count",
    ):
        if getattr(report, field_name) != 0:
            raise ValueError("empty NAV risk metrics report cannot include populated metrics")
    if report.exposure_rows:
        raise ValueError("empty NAV risk metrics report cannot include populated metrics")


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= ZERO:
        return None
    return _quantize_ratio(numerator / denominator)


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _normalize_exposure_rows(
    exposure_rows: tuple[PaperNavRiskExposureRow, ...],
) -> tuple[PaperNavRiskExposureRow, ...]:
    try:
        rows = tuple(exposure_rows)
    except TypeError as exc:
        raise ValueError("exposure_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperNavRiskExposureRow:
            raise ValueError("exposure_rows must contain PaperNavRiskExposureRow values")
    return rows


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_positive_int(field_name: str, value: int) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


def _require_optional_datetime(field_name: str, value: datetime | None) -> None:
    if value is None:
        return
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime or None")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_decimal(field_name: str, value: Decimal | None) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _require_optional_ratio_decimal(field_name: str, value: Decimal | None) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)
    if value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_none(field_name: str, value: object) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None")


def _require_zero(field_name: str, value: int) -> None:
    if value != 0:
        raise ValueError(f"{field_name} must be zero")


def _require_zero_decimal(field_name: str, value: Decimal | None) -> None:
    if value != ZERO:
        raise ValueError(f"{field_name} must be zero")


__all__ = (
    "PaperNavRiskMetricsConfig",
    "PaperNavRiskExposureRow",
    "PaperNavRiskMetricsReport",
    "build_paper_nav_risk_metrics_report",
)

"""Paper-only performance summary aggregator over history logs (Stage 6).

Pure arithmetic over the three persisted JSONL streams (cycle reports, paper
trades, NAV snapshots). It reads nothing itself -- callers pass already-typed
tuples reconstructed by ``PaperStrategyCycleLog.read`` /
``PaperTradeJournal.read`` / ``PaperNavLog.read``. The summary is a research/
audit aggregate: it is paper-only and report-only, never a trade instruction,
investment ranking, recommendation, financial advice, or live-execution signal.

Phase 1 boundary: read-only data analysis over local typed tuples. No fetch,
no live orders, no auth, no wallets, no credentials, no exchange writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.positions import PaperNavSnapshot
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport


__all__ = (
    "PerformanceSummaryConfig",
    "PerformanceSummary",
    "build_performance_summary",
)


@dataclass(frozen=True)
class PerformanceSummaryConfig:
    config_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.config_version, str):
            raise ValueError("config_version must be a string")
        if not self.config_version or self.config_version.strip() != self.config_version:
            raise ValueError("config_version must be a canonical nonblank string")


@dataclass(frozen=True)
class PerformanceSummary:
    generated_at: datetime
    config_version: str
    cycle_count: int
    total_scan_market_count: int
    total_snapshot_ready_count: int
    total_cost_aware_report_count: int
    paper_trade_count: int
    last_exit_nav: Decimal | None
    last_starting_cash: Decimal | None
    total_realized_pnl: Decimal | None
    nav_snapshot_count: int
    first_cycle_at: datetime | None
    last_cycle_at: datetime | None
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at, datetime):
            raise ValueError("generated_at must be a datetime")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "cycle_count",
            "total_scan_market_count",
            "total_snapshot_ready_count",
            "total_cost_aware_report_count",
            "paper_trade_count",
            "nav_snapshot_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_decimal("last_exit_nav", self.last_exit_nav)
        _require_optional_decimal("last_starting_cash", self.last_starting_cash)
        _require_optional_decimal("total_realized_pnl", self.total_realized_pnl)
        if self.first_cycle_at is not None and not isinstance(
            self.first_cycle_at, datetime
        ):
            raise ValueError("first_cycle_at must be a datetime or None")
        if self.last_cycle_at is not None and not isinstance(
            self.last_cycle_at, datetime
        ):
            raise ValueError("last_cycle_at must be a datetime or None")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        # If there are cycles, the time span must be non-empty; first/last come
        # from the same set so either both are None or both are datetimes.
        if (self.first_cycle_at is None) != (self.last_cycle_at is None):
            raise ValueError(
                "first_cycle_at and last_cycle_at must both be set or both be None",
            )


def build_performance_summary(
    cycle_reports: Iterable[PaperStrategyCycleReport],
    trade_records: Iterable[PaperTradeRecord],
    nav_snapshots: Iterable[PaperNavSnapshot],
    *,
    config: PerformanceSummaryConfig,
    generated_at: datetime,
) -> PerformanceSummary:
    """Aggregate the three history streams into one performance summary.

    Pure arithmetic: counts and sums over the supplied typed tuples, plus the
    most-recent NAV snapshot's exit NAV / starting cash / cumulative realized
    P&L and the min/max cycle ``generated_at`` span. Empty inputs yield zeros
    and ``None`` for the NAV-derived and time-span fields.
    """
    if not isinstance(config, PerformanceSummaryConfig):
        raise ValueError("config must be a PerformanceSummaryConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    cycles = tuple(cycle_reports)
    trades = tuple(trade_records)
    snapshots = tuple(nav_snapshots)

    cycle_count = len(cycles)
    total_scan_market_count = sum(
        _as_int(report.scan_market_count) for report in cycles
    )
    total_snapshot_ready_count = sum(
        _as_int(report.snapshot_ready_count) for report in cycles
    )
    total_cost_aware_report_count = sum(
        _as_int(report.cost_aware_report_count) for report in cycles
    )

    if cycles:
        cycle_times = tuple(report.generated_at for report in cycles)
        first_cycle_at = min(cycle_times)
        last_cycle_at = max(cycle_times)
    else:
        first_cycle_at = None
        last_cycle_at = None

    if snapshots:
        latest = snapshots[-1]
        last_exit_nav = latest.exit_nav
        last_starting_cash = latest.starting_cash
        total_realized_pnl = latest.realized_pnl
    else:
        last_exit_nav = None
        last_starting_cash = None
        total_realized_pnl = None

    return PerformanceSummary(
        generated_at=generated_at,
        config_version=config.config_version,
        cycle_count=cycle_count,
        total_scan_market_count=total_scan_market_count,
        total_snapshot_ready_count=total_snapshot_ready_count,
        total_cost_aware_report_count=total_cost_aware_report_count,
        paper_trade_count=len(trades),
        last_exit_nav=last_exit_nav,
        last_starting_cash=last_starting_cash,
        total_realized_pnl=total_realized_pnl,
        nav_snapshot_count=len(snapshots),
        first_cycle_at=first_cycle_at,
        last_cycle_at=last_cycle_at,
    )


def _as_int(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("count must be an int")
    return value


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


def _require_optional_decimal(field_name: str, value: Decimal | None) -> None:
    if value is None:
        return
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")

"""Continuous run v0 orchestrator (Stage 7).

Thin live-layer loop that chains the already-tested Stage 1b/4/5 primitives in
a synchronous ``time.sleep`` loop:

    run_strategy_cycle -> PaperStrategyCycleLog.append -> mark_paper_portfolio_nav

Each iteration is isolated: a single cycle/NAV failure is recorded in the
``RunLoopSummary`` (``iterations_failed`` + ``last_error``) and the loop
continues when ``on_cycle_error="log_and_continue"`` (default), or propagates
when ``on_cycle_error="raise"``.

First-run journal skip (IMPORTANT): on the first iteration the paper-trade
journal may not exist yet (no paper trades journaled -- paper execution
default-off, or the cycle produced no screening_ready candidate).
``mark_paper_portfolio_nav`` reads the journal via ``PaperTradeJournal.read``,
which opens the file directly and raises ``FileNotFoundError`` if it is absent.
The runner pre-checks the journal path AND defensively catches
``FileNotFoundError`` around the NAV mark, skipping the mark and recording the
skip in ``RunLoopSummary.nav_marks_skipped``. The iteration itself still
completes (the cycle ran and the report was logged) -- the skip is a benign
first-run condition, never a cycle failure.

Protocol-only (Q5): this module does NOT import ``api``. It reuses
``strategy_cycle.MarketDataClient`` (a superset of
``paper_portfolio_nav.MarketNavClient`` -- it carries both ``list_markets`` and
``get_order_book``) as the injected client surface; ``cli.py`` constructs the
concrete ``PolymarketPublicClient`` and injects it.

Phase 1 boundary: pure composition of paper-only + read-only primitives,
repeated. No live orders, auth, wallets, private keys, credentials,
account/position reads, or exchange writes. Synchronous ``time.sleep`` loop
only (async/scheduler/daemon is a later stage). The output ``RunLoopSummary``
is paper-only/report-only (``paper_only is True`` / ``report_only is True`` are
hard-enforced with ``is``).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from polymarket_alpha_lab.paper_portfolio_nav import mark_paper_portfolio_nav
from polymarket_alpha_lab.pipeline import MarketScanConfig
from polymarket_alpha_lab.strategy_cycle import (
    MarketDataClient,
    PaperStrategyCycleConfig,
    PaperStrategyCycleLog,
    run_strategy_cycle,
)


__all__ = (
    "RunLoopSummary",
    "run_strategy_loop",
)


@dataclass(frozen=True)
class RunLoopSummary:
    """Paper-only/report-only summary of one ``run_strategy_loop`` invocation.

    Invariant: ``iterations_completed + iterations_failed`` equals the number
    of iterations attempted (``max_iterations``) when the loop ran to
    completion under ``on_cycle_error="log_and_continue"``. Under
    ``on_cycle_error="raise"`` a failing iteration propagates and no summary is
    returned. ``nav_marks_skipped`` counts iterations where the NAV mark was
    skipped because the paper-trade journal did not exist yet (first run, no
    paper trades) -- these iterations still count as completed.
    """

    iterations_completed: int
    iterations_failed: int
    first_iteration_at: datetime
    last_iteration_at: datetime
    last_error: str | None
    nav_marks_skipped: int = 0
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        _require_nonnegative_int("iterations_completed", self.iterations_completed)
        _require_nonnegative_int("iterations_failed", self.iterations_failed)
        _require_nonnegative_int("nav_marks_skipped", self.nav_marks_skipped)
        if not isinstance(self.first_iteration_at, datetime):
            raise ValueError("first_iteration_at must be a datetime")
        if not isinstance(self.last_iteration_at, datetime):
            raise ValueError("last_iteration_at must be a datetime")
        object.__setattr__(self, "first_iteration_at", _as_utc(self.first_iteration_at))
        object.__setattr__(self, "last_iteration_at", _as_utc(self.last_iteration_at))
        if self.last_iteration_at < self.first_iteration_at:
            raise ValueError(
                "last_iteration_at must not be before first_iteration_at",
            )
        if self.last_error is not None and not isinstance(self.last_error, str):
            raise ValueError("last_error must be a string or None")
        if self.last_error is not None and not self.last_error.strip():
            raise ValueError("last_error must be a nonblank string")
        if not isinstance(self.paper_only, bool):
            raise ValueError("paper_only must be a bool")
        if not isinstance(self.report_only, bool):
            raise ValueError("report_only must be a bool")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


def run_strategy_loop(
    *,
    client: MarketDataClient,
    scan_config: MarketScanConfig,
    cycle_config: PaperStrategyCycleConfig,
    starting_cash: Decimal,
    nav_log_path: Path | str | None,
    cycle_report_log_path: Path | str,
    repeat_mode: str = "once",
    interval_seconds: int = 0,
    max_iterations: int = 1,
    on_cycle_error: str = "log_and_continue",
) -> RunLoopSummary:
    """Run the strategy cycle + NAV mark loop ``max_iterations`` times.

    Per iteration (each isolated in its own ``try/except``):

    (a) ``report = run_strategy_cycle(client, scan_config, cycle_config)``.
    (b) ``PaperStrategyCycleLog(cycle_report_log_path).append(report)``.
    (c) If ``cycle_config.paper_trade_journal_path`` is set AND the journal file
        exists, ``mark_paper_portfolio_nav(...)``; otherwise skip the NAV mark
        (first-run / no paper trades yet) and increment ``nav_marks_skipped``.
        ``FileNotFoundError`` from the NAV mark (race: file vanished between the
        existence check and ``PaperTradeJournal.read``) is also treated as a
        benign skip, never a cycle failure.
    (d) If ``repeat_mode == "interval"`` and more iterations remain,
        ``time.sleep(interval_seconds)``.

    ``on_cycle_error="log_and_continue"`` records the failure
    (``iterations_failed`` + ``last_error``) and continues;
    ``on_cycle_error="raise"`` propagates immediately. The returned
    ``RunLoopSummary`` is paper-only/report-only.
    """
    _validate_loop_params(
        client=client,
        scan_config=scan_config,
        cycle_config=cycle_config,
        starting_cash=starting_cash,
        nav_log_path=nav_log_path,
        cycle_report_log_path=cycle_report_log_path,
        repeat_mode=repeat_mode,
        interval_seconds=interval_seconds,
        max_iterations=max_iterations,
        on_cycle_error=on_cycle_error,
    )

    iterations_completed = 0
    iterations_failed = 0
    nav_marks_skipped = 0
    last_error: str | None = None
    first_iteration_at: datetime | None = None
    last_iteration_at: datetime | None = None

    for iteration in range(max_iterations):
        iteration_at = datetime.now(UTC)
        if first_iteration_at is None:
            first_iteration_at = iteration_at
        last_iteration_at = iteration_at

        try:
            # (a) Run one paper-only/read-only strategy cycle.
            report = run_strategy_cycle(
                client=client,
                scan_config=scan_config,
                cycle_config=cycle_config,
            )
            # (b) Append the validated report to the cycle JSONL log.
            PaperStrategyCycleLog(cycle_report_log_path).append(report)
            # (c) Optional NAV mark.
            nav_marks_skipped += _mark_nav_or_skip(
                cycle_config=cycle_config,
                client=client,
                starting_cash=starting_cash,
                nav_log_path=nav_log_path,
                marked_at=iteration_at,
            )
            iterations_completed += 1
        except Exception as exc:
            if on_cycle_error == "raise":
                raise
            iterations_failed += 1
            last_error = f"{type(exc).__name__}: {exc}"
            continue

        # (d) Sleep between iterations (never after last).
        if repeat_mode == "interval" and iteration + 1 < max_iterations:
            time.sleep(interval_seconds)

    # max_iterations >= 1 is validated above, so the loop always ran at least
    # one iteration and both timestamps are set.
    return RunLoopSummary(
        iterations_completed=iterations_completed,
        iterations_failed=iterations_failed,
        first_iteration_at=first_iteration_at,  # type: ignore[arg-type]
        last_iteration_at=last_iteration_at,  # type: ignore[arg-type]
        last_error=last_error,
        nav_marks_skipped=nav_marks_skipped,
    )


def _mark_nav_or_skip(
    *,
    cycle_config: PaperStrategyCycleConfig,
    client: MarketDataClient,
    starting_cash: Decimal,
    nav_log_path: Path | str | None,
    marked_at: datetime,
) -> int:
    """Run the NAV mark when the journal exists; otherwise return skip count.

    Returns ``1`` when the NAV mark was skipped (journal absent or read raised
    ``FileNotFoundError``), ``0`` when the mark ran. A ``None`` journal path
    (paper execution default-off) returns ``0`` -- there is no journal to read,
    so NAV marking is simply not configured for this cycle, not a skip.
    """
    journal_path = cycle_config.paper_trade_journal_path
    if journal_path is None:
        return 0
    try:
        if not Path(journal_path).exists():
            # First run: the cycle ran but produced no paper trades yet (or
            # paper execution is wired but yielded no screening_ready
            # candidate), so the journal file was never created. Skip the NAV
            # mark rather than crashing on PaperTradeJournal.read's open().
            return 1
        mark_paper_portfolio_nav(
            journal_path,
            starting_cash=starting_cash,
            client=client,
            marked_at=marked_at,
            nav_log_path=nav_log_path,
        )
    except FileNotFoundError:
        # Race: the journal existed at the pre-check but vanished before
        # PaperTradeJournal.read opened it. Treat as the same benign skip.
        return 1
    return 0


def _validate_loop_params(
    *,
    client: object,
    scan_config: object,
    cycle_config: object,
    starting_cash: object,
    nav_log_path: object,
    cycle_report_log_path: object,
    repeat_mode: str,
    interval_seconds: object,
    max_iterations: object,
    on_cycle_error: str,
) -> None:
    if not isinstance(client, MarketDataClient):
        raise ValueError("client must be a MarketDataClient")
    if not isinstance(scan_config, MarketScanConfig):
        raise ValueError("scan_config must be a MarketScanConfig")
    if not isinstance(cycle_config, PaperStrategyCycleConfig):
        raise ValueError("cycle_config must be a PaperStrategyCycleConfig")
    if not isinstance(starting_cash, Decimal):
        raise ValueError("starting_cash must be a Decimal")
    assert isinstance(starting_cash, Decimal)
    if starting_cash <= 0:
        raise ValueError("starting_cash must be positive")
    if not isinstance(cycle_report_log_path, (Path, str)):
        raise ValueError("cycle_report_log_path must be a Path or string")
    if isinstance(cycle_report_log_path, str) and not cycle_report_log_path.strip():
        raise ValueError("cycle_report_log_path must be nonblank")
    if nav_log_path is not None and not isinstance(nav_log_path, (Path, str)):
        raise ValueError("nav_log_path must be a Path, string, or None")
    if (
        isinstance(nav_log_path, str)
        and not nav_log_path.strip()
    ):
        raise ValueError("nav_log_path must be nonblank")
    if repeat_mode not in ("once", "interval"):
        raise ValueError("repeat_mode must be 'once' or 'interval'")
    if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, int):
        raise ValueError("interval_seconds must be an int")
    if interval_seconds < 0:
        raise ValueError("interval_seconds must be nonnegative")
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int):
        raise ValueError("max_iterations must be an int")
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")
    if on_cycle_error not in ("log_and_continue", "raise"):
        raise ValueError("on_cycle_error must be 'log_and_continue' or 'raise'")


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")

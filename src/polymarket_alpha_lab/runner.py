"""Continuous run v0 orchestrator (Stage 7).

Thin live-layer loop that chains the already-tested Stage 1b/4/5 primitives in
a synchronous ``time.sleep`` loop:

    run_strategy_cycle -> injected cycle report sink/export -> paper NAV mark

Each iteration is isolated: a single cycle/NAV failure is recorded in the
``RunLoopSummary`` (``iterations_failed`` + ``last_error``) and the loop
continues when ``on_cycle_error="log_and_continue"`` (default), or propagates
when ``on_cycle_error="raise"``.

First-run journal skip (IMPORTANT): on the first iteration the paper-trade
journal may not exist yet (no paper trades journaled -- paper execution
default-off, or the cycle produced no screening_ready candidate).
The NAV reader opens the journal directly and raises ``FileNotFoundError`` if
it is absent. The runner pre-checks the journal path AND defensively catches
``FileNotFoundError`` around that read only, skipping the mark and recording
the skip in ``RunLoopSummary.nav_marks_skipped``. Downstream NAV log/client/sink
failures remain iteration failures. The iteration itself still completes when
the skip is a benign first-run condition (the cycle ran and the report was
logged).

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

Optional recommendation cycle snapshot and action-gated queue persistence are
injected as source/sink pairs, so this module never fakes artifacts from a
``PaperStrategyCycleReport`` and never imports DB adapters.

Paper trade record and NAV snapshot persistence use the same boundary: optional
callable sinks are injected by the CLI/process layer. This module never imports
DB config or adapter modules.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from polymarket_alpha_lab.paper_portfolio_nav import (
    _mark_paper_portfolio_nav_from_records,
    _read_paper_trade_journal_records,
)
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
    cycle_snapshots_persisted: int = 0
    paper_only: bool = True
    report_only: bool = True
    action_gated_queues_persisted: int = 0
    execution_pipelines_persisted: int = 0
    execution_reconciliations_persisted: int = 0
    cycle_reports_persisted: int = 0

    def __post_init__(self) -> None:
        _require_nonnegative_int("iterations_completed", self.iterations_completed)
        _require_nonnegative_int("iterations_failed", self.iterations_failed)
        _require_nonnegative_int("nav_marks_skipped", self.nav_marks_skipped)
        _require_nonnegative_int(
            "cycle_snapshots_persisted",
            self.cycle_snapshots_persisted,
        )
        _require_nonnegative_int(
            "action_gated_queues_persisted",
            self.action_gated_queues_persisted,
        )
        _require_nonnegative_int(
            "execution_reconciliations_persisted",
            self.execution_reconciliations_persisted,
        )
        _require_nonnegative_int(
            "cycle_reports_persisted",
            self.cycle_reports_persisted,
        )
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
    cycle_report_log_path: Path | str | None,
    cycle_report_sink: object | None = None,
    repeat_mode: str = "once",
    interval_seconds: int = 0,
    max_iterations: int = 1,
    on_cycle_error: str = "log_and_continue",
    cycle_snapshot_source: object | None = None,
    cycle_snapshot_sink: object | None = None,
    action_gated_queue_source: object | None = None,
    action_gated_queue_sink: object | None = None,
    paper_trade_record_sink: object | None = None,
    paper_trade_record_source: object | None = None,
    nav_snapshot_sink: object | None = None,
    execution_pipeline_source: object | None = None,
    execution_pipeline_sink: object | None = None,
    execution_reconciliation_source: object | None = None,
    execution_reconciliation_sink: object | None = None,
) -> RunLoopSummary:
    """Run the strategy cycle + NAV mark loop ``max_iterations`` times.

    Per iteration (each isolated in its own ``try/except``):

    (a) ``report = run_strategy_cycle(client, scan_config, cycle_config)``.
    (b) If ``cycle_report_sink`` is set, call ``cycle_report_sink(report)``.
    (c) If ``cycle_report_log_path`` is set, append a JSONL compatibility export.
    (d) If ``cycle_config.paper_trade_journal_path`` is set AND the journal file
        exists, ``mark_paper_portfolio_nav(...)``; otherwise skip the NAV mark
        (first-run / no paper trades yet) and increment ``nav_marks_skipped``.
        ``FileNotFoundError`` from the NAV journal read (race: file vanished
        between the existence check and read) is also treated as a benign skip,
        never a cycle failure. Later NAV log/client/sink failures are cycle
        failures.
    (e) If ``repeat_mode == "interval"`` and more iterations remain,
        ``time.sleep(interval_seconds)``.

    ``on_cycle_error="log_and_continue"`` records the failure
    (``iterations_failed`` + ``last_error``) and continues;
    ``on_cycle_error="raise"`` propagates immediately. The returned
    ``RunLoopSummary`` is paper-only/report-only.

    Paper trade records are emitted by ``run_strategy_cycle`` through the
    required ``paper_trade_record_sink`` whenever paper execution is enabled;
    sink failures are handled as iteration failures by the policy below. When
    ``paper_trade_record_source`` is supplied, NAV marking uses those records
    before falling back to the legacy ``paper_trade_journal_path`` compatibility
    reader.

    ``cycle_report_sink``, ``cycle_snapshot_source`` / ``cycle_snapshot_sink``,
    ``action_gated_queue_source`` / ``action_gated_queue_sink``,
    ``paper_trade_record_sink``, ``paper_trade_record_source``,
    ``nav_snapshot_sink``,
    ``execution_pipeline_source`` / ``execution_pipeline_sink``, and
    ``execution_reconciliation_source`` / ``execution_reconciliation_sink``
    are optional injected persistence hooks. Sink failures are treated like any
    other iteration failure by the existing ``on_cycle_error`` policy.
    """
    _validate_loop_params(
        client=client,
        scan_config=scan_config,
        cycle_config=cycle_config,
        starting_cash=starting_cash,
        nav_log_path=nav_log_path,
        cycle_report_log_path=cycle_report_log_path,
        cycle_report_sink=cycle_report_sink,
        repeat_mode=repeat_mode,
        interval_seconds=interval_seconds,
        max_iterations=max_iterations,
        on_cycle_error=on_cycle_error,
        cycle_snapshot_source=cycle_snapshot_source,
        cycle_snapshot_sink=cycle_snapshot_sink,
        action_gated_queue_source=action_gated_queue_source,
        action_gated_queue_sink=action_gated_queue_sink,
        paper_trade_record_sink=paper_trade_record_sink,
        paper_trade_record_source=paper_trade_record_source,
        nav_snapshot_sink=nav_snapshot_sink,
        execution_pipeline_source=execution_pipeline_source,
        execution_pipeline_sink=execution_pipeline_sink,
        execution_reconciliation_source=execution_reconciliation_source,
        execution_reconciliation_sink=execution_reconciliation_sink,
    )

    iterations_completed = 0
    iterations_failed = 0
    nav_marks_skipped = 0
    cycle_reports_persisted = 0
    cycle_snapshots_persisted = 0
    action_gated_queues_persisted = 0
    execution_pipelines_persisted = 0
    execution_reconciliations_persisted = 0
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
                paper_trade_record_sink=paper_trade_record_sink,
            )
            # (b) Optional supplied full cycle report persistence.
            if cycle_report_sink is not None:
                cycle_report_sink(report)
                cycle_reports_persisted += 1
            # (c) Optional explicit JSONL compatibility export.
            if cycle_report_log_path is not None:
                PaperStrategyCycleLog(cycle_report_log_path).append(report)
            # (d) Optional supplied recommendation-cycle snapshot persistence.
            if cycle_snapshot_source is not None and cycle_snapshot_sink is not None:
                cycle_snapshot = cycle_snapshot_source(
                    cycle_report=report,
                    iteration_started_at=iteration_at,
                )
                _require_snapshot_safety_flags(cycle_snapshot)
                cycle_snapshot_sink(cycle_snapshot)
                cycle_snapshots_persisted += 1
            # (e) Optional supplied action-gated queue persistence.
            if (
                action_gated_queue_source is not None
                and action_gated_queue_sink is not None
            ):
                action_gated_queue = action_gated_queue_source(
                    cycle_report=report,
                    iteration_started_at=iteration_at,
                )
                _require_action_gated_queue_safety_flags(action_gated_queue)
                action_gated_queue_sink(action_gated_queue)
                action_gated_queues_persisted += 1
            # (f) Optional paper execution pipeline.
            if (
                execution_pipeline_source is not None
                and execution_pipeline_sink is not None
            ):
                pipeline_report = execution_pipeline_source(
                    cycle_report=report,
                    iteration_started_at=iteration_at,
                )
                execution_pipeline_sink(pipeline_report)
                execution_pipelines_persisted += 1
            # (g) Optional execution reconciliation persistence.
            if (
                execution_reconciliation_source is not None
                and execution_reconciliation_sink is not None
            ):
                reconciliation_report = execution_reconciliation_source(
                    cycle_report=report,
                    iteration_started_at=iteration_at,
                )
                _require_execution_reconciliation_safety_flags(
                    reconciliation_report,
                )
                execution_reconciliation_sink(reconciliation_report)
                execution_reconciliations_persisted += 1
            # (h) Optional NAV mark.
            nav_marks_skipped += _mark_nav_or_skip(
                cycle_config=cycle_config,
                client=client,
                starting_cash=starting_cash,
                nav_log_path=nav_log_path,
                marked_at=iteration_at,
                paper_trade_record_source=paper_trade_record_source,
                nav_snapshot_sink=nav_snapshot_sink,
            )
            iterations_completed += 1
        except Exception as exc:
            if on_cycle_error == "raise":
                raise
            iterations_failed += 1
            last_error = f"{type(exc).__name__}: {exc}"
            continue

        # Sleep between iterations (never after last).
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
        cycle_snapshots_persisted=cycle_snapshots_persisted,
        action_gated_queues_persisted=action_gated_queues_persisted,
        execution_pipelines_persisted=execution_pipelines_persisted,
        execution_reconciliations_persisted=execution_reconciliations_persisted,
        cycle_reports_persisted=cycle_reports_persisted,
    )


def _mark_nav_or_skip(
    *,
    cycle_config: PaperStrategyCycleConfig,
    client: MarketDataClient,
    starting_cash: Decimal,
    nav_log_path: Path | str | None,
    marked_at: datetime,
    paper_trade_record_source: object | None = None,
    nav_snapshot_sink: object | None = None,
) -> int:
    """Run the NAV mark when records are configured; otherwise return skip count.

    Returns ``1`` when the NAV mark was skipped (journal absent or the journal
    read raised ``FileNotFoundError``), ``0`` when the mark ran. A ``None``
    journal path (paper execution default-off) returns ``0`` -- there is no
    journal to read, so NAV marking is simply not configured for this cycle, not
    a skip.
    """
    if paper_trade_record_source is not None:
        records = tuple(paper_trade_record_source())
        _mark_paper_portfolio_nav_from_records(
            records,
            starting_cash=starting_cash,
            client=client,
            marked_at=marked_at,
            nav_log_path=nav_log_path,
            nav_snapshot_sink=nav_snapshot_sink,  # type: ignore[arg-type]
        )
        return 0

    journal_path = cycle_config.paper_trade_journal_path
    if journal_path is None:
        return 0
    if not Path(journal_path).exists():
        # First run: the cycle ran but produced no paper trades yet (or paper
        # execution is wired but yielded no screening_ready candidate), so the
        # journal file was never created. Skip the NAV mark rather than crashing
        # on the journal reader's open().
        return 1
    try:
        records = _read_paper_trade_journal_records(journal_path)
    except FileNotFoundError:
        return 1
    _mark_paper_portfolio_nav_from_records(
        records,
        starting_cash=starting_cash,
        client=client,
        marked_at=marked_at,
        nav_log_path=nav_log_path,
        nav_snapshot_sink=nav_snapshot_sink,  # type: ignore[arg-type]
    )
    return 0


def _validate_loop_params(
    *,
    client: object,
    scan_config: object,
    cycle_config: object,
    starting_cash: object,
    nav_log_path: object,
    cycle_report_log_path: object,
    cycle_report_sink: object,
    repeat_mode: str,
    interval_seconds: object,
    max_iterations: object,
    on_cycle_error: str,
    cycle_snapshot_source: object,
    cycle_snapshot_sink: object,
    action_gated_queue_source: object,
    action_gated_queue_sink: object,
    paper_trade_record_sink: object,
    paper_trade_record_source: object,
    nav_snapshot_sink: object,
    execution_pipeline_source: object,
    execution_pipeline_sink: object,
    execution_reconciliation_source: object,
    execution_reconciliation_sink: object,
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
    if cycle_report_sink is None and cycle_report_log_path is None:
        raise ValueError("cycle_report_sink or cycle_report_log_path is required")
    if cycle_report_log_path is not None and not isinstance(
        cycle_report_log_path,
        (Path, str),
    ):
        raise ValueError("cycle_report_log_path must be a Path, string, or None")
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
    if cycle_report_sink is not None and not callable(cycle_report_sink):
        raise ValueError("cycle_report_sink must be callable or None")
    if cycle_snapshot_source is not None and not callable(cycle_snapshot_source):
        raise ValueError("cycle_snapshot_source must be callable or None")
    if cycle_snapshot_sink is not None and not callable(cycle_snapshot_sink):
        raise ValueError("cycle_snapshot_sink must be callable or None")
    if (
        action_gated_queue_source is not None
        and not callable(action_gated_queue_source)
    ):
        raise ValueError("action_gated_queue_source must be callable or None")
    if action_gated_queue_sink is not None and not callable(action_gated_queue_sink):
        raise ValueError("action_gated_queue_sink must be callable or None")
    if paper_trade_record_sink is not None and not callable(paper_trade_record_sink):
        raise ValueError("paper_trade_record_sink must be callable or None")
    if paper_trade_record_source is not None and not callable(paper_trade_record_source):
        raise ValueError("paper_trade_record_source must be callable or None")
    if nav_snapshot_sink is not None and not callable(nav_snapshot_sink):
        raise ValueError("nav_snapshot_sink must be callable or None")
    if execution_pipeline_source is not None and not callable(execution_pipeline_source):
        raise ValueError("execution_pipeline_source must be callable or None")
    if execution_pipeline_sink is not None and not callable(execution_pipeline_sink):
        raise ValueError("execution_pipeline_sink must be callable or None")
    if (
        execution_reconciliation_source is not None
        and not callable(execution_reconciliation_source)
    ):
        raise ValueError(
            "execution_reconciliation_source must be callable or None",
        )
    if (
        execution_reconciliation_sink is not None
        and not callable(execution_reconciliation_sink)
    ):
        raise ValueError(
            "execution_reconciliation_sink must be callable or None",
        )


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


def _require_snapshot_safety_flags(snapshot: object) -> None:
    if getattr(snapshot, "paper_only", None) is not True:
        raise ValueError("cycle snapshot must be paper_only")
    if getattr(snapshot, "report_only", None) is not True:
        raise ValueError("cycle snapshot must be report_only")
    if getattr(snapshot, "readonly", None) is not True:
        raise ValueError("cycle snapshot must be readonly")


def _require_action_gated_queue_safety_flags(report: object) -> None:
    if getattr(report, "paper_only", None) is not True:
        raise ValueError("action-gated queue report must be paper_only")
    if getattr(report, "report_only", None) is not True:
        raise ValueError("action-gated queue report must be report_only")
    if getattr(report, "readonly", None) is not True:
        raise ValueError("action-gated queue report must be readonly")


def _require_execution_reconciliation_safety_flags(report: object) -> None:
    if getattr(report, "paper_only", None) is not True:
        raise ValueError("execution reconciliation report must be paper_only")
    if getattr(report, "report_only", None) is not True:
        raise ValueError("execution reconciliation report must be report_only")
    if getattr(report, "readonly", None) is not True:
        raise ValueError("execution reconciliation report must be readonly")

"""Functional tests for ``polymarket_alpha_lab.runner`` (Stage 7 continuous run).

These compose the already-tested Stage 1b/4/5 primitives behind the new loop
orchestrator using a canned, no-network ``MarketDataClient``. ``time.sleep`` is
patched so multi-iteration runs do not actually block. All timestamps are
caller-stamped via ``datetime.now(UTC)`` inside the loop, so the assertions
check ordering/validity, not exact wall-clock values.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from polymarket_alpha_lab.book_imbalance_forecast import (
    PaperBookImbalanceForecastConfig,
)
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventStrategyConfig,
)
from polymarket_alpha_lab.cost_aware_snapshot_builder import (
    PaperCostAwareSnapshotConfig,
)
from polymarket_alpha_lab.forecast_provider import PaperForecastConfig
from polymarket_alpha_lab.journal import PaperTradeJournal
from polymarket_alpha_lab.paper_execution import PaperExecutionConfig
from polymarket_alpha_lab.pipeline import MarketScanConfig
from polymarket_alpha_lab.project_screening import PaperProjectScreeningConfig
from polymarket_alpha_lab.runner import RunLoopSummary, run_strategy_loop
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleLog


# ---------------------------------------------------------------------------
# Canned raw Gamma market / CLOB book payload builders + fake client
# ---------------------------------------------------------------------------


def raw_market(
    *,
    condition_id: str,
    slug: str,
    question: str,
    token_ids: tuple[str, ...],
    outcomes: tuple[str, ...] = ("Yes", "No"),
    **overrides,
):
    payload = {
        "conditionId": condition_id,
        "outcomes": list(outcomes),
        "clobTokenIds": list(token_ids),
        "slug": slug,
        "question": question,
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "enableOrderBook": True,
        "volume24hr": "5000",
        "liquidity": "10000",
        "description": "Market resolves according to the public source.",
        "resolutionSource": "public-source",
    }
    payload.update(overrides)
    return payload


def raw_book(token_id: str, *, bid="0.5000", ask="0.5500", size="100.0000"):
    return {
        "asset_id": token_id,
        "bids": [{"price": bid, "size": size}],
        "asks": [{"price": ask, "size": size}],
    }


class FakeMarketDataClient:
    """Canned, no-network client satisfying the loop's MarketDataClient surface."""

    def __init__(self, markets, books):
        self._markets = list(markets)
        self._books = dict(books)
        self.list_markets_calls = []
        self.get_order_book_calls = []

    def list_markets(self, *, active, closed, limit, search=None):
        self.list_markets_calls.append({"active": active, "closed": closed, "limit": limit})
        return list(self._markets)

    def get_order_book(self, *, token_id):
        self.get_order_book_calls.append(token_id)
        if token_id not in self._books:
            raise KeyError(token_id)
        return self._books[token_id]


class FailingMarketDataClient:
    """Client whose list_markets raises, to drive cycle-level failures."""

    def __init__(self, error: Exception):
        self._error = error
        self.list_markets_calls = 0

    def list_markets(self, *, active, closed, limit, search=None):
        self.list_markets_calls += 1
        raise self._error

    def get_order_book(self, *, token_id):  # pragma: no cover - never reached
        raise AssertionError("get_order_book should not be reached when list_markets fails")


@dataclass(frozen=True)
class CycleSnapshotShape:
    generated_at: datetime
    config_version: str = "cycle-snapshot-test-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _screening_ready_market_and_books():
    """Binary market whose NO side yields a screening_ready candidate.

    Mirrors tests/test_strategy_cycle._screening_ready_market_and_books: naive
    forecast -> NO net_edge 0.05 (>= 0.01), tight yes spread + depth -> high
    confidence (>= 0.70), screening_score 0.05 (>= 0.01) -> screening_ready on
    the NO side. The inline paper-execution pass journals one buy on "no-paper".
    """
    market = raw_market(
        condition_id="0xcondPaper",
        slug="market-paper",
        question="Will Paper happen?",
        token_ids=("yes-paper", "no-paper"),
    )
    books = {
        "yes-paper": raw_book(
            "yes-paper",
            bid="0.5300",
            ask="0.5500",
            size="100.0000",
        ),
        "no-paper": raw_book(
            "no-paper",
            bid="0.3700",
            ask="0.4000",
            size="100.0000",
        ),
    }
    return market, books


# ---------------------------------------------------------------------------
# Config factories (mirror tests/test_strategy_cycle defaults)
# ---------------------------------------------------------------------------


def forecast_config(**overrides):
    values = {
        "config_version": "naive-forecast-v1",
        "min_book_depth": Decimal("1.0000"),
        "low_confidence_value": Decimal("0.5000"),
        "high_confidence_value": Decimal("0.7500"),
        "max_spread_for_high_confidence": Decimal("0.0300"),
    }
    values.update(overrides)
    return PaperForecastConfig(**values)


def snapshot_config(**overrides):
    values = {
        "config_version": "snapshot-builder-v1",
        "default_resolution_risk": Decimal("0.1000"),
        "missing_rules_resolution_risk": Decimal("0.3000"),
        "imminent_resolution_risk_cap": Decimal("0.0500"),
        "imminent_resolution_horizon_hours": 24,
    }
    values.update(overrides)
    return PaperCostAwareSnapshotConfig(**values)


def strategy_config(**overrides):
    values = {
        "config_version": "cost-aware-event-v1",
        "min_confidence": Decimal("0.7000"),
        "max_spread": Decimal("0.0500"),
        "max_resolution_risk": Decimal("0.2000"),
        "min_ask_size": Decimal("10.0000"),
        "min_net_edge": Decimal("0.0100"),
    }
    values.update(overrides)
    return PaperCostAwareEventStrategyConfig(**values)


def screening_config(**overrides):
    values = {
        "config_version": "project-screening-v1",
        "min_screening_score": Decimal("0.010000"),
        "reference_ask_size": Decimal("100.0000"),
        "net_edge_weight": Decimal("1.0000"),
        "confidence_weight": Decimal("0.0000"),
        "depth_weight": Decimal("0.0000"),
        "spread_penalty_weight": Decimal("0.0000"),
        "resolution_risk_penalty_weight": Decimal("0.0000"),
        "cost_penalty_weight": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperProjectScreeningConfig(**values)


def cost_assumptions(**overrides):
    values = {
        "taker_fee_rate": Decimal("0.0000"),
        "slippage_cost_per_share": Decimal("0.0000"),
        "funding_cost_per_share": Decimal("0.0000"),
        "finalization_cost_per_share": Decimal("0.0000"),
        "time_cost_per_share": Decimal("0.0000"),
        "risk_cost_per_share": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperCostAwareEventCostAssumptions(**values)


def cycle_config(**overrides):
    values = {
        "config_version": "strategy-cycle-v1",
        "forecast_config": forecast_config(),
        "snapshot_config": snapshot_config(),
        "strategy_config": strategy_config(),
        "screening_config": screening_config(),
        "cost_assumptions": cost_assumptions(),
        "max_markets_per_cycle": 50,
        "prefilter_by_score": True,
    }
    values.update(overrides)
    return _build_cycle_config(**values)


def _build_cycle_config(**values):
    overrides = dict(values)
    paper_exec = overrides.pop("paper_execution_config", None)
    paper_journal = overrides.pop("paper_trade_journal_path", None)
    base_kwargs = {
        "config_version": overrides.pop("config_version", "strategy-cycle-v1"),
        "forecast_config": overrides.pop("forecast_config", forecast_config()),
        "snapshot_config": overrides.pop("snapshot_config", snapshot_config()),
        "strategy_config": overrides.pop("strategy_config", strategy_config()),
        "screening_config": overrides.pop("screening_config", screening_config()),
        "cost_assumptions": overrides.pop("cost_assumptions", cost_assumptions()),
        "max_markets_per_cycle": overrides.pop("max_markets_per_cycle", 50),
        "prefilter_by_score": overrides.pop("prefilter_by_score", True),
    }
    base_kwargs.update(overrides)
    if paper_exec is None and paper_journal is None:
        return _PaperStrategyCycleConfigBase(**base_kwargs)
    return _PaperStrategyCycleConfigBase(
        **base_kwargs,
        paper_execution_config=paper_exec,
        paper_trade_journal_path=paper_journal,
    )


# Local alias to avoid importing PaperStrategyCycleConfig's full name in every
# factory call; the real frozen dataclass is used end-to-end.
from polymarket_alpha_lab.strategy_cycle import (  # noqa: E402
    PaperStrategyCycleConfig as _PaperStrategyCycleConfigBase,
)


def scan_config(archive_root: Path, *, limit: int = 50) -> MarketScanConfig:
    return MarketScanConfig(
        limit=limit,
        archive_root=Path(archive_root),
        output_path=Path(archive_root) / "ignored.json",
    )


def _paper_exec_config() -> PaperExecutionConfig:
    return PaperExecutionConfig(config_version="paper-execution-v1")


# ---------------------------------------------------------------------------
# Behavior tests
# ---------------------------------------------------------------------------


def test_single_shot_runs_one_cycle_and_logs_report_without_sleep(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    journal_path = tmp_path / "paper-trades.jsonl"
    cycle_log = tmp_path / "cycle.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=journal_path,
    )

    with patch("polymarket_alpha_lab.runner.time.sleep") as sleep_mock:
        summary = run_strategy_loop(
            client=client,
            scan_config=scan_config(tmp_path),
            cycle_config=config,
            starting_cash=Decimal("10000"),
            nav_log_path=nav_log,
            cycle_report_log_path=cycle_log,
        )

    # Single-shot: exactly one cycle ran, no inter-iteration sleep.
    assert len(client.list_markets_calls) == 1
    assert sleep_mock.call_count == 0
    assert isinstance(summary, RunLoopSummary)
    assert summary.iterations_completed == 1
    assert summary.iterations_failed == 0
    assert summary.nav_marks_skipped == 0
    assert summary.last_error is None
    assert summary.paper_only is True
    assert summary.report_only is True
    # The cycle report was appended to the JSONL log and round-trips.
    reports = PaperStrategyCycleLog.read(cycle_log)
    assert len(reports) == 1
    assert reports[0].scan_market_count == 1
    assert reports[0].snapshot_ready_count == 1
    # Paper execution journaled one trade, so the NAV mark ran and was logged.
    assert journal_path.exists()
    assert nav_log.exists()
    assert len(nav_log.read_text(encoding="utf-8").splitlines()) == 1


def test_multi_iteration_runs_cycle_per_iteration_and_sleeps_between(tmp_path):
    # Paper execution OFF: each iteration is a clean read-only cycle that
    # always succeeds (no journal writes, no duplicate-packet NAV conflict).
    # This isolates the loop/sleep/repetition behavior.
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    cycle_log = tmp_path / "cycle.jsonl"
    nav_log = tmp_path / "nav.jsonl"

    with patch("polymarket_alpha_lab.runner.time.sleep") as sleep_mock:
        summary = run_strategy_loop(
            client=client,
            scan_config=scan_config(tmp_path),
            cycle_config=cycle_config(),
            starting_cash=Decimal("10000"),
            nav_log_path=nav_log,
            cycle_report_log_path=cycle_log,
            repeat_mode="interval",
            interval_seconds=60,
            max_iterations=3,
        )

    # Three cycles, two inter-iteration sleeps (never after the last).
    assert len(client.list_markets_calls) == 3
    assert sleep_mock.call_count == 2
    assert [call.args[0] for call in sleep_mock.call_args_list] == [60, 60]
    assert summary.iterations_completed == 3
    assert summary.iterations_failed == 0
    # No journal configured -> NAV marking not engaged (not a "skip").
    assert summary.nav_marks_skipped == 0
    # Timestamps: first <= last, both recent UTC.
    assert summary.first_iteration_at.tzinfo == UTC
    assert summary.last_iteration_at.tzinfo == UTC
    assert summary.first_iteration_at <= summary.last_iteration_at
    now = datetime.now(UTC)
    assert now - timedelta(seconds=5) <= summary.last_iteration_at <= now + timedelta(seconds=5)
    # Each iteration appended one report; no NAV log (paper execution off).
    assert len(PaperStrategyCycleLog.read(cycle_log)) == 3
    assert not nav_log.exists()


def test_error_isolation_log_and_continue_records_failure_and_keeps_going(tmp_path):
    error = RuntimeError("cycle exploded")
    client = FailingMarketDataClient(error)
    cycle_log = tmp_path / "cycle.jsonl"
    nav_log = tmp_path / "nav.jsonl"

    with patch("polymarket_alpha_lab.runner.time.sleep") as sleep_mock:
        summary = run_strategy_loop(
            client=client,
            scan_config=scan_config(tmp_path),
            cycle_config=cycle_config(),
            starting_cash=Decimal("10000"),
            nav_log_path=nav_log,
            cycle_report_log_path=cycle_log,
            repeat_mode="interval",
            interval_seconds=1,
            max_iterations=3,
            on_cycle_error="log_and_continue",
        )

    # Every iteration failed at list_markets; none reached the report log or
    # the inter-iteration sleep (continue skips the sleep step).
    assert client.list_markets_calls == 3
    assert sleep_mock.call_count == 0
    assert summary.iterations_completed == 0
    assert summary.iterations_failed == 3
    assert summary.last_error == "RuntimeError: cycle exploded"
    assert not cycle_log.exists()
    assert not nav_log.exists()


def test_error_isolation_continues_after_a_failed_iteration_then_succeeds(tmp_path):
    # Failing client that raises once on the first list_markets call, then a
    # canned working client takes over for the remaining iterations. This
    # proves a single bad iteration does not abort the loop.
    market, books = _screening_ready_market_and_books()

    call_state = {"failures_left": 1}

    class FlakyClient:
        def __init__(self):
            self.working = FakeMarketDataClient([market], books)

        def list_markets(self, *, active, closed, limit, search=None):
            if call_state["failures_left"] > 0:
                call_state["failures_left"] -= 1
                raise RuntimeError("transient outage")
            return self.working.list_markets(active=active, closed=closed, limit=limit)

        def get_order_book(self, *, token_id):
            return self.working.get_order_book(token_id=token_id)

    journal_path = tmp_path / "paper-trades.jsonl"
    cycle_log = tmp_path / "cycle.jsonl"
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=journal_path,
    )

    with patch("polymarket_alpha_lab.runner.time.sleep"):
        summary = run_strategy_loop(
            client=FlakyClient(),
            scan_config=scan_config(tmp_path),
            cycle_config=config,
            starting_cash=Decimal("10000"),
            nav_log_path=tmp_path / "nav.jsonl",
            cycle_report_log_path=cycle_log,
            repeat_mode="interval",
            interval_seconds=0,
            max_iterations=2,
            on_cycle_error="log_and_continue",
        )

    assert summary.iterations_completed == 1
    assert summary.iterations_failed == 1
    assert summary.last_error == "RuntimeError: transient outage"
    # The successful iteration appended exactly one report.
    assert len(PaperStrategyCycleLog.read(cycle_log)) == 1


def test_on_cycle_error_raise_propagates_without_summary(tmp_path):
    error = ValueError("hard failure")
    client = FailingMarketDataClient(error)

    with patch("polymarket_alpha_lab.runner.time.sleep"), pytest.raises(ValueError, match="hard failure"):
        run_strategy_loop(
            client=client,
            scan_config=scan_config(tmp_path),
            cycle_config=cycle_config(),
            starting_cash=Decimal("10000"),
            nav_log_path=tmp_path / "nav.jsonl",
            cycle_report_log_path=tmp_path / "cycle.jsonl",
            max_iterations=3,
            on_cycle_error="raise",
        )


def test_first_run_skips_nav_mark_when_journal_does_not_exist(tmp_path):
    # Paper execution is OFF, so the cycle never creates a journal. The NAV
    # mark is configured (paper_trade_journal_path set) but the file is absent
    # on the first run -> the NAV mark is skipped, not treated as a failure.
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    journal_path = tmp_path / "paper-trades.jsonl"
    cycle_log = tmp_path / "cycle.jsonl"
    nav_log = tmp_path / "nav.jsonl"

    # Build a cycle config with paper execution enabled so paper_trade_journal_path
    # is set (the config invariant requires both fields together), then use a
    # scan that produces NO screening_ready candidate so no trade is journaled.
    # Easiest: a non-binary market -> blocked_non_binary_market, zero trades.
    non_binary = raw_market(
        condition_id="0xcondNonBinary",
        slug="market-non-binary",
        question="Will a multi-outcome resolve?",
        token_ids=("alpha-token", "beta-token", "gamma-token"),
        outcomes=("Alpha", "Beta", "Gamma"),
    )
    non_binary_client = FakeMarketDataClient([non_binary], {})
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=journal_path,
    )

    summary = run_strategy_loop(
        client=non_binary_client,
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        starting_cash=Decimal("10000"),
        nav_log_path=nav_log,
        cycle_report_log_path=cycle_log,
    )

    # The cycle completed (one report logged) but produced no paper trade, so
    # the journal file was never created and the NAV mark was skipped.
    assert summary.iterations_completed == 1
    assert summary.iterations_failed == 0
    assert summary.nav_marks_skipped == 1
    assert summary.last_error is None
    assert len(PaperStrategyCycleLog.read(cycle_log)) == 1
    assert not journal_path.exists()
    assert not nav_log.exists()


def test_nav_mark_runs_when_journal_exists_after_paper_trade(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    journal_path = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=journal_path,
    )

    summary = run_strategy_loop(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        starting_cash=Decimal("10000"),
        nav_log_path=nav_log,
        cycle_report_log_path=tmp_path / "cycle.jsonl",
    )

    # The screening_ready candidate journaled a buy; the journal now exists, so
    # the NAV mark ran and was appended to the nav log (skip count zero).
    assert summary.nav_marks_skipped == 0
    assert journal_path.exists()
    assert nav_log.exists()
    nav_lines = nav_log.read_text(encoding="utf-8").splitlines()
    assert len(nav_lines) == 1
    snapshot = json.loads(nav_lines[0])
    # Paper-only enforced on every persisted snapshot.
    assert snapshot["paper_only"] is True
    assert Decimal(snapshot["starting_cash"]) == Decimal("10000")


def test_paper_trade_record_sink_runs_for_journaled_trade(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    journal_path = tmp_path / "paper-trades.jsonl"
    trade_records = []
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=journal_path,
    )

    summary = run_strategy_loop(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        starting_cash=Decimal("10000"),
        nav_log_path=tmp_path / "nav.jsonl",
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        paper_trade_record_sink=trade_records.append,
    )

    assert summary.iterations_completed == 1
    assert summary.iterations_failed == 0
    assert len(trade_records) == 1
    assert PaperTradeJournal.read(journal_path) == (trade_records[0],)


def test_paper_trade_record_sink_failure_counts_as_iteration_failure(
    tmp_path,
):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    journal_path = tmp_path / "paper-trades.jsonl"
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=journal_path,
    )

    def broken_trade_sink(record):
        raise RuntimeError("trade db unavailable")

    summary = run_strategy_loop(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        starting_cash=Decimal("10000"),
        nav_log_path=tmp_path / "nav.jsonl",
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        paper_trade_record_sink=broken_trade_sink,
        on_cycle_error="log_and_continue",
    )

    assert summary.iterations_completed == 0
    assert summary.iterations_failed == 1
    assert summary.last_error == "RuntimeError: trade db unavailable"
    assert len(PaperTradeJournal.read(journal_path)) == 1


def test_nav_snapshot_sink_runs_after_successful_nav_mark(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    journal_path = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    nav_snapshots = []
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=journal_path,
    )

    summary = run_strategy_loop(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        starting_cash=Decimal("10000"),
        nav_log_path=nav_log,
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        nav_snapshot_sink=nav_snapshots.append,
    )

    assert summary.iterations_completed == 1
    assert summary.iterations_failed == 0
    assert summary.nav_marks_skipped == 0
    assert len(nav_snapshots) == 1
    assert nav_snapshots[0].paper_only is True
    assert len(nav_log.read_text(encoding="utf-8").splitlines()) == 1


def test_nav_snapshot_sink_is_not_called_when_nav_mark_is_skipped(tmp_path):
    non_binary = raw_market(
        condition_id="0xcondNonBinary",
        slug="market-non-binary",
        question="Will a multi-outcome resolve?",
        token_ids=("alpha-token", "beta-token", "gamma-token"),
        outcomes=("Alpha", "Beta", "Gamma"),
    )
    journal_path = tmp_path / "paper-trades.jsonl"
    nav_snapshots = []
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=journal_path,
    )

    summary = run_strategy_loop(
        client=FakeMarketDataClient([non_binary], {}),
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        starting_cash=Decimal("10000"),
        nav_log_path=tmp_path / "nav.jsonl",
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        nav_snapshot_sink=nav_snapshots.append,
    )

    assert summary.iterations_completed == 1
    assert summary.iterations_failed == 0
    assert summary.nav_marks_skipped == 1
    assert nav_snapshots == []


def test_nav_snapshot_sink_failure_counts_as_iteration_failure_not_nav_skip(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    journal_path = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=journal_path,
    )

    def broken_nav_sink(snapshot):
        raise RuntimeError("nav db unavailable")

    summary = run_strategy_loop(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        starting_cash=Decimal("10000"),
        nav_log_path=nav_log,
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        nav_snapshot_sink=broken_nav_sink,
        on_cycle_error="log_and_continue",
    )

    assert summary.iterations_completed == 0
    assert summary.iterations_failed == 1
    assert summary.nav_marks_skipped == 0
    assert summary.last_error == "RuntimeError: nav db unavailable"
    assert len(nav_log.read_text(encoding="utf-8").splitlines()) == 1


def test_nav_snapshot_sink_file_not_found_counts_as_iteration_failure_not_nav_skip(
    tmp_path,
):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    journal_path = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=journal_path,
    )

    def broken_nav_sink(snapshot):
        raise FileNotFoundError("nav db certificate file missing")

    summary = run_strategy_loop(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        starting_cash=Decimal("10000"),
        nav_log_path=nav_log,
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        nav_snapshot_sink=broken_nav_sink,
        on_cycle_error="log_and_continue",
    )

    assert summary.iterations_completed == 0
    assert summary.iterations_failed == 1
    assert summary.nav_marks_skipped == 0
    assert summary.last_error == "FileNotFoundError: nav db certificate file missing"
    assert len(nav_log.read_text(encoding="utf-8").splitlines()) == 1


def test_none_journal_path_skips_nav_mark_without_counting_as_skip(tmp_path):
    # Paper execution OFF -> paper_trade_journal_path is None. NAV marking is
    # not configured for this cycle, so the skip count stays zero (it is not a
    # "first-run" skip -- there is simply no journal to mark).
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    nav_log = tmp_path / "nav.jsonl"

    summary = run_strategy_loop(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(),
        starting_cash=Decimal("10000"),
        nav_log_path=nav_log,
        cycle_report_log_path=tmp_path / "cycle.jsonl",
    )

    assert summary.iterations_completed == 1
    assert summary.nav_marks_skipped == 0
    assert not nav_log.exists()


def test_cycle_snapshot_source_and_sink_run_once_per_completed_iteration(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    source_calls = []
    sink_calls = []

    def cycle_snapshot_source(*, cycle_report, iteration_started_at):
        source_calls.append((cycle_report, iteration_started_at))
        return CycleSnapshotShape(generated_at=iteration_started_at)

    def cycle_snapshot_sink(snapshot):
        sink_calls.append(snapshot)

    with patch("polymarket_alpha_lab.runner.time.sleep"):
        summary = run_strategy_loop(
            client=client,
            scan_config=scan_config(tmp_path),
            cycle_config=cycle_config(),
            starting_cash=Decimal("10000"),
            nav_log_path=tmp_path / "nav.jsonl",
            cycle_report_log_path=tmp_path / "cycle.jsonl",
            repeat_mode="interval",
            interval_seconds=0,
            max_iterations=2,
            cycle_snapshot_source=cycle_snapshot_source,
            cycle_snapshot_sink=cycle_snapshot_sink,
        )

    assert summary.iterations_completed == 2
    assert summary.iterations_failed == 0
    assert summary.cycle_snapshots_persisted == 2
    assert len(source_calls) == 2
    assert len(sink_calls) == 2
    assert all(snapshot.paper_only is True for snapshot in sink_calls)
    assert all(snapshot.report_only is True for snapshot in sink_calls)
    assert all(snapshot.readonly is True for snapshot in sink_calls)


def test_cycle_snapshot_sink_is_inert_without_source(tmp_path):
    market, books = _screening_ready_market_and_books()
    sink_calls = []

    summary = run_strategy_loop(
        client=FakeMarketDataClient([market], books),
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(),
        starting_cash=Decimal("10000"),
        nav_log_path=tmp_path / "nav.jsonl",
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        cycle_snapshot_sink=lambda snapshot: sink_calls.append(snapshot),
    )

    assert summary.iterations_completed == 1
    assert summary.cycle_snapshots_persisted == 0
    assert sink_calls == []


def test_cycle_snapshot_sink_failure_counts_as_iteration_failure(tmp_path):
    market, books = _screening_ready_market_and_books()

    def cycle_snapshot_source(*, cycle_report, iteration_started_at):
        return CycleSnapshotShape(generated_at=iteration_started_at)

    def broken_cycle_snapshot_sink(snapshot):
        raise RuntimeError("snapshot db unavailable")

    summary = run_strategy_loop(
        client=FakeMarketDataClient([market], books),
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(),
        starting_cash=Decimal("10000"),
        nav_log_path=tmp_path / "nav.jsonl",
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        cycle_snapshot_source=cycle_snapshot_source,
        cycle_snapshot_sink=broken_cycle_snapshot_sink,
        on_cycle_error="log_and_continue",
    )

    assert summary.iterations_completed == 0
    assert summary.iterations_failed == 1
    assert summary.cycle_snapshots_persisted == 0
    assert summary.last_error == "RuntimeError: snapshot db unavailable"


def test_cycle_report_log_is_appended_before_cycle_snapshot_sink_failure(tmp_path):
    market, books = _screening_ready_market_and_books()
    cycle_log = tmp_path / "cycle.jsonl"

    def cycle_snapshot_source(*, cycle_report, iteration_started_at):
        return CycleSnapshotShape(generated_at=iteration_started_at)

    def broken_cycle_snapshot_sink(snapshot):
        assert len(PaperStrategyCycleLog.read(cycle_log)) == 1
        raise RuntimeError("snapshot db unavailable")

    summary = run_strategy_loop(
        client=FakeMarketDataClient([market], books),
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(),
        starting_cash=Decimal("10000"),
        nav_log_path=tmp_path / "nav.jsonl",
        cycle_report_log_path=cycle_log,
        cycle_snapshot_source=cycle_snapshot_source,
        cycle_snapshot_sink=broken_cycle_snapshot_sink,
        on_cycle_error="log_and_continue",
    )

    assert summary.iterations_completed == 0
    assert summary.iterations_failed == 1
    assert summary.cycle_snapshots_persisted == 0
    assert summary.last_error == "RuntimeError: snapshot db unavailable"
    assert len(PaperStrategyCycleLog.read(cycle_log)) == 1


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"repeat_mode": "forever"}, "repeat_mode"),
        ({"interval_seconds": -1}, "interval_seconds|nonnegative"),
        ({"interval_seconds": 1.5}, "interval_seconds|int"),
        ({"interval_seconds": True}, "interval_seconds|int"),
        ({"max_iterations": 0}, "max_iterations|positive"),
        ({"max_iterations": True}, "max_iterations|int"),
        ({"on_cycle_error": "stop"}, "on_cycle_error"),
        ({"starting_cash": 10000}, "starting_cash must be a Decimal"),
        (
            {"cycle_snapshot_source": object()},
            "cycle_snapshot_source must be callable or None",
        ),
        (
            {"cycle_snapshot_sink": object()},
            "cycle_snapshot_sink must be callable or None",
        ),
        (
            {"paper_trade_record_sink": object()},
            "paper_trade_record_sink must be callable or None",
        ),
        (
            {"nav_snapshot_sink": object()},
            "nav_snapshot_sink must be callable or None",
        ),
    ),
)
def test_run_strategy_loop_rejects_invalid_loop_params(tmp_path, overrides, message):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    defaults = dict(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(),
        starting_cash=Decimal("10000"),
        nav_log_path=tmp_path / "nav.jsonl",
        cycle_report_log_path=tmp_path / "cycle.jsonl",
    )
    defaults.update(overrides)
    with pytest.raises(ValueError, match=message):
        run_strategy_loop(**defaults)


def test_run_strategy_loop_rejects_non_protocol_client(tmp_path):
    with pytest.raises(ValueError, match="client must be a MarketDataClient"):
        run_strategy_loop(
            client=object(),
            scan_config=scan_config(tmp_path),
            cycle_config=cycle_config(),
            starting_cash=Decimal("10000"),
            nav_log_path=None,
            cycle_report_log_path=tmp_path / "cycle.jsonl",
        )


def test_run_loop_summary_is_frozen_and_enforces_paper_flags():
    summary = RunLoopSummary(
        iterations_completed=1,
        iterations_failed=0,
        first_iteration_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        last_iteration_at=datetime(2026, 6, 16, 12, 5, tzinfo=UTC),
        last_error=None,
    )
    with pytest.raises(FrozenInstanceError):
        summary.iterations_completed = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.last_error = "x"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"iterations_completed": -1}, "iterations_completed|nonnegative"),
        ({"iterations_failed": -1}, "iterations_failed|nonnegative"),
        ({"nav_marks_skipped": -1}, "nav_marks_skipped|nonnegative"),
        (
            {
                "first_iteration_at": datetime(2026, 6, 16, 12, 5, tzinfo=UTC),
                "last_iteration_at": datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
            },
            "last_iteration_at must not be before",
        ),
        ({"paper_only": False}, "paper_only must be True"),
        ({"report_only": False}, "report_only must be True"),
        ({"last_error": "   "}, "last_error must be a nonblank"),
    ),
)
def test_run_loop_summary_rejects_invalid_state(kwargs, message):
    defaults = dict(
        iterations_completed=1,
        iterations_failed=0,
        first_iteration_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        last_iteration_at=datetime(2026, 6, 16, 12, 5, tzinfo=UTC),
        last_error=None,
    )
    defaults.update(kwargs)
    with pytest.raises(ValueError, match=message):
        RunLoopSummary(**defaults)

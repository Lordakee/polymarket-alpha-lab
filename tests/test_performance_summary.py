"""Tests for the pure performance-summary aggregator (Stage 6).

Pure arithmetic over typed tuples reconstructed by the readers. No fetch, no
api, no live surfaces. Empty inputs collapse to zeros/None.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.performance_summary import (
    PerformanceSummary,
    PerformanceSummaryConfig,
    build_performance_summary,
)
from polymarket_alpha_lab.positions import PaperNavSnapshot
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningCandidate,
    PaperProjectScreeningGateResult,
    PaperProjectScreeningQueueItem,
    PaperProjectScreeningReport,
)
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport

GENERATED_AT = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
CONFIG = PerformanceSummaryConfig(config_version="performance-summary-v1")


def _screening(generated_at: datetime) -> PaperProjectScreeningReport:
    """A minimal valid screening report (1 blocked candidate) to satisfy the
    PaperStrategyCycleReport invariant (screening must be non-None whenever
    cost_aware_report_count > 0)."""
    candidate = PaperProjectScreeningCandidate(
        market_slug="example-market",
        question="Will it resolve yes?",
        source_status="blocked_by_inputs",
        scoring_side="none",
        valid_depth=False,
        net_edge_per_share=None,
        total_cost_per_share=None,
        ask_size=None,
        edge_component=Decimal("0"),
        confidence_component=Decimal("0"),
        depth_component=Decimal("0"),
        spread_penalty=Decimal("0"),
        resolution_risk_penalty=Decimal("0"),
        cost_penalty=Decimal("0"),
        screening_score=Decimal("0"),
        screening_status="screening_blocked",
        reason_codes=("source_blocked_by_inputs",),
    )
    queue_item = PaperProjectScreeningQueueItem(
        queue_position=1,
        market_slug="example-market",
        question="Will it resolve yes?",
        research_bucket="blocked",
        screening_score=Decimal("0"),
        source_status="blocked_by_inputs",
        scoring_side="none",
        reason_codes=("source_blocked_by_inputs",),
    )
    gates = tuple(
        PaperProjectScreeningGateResult(
            gate_name=name,
            status="pass",
            reason_code=reason,
            message=msg,
            observed_value=1,
            threshold=1,
        )
        for name, reason, msg in (
            ("input_count", "source_reports_supplied", "At least one source report is supplied."),
            ("candidate_types", "source_report_types_ready", "Every candidate source is a cost-aware event strategy report."),
            ("unique_slugs", "unique_market_slugs", "Every source report has a unique market slug."),
            ("screenable_candidates", "screenable_candidates_ready", "At least one candidate can be screened."),
        )
    )
    return PaperProjectScreeningReport(
        generated_at=generated_at,
        config_version="strategy-cycle-v1",
        candidate_count=1,
        ready_count=0,
        watch_count=0,
        defer_count=0,
        blocked_count=1,
        gate_results=gates,
        candidates=(candidate,),
        queue_items=(queue_item,),
    )


def _cycle(
    generated_at: datetime,
    *,
    scan: int = 10,
    snapshot_ready: int = 2,
) -> PaperStrategyCycleReport:
    """Build a valid cycle report. When snapshot_ready > 0 a screening report is
    attached; considered is derived as snapshot_ready + blocked."""
    blocked = max(scan - snapshot_ready, 0)
    considered = snapshot_ready + blocked
    screening = _screening(generated_at) if snapshot_ready > 0 else None
    blocked_counts = (("blocked_fetch_error", blocked),) if blocked > 0 else ()
    return PaperStrategyCycleReport(
        generated_at=generated_at,
        config_version="strategy-cycle-v1",
        scan_market_count=scan,
        considered_count=considered,
        snapshot_ready_count=snapshot_ready,
        cost_aware_report_count=snapshot_ready,
        blocked_counts=blocked_counts,
        screening_report=screening,
    )


def _nav(
    marked_at: datetime,
    *,
    cash_balance: Decimal = Decimal("10000"),
    realized_pnl: Decimal = Decimal("0"),
) -> PaperNavSnapshot:
    # Empty marks -> exit_nav/midpoint_nav must equal cash_balance and
    # total_cost_basis/unrealized_exit_pnl must be 0; starting_cash must satisfy
    # the identity starting_cash == cash_balance + cost_basis - realized_pnl.
    return PaperNavSnapshot(
        marked_at=marked_at,
        starting_cash=cash_balance - realized_pnl,
        cash_balance=cash_balance,
        realized_pnl=realized_pnl,
        exit_nav=cash_balance,
        midpoint_nav=cash_balance,
        total_cost_basis=Decimal("0"),
        unrealized_exit_pnl=Decimal("0"),
        marks=(),
    )


def test_build_performance_summary_aggregates_counts_and_latest_nav():
    cycles = (
        _cycle(datetime(2026, 6, 14, 9, 0, tzinfo=UTC), scan=10, snapshot_ready=2),
        _cycle(datetime(2026, 6, 15, 9, 0, tzinfo=UTC), scan=8, snapshot_ready=3),
    )
    trades = (object(), object(), object())  # only len() is used
    snapshots = (
        _nav(datetime(2026, 6, 14, 10, 0, tzinfo=UTC), cash_balance=Decimal("10010"), realized_pnl=Decimal("10")),
        _nav(datetime(2026, 6, 15, 10, 0, tzinfo=UTC), cash_balance=Decimal("10050"), realized_pnl=Decimal("25")),
    )

    summary = build_performance_summary(
        cycles,
        trades,
        snapshots,
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert summary.cycle_count == 2
    assert summary.total_scan_market_count == 18
    assert summary.total_snapshot_ready_count == 5
    assert summary.total_cost_aware_report_count == 5
    assert summary.paper_trade_count == 3
    assert summary.nav_snapshot_count == 2
    # last_* come from the most-recent snapshot (snapshots[-1]).
    assert summary.last_exit_nav == Decimal("10050")
    assert summary.last_starting_cash == Decimal("10025")
    assert summary.total_realized_pnl == Decimal("25")
    assert summary.first_cycle_at == datetime(2026, 6, 14, 9, 0, tzinfo=UTC)
    assert summary.last_cycle_at == datetime(2026, 6, 15, 9, 0, tzinfo=UTC)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.config_version == "performance-summary-v1"
    assert summary.generated_at == GENERATED_AT


def test_build_performance_summary_empty_inputs_yield_zeros_and_none():
    summary = build_performance_summary(
        (),
        (),
        (),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert summary.cycle_count == 0
    assert summary.total_scan_market_count == 0
    assert summary.total_snapshot_ready_count == 0
    assert summary.total_cost_aware_report_count == 0
    assert summary.paper_trade_count == 0
    assert summary.nav_snapshot_count == 0
    assert summary.last_exit_nav is None
    assert summary.last_starting_cash is None
    assert summary.total_realized_pnl is None
    assert summary.first_cycle_at is None
    assert summary.last_cycle_at is None


def test_build_performance_summary_with_cycles_but_no_navs_has_span_but_none_nav():
    cycles = (_cycle(datetime(2026, 6, 14, 9, 0, tzinfo=UTC)),)

    summary = build_performance_summary(
        cycles, (), (), config=CONFIG, generated_at=GENERATED_AT
    )

    assert summary.cycle_count == 1
    assert summary.first_cycle_at == datetime(2026, 6, 14, 9, 0, tzinfo=UTC)
    assert summary.last_cycle_at == datetime(2026, 6, 14, 9, 0, tzinfo=UTC)
    assert summary.last_exit_nav is None
    assert summary.nav_snapshot_count == 0


def test_build_performance_summary_rejects_non_config_object():
    with pytest.raises(ValueError, match="config must be"):
        build_performance_summary((), (), (), config="x", generated_at=GENERATED_AT)


def test_build_performance_summary_rejects_non_datetime_generated_at():
    with pytest.raises(ValueError, match="generated_at"):
        build_performance_summary(
            (), (), (), config=CONFIG, generated_at="2026-06-14"
        )


def test_performance_summary_config_rejects_blank_version():
    with pytest.raises(ValueError, match="config_version"):
        PerformanceSummaryConfig(config_version="  ")


def test_performance_summary_config_rejects_non_string_version():
    with pytest.raises(ValueError, match="config_version"):
        PerformanceSummaryConfig(config_version=1)


def test_performance_summary_post_init_rejects_paper_only_false():
    with pytest.raises(ValueError, match="paper_only must be True"):
        PerformanceSummary(
            generated_at=GENERATED_AT,
            config_version="performance-summary-v1",
            cycle_count=0,
            total_scan_market_count=0,
            total_snapshot_ready_count=0,
            total_cost_aware_report_count=0,
            paper_trade_count=0,
            last_exit_nav=None,
            last_starting_cash=None,
            total_realized_pnl=None,
            nav_snapshot_count=0,
            first_cycle_at=None,
            last_cycle_at=None,
            paper_only=False,
        )

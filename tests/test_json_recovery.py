"""Round-trip tests for the recursive ``json_recovery.from_jsonable`` helper.

These cover the hard cases that a flat Stage 5-style coercion cannot handle:
  - ``PaperStrategyCycleReport`` with a populated nested ``screening_report``
    (full PaperProjectScreeningReport subtree) AND non-empty ``blocked_counts``
    (C2: ``tuple[tuple[str, int], ...]`` -> deep list->tuple at every level).
  - ``PaperNavSnapshot`` with a populated ``marks`` tuple of ``PaperPositionMark``
    (Decimal/datetime/optional fields).

The reports/snapshots are constructed directly (not via the live network), so
the test is deterministic. Each is serialized with ``_json_ready(asdict(...))``
(the exact path the JSONL append uses), reconstructed with ``from_jsonable``,
and compared with dataclass ``__eq__`` -- which only holds if every nested
dataclass, every C2 deep tuple, and every Decimal/datetime is reconstructed
faithfully so each validating ``__post_init__`` passes.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.positions import (
    PaperNavSnapshot,
    PaperPositionMark,
    _json_ready as nav_json_ready,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningCandidate,
    PaperProjectScreeningGateResult,
    PaperProjectScreeningQueueItem,
    PaperProjectScreeningReport,
)
from polymarket_alpha_lab.strategy_cycle import (
    PaperStrategyCycleReport,
    _json_ready as cycle_json_ready,
)


def _blocked_candidate() -> PaperProjectScreeningCandidate:
    return PaperProjectScreeningCandidate(
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


def _screening_report() -> PaperProjectScreeningReport:
    candidate = _blocked_candidate()
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
    gate_results = (
        PaperProjectScreeningGateResult(
            gate_name="input_count",
            status="pass",
            reason_code="source_reports_supplied",
            message="At least one source report is supplied.",
            observed_value=1,
            threshold=1,
        ),
        PaperProjectScreeningGateResult(
            gate_name="candidate_types",
            status="pass",
            reason_code="source_report_types_ready",
            message="Every candidate source is a cost-aware event strategy report.",
            observed_value=1,
            threshold=1,
        ),
        PaperProjectScreeningGateResult(
            gate_name="unique_slugs",
            status="pass",
            reason_code="unique_market_slugs",
            message="Every source report has a unique market slug.",
            observed_value=1,
            threshold=1,
        ),
        PaperProjectScreeningGateResult(
            gate_name="screenable_candidates",
            status="pass",
            reason_code="screenable_candidates_ready",
            message="At least one candidate can be screened.",
            observed_value=1,
            threshold=1,
        ),
    )
    return PaperProjectScreeningReport(
        generated_at=datetime(2026, 6, 14, 9, 0, tzinfo=UTC),
        config_version="strategy-cycle-v1",
        candidate_count=1,
        ready_count=0,
        watch_count=0,
        defer_count=0,
        blocked_count=1,
        gate_results=gate_results,
        candidates=(candidate,),
        queue_items=(queue_item,),
    )


def _cycle_report() -> PaperStrategyCycleReport:
    return PaperStrategyCycleReport(
        generated_at=datetime(2026, 6, 14, 9, 0, tzinfo=UTC),
        config_version="strategy-cycle-v1",
        scan_market_count=3,
        considered_count=2,
        snapshot_ready_count=1,
        cost_aware_report_count=1,
        blocked_counts=(("blocked_fetch_error", 1),),
        screening_report=_screening_report(),
    )


def _nav_snapshot() -> PaperNavSnapshot:
    mark = PaperPositionMark(
        condition_id="0xabc",
        token_id="111",
        market_slug="example-market",
        outcome_name="Yes",
        open_size=Decimal("100"),
        cost_basis=Decimal("51.4"),
        average_entry_price=Decimal("0.514"),
        order_book_captured_at=datetime(2026, 6, 14, 9, 0, tzinfo=UTC),
        order_book_snapshot_sha256="a" * 64,
        exit_filled_size=Decimal("0"),
        exit_unfilled_size=Decimal("100"),
        exit_average_price=None,
        exit_worst_price=None,
        exit_value=Decimal("0"),
        midpoint_price=None,
        midpoint_value=None,
        best_bid=None,
        best_ask=None,
        spread=None,
        slippage_estimate=None,
        mark_status="no_exit_depth",
    )
    return PaperNavSnapshot(
        marked_at=datetime(2026, 6, 14, 10, 0, tzinfo=UTC),
        starting_cash=Decimal("10000"),
        cash_balance=Decimal("9948.6"),
        realized_pnl=Decimal("0"),
        exit_nav=Decimal("9948.6"),
        midpoint_nav=None,
        total_cost_basis=Decimal("51.4"),
        unrealized_exit_pnl=Decimal("-51.4"),
        marks=(mark,),
    )


def test_from_jsonable_round_trips_cycle_report_with_nested_screening_and_blocked_counts():
    report = _cycle_report()
    row = cycle_json_ready(asdict(report))

    reconstructed = from_jsonable(PaperStrategyCycleReport, row)

    # dataclass __eq__ across the full nested tree: only holds if the recursive
    # helper rebuilt the screening subtree AND converted blocked_counts from
    # list-of-lists to tuple-of-tuples (C2) so __post_init__ passes.
    assert reconstructed == report
    assert isinstance(reconstructed, PaperStrategyCycleReport)
    assert isinstance(reconstructed.blocked_counts, tuple)
    assert all(isinstance(entry, tuple) for entry in reconstructed.blocked_counts)
    assert reconstructed.blocked_counts == (("blocked_fetch_error", 1),)
    assert reconstructed.screening_report is not None
    assert isinstance(
        reconstructed.screening_report, PaperProjectScreeningReport
    )
    # Nested dataclass tuple-of-dataclasses reconstructed as PaperProjectScreening*.
    assert isinstance(reconstructed.screening_report.candidates[0], PaperProjectScreeningCandidate)
    assert isinstance(reconstructed.screening_report.queue_items[0], PaperProjectScreeningQueueItem)
    assert isinstance(
        reconstructed.screening_report.gate_results[0],
        PaperProjectScreeningGateResult,
    )
    # reason_codes: flat list -> tuple[str, ...].
    assert isinstance(reconstructed.screening_report.candidates[0].reason_codes, tuple)
    # Decimal fields preserved as Decimal (not str).
    assert isinstance(
        reconstructed.screening_report.candidates[0].screening_score, Decimal
    )
    assert reconstructed.screening_report.candidates[0].net_edge_per_share is None


def test_from_jsonable_round_trips_nav_snapshot_with_marks():
    snapshot = _nav_snapshot()
    row = nav_json_ready(asdict(snapshot))

    reconstructed = from_jsonable(PaperNavSnapshot, row)

    # dataclass __eq__: only holds if the marks tuple-of-dataclass is rebuilt
    # (isinstance-checked by PaperNavSnapshot.__post_init__) AND every
    # Decimal/datetime/optional field is coerced.
    assert reconstructed == snapshot
    assert isinstance(reconstructed, PaperNavSnapshot)
    assert isinstance(reconstructed.marks, tuple)
    assert len(reconstructed.marks) == 1
    mark = reconstructed.marks[0]
    assert isinstance(mark, PaperPositionMark)
    assert isinstance(mark.open_size, Decimal)
    assert isinstance(mark.cost_basis, Decimal)
    assert isinstance(mark.order_book_captured_at, datetime)
    assert mark.exit_average_price is None
    assert mark.midpoint_value is None
    assert isinstance(reconstructed.exit_nav, Decimal)
    assert isinstance(reconstructed.marked_at, datetime)


def test_from_jsonable_handles_empty_blocked_counts_and_none_screening():
    report = PaperStrategyCycleReport(
        generated_at=datetime(2026, 6, 14, 9, 0, tzinfo=UTC),
        config_version="strategy-cycle-v1",
        scan_market_count=0,
        considered_count=0,
        snapshot_ready_count=0,
        cost_aware_report_count=0,
        blocked_counts=(),
        screening_report=None,
    )
    row = cycle_json_ready(asdict(report))

    reconstructed = from_jsonable(PaperStrategyCycleReport, row)

    assert reconstructed == report
    assert reconstructed.blocked_counts == ()
    assert reconstructed.screening_report is None


def test_from_jsonable_rejects_float_decimal_value():
    mark = PaperPositionMark(
        condition_id="0xabc",
        token_id="111",
        market_slug="example-market",
        outcome_name="Yes",
        open_size=Decimal("100"),
        cost_basis=Decimal("51.4"),
        average_entry_price=Decimal("0.514"),
        order_book_captured_at=datetime(2026, 6, 14, 9, 0, tzinfo=UTC),
        order_book_snapshot_sha256="a" * 64,
        exit_filled_size=Decimal("0"),
        exit_unfilled_size=Decimal("100"),
        exit_average_price=None,
        exit_worst_price=None,
        exit_value=Decimal("0"),
        midpoint_price=None,
        midpoint_value=None,
        best_bid=None,
        best_ask=None,
        spread=None,
        slippage_estimate=None,
        mark_status="no_exit_depth",
    )
    row = nav_json_ready(asdict(PaperNavSnapshot(
        marked_at=datetime(2026, 6, 14, 10, 0, tzinfo=UTC),
        starting_cash=Decimal("10000"),
        cash_balance=Decimal("9948.6"),
        realized_pnl=Decimal("0"),
        exit_nav=Decimal("9948.6"),
        midpoint_nav=None,
        total_cost_basis=Decimal("51.4"),
        unrealized_exit_pnl=Decimal("-51.4"),
        marks=(mark,),
    )))
    # Corrupt a Decimal field to a float; the helper must reject floats.
    row["exit_nav"] = 9948.6

    with pytest.raises(ValueError, match="float"):
        from_jsonable(PaperNavSnapshot, row)


def test_from_jsonable_deeply_nested_blocked_counts_preserves_multiple_entries():
    """C2 hard case: multiple blocked statuses -> tuple-of-tuples, sorted."""
    report = PaperStrategyCycleReport(
        generated_at=datetime(2026, 6, 14, 9, 0, tzinfo=UTC),
        config_version="strategy-cycle-v1",
        scan_market_count=5,
        considered_count=5,
        snapshot_ready_count=1,
        cost_aware_report_count=1,
        blocked_counts=(
            ("blocked_fetch_error", 2),
            ("blocked_non_binary_market", 2),
        ),
        screening_report=_screening_report(),
    )
    row = cycle_json_ready(asdict(report))

    reconstructed = from_jsonable(PaperStrategyCycleReport, row)

    assert reconstructed == report
    # JSON serialized blocked_counts as a list of lists; reconstruction must
    # yield tuple-of-tuples (not tuple-of-lists) so _normalize_blocked_counts
    # accepts every entry.
    assert reconstructed.blocked_counts == (
        ("blocked_fetch_error", 2),
        ("blocked_non_binary_market", 2),
    )
    for status, count in reconstructed.blocked_counts:
        assert isinstance(status, str)
        assert isinstance(count, int)

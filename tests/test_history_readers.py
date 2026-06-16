"""Reader tests for PaperStrategyCycleLog.read and PaperNavLog.read (Stage 6).

These exercise the JSONL ``read()`` staticmethods end-to-end: append a fully
populated report/snapshot, read it back, and assert dataclass ``__eq__``. This
catches that the readers wire ``json_recovery.from_jsonable`` correctly
(reconstructing the nested validating tree) and handle blank lines / order /
empty files / non-JSON lines.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.positions import (
    PaperNavLog,
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
    PaperStrategyCycleLog,
    PaperStrategyCycleReport,
    _json_ready as cycle_json_ready,
)


def _screening() -> PaperProjectScreeningReport:
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
    gates = (
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
        gate_results=gates,
        candidates=(candidate,),
        queue_items=(queue_item,),
    )


def _cycle_report(generated_at: datetime) -> PaperStrategyCycleReport:
    return PaperStrategyCycleReport(
        generated_at=generated_at,
        config_version="strategy-cycle-v1",
        scan_market_count=3,
        considered_count=2,
        snapshot_ready_count=1,
        cost_aware_report_count=1,
        blocked_counts=(("blocked_fetch_error", 1),),
        screening_report=_screening(),
    )


def _nav_snapshot(marked_at: datetime) -> PaperNavSnapshot:
    mark = PaperPositionMark(
        condition_id="0xabc",
        token_id="111",
        market_slug="example-market",
        outcome_name="Yes",
        open_size=Decimal("100"),
        cost_basis=Decimal("51.4"),
        average_entry_price=Decimal("0.514"),
        order_book_captured_at=marked_at,
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
        marked_at=marked_at,
        starting_cash=Decimal("10000"),
        cash_balance=Decimal("9948.6"),
        realized_pnl=Decimal("0"),
        exit_nav=Decimal("9948.6"),
        midpoint_nav=None,
        total_cost_basis=Decimal("51.4"),
        unrealized_exit_pnl=Decimal("-51.4"),
        marks=(mark,),
    )


def test_strategy_cycle_log_read_round_trips_fully_populated_report(tmp_path):
    log = PaperStrategyCycleLog(path=tmp_path / "cycle.jsonl")
    report = _cycle_report(datetime(2026, 6, 14, 9, 0, tzinfo=UTC))
    log.append(report)

    (read_report,) = PaperStrategyCycleLog.read(log.path)

    assert read_report == report
    assert isinstance(read_report.screening_report, PaperProjectScreeningReport)


def test_strategy_cycle_log_read_round_trips_report_without_screening(tmp_path):
    log = PaperStrategyCycleLog(path=tmp_path / "cycle.jsonl")
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
    log.append(report)

    (read_report,) = PaperStrategyCycleLog.read(log.path)

    assert read_report == report
    assert read_report.screening_report is None


def test_strategy_cycle_log_read_preserves_order_and_skips_blank_lines(tmp_path):
    log = PaperStrategyCycleLog(path=tmp_path / "cycle.jsonl")
    first = _cycle_report(datetime(2026, 6, 14, 9, 0, tzinfo=UTC))
    second = _cycle_report(datetime(2026, 6, 15, 9, 0, tzinfo=UTC))
    log.append(first)
    log.append(second)

    # Inject blank lines around the records.
    original = log.path.read_text(encoding="utf-8")
    log.path.write_text(f"\n   \n{original}\n\n", encoding="utf-8")

    first_read, second_read = PaperStrategyCycleLog.read(log.path)
    assert first_read == first
    assert second_read == second


def test_strategy_cycle_log_read_returns_empty_tuple_for_empty_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")

    assert PaperStrategyCycleLog.read(path) == ()


def test_strategy_cycle_log_read_rejects_non_json_line_with_line_number(tmp_path):
    path = tmp_path / "cycle.jsonl"
    path.write_text("not json at all\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        PaperStrategyCycleLog.read(path)


def test_nav_log_read_round_trips_fully_populated_snapshot(tmp_path):
    log = PaperNavLog(path=tmp_path / "nav.jsonl")
    snapshot = _nav_snapshot(datetime(2026, 6, 14, 10, 0, tzinfo=UTC))
    log.append(snapshot)

    (read_snapshot,) = PaperNavLog.read(log.path)

    assert read_snapshot == snapshot
    assert isinstance(read_snapshot.marks[0], PaperPositionMark)
    assert isinstance(read_snapshot.marks[0].open_size, Decimal)


def test_nav_log_read_preserves_order_and_skips_blank_lines(tmp_path):
    log = PaperNavLog(path=tmp_path / "nav.jsonl")
    first = _nav_snapshot(datetime(2026, 6, 14, 10, 0, tzinfo=UTC))
    second = _nav_snapshot(datetime(2026, 6, 15, 10, 0, tzinfo=UTC))
    log.append(first)
    log.append(second)

    first_read, second_read = PaperNavLog.read(log.path)
    assert first_read == first
    assert second_read == second


def test_nav_log_read_returns_empty_tuple_for_empty_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")

    assert PaperNavLog.read(path) == ()


def test_nav_log_read_rejects_non_json_line_with_line_number(tmp_path):
    path = tmp_path / "nav.jsonl"
    path.write_text("garbage\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        PaperNavLog.read(path)

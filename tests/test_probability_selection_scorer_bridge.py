from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.autonomous_market_scorer import (
    build_autonomous_market_scorer_report,
)
from polymarket_alpha_lab.paper_probability_selection_summary import (
    PaperProbabilitySelectionSummaryReport,
    PaperProbabilitySelectionSummaryRow,
)
from tests.test_autonomous_market_scorer import _pass_gate_report


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)


class SelectionSummaryReportSubclass(PaperProbabilitySelectionSummaryReport):
    pass


class SelectionSummaryRowSubclass(PaperProbabilitySelectionSummaryRow):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _bridge_module():
    from polymarket_alpha_lab import probability_selection_scorer_bridge

    return probability_selection_scorer_bridge


def _ready_row(
    *,
    queue_rank: int = 1,
    market_slug: str = "event-alpha",
    question: str = "Will event-alpha resolve yes?",
    side: str = "yes",
    recommendation_score: Decimal = d("0.200000"),
    net_probability_edge: Decimal = d("0.100000"),
    executable_paper_shares: Decimal = d("15.000000"),
    reason_codes: tuple[str, ...] = ("source_edge", "cost_stress_passed"),
) -> PaperProbabilitySelectionSummaryRow:
    return PaperProbabilitySelectionSummaryRow(
        queue_rank=queue_rank,
        market_slug=market_slug,
        question=question,
        side=side,
        action="recommend",
        recommendation_score=recommendation_score,
        net_probability_edge=net_probability_edge,
        executable_paper_shares=executable_paper_shares,
        recommended_next_step="research_review",
        selection_status="ready",
        stress_scenario_count=2,
        stress_pass_count=2,
        stress_watch_count=0,
        stress_fail_count=0,
        worst_stressed_net_probability_edge=d("0.050000"),
        reason_codes=reason_codes,
    )


def _watch_row() -> PaperProbabilitySelectionSummaryRow:
    return PaperProbabilitySelectionSummaryRow(
        queue_rank=2,
        market_slug="event-beta",
        question="Will event-beta resolve no?",
        side="no",
        action="watch",
        recommendation_score=d("0.040000"),
        net_probability_edge=d("0.030000"),
        executable_paper_shares=d("7.000000"),
        recommended_next_step="await_fresh_context",
        selection_status="watch",
        stress_scenario_count=1,
        stress_pass_count=0,
        stress_watch_count=1,
        stress_fail_count=0,
        worst_stressed_net_probability_edge=d("0.020000"),
        reason_codes=("market_context_stale", "source_next_step_await_fresh_context"),
    )


def _report(
    rows: tuple[PaperProbabilitySelectionSummaryRow, ...],
) -> PaperProbabilitySelectionSummaryReport:
    return PaperProbabilitySelectionSummaryReport(
        generated_at=GENERATED_AT,
        config_version="paper-probability-selection-summary-v0",
        source_queue_config_version="probability-recommendation-queue-v0",
        source_cost_stress_config_version="paper-cost-stress-v0",
        queue_count=len(rows),
        ready_count=sum(1 for row in rows if row.selection_status == "ready"),
        watch_count=sum(1 for row in rows if row.selection_status == "watch"),
        blocked_count=sum(1 for row in rows if row.selection_status == "blocked"),
        missing_stress_count=sum(1 for row in rows if row.stress_scenario_count == 0),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def _report_reason_codes(
    rows: tuple[PaperProbabilitySelectionSummaryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_probability_queue_rows",)
    if any(row.stress_scenario_count == 0 for row in rows):
        return ("missing_cost_stress",)
    if any(row.selection_status == "blocked" for row in rows):
        return ("blocked_selection_rows_present",)
    if any(row.selection_status == "watch" for row in rows):
        return ("watch_selection_rows_present",)
    return ("ready_selection_rows_present",)


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("market_data must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, tuple):
        for item in value:
            _assert_no_floats(item)


def test_bridge_converts_selection_summary_rows_to_scorer_market_data() -> None:
    bridge = _bridge_module()
    ready = _ready_row()
    watch = _watch_row()
    report = _report((ready, watch))

    market_data = bridge.paper_probability_selection_summary_report_to_market_data(
        report,
    )

    assert type(market_data) is tuple
    assert market_data == (
        {
            "condition_id": "selection_summary:event-alpha:yes",
            "market_slug": "event-alpha",
            "question": "Will event-alpha resolve yes?",
            "scoring_side": "yes",
            "confidence_score": d("0.200000"),
            "edge_score": d("0.100000"),
            "recommended_notional": d("15.000000"),
            "selection_status": "ready",
            "reason_codes": ("cost_stress_passed", "source_edge"),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "condition_id": "selection_summary:event-beta:no",
            "market_slug": "event-beta",
            "question": "Will event-beta resolve no?",
            "scoring_side": "no",
            "confidence_score": d("0.040000"),
            "edge_score": d("0.030000"),
            "recommended_notional": d("7.000000"),
            "selection_status": "watch",
            "reason_codes": (
                "market_context_stale",
                "source_next_step_await_fresh_context",
            ),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    assert market_data[0]["confidence_score"] is ready.recommendation_score
    assert market_data[0]["edge_score"] is ready.net_probability_edge
    assert market_data[0]["recommended_notional"] is ready.executable_paper_shares
    _assert_no_floats(market_data)


def test_bridge_market_data_is_accepted_by_autonomous_market_scorer() -> None:
    bridge = _bridge_module()
    report = _report((_ready_row(), _watch_row()))
    market_data = bridge.paper_probability_selection_summary_report_to_market_data(
        report,
    )

    scorer_report = build_autonomous_market_scorer_report(
        gate_report=_pass_gate_report(),
        generated_at=GENERATED_AT,
        market_data=market_data,
    )

    assert [row.condition_id for row in scorer_report.score_rows] == [
        "selection_summary:event-alpha:yes",
        "selection_summary:event-beta:no",
    ]
    assert [row.scoring_side for row in scorer_report.score_rows] == ["yes", "no"]
    assert [row.score_status for row in scorer_report.score_rows] == [
        "scored",
        "skipped",
    ]
    assert scorer_report.score_rows[0].confidence_score == d("0.200000")
    assert scorer_report.score_rows[0].edge_score == d("0.100000")
    assert scorer_report.score_rows[0].recommended_notional == d("15.000000")
    assert scorer_report.score_rows[1].recommended_notional == d("0.000000")


def test_bridge_returns_empty_market_data_for_empty_report() -> None:
    bridge = _bridge_module()

    assert bridge.paper_probability_selection_summary_report_to_market_data(
        _report(()),
    ) == ()


def test_bridge_rejects_wrong_report_types_and_subclasses() -> None:
    bridge = _bridge_module()

    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryReport"):
        bridge.paper_probability_selection_summary_report_to_market_data(object())

    report = _report((_ready_row(),))
    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryReport"):
        bridge.paper_probability_selection_summary_report_to_market_data(
            SelectionSummaryReportSubclass(**report.__dict__),
        )


def test_bridge_rejects_non_exact_selection_rows() -> None:
    bridge = _bridge_module()
    row = _ready_row()
    report = _report((row,))
    object.__setattr__(
        report,
        "rows",
        (SelectionSummaryRowSubclass(**row.__dict__),),
    )

    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryRow"):
        bridge.paper_probability_selection_summary_report_to_market_data(report)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_bridge_rejects_unsafe_report_flags(flag_name: str) -> None:
    bridge = _bridge_module()
    report = _report((_ready_row(),))
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        bridge.paper_probability_selection_summary_report_to_market_data(report)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_bridge_rejects_unsafe_row_flags(flag_name: str) -> None:
    bridge = _bridge_module()
    row = _ready_row()
    report = _report((row,))
    object.__setattr__(row, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        bridge.paper_probability_selection_summary_report_to_market_data(report)


@pytest.mark.parametrize(
    "field_name",
    (
        "recommendation_score",
        "net_probability_edge",
        "executable_paper_shares",
        "worst_stressed_net_probability_edge",
    ),
)
def test_bridge_rejects_float_market_data_quantities(field_name: str) -> None:
    bridge = _bridge_module()
    row = _ready_row()
    report = _report((row,))
    object.__setattr__(row, field_name, 0.1)

    with pytest.raises(ValueError, match=field_name):
        bridge.paper_probability_selection_summary_report_to_market_data(report)


def test_bridge_rejects_float_values_anywhere_in_report_tree() -> None:
    bridge = _bridge_module()
    report = _report((_ready_row(),))
    object.__setattr__(report, "queue_count", 1.0)

    with pytest.raises(ValueError, match="queue_count"):
        bridge.paper_probability_selection_summary_report_to_market_data(report)

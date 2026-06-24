from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal import (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION,
    PaperAutonomousAllocationProposalReasonCodeCount,
    PaperAutonomousAllocationProposalReport,
    PaperAutonomousAllocationProposalSourceQueueSummary,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics import (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_CONFIG_VERSION,
    PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow,
    PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow,
    PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    PaperAutonomousAllocationProposalDbHistoryMetricsReport,
    PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary,
    build_paper_autonomous_allocation_proposal_db_history_metrics_report,
)
from polymarket_alpha_lab.paper_recommendation_allocation import (
    PaperRecommendationAllocationReport,
    PaperRecommendationAllocationRow,
)


NOW = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)
T1 = datetime(2026, 6, 24, 9, 0, tzinfo=UTC)
T2 = datetime(2026, 6, 24, 10, 0, tzinfo=UTC)
T3 = datetime(2026, 6, 24, 11, 0, tzinfo=UTC)
NON_UTC = datetime(2026, 6, 24, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"))


def _reason_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PaperAutonomousAllocationProposalReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperAutonomousAllocationProposalReasonCodeCount(
            reason_code=reason_code,
            report_count=report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _proposal_reason_codes(
    allocation_report: PaperRecommendationAllocationReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if allocation_report.allocated_count + allocation_report.capped_count == 0:
        if allocation_report.non_recommend_count == 0:
            reason_codes.append("no_allocated_or_capped_rows")
    if allocation_report.capped_count > 0:
        reason_codes.append("allocation_capped")
    if allocation_report.no_budget_count > 0:
        reason_codes.append("allocation_no_budget")
    if allocation_report.non_recommend_count > 0:
        reason_codes.append("allocation_non_recommend")
    if allocation_report.skipped_count > 0:
        reason_codes.append("allocation_skipped")
    if not reason_codes:
        reason_codes.append("paper_autonomous_allocation_proposal_passed")
    return tuple(sorted(set(reason_codes)))


def _proposal_status(reason_codes: tuple[str, ...]) -> str:
    if "no_allocated_or_capped_rows" in reason_codes:
        return "blocked"
    if reason_codes != ("paper_autonomous_allocation_proposal_passed",):
        return "watch"
    return "pass"


def _recommended_next_step(proposal_status: str) -> str:
    return {
        "pass": "review_paper_autonomous_allocation_proposal",
        "watch": "hold_paper_autonomous_allocation_proposal",
        "blocked": "block_paper_autonomous_allocation_proposal",
    }[proposal_status]


def _row(
    *,
    market_slug: str,
    side: str = "yes",
    score: Decimal = d("0.900000"),
    net_probability_edge: Decimal | None = None,
    requested: Decimal,
    allocated: Decimal,
    cap_status: str = "allocated",
    reason_codes: tuple[str, ...] = ("selected_by_policy",),
    event_id: str | None = None,
    theme_id: str | None = None,
    correlation_group: str | None = None,
) -> PaperRecommendationAllocationRow:
    action = "watch" if cap_status == "non_recommend" else "recommend"
    return PaperRecommendationAllocationRow(
        market_slug=market_slug,
        side=side,
        action=action,
        recommendation_score=score,
        net_probability_edge=net_probability_edge,
        executable_paper_shares=requested,
        side_price=ONE,
        market_implied_probability=ONE,
        event_id=event_id,
        theme_id=theme_id,
        correlation_group=correlation_group,
        requested_paper_notional=requested,
        allocated_paper_notional=allocated,
        allocated_paper_shares=allocated,
        cap_status=cap_status,
        reason_codes=reason_codes,
    )


def _row_sort_key(
    row: PaperRecommendationAllocationRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    candidate_edge = (
        row.recommendation_score
        if row.recommendation_score is not None
        else row.net_probability_edge
    )
    assert candidate_edge is not None
    return (
        -candidate_edge,
        -(row.net_probability_edge if row.net_probability_edge is not None else ZERO),
        -row.executable_paper_shares,
        row.market_slug,
        row.side,
    )


def _allocation_report(
    *,
    generated_at: datetime,
    rows: tuple[PaperRecommendationAllocationRow, ...],
    total_paper_budget: Decimal = d("100.000000"),
) -> PaperRecommendationAllocationReport:
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    total_requested = _q(
        sum((row.requested_paper_notional for row in sorted_rows), ZERO),
    )
    total_allocated = _q(
        sum((row.allocated_paper_notional for row in sorted_rows), ZERO),
    )
    return PaperRecommendationAllocationReport(
        generated_at=generated_at,
        config_version="allocation-v0",
        input_count=len(sorted_rows),
        row_count=len(sorted_rows),
        allocated_count=sum(1 for row in sorted_rows if row.cap_status == "allocated"),
        capped_count=sum(1 for row in sorted_rows if row.cap_status == "capped"),
        no_budget_count=sum(1 for row in sorted_rows if row.cap_status == "no_budget"),
        non_recommend_count=sum(
            1 for row in sorted_rows if row.cap_status == "non_recommend"
        ),
        skipped_count=sum(1 for row in sorted_rows if row.cap_status == "skipped"),
        total_requested_paper_notional=total_requested,
        total_allocated_paper_notional=total_allocated,
        remaining_paper_budget=_q(total_paper_budget - total_allocated),
        total_paper_budget=total_paper_budget,
        max_paper_notional_per_market=d("100.000000"),
        max_paper_notional_per_event=d("100.000000"),
        max_paper_notional_per_theme=d("100.000000"),
        max_paper_notional_per_correlation_group=d("100.000000"),
        rows=sorted_rows,
    )


def _proposal_report(
    *,
    generated_at: datetime,
    rows: tuple[PaperRecommendationAllocationRow, ...],
    total_paper_budget: Decimal = d("100.000000"),
) -> PaperAutonomousAllocationProposalReport:
    allocation_report = _allocation_report(
        generated_at=generated_at,
        rows=rows,
        total_paper_budget=total_paper_budget,
    )
    reason_codes = _proposal_reason_codes(allocation_report)
    proposal_status = _proposal_status(reason_codes)
    return PaperAutonomousAllocationProposalReport(
        generated_at=generated_at,
        config_version=DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION,
        proposal_status=proposal_status,
        recommended_next_step=_recommended_next_step(proposal_status),
        reason_code_counts=_reason_counts(reason_codes),
        reason_codes=reason_codes,
        screening_gate_config_version="paper-autonomous-screening-decision-support-gate-v0",
        screening_gate_generated_at=generated_at,
        screening_gate_status="pass",
        screening_gate_recommended_next_step=(
            "advance_paper_autonomous_screening_recommendations"
        ),
        queue_priority_generated_at=generated_at,
        queue_risk_generated_at=generated_at,
        queue_risk_config_version="action-gated-queue-risk-v0",
        queue_risk_status="pass",
        queue_risk_recommended_next_step="advance_action_gated_strategy_queue",
        source_queue_count=1,
        source_queue_summaries=(
            PaperAutonomousAllocationProposalSourceQueueSummary(
                source_generated_at=generated_at,
                config_version="action-gated-queue-v0",
                source_config_version="paper-recommendation-cycle-action-gate-v0",
                action_status="research_ready",
                queue_count=allocation_report.input_count,
                ready_count=allocation_report.input_count,
                watch_count=0,
                blocked_count=0,
                total_ready_notional=allocation_report.total_requested_paper_notional,
                allocation_input_count=allocation_report.input_count,
            ),
        ),
        allocation_config_version=allocation_report.config_version,
        allocation_input_count=allocation_report.input_count,
        allocation_report=allocation_report,
    )


def _first_report() -> PaperAutonomousAllocationProposalReport:
    return _proposal_report(
        generated_at=T1,
        rows=(
            _row(
                market_slug="alpha",
                score=d("0.900000"),
                requested=d("5.000000"),
                allocated=d("5.000000"),
                net_probability_edge=d("0.100000"),
                event_id="event-1",
                theme_id="theme-a",
                correlation_group="group-a",
            ),
        ),
    )


def _previous_report() -> PaperAutonomousAllocationProposalReport:
    return _proposal_report(
        generated_at=T2,
        rows=(
            _row(
                market_slug="alpha",
                score=d("0.900000"),
                requested=d("8.000000"),
                allocated=d("8.000000"),
                net_probability_edge=d("0.100000"),
            ),
            _row(
                market_slug="beta",
                side="no",
                score=d("0.800000"),
                requested=d("6.000000"),
                allocated=d("6.000000"),
            ),
            _row(
                market_slug="old",
                score=d("0.700000"),
                requested=d("4.000000"),
                allocated=d("4.000000"),
                net_probability_edge=d("0.200000"),
            ),
        ),
    )


def _latest_report() -> PaperAutonomousAllocationProposalReport:
    return _proposal_report(
        generated_at=T3,
        rows=(
            _row(
                market_slug="alpha",
                score=d("0.900000"),
                requested=d("10.000000"),
                allocated=d("10.000000"),
                net_probability_edge=d("0.100000"),
                event_id="event-1",
                theme_id="theme-a",
                correlation_group="group-a",
            ),
            _row(
                market_slug="beta",
                side="no",
                score=d("0.800000"),
                requested=d("20.000000"),
                allocated=d("20.000000"),
                event_id="event-1",
                theme_id="theme-b",
                correlation_group="group-a",
            ),
            _row(
                market_slug="gamma",
                score=d("0.700000"),
                requested=d("30.000000"),
                allocated=d("15.000000"),
                cap_status="capped",
                reason_codes=(
                    "capped",
                    "correlation_cap",
                    "event_cap",
                    "market_cap",
                    "theme_cap",
                ),
                event_id="event-2",
                theme_id="theme-b",
            ),
            _row(
                market_slug="delta",
                score=d("0.600000"),
                requested=d("5.000000"),
                allocated=ZERO,
                cap_status="no_budget",
                reason_codes=("no_budget", "total_budget_cap"),
            ),
            _row(
                market_slug="epsilon",
                score=d("0.500000"),
                requested=d("7.000000"),
                allocated=ZERO,
                cap_status="non_recommend",
                reason_codes=("non_recommend",),
            ),
            _row(
                market_slug="zeta",
                score=d("0.400000"),
                requested=d("9.000000"),
                allocated=ZERO,
                cap_status="skipped",
                reason_codes=("nonpositive_edge", "skipped"),
            ),
        ),
    )


def _empty_metrics_report(
    **overrides: object,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsReport:
    values = {
        "generated_at": NOW,
        "config_version": (
            DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_CONFIG_VERSION
        ),
        "source_report_count": 0,
        "first_report_generated_at": None,
        "latest_report_generated_at": None,
        "latest_proposal_status": None,
        "latest_allocation_input_count": None,
        "latest_allocation_row_count": None,
        "latest_allocated_count": None,
        "latest_capped_count": None,
        "latest_no_budget_count": None,
        "latest_non_recommend_count": None,
        "latest_skipped_count": None,
        "first_allocated_count": None,
        "delta_allocated_count": None,
        "latest_total_requested_paper_notional": None,
        "latest_total_allocated_paper_notional": None,
        "latest_remaining_paper_budget": None,
        "latest_total_paper_budget": None,
        "latest_budget_utilization": None,
        "latest_requested_fill_ratio": None,
        "latest_allocated_row_share": None,
        "latest_capped_row_share": None,
        "latest_no_budget_row_share": None,
        "latest_non_recommend_row_share": None,
        "latest_skipped_row_share": None,
        "first_total_requested_paper_notional": None,
        "delta_total_requested_paper_notional": None,
        "first_total_allocated_paper_notional": None,
        "delta_total_allocated_paper_notional": None,
        "first_budget_utilization": None,
        "delta_budget_utilization": None,
        "first_requested_fill_ratio": None,
        "delta_requested_fill_ratio": None,
        "latest_largest_concentration_rows": (),
        "latest_cap_reason_rows": (),
        "latest_added_market_side_count": 0,
        "latest_removed_market_side_count": 0,
        "latest_persisted_market_side_count": 0,
        "latest_notional_turnover": ZERO,
        "latest_allocated_edge_count": None,
        "latest_allocated_edge_share": None,
        "latest_expected_edge_notional": None,
        "latest_expected_edge_notional_share": None,
        "source_summaries": (),
    }
    values.update(overrides)
    return PaperAutonomousAllocationProposalDbHistoryMetricsReport(**values)


def test_empty_input_yields_absent_first_latest_delta_metrics_and_empty_rows() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_report(
        (),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsConfig(),
        generated_at=NOW,
    )

    assert report.source_report_count == 0
    assert report.source_summaries == ()
    assert report.latest_largest_concentration_rows == ()
    assert report.latest_cap_reason_rows == ()

    absent_metric_fields = (
        "first_report_generated_at",
        "latest_report_generated_at",
        "latest_proposal_status",
        "latest_allocation_input_count",
        "latest_allocation_row_count",
        "latest_allocated_count",
        "latest_capped_count",
        "latest_no_budget_count",
        "latest_non_recommend_count",
        "latest_skipped_count",
        "first_allocated_count",
        "delta_allocated_count",
        "latest_total_requested_paper_notional",
        "latest_total_allocated_paper_notional",
        "latest_remaining_paper_budget",
        "latest_total_paper_budget",
        "latest_budget_utilization",
        "latest_requested_fill_ratio",
        "latest_allocated_row_share",
        "latest_capped_row_share",
        "latest_no_budget_row_share",
        "latest_non_recommend_row_share",
        "latest_skipped_row_share",
        "first_total_requested_paper_notional",
        "delta_total_requested_paper_notional",
        "first_total_allocated_paper_notional",
        "delta_total_allocated_paper_notional",
        "first_budget_utilization",
        "delta_budget_utilization",
        "first_requested_fill_ratio",
        "delta_requested_fill_ratio",
        "latest_allocated_edge_count",
        "latest_allocated_edge_share",
        "latest_expected_edge_notional",
        "latest_expected_edge_notional_share",
    )
    for field_name in absent_metric_fields:
        assert getattr(report, field_name) is None, field_name

    assert report.latest_added_market_side_count == 0
    assert report.latest_removed_market_side_count == 0
    assert report.latest_persisted_market_side_count == 0
    assert report.latest_notional_turnover == ZERO


def test_reducer_sorts_reports_and_computes_latest_snapshot_delta_and_churn() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_report(
        (_latest_report(), _first_report(), _previous_report()),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsConfig(),
        generated_at=NOW,
    )

    assert report.source_report_count == 3
    assert report.first_report_generated_at == T1
    assert report.latest_report_generated_at == T3
    assert report.latest_proposal_status == "watch"
    assert report.latest_allocation_input_count == 6
    assert report.latest_allocation_row_count == 6
    assert report.latest_allocated_count == 2
    assert report.latest_capped_count == 1
    assert report.latest_no_budget_count == 1
    assert report.latest_non_recommend_count == 1
    assert report.latest_skipped_count == 1
    assert report.latest_total_requested_paper_notional == d("81.000000")
    assert report.latest_total_allocated_paper_notional == d("45.000000")
    assert report.latest_remaining_paper_budget == d("55.000000")
    assert report.latest_total_paper_budget == d("100.000000")
    assert report.latest_budget_utilization == d("0.450000")
    assert report.latest_requested_fill_ratio == d("0.555556")
    assert report.latest_allocated_row_share == d("0.333333")
    assert report.latest_capped_row_share == d("0.166667")
    assert report.latest_no_budget_row_share == d("0.166667")
    assert report.latest_non_recommend_row_share == d("0.166667")
    assert report.latest_skipped_row_share == d("0.166667")

    assert report.first_total_requested_paper_notional == d("5.000000")
    assert report.delta_total_requested_paper_notional == d("76.000000")
    assert report.first_total_allocated_paper_notional == d("5.000000")
    assert report.delta_total_allocated_paper_notional == d("40.000000")
    assert report.first_budget_utilization == d("0.050000")
    assert report.delta_budget_utilization == d("0.400000")
    assert report.first_requested_fill_ratio == d("1.000000")
    assert report.delta_requested_fill_ratio == d("-0.444444")
    assert report.first_allocated_count == 1
    assert report.delta_allocated_count == 1

    assert tuple(summary.input_position for summary in report.source_summaries) == (
        1,
        2,
        0,
    )
    assert tuple(summary.generated_at for summary in report.source_summaries) == (
        T1,
        T2,
        T3,
    )

    assert report.latest_added_market_side_count == 1
    assert report.latest_removed_market_side_count == 1
    assert report.latest_persisted_market_side_count == 2
    assert report.latest_notional_turnover == d("35.000000")


def test_latest_concentration_cap_reason_and_edge_metrics_are_deterministic() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_report(
        (_previous_report(), _latest_report()),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsConfig(),
        generated_at=NOW,
    )

    assert [
        (
            row.group_type,
            row.group_id,
            row.allocated_paper_notional,
            row.allocated_paper_notional_share,
            row.row_count,
        )
        for row in report.latest_largest_concentration_rows
    ] == [
        ("correlation_group", "group-a", d("30.000000"), d("0.666667"), 2),
        ("event", "event-1", d("30.000000"), d("0.666667"), 2),
        ("market", "beta", d("20.000000"), d("0.444444"), 1),
        ("theme", "theme-b", d("35.000000"), d("0.777778"), 2),
    ]

    assert [
        (row.reason_code, row.row_count, row.allocated_paper_notional)
        for row in report.latest_cap_reason_rows
    ] == [
        ("capped", 1, d("15.000000")),
        ("correlation_cap", 1, d("15.000000")),
        ("event_cap", 1, d("15.000000")),
        ("market_cap", 1, d("15.000000")),
        ("no_budget", 1, ZERO),
        ("theme_cap", 1, d("15.000000")),
        ("total_budget_cap", 1, ZERO),
    ]

    assert report.latest_allocated_edge_count == 1
    assert report.latest_allocated_edge_share == d("0.500000")
    assert report.latest_expected_edge_notional == d("1.000000")
    assert report.latest_expected_edge_notional_share == d("0.022222")


def test_zero_allocated_notional_keeps_concentration_rows_with_absent_shares() -> None:
    source = _proposal_report(
        generated_at=T1,
        rows=(
            _row(
                market_slug="zero-market",
                requested=d("5.000000"),
                allocated=ZERO,
                cap_status="no_budget",
                reason_codes=("no_budget",),
                event_id="zero-event",
                theme_id="zero-theme",
                correlation_group="zero-group",
            ),
        ),
    )

    report = build_paper_autonomous_allocation_proposal_db_history_metrics_report(
        (source,),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsConfig(),
        generated_at=NOW,
    )

    assert [
        (row.group_type, row.group_id, row.allocated_paper_notional_share)
        for row in report.latest_largest_concentration_rows
    ] == [
        ("correlation_group", "zero-group", None),
        ("event", "zero-event", None),
        ("market", "zero-market", None),
        ("theme", "zero-theme", None),
    ]


def test_direct_constructor_values_are_frozen_and_validate_hard_flags_and_types() -> None:
    config = PaperAutonomousAllocationProposalDbHistoryMetricsConfig()
    concentration = PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow(
        group_type="market",
        group_id="alpha",
        allocated_paper_notional=d("1.234567"),
        allocated_paper_notional_share=d("0.123456"),
        row_count=1,
    )
    cap_reason = PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow(
        reason_code="capped",
        row_count=1,
        allocated_paper_notional=d("1.000000"),
    )
    summary = PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary(
        input_position=0,
        generated_at=NON_UTC,
        proposal_status="pass",
        allocation_input_count=1,
        allocation_row_count=1,
        allocated_count=1,
        capped_count=0,
        no_budget_count=0,
        non_recommend_count=0,
        skipped_count=0,
        total_requested_paper_notional=d("10.000000"),
        total_allocated_paper_notional=d("10.000000"),
        remaining_paper_budget=d("90.000000"),
        total_paper_budget=d("100.000000"),
        budget_utilization=d("0.100000"),
        requested_fill_ratio=d("1.000000"),
        allocated_row_share=d("1.000000"),
        capped_row_share=ZERO,
        no_budget_row_share=ZERO,
        non_recommend_row_share=ZERO,
        skipped_row_share=ZERO,
    )
    direct_report = _empty_metrics_report(generated_at=NON_UTC)

    assert config.config_version == (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_CONFIG_VERSION
    )
    assert summary.generated_at == NOW
    assert direct_report.generated_at == NOW
    assert type(concentration.allocated_paper_notional) is Decimal
    assert concentration.allocated_paper_notional == d("1.234567")

    with pytest.raises(FrozenInstanceError):
        concentration.row_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        direct_report.source_report_count = 99  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        PaperAutonomousAllocationProposalDbHistoryMetricsConfig(config_version=" v0 ")
    with pytest.raises(ValueError, match="paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(cap_reason, readonly=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="row_count"):
        replace(concentration, row_count=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        replace(summary, generated_at=datetime(2026, 6, 24, 12, 0))
    with pytest.raises(ValueError, match="total_allocated_paper_notional"):
        replace(summary, total_allocated_paper_notional=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="latest_total_allocated_paper_notional"):
        _empty_metrics_report(latest_total_allocated_paper_notional=1.0)


def test_reducer_rejects_non_exact_config_and_proposal_report_values() -> None:
    class ConfigSubclass(PaperAutonomousAllocationProposalDbHistoryMetricsConfig):
        pass

    class ProposalReportSubclass(PaperAutonomousAllocationProposalReport):
        pass

    source = _first_report()
    subclass_source = ProposalReportSubclass(**source.__dict__)

    with pytest.raises(ValueError, match="config"):
        build_paper_autonomous_allocation_proposal_db_history_metrics_report(
            (),
            config=ConfigSubclass(),
            generated_at=NOW,
        )
    with pytest.raises(ValueError, match="PaperAutonomousAllocationProposalReport"):
        build_paper_autonomous_allocation_proposal_db_history_metrics_report(
            (subclass_source,),
            config=PaperAutonomousAllocationProposalDbHistoryMetricsConfig(),
            generated_at=NOW,
        )


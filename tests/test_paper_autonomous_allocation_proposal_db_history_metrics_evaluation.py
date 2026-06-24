from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics import (
    PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow,
    PaperAutonomousAllocationProposalDbHistoryMetricsReport,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation import (
    ALLOWED_REASON_CODES,
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_CONFIG_VERSION,
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount,
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport,
    build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report,
)


NOW = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)
NOW_MINUS_1H = datetime(2026, 6, 24, 11, 0, tzinfo=UTC)
NOW_MINUS_25H = datetime(2026, 6, 23, 11, 0, tzinfo=UTC)
EASTERN = timezone(timedelta(hours=-4))
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def _q(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.000001"))


def _metrics_report(**overrides: object) -> PaperAutonomousAllocationProposalDbHistoryMetricsReport:
    values = {
        "generated_at": NOW,
        "config_version": "metrics-v0",
        "source_report_count": 3,
        "first_report_generated_at": NOW_MINUS_25H,
        "latest_report_generated_at": NOW_MINUS_1H,
        "latest_proposal_status": "pass",
        "latest_allocation_input_count": 5,
        "latest_allocation_row_count": 5,
        "latest_allocated_count": 3,
        "latest_capped_count": 0,
        "latest_no_budget_count": 0,
        "latest_non_recommend_count": 0,
        "latest_skipped_count": 0,
        "first_allocated_count": 1,
        "delta_allocated_count": 2,
        "latest_total_requested_paper_notional": d("81.000000"),
        "latest_total_allocated_paper_notional": d("45.000000"),
        "latest_remaining_paper_budget": d("55.000000"),
        "latest_total_paper_budget": d("100.000000"),
        "latest_budget_utilization": d("0.450000"),
        "latest_requested_fill_ratio": d("0.555556"),
        "latest_allocated_row_share": d("0.600000"),
        "latest_capped_row_share": ZERO,
        "latest_no_budget_row_share": ZERO,
        "latest_non_recommend_row_share": ZERO,
        "latest_skipped_row_share": ZERO,
        "first_total_requested_paper_notional": d("5.000000"),
        "delta_total_requested_paper_notional": d("76.000000"),
        "first_total_allocated_paper_notional": d("5.000000"),
        "delta_total_allocated_paper_notional": d("40.000000"),
        "first_budget_utilization": d("0.050000"),
        "delta_budget_utilization": d("0.400000"),
        "first_requested_fill_ratio": d("1.000000"),
        "delta_requested_fill_ratio": d("-0.444444"),
        "latest_largest_concentration_rows": (),
        "latest_cap_reason_rows": (),
        "latest_added_market_side_count": 0,
        "latest_removed_market_side_count": 0,
        "latest_persisted_market_side_count": 0,
        "latest_notional_turnover": d("10.000000"),
        "latest_allocated_edge_count": 2,
        "latest_allocated_edge_share": d("0.666667"),
        "latest_expected_edge_notional": d("3.000000"),
        "latest_expected_edge_notional_share": d("0.066667"),
        "source_summaries": (),
    }
    values.update(overrides)
    return PaperAutonomousAllocationProposalDbHistoryMetricsReport(**values)


def test_config_validates_hard_flags_and_thresholds() -> None:
    config = PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig()
    assert config.config_version == (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_CONFIG_VERSION
    )
    assert config.max_budget_utilization == d("0.900000")
    with pytest.raises(FrozenInstanceError):
        config.min_source_report_count = 2  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="config_version"):
        PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(
            config_version=" bad "
        )
    with pytest.raises(ValueError, match="quantized"):
        PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(
            max_budget_utilization=Decimal("0.1234567")
        )


def test_empty_metrics_yields_blocked_status() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(source_report_count=0),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        generated_at=NOW,
    )
    assert report.source_report_count == 0
    assert report.evaluation_status == "blocked"
    assert report.recommended_next_step == "block_paper_autonomous_allocation_proposal"
    assert report.reason_codes == (
        "missing_paper_autonomous_allocation_proposal_metrics_source_history",
    )


def test_pass_case_has_only_pass_reason_code_and_matching_diagnostics() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        generated_at=NOW,
    )
    assert report.evaluation_status == "pass"
    assert report.reason_codes == (
        "paper_autonomous_allocation_proposal_metrics_evaluation_passed",
    )
    diag = report.diagnostics
    assert diag.source_report_count == 3
    assert diag.latest_source_age_seconds == 3600
    assert diag.top_reason_codes == report.reason_codes
    assert diag.top_reason_code_limit == 6


def test_stale_age_triggers_watch_status() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(latest_report_generated_at=NOW_MINUS_25H),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(
            max_latest_age_seconds=3600,
        ),
        generated_at=NOW,
    )
    assert report.evaluation_status == "watch"
    assert (
        "stale_paper_autonomous_allocation_proposal_metrics_latest_report"
        in report.reason_codes
    )


def test_budget_utilization_triggers_watch_when_above_threshold() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(latest_budget_utilization=d("0.950000")),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        generated_at=NOW,
    )
    assert "metrics_budget_utilization_watch" in report.reason_codes
    assert report.diagnostics.evaluated_budget_utilization is True


def test_requested_fill_ratio_triggers_watch_when_below_threshold() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(latest_requested_fill_ratio=d("0.100000")),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        generated_at=NOW,
    )
    assert "metrics_requested_fill_ratio_watch" in report.reason_codes
    assert report.diagnostics.evaluated_requested_fill_ratio is True


def test_concentration_emits_group_specific_reason_codes() -> None:
    rows = (
        PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow(
            group_type="market",
            group_id="alpha",
            allocated_paper_notional=d("5.000000"),
            allocated_paper_notional_share=d("0.800000"),
            row_count=1,
        ),
        PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow(
            group_type="event",
            group_id="event-1",
            allocated_paper_notional=d("3.000000"),
            allocated_paper_notional_share=d("0.500000"),
            row_count=1,
        ),
    )
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(latest_largest_concentration_rows=rows),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        generated_at=NOW,
    )
    assert "metrics_concentration_market_watch" in report.reason_codes
    assert "metrics_concentration_event_watch" not in report.reason_codes
    assert report.diagnostics.largest_concentration_group_type == "market"
    assert report.diagnostics.largest_concentration_share == d("0.800000")


def test_churn_share_triggers_watch_when_above_threshold() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(
            latest_notional_turnover=d("30.000000"),
            latest_total_allocated_paper_notional=d("45.000000"),
        ),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        generated_at=NOW,
    )
    assert "metrics_churn_share_watch" in report.reason_codes


def test_edge_coverage_and_quality_trigger_watch_independently() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(
            latest_allocated_edge_share=d("0.200000"),
            latest_expected_edge_notional_share=d("0.120000"),
        ),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        generated_at=NOW,
    )
    assert "metrics_edge_coverage_watch" in report.reason_codes
    assert "metrics_edge_quality_watch" in report.reason_codes


def test_missing_notional_dependent_metrics_disable_checks() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(
            latest_total_allocated_paper_notional=None,
            latest_allocated_edge_share=None,
            latest_expected_edge_notional_share=None,
        ),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        generated_at=NOW,
    )
    assert report.evaluation_status == "pass"
    assert report.diagnostics.evaluated_churn is False
    assert report.diagnostics.evaluated_edge_coverage is False
    assert report.diagnostics.evaluated_edge_quality is False


def test_negative_age_is_rejected() -> None:
    with pytest.raises(ValueError, match="negative"):
        build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
            _metrics_report(
                latest_report_generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
            ),
            config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
            generated_at=NOW,
        )


def test_builder_rejects_non_exact_inputs() -> None:
    class MetricsSubclass(PaperAutonomousAllocationProposalDbHistoryMetricsReport):
        pass

    metrics = _metrics_report()
    subclass_metrics = MetricsSubclass(**metrics.__dict__)

    with pytest.raises(ValueError, match="config"):
        build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
            metrics,
            config="bad",
            generated_at=NOW,
        )
    with pytest.raises(ValueError, match="metrics_report"):
        build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
            subclass_metrics,
            config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
            generated_at=NOW,
        )


def test_non_utc_generated_at_is_normalized_and_naive_rejected() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        generated_at=datetime(2026, 6, 24, 8, 0, tzinfo=EASTERN),
    )
    assert report.generated_at.tzinfo == UTC

    with pytest.raises(ValueError, match="timezone-aware"):
        build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
            _metrics_report(),
            config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
            generated_at=datetime(2026, 6, 24, 12, 0),
        )


def test_reason_codes_are_sorted_unique_and_within_allowlist() -> None:
    report = build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        _metrics_report(
            latest_budget_utilization=d("0.950000"),
            latest_requested_fill_ratio=d("0.100000"),
        ),
        config=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(),
        generated_at=NOW,
    )
    assert report.reason_codes == tuple(sorted(set(report.reason_codes)))
    assert len(report.reason_codes) == len(set(report.reason_codes))
    assert set(report.reason_codes) <= set(ALLOWED_REASON_CODES)

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation import (
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics,
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount,
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row import (
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow,
    paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row,
    paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row,
)


GENERATED_AT = datetime(2026, 6, 24, 16, 0, tzinfo=UTC)
LATEST_REPORT_GENERATED_AT = datetime(2026, 6, 24, 15, 45, tzinfo=UTC)
CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0"


def d(value: str) -> Decimal:
    return Decimal(value)


def _report(
    *,
    generated_at: datetime = GENERATED_AT,
    status: str = "watch",
) -> PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport:
    return PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport(
        generated_at=generated_at,
        config_version=CONFIG_VERSION,
        evaluation_status=status,
        recommended_next_step="hold_paper_autonomous_allocation_proposal",
        source_report_count=5,
        latest_report_generated_at=LATEST_REPORT_GENERATED_AT,
        reason_code_counts=(
            PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount(
                reason_code="metrics_budget_utilization_watch",
                report_count=1,
            ),
            PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount(
                reason_code="metrics_churn_share_watch",
                report_count=1,
            ),
        ),
        reason_codes=(
            "metrics_budget_utilization_watch",
            "metrics_churn_share_watch",
        ),
        diagnostics=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics(
            evaluated_min_source_report_count=True,
            evaluated_latest_age=True,
            evaluated_budget_utilization=True,
            evaluated_requested_fill_ratio=True,
            evaluated_concentration=True,
            evaluated_churn=True,
            evaluated_edge_coverage=True,
            evaluated_edge_quality=True,
            source_report_count=5,
            latest_source_age_seconds=900,
            latest_budget_utilization=d("0.950000"),
            latest_requested_fill_ratio=d("0.450000"),
            largest_concentration_group_type="market",
            largest_concentration_share=d("0.700000"),
            churn_share=d("0.625000"),
            latest_allocated_edge_share=d("0.800000"),
            latest_expected_edge_notional_share=d("0.125000"),
            top_reason_codes=(
                "metrics_budget_utilization_watch",
                "metrics_churn_share_watch",
            ),
            top_reason_code_limit=6,
        ),
    )


def _pass_report() -> PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport:
    return PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        evaluation_status="pass",
        recommended_next_step="review_paper_autonomous_allocation_proposal",
        source_report_count=3,
        latest_report_generated_at=LATEST_REPORT_GENERATED_AT,
        reason_code_counts=(
            PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount(
                reason_code="paper_autonomous_allocation_proposal_metrics_evaluation_passed",
                report_count=1,
            ),
        ),
        reason_codes=(
            "paper_autonomous_allocation_proposal_metrics_evaluation_passed",
        ),
        diagnostics=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics(
            evaluated_min_source_report_count=True,
            evaluated_latest_age=True,
            evaluated_budget_utilization=True,
            evaluated_requested_fill_ratio=True,
            evaluated_concentration=False,
            evaluated_churn=True,
            evaluated_edge_coverage=True,
            evaluated_edge_quality=True,
            source_report_count=3,
            latest_source_age_seconds=120,
            latest_budget_utilization=d("0.500000"),
            latest_requested_fill_ratio=d("0.700000"),
            largest_concentration_group_type=None,
            largest_concentration_share=None,
            churn_share=d("0.100000"),
            latest_allocated_edge_share=d("0.900000"),
            latest_expected_edge_notional_share=d("0.040000"),
            top_reason_codes=(
                "paper_autonomous_allocation_proposal_metrics_evaluation_passed",
            ),
            top_reason_code_limit=6,
        ),
    )


def _blocked_report() -> PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport:
    return PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        evaluation_status="blocked",
        recommended_next_step="block_paper_autonomous_allocation_proposal",
        source_report_count=0,
        latest_report_generated_at=None,
        reason_code_counts=(
            PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount(
                reason_code=(
                    "missing_paper_autonomous_allocation_proposal_metrics_source_history"
                ),
                report_count=1,
            ),
        ),
        reason_codes=(
            "missing_paper_autonomous_allocation_proposal_metrics_source_history",
        ),
        diagnostics=PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics(
            evaluated_min_source_report_count=True,
            evaluated_latest_age=False,
            evaluated_budget_utilization=False,
            evaluated_requested_fill_ratio=False,
            evaluated_concentration=False,
            evaluated_churn=False,
            evaluated_edge_coverage=False,
            evaluated_edge_quality=False,
            source_report_count=0,
            latest_source_age_seconds=None,
            latest_budget_utilization=None,
            latest_requested_fill_ratio=None,
            largest_concentration_group_type=None,
            largest_concentration_share=None,
            churn_share=None,
            latest_allocated_edge_share=None,
            latest_expected_edge_notional_share=None,
            top_reason_codes=(
                "missing_paper_autonomous_allocation_proposal_metrics_source_history",
            ),
            top_reason_code_limit=6,
        ),
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_metrics_evaluation_db_row_serializes_canonical_payload_and_round_trips():
    report = _report(
        generated_at=datetime(2026, 6, 24, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    row = paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
        report,
    )

    assert type(row) is PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.generated_at.tzinfo is UTC
    assert row.config_version == CONFIG_VERSION
    assert row.evaluation_status == "watch"
    assert row.recommended_next_step == "hold_paper_autonomous_allocation_proposal"
    assert row.source_report_count == 5
    assert row.latest_report_generated_at == LATEST_REPORT_GENERATED_AT
    assert row.reason_code_counts_json == {
        "metrics_budget_utilization_watch": 1,
        "metrics_churn_share_watch": 1,
    }
    assert row.reason_codes == (
        "metrics_budget_utilization_watch",
        "metrics_churn_share_watch",
    )
    assert row.diagnostics_json == {
        "evaluated_min_source_report_count": True,
        "evaluated_latest_age": True,
        "evaluated_budget_utilization": True,
        "evaluated_requested_fill_ratio": True,
        "evaluated_concentration": True,
        "evaluated_churn": True,
        "evaluated_edge_coverage": True,
        "evaluated_edge_quality": True,
        "source_report_count": 5,
        "latest_source_age_seconds": 900,
        "latest_budget_utilization": "0.950000",
        "latest_requested_fill_ratio": "0.450000",
        "largest_concentration_group_type": "market",
        "largest_concentration_share": "0.700000",
        "churn_share": "0.625000",
        "latest_allocated_edge_share": "0.800000",
        "latest_expected_edge_notional_share": "0.125000",
        "top_reason_codes": [
            "metrics_budget_utilization_watch",
            "metrics_churn_share_watch",
        ],
        "top_reason_code_limit": 6,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert row.payload_json["generated_at"] == "2026-06-24T16:00:00+00:00"
    assert row.payload_json["latest_report_generated_at"] == (
        "2026-06-24T15:45:00+00:00"
    )
    assert row.payload_json["diagnostics"]["latest_budget_utilization"] == "0.950000"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.diagnostics_json)

    assert (
        paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row(
            row,
        )
        == report
    )


def test_metrics_evaluation_db_row_hash_is_deterministic_for_equivalent_reports():
    report = _report()
    same_report = PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport(
        **report.__dict__,
    )

    first = paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
        report,
    )
    second = paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
        same_report,
    )

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json


def test_metrics_evaluation_db_row_rejects_wrong_report_type_and_subclasses():
    with pytest.raises(ValueError, match="MetricsEvaluationReport"):
        paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
            object(),
        )

    report = _report()
    with pytest.raises(TypeError, match="does not support subclassing"):
        class EvaluationReportSubclass(
            PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport,
        ):
            pass

        EvaluationReportSubclass(**report.__dict__)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_metrics_evaluation_db_row_rejects_false_report_flags(flag_name: str):
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
            report,
        )


@pytest.mark.parametrize("report_factory", (_pass_report, _blocked_report))
def test_metrics_evaluation_db_row_round_trips_boundary_statuses(report_factory):
    report = report_factory()

    row = paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
        report,
    )

    assert row.evaluation_status == report.evaluation_status
    assert row.latest_report_generated_at == report.latest_report_generated_at
    assert (
        paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row(
            row,
        )
        == report
    )


def test_metrics_evaluation_db_row_rejects_malformed_stored_payload():
    row = paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
        _report(),
    )
    malformed = PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow(
        report_sha256="a" * 64,
        generated_at=row.generated_at,
        config_version=row.config_version,
        evaluation_status=row.evaluation_status,
        recommended_next_step=row.recommended_next_step,
        source_report_count=row.source_report_count,
        latest_report_generated_at=row.latest_report_generated_at,
        reason_code_counts_json=row.reason_code_counts_json,
        reason_codes=row.reason_codes,
        diagnostics_json=row.diagnostics_json,
        payload_json={**row.payload_json, "readonly": False},
    )

    with pytest.raises(ValueError, match="readonly"):
        paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row(
            malformed,
        )


def test_metrics_evaluation_db_row_wraps_payload_recovery_errors_as_value_error():
    row = paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
        _report(),
    )
    malformed = PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow(
        report_sha256="a" * 64,
        generated_at=row.generated_at,
        config_version=row.config_version,
        evaluation_status=row.evaluation_status,
        recommended_next_step=row.recommended_next_step,
        source_report_count=row.source_report_count,
        latest_report_generated_at=row.latest_report_generated_at,
        reason_code_counts_json=row.reason_code_counts_json,
        reason_codes=row.reason_codes,
        diagnostics_json=row.diagnostics_json,
        payload_json={
            key: value
            for key, value in row.payload_json.items()
            if key != "diagnostics"
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row(
            malformed,
        )


def test_metrics_evaluation_db_row_validates_row_shape_and_summary_parity():
    row = paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
        _report(),
    )

    with pytest.raises(FrozenInstanceError):
        row.evaluation_status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="report_sha256"):
        replace(row, report_sha256="bad")

    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})

    with pytest.raises(ValueError, match="summary columns"):
        paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row(
            replace(row, source_report_count=999),
        )

    with pytest.raises(ValueError, match="diagnostics_json"):
        replace(
            row,
            diagnostics_json={
                **row.diagnostics_json,
                "latest_budget_utilization": "0.100000",
            },
        )

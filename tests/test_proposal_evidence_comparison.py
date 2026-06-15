import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tests.test_forecast_evidence import sample_observations
from tests.test_proposal_review_dossier_batch import (
    complete_dossier_fixture,
    incomplete_dossier_fixture,
    unstable_dossier_fixture,
)
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceBucket,
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceGateResult,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison import (
    DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT,
    GATE_NAMES,
    TradeProposalEvidenceComparisonConfig,
    TradeProposalEvidenceComparisonFindingRow,
    TradeProposalEvidenceComparisonGateResult,
    TradeProposalEvidenceComparisonLog,
    TradeProposalEvidenceComparisonMetricRow,
    TradeProposalEvidenceComparisonReport,
    TradeProposalEvidenceComparisonSourceRow,
    build_trade_proposal_evidence_comparison_report,
)
from polymarket_alpha_lab.proposal_review_dossier_batch import (
    TradeProposalReviewDossierBatchConfig,
    TradeProposalReviewDossierBatchGateResult,
    TradeProposalReviewDossierBatchReport,
    TradeProposalReviewDossierBatchSourceSummary,
    build_trade_proposal_review_dossier_batch_report,
)


def ready_forecast_fixture():
    return build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(
            config_version="forecast-v1",
            min_probability_observations=1,
            min_edge_observations=1,
            max_mean_probability_loss=Decimal("1.0000"),
            max_bucket_error=Decimal("1.0000"),
            max_mean_edge_gap_ratio=Decimal("1.0000"),
            min_positive_edge_hit_rate=Decimal("0.0000"),
            max_residual_exposure_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 10, 12, tzinfo=UTC),
    )


def unstable_forecast_fixture():
    return build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(
            config_version="forecast-v1",
            min_probability_observations=1,
            min_edge_observations=1,
            max_mean_probability_loss=Decimal("0.0000"),
            max_bucket_error=Decimal("0.0000"),
            max_mean_edge_gap_ratio=Decimal("0.0000"),
            min_positive_edge_hit_rate=Decimal("1.0000"),
            max_residual_exposure_ratio=Decimal("0.0000"),
        ),
        generated_at=datetime(2026, 9, 10, 12, tzinfo=UTC),
    )


def empty_forecast_fixture():
    return build_paper_forecast_evidence_report(
        [],
        config=PaperForecastEvidenceConfig(config_version="forecast-v1"),
        generated_at=datetime(2026, 9, 10, 12, tzinfo=UTC),
    )


def insufficient_forecast_fixture():
    return build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(
            config_version="forecast-v1",
            min_probability_observations=4,
            min_edge_observations=4,
            max_mean_probability_loss=Decimal("1.0000"),
            max_bucket_error=Decimal("1.0000"),
            max_mean_edge_gap_ratio=Decimal("1.0000"),
            min_positive_edge_hit_rate=Decimal("0.0000"),
            max_residual_exposure_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 10, 12, tzinfo=UTC),
    )


def ready_dossier_batch_fixture():
    return build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=1)],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
        ),
        generated_at=datetime(2026, 9, 10, 13, tzinfo=UTC),
    )


def incomplete_dossier_batch_fixture():
    return build_trade_proposal_review_dossier_batch_report(
        [],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
        ),
        generated_at=datetime(2026, 9, 10, 13, tzinfo=UTC),
    )


def nonempty_incomplete_dossier_batch_fixture():
    return build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=1), incomplete_dossier_fixture(index=2)],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
        ),
        generated_at=datetime(2026, 9, 10, 13, tzinfo=UTC),
    )


def unstable_dossier_batch_fixture():
    return build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=1), unstable_dossier_fixture(index=2)],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
        ),
        generated_at=datetime(2026, 9, 10, 13, tzinfo=UTC),
    )


def comparison_config(**overrides):
    values = {
        "config_version": "comparison-v1",
        "min_forecast_observation_count": 1,
        "min_dossier_count": 1,
    }
    values.update(overrides)
    return TradeProposalEvidenceComparisonConfig(**values)


def build_comparison(forecast=None, dossier_batch=None, config=None):
    return build_trade_proposal_evidence_comparison_report(
        forecast_evidence=forecast or ready_forecast_fixture(),
        dossier_batch=dossier_batch or ready_dossier_batch_fixture(),
        config=config or comparison_config(),
        generated_at=datetime(2026, 9, 10, 14, tzinfo=UTC),
    )


def test_build_trade_proposal_evidence_comparison_report_copies_supplied_metrics():
    forecast = ready_forecast_fixture()
    dossier_batch = ready_dossier_batch_fixture()

    report = build_comparison(forecast=forecast, dossier_batch=dossier_batch)

    assert report.generated_at == datetime(2026, 9, 10, 14, tzinfo=UTC)
    assert report.report_only is True
    assert report.boundary_statement == DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT
    assert report.status == "proposal_evidence_comparison_complete"
    assert report.forecast_evidence_generated_at == forecast.generated_at
    assert report.dossier_batch_generated_at == dossier_batch.generated_at
    assert report.forecast_status == "paper_review_ready"
    assert report.dossier_batch_status == "proposal_review_dossier_batch_ready"
    assert report.forecast_observation_count == forecast.observation_count
    assert (
        report.forecast_probability_observation_count
        == forecast.probability_observation_count
    )
    assert report.forecast_edge_observation_count == forecast.edge_observation_count
    assert report.dossier_count == dossier_batch.dossier_count
    assert report.complete_dossier_count == dossier_batch.complete_dossier_count
    assert report.incomplete_dossier_ratio == dossier_batch.incomplete_dossier_ratio
    assert report.inconsistent_dossier_ratio == dossier_batch.inconsistent_dossier_ratio
    assert report.unstable_dossier_ratio == dossier_batch.unstable_dossier_ratio
    assert report.mean_probability_loss == forecast.mean_probability_loss
    assert report.worst_bucket_error == forecast.worst_bucket_error
    assert report.mean_edge_gap_ratio == forecast.mean_edge_gap_ratio
    assert report.positive_edge_hit_rate == forecast.positive_edge_hit_rate
    assert report.worst_residual_exposure_ratio == forecast.worst_residual_exposure_ratio
    assert tuple(row.gate_name for row in report.gate_results) == GATE_NAMES
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.source_name for row in report.source_rows) == (
        "dossier_batch",
        "forecast_evidence",
    )
    assert report.finding_rows == ()


def test_trade_proposal_evidence_comparison_builds_source_and_metric_rows():
    forecast = ready_forecast_fixture()
    dossier_batch = ready_dossier_batch_fixture()

    report = build_comparison(forecast=forecast, dossier_batch=dossier_batch)

    assert report.source_rows == (
        TradeProposalEvidenceComparisonSourceRow(
            source_name="dossier_batch",
            source_status="proposal_review_dossier_batch_ready",
            generated_at=dossier_batch.generated_at,
            sample_count=1,
            status_category="complete",
        ),
        TradeProposalEvidenceComparisonSourceRow(
            source_name="forecast_evidence",
            source_status="paper_review_ready",
            generated_at=forecast.generated_at,
            sample_count=3,
            status_category="complete",
        ),
    )
    assert tuple(
        (row.source_name, row.metric_name, row.status) for row in report.metric_rows
    ) == (
        ("dossier_batch", "complete_dossier_count", "pass"),
        ("dossier_batch", "dossier_count", "pass"),
        ("dossier_batch", "incomplete_dossier_ratio", "pass"),
        ("dossier_batch", "inconsistent_dossier_ratio", "pass"),
        ("dossier_batch", "unstable_dossier_ratio", "pass"),
        ("forecast_evidence", "forecast_edge_observation_count", "pass"),
        ("forecast_evidence", "forecast_observation_count", "pass"),
        ("forecast_evidence", "forecast_probability_observation_count", "pass"),
        ("forecast_evidence", "mean_edge_gap_ratio", "pass"),
        ("forecast_evidence", "mean_probability_loss", "pass"),
        ("forecast_evidence", "positive_edge_hit_rate", "pass"),
        ("forecast_evidence", "worst_bucket_error", "pass"),
        ("forecast_evidence", "worst_residual_exposure_ratio", "pass"),
    )
    assert len(report.metric_rows) == 13
    metrics = {(row.source_name, row.metric_name): row for row in report.metric_rows}
    assert metrics[("forecast_evidence", "forecast_observation_count")] == (
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="forecast_observation_count",
            source_name="forecast_evidence",
            observed_value=3,
            threshold=1,
            status="pass",
        )
    )
    assert metrics[("forecast_evidence", "mean_probability_loss")].threshold == (
        "max_mean_probability_loss=1.0000; max_bucket_error=1.0000"
    )
    assert metrics[("dossier_batch", "incomplete_dossier_ratio")].threshold == (
        Decimal("0.0000")
    )


def test_trade_proposal_evidence_comparison_statuses_cover_incomplete_and_divergent_inputs():
    source_sample_incomplete = build_comparison(
        forecast=empty_forecast_fixture(),
        dossier_batch=incomplete_dossier_batch_fixture(),
    )
    assert source_sample_incomplete.status == "incomplete_evidence_comparison"
    assert source_sample_incomplete.gate_results[0].status == "incomplete"
    assert tuple(row.finding_code for row in source_sample_incomplete.finding_rows) == (
        "dossier_batch_incomplete",
        "forecast_evidence_incomplete",
    )

    ready_forecast_with_empty_dossier = build_comparison(
        forecast=ready_forecast_fixture(),
        dossier_batch=incomplete_dossier_batch_fixture(),
    )
    assert ready_forecast_with_empty_dossier.status == "incomplete_evidence_comparison"
    assert tuple(row.status for row in ready_forecast_with_empty_dossier.gate_results) == (
        "incomplete",
        "pass",
        "incomplete",
        "fail",
    )

    insufficient_forecast_with_ready_batch = build_comparison(
        forecast=insufficient_forecast_fixture(),
        dossier_batch=ready_dossier_batch_fixture(),
    )
    assert insufficient_forecast_with_ready_batch.status == (
        "divergent_evidence_comparison"
    )
    assert tuple(
        row.status for row in insufficient_forecast_with_ready_batch.gate_results
    ) == (
        "pass",
        "incomplete",
        "pass",
        "fail",
    )

    ready_forecast_with_nonempty_incomplete_batch = build_comparison(
        forecast=ready_forecast_fixture(),
        dossier_batch=nonempty_incomplete_dossier_batch_fixture(),
    )
    assert ready_forecast_with_nonempty_incomplete_batch.status == (
        "divergent_evidence_comparison"
    )
    assert tuple(
        row.status for row in ready_forecast_with_nonempty_incomplete_batch.gate_results
    ) == (
        "pass",
        "pass",
        "incomplete",
        "fail",
    )

    ready_forecast_with_unstable_batch = build_comparison(
        forecast=ready_forecast_fixture(),
        dossier_batch=unstable_dossier_batch_fixture(),
    )
    assert ready_forecast_with_unstable_batch.status == "divergent_evidence_comparison"
    assert tuple(row.status for row in ready_forecast_with_unstable_batch.gate_results) == (
        "pass",
        "pass",
        "fail",
        "fail",
    )
    assert ready_forecast_with_unstable_batch.finding_rows == (
        TradeProposalEvidenceComparisonFindingRow(
            finding_code="evidence_consistency_divergent",
            severity="divergent",
            source_name="comparison",
            message="Forecast evidence and dossier batch gate statuses differ.",
            observed_value="forecast=pass; dossier=fail",
            threshold="matching_status_categories",
        ),
        TradeProposalEvidenceComparisonFindingRow(
            finding_code="dossier_batch_unstable",
            severity="unstable",
            source_name="dossier_batch",
            message="Dossier batch health is unstable or inconsistent.",
            observed_value="unstable_dossier_batch",
            threshold="proposal_review_dossier_batch_ready",
        ),
    )

    unstable_forecast_with_ready_batch = build_comparison(
        forecast=unstable_forecast_fixture(),
        dossier_batch=ready_dossier_batch_fixture(),
    )
    assert unstable_forecast_with_ready_batch.status == "divergent_evidence_comparison"
    assert tuple(row.status for row in unstable_forecast_with_ready_batch.gate_results) == (
        "pass",
        "fail",
        "pass",
        "fail",
    )
    assert tuple(row.finding_code for row in unstable_forecast_with_ready_batch.finding_rows) == (
        "evidence_consistency_divergent",
        "forecast_evidence_unstable",
    )

    unstable_forecast_with_unstable_batch = build_comparison(
        forecast=unstable_forecast_fixture(),
        dossier_batch=unstable_dossier_batch_fixture(),
    )
    assert unstable_forecast_with_unstable_batch.status == "unstable_evidence_comparison"
    assert tuple(row.status for row in unstable_forecast_with_unstable_batch.gate_results) == (
        "pass",
        "fail",
        "fail",
        "pass",
    )


def test_trade_proposal_evidence_comparison_supports_optional_readiness_requirements():
    report = build_comparison(
        forecast=unstable_forecast_fixture(),
        dossier_batch=unstable_dossier_batch_fixture(),
        config=comparison_config(
            require_forecast_ready=False,
            require_dossier_batch_ready=False,
        ),
    )

    assert report.status == "proposal_evidence_comparison_complete"
    assert tuple(row.status for row in report.gate_results) == (
        "pass",
        "pass",
        "pass",
        "pass",
    )
    assert report.gate_results[1].threshold == "not_required"
    assert report.gate_results[2].threshold == "not_required"
    assert report.finding_rows == ()
    metric_statuses = {
        (row.source_name, row.metric_name): row.status for row in report.metric_rows
    }
    assert metric_statuses[("forecast_evidence", "mean_probability_loss")] == "fail"
    assert metric_statuses[("dossier_batch", "unstable_dossier_ratio")] == "fail"


def test_trade_proposal_evidence_comparison_rejects_bad_public_inputs():
    forecast = ready_forecast_fixture()
    dossier_batch = ready_dossier_batch_fixture()
    config = comparison_config()

    with pytest.raises(ValueError, match="PaperForecastEvidenceReport"):
        build_trade_proposal_evidence_comparison_report(
            forecast_evidence=object(),
            dossier_batch=dossier_batch,
            config=config,
            generated_at=datetime(2026, 9, 10, 14, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="TradeProposalReviewDossierBatchReport"):
        build_trade_proposal_evidence_comparison_report(
            forecast_evidence=forecast,
            dossier_batch=object(),
            config=config,
            generated_at=datetime(2026, 9, 10, 14, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_trade_proposal_evidence_comparison_report(
            forecast_evidence=forecast,
            dossier_batch=dossier_batch,
            config=object(),
            generated_at=datetime(2026, 9, 10, 14, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_trade_proposal_evidence_comparison_report(
            forecast_evidence=forecast,
            dossier_batch=dossier_batch,
            config=config,
            generated_at="2026-09-10T14:00:00+00:00",
        )


def test_trade_proposal_evidence_comparison_rejects_non_exact_report_subclasses():
    forecast = ready_forecast_fixture()
    dossier_batch = ready_dossier_batch_fixture()

    class ForecastSubclass(PaperForecastEvidenceReport):
        pass

    class DossierBatchSubclass(TradeProposalReviewDossierBatchReport):
        pass

    forecast_subclass = ForecastSubclass(
        generated_at=forecast.generated_at,
        config_version=forecast.config_version,
        first_observed_at=forecast.first_observed_at,
        last_observed_at=forecast.last_observed_at,
        observation_count=forecast.observation_count,
        probability_observation_count=forecast.probability_observation_count,
        edge_observation_count=forecast.edge_observation_count,
        unique_market_count=forecast.unique_market_count,
        unique_strategy_count=forecast.unique_strategy_count,
        unique_risk_tag_count=forecast.unique_risk_tag_count,
        mean_probability_loss=forecast.mean_probability_loss,
        worst_bucket_error=forecast.worst_bucket_error,
        mean_edge_gap_ratio=forecast.mean_edge_gap_ratio,
        positive_edge_hit_rate=forecast.positive_edge_hit_rate,
        worst_residual_exposure_ratio=forecast.worst_residual_exposure_ratio,
        status=forecast.status,
        gate_results=forecast.gate_results,
        buckets=forecast.buckets,
        paper_only=forecast.paper_only,
    )
    dossier_batch_subclass = DossierBatchSubclass(
        generated_at=dossier_batch.generated_at,
        config_version=dossier_batch.config_version,
        report_only=dossier_batch.report_only,
        boundary_statement=dossier_batch.boundary_statement,
        dossier_count=dossier_batch.dossier_count,
        complete_dossier_count=dossier_batch.complete_dossier_count,
        incomplete_dossier_count=dossier_batch.incomplete_dossier_count,
        inconsistent_dossier_count=dossier_batch.inconsistent_dossier_count,
        unstable_dossier_count=dossier_batch.unstable_dossier_count,
        incomplete_dossier_ratio=dossier_batch.incomplete_dossier_ratio,
        inconsistent_dossier_ratio=dossier_batch.inconsistent_dossier_ratio,
        unstable_dossier_ratio=dossier_batch.unstable_dossier_ratio,
        first_dossier_generated_at=dossier_batch.first_dossier_generated_at,
        last_dossier_generated_at=dossier_batch.last_dossier_generated_at,
        status=dossier_batch.status,
        gate_results=dossier_batch.gate_results,
        config_version_summaries=dossier_batch.config_version_summaries,
        duplicate_summaries=dossier_batch.duplicate_summaries,
        finding_summaries=dossier_batch.finding_summaries,
        source_summaries=dossier_batch.source_summaries,
    )

    with pytest.raises(ValueError, match="PaperForecastEvidenceReport"):
        build_comparison(forecast=forecast_subclass, dossier_batch=dossier_batch)
    with pytest.raises(ValueError, match="TradeProposalReviewDossierBatchReport"):
        build_comparison(forecast=forecast, dossier_batch=dossier_batch_subclass)


def test_trade_proposal_evidence_comparison_revalidates_nested_upstream_rows():
    forecast_gate_drift = ready_forecast_fixture()
    object.__setattr__(forecast_gate_drift.gate_results[0], "status", "unknown")
    with pytest.raises(ValueError, match="status"):
        build_comparison(forecast=forecast_gate_drift)

    forecast_bucket_drift = ready_forecast_fixture()
    object.__setattr__(forecast_bucket_drift.buckets[0], "observation_count", -1)
    with pytest.raises(ValueError, match="observation_count"):
        build_comparison(forecast=forecast_bucket_drift)

    batch_gate_drift = ready_dossier_batch_fixture()
    object.__setattr__(batch_gate_drift.gate_results[0], "status", "unknown")
    with pytest.raises(ValueError, match="status"):
        build_comparison(dossier_batch=batch_gate_drift)

    batch_source_drift = ready_dossier_batch_fixture()
    object.__setattr__(
        batch_source_drift.source_summaries[0],
        "source_report_name",
        "approval_workflow",
    )
    with pytest.raises(ValueError, match="source_report_name"):
        build_comparison(dossier_batch=batch_source_drift)


def test_trade_proposal_evidence_comparison_config_and_dataclasses_validate_invariants():
    assert DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT == (
        "This is a report-only proposal evidence comparison artifact over supplied "
        "forecast evidence and proposal-review dossier batch reports, not an "
        "approval workflow, proposal approval, approved-proposal selector, "
        "latest-decision selector, decision-resolution process, investment ranking, "
        "trade recommendation, strategy-promotion signal, trade instruction, order "
        "instruction, broker request, order request, account action, account "
        "authentication, private-key handling, wallet signature, live-execution "
        "signal, credential workflow, external-history loader, JSONL reader, "
        "scraping workflow, settlement review, reconciliation process, compliance "
        "review, geographic access analysis, or automatic order-placement "
        "authorization."
    )
    with pytest.raises(ValueError, match="config_version"):
        TradeProposalEvidenceComparisonConfig(config_version="")
    with pytest.raises(ValueError, match="min_forecast_observation_count"):
        TradeProposalEvidenceComparisonConfig(
            config_version="comparison-v1",
            min_forecast_observation_count=-1,
        )
    with pytest.raises(ValueError, match="max_incomplete_dossier_ratio"):
        TradeProposalEvidenceComparisonConfig(
            config_version="comparison-v1",
            max_incomplete_dossier_ratio=Decimal("1.0001"),
        )
    with pytest.raises(ValueError, match="require_forecast_ready"):
        TradeProposalEvidenceComparisonConfig(
            config_version="comparison-v1",
            require_forecast_ready=1,
        )
    with pytest.raises(ValueError, match="boundary_statement"):
        TradeProposalEvidenceComparisonConfig(
            config_version="comparison-v1",
            boundary_statement="comparison report",
        )
    flexible_boundary = DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT.replace(
        ", ",
        " ,  ",
    )
    assert (
        TradeProposalEvidenceComparisonConfig(
            config_version="comparison-v1",
            boundary_statement=flexible_boundary,
        ).boundary_statement
        == flexible_boundary
    )
    with pytest.raises(ValueError, match="boundary_statement"):
        TradeProposalEvidenceComparisonConfig(
            config_version="comparison-v1",
            boundary_statement=(
                f"{DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT} Extra permission."
            ),
        )

    report = build_comparison()
    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(FrozenInstanceError):
        report.gate_results[0].status = "fail"
    with pytest.raises(ValueError, match="gate_name"):
        TradeProposalEvidenceComparisonGateResult(
            gate_name="approval_workflow",
            status="pass",
            message="bad",
        )
    with pytest.raises(ValueError, match="observed_value"):
        replace(report.gate_results[0], observed_value=True)
    with pytest.raises(ValueError, match="observed_value"):
        replace(report.metric_rows[0], observed_value=1.0)
    with pytest.raises(ValueError, match="severity"):
        TradeProposalEvidenceComparisonFindingRow(
            finding_code="bad",
            severity="approval",
            source_name="comparison",
            message="bad",
        )
    with pytest.raises(ValueError, match="source_rows"):
        replace(report, source_rows=tuple(reversed(report.source_rows)))
    with pytest.raises(ValueError, match="metric_rows"):
        replace(report, metric_rows=tuple(reversed(report.metric_rows)))
    with pytest.raises(ValueError, match="finding_rows"):
        replace(
            report,
            finding_rows=(
                TradeProposalEvidenceComparisonFindingRow(
                    finding_code="z",
                    severity="unstable",
                    source_name="forecast_evidence",
                    message="z",
                ),
                TradeProposalEvidenceComparisonFindingRow(
                    finding_code="a",
                    severity="incomplete",
                    source_name="forecast_evidence",
                    message="a",
                ),
            ),
        )


def test_trade_proposal_evidence_comparison_log_appends_jsonl_report(tmp_path):
    report = build_trade_proposal_evidence_comparison_report(
        forecast_evidence=ready_forecast_fixture(),
        dossier_batch=ready_dossier_batch_fixture(),
        config=comparison_config(),
        generated_at=datetime(
            2026,
            9,
            10,
            22,
            30,
            tzinfo=timezone(timedelta(hours=8)),
        ),
    )
    log = TradeProposalEvidenceComparisonLog(
        path=tmp_path / "nested" / "proposal-evidence-comparison.jsonl",
    )

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    stored = json.loads(lines[0])
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-09-10T14:30:00+00:00"
    assert stored["config_version"] == "comparison-v1"
    assert stored["forecast_observation_count"] == 3
    assert stored["mean_probability_loss"] == "0.1800"
    assert stored["source_rows"][0]["source_name"] == "dossier_batch"


def test_trade_proposal_evidence_comparison_log_validates_before_open(tmp_path):
    report = build_comparison()
    object.__setattr__(report.metric_rows[0], "observed_value", Decimal("NaN"))
    log = TradeProposalEvidenceComparisonLog(
        path=tmp_path / "proposal-evidence-comparison.jsonl",
    )

    with pytest.raises(ValueError, match="finite|observed_value"):
        log.append(report)

    assert not log.path.exists()

    existing_log = TradeProposalEvidenceComparisonLog(path=tmp_path / "existing.jsonl")
    existing_log.path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="finite|observed_value"):
        existing_log.append(report)
    assert existing_log.path.read_text(encoding="utf-8") == "existing\n"

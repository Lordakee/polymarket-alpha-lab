import json
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tests.test_proposal_review_coverage import (
    approved_record,
    coverage_report,
    packet,
    rejected_record,
)
from tests.test_proposal_review_dossier import dossier_inputs, dossier_report
from polymarket_alpha_lab.proposal_review_diagnostics import (
    TradeProposalReviewDiagnosticConfig,
    build_trade_proposal_review_diagnostic_report,
)
from polymarket_alpha_lab.proposal_review_dossier_batch import (
    DEFAULT_REVIEW_DOSSIER_BATCH_BOUNDARY_STATEMENT,
    GATE_NAMES,
    TradeProposalReviewDossierBatchConfig,
    TradeProposalReviewDossierBatchConfigVersionSummary,
    TradeProposalReviewDossierBatchDuplicateSummary,
    TradeProposalReviewDossierBatchFindingSummary,
    TradeProposalReviewDossierBatchGateResult,
    TradeProposalReviewDossierBatchLog,
    TradeProposalReviewDossierBatchSourceSummary,
    build_trade_proposal_review_dossier_batch_report,
)
from polymarket_alpha_lab.proposal_review_quality import (
    TradeProposalReviewQualityConfig,
    build_trade_proposal_review_quality_report,
)
from polymarket_alpha_lab.proposal_review_summary import (
    TradeProposalReviewSummaryConfig,
    build_trade_proposal_review_summary_report,
)


def complete_dossier_fixture(index=1):
    _require_fixture_index(index)
    source = packet(index)
    records = [approved_record(source, minute=index)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])
    return dossier_report(
        summary,
        quality,
        diagnostics,
        coverage,
        generated_at=_fixture_generated_at(index),
    )


def incomplete_dossier_fixture(index=1):
    _require_fixture_index(index)
    summary, quality, diagnostics, coverage = dossier_inputs([], [])
    return dossier_report(
        summary,
        quality,
        diagnostics,
        coverage,
        generated_at=_fixture_generated_at(index),
    )


def inconsistent_dossier_fixture(index=1):
    _require_fixture_index(index)
    summary_source = packet(20 + index)
    coverage_source = packet(30 + index)
    summary_records = [approved_record(summary_source, minute=20 + index)]
    summary, quality, diagnostics, _ = dossier_inputs(summary_records, [summary_source])
    coverage = coverage_report(
        [coverage_source],
        [rejected_record(coverage_source, minute=30 + index)],
        generated_at=datetime(2026, 9, 8, 20, tzinfo=UTC),
    )
    return dossier_report(
        summary,
        quality,
        diagnostics,
        coverage,
        generated_at=_fixture_generated_at(index),
    )


def unstable_dossier_fixture(index=1):
    _require_fixture_index(index)
    source = packet(40 + index)
    records = [rejected_record(source, minute=40 + index)]
    summary = build_trade_proposal_review_summary_report(
        records,
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("0.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 17, tzinfo=UTC),
    )
    quality = build_trade_proposal_review_quality_report(
        [summary],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 18, tzinfo=UTC),
    )
    diagnostics = build_trade_proposal_review_diagnostic_report(
        records,
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 19, tzinfo=UTC),
    )
    coverage = coverage_report(
        [source],
        records,
        generated_at=datetime(2026, 9, 8, 20, tzinfo=UTC),
    )
    return dossier_report(
        summary,
        quality,
        diagnostics,
        coverage,
        generated_at=_fixture_generated_at(index),
    )


def expected_dossier_fingerprint(dossier):
    return json.dumps(_json_ready(asdict(dossier)), allow_nan=False, sort_keys=True)


def _fixture_generated_at(index):
    return datetime(2026, 9, 9, index % 24, index % 60, tzinfo=UTC)


def _require_fixture_index(index):
    if index < 1 or index > 9:
        raise ValueError("fixture index must be between 1 and 9")


def _json_ready(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def test_build_trade_proposal_review_dossier_batch_report_summarizes_supplied_dossiers():
    complete = complete_dossier_fixture(index=1)
    incomplete = incomplete_dossier_fixture(index=4)
    inconsistent = inconsistent_dossier_fixture(index=2)
    unstable = unstable_dossier_fixture(index=3)

    report = build_trade_proposal_review_dossier_batch_report(
        [unstable, incomplete, complete, inconsistent],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            max_incomplete_dossier_ratio=Decimal("1.0000"),
            max_inconsistent_dossier_ratio=Decimal("1.0000"),
            max_unstable_dossier_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 9, 12, tzinfo=UTC),
    )

    assert report.report_only is True
    assert report.dossier_count == 4
    assert report.complete_dossier_count == 1
    assert report.incomplete_dossier_count == 1
    assert report.inconsistent_dossier_count == 1
    assert report.unstable_dossier_count == 1
    assert report.incomplete_dossier_ratio == Decimal("0.2500")
    assert report.inconsistent_dossier_ratio == Decimal("0.2500")
    assert report.unstable_dossier_ratio == Decimal("0.2500")
    assert report.config_version == "dossier-batch-v1"
    assert report.status == "proposal_review_dossier_batch_ready"
    assert tuple(row.gate_name for row in report.gate_results) == GATE_NAMES
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.source_report_name for row in report.source_summaries) == (
        "coverage",
        "diagnostics",
        "quality",
        "summary",
    )
    assert tuple(
        row.dossier_config_version for row in report.config_version_summaries
    ) == ("dossier-v1",)
    assert report.duplicate_summaries == ()
    assert (
        report.complete_dossier_count
        + report.incomplete_dossier_count
        + report.inconsistent_dossier_count
        + report.unstable_dossier_count
    ) == report.dossier_count
    assert report.first_dossier_generated_at == min(
        row.generated_at for row in (complete, incomplete, inconsistent, unstable)
    )
    assert report.last_dossier_generated_at == max(
        row.generated_at for row in (complete, incomplete, inconsistent, unstable)
    )
    assert report.finding_summaries == (
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="coverage_evidence_incomplete",
            severity="incomplete",
            source_report_name="coverage",
            dossier_count=1,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="diagnostic_evidence_incomplete",
            severity="incomplete",
            source_report_name="diagnostics",
            dossier_count=1,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="quality_evidence_incomplete",
            severity="incomplete",
            source_report_name="quality",
            dossier_count=1,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="summary_evidence_incomplete",
            severity="incomplete",
            source_report_name="summary",
            dossier_count=1,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="count_consistency_failed",
            severity="inconsistent",
            source_report_name="dossier",
            dossier_count=1,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="summary_evidence_unstable",
            severity="unstable",
            source_report_name="summary",
            dossier_count=1,
        ),
    )
    assert report.source_summaries == (
        TradeProposalReviewDossierBatchSourceSummary("coverage", 3, 1, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("diagnostics", 3, 1, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("quality", 3, 1, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("summary", 2, 1, 0, 1),
    )


def test_trade_proposal_review_dossier_batch_statuses_cover_sample_and_rate_failures():
    complete = complete_dossier_fixture(index=4)
    incomplete = incomplete_dossier_fixture(index=7)
    inconsistent = inconsistent_dossier_fixture(index=5)
    unstable = unstable_dossier_fixture(index=6)

    empty = build_trade_proposal_review_dossier_batch_report(
        [],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 13, tzinfo=UTC),
    )
    assert empty.status == "incomplete_dossier_batch"
    assert (
        next(row for row in empty.gate_results if row.gate_name == "dossier_sample").status
        == "fail"
    )
    assert all(
        row.observed_value is None
        for row in empty.gate_results
        if row.gate_name.endswith("_rate")
    )
    assert empty.source_summaries == (
        TradeProposalReviewDossierBatchSourceSummary("coverage", 0, 0, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("diagnostics", 0, 0, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("quality", 0, 0, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("summary", 0, 0, 0, 0),
    )

    inconsistent_batch = build_trade_proposal_review_dossier_batch_report(
        [complete, inconsistent],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 14, tzinfo=UTC),
    )
    assert inconsistent_batch.status == "inconsistent_dossier_batch"

    incomplete_batch = build_trade_proposal_review_dossier_batch_report(
        [complete, incomplete],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 15, tzinfo=UTC),
    )
    assert incomplete_batch.status == "incomplete_dossier_batch"
    incomplete_rate = next(
        row
        for row in incomplete_batch.gate_results
        if row.gate_name == "incomplete_dossier_rate"
    )
    assert incomplete_rate.status == "fail"
    assert incomplete_rate.message == (
        "Incomplete dossier rate exceeds threshold or is unavailable."
    )
    assert incomplete_rate.observed_value == Decimal("0.5000")
    assert incomplete_rate.threshold == Decimal("0.0000")

    unstable_batch = build_trade_proposal_review_dossier_batch_report(
        [complete, unstable],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 16, tzinfo=UTC),
    )
    assert unstable_batch.status == "unstable_dossier_batch"

    multi_failure = build_trade_proposal_review_dossier_batch_report(
        [complete, inconsistent, incomplete, unstable],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 17, tzinfo=UTC),
    )
    assert multi_failure.status == "inconsistent_dossier_batch"


def test_trade_proposal_review_dossier_batch_gates_report_exact_semantics():
    report = build_trade_proposal_review_dossier_batch_report(
        (item for item in [complete_dossier_fixture(index=1)]),
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 12, tzinfo=UTC),
    )

    assert report.gate_results == (
        TradeProposalReviewDossierBatchGateResult(
            gate_name="dossier_sample",
            status="pass",
            message="Dossier sample size meets the configured minimum.",
            observed_value=1,
            threshold=1,
        ),
        TradeProposalReviewDossierBatchGateResult(
            gate_name="incomplete_dossier_rate",
            status="pass",
            message="Incomplete dossier rate is within threshold.",
            observed_value=Decimal("0.0000"),
            threshold=Decimal("0.0000"),
        ),
        TradeProposalReviewDossierBatchGateResult(
            gate_name="inconsistent_dossier_rate",
            status="pass",
            message="Inconsistent dossier rate is within threshold.",
            observed_value=Decimal("0.0000"),
            threshold=Decimal("0.0000"),
        ),
        TradeProposalReviewDossierBatchGateResult(
            gate_name="unstable_dossier_rate",
            status="pass",
            message="Unstable dossier rate is within threshold.",
            observed_value=Decimal("0.0000"),
            threshold=Decimal("0.0000"),
        ),
    )

    empty = build_trade_proposal_review_dossier_batch_report(
        (),
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            min_dossier_count=2,
        ),
        generated_at=datetime(2026, 9, 9, 13, tzinfo=UTC),
    )
    assert empty.gate_results[0] == TradeProposalReviewDossierBatchGateResult(
        gate_name="dossier_sample",
        status="fail",
        message="Dossier sample size is below the configured minimum.",
        observed_value=0,
        threshold=2,
    )
    assert empty.gate_results[1:] == (
        TradeProposalReviewDossierBatchGateResult(
            gate_name="incomplete_dossier_rate",
            status="fail",
            message="Incomplete dossier rate exceeds threshold or is unavailable.",
            observed_value=None,
            threshold=Decimal("0.0000"),
        ),
        TradeProposalReviewDossierBatchGateResult(
            gate_name="inconsistent_dossier_rate",
            status="fail",
            message="Inconsistent dossier rate exceeds threshold or is unavailable.",
            observed_value=None,
            threshold=Decimal("0.0000"),
        ),
        TradeProposalReviewDossierBatchGateResult(
            gate_name="unstable_dossier_rate",
            status="fail",
            message="Unstable dossier rate exceeds threshold or is unavailable.",
            observed_value=None,
            threshold=Decimal("0.0000"),
        ),
    )


def test_trade_proposal_review_dossier_batch_rejects_bad_inputs_and_mutated_dossiers():
    complete = complete_dossier_fixture(index=7)

    with pytest.raises(ValueError, match="dossiers"):
        build_trade_proposal_review_dossier_batch_report(
            "not dossiers",
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 17, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="TradeProposalReviewDossierReport"):
        build_trade_proposal_review_dossier_batch_report(
            [object()],
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 18, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="dossiers"):
        build_trade_proposal_review_dossier_batch_report(
            b"not dossiers",
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 18, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="config"):
        build_trade_proposal_review_dossier_batch_report(
            [complete],
            config=object(),
            generated_at=datetime(2026, 9, 9, 18, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="generated_at"):
        build_trade_proposal_review_dossier_batch_report(
            [complete],
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at="2026-09-09T18:00:00+00:00",
        )

    object.__setattr__(complete, "review_coverage_ratio", Decimal("NaN"))
    with pytest.raises(ValueError, match="finite|review_coverage_ratio"):
        build_trade_proposal_review_dossier_batch_report(
            [complete],
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 19, tzinfo=UTC),
        )


def test_trade_proposal_review_dossier_batch_revalidates_nested_dossier_rows():
    gate_drift = complete_dossier_fixture(index=1)
    object.__setattr__(gate_drift.gate_results[0], "observed_value", Decimal("NaN"))
    with pytest.raises(ValueError, match="finite|observed_value"):
        build_trade_proposal_review_dossier_batch_report(
            [gate_drift],
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 19, tzinfo=UTC),
        )

    source_drift = complete_dossier_fixture(index=2)
    object.__setattr__(source_drift.source_rows[0], "status_category", "approval")
    with pytest.raises(ValueError, match="status_category"):
        build_trade_proposal_review_dossier_batch_report(
            [source_drift],
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 19, tzinfo=UTC),
        )

    finding_drift = incomplete_dossier_fixture(index=3)
    object.__setattr__(finding_drift.finding_rows[0], "severity", "approval")
    with pytest.raises(ValueError, match="severity"):
        build_trade_proposal_review_dossier_batch_report(
            [finding_drift],
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 19, tzinfo=UTC),
        )

    type_drift = complete_dossier_fixture(index=4)
    object.__setattr__(type_drift, "gate_results", (object(),))
    with pytest.raises(ValueError, match="gate_results"):
        build_trade_proposal_review_dossier_batch_report(
            [type_drift],
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 19, tzinfo=UTC),
        )


def test_trade_proposal_review_dossier_batch_log_appends_jsonl_report(tmp_path):
    report = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=8)],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 20, tzinfo=UTC),
    )
    log = TradeProposalReviewDossierBatchLog(path=tmp_path / "dossier-batch.jsonl")

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    stored = json.loads(lines[0])
    assert stored["report_only"] is True
    assert stored["dossier_count"] == 1
    assert stored["complete_dossier_count"] == 1
    assert stored["config_version"] == "dossier-batch-v1"
    assert (
        stored["config_version_summaries"][0]["dossier_config_version"] == "dossier-v1"
    )


def test_trade_proposal_review_dossier_batch_log_serializes_decimals_and_utc_datetimes(
    tmp_path,
):
    report = build_trade_proposal_review_dossier_batch_report(
        [
            complete_dossier_fixture(index=1),
            complete_dossier_fixture(index=2),
            incomplete_dossier_fixture(index=3),
        ],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            max_incomplete_dossier_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(
            2026,
            9,
            10,
            8,
            30,
            tzinfo=timezone(timedelta(hours=8)),
        ),
    )
    log = TradeProposalReviewDossierBatchLog(path=tmp_path / "dossier-batch.jsonl")

    log.append(report)

    stored = json.loads(log.path.read_text(encoding="utf-8"))
    assert stored["generated_at"] == "2026-09-10T00:30:00+00:00"
    assert stored["first_dossier_generated_at"] == "2026-09-09T01:01:00+00:00"
    assert stored["last_dossier_generated_at"] == "2026-09-09T03:03:00+00:00"
    assert stored["incomplete_dossier_ratio"] == "0.3333"
    assert stored["inconsistent_dossier_ratio"] == "0.0000"
    assert stored["unstable_dossier_ratio"] == "0.0000"
    assert stored["gate_results"][1]["observed_value"] == "0.3333"


def test_trade_proposal_review_dossier_batch_log_handles_nested_paths_and_type_errors(
    tmp_path,
):
    report = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=8)],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 20, tzinfo=UTC),
    )
    log = TradeProposalReviewDossierBatchLog(
        path=tmp_path / "nested" / "dossier-batch.jsonl",
    )

    log.append(report)

    assert log.path.exists()
    with pytest.raises(ValueError, match="TradeProposalReviewDossierBatchReport"):
        log.append(object())


def test_trade_proposal_review_dossier_batch_log_validates_before_open(tmp_path):
    report = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=8)],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 22, tzinfo=UTC),
    )
    object.__setattr__(report, "incomplete_dossier_ratio", Decimal("NaN"))
    log = TradeProposalReviewDossierBatchLog(path=tmp_path / "dossier-batch.jsonl")

    with pytest.raises(ValueError, match="finite|incomplete_dossier_ratio"):
        log.append(report)

    assert not log.path.exists()

    existing_log = TradeProposalReviewDossierBatchLog(path=tmp_path / "existing.jsonl")
    existing_log.path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="finite|incomplete_dossier_ratio"):
        existing_log.append(report)
    assert existing_log.path.read_text(encoding="utf-8") == "existing\n"


def test_trade_proposal_review_dossier_batch_reports_duplicate_dossier_fingerprints():
    complete = complete_dossier_fixture(index=9)
    duplicate_content = replace(complete)
    assert duplicate_content is not complete

    report = build_trade_proposal_review_dossier_batch_report(
        [complete, duplicate_content],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 21, tzinfo=UTC),
    )

    assert report.dossier_count == 2
    assert len(report.duplicate_summaries) == 1
    assert (
        report.duplicate_summaries[0].dossier_fingerprint
        == expected_dossier_fingerprint(complete)
    )
    assert report.duplicate_summaries[0].dossier_count == 2

    same_object_report = build_trade_proposal_review_dossier_batch_report(
        [complete, complete],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 21, tzinfo=UTC),
    )
    assert same_object_report.duplicate_summaries == (
        TradeProposalReviewDossierBatchDuplicateSummary(
            dossier_fingerprint=expected_dossier_fingerprint(complete),
            dossier_count=2,
        ),
    )


def test_trade_proposal_review_dossier_batch_sorts_duplicate_and_config_summaries():
    early = complete_dossier_fixture(index=1)
    late = replace(complete_dossier_fixture(index=2), config_version="z-dossier-v2")

    report = build_trade_proposal_review_dossier_batch_report(
        [late, replace(late), early, replace(early)],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 21, tzinfo=UTC),
    )

    assert report.config_version_summaries == (
        TradeProposalReviewDossierBatchConfigVersionSummary("dossier-v1", 2),
        TradeProposalReviewDossierBatchConfigVersionSummary("z-dossier-v2", 2),
    )
    assert tuple(row.dossier_fingerprint for row in report.duplicate_summaries) == tuple(
        sorted(
            (
                expected_dossier_fingerprint(early),
                expected_dossier_fingerprint(late),
            ),
        ),
    )
    assert tuple(row.dossier_count for row in report.duplicate_summaries) == (2, 2)


def test_trade_proposal_review_dossier_batch_finding_summaries_count_dossiers():
    report = build_trade_proposal_review_dossier_batch_report(
        [incomplete_dossier_fixture(index=1), incomplete_dossier_fixture(index=2)],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            max_incomplete_dossier_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 9, 21, tzinfo=UTC),
    )

    assert report.finding_summaries == (
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="coverage_evidence_incomplete",
            severity="incomplete",
            source_report_name="coverage",
            dossier_count=2,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="diagnostic_evidence_incomplete",
            severity="incomplete",
            source_report_name="diagnostics",
            dossier_count=2,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="quality_evidence_incomplete",
            severity="incomplete",
            source_report_name="quality",
            dossier_count=2,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="summary_evidence_incomplete",
            severity="incomplete",
            source_report_name="summary",
            dossier_count=2,
        ),
    )


def test_trade_proposal_review_dossier_batch_config_validates_thresholds():
    assert DEFAULT_REVIEW_DOSSIER_BATCH_BOUNDARY_STATEMENT == (
        "This is a report-only proposal-review dossier batch artifact over supplied "
        "dossier reports, not an approval workflow, proposal approval, "
        "approved-proposal selector, latest-decision selector, decision-resolution "
        "process, investment ranking, trade recommendation, trade instruction, "
        "order instruction, broker request, order request, account action, account "
        "authentication, private-key handling, wallet signature, live-execution "
        "signal, credential workflow, external-history loader, JSONL reader, "
        "scraping workflow, strategy-promotion signal, settlement review, "
        "reconciliation process, compliance review, geographic access analysis, or "
        "automatic order-placement authorization."
    )
    with pytest.raises(ValueError, match="config_version"):
        TradeProposalReviewDossierBatchConfig(config_version="")
    with pytest.raises(ValueError, match="min_dossier_count"):
        TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            min_dossier_count=-1,
        )
    with pytest.raises(ValueError, match="max_incomplete_dossier_ratio"):
        TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            max_incomplete_dossier_ratio=Decimal("1.5000"),
        )
    with pytest.raises(ValueError, match="max_inconsistent_dossier_ratio"):
        TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            max_inconsistent_dossier_ratio=0.5,
        )
    with pytest.raises(ValueError, match="boundary_statement"):
        TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            boundary_statement="dossier batch",
        )
    flexible_boundary = DEFAULT_REVIEW_DOSSIER_BATCH_BOUNDARY_STATEMENT.replace(
        ", ",
        " ,  ",
    )
    assert (
        TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            boundary_statement=flexible_boundary,
        ).boundary_statement
        == flexible_boundary
    )
    with pytest.raises(ValueError, match="boundary_statement"):
        TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            boundary_statement=(
                f"{DEFAULT_REVIEW_DOSSIER_BATCH_BOUNDARY_STATEMENT} Extra permission."
            ),
        )
    report = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=1)],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            boundary_statement=flexible_boundary,
        ),
        generated_at=datetime(2026, 9, 9, 22, tzinfo=UTC),
    )
    assert report.boundary_statement == flexible_boundary


def test_trade_proposal_review_dossier_batch_dataclasses_are_frozen_and_validate_invariants():
    report = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=9)],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 22, tzinfo=UTC),
    )
    config = TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1")

    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(ValueError, match="status"):
        replace(report, status="incomplete_dossier_batch")
    with pytest.raises(ValueError, match="gate_results"):
        replace(report, gate_results=tuple(reversed(report.gate_results)))
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(config, boundary_statement="dossier batch")
    with pytest.raises(ValueError, match="dossier_config_version"):
        replace(report.config_version_summaries[0], dossier_config_version="")
    with pytest.raises(ValueError, match="gate_name"):
        replace(report.gate_results[0], gate_name="approval_workflow")
    with pytest.raises(ValueError, match="source_report_name"):
        replace(report.source_summaries[0], source_report_name="approval_workflow")
    with pytest.raises(ValueError, match="finding_code"):
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="",
            severity="incomplete",
            source_report_name="summary",
            dossier_count=1,
        )


def test_trade_proposal_review_dossier_batch_report_validates_summary_invariants():
    ready = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=1)],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 22, tzinfo=UTC),
    )
    incomplete = build_trade_proposal_review_dossier_batch_report(
        [incomplete_dossier_fixture(index=1), incomplete_dossier_fixture(index=2)],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            max_incomplete_dossier_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 9, 23, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="config_version_summaries"):
        replace(
            ready,
            config_version_summaries=(
                TradeProposalReviewDossierBatchConfigVersionSummary("dossier-v1", 2),
            ),
        )
    with pytest.raises(ValueError, match="config_version_summaries"):
        replace(
            ready,
            config_version_summaries=(
                ready.config_version_summaries[0],
                TradeProposalReviewDossierBatchConfigVersionSummary("phantom-v1", 1),
            ),
        )
    with pytest.raises(ValueError, match="duplicate_summaries"):
        replace(
            ready,
            duplicate_summaries=(
                TradeProposalReviewDossierBatchDuplicateSummary("impossible", 2),
            ),
        )
    with pytest.raises(ValueError, match="duplicate_summaries"):
        replace(
            ready,
            duplicate_summaries=(
                TradeProposalReviewDossierBatchDuplicateSummary("b", 2),
                TradeProposalReviewDossierBatchDuplicateSummary("a", 2),
            ),
        )
    with pytest.raises(ValueError, match="duplicate_summaries"):
        replace(
            ready,
            duplicate_summaries=(
                TradeProposalReviewDossierBatchDuplicateSummary("same", 2),
                TradeProposalReviewDossierBatchDuplicateSummary("same", 2),
            ),
        )
    with pytest.raises(ValueError, match="finding_summaries"):
        replace(incomplete, finding_summaries=tuple(reversed(incomplete.finding_summaries)))
    with pytest.raises(ValueError, match="finding_summaries"):
        replace(
            incomplete,
            finding_summaries=(
                incomplete.finding_summaries[0],
                incomplete.finding_summaries[0],
            ),
        )
    with pytest.raises(ValueError, match="source_summaries"):
        replace(ready, source_summaries=ready.source_summaries[:3])
    with pytest.raises(ValueError, match="source_summaries"):
        replace(
            ready,
            source_summaries=(
                replace(ready.source_summaries[0], complete_count=0),
                *ready.source_summaries[1:],
            ),
        )


def test_trade_proposal_review_dossier_batch_report_validates_gate_semantics():
    ready = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=1)],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 22, tzinfo=UTC),
    )
    incomplete_pass = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=2), incomplete_dossier_fixture(index=3)],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            max_incomplete_dossier_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 9, 23, tzinfo=UTC),
    )

    for replacement in (
        replace(ready.gate_results[0], message="Wrong sample message."),
        replace(ready.gate_results[0], observed_value=2),
        replace(ready.gate_results[0], threshold=2),
        replace(ready.gate_results[1], message="Wrong incomplete message."),
        replace(ready.gate_results[1], observed_value=Decimal("0.5000")),
    ):
        with pytest.raises(ValueError, match="gate_results"):
            replace(
                ready,
                gate_results=(replacement, *ready.gate_results[1:])
                if replacement.gate_name == "dossier_sample"
                else (ready.gate_results[0], replacement, *ready.gate_results[2:]),
            )
    with pytest.raises(ValueError, match="gate_results"):
        replace(
            incomplete_pass,
            gate_results=(
                incomplete_pass.gate_results[0],
                replace(
                    incomplete_pass.gate_results[1],
                    threshold=Decimal("0.0000"),
                ),
                *incomplete_pass.gate_results[2:],
            ),
        )


def test_trade_proposal_review_dossier_batch_row_dataclasses_validate_fields():
    with pytest.raises(ValueError, match="dossier_config_version"):
        TradeProposalReviewDossierBatchConfigVersionSummary("", 1)
    with pytest.raises(ValueError, match="dossier_count"):
        TradeProposalReviewDossierBatchDuplicateSummary("fingerprint", -1)
    with pytest.raises(ValueError, match="dossier_fingerprint"):
        TradeProposalReviewDossierBatchDuplicateSummary("", 2)
    with pytest.raises(ValueError, match="dossier_count"):
        TradeProposalReviewDossierBatchDuplicateSummary("fingerprint", 1)
    with pytest.raises(ValueError, match="dossier_count"):
        TradeProposalReviewDossierBatchConfigVersionSummary("dossier-v1", True)
    with pytest.raises(ValueError, match="dossier_count"):
        TradeProposalReviewDossierBatchConfigVersionSummary("dossier-v1", 0)
    with pytest.raises(ValueError, match="severity"):
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="finding",
            severity="approval",
            source_report_name="summary",
            dossier_count=1,
        )
    with pytest.raises(ValueError, match="dossier_count"):
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="finding",
            severity="incomplete",
            source_report_name="summary",
            dossier_count=-1,
        )
    with pytest.raises(ValueError, match="dossier_count"):
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="finding",
            severity="incomplete",
            source_report_name="summary",
            dossier_count=0,
        )
    with pytest.raises(ValueError, match="source_report_name"):
        TradeProposalReviewDossierBatchSourceSummary("approval", 1, 0, 0, 0)
    with pytest.raises(ValueError, match="complete_count"):
        TradeProposalReviewDossierBatchSourceSummary("summary", -1, 0, 0, 0)
    with pytest.raises(ValueError, match="incomplete_count"):
        TradeProposalReviewDossierBatchSourceSummary("summary", 0, -1, 0, 0)
    with pytest.raises(ValueError, match="inconsistent_count"):
        TradeProposalReviewDossierBatchSourceSummary("summary", 0, 0, -1, 0)
    with pytest.raises(ValueError, match="unstable_count"):
        TradeProposalReviewDossierBatchSourceSummary("summary", 0, 0, 0, -1)
    with pytest.raises(ValueError, match="gate_name"):
        TradeProposalReviewDossierBatchGateResult(
            gate_name="approval",
            status="pass",
            message="bad",
        )
    with pytest.raises(ValueError, match="status"):
        TradeProposalReviewDossierBatchGateResult(
            gate_name="dossier_sample",
            status="maybe",
            message="bad",
        )
    with pytest.raises(ValueError, match="message"):
        TradeProposalReviewDossierBatchGateResult(
            gate_name="dossier_sample",
            status="pass",
            message="",
        )
    with pytest.raises(ValueError, match="observed_value"):
        TradeProposalReviewDossierBatchGateResult(
            gate_name="dossier_sample",
            status="pass",
            message="bad",
            observed_value=True,
        )
    with pytest.raises(ValueError, match="threshold"):
        TradeProposalReviewDossierBatchGateResult(
            gate_name="dossier_sample",
            status="pass",
            message="bad",
            threshold=0.5,
        )

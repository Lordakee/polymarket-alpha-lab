import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from tests.test_proposal_evidence_comparison import (
    build_comparison,
    empty_forecast_fixture,
    incomplete_dossier_batch_fixture,
    insufficient_forecast_fixture,
    ready_dossier_batch_fixture,
    ready_forecast_fixture,
    unstable_dossier_batch_fixture,
    unstable_forecast_fixture,
)
from polymarket_alpha_lab.proposal_evidence_comparison import (
    TradeProposalEvidenceComparisonReport,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history import (
    DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT,
    GATE_NAMES,
    TradeProposalEvidenceComparisonHistoryConfig,
    TradeProposalEvidenceComparisonHistoryConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryFindingSummary,
    TradeProposalEvidenceComparisonHistoryGateResult,
    TradeProposalEvidenceComparisonHistoryLog,
    TradeProposalEvidenceComparisonHistoryReport,
    TradeProposalEvidenceComparisonHistorySourceTransition,
    TradeProposalEvidenceComparisonHistoryStatusRow,
    build_trade_proposal_evidence_comparison_history_report,
)


def complete_comparison_fixture(index=1):
    report = build_comparison(
        forecast=ready_forecast_fixture(),
        dossier_batch=ready_dossier_batch_fixture(),
    )
    return replace(report, generated_at=datetime(2026, 9, 11, index, tzinfo=UTC))


def divergent_comparison_fixture(index=2):
    report = build_comparison(
        forecast=insufficient_forecast_fixture(),
        dossier_batch=ready_dossier_batch_fixture(),
    )
    return replace(report, generated_at=datetime(2026, 9, 11, index, tzinfo=UTC))


def unstable_comparison_fixture(index=3):
    report = build_comparison(
        forecast=unstable_forecast_fixture(),
        dossier_batch=unstable_dossier_batch_fixture(),
    )
    return replace(report, generated_at=datetime(2026, 9, 11, index, tzinfo=UTC))


def incomplete_comparison_fixture(index=4):
    report = build_comparison(
        forecast=empty_forecast_fixture(),
        dossier_batch=incomplete_dossier_batch_fixture(),
    )
    return replace(report, generated_at=datetime(2026, 9, 11, index, tzinfo=UTC))


def history_config(**overrides):
    values = {"config_version": "comparison-history-v1"}
    values.update(overrides)
    return TradeProposalEvidenceComparisonHistoryConfig(**values)


def build_history(comparisons=None, config=None):
    return build_trade_proposal_evidence_comparison_history_report(
        comparisons
        if comparisons is not None
        else (
            complete_comparison_fixture(index=1),
            divergent_comparison_fixture(index=2),
            unstable_comparison_fixture(index=3),
        ),
        config=config
        or history_config(
            max_divergent_comparison_ratio=Decimal("1.0000"),
            max_unstable_comparison_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )


def test_build_trade_proposal_evidence_comparison_history_report_summarizes_reports():
    complete = complete_comparison_fixture(index=1)
    divergent = divergent_comparison_fixture(index=2)
    unstable = unstable_comparison_fixture(index=3)

    report = build_history(comparisons=[unstable, complete, divergent])

    assert report.generated_at == datetime(2026, 9, 11, 12, tzinfo=UTC)
    assert report.config_version == "comparison-history-v1"
    assert report.report_only is True
    assert (
        report.boundary_statement
        == DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT
    )
    assert report.status == "proposal_evidence_comparison_history_ready"
    assert report.comparison_count == 3
    assert report.complete_comparison_count == 1
    assert report.incomplete_comparison_count == 0
    assert report.divergent_comparison_count == 1
    assert report.unstable_comparison_count == 1
    assert report.incomplete_comparison_ratio == Decimal("0.0000")
    assert report.divergent_comparison_ratio == Decimal("0.3333")
    assert report.unstable_comparison_ratio == Decimal("0.3333")
    assert report.first_comparison_generated_at == complete.generated_at
    assert report.last_comparison_generated_at == unstable.generated_at
    assert tuple(row.gate_name for row in report.gate_results) == GATE_NAMES
    assert all(row.status == "pass" for row in report.gate_results)
    assert (
        (
            report.gate_results[0].observed_value,
            report.gate_results[0].threshold,
            report.gate_results[1].observed_value,
            report.gate_results[1].threshold,
            report.gate_results[2].observed_value,
            report.gate_results[2].threshold,
            report.gate_results[3].observed_value,
            report.gate_results[3].threshold,
        )
        == (
            3,
            1,
            Decimal("0.0000"),
            Decimal("0.0000"),
            Decimal("0.3333"),
            Decimal("1.0000"),
            Decimal("0.3333"),
            Decimal("1.0000"),
        )
    )
    assert report.status_rows == (
        TradeProposalEvidenceComparisonHistoryStatusRow(
            comparison_status="divergent_evidence_comparison",
            comparison_count=1,
            comparison_ratio=Decimal("0.3333"),
        ),
        TradeProposalEvidenceComparisonHistoryStatusRow(
            comparison_status="incomplete_evidence_comparison",
            comparison_count=0,
            comparison_ratio=Decimal("0.0000"),
        ),
        TradeProposalEvidenceComparisonHistoryStatusRow(
            comparison_status="proposal_evidence_comparison_complete",
            comparison_count=1,
            comparison_ratio=Decimal("0.3333"),
        ),
        TradeProposalEvidenceComparisonHistoryStatusRow(
            comparison_status="unstable_evidence_comparison",
            comparison_count=1,
            comparison_ratio=Decimal("0.3333"),
        ),
    )
    assert report.config_version_summaries == (
        TradeProposalEvidenceComparisonHistoryConfigVersionSummary(
            comparison_config_version="comparison-v1",
            comparison_count=3,
        ),
    )
    assert report.finding_summaries == (
        TradeProposalEvidenceComparisonHistoryFindingSummary(
            finding_code="evidence_consistency_divergent",
            severity="divergent",
            source_name="comparison",
            comparison_count=1,
        ),
        TradeProposalEvidenceComparisonHistoryFindingSummary(
            finding_code="forecast_evidence_incomplete",
            severity="incomplete",
            source_name="forecast_evidence",
            comparison_count=1,
        ),
        TradeProposalEvidenceComparisonHistoryFindingSummary(
            finding_code="dossier_batch_unstable",
            severity="unstable",
            source_name="dossier_batch",
            comparison_count=1,
        ),
        TradeProposalEvidenceComparisonHistoryFindingSummary(
            finding_code="forecast_evidence_unstable",
            severity="unstable",
            source_name="forecast_evidence",
            comparison_count=1,
        ),
    )
    assert report.source_transitions == (
        TradeProposalEvidenceComparisonHistorySourceTransition(
            source_name="dossier_batch",
            from_source_status="proposal_review_dossier_batch_ready",
            to_source_status="proposal_review_dossier_batch_ready",
            transition_count=1,
        ),
        TradeProposalEvidenceComparisonHistorySourceTransition(
            source_name="dossier_batch",
            from_source_status="proposal_review_dossier_batch_ready",
            to_source_status="unstable_dossier_batch",
            transition_count=1,
        ),
        TradeProposalEvidenceComparisonHistorySourceTransition(
            source_name="forecast_evidence",
            from_source_status="insufficient_evidence",
            to_source_status="blocked_by_quality",
            transition_count=1,
        ),
        TradeProposalEvidenceComparisonHistorySourceTransition(
            source_name="forecast_evidence",
            from_source_status="paper_review_ready",
            to_source_status="insufficient_evidence",
            transition_count=1,
        ),
    )


def test_trade_proposal_evidence_comparison_history_statuses_cover_rate_failures():
    empty = build_history(comparisons=())
    assert empty.status == "incomplete_comparison_history"
    assert empty.comparison_count == 0
    assert empty.first_comparison_generated_at is None
    assert empty.last_comparison_generated_at is None
    assert empty.source_transitions == ()
    assert tuple(row.status for row in empty.gate_results) == (
        "incomplete",
        "incomplete",
        "incomplete",
        "incomplete",
    )
    assert all(row.comparison_ratio is None for row in empty.status_rows)

    below_sample = build_history(
        comparisons=[complete_comparison_fixture(index=1)],
        config=history_config(min_comparison_count=2),
    )
    assert below_sample.status == "incomplete_comparison_history"
    assert below_sample.gate_results[0].status == "incomplete"
    assert below_sample.source_transitions == ()

    divergent = build_history(
        comparisons=[
            complete_comparison_fixture(index=1),
            divergent_comparison_fixture(index=2),
        ],
        config=history_config(),
    )
    assert divergent.status == "divergent_comparison_history"
    assert tuple(row.status for row in divergent.gate_results) == (
        "pass",
        "pass",
        "fail",
        "pass",
    )

    unstable = build_history(
        comparisons=[
            complete_comparison_fixture(index=1),
            unstable_comparison_fixture(index=2),
        ],
        config=history_config(max_divergent_comparison_ratio=Decimal("1.0000")),
    )
    assert unstable.status == "unstable_comparison_history"
    assert tuple(row.status for row in unstable.gate_results) == (
        "pass",
        "pass",
        "pass",
        "fail",
    )

    incomplete = build_history(
        comparisons=[
            complete_comparison_fixture(index=1),
            incomplete_comparison_fixture(index=2),
        ],
    )
    assert incomplete.status == "incomplete_comparison_history"

    sample_dominates = build_history(
        comparisons=[
            divergent_comparison_fixture(index=1),
            unstable_comparison_fixture(index=2),
        ],
        config=history_config(min_comparison_count=3),
    )
    assert sample_dominates.status == "incomplete_comparison_history"

    divergent_dominates_unstable = build_history(
        comparisons=[
            complete_comparison_fixture(index=1),
            divergent_comparison_fixture(index=2),
            unstable_comparison_fixture(index=3),
        ],
        config=history_config(),
    )
    assert divergent_dominates_unstable.status == "divergent_comparison_history"

    unstable_dominates_incomplete = build_history(
        comparisons=[
            complete_comparison_fixture(index=1),
            incomplete_comparison_fixture(index=2),
            unstable_comparison_fixture(index=3),
        ],
        config=history_config(max_divergent_comparison_ratio=Decimal("1.0000")),
    )
    assert unstable_dominates_incomplete.status == "unstable_comparison_history"

    relaxed_mixed = build_history(
        comparisons=[
            complete_comparison_fixture(index=1),
            incomplete_comparison_fixture(index=2),
            divergent_comparison_fixture(index=3),
            unstable_comparison_fixture(index=4),
        ],
        config=history_config(
            max_incomplete_comparison_ratio=Decimal("1.0000"),
            max_divergent_comparison_ratio=Decimal("1.0000"),
            max_unstable_comparison_ratio=Decimal("1.0000"),
        ),
    )
    assert relaxed_mixed.status == "proposal_evidence_comparison_history_ready"


def test_trade_proposal_evidence_comparison_history_quantizes_half_even_ratios():
    base = complete_comparison_fixture(index=1)
    comparisons = [
        replace(
            base,
            generated_at=datetime(2026, 9, 11, tzinfo=UTC) + timedelta(minutes=offset),
        )
        for offset in range(31)
    ]
    comparisons.append(
        replace(
            divergent_comparison_fixture(index=2),
            generated_at=datetime(2026, 9, 11, tzinfo=UTC) + timedelta(minutes=31),
        )
    )

    report = build_history(comparisons=comparisons)

    assert report.comparison_count == 32
    assert report.divergent_comparison_ratio == Decimal("0.0312")
    assert report.status_rows[0].comparison_ratio == Decimal("0.0312")


def test_trade_proposal_evidence_comparison_history_rejects_bad_inputs():
    config = history_config()
    generated_at = datetime(2026, 9, 11, 12, tzinfo=UTC)

    class ExplodingIterable:
        def __iter__(self):
            raise AssertionError("loader-shaped iterable was consumed")

    for bad_input in (
        "[]",
        b"[]",
        {"comparison": complete_comparison_fixture()},
        Path("history.jsonl"),
        '{"serialized": true}',
        (item for item in (complete_comparison_fixture(),)),
        ExplodingIterable(),
        object(),
    ):
        with pytest.raises(ValueError, match="comparisons"):
            build_trade_proposal_evidence_comparison_history_report(
                bad_input,
                config=config,
            generated_at=generated_at,
        )

    for bad_report in (object(), ready_forecast_fixture(), ready_dossier_batch_fixture()):
        with pytest.raises(ValueError, match="TradeProposalEvidenceComparisonReport"):
            build_trade_proposal_evidence_comparison_history_report(
                [bad_report],
                config=config,
                generated_at=generated_at,
            )
    with pytest.raises(ValueError, match="config"):
        build_trade_proposal_evidence_comparison_history_report(
            [complete_comparison_fixture()],
            config=object(),
            generated_at=generated_at,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_trade_proposal_evidence_comparison_history_report(
            [complete_comparison_fixture()],
            config=config,
            generated_at="2026-09-11T12:00:00+00:00",
        )


def test_trade_proposal_evidence_comparison_history_rejects_subclasses_and_duplicate_times():
    comparison = complete_comparison_fixture()

    class ComparisonSubclass(TradeProposalEvidenceComparisonReport):
        pass

    comparison_subclass = ComparisonSubclass(
        generated_at=comparison.generated_at,
        config_version=comparison.config_version,
        report_only=comparison.report_only,
        boundary_statement=comparison.boundary_statement,
        forecast_evidence_generated_at=comparison.forecast_evidence_generated_at,
        dossier_batch_generated_at=comparison.dossier_batch_generated_at,
        forecast_status=comparison.forecast_status,
        dossier_batch_status=comparison.dossier_batch_status,
        forecast_observation_count=comparison.forecast_observation_count,
        forecast_probability_observation_count=(
            comparison.forecast_probability_observation_count
        ),
        forecast_edge_observation_count=comparison.forecast_edge_observation_count,
        dossier_count=comparison.dossier_count,
        complete_dossier_count=comparison.complete_dossier_count,
        incomplete_dossier_ratio=comparison.incomplete_dossier_ratio,
        inconsistent_dossier_ratio=comparison.inconsistent_dossier_ratio,
        unstable_dossier_ratio=comparison.unstable_dossier_ratio,
        mean_probability_loss=comparison.mean_probability_loss,
        worst_bucket_error=comparison.worst_bucket_error,
        mean_edge_gap_ratio=comparison.mean_edge_gap_ratio,
        positive_edge_hit_rate=comparison.positive_edge_hit_rate,
        worst_residual_exposure_ratio=comparison.worst_residual_exposure_ratio,
        status=comparison.status,
        gate_results=comparison.gate_results,
        source_rows=comparison.source_rows,
        metric_rows=comparison.metric_rows,
        finding_rows=comparison.finding_rows,
    )

    with pytest.raises(ValueError, match="TradeProposalEvidenceComparisonReport"):
        build_history(comparisons=[comparison_subclass])
    with pytest.raises(ValueError, match="duplicate"):
        build_history(comparisons=[comparison, comparison])
    with pytest.raises(ValueError, match="duplicate"):
        build_history(
            comparisons=[
                replace(
                    divergent_comparison_fixture(index=2),
                    generated_at=datetime(
                        2026,
                        9,
                        10,
                        21,
                        tzinfo=timezone(timedelta(hours=-4)),
                    ),
                ),
                replace(
                    comparison,
                    generated_at=datetime(2026, 9, 11, 1, tzinfo=timezone(timedelta(0))),
                ),
            ],
        )


def test_trade_proposal_evidence_comparison_history_revalidates_nested_comparison_rows():
    class DriftDatetime(datetime):
        def astimezone(self, tz=None):
            return self

        def replace(self, *args, **kwargs):
            return self

        def __eq__(self, other):
            return self is other

        def __hash__(self):
            return id(self)

    duplicate_instant_one = complete_comparison_fixture(index=1)
    duplicate_instant_two = divergent_comparison_fixture(index=2)
    object.__setattr__(
        duplicate_instant_one,
        "generated_at",
        DriftDatetime(2026, 9, 11, 1, tzinfo=UTC),
    )
    object.__setattr__(
        duplicate_instant_two,
        "generated_at",
        DriftDatetime(2026, 9, 11, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="datetime"):
        build_history(comparisons=[duplicate_instant_one, duplicate_instant_two])

    gate_drift = complete_comparison_fixture(index=1)
    object.__setattr__(gate_drift.gate_results[0], "status", "unknown")
    with pytest.raises(ValueError, match="status"):
        build_history(comparisons=[gate_drift])

    source_drift = complete_comparison_fixture(index=2)
    object.__setattr__(source_drift.source_rows[0], "status_category", "approval")
    with pytest.raises(ValueError, match="status_category"):
        build_history(comparisons=[source_drift])

    source_status_drift = complete_comparison_fixture(index=3)
    object.__setattr__(
        source_status_drift.source_rows[0],
        "source_status",
        "approval_workflow",
    )
    with pytest.raises(ValueError, match="source_status"):
        build_history(comparisons=[source_status_drift])

    metric_drift = complete_comparison_fixture(index=3)
    object.__setattr__(metric_drift.metric_rows[0], "observed_value", Decimal("NaN"))
    with pytest.raises(ValueError, match="finite|observed_value"):
        build_history(comparisons=[metric_drift])

    finding_drift = divergent_comparison_fixture(index=4)
    object.__setattr__(finding_drift.finding_rows[0], "severity", "approval")
    with pytest.raises(ValueError, match="severity"):
        build_history(comparisons=[finding_drift])

    finding_code_drift = divergent_comparison_fixture(index=5)
    object.__setattr__(
        finding_code_drift.finding_rows[0],
        "finding_code",
        "approval_workflow",
    )
    with pytest.raises(ValueError, match="finding_code"):
        build_history(comparisons=[finding_code_drift])

    top_level_drift = complete_comparison_fixture(index=5)
    object.__setattr__(top_level_drift, "status", "divergent_evidence_comparison")
    with pytest.raises(ValueError, match="status"):
        build_history(comparisons=[top_level_drift])

    report_only_drift = complete_comparison_fixture(index=6)
    object.__setattr__(report_only_drift, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        build_history(comparisons=[report_only_drift])

    ordered = build_history(
        comparisons=[
            complete_comparison_fixture(index=7),
            divergent_comparison_fixture(index=8),
        ],
        config=history_config(max_divergent_comparison_ratio=Decimal("1.0000")),
    )
    original_count = ordered.complete_comparison_count
    object.__setattr__(
        ordered.status_rows[0],
        "comparison_count",
        999,
    )
    with pytest.raises(ValueError, match="status_rows"):
        replace(ordered, status_rows=ordered.status_rows)
    assert original_count == 1


def test_trade_proposal_evidence_comparison_history_copies_supplied_reports():
    comparison = divergent_comparison_fixture(index=1)
    report = build_history(
        comparisons=[comparison],
        config=history_config(
            max_divergent_comparison_ratio=Decimal("1.0000"),
        ),
    )
    finding_summaries = report.finding_summaries
    status_rows = report.status_rows
    source_transitions = report.source_transitions

    object.__setattr__(comparison.finding_rows[0], "severity", "approval")
    object.__setattr__(comparison.source_rows[0], "source_status", "approval")
    object.__setattr__(comparison.gate_results[0], "status", "unknown")

    assert report.finding_summaries == finding_summaries
    assert report.status_rows == status_rows
    assert report.source_transitions == source_transitions


def test_trade_proposal_evidence_comparison_history_config_and_dataclasses_validate_invariants():
    assert DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT == (
        "This is a report-only proposal evidence comparison history artifact over "
        "supplied proposal evidence comparison reports, not an approval workflow, "
        "proposal approval, approved-proposal selector, latest-decision selector, "
        "decision-resolution process, investment ranking, trade recommendation, "
        "strategy-promotion signal, trade instruction, order instruction, broker "
        "request, order request, account action, account authentication, private-key "
        "handling, wallet signature, live-execution signal, credential workflow, "
        "external-history loader, JSONL reader, scraping workflow, outcome loader, "
        "settlement review, reconciliation process, compliance review, geographic "
        "access analysis, realized false-positive analysis, profitability analysis, "
        "or automatic order-placement authorization."
    )
    with pytest.raises(ValueError, match="config_version"):
        TradeProposalEvidenceComparisonHistoryConfig(config_version="")
    with pytest.raises(ValueError, match="min_comparison_count"):
        TradeProposalEvidenceComparisonHistoryConfig(
            config_version="comparison-history-v1",
            min_comparison_count=-1,
        )
    with pytest.raises(ValueError, match="max_divergent_comparison_ratio"):
        TradeProposalEvidenceComparisonHistoryConfig(
            config_version="comparison-history-v1",
            max_divergent_comparison_ratio=Decimal("1.0001"),
        )
    with pytest.raises(ValueError, match="max_unstable_comparison_ratio"):
        TradeProposalEvidenceComparisonHistoryConfig(
            config_version="comparison-history-v1",
            max_unstable_comparison_ratio=1,
        )
    with pytest.raises(ValueError, match="boundary_statement"):
        TradeProposalEvidenceComparisonHistoryConfig(
            config_version="comparison-history-v1",
            boundary_statement="history",
        )

    flexible_boundary = (
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT.replace(
            ", ",
            " ,  ",
        )
    )
    assert (
        TradeProposalEvidenceComparisonHistoryConfig(
            config_version="comparison-history-v1",
            boundary_statement=flexible_boundary,
        ).boundary_statement
        == flexible_boundary
    )

    report = build_history()
    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(ValueError, match="gate_name"):
        TradeProposalEvidenceComparisonHistoryGateResult(
            gate_name="approval_workflow",
            status="pass",
            message="bad",
        )
    with pytest.raises(ValueError, match="observed_value"):
        replace(report.gate_results[0], observed_value=True)
    with pytest.raises(ValueError, match="observed_value"):
        replace(report.gate_results[0], observed_value=1.0)
    with pytest.raises(ValueError, match="comparison_status"):
        TradeProposalEvidenceComparisonHistoryStatusRow(
            comparison_status="approval_workflow",
            comparison_count=1,
            comparison_ratio=Decimal("1.0000"),
        )
    with pytest.raises(ValueError, match="finding_code"):
        TradeProposalEvidenceComparisonHistoryFindingSummary(
            finding_code="",
            severity="divergent",
            source_name="comparison",
            comparison_count=1,
        )
    with pytest.raises(ValueError, match="known comparison finding"):
        TradeProposalEvidenceComparisonHistoryFindingSummary(
            finding_code="forecast_evidence_incomplete",
            severity="unstable",
            source_name="comparison",
            comparison_count=1,
        )
    with pytest.raises(ValueError, match="transition_count"):
        TradeProposalEvidenceComparisonHistorySourceTransition(
            source_name="forecast_evidence",
            from_source_status="paper_review_ready",
            to_source_status="insufficient_evidence",
            transition_count=0,
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="status_rows"):
        replace(report, status_rows=tuple(reversed(report.status_rows)))
    with pytest.raises(ValueError, match="source_transitions"):
        replace(report, source_transitions=tuple(reversed(report.source_transitions)))
    with pytest.raises(ValueError, match="gate_results"):
        replace(report, gate_results=list(report.gate_results))
    with pytest.raises(ValueError, match="gate_results"):
        replace(
            report,
            gate_results=(
                replace(report.gate_results[0], observed_value=999),
                *report.gate_results[1:],
            ),
        )
    with pytest.raises(ValueError, match="gate_results"):
        replace(
            report,
            gate_results=(
                replace(report.gate_results[0], observed_value=Decimal("3")),
                *report.gate_results[1:],
            ),
        )
    with pytest.raises(ValueError, match="gate_results"):
        replace(
            report,
            gate_results=(
                replace(report.gate_results[0], threshold=-1),
                *report.gate_results[1:],
            ),
        )
    with pytest.raises(ValueError, match="gate_results"):
        replace(
            report,
            gate_results=(
                report.gate_results[0],
                replace(report.gate_results[1], observed_value=0),
                *report.gate_results[2:],
            ),
        )
    with pytest.raises(ValueError, match="finding_summaries"):
        replace(
            report,
            finding_summaries=(
                replace(report.finding_summaries[0], comparison_count=999),
                *report.finding_summaries[1:],
            ),
        )
    with pytest.raises(ValueError, match="source_transitions"):
        replace(
            report,
            source_transitions=(
                replace(report.source_transitions[0], transition_count=999),
                *report.source_transitions[1:],
            ),
        )
    with pytest.raises(ValueError, match="source_transitions"):
        replace(report, source_transitions=())


def test_trade_proposal_evidence_comparison_history_log_appends_jsonl_report(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_report(
        [
            complete_comparison_fixture(index=1),
            divergent_comparison_fixture(index=2),
            unstable_comparison_fixture(index=3),
        ],
        config=history_config(
            max_divergent_comparison_ratio=Decimal("1.0000"),
            max_unstable_comparison_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(
            2026,
            9,
            11,
            22,
            30,
            tzinfo=timezone(timedelta(hours=8)),
        ),
    )
    log = TradeProposalEvidenceComparisonHistoryLog(
        path=tmp_path / "nested" / "comparison-history.jsonl",
    )

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].startswith('{"boundary_statement"')
    stored = json.loads(lines[0])
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-09-11T14:30:00+00:00"
    assert stored["divergent_comparison_ratio"] == "0.3333"
    assert stored["status_rows"][0]["comparison_ratio"] == "0.3333"
    assert stored["source_transitions"][0]["source_name"] == "dossier_batch"


def test_trade_proposal_evidence_comparison_history_log_validates_before_open(tmp_path):
    report = build_history()
    object.__setattr__(report.status_rows[0], "comparison_ratio", Decimal("NaN"))
    log = TradeProposalEvidenceComparisonHistoryLog(
        path=tmp_path / "comparison-history.jsonl",
    )

    with pytest.raises(ValueError, match="finite|comparison_ratio"):
        log.append(report)

    assert not log.path.exists()

    existing_log = TradeProposalEvidenceComparisonHistoryLog(
        path=tmp_path / "existing.jsonl",
    )
    existing_log.path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="finite|comparison_ratio"):
        existing_log.append(report)
    assert existing_log.path.read_text(encoding="utf-8") == "existing\n"

    with pytest.raises(ValueError, match="TradeProposalEvidenceComparisonHistoryReport"):
        TradeProposalEvidenceComparisonHistoryLog(
            path=tmp_path / "bad-input.jsonl",
        ).append(object())
    assert not (tmp_path / "bad-input.jsonl").exists()

import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tests.test_proposal_review_summary import (
    proposal_for_source,
    review_record,
    summary_report,
)
from polymarket_alpha_lab.proposal_review_quality import (
    TradeProposalReviewQualityConfig,
    TradeProposalReviewQualityGateResult,
    TradeProposalReviewQualityLog,
    TradeProposalReviewQualityReasonTrend,
    TradeProposalReviewQualityReport,
    build_trade_proposal_review_quality_report,
)


DEFAULT_REVIEW_QUALITY_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review quality artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, or automatic order-placement "
    "authorization."
)


def quality_report(summaries, **overrides):
    values = {
        "summaries": summaries,
        "config": TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            min_summary_report_count=1,
            min_total_review_record_count=1,
            max_duplicate_source_proposal_count=10,
        ),
        "generated_at": datetime(2026, 9, 5, 9, tzinfo=timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return build_trade_proposal_review_quality_report(**values)


def rejected_review(index, reason_codes=("liquidity_exit_risk",), **overrides):
    values = {
        "proposal": proposal_for_source(index, market_slug=f"market-{index}"),
        "decision": "rejected",
        "review_reason_codes": reason_codes,
        "review_rationale": "Rejected after checking review-quality proxy inputs.",
        "recorded_at": datetime(2026, 9, 3, 12, index, tzinfo=UTC),
    }
    values.update(overrides)
    return review_record(**values)


def approved_review(index, **overrides):
    values = {
        "proposal": proposal_for_source(index, market_slug=f"market-{index}"),
        "recorded_at": datetime(2026, 9, 3, 12, index, tzinfo=UTC),
    }
    values.update(overrides)
    return review_record(**values)


def ready_quality_report():
    first = summary_report(
        [
            review_record(
                proposal=proposal_for_source(1, market_slug="alpha-market"),
                recorded_at=datetime(2026, 9, 3, 12, 1, tzinfo=UTC),
            ),
            rejected_review(2, ("liquidity_exit_risk",)),
        ],
        generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
    )
    second = summary_report(
        [
            review_record(
                proposal=proposal_for_source(3, market_slug="beta-market"),
                recorded_at=datetime(2026, 9, 4, 12, 3, tzinfo=UTC),
            ),
            rejected_review(4, ("resolution_ambiguity",)),
        ],
        generated_at=datetime(2026, 9, 5, 8, tzinfo=UTC),
    )
    return quality_report([second, first])


def test_build_trade_proposal_review_quality_report_counts_quality_gates():
    first = summary_report(
        [
            review_record(
                proposal=proposal_for_source(1, market_slug="alpha-market"),
                recorded_at=datetime(2026, 9, 3, 12, 1, tzinfo=UTC),
            ),
            rejected_review(2, ("liquidity_exit_risk",)),
        ],
        generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
    )
    second = summary_report(
        [
            review_record(
                proposal=proposal_for_source(3, market_slug="beta-market"),
                recorded_at=datetime(2026, 9, 4, 12, 3, tzinfo=UTC),
            ),
            rejected_review(4, ("resolution_ambiguity",)),
        ],
        generated_at=datetime(2026, 9, 5, 8, tzinfo=UTC),
    )

    report = quality_report([second, first])

    assert report.generated_at == datetime(2026, 9, 5, 13, tzinfo=UTC)
    assert report.config_version == "quality-v1"
    assert report.report_only is True
    assert report.summary_report_count == 2
    assert report.first_summary_generated_at == datetime(2026, 9, 4, 8, tzinfo=UTC)
    assert report.last_summary_generated_at == datetime(2026, 9, 5, 8, tzinfo=UTC)
    assert report.total_review_record_count == 4
    assert report.summed_unique_source_proposal_count == 4
    assert report.total_duplicate_source_proposal_count == 0
    assert report.approved_decision_count == 2
    assert report.rejected_decision_count == 2
    assert report.overall_rejection_ratio == Decimal("0.5000")
    assert report.latest_summary_rejection_ratio == Decimal("0.5000")
    assert report.worst_summary_rejection_ratio == Decimal("0.5000")
    assert report.max_reason_code_rejection_share == Decimal("0.5000")
    assert report.duplicate_source_proposal_ratio == Decimal("0.0000")
    assert report.status == "proposal_review_quality_ready"
    assert tuple(row.gate_name for row in report.gate_results) == (
        "data_integrity",
        "sample_size",
        "rejection_ratio",
        "reason_concentration",
        "duplicate_source_review_volume",
    )
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.reason_code for row in report.reason_trends) == (
        "liquidity_exit_risk",
        "resolution_ambiguity",
    )


def test_trade_proposal_review_quality_statuses_cover_empty_sample_and_thresholds():
    empty = quality_report([])
    assert empty.summary_report_count == 0
    assert empty.first_summary_generated_at is None
    assert empty.last_summary_generated_at is None
    assert empty.total_review_record_count == 0
    assert empty.summed_unique_source_proposal_count == 0
    assert empty.total_duplicate_source_proposal_count == 0
    assert empty.approved_decision_count == 0
    assert empty.rejected_decision_count == 0
    assert empty.overall_rejection_ratio is None
    assert empty.latest_summary_rejection_ratio is None
    assert empty.worst_summary_rejection_ratio is None
    assert empty.max_reason_code_rejection_share is None
    assert empty.duplicate_source_proposal_ratio is None
    assert empty.reason_trends == ()
    assert empty.status == "incomplete_review_data"

    insufficient = quality_report(
        [
            summary_report(
                [approved_review(10), approved_review(11)],
                generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
            )
        ],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            min_summary_report_count=1,
            min_total_review_record_count=3,
            max_duplicate_source_proposal_count=10,
        ),
    )
    assert insufficient.total_review_record_count == 2
    assert insufficient.status == "insufficient_review_sample"

    high_rejection = quality_report(
        [
            summary_report(
                [rejected_review(20, ("liquidity_exit_risk",))],
                generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
            )
        ],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("0.2500"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
    )
    assert high_rejection.overall_rejection_ratio == Decimal("1.0000")
    assert high_rejection.status == "unstable_review_quality"

    concentrated_reason = quality_report(
        [
            summary_report(
                [
                    approved_review(30),
                    rejected_review(31, ("liquidity_exit_risk",)),
                    rejected_review(32, ("liquidity_exit_risk",)),
                ],
                generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
            )
        ],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("0.5000"),
            max_duplicate_source_proposal_count=10,
        ),
    )
    assert concentrated_reason.max_reason_code_rejection_share == Decimal("1.0000")
    assert concentrated_reason.status == "unstable_review_quality"

    duplicate_proposal = proposal_for_source(40, market_slug="duplicate-market")
    duplicate_volume = quality_report(
        [
            summary_report(
                [
                    review_record(
                        proposal=duplicate_proposal,
                        recorded_at=datetime(2026, 9, 3, 12, 40, tzinfo=UTC),
                    ),
                    review_record(
                        proposal=duplicate_proposal,
                        recorded_at=datetime(2026, 9, 3, 12, 41, tzinfo=UTC),
                    ),
                ],
                generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
            )
        ],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_duplicate_source_proposal_count=0,
        ),
    )
    assert duplicate_volume.total_duplicate_source_proposal_count == 1
    assert duplicate_volume.duplicate_source_proposal_ratio == Decimal("0.5000")
    assert duplicate_volume.status == "unstable_review_quality"

    empty_summary = summary_report(
        [],
        generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
    )
    no_review_decisions = quality_report(
        [empty_summary],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            min_summary_report_count=1,
            min_total_review_record_count=0,
            max_duplicate_source_proposal_count=10,
        ),
    )
    gates = {row.gate_name: row for row in no_review_decisions.gate_results}
    assert gates["sample_size"].status == "fail"
    assert gates["rejection_ratio"].status == "incomplete"
    assert gates["duplicate_source_review_volume"].status == "incomplete"
    assert no_review_decisions.status == "insufficient_review_sample"


def test_trade_proposal_review_quality_reason_trends_are_deterministic():
    first = summary_report(
        [
            rejected_review(50, ("liquidity_exit_risk", "model_confidence")),
            rejected_review(51, ("resolution_ambiguity",)),
        ],
        generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
    )
    second = summary_report(
        [
            approved_review(52),
            rejected_review(53, ("liquidity_exit_risk",)),
        ],
        generated_at=datetime(2026, 9, 5, 8, tzinfo=UTC),
    )
    third = summary_report(
        [
            rejected_review(54, ("model_confidence",)),
            rejected_review(55, ("model_confidence", "resolution_ambiguity")),
        ],
        generated_at=datetime(2026, 9, 6, 8, tzinfo=UTC),
    )

    report = quality_report([third, first, second])

    assert tuple(
        (
            row.reason_code,
            row.summary_report_count,
            row.total_rejected_decision_count,
            row.max_rejected_decision_ratio,
            row.latest_rejected_decision_ratio,
        )
        for row in report.reason_trends
    ) == (
        ("liquidity_exit_risk", 2, 2, Decimal("1.0000"), Decimal("1.0000")),
        ("model_confidence", 2, 3, Decimal("1.0000"), Decimal("1.0000")),
        ("resolution_ambiguity", 2, 2, Decimal("0.5000"), Decimal("0.5000")),
    )


def test_trade_proposal_review_quality_gate_results_explain_thresholds():
    duplicate_proposal = proposal_for_source(56, market_slug="failing-market")
    report = quality_report(
        [
            summary_report(
                [
                    rejected_review(
                        57,
                        ("liquidity_exit_risk",),
                        proposal=duplicate_proposal,
                        recorded_at=datetime(2026, 9, 3, 12, 1, tzinfo=UTC),
                    ),
                    rejected_review(
                        58,
                        ("liquidity_exit_risk",),
                        proposal=duplicate_proposal,
                        recorded_at=datetime(2026, 9, 3, 12, 2, tzinfo=UTC),
                    ),
                ],
                generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
            )
        ],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            min_summary_report_count=2,
            min_total_review_record_count=3,
            max_overall_rejection_ratio=Decimal("0.2500"),
            max_worst_summary_rejection_ratio=Decimal("0.7500"),
            max_reason_code_rejection_share=Decimal("0.5000"),
            max_duplicate_source_proposal_ratio=Decimal("0.2500"),
            max_duplicate_source_proposal_count=0,
        ),
    )

    gates = {row.gate_name: row for row in report.gate_results}
    assert {name: row.status for name, row in gates.items()} == {
        "data_integrity": "pass",
        "sample_size": "fail",
        "rejection_ratio": "fail",
        "reason_concentration": "fail",
        "duplicate_source_review_volume": "fail",
    }
    for gate_name in (
        "sample_size",
        "rejection_ratio",
        "reason_concentration",
        "duplicate_source_review_volume",
    ):
        row = gates[gate_name]
        assert row.message == row.message.strip()
        assert row.message
        assert row.observed_value is not None
        assert row.threshold is not None
        assert isinstance(row.observed_value, (Decimal, int, str))
        assert isinstance(row.threshold, (Decimal, int, str))


def test_trade_proposal_review_quality_rejects_bad_inputs_and_duplicates():
    with pytest.raises(ValueError, match="summaries"):
        quality_report(object())
    with pytest.raises(ValueError, match="summaries"):
        quality_report("summaries")
    with pytest.raises(ValueError, match="summaries"):
        quality_report(b"summaries")
    with pytest.raises(ValueError, match="TradeProposalReviewSummaryReport"):
        quality_report([object()])
    with pytest.raises(ValueError, match="config"):
        quality_report([], config=object())
    with pytest.raises(ValueError, match="generated_at"):
        quality_report([], generated_at="2026-09-05")

    first = summary_report(
        [approved_review(56)],
        generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
    )
    second = summary_report(
        [approved_review(57)],
        generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="duplicate summary generated_at"):
        quality_report([first, second])


def test_trade_proposal_review_quality_revalidates_mutated_summaries():
    non_finite_summary = summary_report(
        [rejected_review(56, ("liquidity_exit_risk",))],
        generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
    )
    object.__setattr__(non_finite_summary, "rejection_ratio", Decimal("NaN"))

    with pytest.raises(ValueError, match="finite|rejection_ratio"):
        quality_report([non_finite_summary])

    unsorted_summary = summary_report(
        [
            rejected_review(57, ("liquidity_exit_risk", "resolution_ambiguity")),
            rejected_review(58, ("model_confidence",)),
        ],
        generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
    )
    object.__setattr__(
        unsorted_summary,
        "reason_code_summaries",
        tuple(reversed(unsorted_summary.reason_code_summaries)),
    )

    with pytest.raises(ValueError, match="reason_code_summaries"):
        quality_report([unsorted_summary])


def test_trade_proposal_review_quality_dataclasses_are_frozen_and_validate_invariants():
    config = TradeProposalReviewQualityConfig(
        config_version="quality-v1",
        max_duplicate_source_proposal_count=10,
    )
    report = ready_quality_report()
    gate_row = report.gate_results[0]
    reason_trend = report.reason_trends[0]

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        gate_row.status = "other"
    with pytest.raises(FrozenInstanceError):
        reason_trend.reason_code = "other"
    with pytest.raises(FrozenInstanceError):
        report.status = "other"

    with pytest.raises(ValueError, match="min_summary_report_count"):
        replace(config, min_summary_report_count=-1)
    with pytest.raises(ValueError, match="min_total_review_record_count"):
        replace(config, min_total_review_record_count=True)
    with pytest.raises(ValueError, match="max_overall_rejection_ratio"):
        replace(config, max_overall_rejection_ratio=Decimal("1.0001"))
    with pytest.raises(ValueError, match="max_worst_summary_rejection_ratio"):
        replace(config, max_worst_summary_rejection_ratio=Decimal("-0.0001"))
    with pytest.raises(ValueError, match="max_reason_code_rejection_share"):
        replace(config, max_reason_code_rejection_share=Decimal("NaN"))
    with pytest.raises(ValueError, match="max_duplicate_source_proposal_ratio"):
        replace(config, max_duplicate_source_proposal_ratio=Decimal("1.0001"))
    with pytest.raises(ValueError, match="max_duplicate_source_proposal_count"):
        replace(config, max_duplicate_source_proposal_count=-1)
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(config, boundary_statement="quality report")

    with pytest.raises(ValueError, match="gate_name"):
        replace(gate_row, gate_name="approval_queue")
    with pytest.raises(ValueError, match="status"):
        replace(gate_row, status="ready")
    with pytest.raises(ValueError, match="message"):
        replace(gate_row, message=" ")
    with pytest.raises(ValueError, match="observed_value"):
        replace(gate_row, observed_value=0.5)
    with pytest.raises(ValueError, match="threshold"):
        replace(gate_row, threshold=True)

    with pytest.raises(ValueError, match="summary_report_count"):
        replace(reason_trend, summary_report_count=0)
    with pytest.raises(ValueError, match="total_rejected_decision_count"):
        replace(reason_trend, total_rejected_decision_count=0)
    with pytest.raises(ValueError, match="max_rejected_decision_ratio"):
        replace(reason_trend, max_rejected_decision_ratio=Decimal("1.0001"))
    with pytest.raises(ValueError, match="latest_rejected_decision_ratio"):
        replace(reason_trend, latest_rejected_decision_ratio=Decimal("NaN"))
    with pytest.raises(ValueError, match="latest_rejected_decision_ratio"):
        replace(
            reason_trend,
            max_rejected_decision_ratio=Decimal("0.2500"),
            latest_rejected_decision_ratio=Decimal("0.5000"),
        )

    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="total_review_record_count"):
        replace(report, total_review_record_count=5)
    with pytest.raises(ValueError, match="summed_unique_source_proposal_count"):
        replace(report, summed_unique_source_proposal_count=5)
    with pytest.raises(ValueError, match="total_duplicate_source_proposal_count"):
        replace(report, total_duplicate_source_proposal_count=5)
    with pytest.raises(ValueError, match="overall_rejection_ratio"):
        replace(report, overall_rejection_ratio=Decimal("0.2500"))
    with pytest.raises(ValueError, match="duplicate_source_proposal_ratio"):
        replace(report, duplicate_source_proposal_ratio=Decimal("0.5000"))
    with pytest.raises(ValueError, match="latest_summary_rejection_ratio"):
        replace(report, latest_summary_rejection_ratio=Decimal("1.0001"))
    with pytest.raises(ValueError, match="worst_summary_rejection_ratio"):
        replace(report, worst_summary_rejection_ratio=Decimal("0.2500"))
    with pytest.raises(ValueError, match="latest_summary_rejection_ratio"):
        replace(
            report,
            latest_summary_rejection_ratio=Decimal("0.7500"),
            worst_summary_rejection_ratio=Decimal("0.5000"),
        )
    with pytest.raises(ValueError, match="max_reason_code_rejection_share"):
        replace(report, max_reason_code_rejection_share=Decimal("1.0001"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="approved")
    with pytest.raises(ValueError, match="status"):
        replace(report, status="unstable_review_quality")
    with pytest.raises(ValueError, match="gate_results"):
        replace(report, gate_results=tuple(reversed(report.gate_results)))
    with pytest.raises(ValueError, match="reason_trends"):
        replace(report, reason_trends=tuple(reversed(report.reason_trends)))
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(report, boundary_statement="quality report")


def test_trade_proposal_review_quality_boundary_statement_contract():
    config = TradeProposalReviewQualityConfig(config_version="quality-v1")
    assert config.boundary_statement == DEFAULT_REVIEW_QUALITY_BOUNDARY_STATEMENT

    for boundary_statement in (
        "This is a report-only proposal-review quality artifact.",
        "This is a report-only proposal-review quality artifact, not an approval workflow.",
        (
            "This is a report-only proposal-review quality artifact, not an approval "
            "workflow, trade instruction, order instruction, broker request, order "
            "request."
        ),
    ):
        with pytest.raises(ValueError, match="boundary_statement"):
            TradeProposalReviewQualityConfig(
                config_version="quality-v1",
                boundary_statement=boundary_statement,
            )


def test_trade_proposal_review_quality_log_appends_jsonl_report(tmp_path):
    report = ready_quality_report()
    log = TradeProposalReviewQualityLog(path=tmp_path / "proposal-review-quality.jsonl")

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    stored = json.loads(lines[0])
    assert stored["generated_at"] == "2026-09-05T13:00:00+00:00"
    assert stored["config_version"] == "quality-v1"
    assert stored["report_only"] is True
    assert stored["summary_report_count"] == 2
    assert stored["first_summary_generated_at"] == "2026-09-04T08:00:00+00:00"
    assert stored["last_summary_generated_at"] == "2026-09-05T08:00:00+00:00"
    assert stored["total_review_record_count"] == 4
    assert stored["summed_unique_source_proposal_count"] == 4
    assert stored["total_duplicate_source_proposal_count"] == 0
    assert stored["approved_decision_count"] == 2
    assert stored["rejected_decision_count"] == 2
    assert stored["overall_rejection_ratio"] == "0.5000"
    assert stored["latest_summary_rejection_ratio"] == "0.5000"
    assert stored["worst_summary_rejection_ratio"] == "0.5000"
    assert stored["max_reason_code_rejection_share"] == "0.5000"
    assert stored["duplicate_source_proposal_ratio"] == "0.0000"
    assert stored["status"] == "proposal_review_quality_ready"
    assert [
        (row["gate_name"], row["status"])
        for row in stored["gate_results"]
    ] == [
        ("data_integrity", "pass"),
        ("sample_size", "pass"),
        ("rejection_ratio", "pass"),
        ("reason_concentration", "pass"),
        ("duplicate_source_review_volume", "pass"),
    ]
    assert all(row["message"] for row in stored["gate_results"])
    assert stored["reason_trends"] == [
        {
            "latest_rejected_decision_ratio": "1.0000",
            "max_rejected_decision_ratio": "1.0000",
            "reason_code": "liquidity_exit_risk",
            "summary_report_count": 1,
            "total_rejected_decision_count": 1,
        },
        {
            "latest_rejected_decision_ratio": "1.0000",
            "max_rejected_decision_ratio": "1.0000",
            "reason_code": "resolution_ambiguity",
            "summary_report_count": 1,
            "total_rejected_decision_count": 1,
        },
    ]


def test_trade_proposal_review_quality_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    report = quality_report(
        [
            summary_report(
                [approved_review(56)],
                generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
            )
        ]
    )
    log = TradeProposalReviewQualityLog(
        path=str(tmp_path / "nested" / "proposal-review-quality.jsonl"),
    )

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["summary_report_count"] == 1
    assert json.loads(lines[1])["summary_report_count"] == 1


def test_trade_proposal_review_quality_log_rejects_invalid_paths_and_inputs(tmp_path):
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewQualityLog(path=object())
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewQualityLog(path=" ")

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewQualityLog(path=existing_dir)

    existing_file = tmp_path / "parent-file"
    existing_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        TradeProposalReviewQualityLog(path=existing_file / "quality.jsonl")

    path = tmp_path / "proposal-review-quality.jsonl"
    log = TradeProposalReviewQualityLog(path=path)
    with pytest.raises(ValueError, match="TradeProposalReviewQualityReport"):
        log.append(object())
    assert not path.exists()


def test_trade_proposal_review_quality_log_preserves_existing_file_when_validation_fails(
    tmp_path,
):
    report = ready_quality_report()
    nested_gate_row = report.gate_results[2]
    object.__setattr__(nested_gate_row, "observed_value", Decimal("NaN"))
    path = tmp_path / "proposal-review-quality.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = TradeProposalReviewQualityLog(path=path)

    with pytest.raises(ValueError, match="finite|observed_value"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_trade_proposal_review_quality_log_rejects_non_finite_decimal_before_open(
    tmp_path,
):
    report = ready_quality_report()
    object.__setattr__(report, "overall_rejection_ratio", Decimal("NaN"))
    log = TradeProposalReviewQualityLog(path=tmp_path / "proposal-review-quality.jsonl")

    with pytest.raises(ValueError, match="finite|overall_rejection_ratio"):
        log.append(report)

    assert not log.path.exists()

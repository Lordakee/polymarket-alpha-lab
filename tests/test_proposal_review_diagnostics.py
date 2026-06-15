import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tests.test_proposal_review_summary import (
    proposal_for_source,
    review_record,
)
from polymarket_alpha_lab.proposal_review_diagnostics import (
    TradeProposalReviewDiagnosticBucketRow,
    TradeProposalReviewDiagnosticConfig,
    TradeProposalReviewDiagnosticLog,
    TradeProposalReviewDiagnosticReasonRow,
    TradeProposalReviewDiagnosticReport,
    TradeProposalReviewDiagnosticSourceRow,
    build_trade_proposal_review_diagnostic_report,
)


DEFAULT_REVIEW_DIAGNOSTIC_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review diagnostic artifact using rejected "
    "human-review decisions as a false-positive proxy, not realized false-positive "
    "confirmation, approval workflow, trade instruction, order instruction, broker "
    "request, order request, account action, account authentication, private-key "
    "handling, wallet signature, live-execution signal, credential workflow, "
    "manual execution import, strategy-promotion signal, settlement review, "
    "reconciliation process, or automatic order-placement authorization."
)


def diagnostic_report(records, **overrides):
    values = {
        "records": records,
        "config": TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            min_review_record_count=1,
            max_source_rows=20,
        ),
        "generated_at": datetime(2026, 9, 6, 9, tzinfo=timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return build_trade_proposal_review_diagnostic_report(**values)


def approved_review(index, **overrides):
    values = {
        "proposal": proposal_for_source(index, market_slug=f"market-{index}"),
        "recorded_at": datetime(2026, 9, 3, 12, index, tzinfo=UTC),
    }
    values.update(overrides)
    return review_record(**values)


def rejected_review(index, reason_codes=("liquidity_exit_risk",), **overrides):
    values = {
        "proposal": proposal_for_source(index, market_slug=f"market-{index}"),
        "decision": "rejected",
        "review_reason_codes": reason_codes,
        "review_rationale": (
            "Rejected after checking proposal-review diagnostic proxy inputs."
        ),
        "recorded_at": datetime(2026, 9, 3, 12, index, tzinfo=UTC),
    }
    values.update(overrides)
    return review_record(**values)


def test_build_trade_proposal_review_diagnostic_report_counts_rejection_proxy_rows():
    duplicate_proposal = proposal_for_source(4, market_slug="duplicate-market")
    records = [
        rejected_review(
            2,
            ("liquidity_exit_risk", "model_confidence"),
            proposal=proposal_for_source(
                2,
                market_slug="alpha-market",
                strategy_type="mean_reversion",
                risk_tags=("liquidity", "resolution"),
            ),
        ),
        approved_review(
            1,
            proposal=proposal_for_source(
                1,
                market_slug="alpha-market",
                strategy_type="mean_reversion",
                risk_tags=("liquidity",),
            ),
        ),
        rejected_review(
            3,
            ("resolution_ambiguity",),
            proposal=proposal_for_source(
                3,
                market_slug="beta-market",
                strategy_type="event_value",
                risk_tags=("resolution",),
            ),
        ),
        rejected_review(
            4,
            ("liquidity_exit_risk",),
            proposal=duplicate_proposal,
            recorded_at=datetime(2026, 9, 3, 12, 4, tzinfo=UTC),
        ),
        approved_review(
            5,
            proposal=duplicate_proposal,
            recorded_at=datetime(2026, 9, 3, 12, 5, tzinfo=UTC),
        ),
    ]

    report = diagnostic_report(list(reversed(records)))

    assert report.generated_at == datetime(2026, 9, 6, 13, tzinfo=UTC)
    assert report.config_version == "diagnostic-v1"
    assert report.report_only is True
    assert report.review_record_count == 5
    assert report.unique_source_proposal_count == 4
    assert report.duplicate_source_proposal_review_count == 1
    assert report.approved_decision_count == 2
    assert report.rejected_decision_count == 3
    assert report.rejected_source_proposal_count == 3
    assert report.rejected_decision_ratio == Decimal("0.6000")
    assert report.rejected_source_proposal_ratio == Decimal("0.7500")
    assert report.max_reason_code_rejected_decision_share == Decimal("0.6667")
    assert report.first_recorded_at == datetime(2026, 9, 3, 12, 1, tzinfo=UTC)
    assert report.last_recorded_at == datetime(2026, 9, 3, 12, 5, tzinfo=UTC)
    assert report.status == "high_rejection_proxy"
    assert tuple(row.reason_code for row in report.reason_rows) == (
        "liquidity_exit_risk",
        "model_confidence",
        "resolution_ambiguity",
    )
    assert tuple(row.bucket_type for row in report.bucket_rows).count("market_slug") == 3
    source_rows_by_id = {row.source_proposal_packet_id: row for row in report.source_rows}
    assert set(source_rows_by_id) == {
        duplicate_proposal.proposal_packet_id,
        records[0].source_proposal_packet_id,
        records[2].source_proposal_packet_id,
    }
    assert (
        source_rows_by_id[duplicate_proposal.proposal_packet_id].review_record_count
        == 2
    )


def ready_diagnostic_report():
    return diagnostic_report(
        [
            approved_review(10),
            approved_review(11),
            rejected_review(12, ("liquidity_exit_risk", "resolution_ambiguity")),
            rejected_review(13, ("model_confidence",)),
        ],
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("0.7500"),
            max_rejected_source_proposal_ratio=Decimal("0.7500"),
            max_reason_code_rejected_decision_share=Decimal("0.7500"),
            max_source_rows=20,
        ),
    )


def test_trade_proposal_review_diagnostic_statuses_cover_empty_sample_and_thresholds():
    empty = diagnostic_report([])
    assert empty.review_record_count == 0
    assert empty.unique_source_proposal_count == 0
    assert empty.duplicate_source_proposal_review_count == 0
    assert empty.approved_decision_count == 0
    assert empty.rejected_decision_count == 0
    assert empty.rejected_source_proposal_count == 0
    assert empty.rejected_decision_ratio is None
    assert empty.rejected_source_proposal_ratio is None
    assert empty.max_reason_code_rejected_decision_share is None
    assert empty.first_recorded_at is None
    assert empty.last_recorded_at is None
    assert empty.reason_rows == ()
    assert empty.bucket_rows == ()
    assert empty.source_rows == ()
    assert empty.status == "incomplete_review_data"

    insufficient = diagnostic_report(
        [approved_review(20)],
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            min_review_record_count=2,
        ),
    )
    assert insufficient.status == "insufficient_review_sample"

    high_decision_ratio = diagnostic_report(
        [approved_review(21), rejected_review(22, ("liquidity_exit_risk",))],
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("0.2500"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
    )
    assert high_decision_ratio.rejected_decision_ratio == Decimal("0.5000")
    assert high_decision_ratio.status == "high_rejection_proxy"

    high_source_ratio = diagnostic_report(
        [rejected_review(23, ("liquidity_exit_risk",)), approved_review(24)],
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("0.2500"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
    )
    assert high_source_ratio.rejected_source_proposal_ratio == Decimal("0.5000")
    assert high_source_ratio.status == "high_rejection_proxy"

    concentrated_reason = diagnostic_report(
        [
            approved_review(25),
            rejected_review(26, ("liquidity_exit_risk",)),
            rejected_review(27, ("liquidity_exit_risk",)),
        ],
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("0.5000"),
        ),
    )
    assert concentrated_reason.max_reason_code_rejected_decision_share == Decimal(
        "1.0000"
    )
    assert concentrated_reason.status == "high_rejection_proxy"

    ready = diagnostic_report([approved_review(28), approved_review(29)])
    assert ready.status == "diagnostics_ready"


def test_trade_proposal_review_diagnostic_reason_rows_are_deterministic():
    report = diagnostic_report(
        [
            rejected_review(30, ("resolution_ambiguity", "liquidity_exit_risk")),
            rejected_review(31, ("model_confidence", "liquidity_exit_risk")),
            approved_review(32),
        ],
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
        ),
    )

    assert tuple(
        (
            row.reason_code,
            row.rejected_decision_count,
            row.rejected_source_proposal_count,
            row.rejected_decision_share,
        )
        for row in report.reason_rows
    ) == (
        ("liquidity_exit_risk", 2, 2, Decimal("1.0000")),
        ("model_confidence", 1, 1, Decimal("0.5000")),
        ("resolution_ambiguity", 1, 1, Decimal("0.5000")),
    )


def test_trade_proposal_review_diagnostic_bucket_rows_respect_config():
    alpha_approved = approved_review(
        40,
        proposal=proposal_for_source(
            40,
            market_slug="alpha-market",
            strategy_type="relative_value",
            risk_tags=("liquidity", "event-risk"),
        ),
    )
    alpha_rejected = rejected_review(
        41,
        ("liquidity_exit_risk",),
        proposal=proposal_for_source(
            41,
            market_slug="alpha-market",
            strategy_type="relative_value",
            risk_tags=("liquidity",),
        ),
    )
    beta_rejected = rejected_review(
        42,
        ("resolution_ambiguity",),
        proposal=proposal_for_source(
            42,
            market_slug="beta-market",
            strategy_type="macro_event",
            risk_tags=("event-risk", "resolution"),
        ),
    )

    report = diagnostic_report([beta_rejected, alpha_approved, alpha_rejected])
    rows = {
        (row.bucket_type, row.bucket_value): row
        for row in report.bucket_rows
    }
    assert rows[("market_slug", "alpha-market")].review_record_count == 2
    assert rows[("market_slug", "alpha-market")].rejected_decision_count == 1
    assert rows[("market_slug", "alpha-market")].rejected_decision_ratio == Decimal(
        "0.5000"
    )
    assert rows[("strategy_type", "relative_value")].unique_source_proposal_count == 2
    assert rows[("risk_tag", "event-risk")].review_record_count == 2
    assert "review_focus" in {row.bucket_type for row in report.bucket_rows}

    compact = diagnostic_report(
        [beta_rejected, alpha_approved, alpha_rejected],
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            include_risk_tag_buckets=False,
            include_review_focus_buckets=False,
        ),
    )
    assert {row.bucket_type for row in compact.bucket_rows} == {
        "market_slug",
        "strategy_type",
    }


def test_trade_proposal_review_diagnostic_source_rows_are_limited_and_sorted():
    shared = proposal_for_source(50, market_slug="shared-market")
    report = diagnostic_report(
        [
            rejected_review(51, ("liquidity_exit_risk",), proposal=shared),
            rejected_review(
                52,
                ("model_confidence",),
                proposal=shared,
                recorded_at=datetime(2026, 9, 3, 12, 52, tzinfo=UTC),
            ),
            rejected_review(53, ("resolution_ambiguity",)),
            rejected_review(54, ("liquidity_exit_risk",)),
        ],
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
            max_source_rows=2,
        ),
    )

    assert len(report.source_rows) == 2
    assert report.source_rows[0].source_proposal_packet_id == shared.proposal_packet_id
    assert report.source_rows[0].review_record_count == 2
    assert report.source_rows[0].rejected_decision_count == 2
    assert report.source_rows[0].reason_codes == (
        "liquidity_exit_risk",
        "model_confidence",
    )

    suppressed = diagnostic_report(
        [rejected_review(55, ("liquidity_exit_risk",))],
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_source_rows=0,
        ),
    )
    assert suppressed.rejected_source_proposal_count == 1
    assert suppressed.source_rows == ()


def test_trade_proposal_review_diagnostic_rejects_bad_inputs_and_duplicates():
    with pytest.raises(ValueError, match="records"):
        diagnostic_report(object())
    with pytest.raises(ValueError, match="records"):
        diagnostic_report("records")
    with pytest.raises(ValueError, match="records"):
        diagnostic_report(b"records")
    with pytest.raises(ValueError, match="TradeProposalReviewRecord"):
        diagnostic_report([object()])
    with pytest.raises(ValueError, match="config"):
        diagnostic_report([], config=object())
    with pytest.raises(ValueError, match="generated_at"):
        diagnostic_report([], generated_at="2026-09-06")

    record = approved_review(56)
    with pytest.raises(ValueError, match="duplicate review_record_id"):
        diagnostic_report([record, record])


def test_trade_proposal_review_diagnostic_revalidates_mutated_records():
    bad_time = approved_review(57)
    object.__setattr__(bad_time, "recorded_at", "2026-09-03")
    with pytest.raises(ValueError, match="recorded_at|datetime"):
        diagnostic_report([bad_time])

    bad_reason_codes = rejected_review(58, ("liquidity_exit_risk",))
    object.__setattr__(
        bad_reason_codes,
        "review_reason_codes",
        ("liquidity_exit_risk", "liquidity_exit_risk"),
    )
    with pytest.raises(ValueError, match="review_record_id"):
        diagnostic_report([bad_reason_codes])

    stale_fingerprint = approved_review(59)
    object.__setattr__(stale_fingerprint, "source_proposal_fingerprint", "stale")
    with pytest.raises(ValueError, match="source_proposal_fingerprint"):
        diagnostic_report([stale_fingerprint])


def test_trade_proposal_review_diagnostic_dataclasses_are_frozen_and_validate_invariants():
    config = TradeProposalReviewDiagnosticConfig(config_version="diagnostic-v1")
    report = ready_diagnostic_report()
    reason_row = report.reason_rows[0]
    bucket_row = report.bucket_rows[0]
    source_row = report.source_rows[0]
    ordered_source_row = TradeProposalReviewDiagnosticSourceRow(
        source_proposal_packet_id="source-proposal-test",
        source_proposal_fingerprint="source-proposal-fingerprint",
        first_recorded_at=datetime(2026, 9, 3, 12, tzinfo=UTC),
        last_recorded_at=datetime(2026, 9, 3, 12, 1, tzinfo=UTC),
        review_record_count=2,
        rejected_decision_count=1,
        reason_codes=("a-reason", "z-reason"),
        market_slug="source-market",
        strategy_type="relative_value",
        risk_tags=("a-risk", "z-risk"),
        review_focus=("a-focus", "z-focus"),
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        reason_row.reason_code = "other"
    with pytest.raises(FrozenInstanceError):
        bucket_row.bucket_value = "other"
    with pytest.raises(FrozenInstanceError):
        source_row.market_slug = "other"
    with pytest.raises(FrozenInstanceError):
        report.status = "other"

    with pytest.raises(ValueError, match="min_review_record_count"):
        replace(config, min_review_record_count=True)
    with pytest.raises(ValueError, match="max_rejected_decision_ratio"):
        replace(config, max_rejected_decision_ratio=Decimal("1.0001"))
    with pytest.raises(ValueError, match="max_rejected_source_proposal_ratio"):
        replace(config, max_rejected_source_proposal_ratio=Decimal("-0.0001"))
    with pytest.raises(ValueError, match="max_reason_code_rejected_decision_share"):
        replace(config, max_reason_code_rejected_decision_share=Decimal("NaN"))
    with pytest.raises(ValueError, match="include_market_slug_buckets"):
        replace(config, include_market_slug_buckets=1)
    with pytest.raises(ValueError, match="max_source_rows"):
        replace(config, max_source_rows=-1)
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(config, boundary_statement="diagnostic report")

    with pytest.raises(ValueError, match="rejected_decision_count"):
        replace(reason_row, rejected_decision_count=0)
    with pytest.raises(ValueError, match="rejected_source_proposal_count"):
        replace(reason_row, rejected_source_proposal_count=0)
    with pytest.raises(ValueError, match="rejected_source_proposal_count"):
        replace(reason_row, rejected_source_proposal_count=2)
    with pytest.raises(ValueError, match="rejected_decision_share"):
        replace(reason_row, rejected_decision_share=Decimal("1.0001"))

    with pytest.raises(ValueError, match="bucket_type"):
        replace(bucket_row, bucket_type="reviewer_label")
    with pytest.raises(ValueError, match="review_record_count"):
        replace(bucket_row, review_record_count=0)
    with pytest.raises(ValueError, match="rejected_decision_count"):
        replace(bucket_row, rejected_decision_count=5)
    with pytest.raises(ValueError, match="rejected_decision_ratio"):
        replace(bucket_row, rejected_decision_ratio=Decimal("0.9999"))

    with pytest.raises(ValueError, match="first_recorded_at"):
        replace(
            source_row,
            first_recorded_at=source_row.last_recorded_at + timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ordered_source_row,
            reason_codes=tuple(reversed(ordered_source_row.reason_codes)),
        )
    with pytest.raises(ValueError, match="risk_tags"):
        replace(ordered_source_row, risk_tags=("z-risk", "a-risk"))
    with pytest.raises(ValueError, match="review_focus"):
        replace(ordered_source_row, review_focus=("z-focus", "a-focus"))

    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="review_record_count"):
        replace(report, review_record_count=5)
    with pytest.raises(ValueError, match="duplicate_source_proposal_review_count"):
        replace(report, duplicate_source_proposal_review_count=5)
    with pytest.raises(ValueError, match="rejected_decision_ratio"):
        replace(report, rejected_decision_ratio=Decimal("0.9999"))
    with pytest.raises(ValueError, match="rejected_source_proposal_ratio"):
        replace(report, rejected_source_proposal_ratio=Decimal("0.9999"))
    with pytest.raises(ValueError, match="max_reason_code_rejected_decision_share"):
        replace(report, max_reason_code_rejected_decision_share=Decimal("0.9999"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="approved")
    with pytest.raises(ValueError, match="reason_rows"):
        replace(report, reason_rows=tuple(reversed(report.reason_rows)))
    with pytest.raises(ValueError, match="bucket_rows"):
        replace(report, bucket_rows=tuple(reversed(report.bucket_rows)))
    if len(report.source_rows) > 1:
        with pytest.raises(ValueError, match="source_rows"):
            replace(report, source_rows=tuple(reversed(report.source_rows)))
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(report, boundary_statement="diagnostic report")


def test_trade_proposal_review_diagnostic_dataclasses_reject_impossible_grouped_rows():
    report = ready_diagnostic_report()

    with pytest.raises(ValueError, match="rejected_source_proposal_count"):
        TradeProposalReviewDiagnosticBucketRow(
            bucket_type="market_slug",
            bucket_value="impossible-market",
            review_record_count=3,
            unique_source_proposal_count=3,
            rejected_decision_count=1,
            rejected_source_proposal_count=2,
            rejected_decision_ratio=Decimal("0.3333"),
        )

    with pytest.raises(ValueError, match="rejected_source_proposal_count"):
        replace(
            report,
            approved_decision_count=4,
            rejected_decision_count=0,
            rejected_source_proposal_count=1,
            rejected_decision_ratio=Decimal("0.0000"),
            rejected_source_proposal_ratio=Decimal("0.2500"),
            max_reason_code_rejected_decision_share=None,
            reason_rows=(),
            source_rows=(),
        )

    wrong_reason_rows = (
        replace(report.reason_rows[0], rejected_decision_share=Decimal("1.0000")),
        report.reason_rows[1],
        report.reason_rows[2],
    )
    with pytest.raises(ValueError, match="rejected_decision_share"):
        replace(report, reason_rows=wrong_reason_rows)

    with pytest.raises(ValueError, match="reason_rows"):
        replace(report, reason_rows=(report.reason_rows[0], report.reason_rows[0]))

    with pytest.raises(ValueError, match="bucket_rows"):
        replace(report, bucket_rows=(report.bucket_rows[0], report.bucket_rows[0]))

    if report.source_rows:
        with pytest.raises(ValueError, match="source_rows"):
            replace(report, source_rows=(report.source_rows[0], report.source_rows[0]))


def test_trade_proposal_review_diagnostic_boundary_statement_contract():
    config = TradeProposalReviewDiagnosticConfig(config_version="diagnostic-v1")
    assert config.boundary_statement == DEFAULT_REVIEW_DIAGNOSTIC_BOUNDARY_STATEMENT

    for boundary_statement in (
        "This is a report-only proposal-review diagnostic artifact.",
        (
            "This is a report-only proposal-review diagnostic artifact using rejected "
            "human-review decisions as a false-positive proxy."
        ),
        (
            "This is a report-only proposal-review diagnostic artifact using rejected "
            "human-review decisions as a false-positive proxy, not realized "
            "false-positive confirmation."
        ),
    ):
        with pytest.raises(ValueError, match="boundary_statement"):
            TradeProposalReviewDiagnosticConfig(
                config_version="diagnostic-v1",
                boundary_statement=boundary_statement,
            )


def test_trade_proposal_review_diagnostic_log_appends_jsonl_report(tmp_path):
    report = ready_diagnostic_report()
    log = TradeProposalReviewDiagnosticLog(
        path=tmp_path / "proposal-review-diagnostics.jsonl"
    )

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    stored = json.loads(lines[0])
    assert stored["generated_at"] == "2026-09-06T13:00:00+00:00"
    assert stored["config_version"] == "diagnostic-v1"
    assert stored["report_only"] is True
    assert stored["review_record_count"] == 4
    assert stored["unique_source_proposal_count"] == 4
    assert stored["duplicate_source_proposal_review_count"] == 0
    assert stored["approved_decision_count"] == 2
    assert stored["rejected_decision_count"] == 2
    assert stored["rejected_source_proposal_count"] == 2
    assert stored["rejected_decision_ratio"] == "0.5000"
    assert stored["rejected_source_proposal_ratio"] == "0.5000"
    assert stored["max_reason_code_rejected_decision_share"] == "0.5000"
    assert stored["status"] == "diagnostics_ready"
    assert [row["reason_code"] for row in stored["reason_rows"]] == [
        "liquidity_exit_risk",
        "model_confidence",
        "resolution_ambiguity",
    ]
    assert stored["bucket_rows"]
    assert stored["source_rows"]
    assert isinstance(stored["source_rows"][0]["risk_tags"], list)
    assert isinstance(stored["source_rows"][0]["review_focus"], list)


def test_trade_proposal_review_diagnostic_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    report = diagnostic_report([approved_review(56)])
    log = TradeProposalReviewDiagnosticLog(
        path=str(tmp_path / "nested" / "proposal-review-diagnostics.jsonl"),
    )

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["review_record_count"] == 1
    assert json.loads(lines[1])["review_record_count"] == 1


def test_trade_proposal_review_diagnostic_log_rejects_invalid_paths_and_inputs(tmp_path):
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewDiagnosticLog(path=object())
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewDiagnosticLog(path=" ")

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewDiagnosticLog(path=existing_dir)

    existing_file = tmp_path / "parent-file"
    existing_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        TradeProposalReviewDiagnosticLog(path=existing_file / "diagnostic.jsonl")

    path = tmp_path / "proposal-review-diagnostics.jsonl"
    log = TradeProposalReviewDiagnosticLog(path=path)
    with pytest.raises(ValueError, match="TradeProposalReviewDiagnosticReport"):
        log.append(object())
    assert not path.exists()


def test_trade_proposal_review_diagnostic_log_preserves_existing_file_when_validation_fails(
    tmp_path,
):
    report = ready_diagnostic_report()
    nested_reason_row = report.reason_rows[0]
    object.__setattr__(nested_reason_row, "rejected_decision_share", Decimal("NaN"))
    path = tmp_path / "proposal-review-diagnostics.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = TradeProposalReviewDiagnosticLog(path=path)

    with pytest.raises(ValueError, match="finite|rejected_decision_share"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_trade_proposal_review_diagnostic_log_rejects_non_finite_decimal_before_open(
    tmp_path,
):
    report = ready_diagnostic_report()
    object.__setattr__(report, "rejected_decision_ratio", Decimal("NaN"))
    log = TradeProposalReviewDiagnosticLog(
        path=tmp_path / "proposal-review-diagnostics.jsonl"
    )

    with pytest.raises(ValueError, match="finite|rejected_decision_ratio"):
        log.append(report)

    assert not log.path.exists()

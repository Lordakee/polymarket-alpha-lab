import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.analytics_history import (
    PaperAnalyticsHistoryGateResult,
    PaperAnalyticsHistoryReport,
    PaperAnalyticsHistoryTrend,
)
from polymarket_alpha_lab.domain import MarketScore
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.manual_review_queue import (
    PaperManualReviewCandidate,
    PaperManualReviewConfig,
    PaperManualReviewQueueItem,
    build_paper_manual_review_queue,
)
from polymarket_alpha_lab.proposal_packet import (
    TradeProposalPacketConfig,
    build_trade_proposal_packet,
)
from polymarket_alpha_lab.proposal_review import (
    TradeProposalReviewConfig,
    build_trade_proposal_review_record,
)
from polymarket_alpha_lab.proposal_review_summary import (
    TradeProposalReviewBucketSummary,
    TradeProposalReviewReasonCodeSummary,
    TradeProposalReviewSummaryConfig,
    TradeProposalReviewSummaryLog,
    build_trade_proposal_review_summary_report,
)


DEFAULT_REVIEW_ATTESTATION = (
    "I reviewed this proposal packet and understand this record is not a "
    "trade instruction, order instruction, broker request, order request, "
    "account action, account authentication, private-key handling, wallet "
    "signature, live-execution signal, manual execution import, credential "
    "request, or automatic order-placement authorization."
)

DEFAULT_REVIEW_SUMMARY_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review summary artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, or automatic order-placement "
    "authorization."
)


def market_score(token_id: str, total_bias: Decimal = Decimal("0")) -> MarketScore:
    return MarketScore(
        condition_id="condition-1",
        token_id=token_id,
        activity=Decimal("90") + total_bias,
        liquidity=Decimal("80"),
        spread_quality=Decimal("85"),
        time_structure=Decimal("70"),
        information_structure=Decimal("75"),
        price_behavior=Decimal("65"),
        duplicate_penalty=Decimal("0"),
    )


def ready_history_report() -> PaperAnalyticsHistoryReport:
    gate_results = tuple(
        PaperAnalyticsHistoryGateResult(
            gate_name=gate_name,
            status="pass",
            message=f"{gate_name} is ready for manual review.",
        )
        for gate_name in (
            "data_integrity",
            "sample_size",
            "execution_cost_reality",
            "forecast_edge_quality",
            "risk_drawdown",
        )
    )
    trend = PaperAnalyticsHistoryTrend(
        marked_at=datetime(2026, 9, 1, tzinfo=UTC),
        exit_nav=Decimal("10100"),
        total_exit_pnl=Decimal("100"),
        drawdown=Decimal("0"),
        drawdown_ratio=Decimal("0.0000"),
        exit_depth_shortfall_ratio=Decimal("0.0000"),
        no_exit_depth_cost_basis_ratio=Decimal("0.0000"),
        midpoint_nav_gap_ratio=Decimal("0.0000"),
        breach_count=0,
    )
    return PaperAnalyticsHistoryReport(
        generated_at=datetime(2026, 9, 2, tzinfo=UTC),
        config_version="history-ready",
        first_marked_at=trend.marked_at,
        last_marked_at=trend.marked_at,
        report_count=1,
        candidate_observation_count=250,
        simulated_trade_count=55,
        exited_trade_count=31,
        forward_window_days=28,
        unique_market_count=1,
        unique_strategy_count=1,
        unique_risk_tag_count=1,
        latest_exit_nav=trend.exit_nav,
        latest_total_exit_pnl=trend.total_exit_pnl,
        max_drawdown=trend.drawdown,
        max_drawdown_ratio=trend.drawdown_ratio,
        worst_exit_depth_shortfall_ratio=trend.exit_depth_shortfall_ratio,
        worst_no_exit_depth_cost_basis_ratio=trend.no_exit_depth_cost_basis_ratio,
        worst_midpoint_nav_gap_ratio=trend.midpoint_nav_gap_ratio,
        largest_market_cost_basis_ratio=Decimal("0.1000"),
        largest_risk_tag_cost_basis_ratio=Decimal("0.1000"),
        max_breach_count=0,
        status="paper_review_ready",
        gate_results=gate_results,
        trends=(trend,),
    )


def forecast_observation(index: int) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 9, 1, tzinfo=UTC) + timedelta(hours=index),
        source_packet_id=f"packet-{index}",
        condition_id="condition-1",
        token_id=f"token-{index}",
        market_slug="market-1",
        strategy_type="relative_value",
        risk_tags=("liquidity",),
        predicted_probability=Decimal("0.7000") if index % 2 else Decimal("0.3000"),
        actual_outcome_value=Decimal("1") if index % 2 else Decimal("0"),
        theoretical_edge_ratio=Decimal("0.1200"),
        executable_edge_ratio=Decimal("0.0900"),
        fill_probability=Decimal("0.8000"),
        residual_exposure_ratio=Decimal("0.0000"),
        paper_return_ratio=Decimal("0.1000"),
    )


def ready_forecast_report():
    return build_paper_forecast_evidence_report(
        [forecast_observation(index) for index in range(1, 4)],
        config=PaperForecastEvidenceConfig(
            config_version="forecast-ready",
            min_probability_observations=3,
            min_edge_observations=3,
            max_mean_probability_loss=Decimal("0.1000"),
            max_bucket_error=Decimal("0.3000"),
            max_mean_edge_gap_ratio=Decimal("0.0500"),
            min_positive_edge_hit_rate=Decimal("0.6000"),
            max_residual_exposure_ratio=Decimal("0.1000"),
        ),
        generated_at=datetime(2026, 9, 2, 12, tzinfo=UTC),
    )


def candidate(
    index: int,
    *,
    score: Decimal = Decimal("80.0000"),
    cost_adjusted_edge: Decimal | None = Decimal("0.0500"),
    confidence: Decimal | None = Decimal("0.7000"),
    max_executable_size: Decimal | None = Decimal("100"),
    risk_gate_passed: bool = True,
    risk_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
) -> PaperManualReviewCandidate:
    return PaperManualReviewCandidate(
        queued_at=datetime(2026, 9, 2, tzinfo=UTC) + timedelta(minutes=index),
        packet_id=f"packet-{index}",
        condition_id="condition-1",
        token_id=f"token-{index}",
        market_slug=f"market-{index}",
        market_url=f"https://polymarket.com/event/market-{index}",
        question=f"Will test market {index} resolve yes?",
        outcome_name="Yes",
        source_score=score,
        raw_archive_path=f"archives/market-{index}.json",
        strategy_type="relative_value",
        risk_tags=("liquidity", "event-risk"),
        thesis=f"Candidate {index} has paper evidence.",
        invalidating_conditions="Resolution rule changes or liquidity evaporates.",
        rule_text_hash=f"rule-hash-{index}",
        resolution_source="official source",
        model_probability=Decimal("0.6500"),
        expected_entry_price=Decimal("0.5400"),
        fair_value_estimate=Decimal("0.6500"),
        theoretical_edge=Decimal("0.1100"),
        cost_adjusted_edge=cost_adjusted_edge,
        confidence=confidence,
        max_executable_size=max_executable_size,
        risk_gate_passed=risk_gate_passed,
        risk_reason_codes=risk_reason_codes,
        risk_reason_summary=None if risk_gate_passed else "Risk threshold failed.",
        paper_only=paper_only,
    )


def ready_queue_item(
    *,
    analytics_history=None,
    forecast_evidence=None,
    config=None,
    **overrides,
) -> PaperManualReviewQueueItem:
    base_candidate = candidate(1)
    if overrides:
        base_candidate = replace(base_candidate, **overrides)
    queue = build_paper_manual_review_queue(
        [base_candidate],
        market_scores=(market_score("token-1"),),
        analytics_history=analytics_history or ready_history_report(),
        forecast_evidence=forecast_evidence or ready_forecast_report(),
        config=(
            config
            or PaperManualReviewConfig(
                config_version="node6-test",
                min_source_score=Decimal("80.0000"),
            )
        ),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )
    return queue.items[0]


def proposal_packet(**overrides):
    values = {
        "queue_item": ready_queue_item(),
        "side": "buy",
        "intended_order_type": "limit",
        "maximum_size": Decimal("25"),
        "exposure_after_trade": Decimal("0.1200"),
        "exit_rule": "Exit if executable price reaches fair value or thesis invalidates.",
        "reason_trade_could_be_wrong": (
            "Liquidity could disappear before exit or the resolution source could "
            "clarify against the thesis."
        ),
        "config": TradeProposalPacketConfig(config_version="proposal-v1"),
        "generated_at": datetime(2026, 9, 3, 12, tzinfo=UTC),
    }
    values.update(overrides)
    return build_trade_proposal_packet(**values)


def review_record(**overrides):
    values = {
        "proposal": proposal_packet(),
        "decision": "approved",
        "reviewer_label": "human-reviewer-1",
        "review_rationale": (
            "Approved after checking the packet evidence and exit liquidity constraints."
        ),
        "review_reason_codes": (),
        "human_attestation": DEFAULT_REVIEW_ATTESTATION,
        "config": TradeProposalReviewConfig(config_version="review-v1"),
        "recorded_at": datetime(2026, 9, 3, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return build_trade_proposal_review_record(**values)


def proposal_for_source(
    index: int,
    *,
    market_slug: str,
    strategy_type: str = "relative_value",
    risk_tags: tuple[str, ...] = ("liquidity", "event-risk"),
):
    queue_item = ready_queue_item(
        packet_id=f"packet-{index}",
        market_slug=market_slug,
        market_url=f"https://polymarket.com/event/{market_slug}",
        question=f"Will {market_slug} resolve yes?",
        strategy_type=strategy_type,
        risk_tags=risk_tags,
    )
    return proposal_packet(
        queue_item=queue_item,
        generated_at=datetime(2026, 9, 3, 12, index, tzinfo=UTC),
    )


def summary_report(records, **overrides):
    values = {
        "records": records,
        "config": TradeProposalReviewSummaryConfig(config_version="summary-v1"),
        "generated_at": datetime(2026, 9, 4, 9, tzinfo=timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return build_trade_proposal_review_summary_report(**values)


def test_build_trade_proposal_review_summary_report_counts_review_outcomes():
    approved = review_record(recorded_at=datetime(2026, 9, 3, 12, tzinfo=UTC))
    rejected = review_record(
        decision="rejected",
        review_reason_codes=("liquidity_exit_risk", "resolution_ambiguity"),
        review_rationale="Rejected after checking exit depth and resolution language.",
        recorded_at=datetime(2026, 9, 3, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
    )

    report = summary_report([rejected, approved])

    assert report.generated_at == datetime(2026, 9, 4, 13, tzinfo=UTC)
    assert report.config_version == "summary-v1"
    assert report.report_only is True
    assert report.review_record_count == 2
    assert report.unique_source_proposal_count == 1
    assert report.duplicate_source_proposal_count == 1
    assert report.first_recorded_at == datetime(2026, 9, 3, 12, tzinfo=UTC)
    assert report.last_recorded_at == datetime(2026, 9, 3, 12, 30, tzinfo=UTC)
    assert report.approved_decision_count == 1
    assert report.rejected_decision_count == 1
    assert report.rejection_ratio == Decimal("0.5000")
    assert report.status == "summary_ready"
    assert tuple(row.reason_code for row in report.reason_code_summaries) == (
        "liquidity_exit_risk",
        "resolution_ambiguity",
    )
    assert tuple((row.bucket_type, row.bucket_value) for row in report.bucket_summaries) == (
        ("market_slug", "market-1"),
        ("risk_tag", "event-risk"),
        ("risk_tag", "liquidity"),
        ("strategy_type", "relative_value"),
    )


def test_trade_proposal_review_summary_report_statuses_cover_sample_and_rejection_thresholds():
    insufficient = summary_report(
        [],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            min_review_record_count=1,
        ),
    )
    assert insufficient.review_record_count == 0
    assert insufficient.rejection_ratio is None
    assert insufficient.reason_code_summaries == ()
    assert insufficient.bucket_summaries == ()
    assert insufficient.status == "insufficient_review_sample"

    empty_ready = summary_report(
        [],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            min_review_record_count=0,
        ),
    )
    assert empty_ready.review_record_count == 0
    assert empty_ready.rejection_ratio is None
    assert empty_ready.reason_code_summaries == ()
    assert empty_ready.bucket_summaries == ()
    assert empty_ready.status == "summary_ready"

    rejected = review_record(
        decision="rejected",
        review_reason_codes=("liquidity_exit_risk",),
        review_rationale="Rejected after checking exit depth.",
    )
    high_rejection = summary_report(
        [rejected],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("0.2500"),
        ),
    )
    assert high_rejection.rejection_ratio == Decimal("1.0000")
    assert high_rejection.status == "high_rejection_ratio"

    approved = summary_report(
        [review_record()],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("0.2500"),
        ),
    )
    assert approved.rejected_decision_count == 0
    assert approved.rejection_ratio == Decimal("0.0000")
    assert approved.reason_code_summaries == ()
    assert approved.status == "summary_ready"


def test_trade_proposal_review_summary_reason_rows_are_rejected_only_and_deterministic():
    approved = review_record(
        proposal=proposal_for_source(1, market_slug="market-approved"),
        recorded_at=datetime(2026, 9, 3, 12, 5, tzinfo=UTC),
    )
    rejected_a = review_record(
        proposal=proposal_for_source(2, market_slug="market-rejected-a"),
        decision="rejected",
        review_reason_codes=("resolution_ambiguity", "liquidity_exit_risk"),
        review_rationale="Rejected after checking exit depth and resolution language.",
        recorded_at=datetime(2026, 9, 3, 12, 15, tzinfo=UTC),
    )
    rejected_b = review_record(
        proposal=proposal_for_source(3, market_slug="market-rejected-b"),
        decision="rejected",
        review_reason_codes=("model_confidence", "liquidity_exit_risk"),
        review_rationale="Rejected after checking model confidence and exit depth.",
        recorded_at=datetime(2026, 9, 3, 12, 10, tzinfo=UTC),
    )

    report = summary_report([rejected_a, approved, rejected_b])

    assert report.review_record_count == 3
    assert report.rejected_decision_count == 2
    assert tuple(
        (
            row.reason_code,
            row.rejected_decision_count,
            row.rejected_source_proposal_count,
            row.rejected_decision_ratio,
        )
        for row in report.reason_code_summaries
    ) == (
        ("liquidity_exit_risk", 2, 2, Decimal("1.0000")),
        ("model_confidence", 1, 1, Decimal("0.5000")),
        ("resolution_ambiguity", 1, 1, Decimal("0.5000")),
    )


def test_trade_proposal_review_summary_bucket_rows_count_market_strategy_and_risk_tags():
    alpha_approved = review_record(
        proposal=proposal_for_source(
            1,
            market_slug="alpha-market",
            strategy_type="relative_value",
            risk_tags=("liquidity", "event-risk"),
        ),
        recorded_at=datetime(2026, 9, 3, 12, 5, tzinfo=UTC),
    )
    alpha_rejected = review_record(
        proposal=proposal_for_source(
            2,
            market_slug="alpha-market",
            strategy_type="relative_value",
            risk_tags=("liquidity",),
        ),
        decision="rejected",
        review_reason_codes=("liquidity_exit_risk",),
        review_rationale="Rejected after checking exit depth.",
        recorded_at=datetime(2026, 9, 3, 12, 10, tzinfo=UTC),
    )
    beta_rejected = review_record(
        proposal=proposal_for_source(
            3,
            market_slug="beta-market",
            strategy_type="macro_event",
            risk_tags=("event-risk", "resolution"),
        ),
        decision="rejected",
        review_reason_codes=("resolution_ambiguity",),
        review_rationale="Rejected after checking resolution language.",
        recorded_at=datetime(2026, 9, 3, 12, 15, tzinfo=UTC),
    )

    report = summary_report([beta_rejected, alpha_approved, alpha_rejected])

    assert tuple(
        (
            row.bucket_type,
            row.bucket_value,
            row.review_record_count,
            row.unique_source_proposal_count,
            row.approved_decision_count,
            row.rejected_decision_count,
            row.rejection_ratio,
        )
        for row in report.bucket_summaries
    ) == (
        ("market_slug", "alpha-market", 2, 2, 1, 1, Decimal("0.5000")),
        ("market_slug", "beta-market", 1, 1, 0, 1, Decimal("1.0000")),
        ("risk_tag", "event-risk", 2, 2, 1, 1, Decimal("0.5000")),
        ("risk_tag", "liquidity", 2, 2, 1, 1, Decimal("0.5000")),
        ("risk_tag", "resolution", 1, 1, 0, 1, Decimal("1.0000")),
        ("strategy_type", "macro_event", 1, 1, 0, 1, Decimal("1.0000")),
        ("strategy_type", "relative_value", 2, 2, 1, 1, Decimal("0.5000")),
    )


def test_trade_proposal_review_summary_rejects_bad_inputs_and_duplicates():
    with pytest.raises(ValueError, match="records"):
        summary_report(object())
    with pytest.raises(ValueError, match="records"):
        summary_report("records")
    with pytest.raises(ValueError, match="records"):
        summary_report(b"records")
    with pytest.raises(ValueError, match="TradeProposalReviewRecord"):
        summary_report([object()])
    with pytest.raises(ValueError, match="config"):
        summary_report([], config=object())
    with pytest.raises(ValueError, match="generated_at"):
        summary_report([], generated_at="2026-09-04")

    record = review_record()
    with pytest.raises(ValueError, match="duplicate review_record_id"):
        summary_report([record, record])


def test_trade_proposal_review_summary_revalidates_mutated_records():
    non_finite_record = review_record()
    object.__setattr__(non_finite_record, "maximum_size", Decimal("NaN"))

    with pytest.raises(ValueError, match="finite|maximum_size"):
        summary_report([non_finite_record])

    bad_id_record = review_record()
    object.__setattr__(bad_id_record, "review_record_id", "bad")

    with pytest.raises(ValueError, match="review_record_id"):
        summary_report([bad_id_record])


def test_trade_proposal_review_summary_dataclasses_are_frozen_and_validate_invariants():
    config = TradeProposalReviewSummaryConfig(config_version="summary-v1")
    report = summary_report(
        [
            review_record(recorded_at=datetime(2026, 9, 3, 12, tzinfo=UTC)),
            review_record(
                decision="rejected",
                review_reason_codes=("liquidity_exit_risk", "resolution_ambiguity"),
                review_rationale=(
                    "Rejected after checking exit depth and resolution language."
                ),
            ),
        ],
        config=config,
    )
    reason_row = report.reason_code_summaries[0]
    bucket_row = report.bucket_summaries[0]

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        reason_row.reason_code = "other"
    with pytest.raises(FrozenInstanceError):
        bucket_row.bucket_value = "other"
    with pytest.raises(FrozenInstanceError):
        report.status = "other"

    with pytest.raises(ValueError, match="min_review_record_count"):
        replace(config, min_review_record_count=-1)
    with pytest.raises(ValueError, match="min_review_record_count"):
        replace(config, min_review_record_count=True)
    with pytest.raises(ValueError, match="max_rejection_ratio"):
        replace(config, max_rejection_ratio=Decimal("1.0001"))
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(config, boundary_statement="report only")

    with pytest.raises(ValueError, match="rejected_decision_count"):
        replace(reason_row, rejected_decision_count=0)
    with pytest.raises(ValueError, match="rejected_source_proposal_count"):
        replace(reason_row, rejected_source_proposal_count=0)
    with pytest.raises(ValueError, match="rejected_decision_ratio"):
        replace(reason_row, rejected_decision_ratio=Decimal("1.0001"))

    with pytest.raises(ValueError, match="bucket_type"):
        replace(bucket_row, bucket_type="reviewer_label")
    with pytest.raises(ValueError, match="review_record_count"):
        replace(bucket_row, review_record_count=0)
    with pytest.raises(ValueError, match="approved_decision_count"):
        replace(bucket_row, approved_decision_count=-1)
    with pytest.raises(ValueError, match="rejection_ratio"):
        replace(bucket_row, rejection_ratio=Decimal("0.2500"))

    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="review_record_count"):
        replace(report, review_record_count=3)
    with pytest.raises(ValueError, match="duplicate_source_proposal_count"):
        replace(report, duplicate_source_proposal_count=0)
    with pytest.raises(ValueError, match="rejection_ratio"):
        replace(report, rejection_ratio=Decimal("0.2500"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="approved")
    with pytest.raises(ValueError, match="reason_code_summaries"):
        replace(report, reason_code_summaries=tuple(reversed(report.reason_code_summaries)))
    with pytest.raises(ValueError, match="bucket_summaries"):
        replace(report, bucket_summaries=tuple(reversed(report.bucket_summaries)))
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(report, boundary_statement="summary report")


def test_trade_proposal_review_summary_boundary_statement_contract():
    config = TradeProposalReviewSummaryConfig(config_version="summary-v1")
    assert config.boundary_statement == DEFAULT_REVIEW_SUMMARY_BOUNDARY_STATEMENT

    for boundary_statement in (
        "This is a report-only proposal-review summary artifact.",
        "This is a report-only proposal-review summary artifact, not an approval workflow.",
        (
            "This is a report-only proposal-review summary artifact, not an approval "
            "workflow, trade instruction, order instruction, broker request, order "
            "request."
        ),
    ):
        with pytest.raises(ValueError, match="boundary_statement"):
            TradeProposalReviewSummaryConfig(
                config_version="summary-v1",
                boundary_statement=boundary_statement,
            )


def test_trade_proposal_review_summary_log_appends_jsonl_report(tmp_path):
    report = summary_report(
        [
            review_record(recorded_at=datetime(2026, 9, 3, 12, tzinfo=UTC)),
            review_record(
                decision="rejected",
                review_reason_codes=("liquidity_exit_risk", "resolution_ambiguity"),
                review_rationale=(
                    "Rejected after checking exit depth and resolution language."
                ),
            ),
        ],
    )
    log = TradeProposalReviewSummaryLog(path=tmp_path / "proposal-review-summaries.jsonl")

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    stored = json.loads(lines[0])
    assert stored["generated_at"] == "2026-09-04T13:00:00+00:00"
    assert stored["report_only"] is True
    assert stored["review_record_count"] == 2
    assert stored["unique_source_proposal_count"] == 1
    assert stored["duplicate_source_proposal_count"] == 1
    assert stored["rejection_ratio"] == "0.5000"
    assert stored["reason_code_summaries"] == [
        {
            "reason_code": "liquidity_exit_risk",
            "rejected_decision_count": 1,
            "rejected_decision_ratio": "1.0000",
            "rejected_source_proposal_count": 1,
        },
        {
            "reason_code": "resolution_ambiguity",
            "rejected_decision_count": 1,
            "rejected_decision_ratio": "1.0000",
            "rejected_source_proposal_count": 1,
        },
    ]
    assert stored["bucket_summaries"] == [
        {
            "approved_decision_count": 1,
            "bucket_type": "market_slug",
            "bucket_value": "market-1",
            "rejected_decision_count": 1,
            "rejection_ratio": "0.5000",
            "review_record_count": 2,
            "unique_source_proposal_count": 1,
        },
        {
            "approved_decision_count": 1,
            "bucket_type": "risk_tag",
            "bucket_value": "event-risk",
            "rejected_decision_count": 1,
            "rejection_ratio": "0.5000",
            "review_record_count": 2,
            "unique_source_proposal_count": 1,
        },
        {
            "approved_decision_count": 1,
            "bucket_type": "risk_tag",
            "bucket_value": "liquidity",
            "rejected_decision_count": 1,
            "rejection_ratio": "0.5000",
            "review_record_count": 2,
            "unique_source_proposal_count": 1,
        },
        {
            "approved_decision_count": 1,
            "bucket_type": "strategy_type",
            "bucket_value": "relative_value",
            "rejected_decision_count": 1,
            "rejection_ratio": "0.5000",
            "review_record_count": 2,
            "unique_source_proposal_count": 1,
        },
    ]


def test_trade_proposal_review_summary_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    report = summary_report([review_record()])
    log = TradeProposalReviewSummaryLog(
        path=str(tmp_path / "nested" / "proposal-review-summaries.jsonl"),
    )

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["review_record_count"] == 1
    assert json.loads(lines[1])["review_record_count"] == 1


def test_trade_proposal_review_summary_log_rejects_invalid_paths_and_inputs(tmp_path):
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewSummaryLog(path=object())
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewSummaryLog(path=" ")

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewSummaryLog(path=existing_dir)

    existing_file = tmp_path / "parent-file"
    existing_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        TradeProposalReviewSummaryLog(path=existing_file / "summary.jsonl")

    path = tmp_path / "proposal-review-summaries.jsonl"
    log = TradeProposalReviewSummaryLog(path=path)
    with pytest.raises(ValueError, match="TradeProposalReviewSummaryReport"):
        log.append(object())
    assert not path.exists()


def test_trade_proposal_review_summary_log_preserves_existing_file_when_validation_fails(
    tmp_path,
):
    report = summary_report([review_record()])
    nested_bucket_row = report.bucket_summaries[0]
    object.__setattr__(nested_bucket_row, "rejection_ratio", Decimal("NaN"))
    path = tmp_path / "proposal-review-summaries.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = TradeProposalReviewSummaryLog(path=path)

    with pytest.raises(ValueError, match="finite|rejection_ratio"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_trade_proposal_review_summary_log_rejects_non_finite_decimal_before_open(tmp_path):
    report = summary_report([review_record()])
    object.__setattr__(report, "rejection_ratio", Decimal("NaN"))
    log = TradeProposalReviewSummaryLog(path=tmp_path / "proposal-review-summaries.jsonl")

    with pytest.raises(ValueError, match="finite|rejection_ratio"):
        log.append(report)

    assert not log.path.exists()

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
    TradeProposalReviewLog,
    build_trade_proposal_review_record,
)
from polymarket_alpha_lab.research_public_payload_safety_audit import (
    audit_research_public_payload,
)


DEFAULT_REVIEW_ATTESTATION = (
    "I reviewed this proposal packet and understand this record is not a "
    "trade instruction, order instruction, broker request, order request, "
    "account action, account authentication, private-key handling, wallet "
    "signature, live-execution signal, manual execution import, credential "
    "request, or automatic order-placement authorization."
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


def test_build_trade_proposal_review_record_records_explicit_human_decision():
    packet = proposal_packet()

    record = review_record(proposal=packet)

    assert record.decision == "approved"
    assert record.record_only is True
    assert record.explicit_human_decision is True
    assert record.recorded_at == datetime(2026, 9, 3, 12, 30, tzinfo=UTC)
    assert record.source_proposal_packet_id == packet.proposal_packet_id
    assert record.source_proposal_generated_at == packet.generated_at
    assert record.source_proposal_config_version == packet.proposal_config_version
    assert record.source_proposal_boundary_statement == packet.boundary_statement
    assert record.source_queue_boundary_statement == packet.source_boundary_statement
    assert record.source_proposal_only is True
    assert record.source_human_approval_required is True
    assert record.source_queue_item_id == packet.source_queue_item_id
    assert record.source_queue_rank == packet.source_queue_rank
    assert record.source_manual_review_status == "paper_review_ready"
    assert record.source_packet_id == packet.source_packet_id
    assert record.source_paper_only is True
    assert record.condition_id == packet.condition_id
    assert record.token_id == packet.token_id
    assert record.market_slug == packet.market_slug
    assert record.market_url == packet.market_url
    assert record.question == packet.question
    assert record.outcome_name == packet.outcome_name
    assert record.strategy_type == packet.strategy_type
    assert record.side == packet.side
    assert record.intended_order_type == packet.intended_order_type
    assert record.executable_price_assumption == packet.executable_price_assumption
    assert record.maximum_size == packet.maximum_size
    assert record.source_max_executable_size == packet.source_max_executable_size
    assert record.cost_adjusted_edge == packet.cost_adjusted_edge
    assert record.theoretical_edge == packet.theoretical_edge
    assert record.fair_value_estimate == packet.fair_value_estimate
    assert record.model_probability == packet.model_probability
    assert record.confidence == packet.confidence
    assert record.source_score == packet.source_score
    assert record.market_score_total == packet.market_score_total
    assert record.exposure_after_trade == packet.exposure_after_trade
    assert record.exit_rule == packet.exit_rule
    assert record.thesis == packet.thesis
    assert record.invalidating_conditions == packet.invalidating_conditions
    assert record.rule_text_hash == packet.rule_text_hash
    assert record.resolution_source == packet.resolution_source
    assert record.risk_tags == packet.risk_tags
    assert record.reason_trade_could_be_wrong == packet.reason_trade_could_be_wrong
    assert record.readiness_summary == packet.readiness_summary
    assert record.risk_summary == packet.risk_summary
    assert record.evidence_summary == packet.evidence_summary
    assert record.why_in_queue == packet.why_in_queue
    assert record.primary_reason_code == packet.primary_reason_code
    assert record.supporting_reason_codes == packet.supporting_reason_codes
    assert record.review_focus == packet.review_focus
    assert record.evidence_scope == packet.evidence_scope
    assert record.history_status == packet.history_status
    assert record.forecast_status == packet.forecast_status
    assert record.history_gate_pass_count == packet.history_gate_pass_count
    assert record.forecast_gate_pass_count == packet.forecast_gate_pass_count
    assert record.history_gate_fail_count == packet.history_gate_fail_count
    assert record.forecast_gate_fail_count == packet.forecast_gate_fail_count
    assert record.risk_gate_passed == packet.risk_gate_passed
    assert record.hard_block_count == packet.hard_block_count
    assert record.blocking_reason_codes == packet.blocking_reason_codes
    assert record.review_reason_codes == ()
    assert "not an approval workflow" in record.boundary_statement
    assert "automatic order-placement authorization" in record.boundary_statement


def test_trade_proposal_review_record_supports_rejected_decision():
    record = review_record(
        decision="rejected",
        review_reason_codes=("liquidity_exit_risk", "resolution_ambiguity"),
        review_rationale="Rejected after checking exit depth and resolution language.",
    )

    assert record.decision == "rejected"
    assert record.review_reason_codes == (
        "liquidity_exit_risk",
        "resolution_ambiguity",
    )


def test_trade_proposal_review_record_id_and_fingerprint_are_deterministic():
    record = review_record()
    same_record = review_record()
    same_instant_record = review_record(
        recorded_at=datetime(2026, 9, 3, 13, 30, tzinfo=timezone(timedelta(hours=1))),
    )

    assert record.review_record_id.startswith("review-")
    assert len(record.review_record_id) == len("review-") + 24
    assert same_record.review_record_id == record.review_record_id
    assert same_record.source_proposal_fingerprint == record.source_proposal_fingerprint
    assert same_instant_record.review_record_id == record.review_record_id
    assert same_instant_record.source_proposal_fingerprint == (
        record.source_proposal_fingerprint
    )

    review_variants = (
        review_record(config=TradeProposalReviewConfig(config_version="review-v2")),
        review_record(recorded_at=datetime(2026, 9, 3, 12, 31, tzinfo=UTC)),
        review_record(decision="rejected", review_reason_codes=("liquidity_exit_risk",)),
        review_record(reviewer_label="human-reviewer-2"),
        review_record(review_rationale="Approved after a separate human review pass."),
    )
    proposal_variants = (
        review_record(
            proposal=proposal_packet(
                generated_at=datetime(2026, 9, 3, 12, 1, tzinfo=UTC),
            )
        ),
        review_record(proposal=proposal_packet(maximum_size=Decimal("20"))),
    )

    assert {variant.review_record_id for variant in review_variants}.isdisjoint(
        {record.review_record_id},
    )
    assert {variant.source_proposal_fingerprint for variant in review_variants} == {
        record.source_proposal_fingerprint,
    }
    assert {variant.review_record_id for variant in proposal_variants}.isdisjoint(
        {record.review_record_id},
    )
    assert {
        variant.source_proposal_fingerprint for variant in proposal_variants
    }.isdisjoint({record.source_proposal_fingerprint})


@pytest.mark.parametrize(
    "field_name,bad_value",
    (
        ("decision", "hold"),
        ("reviewer_label", " "),
        ("review_rationale", " "),
        ("recorded_at", "2026-09-03"),
    ),
)
def test_trade_proposal_review_record_rejects_invalid_public_inputs(
    field_name,
    bad_value,
):
    with pytest.raises(ValueError, match=field_name):
        review_record(**{field_name: bad_value})


def test_trade_proposal_review_record_rejects_invalid_config_and_source_type():
    with pytest.raises(ValueError, match="proposal"):
        review_record(proposal=object())
    with pytest.raises(ValueError, match="config"):
        review_record(config=object())
    with pytest.raises(ValueError, match="allowed_decisions"):
        TradeProposalReviewConfig(config_version="review-v1", allowed_decisions=())
    with pytest.raises(ValueError, match="allowed_decisions"):
        TradeProposalReviewConfig(
            config_version="review-v1",
            allowed_decisions=("approved",),
        )
    with pytest.raises(ValueError, match="human_attestation"):
        review_record(human_attestation="I approve this trade.")


def test_trade_proposal_review_record_enforces_decision_reason_code_rules():
    with pytest.raises(ValueError, match="review_reason_codes"):
        review_record(review_reason_codes=("unexpected_reason",))
    with pytest.raises(ValueError, match="review_reason_codes"):
        review_record(decision="rejected", review_reason_codes=())
    with pytest.raises(ValueError, match="review_reason_codes"):
        review_record(
            decision="rejected",
            review_reason_codes=("liquidity_exit_risk", " "),
        )


@pytest.mark.parametrize(
    "field_name,bad_value,match",
    (
        ("proposal_only", False, "proposal_only"),
        ("human_approval_required", False, "human_approval_required"),
        ("source_paper_only", False, "source_paper_only"),
        ("source_manual_review_status", "blocked_by_risk", "paper_review_ready"),
        ("risk_gate_passed", False, "risk_gate_passed"),
        ("hard_block_count", 1, "hard_block_count"),
        ("blocking_reason_codes", ("risk_gate:drawdown",), "blocking_reason_codes"),
        ("history_status", "blocked_by_quality", "history_status"),
        ("forecast_status", "blocked_by_quality", "forecast_status"),
        ("history_gate_fail_count", 1, "history_gate_fail_count"),
        ("forecast_gate_fail_count", 1, "forecast_gate_fail_count"),
        ("source_boundary_statement", " ", "source_boundary_statement"),
    ),
)
def test_trade_proposal_review_record_rejects_mutated_source_proposals(
    field_name,
    bad_value,
    match,
):
    packet = proposal_packet()
    object.__setattr__(packet, field_name, bad_value)

    with pytest.raises(ValueError, match=match):
        review_record(proposal=packet)


def test_trade_proposal_review_dataclasses_are_frozen_and_validate_invariants():
    config = TradeProposalReviewConfig(config_version="review-v1")
    record = review_record(config=config)

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        record.decision = "rejected"
    with pytest.raises(ValueError, match="review_record_id"):
        replace(record, review_record_id="bad")
    with pytest.raises(ValueError, match="source_proposal_fingerprint"):
        replace(record, source_proposal_fingerprint="bad")
    with pytest.raises(ValueError, match="record_only"):
        replace(record, record_only=False)
    with pytest.raises(ValueError, match="explicit_human_decision"):
        replace(record, explicit_human_decision=False)
    with pytest.raises(ValueError, match="source_proposal_only"):
        replace(record, source_proposal_only=False)
    with pytest.raises(ValueError, match="source_human_approval_required"):
        replace(record, source_human_approval_required=False)
    with pytest.raises(ValueError, match="review_reason_codes"):
        replace(record, review_reason_codes=("unexpected_reason",))
    with pytest.raises(ValueError, match="source_queue_item_id"):
        replace(record, source_queue_item_id="condition-1:token-1:other-packet")
    with pytest.raises(ValueError, match="source_queue_rank"):
        replace(record, source_queue_rank=0)
    with pytest.raises(ValueError, match="maximum_size"):
        replace(record, maximum_size=Decimal("101"))
    with pytest.raises(ValueError, match="history_gate_fail_count"):
        replace(record, history_gate_fail_count=1)
    with pytest.raises(ValueError, match="forecast_gate_fail_count"):
        replace(record, forecast_gate_fail_count=True)
    with pytest.raises(ValueError, match="source_proposal_boundary_statement"):
        replace(record, source_proposal_boundary_statement="proposal only")
    with pytest.raises(ValueError, match="source_queue_boundary_statement"):
        replace(record, source_queue_boundary_statement=" ")


def test_trade_proposal_review_boundary_statement_contract():
    config = TradeProposalReviewConfig(config_version="review-v1")
    assert config.boundary_statement == (
        "This is a record-only human-review decision artifact, not an approval "
        "workflow, trade instruction, order instruction, broker request, order "
        "request, account action, account authentication, private-key handling, "
        "wallet signature, live-execution signal, credential workflow, manual "
        "execution import, or automatic order-placement authorization."
    )

    for boundary_statement in (
        "record-only human-review decision",
        "This is a record-only human-review decision artifact.",
        "This is a record-only artifact, not an approval workflow, trade instruction.",
    ):
        with pytest.raises(ValueError, match="boundary_statement"):
            TradeProposalReviewConfig(
                config_version="review-v1",
                boundary_statement=boundary_statement,
            )


def test_trade_proposal_review_record_timestamps_normalize_to_utc():
    record = review_record(
        recorded_at=datetime(2026, 9, 3, 20, 30, tzinfo=timezone(timedelta(hours=8))),
    )

    assert record.recorded_at == datetime(2026, 9, 3, 12, 30, tzinfo=UTC)


def test_trade_proposal_review_log_appends_jsonl_record(tmp_path):
    record = review_record()
    log = TradeProposalReviewLog(path=tmp_path / "proposal-reviews.jsonl")

    log.record(record)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"blocking_reason_codes"')
    stored = json.loads(lines[0])
    assert stored["review_record_id"] == record.review_record_id
    assert stored["record_only"] is True
    assert stored["explicit_human_decision"] is True
    assert stored["recorded_at"] == "2026-09-03T12:30:00+00:00"
    assert stored["review_config_version"] == "review-v1"
    assert stored["source_proposal_packet_id"] == record.source_proposal_packet_id
    assert stored["source_proposal_boundary_statement"] == (
        record.source_proposal_boundary_statement
    )
    assert stored["source_queue_boundary_statement"] == (
        record.source_queue_boundary_statement
    )
    assert stored["maximum_size"] == "25"
    assert stored["source_max_executable_size"] == "100"
    assert stored["risk_tags"] == ["liquidity", "event-risk"]
    assert stored["review_reason_codes"] == []


def test_trade_proposal_review_record_public_safe_payload_excludes_trade_proposal_fields():
    record = review_record()

    payload = record.public_safe_payload()

    forbidden_fields = {
        "condition_id",
        "token_id",
        "market_slug",
        "question",
        "side",
        "intended_order_type",
        "maximum_size",
        "source_max_executable_size",
        "order",
        "trade",
        "size",
    }
    assert forbidden_fields.isdisjoint(payload)
    assert payload == {
        "review_record_id": record.review_record_id,
        "recorded_at": "2026-09-03T12:30:00+00:00",
        "review_config_version": "review-v1",
        "record_only": True,
        "explicit_human_decision": True,
        "decision": "approved",
        "review_reason_codes": [],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "public_export_scope": "public_safe_review_attestation",
    }
    audit = audit_research_public_payload(
        payload,
        generated_at=datetime(2026, 9, 3, 13, tzinfo=UTC),
        report_name="trade_proposal_review_public_safe_payload",
    )
    assert audit.audit_status == "pass"


def test_trade_proposal_review_log_marks_file_append_as_ephemeral_local_only(tmp_path):
    log = TradeProposalReviewLog(path=tmp_path / "proposal-reviews.jsonl")

    assert log.storage_scope == "ephemeral_local_review_log"
    assert log.durable_memory is False
    assert log.public_output is False
    assert "ephemeral/local review log" in TradeProposalReviewLog.__doc__
    with pytest.raises(ValueError, match="durable_memory"):
        TradeProposalReviewLog(
            path=tmp_path / "durable-reviews.jsonl",
            durable_memory=True,
        )


def test_trade_proposal_review_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    record = review_record()
    log = TradeProposalReviewLog(path=str(tmp_path / "nested" / "reviews.jsonl"))

    log.record(record)
    log.record(record)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["review_record_id"] == record.review_record_id
    assert json.loads(lines[1])["review_record_id"] == record.review_record_id


def test_trade_proposal_review_log_rejects_invalid_paths_and_inputs(tmp_path):
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewLog(path=object())
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewLog(path=" ")

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewLog(path=existing_dir)

    existing_file = tmp_path / "parent-file"
    existing_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        TradeProposalReviewLog(path=existing_file / "reviews.jsonl")

    path = tmp_path / "proposal-reviews.jsonl"
    log = TradeProposalReviewLog(path=path)
    with pytest.raises(ValueError, match="TradeProposalReviewRecord"):
        log.record(object())
    assert not path.exists()


def test_trade_proposal_review_log_preserves_existing_file_when_validation_fails(
    tmp_path,
):
    record = review_record()
    object.__setattr__(record, "maximum_size", Decimal("NaN"))
    path = tmp_path / "proposal-reviews.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = TradeProposalReviewLog(path=path)

    with pytest.raises(ValueError, match="finite|maximum_size"):
        log.record(record)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_trade_proposal_review_log_rejects_non_finite_decimal_before_open(tmp_path):
    record = review_record()
    object.__setattr__(record, "source_score", Decimal("NaN"))
    log = TradeProposalReviewLog(path=tmp_path / "proposal-reviews.jsonl")

    with pytest.raises(ValueError, match="finite|source_score"):
        log.record(record)

    assert not log.path.exists()

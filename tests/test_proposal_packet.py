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
    STATUS_RANK,
    build_paper_manual_review_queue,
)
from polymarket_alpha_lab.proposal_packet import (
    TradeProposalPacketConfig,
    TradeProposalPacketLog,
    build_trade_proposal_packet,
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


def test_build_trade_proposal_packet_records_required_human_review_fields():
    item = ready_queue_item()

    packet = proposal_packet(queue_item=item)

    assert packet.source_queue_item_id == item.queue_item_id
    assert packet.source_queue_rank == item.rank
    assert packet.source_manual_review_status == "paper_review_ready"
    assert packet.source_packet_id == item.packet_id
    assert packet.source_boundary_statement == item.boundary_statement
    assert packet.source_paper_only is True
    assert packet.condition_id == item.condition_id
    assert packet.token_id == item.token_id
    assert packet.market_slug == item.market_slug
    assert packet.market_url == item.market_url
    assert packet.question == item.question
    assert packet.outcome_name == item.outcome_name
    assert packet.strategy_type == item.strategy_type
    assert packet.side == "buy"
    assert packet.intended_order_type == "limit"
    assert packet.executable_price_assumption == item.expected_entry_price
    assert packet.maximum_size == Decimal("25")
    assert packet.source_max_executable_size == item.max_executable_size
    assert packet.cost_adjusted_edge == item.cost_adjusted_edge
    assert packet.theoretical_edge == item.theoretical_edge
    assert packet.fair_value_estimate == item.fair_value_estimate
    assert packet.model_probability == item.model_probability
    assert packet.confidence == item.confidence
    assert packet.source_score == item.source_score
    assert packet.market_score_total == item.market_score_total
    assert packet.thesis == item.thesis
    assert packet.invalidating_conditions == item.invalidating_conditions
    assert packet.rule_text_hash == item.rule_text_hash
    assert packet.resolution_source == item.resolution_source
    assert packet.risk_tags == item.risk_tags
    assert packet.exposure_after_trade == Decimal("0.1200")
    assert packet.exit_rule.startswith("Exit if executable price")
    assert "Liquidity could disappear" in packet.reason_trade_could_be_wrong
    assert packet.readiness_summary == item.readiness_summary
    assert packet.risk_summary == item.risk_summary
    assert packet.evidence_summary == item.evidence_summary
    assert packet.why_in_queue == item.why_in_queue
    assert packet.primary_reason_code == item.primary_reason_code
    assert packet.supporting_reason_codes == item.supporting_reason_codes
    assert packet.blocking_reason_codes == ()
    assert packet.review_focus == item.review_focus
    assert packet.history_status == item.history_status
    assert packet.forecast_status == item.forecast_status
    assert packet.history_gate_pass_count == item.history_gate_pass_count
    assert packet.forecast_gate_pass_count == item.forecast_gate_pass_count
    assert packet.history_gate_fail_count == item.history_gate_fail_count
    assert packet.forecast_gate_fail_count == item.forecast_gate_fail_count
    assert packet.evidence_scope == item.evidence_scope
    assert packet.risk_gate_passed is True
    assert packet.hard_block_count == 0
    assert packet.proposal_only is True
    assert packet.human_approval_required is True
    assert "not an approval workflow" in packet.boundary_statement
    assert "explicit human approval" in packet.boundary_statement


def test_trade_proposal_packet_rejects_non_ready_manual_review_items():
    cases = (
        "insufficient_evidence",
        "blocked_by_risk",
        "blocked_by_quality",
        "incomplete_data",
    )

    for status in cases:
        with pytest.raises(ValueError, match="paper_review_ready|queue_item"):
            proposal_packet(
                queue_item=replace(
                    ready_queue_item(),
                    status=status,
                    status_rank=STATUS_RANK[status],
                )
            )


@pytest.mark.parametrize(
    "field_name,bad_value",
    (
        ("history_status", "blocked_by_risk"),
        ("forecast_status", "blocked_by_quality"),
        ("history_gate_fail_count", 1),
        ("forecast_gate_fail_count", 1),
    ),
)
def test_trade_proposal_packet_rejects_inconsistent_ready_queue_item_details(
    field_name,
    bad_value,
):
    with pytest.raises(ValueError, match=field_name):
        proposal_packet(queue_item=replace(ready_queue_item(), **{field_name: bad_value}))


@pytest.mark.parametrize(
    "field_name,bad_value,match",
    (
        ("paper_only", False, "paper_only|paper-only|queue_item"),
        ("risk_gate_passed", False, "risk gate"),
        ("hard_block_count", 1, "hard blocks"),
        ("blocking_reason_codes", ("risk_gate:drawdown",), "blocking reason codes"),
    ),
)
def test_trade_proposal_packet_rejects_source_queue_safety_gate_failures(
    field_name,
    bad_value,
    match,
):
    item = ready_queue_item()
    if field_name == "paper_only":
        object.__setattr__(item, field_name, bad_value)
    else:
        item = replace(item, **{field_name: bad_value})

    with pytest.raises(ValueError, match=match):
        proposal_packet(queue_item=item)


@pytest.mark.parametrize(
    "field_name,bad_value",
    (
        ("side", "hold"),
        ("intended_order_type", " "),
        ("maximum_size", Decimal("0")),
        ("maximum_size", Decimal("NaN")),
        ("maximum_size", Decimal("101")),
        ("exposure_after_trade", Decimal("-0.0001")),
        ("exposure_after_trade", Decimal("NaN")),
        ("exit_rule", " "),
        ("reason_trade_could_be_wrong", " "),
        ("generated_at", "2026-09-03"),
    ),
)
def test_trade_proposal_packet_rejects_invalid_public_inputs_and_values(
    field_name,
    bad_value,
):
    with pytest.raises(ValueError, match=field_name):
        proposal_packet(**{field_name: bad_value})


def test_trade_proposal_packet_rejects_invalid_config_and_source_type():
    with pytest.raises(ValueError, match="queue_item"):
        proposal_packet(queue_item=object())
    with pytest.raises(ValueError, match="config"):
        proposal_packet(config=object())
    with pytest.raises(ValueError, match="allowed_sides"):
        TradeProposalPacketConfig(config_version="proposal-v1", allowed_sides=())
    with pytest.raises(ValueError, match="allowed_sides"):
        TradeProposalPacketConfig(config_version="proposal-v1", allowed_sides=("hold",))
    with pytest.raises(ValueError, match="allowed_intended_order_types"):
        TradeProposalPacketConfig(
            config_version="proposal-v1",
            allowed_intended_order_types=(),
        )
    with pytest.raises(ValueError, match="max_proposal_size"):
        TradeProposalPacketConfig(
            config_version="proposal-v1",
            max_proposal_size=Decimal("0"),
        )


@pytest.mark.parametrize(
    "field_name,bad_value",
    (
        ("market_url", ""),
        ("thesis", " "),
        ("invalidating_conditions", " "),
        ("rule_text_hash", " "),
        ("resolution_source", " "),
        ("risk_tags", ()),
        ("expected_entry_price", None),
        ("expected_entry_price", Decimal("0")),
        ("expected_entry_price", Decimal("1")),
        ("expected_entry_price", Decimal("NaN")),
        ("max_executable_size", None),
        ("max_executable_size", Decimal("0")),
        ("cost_adjusted_edge", None),
        ("cost_adjusted_edge", Decimal("-0.0001")),
    ),
)
def test_trade_proposal_packet_rejects_missing_gate_6_packet_fields(
    field_name,
    bad_value,
):
    with pytest.raises(ValueError, match=field_name):
        proposal_packet(queue_item=replace(ready_queue_item(), **{field_name: bad_value}))


def test_trade_proposal_packet_timestamps_normalize_to_utc():
    packet = proposal_packet(
        generated_at=datetime(2026, 9, 3, 8, 31, tzinfo=timezone(timedelta(hours=8))),
    )

    assert packet.generated_at == datetime(2026, 9, 3, 0, 31, tzinfo=UTC)


def test_trade_proposal_packet_id_is_deterministic_and_input_sensitive():
    packet = proposal_packet()
    same_packet = proposal_packet()
    same_instant_packet = proposal_packet(
        generated_at=datetime(2026, 9, 3, 20, tzinfo=timezone(timedelta(hours=8))),
    )

    assert packet.proposal_packet_id == "proposal-1ee22d35e07c9d7bf96cc486"
    assert same_packet.proposal_packet_id == packet.proposal_packet_id
    assert same_instant_packet.proposal_packet_id == packet.proposal_packet_id

    variants = (
        proposal_packet(config=TradeProposalPacketConfig(config_version="proposal-v2")),
        proposal_packet(generated_at=datetime(2026, 9, 3, 12, 1, tzinfo=UTC)),
        proposal_packet(queue_item=ready_queue_item(packet_id="packet-other")),
        proposal_packet(side="sell"),
        proposal_packet(intended_order_type="marketable_limit"),
        proposal_packet(maximum_size=Decimal("26")),
        proposal_packet(exposure_after_trade=Decimal("0.1300")),
    )

    assert {variant.proposal_packet_id for variant in variants}.isdisjoint(
        {packet.proposal_packet_id},
    )
    assert len({variant.proposal_packet_id for variant in variants}) == len(variants)


def test_trade_proposal_packet_dataclasses_are_frozen_and_validate_invariants():
    config = TradeProposalPacketConfig(config_version="proposal-v1")
    packet = proposal_packet(config=config)

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        packet.maximum_size = Decimal("1")
    with pytest.raises(ValueError, match="proposal_packet_id"):
        replace(packet, proposal_packet_id="bad")
    with pytest.raises(ValueError, match="human_approval_required"):
        replace(packet, human_approval_required=False)
    with pytest.raises(ValueError, match="proposal_only"):
        replace(packet, proposal_only=False)
    with pytest.raises(ValueError, match="source_queue_item_id"):
        replace(packet, source_queue_item_id="condition-1:token-1:other-packet")
    with pytest.raises(ValueError, match="blocking_reason_codes"):
        replace(packet, blocking_reason_codes=("risk_gate:drawdown",))
    with pytest.raises(ValueError, match="history_gate_pass_count"):
        replace(packet, history_gate_pass_count=-1)
    with pytest.raises(ValueError, match="forecast_gate_pass_count"):
        replace(packet, forecast_gate_pass_count="bad")
    with pytest.raises(ValueError, match="history_gate_fail_count"):
        replace(packet, history_gate_fail_count=True)
    with pytest.raises(ValueError, match="forecast_gate_fail_count"):
        replace(packet, forecast_gate_fail_count=-1)
    with pytest.raises(ValueError, match="hard_block_count"):
        replace(packet, hard_block_count=False)


def test_trade_proposal_packet_enforces_configured_builder_limits():
    with pytest.raises(ValueError, match="side"):
        proposal_packet(
            side="sell",
            config=TradeProposalPacketConfig(
                config_version="proposal-v1",
                allowed_sides=("buy",),
            ),
        )
    with pytest.raises(ValueError, match="intended_order_type"):
        proposal_packet(
            intended_order_type="marketable_limit",
            config=TradeProposalPacketConfig(
                config_version="proposal-v1",
                allowed_intended_order_types=("limit",),
            ),
        )
    with pytest.raises(ValueError, match="cost_adjusted_edge"):
        proposal_packet(
            config=TradeProposalPacketConfig(
                config_version="proposal-v1",
                min_cost_adjusted_edge=Decimal("0.0600"),
            ),
        )
    with pytest.raises(ValueError, match="maximum_size"):
        proposal_packet(
            maximum_size=Decimal("25"),
            config=TradeProposalPacketConfig(
                config_version="proposal-v1",
                max_proposal_size=Decimal("24"),
            ),
        )
    with pytest.raises(ValueError, match="exposure_after_trade"):
        proposal_packet(
            exposure_after_trade=Decimal("0.1200"),
            config=TradeProposalPacketConfig(
                config_version="proposal-v1",
                max_exposure_after_trade=Decimal("0.1100"),
            ),
        )


def test_trade_proposal_packet_boundary_statement_contract():
    config = TradeProposalPacketConfig(config_version="proposal-v1")
    assert config.boundary_statement == (
        "This is a proposal-only human-review packet, not an approval workflow, "
        "trade instruction, order instruction, broker request, strategy-promotion "
        "signal, or live-execution signal; no order may leave the system without "
        "explicit human approval."
    )

    for boundary_statement in (
        "proposal-only human-review packet, not an approval workflow, trade instruction, order instruction.",
        "This is a human-review packet, not an approval workflow, trade instruction, order instruction, broker request, strategy-promotion signal, or live-execution signal; no order may leave the system without explicit human approval.",
        "This is a proposal-only human-review packet.",
    ):
        with pytest.raises(ValueError, match="boundary_statement"):
            TradeProposalPacketConfig(
                config_version="proposal-v1",
                boundary_statement=boundary_statement,
            )


def test_trade_proposal_packet_log_appends_jsonl_packet(tmp_path):
    packet = proposal_packet()
    log = TradeProposalPacketLog(path=tmp_path / "proposal-packets.jsonl")

    log.append(packet)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"blocking_reason_codes"')
    stored = json.loads(lines[0])
    assert stored["proposal_only"] is True
    assert stored["human_approval_required"] is True
    assert stored["generated_at"] == "2026-09-03T12:00:00+00:00"
    assert stored["proposal_config_version"] == "proposal-v1"
    assert stored["maximum_size"] == "25"
    assert stored["source_max_executable_size"] == "100"
    assert stored["cost_adjusted_edge"] == "0.0500"
    assert stored["exposure_after_trade"] == "0.1200"
    assert stored["risk_tags"] == ["liquidity", "event-risk"]
    assert stored["boundary_statement"] == packet.boundary_statement


def test_trade_proposal_packet_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    packet = proposal_packet()
    log = TradeProposalPacketLog(path=str(tmp_path / "nested" / "proposal-packets.jsonl"))

    log.append(packet)
    log.append(packet)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["proposal_packet_id"] == packet.proposal_packet_id
    assert json.loads(lines[1])["proposal_packet_id"] == packet.proposal_packet_id


def test_trade_proposal_packet_log_rejects_invalid_paths_and_inputs(tmp_path):
    with pytest.raises(ValueError, match="path"):
        TradeProposalPacketLog(path=object())
    with pytest.raises(ValueError, match="path"):
        TradeProposalPacketLog(path=" ")

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    with pytest.raises(ValueError, match="path"):
        TradeProposalPacketLog(path=existing_dir)

    existing_file = tmp_path / "parent-file"
    existing_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        TradeProposalPacketLog(path=existing_file / "proposal-packets.jsonl")

    path = tmp_path / "proposal-packets.jsonl"
    log = TradeProposalPacketLog(path=path)
    with pytest.raises(ValueError, match="TradeProposalPacket"):
        log.append(object())
    assert not path.exists()


def test_trade_proposal_packet_log_preserves_existing_file_when_validation_fails(
    tmp_path,
):
    packet = proposal_packet()
    object.__setattr__(packet, "maximum_size", Decimal("NaN"))
    path = tmp_path / "proposal-packets.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = TradeProposalPacketLog(path=path)

    with pytest.raises(ValueError, match="finite|JSON|serializable|maximum_size"):
        log.append(packet)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_trade_proposal_packet_log_rejects_non_finite_decimal_before_open(tmp_path):
    packet = proposal_packet()
    object.__setattr__(packet, "cost_adjusted_edge", Decimal("NaN"))
    log = TradeProposalPacketLog(path=tmp_path / "proposal-packets.jsonl")

    with pytest.raises(ValueError, match="finite|cost_adjusted_edge"):
        log.append(packet)

    assert not log.path.exists()

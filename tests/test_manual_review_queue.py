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
    PaperManualReviewLog,
    build_paper_manual_review_queue,
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


def test_build_paper_manual_review_queue_summarizes_and_sorts_items():
    queue = build_paper_manual_review_queue(
        [
            candidate(1, score=Decimal("90.0000"), cost_adjusted_edge=Decimal("0.0100")),
            candidate(2, score=Decimal("95.0000"), cost_adjusted_edge=Decimal("0.0200")),
            candidate(3, score=Decimal("95.0000"), cost_adjusted_edge=Decimal("0.0500")),
        ],
        market_scores=(
            market_score("token-1"),
            market_score("token-2", total_bias=Decimal("5")),
            market_score("token-3", total_bias=Decimal("10")),
        ),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(
            config_version="node6-test",
            min_source_score=Decimal("80.0000"),
        ),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    assert queue.generated_at == datetime(2026, 9, 3, tzinfo=UTC)
    assert queue.config_version == "node6-test"
    assert queue.candidate_count == 3
    assert queue.item_count == 3
    assert queue.ready_item_count == 3
    assert queue.status == "paper_review_ready"
    assert queue.first_queued_at == datetime(2026, 9, 2, 0, 1, tzinfo=UTC)
    assert queue.last_queued_at == datetime(2026, 9, 2, 0, 3, tzinfo=UTC)
    assert queue.unique_market_count == 3
    assert queue.unique_strategy_count == 1
    assert queue.unique_risk_tag_count == 2
    assert [item.packet_id for item in queue.items] == ["packet-3", "packet-2", "packet-1"]
    assert [item.rank for item in queue.items] == [1, 2, 3]
    assert queue.top_queue_item_id == "condition-1:token-3:packet-3"

    top_item = queue.items[0]
    assert top_item.status == "paper_review_ready"
    assert top_item.status_rank == 0
    assert top_item.hard_block_count == 0
    assert top_item.evidence_pass_count == 10
    assert top_item.source_score == Decimal("95.0000")
    assert top_item.market_score_total == market_score("token-3", Decimal("10")).total
    assert top_item.history_gate_pass_count == 5
    assert top_item.forecast_gate_pass_count == 5
    assert top_item.history_gate_fail_count == 0
    assert top_item.forecast_gate_fail_count == 0
    assert top_item.primary_reason_code == "paper_evidence_ready"
    assert top_item.supporting_reason_codes == (
        "high_source_score",
        "risk_gate_passed",
        "history_ready",
        "forecast_ready",
        "sample_size_passed",
        "edge_quality_passed",
    )
    assert top_item.blocking_reason_codes == ()
    assert top_item.review_focus == (
        "resolution_rule_ambiguity",
        "liquidity_exit_risk",
        "probability_quality",
        "edge_quality",
        "residual_exposure",
        "theme_concentration",
    )
    assert top_item.evidence_scope == "portfolio_and_forecast_aggregate"
    assert "paper-only manual-review artifact" in top_item.boundary_statement
    assert "trade instruction" in top_item.boundary_statement
    assert top_item.paper_only is True
    assert queue.paper_only is True


def test_manual_review_queue_status_precedence_and_reason_codes():
    cases = (
        (
            replace(
                candidate(
                    1,
                    score=Decimal("10.0000"),
                    risk_gate_passed=False,
                    risk_reason_codes=("drawdown",),
                ),
                market_url="",
            ),
            ready_history_report(),
            replace(ready_forecast_report(), status="blocked_by_quality"),
            "incomplete_data",
            "incomplete_data",
        ),
        (
            candidate(
                2,
                score=Decimal("10.0000"),
                risk_gate_passed=False,
                risk_reason_codes=("drawdown",),
            ),
            ready_history_report(),
            replace(ready_forecast_report(), status="blocked_by_quality"),
            "blocked_by_risk",
            "blocked_risk_drawdown",
        ),
        (
            candidate(3, score=Decimal("10.0000")),
            ready_history_report(),
            replace(ready_forecast_report(), status="blocked_by_quality"),
            "blocked_by_quality",
            "blocked_forecast_quality",
        ),
        (
            candidate(4, score=Decimal("10.0000")),
            replace(ready_history_report(), status="insufficient_evidence"),
            ready_forecast_report(),
            "insufficient_evidence",
            "needs_more_sample",
        ),
        (
            candidate(5, score=Decimal("10.0000")),
            ready_history_report(),
            ready_forecast_report(),
            "insufficient_evidence",
            "below_source_score",
        ),
    )

    for candidate_item, history_report, forecast_report, status, reason_code in cases:
        queue = build_paper_manual_review_queue(
            [candidate_item],
            market_scores=(),
            analytics_history=history_report,
            forecast_evidence=forecast_report,
            config=PaperManualReviewConfig(
                config_version="node6-test",
                min_source_score=Decimal("80.0000"),
            ),
            generated_at=datetime(2026, 9, 3, tzinfo=UTC),
        )

        assert queue.items[0].status == status
        assert queue.items[0].primary_reason_code == reason_code


def test_manual_review_queue_status_counts_and_filtering_use_final_items():
    queue = build_paper_manual_review_queue(
        [
            candidate(1, score=Decimal("90.0000")),
            candidate(2, score=Decimal("10.0000")),
            candidate(
                3,
                risk_gate_passed=False,
                risk_reason_codes=("drawdown",),
            ),
            replace(candidate(4), market_url=""),
        ],
        market_scores=(),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(
            config_version="node6-test",
            min_source_score=Decimal("80.0000"),
            include_blocked_items=False,
        ),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    assert queue.candidate_count == 4
    assert [item.status for item in queue.items] == [
        "paper_review_ready",
        "insufficient_evidence",
    ]
    assert queue.item_count == 2
    assert queue.ready_item_count == 1
    assert queue.insufficient_item_count == 1
    assert queue.blocked_risk_item_count == 0
    assert queue.incomplete_item_count == 0
    assert queue.status == "paper_review_ready"
    assert [item.rank for item in queue.items] == [1, 2]

    empty_queue = build_paper_manual_review_queue(
        [
            candidate(
                5,
                risk_gate_passed=False,
                risk_reason_codes=("drawdown",),
            )
        ],
        market_scores=(),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(
            config_version="node6-test",
            include_blocked_items=False,
        ),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    assert empty_queue.candidate_count == 1
    assert empty_queue.item_count == 0
    assert empty_queue.items == ()
    assert empty_queue.first_queued_at is None
    assert empty_queue.last_queued_at is None
    assert empty_queue.top_queue_item_id is None
    assert empty_queue.status == "incomplete_data"


def test_manual_review_queue_status_honors_min_ready_items_before_other_statuses():
    queue = build_paper_manual_review_queue(
        [
            candidate(1, score=Decimal("90.0000")),
            candidate(
                2,
                risk_gate_passed=False,
                risk_reason_codes=("drawdown",),
            ),
        ],
        market_scores=(),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(
            config_version="node6-test",
            min_ready_items=2,
        ),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    assert queue.ready_item_count == 1
    assert queue.blocked_risk_item_count == 1
    assert queue.status == "blocked_by_risk"

    ready_queue = build_paper_manual_review_queue(
        [
            candidate(3, score=Decimal("90.0000")),
            candidate(4, score=Decimal("91.0000")),
            candidate(
                5,
                risk_gate_passed=False,
                risk_reason_codes=("drawdown",),
            ),
        ],
        market_scores=(),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(
            config_version="node6-test",
            min_ready_items=2,
        ),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    assert ready_queue.ready_item_count == 2
    assert ready_queue.blocked_risk_item_count == 1
    assert ready_queue.status == "paper_review_ready"


def test_manual_review_queue_sorting_prioritizes_status_before_scores():
    queue = build_paper_manual_review_queue(
        [
            replace(candidate(4, score=Decimal("100.0000")), market_url=""),
            candidate(
                3,
                score=Decimal("100.0000"),
                risk_gate_passed=False,
                risk_reason_codes=("drawdown",),
            ),
            candidate(2, score=Decimal("10.0000")),
            candidate(1, score=Decimal("80.0000")),
        ],
        market_scores=(),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(
            config_version="node6-test",
            min_source_score=Decimal("80.0000"),
        ),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    assert [item.status for item in queue.items] == [
        "paper_review_ready",
        "insufficient_evidence",
        "blocked_by_risk",
        "incomplete_data",
    ]
    assert [item.rank for item in queue.items] == [1, 2, 3, 4]


def test_manual_review_queue_sorting_tie_breakers_are_deterministic():
    older = replace(
        candidate(
            1,
            score=Decimal("90.0000"),
            cost_adjusted_edge=Decimal("0.0100"),
            confidence=Decimal("0.7000"),
            max_executable_size=Decimal("100"),
        ),
        market_slug="market-b",
        token_id="token-b",
        packet_id="packet-b",
    )
    fresher = replace(
        candidate(
            2,
            score=Decimal("90.0000"),
            cost_adjusted_edge=Decimal("0.0100"),
            confidence=Decimal("0.7000"),
            max_executable_size=Decimal("100"),
        ),
        market_slug="market-a",
        token_id="token-a",
        packet_id="packet-a",
    )

    queue = build_paper_manual_review_queue(
        [older, fresher],
        market_scores=(),
        analytics_history=replace(
            ready_history_report(),
            generated_at=datetime(2026, 8, 1, tzinfo=UTC),
        ),
        forecast_evidence=replace(
            ready_forecast_report(),
            generated_at=datetime(2026, 8, 1, tzinfo=UTC),
        ),
        config=PaperManualReviewConfig(config_version="node6-test"),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    assert [item.packet_id for item in queue.items] == ["packet-a", "packet-b"]

    lexical_queue = build_paper_manual_review_queue(
        [
            replace(fresher, queued_at=datetime(2026, 9, 2, 0, 1, tzinfo=UTC)),
            replace(older, queued_at=datetime(2026, 9, 2, 0, 1, tzinfo=UTC)),
        ],
        market_scores=(),
        analytics_history=replace(
            ready_history_report(),
            generated_at=datetime(2026, 8, 1, tzinfo=UTC),
        ),
        forecast_evidence=replace(
            ready_forecast_report(),
            generated_at=datetime(2026, 8, 1, tzinfo=UTC),
        ),
        config=PaperManualReviewConfig(config_version="node6-test"),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    assert [item.packet_id for item in lexical_queue.items] == ["packet-a", "packet-b"]


def test_manual_review_queue_market_score_join_and_duplicate_guards():
    queue = build_paper_manual_review_queue(
        [candidate(1), candidate(2)],
        market_scores=(
            market_score("token-1"),
            MarketScore(
                condition_id="condition-extra",
                token_id="token-extra",
                activity=Decimal("100"),
                liquidity=Decimal("100"),
                spread_quality=Decimal("100"),
                time_structure=Decimal("100"),
                information_structure=Decimal("100"),
                price_behavior=Decimal("100"),
                duplicate_penalty=Decimal("0"),
            ),
        ),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(config_version="node6-test"),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    by_token = {item.token_id: item for item in queue.items}
    assert by_token["token-1"].market_score_total == market_score("token-1").total
    assert by_token["token-2"].market_score_total is None

    with pytest.raises(ValueError, match="duplicate.*market score"):
        build_paper_manual_review_queue(
            [candidate(1)],
            market_scores=(market_score("token-1"), market_score("token-1")),
            analytics_history=ready_history_report(),
            forecast_evidence=ready_forecast_report(),
            config=PaperManualReviewConfig(config_version="node6-test"),
            generated_at=datetime(2026, 9, 3, tzinfo=UTC),
        )

    same_utc = replace(
        candidate(6),
        queued_at=datetime(2026, 9, 2, 8, 6, tzinfo=timezone(timedelta(hours=8))),
    )
    utc_item = replace(
        candidate(7),
        queued_at=datetime(2026, 9, 2, 0, 6, tzinfo=UTC),
        token_id=same_utc.token_id,
        packet_id=same_utc.packet_id,
    )
    with pytest.raises(ValueError, match="duplicate.*candidate"):
        build_paper_manual_review_queue(
            [same_utc, utc_item],
            market_scores=(),
            analytics_history=ready_history_report(),
            forecast_evidence=ready_forecast_report(),
            config=PaperManualReviewConfig(config_version="node6-test"),
            generated_at=datetime(2026, 9, 3, tzinfo=UTC),
        )

    duplicate_id = replace(
        candidate(8),
        condition_id="condition-1",
        token_id="token-1",
        packet_id="packet-1",
    )
    with pytest.raises(ValueError, match="duplicate.*queue_item_id"):
        build_paper_manual_review_queue(
            [candidate(1), duplicate_id],
            market_scores=(),
            analytics_history=ready_history_report(),
            forecast_evidence=ready_forecast_report(),
            config=PaperManualReviewConfig(config_version="node6-test"),
            generated_at=datetime(2026, 9, 3, tzinfo=UTC),
        )


def test_manual_review_queue_rejects_bad_public_inputs_and_values():
    valid_candidate = candidate(1)
    config = PaperManualReviewConfig(config_version="node6-test")

    with pytest.raises(ValueError, match="candidates"):
        build_paper_manual_review_queue(
            "not-candidates",
            market_scores=(),
            analytics_history=ready_history_report(),
            forecast_evidence=ready_forecast_report(),
            config=config,
            generated_at=datetime(2026, 9, 3, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="PaperManualReviewCandidate"):
        build_paper_manual_review_queue(
            [object()],
            market_scores=(),
            analytics_history=ready_history_report(),
            forecast_evidence=ready_forecast_report(),
            config=config,
            generated_at=datetime(2026, 9, 3, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="MarketScore"):
        build_paper_manual_review_queue(
            [valid_candidate],
            market_scores=(object(),),
            analytics_history=ready_history_report(),
            forecast_evidence=ready_forecast_report(),
            config=config,
            generated_at=datetime(2026, 9, 3, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="analytics_history"):
        build_paper_manual_review_queue(
            [valid_candidate],
            market_scores=(),
            analytics_history=object(),
            forecast_evidence=ready_forecast_report(),
            config=config,
            generated_at=datetime(2026, 9, 3, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_manual_review_queue(
            [valid_candidate],
            market_scores=(),
            analytics_history=ready_history_report(),
            forecast_evidence=ready_forecast_report(),
            config=object(),
            generated_at=datetime(2026, 9, 3, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_manual_review_queue(
            [valid_candidate],
            market_scores=(),
            analytics_history=ready_history_report(),
            forecast_evidence=ready_forecast_report(),
            config=config,
            generated_at=None,
        )
    with pytest.raises(ValueError, match="min_source_score"):
        PaperManualReviewConfig(
            config_version="node6-test",
            min_source_score=Decimal("-0.0001"),
        )
    with pytest.raises(ValueError, match="min_ready_items"):
        PaperManualReviewConfig(config_version="node6-test", min_ready_items=True)
    with pytest.raises(ValueError, match="source_score"):
        replace(valid_candidate, source_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="risk_reason_codes"):
        replace(valid_candidate, risk_reason_codes=("unexpected",))
    with pytest.raises(ValueError, match="risk_reason_codes"):
        replace(valid_candidate, risk_gate_passed=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(valid_candidate, paper_only=False)


def test_manual_review_queue_dataclasses_are_frozen_and_validate_invariants():
    queue = build_paper_manual_review_queue(
        [candidate(1, score=Decimal("90.0000"))],
        market_scores=(market_score("token-1"),),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(config_version="node6-test"),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        queue.item_count = 0
    with pytest.raises(FrozenInstanceError):
        queue.items[0].rank = 0
    with pytest.raises(ValueError, match="status_rank"):
        replace(queue.items[0], status_rank=2)
    with pytest.raises(ValueError, match="item_count"):
        replace(queue, item_count=0)
    with pytest.raises(ValueError, match="top_queue_item_id"):
        replace(queue, top_queue_item_id="other")


def test_paper_manual_review_log_appends_jsonl_queue(tmp_path):
    queue = build_paper_manual_review_queue(
        [candidate(1, score=Decimal("90.0000"))],
        market_scores=(market_score("token-1"),),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(config_version="node6-test"),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )
    log = PaperManualReviewLog(path=tmp_path / "manual-review.jsonl")

    log.append(queue)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"blocked_quality_item_count"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["generated_at"] == "2026-09-03T00:00:00+00:00"
    assert stored["config_version"] == "node6-test"
    assert stored["items"][0]["source_score"] == "90.0000"
    assert stored["items"][0]["status"] == "paper_review_ready"
    assert stored["items"][0]["boundary_statement"] == queue.boundary_statement


def test_paper_manual_review_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    queue = build_paper_manual_review_queue(
        [candidate(1, score=Decimal("90.0000"))],
        market_scores=(),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(config_version="node6-test"),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )
    log = PaperManualReviewLog(path=str(tmp_path / "nested" / "queue.jsonl"))

    log.append(queue)
    log.append(queue)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["generated_at"] == "2026-09-03T00:00:00+00:00"
    assert json.loads(lines[1])["generated_at"] == "2026-09-03T00:00:00+00:00"


def test_paper_manual_review_log_rejects_invalid_paths_and_inputs(tmp_path):
    with pytest.raises(ValueError, match="path"):
        PaperManualReviewLog(path=object())
    with pytest.raises(ValueError, match="path"):
        PaperManualReviewLog(path=" ")

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    with pytest.raises(ValueError, match="path"):
        PaperManualReviewLog(path=existing_dir)

    existing_file = tmp_path / "parent-file"
    existing_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        PaperManualReviewLog(path=existing_file / "manual-review.jsonl")

    path = tmp_path / "manual-review.jsonl"
    log = PaperManualReviewLog(path=path)
    with pytest.raises(ValueError, match="PaperManualReviewQueue"):
        log.append(object())
    assert not path.exists()


def test_paper_manual_review_log_preserves_existing_file_when_validation_fails(
    tmp_path,
):
    queue = build_paper_manual_review_queue(
        [candidate(1, score=Decimal("90.0000"))],
        market_scores=(),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(config_version="node6-test"),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )
    object.__setattr__(queue.items[0], "source_score", Decimal("NaN"))
    path = tmp_path / "manual-review.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperManualReviewLog(path=path)

    with pytest.raises(ValueError, match="finite|JSON|serializable"):
        log.append(queue)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_manual_review_queue_boundary_statement_contract():
    config = PaperManualReviewConfig(config_version="node6-test")
    assert (
        config.boundary_statement
        == "This is a paper-only manual-review artifact for human inspection, not a trade instruction or order instruction."
    )

    for boundary_statement in (
        "manual-review artifact for human inspection, not a trade instruction or order instruction.",
        "This is a paper-only artifact for human inspection, not a trade instruction or order instruction.",
        "This is a paper-only manual-review artifact for human inspection.",
        "This is a paper-only manual-review artifact for human inspection, not a trade instruction.",
    ):
        with pytest.raises(ValueError, match="boundary_statement"):
            PaperManualReviewConfig(
                config_version="node6-test",
                boundary_statement=boundary_statement,
            )

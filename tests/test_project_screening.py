import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventMarketSnapshot,
    PaperCostAwareEventStrategyConfig,
    PaperCostAwareEventStrategyReport,
    build_paper_cost_aware_event_strategy_report,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningCandidate,
    PaperProjectScreeningConfig,
    PaperProjectScreeningGateResult,
    PaperProjectScreeningLog,
    PaperProjectScreeningQueueItem,
    PaperProjectScreeningReport,
    build_paper_project_screening_report,
)


GENERATED_AT = datetime(2026, 6, 16, 13, 0, tzinfo=UTC)


def cost_assumptions(**overrides):
    values = {
        "taker_fee_rate": Decimal("0.0000"),
        "slippage_cost_per_share": Decimal("0.0000"),
        "funding_cost_per_share": Decimal("0.0000"),
        "finalization_cost_per_share": Decimal("0.0000"),
        "time_cost_per_share": Decimal("0.0000"),
        "risk_cost_per_share": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperCostAwareEventCostAssumptions(**values)


def cost_aware_config(**overrides):
    values = {
        "config_version": "cost-aware-event-v1",
        "min_confidence": Decimal("0.7000"),
        "max_spread": Decimal("0.0500"),
        "max_resolution_risk": Decimal("0.2000"),
        "min_ask_size": Decimal("10.0000"),
        "min_net_edge": Decimal("0.0100"),
    }
    values.update(overrides)
    return PaperCostAwareEventStrategyConfig(**values)


def cost_aware_report(**overrides):
    values = {
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "fair_probability_yes": Decimal("0.6200"),
        "confidence": Decimal("0.9000"),
        "yes_bid": Decimal("0.5400"),
        "yes_ask": Decimal("0.5500"),
        "yes_ask_size": Decimal("250.0000"),
        "no_bid": Decimal("0.4400"),
        "no_ask": Decimal("0.5000"),
        "no_ask_size": Decimal("200.0000"),
        "spread": Decimal("0.0100"),
        "resolution_risk": Decimal("0.0500"),
        "risk_cost_per_share": Decimal("0.0000"),
        "min_net_edge": Decimal("0.0100"),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    snapshot = PaperCostAwareEventMarketSnapshot(
        market_slug=values["market_slug"],
        question=values["question"],
        fair_probability_yes=values["fair_probability_yes"],
        confidence=values["confidence"],
        yes_bid=values["yes_bid"],
        yes_ask=values["yes_ask"],
        yes_ask_size=values["yes_ask_size"],
        no_bid=values["no_bid"],
        no_ask=values["no_ask"],
        no_ask_size=values["no_ask_size"],
        spread=values["spread"],
        resolution_risk=values["resolution_risk"],
    )
    return build_paper_cost_aware_event_strategy_report(
        snapshot,
        cost_assumptions=cost_assumptions(
            risk_cost_per_share=values["risk_cost_per_share"],
        ),
        config=cost_aware_config(min_net_edge=values["min_net_edge"]),
        generated_at=values["generated_at"],
    )


def screening_config(**overrides):
    values = {
        "config_version": "project-screening-v1",
        "min_screening_score": Decimal("0.010000"),
        "reference_ask_size": Decimal("100.0000"),
        "net_edge_weight": Decimal("1.0000"),
        "confidence_weight": Decimal("0.0000"),
        "depth_weight": Decimal("0.0000"),
        "spread_penalty_weight": Decimal("0.0000"),
        "resolution_risk_penalty_weight": Decimal("0.0000"),
        "cost_penalty_weight": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperProjectScreeningConfig(**values)


def build_report(reports, config=None):
    return build_paper_project_screening_report(
        reports,
        config=config or screening_config(),
        generated_at=GENERATED_AT,
    )


def gate_statuses(report):
    return {gate.gate_name: gate.status for gate in report.gate_results}


def test_project_screening_builds_research_queue_from_cost_aware_reports():
    ready = cost_aware_report(
        market_slug="fed-cut-june-2026",
        question="Will the Fed cut rates by June 2026?",
        fair_probability_yes=Decimal("0.6200"),
        yes_ask=Decimal("0.5500"),
        yes_ask_size=Decimal("250.0000"),
    )
    watch = cost_aware_report(
        market_slug="inflation-above-three-2026",
        question="Will inflation be above 3% in 2026?",
        fair_probability_yes=Decimal("0.5600"),
        yes_ask=Decimal("0.5500"),
        yes_ask_size=Decimal("50.0000"),
        min_net_edge=Decimal("0.0200"),
    )

    report = build_report((watch, ready))

    assert isinstance(report, PaperProjectScreeningReport)
    assert isinstance(report.queue_items[0], PaperProjectScreeningQueueItem)
    assert isinstance(report.candidates[0], PaperProjectScreeningCandidate)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.generated_at == GENERATED_AT
    assert report.candidate_count == 2
    assert tuple(item.market_slug for item in report.queue_items) == (
        "fed-cut-june-2026",
        "inflation-above-three-2026",
    )
    assert report.queue_items[0].queue_position == 1
    assert report.queue_items[0].research_bucket == "research_ready"
    assert report.queue_items[0].source_status == "paper_review_ready"
    assert report.queue_items[0].scoring_side == "yes"
    assert report.queue_items[0].screening_score == Decimal("0.070000")
    assert report.queue_items[1].queue_position == 2
    assert report.queue_items[1].research_bucket == "watch"
    assert report.queue_items[1].screening_score == Decimal("0.010000")
    assert gate_statuses(report) == {
        "input_count": "pass",
        "candidate_types": "pass",
        "unique_slugs": "pass",
        "screenable_candidates": "pass",
    }


def test_project_screening_score_uses_weighted_edge_confidence_depth_risk_and_cost_components():
    report = build_report(
        (
            cost_aware_report(
                fair_probability_yes=Decimal("0.6200"),
                yes_ask=Decimal("0.5500"),
                yes_ask_size=Decimal("50.0000"),
                spread=Decimal("0.0200"),
                resolution_risk=Decimal("0.1000"),
                risk_cost_per_share=Decimal("0.0100"),
            ),
        ),
        config=screening_config(
            min_screening_score=Decimal("0.0000"),
            reference_ask_size=Decimal("100.0000"),
            net_edge_weight=Decimal("1.0000"),
            confidence_weight=Decimal("0.1000"),
            depth_weight=Decimal("0.0500"),
            spread_penalty_weight=Decimal("0.5000"),
            resolution_risk_penalty_weight=Decimal("0.2500"),
            cost_penalty_weight=Decimal("1.0000"),
        ),
    )

    candidate = report.candidates[0]
    assert candidate.edge_component == Decimal("0.060000")
    assert candidate.confidence_component == Decimal("0.090000")
    assert candidate.depth_component == Decimal("0.025000")
    assert candidate.spread_penalty == Decimal("0.010000")
    assert candidate.resolution_risk_penalty == Decimal("0.025000")
    assert candidate.cost_penalty == Decimal("0.010000")
    assert candidate.screening_score == Decimal("0.130000")
    assert report.queue_items[0].screening_score == Decimal("0.130000")


@pytest.mark.parametrize(
    ("source_report", "expected_bucket"),
    (
        (
            cost_aware_report(
                market_slug="cost-eroded",
                fair_probability_yes=Decimal("0.5600"),
                yes_ask=Decimal("0.5500"),
                risk_cost_per_share=Decimal("0.0200"),
                min_net_edge=Decimal("0.0001"),
            ),
            "defer",
        ),
        (
            cost_aware_report(
                market_slug="no-edge",
                fair_probability_yes=Decimal("0.5000"),
                yes_ask=Decimal("0.5500"),
                no_ask=Decimal("0.5500"),
            ),
            "defer",
        ),
        (
            cost_aware_report(market_slug="risk-blocked", confidence=Decimal("0.6500")),
            "blocked",
        ),
    ),
)
def test_project_screening_assigns_blocked_and_defer_buckets(source_report, expected_bucket):
    report = build_report((source_report,))

    assert report.queue_items[0].research_bucket == expected_bucket
    assert report.queue_items[0].market_slug == source_report.market_slug


def test_project_screening_marks_blocked_sources_as_screening_blocked():
    source_report = cost_aware_report(
        market_slug="blocked-with-edge",
        confidence=Decimal("0.6500"),
    )

    report = build_report(
        (source_report,),
        config=screening_config(min_screening_score=Decimal("0.100000")),
    )

    assert source_report.status == "blocked_by_risk"
    assert report.queue_items[0].research_bucket == "blocked"
    assert report.candidates[0].screening_status == "screening_blocked"


def test_project_screening_uses_valid_depth_side_when_source_has_no_selected_side():
    source_report = cost_aware_report(
        market_slug="valid-depth-watch",
        fair_probability_yes=Decimal("0.5600"),
        yes_ask=Decimal("0.5500"),
        yes_ask_size=Decimal("25.0000"),
        no_ask=Decimal("0.5000"),
        min_net_edge=Decimal("0.0200"),
    )

    report = build_report((source_report,))

    assert source_report.selected_side == "none"
    assert source_report.status == "watch"
    assert report.candidates[0].scoring_side == "yes"
    assert report.candidates[0].net_edge_per_share == Decimal("0.010000")
    assert report.queue_items[0].research_bucket == "watch"


def test_project_screening_depth_validity_uses_source_depth_gates_not_positive_size_only():
    source_report = cost_aware_report(
        market_slug="insufficient-depth",
        fair_probability_yes=Decimal("0.6200"),
        yes_ask=Decimal("0.5500"),
        yes_ask_size=Decimal("5.0000"),
        no_ask=Decimal("0.5000"),
        no_ask_size=Decimal("5.0000"),
    )

    report = build_report((source_report,))

    assert source_report.status == "blocked_by_inputs"
    assert report.candidates[0].valid_depth is False
    assert report.candidates[0].scoring_side == "none"
    assert report.candidates[0].ask_size is None
    assert report.candidates[0].depth_component == Decimal("0.000000")
    assert report.candidates[0].screening_score == Decimal("0.000000")
    assert report.queue_items[0].research_bucket == "blocked"


def test_project_screening_rejects_duplicate_slugs_and_invalid_source_types():
    source_report = cost_aware_report()

    with pytest.raises(ValueError, match="unique"):
        build_report((source_report, source_report))
    with pytest.raises(ValueError, match="PaperCostAwareEventStrategyReport"):
        build_report((object(),))
    with pytest.raises(ValueError, match="at least one"):
        build_report(())


def test_project_screening_report_rejects_queue_items_that_do_not_match_candidates():
    report = build_report((cost_aware_report(),))
    mismatched_item = replace(
        report.queue_items[0],
        market_slug="unrelated-market",
        screening_score=Decimal("999.000000"),
    )

    with pytest.raises(ValueError, match="queue_items"):
        replace(report, queue_items=(mismatched_item,))


def test_project_screening_report_rejects_queue_bucket_that_conflicts_with_candidate_status():
    report = build_report((cost_aware_report(),))
    mismatched_item = replace(report.queue_items[0], research_bucket="watch")

    with pytest.raises(ValueError, match="queue_items must match candidates"):
        replace(
            report,
            ready_count=0,
            watch_count=1,
            queue_items=(mismatched_item,),
        )


@pytest.mark.parametrize(
    ("config_overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"min_screening_score": Decimal("-0.000001")}, "min_screening_score"),
        ({"reference_ask_size": Decimal("0.0000")}, "reference_ask_size|positive"),
        ({"net_edge_weight": "1.0000"}, "net_edge_weight"),
        ({"cost_penalty_weight": Decimal("NaN")}, "cost_penalty_weight|finite"),
    ),
)
def test_project_screening_config_rejects_invalid_inputs(config_overrides, message):
    with pytest.raises(ValueError, match=message):
        screening_config(**config_overrides)


def test_project_screening_dataclasses_are_frozen_and_revalidate_report_flags():
    report = build_report((cost_aware_report(),))

    with pytest.raises(FrozenInstanceError):
        report.candidate_count = 10
    with pytest.raises(FrozenInstanceError):
        report.queue_items[0].research_bucket = "blocked"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)


def test_project_screening_log_appends_jsonl_decimal_strings_and_preserves_existing_file(tmp_path):
    report = build_report((cost_aware_report(),))
    log = PaperProjectScreeningLog(
        path=tmp_path / "nested" / "project-screening.jsonl",
    )

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-06-16T13:00:00+00:00"
    assert stored["candidate_count"] == 1
    assert stored["queue_items"][0]["market_slug"] == "fed-cut-june-2026"
    assert stored["queue_items"][0]["research_bucket"] == "research_ready"
    assert stored["queue_items"][0]["screening_score"] == "0.070000"
    assert stored["candidates"][0]["net_edge_per_share"] == "0.070000"

    existing_log_path = tmp_path / "existing.jsonl"
    existing_log_path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PaperProjectScreeningReport"):
        PaperProjectScreeningLog(path=existing_log_path).append(object())
    assert existing_log_path.read_text(encoding="utf-8") == "existing\n"

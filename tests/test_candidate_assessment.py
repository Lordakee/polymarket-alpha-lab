from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.candidate_assessment import (
    PaperCandidateAssessmentConfig,
    PaperCandidateAssessmentReport,
    PaperCandidateAssessmentRow,
    build_paper_candidate_assessment_report,
)
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventMarketSnapshot,
    PaperCostAwareEventStrategyConfig,
    build_paper_cost_aware_event_strategy_report,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningConfig,
    build_paper_project_screening_report,
)


SOURCE_GENERATED_AT = datetime(2026, 6, 16, 13, 0, tzinfo=UTC)
ASSESSMENT_GENERATED_AT = datetime(
    2026,
    6,
    16,
    15,
    30,
    tzinfo=timezone(timedelta(hours=2)),
)


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
        "generated_at": SOURCE_GENERATED_AT,
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


def screening_report(cost_reports, config=None):
    return build_paper_project_screening_report(
        cost_reports,
        config=config or screening_config(),
        generated_at=SOURCE_GENERATED_AT,
    )


def assessment_config(**overrides):
    values = {
        "config_version": "candidate-assessment-v1",
        "min_ready_score": Decimal("0.010000"),
        "max_total_cost_per_share": Decimal("0.050000"),
    }
    values.update(overrides)
    return PaperCandidateAssessmentConfig(**values)


def build_assessment(screening, cost_reports, config=None):
    return build_paper_candidate_assessment_report(
        screening,
        cost_reports,
        config=config or assessment_config(),
        generated_at=ASSESSMENT_GENERATED_AT,
    )


def row_by_slug(report):
    return {row.market_slug: row for row in report.assessment_rows}


def test_candidate_assessment_builds_rows_from_screening_and_cost_evidence():
    ready = cost_aware_report(
        market_slug="b-fed-cut-june-2026",
        question="Will the Fed cut rates by June 2026?",
        fair_probability_yes=Decimal("0.6300"),
        yes_ask=Decimal("0.5500"),
        spread=Decimal("0.0100"),
        resolution_risk=Decimal("0.0200"),
    )
    watch = cost_aware_report(
        market_slug="a-watch-inflation-2026",
        question="Will inflation be above 3% in 2026?",
        fair_probability_yes=Decimal("0.5600"),
        yes_ask=Decimal("0.5500"),
        spread=Decimal("0.0100"),
        resolution_risk=Decimal("0.0200"),
        min_net_edge=Decimal("0.0200"),
    )
    screening = screening_report((watch, ready))

    report = build_assessment(screening, (ready, watch))

    assert isinstance(report, PaperCandidateAssessmentReport)
    assert isinstance(report.assessment_rows[0], PaperCandidateAssessmentRow)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == datetime(2026, 6, 16, 13, 30, tzinfo=UTC)
    assert report.config_version == "candidate-assessment-v1"
    assert report.candidate_count == 2
    assert report.assessed_count == 2
    assert report.ready_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 0
    assert tuple(row.market_slug for row in report.assessment_rows) == (
        "b-fed-cut-june-2026",
        "a-watch-inflation-2026",
    )

    ready_row = report.assessment_rows[0]
    assert ready_row.market_slug == "b-fed-cut-june-2026"
    assert ready_row.question == "Will the Fed cut rates by June 2026?"
    assert ready_row.research_bucket == "research_ready"
    assert ready_row.assessment_status == "ready"
    assert ready_row.source_status == "paper_review_ready"
    assert ready_row.selected_side == "yes"
    assert ready_row.scoring_side == "yes"
    assert ready_row.screening_score == Decimal("0.080000")
    assert ready_row.net_edge_per_share == Decimal("0.080000")
    assert ready_row.total_cost_per_share == Decimal("0.000000")
    assert ready_row.confidence == Decimal("0.9000")
    assert ready_row.spread == Decimal("0.0100")
    assert ready_row.resolution_risk == Decimal("0.0200")
    assert ready_row.readiness_score == Decimal("0.220000")
    assert "assessment_ready" in ready_row.reason_codes

    watch_row = report.assessment_rows[1]
    assert watch_row.research_bucket == "watch"
    assert watch_row.assessment_status == "watch"
    assert watch_row.selected_side == "none"
    assert watch_row.scoring_side == "yes"
    assert watch_row.readiness_score == Decimal("0.080000")
    assert "positive_edge_watch" in watch_row.reason_codes


def test_candidate_assessment_orders_equal_scores_by_market_slug():
    alpha = cost_aware_report(
        market_slug="alpha-equal-score",
        fair_probability_yes=Decimal("0.5500"),
        yes_ask=Decimal("0.5500"),
        no_ask=Decimal("0.5500"),
    )
    beta = cost_aware_report(
        market_slug="beta-equal-score",
        fair_probability_yes=Decimal("0.5500"),
        yes_ask=Decimal("0.5500"),
        no_ask=Decimal("0.5500"),
    )
    screening = screening_report((beta, alpha))

    report = build_assessment(screening, (beta, alpha))

    assert tuple(row.market_slug for row in report.assessment_rows) == (
        "alpha-equal-score",
        "beta-equal-score",
    )
    assert tuple(row.readiness_score for row in report.assessment_rows) == (
        Decimal("0.000000"),
        Decimal("0.000000"),
    )


def test_candidate_assessment_marks_missing_cost_report_as_blocked_evidence_gap():
    ready = cost_aware_report(
        market_slug="ready-with-cost-evidence",
        fair_probability_yes=Decimal("0.6300"),
        yes_ask=Decimal("0.5500"),
    )
    missing = cost_aware_report(
        market_slug="missing-cost-evidence",
        fair_probability_yes=Decimal("0.6200"),
        yes_ask=Decimal("0.5500"),
    )
    screening = screening_report((ready, missing))

    report = build_assessment(screening, (ready,))
    rows = row_by_slug(report)

    missing_row = rows["missing-cost-evidence"]
    assert report.candidate_count == 2
    assert report.assessed_count == 2
    assert report.ready_count == 1
    assert report.blocked_count == 1
    assert missing_row.assessment_status == "blocked"
    assert missing_row.readiness_score == Decimal("0.000000")
    assert missing_row.confidence is None
    assert missing_row.spread is None
    assert missing_row.resolution_risk is None
    assert "missing_cost_report" in missing_row.reason_codes


def test_candidate_assessment_blocks_high_cost_and_nonpositive_edge_rows():
    high_cost = cost_aware_report(
        market_slug="high-cost-positive-edge",
        fair_probability_yes=Decimal("0.6800"),
        yes_ask=Decimal("0.5500"),
        risk_cost_per_share=Decimal("0.0600"),
    )
    nonpositive_edge = cost_aware_report(
        market_slug="cost-eroded-edge",
        fair_probability_yes=Decimal("0.5600"),
        yes_ask=Decimal("0.5500"),
        risk_cost_per_share=Decimal("0.0200"),
        min_net_edge=Decimal("0.0001"),
    )
    screening = screening_report((high_cost, nonpositive_edge))

    report = build_assessment(screening, (high_cost, nonpositive_edge))
    rows = row_by_slug(report)

    assert report.ready_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 2
    assert rows["high-cost-positive-edge"].assessment_status == "blocked"
    assert rows["high-cost-positive-edge"].net_edge_per_share == Decimal("0.070000")
    assert "high_cost" in rows["high-cost-positive-edge"].reason_codes
    assert rows["cost-eroded-edge"].assessment_status == "blocked"
    assert rows["cost-eroded-edge"].net_edge_per_share == Decimal("-0.010000")
    assert "nonpositive_net_edge" in rows["cost-eroded-edge"].reason_codes


def test_candidate_assessment_rejects_mismatched_duplicate_and_invalid_cost_reports():
    ready = cost_aware_report(market_slug="ready-candidate")
    extra = cost_aware_report(market_slug="extra-candidate")
    screening = screening_report((ready,))

    with pytest.raises(ValueError, match="screening candidates"):
        build_assessment(screening, (ready, extra))
    with pytest.raises(ValueError, match="unique"):
        build_assessment(screening, (ready, ready))
    with pytest.raises(ValueError, match="PaperCostAwareEventStrategyReport"):
        build_assessment(screening, (object(),))


def test_candidate_assessment_dataclasses_are_frozen_and_revalidate_counts_and_flags():
    report = build_assessment(
        screening_report((cost_aware_report(),)),
        (cost_aware_report(),),
    )

    with pytest.raises(FrozenInstanceError):
        report.ready_count = 99
    with pytest.raises(FrozenInstanceError):
        report.assessment_rows[0].readiness_score = Decimal("0.999999")
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ready_count"):
        replace(report, ready_count=0)
    with pytest.raises(ValueError, match="assessed_count"):
        replace(report, assessed_count=2)


def test_candidate_assessment_rejects_non_decimal_numeric_values_and_bool_counts():
    report = build_assessment(
        screening_report((cost_aware_report(),)),
        (cost_aware_report(),),
    )
    row = report.assessment_rows[0]

    with pytest.raises(ValueError, match="min_ready_score"):
        assessment_config(min_ready_score=1)
    with pytest.raises(ValueError, match="max_total_cost_per_share"):
        assessment_config(max_total_cost_per_share=0.05)
    with pytest.raises(ValueError, match="assessed_count"):
        replace(report, assessed_count=True)
    with pytest.raises(ValueError, match="readiness_score"):
        replace(row, readiness_score=0.1)

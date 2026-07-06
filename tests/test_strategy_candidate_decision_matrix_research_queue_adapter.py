from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_candidate_decision_matrix import (
    PaperStrategyCandidateDecisionInput,
    PaperStrategyCandidateDecisionMatrixConfig,
    build_paper_strategy_candidate_decision_matrix_report,
)
from polymarket_alpha_lab.strategy_candidate_decision_matrix_research_queue_adapter import (
    PaperStrategyCandidateDecisionResearchQueueSupplement,
    PaperStrategyCandidateDecisionResearchQueueSupplementRow,
    paper_strategy_candidate_decision_inputs_from_research_queue,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)


GENERATED_AT = datetime(2026, 7, 6, 17, 30, tzinfo=timezone(timedelta(hours=2)))
GENERATED_AT_UTC = datetime(2026, 7, 6, 15, 30, tzinfo=UTC)


def test_adapter_maps_research_queue_and_supplement_into_decision_inputs() -> None:
    report = _research_report(
        (
            _research_row(
                market_slug="alpha-market",
                question="Will alpha resolve yes?",
                research_rank=1,
                queue_rank=1,
                net_edge_per_share=Decimal("0.090000"),
                total_cost_per_share=Decimal("0.020000"),
                resolution_risk=Decimal("0.120000"),
                reason_codes=("queue_alpha",),
                evidence_gap_codes=("queue_gap_alpha",),
            ),
            _research_row(
                market_slug="beta-market",
                question="Will beta resolve yes?",
                research_rank=2,
                queue_rank=2,
                net_edge_per_share=Decimal("0.060000"),
                total_cost_per_share=Decimal("0.010000"),
                resolution_risk=Decimal("0.200000"),
                reason_codes=("queue_beta",),
            ),
        ),
    )
    supplement = _supplement(
        report,
        (
            _supplement_row(
                "alpha-market",
                question="Will alpha resolve yes?",
                forecast_probability=Decimal("0.650000"),
                market_probability=Decimal("0.560000"),
                resolution_risk_score=Decimal("0.120000"),
                reason_codes=("source_fresh",),
                evidence_gap_codes=("supplement_gap_alpha",),
            ),
            _supplement_row(
                "beta-market",
                question="Will beta resolve yes?",
                forecast_probability=Decimal("0.610000"),
                market_probability=Decimal("0.550000"),
                resolution_risk_score=Decimal("0.200000"),
                reason_codes=("source_fresh",),
            ),
        ),
    )

    inputs = paper_strategy_candidate_decision_inputs_from_research_queue(
        report,
        supplement=supplement,
    )

    assert tuple(type(item) for item in inputs) == (
        PaperStrategyCandidateDecisionInput,
        PaperStrategyCandidateDecisionInput,
    )
    assert tuple(item.market_slug for item in inputs) == ("alpha-market", "beta-market")
    assert inputs[0].question == "Will alpha resolve yes?"
    assert inputs[0].team_id == "macro_team"
    assert inputs[0].category == "macro"
    assert inputs[0].forecast_probability == Decimal("0.650000")
    assert inputs[0].market_probability == Decimal("0.560000")
    assert inputs[0].net_edge_per_share == Decimal("0.090000")
    assert inputs[0].total_cost_per_share == Decimal("0.020000")
    assert inputs[0].resolution_risk_score == Decimal("0.120000")
    assert inputs[0].reason_codes == (
        "decision_matrix_research_queue_adapter",
        "decision_matrix_research_queue_supplement",
        "high_net_edge",
        "queue_alpha",
        "queue_gap_alpha",
        "source_fresh",
    )
    assert inputs[0].evidence_gap_codes == (
        "queue_gap_alpha",
        "supplement_gap_alpha",
    )

    matrix_report = build_paper_strategy_candidate_decision_matrix_report(
        inputs,
        config=PaperStrategyCandidateDecisionMatrixConfig(
            config_version="strategy-candidate-decision-matrix-v1",
        ),
        generated_at=GENERATED_AT,
    )
    assert matrix_report.generated_at == GENERATED_AT_UTC
    assert matrix_report.candidate_count == Decimal("2.000000")


def test_adapter_rejects_missing_extra_and_duplicate_market_slug_coverage() -> None:
    report = _research_report((_research_row(market_slug="alpha-market"),))

    with pytest.raises(ValueError, match="missing market_slug"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            report,
            supplement=_supplement(report, ()),
        )

    with pytest.raises(ValueError, match="extra market_slug"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            report,
            supplement=_supplement(
                report,
                (
                    _supplement_row("alpha-market"),
                    _supplement_row("extra-market"),
                ),
            ),
        )

    with pytest.raises(ValueError, match="duplicate market_slug"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            report,
            supplement=_supplement(
                report,
                (
                    _supplement_row("alpha-market"),
                    _supplement_row("alpha-market"),
                ),
            ),
        )

    duplicate_report = _research_report(
        (
            _research_row(market_slug="alpha-market", research_rank=1, queue_rank=1),
            _research_row(market_slug="alpha-market", research_rank=2, queue_rank=2),
        ),
    )
    with pytest.raises(ValueError, match="duplicate market_slug"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            duplicate_report,
            supplement=_supplement(duplicate_report, (_supplement_row("alpha-market"),)),
        )


def test_adapter_rejects_identity_and_numeric_mismatches() -> None:
    report = _research_report(
        (
            _research_row(
                market_slug="alpha-market",
                question="Will alpha resolve yes?",
                net_edge_per_share=Decimal("0.090000"),
                total_cost_per_share=Decimal("0.020000"),
                resolution_risk=Decimal("0.120000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="question must match"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            report,
            supplement=_supplement(
                report,
                (_supplement_row("alpha-market", question="Different question?"),),
            ),
        )

    with pytest.raises(ValueError, match="selected_side must match"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            report,
            supplement=_supplement(
                report,
                (
                    _supplement_row(
                        "alpha-market",
                        question="Will alpha resolve yes?",
                        selected_side="no",
                    ),
                ),
            ),
        )

    with pytest.raises(ValueError, match="source_queue_config_version"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            report,
            supplement=replace(
                _supplement(report, (_supplement_row("alpha-market"),)),
                source_queue_config_version="wrong-version",
            ),
        )

    with pytest.raises(ValueError, match="net_edge_per_share is required"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            _research_report(
                (
                    _research_row(
                        market_slug="alpha-market",
                        net_edge_per_share=None,
                    ),
                ),
            ),
            supplement=_supplement(report, (_supplement_row("alpha-market"),)),
        )

    with pytest.raises(ValueError, match="forecast edge must match"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            report,
            supplement=_supplement(
                report,
                (
                    _supplement_row(
                        "alpha-market",
                        question="Will alpha resolve yes?",
                        forecast_probability=Decimal("0.640000"),
                        market_probability=Decimal("0.560000"),
                    ),
                ),
            ),
        )

    with pytest.raises(ValueError, match="resolution_risk_score must match"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            report,
            supplement=_supplement(
                report,
                (
                    _supplement_row(
                        "alpha-market",
                        question="Will alpha resolve yes?",
                        resolution_risk_score=Decimal("0.130000"),
                    ),
                ),
            ),
        )


def test_adapter_enforces_frozen_dataclasses_and_hard_flags() -> None:
    report = _research_report((_research_row(market_slug="alpha-market"),))
    supplement = _supplement(report, (_supplement_row("alpha-market"),))

    with pytest.raises(FrozenInstanceError):
        supplement.rows = ()  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_report must be exactly"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            "not-report",
            supplement=supplement,
        )
    with pytest.raises(ValueError, match="supplement must be exactly"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            report,
            supplement="not-supplement",
        )
    with pytest.raises(ValueError, match="supplement must be readonly"):
        paper_strategy_candidate_decision_inputs_from_research_queue(
            report,
            supplement=replace(supplement, readonly=False),
        )
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        _supplement_row("alpha-market", forecast_probability=0.65)  # type: ignore[arg-type]


def _research_report(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> PaperStrategyCandidateResearchQueueReport:
    ready_count = sum(1 for row in rows if row.research_status == "ready")
    selected_count = sum(1 for row in rows if row.decision == "selected")
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=datetime(2026, 7, 6, 14, tzinfo=UTC),
        config_version="strategy-candidate-research-queue-v0",
        source_config_version="paper-action-gated-strategy-recommendation-queue-v0",
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
        source_reason_code_counts=(),
        research_status="ready",
        candidate_count=len(rows),
        research_ready_count=ready_count,
        watch_count=sum(1 for row in rows if row.research_status == "watch"),
        blocked_count=sum(1 for row in rows if row.research_status == "blocked"),
        selected_count=selected_count,
        skipped_count=sum(1 for row in rows if row.decision == "skipped"),
        not_selected_count=sum(1 for row in rows if row.decision == "not_selected"),
        total_ready_notional=sum(
            (row.suggested_notional for row in rows if row.research_status == "ready"),
            Decimal("0"),
        ),
        total_selected_notional=sum(
            (row.selected_position_notional for row in rows),
            Decimal("0"),
        ),
        total_suggested_notional=sum(
            (row.suggested_notional for row in rows),
            Decimal("0"),
        ),
        top_research_priority_score=rows[0].research_priority_score if rows else Decimal("0"),
        average_research_ready_score=(
            sum((row.research_priority_score for row in rows), Decimal("0"))
            / Decimal(ready_count)
            if ready_count
            else Decimal("0")
        ),
        primary_reason_code_counts=tuple(
            sorted(
                {
                    row.primary_reason_code: sum(
                        1 for item in rows if item.primary_reason_code == row.primary_reason_code
                    )
                    for row in rows
                }.items(),
                key=lambda item: (-item[1], item[0]),
            ),
        ),
        rows=rows,
        reason_codes=("candidate_research_queue_ready",),
    )


def _research_row(
    *,
    market_slug: str = "alpha-market",
    question: str | None = None,
    selected_side: str = "yes",
    research_rank: int = 1,
    queue_rank: int = 1,
    net_edge_per_share: Decimal | None = Decimal("0.090000"),
    total_cost_per_share: Decimal | None = Decimal("0.020000"),
    resolution_risk: Decimal | None = Decimal("0.120000"),
    reason_codes: tuple[str, ...] = ("queue_reason",),
    evidence_gap_codes: tuple[str, ...] = (),
) -> PaperStrategyCandidateResearchQueueRow:
    if question is None:
        question = f"Will {market_slug} resolve yes?"
    if "high_net_edge" not in reason_codes:
        reason_codes = ("high_net_edge", *reason_codes)
    for evidence_gap_code in evidence_gap_codes:
        if evidence_gap_code not in reason_codes:
            reason_codes = (*reason_codes, evidence_gap_code)
    return PaperStrategyCandidateResearchQueueRow(
        research_rank=research_rank,
        queue_rank=queue_rank,
        market_slug=market_slug,
        question=question,
        selected_side=selected_side,
        scoring_side=selected_side,
        source_action="recommend",
        decision="selected",
        queue_status="ready",
        research_status="ready",
        research_bucket="macro",
        assessment_status="ready",
        source_status="ready",
        readiness_status="ready",
        recommendation_score=Decimal("0.800000"),
        readiness_score=Decimal("0.600000"),
        screening_score=Decimal("0.750000"),
        net_edge_per_share=net_edge_per_share,
        total_cost_per_share=total_cost_per_share,
        confidence=Decimal("0.700000"),
        spread=Decimal("0.020000"),
        resolution_risk=resolution_risk,
        suggested_notional=Decimal("20.000000"),
        selected_position_notional=Decimal("20.000000"),
        primary_reason_code="high_net_edge",
        research_priority_score=Decimal("0.700000"),
        evidence_gap_codes=evidence_gap_codes,
        reason_codes=reason_codes,
        explanation="Candidate has enough paper-only evidence.",
    )


def _supplement(
    source_report: PaperStrategyCandidateResearchQueueReport,
    rows: tuple[PaperStrategyCandidateDecisionResearchQueueSupplementRow, ...],
) -> PaperStrategyCandidateDecisionResearchQueueSupplement:
    return PaperStrategyCandidateDecisionResearchQueueSupplement(
        generated_at=GENERATED_AT,
        config_version="decision-matrix-research-queue-supplement-v1",
        source_queue_config_version=source_report.config_version,
        rows=rows,
    )


def _supplement_row(
    market_slug: str,
    *,
    question: str | None = None,
    selected_side: str = "yes",
    forecast_probability: Decimal = Decimal("0.650000"),
    market_probability: Decimal = Decimal("0.560000"),
    reason_codes: tuple[str, ...] = ("source_fresh",),
    evidence_gap_codes: tuple[str, ...] = (),
    resolution_risk_score: Decimal = Decimal("0.120000"),
) -> PaperStrategyCandidateDecisionResearchQueueSupplementRow:
    if question is None:
        question = f"Will {market_slug} resolve yes?"
    return PaperStrategyCandidateDecisionResearchQueueSupplementRow(
        market_slug=market_slug,
        question=question,
        selected_side=selected_side,
        team_id="macro_team",
        category="macro",
        forecast_probability=forecast_probability,
        market_probability=market_probability,
        liquidity_score=Decimal("0.800000"),
        information_quality_score=Decimal("0.850000"),
        source_count=Decimal("4"),
        freshness_minutes=Decimal("20"),
        resolution_risk_score=resolution_risk_score,
        team_memory_score=Decimal("0.700000"),
        calibration_score=Decimal("0.720000"),
        reason_codes=reason_codes,
        evidence_gap_codes=evidence_gap_codes,
    )

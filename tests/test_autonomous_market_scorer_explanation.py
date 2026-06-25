from datetime import UTC, datetime
from decimal import Decimal

import polymarket_alpha_lab.paper_recommendation_score_explanation as score_explanation
from polymarket_alpha_lab.autonomous_market_scorer import (
    AutonomousMarketScorerReport,
    AutonomousMarketScoreRow,
)


GENERATED_AT = datetime(2026, 6, 20, 14, 0, tzinfo=UTC)


def _score_row(**overrides) -> AutonomousMarketScoreRow:
    values = {
        "condition_id": "condition-a",
        "market_slug": "market-a",
        "question": "Will market A resolve yes?",
        "scoring_side": "yes",
        "confidence_score": Decimal("0.800000"),
        "liquidity_score": Decimal("0.700000"),
        "spread_score": Decimal("0.600000"),
        "edge_score": Decimal("0.500000"),
        "cost_score": Decimal("0.020000"),
        "risk_score": Decimal("0.300000"),
        "total_score": Decimal("0.578000"),
        "score_status": "scored",
        "recommended_notional": Decimal("25.000000"),
        "estimated_edge": Decimal("0.050000"),
        "reason_codes": (
            "autonomous_market_scorer_cluster_scored",
            "liquidity_supported",
        ),
    }
    values.update(overrides)
    return AutonomousMarketScoreRow(**values)


def _scorer_report(*rows: AutonomousMarketScoreRow) -> AutonomousMarketScorerReport:
    return AutonomousMarketScorerReport(
        generated_at=GENERATED_AT,
        config_version="autonomous-market-scorer-v0",
        gate_status="pass",
        markets_scored=sum(1 for row in rows if row.score_status == "scored"),
        markets_skipped=sum(1 for row in rows if row.score_status == "skipped"),
        markets_blocked=sum(1 for row in rows if row.score_status == "blocked"),
        top_total_score=max((row.total_score for row in rows), default=Decimal("0.000000")),
        average_total_score=(
            sum((row.total_score for row in rows), Decimal("0.000000"))
            / Decimal(len(rows))
        ).quantize(Decimal("0.000001"))
        if rows
        else Decimal("0.000000"),
        total_recommended_notional=sum(
            (row.recommended_notional for row in rows),
            Decimal("0.000000"),
        ),
        score_rows=rows,
        reason_codes=tuple(
            sorted(
                {
                    reason_code
                    for row in rows
                    for reason_code in row.reason_codes
                },
            ),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_autonomous_market_scorer_report_bridges_to_report_only_explanation():
    scored = _score_row()
    skipped = _score_row(
        condition_id="condition-b",
        market_slug="market-b",
        scoring_side="no",
        total_score=Decimal("0.000000"),
        score_status="skipped",
        recommended_notional=Decimal("0.000000"),
        reason_codes=("autonomous_market_scorer_below_threshold",),
    )
    blocked = _score_row(
        condition_id="condition-c",
        market_slug="market-c",
        scoring_side="none",
        total_score=Decimal("0.000000"),
        score_status="blocked",
        recommended_notional=Decimal("0.000000"),
        reason_codes=("autonomous_market_scorer_gate_blocked",),
    )

    explanation = (
        score_explanation.build_autonomous_market_scorer_score_explanation_report(
            _scorer_report(skipped, scored, blocked),
        )
    )

    assert explanation.paper_only is True
    assert explanation.report_only is True
    assert explanation.readonly is True
    assert explanation.generated_at == GENERATED_AT
    assert explanation.config_version == "autonomous-market-scorer-v0"
    assert explanation.row_count == 3
    assert explanation.pass_count == 1
    assert explanation.watch_count == 1
    assert explanation.blocked_count == 1
    assert explanation.top_total_score == Decimal("0.578000")
    assert explanation.average_total_score == Decimal("0.192667")
    assert tuple((row.market_slug, row.side, row.score_status) for row in explanation.rows) == (
        ("market-a", "yes", "pass"),
        ("market-b", "no", "watch"),
        ("market-c", "none", "blocked"),
    )
    assert explanation.rows[0].total_score == Decimal("0.578000")
    assert explanation.rows[0].reason_codes == (
        "autonomous_market_scorer_cluster_scored",
        "liquidity_supported",
    )
    assert tuple(
        (component.component_name, component.contribution, component.direction)
        for component in explanation.rows[0].components
    ) == (("autonomous_market_scorer_total", Decimal("0.578000"), "positive"),)
    assert explanation.flags == (
        "autonomous_market_scorer_explanation",
        "paper_only",
        "readonly",
        "report_only",
    )

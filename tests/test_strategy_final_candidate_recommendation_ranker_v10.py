from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_final_candidate_recommendation_ranker_v10 import (
    FinalCandidateRecommendationRankerV10Config,
    FinalCandidateRecommendationRankerV10Input,
    FinalCandidateRecommendationRankerV10RankedRow,
    FinalCandidateRecommendationRankerV10Report,
    final_candidate_recommendation_ranker_v10_payload,
    rank_final_candidate_recommendations_v10,
)


def _config(**overrides):
    values = {
        "config_version": "final-candidate-recommendation-ranker-v10",
        "minimum_recommendation_score_bps": Decimal("50.000000"),
        "minimum_review_score_bps": Decimal("0.000000"),
        "liquidity_weight_bps": Decimal("20.000000"),
        "team_fit_weight_bps": Decimal("15.000000"),
        "minor_data_gap_penalty_bps": Decimal("10.000000"),
        "material_data_gap_penalty_bps": Decimal("35.000000"),
        "human_review_penalty_bps": Decimal("25.000000"),
    }
    values.update(overrides)
    return FinalCandidateRecommendationRankerV10Config(**values)


def _candidate(
    market_id: str,
    *,
    cost_adjusted_edge_bps: Decimal = Decimal("100.000000"),
    confidence_penalty_bps: Decimal = Decimal("10.000000"),
    liquidity_score: Decimal = Decimal("0.500000"),
    resolution_risk_premium_bps: Decimal = Decimal("5.000000"),
    team_fit_score: Decimal = Decimal("0.500000"),
    data_gap_status: str = "none",
    human_review_required: bool = False,
) -> FinalCandidateRecommendationRankerV10Input:
    return FinalCandidateRecommendationRankerV10Input(
        market_id=market_id,
        cost_adjusted_edge_bps=cost_adjusted_edge_bps,
        confidence_penalty_bps=confidence_penalty_bps,
        liquidity_score=liquidity_score,
        resolution_risk_premium_bps=resolution_risk_premium_bps,
        team_fit_score=team_fit_score,
        data_gap_status=data_gap_status,
        human_review_required=human_review_required,
    )


def test_final_candidate_recommendation_ranker_ranks_candidates_for_human_review():
    report = rank_final_candidate_recommendations_v10(
        (
            _candidate(
                "market-b",
                cost_adjusted_edge_bps=Decimal("95.000000"),
                confidence_penalty_bps=Decimal("5.000000"),
                liquidity_score=Decimal("0.800000"),
                resolution_risk_premium_bps=Decimal("10.000000"),
                team_fit_score=Decimal("0.900000"),
            ),
            _candidate(
                "market-a",
                cost_adjusted_edge_bps=Decimal("95.000000"),
                confidence_penalty_bps=Decimal("5.000000"),
                liquidity_score=Decimal("0.800000"),
                resolution_risk_premium_bps=Decimal("10.000000"),
                team_fit_score=Decimal("0.900000"),
            ),
            _candidate(
                "market-c",
                cost_adjusted_edge_bps=Decimal("40.000000"),
                confidence_penalty_bps=Decimal("10.000000"),
                liquidity_score=Decimal("0.400000"),
                resolution_risk_premium_bps=Decimal("10.000000"),
                team_fit_score=Decimal("0.400000"),
                data_gap_status="minor",
            ),
        ),
        config=_config(),
    )

    assert isinstance(report, FinalCandidateRecommendationRankerV10Report)
    assert tuple(row.market_id for row in report.ranked_rows) == (
        "market-a",
        "market-b",
        "market-c",
    )
    assert tuple(row.rank for row in report.ranked_rows) == (
        Decimal("1"),
        Decimal("2"),
        Decimal("3"),
    )
    assert report.top_market_id == "market-a"
    assert report.recommendation_status == "recommend"
    assert report.reason_codes == ("top_candidate_recommended", "candidates_ranked")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    top = report.ranked_rows[0]
    assert isinstance(top, FinalCandidateRecommendationRankerV10RankedRow)
    assert top.recommendation_score_bps == Decimal("109.500000")
    assert top.recommendation_status == "recommend"
    assert top.reason_codes == (
        "positive_net_edge",
        "liquidity_supported",
        "team_fit_supported",
        "data_gap_none",
        "manual_research_ready",
    )

    payload = report.payload
    assert payload == final_candidate_recommendation_ranker_v10_payload(report)
    assert payload["top_market_id"] == "market-a"
    assert payload["candidate_count"] == "3"
    assert payload["ranked_rows"][0]["rank"] == "1"
    assert payload["ranked_rows"][0]["recommendation_score_bps"] == "109.500000"
    assert payload["ranked_rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_final_candidate_recommendation_ranker_routes_manual_review_and_blockers():
    report = rank_final_candidate_recommendations_v10(
        (
            _candidate(
                "needs-human",
                cost_adjusted_edge_bps=Decimal("110.000000"),
                confidence_penalty_bps=Decimal("5.000000"),
                liquidity_score=Decimal("0.900000"),
                resolution_risk_premium_bps=Decimal("5.000000"),
                team_fit_score=Decimal("0.900000"),
                human_review_required=True,
            ),
            _candidate(
                "blocked-gap",
                cost_adjusted_edge_bps=Decimal("250.000000"),
                confidence_penalty_bps=Decimal("0.000000"),
                liquidity_score=Decimal("1.000000"),
                resolution_risk_premium_bps=Decimal("0.000000"),
                team_fit_score=Decimal("1.000000"),
                data_gap_status="blocking",
            ),
        ),
        config=_config(),
    )

    assert report.top_market_id == "needs-human"
    assert report.recommendation_status == "review"
    assert report.reason_codes == ("top_candidate_needs_human_review", "candidates_ranked")
    assert report.ranked_rows[0].recommendation_score_bps == Decimal("106.500000")
    assert report.ranked_rows[0].recommendation_status == "review"
    assert "human_review_required" in report.ranked_rows[0].reason_codes
    assert report.ranked_rows[1].recommendation_status == "blocked"
    assert report.ranked_rows[1].recommendation_score_bps == Decimal("0.000000")
    assert report.ranked_rows[1].reason_codes == ("data_gap_blocking",)


def test_final_candidate_recommendation_ranker_empty_input_is_readonly_report():
    report = rank_final_candidate_recommendations_v10((), config=_config())

    assert report.ranked_rows == ()
    assert report.candidate_count == Decimal("0")
    assert report.top_market_id is None
    assert report.recommendation_status == "empty"
    assert report.reason_codes == ("no_candidates",)
    assert report.payload["ranked_rows"] == []
    assert report.payload["top_market_id"] is None


def test_final_candidate_recommendation_ranker_validates_types_flags_and_consistency():
    report = rank_final_candidate_recommendations_v10(
        (_candidate("alpha"), _candidate("beta")),
        config=_config(),
    )

    with pytest.raises(FrozenInstanceError):
        report.top_market_id = "beta"
    with pytest.raises(FrozenInstanceError):
        report.ranked_rows[0].recommendation_status = "review"
    with pytest.raises(ValueError, match="cost_adjusted_edge_bps"):
        _candidate("float-edge", cost_adjusted_edge_bps=0.1)
    with pytest.raises(ValueError, match="cost_adjusted_edge_bps"):
        _candidate("int-edge", cost_adjusted_edge_bps=1)
    with pytest.raises(ValueError, match="liquidity_score"):
        _candidate("bad-liquidity", liquidity_score=Decimal("1.000001"))
    with pytest.raises(ValueError, match="human_review_required"):
        _candidate("bad-review", human_review_required="yes")
    with pytest.raises(ValueError, match="duplicate market_id"):
        rank_final_candidate_recommendations_v10(
            (_candidate("dup"), _candidate("dup")),
            config=_config(),
        )
    misordered_rows = (
        replace(report.ranked_rows[1], rank=Decimal("1")),
        replace(report.ranked_rows[0], rank=Decimal("2")),
    )
    with pytest.raises(ValueError, match="deterministic ranking"):
        replace(report, ranked_rows=misordered_rows)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="ranked_rows"):
        replace(report, ranked_rows=(object(),))
    with pytest.raises(ValueError, match="config"):
        rank_final_candidate_recommendations_v10((_candidate("alpha"),), config=object())
    with pytest.raises(ValueError, match="Decimal"):
        _config(minimum_recommendation_score_bps=50)


def test_final_candidate_recommendation_ranker_module_scope_stays_report_only():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_final_candidate_recommendation_ranker_v10.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()

    forbidden_fragments = (
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "wallet",
        "private_key",
        "signature",
        "place_order",
        "submit_order",
        "open(",
    )
    assert all(fragment not in source for fragment in forbidden_fragments)

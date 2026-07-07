from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
import re

import pytest

from polymarket_alpha_lab.strategy_recommendation_cost_adjusted_quorum_ranker_v2 import (
    StrategyRecommendationCostAdjustedQuorumRankerV2Config,
    StrategyRecommendationCostAdjustedQuorumRankerV2Input,
    StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow,
    StrategyRecommendationCostAdjustedQuorumRankerV2Report,
    rank_strategy_recommendation_cost_adjusted_quorum_v2,
    strategy_recommendation_cost_adjusted_quorum_ranker_v2_payload,
)


DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def _config(**overrides):
    values = {
        "config_version": "strategy-recommendation-cost-adjusted-quorum-ranker-v2",
        "minimum_specialist_agreement_count": Decimal("2"),
        "minimum_source_family_count": Decimal("2"),
        "minimum_liquidity_depth_usd": Decimal("1000.000000"),
        "minimum_cost_adjusted_ev_bps": Decimal("25.000000"),
        "minimum_recommendation_score_bps": Decimal("100.000000"),
        "specialist_quorum_weight_bps": Decimal("20.000000"),
        "source_family_weight_bps": Decimal("20.000000"),
        "official_source_weight_bps": Decimal("10.000000"),
        "liquidity_depth_weight_bps": Decimal("15.000000"),
        "require_official_source": True,
    }
    values.update(overrides)
    return StrategyRecommendationCostAdjustedQuorumRankerV2Config(**values)


def _candidate(
    candidate_id: str,
    *,
    market_slug: str | None = None,
    side: str = "yes",
    gross_edge_bps: Decimal = Decimal("100.000000"),
    taker_fee_bps: Decimal = Decimal("5.000000"),
    spread_cost_bps: Decimal = Decimal("10.000000"),
    slippage_cost_bps: Decimal = Decimal("8.000000"),
    liquidity_depth_usd: Decimal = Decimal("1500.000000"),
    specialist_agreement_count: Decimal = Decimal("3"),
    source_family_count: Decimal = Decimal("2"),
    has_official_source: bool = True,
) -> StrategyRecommendationCostAdjustedQuorumRankerV2Input:
    return StrategyRecommendationCostAdjustedQuorumRankerV2Input(
        candidate_id=candidate_id,
        market_slug=market_slug or f"{candidate_id}-market",
        side=side,
        gross_edge_bps=gross_edge_bps,
        taker_fee_bps=taker_fee_bps,
        spread_cost_bps=spread_cost_bps,
        slippage_cost_bps=slippage_cost_bps,
        liquidity_depth_usd=liquidity_depth_usd,
        specialist_agreement_count=specialist_agreement_count,
        source_family_count=source_family_count,
        has_official_source=has_official_source,
    )


def test_cost_adjusted_quorum_ranker_scores_and_ranks_deterministically():
    candidates = (
        _candidate("beta", market_slug="shared-market"),
        _candidate("gamma", gross_edge_bps=Decimal("60.000000"), liquidity_depth_usd=Decimal("500.000000")),
        _candidate("alpha", market_slug="shared-market"),
    )

    report = rank_strategy_recommendation_cost_adjusted_quorum_v2(
        candidates,
        config=_config(),
    )
    repeat_report = rank_strategy_recommendation_cost_adjusted_quorum_v2(
        candidates,
        config=_config(),
    )

    assert report == repeat_report
    assert isinstance(report, StrategyRecommendationCostAdjustedQuorumRankerV2Report)
    assert tuple(row.candidate_id for row in report.ranked_rows) == (
        "alpha",
        "beta",
        "gamma",
    )
    assert tuple(row.rank for row in report.ranked_rows) == (
        Decimal("1"),
        Decimal("2"),
        Decimal("3"),
    )
    assert report.top_candidate_id == "alpha"
    assert report.recommendation_status == "recommend"
    assert report.reason_codes == ("top_candidate_recommended", "candidates_ranked")
    assert DIGEST_PATTERN.match(report.report_digest)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    top = report.ranked_rows[0]
    assert isinstance(top, StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow)
    assert top.total_cost_bps == Decimal("23.000000")
    assert top.cost_adjusted_ev_bps == Decimal("77.000000")
    assert top.edge_margin_bps == Decimal("52.000000")
    assert top.quorum_score_bps == Decimal("50.000000")
    assert top.liquidity_depth_score_bps == Decimal("15.000000")
    assert top.recommendation_score_bps == Decimal("194.000000")
    assert top.recommendation_status == "recommend"
    assert top.reason_codes == (
        "positive_cost_adjusted_ev",
        "edge_margin_met",
        "specialist_quorum_met",
        "source_family_quorum_met",
        "official_source_present",
        "liquidity_depth_met",
        "costs_applied",
        "status_recommend",
    )
    assert DIGEST_PATTERN.match(top.decision_digest)

    review_row = report.ranked_rows[2]
    assert review_row.candidate_id == "gamma"
    assert review_row.cost_adjusted_ev_bps == Decimal("37.000000")
    assert review_row.edge_margin_bps == Decimal("12.000000")
    assert review_row.liquidity_depth_score_bps == Decimal("7.500000")
    assert review_row.recommendation_score_bps == Decimal("106.500000")
    assert review_row.recommendation_status == "review"
    assert "edge_margin_short" in review_row.reason_codes
    assert "liquidity_depth_short" in review_row.reason_codes

    payload = report.payload
    assert payload == strategy_recommendation_cost_adjusted_quorum_ranker_v2_payload(report)
    assert payload["candidate_count"] == "3"
    assert payload["top_candidate_id"] == "alpha"
    assert payload["ranked_rows"][0]["rank"] == "1"
    assert payload["ranked_rows"][0]["total_cost_bps"] == "23.000000"
    assert payload["ranked_rows"][0]["recommendation_score_bps"] == "194.000000"
    assert payload["ranked_rows"][0]["decision_digest"] == top.decision_digest
    assert payload["report_digest"] == report.report_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_cost_adjusted_quorum_ranker_blocks_missing_quorum_and_routes_review():
    report = rank_strategy_recommendation_cost_adjusted_quorum_v2(
        (
            _candidate(
                "thin-quorum",
                gross_edge_bps=Decimal("250.000000"),
                taker_fee_bps=Decimal("0.000000"),
                spread_cost_bps=Decimal("0.000000"),
                slippage_cost_bps=Decimal("0.000000"),
                liquidity_depth_usd=Decimal("2500.000000"),
                specialist_agreement_count=Decimal("1"),
                source_family_count=Decimal("1"),
                has_official_source=False,
            ),
            _candidate(
                "review-edge",
                gross_edge_bps=Decimal("45.000000"),
                taker_fee_bps=Decimal("5.000000"),
                spread_cost_bps=Decimal("0.000000"),
                slippage_cost_bps=Decimal("0.000000"),
                liquidity_depth_usd=Decimal("800.000000"),
            ),
        ),
        config=_config(),
    )

    assert report.top_candidate_id == "review-edge"
    assert report.recommendation_status == "review"
    assert report.reason_codes == ("top_candidate_review", "candidates_ranked")

    review_row = report.ranked_rows[0]
    assert review_row.total_cost_bps == Decimal("5.000000")
    assert review_row.cost_adjusted_ev_bps == Decimal("40.000000")
    assert review_row.edge_margin_bps == Decimal("15.000000")
    assert review_row.recommendation_score_bps == Decimal("117.000000")
    assert review_row.recommendation_status == "review"

    blocked = report.ranked_rows[1]
    assert blocked.candidate_id == "thin-quorum"
    assert blocked.recommendation_score_bps == Decimal("0.000000")
    assert blocked.recommendation_status == "blocked"
    assert blocked.reason_codes == (
        "positive_cost_adjusted_ev",
        "edge_margin_met",
        "specialist_quorum_short",
        "source_family_quorum_short",
        "official_source_missing",
        "liquidity_depth_met",
        "status_blocked",
    )


def test_cost_adjusted_quorum_ranker_empty_input_is_readonly_report():
    report = rank_strategy_recommendation_cost_adjusted_quorum_v2((), config=_config())

    assert report.ranked_rows == ()
    assert report.candidate_count == Decimal("0")
    assert report.top_candidate_id is None
    assert report.recommendation_status == "empty"
    assert report.reason_codes == ("no_candidates",)
    assert DIGEST_PATTERN.match(report.report_digest)
    assert report.payload["ranked_rows"] == []
    assert report.payload["top_candidate_id"] is None


def test_cost_adjusted_quorum_ranker_validates_decimals_flags_and_consistency():
    report = rank_strategy_recommendation_cost_adjusted_quorum_v2(
        (_candidate("alpha"), _candidate("beta")),
        config=_config(),
    )

    with pytest.raises(FrozenInstanceError):
        report.top_candidate_id = "beta"
    with pytest.raises(FrozenInstanceError):
        report.ranked_rows[0].recommendation_status = "review"
    with pytest.raises(ValueError, match="gross_edge_bps"):
        _candidate("float-edge", gross_edge_bps=0.1)
    with pytest.raises(ValueError, match="gross_edge_bps"):
        _candidate("int-edge", gross_edge_bps=1)
    with pytest.raises(ValueError, match="specialist_agreement_count"):
        _candidate("int-count", specialist_agreement_count=2)
    with pytest.raises(ValueError, match="taker_fee_bps"):
        _candidate("negative-cost", taker_fee_bps=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="liquidity_depth_usd"):
        _candidate("negative-depth", liquidity_depth_usd=Decimal("-1.000000"))
    with pytest.raises(ValueError, match="side"):
        _candidate("bad-side", side="maybe")
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        rank_strategy_recommendation_cost_adjusted_quorum_v2(
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
        replace(report, ranked_rows=(object(),), report_digest=None)
    with pytest.raises(ValueError, match="config"):
        rank_strategy_recommendation_cost_adjusted_quorum_v2((_candidate("alpha"),), config=object())
    with pytest.raises(ValueError, match="Decimal"):
        _config(minimum_recommendation_score_bps=50)


def test_cost_adjusted_quorum_ranker_module_scope_stays_report_only():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_recommendation_cost_adjusted_quorum_ranker_v2.py"
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
        "cancel_order",
        "execute_trade",
        "live_trading",
        "database",
        "db.",
        "open(",
    )
    assert all(fragment not in source for fragment in forbidden_fragments)

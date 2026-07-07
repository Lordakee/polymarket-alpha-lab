from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
import re

import pytest

from polymarket_alpha_lab.strategy_recommendation_abstain_reason_ranker_v2 import (
    StrategyRecommendationAbstainReasonRankerV2Config,
    StrategyRecommendationAbstainReasonRankerV2Input,
    StrategyRecommendationAbstainReasonRankerV2RankedReason,
    StrategyRecommendationAbstainReasonRankerV2Report,
    rank_strategy_recommendation_abstain_reasons_v2,
    strategy_recommendation_abstain_reason_ranker_v2_payload,
)


DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> StrategyRecommendationAbstainReasonRankerV2Config:
    values: dict[str, object] = {
        "config_version": "strategy-recommendation-abstain-reason-ranker-v2",
        "minimum_edge_after_cost_bps": d("50.000000"),
        "edge_shortfall_weight_bps": d("1.000000"),
        "stale_source_weight_bps": d("80.000000"),
        "weak_evidence_quorum_weight_bps": d("100.000000"),
        "contradiction_severity_weight_bps": d("100.000000"),
        "resolution_ambiguity_weight_bps": d("100.000000"),
        "liquidity_risk_weight_bps": d("100.000000"),
        "category_budget_pressure_weight_bps": d("100.000000"),
        "stale_source_reason_threshold": d("0.250000"),
        "evidence_quorum_floor": d("0.700000"),
        "contradiction_severity_reason_threshold": d("0.250000"),
        "resolution_ambiguity_reason_threshold": d("0.250000"),
        "liquidity_risk_reason_threshold": d("0.250000"),
        "category_budget_pressure_reason_threshold": d("0.250000"),
    }
    values.update(overrides)
    return StrategyRecommendationAbstainReasonRankerV2Config(**values)


def _decision(
    recommendation_id: str,
    *,
    market_slug: str | None = None,
    selected_side: str = "yes",
    decision_status: str = "abstain",
    edge_after_cost_bps: Decimal = d("10.000000"),
    source_staleness_score: Decimal = d("0.800000"),
    evidence_quorum_score: Decimal = d("0.400000"),
    contradiction_severity_score: Decimal = d("0.900000"),
    resolution_ambiguity_score: Decimal = d("0.300000"),
    liquidity_risk_score: Decimal = d("0.600000"),
    category_budget_pressure_score: Decimal = d("0.500000"),
) -> StrategyRecommendationAbstainReasonRankerV2Input:
    return StrategyRecommendationAbstainReasonRankerV2Input(
        recommendation_id=recommendation_id,
        market_slug=market_slug or f"{recommendation_id}-market",
        selected_side=selected_side,
        decision_status=decision_status,
        edge_after_cost_bps=edge_after_cost_bps,
        source_staleness_score=source_staleness_score,
        evidence_quorum_score=evidence_quorum_score,
        contradiction_severity_score=contradiction_severity_score,
        resolution_ambiguity_score=resolution_ambiguity_score,
        liquidity_risk_score=liquidity_risk_score,
        category_budget_pressure_score=category_budget_pressure_score,
    )


def test_abstain_reason_ranker_scores_ranks_and_digests_deterministically() -> None:
    decisions = (
        _decision("alpha"),
        _decision(
            "beta",
            decision_status="manual_review",
            edge_after_cost_bps=d("55.000000"),
            source_staleness_score=d("0.100000"),
            evidence_quorum_score=d("0.900000"),
            contradiction_severity_score=d("0.250000"),
            resolution_ambiguity_score=d("0.000000"),
            liquidity_risk_score=d("0.250000"),
            category_budget_pressure_score=d("0.800000"),
        ),
    )

    report = rank_strategy_recommendation_abstain_reasons_v2(
        decisions,
        config=_config(),
    )
    repeat_report = rank_strategy_recommendation_abstain_reasons_v2(
        tuple(reversed(decisions)),
        config=_config(),
    )

    assert report == repeat_report
    assert isinstance(report, StrategyRecommendationAbstainReasonRankerV2Report)
    assert report.decision_count == d("2")
    assert report.ranked_reason_count == d("10")
    assert report.top_reason_code == "contradiction_severity"
    assert report.reason_codes == (
        "insufficient_edge_after_cost",
        "stale_sources",
        "weak_evidence_quorum",
        "contradiction_severity",
        "resolution_ambiguity",
        "liquidity_risk",
        "category_budget_pressure",
    )
    assert DIGEST_PATTERN.match(report.report_digest)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.reason_code for row in report.ranked_reasons) == (
        "contradiction_severity",
        "category_budget_pressure",
        "stale_sources",
        "liquidity_risk",
        "category_budget_pressure",
        "insufficient_edge_after_cost",
        "weak_evidence_quorum",
        "resolution_ambiguity",
        "contradiction_severity",
        "liquidity_risk",
    )
    assert tuple(row.recommendation_id for row in report.ranked_reasons[:5]) == (
        "alpha",
        "beta",
        "alpha",
        "alpha",
        "alpha",
    )
    assert tuple(row.reason_rank for row in report.ranked_reasons[:5]) == (
        d("1"),
        d("2"),
        d("3"),
        d("4"),
        d("5"),
    )

    top = report.ranked_reasons[0]
    assert isinstance(top, StrategyRecommendationAbstainReasonRankerV2RankedReason)
    assert top.recommendation_id == "alpha"
    assert top.decision_status == "abstain"
    assert top.reason_code == "contradiction_severity"
    assert top.reason_score_bps == d("90.000000")
    assert top.factor_value == d("0.900000")
    assert top.threshold_value == d("0.250000")
    assert DIGEST_PATTERN.match(top.reason_digest)
    assert top.paper_only is True
    assert top.report_only is True
    assert top.readonly is True

    edge = report.ranked_reasons[5]
    assert edge.reason_code == "insufficient_edge_after_cost"
    assert edge.reason_score_bps == d("40.000000")
    assert edge.factor_value == d("40.000000")
    assert edge.threshold_value == d("50.000000")

    payload = report.payload
    assert payload == strategy_recommendation_abstain_reason_ranker_v2_payload(report)
    assert payload["decision_count"] == "2"
    assert payload["ranked_reason_count"] == "10"
    assert payload["ranked_reasons"][0]["reason_rank"] == "1"
    assert payload["ranked_reasons"][0]["reason_score_bps"] == "90.000000"
    assert payload["ranked_reasons"][0]["reason_digest"] == top.reason_digest
    assert payload["report_digest"] == report.report_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_abstain_reason_ranker_returns_no_rankable_reason_for_clean_review() -> None:
    report = rank_strategy_recommendation_abstain_reasons_v2(
        (
            _decision(
                "clean",
                decision_status="manual_review",
                edge_after_cost_bps=d("80.000000"),
                source_staleness_score=d("0.000000"),
                evidence_quorum_score=d("0.900000"),
                contradiction_severity_score=d("0.000000"),
                resolution_ambiguity_score=d("0.000000"),
                liquidity_risk_score=d("0.000000"),
                category_budget_pressure_score=d("0.000000"),
            ),
        ),
        config=_config(),
    )

    assert report.decision_count == d("1")
    assert report.ranked_reason_count == d("1")
    assert report.top_reason_code == "no_rankable_abstain_reason"
    assert report.reason_codes == ("no_rankable_abstain_reason",)
    assert report.ranked_reasons[0].reason_code == "no_rankable_abstain_reason"
    assert report.ranked_reasons[0].reason_score_bps == d("0.000000")
    assert report.ranked_reasons[0].factor_value == d("0.000000")
    assert report.ranked_reasons[0].threshold_value == d("0.000000")


def test_abstain_reason_ranker_tie_breakers_ignore_source_order() -> None:
    first = _decision(
        "reason-b",
        edge_after_cost_bps=d("50.000000"),
        source_staleness_score=d("0.000000"),
        evidence_quorum_score=d("1.000000"),
        contradiction_severity_score=d("0.000000"),
        resolution_ambiguity_score=d("0.000000"),
        liquidity_risk_score=d("0.400000"),
        category_budget_pressure_score=d("0.000000"),
    )
    second = replace(first, recommendation_id="reason-a", market_slug="reason-a-market")

    forward = rank_strategy_recommendation_abstain_reasons_v2(
        (first, second),
        config=_config(),
    )
    reverse = rank_strategy_recommendation_abstain_reasons_v2(
        (second, first),
        config=_config(),
    )

    assert forward == reverse
    assert tuple(row.recommendation_id for row in forward.ranked_reasons) == (
        "reason-a",
        "reason-b",
    )
    assert tuple(row.reason_rank for row in forward.ranked_reasons) == (d("1"), d("2"))


def test_abstain_reason_ranker_validates_decimals_flags_and_consistency() -> None:
    report = rank_strategy_recommendation_abstain_reasons_v2(
        (_decision("alpha"), _decision("beta")),
        config=_config(),
    )

    with pytest.raises(FrozenInstanceError):
        report.top_reason_code = "liquidity_risk"
    with pytest.raises(FrozenInstanceError):
        report.ranked_reasons[0].reason_score_bps = d("0.000000")
    with pytest.raises(ValueError, match="edge_after_cost_bps"):
        _decision("int-edge", edge_after_cost_bps=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_staleness_score"):
        _decision("float-stale", source_staleness_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_risk_score"):
        _decision("bad-risk", liquidity_risk_score=d("1.000001"))
    with pytest.raises(ValueError, match="decision_status"):
        _decision("bad-status", decision_status="recommend")
    with pytest.raises(ValueError, match="paper_only"):
        replace(_decision("flag"), paper_only=False)
    with pytest.raises(ValueError, match="duplicate recommendation_id"):
        rank_strategy_recommendation_abstain_reasons_v2(
            (_decision("dup"), _decision("dup")),
            config=_config(),
        )
    with pytest.raises(ValueError, match="config"):
        rank_strategy_recommendation_abstain_reasons_v2(
            (_decision("alpha"),),
            config=object(),
        )
    with pytest.raises(ValueError, match="Decimal"):
        _config(minimum_edge_after_cost_bps=50)

    bad_digest = "sha256:" + ("0" * 64)
    with pytest.raises(ValueError, match="reason_digest"):
        replace(report.ranked_reasons[0], reason_digest=bad_digest)
    with pytest.raises(ValueError, match="report_digest"):
        replace(report, report_digest=bad_digest)

    misranked_rows = (
        replace(report.ranked_reasons[1], reason_rank=d("1"), reason_digest=None),
        replace(report.ranked_reasons[0], reason_rank=d("2"), reason_digest=None),
        *report.ranked_reasons[2:],
    )
    with pytest.raises(ValueError, match="deterministic ranking"):
        replace(report, ranked_reasons=misranked_rows, report_digest=None)
    with pytest.raises(ValueError, match="decision_count"):
        replace(report, decision_count=d("1"), report_digest=None)
    with pytest.raises(ValueError, match="ranked_reasons"):
        replace(report, ranked_reasons=(object(),), report_digest=None)


def test_abstain_reason_ranker_empty_input_is_paper_only_report() -> None:
    report = rank_strategy_recommendation_abstain_reasons_v2((), config=_config())

    assert report.decision_count == d("0")
    assert report.ranked_reason_count == d("0")
    assert report.top_reason_code is None
    assert report.reason_codes == ("no_abstain_decisions",)
    assert report.ranked_reasons == ()
    assert DIGEST_PATTERN.match(report.report_digest)
    assert report.payload["ranked_reasons"] == []


def test_abstain_reason_ranker_module_scope_stays_readonly() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_recommendation_abstain_reason_ranker_v2.py"
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
        ".write(",
        ".connect(",
        ".execute(",
    )
    assert all(fragment not in source for fragment in forbidden_fragments)

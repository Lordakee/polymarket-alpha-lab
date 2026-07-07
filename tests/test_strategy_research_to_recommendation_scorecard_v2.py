from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_research_to_recommendation_scorecard_v2 import (
    StrategyResearchToRecommendationScorecardV2Config,
    StrategyResearchToRecommendationScorecardV2Input,
    StrategyResearchToRecommendationScorecardV2ReasonCodeCount,
    StrategyResearchToRecommendationScorecardV2Report,
    StrategyResearchToRecommendationScorecardV2Row,
    build_strategy_research_to_recommendation_scorecard_v2_report,
    strategy_research_to_recommendation_scorecard_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> StrategyResearchToRecommendationScorecardV2Config:
    values = {
        "config_version": "strategy-research-to-recommendation-scorecard-v2",
        "minimum_promote_score": d("0.800000"),
        "maximum_block_score": d("0.250000"),
        "minimum_research_packet_quality": d("0.600000"),
        "minimum_source_crosscheck_readiness": d("0.600000"),
        "minimum_rule_clarity": d("0.600000"),
        "minimum_information_freshness": d("0.600000"),
        "minimum_specialist_quorum": d("0.600000"),
        "minimum_cost_adjusted_edge": d("0.020000"),
        "block_cost_adjusted_edge": d("0.000000"),
        "target_promote_cost_adjusted_edge": d("0.050000"),
        "minimum_exit_feasibility": d("0.600000"),
        "block_exit_feasibility": d("0.250000"),
    }
    values.update(overrides)
    return StrategyResearchToRecommendationScorecardV2Config(**values)


def candidate(
    candidate_id: str = "candidate-alpha",
    *,
    research_packet_quality: Decimal = d("0.900000"),
    source_crosscheck_readiness: Decimal = d("0.880000"),
    rule_clarity: Decimal = d("0.860000"),
    information_freshness: Decimal = d("0.920000"),
    specialist_quorum: Decimal = d("0.820000"),
    cost_adjusted_edge: Decimal = d("0.070000"),
    exit_feasibility: Decimal = d("0.850000"),
    reason_codes: tuple[str, ...] = ("research_packet_complete",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyResearchToRecommendationScorecardV2Input:
    return StrategyResearchToRecommendationScorecardV2Input(
        candidate_id=candidate_id,
        research_packet_quality=research_packet_quality,
        source_crosscheck_readiness=source_crosscheck_readiness,
        rule_clarity=rule_clarity,
        information_freshness=information_freshness,
        specialist_quorum=specialist_quorum,
        cost_adjusted_edge=cost_adjusted_edge,
        exit_feasibility=exit_feasibility,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: StrategyResearchToRecommendationScorecardV2Input,
    cfg: StrategyResearchToRecommendationScorecardV2Config | None = None,
) -> StrategyResearchToRecommendationScorecardV2Report:
    return build_strategy_research_to_recommendation_scorecard_v2_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_promote_scorecard_payload_is_decimal_string_readonly_and_digest_checked() -> None:
    scorecard = report(candidate())

    assert is_dataclass(scorecard)
    assert scorecard.overall_posture == "promote"
    assert scorecard.candidate_count == d("1.000000")
    assert scorecard.promote_count == d("1.000000")
    assert scorecard.watch_count == ZERO
    assert scorecard.block_count == ZERO
    assert scorecard.research_needed_count == ZERO
    assert scorecard.average_score == d("0.890000")
    assert scorecard.reason_codes == ("scorecard_promote_ready",)
    assert scorecard.paper_only is True
    assert scorecard.report_only is True
    assert scorecard.readonly is True
    assert len(scorecard.derived_validation_digest) == 64

    row = scorecard.scorecard_rows[0]
    assert is_dataclass(row)
    assert row.posture == "promote"
    assert row.score == d("0.890000")
    assert row.cost_adjusted_edge_score == d("1.000000")
    assert row.reason_codes == (
        "research_packet_complete",
        "scorecard_promote_ready",
    )
    assert len(row.derived_validation_digest) == 64

    payload = strategy_research_to_recommendation_scorecard_v2_payload(scorecard)
    assert payload["candidate_count"] == "1.000000"
    assert payload["average_score"] == "0.890000"
    assert payload["scorecard_rows"][0]["score"] == "0.890000"
    assert payload["scorecard_rows"][0]["cost_adjusted_edge"] == "0.070000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_scorecard_distinguishes_research_needed_watch_and_block_postures() -> None:
    scorecard = report(
        candidate(
            "needs-research",
            research_packet_quality=d("0.550000"),
            source_crosscheck_readiness=d("0.500000"),
            information_freshness=d("0.580000"),
        ),
        candidate(
            "watch-edge",
            cost_adjusted_edge=d("0.010000"),
            exit_feasibility=d("0.580000"),
        ),
        candidate(
            "block-exit",
            cost_adjusted_edge=d("-0.010000"),
            exit_feasibility=d("0.200000"),
        ),
    )

    assert scorecard.overall_posture == "block"
    assert scorecard.block_count == d("1.000000")
    assert scorecard.research_needed_count == d("1.000000")
    assert scorecard.watch_count == d("1.000000")
    assert scorecard.promote_count == ZERO
    assert tuple(row.candidate_id for row in scorecard.scorecard_rows) == (
        "block-exit",
        "needs-research",
        "watch-edge",
    )

    rows_by_id = {row.candidate_id: row for row in scorecard.scorecard_rows}
    assert rows_by_id["block-exit"].posture == "block"
    assert rows_by_id["block-exit"].reason_codes == (
        "research_packet_complete",
        "scorecard_cost_adjusted_edge_block",
        "scorecard_exit_feasibility_block",
    )
    assert rows_by_id["needs-research"].posture == "research-needed"
    assert rows_by_id["needs-research"].reason_codes == (
        "research_packet_complete",
        "scorecard_information_freshness_research_needed",
        "scorecard_research_packet_quality_research_needed",
        "scorecard_source_crosscheck_readiness_research_needed",
    )
    assert rows_by_id["watch-edge"].posture == "watch"
    assert rows_by_id["watch-edge"].reason_codes == (
        "research_packet_complete",
        "scorecard_cost_adjusted_edge_watch",
        "scorecard_composite_watch",
        "scorecard_exit_feasibility_watch",
    )
    assert scorecard.reason_codes == (
        "scorecard_block",
        "scorecard_cost_adjusted_edge_block",
        "scorecard_cost_adjusted_edge_watch",
        "scorecard_exit_feasibility_block",
        "scorecard_exit_feasibility_watch",
        "scorecard_information_freshness_research_needed",
        "scorecard_research_packet_quality_research_needed",
        "scorecard_source_crosscheck_readiness_research_needed",
    )
    assert scorecard.reason_code_counts == (
        StrategyResearchToRecommendationScorecardV2ReasonCodeCount(
            reason_code="research_packet_complete",
            count=d("3.000000"),
        ),
        StrategyResearchToRecommendationScorecardV2ReasonCodeCount(
            reason_code="scorecard_composite_watch",
            count=d("1.000000"),
        ),
        StrategyResearchToRecommendationScorecardV2ReasonCodeCount(
            reason_code="scorecard_cost_adjusted_edge_block",
            count=d("1.000000"),
        ),
        StrategyResearchToRecommendationScorecardV2ReasonCodeCount(
            reason_code="scorecard_cost_adjusted_edge_watch",
            count=d("1.000000"),
        ),
        StrategyResearchToRecommendationScorecardV2ReasonCodeCount(
            reason_code="scorecard_exit_feasibility_block",
            count=d("1.000000"),
        ),
        StrategyResearchToRecommendationScorecardV2ReasonCodeCount(
            reason_code="scorecard_exit_feasibility_watch",
            count=d("1.000000"),
        ),
        StrategyResearchToRecommendationScorecardV2ReasonCodeCount(
            reason_code="scorecard_information_freshness_research_needed",
            count=d("1.000000"),
        ),
        StrategyResearchToRecommendationScorecardV2ReasonCodeCount(
            reason_code="scorecard_research_packet_quality_research_needed",
            count=d("1.000000"),
        ),
        StrategyResearchToRecommendationScorecardV2ReasonCodeCount(
            reason_code="scorecard_source_crosscheck_readiness_research_needed",
            count=d("1.000000"),
        ),
    )


def test_empty_scorecard_is_research_needed_and_decimal_zeroed() -> None:
    scorecard = report()

    assert scorecard.overall_posture == "research-needed"
    assert scorecard.reason_codes == ("scorecard_no_candidates_research_needed",)
    assert scorecard.candidate_count == ZERO
    assert scorecard.average_score == ZERO
    assert scorecard.max_score == ZERO
    assert scorecard.min_score == ZERO
    assert scorecard.scorecard_rows == ()
    assert scorecard.paper_only is True
    assert scorecard.report_only is True
    assert scorecard.readonly is True


def test_frozen_dataclasses_decimal_only_flags_and_consistency_validation() -> None:
    scorecard = report(candidate("consistent"))

    assert is_dataclass(StrategyResearchToRecommendationScorecardV2Config)
    assert is_dataclass(StrategyResearchToRecommendationScorecardV2Input)
    assert is_dataclass(StrategyResearchToRecommendationScorecardV2Row)
    assert is_dataclass(StrategyResearchToRecommendationScorecardV2ReasonCodeCount)
    assert is_dataclass(StrategyResearchToRecommendationScorecardV2Report)
    with pytest.raises(FrozenInstanceError):
        scorecard.overall_posture = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        scorecard.scorecard_rows[0].score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(scorecard, readonly=False)
    with pytest.raises(ValueError, match="candidate_count"):
        replace(scorecard, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="overall_posture"):
        replace(scorecard, overall_posture="block")

    for item in (scorecard, *scorecard.scorecard_rows, *scorecard.reason_code_counts):
        for field_name, value in item.__dict__.items():
            if field_name in {
                "paper_only",
                "report_only",
                "readonly",
                "derived_validation_digest",
            }:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field_name
            assert type(value) is not float, field_name

    with pytest.raises(ValueError, match="minimum_promote_score"):
        config(minimum_promote_score=d("-0.000001"))
    with pytest.raises(ValueError, match="maximum_block_score"):
        config(maximum_block_score=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(candidate_id=" candidate")
    with pytest.raises(ValueError, match="research_packet_quality"):
        candidate(research_packet_quality=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_adjusted_edge"):
        candidate(cost_adjusted_edge=d("-1.000001"))
    with pytest.raises(ValueError, match="exit_feasibility"):
        candidate(exit_feasibility=d("1.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=("duplicate", "duplicate"))


def test_derived_validation_digest_rejects_dataclass_and_payload_tampering() -> None:
    scorecard = report(candidate("tamper-check"))
    payload = strategy_research_to_recommendation_scorecard_v2_payload(scorecard)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(scorecard, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(scorecard.scorecard_rows[0], score=d("0.100000"))

    tampered_report = dict(payload)
    tampered_report["average_score"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_research_to_recommendation_scorecard_v2_payload(tampered_report)

    tampered_row = dict(payload)
    tampered_row["scorecard_rows"] = [dict(payload["scorecard_rows"][0])]
    tampered_row["scorecard_rows"][0]["posture"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_research_to_recommendation_scorecard_v2_payload(tampered_row)


def test_public_payload_rejects_unsafe_keys_values_and_flag_downgrades() -> None:
    scorecard = report(candidate("public-safe"))
    payload = strategy_research_to_recommendation_scorecard_v2_payload(scorecard)

    for unsafe_key in (
        "live_mode",
        "auth_token",
        "wallet_ref",
        "order_id",
        "network_path",
        "database_row",
        "persisted_ref",
        "signing_hint",
        "mutation_route",
        "buy_button",
        "sell_button",
        "trade_route",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "blocked"
        with pytest.raises(ValueError, match="unsafe"):
            strategy_research_to_recommendation_scorecard_v2_payload(unsafe_payload)

    for unsafe_value in (
        "live cycle",
        "auth secret",
        "wallet value",
        "order ready",
        "network call",
        "database path",
        "persist this",
        "signing needed",
        "mutation enabled",
        "buy now",
        "sell now",
        "trade now",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload["summary"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe"):
            strategy_research_to_recommendation_scorecard_v2_payload(unsafe_payload)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        strategy_research_to_recommendation_scorecard_v2_payload(downgraded)

    with pytest.raises(ValueError, match="unsafe"):
        candidate(candidate_id="trade-candidate")
    with pytest.raises(ValueError, match="unsafe"):
        candidate(reason_codes=("research_packet_complete", "wallet_seen"))


def test_static_module_surface_has_no_external_io_or_float_literals() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_research_to_recommendation_scorecard_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests.",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "subprocess",
        "open(",
        "path(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False

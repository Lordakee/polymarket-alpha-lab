from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_recommendation_review_backlog_prioritizer_v2 import (
    StrategyRecommendationReviewBacklogPrioritizerV2Config,
    StrategyRecommendationReviewBacklogPrioritizerV2Input,
    StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount,
    StrategyRecommendationReviewBacklogPrioritizerV2Report,
    StrategyRecommendationReviewBacklogPrioritizerV2Row,
    build_strategy_recommendation_review_backlog_prioritizer_v2_report,
    strategy_recommendation_review_backlog_prioritizer_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> StrategyRecommendationReviewBacklogPrioritizerV2Config:
    values = {
        "config_version": "strategy-recommendation-review-backlog-prioritizer-v2",
        "minimum_source_verified_edge": d("0.030000"),
        "stale_research_ready_age_seconds": d("7200.000000"),
        "market_probability_movement_watch": d("0.040000"),
        "uncertainty_band_width_watch": d("0.120000"),
        "liquidity_exit_risk_watch": d("0.500000"),
        "liquidity_exit_risk_block": d("0.850000"),
        "portfolio_impact_watch": d("0.100000"),
        "portfolio_impact_block": d("0.250000"),
        "resolution_ambiguity_watch": d("0.400000"),
        "resolution_ambiguity_block": d("0.800000"),
        "minimum_specialist_confidence": d("0.600000"),
        "source_verified_edge_weight": d("3.000000"),
        "stale_research_readiness_weight": d("1.500000"),
        "market_probability_movement_weight": d("2.000000"),
        "uncertainty_band_width_weight": d("1.250000"),
        "liquidity_exit_risk_weight": d("2.250000"),
        "portfolio_impact_weight": d("1.750000"),
        "resolution_ambiguity_weight": d("2.500000"),
        "specialist_confidence_weight": d("1.000000"),
    }
    values.update(overrides)
    return StrategyRecommendationReviewBacklogPrioritizerV2Config(**values)


def candidate(
    recommendation_id: str = "candidate-alpha",
    *,
    source_verified_edge: Decimal = d("0.060000"),
    research_observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    market_probability_movement: Decimal = d("0.020000"),
    uncertainty_low_probability: Decimal = d("0.420000"),
    uncertainty_high_probability: Decimal = d("0.500000"),
    liquidity_exit_risk: Decimal = d("0.200000"),
    portfolio_impact: Decimal = d("0.050000"),
    resolution_ambiguity: Decimal = d("0.200000"),
    specialist_confidence: Decimal = d("0.850000"),
    reason_codes: tuple[str, ...] = ("review_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyRecommendationReviewBacklogPrioritizerV2Input:
    return StrategyRecommendationReviewBacklogPrioritizerV2Input(
        recommendation_id=recommendation_id,
        source_verified_edge=source_verified_edge,
        research_observed_at=research_observed_at,
        market_probability_movement=market_probability_movement,
        uncertainty_low_probability=uncertainty_low_probability,
        uncertainty_high_probability=uncertainty_high_probability,
        liquidity_exit_risk=liquidity_exit_risk,
        portfolio_impact=portfolio_impact,
        resolution_ambiguity=resolution_ambiguity,
        specialist_confidence=specialist_confidence,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: StrategyRecommendationReviewBacklogPrioritizerV2Input,
    cfg: StrategyRecommendationReviewBacklogPrioritizerV2Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyRecommendationReviewBacklogPrioritizerV2Report:
    return build_strategy_recommendation_review_backlog_prioritizer_v2_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_happy_path_prioritizes_review_backlog_and_serializes_decimal_strings() -> None:
    digest = report(
        candidate(
            "candidate-alpha",
            source_verified_edge=d("0.090000"),
            market_probability_movement=d("0.050000"),
            uncertainty_low_probability=d("0.370000"),
            uncertainty_high_probability=d("0.520000"),
            liquidity_exit_risk=d("0.600000"),
            portfolio_impact=d("0.130000"),
            resolution_ambiguity=d("0.450000"),
            specialist_confidence=d("0.550000"),
            research_observed_at=GENERATED_AT - timedelta(hours=3),
            reason_codes=("manual_review_requested", "review_input_available"),
        ),
        candidate(
            "candidate-beta",
            source_verified_edge=d("0.035000"),
            market_probability_movement=d("0.010000"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.candidate_count == d("2.000000")
    assert digest.review_now_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == ZERO
    assert digest.status == "watch"
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert len(digest.derived_validation_digest) == 64

    first = digest.priority_rows[0]
    assert first.recommendation_id == "candidate-alpha"
    assert first.priority_rank == d("1.000000")
    assert first.review_status == "watch"
    assert first.research_age_seconds == d("10800.000000")
    assert first.stale_research_readiness == d("1.000000")
    assert first.uncertainty_band_width == d("0.150000")
    assert first.specialist_confidence_deficit == d("0.050000")
    assert first.reason_codes == (
        "liquidity_exit_risk_watch",
        "manual_review_requested",
        "market_probability_movement_watch",
        "portfolio_impact_watch",
        "resolution_ambiguity_watch",
        "review_input_available",
        "specialist_confidence_low_watch",
        "stale_research_ready_watch",
        "uncertainty_band_width_watch",
    )
    assert first.priority_score == d("15.250000")
    assert digest.priority_rows[1].review_status == "review_now"
    assert digest.reason_code_counts == (
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code="review_input_available",
            count=d("2.000000"),
        ),
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code="liquidity_exit_risk_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code="manual_review_requested",
            count=d("1.000000"),
        ),
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code="market_probability_movement_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code="portfolio_impact_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code="resolution_ambiguity_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code="review_backlog_ready",
            count=d("1.000000"),
        ),
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code="specialist_confidence_low_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code="stale_research_ready_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code="uncertainty_band_width_watch",
            count=d("1.000000"),
        ),
    )

    payload = strategy_recommendation_review_backlog_prioritizer_v2_payload(digest)
    assert payload["candidate_count"] == "2.000000"
    assert payload["priority_rows"][0]["priority_score"] == "15.250000"
    assert payload["priority_rows"][0]["source_verified_edge"] == "0.090000"
    assert payload["priority_rows"][0]["research_observed_at"] == (
        GENERATED_AT - timedelta(hours=3)
    ).isoformat()
    assert payload["derived_validation_digest"] == digest.derived_validation_digest
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_blocking_risks_sort_first_and_emit_distinct_reason_codes() -> None:
    digest = report(
        candidate(
            "candidate-watch",
            source_verified_edge=d("0.010000"),
            specialist_confidence=d("0.400000"),
        ),
        candidate(
            "candidate-blocked",
            source_verified_edge=d("-0.010000"),
            liquidity_exit_risk=d("0.900000"),
            portfolio_impact=d("0.300000"),
            resolution_ambiguity=d("0.850000"),
        ),
        candidate("candidate-ready", source_verified_edge=d("0.050000")),
    )

    assert digest.status == "blocked"
    assert digest.blocked_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert tuple(row.recommendation_id for row in digest.priority_rows) == (
        "candidate-blocked",
        "candidate-watch",
        "candidate-ready",
    )
    assert digest.priority_rows[0].reason_codes == (
        "liquidity_exit_risk_blocked",
        "portfolio_impact_blocked",
        "resolution_ambiguity_blocked",
        "review_input_available",
        "source_verified_edge_negative_blocked",
    )
    assert digest.reason_codes == (
        "review_backlog_blocked",
        "liquidity_exit_risk_blocked",
        "portfolio_impact_blocked",
        "resolution_ambiguity_blocked",
        "source_verified_edge_below_minimum_watch",
        "source_verified_edge_negative_blocked",
        "specialist_confidence_low_watch",
    )


def test_utc_normalization_for_generated_and_research_times() -> None:
    digest = report(
        candidate(
            research_observed_at=datetime(
                2026,
                7,
                6,
                7,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            6,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert digest.generated_at == GENERATED_AT
    assert digest.priority_rows[0].research_observed_at == datetime(
        2026,
        7,
        6,
        11,
        30,
        tzinfo=UTC,
    )
    assert digest.priority_rows[0].research_age_seconds == d("1800.000000")


def test_frozen_dataclasses_hard_flags_and_decimal_only_public_numbers() -> None:
    digest = report(candidate("frozen"))

    assert is_dataclass(StrategyRecommendationReviewBacklogPrioritizerV2Config)
    assert is_dataclass(StrategyRecommendationReviewBacklogPrioritizerV2Input)
    assert is_dataclass(StrategyRecommendationReviewBacklogPrioritizerV2Row)
    assert is_dataclass(StrategyRecommendationReviewBacklogPrioritizerV2Report)
    with pytest.raises(FrozenInstanceError):
        digest.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.priority_rows[0].priority_score = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)

    for item in (digest, *digest.priority_rows, *digest.reason_code_counts):
        for field_name, value in item.__dict__.items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field_name
            assert type(value) is not float, field_name
    for field_name in (
        "candidate_count",
        "review_now_count",
        "watch_count",
        "blocked_count",
        "max_priority_score",
        "min_priority_score",
        "average_priority_score",
    ):
        assert isinstance(getattr(digest, field_name), Decimal)


def test_validation_errors_cover_inputs_config_payload_and_digest_tampering() -> None:
    with pytest.raises(ValueError, match="minimum_source_verified_edge"):
        config(minimum_source_verified_edge=d("-0.000001"))
    with pytest.raises(ValueError, match="source_verified_edge_weight"):
        config(source_verified_edge_weight=d("0.000000"))
    with pytest.raises(ValueError, match="liquidity_exit_risk_watch"):
        config(liquidity_exit_risk_watch=d("0.900000"))
    with pytest.raises(ValueError, match="minimum_specialist_confidence"):
        config(minimum_specialist_confidence=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="recommendation_id"):
        candidate(recommendation_id=" candidate")
    with pytest.raises(ValueError, match="source_verified_edge"):
        candidate(source_verified_edge=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_probability_movement"):
        candidate(market_probability_movement=d("1.000001"))
    with pytest.raises(ValueError, match="uncertainty"):
        candidate(
            uncertainty_low_probability=d("0.600000"),
            uncertainty_high_probability=d("0.500000"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("aware-research"),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_observed_at"):
        report(candidate(research_observed_at=GENERATED_AT + timedelta(seconds=1)))

    digest = report(candidate("consistent"))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(digest, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(digest, status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest, derived_validation_digest="0" * 64)

    payload = strategy_recommendation_review_backlog_prioritizer_v2_payload(digest)
    tampered = {
        **payload,
        "priority_rows": [
            {
                **payload["priority_rows"][0],
                "priority_score": "9.000000",
            },
        ],
    }
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_recommendation_review_backlog_prioritizer_v2_payload(tampered)

    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_review_backlog_prioritizer_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                "wa" + "llet_field": "blocked",
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_review_backlog_prioritizer_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                "summary": "please " + "sell" + " this",
            },
        )
    with pytest.raises(ValueError, match="readonly"):
        strategy_recommendation_review_backlog_prioritizer_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                "priority_rows": [
                    {
                        "paper_only": True,
                        "report_only": True,
                        "readonly": False,
                    },
                ],
            },
        )


def test_static_module_surface_has_no_imports_or_calls_for_external_side_effects() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_recommendation_review_backlog_prioritizer_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite",
        "open(",
        "subprocess",
        "pathlib",
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

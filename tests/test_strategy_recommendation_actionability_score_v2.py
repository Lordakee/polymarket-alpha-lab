from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

import polymarket_alpha_lab.strategy_recommendation_actionability_score_v2 as score_module
from polymarket_alpha_lab.strategy_recommendation_actionability_score_v2 import (
    StrategyRecommendationActionabilityScoreV2Config,
    StrategyRecommendationActionabilityScoreV2Recommendation,
    StrategyRecommendationActionabilityScoreV2Report,
    build_strategy_recommendation_actionability_score_v2_report,
    strategy_recommendation_actionability_score_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
CONFIG = StrategyRecommendationActionabilityScoreV2Config(
    config_version="strategy-recommendation-actionability-score-v2-phase1",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _MissingOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    def dst(self, dt: datetime | None) -> timedelta | None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _recommendation(
    *,
    recommendation_id: str = "rec-001",
    market_slug: str = "market-alpha",
    source_verified_edge: Decimal = d("0.900000"),
    expected_value_consistency: Decimal = d("0.800000"),
    research_readiness: Decimal = d("0.700000"),
    uncertainty_band_width: Decimal = d("0.100000"),
    liquidity_exit_risk: Decimal = d("0.200000"),
    resolution_ambiguity: Decimal = d("0.100000"),
    portfolio_impact: Decimal = d("0.600000"),
    specialist_confidence: Decimal = d("0.850000"),
    market_probability_move_recheck_status: str = "confirmed",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyRecommendationActionabilityScoreV2Recommendation:
    return StrategyRecommendationActionabilityScoreV2Recommendation(
        recommendation_id=recommendation_id,
        market_slug=market_slug,
        source_verified_edge=source_verified_edge,
        expected_value_consistency=expected_value_consistency,
        research_readiness=research_readiness,
        uncertainty_band_width=uncertainty_band_width,
        liquidity_exit_risk=liquidity_exit_risk,
        resolution_ambiguity=resolution_ambiguity,
        portfolio_impact=portfolio_impact,
        specialist_confidence=specialist_confidence,
        market_probability_move_recheck_status=market_probability_move_recheck_status,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    recommendation: StrategyRecommendationActionabilityScoreV2Recommendation | None = None,
    *,
    config: StrategyRecommendationActionabilityScoreV2Config = CONFIG,
    generated_at: datetime = GENERATED_AT,
) -> StrategyRecommendationActionabilityScoreV2Report:
    return build_strategy_recommendation_actionability_score_v2_report(
        recommendation if recommendation is not None else _recommendation(),
        config=config,
        generated_at=generated_at,
    )


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for key, item in value.items():
            values.append(key)
            values.extend(_walk_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return tuple(values)
    return (value,)


def test_score_v2_builds_decimal_report_payload_and_digest() -> None:
    report = _report(
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "strategy-recommendation-actionability-score-v2-phase1"
    assert report.recommendation_id == "rec-001"
    assert report.market_slug == "market-alpha"
    assert report.source_verified_edge == d("0.900000")
    assert report.expected_value_consistency == d("0.800000")
    assert report.research_readiness == d("0.700000")
    assert report.uncertainty_band_width == d("0.100000")
    assert report.liquidity_exit_risk == d("0.200000")
    assert report.resolution_ambiguity == d("0.100000")
    assert report.portfolio_impact == d("0.600000")
    assert report.specialist_confidence == d("0.850000")
    assert report.market_probability_move_recheck_status == "confirmed"
    assert report.market_probability_move_recheck_score == d("1.000000")
    assert report.actionability_score == d("0.829500")
    assert report.actionability_status == "actionable"
    assert report.reason_codes == (
        "actionability_score_ready",
        "market_probability_move_recheck_confirmed",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.derived_validation_digest == report.derived_validation_digest.lower()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = strategy_recommendation_actionability_score_v2_payload(report)
    values = _walk_values(payload)

    assert payload["source_verified_edge"] == "0.900000"
    assert payload["uncertainty_band_width"] == "0.100000"
    assert payload["market_probability_move_recheck_score"] == "1.000000"
    assert payload["actionability_score"] == "0.829500"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (Decimal, datetime, float, int) for value in values)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_score_v2_recheck_and_risk_dimensions_gate_status() -> None:
    stale_report = _report(
        _recommendation(market_probability_move_recheck_status="stale"),
    )
    assert stale_report.market_probability_move_recheck_score == d("0.250000")
    assert stale_report.actionability_score == d("0.769500")
    assert stale_report.actionability_status == "watch"
    assert "market_probability_move_recheck_stale" in stale_report.reason_codes

    blocked_report = _report(
        _recommendation(
            source_verified_edge=d("0.300000"),
            expected_value_consistency=d("0.400000"),
            research_readiness=d("0.450000"),
            uncertainty_band_width=d("0.500000"),
            liquidity_exit_risk=d("0.600000"),
            resolution_ambiguity=d("0.700000"),
            portfolio_impact=d("0.350000"),
            specialist_confidence=d("0.250000"),
            market_probability_move_recheck_status="adverse_move",
        ),
    )
    assert blocked_report.market_probability_move_recheck_score == d("0.000000")
    assert blocked_report.actionability_score == d("0.344500")
    assert blocked_report.actionability_status == "blocked"
    assert blocked_report.reason_codes == (
        "expected_value_consistency_below_floor",
        "liquidity_exit_risk_elevated",
        "market_probability_move_recheck_adverse_move",
        "portfolio_impact_below_floor",
        "research_readiness_below_floor",
        "resolution_ambiguity_elevated",
        "source_verified_edge_below_floor",
        "specialist_confidence_below_floor",
        "uncertainty_band_too_wide",
    )


def test_score_v2_rejects_invalid_inputs_and_report_inconsistency() -> None:
    with pytest.raises(ValueError, match="source_verified_edge"):
        _recommendation(source_verified_edge=d("-0.000001"))
    with pytest.raises(ValueError, match="source_verified_edge"):
        _recommendation(source_verified_edge=d("1.000001"))
    with pytest.raises(ValueError, match="source_verified_edge"):
        _recommendation(source_verified_edge=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_verified_edge"):
        _recommendation(source_verified_edge=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_verified_edge"):
        _recommendation(source_verified_edge=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="market_probability_move_recheck_status"):
        _recommendation(market_probability_move_recheck_status="unknown")
    with pytest.raises(ValueError, match="paper_only"):
        _recommendation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _recommendation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _recommendation(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_strategy_recommendation_actionability_score_v2_report(
            _recommendation(),
            config="bad",  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(generated_at=datetime(2026, 7, 6))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        _report(generated_at=datetime(2026, 7, 6, tzinfo=_MissingOffsetTZ()))
    with pytest.raises(ValueError, match="generated_at"):
        _report(generated_at=_DatetimeSubclass(2026, 7, 6, tzinfo=UTC))

    report = _report()
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, actionability_score=d("0.100000"))
    with pytest.raises(ValueError, match="actionability_status"):
        replace(
            report,
            actionability_status="blocked",
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="market_probability_move_recheck_score"):
        replace(
            report,
            market_probability_move_recheck_score=d("0.250000"),
            derived_validation_digest="",
        )


def test_score_v2_payload_revalidates_digest_flags_and_public_safety() -> None:
    report = _report()
    object.__setattr__(report, "actionability_score", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_recommendation_actionability_score_v2_payload(report)

    flag_tampered = _report()
    object.__setattr__(flag_tampered, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        strategy_recommendation_actionability_score_v2_payload(flag_tampered)

    value_tampered = _report()
    object.__setattr__(value_tampered, "reason_codes", ("net" + "work" + "_seen",))
    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_actionability_score_v2_payload(value_tampered)

    with pytest.raises(ValueError, match="unsafe"):
        score_module._payload_value({"li" + "ve": "safe"})
    with pytest.raises(ValueError, match="unsafe"):
        score_module._payload_value({"safe_key": "wall" + "et"})

    unsafe_market = "au" + "th" + "_leak"
    with pytest.raises(ValueError, match="unsafe") as market_error:
        _recommendation(market_slug=unsafe_market)
    assert unsafe_market not in str(market_error.value)


def test_score_v2_public_dataclasses_are_frozen() -> None:
    recommendation = _recommendation()
    report = _report(recommendation)

    with pytest.raises(FrozenInstanceError):
        recommendation.source_verified_edge = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.actionability_score = d("0.100000")  # type: ignore[misc]


def test_score_v2_module_stays_readonly_report_only_scope() -> None:
    source = inspect.getsource(score_module)
    lowered_source = source.lower()
    forbidden_markers = (
        "li" + "ve",
        "au" + "th",
        "wall" + "et",
        "ord" + "er",
        "net" + "work",
        "data" + "base",
        "per" + "sist",
        "sig" + "ning",
        "mut" + "ation",
        "bu" + "y",
        "se" + "ll",
        "tra" + "de",
    )

    assert all(marker not in lowered_source for marker in forbidden_markers)

    tree = ast.parse(source)
    imports = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imports.isdisjoint(
        {
            "asyncio",
            "httpx",
            "pathlib",
            "pickle",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "supabase",
            "urllib",
        },
    )

    forbidden_name_calls = {"eval", "exec", "open", "compile", "__import__"}
    forbidden_attribute_calls = {
        "connect",
        "execute",
        "post",
        "put",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_name_calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_attribute_calls

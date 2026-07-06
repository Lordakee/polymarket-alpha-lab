from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_recommendation_evidence_weighted_rank_v2"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/strategy_recommendation_evidence_weighted_rank_v2.py",
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_WEIGHTED_RANK_V2_CONFIG_VERSION
        ),
        "evidence_weight": d("0.350000"),
        "source_quality_weight": d("0.200000"),
        "weak_evidence_penalty_weight": d("0.250000"),
        "min_evidence_strength_score": d("0.600000"),
        "min_source_quality_score": d("0.650000"),
        "min_independent_source_count": d("2"),
        "max_weak_evidence_ratio": d("0.250000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationEvidenceWeightedRankV2Config(**values)


def candidate(recommendation_id: str = "rec-alpha", **overrides: object) -> Any:
    module = api()
    values = {
        "recommendation_id": recommendation_id,
        "market_slug": "btc-above-100k",
        "selected_side": "yes",
        "model_probability": d("0.650000"),
        "market_probability": d("0.600000"),
        "expected_edge": d("0.050000"),
        "evidence_strength_score": d("0.800000"),
        "source_quality_score": d("0.900000"),
        "independent_source_count": d("3"),
        "weak_evidence_count": d("0"),
        "source_reference": "official-source-alpha",
        "rationale_summary": "public evidence supports paper review",
    }
    values.update(overrides)
    return module.StrategyRecommendationEvidenceWeightedRankV2Input(**values)


def report(*rows: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_strategy_recommendation_evidence_weighted_rank_v2(
        rows,
        config=cfg or config(),
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for child in value.values():
            items.extend(walk(child))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(walk(child))
        return tuple(items)
    return (value,)


def assert_no_json_numbers(value: object) -> None:
    assert type(value) is not float
    assert not (type(value) is int and type(value) is not bool)
    if isinstance(value, dict):
        for item in value.values():
            assert_no_json_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_json_numbers(item)


def test_evidence_weighted_ranking_prioritizes_stronger_supported_candidate() -> None:
    result = report(
        candidate(
            "rec-weak",
            market_slug="eth-above-5k",
            model_probability=d("0.700000"),
            market_probability=d("0.620000"),
            expected_edge=d("0.080000"),
            evidence_strength_score=d("0.500000"),
            source_quality_score=d("0.500000"),
            independent_source_count=d("2"),
            weak_evidence_count=d("2"),
            source_reference="thin-source-beta",
            rationale_summary="thin support requires paper review",
        ),
        candidate("rec-strong"),
    )

    assert is_dataclass(result)
    assert result.recommendation_count == d("2")
    assert result.top_recommendation_id == "rec-strong"
    assert tuple(row.recommendation_id for row in result.ranked_recommendations) == (
        "rec-strong",
        "rec-weak",
    )
    assert result.ranked_recommendations[0].evidence_weighted_rank_score == d("0.510000")
    assert result.ranked_recommendations[1].evidence_weighted_rank_score == d("0.105000")
    assert result.ranked_recommendations[0].recommendation_rank == d("1")
    assert result.ranked_recommendations[1].recommendation_rank == d("2")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_weak_evidence_penalty_blocks_high_raw_edge_candidate() -> None:
    result = report(
        candidate(
            "rec-weak",
            model_probability=d("0.730000"),
            market_probability=d("0.600000"),
            expected_edge=d("0.130000"),
            weak_evidence_count=d("2"),
            independent_source_count=d("2"),
        ),
    )
    row = result.ranked_recommendations[0]

    assert row.weak_evidence_ratio == d("1.000000")
    assert row.evidence_weighted_rank_score == d("0.340000")
    assert row.paper_status == "blocked"
    assert row.recommended_next_step == "drop_from_paper_review"
    assert (
        "strategy_recommendation_evidence_weighted_rank_v2_weak_evidence_penalty"
        in row.reason_codes
    )


def test_source_quality_boost_lifts_otherwise_equal_candidate() -> None:
    result = report(
        candidate(
            "rec-low-source",
            source_quality_score=d("0.500000"),
            source_reference="public-source-low",
            rationale_summary="lower quality source set",
        ),
        candidate("rec-high-source"),
    )

    high, low = result.ranked_recommendations
    assert high.recommendation_id == "rec-high-source"
    assert high.evidence_weighted_rank_score - low.evidence_weighted_rank_score == d(
        "0.080000",
    )
    assert (
        "strategy_recommendation_evidence_weighted_rank_v2_source_quality_boost"
        in high.reason_codes
    )
    assert low.paper_status == "watch"


def test_serialization_decimal_strings_digest_and_json_ready_payload() -> None:
    module = api()
    result = report(candidate("rec-strong"))
    payload = module.strategy_recommendation_evidence_weighted_rank_v2_payload(result)

    assert result.payload == payload
    assert payload["recommendation_count"] == "1"
    assert payload["ranked_recommendations"][0]["model_probability"] == "0.650000"
    assert payload["ranked_recommendations"][0]["recommendation_rank"] == "1"
    assert len(payload["derived_validation_digest"]) == 64
    assert len(payload["ranked_recommendations"][0]["derived_validation_digest"]) == 64
    assert_no_json_numbers(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert module.strategy_recommendation_evidence_weighted_rank_v2_payload(payload) == payload


def test_public_dataclasses_are_frozen_and_public_numbers_are_decimal_only() -> None:
    module = api()
    values = (config(), candidate(), report(candidate()))
    numeric_field_names = {
        "evidence_weight",
        "source_quality_weight",
        "weak_evidence_penalty_weight",
        "min_evidence_strength_score",
        "min_source_quality_score",
        "min_independent_source_count",
        "max_weak_evidence_ratio",
        "model_probability",
        "market_probability",
        "expected_edge",
        "evidence_strength_score",
        "source_quality_score",
        "independent_source_count",
        "weak_evidence_count",
        "weak_evidence_ratio",
        "evidence_weighted_rank_score",
        "recommendation_rank",
        "recommendation_count",
    }

    assert module.__all__ == (
        "DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_WEIGHTED_RANK_V2_CONFIG_VERSION",
        "StrategyRecommendationEvidenceWeightedRankV2Config",
        "StrategyRecommendationEvidenceWeightedRankV2Input",
        "StrategyRecommendationEvidenceWeightedRankV2Row",
        "StrategyRecommendationEvidenceWeightedRankV2Report",
        "build_strategy_recommendation_evidence_weighted_rank_v2",
        "strategy_recommendation_evidence_weighted_rank_v2_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]
        for field in fields(value):
            if field.name in numeric_field_names:
                assert type(getattr(value, field.name)) is Decimal

    for dataclass_type in (
        module.StrategyRecommendationEvidenceWeightedRankV2Config,
        module.StrategyRecommendationEvidenceWeightedRankV2Input,
        module.StrategyRecommendationEvidenceWeightedRankV2Row,
        module.StrategyRecommendationEvidenceWeightedRankV2Report,
    ):
        hints = get_type_hints(dataclass_type)
        for field in fields(dataclass_type):
            if field.name in numeric_field_names:
                assert hints[field.name] is Decimal


def test_hard_flags_and_payload_flag_validation() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        candidate(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        report(candidate(readonly=False))

    payload = report(candidate()).payload
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_recommendation_evidence_weighted_rank_v2_payload(
            {**payload, "readonly": False},
        )


def test_derived_validation_digest_rejects_row_report_and_payload_tampering() -> None:
    module = api()
    result = report(candidate())
    row = result.ranked_recommendations[0]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, evidence_weighted_rank_score=d("0.520000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    payload = result.payload
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_recommendation_evidence_weighted_rank_v2_payload(
            {**payload, "top_recommendation_id": "rec-other"},
        )
    row_payload = payload["ranked_recommendations"][0]
    tampered_rows = [{**row_payload, "evidence_weighted_rank_score": "0.520000"}]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_recommendation_evidence_weighted_rank_v2_payload(
            {**payload, "ranked_recommendations": tampered_rows},
        )


def test_unsafe_public_key_and_value_rejection() -> None:
    module = api()

    for unsafe in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        with pytest.raises(ValueError, match="unsafe public content"):
            candidate(rationale_summary=f"contains {unsafe} term")
        with pytest.raises(ValueError, match="unsafe public content"):
            module.strategy_recommendation_evidence_weighted_rank_v2_payload(
                {**report(candidate()).payload, unsafe: "blocked"},
            )

    with pytest.raises(ValueError, match="exactly Decimal"):
        candidate(model_probability=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="Decimal"):
        candidate(model_probability=0.65)
    with pytest.raises(ValueError, match="nonblank trimmed string"):
        candidate(recommendation_id=_StringSubclass("rec-alpha"))


def test_no_unsafe_surfaces_or_public_numeric_literals_in_module_source() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live trading",
        "wallet",
        "auth",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
        "private_key",
        "account",
        "broker",
        "place_order",
        "submit_order",
        "http",
        "requests",
        "socket",
        "subprocess",
        "open(",
        "psycopg",
        "sqlite",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    banned_imports = {
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_call_names = {
        "__import__",
        "connect",
        "eval",
        "exec",
        "float",
        "open",
        "print",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            assert not ({alias.name.split(".", 1)[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in banned_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names


def test_payload_rejects_json_numbers_and_preserves_hard_flags() -> None:
    module = api()
    payload = report(candidate()).payload
    row_payload = payload["ranked_recommendations"][0]

    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_recommendation_evidence_weighted_rank_v2_payload(
            {**payload, "recommendation_count": 1},
        )
    with pytest.raises(ValueError, match="float"):
        module.strategy_recommendation_evidence_weighted_rank_v2_payload(
            {
                **payload,
                "ranked_recommendations": [
                    {**row_payload, "evidence_weighted_rank_score": 0.51},
                ],
            },
        )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert row_payload["paper_only"] is True
    assert row_payload["report_only"] is True
    assert row_payload["readonly"] is True

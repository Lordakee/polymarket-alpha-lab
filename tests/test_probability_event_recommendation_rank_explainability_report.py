from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_recommendation_rank_explainability_report as module


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_recommendation_rank_explainability_report.py",
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> module.ProbabilityEventRecommendationRankExplainabilityReport:
    values = {
        "edge_score_probability": d("0.220000"),
        "confidence_score_probability": d("0.820000"),
        "source_quality_probability": d("0.900000"),
        "cost_penalty_probability": d("0.050000"),
        "risk_penalty_probability": d("0.070000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.build_probability_event_recommendation_rank_explainability_report(**values)


def walk_payload_values(value: Any) -> tuple[object, ...]:
    if type(value) is dict:
        return tuple(item for child in value.values() for item in walk_payload_values(child))
    if type(value) is list:
        return tuple(item for child in value for item in walk_payload_values(child))
    return (value,)


def assert_no_runtime_numbers_or_unsafe_terms(value: Any) -> None:
    if type(value) is int or type(value) is float or type(value) is Decimal:
        pytest.fail(f"payload contains runtime numeric value: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for forbidden in (
                "live",
                "auth",
                "wallet",
                "key",
                "sign",
                "order",
                "network",
                "database",
                "persist",
                "execute",
                "trade",
                "buy",
                "sell",
            ):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers_or_unsafe_terms(item)
    if isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers_or_unsafe_terms(item)


def test_rank_explainability_report_recommends_manual_candidate_and_serializes_payload() -> None:
    ranked = report()

    assert isinstance(ranked, module.ProbabilityEventRecommendationRankExplainabilityReport)
    assert ranked.recommendation_status == "recommend"
    assert ranked.rank_explainability_score == d("0.306000")
    assert ranked.reason_codes == ("edge_positive", "confidence_high", "source_quality_high")
    assert ranked.manual_next_step == "manual_review_candidate"
    assert ranked.paper_only is True
    assert ranked.report_only is True
    assert ranked.readonly is True
    assert len(ranked.payload_digest) == 64
    assert all(character in "0123456789abcdef" for character in ranked.payload_digest)

    payload = module.probability_event_recommendation_rank_explainability_report_payload(ranked)
    assert payload == ranked.public_payload
    assert payload["recommendation_status"] == "recommend"
    assert payload["rank_explainability_score"] == "0.306000"
    assert payload["edge_score_probability"] == "0.220000"
    assert payload["confidence_score_probability"] == "0.820000"
    assert payload["source_quality_probability"] == "0.900000"
    assert payload["cost_penalty_probability"] == "0.050000"
    assert payload["risk_penalty_probability"] == "0.070000"
    assert payload["reason_codes"] == [
        "edge_positive",
        "confidence_high",
        "source_quality_high",
    ]
    assert payload["manual_next_step"] == "manual_review_candidate"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == ranked.payload_digest
    assert_no_runtime_numbers_or_unsafe_terms(payload)
    json.dumps(payload, sort_keys=True)


def test_watch_status_explains_penalties_and_low_signal_without_execution_path() -> None:
    ranked = report(
        edge_score_probability=d("0.090000"),
        confidence_score_probability=d("0.560000"),
        source_quality_probability=d("0.580000"),
        cost_penalty_probability=d("0.210000"),
        risk_penalty_probability=d("0.270000"),
    )

    assert ranked.recommendation_status == "watch"
    assert ranked.rank_explainability_score == ZERO
    assert ranked.reason_codes == (
        "edge_below_review_threshold",
        "confidence_below_review_threshold",
        "source_quality_below_review_threshold",
        "cost_penalty_high",
        "risk_penalty_high",
    )
    assert ranked.manual_next_step == "manual_research_update"


def test_reject_status_blocks_negative_or_unsafe_manual_ranking_candidate() -> None:
    ranked = report(
        edge_score_probability=d("0.000000"),
        confidence_score_probability=d("0.900000"),
        source_quality_probability=d("0.900000"),
        cost_penalty_probability=d("0.900000"),
        risk_penalty_probability=d("0.900000"),
    )

    assert ranked.recommendation_status == "reject"
    assert ranked.rank_explainability_score == ZERO
    assert ranked.reason_codes == (
        "edge_below_review_threshold",
        "cost_penalty_extreme",
        "risk_penalty_extreme",
    )
    assert ranked.manual_next_step == "manual_reject_candidate"


def test_payload_digest_rejects_tampering_and_public_payload_validation() -> None:
    ranked = report()
    with pytest.raises(ValueError, match="payload_digest"):
        replace(ranked, payload_digest="0" * 64)

    tampered_report = report()
    object.__setattr__(tampered_report, "rank_explainability_score", d("0.000001"))
    with pytest.raises(ValueError, match="payload_digest"):
        module.probability_event_recommendation_rank_explainability_report_payload(
            tampered_report,
        )

    payload = ranked.public_payload
    tampered_payload = dict(payload)
    tampered_payload["rank_explainability_score"] = "0.000001"
    with pytest.raises(ValueError, match="payload_digest"):
        module.validate_probability_event_recommendation_rank_explainability_public_payload(
            tampered_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["wallet_field"] = "safe_value"
    with pytest.raises(ValueError, match="unsafe public"):
        module.validate_probability_event_recommendation_rank_explainability_public_payload(
            unsafe_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["manual_next_step"] = "manual_trade_candidate"
    with pytest.raises(ValueError, match="unsafe public"):
        module.validate_probability_event_recommendation_rank_explainability_public_payload(
            unsafe_value_payload,
        )


def test_frozen_dataclass_decimal_only_flags_and_consistency_validation() -> None:
    ranked = report()

    assert is_dataclass(module.ProbabilityEventRecommendationRankExplainabilityReport)
    assert ranked.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        ranked.recommendation_status = "watch"  # type: ignore[misc]

    decimal_fields = {
        "edge_score_probability",
        "confidence_score_probability",
        "source_quality_probability",
        "cost_penalty_probability",
        "risk_penalty_probability",
        "rank_explainability_score",
    }
    for field in fields(ranked):
        value = getattr(ranked, field.name)
        if field.name in decimal_fields:
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(ranked, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(ranked, readonly=False)
    with pytest.raises(ValueError, match="edge_score_probability"):
        report(edge_score_probability=0.22)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence_score_probability"):
        report(confidence_score_probability="0.820000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_quality_probability"):
        report(source_quality_probability=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="recommendation_status"):
        replace(ranked, recommendation_status="execute")
    with pytest.raises(ValueError, match="rank_explainability_score"):
        replace(ranked, rank_explainability_score=d("0.500000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(ranked, reason_codes=("confidence_high",))
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(ranked, manual_next_step="manual_trade_candidate")


def test_module_is_readonly_report_only_and_has_no_persistence_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "auth",
        "wallet",
        "private_key",
        "secret",
        "signature",
        "signing",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "execute(",
        "urlopen",
        "connect(",
        "write_text",
        "open(",
        "jsonl",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imports = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not (imports & {"os", "socket", "subprocess", "requests", "urllib"})
    assert not (imported_from & {"pathlib", "sqlite3"})

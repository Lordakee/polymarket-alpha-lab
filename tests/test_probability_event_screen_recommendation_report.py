from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_screen_recommendation_report as api
from polymarket_alpha_lab.probability_event_screen_recommendation_report import (
    ProbabilityEventScreenRecommendationInput,
    ProbabilityEventScreenRecommendationReport,
    build_probability_event_screen_recommendation_report,
    probability_event_screen_recommendation_report_digest,
    probability_event_screen_recommendation_report_to_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_recommendation_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def screen_input(
    *,
    screen_status: str = "ready_for_manual_review",
    edge_to_threshold_probability: Decimal = d("0.040000"),
    source_quality_status: str = "ready",
    team_route_confidence: Decimal = ONE,
    memory_context_ready: Decimal = ONE,
    position_sizing_risk_band: str = "low",
    preflight_ready: Decimal = ONE,
    operator_safety_ready: Decimal = ONE,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenRecommendationInput:
    return ProbabilityEventScreenRecommendationInput(
        screen_status=screen_status,
        edge_to_threshold_probability=edge_to_threshold_probability,
        source_quality_status=source_quality_status,
        team_route_confidence=team_route_confidence,
        memory_context_ready=memory_context_ready,
        position_sizing_risk_band=position_sizing_risk_band,
        preflight_ready=preflight_ready,
        operator_safety_ready=operator_safety_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    screen: ProbabilityEventScreenRecommendationInput,
) -> ProbabilityEventScreenRecommendationReport:
    return build_probability_event_screen_recommendation_report(screen)


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_ready_screen_builds_manual_review_report_payload_and_digest() -> None:
    recommendation = report(screen_input())

    assert is_dataclass(recommendation)
    assert recommendation.recommendation_band == "ready_for_manual_review"
    assert recommendation.primary_reason_codes == (
        "probability_event_screen_ready_for_manual_review",
    )
    assert recommendation.blocker_count == ZERO
    assert recommendation.attention_count == ZERO
    assert recommendation.ready_component_ratio == ONE
    assert recommendation.paper_only is True
    assert recommendation.report_only is True
    assert recommendation.readonly is True

    payload = probability_event_screen_recommendation_report_to_payload(recommendation)
    assert recommendation.public_payload == payload
    assert payload == {
        "screen_status": "ready_for_manual_review",
        "edge_to_threshold_probability": "0.040000",
        "source_quality_status": "ready",
        "team_route_confidence": "1.000000",
        "memory_context_ready": "1.000000",
        "position_sizing_risk_band": "low",
        "preflight_ready": "1.000000",
        "operator_safety_ready": "1.000000",
        "recommendation_band": "ready_for_manual_review",
        "primary_reason_codes": [
            "probability_event_screen_ready_for_manual_review",
        ],
        "blocker_count": "0.000000",
        "attention_count": "0.000000",
        "ready_component_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert recommendation.digest == expected_digest
    assert probability_event_screen_recommendation_report_digest(recommendation) == (
        expected_digest
    )
    assert_no_int_or_float_values(payload)


def test_blocker_recommendation_explains_all_block_and_watch_components() -> None:
    recommendation = report(
        screen_input(
            screen_status="block",
            edge_to_threshold_probability=d("-0.010000"),
            source_quality_status="block",
            team_route_confidence=ZERO,
            memory_context_ready=d("0.500000"),
            position_sizing_risk_band="high",
            preflight_ready=ZERO,
            operator_safety_ready=d("0.750000"),
        ),
    )

    assert recommendation.recommendation_band == "block"
    assert recommendation.blocker_count == d("6.000000")
    assert recommendation.attention_count == d("2.000000")
    assert recommendation.ready_component_ratio == ZERO
    assert recommendation.primary_reason_codes == (
        "probability_event_screen_status_block",
        "probability_event_edge_below_threshold_block",
        "probability_event_source_quality_block",
        "probability_event_team_route_confidence_block",
        "probability_event_position_sizing_risk_block",
        "probability_event_preflight_block",
        "probability_event_memory_context_watch",
        "probability_event_operator_safety_watch",
    )

    payload = recommendation.public_payload
    assert payload["recommendation_band"] == "block"
    assert payload["blocker_count"] == "6.000000"
    assert payload["attention_count"] == "2.000000"
    assert payload["ready_component_ratio"] == "0.000000"
    assert_no_int_or_float_values(payload)


def test_watch_recommendation_has_no_blockers_and_partial_ready_ratio() -> None:
    recommendation = report(
        screen_input(
            screen_status="watch",
            edge_to_threshold_probability=ZERO,
            source_quality_status="watch",
            team_route_confidence=d("0.500000"),
            position_sizing_risk_band="medium",
        ),
    )

    assert recommendation.recommendation_band == "watch"
    assert recommendation.blocker_count == ZERO
    assert recommendation.attention_count == d("5.000000")
    assert recommendation.ready_component_ratio == d("0.375000")
    assert recommendation.primary_reason_codes == (
        "probability_event_screen_status_watch",
        "probability_event_edge_at_threshold_watch",
        "probability_event_source_quality_watch",
        "probability_event_team_route_confidence_watch",
        "probability_event_position_sizing_risk_watch",
    )


def test_dataclasses_are_frozen_decimal_only_and_flags_are_enforced() -> None:
    recommendation = report(screen_input())

    with pytest.raises(FrozenInstanceError):
        recommendation.recommendation_band = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenRecommendationInput):
            pass

    with pytest.raises(ValueError, match="edge_to_threshold_probability must be a Decimal"):
        screen_input(edge_to_threshold_probability=0.01)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="team_route_confidence must be a Decimal"):
        screen_input(team_route_confidence=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="screen_status must be canonical lowercase text"):
        screen_input(screen_status="WATCH")

    with pytest.raises(ValueError, match="paper_only"):
        screen_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        screen_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(recommendation, readonly=False)


def test_public_api_stays_leaf_readonly_report_only_and_side_effect_free() -> None:
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "database",
        "network",
        "request",
        "http",
        "broker",
        "private_key",
        "api_key",
        "order_execution",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ProbabilityEventScreenRecommendationInput,
        ProbabilityEventScreenRecommendationReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr.lower())

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "supabase",
            "web3",
            "ccxt",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "execute_order",
            "place_order",
            "sign_order",
            "submit_order",
            "insert",
            "update",
            "delete",
        },
    )

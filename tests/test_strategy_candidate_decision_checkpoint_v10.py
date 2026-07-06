from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.strategy_candidate_decision_checkpoint_v10",
    )


def checkpoint_input(**overrides: Any):
    values: dict[str, Any] = {
        "market_id": "market-alpha",
        "recommendation_status": "recommend",
        "decision_readiness": d("0.910000"),
        "data_gap_status": "none",
        "risk_register_status": "clear",
        "portfolio_fit_status": "fit",
        "human_review_required": False,
        "time_to_resolution_minutes": d("1440.000000"),
    }
    values.update(overrides)
    return api().StrategyCandidateDecisionCheckpointV10Input(**values)


def build(subject: object | None = None):
    return api().build_strategy_candidate_decision_checkpoint_v10(
        checkpoint_input() if subject is None else subject,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_approved_checkpoint_routes_candidate_to_paper_approval_payload() -> None:
    module = api()

    result = build()

    assert result == module.StrategyCandidateDecisionCheckpointV10Result(
        market_id="market-alpha",
        recommendation_status="recommend",
        decision_readiness=d("0.910000"),
        data_gap_status="none",
        risk_register_status="clear",
        portfolio_fit_status="fit",
        human_review_required=False,
        time_to_resolution_minutes=d("1440.000000"),
        checkpoint_status="approved",
        approval_path="paper_approval_ready",
        blocking_reasons=(),
        reason_codes=(
            "recommendation_recommend",
            "decision_readiness_ready",
            "data_gap_none",
            "risk_register_clear",
            "portfolio_fit",
            "human_review_not_required",
            "resolution_window_sufficient",
            "checkpoint_approved",
        ),
    )
    assert type(result.decision_readiness) is Decimal
    assert type(result.time_to_resolution_minutes) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload == module.strategy_candidate_decision_checkpoint_v10_payload(result)
    assert payload["checkpoint_status"] == "approved"
    assert payload["approval_path"] == "paper_approval_ready"
    assert payload["decision_readiness"] == "0.910000"
    assert payload["time_to_resolution_minutes"] == "1440.000000"
    assert payload["blocking_reasons"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_review_required_checkpoint_collects_manual_decision_reasons() -> None:
    result = build(
        checkpoint_input(
            market_id="market-review",
            recommendation_status="review",
            decision_readiness=d("0.660000"),
            data_gap_status="material",
            risk_register_status="watch",
            portfolio_fit_status="watch",
            human_review_required=True,
            time_to_resolution_minutes=d("45.000000"),
        ),
    )

    assert result.checkpoint_status == "review_required"
    assert result.approval_path == "manual_review"
    assert result.blocking_reasons == (
        "Recommendation status review requires human decision.",
        "Raise decision readiness to at least 0.700000.",
        "Resolve material data gaps before approval.",
        "Review risk register status watch.",
        "Portfolio fit status watch requires review.",
        "Human review is explicitly required.",
        "Only 45.000000 minutes remain to resolution.",
    )
    assert result.reason_codes == (
        "recommendation_review",
        "decision_readiness_watch",
        "data_gap_material",
        "risk_register_watch",
        "portfolio_fit_watch",
        "human_review_required",
        "near_resolution",
        "checkpoint_review_required",
    )
    assert result.payload["blocking_reasons"] == list(result.blocking_reasons)


def test_blocked_checkpoint_surfaces_hard_blocking_reasons() -> None:
    result = build(
        checkpoint_input(
            market_id="market-blocked",
            recommendation_status="blocked",
            decision_readiness=d("0.420000"),
            data_gap_status="blocking",
            risk_register_status="blocking",
            portfolio_fit_status="blocked",
            human_review_required=True,
            time_to_resolution_minutes=d("10.000000"),
        ),
    )

    assert result.checkpoint_status == "blocked"
    assert result.approval_path == "blocked"
    assert result.blocking_reasons == (
        "Recommendation status blocked prevents approval.",
        "Decision readiness below 0.500000 blocks checkpoint approval.",
        "Blocking data gaps must be resolved.",
        "Risk register status blocking prevents approval.",
        "Portfolio fit status blocked prevents approval.",
        "Human review is explicitly required.",
        "Only 10.000000 minutes remain to resolution.",
    )
    assert result.reason_codes == (
        "recommendation_blocked",
        "decision_readiness_blocked",
        "data_gap_blocking",
        "risk_register_blocking",
        "portfolio_fit_blocked",
        "human_review_required",
        "resolution_window_blocking",
        "checkpoint_blocked",
    )


def test_checkpoint_validates_decimal_types_choices_bool_flags_and_freezing() -> None:
    subject = checkpoint_input()
    result = build(subject)

    with pytest.raises(FrozenInstanceError):
        subject.market_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.checkpoint_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="decision_readiness must be a Decimal"):
        checkpoint_input(decision_readiness=0.91)
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be a Decimal"):
        checkpoint_input(time_to_resolution_minutes=1440)
    with pytest.raises(ValueError, match="recommendation_status must be one of"):
        checkpoint_input(recommendation_status="approve")
    with pytest.raises(ValueError, match="data_gap_status must be one of"):
        checkpoint_input(data_gap_status="unknown")
    with pytest.raises(ValueError, match="risk_register_status must be one of"):
        checkpoint_input(risk_register_status="unknown")
    with pytest.raises(ValueError, match="portfolio_fit_status must be one of"):
        checkpoint_input(portfolio_fit_status="unknown")
    with pytest.raises(ValueError, match="human_review_required must be a bool"):
        checkpoint_input(human_review_required="yes")
    with pytest.raises(ValueError, match="paper_only must be True"):
        checkpoint_input(paper_only=False)
    with pytest.raises(ValueError, match="candidate"):
        build(object())


def test_checkpoint_module_is_report_readonly_and_unwired_from_io_execution() -> None:
    module = api()
    source = inspect.getsource(module)
    lowered = source.lower()

    assert module.StrategyCandidateDecisionCheckpointV10Input.__dataclass_params__.frozen
    assert module.StrategyCandidateDecisionCheckpointV10Result.__dataclass_params__.frozen
    assert module.__all__ == (
        "CHECKPOINT_STATUSES",
        "APPROVAL_PATHS",
        "RECOMMENDATION_STATUSES",
        "DATA_GAP_STATUSES",
        "RISK_REGISTER_STATUSES",
        "PORTFOLIO_FIT_STATUSES",
        "REASON_CODES",
        "StrategyCandidateDecisionCheckpointV10Input",
        "StrategyCandidateDecisionCheckpointV10Result",
        "build_strategy_candidate_decision_checkpoint_v10",
        "strategy_candidate_decision_checkpoint_v10_payload",
    )

    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "clob",
        "wallet",
        "private_key",
        "signing",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    assert all(fragment not in source for fragment in forbidden_fragments)

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
    assert "database" not in lowered

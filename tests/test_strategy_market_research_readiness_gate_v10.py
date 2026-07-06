from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_market_research_readiness_gate_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def gate_input(**overrides: object):
    gate = api()
    values = {
        "information_edge_score": d("0.820000"),
        "source_quorum_status": "pass",
        "forecast_rationale_status": "pass",
        "liquidity_guard_status": "pass",
        "resolution_precedent_score": d("0.760000"),
        "team_capacity_score": d("0.740000"),
        "human_review_required": False,
    }
    values.update(overrides)
    return gate.MarketResearchReadinessGateV10Input(**values)


def evaluate(**overrides: object):
    gate = api()
    return gate.evaluate_market_research_readiness_gate_v10(gate_input(**overrides))


def test_readiness_gate_passes_and_returns_json_ready_payload() -> None:
    gate = api()

    report = evaluate()
    payload = gate.strategy_market_research_readiness_gate_v10_payload(report)

    assert is_dataclass(report)
    assert report.readiness_status == "ready"
    assert report.research_depth_level == "deep_research"
    assert report.blocking_reasons == ()
    assert report.reason_codes == ("market_research_ready", "deep_research_candidate")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.payload == payload

    assert payload == {
        "information_edge_score": "0.820000",
        "source_quorum_status": "pass",
        "forecast_rationale_status": "pass",
        "liquidity_guard_status": "pass",
        "resolution_precedent_score": "0.760000",
        "team_capacity_score": "0.740000",
        "human_review_required": False,
        "readiness_status": "ready",
        "research_depth_level": "deep_research",
        "blocking_reasons": [],
        "reason_codes": ["market_research_ready", "deep_research_candidate"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    def assert_no_float(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float(item)
        else:
            assert type(value) is not float

    assert_no_float(payload)


def test_readiness_gate_blocks_on_hard_prerequisites_in_priority_order() -> None:
    report = evaluate(
        information_edge_score=d("0.810000"),
        source_quorum_status="blocked",
        forecast_rationale_status="blocked",
        liquidity_guard_status="blocked",
        resolution_precedent_score=d("0.690000"),
        team_capacity_score=d("0.790000"),
        human_review_required=False,
    )

    assert report.readiness_status == "blocked"
    assert report.research_depth_level == "do_not_research"
    assert report.blocking_reasons == (
        "source_quorum_blocked",
        "forecast_rationale_blocked",
        "liquidity_guard_blocked",
        "resolution_precedent_below_floor",
    )
    assert report.reason_codes == (
        "source_quorum_blocked",
        "forecast_rationale_blocked",
        "liquidity_guard_blocked",
        "resolution_precedent_below_floor",
    )


def test_readiness_gate_escalates_human_review_and_watch_depths() -> None:
    manual_review = evaluate(
        information_edge_score=d("0.780000"),
        source_quorum_status="pass",
        forecast_rationale_status="watch",
        liquidity_guard_status="pass",
        resolution_precedent_score=d("0.700000"),
        team_capacity_score=d("0.710000"),
        human_review_required=True,
    )
    light_watch = evaluate(
        information_edge_score=d("0.640000"),
        source_quorum_status="pass",
        forecast_rationale_status="pass",
        liquidity_guard_status="watch",
        resolution_precedent_score=d("0.690000"),
        team_capacity_score=d("0.680000"),
        human_review_required=False,
    )

    assert manual_review.readiness_status == "needs_human_review"
    assert manual_review.research_depth_level == "standard_research"
    assert manual_review.blocking_reasons == ()
    assert manual_review.reason_codes == (
        "forecast_rationale_watch",
        "human_review_required",
        "standard_research_candidate",
    )

    assert light_watch.readiness_status == "watch"
    assert light_watch.research_depth_level == "light_research"
    assert light_watch.reason_codes == (
        "liquidity_guard_watch",
        "resolution_precedent_watch",
        "team_capacity_watch",
        "light_research_candidate",
    )


def test_readiness_gate_validates_decimal_inputs_statuses_and_flags() -> None:
    gate = api()
    report = evaluate()

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(FrozenInstanceError):
        report.readiness_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="information_edge_score must be a Decimal"):
        gate_input(information_edge_score=0.82)
    with pytest.raises(ValueError, match="information_edge_score"):
        gate_input(information_edge_score=DecimalSubclass("0.820000"))
    with pytest.raises(ValueError, match="team_capacity_score must be between zero and one"):
        gate_input(team_capacity_score=d("1.100000"))
    with pytest.raises(ValueError, match="source_quorum_status"):
        gate_input(source_quorum_status="ready")
    with pytest.raises(ValueError, match="human_review_required must be a bool"):
        gate_input(human_review_required=1)
    with pytest.raises(ValueError, match="paper_only"):
        gate_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="payload"):
        replace(report, payload={})


def test_payload_rejects_float_downgraded_flags_and_live_surface() -> None:
    gate = api()

    with pytest.raises(ValueError, match="payload readonly must be True"):
        gate.strategy_market_research_readiness_gate_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        gate.strategy_market_research_readiness_gate_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "information_edge_score": 0.82,
            },
        )

    with pytest.raises(ValueError, match="unsafe live surface"):
        gate.strategy_market_research_readiness_gate_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet": "redacted",
            },
        )


def test_module_scope_stays_paper_report_readonly_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_market_research_readiness_gate_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "db",
        "file io",
        "open(",
        "advice",
        "order",
        "trade",
        "trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

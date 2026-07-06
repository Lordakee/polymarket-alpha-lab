from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab import (
    strategy_market_candidate_explainability_panel_v10 as panel_module,
)
from polymarket_alpha_lab.strategy_market_candidate_explainability_panel_v10 import (
    StrategyMarketCandidateExplainabilityPanelV10Component,
    StrategyMarketCandidateExplainabilityPanelV10Input,
    StrategyMarketCandidateExplainabilityPanelV10Payload,
    StrategyMarketCandidateExplainabilityPanelV10Result,
    build_strategy_market_candidate_explainability_panel_v10_result,
    explain_strategy_market_candidate_explainability_panel_v10,
    strategy_market_candidate_explainability_panel_v10_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def component(
    code: str = "forecast_edge",
    *,
    label: str = "Forecast edge",
    value: Decimal = d("0.300000"),
) -> StrategyMarketCandidateExplainabilityPanelV10Component:
    return StrategyMarketCandidateExplainabilityPanelV10Component(
        code=code,
        label=label,
        value=value,
    )


def panel_input(**overrides: object) -> StrategyMarketCandidateExplainabilityPanelV10Input:
    values = {
        "market_id": "market-alpha",
        "triage_status": "pass",
        "edge_components": (
            component("forecast_edge", label="Forecast edge", value=d("0.300000")),
            component("source_edge", label="Source edge", value=d("0.120000")),
        ),
        "cost_components": (
            component("fees", label="Fees", value=d("0.050000")),
            component("spread", label="Spread", value=d("0.020000")),
        ),
        "risk_components": (
            component("resolution_risk", label="Resolution risk", value=d("0.100000")),
        ),
        "team_assignment": "macro-research",
        "missing_evidence_count": d("0.000000"),
        "recommended_next_step": "advance_to_readonly_research_packet",
    }
    values.update(overrides)
    return StrategyMarketCandidateExplainabilityPanelV10Input(**values)


def result(
    input_row: StrategyMarketCandidateExplainabilityPanelV10Input | None = None,
) -> StrategyMarketCandidateExplainabilityPanelV10Result:
    return build_strategy_market_candidate_explainability_panel_v10_result(
        input_row or panel_input(),
    )


def test_pass_candidate_builds_ready_explanation_payload() -> None:
    explanation = result()

    assert is_dataclass(explanation)
    assert explanation.explanation_status == "ready"
    assert explanation.blocking_points == ()
    assert explanation.reason_codes == (
        "candidate_explainability_ready",
        "candidate_triage_pass",
        "candidate_positive_net_score",
        "candidate_evidence_complete",
        "candidate_team_assignment_ready",
    )
    assert explanation.paper_only is True
    assert explanation.report_only is True
    assert explanation.readonly is True

    assert explanation.payload.market_id == "market-alpha"
    assert explanation.payload.triage_status == "pass"
    assert explanation.payload.edge_total == d("0.420000")
    assert explanation.payload.cost_total == d("0.070000")
    assert explanation.payload.risk_total == d("0.100000")
    assert explanation.payload.net_explainability_score == d("0.250000")
    assert explanation.payload.missing_evidence_count == d("0.000000")
    assert type(explanation.payload.net_explainability_score) is Decimal

    assert explanation.summary_points == (
        "Market market-alpha is pass and assigned to macro-research.",
        (
            "Components: edge 0.420000 less cost 0.070000 and risk 0.100000 "
            "leaves net explainability score 0.250000."
        ),
        (
            "Evidence: 0.000000 missing items; next step "
            "advance_to_readonly_research_packet."
        ),
    )
    assert explanation.positive_points == (
        "Edge components contribute 0.420000.",
        "Net explainability score is positive: 0.250000.",
        "No missing evidence items are reported.",
        "Assigned team macro-research owns the next review.",
    )

    payload = strategy_market_candidate_explainability_panel_v10_payload(explanation)
    assert payload["explanation_status"] == "ready"
    assert payload["payload"]["net_explainability_score"] == "0.250000"
    assert payload["payload"]["missing_evidence_count"] == "0.000000"
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_watch_candidate_requires_review_without_blocking() -> None:
    explanation = result(
        panel_input(
            triage_status="watch",
            recommended_next_step="refresh_scores_before_specialist_review",
        ),
    )

    assert explanation.explanation_status == "needs_review"
    assert explanation.blocking_points == ()
    assert explanation.reason_codes == (
        "candidate_explainability_needs_review",
        "candidate_triage_watch",
        "candidate_positive_net_score",
        "candidate_evidence_complete",
        "candidate_team_assignment_ready",
    )
    assert explanation.payload.net_explainability_score == d("0.250000")


def test_blocked_candidate_surfaces_human_blocking_points() -> None:
    explanation = result(
        panel_input(
            triage_status="blocked",
            edge_components=(component(value=d("0.100000")),),
            cost_components=(component("cost_drag", label="Cost drag", value=d("0.090000")),),
            risk_components=(component("risk_drag", label="Risk drag", value=d("0.050000")),),
            missing_evidence_count=d("2.000000"),
            recommended_next_step="do_not_advance_until_blockers_clear",
        ),
    )

    assert explanation.explanation_status == "blocked"
    assert explanation.payload.net_explainability_score == d("-0.040000")
    assert explanation.blocking_points == (
        "Triage status is blocked; clear candidate blockers before promotion.",
        "Missing evidence count is 2.000000; attach required evidence before promotion.",
        "Net explainability score is not positive: -0.040000.",
    )
    assert explanation.positive_points == (
        "Edge components contribute 0.100000.",
        "Assigned team macro-research owns the next review.",
    )
    assert explanation.reason_codes == (
        "candidate_explainability_blocked",
        "candidate_triage_blocked",
        "candidate_missing_evidence_blocked",
        "candidate_nonpositive_net_score_blocked",
        "candidate_team_assignment_ready",
    )


def test_direct_function_accepts_required_input_surface() -> None:
    explanation = explain_strategy_market_candidate_explainability_panel_v10(
        market_id="market-direct",
        triage_status="pass",
        edge_components=(component(value=d("0.500000")),),
        cost_components=(component("direct_cost", label="Direct cost", value=d("0.100000")),),
        risk_components=(component("direct_risk", label="Direct risk", value=d("0.050000")),),
        team_assignment="sports-research",
        missing_evidence_count=d("0.000000"),
        recommended_next_step="advance_to_readonly_research_packet",
    )

    assert explanation.explanation_status == "ready"
    assert explanation.payload.market_id == "market-direct"
    assert explanation.payload.team_assignment == "sports-research"
    assert explanation.payload.net_explainability_score == d("0.350000")


def test_dataclasses_are_frozen_and_numeric_fields_are_decimal_only() -> None:
    input_row = panel_input()
    explanation = result(input_row)

    for dataclass_type in (
        StrategyMarketCandidateExplainabilityPanelV10Component,
        StrategyMarketCandidateExplainabilityPanelV10Input,
        StrategyMarketCandidateExplainabilityPanelV10Payload,
        StrategyMarketCandidateExplainabilityPanelV10Result,
    ):
        assert is_dataclass(dataclass_type)

    with pytest.raises(FrozenInstanceError):
        explanation.explanation_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        explanation.payload.net_explainability_score = d("0.000000")  # type: ignore[misc]

    assert type(input_row.missing_evidence_count) is Decimal
    assert type(explanation.payload.edge_total) is Decimal
    assert type(explanation.payload.cost_total) is Decimal
    assert type(explanation.payload.risk_total) is Decimal
    assert type(explanation.payload.net_explainability_score) is Decimal
    _assert_no_int_or_float(input_row)
    _assert_no_int_or_float(explanation)


def test_validation_rejects_bad_types_flags_and_inconsistent_text() -> None:
    with pytest.raises(ValueError, match="market_id"):
        panel_input(market_id=" market-alpha")
    with pytest.raises(ValueError, match="triage_status"):
        panel_input(triage_status="unknown")
    with pytest.raises(ValueError, match="value"):
        component(value=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="value"):
        component(value=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="cost_components"):
        panel_input(cost_components=(component(value=d("-0.010000")),))
    with pytest.raises(ValueError, match="risk_components"):
        panel_input(risk_components=(component(value=d("-0.010000")),))
    with pytest.raises(ValueError, match="missing_evidence_count"):
        panel_input(missing_evidence_count=d("1.500000"))
    with pytest.raises(ValueError, match="recommended_next_step"):
        panel_input(recommended_next_step="")
    with pytest.raises(ValueError, match="paper_only"):
        panel_input(paper_only=False)
    with pytest.raises(ValueError, match="input_row"):
        build_strategy_market_candidate_explainability_panel_v10_result(
            object(),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="explanation_status"):
        replace(result(), explanation_status="blocked")
    with pytest.raises(ValueError, match="unsafe"):
        panel_input(market_id="market-" + "wal" "let")


def test_payload_serializer_rejects_float_and_flag_downgrades() -> None:
    with pytest.raises(ValueError, match="readonly"):
        strategy_market_candidate_explainability_panel_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": False,
            },
        )

    with pytest.raises(ValueError, match="float"):
        strategy_market_candidate_explainability_panel_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "payload": {"score": 0.1},
            },
        )


def test_module_surface_stays_report_only_without_external_side_effects() -> None:
    source = inspect.getsource(panel_module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    float_literals: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_literals.append(node.value)

    forbidden_imports = {
        "os",
        "pathlib",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "socket",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "open",
        "urlopen",
        "request",
        "get",
        "post",
        "put",
        "delete",
        "submit_" + "order",
        "cancel_" + "order",
        "sign_" + "order",
        "place_" + "order",
    }
    forbidden_fragments = (
        "li" "ve " + "trad" "ing",
        "private" "_" "key",
        "submit" "_" "order",
        "place" "_" "order",
        "sign" "_" "order",
    )

    assert imported_modules.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert float_literals == []
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def _assert_no_int_or_float(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float):
        raise AssertionError(f"numeric value must be Decimal, got {type(value).__name__}")
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if is_dataclass(value) and not isinstance(value, type):
        for item in value.__dict__.values():
            _assert_no_int_or_float(item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _assert_no_int_or_float(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_int_or_float(item)

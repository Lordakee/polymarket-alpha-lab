from dataclasses import FrozenInstanceError
from decimal import Decimal
import inspect
from importlib import import_module

import pytest

from polymarket_alpha_lab.strategy_market_screening_stage_gate_v10 import (
    MarketScreeningStageGateInput,
    MarketScreeningStageGateReport,
    evaluate_market_screening_stage_gate,
    market_screening_stage_gate_payload,
)


def _gate_input(**overrides):
    values = {
        "market_id": "market-123",
        "stage_name": "edge_screen",
        "candidate_status": "research_ready",
        "source_confidence_level": "high",
        "cost_adjusted_edge_bps": Decimal("37.125000"),
        "portfolio_fit_status": "fit",
        "research_budget_status": "available",
        "human_review_required": False,
    }
    values.update(overrides)
    return MarketScreeningStageGateInput(**values)


def _contains_decimal(value) -> bool:
    if isinstance(value, Decimal):
        return True
    if isinstance(value, dict):
        return any(_contains_decimal(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_decimal(item) for item in value)
    return False


def test_stage_gate_passes_clean_candidate_to_next_screening_stage() -> None:
    report = evaluate_market_screening_stage_gate(_gate_input())

    assert type(report) is MarketScreeningStageGateReport
    assert report.market_id == "market-123"
    assert report.stage_name == "edge_screen"
    assert report.cost_adjusted_edge_bps == Decimal("37.125000")
    assert report.stage_gate_status == "pass"
    assert report.next_stage == "portfolio_fit"
    assert report.blocking_reasons == ()
    assert report.reason_codes == ("market_screening_stage_gate_passed",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_stage_gate_skips_optional_human_review_when_budget_stage_passes() -> None:
    report = evaluate_market_screening_stage_gate(
        _gate_input(stage_name="research_budget"),
    )

    assert report.stage_gate_status == "pass"
    assert report.next_stage == "paper_queue"
    assert report.reason_codes == ("market_screening_stage_gate_passed",)


def test_stage_gate_blocks_hard_failures_before_any_next_stage() -> None:
    report = evaluate_market_screening_stage_gate(
        _gate_input(
            candidate_status="blocked",
            source_confidence_level="low",
            cost_adjusted_edge_bps=Decimal("-1.000000"),
            portfolio_fit_status="blocked",
            research_budget_status="exhausted",
        ),
    )

    assert report.stage_gate_status == "blocked"
    assert report.next_stage == "screening_blocked"
    assert report.blocking_reasons == (
        "candidate_status=blocked",
        "source_confidence_level=low",
        "cost_adjusted_edge_bps_below_zero",
        "portfolio_fit_status=blocked",
        "research_budget_status=exhausted",
    )
    assert report.reason_codes == (
        "market_screening_stage_gate_blocked",
        "candidate_status_blocked",
        "source_confidence_low",
        "cost_adjusted_edge_negative",
        "portfolio_fit_blocked",
        "research_budget_exhausted",
    )


def test_stage_gate_watches_soft_failures_and_routes_required_review() -> None:
    report = evaluate_market_screening_stage_gate(
        _gate_input(
            stage_name="research_budget",
            candidate_status="watch",
            source_confidence_level="medium",
            cost_adjusted_edge_bps=Decimal("9.999999"),
            portfolio_fit_status="watch",
            research_budget_status="limited",
            human_review_required=True,
        ),
    )

    assert report.stage_gate_status == "watch"
    assert report.next_stage == "human_review"
    assert report.blocking_reasons == ()
    assert report.reason_codes == (
        "market_screening_stage_gate_watch",
        "candidate_status_watch",
        "source_confidence_medium",
        "cost_adjusted_edge_below_pass_threshold",
        "portfolio_fit_watch",
        "research_budget_limited",
        "human_review_required",
    )


def test_payload_is_report_only_json_ready_and_contains_no_decimals() -> None:
    report = evaluate_market_screening_stage_gate(_gate_input())
    payload = market_screening_stage_gate_payload(report)

    assert payload == report.payload
    assert payload["market_id"] == "market-123"
    assert payload["cost_adjusted_edge_bps"] == "37.125000"
    assert payload["stage_gate_status"] == "pass"
    assert payload["next_stage"] == "portfolio_fit"
    assert payload["blocking_reasons"] == []
    assert payload["reason_codes"] == ["market_screening_stage_gate_passed"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _contains_decimal(payload)


def test_stage_gate_uses_decimal_only_inputs_and_validates_domains() -> None:
    with pytest.raises(ValueError, match="cost_adjusted_edge_bps must be a Decimal"):
        _gate_input(cost_adjusted_edge_bps=37.125)

    with pytest.raises(ValueError, match="stage_name must be one of"):
        _gate_input(stage_name="unknown_stage")

    with pytest.raises(ValueError, match="candidate_status must be one of"):
        _gate_input(candidate_status="maybe")

    with pytest.raises(ValueError, match="source_confidence_level must be one of"):
        _gate_input(source_confidence_level="certain")

    with pytest.raises(ValueError, match="portfolio_fit_status must be one of"):
        _gate_input(portfolio_fit_status="oversized")

    with pytest.raises(ValueError, match="research_budget_status must be one of"):
        _gate_input(research_budget_status="overspent")

    with pytest.raises(ValueError, match="human_review_required must be a bool"):
        _gate_input(human_review_required=1)


def test_stage_gate_requires_hard_phase_1_flags_and_frozen_dataclasses() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        _gate_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        _gate_input(report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        _gate_input(readonly=False)

    gate_input = _gate_input()
    report = evaluate_market_screening_stage_gate(gate_input)

    with pytest.raises(FrozenInstanceError):
        gate_input.market_id = "other-market"

    with pytest.raises(FrozenInstanceError):
        report.stage_gate_status = "blocked"


def test_stage_gate_rejects_wrong_report_type_for_payload() -> None:
    unsafe = object.__new__(MarketScreeningStageGateReport)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)

    with pytest.raises(ValueError, match="report must be a MarketScreeningStageGateReport"):
        market_screening_stage_gate_payload(object())

    with pytest.raises(ValueError, match="paper_only must be True"):
        market_screening_stage_gate_payload(unsafe)


def test_module_has_no_persistence_network_or_execution_surface_imports() -> None:
    module = import_module("polymarket_alpha_lab.strategy_market_screening_stage_gate_v10")
    source = inspect.getsource(module)

    forbidden_fragments = (
        "requests",
        "httpx",
        "socket",
        "urllib",
        "aiohttp",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "web3",
        "wallet",
        "private_key",
        "credential",
        "py_clob_client",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

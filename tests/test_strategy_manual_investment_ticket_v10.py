from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_manual_investment_ticket_v10"


def api():
    return import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object):
    module = api()
    values = {
        "market_id": "market-alpha",
        "outcome": "Yes",
        "side": "buy",
        "limit_price": d("0.420000"),
        "max_size": d("12.500000"),
        "expected_value": d("0.037500"),
        "estimated_fee": d("0.075000"),
        "estimated_slippage": d("0.050000"),
        "evidence_summary": ("official source checked", "book depth reviewed"),
        "risk_warnings": ("thin exit depth",),
        "expiration_minutes": d("15.000000"),
    }
    values.update(overrides)
    return module.StrategyManualInvestmentTicketV10Candidate(**values)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert "auth" not in lowered
            assert "wallet" not in lowered
            assert "private_key" not in lowered
            assert "sign" not in lowered
            assert "order" not in lowered
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_builds_readonly_ticket_from_final_candidate_with_cost_summary() -> None:
    module = api()
    ticket = module.build_strategy_manual_investment_ticket_v10(candidate())

    assert isinstance(ticket, module.StrategyManualInvestmentTicketV10Ticket)
    assert ticket.market_id == "market-alpha"
    assert ticket.outcome == "Yes"
    assert ticket.side == "buy"
    assert ticket.limit_price == d("0.420000")
    assert ticket.max_size == d("12.500000")
    assert ticket.expected_value == d("0.037500")
    assert ticket.evidence_summary == (
        "official source checked",
        "book depth reviewed",
    )
    assert ticket.risk_warnings == ("thin exit depth",)
    assert ticket.expiration_minutes == d("15.000000")
    assert ticket.paper_only is True
    assert ticket.report_only is True
    assert ticket.readonly is True

    assert ticket.cost_summary.gross_notional == d("5.250000")
    assert ticket.cost_summary.estimated_fee == d("0.075000")
    assert ticket.cost_summary.estimated_slippage == d("0.050000")
    assert ticket.cost_summary.total_cost == d("5.375000")


def test_builds_multiple_tickets_preserving_candidate_order_and_rejects_duplicates() -> None:
    module = api()
    first = candidate(market_id="market-alpha")
    second = candidate(market_id="market-beta", outcome="No")

    tickets = module.build_strategy_manual_investment_tickets_v10((first, second))

    assert tuple(ticket.market_id for ticket in tickets) == (
        "market-alpha",
        "market-beta",
    )
    assert tuple(ticket.outcome for ticket in tickets) == ("Yes", "No")

    with pytest.raises(ValueError, match="duplicate market_id/outcome/side tickets"):
        module.build_strategy_manual_investment_tickets_v10((first, first))


def test_payload_is_json_ready_readonly_and_stringifies_decimals() -> None:
    module = api()
    ticket = module.build_strategy_manual_investment_ticket_v10(candidate())

    payload = module.strategy_manual_investment_ticket_v10_payload(ticket)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["limit_price"] == "0.420000"
    assert payload["max_size"] == "12.500000"
    assert payload["expected_value"] == "0.037500"
    assert payload["expiration_minutes"] == "15.000000"
    assert payload["cost_summary"]["gross_notional"] == "5.250000"
    assert payload["cost_summary"]["total_cost"] == "5.375000"
    assert_no_float_values(payload)


def test_dataclasses_are_frozen_and_reject_float_or_non_decimal_numeric_inputs() -> None:
    module = api()
    ticket = module.build_strategy_manual_investment_ticket_v10(candidate())

    with pytest.raises(FrozenInstanceError):
        ticket.limit_price = d("0.430000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="limit_price must be a Decimal"):
        candidate(limit_price=0.42)

    with pytest.raises(ValueError, match="expiration_minutes must be a Decimal"):
        candidate(expiration_minutes=15)

    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate(paper_only=False)


def test_validates_manual_ticket_shape_before_human_review() -> None:
    module = api()

    with pytest.raises(ValueError, match="side must be buy or sell"):
        candidate(side="hold")

    with pytest.raises(ValueError, match="limit_price must be greater than zero and less than one"):
        candidate(limit_price=d("1.000000"))

    with pytest.raises(ValueError, match="max_size must be greater than zero"):
        candidate(max_size=d("0.000000"))

    with pytest.raises(ValueError, match="evidence_summary must not be empty"):
        candidate(evidence_summary=())

    with pytest.raises(ValueError, match="candidate must be a StrategyManualInvestmentTicketV10Candidate"):
        module.build_strategy_manual_investment_ticket_v10(object())


def test_module_stays_pure_readonly_and_exports_only_ticket_surface() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    imported_modules: list[str] = []
    public_exports: tuple[str, ...] | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    public_exports = ast.literal_eval(node.value)

    assert public_exports == (
        "StrategyManualInvestmentTicketV10Candidate",
        "StrategyManualInvestmentTicketV10CostSummary",
        "StrategyManualInvestmentTicketV10Ticket",
        "build_strategy_manual_investment_ticket_v10",
        "build_strategy_manual_investment_tickets_v10",
        "strategy_manual_investment_ticket_v10_payload",
    )
    assert set(imported_modules) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "decimal",
        "typing",
        "polymarket_alpha_lab.team_paper_guard",
    }
    lowered_source = source.lower()
    for forbidden_fragment in (
        "requests",
        "httpx",
        "aiohttp",
        "sqlite3",
        "psycopg",
        "socket",
        "websocket",
        "py_clob_client",
        "place_order",
        "submit_order",
        "create_order",
        "cancel_order",
        "private_key",
        "wallet",
        "auth",
    ):
        assert forbidden_fragment not in lowered_source

    assert module.StrategyManualInvestmentTicketV10Candidate.__dataclass_params__.frozen is True
    assert module.StrategyManualInvestmentTicketV10CostSummary.__dataclass_params__.frozen is True
    assert module.StrategyManualInvestmentTicketV10Ticket.__dataclass_params__.frozen is True

from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_portfolio_concentration_gate.py"
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_portfolio_concentration_gate",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-portfolio-concentration-gate-test-v0",
        "category_watch_share": d("0.200000"),
        "category_block_share": d("0.300000"),
        "team_watch_share": d("0.150000"),
        "team_block_share": d("0.250000"),
        "event_cluster_watch_share": d("0.100000"),
        "event_cluster_block_share": d("0.200000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioConcentrationGateConfig(**values)


def evaluate(**overrides: object):
    module = api()
    values = {
        "category_exposure": d("100.000000"),
        "team_exposure": d("50.000000"),
        "event_cluster_exposure": d("40.000000"),
        "candidate_notional": d("40.000000"),
        "nav": d("1000.000000"),
        "config": config(),
    }
    values.update(overrides)
    return module.evaluate_strategy_portfolio_concentration_gate(**values)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_concentration_gate_passes_when_candidate_stays_inside_watch_caps() -> None:
    result = evaluate()

    assert result.config_version == "strategy-portfolio-concentration-gate-test-v0"
    assert result.category_exposure == d("100.000000")
    assert result.team_exposure == d("50.000000")
    assert result.event_cluster_exposure == d("40.000000")
    assert result.candidate_notional == d("40.000000")
    assert result.nav == d("1000.000000")
    assert result.post_trade_category_exposure == d("140.000000")
    assert result.post_trade_team_exposure == d("90.000000")
    assert result.post_trade_event_cluster_exposure == d("80.000000")
    assert result.category_exposure_share == d("0.140000")
    assert result.team_exposure_share == d("0.090000")
    assert result.event_cluster_exposure_share == d("0.080000")
    assert result.category_allowed_notional == d("200.000000")
    assert result.team_allowed_notional == d("200.000000")
    assert result.event_cluster_allowed_notional == d("160.000000")
    assert result.allowed_notional == d("40.000000")
    assert result.concentration_status == "pass"
    assert result.reason_codes == ("portfolio_concentration_pass",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_concentration_gate_watches_candidate_that_crosses_watch_cap() -> None:
    result = evaluate(
        category_exposure=d("190.000000"),
        team_exposure=d("100.000000"),
        event_cluster_exposure=d("70.000000"),
        candidate_notional=d("20.000000"),
    )

    assert result.post_trade_category_exposure == d("210.000000")
    assert result.category_exposure_share == d("0.210000")
    assert result.allowed_notional == d("20.000000")
    assert result.concentration_status == "watch"
    assert result.reason_codes == ("category_concentration_watch",)


def test_concentration_gate_blocks_and_caps_allowed_notional_at_tightest_limit() -> None:
    result = evaluate(
        category_exposure=d("295.000000"),
        team_exposure=d("100.000000"),
        event_cluster_exposure=d("150.000000"),
        candidate_notional=d("20.000000"),
    )

    assert result.post_trade_category_exposure == d("315.000000")
    assert result.category_exposure_share == d("0.315000")
    assert result.category_allowed_notional == d("5.000000")
    assert result.team_allowed_notional == d("150.000000")
    assert result.event_cluster_allowed_notional == d("50.000000")
    assert result.allowed_notional == d("5.000000")
    assert result.concentration_status == "blocked"
    assert result.reason_codes == (
        "category_concentration_block",
        "candidate_notional_exceeds_allowed",
    )


def test_concentration_gate_blocks_when_existing_exposure_already_exceeds_limit() -> None:
    result = evaluate(
        category_exposure=d("350.000000"),
        team_exposure=d("100.000000"),
        event_cluster_exposure=d("150.000000"),
        candidate_notional=d("20.000000"),
    )

    assert result.category_allowed_notional == ZERO
    assert result.allowed_notional == ZERO
    assert result.concentration_status == "blocked"
    assert result.reason_codes == (
        "category_concentration_block",
        "candidate_notional_exceeds_allowed",
    )


def test_outputs_are_decimal_only_frozen_and_tuple_only() -> None:
    module = api()
    result = evaluate()

    for item in fields(result):
        item_value = getattr(result, item.name)
        if item.name in {
            "config_version",
            "concentration_status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        }:
            continue
        assert type(item_value) is Decimal

    assert type(result.reason_codes) is tuple
    with pytest.raises(FrozenInstanceError):
        result.allowed_notional = d("1.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="category_exposure must be a Decimal"):
        evaluate(category_exposure=100)

    with pytest.raises(ValueError, match="candidate_notional must be a Decimal"):
        evaluate(candidate_notional=20.0)

    with pytest.raises(ValueError, match="nav must be a Decimal"):
        evaluate(nav=_DecimalSubclass("1000.000000"))

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(result, reason_codes=["portfolio_concentration_pass"])

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_portfolio_concentration_gate_payload(object())


def test_validation_rejects_bad_caps_negative_inputs_and_flag_downgrades() -> None:
    module = api()

    with pytest.raises(ValueError, match="category_block_share must not be below"):
        config(category_watch_share=d("0.300000"), category_block_share=d("0.200000"))

    with pytest.raises(ValueError, match="team_watch_share must be a probability"):
        config(team_watch_share=d("1.000001"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyPortfolioConcentrationGateConfig(paper_only=False)

    with pytest.raises(ValueError, match="category_exposure must be nonnegative"):
        evaluate(category_exposure=d("-1.000000"))

    with pytest.raises(ValueError, match="candidate_notional must be nonnegative"):
        evaluate(candidate_notional=d("-1.000000"))

    with pytest.raises(ValueError, match="nav must be positive"):
        evaluate(nav=ZERO)

    with pytest.raises(ValueError, match="config must be"):
        evaluate(config=object())


def test_payload_uses_decimal_strings_flags_and_no_floats() -> None:
    module = api()
    result = evaluate(
        category_exposure=d("295.000000"),
        team_exposure=d("100.000000"),
        event_cluster_exposure=d("150.000000"),
        candidate_notional=d("20.000000"),
    )

    payload = module.strategy_portfolio_concentration_gate_payload(result)

    assert payload["config_version"] == "strategy-portfolio-concentration-gate-test-v0"
    assert payload["category_exposure"] == "295.000000"
    assert payload["category_exposure_share"] == "0.315000"
    assert payload["allowed_notional"] == "5.000000"
    assert payload["concentration_status"] == "blocked"
    assert payload["reason_codes"] == [
        "category_concentration_block",
        "candidate_notional_exceeds_allowed",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.strategy_portfolio_concentration_gate_payload(
            replace(result, paper_only=False),
        )


def test_module_scope_has_no_live_trading_persistence_network_or_sensitive_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
        "recommend",
    }
    forbidden_attr_fragments = (
        "account",
        "advice",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)

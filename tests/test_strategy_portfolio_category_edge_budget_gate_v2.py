from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_portfolio_category_edge_budget_gate_v2"
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_portfolio_category_edge_budget_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


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
            "strategy-portfolio-category-edge-budget-gate-v2-test"
        ),
        "portfolio_notional_cap": d("1000.000000"),
        "category_budget_share": d("0.200000"),
        "category_exposure_watch_share": d("0.800000"),
        "category_exposure_block_share": d("1.000000"),
        "open_candidate_watch_count": d("4"),
        "open_candidate_block_count": d("6"),
        "correlated_event_watch_count": d("3"),
        "correlated_event_block_count": d("5"),
        "min_candidate_cost_adjusted_edge": d("0.020000"),
        "min_watch_cost_adjusted_edge": d("0.000000"),
        "min_liquidity_capacity_ratio": d("1.500000"),
        "block_liquidity_capacity_ratio": d("1.000000"),
        "category_drawdown_watch_ratio": d("0.100000"),
        "category_drawdown_block_ratio": d("0.200000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioCategoryEdgeBudgetGateV2Config(**values)


def category(**overrides: object) -> Any:
    module = api()
    values = {
        "category": "macro",
        "current_category_exposure": d("100.000000"),
        "open_candidate_count": d("1"),
        "correlated_event_count": d("1"),
        "category_drawdown_ratio": d("0.030000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot(**values)


def candidate(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_id": "ready",
        "category": "macro",
        "correlated_event_key": "fomc-july",
        "candidate_notional": d("20.000000"),
        "gross_edge": d("0.120000"),
        "total_cost": d("0.030000"),
        "available_liquidity": d("60.000000"),
        "reason_codes": ("seed",),
    }
    values.update(overrides)
    return module.StrategyPortfolioCategoryEdgeBudgetGateV2Candidate(**values)


def report(
    *candidates: object,
    categories: tuple[object, ...] | None = None,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_portfolio_category_edge_budget_gate_v2_report(
        candidates,
        category_snapshots=categories if categories is not None else (category(),),
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_decimal_only_dataclass(value: object) -> None:
    for item in fields(value):
        field_value = getattr(value, item.name)
        if type(field_value) in (bool, str, datetime, tuple) or field_value is None:
            continue
        assert type(field_value) is Decimal


def assert_no_float_decimal_or_int_payload_values(value: object) -> None:
    if type(value) in (float, int) or isinstance(value, Decimal):
        raise AssertionError(f"unexpected non-JSON numeric value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_decimal_or_int_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_decimal_or_int_payload_values(item)


def test_builds_phase_one_category_edge_budget_report_with_pass_watch_block_rows() -> None:
    result = report(
        candidate(
            candidate_id="ready",
            category="macro",
            correlated_event_key="fomc-july",
        ),
        candidate(
            candidate_id="watch",
            category="sports",
            correlated_event_key="cup-final",
            gross_edge=d("0.040000"),
            total_cost=d("0.015000"),
            available_liquidity=d("40.000000"),
        ),
        candidate(
            candidate_id="blocked",
            category="crypto",
            correlated_event_key="reserve-shock",
            gross_edge=d("0.015000"),
            total_cost=d("0.020000"),
            available_liquidity=d("15.000000"),
        ),
        categories=(
            category(
                category="macro",
                current_category_exposure=d("100.000000"),
                open_candidate_count=d("1"),
                correlated_event_count=d("1"),
                category_drawdown_ratio=d("0.030000"),
            ),
            category(
                category="sports",
                current_category_exposure=d("150.000000"),
                open_candidate_count=d("3"),
                correlated_event_count=d("1"),
                category_drawdown_ratio=d("0.050000"),
            ),
            category(
                category="crypto",
                current_category_exposure=d("195.000000"),
                open_candidate_count=d("5"),
                correlated_event_count=d("4"),
                category_drawdown_ratio=d("0.220000"),
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-portfolio-category-edge-budget-gate-v2-test"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.digest_status == "blocked"
    assert result.total_candidate_notional == d("60.000000")
    assert result.total_allowed_candidate_notional == d("45.000000")
    assert result.max_category_exposure_budget_share == d("1.075000")
    assert result.max_open_candidate_count == d("6")
    assert result.max_correlated_event_count == d("5")
    assert result.min_cost_adjusted_edge == d("-0.005000")
    assert result.min_liquidity_capacity_ratio == d("0.750000")
    assert result.max_category_drawdown_ratio == d("0.220000")
    assert result.reason_codes == (
        "seed",
        "category_edge_budget_pass",
        "category_edge_budget_watch",
        "category_edge_budget_blocked",
        "category_exposure_watch",
        "category_exposure_block",
        "open_candidate_count_watch",
        "open_candidate_count_block",
        "correlated_event_count_block",
        "cost_adjusted_edge_below_watch",
        "liquidity_capacity_block",
        "category_drawdown_block",
        "candidate_notional_exceeds_allowed",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    assert tuple(row.candidate_id for row in result.rows) == (
        "blocked",
        "watch",
        "ready",
    )

    blocked = result.rows[0]
    assert blocked.rank == d("1")
    assert blocked.category == "crypto"
    assert blocked.category_budget_notional == d("200.000000")
    assert blocked.current_category_exposure == d("195.000000")
    assert blocked.post_trade_category_exposure == d("215.000000")
    assert blocked.category_exposure_budget_share == d("1.075000")
    assert blocked.post_trade_open_candidate_count == d("6")
    assert blocked.post_trade_correlated_event_count == d("5")
    assert blocked.cost_adjusted_edge == d("-0.005000")
    assert blocked.liquidity_capacity_ratio == d("0.750000")
    assert blocked.liquidity_capacity_notional == d("10.000000")
    assert blocked.allowed_candidate_notional == d("5.000000")
    assert blocked.category_drawdown_ratio == d("0.220000")
    assert blocked.gate_status == "blocked"
    assert blocked.reason_codes == (
        "seed",
        "category_edge_budget_blocked",
        "category_exposure_block",
        "open_candidate_count_block",
        "correlated_event_count_block",
        "cost_adjusted_edge_below_watch",
        "liquidity_capacity_block",
        "category_drawdown_block",
        "candidate_notional_exceeds_allowed",
    )
    assert len(blocked.derived_validation_digest) == 64

    watched = result.rows[1]
    assert watched.rank == d("2")
    assert watched.category_exposure_budget_share == d("0.850000")
    assert watched.post_trade_open_candidate_count == d("4")
    assert watched.cost_adjusted_edge == d("0.025000")
    assert watched.liquidity_capacity_ratio == d("2.000000")
    assert watched.allowed_candidate_notional == d("20.000000")
    assert watched.gate_status == "watch"
    assert watched.reason_codes == (
        "seed",
        "category_edge_budget_watch",
        "category_exposure_watch",
        "open_candidate_count_watch",
    )

    passed = result.rows[2]
    assert passed.rank == d("3")
    assert passed.category_exposure_budget_share == d("0.600000")
    assert passed.post_trade_open_candidate_count == d("2")
    assert passed.post_trade_correlated_event_count == d("2")
    assert passed.cost_adjusted_edge == d("0.090000")
    assert passed.liquidity_capacity_ratio == d("3.000000")
    assert passed.allowed_candidate_notional == d("20.000000")
    assert passed.gate_status == "pass"
    assert passed.reason_codes == ("seed", "category_edge_budget_pass")


def test_payload_serializes_decimal_strings_and_is_digest_deterministic() -> None:
    module = api()
    macro = category(category="macro")
    sports = category(
        category="sports",
        current_category_exposure=d("150.000000"),
        open_candidate_count=d("3"),
    )
    ready = candidate(candidate_id="ready", category="macro")
    watched = candidate(
        candidate_id="watch",
        category="sports",
        gross_edge=d("0.040000"),
        total_cost=d("0.015000"),
        available_liquidity=d("40.000000"),
    )

    first = report(watched, ready, categories=(sports, macro))
    second = report(ready, watched, categories=(macro, sports))

    assert first.derived_validation_digest == second.derived_validation_digest
    assert tuple(row.derived_validation_digest for row in first.rows) == tuple(
        row.derived_validation_digest for row in second.rows
    )

    payload = module.strategy_portfolio_category_edge_budget_gate_v2_payload(first)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "2"
    assert payload["total_candidate_notional"] == "40.000000"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["candidate_id"] == "watch"
    assert payload["rows"][0]["category_exposure_budget_share"] == "0.850000"
    assert payload["rows"][0]["reason_codes"] == [
        "seed",
        "category_edge_budget_watch",
        "category_exposure_watch",
        "open_candidate_count_watch",
    ]
    assert payload["rows"][0]["derived_validation_digest"] == first.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_decimal_or_int_payload_values(payload)


def test_outputs_are_decimal_only_frozen_and_tamper_evident() -> None:
    module = api()
    result = report(candidate())
    row = result.rows[0]

    for instance in (config(), category(), candidate(), row, result):
        assert_decimal_only_dataclass(instance)

    with pytest.raises(FrozenInstanceError):
        row.gate_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        result.digest_status = "watch"
    with pytest.raises(FrozenInstanceError):
        config().category_budget_share = d("0.300000")

    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(category(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, gate_status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, blocked_count=d("1"))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_portfolio_category_edge_budget_gate_v2_payload(object())


def test_validates_decimal_only_inputs_thresholds_utc_and_category_mapping() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    converted = report(
        candidate(),
        categories=(category(),),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=eastern),
    )
    assert converted.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="category_exposure_block_share"):
        config(
            category_exposure_watch_share=d("0.900000"),
            category_exposure_block_share=d("0.800000"),
        )
    with pytest.raises(ValueError, match="block_liquidity_capacity_ratio"):
        config(
            min_liquidity_capacity_ratio=d("1.500000"),
            block_liquidity_capacity_ratio=d("2.000000"),
        )
    with pytest.raises(ValueError, match="candidate_notional"):
        candidate(candidate_notional=20)
    with pytest.raises(ValueError, match="available_liquidity"):
        candidate(available_liquidity=_DecimalSubclass("60.000000"))
    with pytest.raises(ValueError, match="category"):
        category(category=_StringSubclass("macro"))
    with pytest.raises(ValueError, match="open_candidate_count"):
        category(open_candidate_count=d("1.5"))
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=["seed"])
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate(), generated_at=_DatetimeSubclass(2026, 7, 6, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        report(candidate(), generated_at=datetime(2026, 7, 6, 12))
    with pytest.raises(ValueError, match="category_snapshots"):
        module.build_strategy_portfolio_category_edge_budget_gate_v2_report(
            (candidate(category="missing"),),
            category_snapshots=(category(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="candidates"):
        module.build_strategy_portfolio_category_edge_budget_gate_v2_report(
            "not-candidates",
            category_snapshots=(category(),),
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_module_scope_has_no_external_io_execution_or_live_surfaces() -> None:
    module = api()
    assert set(module.__all__) == {
        "DEFAULT_STRATEGY_PORTFOLIO_CATEGORY_EDGE_BUDGET_GATE_V2_CONFIG_VERSION",
        "StrategyPortfolioCategoryEdgeBudgetGateV2Candidate",
        "StrategyPortfolioCategoryEdgeBudgetGateV2CategorySnapshot",
        "StrategyPortfolioCategoryEdgeBudgetGateV2Config",
        "StrategyPortfolioCategoryEdgeBudgetGateV2Report",
        "StrategyPortfolioCategoryEdgeBudgetGateV2Row",
        "build_strategy_portfolio_category_edge_budget_gate_v2_report",
        "strategy_portfolio_category_edge_budget_gate_v2_payload",
    }

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    forbidden_source_snippets = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "clob",
        "private_key",
        "secret",
        "account",
        "broker",
        "submit",
        "cancel",
        "connect(",
        "execute(",
        "fetch(",
        "commit(",
        "rollback(",
        "open(",
        "path(",
        ".write",
        "live trading",
    )
    assert not any(snippet in lowered_source for snippet in forbidden_source_snippets)

    tree = ast.parse(source)
    imported_modules: list[str] = []
    call_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not any(
        module_name.split(".")[0]
        in {
            "asyncio",
            "os",
            "pathlib",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "urllib",
        }
        for module_name in imported_modules
    )
    assert not any(
        call_name
        in {
            "buy",
            "connect",
            "cursor",
            "environ",
            "execute",
            "fetch",
            "getenv",
            "insert",
            "login",
            "open",
            "persist",
            "sell",
            "send",
            "write",
        }
        for call_name in call_names
    )

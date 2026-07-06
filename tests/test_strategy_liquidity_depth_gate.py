from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 9, 30, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "strategy_liquidity_depth_gate.py"
)

EXPECTED_EXPORTS = (
    "StrategyLiquidityDepthGateInput",
    "StrategyLiquidityDepthGateConfig",
    "StrategyLiquidityDepthGateRow",
    "StrategyLiquidityDepthGateReport",
    "build_strategy_liquidity_depth_gate_report",
    "strategy_liquidity_depth_gate_payload",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "typing",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
    "asyncio",
    "bs4",
    "clob_client",
    "cloudscraper",
    "curl_cffi",
    "duckdb",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "http",
    "httpx",
    "json",
    "mechanize",
    "os",
    "pandas",
    "pathlib",
    "playwright",
    "polars",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.runner",
    "polymarket_alpha_lab.strategy_recommendation_log",
    "py_clob_client",
    "requests",
    "requests_html",
    "runpy",
    "scrapy",
    "selenium",
    "socket",
    "sqlite3",
    "ssl",
    "subprocess",
    "urllib",
    "urllib3",
    "web3",
    "websocket",
    "websockets",
}

FORBIDDEN_NAME_FRAGMENTS = {
    "account",
    "apikey",
    "apitoken",
    "auth",
    "authenticate",
    "broker",
    "browser",
    "cancelorder",
    "client",
    "credential",
    "credentialloader",
    "credentialmanager",
    "credentials",
    "executionclient",
    "fetch",
    "http",
    "liveorder",
    "network",
    "order",
    "pathlib",
    "placeorder",
    "postorder",
    "private",
    "privatekey",
    "requestpayload",
    "secret",
    "sendorder",
    "sign",
    "signature",
    "submit",
    "submitorder",
    "token",
    "tradeclient",
    "wallet",
    "websocket",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "append",
    "compile",
    "eval",
    "exec",
    "input",
    "open",
    "print",
    "read",
    "write",
}

ALLOWED_FORBIDDEN_NAME_MATCHES = {
    "readonly",
    "strategiliquiditydepthgateconfig",
    "strategiliquiditydepthgateinput",
    "strategiliquiditydepthgatereport",
    "strategiliquiditydepthgaterow",
    "buildstrategyliquiditydepthgatereport",
    "strategyliquiditydepthgatepayload",
}


def _api():
    return import_module("polymarket_alpha_lab.strategy_liquidity_depth_gate")


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides):
    values = {
        "config_version": "strategy-liquidity-depth-gate-v0",
        "max_pass_top_of_book_spread": d("0.020000"),
        "max_watch_top_of_book_spread": d("0.050000"),
        "min_pass_depth_ratio": d("0.800000"),
        "min_watch_depth_ratio": d("0.500000"),
        "min_pass_market_activity_score": d("0.700000"),
        "min_watch_market_activity_score": d("0.400000"),
    }
    values.update(overrides)
    return _api().StrategyLiquidityDepthGateConfig(**values)


def _input(**overrides):
    values = {
        "market_slug": "fed-cut-july-2026",
        "top_of_book_spread": d("0.010000"),
        "available_depth": d("100.000000"),
        "target_notional": d("100.000000"),
        "market_activity_score": d("0.900000"),
    }
    values.update(overrides)
    return _api().StrategyLiquidityDepthGateInput(**values)


def _report(*inputs, gate_config=None, generated_at=GENERATED_AT):
    return _api().build_strategy_liquidity_depth_gate_report(
        inputs,
        config=gate_config or _config(),
        generated_at=generated_at,
    )


def _field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_liquidity_depth_gate_passes_deep_active_tight_market() -> None:
    api = _api()

    report = _report(_input())

    assert type(report) is api.StrategyLiquidityDepthGateReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-liquidity-depth-gate-v0"
    assert report.gate_status == "pass"
    assert report.input_count == d("1")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.capacity_notional == d("100.000000")
    assert report.reason_codes == ("strategy_liquidity_depth_gate_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert type(row) is api.StrategyLiquidityDepthGateRow
    assert row.market_slug == "fed-cut-july-2026"
    assert row.top_of_book_spread == d("0.010000")
    assert row.available_depth == d("100.000000")
    assert row.target_notional == d("100.000000")
    assert row.market_activity_score == d("0.900000")
    assert row.depth_ratio == d("1.000000")
    assert row.gate_status == "pass"
    assert row.capacity_notional == d("100.000000")
    assert row.reason_codes == ("strategy_liquidity_depth_gate_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True

    payload = api.strategy_liquidity_depth_gate_payload(report)
    assert payload["generated_at"] == "2026-07-06T09:30:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["capacity_notional"] == "100.000000"
    assert payload["rows"][0]["depth_ratio"] == "1.000000"
    assert "recommend" not in repr(payload).lower()


def test_liquidity_depth_gate_watches_partial_depth_wide_spread_and_activity() -> None:
    report = _report(
        _input(
            market_slug="partial-depth",
            top_of_book_spread=d("0.030000"),
            available_depth=d("60.000000"),
            target_notional=d("100.000000"),
            market_activity_score=d("0.550000"),
        ),
    )

    row = report.rows[0]
    assert report.gate_status == "watch"
    assert report.pass_count == d("0")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("0")
    assert report.capacity_notional == d("60.000000")
    assert row.depth_ratio == d("0.600000")
    assert row.gate_status == "watch"
    assert row.capacity_notional == d("60.000000")
    assert row.reason_codes == (
        "depth_below_pass_threshold",
        "spread_above_pass_threshold",
        "activity_below_pass_threshold",
    )
    assert report.reason_codes == row.reason_codes


def test_liquidity_depth_gate_blocks_zero_depth_missing_target_and_hard_thresholds() -> None:
    report = _report(
        _input(
            market_slug="zero-depth",
            available_depth=d("0.000000"),
            target_notional=d("100.000000"),
        ),
        _input(
            market_slug="missing-target",
            available_depth=d("10.000000"),
            target_notional=d("0.000000"),
        ),
        _input(
            market_slug="hard-thresholds",
            top_of_book_spread=d("0.060000"),
            available_depth=d("20.000000"),
            target_notional=d("100.000000"),
            market_activity_score=d("0.300000"),
        ),
    )

    assert report.gate_status == "blocked"
    assert report.input_count == d("3")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("3")
    assert report.capacity_notional == d("20.000000")
    assert report.reason_codes == (
        "missing_target_notional",
        "no_available_depth",
        "depth_below_watch_threshold",
        "spread_above_watch_threshold",
        "activity_below_watch_threshold",
    )
    assert tuple((row.market_slug, row.capacity_notional) for row in report.rows) == (
        ("hard-thresholds", d("20.000000")),
        ("missing-target", d("0.000000")),
        ("zero-depth", d("0.000000")),
    )


def test_liquidity_depth_gate_sorts_by_status_capacity_and_identity() -> None:
    report = _report(
        _input(market_slug="zeta-pass"),
        _input(
            market_slug="alpha-watch",
            available_depth=d("60.000000"),
            target_notional=d("100.000000"),
        ),
        _input(
            market_slug="beta-watch",
            available_depth=d("70.000000"),
            target_notional=d("100.000000"),
        ),
        _input(market_slug="delta-blocked", available_depth=d("0.000000")),
    )

    assert tuple((row.gate_status, row.market_slug) for row in report.rows) == (
        ("pass", "zeta-pass"),
        ("watch", "beta-watch"),
        ("watch", "alpha-watch"),
        ("blocked", "delta-blocked"),
    )


def test_liquidity_depth_gate_decimal_only_tuple_only_flags_and_utc() -> None:
    api = _api()

    eastern = timezone(timedelta(hours=-4))
    report = api.build_strategy_liquidity_depth_gate_report(
        (
            _input(
                top_of_book_spread=d("0.0100004"),
                available_depth=d("33.3333334"),
                target_notional=d("100.0000004"),
                market_activity_score=d("0.9000004"),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 6, 5, 30, tzinfo=eastern),
    )

    row = report.rows[0]
    assert report.generated_at == GENERATED_AT
    assert row.top_of_book_spread == d("0.010000")
    assert row.available_depth == d("33.333333")
    assert row.target_notional == d("100.000000")
    assert row.market_activity_score == d("0.900000")
    assert row.depth_ratio == d("0.333333")

    with pytest.raises(ValueError, match="top_of_book_spread"):
        replace(_input(), top_of_book_spread=0.01)
    with pytest.raises(ValueError, match="available_depth"):
        replace(_input(), available_depth=100)
    with pytest.raises(ValueError, match="market_activity_score"):
        replace(_input(), market_activity_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_input(), readonly=False)
    with pytest.raises(ValueError, match="inputs"):
        api.build_strategy_liquidity_depth_gate_report(
            [_input()],
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="inputs"):
        api.build_strategy_liquidity_depth_gate_report(
            (_input(), object()),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_liquidity_depth_gate_dataclasses_are_frozen_and_direct_validation_holds() -> None:
    api = _api()
    source_input = _input()
    cfg = _config()
    report = _report(source_input)

    with pytest.raises(FrozenInstanceError):
        source_input.market_slug = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cfg.max_pass_top_of_book_spread = d("0.010000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].gate_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    rebuilt_row = api.StrategyLiquidityDepthGateRow(**_field_values(report.rows[0]))
    assert rebuilt_row == report.rows[0]

    with pytest.raises(ValueError, match="depth_ratio"):
        replace(report.rows[0], depth_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="capacity_notional"):
        replace(report.rows[0], capacity_notional=d("50.000000"))
    with pytest.raises(ValueError, match="input_count"):
        replace(report, input_count=d("2"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.rows[0], reason_codes=["strategy_liquidity_depth_gate_pass"])


def test_liquidity_depth_gate_empty_tuple_blocks_with_decimal_zeroes() -> None:
    report = _report()

    assert report.gate_status == "blocked"
    assert report.input_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.capacity_notional == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("missing_strategy_liquidity_depth_inputs",)


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> list[str]:
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


def module_exports(tree: ast.Module) -> tuple[str, ...]:
    assigned_exports = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def collected_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.name)
            if node.asname is not None:
                names.add(node.asname)
    return names


def test_strategy_liquidity_depth_gate_imports_only_allowed_dependencies() -> None:
    tree = parse_module()

    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_strategy_liquidity_depth_gate_does_not_import_forbidden_surfaces() -> None:
    tree = parse_module()

    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_strategy_liquidity_depth_gate_exports_only_report_api() -> None:
    tree = parse_module()

    assert module_exports(tree) == EXPECTED_EXPORTS


def test_strategy_liquidity_depth_gate_defines_no_forbidden_live_names() -> None:
    tree = parse_module()
    normalized_names = {
        normalize_identifier(name)
        for name in collected_names(tree)
        if normalize_identifier(name) not in ALLOWED_FORBIDDEN_NAME_MATCHES
    }

    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(
            normalize_identifier(fragment) in name for name in normalized_names
        ), (
            fragment,
            normalized_names,
        )


def test_strategy_liquidity_depth_gate_does_not_perform_io_or_dynamic_execution() -> None:
    tree = parse_module()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALL_NAMES, node.func.id
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in FORBIDDEN_CALL_NAMES, node.func.attr

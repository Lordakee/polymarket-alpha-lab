import ast
from pathlib import Path

import pytest

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


REPO_ROOT = Path(__file__).resolve().parents[1]
TEAM_MODULE_ROOT = REPO_ROOT / "src" / "polymarket_alpha_lab"

PSYCOPG_MODULE_NAMES = frozenset(
    (
        "team_forecast_psycopg.py",
        "team_diagnostics_snapshot_psycopg.py",
        "team_memory_readiness_digest_psycopg.py",
        "team_research_assignment_psycopg.py",
        "team_evidence_aggregation_attempt_psycopg.py",
    ),
)
PAPER_GUARD_MODULE_NAME = "team_paper_guard.py"
ADDITIONAL_STATIC_TEAM_MODULE_NAMES = (
    "supabase_team_forecast_config.py",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "clob_client",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "polymarket",
    "py_clob_client",
    "web3",
)

FORBIDDEN_INTERNAL_IMPORT_PREFIXES = (
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.paper_broker",
    "polymarket_alpha_lab.paper_broker_psycopg",
    "polymarket_alpha_lab.paper_broker_store",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.paper_execution_reconciliation",
    "polymarket_alpha_lab.paper_order_lifecycle",
    "polymarket_alpha_lab.paper_trade_journal",
    "polymarket_alpha_lab.positions",
)

FORBIDDEN_POLYMARKET_CLIENT_NAMES = frozenset(
    (
        "ApiCreds",
        "AssetType",
        "BalanceAllowanceParams",
        "BookParams",
        "ClobClient",
        "OpenOrderParams",
        "OrderArgs",
        "OrderBookSummary",
        "OrderType",
        "PostOrderArgs",
        "TradeParams",
    ),
)

FORBIDDEN_CALL_NAMES = frozenset(
    (
        "cancel_order",
        "cancel_orders",
        "create_api_key",
        "create_order",
        "create_or_derive_api_creds",
        "derive_api_key",
        "get_balance_allowance",
        "get_order",
        "get_orders",
        "post_order",
        "post_orders",
        "set_api_creds",
    ),
)

FORBIDDEN_LIVE_IDENTIFIER_FRAGMENTS = (
    "apikey",
    "apicreds",
    "apisecret",
    "authenticator",
    "clobclient",
    "createorder",
    "deriveapikey",
    "ethaccount",
    "privatekey",
    "signer",
    "wallet",
)


def _team_module_paths() -> tuple[Path, ...]:
    paths = set(TEAM_MODULE_ROOT.glob("team_*.py"))
    paths.update(TEAM_MODULE_ROOT.glob("*_team.py"))
    paths.update(
        TEAM_MODULE_ROOT / module_name
        for module_name in ADDITIONAL_STATIC_TEAM_MODULE_NAMES
    )
    return tuple(sorted(paths))


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append("." * node.level + (node.module or ""))
    return tuple(modules)


def _imported_names(tree: ast.AST) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name.rsplit(".", 1)[-1])
                if alias.asname is not None:
                    names.append(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.append(alias.name)
                if alias.asname is not None:
                    names.append(alias.asname)
    return tuple(names)


def _matches_module_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def _normal_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _identifier_names(tree: ast.AST) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.append(node.name)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.append(node.arg)
        elif isinstance(node, ast.alias):
            names.append(node.name.rsplit(".", 1)[-1])
            if node.asname is not None:
                names.append(node.asname)
    return tuple(names)


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _is_float_type_check(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Name)
        and node.func.id == "isinstance"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == "float"
    )


def _float_violations(path: Path, tree: ast.AST) -> tuple[str, ...]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and type(node.value) is float:
            violations.append(f"{path.name}:{node.lineno} float literal")
        elif isinstance(node, ast.Call):
            call_name = _call_name(node)
            if call_name == "float" and not (
                path.name == PAPER_GUARD_MODULE_NAME and _is_float_type_check(node)
            ):
                violations.append(f"{path.name}:{node.lineno} float constructor")
    return tuple(violations)


def test_team_modules_exist_and_are_discovered_by_static_scope():
    assert _team_module_paths()
    assert TEAM_MODULE_ROOT / "team_forecast_packet.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "team_paper_guard.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "commodities_gold_team.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "commodities_oil_team.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "crypto_btc_team.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "crypto_eth_team.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "equity_indices_team.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "macro_rates_team.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "politics_team.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "sports_basketball_team.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "sports_other_team.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "sports_soccer_team.py" in _team_module_paths()
    assert TEAM_MODULE_ROOT / "supabase_team_forecast_config.py" in _team_module_paths()


def test_team_modules_do_not_import_live_trading_auth_or_order_surfaces():
    failures = []
    forbidden_prefixes = FORBIDDEN_IMPORT_PREFIXES + FORBIDDEN_INTERNAL_IMPORT_PREFIXES
    for path in _team_module_paths():
        for module_name in _imported_modules(_parse_module(path)):
            if any(
                _matches_module_prefix(module_name, forbidden)
                for forbidden in forbidden_prefixes
            ):
                failures.append(f"{path.name}: {module_name}")

    assert not failures


def test_only_allowlisted_team_psycopg_adapters_import_psycopg():
    failures = []
    for path in _team_module_paths():
        tree = _parse_module(path)
        for module_name in _imported_modules(tree):
            if module_name == "psycopg" or module_name.startswith("psycopg."):
                if path.name not in PSYCOPG_MODULE_NAMES:
                    failures.append(f"{path.name}: {module_name}")

    assert not failures


def test_team_modules_do_not_import_polymarket_execution_order_clients():
    failures = []
    for path in _team_module_paths():
        imported_forbidden_names = (
            set(_imported_names(_parse_module(path))) & FORBIDDEN_POLYMARKET_CLIENT_NAMES
        )
        for imported_name in sorted(imported_forbidden_names):
            failures.append(f"{path.name}: {imported_name}")

    assert not failures


def test_team_modules_do_not_call_polymarket_order_or_auth_clients():
    failures = []
    for path in _team_module_paths():
        tree = _parse_module(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            call_name = _call_name(node)
            if call_name in FORBIDDEN_CALL_NAMES:
                failures.append(f"{path.name}:{node.lineno} {call_name}")

    assert not failures


def test_team_modules_do_not_define_live_trading_auth_or_order_identifiers():
    failures = []
    for path in _team_module_paths():
        if path.name == PAPER_GUARD_MODULE_NAME:
            continue
        for name in _identifier_names(_parse_module(path)):
            normalized = _normal_identifier(name)
            for fragment in FORBIDDEN_LIVE_IDENTIFIER_FRAGMENTS:
                if fragment in normalized:
                    failures.append(f"{path.name}: {name}")

    assert not failures


def test_team_modules_do_not_use_float_constructor_or_durable_float_literals():
    failures = []
    for path in _team_module_paths():
        failures.extend(_float_violations(path, _parse_module(path)))

    assert not failures


def test_json_ready_no_floats_rejects_floats_at_any_depth():
    with pytest.raises(ValueError, match="JSON value must not be a float"):
        json_ready_no_floats(0.5)

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        json_ready_no_floats({"outer": [{"inner": 0.5}]})

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_execution_reconciliation_health_gate.py"
)

EXPECTED_EXPORTS = (
    "DEFAULT_PAPER_EXECUTION_RECONCILIATION_HEALTH_GATE_CONFIG_VERSION",
    "PaperExecutionReconciliationHealthGateConfig",
    "PaperExecutionReconciliationHealthGateReasonCodeCount",
    "PaperExecutionReconciliationHealthGateReport",
    "build_paper_execution_reconciliation_health_gate_report",
)
EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.paper_execution_reconciliation": {
        "PaperExecutionReconciliationReport",
    },
}
ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "collections",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.paper_execution_reconciliation",
}
FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
    "asyncio",
    "bs4",
    "clob_client",
    "cloudscraper",
    "curl_cffi",
    "eth_account",
    "eth_keys",
    "http",
    "httpx",
    "importlib",
    "json",
    "mechanize",
    "os",
    "pathlib",
    "playwright",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.auth",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.paper_execution_reconciliation_db_row",
    "polymarket_alpha_lab.paper_execution_reconciliation_psycopg",
    "polymarket_alpha_lab.paper_execution_reconciliation_store",
    "polymarket_alpha_lab.wallet",
    "py_clob_client",
    "requests",
    "requests_html",
    "runpy",
    "scrapy",
    "selenium",
    "socket",
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
    "approve",
    "auth",
    "authenticate",
    "broker",
    "browser",
    "client",
    "credential",
    "dbrow",
    "dsn",
    "env",
    "fetch",
    "filesystem",
    "http",
    "key",
    "live",
    "network",
    "openfile",
    "privatekey",
    "psycopg",
    "request",
    "secret",
    "sign",
    "signature",
    "socket",
    "submit",
    "tablename",
    "trade",
    "wallet",
    "websocket",
}
ALLOWED_FORBIDDEN_NAME_MATCHES = {
    "configversion",
    "latestsourceageseconds",
    "maxlatestsourceageseconds",
    "paperexecutionreconciliationhealthgateconfig",
    "paperexecutionreconciliationhealthgatereasoncodecount",
    "paperexecutionreconciliationhealthgatereport",
    "readonly",
    "sourcereports",
}
FORBIDDEN_CALL_NAMES = {
    "__import__",
    "compile",
    "connect",
    "eval",
    "exec",
    "input",
    "open",
    "print",
    "read",
    "write",
}
BANNED_SOURCE_STRING_TOKENS = {
    "auth",
    "approve",
    "dsn",
    "live",
    "network",
    "private",
    "secret",
    "submit",
    "wallet",
}


def parse_module() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def imported_modules(tree: ast.Module) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


def imported_first_party_symbols(tree: ast.Module) -> dict[str, set[str]]:
    symbols: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in EXPECTED_FIRST_PARTY_IMPORTS:
            symbols.setdefault(node.module, set()).update(alias.name for alias in node.names)
    return symbols


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


def test_health_gate_imports_only_allowed_dependencies() -> None:
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert any(
            module_matches_prefix(module_name, allowed)
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_health_gate_does_not_import_forbidden_surfaces() -> None:
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_health_gate_uses_only_allowed_first_party_symbols() -> None:
    tree = parse_module()
    assert imported_first_party_symbols(tree) == EXPECTED_FIRST_PARTY_IMPORTS


def test_health_gate_exports_only_report_api() -> None:
    tree = parse_module()
    assert module_exports(tree) == EXPECTED_EXPORTS


def test_health_gate_defines_no_live_or_io_names() -> None:
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


def test_health_gate_does_not_perform_io_dynamic_execution_or_live_calls() -> None:
    tree = parse_module()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALL_NAMES, node.func.id
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in FORBIDDEN_CALL_NAMES, node.func.attr


def test_health_gate_source_strings_do_not_reference_forbidden_live_surfaces() -> None:
    tree = parse_module()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        normalized = normalize_identifier(node.value)
        for token in BANNED_SOURCE_STRING_TOKENS:
            assert token not in normalized, (node.value, token)

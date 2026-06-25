from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_autonomous_investment_ledger.py"
)

EXPECTED_EXPORTS = (
    "DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_CONFIG_VERSION",
    "PaperAutonomousInvestmentLedgerConfig",
    "PaperAutonomousInvestmentLedgerEntry",
    "PaperAutonomousInvestmentLedgerReasonCodeCount",
    "PaperAutonomousInvestmentLedgerReport",
    "build_paper_autonomous_investment_ledger_report",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.paper_broker",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
    "asyncio",
    "clob_client",
    "cloudscraper",
    "curl_cffi",
    "eth_account",
    "eth_keys",
    "http",
    "httpx",
    "json",
    "os",
    "pathlib",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.positions",
    "py_clob_client",
    "requests",
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
    "auth",
    "authenticate",
    "cancelorder",
    "client",
    "credential",
    "fetch",
    "golive",
    "http",
    "network",
    "orderbook",
    "orderpayload",
    "orderplacement",
    "placeorder",
    "privatekey",
    "sdk",
    "signing",
    "signorder",
    "submitorder",
    "wallet",
    "websocket",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
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
    "paperbrokerexecutionrecord",
    "readonly",
    "submittedcount",
    "submittedrecords",
    "totalsubmittednotional",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module() -> ast.Module:
    assert MODULE_PATH.exists(), f"{MODULE_PATH} is missing"
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


def test_paper_autonomous_investment_ledger_imports_only_allowed_dependencies() -> None:
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_paper_autonomous_investment_ledger_does_not_import_live_surfaces() -> None:
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_paper_autonomous_investment_ledger_exports_exact_reducer_api() -> None:
    assert module_exports(parse_module()) == EXPECTED_EXPORTS


def test_paper_autonomous_investment_ledger_defines_no_forbidden_surfaces() -> None:
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


def test_paper_autonomous_investment_ledger_has_no_io_or_dynamic_execution() -> None:
    tree = parse_module()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALL_NAMES, node.func.id
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in FORBIDDEN_CALL_NAMES, node.func.attr

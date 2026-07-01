"""Phase 1 live-surface guard for CLI/runner/paper orchestration modules.

This focused guard keeps the Phase 1 surfaces paper-only/report-only/read-only:
no live trading clients, auth/private-key/wallet handling, or order mutation
APIs may be imported or called from the checked modules.
"""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "polymarket_alpha_lab"

GUARDED_MODULES = (
    SOURCE_ROOT / "cli.py",
    SOURCE_ROOT / "runner.py",
    SOURCE_ROOT / "strategy_cycle.py",
    SOURCE_ROOT / "paper_execution.py",
    SOURCE_ROOT / "paper_broker.py",
)

FORBIDDEN_IMPORT_MODULES = {
    "clob_client",
    "py_clob_client",
    "polymarket_clob_client",
    "polymarket_clob_client.client",
}

FORBIDDEN_IMPORT_PREFIXES = (
    "clob_client.",
    "py_clob_client.",
    "polymarket_clob_client.",
)

FORBIDDEN_CALL_NAMES = {
    "approve",
    "authenticate",
    "cancel",
    "cancel_order",
    "create_order",
    "delete_order",
    "execute_order",
    "place_order",
    "replace_order",
    "route_order",
    "sign",
    "sign_order",
    "submit_order",
}

FORBIDDEN_IDENTIFIER_FRAGMENTS = {
    "apikey",
    "apitoken",
    "auth",
    "authorization",
    "clobclient",
    "credential",
    "liveexecution",
    "orderclient",
    "orderplacement",
    "orderrequest",
    "placeorder",
    "polymarketclobclient",
    "privatekey",
    "pyclobclient",
    "signorder",
    "submitorder",
    "wallet",
}

# These modules already carry paper-only documentation/redaction vocabulary that
# must stay explicit. Keep this whitelist narrow and line-bound so new live
# surface mentions are reviewed instead of silently accepted.
ALLOWED_STRING_LITERAL_TOKENS_BY_MODULE = {
    "cli.py": {
        "auth",
        "authorization",
        "private_key",
        "wallet",
    },
    "runner.py": {
        "auth",
        "private keys",
        "wallet",
        "wallets",
    },
    "strategy_cycle.py": {
        "live",
        "wallet",
    },
    "paper_execution.py": {
        "wallet",
    },
    "paper_broker.py": {
        "authenticate",
        "private keys",
        "sign",
    },
}

ALLOWED_IDENTIFIER_NAMES_BY_MODULE = {
    "cli.py": {
        "api_token",
        "llm_api_token",
    },
    "runner.py": set(),
    "strategy_cycle.py": set(),
    "paper_execution.py": set(),
    "paper_broker.py": set(),
}

FORBIDDEN_STRING_TOKENS = {
    "cancel_order",
    "clob_client",
    "create_order",
    "live trading",
    "order mutation",
    "polymarket_clob_client",
    "private_key",
    "py_clob_client",
    "wallet",
}


def _normalized_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return modules


def _call_name(node: ast.Call) -> str | None:
    function = node.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return None


def _identifier_names(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.append(node.arg)
        elif isinstance(node, ast.alias):
            names.append(node.name)
            if node.asname is not None:
                names.append(node.asname)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
    return names


def _line_for_node(source_lines: list[str], node: ast.AST) -> str:
    line_number = getattr(node, "lineno", 0)
    if line_number < 1 or line_number > len(source_lines):
        return ""
    return source_lines[line_number - 1].strip()


def _allowed_literal_context(path: Path, source_lines: list[str], node: ast.AST) -> bool:
    line_index = getattr(node, "lineno", 1) - 1
    start = max(0, line_index - 40)
    context = "\n".join(source_lines[start : line_index + 1]).lower()
    if path.name == "cli.py":
        return (
            "_redact_keyed_sensitive_fields" in context
            or "forbidden_fragments" in context
        )
    return False


def test_phase1_guarded_modules_are_the_expected_live_surface_boundary() -> None:
    assert tuple(path.name for path in GUARDED_MODULES) == (
        "cli.py",
        "runner.py",
        "strategy_cycle.py",
        "paper_execution.py",
        "paper_broker.py",
    )
    for path in GUARDED_MODULES:
        assert path.exists(), path


def test_phase1_modules_do_not_import_live_trading_clients() -> None:
    for path in GUARDED_MODULES:
        for module_name in _imported_modules(_parse(path)):
            assert module_name not in FORBIDDEN_IMPORT_MODULES, (path, module_name)
            assert not module_name.startswith(FORBIDDEN_IMPORT_PREFIXES), (
                path,
                module_name,
            )


def test_phase1_modules_do_not_call_live_order_mutation_or_auth_surfaces() -> None:
    for path in GUARDED_MODULES:
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            call_name = _call_name(node)
            assert call_name not in FORBIDDEN_CALL_NAMES, (path, call_name)


def test_phase1_modules_do_not_define_live_auth_wallet_identifiers() -> None:
    for path in GUARDED_MODULES:
        tree = _parse(path)
        allowed_names = ALLOWED_IDENTIFIER_NAMES_BY_MODULE[path.name]
        for name in _identifier_names(tree):
            if name in allowed_names:
                continue
            normalized_name = _normalized_identifier(name)
            for fragment in FORBIDDEN_IDENTIFIER_FRAGMENTS:
                assert fragment not in normalized_name, (path, name, fragment)


def test_phase1_modules_only_use_whitelisted_live_surface_text_mentions() -> None:
    for path in GUARDED_MODULES:
        source_lines = path.read_text(encoding="utf-8").splitlines()
        allowed_tokens = ALLOWED_STRING_LITERAL_TOKENS_BY_MODULE[path.name]
        for node in ast.walk(_parse(path)):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            literal = node.value.lower()
            line = _line_for_node(source_lines, node)
            for token in FORBIDDEN_STRING_TOKENS:
                if token not in literal:
                    continue
                assert token in allowed_tokens, (path, node.lineno, token, line)
                assert (
                    "_redact" in line.lower()
                    or _allowed_literal_context(path, source_lines, node)
                    or "paper" in literal
                ), (
                    path,
                    node.lineno,
                    token,
                    line,
                )

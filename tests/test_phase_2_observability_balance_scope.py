from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "phase_2_observability_balance.py"
)

ALLOWED_PROJECT_IMPORTS = {
    "polymarket_alpha_lab.phase_2_observability_state",
}

ALLOWED_STDLIB_IMPORTS = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
}

FORBIDDEN_IMPORT_FRAGMENTS = {
    "api",
    "auth",
    "browser",
    "client",
    "click",
    "clob",
    "dotenv",
    "exchange",
    "http",
    "io",
    "key",
    "network",
    "order",
    "os",
    "path",
    "request",
    "socket",
    "subprocess",
    "sys",
    "urllib",
    "wallet",
    "web",
}

FORBIDDEN_NAME_FRAGMENTS = {
    "advice",
    "alias",
    "auth",
    "builtins",
    "cli",
    "client",
    "command",
    "dynamic",
    "eval",
    "exec",
    "filesystem",
    "getattr",
    "globals",
    "importlib",
    "locals",
    "network",
    "open",
    "order",
    "rank",
    "recommend",
    "request",
    "shell",
    "socket",
    "subprocess",
    "trade",
    "wallet",
    "write",
}

FORBIDDEN_EXACT_NAMES = {
    "io",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "getattr",
    "globals",
    "hasattr",
    "input",
    "locals",
    "open",
    "print",
    "rank",
    "read",
    "recommend",
    "setattr",
    "write",
}

FORBIDDEN_ATTR_NAMES = {
    "auth",
    "client",
    "connect",
    "delete",
    "fetch",
    "get",
    "list_markets",
    "open",
    "order",
    "post",
    "rank",
    "read",
    "recommend",
    "request",
    "send",
    "sign",
    "submit",
    "wallet",
    "write",
}


def _normalized(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in "".join(
            character.lower() if character.isalnum() else " "
            for character in value
        ).split()
        if token
    }


def _tree() -> ast.AST:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def test_phase_2_observability_balance_import_scope_is_pure_phase_2_memory_only():
    imported_modules: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
            for alias in node.names:
                assert alias.asname is None, (node.module, alias.name, alias.asname)

    project_imports = {
        module
        for module in imported_modules
        if module.startswith("polymarket_alpha_lab.")
    }
    assert project_imports == ALLOWED_PROJECT_IMPORTS
    for module in imported_modules:
        if module.startswith("polymarket_alpha_lab."):
            continue
        top_level = module.split(".", 1)[0]
        assert top_level in ALLOWED_STDLIB_IMPORTS, module
        normalized_module = _normalized(module)
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
            assert _normalized(fragment) not in normalized_module, (module, fragment)


def test_phase_2_observability_balance_has_no_forbidden_names_calls_aliases_or_escapes():
    tree = _tree()

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                assert alias.asname is None, (alias.name, alias.asname)
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in FORBIDDEN_CALL_NAMES, callee_name
            assert not (
                isinstance(node.func, ast.Name) and node.func.id == "object"
            ), "object() dynamic escape"
        elif isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_ATTR_NAMES, node.attr
        elif isinstance(node, ast.Name):
            normalized_name = _normalized(node.id)
            assert normalized_name not in FORBIDDEN_EXACT_NAMES, node.id
            for fragment in FORBIDDEN_NAME_FRAGMENTS:
                assert _normalized(fragment) not in normalized_name, (node.id, fragment)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value_tokens = _tokens(node.value)
            assert not (value_tokens & FORBIDDEN_EXACT_NAMES), node.value
            for fragment in FORBIDDEN_NAME_FRAGMENTS:
                assert _normalized(fragment) not in value_tokens, (
                    node.value,
                    fragment,
                )

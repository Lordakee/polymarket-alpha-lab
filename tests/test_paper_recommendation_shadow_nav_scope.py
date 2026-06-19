import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_recommendation_shadow_nav.py"
)

ALLOWED_IMPORTS = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
}

FORBIDDEN_NAME_FRAGMENTS = (
    "auth",
    "authenticate",
    "client",
    "credential",
    "key",
    "live",
    "network",
    "order",
    "place",
    "request",
    "route",
    "sign",
    "submit",
    "trade",
    "wallet",
)

FORBIDDEN_CALL_NAMES = {
    "append",
    "cancel",
    "connect",
    "delete",
    "execute",
    "fetch",
    "open",
    "place",
    "post",
    "read",
    "request",
    "send",
    "sign",
    "submit",
    "write",
}


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _tree() -> ast.AST:
    assert MODULE_PATH.exists(), f"missing module: {MODULE_PATH}"
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def test_shadow_nav_module_import_scope_is_memory_only_stdlib():
    tree = _tree()
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")

    assert modules
    for module in modules:
        assert module in ALLOWED_IMPORTS, module
        normalized = _normalize_identifier(module)
        for fragment in FORBIDDEN_NAME_FRAGMENTS:
            assert _normalize_identifier(fragment) not in normalized, (module, fragment)


def test_shadow_nav_module_has_no_live_or_mutating_operation_surface():
    tree = _tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in FORBIDDEN_CALL_NAMES, callee_name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            normalized = _normalize_identifier(node.name)
            for fragment in FORBIDDEN_NAME_FRAGMENTS:
                assert _normalize_identifier(fragment) not in normalized, (
                    node.name,
                    fragment,
                )
        elif isinstance(node, ast.Attribute):
            normalized = _normalize_identifier(node.attr)
            for fragment in FORBIDDEN_NAME_FRAGMENTS:
                assert _normalize_identifier(fragment) not in normalized, (
                    node.attr,
                    fragment,
                )

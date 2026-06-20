import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_recommendation_cycle_action_gate.py"
)
ALLOWED_STDLIB_IMPORTS = {
    "__future__",
    "collections",
    "dataclasses",
    "datetime",
    "typing",
}
ALLOWED_PROJECT_IMPORTS = {
    "polymarket_alpha_lab.paper_recommendation_cycle_review",
}
FORBIDDEN_IMPORT_FRAGMENTS = {
    "account",
    "api",
    "auth",
    "client",
    "db",
    "file",
    "http",
    "live",
    "network",
    "order",
    "private_key",
    "request",
    "sign",
    "urllib",
    "wallet",
}
FORBIDDEN_CALL_NAMES = {
    "connect",
    "delete",
    "execute",
    "fetch",
    "get",
    "list",
    "open",
    "post",
    "put",
    "read",
    "request",
    "send",
    "sign",
    "submit",
    "write",
}
FORBIDDEN_ATTR_NAMES = {
    "account",
    "auth",
    "cancel",
    "client",
    "connect",
    "delete",
    "execute",
    "fetch",
    "get",
    "list_markets",
    "open",
    "order",
    "post",
    "put",
    "read",
    "request",
    "send",
    "sign",
    "submit",
    "wallet",
    "write",
}


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _parse_module() -> ast.AST:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def _imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def test_cycle_action_gate_import_scope_is_pure_reducer_only():
    tree = _parse_module()

    for module in _imported_modules(tree):
        if module.startswith("polymarket_alpha_lab."):
            assert module in ALLOWED_PROJECT_IMPORTS
            continue
        top_level = module.split(".", 1)[0]
        assert top_level in ALLOWED_STDLIB_IMPORTS, module
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
            assert _normalize_identifier(fragment) not in _normalize_identifier(module), (
                module,
                fragment,
            )


def test_cycle_action_gate_has_no_db_cli_file_network_or_live_operations():
    tree = _parse_module()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in FORBIDDEN_CALL_NAMES, callee_name
        elif isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_ATTR_NAMES, node.attr

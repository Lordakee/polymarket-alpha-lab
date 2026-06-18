import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "phase_2_history_bundle.py"

EXPECTED_PROJECT_IMPORTS = {
    "polymarket_alpha_lab.phase_2_evidence_snapshot",
    "polymarket_alpha_lab.phase_2_evidence_snapshot_transition",
    "polymarket_alpha_lab.phase_2_evidence_snapshot_trend",
}
ALLOWED_STDLIB_IMPORTS = {
    "__future__",
    "dataclasses",
    "datetime",
}
FORBIDDEN_IMPORT_FRAGMENTS = {
    "advice",
    "api",
    "auth",
    "client",
    "cli",
    "http",
    "journal",
    "network",
    "order",
    "private_key",
    "rank",
    "recommend",
    "request",
    "urllib",
    "wallet",
}
FORBIDDEN_NAMES = {
    "__import__",
    "advice",
    "auth",
    "client",
    "eval",
    "exec",
    "getattr",
    "input",
    "open",
    "order",
    "print",
    "rank",
    "read",
    "recommend",
    "request",
    "setattr",
    "wallet",
    "write",
}
FORBIDDEN_ATTR_NAMES = FORBIDDEN_NAMES | {
    "connect",
    "delete",
    "fetch",
    "get",
    "list_markets",
    "patch",
    "post",
    "put",
    "send",
    "sign",
    "submit",
}
FORBIDDEN_CALL_NAMES = FORBIDDEN_NAMES | FORBIDDEN_ATTR_NAMES
FORBIDDEN_STRING_FRAGMENTS = {
    "__import__",
    "advice",
    "auth",
    "client",
    "eval",
    "exec",
    "getattr",
    "open",
    "order",
    "paper only must be false",
    "rank",
    "recommend",
    "request",
    "setattr",
    "wallet",
}


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _string_mentions_forbidden_token(value: str, fragment: str) -> bool:
    if fragment.startswith("__") and fragment.endswith("__"):
        return fragment in value
    tokens = tuple(
        token
        for token in "".join(
            character.lower() if character.isalnum() or character == "_" else " "
            for character in value
        ).split()
        if token
    )
    return fragment in tokens


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


def _import_aliases(tree: ast.AST) -> tuple[str, ...]:
    aliases: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            aliases.extend(alias.asname or alias.name.rsplit(".", maxsplit=1)[-1] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            aliases.extend(alias.asname or alias.name for alias in node.names)
    return tuple(aliases)


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def test_phase_2_history_bundle_import_scope():
    tree = _parse_module()
    modules = _imported_modules(tree)
    project_modules = {
        module for module in modules if module.startswith("polymarket_alpha_lab.")
    }

    assert project_modules == EXPECTED_PROJECT_IMPORTS
    for module in modules:
        if module.startswith("polymarket_alpha_lab."):
            continue
        top_level = module.split(".", maxsplit=1)[0]
        assert top_level in ALLOWED_STDLIB_IMPORTS, module
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
            assert _normalize_identifier(fragment) not in _normalize_identifier(module), (
                module,
                fragment,
            )
    for alias in _import_aliases(tree):
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
            assert _normalize_identifier(fragment) not in _normalize_identifier(alias), (
                alias,
                fragment,
            )


def test_phase_2_history_bundle_operation_scope():
    tree = _parse_module()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee_name = _call_name(node)
            assert callee_name not in FORBIDDEN_CALL_NAMES, callee_name
        elif isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_ATTR_NAMES, node.attr
        elif isinstance(node, ast.Name):
            assert node.id not in FORBIDDEN_NAMES, node.id


def test_phase_2_history_bundle_dynamic_escape_scope():
    tree = _parse_module()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for fragment in FORBIDDEN_STRING_FRAGMENTS:
                assert not _string_mentions_forbidden_token(node.value, fragment), (
                    node.value,
                    fragment,
                )

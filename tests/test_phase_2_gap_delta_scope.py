import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "phase_2_gap_delta.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"

EXPECTED_EXPORTS = (
    "PaperPhase2GapDeltaConfig",
    "PaperPhase2GapDeltaReport",
    "PaperPhase2GapDeltaRow",
    "build_paper_phase_2_gap_delta_report",
)
ALLOWED_PROJECT_IMPORTS = {
    "polymarket_alpha_lab.phase_2_evidence_snapshot",
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
    "dotenv",
    "http",
    "io",
    "journal",
    "network",
    "order",
    "os",
    "path",
    "private",
    "rank",
    "recommend",
    "request",
    "socket",
    "subprocess",
    "urllib",
    "wallet",
    "web",
}
FORBIDDEN_NAME_FRAGMENTS = {
    "advice",
    "auth",
    "builtins",
    "client",
    "command",
    "credential",
    "download",
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
    "package",
    "rank",
    "recommend",
    "request",
    "shell",
    "socket",
    "subprocess",
    "wallet",
    "write",
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
FORBIDDEN_ATTR_NAMES = FORBIDDEN_CALL_NAMES | {
    "auth",
    "client",
    "connect",
    "delete",
    "fetch",
    "get",
    "list_markets",
    "order",
    "patch",
    "post",
    "put",
    "rank",
    "recommend",
    "request",
    "send",
    "sign",
    "submit",
    "wallet",
}


def _normalized(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in "".join(
            character.lower() if character.isalnum() or character == "_" else " "
            for character in value
        ).split()
        if token
    }


def _tree() -> ast.AST:
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


def _module_exports(tree: ast.AST) -> tuple[str, ...]:
    assigned_exports = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def test_phase_2_gap_delta_import_scope_is_pure_phase_2_memory_only():
    modules = _imported_modules(_tree())
    project_modules = {
        module for module in modules if module.startswith("polymarket_alpha_lab.")
    }

    assert project_modules == ALLOWED_PROJECT_IMPORTS
    for module in modules:
        if module.startswith("polymarket_alpha_lab."):
            continue
        top_level = module.split(".", maxsplit=1)[0]
        assert top_level in ALLOWED_STDLIB_IMPORTS, module
        normalized_module = _normalized(module)
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
            assert _normalized(fragment) not in normalized_module, (module, fragment)


def test_phase_2_gap_delta_public_exports_are_exact_report_api():
    assert _module_exports(_tree()) == EXPECTED_EXPORTS


def test_phase_2_gap_delta_has_no_forbidden_names_calls_aliases_or_escapes():
    tree = _tree()

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                assert alias.asname is None, (alias.name, alias.asname)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node)
            assert call_name not in FORBIDDEN_CALL_NAMES, call_name
            assert not (
                isinstance(node.func, ast.Name) and node.func.id == "object"
            ), "object dynamic escape"
        elif isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_ATTR_NAMES, node.attr
        elif isinstance(node, ast.Name):
            normalized_name = _normalized(node.id)
            for fragment in FORBIDDEN_NAME_FRAGMENTS:
                assert _normalized(fragment) not in normalized_name, (node.id, fragment)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value_tokens = _tokens(node.value)
            for fragment in FORBIDDEN_NAME_FRAGMENTS:
                assert _normalized(fragment) not in value_tokens, (
                    node.value,
                    fragment,
                )


def test_phase_2_gap_delta_is_not_exported_from_package_root():
    package_source = PACKAGE_ROOT_PATH.read_text(encoding="utf-8")
    package_tree = ast.parse(package_source)

    assert "polymarket_alpha_lab.phase_2_gap_delta" not in _imported_modules(
        package_tree,
    )
    for export_name in EXPECTED_EXPORTS:
        assert export_name not in package_source

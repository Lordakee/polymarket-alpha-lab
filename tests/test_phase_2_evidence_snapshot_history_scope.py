import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "phase_2_evidence_snapshot_history.py"
)
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
EXPECTED_EXPORTS = (
    "PaperPhase2EvidenceSnapshotHistoryConfig",
    "build_paper_phase_2_evidence_snapshot_history",
)

ALLOWED_PROJECT_IMPORTS = {
    "polymarket_alpha_lab.forecast_calibration",
    "polymarket_alpha_lab.phase_2_evidence_snapshot",
    "polymarket_alpha_lab.strategy_segment_summary",
}

ALLOWED_STDLIB_IMPORTS = {
    "__future__",
    "dataclasses",
    "datetime",
}

FORBIDDEN_FRAGMENTS = {
    "advice",
    "auth",
    "cli",
    "http",
    "key",
    "live",
    "network",
    "order",
    "private",
    "rank",
    "recommend",
    "request",
    "token",
    "wallet",
}
FORBIDDEN_CALLS = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "getattr",
    "globals",
    "input",
    "locals",
    "open",
    "print",
    "setattr",
}
FORBIDDEN_STRING_TOKENS = {
    "advice",
    "auth",
    "cli",
    "http",
    "key",
    "live",
    "network",
    "order",
    "private",
    "rank",
    "recommend",
    "request",
    "wallet",
}


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _parse_module() -> ast.AST:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def _assert_no_forbidden_operations(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            normalized_string = _normalize_identifier(node.value)
            for token in FORBIDDEN_STRING_TOKENS:
                assert token not in normalized_string, (node.value, token)
        elif isinstance(node, ast.Name):
            normalized_name = _normalize_identifier(node.id)
            for fragment in FORBIDDEN_FRAGMENTS:
                assert fragment not in normalized_name, (node.id, fragment)
        elif isinstance(node, ast.Attribute):
            normalized_attribute = _normalize_identifier(node.attr)
            for fragment in FORBIDDEN_FRAGMENTS:
                assert fragment not in normalized_attribute, (node.attr, fragment)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in FORBIDDEN_CALLS, callee_name
            normalized_callee = _normalize_identifier(callee_name)
            for fragment in FORBIDDEN_FRAGMENTS:
                assert fragment not in normalized_callee, (callee_name, fragment)


def _imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def test_phase_2_evidence_snapshot_history_import_scope_is_pure_phase_2():
    tree = _parse_module()
    imported_modules = _imported_modules(tree)
    project_imports = {
        module
        for module in imported_modules
        if module.startswith("polymarket_alpha_lab.")
    }

    assert project_imports == ALLOWED_PROJECT_IMPORTS
    for module in imported_modules:
        if module.startswith("polymarket_alpha_lab."):
            continue
        assert module.split(".", 1)[0] in ALLOWED_STDLIB_IMPORTS, module
        normalized_module = _normalize_identifier(module)
        for fragment in FORBIDDEN_FRAGMENTS:
            assert fragment not in normalized_module, (module, fragment)


def test_phase_2_evidence_snapshot_history_has_no_forbidden_operations():
    tree = _parse_module()
    _assert_no_forbidden_operations(tree)


def test_phase_2_evidence_snapshot_history_forbidden_operation_guard_catches_escape_hatches():
    tree = ast.parse(
        """
def bad(value):
    print(value)
    open('/tmp/phase-2-history', 'w')
    __import__('os')
""",
    )

    try:
        _assert_no_forbidden_operations(tree)
    except AssertionError:
        return
    raise AssertionError("forbidden operation guard accepted escape hatches")


def test_package_root_does_not_export_phase_2_evidence_snapshot_history_names():
    tree = ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8"))
    assigned_exports = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    for name in EXPECTED_EXPORTS:
        assert name not in tuple(assigned_exports)

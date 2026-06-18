from __future__ import annotations

import ast
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "phase_2_observability_trends.py"
)
PACKAGE_INIT_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "polymarket_alpha_lab" / "__init__.py"
)

FORBIDDEN_NAME_PARTS = (
    "auth",
    "wallet",
    "order",
    "rank",
    "recommend",
    "advice",
    "cli",
    "network",
)
FORBIDDEN_MODULES = (
    "argparse",
    "asyncio",
    "click",
    "httpx",
    "json",
    "os",
    "pathlib",
    "requests",
    "socket",
    "subprocess",
    "sys",
    "urllib",
)
FORBIDDEN_CALLS = (
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
)
FORBIDDEN_STRING_TOKENS = (
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
)
REQUIRED_DECORATED_CLASSES = {
    "PaperPhase2ObservabilityTrendsConfig",
    "PaperPhase2ObservabilityTrendsReport",
}


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _module_tree() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def _assert_no_forbidden_operations(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                normalized_alias = _normalize_identifier(alias.name)
                for fragment in FORBIDDEN_NAME_PARTS:
                    assert fragment not in normalized_alias, (alias.name, fragment)
                if alias.asname is not None:
                    normalized_asname = _normalize_identifier(alias.asname)
                    for fragment in FORBIDDEN_NAME_PARTS:
                        assert fragment not in normalized_asname, (alias.asname, fragment)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                normalized_module = _normalize_identifier(node.module)
                for fragment in FORBIDDEN_NAME_PARTS:
                    assert fragment not in normalized_module, (node.module, fragment)
            for alias in node.names:
                normalized_alias = _normalize_identifier(alias.name)
                for fragment in FORBIDDEN_NAME_PARTS:
                    assert fragment not in normalized_alias, (alias.name, fragment)
                if alias.asname is not None:
                    normalized_asname = _normalize_identifier(alias.asname)
                    for fragment in FORBIDDEN_NAME_PARTS:
                        assert fragment not in normalized_asname, (alias.asname, fragment)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            normalized_value = _normalize_identifier(node.value)
            for token in FORBIDDEN_STRING_TOKENS:
                assert token not in normalized_value, (node.value, token)
        elif isinstance(node, ast.Name):
            normalized_name = _normalize_identifier(node.id)
            for fragment in FORBIDDEN_NAME_PARTS:
                assert fragment not in normalized_name, (node.id, fragment)
        elif isinstance(node, ast.Attribute):
            normalized_attribute = _normalize_identifier(node.attr)
            for fragment in FORBIDDEN_NAME_PARTS:
                assert fragment not in normalized_attribute, (node.attr, fragment)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in FORBIDDEN_CALLS, callee_name
            normalized_callee = _normalize_identifier(callee_name)
            for fragment in FORBIDDEN_NAME_PARTS:
                assert fragment not in normalized_callee, (callee_name, fragment)


def test_phase_2_observability_trends_file_exists_without_package_root_export():
    assert MODULE_PATH.exists()
    package_root_source = PACKAGE_INIT_PATH.read_text(encoding="utf-8")

    assert "phase_2_observability_trends" not in package_root_source
    assert "PaperPhase2ObservabilityTrends" not in package_root_source


def test_phase_2_observability_trends_scope_has_no_forbidden_imports_or_calls():
    tree = _module_tree()
    _assert_no_forbidden_operations(tree)

    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.append(node.module)

    for module_name in imported_modules:
        assert not any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_MODULES
        ), module_name


def test_phase_2_observability_trends_scope_guard_catches_escape_hatches():
    tree = ast.parse(
        """
from polymarket_alpha_lab.paper import PaperOrder

def bad(value):
    print(value)
    open('/tmp/phase-2-observability', 'w')
    __import__('os')
""",
    )

    try:
        _assert_no_forbidden_operations(tree)
    except AssertionError:
        return
    raise AssertionError("forbidden operation guard accepted escape hatches")


def test_phase_2_observability_trends_dataclasses_are_frozen_and_all_is_local():
    tree = _module_tree()
    decorated_classes: dict[str, ast.ClassDef] = {}

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and getattr(
                    decorator.func,
                    "id",
                    None,
                ) == "dataclass":
                    decorated_classes[node.name] = node

    assert set(decorated_classes) == REQUIRED_DECORATED_CLASSES

    for class_node in decorated_classes.values():
        dataclass_call = class_node.decorator_list[0]
        assert isinstance(dataclass_call, ast.Call)
        frozen_keywords = [
            keyword
            for keyword in dataclass_call.keywords
            if keyword.arg == "frozen"
        ]
        assert len(frozen_keywords) == 1
        assert isinstance(frozen_keywords[0].value, ast.Constant)
        assert frozen_keywords[0].value.value is True

    all_assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
    ]
    assert len(all_assignments) == 1
    assert isinstance(all_assignments[0].value, ast.Tuple)
    assert tuple(
        element.value
        for element in all_assignments[0].value.elts
        if isinstance(element, ast.Constant)
    ) == (
        "PaperPhase2ObservabilityTrendsConfig",
        "PaperPhase2ObservabilityTrendsReport",
        "build_paper_phase_2_observability_trends_report",
    )


def test_package_root_does_not_export_phase_2_observability_trends_names():
    package_root = ast.parse(PACKAGE_INIT_PATH.read_text(encoding="utf-8"))
    assigned_exports = None
    for node in ast.walk(package_root):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    for name in (
        "PaperPhase2ObservabilityTrendsConfig",
        "PaperPhase2ObservabilityTrendsReport",
        "build_paper_phase_2_observability_trends_report",
    ):
        assert name not in tuple(assigned_exports)

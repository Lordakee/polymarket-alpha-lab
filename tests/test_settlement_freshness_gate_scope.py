from __future__ import annotations

import ast
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "settlement_freshness_gate.py"
)

EXPECTED_EXPORTS = (
    "PaperSettlementFreshnessGateConfig",
    "PaperSettlementFreshnessGateRow",
    "PaperSettlementFreshnessGateReport",
    "build_paper_settlement_freshness_gate_report",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "typing",
    "polymarket_alpha_lab.outcome_freshness",
    "polymarket_alpha_lab.outcome_tracker",
}

FORBIDDEN_IMPORT_PREFIXES = (
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.runner",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.journal",
    "requests",
    "httpx",
    "web3",
)

FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS = (
    "rank",
    "recommend",
)


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module() -> ast.AST:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


def module_exports(tree: ast.AST) -> tuple[str, ...]:
    assigned_exports = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def public_export_fragment_matches(name: str) -> bool:
    normalized = normalize_identifier(name)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


def test_settlement_freshness_gate_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_settlement_freshness_gate_does_not_import_live_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_settlement_freshness_gate_public_exports_are_paper_report_api():
    tree = parse_module()
    assigned_exports = module_exports(tree)

    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        assert not public_export_fragment_matches(name), name


def test_settlement_freshness_gate_does_not_define_forbidden_public_names():
    tree = parse_module()
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

    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS:
        assert not any(normalize_identifier(fragment) in name for name in lowered), (
            fragment,
            lowered,
        )

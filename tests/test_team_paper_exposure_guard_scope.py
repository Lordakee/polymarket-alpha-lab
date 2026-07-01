from __future__ import annotations

import ast
from pathlib import Path


MODULE = Path("src/polymarket_alpha_lab/team_paper_exposure_guard.py")
PACKAGE_ROOT = Path("src/polymarket_alpha_lab/__init__.py")
PUBLIC_NAMES = (
    "TeamPaperExposureGuardConfig",
    "TeamPaperExposureInput",
    "TeamPaperExposureGuardRow",
    "TeamPaperExposureGuardReport",
    "build_team_paper_exposure_guard_report",
)


def _literal_all(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
                value = ast.literal_eval(node.value)
                return tuple(value)
    raise AssertionError("__all__ assignment not found")


def test_team_paper_exposure_guard_module_has_only_pure_diagnostic_surface():
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = []
    call_names = []
    attribute_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
    }
    assert _literal_all(tree) == PUBLIC_NAMES

    banned = {
        "approve",
        "auth",
        "cancel",
        "client",
        "commit",
        "connect",
        "cursor",
        "db",
        "delete",
        "env",
        "exchange",
        "execute",
        "httpx",
        "insert",
        "network",
        "open",
        "order",
        "persist",
        "place",
        "print",
        "psycopg",
        "replace",
        "requests",
        "rollback",
        "sign",
        "socket",
        "submit",
        "supabase",
        "trade",
        "update",
        "upsert",
        "urllib",
        "wallet",
    }
    lower_source = source.lower()
    for token in banned:
        assert token not in lower_source
    assert not (banned & set(name.lower() for name in call_names))
    assert not (banned & set(name.lower() for name in attribute_names))


def test_team_paper_exposure_guard_is_not_exported_from_package_root():
    source = PACKAGE_ROOT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    root_exports = _literal_all(tree)

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "polymarket_alpha_lab.team_paper_exposure_guard"
        ):
            raise AssertionError("team_paper_exposure_guard must stay module-local")

    assert "team_paper_exposure_guard" not in source
    assert not (set(PUBLIC_NAMES) & set(root_exports))

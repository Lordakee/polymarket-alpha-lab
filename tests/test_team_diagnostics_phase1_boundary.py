from __future__ import annotations

import ast
import importlib
from dataclasses import is_dataclass
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "src" / "polymarket_alpha_lab"
PACKAGE_INIT = PACKAGE_ROOT / "__init__.py"
CLI_MODULE = PACKAGE_ROOT / "cli.py"
PYPROJECT = REPO_ROOT / "pyproject.toml"

PHASE1_FLAG_NAMES = ("paper_only", "report_only", "readonly")

EXPECTED_MODULE_EXPORTS = {
    "team_diagnostics_bundle": {
        "TeamDiagnosticsBundleConfig",
        "TeamDiagnosticsBundleReport",
        "build_team_diagnostics_bundle_report",
    },
    "team_diagnostics_db_source": {
        "TeamDiagnosticsDbRows",
        "TeamDiagnosticsDbSourceRequest",
        "load_team_diagnostics_rows_from_env",
    },
    "team_cli_wiring": {
        "TeamDiagnosticsCliLoaders",
        "TeamDiagnosticsCliOutputRow",
        "TeamDiagnosticsCliRequest",
        "TeamDiagnosticsCliResult",
        "run_team_diagnostics_cli_request",
    },
    "team_diagnostics_cli_format": {
        "format_team_diagnostics_cli_lines",
        "format_team_diagnostics_cli_stdout",
    },
}
EXPECTED_FLAGGED_EXPORTS = {
    "TeamDiagnosticsBundleConfig",
    "TeamDiagnosticsBundleReport",
    "TeamDiagnosticsDbRows",
    "TeamDiagnosticsCliResult",
}

FORBIDDEN_DURABLE_IMPORT_PREFIXES = {
    "pymongo",
    "redis",
    "sqlalchemy",
    "sqlite3",
}
FORBIDDEN_LIVE_IMPORT_PREFIXES = {
    "clob_client",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "polymarket",
    "py_clob_client",
    "web3",
}
FORBIDDEN_FIRST_PARTY_IMPORT_PREFIXES = {
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.paper_broker",
    "polymarket_alpha_lab.paper_broker_psycopg",
    "polymarket_alpha_lab.paper_broker_store",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.paper_execution_reconciliation",
    "polymarket_alpha_lab.paper_order_lifecycle",
    "polymarket_alpha_lab.paper_trade_journal",
    "polymarket_alpha_lab.positions",
}
FORBIDDEN_PUBLIC_FRAGMENTS = {
    "account",
    "allowance",
    "apikey",
    "apisecret",
    "authentication",
    "authenticator",
    "balance",
    "cancel",
    "clob",
    "credential",
    "deriveapikey",
    "exchange",
    "livetrading",
    "mutation",
    "cancelorder",
    "ordercancel",
    "orderreplace",
    "orderrequest",
    "ordersigning",
    "ordersubmission",
    "privatekey",
    "replace",
    "secret",
    "signature",
    "signer",
    "signorder",
    "submit",
    "submitorder",
    "wallet",
}
FORBIDDEN_CALL_NAMES = {
    "cancel_order",
    "cancel_orders",
    "create_api_key",
    "create_order",
    "create_or_derive_api_creds",
    "derive_api_key",
    "get_balance_allowance",
    "get_order",
    "get_orders",
    "post_order",
    "post_orders",
    "set_api_creds",
    "sign_order",
    "submit_order",
}


def _module_path(module_name: str) -> Path:
    return PACKAGE_ROOT / f"{module_name}.py"


def _require_module_path(module_name: str) -> Path:
    path = _module_path(module_name)
    if not path.exists():
        pytest.fail(
            "Expected Phase 1 team diagnostics module at "
            f"src/polymarket_alpha_lab/{module_name}.py",
        )
    return path


def _require_import(module_name: str) -> object:
    import_name = f"polymarket_alpha_lab.{module_name}"
    try:
        return importlib.import_module(import_name)
    except ModuleNotFoundError as exc:
        raise AssertionError(
            f"Expected importable Phase 1 team diagnostics API at {import_name}",
        ) from exc


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _literal_all(tree: ast.Module, *, module_name: str) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            return tuple(value)
    pytest.fail(f"__all__ assignment not found in {module_name}.py")


def _imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
            modules.extend(alias.asname for alias in node.names if alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
            modules.extend(alias.asname for alias in node.names if alias.asname)
    return tuple(modules)


def _identifier_names(tree: ast.AST) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.append(node.name)
        elif isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.append(node.arg)
        elif isinstance(node, ast.alias):
            names.append(node.name.rsplit(".", 1)[-1])
            if node.asname is not None:
                names.append(node.asname)
    return tuple(names)


def _call_names(tree: ast.AST) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            names.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            names.append(node.func.attr)
    return tuple(names)


def _normal_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _matches_module_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def _exported_names(module: object, *, module_name: str) -> tuple[str, ...]:
    exports = getattr(module, "__all__", None)
    if exports is None:
        pytest.fail(f"{module_name} must define __all__")
    return tuple(exports)


def test_expected_team_diagnostics_modules_exist_with_public_exports() -> None:
    for module_name, expected_exports in EXPECTED_MODULE_EXPORTS.items():
        tree = _parse_module(_require_module_path(module_name))
        assigned_exports = set(_literal_all(tree, module_name=module_name))

        assert assigned_exports >= expected_exports
        for export_name in assigned_exports:
            normalized = _normal_identifier(export_name)
            assert not any(
                fragment in normalized for fragment in FORBIDDEN_PUBLIC_FRAGMENTS
            ), f"{module_name}: {export_name}"


def test_team_diagnostics_modules_import_no_live_or_forbidden_durable_dependencies() -> None:
    forbidden_prefixes = (
        FORBIDDEN_DURABLE_IMPORT_PREFIXES
        | FORBIDDEN_LIVE_IMPORT_PREFIXES
        | FORBIDDEN_FIRST_PARTY_IMPORT_PREFIXES
    )
    failures = []
    for module_name in EXPECTED_MODULE_EXPORTS:
        tree = _parse_module(_require_module_path(module_name))
        for imported_module in _imported_modules(tree):
            if any(
                _matches_module_prefix(imported_module, forbidden)
                for forbidden in forbidden_prefixes
            ):
                failures.append(f"{module_name}: {imported_module}")

    assert not failures


def test_team_diagnostics_modules_define_no_live_auth_wallet_or_order_identifiers() -> None:
    failures = []
    for module_name in EXPECTED_MODULE_EXPORTS:
        tree = _parse_module(_require_module_path(module_name))
        for name in _identifier_names(tree):
            normalized = _normal_identifier(name)
            for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
                if fragment in normalized:
                    failures.append(f"{module_name}: {name}")

    assert not sorted(set(failures))


def test_team_diagnostics_modules_call_no_live_order_or_auth_methods() -> None:
    forbidden_calls = {_normal_identifier(name) for name in FORBIDDEN_CALL_NAMES}
    failures = []
    for module_name in EXPECTED_MODULE_EXPORTS:
        tree = _parse_module(_require_module_path(module_name))
        for call_name in _call_names(tree):
            normalized = _normal_identifier(call_name)
            if normalized in forbidden_calls:
                failures.append(f"{module_name}: {call_name}")

    assert not failures


def test_team_diagnostics_public_objects_preserve_phase1_flags() -> None:
    for module_name, expected_exports in EXPECTED_MODULE_EXPORTS.items():
        module = _require_import(module_name)
        module_exports = set(_exported_names(module, module_name=module_name))
        assert module_exports >= expected_exports

        for export_name in module_exports:
            exported = getattr(module, export_name)
            annotations = getattr(exported, "__annotations__", {})
            if export_name in EXPECTED_FLAGGED_EXPORTS:
                assert is_dataclass(exported), f"{module_name}.{export_name}"
                for flag_name in PHASE1_FLAG_NAMES:
                    assert flag_name in annotations, (
                        f"{module_name}.{export_name}.{flag_name}"
                    )
                    assert getattr(exported, flag_name, True) is True, (
                        f"{module_name}.{export_name}.{flag_name} must default to True"
                    )
                continue

            declared_flags = set(annotations) & set(PHASE1_FLAG_NAMES)
            if declared_flags:
                assert declared_flags == set(PHASE1_FLAG_NAMES), (
                    f"{module_name}.{export_name} must declare all Phase 1 flags"
                )


def test_package_root_team_diagnostics_exports_remain_readonly_if_added() -> None:
    root = importlib.import_module("polymarket_alpha_lab")
    root_exports = set(getattr(root, "__all__", ()))

    for module_name, expected_exports in EXPECTED_MODULE_EXPORTS.items():
        module = _require_import(module_name)
        for export_name in expected_exports & root_exports:
            assert getattr(root, export_name) is getattr(module, export_name)

    for export_name in root_exports:
        normalized = _normal_identifier(export_name)
        if "teamdiagnostic" not in normalized:
            continue
        assert not any(
            fragment in normalized for fragment in FORBIDDEN_PUBLIC_FRAGMENTS
        ), export_name


def test_cli_surfaces_do_not_expose_live_team_diagnostics_verbs() -> None:
    forbidden_fragments = tuple(sorted(FORBIDDEN_PUBLIC_FRAGMENTS))
    surfaces = (
        ("pyproject.toml", PYPROJECT.read_text(encoding="utf-8")),
        ("cli.py", CLI_MODULE.read_text(encoding="utf-8")),
    )

    for file_name, source in surfaces:
        for line_number, line in enumerate(source.splitlines(), start=1):
            normalized = _normal_identifier(line)
            if "teamdiagnostic" not in normalized:
                continue
            assert not any(fragment in normalized for fragment in forbidden_fragments), (
                f"{file_name}:{line_number}"
            )

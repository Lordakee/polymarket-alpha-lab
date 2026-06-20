from __future__ import annotations

import ast
import dataclasses
import importlib
import inspect
import re
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "src" / "polymarket_alpha_lab"

TARGET_MODULE_NAMES = (
    "paper_recommendation_cycle_snapshot",
    "paper_recommendation_cycle_snapshot_db_row",
    "paper_recommendation_cycle_snapshot_log",
    "paper_recommendation_cycle_snapshot_store",
    "paper_recommendation_cycle_snapshot_trend",
    "strategy_cycle_snapshot_source",
)
NON_LOG_MODULE_NAMES = (
    "paper_recommendation_cycle_snapshot",
    "paper_recommendation_cycle_snapshot_trend",
)
SAFETY_DATACLASS_FIELDS = ("paper_only", "report_only", "readonly")

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "collections",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "hashlib",
    "json",
    "pathlib",
    "re",
    "typing",
    "polymarket_alpha_lab.json_recovery",
    "polymarket_alpha_lab.paper_recommendation_artifact_index",
    "polymarket_alpha_lab.paper_recommendation_cycle_snapshot",
    "polymarket_alpha_lab.paper_recommendation_cycle_snapshot_db_row",
    "polymarket_alpha_lab.paper_recommendation_pipeline",
    "polymarket_alpha_lab.strategy_cycle_recommendation_artifact_source",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
    "asyncio",
    "clob_client",
    "cloudscraper",
    "curl_cffi",
    "eth_account",
    "eth_keys",
    "http",
    "httpx",
    "mechanize",
    "os",
    "playwright",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.auth",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.exchange",
    "polymarket_alpha_lab.execution",
    "polymarket_alpha_lab.orders",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.runner",
    "polymarket_alpha_lab.trading",
    "py_clob_client",
    "requests",
    "requests_html",
    "scrapy",
    "selenium",
    "socket",
    "ssl",
    "subprocess",
    "urllib",
    "urllib3",
    "web3",
    "websocket",
    "websockets",
}

FORBIDDEN_NAME_FRAGMENTS = {
    "account",
    "apikey",
    "apitoken",
    "auth",
    "authenticate",
    "broker",
    "browser",
    "cancelorder",
    "clobclient",
    "client",
    "credential",
    "exchange",
    "fetch",
    "golive",
    "http",
    "live",
    "network",
    "orderbook",
    "orderbuilder",
    "orderpayload",
    "orderplacement",
    "placeorder",
    "privatekey",
    "sdk",
    "secret",
    "signature",
    "signmessage",
    "signorder",
    "submitorder",
    "tradeclient",
    "wallet",
    "websocket",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "cancel_order",
    "compile",
    "create_order",
    "delete",
    "eval",
    "exec",
    "fetch",
    "input",
    "login",
    "open",
    "patch",
    "place_order",
    "post",
    "print",
    "put",
    "read",
    "request",
    "send",
    "sign",
    "sign_message",
    "sign_order",
    "submit",
    "submit_order",
    "write",
}
LOCAL_LOG_IO_CALL_NAMES = {"open", "read", "write"}

FORBIDDEN_TEXT_FRAGMENTS = FORBIDDEN_NAME_FRAGMENTS | {
    "__import__",
    "cancel_order",
    "create_order",
    "eval",
    "exec",
    "login",
    "patch",
    "place_order",
    "post",
    "put",
    "request",
    "send",
    "sign_message",
    "sign_order",
    "submit_order",
}

ALLOWED_FORBIDDEN_NAME_MATCHES = {
    "jsonable",
    "readonly",
    "reportonly",
}
MODULE_ALLOWED_FORBIDDEN_NAME_MATCHES = {
    "paper_recommendation_cycle_snapshot_store": {"fetchall"},
}


def module_path(module_name: str) -> Path:
    return PACKAGE_ROOT / f"{module_name}.py"


def require_module_path(module_name: str) -> Path:
    path = module_path(module_name)
    if not path.exists():
        pytest.skip(f"{module_name} is not present yet")
    return path


def parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def absolute_import_module(current_module_name: str, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    assert node.level == 1, (current_module_name, ast.unparse(node))
    if node.module is None:
        return "polymarket_alpha_lab"
    return f"polymarket_alpha_lab.{node.module}"


def imported_modules(module_name: str, tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(absolute_import_module(module_name, node))
    return tuple(modules)


def collected_names(tree: ast.Module) -> set[str]:
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
    return names


def call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def public_api_names(module: ModuleType) -> tuple[str, ...]:
    explicit_exports = getattr(module, "__all__", None)
    if explicit_exports is not None:
        return tuple(explicit_exports)
    return tuple(
        sorted(
            name
            for name, value in vars(module).items()
            if is_public_module_member(name, value, module.__name__)
        ),
    )


def is_public_module_member(name: str, value: Any, module_name: str) -> bool:
    if name.startswith("_") or inspect.ismodule(value):
        return False
    owner_module = getattr(value, "__module__", None)
    if owner_module is not None:
        return owner_module == module_name
    return True


def public_report_dataclass_types(module: ModuleType) -> tuple[type[Any], ...]:
    report_types: list[type[Any]] = []
    for name in public_api_names(module):
        value = getattr(module, name, None)
        if (
            inspect.isclass(value)
            and dataclasses.is_dataclass(value)
            and name.endswith("Report")
        ):
            report_types.append(value)
    return tuple(report_types)


def assert_imports_are_allowlisted(module_name: str, tree: ast.Module) -> None:
    for module in imported_modules(module_name, tree):
        assert not any(
            module_matches_prefix(module, prefix) for prefix in FORBIDDEN_IMPORT_PREFIXES
        ), (module_name, module)
        assert module in ALLOWED_IMPORT_MODULES, (module_name, module)


def assert_no_forbidden_names(module_name: str, tree: ast.Module) -> None:
    allowed_matches = (
        ALLOWED_FORBIDDEN_NAME_MATCHES
        | MODULE_ALLOWED_FORBIDDEN_NAME_MATCHES.get(module_name, set())
    )
    normalized_names = {
        normalize_identifier(name)
        for name in collected_names(tree)
        if normalize_identifier(name) not in allowed_matches
    }
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        normalized_fragment = normalize_identifier(fragment)
        assert not any(normalized_fragment in name for name in normalized_names), (
            module_name,
            fragment,
        )


def assert_no_forbidden_calls(module_name: str, tree: ast.Module) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee_name = call_name(node)
            if (
                module_name.endswith("_log")
                and callee_name in LOCAL_LOG_IO_CALL_NAMES
            ):
                continue
            if (
                callee_name == "compile"
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "re"
            ):
                continue
            assert callee_name not in FORBIDDEN_CALL_NAMES, (module_name, callee_name)


def assert_no_forbidden_text(module_name: str, source: str) -> None:
    for fragment in FORBIDDEN_TEXT_FRAGMENTS:
        if normalize_identifier(fragment) in ALLOWED_FORBIDDEN_NAME_MATCHES:
            continue
        token_pattern = re.compile(
            rf"(?<![0-9A-Za-z_]){re.escape(fragment.lower())}(?![0-9A-Za-z_])",
        )
        assert token_pattern.search(source.lower()) is None, (module_name, fragment)


@pytest.mark.parametrize("module_name", TARGET_MODULE_NAMES)
def test_cycle_snapshot_layer_imports_stay_in_paper_report_scope(module_name: str):
    path = require_module_path(module_name)
    tree = parse_module(path)

    assert_imports_are_allowlisted(module_name, tree)


@pytest.mark.parametrize("module_name", TARGET_MODULE_NAMES)
def test_cycle_snapshot_layer_omits_live_execution_surface_names(module_name: str):
    path = require_module_path(module_name)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert_no_forbidden_names(module_name, tree)
    assert_no_forbidden_calls(module_name, tree)
    assert_no_forbidden_text(module_name, source)


@pytest.mark.parametrize("module_name", NON_LOG_MODULE_NAMES)
def test_cycle_snapshot_public_report_dataclasses_default_to_readonly_paper_flags(
    module_name: str,
):
    require_module_path(module_name)
    module = importlib.import_module(f"polymarket_alpha_lab.{module_name}")
    report_dataclasses = public_report_dataclass_types(module)

    assert report_dataclasses, module_name
    for dataclass_type in report_dataclasses:
        fields = {field.name: field for field in dataclasses.fields(dataclass_type)}
        for field_name in SAFETY_DATACLASS_FIELDS:
            assert field_name in fields, (dataclass_type.__name__, field_name)
            assert fields[field_name].default is True, (
                dataclass_type.__name__,
                field_name,
            )

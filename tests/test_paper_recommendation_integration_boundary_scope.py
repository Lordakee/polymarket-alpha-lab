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
PACKAGE_ROOT = "polymarket_alpha_lab"
INTEGRATION_MODULE_NAMES = (
    "paper_recommendation_pipeline",
    "paper_recommendation_cycle_bundle",
    "paper_recommendation_pipeline_trend",
)
SAFETY_DATACLASS_FIELDS = ("paper_only", "report_only", "readonly")

FORBIDDEN_IMPORT_PREFIXES = (
    "aiohttp",
    "asyncio",
    "bs4",
    "clob_client",
    "cloudscraper",
    "curl_cffi",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "ftplib",
    "http",
    "httpx",
    "importlib",
    "mechanize",
    "os",
    "pathlib",
    "playwright",
    "polymarket",
    "poplib",
    "py_clob_client",
    "requests",
    "requests_html",
    "runpy",
    "scrapy",
    "selenium",
    "smtplib",
    "socket",
    "socketserver",
    "ssl",
    "subprocess",
    "urllib",
    "urllib3",
    "web3",
    "websocket",
    "websockets",
    "polymarket_alpha_lab.__main__",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.auth",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.execution",
    "polymarket_alpha_lab.forecast_provider",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.llm_forecast",
    "polymarket_alpha_lab.llm_research_transport",
    "polymarket_alpha_lab.orders",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.runner",
    "polymarket_alpha_lab.strategy_cycle",
    "polymarket_alpha_lab.trading",
)

FORBIDDEN_CALL_NAMES = (
    "__import__",
    "compile",
    "connect",
    "delete",
    "eval",
    "exec",
    "input",
    "mkdir",
    "open",
    "post",
    "print",
    "put",
    "read",
    "read_text",
    "recv",
    "request",
    "run",
    "send",
    "sign_message",
    "sign_order",
    "submit",
    "write",
    "write_text",
)

FORBIDDEN_IDENTIFIER_TOKEN_GROUPS = (
    ("api",),
    ("auth",),
    ("authenticate",),
    ("browser",),
    ("clob",),
    ("cli",),
    ("client",),
    ("credential",),
    ("exchange",),
    ("execution",),
    ("fetch",),
    ("http",),
    ("key",),
    ("live",),
    ("network",),
    ("private",),
    ("request",),
    ("secret",),
    ("sign",),
    ("signer",),
    ("signature",),
    ("submit",),
    ("token",),
    ("transport",),
    ("wallet",),
    ("websocket",),
    ("allowance",),
    ("cancel", "order"),
    ("create", "order"),
    ("live", "order"),
    ("order", "builder"),
    ("order", "payload"),
    ("place", "order"),
    ("post", "order"),
    ("send", "order"),
    ("sign", "order"),
    ("submit", "order"),
    ("trade", "client"),
)

ALLOWED_IDENTIFIER_TOKEN_GROUPS = {
    "config_version": {("token",)},
}

IDENTIFIER_TOKEN_RE = re.compile(
    r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+",
)


def module_path(module_name: str) -> Path:
    return REPO_ROOT / "src" / PACKAGE_ROOT / f"{module_name}.py"


def parse_module(module_name: str) -> ast.Module:
    path = module_path(module_name)
    assert path.exists(), (
        f"{module_name} integration module must exist at {path} before this "
        "boundary test can pass"
    )
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def import_integration_module(module_name: str) -> ModuleType:
    full_name = f"{PACKAGE_ROOT}.{module_name}"
    try:
        return importlib.import_module(full_name)
    except ModuleNotFoundError as exc:
        if exc.name == full_name:
            pytest.fail(f"{full_name} must be importable for integration boundary tests")
        pytest.fail(f"{full_name} imports missing dependency {exc.name!r}")


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def absolute_import_from_module(node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    assert node.level == 1, ast.unparse(node)
    if node.module is None:
        return PACKAGE_ROOT
    return f"{PACKAGE_ROOT}.{node.module}"


def imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(absolute_import_from_module(node))
    return tuple(modules)


def identifier_tokens(identifier: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for chunk in re.split(r"[^0-9A-Za-z]+", identifier):
        if not chunk:
            continue
        tokens.extend(match.group(0).lower() for match in IDENTIFIER_TOKEN_RE.finditer(chunk))
    return tuple(tokens)


def token_group_is_present(
    identifier_tokens_: tuple[str, ...],
    forbidden_group: tuple[str, ...],
) -> bool:
    if len(forbidden_group) > len(identifier_tokens_):
        return False
    return any(
        identifier_tokens_[index : index + len(forbidden_group)] == forbidden_group
        for index in range(len(identifier_tokens_) - len(forbidden_group) + 1)
    )


def assert_identifier_omits_live_execution_terms(identifier: str) -> None:
    tokens = identifier_tokens(identifier)
    allowed_groups = ALLOWED_IDENTIFIER_TOKEN_GROUPS.get(identifier, set())
    for forbidden_group in FORBIDDEN_IDENTIFIER_TOKEN_GROUPS:
        if forbidden_group in allowed_groups:
            continue
        assert not token_group_is_present(tokens, forbidden_group), (
            identifier,
            forbidden_group,
        )


def assert_imports_omit_live_execution_modules(
    module_name: str,
    tree: ast.Module,
) -> None:
    for imported_module in imported_modules(tree):
        assert not any(
            module_matches_prefix(imported_module, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), (module_name, imported_module)


def assert_tree_omits_live_execution_names_and_calls(tree: ast.Module) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            assert_identifier_omits_live_execution_terms(node.name)
        elif isinstance(node, ast.arg):
            assert_identifier_omits_live_execution_terms(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            assert_identifier_omits_live_execution_terms(node.arg)
        elif isinstance(node, ast.Name):
            assert_identifier_omits_live_execution_terms(node.id)
        elif isinstance(node, ast.Attribute):
            assert_identifier_omits_live_execution_terms(node.attr)
        elif isinstance(node, ast.alias):
            assert_identifier_omits_live_execution_terms(node.name.rsplit(".", 1)[-1])
            if node.asname is not None:
                assert_identifier_omits_live_execution_terms(node.asname)
        elif isinstance(node, ast.Call):
            call_name = call_name_from_node(node)
            if call_name is not None:
                assert call_name not in FORBIDDEN_CALL_NAMES, call_name
                assert_identifier_omits_live_execution_terms(call_name)


def call_name_from_node(node: ast.Call) -> str | None:
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


def public_dataclass_types(module: ModuleType) -> tuple[type[Any], ...]:
    dataclass_types: list[type[Any]] = []
    for name in public_api_names(module):
        value = getattr(module, name, None)
        if inspect.isclass(value) and dataclasses.is_dataclass(value):
            dataclass_types.append(value)
    return tuple(dataclass_types)


@pytest.mark.parametrize("module_name", INTEGRATION_MODULE_NAMES)
def test_paper_recommendation_integration_modules_exist(module_name: str) -> None:
    path = module_path(module_name)
    assert path.exists(), f"{module_name} integration module must exist at {path}"


@pytest.mark.parametrize("module_name", INTEGRATION_MODULE_NAMES)
def test_paper_recommendation_integration_modules_are_importable(
    module_name: str,
) -> None:
    import_integration_module(module_name)


@pytest.mark.parametrize("module_name", INTEGRATION_MODULE_NAMES)
def test_paper_recommendation_integration_modules_do_not_import_live_surfaces(
    module_name: str,
) -> None:
    assert_imports_omit_live_execution_modules(module_name, parse_module(module_name))


@pytest.mark.parametrize("module_name", INTEGRATION_MODULE_NAMES)
def test_paper_recommendation_integration_modules_do_not_define_live_surfaces(
    module_name: str,
) -> None:
    assert_tree_omits_live_execution_names_and_calls(parse_module(module_name))


@pytest.mark.parametrize("module_name", INTEGRATION_MODULE_NAMES)
def test_paper_recommendation_integration_public_dataclasses_have_hard_flags(
    module_name: str,
) -> None:
    module = import_integration_module(module_name)
    dataclass_types = public_dataclass_types(module)

    assert dataclass_types, f"{module.__name__} must expose public dataclass reports"
    for dataclass_type in dataclass_types:
        fields = {field.name: field for field in dataclasses.fields(dataclass_type)}
        for field_name in SAFETY_DATACLASS_FIELDS:
            assert field_name in fields, (dataclass_type.__name__, field_name)
            assert fields[field_name].default is True, (
                dataclass_type.__name__,
                field_name,
            )


@pytest.mark.parametrize(
    "bad_source",
    (
        pytest.param(
            "from polymarket_alpha_lab.cli import main\n",
            id="first-party-cli-import",
        ),
        pytest.param(
            "from polymarket_alpha_lab.paper_execution import execute_paper_trade\n",
            id="first-party-paper-execution-import",
        ),
        pytest.param("import requests\n", id="network-import"),
        pytest.param("from eth_account import Account\n", id="wallet-signing-import"),
        pytest.param(
            """
def build_wallet_order_payload(wallet):
    return wallet
""",
            id="wallet-order-identifier",
        ),
        pytest.param(
            """
def build_report():
    return __import__("polymarket_alpha_lab.auth")
""",
            id="dynamic-import-call",
        ),
    ),
)
def test_paper_recommendation_integration_scope_guard_rejects_bad_sources(
    bad_source: str,
) -> None:
    tree = ast.parse(bad_source)
    with pytest.raises(AssertionError):
        assert_imports_omit_live_execution_modules("bad_module", tree)
        assert_tree_omits_live_execution_names_and_calls(tree)

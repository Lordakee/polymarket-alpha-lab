from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "polymarket_alpha_lab"
PACKAGE_ROOT = REPO_ROOT / "src" / PACKAGE_NAME

OPTIONAL_REDUCER_MODULES = (
    "paper_external_cost_assumptions",
    "paper_fee_schedule",
    "paper_recommendation_decision_ledger",
    "paper_recommendation_artifact_index",
    "paper_recommendation_score_explanation",
)

SAFETY_FLAG_NAMES = ("paper_only", "report_only", "readonly")

FORBIDDEN_IMPORT_PREFIXES = (
    "aiohttp",
    "argparse",
    "click",
    "clob_client",
    "curl_cffi",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "http",
    "httpx",
    "os",
    "playwright",
    "polymarket",
    "polymarket_clob_client",
    "py_clob_client",
    "requests",
    "requests_html",
    "runpy",
    "scrapy",
    "selenium",
    "shlex",
    "socket",
    "socketserver",
    "ssl",
    "subprocess",
    "typer",
    "urllib",
    "urllib3",
    "web3",
    "websocket",
    "websockets",
    f"{PACKAGE_NAME}.__main__",
    f"{PACKAGE_NAME}.api",
    f"{PACKAGE_NAME}.auth",
    f"{PACKAGE_NAME}.cli",
    f"{PACKAGE_NAME}.execution",
    f"{PACKAGE_NAME}.orders",
    f"{PACKAGE_NAME}.paper_execution",
    f"{PACKAGE_NAME}.runner",
    f"{PACKAGE_NAME}.trading",
    f"{PACKAGE_NAME}.wallet",
)

FORBIDDEN_CALL_OR_ATTRIBUTE_NAMES = {
    "__import__",
    "authenticate",
    "cancel",
    "cancel_order",
    "compile",
    "connect",
    "create_order",
    "delete",
    "eval",
    "exec",
    "fetch",
    "input",
    "login",
    "main",
    "mkdir",
    "open",
    "patch",
    "place_order",
    "post",
    "put",
    "read",
    "read_text",
    "recv",
    "request",
    "run",
    "send",
    "sign",
    "sign_message",
    "sign_order",
    "submit",
    "submit_order",
    "unlink",
    "write",
    "write_text",
}

FORBIDDEN_SOURCE_TOKEN_GROUPS = (
    ("api",),
    ("auth",),
    ("authenticate",),
    ("browser",),
    ("clob",),
    ("cli",),
    ("client",),
    ("credential",),
    ("exchange", "mutation"),
    ("exchange", "write"),
    ("http",),
    ("live",),
    ("login",),
    ("network", "client"),
    ("network", "mutation"),
    ("private", "key"),
    ("request",),
    ("secret",),
    ("sign",),
    ("signer",),
    ("signature",),
    ("wallet",),
    ("websocket",),
    ("cancel", "order"),
    ("create", "order"),
    ("order", "cancellation"),
    ("order", "submission"),
    ("place", "order"),
    ("post", "order"),
    ("send", "order"),
    ("sign", "order"),
    ("submit", "order"),
)

IDENTIFIER_TOKEN_RE = re.compile(
    r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+",
)
GUARDRAIL_NAME_MARKERS = ("DENY", "FORBIDDEN", "UNSAFE")


def module_path(module_name: str) -> Path:
    return PACKAGE_ROOT / f"{module_name}.py"


def existing_module_source(module_name: str) -> tuple[Path, str, ast.Module]:
    path = module_path(module_name)
    if not path.exists():
        pytest.skip(f"optional reducer module is not present yet: {module_name}")
    source = path.read_text(encoding="utf-8")
    return path, source, ast.parse(source, filename=str(path))


def absolute_import_from_module(node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    if node.module is None:
        return PACKAGE_NAME
    return f"{PACKAGE_NAME}.{node.module}"


def imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(absolute_import_from_module(node))
    return tuple(modules)


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def identifier_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for chunk in re.split(r"[^0-9A-Za-z]+", value):
        if not chunk:
            continue
        tokens.extend(
            match.group(0).lower() for match in IDENTIFIER_TOKEN_RE.finditer(chunk)
        )
    return tuple(tokens)


def token_group_is_present(
    source_tokens: tuple[str, ...],
    forbidden_group: tuple[str, ...],
) -> bool:
    if len(forbidden_group) > len(source_tokens):
        return False
    return any(
        source_tokens[index : index + len(forbidden_group)] == forbidden_group
        for index in range(len(source_tokens) - len(forbidden_group) + 1)
    )


def assert_no_forbidden_source_token_groups(
    module_name: str,
    value: str,
) -> None:
    source_tokens = identifier_tokens(value)
    for forbidden_group in FORBIDDEN_SOURCE_TOKEN_GROUPS:
        assert not token_group_is_present(source_tokens, forbidden_group), (
            module_name,
            value,
            forbidden_group,
        )


def source_name_tokens(source: str) -> tuple[str, ...]:
    tokens: list[str] = []
    readline = io.StringIO(source).readline
    for token in tokenize.generate_tokens(readline):
        if token.type == tokenize.NAME:
            tokens.append(token.string)
    return tuple(tokens)


def guardrail_string_literal_ids(tree: ast.Module) -> set[int]:
    literal_ids: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        target_names = {
            target.id
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        if not any(is_guardrail_name(name) for name in target_names):
            continue
        for child in ast.walk(node.value):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                literal_ids.add(id(child))
    return literal_ids


def is_guardrail_name(value: str) -> bool:
    return any(marker in value for marker in GUARDRAIL_NAME_MARKERS)


def is_safe_qualified_helper_call(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and is_safe_qualified_helper_attribute(node.func)
    )


def is_safe_qualified_helper_attribute(node: ast.Attribute) -> bool:
    return (
        isinstance(node.value, ast.Name)
        and node.value.id == "re"
        and node.attr == "compile"
    )


@pytest.mark.parametrize("module_name", OPTIONAL_REDUCER_MODULES)
def test_optional_reducer_imports_stay_inside_pure_paper_scope(
    module_name: str,
) -> None:
    _, _, tree = existing_module_source(module_name)

    for imported_module in imported_modules(tree):
        assert not any(
            module_matches_prefix(imported_module, forbidden_prefix)
            for forbidden_prefix in FORBIDDEN_IMPORT_PREFIXES
        ), (module_name, imported_module)
        assert_no_forbidden_source_token_groups(module_name, imported_module)


@pytest.mark.parametrize("module_name", OPTIONAL_REDUCER_MODULES)
def test_optional_reducer_has_no_live_execution_calls_or_attributes(
    module_name: str,
) -> None:
    _, _, tree = existing_module_source(module_name)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            if is_safe_qualified_helper_call(node):
                continue
            assert callee_name not in FORBIDDEN_CALL_OR_ATTRIBUTE_NAMES, (
                module_name,
                callee_name,
            )
        elif isinstance(node, ast.Attribute):
            if is_safe_qualified_helper_attribute(node):
                continue
            assert node.attr not in FORBIDDEN_CALL_OR_ATTRIBUTE_NAMES, (
                module_name,
                node.attr,
            )


@pytest.mark.parametrize("module_name", OPTIONAL_REDUCER_MODULES)
def test_optional_reducer_source_tokens_omit_live_execution_boundaries(
    module_name: str,
) -> None:
    _, source, tree = existing_module_source(module_name)
    allowed_guardrail_literal_ids = guardrail_string_literal_ids(tree)

    for token_name in source_name_tokens(source):
        if is_guardrail_name(token_name):
            continue
        assert_no_forbidden_source_token_groups(module_name, token_name)

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in allowed_guardrail_literal_ids:
                continue
            assert_no_forbidden_source_token_groups(module_name, node.value)


@pytest.mark.parametrize("module_name", OPTIONAL_REDUCER_MODULES)
def test_optional_reducer_declares_paper_report_readonly_boundary(
    module_name: str,
) -> None:
    _, source, _ = existing_module_source(module_name)

    for safety_flag_name in SAFETY_FLAG_NAMES:
        assert safety_flag_name in source, (module_name, safety_flag_name)

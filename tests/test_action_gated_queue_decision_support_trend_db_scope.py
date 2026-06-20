from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "polymarket_alpha_lab"
PACKAGE_ROOT = REPO_ROOT / "src" / PACKAGE_NAME

MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260620000003_action_gated_queue_decision_support_trend_reports.sql"
)

POSTGRES_IDENTIFIER_LIMIT = 63


@dataclass(frozen=True)
class PlannedModule:
    path: Path
    allow_sql_terms: bool = False
    allow_psycopg_terms: bool = False


PLANNED_MODULES = (
    PlannedModule(
        PACKAGE_ROOT
        / "action_gated_strategy_recommendation_queue_decision_support_trend_db_row.py",
    ),
    PlannedModule(
        PACKAGE_ROOT
        / "action_gated_strategy_recommendation_queue_decision_support_trend_store.py",
        allow_sql_terms=True,
    ),
    PlannedModule(
        PACKAGE_ROOT
        / "action_gated_strategy_recommendation_queue_decision_support_trend_psycopg.py",
        allow_sql_terms=True,
        allow_psycopg_terms=True,
    ),
    PlannedModule(
        PACKAGE_ROOT
        / "supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config.py",
        allow_sql_terms=True,
    ),
)

FORBIDDEN_IMPORT_PREFIXES = (
    "aiohttp",
    "bs4",
    "clob_client",
    "cloudscraper",
    "curl_cffi",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "http",
    "httpx",
    "mechanize",
    "playwright",
    "polymarket",
    "polymarket_clob_client",
    "py_clob_client",
    "requests",
    "requests_html",
    "scrapy",
    "selenium",
    "socket",
    "socketserver",
    "ssl",
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
    f"{PACKAGE_NAME}.positions",
    f"{PACKAGE_NAME}.runner",
    f"{PACKAGE_NAME}.trading",
    f"{PACKAGE_NAME}.wallet",
)

FORBIDDEN_CALL_OR_ATTRIBUTE_NAMES = {
    "__import__",
    "authenticate",
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
    "open",
    "patch",
    "place_order",
    "post",
    "put",
    "read_text",
    "recv",
    "replace_order",
    "request",
    "run",
    "send",
    "send_order",
    "sign",
    "sign_message",
    "sign_order",
    "submit",
    "submit_order",
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
    ("https",),
    ("live", "execution"),
    ("live", "trading"),
    ("login",),
    ("network",),
    ("private", "key"),
    ("account",),
    ("secret",),
    ("sign",),
    ("signer",),
    ("signature",),
    ("trading",),
    ("wallet",),
    ("websocket",),
    ("cancel", "order"),
    ("cancel", "orders"),
    ("create", "order"),
    ("construct", "order"),
    ("live", "order"),
    ("order", "builder"),
    ("order", "cancellation"),
    ("order", "construction"),
    ("order", "payload"),
    ("order", "replacement"),
    ("order", "submission"),
    ("place", "order"),
    ("post", "order"),
    ("replace", "order"),
    ("send", "order"),
    ("sign", "order"),
    ("submit", "order"),
    ("trade", "client"),
)

IDENTIFIER_TOKEN_RE = re.compile(
    r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+",
)
POSTGRES_IDENTIFIER_VALUE_RE = re.compile(
    r'^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)?$',
)
GUARDRAIL_NAME_MARKERS = ("ALLOW", "DENY", "FORBIDDEN", "UNSAFE")


def parse_module(planned_module: PlannedModule) -> tuple[str, ast.Module]:
    assert planned_module.path.exists(), (
        f"planned trend DB persistence module must exist at {planned_module.path}"
    )
    source = planned_module.path.read_text(encoding="utf-8")
    return source, ast.parse(source, filename=str(planned_module.path))


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


def token_group_start_indexes(
    source_tokens: tuple[str, ...],
    forbidden_group: tuple[str, ...],
) -> tuple[int, ...]:
    if len(forbidden_group) > len(source_tokens):
        return ()
    return tuple(
        index
        for index in range(len(source_tokens) - len(forbidden_group) + 1)
        if source_tokens[index : index + len(forbidden_group)] == forbidden_group
    )


def allowed_source_token_groups(planned_module: PlannedModule) -> set[tuple[str, ...]]:
    allowed_groups: set[tuple[str, ...]] = set()
    if planned_module.allow_sql_terms:
        allowed_groups.add(("sql",))
    if planned_module.allow_psycopg_terms:
        allowed_groups.add(("psycopg",))
    return allowed_groups


def token_group_is_allowed_in_context(
    source_tokens: tuple[str, ...],
    forbidden_group: tuple[str, ...],
) -> bool:
    if forbidden_group != ("api",):
        return False

    start_indexes = token_group_start_indexes(source_tokens, forbidden_group)
    return bool(start_indexes) and all(
        index > 0 and source_tokens[index - 1] == "db" for index in start_indexes
    )


def assert_no_forbidden_source_token_groups(
    planned_module: PlannedModule,
    value: str,
) -> None:
    source_tokens = identifier_tokens(value)
    allowed_groups = allowed_source_token_groups(planned_module)
    for forbidden_group in FORBIDDEN_SOURCE_TOKEN_GROUPS:
        if forbidden_group in allowed_groups:
            continue
        if token_group_is_allowed_in_context(source_tokens, forbidden_group):
            continue
        assert not token_group_is_present(source_tokens, forbidden_group), (
            planned_module.path.name,
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


def call_name_from_node(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def call_qualifier_from_node(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return ast.unparse(node.func)
    return ""


def is_allowed_db_connect_call(planned_module: PlannedModule, node: ast.Call) -> bool:
    return (
        planned_module.allow_psycopg_terms
        and call_name_from_node(node) == "connect"
        and call_qualifier_from_node(node).startswith("psycopg.")
    )


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


def is_allowed_db_connect_attribute(
    planned_module: PlannedModule,
    node: ast.Attribute,
) -> bool:
    return (
        planned_module.allow_psycopg_terms
        and node.attr == "connect"
        and ast.unparse(node).startswith("psycopg.")
    )


def is_safe_persistence_call_or_attribute(
    planned_module: PlannedModule,
    node: ast.AST,
) -> bool:
    if isinstance(node, ast.Call):
        return is_allowed_db_connect_call(planned_module, node) or (
            is_safe_qualified_helper_call(node)
        )
    if isinstance(node, ast.Attribute):
        return is_allowed_db_connect_attribute(
            planned_module,
            node,
        ) or is_safe_qualified_helper_attribute(node)
    return False


def string_constant_values(tree: ast.Module) -> tuple[ast.Constant, ...]:
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )


def assigned_string_constants(tree: ast.Module) -> dict[str, str]:
    constants: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if not isinstance(node.value.value, str):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    constants[target.id] = node.value.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Constant):
            if isinstance(node.target, ast.Name) and isinstance(node.value.value, str):
                constants[node.target.id] = node.value.value
    return constants


def assert_postgres_identifier_fits(identifier: str) -> None:
    for part in identifier.split("."):
        normalized_part = part.strip('"')
        if not normalized_part:
            continue
        assert len(normalized_part.encode("utf-8")) <= POSTGRES_IDENTIFIER_LIMIT, (
            identifier,
            normalized_part,
        )


def visible_postgres_constant_values(tree: ast.Module) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for name, value in assigned_string_constants(tree).items():
        if "ENV_VAR" in name or "ERROR" in name:
            continue
        if (
            any(marker in name for marker in ("TABLE", "INDEX"))
            and POSTGRES_IDENTIFIER_VALUE_RE.fullmatch(value) is not None
        ):
            values.append((name, value))
    return tuple(values)


@pytest.mark.parametrize("planned_module", PLANNED_MODULES, ids=lambda module: module.path.name)
def test_planned_trend_db_persistence_modules_exist(
    planned_module: PlannedModule,
) -> None:
    assert planned_module.path.exists(), (
        f"planned trend DB persistence module must exist at {planned_module.path}"
    )


@pytest.mark.parametrize("planned_module", PLANNED_MODULES, ids=lambda module: module.path.name)
def test_planned_trend_db_persistence_modules_do_not_import_live_or_network_surfaces(
    planned_module: PlannedModule,
) -> None:
    _, tree = parse_module(planned_module)

    for imported_module in imported_modules(tree):
        assert not any(
            module_matches_prefix(imported_module, forbidden_prefix)
            for forbidden_prefix in FORBIDDEN_IMPORT_PREFIXES
        ), (planned_module.path.name, imported_module)
        assert_no_forbidden_source_token_groups(planned_module, imported_module)


@pytest.mark.parametrize("planned_module", PLANNED_MODULES, ids=lambda module: module.path.name)
def test_planned_trend_db_persistence_modules_do_not_define_live_or_order_surfaces(
    planned_module: PlannedModule,
) -> None:
    source, tree = parse_module(planned_module)
    allowed_guardrail_literal_ids = guardrail_string_literal_ids(tree)

    for token_name in source_name_tokens(source):
        if is_guardrail_name(token_name):
            continue
        assert_no_forbidden_source_token_groups(planned_module, token_name)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if is_safe_persistence_call_or_attribute(planned_module, node):
                continue
            callee_name = call_name_from_node(node)
            assert callee_name not in FORBIDDEN_CALL_OR_ATTRIBUTE_NAMES, (
                planned_module.path.name,
                callee_name,
            )
            if callee_name is not None:
                assert_no_forbidden_source_token_groups(planned_module, callee_name)
        elif isinstance(node, ast.Attribute):
            if is_safe_persistence_call_or_attribute(planned_module, node):
                continue
            assert node.attr not in FORBIDDEN_CALL_OR_ATTRIBUTE_NAMES, (
                planned_module.path.name,
                node.attr,
            )
            assert_no_forbidden_source_token_groups(planned_module, node.attr)

    for node in string_constant_values(tree):
        if id(node) in allowed_guardrail_literal_ids:
            continue
        assert_no_forbidden_source_token_groups(planned_module, node.value)


@pytest.mark.parametrize("planned_module", PLANNED_MODULES, ids=lambda module: module.path.name)
def test_visible_default_table_and_index_names_fit_postgres_identifier_limit(
    planned_module: PlannedModule,
) -> None:
    _, tree = parse_module(planned_module)

    for constant_name, identifier in visible_postgres_constant_values(tree):
        assert_postgres_identifier_fits(identifier), (
            planned_module.path.name,
            constant_name,
            identifier,
        )


def test_visible_migration_table_and_index_names_fit_postgres_identifier_limit() -> None:
    if not MIGRATION.exists():
        return

    migration_sql = MIGRATION.read_text(encoding="utf-8")
    for regex in (
        r"create\s+table\s+if\s+not\s+exists\s+([a-zA-Z0-9_.\"]+)",
        r"create\s+(?:unique\s+)?index\s+if\s+not\s+exists\s+([a-zA-Z0-9_.\"]+)",
    ):
        for identifier in re.findall(regex, migration_sql, flags=re.IGNORECASE):
            assert_postgres_identifier_fits(identifier)


@pytest.mark.parametrize(
    "bad_source",
    (
        pytest.param("from polymarket_alpha_lab.trading import TradeClient\n", id="trading-import"),
        pytest.param("import requests\n", id="http-client-import"),
        pytest.param("from eth_account import Account\n", id="wallet-account-import"),
        pytest.param("def submit_order_payload(wallet):\n    return wallet\n", id="order-submit"),
        pytest.param("def read_account_secret(private_key):\n    return private_key\n", id="secret-read"),
        pytest.param("def build_network_client():\n    return object()\n", id="network-client"),
    ),
)
def test_trend_db_scope_guard_rejects_bad_sources(bad_source: str) -> None:
    planned_module = PlannedModule(PACKAGE_ROOT / "bad_scope.py")
    tree = ast.parse(bad_source)

    with pytest.raises(AssertionError):
        for imported_module in imported_modules(tree):
            assert not any(
                module_matches_prefix(imported_module, forbidden_prefix)
                for forbidden_prefix in FORBIDDEN_IMPORT_PREFIXES
            ), imported_module
            assert_no_forbidden_source_token_groups(planned_module, imported_module)
        for token_name in source_name_tokens(bad_source):
            assert_no_forbidden_source_token_groups(planned_module, token_name)


def test_trend_db_scope_guard_allows_recommendation_domain_word() -> None:
    planned_module = PlannedModule(PACKAGE_ROOT / "recommendation_scope.py")

    assert_no_forbidden_source_token_groups(
        planned_module,
        "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow",
    )

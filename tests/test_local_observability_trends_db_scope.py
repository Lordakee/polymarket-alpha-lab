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
DOC_PATH = REPO_ROOT / "docs" / "local-observability-trends-db-persistence.md"
MIGRATION_GLOB = "*local_observability_trends*.sql"
EXPECTED_TABLE = "local_observability_trends_reports"
POSTGRES_IDENTIFIER_LIMIT = 63

LOCAL_OBSERVABILITY_TRENDS_ENV_VARS = (
    "POLYMARKET_ALPHA_LAB_LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_LOCAL_OBSERVABILITY_TRENDS_DB_DSN",
    "POLYMARKET_ALPHA_LAB_LOCAL_OBSERVABILITY_TRENDS_DB_TABLE",
)

HARD_FLAGS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class PlannedModule:
    path: Path
    allow_sql_terms: bool = False
    allow_psycopg_import: bool = False
    allow_psycopg_connect: bool = False


ROW_MODULE = PlannedModule(PACKAGE_ROOT / "local_observability_trends_db_row.py")
STORE_MODULE = PlannedModule(
    PACKAGE_ROOT / "local_observability_trends_store.py",
    allow_sql_terms=True,
)
PSYCOPG_MODULE = PlannedModule(
    PACKAGE_ROOT / "local_observability_trends_psycopg.py",
    allow_sql_terms=True,
    allow_psycopg_import=True,
    allow_psycopg_connect=True,
)
CONFIG_MODULE = PlannedModule(
    PACKAGE_ROOT / "supabase_local_observability_trends_config.py",
    allow_sql_terms=True,
)

PLANNED_MODULES = (
    ROW_MODULE,
    STORE_MODULE,
    PSYCOPG_MODULE,
    CONFIG_MODULE,
)

HARD_FLAG_SOURCE_PATHS = (
    ROW_MODULE.path,
    STORE_MODULE.path,
    DOC_PATH,
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
    "delete_order",
    "eval",
    "exec",
    "fetch",
    "input",
    "load_dotenv",
    "login",
    "open",
    "patch",
    "place_order",
    "post",
    "post_order",
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
    ("cancel", "order"),
    ("cancel", "orders"),
    ("clob",),
    ("cli",),
    ("client",),
    ("credential",),
    ("create", "order"),
    ("exchange",),
    ("exchange", "mutation"),
    ("exchange", "write"),
    ("http",),
    ("https",),
    ("live", "execution"),
    ("live", "order"),
    ("live", "trading"),
    ("login",),
    ("network",),
    ("order", "builder"),
    ("order", "cancellation"),
    ("order", "construction"),
    ("order", "payload"),
    ("order", "replacement"),
    ("order", "submission"),
    ("place", "order"),
    ("post", "order"),
    ("private", "key"),
    ("account",),
    ("replace", "order"),
    ("secret",),
    ("send", "order"),
    ("sign",),
    ("signer",),
    ("signature",),
    ("sign", "order"),
    ("submit", "order"),
    ("trade", "client"),
    ("trading",),
    ("wallet",),
    ("websocket",),
)

IDENTIFIER_TOKEN_RE = re.compile(
    r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+",
)
POSTGRES_IDENTIFIER_VALUE_RE = re.compile(
    r'^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)?$',
)
SQL_IDENTIFIER_RE = r'"[^"]+"|[A-Za-z_][A-Za-z0-9_]*'
GUARDRAIL_NAME_MARKERS = ("ALLOW", "DENY", "FORBIDDEN", "UNSAFE")


def migration_path() -> Path:
    matches = tuple(
        sorted((REPO_ROOT / "supabase" / "migrations").glob(MIGRATION_GLOB)),
    )
    assert len(matches) == 1, (
        "expected exactly one local observability trends migration",
        matches,
    )
    return matches[0]


def parse_module(planned_module: PlannedModule) -> tuple[str, ast.Module]:
    assert planned_module.path.exists(), (
        f"planned local observability trends DB persistence module must exist at "
        f"{planned_module.path}"
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


def module_import_is_allowed(planned_module: PlannedModule, imported_module: str) -> bool:
    return planned_module.allow_psycopg_import and module_matches_prefix(
        imported_module,
        "psycopg",
    )


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
    allowed_groups: set[tuple[str, ...]] = {("db",)}
    if planned_module.allow_sql_terms:
        allowed_groups.add(("sql",))
    if planned_module.allow_psycopg_import:
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


def is_guardrail_name(value: str) -> bool:
    return any(marker in value for marker in GUARDRAIL_NAME_MARKERS)


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


def is_allowed_psycopg_connect_call(
    planned_module: PlannedModule,
    node: ast.Call,
) -> bool:
    return (
        planned_module.allow_psycopg_connect
        and call_name_from_node(node) == "connect"
        and call_qualifier_from_node(node).startswith("psycopg.")
    )


def is_allowed_psycopg_connect_attribute(
    planned_module: PlannedModule,
    node: ast.Attribute,
) -> bool:
    return (
        planned_module.allow_psycopg_connect
        and node.attr == "connect"
        and ast.unparse(node).startswith("psycopg.")
    )


def is_safe_qualified_helper_call(node: ast.Call) -> bool:
    return isinstance(node.func, ast.Attribute) and is_safe_qualified_helper_attribute(
        node.func,
    )


def is_safe_qualified_helper_attribute(node: ast.Attribute) -> bool:
    return (
        isinstance(node.value, ast.Name)
        and node.value.id == "re"
        and node.attr == "compile"
    )


def is_safe_persistence_call_or_attribute(
    planned_module: PlannedModule,
    node: ast.AST,
) -> bool:
    if isinstance(node, ast.Call):
        return is_allowed_psycopg_connect_call(planned_module, node) or (
            is_safe_qualified_helper_call(node)
        )
    if isinstance(node, ast.Attribute):
        return is_allowed_psycopg_connect_attribute(planned_module, node) or (
            is_safe_qualified_helper_attribute(node)
        )
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


def assert_postgres_identifier_fits(identifier: str) -> None:
    for part in identifier.split("."):
        normalized_part = part.strip('"')
        if not normalized_part:
            continue
        assert len(normalized_part.encode("utf-8")) <= POSTGRES_IDENTIFIER_LIMIT, (
            identifier,
            normalized_part,
        )


def strip_sql_comments(sql: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return re.sub(r"--.*?$", "", without_block_comments, flags=re.MULTILINE)


def split_top_level_csv(value: str) -> tuple[str, ...]:
    parts: list[str] = []
    start = 0
    depth = 0
    in_single_quote = False
    in_double_quote = False
    index = 0
    while index < len(value):
        character = value[index]
        if character == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif character == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif not in_single_quote and not in_double_quote:
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
            elif character == "," and depth == 0:
                parts.append(value[start:index].strip())
                start = index + 1
        index += 1
    parts.append(value[start:].strip())
    return tuple(part for part in parts if part)


def visible_migration_identifiers(sql: str) -> tuple[str, ...]:
    stripped = strip_sql_comments(sql)
    identifiers: list[str] = []
    identifier_pattern = rf"(?:{SQL_IDENTIFIER_RE})(?:\.(?:{SQL_IDENTIFIER_RE}))?"

    for regex in (
        rf"create\s+table\s+if\s+not\s+exists\s+({identifier_pattern})",
        rf"create\s+(?:unique\s+)?index\s+if\s+not\s+exists\s+({identifier_pattern})",
        rf"\bconstraint\s+({SQL_IDENTIFIER_RE})",
    ):
        identifiers.extend(re.findall(regex, stripped, flags=re.IGNORECASE))

    for match in re.finditer(
        rf"create\s+table\s+if\s+not\s+exists\s+"
        rf"({identifier_pattern})\s*\((.*?)\);",
        stripped,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        identifiers.append(match.group(1))
        for table_item in split_top_level_csv(match.group(2)):
            first_token = re.match(rf"\s*({SQL_IDENTIFIER_RE})", table_item)
            if first_token is None:
                continue
            column_or_constraint = first_token.group(1)
            if column_or_constraint.lower().strip('"') in {
                "check",
                "constraint",
                "exclude",
                "foreign",
                "primary",
                "unique",
            }:
                continue
            identifiers.append(column_or_constraint)

    return tuple(dict.fromkeys(identifiers))


@pytest.mark.parametrize("planned_module", PLANNED_MODULES, ids=lambda module: module.path.name)
def test_planned_local_observability_trends_db_modules_exist(
    planned_module: PlannedModule,
) -> None:
    assert planned_module.path.exists(), (
        f"planned local observability trends DB persistence module must exist at "
        f"{planned_module.path}"
    )


@pytest.mark.parametrize("planned_module", PLANNED_MODULES, ids=lambda module: module.path.name)
def test_planned_local_observability_trends_db_modules_do_not_import_live_or_network_surfaces(
    planned_module: PlannedModule,
) -> None:
    _, tree = parse_module(planned_module)

    for imported_module in imported_modules(tree):
        if module_import_is_allowed(planned_module, imported_module):
            continue
        assert not module_matches_prefix(imported_module, "psycopg"), (
            planned_module.path.name,
            imported_module,
        )
        assert not any(
            module_matches_prefix(imported_module, forbidden_prefix)
            for forbidden_prefix in FORBIDDEN_IMPORT_PREFIXES
        ), (planned_module.path.name, imported_module)
        assert_no_forbidden_source_token_groups(planned_module, imported_module)


@pytest.mark.parametrize("planned_module", PLANNED_MODULES, ids=lambda module: module.path.name)
def test_planned_local_observability_trends_db_modules_do_not_define_live_or_order_surfaces(
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


def test_local_observability_trends_db_hard_flags_are_visible_in_row_store_migration_and_docs() -> None:
    paths = (*HARD_FLAG_SOURCE_PATHS, migration_path())

    for path in paths:
        text = path.read_text(encoding="utf-8").lower()
        for flag in HARD_FLAGS:
            assert flag in text, (path, flag)


def test_local_observability_trends_migration_is_paper_report_readonly_only() -> None:
    sql = migration_path().read_text(encoding="utf-8").lower()

    assert EXPECTED_TABLE in sql
    for required in (
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert required in sql
    for forbidden in (
        "auth",
        "clob",
        "credential",
        "private_key",
        "secret",
        "submit_order",
        "cancel_order",
        "replace_order",
        "wallet",
    ):
        assert forbidden not in sql


def test_visible_migration_sql_identifiers_fit_postgres_identifier_limit() -> None:
    migration_sql = migration_path().read_text(encoding="utf-8")

    identifiers = visible_migration_identifiers(migration_sql)
    assert identifiers, "migration must expose table, column, index, or constraint names"
    for identifier in identifiers:
        assert_postgres_identifier_fits(identifier)


def test_local_observability_trends_docs_state_persistence_only_boundary() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    for required in (
        "optional supabase/postgres persistence",
        "localobservabilitytrendsreport",
        EXPECTED_TABLE,
        "payload_json",
        "canonical report payload",
        "scalars",
        "query aids",
        "persistence-only",
        "paper-only",
        "report-only",
        "readonly",
        "no live trading",
        "no auth",
        "no wallet",
        "no private keys",
        "no account reads",
        "no order construction",
        "no signing",
        "no order submission",
        "no cancellation",
        "no replacement",
        "no exchange mutation",
        "no cli wiring",
    ):
        assert required in text
    for env_var in LOCAL_OBSERVABILITY_TRENDS_ENV_VARS:
        assert env_var.lower() in text


def test_local_observability_trends_scope_guard_rejects_bad_sources() -> None:
    planned_module = PlannedModule(PACKAGE_ROOT / "bad_scope.py")
    bad_sources = (
        "from polymarket_alpha_lab.trading import TradeClient\n",
        "import requests\n",
        "from eth_account import Account\n",
        "def submit_order_payload(wallet):\n    return wallet\n",
        "def read_account_secret(private_key):\n    return private_key\n",
        "def build_network_client():\n    return object()\n",
        "def cli_persist_command():\n    return None\n",
    )

    for bad_source in bad_sources:
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


def test_local_observability_trends_scope_guard_allows_report_domain_words() -> None:
    assert_no_forbidden_source_token_groups(
        ROW_MODULE,
        "LocalObservabilityTrendsDbRow",
    )
    assert_no_forbidden_source_token_groups(
        PSYCOPG_MODULE,
        "persist_local_observability_trends_report_with_psycopg",
    )

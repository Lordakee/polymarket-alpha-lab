import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_action_gated_strategy_recommendation_queue_history_config.py"
)
DOC_PATH = REPO_ROOT / "docs" / "action-gated-queue-history-db-persistence.md"
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"
MIGRATION_PATH = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260620000001_action_gated_strategy_recommendation_queue_history_reports.sql"
)

HISTORY_ENV_VARS = (
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_HISTORY_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_HISTORY_DB_DSN",
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_HISTORY_DB_TABLE",
)

ALLOWED_STDLIB_IMPORTS = {
    "__future__",
    "dataclasses",
    "os",
    "re",
    "typing",
}
ALLOWED_LOCAL_IMPORTS = {
    "polymarket_alpha_lab.supabase_local_dsn",
}

FORBIDDEN_SOURCE_FRAGMENTS = (
    "auth",
    "cancel",
    "clob",
    "exchange",
    "live_trading",
    "order_args",
    "private_key",
    "replace",
    "sign",
    "submit",
    "wallet",
)

FORBIDDEN_CALL_NAMES = {
    "cancel",
    "create_order",
    "delete_order",
    "load_dotenv",
    "post_order",
    "replace",
    "sign",
    "submit",
}

FORBIDDEN_ATTR_NAMES = (
    "auth",
    "cancel",
    "client",
    "create_order",
    "delete_order",
    "exchange",
    "load_dotenv",
    "post_order",
    "private_key",
    "replace",
    "sign",
    "submit",
    "wallet",
)


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def parse_module(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def test_history_env_config_stays_at_env_boundary() -> None:
    tree = parse_module(CONFIG_PATH)

    assert {
        module
        for module in imported_modules(tree)
        if module.startswith("polymarket_alpha_lab.")
    } == ALLOWED_LOCAL_IMPORTS
    for module in imported_modules(tree):
        if module in ALLOWED_LOCAL_IMPORTS:
            continue
        top_level = module.split(".", 1)[0]
        assert top_level in ALLOWED_STDLIB_IMPORTS, module

    source = CONFIG_PATH.read_text(encoding="utf-8")
    normalized_source = normalize_identifier(source)
    for fragment in FORBIDDEN_SOURCE_FRAGMENTS:
        assert normalize_identifier(fragment) not in normalized_source, fragment

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in FORBIDDEN_CALL_NAMES
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in FORBIDDEN_CALL_NAMES
        elif isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_ATTR_NAMES


def test_history_docs_state_persistence_only_boundary() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    for required in (
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
        "persisted history db history",
        "action-gated-queue-history-db-history",
        "reads already-persisted history reports only",
        "uses the same history db environment variables",
        "supports only --limit",
        "--latest-action-status research_ready|watch|blocked",
        "never persists rows",
    ):
        assert required in text


def test_history_migration_is_paper_report_readonly_only() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()

    assert "paper_action_gated_strategy_recommendation_queue_history_reports" in sql
    assert "paper_only boolean not null default true" in sql
    assert "report_only boolean not null default true" in sql
    assert "readonly boolean not null default true" in sql
    assert "check (paper_only is true)" in sql
    assert "check (report_only is true)" in sql
    assert "check (readonly is true)" in sql
    for fragment in (
        "auth",
        "private_key",
        "wallet",
        "clob",
        "order_args",
        "submit",
        "cancel",
        "replace",
        "exchange",
    ):
        assert fragment not in sql


def test_env_example_declares_only_blank_history_db_vars() -> None:
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    for env_var in HISTORY_ENV_VARS:
        assert f"{env_var}=" in lines
        assert f"{env_var}=postgresql://" not in text
    assert all(line.endswith("=") for line in lines)
    assert "ACTION_GATED_QUEUE_HISTORY_DB_PRIVATE_KEY" not in text
    assert "ACTION_GATED_QUEUE_HISTORY_DB_WALLET" not in text

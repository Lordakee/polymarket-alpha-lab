from __future__ import annotations

from pathlib import Path


PRODUCTION_PATHS = (
    Path("src/polymarket_alpha_lab/strategy_risk_audit_db_row.py"),
    Path("src/polymarket_alpha_lab/strategy_risk_audit_store.py"),
    Path("src/polymarket_alpha_lab/strategy_risk_audit_psycopg.py"),
    Path("src/polymarket_alpha_lab/supabase_strategy_risk_audit_config.py"),
    Path("supabase/migrations/20260620000005_strategy_risk_audit_reports.sql"),
)
FORBIDDEN_RUNTIME_FRAGMENTS = (
    "private_key",
    "wallet",
    "auth_token",
    "api_key",
    "secret_key",
    "py_clob_client",
    "clob_client",
    "polymarket_client",
    "exchange_client",
    "create_order",
    "build_order",
    "sign_order",
    "submit_order",
    "post_order",
    "cancel_order",
    "replace_order",
    "mutation",
)
CLI_PATH = Path("src/polymarket_alpha_lab/cli.py")
FORBIDDEN_CLI_FLAG_FRAGMENTS = (
    "--strategy-risk-audit-db-dsn",
    "--strategy-risk-audit-db-table",
    "--strategy-risk-audit-db-enabled",
)


def _read_lower(path: Path) -> str:
    assert path.exists(), f"missing expected foundation file: {path}"
    return path.read_text(encoding="utf-8").lower()


def test_strategy_risk_audit_db_foundation_has_no_execution_surface() -> None:
    combined = "\n".join(_read_lower(path) for path in PRODUCTION_PATHS)

    for fragment in FORBIDDEN_RUNTIME_FRAGMENTS:
        assert fragment not in combined


def test_strategy_risk_audit_db_foundation_exposes_no_explicit_cli_db_flags() -> None:
    cli_text = CLI_PATH.read_text(encoding="utf-8")

    command_index = cli_text.index('"strategy-audit"')
    next_command_index = cli_text.index('"strategy-audit-history"', command_index)
    command_block = cli_text[command_index:next_command_index]

    for fragment in FORBIDDEN_CLI_FLAG_FRAGMENTS:
        assert fragment not in command_block
        assert fragment not in cli_text

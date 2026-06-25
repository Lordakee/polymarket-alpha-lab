from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_config import (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_TABLE,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_TABLE_ENV_VAR,
    SupabasePaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
    from_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_env,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260625000010_paper_autonomous_allocation_proposal_metrics_evaluation_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_autonomous_allocation_proposal_metrics_evaluation_reports"
        r"\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, (
        "migration must create "
        "public.paper_autonomous_allocation_proposal_metrics_evaluation_reports"
    )
    return compact(match.group(1))


def test_env_config_defaults_disabled_and_masks_dsn() -> None:
    config = from_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_env(
        {},
    )

    assert config == (
        SupabasePaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(
            enabled=False,
            dsn=None,
            table_name=(
                "paper_autonomous_allocation_proposal_metrics_evaluation_reports"
            ),
        )
    )
    assert DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_TABLE == (
        "paper_autonomous_allocation_proposal_metrics_evaluation_reports"
    )

    enabled = SupabasePaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig(
        enabled=True,
        dsn="postgresql://user:secret@example.invalid/db",
        table_name="paper_ops.metrics_evaluation_archive",
    )
    assert "secret" not in repr(enabled)
    assert "postgresql://" not in repr(enabled)
    assert "<redacted>" in repr(enabled)


def test_env_config_parses_enabled_values_and_validates_dsn_and_table() -> None:
    config = from_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_env(
        {
            PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_ENABLED_ENV_VAR: (
                " TRUE "
            ),
            PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_DSN_ENV_VAR: (
                "postgresql://user:secret@example.invalid/db"
            ),
            PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_TABLE_ENV_VAR: (
                "paper_ops.metrics_evaluation_archive"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == "postgresql://user:secret@example.invalid/db"
    assert config.table_name == "paper_ops.metrics_evaluation_archive"

    disabled = from_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_env(
        {
            PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_ENABLED_ENV_VAR: (
                " FALSE "
            ),
            PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_DSN_ENV_VAR: (
                "postgresql://user:secret@example.invalid/db"
            ),
        },
    )
    assert disabled.enabled is False

    with pytest.raises(ValueError, match="must be set"):
        from_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_env(
            {
                PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_ENABLED_ENV_VAR: (
                    "1"
                ),
            },
        )

    with pytest.raises(ValueError, match="true or false"):
        from_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_env(
            {
                PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_ENABLED_ENV_VAR: (
                    "yes"
                ),
            },
        )

    with pytest.raises(ValueError, match="simple lowercase identifier"):
        from_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_env(
            {
                PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_TABLE_ENV_VAR: (
                    "public.bad-name"
                ),
            },
        )


def test_migration_creates_metrics_evaluation_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "evaluation_status text not null",
        "recommended_next_step text not null",
        "source_report_count integer not null",
        "latest_report_generated_at timestamptz",
        "reason_code_counts jsonb not null",
        "reason_codes jsonb not null",
        "diagnostics jsonb not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_metrics_evaluation_invariants_with_checks():
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (evaluation_status in ('pass', 'watch', 'blocked'))",
        "check (source_report_count >= 0)",
        "check (jsonb_typeof(reason_code_counts) = 'object')",
        "check (jsonb_typeof(reason_codes) = 'array')",
        "check (jsonb_typeof(diagnostics) = 'object')",
        "check (jsonb_typeof(payload) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_adds_useful_lookup_indexes():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_paapmer_generated_at on public.paper_autonomous_allocation_proposal_metrics_evaluation_reports (generated_at desc);",
        "create index if not exists idx_paapmer_status_generated_at on public.paper_autonomous_allocation_proposal_metrics_evaluation_reports (evaluation_status, generated_at desc);",
        "create index if not exists idx_paapmer_config_generated_at on public.paper_autonomous_allocation_proposal_metrics_evaluation_reports (config_version, generated_at desc);",
        "create index if not exists idx_paapmer_reason_codes_gin on public.paper_autonomous_allocation_proposal_metrics_evaluation_reports using gin (reason_codes jsonb_path_ops);",
        "create index if not exists idx_paapmer_payload_gin on public.paper_autonomous_allocation_proposal_metrics_evaluation_reports using gin (payload jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_live_trading_or_account_terms():
    sql = migration_sql().lower()

    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\border\b",
        r"\bsubmit(?:s|ted|ting|tal)?\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern


def test_new_db_modules_do_not_import_live_trading_or_network_surfaces():
    module_paths = (
        REPO_ROOT
        / "src"
        / "polymarket_alpha_lab"
        / "paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row.py",
        REPO_ROOT
        / "src"
        / "polymarket_alpha_lab"
        / "paper_autonomous_allocation_proposal_db_history_metrics_evaluation_store.py",
        REPO_ROOT
        / "src"
        / "polymarket_alpha_lab"
        / "paper_autonomous_allocation_proposal_db_history_metrics_evaluation_psycopg.py",
        REPO_ROOT
        / "src"
        / "polymarket_alpha_lab"
        / "supabase_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_config.py",
    )
    forbidden_roots = {
        "aiohttp",
        "eth_account",
        "httpx",
        "py_clob_client",
        "requests",
        "socket",
        "urllib",
        "websocket",
        "websockets",
    }

    for module_path in module_paths:
        module = ast.parse(module_path.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_roots.add(node.module.split(".", 1)[0])

        assert not imported_roots & forbidden_roots, module_path.name

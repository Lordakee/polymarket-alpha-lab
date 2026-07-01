from __future__ import annotations

from pathlib import Path
import re


RUNBOOK_PATH = Path("docs/team-forecast-supabase-runbook.md")
MIGRATION_PATH = Path("supabase/migrations/20260701000000_team_forecast_tables.sql")

EXPECTED_TABLES = (
    "team_profiles",
    "team_market_routes",
    "team_forecasts",
    "team_forecast_evidence",
    "team_forecast_outcomes",
)
EXPECTED_ENV_VARS = (
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN",
    "POLYMARKET_ALPHA_LAB_TEAM_PROFILE_DB_TABLE",
    "POLYMARKET_ALPHA_LAB_TEAM_ROUTE_DB_TABLE",
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_TABLE",
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_EVIDENCE_DB_TABLE",
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_OUTCOME_DB_TABLE",
)


def _runbook_text() -> str:
    assert RUNBOOK_PATH.exists(), f"{RUNBOOK_PATH} must exist"
    return RUNBOOK_PATH.read_text(encoding="utf-8")


def test_team_forecast_runbook_documents_local_apply_and_operator_commands() -> None:
    text = _runbook_text()

    required_fragments = (
        "sudo -n docker ps",
        "sudo -n docker exec supabase-db psql",
        "psql -v ON_ERROR_STOP=1",
        "/home/ubuntu/supabase/node_modules/.bin/supabase",
        str(MIGRATION_PATH),
        "local Supabase/Postgres",
        "Phase 1 paper-only/report-only/readonly",
    )

    for fragment in required_fragments:
        assert fragment in text


def test_team_forecast_runbook_verifies_exact_tables_without_mutation() -> None:
    text = _runbook_text()
    lower_text = text.lower()

    for table_name in EXPECTED_TABLES:
        assert table_name in text
        assert (
            f"to_regclass('public.{table_name}')" in text
            or (
                "information_schema" in lower_text
                and f"table_name = '{table_name}'" in lower_text
            )
        )

    mutation_phrases = (
        "insert into",
        "update ",
        "delete from",
        "truncate ",
        "drop table",
        "alter table",
        "create table",
        "upsert",
    )
    for phrase in mutation_phrases:
        assert phrase not in lower_text


def test_team_forecast_runbook_names_env_surface_and_local_dsn_boundary() -> None:
    text = _runbook_text()

    for env_var in EXPECTED_ENV_VARS:
        assert env_var in text

    assert "supabase_team_forecast_config" in text
    assert "validate_local_postgres_dsn" in text
    assert "local DSN validator boundary" in text


def test_team_forecast_runbook_omits_secret_and_positive_authorization_language() -> None:
    text = _runbook_text()
    lower_text = text.lower()

    forbidden_patterns = (
        r"postgres(?:ql)?://",
        r"\bdb\.[a-z0-9-]+\.supabase\.co\b",
        r"\b[a-z0-9-]+\.pooler\.supabase\.com\b",
        r"supabase_(?:anon|service)_key",
        r"service_role",
        r"\bsbp_[a-z0-9_=-]{8,}",
        r"\beyj[a-z0-9_-]{20,}",
        r"\bsk-[a-z0-9_-]{20,}",
    )
    for pattern in forbidden_patterns:
        assert re.search(pattern, lower_text) is None

    positive_authorization_patterns = (
        r"\benable(?:s|d)? live\b",
        r"\bauthori[sz]e(?:s|d)? live\b",
        r"\bpermit(?:s|ted)? live\b",
        r"\benable(?:s|d)? auth\b",
        r"\bauthori[sz]e(?:s|d)? auth\b",
        r"\bpermit(?:s|ted)? auth\b",
        r"\benable(?:s|d)? wallet\b",
        r"\bauthori[sz]e(?:s|d)? wallet\b",
        r"\bpermit(?:s|ted)? wallet\b",
        r"\benable(?:s|d)? account\b",
        r"\bauthori[sz]e(?:s|d)? account\b",
        r"\bpermit(?:s|ted)? account\b",
        r"\benable(?:s|d)? order\b",
        r"\bauthori[sz]e(?:s|d)? order\b",
        r"\bpermit(?:s|ted)? order\b",
    )
    for pattern in positive_authorization_patterns:
        assert re.search(pattern, lower_text) is None

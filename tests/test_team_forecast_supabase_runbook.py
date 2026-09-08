from __future__ import annotations

from pathlib import Path
import re


RUNBOOK_PATH = Path("docs/team-forecast-supabase-runbook.md")
MIGRATION_PATH = Path("supabase/migrations/20260701000000_team_forecast_tables.sql")
PROBABILITY_YES_CONTRACT_MIGRATION_PATH = Path(
    "supabase/migrations/20260713000000_team_forecast_probability_yes_contract.sql"
)

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


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    assert marker in text, f"runbook must contain the {heading!r} section"
    return text.split(marker, 1)[1].split("\n## ", 1)[0]


def test_team_forecast_runbook_documents_local_apply_and_operator_commands() -> None:
    text = _runbook_text()

    required_fragments = (
        "sudo -n docker ps",
        "sudo -n docker exec supabase-db psql",
        "psql -v ON_ERROR_STOP=1",
        "/home/ubuntu/supabase/node_modules/.bin/supabase",
        MIGRATION_PATH.as_posix(),
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


def test_team_forecast_runbook_documents_comment_migration_and_readonly_verification() -> None:
    text = _runbook_text()
    lower_text = text.lower()

    expected_order = (
        f"1. `{MIGRATION_PATH.as_posix()}`\n"
        f"2. `{PROBABILITY_YES_CONTRACT_MIGRATION_PATH.as_posix()}`"
    )
    assert expected_order in text
    assert "migrations are operator prerequisites" in lower_text
    assert "must not auto-reset or auto-apply to the host database" in lower_text

    expected_query = """
    SELECT
        col_description('public.team_forecasts'::regclass, a.attnum) AS column_comment
    FROM pg_attribute AS a
    WHERE a.attrelid = 'public.team_forecasts'::regclass
      AND a.attname IN ('forecast_probability', 'selected_side')
    ORDER BY a.attname;
    """
    assert _compact(expected_query) in _compact(text)


def test_comment_verification_runs_a_local_readonly_catalog_command_without_secrets() -> None:
    section = _section(_runbook_text(), "Verify Forecast Column Comments")
    compact_section = _compact(section)
    lower_section = compact_section.lower()

    assert "sudo -n docker exec supabase-db psql" in compact_section
    assert "-U postgres -d postgres" in compact_section
    assert "SELECT" in compact_section
    assert "FROM pg_attribute" in compact_section
    for forbidden_fragment in (
        "postgresql://",
        "password",
        "PGPASSWORD",
        "service_role",
        "supabase_anon_key",
        "supabase_service_key",
    ):
        assert forbidden_fragment.lower() not in lower_section


def test_missing_table_recovery_applies_both_migrations_in_order_with_error_stop() -> None:
    section = _section(_runbook_text(), "Recovery")
    baseline_apply = (
        "sudo -n docker exec -i supabase-db psql -v ON_ERROR_STOP=1 -U postgres -d postgres \\\n  < supabase/migrations/20260701000000_team_forecast_tables.sql"
    )
    comment_apply = (
        "sudo -n docker exec -i supabase-db psql -v ON_ERROR_STOP=1 -U postgres -d postgres \\\n  < supabase/migrations/20260713000000_team_forecast_probability_yes_contract.sql"
    )

    assert "missing-table recovery" in section.lower()
    assert baseline_apply in section
    assert comment_apply in section
    assert section.index(baseline_apply) < section.index(comment_apply)

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260622000006_paper_recommendation_quality_history_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_recommendation_quality_history_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_recommendation_quality_history_reports"
    return compact(match.group(1))


def test_migration_creates_quality_history_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "history_status text not null",
        "source_report_count integer not null",
        "first_source_generated_at timestamptz null",
        "latest_source_generated_at timestamptz null",
        "summary_status_rows_json jsonb not null default '[]'::jsonb",
        "pass_summary_count integer not null",
        "watch_summary_count integer not null",
        "blocked_summary_count integer not null",
        "incomplete_summary_count integer not null",
        "duplicate_generated_at_count integer not null",
        "recurring_blocked_reason_codes_json jsonb not null default '[]'::jsonb",
        "recurring_incomplete_subreports_json jsonb not null default '[]'::jsonb",
        "recurring_incomplete_subreport_count integer not null",
        "reason_codes_json jsonb not null default '[]'::jsonb",
        "reason_code_count integer not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_quality_history_invariants_with_checks():
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (history_status in ('pass', 'watch', 'blocked'))",
        "check (source_report_count >= 0)",
        "check (pass_summary_count >= 0)",
        "check (watch_summary_count >= 0)",
        "check (blocked_summary_count >= 0)",
        "check (incomplete_summary_count >= 0)",
        "check (duplicate_generated_at_count >= 0)",
        "check (recurring_incomplete_subreport_count >= 0)",
        "check (reason_code_count > 0)",
        "check (jsonb_typeof(summary_status_rows_json) = 'array')",
        "check (jsonb_typeof(recurring_blocked_reason_codes_json) = 'array')",
        "check (jsonb_typeof(recurring_incomplete_subreports_json) = 'array')",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
        "check (jsonb_array_length(summary_status_rows_json) = 4)",
        "check (source_report_count = pass_summary_count + watch_summary_count + blocked_summary_count + incomplete_summary_count)",
        "check (reason_code_count = jsonb_array_length(reason_codes_json))",
        "check (recurring_incomplete_subreport_count = jsonb_array_length(recurring_incomplete_subreports_json))",
    )
    for check in expected_checks:
        assert check in body


def test_migration_enforces_source_timestamp_relationships():
    body = table_body(migration_sql())

    assert (
        "source_report_count = 0 and first_source_generated_at is null "
        "and latest_source_generated_at is null"
    ) in body
    assert (
        "source_report_count > 0 and first_source_generated_at is not null "
        "and latest_source_generated_at is not null "
        "and first_source_generated_at <= latest_source_generated_at"
    ) in body


def test_migration_uses_jsonb_for_payloads_and_avoids_float_columns():
    body = table_body(migration_sql())

    assert "summary_status_rows_json jsonb" in body
    assert "recurring_blocked_reason_codes_json jsonb" in body
    assert "recurring_incomplete_subreports_json jsonb" in body
    assert "reason_codes_json jsonb" in body
    assert "payload_json jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_prqhr_generated_at on public.paper_recommendation_quality_history_reports (generated_at desc);",
        "create index if not exists idx_prqhr_config_version_generated_at on public.paper_recommendation_quality_history_reports (config_version, generated_at desc);",
        "create index if not exists idx_prqhr_history_status_generated_at on public.paper_recommendation_quality_history_reports (history_status, generated_at desc);",
        "create index if not exists idx_prqhr_recurring_blocked_reason_codes_json on public.paper_recommendation_quality_history_reports using gin (recurring_blocked_reason_codes_json jsonb_path_ops);",
        "create index if not exists idx_prqhr_reason_codes_json on public.paper_recommendation_quality_history_reports using gin (reason_codes_json jsonb_path_ops);",
        "create index if not exists idx_prqhr_payload_json on public.paper_recommendation_quality_history_reports using gin (payload_json jsonb_path_ops);",
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
        r"\bcancel(?:s|ed|ing|lation)?\b",
        r"\bsign(?:s|ed|ing|ature)?\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
        r"\bexchange\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260702000000_team_research_assignment_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.team_research_assignment_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.team_research_assignment_reports"
    return compact(match.group(1))


def test_migration_creates_team_research_assignment_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "source_queue_config_version text not null",
        "source_route_config_version text not null",
        "source_memory_config_version text not null",
        "assignment_status text not null",
        "assignment_count integer not null",
        "assigned_count integer not null",
        "watch_count integer not null",
        "blocked_count integer not null",
        "reason_codes_json jsonb not null default '[]'::jsonb",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_team_research_assignment_invariants_with_checks():
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (assignment_status in ('ready', 'watch', 'blocked'))",
        "check (assignment_count >= 0)",
        "check (assigned_count >= 0)",
        "check (watch_count >= 0)",
        "check (blocked_count >= 0)",
        "check (assigned_count + watch_count + blocked_count = assignment_count)",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (((payload_json ->> 'generated_at')::timestamptz = generated_at) is true)",
        "check ((payload_json ->> 'config_version' = config_version) is true)",
        "check ((payload_json ->> 'source_queue_config_version' = source_queue_config_version) is true)",
        "check ((payload_json ->> 'source_route_config_version' = source_route_config_version) is true)",
        "check ((payload_json ->> 'source_memory_config_version' = source_memory_config_version) is true)",
        "check ((payload_json ->> 'assignment_status' = assignment_status) is true)",
        "check (((payload_json ->> 'assignment_count')::integer = assignment_count) is true)",
        "check (((payload_json ->> 'assigned_count')::integer = assigned_count) is true)",
        "check (((payload_json ->> 'watch_count')::integer = watch_count) is true)",
        "check (((payload_json ->> 'blocked_count')::integer = blocked_count) is true)",
        "check ((payload_json -> 'reason_codes' = reason_codes_json) is true)",
        "check ((payload_json ->> 'paper_only' = 'true') is true)",
        "check ((payload_json ->> 'report_only' = 'true') is true)",
        "check ((payload_json ->> 'readonly' = 'true') is true)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_adds_useful_team_research_assignment_lookup_indexes():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_trar_generated_at on public.team_research_assignment_reports (generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_trar_assignment_status_generated_at on public.team_research_assignment_reports (assignment_status, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_trar_config_version_generated_at on public.team_research_assignment_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_trar_reason_codes_json_gin on public.team_research_assignment_reports using gin (reason_codes_json jsonb_path_ops);",
        "create index if not exists idx_trar_payload_json_gin on public.team_research_assignment_reports using gin (payload_json jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_enables_rls_and_documents_team_research_assignment_table():
    sql = compact(migration_sql())

    assert (
        "alter table public.team_research_assignment_reports "
        "enable row level security;"
    ) in sql
    assert "comment on table public.team_research_assignment_reports is" in sql


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
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

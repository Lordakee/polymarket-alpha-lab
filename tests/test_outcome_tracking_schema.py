import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260619010200_outcome_tracking_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.outcome_tracking_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.outcome_tracking_reports"
    return compact(match.group(1))


def test_migration_creates_outcome_tracking_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "total_markets_checked integer not null",
        "resolved_count integer not null",
        "pending_count integer not null",
        "observation_count integer not null",
        "forecast_evidence_status text",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_outcome_tracking_invariants_with_checks():
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (total_markets_checked >= 0)",
        "check (resolved_count >= 0)",
        "check (pending_count >= 0)",
        "check (observation_count >= 0)",
        "check (resolved_count + pending_count = total_markets_checked)",
        "check (observation_count = resolved_count)",
        "check (forecast_evidence_status is null or forecast_evidence_status in ('incomplete_data', 'insufficient_evidence', 'blocked_by_quality', 'paper_review_ready'))",
        "check (jsonb_typeof(payload) = 'object')",
        "check (paper_only is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_adds_useful_lookup_indexes():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_otr_generated_at on public.outcome_tracking_reports (generated_at desc);",
        "create index if not exists idx_otr_config_version_generated_at on public.outcome_tracking_reports (config_version, generated_at desc);",
        "create index if not exists idx_otr_forecast_evidence_status_generated_at on public.outcome_tracking_reports (forecast_evidence_status, generated_at desc);",
        "create index if not exists idx_otr_payload_gin on public.outcome_tracking_reports using gin (payload jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_phase_1_forbidden_terms():
    sql = migration_sql().lower()

    forbidden_patterns = (
        r"\bgamma\b",
        r"\bsettlement\b",
        r"\baction\b",
        r"\border\b",
        r"\bauth\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260619000000_paper_recommendation_cycle_snapshots.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_recommendation_cycle_snapshots\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_recommendation_cycle_snapshots"
    return compact(match.group(1))


def test_migration_creates_snapshot_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "snapshot_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "final_status text not null",
        "stage_counts jsonb not null",
        "artifact_counts jsonb not null",
        "reason_codes jsonb not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_snapshot_invariants_with_checks():
    body = table_body(migration_sql())

    expected_checks = (
        "check (snapshot_sha256 ~ '^[a-f0-9]{64}$')",
        "check (final_status in ('pass', 'watch', 'blocked'))",
        "check (jsonb_typeof(stage_counts) = 'object')",
        "check (jsonb_typeof(artifact_counts) = 'object')",
        "check (jsonb_typeof(reason_codes) = 'array')",
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
        "create index if not exists idx_prcs_generated_at on public.paper_recommendation_cycle_snapshots (generated_at desc);",
        "create index if not exists idx_prcs_final_status_generated_at on public.paper_recommendation_cycle_snapshots (final_status, generated_at desc);",
        "create index if not exists idx_prcs_reason_codes_gin on public.paper_recommendation_cycle_snapshots using gin (reason_codes jsonb_path_ops);",
        "create index if not exists idx_prcs_payload_gin on public.paper_recommendation_cycle_snapshots using gin (payload jsonb_path_ops);",
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

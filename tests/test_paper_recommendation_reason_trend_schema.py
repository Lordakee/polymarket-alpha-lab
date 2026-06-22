import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260622000002_paper_recommendation_reason_trend_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_recommendation_reason_trend_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_recommendation_reason_trend_reports"
    return compact(match.group(1))


def test_migration_creates_reason_trend_report_table_with_required_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "source_report_count integer not null",
        "reason_trend_rows jsonb not null default '[]'::jsonb",
        "transition_trend_rows jsonb not null default '[]'::jsonb",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_reason_trend_report_invariants_with_checks() -> None:
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (source_report_count >= 0)",
        "check (jsonb_typeof(reason_trend_rows) = 'array')",
        "check (jsonb_typeof(transition_trend_rows) = 'array')",
        "check (jsonb_typeof(payload) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_uses_jsonb_for_payloads_and_avoids_float_columns() -> None:
    body = table_body(migration_sql())

    assert "reason_trend_rows jsonb" in body
    assert "transition_trend_rows jsonb" in body
    assert "payload jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes() -> None:
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_prrtr_generated_at on public.paper_recommendation_reason_trend_reports (generated_at desc);",
        "create index if not exists idx_prrtr_config_version_generated_at on public.paper_recommendation_reason_trend_reports (config_version, generated_at desc);",
        "create index if not exists idx_prrtr_reason_trend_rows_gin on public.paper_recommendation_reason_trend_reports using gin (reason_trend_rows jsonb_path_ops);",
        "create index if not exists idx_prrtr_transition_trend_rows_gin on public.paper_recommendation_reason_trend_reports using gin (transition_trend_rows jsonb_path_ops);",
        "create index if not exists idx_prrtr_payload_gin on public.paper_recommendation_reason_trend_reports using gin (payload jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_live_trading_or_account_terms() -> None:
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

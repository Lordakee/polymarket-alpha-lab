import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260622000000_paper_recommendation_health_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_recommendation_health_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_recommendation_health_reports"
    return compact(match.group(1))


def test_migration_creates_health_report_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "health_status text not null",
        "row_count integer not null",
        "recommend_count integer not null",
        "watch_count integer not null",
        "reject_count integer not null",
        "average_net_probability_edge numeric not null",
        "average_total_cost_per_share numeric not null",
        "top_recommendation_score numeric not null",
        "reason_code_counts jsonb not null default '[]'::jsonb",
        "max_average_cost_per_share numeric not null",
        "min_recommend_share numeric not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_health_report_invariants_with_checks():
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (health_status in ('pass', 'watch', 'blocked'))",
        "check (row_count >= 0)",
        "check (recommend_count >= 0)",
        "check (watch_count >= 0)",
        "check (reject_count >= 0)",
        "check (row_count = recommend_count + watch_count + reject_count)",
        "check (average_total_cost_per_share >= 0)",
        "check (top_recommendation_score >= 0)",
        "check (jsonb_typeof(reason_code_counts) = 'array')",
        "check (max_average_cost_per_share >= 0)",
        "check (min_recommend_share >= 0 and min_recommend_share <= 1)",
        "check (jsonb_typeof(payload) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_uses_numeric_for_decimal_scalars_and_jsonb_for_payloads():
    body = table_body(migration_sql())

    decimal_columns = (
        "average_net_probability_edge",
        "average_total_cost_per_share",
        "top_recommendation_score",
        "max_average_cost_per_share",
        "min_recommend_share",
    )
    for column in decimal_columns:
        assert f"{column} numeric" in body

    assert "reason_code_counts jsonb" in body
    assert "payload jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_prhr_generated_at on public.paper_recommendation_health_reports (generated_at desc);",
        "create index if not exists idx_prhr_config_version_generated_at on public.paper_recommendation_health_reports (config_version, generated_at desc);",
        "create index if not exists idx_prhr_health_status_generated_at on public.paper_recommendation_health_reports (health_status, generated_at desc);",
        "create index if not exists idx_prhr_reason_code_counts_gin on public.paper_recommendation_health_reports using gin (reason_code_counts jsonb_path_ops);",
        "create index if not exists idx_prhr_payload_gin on public.paper_recommendation_health_reports using gin (payload jsonb_path_ops);",
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
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260621000003_paper_recommendation_risk_budget_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_recommendation_risk_budget_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_recommendation_risk_budget_reports"
    return compact(match.group(1))


def test_migration_creates_risk_budget_report_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "status text not null",
        "reason_codes jsonb not null default '[]'::jsonb",
        "total_suggested_notional numeric not null",
        "remaining_total_notional numeric null",
        "total_notional_utilization numeric null",
        "largest_single_recommendation_share numeric null",
        "selected_count integer not null",
        "blocked_count integer not null",
        "nav_notional numeric null",
        "max_total_utilization numeric not null",
        "max_single_recommendation_share numeric not null",
        "min_remaining_notional numeric not null",
        "max_selected_count integer not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_risk_budget_report_invariants_with_checks():
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (status in ('pass', 'watch', 'blocked'))",
        "check (jsonb_typeof(reason_codes) = 'array')",
        "check (total_suggested_notional >= 0)",
        "check (remaining_total_notional is null or remaining_total_notional >= 0)",
        "check (total_notional_utilization is null or (total_notional_utilization >= 0 and total_notional_utilization <= 1))",
        "check (largest_single_recommendation_share is null or (largest_single_recommendation_share >= 0 and largest_single_recommendation_share <= 1))",
        "check (selected_count >= 0)",
        "check (blocked_count >= 0)",
        "check (nav_notional is null or nav_notional >= 0)",
        "check (max_total_utilization > 0 and max_total_utilization <= 1)",
        "check (max_single_recommendation_share > 0 and max_single_recommendation_share <= 1)",
        "check (min_remaining_notional >= 0)",
        "check (max_selected_count > 0)",
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
        "total_suggested_notional",
        "remaining_total_notional",
        "total_notional_utilization",
        "largest_single_recommendation_share",
        "nav_notional",
        "max_total_utilization",
        "max_single_recommendation_share",
        "min_remaining_notional",
    )
    for column in decimal_columns:
        assert f"{column} numeric" in body

    assert "reason_codes jsonb" in body
    assert "payload jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_prrbr_generated_at on public.paper_recommendation_risk_budget_reports (generated_at desc);",
        "create index if not exists idx_prrbr_config_version_generated_at on public.paper_recommendation_risk_budget_reports (config_version, generated_at desc);",
        "create index if not exists idx_prrbr_status_generated_at on public.paper_recommendation_risk_budget_reports (status, generated_at desc);",
        "create index if not exists idx_prrbr_reason_codes_gin on public.paper_recommendation_risk_budget_reports using gin (reason_codes jsonb_path_ops);",
        "create index if not exists idx_prrbr_payload_gin on public.paper_recommendation_risk_budget_reports using gin (payload jsonb_path_ops);",
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

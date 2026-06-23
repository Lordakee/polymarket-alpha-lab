import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260622000005_paper_recommendation_reason_trend_health_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def compact_expression(sql: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\(\s+|\s+\)", lambda match: match.group(0).strip(), sql).strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_recommendation_reason_trend_health_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_recommendation_reason_trend_health_reports"
    return compact(match.group(1))


def test_migration_creates_reason_trend_health_table_with_required_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "health_status text not null",
        "source_report_count integer not null",
        "reason_code_count integer not null",
        "blocked_status_count integer not null",
        "blocked_status_share numeric",
        "reject_status_count integer not null",
        "reject_status_share numeric",
        "new_reason_code_count integer not null",
        "transition_count integer not null",
        "persistent_reason_codes jsonb not null default '[]'::jsonb",
        "reason_codes jsonb not null default '[]'::jsonb",
        "max_blocked_status_share numeric not null",
        "max_reject_status_share numeric not null",
        "max_new_reason_code_count integer not null",
        "max_transition_count integer not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_reason_trend_health_invariants_with_checks() -> None:
    body = table_body(migration_sql())
    expression_body = compact_expression(body)

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (health_status in ('pass', 'watch', 'blocked'))",
        "check (source_report_count >= 0)",
        "check (reason_code_count >= 0)",
        "check (blocked_status_count >= 0)",
        "check (blocked_status_share is null or (blocked_status_share >= 0 and blocked_status_share <= 1))",
        "check (reject_status_count >= 0)",
        "check (reject_status_share is null or (reject_status_share >= 0 and reject_status_share <= 1))",
        "check (new_reason_code_count >= 0)",
        "check (transition_count >= 0)",
        "check (jsonb_typeof(persistent_reason_codes) = 'array')",
        "check (jsonb_typeof(reason_codes) = 'array')",
        "check (max_blocked_status_share >= 0 and max_blocked_status_share <= 1)",
        "check (max_reject_status_share >= 0 and max_reject_status_share <= 1)",
        "check (max_new_reason_code_count >= 0)",
        "check (max_transition_count >= 0)",
        "check (jsonb_typeof(payload) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
        "check (reason_code_count = jsonb_array_length(reason_codes))",
        "check (jsonb_array_length(persistent_reason_codes) <= reason_code_count)",
        (
            "check ((reason_code_count = 0 and blocked_status_count = 0 and "
            "blocked_status_share is null and reject_status_count = 0 and "
            "reject_status_share is null) or (reason_code_count > 0 and "
            "blocked_status_share is not null and reject_status_share is not null))"
        ),
        (
            "check (source_report_count > 0 or (health_status = 'blocked' and "
            "reason_code_count = 0 and blocked_status_count = 0 and "
            "blocked_status_share is null and reject_status_count = 0 and "
            "reject_status_share is null and new_reason_code_count = 0 and "
            "transition_count = 0 and jsonb_array_length(persistent_reason_codes) = 0 "
            "and jsonb_array_length(reason_codes) = 0))"
        ),
    )
    for check in expected_checks:
        assert compact_expression(check) in expression_body


def test_migration_uses_numeric_for_decimal_scalars_and_jsonb_for_payloads() -> None:
    body = table_body(migration_sql())

    for column in (
        "blocked_status_share",
        "reject_status_share",
        "max_blocked_status_share",
        "max_reject_status_share",
    ):
        assert f"{column} numeric" in body
    assert "persistent_reason_codes jsonb" in body
    assert "reason_codes jsonb" in body
    assert "payload jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes() -> None:
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_prrthr_generated_at on public.paper_recommendation_reason_trend_health_reports (generated_at desc);",
        "create index if not exists idx_prrthr_config_version_generated_at on public.paper_recommendation_reason_trend_health_reports (config_version, generated_at desc);",
        "create index if not exists idx_prrthr_health_status_generated_at on public.paper_recommendation_reason_trend_health_reports (health_status, generated_at desc);",
        "create index if not exists idx_prrthr_reason_codes_gin on public.paper_recommendation_reason_trend_health_reports using gin (reason_codes jsonb_path_ops);",
        "create index if not exists idx_prrthr_payload_gin on public.paper_recommendation_reason_trend_health_reports using gin (payload jsonb_path_ops);",
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

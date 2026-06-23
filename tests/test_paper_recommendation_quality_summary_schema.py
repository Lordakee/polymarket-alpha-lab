import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260622000008_paper_recommendation_quality_summary_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def compact_expression(sql: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        re.sub(r"\(\s+|\s+\)", lambda match: match.group(0).strip(), sql).strip().lower(),
    )


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_recommendation_quality_summary_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_recommendation_quality_summary_reports"
    return compact(match.group(1))


def test_migration_creates_quality_summary_table_with_required_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "summary_status text not null",
        "subreport_count integer not null",
        "pass_count integer not null",
        "watch_count integer not null",
        "blocked_count integer not null",
        "incomplete_count integer not null",
        "reason_code_counts_json jsonb not null default '[]'::jsonb",
        "reason_codes_json jsonb not null default '[]'::jsonb",
        "subreports_json jsonb not null default '[]'::jsonb",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_quality_summary_invariants_with_checks() -> None:
    expression_body = compact_expression(table_body(migration_sql()))

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (summary_status in ('pass', 'watch', 'blocked', 'incomplete'))",
        "check (subreport_count >= 0)",
        "check (pass_count >= 0)",
        "check (watch_count >= 0)",
        "check (blocked_count >= 0)",
        "check (incomplete_count >= 0)",
        "check (jsonb_typeof(reason_code_counts_json) = 'array')",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(subreports_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
        "check (subreport_count = 5)",
        "check (subreport_count = pass_count + watch_count + blocked_count + incomplete_count)",
        "check (subreport_count = jsonb_array_length(subreports_json))",
        "check (jsonb_array_length(reason_codes_json) = jsonb_array_length(reason_code_counts_json))",
        "check ((subreports_json -> 0 ->> 'report_name') = 'health')",
        "check ((subreports_json -> 1 ->> 'report_name') = 'consistency')",
        "check ((subreports_json -> 2 ->> 'report_name') = 'risk_budget')",
        "check ((subreports_json -> 3 ->> 'report_name') = 'reason_trend')",
        "check ((subreports_json -> 4 ->> 'report_name') = 'rank_stability')",
        "check (pass_count = jsonb_array_length(jsonb_path_query_array(subreports_json, '$[*] ? (@.status == \"pass\")')))",
        "check (watch_count = jsonb_array_length(jsonb_path_query_array(subreports_json, '$[*] ? (@.status == \"watch\")')))",
        "check (blocked_count = jsonb_array_length(jsonb_path_query_array(subreports_json, '$[*] ? (@.status == \"blocked\")')))",
        "check (incomplete_count = jsonb_array_length(jsonb_path_query_array(subreports_json, '$[*] ? (@.status == \"incomplete\")')))",
        (
            "check ((summary_status = 'blocked' and blocked_count > 0) or "
            "(summary_status = 'incomplete' and blocked_count = 0 and incomplete_count > 0) or "
            "(summary_status = 'watch' and blocked_count = 0 and incomplete_count = 0 and watch_count > 0) or "
            "(summary_status = 'pass' and blocked_count = 0 and incomplete_count = 0 and watch_count = 0))"
        ),
        "check ((payload_json ->> 'paper_only') = 'true')",
        "check ((payload_json ->> 'report_only') = 'true')",
        "check ((payload_json ->> 'readonly') = 'true')",
        (
            "check (not jsonb_path_exists(subreports_json, "
            "'$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'))"
        ),
        (
            "check (not jsonb_path_exists(payload_json, "
            "'$.subreports[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'))"
        ),
    )
    for check in expected_checks:
        assert compact_expression(check) in expression_body


def test_migration_uses_jsonb_for_payloads_and_no_float_types() -> None:
    body = table_body(migration_sql())

    assert "reason_code_counts_json jsonb" in body
    assert "reason_codes_json jsonb" in body
    assert "subreports_json jsonb" in body
    assert "payload_json jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes() -> None:
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_prqsr_generated_at on public.paper_recommendation_quality_summary_reports (generated_at desc);",
        "create index if not exists idx_prqsr_config_version_generated_at on public.paper_recommendation_quality_summary_reports (config_version, generated_at desc);",
        "create index if not exists idx_prqsr_summary_status_generated_at on public.paper_recommendation_quality_summary_reports (summary_status, generated_at desc);",
        "create index if not exists idx_prqsr_reason_codes_json on public.paper_recommendation_quality_summary_reports using gin (reason_codes_json jsonb_path_ops);",
        "create index if not exists idx_prqsr_subreports_json on public.paper_recommendation_quality_summary_reports using gin (subreports_json jsonb_path_ops);",
        "create index if not exists idx_prqsr_payload_json on public.paper_recommendation_quality_summary_reports using gin (payload_json jsonb_path_ops);",
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

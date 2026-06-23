from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260623000000_paper_research_packet_quality_reports.sql"
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
        r"public\.paper_research_packet_quality_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_research_packet_quality_reports"
    return compact(match.group(1))


def test_migration_creates_quality_report_table_with_required_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "source_generated_at timestamptz not null",
        "source_config_version text not null",
        "input_row_count integer not null",
        "packet_row_count integer not null",
        "included_count integer not null",
        "skipped_count integer not null",
        "high_priority_count integer not null",
        "medium_priority_count integer not null",
        "low_priority_count integer not null",
        "source_age_seconds integer not null",
        "included_share numeric(18, 6) null",
        "skipped_share numeric(18, 6) null",
        "check_count integer not null",
        "pass_count integer not null",
        "watch_count integer not null",
        "blocked_count integer not null",
        "quality_status text not null",
        "check_rows_json jsonb not null default '[]'::jsonb",
        "reason_code_counts_json jsonb not null default '[]'::jsonb",
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


def test_migration_enforces_quality_report_invariants_with_checks() -> None:
    expression_body = compact_expression(table_body(migration_sql()))

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (input_row_count >= 0)",
        "check (packet_row_count >= 0)",
        "check (included_count >= 0)",
        "check (skipped_count >= 0)",
        "check (high_priority_count >= 0)",
        "check (medium_priority_count >= 0)",
        "check (low_priority_count >= 0)",
        "check (source_age_seconds >= 0)",
        "check (included_share is null or (included_share >= 0 and included_share <= 1))",
        "check (skipped_share is null or (skipped_share >= 0 and skipped_share <= 1))",
        "check (check_count >= 0)",
        "check (pass_count >= 0)",
        "check (watch_count >= 0)",
        "check (blocked_count >= 0)",
        "check (quality_status in ('pass', 'watch', 'blocked'))",
        "check (jsonb_typeof(check_rows_json) = 'array')",
        "check (jsonb_typeof(reason_code_counts_json) = 'array')",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
        "check (source_generated_at <= generated_at)",
        "check (input_row_count >= packet_row_count)",
        "check (packet_row_count = included_count + skipped_count)",
        "check (included_count = high_priority_count + medium_priority_count + low_priority_count)",
        "check (check_count = 3)",
        "check (check_count = pass_count + watch_count + blocked_count)",
        "check (check_count = jsonb_array_length(check_rows_json))",
        "check (reason_code_count >= 0)",
        "check (reason_code_count = jsonb_array_length(reason_codes_json))",
        "check (reason_code_count = jsonb_array_length(reason_code_counts_json))",
        "check ((check_rows_json -> 0 ->> 'check_name') = 'source_freshness')",
        "check ((check_rows_json -> 1 ->> 'check_name') = 'packet_population')",
        "check ((check_rows_json -> 2 ->> 'check_name') = 'skip_pressure')",
        "check (pass_count = jsonb_array_length(jsonb_path_query_array(check_rows_json, '$[*] ? (@.status == \"pass\")')))",
        "check (watch_count = jsonb_array_length(jsonb_path_query_array(check_rows_json, '$[*] ? (@.status == \"watch\")')))",
        "check (blocked_count = jsonb_array_length(jsonb_path_query_array(check_rows_json, '$[*] ? (@.status == \"blocked\")')))",
        (
            "check ((quality_status = 'blocked' and blocked_count > 0) or "
            "(quality_status = 'watch' and blocked_count = 0 and watch_count > 0) or "
            "(quality_status = 'pass' and blocked_count = 0 and watch_count = 0))"
        ),
        "check (((payload_json -> 'paper_only') = 'true'::jsonb) is true)",
        "check (((payload_json -> 'report_only') = 'true'::jsonb) is true)",
        "check (((payload_json -> 'readonly') = 'true'::jsonb) is true)",
        (
            "check (payload_json ? 'generated_at' and "
            "jsonb_typeof(payload_json -> 'generated_at') = 'string' and "
            "(payload_json ->> 'generated_at')::timestamptz = generated_at)"
        ),
        (
            "check (payload_json ? 'config_version' and "
            "jsonb_typeof(payload_json -> 'config_version') = 'string' and "
            "payload_json ->> 'config_version' = config_version)"
        ),
        (
            "check (payload_json ? 'source_generated_at' and "
            "jsonb_typeof(payload_json -> 'source_generated_at') = 'string' and "
            "(payload_json ->> 'source_generated_at')::timestamptz = source_generated_at)"
        ),
        (
            "check (payload_json ? 'source_config_version' and "
            "jsonb_typeof(payload_json -> 'source_config_version') = 'string' and "
            "payload_json ->> 'source_config_version' = source_config_version)"
        ),
        "check (((payload_json -> 'input_row_count') = to_jsonb(input_row_count)) is true)",
        "check (((payload_json -> 'packet_row_count') = to_jsonb(packet_row_count)) is true)",
        "check (((payload_json -> 'included_count') = to_jsonb(included_count)) is true)",
        "check (((payload_json -> 'skipped_count') = to_jsonb(skipped_count)) is true)",
        "check (((payload_json -> 'high_priority_count') = to_jsonb(high_priority_count)) is true)",
        "check (((payload_json -> 'medium_priority_count') = to_jsonb(medium_priority_count)) is true)",
        "check (((payload_json -> 'low_priority_count') = to_jsonb(low_priority_count)) is true)",
        "check (((payload_json -> 'source_age_seconds') = to_jsonb(source_age_seconds)) is true)",
        (
            "check ((included_share is null and ((payload_json -> 'included_share') = 'null'::jsonb) is true) "
            "or (included_share is not null and jsonb_typeof(payload_json -> 'included_share') = 'string' "
            "and (payload_json ->> 'included_share')::numeric(18, 6) = included_share))"
        ),
        (
            "check ((skipped_share is null and ((payload_json -> 'skipped_share') = 'null'::jsonb) is true) "
            "or (skipped_share is not null and jsonb_typeof(payload_json -> 'skipped_share') = 'string' "
            "and (payload_json ->> 'skipped_share')::numeric(18, 6) = skipped_share))"
        ),
        "check (((payload_json -> 'check_count') = to_jsonb(check_count)) is true)",
        "check (((payload_json -> 'pass_count') = to_jsonb(pass_count)) is true)",
        "check (((payload_json -> 'watch_count') = to_jsonb(watch_count)) is true)",
        "check (((payload_json -> 'blocked_count') = to_jsonb(blocked_count)) is true)",
        (
            "check (payload_json ? 'quality_status' and "
            "jsonb_typeof(payload_json -> 'quality_status') = 'string' and "
            "payload_json ->> 'quality_status' = quality_status)"
        ),
        "check (((payload_json -> 'check_rows') = check_rows_json) is true)",
        "check (((payload_json -> 'reason_code_counts') = reason_code_counts_json) is true)",
        "check (reason_codes_json = jsonb_path_query_array(reason_code_counts_json, '$[*].reason_code'))",
    )
    for check in expected_checks:
        assert compact_expression(check) in expression_body


def test_migration_enforces_nested_hard_flags() -> None:
    expression_body = compact_expression(table_body(migration_sql()))

    expected_checks = (
        (
            "check (not jsonb_path_exists(check_rows_json, "
            "'$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'))"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(check_rows_json, "
            "'$[*] ? (@.paper_only == true)')) = check_count)"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(check_rows_json, "
            "'$[*] ? (@.report_only == true)')) = check_count)"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(check_rows_json, "
            "'$[*] ? (@.readonly == true)')) = check_count)"
        ),
        (
            "check (not jsonb_path_exists(reason_code_counts_json, "
            "'$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'))"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(reason_code_counts_json, "
            "'$[*] ? (@.paper_only == true)')) = reason_code_count)"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(reason_code_counts_json, "
            "'$[*] ? (@.report_only == true)')) = reason_code_count)"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(reason_code_counts_json, "
            "'$[*] ? (@.readonly == true)')) = reason_code_count)"
        ),
        (
            "check (not jsonb_path_exists(payload_json, "
            "'$.check_rows[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'))"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(payload_json, "
            "'$.check_rows[*] ? (@.paper_only == true)')) = check_count)"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(payload_json, "
            "'$.check_rows[*] ? (@.report_only == true)')) = check_count)"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(payload_json, "
            "'$.check_rows[*] ? (@.readonly == true)')) = check_count)"
        ),
        (
            "check (not jsonb_path_exists(payload_json, "
            "'$.reason_code_counts[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'))"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(payload_json, "
            "'$.reason_code_counts[*] ? (@.paper_only == true)')) = reason_code_count)"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(payload_json, "
            "'$.reason_code_counts[*] ? (@.report_only == true)')) = reason_code_count)"
        ),
        (
            "check (jsonb_array_length(jsonb_path_query_array(payload_json, "
            "'$.reason_code_counts[*] ? (@.readonly == true)')) = reason_code_count)"
        ),
    )
    for check in expected_checks:
        assert compact_expression(check) in expression_body


def test_migration_uses_numeric_and_jsonb_without_float_types() -> None:
    body = table_body(migration_sql())

    assert "included_share numeric(18, 6)" in body
    assert "skipped_share numeric(18, 6)" in body
    assert "check_rows_json jsonb" in body
    assert "reason_code_counts_json jsonb" in body
    assert "reason_codes_json jsonb" in body
    assert "payload_json jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes() -> None:
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_prpqr_generated_at on public.paper_research_packet_quality_reports (generated_at desc);",
        "create index if not exists idx_prpqr_config_version_generated_at on public.paper_research_packet_quality_reports (config_version, generated_at desc);",
        "create index if not exists idx_prpqr_quality_status_generated_at on public.paper_research_packet_quality_reports (quality_status, generated_at desc);",
        "create index if not exists idx_prpqr_source_generated_at on public.paper_research_packet_quality_reports (source_generated_at desc);",
        "create index if not exists idx_prpqr_check_rows_json on public.paper_research_packet_quality_reports using gin (check_rows_json jsonb_path_ops);",
        "create index if not exists idx_prpqr_reason_codes_json on public.paper_research_packet_quality_reports using gin (reason_codes_json jsonb_path_ops);",
        "create index if not exists idx_prpqr_payload_json on public.paper_research_packet_quality_reports using gin (payload_json jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_matches_existing_no_rls_posture() -> None:
    sql = migration_sql().lower()

    assert "row level security" not in sql
    assert "create policy" not in sql
    assert "alter table" not in sql


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
        r"\bexchange\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

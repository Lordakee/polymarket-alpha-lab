from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260624000001_paper_autonomous_allocation_proposal_db_history_health_reports.sql"
)
TABLE_NAME = "paper_autonomous_allocation_proposal_db_history_health_reports"


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def compact_expression(sql: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        re.sub(r"\(\s+|\s+\)", lambda match: match.group(0).strip(), sql)
        .strip()
        .lower(),
    )


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+public\."
        + re.escape(TABLE_NAME)
        + r"\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{TABLE_NAME}"
    return compact(match.group(1))


def test_migration_creates_db_history_health_table_with_required_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "health_status text not null",
        "recommended_next_step text not null",
        "history_report_count integer not null",
        "pass_report_count integer not null",
        "watch_report_count integer not null",
        "blocked_report_count integer not null",
        "latest_history_status text",
        "latest_proposal_status text",
        "latest_allocated_count integer",
        "latest_total_allocated_paper_notional numeric(38, 6)",
        "max_source_age_seconds integer",
        "latest_source_age_seconds integer",
        "duplicate_latest_report_generated_at_count integer not null",
        "reason_code_counts_json jsonb not null",
        "reason_codes_json jsonb not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_db_history_health_invariants_with_checks() -> None:
    body = table_body(migration_sql())
    expression_body = compact_expression(body)

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (health_status in ('pass', 'watch', 'blocked'))",
        "check (recommended_next_step = case health_status when 'pass' then 'allow_paper_autonomous_allocation_proposal_history_review' when 'watch' then 'throttle_paper_autonomous_allocation_proposal_history_review' when 'blocked' then 'block_paper_autonomous_allocation_proposal_history_review' end)",
        "check (history_report_count >= 0)",
        "check (pass_report_count >= 0)",
        "check (watch_report_count >= 0)",
        "check (blocked_report_count >= 0)",
        "check (history_report_count = pass_report_count + watch_report_count + blocked_report_count)",
        "check (latest_history_status is null or latest_history_status in ('pass', 'watch', 'blocked'))",
        "check (latest_proposal_status is null or latest_proposal_status in ('pass', 'watch', 'blocked'))",
        "check (latest_allocated_count is null or latest_allocated_count >= 0)",
        "check (latest_total_allocated_paper_notional is null or latest_total_allocated_paper_notional >= 0)",
        "check (max_source_age_seconds is null or max_source_age_seconds >= 0)",
        "check (latest_source_age_seconds is null or latest_source_age_seconds >= 0)",
        "check (latest_source_age_seconds is null or max_source_age_seconds is null or latest_source_age_seconds <= max_source_age_seconds)",
        "check (duplicate_latest_report_generated_at_count >= 0)",
        "check (jsonb_typeof(reason_code_counts_json) = 'array')",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert compact_expression(check) in expression_body


def test_migration_enforces_empty_and_nonempty_snapshot_shape() -> None:
    expression_body = compact_expression(table_body(migration_sql()))

    for expected_check in (
        (
            "check ((history_report_count = 0 and latest_history_status is null and "
            "latest_proposal_status is null and latest_allocated_count is null and "
            "latest_total_allocated_paper_notional is null and max_source_age_seconds is null "
            "and latest_source_age_seconds is null and "
            "duplicate_latest_report_generated_at_count = 0 and "
            "jsonb_array_length(reason_code_counts_json) = 0) or "
            "(history_report_count > 0 and latest_history_status is not null and "
            "latest_proposal_status is not null and "
            "jsonb_array_length(reason_code_counts_json) > 0))"
        ),
    ):
        assert compact_expression(expected_check) in expression_body


def test_migration_enforces_payload_scalar_parity() -> None:
    body = table_body(migration_sql())
    expression_body = compact_expression(body)

    expected_checks = (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (payload_json ? 'health_status' and jsonb_typeof(payload_json -> 'health_status') = 'string' and payload_json ->> 'health_status' = health_status)",
        "check (payload_json ? 'recommended_next_step' and jsonb_typeof(payload_json -> 'recommended_next_step') = 'string' and payload_json ->> 'recommended_next_step' = recommended_next_step)",
        "check (payload_json ? 'history_report_count' and jsonb_typeof(payload_json -> 'history_report_count') = 'number' and (payload_json ->> 'history_report_count')::integer = history_report_count)",
        "check (payload_json ? 'pass_report_count' and jsonb_typeof(payload_json -> 'pass_report_count') = 'number' and (payload_json ->> 'pass_report_count')::integer = pass_report_count)",
        "check (payload_json ? 'watch_report_count' and jsonb_typeof(payload_json -> 'watch_report_count') = 'number' and (payload_json ->> 'watch_report_count')::integer = watch_report_count)",
        "check (payload_json ? 'blocked_report_count' and jsonb_typeof(payload_json -> 'blocked_report_count') = 'number' and (payload_json ->> 'blocked_report_count')::integer = blocked_report_count)",
        "check (payload_json ? 'latest_history_status' and ((payload_json -> 'latest_history_status' = 'null'::jsonb and latest_history_status is null) or (jsonb_typeof(payload_json -> 'latest_history_status') = 'string' and payload_json ->> 'latest_history_status' = latest_history_status)))",
        "check (payload_json ? 'latest_proposal_status' and ((payload_json -> 'latest_proposal_status' = 'null'::jsonb and latest_proposal_status is null) or (jsonb_typeof(payload_json -> 'latest_proposal_status') = 'string' and payload_json ->> 'latest_proposal_status' = latest_proposal_status)))",
        "check (payload_json ? 'latest_allocated_count' and ((payload_json -> 'latest_allocated_count' = 'null'::jsonb and latest_allocated_count is null) or (jsonb_typeof(payload_json -> 'latest_allocated_count') = 'number' and (payload_json ->> 'latest_allocated_count')::integer = latest_allocated_count)))",
        "check (payload_json ? 'latest_total_allocated_paper_notional' and ((payload_json -> 'latest_total_allocated_paper_notional' = 'null'::jsonb and latest_total_allocated_paper_notional is null) or (jsonb_typeof(payload_json -> 'latest_total_allocated_paper_notional') = 'string' and (payload_json ->> 'latest_total_allocated_paper_notional')::numeric = latest_total_allocated_paper_notional)))",
        "check (payload_json ? 'max_source_age_seconds' and ((payload_json -> 'max_source_age_seconds' = 'null'::jsonb and max_source_age_seconds is null) or (jsonb_typeof(payload_json -> 'max_source_age_seconds') = 'number' and (payload_json ->> 'max_source_age_seconds')::integer = max_source_age_seconds)))",
        "check (payload_json ? 'latest_source_age_seconds' and ((payload_json -> 'latest_source_age_seconds' = 'null'::jsonb and latest_source_age_seconds is null) or (jsonb_typeof(payload_json -> 'latest_source_age_seconds') = 'number' and (payload_json ->> 'latest_source_age_seconds')::integer = latest_source_age_seconds)))",
        "check (payload_json ? 'duplicate_latest_report_generated_at_count' and jsonb_typeof(payload_json -> 'duplicate_latest_report_generated_at_count') = 'number' and (payload_json ->> 'duplicate_latest_report_generated_at_count')::integer = duplicate_latest_report_generated_at_count)",
        "check (payload_json ? 'reason_code_counts' and jsonb_typeof(payload_json -> 'reason_code_counts') = 'array' and payload_json -> 'reason_code_counts' = reason_code_counts_json)",
        "check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and payload_json -> 'reason_codes' = reason_codes_json)",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)",
    )
    for check in expected_checks:
        assert compact_expression(check) in expression_body


def test_migration_uses_numeric_for_decimal_scalars_and_jsonb_for_payloads() -> None:
    body = table_body(migration_sql())

    assert "latest_total_allocated_paper_notional numeric(38, 6)" in body
    assert "reason_code_counts_json jsonb" in body
    assert "reason_codes_json jsonb" in body
    assert "payload_json jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes() -> None:
    sql = compact(migration_sql())

    expected_indexes = (
        f"create index if not exists idx_paapdhhr_generated_at on public.{TABLE_NAME} (generated_at desc);",
        f"create index if not exists idx_paapdhhr_config_generated on public.{TABLE_NAME} (config_version, generated_at desc);",
        f"create index if not exists idx_paapdhhr_health_status_generated on public.{TABLE_NAME} (health_status, generated_at desc);",
        f"create index if not exists idx_paapdhhr_latest_history_status_generated on public.{TABLE_NAME} (latest_history_status, generated_at desc);",
        f"create index if not exists idx_paapdhhr_reason_code_counts_json on public.{TABLE_NAME} using gin (reason_code_counts_json jsonb_path_ops);",
        f"create index if not exists idx_paapdhhr_reason_codes_json on public.{TABLE_NAME} using gin (reason_codes_json jsonb_path_ops);",
        f"create index if not exists idx_paapdhhr_payload_json on public.{TABLE_NAME} using gin (payload_json jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_keeps_table_and_index_names_under_postgres_limit() -> None:
    sql = migration_sql()
    names = set(
        re.findall(
            r"create\s+table\s+if\s+not\s+exists\s+public\.([a-z0-9_]+)",
            sql,
            flags=re.IGNORECASE,
        ),
    )
    names.update(
        re.findall(
            r"create\s+(?:unique\s+)?index\s+if\s+not\s+exists\s+([a-z0-9_]+)",
            sql,
            flags=re.IGNORECASE,
        ),
    )

    assert TABLE_NAME in names
    assert names
    assert all(len(name) <= 63 for name in names)


def test_migration_does_not_include_live_trading_or_account_terms() -> None:
    sql = migration_sql().lower()

    forbidden_patterns = (
        r"\blive_trading\b",
        r"\bprivate[_ -]?key\b",
        r"\bwallet\b",
        r"\baccount\b",
        r"\border\b",
        r"\btrade\b",
        r"\bexecute\b",
        r"\bsubmit\b",
        r"\bapprove\b",
        r"\bcancel\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

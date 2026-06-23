from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260623000001_paper_research_packet_operator_flow_reports.sql"
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


def raw_table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_research_packet_operator_flow_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_research_packet_operator_flow_reports"
    return match.group(1)


def table_body(sql: str) -> str:
    return compact(raw_table_body(sql))


def table_column_names(sql: str) -> tuple[str, ...]:
    return tuple(
        match.group(1)
        for match in re.finditer(
            r"^\s{2}([a-z][a-z0-9_]*)\s+(?:text|timestamptz|boolean|integer|jsonb)\b",
            raw_table_body(sql),
            flags=re.MULTILINE,
        )
    )


def test_migration_creates_operator_flow_report_table_with_required_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "flow_status text not null",
        "packet_generated_at timestamptz not null",
        "packet_config_version text not null",
        "packet_persisted boolean not null",
        "packet_row_count integer not null",
        "included_count integer not null",
        "skipped_count integer not null",
        "quality_generated_at timestamptz not null",
        "quality_config_version text not null",
        "quality_status text not null",
        "quality_persisted boolean not null",
        "quality_check_count integer not null",
        "quality_pass_count integer not null",
        "quality_watch_count integer not null",
        "quality_blocked_count integer not null",
        "history_generated_at timestamptz not null",
        "history_config_version text not null",
        "history_status text not null",
        "history_source_report_count integer not null",
        "history_latest_quality_status text not null",
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
    assert table_column_names(migration_sql()) == tuple(
        column.split(" ", maxsplit=1)[0] for column in required_columns
    )


def test_migration_enforces_operator_flow_invariants_with_checks() -> None:
    expression_body = compact_expression(table_body(migration_sql()))

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (flow_status in ('pass', 'watch', 'blocked'))",
        "check (quality_status in ('pass', 'watch', 'blocked'))",
        "check (history_status in ('pass', 'watch', 'blocked'))",
        "check (history_latest_quality_status in ('pass', 'watch', 'blocked'))",
        "check (packet_row_count >= 0)",
        "check (included_count >= 0)",
        "check (skipped_count >= 0)",
        "check (quality_check_count >= 0)",
        "check (quality_pass_count >= 0)",
        "check (quality_watch_count >= 0)",
        "check (quality_blocked_count >= 0)",
        "check (history_source_report_count >= 0)",
        "check (history_source_report_count > 0)",
        "check (reason_code_count >= 0)",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
        "check (reason_code_count = jsonb_array_length(reason_codes_json))",
        "check (((payload_json -> 'reason_codes') = reason_codes_json) is true)",
        "check (packet_generated_at <= quality_generated_at)",
        "check (quality_generated_at <= history_generated_at)",
        "check (history_generated_at <= generated_at)",
        (
            "check (quality_check_count = quality_pass_count + "
            "quality_watch_count + quality_blocked_count)"
        ),
        "check (history_latest_quality_status = quality_status)",
        "check (((payload_json -> 'paper_only') = 'true'::jsonb) is true)",
        "check (((payload_json -> 'report_only') = 'true'::jsonb) is true)",
        "check (((payload_json -> 'readonly') = 'true'::jsonb) is true)",
    )
    for check in expected_checks:
        assert compact_expression(check) in expression_body


def test_migration_enforces_quality_status_precedence() -> None:
    expression_body = compact_expression(table_body(migration_sql()))

    expected_check = (
        "check ("
        "(quality_status = 'blocked' and quality_blocked_count > 0) "
        "or (quality_status = 'watch' and quality_blocked_count = 0 and "
        "quality_watch_count > 0) "
        "or (quality_status = 'pass' and quality_blocked_count = 0 and "
        "quality_watch_count = 0))"
    )

    assert compact_expression(expected_check) in expression_body


def test_migration_syncs_payload_values_to_promoted_columns() -> None:
    expression_body = compact_expression(table_body(migration_sql()))

    expected_checks = (
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
            "check (payload_json ? 'flow_status' and "
            "jsonb_typeof(payload_json -> 'flow_status') = 'string' and "
            "payload_json ->> 'flow_status' = flow_status)"
        ),
        (
            "check (payload_json ? 'packet_generated_at' and "
            "jsonb_typeof(payload_json -> 'packet_generated_at') = 'string' and "
            "(payload_json ->> 'packet_generated_at')::timestamptz = packet_generated_at)"
        ),
        (
            "check (payload_json ? 'packet_config_version' and "
            "jsonb_typeof(payload_json -> 'packet_config_version') = 'string' and "
            "payload_json ->> 'packet_config_version' = packet_config_version)"
        ),
        "check (((payload_json -> 'packet_persisted') = to_jsonb(packet_persisted)) is true)",
        "check (((payload_json -> 'packet_row_count') = to_jsonb(packet_row_count)) is true)",
        "check (((payload_json -> 'included_count') = to_jsonb(included_count)) is true)",
        "check (((payload_json -> 'skipped_count') = to_jsonb(skipped_count)) is true)",
        (
            "check (payload_json ? 'quality_generated_at' and "
            "jsonb_typeof(payload_json -> 'quality_generated_at') = 'string' and "
            "(payload_json ->> 'quality_generated_at')::timestamptz = quality_generated_at)"
        ),
        (
            "check (payload_json ? 'quality_config_version' and "
            "jsonb_typeof(payload_json -> 'quality_config_version') = 'string' and "
            "payload_json ->> 'quality_config_version' = quality_config_version)"
        ),
        (
            "check (payload_json ? 'quality_status' and "
            "jsonb_typeof(payload_json -> 'quality_status') = 'string' and "
            "payload_json ->> 'quality_status' = quality_status)"
        ),
        "check (((payload_json -> 'quality_persisted') = to_jsonb(quality_persisted)) is true)",
        (
            "check (((payload_json -> 'quality_check_count') = "
            "to_jsonb(quality_check_count)) is true)"
        ),
        "check (((payload_json -> 'quality_pass_count') = to_jsonb(quality_pass_count)) is true)",
        (
            "check (((payload_json -> 'quality_watch_count') = "
            "to_jsonb(quality_watch_count)) is true)"
        ),
        (
            "check (((payload_json -> 'quality_blocked_count') = "
            "to_jsonb(quality_blocked_count)) is true)"
        ),
        (
            "check (payload_json ? 'history_generated_at' and "
            "jsonb_typeof(payload_json -> 'history_generated_at') = 'string' and "
            "(payload_json ->> 'history_generated_at')::timestamptz = history_generated_at)"
        ),
        (
            "check (payload_json ? 'history_config_version' and "
            "jsonb_typeof(payload_json -> 'history_config_version') = 'string' and "
            "payload_json ->> 'history_config_version' = history_config_version)"
        ),
        (
            "check (payload_json ? 'history_status' and "
            "jsonb_typeof(payload_json -> 'history_status') = 'string' and "
            "payload_json ->> 'history_status' = history_status)"
        ),
        (
            "check (((payload_json -> 'history_source_report_count') = "
            "to_jsonb(history_source_report_count)) is true)"
        ),
        (
            "check (payload_json ? 'history_latest_quality_status' and "
            "jsonb_typeof(payload_json -> 'history_latest_quality_status') = 'string' and "
            "payload_json ->> 'history_latest_quality_status' = history_latest_quality_status)"
        ),
    )
    for check in expected_checks:
        assert compact_expression(check) in expression_body


def test_migration_enforces_flow_status_precedence() -> None:
    expression_body = compact_expression(table_body(migration_sql()))

    expected_check = (
        "check ("
        "(flow_status = 'blocked' and "
        "(packet_persisted is false or quality_persisted is false or "
        "quality_status = 'blocked' or history_status = 'blocked')) "
        "or (flow_status = 'watch' and packet_persisted is true and "
        "quality_persisted is true and quality_status <> 'blocked' and "
        "history_status <> 'blocked' and "
        "(quality_status = 'watch' or history_status = 'watch')) "
        "or (flow_status = 'pass' and packet_persisted is true and "
        "quality_persisted is true and quality_status = 'pass' and history_status = 'pass'))"
    )

    assert compact_expression(expected_check) in expression_body


def test_migration_uses_jsonb_without_float_types() -> None:
    body = table_body(migration_sql())

    assert "reason_codes_json jsonb" in body
    assert "payload_json jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes() -> None:
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_prpofr_generated_at on public.paper_research_packet_operator_flow_reports (generated_at desc);",
        "create index if not exists idx_prpofr_config_version_generated_at on public.paper_research_packet_operator_flow_reports (config_version, generated_at desc);",
        "create index if not exists idx_prpofr_flow_status_generated_at on public.paper_research_packet_operator_flow_reports (flow_status, generated_at desc);",
        "create index if not exists idx_prpofr_quality_status_generated_at on public.paper_research_packet_operator_flow_reports (quality_status, generated_at desc);",
        "create index if not exists idx_prpofr_history_status_generated_at on public.paper_research_packet_operator_flow_reports (history_status, generated_at desc);",
        "create index if not exists idx_prpofr_packet_generated_at on public.paper_research_packet_operator_flow_reports (packet_generated_at desc);",
        "create index if not exists idx_prpofr_quality_generated_at on public.paper_research_packet_operator_flow_reports (quality_generated_at desc);",
        "create index if not exists idx_prpofr_history_generated_at on public.paper_research_packet_operator_flow_reports (history_generated_at desc);",
        "create index if not exists idx_prpofr_reason_codes_json on public.paper_research_packet_operator_flow_reports using gin (reason_codes_json jsonb_path_ops);",
        "create index if not exists idx_prpofr_payload_json on public.paper_research_packet_operator_flow_reports using gin (payload_json jsonb_path_ops);",
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
        r"\baccount\b",
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

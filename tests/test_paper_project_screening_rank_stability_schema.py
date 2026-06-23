from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260622000007_paper_project_screening_rank_stability_reports.sql"
)
DEFAULT_TABLE = "paper_project_screening_rank_stability_reports"


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_project_screening_rank_stability_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_project_screening_rank_stability_reports"
    return compact(match.group(1))


def test_migration_creates_project_rank_stability_report_table() -> None:
    body = table_body(migration_sql())

    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "stability_status text not null",
        "reason_codes_json jsonb not null",
        "source_report_count integer not null",
        "candidate_count integer not null",
        "stable_count integer not null",
        "watch_count integer not null",
        "blocked_count integer not null",
        "stable_ready_count integer not null",
        "unstable_ready_count integer not null",
        "scoring_side_changed_count integer not null",
        "source_status_changed_count integer not null",
        "screening_status_changed_count integer not null",
        "research_bucket_changed_count integer not null",
        "latest_generated_at timestamptz null",
        "top_stable_market_slug text null",
        "rows_json jsonb not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body


def test_migration_enforces_core_report_invariants_and_hard_flags() -> None:
    body = table_body(migration_sql())

    for expected_check in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (stability_status in ('stable', 'watch', 'blocked'))",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (source_report_count >= 0)",
        "check (candidate_count >= 0)",
        "check (stable_count >= 0)",
        "check (watch_count >= 0)",
        "check (blocked_count >= 0)",
        "check (stable_ready_count >= 0)",
        "check (unstable_ready_count >= 0)",
        "check (scoring_side_changed_count >= 0)",
        "check (source_status_changed_count >= 0)",
        "check (screening_status_changed_count >= 0)",
        "check (research_bucket_changed_count >= 0)",
        "check (stable_count + watch_count + blocked_count = candidate_count)",
        "check (stable_ready_count <= stable_count)",
        "check (unstable_ready_count <= watch_count + blocked_count)",
        "check (stable_ready_count + unstable_ready_count <= candidate_count)",
        "check (scoring_side_changed_count <= candidate_count)",
        "check (source_status_changed_count <= candidate_count)",
        "check (screening_status_changed_count <= candidate_count)",
        "check (research_bucket_changed_count <= candidate_count)",
        "check (jsonb_typeof(rows_json) = 'array')",
        "check (jsonb_array_length(rows_json) = candidate_count)",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body


def test_migration_enforces_payload_scalar_parity() -> None:
    body = table_body(migration_sql())

    for expected_check in (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (payload_json ? 'stability_status' and jsonb_typeof(payload_json -> 'stability_status') = 'string' and payload_json ->> 'stability_status' = stability_status)",
        "check (payload_json ? 'source_report_count' and jsonb_typeof(payload_json -> 'source_report_count') = 'number' and (payload_json ->> 'source_report_count')::integer = source_report_count)",
        "check (payload_json ? 'candidate_count' and jsonb_typeof(payload_json -> 'candidate_count') = 'number' and (payload_json ->> 'candidate_count')::integer = candidate_count)",
        "check (payload_json ? 'stable_count' and jsonb_typeof(payload_json -> 'stable_count') = 'number' and (payload_json ->> 'stable_count')::integer = stable_count)",
        "check (payload_json ? 'watch_count' and jsonb_typeof(payload_json -> 'watch_count') = 'number' and (payload_json ->> 'watch_count')::integer = watch_count)",
        "check (payload_json ? 'blocked_count' and jsonb_typeof(payload_json -> 'blocked_count') = 'number' and (payload_json ->> 'blocked_count')::integer = blocked_count)",
        "check (payload_json ? 'stable_ready_count' and jsonb_typeof(payload_json -> 'stable_ready_count') = 'number' and (payload_json ->> 'stable_ready_count')::integer = stable_ready_count)",
        "check (payload_json ? 'unstable_ready_count' and jsonb_typeof(payload_json -> 'unstable_ready_count') = 'number' and (payload_json ->> 'unstable_ready_count')::integer = unstable_ready_count)",
        "check (payload_json ? 'scoring_side_changed_count' and jsonb_typeof(payload_json -> 'scoring_side_changed_count') = 'number' and (payload_json ->> 'scoring_side_changed_count')::integer = scoring_side_changed_count)",
        "check (payload_json ? 'source_status_changed_count' and jsonb_typeof(payload_json -> 'source_status_changed_count') = 'number' and (payload_json ->> 'source_status_changed_count')::integer = source_status_changed_count)",
        "check (payload_json ? 'screening_status_changed_count' and jsonb_typeof(payload_json -> 'screening_status_changed_count') = 'number' and (payload_json ->> 'screening_status_changed_count')::integer = screening_status_changed_count)",
        "check (payload_json ? 'research_bucket_changed_count' and jsonb_typeof(payload_json -> 'research_bucket_changed_count') = 'number' and (payload_json ->> 'research_bucket_changed_count')::integer = research_bucket_changed_count)",
        "check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and payload_json -> 'reason_codes' = reason_codes_json)",
        "check (payload_json ? 'rows' and jsonb_typeof(payload_json -> 'rows') = 'array' and payload_json -> 'rows' = rows_json)",
    ):
        assert expected_check in body


def test_migration_enforces_empty_candidate_state_and_source_timestamp_rules() -> None:
    body = table_body(migration_sql())

    assert (
        "check (candidate_count > 0 or (stability_status = 'watch' and stable_count = 0 "
        "and watch_count = 0 and blocked_count = 0 and stable_ready_count = 0 "
        "and unstable_ready_count = 0 and scoring_side_changed_count = 0 "
        "and source_status_changed_count = 0 and screening_status_changed_count = 0 "
        "and research_bucket_changed_count = 0 and top_stable_market_slug is null "
        "and jsonb_array_length(rows_json) = 0 and reason_codes_json = '[\"no_latest_candidates\"]'::jsonb))"
    ) in body
    assert (
        "check (source_report_count > 0 or (candidate_count = 0 and latest_generated_at is null))"
    ) in body


def test_migration_uses_jsonb_for_payloads_and_no_float_columns() -> None:
    body = table_body(migration_sql())

    assert "rows_json jsonb" in body
    assert "payload_json jsonb" in body
    assert "reason_codes_json jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes() -> None:
    sql = compact(migration_sql())

    for index in (
        "create index if not exists idx_ppssr_generated_at on "
        "public.paper_project_screening_rank_stability_reports (generated_at desc);",
        "create index if not exists idx_ppssr_status_generated on "
        "public.paper_project_screening_rank_stability_reports (stability_status, generated_at desc);",
        "create index if not exists idx_ppssr_config_generated on "
        "public.paper_project_screening_rank_stability_reports (config_version, generated_at desc);",
        "create index if not exists idx_ppssr_reason_codes_json on "
        "public.paper_project_screening_rank_stability_reports using gin (reason_codes_json);",
        "create index if not exists idx_ppssr_rows_json on "
        "public.paper_project_screening_rank_stability_reports using gin (rows_json);",
        "create index if not exists idx_ppssr_payload_json on "
        "public.paper_project_screening_rank_stability_reports using gin (payload_json);",
    ):
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

    assert DEFAULT_TABLE in names
    assert names
    assert all(len(name) <= 63 for name in names)


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

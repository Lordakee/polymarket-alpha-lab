from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
EXPECTED_MIGRATION_NAME = (
    "20260630000102_probability_selection_scorer_agreement_trend_gate_reports.sql"
)
DEFAULT_TABLE = "probability_selection_scorer_agreement_trend_gate_reports"


def _migration_path() -> Path:
    candidates = sorted(
        MIGRATIONS_DIR.glob(
            "*probability_selection_scorer_agreement_trend_gate_reports.sql",
        ),
    )
    assert candidates, "probability selection scorer agreement trend-gate migration is missing"
    assert len(candidates) == 1
    return candidates[0]


def _migration_text() -> str:
    return _migration_path().read_text(encoding="utf-8").lower()


def _compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def _without_space_after_open_paren(sql: str) -> str:
    sql = re.sub(r"\(\s+", "(", sql)
    return re.sub(r"\s+\)", ")", sql)


def _table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.probability_selection_scorer_agreement_trend_gate_reports"
        r"\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{DEFAULT_TABLE}"
    return _compact(match.group(1))


def _compact_index_sql(sql: str) -> str:
    return _without_space_after_open_paren(_compact(sql))


def test_trend_gate_migration_uses_requested_free_version() -> None:
    path = _migration_path()
    versions = [
        migration_path.name.split("_", 1)[0]
        for migration_path in MIGRATIONS_DIR.glob("*.sql")
    ]

    assert path.name == EXPECTED_MIGRATION_NAME
    assert Counter(versions)[EXPECTED_MIGRATION_NAME.split("_", 1)[0]] == 1


def test_trend_gate_migration_creates_report_table_with_contract_columns() -> None:
    body = _table_body(_migration_text())

    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "source_config_version text not null",
        "source_generated_at timestamptz not null",
        "trend_report_age_seconds integer not null",
        "gate_status text not null",
        "recommended_next_step text not null",
        "reason_code_counts jsonb not null",
        "source_report_count integer not null",
        "source_trend_status text not null",
        "source_recommended_next_step text not null",
        "latest_agreement_status text not null",
        "latest_agreement_status_streak integer not null",
        "aligned_report_count integer not null",
        "low_overlap_report_count integer not null",
        "gate_blocked_report_count integer not null",
        "missing_inputs_report_count integer not null",
        "insufficient_identifiers_report_count integer not null",
        "average_selected_count numeric not null",
        "average_scorer_candidate_count numeric not null",
        "latest_source_reason_codes jsonb not null",
        "recurring_source_reason_code_counts jsonb not null",
        "reason_codes jsonb not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body


def test_trend_gate_migration_constrains_status_json_counts_and_flags() -> None:
    body = _without_space_after_open_paren(_table_body(_migration_text()))

    for expected_check in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (gate_status in ('pass', 'watch', 'blocked'))",
        "check (source_trend_status in ('insufficient_history', 'blocked', 'watch', 'stable'))",
        "check (latest_agreement_status in ('aligned', 'gate_blocked', 'insufficient_identifiers', 'low_overlap', 'missing_inputs'))",
        "check (jsonb_typeof(reason_code_counts) = 'array')",
        "check (jsonb_typeof(latest_source_reason_codes) = 'array')",
        "check (jsonb_typeof(recurring_source_reason_code_counts) = 'array')",
        "check (jsonb_typeof(reason_codes) = 'array')",
        "check (jsonb_typeof(payload) = 'object')",
        "check (jsonb_array_length(reason_code_counts) >= 1)",
        "check (jsonb_array_length(reason_codes) >= 1)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
        "check (payload ? 'paper_only' and payload -> 'paper_only' = 'true'::jsonb)",
        "check (payload ? 'report_only' and payload -> 'report_only' = 'true'::jsonb)",
        "check (payload ? 'readonly' and payload -> 'readonly' = 'true'::jsonb)",
    ):
        assert expected_check in body

    for column in (
        "trend_report_age_seconds",
        "source_report_count",
        "latest_agreement_status_streak",
        "aligned_report_count",
        "low_overlap_report_count",
        "gate_blocked_report_count",
        "missing_inputs_report_count",
        "insufficient_identifiers_report_count",
        "average_selected_count",
        "average_scorer_candidate_count",
    ):
        assert f"check ({column} >= 0)" in body


def test_trend_gate_migration_enforces_payload_materialized_consistency() -> None:
    body = _table_body(_migration_text())

    for expected_check in (
        "check (payload ? 'generated_at' and jsonb_typeof(payload -> 'generated_at') = 'string' and (payload ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload ? 'config_version' and jsonb_typeof(payload -> 'config_version') = 'string' and payload ->> 'config_version' = config_version)",
        "check (payload ? 'source_config_version' and jsonb_typeof(payload -> 'source_config_version') = 'string' and payload ->> 'source_config_version' = source_config_version)",
        "check (payload ? 'source_generated_at' and jsonb_typeof(payload -> 'source_generated_at') = 'string' and (payload ->> 'source_generated_at')::timestamptz = source_generated_at)",
        "check (payload ? 'trend_report_age_seconds' and (payload ->> 'trend_report_age_seconds')::integer = trend_report_age_seconds)",
        "check (payload ? 'trend_report_age_seconds' and payload -> 'trend_report_age_seconds' = to_jsonb(trend_report_age_seconds))",
        "check (payload ? 'gate_status' and jsonb_typeof(payload -> 'gate_status') = 'string' and payload ->> 'gate_status' = gate_status)",
        "check (payload ? 'recommended_next_step' and jsonb_typeof(payload -> 'recommended_next_step') = 'string' and payload ->> 'recommended_next_step' = recommended_next_step)",
        "check (payload ? 'reason_code_counts' and jsonb_typeof(payload -> 'reason_code_counts') = 'array' and reason_code_counts = payload -> 'reason_code_counts')",
        "check (payload ? 'latest_source_reason_codes' and jsonb_typeof(payload -> 'latest_source_reason_codes') = 'array' and latest_source_reason_codes = payload -> 'latest_source_reason_codes')",
        "check (payload ? 'recurring_source_reason_code_counts' and jsonb_typeof(payload -> 'recurring_source_reason_code_counts') = 'array' and recurring_source_reason_code_counts = payload -> 'recurring_source_reason_code_counts')",
        "check (payload ? 'reason_codes' and jsonb_typeof(payload -> 'reason_codes') = 'array' and reason_codes = payload -> 'reason_codes')",
        "check (payload ? 'average_selected_count' and jsonb_typeof(payload -> 'average_selected_count') = 'string' and (payload ->> 'average_selected_count')::numeric = average_selected_count)",
        "check (payload ? 'average_scorer_candidate_count' and jsonb_typeof(payload -> 'average_scorer_candidate_count') = 'string' and (payload ->> 'average_scorer_candidate_count')::numeric = average_scorer_candidate_count)",
        "check (payload ? 'source_report_count' and payload -> 'source_report_count' = to_jsonb(source_report_count))",
        "check (payload ? 'source_trend_status' and jsonb_typeof(payload -> 'source_trend_status') = 'string' and payload ->> 'source_trend_status' = source_trend_status)",
        "check (payload ? 'source_recommended_next_step' and jsonb_typeof(payload -> 'source_recommended_next_step') = 'string' and payload ->> 'source_recommended_next_step' = source_recommended_next_step)",
        "check (payload ? 'latest_agreement_status' and jsonb_typeof(payload -> 'latest_agreement_status') = 'string' and payload ->> 'latest_agreement_status' = latest_agreement_status)",
        "check (payload ? 'latest_agreement_status_streak' and payload -> 'latest_agreement_status_streak' = to_jsonb(latest_agreement_status_streak))",
        "check (payload ? 'aligned_report_count' and payload -> 'aligned_report_count' = to_jsonb(aligned_report_count))",
        "check (payload ? 'low_overlap_report_count' and payload -> 'low_overlap_report_count' = to_jsonb(low_overlap_report_count))",
        "check (payload ? 'gate_blocked_report_count' and payload -> 'gate_blocked_report_count' = to_jsonb(gate_blocked_report_count))",
        "check (payload ? 'missing_inputs_report_count' and payload -> 'missing_inputs_report_count' = to_jsonb(missing_inputs_report_count))",
        "check (payload ? 'insufficient_identifiers_report_count' and payload -> 'insufficient_identifiers_report_count' = to_jsonb(insufficient_identifiers_report_count))",
        "check (payload ->> 'average_selected_count' ~ '^(0|[1-9][0-9]*)[.][0-9]{6}$')",
        "check (payload ->> 'average_scorer_candidate_count' ~ '^(0|[1-9][0-9]*)[.][0-9]{6}$')",
    ):
        assert expected_check in body


def test_trend_gate_migration_enforces_reason_code_count_hard_flags() -> None:
    body = _without_space_after_open_paren(_table_body(_migration_text()))

    for expected_check in (
        "check (not jsonb_path_exists(reason_code_counts, '$[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'))",
        "check (jsonb_array_length(jsonb_path_query_array(reason_code_counts, '$[*] ? (@.paper_only == true)')) = jsonb_array_length(reason_code_counts))",
        "check (jsonb_array_length(jsonb_path_query_array(reason_code_counts, '$[*] ? (@.report_only == true)')) = jsonb_array_length(reason_code_counts))",
        "check (jsonb_array_length(jsonb_path_query_array(reason_code_counts, '$[*] ? (@.readonly == true)')) = jsonb_array_length(reason_code_counts))",
        "check (not jsonb_path_exists(payload, '$.reason_code_counts[*] ? (@.paper_only != true || @.report_only != true || @.readonly != true)'))",
        "check (jsonb_array_length(jsonb_path_query_array(payload, '$.reason_code_counts[*] ? (@.paper_only == true)')) = jsonb_array_length(payload -> 'reason_code_counts'))",
        "check (jsonb_array_length(jsonb_path_query_array(payload, '$.reason_code_counts[*] ? (@.report_only == true)')) = jsonb_array_length(payload -> 'reason_code_counts'))",
        "check (jsonb_array_length(jsonb_path_query_array(payload, '$.reason_code_counts[*] ? (@.readonly == true)')) = jsonb_array_length(payload -> 'reason_code_counts'))",
    ):
        assert expected_check in body


def test_trend_gate_migration_indexes_load_order_and_json_payloads() -> None:
    sql = _compact_index_sql(_migration_text())

    for expected_index in (
        "create index if not exists pssatgr_generated_order_idx on public.probability_selection_scorer_agreement_trend_gate_reports (generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists pssatgr_config_order_idx on public.probability_selection_scorer_agreement_trend_gate_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists pssatgr_gate_order_idx on public.probability_selection_scorer_agreement_trend_gate_reports (gate_status, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists pssatgr_source_trend_order_idx on public.probability_selection_scorer_agreement_trend_gate_reports (source_trend_status, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists pssatgr_reason_codes_idx on public.probability_selection_scorer_agreement_trend_gate_reports using gin (reason_codes jsonb_path_ops);",
        "create index if not exists pssatgr_payload_idx on public.probability_selection_scorer_agreement_trend_gate_reports using gin (payload jsonb_path_ops);",
    ):
        assert expected_index in sql


def test_trend_gate_migration_has_no_market_or_live_trading_columns() -> None:
    text = _migration_text()

    for column_name in (
        "auth",
        "cancel_order",
        "condition_id",
        "market_slug",
        "order",
        "private_key",
        "question",
        "submit_order",
        "trade",
        "wallet",
    ):
        assert re.search(rf"^\s*{re.escape(column_name)}\s+", text, re.MULTILINE) is None


def test_trend_gate_migration_rejects_sensitive_payload_keys() -> None:
    text = _migration_text()

    assert "check (not (payload ?| array[" in text
    for key in (
        "account",
        "auth",
        "condition_id",
        "market_slug",
        "order",
        "private_key",
        "question",
        "wallet",
    ):
        assert f"'{key}'" in text

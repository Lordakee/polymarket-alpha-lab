from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
EXPECTED_MIGRATION_NAME = (
    "20260625000005_paper_autonomous_investment_ledger_reports.sql"
)
PREVIOUS_MIGRATION_NAME = "20260625000004_paper_broker_execution_records.sql"
DEFAULT_TABLE = "paper_autonomous_investment_ledger_reports"


def _migration_path() -> Path:
    candidates = sorted(
        MIGRATIONS_DIR.glob("*paper_autonomous_investment_ledger_reports.sql"),
    )
    assert candidates, "paper autonomous investment ledger migration is missing"
    assert len(candidates) == 1
    return candidates[0]


def _migration_text() -> str:
    return _migration_path().read_text(encoding="utf-8").lower()


def _compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def _without_space_after_open_paren(sql: str) -> str:
    return re.sub(r"\(\s+", "(", sql)


def _table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_autonomous_investment_ledger_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{DEFAULT_TABLE}"
    return _compact(match.group(1))


def test_ledger_migration_uses_next_safe_version_and_unique_order() -> None:
    path = _migration_path()
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))
    names = [migration_path.name for migration_path in migration_paths]
    versions = [name.split("_", 1)[0] for name in names]

    assert path.name == EXPECTED_MIGRATION_NAME
    assert PREVIOUS_MIGRATION_NAME in names
    assert names[names.index(PREVIOUS_MIGRATION_NAME) + 1] == EXPECTED_MIGRATION_NAME
    assert Counter(versions)[EXPECTED_MIGRATION_NAME.split("_", 1)[0]] == 1


def test_ledger_migration_creates_report_table_matching_report_scalars() -> None:
    body = _table_body(_migration_text())

    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "ledger_status text not null",
        "recommended_next_step text not null",
        "source_record_count integer not null",
        "submitted_count integer not null",
        "held_count integer not null",
        "blocked_count integer not null",
        "total_submitted_notional numeric(38, 6) not null",
        "held_zero_notional_count integer not null",
        "blocked_zero_notional_count integer not null",
        "latest_generated_at timestamptz",
        "latest_age_seconds integer",
        "reason_code_counts jsonb not null",
        "entries jsonb not null",
        "reason_codes jsonb not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body


def test_ledger_migration_constrains_statuses_json_flags_and_scalars() -> None:
    body = _table_body(_migration_text())

    assert "check (report_sha256 ~ '^[a-f0-9]{64}$')" in body
    assert "check (ledger_status in ('pass', 'watch', 'blocked'))" in body
    assert "check (source_record_count >= 0)" in body
    assert "check (submitted_count >= 0)" in body
    assert "check (held_count >= 0)" in body
    assert "check (blocked_count >= 0)" in body
    assert "check (total_submitted_notional >= 0)" in body
    assert "check (held_zero_notional_count >= 0)" in body
    assert "check (blocked_zero_notional_count >= 0)" in body
    assert "check (latest_age_seconds is null or latest_age_seconds >= 0)" in body
    assert "check (jsonb_typeof(reason_code_counts) = 'array')" in body
    assert "check (jsonb_typeof(entries) = 'array')" in body
    assert "check (jsonb_typeof(reason_codes) = 'array')" in body
    assert "check (jsonb_typeof(payload) = 'object')" in body
    assert "check (paper_only is true)" in body
    assert "check (report_only is true)" in body
    assert "check (readonly is true)" in body
    assert (
        "check (payload ? 'paper_only' and payload -> 'paper_only' = 'true'::jsonb)"
        in body
    )
    assert (
        "check (payload ? 'report_only' and payload -> 'report_only' = 'true'::jsonb)"
        in body
    )
    assert (
        "check (payload ? 'readonly' and payload -> 'readonly' = 'true'::jsonb)"
        in body
    )


def test_ledger_migration_constrains_next_step_and_report_consistency() -> None:
    body = _without_space_after_open_paren(_table_body(_migration_text()))
    text = _compact(_migration_text())

    assert (
        "recommended_next_step = case ledger_status when 'pass' then "
        "'archive_paper_autonomous_investment_ledger' when 'watch' then "
        "'review_paper_autonomous_investment_ledger' when 'blocked' then "
        "'block_paper_autonomous_investment_ledger' end"
    ) in body
    assert "source_record_count = submitted_count + held_count + blocked_count" in body
    assert "held_zero_notional_count = held_count" in body
    assert "blocked_zero_notional_count = blocked_count" in body
    for status_column, execution_status in (
        ("submitted_count", "paper_submitted"),
        ("held_count", "paper_held"),
        ("blocked_count", "paper_blocked"),
    ):
        assert status_column in body
        assert (
            f"@.execution_status == \"{execution_status}\""
        ) in body
    assert "jsonb_array_length(entries) = source_record_count" in body
    assert (
        "(source_record_count = 0 and reason_codes @> "
        "'[\"paper_autonomous_investment_ledger_no_source_records\"]'::jsonb)"
    ) in body
    assert "blocked_count = 0" in body
    assert (
        "'[\"paper_autonomous_investment_ledger_blocked_records_present\"]'::jsonb"
        in body
    )
    assert "held_count = 0" in body
    assert (
        "'[\"paper_autonomous_investment_ledger_held_records_present\"]'::jsonb"
        in body
    )
    assert "'[\"paper_autonomous_investment_ledger_passed\"]'::jsonb" in body
    assert "source_record_count > 0 and held_count = 0 and blocked_count = 0" in body
    assert "create or replace function public.pailr_entries_consistent" in text
    assert "returns boolean language sql immutable" in text
    assert "public.pailr_entries_consistent(" in text
    for argument in (
        "entries",
        "reason_code_counts",
        "total_submitted_notional",
        "latest_generated_at",
        "latest_age_seconds",
        "generated_at",
    ):
        assert argument in text
    assert "source_record_count = 0" in body
    assert "latest_generated_at is null" in body
    assert "latest_age_seconds is null" in body
    assert "jsonb_array_length(reason_code_counts) = 0" in body
    assert "source_record_count > 0" in body
    assert "latest_generated_at is not null" in body
    assert "latest_age_seconds is not null" in body


def test_ledger_migration_enforces_payload_shape_and_nested_hard_flags() -> None:
    body = _without_space_after_open_paren(_table_body(_migration_text()))

    for expected_check in (
        "check (payload ? 'generated_at' and jsonb_typeof(payload -> 'generated_at') = 'string' and (payload ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload ? 'config_version' and jsonb_typeof(payload -> 'config_version') = 'string' and payload ->> 'config_version' = config_version)",
        "check (payload ? 'ledger_status' and jsonb_typeof(payload -> 'ledger_status') = 'string' and payload ->> 'ledger_status' = ledger_status)",
        "check (payload ? 'recommended_next_step' and jsonb_typeof(payload -> 'recommended_next_step') = 'string' and payload ->> 'recommended_next_step' = recommended_next_step)",
        "check (payload ? 'source_record_count' and payload -> 'source_record_count' = to_jsonb(source_record_count))",
        "check (payload ? 'submitted_count' and payload -> 'submitted_count' = to_jsonb(submitted_count))",
        "check (payload ? 'held_count' and payload -> 'held_count' = to_jsonb(held_count))",
        "check (payload ? 'blocked_count' and payload -> 'blocked_count' = to_jsonb(blocked_count))",
        "check (payload ? 'total_submitted_notional' and jsonb_typeof(payload -> 'total_submitted_notional') = 'string' and (payload ->> 'total_submitted_notional')::numeric(38, 6) = total_submitted_notional)",
        "check (payload ? 'held_zero_notional_count' and payload -> 'held_zero_notional_count' = to_jsonb(held_zero_notional_count))",
        "check (payload ? 'blocked_zero_notional_count' and payload -> 'blocked_zero_notional_count' = to_jsonb(blocked_zero_notional_count))",
        "check (payload ? 'reason_code_counts' and jsonb_typeof(payload -> 'reason_code_counts') = 'array' and payload -> 'reason_code_counts' = reason_code_counts)",
        "check (payload ? 'entries' and jsonb_typeof(payload -> 'entries') = 'array' and payload -> 'entries' = entries)",
        "check (payload ? 'reason_codes' and jsonb_typeof(payload -> 'reason_codes') = 'array' and payload -> 'reason_codes' = reason_codes)",
    ):
        assert expected_check in body
    assert "latest_generated_at is null and payload ? 'latest_generated_at'" in body
    assert "payload -> 'latest_generated_at' = 'null'::jsonb" in body
    assert "(payload ->> 'latest_generated_at')::timestamptz = latest_generated_at" in body
    assert "latest_age_seconds is null and payload ? 'latest_age_seconds'" in body
    assert "payload -> 'latest_age_seconds' = 'null'::jsonb" in body
    assert "payload -> 'latest_age_seconds' = to_jsonb(latest_age_seconds)" in body

    assert "not jsonb_path_exists(entries" in body
    assert "not jsonb_path_exists(reason_code_counts" in body
    assert "@.paper_only != true || @.report_only != true || @.readonly != true" in body
    for array_name in ("entries", "reason_code_counts"):
        for flag_name in ("paper_only", "report_only", "readonly"):
            assert (
                f"jsonb_array_length(jsonb_path_query_array({array_name}, "
                f"'$[*] ? (@.{flag_name} == true)')) = jsonb_array_length({array_name})"
            ) in body
    for array_path in ("$.entries", "$.reason_code_counts"):
        for flag_name in ("paper_only", "report_only", "readonly"):
            assert (
                "jsonb_array_length(jsonb_path_query_array(payload, "
                f"'{array_path}[*] ? (@.{flag_name} == true)')) = "
                f"jsonb_array_length(payload -> '{array_path.split('.')[1]}')"
            ) in body
    assert "not jsonb_path_exists(payload" in body
    assert "$.entries[*]" in body
    assert "$.reason_code_counts[*]" in body


def test_ledger_migration_uses_numeric_for_decimals_and_jsonb_for_payloads() -> None:
    body = _table_body(_migration_text())

    assert "total_submitted_notional numeric(38, 6)" in body
    assert "reason_code_counts jsonb" in body
    assert "entries jsonb" in body
    assert "reason_codes jsonb" in body
    assert "payload jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_ledger_migration_indexes_load_order_and_filter_paths() -> None:
    text = _compact(_migration_text())

    assert (
        "on public.paper_autonomous_investment_ledger_reports "
        "(generated_at desc, inserted_at desc, report_sha256 desc)"
    ) in text
    assert (
        "config_version, generated_at desc, inserted_at desc, report_sha256 desc"
    ) in text
    assert (
        "ledger_status, generated_at desc, inserted_at desc, report_sha256 desc"
    ) in text
    assert (
        "latest_generated_at desc, generated_at desc, inserted_at desc, "
        "report_sha256 desc"
    ) in text
    assert "using gin (reason_code_counts jsonb_path_ops)" in text
    assert "using gin (entries jsonb_path_ops)" in text
    assert "using gin (reason_codes jsonb_path_ops)" in text
    assert "using gin (payload jsonb_path_ops)" in text


def test_ledger_migration_keeps_table_and_index_names_under_postgres_limit() -> None:
    text = _migration_text()
    names = set(
        re.findall(
            r"create\s+table\s+if\s+not\s+exists\s+public\.([a-z0-9_]+)",
            text,
            flags=re.IGNORECASE,
        ),
    )
    names.update(
        re.findall(
            r"create\s+(?:unique\s+)?index\s+if\s+not\s+exists\s+([a-z0-9_]+)",
            text,
            flags=re.IGNORECASE,
        ),
    )

    assert DEFAULT_TABLE in names
    assert names
    assert all(len(name) <= 63 for name in names)


def test_ledger_migration_stays_paper_only_without_live_surfaces() -> None:
    text = _migration_text()

    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
        r"\bsign(?:s|ed|ing|ature)?\b",
        r"\bcancel(?:s|ed|ing|lation)?\b",
        r"\bplace(?:s|d|ment|ing)?\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, text), pattern

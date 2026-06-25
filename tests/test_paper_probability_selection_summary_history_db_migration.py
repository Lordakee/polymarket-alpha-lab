from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
EXPECTED_MIGRATION_NAME = (
    "20260625000006_probability_selection_summary_history_reports.sql"
)
PREVIOUS_MIGRATION_NAME = "20260625000005_paper_autonomous_investment_ledger_reports.sql"
DEFAULT_TABLE = "paper_probability_selection_summary_history_reports"


def _migration_path() -> Path:
    candidates = sorted(
        MIGRATIONS_DIR.glob("*probability_selection_summary_history_reports.sql"),
    )
    assert candidates, "probability selection summary history migration is missing"
    assert len(candidates) == 1
    return candidates[0]


def _migration_text() -> str:
    return _migration_path().read_text(encoding="utf-8").lower()


def _compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def _table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_probability_selection_summary_history_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{DEFAULT_TABLE}"
    return _compact(match.group(1))


def test_history_migration_uses_next_safe_version_and_unique_order() -> None:
    path = _migration_path()
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))
    names = [migration_path.name for migration_path in migration_paths]
    versions = [name.split("_", 1)[0] for name in names]

    assert path.name == EXPECTED_MIGRATION_NAME
    assert PREVIOUS_MIGRATION_NAME in names
    assert names[names.index(PREVIOUS_MIGRATION_NAME) + 1] == EXPECTED_MIGRATION_NAME
    assert Counter(versions)[EXPECTED_MIGRATION_NAME.split("_", 1)[0]] == 1


def test_history_migration_creates_report_table_matching_store_columns() -> None:
    body = _table_body(_migration_text())

    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "source_report_count integer not null",
        "latest_generated_at timestamptz",
        "latest_age_seconds integer",
        "latest_queue_count integer not null",
        "latest_selected_count integer not null",
        "latest_selected_share numeric(12, 6) not null",
        "average_selected_share numeric(12, 6) not null",
        "history_status text not null",
        "recommended_next_step text not null",
        "reason_codes jsonb not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body


def test_history_migration_constrains_statuses_probabilities_json_and_flags() -> None:
    body = _table_body(_migration_text())

    assert "check (report_sha256 ~ '^[a-f0-9]{64}$')" in body
    assert "check (source_report_count >= 0)" in body
    assert "check (latest_age_seconds is null or latest_age_seconds >= 0)" in body
    assert "check (latest_queue_count >= 0)" in body
    assert "check (latest_selected_count >= 0)" in body
    assert "check (latest_selected_count <= latest_queue_count)" in body
    assert "check (latest_selected_share >= 0 and latest_selected_share <= 1)" in body
    assert "check (average_selected_share >= 0 and average_selected_share <= 1)" in body
    assert "check (history_status in ('ready', 'watch', 'blocked'))" in body
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


def test_history_migration_constrains_next_step_and_payload_consistency() -> None:
    body = _table_body(_migration_text())

    assert (
        "recommended_next_step in ( 'collect_more_history', "
        "'refresh_selection_summary', 'review_probability_selection', "
        "'proceed_to_paper_allocation' )"
    ) in body
    for expected_check in (
        "check (payload ? 'generated_at' and jsonb_typeof(payload -> 'generated_at') = 'string' and (payload ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload ? 'config_version' and jsonb_typeof(payload -> 'config_version') = 'string' and payload ->> 'config_version' = config_version)",
        "check (payload ? 'source_report_count' and (payload ->> 'source_report_count')::integer = source_report_count)",
        "check (payload ? 'latest_queue_count' and (payload ->> 'latest_queue_count')::integer = latest_queue_count)",
        "check (payload ? 'latest_selected_count' and (payload ->> 'latest_selected_count')::integer = latest_selected_count)",
        "check (payload ? 'history_status' and jsonb_typeof(payload -> 'history_status') = 'string' and payload ->> 'history_status' = history_status)",
        "check (payload ? 'recommended_next_step' and jsonb_typeof(payload -> 'recommended_next_step') = 'string' and payload ->> 'recommended_next_step' = recommended_next_step)",
        "check (payload ? 'reason_codes' and jsonb_typeof(payload -> 'reason_codes') = 'array' and payload -> 'reason_codes' = reason_codes)",
    ):
        assert expected_check in body


def test_history_migration_uses_numeric_for_probabilities_and_jsonb_payloads() -> None:
    body = _table_body(_migration_text())

    assert "latest_selected_share numeric(12, 6)" in body
    assert "average_selected_share numeric(12, 6)" in body
    assert "reason_codes jsonb" in body
    assert "payload jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_history_migration_indexes_load_order_and_filter_paths() -> None:
    text = _compact(_migration_text())

    assert (
        "on public.paper_probability_selection_summary_history_reports "
        "(generated_at desc, inserted_at desc, report_sha256 desc)"
    ) in text
    assert (
        "config_version, generated_at desc, inserted_at desc, report_sha256 desc"
    ) in text
    assert (
        "history_status, generated_at desc, inserted_at desc, report_sha256 desc"
    ) in text
    assert (
        "latest_generated_at desc, generated_at desc, inserted_at desc, "
        "report_sha256 desc"
    ) in text
    assert "using gin (reason_codes jsonb_path_ops)" in text
    assert "using gin (payload jsonb_path_ops)" in text


def test_history_migration_keeps_table_and_index_names_under_postgres_limit() -> None:
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


def test_history_migration_stays_paper_only_without_live_surfaces() -> None:
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

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
EXPECTED_MIGRATION_NAME = "20260625000004_paper_broker_execution_records.sql"
PREVIOUS_MIGRATION_NAME = "20260625000003_probability_selection_summary_reports.sql"


def _migration_path() -> Path:
    candidates = sorted(MIGRATIONS_DIR.glob("*paper_broker_execution_records.sql"))
    assert candidates, "paper broker execution records migration is missing"
    assert len(candidates) == 1
    return candidates[0]


def _migration_text() -> str:
    return _migration_path().read_text(encoding="utf-8").lower()


def _compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def _table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_broker_execution_records\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_broker_execution_records"
    return _compact(match.group(1))


def test_broker_migration_uses_next_safe_version_and_unique_order() -> None:
    path = _migration_path()
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))
    names = [migration_path.name for migration_path in migration_paths]
    versions = [name.split("_", 1)[0] for name in names]

    assert path.name == EXPECTED_MIGRATION_NAME
    assert PREVIOUS_MIGRATION_NAME in names
    assert names[names.index(PREVIOUS_MIGRATION_NAME) + 1] == EXPECTED_MIGRATION_NAME
    assert Counter(versions)[EXPECTED_MIGRATION_NAME.split("_", 1)[0]] == 1


def test_broker_migration_creates_execution_record_table_matching_db_row_columns() -> None:
    body = _table_body(_migration_text())

    for column in (
        "record_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "execution_status text not null",
        "recommended_next_step text not null",
        "source_gate_status text not null",
        "source_proposal_count integer not null",
        "source_proposal_total_notional numeric not null",
        "execution_notional numeric not null",
        "reason_codes jsonb not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body


def test_broker_migration_constrains_statuses_json_flags_and_scalars() -> None:
    body = _table_body(_migration_text())

    assert "check (record_sha256 ~ '^[a-f0-9]{64}$')" in body
    assert "check (execution_status in (" in body
    for status in ("'paper_submitted'", "'paper_blocked'", "'paper_held'"):
        assert status in body
    assert "check (source_gate_status in ('pass', 'watch', 'blocked'))" in body
    assert "check (source_proposal_count >= 0)" in body
    assert "check (source_proposal_total_notional >= 0)" in body
    assert "check (execution_notional >= 0)" in body
    assert "check (jsonb_typeof(reason_codes) = 'array')" in body
    assert "check (jsonb_typeof(payload) = 'object')" in body
    assert "check (paper_only is true)" in body
    assert "check (report_only is true)" in body
    assert "check (readonly is true)" in body
    assert "check ((payload ->> 'paper_only')::boolean is true)" in body
    assert "check ((payload ->> 'report_only')::boolean is true)" in body
    assert "check ((payload ->> 'readonly')::boolean is true)" in body


def test_broker_migration_constrains_next_step_and_notional_consistency() -> None:
    body = _table_body(_migration_text())

    assert "execution_status = 'paper_submitted'" in body
    assert "recommended_next_step = 'route_to_paper_order_lifecycle'" in body
    assert "execution_status = 'paper_held'" in body
    assert "recommended_next_step = 'hold_for_broker_review'" in body
    assert "execution_status = 'paper_blocked'" in body
    assert (
        "recommended_next_step = 'block_paper_execution_pending_repair'" in body
    )
    assert "execution_notional > 0" in body
    assert "execution_notional = 0" in body


def test_broker_migration_uses_numeric_for_decimals_and_jsonb_for_payloads() -> None:
    body = _table_body(_migration_text())

    for column in ("source_proposal_total_notional", "execution_notional"):
        assert f"{column} numeric" in body

    assert "reason_codes jsonb" in body
    assert "payload jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_broker_migration_indexes_load_order_and_filter_paths() -> None:
    text = _compact(_migration_text())

    assert (
        "on public.paper_broker_execution_records "
        "(generated_at desc, inserted_at desc, record_sha256 desc)"
    ) in text
    assert (
        "config_version, generated_at desc, inserted_at desc, record_sha256 desc"
    ) in text
    assert (
        "execution_status, generated_at desc, inserted_at desc, record_sha256 desc"
    ) in text
    assert (
        "source_gate_status, generated_at desc, inserted_at desc, record_sha256 desc"
    ) in text
    assert "using gin (reason_codes jsonb_path_ops)" in text
    assert "using gin (payload jsonb_path_ops)" in text


def test_broker_migration_stays_paper_only_without_auth_or_wallet_surface() -> None:
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

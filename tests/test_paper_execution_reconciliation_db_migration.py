from __future__ import annotations

from pathlib import Path


def _migration_text() -> str:
    candidates = sorted(
        Path("supabase/migrations").glob("*paper_execution_reconciliation*.sql"),
    )
    assert candidates, "paper execution reconciliation migration is missing"
    assert len(candidates) == 1
    return candidates[0].read_text(encoding="utf-8").lower()


def test_reconciliation_migration_creates_report_table_with_jsonb_payloads():
    text = _migration_text()

    assert "create table if not exists public.paper_execution_reconciliation_reports" in text
    assert "report_sha256 text primary key" in text
    assert "generated_at timestamptz not null" in text
    assert "position_rows_json jsonb not null" in text
    assert "reason_codes_json jsonb not null" in text
    assert "payload_json jsonb not null" in text
    assert "inserted_at timestamptz not null default now()" in text
    assert "on public.paper_execution_reconciliation_reports" in text
    assert "generated_at desc, inserted_at desc, report_sha256 desc" in text


def test_reconciliation_migration_constrains_status_json_types_flags_and_counts():
    text = _migration_text()

    assert "check (report_sha256 ~ '^[a-f0-9]{64}$')" in text
    assert "check (reconciliation_status in (" in text
    for status in ("'reconciled'", "'has_pending'", "'has_discrepancies'"):
        assert status in text
    assert "check (jsonb_typeof(position_rows_json) = 'array')" in text
    assert "check (jsonb_typeof(reason_codes_json) = 'array')" in text
    assert "check (jsonb_typeof(payload_json) = 'object')" in text
    assert "check (paper_only is true)" in text
    assert "check (report_only is true)" in text
    assert "check (readonly is true)" in text
    for column in (
        "total_positions",
        "filled_pending_count",
        "settled_win_count",
        "settled_loss_count",
        "expired_count",
        "cancelled_count",
        "total_fill_notional",
        "total_cost_basis",
        "total_outcome_value",
    ):
        assert f"check ({column} >= 0" in text

from __future__ import annotations

from pathlib import Path


def _migration_text() -> str:
    matches = sorted(
        Path("supabase/migrations").glob("*autonomous_market_scorer*.sql"),
    )
    assert len(matches) == 1
    return matches[0].read_text(encoding="utf-8").lower()


def test_autonomous_market_scorer_migration_has_required_columns_and_constraints() -> None:
    text = _migration_text()

    assert "create table if not exists public.autonomous_market_scorer_reports" in text
    assert "report_sha256 text primary key" in text
    assert "generated_at timestamptz not null" in text
    assert "gate_status text not null" in text
    assert "reason_codes jsonb not null" in text
    assert "score_rows jsonb not null" in text
    assert "payload jsonb not null" in text
    assert "inserted_at timestamptz not null default now()" in text
    assert "check (paper_only is true)" in text
    assert "check (report_only is true)" in text
    assert "check (readonly is true)" in text
    assert "check (jsonb_typeof(reason_codes) = 'array')" in text
    assert "check (jsonb_typeof(score_rows) = 'array')" in text
    assert "check (jsonb_typeof(payload) = 'object')" in text
    assert "check (gate_status in ('pass', 'watch', 'blocked'))" in text
    for column in (
        "markets_scored",
        "markets_skipped",
        "markets_blocked",
        "top_total_score",
        "average_total_score",
        "total_recommended_notional",
    ):
        assert f"check ({column} >= 0)" in text


def test_autonomous_market_scorer_migration_indexes_load_order() -> None:
    text = _migration_text()

    assert "generated_at desc, inserted_at desc, report_sha256 desc" in text
    assert "gate_status, generated_at desc, inserted_at desc, report_sha256 desc" in text

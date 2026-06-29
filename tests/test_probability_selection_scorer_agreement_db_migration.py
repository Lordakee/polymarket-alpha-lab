from __future__ import annotations

from pathlib import Path
import re


def _migration_text() -> str:
    matches = sorted(
        Path("supabase/migrations").glob(
            "*probability_selection_scorer_agreement_reports*.sql",
        ),
    )
    assert len(matches) == 1
    return matches[0].read_text(encoding="utf-8").lower()


def test_agreement_migration_has_required_columns_and_constraints() -> None:
    text = _migration_text()

    assert (
        "create table if not exists public.probability_selection_scorer_agreement_reports"
        in text
    )
    assert "report_sha256 text primary key" in text
    assert "generated_at timestamptz not null" in text
    assert "selection_generated_at timestamptz" in text
    assert "scorer_generated_at timestamptz" in text
    assert "scorer_gate_status text not null" in text
    assert "agreement_status text not null" in text
    assert "recommended_next_step text not null" in text
    assert "reason_codes jsonb not null" in text
    assert "reason_code_divergence_counts jsonb not null" in text
    assert "payload jsonb not null" in text
    assert "inserted_at timestamptz not null default now()" in text
    assert "check (paper_only is true)" in text
    assert "check (report_only is true)" in text
    assert "check (readonly is true)" in text
    assert "check ((payload ->> 'paper_only') = 'true')" in text
    assert "check ((payload ->> 'report_only') = 'true')" in text
    assert "check ((payload ->> 'readonly') = 'true')" in text
    assert "check (not (payload ?| array[" in text
    assert "check (jsonb_typeof(reason_codes) = 'array')" in text
    assert "check (jsonb_typeof(reason_code_divergence_counts) = 'array')" in text
    assert "check (jsonb_typeof(payload) = 'object')" in text
    assert (
        "check (agreement_status in ('aligned', 'gate_blocked', "
        "'insufficient_identifiers', 'low_overlap', 'missing_inputs'))"
        in text
    )
    for column in (
        "selected_count",
        "scorer_candidate_count",
        "selected_market_overlap_count",
        "selected_condition_overlap_count",
        "rejected_but_scored_count",
        "scored_but_unselected_count",
    ):
        assert f"check ({column} >= 0)" in text


def test_agreement_migration_indexes_load_order_and_filters() -> None:
    text = _migration_text()

    assert "generated_at desc, inserted_at desc, report_sha256 desc" in text
    assert "config_version, generated_at desc, inserted_at desc, report_sha256 desc" in text
    assert "agreement_status, generated_at desc, inserted_at desc, report_sha256 desc" in text
    assert "scorer_gate_status, generated_at desc, inserted_at desc, report_sha256 desc" in text


def test_agreement_migration_has_no_market_or_live_trading_columns() -> None:
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


def test_agreement_migration_rejects_sensitive_payload_keys() -> None:
    text = _migration_text()

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

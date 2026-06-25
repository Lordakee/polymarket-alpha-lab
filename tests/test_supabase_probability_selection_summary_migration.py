from __future__ import annotations

from pathlib import Path


def _migration_path() -> Path:
    candidates = sorted(
        Path("supabase/migrations").glob("*probability_selection_summary_reports.sql"),
    )
    assert candidates, "paper probability selection summary migration is missing"
    assert len(candidates) == 1
    return candidates[0]


def _migration_text() -> str:
    return _migration_path().read_text(encoding="utf-8").lower()


def test_selection_summary_migration_uses_next_safe_version_and_canonical_name() -> None:
    path = _migration_path()

    assert path.name == (
        "20260625000003_probability_selection_summary_reports.sql"
    )


def test_selection_summary_migration_creates_report_table_matching_store_columns() -> None:
    text = _migration_text()

    assert (
        "create table if not exists public.paper_probability_selection_summary_reports"
        in text
    )
    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "source_queue_config_version text not null",
        "source_cost_stress_config_version text not null",
        "queue_count integer not null",
        "ready_count integer not null",
        "watch_count integer not null",
        "blocked_count integer not null",
        "missing_stress_count integer not null",
        "rows jsonb not null",
        "reason_codes jsonb not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in text


def test_selection_summary_migration_constrains_hash_status_json_flags_and_counts() -> None:
    text = _migration_text()

    assert "check (report_sha256 ~ '^[a-f0-9]{64}$')" in text
    assert "check (jsonb_typeof(rows) = 'array')" in text
    assert "check (jsonb_typeof(reason_codes) = 'array')" in text
    assert "check (jsonb_typeof(payload) = 'object')" in text
    assert "check (paper_only is true)" in text
    assert "check (report_only is true)" in text
    assert "check (readonly is true)" in text
    assert (
        "check (queue_count = ready_count + watch_count + blocked_count)" in text
    )
    assert "check (queue_count = jsonb_array_length(rows))" in text
    assert "check ((payload ->> 'paper_only') = 'true')" in text
    assert "check ((payload ->> 'report_only') = 'true')" in text
    assert "check ((payload ->> 'readonly') = 'true')" in text
    for column in (
        "queue_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "missing_stress_count",
    ):
        assert f"check ({column} >= 0)" in text


def test_selection_summary_migration_indexes_load_order_and_filter_paths() -> None:
    text = _migration_text()

    assert (
        "on public.paper_probability_selection_summary_reports "
        "(generated_at desc, inserted_at desc, report_sha256 desc)"
    ) in text
    assert (
        "config_version, generated_at desc, inserted_at desc, report_sha256 desc"
    ) in text
    assert (
        "source_queue_config_version, generated_at desc, inserted_at desc, report_sha256 desc"
    ) in text
    assert (
        "source_cost_stress_config_version, generated_at desc, inserted_at desc, report_sha256 desc"
    ) in text
    for column in ("ready_count", "watch_count", "blocked_count"):
        assert f"where {column} > 0" in text
    assert "using gin (reason_codes jsonb_path_ops)" in text
    assert "using gin (rows jsonb_path_ops)" in text
    assert "using gin (payload jsonb_path_ops)" in text

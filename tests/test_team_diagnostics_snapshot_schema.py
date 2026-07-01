import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260701000001_team_diagnostics_snapshots.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.team_diagnostics_snapshots\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.team_diagnostics_snapshots"
    return compact(match.group(1))


def test_migration_creates_team_diagnostics_snapshot_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "source_config_version text not null",
        "team_id text null",
        "market_slug text null",
        "forecast_id text null",
        "forecast_row_count integer not null",
        "evidence_row_count integer not null",
        "outcome_row_count integer not null",
        "memory_eligible_reference_count integer not null",
        "calibration_status text not null",
        "calibration_settled_count integer not null",
        "calibration_group_count integer not null",
        "event_template_status text not null",
        "event_template_row_count integer not null",
        "source_reliability_row_count integer not null",
        "source_reliability_missing_source_evidence_count integer not null",
        "evidence_quality_status text not null",
        "evidence_quality_pass_count integer not null",
        "evidence_quality_watch_count integer not null",
        "evidence_quality_blocked_count integer not null",
        "evidence_quality_average_quality_score numeric not null",
        "reason_codes_json jsonb not null default '[]'::jsonb",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_team_diagnostics_snapshot_invariants():
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (forecast_row_count >= 0)",
        "check (evidence_row_count >= 0)",
        "check (outcome_row_count >= 0)",
        "check (memory_eligible_reference_count >= 0)",
        "check (calibration_status <> '')",
        "check (calibration_settled_count >= 0)",
        "check (calibration_group_count >= 0)",
        "check (event_template_status <> '')",
        "check (event_template_row_count >= 0)",
        "check (source_reliability_row_count >= 0)",
        "check (source_reliability_missing_source_evidence_count >= 0)",
        "check (evidence_quality_status in ('evidence_quality_pass', 'evidence_quality_watch', 'evidence_quality_blocked'))",
        "check (evidence_quality_pass_count >= 0)",
        "check (evidence_quality_watch_count >= 0)",
        "check (evidence_quality_blocked_count >= 0)",
        "check (evidence_quality_average_quality_score >= 0 and evidence_quality_average_quality_score <= 1)",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check ((payload_json ->> 'paper_only') = 'true')",
        "check ((payload_json ->> 'report_only') = 'true')",
        "check ((payload_json ->> 'readonly') = 'true')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_uses_numeric_and_jsonb_for_compact_snapshot_fields():
    body = table_body(migration_sql())

    assert "evidence_quality_average_quality_score numeric" in body
    assert "reason_codes_json jsonb" in body
    assert "payload_json jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_team_filter_and_history_lookup_indexes():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_tds_generated_at on public.team_diagnostics_snapshots (generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_tds_team_market_history on public.team_diagnostics_snapshots (team_id, market_slug, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_tds_forecast_history on public.team_diagnostics_snapshots (forecast_id, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_tds_config_version_history on public.team_diagnostics_snapshots (config_version, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_tds_reason_codes_gin on public.team_diagnostics_snapshots using gin (reason_codes_json jsonb_path_ops);",
        "create index if not exists idx_tds_payload_gin on public.team_diagnostics_snapshots using gin (payload_json jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_non_phase_one_surfaces():
    sql = migration_sql().lower()

    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\border\b",
        r"\baccount\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
        r"\bsign(?:s|ed|ing|ature)?\b",
        r"\bsubmit(?:s|ted|ting|tal)?\b",
        r"\bcancel(?:s|ed|ing|lation)?\b",
        r"\breplace(?:s|d|ment)?\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

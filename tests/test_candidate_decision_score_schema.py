from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260707000000_candidate_decision_score_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.candidate_decision_score_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.candidate_decision_score_reports"
    return compact(match.group(1))


def test_migration_creates_candidate_decision_score_report_table_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "candidate_id text not null",
        "market_id text not null",
        "normalized_market_question text not null",
        "primary_team_id text not null",
        "secondary_team_ids jsonb not null default '[]'::jsonb",
        "selected_side text not null",
        "forecast_probability numeric(18, 6)",
        "executable_price numeric(18, 6)",
        "gross_edge numeric(18, 6)",
        "estimated_cost_drag numeric(18, 6) not null",
        "net_edge numeric(18, 6)",
        "cost_score numeric(18, 6) not null",
        "liquidity_score numeric(18, 6) not null",
        "evidence_score numeric(18, 6) not null",
        "resolution_score numeric(18, 6) not null",
        "team_memory_score numeric(18, 6) not null",
        "team_memory_policy text not null",
        "decision_score numeric(18, 6) not null",
        "action text not null",
        "hard_blocker_codes jsonb not null default '[]'::jsonb",
        "reason_codes jsonb not null default '[]'::jsonb",
        "source_report_refs jsonb not null default '[]'::jsonb",
        "derived_validation_digest text not null",
        "boundary_statement text not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_candidate_decision_score_invariants() -> None:
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (selected_side in ('yes', 'no'))",
        "check (forecast_probability is null or forecast_probability between 0 and 1)",
        "check (executable_price is null or executable_price between 0 and 1)",
        "check (gross_edge is null or gross_edge between -1 and 1)",
        "check (estimated_cost_drag >= 0)",
        "check (net_edge is null or net_edge between -1 and 1)",
        "check (cost_score between 0 and 1)",
        "check (liquidity_score between 0 and 1)",
        "check (evidence_score between 0 and 1)",
        "check (resolution_score between 0 and 1)",
        "check (team_memory_score between 0 and 1)",
        "check (team_memory_policy in ('allow', 'throttle', 'block'))",
        "check (decision_score between 0 and 1)",
        "check (action in ('reject', 'watch', 'research_more', 'paper_recommend'))",
        "check (derived_validation_digest ~ '^[a-f0-9]{64}$')",
        "check (jsonb_typeof(secondary_team_ids) = 'array')",
        "check (jsonb_typeof(hard_blocker_codes) = 'array')",
        "check (jsonb_typeof(reason_codes) = 'array')",
        "check (jsonb_typeof(source_report_refs) = 'array')",
        "check (jsonb_typeof(payload) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_enforces_payload_materialized_column_consistency() -> None:
    body = table_body(migration_sql())

    expected_fragments = (
        "check (((payload ->> 'generated_at')::timestamptz = generated_at) is true)",
        "check ((payload ->> 'config_version' = config_version) is true)",
        "check ((payload ->> 'candidate_id' = candidate_id) is true)",
        "check ((payload ->> 'market_id' = market_id) is true)",
        "check ((payload ->> 'normalized_market_question' = normalized_market_question) is true)",
        "check ((payload ->> 'primary_team_id' = primary_team_id) is true)",
        "check ((payload -> 'secondary_team_ids' = secondary_team_ids) is true)",
        "check ((payload ->> 'selected_side' = selected_side) is true)",
        "((payload ->> 'forecast_probability')::numeric = forecast_probability)",
        "((payload ->> 'executable_price')::numeric = executable_price)",
        "((payload ->> 'gross_edge')::numeric = gross_edge)",
        "check (((payload ->> 'estimated_cost_drag')::numeric = estimated_cost_drag) is true)",
        "((payload ->> 'net_edge')::numeric = net_edge)",
        "check (((payload ->> 'cost_score')::numeric = cost_score) is true)",
        "check (((payload ->> 'liquidity_score')::numeric = liquidity_score) is true)",
        "check (((payload ->> 'evidence_score')::numeric = evidence_score) is true)",
        "check (((payload ->> 'resolution_score')::numeric = resolution_score) is true)",
        "check (((payload ->> 'team_memory_score')::numeric = team_memory_score) is true)",
        "check ((payload ->> 'team_memory_policy' = team_memory_policy) is true)",
        "check (((payload ->> 'decision_score')::numeric = decision_score) is true)",
        "check ((payload ->> 'action' = action) is true)",
        "check ((payload -> 'hard_blocker_codes' = hard_blocker_codes) is true)",
        "check ((payload -> 'reason_codes' = reason_codes) is true)",
        "check ((payload -> 'source_report_refs' = source_report_refs) is true)",
        "check ((payload ->> 'derived_validation_digest' = derived_validation_digest) is true)",
        "check ((payload ->> 'boundary_statement' = boundary_statement) is true)",
        "check ((payload ->> 'paper_only' = 'true') is true)",
        "check ((payload ->> 'report_only' = 'true') is true)",
        "check ((payload ->> 'readonly' = 'true') is true)",
    )
    for fragment in expected_fragments:
        assert fragment in body


def test_migration_blocks_sensitive_payload_keys() -> None:
    body = table_body(migration_sql())

    assert "payload::text !~*" in body
    for term in (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "execute",
        "submit",
        "cancel",
        "sign",
        "private[_ -]?key",
        "api[_ -]?key",
        "secret",
        "token",
        "credential",
    ):
        assert term in body


def test_migration_adds_store_aligned_lookup_indexes() -> None:
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_cdsr_generated_at on public.candidate_decision_score_reports (generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_cdsr_action_generated_at on public.candidate_decision_score_reports (action, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_cdsr_primary_team_generated_at on public.candidate_decision_score_reports (primary_team_id, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_cdsr_config_version_generated_at on public.candidate_decision_score_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_cdsr_candidate_market on public.candidate_decision_score_reports (candidate_id, market_id, generated_at desc);",
        "create index if not exists idx_cdsr_reason_codes_gin on public.candidate_decision_score_reports using gin (reason_codes jsonb_path_ops);",
        "create index if not exists idx_cdsr_source_report_refs_gin on public.candidate_decision_score_reports using gin (source_report_refs jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_has_no_live_trading_or_external_mutation_paths() -> None:
    raw_sql = migration_sql().lower()
    sql = compact(raw_sql)

    assert "comment on table public.candidate_decision_score_reports is" in sql
    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bcreate\s+(?:function|trigger|policy)\b",
        r"\bgrant\b",
        r"\bnotify\b",
        r"\bhttp(?:s)?://",
        r"\bnet\.",
        r"\bvault\.",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, raw_sql), pattern

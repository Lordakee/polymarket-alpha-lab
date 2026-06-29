import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260629000000_paper_strategy_cycle_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_strategy_cycle_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_strategy_cycle_reports"
    return compact(match.group(1))


def test_migration_creates_strategy_cycle_report_table_with_required_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "scan_market_count integer not null",
        "considered_count integer not null",
        "snapshot_ready_count integer not null",
        "cost_aware_report_count integer not null",
        "blocked_counts_json jsonb not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_strategy_cycle_report_invariants_with_checks() -> None:
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (scan_market_count >= 0)",
        "check (considered_count >= 0)",
        "check (snapshot_ready_count >= 0)",
        "check (cost_aware_report_count >= 0)",
        "check (jsonb_typeof(blocked_counts_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (snapshot_ready_count <= considered_count)",
        "check (considered_count <= scan_market_count)",
        "check (cost_aware_report_count = snapshot_ready_count)",
        "check (payload_json ? 'paper_only' and (payload_json ->> 'paper_only')::boolean is true)",
        "check (payload_json ? 'report_only' and (payload_json ->> 'report_only')::boolean is true)",
        "check (payload_json ? 'generated_at' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and payload_json ->> 'config_version' = config_version)",
        "check (payload_json ? 'scan_market_count' and (payload_json ->> 'scan_market_count')::integer = scan_market_count)",
        "check (payload_json ? 'considered_count' and (payload_json ->> 'considered_count')::integer = considered_count)",
        "check (payload_json ? 'snapshot_ready_count' and (payload_json ->> 'snapshot_ready_count')::integer = snapshot_ready_count)",
        "check (payload_json ? 'cost_aware_report_count' and (payload_json ->> 'cost_aware_report_count')::integer = cost_aware_report_count)",
        "check (payload_json ? 'blocked_counts' and blocked_counts_json = payload_json -> 'blocked_counts')",
    )
    for check in expected_checks:
        assert check in body


def test_migration_adds_strategy_cycle_report_lookup_indexes() -> None:
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_pscr_generated_at on public.paper_strategy_cycle_reports (generated_at desc);",
        "create index if not exists idx_pscr_config_version_generated_at on public.paper_strategy_cycle_reports (config_version, generated_at desc);",
        "create index if not exists idx_pscr_blocked_counts_json_gin on public.paper_strategy_cycle_reports using gin (blocked_counts_json jsonb_path_ops);",
        "create index if not exists idx_pscr_payload_json_gin on public.paper_strategy_cycle_reports using gin (payload_json jsonb_path_ops);",
        "create index if not exists idx_pscr_load_generated_inserted_sha on public.paper_strategy_cycle_reports (generated_at desc, inserted_at desc, report_sha256 desc);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_live_trading_or_secret_terms() -> None:
    sql = migration_sql().lower()

    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\border\b",
        r"\bsubmit(?:s|ted|ting|tal)?\b",
        r"\bcancel(?:s|ed|ing|lation)?\b",
        r"\bsign(?:s|ed|ing|ature)?\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

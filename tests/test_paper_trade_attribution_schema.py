import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260630000100_paper_trade_attribution_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_trade_attribution_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_trade_attribution_reports"
    return compact(match.group(1))


def test_migration_creates_attribution_report_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "trade_count integer not null",
        "row_count integer not null",
        "market_count integer not null",
        "filled_count integer not null",
        "complete_fill_count integer not null",
        "partial_fill_count integer not null",
        "resolved_count integer",
        "pending_count integer",
        "realized_win_count integer",
        "realized_loss_count integer",
        "total_requested_size numeric not null",
        "total_filled_size numeric not null",
        "total_unfilled_size numeric not null",
        "total_notional numeric not null",
        "first_trade_decision_at timestamptz",
        "latest_trade_decision_at timestamptz",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_attribution_report_invariants_with_checks():
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (trade_count >= 0)",
        "check (row_count >= 0)",
        "check (market_count >= 0)",
        "check (filled_count >= 0)",
        "check (complete_fill_count >= 0)",
        "check (partial_fill_count >= 0)",
        "check (resolved_count is null or resolved_count >= 0)",
        "check (pending_count is null or pending_count >= 0)",
        "check (realized_win_count is null or realized_win_count >= 0)",
        "check (realized_loss_count is null or realized_loss_count >= 0)",
        "check (total_requested_size >= 0)",
        "check (total_filled_size >= 0)",
        "check (total_unfilled_size >= 0)",
        "check (total_notional >= 0)",
        "check (filled_count <= trade_count)",
        "check (complete_fill_count + partial_fill_count <= trade_count)",
        "check ((resolved_count is null and pending_count is null and realized_win_count is null and realized_loss_count is null) or (resolved_count is not null and pending_count is not null and realized_win_count is not null and realized_loss_count is not null))",
        "check (resolved_count is null or resolved_count + pending_count = trade_count)",
        "check (resolved_count is null or realized_win_count + realized_loss_count = resolved_count)",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (payload_json ? 'rows' and jsonb_typeof(payload_json -> 'rows') = 'array')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_uses_numeric_for_decimal_scalars_and_jsonb_for_payloads():
    body = table_body(migration_sql())

    decimal_columns = (
        "total_requested_size",
        "total_filled_size",
        "total_unfilled_size",
        "total_notional",
    )
    for column in decimal_columns:
        assert f"{column} numeric" in body

    assert "payload_json jsonb" in body
    assert "double precision" not in body
    assert not re.search(r"\breal\b", body)
    assert "float" not in body


def test_migration_adds_useful_lookup_indexes():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_ptar_generated_inserted_report on public.paper_trade_attribution_reports (generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_ptar_config_generated on public.paper_trade_attribution_reports (config_version, generated_at desc);",
        "create index if not exists idx_ptar_payload_json_gin on public.paper_trade_attribution_reports using gin (payload_json jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_live_trading_or_account_terms():
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

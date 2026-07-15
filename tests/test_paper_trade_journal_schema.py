import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260619010000_paper_trade_journal_records.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_trade_journal_records\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_trade_journal_records"
    return compact(match.group(1))


def test_migration_creates_paper_trade_journal_table_with_required_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "record_sha256 text primary key",
        "packet_id text not null",
        "decision_timestamp_utc timestamptz not null",
        "condition_id text not null",
        "token_id text not null",
        "market_slug text not null",
        "outcome_name text not null",
        "order_side text not null",
        "fill_status text not null",
        "fill_filled_size numeric not null",
        "fill_average_price numeric not null",
        "account_equity_before_trade numeric not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_paper_trade_journal_invariants_with_checks() -> None:
    body = table_body(migration_sql())

    expected_checks = (
        "check (record_sha256 ~ '^[a-f0-9]{64}$')",
        "check (order_side in ('buy', 'sell'))",
        "check (fill_status in ('complete', 'partial'))",
        "check (fill_filled_size > 0)",
        "check (fill_average_price >= 0 and fill_average_price <= 1)",
        "check (account_equity_before_trade > 0)",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_adds_useful_lookup_indexes() -> None:
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_ptjr_decision_timestamp on public.paper_trade_journal_records (decision_timestamp_utc desc);",
        "create index if not exists idx_ptjr_condition_decision on public.paper_trade_journal_records (condition_id, decision_timestamp_utc desc);",
        "create index if not exists idx_ptjr_token_decision on public.paper_trade_journal_records (token_id, decision_timestamp_utc desc);",
        "create index if not exists idx_ptjr_market_slug_decision on public.paper_trade_journal_records (market_slug, decision_timestamp_utc desc);",
        "create index if not exists idx_ptjr_payload_json_gin on public.paper_trade_journal_records using gin (payload_json jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_live_trading_or_secret_terms() -> None:
    sql = migration_sql().lower()

    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\bsubmit(?:s|ted|ting|tal)?\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

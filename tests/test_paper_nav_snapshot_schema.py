import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260619010100_paper_nav_snapshots.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_nav_snapshots\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_nav_snapshots"
    return compact(match.group(1))


def test_migration_creates_nav_snapshot_table_with_required_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "snapshot_sha256 text primary key",
        "marked_at timestamptz not null",
        "starting_cash numeric not null",
        "cash_balance numeric not null",
        "exit_nav numeric not null",
        "midpoint_nav numeric",
        "total_cost_basis numeric not null",
        "unrealized_exit_pnl numeric not null",
        "mark_count integer not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_nav_snapshot_invariants_with_checks() -> None:
    body = table_body(migration_sql())

    expected_checks = (
        "check (snapshot_sha256 ~ '^[a-f0-9]{64}$')",
        "check (starting_cash > 0)",
        "check (cash_balance >= 0)",
        "check (exit_nav >= 0)",
        "check (midpoint_nav is null or midpoint_nav >= 0)",
        "check (total_cost_basis >= 0)",
        "check (mark_count >= 0)",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_adds_useful_nav_snapshot_lookup_indexes() -> None:
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_pns_marked_at_snapshot_sha256 on public.paper_nav_snapshots (marked_at desc, snapshot_sha256 desc);",
        "create index if not exists idx_pns_mark_count_marked_at on public.paper_nav_snapshots (mark_count, marked_at desc);",
        "create index if not exists idx_pns_payload_json_gin on public.paper_nav_snapshots using gin (payload_json jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_live_trading_or_account_terms() -> None:
    sql = migration_sql().lower()

    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\border\s+book\b",
        r"\baccount\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

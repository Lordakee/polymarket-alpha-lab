import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260706000000_strategy_candidate_decision_matrix_reports.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.strategy_candidate_decision_matrix_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.strategy_candidate_decision_matrix_reports"
    return compact(match.group(1))


def test_migration_creates_strategy_candidate_decision_matrix_table_with_required_columns():
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "source_queue_config_version text not null",
        "decision_matrix_status text not null",
        "candidate_count integer not null",
        "advance_count integer not null",
        "monitor_count integer not null",
        "decline_count integer not null",
        "blocked_count integer not null",
        "reason_codes_json jsonb not null default '[]'::jsonb",
        "rows_json jsonb not null default '[]'::jsonb",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_strategy_candidate_decision_matrix_invariants_with_checks():
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (decision_matrix_status in ('ready', 'watch', 'blocked'))",
        "check (candidate_count >= 0)",
        "check (advance_count >= 0)",
        "check (monitor_count >= 0)",
        "check (decline_count >= 0)",
        "check (blocked_count >= 0)",
        "check (advance_count + monitor_count + decline_count + blocked_count = candidate_count)",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(rows_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (((payload_json ->> 'generated_at')::timestamptz = generated_at) is true)",
        "check ((payload_json ->> 'config_version' = config_version) is true)",
        "check ((payload_json ->> 'source_queue_config_version' = source_queue_config_version) is true)",
        "check ((payload_json ->> 'decision_matrix_status' = decision_matrix_status) is true)",
        "check (((payload_json ->> 'candidate_count')::integer = candidate_count) is true)",
        "check (((payload_json ->> 'advance_count')::integer = advance_count) is true)",
        "check (((payload_json ->> 'monitor_count')::integer = monitor_count) is true)",
        "check (((payload_json ->> 'decline_count')::integer = decline_count) is true)",
        "check (((payload_json ->> 'blocked_count')::integer = blocked_count) is true)",
        "check ((payload_json -> 'reason_codes' = reason_codes_json) is true)",
        "check ((payload_json -> 'rows' = rows_json) is true)",
        "check ((payload_json ->> 'paper_only' = 'true') is true)",
        "check ((payload_json ->> 'report_only' = 'true') is true)",
        "check ((payload_json ->> 'readonly' = 'true') is true)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_blocks_plaintext_sensitive_payload_keys():
    body = table_body(migration_sql())

    assert "payload_json::text !~*" in body
    assert '"[[:space:]]*:' in body
    sensitive_key_terms = (
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
    )
    for term in sensitive_key_terms:
        assert term in body


def test_migration_adds_useful_decision_matrix_lookup_indexes():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_scdmr_generated_at on public.strategy_candidate_decision_matrix_reports (generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_scdmr_decision_matrix_status_generated_at on public.strategy_candidate_decision_matrix_reports (decision_matrix_status, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_scdmr_config_version_generated_at on public.strategy_candidate_decision_matrix_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_scdmr_source_queue_config_version_generated_at on public.strategy_candidate_decision_matrix_reports (source_queue_config_version, generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_scdmr_reason_codes_json_gin on public.strategy_candidate_decision_matrix_reports using gin (reason_codes_json jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_index_full_payload_or_rows_json():
    sql = compact(migration_sql())

    assert "using gin (payload_json" not in sql
    assert "using gin (rows_json" not in sql


def test_migration_documents_local_readonly_report_table_without_external_mutation_paths():
    sql = compact(migration_sql())

    assert "comment on table public.strategy_candidate_decision_matrix_reports is" in sql
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
        assert not re.search(pattern, sql), pattern


def test_migration_does_not_define_live_trading_or_account_columns():
    raw_sql = migration_sql().lower()

    column_names = re.findall(
        r"(?:^|\n)\s*([a-z_][a-z0-9_]*)\s+"
        r"(?:text|integer|numeric|jsonb|boolean|timestamptz)\b",
        raw_sql,
    )
    forbidden_column_pattern = re.compile(
        r"(^|_)(auth|wallet|account|order|private_key|api_key|secret|token|"
        r"trade|execute|submit|cancel|signing|signature)(_|$)",
    )
    for column_name in column_names:
        assert not forbidden_column_pattern.search(column_name), column_name

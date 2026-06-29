from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
EXPECTED_MIGRATION_NAME = (
    "20260629000001_paper_strategy_cycle_report_history_gate_reports.sql"
)
PREVIOUS_MIGRATION_NAME = "20260629000000_paper_strategy_cycle_reports.sql"
DEFAULT_TABLE = "paper_strategy_cycle_report_history_gate_reports"


def _migration_path() -> Path:
    candidates = sorted(
        MIGRATIONS_DIR.glob("*paper_strategy_cycle_report_history_gate_reports.sql"),
    )
    assert candidates, "paper strategy cycle report history gate migration is missing"
    assert len(candidates) == 1
    return candidates[0]


def _migration_text() -> str:
    return _migration_path().read_text(encoding="utf-8").lower()


def _compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def _without_space_after_open_paren(sql: str) -> str:
    sql = re.sub(r"\(\s+", "(", sql)
    return re.sub(r"\s+\)", ")", sql)


def _compact_index_sql(sql: str) -> str:
    sql = _compact(sql)
    return _without_space_after_open_paren(sql)


def _table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_strategy_cycle_report_history_gate_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{DEFAULT_TABLE}"
    return _compact(match.group(1))


def test_history_gate_migration_uses_next_safe_version_and_unique_sequence() -> None:
    path = _migration_path()
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))
    names = [migration_path.name for migration_path in migration_paths]
    versions = [name.split("_", 1)[0] for name in names]

    assert path.name == EXPECTED_MIGRATION_NAME
    assert PREVIOUS_MIGRATION_NAME in names
    assert names[names.index(PREVIOUS_MIGRATION_NAME) + 1] == EXPECTED_MIGRATION_NAME
    assert Counter(versions)[EXPECTED_MIGRATION_NAME.split("_", 1)[0]] == 1


def test_history_gate_migration_creates_report_table_with_contract_columns() -> None:
    body = _table_body(_migration_text())

    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "source_config_version text not null",
        "source_generated_at timestamptz not null",
        "gate_status text not null",
        "recommended_next_step text not null",
        "source_history_status text not null",
        "source_report_count integer not null",
        "latest_source_generated_at timestamptz null",
        "latest_source_age_seconds integer null",
        "latest_snapshot_ready_share numeric(18, 6) not null",
        "blocked_market_share numeric(18, 6) not null",
        "latest_snapshot_ready_count integer not null",
        "latest_considered_count integer not null",
        "total_blocked_market_count integer not null",
        "reason_code_counts_json jsonb not null",
        "reason_codes_json jsonb not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body


def test_history_gate_migration_constrains_status_next_step_counts_and_flags() -> None:
    body = _without_space_after_open_paren(_table_body(_migration_text()))

    for expected_check in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (gate_status in ('pass', 'watch', 'blocked'))",
        "check (source_history_status in ('pass', 'watch', 'blocked'))",
        "check (recommended_next_step = case gate_status when 'pass' then 'allow_strategy_cycle_history_gate' when 'watch' then 'throttle_strategy_cycle_history_gate' when 'blocked' then 'block_strategy_cycle_history_gate' end)",
        "check (source_report_count > 0)",
        "check (latest_source_age_seconds is null or latest_source_age_seconds >= 0)",
        "check (latest_snapshot_ready_share >= 0 and latest_snapshot_ready_share <= 1)",
        "check (blocked_market_share >= 0 and blocked_market_share <= 1)",
        "check (latest_snapshot_ready_count >= 0)",
        "check (latest_considered_count >= 0)",
        "check (total_blocked_market_count >= 0)",
        "check (latest_snapshot_ready_count <= latest_considered_count)",
        "check (jsonb_typeof(reason_code_counts_json) = 'array')",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body


def test_history_gate_migration_enforces_json_payload_consistency() -> None:
    body = _table_body(_migration_text())

    for expected_check in (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (payload_json ? 'source_config_version' and jsonb_typeof(payload_json -> 'source_config_version') = 'string' and payload_json ->> 'source_config_version' = source_config_version)",
        "check (payload_json ? 'source_generated_at' and jsonb_typeof(payload_json -> 'source_generated_at') = 'string' and (payload_json ->> 'source_generated_at')::timestamptz = source_generated_at)",
        "check (payload_json ? 'gate_status' and jsonb_typeof(payload_json -> 'gate_status') = 'string' and payload_json ->> 'gate_status' = gate_status)",
        "check (payload_json ? 'recommended_next_step' and jsonb_typeof(payload_json -> 'recommended_next_step') = 'string' and payload_json ->> 'recommended_next_step' = recommended_next_step)",
        "check (payload_json ? 'source_history_status' and jsonb_typeof(payload_json -> 'source_history_status') = 'string' and payload_json ->> 'source_history_status' = source_history_status)",
        "check (payload_json ? 'source_report_count' and (payload_json ->> 'source_report_count')::integer = source_report_count)",
        "check (payload_json ? 'latest_source_age_seconds' and ((latest_source_age_seconds is null and payload_json -> 'latest_source_age_seconds' = 'null'::jsonb) or (latest_source_age_seconds is not null and (payload_json ->> 'latest_source_age_seconds')::integer = latest_source_age_seconds)))",
        "check (payload_json ? 'latest_source_generated_at' and ((latest_source_generated_at is null and payload_json -> 'latest_source_generated_at' = 'null'::jsonb) or (latest_source_generated_at is not null and jsonb_typeof(payload_json -> 'latest_source_generated_at') = 'string' and (payload_json ->> 'latest_source_generated_at')::timestamptz = latest_source_generated_at)))",
        "check (payload_json ? 'latest_snapshot_ready_share' and jsonb_typeof(payload_json -> 'latest_snapshot_ready_share') = 'string' and (payload_json ->> 'latest_snapshot_ready_share')::numeric(18, 6) = latest_snapshot_ready_share)",
        "check (payload_json ? 'blocked_market_share' and jsonb_typeof(payload_json -> 'blocked_market_share') = 'string' and (payload_json ->> 'blocked_market_share')::numeric(18, 6) = blocked_market_share)",
        "check (payload_json ? 'latest_snapshot_ready_count' and (payload_json ->> 'latest_snapshot_ready_count')::integer = latest_snapshot_ready_count)",
        "check (payload_json ? 'latest_considered_count' and (payload_json ->> 'latest_considered_count')::integer = latest_considered_count)",
        "check (payload_json ? 'total_blocked_market_count' and (payload_json ->> 'total_blocked_market_count')::integer = total_blocked_market_count)",
        "check (payload_json ? 'reason_code_counts' and jsonb_typeof(payload_json -> 'reason_code_counts') = 'array' and reason_code_counts_json = payload_json -> 'reason_code_counts')",
        "check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and reason_codes_json = payload_json -> 'reason_codes')",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)",
    ):
        assert expected_check in body


def test_history_gate_migration_uses_jsonb_payloads_without_float_columns() -> None:
    body = _table_body(_migration_text())

    for jsonb_column in (
        "reason_code_counts_json",
        "reason_codes_json",
        "payload_json",
    ):
        assert f"{jsonb_column} jsonb" in body

    assert "latest_snapshot_ready_share numeric(18, 6)" in body
    assert "blocked_market_share numeric(18, 6)" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_history_gate_migration_adds_expected_lookup_indexes() -> None:
    sql = _compact_index_sql(_migration_text())

    for index in (
        "create index if not exists pschgr_generated_at_idx on public.paper_strategy_cycle_report_history_gate_reports (generated_at desc);",
        "create index if not exists pschgr_gate_status_generated_at_idx on public.paper_strategy_cycle_report_history_gate_reports (gate_status, generated_at desc);",
        "create index if not exists pschgr_config_version_generated_at_idx on public.paper_strategy_cycle_report_history_gate_reports (config_version, generated_at desc);",
        "create index if not exists pschgr_source_config_generated_at_idx on public.paper_strategy_cycle_report_history_gate_reports (source_config_version, source_generated_at desc);",
        "create index if not exists pschgr_reason_codes_json_idx on public.paper_strategy_cycle_report_history_gate_reports using gin (reason_codes_json jsonb_path_ops);",
        "create index if not exists pschgr_payload_json_idx on public.paper_strategy_cycle_report_history_gate_reports using gin (payload_json jsonb_path_ops);",
        "create index if not exists pschgr_load_sort_idx on public.paper_strategy_cycle_report_history_gate_reports (generated_at desc, inserted_at desc, report_sha256 desc);",
    ):
        assert index in sql


def test_history_gate_migration_keeps_table_and_index_names_under_postgres_limit() -> None:
    text = _migration_text()
    names = set(
        re.findall(
            r"create\s+table\s+if\s+not\s+exists\s+public\.([a-z0-9_]+)",
            text,
            flags=re.IGNORECASE,
        ),
    )
    names.update(
        re.findall(
            r"create\s+(?:unique\s+)?index\s+if\s+not\s+exists\s+([a-z0-9_]+)",
            text,
            flags=re.IGNORECASE,
        ),
    )

    assert DEFAULT_TABLE in names
    assert names
    assert all(len(name) <= 63 for name in names)


def test_history_gate_migration_avoids_forbidden_database_surfaces() -> None:
    text = _migration_text()

    forbidden_patterns = (
        r"\bcreate\s+(?:or\s+replace\s+)?function\b",
        r"\btrigger\b",
        r"\brow\s+level\s+security\b",
        r"\benable\s+row\s+level\s+security\b",
        r"\bpolicy\b",
        r"\bforeign\s+key\b",
        r"\breferences\b",
        r"\bsqlite\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, text), pattern


def test_history_gate_migration_stays_paper_only_without_live_account_surfaces() -> None:
    text = _migration_text()
    forbidden_live_phrase = r"\b" + "live" + r"\s+" + "trading" + r"\b"
    forbidden_account_surface_a = "au" + "th"
    forbidden_account_surface_b = "wal" + "let"
    forbidden_secret_pattern = r"\b" + "private" + r"[_ -]?" + "key" + r"\b"
    forbidden_trade_surface = "or" + "der"

    forbidden_patterns = (
        forbidden_live_phrase,
        rf"\b{forbidden_account_surface_a}\b",
        rf"\b{forbidden_account_surface_b}\b",
        forbidden_secret_pattern,
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, text), pattern
    assert forbidden_trade_surface not in text

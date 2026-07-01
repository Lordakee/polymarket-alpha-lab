from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
EXPECTED_MIGRATION_NAME = (
    "20260630000103_paper_autonomous_screening_gate_transition_trend_reports.sql"
)
DEFAULT_TABLE = "paper_autonomous_screening_gate_transition_trend_reports"


def _migration_path() -> Path:
    candidates = sorted(
        MIGRATIONS_DIR.glob("*paper_autonomous_screening_gate_transition_trend_reports.sql"),
    )
    assert candidates, "paper autonomous screening gate transition trend migration is missing"
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
    return _without_space_after_open_paren(_compact(sql))


def _table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_autonomous_screening_gate_transition_trend_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{DEFAULT_TABLE}"
    return _compact(match.group(1))


def test_trend_migration_uses_requested_version_and_unique_sequence() -> None:
    path = _migration_path()
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))
    names = [migration_path.name for migration_path in migration_paths]
    versions = [name.split("_", 1)[0] for name in names]

    assert path.name == EXPECTED_MIGRATION_NAME
    assert Counter(versions)[EXPECTED_MIGRATION_NAME.split("_", 1)[0]] == 1


def test_trend_migration_creates_report_table_with_contract_columns() -> None:
    body = _table_body(_migration_text())
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_store import (
        _SELECT_COLUMNS,
    )

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "transition_report_count integer not null",
        "first_transition_generated_at timestamptz",
        "latest_transition_generated_at timestamptz",
        "latest_from_gate_status text",
        "latest_to_gate_status text",
        "latest_introduced_reason_code_count integer not null",
        "latest_cleared_reason_code_count integer not null",
        "latest_persistent_reason_code_count integer not null",
        "latest_transition_count integer not null",
        "latest_instability_ratio numeric(18, 6)",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body

    table_columns = {
        stripped.removesuffix(",").split()[0]
        for line in _migration_text().splitlines()
        if (stripped := line.strip())
        and not stripped.startswith("check ")
        and not stripped.startswith("create ")
        and not stripped.startswith("on ")
        and not stripped.startswith("(")
    }
    assert {*_SELECT_COLUMNS, "inserted_at"} <= table_columns


def test_trend_migration_constrains_status_json_counts_decimals_and_flags() -> None:
    body = _without_space_after_open_paren(_table_body(_migration_text()))

    for expected_check in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (latest_from_gate_status is null or latest_from_gate_status in ('pass', 'watch', 'blocked'))",
        "check (latest_to_gate_status is null or latest_to_gate_status in ('pass', 'watch', 'blocked'))",
        "check (transition_report_count >= 0)",
        "check (latest_introduced_reason_code_count >= 0)",
        "check (latest_cleared_reason_code_count >= 0)",
        "check (latest_persistent_reason_code_count >= 0)",
        "check (latest_transition_count >= 0)",
        "check (latest_instability_ratio is null or (latest_instability_ratio >= 0 and latest_instability_ratio <= 1))",
        "check (payload_json is not null and jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body


def test_trend_migration_enforces_json_payload_consistency() -> None:
    body = _table_body(_migration_text())

    for expected_check in (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (((payload_json -> 'transition_report_count') = to_jsonb(transition_report_count)) is true)",
        "check (((payload_json -> 'latest_introduced_reason_code_count') = to_jsonb(latest_introduced_reason_code_count)) is true)",
        "check (((payload_json -> 'latest_cleared_reason_code_count') = to_jsonb(latest_cleared_reason_code_count)) is true)",
        "check (((payload_json -> 'latest_persistent_reason_code_count') = to_jsonb(latest_persistent_reason_code_count)) is true)",
        "check (((payload_json -> 'latest_transition_count') = to_jsonb(latest_transition_count)) is true)",
        "check (payload_json ? 'latest_instability_ratio' and ((latest_instability_ratio is null and payload_json -> 'latest_instability_ratio' = 'null'::jsonb) or (latest_instability_ratio is not null and jsonb_typeof(payload_json -> 'latest_instability_ratio') = 'string' and (payload_json ->> 'latest_instability_ratio')::numeric(18, 6) = latest_instability_ratio)))",
        "check (payload_json ->> 'latest_instability_ratio' is null or payload_json ->> 'latest_instability_ratio' ~ '^(0|1)[.][0-9]{6}$')",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)",
    ):
        assert expected_check in body


def test_trend_migration_enforces_nullable_timestamp_and_status_consistency() -> None:
    body = _table_body(_migration_text())

    for expected_check in (
        "check (payload_json ? 'first_transition_generated_at' and ((first_transition_generated_at is null and payload_json -> 'first_transition_generated_at' = 'null'::jsonb) or (first_transition_generated_at is not null and jsonb_typeof(payload_json -> 'first_transition_generated_at') = 'string' and (payload_json ->> 'first_transition_generated_at')::timestamptz = first_transition_generated_at)))",
        "check (payload_json ? 'latest_transition_generated_at' and ((latest_transition_generated_at is null and payload_json -> 'latest_transition_generated_at' = 'null'::jsonb) or (latest_transition_generated_at is not null and jsonb_typeof(payload_json -> 'latest_transition_generated_at') = 'string' and (payload_json ->> 'latest_transition_generated_at')::timestamptz = latest_transition_generated_at)))",
        "check (payload_json ? 'latest_from_gate_status' and ((latest_from_gate_status is null and payload_json -> 'latest_from_gate_status' = 'null'::jsonb) or (latest_from_gate_status is not null and jsonb_typeof(payload_json -> 'latest_from_gate_status') = 'string' and payload_json ->> 'latest_from_gate_status' = latest_from_gate_status)))",
        "check (payload_json ? 'latest_to_gate_status' and ((latest_to_gate_status is null and payload_json -> 'latest_to_gate_status' = 'null'::jsonb) or (latest_to_gate_status is not null and jsonb_typeof(payload_json -> 'latest_to_gate_status') = 'string' and payload_json ->> 'latest_to_gate_status' = latest_to_gate_status)))",
    ):
        assert expected_check in body


def test_trend_migration_adds_expected_lookup_indexes() -> None:
    sql = _compact_index_sql(_migration_text())

    for index in (
        "create index if not exists pasgttr_generated_at_idx on public.paper_autonomous_screening_gate_transition_trend_reports (generated_at desc);",
        "create index if not exists pasgttr_config_generated_at_idx on public.paper_autonomous_screening_gate_transition_trend_reports (config_version, generated_at desc);",
        "create index if not exists pasgttr_latest_from_idx on public.paper_autonomous_screening_gate_transition_trend_reports (latest_from_gate_status, generated_at desc);",
        "create index if not exists pasgttr_latest_to_idx on public.paper_autonomous_screening_gate_transition_trend_reports (latest_to_gate_status, generated_at desc);",
        "create index if not exists pasgttr_payload_json_idx on public.paper_autonomous_screening_gate_transition_trend_reports using gin (payload_json jsonb_path_ops);",
        "create index if not exists pasgttr_load_sort_idx on public.paper_autonomous_screening_gate_transition_trend_reports (generated_at desc, inserted_at desc, report_sha256 desc);",
    ):
        assert index in sql


def test_trend_migration_keeps_table_and_index_names_under_postgres_limit() -> None:
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


def test_trend_migration_uses_jsonb_payload_without_float_columns() -> None:
    body = _table_body(_migration_text())

    assert "payload_json jsonb" in body
    assert "latest_instability_ratio numeric(18, 6)" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_trend_migration_avoids_forbidden_database_surfaces() -> None:
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
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, text), pattern

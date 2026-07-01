from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
EXPECTED_MIGRATION_NAME = (
    "20260630000104_paper_autonomous_proposal_risk_gate_reports.sql"
)
DEFAULT_TABLE = "paper_autonomous_proposal_risk_gate_reports"


def _migration_path() -> Path:
    candidates = sorted(
        MIGRATIONS_DIR.glob("*paper_autonomous_proposal_risk_gate_reports.sql"),
    )
    assert candidates, "paper autonomous proposal risk gate migration is missing"
    assert len(candidates) == 1
    return candidates[0]


def _migration_text() -> str:
    return _migration_path().read_text(encoding="utf-8")


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
        r"public\.paper_autonomous_proposal_risk_gate_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{DEFAULT_TABLE}"
    return _compact(match.group(1))


def test_migration_uses_requested_safe_version_and_unique_sequence() -> None:
    path = _migration_path()
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))
    names = [migration_path.name for migration_path in migration_paths]
    versions = [name.split("_", 1)[0] for name in names]

    assert path.name == EXPECTED_MIGRATION_NAME
    assert Counter(versions)[EXPECTED_MIGRATION_NAME.split("_", 1)[0]] == 1


def test_migration_creates_report_table_matching_store_columns() -> None:
    sql = _migration_text().lower()
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        _SELECT_COLUMNS,
    )

    assert (
        "create table if not exists "
        "public.paper_autonomous_proposal_risk_gate_reports"
    ) in sql
    table_body = sql.split(
        "create table if not exists "
        "public.paper_autonomous_proposal_risk_gate_reports (",
        1,
    )[1].split("\n);", 1)[0]
    migration_columns = {
        stripped.removesuffix(",").split()[0]
        for line in table_body.splitlines()
        if (stripped := line.strip()) and not stripped.startswith("check ")
    }
    assert migration_columns == {*_SELECT_COLUMNS, "inserted_at"}


def test_migration_creates_report_table_with_required_column_types() -> None:
    body = _table_body(_migration_text())

    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "gate_status text not null",
        "recommended_next_step text not null",
        "source_proposal_status text not null",
        "source_proposal_count integer not null",
        "source_proposal_total_notional numeric(38, 6) not null",
        "blocked_reason_codes_json jsonb not null",
        "watch_reason_codes_json jsonb not null",
        "reason_codes_json jsonb not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body


def test_migration_constrains_status_next_step_json_types_and_flags() -> None:
    body = _without_space_after_open_paren(_table_body(_migration_text()))

    for expected_check in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (gate_status in ('pass', 'watch', 'blocked'))",
        (
            "check (source_proposal_status in "
            "('candidate', 'blocked', 'watch', 'retired'))"
        ),
        (
            "check (recommended_next_step = case gate_status "
            "when 'pass' then 'allow_paper_proposal_to_paper_broker' "
            "when 'watch' then 'hold_paper_proposal_for_risk_review' "
            "when 'blocked' then 'block_paper_proposal_pending_risk_repair' "
            "end)"
        ),
        "check (jsonb_typeof(blocked_reason_codes_json) = 'array')",
        "check (jsonb_typeof(watch_reason_codes_json) = 'array')",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)",
    ):
        assert expected_check in body


def test_migration_enforces_nonnegative_source_counts_and_notional_values() -> None:
    body = _table_body(_migration_text())

    for expected_check in (
        "check (source_proposal_count >= 0)",
        "check (source_proposal_total_notional >= 0)",
    ):
        assert expected_check in body


def test_migration_enforces_payload_scalar_and_reason_array_parity() -> None:
    body = _table_body(_migration_text())

    for expected_check in (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (payload_json ? 'gate_status' and jsonb_typeof(payload_json -> 'gate_status') = 'string' and payload_json ->> 'gate_status' = gate_status)",
        "check (payload_json ? 'recommended_next_step' and jsonb_typeof(payload_json -> 'recommended_next_step') = 'string' and payload_json ->> 'recommended_next_step' = recommended_next_step)",
        "check (payload_json ? 'source_proposal_status' and jsonb_typeof(payload_json -> 'source_proposal_status') = 'string' and payload_json ->> 'source_proposal_status' = source_proposal_status)",
        "check (payload_json ? 'source_proposal_count' and jsonb_typeof(payload_json -> 'source_proposal_count') = 'number' and (payload_json ->> 'source_proposal_count')::integer = source_proposal_count)",
        "check (payload_json ? 'source_proposal_total_notional' and jsonb_typeof(payload_json -> 'source_proposal_total_notional') = 'string' and (payload_json ->> 'source_proposal_total_notional')::numeric = source_proposal_total_notional)",
        "check (payload_json ? 'blocked_reason_codes' and jsonb_typeof(payload_json -> 'blocked_reason_codes') = 'array' and payload_json -> 'blocked_reason_codes' = blocked_reason_codes_json)",
        "check (payload_json ? 'watch_reason_codes' and jsonb_typeof(payload_json -> 'watch_reason_codes') = 'array' and payload_json -> 'watch_reason_codes' = watch_reason_codes_json)",
        "check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and payload_json -> 'reason_codes' = reason_codes_json)",
    ):
        assert expected_check in body


def test_migration_enforces_canonical_scalar_payload_values() -> None:
    body = _table_body(_migration_text())

    assert (
        "check (config_version <> '' and config_version !~ "
        "'^[[:space:]]|[[:space:]]$')"
    ) in body
    assert (
        "check (payload_json ->> 'source_proposal_total_notional' ~ "
        "'^(0|[1-9][0-9]*)[.][0-9]{6}$')"
    ) in body


def test_migration_enforces_reason_code_arrays_as_strings() -> None:
    body = _table_body(_migration_text())

    for jsonb_column in (
        "blocked_reason_codes_json",
        "watch_reason_codes_json",
        "reason_codes_json",
    ):
        assert (
            f"check (not jsonb_path_exists({jsonb_column}, "
            "'$[*] ? (@.type() != \"string\")'))"
        ) in body


def test_migration_enforces_gate_status_reason_code_consistency() -> None:
    body = _table_body(_migration_text())

    for expected_check in (
        "check (gate_status <> 'blocked' or jsonb_array_length(blocked_reason_codes_json) > 0)",
        "check (gate_status <> 'pass' or jsonb_array_length(blocked_reason_codes_json) = 0)",
        "check (gate_status <> 'pass' or jsonb_array_length(watch_reason_codes_json) = 0)",
        "check (gate_status <> 'watch' or jsonb_array_length(blocked_reason_codes_json) = 0)",
    ):
        assert expected_check in body


def test_migration_uses_numeric_safe_json_payloads_without_float_columns() -> None:
    body = _table_body(_migration_text())

    for jsonb_column in (
        "blocked_reason_codes_json",
        "watch_reason_codes_json",
        "reason_codes_json",
        "payload_json",
    ):
        assert f"{jsonb_column} jsonb" in body

    assert "source_proposal_total_notional numeric(38, 6)" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_lookup_and_json_indexes() -> None:
    sql = _compact_index_sql(_migration_text())

    for index in (
        "create index if not exists idx_paprg_generated_at on public.paper_autonomous_proposal_risk_gate_reports (generated_at desc);",
        "create index if not exists idx_paprg_gate_status_generated on public.paper_autonomous_proposal_risk_gate_reports (gate_status, generated_at desc);",
        "create index if not exists idx_paprg_source_status_generated on public.paper_autonomous_proposal_risk_gate_reports (source_proposal_status, generated_at desc);",
        "create index if not exists idx_paprg_config_generated on public.paper_autonomous_proposal_risk_gate_reports (config_version, generated_at desc);",
        "create index if not exists idx_paprg_reason_codes_json on public.paper_autonomous_proposal_risk_gate_reports using gin (reason_codes_json);",
        "create index if not exists idx_paprg_payload_json on public.paper_autonomous_proposal_risk_gate_reports using gin (payload_json);",
        "create index if not exists idx_paprg_load_sort on public.paper_autonomous_proposal_risk_gate_reports (generated_at desc, inserted_at desc, report_sha256 desc);",
    ):
        assert index in sql


def test_migration_keeps_table_and_index_names_under_postgres_limit() -> None:
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


def test_migration_avoids_nonlocal_db_and_live_account_mutation_surfaces() -> None:
    text = _migration_text().lower()

    forbidden_patterns = (
        r"\bcreate\s+(?:or\s+replace\s+)?function\b",
        r"\btrigger\b",
        r"\brow\s+level\s+security\b",
        r"\benable\s+row\s+level\s+security\b",
        r"\bpolicy\b",
        r"\bforeign\s+key\b",
        r"\breferences\b",
        r"\bsqlite\b",
        r"\bredis\b",
        r"\bmongo\b",
        r"\bsqlalchemy\b",
        r"\bhosted\s+db\b",
        r"\bexternal\s+db\b",
        r"\bjsonl\b",
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
        r"\border\s+mutation\b",
        r"\border\s+submission\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, text), pattern

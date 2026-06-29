from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
EXPECTED_MIGRATION_NAME = (
    "20260625000007_paper_autonomous_readiness_gate_reports.sql"
)
PREVIOUS_MIGRATION_NAME = "20260625000006_probability_selection_summary_history_reports.sql"
NEW_MIGRATION = (
    MIGRATIONS_DIR
    / "20260629000002_paper_autonomous_readiness_gate_strategy_cycle_source.sql"
)
DEFAULT_TABLE = "paper_autonomous_readiness_gate_reports"


def _migration_path() -> Path:
    candidates = sorted(
        MIGRATIONS_DIR.glob("*paper_autonomous_readiness_gate_reports.sql"),
    )
    assert candidates, "paper autonomous readiness gate migration is missing"
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
        r"public\.paper_autonomous_readiness_gate_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{DEFAULT_TABLE}"
    return _compact(match.group(1))


def test_readiness_gate_migration_uses_next_safe_version_and_unique_sequence() -> None:
    path = _migration_path()
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))
    names = [migration_path.name for migration_path in migration_paths]
    versions = [name.split("_", 1)[0] for name in names]

    assert path.name == EXPECTED_MIGRATION_NAME
    assert PREVIOUS_MIGRATION_NAME in names
    assert names[names.index(PREVIOUS_MIGRATION_NAME) + 1] == EXPECTED_MIGRATION_NAME
    assert Counter(versions)[EXPECTED_MIGRATION_NAME.split("_", 1)[0]] == 1


def test_readiness_gate_strategy_cycle_source_migration_uses_expected_sequence() -> None:
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))
    versions = [migration_path.name.split("_", 1)[0] for migration_path in migration_paths]

    assert NEW_MIGRATION.exists()
    assert NEW_MIGRATION.name.startswith("20260629000002_")
    assert Counter(versions)["20260629000002"] == 1


def test_readiness_gate_strategy_cycle_source_migration_relaxes_source_lengths() -> None:
    sql = NEW_MIGRATION.read_text(encoding="utf-8").lower()
    assert "jsonb_array_length(source_statuses_json) in (3, 4)" in sql
    assert "jsonb_array_length(source_config_versions_json) in (3, 4)" in sql


def test_readiness_gate_strategy_cycle_source_migration_adds_four_source_sort_index() -> None:
    sql = " ".join(NEW_MIGRATION.read_text(encoding="utf-8").lower().split())
    assert "source_statuses_json #>> '{3,status}'" in sql
    assert "pargr_four_source_status_sort_idx" in sql


def test_readiness_gate_strategy_cycle_source_migration_avoids_forbidden_surfaces() -> None:
    text = NEW_MIGRATION.read_text(encoding="utf-8").lower()
    forbidden_patterns = (
        r"\bsqlite\b",
        r"\bredis\b",
        r"\bmongo\b",
        r"\bsqlalchemy\b",
        r"\bhosted\s+db\b",
        r"\bauth\b",
        r"\bwallet\b",
        r"\bprivate\s+keys?\b",
        r"\border\s+signing\b",
        r"\border\s+submission\b",
        r"\blive\s+trading\b",
    )

    for pattern in forbidden_patterns:
        assert not re.search(pattern, text), pattern


def test_readiness_gate_migration_creates_report_table_with_contract_columns() -> None:
    body = _table_body(_migration_text())

    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "readiness_status text not null",
        "recommended_next_step text not null",
        "source_statuses_json jsonb not null",
        "source_config_versions_json jsonb not null",
        "reason_code_counts_json jsonb not null",
        "reason_codes_json jsonb not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body


def test_readiness_gate_migration_constrains_status_next_step_json_and_flags() -> None:
    body = _without_space_after_open_paren(_table_body(_migration_text()))

    for expected_check in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (readiness_status in ('pass', 'watch', 'blocked'))",
        "check (recommended_next_step = case readiness_status when 'pass' then 'allow_paper_autonomous_readiness_review' when 'watch' then 'throttle_paper_autonomous_readiness_review' when 'blocked' then 'block_paper_autonomous_readiness_review' end)",
        "check (jsonb_typeof(source_statuses_json) = 'array')",
        "check (jsonb_typeof(source_config_versions_json) = 'array')",
        "check (jsonb_typeof(reason_code_counts_json) = 'array')",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (jsonb_array_length(source_statuses_json) = 3)",
        "check (jsonb_array_length(source_config_versions_json) = 3)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body


def test_readiness_gate_migration_enforces_json_payload_consistency() -> None:
    body = _table_body(_migration_text())

    for expected_check in (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (payload_json ? 'readiness_status' and jsonb_typeof(payload_json -> 'readiness_status') = 'string' and payload_json ->> 'readiness_status' = readiness_status)",
        "check (payload_json ? 'recommended_next_step' and jsonb_typeof(payload_json -> 'recommended_next_step') = 'string' and payload_json ->> 'recommended_next_step' = recommended_next_step)",
        "check (payload_json ? 'source_statuses' and jsonb_typeof(payload_json -> 'source_statuses') = 'array' and source_statuses_json = payload_json -> 'source_statuses')",
        "check (payload_json ? 'source_config_versions' and jsonb_typeof(payload_json -> 'source_config_versions') = 'array' and source_config_versions_json = payload_json -> 'source_config_versions')",
        "check (payload_json ? 'reason_code_counts' and jsonb_typeof(payload_json -> 'reason_code_counts') = 'array' and reason_code_counts_json = payload_json -> 'reason_code_counts')",
        "check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and reason_codes_json = payload_json -> 'reason_codes')",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)",
    ):
        assert expected_check in body


def test_readiness_gate_migration_uses_jsonb_payloads_without_float_columns() -> None:
    body = _table_body(_migration_text())

    for jsonb_column in (
        "source_statuses_json",
        "source_config_versions_json",
        "reason_code_counts_json",
        "reason_codes_json",
        "payload_json",
    ):
        assert f"{jsonb_column} jsonb" in body

    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_readiness_gate_migration_adds_expected_lookup_indexes() -> None:
    sql = _compact_index_sql(_migration_text())

    for index in (
        "create index if not exists paper_autonomous_readiness_gate_generated_at_idx on public.paper_autonomous_readiness_gate_reports (generated_at desc);",
        "create index if not exists paper_autonomous_readiness_gate_status_generated_at_idx on public.paper_autonomous_readiness_gate_reports (readiness_status, generated_at desc);",
        "create index if not exists paper_autonomous_readiness_gate_config_generated_at_idx on public.paper_autonomous_readiness_gate_reports (config_version, generated_at desc);",
        "create index if not exists paper_autonomous_readiness_gate_source_statuses_idx on public.paper_autonomous_readiness_gate_reports using gin (source_statuses_json jsonb_path_ops);",
        "create index if not exists pargr_source_status_sort_idx on public.paper_autonomous_readiness_gate_reports ((source_statuses_json #>> '{0,status}'), (source_statuses_json #>> '{1,status}'), (source_statuses_json #>> '{2,status}'), generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists paper_autonomous_readiness_gate_status_sort_idx on public.paper_autonomous_readiness_gate_reports (readiness_status, generated_at desc, inserted_at desc, report_sha256 desc);",
    ):
        assert index in sql


def test_readiness_gate_migration_keeps_table_and_index_names_under_postgres_limit() -> None:
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


def test_readiness_gate_migration_avoids_forbidden_database_surfaces() -> None:
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


def test_readiness_gate_migration_stays_paper_only_without_live_account_surfaces() -> None:
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

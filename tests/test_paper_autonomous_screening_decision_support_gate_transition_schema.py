from __future__ import annotations

from collections import Counter
from dataclasses import FrozenInstanceError
from pathlib import Path
import re

import pytest


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
EXPECTED_MIGRATION_NAME = (
    "20260625000009_paper_autonomous_screening_gate_transition_reports.sql"
)
DEFAULT_TABLE = "paper_autonomous_screening_gate_transition_reports"
LOCAL_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_GATE_TRANSITION_DB_ENABLED"
)
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_GATE_TRANSITION_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_GATE_TRANSITION_DB_TABLE"


def _migration_path() -> Path:
    path = MIGRATIONS_DIR / EXPECTED_MIGRATION_NAME
    assert path.exists(), "paper autonomous screening gate transition migration is missing"
    return path


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
        r"public\.paper_autonomous_screening_gate_transition_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{DEFAULT_TABLE}"
    return _compact(match.group(1))


def _config_module():
    import polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_transition_config as config_module

    return config_module


def test_transition_migration_uses_requested_version_and_unique_sequence() -> None:
    path = _migration_path()
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))
    names = [migration_path.name for migration_path in migration_paths]
    versions = [name.split("_", 1)[0] for name in names]

    assert path.name == EXPECTED_MIGRATION_NAME
    assert Counter(versions)[EXPECTED_MIGRATION_NAME.split("_", 1)[0]] == 1


def test_transition_migration_creates_report_table_with_contract_columns() -> None:
    body = _table_body(_migration_text())
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        _SELECT_COLUMNS,
    )

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "gate_report_count integer not null",
        "transition_count integer not null",
        "first_report_generated_at timestamptz",
        "latest_report_generated_at timestamptz",
        "latest_from_gate_status text",
        "latest_to_gate_status text",
        "latest_introduced_reason_codes_json jsonb not null default '[]'::jsonb",
        "latest_cleared_reason_codes_json jsonb not null default '[]'::jsonb",
        "latest_persistent_reason_codes_json jsonb not null default '[]'::jsonb",
        "status_transition_rows_json jsonb",
        "reason_change_rows_json jsonb",
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


def test_transition_migration_constrains_status_json_counts_and_flags() -> None:
    body = _without_space_after_open_paren(_table_body(_migration_text()))

    for expected_check in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (latest_from_gate_status is null or latest_from_gate_status in ('pass', 'watch', 'blocked'))",
        "check (latest_to_gate_status is null or latest_to_gate_status in ('pass', 'watch', 'blocked'))",
        "check (gate_report_count >= 0)",
        "check (transition_count >= 0)",
        "check (transition_count = greatest(gate_report_count - 1, 0))",
        "check (jsonb_typeof(latest_introduced_reason_codes_json) = 'array')",
        "check (jsonb_typeof(latest_cleared_reason_codes_json) = 'array')",
        "check (jsonb_typeof(latest_persistent_reason_codes_json) = 'array')",
        "check (status_transition_rows_json is null or jsonb_typeof(status_transition_rows_json) = 'array')",
        "check (reason_change_rows_json is null or jsonb_typeof(reason_change_rows_json) = 'array')",
        "check (payload_json is not null and jsonb_typeof(payload_json) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body


def test_transition_migration_enforces_json_payload_consistency() -> None:
    body = _table_body(_migration_text())

    for expected_check in (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (((payload_json -> 'gate_report_count') = to_jsonb(gate_report_count)) is true)",
        "check (((payload_json -> 'transition_count') = to_jsonb(transition_count)) is true)",
        "check (latest_introduced_reason_codes_json = payload_json -> 'latest_introduced_reason_codes')",
        "check (latest_cleared_reason_codes_json = payload_json -> 'latest_cleared_reason_codes')",
        "check (latest_persistent_reason_codes_json = payload_json -> 'latest_persistent_reason_codes')",
        "check ((status_transition_rows_json is null and payload_json -> 'status_transition_rows' = 'null'::jsonb) or (status_transition_rows_json is not null and status_transition_rows_json = payload_json -> 'status_transition_rows'))",
        "check ((reason_change_rows_json is null and payload_json -> 'reason_change_rows' = 'null'::jsonb) or (reason_change_rows_json is not null and reason_change_rows_json = payload_json -> 'reason_change_rows'))",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)",
    ):
        assert expected_check in body


def test_transition_migration_adds_expected_lookup_indexes() -> None:
    sql = _compact_index_sql(_migration_text())

    for index in (
        "create index if not exists pasgtr_generated_at_idx on public.paper_autonomous_screening_gate_transition_reports (generated_at desc);",
        "create index if not exists pasgtr_config_generated_at_idx on public.paper_autonomous_screening_gate_transition_reports (config_version, generated_at desc);",
        "create index if not exists pasgtr_latest_from_idx on public.paper_autonomous_screening_gate_transition_reports (latest_from_gate_status, generated_at desc);",
        "create index if not exists pasgtr_latest_to_idx on public.paper_autonomous_screening_gate_transition_reports (latest_to_gate_status, generated_at desc);",
        "create index if not exists pasgtr_status_sort_idx on public.paper_autonomous_screening_gate_transition_reports (latest_from_gate_status, latest_to_gate_status, generated_at desc, inserted_at desc, report_sha256 desc);",
    ):
        assert index in sql


def test_transition_migration_keeps_table_and_index_names_under_postgres_limit() -> None:
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


def test_transition_migration_avoids_forbidden_database_surfaces() -> None:
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


def test_transition_config_public_constants_match_expected_env_surface() -> None:
    config_module = _config_module()
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_REPORTS_TABLE,
    )

    assert (
        config_module.PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_DB_ENABLED_ENV_VAR
        == ENABLED_ENV_VAR
    )
    assert (
        config_module.PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_DB_DSN_ENV_VAR
        == DSN_ENV_VAR
    )
    assert (
        config_module.PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_DB_TABLE_ENV_VAR
        == TABLE_ENV_VAR
    )
    assert (
        config_module.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_DB_TABLE
        == DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_REPORTS_TABLE
        == DEFAULT_TABLE
    )


def test_transition_config_disabled_env_accepts_missing_dsn() -> None:
    config_module = _config_module()

    config = (
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_db_env(
            {},
        )
    )

    assert config == (
        config_module.SupabasePaperAutonomousScreeningDecisionSupportGateTransitionConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_TABLE,
        )
    )


def test_transition_config_enabled_env_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: " ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message


def test_transition_config_reads_explicit_dsn_at_process_edge() -> None:
    config_module = _config_module()
    dsn = LOCAL_DSN

    config = (
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_db_env(
            {
                ENABLED_ENV_VAR: "1",
                DSN_ENV_VAR: dsn,
                TABLE_ENV_VAR: "paper_autonomous_screening_gate_transition_archive",
            },
        )
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_autonomous_screening_gate_transition_archive"


def test_transition_config_rejects_remote_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://worker:sensitive-token@db.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_db_env(
            {
                ENABLED_ENV_VAR: "false",
                DSN_ENV_VAR: secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message
    assert "secret" not in message.lower()


@pytest.mark.parametrize(
    ("enabled_value", "expected_enabled"),
    [
        ("", False),
        ("0", False),
        ("false", False),
        (" FALSE ", False),
        ("1", True),
        ("true", True),
        (" TRUE ", True),
    ],
)
def test_transition_config_accepts_only_strict_enabled_values(
    enabled_value: str,
    expected_enabled: bool,
) -> None:
    config_module = _config_module()

    config = (
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: LOCAL_DSN,
            },
        )
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", ["yes", "on", "2"])
def test_transition_config_rejects_non_strict_enabled_values(
    enabled_value: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
        config_module.from_paper_autonomous_screening_decision_support_gate_transition_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: LOCAL_DSN,
            },
        )


def test_transition_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabasePaperAutonomousScreeningDecisionSupportGateTransitionConfig(
        enabled=True,
        dsn="postgresql://postgres:sensitive-token@localhost:54322/postgres",
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered
    assert DEFAULT_TABLE in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperReports",
        "paper-reports",
        "paper.reports",
        "_paper_reports",
        "paper_reports_",
        "a",
        "",
    ],
)
def test_transition_config_table_name_must_be_simple_lowercase_identifier(
    table_name: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        config_module.SupabasePaperAutonomousScreeningDecisionSupportGateTransitionConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


def test_transition_config_public_exports_include_constants_config_and_loader() -> None:
    config_module = _config_module()

    assert config_module.__all__ == (
        "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_DB_TABLE",
        "PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_DB_DSN_ENV_VAR",
        "PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_DB_ENABLED_ENV_VAR",
        "PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_DB_TABLE_ENV_VAR",
        "SupabasePaperAutonomousScreeningDecisionSupportGateTransitionConfig",
        "from_paper_autonomous_screening_decision_support_gate_transition_db_env",
    )

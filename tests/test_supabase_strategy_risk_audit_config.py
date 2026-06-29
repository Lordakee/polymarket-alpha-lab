from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import re

import pytest


MIGRATION_PATH = Path(
    "supabase/migrations/20260620000005_strategy_risk_audit_reports.sql",
)
DOC_PATH = Path("docs/strategy-risk-audit-db-persistence.md")
ENV_EXAMPLE_PATH = Path(".env.example")
ENABLED_ENV_VAR = "POLYMARKET_ALPHA_LAB_STRATEGY_RISK_AUDIT_DB_ENABLED"
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_STRATEGY_RISK_AUDIT_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_STRATEGY_RISK_AUDIT_DB_TABLE"
DEFAULT_TABLE = "strategy_risk_audit_reports"
DOC_ENV_VARS = (
    ENABLED_ENV_VAR,
    DSN_ENV_VAR,
    TABLE_ENV_VAR,
)


def _doc_text() -> str:
    assert DOC_PATH.exists(), f"{DOC_PATH} must exist"
    return DOC_PATH.read_text(encoding="utf-8")


def _env_example_text() -> str:
    assert ENV_EXAMPLE_PATH.exists(), f"{ENV_EXAMPLE_PATH} must exist"
    return ENV_EXAMPLE_PATH.read_text(encoding="utf-8")


def _config_module():
    import polymarket_alpha_lab.supabase_strategy_risk_audit_config as config_module

    return config_module


def _migration_sql() -> str:
    assert MIGRATION_PATH.exists(), f"missing migration: {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8")


def _compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def _table_body(sql: str, table_name: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+public\."
        + re.escape(table_name)
        + r"\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{table_name}"
    return _compact(match.group(1))


def test_disabled_env_config_uses_default_table_and_accepts_absent_dsn() -> None:
    config_module = _config_module()

    config = config_module.from_strategy_risk_audit_db_env({})

    assert config == config_module.SupabaseStrategyRiskAuditConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    unrelated_secret = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_strategy_risk_audit_db_env(
            {
                ENABLED_ENV_VAR: "true",
                "UNRELATED_SECRET": unrelated_secret,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert unrelated_secret not in message
    assert "topsecret" not in message


def test_enabled_env_config_rejects_padded_dsn_without_echoing_it() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_strategy_risk_audit_db_env(
            {
                ENABLED_ENV_VAR: "1",
                DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "topsecret" not in message


@pytest.mark.parametrize(
    ("enabled_value", "expected_enabled"),
    [
        ("", False),
        ("0", False),
        ("false", False),
        ("1", True),
        ("true", True),
    ],
)
def test_enabled_env_config_accepts_only_strict_values(
    enabled_value: str,
    expected_enabled: bool,
) -> None:
    config_module = _config_module()

    config = config_module.from_strategy_risk_audit_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: "postgresql://localhost:54322/postgres",
            },
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize(
    "enabled_value",
    [" TRUE ", "true ", " false", "TRUE", "False", "yes", "on", "2"],
)
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_strategy_risk_audit_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: "postgresql://localhost:54322/postgres",
            },
        )

    assert ENABLED_ENV_VAR in str(exc_info.value)


def test_enabled_env_config_reads_explicit_dsn_and_table_name() -> None:
    config_module = _config_module()
    dsn = "postgresql://localhost:54322/postgres"

    config = config_module.from_strategy_risk_audit_db_env(
        {
            ENABLED_ENV_VAR: "true",
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "audit.strategy_risk_audit_reports",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "audit.strategy_risk_audit_reports"


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabaseStrategyRiskAuditConfig(
        enabled=True,
        dsn="postgresql://topsecret@localhost:54322/postgres",
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=<redacted>" in rendered
    assert DEFAULT_TABLE in rendered


def test_direct_config_rejects_remote_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://topsecret@example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabaseStrategyRiskAuditConfig(
            enabled=False,
            dsn=secret_dsn,
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "topsecret" not in message


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    config_module = _config_module()

    rendered = repr(
        config_module.SupabaseStrategyRiskAuditConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "StrategyRiskAuditReports",
        "strategy-risk-audit-reports",
        "audit.StrategyRiskAuditReports",
        "audit.strategy-risk-audit-reports",
        "_strategy_risk_audit_reports",
        "audit._strategy_risk_audit_reports",
        "strategy_risk_audit_reports_",
        "audit.strategy_risk_audit_reports_",
        "public.audit.strategy_risk_audit_reports",
        ".strategy_risk_audit_reports",
        "audit.",
        "",
    ],
)
def test_table_name_must_be_lowercase_identifier_with_optional_schema(
    table_name: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(
        ValueError,
        match="lowercase identifier with optional schema prefix",
    ):
        config_module.SupabaseStrategyRiskAuditConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


def test_table_name_accepts_optional_schema_and_63_byte_identifier_parts() -> None:
    config_module = _config_module()
    max_length_part = "a" + ("b" * 61) + "1"
    assert len(max_length_part) == 63

    config = config_module.SupabaseStrategyRiskAuditConfig(
        enabled=False,
        dsn=None,
        table_name=f"public.{max_length_part}",
    )

    assert config.table_name == f"public.{max_length_part}"


def test_table_name_rejects_identifier_parts_longer_than_63_bytes() -> None:
    config_module = _config_module()
    too_long_part = "a" + ("b" * 62) + "1"
    assert len(too_long_part) == 64

    with pytest.raises(ValueError, match="63"):
        config_module.SupabaseStrategyRiskAuditConfig(
            enabled=False,
            dsn=None,
            table_name=f"public.{too_long_part}",
        )


def test_env_table_name_error_mentions_variable_name() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_strategy_risk_audit_db_env(
            {TABLE_ENV_VAR: "StrategyRiskAuditReports"},
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        config_module.SupabaseStrategyRiskAuditConfig(
            enabled=1,
            dsn="postgresql://localhost:54322/postgres",
            table_name=DEFAULT_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabaseStrategyRiskAuditConfig(
            enabled=True,
            dsn=object(),
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_include_constants_config_and_loader_in_order() -> None:
    config_module = _config_module()

    assert config_module.__all__ == (
        "STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR",
        "STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR",
        "STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR",
        "DEFAULT_STRATEGY_RISK_AUDIT_DB_TABLE",
        "SupabaseStrategyRiskAuditConfig",
        "from_strategy_risk_audit_db_env",
    )


def test_migration_creates_strategy_risk_audit_report_table() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "status text not null",
        "gate_count integer not null",
        "pass_count integer not null",
        "fail_count integer not null",
        "incomplete_count integer not null",
        "gate_results_json jsonb not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body


def test_migration_enforces_row_scalar_and_payload_invariants() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    for expected_check in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (status in ('audit_ready', 'blocked_by_risk', 'insufficient_evidence'))",
        "check (gate_count >= 0)",
        "check (pass_count >= 0)",
        "check (fail_count >= 0)",
        "check (incomplete_count >= 0)",
        "check (gate_count = pass_count + fail_count + incomplete_count)",
        "check ((fail_count > 0 and status = 'blocked_by_risk') or (fail_count = 0 and incomplete_count > 0 and status = 'insufficient_evidence') or (fail_count = 0 and incomplete_count = 0 and status = 'audit_ready'))",
        "check (jsonb_typeof(gate_results_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body


def test_migration_enforces_payload_scalar_parity() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    for expected_check in (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (payload_json ? 'status' and jsonb_typeof(payload_json -> 'status') = 'string' and payload_json ->> 'status' = status)",
        "check (payload_json ? 'gate_count' and jsonb_typeof(payload_json -> 'gate_count') = 'number' and (payload_json ->> 'gate_count')::integer = gate_count)",
        "check (payload_json ? 'pass_count' and jsonb_typeof(payload_json -> 'pass_count') = 'number' and (payload_json ->> 'pass_count')::integer = pass_count)",
        "check (payload_json ? 'fail_count' and jsonb_typeof(payload_json -> 'fail_count') = 'number' and (payload_json ->> 'fail_count')::integer = fail_count)",
        "check (payload_json ? 'incomplete_count' and jsonb_typeof(payload_json -> 'incomplete_count') = 'number' and (payload_json ->> 'incomplete_count')::integer = incomplete_count)",
        "check (payload_json ? 'gate_results' and jsonb_typeof(payload_json -> 'gate_results') = 'array' and payload_json -> 'gate_results' = gate_results_json)",
    ):
        assert expected_check in body


def test_migration_adds_useful_short_indexes() -> None:
    sql = _compact(_migration_sql())

    for index in (
        "create index if not exists idx_srar_generated_at on "
        "public.strategy_risk_audit_reports (generated_at desc);",
        "create index if not exists idx_srar_status_generated on "
        "public.strategy_risk_audit_reports (status, generated_at desc);",
        "create index if not exists idx_srar_config_generated on "
        "public.strategy_risk_audit_reports (config_version, generated_at desc);",
        "create index if not exists idx_srar_payload_json on "
        "public.strategy_risk_audit_reports using gin (payload_json);",
        "create index if not exists idx_srar_gate_results_json on "
        "public.strategy_risk_audit_reports using gin (gate_results_json);",
    ):
        assert index in sql


def test_migration_keeps_table_and_index_names_under_postgres_limit() -> None:
    sql = _migration_sql()
    names = set(
        re.findall(
            r"create\s+table\s+if\s+not\s+exists\s+public\.([a-z0-9_]+)",
            sql,
            flags=re.IGNORECASE,
        ),
    )
    names.update(
        re.findall(
            r"create\s+(?:unique\s+)?index\s+if\s+not\s+exists\s+([a-z0-9_]+)",
            sql,
            flags=re.IGNORECASE,
        ),
    )

    assert DEFAULT_TABLE in names
    assert names
    assert all(len(name) <= 63 for name in names)


def test_strategy_risk_audit_db_persistence_doc_states_boundary() -> None:
    text = _doc_text().lower()

    for heading in (
        "# strategy risk audit db persistence",
        "## environment",
        "## table",
        "## scope boundary",
    ):
        assert heading in text
    for required in (
        "optional supabase/postgres persistence-only surface",
        "paperstrategyriskauditreport",
        "default-off",
        "env-driven",
        "no dsn cli flags",
        "strategy_risk_audit_reports",
        "payload_json",
        "canonical report payload",
        "read-only",
        "paper_only",
        "report_only",
        "readonly",
        "no live trading",
        "no auth",
        "no wallet access",
        "no private keys",
        "no account reads",
        "no order construction",
        "no signing",
        "no order submission",
        "no cancellation",
        "no replacement",
        "no exchange mutation",
    ):
        assert required in text
    for env_var in DOC_ENV_VARS:
        assert env_var.lower() in text


def test_env_example_contains_blank_strategy_risk_audit_db_vars() -> None:
    lines = set(_env_example_text().splitlines())

    for env_var in DOC_ENV_VARS:
        assert f"{env_var}=" in lines

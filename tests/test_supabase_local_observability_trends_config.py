from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import re

import pytest


ENV_EXAMPLE_PATH = Path(".env.example")
MIGRATION_PATH = Path(
    "supabase/migrations/20260620000004_local_observability_trends_reports.sql",
)

ENABLED_ENV_VAR = "POLYMARKET_ALPHA_LAB_LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED"
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_LOCAL_OBSERVABILITY_TRENDS_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_LOCAL_OBSERVABILITY_TRENDS_DB_TABLE"
DEFAULT_TABLE = "local_observability_trends_reports"


def _config_module():
    import polymarket_alpha_lab.supabase_local_observability_trends_config as config_module

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

    config = config_module.from_local_observability_trends_db_env({})

    assert config == config_module.SupabaseLocalObservabilityTrendsConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    unrelated_secret = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_local_observability_trends_db_env(
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
        config_module.from_local_observability_trends_db_env(
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

    config = config_module.from_local_observability_trends_db_env(
        {
            ENABLED_ENV_VAR: enabled_value,
            DSN_ENV_VAR: "postgresql://example.invalid/postgres",
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
        config_module.from_local_observability_trends_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: "postgresql://example.invalid/postgres",
            },
        )

    assert ENABLED_ENV_VAR in str(exc_info.value)


def test_enabled_env_config_reads_explicit_dsn_and_table_name() -> None:
    config_module = _config_module()
    dsn = "postgresql://example.invalid/postgres"

    config = config_module.from_local_observability_trends_db_env(
        {
            ENABLED_ENV_VAR: "true",
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "audit.local_observability_trends_reports",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "audit.local_observability_trends_reports"


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabaseLocalObservabilityTrendsConfig(
        enabled=True,
        dsn="postgresql://topsecret.example.invalid/postgres",
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=<redacted>" in rendered
    assert DEFAULT_TABLE in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    config_module = _config_module()

    rendered = repr(
        config_module.SupabaseLocalObservabilityTrendsConfig(
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
        "LocalObservabilityTrendsReports",
        "local-observability-trends-reports",
        "audit.LocalObservabilityTrendsReports",
        "audit.local-observability-trends-reports",
        "_local_observability_trends_reports",
        "audit._local_observability_trends_reports",
        "local_observability_trends_reports_",
        "audit.local_observability_trends_reports_",
        "public.audit.local_observability_trends_reports",
        ".local_observability_trends_reports",
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
        config_module.SupabaseLocalObservabilityTrendsConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


def test_table_name_accepts_optional_schema_and_63_byte_identifier_parts() -> None:
    config_module = _config_module()
    max_length_part = "a" + ("b" * 61) + "1"
    assert len(max_length_part) == 63

    config = config_module.SupabaseLocalObservabilityTrendsConfig(
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
        config_module.SupabaseLocalObservabilityTrendsConfig(
            enabled=False,
            dsn=None,
            table_name=f"public.{too_long_part}",
        )


def test_env_table_name_error_mentions_variable_name() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_local_observability_trends_db_env(
            {TABLE_ENV_VAR: "LocalObservabilityTrendsReports"},
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        config_module.SupabaseLocalObservabilityTrendsConfig(
            enabled=1,
            dsn="postgresql://example.invalid/postgres",
            table_name=DEFAULT_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabaseLocalObservabilityTrendsConfig(
            enabled=True,
            dsn=object(),
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_env_example_contains_blank_local_observability_trends_db_vars() -> None:
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    expected_lines = [
        f"{ENABLED_ENV_VAR}=",
        f"{DSN_ENV_VAR}=",
        f"{TABLE_ENV_VAR}=",
    ]

    for line in expected_lines:
        assert line in lines
    assert "postgresql://" not in text
    assert "POLYMARKET_ALPHA_DATABASE_URL" not in text
    assert "POLYMARKET_ALPHA_DB_SCHEMA" not in text
    assert all(line.endswith("=") for line in lines)


def test_public_exports_include_constants_config_and_loader_in_order() -> None:
    config_module = _config_module()

    assert config_module.__all__ == (
        "LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR",
        "LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR",
        "LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR",
        "DEFAULT_LOCAL_OBSERVABILITY_TRENDS_DB_TABLE",
        "SupabaseLocalObservabilityTrendsConfig",
        "from_local_observability_trends_db_env",
    )


def test_migration_creates_local_observability_trends_report_table() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "strategy_evidence_snapshot_count integer not null",
        "strategy_evidence_latest_status text",
        "outcome_freshness_status text not null",
        "outcome_report_count integer not null",
        "nav_risk_status text not null",
        "nav_risk_report_count integer not null",
        "paper_trade_cost_status text not null",
        "paper_trade_cost_report_count integer not null",
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
        "check (strategy_evidence_snapshot_count >= 0)",
        "check (outcome_report_count >= 0)",
        "check (nav_risk_report_count >= 0)",
        "check (paper_trade_cost_report_count >= 0)",
        "check (strategy_evidence_latest_status is null or strategy_evidence_latest_status in ('no_local_evidence', 'local_evidence_gaps', 'local_risk_flags', 'local_evidence_observed'))",
        "check ((strategy_evidence_snapshot_count = 0 and strategy_evidence_latest_status is null) or (strategy_evidence_snapshot_count > 0 and strategy_evidence_latest_status is not null))",
        "check (outcome_freshness_status in ('empty_outcome_history', 'latest_outcomes_fresh', 'latest_outcomes_pending', 'latest_outcomes_stale'))",
        "check (nav_risk_status in ('empty_nav_risk_history', 'latest_nav_risk_observed', 'latest_nav_has_unexecutable_positions'))",
        "check (paper_trade_cost_status in ('empty_cost_audit_history', 'latest_cost_observed', 'latest_negative_cost_adjusted_edges'))",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (payload_json -> 'paper_only' is null or payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json -> 'report_only' is null or payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json -> 'readonly' is null or payload_json -> 'readonly' = 'true'::jsonb)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body


def test_migration_adds_useful_short_indexes() -> None:
    sql = _compact(_migration_sql())

    for index in (
        "create index if not exists idx_lotr_generated_at on "
        "public.local_observability_trends_reports (generated_at desc);",
        "create index if not exists idx_lotr_config_generated on "
        "public.local_observability_trends_reports "
        "(config_version, generated_at desc);",
        "create index if not exists idx_lotr_strategy_status on "
        "public.local_observability_trends_reports "
        "(strategy_evidence_latest_status, generated_at desc);",
        "create index if not exists idx_lotr_outcome_status on "
        "public.local_observability_trends_reports "
        "(outcome_freshness_status, generated_at desc);",
        "create index if not exists idx_lotr_nav_status on "
        "public.local_observability_trends_reports "
        "(nav_risk_status, generated_at desc);",
        "create index if not exists idx_lotr_cost_status on "
        "public.local_observability_trends_reports "
        "(paper_trade_cost_status, generated_at desc);",
        "create index if not exists idx_lotr_payload_json on "
        "public.local_observability_trends_reports using gin (payload_json);",
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

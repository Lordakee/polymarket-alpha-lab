from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from polymarket_alpha_lab.supabase_team_memory_readiness_digest_config import (
    DEFAULT_TEAM_MEMORY_READINESS_DIGEST_DB_TABLE,
    TEAM_MEMORY_READINESS_DIGEST_DB_DSN_ENV_VAR,
    TEAM_MEMORY_READINESS_DIGEST_DB_ENABLED_ENV_VAR,
    TEAM_MEMORY_READINESS_DIGEST_DB_TABLE_ENV_VAR,
    SupabaseTeamMemoryReadinessDigestConfig,
    from_team_memory_readiness_digest_db_env,
)


LOCAL_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
LOCAL_SECRET_DSN = "postgresql://digest:secret@localhost:54322/postgres"
REMOTE_SECRET_DSN = "postgresql://digest:secret@example.invalid/postgres"


def test_env_var_names_and_default_table_are_exact_contract() -> None:
    assert (
        TEAM_MEMORY_READINESS_DIGEST_DB_ENABLED_ENV_VAR
        == "POLYMARKET_ALPHA_LAB_TEAM_MEMORY_READINESS_DIGEST_DB_ENABLED"
    )
    assert (
        TEAM_MEMORY_READINESS_DIGEST_DB_DSN_ENV_VAR
        == "POLYMARKET_ALPHA_LAB_TEAM_MEMORY_READINESS_DIGEST_DB_DSN"
    )
    assert (
        TEAM_MEMORY_READINESS_DIGEST_DB_TABLE_ENV_VAR
        == "POLYMARKET_ALPHA_LAB_TEAM_MEMORY_READINESS_DIGEST_DB_TABLE"
    )
    assert (
        DEFAULT_TEAM_MEMORY_READINESS_DIGEST_DB_TABLE
        == "team_memory_readiness_digest_reports"
    )


def test_disabled_env_config_accepts_missing_dsn_and_uses_default_table() -> None:
    config = from_team_memory_readiness_digest_db_env({})

    assert config == SupabaseTeamMemoryReadinessDigestConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TEAM_MEMORY_READINESS_DIGEST_DB_TABLE,
    )


def test_enabled_env_config_reads_local_dsn_and_table_at_process_edge() -> None:
    config = from_team_memory_readiness_digest_db_env(
        {
            TEAM_MEMORY_READINESS_DIGEST_DB_ENABLED_ENV_VAR: "1",
            TEAM_MEMORY_READINESS_DIGEST_DB_DSN_ENV_VAR: LOCAL_DSN,
            TEAM_MEMORY_READINESS_DIGEST_DB_TABLE_ENV_VAR: (
                "team_memory_readiness_digest_report_archive"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == LOCAL_DSN
    assert config.table_name == "team_memory_readiness_digest_report_archive"


@pytest.mark.parametrize("enabled_value", [" TRUE", "true ", "True", "FALSE", " false"])
def test_enabled_env_config_rejects_noncanonical_enabled_values(
    enabled_value: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        from_team_memory_readiness_digest_db_env(
            {TEAM_MEMORY_READINESS_DIGEST_DB_ENABLED_ENV_VAR: enabled_value},
        )

    message = str(exc_info.value)
    assert TEAM_MEMORY_READINESS_DIGEST_DB_ENABLED_ENV_VAR in message
    assert repr(enabled_value) not in message


def test_enabled_env_requires_dsn_without_echoing_secrets() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_team_memory_readiness_digest_db_env(
            {
                TEAM_MEMORY_READINESS_DIGEST_DB_ENABLED_ENV_VAR: "true",
                TEAM_MEMORY_READINESS_DIGEST_DB_DSN_ENV_VAR: f" {LOCAL_SECRET_DSN} ",
            },
        )

    message = str(exc_info.value)
    assert TEAM_MEMORY_READINESS_DIGEST_DB_DSN_ENV_VAR in message
    assert LOCAL_SECRET_DSN not in message
    assert "secret" not in message.lower()


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config = SupabaseTeamMemoryReadinessDigestConfig(
        enabled=True,
        dsn=LOCAL_SECRET_DSN,
        table_name=DEFAULT_TEAM_MEMORY_READINESS_DIGEST_DB_TABLE,
    )

    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config, readonly=False)

    rendered = repr(config)
    assert "secret" not in rendered.lower()
    assert LOCAL_SECRET_DSN not in rendered
    assert DEFAULT_TEAM_MEMORY_READINESS_DIGEST_DB_TABLE not in rendered
    assert "dsn=<redacted>" in rendered
    assert "table_name=<redacted-table>" in rendered


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://localhost/postgres",
        "postgres://127.0.0.1:54322/postgres",
        "host=localhost port=54322 dbname=postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
    ],
)
def test_config_accepts_local_postgres_dsn_forms(dsn: str) -> None:
    config = SupabaseTeamMemoryReadinessDigestConfig(
        enabled=True,
        dsn=dsn,
        table_name=DEFAULT_TEAM_MEMORY_READINESS_DIGEST_DB_TABLE,
    )

    assert config.dsn == dsn


@pytest.mark.parametrize(
    "dsn",
    [
        REMOTE_SECRET_DSN,
        "postgres://db.example.com/postgres",
        "postgresql://localhost/postgres?hostaddr=127.0.0.1",
        "host=example.invalid dbname=postgres",
        "sqlite:///tmp/project.db",
    ],
)
def test_config_rejects_remote_or_unsafe_dsn_without_echoing_secret(dsn: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        SupabaseTeamMemoryReadinessDigestConfig(
            enabled=False,
            dsn=dsn,
            table_name=DEFAULT_TEAM_MEMORY_READINESS_DIGEST_DB_TABLE,
        )

    message = str(exc_info.value)
    assert TEAM_MEMORY_READINESS_DIGEST_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "secret" not in message.lower()
    assert "example.invalid" not in message


@pytest.mark.parametrize(
    "table_name",
    [
        "TeamMemoryReadinessDigestReports",
        "team-memory-readiness-digest-reports",
        "public.team_memory_readiness_digest_reports",
        "_team_memory_readiness_digest_reports",
        "team_memory_readiness_digest_reports_",
        "a" * 64,
        "",
    ],
)
def test_table_name_must_be_simple_lowercase_identifier(table_name: str) -> None:
    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        SupabaseTeamMemoryReadinessDigestConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


def test_env_table_name_error_mentions_variable_name() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_team_memory_readiness_digest_db_env(
            {
                TEAM_MEMORY_READINESS_DIGEST_DB_TABLE_ENV_VAR: (
                    "TeamMemoryReadinessDigestReports"
                ),
            },
        )

    assert TEAM_MEMORY_READINESS_DIGEST_DB_TABLE_ENV_VAR in str(exc_info.value)


def test_enabled_flag_is_strict() -> None:
    with pytest.raises(ValueError, match=TEAM_MEMORY_READINESS_DIGEST_DB_ENABLED_ENV_VAR):
        from_team_memory_readiness_digest_db_env(
            {
                TEAM_MEMORY_READINESS_DIGEST_DB_ENABLED_ENV_VAR: "yes",
                TEAM_MEMORY_READINESS_DIGEST_DB_DSN_ENV_VAR: LOCAL_DSN,
            },
        )


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    with pytest.raises(ValueError, match="enabled must be a bool"):
        SupabaseTeamMemoryReadinessDigestConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn=LOCAL_DSN,
            table_name=DEFAULT_TEAM_MEMORY_READINESS_DIGEST_DB_TABLE,
        )

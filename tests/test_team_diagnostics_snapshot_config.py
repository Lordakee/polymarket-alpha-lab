from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from polymarket_alpha_lab.supabase_team_diagnostics_snapshot_config import (
    DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR,
    SupabaseTeamDiagnosticsSnapshotConfig,
    from_team_diagnostics_snapshot_db_env,
)


LOCAL_SECRET_DSN = "postgresql://team-diagnostics:secret@localhost:54322/postgres"
REMOTE_SECRET_DSN = "postgresql://team-diagnostics:secret@example.invalid/postgres"


def test_disabled_env_config_accepts_missing_dsn() -> None:
    config = from_team_diagnostics_snapshot_db_env({})

    assert config == SupabaseTeamDiagnosticsSnapshotConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_team_diagnostics_snapshot_db_env(
            {
                TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR: "true",
                TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR: " ",
                "UNRELATED_SECRET": LOCAL_SECRET_DSN,
            },
        )

    message = str(exc_info.value)
    assert TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert "must be set when DB is enabled" in message
    assert LOCAL_SECRET_DSN not in message
    assert "postgresql://" not in message
    assert "secret" not in message.lower()


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
    config = SupabaseTeamDiagnosticsSnapshotConfig(
        enabled=True,
        dsn=dsn,
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
def test_config_rejects_remote_or_unsafe_dsn_without_echoing_secret(
    dsn: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        SupabaseTeamDiagnosticsSnapshotConfig(
            enabled=False,
            dsn=dsn,
        )

    message = str(exc_info.value)
    assert TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "secret" not in message.lower()


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config = SupabaseTeamDiagnosticsSnapshotConfig(
        enabled=True,
        dsn=LOCAL_SECRET_DSN,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "dsn=<redacted>" in rendered
    assert LOCAL_SECRET_DSN not in rendered
    assert "secret" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "TeamDiagnosticsSnapshots",
        "team-diagnostics-snapshots",
        "team.diagnostics_snapshots",
        "_team_diagnostics_snapshots",
        "team_diagnostics_snapshots_",
        "",
    ],
)
def test_table_name_must_match_store_simple_lowercase_identifier(
    table_name: str,
) -> None:
    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        SupabaseTeamDiagnosticsSnapshotConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


def test_env_table_name_error_mentions_variable_name() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_team_diagnostics_snapshot_db_env(
            {
                TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR: "TeamDiagnosticsSnapshots",
            },
        )

    assert TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR in str(exc_info.value)


def test_enabled_flag_is_explicit_and_strict() -> None:
    with pytest.raises(ValueError, match=TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR):
        from_team_diagnostics_snapshot_db_env(
            {
                TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR: "yes",
                TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR: "postgresql://localhost/postgres",
            },
        )

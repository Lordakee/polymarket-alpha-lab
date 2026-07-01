from __future__ import annotations

from pathlib import Path

import pytest

from polymarket_alpha_lab.supabase_team_forecast_config import (
    DEFAULT_TEAM_FORECAST_DB_TABLE,
    DEFAULT_TEAM_FORECAST_EVIDENCE_DB_TABLE,
    DEFAULT_TEAM_FORECAST_OUTCOME_DB_TABLE,
    DEFAULT_TEAM_PROFILE_DB_TABLE,
    DEFAULT_TEAM_ROUTE_DB_TABLE,
    TEAM_FORECAST_DB_DSN_ENV_VAR,
    TEAM_FORECAST_DB_ENABLED_ENV_VAR,
    TEAM_FORECAST_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR,
    TEAM_PROFILE_DB_TABLE_ENV_VAR,
    TEAM_ROUTE_DB_TABLE_ENV_VAR,
    SupabaseTeamForecastConfig,
    from_team_forecast_db_env,
)


ENV_EXAMPLE_PATH = Path(".env.example")
RUNBOOK_PATH = Path("docs/team-forecast-supabase-runbook.md")
MIGRATION_SAFETY_PATH = Path("docs/team-forecast-migration-safety.md")

LOCAL_SECRET_POSTGRES_DSN = (
    "postgresql://sensitive-token:postgres@localhost:54322/postgres"
)
TEAM_FORECAST_ENV_VARS = (
    TEAM_FORECAST_DB_ENABLED_ENV_VAR,
    TEAM_FORECAST_DB_DSN_ENV_VAR,
    TEAM_PROFILE_DB_TABLE_ENV_VAR,
    TEAM_ROUTE_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR,
)
DEFAULT_TABLE_NAMES = (
    DEFAULT_TEAM_PROFILE_DB_TABLE,
    DEFAULT_TEAM_ROUTE_DB_TABLE,
    DEFAULT_TEAM_FORECAST_DB_TABLE,
    DEFAULT_TEAM_FORECAST_EVIDENCE_DB_TABLE,
    DEFAULT_TEAM_FORECAST_OUTCOME_DB_TABLE,
)


def test_team_forecast_env_vars_are_blank_in_env_example_without_dsn_sample() -> None:
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    for env_var in TEAM_FORECAST_ENV_VARS:
        assert lines.count(f"{env_var}=") == 1

    assert "postgresql://" not in text


def test_default_table_names_align_with_docs() -> None:
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")
    safety_text = MIGRATION_SAFETY_PATH.read_text(encoding="utf-8")

    for table_name in DEFAULT_TABLE_NAMES:
        assert table_name in runbook_text
        assert table_name in safety_text


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://postgres:super-secret-password@db.abcdefghijklmnopqrst.supabase.co:5432/postgres",
        "postgresql://postgres:super-secret-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
    ],
)
def test_from_team_forecast_db_env_rejects_hosted_or_pooler_dsn_without_echoing_it(
    dsn: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        from_team_forecast_db_env(
            {
                TEAM_FORECAST_DB_ENABLED_ENV_VAR: "true",
                TEAM_FORECAST_DB_DSN_ENV_VAR: dsn,
            },
        )

    message = str(exc_info.value)
    assert TEAM_FORECAST_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "super-secret-password" not in message
    assert "db.abcdefghijklmnopqrst.supabase.co" not in message
    assert "pooler.supabase.com" not in message


def test_team_forecast_config_repr_redacts_dsn() -> None:
    config = SupabaseTeamForecastConfig(
        enabled=True,
        dsn=LOCAL_SECRET_POSTGRES_DSN,
    )

    rendered = repr(config)

    assert "dsn=<redacted>" in rendered
    assert LOCAL_SECRET_POSTGRES_DSN not in rendered
    assert "sensitive-token" not in rendered


def test_enabling_team_forecast_db_requires_dsn_without_echoing_dsn_shape() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_team_forecast_db_env({TEAM_FORECAST_DB_ENABLED_ENV_VAR: "true"})

    message = str(exc_info.value)
    assert TEAM_FORECAST_DB_DSN_ENV_VAR in message
    assert "must be set when DB is enabled" in message
    assert "postgresql://" not in message


def test_supplied_team_forecast_dsn_is_validated_even_when_disabled() -> None:
    hosted_dsn = (
        "postgresql://postgres:super-secret-password@db.abcdefghijklmnopqrst.supabase.co"
        ":5432/postgres"
    )

    with pytest.raises(ValueError) as exc_info:
        from_team_forecast_db_env(
            {
                TEAM_FORECAST_DB_ENABLED_ENV_VAR: "false",
                TEAM_FORECAST_DB_DSN_ENV_VAR: hosted_dsn,
            },
        )

    message = str(exc_info.value)
    assert TEAM_FORECAST_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert hosted_dsn not in message
    assert "super-secret-password" not in message

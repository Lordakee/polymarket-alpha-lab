from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import polymarket_alpha_lab.supabase_outcome_tracking_config as outcome_config
from polymarket_alpha_lab.supabase_outcome_tracking_config import (
    DEFAULT_OUTCOME_TRACKING_DB_TABLE,
    OUTCOME_TRACKING_DB_DSN_ENV_VAR,
    OUTCOME_TRACKING_DB_ENABLED_ENV_VAR,
    OUTCOME_TRACKING_DB_TABLE_ENV_VAR,
    SupabaseOutcomeTrackingConfig,
    from_outcome_tracking_db_env,
)


LOCAL_POSTGRES_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


def test_disabled_env_config_uses_default_table_and_accepts_absent_dsn() -> None:
    config = from_outcome_tracking_db_env({})

    assert config == SupabaseOutcomeTrackingConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_OUTCOME_TRACKING_DB_TABLE,
    )


@pytest.mark.parametrize("enabled_value", ["1", "true", " TRUE "])
def test_enabled_env_config_accepts_explicit_true_values(enabled_value: str) -> None:
    dsn = LOCAL_POSTGRES_DSN

    config = from_outcome_tracking_db_env(
        {
            OUTCOME_TRACKING_DB_ENABLED_ENV_VAR: enabled_value,
            OUTCOME_TRACKING_DB_DSN_ENV_VAR: dsn,
            OUTCOME_TRACKING_DB_TABLE_ENV_VAR: "outcome_tracking_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "outcome_tracking_archive"


@pytest.mark.parametrize("enabled_value", ["", "0", "false", " FALSE "])
def test_enabled_env_config_accepts_explicit_false_values(enabled_value: str) -> None:
    config = from_outcome_tracking_db_env(
        {
            OUTCOME_TRACKING_DB_ENABLED_ENV_VAR: enabled_value,
            OUTCOME_TRACKING_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
        },
    )

    assert config.enabled is False


def test_enabled_env_config_rejects_invalid_flag_with_env_var_name() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_outcome_tracking_db_env(
            {
                OUTCOME_TRACKING_DB_ENABLED_ENV_VAR: "yes",
                OUTCOME_TRACKING_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            },
        )

    assert OUTCOME_TRACKING_DB_ENABLED_ENV_VAR in str(exc_info.value)


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://postgres:postgres@localhost:54322/postgres",
        "postgres://postgres:postgres@127.0.0.1:54322/postgres",
        "host=localhost port=54322 dbname=postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
        "host=/var/run/postgresql dbname=postgres",
    ],
)
def test_config_accepts_local_postgres_dsn_shapes(dsn: str) -> None:
    config = SupabaseOutcomeTrackingConfig(
        enabled=False,
        dsn=dsn,
        table_name=DEFAULT_OUTCOME_TRACKING_DB_TABLE,
    )

    assert config.dsn == dsn


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://topsecret@example.invalid/postgres",
        "postgres://db.example.com/postgres",
        "postgresql://localhost:54322/postgres?hostaddr=127.0.0.1",
        "host=example.invalid dbname=postgres",
    ],
)
def test_config_rejects_remote_or_unsafe_dsn_without_echoing_secret(
    dsn: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        SupabaseOutcomeTrackingConfig(
            enabled=False,
            dsn=dsn,
            table_name=DEFAULT_OUTCOME_TRACKING_DB_TABLE,
        )

    message = str(exc_info.value)
    assert OUTCOME_TRACKING_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "topsecret" not in message


@pytest.mark.parametrize(
    "dsn_value",
    [
        None,
        "",
        " ",
        "postgresql://sensitive-token:postgres@localhost:54322/postgres ",
        " postgresql://sensitive-token:postgres@localhost:54322/postgres",
    ],
)
def test_disabled_config_normalizes_absent_blank_and_padded_dsn_to_none(
    dsn_value: str | None,
) -> None:
    config = SupabaseOutcomeTrackingConfig(
        enabled=False,
        dsn=dsn_value,
        table_name=DEFAULT_OUTCOME_TRACKING_DB_TABLE,
    )

    assert config.dsn is None


@pytest.mark.parametrize("dsn_value", [None, "", " "])
def test_enabled_env_config_requires_dsn_without_echoing_secret(
    dsn_value: str | None,
) -> None:
    unrelated_secret = "postgresql://topsecret:postgres@localhost:54322/postgres"
    env = {
        OUTCOME_TRACKING_DB_ENABLED_ENV_VAR: "true",
        "UNRELATED_SECRET": unrelated_secret,
    }
    if dsn_value is not None:
        env[OUTCOME_TRACKING_DB_DSN_ENV_VAR] = dsn_value

    with pytest.raises(ValueError) as exc_info:
        from_outcome_tracking_db_env(env)

    message = str(exc_info.value)
    assert OUTCOME_TRACKING_DB_DSN_ENV_VAR in message
    assert unrelated_secret not in message
    assert "topsecret" not in message


def test_enabled_env_config_rejects_padded_dsn_without_echoing_secret() -> None:
    secret_dsn = "postgresql://topsecret:postgres@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        from_outcome_tracking_db_env(
            {
                OUTCOME_TRACKING_DB_ENABLED_ENV_VAR: "1",
                OUTCOME_TRACKING_DB_DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert OUTCOME_TRACKING_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "topsecret" not in message


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config = SupabaseOutcomeTrackingConfig(
        enabled=True,
        dsn="postgresql://topsecret:postgres@localhost:54322/postgres",
        table_name=DEFAULT_OUTCOME_TRACKING_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=<redacted>" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    rendered = repr(
        SupabaseOutcomeTrackingConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_OUTCOME_TRACKING_DB_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "OutcomeTrackingReports",
        "outcome-tracking-reports",
        "outcome.tracking.reports",
        "_outcome_tracking_reports",
        "outcome_tracking_reports_",
        "",
    ],
)
def test_table_name_must_match_simple_lowercase_identifier(table_name: str) -> None:
    with pytest.raises(
        ValueError,
        match="table_name must be a simple lowercase identifier",
    ):
        SupabaseOutcomeTrackingConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "outcome_tracking_reports",
        "outcome_1_tracking_2_reports",
    ],
)
def test_table_name_accepts_simple_lowercase_identifier_values(table_name: str) -> None:
    config = SupabaseOutcomeTrackingConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_outcome_tracking_db_env(
            {
                OUTCOME_TRACKING_DB_TABLE_ENV_VAR: "OutcomeTrackingReports",
            },
        )

    assert OUTCOME_TRACKING_DB_TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    with pytest.raises(ValueError, match="enabled must be a bool"):
        SupabaseOutcomeTrackingConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn=LOCAL_POSTGRES_DSN,
            table_name=DEFAULT_OUTCOME_TRACKING_DB_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    with pytest.raises(ValueError) as exc_info:
        SupabaseOutcomeTrackingConfig(
            enabled=True,
            dsn=object(),  # type: ignore[arg-type]
            table_name=DEFAULT_OUTCOME_TRACKING_DB_TABLE,
        )

    message = str(exc_info.value)
    assert OUTCOME_TRACKING_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_include_constants_config_and_loader() -> None:
    assert outcome_config.__all__ == (
        "OUTCOME_TRACKING_DB_DSN_ENV_VAR",
        "OUTCOME_TRACKING_DB_ENABLED_ENV_VAR",
        "OUTCOME_TRACKING_DB_TABLE_ENV_VAR",
        "DEFAULT_OUTCOME_TRACKING_DB_TABLE",
        "SupabaseOutcomeTrackingConfig",
        "from_outcome_tracking_db_env",
    )

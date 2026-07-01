from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from types import ModuleType

import pytest


MODULE_NAME = "polymarket_alpha_lab.supabase_team_forecast_config"
LOCAL_POSTGRES_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
LOCAL_SECRET_POSTGRES_DSN = (
    "postgresql://sensitive-token:postgres@localhost:54322/postgres"
)


def _config_module() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} module is not implemented")
        raise


def test_public_env_vars_defaults_and_exports() -> None:
    module = _config_module()

    assert module.TEAM_FORECAST_DB_ENABLED_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_ENABLED"
    )
    assert module.TEAM_FORECAST_DB_DSN_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN"
    )
    assert module.TEAM_PROFILE_DB_TABLE_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_TEAM_PROFILE_DB_TABLE"
    )
    assert module.TEAM_ROUTE_DB_TABLE_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_TEAM_ROUTE_DB_TABLE"
    )
    assert module.TEAM_FORECAST_DB_TABLE_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_TABLE"
    )
    assert module.TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_EVIDENCE_DB_TABLE"
    )
    assert module.TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_OUTCOME_DB_TABLE"
    )
    assert module.DEFAULT_TEAM_PROFILE_DB_TABLE == "team_profiles"
    assert module.DEFAULT_TEAM_ROUTE_DB_TABLE == "team_market_routes"
    assert module.DEFAULT_TEAM_FORECAST_DB_TABLE == "team_forecasts"
    assert module.DEFAULT_TEAM_FORECAST_EVIDENCE_DB_TABLE == (
        "team_forecast_evidence"
    )
    assert module.DEFAULT_TEAM_FORECAST_OUTCOME_DB_TABLE == (
        "team_forecast_outcomes"
    )
    assert module.__all__ == (
        "TEAM_FORECAST_DB_ENABLED_ENV_VAR",
        "TEAM_FORECAST_DB_DSN_ENV_VAR",
        "TEAM_PROFILE_DB_TABLE_ENV_VAR",
        "TEAM_ROUTE_DB_TABLE_ENV_VAR",
        "TEAM_FORECAST_DB_TABLE_ENV_VAR",
        "TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR",
        "TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR",
        "DEFAULT_TEAM_PROFILE_DB_TABLE",
        "DEFAULT_TEAM_ROUTE_DB_TABLE",
        "DEFAULT_TEAM_FORECAST_DB_TABLE",
        "DEFAULT_TEAM_FORECAST_EVIDENCE_DB_TABLE",
        "DEFAULT_TEAM_FORECAST_OUTCOME_DB_TABLE",
        "SupabaseTeamForecastConfig",
        "from_team_forecast_db_env",
    )


def test_disabled_env_config_accepts_missing_dsn_and_default_tables() -> None:
    module = _config_module()

    config = module.from_team_forecast_db_env({})

    assert config == module.SupabaseTeamForecastConfig(
        enabled=False,
        dsn=None,
        team_profile_table_name="team_profiles",
        team_route_table_name="team_market_routes",
        team_forecast_table_name="team_forecasts",
        team_forecast_evidence_table_name="team_forecast_evidence",
        team_forecast_outcome_table_name="team_forecast_outcomes",
    )


@pytest.mark.parametrize("enabled_value", ["1", "true", " TRUE "])
def test_enabled_env_config_reads_local_dsn_and_table_names(
    enabled_value: str,
) -> None:
    module = _config_module()

    config = module.from_team_forecast_db_env(
        {
            module.TEAM_FORECAST_DB_ENABLED_ENV_VAR: enabled_value,
            module.TEAM_FORECAST_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            module.TEAM_PROFILE_DB_TABLE_ENV_VAR: "public.team_profiles",
            module.TEAM_ROUTE_DB_TABLE_ENV_VAR: "research.team_market_routes",
            module.TEAM_FORECAST_DB_TABLE_ENV_VAR: "research.team_forecasts",
            module.TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR: (
                "research.team_forecast_evidence"
            ),
            module.TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR: (
                "research.team_forecast_outcomes"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == LOCAL_POSTGRES_DSN
    assert config.team_profile_table_name == "public.team_profiles"
    assert config.team_route_table_name == "research.team_market_routes"
    assert config.team_forecast_table_name == "research.team_forecasts"
    assert config.team_forecast_evidence_table_name == (
        "research.team_forecast_evidence"
    )
    assert config.team_forecast_outcome_table_name == (
        "research.team_forecast_outcomes"
    )


@pytest.mark.parametrize("enabled_value", ["", "0", "false", " FALSE "])
def test_disabled_env_config_parses_false_values_and_normalizes_blank_dsn(
    enabled_value: str,
) -> None:
    module = _config_module()

    config = module.from_team_forecast_db_env(
        {
            module.TEAM_FORECAST_DB_ENABLED_ENV_VAR: enabled_value,
            module.TEAM_FORECAST_DB_DSN_ENV_VAR: " ",
        },
    )

    assert config.enabled is False
    assert config.dsn is None


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_team_forecast_db_env(
            {
                module.TEAM_FORECAST_DB_ENABLED_ENV_VAR: "true",
                module.TEAM_FORECAST_DB_DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert module.TEAM_FORECAST_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


@pytest.mark.parametrize("enabled_value", ["yes", "2", True])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: object) -> None:
    module = _config_module()

    with pytest.raises(ValueError, match=module.TEAM_FORECAST_DB_ENABLED_ENV_VAR):
        module.from_team_forecast_db_env(
            {
                module.TEAM_FORECAST_DB_ENABLED_ENV_VAR: enabled_value,
                module.TEAM_FORECAST_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            },
        )


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
    module = _config_module()

    config = module.SupabaseTeamForecastConfig(
        enabled=False,
        dsn=dsn,
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
def test_any_supplied_dsn_is_validated_as_local_without_echoing_secret(
    dsn: str,
) -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabaseTeamForecastConfig(
            enabled=False,
            dsn=dsn,
        )

    message = str(exc_info.value)
    assert module.TEAM_FORECAST_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "topsecret" not in message


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _config_module()
    config = module.SupabaseTeamForecastConfig(
        enabled=True,
        dsn=LOCAL_SECRET_POSTGRES_DSN,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert LOCAL_SECRET_POSTGRES_DSN not in rendered
    assert "dsn=<redacted>" in rendered


@pytest.mark.parametrize(
    "field_name",
    [
        "team_profile_table_name",
        "team_route_table_name",
        "team_forecast_table_name",
        "team_forecast_evidence_table_name",
        "team_forecast_outcome_table_name",
    ],
)
@pytest.mark.parametrize(
    "table_name",
    [
        "a",
        "a0",
        "team_forecasts",
        "team_1_forecasts_2",
        "public.team_forecasts",
        "research_2026.team_forecast_evidence",
    ],
)
def test_table_names_accept_lowercase_identifiers_and_schema_prefix(
    field_name: str,
    table_name: str,
) -> None:
    module = _config_module()

    config = module.SupabaseTeamForecastConfig(
        enabled=False,
        dsn=None,
        **{field_name: table_name},
    )

    assert getattr(config, field_name) == table_name


@pytest.mark.parametrize(
    "field_name",
    [
        "team_profile_table_name",
        "team_route_table_name",
        "team_forecast_table_name",
        "team_forecast_evidence_table_name",
        "team_forecast_outcome_table_name",
    ],
)
def test_table_names_accept_63_byte_identifier_parts(field_name: str) -> None:
    module = _config_module()
    max_length_part = "a" + ("b" * 61) + "1"
    assert len(max_length_part.encode("utf-8")) == 63

    config = module.SupabaseTeamForecastConfig(
        enabled=False,
        dsn=None,
        **{field_name: f"public.{max_length_part}"},
    )

    assert getattr(config, field_name) == f"public.{max_length_part}"


@pytest.mark.parametrize(
    "field_name",
    [
        "team_profile_table_name",
        "team_route_table_name",
        "team_forecast_table_name",
        "team_forecast_evidence_table_name",
        "team_forecast_outcome_table_name",
    ],
)
@pytest.mark.parametrize(
    "table_name",
    [
        "TeamForecasts",
        "team-forecasts",
        "public.team.forecasts",
        "_team_forecasts",
        "team_forecasts_",
        "a" + ("b" * 62) + "1",
        "",
        ".team_forecasts",
        "public.",
    ],
)
def test_table_names_reject_values_outside_lowercase_identifier_contract(
    field_name: str,
    table_name: str,
) -> None:
    module = _config_module()

    with pytest.raises(
        ValueError,
        match="lowercase identifier with optional schema prefix",
    ):
        module.SupabaseTeamForecastConfig(
            enabled=False,
            dsn=None,
            **{field_name: table_name},
        )


def test_env_table_name_errors_mention_specific_variable_without_echoing_dsn() -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_team_forecast_db_env(
            {
                module.TEAM_FORECAST_DB_DSN_ENV_VAR: LOCAL_SECRET_POSTGRES_DSN,
                module.TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR: "BadTable",
            },
        )

    message = str(exc_info.value)
    assert module.TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR in message
    assert LOCAL_SECRET_POSTGRES_DSN not in message
    assert "sensitive-token" not in message


def test_direct_config_rejects_non_bool_enabled_and_non_string_dsn() -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabaseTeamForecastConfig(
            enabled=1,
            dsn=None,
        )

    with pytest.raises(ValueError) as exc_info:
        module.SupabaseTeamForecastConfig(
            enabled=False,
            dsn=object(),
        )

    message = str(exc_info.value)
    assert module.TEAM_FORECAST_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message

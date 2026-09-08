from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from types import ModuleType

import pytest


MODULE_NAME = "polymarket_alpha_lab.supabase_team_evidence_aggregation_config"
ENABLED_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_ENABLED"
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_TABLE"
LOCAL_POSTGRES_DSN = "postgresql://postgres:postgres@localhost:5432/postgres"
LOCAL_SECRET_POSTGRES_DSN = (
    "postgresql://sensitive-token:postgres@127.0.0.1:5432/postgres"
)
TABLE_ERROR = "lowercase identifier with optional schema prefix"


def _config_module() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} module is not implemented")
        raise


def test_public_env_vars_defaults_and_exports() -> None:
    module = _config_module()

    assert module.TEAM_EVIDENCE_AGGREGATION_DB_ENABLED_ENV_VAR == ENABLED_ENV_VAR
    assert module.TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR == DSN_ENV_VAR
    assert module.TEAM_EVIDENCE_AGGREGATION_DB_TABLE_ENV_VAR == TABLE_ENV_VAR
    assert module.DEFAULT_TEAM_EVIDENCE_AGGREGATION_DB_TABLE == (
        "team_evaluation_attempts"
    )
    assert module.__all__ == (
        "TEAM_EVIDENCE_AGGREGATION_DB_ENABLED_ENV_VAR",
        "TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR",
        "TEAM_EVIDENCE_AGGREGATION_DB_TABLE_ENV_VAR",
        "DEFAULT_TEAM_EVIDENCE_AGGREGATION_DB_TABLE",
        "SupabaseTeamEvidenceAggregationConfig",
        "from_team_evidence_aggregation_db_env",
    )


def test_disabled_default_env_config_needs_no_dsn() -> None:
    module = _config_module()

    config = module.from_team_evidence_aggregation_db_env({})

    assert config.enabled is False
    assert config.dsn is None
    assert config.table_name == "team_evaluation_attempts"


def test_env_loader_parses_enabled_strictly_and_reads_local_dsn() -> None:
    module = _config_module()

    for enabled_value in ("1", "true", " TRUE "):
        config = module.from_team_evidence_aggregation_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
                TABLE_ENV_VAR: "research.team_evaluation_attempts",
            },
        )
        assert config.enabled is True
        assert config.dsn == LOCAL_POSTGRES_DSN
        assert config.table_name == "research.team_evaluation_attempts"

    for enabled_value in ("", "0", "false", " FALSE "):
        config = module.from_team_evidence_aggregation_db_env(
            {ENABLED_ENV_VAR: enabled_value, DSN_ENV_VAR: " "},
        )
        assert config.enabled is False
        assert config.dsn is None
        assert config.table_name == "team_evaluation_attempts"

    for enabled_value in ("yes", "2", True):
        with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
            module.from_team_evidence_aggregation_db_env(
                {ENABLED_ENV_VAR: enabled_value, DSN_ENV_VAR: LOCAL_POSTGRES_DSN},
            )


def test_blank_table_env_value_falls_back_to_default_table() -> None:
    module = _config_module()
    default_table = module.DEFAULT_TEAM_EVIDENCE_AGGREGATION_DB_TABLE

    for blank_table in ("", " "):
        config = module.from_team_evidence_aggregation_db_env(
            {TABLE_ENV_VAR: blank_table},
        )
        assert config.table_name == default_table


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_team_evidence_aggregation_db_env(
            {ENABLED_ENV_VAR: "true", DSN_ENV_VAR: f" {secret_dsn} "},
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "must be set when DB is enabled" in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_dsn_validation_goes_through_validate_local_postgres_dsn() -> None:
    module = _config_module()

    for dsn in (
        "postgresql://postgres:postgres@localhost:5432/postgres",
        "postgres://postgres:postgres@127.0.0.1:5432/postgres",
    ):
        config = module.SupabaseTeamEvidenceAggregationConfig(
            enabled=True,
            dsn=dsn,
        )
        assert config.dsn == dsn

    for dsn in (
        "jsonl://data/team_evidence.jsonl",
        "sqlite:///team_evidence.db",
        "postgresql://topsecret@db.example.com/postgres",
        "host=db.example.com dbname=postgres",
    ):
        for enabled in (True, False):
            with pytest.raises(ValueError) as exc_info:
                module.SupabaseTeamEvidenceAggregationConfig(
                    enabled=enabled,
                    dsn=dsn,
                )
            message = str(exc_info.value)
            assert DSN_ENV_VAR in message
            assert "local Postgres/Supabase" in message
            assert dsn not in message
            assert "topsecret" not in message


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _config_module()
    config = module.SupabaseTeamEvidenceAggregationConfig(
        enabled=True,
        dsn=LOCAL_SECRET_POSTGRES_DSN,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert LOCAL_SECRET_POSTGRES_DSN not in rendered
    assert "dsn=<redacted>" in rendered


def test_table_name_validation_contract_and_env_error_mapping() -> None:
    module = _config_module()

    for table_name in (
        "team_evaluation_attempts",
        "a",
        "a" + ("b" * 61) + "1",
        "public.team_evaluation_attempts",
    ):
        config = module.SupabaseTeamEvidenceAggregationConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )
        assert config.table_name == table_name

    for table_name in (
        "TeamEvaluationAttempts",
        "team-evaluation-attempts",
        "public.team.evaluation_attempts",
        "_team_evaluation_attempts",
        "team_evaluation_attempts_",
        "a" + ("b" * 62) + "1",
        "",
    ):
        with pytest.raises(ValueError, match=TABLE_ERROR):
            module.SupabaseTeamEvidenceAggregationConfig(
                enabled=False,
                dsn=None,
                table_name=table_name,
            )

    with pytest.raises(ValueError) as exc_info:
        module.from_team_evidence_aggregation_db_env(
            {DSN_ENV_VAR: LOCAL_SECRET_POSTGRES_DSN, TABLE_ENV_VAR: "BadTable"},
        )
    message = str(exc_info.value)
    assert TABLE_ENV_VAR in message
    assert "sensitive-token" not in message


def test_direct_config_rejects_non_bool_enabled_and_non_string_dsn() -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabaseTeamEvidenceAggregationConfig(enabled=1, dsn=None)

    with pytest.raises(ValueError) as exc_info:
        module.SupabaseTeamEvidenceAggregationConfig(enabled=False, dsn=object())

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message

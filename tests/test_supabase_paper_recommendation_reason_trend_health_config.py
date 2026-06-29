from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest


ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_REASON_TREND_HEALTH_DB_ENABLED"
)
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_REASON_TREND_HEALTH_DB_DSN"
TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_REASON_TREND_HEALTH_DB_TABLE"
)
DEFAULT_TABLE = "paper_recommendation_reason_trend_health_reports"
LOCAL_POSTGRESQL_DSN = "postgresql://localhost:54322/postgres"


def _config_module():
    import polymarket_alpha_lab.supabase_paper_recommendation_reason_trend_health_config as config_module

    return config_module


def test_public_constants_match_expected_env_surface() -> None:
    config_module = _config_module()

    assert (
        config_module.PAPER_RECOMMENDATION_REASON_TREND_HEALTH_DB_ENABLED_ENV_VAR
        == ENABLED_ENV_VAR
    )
    assert (
        config_module.PAPER_RECOMMENDATION_REASON_TREND_HEALTH_DB_DSN_ENV_VAR
        == DSN_ENV_VAR
    )
    assert (
        config_module.PAPER_RECOMMENDATION_REASON_TREND_HEALTH_DB_TABLE_ENV_VAR
        == TABLE_ENV_VAR
    )
    assert (
        config_module.DEFAULT_PAPER_RECOMMENDATION_REASON_TREND_HEALTH_DB_TABLE
        == DEFAULT_TABLE
    )
    assert "SupabasePaperRecommendationReasonTrendHealthConfig" in config_module.__all__
    assert "from_paper_recommendation_reason_trend_health_db_env" in config_module.__all__


def test_disabled_env_config_accepts_missing_dsn() -> None:
    config_module = _config_module()

    config = config_module.from_paper_recommendation_reason_trend_health_db_env({})

    assert config == config_module.SupabasePaperRecommendationReasonTrendHealthConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_recommendation_reason_trend_health_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: " ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_enabled_env_config_reads_explicit_dsn_at_process_edge() -> None:
    config_module = _config_module()
    dsn = LOCAL_POSTGRESQL_DSN

    config = config_module.from_paper_recommendation_reason_trend_health_db_env(
        {
            ENABLED_ENV_VAR: "1",
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "paper_recommendation_reason_trend_health_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_recommendation_reason_trend_health_archive"


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://localhost:54322/postgres",
        "postgres://127.0.0.1:5432/postgres",
        "host=localhost port=54322 dbname=postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
    ],
)
def test_config_accepts_local_postgres_dsn_forms(dsn: str) -> None:
    config_module = _config_module()

    config = config_module.SupabasePaperRecommendationReasonTrendHealthConfig(
        enabled=True,
        dsn=dsn,
        table_name=DEFAULT_TABLE,
    )

    assert config.dsn == dsn


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://sensitive-token@db.example.com/postgres",
        "postgres://192.168.1.10/postgres",
        "hostaddr=127.0.0.1 password=sensitive-token dbname=postgres",
        "sqlite:///tmp/sensitive-token.db",
    ],
)
def test_config_rejects_remote_or_unsafe_dsn_without_echoing_secret(
    dsn: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabasePaperRecommendationReasonTrendHealthConfig(
            enabled=True,
            dsn=dsn,
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "sensitive-token" not in message


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabasePaperRecommendationReasonTrendHealthConfig(
        enabled=True,
        dsn="postgresql://sensitive-token@localhost:54322/postgres",
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered


@pytest.mark.parametrize(
    "table_name",
    ["PaperReports", "paper-reports", "paper.reports", "_paper_reports", "paper_reports_", ""],
)
def test_table_name_must_match_store_simple_lowercase_identifier(table_name: str) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        config_module.SupabasePaperRecommendationReasonTrendHealthConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


def test_env_table_name_error_mentions_variable_name() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_recommendation_reason_trend_health_db_env(
            {TABLE_ENV_VAR: "PaperReports"},
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_enabled_flag_is_explicit_and_strict() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
        config_module.from_paper_recommendation_reason_trend_health_db_env(
            {
                ENABLED_ENV_VAR: "yes",
                DSN_ENV_VAR: LOCAL_POSTGRESQL_DSN,
            },
        )

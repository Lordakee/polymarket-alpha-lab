from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest


ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_QUALITY_SUMMARY_DB_ENABLED"
)
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_QUALITY_SUMMARY_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_QUALITY_SUMMARY_DB_TABLE"
DEFAULT_TABLE = "paper_recommendation_quality_summary_reports"
LOCAL_SUPABASE_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


def _config_module():
    import polymarket_alpha_lab.supabase_paper_recommendation_quality_summary_config as config_module

    return config_module


def test_public_constants_match_expected_env_surface() -> None:
    config_module = _config_module()
    from polymarket_alpha_lab.paper_recommendation_quality_summary_store import (
        DEFAULT_PAPER_RECOMMENDATION_QUALITY_SUMMARY_REPORTS_TABLE,
    )

    assert (
        config_module.PAPER_RECOMMENDATION_QUALITY_SUMMARY_DB_ENABLED_ENV_VAR
        == ENABLED_ENV_VAR
    )
    assert config_module.PAPER_RECOMMENDATION_QUALITY_SUMMARY_DB_DSN_ENV_VAR == DSN_ENV_VAR
    assert (
        config_module.PAPER_RECOMMENDATION_QUALITY_SUMMARY_DB_TABLE_ENV_VAR
        == TABLE_ENV_VAR
    )
    assert (
        config_module.DEFAULT_PAPER_RECOMMENDATION_QUALITY_SUMMARY_DB_TABLE
        == DEFAULT_PAPER_RECOMMENDATION_QUALITY_SUMMARY_REPORTS_TABLE
        == DEFAULT_TABLE
    )
    assert "SupabasePaperRecommendationQualitySummaryConfig" in config_module.__all__
    assert "from_paper_recommendation_quality_summary_db_env" in config_module.__all__


def test_disabled_env_config_accepts_missing_dsn() -> None:
    config_module = _config_module()

    config = config_module.from_paper_recommendation_quality_summary_db_env({})

    assert config == config_module.SupabasePaperRecommendationQualitySummaryConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://postgres:sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_recommendation_quality_summary_db_env(
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
    dsn = LOCAL_SUPABASE_DSN

    config = config_module.from_paper_recommendation_quality_summary_db_env(
        {
            ENABLED_ENV_VAR: "1",
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "paper_recommendation_quality_summary_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_recommendation_quality_summary_archive"


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://postgres:postgres@localhost:54322/postgres",
        "postgres://postgres:postgres@127.0.0.1:54322/postgres",
        "postgresql://postgres:postgres@[::1]:54322/postgres",
        "host=localhost port=54322 dbname=postgres user=postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
        "host=/var/run/postgresql dbname=postgres user=postgres",
    ],
)
def test_enabled_env_config_accepts_local_postgres_dsns(dsn: str) -> None:
    config_module = _config_module()

    config = config_module.from_paper_recommendation_quality_summary_db_env(
        {
            ENABLED_ENV_VAR: "true",
            DSN_ENV_VAR: dsn,
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == DEFAULT_TABLE


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://postgres:super-secret@hosted.example.invalid:5432/postgres",
        "postgres://postgres:super-secret@192.168.1.10:5432/postgres",
        "host=hosted.example.invalid dbname=postgres password=super-secret",
        "postgresql:///postgres?hostaddr=127.0.0.1",
        "postgresql:///postgres?service=local-supabase",
        "hostaddr=127.0.0.1 dbname=postgres password=super-secret",
        "service=local-supabase password=super-secret",
    ],
)
def test_enabled_env_config_rejects_remote_or_unsafe_dsns_without_echoing_secret(
    dsn: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_recommendation_quality_summary_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "hosted.example.invalid" not in message
    assert "192.168.1.10" not in message
    assert "super-secret" not in message


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabasePaperRecommendationQualitySummaryConfig(
        enabled=True,
        dsn="postgresql://postgres:sensitive-token@localhost:54322/postgres",
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
        config_module.SupabasePaperRecommendationQualitySummaryConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


def test_env_table_name_error_mentions_variable_name() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_recommendation_quality_summary_db_env(
            {TABLE_ENV_VAR: "PaperReports"},
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_enabled_flag_is_explicit_and_strict() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
        config_module.from_paper_recommendation_quality_summary_db_env(
            {
                ENABLED_ENV_VAR: "yes",
                DSN_ENV_VAR: LOCAL_SUPABASE_DSN,
            },
        )

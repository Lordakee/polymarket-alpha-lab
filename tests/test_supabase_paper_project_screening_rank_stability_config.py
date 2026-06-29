from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_ENABLED"
)
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE"
DEFAULT_TABLE = "paper_project_screening_rank_stability_reports"
LOCAL_POSTGRES_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
LOCAL_SECRET_POSTGRES_DSN = (
    "postgresql://sensitive-token:postgres@localhost:54322/postgres"
)
CONFIG_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_paper_project_screening_rank_stability_config.py"
)


def _config_module():
    import polymarket_alpha_lab.supabase_paper_project_screening_rank_stability_config as config_module

    return config_module


def test_public_constants_match_expected_env_surface() -> None:
    config_module = _config_module()
    from polymarket_alpha_lab.paper_project_screening_rank_stability_store import (
        DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_REPORTS_TABLE,
    )

    assert config_module.PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_ENABLED_ENV_VAR == ENABLED_ENV_VAR
    assert config_module.PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_DSN_ENV_VAR == DSN_ENV_VAR
    assert config_module.PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE_ENV_VAR == TABLE_ENV_VAR
    assert (
        config_module.DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE
        == DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_REPORTS_TABLE
        == DEFAULT_TABLE
    )
    assert "SupabasePaperProjectScreeningRankStabilityConfig" in config_module.__all__
    assert "from_paper_project_screening_rank_stability_db_env" in config_module.__all__


def test_default_table_constant_is_imported_from_store_to_avoid_drift() -> None:
    source = CONFIG_SOURCE.read_text(encoding="utf-8")

    assert "DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_REPORTS_TABLE" in source
    assert '"paper_project_screening_rank_stability_reports"' not in source


def test_disabled_env_config_accepts_missing_dsn() -> None:
    config_module = _config_module()

    config = config_module.from_paper_project_screening_rank_stability_db_env({})

    assert config == config_module.SupabasePaperProjectScreeningRankStabilityConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_project_screening_rank_stability_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: " ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message


def test_enabled_env_config_reads_explicit_dsn_at_process_edge() -> None:
    config_module = _config_module()
    dsn = LOCAL_POSTGRES_DSN

    config = config_module.from_paper_project_screening_rank_stability_db_env(
        {
            ENABLED_ENV_VAR: "1",
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "paper_project_screening_rank_stability_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_project_screening_rank_stability_archive"


@pytest.mark.parametrize(
    ("enabled_value", "expected_enabled"),
    [
        ("", False),
        ("0", False),
        ("false", False),
        (" FALSE ", False),
        ("1", True),
        ("true", True),
        (" TRUE ", True),
    ],
)
def test_enabled_env_config_accepts_only_strict_values(
    enabled_value: str,
    expected_enabled: bool,
) -> None:
    config_module = _config_module()

    config = config_module.from_paper_project_screening_rank_stability_db_env(
        {
            ENABLED_ENV_VAR: enabled_value,
            DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
        },
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", ["yes", "on", "2"])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
        config_module.from_paper_project_screening_rank_stability_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            },
        )


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabasePaperProjectScreeningRankStabilityConfig(
        enabled=True,
        dsn=LOCAL_SECRET_POSTGRES_DSN,
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert LOCAL_SECRET_POSTGRES_DSN not in rendered
    assert "dsn=<redacted>" in rendered
    assert DEFAULT_TABLE in rendered


def test_config_rejects_remote_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    dsn = "postgresql://sensitive-token@example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabasePaperProjectScreeningRankStabilityConfig(
            enabled=False,
            dsn=dsn,
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "sensitive-token" not in message


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperReports",
        "paper-reports",
        "paper.reports",
        "_paper_reports",
        "paper_reports_",
        "a",
        "",
    ],
)
def test_table_name_must_match_store_simple_lowercase_identifier(table_name: str) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        config_module.SupabasePaperProjectScreeningRankStabilityConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_project_screening_rank_stability_archive",
        "rank_1_stability_2_archive",
    ],
)
def test_table_name_accepts_simple_lowercase_identifier_values(table_name: str) -> None:
    config_module = _config_module()

    config = config_module.SupabasePaperProjectScreeningRankStabilityConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_project_screening_rank_stability_db_env(
            {TABLE_ENV_VAR: "PaperReports"},
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        config_module.SupabasePaperProjectScreeningRankStabilityConfig(
            enabled=1,
            dsn=LOCAL_POSTGRES_DSN,
            table_name=DEFAULT_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabasePaperProjectScreeningRankStabilityConfig(
            enabled=True,
            dsn=object(),
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message

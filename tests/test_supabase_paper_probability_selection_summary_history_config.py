from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from types import ModuleType

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "supabase_paper_probability_selection_summary_history_config"
)


def _config_module() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} module is not implemented")
        raise


def test_public_constants_match_history_store_surface() -> None:
    module = _config_module()
    from polymarket_alpha_lab.paper_probability_selection_summary_history_store import (
        DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE,
    )

    assert module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_"
        "PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED"
    )
    assert module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN"
    )
    assert module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE"
    )
    assert (
        module.DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE
        == DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE
        == "paper_probability_selection_summary_history_reports"
    )
    assert module.__all__ == (
        "DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE",
        "PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR",
        "PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR",
        "PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR",
        "SupabasePaperProbabilitySelectionSummaryHistoryConfig",
        "from_paper_probability_selection_summary_history_db_env",
    )


def test_disabled_env_config_accepts_missing_dsn_and_default_table() -> None:
    module = _config_module()

    config = module.from_paper_probability_selection_summary_history_db_env({})

    assert config == module.SupabasePaperProbabilitySelectionSummaryHistoryConfig(
        enabled=False,
        dsn=None,
        table_name=module.DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE,
    )


@pytest.mark.parametrize("enabled_value", ["1", "true", " TRUE "])
def test_enabled_env_config_reads_specific_history_dsn_and_table(
    enabled_value: str,
) -> None:
    module = _config_module()
    dsn = "postgresql://localhost:54322/postgres"

    config = module.from_paper_probability_selection_summary_history_db_env(
        {
            module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR: (
                enabled_value
            ),
            module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR: dsn,
            module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR: (
                "paper_probability_selection_summary_history_archive"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == (
        "paper_probability_selection_summary_history_archive"
    )


@pytest.mark.parametrize("enabled_value", ["", "0", "false", " FALSE "])
def test_disabled_env_config_parses_only_explicit_false_values(
    enabled_value: str,
) -> None:
    module = _config_module()

    config = module.from_paper_probability_selection_summary_history_db_env(
        {
            module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR: (
                enabled_value
            ),
            module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR: " ",
        },
    )

    assert config.enabled is False
    assert config.dsn is None
    assert (
        config.table_name
        == module.DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_probability_selection_summary_history_db_env(
            {
                module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR: (
                    "true"
                ),
                module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR: (
                    f" {secret_dsn} "
                ),
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_invalid_enabled_env_value_names_variable_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_probability_selection_summary_history_db_env(
            {
                module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR: (
                    "yes"
                ),
                module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR: (
                    secret_dsn
                ),
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


@pytest.mark.parametrize(
    "raw_dsn",
    [
        None,
        "",
        " ",
        "\t\n",
        " postgresql://sensitive-token.example.invalid/postgres",
        "postgresql://sensitive-token.example.invalid/postgres ",
    ],
)
def test_dsn_normalizes_absent_blank_or_padded_values_to_none(
    raw_dsn: str | None,
) -> None:
    module = _config_module()

    config = module.SupabasePaperProbabilitySelectionSummaryHistoryConfig(
        enabled=False,
        dsn=raw_dsn,
        table_name=module.DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE,
    )

    assert config.dsn is None
    assert "secret" not in repr(config).lower()


def test_direct_config_rejects_remote_dsn_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token@example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperProbabilitySelectionSummaryHistoryConfig(
            enabled=False,
            dsn=secret_dsn,
            table_name=(
                module.DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE
            ),
        )

    message = str(exc_info.value)
    assert (
        module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR in message
    )
    assert secret_dsn not in message
    assert "sensitive-token" not in message


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _config_module()
    config = module.SupabasePaperProbabilitySelectionSummaryHistoryConfig(
        enabled=True,
        dsn="postgresql://sensitive-token@localhost:54322/postgres",
        table_name=module.DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperProbabilitySelectionSummaryHistory",
        "paper-probability-selection-summary-history",
        "paper.probability.selection.summary.history",
        "_paper_probability_selection_summary_history_reports",
        "paper_probability_selection_summary_history_reports_",
        "",
    ],
)
def test_table_name_must_match_simple_lowercase_identifier(table_name: str) -> None:
    module = _config_module()

    with pytest.raises(
        ValueError,
        match="table_name must be a simple lowercase identifier",
    ):
        module.SupabasePaperProbabilitySelectionSummaryHistoryConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


def test_env_table_name_error_mentions_variable_name_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_probability_selection_summary_history_db_env(
            {
                module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR: (
                    secret_dsn
                ),
                module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR: (
                    "PaperProbabilitySelectionSummaryHistory"
                ),
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabasePaperProbabilitySelectionSummaryHistoryConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn="postgresql://localhost:54322/postgres",
            table_name=module.DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE,
        )

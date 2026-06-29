from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from types import ModuleType

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.supabase_probability_selection_scorer_agreement_config"
)


def _config_module() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} module is not implemented")
        raise


def test_disabled_env_config_accepts_missing_dsn_and_default_table() -> None:
    module = _config_module()

    config = module.from_probability_selection_scorer_agreement_db_env({})

    assert config == module.SupabaseProbabilitySelectionScorerAgreementConfig(
        enabled=False,
        dsn=None,
        table_name=module.DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE,
    )


@pytest.mark.parametrize("enabled_value", ["1", "true", " TRUE "])
def test_enabled_env_config_reads_explicit_dsn_at_process_edge(
    enabled_value: str,
) -> None:
    module = _config_module()
    dsn = "postgresql://example.invalid/postgres"

    config = module.from_probability_selection_scorer_agreement_db_env(
        {
            module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR: (
                enabled_value
            ),
            module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR: dsn,
            module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE_ENV_VAR: (
                "probability_selection_scorer_agreement_archive"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "probability_selection_scorer_agreement_archive"


@pytest.mark.parametrize("enabled_value", ["", "0", "false", " FALSE "])
def test_disabled_env_config_parses_only_explicit_false_values(
    enabled_value: str,
) -> None:
    module = _config_module()

    config = module.from_probability_selection_scorer_agreement_db_env(
        {
            module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR: (
                enabled_value
            ),
            module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR: " ",
        },
    )

    assert config.enabled is False
    assert config.dsn is None
    assert (
        config.table_name
        == module.DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_probability_selection_scorer_agreement_db_env(
            {
                module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR: (
                    "true"
                ),
                module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR: (
                    f" {secret_dsn} "
                ),
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_invalid_enabled_env_value_names_variable_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_probability_selection_scorer_agreement_db_env(
            {
                module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR: (
                    "yes"
                ),
                module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR: (
                    secret_dsn
                ),
            },
        )

    message = str(exc_info.value)
    assert module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR in message
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

    config = module.SupabaseProbabilitySelectionScorerAgreementConfig(
        enabled=False,
        dsn=raw_dsn,
        table_name=module.DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE,
    )

    assert config.dsn is None
    assert "secret" not in repr(config).lower()


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _config_module()
    config = module.SupabaseProbabilitySelectionScorerAgreementConfig(
        enabled=True,
        dsn="postgresql://sensitive-token.example.invalid/postgres",
        table_name=module.DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE,
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
        "ProbabilitySelectionScorerAgreementReports",
        "probability-selection-scorer-agreement-reports",
        "probability.selection.scorer.agreement.reports",
        "_probability_selection_scorer_agreement_reports",
        "probability_selection_scorer_agreement_reports_",
        "",
    ],
)
def test_config_rejects_unsafe_table_names(table_name: str) -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="simple lowercase identifier"):
        module.from_probability_selection_scorer_agreement_db_env(
            {
                module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR: (
                    "false"
                ),
                module.PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE_ENV_VAR: (
                    table_name
                ),
            },
        )


def test_config_module_has_expected_public_exports() -> None:
    module = _config_module()

    assert set(module.__all__) == {
        "DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE",
        "PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR",
        "PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_ENABLED_ENV_VAR",
        "PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_TABLE_ENV_VAR",
        "SupabaseProbabilitySelectionScorerAgreementConfig",
        "from_probability_selection_scorer_agreement_db_env",
    }

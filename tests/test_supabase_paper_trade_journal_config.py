from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError
from types import ModuleType

import pytest

MODULE_NAME = "polymarket_alpha_lab.supabase_paper_trade_journal_config"
PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_ENABLED"
)
PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_DSN"
)
PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_TABLE"
)
DEFAULT_PAPER_TRADE_JOURNAL_DB_TABLE = "paper_trade_journal_records"


def _load_module() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} should exist")
        raise


def test_disabled_env_config_accepts_missing_dsn_and_uses_default_table() -> None:
    module = _load_module()

    config = module.from_paper_trade_journal_db_env({})

    assert config == module.SupabasePaperTradeJournalConfig(
        enabled=False,
        dsn=None,
        table_name=module.DEFAULT_PAPER_TRADE_JOURNAL_DB_TABLE,
    )
    assert config.table_name == "paper_trade_journal_records"


@pytest.mark.parametrize(
    "enabled_value",
    [
        "1",
        "true",
        " TRUE ",
    ],
)
def test_enabled_env_config_accepts_explicit_true_values(enabled_value: str) -> None:
    module = _load_module()
    dsn = "postgresql://example.invalid/postgres"

    config = module.from_paper_trade_journal_db_env(
        {
            module.PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR: enabled_value,
            module.PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR: dsn,
            module.PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR: "paper_journal_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_journal_archive"


@pytest.mark.parametrize(
    "enabled_value",
    [
        "",
        "0",
        "false",
        " FALSE ",
    ],
)
def test_enabled_env_config_accepts_explicit_false_values(enabled_value: str) -> None:
    module = _load_module()

    config = module.from_paper_trade_journal_db_env(
        {
            module.PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR: enabled_value,
        },
    )

    assert config.enabled is False
    assert config.dsn is None


@pytest.mark.parametrize("enabled_value", ["yes", "on", "2", "truthy"])
def test_enabled_env_config_rejects_invalid_enabled_values(enabled_value: str) -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_journal_db_env(
            {
                module.PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR: enabled_value,
                module.PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR: (
                    "postgresql://example.invalid/postgres"
                ),
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR in message
    assert enabled_value not in message


@pytest.mark.parametrize(
    "dsn_value",
    [
        None,
        "",
        " ",
        "\t\n",
        " postgresql://sensitive-token.example.invalid/postgres ",
    ],
)
def test_dsn_normalizes_missing_blank_or_padded_values_to_none(
    dsn_value: str | None,
) -> None:
    module = _load_module()

    config = module.SupabasePaperTradeJournalConfig(
        enabled=False,
        dsn=dsn_value,
        table_name=module.DEFAULT_PAPER_TRADE_JOURNAL_DB_TABLE,
    )

    assert config.dsn is None


@pytest.mark.parametrize("dsn_value", [None, "", " ", "\t\n"])
def test_enabled_config_requires_dsn_without_echoing_secret(
    dsn_value: str | None,
) -> None:
    module = _load_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_journal_db_env(
            {
                module.PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR: "true",
                module.PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR: dsn_value,
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_padded_enabled_dsn_is_rejected_without_echoing_secret() -> None:
    module = _load_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_journal_db_env(
            {
                module.PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR: "true",
                module.PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _load_module()

    config = module.SupabasePaperTradeJournalConfig(
        enabled=True,
        dsn="postgresql://sensitive-token.example.invalid/postgres",
        table_name=module.DEFAULT_PAPER_TRADE_JOURNAL_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    module = _load_module()

    rendered = repr(
        module.SupabasePaperTradeJournalConfig(
            enabled=False,
            dsn=None,
            table_name=module.DEFAULT_PAPER_TRADE_JOURNAL_DB_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperTradeJournal",
        "paper-trade-journal",
        "paper.trade_journal",
        "_paper_trade_journal",
        "paper_trade_journal_",
        "",
    ],
)
def test_table_name_must_match_simple_lowercase_identifier(
    table_name: str,
) -> None:
    module = _load_module()

    with pytest.raises(
        ValueError,
        match="table_name must be a simple lowercase identifier",
    ):
        module.SupabasePaperTradeJournalConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_trade_journal_records",
        "paper_1_trade_2_journal",
    ],
)
def test_table_name_accepts_simple_lowercase_identifier_values(
    table_name: str,
) -> None:
    module = _load_module()

    config = module.SupabasePaperTradeJournalConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name_without_echoing_value() -> None:
    module = _load_module()
    invalid_table_name = "PaperTradeJournal"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_journal_db_env(
            {
                module.PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR: invalid_table_name,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR in message
    assert invalid_table_name not in message


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    module = _load_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabasePaperTradeJournalConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn="postgresql://example.invalid/postgres",
            table_name=module.DEFAULT_PAPER_TRADE_JOURNAL_DB_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperTradeJournalConfig(
            enabled=True,
            dsn=object(),  # type: ignore[arg-type]
            table_name=module.DEFAULT_PAPER_TRADE_JOURNAL_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_module_exports_only_public_config_api() -> None:
    module = _load_module()

    assert module.__all__ == (
        "PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR",
        "PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR",
        "PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR",
        "DEFAULT_PAPER_TRADE_JOURNAL_DB_TABLE",
        "SupabasePaperTradeJournalConfig",
        "from_paper_trade_journal_db_env",
    )

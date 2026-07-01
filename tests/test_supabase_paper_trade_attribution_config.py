from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from types import ModuleType

import pytest


MODULE_NAME = "polymarket_alpha_lab.supabase_paper_trade_attribution_config"
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


def test_disabled_env_config_accepts_missing_dsn_and_default_table() -> None:
    module = _config_module()

    config = module.from_paper_trade_attribution_db_env({})

    assert config == module.SupabasePaperTradeAttributionConfig(
        enabled=False,
        dsn=None,
        table_name=module.DEFAULT_PAPER_TRADE_ATTRIBUTION_DB_TABLE,
    )


@pytest.mark.parametrize("enabled_value", ["1", "true"])
def test_enabled_env_config_reads_explicit_local_dsn_at_process_edge(
    enabled_value: str,
) -> None:
    module = _config_module()

    config = module.from_paper_trade_attribution_db_env(
        {
            module.PAPER_TRADE_ATTRIBUTION_DB_ENABLED_ENV_VAR: enabled_value,
            module.PAPER_TRADE_ATTRIBUTION_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            module.PAPER_TRADE_ATTRIBUTION_DB_TABLE_ENV_VAR: (
                "public.paper_trade_attribution_reports"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == LOCAL_POSTGRES_DSN
    assert config.table_name == "public.paper_trade_attribution_reports"


@pytest.mark.parametrize("enabled_value", ["", "0", "false"])
def test_disabled_env_config_parses_only_explicit_false_values(
    enabled_value: str,
) -> None:
    module = _config_module()

    config = module.from_paper_trade_attribution_db_env(
        {
            module.PAPER_TRADE_ATTRIBUTION_DB_ENABLED_ENV_VAR: enabled_value,
            module.PAPER_TRADE_ATTRIBUTION_DB_DSN_ENV_VAR: " ",
        },
    )

    assert config.enabled is False
    assert config.dsn is None
    assert config.table_name == module.DEFAULT_PAPER_TRADE_ATTRIBUTION_DB_TABLE


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_attribution_db_env(
            {
                module.PAPER_TRADE_ATTRIBUTION_DB_ENABLED_ENV_VAR: "true",
                module.PAPER_TRADE_ATTRIBUTION_DB_DSN_ENV_VAR: f" {secret_dsn} ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_ATTRIBUTION_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


@pytest.mark.parametrize(
    "enabled_value",
    [" TRUE ", "true ", " false", "TRUE", "False", "yes", "on", "2"],
)
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_attribution_db_env(
            {
                module.PAPER_TRADE_ATTRIBUTION_DB_ENABLED_ENV_VAR: enabled_value,
                module.PAPER_TRADE_ATTRIBUTION_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            },
        )

    assert module.PAPER_TRADE_ATTRIBUTION_DB_ENABLED_ENV_VAR in str(exc_info.value)


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

    config = module.SupabasePaperTradeAttributionConfig(
        enabled=False,
        dsn=raw_dsn,
        table_name=module.DEFAULT_PAPER_TRADE_ATTRIBUTION_DB_TABLE,
    )

    assert config.dsn is None
    assert "secret" not in repr(config).lower()


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _config_module()
    config = module.SupabasePaperTradeAttributionConfig(
        enabled=True,
        dsn=LOCAL_SECRET_POSTGRES_DSN,
        table_name=module.DEFAULT_PAPER_TRADE_ATTRIBUTION_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert LOCAL_SECRET_POSTGRES_DSN not in rendered
    assert "dsn=<redacted>" in rendered


def test_config_rejects_remote_dsn_without_echoing_secret() -> None:
    module = _config_module()
    dsn = "postgresql://sensitive-token@example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperTradeAttributionConfig(
            enabled=False,
            dsn=dsn,
            table_name=module.DEFAULT_PAPER_TRADE_ATTRIBUTION_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_ATTRIBUTION_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "sensitive-token" not in message


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperTradeAttributionReports",
        "paper-trade-attribution-reports",
        "public.attribution.reports",
        "_paper_trade_attribution_reports",
        "paper_trade_attribution_reports_",
        "a" + ("b" * 62) + "1",
        "",
    ],
)
def test_table_name_must_match_schema_safe_lower_identifier(table_name: str) -> None:
    module = _config_module()

    with pytest.raises(
        ValueError,
        match="table_name must be a lowercase identifier with optional schema prefix",
    ):
        module.SupabasePaperTradeAttributionConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_trade_attribution_reports",
        "paper_1_trade_2_attribution_reports",
        "public.paper_trade_attribution_reports",
    ],
)
def test_table_name_accepts_schema_safe_lower_identifier_values(
    table_name: str,
) -> None:
    module = _config_module()

    config = module.SupabasePaperTradeAttributionConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_table_name_accepts_63_byte_identifier_parts() -> None:
    module = _config_module()
    max_length_part = "a" + ("b" * 61) + "1"
    assert len(max_length_part) == 63

    config = module.SupabasePaperTradeAttributionConfig(
        enabled=False,
        dsn=None,
        table_name=f"public.{max_length_part}",
    )

    assert config.table_name == f"public.{max_length_part}"


def test_env_table_name_error_mentions_variable_name_without_echoing_secret() -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_attribution_db_env(
            {
                module.PAPER_TRADE_ATTRIBUTION_DB_DSN_ENV_VAR: LOCAL_SECRET_POSTGRES_DSN,
                module.PAPER_TRADE_ATTRIBUTION_DB_TABLE_ENV_VAR: "PaperReports",
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_ATTRIBUTION_DB_TABLE_ENV_VAR in message
    assert LOCAL_SECRET_POSTGRES_DSN not in message
    assert "secret" not in message.lower()


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabasePaperTradeAttributionConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn=LOCAL_POSTGRES_DSN,
            table_name=module.DEFAULT_PAPER_TRADE_ATTRIBUTION_DB_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperTradeAttributionConfig(
            enabled=True,
            dsn=object(),  # type: ignore[arg-type]
            table_name=module.DEFAULT_PAPER_TRADE_ATTRIBUTION_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_ATTRIBUTION_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_are_limited_to_constants_dataclass_and_loader() -> None:
    module = _config_module()

    assert module.__all__ == (
        "PAPER_TRADE_ATTRIBUTION_DB_DSN_ENV_VAR",
        "PAPER_TRADE_ATTRIBUTION_DB_ENABLED_ENV_VAR",
        "PAPER_TRADE_ATTRIBUTION_DB_TABLE_ENV_VAR",
        "DEFAULT_PAPER_TRADE_ATTRIBUTION_DB_TABLE",
        "SupabasePaperTradeAttributionConfig",
        "from_paper_trade_attribution_db_env",
    )

from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from pathlib import Path
from types import ModuleType

import pytest


MODULE_NAME = "polymarket_alpha_lab.supabase_paper_trade_cost_audit_config"
REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs" / "paper-trade-cost-audit-db-persistence.md"
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"


def _config_module() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} module is not implemented")
        raise


def test_disabled_env_config_accepts_missing_dsn_and_default_table() -> None:
    module = _config_module()

    config = module.from_paper_trade_cost_audit_db_env({})

    assert config == module.SupabasePaperTradeCostAuditConfig(
        enabled=False,
        dsn=None,
        table_name=module.DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE,
    )


@pytest.mark.parametrize("enabled_value", ["1", "true"])
def test_enabled_env_config_reads_explicit_dsn_at_process_edge(
    enabled_value: str,
) -> None:
    module = _config_module()
    dsn = "postgresql://example.invalid/postgres"

    config = module.from_paper_trade_cost_audit_db_env(
        {
            module.PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR: enabled_value,
            module.PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR: dsn,
            module.PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR: (
                "public.paper_trade_cost_audit_reports"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "public.paper_trade_cost_audit_reports"


@pytest.mark.parametrize("enabled_value", ["", "0", "false"])
def test_disabled_env_config_parses_only_explicit_false_values(
    enabled_value: str,
) -> None:
    module = _config_module()

    config = module.from_paper_trade_cost_audit_db_env(
        {
            module.PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR: enabled_value,
            module.PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR: " ",
        },
    )

    assert config.enabled is False
    assert config.dsn is None
    assert config.table_name == module.DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_cost_audit_db_env(
            {
                module.PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR: "true",
                module.PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR: f" {secret_dsn} ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_invalid_enabled_env_value_names_variable_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_cost_audit_db_env(
            {
                module.PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR: "yes",
                module.PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR: secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


@pytest.mark.parametrize(
    "enabled_value",
    [" TRUE ", "true ", " false", "TRUE", "False", "yes", "on", "2"],
)
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_cost_audit_db_env(
            {
                module.PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR: enabled_value,
                module.PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR: (
                    "postgresql://example.invalid/postgres"
                ),
            },
        )

    assert module.PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR in str(exc_info.value)


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

    config = module.SupabasePaperTradeCostAuditConfig(
        enabled=False,
        dsn=raw_dsn,
        table_name=module.DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE,
    )

    assert config.dsn is None
    assert "secret" not in repr(config).lower()


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _config_module()
    config = module.SupabasePaperTradeCostAuditConfig(
        enabled=True,
        dsn="postgresql://sensitive-token.example.invalid/postgres",
        table_name=module.DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    module = _config_module()

    rendered = repr(
        module.SupabasePaperTradeCostAuditConfig(
            enabled=False,
            dsn=None,
            table_name=module.DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperTradeCostAuditReports",
        "paper-trade-cost-audit-reports",
        "public.audit.reports",
        "_paper_trade_cost_audit_reports",
        "paper_trade_cost_audit_reports_",
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
        module.SupabasePaperTradeCostAuditConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_trade_cost_audit_reports",
        "paper_1_trade_2_cost_audit_reports",
        "public.paper_trade_cost_audit_reports",
    ],
)
def test_table_name_accepts_schema_safe_lower_identifier_values(
    table_name: str,
) -> None:
    module = _config_module()

    config = module.SupabasePaperTradeCostAuditConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_table_name_accepts_63_byte_identifier_parts() -> None:
    module = _config_module()
    max_length_part = "a" + ("b" * 61) + "1"
    assert len(max_length_part) == 63

    config = module.SupabasePaperTradeCostAuditConfig(
        enabled=False,
        dsn=None,
        table_name=f"public.{max_length_part}",
    )

    assert config.table_name == f"public.{max_length_part}"


def test_env_table_name_error_mentions_variable_name_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_trade_cost_audit_db_env(
            {
                module.PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR: secret_dsn,
                module.PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR: "PaperReports",
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabasePaperTradeCostAuditConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn="postgresql://example.invalid/postgres",
            table_name=module.DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperTradeCostAuditConfig(
            enabled=True,
            dsn=object(),  # type: ignore[arg-type]
            table_name=module.DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_are_limited_to_constants_dataclass_and_loader() -> None:
    module = _config_module()

    assert module.__all__ == (
        "PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR",
        "PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR",
        "PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR",
        "DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE",
        "SupabasePaperTradeCostAuditConfig",
        "from_paper_trade_cost_audit_db_env",
    )


def test_doc_states_persistence_only_env_driven_boundary() -> None:
    module = _config_module()
    assert DOC_PATH.exists(), f"doc must exist at {DOC_PATH}"

    text = " ".join(
        DOC_PATH.read_text(encoding="utf-8").lower().replace("`", "").split(),
    )

    for env_var in (
        module.PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR,
        module.PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR,
        module.PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR,
    ):
        assert env_var.lower() in text
    assert module.DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE in text
    assert "postgresql://" not in text
    assert "postgres://" not in text

    for fragment in (
        "optional supabase/postgres persistence-only surface",
        "papertradecostauditreport",
        "default-off",
        "env-driven",
        "no dsn cli flags",
        "paper_only",
        "report_only",
        "readonly",
        "payload_json is canonical and read-only",
        "paper_trade_cost_audit_reports",
        "no live trading",
        "no auth",
        "no wallet",
        "no private keys",
        "no account reads",
        "no order construction",
        "no order submission",
        "no exchange mutation",
    ):
        assert fragment in text, fragment


def test_env_example_contains_blank_paper_trade_cost_audit_db_vars() -> None:
    module = _config_module()
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    for env_var in (
        module.PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR,
        module.PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR,
        module.PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR,
    ):
        assert f"{env_var}=" in text
        assert f"{env_var}=postgresql://" not in text

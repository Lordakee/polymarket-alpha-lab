from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import ast

import pytest


ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_"
    "PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED"
)
DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_"
    "PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN"
)
TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_"
    "PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE"
)
DEFAULT_TABLE = "paper_autonomous_investment_ledger_db_history_health_reports"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_paper_autonomous_investment_ledger_db_history_health_config.py"
)
SECRET_DSN = "postgresql://worker:secret@localhost:54322/polymarket"
REMOTE_SECRET_DSN = "postgresql://worker:secret@example.invalid/polymarket"


def _module():
    import polymarket_alpha_lab.supabase_paper_autonomous_investment_ledger_db_history_health_config as config_module

    return config_module


def test_public_constants_match_expected_env_surface() -> None:
    config_module = _module()
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_store import (
        DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_REPORTS_TABLE,
    )

    assert (
        config_module.PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR
        == ENABLED_ENV_VAR
    )
    assert (
        config_module.PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR
        == DSN_ENV_VAR
    )
    assert (
        config_module.PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR
        == TABLE_ENV_VAR
    )
    assert (
        config_module.DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE
        == DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_REPORTS_TABLE
        == DEFAULT_TABLE
    )


def test_default_table_constant_is_imported_from_store_to_avoid_drift() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert (
        "DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_REPORTS_TABLE"
        in source
    )
    assert '"paper_autonomous_investment_ledger_db_history_health_reports"' not in source


def test_investment_ledger_db_history_health_config_defaults_disabled_without_dsn() -> None:
    config_module = _module()

    config = config_module.from_paper_autonomous_investment_ledger_db_history_health_db_env(
        {},
    )

    assert config.enabled is False
    assert config.dsn is None
    assert config.table_name == DEFAULT_TABLE


@pytest.mark.parametrize("enabled", ("1", "true", " TRUE "))
def test_investment_ledger_db_history_health_config_reads_enabled_dsn_and_table(
    enabled: str,
) -> None:
    config_module = _module()

    config = config_module.from_paper_autonomous_investment_ledger_db_history_health_db_env(
        {
            ENABLED_ENV_VAR: enabled,
            DSN_ENV_VAR: SECRET_DSN,
            TABLE_ENV_VAR: "audit.paper_autonomous_investment_ledger_db_history_health_reports",
        },
    )

    assert config.enabled is True
    assert config.dsn == SECRET_DSN
    assert (
        config.table_name
        == "audit.paper_autonomous_investment_ledger_db_history_health_reports"
    )


def test_investment_ledger_db_history_health_config_rejects_remote_dsn_without_echoing_secret() -> None:
    config_module = _module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_investment_ledger_db_history_health_db_env(
            {
                ENABLED_ENV_VAR: "false",
                DSN_ENV_VAR: REMOTE_SECRET_DSN,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert REMOTE_SECRET_DSN not in message
    assert "secret" not in message.lower()


def test_investment_ledger_db_history_health_config_requires_dsn_when_enabled() -> None:
    config_module = _module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_investment_ledger_db_history_health_db_env(
            {
                ENABLED_ENV_VAR: "true",
            },
        )

    assert DSN_ENV_VAR in str(exc_info.value)
    assert "must be set when DB-history health DB is enabled" in str(exc_info.value)


@pytest.mark.parametrize(
    ("enabled_value", "expected_enabled"),
    (
        ("", False),
        ("0", False),
        ("false", False),
        (" FALSE ", False),
        ("1", True),
        ("true", True),
        (" TRUE ", True),
    ),
)
def test_investment_ledger_db_history_health_config_accepts_only_strict_enabled_values(
    enabled_value: str,
    expected_enabled: bool,
) -> None:
    config_module = _module()

    config = config_module.from_paper_autonomous_investment_ledger_db_history_health_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: SECRET_DSN,
            },
        )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", ("yes", "on", "2"))
def test_investment_ledger_db_history_health_config_rejects_non_strict_enabled_values(
    enabled_value: str,
) -> None:
    config_module = _module()

    with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
        config_module.from_paper_autonomous_investment_ledger_db_history_health_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: SECRET_DSN,
            },
        )


@pytest.mark.parametrize(
    "raw_dsn",
    (
        None,
        "",
        " ",
        "\t\n",
        f" {SECRET_DSN}",
        f"{SECRET_DSN} ",
    ),
)
def test_investment_ledger_db_history_health_dsn_normalizes_absent_blank_or_padded_values_to_none(
    raw_dsn: str | None,
) -> None:
    config_module = _module()

    config = config_module.SupabasePaperAutonomousInvestmentLedgerDbHistoryHealthConfig(
        enabled=False,
        dsn=raw_dsn,
        table_name=DEFAULT_TABLE,
    )

    assert config.dsn is None
    assert "secret" not in repr(config).lower()


def test_investment_ledger_db_history_health_enabled_padded_dsn_error_omits_secret() -> None:
    config_module = _module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_investment_ledger_db_history_health_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: f" {SECRET_DSN} ",
                "UNRELATED_SECRET": SECRET_DSN,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert SECRET_DSN not in message
    assert "secret" not in message.lower()


@pytest.mark.parametrize(
    "table_name",
    (
        "PaperAutonomousInvestmentLedgerDbHistoryHealthReports",
        "audit..paper_autonomous_investment_ledger_db_history_health_reports",
        "_paper_autonomous_investment_ledger_db_history_health_reports",
        "paper_autonomous_investment_ledger_db_history_health_reports_",
        "audit.paper_autonomous_investment_ledger_db_history_health_reports.extra",
    ),
)
def test_investment_ledger_db_history_health_config_rejects_invalid_table_names(
    table_name: str,
) -> None:
    config_module = _module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_investment_ledger_db_history_health_db_env(
            {
                TABLE_ENV_VAR: table_name,
                DSN_ENV_VAR: SECRET_DSN,
            },
        )

    message = str(exc_info.value)
    assert TABLE_ENV_VAR in message
    assert "lowercase identifier with optional schema prefix" in message
    assert SECRET_DSN not in message


@pytest.mark.parametrize(
    "table_name",
    (
        "a",
        "a0",
        DEFAULT_TABLE,
        "audit.paper_autonomous_investment_ledger_db_history_health_reports",
        "health_1_archive_2",
    ),
)
def test_investment_ledger_db_history_health_config_accepts_valid_table_names(
    table_name: str,
) -> None:
    config_module = _module()

    config = config_module.SupabasePaperAutonomousInvestmentLedgerDbHistoryHealthConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_investment_ledger_db_history_health_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _module()
    config = config_module.SupabasePaperAutonomousInvestmentLedgerDbHistoryHealthConfig(
        enabled=True,
        dsn=SECRET_DSN,
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "worker:secret" not in rendered
    assert SECRET_DSN not in rendered
    assert "dsn=<redacted>" in rendered


def test_investment_ledger_db_history_health_config_repr_redacts_dsn() -> None:
    config_module = _module()

    config = config_module.from_paper_autonomous_investment_ledger_db_history_health_db_env(
        {
            ENABLED_ENV_VAR: "true",
            DSN_ENV_VAR: SECRET_DSN,
        },
    )

    text = repr(config)

    assert "dsn=<redacted>" in text
    assert SECRET_DSN not in text


def test_investment_ledger_db_history_health_config_rejects_non_bool_enabled_flag() -> None:
    config_module = _module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        config_module.SupabasePaperAutonomousInvestmentLedgerDbHistoryHealthConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn=SECRET_DSN,
            table_name=DEFAULT_TABLE,
        )


def test_investment_ledger_db_history_health_config_rejects_non_string_dsn_without_echoing_value() -> None:
    config_module = _module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabasePaperAutonomousInvestmentLedgerDbHistoryHealthConfig(
            enabled=True,
            dsn=object(),  # type: ignore[arg-type]
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_investment_ledger_db_history_health_config_all_exports_are_explicit() -> None:
    config_module = _module()

    expected_exports = (
        "DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE",
        "PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR",
        "PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR",
        "PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR",
        "SupabasePaperAutonomousInvestmentLedgerDbHistoryHealthConfig",
        "from_paper_autonomous_investment_ledger_db_history_health_db_env",
    )

    assert config_module.__all__ == expected_exports
    for export in expected_exports:
        assert hasattr(config_module, export)
    assert "_TABLE_NAME_ERROR" not in config_module.__all__
    text = MODULE_PATH.read_text(encoding="utf-8")
    assert "POLYMARKET_ALPHA_LAB_" in text
    assert "PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED" in text
    assert "PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN" in text
    assert "PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE" in text


def test_investment_ledger_db_history_health_config_has_no_live_driver_or_network_imports() -> None:
    module = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not (
        imported_roots
        & {"psycopg", "requests", "httpx", "urllib", "supabase", "web3"}
    )

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import ast

import pytest


ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_"
    "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED"
)
DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_"
    "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN"
)
TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_"
    "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE"
)
DEFAULT_TABLE = "paper_autonomous_allocation_proposal_db_history_health_reports"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_paper_autonomous_allocation_proposal_db_history_health_config.py"
)


def _module():
    import polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_db_history_health_config as config_module

    return config_module


def test_public_constants_match_expected_env_surface() -> None:
    config_module = _module()
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE,
    )

    assert (
        config_module.PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR
        == ENABLED_ENV_VAR
    )
    assert (
        config_module.PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR
        == DSN_ENV_VAR
    )
    assert (
        config_module.PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR
        == TABLE_ENV_VAR
    )
    assert (
        config_module.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE
        == DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE
        == DEFAULT_TABLE
    )


def test_default_table_constant_is_imported_from_store_to_avoid_drift() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert (
        "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE"
        in source
    )
    assert '"paper_autonomous_allocation_proposal_db_history_health_reports"' not in source


def test_disabled_env_config_accepts_missing_dsn() -> None:
    config_module = _module()

    config = (
        config_module.from_paper_autonomous_allocation_proposal_db_history_health_db_env(
            {},
        )
    )

    assert config == (
        config_module.SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_TABLE,
        )
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    config_module = _module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_allocation_proposal_db_history_health_db_env(
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
    config_module = _module()
    dsn = "postgresql://example.invalid/postgres"

    config = (
        config_module.from_paper_autonomous_allocation_proposal_db_history_health_db_env(
            {
                ENABLED_ENV_VAR: "1",
                DSN_ENV_VAR: dsn,
                TABLE_ENV_VAR: "audit.db_history_health_archive",
            },
        )
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "audit.db_history_health_archive"


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
    config_module = _module()

    config = (
        config_module.from_paper_autonomous_allocation_proposal_db_history_health_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: "postgresql://example.invalid/postgres",
            },
        )
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", ["yes", "on", "2"])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    config_module = _module()

    with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
        config_module.from_paper_autonomous_allocation_proposal_db_history_health_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: "postgresql://example.invalid/postgres",
            },
        )


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _module()
    config = (
        config_module.SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig(
            enabled=True,
            dsn="postgresql://sensitive-token.example.invalid/postgres",
            table_name=DEFAULT_TABLE,
        )
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered
    assert DEFAULT_TABLE in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperReports",
        "paper-reports",
        "paper..reports",
        "paper.reports.extra",
        "_paper_reports",
        "paper_reports_",
        "",
    ],
)
def test_table_name_must_match_store_lowercase_identifier_contract(
    table_name: str,
) -> None:
    config_module = _module()

    with pytest.raises(
        ValueError,
        match="table_name must be a lowercase identifier with optional schema prefix",
    ):
        config_module.SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a",
        "a0",
        "db_history_health_archive",
        "audit.db_history_health_archive",
        "health_1_archive_2",
    ],
)
def test_table_name_accepts_lowercase_identifier_values(
    table_name: str,
) -> None:
    config_module = _module()

    config = config_module.SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_table_name_accepts_postgres_identifier_at_length_limit() -> None:
    config_module = _module()
    table_name = "a" * 63

    config = config_module.SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_table_name_rejects_postgres_identifier_over_length_limit() -> None:
    config_module = _module()

    with pytest.raises(
        ValueError,
        match="table_name must be a lowercase identifier with optional schema prefix",
    ):
        config_module.SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig(
            enabled=False,
            dsn=None,
            table_name="a" * 64,
        )


def test_env_table_name_error_mentions_variable_name() -> None:
    config_module = _module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_allocation_proposal_db_history_health_db_env(
            {TABLE_ENV_VAR: "PaperReports"},
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    config_module = _module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        config_module.SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig(
            enabled=1,
            dsn="postgresql://example.invalid/postgres",
            table_name=DEFAULT_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    config_module = _module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig(
            enabled=True,
            dsn=object(),
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_include_constants_config_and_loader() -> None:
    config_module = _module()

    assert config_module.__all__ == (
        "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE",
        "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR",
        "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR",
        "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR",
        "SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig",
        "from_paper_autonomous_allocation_proposal_db_history_health_db_env",
    )


def test_config_module_has_no_live_driver_or_network_imports() -> None:
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

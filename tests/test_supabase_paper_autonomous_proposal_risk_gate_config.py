from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from pathlib import Path
from types import ModuleType

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "supabase_paper_autonomous_proposal_risk_gate_config"
)
ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_ENABLED"
)
DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_DSN"
)
TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_TABLE"
)
DEFAULT_TABLE = "paper_autonomous_proposal_risk_gate_reports"
LOCAL_SUPABASE_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
CONFIG_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_paper_autonomous_proposal_risk_gate_config.py"
)


def _config_module() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} module is not implemented")
        raise


def test_public_constants_match_expected_env_surface_and_store_default() -> None:
    module = _config_module()
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE,
    )

    assert (
        module.PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_ENABLED_ENV_VAR
        == ENABLED_ENV_VAR
    )
    assert (
        module.PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_DSN_ENV_VAR
        == DSN_ENV_VAR
    )
    assert (
        module.PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_TABLE_ENV_VAR
        == TABLE_ENV_VAR
    )
    assert (
        module.DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_TABLE
        == DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE
        == DEFAULT_TABLE
    )


def test_default_table_constant_is_imported_from_store_to_avoid_drift() -> None:
    assert CONFIG_SOURCE.exists(), f"missing config source: {CONFIG_SOURCE}"
    source = CONFIG_SOURCE.read_text(encoding="utf-8")

    assert "DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE" in source
    assert '"paper_autonomous_proposal_risk_gate_reports"' not in source


def test_config_module_is_env_only_without_runtime_db_or_file_store_surfaces() -> None:
    assert CONFIG_SOURCE.exists(), f"missing config source: {CONFIG_SOURCE}"
    source = CONFIG_SOURCE.read_text(encoding="utf-8")

    forbidden_tokens = (
        "psycopg",
        "connect(",
        "cursor(",
        "execute(",
        "insert_paper_autonomous_proposal_risk_gate",
        "load_paper_autonomous_proposal_risk_gate",
        "jsonl",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_disabled_env_config_accepts_missing_dsn_and_default_table() -> None:
    module = _config_module()

    config = module.from_paper_autonomous_proposal_risk_gate_db_env({})

    assert config == module.SupabasePaperAutonomousProposalRiskGateConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


@pytest.mark.parametrize("enabled_value", ["1", "true", " TRUE "])
def test_enabled_env_config_reads_explicit_dsn_at_process_edge(
    enabled_value: str,
) -> None:
    module = _config_module()

    config = module.from_paper_autonomous_proposal_risk_gate_db_env(
        {
            ENABLED_ENV_VAR: enabled_value,
            DSN_ENV_VAR: LOCAL_SUPABASE_DSN,
            TABLE_ENV_VAR: "audit.paper_autonomous_proposal_risk_gate_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == LOCAL_SUPABASE_DSN
    assert config.table_name == "audit.paper_autonomous_proposal_risk_gate_archive"


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
    module = _config_module()

    config = module.from_paper_autonomous_proposal_risk_gate_db_env(
        {
            ENABLED_ENV_VAR: enabled_value,
            DSN_ENV_VAR: LOCAL_SUPABASE_DSN,
        },
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://postgres:postgres@localhost:54322/postgres",
        "postgres://postgres:postgres@localhost:54322/postgres",
        "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
        "postgresql://postgres:postgres@[::1]:54322/postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
        "host=/var/run/postgresql port=54322 dbname=postgres user=postgres",
    ],
)
def test_enabled_env_config_accepts_current_node_local_postgres_dsns(
    dsn: str,
) -> None:
    module = _config_module()

    config = module.from_paper_autonomous_proposal_risk_gate_db_env(
        {
            ENABLED_ENV_VAR: "true",
            DSN_ENV_VAR: dsn,
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == DEFAULT_TABLE


@pytest.mark.parametrize(
    "remote_dsn",
    [
        "postgresql://postgres:super-secret@hosted.example.invalid:5432/postgres",
        "postgres://postgres:super-secret@hosted.example.invalid:5432/postgres",
        (
            "host=hosted.example.invalid port=5432 dbname=postgres "
            "user=postgres password=super-secret"
        ),
    ],
)
def test_enabled_env_config_rejects_remote_postgres_hosts_without_echoing_secret(
    remote_dsn: str,
) -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_autonomous_proposal_risk_gate_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: remote_dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert remote_dsn not in message
    assert "hosted.example.invalid" not in message
    assert "super-secret" not in message


@pytest.mark.parametrize("enabled_value", ["yes", "on", "2", "truthy"])
def test_enabled_env_config_rejects_non_strict_values_without_echoing_dsn(
    enabled_value: str,
) -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_autonomous_proposal_risk_gate_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert ENABLED_ENV_VAR in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message


@pytest.mark.parametrize("dsn_value", [None, "", " ", "\t\n"])
def test_enabled_env_config_requires_dsn_without_echoing_secret(
    dsn_value: str | None,
) -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_autonomous_proposal_risk_gate_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: dsn_value,
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message


@pytest.mark.parametrize(
    "dsn_value",
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
    dsn_value: str | None,
) -> None:
    module = _config_module()

    config = module.SupabasePaperAutonomousProposalRiskGateConfig(
        enabled=False,
        dsn=dsn_value,
        table_name=DEFAULT_TABLE,
    )

    assert config.dsn is None
    assert "sensitive-token" not in repr(config)


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _config_module()
    config = module.SupabasePaperAutonomousProposalRiskGateConfig(
        enabled=True,
        dsn="postgresql://sensitive-token@localhost/postgres",
        table_name=DEFAULT_TABLE,
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
    module = _config_module()

    with pytest.raises(
        ValueError,
        match="table_name must be a lowercase identifier with optional schema prefix",
    ):
        module.SupabasePaperAutonomousProposalRiskGateConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a",
        "a0",
        "paper_autonomous_proposal_risk_gate_archive",
        "audit.paper_autonomous_proposal_risk_gate_archive",
        "proposal_1_risk_gate_2",
    ],
)
def test_table_name_accepts_lowercase_identifier_values(
    table_name: str,
) -> None:
    module = _config_module()

    config = module.SupabasePaperAutonomousProposalRiskGateConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_table_name_accepts_postgres_identifier_at_length_limit() -> None:
    module = _config_module()
    table_name = "a" * 63

    config = module.SupabasePaperAutonomousProposalRiskGateConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_table_name_rejects_postgres_identifier_over_length_limit() -> None:
    module = _config_module()

    with pytest.raises(
        ValueError,
        match="table_name must be a lowercase identifier with optional schema prefix",
    ):
        module.SupabasePaperAutonomousProposalRiskGateConfig(
            enabled=False,
            dsn=None,
            table_name="a" * 64,
        )


def test_env_table_name_error_mentions_variable_name() -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_autonomous_proposal_risk_gate_db_env(
            {TABLE_ENV_VAR: "PaperReports"},
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabasePaperAutonomousProposalRiskGateConfig(
            enabled=1,
            dsn=LOCAL_SUPABASE_DSN,
            table_name=DEFAULT_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperAutonomousProposalRiskGateConfig(
            enabled=True,
            dsn=object(),
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_include_constants_config_and_loader() -> None:
    module = _config_module()

    assert module.__all__ == (
        "DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_TABLE",
        "PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_DSN_ENV_VAR",
        "PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_ENABLED_ENV_VAR",
        "PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_DB_TABLE_ENV_VAR",
        "SupabasePaperAutonomousProposalRiskGateConfig",
        "from_paper_autonomous_proposal_risk_gate_db_env",
    )

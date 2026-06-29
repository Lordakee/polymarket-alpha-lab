from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from types import ModuleType

import pytest


MODULE_NAME = "polymarket_alpha_lab.supabase_paper_autonomous_readiness_gate_config"
ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_GATE_DB_ENABLED"
)
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_GATE_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_GATE_DB_TABLE"
DEFAULT_TABLE = "paper_autonomous_readiness_gate_reports"
LOCAL_SUPABASE_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


def _config_module() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} module is not implemented")
        raise


def test_public_constants_match_expected_env_surface_and_store_default() -> None:
    module = _config_module()
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE,
    )

    assert (
        module.PAPER_AUTONOMOUS_READINESS_GATE_DB_ENABLED_ENV_VAR
        == ENABLED_ENV_VAR
    )
    assert module.PAPER_AUTONOMOUS_READINESS_GATE_DB_DSN_ENV_VAR == DSN_ENV_VAR
    assert module.PAPER_AUTONOMOUS_READINESS_GATE_DB_TABLE_ENV_VAR == TABLE_ENV_VAR
    assert (
        module.DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_DB_TABLE
        == DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE
        == DEFAULT_TABLE
    )


def test_disabled_env_config_accepts_missing_dsn_and_default_table() -> None:
    module = _config_module()

    config = module.from_paper_autonomous_readiness_gate_db_env({})

    assert config == module.SupabasePaperAutonomousReadinessGateConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


@pytest.mark.parametrize("enabled_value", ["1", "true", " TRUE "])
def test_enabled_env_config_reads_explicit_dsn_at_process_edge(
    enabled_value: str,
) -> None:
    module = _config_module()
    dsn = LOCAL_SUPABASE_DSN

    config = module.from_paper_autonomous_readiness_gate_db_env(
        {
            ENABLED_ENV_VAR: enabled_value,
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "paper_autonomous_readiness_gate_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_autonomous_readiness_gate_archive"


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

    config = module.from_paper_autonomous_readiness_gate_db_env(
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
    ids=[
        "localhost-supabase-port",
        "localhost-supabase-port-postgres-scheme",
        "ipv4-loopback-supabase-port",
        "ipv6-loopback-supabase-port",
        "unix-socket-uri-query",
        "unix-socket-keyword-dsn",
    ],
)
def test_enabled_env_config_accepts_current_node_local_postgres_dsns(
    dsn: str,
) -> None:
    module = _config_module()

    config = module.from_paper_autonomous_readiness_gate_db_env(
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
    ids=["postgresql-uri", "postgres-uri", "keyword-dsn"],
)
def test_enabled_env_config_rejects_remote_postgres_hosts_without_echoing_secret(
    remote_dsn: str,
) -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_autonomous_readiness_gate_db_env(
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
        module.from_paper_autonomous_readiness_gate_db_env(
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
        module.from_paper_autonomous_readiness_gate_db_env(
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


def test_padded_enabled_dsn_is_rejected_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_autonomous_readiness_gate_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: f" {secret_dsn} ",
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

    config = module.SupabasePaperAutonomousReadinessGateConfig(
        enabled=False,
        dsn=dsn_value,
        table_name=DEFAULT_TABLE,
    )

    assert config.dsn is None
    assert "sensitive-token" not in repr(config)


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _config_module()
    config = module.SupabasePaperAutonomousReadinessGateConfig(
        enabled=True,
        dsn="postgresql://postgres:sensitive-token@localhost:54322/postgres",
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered
    assert DEFAULT_TABLE in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    module = _config_module()

    rendered = repr(
        module.SupabasePaperAutonomousReadinessGateConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


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
def test_table_name_must_match_store_simple_lowercase_identifier(
    table_name: str,
) -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        module.SupabasePaperAutonomousReadinessGateConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_autonomous_readiness_gate_reports",
        "paper_autonomous_readiness_gate_archive",
        "gate_1_archive_2",
    ],
)
def test_table_name_accepts_simple_lowercase_identifier_values(
    table_name: str,
) -> None:
    module = _config_module()

    config = module.SupabasePaperAutonomousReadinessGateConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_autonomous_readiness_gate_db_env(
            {
                DSN_ENV_VAR: secret_dsn,
                TABLE_ENV_VAR: "PaperReports",
            },
        )

    message = str(exc_info.value)
    assert TABLE_ENV_VAR in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabasePaperAutonomousReadinessGateConfig(
            enabled=1,
            dsn=LOCAL_SUPABASE_DSN,
            table_name=DEFAULT_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperAutonomousReadinessGateConfig(
            enabled=True,
            dsn=object(),
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_are_limited_to_constants_dataclass_and_loader() -> None:
    module = _config_module()

    assert module.__all__ == (
        "DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_DB_TABLE",
        "PAPER_AUTONOMOUS_READINESS_GATE_DB_DSN_ENV_VAR",
        "PAPER_AUTONOMOUS_READINESS_GATE_DB_ENABLED_ENV_VAR",
        "PAPER_AUTONOMOUS_READINESS_GATE_DB_TABLE_ENV_VAR",
        "SupabasePaperAutonomousReadinessGateConfig",
        "from_paper_autonomous_readiness_gate_db_env",
    )

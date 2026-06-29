from __future__ import annotations

from dataclasses import FrozenInstanceError
import importlib
from types import ModuleType

import pytest


MODULE_NAME = "polymarket_alpha_lab.supabase_paper_nav_snapshot_config"
LOCAL_POSTGRES_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


def _config_module() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} module is not implemented")
        raise


def test_disabled_env_config_accepts_missing_dsn_and_default_table() -> None:
    module = _config_module()

    config = module.from_paper_nav_snapshot_db_env({})

    assert config == module.SupabasePaperNavSnapshotConfig(
        enabled=False,
        dsn=None,
        table_name=module.DEFAULT_PAPER_NAV_SNAPSHOT_DB_TABLE,
    )


@pytest.mark.parametrize("enabled_value", ["1", "true", " TRUE "])
def test_enabled_env_config_reads_explicit_dsn_at_process_edge(
    enabled_value: str,
) -> None:
    module = _config_module()
    dsn = LOCAL_POSTGRES_DSN

    config = module.from_paper_nav_snapshot_db_env(
        {
            module.PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR: enabled_value,
            module.PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR: dsn,
            module.PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR: "paper_nav_snapshot_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_nav_snapshot_archive"


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://postgres:postgres@localhost:54322/postgres",
        "postgres://postgres:postgres@127.0.0.1:54322/postgres",
        "host=localhost port=54322 dbname=postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
        "host=/var/run/postgresql dbname=postgres",
    ],
)
def test_config_accepts_local_postgres_dsn_shapes(dsn: str) -> None:
    module = _config_module()

    config = module.SupabasePaperNavSnapshotConfig(
        enabled=False,
        dsn=dsn,
        table_name=module.DEFAULT_PAPER_NAV_SNAPSHOT_DB_TABLE,
    )

    assert config.dsn == dsn


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://topsecret@example.invalid/postgres",
        "postgres://db.example.com/postgres",
        "postgresql://localhost:54322/postgres?hostaddr=127.0.0.1",
        "host=example.invalid dbname=postgres",
    ],
)
def test_config_rejects_remote_or_unsafe_dsn_without_echoing_secret(
    dsn: str,
) -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperNavSnapshotConfig(
            enabled=False,
            dsn=dsn,
            table_name=module.DEFAULT_PAPER_NAV_SNAPSHOT_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "topsecret" not in message


@pytest.mark.parametrize("enabled_value", ["", "0", "false", " FALSE "])
def test_disabled_env_config_parses_only_explicit_false_values(
    enabled_value: str,
) -> None:
    module = _config_module()

    config = module.from_paper_nav_snapshot_db_env(
        {
            module.PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR: enabled_value,
            module.PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR: " ",
        },
    )

    assert config.enabled is False
    assert config.dsn is None
    assert config.table_name == module.DEFAULT_PAPER_NAV_SNAPSHOT_DB_TABLE


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token:postgres@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_nav_snapshot_db_env(
            {
                module.PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR: "true",
                module.PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR: f" {secret_dsn} ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_invalid_enabled_env_value_names_variable_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token:postgres@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_nav_snapshot_db_env(
            {
                module.PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR: "yes",
                module.PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR: secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


@pytest.mark.parametrize(
    "raw_dsn",
    [
        None,
        "",
        " ",
        "\t\n",
        " postgresql://sensitive-token:postgres@localhost:54322/postgres",
        "postgresql://sensitive-token:postgres@localhost:54322/postgres ",
    ],
)
def test_dsn_normalizes_absent_blank_or_padded_values_to_none(
    raw_dsn: str | None,
) -> None:
    module = _config_module()

    config = module.SupabasePaperNavSnapshotConfig(
        enabled=False,
        dsn=raw_dsn,
        table_name=module.DEFAULT_PAPER_NAV_SNAPSHOT_DB_TABLE,
    )

    assert config.dsn is None
    assert "secret" not in repr(config).lower()


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _config_module()
    config = module.SupabasePaperNavSnapshotConfig(
        enabled=True,
        dsn="postgresql://sensitive-token:postgres@localhost:54322/postgres",
        table_name=module.DEFAULT_PAPER_NAV_SNAPSHOT_DB_TABLE,
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
        module.SupabasePaperNavSnapshotConfig(
            enabled=False,
            dsn=None,
            table_name=module.DEFAULT_PAPER_NAV_SNAPSHOT_DB_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperSnapshots",
        "paper-snapshots",
        "paper.snapshots",
        "_paper_nav_snapshots",
        "paper_nav_snapshots_",
        "",
    ],
)
def test_table_name_must_match_simple_lowercase_identifier(table_name: str) -> None:
    module = _config_module()

    with pytest.raises(
        ValueError,
        match="table_name must be a simple lowercase identifier",
    ):
        module.SupabasePaperNavSnapshotConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_nav_snapshots",
        "paper_1_nav_2_snapshots",
    ],
)
def test_table_name_accepts_simple_lowercase_identifier_values(
    table_name: str,
) -> None:
    module = _config_module()

    config = module.SupabasePaperNavSnapshotConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token:postgres@localhost:54322/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_nav_snapshot_db_env(
            {
                module.PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR: secret_dsn,
                module.PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR: "PaperSnapshots",
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabasePaperNavSnapshotConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn=LOCAL_POSTGRES_DSN,
            table_name=module.DEFAULT_PAPER_NAV_SNAPSHOT_DB_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperNavSnapshotConfig(
            enabled=True,
            dsn=object(),  # type: ignore[arg-type]
            table_name=module.DEFAULT_PAPER_NAV_SNAPSHOT_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_are_limited_to_constants_dataclass_and_loader() -> None:
    module = _config_module()

    assert module.__all__ == (
        "PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR",
        "PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR",
        "PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR",
        "DEFAULT_PAPER_NAV_SNAPSHOT_DB_TABLE",
        "SupabasePaperNavSnapshotConfig",
        "from_paper_nav_snapshot_db_env",
    )

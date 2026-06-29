from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from polymarket_alpha_lab.paper_order_lifecycle_store import (
    DEFAULT_PAPER_ORDER_LIFECYCLE_RECORDS_TABLE,
)
from polymarket_alpha_lab.supabase_paper_execution_pipeline_config import (
    DEFAULT_PAPER_EXECUTION_PIPELINE_DB_TABLE,
    PAPER_EXECUTION_PIPELINE_DB_DSN_ENV_VAR,
    PAPER_EXECUTION_PIPELINE_DB_ENABLED_ENV_VAR,
    PAPER_EXECUTION_PIPELINE_DB_TABLE_ENV_VAR,
    SupabasePaperExecutionPipelineConfig,
    from_paper_execution_pipeline_db_env,
)


LOCAL_POSTGRES_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


def test_default_table_matches_lifecycle_store_table() -> None:
    assert (
        DEFAULT_PAPER_EXECUTION_PIPELINE_DB_TABLE
        == DEFAULT_PAPER_ORDER_LIFECYCLE_RECORDS_TABLE
    )
    assert from_paper_execution_pipeline_db_env({}).table_name == (
        DEFAULT_PAPER_ORDER_LIFECYCLE_RECORDS_TABLE
    )


def test_enabled_config_requires_dsn() -> None:
    with pytest.raises(ValueError, match="dsn is required"):
        SupabasePaperExecutionPipelineConfig(
            enabled=True,
            dsn=None,
            table_name=DEFAULT_PAPER_EXECUTION_PIPELINE_DB_TABLE,
        )


def test_from_env_reads_enabled_dsn_and_table() -> None:
    config = from_paper_execution_pipeline_db_env(
        {
            PAPER_EXECUTION_PIPELINE_DB_ENABLED_ENV_VAR: "true",
            PAPER_EXECUTION_PIPELINE_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            PAPER_EXECUTION_PIPELINE_DB_TABLE_ENV_VAR: "paper_execution_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == LOCAL_POSTGRES_DSN
    assert config.table_name == "paper_execution_archive"


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
    config = SupabasePaperExecutionPipelineConfig(
        enabled=False,
        dsn=dsn,
        table_name=DEFAULT_PAPER_EXECUTION_PIPELINE_DB_TABLE,
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
    with pytest.raises(ValueError) as exc_info:
        SupabasePaperExecutionPipelineConfig(
            enabled=False,
            dsn=dsn,
            table_name=DEFAULT_PAPER_EXECUTION_PIPELINE_DB_TABLE,
        )

    message = str(exc_info.value)
    assert PAPER_EXECUTION_PIPELINE_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "topsecret" not in message


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config = SupabasePaperExecutionPipelineConfig(
        enabled=True,
        dsn="postgresql://topsecret:postgres@localhost:54322/postgres",
        table_name=DEFAULT_PAPER_EXECUTION_PIPELINE_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=***" in rendered


def test_from_env_rejects_bad_enabled_value() -> None:
    with pytest.raises(ValueError, match="must be true or false"):
        from_paper_execution_pipeline_db_env(
            {PAPER_EXECUTION_PIPELINE_DB_ENABLED_ENV_VAR: "maybe"},
        )


def test_from_env_rejects_bad_table_name() -> None:
    with pytest.raises(ValueError, match="must be a simple lowercase identifier"):
        from_paper_execution_pipeline_db_env(
            {
                PAPER_EXECUTION_PIPELINE_DB_TABLE_ENV_VAR: "bad-table-name",
            },
        )

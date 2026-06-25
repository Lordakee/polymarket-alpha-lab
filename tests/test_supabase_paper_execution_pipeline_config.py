from __future__ import annotations

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
            PAPER_EXECUTION_PIPELINE_DB_DSN_ENV_VAR: "postgresql://example.invalid/db",
            PAPER_EXECUTION_PIPELINE_DB_TABLE_ENV_VAR: "paper_execution_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == "postgresql://example.invalid/db"
    assert config.table_name == "paper_execution_archive"


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

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from polymarket_alpha_lab.supabase_cycle_snapshot_config import (
    CYCLE_SNAPSHOT_DB_DSN_ENV_VAR,
    CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR,
    CYCLE_SNAPSHOT_DB_TABLE_ENV_VAR,
    DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
    SupabaseCycleSnapshotConfig,
    from_cycle_snapshot_db_env,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_config import (
    ACTION_GATED_QUEUE_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_history_config import (
    ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_local_observability_trends_config import (
    LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR,
    LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR,
    LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_trade_cost_audit_config import (
    PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR,
    PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR,
    PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_outcome_tracking_config import (
    OUTCOME_TRACKING_DB_DSN_ENV_VAR,
    OUTCOME_TRACKING_DB_ENABLED_ENV_VAR,
    OUTCOME_TRACKING_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_nav_snapshot_config import (
    PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR,
    PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR,
    PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_trade_journal_config import (
    PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR,
    PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR,
    PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_strategy_risk_audit_config import (
    STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR,
    STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR,
    STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR,
)


ENV_EXAMPLE_PATH = Path(".env.example")


def test_disabled_env_config_accepts_missing_dsn() -> None:
    config = from_cycle_snapshot_db_env({})

    assert config == SupabaseCycleSnapshotConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        from_cycle_snapshot_db_env(
            {
                CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR: "true",
                CYCLE_SNAPSHOT_DB_DSN_ENV_VAR: " ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert CYCLE_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message


def test_enabled_config_requires_dsn_without_echoing_secret() -> None:
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        SupabaseCycleSnapshotConfig(
            enabled=True,
            dsn=None,
            table_name=DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
        )

    message = str(exc_info.value)
    assert CYCLE_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message


def test_enabled_env_config_reads_explicit_dsn_at_process_edge() -> None:
    dsn = "postgresql://example.invalid/postgres"

    config = from_cycle_snapshot_db_env(
        {
            CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR: "1",
            CYCLE_SNAPSHOT_DB_DSN_ENV_VAR: dsn,
            CYCLE_SNAPSHOT_DB_TABLE_ENV_VAR: "paper_cycle_snapshots",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_cycle_snapshots"


def test_padded_enabled_dsn_is_rejected_without_echoing_secret() -> None:
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        from_cycle_snapshot_db_env(
            {
                CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR: "true",
                CYCLE_SNAPSHOT_DB_DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert CYCLE_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config = SupabaseCycleSnapshotConfig(
        enabled=True,
        dsn="postgresql://sensitive-token.example.invalid/postgres",
        table_name=DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    rendered = repr(
        SupabaseCycleSnapshotConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    with pytest.raises(ValueError) as exc_info:
        SupabaseCycleSnapshotConfig(
            enabled=True,
            dsn=object(),  # type: ignore[arg-type]
            table_name=DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
        )

    message = str(exc_info.value)
    assert CYCLE_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperSnapshots",
        "paper-snapshots",
        "paper.snapshots",
        "_paper_snapshots",
        "paper_snapshots_",
        "",
    ],
)
def test_table_name_must_match_store_simple_lowercase_identifier(
    table_name: str,
) -> None:
    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        SupabaseCycleSnapshotConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_recommendation_cycle_snapshots",
        "paper_1_cycle_2_snapshots",
    ],
)
def test_table_name_accepts_store_simple_lowercase_identifier_values(
    table_name: str,
) -> None:
    config = SupabaseCycleSnapshotConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_cycle_snapshot_db_env(
            {
                CYCLE_SNAPSHOT_DB_TABLE_ENV_VAR: "PaperSnapshots",
            },
        )

    assert CYCLE_SNAPSHOT_DB_TABLE_ENV_VAR in str(exc_info.value)


def test_enabled_flag_is_explicit_and_strict() -> None:
    with pytest.raises(ValueError, match=CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR):
        from_cycle_snapshot_db_env(
            {
                CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR: "yes",
                CYCLE_SNAPSHOT_DB_DSN_ENV_VAR: "postgresql://example.test/postgres",
            },
        )


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    with pytest.raises(ValueError, match="enabled must be a bool"):
        SupabaseCycleSnapshotConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn="postgresql://example.test/postgres",
            table_name=DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
        )


def test_env_example_documents_supported_db_variable_names_only() -> None:
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    expected_lines = [
        f"{CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR}=",
        f"{CYCLE_SNAPSHOT_DB_DSN_ENV_VAR}=",
        f"{CYCLE_SNAPSHOT_DB_TABLE_ENV_VAR}=",
        f"{PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR}=",
        f"{PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR}=",
        f"{PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR}=",
        f"{PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR}=",
        f"{OUTCOME_TRACKING_DB_ENABLED_ENV_VAR}=",
        f"{OUTCOME_TRACKING_DB_DSN_ENV_VAR}=",
        f"{OUTCOME_TRACKING_DB_TABLE_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DB_DSN_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR}=",
        f"{LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR}=",
        f"{LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR}=",
        f"{LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR}=",
        f"{STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR}=",
        f"{STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR}=",
        f"{STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR}=",
        f"{PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR}=",
        f"{PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR}=",
    ]

    assert CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR in text
    assert CYCLE_SNAPSHOT_DB_DSN_ENV_VAR in text
    assert CYCLE_SNAPSHOT_DB_TABLE_ENV_VAR in text
    assert PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR in text
    assert PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR in text
    assert PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR in text
    assert PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR in text
    assert PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR in text
    assert PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR in text
    assert OUTCOME_TRACKING_DB_ENABLED_ENV_VAR in text
    assert OUTCOME_TRACKING_DB_DSN_ENV_VAR in text
    assert OUTCOME_TRACKING_DB_TABLE_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DB_DSN_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR in text
    assert ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR in text
    assert ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR in text
    assert ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR in text
    assert LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR in text
    assert LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR in text
    assert LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR in text
    assert STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR in text
    assert STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR in text
    assert STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR in text
    assert PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR in text
    assert PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR in text
    assert PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR in text
    assert lines == expected_lines
    assert all(line.endswith("=") for line in lines)
    assert "POLYMARKET_ALPHA_DATABASE_URL" not in text
    assert "POLYMARKET_ALPHA_DB_SCHEMA" not in text
    assert "postgresql://" not in text
    assert "secret" not in text.lower()

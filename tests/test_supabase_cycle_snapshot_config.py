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
from polymarket_alpha_lab.supabase_paper_probability_recommendation_queue_config import (
    PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_DSN_ENV_VAR,
    PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_ENABLED_ENV_VAR,
    PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_recommendation_risk_budget_config import (
    PAPER_RECOMMENDATION_RISK_BUDGET_DB_DSN_ENV_VAR,
    PAPER_RECOMMENDATION_RISK_BUDGET_DB_ENABLED_ENV_VAR,
    PAPER_RECOMMENDATION_RISK_BUDGET_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_config import (
    ACTION_GATED_QUEUE_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config import (
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_research_packet_config import (
    PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_research_packet_quality_config import (
    PAPER_RESEARCH_PACKET_QUALITY_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_QUALITY_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_QUALITY_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_research_packet_operator_flow_config import (
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_history_config import (
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
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
from polymarket_alpha_lab.supabase_paper_project_screening_rank_stability_config import (
    PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_DSN_ENV_VAR,
    PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_ENABLED_ENV_VAR,
    PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_config import (
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_config import (
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_autonomous_investment_ledger_config import (
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_autonomous_investment_ledger_db_history_health_config import (
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_db_history_health_config import (
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_broker_config import (
    PAPER_BROKER_DB_DSN_ENV_VAR,
    PAPER_BROKER_DB_ENABLED_ENV_VAR,
    PAPER_BROKER_DB_TABLE_ENV_VAR,
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
from polymarket_alpha_lab.supabase_team_forecast_config import (
    TEAM_FORECAST_DB_DSN_ENV_VAR,
    TEAM_FORECAST_DB_ENABLED_ENV_VAR,
    TEAM_FORECAST_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR,
    TEAM_PROFILE_DB_TABLE_ENV_VAR,
    TEAM_ROUTE_DB_TABLE_ENV_VAR,
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
    secret_dsn = "postgresql://user:sensitive-token@localhost/postgres"

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
    secret_dsn = "postgresql://user:sensitive-token@localhost/postgres"

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
    dsn = "postgresql://localhost/postgres"

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
    secret_dsn = "postgresql://user:sensitive-token@localhost/postgres"

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
        dsn="postgresql://user:sensitive-token@localhost/postgres",
        table_name=DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://user:sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://localhost/postgres",
        "postgres://127.0.0.1:54322/postgres",
        "host=localhost port=54322 dbname=postgres",
        "postgresql:///postgres?host=/var/run/postgresql",
    ],
)
def test_config_accepts_local_postgres_dsn_forms(dsn: str) -> None:
    config = SupabaseCycleSnapshotConfig(
        enabled=True,
        dsn=dsn,
        table_name=DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
    )

    assert config.dsn == dsn


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://example.invalid/postgres",
        "postgres://db.example.com/postgres",
        "postgresql://localhost/postgres?hostaddr=127.0.0.1",
        "host=example.invalid dbname=postgres",
        "sqlite:///tmp/project.db",
    ],
)
def test_config_rejects_remote_or_unsafe_dsn_without_echoing_secret(
    dsn: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        SupabaseCycleSnapshotConfig(
            enabled=False,
            dsn=dsn,
            table_name=DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
        )

    message = str(exc_info.value)
    assert CYCLE_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message


def test_env_config_rejects_remote_dsn_without_echoing_secret() -> None:
    secret_dsn = "postgresql://user:sensitive-token@example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        from_cycle_snapshot_db_env(
            {
                CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR: "true",
                CYCLE_SNAPSHOT_DB_DSN_ENV_VAR: secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert CYCLE_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message


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
                CYCLE_SNAPSHOT_DB_DSN_ENV_VAR: "postgresql://localhost/postgres",
            },
        )


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    with pytest.raises(ValueError, match="enabled must be a bool"):
        SupabaseCycleSnapshotConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn="postgresql://localhost/postgres",
            table_name=DEFAULT_CYCLE_SNAPSHOT_DB_TABLE,
        )


def test_env_example_documents_supported_db_variable_names_only() -> None:
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    expected_lines = [
        f"{CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR}=",
        f"{CYCLE_SNAPSHOT_DB_DSN_ENV_VAR}=",
        f"{CYCLE_SNAPSHOT_DB_TABLE_ENV_VAR}=",
        f"{PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_DSN_ENV_VAR}=",
        f"{PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_TABLE_ENV_VAR}=",
        f"{PAPER_RECOMMENDATION_RISK_BUDGET_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_RECOMMENDATION_RISK_BUDGET_DB_DSN_ENV_VAR}=",
        f"{PAPER_RECOMMENDATION_RISK_BUDGET_DB_TABLE_ENV_VAR}=",
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
        f"{STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR}=",
        f"{STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR}=",
        f"{STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR}=",
        f"{PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR}=",
        f"{PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR}=",
        f"{PAPER_RESEARCH_PACKET_QUALITY_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_RESEARCH_PACKET_QUALITY_DB_DSN_ENV_VAR}=",
        f"{PAPER_RESEARCH_PACKET_QUALITY_DB_TABLE_ENV_VAR}=",
        f"{PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR}=",
        f"{PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR}=",
        f"{STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR}=",
        f"{STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR}=",
        f"{STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR}=",
        f"{PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_DSN_ENV_VAR}=",
        f"{PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR}=",
        f"{PAPER_BROKER_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_BROKER_DB_DSN_ENV_VAR}=",
        f"{PAPER_BROKER_DB_TABLE_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_TABLE_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR}=",
        f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR}=",
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
        f"{TEAM_FORECAST_DB_ENABLED_ENV_VAR}=",
        f"{TEAM_FORECAST_DB_DSN_ENV_VAR}=",
        f"{TEAM_PROFILE_DB_TABLE_ENV_VAR}=",
        f"{TEAM_ROUTE_DB_TABLE_ENV_VAR}=",
        f"{TEAM_FORECAST_DB_TABLE_ENV_VAR}=",
        f"{TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR}=",
        f"{TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR}=",
    ]

    assert CYCLE_SNAPSHOT_DB_ENABLED_ENV_VAR in text
    assert CYCLE_SNAPSHOT_DB_DSN_ENV_VAR in text
    assert CYCLE_SNAPSHOT_DB_TABLE_ENV_VAR in text
    assert PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_ENABLED_ENV_VAR in text
    assert PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_DSN_ENV_VAR in text
    assert PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_TABLE_ENV_VAR in text
    assert PAPER_RECOMMENDATION_RISK_BUDGET_DB_ENABLED_ENV_VAR in text
    assert PAPER_RECOMMENDATION_RISK_BUDGET_DB_DSN_ENV_VAR in text
    assert PAPER_RECOMMENDATION_RISK_BUDGET_DB_TABLE_ENV_VAR in text
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
    assert STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR in text
    assert STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR in text
    assert STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR in text
    assert PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR in text
    assert PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR in text
    assert PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR in text
    assert PAPER_RESEARCH_PACKET_QUALITY_DB_ENABLED_ENV_VAR in text
    assert PAPER_RESEARCH_PACKET_QUALITY_DB_DSN_ENV_VAR in text
    assert PAPER_RESEARCH_PACKET_QUALITY_DB_TABLE_ENV_VAR in text
    assert PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR in text
    assert PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR in text
    assert PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR in text
    assert STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR in text
    assert STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR in text
    assert STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE_ENV_VAR in text
    assert ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR in text
    assert ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR in text
    assert ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR in text
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR in text
    assert PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_ENABLED_ENV_VAR in text
    assert PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_DSN_ENV_VAR in text
    assert PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE_ENV_VAR in text
    assert PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR in text
    assert PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR in text
    assert PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR in text
    assert PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR in text
    assert PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR in text
    assert PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR in text
    assert PAPER_BROKER_DB_ENABLED_ENV_VAR in text
    assert PAPER_BROKER_DB_DSN_ENV_VAR in text
    assert PAPER_BROKER_DB_TABLE_ENV_VAR in text
    assert PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR in text
    assert PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR in text
    assert PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_TABLE_ENV_VAR in text
    assert (
        PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR
        in text
    )
    assert (
        PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR
        in text
    )
    assert (
        PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR
        in text
    )
    assert (
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR
        in text
    )
    assert PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR in text
    assert (
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR
        in text
    )
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
    assert TEAM_FORECAST_DB_ENABLED_ENV_VAR in text
    assert TEAM_FORECAST_DB_DSN_ENV_VAR in text
    assert TEAM_PROFILE_DB_TABLE_ENV_VAR in text
    assert TEAM_ROUTE_DB_TABLE_ENV_VAR in text
    assert TEAM_FORECAST_DB_TABLE_ENV_VAR in text
    assert TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR in text
    assert TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR in text
    assert lines == expected_lines
    assert all(line.endswith("=") for line in lines)
    assert "POLYMARKET_ALPHA_DATABASE_URL" not in text
    assert "POLYMARKET_ALPHA_DB_SCHEMA" not in text
    assert "postgresql://" not in text
    assert "secret" not in text.lower()

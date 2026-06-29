from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import re

import pytest

import polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_config as decision_support_config
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
    DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE,
    SupabaseActionGatedStrategyRecommendationQueueDecisionSupportConfig,
    from_action_gated_strategy_recommendation_queue_decision_support_db_env,
)


ENV_EXAMPLE_PATH = Path(".env.example")
MIGRATION_PATH = Path(
    "supabase/migrations/"
    "20260620000002_action_gated_strategy_recommendation_queue_decision_support_reports.sql",
)
RENAME_MIGRATION_PATH = Path(
    "supabase/migrations/"
    "20260624000000_shorten_action_gated_queue_decision_support_table.sql",
)
LOCAL_POSTGRES_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


def test_disabled_env_config_uses_default_table_and_accepts_absent_dsn() -> None:
    config = from_action_gated_strategy_recommendation_queue_decision_support_db_env(
        {},
    )

    assert (
        config
        == SupabaseActionGatedStrategyRecommendationQueueDecisionSupportConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE,
        )
    )


def test_default_table_name_is_postgres_identifier_safe() -> None:
    assert (
        DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE
        == "paper_action_gated_queue_decision_support_reports"
    )
    assert len(DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE) <= 63


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    unrelated_secret = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        from_action_gated_strategy_recommendation_queue_decision_support_db_env(
            {
                ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR: "true",
                "UNRELATED_SECRET": unrelated_secret,
            },
        )

    message = str(exc_info.value)
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR in message
    assert unrelated_secret not in message
    assert "topsecret" not in message


def test_enabled_env_config_rejects_padded_dsn_without_echoing_it() -> None:
    secret_dsn = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        from_action_gated_strategy_recommendation_queue_decision_support_db_env(
            {
                ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR: "1",
                ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR: (
                    f" {secret_dsn} "
                ),
            },
        )

    message = str(exc_info.value)
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "topsecret" not in message


@pytest.mark.parametrize(
    ("enabled_value", "expected_enabled"),
    [
        ("", False),
        ("0", False),
        ("false", False),
        ("1", True),
        ("true", True),
    ],
)
def test_enabled_env_config_accepts_only_strict_values(
    enabled_value: str,
    expected_enabled: bool,
) -> None:
    env = {
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR: enabled_value,
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
    }

    config = from_action_gated_strategy_recommendation_queue_decision_support_db_env(
        env,
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", [" TRUE ", " FALSE ", "yes", "on", "2"])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        from_action_gated_strategy_recommendation_queue_decision_support_db_env(
            {
                ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR: enabled_value,
                ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            },
        )

    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR in str(
        exc_info.value,
    )


def test_enabled_env_config_reads_explicit_dsn_at_process_edge() -> None:
    dsn = LOCAL_POSTGRES_DSN

    config = from_action_gated_strategy_recommendation_queue_decision_support_db_env(
        {
            ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR: "true",
            ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR: dsn,
            ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR: (
                "audit.action_gated_queue_decision_support_reports"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "audit.action_gated_queue_decision_support_reports"


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config = SupabaseActionGatedStrategyRecommendationQueueDecisionSupportConfig(
        enabled=True,
        dsn="postgresql://topsecret:postgres@localhost:54322/postgres",
        table_name=DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=<redacted>" in rendered


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
        SupabaseActionGatedStrategyRecommendationQueueDecisionSupportConfig(
            enabled=False,
            dsn=dsn,
            table_name=DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE,
        )

    message = str(exc_info.value)
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "topsecret" not in message


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    rendered = repr(
        SupabaseActionGatedStrategyRecommendationQueueDecisionSupportConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "ActionGatedQueueDecisionSupportReports",
        "action-gated-queue-decision-support-reports",
        "audit.ActionGatedQueueDecisionSupportReports",
        "audit.action-gated-queue-decision-support-reports",
        "_action_gated_queue_decision_support_reports",
        "audit._action_gated_queue_decision_support_reports",
        "action_gated_queue_decision_support_reports_",
        "audit.action_gated_queue_decision_support_reports_",
        "public.audit.action_gated_queue_decision_support_reports",
        "",
    ],
)
def test_table_name_must_be_lowercase_identifier_with_optional_schema(
    table_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="table_name must be a lowercase identifier with optional schema prefix",
    ):
        SupabaseActionGatedStrategyRecommendationQueueDecisionSupportConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_action_gated_queue_decision_support_reports",
        "action_gated_1_queue_2_decision_support_reports",
        "public.paper_action_gated_queue_decision_support_reports",
        "audit.action_gated_queue_decision_support_reports",
    ],
)
def test_table_name_accepts_lowercase_identifier_with_optional_schema(
    table_name: str,
) -> None:
    config = SupabaseActionGatedStrategyRecommendationQueueDecisionSupportConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_action_gated_strategy_recommendation_queue_decision_support_db_env(
            {
                ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR: (
                    "ActionGatedQueueDecisionSupportReports"
                ),
            },
        )

    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    with pytest.raises(ValueError, match="enabled must be a bool"):
        SupabaseActionGatedStrategyRecommendationQueueDecisionSupportConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn=LOCAL_POSTGRES_DSN,
            table_name=DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    with pytest.raises(ValueError) as exc_info:
        SupabaseActionGatedStrategyRecommendationQueueDecisionSupportConfig(
            enabled=True,
            dsn=object(),  # type: ignore[arg-type]
            table_name=DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE,
        )

    message = str(exc_info.value)
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_env_example_contains_blank_decision_support_db_vars_and_no_sample_dsn() -> None:
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    expected_lines = [
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR}=",
    ]

    for line in expected_lines:
        assert line in lines
    assert "postgresql://" not in text
    assert "POLYMARKET_ALPHA_DATABASE_URL" not in text
    assert "POLYMARKET_ALPHA_DB_SCHEMA" not in text
    assert all(line.endswith("=") for line in lines)


def test_public_exports_include_constants_config_and_loader() -> None:
    assert decision_support_config.__all__ == (
        "ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR",
        "ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR",
        "ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR",
        "DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE",
        "SupabaseActionGatedStrategyRecommendationQueueDecisionSupportConfig",
        "from_action_gated_strategy_recommendation_queue_decision_support_db_env",
    )


def test_migration_defines_action_gated_queue_decision_support_report_table() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert (
        "create table if not exists "
        "public.paper_action_gated_strategy_recommendation_queue_decision_support_reports"
    ) in sql
    for column in (
        "snapshot_sha256 text primary key",
        "generated_at timestamptz not null",
        "priority_source_report_count integer not null",
        "priority_research_ready_count integer not null",
        "priority_watch_count integer not null",
        "priority_blocked_count integer not null",
        "priority_total_ready_notional numeric not null",
        "top_research_priority_score numeric not null",
        "average_research_priority_score numeric not null",
        "risk_config_version text not null",
        "risk_status text not null",
        "risk_recommended_next_step text not null",
        "risk_source_queue_count integer not null",
        "risk_candidate_count integer not null",
        "risk_ready_count integer not null",
        "risk_total_ready_notional numeric not null",
        "risk_largest_queue_ready_notional numeric not null",
        "risk_reason_codes jsonb not null",
        "priority_payload jsonb not null",
        "risk_payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in sql
    assert "check (snapshot_sha256 ~ '^[a-f0-9]{64}$')" in sql
    assert "check (jsonb_typeof(risk_reason_codes) = 'array')" in sql
    assert "check (jsonb_typeof(priority_payload) = 'object')" in sql
    assert "check (jsonb_typeof(risk_payload) = 'object')" in sql
    assert "check (risk_status in ('pass', 'watch', 'blocked'))" in sql
    assert (
        "check (risk_recommended_next_step in "
        "('allocate_paper_research_queue', "
        "'throttle_paper_research_queue', "
        "'block_paper_research_queue'))"
    ) in sql
    assert (
        "check ((risk_status = 'pass' "
        "and risk_recommended_next_step = 'allocate_paper_research_queue') "
        "or (risk_status = 'watch' "
        "and risk_recommended_next_step = 'throttle_paper_research_queue') "
        "or (risk_status = 'blocked' "
        "and risk_recommended_next_step = 'block_paper_research_queue'))"
    ) in sql
    for count_column in (
        "priority_source_report_count",
        "priority_research_ready_count",
        "priority_watch_count",
        "priority_blocked_count",
        "risk_source_queue_count",
        "risk_candidate_count",
        "risk_ready_count",
    ):
        assert f"check ({count_column} >= 0)" in sql
    assert (
        "check (priority_source_report_count = "
        "priority_research_ready_count + priority_watch_count + priority_blocked_count)"
    ) in sql
    assert "check (risk_candidate_count >= risk_ready_count)" in sql
    for numeric_column in (
        "priority_total_ready_notional",
        "top_research_priority_score",
        "average_research_priority_score",
        "risk_total_ready_notional",
        "risk_largest_queue_ready_notional",
    ):
        assert f"check ({numeric_column} >= 0)" in sql
    for hard_flag in ("paper_only", "report_only", "readonly"):
        assert f"check ({hard_flag} is true)" in sql
    for index_fragment in (
        "(generated_at desc)",
        "(risk_status, generated_at desc)",
        "(risk_config_version, generated_at desc)",
        "(priority_source_report_count, generated_at desc)",
        "(risk_status, generated_at desc, inserted_at desc, snapshot_sha256 desc)",
    ):
        assert index_fragment in sql


def test_forward_migration_renames_overlong_decision_support_table() -> None:
    sql = RENAME_MIGRATION_PATH.read_text(encoding="utf-8")

    assert re.search(
        r"alter table if exists\s+"
        r"public\.paper_action_gated_strategy_recommendation_queue_decision_support_reports\s+"
        r"rename to paper_action_gated_queue_decision_support_reports",
        sql,
    )
    assert "paper_action_gated_queue_decision_support_reports" in sql


def test_forward_migration_uses_postgres_safe_replacement_identifiers() -> None:
    sql = RENAME_MIGRATION_PATH.read_text(encoding="utf-8")
    replacement_identifiers = re.findall(
        r"\b(?:rename to|add constraint|drop constraint if exists)\s+([a-z][a-z0-9_]*)",
        sql,
    )

    assert replacement_identifiers
    assert all(len(identifier) <= 63 for identifier in replacement_identifiers)
    assert "add constraint pagqdst_sources_snapshot_sha256_fkey" in sql

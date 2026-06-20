from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_history_config as history_config
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_history_config import (
    ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
    DEFAULT_ACTION_GATED_QUEUE_HISTORY_DB_TABLE,
    SupabaseActionGatedStrategyRecommendationQueueHistoryConfig,
    from_action_gated_strategy_recommendation_queue_history_db_env,
)


ENV_EXAMPLE_PATH = Path(".env.example")
MIGRATION_PATH = Path(
    "supabase/migrations/"
    "20260620000001_action_gated_strategy_recommendation_queue_history_reports.sql",
)


def test_disabled_env_config_uses_default_table_and_accepts_absent_dsn() -> None:
    config = from_action_gated_strategy_recommendation_queue_history_db_env({})

    assert config == SupabaseActionGatedStrategyRecommendationQueueHistoryConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_ACTION_GATED_QUEUE_HISTORY_DB_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    unrelated_secret = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        from_action_gated_strategy_recommendation_queue_history_db_env(
            {
                ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR: "true",
                "UNRELATED_SECRET": unrelated_secret,
            },
        )

    message = str(exc_info.value)
    assert ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR in message
    assert unrelated_secret not in message
    assert "topsecret" not in message


def test_enabled_env_config_rejects_padded_dsn_without_echoing_it() -> None:
    secret_dsn = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        from_action_gated_strategy_recommendation_queue_history_db_env(
            {
                ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR: "1",
                ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR in message
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
        ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR: enabled_value,
        ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR: "postgresql://example.invalid/postgres",
    }

    config = from_action_gated_strategy_recommendation_queue_history_db_env(env)

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", [" TRUE ", " FALSE ", "yes", "on", "2"])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        from_action_gated_strategy_recommendation_queue_history_db_env(
            {
                ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR: enabled_value,
                ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR: (
                    "postgresql://example.invalid/postgres"
                ),
            },
        )

    assert ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR in str(exc_info.value)


def test_enabled_env_config_reads_explicit_dsn_at_process_edge() -> None:
    dsn = "postgresql://example.invalid/postgres"

    config = from_action_gated_strategy_recommendation_queue_history_db_env(
        {
            ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR: "true",
            ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR: dsn,
            ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR: (
                "audit.action_gated_queue_history_reports"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "audit.action_gated_queue_history_reports"


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config = SupabaseActionGatedStrategyRecommendationQueueHistoryConfig(
        enabled=True,
        dsn="postgresql://topsecret.example.invalid/postgres",
        table_name=DEFAULT_ACTION_GATED_QUEUE_HISTORY_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=<redacted>" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    rendered = repr(
        SupabaseActionGatedStrategyRecommendationQueueHistoryConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_ACTION_GATED_QUEUE_HISTORY_DB_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "ActionGatedQueueHistoryReports",
        "action-gated-queue-history-reports",
        "audit.ActionGatedQueueHistoryReports",
        "audit.action-gated-queue-history-reports",
        "_action_gated_queue_history_reports",
        "audit._action_gated_queue_history_reports",
        "action_gated_queue_history_reports_",
        "audit.action_gated_queue_history_reports_",
        "public.audit.action_gated_queue_history_reports",
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
        SupabaseActionGatedStrategyRecommendationQueueHistoryConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_action_gated_strategy_recommendation_queue_history_reports",
        "action_gated_1_queue_2_history_reports",
        "public.paper_action_gated_strategy_recommendation_queue_history_reports",
        "audit.action_gated_queue_history_reports",
    ],
)
def test_table_name_accepts_lowercase_identifier_with_optional_schema(
    table_name: str,
) -> None:
    config = SupabaseActionGatedStrategyRecommendationQueueHistoryConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name() -> None:
    with pytest.raises(ValueError) as exc_info:
        from_action_gated_strategy_recommendation_queue_history_db_env(
            {
                ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR: (
                    "ActionGatedQueueHistoryReports"
                ),
            },
        )

    assert ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    with pytest.raises(ValueError, match="enabled must be a bool"):
        SupabaseActionGatedStrategyRecommendationQueueHistoryConfig(
            enabled=1,  # type: ignore[arg-type]
            dsn="postgresql://example.invalid/postgres",
            table_name=DEFAULT_ACTION_GATED_QUEUE_HISTORY_DB_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    with pytest.raises(ValueError) as exc_info:
        SupabaseActionGatedStrategyRecommendationQueueHistoryConfig(
            enabled=True,
            dsn=object(),  # type: ignore[arg-type]
            table_name=DEFAULT_ACTION_GATED_QUEUE_HISTORY_DB_TABLE,
        )

    message = str(exc_info.value)
    assert ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_env_example_contains_blank_history_db_vars_and_no_sample_dsn() -> None:
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    expected_lines = [
        f"{ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR}=",
        f"{ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR}=",
    ]

    for line in expected_lines:
        assert line in lines
    assert "postgresql://" not in text
    assert "POLYMARKET_ALPHA_DATABASE_URL" not in text
    assert "POLYMARKET_ALPHA_DB_SCHEMA" not in text
    assert all(line.endswith("=") for line in lines)


def test_public_exports_include_constants_config_and_loader() -> None:
    assert history_config.__all__ == (
        "ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR",
        "ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR",
        "ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR",
        "DEFAULT_ACTION_GATED_QUEUE_HISTORY_DB_TABLE",
        "SupabaseActionGatedStrategyRecommendationQueueHistoryConfig",
        "from_action_gated_strategy_recommendation_queue_history_db_env",
    )


def test_migration_defines_action_gated_queue_history_report_table() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert (
        "create table if not exists "
        "public.paper_action_gated_strategy_recommendation_queue_history_reports"
    ) in sql
    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "source_report_count integer not null",
        "first_source_generated_at timestamptz",
        "last_source_generated_at timestamptz",
        "research_ready_count integer not null",
        "watch_count integer not null",
        "blocked_count integer not null",
        "total_ready_notional numeric not null",
        "latest_action_status text",
        "latest_recommended_next_step text",
        "status_transition_count integer not null",
        "ready_notional_delta numeric not null",
        "latest_reason_code_counts jsonb not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in sql
    assert "check (jsonb_typeof(latest_reason_code_counts) = 'object')" in sql
    assert "check (jsonb_typeof(payload) = 'object')" in sql
    assert "check (report_sha256 ~ '^[a-f0-9]{64}$')" in sql
    assert (
        "check (latest_action_status is null "
        "or latest_action_status in ('research_ready', 'watch', 'blocked'))"
    ) in sql
    assert (
        "check (latest_recommended_next_step is null "
        "or latest_recommended_next_step in "
        "('review_candidate_research_queue', "
        "'await_fresh_cycle_evidence', "
        "'repair_cycle_evidence'))"
    ) in sql
    assert (
        "check ((latest_action_status is null "
        "and latest_recommended_next_step is null) "
        "or (latest_action_status = 'research_ready' "
        "and latest_recommended_next_step = 'review_candidate_research_queue') "
        "or (latest_action_status = 'watch' "
        "and latest_recommended_next_step = 'await_fresh_cycle_evidence') "
        "or (latest_action_status = 'blocked' "
        "and latest_recommended_next_step = 'repair_cycle_evidence'))"
    ) in sql
    for count_column in (
        "source_report_count",
        "research_ready_count",
        "watch_count",
        "blocked_count",
        "status_transition_count",
    ):
        assert f"check ({count_column} >= 0)" in sql
    assert (
        "check (source_report_count = "
        "research_ready_count + watch_count + blocked_count)"
    ) in sql
    assert "check (total_ready_notional >= 0)" in sql
    assert (
        "check (source_report_count > 0 "
        "or (first_source_generated_at is null "
        "and last_source_generated_at is null "
        "and latest_action_status is null "
        "and latest_recommended_next_step is null "
        "and status_transition_count = 0 "
        "and total_ready_notional = 0 "
        "and ready_notional_delta = 0))"
    ) in sql
    assert (
        "check (source_report_count = 0 "
        "or (first_source_generated_at is not null "
        "and last_source_generated_at is not null "
        "and latest_action_status is not null "
        "and latest_recommended_next_step is not null))"
    ) in sql
    for hard_flag in ("paper_only", "report_only", "readonly"):
        assert f"check ({hard_flag} is true)" in sql
    for index_fragment in (
        "(generated_at desc)",
        "(latest_action_status, generated_at desc)",
        "(latest_recommended_next_step, generated_at desc)",
        "(source_report_count, generated_at desc)",
        "(latest_action_status, generated_at desc, inserted_at desc, "
        "report_sha256 desc)",
    ):
        assert index_fragment in sql

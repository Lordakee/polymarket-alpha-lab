from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_history_config import (
    DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR,
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
    SupabaseStrategyCandidateResearchQueueHistoryConfig,
    from_strategy_candidate_research_queue_history_db_env,
)


def test_disabled_env_config_uses_default_table_and_accepts_absent_dsn() -> None:
    config = from_strategy_candidate_research_queue_history_db_env({})

    assert config == SupabaseStrategyCandidateResearchQueueHistoryConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    secret = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        from_strategy_candidate_research_queue_history_db_env(
            {
                STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR: "true",
                "UNRELATED_SECRET": secret,
            },
        )

    message = str(exc_info.value)
    assert STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR in message
    assert secret not in message
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
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR: enabled_value,
        STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR: (
            "postgresql://example.invalid/postgres"
        ),
    }

    config = from_strategy_candidate_research_queue_history_db_env(env)

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", [" TRUE ", "yes", "on", "2"])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        from_strategy_candidate_research_queue_history_db_env(
            {
                STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR: (
                    enabled_value
                ),
                STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR: (
                    "postgresql://example.invalid/postgres"
                ),
            },
        )

    assert STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR in str(
        exc_info.value,
    )


def test_enabled_env_config_reads_explicit_dsn_and_table() -> None:
    dsn = "postgresql://example.invalid/postgres"

    config = from_strategy_candidate_research_queue_history_db_env(
        {
            STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED_ENV_VAR: "true",
            STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN_ENV_VAR: dsn,
            STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE_ENV_VAR: (
                "audit.strategy_candidate_research_queue_history_reports"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "audit.strategy_candidate_research_queue_history_reports"


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config = SupabaseStrategyCandidateResearchQueueHistoryConfig(
        enabled=True,
        dsn="postgresql://topsecret.example.invalid/postgres",
        table_name=DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=<redacted>" in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "StrategyCandidateResearchQueueHistoryReports",
        "strategy-candidate-research-queue-history-reports",
        "_strategy_candidate_research_queue_history_reports",
        "strategy_candidate_research_queue_history_reports_",
        "public.audit.strategy_candidate_research_queue_history_reports",
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
        SupabaseStrategyCandidateResearchQueueHistoryConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )

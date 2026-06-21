from __future__ import annotations

from dataclasses import FrozenInstanceError
from importlib import import_module
from pathlib import Path

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config"
)
ENV_EXAMPLE_PATH = Path(".env.example")
MIGRATION_PATH = Path(
    "supabase/migrations/"
    "20260621000000_strategy_candidate_research_queue_reports.sql",
)


def _load_module():
    return import_module(MODULE_NAME)


def test_constants_use_strategy_candidate_research_queue_env_names() -> None:
    module = _load_module()

    assert (
        module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR
        == "POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED"
    )
    assert (
        module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR
        == "POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN"
    )
    assert (
        module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR
        == "POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE"
    )
    assert (
        module.DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE
        == "paper_strategy_candidate_research_queue_reports"
    )


def test_disabled_env_config_uses_default_table_and_accepts_absent_dsn() -> None:
    module = _load_module()

    config = module.from_strategy_candidate_research_queue_db_env({})

    assert config == module.SupabaseStrategyCandidateResearchQueueConfig(
        enabled=False,
        dsn=None,
        table_name=module.DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    module = _load_module()
    unrelated_secret = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_strategy_candidate_research_queue_db_env(
            {
                module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR: "true",
                "UNRELATED_SECRET": unrelated_secret,
            },
        )

    message = str(exc_info.value)
    assert module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR in message
    assert unrelated_secret not in message
    assert "topsecret" not in message


def test_enabled_env_config_rejects_padded_dsn_without_echoing_it() -> None:
    module = _load_module()
    secret_dsn = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_strategy_candidate_research_queue_db_env(
            {
                module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR: "1",
                module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR: (
                    f" {secret_dsn} "
                ),
            },
        )

    message = str(exc_info.value)
    assert module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR in message
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
    module = _load_module()
    env = {
        module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR: enabled_value,
        module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR: (
            "postgresql://example.invalid/postgres"
        ),
    }

    config = module.from_strategy_candidate_research_queue_db_env(env)

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", [" TRUE ", " FALSE ", "yes", "on", "2"])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_strategy_candidate_research_queue_db_env(
            {
                module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR: (
                    enabled_value
                ),
                module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR: (
                    "postgresql://example.invalid/postgres"
                ),
            },
        )

    assert module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR in str(
        exc_info.value,
    )


def test_enabled_env_config_reads_explicit_dsn_at_process_edge() -> None:
    module = _load_module()
    dsn = "postgresql://example.invalid/postgres"

    config = module.from_strategy_candidate_research_queue_db_env(
        {
            module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR: "true",
            module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR: dsn,
            module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR: (
                "audit.strategy_candidate_research_queue_reports"
            ),
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "audit.strategy_candidate_research_queue_reports"


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _load_module()
    config = module.SupabaseStrategyCandidateResearchQueueConfig(
        enabled=True,
        dsn="postgresql://topsecret.example.invalid/postgres",
        table_name=module.DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=<redacted>" in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    module = _load_module()

    rendered = repr(
        module.SupabaseStrategyCandidateResearchQueueConfig(
            enabled=False,
            dsn=None,
            table_name=module.DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "StrategyCandidateResearchQueueReports",
        "strategy-candidate-research-queue-reports",
        "audit.StrategyCandidateResearchQueueReports",
        "audit.strategy-candidate-research-queue-reports",
        "_strategy_candidate_research_queue_reports",
        "audit._strategy_candidate_research_queue_reports",
        "strategy_candidate_research_queue_reports_",
        "audit.strategy_candidate_research_queue_reports_",
        "public.audit.strategy_candidate_research_queue_reports",
        "",
    ],
)
def test_table_name_must_be_lowercase_identifier_with_optional_schema(
    table_name: str,
) -> None:
    module = _load_module()

    with pytest.raises(
        ValueError,
        match="table_name must be a lowercase identifier with optional schema prefix",
    ):
        module.SupabaseStrategyCandidateResearchQueueConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_strategy_candidate_research_queue_reports",
        "strategy_candidate_1_research_queue_2_reports",
        "public.paper_strategy_candidate_research_queue_reports",
        "audit.strategy_candidate_research_queue_reports",
    ],
)
def test_table_name_accepts_lowercase_identifier_with_optional_schema(
    table_name: str,
) -> None:
    module = _load_module()

    config = module.SupabaseStrategyCandidateResearchQueueConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name() -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.from_strategy_candidate_research_queue_db_env(
            {
                module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR: (
                    "StrategyCandidateResearchQueueReports"
                ),
            },
        )

    assert module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR in str(
        exc_info.value,
    )


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    module = _load_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        module.SupabaseStrategyCandidateResearchQueueConfig(
            enabled=1,
            dsn="postgresql://example.invalid/postgres",
            table_name=module.DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    module = _load_module()

    with pytest.raises(ValueError) as exc_info:
        module.SupabaseStrategyCandidateResearchQueueConfig(
            enabled=True,
            dsn=object(),
            table_name=module.DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_env_example_contains_blank_db_vars_and_no_sample_dsn() -> None:
    module = _load_module()
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    expected_lines = [
        f"{module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR}=",
        f"{module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR}=",
        f"{module.STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR}=",
    ]

    for line in expected_lines:
        assert line in lines
    assert "postgresql://" not in text
    assert all(line.endswith("=") for line in lines)


def test_public_exports_include_constants_config_and_loader() -> None:
    module = _load_module()

    assert module.__all__ == (
        "STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR",
        "STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED_ENV_VAR",
        "STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE_ENV_VAR",
        "DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE",
        "SupabaseStrategyCandidateResearchQueueConfig",
        "from_strategy_candidate_research_queue_db_env",
    )


def test_migration_defines_strategy_candidate_research_queue_report_table() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert (
        "create table if not exists "
        "public.paper_strategy_candidate_research_queue_reports"
    ) in sql
    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "source_config_version text not null",
        "action_status text not null",
        "recommended_next_step text not null",
        "research_status text not null",
        "candidate_count integer not null",
        "research_ready_count integer not null",
        "watch_count integer not null",
        "blocked_count integer not null",
        "selected_count integer not null",
        "skipped_count integer not null",
        "not_selected_count integer not null",
        "total_ready_notional numeric not null",
        "total_selected_notional numeric not null",
        "total_suggested_notional numeric not null",
        "top_research_priority_score numeric not null",
        "average_research_ready_score numeric not null",
        "source_reason_code_counts jsonb not null",
        "primary_reason_code_counts jsonb not null",
        "reason_codes jsonb not null",
        "rows jsonb not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in sql
    assert "check (jsonb_typeof(source_reason_code_counts) = 'object')" in sql
    assert "check (jsonb_typeof(primary_reason_code_counts) = 'object')" in sql
    assert "check (jsonb_typeof(reason_codes) = 'array')" in sql
    assert "check (jsonb_typeof(rows) = 'array')" in sql
    assert "check (jsonb_typeof(payload) = 'object')" in sql
    assert "check (report_sha256 ~ '^[a-f0-9]{64}$')" in sql
    assert "check (action_status in ('research_ready', 'watch', 'blocked'))" in sql
    assert (
        "check (recommended_next_step in "
        "('review_candidate_research_queue', "
        "'await_fresh_cycle_evidence', "
        "'repair_cycle_evidence'))"
    ) in sql
    assert (
        "check ((action_status = 'research_ready' "
        "and recommended_next_step = 'review_candidate_research_queue') "
        "or (action_status = 'watch' "
        "and recommended_next_step = 'await_fresh_cycle_evidence') "
        "or (action_status = 'blocked' "
        "and recommended_next_step = 'repair_cycle_evidence'))"
    ) in sql
    assert "check (research_status in ('ready', 'watch', 'blocked'))" in sql
    for count_column in (
        "candidate_count",
        "research_ready_count",
        "watch_count",
        "blocked_count",
        "selected_count",
        "skipped_count",
        "not_selected_count",
    ):
        assert f"check ({count_column} >= 0)" in sql
    assert (
        "check (candidate_count = "
        "research_ready_count + watch_count + blocked_count)"
    ) in sql
    assert (
        "check (candidate_count = "
        "selected_count + skipped_count + not_selected_count)"
    ) in sql
    for numeric_column in (
        "total_ready_notional",
        "total_selected_notional",
        "total_suggested_notional",
        "top_research_priority_score",
        "average_research_ready_score",
    ):
        assert f"check ({numeric_column} >= 0)" in sql
    for hard_flag in ("paper_only", "report_only", "readonly"):
        assert f"check ({hard_flag} is true)" in sql
    for index_fragment in (
        "(generated_at desc)",
        "(source_config_version, generated_at desc)",
        "(action_status, generated_at desc)",
        "(recommended_next_step, generated_at desc)",
        "(research_status, generated_at desc)",
        "(source_config_version, action_status, recommended_next_step, "
        "research_status, generated_at desc, inserted_at desc, report_sha256 desc)",
    ):
        assert index_fragment in sql

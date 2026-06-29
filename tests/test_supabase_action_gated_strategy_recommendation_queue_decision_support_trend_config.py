from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import re

import pytest


ENV_EXAMPLE_PATH = Path(".env.example")
MIGRATION_PATH = Path(
    "supabase/migrations/"
    "20260620000003_action_gated_queue_decision_support_trend_reports.sql",
)
DOC_PATH = Path("docs/action-gated-queue-decision-support.md")

ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED"
)
DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN"
)
REPORTS_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE"
)
SOURCES_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE"
)
DEFAULT_REPORTS_TABLE = "paper_action_gated_queue_decision_support_trend_reports"
DEFAULT_SOURCES_TABLE = "paper_action_gated_queue_decision_support_trend_sources"
LOCAL_POSTGRES_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


def _config_module():
    import polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config as config_module

    return config_module


def _migration_sql() -> str:
    assert MIGRATION_PATH.exists(), f"missing migration: {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8")


def _compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def _table_body(sql: str, table_name: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+public\."
        + re.escape(table_name)
        + r"\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{table_name}"
    return _compact(match.group(1))


def test_disabled_env_config_uses_default_tables_and_accepts_absent_dsn() -> None:
    config_module = _config_module()

    config = (
        config_module.from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env(
            {},
        )
    )

    assert config == config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
        enabled=False,
        dsn=None,
        reports_table_name=DEFAULT_REPORTS_TABLE,
        sources_table_name=DEFAULT_SOURCES_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    unrelated_secret = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env(
            {
                ENABLED_ENV_VAR: "true",
                "UNRELATED_SECRET": unrelated_secret,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert unrelated_secret not in message
    assert "topsecret" not in message


def test_enabled_env_config_rejects_padded_dsn_without_echoing_it() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env(
            {
                ENABLED_ENV_VAR: "1",
                DSN_ENV_VAR: f" {secret_dsn} ",
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
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
    config_module = _config_module()

    config = (
        config_module.from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            },
        )
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", [" TRUE ", " FALSE ", "yes", "on", "2"])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: LOCAL_POSTGRES_DSN,
            },
        )

    assert ENABLED_ENV_VAR in str(exc_info.value)


def test_enabled_env_config_reads_explicit_dsn_and_table_names() -> None:
    config_module = _config_module()
    dsn = LOCAL_POSTGRES_DSN

    config = (
        config_module.from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: dsn,
                REPORTS_TABLE_ENV_VAR: (
                    "audit.action_gated_queue_decision_support_trend_reports"
                ),
                SOURCES_TABLE_ENV_VAR: (
                    "audit.action_gated_queue_decision_support_trend_sources"
                ),
            },
        )
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert (
        config.reports_table_name
        == "audit.action_gated_queue_decision_support_trend_reports"
    )
    assert (
        config.sources_table_name
        == "audit.action_gated_queue_decision_support_trend_sources"
    )


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
        enabled=True,
        dsn="postgresql://topsecret:postgres@localhost:54322/postgres",
        reports_table_name=DEFAULT_REPORTS_TABLE,
        sources_table_name=DEFAULT_SOURCES_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=<redacted>" in rendered
    assert DEFAULT_REPORTS_TABLE in rendered
    assert DEFAULT_SOURCES_TABLE in rendered


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
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
            enabled=False,
            dsn=dsn,
            reports_table_name=DEFAULT_REPORTS_TABLE,
            sources_table_name=DEFAULT_SOURCES_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "topsecret" not in message


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    config_module = _config_module()

    rendered = repr(
        config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
            enabled=False,
            dsn=None,
            reports_table_name=DEFAULT_REPORTS_TABLE,
            sources_table_name=DEFAULT_SOURCES_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "ActionGatedQueueDecisionSupportTrendReports",
        "action-gated-queue-decision-support-trend-reports",
        "audit.ActionGatedQueueDecisionSupportTrendReports",
        "audit.action-gated-queue-decision-support-trend-reports",
        "_action_gated_queue_decision_support_trend_reports",
        "audit._action_gated_queue_decision_support_trend_reports",
        "action_gated_queue_decision_support_trend_reports_",
        "audit.action_gated_queue_decision_support_trend_reports_",
        "public.audit.action_gated_queue_decision_support_trend_reports",
        "",
    ],
)
def test_table_names_must_be_lowercase_identifiers_with_optional_schema(
    table_name: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(
        ValueError,
        match="lowercase identifier with optional schema prefix",
    ):
        config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
            enabled=False,
            dsn=None,
            reports_table_name=table_name,
            sources_table_name=DEFAULT_SOURCES_TABLE,
        )

    with pytest.raises(
        ValueError,
        match="lowercase identifier with optional schema prefix",
    ):
        config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
            enabled=False,
            dsn=None,
            reports_table_name=DEFAULT_REPORTS_TABLE,
            sources_table_name=table_name,
        )


def test_table_names_accept_optional_schema_and_63_byte_identifier_parts() -> None:
    config_module = _config_module()
    max_length_part = "a" + ("b" * 61) + "1"
    assert len(max_length_part) == 63

    config = config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
        enabled=False,
        dsn=None,
        reports_table_name=f"public.{max_length_part}",
        sources_table_name=f"audit.{max_length_part}",
    )

    assert config.reports_table_name == f"public.{max_length_part}"
    assert config.sources_table_name == f"audit.{max_length_part}"


def test_table_names_reject_identifier_parts_longer_than_63_bytes() -> None:
    config_module = _config_module()
    too_long_part = "a" + ("b" * 62) + "1"
    assert len(too_long_part) == 64

    with pytest.raises(ValueError, match="63"):
        config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
            enabled=False,
            dsn=None,
            reports_table_name=f"public.{too_long_part}",
            sources_table_name=DEFAULT_SOURCES_TABLE,
        )

    with pytest.raises(ValueError, match="63"):
        config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
            enabled=False,
            dsn=None,
            reports_table_name=DEFAULT_REPORTS_TABLE,
            sources_table_name=f"public.{too_long_part}",
        )


def test_env_table_name_errors_mention_variable_names() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as reports_exc:
        config_module.from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env(
            {REPORTS_TABLE_ENV_VAR: "ActionGatedQueueDecisionSupportTrendReports"},
        )
    with pytest.raises(ValueError) as sources_exc:
        config_module.from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env(
            {SOURCES_TABLE_ENV_VAR: "ActionGatedQueueDecisionSupportTrendSources"},
        )

    assert REPORTS_TABLE_ENV_VAR in str(reports_exc.value)
    assert SOURCES_TABLE_ENV_VAR in str(sources_exc.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
            enabled=1,
            dsn=LOCAL_POSTGRES_DSN,
            reports_table_name=DEFAULT_REPORTS_TABLE,
            sources_table_name=DEFAULT_SOURCES_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
            enabled=True,
            dsn=object(),
            reports_table_name=DEFAULT_REPORTS_TABLE,
            sources_table_name=DEFAULT_SOURCES_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_env_example_contains_blank_trend_db_vars_and_no_sample_dsn() -> None:
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    expected_lines = [
        f"{ENABLED_ENV_VAR}=",
        f"{DSN_ENV_VAR}=",
        f"{REPORTS_TABLE_ENV_VAR}=",
        f"{SOURCES_TABLE_ENV_VAR}=",
    ]

    for line in expected_lines:
        assert line in lines
    assert "postgresql://" not in text
    assert "POLYMARKET_ALPHA_DATABASE_URL" not in text
    assert "POLYMARKET_ALPHA_DB_SCHEMA" not in text
    assert all(line.endswith("=") for line in lines)


def test_public_exports_include_constants_config_and_loader() -> None:
    config_module = _config_module()

    assert config_module.__all__ == (
        "ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR",
        "ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR",
        "ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR",
        "ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR",
        "DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE",
        "DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE",
        "SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig",
        "from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env",
    )


def test_migration_creates_trend_report_table_with_compact_summary_columns() -> None:
    body = _table_body(_migration_sql(), DEFAULT_REPORTS_TABLE)

    for column in (
        "trend_sha256 text primary key",
        "trend_schema_version text not null",
        "source_window_sha256 text not null",
        "generated_at timestamptz not null",
        "source_snapshot_count integer not null",
        "first_generated_at timestamptz",
        "latest_generated_at timestamptz",
        "latest_risk_status text",
        "risk_pass_count integer not null",
        "risk_watch_count integer not null",
        "risk_blocked_count integer not null",
        "consecutive_latest_watch_count integer not null",
        "consecutive_latest_blocked_count integer not null",
        "duplicate_generated_at_count integer not null",
        "ready_notional_first numeric",
        "ready_notional_latest numeric",
        "ready_notional_delta numeric",
        "top_priority_score_first numeric",
        "top_priority_score_latest numeric",
        "top_priority_score_delta numeric",
        "average_priority_score_first numeric",
        "average_priority_score_latest numeric",
        "average_priority_score_delta numeric",
        "source_queue_count_first integer",
        "source_queue_count_latest integer",
        "source_queue_count_delta integer",
        "latest_reason_code_counts jsonb not null",
        "total_reason_code_counts jsonb not null",
        "repeated_reason_code_counts jsonb not null",
        "reason_code_rows jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body
    assert "unique (trend_schema_version, source_window_sha256)" in body
    assert "priority_payload" not in body
    assert "risk_payload" not in body


def test_migration_enforces_trend_report_invariants_with_checks() -> None:
    body = _table_body(_migration_sql(), DEFAULT_REPORTS_TABLE)

    for expected_check in (
        "check (trend_sha256 ~ '^[a-f0-9]{64}$')",
        "check (source_window_sha256 ~ '^[a-f0-9]{64}$')",
        "check (source_snapshot_count >= 0)",
        "check (risk_pass_count >= 0)",
        "check (risk_watch_count >= 0)",
        "check (risk_blocked_count >= 0)",
        "check (risk_pass_count + risk_watch_count + risk_blocked_count = source_snapshot_count)",
        "check (latest_risk_status is null or latest_risk_status in ('pass', 'watch', 'blocked'))",
        "check (consecutive_latest_watch_count >= 0)",
        "check (consecutive_latest_watch_count <= source_snapshot_count)",
        "check (consecutive_latest_blocked_count >= 0)",
        "check (consecutive_latest_blocked_count <= source_snapshot_count)",
        "check (duplicate_generated_at_count >= 0)",
        "check (source_snapshot_count = 0 or duplicate_generated_at_count < source_snapshot_count)",
        "check (jsonb_typeof(latest_reason_code_counts) = 'object')",
        "check (jsonb_typeof(total_reason_code_counts) = 'object')",
        "check (jsonb_typeof(repeated_reason_code_counts) = 'object')",
        "check (jsonb_typeof(reason_code_rows) = 'array')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body
    for nullable_invariant in (
        "check ((source_snapshot_count = 0 and first_generated_at is null",
        "and latest_generated_at is null",
        "and latest_risk_status is null",
        "and ready_notional_first is null",
        "and top_priority_score_latest is null",
        "and average_priority_score_delta is null",
        "and source_queue_count_delta is null",
        "or (source_snapshot_count > 0 and first_generated_at is not null",
        "and latest_generated_at is not null",
        "and latest_risk_status is not null",
        "and ready_notional_first is not null",
        "and top_priority_score_latest is not null",
        "and average_priority_score_delta is not null",
        "and source_queue_count_delta is not null",
    ):
        assert nullable_invariant in body


def test_migration_creates_ordered_trend_source_manifest_table() -> None:
    body = _table_body(_migration_sql(), DEFAULT_SOURCES_TABLE)

    for column in (
        "trend_sha256 text not null",
        "trend_ordinal integer not null",
        "source_input_position integer not null",
        "snapshot_sha256 text not null",
        "source_generated_at timestamptz not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body
    assert "primary key (trend_sha256, trend_ordinal)" in body
    assert (
        "foreign key (trend_sha256) references "
        "public.paper_action_gated_queue_decision_support_trend_reports(trend_sha256) "
        "on delete cascade"
    ) in body
    assert (
        "foreign key (snapshot_sha256) references "
        "public.paper_action_gated_strategy_recommendation_queue_decision_support_reports(snapshot_sha256)"
    ) in body


def test_migration_enforces_source_manifest_invariants_with_checks() -> None:
    body = _table_body(_migration_sql(), DEFAULT_SOURCES_TABLE)

    for expected_check in (
        "check (trend_sha256 ~ '^[a-f0-9]{64}$')",
        "check (snapshot_sha256 ~ '^[a-f0-9]{64}$')",
        "check (trend_ordinal >= 1)",
        "check (source_input_position >= 1)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body


def test_migration_adds_useful_short_indexes() -> None:
    sql = _compact(_migration_sql())

    for index in (
        "create index if not exists idx_pagqdst_generated_at on "
        "public.paper_action_gated_queue_decision_support_trend_reports "
        "(generated_at desc);",
        "create index if not exists idx_pagqdst_risk_generated on "
        "public.paper_action_gated_queue_decision_support_trend_reports "
        "(latest_risk_status, generated_at desc);",
        "create index if not exists idx_pagqdst_inserted on "
        "public.paper_action_gated_queue_decision_support_trend_reports "
        "(generated_at desc, inserted_at desc, trend_sha256 desc);",
        "create index if not exists idx_pagqdst_src_snapshot on "
        "public.paper_action_gated_queue_decision_support_trend_sources "
        "(snapshot_sha256);",
        "create index if not exists idx_pagqdst_src_generated on "
        "public.paper_action_gated_queue_decision_support_trend_sources "
        "(source_generated_at desc);",
    ):
        assert index in sql


def test_migration_keeps_new_table_and_index_names_under_postgres_limit() -> None:
    sql = _migration_sql()
    names = set(
        re.findall(
            r"create\s+table\s+if\s+not\s+exists\s+public\.([a-z0-9_]+)",
            sql,
            flags=re.IGNORECASE,
        )
    )
    names.update(
        re.findall(
            r"create\s+(?:unique\s+)?index\s+if\s+not\s+exists\s+([a-z0-9_]+)",
            sql,
            flags=re.IGNORECASE,
        )
    )

    assert DEFAULT_REPORTS_TABLE in names
    assert DEFAULT_SOURCES_TABLE in names
    assert names
    assert all(len(name) <= 63 for name in names)


def test_docs_state_trend_db_persistence_scope() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    normalized = re.sub(r"\s+", " ", text)

    for phrase in (
        "Trend DB persistence stores compact scalar trend summaries",
        "ordered source snapshot references",
        "does not duplicate priority/risk payloads",
        "does not provide full trend hydration",
        "polymarket-alpha-lab action-gated-queue-decision-support-trend",
        "Without `--persist`, the command is a read/report-only trend summary",
        "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE",
        "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE",
    ):
        assert phrase in normalized

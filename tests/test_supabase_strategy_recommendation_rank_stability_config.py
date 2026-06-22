from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import re

import pytest


MIGRATION_PATH = Path(
    "supabase/migrations/20260622000003_strategy_recommendation_rank_stability_reports.sql",
)
ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_STRATEGY_RECOMMENDATION_RANK_STABILITY_DB_ENABLED"
)
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_STRATEGY_RECOMMENDATION_RANK_STABILITY_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_STRATEGY_RECOMMENDATION_RANK_STABILITY_DB_TABLE"
DEFAULT_TABLE = "strategy_recommendation_rank_stability_reports"


def _config_module():
    import polymarket_alpha_lab.supabase_strategy_recommendation_rank_stability_config as config_module

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


def test_disabled_env_config_uses_default_table_and_accepts_absent_dsn() -> None:
    config_module = _config_module()

    config = config_module.from_strategy_recommendation_rank_stability_db_env({})

    assert config == config_module.SupabaseStrategyRecommendationRankStabilityConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    unrelated_secret = "postgresql://topsecret.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_strategy_recommendation_rank_stability_db_env(
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
        config_module.from_strategy_recommendation_rank_stability_db_env(
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

    config = config_module.from_strategy_recommendation_rank_stability_db_env(
        {
            ENABLED_ENV_VAR: enabled_value,
            DSN_ENV_VAR: "postgresql://example.invalid/postgres",
        },
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", [" TRUE ", "true ", " false", "TRUE", "False"])
def test_enabled_env_config_accepts_padded_and_casefolded_boolean_values(
    enabled_value: str,
) -> None:
    config_module = _config_module()

    config = config_module.from_strategy_recommendation_rank_stability_db_env(
        {
            ENABLED_ENV_VAR: enabled_value,
            DSN_ENV_VAR: "postgresql://example.invalid/postgres",
        },
    )

    assert config.enabled is (enabled_value.strip().lower() in {"1", "true"})


@pytest.mark.parametrize("enabled_value", ["yes", "on", "2"])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_strategy_recommendation_rank_stability_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: "postgresql://example.invalid/postgres",
            },
        )

    assert ENABLED_ENV_VAR in str(exc_info.value)


def test_enabled_env_config_reads_explicit_dsn_and_table_name() -> None:
    config_module = _config_module()
    dsn = "postgresql://example.invalid/postgres"

    config = config_module.from_strategy_recommendation_rank_stability_db_env(
        {
            ENABLED_ENV_VAR: "true",
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "rank_stability_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "rank_stability_archive"


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabaseStrategyRecommendationRankStabilityConfig(
        enabled=True,
        dsn="postgresql://topsecret.example.invalid/postgres",
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "topsecret" not in rendered
    assert "postgresql://topsecret" not in rendered
    assert "dsn=<redacted>" in rendered
    assert DEFAULT_TABLE in rendered


def test_disabled_config_repr_shows_absent_dsn_without_secret_shape() -> None:
    config_module = _config_module()

    rendered = repr(
        config_module.SupabaseStrategyRecommendationRankStabilityConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_TABLE,
        ),
    )

    assert "dsn=None" in rendered
    assert "<redacted>" not in rendered
    assert "postgresql://" not in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "StrategyRecommendationRankStabilityReports",
        "strategy-recommendation-rank-stability-reports",
        "audit.strategy_recommendation_rank_stability_reports",
        "_strategy_recommendation_rank_stability_reports",
        "strategy_recommendation_rank_stability_reports_",
        "a",
        "",
    ],
)
def test_table_name_must_be_simple_lowercase_identifier(
    table_name: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(
        ValueError,
        match="simple lowercase identifier",
    ):
        config_module.SupabaseStrategyRecommendationRankStabilityConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "rank_stability_archive",
        "rank_1_stability_2_archive",
    ],
)
def test_table_name_accepts_simple_lowercase_identifier_values(
    table_name: str,
) -> None:
    config_module = _config_module()

    config = config_module.SupabaseStrategyRecommendationRankStabilityConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_strategy_recommendation_rank_stability_db_env(
            {TABLE_ENV_VAR: "StrategyRecommendationRankStabilityReports"},
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        config_module.SupabaseStrategyRecommendationRankStabilityConfig(
            enabled=1,
            dsn="postgresql://example.invalid/postgres",
            table_name=DEFAULT_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabaseStrategyRecommendationRankStabilityConfig(
            enabled=True,
            dsn=object(),
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_include_constants_config_and_loader_in_order() -> None:
    config_module = _config_module()

    assert config_module.__all__ == (
        "STRATEGY_RECOMMENDATION_RANK_STABILITY_DB_DSN_ENV_VAR",
        "STRATEGY_RECOMMENDATION_RANK_STABILITY_DB_ENABLED_ENV_VAR",
        "STRATEGY_RECOMMENDATION_RANK_STABILITY_DB_TABLE_ENV_VAR",
        "DEFAULT_STRATEGY_RECOMMENDATION_RANK_STABILITY_DB_TABLE",
        "SupabaseStrategyRecommendationRankStabilityConfig",
        "from_strategy_recommendation_rank_stability_db_env",
    )


def test_migration_creates_rank_stability_report_table() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "stability_status text not null",
        "reason_codes_json jsonb not null",
        "source_report_count integer not null",
        "candidate_count integer not null",
        "stable_count integer not null",
        "watch_count integer not null",
        "blocked_count integer not null",
        "stable_ready_count integer not null",
        "unstable_ready_count integer not null",
        "selected_side_changed_count integer not null",
        "queue_status_changed_count integer not null",
        "latest_generated_at timestamptz null",
        "top_stable_market_slug text null",
        "rows_json jsonb not null",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in body


def test_migration_enforces_row_scalar_and_payload_invariants() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    for expected_check in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (stability_status in ('stable', 'watch', 'blocked'))",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (source_report_count >= 0)",
        "check (candidate_count >= 0)",
        "check (stable_count >= 0)",
        "check (watch_count >= 0)",
        "check (blocked_count >= 0)",
        "check (stable_ready_count >= 0)",
        "check (unstable_ready_count >= 0)",
        "check (selected_side_changed_count >= 0)",
        "check (queue_status_changed_count >= 0)",
        "check (stable_count + watch_count + blocked_count = candidate_count)",
        "check (jsonb_typeof(rows_json) = 'array')",
        "check (jsonb_array_length(rows_json) = candidate_count)",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body


def test_migration_enforces_payload_scalar_parity() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    for expected_check in (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (payload_json ? 'stability_status' and jsonb_typeof(payload_json -> 'stability_status') = 'string' and payload_json ->> 'stability_status' = stability_status)",
        "check (payload_json ? 'source_report_count' and jsonb_typeof(payload_json -> 'source_report_count') = 'number' and (payload_json ->> 'source_report_count')::integer = source_report_count)",
        "check (payload_json ? 'candidate_count' and jsonb_typeof(payload_json -> 'candidate_count') = 'number' and (payload_json ->> 'candidate_count')::integer = candidate_count)",
        "check (payload_json ? 'stable_count' and jsonb_typeof(payload_json -> 'stable_count') = 'number' and (payload_json ->> 'stable_count')::integer = stable_count)",
        "check (payload_json ? 'watch_count' and jsonb_typeof(payload_json -> 'watch_count') = 'number' and (payload_json ->> 'watch_count')::integer = watch_count)",
        "check (payload_json ? 'blocked_count' and jsonb_typeof(payload_json -> 'blocked_count') = 'number' and (payload_json ->> 'blocked_count')::integer = blocked_count)",
        "check (payload_json ? 'stable_ready_count' and jsonb_typeof(payload_json -> 'stable_ready_count') = 'number' and (payload_json ->> 'stable_ready_count')::integer = stable_ready_count)",
        "check (payload_json ? 'unstable_ready_count' and jsonb_typeof(payload_json -> 'unstable_ready_count') = 'number' and (payload_json ->> 'unstable_ready_count')::integer = unstable_ready_count)",
        "check (payload_json ? 'selected_side_changed_count' and jsonb_typeof(payload_json -> 'selected_side_changed_count') = 'number' and (payload_json ->> 'selected_side_changed_count')::integer = selected_side_changed_count)",
        "check (payload_json ? 'queue_status_changed_count' and jsonb_typeof(payload_json -> 'queue_status_changed_count') = 'number' and (payload_json ->> 'queue_status_changed_count')::integer = queue_status_changed_count)",
        "check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and payload_json -> 'reason_codes' = reason_codes_json)",
        "check (payload_json ? 'rows' and jsonb_typeof(payload_json -> 'rows') = 'array' and payload_json -> 'rows' = rows_json)",
    ):
        assert expected_check in body


def test_migration_uses_numeric_safe_payloads_and_no_float_columns() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    assert "rows_json jsonb" in body
    assert "payload_json jsonb" in body
    assert "reason_codes_json jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_short_indexes() -> None:
    sql = _compact(_migration_sql())

    for index in (
        "create index if not exists idx_srrsr_generated_at on "
        "public.strategy_recommendation_rank_stability_reports (generated_at desc);",
        "create index if not exists idx_srrsr_status_generated on "
        "public.strategy_recommendation_rank_stability_reports (stability_status, generated_at desc);",
        "create index if not exists idx_srrsr_config_generated on "
        "public.strategy_recommendation_rank_stability_reports (config_version, generated_at desc);",
        "create index if not exists idx_srrsr_reason_codes_json on "
        "public.strategy_recommendation_rank_stability_reports using gin (reason_codes_json);",
        "create index if not exists idx_srrsr_rows_json on "
        "public.strategy_recommendation_rank_stability_reports using gin (rows_json);",
        "create index if not exists idx_srrsr_payload_json on "
        "public.strategy_recommendation_rank_stability_reports using gin (payload_json);",
    ):
        assert index in sql


def test_migration_keeps_table_and_index_names_under_postgres_limit() -> None:
    sql = _migration_sql()
    names = set(
        re.findall(
            r"create\s+table\s+if\s+not\s+exists\s+public\.([a-z0-9_]+)",
            sql,
            flags=re.IGNORECASE,
        ),
    )
    names.update(
        re.findall(
            r"create\s+(?:unique\s+)?index\s+if\s+not\s+exists\s+([a-z0-9_]+)",
            sql,
            flags=re.IGNORECASE,
        ),
    )

    assert DEFAULT_TABLE in names
    assert names
    assert all(len(name) <= 63 for name in names)


def test_migration_does_not_include_live_trading_or_account_terms() -> None:
    sql = _migration_sql().lower()

    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\border\b",
        r"\bsubmit(?:s|ted|ting|tal)?\b",
        r"\bcancel(?:s|ed|ing|lation)?\b",
        r"\bsign(?:s|ed|ing|ature)?\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

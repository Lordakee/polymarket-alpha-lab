from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED"
)
DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN"
)
TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE"
)
DEFAULT_TABLE = "paper_autonomous_screening_decision_support_gate_reports"
CONFIG_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_paper_autonomous_screening_decision_support_gate_config.py"
)
MIGRATION_PATH = Path(
    "supabase/migrations/"
    "20260623000002_paper_autonomous_screening_decision_support_gate_reports.sql",
)


def _config_module():
    import polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_config as config_module

    return config_module


def test_public_constants_match_expected_env_surface() -> None:
    config_module = _config_module()
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE,
    )

    assert (
        config_module.PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR
        == ENABLED_ENV_VAR
    )
    assert (
        config_module.PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR
        == DSN_ENV_VAR
    )
    assert (
        config_module.PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR
        == TABLE_ENV_VAR
    )
    assert (
        config_module.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE
        == DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE
        == DEFAULT_TABLE
    )
    assert (
        "SupabasePaperAutonomousScreeningDecisionSupportGateConfig"
        in config_module.__all__
    )
    assert (
        "from_paper_autonomous_screening_decision_support_gate_db_env"
        in config_module.__all__
    )


def test_default_table_constant_is_imported_from_store_to_avoid_drift() -> None:
    source = CONFIG_SOURCE.read_text(encoding="utf-8")

    assert (
        "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE"
        in source
    )
    assert '"paper_autonomous_screening_decision_support_gate_reports"' not in source


def test_disabled_env_config_accepts_missing_dsn() -> None:
    config_module = _config_module()

    config = config_module.from_paper_autonomous_screening_decision_support_gate_db_env(
        {},
    )

    assert config == (
        config_module.SupabasePaperAutonomousScreeningDecisionSupportGateConfig(
            enabled=False,
            dsn=None,
            table_name=DEFAULT_TABLE,
        )
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_screening_decision_support_gate_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: " ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "sensitive-token" not in message


def test_enabled_env_config_reads_explicit_dsn_at_process_edge() -> None:
    config_module = _config_module()
    dsn = "postgresql://example.invalid/postgres"

    config = config_module.from_paper_autonomous_screening_decision_support_gate_db_env(
        {
            ENABLED_ENV_VAR: "1",
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "paper_autonomous_screening_gate_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_autonomous_screening_gate_archive"


@pytest.mark.parametrize(
    ("enabled_value", "expected_enabled"),
    [
        ("", False),
        ("0", False),
        ("false", False),
        (" FALSE ", False),
        ("1", True),
        ("true", True),
        (" TRUE ", True),
    ],
)
def test_enabled_env_config_accepts_only_strict_values(
    enabled_value: str,
    expected_enabled: bool,
) -> None:
    config_module = _config_module()

    config = config_module.from_paper_autonomous_screening_decision_support_gate_db_env(
        {
            ENABLED_ENV_VAR: enabled_value,
            DSN_ENV_VAR: "postgresql://example.invalid/postgres",
        },
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", ["yes", "on", "2"])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
        config_module.from_paper_autonomous_screening_decision_support_gate_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: "postgresql://example.invalid/postgres",
            },
        )


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabasePaperAutonomousScreeningDecisionSupportGateConfig(
        enabled=True,
        dsn="postgresql://sensitive-token.example.invalid/postgres",
        table_name=DEFAULT_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert "postgresql://sensitive-token" not in rendered
    assert "dsn=<redacted>" in rendered
    assert DEFAULT_TABLE in rendered


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperReports",
        "paper-reports",
        "paper.reports",
        "_paper_reports",
        "paper_reports_",
        "a",
        "",
    ],
)
def test_table_name_must_match_store_simple_lowercase_identifier(
    table_name: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        config_module.SupabasePaperAutonomousScreeningDecisionSupportGateConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "paper_autonomous_screening_gate_archive",
        "gate_1_archive_2",
    ],
)
def test_table_name_accepts_simple_lowercase_identifier_values(
    table_name: str,
) -> None:
    config_module = _config_module()

    config = config_module.SupabasePaperAutonomousScreeningDecisionSupportGateConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_env_table_name_error_mentions_variable_name() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_screening_decision_support_gate_db_env(
            {TABLE_ENV_VAR: "PaperReports"},
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        config_module.SupabasePaperAutonomousScreeningDecisionSupportGateConfig(
            enabled=1,
            dsn="postgresql://example.invalid/postgres",
            table_name=DEFAULT_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabasePaperAutonomousScreeningDecisionSupportGateConfig(
            enabled=True,
            dsn=object(),
            table_name=DEFAULT_TABLE,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "object at 0x" not in message


def test_public_exports_include_constants_config_and_loader() -> None:
    config_module = _config_module()

    assert config_module.__all__ == (
        "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE",
        "PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR",
        "PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR",
        "PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR",
        "SupabasePaperAutonomousScreeningDecisionSupportGateConfig",
        "from_paper_autonomous_screening_decision_support_gate_db_env",
    )


def test_migration_defines_autonomous_screening_gate_report_table() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        _SELECT_COLUMNS,
    )

    assert (
        "create table if not exists "
        "public.paper_autonomous_screening_decision_support_gate_reports"
    ) in sql
    table_body = sql.split(
        "create table if not exists "
        "public.paper_autonomous_screening_decision_support_gate_reports (",
        1,
    )[1].split("\n);", 1)[0]
    migration_columns = {
        stripped.removesuffix(",").split()[0]
        for line in table_body.splitlines()
        if (stripped := line.strip())
        and not stripped.startswith("check ")
    }
    assert migration_columns == {*_SELECT_COLUMNS, "inserted_at"}
    assert "inserted_at timestamptz not null default now()" in sql
    for stale_column in (
        "source_config_version",
        "source_generated_at",
        "source_report_count",
        "latest_source_generated_at",
        "latest_source_age_seconds",
        "candidate_count",
        "approved_count",
        "review_count",
        "total_approved_notional",
        "reason_code_counts jsonb",
        "payload jsonb",
    ):
        if " " in stale_column:
            assert stale_column not in sql
        else:
            assert stale_column not in migration_columns
    assert "check (report_sha256 ~ '^[a-f0-9]{64}$')" in sql
    assert "check (gate_status in ('pass', 'watch', 'blocked'))" in sql
    assert "check (operator_flow_gate_status in ('pass', 'watch', 'blocked'))" in sql
    assert "check (queue_risk_status in ('pass', 'watch', 'blocked'))" in sql
    assert "check (trend_latest_risk_status is null or trend_latest_risk_status in ('pass', 'watch', 'blocked'))" in sql
    assert "check (rank_stability_status is null or rank_stability_status in ('stable', 'watch', 'blocked'))" in sql
    assert "check (jsonb_typeof(reason_codes_json) = 'array')" in sql
    assert "check (jsonb_typeof(reason_code_counts_json) = 'array')" in sql
    assert "check (jsonb_typeof(payload_json) = 'object')" in sql
    for nonnegative_column in (
        "queue_source_report_count",
        "queue_research_ready_count",
        "queue_watch_count",
        "queue_blocked_count",
        "queue_candidate_count",
        "queue_ready_count",
        "queue_candidate_watch_count",
        "queue_candidate_blocked_count",
        "queue_total_ready_notional",
        "queue_largest_ready_notional",
        "queue_top_research_priority_score",
        "queue_average_research_priority_score",
    ):
        assert f"check ({nonnegative_column} >= 0)" in sql
    for nullable_nonnegative_column in (
        "trend_source_snapshot_count",
        "trend_consecutive_latest_watch_count",
        "trend_consecutive_latest_blocked_count",
        "trend_duplicate_generated_at_count",
        "rank_stable_ready_count",
        "rank_unstable_ready_count",
        "rank_blocked_count",
    ):
        assert (
            "check "
            f"({nullable_nonnegative_column} is null or "
            f"{nullable_nonnegative_column} >= 0)"
        ) in sql
    for hard_flag in ("paper_only", "report_only", "readonly"):
        assert f"check ({hard_flag} is true)" in sql
    for index_fragment in (
        "(generated_at desc)",
        "(gate_status, generated_at desc)",
        "(config_version, generated_at desc)",
        "(operator_flow_gate_status, generated_at desc)",
        "(queue_risk_config_version, generated_at desc)",
        "(gate_status, generated_at desc, inserted_at desc, report_sha256 desc)",
    ):
        assert index_fragment in sql

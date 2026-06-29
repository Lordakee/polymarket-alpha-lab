from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import re

import pytest


ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED"
)
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN"
TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE"
DEFAULT_TABLE = "paper_autonomous_allocation_proposal_reports"
CONFIG_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_paper_autonomous_allocation_proposal_config.py"
)
MIGRATION_PATH = Path(
    "supabase/migrations/"
    "20260623000003_paper_autonomous_allocation_proposal_reports.sql",
)


def _config_module():
    import polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_config as config_module

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


def test_public_constants_match_expected_env_surface() -> None:
    config_module = _config_module()
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_REPORTS_TABLE,
    )

    assert (
        config_module.PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR
        == ENABLED_ENV_VAR
    )
    assert config_module.PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR == (
        DSN_ENV_VAR
    )
    assert config_module.PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR == (
        TABLE_ENV_VAR
    )
    assert (
        config_module.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE
        == DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_REPORTS_TABLE
        == DEFAULT_TABLE
    )


def test_default_table_constant_is_imported_from_store_to_avoid_drift() -> None:
    source = CONFIG_SOURCE.read_text(encoding="utf-8")

    assert "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_REPORTS_TABLE" in source
    assert '"paper_autonomous_allocation_proposal_reports"' not in source


def test_disabled_env_config_accepts_missing_dsn() -> None:
    config_module = _config_module()

    config = config_module.from_paper_autonomous_allocation_proposal_db_env({})

    assert config == config_module.SupabasePaperAutonomousAllocationProposalConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    config_module = _config_module()
    secret_dsn = "postgresql://sensitive-token@localhost/postgres"

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_allocation_proposal_db_env(
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


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://localhost/postgres",
        "postgres://localhost:54322/postgres",
        "postgresql://user:password@127.0.0.1:5432/postgres",
        "postgresql://user:password@[::1]:5432/postgres",
    ],
)
def test_enabled_env_config_accepts_local_postgres_dsns(dsn: str) -> None:
    config_module = _config_module()

    config = config_module.from_paper_autonomous_allocation_proposal_db_env(
        {
            ENABLED_ENV_VAR: "1",
            DSN_ENV_VAR: dsn,
            TABLE_ENV_VAR: "audit.paper_autonomous_allocation_proposal_archive",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "audit.paper_autonomous_allocation_proposal_archive"


@pytest.mark.parametrize(
    "dsn",
    [
        "postgresql://example.invalid/postgres",
        "postgres://db.example.com/postgres",
        "postgresql://192.168.1.10/postgres",
    ],
)
def test_enabled_env_config_rejects_remote_postgres_dsns_without_echoing_dsn(
    dsn: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_allocation_proposal_db_env(
            {
                ENABLED_ENV_VAR: "true",
                DSN_ENV_VAR: dsn,
            },
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert "local Postgres" in message
    assert dsn not in message
    assert "example.invalid" not in message
    assert "db.example.com" not in message
    assert "192.168.1.10" not in message


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

    config = config_module.from_paper_autonomous_allocation_proposal_db_env(
        {
            ENABLED_ENV_VAR: enabled_value,
            DSN_ENV_VAR: "postgresql://localhost/postgres",
        },
    )

    assert config.enabled is expected_enabled


@pytest.mark.parametrize("enabled_value", ["yes", "on", "2"])
def test_enabled_env_config_rejects_non_strict_values(enabled_value: str) -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match=ENABLED_ENV_VAR):
        config_module.from_paper_autonomous_allocation_proposal_db_env(
            {
                ENABLED_ENV_VAR: enabled_value,
                DSN_ENV_VAR: "postgresql://localhost/postgres",
            },
        )


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    config_module = _config_module()
    config = config_module.SupabasePaperAutonomousAllocationProposalConfig(
        enabled=True,
        dsn="postgresql://sensitive-token@localhost/postgres",
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
        "paper..reports",
        "paper.reports.extra",
        "_paper_reports",
        "paper_reports_",
        "",
    ],
)
def test_table_name_must_match_store_lowercase_identifier_contract(
    table_name: str,
) -> None:
    config_module = _config_module()

    with pytest.raises(
        ValueError,
        match="table_name must be a lowercase identifier with optional schema prefix",
    ):
        config_module.SupabasePaperAutonomousAllocationProposalConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )


@pytest.mark.parametrize(
    "table_name",
    [
        "a",
        "a0",
        "paper_autonomous_allocation_proposal_archive",
        "audit.paper_autonomous_allocation_proposal_archive",
        "proposal_1_archive_2",
    ],
)
def test_table_name_accepts_lowercase_identifier_values(
    table_name: str,
) -> None:
    config_module = _config_module()

    config = config_module.SupabasePaperAutonomousAllocationProposalConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_table_name_accepts_postgres_identifier_at_length_limit() -> None:
    config_module = _config_module()
    table_name = "a" * 63

    config = config_module.SupabasePaperAutonomousAllocationProposalConfig(
        enabled=False,
        dsn=None,
        table_name=table_name,
    )

    assert config.table_name == table_name


def test_table_name_rejects_postgres_identifier_over_length_limit() -> None:
    config_module = _config_module()

    with pytest.raises(
        ValueError,
        match="table_name must be a lowercase identifier with optional schema prefix",
    ):
        config_module.SupabasePaperAutonomousAllocationProposalConfig(
            enabled=False,
            dsn=None,
            table_name="a" * 64,
        )


def test_env_table_name_error_mentions_variable_name() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.from_paper_autonomous_allocation_proposal_db_env(
            {TABLE_ENV_VAR: "PaperReports"},
        )

    assert TABLE_ENV_VAR in str(exc_info.value)


def test_direct_config_rejects_non_bool_enabled_flag() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError, match="enabled must be a bool"):
        config_module.SupabasePaperAutonomousAllocationProposalConfig(
            enabled=1,
            dsn="postgresql://localhost/postgres",
            table_name=DEFAULT_TABLE,
        )


def test_direct_config_rejects_non_string_dsn_without_echoing_value() -> None:
    config_module = _config_module()

    with pytest.raises(ValueError) as exc_info:
        config_module.SupabasePaperAutonomousAllocationProposalConfig(
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
        "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE",
        "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR",
        "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR",
        "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR",
        "SupabasePaperAutonomousAllocationProposalConfig",
        "from_paper_autonomous_allocation_proposal_db_env",
    )


def test_migration_defines_allocation_proposal_report_table() -> None:
    sql = _migration_sql()
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        _SELECT_COLUMNS,
    )

    assert (
        "create table if not exists "
        "public.paper_autonomous_allocation_proposal_reports"
    ) in sql
    table_body = sql.split(
        "create table if not exists "
        "public.paper_autonomous_allocation_proposal_reports (",
        1,
    )[1].split("\n);", 1)[0]
    migration_columns = {
        stripped.removesuffix(",").split()[0]
        for line in table_body.splitlines()
        if (stripped := line.strip()) and not stripped.startswith("check ")
    }
    assert migration_columns == {*_SELECT_COLUMNS, "inserted_at"}
    assert "inserted_at timestamptz not null default now()" in sql


def test_migration_enforces_row_scalar_json_and_hard_flag_invariants() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    for expected_check in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (proposal_status in ('pass', 'watch', 'blocked'))",
        "check (screening_gate_status in ('pass', 'watch', 'blocked'))",
        "check (queue_risk_status in ('pass', 'watch', 'blocked'))",
        "check (recommended_next_step = case proposal_status when 'pass' then 'review_paper_autonomous_allocation_proposal' when 'watch' then 'hold_paper_autonomous_allocation_proposal' when 'blocked' then 'block_paper_autonomous_allocation_proposal' end)",
        "check (jsonb_typeof(reason_codes_json) = 'array')",
        "check (jsonb_typeof(reason_code_counts_json) = 'array')",
        "check (jsonb_typeof(allocation_rows_json) = 'array')",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    ):
        assert expected_check in body


def test_migration_enforces_nonnegative_counts_and_notional_values() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    for nonnegative_column in (
        "source_queue_report_count",
        "source_queue_ready_count",
        "source_queue_watch_count",
        "source_queue_blocked_count",
        "allocation_input_count",
        "allocation_row_count",
        "allocation_allocated_count",
        "allocation_capped_count",
        "allocation_no_budget_count",
        "allocation_non_recommend_count",
        "allocation_skipped_count",
        "allocation_total_requested_paper_notional",
        "allocation_total_allocated_paper_notional",
        "allocation_remaining_paper_budget",
        "allocation_total_paper_budget",
        "allocation_max_paper_notional_per_market",
        "allocation_max_paper_notional_per_event",
        "allocation_max_paper_notional_per_theme",
        "allocation_max_paper_notional_per_correlation_group",
    ):
        assert f"check ({nonnegative_column} >= 0)" in body


def test_migration_enforces_payload_scalar_parity() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    for expected_check in (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (payload_json ? 'proposal_status' and jsonb_typeof(payload_json -> 'proposal_status') = 'string' and payload_json ->> 'proposal_status' = proposal_status)",
        "check (payload_json ? 'recommended_next_step' and jsonb_typeof(payload_json -> 'recommended_next_step') = 'string' and payload_json ->> 'recommended_next_step' = recommended_next_step)",
        "check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and payload_json -> 'reason_codes' = reason_codes_json)",
        "check (payload_json ? 'reason_code_counts' and jsonb_typeof(payload_json -> 'reason_code_counts') = 'array' and payload_json -> 'reason_code_counts' = reason_code_counts_json)",
        "check (payload_json ? 'allocation_report' and jsonb_typeof(payload_json -> 'allocation_report') = 'object')",
        "check (payload_json -> 'allocation_report' ? 'rows' and jsonb_typeof(payload_json -> 'allocation_report' -> 'rows') = 'array' and payload_json -> 'allocation_report' -> 'rows' = allocation_rows_json)",
    ):
        assert expected_check in body


def test_migration_uses_numeric_safe_payloads_and_no_float_columns() -> None:
    body = _table_body(_migration_sql(), DEFAULT_TABLE)

    assert "allocation_rows_json jsonb" in body
    assert "payload_json jsonb" in body
    assert "reason_codes_json jsonb" in body
    assert "reason_code_counts_json jsonb" in body
    assert "double precision" not in body
    assert "real" not in body
    assert "float" not in body


def test_migration_adds_useful_indexes() -> None:
    sql = _compact(_migration_sql())

    for index in (
        "create index if not exists idx_paapr_generated_at on public.paper_autonomous_allocation_proposal_reports (generated_at desc);",
        "create index if not exists idx_paapr_status_generated on public.paper_autonomous_allocation_proposal_reports (proposal_status, generated_at desc);",
        "create index if not exists idx_paapr_config_generated on public.paper_autonomous_allocation_proposal_reports (config_version, generated_at desc);",
        "create index if not exists idx_paapr_screening_status_generated on public.paper_autonomous_allocation_proposal_reports (screening_gate_status, generated_at desc);",
        "create index if not exists idx_paapr_allocation_config_generated on public.paper_autonomous_allocation_proposal_reports (allocation_config_version, generated_at desc);",
        "create index if not exists idx_paapr_reason_codes_json on public.paper_autonomous_allocation_proposal_reports using gin (reason_codes_json);",
        "create index if not exists idx_paapr_allocation_rows_json on public.paper_autonomous_allocation_proposal_reports using gin (allocation_rows_json);",
        "create index if not exists idx_paapr_payload_json on public.paper_autonomous_allocation_proposal_reports using gin (payload_json);",
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


def test_migration_does_not_include_live_terms() -> None:
    sql = _migration_sql().lower()

    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\bsubmit(?:s|ted|ting|tal)?\b",
        r"\bcancel(?:s|ed|ing|lation)?\b",
        r"\bsign(?:s|ed|ing|ature)?\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern

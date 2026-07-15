import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260701000000_team_forecast_tables.sql"
)
PROBABILITY_YES_CONTRACT_MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260713000000_team_forecast_probability_yes_contract.sql"
)


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def probability_yes_contract_migration_sql() -> str:
    assert PROBABILITY_YES_CONTRACT_MIGRATION.exists(), (
        f"missing migration: {PROBABILITY_YES_CONTRACT_MIGRATION}"
    )
    return PROBABILITY_YES_CONTRACT_MIGRATION.read_text(encoding="utf-8")


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str, table_name: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        rf"public\.{re.escape(table_name)}\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, f"migration must create public.{table_name}"
    return compact(match.group(1))


def assert_has_columns(body: str, required_columns: tuple[str, ...]) -> None:
    for column in required_columns:
        assert column in body


def assert_on_conflict_compatible_key(body: str, column_name: str) -> None:
    compatible_patterns = (
        f"{column_name} text primary key",
        f"{column_name} text not null primary key",
        f"{column_name} text unique",
        f"{column_name} text not null unique",
        f"primary key ({column_name})",
        f"unique ({column_name})",
    )
    assert any(pattern in body for pattern in compatible_patterns), column_name


def test_migration_creates_team_forecast_tables():
    sql = migration_sql()

    for table_name in (
        "team_profiles",
        "team_market_routes",
        "team_forecasts",
        "team_forecast_evidence",
        "team_forecast_outcomes",
    ):
        table_body(sql, table_name)


def test_team_profiles_has_profile_columns_and_team_id_key():
    body = table_body(migration_sql(), "team_profiles")

    assert_has_columns(
        body,
        (
            "team_id text primary key",
            "display_name text not null",
            "primary_categories jsonb not null",
            "agent_roles jsonb not null",
            "paper_only boolean not null default true",
            "report_only boolean not null default true",
            "readonly boolean not null default true",
            "inserted_at timestamptz not null default now()",
        ),
    )
    assert "check (jsonb_typeof(primary_categories) = 'array')" in body
    assert "check (jsonb_typeof(agent_roles) = 'array')" in body


def test_route_forecast_and_evidence_columns_match_store_conflict_keys():
    sql = migration_sql()
    expected_columns = {
        "team_market_routes": (
            "payload_sha256 text",
            "generated_at timestamptz not null",
            "team_id text not null",
            "market_slug text not null",
            "config_version text not null",
            "condition_id text not null",
            "category_id text not null",
            "event_template text not null",
            "routing_confidence numeric not null",
            "payload_json jsonb not null",
            "paper_only boolean not null default true",
            "report_only boolean not null default true",
            "readonly boolean not null default true",
            "inserted_at timestamptz not null default now()",
        ),
        "team_forecasts": (
            "payload_sha256 text",
            "generated_at timestamptz not null",
            "forecast_id text not null",
            "condition_id text not null",
            "team_id text not null",
            "market_slug text not null",
            "config_version text not null",
            "selected_side text not null",
            "forecast_probability numeric not null",
            "confidence numeric not null",
            "payload_json jsonb not null",
            "paper_only boolean not null default true",
            "report_only boolean not null default true",
            "readonly boolean not null default true",
            "inserted_at timestamptz not null default now()",
        ),
        "team_forecast_evidence": (
            "payload_sha256 text",
            "generated_at timestamptz not null",
            "forecast_id text not null",
            "evidence_id text not null",
            "team_id text not null",
            "market_slug text not null",
            "config_version text not null",
            "source_id text not null",
            "data_timestamp timestamptz not null",
            "data_freshness_seconds integer not null",
            "evidence_type text not null",
            "weight numeric not null",
            "payload_json jsonb not null",
            "paper_only boolean not null default true",
            "report_only boolean not null default true",
            "readonly boolean not null default true",
            "inserted_at timestamptz not null default now()",
        ),
    }

    for table_name, columns in expected_columns.items():
        body = table_body(sql, table_name)
        assert_has_columns(body, columns)
        assert_on_conflict_compatible_key(body, "payload_sha256")


def test_outcomes_columns_match_store_and_outcome_id_conflict_key():
    body = table_body(migration_sql(), "team_forecast_outcomes")

    assert_has_columns(
        body,
        (
            "payload_sha256 text not null",
            "generated_at timestamptz not null",
            "outcome_id text",
            "forecast_id text not null",
            "team_id text not null",
            "market_slug text not null",
            "config_version text not null",
            "resolved_at timestamptz not null",
            "actual_outcome text not null",
            "forecast_error numeric not null",
            "brier_score numeric not null",
            "paper_pnl numeric not null",
            "cost_adjusted_return numeric not null",
            "directionally_correct boolean not null",
            "profitable_after_cost boolean not null",
            "resolution_dispute_flag boolean not null",
            "payload_json jsonb not null",
            "paper_only boolean not null default true",
            "report_only boolean not null default true",
            "readonly boolean not null default true",
            "inserted_at timestamptz not null default now()",
        ),
    )
    assert_on_conflict_compatible_key(body, "outcome_id")


def test_payload_tables_enforce_json_and_paper_report_readonly_safety():
    sql = migration_sql()

    for table_name in (
        "team_market_routes",
        "team_forecasts",
        "team_forecast_evidence",
        "team_forecast_outcomes",
    ):
        body = table_body(sql, table_name)
        for expected_check in (
            "check (jsonb_typeof(payload_json) = 'object')",
            "check ((payload_json ->> 'paper_only') = 'true')",
            "check ((payload_json ->> 'report_only') = 'true')",
            "check ((payload_json ->> 'readonly') = 'true')",
            "check (paper_only is true)",
            "check (report_only is true)",
            "check (readonly is true)",
        ):
            assert expected_check in body


def test_migration_enforces_store_scalar_invariants():
    sql = migration_sql()
    expected_checks = {
        "team_market_routes": (
            "check (payload_sha256 ~ '^[a-f0-9]{64}$')",
            "check (routing_confidence >= 0 and routing_confidence <= 1)",
        ),
        "team_forecasts": (
            "check (payload_sha256 ~ '^[a-f0-9]{64}$')",
            "check (selected_side in ('yes', 'no'))",
            "check (forecast_probability >= 0 and forecast_probability <= 1)",
            "check (confidence >= 0 and confidence <= 1)",
        ),
        "team_forecast_evidence": (
            "check (payload_sha256 ~ '^[a-f0-9]{64}$')",
            "check (data_freshness_seconds >= 0)",
            "check (weight >= 0 and weight <= 1)",
        ),
        "team_forecast_outcomes": (
            "check (payload_sha256 ~ '^[a-f0-9]{64}$')",
            "check (actual_outcome in ('yes', 'no'))",
            "check (forecast_error >= 0)",
            "check (brier_score >= 0)",
        ),
    }

    for table_name, checks in expected_checks.items():
        body = table_body(sql, table_name)
        for expected_check in checks:
            assert expected_check in body


def test_migration_adds_load_indexes_for_persistence_queries():
    sql = compact(migration_sql())

    expected_indexes = (
        "create index if not exists idx_team_forecasts_load on public.team_forecasts (team_id, market_slug, generated_at desc, inserted_at desc, payload_sha256 desc);",
        "create index if not exists idx_team_forecast_evidence_load on public.team_forecast_evidence (forecast_id, team_id, market_slug, generated_at desc, inserted_at desc, payload_sha256 desc);",
        "create index if not exists idx_team_forecast_outcomes_load on public.team_forecast_outcomes (team_id, market_slug, resolved_at desc, generated_at desc, inserted_at desc, outcome_id desc);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_non_phase_one_surfaces():
    sql = migration_sql().lower()

    forbidden_patterns = (
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\border\b",
        r"\baccount\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern


def test_probability_yes_contract_migration_contains_only_column_comments() -> None:
    sql = probability_yes_contract_migration_sql()
    expected_sql = """
    COMMENT ON COLUMN public.team_forecasts.forecast_probability IS
        'Canonical Decimal P(YES) for the event; never P(selected_side).';
    COMMENT ON COLUMN public.team_forecasts.selected_side IS
        'Paper-review side being evaluated; does not reorient forecast_probability.';
    """
    normalize_whitespace = lambda value: re.sub(r"\s+", " ", value.strip())
    assert normalize_whitespace(sql) == normalize_whitespace(expected_sql)

    forbidden_patterns = (
        r"\binsert\b",
        r"\bupdate\b",
        r"\bdelete\b",
        r"\balter\s+table\b",
        r"\bcreate\s+table\b",
        r"\bdrop\b",
        r"\bbegin\b",
        r"\bcommit\b",
        r"\brollback\b",
        r"\bsavepoint\b",
        r"\brelease\s+savepoint\b",
        r"\bstart\s+transaction\b",
        r"\bset\s+transaction\b",
        r"\bprepare\s+transaction\b",
    )
    for pattern in forbidden_patterns:
        assert re.search(pattern, sql, flags=re.IGNORECASE) is None, pattern

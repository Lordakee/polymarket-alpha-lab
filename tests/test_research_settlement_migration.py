from pathlib import Path


MIGRATION = Path("supabase/migrations/20260907000000_research_settlement.sql")


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_research_settlement_migration_is_local_owner_scoped() -> None:
    sql = _sql()
    assert "current_user <> 'postgres'" in sql
    assert "current_database() <> 'postgres'" in sql
    assert "CREATE SCHEMA IF NOT EXISTS research_settlement AUTHORIZATION postgres" in sql
    assert "ALTER TABLE research_settlement.research_settled_outcomes OWNER TO postgres" in sql


def test_research_settlement_migration_pins_outcome_and_readonly_contract() -> None:
    sql = _sql()
    assert "PRIMARY KEY (condition_id, observed_at)" in sql
    assert "outcome IN ('yes', 'no')" in sql
    assert "jsonb_typeof(outcome_prices_snapshot) = 'array'" in sql
    assert "payload_sha256 ~ '^[a-f0-9]{64}$'" in sql
    for flag in ("paper_only", "report_only", "readonly"):
        assert f"CHECK ({flag} IS true)" in sql


def test_research_settlement_migration_enables_rls_and_revokes_platform_roles() -> None:
    sql = _sql()
    assert "ENABLE ROW LEVEL SECURITY" in sql
    for role in ("PUBLIC", "anon", "authenticated", "service_role"):
        assert (
            "REVOKE ALL ON TABLE research_settlement.research_settled_outcomes "
            f"FROM {role}"
        ) in sql

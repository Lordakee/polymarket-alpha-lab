from pathlib import Path


MIGRATION = Path(__file__).parents[1] / "supabase" / "migrations" / "20260731000000_central_data_evidence.sql"


def test_migration_uses_internal_schema_and_hard_flags() -> None:
    sql = MIGRATION.read_text()
    assert "CREATE SCHEMA IF NOT EXISTS central_data_internal" in sql
    assert "raw_body bytea NOT NULL" in sql
    assert "octet_length(raw_body) <= 2097152" in sql
    assert "pg_catalog.sha256(raw_body)" in sql
    assert "paper_only IS true" in sql
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "CREATE POLICY" not in sql
    assert "ON DELETE CASCADE" not in sql.upper()
    assert "CHECK (parse_state IN ('success', 'failed', 'unknown'))" in sql
    assert "CHECK (freshness_state IN ('fresh', 'stale', 'unknown'))" in sql
    assert "CHECK (value_state IN ('present', 'null', 'zero', 'unknown'))" in sql


def test_migration_pins_cron_contract_and_audit_before_delete() -> None:
    sql = MIGRATION.read_text()
    assert "CREATE EXTENSION IF NOT EXISTS pg_cron;" in sql
    assert "cron.schedule_in_database" in sql
    assert "'central_data_raw_retention_15m'" in sql
    assert "'*/15 * * * *'" in sql
    assert "database = 'postgres'" in sql
    assert "username = 'postgres'" in sql
    assert "INSERT INTO central_data_internal.central_data_raw_retention_audit" in sql
    assert "DELETE FROM central_data_internal.central_data_raw_response_events" in sql
    assert "FOR UPDATE SKIP LOCKED" in sql
    assert "cron.unschedule" not in sql
    assert "extract(epoch FROM v_row.expires_at)::text" in sql


def test_migration_retention_checks_are_timestamp_difference_based() -> None:
    sql = MIGRATION.read_text()
    assert "expires_at - retrieval_time = interval '29 days'" in sql
    assert "expires_at - retrieval_time <= interval '30 days'" in sql
    assert "expires_at > statement_timestamp()" not in sql.split("CREATE TABLE", 1)[1].split("CREATE INDEX", 1)[0]

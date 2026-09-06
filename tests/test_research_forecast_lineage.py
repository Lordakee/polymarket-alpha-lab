from datetime import UTC, datetime
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.research_forecast_lineage_db_row import (
    ResearchForecastLineageRow,
)
from polymarket_alpha_lab.research_forecast_lineage_store import (
    ResearchForecastLineageStore,
    ResearchForecastLineageStoreError,
)


OBSERVED = datetime(2026, 9, 7, 12, tzinfo=UTC)
END = datetime(2026, 10, 1, tzinfo=UTC)
MIGRATION = Path("supabase/migrations/20260907000001_research_forecast_lineage.sql")
IDENTITY_MIGRATION = Path(
    "supabase/migrations/20260907000002_research_forecast_lineage_identity.sql"
)


def _row(**overrides):
    values = {
        "forecast_payload_sha256": "f" * 64,
        "forecast_id": "forecast-1",
        "condition_id": "0xabc",
        "team_id": "crypto_btc",
        "config_version": "p1-crypto_btc-v1",
        "event_id": "event-1",
        "event_slug": "event-one",
        "market_end_at": END,
        "event_lineage_state": "verified",
        "metadata_observed_at": OBSERVED,
        "metadata_payload_sha256": "a" * 64,
    }
    values.update(overrides)
    return ResearchForecastLineageRow(**values)


class Cursor:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []
        self.closed = False

    def execute(self, sql, params=()):
        self.calls.append((sql, params))

    def fetchone(self):
        return next(self.responses)

    def close(self):
        self.closed = True


class Connection:
    def __init__(self, responses):
        self.cursor_instance = Cursor(responses)
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def test_lineage_row_requires_complete_verified_or_empty_unknown_identity() -> None:
    assert _row().paper_only is True
    unknown = _row(
        event_id=None,
        event_slug=None,
        market_end_at=None,
        event_lineage_state="missing_event",
    )
    assert unknown.event_id is None
    with pytest.raises(ValueError, match="unknown event lineage"):
        _row(event_lineage_state="malformed_event")
    with pytest.raises(ValueError, match="paper-only"):
        _row(paper_only=False)


def test_store_inserts_and_exact_replay_is_idempotent() -> None:
    row = _row()
    inserted_connection = Connection([("f" * 64,)])
    inserted = ResearchForecastLineageStore(inserted_connection).insert(row)
    assert inserted.status == "inserted"
    assert inserted_connection.cursor_instance.closed

    replay_connection = Connection([None, row.as_parameters()])
    replayed = ResearchForecastLineageStore(replay_connection).insert(row)
    assert replayed.status == "already_present"
    assert "ON CONFLICT (forecast_payload_sha256) DO NOTHING" in replay_connection.cursor_instance.calls[0][0]


def test_store_refuses_forecast_identity_collision() -> None:
    row = _row()
    conflicting = list(row.as_parameters())
    conflicting[1] = "0xdifferent"
    connection = Connection([None, tuple(conflicting)])
    with pytest.raises(ResearchForecastLineageStoreError) as error:
        ResearchForecastLineageStore(connection).insert(row)
    assert error.value.code == "identity_collision"
    assert connection.cursor_instance.closed


def test_psycopg_adapter_commits_successful_insert(monkeypatch) -> None:
    from polymarket_alpha_lab import research_forecast_lineage_psycopg as adapter

    connection = Connection([("f" * 64,)])
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=lambda _dsn: connection))
    result = adapter.insert_research_forecast_lineage_with_psycopg(
        "postgresql://postgres@127.0.0.1:5432/postgres", _row()
    )
    assert result.status == "inserted"
    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.closed


def test_psycopg_adapter_rolls_back_identity_collision(monkeypatch) -> None:
    from polymarket_alpha_lab import research_forecast_lineage_psycopg as adapter

    row = _row()
    conflicting = list(row.as_parameters())
    conflicting[1] = "0xdifferent"
    connection = Connection([None, tuple(conflicting)])
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=lambda _dsn: connection))
    with pytest.raises(ResearchForecastLineageStoreError):
        adapter.insert_research_forecast_lineage_with_psycopg(
            "postgresql://postgres@127.0.0.1:5432/postgres", row
        )
    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.closed


def test_psycopg_adapter_rejects_remote_dsn_before_driver_import() -> None:
    from polymarket_alpha_lab.research_forecast_lineage_psycopg import (
        insert_research_forecast_lineage_with_psycopg,
    )

    with pytest.raises(ValueError, match="local postgres DSN"):
        insert_research_forecast_lineage_with_psycopg(
            "postgresql://postgres@remote.example/postgres", _row()
        )


def test_single_cycle_reports_recoverable_lineage_partial_failure(monkeypatch, capsys) -> None:
    from polymarket_alpha_lab import crypto_research_cycle_cli as cli

    execution = cli._CycleExecution(
        result=SimpleNamespace(status="ready", operator_packet="ready"),
        bundle=object(),
        outcomes=(),
        lineage_persistence_status="partial_failure",
        lineage_failure_code="identity_collision",
    )
    monkeypatch.setattr(cli, "_team_wiring", lambda _team: {})
    monkeypatch.setattr(cli, "_resolve_persistence", lambda: (object(), SimpleNamespace(enabled=True, dsn="local"), SimpleNamespace()))
    monkeypatch.setattr(cli, "_execute_crypto_cycle", lambda *_args, **_kwargs: execution)
    monkeypatch.setattr(
        "polymarket_alpha_lab.btc_cycle_diagnostics.format_btc_cycle_diagnostics",
        lambda *_args: "diagnostics",
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.central_data_registry.build_default_source_registry",
        lambda: object(),
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.central_data_registry.default_allowed_hosts",
        lambda: (),
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.central_data_transport.SafeGETTransport",
        lambda **_kwargs: object(),
    )

    assert cli.run_crypto_research_cycle_command(team="crypto_btc", market="market") == 1
    error = capsys.readouterr().err
    assert "forecast persisted" in error
    assert "recoverable by rerun" in error
    assert "identity_collision" in error


def test_lineage_migration_is_restricted_and_pins_hard_flags() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "current_user <> 'postgres'" in sql
    assert "current_database() <> 'postgres'" in sql
    assert "forecast_payload_sha256 text PRIMARY KEY" in sql
    assert "forecast_id text NOT NULL" in sql
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "event_lineage_state = 'verified'" in sql
    for flag in ("paper_only", "report_only", "readonly"):
        assert f"CHECK ({flag} IS true)" in sql
    for role in ("PUBLIC", "anon", "authenticated", "service_role"):
        assert (
            "REVOKE ALL ON TABLE research_settlement.research_forecast_lineage "
            f"FROM {role}"
        ) in sql


def test_lineage_identity_correction_refuses_unaudited_backfill() -> None:
    sql = IDENTITY_MIGRATION.read_text(encoding="utf-8")
    assert "current_user <> 'postgres'" in sql
    assert "current_database() <> 'postgres'" in sql
    assert "ADD COLUMN IF NOT EXISTS forecast_payload_sha256 text" in sql
    assert "existing lineage rows require audited forecast snapshot binding" in sql
    assert "PRIMARY KEY (forecast_payload_sha256)" in sql
    assert "idx_research_forecast_lineage_forecast_id" in sql
    assert "DELETE FROM" not in sql.upper()
    assert "DROP TABLE" not in sql.upper()

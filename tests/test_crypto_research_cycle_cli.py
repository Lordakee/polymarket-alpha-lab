from datetime import UTC, datetime
from types import SimpleNamespace
import json
import sys

from polymarket_alpha_lab.central_data_contracts import FailureStatus
from polymarket_alpha_lab.central_data_db_row import TypedEnvelope
from polymarket_alpha_lab.crypto_research_cycle_cli import (
    _DiscardingCentralStore,
    _derive_outcome_for_condition,
    run_collect_research_cycles_command,
    run_export_settlement_samples_command,
    run_import_settled_outcomes_command,
)


RETRIEVED_AT = datetime(2026, 9, 7, 12, tzinfo=UTC)
LOCAL_DSN = "postgresql://postgres@127.0.0.1:5432/postgres"


def _outcome_row(*, closed=True, outcomes=None, tokens=None, prices=None):
    value = {
        "condition_id": "0xabc",
        "closed": closed,
        "outcomes": outcomes if outcomes is not None else ["No", "Yes"],
        "clob_token_ids": tokens if tokens is not None else ["no-token", "yes-token"],
        "outcome_prices": prices if prices is not None else ["0", "1"],
    }
    return SimpleNamespace(
        typed_value=TypedEnvelope.encode(value),
        retrieval_time=RETRIEVED_AT,
        raw_payload_sha256="a" * 64,
    )


def _install_acquisition(monkeypatch, row):
    outcome = SimpleNamespace(
        failure_status=FailureStatus.NONE,
        normalized_rows=(row,),
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.central_data_acquisition.acquire_once",
        lambda *_args, **_kwargs: outcome,
    )


def test_outcome_derivation_uses_yes_label_and_retrieval_time(monkeypatch) -> None:
    _install_acquisition(monkeypatch, _outcome_row())
    registry = SimpleNamespace(get=lambda _source_id: object())

    result = _derive_outcome_for_condition(
        "0xabc", registry=registry, transport=object(), store=object()
    )

    assert result == (RETRIEVED_AT, "yes", "a" * 64, ["0", "1"])


def test_outcome_derivation_refuses_open_ambiguous_and_missing_yes(monkeypatch) -> None:
    registry = SimpleNamespace(get=lambda _source_id: object())
    cases = (
        _outcome_row(closed=False),
        _outcome_row(prices=["0.5", "0.5"]),
        _outcome_row(outcomes=["Up", "Down"]),
        _outcome_row(tokens=["no-token"]),
    )
    for row in cases:
        _install_acquisition(monkeypatch, row)
        assert _derive_outcome_for_condition(
            "0xabc", registry=registry, transport=object(), store=object()
        ) is None


def test_outcome_derivation_refuses_identity_mismatch(monkeypatch) -> None:
    row = _outcome_row()
    mismatched = SimpleNamespace(
        typed_value=TypedEnvelope.encode(
            {
                "condition_id": "0xother",
                "closed": True,
                "outcomes": ["No", "Yes"],
                "clob_token_ids": ["no-token", "yes-token"],
                "outcome_prices": ["0", "1"],
            }
        ),
        retrieval_time=row.retrieval_time,
        raw_payload_sha256=row.raw_payload_sha256,
    )
    _install_acquisition(monkeypatch, mismatched)
    registry = SimpleNamespace(get=lambda _source_id: object())

    assert _derive_outcome_for_condition(
        "0xabc", registry=registry, transport=object(), store=object()
    ) is None


def test_collection_validates_page_bounds_before_io(capsys) -> None:
    assert run_collect_research_cycles_command(
        team="crypto_btc", limit=101, offset=0
    ) == 2
    assert run_collect_research_cycles_command(
        team="crypto_eth", limit=10, offset=-1
    ) == 2
    assert "--limit must be between 1 and 100" in capsys.readouterr().err


def test_import_and_export_require_both_persistence_gates(monkeypatch, capsys) -> None:
    disabled = SimpleNamespace(enabled=False, dsn=None)
    monkeypatch.setattr(
        "polymarket_alpha_lab.crypto_research_cycle_cli._resolve_persistence",
        lambda: (_DiscardingCentralStore(), disabled, disabled),
    )

    assert run_import_settled_outcomes_command() == 2
    assert run_export_settlement_samples_command(
        cutoff="2026-10-01T00:00:00+00:00", out_path="unused.json"
    ) == 2
    errors = capsys.readouterr().err
    assert "team-forecast persistence is disabled" in errors


def test_import_adapts_snapshot_as_jsonb_and_reports_conflicts(monkeypatch, capsys) -> None:
    class Jsonb:
        def __init__(self, value):
            self.value = value

    class Cursor:
        def __init__(self):
            self.rowcount = 0
            self.params = None

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, _sql, params):
            self.params = params

    class Connection:
        def __init__(self):
            self.cursor_instance = Cursor()
            self.committed = False
            self.closed = False

        def cursor(self):
            return self.cursor_instance

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

    connection = Connection()
    psycopg = SimpleNamespace(connect=lambda _dsn: connection)
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.types", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "psycopg.types.json", SimpleNamespace(Jsonb=Jsonb))

    central = SimpleNamespace(enabled=True, dsn=LOCAL_DSN)
    forecast = SimpleNamespace(
        enabled=True,
        dsn=LOCAL_DSN,
        team_forecast_table_name="team_forecasts",
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.crypto_research_cycle_cli._resolve_persistence",
        lambda: (object(), central, forecast),
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.crypto_research_cycle_cli._derive_outcome_for_condition",
        lambda *_args, **_kwargs: (RETRIEVED_AT, "yes", "a" * 64, ["0", "1"]),
    )

    assert run_import_settled_outcomes_command(condition_ids=("0xabc",)) == 0
    assert isinstance(connection.cursor_instance.params[4], Jsonb)
    assert connection.cursor_instance.params[4].value == ["0", "1"]
    assert connection.committed and connection.closed
    output = capsys.readouterr().out
    assert "status=already_present" in output
    assert "summary imported=0 refused=0" in output


def test_export_accounts_for_invalid_db_rows(monkeypatch, tmp_path) -> None:
    valid_payload = {"market_implied_probability_observed": "0.4"}
    forecast_records = [
        (
            "forecast-1",
            "0xabc",
            "crypto_btc",
            "p1-crypto_btc-v1",
            "0.6",
            RETRIEVED_AT,
            valid_payload,
        ),
        (
            "forecast-invalid",
            "0xdef",
            "crypto_btc",
            "p1-crypto_btc-v1",
            "0.6",
            RETRIEVED_AT,
            {},
        ),
    ]

    class Cursor:
        def __init__(self, rows):
            self.rows = rows

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, _sql):
            return None

        def fetchall(self):
            return self.rows

    class Connection:
        def __init__(self, rows):
            self.rows = rows

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def cursor(self):
            return Cursor(self.rows)

    connections = iter((Connection(forecast_records), Connection([])))
    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda _dsn: next(connections)),
    )
    central = SimpleNamespace(enabled=True, dsn="central")
    forecast = SimpleNamespace(
        enabled=True,
        dsn="forecast",
        team_forecast_table_name="team_forecasts",
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.crypto_research_cycle_cli._resolve_persistence",
        lambda: (object(), central, forecast),
    )

    output = tmp_path / "samples.json"
    assert run_export_settlement_samples_command(
        cutoff="2026-10-01T00:00:00+00:00", out_path=str(output)
    ) == 0
    manifest = json.loads((tmp_path / "samples.json.manifest.json").read_text())
    assert manifest["input_forecast_rows"] == 2
    assert manifest["exclusion_reasons"] == {"invalid_forecast_row": 1}
    assert manifest["pending_count"] == 1

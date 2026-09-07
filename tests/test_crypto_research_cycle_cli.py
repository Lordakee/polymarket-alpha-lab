from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
import hashlib
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
from polymarket_alpha_lab.team_forecast_db_row import team_forecast_to_db_row
from polymarket_alpha_lab.team_forecast_packet import TeamForecastPacket


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
        cutoff="2026-10-01T00:00:00+00:00",
        outcome_cutoff="2026-10-02T00:00:00+00:00",
        checkpoint_path="unused.json",
        out_path="unused.json",
    ) == 2
    errors = capsys.readouterr().err
    assert "team-forecast persistence is disabled" in errors


def test_import_adapts_snapshot_as_jsonb_and_reports_conflicts(monkeypatch, capsys) -> None:
    class Jsonb:
        def __init__(self, value):
            self.value = value

    class Cursor:
        def __init__(self, existing):
            self.rowcount = 0
            self.insert_params = None
            self.existing = existing

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, sql, params):
            if sql.startswith("INSERT"):
                self.insert_params = params

        def fetchone(self):
            return self.existing

    class Connection:
        def __init__(self, existing):
            self.cursor_instance = Cursor(existing)
            self.committed = False
            self.closed = False

        def cursor(self):
            return self.cursor_instance

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

    connection = Connection(("yes", "polymarket_gamma", ["0", "1"], "a" * 64, False))
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
    assert isinstance(connection.cursor_instance.insert_params[4], Jsonb)
    assert connection.cursor_instance.insert_params[4].value == ["0", "1"]
    assert connection.committed and connection.closed
    output = capsys.readouterr().out
    assert "status=already_present" in output
    assert "summary imported=0 refused=0" in output


def test_import_refuses_same_identity_with_different_outcome(monkeypatch, capsys) -> None:
    class Jsonb:
        def __init__(self, value):
            self.value = value

    class Cursor:
        rowcount = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, _sql, _params):
            return None

        def fetchone(self):
            return ("no", "polymarket_gamma", ["1", "0"], "b" * 64, False)

    class Connection:
        def __init__(self):
            self.committed = False
            self.closed = False

        def cursor(self):
            return Cursor()

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

    connection = Connection()
    monkeypatch.setitem(
        sys.modules, "psycopg", SimpleNamespace(connect=lambda _dsn: connection)
    )
    monkeypatch.setitem(sys.modules, "psycopg.types", SimpleNamespace())
    monkeypatch.setitem(
        sys.modules, "psycopg.types.json", SimpleNamespace(Jsonb=Jsonb)
    )
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

    assert run_import_settled_outcomes_command(condition_ids=("0xabc",)) == 1
    assert connection.committed and connection.closed
    output = capsys.readouterr().out
    assert "status=refused reason=identity_collision" in output
    assert "summary imported=0 refused=1" in output


EXPORT_CUTOFF = "2026-09-08T00:00:00+00:00"
EXPORT_HORIZON = "2026-10-07T00:00:00+00:00"
MARKET_END_AT = datetime(2026, 9, 9, tzinfo=UTC)


def _forecast_packet(forecast_id: str, team_id: str, condition_id: str) -> TeamForecastPacket:
    category_id = {
        "crypto_btc": "finance.crypto.btc",
        "crypto_eth": "finance.crypto.eth",
    }[team_id]
    return TeamForecastPacket(
        forecast_id=forecast_id,
        team_id=team_id,
        condition_id=condition_id,
        market_slug=f"market-{forecast_id}",
        question=f"Question for {forecast_id}?",
        category_id=category_id,
        event_template="crypto_price_threshold",
        selected_side="yes",
        forecast_probability=Decimal("0.620000"),
        confidence=Decimal("0.710000"),
        evidence_quality=Decimal("0.800000"),
        data_freshness_score=Decimal("0.900000"),
        resolution_risk=Decimal("0.100000"),
        base_rate=Decimal("0.540000"),
        market_implied_probability_observed=Decimal("0.570000"),
        reason_codes=(f"team_{team_id}",),
        memory_references=(),
        source_references=(),
        known_failure_modes=(),
        config_version=f"p1-{team_id}-v1",
        prompt_version="crypto-team-prompt-v1",
        generated_at=RETRIEVED_AT,
    )


def _forecast_db_record(packet: TeamForecastPacket) -> tuple:
    row = team_forecast_to_db_row(packet)
    return (
        row.payload_sha256,
        row.generated_at,
        row.forecast_id,
        row.condition_id,
        row.team_id,
        row.market_slug,
        row.config_version,
        row.selected_side,
        row.forecast_probability,
        row.confidence,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _write_strict_checkpoint(tmp_path, packets, *, event_ids) -> tuple:
    lead_seconds = int((MARKET_END_AT - RETRIEVED_AT).total_seconds())
    records = [
        {
            "forecast_id": packet.forecast_id,
            "forecast_payload_sha256": team_forecast_to_db_row(packet).payload_sha256,
            "condition_id": packet.condition_id,
            "team_id": packet.team_id,
            "config_version": packet.config_version,
            "event_id": event_id,
            "event_slug": f"event-{event_id}" if event_id is not None else None,
            "generated_at": packet.generated_at.isoformat(),
            "market_end_at": MARKET_END_AT.isoformat(),
            "lead_seconds": lead_seconds,
            "metadata_observed_at": packet.generated_at.isoformat(),
            "metadata_payload_sha256": "f" * 64,
        }
        for packet, event_id in zip(packets, event_ids)
    ]
    inventory = tmp_path / "inventory-test.json"
    collection = tmp_path / "collection-test.json"
    inventory.write_bytes(b"inventory")
    collection.write_bytes(b"collection")
    document = {
        "schema_version": "p2-settlement-checkpoint-v1",
        "cohort_id": "p2-test-cohort",
        "hypothesis_label": "zero_impact_market_control",
        "independent_hypothesis_status": "not_implemented",
        "teams": [
            {"team_id": "crypto_btc", "config_version": "p1-crypto_btc-v1", "tag_id": "235"},
            {"team_id": "crypto_eth", "config_version": "p1-crypto_eth-v1", "tag_id": "39"},
        ],
        "gamma_query": {"closed": False, "limit": 100, "offset": 0},
        "market_selector": {
            "active": True,
            "binary": True,
            "closed": False,
            "team_keyword_required": True,
        },
        "forecast_selection_rule": (
            "earliest eligible forecast per (condition_id, team_id, config_version) "
            "generated before the forecast cutoff"
        ),
        "minimum_lead_seconds": 1800,
        "cohort_horizon": EXPORT_HORIZON,
        "as_of_evaluation_cutoff": EXPORT_CUTOFF,
        "selected_forecast_ids": [record["forecast_id"] for record in records],
        "selected_forecast_payload_sha256": [
            record["forecast_payload_sha256"] for record in records
        ],
        "selected_forecast_event_ids": [record["event_id"] for record in records],
        "selected_event_ids": sorted(
            {record["event_id"] for record in records if record["event_id"] is not None}
        ),
        "unknown_event_lineage_count": sum(
            record["event_id"] is None for record in records
        ),
        "selected_cohorts": sorted(
            {f"{record['team_id']}:{record['config_version']}" for record in records}
        ),
        "selected_forecasts": records,
        "inventory_artifact": inventory.name,
        "inventory_sha256": hashlib.sha256(b"inventory").hexdigest(),
        "collection_artifact": collection.name,
        "collection_sha256": hashlib.sha256(b"collection").hexdigest(),
        "generated_at": EXPORT_CUTOFF,
        "reassessment_at": EXPORT_HORIZON,
        "outcome_refresh": "not_performed",
        "flags": {"paper_only": True, "report_only": True, "readonly": True},
    }
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
    return checkpoint, document


class _ExportCursor:
    def __init__(self, row_sets):
        self.row_sets = iter(row_sets)
        self.rows = []
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        self.rows = next(self.row_sets)

    def fetchall(self):
        return self.rows


class _ExportConnection:
    def __init__(self, row_sets):
        self.row_sets = row_sets
        self._cursor = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def cursor(self):
        if self._cursor is None:
            self._cursor = _ExportCursor(self.row_sets)
        return self._cursor


def _install_export_psycopg(monkeypatch, connections):
    connections = iter(connections)
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
    return forecast


def test_export_checkpoint_rejects_minimal_fabricated_document(tmp_path, monkeypatch, capsys) -> None:
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "as_of_evaluation_cutoff": EXPORT_CUTOFF,
                "selected_forecast_ids": ["forecast-1"],
                "selected_forecast_payload_sha256": ["a" * 64],
            }
        )
    )
    _install_export_psycopg(monkeypatch, ())

    output = tmp_path / "samples.json"
    assert run_export_settlement_samples_command(
        cutoff=EXPORT_CUTOFF,
        outcome_cutoff="2026-09-09T00:00:00+00:00",
        checkpoint_path=str(checkpoint),
        out_path=str(output),
    ) == 2
    assert "invalid checkpoint" in capsys.readouterr().err
    assert not output.exists()


def test_export_checkpoint_filters_unselected_forecasts(monkeypatch, tmp_path) -> None:
    selected = _forecast_packet("forecast-selected", "crypto_btc", "0xabc")
    unselected = _forecast_packet("forecast-unselected", "crypto_eth", "0xdef")
    selected_hash = team_forecast_to_db_row(selected).payload_sha256
    checkpoint, _document = _write_strict_checkpoint(
        tmp_path, (selected,), event_ids=("event-1",)
    )
    forecast_rows = [_forecast_db_record(selected), _forecast_db_record(unselected)]
    lineage_rows = [
        (selected_hash, "event-1", "verified"),
        (team_forecast_to_db_row(unselected).payload_sha256, "event-2", "verified"),
    ]
    outcome_rows = [("0xabc", "yes", RETRIEVED_AT, False, "c" * 64)]
    _install_export_psycopg(
        monkeypatch,
        (
            _ExportConnection([forecast_rows]),
            _ExportConnection([lineage_rows, outcome_rows]),
        ),
    )

    output = tmp_path / "samples.json"
    assert run_export_settlement_samples_command(
        cutoff=EXPORT_CUTOFF,
        outcome_cutoff="2026-09-09T00:00:00+00:00",
        checkpoint_path=str(checkpoint),
        out_path=str(output),
    ) == 0
    manifest = json.loads((tmp_path / "samples.json.manifest.json").read_text())
    assert manifest["selected_forecast_ids"] == [selected.forecast_id]
    assert manifest["selected_forecast_payload_sha256"] == [selected_hash]
    assert manifest["selected_event_ids"] == ["event-1"]
    assert manifest["input_forecast_rows"] == 1
    assert manifest["input_outcome_rows"] == 1
    assert manifest["included_count"] == 1
    assert manifest["pending_count"] == 0


def test_export_checkpoint_fails_closed_on_missing_readback(monkeypatch, tmp_path, capsys) -> None:
    selected = _forecast_packet("forecast-missing", "crypto_btc", "0xabc")
    checkpoint, _document = _write_strict_checkpoint(
        tmp_path, (selected,), event_ids=("event-1",)
    )
    _install_export_psycopg(monkeypatch, (_ExportConnection([[]]),))

    output = tmp_path / "samples.json"
    assert run_export_settlement_samples_command(
        cutoff=EXPORT_CUTOFF,
        outcome_cutoff="2026-09-09T00:00:00+00:00",
        checkpoint_path=str(checkpoint),
        out_path=str(output),
    ) == 2
    assert "checkpoint forecast readback mismatch" in capsys.readouterr().err
    assert not output.exists()


def test_export_checkpoint_fails_closed_on_payload_tamper(monkeypatch, tmp_path, capsys) -> None:
    selected = _forecast_packet("forecast-tampered", "crypto_btc", "0xabc")
    checkpoint, _document = _write_strict_checkpoint(
        tmp_path, (selected,), event_ids=("event-1",)
    )
    tampered = list(_forecast_db_record(selected))
    tampered[10] = {
        **tampered[10],
        "market_implied_probability_observed": "0.111111",
    }
    _install_export_psycopg(monkeypatch, (_ExportConnection([[tuple(tampered)]]),))

    output = tmp_path / "samples.json"
    assert run_export_settlement_samples_command(
        cutoff=EXPORT_CUTOFF,
        outcome_cutoff="2026-09-09T00:00:00+00:00",
        checkpoint_path=str(checkpoint),
        out_path=str(output),
    ) == 2
    assert "checkpoint forecast readback mismatch" in capsys.readouterr().err
    assert not output.exists()


def test_export_checkpoint_fails_closed_on_lineage_mismatch(monkeypatch, tmp_path, capsys) -> None:
    selected = _forecast_packet("forecast-lineage", "crypto_btc", "0xabc")
    selected_hash = team_forecast_to_db_row(selected).payload_sha256
    checkpoint, _document = _write_strict_checkpoint(
        tmp_path, (selected,), event_ids=("event-1",)
    )
    _install_export_psycopg(
        monkeypatch,
        (
            _ExportConnection([[_forecast_db_record(selected)]]),
            _ExportConnection([[(selected_hash, "event-other", "verified")], []]),
        ),
    )

    output = tmp_path / "samples.json"
    assert run_export_settlement_samples_command(
        cutoff=EXPORT_CUTOFF,
        outcome_cutoff="2026-09-09T00:00:00+00:00",
        checkpoint_path=str(checkpoint),
        out_path=str(output),
    ) == 2
    assert "checkpoint lineage mismatch" in capsys.readouterr().err
    assert not output.exists()


def test_export_scopes_outcomes_to_cohort_and_counts_invalid_rows(monkeypatch, tmp_path) -> None:
    selected = _forecast_packet("forecast-selected", "crypto_btc", "0xabc")
    selected_hash = team_forecast_to_db_row(selected).payload_sha256
    checkpoint, _document = _write_strict_checkpoint(
        tmp_path, (selected,), event_ids=("event-1",)
    )
    lineage_rows = [(selected_hash, "event-1", "verified")]
    outcome_rows = [
        ("0xabc", "yes", RETRIEVED_AT, False, "c" * 64),
        ("0xabc", "maybe", RETRIEVED_AT, False, "d" * 64),
    ]
    outcome_connection = _ExportConnection([lineage_rows, outcome_rows])
    _install_export_psycopg(
        monkeypatch,
        (
            _ExportConnection([[_forecast_db_record(selected)]]),
            outcome_connection,
        ),
    )

    output = tmp_path / "samples.json"
    assert run_export_settlement_samples_command(
        cutoff=EXPORT_CUTOFF,
        outcome_cutoff="2026-09-09T00:00:00+00:00",
        checkpoint_path=str(checkpoint),
        out_path=str(output),
    ) == 0
    cursor = outcome_connection._cursor
    outcome_calls = [call for call in cursor.calls if "research_settled_outcomes" in call[0]]
    assert len(outcome_calls) == 1
    sql, params = outcome_calls[0]
    assert "WHERE condition_id = ANY(%s)" in sql
    assert params == (["0xabc"],)
    manifest = json.loads((tmp_path / "samples.json.manifest.json").read_text())
    assert manifest["input_outcome_rows"] == 2
    assert manifest["exclusion_reasons"] == {"invalid_outcome_row": 1}
    assert manifest["included_count"] == 1
    assert manifest["pending_count"] == 0


def test_export_counts_malformed_outcome_shapes_without_aborting(monkeypatch, tmp_path) -> None:
    selected = _forecast_packet("forecast-shapes", "crypto_btc", "0xabc")
    selected_hash = team_forecast_to_db_row(selected).payload_sha256
    checkpoint, _document = _write_strict_checkpoint(
        tmp_path, (selected,), event_ids=("event-1",)
    )
    lineage_rows = [(selected_hash, "event-1", "verified")]
    outcome_rows = [
        ("0xabc",),
        ("0xabc", "yes", "not-a-timestamp", False, "c" * 64),
    ]
    _install_export_psycopg(
        monkeypatch,
        (
            _ExportConnection([[_forecast_db_record(selected)]]),
            _ExportConnection([lineage_rows, outcome_rows]),
        ),
    )

    output = tmp_path / "samples.json"
    assert run_export_settlement_samples_command(
        cutoff=EXPORT_CUTOFF,
        outcome_cutoff="2026-09-09T00:00:00+00:00",
        checkpoint_path=str(checkpoint),
        out_path=str(output),
    ) == 0
    manifest = json.loads((tmp_path / "samples.json.manifest.json").read_text())
    assert manifest["input_outcome_rows"] == 2
    assert manifest["exclusion_reasons"] == {"invalid_outcome_row": 2}
    assert manifest["included_count"] == 0
    assert manifest["pending_count"] == 1

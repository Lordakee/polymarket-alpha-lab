from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import sys
import types
from typing import Any

import pytest


STORE_MODULE_NAME = "polymarket_alpha_lab.team_diagnostics_snapshot_store"
DB_ROW_MODULE_NAME = "polymarket_alpha_lab.team_diagnostics_snapshot_db_row"
DEFAULT_TABLE = "team_diagnostics_snapshots"
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_config_version",
    "team_id",
    "market_slug",
    "forecast_id",
    "forecast_row_count",
    "evidence_row_count",
    "outcome_row_count",
    "memory_eligible_reference_count",
    "calibration_status",
    "calibration_settled_count",
    "calibration_group_count",
    "event_template_row_count",
    "event_template_status",
    "source_reliability_row_count",
    "source_reliability_missing_source_evidence_count",
    "evidence_quality_status",
    "evidence_quality_pass_count",
    "evidence_quality_watch_count",
    "evidence_quality_blocked_count",
    "evidence_quality_average_quality_score",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class FakeReport:
    team_id: str | None
    market_slug: str | None
    forecast_id: str | None


@dataclass(frozen=True)
class FakeDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_config_version: str
    team_id: str | None
    market_slug: str | None
    forecast_id: str | None
    forecast_row_count: int
    evidence_row_count: int
    outcome_row_count: int
    memory_eligible_reference_count: int
    calibration_status: str
    calibration_settled_count: int
    calibration_group_count: int
    event_template_row_count: int
    event_template_status: str
    source_reliability_row_count: int
    source_reliability_missing_source_evidence_count: int
    evidence_quality_status: str
    evidence_quality_pass_count: int
    evidence_quality_watch_count: int
    evidence_quality_blocked_count: int
    evidence_quality_average_quality_score: Decimal
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        rowcount: int = 1,
        *,
        execute_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.rows = rows
        self.rowcount = rowcount
        self.execute_error = execute_error
        self.close_error = close_error
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
        return self.rows

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        rowcount: int = 1,
        *,
        cursor: FakeCursor | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(rows, rowcount) if cursor is None else cursor
        self.cursor_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def _row(**overrides: Any) -> FakeDbRow:
    generated_at = datetime(2026, 7, 1, 16, 30, tzinfo=UTC)
    values: dict[str, Any] = {
        "report_sha256": "a" * 64,
        "generated_at": generated_at,
        "config_version": "team-diagnostics-snapshot-test-v0",
        "source_config_version": "team-diagnostics-bundle-v0",
        "team_id": "crypto_btc",
        "market_slug": "bitcoin-above-120k",
        "forecast_id": "forecast-btc-1",
        "forecast_row_count": 2,
        "evidence_row_count": 5,
        "outcome_row_count": 1,
        "memory_eligible_reference_count": 1,
        "calibration_status": "calibration_watch",
        "calibration_settled_count": 3,
        "calibration_group_count": 2,
        "event_template_row_count": 4,
        "event_template_status": "event_template_pass",
        "source_reliability_row_count": 6,
        "source_reliability_missing_source_evidence_count": 1,
        "evidence_quality_status": "evidence_quality_watch",
        "evidence_quality_pass_count": 3,
        "evidence_quality_watch_count": 2,
        "evidence_quality_blocked_count": 0,
        "evidence_quality_average_quality_score": Decimal("0.740000"),
        "reason_codes_json": ["calibration_watch", "evidence_quality_watch"],
        "payload_json": {
            "generated_at": generated_at.isoformat(),
            "config_version": "team-diagnostics-snapshot-test-v0",
            "source_config_version": "team-diagnostics-bundle-v0",
            "filters": [
                ["team_id", "crypto_btc"],
                ["market_slug", "bitcoin-above-120k"],
                ["forecast_id", "forecast-btc-1"],
            ],
            "forecast_row_count": 2,
            "evidence_row_count": 5,
            "outcome_row_count": 1,
            "memory_eligible_reference_count": 1,
            "calibration_status": "calibration_watch",
            "calibration_settled_count": 3,
            "calibration_group_count": 2,
            "event_template_row_count": 4,
            "event_template_status": "event_template_pass",
            "source_reliability_row_count": 6,
            "source_reliability_missing_source_evidence_count": 1,
            "evidence_quality_status": "evidence_quality_watch",
            "evidence_quality_pass_count": 3,
            "evidence_quality_watch_count": 2,
            "evidence_quality_blocked_count": 0,
            "evidence_quality_average_quality_score": "0.740000",
            "reason_codes": ["calibration_watch", "evidence_quality_watch"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return FakeDbRow(**values)


def _row_values(row: FakeDbRow) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def _install_fake_db_row(
    monkeypatch: pytest.MonkeyPatch,
    *,
    row: FakeDbRow | None = None,
    report: FakeReport | None = None,
) -> None:
    module = types.ModuleType(DB_ROW_MODULE_NAME)
    expected_row = _row() if row is None else row
    expected_report = (
        FakeReport(
            team_id=expected_row.team_id,
            market_slug=expected_row.market_slug,
            forecast_id=expected_row.forecast_id,
        )
        if report is None
        else report
    )
    module.TeamDiagnosticsSnapshotDbRow = FakeDbRow
    module.team_diagnostics_snapshot_report_to_db_row = lambda report_arg: expected_row
    module.team_diagnostics_snapshot_report_from_db_row = lambda row_arg: expected_report
    monkeypatch.setitem(sys.modules, DB_ROW_MODULE_NAME, module)


def _import_store(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    _install_fake_db_row(monkeypatch)
    sys.modules.pop(STORE_MODULE_NAME, None)
    return importlib.import_module(STORE_MODULE_NAME)


def test_insert_snapshot_report_uses_parameterized_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()
    report = FakeReport(
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        forecast_id="forecast-btc-1",
    )
    expected_row = _row()

    inserted = store.insert_team_diagnostics_snapshot_report(
        connection,
        report,
        table_name="research.team_diagnostics_snapshots",
    )

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO research.team_diagnostics_snapshots (
            report_sha256,
            generated_at,
            config_version,
            source_config_version,
            team_id,
            market_slug,
            forecast_id,
            forecast_row_count,
            evidence_row_count,
            outcome_row_count,
            memory_eligible_reference_count,
            calibration_status,
            calibration_settled_count,
            calibration_group_count,
            event_template_row_count,
            event_template_status,
            source_reliability_row_count,
            source_reliability_missing_source_evidence_count,
            evidence_quality_status,
            evidence_quality_pass_count,
            evidence_quality_watch_count,
            evidence_quality_blocked_count,
            evidence_quality_average_quality_score,
            reason_codes_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)
    assert "team-diagnostics-snapshot-test-v0" not in sql
    assert "bitcoin-above-120k" not in sql


def test_insert_snapshot_report_with_result_observes_conflict_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _import_store(monkeypatch)
    report = FakeReport(
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        forecast_id="forecast-btc-1",
    )
    expected_row = _row()

    inserted = store.insert_team_diagnostics_snapshot_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store.insert_team_diagnostics_snapshot_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_load_snapshot_reports_filters_limits_orders_and_maps_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _row()
    report = FakeReport(
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        forecast_id="forecast-btc-1",
    )
    _install_fake_db_row(monkeypatch, row=row, report=report)
    sys.modules.pop(STORE_MODULE_NAME, None)
    store = importlib.import_module(STORE_MODULE_NAME)
    connection = FakeConnection(rows=(dict(zip(SELECT_COLUMNS, _row_values(row), strict=True)),))

    reports = store.load_team_diagnostics_snapshot_reports(
        connection,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        forecast_id="forecast-btc-1",
        config_version="team-diagnostics-snapshot-test-v0",
        limit=25,
        table_name="research.team_diagnostics_snapshots",
    )

    assert reports == (report,)
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            source_config_version,
            team_id,
            market_slug,
            forecast_id,
            forecast_row_count,
            evidence_row_count,
            outcome_row_count,
            memory_eligible_reference_count,
            calibration_status,
            calibration_settled_count,
            calibration_group_count,
            event_template_row_count,
            event_template_status,
            source_reliability_row_count,
            source_reliability_missing_source_evidence_count,
            evidence_quality_status,
            evidence_quality_pass_count,
            evidence_quality_watch_count,
            evidence_quality_blocked_count,
            evidence_quality_average_quality_score,
            reason_codes_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM research.team_diagnostics_snapshots
        WHERE team_id = %s AND market_slug = %s AND forecast_id = %s AND config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "crypto_btc",
        "bitcoin-above-120k",
        "forecast-btc-1",
        "team-diagnostics-snapshot-test-v0",
        25,
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
        ({"limit": "25"}, "limit"),
    ),
)
def test_load_rejects_invalid_limit_before_cursor_creation(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store.load_team_diagnostics_snapshot_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    "table_name",
    (
        "schema.too.many.parts",
        "TeamDiagnosticsSnapshots",
        "_team_diagnostics_snapshots",
        "team_diagnostics_snapshots_",
        "public." + ("a" * 64),
        "team_diagnostics_snapshots; drop table users",
    ),
)
def test_table_name_validation_rejects_unsafe_names_without_cursor_creation(
    monkeypatch: pytest.MonkeyPatch,
    table_name: str,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store.load_team_diagnostics_snapshot_reports(
            connection,
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []

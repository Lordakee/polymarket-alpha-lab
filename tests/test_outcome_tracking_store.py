from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeOutcomeTrackingReport:
    generated_at: datetime
    config_version: str
    total_markets_checked: int
    resolved_count: int
    pending_count: int


@dataclass(frozen=True)
class FakeOutcomeTrackingDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    total_markets_checked: int
    resolved_count: int
    pending_count: int
    observation_count: int
    forecast_evidence_status: str | None
    payload_json: dict[str, Any]
    paper_only: bool = True


class FakeCursor:
    def __init__(self, rows: tuple[Any, ...] = ()) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchall(self) -> tuple[Any, ...]:
        return self.rows

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, rows: tuple[Any, ...] = ()) -> None:
        self.cursor_instance = FakeCursor(rows)
        self.cursor_count = 0
        self.commit_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType("polymarket_alpha_lab.outcome_tracking_db_row")

    def to_db_row(report: FakeOutcomeTrackingReport) -> FakeOutcomeTrackingDbRow:
        return FakeOutcomeTrackingDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            total_markets_checked=report.total_markets_checked,
            resolved_count=report.resolved_count,
            pending_count=report.pending_count,
            observation_count=report.resolved_count,
            forecast_evidence_status="insufficient_evidence"
            if report.resolved_count
            else None,
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "total_markets_checked": report.total_markets_checked,
            },
        )

    def from_db_row(row: FakeOutcomeTrackingDbRow) -> FakeOutcomeTrackingReport:
        return FakeOutcomeTrackingReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            total_markets_checked=row.total_markets_checked,
            resolved_count=row.resolved_count,
            pending_count=row.pending_count,
        )

    companion.OutcomeTrackingReportDbRow = FakeOutcomeTrackingDbRow
    companion.outcome_tracking_report_to_db_row = to_db_row
    companion.outcome_tracking_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.outcome_tracking_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.outcome_tracking_store", None)
    return importlib.import_module("polymarket_alpha_lab.outcome_tracking_store")


def test_insert_outcome_tracking_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeOutcomeTrackingReport(
        generated_at=datetime(2026, 6, 19, 19, 30, tzinfo=UTC),
        config_version="outcome-tracker-db-v0",
        total_markets_checked=3,
        resolved_count=2,
        pending_count=1,
    )

    inserted = store_module.insert_outcome_tracking_report(connection, report)

    assert inserted == FakeOutcomeTrackingDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        total_markets_checked=3,
        resolved_count=2,
        pending_count=1,
        observation_count=2,
        forecast_evidence_status="insufficient_evidence",
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "total_markets_checked": 3,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO outcome_tracking_reports (
            report_sha256,
            generated_at,
            config_version,
            total_markets_checked,
            resolved_count,
            pending_count,
            observation_count,
            forecast_evidence_status,
            payload,
            paper_only
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        3,
        2,
        1,
        2,
        "insufficient_evidence",
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "total_markets_checked": 3,
        },
        True,
    )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_outcome_tracking_report(
            connection,
            FakeOutcomeTrackingReport(
                generated_at=datetime(2026, 6, 19, 19, 30, tzinfo=UTC),
                config_version="outcome-tracker-db-v0",
                total_markets_checked=0,
                resolved_count=0,
                pending_count=0,
            ),
            table_name="outcome_tracking_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_outcome_tracking_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = FakeOutcomeTrackingDbRow(
        report_sha256="b" * 64,
        generated_at=datetime(2026, 6, 19, 20, 0, tzinfo=UTC),
        config_version="outcome-tracker-db-v0",
        total_markets_checked=5,
        resolved_count=3,
        pending_count=2,
        observation_count=3,
        forecast_evidence_status="insufficient_evidence",
        payload_json={
            "generated_at": "2026-06-19T20:00:00+00:00",
            "config_version": "outcome-tracker-db-v0",
            "total_markets_checked": 5,
        },
    )
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_outcome_tracking_reports(
        connection,
        config_version="outcome-tracker-db-v0",
        limit=25,
        table_name="outcome_tracking_archive",
    )

    assert reports == (
        FakeOutcomeTrackingReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            total_markets_checked=5,
            resolved_count=3,
            pending_count=2,
        ),
    )
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            total_markets_checked,
            resolved_count,
            pending_count,
            observation_count,
            forecast_evidence_status,
            payload,
            paper_only
        FROM outcome_tracking_archive
        WHERE config_version = %s
        ORDER BY generated_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("outcome-tracker-db-v0", 25)


def test_load_outcome_tracking_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 19, 20, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "outcome-tracker-db-v0",
                2,
                1,
                1,
                1,
                "insufficient_evidence",
                {
                    "generated_at": "2026-06-19T20:00:00+00:00",
                    "config_version": "outcome-tracker-db-v0",
                    "total_markets_checked": 2,
                },
                True,
            ),
        ),
    )

    reports = store_module.load_outcome_tracking_reports(connection)

    assert reports == (
        FakeOutcomeTrackingReport(
            generated_at=generated_at,
            config_version="outcome-tracker-db-v0",
            total_markets_checked=2,
            resolved_count=1,
            pending_count=1,
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.outcome_tracking_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " outcome-tracker-db-v0"}, "config_version"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_without_executing_sql(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_module.load_outcome_tracking_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []

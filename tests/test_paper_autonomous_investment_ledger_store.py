from __future__ import annotations

import importlib
import sys
import types
from collections import namedtuple
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeLedgerReport:
    generated_at: datetime
    config_version: str
    ledger_status: str
    source_record_count: int


@dataclass(frozen=True)
class FakeLedgerDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    ledger_status: str
    recommended_next_step: str
    source_record_count: int
    submitted_count: int
    held_count: int
    blocked_count: int
    total_submitted_notional: Decimal
    held_zero_notional_count: int
    blocked_zero_notional_count: int
    latest_generated_at: datetime | None
    latest_age_seconds: int | None
    reason_code_counts_json: list[dict[str, Any]]
    entries_json: list[dict[str, Any]]
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(self, rows: tuple[Any, ...] = (), rowcount: int = 1) -> None:
        self.rows = rows
        self.rowcount = rowcount
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchall(self) -> tuple[Any, ...]:
        return self.rows

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, rows: tuple[Any, ...] = (), rowcount: int = 1) -> None:
        self.cursor_instance = FakeCursor(rows, rowcount)
        self.cursor_count = 0
        self.commit_count = 0
        self.rollback_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def d(value: str) -> Decimal:
    return Decimal(value)


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


DB_COLUMN_TO_ROW_ATTR = {
    "reason_code_counts": "reason_code_counts_json",
    "entries": "entries_json",
    "reason_codes": "reason_codes_json",
    "payload": "payload_json",
}


def fake_db_row(
    *,
    report_sha256: str = "a" * 64,
    generated_at: datetime = datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
    config_version: str = "paper-autonomous-investment-ledger-v0",
    ledger_status: str = "watch",
    source_record_count: int = 2,
) -> FakeLedgerDbRow:
    return FakeLedgerDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        ledger_status=ledger_status,
        recommended_next_step="review_paper_autonomous_investment_ledger",
        source_record_count=source_record_count,
        submitted_count=1,
        held_count=1,
        blocked_count=0,
        total_submitted_notional=d("12.500000"),
        held_zero_notional_count=1,
        blocked_zero_notional_count=0,
        latest_generated_at=datetime(2026, 6, 25, 11, 59, 30, tzinfo=UTC),
        latest_age_seconds=30,
        reason_code_counts_json=[
            {
                "reason_code": "paper_autonomous_investment_ledger_held_records_present",
                "source_record_count": 1,
            },
        ],
        entries_json=[
            {
                "entry_rank": 1,
                "execution_status": "paper_held",
            },
        ],
        reason_codes_json=[
            "paper_autonomous_investment_ledger_held_records_present",
        ],
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "ledger_status": ledger_status,
            "source_record_count": source_record_count,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_row",
    )

    def to_db_row(report: FakeLedgerReport) -> FakeLedgerDbRow:
        return fake_db_row(
            generated_at=report.generated_at,
            config_version=report.config_version,
            ledger_status=report.ledger_status,
            source_record_count=report.source_record_count,
        )

    def from_db_row(row: FakeLedgerDbRow) -> FakeLedgerReport:
        return FakeLedgerReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            ledger_status=row.ledger_status,
            source_record_count=row.source_record_count,
        )

    companion.PaperAutonomousInvestmentLedgerDbRow = FakeLedgerDbRow
    companion.paper_autonomous_investment_ledger_report_to_db_row = to_db_row
    companion.paper_autonomous_investment_ledger_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_store",
    )


def _fake_report() -> FakeLedgerReport:
    return FakeLedgerReport(
        generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
        config_version="paper-autonomous-investment-ledger-v0",
        ledger_status="watch",
        source_record_count=2,
    )


def test_insert_ledger_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rowcount=1)
    report = _fake_report()

    inserted = store_module.insert_paper_autonomous_investment_ledger_report(
        connection,
        report,
    )
    result = store_module.insert_paper_autonomous_investment_ledger_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )

    assert inserted == result.row
    assert result.inserted is True
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_autonomous_investment_ledger_reports (
            report_sha256,
            generated_at,
            config_version,
            ledger_status,
            recommended_next_step,
            source_record_count,
            submitted_count,
            held_count,
            blocked_count,
            total_submitted_notional,
            held_zero_notional_count,
            blocked_zero_notional_count,
            latest_generated_at,
            latest_age_seconds,
            reason_code_counts,
            entries,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        "paper-autonomous-investment-ledger-v0",
        "watch",
        "review_paper_autonomous_investment_ledger",
        2,
        1,
        1,
        0,
        d("12.500000"),
        1,
        0,
        datetime(2026, 6, 25, 11, 59, 30, tzinfo=UTC),
        30,
        [
            {
                "reason_code": "paper_autonomous_investment_ledger_held_records_present",
                "source_record_count": 1,
            },
        ],
        [
            {
                "entry_rank": 1,
                "execution_status": "paper_held",
            },
        ],
        [
            "paper_autonomous_investment_ledger_held_records_present",
        ],
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": "paper-autonomous-investment-ledger-v0",
            "ledger_status": "watch",
            "source_record_count": 2,
        },
        True,
        True,
        True,
    )


def test_insert_ledger_report_with_result_observes_duplicate_insert(
    store_module: types.ModuleType,
) -> None:
    report = _fake_report()
    expected_row = fake_db_row()

    inserted = store_module.insert_paper_autonomous_investment_ledger_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store_module.insert_paper_autonomous_investment_ledger_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_ledger_report_rejects_unexpected_rowcount(
    store_module: types.ModuleType,
) -> None:
    with pytest.raises(ValueError, match="rowcount"):
        store_module.insert_paper_autonomous_investment_ledger_report_with_result(
            FakeConnection(rowcount=2),
            _fake_report(),
        )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_autonomous_investment_ledger_report(
            connection,
            _fake_report(),
            table_name="paper_autonomous_investment_ledger_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_ledger_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(source_record_count=3)
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_autonomous_investment_ledger_reports(
        connection,
        config_version="paper-autonomous-investment-ledger-v0",
        ledger_status="watch",
        limit=25,
        table_name="paper_autonomous_investment_ledger_archive",
    )

    assert reports == (
        FakeLedgerReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            ledger_status=row.ledger_status,
            source_record_count=3,
        ),
    )
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            ledger_status,
            recommended_next_step,
            source_record_count,
            submitted_count,
            held_count,
            blocked_count,
            total_submitted_notional,
            held_zero_notional_count,
            blocked_zero_notional_count,
            latest_generated_at,
            latest_age_seconds,
            reason_code_counts,
            entries,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        FROM paper_autonomous_investment_ledger_archive
        WHERE config_version = %s AND ledger_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "paper-autonomous-investment-ledger-v0",
        "watch",
        25,
    )


def test_load_ledger_reports_accepts_positional_dict_and_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 25, 13, 0, tzinfo=UTC)
    row = fake_db_row(generated_at=generated_at, source_record_count=4)
    record_type = namedtuple(
        "LedgerRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "ledger_status",
            "recommended_next_step",
            "source_record_count",
            "submitted_count",
            "held_count",
            "blocked_count",
            "total_submitted_notional",
            "held_zero_notional_count",
            "blocked_zero_notional_count",
            "latest_generated_at",
            "latest_age_seconds",
            "reason_code_counts",
            "entries",
            "reason_codes",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    values = tuple(
        getattr(row, DB_COLUMN_TO_ROW_ATTR.get(field_name, field_name))
        for field_name in record_type._fields
    )
    connections = (
        FakeConnection(rows=(values,)),
        FakeConnection(rows=({field_name: value for field_name, value in zip(record_type._fields, values, strict=True)},)),
        FakeConnection(rows=(record_type(*values),)),
    )

    for connection in connections:
        assert store_module.load_paper_autonomous_investment_ledger_reports(
            connection,
        ) == (
            FakeLedgerReport(
                generated_at=generated_at,
                config_version="paper-autonomous-investment-ledger-v0",
                ledger_status="watch",
                source_record_count=4,
            ),
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_autonomous_investment_ledger_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"ledger_status": "live"}, "ledger_status"),
        ({"ledger_status": True}, "ledger_status"),
        ({"limit": 0}, "limit"),
        ({"limit": -1}, "limit"),
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
        store_module.load_paper_autonomous_investment_ledger_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_public_exports_include_default_table_insert_result_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_REPORTS_TABLE == (
        "paper_autonomous_investment_ledger_reports"
    )
    assert "DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_REPORTS_TABLE" in store_module.__all__
    assert "PaperAutonomousInvestmentLedgerInsertResult" in store_module.__all__
    assert "insert_paper_autonomous_investment_ledger_report" in store_module.__all__
    assert "insert_paper_autonomous_investment_ledger_report_with_result" in store_module.__all__
    assert "load_paper_autonomous_investment_ledger_reports" in store_module.__all__

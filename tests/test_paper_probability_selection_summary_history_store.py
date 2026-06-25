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
class FakeHistoryReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    latest_queue_count: int
    history_status: str


@dataclass(frozen=True)
class FakeHistoryDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_report_count: int
    latest_generated_at: datetime | None
    latest_age_seconds: int | None
    latest_queue_count: int
    latest_selected_count: int
    latest_selected_share: Decimal
    average_selected_share: Decimal
    history_status: str
    recommended_next_step: str
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


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def d(value: str) -> Decimal:
    return Decimal(value)


def fake_db_row(
    *,
    report_sha256: str = "b" * 64,
    generated_at: datetime = datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
    config_version: str = "paper-probability-selection-summary-history-v0",
    source_report_count: int = 3,
    latest_queue_count: int = 6,
    history_status: str = "watch",
) -> FakeHistoryDbRow:
    latest_generated_at = datetime(2026, 6, 22, 11, 45, tzinfo=UTC)
    return FakeHistoryDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        source_report_count=source_report_count,
        latest_generated_at=latest_generated_at,
        latest_age_seconds=900,
        latest_queue_count=latest_queue_count,
        latest_selected_count=4,
        latest_selected_share=d("0.666667"),
        average_selected_share=d("0.600000"),
        history_status=history_status,
        recommended_next_step="review_probability_selection",
        reason_codes_json=["latest_selection_has_watch_rows"],
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "source_report_count": source_report_count,
            "latest_queue_count": latest_queue_count,
            "history_status": history_status,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_probability_selection_summary_history_db_row",
    )

    def to_db_row(report: FakeHistoryReport) -> FakeHistoryDbRow:
        return fake_db_row(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            source_report_count=report.source_report_count,
            latest_queue_count=report.latest_queue_count,
            history_status=report.history_status,
        )

    def from_db_row(row: FakeHistoryDbRow) -> FakeHistoryReport:
        return FakeHistoryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_report_count=row.source_report_count,
            latest_queue_count=row.latest_queue_count,
            history_status=row.history_status,
        )

    companion.PaperProbabilitySelectionSummaryHistoryDbRow = FakeHistoryDbRow
    companion.paper_probability_selection_summary_history_report_to_db_row = to_db_row
    companion.paper_probability_selection_summary_history_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_probability_selection_summary_history_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_probability_selection_summary_history_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_probability_selection_summary_history_store",
    )


def test_insert_history_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeHistoryReport(
        generated_at=datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
        config_version="paper-probability-selection-summary-history-v0",
        source_report_count=3,
        latest_queue_count=6,
        history_status="watch",
    )

    inserted = store_module.insert_paper_probability_selection_summary_history_report(
        connection,
        report,
    )

    assert inserted == fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_report_count=3,
        latest_queue_count=6,
        history_status="watch",
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_probability_selection_summary_history_reports (
            report_sha256,
            generated_at,
            config_version,
            source_report_count,
            latest_generated_at,
            latest_age_seconds,
            latest_queue_count,
            latest_selected_count,
            latest_selected_share,
            average_selected_share,
            history_status,
            recommended_next_step,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        "paper-probability-selection-summary-history-v0",
        3,
        datetime(2026, 6, 22, 11, 45, tzinfo=UTC),
        900,
        6,
        4,
        d("0.666667"),
        d("0.600000"),
        "watch",
        "review_probability_selection",
        ["latest_selection_has_watch_rows"],
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": "paper-probability-selection-summary-history-v0",
            "source_report_count": 3,
            "latest_queue_count": 6,
            "history_status": "watch",
        },
        True,
        True,
        True,
    )


def test_insert_history_report_with_result_observes_duplicate_insert(
    store_module: types.ModuleType,
) -> None:
    assert hasattr(
        store_module,
        "insert_paper_probability_selection_summary_history_report_with_result",
    )
    report = FakeHistoryReport(
        generated_at=datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
        config_version="paper-probability-selection-summary-history-v0",
        source_report_count=3,
        latest_queue_count=6,
        history_status="watch",
    )
    expected_row = fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_report_count=3,
        latest_queue_count=6,
        history_status="watch",
    )

    inserted = store_module.insert_paper_probability_selection_summary_history_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store_module.insert_paper_probability_selection_summary_history_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_history_report_rejects_unexpected_rowcount(
    store_module: types.ModuleType,
) -> None:
    with pytest.raises(ValueError, match="rowcount"):
        store_module.insert_paper_probability_selection_summary_history_report_with_result(
            FakeConnection(rowcount=2),
            FakeHistoryReport(
                generated_at=datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
                config_version="paper-probability-selection-summary-history-v0",
                source_report_count=3,
                latest_queue_count=6,
                history_status="watch",
            ),
        )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_probability_selection_summary_history_report(
            connection,
            FakeHistoryReport(
                generated_at=datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
                config_version="paper-probability-selection-summary-history-v0",
                source_report_count=3,
                latest_queue_count=6,
                history_status="watch",
            ),
            table_name="paper_probability_selection_summary_history_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_history_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(latest_queue_count=8)
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_probability_selection_summary_history_reports(
        connection,
        config_version="paper-probability-selection-summary-history-v0",
        history_status="watch",
        limit=25,
        table_name="selection_summary_history_archive",
    )

    assert reports == (
        FakeHistoryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_report_count=3,
            latest_queue_count=8,
            history_status="watch",
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
            source_report_count,
            latest_generated_at,
            latest_age_seconds,
            latest_queue_count,
            latest_selected_count,
            latest_selected_share,
            average_selected_share,
            history_status,
            recommended_next_step,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        FROM selection_summary_history_archive
        WHERE config_version = %s AND history_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "paper-probability-selection-summary-history-v0",
        "watch",
        25,
    )


def test_load_history_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 22, 13, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-probability-selection-summary-history-v0",
                4,
                datetime(2026, 6, 22, 12, 45, tzinfo=UTC),
                900,
                7,
                5,
                d("0.714286"),
                d("0.650000"),
                "ready",
                "proceed_to_paper_allocation",
                ["selection_summary_history_stable"],
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-probability-selection-summary-history-v0",
                    "source_report_count": 4,
                    "latest_queue_count": 7,
                    "history_status": "ready",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_probability_selection_summary_history_reports(connection)

    assert reports == (
        FakeHistoryReport(
            generated_at=generated_at,
            config_version="paper-probability-selection-summary-history-v0",
            source_report_count=4,
            latest_queue_count=7,
            history_status="ready",
        ),
    )


def test_load_history_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 22, 14, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "config_version": "paper-probability-selection-summary-history-v0",
                "source_report_count": 5,
                "latest_generated_at": datetime(2026, 6, 22, 13, 45, tzinfo=UTC),
                "latest_age_seconds": 900,
                "latest_queue_count": 9,
                "latest_selected_count": 6,
                "latest_selected_share": d("0.666667"),
                "average_selected_share": d("0.600000"),
                "history_status": "blocked",
                "recommended_next_step": "collect_more_history",
                "reason_codes": ["insufficient_selection_summary_history"],
                "payload": {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-probability-selection-summary-history-v0",
                    "source_report_count": 5,
                    "latest_queue_count": 9,
                    "history_status": "blocked",
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = store_module.load_paper_probability_selection_summary_history_reports(connection)

    assert reports == (
        FakeHistoryReport(
            generated_at=generated_at,
            config_version="paper-probability-selection-summary-history-v0",
            source_report_count=5,
            latest_queue_count=9,
            history_status="blocked",
        ),
    )


def test_load_history_reports_accepts_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 22, 15, 0, tzinfo=UTC)
    record_type = namedtuple(
        "SelectionSummaryHistoryRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "source_report_count",
            "latest_generated_at",
            "latest_age_seconds",
            "latest_queue_count",
            "latest_selected_count",
            "latest_selected_share",
            "average_selected_share",
            "history_status",
            "recommended_next_step",
            "reason_codes",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    connection = FakeConnection(
        rows=(
            record_type(
                "e" * 64,
                generated_at,
                "paper-probability-selection-summary-history-v0",
                6,
                datetime(2026, 6, 22, 14, 45, tzinfo=UTC),
                900,
                10,
                7,
                d("0.700000"),
                d("0.625000"),
                "watch",
                "review_probability_selection",
                ["latest_selection_has_watch_rows"],
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-probability-selection-summary-history-v0",
                    "source_report_count": 6,
                    "latest_queue_count": 10,
                    "history_status": "watch",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_probability_selection_summary_history_reports(connection)

    assert reports == (
        FakeHistoryReport(
            generated_at=generated_at,
            config_version="paper-probability-selection-summary-history-v0",
            source_report_count=6,
            latest_queue_count=10,
            history_status="watch",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_probability_selection_summary_history_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"history_status": "stable"}, "history_status"),
        ({"history_status": True}, "history_status"),
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
        store_module.load_paper_probability_selection_summary_history_reports(
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
    assert store_module.DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE == (
        "paper_probability_selection_summary_history_reports"
    )
    assert (
        "DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE"
        in store_module.__all__
    )
    assert "PaperProbabilitySelectionSummaryHistoryInsertResult" in store_module.__all__
    assert "insert_paper_probability_selection_summary_history_report" in store_module.__all__
    assert (
        "insert_paper_probability_selection_summary_history_report_with_result"
        in store_module.__all__
    )
    assert "load_paper_probability_selection_summary_history_reports" in store_module.__all__

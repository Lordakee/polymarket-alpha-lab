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
    source_report_count: int
    latest_action_status: str | None
    latest_recommended_next_step: str | None


@dataclass(frozen=True)
class FakeHistoryDbRow:
    report_sha256: str
    generated_at: datetime
    source_report_count: int
    first_source_generated_at: datetime | None
    last_source_generated_at: datetime | None
    action_status_research_ready_count: int
    action_status_watch_count: int
    action_status_blocked_count: int
    research_status_ready_count: int
    research_status_watch_count: int
    research_status_blocked_count: int
    total_ready_notional: Decimal
    total_selected_notional: Decimal
    total_suggested_notional: Decimal
    latest_action_status: str | None
    latest_recommended_next_step: str | None
    latest_research_status: str | None
    latest_top_research_priority_score: Decimal | None
    latest_average_research_ready_score: Decimal | None
    status_transition_count: int
    ready_notional_delta: Decimal
    selected_notional_delta: Decimal
    latest_selected_count: int
    latest_skipped_count: int
    latest_not_selected_count: int
    latest_primary_reason_code_counts_json: dict[str, int]
    latest_reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        execute_error: BaseException | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.rows = rows
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
        *,
        cursor: FakeCursor | None = None,
    ) -> None:
        self.cursor_instance = cursor if cursor is not None else FakeCursor(rows)
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


def _history_db_row(report: FakeHistoryReport) -> FakeHistoryDbRow:
    return FakeHistoryDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        source_report_count=report.source_report_count,
        first_source_generated_at=datetime(2026, 6, 20, 8, 0, tzinfo=UTC),
        last_source_generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
        action_status_research_ready_count=1,
        action_status_watch_count=1,
        action_status_blocked_count=1,
        research_status_ready_count=1,
        research_status_watch_count=1,
        research_status_blocked_count=1,
        total_ready_notional=Decimal("42.000000"),
        total_selected_notional=Decimal("18.000000"),
        total_suggested_notional=Decimal("54.000000"),
        latest_action_status=report.latest_action_status,
        latest_recommended_next_step=report.latest_recommended_next_step,
        latest_research_status="ready",
        latest_top_research_priority_score=Decimal("0.750000"),
        latest_average_research_ready_score=Decimal("0.650000"),
        status_transition_count=2,
        ready_notional_delta=Decimal("12.000000"),
        selected_notional_delta=Decimal("6.000000"),
        latest_selected_count=2,
        latest_skipped_count=1,
        latest_not_selected_count=0,
        latest_primary_reason_code_counts_json={
            "recommendation_ready": 2,
            "low_net_edge": 1,
        },
        latest_reason_codes_json=[
            "candidate_research_queue_ready",
            "sufficient_depth",
        ],
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "source_report_count": report.source_report_count,
            "latest_action_status": report.latest_action_status,
            "latest_recommended_next_step": report.latest_recommended_next_step,
        },
    )


def _history_select_column_dict(row: FakeHistoryDbRow) -> dict[str, Any]:
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "source_report_count": row.source_report_count,
        "first_source_generated_at": row.first_source_generated_at,
        "last_source_generated_at": row.last_source_generated_at,
        "action_status_research_ready_count": row.action_status_research_ready_count,
        "action_status_watch_count": row.action_status_watch_count,
        "action_status_blocked_count": row.action_status_blocked_count,
        "research_status_ready_count": row.research_status_ready_count,
        "research_status_watch_count": row.research_status_watch_count,
        "research_status_blocked_count": row.research_status_blocked_count,
        "total_ready_notional": row.total_ready_notional,
        "total_selected_notional": row.total_selected_notional,
        "total_suggested_notional": row.total_suggested_notional,
        "latest_action_status": row.latest_action_status,
        "latest_recommended_next_step": row.latest_recommended_next_step,
        "latest_research_status": row.latest_research_status,
        "latest_top_research_priority_score": row.latest_top_research_priority_score,
        "latest_average_research_ready_score": (
            row.latest_average_research_ready_score
        ),
        "status_transition_count": row.status_transition_count,
        "ready_notional_delta": row.ready_notional_delta,
        "selected_notional_delta": row.selected_notional_delta,
        "latest_selected_count": row.latest_selected_count,
        "latest_skipped_count": row.latest_skipped_count,
        "latest_not_selected_count": row.latest_not_selected_count,
        "latest_primary_reason_code_counts": (
            row.latest_primary_reason_code_counts_json
        ),
        "latest_reason_codes": row.latest_reason_codes_json,
        "payload": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.strategy_candidate_research_queue_history_db_row",
    )

    def to_db_row(report: FakeHistoryReport) -> FakeHistoryDbRow:
        return _history_db_row(report)

    def from_db_row(row: FakeHistoryDbRow) -> FakeHistoryReport:
        for flag_name in ("paper_only", "report_only", "readonly"):
            if getattr(row, flag_name, None) is not True:
                raise ValueError(f"DB row must be {flag_name}")
        return FakeHistoryReport(
            generated_at=row.generated_at,
            source_report_count=row.source_report_count,
            latest_action_status=row.latest_action_status,
            latest_recommended_next_step=row.latest_recommended_next_step,
        )

    companion.PaperStrategyCandidateResearchQueueHistoryDbRow = FakeHistoryDbRow
    companion.paper_strategy_candidate_research_queue_history_report_to_db_row = (
        to_db_row
    )
    companion.paper_strategy_candidate_research_queue_history_report_from_db_row = (
        from_db_row
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.strategy_candidate_research_queue_history_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.strategy_candidate_research_queue_history_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_research_queue_history_store",
    )


def _history_report() -> FakeHistoryReport:
    return FakeHistoryReport(
        generated_at=datetime(2026, 6, 20, 12, 30, tzinfo=UTC),
        source_report_count=3,
        latest_action_status="research_ready",
        latest_recommended_next_step="review_candidate_research_queue",
    )


def test_insert_history_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = _history_report()

    inserted = (
        store_module.insert_paper_strategy_candidate_research_queue_history_report(
            connection,
            report,
        )
    )

    assert inserted == FakeHistoryDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        source_report_count=3,
        first_source_generated_at=datetime(2026, 6, 20, 8, 0, tzinfo=UTC),
        last_source_generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
        action_status_research_ready_count=1,
        action_status_watch_count=1,
        action_status_blocked_count=1,
        research_status_ready_count=1,
        research_status_watch_count=1,
        research_status_blocked_count=1,
        total_ready_notional=Decimal("42.000000"),
        total_selected_notional=Decimal("18.000000"),
        total_suggested_notional=Decimal("54.000000"),
        latest_action_status="research_ready",
        latest_recommended_next_step="review_candidate_research_queue",
        latest_research_status="ready",
        latest_top_research_priority_score=Decimal("0.750000"),
        latest_average_research_ready_score=Decimal("0.650000"),
        status_transition_count=2,
        ready_notional_delta=Decimal("12.000000"),
        selected_notional_delta=Decimal("6.000000"),
        latest_selected_count=2,
        latest_skipped_count=1,
        latest_not_selected_count=0,
        latest_primary_reason_code_counts_json={
            "recommendation_ready": 2,
            "low_net_edge": 1,
        },
        latest_reason_codes_json=[
            "candidate_research_queue_ready",
            "sufficient_depth",
        ],
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "source_report_count": 3,
            "latest_action_status": "research_ready",
            "latest_recommended_next_step": "review_candidate_research_queue",
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql).startswith("INSERT INTO paper_strategy_candidate_research_queue_history_reports")
    assert params[0] == "a" * 64


def test_insert_history_report_preserves_execute_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(execute_error=execute_error, close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        store_module.insert_paper_strategy_candidate_research_queue_history_report(
            connection,
            _history_report(),
        )

    assert exc_info.value is execute_error
    assert cursor.closed is True


def test_insert_history_report_propagates_cursor_close_error_after_successful_execute(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.insert_paper_strategy_candidate_research_queue_history_report(
            connection,
            _history_report(),
        )

    assert exc_info.value is close_error
    assert cursor.calls


def test_insert_rejects_invalid_history_table_name_before_cursor_creation(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_strategy_candidate_research_queue_history_report(
            connection,
            _history_report(),
            table_name="public.audit.strategy_candidate_research_queue_history_reports",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_history_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = _history_db_row(_history_report())
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_strategy_candidate_research_queue_history_reports(
        connection,
        latest_action_status="research_ready",
        latest_research_status="ready",
        limit=25,
        table_name="audit.strategy_candidate_research_queue_history_reports",
    )

    assert reports == (_history_report(),)
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            source_report_count,
            first_source_generated_at,
            last_source_generated_at,
            action_status_research_ready_count,
            action_status_watch_count,
            action_status_blocked_count,
            research_status_ready_count,
            research_status_watch_count,
            research_status_blocked_count,
            total_ready_notional,
            total_selected_notional,
            total_suggested_notional,
            latest_action_status,
            latest_recommended_next_step,
            latest_research_status,
            latest_top_research_priority_score,
            latest_average_research_ready_score,
            status_transition_count,
            ready_notional_delta,
            selected_notional_delta,
            latest_selected_count,
            latest_skipped_count,
            latest_not_selected_count,
            latest_primary_reason_code_counts,
            latest_reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        FROM audit.strategy_candidate_research_queue_history_reports
        WHERE latest_action_status = %s AND latest_research_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("research_ready", "ready", 25)


def test_load_history_reports_preserves_execute_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(execute_error=execute_error, close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        store_module.load_paper_strategy_candidate_research_queue_history_reports(
            connection,
        )

    assert exc_info.value is execute_error
    assert cursor.closed is True


def test_load_history_reports_propagates_cursor_close_error_after_successful_fetch(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    row = _history_db_row(_history_report())
    cursor = FakeCursor(rows=(row,), close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.load_paper_strategy_candidate_research_queue_history_reports(
            connection,
        )

    assert exc_info.value is close_error
    assert cursor.calls


def test_load_history_reports_filters_by_research_status_only(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    store_module.load_paper_strategy_candidate_research_queue_history_reports(
        connection,
        latest_research_status="blocked",
    )

    sql, params = connection.cursor_instance.calls[0]
    assert "WHERE latest_research_status = %s" in normalize_sql(sql)
    assert params == ("blocked",)


def test_load_history_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    row = _history_db_row(_history_report())
    connection = FakeConnection(
        rows=(
            (
                row.report_sha256,
                row.generated_at,
                row.source_report_count,
                row.first_source_generated_at,
                row.last_source_generated_at,
                row.action_status_research_ready_count,
                row.action_status_watch_count,
                row.action_status_blocked_count,
                row.research_status_ready_count,
                row.research_status_watch_count,
                row.research_status_blocked_count,
                row.total_ready_notional,
                row.total_selected_notional,
                row.total_suggested_notional,
                row.latest_action_status,
                row.latest_recommended_next_step,
                row.latest_research_status,
                row.latest_top_research_priority_score,
                row.latest_average_research_ready_score,
                row.status_transition_count,
                row.ready_notional_delta,
                row.selected_notional_delta,
                row.latest_selected_count,
                row.latest_skipped_count,
                row.latest_not_selected_count,
                row.latest_primary_reason_code_counts_json,
                row.latest_reason_codes_json,
                row.payload_json,
                row.paper_only,
                row.report_only,
                row.readonly,
            ),
        ),
    )

    reports = store_module.load_paper_strategy_candidate_research_queue_history_reports(
        connection,
    )

    assert reports == (_history_report(),)


def test_load_history_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    row = _history_db_row(_history_report())
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": row.report_sha256,
                "generated_at": row.generated_at,
                "source_report_count": row.source_report_count,
                "first_source_generated_at": row.first_source_generated_at,
                "last_source_generated_at": row.last_source_generated_at,
                "action_status_research_ready_count": (
                    row.action_status_research_ready_count
                ),
                "action_status_watch_count": row.action_status_watch_count,
                "action_status_blocked_count": row.action_status_blocked_count,
                "research_status_ready_count": row.research_status_ready_count,
                "research_status_watch_count": row.research_status_watch_count,
                "research_status_blocked_count": row.research_status_blocked_count,
                "total_ready_notional": row.total_ready_notional,
                "total_selected_notional": row.total_selected_notional,
                "total_suggested_notional": row.total_suggested_notional,
                "latest_action_status": row.latest_action_status,
                "latest_recommended_next_step": row.latest_recommended_next_step,
                "latest_research_status": row.latest_research_status,
                "latest_top_research_priority_score": (
                    row.latest_top_research_priority_score
                ),
                "latest_average_research_ready_score": (
                    row.latest_average_research_ready_score
                ),
                "status_transition_count": row.status_transition_count,
                "ready_notional_delta": row.ready_notional_delta,
                "selected_notional_delta": row.selected_notional_delta,
                "latest_selected_count": row.latest_selected_count,
                "latest_skipped_count": row.latest_skipped_count,
                "latest_not_selected_count": row.latest_not_selected_count,
                "latest_primary_reason_code_counts": (
                    row.latest_primary_reason_code_counts_json
                ),
                "latest_reason_codes": row.latest_reason_codes_json,
                "payload": row.payload_json,
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            },
        ),
    )

    reports = store_module.load_paper_strategy_candidate_research_queue_history_reports(
        connection,
    )

    assert reports == (_history_report(),)


def test_load_history_reports_accepts_namedtuple_like_rows(
    store_module: types.ModuleType,
) -> None:
    row = _history_db_row(_history_report())
    Record = namedtuple(
        "Record",
        [
            "report_sha256",
            "generated_at",
            "source_report_count",
            "first_source_generated_at",
            "last_source_generated_at",
            "action_status_research_ready_count",
            "action_status_watch_count",
            "action_status_blocked_count",
            "research_status_ready_count",
            "research_status_watch_count",
            "research_status_blocked_count",
            "total_ready_notional",
            "total_selected_notional",
            "total_suggested_notional",
            "latest_action_status",
            "latest_recommended_next_step",
            "latest_research_status",
            "latest_top_research_priority_score",
            "latest_average_research_ready_score",
            "status_transition_count",
            "ready_notional_delta",
            "selected_notional_delta",
            "latest_selected_count",
            "latest_skipped_count",
            "latest_not_selected_count",
            "latest_primary_reason_code_counts",
            "latest_reason_codes",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        ],
    )
    connection = FakeConnection(
        rows=(
            Record(
                report_sha256=row.report_sha256,
                generated_at=row.generated_at,
                source_report_count=row.source_report_count,
                first_source_generated_at=row.first_source_generated_at,
                last_source_generated_at=row.last_source_generated_at,
                action_status_research_ready_count=(
                    row.action_status_research_ready_count
                ),
                action_status_watch_count=row.action_status_watch_count,
                action_status_blocked_count=row.action_status_blocked_count,
                research_status_ready_count=row.research_status_ready_count,
                research_status_watch_count=row.research_status_watch_count,
                research_status_blocked_count=row.research_status_blocked_count,
                total_ready_notional=row.total_ready_notional,
                total_selected_notional=row.total_selected_notional,
                total_suggested_notional=row.total_suggested_notional,
                latest_action_status=row.latest_action_status,
                latest_recommended_next_step=row.latest_recommended_next_step,
                latest_research_status=row.latest_research_status,
                latest_top_research_priority_score=row.latest_top_research_priority_score,
                latest_average_research_ready_score=(
                    row.latest_average_research_ready_score
                ),
                status_transition_count=row.status_transition_count,
                ready_notional_delta=row.ready_notional_delta,
                selected_notional_delta=row.selected_notional_delta,
                latest_selected_count=row.latest_selected_count,
                latest_skipped_count=row.latest_skipped_count,
                latest_not_selected_count=row.latest_not_selected_count,
                latest_primary_reason_code_counts=(
                    row.latest_primary_reason_code_counts_json
                ),
                latest_reason_codes=row.latest_reason_codes_json,
                payload=row.payload_json,
                paper_only=row.paper_only,
                report_only=row.report_only,
                readonly=row.readonly,
            ),
        ),
    )

    reports = store_module.load_paper_strategy_candidate_research_queue_history_reports(
        connection,
    )

    assert reports == (_history_report(),)


def test_load_history_reports_rejects_dict_rows_missing_selected_columns(
    store_module: types.ModuleType,
) -> None:
    row = _history_db_row(_history_report())
    record = _history_select_column_dict(row)
    del record["readonly"]
    connection = FakeConnection(rows=(record,))

    with pytest.raises(
        ValueError,
        match="selected strategy candidate research queue history columns",
    ):
        store_module.load_paper_strategy_candidate_research_queue_history_reports(
            connection,
        )

    assert connection.cursor_instance.closed is True


def test_load_history_reports_rejects_namedtuple_like_rows_missing_selected_columns(
    store_module: types.ModuleType,
) -> None:
    row = _history_db_row(_history_report())
    record_values = _history_select_column_dict(row)
    del record_values["readonly"]
    Record = namedtuple("Record", tuple(record_values))
    connection = FakeConnection(rows=(Record(**record_values),))

    with pytest.raises(
        ValueError,
        match="selected strategy candidate research queue history columns",
    ):
        store_module.load_paper_strategy_candidate_research_queue_history_reports(
            connection,
        )

    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.audit.strategy_candidate_research_queue_history_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"latest_action_status": ""}, "latest_action_status"),
        ({"latest_action_status": " research_ready"}, "latest_action_status"),
        ({"latest_research_status": ""}, "latest_research_status"),
        ({"latest_research_status": " blocked"}, "latest_research_status"),
        ({"limit": 0}, "limit"),
        ({"limit": -1}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_rejects_invalid_history_query_inputs_before_cursor_creation(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_module.load_paper_strategy_candidate_research_queue_history_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_closes_cursor_when_history_db_row_hard_flags_fail(
    store_module: types.ModuleType,
) -> None:
    row = _history_db_row(_history_report())
    bad_row = FakeHistoryDbRow(
        **{
            **row.__dict__,
            "readonly": False,
        },
    )
    connection = FakeConnection(rows=(bad_row,))

    with pytest.raises(ValueError, match="readonly"):
        store_module.load_paper_strategy_candidate_research_queue_history_reports(
            connection,
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True

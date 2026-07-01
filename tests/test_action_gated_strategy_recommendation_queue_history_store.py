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
class FakeActionGatedQueueHistoryReport:
    generated_at: datetime
    source_report_count: int
    latest_action_status: str | None
    latest_recommended_next_step: str | None


@dataclass(frozen=True)
class FakeActionGatedQueueHistoryDbRow:
    report_sha256: str
    generated_at: datetime
    source_report_count: int
    first_source_generated_at: datetime | None
    last_source_generated_at: datetime | None
    research_ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    latest_action_status: str | None
    latest_recommended_next_step: str | None
    status_transition_count: int
    ready_notional_delta: Decimal
    latest_reason_code_counts_json: dict[str, int]
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
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False
        self.execute_error = execute_error
        self.fetchall_error = fetchall_error
        self.close_error = close_error

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
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


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_db_row",
    )

    def to_db_row(
        report: FakeActionGatedQueueHistoryReport,
    ) -> FakeActionGatedQueueHistoryDbRow:
        return FakeActionGatedQueueHistoryDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            source_report_count=report.source_report_count,
            first_source_generated_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
            last_source_generated_at=datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
            research_ready_count=1,
            watch_count=1,
            blocked_count=1,
            total_ready_notional=Decimal("42.000000"),
            latest_action_status=report.latest_action_status,
            latest_recommended_next_step=report.latest_recommended_next_step,
            status_transition_count=2,
            ready_notional_delta=Decimal("12.000000"),
            latest_reason_code_counts_json={"cycle_review_passed": 1},
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "source_report_count": report.source_report_count,
                "latest_action_status": report.latest_action_status,
                "latest_recommended_next_step": report.latest_recommended_next_step,
            },
        )

    def from_db_row(
        row: FakeActionGatedQueueHistoryDbRow,
    ) -> FakeActionGatedQueueHistoryReport:
        return FakeActionGatedQueueHistoryReport(
            generated_at=row.generated_at,
            source_report_count=row.source_report_count,
            latest_action_status=row.latest_action_status,
            latest_recommended_next_step=row.latest_recommended_next_step,
        )

    companion.PaperActionGatedStrategyRecommendationQueueHistoryDbRow = (
        FakeActionGatedQueueHistoryDbRow
    )
    companion.paper_action_gated_strategy_recommendation_queue_history_report_to_db_row = (
        to_db_row
    )
    companion.paper_action_gated_strategy_recommendation_queue_history_report_from_db_row = (
        from_db_row
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_store",
    )


def _history_report() -> FakeActionGatedQueueHistoryReport:
    return FakeActionGatedQueueHistoryReport(
        generated_at=datetime(2026, 6, 20, 12, 30, tzinfo=UTC),
        source_report_count=3,
        latest_action_status="research_ready",
        latest_recommended_next_step="review_candidate_research_queue",
    )


def test_insert_action_gated_queue_history_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = _history_report()

    inserted = (
        store_module.insert_paper_action_gated_strategy_recommendation_queue_history_report(
            connection,
            report,
        )
    )

    assert inserted == FakeActionGatedQueueHistoryDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        source_report_count=3,
        first_source_generated_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        last_source_generated_at=datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
        research_ready_count=1,
        watch_count=1,
        blocked_count=1,
        total_ready_notional=Decimal("42.000000"),
        latest_action_status="research_ready",
        latest_recommended_next_step="review_candidate_research_queue",
        status_transition_count=2,
        ready_notional_delta=Decimal("12.000000"),
        latest_reason_code_counts_json={"cycle_review_passed": 1},
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
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_action_gated_strategy_recommendation_queue_history_reports (
            report_sha256,
            generated_at,
            source_report_count,
            first_source_generated_at,
            last_source_generated_at,
            research_ready_count,
            watch_count,
            blocked_count,
            total_ready_notional,
            latest_action_status,
            latest_recommended_next_step,
            status_transition_count,
            ready_notional_delta,
            latest_reason_code_counts,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        3,
        datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
        1,
        1,
        1,
        Decimal("42.000000"),
        "research_ready",
        "review_candidate_research_queue",
        2,
        Decimal("12.000000"),
        {"cycle_review_passed": 1},
        {
            "generated_at": report.generated_at.isoformat(),
            "source_report_count": 3,
            "latest_action_status": "research_ready",
            "latest_recommended_next_step": "review_candidate_research_queue",
        },
        True,
        True,
        True,
    )


def test_insert_propagates_cursor_close_error_after_successful_insert(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.insert_paper_action_gated_strategy_recommendation_queue_history_report(
            connection,
            _history_report(),
        )

    assert exc_info.value is close_error
    assert cursor.calls
    assert cursor.closed is True


def test_load_keeps_fetchall_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    fetchall_error = RuntimeError("fetchall failed")
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(fetchall_error=fetchall_error, close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="fetchall failed") as exc_info:
        store_module.load_paper_action_gated_strategy_recommendation_queue_history_reports(
            connection,
        )

    assert exc_info.value is fetchall_error
    assert cursor.closed is True


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_action_gated_strategy_recommendation_queue_history_reports; drop table users",
        "ActionGatedQueueHistoryReports",
        "audit.ActionGatedQueueHistoryReports",
        "_action_gated_queue_history_reports",
        "audit._action_gated_queue_history_reports",
        "action_gated_queue_history_reports_",
        "public.audit.action_gated_queue_history_reports",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    store_module: types.ModuleType,
    table_name: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_action_gated_strategy_recommendation_queue_history_report(
            connection,
            _history_report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_action_gated_queue_history_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = FakeActionGatedQueueHistoryDbRow(
        report_sha256="b" * 64,
        generated_at=datetime(2026, 6, 20, 13, 0, tzinfo=UTC),
        source_report_count=3,
        first_source_generated_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        last_source_generated_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
        research_ready_count=1,
        watch_count=1,
        blocked_count=1,
        total_ready_notional=Decimal("42.000000"),
        latest_action_status="watch",
        latest_recommended_next_step="await_fresh_cycle_evidence",
        status_transition_count=2,
        ready_notional_delta=Decimal("12.000000"),
        latest_reason_code_counts_json={"cycle_review_watch": 1},
        payload_json={"source_report_count": 3},
    )
    connection = FakeConnection(rows=(row,))

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_history_reports(
            connection,
            latest_action_status="watch",
            limit=25,
            table_name="audit.action_gated_queue_history_reports",
        )
    )

    assert reports == (
        FakeActionGatedQueueHistoryReport(
            generated_at=row.generated_at,
            source_report_count=3,
            latest_action_status="watch",
            latest_recommended_next_step="await_fresh_cycle_evidence",
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
            source_report_count,
            first_source_generated_at,
            last_source_generated_at,
            research_ready_count,
            watch_count,
            blocked_count,
            total_ready_notional,
            latest_action_status,
            latest_recommended_next_step,
            status_transition_count,
            ready_notional_delta,
            latest_reason_code_counts,
            payload,
            paper_only,
            report_only,
            readonly
        FROM audit.action_gated_queue_history_reports
        WHERE latest_action_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("watch", 25)


def test_load_action_gated_queue_history_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 14, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                3,
                datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
                datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
                1,
                1,
                1,
                Decimal("42.000000"),
                "research_ready",
                "review_candidate_research_queue",
                2,
                Decimal("12.000000"),
                {"cycle_review_passed": 1},
                {"source_report_count": 3},
                True,
                True,
                True,
            ),
        ),
    )

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_history_reports(
            connection,
        )
    )

    assert reports == (
        FakeActionGatedQueueHistoryReport(
            generated_at=generated_at,
            source_report_count=3,
            latest_action_status="research_ready",
            latest_recommended_next_step="review_candidate_research_queue",
        ),
    )


def test_load_action_gated_queue_history_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 15, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "source_report_count": 1,
                "first_source_generated_at": generated_at,
                "last_source_generated_at": generated_at,
                "research_ready_count": 0,
                "watch_count": 0,
                "blocked_count": 1,
                "total_ready_notional": Decimal("0.000000"),
                "latest_action_status": "blocked",
                "latest_recommended_next_step": "repair_cycle_evidence",
                "status_transition_count": 0,
                "ready_notional_delta": Decimal("0.000000"),
                "latest_reason_code_counts": {"cycle_review_blocked": 1},
                "payload": {"source_report_count": 1},
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_history_reports(
            connection,
        )
    )

    assert reports == (
        FakeActionGatedQueueHistoryReport(
            generated_at=generated_at,
            source_report_count=1,
            latest_action_status="blocked",
            latest_recommended_next_step="repair_cycle_evidence",
        ),
    )


def test_load_action_gated_queue_history_reports_accepts_namedtuple_like_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 16, 0, tzinfo=UTC)
    Record = namedtuple(
        "Record",
        [
            "report_sha256",
            "generated_at",
            "source_report_count",
            "first_source_generated_at",
            "last_source_generated_at",
            "research_ready_count",
            "watch_count",
            "blocked_count",
            "total_ready_notional",
            "latest_action_status",
            "latest_recommended_next_step",
            "status_transition_count",
            "ready_notional_delta",
            "latest_reason_code_counts",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        ],
    )
    connection = FakeConnection(
        rows=(
            Record(
                report_sha256="e" * 64,
                generated_at=generated_at,
                source_report_count=1,
                first_source_generated_at=generated_at,
                last_source_generated_at=generated_at,
                research_ready_count=0,
                watch_count=1,
                blocked_count=0,
                total_ready_notional=Decimal("0.000000"),
                latest_action_status="watch",
                latest_recommended_next_step="await_fresh_cycle_evidence",
                status_transition_count=0,
                ready_notional_delta=Decimal("0.000000"),
                latest_reason_code_counts={"cycle_review_watch": 1},
                payload={"source_report_count": 1},
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
        ),
    )

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_history_reports(
            connection,
        )
    )

    assert reports == (
        FakeActionGatedQueueHistoryReport(
            generated_at=generated_at,
            source_report_count=1,
            latest_action_status="watch",
            latest_recommended_next_step="await_fresh_cycle_evidence",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.audit.action_gated_queue_history_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"latest_action_status": ""}, "latest_action_status"),
        ({"latest_action_status": " watch"}, "latest_action_status"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_before_cursor_creation(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_module.load_paper_action_gated_strategy_recommendation_queue_history_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.__all__ == (
        "DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_HISTORY_TABLE",
        "insert_paper_action_gated_strategy_recommendation_queue_history_report",
        "load_paper_action_gated_strategy_recommendation_queue_history_reports",
    )

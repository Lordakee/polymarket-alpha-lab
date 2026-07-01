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

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_db_row import (
    paper_action_gated_strategy_recommendation_queue_report_to_db_row,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)


@dataclass(frozen=True)
class FakeActionGatedQueueReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    action_status: str
    recommended_next_step: str


@dataclass(frozen=True)
class FakeActionGatedQueueDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_config_version: str
    action_status: str
    recommended_next_step: str
    candidate_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    reason_code_counts_json: dict[str, int]
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


def _real_watch_report() -> PaperActionGatedStrategyRecommendationQueueReport:
    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=datetime(2026, 6, 20, 17, 0, tzinfo=UTC),
        config_version="action-gated-strategy-recommendation-queue-v0",
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        reason_code_counts=(
            PaperRecommendationCycleActionGateReasonCodeCount(
                reason_code="cycle_review_watch",
                count=1,
            ),
        ),
        candidate_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=Decimal("0.000000"),
    )


def _fake_queue_report() -> FakeActionGatedQueueReport:
    return FakeActionGatedQueueReport(
        generated_at=datetime(2026, 6, 20, 12, 30, tzinfo=UTC),
        config_version="action-gated-queue-v0",
        source_config_version="cycle-action-gate-v0",
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_db_row",
    )

    def to_db_row(
        report: FakeActionGatedQueueReport,
    ) -> FakeActionGatedQueueDbRow:
        return FakeActionGatedQueueDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            source_config_version=report.source_config_version,
            action_status=report.action_status,
            recommended_next_step=report.recommended_next_step,
            candidate_count=4,
            ready_count=2,
            watch_count=1,
            blocked_count=1,
            total_ready_notional=Decimal("42.5000"),
            reason_code_counts_json={"action_gate_research_ready": 1},
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "source_config_version": report.source_config_version,
                "action_status": report.action_status,
                "recommended_next_step": report.recommended_next_step,
            },
        )

    def from_db_row(
        row: FakeActionGatedQueueDbRow,
    ) -> FakeActionGatedQueueReport:
        return FakeActionGatedQueueReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_config_version=row.source_config_version,
            action_status=row.action_status,
            recommended_next_step=row.recommended_next_step,
        )

    companion.PaperActionGatedStrategyRecommendationQueueDbRow = (
        FakeActionGatedQueueDbRow
    )
    companion.paper_action_gated_strategy_recommendation_queue_report_to_db_row = (
        to_db_row
    )
    companion.paper_action_gated_strategy_recommendation_queue_report_from_db_row = (
        from_db_row
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_store",
    )


def test_insert_action_gated_queue_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = _fake_queue_report()

    inserted = (
        store_module.insert_paper_action_gated_strategy_recommendation_queue_report(
            connection,
            report,
        )
    )

    assert inserted == FakeActionGatedQueueDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_config_version=report.source_config_version,
        action_status=report.action_status,
        recommended_next_step=report.recommended_next_step,
        candidate_count=4,
        ready_count=2,
        watch_count=1,
        blocked_count=1,
        total_ready_notional=Decimal("42.5000"),
        reason_code_counts_json={"action_gate_research_ready": 1},
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "source_config_version": report.source_config_version,
            "action_status": report.action_status,
            "recommended_next_step": report.recommended_next_step,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_action_gated_strategy_recommendation_queue_reports (
            report_sha256,
            generated_at,
            config_version,
            source_config_version,
            action_status,
            recommended_next_step,
            candidate_count,
            ready_count,
            watch_count,
            blocked_count,
            total_ready_notional,
            reason_code_counts,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        "action-gated-queue-v0",
        "cycle-action-gate-v0",
        "research_ready",
        "review_candidate_research_queue",
        4,
        2,
        1,
        1,
        Decimal("42.5000"),
        {"action_gate_research_ready": 1},
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": "action-gated-queue-v0",
            "source_config_version": "cycle-action-gate-v0",
            "action_status": "research_ready",
            "recommended_next_step": "review_candidate_research_queue",
        },
        True,
        True,
        True,
    )


def test_insert_keeps_execute_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(execute_error=execute_error, close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        store_module.insert_paper_action_gated_strategy_recommendation_queue_report(
            connection,
            _fake_queue_report(),
        )

    assert exc_info.value is execute_error
    assert cursor.closed is True


def test_load_propagates_cursor_close_error_after_successful_query(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.load_paper_action_gated_strategy_recommendation_queue_reports(
            connection,
        )

    assert exc_info.value is close_error
    assert cursor.calls
    assert cursor.closed is True


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_action_gated_strategy_recommendation_queue_reports; drop table users",
        "ActionGatedQueueReports",
        "audit.ActionGatedQueueReports",
        "_action_gated_queue_reports",
        "audit._action_gated_queue_reports",
        "action_gated_queue_reports_",
        "public.audit.action_gated_queue_reports",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    store_module: types.ModuleType,
    table_name: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_action_gated_strategy_recommendation_queue_report(
            connection,
            FakeActionGatedQueueReport(
                generated_at=datetime(2026, 6, 20, 12, 30, tzinfo=UTC),
                config_version="action-gated-queue-v0",
                source_config_version="cycle-action-gate-v0",
                action_status="watch",
                recommended_next_step="await_fresh_cycle_evidence",
            ),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_action_gated_queue_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = FakeActionGatedQueueDbRow(
        report_sha256="b" * 64,
        generated_at=datetime(2026, 6, 20, 13, 0, tzinfo=UTC),
        config_version="action-gated-queue-v0",
        source_config_version="cycle-action-gate-v0",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        candidate_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=Decimal("0.0000"),
        reason_code_counts_json={"action_gate_watch": 1},
        payload_json={
            "generated_at": "2026-06-20T13:00:00+00:00",
            "config_version": "action-gated-queue-v0",
            "source_config_version": "cycle-action-gate-v0",
            "action_status": "watch",
            "recommended_next_step": "await_fresh_cycle_evidence",
        },
    )
    connection = FakeConnection(rows=(row,))

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_reports(
            connection,
            source_config_version="cycle-action-gate-v0",
            action_status="watch",
            limit=25,
            table_name="audit.action_gated_queue_reports",
        )
    )

    assert reports == (
        FakeActionGatedQueueReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_config_version=row.source_config_version,
            action_status=row.action_status,
            recommended_next_step=row.recommended_next_step,
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
            source_config_version,
            action_status,
            recommended_next_step,
            candidate_count,
            ready_count,
            watch_count,
            blocked_count,
            total_ready_notional,
            reason_code_counts,
            payload,
            paper_only,
            report_only,
            readonly
        FROM audit.action_gated_queue_reports
        WHERE source_config_version = %s AND action_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("cycle-action-gate-v0", "watch", 25)


def test_load_action_gated_queue_reports_filters_by_action_status_only(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    store_module.load_paper_action_gated_strategy_recommendation_queue_reports(
        connection,
        action_status="blocked",
    )

    sql, params = connection.cursor_instance.calls[0]
    assert "WHERE action_status = %s" in normalize_sql(sql)
    assert params == ("blocked",)


def test_load_action_gated_queue_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 14, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "action-gated-queue-v0",
                "cycle-action-gate-v0",
                "research_ready",
                "review_candidate_research_queue",
                3,
                2,
                1,
                0,
                Decimal("35.0000"),
                {"action_gate_research_ready": 1},
                {
                    "generated_at": "2026-06-20T14:00:00+00:00",
                    "config_version": "action-gated-queue-v0",
                    "source_config_version": "cycle-action-gate-v0",
                    "action_status": "research_ready",
                    "recommended_next_step": "review_candidate_research_queue",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_reports(
            connection,
        )
    )

    assert reports == (
        FakeActionGatedQueueReport(
            generated_at=generated_at,
            config_version="action-gated-queue-v0",
            source_config_version="cycle-action-gate-v0",
            action_status="research_ready",
            recommended_next_step="review_candidate_research_queue",
        ),
    )


def test_load_action_gated_queue_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 15, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "config_version": "action-gated-queue-v0",
                "source_config_version": "cycle-action-gate-v0",
                "action_status": "blocked",
                "recommended_next_step": "repair_cycle_evidence",
                "candidate_count": 0,
                "ready_count": 0,
                "watch_count": 0,
                "blocked_count": 0,
                "total_ready_notional": Decimal("0.0000"),
                "reason_code_counts": {"action_gate_blocked": 1},
                "payload": {
                    "generated_at": "2026-06-20T15:00:00+00:00",
                    "config_version": "action-gated-queue-v0",
                    "source_config_version": "cycle-action-gate-v0",
                    "action_status": "blocked",
                    "recommended_next_step": "repair_cycle_evidence",
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_reports(
            connection,
        )
    )

    assert reports == (
        FakeActionGatedQueueReport(
            generated_at=generated_at,
            config_version="action-gated-queue-v0",
            source_config_version="cycle-action-gate-v0",
            action_status="blocked",
            recommended_next_step="repair_cycle_evidence",
        ),
    )


def test_load_action_gated_queue_reports_accepts_namedtuple_like_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 16, 0, tzinfo=UTC)
    Record = namedtuple(
        "Record",
        [
            "report_sha256",
            "generated_at",
            "config_version",
            "source_config_version",
            "action_status",
            "recommended_next_step",
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "total_ready_notional",
            "reason_code_counts",
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
                config_version="action-gated-queue-v0",
                source_config_version="cycle-action-gate-v0",
                action_status="watch",
                recommended_next_step="await_fresh_cycle_evidence",
                candidate_count=0,
                ready_count=0,
                watch_count=0,
                blocked_count=0,
                total_ready_notional=Decimal("0.0000"),
                reason_code_counts={"action_gate_watch": 1},
                payload={
                    "generated_at": "2026-06-20T16:00:00+00:00",
                    "config_version": "action-gated-queue-v0",
                    "source_config_version": "cycle-action-gate-v0",
                    "action_status": "watch",
                    "recommended_next_step": "await_fresh_cycle_evidence",
                },
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
        ),
    )

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_reports(
            connection,
        )
    )

    assert reports == (
        FakeActionGatedQueueReport(
            generated_at=generated_at,
            config_version="action-gated-queue-v0",
            source_config_version="cycle-action-gate-v0",
            action_status="watch",
            recommended_next_step="await_fresh_cycle_evidence",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.audit.action_gated_queue_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"source_config_version": ""}, "source_config_version"),
        ({"source_config_version": " cycle-action-gate-v0"}, "source_config_version"),
        ({"action_status": ""}, "action_status"),
        ({"action_status": " watch"}, "action_status"),
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
        store_module.load_paper_action_gated_strategy_recommendation_queue_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_store_load_round_trips_real_action_gated_queue_report_from_db_columns() -> None:
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_store",
        None,
    )
    store_module = importlib.import_module(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_store",
    )
    report = _real_watch_report()
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(report)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": row.report_sha256,
                "generated_at": row.generated_at,
                "config_version": row.config_version,
                "source_config_version": row.source_config_version,
                "action_status": row.action_status,
                "recommended_next_step": row.recommended_next_step,
                "candidate_count": row.candidate_count,
                "ready_count": row.ready_count,
                "watch_count": row.watch_count,
                "blocked_count": row.blocked_count,
                "total_ready_notional": row.total_ready_notional,
                "reason_code_counts": row.reason_code_counts_json,
                "payload": row.payload_json,
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            },
        ),
    )

    loaded = store_module.load_paper_action_gated_strategy_recommendation_queue_reports(
        connection,
    )

    assert loaded == (report,)


def test_public_exports_include_default_table_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.__all__ == (
        "DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_TABLE",
        "insert_paper_action_gated_strategy_recommendation_queue_report",
        "load_paper_action_gated_strategy_recommendation_queue_reports",
    )

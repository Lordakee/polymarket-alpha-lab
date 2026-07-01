from __future__ import annotations

import ast
import inspect
import sys
import types
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab import (
    action_gated_strategy_recommendation_queue_psycopg_read as read_module,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_db_row import (
    paper_action_gated_strategy_recommendation_queue_report_to_db_row,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg_read import (
    PaperActionGatedStrategyRecommendationQueueReadOptions,
    load_paper_action_gated_strategy_recommendation_queue_reports,
    load_paper_action_gated_strategy_recommendation_queue_reports_with_psycopg,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)


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
        self.rollback_count = 0
        self.closed = False

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.closed = True


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def _watch_report() -> PaperActionGatedStrategyRecommendationQueueReport:
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


def _db_record(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> dict[str, Any]:
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(report)
    return {
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
    }


def test_load_action_gated_queue_reports_uses_bounded_read_only_select() -> None:
    report = _watch_report()
    connection = FakeConnection(rows=(_db_record(report),))

    loaded = load_paper_action_gated_strategy_recommendation_queue_reports(
        connection,
        options=PaperActionGatedStrategyRecommendationQueueReadOptions(
            source_config_version="paper-recommendation-cycle-action-gate-v0",
            action_status="watch",
            limit=25,
            table_name="audit.action_gated_queue_reports",
        ),
    )

    assert loaded == (report,)
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    assert len(connection.cursor_instance.calls) == 1
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
        ORDER BY generated_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-recommendation-cycle-action-gate-v0", "watch", 25)


def test_psycopg_read_module_stays_select_only_by_source_boundary() -> None:
    source = inspect.getsource(read_module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    string_literals: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value.upper())

    forbidden_imports = {
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg",
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.runner",
        "polymarket_alpha_lab.paper_execution",
    }
    forbidden_calls = {
        "commit",
        "rollback",
        "executemany",
        "execute_batch",
        "execute_values",
    }
    forbidden_sql_tokens = (
        "INSERT",
        "UPDATE",
        "DELETE",
        "CREATE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "COMMIT",
        "ROLLBACK",
    )

    assert imported_modules.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert all(
        token not in literal
        for literal in string_literals
        for token in forbidden_sql_tokens
    )


def test_load_with_psycopg_opens_autocommit_connection_without_committing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _watch_report()
    connection = FakeConnection(rows=(_db_record(report),))
    connect_calls: list[tuple[str, dict[str, Any]]] = []

    def connect(dsn: str, **kwargs: Any) -> FakeConnection:
        connect_calls.append((dsn, kwargs))
        return connection

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=connect))

    loaded = load_paper_action_gated_strategy_recommendation_queue_reports_with_psycopg(
        "postgresql://postgres:postgres@localhost:54322/postgres",
        options=PaperActionGatedStrategyRecommendationQueueReadOptions(limit=10),
    )

    assert loaded == (report,)
    assert connect_calls == [
        ("postgresql://postgres:postgres@localhost:54322/postgres", {"autocommit": True}),
    ]
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.closed is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.audit.action_gated_queue_reports"}, "table_name"),
        ({"table_name": "ActionGatedQueueReports"}, "table_name"),
        ({"source_config_version": ""}, "source_config_version"),
        (
            {"source_config_version": " paper-recommendation-cycle-action-gate-v0"},
            "source_config_version",
        ),
        ({"action_status": "ready"}, "action_status"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
        ({"limit": 501}, "limit"),
    ),
)
def test_read_options_reject_invalid_query_inputs(
    kwargs: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        PaperActionGatedStrategyRecommendationQueueReadOptions(**kwargs)


def test_read_options_are_frozen() -> None:
    options = PaperActionGatedStrategyRecommendationQueueReadOptions()

    with pytest.raises(FrozenInstanceError):
        options.limit = 25


def test_load_rejects_row_with_disabled_hard_flags_and_closes_cursor() -> None:
    record = _db_record(_watch_report()) | {"paper_only": False}
    connection = FakeConnection(rows=(record,))

    with pytest.raises(ValueError, match="paper_only"):
        load_paper_action_gated_strategy_recommendation_queue_reports(connection)

    assert connection.cursor_instance.closed is True
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_rejects_payload_json_floats_and_closes_cursor() -> None:
    record = _db_record(_watch_report())
    record["payload"] = dict(record["payload"]) | {"total_ready_notional": 0.0}
    connection = FakeConnection(rows=(record,))

    with pytest.raises(ValueError, match="float|floats"):
        load_paper_action_gated_strategy_recommendation_queue_reports(connection)

    assert connection.cursor_instance.closed is True
    assert connection.commit_count == 0
    assert connection.rollback_count == 0

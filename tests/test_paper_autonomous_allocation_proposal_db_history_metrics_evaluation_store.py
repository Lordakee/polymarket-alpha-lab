from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeEvaluationReport:
    generated_at: datetime
    config_version: str
    evaluation_status: str


@dataclass(frozen=True)
class FakeEvaluationDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    evaluation_status: str
    recommended_next_step: str
    source_report_count: int
    latest_report_generated_at: datetime | None
    reason_code_counts_json: dict[str, int]
    reason_codes: tuple[str, ...]
    diagnostics_json: dict[str, Any]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


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
    companion = types.ModuleType(
        "polymarket_alpha_lab"
        ".paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row",
    )

    def to_db_row(report: FakeEvaluationReport) -> FakeEvaluationDbRow:
        return FakeEvaluationDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            evaluation_status=report.evaluation_status,
            recommended_next_step="hold_paper_autonomous_allocation_proposal",
            source_report_count=4,
            latest_report_generated_at=datetime(2026, 6, 24, 12, 0, tzinfo=UTC),
            reason_code_counts_json={"metrics_churn_share_watch": 1},
            reason_codes=("metrics_churn_share_watch",),
            diagnostics_json={
                "source_report_count": 4,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "evaluation_status": report.evaluation_status,
            },
        )

    def from_db_row(row: FakeEvaluationDbRow) -> FakeEvaluationReport:
        return FakeEvaluationReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            evaluation_status=row.evaluation_status,
        )

    companion.PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow = (
        FakeEvaluationDbRow
    )
    companion.paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row = (
        to_db_row
    )
    companion.paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row = (
        from_db_row
    )
    monkeypatch.setitem(
        sys.modules,
        (
            "polymarket_alpha_lab"
            ".paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row"
        ),
        companion,
    )
    sys.modules.pop(
        (
            "polymarket_alpha_lab"
            ".paper_autonomous_allocation_proposal_db_history_metrics_evaluation_store"
        ),
        None,
    )
    return importlib.import_module(
        (
            "polymarket_alpha_lab"
            ".paper_autonomous_allocation_proposal_db_history_metrics_evaluation_store"
        ),
    )


def test_insert_metrics_evaluation_report_uses_parameterized_idempotent_insert(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 24, 16, 30, tzinfo=UTC)
    connection = FakeConnection()
    report = FakeEvaluationReport(
        generated_at=generated_at,
        config_version="paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0",
        evaluation_status="watch",
    )

    insert_report = (
        store_module
        .insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report
    )
    inserted = insert_report(connection, report)

    assert inserted == FakeEvaluationDbRow(
        report_sha256="a" * 64,
        generated_at=generated_at,
        config_version=report.config_version,
        evaluation_status="watch",
        recommended_next_step="hold_paper_autonomous_allocation_proposal",
        source_report_count=4,
        latest_report_generated_at=datetime(2026, 6, 24, 12, 0, tzinfo=UTC),
        reason_code_counts_json={"metrics_churn_share_watch": 1},
        reason_codes=("metrics_churn_share_watch",),
        diagnostics_json={
            "source_report_count": 4,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": report.config_version,
            "evaluation_status": "watch",
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_autonomous_allocation_proposal_metrics_evaluation_reports (
            report_sha256,
            generated_at,
            config_version,
            evaluation_status,
            recommended_next_step,
            source_report_count,
            latest_report_generated_at,
            reason_code_counts,
            reason_codes,
            diagnostics,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        generated_at,
        report.config_version,
        "watch",
        "hold_paper_autonomous_allocation_proposal",
        4,
        datetime(2026, 6, 24, 12, 0, tzinfo=UTC),
        {"metrics_churn_share_watch": 1},
        ["metrics_churn_share_watch"],
        {
            "source_report_count": 4,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "generated_at": generated_at.isoformat(),
            "config_version": report.config_version,
            "evaluation_status": "watch",
        },
        True,
        True,
        True,
    )


def test_insert_accepts_schema_qualified_table_name(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    insert_report = (
        store_module
        .insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report
    )

    insert_report(
        connection,
        FakeEvaluationReport(
            generated_at=datetime(2026, 6, 24, 16, 30, tzinfo=UTC),
            config_version=(
                "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0"
            ),
            evaluation_status="watch",
        ),
        table_name="paper_ops.paper_autonomous_allocation_proposal_metrics_evaluation_reports",
    )

    sql, _ = connection.cursor_instance.calls[0]
    assert (
        "INSERT INTO paper_ops."
        "paper_autonomous_allocation_proposal_metrics_evaluation_reports"
    ) in normalize_sql(sql)


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    insert_report = (
        store_module
        .insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report
    )

    with pytest.raises(ValueError, match="table_name"):
        insert_report(
            connection,
            FakeEvaluationReport(
                generated_at=datetime(2026, 6, 24, 16, 30, tzinfo=UTC),
                config_version=(
                    "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0"
                ),
                evaluation_status="pass",
            ),
            table_name=(
                "paper_autonomous_allocation_proposal_metrics_evaluation_reports; drop"
            ),
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_metrics_evaluation_reports_filters_status_config_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = FakeEvaluationDbRow(
        report_sha256="b" * 64,
        generated_at=datetime(2026, 6, 24, 18, 0, tzinfo=UTC),
        config_version="paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0",
        evaluation_status="blocked",
        recommended_next_step="block_paper_autonomous_allocation_proposal",
        source_report_count=0,
        latest_report_generated_at=None,
        reason_code_counts_json={
            "missing_paper_autonomous_allocation_proposal_metrics_source_history": 1,
        },
        reason_codes=(
            "missing_paper_autonomous_allocation_proposal_metrics_source_history",
        ),
        diagnostics_json={
            "source_report_count": 0,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        payload_json={
            "generated_at": "2026-06-24T18:00:00+00:00",
            "config_version": (
                "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0"
            ),
            "evaluation_status": "blocked",
        },
    )
    connection = FakeConnection(rows=(row,))
    load_reports = (
        store_module
        .load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports
    )

    reports = load_reports(
        connection,
        config_version=(
            "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0"
        ),
        evaluation_status="blocked",
        limit=25,
        table_name="paper_ops.metrics_evaluation_archive",
    )

    assert reports == (
        FakeEvaluationReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            evaluation_status=row.evaluation_status,
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
            evaluation_status,
            recommended_next_step,
            source_report_count,
            latest_report_generated_at,
            reason_code_counts,
            reason_codes,
            diagnostics,
            payload,
            paper_only,
            report_only,
            readonly
        FROM paper_ops.metrics_evaluation_archive
        WHERE config_version = %s AND evaluation_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0",
        "blocked",
        25,
    )


def test_load_metrics_evaluation_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 24, 18, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0",
                "pass",
                "review_paper_autonomous_allocation_proposal",
                7,
                datetime(2026, 6, 24, 17, 0, tzinfo=UTC),
                {
                    "paper_autonomous_allocation_proposal_metrics_evaluation_passed": 1,
                },
                ("paper_autonomous_allocation_proposal_metrics_evaluation_passed",),
                {
                    "source_report_count": 7,
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
                {
                    "generated_at": "2026-06-24T18:00:00+00:00",
                    "config_version": (
                        "paper-autonomous-allocation-proposal-db-history-metrics-"
                        "evaluation-v0"
                    ),
                    "evaluation_status": "pass",
                },
                True,
                True,
                True,
            ),
        ),
    )
    load_reports = (
        store_module
        .load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports
    )

    reports = load_reports(connection)

    assert reports == (
        FakeEvaluationReport(
            generated_at=generated_at,
            config_version=(
                "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0"
            ),
            evaluation_status="pass",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "bad-name"}, "table_name"),
        ({"table_name": "public.too.many.parts"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"evaluation_status": "pending"}, "evaluation_status"),
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
    load_reports = (
        store_module
        .load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports
    )

    with pytest.raises(ValueError, match=message):
        load_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []

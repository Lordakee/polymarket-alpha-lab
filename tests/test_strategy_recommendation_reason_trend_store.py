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
class FakeReasonTrendReport:
    generated_at: datetime
    config_version: str
    status: str


@dataclass(frozen=True)
class FakeReasonTrendDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    status: str
    source_report_count: int
    first_generated_at: datetime | None
    latest_generated_at: datetime | None
    latest_primary_reason_code_counts_json: dict[str, int]
    total_primary_reason_code_counts_json: dict[str, int]
    top_new_reason_codes_json: dict[str, int]
    persistent_reason_codes_json: list[str]
    latest_reason_code_count: int
    latest_no_reason_code_count: int
    latest_blocked_reason_count: int
    latest_no_reason_code_share: Decimal | None
    latest_blocked_reason_share: Decimal | None
    max_blocked_reason_share: Decimal
    max_no_reason_code_share: Decimal
    top_reason_code_limit: int
    blocked_reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.rows = rows
        self.execute_error = execute_error
        self.fetchall_error = fetchall_error
        self.close_error = close_error
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

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
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows,
            execute_error=execute_error,
            fetchall_error=fetchall_error,
            close_error=close_error,
        )
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


def fake_db_row(
    *,
    report_sha256: str = "b" * 64,
    generated_at: datetime = datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
    config_version: str = "strategy-recommendation-reason-trend-v0",
    status: str = "watch",
) -> FakeReasonTrendDbRow:
    return FakeReasonTrendDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        status=status,
        source_report_count=2,
        first_generated_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        latest_generated_at=generated_at,
        latest_primary_reason_code_counts_json={"new_reason": 2, "alpha_reason": 1},
        total_primary_reason_code_counts_json={"alpha_reason": 3, "new_reason": 2},
        top_new_reason_codes_json={"new_reason": 2},
        persistent_reason_codes_json=["alpha_reason"],
        latest_reason_code_count=3,
        latest_no_reason_code_count=0,
        latest_blocked_reason_count=0,
        latest_no_reason_code_share=Decimal("0.000000"),
        latest_blocked_reason_share=Decimal("0.000000"),
        max_blocked_reason_share=Decimal("0.500000"),
        max_no_reason_code_share=Decimal("0.500000"),
        top_reason_code_limit=5,
        blocked_reason_codes_json=["blocked_forecast_quality"],
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "status": status,
        },
    )


def fake_report() -> FakeReasonTrendReport:
    return FakeReasonTrendReport(
        generated_at=datetime(2026, 6, 20, 9, 30, tzinfo=UTC),
        config_version="strategy-recommendation-reason-trend-v0",
        status="watch",
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.strategy_recommendation_reason_trend_db_row",
    )

    def to_db_row(report: FakeReasonTrendReport) -> FakeReasonTrendDbRow:
        return fake_db_row(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            status=report.status,
        )

    def from_db_row(row: FakeReasonTrendDbRow) -> FakeReasonTrendReport:
        return FakeReasonTrendReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            status=row.status,
        )

    companion.PaperStrategyRecommendationReasonTrendDbRow = FakeReasonTrendDbRow
    companion.strategy_recommendation_reason_trend_report_to_db_row = to_db_row
    companion.strategy_recommendation_reason_trend_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.strategy_recommendation_reason_trend_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.strategy_recommendation_reason_trend_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_reason_trend_store",
    )


def test_insert_strategy_recommendation_reason_trend_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReasonTrendReport(
        generated_at=datetime(2026, 6, 20, 9, 30, tzinfo=UTC),
        config_version="strategy-recommendation-reason-trend-v0",
        status="watch",
    )

    inserted = store_module.insert_strategy_recommendation_reason_trend_report(
        connection,
        report,
    )

    assert inserted == fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO strategy_recommendation_reason_trend_reports (
            report_sha256,
            generated_at,
            config_version,
            status,
            source_report_count,
            first_generated_at,
            latest_generated_at,
            latest_primary_reason_code_counts,
            total_primary_reason_code_counts,
            top_new_reason_codes,
            persistent_reason_codes,
            latest_reason_code_count,
            latest_no_reason_code_count,
            latest_blocked_reason_count,
            latest_no_reason_code_share,
            latest_blocked_reason_share,
            max_blocked_reason_share,
            max_no_reason_code_share,
            top_reason_code_limit,
            blocked_reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        "watch",
        2,
        datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        report.generated_at,
        {"new_reason": 2, "alpha_reason": 1},
        {"alpha_reason": 3, "new_reason": 2},
        {"new_reason": 2},
        ["alpha_reason"],
        3,
        0,
        0,
        Decimal("0.000000"),
        Decimal("0.000000"),
        Decimal("0.500000"),
        Decimal("0.500000"),
        5,
        ["blocked_forecast_quality"],
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "status": "watch",
        },
        True,
        True,
        True,
    )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_strategy_recommendation_reason_trend_report(
            connection,
            FakeReasonTrendReport(
                generated_at=datetime(2026, 6, 20, 9, 30, tzinfo=UTC),
                config_version="strategy-recommendation-reason-trend-v0",
                status="watch",
            ),
            table_name="strategy_recommendation_reason_trend_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_strategy_recommendation_reason_trend_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(status="blocked")
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_strategy_recommendation_reason_trend_reports(
        connection,
        config_version="strategy-recommendation-reason-trend-v0",
        status="blocked",
        limit=25,
        table_name="strategy_reason_trend_archive",
    )

    assert reports == (
        FakeReasonTrendReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            status=row.status,
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
            status,
            source_report_count,
            first_generated_at,
            latest_generated_at,
            latest_primary_reason_code_counts,
            total_primary_reason_code_counts,
            top_new_reason_codes,
            persistent_reason_codes,
            latest_reason_code_count,
            latest_no_reason_code_count,
            latest_blocked_reason_count,
            latest_no_reason_code_share,
            latest_blocked_reason_share,
            max_blocked_reason_share,
            max_no_reason_code_share,
            top_reason_code_limit,
            blocked_reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        FROM strategy_reason_trend_archive
        WHERE config_version = %s AND status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("strategy-recommendation-reason-trend-v0", "blocked", 25)


def test_load_strategy_recommendation_reason_trend_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "strategy-recommendation-reason-trend-v0",
                "stable",
                0,
                None,
                None,
                {},
                {},
                {},
                [],
                0,
                0,
                0,
                None,
                None,
                Decimal("0.500000"),
                Decimal("0.500000"),
                5,
                ["blocked_forecast_quality"],
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "strategy-recommendation-reason-trend-v0",
                    "status": "stable",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_strategy_recommendation_reason_trend_reports(connection)

    assert reports == (
        FakeReasonTrendReport(
            generated_at=generated_at,
            config_version="strategy-recommendation-reason-trend-v0",
            status="stable",
        ),
    )


def test_load_strategy_recommendation_reason_trend_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "config_version": "strategy-recommendation-reason-trend-v0",
                "status": "watch",
                "source_report_count": 2,
                "first_generated_at": datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
                "latest_generated_at": generated_at,
                "latest_primary_reason_code_counts": {"new_reason": 2},
                "total_primary_reason_code_counts": {"alpha_reason": 1, "new_reason": 2},
                "top_new_reason_codes": {"new_reason": 2},
                "persistent_reason_codes": ["alpha_reason"],
                "latest_reason_code_count": 2,
                "latest_no_reason_code_count": 0,
                "latest_blocked_reason_count": 0,
                "latest_no_reason_code_share": Decimal("0.000000"),
                "latest_blocked_reason_share": Decimal("0.000000"),
                "max_blocked_reason_share": Decimal("0.500000"),
                "max_no_reason_code_share": Decimal("0.500000"),
                "top_reason_code_limit": 5,
                "blocked_reason_codes": ["blocked_forecast_quality"],
                "payload": {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "strategy-recommendation-reason-trend-v0",
                    "status": "watch",
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = store_module.load_strategy_recommendation_reason_trend_reports(connection)

    assert reports == (
        FakeReasonTrendReport(
            generated_at=generated_at,
            config_version="strategy-recommendation-reason-trend-v0",
            status="watch",
        ),
    )


def test_load_strategy_recommendation_reason_trend_reports_accepts_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 13, 0, tzinfo=UTC)
    record_type = namedtuple(
        "ReasonTrendRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "status",
            "source_report_count",
            "first_generated_at",
            "latest_generated_at",
            "latest_primary_reason_code_counts",
            "total_primary_reason_code_counts",
            "top_new_reason_codes",
            "persistent_reason_codes",
            "latest_reason_code_count",
            "latest_no_reason_code_count",
            "latest_blocked_reason_count",
            "latest_no_reason_code_share",
            "latest_blocked_reason_share",
            "max_blocked_reason_share",
            "max_no_reason_code_share",
            "top_reason_code_limit",
            "blocked_reason_codes",
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
                "strategy-recommendation-reason-trend-v0",
                "blocked",
                2,
                datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
                generated_at,
                {"blocked_forecast_quality": 2},
                {"blocked_forecast_quality": 3},
                {},
                ["blocked_forecast_quality"],
                2,
                0,
                2,
                Decimal("0.000000"),
                Decimal("1.000000"),
                Decimal("0.500000"),
                Decimal("0.500000"),
                5,
                ["blocked_forecast_quality"],
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "strategy-recommendation-reason-trend-v0",
                    "status": "blocked",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_strategy_recommendation_reason_trend_reports(connection)

    assert reports == (
        FakeReasonTrendReport(
            generated_at=generated_at,
            config_version="strategy-recommendation-reason-trend-v0",
            status="blocked",
        ),
    )


@pytest.mark.parametrize("operation", ("insert", "load"))
def test_cursor_close_error_after_success_is_propagated(
    store_module: types.ModuleType,
    operation: str,
) -> None:
    connection = FakeConnection(close_error=RuntimeError("cursor close failed"))

    with pytest.raises(RuntimeError, match="cursor close failed") as exc_info:
        if operation == "insert":
            store_module.insert_strategy_recommendation_reason_trend_report(
                connection,
                fake_report(),
            )
        else:
            store_module.load_strategy_recommendation_reason_trend_reports(connection)

    assert exc_info.value is connection.cursor_instance.close_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("operation", "operation_error_name"),
    (("insert", "execute_error"), ("load", "fetchall_error")),
)
def test_operation_error_wins_when_cursor_close_also_fails(
    store_module: types.ModuleType,
    operation: str,
    operation_error_name: str,
) -> None:
    operation_error = RuntimeError("db operation failed")
    close_error = RuntimeError("cursor close failed")
    connection = FakeConnection(
        **{
            operation_error_name: operation_error,
            "close_error": close_error,
        },
    )

    with pytest.raises(RuntimeError, match="db operation failed") as exc_info:
        if operation == "insert":
            store_module.insert_strategy_recommendation_reason_trend_report(
                connection,
                fake_report(),
            )
        else:
            store_module.load_strategy_recommendation_reason_trend_reports(connection)

    assert exc_info.value is operation_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("operation", "operation_error_name"),
    (("insert", "execute_error"), ("load", "fetchall_error")),
)
def test_base_exception_operation_error_still_closes_cursor(
    store_module: types.ModuleType,
    operation: str,
    operation_error_name: str,
) -> None:
    class NonExceptionOperationFailure(BaseException):
        pass

    operation_error = NonExceptionOperationFailure("operation interrupted")
    connection = FakeConnection(**{operation_error_name: operation_error})

    with pytest.raises(NonExceptionOperationFailure) as exc_info:
        if operation == "insert":
            store_module.insert_strategy_recommendation_reason_trend_report(
                connection,
                fake_report(),
            )
        else:
            store_module.load_strategy_recommendation_reason_trend_reports(connection)

    assert exc_info.value is operation_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.strategy_recommendation_reason_trend_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " strategy-v0"}, "config_version"),
        ({"status": "pass"}, "status"),
        ({"status": True}, "status"),
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
        store_module.load_strategy_recommendation_reason_trend_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0

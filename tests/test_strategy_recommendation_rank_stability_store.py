from __future__ import annotations

from collections import namedtuple
from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_recommendation_rank_stability import (
    PaperStrategyRecommendationRankStabilityReport,
    PaperStrategyRecommendationRankStabilityRow,
)
from polymarket_alpha_lab.strategy_recommendation_rank_stability_db_row import (
    PaperStrategyRecommendationRankStabilityDbRow,
    strategy_recommendation_rank_stability_report_to_db_row,
)
import polymarket_alpha_lab.strategy_recommendation_rank_stability_store as rank_stability_store
from polymarket_alpha_lab.strategy_recommendation_rank_stability_store import (
    DEFAULT_STRATEGY_RECOMMENDATION_RANK_STABILITY_REPORTS_TABLE,
    insert_strategy_recommendation_rank_stability_report,
    load_strategy_recommendation_rank_stability_reports,
)


GENERATED_AT = datetime(2026, 6, 22, 8, 30, tzinfo=UTC)
LATEST_GENERATED_AT = datetime(2026, 6, 22, 8, 25, tzinfo=UTC)
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "stability_status",
    "reason_codes_json",
    "source_report_count",
    "candidate_count",
    "stable_count",
    "watch_count",
    "blocked_count",
    "stable_ready_count",
    "unstable_ready_count",
    "selected_side_changed_count",
    "queue_status_changed_count",
    "latest_generated_at",
    "top_stable_market_slug",
    "rows_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


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


def _row() -> PaperStrategyRecommendationRankStabilityRow:
    return PaperStrategyRecommendationRankStabilityRow(
        market_slug="alpha",
        stability_status="stable",
        latest_selected_side="yes",
        latest_queue_status="ready",
        present_snapshot_count=2,
        ready_snapshot_count=2,
        first_rank=1,
        latest_rank=1,
        rank_delta=0,
        max_rank_movement=0,
        first_score=d("0.700000"),
        latest_score=d("0.710000"),
        score_delta=d("0.010000"),
        max_score_delta=d("0.010000"),
        first_notional=d("10.000000"),
        latest_notional=d("10.000000"),
        notional_delta=d("0.000000"),
        selected_side_changed=False,
        queue_status_changed=False,
        reason_codes=("stable_ready",),
    )


def _report() -> PaperStrategyRecommendationRankStabilityReport:
    return PaperStrategyRecommendationRankStabilityReport(
        generated_at=GENERATED_AT,
        config_version="strategy-recommendation-rank-stability-v0",
        source_report_count=2,
        candidate_count=1,
        stability_status="stable",
        stable_count=1,
        watch_count=0,
        blocked_count=0,
        stable_ready_count=1,
        unstable_ready_count=0,
        selected_side_changed_count=0,
        queue_status_changed_count=0,
        latest_generated_at=LATEST_GENERATED_AT,
        top_stable_market_slug="alpha",
        reason_codes=("stable_ready_candidates_present",),
        rows=(_row(),),
    )


def _db_row() -> PaperStrategyRecommendationRankStabilityDbRow:
    return strategy_recommendation_rank_stability_report_to_db_row(_report())


def _row_values(row: PaperStrategyRecommendationRankStabilityDbRow) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def test_insert_rank_stability_report_uses_parameterized_insert() -> None:
    connection = FakeConnection()
    report = _report()
    expected_row = _db_row()

    inserted = insert_strategy_recommendation_rank_stability_report(connection, report)

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO strategy_recommendation_rank_stability_reports (
            report_sha256,
            generated_at,
            config_version,
            stability_status,
            reason_codes_json,
            source_report_count,
            candidate_count,
            stable_count,
            watch_count,
            blocked_count,
            stable_ready_count,
            unstable_ready_count,
            selected_side_changed_count,
            queue_status_changed_count,
            latest_generated_at,
            top_stable_market_slug,
            rows_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)


def test_insert_rank_stability_report_with_result_observes_duplicate_insert() -> None:
    assert hasattr(
        rank_stability_store,
        "insert_strategy_recommendation_rank_stability_report_with_result",
    )
    report = _report()
    expected_row = _db_row()

    inserted = (
        rank_stability_store.insert_strategy_recommendation_rank_stability_report_with_result(
            FakeConnection(rowcount=1),
            report,
        )
    )
    duplicate = (
        rank_stability_store.insert_strategy_recommendation_rank_stability_report_with_result(
            FakeConnection(rowcount=0),
            report,
        )
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_load_rank_stability_reports_filters_by_config_status_and_limit() -> None:
    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_strategy_recommendation_rank_stability_reports(
        connection,
        config_version="strategy-recommendation-rank-stability-v0",
        stability_status="stable",
        limit=25,
        table_name="rank_stability_archive",
    )

    assert reports == (_report(),)
    assert connection.cursor_count == 1
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
            stability_status,
            reason_codes_json,
            source_report_count,
            candidate_count,
            stable_count,
            watch_count,
            blocked_count,
            stable_ready_count,
            unstable_ready_count,
            selected_side_changed_count,
            queue_status_changed_count,
            latest_generated_at,
            top_stable_market_slug,
            rows_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM rank_stability_archive
        WHERE config_version = %s AND stability_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("strategy-recommendation-rank-stability-v0", "stable", 25)


def test_load_rank_stability_reports_accepts_positional_rows() -> None:
    row = _db_row()
    connection = FakeConnection(rows=(_row_values(row),))

    reports = load_strategy_recommendation_rank_stability_reports(connection)

    assert reports == (_report(),)


def test_load_rank_stability_reports_accepts_dict_rows_without_mutation() -> None:
    row = _db_row()
    payload_before = deepcopy(row.payload_json)
    rows_before = deepcopy(row.rows_json)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    connection = FakeConnection(rows=(record,))

    reports = load_strategy_recommendation_rank_stability_reports(connection)

    assert reports == (_report(),)
    assert record["payload_json"] == payload_before
    assert record["rows_json"] == rows_before


def test_load_rank_stability_reports_accepts_namedtuple_like_rows() -> None:
    row = _db_row()
    Record = namedtuple("Record", SELECT_COLUMNS)
    connection = FakeConnection(rows=(Record(*_row_values(row)),))

    reports = load_strategy_recommendation_rank_stability_reports(connection)

    assert reports == (_report(),)


def test_load_rank_stability_reports_accepts_db_row_objects() -> None:
    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_strategy_recommendation_rank_stability_reports(connection)

    assert reports == (_report(),)


@pytest.mark.parametrize(
    "table_name",
    [
        "strategy_recommendation_rank_stability_reports; drop table users",
        "audit.strategy_recommendation_rank_stability_reports",
        "StrategyRecommendationRankStabilityReports",
        "_strategy_recommendation_rank_stability_reports",
        "strategy_recommendation_rank_stability_reports_",
        "a",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    table_name: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_strategy_recommendation_rank_stability_report(
            connection,
            _report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_accepts_simple_lowercase_table_names() -> None:
    connection = FakeConnection()

    insert_strategy_recommendation_rank_stability_report(
        connection,
        _report(),
        table_name="rank_stability_archive",
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert "INSERT INTO rank_stability_archive" in sql


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "rank_stability_archive",
        "rank_1_stability_2_archive",
    ],
)
def test_load_accepts_simple_lowercase_table_names(table_name: str) -> None:
    connection = FakeConnection()

    load_strategy_recommendation_rank_stability_reports(connection, table_name=table_name)

    sql, _params = connection.cursor_instance.calls[0]
    assert f"FROM {table_name}" in sql


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.audit.strategy_recommendation_rank_stability_reports"}, "table_name"),
        ({"table_name": "audit.strategy_recommendation_rank_stability_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "a"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " strategy-recommendation-rank-stability-v0"}, "config_version"),
        ({"stability_status": "pass"}, "stability_status"),
        ({"stability_status": True}, "stability_status"),
        ({"limit": 0}, "limit"),
        ({"limit": -1}, "limit"),
        ({"limit": True}, "limit"),
        ({"limit": "5"}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_before_cursor_creation(
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        load_strategy_recommendation_rank_stability_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions() -> None:
    assert DEFAULT_STRATEGY_RECOMMENDATION_RANK_STABILITY_REPORTS_TABLE == (
        "strategy_recommendation_rank_stability_reports"
    )

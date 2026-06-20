from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeTrendReport:
    generated_at: datetime
    name: str = "trend"


@dataclass(frozen=True)
class FakeSnapshotPair:
    input_position: int


@dataclass(frozen=True)
class FakeTrendDbRow:
    trend_sha256: str
    trend_schema_version: str
    source_window_sha256: str
    generated_at: datetime
    source_snapshot_count: int
    first_generated_at: datetime | None
    latest_generated_at: datetime | None
    latest_risk_status: str | None
    risk_pass_count: int
    risk_watch_count: int
    risk_blocked_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    duplicate_generated_at_count: int
    ready_notional_first: Decimal | None
    ready_notional_latest: Decimal | None
    ready_notional_delta: Decimal | None
    top_priority_score_first: Decimal | None
    top_priority_score_latest: Decimal | None
    top_priority_score_delta: Decimal | None
    average_priority_score_first: Decimal | None
    average_priority_score_latest: Decimal | None
    average_priority_score_delta: Decimal | None
    source_queue_count_first: int | None
    source_queue_count_latest: int | None
    source_queue_count_delta: int | None
    latest_reason_code_counts_json: dict[str, int]
    total_reason_code_counts_json: dict[str, int]
    repeated_reason_code_counts_json: dict[str, int]
    reason_code_rows_json: list[dict[str, object]]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class FakeTrendSourceDbRow:
    trend_sha256: str
    trend_ordinal: int
    source_input_position: int
    snapshot_sha256: str
    source_generated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class FakeTrendDbRows:
    trend_row: FakeTrendDbRow
    source_rows: tuple[FakeTrendSourceDbRow, ...]


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
    def __init__(self, cursor_rows: tuple[tuple[Any, ...], ...] = ()) -> None:
        self.cursor_rows = cursor_rows
        self.cursors: list[FakeCursor] = []
        self.commit_count = 0
        self.rollback_count = 0

    def cursor(self) -> FakeCursor:
        rows = self.cursor_rows[len(self.cursors)] if len(self.cursors) < len(self.cursor_rows) else ()
        cursor = FakeCursor(rows)
        self.cursors.append(cursor)
        return cursor

    @property
    def cursor_count(self) -> int:
        return len(self.cursors)

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab."
        "action_gated_strategy_recommendation_queue_decision_support_trend_db_row",
    )

    def to_db_rows(
        trend_report: FakeTrendReport,
        snapshot_pairs: tuple[FakeSnapshotPair, ...],
    ) -> FakeTrendDbRows:
        return FakeTrendDbRows(
            trend_row=_trend_row(
                trend_sha256="a" * 64,
                generated_at=trend_report.generated_at,
                source_snapshot_count=len(snapshot_pairs),
            ),
            source_rows=tuple(
                _source_row(
                    trend_sha256="a" * 64,
                    trend_ordinal=index,
                    source_input_position=pair.input_position,
                    snapshot_sha256=chr(ord("b") + index - 1) * 64,
                )
                for index, pair in enumerate(snapshot_pairs, start=1)
            ),
        )

    def from_db_rows(db_rows: FakeTrendDbRows) -> FakeTrendDbRows:
        return db_rows

    companion.PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow = (
        FakeTrendDbRow
    )
    companion.PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow = (
        FakeTrendSourceDbRow
    )
    companion.PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows = (
        FakeTrendDbRows
    )
    companion.paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows = (
        to_db_rows
    )
    companion.paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows = (
        from_db_rows
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab."
        "action_gated_strategy_recommendation_queue_decision_support_trend_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab."
        "action_gated_strategy_recommendation_queue_decision_support_trend_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab."
        "action_gated_strategy_recommendation_queue_decision_support_trend_store",
    )


def _trend_report() -> FakeTrendReport:
    return FakeTrendReport(generated_at=datetime(2026, 6, 20, 15, 0, tzinfo=UTC))


def _snapshot_pairs() -> tuple[FakeSnapshotPair, ...]:
    return (FakeSnapshotPair(input_position=2), FakeSnapshotPair(input_position=1))


def _trend_row(
    *,
    trend_sha256: str = "a" * 64,
    generated_at: datetime | None = None,
    source_snapshot_count: int = 2,
    latest_risk_status: str | None = "watch",
) -> FakeTrendDbRow:
    generated_at = generated_at or datetime(2026, 6, 20, 15, 0, tzinfo=UTC)
    first_generated_at = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
    latest_generated_at = datetime(2026, 6, 20, 13, 0, tzinfo=UTC)
    return FakeTrendDbRow(
        trend_sha256=trend_sha256,
        trend_schema_version="action-gated-queue-decision-support-trend-v1",
        source_window_sha256="f" * 64,
        generated_at=generated_at,
        source_snapshot_count=source_snapshot_count,
        first_generated_at=first_generated_at,
        latest_generated_at=latest_generated_at,
        latest_risk_status=latest_risk_status,
        risk_pass_count=1,
        risk_watch_count=1 if latest_risk_status == "watch" else 0,
        risk_blocked_count=0,
        consecutive_latest_watch_count=1 if latest_risk_status == "watch" else 0,
        consecutive_latest_blocked_count=0,
        duplicate_generated_at_count=0,
        ready_notional_first=Decimal("10.000000"),
        ready_notional_latest=Decimal("15.000000"),
        ready_notional_delta=Decimal("5.000000"),
        top_priority_score_first=Decimal("0.700000"),
        top_priority_score_latest=Decimal("0.900000"),
        top_priority_score_delta=Decimal("0.200000"),
        average_priority_score_first=Decimal("0.400000"),
        average_priority_score_latest=Decimal("0.600000"),
        average_priority_score_delta=Decimal("0.200000"),
        source_queue_count_first=2,
        source_queue_count_latest=3,
        source_queue_count_delta=1,
        latest_reason_code_counts_json={"portfolio_exposure_ok": 1},
        total_reason_code_counts_json={"portfolio_exposure_ok": 2},
        repeated_reason_code_counts_json={"portfolio_exposure_ok": 2},
        reason_code_rows_json=[
            {
                "reason_code": "portfolio_exposure_ok",
                "total_count": 2,
                "latest_count": 1,
                "snapshot_count": 2,
            },
        ],
    )


def _source_row(
    *,
    trend_sha256: str = "a" * 64,
    trend_ordinal: int = 1,
    source_input_position: int = 1,
    snapshot_sha256: str = "b" * 64,
    source_generated_at: datetime | None = None,
) -> FakeTrendSourceDbRow:
    return FakeTrendSourceDbRow(
        trend_sha256=trend_sha256,
        trend_ordinal=trend_ordinal,
        source_input_position=source_input_position,
        snapshot_sha256=snapshot_sha256,
        source_generated_at=source_generated_at
        or datetime(2026, 6, 20, 12, trend_ordinal, tzinfo=UTC),
    )


def test_insert_trend_db_rows_uses_parameterized_report_then_source_inserts(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    trend_report = _trend_report()

    inserted = (
        store_module.insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(
            connection,
            trend_report,
            _snapshot_pairs(),
        )
    )

    assert inserted == FakeTrendDbRows(
        trend_row=_trend_row(
            trend_sha256="a" * 64,
            generated_at=trend_report.generated_at,
            source_snapshot_count=2,
        ),
        source_rows=(
            _source_row(
                trend_sha256="a" * 64,
                trend_ordinal=1,
                source_input_position=2,
                snapshot_sha256="b" * 64,
            ),
            _source_row(
                trend_sha256="a" * 64,
                trend_ordinal=2,
                source_input_position=1,
                snapshot_sha256="c" * 64,
            ),
        ),
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursors[0].closed is True
    assert len(connection.cursors[0].calls) == 3

    report_sql, report_params = connection.cursors[0].calls[0]
    assert normalize_sql(report_sql) == normalize_sql(
        """
        INSERT INTO paper_action_gated_queue_decision_support_trend_reports (
            trend_sha256,
            trend_schema_version,
            source_window_sha256,
            generated_at,
            source_snapshot_count,
            first_generated_at,
            latest_generated_at,
            latest_risk_status,
            risk_pass_count,
            risk_watch_count,
            risk_blocked_count,
            consecutive_latest_watch_count,
            consecutive_latest_blocked_count,
            duplicate_generated_at_count,
            ready_notional_first,
            ready_notional_latest,
            ready_notional_delta,
            top_priority_score_first,
            top_priority_score_latest,
            top_priority_score_delta,
            average_priority_score_first,
            average_priority_score_latest,
            average_priority_score_delta,
            source_queue_count_first,
            source_queue_count_latest,
            source_queue_count_delta,
            latest_reason_code_counts,
            total_reason_code_counts,
            repeated_reason_code_counts,
            reason_code_rows,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (trend_sha256) DO NOTHING
        """,
    )
    assert report_sql.count("%s") == len(report_params)
    assert report_params == (
        "a" * 64,
        "action-gated-queue-decision-support-trend-v1",
        "f" * 64,
        trend_report.generated_at,
        2,
        datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
        datetime(2026, 6, 20, 13, 0, tzinfo=UTC),
        "watch",
        1,
        1,
        0,
        1,
        0,
        0,
        Decimal("10.000000"),
        Decimal("15.000000"),
        Decimal("5.000000"),
        Decimal("0.700000"),
        Decimal("0.900000"),
        Decimal("0.200000"),
        Decimal("0.400000"),
        Decimal("0.600000"),
        Decimal("0.200000"),
        2,
        3,
        1,
        {"portfolio_exposure_ok": 1},
        {"portfolio_exposure_ok": 2},
        {"portfolio_exposure_ok": 2},
        [
            {
                "reason_code": "portfolio_exposure_ok",
                "total_count": 2,
                "latest_count": 1,
                "snapshot_count": 2,
            },
        ],
        True,
        True,
        True,
    )

    source_sql, source_params = connection.cursors[0].calls[1]
    assert normalize_sql(source_sql) == normalize_sql(
        """
        INSERT INTO paper_action_gated_queue_decision_support_trend_sources (
            trend_sha256,
            trend_ordinal,
            source_input_position,
            snapshot_sha256,
            source_generated_at,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (trend_sha256, trend_ordinal) DO NOTHING
        """,
    )
    assert source_sql.count("%s") == len(source_params)
    assert source_params == (
        "a" * 64,
        1,
        2,
        "b" * 64,
        datetime(2026, 6, 20, 12, 1, tzinfo=UTC),
        True,
        True,
        True,
    )
    assert connection.cursors[0].calls[2][1] == (
        "a" * 64,
        2,
        1,
        "c" * 64,
        datetime(2026, 6, 20, 12, 2, tzinfo=UTC),
        True,
        True,
        True,
    )


def test_insert_accepts_schema_prefixed_table_names(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    store_module.insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(
        connection,
        _trend_report(),
        _snapshot_pairs(),
        reports_table_name="audit.trend_reports",
        sources_table_name="audit.trend_sources",
    )

    report_sql, _ = connection.cursors[0].calls[0]
    source_sql, _ = connection.cursors[0].calls[1]
    assert "INSERT INTO audit.trend_reports" in normalize_sql(report_sql)
    assert "INSERT INTO audit.trend_sources" in normalize_sql(source_sql)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        (
            {
                "reports_table_name": (
                    "paper_action_gated_queue_decision_support_trend_reports; drop table users"
                ),
            },
            "reports_table_name",
        ),
        ({"reports_table_name": "Audit.trend_reports"}, "reports_table_name"),
        ({"reports_table_name": "_trend_reports"}, "reports_table_name"),
        ({"reports_table_name": "trend_reports_"}, "reports_table_name"),
        ({"reports_table_name": "public.audit.trend_reports"}, "reports_table_name"),
        ({"reports_table_name": "a" * 64}, "reports_table_name"),
        ({"sources_table_name": "audit." + ("b" * 64)}, "sources_table_name"),
    ),
)
def test_insert_rejects_unsafe_table_names_before_cursor_creation(
    store_module: types.ModuleType,
    kwargs: dict[str, str],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_module.insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(
            connection,
            _trend_report(),
            _snapshot_pairs(),
            **kwargs,
        )

    assert connection.cursor_count == 0


def test_load_trend_db_rows_filters_limits_sorts_and_groups_sources_by_trend_hash(
    store_module: types.ModuleType,
) -> None:
    trend_a = _trend_row(trend_sha256="a" * 64, latest_risk_status="watch")
    trend_b = _trend_row(
        trend_sha256="b" * 64,
        generated_at=datetime(2026, 6, 20, 14, 0, tzinfo=UTC),
        latest_risk_status="pass",
    )
    source_a1 = _source_row(
        trend_sha256="a" * 64,
        trend_ordinal=1,
        source_input_position=2,
        snapshot_sha256="c" * 64,
    )
    source_a2 = _source_row(
        trend_sha256="a" * 64,
        trend_ordinal=2,
        source_input_position=1,
        snapshot_sha256="d" * 64,
    )
    source_b1 = _source_row(
        trend_sha256="b" * 64,
        trend_ordinal=1,
        source_input_position=3,
        snapshot_sha256="e" * 64,
    )
    connection = FakeConnection(
        cursor_rows=((trend_a, trend_b), (source_a1, source_a2, source_b1)),
    )

    loaded = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(
            connection,
            latest_risk_status="watch",
            limit=25,
            reports_table_name="audit.trend_reports",
            sources_table_name="audit.trend_sources",
        )
    )

    assert loaded == (
        FakeTrendDbRows(trend_row=trend_a, source_rows=(source_a1, source_a2)),
        FakeTrendDbRows(trend_row=trend_b, source_rows=(source_b1,)),
    )
    assert connection.cursor_count == 2
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert all(cursor.closed for cursor in connection.cursors)

    report_sql, report_params = connection.cursors[0].calls[0]
    assert normalize_sql(report_sql) == normalize_sql(
        """
        SELECT
            trend_sha256,
            trend_schema_version,
            source_window_sha256,
            generated_at,
            source_snapshot_count,
            first_generated_at,
            latest_generated_at,
            latest_risk_status,
            risk_pass_count,
            risk_watch_count,
            risk_blocked_count,
            consecutive_latest_watch_count,
            consecutive_latest_blocked_count,
            duplicate_generated_at_count,
            ready_notional_first,
            ready_notional_latest,
            ready_notional_delta,
            top_priority_score_first,
            top_priority_score_latest,
            top_priority_score_delta,
            average_priority_score_first,
            average_priority_score_latest,
            average_priority_score_delta,
            source_queue_count_first,
            source_queue_count_latest,
            source_queue_count_delta,
            latest_reason_code_counts,
            total_reason_code_counts,
            repeated_reason_code_counts,
            reason_code_rows,
            paper_only,
            report_only,
            readonly
        FROM audit.trend_reports
        WHERE latest_risk_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, trend_sha256 DESC
        LIMIT %s
        """,
    )
    assert report_params == ("watch", 25)

    source_sql, source_params = connection.cursors[1].calls[0]
    assert normalize_sql(source_sql) == normalize_sql(
        """
        SELECT
            trend_sha256,
            trend_ordinal,
            source_input_position,
            snapshot_sha256,
            source_generated_at,
            paper_only,
            report_only,
            readonly
        FROM audit.trend_sources
        WHERE trend_sha256 IN (%s, %s)
        ORDER BY trend_sha256 ASC, trend_ordinal ASC
        """,
    )
    assert source_params == ("a" * 64, "b" * 64)


def test_load_returns_empty_tuple_without_querying_sources_when_no_reports(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(cursor_rows=((),))

    loaded = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(
            connection,
        )
    )

    assert loaded == ()
    assert connection.cursor_count == 1


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"reports_table_name": "public.audit.trend_reports"}, "reports_table_name"),
        ({"sources_table_name": "_trend_sources"}, "sources_table_name"),
        ({"latest_risk_status": ""}, "latest_risk_status"),
        ({"latest_risk_status": " ready"}, "latest_risk_status"),
        ({"latest_risk_status": "ready"}, "latest_risk_status"),
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
        store_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0


def test_public_exports_include_defaults_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.__all__ == (
        "DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE",
        "DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE",
        "insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows",
        "load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows",
    )

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
class FakeHealthReport:
    generated_at: datetime
    config_version: str
    health_status: str


@dataclass(frozen=True)
class FakeHealthDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    health_status: str
    row_count: int
    recommend_count: int
    watch_count: int
    reject_count: int
    average_net_probability_edge: Decimal
    average_total_cost_per_share: Decimal
    top_recommendation_score: Decimal
    reason_code_counts_json: list[dict[str, Any]]
    max_average_cost_per_share: Decimal
    min_recommend_share: Decimal
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
    generated_at: datetime = datetime(2026, 6, 21, 10, 0, tzinfo=UTC),
    config_version: str = "paper-recommendation-health-v0",
    health_status: str = "watch",
    reason_code_counts_json: list[dict[str, Any]] | None = None,
) -> FakeHealthDbRow:
    return FakeHealthDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        health_status=health_status,
        row_count=4,
        recommend_count=2,
        watch_count=1,
        reject_count=1,
        average_net_probability_edge=Decimal("0.030000"),
        average_total_cost_per_share=Decimal("0.020000"),
        top_recommendation_score=Decimal("0.080000"),
        reason_code_counts_json=reason_code_counts_json
        or [{"reason_code": "positive_net_edge", "count": 2}],
        max_average_cost_per_share=Decimal("0.030000"),
        min_recommend_share=Decimal("0.500000"),
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "health_status": health_status,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType("polymarket_alpha_lab.paper_recommendation_health_db_row")

    def to_db_row(report: FakeHealthReport) -> FakeHealthDbRow:
        return FakeHealthDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            health_status=report.health_status,
            row_count=4,
            recommend_count=2,
            watch_count=1,
            reject_count=1,
            average_net_probability_edge=Decimal("0.030000"),
            average_total_cost_per_share=Decimal("0.020000"),
            top_recommendation_score=Decimal("0.080000"),
            reason_code_counts_json=[
                {"reason_code": "positive_net_edge", "count": 2},
                {"reason_code": "wide_spread", "count": 2},
            ],
            max_average_cost_per_share=Decimal("0.030000"),
            min_recommend_share=Decimal("0.500000"),
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "health_status": report.health_status,
            },
        )

    def from_db_row(row: FakeHealthDbRow) -> FakeHealthReport:
        return FakeHealthReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            health_status=row.health_status,
        )

    companion.PaperRecommendationHealthDbRow = FakeHealthDbRow
    companion.paper_recommendation_health_report_to_db_row = to_db_row
    companion.paper_recommendation_health_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_recommendation_health_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.paper_recommendation_health_store", None)
    return importlib.import_module("polymarket_alpha_lab.paper_recommendation_health_store")


def test_insert_paper_recommendation_health_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeHealthReport(
        generated_at=datetime(2026, 6, 21, 9, 30, tzinfo=UTC),
        config_version="paper-recommendation-health-v0",
        health_status="pass",
    )

    inserted = store_module.insert_paper_recommendation_health_report(connection, report)

    assert inserted == FakeHealthDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        health_status=report.health_status,
        row_count=4,
        recommend_count=2,
        watch_count=1,
        reject_count=1,
        average_net_probability_edge=Decimal("0.030000"),
        average_total_cost_per_share=Decimal("0.020000"),
        top_recommendation_score=Decimal("0.080000"),
        reason_code_counts_json=[
            {"reason_code": "positive_net_edge", "count": 2},
            {"reason_code": "wide_spread", "count": 2},
        ],
        max_average_cost_per_share=Decimal("0.030000"),
        min_recommend_share=Decimal("0.500000"),
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "health_status": report.health_status,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_recommendation_health_reports (
            report_sha256,
            generated_at,
            config_version,
            health_status,
            row_count,
            recommend_count,
            watch_count,
            reject_count,
            average_net_probability_edge,
            average_total_cost_per_share,
            top_recommendation_score,
            reason_code_counts,
            max_average_cost_per_share,
            min_recommend_share,
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
        report.config_version,
        "pass",
        4,
        2,
        1,
        1,
        Decimal("0.030000"),
        Decimal("0.020000"),
        Decimal("0.080000"),
        [
            {"reason_code": "positive_net_edge", "count": 2},
            {"reason_code": "wide_spread", "count": 2},
        ],
        Decimal("0.030000"),
        Decimal("0.500000"),
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "health_status": report.health_status,
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
        store_module.insert_paper_recommendation_health_report(
            connection,
            FakeHealthReport(
                generated_at=datetime(2026, 6, 21, 9, 30, tzinfo=UTC),
                config_version="paper-recommendation-health-v0",
                health_status="pass",
            ),
            table_name="paper_recommendation_health_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_paper_recommendation_health_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(health_status="blocked")
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_recommendation_health_reports(
        connection,
        config_version="paper-recommendation-health-v0",
        health_status="blocked",
        limit=25,
        table_name="health_archive",
    )

    assert reports == (
        FakeHealthReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            health_status=row.health_status,
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
            health_status,
            row_count,
            recommend_count,
            watch_count,
            reject_count,
            average_net_probability_edge,
            average_total_cost_per_share,
            top_recommendation_score,
            reason_code_counts,
            max_average_cost_per_share,
            min_recommend_share,
            payload,
            paper_only,
            report_only,
            readonly
        FROM health_archive
        WHERE config_version = %s AND health_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-recommendation-health-v0", "blocked", 25)


def test_load_paper_recommendation_health_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 21, 11, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-recommendation-health-v0",
                "pass",
                0,
                0,
                0,
                0,
                Decimal("0.000000"),
                Decimal("0.000000"),
                Decimal("0.000000"),
                [],
                Decimal("0.030000"),
                Decimal("0.500000"),
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-recommendation-health-v0",
                    "health_status": "pass",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_recommendation_health_reports(connection)

    assert reports == (
        FakeHealthReport(
            generated_at=generated_at,
            config_version="paper-recommendation-health-v0",
            health_status="pass",
        ),
    )


def test_load_paper_recommendation_health_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "config_version": "paper-recommendation-health-v0",
                "health_status": "watch",
                "row_count": 4,
                "recommend_count": 2,
                "watch_count": 1,
                "reject_count": 1,
                "average_net_probability_edge": Decimal("0.030000"),
                "average_total_cost_per_share": Decimal("0.020000"),
                "top_recommendation_score": Decimal("0.080000"),
                "reason_code_counts": [{"reason_code": "positive_net_edge", "count": 2}],
                "max_average_cost_per_share": Decimal("0.030000"),
                "min_recommend_share": Decimal("0.500000"),
                "payload": {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-recommendation-health-v0",
                    "health_status": "watch",
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = store_module.load_paper_recommendation_health_reports(connection)

    assert reports == (
        FakeHealthReport(
            generated_at=generated_at,
            config_version="paper-recommendation-health-v0",
            health_status="watch",
        ),
    )


def test_load_paper_recommendation_health_reports_accepts_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 21, 13, 0, tzinfo=UTC)
    record_type = namedtuple(
        "HealthRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "health_status",
            "row_count",
            "recommend_count",
            "watch_count",
            "reject_count",
            "average_net_probability_edge",
            "average_total_cost_per_share",
            "top_recommendation_score",
            "reason_code_counts",
            "max_average_cost_per_share",
            "min_recommend_share",
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
                "paper-recommendation-health-v0",
                "blocked",
                0,
                0,
                0,
                0,
                Decimal("0.000000"),
                Decimal("0.000000"),
                Decimal("0.000000"),
                [],
                Decimal("0.030000"),
                Decimal("0.500000"),
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-recommendation-health-v0",
                    "health_status": "blocked",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_recommendation_health_reports(connection)

    assert reports == (
        FakeHealthReport(
            generated_at=generated_at,
            config_version="paper-recommendation-health-v0",
            health_status="blocked",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_recommendation_health_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"health_status": "selected"}, "health_status"),
        ({"health_status": True}, "health_status"),
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
        store_module.load_paper_recommendation_health_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0

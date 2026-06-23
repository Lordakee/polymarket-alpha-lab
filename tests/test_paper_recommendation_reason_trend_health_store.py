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
class FakeReasonTrendHealthReport:
    generated_at: datetime
    config_version: str
    health_status: str


@dataclass(frozen=True)
class FakeReasonTrendHealthDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    health_status: str
    source_report_count: int
    reason_code_count: int
    blocked_status_count: int
    blocked_status_share: Decimal | None
    reject_status_count: int
    reject_status_share: Decimal | None
    new_reason_code_count: int
    transition_count: int
    persistent_reason_codes_json: list[str]
    reason_codes_json: list[str]
    max_blocked_status_share: Decimal
    max_reject_status_share: Decimal
    max_new_reason_code_count: int
    max_transition_count: int
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
    generated_at: datetime = datetime(2026, 6, 22, 18, 0, tzinfo=UTC),
    config_version: str = "paper-recommendation-reason-trend-health-v0",
    health_status: str = "watch",
) -> FakeReasonTrendHealthDbRow:
    return FakeReasonTrendHealthDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        health_status=health_status,
        source_report_count=3,
        reason_code_count=2,
        blocked_status_count=1,
        blocked_status_share=Decimal("0.250000"),
        reject_status_count=0,
        reject_status_share=Decimal("0.000000"),
        new_reason_code_count=2,
        transition_count=1,
        persistent_reason_codes_json=["alpha"],
        reason_codes_json=["alpha", "beta"],
        max_blocked_status_share=Decimal("0.500000"),
        max_reject_status_share=Decimal("0.500000"),
        max_new_reason_code_count=1,
        max_transition_count=1,
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "health_status": health_status,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_recommendation_reason_trend_health_db_row",
    )

    def to_db_row(report: FakeReasonTrendHealthReport) -> FakeReasonTrendHealthDbRow:
        return fake_db_row(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            health_status=report.health_status,
        )

    def from_db_row(row: FakeReasonTrendHealthDbRow) -> FakeReasonTrendHealthReport:
        return FakeReasonTrendHealthReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            health_status=row.health_status,
        )

    companion.PaperRecommendationReasonTrendHealthDbRow = FakeReasonTrendHealthDbRow
    companion.paper_recommendation_reason_trend_health_report_to_db_row = to_db_row
    companion.paper_recommendation_reason_trend_health_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_recommendation_reason_trend_health_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_recommendation_reason_trend_health_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_recommendation_reason_trend_health_store",
    )


def test_insert_reason_trend_health_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReasonTrendHealthReport(
        generated_at=datetime(2026, 6, 22, 18, 30, tzinfo=UTC),
        config_version="paper-recommendation-reason-trend-health-v0",
        health_status="watch",
    )

    inserted = store_module.insert_paper_recommendation_reason_trend_health_report(
        connection,
        report,
    )

    assert inserted == fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        health_status=report.health_status,
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_recommendation_reason_trend_health_reports (
            report_sha256,
            generated_at,
            config_version,
            health_status,
            source_report_count,
            reason_code_count,
            blocked_status_count,
            blocked_status_share,
            reject_status_count,
            reject_status_share,
            new_reason_code_count,
            transition_count,
            persistent_reason_codes,
            reason_codes,
            max_blocked_status_share,
            max_reject_status_share,
            max_new_reason_code_count,
            max_transition_count,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        "watch",
        3,
        2,
        1,
        Decimal("0.250000"),
        0,
        Decimal("0.000000"),
        2,
        1,
        ["alpha"],
        ["alpha", "beta"],
        Decimal("0.500000"),
        Decimal("0.500000"),
        1,
        1,
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
        store_module.insert_paper_recommendation_reason_trend_health_report(
            connection,
            FakeReasonTrendHealthReport(
                generated_at=datetime(2026, 6, 22, 18, 30, tzinfo=UTC),
                config_version="paper-recommendation-reason-trend-health-v0",
                health_status="pass",
            ),
            table_name="paper_recommendation_reason_trend_health_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_reason_trend_health_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(health_status="blocked")
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_recommendation_reason_trend_health_reports(
        connection,
        config_version="paper-recommendation-reason-trend-health-v0",
        health_status="blocked",
        limit=25,
        table_name="reason_trend_health_archive",
    )

    assert reports == (
        FakeReasonTrendHealthReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            health_status=row.health_status,
        ),
    )
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            health_status,
            source_report_count,
            reason_code_count,
            blocked_status_count,
            blocked_status_share,
            reject_status_count,
            reject_status_share,
            new_reason_code_count,
            transition_count,
            persistent_reason_codes,
            reason_codes,
            max_blocked_status_share,
            max_reject_status_share,
            max_new_reason_code_count,
            max_transition_count,
            payload,
            paper_only,
            report_only,
            readonly
        FROM reason_trend_health_archive
        WHERE config_version = %s AND health_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-recommendation-reason-trend-health-v0", "blocked", 25)


def test_load_reason_trend_health_reports_accepts_positional_dict_and_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 22, 18, 0, tzinfo=UTC)
    positional_connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-recommendation-reason-trend-health-v0",
                "pass",
                3,
                2,
                0,
                Decimal("0.000000"),
                0,
                Decimal("0.000000"),
                0,
                0,
                [],
                ["alpha"],
                Decimal("0.500000"),
                Decimal("0.500000"),
                0,
                0,
                {"generated_at": generated_at.isoformat(), "health_status": "pass"},
                True,
                True,
                True,
            ),
        ),
    )
    dict_connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "config_version": "paper-recommendation-reason-trend-health-v0",
                "health_status": "watch",
                "source_report_count": 3,
                "reason_code_count": 2,
                "blocked_status_count": 1,
                "blocked_status_share": Decimal("0.250000"),
                "reject_status_count": 0,
                "reject_status_share": Decimal("0.000000"),
                "new_reason_code_count": 2,
                "transition_count": 1,
                "persistent_reason_codes": ["alpha"],
                "reason_codes": ["alpha", "beta"],
                "max_blocked_status_share": Decimal("0.500000"),
                "max_reject_status_share": Decimal("0.500000"),
                "max_new_reason_code_count": 1,
                "max_transition_count": 1,
                "payload": {"generated_at": generated_at.isoformat(), "health_status": "watch"},
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )
    record_type = namedtuple(
        "ReasonTrendHealthRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "health_status",
            "source_report_count",
            "reason_code_count",
            "blocked_status_count",
            "blocked_status_share",
            "reject_status_count",
            "reject_status_share",
            "new_reason_code_count",
            "transition_count",
            "persistent_reason_codes",
            "reason_codes",
            "max_blocked_status_share",
            "max_reject_status_share",
            "max_new_reason_code_count",
            "max_transition_count",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    namedtuple_connection = FakeConnection(
        rows=(
            record_type(
                "e" * 64,
                generated_at,
                "paper-recommendation-reason-trend-health-v0",
                "blocked",
                0,
                0,
                0,
                None,
                0,
                None,
                0,
                0,
                [],
                [],
                Decimal("0.500000"),
                Decimal("0.500000"),
                0,
                0,
                {"generated_at": generated_at.isoformat(), "health_status": "blocked"},
                True,
                True,
                True,
            ),
        ),
    )

    assert store_module.load_paper_recommendation_reason_trend_health_reports(
        positional_connection,
    ) == (
        FakeReasonTrendHealthReport(
            generated_at=generated_at,
            config_version="paper-recommendation-reason-trend-health-v0",
            health_status="pass",
        ),
    )
    assert store_module.load_paper_recommendation_reason_trend_health_reports(
        dict_connection,
    ) == (
        FakeReasonTrendHealthReport(
            generated_at=generated_at,
            config_version="paper-recommendation-reason-trend-health-v0",
            health_status="watch",
        ),
    )
    assert store_module.load_paper_recommendation_reason_trend_health_reports(
        namedtuple_connection,
    ) == (
        FakeReasonTrendHealthReport(
            generated_at=generated_at,
            config_version="paper-recommendation-reason-trend-health-v0",
            health_status="blocked",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_recommendation_reason_trend_health_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"health_status": "stable"}, "health_status"),
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
        store_module.load_paper_recommendation_reason_trend_health_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []

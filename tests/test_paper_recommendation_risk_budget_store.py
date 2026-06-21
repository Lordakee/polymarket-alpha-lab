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
class FakeRiskBudgetReport:
    generated_at: datetime
    config_version: str
    status: str


@dataclass(frozen=True)
class FakeRiskBudgetDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    status: str
    reason_codes_json: list[str]
    total_suggested_notional: Decimal
    remaining_total_notional: Decimal | None
    total_notional_utilization: Decimal | None
    largest_single_recommendation_share: Decimal | None
    selected_count: int
    blocked_count: int
    nav_notional: Decimal | None
    max_total_utilization: Decimal
    max_single_recommendation_share: Decimal
    min_remaining_notional: Decimal
    max_selected_count: int
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
    generated_at: datetime = datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
    config_version: str = "paper-recommendation-risk-budget-v0",
    status: str = "watch",
    reason_codes_json: list[str] | None = None,
) -> FakeRiskBudgetDbRow:
    return FakeRiskBudgetDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        status=status,
        reason_codes_json=reason_codes_json or ["near_total_utilization_cap"],
        total_suggested_notional=Decimal("200.000000"),
        remaining_total_notional=Decimal("300.000000"),
        total_notional_utilization=Decimal("0.400000"),
        largest_single_recommendation_share=Decimal("0.125000"),
        selected_count=3,
        blocked_count=1,
        nav_notional=Decimal("500.000000"),
        max_total_utilization=Decimal("0.500000"),
        max_single_recommendation_share=Decimal("0.150000"),
        min_remaining_notional=Decimal("250.000000"),
        max_selected_count=4,
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "status": status,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_recommendation_risk_budget_db_row",
    )

    def to_db_row(report: FakeRiskBudgetReport) -> FakeRiskBudgetDbRow:
        return FakeRiskBudgetDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            status=report.status,
            reason_codes_json=["risk_budget_passed"],
            total_suggested_notional=Decimal("125.000000"),
            remaining_total_notional=Decimal("875.000000"),
            total_notional_utilization=Decimal("0.125000"),
            largest_single_recommendation_share=Decimal("0.075000"),
            selected_count=2,
            blocked_count=0,
            nav_notional=Decimal("1000.000000"),
            max_total_utilization=Decimal("0.250000"),
            max_single_recommendation_share=Decimal("0.100000"),
            min_remaining_notional=Decimal("500.000000"),
            max_selected_count=5,
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "status": report.status,
            },
        )

    def from_db_row(row: FakeRiskBudgetDbRow) -> FakeRiskBudgetReport:
        return FakeRiskBudgetReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            status=row.status,
        )

    companion.PaperRecommendationRiskBudgetDbRow = FakeRiskBudgetDbRow
    companion.paper_recommendation_risk_budget_report_to_db_row = to_db_row
    companion.paper_recommendation_risk_budget_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_recommendation_risk_budget_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_recommendation_risk_budget_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_recommendation_risk_budget_store",
    )


def test_insert_paper_recommendation_risk_budget_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeRiskBudgetReport(
        generated_at=datetime(2026, 6, 20, 9, 30, tzinfo=UTC),
        config_version="paper-recommendation-risk-budget-v0",
        status="pass",
    )

    inserted = store_module.insert_paper_recommendation_risk_budget_report(
        connection,
        report,
    )

    assert inserted == FakeRiskBudgetDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        reason_codes_json=["risk_budget_passed"],
        total_suggested_notional=Decimal("125.000000"),
        remaining_total_notional=Decimal("875.000000"),
        total_notional_utilization=Decimal("0.125000"),
        largest_single_recommendation_share=Decimal("0.075000"),
        selected_count=2,
        blocked_count=0,
        nav_notional=Decimal("1000.000000"),
        max_total_utilization=Decimal("0.250000"),
        max_single_recommendation_share=Decimal("0.100000"),
        min_remaining_notional=Decimal("500.000000"),
        max_selected_count=5,
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "status": report.status,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_recommendation_risk_budget_reports (
            report_sha256,
            generated_at,
            config_version,
            status,
            reason_codes,
            total_suggested_notional,
            remaining_total_notional,
            total_notional_utilization,
            largest_single_recommendation_share,
            selected_count,
            blocked_count,
            nav_notional,
            max_total_utilization,
            max_single_recommendation_share,
            min_remaining_notional,
            max_selected_count,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        "pass",
        ["risk_budget_passed"],
        Decimal("125.000000"),
        Decimal("875.000000"),
        Decimal("0.125000"),
        Decimal("0.075000"),
        2,
        0,
        Decimal("1000.000000"),
        Decimal("0.250000"),
        Decimal("0.100000"),
        Decimal("500.000000"),
        5,
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "status": report.status,
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
        store_module.insert_paper_recommendation_risk_budget_report(
            connection,
            FakeRiskBudgetReport(
                generated_at=datetime(2026, 6, 20, 9, 30, tzinfo=UTC),
                config_version="paper-recommendation-risk-budget-v0",
                status="pass",
            ),
            table_name="paper_recommendation_risk_budget_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_paper_recommendation_risk_budget_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(status="blocked")
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_recommendation_risk_budget_reports(
        connection,
        config_version="paper-recommendation-risk-budget-v0",
        status="blocked",
        limit=25,
        table_name="risk_budget_archive",
    )

    assert reports == (
        FakeRiskBudgetReport(
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
            reason_codes,
            total_suggested_notional,
            remaining_total_notional,
            total_notional_utilization,
            largest_single_recommendation_share,
            selected_count,
            blocked_count,
            nav_notional,
            max_total_utilization,
            max_single_recommendation_share,
            min_remaining_notional,
            max_selected_count,
            payload,
            paper_only,
            report_only,
            readonly
        FROM risk_budget_archive
        WHERE config_version = %s AND status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-recommendation-risk-budget-v0", "blocked", 25)


def test_load_paper_recommendation_risk_budget_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-recommendation-risk-budget-v0",
                "pass",
                ["risk_budget_passed"],
                Decimal("0.000000"),
                None,
                None,
                None,
                0,
                0,
                None,
                Decimal("0.250000"),
                Decimal("0.100000"),
                Decimal("500.000000"),
                5,
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-recommendation-risk-budget-v0",
                    "status": "pass",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_recommendation_risk_budget_reports(connection)

    assert reports == (
        FakeRiskBudgetReport(
            generated_at=generated_at,
            config_version="paper-recommendation-risk-budget-v0",
            status="pass",
        ),
    )


def test_load_paper_recommendation_risk_budget_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "config_version": "paper-recommendation-risk-budget-v0",
                "status": "watch",
                "reason_codes": ["near_max_selected_count"],
                "total_suggested_notional": Decimal("300.000000"),
                "remaining_total_notional": Decimal("200.000000"),
                "total_notional_utilization": Decimal("0.600000"),
                "largest_single_recommendation_share": Decimal("0.200000"),
                "selected_count": 4,
                "blocked_count": 1,
                "nav_notional": Decimal("500.000000"),
                "max_total_utilization": Decimal("0.750000"),
                "max_single_recommendation_share": Decimal("0.250000"),
                "min_remaining_notional": Decimal("100.000000"),
                "max_selected_count": 4,
                "payload": {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-recommendation-risk-budget-v0",
                    "status": "watch",
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = store_module.load_paper_recommendation_risk_budget_reports(connection)

    assert reports == (
        FakeRiskBudgetReport(
            generated_at=generated_at,
            config_version="paper-recommendation-risk-budget-v0",
            status="watch",
        ),
    )


def test_load_paper_recommendation_risk_budget_reports_accepts_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 13, 0, tzinfo=UTC)
    record_type = namedtuple(
        "RiskBudgetRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "status",
            "reason_codes",
            "total_suggested_notional",
            "remaining_total_notional",
            "total_notional_utilization",
            "largest_single_recommendation_share",
            "selected_count",
            "blocked_count",
            "nav_notional",
            "max_total_utilization",
            "max_single_recommendation_share",
            "min_remaining_notional",
            "max_selected_count",
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
                "paper-recommendation-risk-budget-v0",
                "blocked",
                ["max_selected_count_exceeded"],
                Decimal("800.000000"),
                Decimal("0.000000"),
                Decimal("0.800000"),
                Decimal("0.300000"),
                8,
                2,
                Decimal("1000.000000"),
                Decimal("0.500000"),
                Decimal("0.200000"),
                Decimal("50.000000"),
                5,
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-recommendation-risk-budget-v0",
                    "status": "blocked",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_recommendation_risk_budget_reports(connection)

    assert reports == (
        FakeRiskBudgetReport(
            generated_at=generated_at,
            config_version="paper-recommendation-risk-budget-v0",
            status="blocked",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_recommendation_risk_budget_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"status": "selected"}, "status"),
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
        store_module.load_paper_recommendation_risk_budget_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0

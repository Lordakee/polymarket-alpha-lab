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
class FakePriorityReport:
    generated_at: datetime
    source_report_count: int


@dataclass(frozen=True)
class FakeRiskReport:
    config_version: str
    status: str
    recommended_next_step: str


@dataclass(frozen=True)
class FakeActionGatedQueueDecisionSupportDbRow:
    snapshot_sha256: str
    generated_at: datetime
    priority_source_report_count: int
    priority_research_ready_count: int
    priority_watch_count: int
    priority_blocked_count: int
    priority_total_ready_notional: Decimal
    top_research_priority_score: Decimal
    average_research_priority_score: Decimal
    risk_config_version: str
    risk_status: str
    risk_recommended_next_step: str
    risk_source_queue_count: int
    risk_candidate_count: int
    risk_ready_count: int
    risk_total_ready_notional: Decimal
    risk_largest_queue_ready_notional: Decimal
    risk_reason_codes_json: list[str]
    priority_payload_json: dict[str, Any]
    risk_payload_json: dict[str, Any]
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


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab."
        "action_gated_strategy_recommendation_queue_decision_support_db_row",
    )

    def to_db_row(
        priority_report: FakePriorityReport,
        risk_report: FakeRiskReport,
    ) -> FakeActionGatedQueueDecisionSupportDbRow:
        return FakeActionGatedQueueDecisionSupportDbRow(
            snapshot_sha256="a" * 64,
            generated_at=priority_report.generated_at,
            priority_source_report_count=priority_report.source_report_count,
            priority_research_ready_count=2,
            priority_watch_count=1,
            priority_blocked_count=1,
            priority_total_ready_notional=Decimal("42.000000"),
            top_research_priority_score=Decimal("0.900000"),
            average_research_priority_score=Decimal("0.700000"),
            risk_config_version=risk_report.config_version,
            risk_status=risk_report.status,
            risk_recommended_next_step=risk_report.recommended_next_step,
            risk_source_queue_count=4,
            risk_candidate_count=3,
            risk_ready_count=2,
            risk_total_ready_notional=Decimal("30.000000"),
            risk_largest_queue_ready_notional=Decimal("20.000000"),
            risk_reason_codes_json=["queue_risk_passed"],
            priority_payload_json={
                "generated_at": priority_report.generated_at.isoformat(),
                "source_report_count": priority_report.source_report_count,
            },
            risk_payload_json={
                "config_version": risk_report.config_version,
                "status": risk_report.status,
                "recommended_next_step": risk_report.recommended_next_step,
            },
        )

    def from_db_row(
        row: FakeActionGatedQueueDecisionSupportDbRow,
    ) -> tuple[FakePriorityReport, FakeRiskReport]:
        return (
            FakePriorityReport(
                generated_at=row.generated_at,
                source_report_count=row.priority_source_report_count,
            ),
            FakeRiskReport(
                config_version=row.risk_config_version,
                status=row.risk_status,
                recommended_next_step=row.risk_recommended_next_step,
            ),
        )

    companion.PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow = (
        FakeActionGatedQueueDecisionSupportDbRow
    )
    companion.paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row = (
        to_db_row
    )
    companion.paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row = (
        from_db_row
    )
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab."
        "action_gated_strategy_recommendation_queue_decision_support_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab."
        "action_gated_strategy_recommendation_queue_decision_support_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab."
        "action_gated_strategy_recommendation_queue_decision_support_store",
    )


def _priority_report() -> FakePriorityReport:
    return FakePriorityReport(
        generated_at=datetime(2026, 6, 20, 12, 30, tzinfo=UTC),
        source_report_count=4,
    )


def _risk_report() -> FakeRiskReport:
    return FakeRiskReport(
        config_version="risk-v1",
        status="pass",
        recommended_next_step="allocate_paper_research_queue",
    )


def _db_row(
    *,
    snapshot_sha256: str = "b" * 64,
    generated_at: datetime | None = None,
    priority_source_report_count: int = 4,
    risk_config_version: str = "risk-v1",
    risk_status: str = "pass",
    risk_recommended_next_step: str = "allocate_paper_research_queue",
) -> FakeActionGatedQueueDecisionSupportDbRow:
    generated_at = generated_at or datetime(2026, 6, 20, 13, 0, tzinfo=UTC)
    return FakeActionGatedQueueDecisionSupportDbRow(
        snapshot_sha256=snapshot_sha256,
        generated_at=generated_at,
        priority_source_report_count=priority_source_report_count,
        priority_research_ready_count=2,
        priority_watch_count=1,
        priority_blocked_count=1,
        priority_total_ready_notional=Decimal("42.000000"),
        top_research_priority_score=Decimal("0.900000"),
        average_research_priority_score=Decimal("0.700000"),
        risk_config_version=risk_config_version,
        risk_status=risk_status,
        risk_recommended_next_step=risk_recommended_next_step,
        risk_source_queue_count=4,
        risk_candidate_count=3,
        risk_ready_count=2,
        risk_total_ready_notional=Decimal("30.000000"),
        risk_largest_queue_ready_notional=Decimal("20.000000"),
        risk_reason_codes_json=["queue_risk_passed"],
        priority_payload_json={"source_report_count": priority_source_report_count},
        risk_payload_json={
            "config_version": risk_config_version,
            "status": risk_status,
            "recommended_next_step": risk_recommended_next_step,
        },
    )


def test_insert_decision_support_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    priority_report = _priority_report()
    risk_report = _risk_report()

    inserted = (
        store_module.insert_paper_action_gated_strategy_recommendation_queue_decision_support_report(
            connection,
            priority_report,
            risk_report,
        )
    )

    assert inserted == FakeActionGatedQueueDecisionSupportDbRow(
        snapshot_sha256="a" * 64,
        generated_at=priority_report.generated_at,
        priority_source_report_count=4,
        priority_research_ready_count=2,
        priority_watch_count=1,
        priority_blocked_count=1,
        priority_total_ready_notional=Decimal("42.000000"),
        top_research_priority_score=Decimal("0.900000"),
        average_research_priority_score=Decimal("0.700000"),
        risk_config_version="risk-v1",
        risk_status="pass",
        risk_recommended_next_step="allocate_paper_research_queue",
        risk_source_queue_count=4,
        risk_candidate_count=3,
        risk_ready_count=2,
        risk_total_ready_notional=Decimal("30.000000"),
        risk_largest_queue_ready_notional=Decimal("20.000000"),
        risk_reason_codes_json=["queue_risk_passed"],
        priority_payload_json={
            "generated_at": priority_report.generated_at.isoformat(),
            "source_report_count": 4,
        },
        risk_payload_json={
            "config_version": "risk-v1",
            "status": "pass",
            "recommended_next_step": "allocate_paper_research_queue",
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_action_gated_strategy_recommendation_queue_decision_support_reports (
            snapshot_sha256,
            generated_at,
            priority_source_report_count,
            priority_research_ready_count,
            priority_watch_count,
            priority_blocked_count,
            priority_total_ready_notional,
            top_research_priority_score,
            average_research_priority_score,
            risk_config_version,
            risk_status,
            risk_recommended_next_step,
            risk_source_queue_count,
            risk_candidate_count,
            risk_ready_count,
            risk_total_ready_notional,
            risk_largest_queue_ready_notional,
            risk_reason_codes,
            priority_payload,
            risk_payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (snapshot_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        priority_report.generated_at,
        4,
        2,
        1,
        1,
        Decimal("42.000000"),
        Decimal("0.900000"),
        Decimal("0.700000"),
        "risk-v1",
        "pass",
        "allocate_paper_research_queue",
        4,
        3,
        2,
        Decimal("30.000000"),
        Decimal("20.000000"),
        ["queue_risk_passed"],
        {
            "generated_at": priority_report.generated_at.isoformat(),
            "source_report_count": 4,
        },
        {
            "config_version": "risk-v1",
            "status": "pass",
            "recommended_next_step": "allocate_paper_research_queue",
        },
        True,
        True,
        True,
    )


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_action_gated_strategy_recommendation_queue_decision_support_reports; drop table users",
        "ActionGatedQueueDecisionSupportReports",
        "audit.ActionGatedQueueDecisionSupportReports",
        "_action_gated_queue_decision_support_reports",
        "audit._action_gated_queue_decision_support_reports",
        "action_gated_queue_decision_support_reports_",
        "public.audit.action_gated_queue_decision_support_reports",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    store_module: types.ModuleType,
    table_name: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_action_gated_strategy_recommendation_queue_decision_support_report(
            connection,
            _priority_report(),
            _risk_report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_decision_support_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = _db_row(
        risk_status="watch",
        risk_recommended_next_step="throttle_paper_research_queue",
    )
    connection = FakeConnection(rows=(row,))

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_reports(
            connection,
            risk_status="watch",
            risk_config_version="risk-v1",
            limit=25,
            table_name="audit.action_gated_queue_decision_support_reports",
        )
    )

    assert reports == (
        (
            FakePriorityReport(
                generated_at=row.generated_at,
                source_report_count=4,
            ),
            FakeRiskReport(
                config_version="risk-v1",
                status="watch",
                recommended_next_step="throttle_paper_research_queue",
            ),
        ),
    )
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            snapshot_sha256,
            generated_at,
            priority_source_report_count,
            priority_research_ready_count,
            priority_watch_count,
            priority_blocked_count,
            priority_total_ready_notional,
            top_research_priority_score,
            average_research_priority_score,
            risk_config_version,
            risk_status,
            risk_recommended_next_step,
            risk_source_queue_count,
            risk_candidate_count,
            risk_ready_count,
            risk_total_ready_notional,
            risk_largest_queue_ready_notional,
            risk_reason_codes,
            priority_payload,
            risk_payload,
            paper_only,
            report_only,
            readonly
        FROM audit.action_gated_queue_decision_support_reports
        WHERE risk_status = %s AND risk_config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, snapshot_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("watch", "risk-v1", 25)


def test_load_decision_support_reports_accepts_dataclass_rows(
    store_module: types.ModuleType,
) -> None:
    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_reports(
            connection,
        )
    )

    assert reports == (
        (
            FakePriorityReport(generated_at=row.generated_at, source_report_count=4),
            FakeRiskReport(
                config_version="risk-v1",
                status="pass",
                recommended_next_step="allocate_paper_research_queue",
            ),
        ),
    )


def test_load_decision_support_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 14, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                4,
                2,
                1,
                1,
                Decimal("42.000000"),
                Decimal("0.900000"),
                Decimal("0.700000"),
                "risk-v1",
                "pass",
                "allocate_paper_research_queue",
                4,
                3,
                2,
                Decimal("30.000000"),
                Decimal("20.000000"),
                ["queue_risk_passed"],
                {"source_report_count": 4},
                {"status": "pass"},
                True,
                True,
                True,
            ),
        ),
    )

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_reports(
            connection,
        )
    )

    assert reports == (
        (
            FakePriorityReport(generated_at=generated_at, source_report_count=4),
            FakeRiskReport(
                config_version="risk-v1",
                status="pass",
                recommended_next_step="allocate_paper_research_queue",
            ),
        ),
    )


def test_load_decision_support_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 15, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "snapshot_sha256": "d" * 64,
                "generated_at": generated_at,
                "priority_source_report_count": 1,
                "priority_research_ready_count": 0,
                "priority_watch_count": 0,
                "priority_blocked_count": 1,
                "priority_total_ready_notional": Decimal("0.000000"),
                "top_research_priority_score": Decimal("0.000000"),
                "average_research_priority_score": Decimal("0.000000"),
                "risk_config_version": "risk-v2",
                "risk_status": "blocked",
                "risk_recommended_next_step": "block_paper_research_queue",
                "risk_source_queue_count": 1,
                "risk_candidate_count": 1,
                "risk_ready_count": 0,
                "risk_total_ready_notional": Decimal("0.000000"),
                "risk_largest_queue_ready_notional": Decimal("0.000000"),
                "risk_reason_codes": ["source_queue_blocked"],
                "priority_payload": {"source_report_count": 1},
                "risk_payload": {"status": "blocked"},
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_reports(
            connection,
        )
    )

    assert reports == (
        (
            FakePriorityReport(generated_at=generated_at, source_report_count=1),
            FakeRiskReport(
                config_version="risk-v2",
                status="blocked",
                recommended_next_step="block_paper_research_queue",
            ),
        ),
    )


def test_load_decision_support_reports_accepts_namedtuple_like_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 16, 0, tzinfo=UTC)
    Record = namedtuple(
        "Record",
        [
            "snapshot_sha256",
            "generated_at",
            "priority_source_report_count",
            "priority_research_ready_count",
            "priority_watch_count",
            "priority_blocked_count",
            "priority_total_ready_notional",
            "top_research_priority_score",
            "average_research_priority_score",
            "risk_config_version",
            "risk_status",
            "risk_recommended_next_step",
            "risk_source_queue_count",
            "risk_candidate_count",
            "risk_ready_count",
            "risk_total_ready_notional",
            "risk_largest_queue_ready_notional",
            "risk_reason_codes",
            "priority_payload",
            "risk_payload",
            "paper_only",
            "report_only",
            "readonly",
        ],
    )
    connection = FakeConnection(
        rows=(
            Record(
                snapshot_sha256="e" * 64,
                generated_at=generated_at,
                priority_source_report_count=1,
                priority_research_ready_count=0,
                priority_watch_count=1,
                priority_blocked_count=0,
                priority_total_ready_notional=Decimal("0.000000"),
                top_research_priority_score=Decimal("0.100000"),
                average_research_priority_score=Decimal("0.100000"),
                risk_config_version="risk-v1",
                risk_status="watch",
                risk_recommended_next_step="throttle_paper_research_queue",
                risk_source_queue_count=1,
                risk_candidate_count=1,
                risk_ready_count=0,
                risk_total_ready_notional=Decimal("0.000000"),
                risk_largest_queue_ready_notional=Decimal("0.000000"),
                risk_reason_codes=["source_queue_watch"],
                priority_payload={"source_report_count": 1},
                risk_payload={"status": "watch"},
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
        ),
    )

    reports = (
        store_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_reports(
            connection,
        )
    )

    assert reports == (
        (
            FakePriorityReport(generated_at=generated_at, source_report_count=1),
            FakeRiskReport(
                config_version="risk-v1",
                status="watch",
                recommended_next_step="throttle_paper_research_queue",
            ),
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        (
            {"table_name": "public.audit.action_gated_queue_decision_support_reports"},
            "table_name",
        ),
        ({"table_name": "_"}, "table_name"),
        ({"risk_status": ""}, "risk_status"),
        ({"risk_status": " ready"}, "risk_status"),
        ({"risk_status": "ready"}, "risk_status"),
        ({"risk_config_version": ""}, "risk_config_version"),
        ({"risk_config_version": " risk-v1"}, "risk_config_version"),
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
        store_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.__all__ == (
        "DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_DECISION_SUPPORT_TABLE",
        "insert_paper_action_gated_strategy_recommendation_queue_decision_support_report",
        "load_paper_action_gated_strategy_recommendation_queue_decision_support_reports",
    )

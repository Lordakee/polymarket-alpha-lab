from __future__ import annotations

import importlib
import inspect
import sys
import types
from collections import namedtuple
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
)


DEFAULT_TABLE = "paper_strategy_candidate_research_queue_reports"


@dataclass(frozen=True)
class FakeStrategyCandidateResearchQueueDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_config_version: str
    action_status: str
    recommended_next_step: str
    research_status: str
    candidate_count: int
    research_ready_count: int
    watch_count: int
    blocked_count: int
    selected_count: int
    skipped_count: int
    not_selected_count: int
    total_ready_notional: Decimal
    total_selected_notional: Decimal
    total_suggested_notional: Decimal
    top_research_priority_score: Decimal
    average_research_ready_score: Decimal
    source_reason_code_counts_json: dict[str, int]
    primary_reason_code_counts_json: dict[str, int]
    reason_codes_json: list[str]
    rows_json: list[dict[str, Any]]
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


@dataclass(frozen=True)
class StoreFixture:
    module: types.ModuleType
    conversion_calls: list[PaperStrategyCandidateResearchQueueReport]


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def _reason_count(reason_code: str, count: int) -> PaperRecommendationCycleActionGateReasonCodeCount:
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def _watch_report() -> PaperStrategyCandidateResearchQueueReport:
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=datetime(2026, 6, 20, 12, 30, tzinfo=UTC),
        config_version="strategy-candidate-research-queue-v0",
        source_config_version="action-gated-strategy-recommendation-queue-v0",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        source_reason_code_counts=(_reason_count("cycle_review_watch", 1),),
        research_status="watch",
        candidate_count=0,
        research_ready_count=0,
        watch_count=0,
        blocked_count=0,
        selected_count=0,
        skipped_count=0,
        not_selected_count=0,
        total_ready_notional=Decimal("0.000000"),
        total_selected_notional=Decimal("0.000000"),
        total_suggested_notional=Decimal("0.000000"),
        top_research_priority_score=Decimal("0.000000"),
        average_research_ready_score=Decimal("0.000000"),
        primary_reason_code_counts=(),
        rows=(),
        reason_codes=("source_action_status_watch",),
    )


def _db_row(report: PaperStrategyCandidateResearchQueueReport) -> FakeStrategyCandidateResearchQueueDbRow:
    return FakeStrategyCandidateResearchQueueDbRow(
        report_sha256="f" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_config_version=report.source_config_version,
        action_status=report.action_status,
        recommended_next_step=report.recommended_next_step,
        research_status=report.research_status,
        candidate_count=report.candidate_count,
        research_ready_count=report.research_ready_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        selected_count=report.selected_count,
        skipped_count=report.skipped_count,
        not_selected_count=report.not_selected_count,
        total_ready_notional=report.total_ready_notional,
        total_selected_notional=report.total_selected_notional,
        total_suggested_notional=report.total_suggested_notional,
        top_research_priority_score=report.top_research_priority_score,
        average_research_ready_score=report.average_research_ready_score,
        source_reason_code_counts_json={
            item.reason_code: item.count for item in report.source_reason_code_counts
        },
        primary_reason_code_counts_json=dict(report.primary_reason_code_counts),
        reason_codes_json=list(report.reason_codes),
        rows_json=[],
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "source_config_version": report.source_config_version,
            "action_status": report.action_status,
            "recommended_next_step": report.recommended_next_step,
            "research_status": report.research_status,
            "candidate_count": report.candidate_count,
            "reason_codes": list(report.reason_codes),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _copy_report_as_subclass() -> PaperStrategyCandidateResearchQueueReport:
    class ReportSubclass(PaperStrategyCandidateResearchQueueReport):
        pass

    report = _watch_report()
    return ReportSubclass(**{field.name: getattr(report, field.name) for field in fields(report)})


def _unsafe_report(flag_name: str) -> PaperStrategyCandidateResearchQueueReport:
    report = _watch_report()
    object.__setattr__(report, flag_name, False)
    return report


def _config_class() -> type[Any]:
    config_module = importlib.import_module(
        "polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config",
    )
    return config_module.SupabaseStrategyCandidateResearchQueueConfig


@pytest.fixture()
def store_fixture(monkeypatch: pytest.MonkeyPatch) -> StoreFixture:
    conversion_calls: list[PaperStrategyCandidateResearchQueueReport] = []
    companion = types.ModuleType(
        "polymarket_alpha_lab.strategy_candidate_research_queue_db_row",
    )

    def to_db_row(
        report: PaperStrategyCandidateResearchQueueReport,
    ) -> FakeStrategyCandidateResearchQueueDbRow:
        conversion_calls.append(report)
        if type(report) is not PaperStrategyCandidateResearchQueueReport:
            raise ValueError(
                "report must be a PaperStrategyCandidateResearchQueueReport",
            )
        for flag_name in ("paper_only", "report_only", "readonly"):
            if getattr(report, flag_name, None) is not True:
                raise ValueError(f"report must be {flag_name}")
        return _db_row(report)

    def from_db_row(
        row: FakeStrategyCandidateResearchQueueDbRow,
    ) -> PaperStrategyCandidateResearchQueueReport:
        for flag_name in ("paper_only", "report_only", "readonly"):
            if getattr(row, flag_name, None) is not True:
                raise ValueError(f"DB row must be {flag_name}")
        return _watch_report().__class__(
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_config_version=row.source_config_version,
            action_status=row.action_status,
            recommended_next_step=row.recommended_next_step,
            source_reason_code_counts=tuple(
                _reason_count(reason_code, count)
                for reason_code, count in row.source_reason_code_counts_json.items()
            ),
            research_status=row.research_status,
            candidate_count=row.candidate_count,
            research_ready_count=row.research_ready_count,
            watch_count=row.watch_count,
            blocked_count=row.blocked_count,
            selected_count=row.selected_count,
            skipped_count=row.skipped_count,
            not_selected_count=row.not_selected_count,
            total_ready_notional=row.total_ready_notional,
            total_selected_notional=row.total_selected_notional,
            total_suggested_notional=row.total_suggested_notional,
            top_research_priority_score=row.top_research_priority_score,
            average_research_ready_score=row.average_research_ready_score,
            primary_reason_code_counts=tuple(
                row.primary_reason_code_counts_json.items()
            ),
            rows=tuple(),
            reason_codes=tuple(row.reason_codes_json),
            paper_only=row.paper_only,
            report_only=row.report_only,
            readonly=row.readonly,
        )

    companion.PaperStrategyCandidateResearchQueueDbRow = (
        FakeStrategyCandidateResearchQueueDbRow
    )
    companion.paper_strategy_candidate_research_queue_report_to_db_row = to_db_row
    companion.paper_strategy_candidate_research_queue_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.strategy_candidate_research_queue_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.strategy_candidate_research_queue_store",
        None,
    )
    module = importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_research_queue_store",
    )
    return StoreFixture(module=module, conversion_calls=conversion_calls)


def test_insert_strategy_candidate_research_queue_report_uses_codec_and_parameterized_insert(
    store_fixture: StoreFixture,
) -> None:
    connection = FakeConnection()
    report = _watch_report()
    expected = _db_row(report)

    inserted = store_fixture.module.insert_paper_strategy_candidate_research_queue_report(
        connection,
        report,
    )

    assert inserted == expected
    assert store_fixture.conversion_calls == [report]
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_strategy_candidate_research_queue_reports (
            report_sha256,
            generated_at,
            config_version,
            source_config_version,
            action_status,
            recommended_next_step,
            research_status,
            candidate_count,
            research_ready_count,
            watch_count,
            blocked_count,
            selected_count,
            skipped_count,
            not_selected_count,
            total_ready_notional,
            total_selected_notional,
            total_suggested_notional,
            top_research_priority_score,
            average_research_ready_score,
            source_reason_code_counts,
            primary_reason_code_counts,
            reason_codes,
            rows,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        expected.report_sha256,
        expected.generated_at,
        expected.config_version,
        expected.source_config_version,
        expected.action_status,
        expected.recommended_next_step,
        expected.research_status,
        expected.candidate_count,
        expected.research_ready_count,
        expected.watch_count,
        expected.blocked_count,
        expected.selected_count,
        expected.skipped_count,
        expected.not_selected_count,
        expected.total_ready_notional,
        expected.total_selected_notional,
        expected.total_suggested_notional,
        expected.top_research_priority_score,
        expected.average_research_ready_score,
        expected.source_reason_code_counts_json,
        expected.primary_reason_code_counts_json,
        expected.reason_codes_json,
        expected.rows_json,
        expected.payload_json,
        True,
        True,
        True,
    )


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_strategy_candidate_research_queue_reports; drop table users",
        "StrategyCandidateResearchQueueReports",
        "audit.StrategyCandidateResearchQueueReports",
        "_strategy_candidate_research_queue_reports",
        "strategy_candidate_research_queue_reports_",
        "public.audit.strategy_candidate_research_queue_reports",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    store_fixture: StoreFixture,
    table_name: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_fixture.module.insert_paper_strategy_candidate_research_queue_report(
            connection,
            _watch_report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    ("bad_report", "message"),
    [
        (_copy_report_as_subclass(), "PaperStrategyCandidateResearchQueueReport"),
        (_unsafe_report("paper_only"), "paper_only"),
        (_unsafe_report("report_only"), "report_only"),
        (_unsafe_report("readonly"), "readonly"),
    ],
)
def test_insert_validates_exact_report_type_and_hard_flags_before_cursor_creation(
    store_fixture: StoreFixture,
    bad_report: PaperStrategyCandidateResearchQueueReport,
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_fixture.module.insert_paper_strategy_candidate_research_queue_report(
            connection,
            bad_report,
        )

    assert store_fixture.conversion_calls == [bad_report]
    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_strategy_candidate_research_queue_reports_filters_and_limits_with_params(
    store_fixture: StoreFixture,
) -> None:
    row = _db_row(_watch_report())
    connection = FakeConnection(rows=(row,))

    reports = store_fixture.module.load_paper_strategy_candidate_research_queue_reports(
        connection,
        source_config_version="action-gated-strategy-recommendation-queue-v0",
        action_status="watch",
        research_status="watch",
        limit=25,
        table_name="audit.strategy_candidate_research_queue_reports",
    )

    assert reports == (_watch_report(),)
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
            research_status,
            candidate_count,
            research_ready_count,
            watch_count,
            blocked_count,
            selected_count,
            skipped_count,
            not_selected_count,
            total_ready_notional,
            total_selected_notional,
            total_suggested_notional,
            top_research_priority_score,
            average_research_ready_score,
            source_reason_code_counts,
            primary_reason_code_counts,
            reason_codes,
            rows,
            payload,
            paper_only,
            report_only,
            readonly
        FROM audit.strategy_candidate_research_queue_reports
        WHERE source_config_version = %s AND action_status = %s AND research_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "action-gated-strategy-recommendation-queue-v0",
        "watch",
        "watch",
        25,
    )


def test_load_strategy_candidate_research_queue_reports_filters_by_research_status_only(
    store_fixture: StoreFixture,
) -> None:
    connection = FakeConnection()

    store_fixture.module.load_paper_strategy_candidate_research_queue_reports(
        connection,
        research_status="blocked",
    )

    sql, params = connection.cursor_instance.calls[0]
    assert "WHERE research_status = %s" in normalize_sql(sql)
    assert params == ("blocked",)


def test_load_strategy_candidate_research_queue_reports_accepts_positional_rows(
    store_fixture: StoreFixture,
) -> None:
    row = _db_row(_watch_report())
    connection = FakeConnection(
        rows=(
            (
                row.report_sha256,
                row.generated_at,
                row.config_version,
                row.source_config_version,
                row.action_status,
                row.recommended_next_step,
                row.research_status,
                row.candidate_count,
                row.research_ready_count,
                row.watch_count,
                row.blocked_count,
                row.selected_count,
                row.skipped_count,
                row.not_selected_count,
                row.total_ready_notional,
                row.total_selected_notional,
                row.total_suggested_notional,
                row.top_research_priority_score,
                row.average_research_ready_score,
                row.source_reason_code_counts_json,
                row.primary_reason_code_counts_json,
                row.reason_codes_json,
                row.rows_json,
                row.payload_json,
                row.paper_only,
                row.report_only,
                row.readonly,
            ),
        ),
    )

    reports = store_fixture.module.load_paper_strategy_candidate_research_queue_reports(
        connection,
    )

    assert reports == (_watch_report(),)


def test_load_strategy_candidate_research_queue_reports_accepts_dict_rows(
    store_fixture: StoreFixture,
) -> None:
    row = _db_row(_watch_report())
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": row.report_sha256,
                "generated_at": row.generated_at,
                "config_version": row.config_version,
                "source_config_version": row.source_config_version,
                "action_status": row.action_status,
                "recommended_next_step": row.recommended_next_step,
                "research_status": row.research_status,
                "candidate_count": row.candidate_count,
                "research_ready_count": row.research_ready_count,
                "watch_count": row.watch_count,
                "blocked_count": row.blocked_count,
                "selected_count": row.selected_count,
                "skipped_count": row.skipped_count,
                "not_selected_count": row.not_selected_count,
                "total_ready_notional": row.total_ready_notional,
                "total_selected_notional": row.total_selected_notional,
                "total_suggested_notional": row.total_suggested_notional,
                "top_research_priority_score": row.top_research_priority_score,
                "average_research_ready_score": row.average_research_ready_score,
                "source_reason_code_counts": row.source_reason_code_counts_json,
                "primary_reason_code_counts": row.primary_reason_code_counts_json,
                "reason_codes": row.reason_codes_json,
                "rows": row.rows_json,
                "payload": row.payload_json,
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            },
        ),
    )

    reports = store_fixture.module.load_paper_strategy_candidate_research_queue_reports(
        connection,
    )

    assert reports == (_watch_report(),)


def test_load_strategy_candidate_research_queue_reports_accepts_namedtuple_like_rows(
    store_fixture: StoreFixture,
) -> None:
    row = _db_row(_watch_report())
    Record = namedtuple(
        "Record",
        [
            "report_sha256",
            "generated_at",
            "config_version",
            "source_config_version",
            "action_status",
            "recommended_next_step",
            "research_status",
            "candidate_count",
            "research_ready_count",
            "watch_count",
            "blocked_count",
            "selected_count",
            "skipped_count",
            "not_selected_count",
            "total_ready_notional",
            "total_selected_notional",
            "total_suggested_notional",
            "top_research_priority_score",
            "average_research_ready_score",
            "source_reason_code_counts",
            "primary_reason_code_counts",
            "reason_codes",
            "rows",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        ],
    )
    connection = FakeConnection(
        rows=(
            Record(
                report_sha256=row.report_sha256,
                generated_at=row.generated_at,
                config_version=row.config_version,
                source_config_version=row.source_config_version,
                action_status=row.action_status,
                recommended_next_step=row.recommended_next_step,
                research_status=row.research_status,
                candidate_count=row.candidate_count,
                research_ready_count=row.research_ready_count,
                watch_count=row.watch_count,
                blocked_count=row.blocked_count,
                selected_count=row.selected_count,
                skipped_count=row.skipped_count,
                not_selected_count=row.not_selected_count,
                total_ready_notional=row.total_ready_notional,
                total_selected_notional=row.total_selected_notional,
                total_suggested_notional=row.total_suggested_notional,
                top_research_priority_score=row.top_research_priority_score,
                average_research_ready_score=row.average_research_ready_score,
                source_reason_code_counts=row.source_reason_code_counts_json,
                primary_reason_code_counts=row.primary_reason_code_counts_json,
                reason_codes=row.reason_codes_json,
                rows=row.rows_json,
                payload=row.payload_json,
                paper_only=row.paper_only,
                report_only=row.report_only,
                readonly=row.readonly,
            ),
        ),
    )

    reports = store_fixture.module.load_paper_strategy_candidate_research_queue_reports(
        connection,
    )

    assert reports == (_watch_report(),)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.audit.strategy_candidate_research_queue_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"source_config_version": ""}, "source_config_version"),
        (
            {"source_config_version": " action-gated-strategy-recommendation-queue-v0"},
            "source_config_version",
        ),
        ({"action_status": ""}, "action_status"),
        ({"action_status": " watch"}, "action_status"),
        ({"research_status": ""}, "research_status"),
        ({"research_status": " blocked"}, "research_status"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_rejects_invalid_strategy_candidate_research_queue_query_inputs_before_cursor_creation(
    store_fixture: StoreFixture,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_fixture.module.load_paper_strategy_candidate_research_queue_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_closes_cursor_when_db_row_hard_flags_fail(
    store_fixture: StoreFixture,
) -> None:
    row = _db_row(_watch_report())
    bad_row = FakeStrategyCandidateResearchQueueDbRow(
        **{
            **row.__dict__,
            "readonly": False,
        },
    )
    connection = FakeConnection(rows=(bad_row,))

    with pytest.raises(ValueError, match="readonly"):
        store_fixture.module.load_paper_strategy_candidate_research_queue_reports(
            connection,
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True


def test_disabled_config_returns_no_strategy_candidate_research_queue_sink(
    store_fixture: StoreFixture,
) -> None:
    Config = _config_class()
    config = Config(enabled=False, dsn=None, table_name=DEFAULT_TABLE)
    calls: list[tuple[str, PaperStrategyCandidateResearchQueueReport, str]] = []

    def report_sink(
        *,
        dsn: str,
        report: PaperStrategyCandidateResearchQueueReport,
        table_name: str,
    ) -> object:
        calls.append((dsn, report, table_name))
        return report

    sink = store_fixture.module.paper_strategy_candidate_research_queue_report_sink_from_config(
        config,
        report_sink=report_sink,
    )

    assert sink is None
    assert calls == []
    assert store_fixture.conversion_calls == []


def test_enabled_config_sink_writes_converted_db_row_with_configured_dsn_and_table(
    store_fixture: StoreFixture,
) -> None:
    Config = _config_class()
    secret_dsn = "postgresql://research:topsecret@localhost:54322/postgres"
    config = Config(
        enabled=True,
        dsn=secret_dsn,
        table_name="audit.paper_strategy_candidate_research_queue_reports",
    )
    calls: list[tuple[str, PaperStrategyCandidateResearchQueueReport, str]] = []

    def report_sink(
        *,
        dsn: str,
        report: PaperStrategyCandidateResearchQueueReport,
        table_name: str,
    ) -> object:
        calls.append((dsn, report, table_name))
        return {"stored": report.config_version}

    sink = store_fixture.module.paper_strategy_candidate_research_queue_report_sink_from_config(
        config,
        report_sink=report_sink,
    )
    assert callable(sink)
    report = _watch_report()

    result = sink(report)

    assert result == {"stored": report.config_version}
    assert store_fixture.conversion_calls == []
    assert calls == [
        (
            secret_dsn,
            report,
            "audit.paper_strategy_candidate_research_queue_reports",
        ),
    ]


def test_enabled_config_sink_redacts_dsn_from_errors_and_repr(
    store_fixture: StoreFixture,
) -> None:
    Config = _config_class()
    secret_dsn = "postgresql://research:topsecret@localhost:54322/postgres"
    config = Config(enabled=True, dsn=secret_dsn, table_name=DEFAULT_TABLE)

    def report_sink(
        *,
        dsn: str,
        report: PaperStrategyCandidateResearchQueueReport,
        table_name: str,
    ) -> object:
        raise RuntimeError(f"insert failed for {dsn} into {table_name}")

    sink = store_fixture.module.paper_strategy_candidate_research_queue_report_sink_from_config(
        config,
        report_sink=report_sink,
    )

    assert callable(sink)
    assert secret_dsn not in repr(config)
    assert "topsecret" not in repr(config)
    assert secret_dsn not in repr(sink)
    assert "topsecret" not in repr(sink)
    with pytest.raises(RuntimeError) as exc_info:
        sink(_watch_report())

    message = str(exc_info.value)
    assert "insert failed" in message
    assert "postgresql://" not in message
    assert "topsecret" not in message
    assert "localhost:54322" not in message


def test_store_surface_does_not_require_live_trading_auth_wallet_or_order_objects(
    store_fixture: StoreFixture,
) -> None:
    insert_signature = inspect.signature(
        store_fixture.module.insert_paper_strategy_candidate_research_queue_report,
    )
    sink_signature = inspect.signature(
        store_fixture.module.paper_strategy_candidate_research_queue_report_sink_from_config,
    )
    forbidden_names = ("auth", "wallet", "order", "live_trading", "client")

    for signature in (insert_signature, sink_signature):
        parameter_names = set(signature.parameters)
        for name in forbidden_names:
            assert name not in parameter_names

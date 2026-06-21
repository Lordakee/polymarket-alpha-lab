from __future__ import annotations

import ast
import importlib
import inspect
import sys
import types
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)
from polymarket_alpha_lab.strategy_candidate_research_queue_db_row import (
    paper_strategy_candidate_research_queue_report_to_db_row,
)


def _load_read_module() -> Any:
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read",
        )
    except ModuleNotFoundError as exc:
        if exc.name == "polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read":
            pytest.fail("strategy_candidate_research_queue_psycopg_read module missing")
        raise


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


def _source_reason_count(
    reason_code: str,
    count: int,
) -> PaperRecommendationCycleActionGateReasonCodeCount:
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def _research_row(
    *,
    research_rank: int,
    queue_rank: int,
    market_slug: str,
    question: str,
    source_action: str,
    decision: str,
    queue_status: str,
    research_status: str,
    recommendation_score: Decimal,
    readiness_score: Decimal,
    suggested_notional: Decimal,
    selected_position_notional: Decimal,
    primary_reason_code: str,
    reason_codes: tuple[str, ...],
    evidence_gap_codes: tuple[str, ...] = (),
    selected_side: str = "yes",
) -> PaperStrategyCandidateResearchQueueRow:
    return PaperStrategyCandidateResearchQueueRow(
        research_rank=research_rank,
        queue_rank=queue_rank,
        market_slug=market_slug,
        question=question,
        selected_side=selected_side,
        scoring_side="yes",
        source_action=source_action,
        decision=decision,
        queue_status=queue_status,
        research_status=research_status,
        research_bucket="macro_policy",
        assessment_status=research_status,
        source_status="active",
        readiness_status="pass" if research_status == "ready" else research_status,
        recommendation_score=recommendation_score,
        readiness_score=readiness_score,
        screening_score=Decimal("0.080000"),
        net_edge_per_share=Decimal("0.080000"),
        total_cost_per_share=Decimal("0.000000"),
        confidence=Decimal("0.900000"),
        spread=Decimal("0.010000"),
        resolution_risk=Decimal("0.020000"),
        suggested_notional=suggested_notional,
        selected_position_notional=selected_position_notional,
        primary_reason_code=primary_reason_code,
        research_priority_score=(
            (recommendation_score + readiness_score) / Decimal("2")
        ).quantize(Decimal("0.000001")),
        evidence_gap_codes=evidence_gap_codes,
        reason_codes=reason_codes,
        explanation=f"{source_action} because {primary_reason_code}",
    )


def _ready_report() -> PaperStrategyCandidateResearchQueueReport:
    rows = (
        _research_row(
            research_rank=1,
            queue_rank=1,
            market_slug="alpha-ready",
            question="Will alpha resolve yes?",
            source_action="recommend",
            decision="selected",
            queue_status="ready",
            research_status="ready",
            recommendation_score=Decimal("0.700000"),
            readiness_score=Decimal("0.900000"),
            suggested_notional=Decimal("12.000000"),
            selected_position_notional=Decimal("12.000000"),
            primary_reason_code="recommendation_ready",
            reason_codes=("recommendation_ready",),
        ),
        _research_row(
            research_rank=2,
            queue_rank=2,
            market_slug="beta-watch",
            question="Will beta resolve yes?",
            source_action="watch",
            decision="skipped",
            queue_status="watch",
            research_status="watch",
            recommendation_score=Decimal("0.300000"),
            readiness_score=Decimal("0.600000"),
            suggested_notional=Decimal("8.000000"),
            selected_position_notional=Decimal("0.000000"),
            primary_reason_code="low_net_edge",
            evidence_gap_codes=("low_net_edge",),
            reason_codes=("low_net_edge",),
        ),
    )
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=datetime(2026, 6, 20, 12, 30, tzinfo=UTC),
        config_version="strategy-candidate-research-queue-v0",
        source_config_version="action-gated-strategy-recommendation-queue-v0",
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
        source_reason_code_counts=(_source_reason_count("cycle_review_pass", 1),),
        research_status="ready",
        candidate_count=2,
        research_ready_count=1,
        watch_count=1,
        blocked_count=0,
        selected_count=1,
        skipped_count=1,
        not_selected_count=0,
        total_ready_notional=Decimal("12.000000"),
        total_selected_notional=Decimal("12.000000"),
        total_suggested_notional=Decimal("12.000000"),
        top_research_priority_score=Decimal("0.800000"),
        average_research_ready_score=Decimal("0.800000"),
        primary_reason_code_counts=(
            ("low_net_edge", 1),
            ("recommendation_ready", 1),
        ),
        rows=rows,
        reason_codes=("candidate_research_queue_ready",),
    )


def _watch_report() -> PaperStrategyCandidateResearchQueueReport:
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=datetime(2026, 6, 20, 17, 0, tzinfo=UTC),
        config_version="strategy-candidate-research-queue-v0",
        source_config_version="action-gated-strategy-recommendation-queue-v0",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        source_reason_code_counts=(_source_reason_count("cycle_review_watch", 1),),
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


def _db_record(report: PaperStrategyCandidateResearchQueueReport) -> dict[str, Any]:
    row = paper_strategy_candidate_research_queue_report_to_db_row(report)
    return {
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
    }


def test_load_strategy_candidate_research_queue_reports_uses_bounded_read_only_select() -> None:
    module = _load_read_module()
    report = _ready_report()
    connection = FakeConnection(rows=(_db_record(report),))

    loaded = module.load_paper_strategy_candidate_research_queue_reports(
        connection,
        options=module.PaperStrategyCandidateResearchQueueReadOptions(
            source_config_version="action-gated-strategy-recommendation-queue-v0",
            action_status="research_ready",
            research_status="ready",
            limit=25,
            table_name="audit.strategy_candidate_research_queue_reports",
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
        WHERE source_config_version = %s
            AND action_status = %s
            AND research_status = %s
        ORDER BY generated_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "action-gated-strategy-recommendation-queue-v0",
        "research_ready",
        "ready",
        25,
    )


def test_strategy_candidate_research_queue_psycopg_read_module_stays_select_only() -> None:
    module = _load_read_module()
    source = inspect.getsource(module)
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
        "polymarket_alpha_lab.strategy_candidate_research_queue_store",
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
    module = _load_read_module()
    report = _watch_report()
    connection = FakeConnection(rows=(_db_record(report),))
    connect_calls: list[tuple[str, dict[str, Any]]] = []

    def connect(dsn: str, **kwargs: Any) -> FakeConnection:
        connect_calls.append((dsn, kwargs))
        return connection

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=connect))

    loaded = module.load_paper_strategy_candidate_research_queue_reports_with_psycopg(
        "postgresql://readonly.example/research_queue",
        options=module.PaperStrategyCandidateResearchQueueReadOptions(limit=10),
    )

    assert loaded == (report,)
    assert connect_calls == [
        ("postgresql://readonly.example/research_queue", {"autocommit": True}),
    ]
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.closed is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        (
            {"table_name": "public.audit.strategy_candidate_research_queue_reports"},
            "table_name",
        ),
        ({"table_name": "StrategyCandidateResearchQueueReports"}, "table_name"),
        ({"source_config_version": ""}, "source_config_version"),
        (
            {"source_config_version": " action-gated-strategy-recommendation-queue-v0"},
            "source_config_version",
        ),
        ({"action_status": "ready"}, "action_status"),
        ({"research_status": "research_ready"}, "research_status"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
        ({"limit": 501}, "limit"),
    ),
)
def test_read_options_reject_invalid_query_inputs(
    kwargs: dict[str, Any],
    message: str,
) -> None:
    module = _load_read_module()

    with pytest.raises(ValueError, match=message):
        module.PaperStrategyCandidateResearchQueueReadOptions(**kwargs)


def test_read_options_are_frozen() -> None:
    module = _load_read_module()
    options = module.PaperStrategyCandidateResearchQueueReadOptions()

    with pytest.raises(FrozenInstanceError):
        options.limit = 25


def test_load_rejects_invalid_options_type() -> None:
    module = _load_read_module()

    with pytest.raises(ValueError, match="PaperStrategyCandidateResearchQueueReadOptions"):
        module.load_paper_strategy_candidate_research_queue_reports(
            FakeConnection(),
            options=object(),
        )


def test_load_rejects_row_with_disabled_hard_flags_and_closes_cursor() -> None:
    module = _load_read_module()
    record = _db_record(_watch_report()) | {"paper_only": False}
    connection = FakeConnection(rows=(record,))

    with pytest.raises(ValueError, match="paper_only"):
        module.load_paper_strategy_candidate_research_queue_reports(connection)

    assert connection.cursor_instance.closed is True
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_rejects_payload_json_floats_and_closes_cursor() -> None:
    module = _load_read_module()
    record = _db_record(_watch_report())
    record["payload"] = dict(record["payload"]) | {"total_ready_notional": 0.0}
    connection = FakeConnection(rows=(record,))

    with pytest.raises(ValueError, match="float|floats"):
        module.load_paper_strategy_candidate_research_queue_reports(connection)

    assert connection.cursor_instance.closed is True
    assert connection.commit_count == 0
    assert connection.rollback_count == 0

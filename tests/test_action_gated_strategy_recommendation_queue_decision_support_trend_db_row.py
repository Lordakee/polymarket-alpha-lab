from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_db_row import (
    paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend import (
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
    build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_db_row import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION,
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows,
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
    paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows,
    paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueuePriorityRow,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskReport,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
SECOND_GENERATED_AT = datetime(2026, 6, 20, 12, 30, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 20, 8, 0, tzinfo=UTC)

NEXT_STEP_BY_ACTION_STATUS = {
    "research_ready": "review_candidate_research_queue",
    "watch": "await_fresh_cycle_evidence",
    "blocked": "repair_cycle_evidence",
}
RESEARCH_PRIORITY_BY_ACTION_STATUS = {
    "research_ready": "research_review",
    "watch": "await_fresh_context",
    "blocked": "repair_evidence",
}
ACTION_STATUS_SCORE = {
    "research_ready": Decimal("3.000000"),
    "watch": Decimal("1.000000"),
    "blocked": Decimal("0.000000"),
}
NEXT_STEP_BY_RISK_STATUS = {
    "pass": "allocate_paper_research_queue",
    "watch": "throttle_paper_research_queue",
    "blocked": "block_paper_research_queue",
}


class TrendReportSubclass(
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
):
    pass


class TrendDbRowSubclass(
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
):
    pass


class TrendSourceDbRowSubclass(
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
):
    pass


class TrendDbRowsSubclass(
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows,
):
    pass


def _priority_row(
    *,
    priority_rank: int = 1,
    generated_at: datetime = BASE_AT,
    action_status: str = "research_ready",
    candidate_count: int = 1,
    ready_count: int = 1,
    watch_count: int = 0,
    blocked_count: int = 0,
    total_ready_notional: Decimal = Decimal("10.000000"),
    top_queue_score: Decimal = Decimal("0.400000"),
    average_ready_score: Decimal = Decimal("0.300000"),
) -> PaperActionGatedStrategyRecommendationQueuePriorityRow:
    return PaperActionGatedStrategyRecommendationQueuePriorityRow(
        priority_rank=priority_rank,
        source_generated_at=generated_at - timedelta(minutes=5),
        config_version="action-gated-strategy-recommendation-queue-v0",
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status=action_status,
        recommended_next_step=NEXT_STEP_BY_ACTION_STATUS[action_status],
        research_priority=RESEARCH_PRIORITY_BY_ACTION_STATUS[action_status],
        candidate_count=candidate_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        total_ready_notional=total_ready_notional,
        top_queue_score=top_queue_score,
        average_ready_score=average_ready_score,
        research_priority_score=(
            ACTION_STATUS_SCORE[action_status]
            + Decimal(ready_count)
            + top_queue_score
            + average_ready_score
        ).quantize(Decimal("0.000001")),
    )


def _priority_report(
    *,
    generated_at: datetime = BASE_AT,
    rows: tuple[PaperActionGatedStrategyRecommendationQueuePriorityRow, ...] | None = None,
) -> PaperActionGatedStrategyRecommendationQueuePriorityReport:
    if rows is None:
        rows = (_priority_row(generated_at=generated_at),)
    return PaperActionGatedStrategyRecommendationQueuePriorityReport(
        generated_at=generated_at,
        source_report_count=len(rows),
        research_ready_count=sum(1 for row in rows if row.action_status == "research_ready"),
        watch_count=sum(1 for row in rows if row.action_status == "watch"),
        blocked_count=sum(1 for row in rows if row.action_status == "blocked"),
        total_ready_notional=sum((row.total_ready_notional for row in rows), Decimal("0")),
        top_research_priority_score=max(
            (row.research_priority_score for row in rows),
            default=Decimal("0.000000"),
        ),
        average_research_priority_score=(
            (
                sum((row.research_priority_score for row in rows), Decimal("0"))
                / Decimal(len(rows))
            ).quantize(Decimal("0.000001"))
            if rows
            else Decimal("0.000000")
        ),
        priority_rows=rows,
    )


def _risk_report(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    *,
    status: str = "pass",
    reason_codes: tuple[str, ...] = ("queue_risk_passed",),
    max_total_ready_notional: Decimal = Decimal("100.000000"),
    max_single_queue_ready_notional: Decimal = Decimal("200.000000"),
    max_ready_candidate_count: int = 10,
    max_total_candidate_count: int = 20,
    throttle_utilization_threshold: Decimal = Decimal("0.900000"),
) -> PaperActionGatedStrategyRecommendationQueueRiskReport:
    ready_notional = priority_report.total_ready_notional
    largest_notional = max(
        (row.total_ready_notional for row in priority_report.priority_rows),
        default=Decimal("0.000000"),
    )
    source_queue_count = priority_report.source_report_count
    candidate_count = sum(row.candidate_count for row in priority_report.priority_rows)
    ready_count = sum(row.ready_count for row in priority_report.priority_rows)
    watch_count = sum(row.watch_count for row in priority_report.priority_rows)
    blocked_count = sum(row.blocked_count for row in priority_report.priority_rows)
    blocking_reasons = {
        "empty_queue_reports",
        "source_queue_blocked",
        "total_ready_notional_cap_exceeded",
        "single_queue_ready_notional_cap_exceeded",
        "ready_candidate_count_cap_exceeded",
        "candidate_count_cap_exceeded",
    }
    watch_reasons = {
        "source_queue_watch",
        "near_total_ready_notional_cap",
        "near_single_queue_ready_notional_cap",
        "near_ready_candidate_count_cap",
        "near_candidate_count_cap",
    }
    return PaperActionGatedStrategyRecommendationQueueRiskReport(
        generated_at=priority_report.generated_at,
        config_version="action-gated-queue-risk-v0",
        source_config_versions=("action-gated-strategy-recommendation-queue-v0",),
        status=status,
        recommended_next_step=NEXT_STEP_BY_RISK_STATUS[status],
        reason_codes=reason_codes,
        source_queue_count=source_queue_count,
        research_ready_source_count=priority_report.research_ready_count,
        watch_source_count=priority_report.watch_count,
        blocked_source_count=priority_report.blocked_count,
        candidate_count=candidate_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        blocked_reason_count=sum(1 for reason in reason_codes if reason in blocking_reasons),
        watch_reason_count=sum(1 for reason in reason_codes if reason in watch_reasons),
        total_ready_notional=ready_notional,
        largest_queue_ready_notional=largest_notional,
        total_ready_notional_utilization=(
            (ready_notional / max_total_ready_notional).quantize(Decimal("0.000001"))
            if max_total_ready_notional > Decimal("0")
            else None
        ),
        largest_queue_ready_notional_utilization=(
            (largest_notional / max_single_queue_ready_notional).quantize(
                Decimal("0.000001"),
            )
            if max_single_queue_ready_notional > Decimal("0")
            else None
        ),
        max_total_ready_notional=max_total_ready_notional,
        max_single_queue_ready_notional=max_single_queue_ready_notional,
        max_ready_candidate_count=max_ready_candidate_count,
        max_total_candidate_count=max_total_candidate_count,
        throttle_utilization_threshold=throttle_utilization_threshold,
    )


def _snapshot(
    *,
    generated_at: datetime,
    rows: tuple[PaperActionGatedStrategyRecommendationQueuePriorityRow, ...] | None = None,
    risk_status: str = "pass",
    risk_reason_codes: tuple[str, ...] = ("queue_risk_passed",),
    max_total_ready_notional: Decimal = Decimal("100.000000"),
) -> tuple[
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueueRiskReport,
]:
    priority_report = _priority_report(generated_at=generated_at, rows=rows)
    return (
        priority_report,
        _risk_report(
            priority_report,
            status=risk_status,
            reason_codes=risk_reason_codes,
            max_total_ready_notional=max_total_ready_notional,
        ),
    )


def _row_values(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
) -> dict[str, object]:
    return dict(row.__dict__)


def _source_row_values(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
) -> dict[str, object]:
    return dict(row.__dict__)


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("trend DB JSON maps must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _expected_source_window_sha256(
    source_rows: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
        ...,
    ],
) -> str:
    return _json_sha256(
        {
            "sources": [
                {
                    "snapshot_sha256": source_row.snapshot_sha256,
                    "source_input_position": source_row.source_input_position,
                    "trend_ordinal": source_row.trend_ordinal,
                }
                for source_row in source_rows
            ],
        },
    )


def _decimal_or_none(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _expected_trend_sha256(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
) -> str:
    return _json_sha256(
        {
            "trend_schema_version": row.trend_schema_version,
            "source_window_sha256": row.source_window_sha256,
            "source_snapshot_count": row.source_snapshot_count,
            "first_generated_at": (
                None
                if row.first_generated_at is None
                else row.first_generated_at.isoformat()
            ),
            "latest_generated_at": (
                None
                if row.latest_generated_at is None
                else row.latest_generated_at.isoformat()
            ),
            "latest_risk_status": row.latest_risk_status,
            "risk_pass_count": row.risk_pass_count,
            "risk_watch_count": row.risk_watch_count,
            "risk_blocked_count": row.risk_blocked_count,
            "consecutive_latest_watch_count": row.consecutive_latest_watch_count,
            "consecutive_latest_blocked_count": row.consecutive_latest_blocked_count,
            "duplicate_generated_at_count": row.duplicate_generated_at_count,
            "ready_notional_first": _decimal_or_none(row.ready_notional_first),
            "ready_notional_latest": _decimal_or_none(row.ready_notional_latest),
            "ready_notional_delta": _decimal_or_none(row.ready_notional_delta),
            "top_priority_score_first": _decimal_or_none(row.top_priority_score_first),
            "top_priority_score_latest": _decimal_or_none(row.top_priority_score_latest),
            "top_priority_score_delta": _decimal_or_none(row.top_priority_score_delta),
            "average_priority_score_first": _decimal_or_none(
                row.average_priority_score_first,
            ),
            "average_priority_score_latest": _decimal_or_none(
                row.average_priority_score_latest,
            ),
            "average_priority_score_delta": _decimal_or_none(
                row.average_priority_score_delta,
            ),
            "source_queue_count_first": row.source_queue_count_first,
            "source_queue_count_latest": row.source_queue_count_latest,
            "source_queue_count_delta": row.source_queue_count_delta,
            "latest_reason_code_counts_json": row.latest_reason_code_counts_json,
            "total_reason_code_counts_json": row.total_reason_code_counts_json,
            "repeated_reason_code_counts_json": row.repeated_reason_code_counts_json,
            "reason_code_rows_json": row.reason_code_rows_json,
        },
    )


def test_trend_db_rows_serialize_manifest_scalars_and_hashes_deterministically():
    older = _snapshot(
        generated_at=BASE_AT,
        rows=(
            _priority_row(
                generated_at=BASE_AT,
                total_ready_notional=Decimal("10.000000"),
                top_queue_score=Decimal("0.200000"),
                average_ready_score=Decimal("0.100000"),
            ),
        ),
    )
    latest_at = BASE_AT + timedelta(hours=2)
    latest = _snapshot(
        generated_at=latest_at,
        rows=(
            _priority_row(
                priority_rank=1,
                generated_at=latest_at,
                total_ready_notional=Decimal("30.000000"),
                top_queue_score=Decimal("0.600000"),
                average_ready_score=Decimal("0.500000"),
            ),
            _priority_row(
                priority_rank=2,
                generated_at=latest_at,
                action_status="watch",
                candidate_count=1,
                ready_count=0,
                watch_count=1,
                total_ready_notional=Decimal("0.000000"),
                top_queue_score=Decimal("0.000000"),
                average_ready_score=Decimal("0.000000"),
            ),
        ),
        risk_status="watch",
        risk_reason_codes=("source_queue_watch",),
    )
    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (latest, older),
        generated_at=GENERATED_AT,
    )

    db_rows = (
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            trend,
            (latest, older),
        )
    )

    assert type(db_rows) is PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows
    assert type(db_rows.trend_row) is (
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow
    )
    assert all(
        type(source_row)
        is PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow
        for source_row in db_rows.source_rows
    )
    trend_row = db_rows.trend_row
    assert len(trend_row.trend_sha256) == 64
    assert trend_row.trend_sha256 == trend_row.trend_sha256.lower()
    assert len(trend_row.source_window_sha256) == 64
    assert trend_row.trend_schema_version == (
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION
    )
    assert trend_row.generated_at == GENERATED_AT
    assert trend_row.source_snapshot_count == 2
    assert trend_row.first_generated_at == BASE_AT
    assert trend_row.latest_generated_at == latest_at
    assert trend_row.latest_risk_status == "watch"
    assert trend_row.risk_pass_count == 1
    assert trend_row.risk_watch_count == 1
    assert trend_row.risk_blocked_count == 0
    assert trend_row.ready_notional_first == Decimal("10.000000")
    assert trend_row.ready_notional_latest == Decimal("30.000000")
    assert trend_row.ready_notional_delta == Decimal("20.000000")
    assert trend_row.top_priority_score_first == Decimal("4.300000")
    assert trend_row.top_priority_score_latest == Decimal("5.100000")
    assert trend_row.average_priority_score_latest == Decimal("3.050000")
    assert trend_row.source_queue_count_first == 1
    assert trend_row.source_queue_count_latest == 2
    assert trend_row.source_queue_count_delta == 1
    assert trend_row.latest_reason_code_counts_json == {"source_queue_watch": 1}
    assert trend_row.total_reason_code_counts_json == {
        "queue_risk_passed": 1,
        "source_queue_watch": 1,
    }
    assert trend_row.repeated_reason_code_counts_json == {}
    assert trend_row.reason_code_rows_json == [
        {
            "latest_count": 0,
            "reason_code": "queue_risk_passed",
            "snapshot_count": 1,
            "total_count": 1,
        },
        {
            "latest_count": 1,
            "reason_code": "source_queue_watch",
            "snapshot_count": 1,
            "total_count": 1,
        },
    ]
    assert trend_row.paper_only is True
    assert trend_row.report_only is True
    assert trend_row.readonly is True

    latest_snapshot_row = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            *latest,
        )
    )
    older_snapshot_row = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            *older,
        )
    )
    assert db_rows.source_rows == (
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow(
            trend_sha256=trend_row.trend_sha256,
            trend_ordinal=1,
            source_input_position=2,
            snapshot_sha256=older_snapshot_row.snapshot_sha256,
            source_generated_at=BASE_AT,
        ),
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow(
            trend_sha256=trend_row.trend_sha256,
            trend_ordinal=2,
            source_input_position=1,
            snapshot_sha256=latest_snapshot_row.snapshot_sha256,
            source_generated_at=latest_at,
        ),
    )
    assert trend_row.source_window_sha256 == _expected_source_window_sha256(
        db_rows.source_rows,
    )
    assert trend_row.trend_sha256 == _expected_trend_sha256(trend_row)
    _assert_no_floats(trend_row.latest_reason_code_counts_json)
    _assert_no_floats(trend_row.total_reason_code_counts_json)
    _assert_no_floats(trend_row.repeated_reason_code_counts_json)
    _assert_no_floats(trend_row.reason_code_rows_json)
    assert (
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows(
            db_rows,
        )
        == db_rows
    )


def test_trend_hash_excludes_trend_generated_at_but_includes_source_manifest_and_scalars():
    snapshot = _snapshot(generated_at=BASE_AT)
    first_trend = (
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            (snapshot,),
            generated_at=GENERATED_AT,
        )
    )
    second_trend = (
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            (snapshot,),
            generated_at=SECOND_GENERATED_AT,
        )
    )
    different_at = BASE_AT + timedelta(hours=1)
    different_snapshot = _snapshot(
        generated_at=different_at,
        rows=(
            _priority_row(
                generated_at=different_at,
                action_status="watch",
                candidate_count=1,
                ready_count=0,
                watch_count=1,
                total_ready_notional=Decimal("0.000000"),
                top_queue_score=Decimal("0.000000"),
                average_ready_score=Decimal("0.000000"),
            ),
        ),
        risk_status="watch",
        risk_reason_codes=("source_queue_watch",),
    )

    first_rows = (
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            first_trend,
            (snapshot,),
        )
    )
    second_rows = (
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            second_trend,
            (snapshot,),
        )
    )
    changed_trend = (
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            (different_snapshot,),
            generated_at=GENERATED_AT,
        )
    )
    changed_rows = (
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            changed_trend,
            (different_snapshot,),
        )
    )

    assert first_rows.trend_row.generated_at != second_rows.trend_row.generated_at
    assert first_rows.trend_row.source_window_sha256 == (
        second_rows.trend_row.source_window_sha256
    )
    assert first_rows.trend_row.trend_sha256 == second_rows.trend_row.trend_sha256
    assert first_rows.trend_row.trend_sha256 != changed_rows.trend_row.trend_sha256


def test_trend_db_rows_empty_trend_shape_has_empty_manifest_and_stable_hashes():
    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (),
        generated_at=GENERATED_AT,
    )

    db_rows = (
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            trend,
            (),
        )
    )

    assert db_rows.source_rows == ()
    trend_row = db_rows.trend_row
    assert trend_row.source_snapshot_count == 0
    assert trend_row.first_generated_at is None
    assert trend_row.latest_generated_at is None
    assert trend_row.latest_risk_status is None
    assert trend_row.risk_pass_count == 0
    assert trend_row.risk_watch_count == 0
    assert trend_row.risk_blocked_count == 0
    assert trend_row.consecutive_latest_watch_count == 0
    assert trend_row.consecutive_latest_blocked_count == 0
    assert trend_row.duplicate_generated_at_count == 0
    assert trend_row.ready_notional_first is None
    assert trend_row.ready_notional_latest is None
    assert trend_row.ready_notional_delta is None
    assert trend_row.top_priority_score_first is None
    assert trend_row.top_priority_score_latest is None
    assert trend_row.top_priority_score_delta is None
    assert trend_row.average_priority_score_first is None
    assert trend_row.average_priority_score_latest is None
    assert trend_row.average_priority_score_delta is None
    assert trend_row.source_queue_count_first is None
    assert trend_row.source_queue_count_latest is None
    assert trend_row.source_queue_count_delta is None
    assert trend_row.latest_reason_code_counts_json == {}
    assert trend_row.total_reason_code_counts_json == {}
    assert trend_row.repeated_reason_code_counts_json == {}
    assert trend_row.reason_code_rows_json == []
    assert trend_row.source_window_sha256 == _expected_source_window_sha256(())
    assert trend_row.trend_sha256 == _expected_trend_sha256(trend_row)


def test_trend_db_rows_reject_wrong_types_false_flags_and_mismatched_sources():
    snapshot = _snapshot(generated_at=BASE_AT)
    other_at = BASE_AT + timedelta(hours=1)
    other_snapshot = _snapshot(
        generated_at=other_at,
        rows=(
            _priority_row(
                generated_at=other_at,
                action_status="watch",
                candidate_count=1,
                ready_count=0,
                watch_count=1,
                total_ready_notional=Decimal("0.000000"),
                top_queue_score=Decimal("0.000000"),
                average_ready_score=Decimal("0.000000"),
            ),
        ),
        risk_status="watch",
        risk_reason_codes=("source_queue_watch",),
    )
    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (snapshot,),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="TrendReport"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            object(),
            (snapshot,),
        )
    with pytest.raises(ValueError, match="TrendReport"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            TrendReportSubclass(**trend.__dict__),
            (snapshot,),
        )
    with pytest.raises(ValueError, match="snapshot_pairs"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            trend,
            "not snapshots",
        )
    with pytest.raises(ValueError, match="snapshot_pairs"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            trend,
            ((object(), snapshot[1]),),
        )
    with pytest.raises(ValueError, match="match snapshot_pairs"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            trend,
            (snapshot, other_snapshot),
        )

    trend_with_false_flag = PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport(
        **trend.__dict__,
    )
    object.__setattr__(trend_with_false_flag, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            trend_with_false_flag,
            (snapshot,),
        )


def test_trend_db_row_dataclasses_are_frozen_and_revalidate_direct_invariants():
    snapshot = _snapshot(generated_at=BASE_AT)
    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (snapshot,),
        generated_at=GENERATED_AT,
    )
    db_rows = (
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            trend,
            (snapshot,),
        )
    )
    row = db_rows.trend_row

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="trend_schema_version"):
        replace(row, trend_schema_version="bad-version")
    with pytest.raises(ValueError, match="trend_sha256"):
        replace(row, trend_sha256="not a sha")
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="source_snapshot_count"):
        replace(row, source_snapshot_count=2)
    with pytest.raises(ValueError, match="risk status counts"):
        replace(row, risk_pass_count=0)
    with pytest.raises(ValueError, match="latest_reason_code_counts_json"):
        replace(row, latest_reason_code_counts_json={"queue_risk_passed": 2})
    with pytest.raises(ValueError, match="reason_code_rows_json"):
        replace(
            row,
            reason_code_rows_json=[
                {
                    **row.reason_code_rows_json[0],
                    "snapshot_count": 2,
                },
            ],
        )
    with pytest.raises(ValueError, match="source_window_sha256"):
        replace(row, source_window_sha256="a" * 64)
    with pytest.raises(ValueError, match="trend_sha256"):
        replace(
            row,
            ready_notional_latest=row.ready_notional_latest + Decimal("1.000000"),
        )
    with pytest.raises(ValueError, match="latest_reason_code_counts_json"):
        replace(row, latest_reason_code_counts_json={"queue_risk_passed": 0.1})

    source_row = db_rows.source_rows[0]
    with pytest.raises(FrozenInstanceError):
        source_row.readonly = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="trend_ordinal"):
        replace(source_row, trend_ordinal=0)
    with pytest.raises(ValueError, match="snapshot_sha256"):
        replace(source_row, snapshot_sha256="A" * 64)
    with pytest.raises(ValueError, match="report_only"):
        replace(source_row, report_only=False)


def test_trend_db_rows_enforce_sorted_unique_contiguous_source_manifest():
    first = _snapshot(generated_at=BASE_AT)
    second = _snapshot(generated_at=BASE_AT + timedelta(hours=1))
    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (second, first),
        generated_at=GENERATED_AT,
    )
    db_rows = (
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            trend,
            (second, first),
        )
    )

    with pytest.raises(ValueError, match="trend_ordinal"):
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
            trend_row=db_rows.trend_row,
            source_rows=tuple(reversed(db_rows.source_rows)),
        )
    with pytest.raises(ValueError, match="trend_ordinal"):
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
            trend_row=db_rows.trend_row,
            source_rows=(
                db_rows.source_rows[0],
                replace(db_rows.source_rows[1], trend_ordinal=1),
            ),
        )
    with pytest.raises(ValueError, match="source_input_position"):
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
            trend_row=db_rows.trend_row,
            source_rows=(
                db_rows.source_rows[0],
                replace(db_rows.source_rows[1], source_input_position=2),
            ),
        )
    with pytest.raises(ValueError, match="trend_sha256"):
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
            trend_row=db_rows.trend_row,
            source_rows=(
                db_rows.source_rows[0],
                replace(db_rows.source_rows[1], trend_sha256="a" * 64),
            ),
        )


def test_from_db_rows_requires_exact_types_and_recomputes_manifest_hashes():
    snapshot = _snapshot(generated_at=BASE_AT)
    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (snapshot,),
        generated_at=GENERATED_AT,
    )
    db_rows = (
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
            trend,
            (snapshot,),
        )
    )

    with pytest.raises(ValueError, match="TrendDbRows"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows(
            object(),
        )
    with pytest.raises(ValueError, match="TrendDbRows"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows(
            TrendDbRowsSubclass(
                trend_row=db_rows.trend_row,
                source_rows=db_rows.source_rows,
            ),
        )
    with pytest.raises(ValueError, match="TrendDbRow"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows(
            PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
                trend_row=TrendDbRowSubclass(**_row_values(db_rows.trend_row)),
                source_rows=db_rows.source_rows,
            ),
        )
    with pytest.raises(ValueError, match="TrendSourceDbRow"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows(
            PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
                trend_row=db_rows.trend_row,
                source_rows=(
                    TrendSourceDbRowSubclass(**_source_row_values(db_rows.source_rows[0])),
                ),
            ),
        )

    corrupted_trend_row = PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow(
        **_row_values(db_rows.trend_row),
    )
    object.__setattr__(corrupted_trend_row, "trend_sha256", "a" * 64)
    corrupted_rows = PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
        trend_row=db_rows.trend_row,
        source_rows=db_rows.source_rows,
    )
    object.__setattr__(corrupted_rows, "trend_row", corrupted_trend_row)
    with pytest.raises(ValueError, match="trend_sha256"):
        paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows(
            corrupted_rows,
        )


def test_trend_db_row_module_is_pure_codec():
    module_path = Path(
        "src/polymarket_alpha_lab/"
        "action_gated_strategy_recommendation_queue_decision_support_trend_db_row.py",
    )
    source = module_path.read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "sql",
        "network",
        "client",
        "auth",
        "wallet",
        "account",
        "signing",
        "submission",
        "cancellation",
        "replacement",
        "exchange",
        "live_trading",
    ):
        assert banned not in source.lower()

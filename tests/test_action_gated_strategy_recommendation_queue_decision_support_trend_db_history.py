from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_db_history import (
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig,
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryReport,
    build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_history_report,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_db_row import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION,
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows,
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
)


GENERATED_AT = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 21, 8, 0, tzinfo=UTC)
CONFIG_VERSION = (
    "action-gated-strategy-recommendation-queue-decision-support-trend-db-history-v0"
)


class TrendDbRowsSubclass(
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows,
):
    pass


class DatetimeSubclass(datetime):
    pass


def _config() -> (
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig
):
    return PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig(
        config_version=CONFIG_VERSION,
    )


def _history(
    db_rows: list[PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows]
    | tuple[PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows, ...],
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryReport:
    return build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_history_report(
        db_rows,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _sha256_seed(seed: int) -> str:
    return f"{seed:064x}"[-64:]


def _json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_window_sha256(
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


def _trend_sha256_from_values(values: dict[str, object]) -> str:
    return _json_sha256(
        {
            "trend_schema_version": values["trend_schema_version"],
            "source_window_sha256": values["source_window_sha256"],
            "source_snapshot_count": values["source_snapshot_count"],
            "first_generated_at": (
                None
                if values["first_generated_at"] is None
                else values["first_generated_at"].isoformat()
            ),
            "latest_generated_at": (
                None
                if values["latest_generated_at"] is None
                else values["latest_generated_at"].isoformat()
            ),
            "latest_risk_status": values["latest_risk_status"],
            "risk_pass_count": values["risk_pass_count"],
            "risk_watch_count": values["risk_watch_count"],
            "risk_blocked_count": values["risk_blocked_count"],
            "consecutive_latest_watch_count": values[
                "consecutive_latest_watch_count"
            ],
            "consecutive_latest_blocked_count": values[
                "consecutive_latest_blocked_count"
            ],
            "duplicate_generated_at_count": values["duplicate_generated_at_count"],
            "ready_notional_first": _decimal_or_none(
                values["ready_notional_first"],
            ),
            "ready_notional_latest": _decimal_or_none(
                values["ready_notional_latest"],
            ),
            "ready_notional_delta": _decimal_or_none(
                values["ready_notional_delta"],
            ),
            "top_priority_score_first": _decimal_or_none(
                values["top_priority_score_first"],
            ),
            "top_priority_score_latest": _decimal_or_none(
                values["top_priority_score_latest"],
            ),
            "top_priority_score_delta": _decimal_or_none(
                values["top_priority_score_delta"],
            ),
            "average_priority_score_first": _decimal_or_none(
                values["average_priority_score_first"],
            ),
            "average_priority_score_latest": _decimal_or_none(
                values["average_priority_score_latest"],
            ),
            "average_priority_score_delta": _decimal_or_none(
                values["average_priority_score_delta"],
            ),
            "source_queue_count_first": values["source_queue_count_first"],
            "source_queue_count_latest": values["source_queue_count_latest"],
            "source_queue_count_delta": values["source_queue_count_delta"],
            "latest_reason_code_counts_json": values[
                "latest_reason_code_counts_json"
            ],
            "total_reason_code_counts_json": values["total_reason_code_counts_json"],
            "repeated_reason_code_counts_json": values[
                "repeated_reason_code_counts_json"
            ],
            "reason_code_rows_json": values["reason_code_rows_json"],
        },
    )


def _canonical_reason_count_maps(
    latest_reason_counts: dict[str, int],
) -> tuple[dict[str, int], dict[str, int], dict[str, int], list[dict[str, object]]]:
    reason_rows = [
        {
            "latest_count": count,
            "reason_code": reason_code,
            "snapshot_count": 1,
            "total_count": count,
        }
        for reason_code, count in latest_reason_counts.items()
    ]
    reason_rows = sorted(
        reason_rows,
        key=lambda row: (-int(row["total_count"]), str(row["reason_code"])),
    )
    latest_counts = {
        str(row["reason_code"]): int(row["latest_count"])
        for row in reason_rows
        if int(row["latest_count"]) > 0
    }
    total_counts = {
        str(row["reason_code"]): int(row["total_count"]) for row in reason_rows
    }
    repeated_counts = {
        reason_code: count for reason_code, count in total_counts.items() if count > 1
    }
    return latest_counts, total_counts, repeated_counts, reason_rows


def _trend_db_rows(
    *,
    trend_generated_at: datetime,
    latest_risk_status: str = "pass",
    snapshot_seed: int = 1,
    latest_reason_counts: dict[str, int] | None = None,
    ready_notional_delta: Decimal = Decimal("0.000000"),
    top_priority_score_delta: Decimal = Decimal("0.000000"),
    average_priority_score_delta: Decimal = Decimal("0.000000"),
    source_queue_count_delta: int = 0,
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows:
    if latest_reason_counts is None:
        latest_reason_counts = {"queue_risk_passed": 1}
        if latest_risk_status == "watch":
            latest_reason_counts = {"source_queue_watch": 1}
        elif latest_risk_status == "blocked":
            latest_reason_counts = {"source_queue_blocked": 1}

    source_generated_at = trend_generated_at - timedelta(minutes=15)
    placeholder_source_rows = (
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow(
            trend_sha256="0" * 64,
            trend_ordinal=1,
            source_input_position=1,
            snapshot_sha256=_sha256_seed(snapshot_seed),
            source_generated_at=source_generated_at,
        ),
    )
    source_window_sha256 = _source_window_sha256(placeholder_source_rows)
    (
        latest_counts,
        total_counts,
        repeated_counts,
        reason_rows,
    ) = _canonical_reason_count_maps(latest_reason_counts)

    risk_counts = {
        "pass": int(latest_risk_status == "pass"),
        "watch": int(latest_risk_status == "watch"),
        "blocked": int(latest_risk_status == "blocked"),
    }
    values: dict[str, object] = {
        "trend_schema_version": ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION,
        "source_window_sha256": source_window_sha256,
        "generated_at": trend_generated_at,
        "source_snapshot_count": 1,
        "first_generated_at": source_generated_at,
        "latest_generated_at": source_generated_at,
        "latest_risk_status": latest_risk_status,
        "risk_pass_count": risk_counts["pass"],
        "risk_watch_count": risk_counts["watch"],
        "risk_blocked_count": risk_counts["blocked"],
        "consecutive_latest_watch_count": int(latest_risk_status == "watch"),
        "consecutive_latest_blocked_count": int(latest_risk_status == "blocked"),
        "duplicate_generated_at_count": 0,
        "ready_notional_first": Decimal("10.000000"),
        "ready_notional_latest": Decimal("10.000000") + ready_notional_delta,
        "ready_notional_delta": ready_notional_delta,
        "top_priority_score_first": Decimal("1.000000"),
        "top_priority_score_latest": Decimal("1.000000") + top_priority_score_delta,
        "top_priority_score_delta": top_priority_score_delta,
        "average_priority_score_first": Decimal("0.500000"),
        "average_priority_score_latest": (
            Decimal("0.500000") + average_priority_score_delta
        ),
        "average_priority_score_delta": average_priority_score_delta,
        "source_queue_count_first": 2,
        "source_queue_count_latest": 2 + source_queue_count_delta,
        "source_queue_count_delta": source_queue_count_delta,
        "latest_reason_code_counts_json": latest_counts,
        "total_reason_code_counts_json": total_counts,
        "repeated_reason_code_counts_json": repeated_counts,
        "reason_code_rows_json": reason_rows,
    }
    trend_sha256 = _trend_sha256_from_values(values)
    trend_row = PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow(
        trend_sha256=trend_sha256,
        **values,
    )
    source_rows = (
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow(
            trend_sha256=trend_sha256,
            trend_ordinal=1,
            source_input_position=1,
            snapshot_sha256=_sha256_seed(snapshot_seed),
            source_generated_at=source_generated_at,
        ),
    )
    return PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
        trend_row=trend_row,
        source_rows=source_rows,
    )


def test_trend_db_history_empty_input_is_readonly_report():
    history = _history(())

    assert history.generated_at == GENERATED_AT
    assert history.config_version == CONFIG_VERSION
    assert history.trend_count == 0
    assert history.total_source_snapshot_count == 0
    assert history.first_trend_generated_at is None
    assert history.latest_trend_generated_at is None
    assert history.latest_risk_status is None
    assert history.risk_status_counts == (("pass", 0), ("watch", 0), ("blocked", 0))
    assert history.duplicate_generated_at_count == 0
    assert history.consecutive_latest_pass_count == 0
    assert history.consecutive_latest_watch_count == 0
    assert history.consecutive_latest_blocked_count == 0
    assert history.ready_notional_delta is None
    assert history.top_priority_score_delta is None
    assert history.average_priority_score_delta is None
    assert history.source_queue_count_delta is None
    assert history.latest_reason_code_counts == ()
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


def test_trend_db_history_sorts_newest_first_input_chronologically():
    older = _trend_db_rows(
        trend_generated_at=BASE_AT,
        latest_risk_status="pass",
        snapshot_seed=11,
        ready_notional_delta=Decimal("1.000000"),
    )
    latest = _trend_db_rows(
        trend_generated_at=BASE_AT + timedelta(hours=2),
        latest_risk_status="watch",
        snapshot_seed=12,
        ready_notional_delta=Decimal("4.000000"),
        top_priority_score_delta=Decimal("0.250000"),
        average_priority_score_delta=Decimal("0.125000"),
        source_queue_count_delta=2,
    )

    history = _history([latest, older])

    assert history.trend_count == 2
    assert history.total_source_snapshot_count == 2
    assert history.first_trend_generated_at == older.trend_row.generated_at
    assert history.latest_trend_generated_at == latest.trend_row.generated_at
    assert history.latest_risk_status == "watch"
    assert history.consecutive_latest_pass_count == 0
    assert history.consecutive_latest_watch_count == 1
    assert history.consecutive_latest_blocked_count == 0
    assert history.ready_notional_delta == latest.trend_row.ready_notional_delta
    assert history.top_priority_score_delta == latest.trend_row.top_priority_score_delta
    assert (
        history.average_priority_score_delta
        == latest.trend_row.average_priority_score_delta
    )
    assert history.source_queue_count_delta == latest.trend_row.source_queue_count_delta


def test_trend_db_history_counts_risks_duplicates_streaks_and_latest_reason_codes():
    duplicate_at = BASE_AT + timedelta(hours=1)
    rows = (
        _trend_db_rows(
            trend_generated_at=BASE_AT,
            latest_risk_status="pass",
            snapshot_seed=21,
        ),
        _trend_db_rows(
            trend_generated_at=duplicate_at,
            latest_risk_status="blocked",
            snapshot_seed=22,
        ),
        _trend_db_rows(
            trend_generated_at=duplicate_at,
            latest_risk_status="pass",
            snapshot_seed=23,
        ),
        _trend_db_rows(
            trend_generated_at=BASE_AT + timedelta(hours=2),
            latest_risk_status="watch",
            snapshot_seed=24,
        ),
        _trend_db_rows(
            trend_generated_at=BASE_AT + timedelta(hours=3),
            latest_risk_status="watch",
            snapshot_seed=25,
            latest_reason_counts={
                "source_queue_watch": 2,
                "near_candidate_count_cap": 1,
            },
            ready_notional_delta=Decimal("4.250000"),
            top_priority_score_delta=Decimal("-0.125000"),
            average_priority_score_delta=Decimal("0.500000"),
            source_queue_count_delta=3,
        ),
    )

    history = _history(rows)

    assert history.risk_status_counts == (("pass", 2), ("watch", 2), ("blocked", 1))
    assert history.duplicate_generated_at_count == 1
    assert history.consecutive_latest_pass_count == 0
    assert history.consecutive_latest_watch_count == 2
    assert history.consecutive_latest_blocked_count == 0
    assert history.ready_notional_delta == Decimal("4.250000")
    assert history.top_priority_score_delta == Decimal("-0.125000")
    assert history.average_priority_score_delta == Decimal("0.500000")
    assert history.source_queue_count_delta == 3
    assert history.latest_reason_code_counts == (
        ("near_candidate_count_cap", 1),
        ("source_queue_watch", 2),
    )
    assert type(history.ready_notional_delta) is Decimal
    assert type(history.top_priority_score_delta) is Decimal
    assert type(history.average_priority_score_delta) is Decimal


def test_trend_db_history_counts_consecutive_latest_pass_streak():
    rows = (
        _trend_db_rows(
            trend_generated_at=BASE_AT,
            latest_risk_status="pass",
            snapshot_seed=61,
        ),
        _trend_db_rows(
            trend_generated_at=BASE_AT + timedelta(hours=1),
            latest_risk_status="watch",
            snapshot_seed=62,
        ),
        _trend_db_rows(
            trend_generated_at=BASE_AT + timedelta(hours=2),
            latest_risk_status="pass",
            snapshot_seed=63,
        ),
        _trend_db_rows(
            trend_generated_at=BASE_AT + timedelta(hours=3),
            latest_risk_status="pass",
            snapshot_seed=64,
        ),
    )

    history = _history(rows)

    assert history.latest_risk_status == "pass"
    assert history.risk_status_counts == (("pass", 3), ("watch", 1), ("blocked", 0))
    assert history.consecutive_latest_pass_count == 2
    assert history.consecutive_latest_watch_count == 0
    assert history.consecutive_latest_blocked_count == 0


def test_trend_db_history_uses_trend_sha256_as_deterministic_same_time_tie_order():
    first = _trend_db_rows(
        trend_generated_at=BASE_AT,
        latest_risk_status="pass",
        snapshot_seed=31,
    )
    same_time_a = _trend_db_rows(
        trend_generated_at=BASE_AT + timedelta(hours=1),
        latest_risk_status="watch",
        snapshot_seed=32,
        ready_notional_delta=Decimal("2.000000"),
    )
    same_time_b = _trend_db_rows(
        trend_generated_at=BASE_AT + timedelta(hours=1),
        latest_risk_status="blocked",
        snapshot_seed=33,
        ready_notional_delta=Decimal("3.000000"),
    )
    expected_latest = sorted(
        (first, same_time_a, same_time_b),
        key=lambda item: (item.trend_row.generated_at, item.trend_row.trend_sha256),
    )[-1]

    history = _history([same_time_b, same_time_a, first])

    assert history.latest_trend_generated_at == expected_latest.trend_row.generated_at
    assert history.latest_risk_status == expected_latest.trend_row.latest_risk_status
    assert history.ready_notional_delta == expected_latest.trend_row.ready_notional_delta


def test_trend_db_history_rejects_non_container_non_row_and_subclass_inputs():
    row = _trend_db_rows(trend_generated_at=BASE_AT, snapshot_seed=41)

    class ConfigSubclass(
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig,
    ):
        pass

    with pytest.raises(ValueError, match="db_rows must be a list or tuple"):
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_history_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="db_rows must contain"):
        _history((object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="db_rows must contain"):
        _history(
            (
                TrendDbRowsSubclass(
                    trend_row=row.trend_row,
                    source_rows=row.source_rows,
                ),
            ),
        )
    with pytest.raises(ValueError, match="config must be"):
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_history_report(
            (),
            config=ConfigSubclass(config_version=CONFIG_VERSION),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_history_report(
            (),
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 21, 12, 0, tzinfo=UTC),
        )

    history = _history(())
    with pytest.raises(ValueError, match="trend_count must be an int"):
        replace(history, trend_count=True)


def test_trend_db_history_rejects_inconsistent_latest_streak_invariants():
    empty = _history(())
    latest_pass = _history(
        (
            _trend_db_rows(
                trend_generated_at=BASE_AT,
                latest_risk_status="pass",
                snapshot_seed=71,
            ),
        ),
    )
    latest_watch = _history(
        (
            _trend_db_rows(
                trend_generated_at=BASE_AT,
                latest_risk_status="pass",
                snapshot_seed=72,
            ),
            _trend_db_rows(
                trend_generated_at=BASE_AT + timedelta(hours=1),
                latest_risk_status="watch",
                snapshot_seed=73,
            ),
        ),
    )
    latest_blocked = _history(
        (
            _trend_db_rows(
                trend_generated_at=BASE_AT,
                latest_risk_status="pass",
                snapshot_seed=74,
            ),
            _trend_db_rows(
                trend_generated_at=BASE_AT + timedelta(hours=1),
                latest_risk_status="blocked",
                snapshot_seed=75,
            ),
        ),
    )

    with pytest.raises(ValueError, match="consecutive_latest_pass_count must be an int"):
        replace(latest_pass, consecutive_latest_pass_count=True)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_pass_count must be a nonnegative integer",
    ):
        replace(latest_pass, consecutive_latest_pass_count=-1)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_pass_count must be zero without trends",
    ):
        replace(empty, consecutive_latest_pass_count=1)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_watch_count must be zero without trends",
    ):
        replace(empty, consecutive_latest_watch_count=1)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_blocked_count must be zero without trends",
    ):
        replace(empty, consecutive_latest_blocked_count=1)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_pass_count must be positive when latest_risk_status is pass",
    ):
        replace(latest_pass, consecutive_latest_pass_count=0)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_pass_count must be zero unless latest_risk_status is pass",
    ):
        replace(latest_watch, consecutive_latest_pass_count=1)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_pass_count must not exceed pass risk_status_count",
    ):
        replace(latest_pass, consecutive_latest_pass_count=2)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_watch_count must not exceed watch risk_status_count",
    ):
        replace(latest_watch, consecutive_latest_watch_count=2)
    with pytest.raises(
        ValueError,
        match=(
            "consecutive_latest_blocked_count must not exceed "
            "blocked risk_status_count"
        ),
    ):
        replace(latest_blocked, consecutive_latest_blocked_count=2)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_watch_count must be zero unless latest_risk_status is watch",
    ):
        replace(latest_pass, consecutive_latest_watch_count=1)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_blocked_count must be zero unless latest_risk_status is blocked",
    ):
        replace(latest_pass, consecutive_latest_blocked_count=1)
    with pytest.raises(
        ValueError,
        match="consecutive_latest_watch_count must be zero unless latest_risk_status is watch",
    ):
        replace(latest_blocked, consecutive_latest_watch_count=1)


def test_trend_db_history_enforces_hard_flags_on_inputs_and_output():
    row = _trend_db_rows(trend_generated_at=BASE_AT, snapshot_seed=51)
    unsafe_row = _trend_db_rows(trend_generated_at=BASE_AT, snapshot_seed=52)
    object.__setattr__(unsafe_row.trend_row, "readonly", False)

    history = _history((row,))

    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True
    with pytest.raises(FrozenInstanceError):
        history.readonly = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        _config().config_version = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly must be True"):
        _history((unsafe_row,))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(history, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(history, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(history, readonly=False)


def test_trend_db_history_module_is_pure_readonly_ast():
    module_path = Path(
        "src/polymarket_alpha_lab/"
        "action_gated_strategy_recommendation_queue_decision_support_trend_db_history.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    imported_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.append(node.module)
            imported_names.extend(alias.name for alias in node.names)

    banned_module_fragments = (
        "psycopg",
        "supabase",
        "_env",
        "_load",
        "_store",
        "_persist",
    )
    banned_import_names = {
        "build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report",
        "paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows",
        "insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend",
        "load_paper_action_gated_strategy_recommendation_queue_decision_support_reports_with_psycopg",
        "load_paper_action_gated_strategy_recommendation_queue_decision_support_trends_with_psycopg",
    }

    assert all(
        fragment not in module_name
        for module_name in imported_modules
        for fragment in banned_module_fragments
    )
    assert not (set(imported_names) & banned_import_names)

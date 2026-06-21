from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab import (
    action_gated_strategy_recommendation_queue_history_db_history as module_under_test,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history import (
    PaperActionGatedStrategyRecommendationQueueHistoryReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_db_history import (
    PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig,
    PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryReport,
    build_paper_action_gated_strategy_recommendation_queue_history_db_history_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)


GENERATED_AT = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 21, 8, 0, tzinfo=UTC)
CONFIG_VERSION = "action-gated-queue-history-db-history-v0"

NEXT_STEP_BY_STATUS = {
    "research_ready": "review_candidate_research_queue",
    "watch": "await_fresh_cycle_evidence",
    "blocked": "repair_cycle_evidence",
}


class HistoryReportSubclass(PaperActionGatedStrategyRecommendationQueueHistoryReport):
    pass


class DatetimeSubclass(datetime):
    pass


def _config() -> PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig:
    return PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig(
        config_version=CONFIG_VERSION,
    )


def _history(
    history_reports: list[PaperActionGatedStrategyRecommendationQueueHistoryReport]
    | tuple[PaperActionGatedStrategyRecommendationQueueHistoryReport, ...],
) -> PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryReport:
    return build_paper_action_gated_strategy_recommendation_queue_history_db_history_report(
        history_reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _reason_count(
    reason_code: str = "cycle_review_passed",
    count: int = 1,
) -> PaperRecommendationCycleActionGateReasonCodeCount:
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def _history_report(
    *,
    generated_at: datetime,
    latest_action_status: str = "research_ready",
    source_report_count: int = 1,
    total_ready_notional: Decimal = Decimal("0.000000"),
    status_transition_count: int = 0,
    latest_reason_code_counts: tuple[
        PaperRecommendationCycleActionGateReasonCodeCount,
        ...,
    ]
    | None = None,
    **overrides: object,
) -> PaperActionGatedStrategyRecommendationQueueHistoryReport:
    if latest_reason_code_counts is None:
        latest_reason_code_counts = (_reason_count(),)
        if latest_action_status == "watch":
            latest_reason_code_counts = (_reason_count("cycle_review_watch"),)
        elif latest_action_status == "blocked":
            latest_reason_code_counts = (_reason_count("cycle_review_blocked"),)

    status_counts = {
        "research_ready": 0,
        "watch": 0,
        "blocked": 0,
    }
    status_counts[latest_action_status] = source_report_count
    values = {
        "generated_at": generated_at,
        "source_report_count": source_report_count,
        "first_source_generated_at": generated_at - timedelta(minutes=10),
        "last_source_generated_at": generated_at - timedelta(minutes=1),
        "research_ready_count": status_counts["research_ready"],
        "watch_count": status_counts["watch"],
        "blocked_count": status_counts["blocked"],
        "total_ready_notional": total_ready_notional,
        "latest_action_status": latest_action_status,
        "latest_recommended_next_step": NEXT_STEP_BY_STATUS[latest_action_status],
        "status_transition_count": status_transition_count,
        "ready_notional_delta": Decimal("0.000000"),
        "latest_reason_code_counts": latest_reason_code_counts,
    }
    values.update(overrides)
    return PaperActionGatedStrategyRecommendationQueueHistoryReport(**values)


def test_history_db_history_empty_input_is_readonly_report_with_absent_latest_fields():
    history = _history(())

    assert history.generated_at == GENERATED_AT
    assert history.config_version == CONFIG_VERSION
    assert history.history_report_count == 0
    assert history.first_history_generated_at is None
    assert history.latest_history_generated_at is None
    assert history.latest_source_report_count is None
    assert history.latest_action_status is None
    assert history.latest_recommended_next_step is None
    assert history.action_status_counts == (
        ("research_ready", 0),
        ("watch", 0),
        ("blocked", 0),
    )
    assert history.duplicate_generated_at_count == 0
    assert history.consecutive_latest_research_ready_count == 0
    assert history.consecutive_latest_watch_count == 0
    assert history.consecutive_latest_blocked_count == 0
    assert history.latest_total_ready_notional is None
    assert history.latest_ready_notional_delta is None
    assert history.latest_status_transition_count is None
    assert history.latest_reason_code_counts == ()
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


def test_history_db_history_sorts_newest_first_input_chronologically():
    older = _history_report(
        generated_at=BASE_AT,
        latest_action_status="research_ready",
        source_report_count=3,
        total_ready_notional=Decimal("10.000000"),
    )
    latest = _history_report(
        generated_at=BASE_AT + timedelta(hours=2),
        latest_action_status="watch",
        source_report_count=7,
        total_ready_notional=Decimal("14.250000"),
        status_transition_count=2,
        latest_reason_code_counts=(
            _reason_count("cycle_history_stale", 1),
            _reason_count("cycle_review_watch", 2),
        ),
    )

    history = _history([latest, older])

    assert history.history_report_count == 2
    assert history.first_history_generated_at == older.generated_at
    assert history.latest_history_generated_at == latest.generated_at
    assert history.latest_source_report_count == 7
    assert history.latest_action_status == "watch"
    assert history.latest_recommended_next_step == "await_fresh_cycle_evidence"
    assert history.latest_total_ready_notional == Decimal("14.250000")
    assert history.latest_ready_notional_delta == Decimal("4.250000")
    assert history.latest_status_transition_count == 2
    assert history.latest_reason_code_counts == (
        ("cycle_history_stale", 1),
        ("cycle_review_watch", 2),
    )


def test_history_db_history_counts_statuses_and_duplicate_generated_at_values():
    duplicate_at = BASE_AT + timedelta(hours=1)
    rows = (
        _history_report(
            generated_at=BASE_AT,
            latest_action_status="research_ready",
        ),
        _history_report(
            generated_at=duplicate_at,
            latest_action_status="watch",
        ),
        _history_report(
            generated_at=duplicate_at,
            latest_action_status="blocked",
        ),
        _history_report(
            generated_at=BASE_AT + timedelta(hours=2),
            latest_action_status="watch",
        ),
    )

    history = _history(rows)

    assert history.action_status_counts == (
        ("research_ready", 1),
        ("watch", 2),
        ("blocked", 1),
    )
    assert history.duplicate_generated_at_count == 1


@pytest.mark.parametrize(
    ("latest_status", "expected_research_ready", "expected_watch", "expected_blocked"),
    (
        ("research_ready", 2, 0, 0),
        ("watch", 0, 2, 0),
        ("blocked", 0, 0, 2),
    ),
)
def test_history_db_history_computes_consecutive_latest_status_streaks(
    latest_status: str,
    expected_research_ready: int,
    expected_watch: int,
    expected_blocked: int,
):
    rows = (
        _history_report(
            generated_at=BASE_AT,
            latest_action_status="research_ready",
        ),
        _history_report(
            generated_at=BASE_AT + timedelta(hours=1),
            latest_action_status="watch" if latest_status != "watch" else "blocked",
        ),
        _history_report(
            generated_at=BASE_AT + timedelta(hours=2),
            latest_action_status=latest_status,
        ),
        _history_report(
            generated_at=BASE_AT + timedelta(hours=3),
            latest_action_status=latest_status,
        ),
    )

    history = _history(rows)

    assert history.latest_action_status == latest_status
    assert (
        history.consecutive_latest_research_ready_count
        == expected_research_ready
    )
    assert history.consecutive_latest_watch_count == expected_watch
    assert history.consecutive_latest_blocked_count == expected_blocked


def test_history_db_history_exposes_latest_ready_notional_delta_transitions_and_reasons():
    rows = (
        _history_report(
            generated_at=BASE_AT,
            latest_action_status="blocked",
            total_ready_notional=Decimal("12.500000"),
        ),
        _history_report(
            generated_at=BASE_AT + timedelta(hours=1),
            latest_action_status="research_ready",
            source_report_count=4,
            total_ready_notional=Decimal("18.125000"),
            status_transition_count=3,
            latest_reason_code_counts=(
                _reason_count("cycle_review_passed", 2),
                _reason_count("queue_depth_ready", 1),
            ),
        ),
    )

    history = _history(rows)

    assert history.latest_total_ready_notional == Decimal("18.125000")
    assert history.latest_ready_notional_delta == Decimal("5.625000")
    assert history.latest_status_transition_count == 3
    assert history.latest_reason_code_counts == (
        ("cycle_review_passed", 2),
        ("queue_depth_ready", 1),
    )
    assert type(history.latest_total_ready_notional) is Decimal
    assert type(history.latest_ready_notional_delta) is Decimal


def test_history_db_history_uses_history_fields_for_same_time_tie_order():
    first = _history_report(
        generated_at=BASE_AT,
        latest_action_status="research_ready",
        total_ready_notional=Decimal("1.000000"),
    )
    same_time_watch = _history_report(
        generated_at=BASE_AT + timedelta(hours=1),
        latest_action_status="watch",
        total_ready_notional=Decimal("2.000000"),
    )
    same_time_blocked = _history_report(
        generated_at=BASE_AT + timedelta(hours=1),
        latest_action_status="blocked",
        total_ready_notional=Decimal("3.000000"),
    )

    history = _history([same_time_watch, same_time_blocked, first])

    assert history.latest_history_generated_at == same_time_blocked.generated_at
    assert history.latest_action_status == "watch"
    assert history.latest_total_ready_notional == Decimal("2.000000")
    assert history.latest_ready_notional_delta == Decimal("-1.000000")


def test_history_db_history_rejects_non_container_wrong_type_subclasses_and_flags():
    row = _history_report(generated_at=BASE_AT)

    class ConfigSubclass(
        PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig,
    ):
        pass

    with pytest.raises(ValueError, match="history_reports must be a list or tuple"):
        build_paper_action_gated_strategy_recommendation_queue_history_db_history_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="history_reports must contain"):
        _history((object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="history_reports must contain"):
        _history((HistoryReportSubclass(**row.__dict__),))
    with pytest.raises(ValueError, match="config must be"):
        build_paper_action_gated_strategy_recommendation_queue_history_db_history_report(
            (),
            config=ConfigSubclass(config_version=CONFIG_VERSION),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_paper_action_gated_strategy_recommendation_queue_history_db_history_report(
            (),
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 21, 12, 0, tzinfo=UTC),
        )

    unsafe_row = _history_report(generated_at=BASE_AT + timedelta(hours=1))
    object.__setattr__(unsafe_row, "readonly", False)
    with pytest.raises(ValueError, match="readonly must be True"):
        _history((unsafe_row,))

    history = _history((row,))
    with pytest.raises(FrozenInstanceError):
        history.readonly = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        _config().config_version = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(history, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(history, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(history, readonly=False)


def test_history_db_history_rejects_non_decimal_and_wrong_precision_values():
    row = _history_report(generated_at=BASE_AT)

    non_decimal = _history_report(generated_at=BASE_AT + timedelta(hours=1))
    object.__setattr__(non_decimal, "total_ready_notional", "1.000000")
    with pytest.raises(ValueError, match="total_ready_notional must be a Decimal"):
        _history((row, non_decimal))

    wrong_precision = _history_report(generated_at=BASE_AT + timedelta(hours=2))
    object.__setattr__(
        wrong_precision,
        "total_ready_notional",
        Decimal("1.0000001"),
    )
    with pytest.raises(ValueError, match="total_ready_notional must use 0.000001"):
        _history((row, wrong_precision))

    history = _history(
        (
            row,
            _history_report(
                generated_at=BASE_AT + timedelta(hours=3),
                total_ready_notional=Decimal("2.000000"),
            ),
        ),
    )
    with pytest.raises(
        ValueError,
        match="latest_total_ready_notional must be a Decimal or None",
    ):
        replace(history, latest_total_ready_notional="2.000000")
    with pytest.raises(ValueError, match="latest_ready_notional_delta must use 0.000001"):
        replace(history, latest_ready_notional_delta=Decimal("0.0000001"))


def test_history_db_history_module_is_pure_readonly_ast():
    module_path = Path(module_under_test.__file__)
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    imported_names: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.append(node.module)
            imported_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    banned_module_fragments = (
        "psycopg",
        "supabase",
        "_db_row",
        "_env",
        "_load",
        "_loader",
        "_store",
        "_persist",
        "cli",
        "auth",
        "client",
        "exchange",
        "live_trading",
        "network",
        "order",
        "wallet",
    )
    banned_import_names = {
        "PaperActionGatedStrategyRecommendationQueueReport",
        "build_paper_action_gated_strategy_recommendation_queue_history_report",
        "build_paper_action_gated_strategy_recommendation_queue_report",
        "insert_paper_action_gated_strategy_recommendation_queue_history_report",
        "load_paper_action_gated_strategy_recommendation_queue_history_reports",
        "persist_paper_action_gated_strategy_recommendation_queue_history_report",
    }
    banned_call_or_attribute_names = {
        "api_key",
        "cancel",
        "connect",
        "create_order",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "insert",
        "load",
        "persist",
        "private_key",
        "replace_order",
        "sign",
        "submit",
        "wallet",
    }

    assert all(
        fragment not in module_name
        for module_name in imported_modules
        for fragment in banned_module_fragments
    )
    assert not (set(imported_names) & banned_import_names)
    assert not (set(call_names) & banned_call_or_attribute_names)
    assert not (set(attribute_names) & banned_call_or_attribute_names)

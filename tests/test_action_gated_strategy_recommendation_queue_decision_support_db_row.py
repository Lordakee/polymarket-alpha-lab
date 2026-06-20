from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_db_row import (
    PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow,
    paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row,
    paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueuePriorityRow,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskReport,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)


class PriorityReportSubclass(PaperActionGatedStrategyRecommendationQueuePriorityReport):
    pass


class RiskReportSubclass(PaperActionGatedStrategyRecommendationQueueRiskReport):
    pass


class DecisionSupportDbRowSubclass(
    PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow,
):
    pass


def _priority_row(
    *,
    priority_rank: int = 1,
    config_version: str = "action-gated-strategy-recommendation-queue-v0",
    action_status: str = "research_ready",
    recommended_next_step: str = "review_candidate_research_queue",
    research_priority: str = "research_review",
    candidate_count: int = 3,
    ready_count: int = 2,
    watch_count: int = 1,
    blocked_count: int = 0,
    total_ready_notional: Decimal = Decimal("42.000000"),
    top_queue_score: Decimal = Decimal("0.750000"),
    average_ready_score: Decimal = Decimal("0.500000"),
    research_priority_score: Decimal = Decimal("6.250000"),
) -> PaperActionGatedStrategyRecommendationQueuePriorityRow:
    return PaperActionGatedStrategyRecommendationQueuePriorityRow(
        priority_rank=priority_rank,
        source_generated_at=SOURCE_GENERATED_AT,
        config_version=config_version,
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status=action_status,
        recommended_next_step=recommended_next_step,
        research_priority=research_priority,
        candidate_count=candidate_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        total_ready_notional=total_ready_notional,
        top_queue_score=top_queue_score,
        average_ready_score=average_ready_score,
        research_priority_score=research_priority_score,
    )


def _priority_report() -> PaperActionGatedStrategyRecommendationQueuePriorityReport:
    ready_row = _priority_row()
    watch_row = _priority_row(
        priority_rank=2,
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        research_priority="await_fresh_context",
        candidate_count=1,
        ready_count=0,
        watch_count=1,
        blocked_count=0,
        total_ready_notional=Decimal("0.000000"),
        top_queue_score=Decimal("0.000000"),
        average_ready_score=Decimal("0.000000"),
        research_priority_score=Decimal("1.000000"),
    )
    return PaperActionGatedStrategyRecommendationQueuePriorityReport(
        generated_at=GENERATED_AT,
        source_report_count=2,
        research_ready_count=1,
        watch_count=1,
        blocked_count=0,
        total_ready_notional=Decimal("42.000000"),
        top_research_priority_score=Decimal("6.250000"),
        average_research_priority_score=Decimal("3.625000"),
        priority_rows=(ready_row, watch_row),
    )


def _multi_config_priority_report() -> PaperActionGatedStrategyRecommendationQueuePriorityReport:
    first_row = _priority_row(
        config_version="action-gated-strategy-recommendation-queue-a",
        candidate_count=1,
        ready_count=1,
        watch_count=0,
        total_ready_notional=Decimal("10.000000"),
        top_queue_score=Decimal("0.600000"),
        average_ready_score=Decimal("0.600000"),
        research_priority_score=Decimal("5.200000"),
    )
    second_row = _priority_row(
        priority_rank=2,
        config_version="action-gated-strategy-recommendation-queue-b",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        research_priority="await_fresh_context",
        candidate_count=1,
        ready_count=0,
        watch_count=1,
        blocked_count=0,
        total_ready_notional=Decimal("0.000000"),
        top_queue_score=Decimal("0.000000"),
        average_ready_score=Decimal("0.000000"),
        research_priority_score=Decimal("1.000000"),
    )
    return PaperActionGatedStrategyRecommendationQueuePriorityReport(
        generated_at=GENERATED_AT,
        source_report_count=2,
        research_ready_count=1,
        watch_count=1,
        blocked_count=0,
        total_ready_notional=Decimal("10.000000"),
        top_research_priority_score=Decimal("5.200000"),
        average_research_priority_score=Decimal("3.100000"),
        priority_rows=(first_row, second_row),
    )


def _risk_report() -> PaperActionGatedStrategyRecommendationQueueRiskReport:
    return PaperActionGatedStrategyRecommendationQueueRiskReport(
        generated_at=GENERATED_AT,
        config_version="action-gated-queue-risk-v0",
        source_config_versions=("action-gated-strategy-recommendation-queue-v0",),
        status="watch",
        recommended_next_step="throttle_paper_research_queue",
        reason_codes=("source_queue_watch",),
        source_queue_count=2,
        research_ready_source_count=1,
        watch_source_count=1,
        blocked_source_count=0,
        candidate_count=4,
        ready_count=2,
        watch_count=2,
        blocked_count=0,
        blocked_reason_count=0,
        watch_reason_count=1,
        total_ready_notional=Decimal("42.000000"),
        largest_queue_ready_notional=Decimal("42.000000"),
        total_ready_notional_utilization=Decimal("0.420000"),
        largest_queue_ready_notional_utilization=Decimal("0.700000"),
        max_total_ready_notional=Decimal("100.000000"),
        max_single_queue_ready_notional=Decimal("60.000000"),
        max_ready_candidate_count=5,
        max_total_candidate_count=10,
        throttle_utilization_threshold=Decimal("0.900000"),
    )


def test_decision_support_db_row_accepts_source_config_versions_as_set_semantics():
    priority_report = _multi_config_priority_report()
    risk_report = PaperActionGatedStrategyRecommendationQueueRiskReport(
        **{
            **_risk_report().__dict__,
            "source_config_versions": (
                "action-gated-strategy-recommendation-queue-b",
                "action-gated-strategy-recommendation-queue-a",
            ),
            "candidate_count": 2,
            "ready_count": 1,
            "watch_count": 1,
            "total_ready_notional": Decimal("10.000000"),
            "largest_queue_ready_notional": Decimal("10.000000"),
            "total_ready_notional_utilization": Decimal("0.100000"),
            "largest_queue_ready_notional_utilization": Decimal("0.166667"),
        },
    )

    row = paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
        priority_report,
        risk_report,
    )

    assert row.risk_payload_json["source_config_versions"] == [
        "action-gated-strategy-recommendation-queue-b",
        "action-gated-strategy-recommendation-queue-a",
    ]


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _row_values(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow,
) -> dict[str, object]:
    return dict(row.__dict__)


def test_decision_support_db_row_serializes_canonical_payloads_and_round_trips():
    priority_report = _priority_report()
    risk_report = _risk_report()

    row = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            priority_report,
            risk_report,
        )
    )

    assert type(row) is PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow
    assert len(row.snapshot_sha256) == 64
    assert row.snapshot_sha256 == row.snapshot_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.priority_source_report_count == 2
    assert row.priority_research_ready_count == 1
    assert row.priority_watch_count == 1
    assert row.priority_blocked_count == 0
    assert row.priority_total_ready_notional == Decimal("42.000000")
    assert row.top_research_priority_score == Decimal("6.250000")
    assert row.average_research_priority_score == Decimal("3.625000")
    assert row.risk_config_version == "action-gated-queue-risk-v0"
    assert row.risk_status == "watch"
    assert row.risk_recommended_next_step == "throttle_paper_research_queue"
    assert row.risk_source_queue_count == 2
    assert row.risk_candidate_count == 4
    assert row.risk_ready_count == 2
    assert row.risk_total_ready_notional == Decimal("42.000000")
    assert row.risk_largest_queue_ready_notional == Decimal("42.000000")
    assert row.risk_reason_codes_json == ["source_queue_watch"]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.priority_payload_json["generated_at"] == "2026-06-20T12:00:00+00:00"
    assert row.priority_payload_json["total_ready_notional"] == "42.000000"
    assert row.priority_payload_json["priority_rows"][0]["source_generated_at"] == (
        "2026-06-20T11:00:00+00:00"
    )
    assert row.priority_payload_json["priority_rows"][0][
        "research_priority_score"
    ] == "6.250000"
    assert row.risk_payload_json["generated_at"] == "2026-06-20T12:00:00+00:00"
    assert row.risk_payload_json["total_ready_notional_utilization"] == "0.420000"
    assert row.risk_payload_json["reason_codes"] == ["source_queue_watch"]
    assert row.priority_payload_json["paper_only"] is True
    assert row.priority_payload_json["priority_rows"][0]["readonly"] is True
    assert row.risk_payload_json["report_only"] is True
    assert row.risk_payload_json["readonly"] is True
    _assert_no_floats(row.priority_payload_json)
    _assert_no_floats(row.risk_payload_json)

    encoded = json.dumps(
        {
            "priority_payload_json": row.priority_payload_json,
            "risk_payload_json": row.risk_payload_json,
        },
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.snapshot_sha256 == hashlib.sha256(encoded).hexdigest()
    assert (
        paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row(
            row,
        )
        == (priority_report, risk_report)
    )


def test_decision_support_db_row_hash_is_deterministic_for_equivalent_reports():
    priority_report = _priority_report()
    risk_report = _risk_report()
    same_priority_report = PaperActionGatedStrategyRecommendationQueuePriorityReport(
        **priority_report.__dict__,
    )
    same_risk_report = PaperActionGatedStrategyRecommendationQueueRiskReport(
        **risk_report.__dict__,
    )
    different_risk_report = PaperActionGatedStrategyRecommendationQueueRiskReport(
        **{
            **risk_report.__dict__,
            "config_version": "action-gated-queue-risk-v1",
        },
    )

    first = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            priority_report,
            risk_report,
        )
    )
    second = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            same_priority_report,
            same_risk_report,
        )
    )
    third = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            priority_report,
            different_risk_report,
        )
    )

    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.priority_payload_json == second.priority_payload_json
    assert first.risk_payload_json == second.risk_payload_json
    assert first.snapshot_sha256 != third.snapshot_sha256


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (
            lambda priority_report, risk_report: object.__setattr__(
                risk_report,
                "source_queue_count",
                3,
            ),
            "priority_report.source_report_count.*risk_report.source_queue_count",
        ),
        (
            lambda priority_report, risk_report: object.__setattr__(
                risk_report,
                "source_config_versions",
                ("different-action-gated-strategy-recommendation-queue-v0",),
            ),
            "priority_rows.config_version.*risk_report.source_config_versions",
        ),
        (
            lambda priority_report, risk_report: object.__setattr__(
                risk_report,
                "research_ready_source_count",
                2,
            ),
            (
                "priority_report.research_ready_count.*"
                "risk_report.research_ready_source_count"
            ),
        ),
        (
            lambda priority_report, risk_report: object.__setattr__(
                risk_report,
                "watch_source_count",
                2,
            ),
            "priority_report.watch_count.*risk_report.watch_source_count",
        ),
        (
            lambda priority_report, risk_report: object.__setattr__(
                risk_report,
                "blocked_source_count",
                1,
            ),
            "priority_report.blocked_count.*risk_report.blocked_source_count",
        ),
        (
            lambda priority_report, risk_report: object.__setattr__(
                risk_report,
                "total_ready_notional",
                Decimal("43.000000"),
            ),
            (
                "priority_report.total_ready_notional.*"
                "risk_report.total_ready_notional"
            ),
        ),
        (
            lambda priority_report, risk_report: object.__setattr__(
                risk_report,
                "candidate_count",
                5,
            ),
            "sum\\(priority_rows.candidate_count\\).*risk_report.candidate_count",
        ),
        (
            lambda priority_report, risk_report: object.__setattr__(
                priority_report.priority_rows[0],
                "ready_count",
                3,
            ),
            "sum\\(priority_rows.ready_count\\).*risk_report.ready_count",
        ),
        (
            lambda priority_report, risk_report: object.__setattr__(
                priority_report.priority_rows[1],
                "watch_count",
                2,
            ),
            "sum\\(priority_rows.watch_count\\).*risk_report.watch_count",
        ),
        (
            lambda priority_report, risk_report: object.__setattr__(
                priority_report.priority_rows[0],
                "blocked_count",
                1,
            ),
            "sum\\(priority_rows.blocked_count\\).*risk_report.blocked_count",
        ),
    ),
)
def test_decision_support_db_row_rejects_cross_report_snapshot_mismatches(
    mutate,
    message: str,
):
    priority_report = _priority_report()
    risk_report = _risk_report()
    mutate(priority_report, risk_report)

    with pytest.raises(ValueError, match=message):
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            priority_report,
            risk_report,
        )


def test_decision_support_db_row_is_frozen():
    row = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            _priority_report(),
            _risk_report(),
        )
    )

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_decision_support_db_row_rejects_wrong_report_types_and_subclasses():
    with pytest.raises(ValueError, match="PriorityReport"):
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            object(),
            _risk_report(),
        )
    with pytest.raises(ValueError, match="RiskReport"):
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            _priority_report(),
            object(),
        )

    priority_report = _priority_report()
    risk_report = _risk_report()
    with pytest.raises(ValueError, match="PriorityReport"):
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            PriorityReportSubclass(**priority_report.__dict__),
            risk_report,
        )
    with pytest.raises(ValueError, match="RiskReport"):
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            priority_report,
            RiskReportSubclass(**risk_report.__dict__),
        )


def test_decision_support_db_row_rejects_wrong_row_type_and_subclasses():
    row = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            _priority_report(),
            _risk_report(),
        )
    )

    with pytest.raises(ValueError, match="DecisionSupportDbRow"):
        paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row(
            object(),
        )
    with pytest.raises(ValueError, match="DecisionSupportDbRow"):
        paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row(
            DecisionSupportDbRowSubclass(**_row_values(row)),
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_decision_support_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
):
    priority_report = _priority_report()
    risk_report = _risk_report()
    object.__setattr__(priority_report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            priority_report,
            risk_report,
        )


def test_decision_support_db_row_rejects_deep_false_priority_row_flags_before_write():
    priority_report = _priority_report()
    risk_report = _risk_report()
    object.__setattr__(priority_report.priority_rows[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            priority_report,
            risk_report,
        )


def test_decision_support_db_row_rejects_false_risk_report_flags_before_write():
    priority_report = _priority_report()
    risk_report = _risk_report()
    object.__setattr__(risk_report, "report_only", False)

    with pytest.raises(ValueError, match="report_only"):
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            priority_report,
            risk_report,
        )


def test_decision_support_db_row_rejects_corrupted_stored_payload_flags():
    row = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            _priority_report(),
            _risk_report(),
        )
    )
    malformed = PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow(
        **{
            **_row_values(row),
            "priority_payload_json": {
                **row.priority_payload_json,
                "priority_rows": [
                    {**row.priority_payload_json["priority_rows"][0], "readonly": False},
                    row.priority_payload_json["priority_rows"][1],
                ],
            },
        },
    )

    with pytest.raises(ValueError, match="readonly"):
        paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row(
            malformed,
        )


def test_decision_support_db_row_rejects_floats_in_json_columns():
    row = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            _priority_report(),
            _risk_report(),
        )
    )

    with pytest.raises(ValueError, match="priority_payload_json"):
        PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow(
            **{
                **_row_values(row),
                "priority_payload_json": {
                    **row.priority_payload_json,
                    "bad_float": 0.1,
                },
            },
        )

    with pytest.raises(ValueError, match="risk_payload_json"):
        PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow(
            **{
                **_row_values(row),
                "risk_payload_json": {
                    **row.risk_payload_json,
                    "bad_float": 0.1,
                },
            },
        )


@pytest.mark.parametrize(
    "risk_reason_codes_json",
    (
        ["queue_risk_passed", "queue_risk_passed"],
        ["bad risk reason"],
        {"bad risk reason": True},
    ),
)
def test_decision_support_db_row_rejects_duplicate_or_invalid_risk_reason_codes(
    risk_reason_codes_json: object,
):
    row = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            _priority_report(),
            _risk_report(),
        )
    )

    with pytest.raises(ValueError, match="risk_reason_codes_json"):
        PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow(
            **{**_row_values(row), "risk_reason_codes_json": risk_reason_codes_json},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"snapshot_sha256": "b" * 64}, "snapshot_sha256"),
        ({"generated_at": datetime(2026, 6, 20, 12, 1, tzinfo=UTC)}, "generated_at"),
        ({"priority_source_report_count": 3}, "priority_source_report_count"),
        ({"priority_total_ready_notional": Decimal("43.000000")}, "priority_total"),
        (
            {
                "risk_status": "pass",
                "risk_recommended_next_step": "allocate_paper_research_queue",
            },
            "risk_status",
        ),
        ({"risk_candidate_count": 5}, "risk_candidate_count"),
        ({"risk_reason_codes_json": ["queue_risk_passed"]}, "risk_reason_codes_json"),
    ),
)
def test_decision_support_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
):
    row = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            _priority_report(),
            _risk_report(),
        )
    )
    malformed = PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row(
            malformed,
        )


def test_decision_support_db_row_wraps_payload_recovery_errors_as_value_error():
    row = (
        paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
            _priority_report(),
            _risk_report(),
        )
    )
    malformed = PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow(
        **{
            **_row_values(row),
            "risk_payload_json": {
                key: value
                for key, value in row.risk_payload_json.items()
                if key != "reason_codes"
            },
        },
    )

    with pytest.raises(ValueError, match="risk_payload_json"):
        paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row(
            malformed,
        )


def test_decision_support_db_row_module_is_pure_codec():
    module_path = Path(
        "src/polymarket_alpha_lab/"
        "action_gated_strategy_recommendation_queue_decision_support_db_row.py",
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

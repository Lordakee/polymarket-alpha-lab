from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueConfig,
    PaperActionGatedStrategyRecommendationQueueReport,
    build_paper_action_gated_strategy_recommendation_queue_report,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_db_row import (
    PaperActionGatedStrategyRecommendationQueueDbRow,
    paper_action_gated_strategy_recommendation_queue_report_from_db_row,
    paper_action_gated_strategy_recommendation_queue_report_to_db_row,
)
from polymarket_alpha_lab.candidate_assessment import PaperCandidateAssessmentConfig
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventMarketSnapshot,
    PaperCostAwareEventStrategyConfig,
    build_paper_cost_aware_event_strategy_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
    PaperRecommendationCycleActionGateReport,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyConfig,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningConfig,
    build_paper_project_screening_report,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationConfig,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleConfig,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)


class QueueReportSubclass(PaperActionGatedStrategyRecommendationQueueReport):
    pass


def _reason_count(
    reason_code: str,
    count: int,
) -> PaperRecommendationCycleActionGateReasonCodeCount:
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def _action_gate_report(
    *,
    review_status: str = "pass",
    latest_final_status: str | None = "pass",
    action_status: str = "research_ready",
    recommended_next_step: str = "build_candidate_research_queue",
    missing_required_artifact_count: int = 0,
    blocked_reason_count: int = 0,
    watch_reason_count: int = 0,
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...]
    | None = None,
) -> PaperRecommendationCycleActionGateReport:
    if reason_code_counts is None:
        reason_code_counts = (_reason_count(f"cycle_review_{review_status}", 1),)
    return PaperRecommendationCycleActionGateReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-cycle-action-gate-v0",
        source_config_version="paper-recommendation-cycle-review-v0",
        review_status=review_status,
        latest_final_status=latest_final_status,
        action_status=action_status,
        recommended_next_step=recommended_next_step,
        missing_required_artifact_count=missing_required_artifact_count,
        blocked_reason_count=blocked_reason_count,
        watch_reason_count=watch_reason_count,
        reason_code_counts=reason_code_counts,
    )


def _cost_assumptions(**overrides):
    values = {
        "taker_fee_rate": Decimal("0.0000"),
        "slippage_cost_per_share": Decimal("0.0000"),
        "funding_cost_per_share": Decimal("0.0000"),
        "finalization_cost_per_share": Decimal("0.0000"),
        "time_cost_per_share": Decimal("0.0000"),
        "risk_cost_per_share": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperCostAwareEventCostAssumptions(**values)


def _cost_aware_config(**overrides):
    values = {
        "config_version": "cost-aware-event-v1",
        "min_confidence": Decimal("0.7000"),
        "max_spread": Decimal("0.0500"),
        "max_resolution_risk": Decimal("0.2000"),
        "min_ask_size": Decimal("10.0000"),
        "min_net_edge": Decimal("0.0100"),
    }
    values.update(overrides)
    return PaperCostAwareEventStrategyConfig(**values)


def _cost_report(**overrides):
    values = {
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "fair_probability_yes": Decimal("0.6300"),
        "confidence": Decimal("0.9000"),
        "yes_bid": Decimal("0.5400"),
        "yes_ask": Decimal("0.5500"),
        "yes_ask_size": Decimal("250.0000"),
        "no_bid": Decimal("0.4400"),
        "no_ask": Decimal("0.5000"),
        "no_ask_size": Decimal("200.0000"),
        "spread": Decimal("0.0100"),
        "resolution_risk": Decimal("0.0200"),
        "risk_cost_per_share": Decimal("0.0000"),
        "min_net_edge": Decimal("0.0100"),
        "generated_at": SOURCE_GENERATED_AT,
    }
    values.update(overrides)
    snapshot = PaperCostAwareEventMarketSnapshot(
        market_slug=values["market_slug"],
        question=values["question"],
        fair_probability_yes=values["fair_probability_yes"],
        confidence=values["confidence"],
        yes_bid=values["yes_bid"],
        yes_ask=values["yes_ask"],
        yes_ask_size=values["yes_ask_size"],
        no_bid=values["no_bid"],
        no_ask=values["no_ask"],
        no_ask_size=values["no_ask_size"],
        spread=values["spread"],
        resolution_risk=values["resolution_risk"],
    )
    return build_paper_cost_aware_event_strategy_report(
        snapshot,
        cost_assumptions=_cost_assumptions(
            risk_cost_per_share=values["risk_cost_per_share"],
        ),
        config=_cost_aware_config(min_net_edge=values["min_net_edge"]),
        generated_at=values["generated_at"],
    )


def _screening_config(**overrides):
    values = {
        "config_version": "project-screening-v1",
        "min_screening_score": Decimal("0.010000"),
        "reference_ask_size": Decimal("100.0000"),
        "net_edge_weight": Decimal("1.0000"),
        "confidence_weight": Decimal("0.0000"),
        "depth_weight": Decimal("0.0000"),
        "spread_penalty_weight": Decimal("0.0000"),
        "resolution_risk_penalty_weight": Decimal("0.0000"),
        "cost_penalty_weight": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperProjectScreeningConfig(**values)


def _screening_report(cost_reports):
    return build_paper_project_screening_report(
        cost_reports,
        config=_screening_config(),
        generated_at=SOURCE_GENERATED_AT,
    )


def _config() -> PaperActionGatedStrategyRecommendationQueueConfig:
    return PaperActionGatedStrategyRecommendationQueueConfig(
        config_version="action-gated-strategy-recommendation-queue-v0",
        candidate_assessment_config=PaperCandidateAssessmentConfig(
            config_version="candidate-assessment-v1",
            min_ready_score=Decimal("0.010000"),
            max_total_cost_per_share=Decimal("0.050000"),
        ),
        readiness_config_version="strategy-readiness-state-v1",
        bundle_config=PaperStrategyRecommendationBundleConfig(
            config_version="strategy-recommendation-bundle-v1",
            recommendation_config=PaperStrategyCandidateRecommendationConfig(
                config_version="strategy-candidate-recommendation-v1",
                min_recommendation_score=Decimal("0.100000"),
            ),
            selection_policy_config=PaperStrategySelectionPolicyConfig(
                config_version="strategy-selection-policy-v1",
                base_position_notional=Decimal("20.000000"),
                max_position_notional=Decimal("12.000000"),
                max_total_notional=Decimal("20.000000"),
            ),
        ),
    )


def _build_report(
    action_gate_report,
    screening_report,
    cost_reports,
    *,
    config=None,
    generated_at=GENERATED_AT,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    return build_paper_action_gated_strategy_recommendation_queue_report(
        action_gate_report,
        screening_report,
        cost_reports,
        config=config or _config(),
        generated_at=generated_at,
    )


def _ready_report() -> PaperActionGatedStrategyRecommendationQueueReport:
    ready = _cost_report(
        market_slug="alpha-ready",
        question="Will alpha resolve yes?",
        fair_probability_yes=Decimal("0.6300"),
        yes_ask=Decimal("0.5500"),
    )
    watch = _cost_report(
        market_slug="beta-watch",
        question="Will beta resolve yes?",
        fair_probability_yes=Decimal("0.5600"),
        yes_ask=Decimal("0.5500"),
        min_net_edge=Decimal("0.0200"),
    )
    blocked = _cost_report(
        market_slug="gamma-blocked",
        question="Will gamma resolve yes?",
        fair_probability_yes=Decimal("0.6800"),
        yes_ask=Decimal("0.5500"),
        risk_cost_per_share=Decimal("0.0600"),
    )
    return _build_report(
        _action_gate_report(),
        _screening_report((ready, watch, blocked)),
        (ready, watch, blocked),
    )


def _watch_report() -> PaperActionGatedStrategyRecommendationQueueReport:
    gate = _action_gate_report(
        review_status="watch",
        latest_final_status="watch",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        watch_reason_count=2,
        reason_code_counts=(
            _reason_count("cycle_history_stale", 1),
            _reason_count("cycle_review_watch", 1),
        ),
    )
    cost_report = _cost_report()
    return _build_report(gate, _screening_report((cost_report,)), (cost_report,))


def _blocked_report() -> PaperActionGatedStrategyRecommendationQueueReport:
    gate = _action_gate_report(
        review_status="blocked",
        latest_final_status="blocked",
        action_status="blocked",
        recommended_next_step="repair_cycle_evidence",
        blocked_reason_count=2,
        reason_code_counts=(
            _reason_count("cycle_review_blocked", 1),
            _reason_count("pipeline_final_status_blocked", 1),
        ),
    )
    cost_report = _cost_report()
    return _build_report(gate, _screening_report((cost_report,)), (cost_report,))


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return __import__("hashlib").sha256(encoded).hexdigest()


def _row_values(
    row: PaperActionGatedStrategyRecommendationQueueDbRow,
) -> dict[str, object]:
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "source_config_version": row.source_config_version,
        "action_status": row.action_status,
        "recommended_next_step": row.recommended_next_step,
        "candidate_count": row.candidate_count,
        "ready_count": row.ready_count,
        "watch_count": row.watch_count,
        "blocked_count": row.blocked_count,
        "total_ready_notional": row.total_ready_notional,
        "reason_code_counts_json": row.reason_code_counts_json,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _bypassed_queue_row(
    row: PaperActionGatedStrategyRecommendationQueueDbRow,
    **overrides: object,
) -> PaperActionGatedStrategyRecommendationQueueDbRow:
    values = _row_values(row)
    values.update(overrides)
    bypassed = object.__new__(PaperActionGatedStrategyRecommendationQueueDbRow)
    for field_name, value in values.items():
        object.__setattr__(bypassed, field_name, value)
    return bypassed


def test_action_gated_queue_db_row_serializes_ready_payload_and_round_trips():
    report = _ready_report()

    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(report)

    assert type(row) is PaperActionGatedStrategyRecommendationQueueDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "action-gated-strategy-recommendation-queue-v0"
    assert row.source_config_version == "paper-recommendation-cycle-action-gate-v0"
    assert row.action_status == "research_ready"
    assert row.recommended_next_step == "review_candidate_research_queue"
    assert row.candidate_count == 3
    assert row.ready_count == 1
    assert row.watch_count == 1
    assert row.blocked_count == 1
    assert row.total_ready_notional == report.total_ready_notional
    assert row.reason_code_counts_json == {"cycle_review_pass": 1}
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-20T12:00:00+00:00"
    assert row.payload_json["total_ready_notional"] == str(report.total_ready_notional)
    assert row.payload_json["candidate_assessment_report"]["assessment_rows"][0][
        "screening_score"
    ] == "0.080000"
    assert row.payload_json["bundle_report"]["selection_policy_report"][
        "total_selected_notional"
    ] == str(report.total_ready_notional)
    assert row.payload_json["queue_summary_report"]["queue_rows"][0][
        "suggested_notional"
    ] == str(report.total_ready_notional)
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.payload_json["candidate_assessment_report"]["readonly"] is True
    assert row.payload_json["bundle_report"]["readonly"] is True
    assert row.payload_json["queue_summary_report"]["readonly"] is True
    _assert_no_floats(row.payload_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert paper_action_gated_strategy_recommendation_queue_report_from_db_row(row) == report
    assert paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        report,
    ).report_sha256 == row.report_sha256
    assert row.report_sha256 == __import__("hashlib").sha256(encoded).hexdigest()


def test_action_gated_queue_db_row_serializes_watch_payload_and_round_trips():
    report = _watch_report()

    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(report)

    assert row.action_status == "watch"
    assert row.recommended_next_step == "await_fresh_cycle_evidence"
    assert row.candidate_count == 0
    assert row.ready_count == 0
    assert row.watch_count == 0
    assert row.blocked_count == 0
    assert row.total_ready_notional == Decimal("0.000000")
    assert row.reason_code_counts_json == {
        "cycle_history_stale": 1,
        "cycle_review_watch": 1,
    }
    assert row.payload_json["candidate_assessment_report"] is None
    assert row.payload_json["bundle_report"] is None
    assert row.payload_json["queue_summary_report"] is None
    assert row.payload_json["total_ready_notional"] == "0.000000"
    _assert_no_floats(row.payload_json)

    assert paper_action_gated_strategy_recommendation_queue_report_from_db_row(row) == report


def test_action_gated_queue_db_row_serializes_blocked_payload_and_round_trips():
    report = _blocked_report()

    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(report)

    assert row.action_status == "blocked"
    assert row.recommended_next_step == "repair_cycle_evidence"
    assert row.candidate_count == 0
    assert row.ready_count == 0
    assert row.watch_count == 0
    assert row.blocked_count == 0
    assert row.total_ready_notional == Decimal("0.000000")
    assert row.reason_code_counts_json == {
        "cycle_review_blocked": 1,
        "pipeline_final_status_blocked": 1,
    }
    assert row.payload_json["candidate_assessment_report"] is None
    assert row.payload_json["bundle_report"] is None
    assert row.payload_json["queue_summary_report"] is None
    assert row.payload_json["total_ready_notional"] == "0.000000"
    _assert_no_floats(row.payload_json)

    assert paper_action_gated_strategy_recommendation_queue_report_from_db_row(row) == report


def test_action_gated_queue_db_row_hash_uses_canonical_full_payload():
    report = _ready_report()
    same_report = PaperActionGatedStrategyRecommendationQueueReport(**report.__dict__)
    different_payload = _watch_report()

    first = paper_action_gated_strategy_recommendation_queue_report_to_db_row(report)
    second = paper_action_gated_strategy_recommendation_queue_report_to_db_row(same_report)
    third = paper_action_gated_strategy_recommendation_queue_report_to_db_row(different_payload)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_action_gated_queue_db_row_is_frozen():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )

    with pytest.raises(FrozenInstanceError):
        row.paper_only = False  # type: ignore[misc]


def test_action_gated_queue_db_row_rejects_wrong_report_type_and_subclasses():
    with pytest.raises(ValueError, match="PaperActionGatedStrategyRecommendationQueueReport"):
        paper_action_gated_strategy_recommendation_queue_report_to_db_row(object())

    report = _watch_report()
    subclass = QueueReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperActionGatedStrategyRecommendationQueueReport"):
        paper_action_gated_strategy_recommendation_queue_report_to_db_row(subclass)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_action_gated_queue_db_row_rejects_false_report_flags(flag_name: str):
    report = _watch_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        paper_action_gated_strategy_recommendation_queue_report_to_db_row(report)


def test_action_gated_queue_db_row_rejects_deep_false_report_flags_before_write():
    report = _ready_report()
    assert report.bundle_report is not None
    nested_report = report.bundle_report.recommendation_report
    object.__setattr__(nested_report, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        paper_action_gated_strategy_recommendation_queue_report_to_db_row(report)


def test_action_gated_queue_db_row_rejects_duplicate_reason_code_counts_before_write():
    report = _watch_report()
    object.__setattr__(
        report,
        "reason_code_counts",
        (
            _reason_count("cycle_review_watch", 1),
            _reason_count("cycle_review_watch", 2),
        ),
    )

    with pytest.raises(ValueError, match="reason_code_counts"):
        paper_action_gated_strategy_recommendation_queue_report_to_db_row(report)


def test_action_gated_queue_db_row_constructor_rejects_unsafe_stored_flags():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )
    payload_json = {**row.payload_json, "readonly": False}

    with pytest.raises(ValueError, match="readonly"):
        PaperActionGatedStrategyRecommendationQueueDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_db_row_constructor_rejects_nested_payload_flags():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _ready_report(),
    )
    candidate_assessment_report = dict(row.payload_json["candidate_assessment_report"])
    candidate_assessment_report["readonly"] = False
    payload_json = {
        **row.payload_json,
        "candidate_assessment_report": candidate_assessment_report,
    }

    with pytest.raises(ValueError, match="readonly"):
        PaperActionGatedStrategyRecommendationQueueDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_db_row_constructor_rejects_payload_that_cannot_recover():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )
    payload_json = {**row.payload_json, "unexpected_field": "not-a-report-field"}

    with pytest.raises(ValueError, match="payload_json"):
        PaperActionGatedStrategyRecommendationQueueDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_db_row_constructor_rejects_bool_payload_int_count():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _ready_report(),
    )
    payload_json = {**row.payload_json, "ready_count": True}

    with pytest.raises(ValueError, match="payload_json|ready_count"):
        PaperActionGatedStrategyRecommendationQueueDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_db_row_constructor_rejects_self_hashed_noncanonical_decimal():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )
    payload_json = {**row.payload_json, "total_ready_notional": "0"}

    with pytest.raises(ValueError, match="payload_json|total_ready_notional"):
        PaperActionGatedStrategyRecommendationQueueDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "total_ready_notional": Decimal("0"),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_db_row_replace_revalidates_payload_consistency():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )

    with pytest.raises(ValueError, match="candidate_count"):
        replace(row, candidate_count=row.candidate_count + 1)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 20, 12, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "different-action-gated-queue-v0"}, "config_version"),
        (
            {"source_config_version": "different-cycle-action-gate-v0"},
            "source_config_version",
        ),
        (
            {
                "action_status": "blocked",
                "recommended_next_step": "repair_cycle_evidence",
            },
            "action_status",
        ),
        ({"candidate_count": 1}, "candidate_count"),
        ({"ready_count": 1}, "ready_count"),
        ({"watch_count": 1}, "watch_count"),
        ({"blocked_count": 1}, "blocked_count"),
        ({"total_ready_notional": Decimal("1.000000")}, "total_ready_notional"),
        ({"reason_code_counts_json": {"cycle_history_stale": 2}}, "reason_code_counts"),
    ),
)
def test_action_gated_queue_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )
    values = _row_values(row)
    values.update(overrides)

    with pytest.raises(ValueError, match=message):
        PaperActionGatedStrategyRecommendationQueueDbRow(**values)


def test_action_gated_queue_db_row_from_db_row_rejects_bypassed_payload_mismatch():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )
    malformed = _bypassed_queue_row(row, candidate_count=row.candidate_count + 1)

    with pytest.raises(ValueError, match="candidate_count"):
        paper_action_gated_strategy_recommendation_queue_report_from_db_row(malformed)


def test_action_gated_queue_db_row_from_db_row_rejects_bypassed_payload_recovery_error():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )
    payload_json = {**row.payload_json, "unexpected_field": "not-a-report-field"}
    malformed = _bypassed_queue_row(
        row,
        report_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match="payload_json"):
        paper_action_gated_strategy_recommendation_queue_report_from_db_row(malformed)


def test_action_gated_queue_db_row_from_db_row_rejects_bypassed_bool_materialized_int():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _ready_report(),
    )
    malformed = _bypassed_queue_row(row, ready_count=True)

    with pytest.raises(ValueError, match="ready_count"):
        paper_action_gated_strategy_recommendation_queue_report_from_db_row(malformed)


def test_action_gated_queue_db_row_from_db_row_rejects_bypassed_bool_materialized_reason_count():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _ready_report(),
    )
    malformed = _bypassed_queue_row(
        row,
        reason_code_counts_json={"cycle_review_pass": True},
    )

    with pytest.raises(ValueError, match="reason_code_counts_json"):
        paper_action_gated_strategy_recommendation_queue_report_from_db_row(malformed)


def test_action_gated_queue_db_row_from_db_row_rejects_bypassed_noncanonical_materialized_decimal():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )
    malformed = _bypassed_queue_row(row, total_ready_notional=Decimal("0"))

    with pytest.raises(ValueError, match="total_ready_notional"):
        paper_action_gated_strategy_recommendation_queue_report_from_db_row(malformed)


def test_action_gated_queue_db_row_from_db_row_rejects_bypassed_missing_nested_payload_hard_flag():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _ready_report(),
    )
    candidate_assessment_report = dict(row.payload_json["candidate_assessment_report"])
    del candidate_assessment_report["readonly"]
    payload_json = {
        **row.payload_json,
        "candidate_assessment_report": candidate_assessment_report,
    }
    malformed = _bypassed_queue_row(
        row,
        report_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match="readonly"):
        paper_action_gated_strategy_recommendation_queue_report_from_db_row(malformed)


def test_action_gated_queue_db_row_from_db_row_rejects_bypassed_missing_all_nested_payload_hard_flags():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _ready_report(),
    )
    candidate_assessment_report = {
        key: value
        for key, value in row.payload_json["candidate_assessment_report"].items()
        if key not in ("paper_only", "report_only", "readonly")
    }
    payload_json = {
        **row.payload_json,
        "candidate_assessment_report": candidate_assessment_report,
    }
    malformed = _bypassed_queue_row(
        row,
        report_sha256=row.report_sha256,
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match="report_sha256|payload_json"):
        paper_action_gated_strategy_recommendation_queue_report_from_db_row(malformed)


def test_action_gated_queue_db_row_wraps_payload_recovery_errors_as_value_error():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )
    payload_json = {
            key: value
            for key, value in row.payload_json.items()
            if key != "reason_code_counts"
        }

    with pytest.raises(ValueError, match="payload_json"):
        PaperActionGatedStrategyRecommendationQueueDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_db_row_validates_row_shape_and_rejects_floats():
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
        _watch_report(),
    )

    with pytest.raises(ValueError, match="report_sha256"):
        PaperActionGatedStrategyRecommendationQueueDbRow(
            report_sha256="bad",
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_config_version=row.source_config_version,
            action_status=row.action_status,
            recommended_next_step=row.recommended_next_step,
            candidate_count=row.candidate_count,
            ready_count=row.ready_count,
            watch_count=row.watch_count,
            blocked_count=row.blocked_count,
            total_ready_notional=row.total_ready_notional,
            reason_code_counts_json=row.reason_code_counts_json,
            payload_json=row.payload_json,
        )

    with pytest.raises(ValueError, match="payload_json"):
        PaperActionGatedStrategyRecommendationQueueDbRow(
            report_sha256="a" * 64,
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_config_version=row.source_config_version,
            action_status=row.action_status,
            recommended_next_step=row.recommended_next_step,
            candidate_count=row.candidate_count,
            ready_count=row.ready_count,
            watch_count=row.watch_count,
            blocked_count=row.blocked_count,
            total_ready_notional=row.total_ready_notional,
            reason_code_counts_json=row.reason_code_counts_json,
            payload_json={**row.payload_json, "bad_float": 0.1},
        )

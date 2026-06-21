from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)
from polymarket_alpha_lab.strategy_candidate_research_queue_db_row import (
    PaperStrategyCandidateResearchQueueDbRow,
    paper_strategy_candidate_research_queue_report_from_db_row,
    paper_strategy_candidate_research_queue_report_to_db_row,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 30, tzinfo=UTC)


class ResearchQueueReportSubclass(PaperStrategyCandidateResearchQueueReport):
    pass


class ResearchQueueDbRowSubclass(PaperStrategyCandidateResearchQueueDbRow):
    pass


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
        _research_row(
            research_rank=3,
            queue_rank=3,
            market_slug="gamma-blocked",
            question="Will gamma resolve yes?",
            source_action="reject",
            decision="not_selected",
            queue_status="blocked",
            research_status="blocked",
            recommendation_score=Decimal("0.100000"),
            readiness_score=Decimal("0.100000"),
            suggested_notional=Decimal("0.000000"),
            selected_position_notional=Decimal("0.000000"),
            primary_reason_code="high_cost",
            evidence_gap_codes=("high_cost",),
            reason_codes=("high_cost",),
            selected_side="none",
        ),
    )
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=GENERATED_AT,
        config_version="strategy-candidate-research-queue-v0",
        source_config_version="action-gated-strategy-recommendation-queue-v0",
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
        source_reason_code_counts=(_source_reason_count("cycle_review_pass", 1),),
        research_status="ready",
        candidate_count=3,
        research_ready_count=1,
        watch_count=1,
        blocked_count=1,
        selected_count=1,
        skipped_count=1,
        not_selected_count=1,
        total_ready_notional=Decimal("12.000000"),
        total_selected_notional=Decimal("12.000000"),
        total_suggested_notional=Decimal("12.000000"),
        top_research_priority_score=Decimal("0.800000"),
        average_research_ready_score=Decimal("0.800000"),
        primary_reason_code_counts=(
            ("high_cost", 1),
            ("low_net_edge", 1),
            ("recommendation_ready", 1),
        ),
        rows=rows,
        reason_codes=("candidate_research_queue_ready",),
    )


def _watch_report() -> PaperStrategyCandidateResearchQueueReport:
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=GENERATED_AT,
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


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _row_values(row: PaperStrategyCandidateResearchQueueDbRow) -> dict[str, object]:
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
        "source_reason_code_counts_json": row.source_reason_code_counts_json,
        "primary_reason_code_counts_json": row.primary_reason_code_counts_json,
        "reason_codes_json": row.reason_codes_json,
        "rows_json": row.rows_json,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def test_research_queue_db_row_serializes_ready_payload_and_round_trips_exact_report():
    report = _ready_report()

    row = paper_strategy_candidate_research_queue_report_to_db_row(report)

    assert type(row) is PaperStrategyCandidateResearchQueueDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "strategy-candidate-research-queue-v0"
    assert row.source_config_version == "action-gated-strategy-recommendation-queue-v0"
    assert row.action_status == "research_ready"
    assert row.recommended_next_step == "review_candidate_research_queue"
    assert row.research_status == "ready"
    assert row.candidate_count == 3
    assert row.research_ready_count == 1
    assert row.watch_count == 1
    assert row.blocked_count == 1
    assert row.selected_count == 1
    assert row.skipped_count == 1
    assert row.not_selected_count == 1
    assert row.total_ready_notional == Decimal("12.000000")
    assert row.total_selected_notional == Decimal("12.000000")
    assert row.total_suggested_notional == Decimal("12.000000")
    assert row.top_research_priority_score == Decimal("0.800000")
    assert row.average_research_ready_score == Decimal("0.800000")
    assert row.source_reason_code_counts_json == {"cycle_review_pass": 1}
    assert row.primary_reason_code_counts_json == {
        "high_cost": 1,
        "low_net_edge": 1,
        "recommendation_ready": 1,
    }
    assert row.reason_codes_json == ["candidate_research_queue_ready"]
    assert row.rows_json == row.payload_json["rows"]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-20T12:30:00+00:00"
    assert row.payload_json["total_ready_notional"] == "12.000000"
    assert row.payload_json["rows"][0]["research_priority_score"] == "0.800000"
    assert row.payload_json["rows"][1]["evidence_gap_codes"] == ["low_net_edge"]
    assert row.payload_json["primary_reason_code_counts"] == [
        ["high_cost", 1],
        ["low_net_edge", 1],
        ["recommendation_ready", 1],
    ]
    assert row.payload_json["source_reason_code_counts"] == [
        {"count": 1, "reason_code": "cycle_review_pass"},
    ]
    assert row.payload_json["reason_codes"] == ["candidate_research_queue_ready"]
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.payload_json["rows"][0]["readonly"] is True
    _assert_no_floats(row.payload_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert paper_strategy_candidate_research_queue_report_from_db_row(row) == report


def test_research_queue_db_row_serializes_watch_payload_and_round_trips():
    report = _watch_report()

    row = paper_strategy_candidate_research_queue_report_to_db_row(report)

    assert row.action_status == "watch"
    assert row.recommended_next_step == "await_fresh_cycle_evidence"
    assert row.research_status == "watch"
    assert row.candidate_count == 0
    assert row.research_ready_count == 0
    assert row.watch_count == 0
    assert row.blocked_count == 0
    assert row.selected_count == 0
    assert row.skipped_count == 0
    assert row.not_selected_count == 0
    assert row.total_ready_notional == Decimal("0.000000")
    assert row.total_selected_notional == Decimal("0.000000")
    assert row.total_suggested_notional == Decimal("0.000000")
    assert row.source_reason_code_counts_json == {"cycle_review_watch": 1}
    assert row.primary_reason_code_counts_json == {}
    assert row.reason_codes_json == ["source_action_status_watch"]
    assert row.rows_json == []
    assert row.payload_json["primary_reason_code_counts"] == []
    assert row.payload_json["rows"] == []
    assert row.payload_json["reason_codes"] == ["source_action_status_watch"]
    _assert_no_floats(row.payload_json)

    assert paper_strategy_candidate_research_queue_report_from_db_row(row) == report


def test_research_queue_db_row_hash_uses_canonical_full_payload():
    report = _ready_report()
    same_report = PaperStrategyCandidateResearchQueueReport(**report.__dict__)
    different_report = _watch_report()

    first = paper_strategy_candidate_research_queue_report_to_db_row(report)
    second = paper_strategy_candidate_research_queue_report_to_db_row(same_report)
    third = paper_strategy_candidate_research_queue_report_to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_research_queue_db_row_is_frozen():
    row = paper_strategy_candidate_research_queue_report_to_db_row(_watch_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_research_queue_db_row_rejects_wrong_report_type_and_subclasses():
    with pytest.raises(ValueError, match="PaperStrategyCandidateResearchQueueReport"):
        paper_strategy_candidate_research_queue_report_to_db_row(object())

    report = _watch_report()
    subclass = ResearchQueueReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperStrategyCandidateResearchQueueReport"):
        paper_strategy_candidate_research_queue_report_to_db_row(subclass)


def test_research_queue_db_row_from_db_row_rejects_subclasses():
    row = paper_strategy_candidate_research_queue_report_to_db_row(_watch_report())
    subclass = ResearchQueueDbRowSubclass(**_row_values(row))

    with pytest.raises(ValueError, match="PaperStrategyCandidateResearchQueueDbRow"):
        paper_strategy_candidate_research_queue_report_from_db_row(subclass)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_research_queue_db_row_rejects_false_report_flags(flag_name: str):
    report = _watch_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        paper_strategy_candidate_research_queue_report_to_db_row(report)


def test_research_queue_db_row_rejects_deep_false_report_flags_before_write():
    report = _ready_report()
    object.__setattr__(report.rows[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        paper_strategy_candidate_research_queue_report_to_db_row(report)


def test_research_queue_db_row_rejects_duplicate_reason_maps_before_write():
    report = _ready_report()
    object.__setattr__(
        report,
        "primary_reason_code_counts",
        (("low_net_edge", 1), ("low_net_edge", 2)),
    )

    with pytest.raises(ValueError, match="primary_reason_code_counts"):
        paper_strategy_candidate_research_queue_report_to_db_row(report)

    report = _ready_report()
    object.__setattr__(
        report,
        "source_reason_code_counts",
        (
            _source_reason_count("cycle_review_pass", 1),
            _source_reason_count("cycle_review_pass", 2),
        ),
    )
    with pytest.raises(ValueError, match="source_reason_code_counts"):
        paper_strategy_candidate_research_queue_report_to_db_row(report)

    report = _ready_report()
    object.__setattr__(
        report,
        "reason_codes",
        ("candidate_research_queue_ready", "candidate_research_queue_ready"),
    )
    with pytest.raises(ValueError, match="reason_codes"):
        paper_strategy_candidate_research_queue_report_to_db_row(report)


def test_research_queue_db_row_rejects_unsafe_stored_flags():
    row = paper_strategy_candidate_research_queue_report_to_db_row(_watch_report())
    malformed = PaperStrategyCandidateResearchQueueDbRow(
        **{
            **_row_values(row),
            "report_sha256": "a" * 64,
            "payload_json": {**row.payload_json, "readonly": False},
        },
    )

    with pytest.raises(ValueError, match="readonly"):
        paper_strategy_candidate_research_queue_report_from_db_row(malformed)


def test_research_queue_db_row_rejects_deep_unsafe_stored_flags():
    row = paper_strategy_candidate_research_queue_report_to_db_row(_ready_report())
    payload = {
        **row.payload_json,
        "rows": [
            {**row.payload_json["rows"][0], "readonly": False},
            *row.payload_json["rows"][1:],
        ],
    }
    malformed = PaperStrategyCandidateResearchQueueDbRow(
        **{
            **_row_values(row),
            "report_sha256": "a" * 64,
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match="readonly"):
        paper_strategy_candidate_research_queue_report_from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 20, 12, 31, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "different-research-queue-v0"}, "config_version"),
        (
            {"source_config_version": "different-action-gated-queue-v0"},
            "source_config_version",
        ),
        (
            {
                "action_status": "blocked",
                "recommended_next_step": "repair_cycle_evidence",
            },
            "action_status",
        ),
        ({"research_status": "blocked"}, "research_status"),
        ({"candidate_count": 1}, "candidate_count"),
        ({"research_ready_count": 2}, "research_ready_count"),
        ({"watch_count": 2}, "watch_count"),
        ({"blocked_count": 2}, "blocked_count"),
        ({"selected_count": 2}, "selected_count"),
        ({"skipped_count": 2}, "skipped_count"),
        ({"not_selected_count": 2}, "not_selected_count"),
        ({"total_ready_notional": Decimal("1.000000")}, "total_ready_notional"),
        ({"total_selected_notional": Decimal("1.000000")}, "total_selected_notional"),
        ({"total_suggested_notional": Decimal("1.000000")}, "total_suggested_notional"),
        (
            {"top_research_priority_score": Decimal("0.100000")},
            "top_research_priority_score",
        ),
        (
            {"average_research_ready_score": Decimal("0.100000")},
            "average_research_ready_score",
        ),
        (
            {"source_reason_code_counts_json": {"cycle_review_pass": 2}},
            "source_reason_code_counts",
        ),
        (
            {"primary_reason_code_counts_json": {"recommendation_ready": 3}},
            "primary_reason_code_counts",
        ),
        ({"reason_codes_json": ["different_reason"]}, "reason_codes"),
    ),
)
def test_research_queue_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    row = paper_strategy_candidate_research_queue_report_to_db_row(_ready_report())
    values = _row_values(row)
    values.update(overrides)
    malformed = PaperStrategyCandidateResearchQueueDbRow(**values)

    with pytest.raises(ValueError, match=message):
        paper_strategy_candidate_research_queue_report_from_db_row(malformed)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_research_queue_db_row_rejects_tampered_row_hard_flag_mismatches(
    flag_name: str,
) -> None:
    row = paper_strategy_candidate_research_queue_report_to_db_row(_ready_report())
    object.__setattr__(row, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        paper_strategy_candidate_research_queue_report_from_db_row(row)


def test_research_queue_db_row_wraps_payload_recovery_errors_as_value_error():
    row = paper_strategy_candidate_research_queue_report_to_db_row(_watch_report())
    malformed = PaperStrategyCandidateResearchQueueDbRow(
        **{
            **_row_values(row),
            "report_sha256": "a" * 64,
            "payload_json": {
                key: value
                for key, value in row.payload_json.items()
                if key != "reason_codes"
            },
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        paper_strategy_candidate_research_queue_report_from_db_row(malformed)


def test_research_queue_db_row_rejects_duplicate_stored_reason_shapes():
    row = paper_strategy_candidate_research_queue_report_to_db_row(_ready_report())
    payload = {
        **row.payload_json,
        "primary_reason_code_counts": [["low_net_edge", 1], ["low_net_edge", 2]],
    }
    malformed = PaperStrategyCandidateResearchQueueDbRow(
        **{
            **_row_values(row),
            "report_sha256": "a" * 64,
            "payload_json": payload,
        },
    )
    with pytest.raises(ValueError, match="primary_reason_code_counts"):
        paper_strategy_candidate_research_queue_report_from_db_row(malformed)

    payload = {
        **row.payload_json,
        "reason_codes": [
            "candidate_research_queue_ready",
            "candidate_research_queue_ready",
        ],
    }
    malformed = PaperStrategyCandidateResearchQueueDbRow(
        **{
            **_row_values(row),
            "report_sha256": "a" * 64,
            "payload_json": payload,
        },
    )
    with pytest.raises(ValueError, match="reason_codes"):
        paper_strategy_candidate_research_queue_report_from_db_row(malformed)

    payload = {
        **row.payload_json,
        "source_reason_code_counts": [
            {"reason_code": "cycle_review_pass", "count": 1},
            {"reason_code": "cycle_review_pass", "count": 2},
        ],
    }
    malformed = PaperStrategyCandidateResearchQueueDbRow(
        **{
            **_row_values(row),
            "report_sha256": "a" * 64,
            "payload_json": payload,
        },
    )
    with pytest.raises(ValueError, match="source_reason_code_counts"):
        paper_strategy_candidate_research_queue_report_from_db_row(malformed)


def test_research_queue_db_row_validates_row_shape_and_rejects_floats():
    row = paper_strategy_candidate_research_queue_report_to_db_row(_watch_report())

    with pytest.raises(ValueError, match="report_sha256"):
        PaperStrategyCandidateResearchQueueDbRow(
            **{**_row_values(row), "report_sha256": "bad"},
        )

    with pytest.raises(ValueError, match="total_ready_notional"):
        PaperStrategyCandidateResearchQueueDbRow(
            **{**_row_values(row), "total_ready_notional": "0.000000"},
        )

    with pytest.raises(ValueError, match="payload_json"):
        PaperStrategyCandidateResearchQueueDbRow(
            **{
                **_row_values(row),
                "report_sha256": "a" * 64,
                "payload_json": {**row.payload_json, "bad_float": 0.1},
            },
        )

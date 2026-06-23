from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketConfig,
    PaperResearchPacketInputRow,
    PaperResearchPacketReport,
)
from polymarket_alpha_lab.strategy_candidate_research_packet_source import (
    build_paper_research_packet_report_from_strategy_candidate_research_queue_report,
    paper_research_packet_input_rows_from_strategy_candidate_research_queue_report,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)


GENERATED_AT = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
PACKET_GENERATED_AT = datetime(2026, 6, 21, 12, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class ResearchQueueReportSubclass(PaperStrategyCandidateResearchQueueReport):
    pass


class PacketConfigSubclass(PaperResearchPacketConfig):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _packet_config(**overrides) -> PaperResearchPacketConfig:
    values = {
        "config_version": "paper-research-packet-v0",
        "max_packet_rows": 5,
        "min_score": d("0.100000"),
    }
    values.update(overrides)
    return PaperResearchPacketConfig(**values)


def _research_row(**overrides) -> PaperStrategyCandidateResearchQueueRow:
    values = {
        "research_rank": 1,
        "queue_rank": 1,
        "market_slug": "alpha-ready",
        "question": "Will alpha-ready resolve yes?",
        "selected_side": "yes",
        "scoring_side": "yes",
        "source_action": "recommend",
        "decision": "selected",
        "queue_status": "ready",
        "research_status": "ready",
        "research_bucket": "research_ready",
        "assessment_status": "ready",
        "source_status": "paper_review_ready",
        "readiness_status": "pass",
        "recommendation_score": d("0.820000"),
        "readiness_score": d("0.900000"),
        "screening_score": d("0.750000"),
        "net_edge_per_share": d("0.040000"),
        "total_cost_per_share": d("0.010000"),
        "confidence": d("0.900000"),
        "spread": d("0.010000"),
        "resolution_risk": d("0.020000"),
        "suggested_notional": d("12.500000"),
        "selected_position_notional": d("12.500000"),
        "primary_reason_code": "positive_edge",
        "research_priority_score": d("0.860000"),
        "evidence_gap_codes": (),
        "reason_codes": ("positive_edge", "settlement_review"),
        "explanation": "recommend yes because positive_edge",
    }
    values.update(overrides)
    return PaperStrategyCandidateResearchQueueRow(**values)


def _research_report(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
    **overrides,
) -> PaperStrategyCandidateResearchQueueReport:
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "strategy-candidate-research-queue-v0",
        "source_config_version": "action-gated-strategy-recommendation-queue-v0",
        "action_status": "research_ready",
        "recommended_next_step": "review_candidate_research_queue",
        "source_reason_code_counts": (),
        "research_status": "ready" if rows else "watch",
        "candidate_count": len(rows),
        "research_ready_count": sum(1 for row in rows if row.research_status == "ready"),
        "watch_count": sum(1 for row in rows if row.research_status == "watch"),
        "blocked_count": sum(1 for row in rows if row.research_status == "blocked"),
        "selected_count": sum(1 for row in rows if row.decision == "selected"),
        "skipped_count": sum(1 for row in rows if row.decision == "skipped"),
        "not_selected_count": sum(1 for row in rows if row.decision == "not_selected"),
        "total_ready_notional": sum(
            (row.suggested_notional for row in rows if row.research_status == "ready"),
            ZERO,
        ),
        "total_selected_notional": sum(
            (row.selected_position_notional for row in rows),
            ZERO,
        ),
        "total_suggested_notional": sum(
            (row.suggested_notional for row in rows if row.source_action == "recommend"),
            ZERO,
        ),
        "top_research_priority_score": (
            rows[0].research_priority_score if rows else ZERO
        ),
        "average_research_ready_score": _average_ready_score(rows),
        "primary_reason_code_counts": _primary_reason_code_counts(rows),
        "rows": rows,
        "reason_codes": (
            ("candidate_research_queue_ready",)
            if rows
            else ("no_candidate_research_rows",)
        ),
    }
    values.update(overrides)
    return PaperStrategyCandidateResearchQueueReport(**values)


def _average_ready_score(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> Decimal:
    ready_rows = tuple(row for row in rows if row.research_status == "ready")
    if not ready_rows:
        return ZERO
    return (
        sum((row.research_priority_score for row in ready_rows), ZERO)
        / Decimal(len(ready_rows))
    ).quantize(d("0.000001"))


def _primary_reason_code_counts(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.primary_reason_code] = counts.get(row.primary_reason_code, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def test_ready_queue_rows_build_high_and_medium_packet_rows_with_evidence_preserved():
    rows = (
        _research_row(
            market_slug="high-ready",
            question="Will high-ready resolve yes?",
            reason_codes=("positive_edge", "settlement_review"),
        ),
        _research_row(
            research_rank=2,
            queue_rank=2,
            market_slug="medium-ready",
            question="Will medium-ready resolve yes?",
            source_action="watch",
            decision="not_selected",
            recommendation_score=d("0.620000"),
            readiness_score=d("0.700000"),
            net_edge_per_share=d("0.030000"),
            suggested_notional=d("8.000000"),
            selected_position_notional=ZERO,
            primary_reason_code="thin_book",
            research_priority_score=d("0.660000"),
            reason_codes=("thin_book", "cost_review"),
            explanation="watch yes because thin_book",
        ),
    )
    source_report = _research_report(rows)

    input_rows = (
        paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
            source_report,
        )
    )
    report = build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
        source_report,
        config=_packet_config(),
        generated_at=PACKET_GENERATED_AT,
    )

    assert all(type(row) is PaperResearchPacketInputRow for row in input_rows)
    assert input_rows[0].market_slug == "high-ready"
    assert input_rows[0].question == "Will high-ready resolve yes?"
    assert input_rows[0].side == "yes"
    assert input_rows[0].action == "recommend"
    assert input_rows[0].queue_status == "ready"
    assert input_rows[0].recommendation_score == d("0.820000")
    assert input_rows[0].net_edge == d("0.040000")
    assert input_rows[0].allocated_notional == d("12.500000")
    assert input_rows[0].requested_notional == d("12.500000")
    assert input_rows[0].reason_codes == ("positive_edge", "settlement_review")
    assert input_rows[1].action == "watch"
    assert input_rows[1].queue_status == "ready"
    assert input_rows[1].allocated_notional == ZERO
    assert input_rows[1].requested_notional == d("8.000000")

    assert type(report) is PaperResearchPacketReport
    assert report.generated_at == PACKET_GENERATED_AT
    assert report.config_version == "paper-research-packet-v0"
    assert report.input_row_count == 2
    assert report.packet_row_count == 2
    assert tuple(row.market_slug for row in report.packet_rows) == (
        "high-ready",
        "medium-ready",
    )
    assert tuple(row.research_priority for row in report.packet_rows) == (
        "high",
        "medium",
    )
    assert report.packet_rows[0].reason_codes == (
        "positive_edge",
        "settlement_review",
    )
    assert report.packet_rows[1].reason_codes == ("thin_book", "cost_review")
    assert report.packet_rows[0].allocated_notional == d("12.500000")
    assert report.packet_rows[0].requested_notional == d("12.500000")


def test_ready_no_side_is_preserved_into_input_and_packet_rows():
    source_report = _research_report(
        (
            _research_row(
                market_slug="ready-no",
                question="Will ready-no resolve no?",
                selected_side="no",
                scoring_side="no",
                reason_codes=("positive_edge", "settlement_review"),
            ),
        ),
    )

    input_rows = (
        paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
            source_report,
        )
    )
    report = build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
        source_report,
        config=_packet_config(),
        generated_at=PACKET_GENERATED_AT,
    )

    assert input_rows[0].side == "no"
    assert input_rows[0].action == "recommend"
    assert input_rows[0].queue_status == "ready"
    assert report.packet_rows[0].side == "no"
    assert report.packet_rows[0].market_slug == "ready-no"
    assert report.packet_rows[0].research_priority == "high"


@pytest.mark.parametrize("selected_side", ("yes", "no"))
@pytest.mark.parametrize("source_action", ("recommend", "reject"))
def test_blocked_or_reject_selected_side_maps_to_reject_and_skip_packet_row(
    selected_side,
    source_action,
):
    source_report = _research_report(
        (
            _research_row(
                market_slug=f"blocked-{selected_side}",
                question=f"Will blocked-{selected_side} resolve?",
                selected_side=selected_side,
                scoring_side=selected_side,
                source_action=source_action,
                decision="skipped",
                queue_status="blocked",
                research_status="blocked",
                research_bucket="blocked",
                assessment_status="blocked",
                source_status="blocked_by_inputs",
                readiness_status="blocked",
                suggested_notional=ZERO,
                selected_position_notional=ZERO,
                primary_reason_code="blocked_source",
                reason_codes=("blocked_source", "settlement_review"),
                explanation=f"reject {selected_side} because blocked_source",
            ),
        ),
    )

    input_rows = (
        paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
            source_report,
        )
    )
    report = build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
        source_report,
        config=_packet_config(),
        generated_at=PACKET_GENERATED_AT,
    )

    assert input_rows[0].side == selected_side
    assert input_rows[0].action == "reject"
    assert input_rows[0].queue_status == "blocked"
    assert input_rows[0].requested_notional == ZERO
    assert report.packet_row_count == 1
    assert report.skipped_count == 1
    assert report.included_count == 0
    assert report.packet_rows[0].side == selected_side
    assert report.packet_rows[0].research_priority == "skip"
    assert report.packet_rows[0].required_checks == ("outcome_definition",)


def test_recommend_watch_skipped_row_preserves_recommend_action_and_requested_notional():
    source_report = _research_report(
        (
            _research_row(
                market_slug="recommend-watch",
                question="Will recommend-watch resolve yes?",
                source_action="recommend",
                decision="skipped",
                queue_status="watch",
                research_status="watch",
                research_bucket="watch",
                assessment_status="watch",
                source_status="watch",
                readiness_status="watch",
                suggested_notional=d("9.750000"),
                selected_position_notional=ZERO,
                primary_reason_code="readiness_watch",
                reason_codes=("readiness_watch", "settlement_review"),
                explanation="recommend yes because readiness_watch",
            ),
        ),
    )

    input_rows = (
        paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
            source_report,
        )
    )

    report = build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
        source_report,
        config=_packet_config(),
        generated_at=PACKET_GENERATED_AT,
    )

    assert input_rows[0].side == "yes"
    assert input_rows[0].action == "recommend"
    assert input_rows[0].queue_status == "watch"
    assert input_rows[0].allocated_notional == ZERO
    assert input_rows[0].requested_notional == d("9.750000")
    assert report.packet_rows[0].requested_notional == d("9.750000")


def test_watch_none_side_remains_watch_input_and_final_packet_skips():
    source_report = _research_report(
        (
            _research_row(
                market_slug="watch-none",
                question="Will watch-none resolve?",
                selected_side="none",
                source_action="watch",
                decision="skipped",
                queue_status="watch",
                research_status="watch",
                research_bucket="watch",
                assessment_status="watch",
                source_status="watch",
                readiness_status="watch",
                suggested_notional=ZERO,
                selected_position_notional=ZERO,
                primary_reason_code="no_selected_side",
                evidence_gap_codes=("no_selected_side",),
                reason_codes=("no_selected_side", "readiness_watch"),
                explanation="watch none because no_selected_side",
            ),
        ),
    )

    input_rows = (
        paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
            source_report,
        )
    )
    report = build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
        source_report,
        config=_packet_config(),
        generated_at=PACKET_GENERATED_AT,
    )

    assert input_rows[0].side == "none"
    assert input_rows[0].action == "watch"
    assert input_rows[0].queue_status == "watch"
    assert report.packet_row_count == 1
    assert report.skipped_count == 1
    assert report.packet_rows[0].side == "none"
    assert report.packet_rows[0].research_priority == "skip"
    assert report.packet_rows[0].required_checks == ("outcome_definition",)


def test_blocked_no_side_queue_row_becomes_skip_with_only_outcome_definition_check():
    blocked_row = _research_row(
        selected_side="none",
        source_action="reject",
        decision="skipped",
        queue_status="blocked",
        research_status="blocked",
        research_bucket="blocked",
        assessment_status="blocked",
        source_status="blocked_by_inputs",
        readiness_status="blocked",
        recommendation_score=ZERO,
        readiness_score=ZERO,
        screening_score=ZERO,
        net_edge_per_share=None,
        suggested_notional=ZERO,
        selected_position_notional=ZERO,
        primary_reason_code="no_selected_side",
        research_priority_score=ZERO,
        evidence_gap_codes=("no_selected_side",),
        reason_codes=("no_selected_side", "blocked_source"),
        explanation="reject none because no_selected_side",
    )
    source_report = _research_report((blocked_row,))

    input_rows = (
        paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
            source_report,
        )
    )
    report = build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
        source_report,
        config=_packet_config(),
        generated_at=PACKET_GENERATED_AT,
    )

    assert input_rows[0].side == "none"
    assert input_rows[0].action == "reject"
    assert input_rows[0].queue_status == "blocked"
    assert input_rows[0].net_edge == ZERO
    assert type(input_rows[0].net_edge) is Decimal
    assert report.packet_row_count == 1
    assert report.skipped_count == 1
    assert report.packet_rows[0].market_slug == "alpha-ready"
    assert report.packet_rows[0].research_priority == "skip"
    assert report.packet_rows[0].required_checks == ("outcome_definition",)
    assert report.packet_rows[0].reason_codes == ("no_selected_side", "blocked_source")


def test_negative_net_edge_is_preserved_and_only_missing_edge_maps_to_zero():
    rows = (
        _research_row(
            market_slug="negative-edge-ready",
            question="Will negative-edge-ready resolve yes?",
            recommendation_score=d("0.710000"),
            net_edge_per_share=d("-0.012345"),
            primary_reason_code="negative_net_edge",
            research_priority_score=d("0.805000"),
            reason_codes=("negative_net_edge", "readiness_passed"),
            explanation="recommend yes despite negative_net_edge",
        ),
        _research_row(
            research_rank=2,
            queue_rank=2,
            market_slug="missing-edge-ready",
            question="Will missing-edge-ready resolve yes?",
            recommendation_score=d("0.700000"),
            net_edge_per_share=None,
            primary_reason_code="missing_net_edge",
            research_priority_score=d("0.800000"),
            evidence_gap_codes=("missing_net_edge",),
            reason_codes=("missing_net_edge", "readiness_passed"),
        ),
    )
    source_report = _research_report(rows)

    input_rows = (
        paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
            source_report,
        )
    )
    report = build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
        source_report,
        config=_packet_config(),
        generated_at=PACKET_GENERATED_AT,
    )

    input_by_slug = {row.market_slug: row for row in input_rows}
    packet_by_slug = {row.market_slug: row for row in report.packet_rows}
    assert input_by_slug["negative-edge-ready"].net_edge == d("-0.012345")
    assert packet_by_slug["negative-edge-ready"].net_edge == d("-0.012345")
    assert input_by_slug["missing-edge-ready"].net_edge == ZERO
    assert packet_by_slug["missing-edge-ready"].net_edge == ZERO


def test_missing_net_edge_maps_to_zero_decimal_without_float_math():
    source_report = _research_report(
        (
            _research_row(
                market_slug="missing-edge-ready",
                question="Will missing-edge-ready resolve yes?",
                recommendation_score=d("0.700000"),
                net_edge_per_share=None,
                primary_reason_code="missing_net_edge",
                research_priority_score=d("0.800000"),
                reason_codes=("missing_net_edge", "readiness_passed"),
                evidence_gap_codes=("missing_net_edge",),
            ),
        ),
    )

    input_rows = (
        paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
            source_report,
        )
    )
    report = build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
        source_report,
        config=_packet_config(),
        generated_at=PACKET_GENERATED_AT,
    )

    assert input_rows[0].net_edge == ZERO
    assert type(input_rows[0].net_edge) is Decimal
    assert report.packet_rows[0].net_edge == ZERO
    assert type(report.packet_rows[0].net_edge) is Decimal


def test_empty_source_report_builds_empty_input_rows_and_packet_counts():
    source_report = _research_report(())

    input_rows = (
        paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
            source_report,
        )
    )
    report = build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
        source_report,
        config=_packet_config(),
        generated_at=PACKET_GENERATED_AT,
    )

    assert input_rows == ()
    assert report.input_row_count == 0
    assert report.packet_row_count == 0
    assert report.included_count == 0
    assert report.skipped_count == 0
    assert report.high_priority_count == 0
    assert report.medium_priority_count == 0
    assert report.low_priority_count == 0
    assert report.packet_rows == ()


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_adapter_rejects_false_hard_flags_on_source_report_rows_and_config(flag_name):
    source_report = _research_report((_research_row(),))
    object.__setattr__(source_report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
            source_report,
            config=_packet_config(),
            generated_at=PACKET_GENERATED_AT,
        )

    source_report = _research_report((_research_row(),))
    object.__setattr__(source_report.rows[0], flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
            source_report,
        )

    source_report = _research_report((_research_row(),))
    config = _packet_config()
    object.__setattr__(config, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
            source_report,
            config=config,
            generated_at=PACKET_GENERATED_AT,
        )


def test_adapter_rejects_subclassed_source_report_and_packet_config():
    source_report = _research_report((_research_row(),))
    config = _packet_config()

    with pytest.raises(ValueError, match="PaperStrategyCandidateResearchQueueReport"):
        build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
            ResearchQueueReportSubclass(**source_report.__dict__),
            config=config,
            generated_at=PACKET_GENERATED_AT,
        )

    with pytest.raises(ValueError, match="PaperResearchPacketConfig"):
        build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
            source_report,
            config=PacketConfigSubclass(**config.__dict__),
            generated_at=PACKET_GENERATED_AT,
        )

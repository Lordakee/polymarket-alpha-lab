from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketConfig,
    PaperResearchPacketInputRow,
    PaperResearchPacketReport,
    build_paper_research_packet_report,
)


GENERATED_AT = datetime(2026, 6, 18, 15, 30, tzinfo=UTC)


def _config(
    *,
    max_packet_rows: int = 3,
    min_score: Decimal = Decimal("0.200000"),
) -> PaperResearchPacketConfig:
    return PaperResearchPacketConfig(
        config_version="paper-research-packet-v0",
        max_packet_rows=max_packet_rows,
        min_score=min_score,
    )


def _row(
    market_slug: str,
    *,
    question: str | None = None,
    side: str = "yes",
    action: str = "recommend",
    queue_status: str = "ready",
    recommendation_score: Decimal = Decimal("0.800000"),
    net_edge: Decimal = Decimal("0.060000"),
    allocated_notional: Decimal | None = Decimal("12.500000"),
    requested_notional: Decimal | None = Decimal("15.000000"),
    reason_codes: tuple[str, ...] = ("positive_edge",),
) -> PaperResearchPacketInputRow:
    return PaperResearchPacketInputRow(
        market_slug=market_slug,
        question=question or f"Will {market_slug} resolve yes?",
        side=side,
        action=action,
        queue_status=queue_status,
        recommendation_score=recommendation_score,
        net_edge=net_edge,
        allocated_notional=allocated_notional,
        requested_notional=requested_notional,
        reason_codes=reason_codes,
    )


def test_research_packet_orders_priority_rows_and_counts_deterministically():
    generated_at = datetime(
        2026,
        6,
        18,
        11,
        30,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    rows = (
        _row(
            "low-ready",
            recommendation_score=Decimal("0.550000"),
            net_edge=Decimal("0.010000"),
            allocated_notional=Decimal("2.000000"),
            requested_notional=Decimal("8.000000"),
            reason_codes=("small_edge",),
        ),
        _row(
            "skip-reject",
            side="none",
            action="reject",
            queue_status="blocked",
            recommendation_score=Decimal("0.050000"),
            net_edge=Decimal("0.000000"),
            allocated_notional=None,
            requested_notional=None,
            reason_codes=("missing_inputs",),
        ),
        _row(
            "medium-ready",
            side="no",
            recommendation_score=Decimal("0.700000"),
            net_edge=Decimal("0.030000"),
            allocated_notional=Decimal("5.000000"),
            requested_notional=Decimal("9.000000"),
            reason_codes=("good_edge", "thin_book"),
        ),
        _row(
            "high-ready",
            recommendation_score=Decimal("0.920000"),
            net_edge=Decimal("0.080000"),
            allocated_notional=Decimal("10.000000"),
            requested_notional=Decimal("12.000000"),
            reason_codes=("large_edge", "settlement_review"),
        ),
        _row(
            "below-min-watch",
            action="watch",
            queue_status="watch",
            recommendation_score=Decimal("0.190000"),
            net_edge=Decimal("0.020000"),
            allocated_notional=None,
            requested_notional=Decimal("3.000000"),
            reason_codes=("below_threshold",),
        ),
    )

    report = build_paper_research_packet_report(
        rows,
        config=_config(max_packet_rows=4, min_score=Decimal("0.200000")),
        generated_at=generated_at,
    )

    assert isinstance(report, PaperResearchPacketReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-research-packet-v0"
    assert report.input_row_count == 5
    assert report.packet_row_count == 4
    assert report.included_count == 3
    assert report.skipped_count == 1
    assert report.high_priority_count == 1
    assert report.medium_priority_count == 1
    assert report.low_priority_count == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_slug for row in report.packet_rows) == (
        "high-ready",
        "medium-ready",
        "low-ready",
        "skip-reject",
    )
    assert tuple(row.packet_rank for row in report.packet_rows) == (1, 2, 3, 4)
    assert tuple(row.research_priority for row in report.packet_rows) == (
        "high",
        "medium",
        "low",
        "skip",
    )
    assert report.packet_rows[0].required_checks == (
        "outcome_definition",
        "liquidity_depth",
        "cost_sensitivity",
        "settlement_timing",
    )
    assert report.packet_rows[1].required_checks == (
        "outcome_definition",
        "liquidity_depth",
        "cost_sensitivity",
    )
    assert report.packet_rows[2].required_checks == (
        "outcome_definition",
        "cost_sensitivity",
    )
    assert report.packet_rows[3].required_checks == ("outcome_definition",)
    assert report.packet_rows[1].reason_codes == ("good_edge", "thin_book")
    assert report.packet_rows[1].side == "no"


def test_research_packet_dataclasses_are_frozen_and_decimal_only():
    row = _row("frozen-row")
    config = _config()

    with pytest.raises(FrozenInstanceError):
        row.market_slug = "changed"
    with pytest.raises(FrozenInstanceError):
        config.max_packet_rows = 10
    with pytest.raises(ValueError, match="recommendation_score must be a Decimal"):
        _row("float-score", recommendation_score=0.5)
    with pytest.raises(ValueError, match="min_score must be a Decimal"):
        _config(min_score=0.2)

    report = build_paper_research_packet_report(
        (row,),
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.packet_rows[0].research_priority = "skip"
    assert report.packet_rows[0].recommendation_score == Decimal("0.800000")
    assert report.packet_rows[0].net_edge == Decimal("0.060000")


def test_research_packet_report_rejects_inconsistent_manual_rows():
    packet_row = build_paper_research_packet_report(
        (_row("consistent"),),
        config=_config(),
        generated_at=GENERATED_AT,
    ).packet_rows[0]

    with pytest.raises(ValueError, match="packet_row_count must match packet_rows"):
        PaperResearchPacketReport(
            generated_at=GENERATED_AT,
            config_version="paper-research-packet-v0",
            input_row_count=1,
            packet_row_count=2,
            included_count=1,
            skipped_count=0,
            high_priority_count=1,
            medium_priority_count=0,
            low_priority_count=0,
            packet_rows=(packet_row,),
        )

    with pytest.raises(ValueError, match="packet_rows must use deterministic ordering"):
        PaperResearchPacketReport(
            generated_at=GENERATED_AT,
            config_version="paper-research-packet-v0",
            input_row_count=2,
            packet_row_count=2,
            included_count=2,
            skipped_count=0,
            high_priority_count=2,
            medium_priority_count=0,
            low_priority_count=0,
            packet_rows=(
                replace(packet_row, packet_rank=1, market_slug="b-row"),
                replace(packet_row, packet_rank=2, market_slug="a-row"),
            ),
        )

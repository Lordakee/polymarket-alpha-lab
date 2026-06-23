from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketReport,
    PaperResearchPacketRow,
)
from polymarket_alpha_lab.paper_research_packet_db_history import (
    DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION,
    PaperResearchPacketDbHistoryConfig,
    PaperResearchPacketDbHistoryReport,
    build_paper_research_packet_db_history_report,
)


GENERATED_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 23, 8, 0, tzinfo=UTC)


class PacketReportSubclass(PaperResearchPacketReport):
    pass


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config() -> PaperResearchPacketDbHistoryConfig:
    return PaperResearchPacketDbHistoryConfig()


def _history(
    *reports: PaperResearchPacketReport,
    config: PaperResearchPacketDbHistoryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperResearchPacketDbHistoryReport:
    return build_paper_research_packet_db_history_report(
        list(reports),
        config=config or _config(),
        generated_at=generated_at,
    )


def _packet_row(
    *,
    packet_rank: int = 1,
    market_slug: str = "event-alpha",
    side: str = "yes",
    research_priority: str = "high",
    recommendation_score: Decimal = d("0.900000"),
    net_edge: Decimal = d("0.080000"),
    allocated_notional: Decimal | None = d("25.000000"),
    requested_notional: Decimal | None = d("40.000000"),
    reason_codes: tuple[str, ...] = ("side_edge_recommend",),
) -> PaperResearchPacketRow:
    checks = (
        "outcome_definition",
        "liquidity_depth",
        "cost_sensitivity",
        "settlement_timing",
    )
    if research_priority != "high":
        checks = (
            "outcome_definition",
            "liquidity_depth",
            "cost_sensitivity",
        )
    if research_priority == "skip":
        checks = ("outcome_definition",)
        side = "none"
    return PaperResearchPacketRow(
        packet_rank=packet_rank,
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        side=side,
        research_priority=research_priority,
        required_checks=checks,
        reason_codes=reason_codes,
        recommendation_score=recommendation_score,
        net_edge=net_edge,
        allocated_notional=allocated_notional,
        requested_notional=requested_notional,
    )


def _packet_report(
    *,
    generated_at: datetime,
    config_version: str = "paper-research-packet-v0",
    packet_rows: tuple[PaperResearchPacketRow, ...] | None = None,
    input_row_count: int | None = None,
) -> PaperResearchPacketReport:
    rows = (_packet_row(),) if packet_rows is None else packet_rows
    high_count = sum(1 for row in rows if row.research_priority == "high")
    medium_count = sum(1 for row in rows if row.research_priority == "medium")
    low_count = sum(1 for row in rows if row.research_priority == "low")
    skipped_count = sum(1 for row in rows if row.research_priority == "skip")
    included_count = high_count + medium_count + low_count
    return PaperResearchPacketReport(
        generated_at=generated_at,
        config_version=config_version,
        input_row_count=len(rows) if input_row_count is None else input_row_count,
        packet_row_count=len(rows),
        included_count=included_count,
        skipped_count=skipped_count,
        high_priority_count=high_count,
        medium_priority_count=medium_count,
        low_priority_count=low_count,
        packet_rows=rows,
    )


def test_db_history_empty_input_is_readonly_report_with_absent_latest_fields():
    history = _history()

    assert type(history) is PaperResearchPacketDbHistoryReport
    assert history.generated_at == GENERATED_AT
    assert history.config_version == (
        DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION
    )
    assert history.report_count == 0
    assert history.first_report_generated_at is None
    assert history.latest_report_generated_at is None
    assert history.duplicate_generated_at_count == 0
    assert history.latest_packet_config_version is None
    assert history.latest_input_row_count is None
    assert history.latest_packet_row_count is None
    assert history.latest_included_count is None
    assert history.latest_skipped_count is None
    assert history.latest_high_priority_count is None
    assert history.latest_medium_priority_count is None
    assert history.latest_low_priority_count is None
    assert history.latest_top_packet_rank is None
    assert history.latest_top_packet_market_slug is None
    assert history.latest_top_packet_side is None
    assert history.latest_top_packet_research_priority is None
    assert history.latest_top_packet_recommendation_score is None
    assert history.latest_top_packet_net_edge is None
    assert history.latest_top_packet_allocated_notional is None
    assert history.latest_top_packet_requested_notional is None
    assert history.latest_top_packet_reason_codes is None
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


def test_db_history_sorts_chronologically_and_surfaces_latest_packet_summary():
    older = _packet_report(
        generated_at=BASE_AT,
        packet_rows=(
            _packet_row(
                market_slug="older-event",
                recommendation_score=d("0.850000"),
                net_edge=d("0.060000"),
            ),
        ),
    )
    latest_top = _packet_row(
        packet_rank=1,
        market_slug="latest-top",
        side="no",
        research_priority="high",
        recommendation_score=d("0.950000"),
        net_edge=d("0.120000"),
        allocated_notional=d("75.000000"),
        requested_notional=d("100.000000"),
        reason_codes=("queue_ready", "side_edge_recommend"),
    )
    latest_second = _packet_row(
        packet_rank=2,
        market_slug="latest-second",
        research_priority="medium",
        recommendation_score=d("0.720000"),
        net_edge=d("0.030000"),
        allocated_notional=None,
        requested_notional=d("10.000000"),
        reason_codes=("medium_priority",),
    )
    latest = _packet_report(
        generated_at=BASE_AT + timedelta(hours=2),
        config_version="paper-research-packet-v1",
        packet_rows=(latest_top, latest_second),
        input_row_count=5,
    )

    history = _history(latest, older)

    assert history.report_count == 2
    assert history.first_report_generated_at == older.generated_at
    assert history.latest_report_generated_at == latest.generated_at
    assert history.latest_packet_config_version == "paper-research-packet-v1"
    assert history.latest_input_row_count == 5
    assert history.latest_packet_row_count == 2
    assert history.latest_included_count == 2
    assert history.latest_skipped_count == 0
    assert history.latest_high_priority_count == 1
    assert history.latest_medium_priority_count == 1
    assert history.latest_low_priority_count == 0
    assert history.latest_top_packet_rank == 1
    assert history.latest_top_packet_market_slug == "latest-top"
    assert history.latest_top_packet_side == "no"
    assert history.latest_top_packet_research_priority == "high"
    assert history.latest_top_packet_recommendation_score == d("0.950000")
    assert history.latest_top_packet_net_edge == d("0.120000")
    assert history.latest_top_packet_allocated_notional == d("75.000000")
    assert history.latest_top_packet_requested_notional == d("100.000000")
    assert history.latest_top_packet_reason_codes == (
        "queue_ready",
        "side_edge_recommend",
    )


def test_db_history_counts_duplicate_generated_at_values_without_deduping():
    duplicate_at = BASE_AT + timedelta(hours=1)
    reports = (
        _packet_report(generated_at=BASE_AT),
        _packet_report(
            generated_at=duplicate_at,
            packet_rows=(
                _packet_row(
                    market_slug="duplicate-one",
                    recommendation_score=d("0.810000"),
                    net_edge=d("0.050000"),
                ),
            ),
        ),
        _packet_report(
            generated_at=duplicate_at,
            packet_rows=(
                _packet_row(
                    market_slug="duplicate-two",
                    recommendation_score=d("0.820000"),
                    net_edge=d("0.051000"),
                ),
            ),
        ),
        _packet_report(generated_at=BASE_AT + timedelta(hours=3)),
    )

    history = _history(*reports)

    assert history.report_count == 4
    assert history.duplicate_generated_at_count == 1


def test_db_history_uses_none_for_top_packet_fields_when_latest_has_no_rows():
    older = _packet_report(generated_at=BASE_AT)
    latest_empty = _packet_report(
        generated_at=BASE_AT + timedelta(hours=1),
        packet_rows=(),
        input_row_count=4,
    )

    history = _history(older, latest_empty)

    assert history.latest_report_generated_at == latest_empty.generated_at
    assert history.latest_input_row_count == 4
    assert history.latest_packet_row_count == 0
    assert history.latest_included_count == 0
    assert history.latest_skipped_count == 0
    assert history.latest_top_packet_rank is None
    assert history.latest_top_packet_market_slug is None
    assert history.latest_top_packet_side is None
    assert history.latest_top_packet_research_priority is None
    assert history.latest_top_packet_recommendation_score is None
    assert history.latest_top_packet_net_edge is None
    assert history.latest_top_packet_allocated_notional is None
    assert history.latest_top_packet_requested_notional is None
    assert history.latest_top_packet_reason_codes is None


def test_db_history_rejects_wrong_types_subclasses_flags_and_generated_at_type():
    report = _packet_report(generated_at=BASE_AT)

    class ConfigSubclass(PaperResearchPacketDbHistoryConfig):
        pass

    with pytest.raises(ValueError, match="reports must be a list or tuple"):
        build_paper_research_packet_db_history_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="reports must contain"):
        _history(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reports must contain"):
        _history(PacketReportSubclass(**report.__dict__))
    with pytest.raises(ValueError, match="config must be"):
        build_paper_research_packet_db_history_report(
            [],
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_paper_research_packet_db_history_report(
            [],
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 23, 12, 0, tzinfo=UTC),
        )

    unsafe_report = _packet_report(generated_at=BASE_AT + timedelta(hours=1))
    object.__setattr__(unsafe_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly must be True"):
        _history(unsafe_report)

    unsafe_row_report = _packet_report(generated_at=BASE_AT + timedelta(hours=2))
    object.__setattr__(unsafe_row_report.packet_rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        _history(unsafe_row_report)


def test_db_history_dataclasses_are_frozen_and_validate_hard_flags():
    history = _history(_packet_report(generated_at=BASE_AT))
    config = _config()

    with pytest.raises(FrozenInstanceError):
        history.report_count = 0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(history, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(history, readonly=False)

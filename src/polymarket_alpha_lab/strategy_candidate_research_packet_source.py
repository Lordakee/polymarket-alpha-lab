"""Pure adapter from candidate research queues into paper research packets."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketConfig,
    PaperResearchPacketInputRow,
    PaperResearchPacketReport,
    build_paper_research_packet_report,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)


ZERO = Decimal("0.000000")


def paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
    src: PaperStrategyCandidateResearchQueueReport,
) -> tuple[PaperResearchPacketInputRow, ...]:
    if type(src) is not PaperStrategyCandidateResearchQueueReport:
        raise ValueError("src must be a PaperStrategyCandidateResearchQueueReport")
    _need_flags("src", src)
    return tuple(_input_row_from_queue_row(row) for row in _rows(src.rows))


def build_paper_research_packet_report_from_strategy_candidate_research_queue_report(
    src: PaperStrategyCandidateResearchQueueReport,
    *,
    config: PaperResearchPacketConfig,
    generated_at: datetime,
) -> PaperResearchPacketReport:
    if type(config) is not PaperResearchPacketConfig:
        raise ValueError("config must be a PaperResearchPacketConfig")
    _need_flags("config", config)
    rows = paper_research_packet_input_rows_from_strategy_candidate_research_queue_report(
        src,
    )
    return build_paper_research_packet_report(
        rows,
        config=config,
        generated_at=generated_at,
    )


def _input_row_from_queue_row(
    row: PaperStrategyCandidateResearchQueueRow,
) -> PaperResearchPacketInputRow:
    return PaperResearchPacketInputRow(
        market_slug=row.market_slug,
        question=row.question,
        side=row.selected_side,
        action=_packet_action(row),
        queue_status=_packet_status(row),
        recommendation_score=row.recommendation_score,
        net_edge=_net_edge(row.net_edge_per_share),
        allocated_notional=row.selected_position_notional,
        requested_notional=row.suggested_notional,
        reason_codes=row.reason_codes,
    )


def _packet_action(row: PaperStrategyCandidateResearchQueueRow) -> str:
    if _blocked_or_reject(row):
        return "reject"
    if row.source_action in ("recommend", "watch"):
        return row.source_action
    return "watch"


def _packet_status(row: PaperStrategyCandidateResearchQueueRow) -> str:
    if _blocked_or_reject(row):
        return "blocked"
    if row.research_status == "ready" and row.queue_status == "ready":
        return "ready"
    return "watch"


def _blocked_or_reject(row: PaperStrategyCandidateResearchQueueRow) -> bool:
    return (
        row.source_action == "reject"
        or row.research_status == "blocked"
        or row.queue_status == "blocked"
    )


def _net_edge(value: Decimal | None) -> Decimal:
    if value is None:
        return ZERO
    return value


def _rows(
    value: Iterable[PaperStrategyCandidateResearchQueueRow],
) -> tuple[PaperStrategyCandidateResearchQueueRow, ...]:
    rows = tuple(value)
    for row in rows:
        if type(row) is not PaperStrategyCandidateResearchQueueRow:
            raise ValueError("src rows must contain PaperStrategyCandidateResearchQueueRow values")
        _need_flags("src row", row)
    return rows


def _need_flags(name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{name} must be {flag}")


__all__ = (
    "paper_research_packet_input_rows_from_strategy_candidate_research_queue_report",
    "build_paper_research_packet_report_from_strategy_candidate_research_queue_report",
)

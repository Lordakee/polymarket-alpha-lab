"""Research packet assembly for manual market review."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256

from polymarket_alpha_lab.pipeline import ScoredCandidate


@dataclass(frozen=True)
class ResearchPacket:
    packet_id: str
    created_at: datetime
    condition_id: str
    token_id: str
    market_slug: str
    question: str
    source_score: str
    raw_archive_path: str
    market_url: str
    outcome_name: str
    strategy_type: str
    model_probability: Decimal | None
    bid: Decimal | None
    ask: Decimal | None
    midpoint: Decimal | None
    expected_entry_price: Decimal | None
    fair_value_estimate: Decimal | None
    theoretical_edge: Decimal | None
    spread: Decimal | None
    slippage_estimate: Decimal | None
    cost_adjusted_edge: Decimal | None
    confidence: Decimal | None
    max_executable_size: Decimal | None
    risk_tags: tuple[str, ...]
    thesis: str
    invalidating_conditions: str
    rule_text: str
    rule_text_hash: str
    resolution_source: str

    @property
    def is_complete(self) -> bool:
        return self.missing_required_fields() == []

    def missing_required_fields(self) -> list[str]:
        missing: list[str] = []
        for field_name in (
            "market_url",
            "outcome_name",
            "strategy_type",
            "model_probability",
            "bid",
            "ask",
            "midpoint",
            "expected_entry_price",
            "spread",
            "slippage_estimate",
            "cost_adjusted_edge",
            "thesis",
            "invalidating_conditions",
            "rule_text",
            "resolution_source",
        ):
            if not _has_value(getattr(self, field_name)):
                missing.append(field_name)
        if self.max_executable_size is None or self.max_executable_size <= 0:
            missing.append("positive_max_executable_size")
        return missing


def build_research_packet(
    *,
    candidate: ScoredCandidate,
    created_at: datetime,
    market_url: str,
    outcome_name: str,
    strategy_type: str,
    model_probability: Decimal | None,
    bid: Decimal | None,
    ask: Decimal | None,
    midpoint: Decimal | None,
    expected_entry_price: Decimal | None,
    fair_value_estimate: Decimal | None,
    theoretical_edge: Decimal | None,
    spread: Decimal | None,
    slippage_estimate: Decimal | None,
    cost_adjusted_edge: Decimal | None,
    confidence: Decimal | None,
    max_executable_size: Decimal | None,
    risk_tags: tuple[str, ...],
    thesis: str,
    invalidating_conditions: str,
    rule_text: str,
    resolution_source: str,
) -> ResearchPacket:
    utc_created_at = _as_utc(created_at)
    timestamp = utc_created_at.strftime("%Y%m%dT%H%M%SZ")
    return ResearchPacket(
        packet_id=f"{candidate.condition_id}:{candidate.token_id}:{timestamp}",
        created_at=utc_created_at,
        condition_id=candidate.condition_id,
        token_id=candidate.token_id,
        market_slug=candidate.market_slug,
        question=candidate.question,
        source_score=candidate.total_score,
        raw_archive_path=candidate.raw_archive_path,
        market_url=market_url,
        outcome_name=outcome_name,
        strategy_type=strategy_type,
        model_probability=model_probability,
        bid=bid,
        ask=ask,
        midpoint=midpoint,
        expected_entry_price=expected_entry_price,
        fair_value_estimate=fair_value_estimate,
        theoretical_edge=theoretical_edge,
        spread=spread,
        slippage_estimate=slippage_estimate,
        cost_adjusted_edge=cost_adjusted_edge,
        confidence=confidence,
        max_executable_size=max_executable_size,
        risk_tags=tuple(risk_tags),
        thesis=thesis,
        invalidating_conditions=invalidating_conditions,
        rule_text=rule_text,
        rule_text_hash=sha256(rule_text.encode("utf-8")).hexdigest(),
        resolution_source=resolution_source,
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _has_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True

"""Paper-trade journal persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.research import ResearchPacket


@dataclass(frozen=True)
class PaperTradeRecord:
    packet_id: str
    packet_created_at: datetime
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    source_score: str
    market_raw_archive_path: str
    order_book_raw_archive_path: str
    order_book_raw_payload_sha256: str
    order_book_snapshot_sha256: str
    risk_tags: tuple[str, ...]
    rule_text_hash: str
    resolution_source: str
    decision_timestamp_utc: datetime
    model_probability: Decimal
    confidence: Decimal
    research_bid: Decimal
    research_ask: Decimal
    research_midpoint: Decimal
    research_expected_entry_price: Decimal
    research_fair_value_estimate: Decimal
    research_theoretical_edge: Decimal
    research_spread: Decimal
    research_slippage_estimate: Decimal
    research_cost_adjusted_edge: Decimal
    max_executable_size: Decimal
    order_side: str
    order_requested_size: Decimal
    fill_filled_size: Decimal
    fill_unfilled_size: Decimal
    fill_status: str
    fill_average_price: Decimal
    fill_worst_price: Decimal
    fill_best_bid: Decimal | None
    fill_best_ask: Decimal | None
    fill_midpoint: Decimal | None
    fill_spread: Decimal | None
    fill_slippage_estimate: Decimal | None
    order_book_captured_at: datetime
    account_equity_before_trade: Decimal
    sizing_limiter: str
    planned_exit_rule: str
    thesis: str
    invalidating_conditions: str

    @classmethod
    def from_packet_and_fill(
        cls,
        *,
        packet: ResearchPacket,
        fill: PaperFill,
        decision_timestamp: datetime,
        order_book_raw_archive_path: str,
        order_book_raw_payload_sha256: str,
        account_equity_before_trade: Decimal,
        sizing_limiter: str,
        planned_exit_rule: str,
    ) -> "PaperTradeRecord":
        missing = packet.missing_required_fields()
        if missing:
            raise ValueError(f"incomplete research packet: {', '.join(missing)}")
        if packet.token_id != fill.token_id:
            raise ValueError("packet token_id must match paper fill token_id")
        if fill.side not in ("buy", "sell"):
            raise ValueError("fill side must be buy or sell")
        for field_name, value in (
            ("requested_size", fill.requested_size),
            ("filled_size", fill.filled_size),
            ("unfilled_size", fill.unfilled_size),
            ("account_equity_before_trade", account_equity_before_trade),
        ):
            _require_finite_decimal(value, field_name)
        if fill.requested_size <= 0:
            raise ValueError("fill requested_size must be positive")
        if fill.filled_size <= 0:
            raise ValueError("paper fill must have positive filled_size")
        if fill.unfilled_size < 0:
            raise ValueError("fill unfilled_size must be nonnegative")
        if fill.filled_size + fill.unfilled_size != fill.requested_size:
            raise ValueError("fill accounting must match requested_size")
        if fill.average_price is None:
            raise ValueError("fill average_price is required for positive fills")
        if fill.worst_price is None:
            raise ValueError("fill worst_price is required for positive fills")
        if account_equity_before_trade <= 0:
            raise ValueError("account_equity_before_trade must be positive")
        if not sizing_limiter.strip():
            raise ValueError("sizing_limiter is required")
        if not planned_exit_rule.strip():
            raise ValueError("planned_exit_rule is required")
        if not order_book_raw_archive_path.strip():
            raise ValueError("order_book_raw_archive_path is required")
        if not _is_sha256(order_book_raw_payload_sha256):
            raise ValueError(
                "order_book_raw_payload_sha256 must be a lowercase 64-character hex digest"
            )
        if not _is_sha256(fill.order_book_snapshot_sha256):
            raise ValueError(
                "order_book_snapshot_sha256 must be a lowercase 64-character hex digest"
            )

        model_probability = _required_decimal(packet.model_probability, "model_probability")
        confidence = _required_decimal(packet.confidence, "confidence")
        bid = _required_decimal(packet.bid, "bid")
        ask = _required_decimal(packet.ask, "ask")
        midpoint = _required_decimal(packet.midpoint, "midpoint")
        expected_entry_price = _required_decimal(
            packet.expected_entry_price, "expected_entry_price"
        )
        fair_value_estimate = _required_decimal(
            packet.fair_value_estimate, "fair_value_estimate"
        )
        theoretical_edge = _required_decimal(packet.theoretical_edge, "theoretical_edge")
        spread = _required_decimal(packet.spread, "spread")
        slippage_estimate = _required_decimal(packet.slippage_estimate, "slippage_estimate")
        cost_adjusted_edge = _required_decimal(
            packet.cost_adjusted_edge, "cost_adjusted_edge"
        )
        max_executable_size = _required_decimal(
            packet.max_executable_size, "max_executable_size"
        )

        for field_name, value in (
            ("model_probability", model_probability),
            ("confidence", confidence),
            ("bid", bid),
            ("ask", ask),
            ("midpoint", midpoint),
            ("expected_entry_price", expected_entry_price),
            ("fair_value_estimate", fair_value_estimate),
            ("theoretical_edge", theoretical_edge),
            ("spread", spread),
            ("slippage_estimate", slippage_estimate),
            ("cost_adjusted_edge", cost_adjusted_edge),
            ("max_executable_size", max_executable_size),
            ("fill_average_price", fill.average_price),
            ("fill_worst_price", fill.worst_price),
        ):
            _require_finite_decimal(value, field_name)
        for field_name, value in (
            ("fill_best_bid", fill.best_bid),
            ("fill_best_ask", fill.best_ask),
            ("fill_midpoint", fill.midpoint),
            ("fill_spread", fill.spread),
            ("fill_slippage_estimate", fill.slippage_estimate),
        ):
            _require_optional_finite_decimal(value, field_name)

        _require_probability(model_probability, "model_probability")
        _require_probability(confidence, "confidence")
        for field_name, value in (
            ("bid", bid),
            ("ask", ask),
            ("midpoint", midpoint),
            ("expected_entry_price", expected_entry_price),
            ("fair_value_estimate", fair_value_estimate),
            ("fill_average_price", fill.average_price),
            ("fill_worst_price", fill.worst_price),
            ("fill_best_bid", fill.best_bid),
            ("fill_best_ask", fill.best_ask),
            ("fill_midpoint", fill.midpoint),
        ):
            _require_price_domain(value, field_name)

        if fill.requested_size > max_executable_size:
            raise ValueError("fill requested_size exceeds max_executable_size")
        if fill.filled_size > max_executable_size:
            raise ValueError("fill filled_size exceeds max_executable_size")

        return cls(
            packet_id=packet.packet_id,
            packet_created_at=_as_utc(packet.created_at),
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            market_url=packet.market_url,
            question=packet.question,
            outcome_name=packet.outcome_name,
            strategy_type=packet.strategy_type,
            source_score=packet.source_score,
            market_raw_archive_path=packet.raw_archive_path,
            order_book_raw_archive_path=order_book_raw_archive_path,
            order_book_raw_payload_sha256=order_book_raw_payload_sha256,
            order_book_snapshot_sha256=fill.order_book_snapshot_sha256,
            risk_tags=tuple(packet.risk_tags),
            rule_text_hash=packet.rule_text_hash,
            resolution_source=packet.resolution_source,
            decision_timestamp_utc=_as_utc(decision_timestamp),
            model_probability=model_probability,
            confidence=confidence,
            research_bid=bid,
            research_ask=ask,
            research_midpoint=midpoint,
            research_expected_entry_price=expected_entry_price,
            research_fair_value_estimate=fair_value_estimate,
            research_theoretical_edge=theoretical_edge,
            research_spread=spread,
            research_slippage_estimate=slippage_estimate,
            research_cost_adjusted_edge=cost_adjusted_edge,
            max_executable_size=max_executable_size,
            order_side=fill.side,
            order_requested_size=fill.requested_size,
            fill_filled_size=fill.filled_size,
            fill_unfilled_size=fill.unfilled_size,
            fill_status="complete" if fill.is_complete else "partial",
            fill_average_price=fill.average_price,
            fill_worst_price=fill.worst_price,
            fill_best_bid=fill.best_bid,
            fill_best_ask=fill.best_ask,
            fill_midpoint=fill.midpoint,
            fill_spread=fill.spread,
            fill_slippage_estimate=fill.slippage_estimate,
            order_book_captured_at=_as_utc(fill.order_book_captured_at),
            account_equity_before_trade=account_equity_before_trade,
            sizing_limiter=sizing_limiter,
            planned_exit_rule=planned_exit_rule,
            thesis=packet.thesis,
            invalidating_conditions=packet.invalidating_conditions,
        )


@dataclass(frozen=True)
class PaperTradeJournal:
    path: Path

    def append(self, record: PaperTradeRecord) -> None:
        line = json.dumps(_json_ready(asdict(record)), sort_keys=True) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _required_decimal(value: Decimal | None, field_name: str) -> Decimal:
    if value is None:
        raise ValueError(f"{field_name} is required")
    return value


def _require_finite_decimal(value: Decimal, field_name: str) -> None:
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_finite_decimal(value: Decimal | None, field_name: str) -> None:
    if value is not None:
        _require_finite_decimal(value, field_name)


def _require_probability(value: Decimal, field_name: str) -> None:
    _require_finite_decimal(value, field_name)
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be in [0, 1]")


def _require_price_domain(value: Decimal | None, field_name: str) -> None:
    if value is None:
        return
    _require_finite_decimal(value, field_name)
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be in [0, 1]")


def _is_sha256(value: str) -> bool:
    return (
        len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("journal Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value

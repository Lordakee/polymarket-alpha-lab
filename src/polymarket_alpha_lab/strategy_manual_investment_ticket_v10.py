"""Readonly manual investment ticket v10 for final paper candidates."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIDES = ("buy", "sell")


__all__ = (
    "StrategyManualInvestmentTicketV10Candidate",
    "StrategyManualInvestmentTicketV10CostSummary",
    "StrategyManualInvestmentTicketV10Ticket",
    "build_strategy_manual_investment_ticket_v10",
    "build_strategy_manual_investment_tickets_v10",
    "strategy_manual_investment_ticket_v10_payload",
)


@dataclass(frozen=True)
class StrategyManualInvestmentTicketV10CostSummary:
    gross_notional: Decimal
    estimated_fee: Decimal
    estimated_slippage: Decimal
    total_cost: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "gross_notional",
            _normalize_nonnegative_decimal("gross_notional", self.gross_notional),
        )
        object.__setattr__(
            self,
            "estimated_fee",
            _normalize_nonnegative_decimal("estimated_fee", self.estimated_fee),
        )
        object.__setattr__(
            self,
            "estimated_slippage",
            _normalize_nonnegative_decimal(
                "estimated_slippage",
                self.estimated_slippage,
            ),
        )
        object.__setattr__(
            self,
            "total_cost",
            _normalize_nonnegative_decimal("total_cost", self.total_cost),
        )
        if self.total_cost != (
            self.gross_notional + self.estimated_fee + self.estimated_slippage
        ).quantize(DECIMAL_QUANT):
            raise ValueError("total_cost must equal gross_notional plus costs")
        require_paper_only_flags("StrategyManualInvestmentTicketV10CostSummary", self)
        reject_unsafe_surface_fields(
            "StrategyManualInvestmentTicketV10CostSummary",
            self,
        )


@dataclass(frozen=True)
class StrategyManualInvestmentTicketV10Candidate:
    market_id: str
    outcome: str
    side: str
    limit_price: Decimal
    max_size: Decimal
    expected_value: Decimal
    estimated_fee: Decimal
    estimated_slippage: Decimal
    evidence_summary: tuple[str, ...]
    risk_warnings: tuple[str, ...]
    expiration_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("outcome", self.outcome)
        _require_side("side", self.side)
        object.__setattr__(
            self,
            "limit_price",
            _normalize_price("limit_price", self.limit_price),
        )
        object.__setattr__(
            self,
            "max_size",
            _normalize_positive_decimal("max_size", self.max_size),
        )
        object.__setattr__(
            self,
            "expected_value",
            _normalize_decimal("expected_value", self.expected_value),
        )
        object.__setattr__(
            self,
            "estimated_fee",
            _normalize_nonnegative_decimal("estimated_fee", self.estimated_fee),
        )
        object.__setattr__(
            self,
            "estimated_slippage",
            _normalize_nonnegative_decimal(
                "estimated_slippage",
                self.estimated_slippage,
            ),
        )
        object.__setattr__(
            self,
            "evidence_summary",
            _normalize_string_tuple("evidence_summary", self.evidence_summary),
        )
        if not self.evidence_summary:
            raise ValueError("evidence_summary must not be empty")
        object.__setattr__(
            self,
            "risk_warnings",
            _normalize_string_tuple("risk_warnings", self.risk_warnings),
        )
        object.__setattr__(
            self,
            "expiration_minutes",
            _normalize_positive_decimal(
                "expiration_minutes",
                self.expiration_minutes,
            ),
        )
        require_paper_only_flags("StrategyManualInvestmentTicketV10Candidate", self)
        reject_unsafe_surface_fields(
            "StrategyManualInvestmentTicketV10Candidate",
            self,
        )


@dataclass(frozen=True)
class StrategyManualInvestmentTicketV10Ticket:
    market_id: str
    outcome: str
    side: str
    limit_price: Decimal
    max_size: Decimal
    expected_value: Decimal
    cost_summary: StrategyManualInvestmentTicketV10CostSummary
    evidence_summary: tuple[str, ...]
    risk_warnings: tuple[str, ...]
    expiration_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("outcome", self.outcome)
        _require_side("side", self.side)
        object.__setattr__(
            self,
            "limit_price",
            _normalize_price("limit_price", self.limit_price),
        )
        object.__setattr__(
            self,
            "max_size",
            _normalize_positive_decimal("max_size", self.max_size),
        )
        object.__setattr__(
            self,
            "expected_value",
            _normalize_decimal("expected_value", self.expected_value),
        )
        if type(self.cost_summary) is not StrategyManualInvestmentTicketV10CostSummary:
            raise ValueError(
                "cost_summary must be a StrategyManualInvestmentTicketV10CostSummary",
            )
        object.__setattr__(
            self,
            "evidence_summary",
            _normalize_string_tuple("evidence_summary", self.evidence_summary),
        )
        if not self.evidence_summary:
            raise ValueError("evidence_summary must not be empty")
        object.__setattr__(
            self,
            "risk_warnings",
            _normalize_string_tuple("risk_warnings", self.risk_warnings),
        )
        object.__setattr__(
            self,
            "expiration_minutes",
            _normalize_positive_decimal(
                "expiration_minutes",
                self.expiration_minutes,
            ),
        )
        require_paper_only_flags("StrategyManualInvestmentTicketV10Ticket", self)
        reject_unsafe_surface_fields("StrategyManualInvestmentTicketV10Ticket", self)


def build_strategy_manual_investment_ticket_v10(
    candidate: StrategyManualInvestmentTicketV10Candidate,
) -> StrategyManualInvestmentTicketV10Ticket:
    if type(candidate) is not StrategyManualInvestmentTicketV10Candidate:
        raise ValueError(
            "candidate must be a StrategyManualInvestmentTicketV10Candidate",
        )
    require_paper_only_flags("StrategyManualInvestmentTicketV10Candidate", candidate)
    reject_unsafe_surface_fields(
        "StrategyManualInvestmentTicketV10Candidate",
        candidate,
    )
    gross_notional = (candidate.limit_price * candidate.max_size).quantize(
        DECIMAL_QUANT,
    )
    cost_summary = StrategyManualInvestmentTicketV10CostSummary(
        gross_notional=gross_notional,
        estimated_fee=candidate.estimated_fee,
        estimated_slippage=candidate.estimated_slippage,
        total_cost=(
            gross_notional + candidate.estimated_fee + candidate.estimated_slippage
        ).quantize(DECIMAL_QUANT),
    )
    return StrategyManualInvestmentTicketV10Ticket(
        market_id=candidate.market_id,
        outcome=candidate.outcome,
        side=candidate.side,
        limit_price=candidate.limit_price,
        max_size=candidate.max_size,
        expected_value=candidate.expected_value,
        cost_summary=cost_summary,
        evidence_summary=candidate.evidence_summary,
        risk_warnings=candidate.risk_warnings,
        expiration_minutes=candidate.expiration_minutes,
    )


def build_strategy_manual_investment_tickets_v10(
    candidates: Iterable[StrategyManualInvestmentTicketV10Candidate],
) -> tuple[StrategyManualInvestmentTicketV10Ticket, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc

    seen_keys: set[tuple[str, str, str]] = set()
    tickets: list[StrategyManualInvestmentTicketV10Ticket] = []
    for item in items:
        if type(item) is not StrategyManualInvestmentTicketV10Candidate:
            raise ValueError(
                "candidates must contain StrategyManualInvestmentTicketV10Candidate values",
            )
        key = (item.market_id, item.outcome, item.side)
        if key in seen_keys:
            raise ValueError("duplicate market_id/outcome/side tickets")
        seen_keys.add(key)
        tickets.append(build_strategy_manual_investment_ticket_v10(item))
    return tuple(tickets)


def strategy_manual_investment_ticket_v10_payload(
    ticket: StrategyManualInvestmentTicketV10Ticket,
) -> dict[str, Any]:
    if type(ticket) is not StrategyManualInvestmentTicketV10Ticket:
        raise ValueError("ticket must be a StrategyManualInvestmentTicketV10Ticket")
    require_paper_only_flags("StrategyManualInvestmentTicketV10Ticket", ticket)
    reject_unsafe_surface_fields("StrategyManualInvestmentTicketV10Ticket", ticket)
    payload = json_ready_no_floats(ticket)
    if type(payload) is not dict:
        raise ValueError("ticket must serialize to a JSON object")
    reject_unsafe_surface_fields("StrategyManualInvestmentTicketV10Ticket payload", payload)
    return payload


def _normalize_price(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO or normalized >= ONE:
        raise ValueError(f"{field_name} must be greater than zero and less than one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be greater than zero")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANT)


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be buy or sell")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")

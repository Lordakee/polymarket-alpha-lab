from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


CONFIG_VERSION = "strategy-recommendation-manual-order-ticket-v2"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

_UNSAFE_FRAGMENTS = (
    "api" + "_key",
    "sec" + "ret",
    "tok" + "en",
    "pass" + "word",
    "private" + "_key",
    "wal" + "let",
    "au" + "th",
    "bro" + "ker",
    "sig" + "ning",
)


@dataclass(frozen=True)
class StrategyRecommendationManualOrderTicketV2Config:
    config_version: str = CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be strategy-recommendation-manual-order-ticket-v2")
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationManualOrderTicketV2Input:
    recommendation_id: str
    market_id: str
    side: str
    recommendation_rationale: str
    max_price: Decimal
    size_cap: Decimal
    estimated_fee: Decimal
    estimated_slippage: Decimal
    risk_reasons: tuple[str, ...]
    abstain_conditions: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_id", self.market_id)
        if self.side not in ("buy", "sell"):
            raise ValueError("side must be buy or sell")
        _require_canonical_string("recommendation_rationale", self.recommendation_rationale)
        object.__setattr__(self, "max_price", _decimal_between_zero_and_one("max_price", self.max_price))
        object.__setattr__(self, "size_cap", _positive_decimal("size_cap", self.size_cap))
        object.__setattr__(self, "estimated_fee", _nonnegative_decimal("estimated_fee", self.estimated_fee))
        object.__setattr__(
            self,
            "estimated_slippage",
            _nonnegative_decimal("estimated_slippage", self.estimated_slippage),
        )
        object.__setattr__(
            self,
            "risk_reasons",
            _canonical_string_tuple("risk_reasons", self.risk_reasons, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "abstain_conditions",
            _canonical_string_tuple(
                "abstain_conditions",
                self.abstain_conditions,
                require_nonempty=True,
            ),
        )
        _reject_unsafe_value(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationManualOrderTicketV2Ticket:
    recommendation_id: str
    market_id: str
    side: str
    recommendation_rationale: str
    max_price: Decimal
    size_cap: Decimal
    estimated_notional: Decimal
    estimated_fee: Decimal
    estimated_slippage: Decimal
    estimated_total_cost: Decimal
    risk_reasons: tuple[str, ...]
    abstain_conditions: tuple[str, ...]
    manual_ticket_text: str
    ticket_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_id", self.market_id)
        if self.side not in ("buy", "sell"):
            raise ValueError("side must be buy or sell")
        _require_canonical_string("recommendation_rationale", self.recommendation_rationale)
        object.__setattr__(self, "max_price", _decimal_between_zero_and_one("max_price", self.max_price))
        object.__setattr__(self, "size_cap", _positive_decimal("size_cap", self.size_cap))
        object.__setattr__(self, "estimated_notional", _nonnegative_decimal("estimated_notional", self.estimated_notional))
        object.__setattr__(self, "estimated_fee", _nonnegative_decimal("estimated_fee", self.estimated_fee))
        object.__setattr__(self, "estimated_slippage", _nonnegative_decimal("estimated_slippage", self.estimated_slippage))
        object.__setattr__(
            self,
            "estimated_total_cost",
            _nonnegative_decimal("estimated_total_cost", self.estimated_total_cost),
        )
        object.__setattr__(
            self,
            "risk_reasons",
            _canonical_string_tuple("risk_reasons", self.risk_reasons, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "abstain_conditions",
            _canonical_string_tuple(
                "abstain_conditions",
                self.abstain_conditions,
                require_nonempty=True,
            ),
        )
        _require_canonical_string("manual_ticket_text", self.manual_ticket_text)
        _require_hard_flags(self)
        _reject_unsafe_value(self)
        _validate_ticket(self)
        if self.ticket_digest == "":
            object.__setattr__(self, "ticket_digest", _digest(_ticket_payload_without_digest(self)))
        else:
            _require_sha256("ticket_digest", self.ticket_digest)
            if self.ticket_digest != _digest(_ticket_payload_without_digest(self)):
                raise ValueError("ticket_digest must match ticket fields")


@dataclass(frozen=True)
class StrategyRecommendationManualOrderTicketV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    ticket_count: Decimal
    buy_count: Decimal
    sell_count: Decimal
    total_size_cap: Decimal
    total_estimated_notional: Decimal
    total_estimated_fee: Decimal
    total_estimated_slippage: Decimal
    total_estimated_total_cost: Decimal
    tickets: tuple[StrategyRecommendationManualOrderTicketV2Ticket, ...]
    report_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be strategy-recommendation-manual-order-ticket-v2")
        if self.report_status not in ("empty", "ready"):
            raise ValueError("report_status must be empty or ready")
        for field_name in (
            "ticket_count",
            "buy_count",
            "sell_count",
        ):
            object.__setattr__(self, field_name, _count_decimal(field_name, getattr(self, field_name)))
        for field_name in (
            "total_size_cap",
            "total_estimated_notional",
            "total_estimated_fee",
            "total_estimated_slippage",
            "total_estimated_total_cost",
        ):
            object.__setattr__(self, field_name, _nonnegative_decimal(field_name, getattr(self, field_name)))
        if type(self.tickets) is not tuple:
            raise ValueError("tickets must be a tuple")
        for ticket in self.tickets:
            if type(ticket) is not StrategyRecommendationManualOrderTicketV2Ticket:
                raise ValueError("tickets must contain StrategyRecommendationManualOrderTicketV2Ticket")
            _require_hard_flags(ticket)
        _require_hard_flags(self)
        _reject_unsafe_value(self)
        _validate_report(self)
        if self.report_digest == "":
            object.__setattr__(self, "report_digest", _digest(_report_payload_without_digest(self)))
        else:
            _require_sha256("report_digest", self.report_digest)
            if self.report_digest != _digest(_report_payload_without_digest(self)):
                raise ValueError("report_digest must match report fields")


def build_strategy_recommendation_manual_order_ticket_v2(
    recommendations: tuple[StrategyRecommendationManualOrderTicketV2Input, ...],
    *,
    config: StrategyRecommendationManualOrderTicketV2Config,
    generated_at: datetime,
) -> StrategyRecommendationManualOrderTicketV2Report:
    if type(config) is not StrategyRecommendationManualOrderTicketV2Config:
        raise ValueError("config must be StrategyRecommendationManualOrderTicketV2Config")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if type(recommendations) not in (tuple, list):
        raise ValueError("recommendations must be a tuple or list")
    inputs = tuple(recommendations)
    for item in inputs:
        if type(item) is not StrategyRecommendationManualOrderTicketV2Input:
            raise ValueError("recommendations must contain StrategyRecommendationManualOrderTicketV2Input")
        _require_hard_flags(item)
    _require_unique_ids(inputs)
    tickets = tuple(sorted((_ticket_from_input(item) for item in inputs), key=_ticket_sort_key))
    return StrategyRecommendationManualOrderTicketV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status="ready" if tickets else "empty",
        ticket_count=_count(len(tickets)),
        buy_count=_count(sum(1 for ticket in tickets if ticket.side == "buy")),
        sell_count=_count(sum(1 for ticket in tickets if ticket.side == "sell")),
        total_size_cap=_sum_decimal(tuple(ticket.size_cap for ticket in tickets)),
        total_estimated_notional=_sum_decimal(tuple(ticket.estimated_notional for ticket in tickets)),
        total_estimated_fee=_sum_decimal(tuple(ticket.estimated_fee for ticket in tickets)),
        total_estimated_slippage=_sum_decimal(tuple(ticket.estimated_slippage for ticket in tickets)),
        total_estimated_total_cost=_sum_decimal(tuple(ticket.estimated_total_cost for ticket in tickets)),
        tickets=tickets,
    )


def strategy_recommendation_manual_order_ticket_v2_payload(
    report: StrategyRecommendationManualOrderTicketV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is StrategyRecommendationManualOrderTicketV2Report:
        _require_hard_flags(report)
        _validate_report(report)
        return _report_payload(report)
    if type(report) is dict:
        _validate_payload(report)
        return dict(report)
    raise ValueError("report must be StrategyRecommendationManualOrderTicketV2Report")


def _ticket_from_input(
    item: StrategyRecommendationManualOrderTicketV2Input,
) -> StrategyRecommendationManualOrderTicketV2Ticket:
    estimated_notional = _money(item.max_price * item.size_cap)
    estimated_total_cost = _money(
        estimated_notional + item.estimated_fee + item.estimated_slippage,
    )
    return StrategyRecommendationManualOrderTicketV2Ticket(
        recommendation_id=item.recommendation_id,
        market_id=item.market_id,
        side=item.side,
        recommendation_rationale=item.recommendation_rationale,
        max_price=item.max_price,
        size_cap=item.size_cap,
        estimated_notional=estimated_notional,
        estimated_fee=item.estimated_fee,
        estimated_slippage=item.estimated_slippage,
        estimated_total_cost=estimated_total_cost,
        risk_reasons=item.risk_reasons,
        abstain_conditions=item.abstain_conditions,
        manual_ticket_text=_manual_ticket_text(
            side=item.side,
            market_id=item.market_id,
            max_price=item.max_price,
            size_cap=item.size_cap,
            estimated_notional=estimated_notional,
            estimated_fee=item.estimated_fee,
            estimated_slippage=item.estimated_slippage,
            estimated_total_cost=estimated_total_cost,
            recommendation_rationale=item.recommendation_rationale,
            risk_reasons=item.risk_reasons,
            abstain_conditions=item.abstain_conditions,
        ),
    )


def _manual_ticket_text(
    *,
    side: str,
    market_id: str,
    max_price: Decimal,
    size_cap: Decimal,
    estimated_notional: Decimal,
    estimated_fee: Decimal,
    estimated_slippage: Decimal,
    estimated_total_cost: Decimal,
    recommendation_rationale: str,
    risk_reasons: tuple[str, ...],
    abstain_conditions: tuple[str, ...],
) -> str:
    return (
        f"MANUAL REVIEW ONLY | side={side} | market_id={market_id} | "
        f"max_price={_decimal_payload(max_price)} | size_cap={_decimal_payload(size_cap)} | "
        f"estimated_notional={_decimal_payload(estimated_notional)} | "
        f"estimated_fee={_decimal_payload(estimated_fee)} | "
        f"estimated_slippage={_decimal_payload(estimated_slippage)} | "
        f"estimated_total_cost={_decimal_payload(estimated_total_cost)} | "
        f"rationale={recommendation_rationale} | "
        f"risk_reasons={'; '.join(risk_reasons)} | "
        f"abstain_conditions={'; '.join(abstain_conditions)}"
    )


def _validate_ticket(ticket: StrategyRecommendationManualOrderTicketV2Ticket) -> None:
    expected_notional = _money(ticket.max_price * ticket.size_cap)
    if ticket.estimated_notional != expected_notional:
        raise ValueError("estimated_notional must match max_price and size_cap")
    expected_total_cost = _money(
        ticket.estimated_notional + ticket.estimated_fee + ticket.estimated_slippage,
    )
    if ticket.estimated_total_cost != expected_total_cost:
        raise ValueError("estimated_total_cost must match estimated components")
    expected_text = _manual_ticket_text(
        side=ticket.side,
        market_id=ticket.market_id,
        max_price=ticket.max_price,
        size_cap=ticket.size_cap,
        estimated_notional=ticket.estimated_notional,
        estimated_fee=ticket.estimated_fee,
        estimated_slippage=ticket.estimated_slippage,
        estimated_total_cost=ticket.estimated_total_cost,
        recommendation_rationale=ticket.recommendation_rationale,
        risk_reasons=ticket.risk_reasons,
        abstain_conditions=ticket.abstain_conditions,
    )
    if ticket.manual_ticket_text != expected_text:
        raise ValueError("manual_ticket_text must match ticket fields")


def _validate_report(report: StrategyRecommendationManualOrderTicketV2Report) -> None:
    if report.ticket_count != _count(len(report.tickets)):
        raise ValueError("ticket_count must match tickets")
    if report.buy_count != _count(sum(1 for ticket in report.tickets if ticket.side == "buy")):
        raise ValueError("buy_count must match tickets")
    if report.sell_count != _count(sum(1 for ticket in report.tickets if ticket.side == "sell")):
        raise ValueError("sell_count must match tickets")
    expected_status = "ready" if report.tickets else "empty"
    if report.report_status != expected_status:
        raise ValueError("report_status must match tickets")
    if report.total_size_cap != _sum_decimal(tuple(ticket.size_cap for ticket in report.tickets)):
        raise ValueError("total_size_cap must match tickets")
    if report.total_estimated_notional != _sum_decimal(
        tuple(ticket.estimated_notional for ticket in report.tickets),
    ):
        raise ValueError("total_estimated_notional must match tickets")
    if report.total_estimated_fee != _sum_decimal(tuple(ticket.estimated_fee for ticket in report.tickets)):
        raise ValueError("total_estimated_fee must match tickets")
    if report.total_estimated_slippage != _sum_decimal(
        tuple(ticket.estimated_slippage for ticket in report.tickets),
    ):
        raise ValueError("total_estimated_slippage must match tickets")
    if report.total_estimated_total_cost != _sum_decimal(
        tuple(ticket.estimated_total_cost for ticket in report.tickets),
    ):
        raise ValueError("total_estimated_total_cost must match tickets")
    if report.tickets != tuple(sorted(report.tickets, key=_ticket_sort_key)):
        raise ValueError("tickets must be sorted deterministically")


def _ticket_sort_key(
    ticket: StrategyRecommendationManualOrderTicketV2Ticket,
) -> tuple[str, str]:
    return (ticket.market_id, ticket.recommendation_id)


def _require_unique_ids(
    rows: tuple[StrategyRecommendationManualOrderTicketV2Input, ...],
) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.recommendation_id in seen:
            raise ValueError("recommendation_id values must be unique")
        seen.add(row.recommendation_id)


def _report_payload(report: StrategyRecommendationManualOrderTicketV2Report) -> dict[str, object]:
    payload = _report_payload_without_digest(report)
    payload["report_digest"] = report.report_digest
    return payload


def _report_payload_without_digest(
    report: StrategyRecommendationManualOrderTicketV2Report,
) -> dict[str, object]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "report_status": report.report_status,
        "ticket_count": _count_payload(report.ticket_count),
        "buy_count": _count_payload(report.buy_count),
        "sell_count": _count_payload(report.sell_count),
        "total_size_cap": _decimal_payload(report.total_size_cap),
        "total_estimated_notional": _decimal_payload(report.total_estimated_notional),
        "total_estimated_fee": _decimal_payload(report.total_estimated_fee),
        "total_estimated_slippage": _decimal_payload(report.total_estimated_slippage),
        "total_estimated_total_cost": _decimal_payload(report.total_estimated_total_cost),
        "tickets": [_ticket_payload(ticket) for ticket in report.tickets],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _ticket_payload(ticket: StrategyRecommendationManualOrderTicketV2Ticket) -> dict[str, object]:
    payload = _ticket_payload_without_digest(ticket)
    payload["ticket_digest"] = ticket.ticket_digest
    return payload


def _ticket_payload_without_digest(
    ticket: StrategyRecommendationManualOrderTicketV2Ticket,
) -> dict[str, object]:
    return {
        "recommendation_id": ticket.recommendation_id,
        "market_id": ticket.market_id,
        "side": ticket.side,
        "recommendation_rationale": ticket.recommendation_rationale,
        "max_price": _decimal_payload(ticket.max_price),
        "size_cap": _decimal_payload(ticket.size_cap),
        "estimated_notional": _decimal_payload(ticket.estimated_notional),
        "estimated_fee": _decimal_payload(ticket.estimated_fee),
        "estimated_slippage": _decimal_payload(ticket.estimated_slippage),
        "estimated_total_cost": _decimal_payload(ticket.estimated_total_cost),
        "risk_reasons": list(ticket.risk_reasons),
        "abstain_conditions": list(ticket.abstain_conditions),
        "manual_ticket_text": ticket.manual_ticket_text,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload(payload: dict[str, object]) -> None:
    _reject_unsafe_value(payload)
    _reject_numeric_payload(payload)
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")
    if type(payload.get("tickets")) is not list:
        raise ValueError("tickets must be a list")
    report_payload = dict(payload)
    report_digest = report_payload.pop("report_digest", None)
    _require_sha256("report_digest", report_digest)
    if report_digest != _digest(report_payload):
        raise ValueError("report_digest must match payload fields")
    for ticket in payload["tickets"]:
        if type(ticket) is not dict:
            raise ValueError("tickets must contain payload objects")
        for flag_name in ("paper_only", "report_only", "readonly"):
            if ticket.get(flag_name) is not True:
                raise ValueError(f"{flag_name} must be True")
        ticket_payload = dict(ticket)
        ticket_digest = ticket_payload.pop("ticket_digest", None)
        _require_sha256("ticket_digest", ticket_digest)
        if ticket_digest != _digest(ticket_payload):
            raise ValueError("ticket_digest must match payload fields")


def _reject_numeric_payload(value: object) -> None:
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is Decimal:
        raise ValueError("payload must use Decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_numeric_payload(item)
    if type(value) is list:
        for item in value:
            _reject_numeric_payload(item)


def _reject_unsafe_value(value: object) -> None:
    if is_dataclass(value):
        for field in fields(value):
            _reject_unsafe_value(getattr(value, field.name))
        return
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_text(str(key))
            _reject_unsafe_value(item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_value(item)
        return
    if type(value) is str:
        _reject_unsafe_text(value)


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_FRAGMENTS):
        raise ValueError("unsafe value is not allowed")


def _canonical_string_tuple(
    field_name: str,
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if require_nonempty and not value:
        raise ValueError(f"{field_name} must contain at least one value")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        normalized.append(item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(normalized)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be canonical")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _decimal_between_zero_and_one(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _money(value)


def _count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value


def _count(value: int) -> Decimal:
    return Decimal(str(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _money(total)


def _money(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_payload(value: datetime) -> str:
    if value.tzinfo is not UTC:
        value = value.astimezone(UTC)
    return value.isoformat().replace("+00:00", "Z")


def _decimal_payload(value: Decimal) -> str:
    return f"{value:.6f}"


def _count_payload(value: Decimal) -> str:
    return str(value.to_integral_value())


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")


__all__ = (
    "StrategyRecommendationManualOrderTicketV2Config",
    "StrategyRecommendationManualOrderTicketV2Input",
    "StrategyRecommendationManualOrderTicketV2Report",
    "StrategyRecommendationManualOrderTicketV2Ticket",
    "build_strategy_recommendation_manual_order_ticket_v2",
    "strategy_recommendation_manual_order_ticket_v2_payload",
)

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json


CONFIG_VERSION = "strategy-manual-order-ticket-cost-breakdown-v2"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_THRESHOLD = Decimal("0.900000")

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
    "net" + "work",
    "li" + "ve",
    "tra" + "de",
    "exe" + "cution",
    "place_" + "order",
    "submit_" + "order",
    "send_" + "order",
    "cancel_" + "order",
    "replace_" + "order",
)


@dataclass(frozen=True)
class StrategyManualOrderTicketCostBreakdownV2Config:
    config_version: str = CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be strategy-manual-order-ticket-cost-breakdown-v2")
        _require_hard_flags(self)
        _reject_unsafe_value(self)


@dataclass(frozen=True)
class StrategyManualOrderTicketCostBreakdownV2Input:
    candidate_id: str
    market_id: str
    event_slug: str
    side: str
    limit_price: Decimal
    estimated_shares: Decimal
    taker_fee_rate: Decimal
    settlement_cost_rate: Decimal
    slippage_buffer_rate: Decimal
    max_notional_usdc: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("event_slug", self.event_slug)
        if self.side not in ("buy", "sell"):
            raise ValueError("side must be buy or sell")
        object.__setattr__(self, "limit_price", _decimal_between_zero_and_one("limit_price", self.limit_price))
        object.__setattr__(self, "estimated_shares", _positive_decimal("estimated_shares", self.estimated_shares))
        object.__setattr__(
            self,
            "taker_fee_rate",
            _decimal_between_zero_and_one("taker_fee_rate", self.taker_fee_rate),
        )
        object.__setattr__(
            self,
            "settlement_cost_rate",
            _decimal_between_zero_and_one("settlement_cost_rate", self.settlement_cost_rate),
        )
        object.__setattr__(
            self,
            "slippage_buffer_rate",
            _decimal_between_zero_and_one("slippage_buffer_rate", self.slippage_buffer_rate),
        )
        object.__setattr__(
            self,
            "max_notional_usdc",
            _positive_decimal("max_notional_usdc", self.max_notional_usdc),
        )
        _require_hard_flags(self)
        _reject_unsafe_value(self)


@dataclass(frozen=True)
class StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount:
    reason_code: str
    count: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _count_decimal("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _reject_unsafe_value(self)


@dataclass(frozen=True)
class StrategyManualOrderTicketCostBreakdownV2Row:
    candidate_id: str
    market_id: str
    event_slug: str
    side: str
    limit_price: Decimal
    estimated_shares: Decimal
    taker_fee_rate: Decimal
    settlement_cost_rate: Decimal
    slippage_buffer_rate: Decimal
    max_notional_usdc: Decimal
    estimated_notional_usdc: Decimal
    fee_usdc: Decimal
    settlement_cost_usdc: Decimal
    slippage_buffer_usdc: Decimal
    all_in_cost_usdc: Decimal
    max_loss_usdc: Decimal
    status: str
    reason_codes: tuple[str, ...]
    manual_ticket_text: str
    row_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("event_slug", self.event_slug)
        if self.side not in ("buy", "sell"):
            raise ValueError("side must be buy or sell")
        object.__setattr__(self, "limit_price", _decimal_between_zero_and_one("limit_price", self.limit_price))
        object.__setattr__(self, "estimated_shares", _positive_decimal("estimated_shares", self.estimated_shares))
        object.__setattr__(
            self,
            "taker_fee_rate",
            _decimal_between_zero_and_one("taker_fee_rate", self.taker_fee_rate),
        )
        object.__setattr__(
            self,
            "settlement_cost_rate",
            _decimal_between_zero_and_one("settlement_cost_rate", self.settlement_cost_rate),
        )
        object.__setattr__(
            self,
            "slippage_buffer_rate",
            _decimal_between_zero_and_one("slippage_buffer_rate", self.slippage_buffer_rate),
        )
        object.__setattr__(
            self,
            "max_notional_usdc",
            _positive_decimal("max_notional_usdc", self.max_notional_usdc),
        )
        for field_name in (
            "estimated_notional_usdc",
            "fee_usdc",
            "settlement_cost_usdc",
            "slippage_buffer_usdc",
            "all_in_cost_usdc",
            "max_loss_usdc",
        ):
            object.__setattr__(self, field_name, _nonnegative_decimal(field_name, getattr(self, field_name)))
        if self.status not in ("pass", "watch", "block"):
            raise ValueError("status must be pass, watch, or block")
        object.__setattr__(
            self,
            "reason_codes",
            _canonical_string_tuple("reason_codes", self.reason_codes, require_nonempty=False),
        )
        _require_canonical_string("manual_ticket_text", self.manual_ticket_text)
        _require_hard_flags(self)
        _reject_unsafe_value(self)
        _validate_row(self)
        if self.row_digest == "":
            object.__setattr__(self, "row_digest", _digest(_row_payload_without_digest(self)))
        else:
            _require_sha256("row_digest", self.row_digest)
            if self.row_digest != _digest(_row_payload_without_digest(self)):
                raise ValueError("row_digest must match row fields")


@dataclass(frozen=True)
class StrategyManualOrderTicketCostBreakdownV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    ticket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_estimated_notional_usdc: Decimal
    total_all_in_cost_usdc: Decimal
    blocked_cost_count: Decimal
    reason_code_counts: tuple[StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount, ...]
    rows: tuple[StrategyManualOrderTicketCostBreakdownV2Row, ...]
    report_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be strategy-manual-order-ticket-cost-breakdown-v2")
        if self.report_status not in ("empty", "pass", "watch", "block"):
            raise ValueError("report_status must be empty, pass, watch, or block")
        for field_name in (
            "ticket_count",
            "pass_count",
            "watch_count",
            "block_count",
            "blocked_cost_count",
        ):
            object.__setattr__(self, field_name, _count_decimal(field_name, getattr(self, field_name)))
        for field_name in (
            "total_estimated_notional_usdc",
            "total_all_in_cost_usdc",
        ):
            object.__setattr__(self, field_name, _nonnegative_decimal(field_name, getattr(self, field_name)))
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for item in self.reason_code_counts:
            if type(item) is not StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount:
                raise ValueError("reason_code_counts must contain reason code count rows")
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not StrategyManualOrderTicketCostBreakdownV2Row:
                raise ValueError("rows must contain StrategyManualOrderTicketCostBreakdownV2Row")
            _require_hard_flags(row)
        _require_hard_flags(self)
        _reject_unsafe_value(self)
        _validate_report(self)
        if self.report_digest == "":
            object.__setattr__(self, "report_digest", _digest(_report_payload_without_digest(self)))
        else:
            _require_sha256("report_digest", self.report_digest)
            if self.report_digest != _digest(_report_payload_without_digest(self)):
                raise ValueError("report_digest must match report fields")


def build_strategy_manual_order_ticket_cost_breakdown_v2(
    items: tuple[StrategyManualOrderTicketCostBreakdownV2Input, ...],
    *,
    config: StrategyManualOrderTicketCostBreakdownV2Config,
    generated_at: datetime,
) -> StrategyManualOrderTicketCostBreakdownV2Report:
    if type(config) is not StrategyManualOrderTicketCostBreakdownV2Config:
        raise ValueError("config must be StrategyManualOrderTicketCostBreakdownV2Config")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if type(items) not in (tuple, list):
        raise ValueError("items must be a tuple or list")
    inputs = tuple(items)
    for item in inputs:
        if type(item) is not StrategyManualOrderTicketCostBreakdownV2Input:
            raise ValueError("items must contain StrategyManualOrderTicketCostBreakdownV2Input")
        _require_hard_flags(item)
    _require_unique_ids(inputs)
    rows = tuple(sorted((_row_from_input(item) for item in inputs), key=_row_sort_key))
    return StrategyManualOrderTicketCostBreakdownV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        ticket_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        total_estimated_notional_usdc=_sum_decimal(tuple(row.estimated_notional_usdc for row in rows)),
        total_all_in_cost_usdc=_sum_decimal(tuple(row.all_in_cost_usdc for row in rows)),
        blocked_cost_count=_count(sum(1 for row in rows if row.status == "block")),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_manual_order_ticket_cost_breakdown_v2_payload(
    report: StrategyManualOrderTicketCostBreakdownV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is StrategyManualOrderTicketCostBreakdownV2Report:
        _require_hard_flags(report)
        _validate_report(report)
        return _report_payload(report)
    if type(report) is dict:
        _validate_payload(report)
        return dict(report)
    raise ValueError("report must be StrategyManualOrderTicketCostBreakdownV2Report")


def _row_from_input(item: StrategyManualOrderTicketCostBreakdownV2Input) -> StrategyManualOrderTicketCostBreakdownV2Row:
    estimated_notional_usdc = _money(item.limit_price * item.estimated_shares)
    fee_usdc = _money(estimated_notional_usdc * item.taker_fee_rate)
    settlement_cost_usdc = _money(estimated_notional_usdc * item.settlement_cost_rate)
    slippage_buffer_usdc = _money(estimated_notional_usdc * item.slippage_buffer_rate)
    all_in_cost_usdc = _money(
        estimated_notional_usdc + fee_usdc + settlement_cost_usdc + slippage_buffer_usdc,
    )
    max_loss_usdc = all_in_cost_usdc
    reason_codes = _reason_codes(
        estimated_notional_usdc=estimated_notional_usdc,
        all_in_cost_usdc=all_in_cost_usdc,
        max_notional_usdc=item.max_notional_usdc,
    )
    status = _row_status(reason_codes)
    return StrategyManualOrderTicketCostBreakdownV2Row(
        candidate_id=item.candidate_id,
        market_id=item.market_id,
        event_slug=item.event_slug,
        side=item.side,
        limit_price=item.limit_price,
        estimated_shares=item.estimated_shares,
        taker_fee_rate=item.taker_fee_rate,
        settlement_cost_rate=item.settlement_cost_rate,
        slippage_buffer_rate=item.slippage_buffer_rate,
        max_notional_usdc=item.max_notional_usdc,
        estimated_notional_usdc=estimated_notional_usdc,
        fee_usdc=fee_usdc,
        settlement_cost_usdc=settlement_cost_usdc,
        slippage_buffer_usdc=slippage_buffer_usdc,
        all_in_cost_usdc=all_in_cost_usdc,
        max_loss_usdc=max_loss_usdc,
        status=status,
        reason_codes=reason_codes,
        manual_ticket_text=_manual_ticket_text(
            candidate_id=item.candidate_id,
            event_slug=item.event_slug,
            market_id=item.market_id,
            side=item.side,
            limit_price=item.limit_price,
            estimated_shares=item.estimated_shares,
            estimated_notional_usdc=estimated_notional_usdc,
            fee_usdc=fee_usdc,
            settlement_cost_usdc=settlement_cost_usdc,
            slippage_buffer_usdc=slippage_buffer_usdc,
            all_in_cost_usdc=all_in_cost_usdc,
            max_loss_usdc=max_loss_usdc,
            max_notional_usdc=item.max_notional_usdc,
            status=status,
            reason_codes=reason_codes,
        ),
    )


def _manual_ticket_text(
    *,
    candidate_id: str,
    event_slug: str,
    market_id: str,
    side: str,
    limit_price: Decimal,
    estimated_shares: Decimal,
    estimated_notional_usdc: Decimal,
    fee_usdc: Decimal,
    settlement_cost_usdc: Decimal,
    slippage_buffer_usdc: Decimal,
    all_in_cost_usdc: Decimal,
    max_loss_usdc: Decimal,
    max_notional_usdc: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
) -> str:
    reason_text = "; ".join(reason_codes) if reason_codes else "none"
    return (
        "PHASE 1 MANUAL REVIEW ONLY | readonly=true | report_only=true | paper_only=true | "
        f"candidate_id={candidate_id} | event_slug={event_slug} | market_id={market_id} | "
        f"side={side} | limit_price={_decimal_payload(limit_price)} | "
        f"estimated_shares={_decimal_payload(estimated_shares)} | "
        f"estimated_notional_usdc={_decimal_payload(estimated_notional_usdc)} | "
        f"fee_usdc={_decimal_payload(fee_usdc)} | "
        f"settlement_cost_usdc={_decimal_payload(settlement_cost_usdc)} | "
        f"slippage_buffer_usdc={_decimal_payload(slippage_buffer_usdc)} | "
        f"all_in_cost_usdc={_decimal_payload(all_in_cost_usdc)} | "
        f"max_loss_usdc={_decimal_payload(max_loss_usdc)} | "
        f"max_notional_usdc={_decimal_payload(max_notional_usdc)} | "
        f"status={status} | reason_codes={reason_text}"
    )


def _validate_row(row: StrategyManualOrderTicketCostBreakdownV2Row) -> None:
    estimated_notional_usdc = _money(row.limit_price * row.estimated_shares)
    if row.estimated_notional_usdc != estimated_notional_usdc:
        raise ValueError("estimated_notional_usdc must match limit_price and estimated_shares")
    fee_usdc = _money(row.estimated_notional_usdc * row.taker_fee_rate)
    if row.fee_usdc != fee_usdc:
        raise ValueError("fee_usdc must match estimated_notional_usdc and taker_fee_rate")
    settlement_cost_usdc = _money(row.estimated_notional_usdc * row.settlement_cost_rate)
    if row.settlement_cost_usdc != settlement_cost_usdc:
        raise ValueError("settlement_cost_usdc must match estimated_notional_usdc and settlement_cost_rate")
    slippage_buffer_usdc = _money(row.estimated_notional_usdc * row.slippage_buffer_rate)
    if row.slippage_buffer_usdc != slippage_buffer_usdc:
        raise ValueError("slippage_buffer_usdc must match estimated_notional_usdc and slippage_buffer_rate")
    all_in_cost_usdc = _money(
        row.estimated_notional_usdc + row.fee_usdc + row.settlement_cost_usdc + row.slippage_buffer_usdc,
    )
    if row.all_in_cost_usdc != all_in_cost_usdc:
        raise ValueError("all_in_cost_usdc must match estimated cost components")
    if row.max_loss_usdc != row.all_in_cost_usdc:
        raise ValueError("max_loss_usdc must match all_in_cost_usdc")
    reason_codes = _reason_codes(
        estimated_notional_usdc=row.estimated_notional_usdc,
        all_in_cost_usdc=row.all_in_cost_usdc,
        max_notional_usdc=row.max_notional_usdc,
    )
    if row.reason_codes != reason_codes:
        raise ValueError("reason_codes must match row fields")
    if row.status != _row_status(reason_codes):
        raise ValueError("status must match row fields")
    expected_text = _manual_ticket_text(
        candidate_id=row.candidate_id,
        event_slug=row.event_slug,
        market_id=row.market_id,
        side=row.side,
        limit_price=row.limit_price,
        estimated_shares=row.estimated_shares,
        estimated_notional_usdc=row.estimated_notional_usdc,
        fee_usdc=row.fee_usdc,
        settlement_cost_usdc=row.settlement_cost_usdc,
        slippage_buffer_usdc=row.slippage_buffer_usdc,
        all_in_cost_usdc=row.all_in_cost_usdc,
        max_loss_usdc=row.max_loss_usdc,
        max_notional_usdc=row.max_notional_usdc,
        status=row.status,
        reason_codes=row.reason_codes,
    )
    if row.manual_ticket_text != expected_text:
        raise ValueError("manual_ticket_text must match row fields")


def _validate_report(report: StrategyManualOrderTicketCostBreakdownV2Report) -> None:
    if report.ticket_count != _count(len(report.rows)):
        raise ValueError("ticket_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.blocked_cost_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("blocked_cost_count must match rows")
    if report.total_estimated_notional_usdc != _sum_decimal(tuple(row.estimated_notional_usdc for row in report.rows)):
        raise ValueError("total_estimated_notional_usdc must match rows")
    if report.total_all_in_cost_usdc != _sum_decimal(tuple(row.all_in_cost_usdc for row in report.rows)):
        raise ValueError("total_all_in_cost_usdc must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")


def _reason_codes(
    *,
    estimated_notional_usdc: Decimal,
    all_in_cost_usdc: Decimal,
    max_notional_usdc: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if all_in_cost_usdc > max_notional_usdc:
        codes.append("all_in_cost_above_max")
    elif all_in_cost_usdc >= _money(max_notional_usdc * WATCH_THRESHOLD):
        codes.append("all_in_cost_near_max")
    if estimated_notional_usdc > max_notional_usdc:
        codes.append("estimated_notional_above_max")
    return tuple(codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "all_in_cost_above_max" in reason_codes or "estimated_notional_above_max" in reason_codes:
        return "block"
    if reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[StrategyManualOrderTicketCostBreakdownV2Row, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[StrategyManualOrderTicketCostBreakdownV2Row, ...],
) -> tuple[StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + Decimal("1")
    return tuple(
        StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in sorted(counts)
    )


def _row_sort_key(row: StrategyManualOrderTicketCostBreakdownV2Row) -> tuple[str, str, str]:
    return (row.event_slug, row.market_id, row.candidate_id)


def _require_unique_ids(rows: tuple[StrategyManualOrderTicketCostBreakdownV2Input, ...]) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.candidate_id in seen:
            raise ValueError("candidate_id values must be unique")
        seen.add(row.candidate_id)


def _report_payload(report: StrategyManualOrderTicketCostBreakdownV2Report) -> dict[str, object]:
    payload = _report_payload_without_digest(report)
    payload["report_digest"] = report.report_digest
    return payload


def _report_payload_without_digest(report: StrategyManualOrderTicketCostBreakdownV2Report) -> dict[str, object]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "report_status": report.report_status,
        "ticket_count": _count_payload(report.ticket_count),
        "pass_count": _count_payload(report.pass_count),
        "watch_count": _count_payload(report.watch_count),
        "block_count": _count_payload(report.block_count),
        "total_estimated_notional_usdc": _decimal_payload(report.total_estimated_notional_usdc),
        "total_all_in_cost_usdc": _decimal_payload(report.total_all_in_cost_usdc),
        "blocked_cost_count": _count_payload(report.blocked_cost_count),
        "reason_code_counts": [_reason_code_count_payload(item) for item in report.reason_code_counts],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(item: StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount) -> dict[str, object]:
    return {
        "reason_code": item.reason_code,
        "count": _count_payload(item.count),
    }


def _row_payload(row: StrategyManualOrderTicketCostBreakdownV2Row) -> dict[str, object]:
    payload = _row_payload_without_digest(row)
    payload["row_digest"] = row.row_digest
    return payload


def _row_payload_without_digest(row: StrategyManualOrderTicketCostBreakdownV2Row) -> dict[str, object]:
    return {
        "candidate_id": row.candidate_id,
        "market_id": row.market_id,
        "event_slug": row.event_slug,
        "side": row.side,
        "limit_price": _decimal_payload(row.limit_price),
        "estimated_shares": _decimal_payload(row.estimated_shares),
        "taker_fee_rate": _decimal_payload(row.taker_fee_rate),
        "settlement_cost_rate": _decimal_payload(row.settlement_cost_rate),
        "slippage_buffer_rate": _decimal_payload(row.slippage_buffer_rate),
        "max_notional_usdc": _decimal_payload(row.max_notional_usdc),
        "estimated_notional_usdc": _decimal_payload(row.estimated_notional_usdc),
        "fee_usdc": _decimal_payload(row.fee_usdc),
        "settlement_cost_usdc": _decimal_payload(row.settlement_cost_usdc),
        "slippage_buffer_usdc": _decimal_payload(row.slippage_buffer_usdc),
        "all_in_cost_usdc": _decimal_payload(row.all_in_cost_usdc),
        "max_loss_usdc": _decimal_payload(row.max_loss_usdc),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "manual_ticket_text": row.manual_ticket_text,
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
    if type(payload.get("reason_code_counts")) is not list:
        raise ValueError("reason_code_counts must be a list")
    if type(payload.get("rows")) is not list:
        raise ValueError("rows must be a list")
    report_payload = dict(payload)
    report_digest = report_payload.pop("report_digest", None)
    _require_sha256("report_digest", report_digest)
    if report_digest != _digest(report_payload):
        raise ValueError("report_digest must match payload fields")
    for item in payload["reason_code_counts"]:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain payload objects")
    for row in payload["rows"]:
        if type(row) is not dict:
            raise ValueError("rows must contain payload objects")
        for flag_name in ("paper_only", "report_only", "readonly"):
            if row.get(flag_name) is not True:
                raise ValueError(f"{flag_name} must be True")
        row_payload = dict(row)
        row_digest = row_payload.pop("row_digest", None)
        _require_sha256("row_digest", row_digest)
        if row_digest != _digest(row_payload):
            raise ValueError("row_digest must match payload fields")


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
    "StrategyManualOrderTicketCostBreakdownV2Config",
    "StrategyManualOrderTicketCostBreakdownV2Input",
    "StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount",
    "StrategyManualOrderTicketCostBreakdownV2Report",
    "StrategyManualOrderTicketCostBreakdownV2Row",
    "build_strategy_manual_order_ticket_cost_breakdown_v2",
    "strategy_manual_order_ticket_cost_breakdown_v2_payload",
)

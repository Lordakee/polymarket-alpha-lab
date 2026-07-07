from __future__ import annotations

import ast
import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any

import pytest

import polymarket_alpha_lab.strategy_recommendation_manual_order_ticket_v2 as ticket_module
from polymarket_alpha_lab.strategy_recommendation_manual_order_ticket_v2 import (
    StrategyRecommendationManualOrderTicketV2Config,
    StrategyRecommendationManualOrderTicketV2Input,
    StrategyRecommendationManualOrderTicketV2Report,
    build_strategy_recommendation_manual_order_ticket_v2,
    strategy_recommendation_manual_order_ticket_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
CONFIG = StrategyRecommendationManualOrderTicketV2Config()


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _MissingOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    def dst(self, dt: datetime | None) -> timedelta | None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def recommendation(
    recommendation_id: str = "rec-alpha",
    market_id: str = "market-alpha",
    *,
    side: str = "buy",
    recommendation_rationale: str = "Book imbalance supports upside",
    max_price: Decimal = d("0.420000"),
    size_cap: Decimal = d("25.000000"),
    estimated_fee: Decimal = d("0.050000"),
    estimated_slippage: Decimal = d("0.125000"),
    risk_reasons: tuple[str, ...] = ("oracle timing", "thin book"),
    abstain_conditions: tuple[str, ...] = (
        "best ask above max price",
        "depth below size cap",
    ),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyRecommendationManualOrderTicketV2Input:
    return StrategyRecommendationManualOrderTicketV2Input(
        recommendation_id=recommendation_id,
        market_id=market_id,
        side=side,
        recommendation_rationale=recommendation_rationale,
        max_price=max_price,
        size_cap=size_cap,
        estimated_fee=estimated_fee,
        estimated_slippage=estimated_slippage,
        risk_reasons=risk_reasons,
        abstain_conditions=abstain_conditions,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *recommendations: StrategyRecommendationManualOrderTicketV2Input,
    generated_at: datetime = GENERATED_AT,
    config: StrategyRecommendationManualOrderTicketV2Config = CONFIG,
) -> StrategyRecommendationManualOrderTicketV2Report:
    return build_strategy_recommendation_manual_order_ticket_v2(
        recommendations,
        config=config,
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if is_dataclass(value):
        values: list[object] = []
        for field in fields(value):
            values.extend(walk_values(getattr(value, field.name)))
        return tuple(values)
    if isinstance(value, dict):
        values = []
        for item in value.values():
            values.extend(walk_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return tuple(values)
    return (value,)


def assert_decimal_only(value: object) -> None:
    for item in walk_values(value):
        if type(item) is bool:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, Decimal):
            assert type(item) is Decimal


def expected_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_builds_deterministic_manual_tickets_for_human_review() -> None:
    first = recommendation()
    second = recommendation(
        recommendation_id="rec-gamma",
        market_id="market-gamma",
        side="sell",
        recommendation_rationale="Weak catalyst after liquidity faded",
        max_price=d("0.380000"),
        size_cap=d("10.000000"),
        estimated_fee=d("0.010000"),
        estimated_slippage=d("0.020000"),
        risk_reasons=("headline reversal", "thin book"),
        abstain_conditions=("bid below limit", "news feed stale"),
    )

    result = report(
        second,
        first,
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == "strategy-recommendation-manual-order-ticket-v2"
    assert result.report_status == "ready"
    assert result.ticket_count == d("2")
    assert result.buy_count == d("1")
    assert result.sell_count == d("1")
    assert result.total_size_cap == d("35.000000")
    assert result.total_estimated_notional == d("14.300000")
    assert result.total_estimated_fee == d("0.060000")
    assert result.total_estimated_slippage == d("0.145000")
    assert result.total_estimated_total_cost == d("14.505000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_decimal_only(result)

    assert tuple(ticket.market_id for ticket in result.tickets) == (
        "market-alpha",
        "market-gamma",
    )

    ticket = result.tickets[0]
    assert ticket.recommendation_id == "rec-alpha"
    assert ticket.side == "buy"
    assert ticket.recommendation_rationale == "Book imbalance supports upside"
    assert ticket.max_price == d("0.420000")
    assert ticket.size_cap == d("25.000000")
    assert ticket.estimated_notional == d("10.500000")
    assert ticket.estimated_fee == d("0.050000")
    assert ticket.estimated_slippage == d("0.125000")
    assert ticket.estimated_total_cost == d("10.675000")
    assert ticket.risk_reasons == ("oracle timing", "thin book")
    assert ticket.abstain_conditions == (
        "best ask above max price",
        "depth below size cap",
    )
    assert ticket.manual_ticket_text == (
        "MANUAL REVIEW ONLY | side=buy | market_id=market-alpha | "
        "max_price=0.420000 | size_cap=25.000000 | "
        "estimated_notional=10.500000 | estimated_fee=0.050000 | "
        "estimated_slippage=0.125000 | estimated_total_cost=10.675000 | "
        "rationale=Book imbalance supports upside | "
        "risk_reasons=oracle timing; thin book | "
        "abstain_conditions=best ask above max price; depth below size cap"
    )
    assert len(ticket.ticket_digest) == 64

    repeated = report(first, second)
    assert tuple(item.ticket_digest for item in result.tickets) == tuple(
        item.ticket_digest for item in repeated.tickets
    )
    assert result.report_digest == repeated.report_digest


def test_payload_is_json_ready_decimal_stringed_and_digestable() -> None:
    result = report(recommendation())

    payload = strategy_recommendation_manual_order_ticket_v2_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    values = walk_values(payload)
    ticket_payload = dict(payload["tickets"][0])
    ticket_digest = ticket_payload.pop("ticket_digest")
    report_payload = dict(payload)
    report_digest = report_payload.pop("report_digest")

    assert payload["generated_at"] == "2026-07-07T12:00:00Z"
    assert payload["ticket_count"] == "1"
    assert payload["total_estimated_total_cost"] == "10.675000"
    assert payload["tickets"][0]["estimated_notional"] == "10.500000"
    assert payload["tickets"][0]["ticket_digest"] == expected_digest(ticket_payload)
    assert payload["report_digest"] == expected_digest(report_payload)
    assert ticket_digest == result.tickets[0].ticket_digest
    assert report_digest == result.report_digest
    assert "Book imbalance supports upside" in encoded
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in values)
    assert all(type(value) is not int for value in values if type(value) is not bool)
    assert strategy_recommendation_manual_order_ticket_v2_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        strategy_recommendation_manual_order_ticket_v2_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_manual_order_ticket_v2_payload(
            {**payload, "wallet": {"address": "0x0"}},
        )

    with pytest.raises(ValueError, match="float"):
        strategy_recommendation_manual_order_ticket_v2_payload(
            {**payload, "total_estimated_total_cost": 1.0},
        )


def test_empty_report_is_readonly_report_only_and_decimal_zeroed() -> None:
    result = report()

    assert result.report_status == "empty"
    assert result.ticket_count == d("0")
    assert result.buy_count == d("0")
    assert result.sell_count == d("0")
    assert result.total_size_cap == d("0.000000")
    assert result.total_estimated_notional == d("0.000000")
    assert result.total_estimated_fee == d("0.000000")
    assert result.total_estimated_slippage == d("0.000000")
    assert result.total_estimated_total_cost == d("0.000000")
    assert result.tickets == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_decimal_only(result)


def test_inputs_and_report_reject_invalid_or_unsafe_values() -> None:
    with pytest.raises(ValueError, match="max_price must be a Decimal"):
        recommendation(max_price=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_price must be a Decimal"):
        recommendation(max_price=_DecimalSubclass("0.420000"))
    with pytest.raises(ValueError, match="max_price must be at most 1"):
        recommendation(max_price=d("1.000001"))
    with pytest.raises(ValueError, match="size_cap must be positive"):
        recommendation(size_cap=d("0.000000"))
    with pytest.raises(ValueError, match="side must be buy or sell"):
        recommendation(side="BUY")
    with pytest.raises(ValueError, match="market_id must be canonical"):
        recommendation(market_id=" market-alpha")
    with pytest.raises(ValueError, match="risk_reasons must contain at least one value"):
        recommendation(risk_reasons=())
    with pytest.raises(ValueError, match="abstain_conditions must not contain duplicates"):
        recommendation(abstain_conditions=("depth below size cap", "depth below size cap"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        recommendation(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        StrategyRecommendationManualOrderTicketV2Config(readonly=False)

    sensitive_text = "api_key_exposed"
    with pytest.raises(ValueError, match="unsafe") as error:
        recommendation(risk_reasons=(sensitive_text,))
    assert sensitive_text not in str(error.value)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(recommendation(), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(recommendation(), generated_at=datetime(2026, 7, 7, tzinfo=_MissingOffsetTZ()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(recommendation(), generated_at=_DatetimeSubclass(2026, 7, 7, tzinfo=UTC))
    with pytest.raises(ValueError, match="config"):
        build_strategy_recommendation_manual_order_ticket_v2(
            (),
            config="bad",  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="recommendation_id values must be unique"):
        report(recommendation(), recommendation())


def test_derived_fields_are_tamper_evident_and_dataclasses_are_frozen() -> None:
    result = report(
        recommendation("rec-beta", "market-beta"),
        recommendation("rec-alpha", "market-alpha"),
    )
    ticket = result.tickets[0]

    with pytest.raises(ValueError, match="estimated_notional must match"):
        replace(ticket, estimated_notional=ticket.estimated_notional + d("0.000001"))
    with pytest.raises(ValueError, match="estimated_total_cost must match"):
        replace(ticket, estimated_total_cost=ticket.estimated_total_cost + d("0.000001"))
    with pytest.raises(ValueError, match="manual_ticket_text must match"):
        replace(ticket, manual_ticket_text=f"{ticket.manual_ticket_text} changed")
    with pytest.raises(ValueError, match="ticket_digest must match"):
        replace(ticket, ticket_digest="0" * 64)

    with pytest.raises(ValueError, match="ticket_count must match"):
        replace(result, ticket_count=d("3"))
    with pytest.raises(ValueError, match="total_estimated_total_cost must match"):
        replace(
            result,
            total_estimated_total_cost=result.total_estimated_total_cost + d("0.000001"),
        )
    with pytest.raises(ValueError, match="tickets must be sorted deterministically"):
        replace(result, tickets=(result.tickets[1], result.tickets[0]))
    with pytest.raises(ValueError, match="report_digest must match"):
        replace(result, report_digest="0" * 64)

    with pytest.raises(FrozenInstanceError):
        ticket.side = "sell"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.report_status = "empty"  # type: ignore[misc]


def test_module_stays_phase_one_report_only_without_io_surfaces() -> None:
    source = inspect.getsource(ticket_module)
    lowered_source = source.lower()
    forbidden_markers = (
        "net" + "work",
        "li" + "ve",
        "tra" + "de",
        "au" + "th",
        "wall" + "et",
        "bro" + "ker",
        "place_" + "order",
        "submit_" + "order",
        "send_" + "order",
        "cancel_" + "order",
        "replace_" + "order",
        "sig" + "ning",
        "private" + "_key",
        "api" + "_key",
        "sec" + "ret",
        "tok" + "en",
        "pass" + "word",
    )

    assert all(marker not in lowered_source for marker in forbidden_markers)

    tree = ast.parse(source)
    imports = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imports.isdisjoint(
        {
            "asyncio",
            "httpx",
            "os",
            "pathlib",
            "pickle",
            "psycopg",
            "requests",
            "shutil",
            "socket",
            "sqlite3",
            "subprocess",
            "supabase",
            "urllib",
        },
    )

    forbidden_name_calls = {"eval", "exec", "open", "compile", "__import__", "input", "print"}
    forbidden_attribute_calls = {
        "connect",
        "execute",
        "post",
        "put",
        "request",
        "send",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_name_calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_attribute_calls

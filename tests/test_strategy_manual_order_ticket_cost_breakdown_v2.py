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

import polymarket_alpha_lab.strategy_manual_order_ticket_cost_breakdown_v2 as cost_module
from polymarket_alpha_lab.strategy_manual_order_ticket_cost_breakdown_v2 import (
    StrategyManualOrderTicketCostBreakdownV2Config,
    StrategyManualOrderTicketCostBreakdownV2Input,
    StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount,
    StrategyManualOrderTicketCostBreakdownV2Report,
    build_strategy_manual_order_ticket_cost_breakdown_v2,
    strategy_manual_order_ticket_cost_breakdown_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
CONFIG = StrategyManualOrderTicketCostBreakdownV2Config()


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


def ticket_input(
    candidate_id: str = "cand-alpha",
    market_id: str = "market-alpha",
    event_slug: str = "event-alpha",
    *,
    side: str = "buy",
    limit_price: Decimal = d("0.420000"),
    estimated_shares: Decimal = d("20.000000"),
    taker_fee_rate: Decimal = d("0.020000"),
    settlement_cost_rate: Decimal = d("0.010000"),
    slippage_buffer_rate: Decimal = d("0.030000"),
    max_notional_usdc: Decimal = d("12.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyManualOrderTicketCostBreakdownV2Input:
    return StrategyManualOrderTicketCostBreakdownV2Input(
        candidate_id=candidate_id,
        market_id=market_id,
        event_slug=event_slug,
        side=side,
        limit_price=limit_price,
        estimated_shares=estimated_shares,
        taker_fee_rate=taker_fee_rate,
        settlement_cost_rate=settlement_cost_rate,
        slippage_buffer_rate=slippage_buffer_rate,
        max_notional_usdc=max_notional_usdc,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: StrategyManualOrderTicketCostBreakdownV2Input,
    generated_at: datetime = GENERATED_AT,
    config: StrategyManualOrderTicketCostBreakdownV2Config = CONFIG,
) -> StrategyManualOrderTicketCostBreakdownV2Report:
    return build_strategy_manual_order_ticket_cost_breakdown_v2(
        items,
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


def test_builds_deterministic_phase_one_cost_breakdown_report() -> None:
    passing = ticket_input()
    watch = ticket_input(
        candidate_id="cand-bravo",
        market_id="market-bravo",
        event_slug="event-bravo",
        side="sell",
        limit_price=d("0.500000"),
        estimated_shares=d("18.000000"),
        taker_fee_rate=d("0.020000"),
        settlement_cost_rate=d("0.010000"),
        slippage_buffer_rate=d("0.020000"),
        max_notional_usdc=d("10.000000"),
    )
    blocked = ticket_input(
        candidate_id="cand-charlie",
        market_id="market-charlie",
        event_slug="event-charlie",
        limit_price=d("0.600000"),
        estimated_shares=d("20.000000"),
        taker_fee_rate=d("0.020000"),
        settlement_cost_rate=d("0.010000"),
        slippage_buffer_rate=d("0.030000"),
        max_notional_usdc=d("10.000000"),
    )

    result = report(
        blocked,
        passing,
        watch,
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == "strategy-manual-order-ticket-cost-breakdown-v2"
    assert result.report_status == "block"
    assert result.ticket_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.total_estimated_notional_usdc == d("29.400000")
    assert result.total_all_in_cost_usdc == d("31.074000")
    assert result.blocked_cost_count == d("1")
    assert result.reason_code_counts == (
        StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount(
            reason_code="all_in_cost_above_max",
            count=d("1"),
        ),
        StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount(
            reason_code="all_in_cost_near_max",
            count=d("1"),
        ),
        StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount(
            reason_code="estimated_notional_above_max",
            count=d("1"),
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_decimal_only(result)

    assert tuple(row.candidate_id for row in result.rows) == (
        "cand-alpha",
        "cand-bravo",
        "cand-charlie",
    )

    row = result.rows[0]
    assert row.candidate_id == "cand-alpha"
    assert row.event_slug == "event-alpha"
    assert row.side == "buy"
    assert row.limit_price == d("0.420000")
    assert row.estimated_shares == d("20.000000")
    assert row.estimated_notional_usdc == d("8.400000")
    assert row.fee_usdc == d("0.168000")
    assert row.settlement_cost_usdc == d("0.084000")
    assert row.slippage_buffer_usdc == d("0.252000")
    assert row.all_in_cost_usdc == d("8.904000")
    assert row.max_loss_usdc == d("8.904000")
    assert row.max_notional_usdc == d("12.000000")
    assert row.status == "pass"
    assert row.reason_codes == ()
    assert row.manual_ticket_text == (
        "PHASE 1 MANUAL REVIEW ONLY | readonly=true | report_only=true | paper_only=true | "
        "candidate_id=cand-alpha | event_slug=event-alpha | market_id=market-alpha | "
        "side=buy | limit_price=0.420000 | estimated_shares=20.000000 | "
        "estimated_notional_usdc=8.400000 | fee_usdc=0.168000 | "
        "settlement_cost_usdc=0.084000 | slippage_buffer_usdc=0.252000 | "
        "all_in_cost_usdc=8.904000 | max_loss_usdc=8.904000 | "
        "max_notional_usdc=12.000000 | status=pass | reason_codes=none"
    )
    assert len(row.row_digest) == 64

    assert result.rows[1].status == "watch"
    assert result.rows[1].reason_codes == ("all_in_cost_near_max",)
    assert result.rows[2].status == "block"
    assert result.rows[2].reason_codes == (
        "all_in_cost_above_max",
        "estimated_notional_above_max",
    )

    repeated = report(passing, watch, blocked)
    assert tuple(item.row_digest for item in result.rows) == tuple(
        item.row_digest for item in repeated.rows
    )
    assert result.report_digest == repeated.report_digest


def test_payload_is_json_ready_decimal_stringed_and_digestable() -> None:
    result = report(ticket_input())

    payload = strategy_manual_order_ticket_cost_breakdown_v2_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    values = walk_values(payload)
    row_payload = dict(payload["rows"][0])
    row_digest = row_payload.pop("row_digest")
    report_payload = dict(payload)
    report_digest = report_payload.pop("report_digest")

    assert payload["generated_at"] == "2026-07-07T12:00:00Z"
    assert payload["ticket_count"] == "1"
    assert payload["pass_count"] == "1"
    assert payload["total_all_in_cost_usdc"] == "8.904000"
    assert payload["reason_code_counts"] == []
    assert payload["rows"][0]["estimated_notional_usdc"] == "8.400000"
    assert payload["rows"][0]["row_digest"] == expected_digest(row_payload)
    assert payload["report_digest"] == expected_digest(report_payload)
    assert row_digest == result.rows[0].row_digest
    assert report_digest == result.report_digest
    assert "PHASE 1 MANUAL REVIEW ONLY" in encoded
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in values)
    assert all(type(value) is not int for value in values if type(value) is not bool)
    assert strategy_manual_order_ticket_cost_breakdown_v2_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        strategy_manual_order_ticket_cost_breakdown_v2_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        strategy_manual_order_ticket_cost_breakdown_v2_payload(
            {**payload, "wal" + "let": {"address": "0x0"}},
        )

    with pytest.raises(ValueError, match="float"):
        strategy_manual_order_ticket_cost_breakdown_v2_payload(
            {**payload, "total_all_in_cost_usdc": 1.0},
        )


def test_empty_report_is_readonly_report_only_and_decimal_zeroed() -> None:
    result = report()

    assert result.report_status == "empty"
    assert result.ticket_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.total_estimated_notional_usdc == d("0.000000")
    assert result.total_all_in_cost_usdc == d("0.000000")
    assert result.blocked_cost_count == d("0")
    assert result.reason_code_counts == ()
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_decimal_only(result)


def test_inputs_and_report_reject_invalid_or_unsafe_values() -> None:
    with pytest.raises(ValueError, match="limit_price must be a Decimal"):
        ticket_input(limit_price=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="limit_price must be a Decimal"):
        ticket_input(limit_price=_DecimalSubclass("0.420000"))
    with pytest.raises(ValueError, match="limit_price must be at most 1"):
        ticket_input(limit_price=d("1.000001"))
    with pytest.raises(ValueError, match="estimated_shares must be positive"):
        ticket_input(estimated_shares=d("0.000000"))
    with pytest.raises(ValueError, match="side must be buy or sell"):
        ticket_input(side="BUY")
    with pytest.raises(ValueError, match="candidate_id must be canonical"):
        ticket_input(candidate_id=" cand-alpha")
    with pytest.raises(ValueError, match="taker_fee_rate must be nonnegative"):
        ticket_input(taker_fee_rate=d("-0.000001"))
    with pytest.raises(ValueError, match="slippage_buffer_rate must be at most 1"):
        ticket_input(slippage_buffer_rate=d("1.000001"))
    with pytest.raises(ValueError, match="max_notional_usdc must be positive"):
        ticket_input(max_notional_usdc=d("0.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        ticket_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        StrategyManualOrderTicketCostBreakdownV2Config(readonly=False)

    sensitive_text = "private" + "_key"
    with pytest.raises(ValueError, match="unsafe") as error:
        ticket_input(market_id=sensitive_text)
    assert sensitive_text not in str(error.value)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(ticket_input(), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(ticket_input(), generated_at=datetime(2026, 7, 7, tzinfo=_MissingOffsetTZ()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(ticket_input(), generated_at=_DatetimeSubclass(2026, 7, 7, tzinfo=UTC))
    with pytest.raises(ValueError, match="config"):
        build_strategy_manual_order_ticket_cost_breakdown_v2(
            (),
            config="bad",  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="candidate_id values must be unique"):
        report(ticket_input(), ticket_input())


def test_derived_fields_are_tamper_evident_and_dataclasses_are_frozen() -> None:
    result = report(
        ticket_input("cand-bravo", "market-bravo", "event-bravo"),
        ticket_input("cand-alpha", "market-alpha", "event-alpha"),
    )
    row = result.rows[0]

    with pytest.raises(ValueError, match="estimated_notional_usdc must match"):
        replace(row, estimated_notional_usdc=row.estimated_notional_usdc + d("0.000001"))
    with pytest.raises(ValueError, match="all_in_cost_usdc must match"):
        replace(row, all_in_cost_usdc=row.all_in_cost_usdc + d("0.000001"))
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="manual_ticket_text must match"):
        replace(row, manual_ticket_text=f"{row.manual_ticket_text} changed")
    with pytest.raises(ValueError, match="row_digest must match"):
        replace(row, row_digest="0" * 64)

    with pytest.raises(ValueError, match="ticket_count must match"):
        replace(result, ticket_count=d("3"))
    with pytest.raises(ValueError, match="total_all_in_cost_usdc must match"):
        replace(result, total_all_in_cost_usdc=result.total_all_in_cost_usdc + d("0.000001"))
    with pytest.raises(ValueError, match="reason_code_counts must match"):
        replace(
            result,
            reason_code_counts=(
                StrategyManualOrderTicketCostBreakdownV2ReasonCodeCount(
                    reason_code="all_in_cost_near_max",
                    count=d("1"),
                ),
            ),
        )
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(result, rows=(result.rows[1], result.rows[0]))
    with pytest.raises(ValueError, match="report_digest must match"):
        replace(result, report_digest="0" * 64)

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.report_status = "empty"  # type: ignore[misc]


def test_module_stays_phase_one_report_only_without_io_surfaces() -> None:
    source = inspect.getsource(cost_module)
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
        "exe" + "cution",
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

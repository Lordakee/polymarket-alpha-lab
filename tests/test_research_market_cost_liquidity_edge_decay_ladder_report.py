from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_cost_liquidity_edge_decay_ladder_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_EDGE_DECAY_LADDER_REPORT_CONFIG_VERSION
        ),
        "min_pass_net_edge_ratio": d("0.050000"),
        "min_watch_net_edge_ratio": d("0.020000"),
        "max_pass_cost_ratio": d("0.015000"),
        "max_watch_cost_ratio": d("0.050000"),
        "min_pass_liquidity_score": d("0.700000"),
        "min_watch_liquidity_score": d("0.300000"),
        "max_pass_decay_ratio": d("0.250000"),
        "max_watch_decay_ratio": d("0.600000"),
        "edge_weight": d("0.400000"),
        "cost_weight": d("0.250000"),
        "liquidity_weight": d("0.200000"),
        "decay_weight": d("0.150000"),
        "max_pass_ladder_risk_score": d("0.300000"),
        "max_watch_ladder_risk_score": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchMarketCostLiquidityEdgeDecayLadderConfig(**values)


def ladder_input(
    public_ladder_ref: str = "ladder-ref-pass",
    *,
    observed_at: datetime | None = None,
    gross_edge_ratio: Decimal = d("0.090000"),
    fee_rate: Decimal = d("0.004000"),
    spread_ratio: Decimal = d("0.005000"),
    slippage_ratio: Decimal = d("0.003000"),
    liquidity_score: Decimal = d("0.900000"),
    edge_decay_ratio: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketCostLiquidityEdgeDecayLadderInput(
        public_ladder_ref=public_ladder_ref,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(seconds=45)
        ),
        gross_edge_ratio=gross_edge_ratio,
        fee_rate=fee_rate,
        spread_ratio=spread_ratio,
        slippage_ratio=slippage_ratio,
        liquidity_score=liquidity_score,
        edge_decay_ratio=edge_decay_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_cost_liquidity_edge_decay_ladder_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_scores_cost_liquidity_edge_decay_ladder() -> None:
    module = api()

    combined = report(
        ladder_input(
            "ladder-ref-pass",
            reason_codes=("manual_context_reviewed",),
        ),
        ladder_input(
            "ladder-ref-block",
            gross_edge_ratio=d("0.030000"),
            fee_rate=d("0.020000"),
            spread_ratio=d("0.020000"),
            slippage_ratio=d("0.020000"),
            liquidity_score=d("0.200000"),
            edge_decay_ratio=d("0.750000"),
        ),
        ladder_input(
            "ladder-ref-watch",
            gross_edge_ratio=d("0.070000"),
            fee_rate=d("0.010000"),
            spread_ratio=d("0.010000"),
            slippage_ratio=d("0.010000"),
            liquidity_score=d("0.500000"),
            edge_decay_ratio=d("0.300000"),
        ),
    )

    assert module.MARKET_COST_LIQUIDITY_EDGE_DECAY_LADDER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert type(combined) is module.ResearchMarketCostLiquidityEdgeDecayLadderReport
    assert is_dataclass(combined)
    assert combined.status == "block"
    assert combined.input_count == d("3.000000")
    assert combined.row_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.average_ladder_risk_score == d("0.453968")
    assert combined.max_ladder_risk_score == d("1.000000")
    assert combined.max_total_cost_ratio == d("0.060000")
    assert combined.max_edge_decay_ratio == d("0.750000")
    assert combined.min_net_edge_ratio == d("0.000000")
    assert combined.min_liquidity_score == d("0.200000")
    assert combined.reason_codes == (
        "edge_decay_ladder_block",
        "edge_shortfall_block",
        "cost_drag_block",
        "liquidity_shortfall_block",
        "edge_decay_block",
        "edge_shortfall_watch",
        "cost_drag_watch",
        "liquidity_shortfall_watch",
        "edge_decay_watch",
    )
    assert tuple(row.public_ladder_ref for row in combined.rows) == (
        "ladder-ref-block",
        "ladder-ref-watch",
        "ladder-ref-pass",
    )

    block_row, watch_row, pass_row = combined.rows
    assert block_row.total_cost_ratio == d("0.060000")
    assert block_row.net_edge_ratio == d("0.000000")
    assert block_row.edge_shortfall_score == d("1.000000")
    assert block_row.cost_drag_score == d("1.000000")
    assert block_row.liquidity_shortfall_score == d("1.000000")
    assert block_row.decay_pressure_score == d("1.000000")
    assert block_row.ladder_risk_score == d("1.000000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "cost_drag_block",
        "edge_decay_block",
        "edge_decay_ladder_block",
        "edge_shortfall_block",
        "liquidity_shortfall_block",
    )

    assert watch_row.total_cost_ratio == d("0.030000")
    assert watch_row.net_edge_ratio == d("0.040000")
    assert watch_row.edge_shortfall_score == d("0.333333")
    assert watch_row.cost_drag_score == d("0.428571")
    assert watch_row.liquidity_shortfall_score == d("0.500000")
    assert watch_row.decay_pressure_score == d("0.142857")
    assert watch_row.ladder_risk_score == d("0.361904")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "cost_drag_watch",
        "edge_decay_ladder_watch",
        "edge_decay_watch",
        "edge_shortfall_watch",
        "liquidity_shortfall_watch",
    )

    assert pass_row.net_edge_ratio == d("0.078000")
    assert pass_row.status == "pass"
    assert pass_row.ladder_risk_score == d("0.000000")
    assert pass_row.reason_codes == (
        "edge_decay_ladder_pass",
        "input_manual_context_reviewed",
    )

    payload = module.research_market_cost_liquidity_edge_decay_ladder_report_payload(
        combined,
    )
    payload_json = json.dumps(payload, sort_keys=True).lower()
    assert payload["generated_at"] == "2026-07-09T15:00:00+00:00"
    assert payload["rows"][0]["ladder_risk_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(combined.derived_validation_digest) == 64
    int(combined.derived_validation_digest, 16)
    assert not any(isinstance(value, float) for value in walk_payload_values(payload))
    assert ": 0.5" not in payload_json
    assert "candidate" not in payload_json
    assert "market_id" not in payload_json
    assert "market_slug" not in payload_json
    assert "question" not in payload_json
    assert "source_url" not in payload_json
    assert "source_text" not in payload_json
    assert "wallet" not in payload_json
    assert "order" not in payload_json
    assert "trade" not in payload_json


def test_empty_report_blocks_and_payload_digest_is_stable() -> None:
    module = api()
    empty = report()

    assert empty.status == "block"
    assert empty.input_count == d("0.000000")
    assert empty.average_ladder_risk_score is None
    assert empty.reason_codes == ("no_edge_decay_ladder_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount(
            reason_code="no_edge_decay_ladder_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert empty.rows == ()

    left = report(ladder_input("ladder-ref-b"), ladder_input("ladder-ref-a"))
    right = report(ladder_input("ladder-ref-a"), ladder_input("ladder-ref-b"))
    left_payload = module.research_market_cost_liquidity_edge_decay_ladder_report_payload(
        left,
    )
    right_payload = module.research_market_cost_liquidity_edge_decay_ladder_report_payload(
        right,
    )
    digest = module.research_market_cost_liquidity_edge_decay_ladder_report_digest(left)

    assert left_payload == right_payload
    assert left.derived_validation_digest == right.derived_validation_digest
    assert digest.report_digest == left.derived_validation_digest
    assert digest.report_status == left.status
    assert digest.payload == module.research_market_cost_liquidity_edge_decay_ladder_report_payload(
        digest,
    )

    without_digest = dict(left_payload)
    without_digest.pop("derived_validation_digest")
    canonical = json.dumps(
        without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == (
        left.derived_validation_digest
    )
    tampered_payload = dict(left_payload)
    tampered_payload["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_cost_liquidity_edge_decay_ladder_report_payload(
            tampered_payload,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(left, derived_validation_digest="0" * 64)


def test_validates_decimal_exactness_dates_flags_and_status_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="fee_rate"):
        ladder_input(fee_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_ratio"):
        ladder_input(spread_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        ladder_input(observed_at=datetime(2026, 7, 9, 14, 59))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            ladder_input(),
            generated_at=DatetimeSubclass(2026, 7, 9, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="ladder weights"):
        config(edge_weight=d("0.300000"))
    with pytest.raises(ValueError, match="min_pass_net_edge_ratio"):
        config(min_pass_net_edge_ratio=d("0.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ladder_input(report_only=False)

    good = report(ladder_input())
    with pytest.raises(ValueError, match="readonly"):
        replace(good, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(good.rows[0], status="ready")
    with pytest.raises(FrozenInstanceError):
        good.rows[0].ladder_risk_score = d("0.000000")  # type: ignore[misc]

    assert all(field.default is True for field in fields(config())[-3:])
    assert all(field.default is True for field in fields(good.rows[0])[-3:])
    assert all(field.default is True for field in fields(good)[-3:])
    assert module.research_market_cost_liquidity_edge_decay_ladder_report_digest(
        good,
    ).paper_only is True


def test_rejects_public_identifier_and_payload_leakage_surfaces() -> None:
    module = api()

    for unsafe_value in (
        "candidate-123",
        "market-slug-abc",
        "question-will-this-happen",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            ladder_input(public_ladder_ref=unsafe_value)

    for unsafe_codes in (
        ("source_url",),
        ("wallet_pressure",),
        ("buy_signal",),
        ("table_name",),
    ):
        with pytest.raises(ValueError, match="unsafe"):
            ladder_input(reason_codes=unsafe_codes)

    good = report(ladder_input())
    payload = module.research_market_cost_liquidity_edge_decay_ladder_report_payload(good)
    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "abc"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_cost_liquidity_edge_decay_ladder_report_payload(
            unsafe_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["public_note"] = "source_text leaked"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_cost_liquidity_edge_decay_ladder_report_payload(
            unsafe_payload,
        )


def test_owned_module_has_no_live_execution_or_storage_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_cost_liquidity_edge_decay_ladder_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
    )

    assert all(term not in source for term in forbidden_terms)


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)

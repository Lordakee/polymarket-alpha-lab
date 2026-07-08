from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_cost_liquidity_resolution_index_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_RESOLUTION_INDEX_REPORT_CONFIG_VERSION
        ),
        "max_pass_cost_ratio": d("0.030000"),
        "max_watch_cost_ratio": d("0.080000"),
        "min_pass_depth": d("1000.000000"),
        "min_watch_depth": d("250.000000"),
        "max_pass_book_age_seconds": d("120.000000"),
        "max_watch_book_age_seconds": d("600.000000"),
        "max_pass_resolution_seconds": d("3600.000000"),
        "max_watch_resolution_seconds": d("86400.000000"),
        "max_pass_dispute_pressure": d("0.100000"),
        "max_watch_dispute_pressure": d("0.300000"),
        "cost_weight": d("0.300000"),
        "liquidity_weight": d("0.250000"),
        "book_freshness_weight": d("0.200000"),
        "resolution_weight": d("0.250000"),
        "pass_index_score": d("0.750000"),
        "watch_index_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchMarketCostLiquidityResolutionIndexConfig(**values)


def index_input(
    public_index_ref: str = "triage-index-pass",
    *,
    observed_at: datetime | None = None,
    fee_rate: Decimal = d("0.005000"),
    spread_ratio: Decimal = d("0.005000"),
    available_depth: Decimal = d("2000.000000"),
    book_age_seconds: Decimal = d("60.000000"),
    resolution_delay_seconds: Decimal = d("600.000000"),
    settlement_delay_seconds: Decimal = d("600.000000"),
    resolution_dispute_pressure: Decimal = d("0.020000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketCostLiquidityResolutionIndexInput(
        public_index_ref=public_index_ref,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(seconds=60)
        ),
        fee_rate=fee_rate,
        spread_ratio=spread_ratio,
        available_depth=available_depth,
        book_age_seconds=book_age_seconds,
        resolution_delay_seconds=resolution_delay_seconds,
        settlement_delay_seconds=settlement_delay_seconds,
        resolution_dispute_pressure=resolution_dispute_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_cost_liquidity_resolution_index_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_combines_cost_liquidity_staleness_and_resolution_into_public_index() -> None:
    module = api()

    combined = report(
        index_input(
            "triage-index-pass",
            reason_codes=("manual_triage_context",),
        ),
        index_input(
            "triage-index-block",
            fee_rate=d("0.050000"),
            spread_ratio=d("0.040000"),
            available_depth=d("100.000000"),
            book_age_seconds=d("900.000000"),
            resolution_delay_seconds=d("50000.000000"),
            settlement_delay_seconds=d("40000.000000"),
            resolution_dispute_pressure=d("0.400000"),
        ),
        index_input(
            "triage-index-watch",
            fee_rate=d("0.020000"),
            spread_ratio=d("0.030000"),
        ),
    )

    assert module.MARKET_COST_LIQUIDITY_RESOLUTION_INDEX_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert type(combined) is module.ResearchMarketCostLiquidityResolutionIndexReport
    assert is_dataclass(combined)
    assert combined.status == "block"
    assert combined.input_count == d("3.000000")
    assert combined.row_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.average_index_score == d("0.626667")
    assert combined.min_index_score == d("0.000000")
    assert combined.max_cost_ratio == d("0.090000")
    assert combined.min_available_depth == d("100.000000")
    assert combined.max_book_age_seconds == d("900.000000")
    assert combined.max_resolution_friction_seconds == d("90000.000000")
    assert combined.reason_codes == (
        "market_index_block",
        "cost_pressure_block",
        "liquidity_depth_block",
        "book_staleness_block",
        "resolution_friction_block",
        "cost_pressure_watch",
    )
    assert tuple(row.public_index_ref for row in combined.rows) == (
        "triage-index-block",
        "triage-index-watch",
        "triage-index-pass",
    )

    block_row, watch_row, pass_row = combined.rows
    assert block_row.cost_ratio == d("0.090000")
    assert block_row.liquidity_score == d("0.000000")
    assert block_row.book_freshness_score == d("0.000000")
    assert block_row.resolution_friction_seconds == d("90000.000000")
    assert block_row.resolution_score == d("0.000000")
    assert block_row.index_score == d("0.000000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "book_staleness_block",
        "cost_pressure_block",
        "liquidity_depth_block",
        "market_index_block",
        "resolution_friction_block",
    )

    assert watch_row.cost_ratio == d("0.050000")
    assert watch_row.cost_score == d("0.600000")
    assert watch_row.index_score == d("0.880000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "cost_pressure_watch",
        "market_index_watch",
    )

    assert pass_row.status == "pass"
    assert pass_row.index_score == d("1.000000")
    assert pass_row.reason_codes == (
        "input_manual_triage_context",
        "market_index_pass",
    )

    payload = module.research_market_cost_liquidity_resolution_index_report_payload(
        combined,
    )
    payload_json = json.dumps(payload, sort_keys=True).lower()
    assert payload["generated_at"] == "2026-07-08T16:00:00+00:00"
    assert payload["rows"][0]["index_score"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(combined.derived_validation_digest) == 64
    int(combined.derived_validation_digest, 16)
    assert not any(isinstance(value, float) for value in walk_payload_values(payload))
    assert ": 0.5" not in payload_json
    assert "market_id" not in payload_json
    assert "market_slug" not in payload_json
    assert "question" not in payload_json
    assert "source_url" not in payload_json


def test_empty_report_blocks_and_payload_digest_is_stable() -> None:
    module = api()
    empty = report()

    assert empty.status == "block"
    assert empty.input_count == d("0.000000")
    assert empty.average_index_score is None
    assert empty.reason_codes == ("no_market_index_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketCostLiquidityResolutionIndexReasonCodeCount(
            reason_code="no_market_index_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert empty.rows == ()

    left = report(index_input("triage-index-b"), index_input("triage-index-a"))
    right = report(index_input("triage-index-a"), index_input("triage-index-b"))
    left_payload = module.research_market_cost_liquidity_resolution_index_report_payload(
        left,
    )
    right_payload = module.research_market_cost_liquidity_resolution_index_report_payload(
        right,
    )
    digest = module.research_market_cost_liquidity_resolution_index_report_digest(left)

    assert left_payload == right_payload
    assert left.derived_validation_digest == right.derived_validation_digest
    assert digest.report_digest == left.derived_validation_digest
    assert digest.report_status == left.status
    assert digest.payload == module.research_market_cost_liquidity_resolution_index_report_payload(
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
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(left, derived_validation_digest="0" * 64)


def test_validates_decimal_exactness_dates_flags_and_status_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="fee_rate"):
        index_input(fee_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_ratio"):
        index_input(spread_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        index_input(observed_at=datetime(2026, 7, 8, 15, 59))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            index_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="cost_weight"):
        config(cost_weight=d("0.200000"))
    with pytest.raises(ValueError, match="max_pass_cost_ratio"):
        config(max_pass_cost_ratio=d("0.090000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        index_input(report_only=False)

    good = report(index_input())
    with pytest.raises(ValueError, match="readonly"):
        replace(good, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(good.rows[0], status="ready")
    with pytest.raises(FrozenInstanceError):
        good.rows[0].index_score = d("0.000000")  # type: ignore[misc]

    assert all(field.default is True for field in fields(config())[-3:])
    assert all(field.default is True for field in fields(good.rows[0])[-3:])
    assert all(field.default is True for field in fields(good)[-3:])
    assert module.research_market_cost_liquidity_resolution_index_report_digest(
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
            index_input(public_index_ref=unsafe_value)

    for unsafe_codes in (
        ("source_url",),
        ("wallet_pressure",),
        ("buy_signal",),
        ("table_name",),
    ):
        with pytest.raises(ValueError, match="unsafe"):
            index_input(reason_codes=unsafe_codes)

    good = report(index_input())
    payload = module.research_market_cost_liquidity_resolution_index_report_payload(good)
    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "abc"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_cost_liquidity_resolution_index_report_payload(
            unsafe_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["public_note"] = "source_text leaked"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_cost_liquidity_resolution_index_report_payload(
            unsafe_payload,
        )


def test_owned_module_has_no_live_execution_or_storage_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_cost_liquidity_resolution_index_report.py"
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

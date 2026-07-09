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


GENERATED_AT = datetime(2026, 7, 8, 22, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


class StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_spread_volatility_breakpoint_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_BREAKPOINT_REPORT_CONFIG_VERSION
        ),
        "maximum_pass_spread_width_ratio": d("0.020000"),
        "maximum_watch_spread_width_ratio": d("0.080000"),
        "maximum_pass_volatility_ratio": d("0.050000"),
        "maximum_watch_volatility_ratio": d("0.150000"),
        "minimum_pass_depth_ratio": d("0.750000"),
        "minimum_watch_depth_ratio": d("0.350000"),
        "maximum_pass_book_age_seconds": d("90.000000"),
        "maximum_watch_book_age_seconds": d("600.000000"),
        "maximum_pass_fee_drag_ratio": d("0.010000"),
        "maximum_watch_fee_drag_ratio": d("0.040000"),
        "minimum_pass_slippage_cushion_ratio": d("0.040000"),
        "minimum_watch_slippage_cushion_ratio": d("0.010000"),
        "spread_width_weight": d("0.200000"),
        "volatility_weight": d("0.250000"),
        "depth_weight": d("0.150000"),
        "book_age_weight": d("0.100000"),
        "fee_drag_weight": d("0.150000"),
        "slippage_cushion_weight": d("0.150000"),
        "maximum_pass_noise_score": d("0.250000"),
        "maximum_watch_noise_score": d("0.650000"),
    }
    values.update(overrides)
    return module.ResearchMarketSpreadVolatilityBreakpointConfig(**values)


def breakpoint_input(
    public_breakpoint_ref: str = "mechanics-pass",
    *,
    observed_at: datetime | None = None,
    spread_width_ratio: Decimal = d("0.010000"),
    volatility_ratio: Decimal = d("0.020000"),
    depth_ratio: Decimal = d("0.900000"),
    book_age_seconds: Decimal = d("30.000000"),
    fee_drag_ratio: Decimal = d("0.005000"),
    slippage_cushion_ratio: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketSpreadVolatilityBreakpointInput(
        public_breakpoint_ref=public_breakpoint_ref,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(seconds=30)
        ),
        spread_width_ratio=spread_width_ratio,
        volatility_ratio=volatility_ratio,
        depth_ratio=depth_ratio,
        book_age_seconds=book_age_seconds,
        fee_drag_ratio=fee_drag_ratio,
        slippage_cushion_ratio=slippage_cushion_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_spread_volatility_breakpoint_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_breakpoint_review_with_report_only_flags() -> None:
    module = api()
    empty = report()

    assert module.SPREAD_VOLATILITY_BREAKPOINT_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "SPREAD_VOLATILITY_BREAKPOINT_STATUSES",
        "DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_BREAKPOINT_REPORT_CONFIG_VERSION",
        "ResearchMarketSpreadVolatilityBreakpointConfig",
        "ResearchMarketSpreadVolatilityBreakpointInput",
        "ResearchMarketSpreadVolatilityBreakpointReasonCodeCount",
        "ResearchMarketSpreadVolatilityBreakpointReport",
        "ResearchMarketSpreadVolatilityBreakpointRow",
        "build_research_market_spread_volatility_breakpoint_report",
        "research_market_spread_volatility_breakpoint_report_digest",
        "research_market_spread_volatility_breakpoint_report_payload",
    )
    assert type(empty) is module.ResearchMarketSpreadVolatilityBreakpointReport
    assert is_dataclass(empty)
    assert empty.generated_at == GENERATED_AT
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.block_count == d("0.000000")
    assert empty.breakpoint_count == d("0.000000")
    assert empty.average_noise_score is None
    assert empty.max_noise_score == d("0.000000")
    assert empty.max_spread_width_ratio == d("0.000000")
    assert empty.max_volatility_ratio == d("0.000000")
    assert empty.min_depth_ratio == d("0.000000")
    assert empty.max_book_age_seconds == d("0.000000")
    assert empty.max_fee_drag_ratio == d("0.000000")
    assert empty.min_slippage_cushion_ratio == d("0.000000")
    assert empty.status == "block"
    assert empty.rows == ()
    assert empty.reason_codes == ("no_spread_volatility_breakpoint_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketSpreadVolatilityBreakpointReasonCodeCount(
            reason_code="no_spread_volatility_breakpoint_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_scores_pass_watch_and_block_spread_volatility_breakpoints() -> None:
    module = api()
    mechanics = report(
        breakpoint_input(
            "alpha-block",
            observed_at=GENERATED_AT - timedelta(seconds=900),
            spread_width_ratio=d("0.100000"),
            volatility_ratio=d("0.200000"),
            depth_ratio=d("0.200000"),
            book_age_seconds=d("900.000000"),
            fee_drag_ratio=d("0.060000"),
            slippage_cushion_ratio=d("0.005000"),
            reason_codes=("manual_breakpoint_review",),
        ),
        breakpoint_input("beta-pass"),
        breakpoint_input(
            "gamma-watch",
            observed_at=GENERATED_AT - timedelta(seconds=240),
            spread_width_ratio=d("0.050000"),
            volatility_ratio=d("0.100000"),
            depth_ratio=d("0.600000"),
            book_age_seconds=d("240.000000"),
            fee_drag_ratio=d("0.025000"),
            slippage_cushion_ratio=d("0.020000"),
        ),
    )

    assert mechanics.input_count == d("3.000000")
    assert mechanics.row_count == d("3.000000")
    assert mechanics.pass_count == d("1.000000")
    assert mechanics.watch_count == d("1.000000")
    assert mechanics.block_count == d("1.000000")
    assert mechanics.breakpoint_count == d("2.000000")
    assert mechanics.average_noise_score == d("0.550833")
    assert mechanics.max_noise_score == d("0.970000")
    assert mechanics.max_spread_width_ratio == d("0.100000")
    assert mechanics.max_volatility_ratio == d("0.200000")
    assert mechanics.min_depth_ratio == d("0.200000")
    assert mechanics.max_book_age_seconds == d("900.000000")
    assert mechanics.max_fee_drag_ratio == d("0.060000")
    assert mechanics.min_slippage_cushion_ratio == d("0.005000")
    assert mechanics.status == "block"
    assert mechanics.reason_codes == (
        "spread_volatility_breakpoint_block",
        "spread_width_block",
        "volatility_breakpoint_block",
        "thin_depth_block",
        "book_age_block",
        "fee_drag_block",
        "slippage_cushion_block",
        "spread_width_watch",
        "volatility_breakpoint_watch",
        "thin_depth_watch",
        "book_age_watch",
        "fee_drag_watch",
        "slippage_cushion_watch",
    )

    block_row, watch_row, pass_row = mechanics.rows
    assert tuple(row.public_breakpoint_ref for row in mechanics.rows) == (
        "alpha-block",
        "gamma-watch",
        "beta-pass",
    )
    assert tuple(row.status for row in mechanics.rows) == ("block", "watch", "pass")
    assert block_row.spread_width_pressure_score == d("1.000000")
    assert block_row.volatility_pressure_score == d("1.000000")
    assert block_row.depth_pressure_score == d("0.800000")
    assert block_row.book_age_pressure_score == d("1.000000")
    assert block_row.fee_drag_pressure_score == d("1.000000")
    assert block_row.slippage_cushion_pressure_score == d("1.000000")
    assert block_row.noise_score == d("0.970000")
    assert block_row.reason_codes == (
        "book_age_block",
        "fee_drag_block",
        "input_manual_breakpoint_review",
        "slippage_cushion_block",
        "spread_volatility_breakpoint_block",
        "spread_width_block",
        "thin_depth_block",
        "volatility_breakpoint_block",
    )

    assert watch_row.spread_width_pressure_score == d("0.625000")
    assert watch_row.volatility_pressure_score == d("0.666667")
    assert watch_row.depth_pressure_score == d("0.400000")
    assert watch_row.book_age_pressure_score == d("0.400000")
    assert watch_row.fee_drag_pressure_score == d("0.625000")
    assert watch_row.slippage_cushion_pressure_score == d("0.666667")
    assert watch_row.noise_score == d("0.585417")
    assert watch_row.reason_codes == (
        "book_age_watch",
        "fee_drag_watch",
        "slippage_cushion_watch",
        "spread_volatility_breakpoint_watch",
        "spread_width_watch",
        "thin_depth_watch",
        "volatility_breakpoint_watch",
    )

    assert pass_row.noise_score == d("0.097083")
    assert pass_row.reason_codes == ("spread_volatility_breakpoint_pass",)

    digest = module.research_market_spread_volatility_breakpoint_report_digest(mechanics)
    assert digest.reason_codes == mechanics.reason_codes


def test_payload_digest_is_stable_and_public_without_float_values() -> None:
    module = api()
    left = report(breakpoint_input("breakpoint-b"), breakpoint_input("breakpoint-a"))
    right = report(breakpoint_input("breakpoint-a"), breakpoint_input("breakpoint-b"))

    left_payload = module.research_market_spread_volatility_breakpoint_report_payload(left)
    right_payload = module.research_market_spread_volatility_breakpoint_report_payload(right)
    digest = module.research_market_spread_volatility_breakpoint_report_digest(left)

    assert left_payload == right_payload
    assert left.derived_validation_digest == right.derived_validation_digest
    assert digest.report_digest == left.derived_validation_digest
    assert digest.report_status == left.status
    assert digest.payload == module.research_market_spread_volatility_breakpoint_report_payload(
        digest,
    )
    assert left_payload["generated_at"] == "2026-07-08T22:00:00+00:00"
    assert left_payload["rows"][0]["noise_score"] == "0.097083"
    assert left_payload["paper_only"] is True
    assert left_payload["report_only"] is True
    assert left_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(left_payload))

    payload_json = json.dumps(left_payload, sort_keys=True).lower()
    for unsafe_fragment in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        assert unsafe_fragment not in payload_json

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


def test_validates_exact_decimal_datetime_flags_statuses_and_config() -> None:
    module = api()

    with pytest.raises(ValueError, match="spread_width_ratio"):
        breakpoint_input(spread_width_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="volatility_ratio"):
        breakpoint_input(volatility_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        breakpoint_input(observed_at=datetime(2026, 7, 8, 21, 59))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            breakpoint_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 22, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="spread_width_weight"):
        config(spread_width_weight=d("0.100000"))
    with pytest.raises(ValueError, match="maximum_pass_spread_width_ratio"):
        config(maximum_pass_spread_width_ratio=d("0.090000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        breakpoint_input(report_only=False)

    good = report(breakpoint_input())
    with pytest.raises(ValueError, match="readonly"):
        replace(good, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(good.rows[0], status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(good.rows[0], status=StringSubclass("pass"))
    with pytest.raises(FrozenInstanceError):
        good.rows[0].noise_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):

        class ConfigSubclass(module.ResearchMarketSpreadVolatilityBreakpointConfig):
            pass

    assert all(field.default is True for field in fields(config())[-3:])
    assert all(field.default is True for field in fields(good.rows[0])[-3:])
    assert all(field.default is True for field in fields(good)[-3:])
    assert module.research_market_spread_volatility_breakpoint_report_digest(
        good,
    ).paper_only is True


def test_rejects_public_identifier_reason_code_and_payload_leakage_surfaces() -> None:
    module = api()

    for unsafe_value in (
        "candidate-123",
        "market-slug-abc",
        "question-will-this-happen",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            breakpoint_input(public_breakpoint_ref=unsafe_value)

    for unsafe_codes in (
        ("source_url",),
        ("wallet_pressure",),
        ("buy_signal",),
        ("table_name",),
        ("live_surface",),
    ):
        with pytest.raises(ValueError, match="unsafe"):
            breakpoint_input(reason_codes=unsafe_codes)

    good = report(breakpoint_input())
    payload = module.research_market_spread_volatility_breakpoint_report_payload(good)
    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "abc"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_spread_volatility_breakpoint_report_payload(
            unsafe_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["public_note"] = "source_text leaked"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_spread_volatility_breakpoint_report_payload(
            unsafe_payload,
        )


def test_owned_module_has_no_execution_storage_or_private_surface_terms() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_spread_volatility_breakpoint_report.py"
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

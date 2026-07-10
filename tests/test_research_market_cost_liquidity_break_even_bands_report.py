from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_market_cost_liquidity_break_even_bands_report as api
from polymarket_alpha_lab.research_market_cost_liquidity_break_even_bands_report import (
    DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_BREAK_EVEN_BANDS_REPORT_CONFIG_VERSION,
    ResearchMarketCostLiquidityBreakEvenBandsConfig,
    ResearchMarketCostLiquidityBreakEvenBandsInput,
    ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount,
    ResearchMarketCostLiquidityBreakEvenBandsReport,
    ResearchMarketCostLiquidityBreakEvenBandsRow,
    build_research_market_cost_liquidity_break_even_bands_report,
    research_market_cost_liquidity_break_even_bands_report_payload,
    validate_research_market_cost_liquidity_break_even_bands_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_cost_liquidity_break_even_bands_report.py",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchMarketCostLiquidityBreakEvenBandsConfig:
    values: dict[str, object] = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_BREAK_EVEN_BANDS_REPORT_CONFIG_VERSION
        ),
        "pass_break_even_margin_bps": d("10.000000"),
        "watch_break_even_margin_bps": d("0.000000"),
        "pass_depth": d("1000.000000"),
        "watch_depth": d("250.000000"),
        "low_cost_max_bps": d("20.000000"),
        "medium_cost_max_bps": d("50.000000"),
    }
    values.update(overrides)
    return ResearchMarketCostLiquidityBreakEvenBandsConfig(**values)


def row_input(
    research_reference: str,
    *,
    spread_bps: Decimal = d("10.000000"),
    taker_fee_bps: Decimal = d("2.000000"),
    slippage_bps: Decimal = d("3.000000"),
    depth: Decimal = d("1500.000000"),
    probability_edge: Decimal = d("0.003000"),
) -> ResearchMarketCostLiquidityBreakEvenBandsInput:
    return ResearchMarketCostLiquidityBreakEvenBandsInput(
        research_reference=research_reference,
        spread_bps=spread_bps,
        taker_fee_bps=taker_fee_bps,
        slippage_bps=slippage_bps,
        depth=depth,
        probability_edge=probability_edge,
    )


def report(
    *inputs: ResearchMarketCostLiquidityBreakEvenBandsInput,
    cfg: ResearchMarketCostLiquidityBreakEvenBandsConfig | None = None,
) -> ResearchMarketCostLiquidityBreakEvenBandsReport:
    return build_research_market_cost_liquidity_break_even_bands_report(
        inputs,
        config=config() if cfg is None else cfg,
        generated_at=GENERATED_AT,
    )


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    signed = json.loads(json.dumps(payload))
    unsigned = dict(signed)
    unsigned.pop("derived_validation_digest", None)
    signed["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            unsigned,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return signed


def test_reducer_computes_deterministic_cost_liquidity_break_even_bands() -> None:
    result = report(
        row_input("pass-row"),
        row_input(
            "watch-row",
            spread_bps=d("40.000000"),
            taker_fee_bps=d("5.000000"),
            slippage_bps=d("5.000000"),
            depth=d("500.000000"),
            probability_edge=d("0.003500"),
        ),
        row_input(
            "block-row",
            spread_bps=d("80.000000"),
            taker_fee_bps=d("15.000000"),
            slippage_bps=d("5.000000"),
            depth=d("100.000000"),
            probability_edge=d("0.005000"),
        ),
    )

    assert tuple(item.status for item in result.rows) == ("block", "watch", "pass")
    blocked, watched, passed = result.rows

    assert blocked.spread_cost_bps == d("40.000000")
    assert blocked.total_cost_bps == d("60.000000")
    assert blocked.break_even_probability_edge == d("0.006000")
    assert blocked.break_even_margin_bps == d("-10.000000")
    assert blocked.cost_band == "high"
    assert blocked.liquidity_band == "thin"
    assert blocked.reason_codes == (
        "cost_band_high",
        "liquidity_band_thin",
        "probability_edge_below_break_even",
        "break_even_bands_block",
    )

    assert watched.total_cost_bps == d("30.000000")
    assert watched.break_even_probability_edge == d("0.003000")
    assert watched.break_even_margin_bps == d("5.000000")
    assert watched.cost_band == "medium"
    assert watched.liquidity_band == "moderate"
    assert watched.reason_codes == (
        "cost_band_medium",
        "liquidity_band_moderate",
        "probability_edge_near_break_even",
        "break_even_bands_watch",
    )

    assert passed.total_cost_bps == d("10.000000")
    assert passed.break_even_probability_edge == d("0.001000")
    assert passed.break_even_margin_bps == d("20.000000")
    assert passed.cost_band == "low"
    assert passed.liquidity_band == "deep"
    assert passed.reason_codes == (
        "cost_band_low",
        "liquidity_band_deep",
        "probability_edge_above_break_even",
        "break_even_bands_pass",
    )

    assert result.status == "block"
    assert result.input_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.average_total_cost_bps == d("33.333333")
    assert result.max_total_cost_bps == d("60.000000")
    assert result.min_break_even_margin_bps == d("-10.000000")
    assert result.reason_code_counts == (
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="break_even_bands_block",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="break_even_bands_pass",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="break_even_bands_watch",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="cost_band_high",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="cost_band_low",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="cost_band_medium",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="liquidity_band_deep",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="liquidity_band_moderate",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="liquidity_band_thin",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="probability_edge_above_break_even",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="probability_edge_below_break_even",
            count=d("1.000000"),
        ),
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="probability_edge_near_break_even",
            count=d("1.000000"),
        ),
    )


def test_empty_report_is_blocked_and_readonly() -> None:
    result = report()

    assert result.status == "block"
    assert result.input_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.average_total_cost_bps == d("0.000000")
    assert result.max_total_cost_bps == d("0.000000")
    assert result.min_break_even_margin_bps == d("0.000000")
    assert result.reason_codes == (
        "research_market_cost_liquidity_break_even_bands_no_inputs",
    )
    assert result.reason_code_counts == (
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount(
            reason_code="research_market_cost_liquidity_break_even_bands_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_models_are_frozen_decimal_only_and_validate_thresholds() -> None:
    result = report(row_input("frozen-row"))

    for value in (
        config(),
        row_input("input-row"),
        result.rows[0],
        result.reason_code_counts[0],
        result,
    ):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            public_value = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            assert type(public_value) is not int
            assert type(public_value) is not float

    with pytest.raises(ValueError, match="spread_bps"):
        row_input("integer-spread", spread_bps=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="probability_edge"):
        row_input("bad-edge", probability_edge=d("1.000001"))
    with pytest.raises(ValueError, match="depth"):
        row_input("negative-depth", depth=d("-0.000001"))
    with pytest.raises(ValueError, match="pass_break_even_margin_bps"):
        config(
            pass_break_even_margin_bps=d("-0.000001"),
        )
    with pytest.raises(ValueError, match="pass_depth"):
        config(pass_depth=d("100.000000"), watch_depth=d("250.000000"))
    with pytest.raises(ValueError, match="medium_cost_max_bps"):
        config(
            low_cost_max_bps=d("50.000000"),
            medium_cost_max_bps=d("20.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchMarketCostLiquidityBreakEvenBandsConfig(paper_only=False)


def test_payload_is_canonical_deterministic_and_digest_validated() -> None:
    first = report(row_input("canonical-row"))
    second = report(row_input("canonical-row"))

    assert first.payload == second.payload
    payload = research_market_cost_liquidity_break_even_bands_report_payload(first)
    assert payload == validate_research_market_cost_liquidity_break_even_bands_report_payload(
        payload,
    )
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["spread_bps"] == "10.000000"
    assert payload["rows"][0]["break_even_probability_edge"] == "0.001000"
    assert payload["rows"][0]["break_even_margin_bps"] == "20.000000"
    assert len(payload["derived_validation_digest"]) == 64
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    _assert_no_non_string_numbers(payload)

    unsigned = dict(payload)
    digest = unsigned.pop("derived_validation_digest")
    assert digest == hashlib.sha256(
        json.dumps(
            unsigned,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()

    tampered = dict(payload)
    tampered["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_market_cost_liquidity_break_even_bands_report_payload(
            tampered,
        )


def test_public_validator_rejects_forged_resigned_status_and_reason_logic() -> None:
    payload = report(row_input("forged-row")).payload
    forged = json.loads(json.dumps(payload))
    forged["status"] = "block"
    forged["pass_count"] = "0.000000"
    forged["block_count"] = "1.000000"
    forged["reason_codes"] = [
        "research_market_cost_liquidity_break_even_bands_block",
        "cost_band_low",
        "liquidity_band_deep",
        "probability_edge_above_break_even",
        "break_even_bands_block",
    ]
    row = forged["rows"][0]
    row["status"] = "block"
    row["reason_codes"] = [
        "cost_band_low",
        "liquidity_band_deep",
        "probability_edge_above_break_even",
        "break_even_bands_block",
    ]
    for item in forged["reason_code_counts"]:
        if item["reason_code"] == "break_even_bands_pass":
            item["reason_code"] = "break_even_bands_block"
    forged = resign_payload(forged)

    with pytest.raises(ValueError, match="status|reason_codes"):
        validate_research_market_cost_liquidity_break_even_bands_report_payload(
            forged,
        )


def test_module_surface_stays_phase_one_report_only_and_public_safe() -> None:
    forbidden_public_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "execute",
        "recommendation",
        "sizing",
        "auth",
        "network",
        "persist",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_terms)

    for cls in (
        ResearchMarketCostLiquidityBreakEvenBandsConfig,
        ResearchMarketCostLiquidityBreakEvenBandsRow,
        ResearchMarketCostLiquidityBreakEvenBandsReasonCodeCount,
        ResearchMarketCostLiquidityBreakEvenBandsReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_public_terms)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    }
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert set(api.STATUSES) == {"pass", "watch", "block"}
    assert set(api.COST_BANDS) == {"low", "medium", "high"}
    assert set(api.LIQUIDITY_BANDS) == {"deep", "moderate", "thin"}


def _assert_no_non_string_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"payload contains non-string number: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_non_string_numbers(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_non_string_numbers(item)

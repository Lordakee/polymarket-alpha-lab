from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_liquidity_quality_regime_report import (
    DEFAULT_RESEARCH_MARKET_LIQUIDITY_QUALITY_REGIME_REPORT_CONFIG_VERSION,
    LIQUIDITY_QUALITY_REGIME_STATUSES,
    ResearchMarketLiquidityQualityRegimeConfig,
    ResearchMarketLiquidityQualityRegimeInput,
    ResearchMarketLiquidityQualityRegimeReasonCodeCount,
    ResearchMarketLiquidityQualityRegimeReport,
    ResearchMarketLiquidityQualityRegimeRow,
    build_research_market_liquidity_quality_regime_report,
    research_market_liquidity_quality_regime_report_digest,
    research_market_liquidity_quality_regime_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 15, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketLiquidityQualityRegimeConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_LIQUIDITY_QUALITY_REGIME_REPORT_CONFIG_VERSION
        ),
        "max_pass_spread_rate": d("0.015000"),
        "max_watch_spread_rate": d("0.040000"),
        "min_pass_depth_score": d("0.750000"),
        "min_watch_depth_score": d("0.500000"),
        "max_pass_depth_decay_rate": d("0.150000"),
        "max_watch_depth_decay_rate": d("0.350000"),
        "max_pass_volatility_rate": d("0.100000"),
        "max_watch_volatility_rate": d("0.250000"),
        "max_pass_book_age_seconds": d("1800.000000"),
        "max_watch_book_age_seconds": d("21600.000000"),
        "max_pass_fee_drag_rate": d("0.010000"),
        "max_watch_fee_drag_rate": d("0.030000"),
        "max_pass_settlement_friction_rate": d("0.005000"),
        "max_watch_settlement_friction_rate": d("0.020000"),
    }
    values.update(overrides)
    return ResearchMarketLiquidityQualityRegimeConfig(**values)


def input_row(
    research_key: str = "liquidity-quality-case-pass",
    *,
    spread_rate: Decimal = d("0.010000"),
    depth_score: Decimal = d("0.900000"),
    depth_decay_rate: Decimal = d("0.050000"),
    volatility_rate: Decimal = d("0.060000"),
    book_age_seconds: Decimal = d("900.000000"),
    fee_drag_rate: Decimal = d("0.004000"),
    settlement_friction_rate: Decimal = d("0.002000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketLiquidityQualityRegimeInput:
    return ResearchMarketLiquidityQualityRegimeInput(
        research_key=research_key,
        spread_rate=spread_rate,
        depth_score=depth_score,
        depth_decay_rate=depth_decay_rate,
        volatility_rate=volatility_rate,
        book_age_seconds=book_age_seconds,
        fee_drag_rate=fee_drag_rate,
        settlement_friction_rate=settlement_friction_rate,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchMarketLiquidityQualityRegimeInput,
    cfg: ResearchMarketLiquidityQualityRegimeConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketLiquidityQualityRegimeReport:
    return build_research_market_liquidity_quality_regime_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_inputs_block_manual_liquidity_regime_review() -> None:
    quality = report()

    assert type(quality) is ResearchMarketLiquidityQualityRegimeReport
    assert is_dataclass(quality)
    assert LIQUIDITY_QUALITY_REGIME_STATUSES == ("pass", "watch", "block")
    assert quality.generated_at == GENERATED_AT
    assert quality.config_version == "research-market-liquidity-quality-regime-report-v0"
    assert quality.input_count == ZERO
    assert quality.pass_count == ZERO
    assert quality.watch_count == ZERO
    assert quality.block_count == ZERO
    assert quality.average_liquidity_quality_score is None
    assert quality.max_spread_rate == ZERO
    assert quality.min_depth_score == ZERO
    assert quality.max_depth_decay_rate == ZERO
    assert quality.max_volatility_rate == ZERO
    assert quality.max_book_age_risk == ZERO
    assert quality.max_fee_drag_rate == ZERO
    assert quality.max_settlement_friction_rate == ZERO
    assert quality.status == "block"
    assert quality.reason_codes == ("no_liquidity_quality_inputs",)
    assert quality.reason_code_counts == (
        ResearchMarketLiquidityQualityRegimeReasonCodeCount(
            reason_code="no_liquidity_quality_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert quality.rows == ()
    assert quality.paper_only is True
    assert quality.report_only is True
    assert quality.readonly is True


def test_liquidity_quality_regimes_pass_watch_and_block_inputs() -> None:
    quality = report(
        input_row(
            "liquidity-quality-case-watch",
            spread_rate=d("0.030000"),
            depth_score=d("0.650000"),
            depth_decay_rate=d("0.250000"),
            volatility_rate=d("0.180000"),
            book_age_seconds=d("7200.000000"),
            fee_drag_rate=d("0.020000"),
            settlement_friction_rate=d("0.012000"),
        ),
        input_row(
            "liquidity-quality-case-block",
            spread_rate=d("0.060000"),
            depth_score=d("0.400000"),
            depth_decay_rate=d("0.500000"),
            volatility_rate=d("0.300000"),
            book_age_seconds=d("30000.000000"),
            fee_drag_rate=d("0.050000"),
            settlement_friction_rate=d("0.030000"),
            reason_codes=("manual_liquidity_escalation",),
        ),
        input_row(
            "liquidity-quality-case-pass",
            reason_codes=("manual_research_complete",),
        ),
    )

    assert quality.input_count == d("3.000000")
    assert quality.pass_count == d("1.000000")
    assert quality.watch_count == d("1.000000")
    assert quality.block_count == d("1.000000")
    assert quality.average_liquidity_quality_score == d("0.810333")
    assert quality.max_spread_rate == d("0.060000")
    assert quality.min_depth_score == d("0.400000")
    assert quality.max_depth_decay_rate == d("0.500000")
    assert quality.max_volatility_rate == d("0.300000")
    assert quality.max_book_age_risk == d("1.000000")
    assert quality.max_fee_drag_rate == d("0.050000")
    assert quality.max_settlement_friction_rate == d("0.030000")
    assert quality.status == "block"
    assert quality.reason_codes == (
        "market_liquidity_quality_regime_block",
        "spread_block",
        "depth_block",
        "depth_decay_block",
        "volatility_block",
        "book_age_block",
        "fee_drag_block",
        "settlement_friction_block",
        "spread_watch",
        "depth_watch",
        "depth_decay_watch",
        "volatility_watch",
        "book_age_watch",
        "fee_drag_watch",
        "settlement_friction_watch",
    )

    block_row, pass_row, watch_row = quality.rows
    assert type(block_row) is ResearchMarketLiquidityQualityRegimeRow
    assert tuple(row.research_key for row in quality.rows) == (
        "liquidity-quality-case-block",
        "liquidity-quality-case-pass",
        "liquidity-quality-case-watch",
    )
    assert block_row.liquidity_quality_score == d("0.637143")
    assert block_row.book_age_risk == d("1.000000")
    assert block_row.liquidity_quality_regime == "fragile_liquidity"
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "book_age_block",
        "depth_block",
        "depth_decay_block",
        "fee_drag_block",
        "input_manual_liquidity_escalation",
        "manual_research_liquidity_quality_block",
        "market_liquidity_quality_regime_block",
        "settlement_friction_block",
        "spread_block",
        "volatility_block",
    )
    assert pass_row.liquidity_quality_score == d("0.961762")
    assert pass_row.book_age_risk == d("0.041667")
    assert pass_row.liquidity_quality_regime == "high_quality_liquidity"
    assert pass_row.status == "pass"
    assert "market_liquidity_quality_regime_pass" in pass_row.reason_codes
    assert "input_manual_research_complete" in pass_row.reason_codes
    assert watch_row.liquidity_quality_score == d("0.832095")
    assert watch_row.book_age_risk == d("0.333333")
    assert watch_row.liquidity_quality_regime == "degraded_liquidity"
    assert watch_row.status == "watch"
    assert "spread_watch" in watch_row.reason_codes
    assert "depth_watch" in watch_row.reason_codes
    assert "depth_decay_watch" in watch_row.reason_codes
    assert "volatility_watch" in watch_row.reason_codes
    assert "book_age_watch" in watch_row.reason_codes
    assert "fee_drag_watch" in watch_row.reason_codes
    assert "settlement_friction_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    first = report(
        input_row("liquidity-quality-case-z", reason_codes=("zeta", "alpha")),
        input_row("liquidity-quality-case-a"),
    )
    second = report(
        input_row("liquidity-quality-case-a"),
        input_row("liquidity-quality-case-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = research_market_liquidity_quality_regime_report_payload(first)
    second_payload = research_market_liquidity_quality_regime_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True, separators=(",", ":"))
    expected_digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    assert first_payload == second_payload
    assert research_market_liquidity_quality_regime_report_digest(first) == (
        research_market_liquidity_quality_regime_report_digest(second)
    )
    assert research_market_liquidity_quality_regime_report_digest(first) == expected_digest
    assert len(research_market_liquidity_quality_regime_report_digest(first)) == 64
    assert first_payload["rows"][0]["liquidity_quality_score"] == "0.961762"
    assert first_payload["rows"][0]["spread_rate"] == "0.010000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ":0." not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )
    assert not any(
        _has_forbidden_public_surface_value(str(value))
        for value in _walk_payload_values(first_payload)
        if isinstance(value, str)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_rows() -> None:
    populated = report(input_row())

    for value in (
        config(),
        input_row(),
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_rate",
                    "_seconds",
                    "_risk",
                    "_ratio",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].liquidity_quality_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_pass_spread_rate"):
        config(max_pass_spread_rate=0.015)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_watch_spread_rate"):
        config(max_watch_spread_rate=_DecimalSubclass("0.040000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 15, 45))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            input_row(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 15, 45, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_key"):
        input_row(" liquidity-quality-case-pass")
    with pytest.raises(ValueError, match="research_key"):
        input_row("candidate-123")
    with pytest.raises(ValueError, match="spread_rate"):
        input_row(spread_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_score"):
        input_row(depth_score=d("1.100000"))
    with pytest.raises(ValueError, match="book_age_seconds"):
        input_row(book_age_seconds=-d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError):
        input_row(reason_codes=("source_url",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="liquidity_quality_score"):
        replace(populated.rows[0], liquidity_quality_score=d("0.100000"))
    with pytest.raises(ValueError, match="liquidity_quality_regime"):
        replace(populated.rows[0], liquidity_quality_regime="fragile_liquidity")
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="report"):
        research_market_liquidity_quality_regime_report_payload(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="report_only"):
        research_market_liquidity_quality_regime_report_payload(
            replace(populated, report_only=False),
        )


def test_owned_module_has_no_side_effect_or_decision_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_liquidity_quality_regime_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "database",
        "network",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )

    assert all(term not in text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_public_surface_key(key: str) -> bool:
    return key in {
        "candidate_id",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "source_text",
        "source_url",
        "source_reference",
        "raw_text",
        "dsn",
        "table_name",
    }


def _has_forbidden_public_surface_value(value: str) -> bool:
    normalized = value.lower()
    fragments = (
        "candidate-",
        "market_id",
        "market_slug",
        "question:",
        "http://",
        "https://",
        "source_text",
        "raw_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    return any(fragment in normalized for fragment in fragments)

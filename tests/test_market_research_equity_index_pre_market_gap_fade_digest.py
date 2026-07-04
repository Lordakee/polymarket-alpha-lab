from __future__ import annotations

import ast
import dataclasses
from dataclasses import FrozenInstanceError, asdict, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_equity_index_pre_market_gap_fade_digest import (
    DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_PRE_MARKET_GAP_FADE_DIGEST_CONFIG_VERSION,
    MarketResearchEquityIndexPreMarketGapFadeDigestConfig,
    MarketResearchEquityIndexPreMarketGapFadeInputRow,
    MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount,
    MarketResearchEquityIndexPreMarketGapFadeReport,
    MarketResearchEquityIndexPreMarketGapFadeRow,
    build_market_research_equity_index_pre_market_gap_fade_digest,
    market_research_equity_index_pre_market_gap_fade_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 13, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchEquityIndexPreMarketGapFadeDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_PRE_MARKET_GAP_FADE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2"),
        "min_confirmation_count": d("1"),
        "min_abs_pre_market_gap_pct": d("0.006000"),
        "min_fade_pressure_score": d("0.650000"),
        "min_overnight_range_pct": d("0.010000"),
        "min_abs_prior_day_trend_pct": d("0.012000"),
        "max_opening_liquidity_ratio": d("0.350000"),
        "max_acknowledgement_lag_seconds": d("900.000000"),
    }
    values.update(overrides)
    return MarketResearchEquityIndexPreMarketGapFadeDigestConfig(**values)


def input_row(
    research_key: str = "research.spx.gap_fade",
    *,
    condition_id: str = "condition_spx_daily_close_range",
    index_symbol: str = "SPX",
    gap_event_key: str = "spx.20260704.preopen_gap",
    signal_reference: str = "public-premarket-snapshot",
    signaled_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3"),
    confirmation_count: Decimal = d("1"),
    pre_market_gap_pct: Decimal = d("0.008000"),
    overnight_range_pct: Decimal = d("0.012000"),
    prior_day_trend_pct: Decimal = d("-0.014000"),
    fade_pressure_score: Decimal = d("0.700000"),
    opening_liquidity_ratio: Decimal = d("0.300000"),
    contradiction_count: Decimal = ZERO,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEquityIndexPreMarketGapFadeInputRow:
    return MarketResearchEquityIndexPreMarketGapFadeInputRow(
        research_key=research_key,
        condition_id=condition_id,
        index_symbol=index_symbol,
        gap_event_key=gap_event_key,
        signal_reference=signal_reference,
        signaled_at=signaled_at or GENERATED_AT - timedelta(minutes=20),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=10)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        confirmation_count=confirmation_count,
        pre_market_gap_pct=pre_market_gap_pct,
        overnight_range_pct=overnight_range_pct,
        prior_day_trend_pct=prior_day_trend_pct,
        fade_pressure_score=fade_pressure_score,
        opening_liquidity_ratio=opening_liquidity_ratio,
        contradiction_count=contradiction_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[MarketResearchEquityIndexPreMarketGapFadeInputRow, ...],
    *,
    cfg: MarketResearchEquityIndexPreMarketGapFadeDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEquityIndexPreMarketGapFadeReport:
    return build_market_research_equity_index_pre_market_gap_fade_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_high_risk_gap_fade_digest_redacts_refs_and_sorts_deterministically() -> None:
    summary = report(
        (
            input_row(
                "research.ndx.gap_fade",
                condition_id="condition_ndx_daily_close_range",
                index_symbol="NDX",
                gap_event_key="ndx.20260704.preopen_gap",
                signal_reference="https://vendor.example/gapfade?token=raw",
                signaled_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=None,
                source_count=d("1"),
                confirmation_count=ZERO,
                pre_market_gap_pct=d("-0.018000"),
                overnight_range_pct=d("0.026000"),
                prior_day_trend_pct=d("0.020000"),
                fade_pressure_score=d("0.850000"),
                opening_liquidity_ratio=d("0.150000"),
                contradiction_count=d("1"),
            ),
            input_row(
                "research.spx.gap_fade",
                condition_id="condition_spx_daily_close_range",
                index_symbol="SPX",
                gap_event_key="spx.20260704.preopen_gap",
                signaled_at=GENERATED_AT - timedelta(minutes=30),
                acknowledged_at=GENERATED_AT - timedelta(minutes=10),
                source_count=d("3"),
                confirmation_count=d("1"),
                pre_market_gap_pct=d("0.012000"),
                overnight_range_pct=d("0.015000"),
                prior_day_trend_pct=d("-0.018000"),
                fade_pressure_score=d("0.720000"),
                opening_liquidity_ratio=d("0.250000"),
            ),
            input_row(
                "research.rty.gap_fade",
                condition_id="condition_rty_daily_close_range",
                index_symbol="RTY",
                gap_event_key="rty.20260704.preopen_gap",
                signaled_at=GENERATED_AT - timedelta(minutes=15),
                acknowledged_at=GENERATED_AT - timedelta(minutes=14),
                pre_market_gap_pct=d("0.002000"),
                overnight_range_pct=d("0.004000"),
                prior_day_trend_pct=d("0.002000"),
                fade_pressure_score=d("0.200000"),
                opening_liquidity_ratio=d("0.800000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_PRE_MARKET_GAP_FADE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_equity_index_pre_market_gap_fade_digest"
    )
    assert summary.gap_event_count == d("3.000000")
    assert summary.ready_event_count == d("1.000000")
    assert summary.watch_event_count == d("1.000000")
    assert summary.blocked_event_count == d("1.000000")
    assert summary.material_gap_count == d("2.000000")
    assert summary.fade_pressure_count == d("2.000000")
    assert summary.extended_overnight_range_count == d("2.000000")
    assert summary.counter_trend_gap_count == d("2.000000")
    assert summary.low_opening_liquidity_count == d("2.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_confirmation_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.contradiction_count == d("1.000000")
    assert summary.average_gap_abs_pct == d("0.010667")
    assert summary.max_gap_abs_pct == d("0.018000")
    assert summary.average_fade_pressure_score == d("0.590000")
    assert summary.average_opening_liquidity_ratio == d("0.400000")
    assert summary.max_signal_age_seconds == d("10800.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.index_symbol, row.gap_event_key) for row in summary.rows) == (
        ("NDX", "ndx.20260704.preopen_gap"),
        ("SPX", "spx.20260704.preopen_gap"),
        ("RTY", "rty.20260704.preopen_gap"),
    )

    ndx = summary.rows[0]
    assert ndx.gap_status == "blocked"
    assert ndx.gap_direction == "gap_down"
    assert ndx.signal_age_seconds == d("10800.000000")
    assert ndx.acknowledgement_lag_seconds is None
    assert ndx.gap_abs_pct == d("0.018000")
    assert ndx.redacted_signal_reference.startswith("sha256:")
    assert ndx.reason_codes == (
        "market_research_equity_index_pre_market_gap_fade_digest_material_gap",
        "market_research_equity_index_pre_market_gap_fade_digest_fade_pressure",
        "market_research_equity_index_pre_market_gap_fade_digest_extended_overnight_range",
        "market_research_equity_index_pre_market_gap_fade_digest_counter_trend_gap",
        "market_research_equity_index_pre_market_gap_fade_digest_low_opening_liquidity",
        "market_research_equity_index_pre_market_gap_fade_digest_stale_signal",
        "market_research_equity_index_pre_market_gap_fade_digest_thin_sources",
        "market_research_equity_index_pre_market_gap_fade_digest_missing_confirmation",
        "market_research_equity_index_pre_market_gap_fade_digest_contradiction_present",
    )

    spx = summary.rows[1]
    assert spx.gap_status == "watch"
    assert spx.gap_direction == "gap_up"
    assert spx.signal_age_seconds == d("1800.000000")
    assert spx.acknowledgement_lag_seconds == d("1200.000000")
    assert spx.reason_codes == (
        "market_research_equity_index_pre_market_gap_fade_digest_material_gap",
        "market_research_equity_index_pre_market_gap_fade_digest_fade_pressure",
        "market_research_equity_index_pre_market_gap_fade_digest_extended_overnight_range",
        "market_research_equity_index_pre_market_gap_fade_digest_counter_trend_gap",
        "market_research_equity_index_pre_market_gap_fade_digest_low_opening_liquidity",
        "market_research_equity_index_pre_market_gap_fade_digest_slow_acknowledgement",
    )

    rty = summary.rows[2]
    assert rty.gap_status == "ready"
    assert rty.reason_codes == (
        "market_research_equity_index_pre_market_gap_fade_digest_ready",
    )

    assert summary.reason_codes == (
        "market_research_equity_index_pre_market_gap_fade_digest_material_gap",
        "market_research_equity_index_pre_market_gap_fade_digest_fade_pressure",
        "market_research_equity_index_pre_market_gap_fade_digest_extended_overnight_range",
        "market_research_equity_index_pre_market_gap_fade_digest_counter_trend_gap",
        "market_research_equity_index_pre_market_gap_fade_digest_low_opening_liquidity",
        "market_research_equity_index_pre_market_gap_fade_digest_stale_signal",
        "market_research_equity_index_pre_market_gap_fade_digest_thin_sources",
        "market_research_equity_index_pre_market_gap_fade_digest_missing_confirmation",
        "market_research_equity_index_pre_market_gap_fade_digest_slow_acknowledgement",
        "market_research_equity_index_pre_market_gap_fade_digest_contradiction_present",
    )
    assert summary.reason_code_counts == (
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code="market_research_equity_index_pre_market_gap_fade_digest_material_gap",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code="market_research_equity_index_pre_market_gap_fade_digest_fade_pressure",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code=(
                "market_research_equity_index_pre_market_gap_fade_digest_"
                "extended_overnight_range"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code=(
                "market_research_equity_index_pre_market_gap_fade_digest_"
                "counter_trend_gap"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code=(
                "market_research_equity_index_pre_market_gap_fade_digest_"
                "low_opening_liquidity"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code="market_research_equity_index_pre_market_gap_fade_digest_stale_signal",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code="market_research_equity_index_pre_market_gap_fade_digest_thin_sources",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code=(
                "market_research_equity_index_pre_market_gap_fade_digest_"
                "missing_confirmation"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code=(
                "market_research_equity_index_pre_market_gap_fade_digest_"
                "slow_acknowledgement"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code=(
                "market_research_equity_index_pre_market_gap_fade_digest_"
                "contradiction_present"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )

    public = repr(asdict(summary)).lower()
    for token in ("token=raw", "vendor.example", "https://"):
        assert token not in public

    payload = market_research_equity_index_pre_market_gap_fade_digest_payload(summary)
    payload_text = repr(payload).lower()
    assert "condition_ndx_daily_close_range" not in payload_text
    assert "token=raw" not in payload_text
    assert payload["rows"][0]["redacted_condition_ref"] == "<redacted-condition-001>"
    assert payload["rows"][0]["gap_abs_pct"] == "0.018000"
    assert payload["gap_event_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)
    assert_public_numeric_fields_are_decimals(summary)
    assert_public_numeric_fields_are_decimals(summary.rows[0])


def test_empty_input_returns_blocked_report_only_digest() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_equity_index_pre_market_gap_fade_digest"
    )
    assert summary.gap_event_count == ZERO
    assert summary.ready_event_count == ZERO
    assert summary.watch_event_count == ZERO
    assert summary.blocked_event_count == ZERO
    assert summary.average_gap_abs_pct == ZERO
    assert summary.max_gap_abs_pct == ZERO
    assert summary.average_fade_pressure_score == ZERO
    assert summary.average_opening_liquidity_ratio == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_equity_index_pre_market_gap_fade_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code="market_research_equity_index_pre_market_gap_fade_digest_no_inputs",
            count=d("1.000000"),
            event_ratio=d("1.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_reversed_inputs_produce_same_ranked_report() -> None:
    first = input_row(
        "research.spx.gap_fade",
        gap_event_key="spx.20260704.preopen_gap",
        pre_market_gap_pct=d("0.011000"),
        fade_pressure_score=d("0.720000"),
    )
    second = input_row(
        "research.ndx.gap_fade",
        condition_id="condition_ndx_daily_close_range",
        index_symbol="NDX",
        gap_event_key="ndx.20260704.preopen_gap",
        pre_market_gap_pct=d("-0.016000"),
        prior_day_trend_pct=d("0.016000"),
        fade_pressure_score=d("0.810000"),
    )

    forward = report((first, second))
    reverse = report((second, first))

    assert forward.rows == reverse.rows
    assert forward.reason_codes == reverse.reason_codes
    assert forward.reason_code_counts == reverse.reason_code_counts
    assert tuple(row.gap_event_key for row in forward.rows) == (
        "ndx.20260704.preopen_gap",
        "spx.20260704.preopen_gap",
    )


def test_validation_guards_decimals_datetimes_flags_and_frozen_instances() -> None:
    summary = report((input_row(),))

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].gap_abs_pct = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="signaled_at must be timezone-aware"):
        input_row(signaled_at=datetime(2026, 7, 4, 13, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(
            (input_row(),),
            generated_at=_DateTimeSubclass(2026, 7, 4, 13, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="pre_market_gap_pct"):
        input_row(pre_market_gap_pct=d("1.000001"))
    with pytest.raises(ValueError, match="duplicate"):
        report((input_row(), input_row()))
    with pytest.raises(ValueError, match="acknowledged_at cannot be before signaled_at"):
        report(
            (
                input_row(
                    signaled_at=GENERATED_AT - timedelta(minutes=10),
                    acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                ),
            ),
        )
    with pytest.raises(ValueError, match="config must be"):
        build_market_research_equity_index_pre_market_gap_fade_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="ready rows require ready status"):
        MarketResearchEquityIndexPreMarketGapFadeRow(
            research_key="research.bad",
            condition_id="condition_bad",
            index_symbol="SPX",
            gap_event_key="spx.bad",
            gap_status="watch",
            gap_direction="flat",
            signal_age_seconds=d("1.000000"),
            acknowledgement_lag_seconds=d("1.000000"),
            source_count=d("2"),
            confirmation_count=d("1"),
            pre_market_gap_pct=ZERO,
            gap_abs_pct=ZERO,
            overnight_range_pct=ZERO,
            prior_day_trend_pct=ZERO,
            fade_pressure_score=ZERO,
            opening_liquidity_ratio=d("0.500000"),
            contradiction_count=ZERO,
            redacted_signal_reference="public",
            reason_codes=(
                "market_research_equity_index_pre_market_gap_fade_digest_ready",
            ),
        )

    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchEquityIndexPreMarketGapFadeReasonCodeCount(
            reason_code="market_research_equity_index_pre_market_gap_fade_digest_ready",
            count=ZERO,
            event_ratio=ZERO,
        )

    with pytest.raises(ValueError, match="gap_event_count must match rows"):
        MarketResearchEquityIndexPreMarketGapFadeReport(
            generated_at=summary.generated_at,
            config_version=summary.config_version,
            digest_status=summary.digest_status,
            recommended_next_step=summary.recommended_next_step,
            gap_event_count=ZERO,
            ready_event_count=summary.ready_event_count,
            watch_event_count=summary.watch_event_count,
            blocked_event_count=summary.blocked_event_count,
            material_gap_count=summary.material_gap_count,
            fade_pressure_count=summary.fade_pressure_count,
            extended_overnight_range_count=summary.extended_overnight_range_count,
            counter_trend_gap_count=summary.counter_trend_gap_count,
            low_opening_liquidity_count=summary.low_opening_liquidity_count,
            stale_signal_count=summary.stale_signal_count,
            thin_source_count=summary.thin_source_count,
            missing_confirmation_count=summary.missing_confirmation_count,
            slow_acknowledgement_count=summary.slow_acknowledgement_count,
            contradiction_count=summary.contradiction_count,
            average_gap_abs_pct=summary.average_gap_abs_pct,
            max_gap_abs_pct=summary.max_gap_abs_pct,
            average_fade_pressure_score=summary.average_fade_pressure_score,
            average_opening_liquidity_ratio=summary.average_opening_liquidity_ratio,
            max_signal_age_seconds=summary.max_signal_age_seconds,
            rows=summary.rows,
            reason_code_counts=summary.reason_code_counts,
            reason_codes=summary.reason_codes,
        )

    payload = market_research_equity_index_pre_market_gap_fade_digest_payload(summary)
    assert_no_floats(payload)


def test_hard_report_only_flags_are_enforced() -> None:
    summary = report((input_row(),))

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="input row readonly must be True"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        dataclasses.replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        dataclasses.replace(summary.rows[0], report_only=False)


def test_non_default_thresholds_can_suppress_borderline_gap_fade_watch() -> None:
    row = input_row(
        pre_market_gap_pct=d("0.008000"),
        overnight_range_pct=d("0.012000"),
        prior_day_trend_pct=d("-0.014000"),
        fade_pressure_score=d("0.700000"),
        opening_liquidity_ratio=d("0.300000"),
    )

    default_summary = report((row,))
    strict_summary = report(
        (row,),
        cfg=config(
            min_abs_pre_market_gap_pct=d("0.010000"),
            min_fade_pressure_score=d("0.800000"),
            min_overnight_range_pct=d("0.020000"),
            min_abs_prior_day_trend_pct=d("0.030000"),
            max_opening_liquidity_ratio=d("0.100000"),
        ),
    )

    assert default_summary.digest_status == "watch"
    assert default_summary.reason_codes == (
        "market_research_equity_index_pre_market_gap_fade_digest_material_gap",
        "market_research_equity_index_pre_market_gap_fade_digest_fade_pressure",
        "market_research_equity_index_pre_market_gap_fade_digest_extended_overnight_range",
        "market_research_equity_index_pre_market_gap_fade_digest_counter_trend_gap",
        "market_research_equity_index_pre_market_gap_fade_digest_low_opening_liquidity",
    )
    assert strict_summary.digest_status == "ready"
    assert strict_summary.reason_codes == (
        "market_research_equity_index_pre_market_gap_fade_digest_ready",
    )
    assert strict_summary.material_gap_count == ZERO
    assert strict_summary.fade_pressure_count == ZERO
    assert strict_summary.low_opening_liquidity_count == ZERO


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/"
        "market_research_equity_index_pre_market_gap_fade_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "rename",
        "submit",
        "cancel",
        "replace",
        "wallet",
        "broker",
        "account",
        "sign",
        "auth",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in lowered_surface)
    assert "persist" not in source.lower()
    assert "database" not in source.lower()
    assert "wallet" not in source.lower()
    assert "live trading" not in source.lower()


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float value leaked into payload: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_floats(nested)
    if isinstance(value, (list, tuple)):
        for nested in value:
            assert_no_floats(nested)


def assert_public_numeric_fields_are_decimals(value: object) -> None:
    numeric_name_fragments = (
        "age",
        "count",
        "liquidity",
        "pct",
        "range",
        "ratio",
        "score",
        "seconds",
    )
    for field in dataclasses.fields(value):
        if any(fragment in field.name for fragment in numeric_name_fragments):
            field_value: Any = getattr(value, field.name)
            if isinstance(field_value, datetime):
                continue
            if isinstance(field_value, tuple):
                continue
            if field_value is None:
                continue
            assert type(field_value) is Decimal, field.name

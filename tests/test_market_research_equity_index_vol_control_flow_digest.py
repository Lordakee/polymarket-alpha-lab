from __future__ import annotations

import ast
import dataclasses
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_equity_index_vol_control_flow_digest import (
    DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_VOL_CONTROL_FLOW_DIGEST_CONFIG_VERSION,
    MarketResearchEquityIndexVolControlFlowDigestConfig,
    MarketResearchEquityIndexVolControlFlowInputRow,
    MarketResearchEquityIndexVolControlFlowReasonCodeCount,
    MarketResearchEquityIndexVolControlFlowReport,
    MarketResearchEquityIndexVolControlFlowRow,
    build_market_research_equity_index_vol_control_flow_digest,
    market_research_equity_index_vol_control_flow_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchEquityIndexVolControlFlowDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_VOL_CONTROL_FLOW_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2"),
        "min_confirmation_count": d("1"),
        "min_abs_estimated_flow_usd": d("250000000.000000"),
        "min_abs_volatility_gap": d("0.020000"),
        "min_abs_equity_weight_change": d("0.030000"),
        "max_acknowledgement_lag_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return MarketResearchEquityIndexVolControlFlowDigestConfig(**values)


def input_row(
    research_key: str = "research.spx.vol-control",
    *,
    condition_id: str = "condition_spx_vol_control",
    index_symbol: str = "SPX",
    vol_control_event_key: str = "spx.vol-control.deleveraging",
    flow_direction: str = "deleveraging",
    signal_reference: str = "public-vol-control-notice",
    signaled_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3"),
    confirmation_count: Decimal = d("2"),
    realized_volatility: Decimal = d("0.120000"),
    target_volatility: Decimal = d("0.100000"),
    equity_weight_before: Decimal = d("0.800000"),
    equity_weight_after: Decimal = d("0.750000"),
    estimated_flow_usd: Decimal = d("-300000000.000000"),
    tracking_volume_ratio: Decimal = d("0.700000"),
    contradiction_count: Decimal = d("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEquityIndexVolControlFlowInputRow:
    signal_time = signaled_at or GENERATED_AT - timedelta(minutes=30)
    return MarketResearchEquityIndexVolControlFlowInputRow(
        research_key=research_key,
        condition_id=condition_id,
        index_symbol=index_symbol,
        vol_control_event_key=vol_control_event_key,
        flow_direction=flow_direction,
        signal_reference=signal_reference,
        signaled_at=signal_time,
        acknowledged_at=(
            signal_time + timedelta(minutes=10)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        confirmation_count=confirmation_count,
        realized_volatility=realized_volatility,
        target_volatility=target_volatility,
        equity_weight_before=equity_weight_before,
        equity_weight_after=equity_weight_after,
        estimated_flow_usd=estimated_flow_usd,
        tracking_volume_ratio=tracking_volume_ratio,
        contradiction_count=contradiction_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchEquityIndexVolControlFlowDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEquityIndexVolControlFlowReport:
    return build_market_research_equity_index_vol_control_flow_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_vol_control_flow_digest_reduces_rows_redacts_refs_and_sorts_deterministically() -> None:
    summary = report(
        (
            input_row(
                "research.ndx.releveraging",
                condition_id="condition_ndx_releveraging",
                index_symbol="NDX",
                vol_control_event_key="ndx.vol-control.releveraging",
                flow_direction="releveraging",
                signal_reference="public-ndx-vol-control-notice",
                signaled_at=GENERATED_AT - timedelta(minutes=30),
                source_count=d("3"),
                confirmation_count=d("2"),
                realized_volatility=d("0.080000"),
                target_volatility=d("0.100000"),
                equity_weight_before=d("0.600000"),
                equity_weight_after=d("0.660000"),
                estimated_flow_usd=d("300000000.000000"),
                tracking_volume_ratio=d("0.700000"),
            ),
            input_row(
                "research.spx.deleveraging",
                condition_id="condition_spx_deleveraging",
                index_symbol="SPX",
                vol_control_event_key="spx.vol-control.deleveraging",
                flow_direction="deleveraging",
                signal_reference="https://vendor.example/vol-control-flow?case=spx",
                signaled_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=GENERATED_AT - timedelta(minutes=90),
                source_count=d("1"),
                confirmation_count=d("0"),
                realized_volatility=d("0.160000"),
                target_volatility=d("0.100000"),
                equity_weight_before=d("0.850000"),
                equity_weight_after=d("0.720000"),
                estimated_flow_usd=d("-500000000.000000"),
                tracking_volume_ratio=d("0.850000"),
                contradiction_count=d("1"),
            ),
            input_row(
                "research.rty.deleveraging",
                condition_id="condition_rty_deleveraging",
                index_symbol="RTY",
                vol_control_event_key="rty.vol-control.deleveraging",
                flow_direction="deleveraging",
                signal_reference="private-vol-control-feed",
                signaled_at=GENERATED_AT - timedelta(hours=4),
                acknowledged_at=GENERATED_AT - timedelta(hours=2),
                source_count=d("2"),
                confirmation_count=d("1"),
                realized_volatility=d("0.130000"),
                target_volatility=d("0.100000"),
                equity_weight_before=d("0.750000"),
                equity_weight_after=d("0.730000"),
                estimated_flow_usd=d("-100000000.000000"),
                tracking_volume_ratio=d("0.400000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_VOL_CONTROL_FLOW_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_equity_index_vol_control_flow_digest"
    )
    assert summary.vol_control_event_count == d("3.000000")
    assert summary.ready_event_count == d("1.000000")
    assert summary.watch_event_count == d("1.000000")
    assert summary.blocked_event_count == d("1.000000")
    assert summary.material_flow_count == d("2.000000")
    assert summary.volatility_gap_count == d("3.000000")
    assert summary.large_equity_weight_change_count == d("2.000000")
    assert summary.stale_signal_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_confirmation_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("2.000000")
    assert summary.contradiction_count == d("1.000000")
    assert summary.net_estimated_flow_usd == d("-300000000.000000")
    assert summary.gross_estimated_flow_usd == d("900000000.000000")
    assert summary.max_flow_abs_usd == d("500000000.000000")
    assert summary.average_abs_volatility_gap == d("0.036667")
    assert summary.average_tracking_volume_ratio == d("0.650000")
    assert summary.max_signal_age_seconds == d("14400.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.index_symbol, row.vol_control_event_key) for row in summary.rows) == (
        ("SPX", "spx.vol-control.deleveraging"),
        ("RTY", "rty.vol-control.deleveraging"),
        ("NDX", "ndx.vol-control.releveraging"),
    )

    spx = summary.rows[0]
    assert spx.flow_status == "blocked"
    assert spx.signal_age_seconds == d("10800.000000")
    assert spx.acknowledgement_lag_seconds == d("5400.000000")
    assert spx.volatility_gap == d("0.060000")
    assert spx.abs_volatility_gap == d("0.060000")
    assert spx.equity_weight_change == d("-0.130000")
    assert spx.flow_abs_usd == d("500000000.000000")
    assert spx.redacted_signal_reference == "sha256:0767b1dc75b1"
    assert spx.reason_codes == (
        "market_research_equity_index_vol_control_flow_digest_material_flow",
        "market_research_equity_index_vol_control_flow_digest_volatility_gap",
        "market_research_equity_index_vol_control_flow_digest_large_equity_weight_change",
        "market_research_equity_index_vol_control_flow_digest_stale_signal",
        "market_research_equity_index_vol_control_flow_digest_thin_sources",
        "market_research_equity_index_vol_control_flow_digest_missing_confirmation",
        "market_research_equity_index_vol_control_flow_digest_slow_acknowledgement",
        "market_research_equity_index_vol_control_flow_digest_contradiction_present",
    )

    rty = summary.rows[1]
    assert rty.flow_status == "watch"
    assert rty.signal_age_seconds == d("14400.000000")
    assert rty.acknowledgement_lag_seconds == d("7200.000000")
    assert rty.redacted_signal_reference == "sha256:84eafc78d967"
    assert rty.reason_codes == (
        "market_research_equity_index_vol_control_flow_digest_volatility_gap",
        "market_research_equity_index_vol_control_flow_digest_stale_signal",
        "market_research_equity_index_vol_control_flow_digest_slow_acknowledgement",
    )

    ndx = summary.rows[2]
    assert ndx.flow_status == "ready"
    assert ndx.signal_age_seconds == d("1800.000000")
    assert ndx.acknowledgement_lag_seconds == d("600.000000")
    assert ndx.volatility_gap == d("-0.020000")
    assert ndx.equity_weight_change == d("0.060000")
    assert ndx.reason_codes == (
        "market_research_equity_index_vol_control_flow_digest_ready",
        "market_research_equity_index_vol_control_flow_digest_material_flow",
        "market_research_equity_index_vol_control_flow_digest_volatility_gap",
        "market_research_equity_index_vol_control_flow_digest_large_equity_weight_change",
    )

    assert summary.reason_codes == (
        "market_research_equity_index_vol_control_flow_digest_material_flow",
        "market_research_equity_index_vol_control_flow_digest_volatility_gap",
        "market_research_equity_index_vol_control_flow_digest_large_equity_weight_change",
        "market_research_equity_index_vol_control_flow_digest_stale_signal",
        "market_research_equity_index_vol_control_flow_digest_thin_sources",
        "market_research_equity_index_vol_control_flow_digest_missing_confirmation",
        "market_research_equity_index_vol_control_flow_digest_slow_acknowledgement",
        "market_research_equity_index_vol_control_flow_digest_contradiction_present",
    )
    assert summary.reason_code_counts == (
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code=(
                "market_research_equity_index_vol_control_flow_digest_volatility_gap"
            ),
            count=d("3.000000"),
            event_ratio=d("1.000000"),
        ),
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code="market_research_equity_index_vol_control_flow_digest_material_flow",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code=(
                "market_research_equity_index_vol_control_flow_digest_"
                "large_equity_weight_change"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code="market_research_equity_index_vol_control_flow_digest_stale_signal",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code=(
                "market_research_equity_index_vol_control_flow_digest_"
                "slow_acknowledgement"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code="market_research_equity_index_vol_control_flow_digest_thin_sources",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code=(
                "market_research_equity_index_vol_control_flow_digest_"
                "missing_confirmation"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code=(
                "market_research_equity_index_vol_control_flow_digest_"
                "contradiction_present"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )

    payload = market_research_equity_index_vol_control_flow_digest_payload(summary)
    payload_text = repr(payload).lower()
    assert "condition_spx_deleveraging" not in payload_text
    assert "vendor.example" not in payload_text
    assert "case=spx" not in payload_text
    assert "private-vol-control-feed" not in payload_text
    assert payload["rows"][0]["redacted_condition_ref"] == "<redacted-condition-001>"
    assert payload["rows"][0]["redacted_signal_reference"] == "sha256:0767b1dc75b1"
    assert payload["rows"][0]["flow_abs_usd"] == "500000000.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])


def test_empty_input_returns_blocked_report_only_digest() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_equity_index_vol_control_flow_digest"
    )
    assert summary.vol_control_event_count == ZERO
    assert summary.ready_event_count == ZERO
    assert summary.net_estimated_flow_usd == ZERO
    assert summary.gross_estimated_flow_usd == ZERO
    assert summary.average_abs_volatility_gap == ZERO
    assert summary.average_tracking_volume_ratio == ZERO
    assert summary.max_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_equity_index_vol_control_flow_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code="market_research_equity_index_vol_control_flow_digest_no_inputs",
            count=d("1.000000"),
            event_ratio=ZERO,
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_decimal_microsecond_timing_is_deterministic() -> None:
    summary = report(
        (
            input_row(
                signaled_at=datetime(2026, 7, 4, 15, 59, 57, 1, tzinfo=UTC),
                acknowledged_at=datetime(2026, 7, 4, 15, 59, 59, 999999, tzinfo=UTC),
            ),
        ),
        generated_at=datetime(2026, 7, 4, 16, 0, 0, 234567, tzinfo=UTC),
    )

    assert summary.max_signal_age_seconds == d("3.234566")
    assert summary.rows[0].signal_age_seconds == d("3.234566")
    assert summary.rows[0].acknowledgement_lag_seconds == d("2.999998")


def test_validation_guards_decimals_datetimes_flags_and_frozen_instances() -> None:
    assert is_dataclass(MarketResearchEquityIndexVolControlFlowDigestConfig)
    assert is_dataclass(MarketResearchEquityIndexVolControlFlowInputRow)
    assert is_dataclass(MarketResearchEquityIndexVolControlFlowRow)
    assert is_dataclass(MarketResearchEquityIndexVolControlFlowReasonCodeCount)
    assert is_dataclass(MarketResearchEquityIndexVolControlFlowReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].flow_abs_usd = d("0.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        input_row(source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="target_volatility must be a Decimal"):
        input_row(target_volatility=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="signaled_at must be timezone-aware"):
        input_row(signaled_at=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(
            (input_row(),),
            generated_at=_DatetimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="flow_direction must be one of"):
        input_row(flow_direction="sideways")
    with pytest.raises(ValueError, match="estimated_flow_usd direction mismatch"):
        input_row(flow_direction="deleveraging", estimated_flow_usd=d("1.000000"))
    with pytest.raises(ValueError, match="acknowledged_at cannot be before signaled_at"):
        report(
            (
                input_row(
                    signaled_at=GENERATED_AT - timedelta(minutes=20),
                    acknowledged_at=GENERATED_AT - timedelta(minutes=30),
                ),
            ),
        )
    with pytest.raises(ValueError, match="rows must use unique research condition event keys"):
        report((input_row(), input_row()))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="input row readonly must be True"):
        input_row(readonly=False)

    payload = market_research_equity_index_vol_control_flow_digest_payload(summary)
    assert_no_floats(payload)


def test_manual_dataclass_consistency_checks_reject_incoherent_values() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="ready cannot be combined"):
        replace(
            ready,
            reason_codes=(
                "market_research_equity_index_vol_control_flow_digest_ready",
                "market_research_equity_index_vol_control_flow_digest_stale_signal",
            ),
        )
    with pytest.raises(ValueError, match="flow_status must match reason_codes"):
        replace(ready, flow_status="blocked")
    with pytest.raises(ValueError, match="flow_abs_usd must match estimated_flow_usd"):
        replace(ready, flow_abs_usd=d("1.000000"))
    with pytest.raises(ValueError, match="volatility_gap must match"):
        replace(ready, volatility_gap=d("0.990000"))
    with pytest.raises(ValueError, match="redacted_signal_reference must be redacted"):
        replace(ready, redacted_signal_reference="https://vendor.example/raw")

    with pytest.raises(ValueError, match="ready_event_count must match rows"):
        replace(report((input_row(),)), ready_event_count=ZERO)
    with pytest.raises(ValueError, match="rows must use deterministic sort"):
        replace(
            report(
                (
                    input_row("research.a", vol_control_event_key="event.a"),
                    input_row("research.b", vol_control_event_key="event.b"),
                ),
            ),
            rows=tuple(
                reversed(
                    report(
                        (
                            input_row("research.a", vol_control_event_key="event.a"),
                            input_row("research.b", vol_control_event_key="event.b"),
                        ),
                    ).rows,
                ),
            ),
        )

    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchEquityIndexVolControlFlowReasonCodeCount(
            reason_code="market_research_equity_index_vol_control_flow_digest_ready",
            count=ZERO,
            event_ratio=ZERO,
        )


def test_module_has_no_io_store_or_execution_surfaces() -> None:
    import polymarket_alpha_lab.market_research_equity_index_vol_control_flow_digest as module

    module_path = Path(module.__file__)
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
        "subprocess",
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
        "replace",
        "submit",
        "cancel",
        "order",
        "trade",
        "wallet",
        "broker",
        "account",
        "auth",
        "sign",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in lowered_surface)
    assert "database" not in source.lower()
    assert "investment_advice" not in source.lower()
    assert "live_trading" not in source.lower()
    assert "private_key" not in source.lower()
    assert "trading_advice" not in source.lower()


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float value leaked into payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_floats(item)


def assert_decimal_numeric_fields(value: object) -> None:
    numeric_name_fragments = (
        "age",
        "count",
        "gap",
        "lag",
        "ratio",
        "usd",
        "volatility",
        "weight",
    )
    for field in dataclasses.fields(value):
        if any(fragment in field.name for fragment in numeric_name_fragments):
            field_value = getattr(value, field.name)
            if isinstance(field_value, datetime):
                continue
            if isinstance(field_value, tuple):
                continue
            assert type(field_value) is Decimal, field.name

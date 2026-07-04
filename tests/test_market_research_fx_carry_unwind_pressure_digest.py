from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_fx_carry_unwind_pressure_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-fx-carry-unwind-pressure-digest-v0",
        "watch_pressure_score": d("0.350000"),
        "blocked_pressure_score": d("0.700000"),
        "max_source_age_seconds": d("900.000000"),
        "stale_confidence_cap": d("0.350000"),
        "watch_confidence_cap": d("0.650000"),
        "calm_confidence_cap": d("0.550000"),
    }
    values.update(overrides)
    return module.FXCarryUnwindPressureDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "aud-jpy-carry-pressure-watch",
    carry_pair: str = "aud-jpy",
    funding_currency: str = "jpy",
    target_currency: str = "aud",
    carry_return_pct: Decimal = d("-0.020000"),
    funding_currency_return_pct: Decimal = d("0.015000"),
    volatility_z_score: Decimal = d("2.000000"),
    rate_differential_compression_pct: Decimal = d("0.010000"),
    liquidity_stress_ratio: Decimal = d("0.550000"),
    positioning_unwind_ratio: Decimal = d("0.400000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=1200),
    base_confidence: Decimal = d("0.850000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.FXCarryUnwindPressureObservation(
        source_id=source_id,
        market_slug=market_slug,
        carry_pair=carry_pair,
        funding_currency=funding_currency,
        target_currency=target_currency,
        carry_return_pct=carry_return_pct,
        funding_currency_return_pct=funding_currency_return_pct,
        volatility_z_score=volatility_z_score,
        rate_differential_compression_pct=rate_differential_compression_pct,
        liquidity_stress_ratio=liquidity_stress_ratio,
        positioning_unwind_ratio=positioning_unwind_ratio,
        observed_at=observed_at,
        base_confidence=base_confidence,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    inputs: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_fx_carry_unwind_pressure_digest(
        inputs,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_or_decimal_payload(value: object) -> None:
    if isinstance(value, (float, Decimal)):
        pytest.fail("serialized payload must not contain float or Decimal numerics")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_decimal_payload(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_float_or_decimal_payload(child)


def test_empty_digest_payload_is_report_only_readonly_and_decimal_stringed() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_fx_carry_unwind_pressure_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_pressure_count == d("0.000000")
    assert report.watch_pressure_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.max_pressure_score == d("0.000000")
    assert report.average_pressure_score == d("0.000000")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_fx_carry_unwind_pressure_digest"
    )
    assert report.reason_codes == ("fx_carry_unwind_pressure_digest_empty",)
    assert report.reason_code_counts == (
        module.FXCarryUnwindPressureReasonCodeCount(
            reason_code="fx_carry_unwind_pressure_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_decimal_payload(payload)


def test_high_risk_fx_carry_unwind_pressure_classifies_blocked() -> None:
    report = digest(
        (
            observation(
                "zeta-blocked",
                market_slug="mxn-jpy-carry-pressure-blocked",
                carry_pair="mxn-jpy",
                target_currency="mxn",
                carry_return_pct=d("-0.060000"),
                funding_currency_return_pct=d("0.045000"),
                volatility_z_score=d("3.200000"),
                rate_differential_compression_pct=d("0.024000"),
                liquidity_stress_ratio=d("0.800000"),
                positioning_unwind_ratio=d("0.900000"),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                upstream_reason_codes=("macro_catalyst", "dealer_flow"),
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.input_count == d("1.000000")
    assert report.row_count == d("1.000000")
    assert report.blocked_pressure_count == d("1.000000")
    assert report.watch_pressure_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.stale_source_count == d("0.000000")
    assert report.carry_pressure_count == d("1.000000")
    assert report.max_pressure_score == d("0.788000")
    assert report.average_pressure_score == d("0.788000")
    assert report.digest_status == "blocked"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.observed_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert row.source_age_seconds == d("60.000000")
    assert row.pressure_score == d("0.788000")
    assert row.pressure_status == "blocked"
    assert row.pressure_direction == "carry_unwind_pressure"
    assert row.confidence_cap == d("1.000000")
    assert row.capped_confidence == d("0.850000")
    assert row.reason_codes == (
        "carry_leg_drawdown",
        "dealer_flow",
        "funding_currency_rally",
        "fx_carry_pressure_source_fresh",
        "fx_carry_unwind_pressure_blocked",
        "liquidity_stress_high",
        "macro_catalyst",
        "positioning_unwind_high",
        "rate_differential_compression_high",
        "volatility_pressure_high",
    )


def test_sorting_and_reason_rollups_are_deterministic() -> None:
    inputs = (
        observation(
            "beta-calm",
            market_slug="aud-jpy-carry-pressure-calm",
            carry_return_pct=d("0.005000"),
            funding_currency_return_pct=d("-0.001000"),
            volatility_z_score=d("0.400000"),
            rate_differential_compression_pct=d("0.002000"),
            liquidity_stress_ratio=d("0.100000"),
            positioning_unwind_ratio=d("0.050000"),
            observed_at=GENERATED_AT - timedelta(seconds=60),
            upstream_reason_codes=("desk_note",),
        ),
        observation("alpha-watch"),
        observation(
            "zeta-blocked",
            market_slug="mxn-jpy-carry-pressure-blocked",
            carry_pair="mxn-jpy",
            target_currency="mxn",
            carry_return_pct=d("-0.060000"),
            funding_currency_return_pct=d("0.045000"),
            volatility_z_score=d("3.200000"),
            rate_differential_compression_pct=d("0.024000"),
            liquidity_stress_ratio=d("0.800000"),
            positioning_unwind_ratio=d("0.900000"),
            observed_at=GENERATED_AT - timedelta(seconds=120),
            upstream_reason_codes=("macro_catalyst",),
        ),
    )

    report_a = digest(inputs)
    report_b = digest(tuple(reversed(inputs)))

    assert report_a == report_b
    assert [
        (row.source_id, row.pressure_status, row.pressure_score)
        for row in report_a.rows
    ] == [
        ("zeta-blocked", "blocked", d("0.788000")),
        ("alpha-watch", "watch", d("0.355000")),
        ("beta-calm", "pass", d("0.042000")),
    ]
    assert report_a.blocked_pressure_count == d("1.000000")
    assert report_a.watch_pressure_count == d("1.000000")
    assert report_a.pass_count == d("1.000000")
    assert report_a.stale_source_count == d("1.000000")
    assert report_a.carry_pressure_count == d("2.000000")
    assert report_a.max_pressure_score == d("0.788000")
    assert report_a.average_pressure_score == d("0.395000")
    assert report_a.reason_codes == (
        "carry_leg_drawdown",
        "desk_note",
        "funding_currency_rally",
        "fx_carry_pressure_source_fresh",
        "fx_carry_pressure_source_stale",
        "fx_carry_unwind_pressure_blocked",
        "fx_carry_unwind_pressure_calm",
        "fx_carry_unwind_pressure_watch",
        "liquidity_stress_high",
        "macro_catalyst",
        "positioning_unwind_high",
        "rate_differential_compression_high",
        "volatility_pressure_high",
    )
    assert report_a.reason_code_counts[0].reason_code == "carry_leg_drawdown"
    assert report_a.reason_code_counts[0].count == d("2.000000")
    assert report_a.reason_code_counts[0].row_ratio == d("0.666667")

    watch = report_a.rows[1]
    assert watch.confidence_cap == d("0.350000")
    assert watch.capped_confidence == d("0.350000")
    assert watch.reason_codes == (
        "carry_leg_drawdown",
        "fx_carry_pressure_source_stale",
        "fx_carry_unwind_pressure_watch",
    )
    passed = report_a.rows[2]
    assert passed.pressure_direction == "carry_pressure_calm"
    assert passed.confidence_cap == d("0.550000")
    assert passed.capped_confidence == d("0.550000")


def test_non_default_thresholds_can_reclassify_watch_pressure_as_pass() -> None:
    report = digest(
        (observation(),),
        cfg=config(
            watch_pressure_score=d("0.500000"),
            blocked_pressure_score=d("0.900000"),
        ),
    )

    assert report.rows[0].pressure_score == d("0.355000")
    assert report.rows[0].pressure_status == "pass"
    assert report.rows[0].pressure_direction == "carry_pressure_calm"
    assert report.pass_count == d("1.000000")
    assert report.watch_pressure_count == d("0.000000")
    assert report.digest_status == "pass"
    assert report.recommended_next_step == (
        "allow_report_only_market_research_fx_carry_unwind_pressure_digest"
    )


def test_rejects_bad_types_datetimes_duplicates_future_rows_and_thresholds() -> None:
    with pytest.raises(ValueError, match="carry_return_pct"):
        observation(carry_return_pct=_DecimalSubclass("-0.010000"))

    with pytest.raises(ValueError, match="liquidity_stress_ratio"):
        observation(liquidity_stress_ratio=d("1.100000"))

    with pytest.raises(ValueError, match="rate_differential_compression_pct"):
        observation(rate_differential_compression_pct=d("-0.010000"))

    with pytest.raises(ValueError, match="watch_pressure_score"):
        config(watch_pressure_score=0.35)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="watch_pressure_score"):
        config(
            watch_pressure_score=d("0.900000"),
            blocked_pressure_score=d("0.700000"),
        )

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="duplicate source_id"):
        digest((observation("dupe"), observation("dupe")))

    with pytest.raises(ValueError, match="config"):
        module = api()
        module.build_market_research_fx_carry_unwind_pressure_digest(
            (observation(),),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_hard_flags_frozen_public_records_and_pure_surface() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    report = digest((observation(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.FXCarryUnwindPressureDigestConfig,
        module.FXCarryUnwindPressureObservation,
        module.FXCarryUnwindPressureDigestRow,
        module.FXCarryUnwindPressureReasonCodeCount,
        module.FXCarryUnwindPressureDigestReport,
    )
    for type_ in classes:
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type

    source = inspect.getsource(module).lower()
    for forbidden in (
        "requests",
        "httpx",
        "urlopen",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "connect(",
        "execute(",
        "open(",
        "web3",
        "wallet",
        "private_key",
        "place_order",
        "cancel_order",
        "replace_order",
        "auth",
        "secret",
        "database",
        "network",
    ):
        assert forbidden not in source

    tree = ast.parse(
        Path(
            "src/polymarket_alpha_lab/market_research_fx_carry_unwind_pressure_digest.py",
        ).read_text(),
    )
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

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
        "polymarket_alpha_lab.market_research_fx_options_risk_reversal_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-fx-options-risk-reversal-digest-v0",
        "watch_risk_reversal_shift_bps": d("25.000000"),
        "blocked_risk_reversal_shift_bps": d("75.000000"),
        "watch_absolute_risk_reversal_bps": d("50.000000"),
        "blocked_absolute_risk_reversal_bps": d("100.000000"),
        "watch_stress_score": d("0.350000"),
        "blocked_stress_score": d("0.650000"),
        "max_source_age_seconds": d("600.000000"),
        "stale_confidence_cap": d("0.300000"),
        "watch_confidence_cap": d("0.500000"),
    }
    values.update(overrides)
    return module.FXOptionsRiskReversalDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "eur-usd-risk-reversal-stress",
    currency_pair: str = "eur-usd",
    option_tenor: str = "1m",
    current_risk_reversal_bps: Decimal = d("60.000000"),
    baseline_risk_reversal_bps: Decimal = d("20.000000"),
    implied_volatility_z_score: Decimal = d("2.000000"),
    option_liquidity_stress_ratio: Decimal = d("0.400000"),
    skew_dislocation_ratio: Decimal = d("0.350000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    base_confidence: Decimal = d("0.850000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.FXOptionsRiskReversalObservation(
        source_id=source_id,
        market_slug=market_slug,
        currency_pair=currency_pair,
        option_tenor=option_tenor,
        current_risk_reversal_bps=current_risk_reversal_bps,
        baseline_risk_reversal_bps=baseline_risk_reversal_bps,
        implied_volatility_z_score=implied_volatility_z_score,
        option_liquidity_stress_ratio=option_liquidity_stress_ratio,
        skew_dislocation_ratio=skew_dislocation_ratio,
        observed_at=observed_at,
        base_confidence=base_confidence,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(inputs: tuple[Any, ...], *, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_fx_options_risk_reversal_digest(
        inputs,
        config=config(),
        generated_at=generated_at,
    )


def assert_no_float_or_decimal_payload(value: object) -> None:
    if isinstance(value, (float, Decimal)):
        pytest.fail("public payload must not contain float or Decimal numerics")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_decimal_payload(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_float_or_decimal_payload(child)


def test_builds_report_only_fx_options_risk_reversal_digest_with_sorting_reasons() -> None:
    report = digest(
        (
            observation(
                "beta-watch",
                market_slug="gbp-usd-risk-reversal-watch",
                currency_pair="gbp-usd",
                current_risk_reversal_bps=d("60.000000"),
                baseline_risk_reversal_bps=d("20.000000"),
                upstream_reason_codes=("dealer_skew_watch",),
            ),
            observation(
                "alpha-calm",
                market_slug="aud-usd-risk-reversal-calm",
                currency_pair="aud-usd",
                current_risk_reversal_bps=d("-10.000000"),
                baseline_risk_reversal_bps=d("0.000000"),
                implied_volatility_z_score=d("0.400000"),
                option_liquidity_stress_ratio=d("0.100000"),
                skew_dislocation_ratio=d("0.100000"),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
            observation(
                "zeta-blocked",
                market_slug="eur-usd-risk-reversal-blocked",
                current_risk_reversal_bps=d("125.000000"),
                baseline_risk_reversal_bps=d("25.000000"),
                implied_volatility_z_score=d("3.200000"),
                option_liquidity_stress_ratio=d("0.800000"),
                skew_dislocation_ratio=d("0.800000"),
                observed_at=GENERATED_AT - timedelta(seconds=900),
                upstream_reason_codes=("dealer_skew_watch", "option_surface_panel"),
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "market-research-fx-options-risk-reversal-digest-v0"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_skew_count == d("1.000000")
    assert report.watch_skew_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.reversal_steepening_count == d("2.000000")
    assert report.reversal_flattening_count == d("1.000000")
    assert report.max_stress_score == d("0.886667")
    assert report.average_stress_score == d("0.460833")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_fx_options_risk_reversal_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.source_id, row.skew_status, row.stress_score)
        for row in report.rows
    ] == [
        ("zeta-blocked", "blocked", d("0.886667")),
        ("beta-watch", "watch", d("0.402500")),
        ("alpha-calm", "pass", d("0.093333")),
    ]

    blocked, watch, passed = report.rows
    assert blocked.source_age_seconds == d("900.000000")
    assert blocked.risk_reversal_shift_bps == d("100.000000")
    assert blocked.absolute_risk_reversal_bps == d("125.000000")
    assert blocked.confidence_cap == d("0.300000")
    assert blocked.capped_confidence == d("0.300000")
    assert blocked.reason_codes == (
        "dealer_skew_watch",
        "fx_options_risk_reversal_level_blocked",
        "fx_options_risk_reversal_shift_blocked",
        "fx_options_risk_reversal_source_stale",
        "fx_options_risk_reversal_steepening",
        "fx_options_risk_reversal_stress_blocked",
        "implied_volatility_z_high",
        "option_liquidity_stress_high",
        "option_surface_panel",
        "skew_dislocation_high",
    )
    assert watch.confidence_cap == d("0.500000")
    assert watch.capped_confidence == d("0.500000")
    assert watch.reason_codes == (
        "dealer_skew_watch",
        "fx_options_risk_reversal_level_watch",
        "fx_options_risk_reversal_shift_watch",
        "fx_options_risk_reversal_source_fresh",
        "fx_options_risk_reversal_steepening",
        "fx_options_risk_reversal_stress_watch",
    )
    assert passed.observed_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert passed.risk_reversal_shift_bps == d("-10.000000")
    assert passed.absolute_risk_reversal_bps == d("10.000000")
    assert passed.reason_codes == (
        "fx_options_risk_reversal_flattening",
        "fx_options_risk_reversal_source_fresh",
        "fx_options_risk_reversal_stress_calm",
    )
    assert report.reason_codes == (
        "dealer_skew_watch",
        "fx_options_risk_reversal_flattening",
        "fx_options_risk_reversal_level_blocked",
        "fx_options_risk_reversal_level_watch",
        "fx_options_risk_reversal_shift_blocked",
        "fx_options_risk_reversal_shift_watch",
        "fx_options_risk_reversal_source_fresh",
        "fx_options_risk_reversal_source_stale",
        "fx_options_risk_reversal_steepening",
        "fx_options_risk_reversal_stress_blocked",
        "fx_options_risk_reversal_stress_calm",
        "fx_options_risk_reversal_stress_watch",
        "implied_volatility_z_high",
        "option_liquidity_stress_high",
        "option_surface_panel",
        "skew_dislocation_high",
    )
    assert report.reason_code_counts[0].reason_code == "dealer_skew_watch"
    assert report.reason_code_counts[0].count == d("2.000000")
    assert report.reason_code_counts[0].row_ratio == d("0.666667")


def test_empty_digest_and_payload_are_report_only_readonly_decimal_stringed() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_fx_options_risk_reversal_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_skew_count == d("0.000000")
    assert report.max_stress_score == d("0.000000")
    assert report.average_stress_score == d("0.000000")
    assert report.digest_status == "blocked"
    assert report.reason_codes == ("fx_options_risk_reversal_digest_empty",)
    assert report.reason_code_counts == (
        module.FXOptionsRiskReversalReasonCodeCount(
            reason_code="fx_options_risk_reversal_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_decimal_payload(payload)


def test_rejects_bad_public_types_datetimes_duplicates_future_rows_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="current_risk_reversal_bps"):
        observation(current_risk_reversal_bps=_DecimalSubclass("60.000000"))

    with pytest.raises(ValueError, match="option_liquidity_stress_ratio"):
        observation(option_liquidity_stress_ratio=d("1.100000"))

    with pytest.raises(ValueError, match="watch_risk_reversal_shift_bps"):
        config(watch_risk_reversal_shift_bps=25)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="duplicate source_id"):
        digest((observation("dupe"), observation("dupe")))

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    report = digest((observation(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.FXOptionsRiskReversalDigestConfig,
        module.FXOptionsRiskReversalObservation,
        module.FXOptionsRiskReversalDigestRow,
        module.FXOptionsRiskReversalReasonCodeCount,
        module.FXOptionsRiskReversalDigestReport,
    )
    for type_ in classes:
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type


def test_module_scope_is_pure_in_memory_without_live_or_durable_surfaces() -> None:
    module = api()
    source = inspect.getsource(module).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "open(",
        "path(",
        "connect(",
        "cursor(",
        "execute(",
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
        "exchange",
    ):
        assert forbidden not in source

    tree = ast.parse(
        Path(
            "src/polymarket_alpha_lab/market_research_fx_options_risk_reversal_digest.py",
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
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    report = digest((observation(),))
    assert is_dataclass(report)

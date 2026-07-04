from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 14, 0, tzinfo=UTC)
PREFIX = "market_research_gold_real_yield_breakout_digest_"
SIX_DECIMAL = re.compile(r"^-?[0-9]+\.[0-9]{6}$")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_gold_real_yield_breakout_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_BREAKOUT_DIGEST_CONFIG_VERSION
        ),
        "fresh_input_max_age_seconds": d("21600.000000"),
        "watch_real_yield_change_bp_threshold": d("8.000000"),
        "blocked_real_yield_change_bp_threshold": d("15.000000"),
        "watch_usd_index_change_pct_threshold": d("0.005000"),
        "blocked_usd_index_change_pct_threshold": d("0.010000"),
        "watch_probability_delta_threshold": d("0.040000"),
        "blocked_probability_delta_threshold": d("0.080000"),
        "min_source_count": d("2.000000"),
        "min_event_liquidity_usd": d("100.000000"),
    }
    values.update(overrides)
    return module.MarketResearchGoldRealYieldBreakoutDigestConfig(**values)


def input_row(
    research_id: str = "gold-real-yield-base",
    *,
    condition_id: str = "condition_gold_real_yield_base",
    event_slug: str = "gold-above-2500-this-month",
    commodity_symbol: str = "XAU",
    observed_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    event_liquidity_usd: Decimal = d("1250.000000"),
    real_yield_level_pct: Decimal = d("1.750000"),
    real_yield_change_bp: Decimal = d("3.000000"),
    usd_index_change_pct: Decimal = d("0.002000"),
    gold_spot_change_pct: Decimal = d("0.006000"),
    event_probability_before: Decimal = d("0.460000"),
    event_probability_after: Decimal = d("0.480000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchGoldRealYieldBreakoutInputRow(
        research_id=research_id,
        condition_id=condition_id,
        event_slug=event_slug,
        commodity_symbol=commodity_symbol,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        source_count=source_count,
        event_liquidity_usd=event_liquidity_usd,
        real_yield_level_pct=real_yield_level_pct,
        real_yield_change_bp=real_yield_change_bp,
        usd_index_change_pct=usd_index_change_pct,
        gold_spot_change_pct=gold_spot_change_pct,
        event_probability_before=event_probability_before,
        event_probability_after=event_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest_report(
    *rows: object,
    generated_at: datetime = GENERATED_AT,
    cfg: object | None = None,
) -> Any:
    module = api()
    return module.build_market_research_gold_real_yield_breakout_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def assert_payload_decimal_strings(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_decimal_strings(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_payload_decimal_strings(item)
        return
    assert not isinstance(value, (Decimal, datetime, float))
    if isinstance(value, str) and re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value):
        assert SIX_DECIMAL.fullmatch(value), value


def test_gold_real_yield_breakout_digest_scores_pressure_and_sorts_rows() -> None:
    module = api()
    blocked = input_row(
        "gold-real-yield-blocked",
        condition_id="condition_gold_real_yield_blocked",
        event_slug="gold-above-2600-this-month",
        observed_at=GENERATED_AT - timedelta(hours=7),
        source_count=d("1.000000"),
        event_liquidity_usd=d("50.000000"),
        real_yield_level_pct=d("1.950000"),
        real_yield_change_bp=d("18.000000"),
        usd_index_change_pct=d("0.013000"),
        gold_spot_change_pct=d("-0.018000"),
        event_probability_before=d("0.570000"),
        event_probability_after=d("0.450000"),
    )
    watched = input_row(
        "gold-real-yield-watch",
        condition_id="condition_gold_real_yield_watch",
        event_slug="gold-above-2550-this-week",
        observed_at=datetime(2026, 7, 4, 9, 0, tzinfo=timezone(timedelta(hours=-4))),
        real_yield_level_pct=d("1.600000"),
        real_yield_change_bp=d("-9.000000"),
        usd_index_change_pct=d("-0.006000"),
        gold_spot_change_pct=d("0.014000"),
        event_probability_before=d("0.390000"),
        event_probability_after=d("0.420000"),
    )
    passed = input_row(
        "gold-real-yield-pass",
        condition_id="condition_gold_real_yield_pass",
        event_slug="gold-above-2450-this-week",
    )

    report = digest_report(passed, watched, blocked)

    assert isinstance(report, module.MarketResearchGoldRealYieldBreakoutDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_gold_real_yield_breakout_screening"
    )
    assert report.input_count == d("3.000000")
    assert report.blocked_input_count == d("1.000000")
    assert report.watch_input_count == d("1.000000")
    assert report.pass_input_count == d("1.000000")
    assert report.real_yield_breakout_count == d("2.000000")
    assert report.usd_breakout_count == d("2.000000")
    assert report.combined_pressure_count == d("2.000000")
    assert report.probability_repricing_count == d("1.000000")
    assert report.stale_input_count == d("1.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.thin_liquidity_count == d("1.000000")
    assert report.average_pressure_score == d("0.555556")
    assert report.max_pressure_score == d("1.000000")
    assert report.max_input_age_seconds == d("25200.000000")
    assert report.blocked_input_ratio == d("0.333333")
    assert report.reason_codes == (
        f"{PREFIX}real_yield_breakout_pressure",
        f"{PREFIX}usd_breakout_pressure",
        f"{PREFIX}combined_real_yield_usd_pressure",
        f"{PREFIX}probability_repricing",
        f"{PREFIX}stale_input",
        f"{PREFIX}thin_sources",
        f"{PREFIX}thin_liquidity",
    )
    assert report.reason_code_counts[0].reason_code == (
        f"{PREFIX}real_yield_breakout_pressure"
    )
    assert report.reason_code_counts[0].count == d("2.000000")
    assert report.reason_code_counts[0].input_ratio == d("0.666667")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.research_id for row in report.rows) == (
        "gold-real-yield-blocked",
        "gold-real-yield-watch",
        "gold-real-yield-pass",
    )
    blocked_row, watch_row, pass_row = report.rows
    assert blocked_row.screening_status == "blocked"
    assert blocked_row.input_age_seconds == d("25200.000000")
    assert blocked_row.pressure_score == d("1.000000")
    assert blocked_row.probability_delta == d("-0.120000")
    assert blocked_row.pressure_direction == "bearish_gold"
    assert blocked_row.reason_codes == (
        f"{PREFIX}real_yield_breakout_pressure",
        f"{PREFIX}usd_breakout_pressure",
        f"{PREFIX}combined_real_yield_usd_pressure",
        f"{PREFIX}probability_repricing",
        f"{PREFIX}stale_input",
        f"{PREFIX}thin_sources",
        f"{PREFIX}thin_liquidity",
    )
    assert watch_row.screening_status == "watch"
    assert watch_row.observed_at == datetime(2026, 7, 4, 13, 0, tzinfo=UTC)
    assert watch_row.pressure_direction == "bullish_gold"
    assert watch_row.reason_codes == (
        f"{PREFIX}real_yield_breakout_pressure",
        f"{PREFIX}usd_breakout_pressure",
        f"{PREFIX}combined_real_yield_usd_pressure",
    )
    assert pass_row.screening_status == "pass"
    assert pass_row.reason_codes == (f"{PREFIX}pass",)


def test_empty_digest_is_report_only_blocked_and_decimal_serialized() -> None:
    module = api()

    report = digest_report(
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_gold_real_yield_breakout_screening"
    )
    assert report.input_count == d("0.000000")
    assert report.average_pressure_score == d("0.000000")
    assert report.max_pressure_score == d("0.000000")
    assert report.max_input_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (f"{PREFIX}no_inputs",)
    assert report.reason_code_counts == (
        module.MarketResearchGoldRealYieldBreakoutReasonCodeCount(
            reason_code=f"{PREFIX}no_inputs",
            count=d("1.000000"),
            input_ratio=d("0.000000"),
        ),
    )

    payload = module.market_research_gold_real_yield_breakout_digest_payload(report)
    json.dumps(payload, sort_keys=True)
    assert payload["input_count"] == "0.000000"
    assert payload["average_pressure_score"] == "0.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_payload_decimal_strings(payload)


def test_determinism_ignores_input_order_and_sorts_reason_counts() -> None:
    stale = input_row(
        "gold-real-yield-stale",
        condition_id="condition_gold_real_yield_stale",
        event_slug="gold-above-2700-next-month",
        observed_at=GENERATED_AT - timedelta(hours=8),
        real_yield_change_bp=d("2.000000"),
        usd_index_change_pct=d("0.001000"),
    )
    usd = input_row(
        "gold-real-yield-usd",
        condition_id="condition_gold_real_yield_usd",
        event_slug="gold-above-2400-today",
        usd_index_change_pct=d("-0.006000"),
    )
    real_yield = input_row(
        "gold-real-yield-real",
        condition_id="condition_gold_real_yield_real",
        event_slug="gold-above-2500-tomorrow",
        real_yield_change_bp=d("9.000000"),
    )

    first = digest_report(stale, usd, real_yield)
    second = digest_report(real_yield, stale, usd)

    assert first == second
    assert tuple(row.research_id for row in first.rows) == (
        "gold-real-yield-stale",
        "gold-real-yield-real",
        "gold-real-yield-usd",
    )
    assert first.reason_codes == (
        f"{PREFIX}real_yield_breakout_pressure",
        f"{PREFIX}usd_breakout_pressure",
        f"{PREFIX}stale_input",
    )
    assert tuple(item.reason_code for item in first.reason_code_counts) == (
        f"{PREFIX}real_yield_breakout_pressure",
        f"{PREFIX}usd_breakout_pressure",
        f"{PREFIX}stale_input",
    )


def test_validates_exact_types_flags_duplicates_staleness_and_freezing() -> None:
    module = api()

    assert module.MarketResearchGoldRealYieldBreakoutDigestConfig.__dataclass_params__.frozen
    assert module.MarketResearchGoldRealYieldBreakoutInputRow.__dataclass_params__.frozen
    assert module.MarketResearchGoldRealYieldBreakoutDigestRow.__dataclass_params__.frozen
    assert (
        module.MarketResearchGoldRealYieldBreakoutReasonCodeCount.__dataclass_params__.frozen
    )
    assert module.MarketResearchGoldRealYieldBreakoutDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="real_yield_change_bp must be a Decimal"):
        input_row(real_yield_change_bp=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_gold_real_yield_breakout_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest_report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="inputs must not contain duplicate research_id"):
        digest_report(
            input_row("gold-real-yield-dupe"),
            input_row(
                "gold-real-yield-dupe",
                condition_id="condition_gold_real_yield_dupe_two",
            ),
        )
    with pytest.raises(ValueError, match="inputs must not contain duplicate condition_id"):
        digest_report(
            input_row("gold-real-yield-one", condition_id="condition_gold_real_yield_same"),
            input_row("gold-real-yield-two", condition_id="condition_gold_real_yield_same"),
        )
    with pytest.raises(ValueError, match="config paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="input row report_only must be True"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report(input_row()).rows[0], readonly=False)

    row = input_row("gold-real-yield-frozen")
    with pytest.raises(FrozenInstanceError):
        row.real_yield_change_bp = d("5.000000")  # type: ignore[misc]


def test_payload_public_numerics_hard_flags_and_source_have_no_mutation_surfaces() -> None:
    module = api()
    report = digest_report(input_row("gold-real-yield-payload"))
    payload = module.market_research_gold_real_yield_breakout_digest_payload(report)

    assert_payload_decimal_strings(payload)
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in walk_values(payload))
    assert payload == module.market_research_gold_real_yield_breakout_digest_payload(report)
    assert payload["rows"][0]["real_yield_change_bp"] == "3.000000"
    assert payload["rows"][0]["event_probability_after"] == "0.480000"

    for value in (
        config(),
        input_row("gold-real-yield-decimal"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if _is_public_numeric_field(field.name):
                assert type(getattr(value, field.name)) is Decimal, field.name

    source_path = Path(
        "src/polymarket_alpha_lab/"
        "market_research_gold_real_yield_breakout_digest.py",
    )
    source = source_path.read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                called_names.add(func.id)
            elif isinstance(func, ast.Attribute):
                called_names.add(func.attr)

    forbidden_import_fragments = (
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sql",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert called_names.isdisjoint({"open", "connect", "request", "urlopen"})

    forbidden_source_terms = (
        "live trading",
        "wallet",
        "auth",
        "keys",
        "submit_order",
        "cancel",
        "replace",
        "exchange",
        "subprocess",
        "socket",
        "http",
        "psycopg",
        "supabase",
        "secret",
        "token",
        "private",
    )
    lowered_source = source.lower()
    assert not any(term in lowered_source for term in forbidden_source_terms)


def _is_public_numeric_field(field_name: str) -> bool:
    return field_name.endswith(
        (
            "_count",
            "_ratio",
            "_pct",
            "_bp",
            "_usd",
            "_seconds",
            "_score",
        ),
    )

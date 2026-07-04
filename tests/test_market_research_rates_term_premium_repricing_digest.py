from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_rates_term_premium_repricing_digest import (
    DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_REPRICING_DIGEST_CONFIG_VERSION,
    MarketResearchRatesTermPremiumRepricingDigestConfig,
    MarketResearchRatesTermPremiumRepricingDigestReport,
    MarketResearchRatesTermPremiumRepricingDigestRow,
    MarketResearchRatesTermPremiumRepricingInput,
    MarketResearchRatesTermPremiumRepricingReasonCodeCount,
    build_market_research_rates_term_premium_repricing_digest,
    market_research_rates_term_premium_repricing_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_rates_term_premium_repricing_digest.py"
)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def _config(
    **overrides: object,
) -> MarketResearchRatesTermPremiumRepricingDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_REPRICING_DIGEST_CONFIG_VERSION
        ),
        "watch_term_premium_delta_bps": Decimal("10.000000"),
        "blocked_term_premium_delta_bps": Decimal("25.000000"),
        "watch_real_yield_shift_bps": Decimal("8.000000"),
        "watch_inflation_breakeven_shift_bps": Decimal("6.000000"),
        "watch_auction_supply_pressure": Decimal("0.600000"),
        "watch_vol_breakout": Decimal("0.550000"),
        "source_freshness_watch_threshold": Decimal("0.700000"),
        "source_quorum_watch_threshold": Decimal("0.650000"),
        "risk_score_watch_threshold": Decimal("0.500000"),
        "risk_score_blocked_threshold": Decimal("0.800000"),
    }
    values.update(overrides)
    return MarketResearchRatesTermPremiumRepricingDigestConfig(**values)


def _input(
    market_slug: str = "fed-10y-yield-above-4-5-july",
    tenor_bucket: str = "10y",
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=20),
    term_premium_delta_bps: Decimal = Decimal("5.000000"),
    real_yield_shift_bps: Decimal = Decimal("3.000000"),
    inflation_breakeven_shift_bps: Decimal = Decimal("2.000000"),
    auction_supply_pressure: Decimal = Decimal("0.200000"),
    vol_breakout_score: Decimal = Decimal("0.100000"),
    source_freshness_ratio: Decimal = Decimal("0.900000"),
    source_quorum_ratio: Decimal = Decimal("0.900000"),
    upstream_reason_codes: tuple[str, ...] = ("source_quorum_passed",),
    source_config_version: str = "rates-term-premium-source-v0",
) -> MarketResearchRatesTermPremiumRepricingInput:
    return MarketResearchRatesTermPremiumRepricingInput(
        market_slug=market_slug,
        tenor_bucket=tenor_bucket,
        observed_at=observed_at,
        term_premium_delta_bps=term_premium_delta_bps,
        real_yield_shift_bps=real_yield_shift_bps,
        inflation_breakeven_shift_bps=inflation_breakeven_shift_bps,
        auction_supply_pressure=auction_supply_pressure,
        vol_breakout_score=vol_breakout_score,
        source_freshness_ratio=source_freshness_ratio,
        source_quorum_ratio=source_quorum_ratio,
        upstream_reason_codes=upstream_reason_codes,
        source_config_version=source_config_version,
    )


def _assert_no_float(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float found in JSON payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_float(item)


def test_digest_detects_term_premium_repricing_and_sorts_deterministically() -> None:
    report = build_market_research_rates_term_premium_repricing_digest(
        (
            _input(
                "rates-pass",
                "2y",
                observed_at=GENERATED_AT - timedelta(minutes=5),
            ),
            _input(
                "rates-blocked",
                "30y",
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    45,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                term_premium_delta_bps=Decimal("30.000000"),
                real_yield_shift_bps=Decimal("12.000000"),
                inflation_breakeven_shift_bps=Decimal("7.000000"),
                auction_supply_pressure=Decimal("0.800000"),
                vol_breakout_score=Decimal("0.700000"),
                source_freshness_ratio=Decimal("0.600000"),
                source_quorum_ratio=Decimal("0.500000"),
                upstream_reason_codes=(
                    "auction_tail_watch",
                    "rates_volatility_breakout_low_quorum",
                ),
            ),
            _input(
                "rates-watch",
                "10y",
                observed_at=GENERATED_AT - timedelta(minutes=15),
                term_premium_delta_bps=Decimal("-12.000000"),
                real_yield_shift_bps=Decimal("-9.000000"),
                inflation_breakeven_shift_bps=Decimal("1.000000"),
                auction_supply_pressure=Decimal("0.100000"),
                vol_breakout_score=Decimal("0.200000"),
                source_freshness_ratio=Decimal("0.720000"),
                source_quorum_ratio=Decimal("0.680000"),
                upstream_reason_codes=("real_yield_breakout",),
                source_config_version="rates-term-premium-source-v1",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketResearchRatesTermPremiumRepricingDigestReport)
    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_REPRICING_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "review_rates_term_premium_repricing_digest"
    assert report.market_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.blocked_count == Decimal("1.000000")
    assert report.term_premium_repricing_count == Decimal("2.000000")
    assert report.real_yield_shift_count == Decimal("2.000000")
    assert report.inflation_breakeven_shift_count == Decimal("1.000000")
    assert report.auction_supply_pressure_count == Decimal("1.000000")
    assert report.vol_breakout_count == Decimal("1.000000")
    assert report.source_freshness_risk_count == Decimal("1.000000")
    assert report.source_quorum_risk_count == Decimal("1.000000")
    assert report.max_risk_score == Decimal("1.000000")
    assert report.average_risk_score == Decimal("0.493333")
    assert report.reason_codes == (
        "rates_term_premium_repricing_auction_supply_pressure",
        "rates_term_premium_repricing_blocked_score",
        "rates_term_premium_repricing_inflation_breakeven_shift",
        "rates_term_premium_repricing_real_yield_shift",
        "rates_term_premium_repricing_source_freshness_risk",
        "rates_term_premium_repricing_source_quorum_risk",
        "rates_term_premium_repricing_term_premium_delta",
        "rates_term_premium_repricing_vol_breakout",
        "rates_term_premium_repricing_watch_score",
    )
    assert report.reason_code_counts == (
        MarketResearchRatesTermPremiumRepricingReasonCodeCount(
            reason_code="rates_term_premium_repricing_auction_supply_pressure",
            market_count=Decimal("1.000000"),
        ),
        MarketResearchRatesTermPremiumRepricingReasonCodeCount(
            reason_code="rates_term_premium_repricing_blocked_score",
            market_count=Decimal("1.000000"),
        ),
        MarketResearchRatesTermPremiumRepricingReasonCodeCount(
            reason_code="rates_term_premium_repricing_inflation_breakeven_shift",
            market_count=Decimal("1.000000"),
        ),
        MarketResearchRatesTermPremiumRepricingReasonCodeCount(
            reason_code="rates_term_premium_repricing_real_yield_shift",
            market_count=Decimal("2.000000"),
        ),
        MarketResearchRatesTermPremiumRepricingReasonCodeCount(
            reason_code="rates_term_premium_repricing_source_freshness_risk",
            market_count=Decimal("1.000000"),
        ),
        MarketResearchRatesTermPremiumRepricingReasonCodeCount(
            reason_code="rates_term_premium_repricing_source_quorum_risk",
            market_count=Decimal("1.000000"),
        ),
        MarketResearchRatesTermPremiumRepricingReasonCodeCount(
            reason_code="rates_term_premium_repricing_term_premium_delta",
            market_count=Decimal("2.000000"),
        ),
        MarketResearchRatesTermPremiumRepricingReasonCodeCount(
            reason_code="rates_term_premium_repricing_vol_breakout",
            market_count=Decimal("1.000000"),
        ),
        MarketResearchRatesTermPremiumRepricingReasonCodeCount(
            reason_code="rates_term_premium_repricing_watch_score",
            market_count=Decimal("1.000000"),
        ),
    )
    assert report.rows == (
        MarketResearchRatesTermPremiumRepricingDigestRow(
            market_slug="rates-blocked",
            tenor_bucket="30y",
            observed_at=datetime(2026, 7, 4, 11, 45, tzinfo=UTC),
            term_premium_delta_bps=Decimal("30.000000"),
            term_premium_delta_abs_bps=Decimal("30.000000"),
            real_yield_shift_bps=Decimal("12.000000"),
            real_yield_shift_abs_bps=Decimal("12.000000"),
            inflation_breakeven_shift_bps=Decimal("7.000000"),
            inflation_breakeven_shift_abs_bps=Decimal("7.000000"),
            auction_supply_pressure=Decimal("0.800000"),
            vol_breakout_score=Decimal("0.700000"),
            source_freshness_ratio=Decimal("0.600000"),
            source_quorum_ratio=Decimal("0.500000"),
            risk_score=Decimal("1.000000"),
            digest_status="blocked",
            source_config_version="rates-term-premium-source-v0",
            upstream_reason_codes=(
                "auction_tail_watch",
                "rates_volatility_breakout_low_quorum",
            ),
            reason_codes=(
                "rates_term_premium_repricing_auction_supply_pressure",
                "rates_term_premium_repricing_blocked_score",
                "rates_term_premium_repricing_inflation_breakeven_shift",
                "rates_term_premium_repricing_real_yield_shift",
                "rates_term_premium_repricing_source_freshness_risk",
                "rates_term_premium_repricing_source_quorum_risk",
                "rates_term_premium_repricing_term_premium_delta",
                "rates_term_premium_repricing_vol_breakout",
            ),
        ),
        MarketResearchRatesTermPremiumRepricingDigestRow(
            market_slug="rates-watch",
            tenor_bucket="10y",
            observed_at=GENERATED_AT - timedelta(minutes=15),
            term_premium_delta_bps=Decimal("-12.000000"),
            term_premium_delta_abs_bps=Decimal("12.000000"),
            real_yield_shift_bps=Decimal("-9.000000"),
            real_yield_shift_abs_bps=Decimal("9.000000"),
            inflation_breakeven_shift_bps=Decimal("1.000000"),
            inflation_breakeven_shift_abs_bps=Decimal("1.000000"),
            auction_supply_pressure=Decimal("0.100000"),
            vol_breakout_score=Decimal("0.200000"),
            source_freshness_ratio=Decimal("0.720000"),
            source_quorum_ratio=Decimal("0.680000"),
            risk_score=Decimal("0.480000"),
            digest_status="watch",
            source_config_version="rates-term-premium-source-v1",
            upstream_reason_codes=("real_yield_breakout",),
            reason_codes=(
                "rates_term_premium_repricing_real_yield_shift",
                "rates_term_premium_repricing_term_premium_delta",
                "rates_term_premium_repricing_watch_score",
            ),
        ),
        MarketResearchRatesTermPremiumRepricingDigestRow(
            market_slug="rates-pass",
            tenor_bucket="2y",
            observed_at=GENERATED_AT - timedelta(minutes=5),
            term_premium_delta_bps=Decimal("5.000000"),
            term_premium_delta_abs_bps=Decimal("5.000000"),
            real_yield_shift_bps=Decimal("3.000000"),
            real_yield_shift_abs_bps=Decimal("3.000000"),
            inflation_breakeven_shift_bps=Decimal("2.000000"),
            inflation_breakeven_shift_abs_bps=Decimal("2.000000"),
            auction_supply_pressure=Decimal("0.200000"),
            vol_breakout_score=Decimal("0.100000"),
            source_freshness_ratio=Decimal("0.900000"),
            source_quorum_ratio=Decimal("0.900000"),
            risk_score=Decimal("0.000000"),
            digest_status="pass",
            source_config_version="rates-term-premium-source-v0",
            upstream_reason_codes=("source_quorum_passed",),
            reason_codes=("rates_term_premium_repricing_passed",),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    serialized = repr(asdict(report)).lower()
    assert "wallet" not in serialized
    assert "order" not in serialized
    assert "cancel" not in serialized
    assert "exchange_mutation" not in serialized


def test_empty_inputs_pass_with_decimal_zeroes_and_digest_reason() -> None:
    report = build_market_research_rates_term_premium_repricing_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "pass"
    assert report.recommended_next_step == "continue_rates_term_premium_monitoring"
    assert report.market_count == Decimal("0.000000")
    assert report.pass_count == Decimal("0.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.blocked_count == Decimal("0.000000")
    assert report.term_premium_repricing_count == Decimal("0.000000")
    assert report.max_risk_score is None
    assert report.average_risk_score is None
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.reason_codes == ("rates_term_premium_repricing_digest_empty",)


def test_payload_uses_six_decimal_strings_and_no_float_values() -> None:
    report = build_market_research_rates_term_premium_repricing_digest(
        (
            _input(
                "rates-blocked",
                "30y",
                term_premium_delta_bps=Decimal("30"),
                real_yield_shift_bps=Decimal("12"),
                inflation_breakeven_shift_bps=Decimal("7"),
                auction_supply_pressure=Decimal("0.8"),
                vol_breakout_score=Decimal("0.7"),
                source_freshness_ratio=Decimal("0.6"),
                source_quorum_ratio=Decimal("0.5"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = market_research_rates_term_premium_repricing_digest_payload(report)

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["max_risk_score"] == "1.000000"
    assert payload["average_risk_score"] == "1.000000"
    assert payload["rows"][0]["term_premium_delta_bps"] == "30.000000"
    assert payload["rows"][0]["auction_supply_pressure"] == "0.800000"
    assert payload["reason_code_counts"][0]["market_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    _assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_and_public_numerics_are_exact_decimals() -> None:
    input_row = _input()
    report = build_market_research_rates_term_premium_repricing_digest(
        (
            input_row,
            _input(
                "rates-watch",
                "10y",
                term_premium_delta_bps=Decimal("12.000000"),
                real_yield_shift_bps=Decimal("9.000000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        input_row.market_slug = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].risk_score = Decimal("0.1")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.reason_code_counts[0].market_count = Decimal("9")  # type: ignore[misc]

    numeric_suffixes = (
        "_bps",
        "_score",
        "_pressure",
        "_ratio",
        "_count",
    )
    for value in (report, *report.rows, *report.reason_code_counts):
        for field in fields(value):
            if field.name.endswith(numeric_suffixes):
                public_value = getattr(value, field.name)
                assert public_value is None or type(public_value) is Decimal


def test_rejects_bad_types_naive_datetimes_and_false_hard_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        _config(
            config_version=_StringSubclass(
                DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_REPRICING_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="term_premium_delta_bps"):
        _input(term_premium_delta_bps=_DecimalSubclass("1.0"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_rates_term_premium_repricing_digest(
            (),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="inputs must contain"):
        build_market_research_rates_term_premium_repricing_digest(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_input(), paper_only=False)
    with pytest.raises(ValueError, match="source_quorum_ratio"):
        _input(source_quorum_ratio=Decimal("1.1"))
    with pytest.raises(ValueError, match="upstream_reason_codes"):
        _input(upstream_reason_codes=())
    with pytest.raises(ValueError, match="upstream_reason_codes"):
        _input(upstream_reason_codes=("good_reason", "good_reason"))


def test_module_import_has_no_forbidden_side_effect_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(forbidden_import_roots)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots

    source = MODULE_PATH.read_text().lower()
    forbidden_fragments = (
        "getenv",
        "environ",
        "open(",
        "read_text",
        "write_text",
        "urlopen",
        "request(",
        "connect(",
        "execute(",
        "order(",
        "cancel(",
        "replace_order",
        "wallet",
        "private_key",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_rejects_subclasses_and_noncanonical_manual_report_shapes() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_rates_term_premium_repricing_digest",
    )

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "InputSubclass",
            (MarketResearchRatesTermPremiumRepricingInput,),
            {},
        )

    good_report = build_market_research_rates_term_premium_repricing_digest(
        (
            _input("rates-pass", "2y"),
            _input(
                "rates-watch",
                "10y",
                term_premium_delta_bps=Decimal("12.000000"),
                real_yield_shift_bps=Decimal("9.000000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        module.MarketResearchRatesTermPremiumRepricingDigestReport(
            generated_at=good_report.generated_at,
            config_version=good_report.config_version,
            digest_status=good_report.digest_status,
            recommended_next_step=good_report.recommended_next_step,
            market_count=good_report.market_count,
            pass_count=good_report.pass_count,
            watch_count=good_report.watch_count,
            blocked_count=good_report.blocked_count,
            term_premium_repricing_count=good_report.term_premium_repricing_count,
            real_yield_shift_count=good_report.real_yield_shift_count,
            inflation_breakeven_shift_count=good_report.inflation_breakeven_shift_count,
            auction_supply_pressure_count=good_report.auction_supply_pressure_count,
            vol_breakout_count=good_report.vol_breakout_count,
            source_freshness_risk_count=good_report.source_freshness_risk_count,
            source_quorum_risk_count=good_report.source_quorum_risk_count,
            max_risk_score=good_report.max_risk_score,
            average_risk_score=good_report.average_risk_score,
            rows=tuple(reversed(good_report.rows)),
            reason_code_counts=good_report.reason_code_counts,
            reason_codes=good_report.reason_codes,
        )

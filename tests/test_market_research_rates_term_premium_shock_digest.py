from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_rates_term_premium_shock_digest import (
    DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_SHOCK_DIGEST_CONFIG_VERSION,
    MarketResearchRatesTermPremiumShockDigestConfig,
    MarketResearchRatesTermPremiumShockDigestInputRow,
    MarketResearchRatesTermPremiumShockDigestReport,
    build_market_research_rates_term_premium_shock_digest,
    market_research_rates_term_premium_shock_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
PREFIX = "market_research_rates_term_premium_shock_digest_"


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchRatesTermPremiumShockDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_SHOCK_DIGEST_CONFIG_VERSION
        ),
        "fresh_observation_max_age_seconds": d("86400.000000"),
        "term_premium_change_bp_threshold": d("15.000000"),
        "long_end_yield_change_bp_threshold": d("20.000000"),
        "curve_steepening_bp_threshold": d("12.000000"),
        "auction_tail_bp_threshold": d("3.000000"),
        "probability_repricing_threshold": d("0.080000"),
        "min_source_count": d("2.000000"),
        "min_liquidity_usd": d("100.000000"),
    }
    values.update(overrides)
    return MarketResearchRatesTermPremiumShockDigestConfig(**values)


def input_row(
    research_key: str = "rates.term-premium.base",
    *,
    condition_id: str = "condition_rates_term_premium_base",
    market_slug: str = "will-10y-yields-rise-this-week",
    evidence_reference: str = "public-rates-source",
    observed_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    market_liquidity_usd: Decimal = d("1000.000000"),
    term_premium_change_bp: Decimal = d("5.000000"),
    ten_year_yield_change_bp: Decimal = d("4.000000"),
    thirty_year_yield_change_bp: Decimal = d("6.000000"),
    curve_steepening_bp: Decimal = d("3.000000"),
    auction_tail_bp: Decimal = d("0.500000"),
    market_probability_before: Decimal = d("0.480000"),
    market_probability_after: Decimal = d("0.520000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchRatesTermPremiumShockDigestInputRow:
    return MarketResearchRatesTermPremiumShockDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        market_slug=market_slug,
        evidence_reference=evidence_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
        source_count=source_count,
        market_liquidity_usd=market_liquidity_usd,
        term_premium_change_bp=term_premium_change_bp,
        ten_year_yield_change_bp=ten_year_yield_change_bp,
        thirty_year_yield_change_bp=thirty_year_yield_change_bp,
        curve_steepening_bp=curve_steepening_bp,
        auction_tail_bp=auction_tail_bp,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_empty_digest_is_blocked_report_only_and_decimal_clean() -> None:
    report = build_market_research_rates_term_premium_shock_digest(
        (),
        config=config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, MarketResearchRatesTermPremiumShockDigestReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert (
        report.recommended_next_step
        == "block_report_only_rates_term_premium_shock_screening"
    )
    assert report.candidate_count == d("0.000000")
    assert report.high_risk_candidate_count == d("0.000000")
    assert report.average_shock_score == d("0.000000")
    assert report.max_shock_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (f"{PREFIX}no_inputs",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.candidate_count = d("1.000000")  # type: ignore[misc]

    payload = market_research_rates_term_premium_shock_digest_payload(report)
    json.dumps(payload, sort_keys=True)
    assert payload == market_research_rates_term_premium_shock_digest_payload(report)
    assert payload["candidate_count"] == "0.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))


def test_high_risk_term_premium_shock_candidates_are_ranked_and_redacted() -> None:
    high_risk = input_row(
        "rates.term-premium.shock",
        condition_id="condition_rates_shock",
        market_slug="will-fed-emergency-cut-by-september",
        evidence_reference="https://rates.example/research?token=secret-abc",
        term_premium_change_bp=d("25.000000"),
        ten_year_yield_change_bp=d("23.000000"),
        thirty_year_yield_change_bp=d("26.000000"),
        curve_steepening_bp=d("16.000000"),
        auction_tail_bp=d("3.500000"),
        market_probability_before=d("0.420000"),
        market_probability_after=d("0.550000"),
    )
    stable = input_row(
        "rates.term-premium.stable",
        condition_id="condition_rates_stable",
        market_slug="will-10y-yields-fall-this-week",
    )

    report = build_market_research_rates_term_premium_shock_digest(
        (stable, high_risk),
        config=config(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "watch"
    assert (
        report.recommended_next_step
        == "review_report_only_rates_term_premium_shock_candidates"
    )
    assert report.candidate_count == d("2.000000")
    assert report.high_risk_candidate_count == d("1.000000")
    assert report.ready_candidate_count == d("1.000000")
    assert report.term_premium_shock_count == d("1.000000")
    assert report.long_end_yield_shock_count == d("1.000000")
    assert report.curve_steepener_shock_count == d("1.000000")
    assert report.auction_tail_shock_count == d("1.000000")
    assert report.probability_repricing_count == d("1.000000")
    assert report.average_shock_score == d("0.500000")
    assert report.max_shock_score == d("1.000000")
    assert report.max_term_premium_abs_bp == d("25.000000")
    assert tuple(row.market_slug for row in report.rows) == (
        "will-fed-emergency-cut-by-september",
        "will-10y-yields-fall-this-week",
    )

    row = report.rows[0]
    assert row.screening_status == "watch"
    assert row.long_end_yield_change_abs_bp == d("26.000000")
    assert row.market_probability_delta == d("0.130000")
    assert row.shock_factor_count == d("5.000000")
    assert row.shock_score == d("1.000000")
    assert row.reason_codes == (
        f"{PREFIX}term_premium_shock",
        f"{PREFIX}long_end_yield_shock",
        f"{PREFIX}curve_steepener_shock",
        f"{PREFIX}auction_tail_shock",
        f"{PREFIX}probability_repricing",
    )
    assert row.redacted_evidence_reference.startswith("sha256:")
    assert all(
        type(getattr(row, field_name)) is Decimal
        for field_name in (
            "source_count",
            "market_liquidity_usd",
            "term_premium_change_bp",
            "ten_year_yield_change_bp",
            "thirty_year_yield_change_bp",
            "curve_steepening_bp",
            "auction_tail_bp",
            "market_probability_before",
            "market_probability_after",
            "market_probability_delta",
            "observation_age_seconds",
            "shock_factor_count",
            "shock_score",
        )
    )
    assert all(item.paper_only and item.report_only and item.readonly for item in report.rows)
    assert all(
        item.paper_only and item.report_only and item.readonly
        for item in report.reason_code_counts
    )

    payload = market_research_rates_term_premium_shock_digest_payload(report)
    assert payload["rows"][0]["redacted_evidence_reference"].startswith("sha256:")
    assert "'evidence_reference':" not in repr(payload)
    assert "secret-abc" not in repr(payload).lower()
    assert "token" not in repr(payload).lower()


def test_determinism_ignores_input_order_and_sorts_reason_codes() -> None:
    stale = input_row(
        "rates.term-premium.stale",
        condition_id="condition_rates_stale",
        market_slug="will-30y-yields-rise-this-month",
        observed_at=GENERATED_AT - timedelta(days=2),
        source_count=d("1.000000"),
        market_liquidity_usd=d("50.000000"),
        term_premium_change_bp=d("40.000000"),
    )
    shock = input_row(
        "rates.term-premium.shock",
        condition_id="condition_rates_shock",
        market_slug="will-30y-yields-rise-this-week",
        term_premium_change_bp=d("30.000000"),
        ten_year_yield_change_bp=d("22.000000"),
    )
    ready = input_row(
        "rates.term-premium.ready",
        condition_id="condition_rates_ready",
        market_slug="will-10y-yields-hold-this-week",
    )

    first = build_market_research_rates_term_premium_shock_digest(
        (ready, stale, shock),
        config=config(),
        generated_at=GENERATED_AT,
    )
    second = build_market_research_rates_term_premium_shock_digest(
        (shock, ready, stale),
        config=config(),
        generated_at=GENERATED_AT,
    )

    assert first == second
    assert market_research_rates_term_premium_shock_digest_payload(
        first,
    ) == market_research_rates_term_premium_shock_digest_payload(second)
    assert tuple(row.market_slug for row in first.rows) == (
        "will-30y-yields-rise-this-month",
        "will-30y-yields-rise-this-week",
        "will-10y-yields-hold-this-week",
    )
    assert first.rows[0].reason_codes == (
        f"{PREFIX}term_premium_shock",
        f"{PREFIX}stale_observation",
        f"{PREFIX}thin_sources",
        f"{PREFIX}thin_liquidity",
    )
    assert first.reason_codes == tuple(
        item.reason_code for item in first.reason_code_counts
    )


def test_validation_rejects_bad_inputs_and_unsafe_public_identifiers() -> None:
    class DerivedDateTime(datetime):
        pass

    with pytest.raises(ValueError, match="Decimal"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        config(term_premium_change_bp_threshold=15)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 3, 15, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_rates_term_premium_shock_digest(
            (input_row(),),
            config=config(),
            generated_at=DerivedDateTime(2026, 7, 3, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="after generated_at"):
        build_market_research_rates_term_premium_shock_digest(
            (input_row(observed_at=GENERATED_AT + timedelta(seconds=1)),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        build_market_research_rates_term_premium_shock_digest(
            (input_row(), input_row()),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="public identifier"):
        input_row(research_key="rates.private.term-premium")
    with pytest.raises(ValueError, match="list or tuple"):
        build_market_research_rates_term_premium_shock_digest(
            "not rows",  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_hard_flags_are_enforced_on_config_rows_report_and_payload() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)

    report = build_market_research_rates_term_premium_shock_digest(
        (input_row(),),
        config=config(),
        generated_at=GENERATED_AT,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)

    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_rates_term_premium_shock_digest_payload(unsafe_report)


def test_non_default_thresholds_change_screening_classification() -> None:
    moderate = input_row(
        term_premium_change_bp=d("14.000000"),
        ten_year_yield_change_bp=d("19.000000"),
        thirty_year_yield_change_bp=d("17.000000"),
        curve_steepening_bp=d("11.000000"),
        auction_tail_bp=d("2.900000"),
        market_probability_before=d("0.450000"),
        market_probability_after=d("0.520000"),
    )

    default_report = build_market_research_rates_term_premium_shock_digest(
        (moderate,),
        config=config(),
        generated_at=GENERATED_AT,
    )
    sensitive_report = build_market_research_rates_term_premium_shock_digest(
        (moderate,),
        config=config(
            term_premium_change_bp_threshold=d("10.000000"),
            long_end_yield_change_bp_threshold=d("18.000000"),
            curve_steepening_bp_threshold=d("8.000000"),
            auction_tail_bp_threshold=d("2.000000"),
            probability_repricing_threshold=d("0.050000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert default_report.digest_status == "ready"
    assert default_report.rows[0].reason_codes == (f"{PREFIX}ready",)
    assert sensitive_report.digest_status == "watch"
    assert sensitive_report.high_risk_candidate_count == d("1.000000")
    assert sensitive_report.rows[0].shock_score == d("1.000000")
    assert sensitive_report.rows[0].reason_codes == (
        f"{PREFIX}term_premium_shock",
        f"{PREFIX}long_end_yield_shock",
        f"{PREFIX}curve_steepener_shock",
        f"{PREFIX}auction_tail_shock",
        f"{PREFIX}probability_repricing",
    )


def test_module_has_no_live_or_durable_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_rates_term_premium_shock_digest.py"
    )
    tree = ast.parse(module_path.read_text())
    source = module_path.read_text().lower()

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
        "private_key",
        "sqlite",
        "postgres",
        "redis",
    ):
        assert token not in source

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "subprocess",
        "psycopg",
        "psycopg2",
        "supabase",
        "sqlite3",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
        "replace_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names

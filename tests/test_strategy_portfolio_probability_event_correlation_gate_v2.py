from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_portfolio_probability_event_correlation_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
CLOSE_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_portfolio_probability_event_correlation_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-portfolio-probability-event-correlation-gate-v2-test",
        "close_cluster_window_seconds": d("3600.000000"),
        "correlated_exposure_watch_share": d("0.100000"),
        "correlated_exposure_block_share": d("0.200000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioProbabilityEventCorrelationGateV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "market-alpha",
        "event_slug": "event-alpha",
        "category": "macro",
        "tags": ("rates", "central-bank"),
        "catalyst_id": "fomc-july",
        "source_family": "official-data",
        "market_close_at": CLOSE_AT,
        "liquidity_pool_id": "usdc-pool-alpha",
        "available_liquidity_usdc": d("1000.000000"),
        "candidate_notional": d("50.000000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioProbabilityEventCorrelationGateV2Candidate(**values)


def position(**overrides: object):
    module = api()
    values = {
        "position_id": "position-alpha",
        "market_slug": "market-existing-alpha",
        "event_slug": "event-existing-alpha",
        "category": "macro",
        "tags": ("central-bank", "rate-path"),
        "catalyst_id": "fomc-july",
        "source_family": "official-data",
        "market_close_at": CLOSE_AT + timedelta(minutes=30),
        "liquidity_pool_id": "usdc-pool-alpha",
        "available_liquidity_usdc": d("700.000000"),
        "exposure_notional": d("80.000000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioProbabilityEventCorrelationGateV2Position(**values)


def report(*positions: object, cnd=None, cfg=None, portfolio_nav: Decimal = d("1000.000000")):
    module = api()
    return module.build_strategy_portfolio_probability_event_correlation_gate_v2_report(
        cnd if cnd is not None else candidate(),
        positions,
        config=cfg if cfg is not None else config(),
        portfolio_nav=portfolio_nav,
        generated_at=GENERATED_AT,
    )


def assert_no_float_or_decimal_payload_values(value: Any) -> None:
    if isinstance(value, (float, Decimal)):
        raise AssertionError(f"unexpected non-JSON numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_decimal_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_decimal_payload_values(item)


def test_gate_reports_all_correlation_dimensions_and_exposure_watch() -> None:
    result = report(position())

    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-portfolio-probability-event-correlation-gate-v2-test"
    assert result.candidate_id == "candidate-alpha"
    assert result.candidate_notional == d("50.000000")
    assert result.portfolio_nav == d("1000.000000")
    assert result.position_count == d("1.000000")
    assert result.correlated_position_count == d("1.000000")
    assert result.shared_catalyst_count == d("1.000000")
    assert result.shared_source_family_count == d("1.000000")
    assert result.category_overlap_count == d("1.000000")
    assert result.market_close_cluster_count == d("1.000000")
    assert result.liquidity_overlap_count == d("1.000000")
    assert result.existing_correlated_exposure_notional == d("80.000000")
    assert result.maximum_correlated_exposure_notional == d("130.000000")
    assert result.maximum_correlated_exposure_share == d("0.130000")
    assert result.allowed_candidate_notional == d("50.000000")
    assert result.gate_status == "watch"
    assert result.reason_codes == (
        "shared_catalyst_detected",
        "shared_source_family_detected",
        "category_overlap_detected",
        "market_close_cluster_detected",
        "liquidity_overlap_detected",
        "maximum_correlated_exposure_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    row = result.rows[0]
    assert row.position_id == "position-alpha"
    assert row.exposure_notional == d("80.000000")
    assert row.shared_catalyst is True
    assert row.shared_source_family is True
    assert row.category_overlap is True
    assert row.market_close_clustered is True
    assert row.liquidity_overlap is True
    assert row.close_time_distance_seconds == d("1800.000000")
    assert row.liquidity_overlap_notional == d("700.000000")
    assert row.liquidity_overlap_share == d("0.700000")
    assert row.correlation_dimension_count == d("5.000000")
    assert row.correlated_exposure_notional == d("80.000000")
    assert row.reason_codes == (
        "shared_catalyst",
        "shared_source_family",
        "category_overlap",
        "market_close_cluster",
        "liquidity_overlap",
    )
    assert len(row.derived_validation_digest) == 64


def test_gate_blocks_when_maximum_correlated_exposure_exceeds_cap() -> None:
    result = report(position(exposure_notional=d("180.000000")))

    assert result.existing_correlated_exposure_notional == d("180.000000")
    assert result.maximum_correlated_exposure_notional == d("230.000000")
    assert result.maximum_correlated_exposure_share == d("0.230000")
    assert result.allowed_candidate_notional == d("20.000000")
    assert result.gate_status == "blocked"
    assert result.reason_codes == (
        "shared_catalyst_detected",
        "shared_source_family_detected",
        "category_overlap_detected",
        "market_close_cluster_detected",
        "liquidity_overlap_detected",
        "maximum_correlated_exposure_block",
        "candidate_notional_exceeds_correlated_exposure_cap",
    )


def test_gate_passes_when_existing_positions_are_uncorrelated_and_candidate_is_small() -> None:
    uncorrelated = position(
        category="weather",
        tags=("precipitation",),
        catalyst_id="rainfall-august",
        source_family="weather-station",
        market_close_at=CLOSE_AT + timedelta(days=5),
        liquidity_pool_id="usdc-pool-beta",
        exposure_notional=d("900.000000"),
    )

    result = report(uncorrelated)

    assert result.position_count == d("1.000000")
    assert result.correlated_position_count == d("0.000000")
    assert result.existing_correlated_exposure_notional == d("0.000000")
    assert result.maximum_correlated_exposure_notional == d("50.000000")
    assert result.maximum_correlated_exposure_share == d("0.050000")
    assert result.allowed_candidate_notional == d("50.000000")
    assert result.gate_status == "pass"
    assert result.reason_codes == ("portfolio_probability_event_correlation_pass",)
    assert result.rows[0].correlated_exposure_notional == d("0.000000")
    assert result.rows[0].reason_codes == ("uncorrelated_position",)


def test_no_positions_returns_empty_digest_checked_report() -> None:
    result = report()

    assert result.position_count == d("0.000000")
    assert result.correlated_position_count == d("0.000000")
    assert result.rows == ()
    assert result.maximum_correlated_exposure_notional == d("50.000000")
    assert result.maximum_correlated_exposure_share == d("0.050000")
    assert result.gate_status == "pass"
    assert result.reason_codes == ("portfolio_probability_event_correlation_pass",)
    assert len(result.derived_validation_digest) == 64


def test_payload_is_json_ready_decimal_strings_and_deterministic() -> None:
    module = api()
    first = report(
        position(position_id="position-beta", market_slug="market-existing-beta"),
        position(),
    )
    second = report(
        position(),
        position(position_id="position-beta", market_slug="market-existing-beta"),
    )

    assert tuple(row.position_id for row in first.rows) == (
        "position-alpha",
        "position-beta",
    )
    assert first.derived_validation_digest == second.derived_validation_digest
    assert tuple(row.derived_validation_digest for row in first.rows) == tuple(
        row.derived_validation_digest for row in second.rows
    )

    payload = module.strategy_portfolio_probability_event_correlation_gate_v2_payload(first)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_notional"] == "50.000000"
    assert payload["position_count"] == "2.000000"
    assert payload["maximum_correlated_exposure_share"] == "0.210000"
    assert payload["rows"][0]["close_time_distance_seconds"] == "1800.000000"
    assert payload["rows"][0]["derived_validation_digest"] == first.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_decimal_payload_values(payload)


def test_outputs_are_decimal_only_frozen_flags_are_hard_and_digests_reject_tamper() -> None:
    module = api()
    result = report(position())
    row = result.rows[0]

    for item in fields(result):
        if item.name in {
            "generated_at",
            "config_version",
            "candidate_id",
            "market_slug",
            "event_slug",
            "gate_status",
            "reason_codes",
            "rows",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        }:
            continue
        assert type(getattr(result, item.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        result.gate_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        row.shared_catalyst = False
    with pytest.raises(FrozenInstanceError):
        config().close_cluster_window_seconds = d("10.000000")

    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, shared_catalyst=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, maximum_correlated_exposure_share=d("0.010000"))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_portfolio_probability_event_correlation_gate_v2_payload(object())


def test_validates_decimal_only_inputs_utc_datetimes_thresholds_and_positions() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    converted = report(
        position(market_close_at=datetime(2026, 7, 8, 10, 30, tzinfo=eastern)),
        cnd=candidate(market_close_at=datetime(2026, 7, 8, 10, 0, tzinfo=eastern)),
        cfg=config(close_cluster_window_seconds=d("1800.000000")),
    )
    assert converted.rows[0].close_time_distance_seconds == d("1800.000000")

    with pytest.raises(ValueError, match="correlated_exposure_block_share"):
        config(
            correlated_exposure_watch_share=d("0.300000"),
            correlated_exposure_block_share=d("0.200000"),
        )
    with pytest.raises(ValueError, match="candidate_notional"):
        candidate(candidate_notional=50)
    with pytest.raises(ValueError, match="available_liquidity_usdc"):
        candidate(available_liquidity_usdc=_DecimalSubclass("1000.000000"))
    with pytest.raises(ValueError, match="market_close_at"):
        candidate(market_close_at=_DatetimeSubclass(2026, 7, 8, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(market_close_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="tags"):
        candidate(tags=["rates"])
    with pytest.raises(ValueError, match="portfolio_nav"):
        report(position(), portfolio_nav=d("0.000000"))
    with pytest.raises(ValueError, match="positions"):
        module.build_strategy_portfolio_probability_event_correlation_gate_v2_report(
            candidate(),
            "not-positions",
            config=config(),
            portfolio_nav=d("1000.000000"),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="StrategyPortfolioProbabilityEventCorrelationGateV2Position"):
        module.build_strategy_portfolio_probability_event_correlation_gate_v2_report(
            candidate(),
            (object(),),
            config=config(),
            portfolio_nav=d("1000.000000"),
            generated_at=GENERATED_AT,
        )


def test_module_scope_has_no_io_or_external_execution_surface() -> None:
    tree_source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = tree_source.lower()
    blocked_snippets = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "clob",
        "private_key",
        "secret",
        "subprocess",
        "open(",
        "path(",
        ".write",
        "connect(",
        "execute(",
    )

    assert not any(snippet in lowered_source for snippet in blocked_snippets)

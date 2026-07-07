from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_momentum_noise_filter import (
    MarketMomentumNoiseFilterConfig,
    MarketMomentumObservation,
    MarketMomentumReasonCodeCount,
    MarketMomentumReport,
    MarketMomentumRow,
    build_market_momentum_noise_filter_report,
    market_momentum_noise_filter_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketMomentumNoiseFilterConfig:
    values = {
        "config_version": "research-market-momentum-noise-filter-v0",
        "material_move_bps": d("60"),
        "news_catalyst_score": d("0.700000"),
        "liquidity_depth_floor": d("0.250000"),
        "spread_ceiling_bps": d("250"),
        "order_book_imbalance_ceiling": d("0.800000"),
        "anomaly_score_ceiling": d("0.750000"),
        "min_confidence_score": d("0.600000"),
        "watch_confidence_score": d("0.400000"),
        "noise_score_ceiling": d("0.450000"),
    }
    values.update(overrides)
    return MarketMomentumNoiseFilterConfig(**values)


def observation(**overrides: object) -> MarketMomentumObservation:
    values = {
        "probability_move_bps": d("85"),
        "volume_velocity_ratio": d("1.800000"),
        "liquidity_depth_score": d("0.780000"),
        "bid_ask_spread_bps": d("80"),
        "order_book_imbalance_score": d("0.300000"),
        "news_catalyst_score": d("0.860000"),
        "source_confirmation_score": d("0.820000"),
        "anomaly_score": d("0.180000"),
        "model_disagreement_score": d("0.220000"),
    }
    values.update(overrides)
    return MarketMomentumObservation(**values)


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketMomentumNoiseFilterConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketMomentumReport:
    return build_market_momentum_noise_filter_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_news_confirmed_momentum_passes_with_deterministic_scores() -> None:
    momentum_report = report((observation(),))

    assert type(momentum_report) is MarketMomentumReport
    assert momentum_report.generated_at == GENERATED_AT
    assert momentum_report.config_version == "research-market-momentum-noise-filter-v0"
    assert momentum_report.input_count == d("1")
    assert momentum_report.row_count == d("1")
    assert momentum_report.pass_count == d("1")
    assert momentum_report.watch_count == d("0")
    assert momentum_report.blocked_count == d("0")
    assert momentum_report.news_catalyst_count == d("1")
    assert momentum_report.liquidity_noise_count == d("0")
    assert momentum_report.anomalous_order_book_count == d("0")
    assert momentum_report.low_confidence_volatility_count == d("0")
    assert momentum_report.average_confidence_score == d("0.844000")
    assert momentum_report.status == "pass"
    assert momentum_report.reason_codes == ("news_catalyst_confirmed", "momentum_filter_pass")

    row = momentum_report.rows[0]
    assert type(row) is MarketMomentumRow
    assert row.momentum_score == d("0.782000")
    assert row.noise_score == d("0.238000")
    assert row.confidence_score == d("0.844000")
    assert row.volatility_classification == "news_catalyst"
    assert row.status == "pass"
    assert row.reason_codes == (
        "material_probability_move",
        "news_catalyst_confirmed",
        "source_confirmed",
        "healthy_liquidity",
        "order_book_normal",
        "model_agreement",
        "momentum_filter_pass",
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_liquidity_noise_and_anomalous_order_book_block_report() -> None:
    momentum_report = report(
        (
            observation(
                probability_move_bps=d("95"),
                volume_velocity_ratio=d("2.400000"),
                liquidity_depth_score=d("0.100000"),
                bid_ask_spread_bps=d("350"),
                news_catalyst_score=d("0.100000"),
                source_confirmation_score=d("0.100000"),
                model_disagreement_score=d("0.600000"),
            ),
            observation(
                probability_move_bps=d("70"),
                volume_velocity_ratio=d("1.200000"),
                order_book_imbalance_score=d("0.920000"),
                anomaly_score=d("0.810000"),
                news_catalyst_score=d("0.740000"),
                source_confirmation_score=d("0.700000"),
                model_disagreement_score=d("0.500000"),
            ),
        ),
    )

    assert momentum_report.status == "block"
    assert momentum_report.pass_count == d("0")
    assert momentum_report.watch_count == d("0")
    assert momentum_report.blocked_count == d("2")
    assert momentum_report.liquidity_noise_count == d("1")
    assert momentum_report.anomalous_order_book_count == d("1")
    assert momentum_report.news_catalyst_count == d("0")
    assert momentum_report.reason_code_counts == (
        MarketMomentumReasonCodeCount(
            reason_code="momentum_filter_block",
            count=d("2"),
        ),
        MarketMomentumReasonCodeCount(
            reason_code="wide_spread",
            count=d("1"),
        ),
        MarketMomentumReasonCodeCount(
            reason_code="thin_liquidity",
            count=d("1"),
        ),
        MarketMomentumReasonCodeCount(
            reason_code="weak_or_absent_news_catalyst",
            count=d("1"),
        ),
        MarketMomentumReasonCodeCount(
            reason_code="source_confirmation_low",
            count=d("1"),
        ),
        MarketMomentumReasonCodeCount(
            reason_code="model_disagreement_high",
            count=d("1"),
        ),
        MarketMomentumReasonCodeCount(
            reason_code="order_book_anomaly",
            count=d("1"),
        ),
        MarketMomentumReasonCodeCount(
            reason_code="anomaly_score_high",
            count=d("1"),
        ),
    )
    assert tuple(row.volatility_classification for row in momentum_report.rows) == (
        "liquidity_noise",
        "anomalous_order_book",
    )
    assert tuple(row.status for row in momentum_report.rows) == ("block", "block")


def test_low_confidence_move_returns_watch_without_trading_language() -> None:
    momentum_report = report(
        (
            observation(
                probability_move_bps=d("42"),
                liquidity_depth_score=d("0.500000"),
                bid_ask_spread_bps=d("150"),
                order_book_imbalance_score=d("0.450000"),
                news_catalyst_score=d("0.450000"),
                source_confirmation_score=d("0.500000"),
                anomaly_score=d("0.320000"),
                model_disagreement_score=d("0.450000"),
            ),
        ),
    )

    row = momentum_report.rows[0]
    assert momentum_report.status == "watch"
    assert momentum_report.watch_count == d("1")
    assert momentum_report.low_confidence_volatility_count == d("1")
    assert row.volatility_classification == "low_confidence_volatility"
    assert row.status == "watch"
    assert row.confidence_score == d("0.495000")
    assert "momentum_filter_watch" in row.reason_codes

    payload_text = json.dumps(
        market_momentum_noise_filter_report_payload(momentum_report),
        sort_keys=True,
    ).lower()
    forbidden_public_terms = (
        "buy",
        "sell",
        "position",
        "trade",
        "wallet",
        "order_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_url",
    )
    assert all(term not in payload_text for term in forbidden_public_terms)


def test_payload_is_decimal_only_json_ready_and_rejects_identifiers() -> None:
    momentum_report = report((observation(),))
    payload = market_momentum_noise_filter_report_payload(momentum_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["confidence_score"] == "0.844000"
    assert "market_id" not in encoded
    assert "source_id" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded

    with pytest.raises(ValueError, match="identifier"):
        market_momentum_noise_filter_report_payload({"market_id": "abc"})
    with pytest.raises(ValueError, match="identifier"):
        market_momentum_noise_filter_report_payload({"rows": [{"source_url": "https://x"}]})


def test_validation_rejects_bad_types_enums_times_counts_and_flags() -> None:
    with pytest.raises(ValueError, match="material_move_bps"):
        config(material_move_bps=d("-1"))
    with pytest.raises(ValueError, match="min_confidence_score"):
        config(min_confidence_score=0.6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="news_catalyst_score"):
        config(news_catalyst_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="probability_move_bps"):
        observation(probability_move_bps=d("-1"))
    with pytest.raises(ValueError, match="liquidity_depth_score"):
        observation(liquidity_depth_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(), paper_only=False)
    with pytest.raises(ValueError, match="rows"):
        report((object(),))


def test_public_dataclasses_are_frozen_and_manual_report_validates_consistency() -> None:
    momentum_report = report((observation(),))

    with pytest.raises(FrozenInstanceError):
        momentum_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        momentum_report.rows[0].confidence_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="confidence_score"):
        replace(momentum_report.rows[0], confidence_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(momentum_report, status="block")


def test_owned_module_has_no_live_trading_auth_wallet_network_or_db_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_momentum_noise_filter.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
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
        "wallet",
        "private_key",
        "signature",
        "auth",
        "place_order",
        "cancel_order",
        "buy",
        "sell",
        "position",
        "recommend",
    )

    assert all(term not in source for term in forbidden_terms)


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

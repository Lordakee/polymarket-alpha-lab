from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from hashlib import sha256
import json

import pytest

from polymarket_alpha_lab.market_liquidity_volatility_regime_report import (
    MarketLiquidityVolatilityRegimeReport,
    build_market_liquidity_volatility_regime_report,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def _expected_digest(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("payload_digest")
    encoded = json.dumps(digest_payload, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def test_builds_normal_report_with_public_payload_and_digest() -> None:
    report = build_market_liquidity_volatility_regime_report(
        spread_probability=d("0.120000"),
        depth_probability=d("0.180000"),
        recent_volatility_probability=d("0.220000"),
        volume_change_probability=d("0.100000"),
        market_close_hours=d("72.000000"),
    )

    assert report.regime_status == "normal"
    assert report.reason_codes == ("liquidity_volatility_regime_clear",)
    assert report.manual_next_step == "continue_manual_monitoring"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert set(payload) == {
        "spread_probability",
        "depth_probability",
        "recent_volatility_probability",
        "volume_change_probability",
        "market_close_hours",
        "regime_status",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
        "payload_digest",
    }
    assert payload["spread_probability"] == "0.120000"
    assert payload["depth_probability"] == "0.180000"
    assert payload["recent_volatility_probability"] == "0.220000"
    assert payload["volume_change_probability"] == "0.100000"
    assert payload["market_close_hours"] == "72.000000"
    assert payload["payload_digest"] == report.payload_digest
    assert report.payload_digest == _expected_digest(payload)


def test_reports_watch_and_risk_reason_codes_without_action_surface() -> None:
    watch_report = build_market_liquidity_volatility_regime_report(
        spread_probability=d("0.420000"),
        depth_probability=d("0.210000"),
        recent_volatility_probability=d("0.300000"),
        volume_change_probability=d("0.390000"),
        market_close_hours=d("18.000000"),
    )

    assert watch_report.regime_status == "watch"
    assert watch_report.reason_codes == (
        "spread_probability_watch",
        "market_close_hours_watch",
    )
    assert watch_report.manual_next_step == "manual_review_before_new_paper_research"

    risk_report = build_market_liquidity_volatility_regime_report(
        spread_probability=d("0.820000"),
        depth_probability=d("0.720000"),
        recent_volatility_probability=d("0.770000"),
        volume_change_probability=d("0.610000"),
        market_close_hours=d("5.500000"),
    )

    assert risk_report.regime_status == "risk"
    assert risk_report.reason_codes == (
        "spread_probability_high",
        "depth_probability_high",
        "recent_volatility_probability_high",
        "volume_change_probability_watch",
        "market_close_hours_urgent",
    )
    assert risk_report.manual_next_step == "manual_liquidity_volatility_review_required"


def test_report_is_frozen_decimal_only_and_flag_guarded() -> None:
    report = build_market_liquidity_volatility_regime_report(
        spread_probability=d("0.120000"),
        depth_probability=d("0.180000"),
        recent_volatility_probability=d("0.220000"),
        volume_change_probability=d("0.100000"),
        market_close_hours=d("72.000000"),
    )

    with pytest.raises(FrozenInstanceError):
        report.regime_status = "risk"  # type: ignore[misc]

    with pytest.raises(ValueError, match="spread_probability.*Decimal"):
        build_market_liquidity_volatility_regime_report(
            spread_probability="0.120000",  # type: ignore[arg-type]
            depth_probability=d("0.180000"),
            recent_volatility_probability=d("0.220000"),
            volume_change_probability=d("0.100000"),
            market_close_hours=d("72.000000"),
        )

    with pytest.raises(ValueError, match="market_close_hours.*Decimal"):
        build_market_liquidity_volatility_regime_report(
            spread_probability=d("0.120000"),
            depth_probability=d("0.180000"),
            recent_volatility_probability=d("0.220000"),
            volume_change_probability=d("0.100000"),
            market_close_hours=72,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="0" * 64)


def test_rejects_inconsistent_direct_report_fields() -> None:
    with pytest.raises(ValueError, match="regime_status"):
        MarketLiquidityVolatilityRegimeReport(
            spread_probability=d("0.820000"),
            depth_probability=d("0.720000"),
            recent_volatility_probability=d("0.770000"),
            volume_change_probability=d("0.610000"),
            market_close_hours=d("5.500000"),
            regime_status="normal",
            reason_codes=("liquidity_volatility_regime_clear",),
            manual_next_step="continue_manual_monitoring",
        )

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_threshold_backtest_readiness_report import (
    StrategyThresholdBacktestReadinessReport,
    build_strategy_threshold_backtest_readiness_report,
    strategy_threshold_backtest_readiness_report_digest,
    strategy_threshold_backtest_readiness_report_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(
    *,
    historical_screen_count: Decimal = d("120"),
    settled_market_count: Decimal = d("80"),
    domain_split_ready: bool = True,
    cost_model_revision_current: bool = True,
    slippage_model_revision_current: bool = True,
    calibration_error_rate: Decimal = d("0.030000"),
    supabase_history_ready: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyThresholdBacktestReadinessReport:
    return build_strategy_threshold_backtest_readiness_report(
        historical_screen_count=historical_screen_count,
        settled_market_count=settled_market_count,
        domain_split_ready=domain_split_ready,
        cost_model_revision_current=cost_model_revision_current,
        slippage_model_revision_current=slippage_model_revision_current,
        calibration_error_rate=calibration_error_rate,
        supabase_history_ready=supabase_history_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_ready_report_uses_sample_depth_and_operational_flags() -> None:
    readiness_report = report()

    assert type(readiness_report) is StrategyThresholdBacktestReadinessReport
    assert readiness_report.threshold_backtest_ready is True
    assert readiness_report.sample_gap_count == d("0")
    assert readiness_report.blocked_reason_codes == ()
    assert readiness_report.attention_reason_codes == ()
    assert readiness_report.ready_ratio == d("1.000000")
    assert len(readiness_report.digest) == 64
    assert readiness_report.digest == strategy_threshold_backtest_readiness_report_digest(
        readiness_report,
    )
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True


def test_report_blocks_when_samples_domain_models_history_or_calibration_are_missing() -> None:
    readiness_report = report(
        historical_screen_count=d("50"),
        settled_market_count=d("25"),
        domain_split_ready=False,
        cost_model_revision_current=False,
        slippage_model_revision_current=False,
        calibration_error_rate=d("0.120000"),
        supabase_history_ready=False,
    )

    assert readiness_report.threshold_backtest_ready is False
    assert readiness_report.sample_gap_count == d("125")
    assert readiness_report.ready_ratio == d("0.312500")
    assert readiness_report.blocked_reason_codes == (
        "insufficient_historical_screen_count",
        "insufficient_settled_market_count",
        "domain_split_not_ready",
        "cost_model_revision_stale",
        "slippage_model_revision_stale",
        "calibration_error_rate_above_limit",
        "supabase_history_not_ready",
    )
    assert readiness_report.attention_reason_codes == ()


def test_report_surfaces_attention_before_full_blocking_thresholds() -> None:
    readiness_report = report(
        historical_screen_count=d("110"),
        settled_market_count=d("70"),
        calibration_error_rate=d("0.070000"),
    )

    assert readiness_report.threshold_backtest_ready is False
    assert readiness_report.sample_gap_count == d("20")
    assert readiness_report.ready_ratio == d("0.875000")
    assert readiness_report.blocked_reason_codes == ()
    assert readiness_report.attention_reason_codes == (
        "historical_screen_count_below_target",
        "settled_market_count_below_target",
        "calibration_error_rate_watch",
    )


def test_payload_and_digest_are_deterministic_public_safe_decimal_strings() -> None:
    first_report = report()
    second_report = report()

    first_payload = strategy_threshold_backtest_readiness_report_payload(first_report)
    second_payload = strategy_threshold_backtest_readiness_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload["digest"] == first_report.digest
    assert first_payload["historical_screen_count"] == "120"
    assert first_payload["settled_market_count"] == "80"
    assert first_payload["calibration_error_rate"] == "0.030000"
    assert first_payload["ready_ratio"] == "1.000000"
    assert not any(type(value) is float for value in _walk_payload_values(first_payload))
    assert not any(type(value) is int for value in _walk_payload_values(first_payload))
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "market_id",
            "market_slug",
            "wallet",
            "auth",
            "order",
            "trade",
            "live",
            "execution",
            "token",
            "http://",
            "https://",
        )
    )


def test_validation_rejects_non_decimal_counts_rates_and_non_report_flags() -> None:
    with pytest.raises(ValueError, match="historical_screen_count"):
        report(historical_screen_count=120)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="settled_market_count"):
        report(settled_market_count=d("1.5"))
    with pytest.raises(ValueError, match="calibration_error_rate"):
        report(calibration_error_rate=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="calibration_error_rate"):
        report(calibration_error_rate=d("1.000001"))
    with pytest.raises(ValueError, match="domain_split_ready"):
        report(domain_split_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        report(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(readonly=False)


def test_public_dataclass_is_frozen_and_payload_revalidates_tampering() -> None:
    readiness_report = report()

    with pytest.raises(FrozenInstanceError):
        readiness_report.ready_ratio = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="digest"):
        replace(readiness_report, digest="0" * 64)

    object.__setattr__(readiness_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        strategy_threshold_backtest_readiness_report_payload(readiness_report)


def test_owned_module_has_no_io_network_live_trading_auth_or_database_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_threshold_backtest_readiness_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "execution",
        "insert",
        "update ",
        "delete ",
        "commit",
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

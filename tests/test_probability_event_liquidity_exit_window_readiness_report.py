from decimal import Decimal

import pytest

from polymarket_alpha_lab.probability_event_liquidity_exit_window_readiness_report import (
    ProbabilityEventLiquidityExitWindowReadinessReport,
    build_probability_event_liquidity_exit_window_readiness_report,
    probability_event_liquidity_exit_window_readiness_report_payload,
    validate_probability_event_liquidity_exit_window_readiness_public_payload,
)


def test_ready_when_depth_spread_and_resolution_window_are_sufficient() -> None:
    report = build_probability_event_liquidity_exit_window_readiness_report(
        entry_depth_probability=Decimal("0.850000"),
        exit_depth_probability=Decimal("0.900000"),
        time_to_resolution_hours=Decimal("96.000000"),
        spread_probability=Decimal("0.015000"),
        expected_exit_window_hours=Decimal("24.000000"),
    )

    assert report.exit_window_status == "ready"
    assert report.reason_codes == ("exit_window_ready",)
    assert report.manual_next_step == "monitor_exit_window"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_watch_when_exit_window_exists_but_inputs_are_thin() -> None:
    report = build_probability_event_liquidity_exit_window_readiness_report(
        entry_depth_probability=Decimal("0.610000"),
        exit_depth_probability=Decimal("0.650000"),
        time_to_resolution_hours=Decimal("30.000000"),
        spread_probability=Decimal("0.040000"),
        expected_exit_window_hours=Decimal("24.000000"),
    )

    assert report.exit_window_status == "watch"
    assert report.reason_codes == (
        "entry_depth_probability_watch",
        "exit_depth_probability_watch",
        "spread_probability_watch",
    )
    assert report.manual_next_step == "manual_review_exit_liquidity"


def test_blocked_when_resolution_time_cannot_support_expected_exit_window() -> None:
    report = build_probability_event_liquidity_exit_window_readiness_report(
        entry_depth_probability=Decimal("0.950000"),
        exit_depth_probability=Decimal("0.950000"),
        time_to_resolution_hours=Decimal("10.000000"),
        spread_probability=Decimal("0.010000"),
        expected_exit_window_hours=Decimal("24.000000"),
    )

    assert report.exit_window_status == "blocked"
    assert report.reason_codes == ("insufficient_time_to_resolution_exit_window",)
    assert report.manual_next_step == "do_not_enter_without_manual_exit_plan"


def test_public_payload_is_readonly_report_only_and_digest_validated() -> None:
    report = build_probability_event_liquidity_exit_window_readiness_report(
        entry_depth_probability=Decimal("0.800000"),
        exit_depth_probability=Decimal("0.820000"),
        time_to_resolution_hours=Decimal("72.000000"),
        spread_probability=Decimal("0.018000"),
        expected_exit_window_hours=Decimal("12.000000"),
    )

    payload = probability_event_liquidity_exit_window_readiness_report_payload(report)

    assert payload["entry_depth_probability"] == "0.800000"
    assert payload["exit_depth_probability"] == "0.820000"
    assert payload["time_to_resolution_hours"] == "72.000000"
    assert payload["spread_probability"] == "0.018000"
    assert payload["expected_exit_window_hours"] == "12.000000"
    assert payload["exit_window_status"] == "ready"
    assert payload["reason_codes"] == ["exit_window_ready"]
    assert payload["manual_next_step"] == "monitor_exit_window"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert validate_probability_event_liquidity_exit_window_readiness_public_payload(
        payload,
    )


def test_rejects_non_decimal_inputs_and_unsafe_flags() -> None:
    with pytest.raises(ValueError, match="entry_depth_probability.*Decimal"):
        build_probability_event_liquidity_exit_window_readiness_report(
            entry_depth_probability=0.8,  # type: ignore[arg-type]
            exit_depth_probability=Decimal("0.900000"),
            time_to_resolution_hours=Decimal("48.000000"),
            spread_probability=Decimal("0.010000"),
            expected_exit_window_hours=Decimal("12.000000"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        build_probability_event_liquidity_exit_window_readiness_report(
            entry_depth_probability=Decimal("0.800000"),
            exit_depth_probability=Decimal("0.900000"),
            time_to_resolution_hours=Decimal("48.000000"),
            spread_probability=Decimal("0.010000"),
            expected_exit_window_hours=Decimal("12.000000"),
            paper_only=False,
        )


def test_rejects_direct_report_mismatches_and_subclasses() -> None:
    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventLiquidityExitWindowReadinessReport):
            pass

    with pytest.raises(ValueError, match="exit_window_status"):
        ProbabilityEventLiquidityExitWindowReadinessReport(
            entry_depth_probability=Decimal("0.900000"),
            exit_depth_probability=Decimal("0.900000"),
            time_to_resolution_hours=Decimal("72.000000"),
            spread_probability=Decimal("0.010000"),
            expected_exit_window_hours=Decimal("12.000000"),
            exit_window_status="blocked",
            reason_codes=("exit_window_ready",),
            manual_next_step="monitor_exit_window",
        )

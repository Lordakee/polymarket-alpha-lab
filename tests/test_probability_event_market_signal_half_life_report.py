from decimal import Decimal

import pytest

from polymarket_alpha_lab.probability_event_market_signal_half_life_report import (
    ProbabilityEventMarketSignalHalfLifeInput,
    ProbabilityEventMarketSignalHalfLifeReport,
    build_probability_event_market_signal_half_life_report,
    probability_event_market_signal_half_life_report_digest,
)


def test_builds_readonly_half_life_report_with_public_payload_and_digest() -> None:
    signal = ProbabilityEventMarketSignalHalfLifeInput(
        initial_signal_probability=Decimal("0.800000"),
        signal_age_hours=Decimal("12.000000"),
        market_move_probability=Decimal("0.650000"),
        source_refresh_age_hours=Decimal("2.000000"),
        half_life_hours=Decimal("24.000000"),
    )

    report = build_probability_event_market_signal_half_life_report(signal)

    assert report.signal_half_life_status == "watch"
    assert report.decayed_signal_probability == Decimal("0.565685")
    assert report.reason_codes == (
        "market_move_diverged_from_decayed_signal",
        "signal_half_life_watch",
        "source_refresh_current",
    )
    assert report.manual_next_step == "refresh_source_and_compare_market_move"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.payload_digest == probability_event_market_signal_half_life_report_digest(
        report,
    )
    assert len(report.payload_digest) == 64

    payload = report.public_payload
    assert payload == {
        "config_version": "probability-event-market-signal-half-life-report-v0",
        "signal_half_life_status": "watch",
        "decayed_signal_probability": "0.565685",
        "reason_codes": [
            "market_move_diverged_from_decayed_signal",
            "signal_half_life_watch",
            "source_refresh_current",
        ],
        "manual_next_step": "refresh_source_and_compare_market_move",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": report.payload_digest,
    }
    with pytest.raises(TypeError, match="immutable"):
        payload["readonly"] = False


def test_blocks_expired_or_stale_signal_without_execution_surface() -> None:
    signal = ProbabilityEventMarketSignalHalfLifeInput(
        initial_signal_probability=Decimal("0.700000"),
        signal_age_hours=Decimal("96.000000"),
        market_move_probability=Decimal("0.200000"),
        source_refresh_age_hours=Decimal("30.000000"),
        half_life_hours=Decimal("24.000000"),
    )

    report = build_probability_event_market_signal_half_life_report(signal)

    assert report.signal_half_life_status == "block"
    assert report.decayed_signal_probability == Decimal("0.043750")
    assert report.reason_codes == (
        "market_move_diverged_from_decayed_signal",
        "signal_half_life_block",
        "source_refresh_stale",
    )
    assert report.manual_next_step == "manual_research_review_required"
    payload = report.public_payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    for forbidden in ("live", "auth", "wallet", "key", "signing", "execution"):
        assert forbidden not in repr(payload).lower()


def test_accepts_only_decimals_and_hard_readonly_flags() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        ProbabilityEventMarketSignalHalfLifeInput(
            initial_signal_probability=0.8,  # type: ignore[arg-type]
            signal_age_hours=Decimal("1.000000"),
            market_move_probability=Decimal("0.8"),
            source_refresh_age_hours=Decimal("1.000000"),
            half_life_hours=Decimal("24.000000"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        ProbabilityEventMarketSignalHalfLifeInput(
            initial_signal_probability=Decimal("0.800000"),
            signal_age_hours=Decimal("1.000000"),
            market_move_probability=Decimal("0.800000"),
            source_refresh_age_hours=Decimal("1.000000"),
            half_life_hours=Decimal("24.000000"),
            paper_only=False,
        )


def test_report_rejects_digest_or_reason_code_tampering() -> None:
    valid = build_probability_event_market_signal_half_life_report(
        ProbabilityEventMarketSignalHalfLifeInput(
            initial_signal_probability=Decimal("0.500000"),
            signal_age_hours=Decimal("0.000000"),
            market_move_probability=Decimal("0.500000"),
            source_refresh_age_hours=Decimal("0.000000"),
            half_life_hours=Decimal("24.000000"),
        ),
    )

    with pytest.raises(ValueError, match="payload_digest"):
        ProbabilityEventMarketSignalHalfLifeReport(
            config_version=valid.config_version,
            signal_half_life_status=valid.signal_half_life_status,
            decayed_signal_probability=valid.decayed_signal_probability,
            reason_codes=valid.reason_codes,
            manual_next_step=valid.manual_next_step,
            payload_digest="0" * 64,
        )

    with pytest.raises(ValueError, match="reason_codes"):
        ProbabilityEventMarketSignalHalfLifeReport(
            config_version=valid.config_version,
            signal_half_life_status=valid.signal_half_life_status,
            decayed_signal_probability=valid.decayed_signal_probability,
            reason_codes=("trade_now",),
            manual_next_step=valid.manual_next_step,
            payload_digest=valid.payload_digest,
        )

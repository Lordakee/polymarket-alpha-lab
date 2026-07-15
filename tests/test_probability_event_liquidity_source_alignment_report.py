from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.probability_event_liquidity_source_alignment_report import (
    ProbabilityEventLiquiditySourceAlignmentReport,
    build_probability_event_liquidity_source_alignment_report,
    probability_event_liquidity_source_alignment_report_payload,
    validate_probability_event_liquidity_source_alignment_public_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def _build(
    *,
    source_confidence_probability: Decimal = d("0.820000"),
    market_depth_probability: Decimal = d("0.840000"),
    spread_probability: Decimal = d("0.020000"),
    recent_price_move_probability: Decimal = d("0.040000"),
    source_freshness_age_hours: Decimal = d("4.000000"),
) -> ProbabilityEventLiquiditySourceAlignmentReport:
    return build_probability_event_liquidity_source_alignment_report(
        source_confidence_probability=source_confidence_probability,
        market_depth_probability=market_depth_probability,
        spread_probability=spread_probability,
        recent_price_move_probability=recent_price_move_probability,
        source_freshness_age_hours=source_freshness_age_hours,
    )


def test_ready_when_source_confidence_and_liquidity_environment_align() -> None:
    report = _build()

    assert type(report) is ProbabilityEventLiquiditySourceAlignmentReport
    assert report.alignment_status == "ready"
    assert report.liquidity_aligned_confidence_probability == d("0.800000")
    assert report.reason_codes == ("source_liquidity_alignment_ready",)
    assert report.manual_next_step == "continue_readonly_probability_review"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_watch_when_source_signal_is_credible_but_liquidity_environment_is_thin() -> None:
    report = _build(
        source_confidence_probability=d("0.740000"),
        market_depth_probability=d("0.620000"),
        spread_probability=d("0.045000"),
        recent_price_move_probability=d("0.090000"),
        source_freshness_age_hours=d("9.000000"),
    )

    assert report.alignment_status == "watch"
    assert report.liquidity_aligned_confidence_probability == d("0.620000")
    assert report.reason_codes == (
        "market_depth_probability_watch",
        "spread_probability_watch",
        "recent_price_move_probability_watch",
        "source_freshness_age_hours_watch",
    )
    assert report.manual_next_step == "manually_review_source_liquidity_alignment"


def test_blocked_when_source_or_liquidity_inputs_are_not_report_ready() -> None:
    report = _build(
        source_confidence_probability=d("0.480000"),
        market_depth_probability=d("0.390000"),
        spread_probability=d("0.090000"),
        recent_price_move_probability=d("0.160000"),
        source_freshness_age_hours=d("30.000000"),
    )

    assert report.alignment_status == "blocked"
    assert report.liquidity_aligned_confidence_probability == d("0.390000")
    assert report.reason_codes == (
        "source_confidence_probability_blocked",
        "market_depth_probability_blocked",
        "spread_probability_blocked",
        "recent_price_move_probability_blocked",
        "source_freshness_age_hours_blocked",
    )
    assert report.manual_next_step == "pause_and_refresh_sources_before_manual_review"


def test_public_payload_is_canonical_readonly_and_digest_validated() -> None:
    report = _build(
        source_confidence_probability=d("0.8123454"),
        market_depth_probability=d("0.8456784"),
        spread_probability=d("0.0199994"),
        recent_price_move_probability=d("0.0400004"),
        source_freshness_age_hours=d("4.5000004"),
    )

    payload = probability_event_liquidity_source_alignment_report_payload(report)

    assert payload == report.public_payload
    assert payload["source_confidence_probability"] == "0.812345"
    assert payload["market_depth_probability"] == "0.845678"
    assert payload["spread_probability"] == "0.019999"
    assert payload["recent_price_move_probability"] == "0.040000"
    assert payload["source_freshness_age_hours"] == "4.500000"
    assert payload["liquidity_aligned_confidence_probability"] == "0.792346"
    assert payload["alignment_status"] == "ready"
    assert payload["reason_codes"] == ["source_liquidity_alignment_ready"]
    assert payload["manual_next_step"] == "continue_readonly_probability_review"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert type(payload["payload_digest"]) is str
    assert len(payload["payload_digest"]) == 64
    assert validate_probability_event_liquidity_source_alignment_public_payload(payload)
    json.dumps(payload, sort_keys=True)
    _assert_no_decimal_objects(payload)


def test_validation_rejects_non_decimal_inputs_mutation_and_unsafe_public_payloads() -> None:
    report = _build()

    with pytest.raises(FrozenInstanceError):
        report.alignment_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_confidence_probability"):
        _build(source_confidence_probability="0.800000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_depth_probability"):
        _build(market_depth_probability=d("1.100000"))
    with pytest.raises(ValueError, match="source_freshness_age_hours"):
        _build(source_freshness_age_hours=d("-1.000000"))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    unsafe_payload = dict(report.public_payload)
    unsafe_payload["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        validate_probability_event_liquidity_source_alignment_public_payload(
            unsafe_payload,
        )

    tampered_payload = dict(report.public_payload)
    tampered_payload["alignment_status"] = "blocked"
    with pytest.raises(ValueError, match="digest"):
        validate_probability_event_liquidity_source_alignment_public_payload(
            tampered_payload,
        )


def test_direct_report_mismatches_subclasses_and_runtime_surfaces_are_rejected() -> None:
    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventLiquiditySourceAlignmentReport):
            pass

    with pytest.raises(ValueError, match="alignment_status"):
        ProbabilityEventLiquiditySourceAlignmentReport(
            source_confidence_probability=d("0.820000"),
            market_depth_probability=d("0.840000"),
            spread_probability=d("0.020000"),
            recent_price_move_probability=d("0.040000"),
            source_freshness_age_hours=d("4.000000"),
            liquidity_aligned_confidence_probability=d("0.800000"),
            alignment_status="blocked",
            reason_codes=("source_liquidity_alignment_ready",),
            manual_next_step="continue_readonly_probability_review",
        )

    import polymarket_alpha_lab.probability_event_liquidity_source_alignment_report as module

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "ccxt",
        "wallet",
        "sign",
        "execute",
    ):
        assert not hasattr(module, forbidden_name)
    for public_name in module.__all__:
        assert not any(
            fragment in public_name.lower()
            for fragment in ("live", "auth", "wallet", "key", "sign", "execute")
        )


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_book_observation_quality_report import (
    ResearchMarketBookObservation,
    ResearchMarketBookObservationQualityConfig,
    ResearchMarketBookObservationQualityReasonCodeCount,
    ResearchMarketBookObservationQualityReport,
    ResearchMarketBookObservationQualityRow,
    build_research_market_book_observation_quality_report,
    research_market_book_observation_quality_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    index: int,
    *,
    market_slug: str = "alpha-market",
    observed_at: datetime | None = None,
    best_bid_price: Decimal = d("0.490000"),
    best_ask_price: Decimal = d("0.510000"),
    bid_depth: Decimal = d("200.000000"),
    ask_depth: Decimal = d("180.000000"),
    fee_rate: Decimal = d("0.010000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketBookObservation:
    return ResearchMarketBookObservation(
        observation_id=f"book-observation-{index:03d}",
        market_slug=market_slug,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=index)
        ),
        best_bid_price=best_bid_price,
        best_ask_price=best_ask_price,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        fee_rate=fee_rate,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchMarketBookObservation, ...],
    *,
    config: ResearchMarketBookObservationQualityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketBookObservationQualityReport:
    return build_research_market_book_observation_quality_report(
        rows,
        config=config or ResearchMarketBookObservationQualityConfig(),
        generated_at=generated_at,
    )


def test_builds_aggregate_book_quality_rows_without_sizing_or_trade_advice() -> None:
    quality_report = report(
        (
            observation(
                3,
                best_bid_price=d("0.500000"),
                best_ask_price=d("0.520000"),
                reason_codes=("manual_book_check",),
            ),
            observation(1),
            observation(
                4,
                market_slug="beta-market",
                observed_at=GENERATED_AT - timedelta(minutes=20),
                best_bid_price=d("0.400000"),
                best_ask_price=d("0.480000"),
                bid_depth=d("10.000000"),
                ask_depth=d("8.000000"),
                fee_rate=d("0.070000"),
            ),
            observation(
                2,
                best_bid_price=d("0.495000"),
                best_ask_price=d("0.515000"),
            ),
        ),
    )

    assert quality_report.status == "block"
    assert quality_report.market_count == d("2")
    assert quality_report.observation_count == d("4")
    assert quality_report.pass_count == d("1")
    assert quality_report.watch_count == d("0")
    assert quality_report.block_count == d("1")
    assert quality_report.fresh_observation_count == d("3")
    assert quality_report.stale_observation_count == d("1")
    assert quality_report.max_missing_observation_pressure == d("0.666667")
    assert quality_report.average_quality_score == d("0.453334")
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True
    assert tuple(row.market_group_ref for row in quality_report.rows) == (
        "book_observation_group_001",
        "book_observation_group_002",
    )

    alpha = quality_report.rows[0]
    assert type(alpha) is ResearchMarketBookObservationQualityRow
    assert alpha.observation_count == d("3")
    assert alpha.fresh_observation_count == d("3")
    assert alpha.stale_observation_count == d("0")
    assert alpha.latest_observation_age_seconds == d("60")
    assert alpha.average_spread == d("0.020000")
    assert alpha.spread_range == d("0.000000")
    assert alpha.average_fee_rate == d("0.010000")
    assert alpha.min_bid_depth == d("200.000000")
    assert alpha.min_ask_depth == d("180.000000")
    assert alpha.missing_observation_pressure == d("0.000000")
    assert alpha.freshness_score == d("1.000000")
    assert alpha.spread_stability_score == d("0.600000")
    assert alpha.fee_friction_score == d("0.800000")
    assert alpha.observation_completeness_score == d("1.000000")
    assert alpha.quality_score == d("0.840000")
    assert alpha.status == "pass"
    assert alpha.reason_codes == (
        "book_depth_fresh",
        "fee_friction_pass",
        "input_manual_book_check",
        "market_book_observation_quality_pass",
        "missing_observation_pressure_pass",
        "spread_stability_pass",
    )

    beta = quality_report.rows[1]
    assert beta.observation_count == d("1")
    assert beta.fresh_observation_count == d("0")
    assert beta.stale_observation_count == d("1")
    assert beta.latest_observation_age_seconds == d("1200")
    assert beta.average_spread == d("0.080000")
    assert beta.spread_range == d("0.000000")
    assert beta.average_fee_rate == d("0.070000")
    assert beta.missing_observation_pressure == d("0.666667")
    assert beta.quality_score == d("0.066667")
    assert beta.status == "block"
    assert beta.reason_codes == (
        "book_depth_stale",
        "fee_friction_block",
        "market_book_observation_quality_block",
        "missing_observation_pressure_block",
        "spread_stability_block",
    )
    payload_json = json.dumps(
        research_market_book_observation_quality_report_payload(quality_report),
        sort_keys=True,
    ).lower()
    assert "trade" not in payload_json
    assert "market_slug" not in payload_json
    assert "alpha-market" not in payload_json
    assert "beta-market" not in payload_json


def test_payload_digest_and_reason_counts_are_stable_decimal_only_and_report_only() -> None:
    observations = (
        observation(2, reason_codes=("zeta", "alpha")),
        observation(1, reason_codes=("alpha",)),
    )

    first = report(observations)
    second = report(tuple(reversed(observations)))
    first_payload = research_market_book_observation_quality_report_payload(first)
    second_payload = research_market_book_observation_quality_report_payload(second)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["rows"][0]["quality_score"] == "0.773333"
    assert first_payload["rows"][0]["latest_observed_at"] == "2026-07-08T11:59:00+00:00"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in json.dumps(first_payload, sort_keys=True)
    assert tuple(
        (item.reason_code, item.count)
        for item in first.reason_code_counts
        if item.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert first.reason_code_counts == tuple(
        sorted(first.reason_code_counts, key=lambda item: item.reason_code)
    )
    assert ResearchMarketBookObservationQualityReasonCodeCount(
        reason_code="book_depth_fresh",
        count=d("1"),
    ).paper_only is True


def test_empty_report_is_blocked_and_uses_only_allowed_status_values() -> None:
    empty = report(())

    assert empty.status == "block"
    assert empty.market_count == d("0")
    assert empty.observation_count == d("0")
    assert empty.average_quality_score is None
    assert empty.reason_codes == ("no_book_observations",)
    assert empty.reason_code_counts == (
        ResearchMarketBookObservationQualityReasonCodeCount(
            reason_code="no_book_observations",
            count=d("1"),
        ),
    )
    assert empty.rows == ()

    with pytest.raises(ValueError, match="status"):
        replace(
            ResearchMarketBookObservationQualityRow(
                market_group_ref="manual-market-group",
                observation_count=d("1"),
                fresh_observation_count=d("1"),
                stale_observation_count=d("0"),
                latest_observed_at=GENERATED_AT,
                latest_observation_age_seconds=d("0"),
                average_spread=d("0.010000"),
                max_spread=d("0.010000"),
                spread_range=d("0.000000"),
                average_fee_rate=d("0.010000"),
                max_fee_rate=d("0.010000"),
                min_bid_depth=d("100.000000"),
                min_ask_depth=d("100.000000"),
                freshness_score=d("1.000000"),
                spread_stability_score=d("0.800000"),
                fee_friction_score=d("0.800000"),
                observation_completeness_score=d("1.000000"),
                missing_observation_pressure=d("0.000000"),
                quality_score=d("0.880000"),
                status="pass",
                reason_codes=("market_book_observation_quality_pass",),
            ),
            status="blocked",
        )


def test_validation_rejects_bad_types_future_times_flags_and_digest_tampering() -> None:
    quality_report = report((observation(1),))

    with pytest.raises(FrozenInstanceError):
        quality_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        quality_report.rows[0].quality_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="best_bid_price"):
        observation(1, best_bid_price=0.49)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_rate"):
        observation(1, fee_rate=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="best_ask_price"):
        observation(1, best_bid_price=d("0.520000"), best_ask_price=d("0.510000"))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        ResearchMarketBookObservationQualityConfig(paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(quality_report, derived_validation_digest="0" * 64)


def test_owned_module_has_no_db_network_wallet_or_live_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_book_observation_quality_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "postgres",
        "wallet",
        "private_key",
        "place_order",
        "order_size",
        "trade_recommendation",
        "live_trading",
        "connect(",
        "open(",
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

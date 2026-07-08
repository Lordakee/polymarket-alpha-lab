from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_maker_activity_anomaly_scorecard import (
    ResearchMarketMakerActivityAnomalyObservation,
    ResearchMarketMakerActivityAnomalyReasonCodeCount,
    ResearchMarketMakerActivityAnomalyScoreRow,
    ResearchMarketMakerActivityAnomalyScorecardConfig,
    ResearchMarketMakerActivityAnomalyScorecardReport,
    build_research_market_maker_activity_anomaly_scorecard_report,
    research_market_maker_activity_anomaly_scorecard_digest,
    research_market_maker_activity_anomaly_scorecard_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketMakerActivityAnomalyScorecardConfig:
    values = {
        "config_version": "research-market-maker-activity-anomaly-scorecard-v0",
        "watch_anomaly_score": d("0.350000"),
        "block_anomaly_score": d("0.700000"),
        "pass_quote_age_seconds": d("60.000000"),
        "block_quote_age_seconds": d("900.000000"),
        "pass_depth_imbalance_ratio": d("0.200000"),
        "block_depth_imbalance_ratio": d("0.800000"),
        "pass_spread_widening_ratio": d("0.250000"),
        "block_spread_widening_ratio": d("2.000000"),
        "pass_volume_burst_ratio": d("2.000000"),
        "block_volume_burst_ratio": d("8.000000"),
        "pass_top_liquidity_share": d("0.350000"),
        "block_top_liquidity_share": d("0.750000"),
        "quote_freshness_weight": d("0.200000"),
        "depth_imbalance_weight": d("0.200000"),
        "spread_widening_weight": d("0.200000"),
        "volume_burst_weight": d("0.200000"),
        "liquidity_concentration_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchMarketMakerActivityAnomalyScorecardConfig(**values)


def observation(
    index: int,
    *,
    research_bucket: str | None = None,
    public_event_label: str = "public-event",
    observed_at: datetime | None = None,
    quote_age_seconds: Decimal = d("30.000000"),
    bid_depth_units: Decimal = d("100.000000"),
    ask_depth_units: Decimal = d("100.000000"),
    current_spread_bps: Decimal = d("20.000000"),
    baseline_spread_bps: Decimal = d("20.000000"),
    current_volume_units: Decimal = d("100.000000"),
    baseline_volume_units: Decimal = d("100.000000"),
    top_liquidity_share: Decimal = d("0.200000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketMakerActivityAnomalyObservation:
    return ResearchMarketMakerActivityAnomalyObservation(
        research_bucket=research_bucket or f"activity-bucket-{index:03d}",
        public_event_label=public_event_label,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(seconds=30)
        ),
        quote_age_seconds=quote_age_seconds,
        bid_depth_units=bid_depth_units,
        ask_depth_units=ask_depth_units,
        current_spread_bps=current_spread_bps,
        baseline_spread_bps=baseline_spread_bps,
        current_volume_units=current_volume_units,
        baseline_volume_units=baseline_volume_units,
        top_liquidity_share=top_liquidity_share,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchMarketMakerActivityAnomalyScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketMakerActivityAnomalyScorecardReport:
    return build_research_market_maker_activity_anomaly_scorecard_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_block_report() -> None:
    anomaly_report = report(())

    assert type(anomaly_report) is ResearchMarketMakerActivityAnomalyScorecardReport
    assert anomaly_report.generated_at == GENERATED_AT
    assert anomaly_report.config_version == (
        "research-market-maker-activity-anomaly-scorecard-v0"
    )
    assert anomaly_report.observation_count == d("0")
    assert anomaly_report.pass_count == d("0")
    assert anomaly_report.watch_count == d("0")
    assert anomaly_report.block_count == d("0")
    assert anomaly_report.average_anomaly_score is None
    assert anomaly_report.max_anomaly_score == d("0.000000")
    assert anomaly_report.status == "block"
    assert anomaly_report.reason_codes == ("no_activity_observations",)
    assert anomaly_report.reason_code_counts == (
        ResearchMarketMakerActivityAnomalyReasonCodeCount(
            reason_code="no_activity_observations",
            count=d("1"),
        ),
    )
    assert anomaly_report.rows == ()
    assert anomaly_report.paper_only is True
    assert anomaly_report.report_only is True
    assert anomaly_report.readonly is True


def test_normal_fresh_balanced_activity_passes_with_zero_anomaly_score() -> None:
    anomaly_report = report((observation(1),))

    assert anomaly_report.status == "pass"
    assert anomaly_report.observation_count == d("1")
    assert anomaly_report.pass_count == d("1")
    assert anomaly_report.watch_count == d("0")
    assert anomaly_report.block_count == d("0")
    assert anomaly_report.average_anomaly_score == d("0.000000")
    assert anomaly_report.reason_codes == ("activity_anomaly_score_pass",)

    row = anomaly_report.rows[0]
    assert type(row) is ResearchMarketMakerActivityAnomalyScoreRow
    assert row.quote_freshness_score == d("0.000000")
    assert row.depth_imbalance_ratio == d("0.000000")
    assert row.depth_imbalance_score == d("0.000000")
    assert row.spread_widening_ratio == d("0.000000")
    assert row.spread_widening_score == d("0.000000")
    assert row.volume_burst_ratio == d("1.000000")
    assert row.volume_burst_score == d("0.000000")
    assert row.liquidity_concentration_score == d("0.000000")
    assert row.anomaly_score == d("0.000000")
    assert row.status == "pass"
    assert row.reason_codes == ("activity_anomaly_score_pass",)


def test_watch_and_block_rows_capture_only_activity_anomaly_metrics() -> None:
    anomaly_report = report(
        (
            observation(
                3,
                research_bucket="block-bucket",
                quote_age_seconds=d("1200.000000"),
                bid_depth_units=d("0.000000"),
                ask_depth_units=d("100.000000"),
                current_spread_bps=d("300.000000"),
                baseline_spread_bps=d("50.000000"),
                current_volume_units=d("1000.000000"),
                baseline_volume_units=d("100.000000"),
                top_liquidity_share=d("0.900000"),
            ),
            observation(
                2,
                research_bucket="watch-bucket",
                quote_age_seconds=d("300.000000"),
                bid_depth_units=d("120.000000"),
                ask_depth_units=d("30.000000"),
                current_spread_bps=d("80.000000"),
                baseline_spread_bps=d("40.000000"),
                current_volume_units=d("450.000000"),
                baseline_volume_units=d("100.000000"),
                top_liquidity_share=d("0.500000"),
                reason_codes=("manual_review",),
            ),
            observation(1, research_bucket="pass-bucket"),
        ),
    )

    pass_row, watch_row, block_row = anomaly_report.rows
    assert anomaly_report.status == "block"
    assert anomaly_report.pass_count == d("1")
    assert anomaly_report.watch_count == d("1")
    assert anomaly_report.block_count == d("1")
    assert anomaly_report.quote_freshness_count == d("2")
    assert anomaly_report.depth_imbalance_count == d("2")
    assert anomaly_report.spread_widening_count == d("2")
    assert anomaly_report.volume_burst_count == d("2")
    assert anomaly_report.liquidity_concentration_count == d("2")
    assert anomaly_report.average_anomaly_score == d("0.478175")
    assert anomaly_report.max_anomaly_score == d("1.000000")

    assert pass_row.research_bucket == "pass-bucket"
    assert watch_row.research_bucket == "watch-bucket"
    assert watch_row.quote_freshness_score == d("0.285714")
    assert watch_row.depth_imbalance_ratio == d("0.600000")
    assert watch_row.depth_imbalance_score == d("0.666667")
    assert watch_row.spread_widening_ratio == d("1.000000")
    assert watch_row.spread_widening_score == d("0.428571")
    assert watch_row.volume_burst_ratio == d("4.500000")
    assert watch_row.volume_burst_score == d("0.416667")
    assert watch_row.liquidity_concentration_score == d("0.375000")
    assert watch_row.anomaly_score == d("0.434524")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "activity_anomaly_score_watch",
        "depth_imbalance_watch",
        "input_manual_review",
        "liquidity_concentration_watch",
        "quote_freshness_watch",
        "spread_widening_watch",
        "volume_burst_watch",
    )

    assert block_row.research_bucket == "block-bucket"
    assert block_row.anomaly_score == d("1.000000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "activity_anomaly_score_block",
        "depth_imbalance_high",
        "liquidity_concentration_high",
        "quote_freshness_block",
        "spread_widening_high",
        "volume_burst_high",
    )


def test_payload_and_digest_are_deterministic_and_decimal_string_only() -> None:
    first_report = report(
        (
            observation(3, research_bucket="z-bucket"),
            observation(
                1,
                research_bucket="a-bucket",
                reason_codes=("zeta", "alpha"),
            ),
            observation(
                2,
                research_bucket="m-bucket",
                quote_age_seconds=d("300.000000"),
                bid_depth_units=d("120.000000"),
                ask_depth_units=d("30.000000"),
                current_spread_bps=d("80.000000"),
                baseline_spread_bps=d("40.000000"),
                current_volume_units=d("450.000000"),
                baseline_volume_units=d("100.000000"),
                top_liquidity_share=d("0.500000"),
            ),
        ),
    )
    second_report = report(tuple(reversed(first_report.rows)))

    first_payload = research_market_maker_activity_anomaly_scorecard_payload(first_report)
    second_payload = research_market_maker_activity_anomaly_scorecard_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert tuple(row.research_bucket for row in first_report.rows) == (
        "a-bucket",
        "z-bucket",
        "m-bucket",
    )
    assert first_payload == second_payload
    assert research_market_maker_activity_anomaly_scorecard_digest(
        first_report,
    ) == research_market_maker_activity_anomaly_scorecard_digest(second_report)
    assert len(research_market_maker_activity_anomaly_scorecard_digest(first_report)) == 64
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["anomaly_score"] == "0.000000"
    assert tuple(
        (count.reason_code, count.count)
        for count in first_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert "market_id" not in encoded
    assert "source_id" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in encoded


def test_validation_rejects_bad_types_bad_flags_future_times_and_unsafe_surfaces() -> None:
    with pytest.raises(ValueError, match="quote_freshness_weight"):
        config(quote_freshness_weight=d("0.100000"))
    with pytest.raises(ValueError, match="watch_anomaly_score"):
        config(watch_anomaly_score=0.35)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quote_age_seconds"):
        observation(1, quote_age_seconds=30)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="bid_depth_units"):
        observation(1, bid_depth_units=_DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="research_bucket"):
        observation(1, research_bucket="raw_market_id=abc")
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(report((observation(1),)).rows[0], status="blocked")
    with pytest.raises(ValueError, match="unsafe"):
        research_market_maker_activity_anomaly_scorecard_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"raw_market_id": "abc"}],
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_market_maker_activity_anomaly_scorecard_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"public_note": "wallet_address=abc"}],
            },
        )
    with pytest.raises(ValueError, match="readonly"):
        research_market_maker_activity_anomaly_scorecard_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": False,
            },
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    anomaly_report = report((observation(1),))

    with pytest.raises(FrozenInstanceError):
        anomaly_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        anomaly_report.rows[0].anomaly_score = d("1")  # type: ignore[misc]
    with pytest.raises(ValueError, match="anomaly_score"):
        replace(anomaly_report.rows[0], anomaly_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(anomaly_report, status="watch")


def test_owned_module_has_no_network_filesystem_write_or_forbidden_report_language() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_maker_activity_anomaly_scorecard.py"
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
        "sqlite",
        "postgres",
        "insert ",
        "update ",
        "delete ",
        "wallet",
        "auth",
        "api_key",
        "secret",
        "credential",
        "private_key",
        "session",
        "cookie",
        "bearer",
        "order",
        "trade",
        "trading",
        "live",
        "buy",
        "sell",
        "recommend",
        "position sizing",
        "position_size",
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

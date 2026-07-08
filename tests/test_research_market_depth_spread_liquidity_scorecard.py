from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_depth_spread_liquidity_scorecard import (
    ResearchMarketDepthSpreadLiquidityObservation,
    ResearchMarketDepthSpreadLiquidityReasonCodeCount,
    ResearchMarketDepthSpreadLiquidityScoreRow,
    ResearchMarketDepthSpreadLiquidityScorecardConfig,
    ResearchMarketDepthSpreadLiquidityScorecardReport,
    build_research_market_depth_spread_liquidity_scorecard_report,
    research_market_depth_spread_liquidity_scorecard_digest,
    research_market_depth_spread_liquidity_scorecard_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketDepthSpreadLiquidityScorecardConfig:
    values = {
        "config_version": "research-market-depth-spread-liquidity-scorecard-v0",
        "pass_liquidity_score": d("0.700000"),
        "watch_liquidity_score": d("0.400000"),
        "pass_depth_units": d("100.000000"),
        "pass_spread_bps": d("25.000000"),
        "block_spread_bps": d("250.000000"),
        "pass_top_participant_share": d("0.350000"),
        "block_top_participant_share": d("0.750000"),
        "pass_quote_age_seconds": d("60.000000"),
        "block_quote_age_seconds": d("900.000000"),
        "pass_cost_pressure_score": d("0.150000"),
        "block_cost_pressure_score": d("0.750000"),
        "depth_weight": d("0.300000"),
        "spread_weight": d("0.250000"),
        "concentration_weight": d("0.200000"),
        "stale_quote_weight": d("0.150000"),
        "cost_pressure_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchMarketDepthSpreadLiquidityScorecardConfig(**values)


def observation(
    index: int,
    *,
    research_key: str | None = None,
    public_event_id: str = "event-2026-fed",
    public_outcome_label: str = "public-outcome",
    observed_at: datetime | None = None,
    depth_units: Decimal = d("150.000000"),
    spread_bps: Decimal = d("20.000000"),
    top_participant_share: Decimal = d("0.200000"),
    quote_age_seconds: Decimal = d("45.000000"),
    cost_pressure_score: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketDepthSpreadLiquidityObservation:
    return ResearchMarketDepthSpreadLiquidityObservation(
        research_key=research_key or f"research-key-{index:03d}",
        public_event_id=public_event_id,
        public_outcome_label=public_outcome_label,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(seconds=45)
        ),
        depth_units=depth_units,
        spread_bps=spread_bps,
        top_participant_share=top_participant_share,
        quote_age_seconds=quote_age_seconds,
        cost_pressure_score=cost_pressure_score,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchMarketDepthSpreadLiquidityScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketDepthSpreadLiquidityScorecardReport:
    return build_research_market_depth_spread_liquidity_scorecard_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_block_report() -> None:
    liquidity_report = report(())

    assert type(liquidity_report) is ResearchMarketDepthSpreadLiquidityScorecardReport
    assert liquidity_report.generated_at == GENERATED_AT
    assert liquidity_report.config_version == (
        "research-market-depth-spread-liquidity-scorecard-v0"
    )
    assert liquidity_report.observation_count == d("0")
    assert liquidity_report.pass_count == d("0")
    assert liquidity_report.watch_count == d("0")
    assert liquidity_report.block_count == d("0")
    assert liquidity_report.average_liquidity_score is None
    assert liquidity_report.status == "block"
    assert liquidity_report.reason_codes == ("no_liquidity_observations",)
    assert liquidity_report.reason_code_counts == (
        ResearchMarketDepthSpreadLiquidityReasonCodeCount(
            reason_code="no_liquidity_observations",
            count=d("1"),
        ),
    )
    assert liquidity_report.rows == ()
    assert liquidity_report.paper_only is True
    assert liquidity_report.report_only is True
    assert liquidity_report.readonly is True


def test_deep_tight_distributed_fresh_low_cost_observation_passes() -> None:
    liquidity_report = report((observation(1),))

    assert liquidity_report.status == "pass"
    assert liquidity_report.observation_count == d("1")
    assert liquidity_report.pass_count == d("1")
    assert liquidity_report.watch_count == d("0")
    assert liquidity_report.block_count == d("0")
    assert liquidity_report.average_liquidity_score == d("1.000000")
    assert liquidity_report.reason_codes == ("liquidity_score_pass",)

    row = liquidity_report.rows[0]
    assert type(row) is ResearchMarketDepthSpreadLiquidityScoreRow
    assert row.depth_score == d("1.000000")
    assert row.spread_score == d("1.000000")
    assert row.concentration_score == d("1.000000")
    assert row.stale_quote_score == d("1.000000")
    assert row.cost_pressure_score_component == d("1.000000")
    assert row.liquidity_score == d("1.000000")
    assert row.status == "pass"
    assert row.reason_codes == ("liquidity_score_pass",)


def test_watch_and_block_rows_capture_depth_spread_concentration_stale_and_cost_risks() -> None:
    liquidity_report = report(
        (
            observation(
                2,
                research_key="block-row",
                depth_units=d("10.000000"),
                spread_bps=d("300.000000"),
                top_participant_share=d("0.900000"),
                quote_age_seconds=d("1200.000000"),
                cost_pressure_score=d("0.900000"),
            ),
            observation(
                1,
                research_key="watch-row",
                depth_units=d("60.000000"),
                spread_bps=d("80.000000"),
                top_participant_share=d("0.500000"),
                quote_age_seconds=d("300.000000"),
                cost_pressure_score=d("0.400000"),
                reason_codes=("manual_review",),
            ),
        ),
    )

    watch_row, block_row = liquidity_report.rows
    assert liquidity_report.status == "block"
    assert liquidity_report.pass_count == d("0")
    assert liquidity_report.watch_count == d("1")
    assert liquidity_report.block_count == d("1")
    assert liquidity_report.average_liquidity_score == d("0.344683")

    assert watch_row.research_key == "watch-row"
    assert watch_row.liquidity_score == d("0.659365")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "cost_pressure_elevated",
        "elevated_spread",
        "input_manual_review",
        "liquidity_concentration_watch",
        "liquidity_score_watch",
        "quote_age_watch",
        "thin_depth",
    )

    assert block_row.research_key == "block-row"
    assert block_row.liquidity_score == d("0.030000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "cost_pressure_high",
        "liquidity_concentration_high",
        "liquidity_score_block",
        "stale_quote_risk",
        "thin_depth",
        "wide_spread",
    )


def test_payload_and_digest_are_deterministic_and_decimal_string_only() -> None:
    first_report = report(
        (
            observation(
                3,
                research_key="z-row",
                depth_units=d("10.000000"),
                spread_bps=d("300.000000"),
                top_participant_share=d("0.900000"),
                quote_age_seconds=d("1200.000000"),
                cost_pressure_score=d("0.900000"),
            ),
            observation(1, research_key="a-row", reason_codes=("zeta", "alpha")),
            observation(
                2,
                research_key="m-row",
                depth_units=d("60.000000"),
                spread_bps=d("80.000000"),
                top_participant_share=d("0.500000"),
                quote_age_seconds=d("300.000000"),
                cost_pressure_score=d("0.400000"),
            ),
        ),
    )
    second_report = report(tuple(reversed(first_report.rows)))

    first_payload = research_market_depth_spread_liquidity_scorecard_payload(first_report)
    second_payload = research_market_depth_spread_liquidity_scorecard_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert tuple(row.research_key for row in first_report.rows) == (
        "a-row",
        "m-row",
        "z-row",
    )
    assert first_payload == second_payload
    assert research_market_depth_spread_liquidity_scorecard_digest(
        first_report,
    ) == research_market_depth_spread_liquidity_scorecard_digest(second_report)
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["liquidity_score"] == "1.000000"
    assert tuple(
        (count.reason_code, count.count)
        for count in first_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in encoded


def test_validation_rejects_bad_types_bad_flags_future_times_and_unsafe_surfaces() -> None:
    with pytest.raises(ValueError, match="depth_weight"):
        config(depth_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_liquidity_score"):
        config(pass_liquidity_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_units"):
        observation(1, depth_units=50)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_bps"):
        observation(1, spread_bps=_DecimalSubclass("20.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="research_key"):
        observation(1, research_key="raw_market_id=abc")
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)
    with pytest.raises(ValueError, match="unsafe"):
        research_market_depth_spread_liquidity_scorecard_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"raw_market_id": "abc"}],
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_market_depth_spread_liquidity_scorecard_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"public_note": "token=abc"}],
            },
        )
    with pytest.raises(ValueError, match="readonly"):
        research_market_depth_spread_liquidity_scorecard_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": False,
            },
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    liquidity_report = report((observation(1),))

    with pytest.raises(FrozenInstanceError):
        liquidity_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        liquidity_report.rows[0].liquidity_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="liquidity_score"):
        replace(liquidity_report.rows[0], liquidity_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(liquidity_report, status="watch")


def test_owned_module_has_no_network_filesystem_write_or_forbidden_report_language() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_spread_liquidity_scorecard.py"
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

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_resolution_liquidity_mismatch_report import (
    STATUSES,
    ResearchMarketResolutionLiquidityMismatchConfig,
    ResearchMarketResolutionLiquidityMismatchObservation,
    ResearchMarketResolutionLiquidityMismatchReasonCodeCount,
    ResearchMarketResolutionLiquidityMismatchReport,
    ResearchMarketResolutionLiquidityMismatchRow,
    build_research_market_resolution_liquidity_mismatch_report,
    research_market_resolution_liquidity_mismatch_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    index: int,
    *,
    public_cluster: str = "resolution-liquidity",
    resolution_bucket: str = "deadline-risk",
    sample_count: Decimal = d("5"),
    aggregate_rule_ambiguity_score: Decimal = d("0.100000"),
    deadline_pressure_score: Decimal = d("0.100000"),
    depth_fade_rate: Decimal = d("0.050000"),
    spread_widening_rate: Decimal = d("0.020000"),
    quote_staleness_seconds: Decimal = d("30.000000"),
    observed_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketResolutionLiquidityMismatchObservation:
    return ResearchMarketResolutionLiquidityMismatchObservation(
        public_cluster=f"{public_cluster}-{index:03d}",
        resolution_bucket=resolution_bucket,
        sample_count=sample_count,
        aggregate_rule_ambiguity_score=aggregate_rule_ambiguity_score,
        deadline_pressure_score=deadline_pressure_score,
        depth_fade_rate=depth_fade_rate,
        spread_widening_rate=spread_widening_rate,
        quote_staleness_seconds=quote_staleness_seconds,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=5)
        ),
        reason_codes=reason_codes,
    )


def report(
    *rows: ResearchMarketResolutionLiquidityMismatchObservation,
    cfg: ResearchMarketResolutionLiquidityMismatchConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketResolutionLiquidityMismatchReport:
    return build_research_market_resolution_liquidity_mismatch_report(
        rows,
        config=cfg or ResearchMarketResolutionLiquidityMismatchConfig(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_blocked_public_digest() -> None:
    mismatch_report = report()

    assert type(mismatch_report) is ResearchMarketResolutionLiquidityMismatchReport
    assert mismatch_report.status == "block"
    assert mismatch_report.generated_at == GENERATED_AT
    assert mismatch_report.observation_count == d("0")
    assert mismatch_report.sample_count == d("0")
    assert mismatch_report.row_count == d("0")
    assert mismatch_report.pass_count == d("0")
    assert mismatch_report.watch_count == d("0")
    assert mismatch_report.block_count == d("0")
    assert mismatch_report.max_mismatch_score is None
    assert mismatch_report.average_mismatch_score is None
    assert mismatch_report.rows == ()
    assert mismatch_report.reason_codes == (
        "resolution_liquidity_mismatch_no_observations",
    )
    assert mismatch_report.reason_code_counts == (
        ResearchMarketResolutionLiquidityMismatchReasonCodeCount(
            reason_code="resolution_liquidity_mismatch_no_observations",
            count=d("1"),
        ),
    )
    assert len(mismatch_report.derived_validation_digest) == 64
    assert mismatch_report.paper_only is True
    assert mismatch_report.report_only is True
    assert mismatch_report.readonly is True


def test_resolution_risk_and_liquidity_stress_drive_block_watch_pass_rows() -> None:
    mismatch_report = report(
        observation(
            3,
            public_cluster="quiet",
            resolution_bucket="routine",
        ),
        observation(
            1,
            public_cluster="acute",
            resolution_bucket="ambiguous-deadline",
            sample_count=d("7"),
            aggregate_rule_ambiguity_score=d("0.900000"),
            deadline_pressure_score=d("0.800000"),
            depth_fade_rate=d("0.700000"),
            spread_widening_rate=d("0.600000"),
            quote_staleness_seconds=d("900.000000"),
            reason_codes=("public_deadline_marker",),
        ),
        observation(
            2,
            public_cluster="elevated",
            resolution_bucket="approaching-cutoff",
            sample_count=d("4"),
            aggregate_rule_ambiguity_score=d("0.400000"),
            deadline_pressure_score=d("0.300000"),
            depth_fade_rate=d("0.250000"),
            spread_widening_rate=d("0.200000"),
            quote_staleness_seconds=d("300.000000"),
        ),
    )

    assert mismatch_report.status == "block"
    assert mismatch_report.observation_count == d("3")
    assert mismatch_report.sample_count == d("16")
    assert mismatch_report.block_count == d("1")
    assert mismatch_report.watch_count == d("1")
    assert mismatch_report.pass_count == d("1")
    assert mismatch_report.rule_ambiguity_watch_count == d("2")
    assert mismatch_report.deadline_pressure_watch_count == d("2")
    assert mismatch_report.depth_fade_watch_count == d("2")
    assert mismatch_report.spread_widening_watch_count == d("2")
    assert mismatch_report.quote_stale_count == d("2")
    assert mismatch_report.max_mismatch_score == d("0.808334")
    assert mismatch_report.average_mismatch_score == d("0.393704")

    blocked, watched, passed = mismatch_report.rows
    assert blocked.public_cluster == "acute-001"
    assert blocked.resolution_risk_score == d("0.850000")
    assert blocked.liquidity_stress_score == d("0.766667")
    assert blocked.mismatch_score == d("0.808334")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "input_public_deadline_marker",
        "resolution_liquidity_deadline_pressure_block",
        "resolution_liquidity_depth_fade_block",
        "resolution_liquidity_mismatch_block",
        "resolution_liquidity_quote_staleness_block",
        "resolution_liquidity_rule_ambiguity_block",
        "resolution_liquidity_spread_widening_block",
    )

    assert watched.public_cluster == "elevated-002"
    assert watched.status == "watch"
    assert watched.mismatch_score == d("0.305556")
    assert watched.reason_codes == (
        "resolution_liquidity_deadline_pressure_watch",
        "resolution_liquidity_depth_fade_watch",
        "resolution_liquidity_mismatch_watch",
        "resolution_liquidity_quote_staleness_watch",
        "resolution_liquidity_rule_ambiguity_watch",
        "resolution_liquidity_spread_widening_watch",
    )

    assert passed.public_cluster == "quiet-003"
    assert passed.status == "pass"
    assert passed.mismatch_score == d("0.067222")
    assert passed.reason_codes == (
        "resolution_liquidity_deadline_pressure_pass",
        "resolution_liquidity_depth_fade_pass",
        "resolution_liquidity_mismatch_pass",
        "resolution_liquidity_quote_staleness_fresh",
        "resolution_liquidity_rule_ambiguity_pass",
        "resolution_liquidity_spread_widening_pass",
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    first = report(
        observation(
            2,
            public_cluster="beta",
            aggregate_rule_ambiguity_score=d("0.400000"),
            depth_fade_rate=d("0.250000"),
        ),
        observation(1, public_cluster="alpha"),
    )
    second = report(
        observation(1, public_cluster="alpha"),
        observation(
            2,
            public_cluster="beta",
            aggregate_rule_ambiguity_score=d("0.400000"),
            depth_fade_rate=d("0.250000"),
        ),
    )

    first_payload = research_market_resolution_liquidity_mismatch_report_payload(first)
    second_payload = research_market_resolution_liquidity_mismatch_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)
    assert tuple(row["public_cluster"] for row in first_payload["rows"]) == (
        "alpha-001",
        "beta-002",
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert first_payload["rows"][0]["mismatch_score"] == str(first.rows[0].mismatch_score)
    assert "market_id" not in encoded
    assert "market_slug" not in encoded
    assert "source_id" not in encoded
    assert "raw_market" not in encoded
    assert "raw_source" not in encoded

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_validation_rejects_non_decimal_numbers_raw_identifiers_future_times_and_flags() -> None:
    with pytest.raises(ValueError, match="watch_mismatch_score"):
        ResearchMarketResolutionLiquidityMismatchConfig(
            watch_mismatch_score=d("0.700000"),
            block_mismatch_score=d("0.650000"),
        )
    with pytest.raises(ValueError, match="aggregate_rule_ambiguity_score"):
        observation(1, aggregate_rule_ambiguity_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="quote_staleness_seconds"):
        observation(1, quote_staleness_seconds=60)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(1), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="public_cluster"):
        observation(1, public_cluster="market_slug:raw-value")
    with pytest.raises(ValueError, match="resolution_bucket"):
        observation(1, resolution_bucket="source_id_raw")
    with pytest.raises(ValueError, match="reason_codes"):
        observation(1, reason_codes=("NeedsReview",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_statuses_are_exact() -> None:
    mismatch_report = report(observation(1))

    assert STATUSES == ("pass", "watch", "block")
    assert type(mismatch_report).__dataclass_params__.frozen
    assert type(mismatch_report.rows[0]) is ResearchMarketResolutionLiquidityMismatchRow
    assert type(mismatch_report.rows[0]).__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        mismatch_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        mismatch_report.rows[0].mismatch_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(mismatch_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(mismatch_report, status="blocked")


def test_owned_module_has_no_io_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_resolution_liquidity_mismatch_report.py"
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
        "psycopg",
        "sqlite",
        "supabase",
        "wallet",
        "auth",
        "private_key",
        "api_key",
        "secret",
        "credential",
        "buy",
        "sell",
        "position",
        "recommend",
        "size",
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

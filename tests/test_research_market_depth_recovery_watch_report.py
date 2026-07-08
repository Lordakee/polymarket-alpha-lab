from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_depth_recovery_watch_report import (
    ResearchMarketDepthRecoveryWatchConfig,
    ResearchMarketDepthRecoveryWatchObservation,
    ResearchMarketDepthRecoveryWatchReasonCodeCount,
    ResearchMarketDepthRecoveryWatchReport,
    ResearchMarketDepthRecoveryWatchRow,
    build_research_market_depth_recovery_watch_report,
    research_market_depth_recovery_watch_report_digest,
    research_market_depth_recovery_watch_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketDepthRecoveryWatchConfig:
    values = {
        "pass_recovery_score": d("0.700000"),
        "watch_recovery_score": d("0.400000"),
        "pass_aggregate_depth_recovery": d("0.700000"),
        "watch_aggregate_depth_recovery": d("0.400000"),
        "pass_spread_normalization": d("0.700000"),
        "watch_spread_normalization": d("0.400000"),
        "fresh_quote_age_seconds": d("60"),
        "stale_quote_age_seconds": d("900"),
        "watch_catalyst_pressure": d("0.350000"),
        "block_catalyst_pressure": d("0.700000"),
        "watch_fee_friction": d("0.300000"),
        "block_fee_friction": d("0.700000"),
        "aggregate_depth_recovery_weight": d("0.350000"),
        "spread_normalization_weight": d("0.250000"),
        "quote_freshness_weight": d("0.150000"),
        "catalyst_pressure_weight": d("0.150000"),
        "fee_friction_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchMarketDepthRecoveryWatchConfig(**values)


def observation(
    public_recovery_id: str = "recovery-a",
    *,
    public_event_label: str = "public-depth-recovery",
    observed_at: datetime = GENERATED_AT,
    aggregate_depth_recovery: Decimal = d("0.850000"),
    spread_normalization: Decimal = d("0.900000"),
    quote_age_seconds: Decimal = d("30"),
    catalyst_pressure: Decimal = d("0.100000"),
    fee_friction: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketDepthRecoveryWatchObservation:
    return ResearchMarketDepthRecoveryWatchObservation(
        public_recovery_id=public_recovery_id,
        public_event_label=public_event_label,
        observed_at=observed_at,
        aggregate_depth_recovery=aggregate_depth_recovery,
        spread_normalization=spread_normalization,
        quote_age_seconds=quote_age_seconds,
        catalyst_pressure=catalyst_pressure,
        fee_friction=fee_friction,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchMarketDepthRecoveryWatchConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketDepthRecoveryWatchReport:
    return build_research_market_depth_recovery_watch_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_blocked_report() -> None:
    recovery_report = report(())

    assert type(recovery_report) is ResearchMarketDepthRecoveryWatchReport
    assert is_dataclass(recovery_report)
    assert recovery_report.__dataclass_params__.frozen
    assert recovery_report.generated_at == GENERATED_AT
    assert recovery_report.config_version == (
        "research-market-depth-recovery-watch-report-v0"
    )
    assert recovery_report.observation_count == d("0")
    assert recovery_report.pass_count == d("0")
    assert recovery_report.watch_count == d("0")
    assert recovery_report.block_count == d("0")
    assert recovery_report.average_recovery_score is None
    assert recovery_report.min_aggregate_depth_recovery == d("0.000000")
    assert recovery_report.max_quote_age_seconds == d("0")
    assert recovery_report.max_catalyst_pressure == d("0.000000")
    assert recovery_report.max_fee_friction == d("0.000000")
    assert recovery_report.status == "block"
    assert recovery_report.reason_codes == ("no_depth_recovery_observations",)
    assert recovery_report.reason_code_counts == (
        ResearchMarketDepthRecoveryWatchReasonCodeCount(
            reason_code="no_depth_recovery_observations",
            count=d("1"),
        ),
    )
    assert recovery_report.rows == ()
    assert recovery_report.paper_only is True
    assert recovery_report.report_only is True
    assert recovery_report.readonly is True


def test_recovery_rows_score_depth_spread_quote_catalyst_and_fee_friction() -> None:
    recovery_report = report(
        (
            observation(
                "recovery-c",
                aggregate_depth_recovery=d("0.100000"),
                spread_normalization=d("0.200000"),
                quote_age_seconds=d("1200"),
                catalyst_pressure=d("0.900000"),
                fee_friction=d("0.850000"),
            ),
            observation(
                "recovery-b",
                aggregate_depth_recovery=d("0.500000"),
                spread_normalization=d("0.450000"),
                quote_age_seconds=d("480"),
                catalyst_pressure=d("0.450000"),
                fee_friction=d("0.350000"),
                reason_codes=("manual_public_review",),
            ),
            observation("recovery-a"),
        ),
    )

    assert tuple(row.public_recovery_id for row in recovery_report.rows) == (
        "recovery-a",
        "recovery-b",
        "recovery-c",
    )
    assert recovery_report.status == "block"
    assert recovery_report.observation_count == d("3")
    assert recovery_report.pass_count == d("1")
    assert recovery_report.watch_count == d("1")
    assert recovery_report.block_count == d("1")
    assert recovery_report.average_recovery_score == d("0.509167")
    assert recovery_report.min_aggregate_depth_recovery == d("0.100000")
    assert recovery_report.max_quote_age_seconds == d("1200")

    pass_row, watch_row, block_row = recovery_report.rows
    assert type(pass_row) is ResearchMarketDepthRecoveryWatchRow
    assert pass_row.quote_freshness_score == d("1.000000")
    assert pass_row.recovery_score == d("0.902500")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("depth_recovery_pass",)

    assert watch_row.quote_freshness_score == d("0.500000")
    assert watch_row.recovery_score == d("0.510000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "aggregate_depth_recovery_watch",
        "depth_recovery_score_watch",
        "fee_friction_elevated",
        "input_manual_public_review",
        "quote_freshness_watch",
        "spread_normalization_watch",
    )

    assert block_row.quote_freshness_score == d("0.000000")
    assert block_row.recovery_score == d("0.115000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "aggregate_depth_recovery_block",
        "catalyst_pressure_high",
        "depth_recovery_score_block",
        "fee_friction_high",
        "spread_normalization_block",
        "stale_quote_risk",
    )
    assert recovery_report.reason_code_counts == tuple(
        sorted(recovery_report.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    first_report = report(
        (
            observation(
                "z-recovery",
                aggregate_depth_recovery=d("0.100000"),
                spread_normalization=d("0.200000"),
                quote_age_seconds=d("1200"),
                catalyst_pressure=d("0.900000"),
                fee_friction=d("0.850000"),
            ),
            observation("a-recovery", reason_codes=("zeta", "alpha")),
            observation(
                "m-recovery",
                aggregate_depth_recovery=d("0.500000"),
                spread_normalization=d("0.450000"),
                quote_age_seconds=d("480"),
                catalyst_pressure=d("0.450000"),
                fee_friction=d("0.350000"),
            ),
        ),
    )
    second_report = report(tuple(reversed(first_report.rows)))
    first_payload = research_market_depth_recovery_watch_report_payload(first_report)
    second_payload = research_market_depth_recovery_watch_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert tuple(row.public_recovery_id for row in first_report.rows) == (
        "a-recovery",
        "m-recovery",
        "z-recovery",
    )
    assert first_payload == second_payload
    assert research_market_depth_recovery_watch_report_digest(
        first_report,
    ) == research_market_depth_recovery_watch_report_digest(second_report)
    assert len(research_market_depth_recovery_watch_report_digest(first_report)) == 64
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["recovery_score"] == "0.902500"
    assert tuple(
        (count.reason_code, count.count)
        for count in first_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in encoded
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "raw_market",
            "market_id",
            "condition_id",
            "source_id",
            "raw_source",
            "source_url",
            "source_text",
            "wallet",
            "auth",
            "api_key",
            "private_key",
            "order",
            "trade",
            "recommendation",
            "sizing",
            "live",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_values() -> None:
    with pytest.raises(ValueError, match="aggregate_depth_recovery_weight"):
        config(aggregate_depth_recovery_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_recovery_score"):
        config(pass_recovery_score=d("0.350000"))
    with pytest.raises(ValueError, match="fresh_quote_age_seconds"):
        config(fresh_quote_age_seconds=60)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_normalization_weight"):
        config(spread_normalization_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_recovery_id"):
        observation(public_recovery_id="check url")
    with pytest.raises(ValueError, match="public_recovery_id"):
        observation(public_recovery_id="raw-market-alpha")
    with pytest.raises(ValueError, match="quote_age_seconds"):
        observation(quote_age_seconds=480)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="aggregate_depth_recovery"):
        observation(aggregate_depth_recovery=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(), paper_only=False)
    with pytest.raises(ValueError, match="rows must contain"):
        report(("not-a-row",))


def test_dataclasses_are_frozen_and_module_is_report_only_static_surface() -> None:
    recovery_report = report((observation(),))
    row = recovery_report.rows[0]

    assert is_dataclass(ResearchMarketDepthRecoveryWatchConfig)
    assert is_dataclass(ResearchMarketDepthRecoveryWatchObservation)
    assert is_dataclass(ResearchMarketDepthRecoveryWatchRow)
    assert is_dataclass(ResearchMarketDepthRecoveryWatchReport)
    assert ResearchMarketDepthRecoveryWatchRow.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_recovery_watch_report.py"
    )
    module_text = module_path.read_text(encoding="utf-8").lower()
    assert all(
        fragment not in module_text
        for fragment in (
            "requests",
            "httpx",
            "socket",
            "psycopg",
            "sqlite",
            "open(",
            ".write(",
            "wallet",
            "auth",
            "private_key",
            "api_key",
            "order",
            "trade",
            "recommendation",
            "sizing",
            "live execution",
        )
    )


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_walk_payload_values(nested))
    elif isinstance(value, list):
        for nested in value:
            values.extend(_walk_payload_values(nested))
    return tuple(values)

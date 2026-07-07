from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import json
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
_DEFAULT_SOURCE_ID = object()


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def mod():
    return importlib.import_module(
        "polymarket_alpha_lab.research_polymarket_fee_assumption_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values = {
        "config_version": "research-polymarket-fee-assumption-report-v0",
        "max_pass_taker_fee_rate": d("0.000000"),
        "max_watch_taker_fee_rate": d("0.020000"),
        "max_pass_spread_rate": d("0.030000"),
        "max_watch_spread_rate": d("0.080000"),
        "min_pass_depth_usdc": d("2500.00"),
        "min_watch_depth_usdc": d("500.00"),
        "max_pass_settlement_friction_rate": d("0.010000"),
        "max_watch_settlement_friction_rate": d("0.030000"),
        "max_pass_refresh_age_seconds": d("900"),
        "max_watch_refresh_age_seconds": d("3600"),
    }
    values.update(overrides)
    return mod().PolymarketFeeAssumptionConfig(**values)


def assumption(
    index: int,
    *,
    market_id: str | None = None,
    source_id: str | None | object = _DEFAULT_SOURCE_ID,
    observed_at: datetime | None = None,
    taker_fee_rate: Decimal = d("0.000000"),
    spread_rate: Decimal = d("0.015000"),
    depth_usdc: Decimal = d("5000.00"),
    settlement_friction_rate: Decimal = d("0.005000"),
    reason_codes: tuple[str, ...] = (),
):
    return mod().PolymarketFeeAssumptionInputRow(
        market_id=market_id or f"market-{index:03d}",
        source_id=(
            f"source-{index:03d}" if source_id is _DEFAULT_SOURCE_ID else source_id
        ),
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=5)
        ),
        taker_fee_rate=taker_fee_rate,
        spread_rate=spread_rate,
        depth_usdc=depth_usdc,
        settlement_friction_rate=settlement_friction_rate,
        reason_codes=reason_codes,
    )


def report(rows: tuple[object, ...], *, generated_at: datetime = GENERATED_AT):
    return mod().build_research_polymarket_fee_assumption_report(
        rows,
        config=config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_summary() -> None:
    fee_report = report(())

    assert type(fee_report) is mod().PolymarketFeeAssumptionReport
    assert fee_report.generated_at == GENERATED_AT
    assert fee_report.config_version == "research-polymarket-fee-assumption-report-v0"
    assert fee_report.observation_count == d("0")
    assert fee_report.pass_count == d("0")
    assert fee_report.watch_count == d("0")
    assert fee_report.blocked_count == d("0")
    assert fee_report.average_total_cost_rate is None
    assert fee_report.minimum_depth_usdc is None
    assert fee_report.maximum_refresh_age_seconds is None
    assert fee_report.status == "blocked"
    assert fee_report.reason_codes == ("no_fee_assumptions",)
    assert fee_report.reason_code_counts == (
        mod().PolymarketFeeAssumptionReasonCodeCount(
            reason_code="no_fee_assumptions",
            count=d("1"),
        ),
    )
    assert fee_report.rows == ()
    assert fee_report.paper_only is True
    assert fee_report.report_only is True
    assert fee_report.readonly is True


def test_low_cost_deep_fresh_assumption_passes_with_component_statuses() -> None:
    fee_report = report((assumption(1),))

    assert fee_report.status == "pass"
    assert fee_report.observation_count == d("1")
    assert fee_report.pass_count == d("1")
    assert fee_report.watch_count == d("0")
    assert fee_report.blocked_count == d("0")
    assert fee_report.average_total_cost_rate == d("0.020000")
    assert fee_report.minimum_depth_usdc == d("5000.00")
    assert fee_report.maximum_refresh_age_seconds == d("300")
    assert fee_report.reason_codes == ("fee_assumption_pass",)

    row = fee_report.rows[0]
    assert type(row) is mod().PolymarketFeeAssumptionReportRow
    assert row.row_number == d("1")
    assert row.observed_at == GENERATED_AT - timedelta(minutes=5)
    assert row.refresh_age_seconds == d("300")
    assert row.taker_fee_rate == d("0.000000")
    assert row.spread_rate == d("0.015000")
    assert row.depth_usdc == d("5000.00")
    assert row.settlement_friction_rate == d("0.005000")
    assert row.total_cost_rate == d("0.020000")
    assert row.taker_fee_status == "pass"
    assert row.spread_status == "pass"
    assert row.depth_status == "pass"
    assert row.settlement_friction_status == "pass"
    assert row.refresh_cadence_status == "pass"
    assert row.status == "pass"
    assert row.reason_codes == (
        "deep_depth_assumption",
        "fee_assumption_pass",
        "fresh_refresh_cadence",
        "low_settlement_friction",
        "low_taker_fee",
        "tight_spread_assumption",
    )


def test_watch_and_block_outputs_cover_all_fee_assumption_dimensions() -> None:
    fee_report = report(
        (
            assumption(
                2,
                market_id="z-watch",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                spread_rate=d("0.050000"),
                depth_usdc=d("1000.00"),
                reason_codes=("manual_cost_review",),
            ),
            assumption(
                1,
                market_id="a-block",
                observed_at=GENERATED_AT - timedelta(hours=2),
                taker_fee_rate=d("0.050000"),
                spread_rate=d("0.090000"),
                depth_usdc=d("100.00"),
                settlement_friction_rate=d("0.050000"),
            ),
        ),
    )

    assert fee_report.status == "blocked"
    assert fee_report.pass_count == d("0")
    assert fee_report.watch_count == d("1")
    assert fee_report.blocked_count == d("1")
    assert fee_report.average_total_cost_rate == d("0.122500")
    assert fee_report.minimum_depth_usdc == d("100.00")
    assert fee_report.maximum_refresh_age_seconds == d("7200")

    blocked, watch = fee_report.rows
    assert blocked.row_number == d("1")
    assert blocked.taker_fee_status == "blocked"
    assert blocked.spread_status == "blocked"
    assert blocked.depth_status == "blocked"
    assert blocked.settlement_friction_status == "blocked"
    assert blocked.refresh_cadence_status == "blocked"
    assert blocked.status == "blocked"
    assert blocked.reason_codes == (
        "fee_assumption_blocked",
        "high_settlement_friction",
        "high_taker_fee",
        "stale_refresh_cadence",
        "thin_depth_assumption",
        "wide_spread_assumption",
    )

    assert watch.row_number == d("2")
    assert watch.taker_fee_status == "pass"
    assert watch.spread_status == "watch"
    assert watch.depth_status == "watch"
    assert watch.settlement_friction_status == "pass"
    assert watch.refresh_cadence_status == "watch"
    assert watch.status == "watch"
    assert watch.reason_codes == (
        "fee_assumption_watch",
        "input_manual_cost_review",
        "low_settlement_friction",
        "low_taker_fee",
        "moderate_depth_assumption",
        "refresh_cadence_lag",
        "wide_spread_assumption",
    )


def test_payload_uses_decimal_strings_and_redacts_market_source_identifiers() -> None:
    fee_report = report(
        (
            assumption(
                1,
                market_id="market-secret-yes",
                source_id="source-secret-feed",
            ),
        ),
    )

    payload = mod().research_polymarket_fee_assumption_report_payload(fee_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["rows"][0]["total_cost_rate"] == "0.020000"
    assert payload["rows"][0]["depth_usdc"] == "5000.00"
    assert "market-secret-yes" not in encoded
    assert "source-secret-feed" not in encoded
    assert "market_id" not in encoded
    assert "source_id" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_validation_rejects_bad_types_thresholds_times_reason_codes_and_flags() -> None:
    with pytest.raises(ValueError, match="max_pass_spread_rate"):
        config(max_pass_spread_rate=0.03)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_watch_spread_rate"):
        config(
            max_pass_spread_rate=d("0.080000"),
            max_watch_spread_rate=d("0.030000"),
        )
    with pytest.raises(ValueError, match="min_watch_depth_usdc"):
        config(
            min_pass_depth_usdc=d("500.00"),
            min_watch_depth_usdc=d("2500.00"),
        )
    with pytest.raises(ValueError, match="max_pass_taker_fee_rate"):
        config(max_pass_taker_fee_rate=_DecimalSubclass("0.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((assumption(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((assumption(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="market_id"):
        assumption(1, market_id=" market")
    with pytest.raises(ValueError, match="source_id"):
        assumption(1, source_id=" source")
    with pytest.raises(ValueError, match="spread_rate"):
        assumption(1, spread_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_usdc"):
        assumption(1, depth_usdc=_DecimalSubclass("1.00"))
    with pytest.raises(ValueError, match="observed_at"):
        assumption(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="reason_codes"):
        assumption(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="readonly"):
        replace(assumption(1), readonly=False)
    with pytest.raises(ValueError, match="observed_at"):
        report((assumption(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    fee_report = report((assumption(1),))

    with pytest.raises(FrozenInstanceError):
        fee_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        fee_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="total_cost_rate"):
        replace(fee_report.rows[0], total_cost_rate=d("0.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(fee_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="pass_count"):
        replace(fee_report, pass_count=d("0"))


def test_owned_module_has_no_io_mutation_or_advice_language_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_polymarket_fee_assumption_report.py"
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
        "wallet",
        "auth",
        "order",
        "buy",
        "sell",
        "long",
        "short",
        "position",
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

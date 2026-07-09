from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_cost_depth_tradeoff_report import (
    CostDepthTradeoffConfig,
    CostDepthTradeoffObservation,
    CostDepthTradeoffReport,
    CostDepthTradeoffReportDigest,
    CostDepthTradeoffRow,
    build_research_market_cost_depth_tradeoff_report,
    research_market_cost_depth_tradeoff_report_digest,
    research_market_cost_depth_tradeoff_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> CostDepthTradeoffConfig:
    values = {
        "watch_cost_pressure_threshold": d("0.040000"),
        "block_cost_pressure_threshold": d("0.080000"),
    }
    values.update(overrides)
    return CostDepthTradeoffConfig(**values)


def obs(
    index: int,
    *,
    observed_at: datetime = GENERATED_AT,
    spread: Decimal = d("0.010000"),
    fee_drag: Decimal = d("0.004000"),
    slippage_cushion: Decimal = d("0.030000"),
    near_depth: Decimal = d("1000.000000"),
    mid_depth: Decimal = d("500.000000"),
    far_depth: Decimal = d("250.000000"),
    volatility: Decimal = d("0.020000"),
    settlement_friction: Decimal = d("0.004000"),
    upstream_reason_codes: tuple[str, ...] = (),
) -> CostDepthTradeoffObservation:
    return CostDepthTradeoffObservation(
        public_case_key=f"case-{index:03d}",
        observed_at=observed_at,
        spread=spread,
        fee_drag=fee_drag,
        slippage_cushion=slippage_cushion,
        near_depth=near_depth,
        mid_depth=mid_depth,
        far_depth=far_depth,
        volatility=volatility,
        settlement_friction=settlement_friction,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(
    observations: tuple[CostDepthTradeoffObservation, ...],
    *,
    config: CostDepthTradeoffConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> CostDepthTradeoffReport:
    return build_research_market_cost_depth_tradeoff_report(
        observations,
        config=config or cfg(),
        generated_at=generated_at,
    )


def test_low_cost_deep_book_passes_with_public_decimal_payload() -> None:
    result = report((obs(2, upstream_reason_codes=("manual_depth_check",)), obs(1)))
    payload = research_market_cost_depth_tradeoff_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert type(result) is CostDepthTradeoffReport
    assert result.status == "pass"
    assert result.input_count == d("2")
    assert result.row_count == d("2")
    assert result.pass_count == d("2")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.average_cost_pressure == d("0.018000")
    assert result.min_depth_score == d("1.000000")
    assert result.reason_codes == ("cost_depth_balance_pass",)
    assert tuple(row.public_case_key for row in result.rows) == ("case-001", "case-002")
    assert result.rows[0].cost_pressure == d("0.018000")
    assert result.rows[0].depth_score == d("1.000000")
    assert result.rows[0].status == "pass"
    assert result.rows[1].reason_codes[-1] == "input_manual_depth_check"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["cost_pressure"] == "0.018000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    for forbidden in (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "http",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert forbidden not in encoded


def test_watch_case_uses_spread_fee_slippage_depth_age_volatility_and_settlement() -> None:
    result = report(
        (
            obs(
                1,
                observed_at=GENERATED_AT - timedelta(seconds=900),
                spread=d("0.012000"),
                fee_drag=d("0.006000"),
                slippage_cushion=d("0.020000"),
                near_depth=d("800.000000"),
                mid_depth=d("400.000000"),
                far_depth=d("200.000000"),
                volatility=d("0.035000"),
                settlement_friction=d("0.010000"),
            ),
        ),
    )

    row = result.rows[0]

    assert result.status == "watch"
    assert result.watch_count == d("1")
    assert row.book_age_seconds == d("900.000000")
    assert row.depth_score == d("0.800000")
    assert row.depth_gap == d("0.200000")
    assert row.slippage_shortfall == d("0.015000")
    assert row.cost_pressure == d("0.053500")
    assert row.status == "watch"
    assert row.reason_codes == (
        "cost_depth_balance_watch",
        "spread_pass",
        "fee_drag_pass",
        "slippage_shortfall_watch",
        "depth_band_pass",
        "book_age_watch",
        "volatility_pass",
        "settlement_friction_pass",
    )


def test_block_case_for_high_cost_thin_depth_stale_book_and_friction() -> None:
    result = report(
        (
            obs(
                1,
                observed_at=GENERATED_AT - timedelta(seconds=7200),
                spread=d("0.055000"),
                fee_drag=d("0.026000"),
                slippage_cushion=d("0.050000"),
                near_depth=d("100.000000"),
                mid_depth=d("50.000000"),
                far_depth=d("25.000000"),
                volatility=d("0.300000"),
                settlement_friction=d("0.060000"),
                upstream_reason_codes=("manual_cost_review",),
            ),
        ),
    )

    row = result.rows[0]

    assert result.status == "block"
    assert result.block_count == d("1")
    assert result.reason_codes[:4] == (
        "cost_depth_balance_block",
        "spread_block",
        "fee_drag_block",
        "slippage_shortfall_block",
    )
    assert row.depth_score == d("0.100000")
    assert row.depth_gap == d("0.900000")
    assert row.slippage_shortfall == d("0.250000")
    assert row.cost_pressure == d("0.437000")
    assert row.reason_codes == (
        "cost_depth_balance_block",
        "spread_block",
        "fee_drag_block",
        "slippage_shortfall_block",
        "depth_band_block",
        "book_age_block",
        "volatility_block",
        "settlement_friction_block",
        "input_manual_cost_review",
    )


def test_empty_report_blocks_with_only_allowed_status_values() -> None:
    empty = report(())

    assert empty.status == "block"
    assert empty.row_count == d("0")
    assert empty.average_cost_pressure is None
    assert empty.min_depth_score is None
    assert empty.reason_codes == ("no_cost_depth_observations",)

    with pytest.raises(ValueError, match="status"):
        replace(
            CostDepthTradeoffRow(
                public_case_key="case-x",
                observed_at=GENERATED_AT,
                spread=d("0.010000"),
                fee_drag=d("0.004000"),
                slippage_cushion=d("0.030000"),
                near_depth=d("100.000000"),
                mid_depth=d("100.000000"),
                far_depth=d("100.000000"),
                book_age_seconds=d("0"),
                volatility=d("0.020000"),
                settlement_friction=d("0.004000"),
                depth_score=d("1.000000"),
                depth_gap=d("0.000000"),
                slippage_shortfall=d("0.000000"),
                cost_pressure=d("0.018000"),
                status="pass",
                reason_codes=("cost_depth_balance_pass",),
            ),
            status="blocked",
        )


def test_payload_digest_and_digest_view_are_deterministic_and_validated() -> None:
    left = report((obs(3), obs(1), obs(2)))
    right = report((obs(2), obs(3), obs(1)))
    left_payload = research_market_cost_depth_tradeoff_report_payload(left)
    right_payload = research_market_cost_depth_tradeoff_report_payload(right)
    left_digest = research_market_cost_depth_tradeoff_report_digest(left)

    assert left_payload == right_payload
    assert left.derived_validation_digest == right.derived_validation_digest
    assert len(left.derived_validation_digest) == 64
    int(left.derived_validation_digest, 16)
    assert type(left_digest) is CostDepthTradeoffReportDigest
    assert left_digest.report_digest == left.derived_validation_digest
    assert left_digest.report_status == left.status
    assert left_digest.payload == research_market_cost_depth_tradeoff_report_payload(
        left_digest,
    )

    tampered = dict(left_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_market_cost_depth_tradeoff_report_payload(tampered)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(left, derived_validation_digest="0" * 64)

    invalid_status_payload = _with_payload_digest(
        {
            **left_payload,
            "status": "blocked",
        },
    )
    with pytest.raises(ValueError, match="status"):
        research_market_cost_depth_tradeoff_report_payload(invalid_status_payload)

    raw_identifier_payload = json.loads(json.dumps(left_payload))
    raw_identifier_payload["rows"][0]["public_case_key"] = "123456"
    with pytest.raises(ValueError, match="public_case_key"):
        research_market_cost_depth_tradeoff_report_payload(
            _with_payload_digest(raw_identifier_payload),
        )

    extra_field_payload = _with_payload_digest(
        {
            **left_payload,
            "public_note": "redacted",
        },
    )
    with pytest.raises(ValueError, match="unexpected"):
        research_market_cost_depth_tradeoff_report_payload(extra_field_payload)


def test_validation_rejects_non_decimal_subclasses_future_times_and_hard_flag_changes() -> None:
    result = report((obs(1),))

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].cost_pressure = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="spread"):
        obs(1, spread=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_drag"):
        obs(1, fee_drag=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        obs(1, observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((obs(1),), generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report((obs(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(obs(1), paper_only=False)
    with pytest.raises(ValueError, match="depth weights"):
        cfg(near_depth_weight=d("0.600000"))


def test_public_surface_rejects_sensitive_keys_values_and_raw_identifiers() -> None:
    forbidden_values = (
        ("public_case_key", "candidate-123"),
        ("public_case_key", "market_slug-alpha"),
        ("public_case_key", "question.will-event-happen"),
        ("upstream_reason_codes", ("source_url",)),
        ("upstream_reason_codes", ("wallet_review",)),
        ("upstream_reason_codes", ("buy_signal",)),
    )

    for field_name, unsafe_value in forbidden_values:
        with pytest.raises(ValueError):
            replace(obs(1), **{field_name: unsafe_value})

    payload = research_market_cost_depth_tradeoff_report_payload(report((obs(1),)))
    unsafe_payload = dict(payload)
    unsafe_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_market_cost_depth_tradeoff_report_payload(unsafe_payload)


def test_owned_module_has_no_network_persistence_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_cost_depth_tradeoff_report.py"
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
        "private_key",
        "place_order",
        "order_size",
        "trade_recommendation",
        "live_trading",
        "connect(",
        "open(",
    )

    assert all(term not in source for term in forbidden_terms)


def _with_payload_digest(payload: dict[str, object]) -> dict[str, object]:
    values = json.loads(json.dumps(payload))
    values.pop("derived_validation_digest", None)
    canonical = json.dumps(
        values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    values["derived_validation_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
    return values


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

from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_orderbook_cost_resolution_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_ORDERBOOK_COST_RESOLUTION_READINESS_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_depth_stability_ratio": d("0.800000"),
        "minimum_watch_depth_stability_ratio": d("0.500000"),
        "maximum_pass_spread_ratio": d("0.020000"),
        "maximum_watch_spread_ratio": d("0.060000"),
        "maximum_pass_fee_drag_ratio": d("0.010000"),
        "maximum_watch_fee_drag_ratio": d("0.030000"),
        "maximum_pass_slippage_pressure_ratio": d("0.020000"),
        "maximum_watch_slippage_pressure_ratio": d("0.080000"),
        "maximum_pass_settlement_friction_ratio": d("0.100000"),
        "maximum_watch_settlement_friction_ratio": d("0.300000"),
        "maximum_pass_resolution_window_risk_ratio": d("0.100000"),
        "maximum_watch_resolution_window_risk_ratio": d("0.400000"),
        "depth_stability_weight": d("0.250000"),
        "spread_weight": d("0.200000"),
        "fee_drag_weight": d("0.150000"),
        "slippage_pressure_weight": d("0.200000"),
        "settlement_friction_weight": d("0.100000"),
        "resolution_window_weight": d("0.100000"),
        "minimum_pass_readiness_score": d("0.750000"),
        "minimum_watch_readiness_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchMarketOrderbookCostResolutionReadinessConfig(**values)


def readiness_input(
    public_readiness_ref: str = "readiness-pass",
    *,
    observed_at: datetime | None = None,
    depth_stability_ratio: Decimal = d("0.900000"),
    spread_ratio: Decimal = d("0.010000"),
    fee_drag_ratio: Decimal = d("0.005000"),
    slippage_pressure_ratio: Decimal = d("0.010000"),
    settlement_friction_ratio: Decimal = d("0.050000"),
    resolution_window_risk_ratio: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketOrderbookCostResolutionReadinessInput(
        public_readiness_ref=public_readiness_ref,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(seconds=30)
        ),
        depth_stability_ratio=depth_stability_ratio,
        spread_ratio=spread_ratio,
        fee_drag_ratio=fee_drag_ratio,
        slippage_pressure_ratio=slippage_pressure_ratio,
        settlement_friction_ratio=settlement_friction_ratio,
        resolution_window_risk_ratio=resolution_window_risk_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_orderbook_cost_resolution_readiness_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for key, item in value.items():
            values.append(key)
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def digest_source(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }


def payload_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            digest_source(payload),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def test_scores_pass_watch_and_block_sanitized_book_readiness_rows() -> None:
    module = api()

    combined = report(
        readiness_input(
            "alpha-block",
            observed_at=GENERATED_AT - timedelta(seconds=90),
            depth_stability_ratio=d("0.200000"),
            spread_ratio=d("0.080000"),
            fee_drag_ratio=d("0.040000"),
            slippage_pressure_ratio=d("0.100000"),
            settlement_friction_ratio=d("0.350000"),
            resolution_window_risk_ratio=d("0.500000"),
            reason_codes=("manual_depth_review",),
        ),
        readiness_input("beta-pass"),
        readiness_input(
            "gamma-watch",
            depth_stability_ratio=d("0.650000"),
            spread_ratio=d("0.040000"),
            fee_drag_ratio=d("0.020000"),
            slippage_pressure_ratio=d("0.050000"),
            settlement_friction_ratio=d("0.200000"),
            resolution_window_risk_ratio=d("0.250000"),
        ),
    )

    assert module.ORDERBOOK_COST_RESOLUTION_READINESS_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert type(combined) is module.ResearchMarketOrderbookCostResolutionReadinessReport
    assert is_dataclass(combined)
    assert combined.status == "block"
    assert combined.input_count == d("3.000000")
    assert combined.row_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.average_readiness_score == d("0.500000")
    assert combined.min_depth_stability_ratio == d("0.200000")
    assert combined.max_spread_ratio == d("0.080000")
    assert combined.max_fee_drag_ratio == d("0.040000")
    assert combined.max_slippage_pressure_ratio == d("0.100000")
    assert combined.max_settlement_friction_ratio == d("0.350000")
    assert combined.max_resolution_window_risk_ratio == d("0.500000")
    assert combined.reason_codes == (
        "book_readiness_block",
        "depth_stability_block",
        "spread_width_block",
        "fee_drag_block",
        "slippage_pressure_block",
        "settlement_friction_block",
        "resolution_window_block",
        "depth_stability_watch",
        "spread_width_watch",
        "fee_drag_watch",
        "slippage_pressure_watch",
        "settlement_friction_watch",
        "resolution_window_watch",
    )

    block_row, pass_row, watch_row = combined.rows
    assert tuple(row.public_readiness_ref for row in combined.rows) == (
        "alpha-block",
        "beta-pass",
        "gamma-watch",
    )
    assert tuple(row.status for row in combined.rows) == ("block", "pass", "watch")

    assert block_row.depth_stability_score == d("0.000000")
    assert block_row.spread_score == d("0.000000")
    assert block_row.fee_drag_score == d("0.000000")
    assert block_row.slippage_pressure_score == d("0.000000")
    assert block_row.settlement_friction_score == d("0.000000")
    assert block_row.resolution_window_score == d("0.000000")
    assert block_row.readiness_score == d("0.000000")
    assert block_row.reason_codes == (
        "book_readiness_block",
        "depth_stability_block",
        "fee_drag_block",
        "input_manual_depth_review",
        "resolution_window_block",
        "settlement_friction_block",
        "slippage_pressure_block",
        "spread_width_block",
    )

    assert pass_row.readiness_score == d("1.000000")
    assert pass_row.status == "pass"
    assert "book_readiness_pass" in pass_row.reason_codes
    assert "depth_stability_pass" in pass_row.reason_codes

    assert watch_row.depth_stability_score == d("0.500000")
    assert watch_row.spread_score == d("0.500000")
    assert watch_row.fee_drag_score == d("0.500000")
    assert watch_row.slippage_pressure_score == d("0.500000")
    assert watch_row.settlement_friction_score == d("0.500000")
    assert watch_row.resolution_window_score == d("0.500000")
    assert watch_row.readiness_score == d("0.500000")
    assert watch_row.status == "watch"

    with pytest.raises(FrozenInstanceError):
        combined.rows[0].status = "pass"  # type: ignore[misc]


def test_depth_and_cost_thresholds_drive_watch_and_block_states() -> None:
    threshold = report(
        readiness_input(
            "exact-pass",
            depth_stability_ratio=d("0.800000"),
            spread_ratio=d("0.020000"),
            fee_drag_ratio=d("0.010000"),
            slippage_pressure_ratio=d("0.020000"),
            settlement_friction_ratio=d("0.100000"),
            resolution_window_risk_ratio=d("0.100000"),
        ),
        readiness_input(
            "spread-watch",
            spread_ratio=d("0.040000"),
        ),
        readiness_input(
            "depth-block",
            depth_stability_ratio=d("0.499999"),
        ),
        readiness_input(
            "cost-block",
            fee_drag_ratio=d("0.030001"),
        ),
    )

    rows = {row.public_readiness_ref: row for row in threshold.rows}
    assert rows["exact-pass"].status == "pass"
    assert rows["exact-pass"].readiness_score == d("1.000000")
    assert rows["spread-watch"].status == "watch"
    assert rows["spread-watch"].spread_score == d("0.500000")
    assert "spread_width_watch" in rows["spread-watch"].reason_codes
    assert rows["depth-block"].status == "block"
    assert "depth_stability_block" in rows["depth-block"].reason_codes
    assert rows["cost-block"].status == "block"
    assert "fee_drag_block" in rows["cost-block"].reason_codes


def test_public_payload_digest_is_deterministic_and_validated() -> None:
    module = api()

    left = report(
        readiness_input("gamma-watch", spread_ratio=d("0.040000")),
        readiness_input("alpha-pass"),
    )
    right = report(
        readiness_input("alpha-pass"),
        readiness_input("gamma-watch", spread_ratio=d("0.040000")),
    )

    left_payload = module.research_market_orderbook_cost_resolution_readiness_report_payload(
        left,
    )
    right_payload = module.research_market_orderbook_cost_resolution_readiness_report_payload(
        right,
    )

    assert left_payload == right_payload
    assert left.derived_validation_digest == right.derived_validation_digest
    assert left.derived_validation_digest == payload_digest(left_payload)
    assert module.research_market_orderbook_cost_resolution_readiness_report_digest(
        left,
    ) == left.derived_validation_digest
    assert len(left.derived_validation_digest) == 64
    int(left.derived_validation_digest, 16)

    tampered = dict(left_payload)
    tampered["pass_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_orderbook_cost_resolution_readiness_report_payload(tampered)


def test_public_payload_contains_only_sanitized_report_fields() -> None:
    module = api()
    payload = module.research_market_orderbook_cost_resolution_readiness_report_payload(
        report(readiness_input("safe-public-ref")),
    )
    payload_text = json.dumps(payload, sort_keys=True).lower()

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_payload_values(payload))
    for forbidden in (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommend",
        "execution",
        "live",
        "://",
    ):
        assert forbidden not in payload_text

    with pytest.raises(ValueError):
        readiness_input("market_id_001")
    with pytest.raises(ValueError):
        readiness_input("safe-ref", reason_codes=("wallet_surface",))
    unsafe_payload = dict(payload)
    unsafe_payload["rows"] = [dict(payload["rows"][0], readonly=False)]
    with pytest.raises(ValueError, match="readonly"):
        module.research_market_orderbook_cost_resolution_readiness_report_payload(
            unsafe_payload,
        )


def test_custom_config_validation_and_decimal_only_inputs() -> None:
    stricter = config(
        maximum_pass_spread_ratio=d("0.005000"),
        maximum_watch_spread_ratio=d("0.015000"),
    )
    stricter_report = report(
        readiness_input("strict-spread-watch", spread_ratio=d("0.010000")),
        cfg=stricter,
    )

    assert stricter_report.rows[0].status == "watch"
    assert "spread_width_watch" in stricter_report.rows[0].reason_codes

    with pytest.raises(ValueError, match="maximum_pass_spread_ratio"):
        config(
            maximum_pass_spread_ratio=d("0.070000"),
            maximum_watch_spread_ratio=d("0.060000"),
        )
    with pytest.raises(ValueError, match="weights must sum to 1"):
        config(depth_stability_weight=d("0.260000"))
    with pytest.raises(ValueError, match="Decimal"):
        readiness_input("float-cost", spread_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        readiness_input(
            "decimal-subclass",
            spread_ratio=DecimalSubclass("0.010000"),
        )
    with pytest.raises(ValueError, match="datetime"):
        readiness_input(
            "datetime-subclass",
            observed_at=DatetimeSubclass(2026, 7, 9, 11, 59, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_empty_report_blocks_without_leaking_private_surfaces() -> None:
    module = api()
    empty = report()

    assert empty.status == "block"
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.average_readiness_score is None
    assert empty.rows == ()
    assert empty.reason_codes == ("no_book_readiness_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketOrderbookCostResolutionReadinessReasonCodeCount(
            reason_code="no_book_readiness_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )

    replaced = dict(
        module.research_market_orderbook_cost_resolution_readiness_report_payload(empty),
        derived_validation_digest="0" * 64,
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_orderbook_cost_resolution_readiness_report_payload(replaced)

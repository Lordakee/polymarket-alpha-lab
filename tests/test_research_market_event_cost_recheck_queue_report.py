from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_event_cost_recheck_queue_report import (
    ResearchMarketEventCostRecheckObservation,
    ResearchMarketEventCostRecheckQueueConfig,
    ResearchMarketEventCostRecheckQueueReasonCodeCount,
    ResearchMarketEventCostRecheckQueueReport,
    ResearchMarketEventCostRecheckQueueRow,
    build_research_market_event_cost_recheck_queue_report,
    research_market_event_cost_recheck_queue_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 6, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedObservationShape:
    event_bucket: str
    cost_surface_bucket: str
    observed_at: datetime
    spread_drift_bps: Decimal
    depth_fade_ratio: Decimal
    quote_age_seconds: Decimal
    fee_friction_bps: Decimal
    catalyst_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketEventCostRecheckQueueConfig:
    values = {
        "watch_spread_drift_bps": d("10.000000"),
        "block_spread_drift_bps": d("50.000000"),
        "watch_depth_fade_ratio": d("0.150000"),
        "block_depth_fade_ratio": d("0.600000"),
        "watch_quote_age_seconds": d("300.000000"),
        "block_quote_age_seconds": d("900.000000"),
        "watch_fee_friction_bps": d("5.000000"),
        "block_fee_friction_bps": d("25.000000"),
        "watch_catalyst_pressure": d("0.350000"),
        "block_catalyst_pressure": d("0.850000"),
        "watch_aggregate_recheck_pressure": d("0.350000"),
        "block_aggregate_recheck_pressure": d("0.700000"),
    }
    values.update(overrides)
    return ResearchMarketEventCostRecheckQueueConfig(**values)


def observation(
    event_bucket: str,
    cost_surface_bucket: str,
    *,
    spread_drift_bps: Decimal = d("2.000000"),
    depth_fade_ratio: Decimal = d("0.050000"),
    quote_age_seconds: Decimal = d("60.000000"),
    fee_friction_bps: Decimal = d("1.000000"),
    catalyst_pressure: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketEventCostRecheckObservation:
    return ResearchMarketEventCostRecheckObservation(
        event_bucket=event_bucket,
        cost_surface_bucket=cost_surface_bucket,
        observed_at=GENERATED_AT,
        spread_drift_bps=spread_drift_bps,
        depth_fade_ratio=depth_fade_ratio,
        quote_age_seconds=quote_age_seconds,
        fee_friction_bps=fee_friction_bps,
        catalyst_pressure=catalyst_pressure,
        reason_codes=reason_codes,
    )


def report(
    observations: tuple[object, ...],
    *,
    cfg: ResearchMarketEventCostRecheckQueueConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketEventCostRecheckQueueReport:
    return build_research_market_event_cost_recheck_queue_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_queue_snapshot() -> None:
    queue_report = report(())

    assert type(queue_report) is ResearchMarketEventCostRecheckQueueReport
    assert queue_report.generated_at == GENERATED_AT
    assert queue_report.item_count == d("0")
    assert queue_report.queued_recheck_count == d("0")
    assert queue_report.pass_count == d("0")
    assert queue_report.watch_count == d("0")
    assert queue_report.block_count == d("0")
    assert queue_report.average_aggregate_recheck_pressure is None
    assert queue_report.max_aggregate_recheck_pressure is None
    assert queue_report.status == "block"
    assert queue_report.reason_codes == ("no_cost_recheck_candidates",)
    assert queue_report.reason_code_counts == (
        ResearchMarketEventCostRecheckQueueReasonCodeCount(
            reason_code="no_cost_recheck_candidates",
            count=d("1"),
        ),
    )
    assert queue_report.rows == ()
    assert queue_report.paper_only is True
    assert queue_report.report_only is True
    assert queue_report.readonly is True
    assert len(queue_report.payload_digest) == 64


def test_spread_depth_quote_fee_and_catalyst_pressure_drive_queue_statuses() -> None:
    queue_report = report(
        (
            SuppliedObservationShape(
                event_bucket="gamma",
                cost_surface_bucket="late-wide-thin",
                observed_at=GENERATED_AT,
                spread_drift_bps=d("60.000000"),
                depth_fade_ratio=d("0.700000"),
                quote_age_seconds=d("1000.000000"),
                fee_friction_bps=d("30.000000"),
                catalyst_pressure=d("0.900000"),
                reason_codes=("manual_recheck",),
            ),
            observation("alpha", "stable"),
            observation(
                "beta",
                "fading",
                spread_drift_bps=d("15.000000"),
                depth_fade_ratio=d("0.200000"),
                quote_age_seconds=d("400.000000"),
                fee_friction_bps=d("8.000000"),
                catalyst_pressure=d("0.400000"),
            ),
        ),
    )

    assert queue_report.status == "block"
    assert queue_report.item_count == d("3")
    assert queue_report.queued_recheck_count == d("2")
    assert queue_report.pass_count == d("1")
    assert queue_report.watch_count == d("1")
    assert queue_report.block_count == d("1")
    assert queue_report.average_aggregate_recheck_pressure == d("0.481067")
    assert queue_report.max_aggregate_recheck_pressure == d("1.000000")
    assert tuple(row.queue_item_digest for row in queue_report.rows) == tuple(
        sorted(row.queue_item_digest for row in queue_report.rows),
    )

    pass_row = next(row for row in queue_report.rows if row.status == "pass")
    watch_row = next(row for row in queue_report.rows if row.status == "watch")
    block_row = next(row for row in queue_report.rows if row.status == "block")

    assert type(pass_row) is ResearchMarketEventCostRecheckQueueRow
    assert pass_row.recheck_required is False
    assert pass_row.aggregate_recheck_pressure == d("0.069529")
    assert pass_row.reason_codes == ("aggregate_recheck_pressure_pass",)

    assert watch_row.recheck_required is True
    assert watch_row.aggregate_recheck_pressure == d("0.373673")
    assert watch_row.reason_codes == (
        "spread_drift_watch",
        "depth_fade_watch",
        "quote_age_watch",
        "fee_friction_watch",
        "catalyst_pressure_watch",
        "aggregate_recheck_pressure_watch",
    )

    assert block_row.recheck_required is True
    assert block_row.spread_drift_pressure == d("1.000000")
    assert block_row.depth_fade_pressure == d("1.000000")
    assert block_row.quote_age_pressure == d("1.000000")
    assert block_row.fee_friction_pressure == d("1.000000")
    assert block_row.catalyst_pressure_score == d("1.000000")
    assert block_row.aggregate_recheck_pressure == d("1.000000")
    assert block_row.reason_codes == (
        "spread_drift_block",
        "depth_fade_block",
        "quote_age_block",
        "fee_friction_block",
        "catalyst_pressure_block",
        "aggregate_recheck_pressure_block",
        "input_manual_recheck",
    )


def test_payload_is_deterministic_json_safe_and_redacts_raw_identifiers() -> None:
    first = report(
        (
            observation("beta", "fading", spread_drift_bps=d("15.000000")),
            observation("alpha", "stable"),
        ),
    )
    second = report(
        (
            observation("alpha", "stable"),
            observation("beta", "fading", spread_drift_bps=d("15.000000")),
        ),
    )

    payload = research_market_event_cost_recheck_queue_report_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == research_market_event_cost_recheck_queue_report_payload(second)
    assert payload["payload_digest"] == first.payload_digest == second.payload_digest
    assert payload["generated_at"] == "2026-07-08T06:00:00+00:00"
    assert payload["rows"][0]["queue_item_digest"] == min(
        row.queue_item_digest for row in first.rows
    )
    assert not any(
        type(value) is float or type(value) is int
        for value in _walk_payload_values(payload)
    )
    lowered = encoded.lower()
    for forbidden in (
        "event_bucket",
        "cost_surface_bucket",
        "market_id",
        "market_slug",
        "condition_id",
        "source_id",
        "source_url",
        "question",
        "buy",
        "sell",
        "recommend",
    ):
        assert forbidden not in lowered


def test_payload_rejects_raw_identity_fields_and_false_phase_flags() -> None:
    queue_report = report((observation("alpha", "stable"),))
    payload = research_market_event_cost_recheck_queue_report_payload(queue_report)

    with pytest.raises(ValueError, match="market_id"):
        research_market_event_cost_recheck_queue_report_payload(
            {**payload, "market_id": "raw-market"},
        )
    with pytest.raises(ValueError, match="source_id"):
        research_market_event_cost_recheck_queue_report_payload(
            {**payload, "rows": [{**payload["rows"][0], "source_id": "raw-source"}]},
        )
    with pytest.raises(ValueError, match="paper_only"):
        research_market_event_cost_recheck_queue_report_payload(
            {**payload, "paper_only": False},
        )


def test_validation_rejects_bad_numeric_types_thresholds_terms_and_flags() -> None:
    with pytest.raises(ValueError, match="watch_spread_drift_bps"):
        config(watch_spread_drift_bps=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_drift_bps"):
        observation("alpha", "stable", spread_drift_bps=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="block_spread_drift_bps"):
        config(block_spread_drift_bps=d("5.000000"))
    with pytest.raises(ValueError, match="block_depth_fade_ratio"):
        config(block_depth_fade_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation("alpha", "stable"),), generated_at=datetime(2026, 7, 8, 6, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation("alpha", "stable"),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 6, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="event_bucket"):
        observation("https://raw.example", "stable")
    with pytest.raises(ValueError, match="cost_surface_bucket"):
        observation("alpha", "bad bucket")
    with pytest.raises(ValueError, match="depth_fade_ratio"):
        observation("alpha", "stable", depth_fade_ratio=d("-0.010000"))
    with pytest.raises(ValueError, match="quote_age_seconds"):
        observation("alpha", "stable", quote_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        observation("alpha", "stable", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation("alpha", "stable"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    queue_report = report((observation("alpha", "stable"),))

    with pytest.raises(FrozenInstanceError):
        queue_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        queue_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="recheck_required"):
        replace(queue_report.rows[0], recheck_required=True)
    with pytest.raises(ValueError, match="payload_digest"):
        replace(queue_report, payload_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(queue_report, status="watch")


def test_owned_module_has_no_io_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_event_cost_recheck_queue_report.py"
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
        "sqlalchemy",
        "psycopg",
        "pathlib",
        "open(",
        ".write(",
        "connect(",
        "wallet",
        "private_key",
        "auth",
        "place_order",
        "cancel_order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "sizing",
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

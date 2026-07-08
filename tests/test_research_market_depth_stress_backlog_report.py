from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_depth_stress_backlog_report import (
    ResearchMarketDepthStressBacklogConfig,
    ResearchMarketDepthStressBacklogInput,
    ResearchMarketDepthStressBacklogReasonCodeCount,
    ResearchMarketDepthStressBacklogReport,
    ResearchMarketDepthStressBacklogRow,
    build_research_market_depth_stress_backlog_report,
    research_market_depth_stress_backlog_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedDepthStressShape:
    public_check_id: str
    aggregate_depth_fade: Decimal
    spread_widening: Decimal
    quote_age_seconds: Decimal
    fee_friction: Decimal
    catalyst_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketDepthStressBacklogConfig:
    values = {
        "watch_stress_threshold": d("0.350000"),
        "block_stress_threshold": d("0.700000"),
        "fresh_quote_age_seconds": d("60"),
        "stale_quote_age_seconds": d("900"),
        "aggregate_depth_fade_weight": d("0.300000"),
        "spread_widening_weight": d("0.250000"),
        "quote_age_weight": d("0.200000"),
        "fee_friction_weight": d("0.150000"),
        "catalyst_pressure_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchMarketDepthStressBacklogConfig(**values)


def stress_item(
    public_check_id: str = "check-a",
    *,
    aggregate_depth_fade: Decimal = d("0.050000"),
    spread_widening: Decimal = d("0.020000"),
    quote_age_seconds: Decimal = d("30"),
    fee_friction: Decimal = d("0.050000"),
    catalyst_pressure: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketDepthStressBacklogInput:
    return ResearchMarketDepthStressBacklogInput(
        public_check_id=public_check_id,
        aggregate_depth_fade=aggregate_depth_fade,
        spread_widening=spread_widening,
        quote_age_seconds=quote_age_seconds,
        fee_friction=fee_friction,
        catalyst_pressure=catalyst_pressure,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchMarketDepthStressBacklogConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketDepthStressBacklogReport:
    return build_research_market_depth_stress_backlog_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_pass_report_with_digest() -> None:
    depth_report = report(())

    assert type(depth_report) is ResearchMarketDepthStressBacklogReport
    assert depth_report.generated_at == GENERATED_AT
    assert depth_report.check_count == d("0")
    assert depth_report.pass_count == d("0")
    assert depth_report.watch_count == d("0")
    assert depth_report.block_count == d("0")
    assert depth_report.average_depth_stress_pressure is None
    assert depth_report.max_quote_age_seconds == d("0")
    assert depth_report.max_aggregate_depth_fade == d("0.000000")
    assert depth_report.status == "pass"
    assert depth_report.reason_codes == ("no_depth_stress_backlog_items",)
    assert depth_report.reason_code_counts == (
        ResearchMarketDepthStressBacklogReasonCodeCount(
            reason_code="no_depth_stress_backlog_items",
            count=d("1"),
        ),
    )
    assert depth_report.rows == ()
    assert len(depth_report.derived_validation_digest) == 64
    assert depth_report.paper_only is True
    assert depth_report.report_only is True
    assert depth_report.readonly is True


def test_backlog_scores_depth_fade_spread_quote_age_fees_and_catalysts() -> None:
    depth_report = report(
        (
            stress_item(
                "check-c",
                aggregate_depth_fade=d("0.900000"),
                spread_widening=d("0.800000"),
                quote_age_seconds=d("1200"),
                fee_friction=d("0.900000"),
                catalyst_pressure=d("0.800000"),
                reason_codes=("manual_public_review",),
            ),
            stress_item(),
            stress_item(
                "check-b",
                aggregate_depth_fade=d("0.400000"),
                spread_widening=d("0.500000"),
                quote_age_seconds=d("480"),
                fee_friction=d("0.300000"),
                catalyst_pressure=d("0.600000"),
            ),
        ),
    )

    assert tuple(row.public_check_id for row in depth_report.rows) == (
        "check-a",
        "check-b",
        "check-c",
    )
    assert depth_report.status == "block"
    assert depth_report.check_count == d("3")
    assert depth_report.pass_count == d("1")
    assert depth_report.watch_count == d("1")
    assert depth_report.block_count == d("1")
    assert depth_report.average_depth_stress_pressure == d("0.457500")
    assert depth_report.max_quote_age_seconds == d("1200")
    assert depth_report.max_aggregate_depth_fade == d("0.900000")

    pass_row, watch_row, block_row = depth_report.rows
    assert type(pass_row) is ResearchMarketDepthStressBacklogRow
    assert pass_row.quote_age_pressure == d("0.000000")
    assert pass_row.depth_stress_pressure == d("0.037500")
    assert pass_row.status == "pass"
    assert watch_row.quote_age_pressure == d("0.500000")
    assert watch_row.depth_stress_pressure == d("0.450000")
    assert watch_row.status == "watch"
    assert block_row.quote_age_pressure == d("1.000000")
    assert block_row.depth_stress_pressure == d("0.885000")
    assert block_row.status == "block"
    assert "input_manual_public_review" in block_row.reason_codes
    assert depth_report.reason_code_counts == tuple(
        sorted(depth_report.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    rows = (
        SuppliedDepthStressShape(
            public_check_id="check-b",
            aggregate_depth_fade=d("0.400000"),
            spread_widening=d("0.500000"),
            quote_age_seconds=d("480"),
            fee_friction=d("0.300000"),
            catalyst_pressure=d("0.600000"),
            reason_codes=("public_depth_recheck",),
        ),
        stress_item("check-a"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_market_depth_stress_backlog_report_payload(first_report)
    second_payload = research_market_depth_stress_backlog_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["depth_stress_pressure"] == "0.037500"
    assert first_payload["rows"][1]["quote_age_pressure"] == "0.500000"
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
            "order",
            "trade",
            "live",
            "recommendation",
            "sizing",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="aggregate_depth_fade_weight"):
        config(aggregate_depth_fade_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_stress_threshold"):
        config(block_stress_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="fresh_quote_age_seconds"):
        config(fresh_quote_age_seconds=60)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_widening_weight"):
        config(spread_widening_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((stress_item(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (stress_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_check_id"):
        stress_item(public_check_id="check url")
    with pytest.raises(ValueError, match="public_check_id"):
        stress_item(public_check_id="raw-market-alpha")
    with pytest.raises(ValueError, match="quote_age_seconds"):
        stress_item(quote_age_seconds=480)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="aggregate_depth_fade"):
        stress_item(aggregate_depth_fade=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        stress_item(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(stress_item(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    depth_report = report((stress_item(),))

    with pytest.raises(FrozenInstanceError):
        depth_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        depth_report.rows[0].depth_stress_pressure = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(depth_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(depth_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="check_count"):
        replace(depth_report, check_count=d("2"))


def test_owned_module_has_no_filesystem_network_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_stress_backlog_report.py"
    )
    module_text = module_path.read_text(encoding="utf-8").lower()
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
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    )

    assert all(term not in module_text for term in forbidden_terms)


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

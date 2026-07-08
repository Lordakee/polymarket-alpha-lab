from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_fee_cost_quality_report import (
    COST_INPUT_QUALITY_STATUSES,
    DEFAULT_RESEARCH_MARKET_FEE_COST_QUALITY_REPORT_CONFIG_VERSION,
    ResearchMarketFeeCostQualityConfig,
    ResearchMarketFeeCostQualityInput,
    ResearchMarketFeeCostQualityReasonCodeCount,
    ResearchMarketFeeCostQualityReport,
    ResearchMarketFeeCostQualityRow,
    build_research_market_fee_cost_quality_report,
    research_market_fee_cost_quality_report_digest,
    research_market_fee_cost_quality_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketFeeCostQualityConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_FEE_COST_QUALITY_REPORT_CONFIG_VERSION
        ),
        "max_pass_fee_assumption_rate": d("0.020000"),
        "max_watch_fee_assumption_rate": d("0.040000"),
        "max_pass_spread_drag_rate": d("0.010000"),
        "max_watch_spread_drag_rate": d("0.030000"),
        "max_pass_settlement_friction_rate": d("0.005000"),
        "max_watch_settlement_friction_rate": d("0.020000"),
        "min_pass_depth_confidence": d("0.800000"),
        "min_watch_depth_confidence": d("0.550000"),
        "max_pass_cost_input_age_seconds": d("43200.000000"),
        "max_watch_cost_input_age_seconds": d("172800.000000"),
    }
    values.update(overrides)
    return ResearchMarketFeeCostQualityConfig(**values)


def input_row(
    research_key: str = "fee-cost-case-pass",
    *,
    fee_assumption_rate: Decimal = d("0.010000"),
    spread_drag_rate: Decimal = d("0.006000"),
    settlement_friction_rate: Decimal = d("0.002000"),
    depth_confidence: Decimal = d("0.900000"),
    cost_input_age_seconds: Decimal = d("21600.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketFeeCostQualityInput:
    return ResearchMarketFeeCostQualityInput(
        research_key=research_key,
        fee_assumption_rate=fee_assumption_rate,
        spread_drag_rate=spread_drag_rate,
        settlement_friction_rate=settlement_friction_rate,
        depth_confidence=depth_confidence,
        cost_input_age_seconds=cost_input_age_seconds,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchMarketFeeCostQualityInput,
    cfg: ResearchMarketFeeCostQualityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketFeeCostQualityReport:
    return build_research_market_fee_cost_quality_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_manual_fee_cost_review() -> None:
    quality = report()

    assert type(quality) is ResearchMarketFeeCostQualityReport
    assert is_dataclass(quality)
    assert COST_INPUT_QUALITY_STATUSES == ("pass", "watch", "block")
    assert quality.generated_at == GENERATED_AT
    assert quality.config_version == "research-market-fee-cost-quality-report-v0"
    assert quality.input_count == ZERO
    assert quality.pass_count == ZERO
    assert quality.watch_count == ZERO
    assert quality.block_count == ZERO
    assert quality.average_cost_input_quality_score is None
    assert quality.max_fee_assumption_rate == ZERO
    assert quality.max_spread_drag_rate == ZERO
    assert quality.max_settlement_friction_rate == ZERO
    assert quality.min_depth_confidence == ZERO
    assert quality.max_stale_cost_input_risk == ZERO
    assert quality.status == "block"
    assert quality.reason_codes == ("no_fee_cost_inputs",)
    assert quality.reason_code_counts == (
        ResearchMarketFeeCostQualityReasonCodeCount(
            reason_code="no_fee_cost_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert quality.rows == ()
    assert quality.paper_only is True
    assert quality.report_only is True
    assert quality.readonly is True


def test_fee_cost_quality_scores_pass_watch_and_block_inputs() -> None:
    quality = report(
        input_row(
            "fee-cost-case-watch",
            fee_assumption_rate=d("0.030000"),
            spread_drag_rate=d("0.020000"),
            settlement_friction_rate=d("0.010000"),
            depth_confidence=d("0.700000"),
            cost_input_age_seconds=d("86400.000000"),
        ),
        input_row(
            "fee-cost-case-block",
            fee_assumption_rate=d("0.060000"),
            spread_drag_rate=d("0.050000"),
            settlement_friction_rate=d("0.030000"),
            depth_confidence=d("0.400000"),
            cost_input_age_seconds=d("250000.000000"),
            reason_codes=("manual_cost_escalation",),
        ),
        input_row("fee-cost-case-pass", reason_codes=("manual_check_complete",)),
    )

    assert quality.input_count == d("3.000000")
    assert quality.pass_count == d("1.000000")
    assert quality.watch_count == d("1.000000")
    assert quality.block_count == d("1.000000")
    assert quality.average_cost_input_quality_score == d("0.810467")
    assert quality.max_fee_assumption_rate == d("0.060000")
    assert quality.max_spread_drag_rate == d("0.050000")
    assert quality.max_settlement_friction_rate == d("0.030000")
    assert quality.min_depth_confidence == d("0.400000")
    assert quality.max_stale_cost_input_risk == d("1.000000")
    assert quality.status == "block"
    assert quality.reason_codes == (
        "market_fee_cost_quality_block",
        "fee_assumption_block",
        "spread_drag_block",
        "settlement_friction_block",
        "depth_confidence_block",
        "stale_cost_input_block",
        "fee_assumption_watch",
        "spread_drag_watch",
        "settlement_friction_watch",
        "depth_confidence_watch",
        "stale_cost_input_watch",
    )

    block_row, pass_row, watch_row = quality.rows
    assert type(block_row) is ResearchMarketFeeCostQualityRow
    assert tuple(row.research_key for row in quality.rows) == (
        "fee-cost-case-block",
        "fee-cost-case-pass",
        "fee-cost-case-watch",
    )
    assert block_row.cost_input_quality_score == d("0.652000")
    assert block_row.stale_cost_input_risk == d("1.000000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "depth_confidence_block",
        "fee_assumption_block",
        "input_manual_cost_escalation",
        "manual_review_fee_cost_inputs_block",
        "market_fee_cost_quality_block",
        "settlement_friction_block",
        "spread_drag_block",
        "stale_cost_input_block",
    )
    assert pass_row.cost_input_quality_score == d("0.951400")
    assert pass_row.stale_cost_input_risk == d("0.125000")
    assert pass_row.status == "pass"
    assert "market_fee_cost_quality_pass" in pass_row.reason_codes
    assert "input_manual_check_complete" in pass_row.reason_codes
    assert watch_row.cost_input_quality_score == d("0.828000")
    assert watch_row.stale_cost_input_risk == d("0.500000")
    assert watch_row.status == "watch"
    assert "fee_assumption_watch" in watch_row.reason_codes
    assert "spread_drag_watch" in watch_row.reason_codes
    assert "settlement_friction_watch" in watch_row.reason_codes
    assert "depth_confidence_watch" in watch_row.reason_codes
    assert "stale_cost_input_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    first = report(
        input_row("fee-cost-case-z", reason_codes=("zeta", "alpha")),
        input_row("fee-cost-case-a"),
    )
    second = report(
        input_row("fee-cost-case-a"),
        input_row("fee-cost-case-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = research_market_fee_cost_quality_report_payload(first)
    second_payload = research_market_fee_cost_quality_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert research_market_fee_cost_quality_report_digest(first) == (
        research_market_fee_cost_quality_report_digest(second)
    )
    assert len(research_market_fee_cost_quality_report_digest(first)) == 64
    assert first_payload["rows"][0]["cost_input_quality_score"] == "0.951400"
    assert first_payload["rows"][0]["fee_assumption_rate"] == "0.010000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_rows() -> None:
    populated = report(input_row())

    for value in (config(), input_row(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_rate",
                    "_friction",
                    "_confidence",
                    "_seconds",
                    "_risk",
                    "_ratio",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].cost_input_quality_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_pass_fee_assumption_rate"):
        config(max_pass_fee_assumption_rate=0.02)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_watch_fee_assumption_rate"):
        config(max_watch_fee_assumption_rate=_DecimalSubclass("0.040000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 14, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=_DatetimeSubclass(2026, 7, 8, 14, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" fee-cost-case-pass")
    with pytest.raises(ValueError, match="research_key"):
        input_row("raw-fee-cost-case")
    with pytest.raises(ValueError, match="fee_assumption_rate"):
        input_row(fee_assumption_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_drag_rate"):
        input_row(spread_drag_rate=d("1.100000"))
    with pytest.raises(ValueError, match="cost_input_age_seconds"):
        input_row(cost_input_age_seconds=-d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="cost_input_quality_score"):
        replace(populated.rows[0], cost_input_quality_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="report"):
        research_market_fee_cost_quality_report_payload(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="report_only"):
        research_market_fee_cost_quality_report_payload(replace(populated, report_only=False))


def test_owned_module_has_no_side_effect_or_decision_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_fee_cost_quality_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
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
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )

    assert all(term not in text for term in forbidden_terms)


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


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_public_surface_key(key: str) -> bool:
    return key in {
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "source_text",
        "source_url",
        "source_reference",
        "raw_text",
    }

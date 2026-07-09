from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json

import pytest

from polymarket_alpha_lab.research_strategy_cost_confidence_frontier_report import (
    ResearchStrategyCostConfidenceFrontierConfig,
    ResearchStrategyCostConfidenceFrontierInput,
    ResearchStrategyCostConfidenceFrontierReasonCodeCount,
    ResearchStrategyCostConfidenceFrontierReport,
    ResearchStrategyCostConfidenceFrontierRow,
    build_research_strategy_cost_confidence_frontier_report,
    research_strategy_cost_confidence_frontier_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyCostConfidenceFrontierConfig:
    values = {
        "config_version": "research-strategy-cost-confidence-frontier-report-v0",
        "pass_min_confidence": d("0.750000"),
        "watch_min_confidence": d("0.550000"),
        "pass_max_cost_drag": d("0.030000"),
        "block_max_cost_drag": d("0.080000"),
        "liquidity_penalty_weight": d("0.050000"),
    }
    values.update(overrides)
    return ResearchStrategyCostConfidenceFrontierConfig(**values)


def frontier_input(
    index: int,
    *,
    fee_cost: Decimal = d("0.006000"),
    spread_cost: Decimal = d("0.010000"),
    slippage_cost: Decimal = d("0.004000"),
    liquidity_reliability: Decimal = d("0.900000"),
    evidence_strength: Decimal = d("0.820000"),
    resolution_clarity: Decimal = d("0.880000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyCostConfidenceFrontierInput:
    return ResearchStrategyCostConfidenceFrontierInput(
        candidate_id=f"raw-candidate-{index:03d}",
        market_id=f"raw-market-{index:03d}",
        market_slug=f"raw-market-slug-{index:03d}",
        market_question=f"Will this raw question remain private {index}?",
        market_url=f"https://example.test/markets/{index}?token=super-secret",
        fee_cost=fee_cost,
        spread_cost=spread_cost,
        slippage_cost=slippage_cost,
        liquidity_reliability=liquidity_reliability,
        evidence_strength=evidence_strength,
        resolution_clarity=resolution_clarity,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    samples: tuple[ResearchStrategyCostConfidenceFrontierInput, ...],
    *,
    cfg: ResearchStrategyCostConfidenceFrontierConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyCostConfidenceFrontierReport:
    return build_research_strategy_cost_confidence_frontier_report(
        samples,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_digest() -> None:
    result = report(())

    assert type(result) is ResearchStrategyCostConfidenceFrontierReport
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-strategy-cost-confidence-frontier-report-v0"
    assert result.frontier_status == "block"
    assert result.sample_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.average_cost_drag is None
    assert result.average_confidence_score is None
    assert result.best_frontier_score is None
    assert result.rows == ()
    assert result.reason_codes == ("empty_frontier_samples",)
    assert result.reason_code_counts == (
        ResearchStrategyCostConfidenceFrontierReasonCodeCount(
            reason_code="empty_frontier_samples",
            count=d("1"),
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_pass_row_builds_cost_drag_confidence_frontier_without_raw_surfaces() -> None:
    result = report((frontier_input(1, reason_codes=("manual_review_ready",)),))

    assert result.frontier_status == "pass"
    assert result.sample_count == d("1")
    assert result.pass_count == d("1")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.average_cost_drag == d("0.025000")
    assert result.average_confidence_score == d("0.866667")
    assert result.best_frontier_score == d("0.841667")
    assert result.reason_codes == ("cost_confidence_frontier_pass",)

    row = result.rows[0]
    assert type(row) is ResearchStrategyCostConfidenceFrontierRow
    assert row.rank == d("1")
    assert row.fee_cost == d("0.006000")
    assert row.spread_cost == d("0.010000")
    assert row.slippage_cost == d("0.004000")
    assert row.liquidity_reliability == d("0.900000")
    assert row.liquidity_reliability_drag == d("0.005000")
    assert row.total_cost_drag == d("0.025000")
    assert row.evidence_strength == d("0.820000")
    assert row.resolution_clarity == d("0.880000")
    assert row.confidence_score == d("0.866667")
    assert row.frontier_score == d("0.841667")
    assert row.frontier_status == "pass"
    assert row.reason_codes == (
        "cost_confidence_frontier_pass",
        "cost_drag_within_pass_band",
        "high_confidence_score",
        "input_manual_review_ready",
        "liquidity_reliability_drag_applied",
    )

    payload = research_strategy_cost_confidence_frontier_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["sample_count"] == "1"
    assert payload["rows"][0]["frontier_score"] == "0.841667"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["derived_validation_digest"] == _digest_without_digest(payload)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    for raw_fragment in (
        "raw-candidate",
        "raw-market",
        "raw-market-slug",
        "raw question",
        "example.test",
        "super-secret",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "position",
        "sizing",
        "recommend",
    ):
        assert raw_fragment not in encoded.lower()


def test_watch_and_block_rows_rank_deterministically_by_frontier_score() -> None:
    result = report(
        (
            frontier_input(
                3,
                fee_cost=d("0.030000"),
                spread_cost=d("0.030000"),
                slippage_cost=d("0.010000"),
                liquidity_reliability=d("0.600000"),
                evidence_strength=d("0.610000"),
                resolution_clarity=d("0.650000"),
            ),
            frontier_input(
                1,
                fee_cost=d("0.010000"),
                spread_cost=d("0.015000"),
                slippage_cost=d("0.005000"),
                liquidity_reliability=d("0.800000"),
                evidence_strength=d("0.650000"),
                resolution_clarity=d("0.750000"),
            ),
            frontier_input(
                2,
                fee_cost=d("0.040000"),
                spread_cost=d("0.030000"),
                slippage_cost=d("0.020000"),
                liquidity_reliability=d("0.700000"),
                evidence_strength=d("0.400000"),
                resolution_clarity=d("0.500000"),
                reason_codes=("needs_evidence_review",),
            ),
        ),
    )

    assert result.frontier_status == "watch"
    assert result.pass_count == d("0")
    assert result.watch_count == d("2")
    assert result.block_count == d("1")
    assert tuple(row.frontier_score for row in result.rows) == (
        d("0.693333"),
        d("0.530000"),
        d("0.428333"),
    )
    assert tuple(row.rank for row in result.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.frontier_status for row in result.rows) == (
        "watch",
        "watch",
        "block",
    )
    assert result.rows[0].reason_codes == (
        "confidence_score_watch_band",
        "cost_confidence_frontier_watch",
        "cost_drag_watch_band",
        "liquidity_reliability_drag_applied",
    )
    assert result.rows[2].reason_codes == (
        "confidence_score_below_watch_band",
        "cost_confidence_frontier_block",
        "cost_drag_above_block_band",
        "input_needs_evidence_review",
        "liquidity_reliability_drag_applied",
    )


def test_rank_ties_do_not_use_private_candidate_or_market_identifiers() -> None:
    first = replace(
        frontier_input(1),
        candidate_id="zzz-private-candidate",
        market_id="zzz-private-market",
        fee_cost=d("0.020000"),
        spread_cost=d("0.000000"),
        slippage_cost=d("0.000000"),
        liquidity_reliability=d("0.900000"),
        evidence_strength=d("0.820000"),
        resolution_clarity=d("0.880000"),
    )
    second = replace(
        frontier_input(2),
        candidate_id="aaa-private-candidate",
        market_id="aaa-private-market",
        fee_cost=d("0.005000"),
        spread_cost=d("0.005000"),
        slippage_cost=d("0.005000"),
        liquidity_reliability=d("0.800000"),
        evidence_strength=d("0.900000"),
        resolution_clarity=d("0.900000"),
    )

    result = report((first, second))
    encoded = json.dumps(
        research_strategy_cost_confidence_frontier_report_payload(result),
        sort_keys=True,
    )

    assert tuple(row.frontier_score for row in result.rows) == (
        d("0.841667"),
        d("0.841667"),
    )
    assert tuple(row.total_cost_drag for row in result.rows) == (
        d("0.025000"),
        d("0.025000"),
    )
    assert tuple(row.fee_cost for row in result.rows) == (
        d("0.020000"),
        d("0.005000"),
    )
    assert "zzz-private" not in encoded
    assert "aaa-private" not in encoded


def test_validation_rejects_non_decimal_bad_flags_and_unsafe_public_payloads() -> None:
    with pytest.raises(ValueError, match="pass_min_confidence"):
        config(pass_min_confidence=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="watch_min_confidence"):
        config(watch_min_confidence=d("0.000000"))
    with pytest.raises(ValueError, match="block_max_cost_drag"):
        config(block_max_cost_drag=d("0.030000"))
    with pytest.raises(ValueError, match="fee_cost"):
        frontier_input(1, fee_cost=0.006)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_cost"):
        frontier_input(1, spread_cost=d("-0.010000"))
    with pytest.raises(ValueError, match="reason_codes"):
        frontier_input(1, reason_codes=("wallet_live_order",))
    with pytest.raises(ValueError, match="input.report_only"):
        frontier_input(1, report_only=False)

    result = report((frontier_input(1),))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="paper_only"):
        research_strategy_cost_confidence_frontier_report_payload(
            {"report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        research_strategy_cost_confidence_frontier_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "sample_count": 1,
            },
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        research_strategy_cost_confidence_frontier_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"market_id": "raw-market-001"}],
            },
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        research_strategy_cost_confidence_frontier_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"note": "contains wallet token surface"}],
            },
        )
    with pytest.raises(ValueError, match="frontier_status"):
        research_strategy_cost_confidence_frontier_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "frontier_status": "hold",
            },
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        research_strategy_cost_confidence_frontier_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "marketRef": "private-market-001",
            },
        )

    with pytest.raises(FrozenInstanceError):
        result.frontier_status = "watch"  # type: ignore[misc]


def test_public_dataclasses_reject_subclassing_and_statuses_are_only_pass_watch_block() -> None:
    with pytest.raises(TypeError):

        class BadConfig(ResearchStrategyCostConfidenceFrontierConfig):
            pass

    with pytest.raises(ValueError, match="frontier_status"):
        ResearchStrategyCostConfidenceFrontierRow(
            rank=d("1"),
            fee_cost=d("0.000000"),
            spread_cost=d("0.000000"),
            slippage_cost=d("0.000000"),
            liquidity_reliability=d("1.000000"),
            liquidity_reliability_drag=d("0.000000"),
            total_cost_drag=d("0.000000"),
            evidence_strength=d("1.000000"),
            resolution_clarity=d("1.000000"),
            confidence_score=d("1.000000"),
            frontier_score=d("1.000000"),
            frontier_status="blocked",
            reason_codes=("cost_confidence_frontier_pass",),
        )


def _digest_without_digest(payload: dict[str, object]) -> str:
    copied = dict(payload)
    copied.pop("derived_validation_digest", None)
    encoded = json.dumps(copied, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    return tuple(values)

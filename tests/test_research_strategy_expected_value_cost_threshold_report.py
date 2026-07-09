from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.research_strategy_expected_value_cost_threshold_report import (
    ResearchStrategyExpectedValueCostThresholdCandidate,
    ResearchStrategyExpectedValueCostThresholdConfig,
    ResearchStrategyExpectedValueCostThresholdReasonCodeCount,
    ResearchStrategyExpectedValueCostThresholdReport,
    ResearchStrategyExpectedValueCostThresholdRow,
    build_research_strategy_expected_value_cost_threshold_report,
    research_strategy_expected_value_cost_threshold_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


@dataclass(frozen=True)
class SuppliedCandidateShape:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    market_url: str
    model_probability: Decimal
    market_probability: Decimal
    fee_cost: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    settlement_uncertainty: Decimal
    confidence_haircut: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyExpectedValueCostThresholdConfig:
    values = {
        "config_version": "research-strategy-expected-value-cost-threshold-report-v0",
        "pass_adjusted_edge_threshold": d("0.050000"),
        "watch_adjusted_edge_threshold": d("0.010000"),
    }
    values.update(overrides)
    return ResearchStrategyExpectedValueCostThresholdConfig(**values)


def candidate(
    index: int,
    *,
    model_probability: Decimal = d("0.620000"),
    market_probability: Decimal = d("0.520000"),
    fee_cost: Decimal = d("0.010000"),
    spread_cost: Decimal = d("0.010000"),
    slippage_cost: Decimal = d("0.005000"),
    settlement_uncertainty: Decimal = d("0.005000"),
    confidence_haircut: Decimal = d("0.005000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyExpectedValueCostThresholdCandidate:
    return ResearchStrategyExpectedValueCostThresholdCandidate(
        candidate_id=f"raw-candidate-{index:03d}",
        market_id=f"raw-market-{index:03d}",
        market_slug=f"raw-market-slug-{index:03d}",
        market_question=f"Will this raw question stay hidden {index}?",
        market_url=f"https://example.test/markets/{index}?token=super-secret",
        model_probability=model_probability,
        market_probability=market_probability,
        fee_cost=fee_cost,
        spread_cost=spread_cost,
        slippage_cost=slippage_cost,
        settlement_uncertainty=settlement_uncertainty,
        confidence_haircut=confidence_haircut,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    candidates: tuple[object, ...],
    *,
    cfg: ResearchStrategyExpectedValueCostThresholdConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyExpectedValueCostThresholdReport:
    return build_research_strategy_expected_value_cost_threshold_report(
        candidates,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_zero_digest() -> None:
    result = report(())

    assert type(result) is ResearchStrategyExpectedValueCostThresholdReport
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-strategy-expected-value-cost-threshold-report-v0"
    assert result.candidate_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.average_adjusted_expected_value_edge is None
    assert result.top_adjusted_expected_value_edge is None
    assert result.status == "block"
    assert result.rows == ()
    assert result.reason_codes == ("no_expected_value_candidates",)
    assert result.reason_code_counts == (
        ResearchStrategyExpectedValueCostThresholdReasonCodeCount(
            reason_code="no_expected_value_candidates",
            count=d("1"),
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_pass_candidate_uses_net_edge_after_all_costs_without_exposing_raw_surfaces() -> None:
    result = report((candidate(1, reason_codes=("manual_review_ready",)),))

    assert result.status == "pass"
    assert result.candidate_count == d("1")
    assert result.pass_count == d("1")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.average_adjusted_expected_value_edge == d("0.065000")
    assert result.top_adjusted_expected_value_edge == d("0.065000")
    assert result.reason_codes == ("expected_value_cost_threshold_pass",)

    row = result.rows[0]
    assert type(row) is ResearchStrategyExpectedValueCostThresholdRow
    assert row.rank == d("1")
    assert row.model_probability == d("0.620000")
    assert row.market_probability == d("0.520000")
    assert row.gross_expected_value_edge == d("0.100000")
    assert row.total_cost_drag == d("0.035000")
    assert row.adjusted_expected_value_edge == d("0.065000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "confidence_haircut_applied",
        "cost_drag_within_edge",
        "expected_value_cost_threshold_pass",
        "input_manual_review_ready",
        "positive_model_market_edge",
    )

    payload = research_strategy_expected_value_cost_threshold_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["adjusted_expected_value_edge"] == "0.065000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    for raw_fragment in (
        "raw-candidate",
        "raw-market",
        "raw-market-slug",
        "raw question",
        "example.test",
        "super-secret",
        "token",
        "market_url",
        "market_question",
        "candidate_id",
        "market_id",
        "market_slug",
    ):
        assert raw_fragment not in encoded.lower()
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_watch_and_block_candidates_rank_deterministically_by_adjusted_edge() -> None:
    result = report(
        (
            candidate(
                3,
                model_probability=d("0.560000"),
                market_probability=d("0.520000"),
                fee_cost=d("0.010000"),
                spread_cost=d("0.010000"),
                slippage_cost=d("0.005000"),
                settlement_uncertainty=d("0.005000"),
                confidence_haircut=d("0.005000"),
            ),
            candidate(
                1,
                model_probability=d("0.590000"),
                market_probability=d("0.520000"),
                fee_cost=d("0.015000"),
                spread_cost=d("0.010000"),
                slippage_cost=d("0.005000"),
                settlement_uncertainty=d("0.005000"),
                confidence_haircut=d("0.005000"),
            ),
            candidate(
                2,
                model_probability=d("0.480000"),
                market_probability=d("0.520000"),
                fee_cost=d("0.005000"),
                spread_cost=d("0.005000"),
                slippage_cost=d("0.005000"),
                settlement_uncertainty=d("0.005000"),
                confidence_haircut=d("0.000000"),
                reason_codes=("needs_probability_review",),
            ),
        ),
    )

    assert result.status == "watch"
    assert result.pass_count == d("0")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("2")
    assert tuple(row.adjusted_expected_value_edge for row in result.rows) == (
        d("0.030000"),
        d("0.005000"),
        d("-0.060000"),
    )
    assert tuple(row.rank for row in result.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.status for row in result.rows) == ("watch", "block", "block")
    assert result.rows[0].reason_codes == (
        "confidence_haircut_applied",
        "cost_drag_within_edge",
        "expected_value_cost_threshold_watch",
        "positive_model_market_edge",
    )
    assert result.rows[1].reason_codes == (
        "confidence_haircut_applied",
        "cost_drag_within_edge",
        "expected_value_edge_below_watch_threshold",
        "positive_model_market_edge",
    )
    assert result.rows[2].reason_codes == (
        "cost_drag_exceeds_edge",
        "expected_value_edge_below_watch_threshold",
        "input_needs_probability_review",
        "model_edge_not_positive",
    )


def test_payload_rejects_unsafe_public_surfaces_numeric_primitives_and_digest_mismatch() -> None:
    result = report((candidate(1),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="paper_only"):
        research_strategy_expected_value_cost_threshold_report_payload(
            {"report_only": True, "readonly": True},
        )

    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        research_strategy_expected_value_cost_threshold_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "candidate_count": 1,
            },
        )

    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        research_strategy_expected_value_cost_threshold_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "average_adjusted_expected_value_edge": 0.5,
            },
        )

    with pytest.raises(ValueError, match="public payload values must be JSON-safe"):
        research_strategy_expected_value_cost_threshold_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "candidate_count": d("1"),
            },
        )

    with pytest.raises(ValueError, match="unsafe surface"):
        research_strategy_expected_value_cost_threshold_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"candidate_id": "raw-candidate-001"}],
            },
        )

    with pytest.raises(ValueError, match="unsafe surface"):
        research_strategy_expected_value_cost_threshold_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"market_question": "Will this expose raw text?"}],
            },
        )


def test_validation_rejects_non_decimal_inputs_bad_flags_and_live_trading_surfaces() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                "research-strategy-expected-value-cost-threshold-report-v0",
            ),
        )
    with pytest.raises(ValueError, match="pass_adjusted_edge_threshold"):
        config(pass_adjusted_edge_threshold=Decimal("0"))
    with pytest.raises(ValueError, match="watch_adjusted_edge_threshold"):
        config(watch_adjusted_edge_threshold=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="pass_adjusted_edge_threshold"):
        config(
            pass_adjusted_edge_threshold=d("0.010000"),
            watch_adjusted_edge_threshold=d("0.050000"),
        )
    with pytest.raises(ValueError, match="model_probability"):
        candidate(1, model_probability=0.62)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_cost"):
        candidate(1, fee_cost=d("-0.010000"))
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(1, reason_codes=("wallet_live_order",))
    with pytest.raises(ValueError, match="candidate.report_only"):
        candidate(1, report_only=False)

    with pytest.raises(FrozenInstanceError):
        result = report((candidate(1),))
        result.status = "watch"  # type: ignore[misc]


def test_status_vocabulary_is_limited_to_pass_watch_block() -> None:
    result = report((candidate(1),))
    assert {result.status, *(row.status for row in result.rows)} <= {
        "pass",
        "watch",
        "block",
    }

    with pytest.raises(ValueError, match="status"):
        replace(result, status="blocked")

    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="blocked")


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    return tuple(values)

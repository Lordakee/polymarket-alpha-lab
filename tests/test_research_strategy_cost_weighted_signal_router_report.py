from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json

import pytest

from polymarket_alpha_lab.research_strategy_cost_weighted_signal_router_report import (
    ResearchStrategyCostWeightedSignalRouterConfig,
    ResearchStrategyCostWeightedSignalRouterInput,
    ResearchStrategyCostWeightedSignalRouterReasonCodeCount,
    ResearchStrategyCostWeightedSignalRouterReport,
    ResearchStrategyCostWeightedSignalRouterRow,
    build_research_strategy_cost_weighted_signal_router_report,
    research_strategy_cost_weighted_signal_router_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyCostWeightedSignalRouterConfig:
    values = {
        "config_version": "research-strategy-cost-weighted-signal-router-report-v0",
        "pass_min_router_score": d("0.700000"),
        "watch_min_router_score": d("0.450000"),
        "block_min_cost_drag": d("0.120000"),
        "cost_drag_weight": d("0.500000"),
        "staleness_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchStrategyCostWeightedSignalRouterConfig(**values)


def router_input(
    index: int,
    *,
    signal_strength: Decimal = d("0.840000"),
    signal_confidence: Decimal = d("0.900000"),
    source_quorum_score: Decimal = d("0.780000"),
    fee_cost: Decimal = d("0.010000"),
    spread_cost: Decimal = d("0.020000"),
    slippage_cost: Decimal = d("0.010000"),
    source_staleness: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyCostWeightedSignalRouterInput:
    return ResearchStrategyCostWeightedSignalRouterInput(
        signal_id=f"private-signal-{index:03d}",
        candidate_id=f"raw-candidate-{index:03d}",
        market_id=f"raw-market-{index:03d}",
        market_slug=f"raw-market-slug-{index:03d}",
        market_question=f"Will this raw question remain private {index}?",
        source_url=f"https://example.test/source/{index}?token=secret-token",
        source_text=f"private source text for signal {index}",
        signal_strength=signal_strength,
        signal_confidence=signal_confidence,
        source_quorum_score=source_quorum_score,
        fee_cost=fee_cost,
        spread_cost=spread_cost,
        slippage_cost=slippage_cost,
        source_staleness=source_staleness,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    samples: tuple[ResearchStrategyCostWeightedSignalRouterInput, ...],
    *,
    cfg: ResearchStrategyCostWeightedSignalRouterConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyCostWeightedSignalRouterReport:
    return build_research_strategy_cost_weighted_signal_router_report(
        samples,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_digest() -> None:
    result = report(())

    assert type(result) is ResearchStrategyCostWeightedSignalRouterReport
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-strategy-cost-weighted-signal-router-report-v0"
    assert result.router_status == "block"
    assert result.sample_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.average_router_score is None
    assert result.average_cost_drag is None
    assert result.top_router_score is None
    assert result.rows == ()
    assert result.reason_codes == ("empty_signal_router_samples",)
    assert result.reason_code_counts == (
        ResearchStrategyCostWeightedSignalRouterReasonCodeCount(
            reason_code="empty_signal_router_samples",
            count=d("1"),
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_pass_row_routes_weighted_signal_without_raw_public_surfaces() -> None:
    result = report((router_input(1, reason_codes=("manual_review_ready",)),))

    assert result.router_status == "pass"
    assert result.sample_count == d("1")
    assert result.pass_count == d("1")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.average_router_score == d("0.800000")
    assert result.average_cost_drag == d("0.040000")
    assert result.top_router_score == d("0.800000")
    assert result.reason_codes == ("cost_weighted_signal_router_pass",)

    row = result.rows[0]
    assert type(row) is ResearchStrategyCostWeightedSignalRouterRow
    assert row.rank == d("1")
    assert row.signal_strength == d("0.840000")
    assert row.signal_confidence == d("0.900000")
    assert row.source_quorum_score == d("0.780000")
    assert row.raw_signal_score == d("0.840000")
    assert row.cost_drag == d("0.040000")
    assert row.cost_drag_penalty == d("0.020000")
    assert row.staleness_penalty == d("0.020000")
    assert row.router_score == d("0.800000")
    assert row.router_status == "pass"
    assert row.reason_codes == (
        "cost_drag_within_router_band",
        "cost_weighted_signal_router_pass",
        "input_manual_review_ready",
        "source_freshness_penalty_applied",
        "strong_weighted_signal",
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True

    payload = research_strategy_cost_weighted_signal_router_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["sample_count"] == "1"
    assert payload["rows"][0]["router_score"] == "0.800000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["derived_validation_digest"] == _digest_without_digest(payload)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    for raw_fragment in (
        "private-signal",
        "raw-candidate",
        "raw-market",
        "raw-market-slug",
        "raw question",
        "example.test",
        "secret-token",
        "source text",
        "signal_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
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


def test_watch_and_block_rows_rank_deterministically_by_router_score() -> None:
    result = report(
        (
            router_input(
                3,
                signal_strength=d("0.650000"),
                signal_confidence=d("0.700000"),
                source_quorum_score=d("0.620000"),
                fee_cost=d("0.030000"),
                spread_cost=d("0.040000"),
                slippage_cost=d("0.020000"),
                source_staleness=d("0.300000"),
            ),
            router_input(
                1,
                signal_strength=d("0.700000"),
                signal_confidence=d("0.750000"),
                source_quorum_score=d("0.650000"),
                fee_cost=d("0.030000"),
                spread_cost=d("0.040000"),
                slippage_cost=d("0.020000"),
                source_staleness=d("0.250000"),
            ),
            router_input(
                2,
                signal_strength=d("0.350000"),
                signal_confidence=d("0.400000"),
                source_quorum_score=d("0.300000"),
                fee_cost=d("0.060000"),
                spread_cost=d("0.050000"),
                slippage_cost=d("0.030000"),
                source_staleness=d("0.500000"),
                reason_codes=("needs_evidence_review",),
            ),
        ),
    )

    assert result.router_status == "watch"
    assert result.pass_count == d("0")
    assert result.watch_count == d("2")
    assert result.block_count == d("1")
    assert tuple(row.router_score for row in result.rows) == (
        d("0.605000"),
        d("0.545000"),
        d("0.180000"),
    )
    assert tuple(row.rank for row in result.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.router_status for row in result.rows) == (
        "watch",
        "watch",
        "block",
    )
    assert result.rows[0].reason_codes == (
        "cost_drag_watch_band",
        "cost_weighted_signal_router_watch",
        "source_freshness_penalty_applied",
        "weighted_signal_watch_band",
    )
    assert result.rows[2].reason_codes == (
        "cost_drag_above_block_band",
        "cost_weighted_signal_router_block",
        "input_needs_evidence_review",
        "source_freshness_penalty_applied",
        "weighted_signal_below_watch_band",
    )


def test_validation_rejects_non_decimal_bad_flags_and_unsafe_public_payloads() -> None:
    with pytest.raises(ValueError, match="pass_min_router_score"):
        config(pass_min_router_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="watch_min_router_score"):
        config(watch_min_router_score=d("0.000000"))
    with pytest.raises(ValueError, match="block_min_cost_drag"):
        config(block_min_cost_drag=d("0.000000"))
    with pytest.raises(ValueError, match="fee_cost"):
        router_input(1, fee_cost=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_cost"):
        router_input(1, spread_cost=d("-0.010000"))
    with pytest.raises(ValueError, match="reason_codes"):
        router_input(1, reason_codes=("wallet_live_order",))
    with pytest.raises(ValueError, match="input.report_only"):
        router_input(1, report_only=False)

    result = report((router_input(1),))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="paper_only"):
        research_strategy_cost_weighted_signal_router_report_payload(
            {"report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="public numeric values must be Decimal strings"):
        research_strategy_cost_weighted_signal_router_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "sample_count": 1,
            },
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        research_strategy_cost_weighted_signal_router_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"market_id": "raw-market-001"}],
            },
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        research_strategy_cost_weighted_signal_router_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"note": "contains wallet token surface"}],
            },
        )

    with pytest.raises(FrozenInstanceError):
        result.router_status = "watch"  # type: ignore[misc]


def test_public_dataclasses_reject_subclassing_and_statuses_are_only_pass_watch_block() -> None:
    with pytest.raises(TypeError):

        class BadConfig(ResearchStrategyCostWeightedSignalRouterConfig):
            pass

    with pytest.raises(ValueError, match="router_status"):
        ResearchStrategyCostWeightedSignalRouterRow(
            rank=d("1"),
            signal_strength=d("1.000000"),
            signal_confidence=d("1.000000"),
            source_quorum_score=d("1.000000"),
            raw_signal_score=d("1.000000"),
            cost_drag=d("0.000000"),
            cost_drag_penalty=d("0.000000"),
            source_staleness=d("0.000000"),
            staleness_penalty=d("0.000000"),
            router_score=d("1.000000"),
            router_status="blocked",
            reason_codes=("cost_weighted_signal_router_pass",),
        )
    with pytest.raises(ValueError, match="router_status"):
        research_strategy_cost_weighted_signal_router_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "router_status": "hold",
                "rows": [{"router_status": "blocked"}],
            },
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

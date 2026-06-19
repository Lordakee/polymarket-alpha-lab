from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_probability_side_edge import PaperProbabilitySideEdgeReport
from polymarket_alpha_lab.paper_side_edge_adapter import (
    PaperSideEdgeAdapterConfig,
    PaperSideEdgeStrategyRow,
    build_paper_side_edge_report_from_strategy_rows,
    paper_side_edge_inputs_from_strategy_rows,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def strategy_row(
    *,
    market_slug: str = "event-alpha",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperSideEdgeStrategyRow:
    return PaperSideEdgeStrategyRow(
        market_slug=market_slug,
        question="Will alpha happen?",
        side="yes",
        forecast_probability=d("0.640000"),
        side_price=d("0.570000"),
        fee_cost_per_share=d("0.010000"),
        spread_cost_per_share=d("0.002000"),
        slippage_cost_per_share=d("0.003000"),
        funding_cost_per_share=d("0.004000"),
        finalization_cost_per_share=d("0.005000"),
        time_cost_per_share=d("0.006000"),
        risk_cost_per_share=d("0.007000"),
        capital_cost_per_share=d("0.008000"),
        requested_paper_shares=d("100.000000"),
        max_executable_shares=d("100.000000"),
        market_context_fresh=True,
        settlement_context_fresh=True,
        reason_codes=("strategy_candidate",),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def adapter_config(
    *,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperSideEdgeAdapterConfig:
    return PaperSideEdgeAdapterConfig(
        config_version="paper-side-edge-adapter-v0",
        min_net_probability_edge=d("0.010000"),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_adapter_rejects_unsafe_strategy_rows_at_construction_and_conversion():
    with pytest.raises(ValueError, match="paper_only"):
        strategy_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        strategy_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        strategy_row(readonly=False)

    safe_row = strategy_row()
    unsafe_row = object.__new__(PaperSideEdgeStrategyRow)
    for field_name, value in safe_row.__dict__.items():
        object.__setattr__(unsafe_row, field_name, value)
    object.__setattr__(unsafe_row, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        paper_side_edge_inputs_from_strategy_rows((unsafe_row,))


def test_adapter_rejects_unsafe_config_before_building_report():
    with pytest.raises(ValueError, match="paper_only"):
        adapter_config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        adapter_config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        adapter_config(readonly=False)

    safe_config = adapter_config()
    unsafe_config = object.__new__(PaperSideEdgeAdapterConfig)
    for field_name, value in safe_config.__dict__.items():
        object.__setattr__(unsafe_config, field_name, value)
    object.__setattr__(unsafe_config, "paper_only", False)

    with pytest.raises(ValueError, match="paper_only"):
        build_paper_side_edge_report_from_strategy_rows(
            (strategy_row(),),
            config=unsafe_config,
            generated_at=GENERATED_AT,
        )


def test_adapter_rejects_non_exact_public_types_and_bad_iterables():
    with pytest.raises(ValueError, match="rows"):
        paper_side_edge_inputs_from_strategy_rows("not rows")
    with pytest.raises(ValueError, match="rows"):
        paper_side_edge_inputs_from_strategy_rows((object(),))
    with pytest.raises(ValueError, match="config"):
        build_paper_side_edge_report_from_strategy_rows(
            (strategy_row(),),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_side_edge_report_from_strategy_rows(
            (strategy_row(),),
            config=adapter_config(),
            generated_at="2026-06-19T12:00:00Z",
        )


def test_adapter_returns_empty_canonical_report_for_empty_safe_input():
    report = build_paper_side_edge_report_from_strategy_rows(
        (),
        config=adapter_config(),
        generated_at=GENERATED_AT,
    )

    assert type(report) is PaperProbabilitySideEdgeReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-side-edge-adapter-v0"
    assert report.input_count == 0
    assert report.row_count == 0
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_adapter_preserves_source_reason_codes_without_aliasing_mutable_inputs():
    source_reason_codes = ["zeta", "alpha", "alpha"]

    report = build_paper_side_edge_report_from_strategy_rows(
        (
            replace(
                strategy_row(),
                reason_codes=source_reason_codes,
            ),
        ),
        config=adapter_config(),
        generated_at=GENERATED_AT,
    )
    source_reason_codes.append("late_mutation")

    assert report.rows[0].reason_codes == ("alpha", "zeta")

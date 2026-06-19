from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_readiness import (
    PaperRecommendationReadinessConfig,
    PaperRecommendationReadinessGateInput,
    PaperRecommendationReadinessReport,
    build_paper_recommendation_readiness_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


def gate_input(
    market_slug: str = "alpha",
    *,
    side: str = "yes",
    gate_name: str = "side_edge",
    gate_status: str = "pass",
    adjusted_net_probability_edge: Decimal = Decimal("0.070000"),
    cost_per_share: Decimal = Decimal("0.010000"),
    reason_codes: tuple[str, ...] = ("side_edge_passed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationReadinessGateInput:
    return PaperRecommendationReadinessGateInput(
        market_slug=market_slug,
        side=side,
        gate_name=gate_name,
        gate_status=gate_status,
        adjusted_net_probability_edge=adjusted_net_probability_edge,
        cost_per_share=cost_per_share,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides: object) -> PaperRecommendationReadinessConfig:
    values = {
        "config_version": "readiness-v0",
        "min_pass_net_probability_edge": Decimal("0.030000"),
        "max_watch_gate_count": 1,
    }
    values.update(overrides)
    return PaperRecommendationReadinessConfig(**values)


def report(
    rows: tuple[PaperRecommendationReadinessGateInput, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: PaperRecommendationReadinessConfig | None = None,
) -> PaperRecommendationReadinessReport:
    return build_paper_recommendation_readiness_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_readiness_passes_when_all_gates_pass_and_edge_stays_above_threshold():
    readiness = report(
        (
            gate_input("beta", gate_name="cost_stress"),
            gate_input("alpha", gate_name="side_edge", cost_per_share=Decimal("0.020000")),
        ),
    )

    assert readiness.generated_at == GENERATED_AT
    assert readiness.generated_at.tzinfo is UTC
    assert readiness.config_version == "readiness-v0"
    assert readiness.input_count == 2
    assert readiness.row_count == 2
    assert readiness.ready_count == 2
    assert readiness.watch_count == 0
    assert readiness.blocked_count == 0
    assert readiness.top_adjusted_net_probability_edge == Decimal("0.070000")
    assert readiness.total_cost_per_share == Decimal("0.030000")
    assert tuple(row.market_slug for row in readiness.rows) == ("alpha", "beta")
    assert tuple(row.readiness_status for row in readiness.rows) == ("ready", "ready")
    assert readiness.rows[0].reason_codes == ("side_edge_passed",)
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True


def test_readiness_watches_stale_or_low_edge_rows_without_hard_blocks():
    readiness = report(
        (
            gate_input(
                "alpha",
                gate_name="settlement_timing",
                gate_status="watch",
                adjusted_net_probability_edge=Decimal("0.050000"),
                reason_codes=("settlement_context_stale",),
            ),
            gate_input(
                "beta",
                adjusted_net_probability_edge=Decimal("0.020000"),
                reason_codes=("side_edge_passed",),
            ),
        ),
    )

    assert readiness.ready_count == 0
    assert readiness.watch_count == 2
    assert readiness.blocked_count == 0
    assert tuple(row.market_slug for row in readiness.rows) == ("alpha", "beta")
    assert readiness.rows[0].readiness_status == "watch"
    assert readiness.rows[0].reason_codes == (
        "readiness_watch_gate",
        "settlement_context_stale",
    )
    assert readiness.rows[1].reason_codes == (
        "below_readiness_edge_threshold",
        "side_edge_passed",
    )


def test_readiness_blocks_failed_gates_and_too_many_watch_gates():
    readiness = report(
        (
            gate_input(
                "alpha",
                gate_name="outcome_uncertainty",
                gate_status="blocked",
                reason_codes=("ambiguous_outcome_definition",),
            ),
            gate_input(
                "beta",
                gate_name="settlement_timing",
                gate_status="watch",
                reason_codes=("settlement_context_stale",),
            ),
            gate_input(
                "beta",
                gate_name="liquidity_depth",
                gate_status="watch",
                reason_codes=("partial_depth",),
            ),
        ),
    )

    assert readiness.ready_count == 0
    assert readiness.watch_count == 0
    assert readiness.blocked_count == 2
    assert tuple(row.market_slug for row in readiness.rows) == ("alpha", "beta")
    assert readiness.rows[0].readiness_status == "blocked"
    assert readiness.rows[0].reason_codes == (
        "ambiguous_outcome_definition",
        "readiness_blocked_gate",
    )
    assert readiness.rows[1].readiness_status == "blocked"
    assert readiness.rows[1].reason_codes == (
        "partial_depth",
        "readiness_watch_gate_limit_exceeded",
        "settlement_context_stale",
    )


def test_readiness_rejects_empty_inputs_and_invalid_config_values():
    with pytest.raises(ValueError, match="gate_inputs"):
        report(())
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" readiness-v0")
    with pytest.raises(ValueError, match="min_pass_net_probability_edge"):
        config(min_pass_net_probability_edge=Decimal("1.000001"))
    with pytest.raises(ValueError, match="min_pass_net_probability_edge"):
        config(min_pass_net_probability_edge=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="max_watch_gate_count"):
        config(max_watch_gate_count=-1)
    with pytest.raises(ValueError, match="max_watch_gate_count"):
        config(max_watch_gate_count=_IntSubclass(1))


def test_readiness_validates_inputs_flags_counts_and_consistency():
    with pytest.raises(ValueError, match="side"):
        gate_input(side="maybe")
    with pytest.raises(ValueError, match="gate_status"):
        gate_input(gate_status="skip")
    with pytest.raises(ValueError, match="adjusted_net_probability_edge"):
        gate_input(adjusted_net_probability_edge=Decimal("0.0100001"))
    with pytest.raises(ValueError, match="cost_per_share"):
        gate_input(cost_per_share=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        gate_input(reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="paper_only"):
        gate_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        gate_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        gate_input(readonly=False)

    readiness = report((gate_input("alpha"),))

    with pytest.raises(ValueError, match="row_count"):
        replace(readiness, row_count=2)
    with pytest.raises(ValueError, match="ready_count"):
        replace(readiness, ready_count=0)
    with pytest.raises(ValueError, match="total_cost_per_share"):
        replace(readiness, total_cost_per_share=Decimal("0.020000"))
    with pytest.raises(ValueError, match="top_adjusted_net_probability_edge"):
        replace(readiness, top_adjusted_net_probability_edge=Decimal("0.010000"))
    with pytest.raises(FrozenInstanceError):
        readiness.ready_count = 0  # type: ignore[misc]


def test_readiness_normalizes_generated_at_to_utc_and_rejects_datetime_subclasses():
    readiness = report(
        (gate_input("alpha"),),
        generated_at=datetime(2026, 6, 19, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert readiness.generated_at == GENERATED_AT
    assert readiness.generated_at.tzinfo is UTC

    with pytest.raises(ValueError, match="generated_at"):
        report((gate_input("alpha"),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (gate_input("alpha"),),
            generated_at=_DatetimeSubclass(2026, 6, 19, 12, 0, tzinfo=UTC),
        )

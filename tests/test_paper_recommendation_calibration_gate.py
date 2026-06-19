from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_calibration_gate import (
    PaperRecommendationCalibrationGateConfig,
    PaperRecommendationCalibrationGateMetric,
    PaperRecommendationCalibrationGateReport,
    PaperRecommendationCalibrationGateRow,
    PaperRecommendationCalibrationGateSourceRow,
    build_paper_recommendation_calibration_gate_report,
)


GENERATED_AT = datetime(2026, 6, 19, 14, 0, tzinfo=UTC)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def source_row(**overrides: object) -> PaperRecommendationCalibrationGateSourceRow:
    values = {
        "market_slug": "fed-cut-june-2026",
        "side": "yes",
        "action": "recommend",
        "recommendation_score": d("0.120000"),
        "net_probability_edge": d("0.120000"),
        "forecaster_id": "book-imbalance-v1",
        "reason_codes": ("positive_net_probability_edge",),
    }
    values.update(overrides)
    return PaperRecommendationCalibrationGateSourceRow(**values)


def metric(**overrides: object) -> PaperRecommendationCalibrationGateMetric:
    values = {
        "forecaster_id": "book-imbalance-v1",
        "sample_count": 80,
        "brier_score": d("0.180000"),
        "log_loss": d("0.590000"),
        "calibration_status": "pass",
    }
    values.update(overrides)
    return PaperRecommendationCalibrationGateMetric(**values)


def config(**overrides: object) -> PaperRecommendationCalibrationGateConfig:
    values = {
        "config_version": "paper-recommendation-calibration-gate-v0",
        "min_sample_count": 30,
        "max_brier_score": d("0.250000"),
        "fail_penalty_per_share": d("0.050000"),
        "watch_penalty_per_share": d("0.010000"),
    }
    values.update(overrides)
    return PaperRecommendationCalibrationGateConfig(**values)


def report(
    rows: tuple[PaperRecommendationCalibrationGateSourceRow, ...],
    metrics: tuple[PaperRecommendationCalibrationGateMetric, ...],
    *,
    cfg: PaperRecommendationCalibrationGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationCalibrationGateReport:
    return build_paper_recommendation_calibration_gate_report(
        rows,
        metrics,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_calibration_gate_passes_rows_when_forecaster_metrics_are_strong():
    result = report(
        (
            source_row(market_slug="alpha", net_probability_edge=d("0.120000")),
            source_row(
                market_slug="beta",
                side="no",
                action="watch",
                recommendation_score=d("0.020000"),
                net_probability_edge=d("0.020000"),
                reason_codes=("below_min_net_probability_edge",),
            ),
        ),
        (metric(),),
    )

    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == "paper-recommendation-calibration-gate-v0"
    assert result.row_count == 2
    assert result.pass_count == 2
    assert result.watch_count == 0
    assert result.blocked_count == 0
    assert result.reason_codes == ("calibration_gate_passed",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    alpha = result.rows[0]
    assert alpha.market_slug == "alpha"
    assert alpha.side == "yes"
    assert alpha.action == "recommend"
    assert alpha.recommendation_score == d("0.120000")
    assert alpha.net_probability_edge == d("0.120000")
    assert alpha.forecaster_id == "book-imbalance-v1"
    assert alpha.calibration_gate_status == "pass"
    assert alpha.calibration_cost_per_share == ZERO
    assert alpha.adjusted_net_probability_edge == d("0.120000")
    assert alpha.sample_count == 80
    assert alpha.brier_score == d("0.180000")
    assert alpha.log_loss == d("0.590000")
    assert alpha.metric_calibration_status == "pass"
    assert alpha.reason_codes == (
        "positive_net_probability_edge",
        "calibration_gate_passed",
    )

    beta = result.rows[1]
    assert beta.calibration_gate_status == "pass"
    assert beta.calibration_cost_per_share == ZERO
    assert beta.adjusted_net_probability_edge == d("0.020000")
    assert beta.reason_codes == (
        "below_min_net_probability_edge",
        "calibration_gate_passed",
    )


def test_calibration_gate_watches_low_sample_count_and_applies_watch_penalty():
    result = report(
        (source_row(net_probability_edge=d("0.020000")),),
        (metric(sample_count=12),),
    )

    row = result.rows[0]
    assert result.pass_count == 0
    assert result.watch_count == 1
    assert result.blocked_count == 0
    assert result.reason_codes == ("insufficient_calibration_sample",)
    assert row.calibration_gate_status == "watch"
    assert row.calibration_cost_per_share == d("0.010000")
    assert row.adjusted_net_probability_edge == d("0.010000")
    assert row.reason_codes == (
        "positive_net_probability_edge",
        "insufficient_calibration_sample",
    )


def test_calibration_gate_blocks_failed_or_high_brier_forecasters():
    result = report(
        (
            source_row(
                market_slug="failed-status",
                forecaster_id="failed-model",
                net_probability_edge=d("0.040000"),
            ),
            source_row(
                market_slug="high-brier",
                forecaster_id="noisy-model",
                net_probability_edge=d("0.030000"),
            ),
        ),
        (
            metric(
                forecaster_id="failed-model",
                brier_score=d("0.240000"),
                calibration_status="fail",
            ),
            metric(
                forecaster_id="noisy-model",
                brier_score=d("0.310000"),
                calibration_status="pass",
            ),
        ),
    )

    assert result.pass_count == 0
    assert result.watch_count == 0
    assert result.blocked_count == 2
    assert result.reason_codes == (
        "calibration_status_fail",
        "brier_score_exceeds_threshold",
    )

    failed_status, high_brier = result.rows
    assert failed_status.calibration_gate_status == "blocked"
    assert failed_status.calibration_cost_per_share == d("0.050000")
    assert failed_status.adjusted_net_probability_edge == d("-0.010000")
    assert failed_status.reason_codes == (
        "positive_net_probability_edge",
        "calibration_status_fail",
    )
    assert high_brier.calibration_gate_status == "blocked"
    assert high_brier.calibration_cost_per_share == d("0.050000")
    assert high_brier.adjusted_net_probability_edge == d("-0.020000")
    assert high_brier.reason_codes == (
        "positive_net_probability_edge",
        "brier_score_exceeds_threshold",
    )


def test_missing_metrics_block_by_default_and_can_be_configured_to_watch():
    missing_metric_result = report((source_row(net_probability_edge=d("0.040000")),), ())

    blocked = missing_metric_result.rows[0]
    assert missing_metric_result.reason_codes == ("missing_calibration_metrics",)
    assert blocked.calibration_gate_status == "blocked"
    assert blocked.calibration_cost_per_share == d("0.050000")
    assert blocked.adjusted_net_probability_edge == d("-0.010000")
    assert blocked.sample_count is None
    assert blocked.brier_score is None
    assert blocked.log_loss is None
    assert blocked.metric_calibration_status is None

    watch_result = report(
        (source_row(net_probability_edge=d("0.040000")),),
        (),
        cfg=config(missing_metrics_gate_status="watch"),
    )

    watched = watch_result.rows[0]
    assert watch_result.reason_codes == ("missing_calibration_metrics",)
    assert watched.calibration_gate_status == "watch"
    assert watched.calibration_cost_per_share == d("0.010000")
    assert watched.adjusted_net_probability_edge == d("0.030000")


def test_calibration_gate_deduplicates_metrics_by_forecaster_and_sorts_rows():
    rows = (
        source_row(
            market_slug="zeta",
            recommendation_score=d("0.030000"),
            net_probability_edge=d("0.030000"),
        ),
        source_row(
            market_slug="alpha",
            recommendation_score=d("0.120000"),
            net_probability_edge=d("0.120000"),
        ),
    )

    result = report(rows, (metric(),))

    assert tuple(row.market_slug for row in result.rows) == ("alpha", "zeta")
    with pytest.raises(ValueError, match="duplicate forecaster_id"):
        report(rows, (metric(log_loss=None), metric(log_loss=d("0.600000"))))


def test_calibration_gate_validates_decimal_precision_utc_and_frozen_outputs():
    result = report(
        (source_row(net_probability_edge=d("0.020000")),),
        (metric(sample_count=12, log_loss=None),),
        generated_at=datetime(2026, 6, 19, 7, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert result.generated_at == GENERATED_AT
    assert result.rows[0].log_loss is None
    with pytest.raises(FrozenInstanceError):
        result.rows[0].calibration_gate_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        report((source_row(),), (metric(),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        PaperRecommendationCalibrationGateReport(
            generated_at=_DatetimeSubclass(2026, 6, 19, 14, 0, tzinfo=UTC),
            config_version="paper-recommendation-calibration-gate-v0",
            row_count=0,
            pass_count=0,
            watch_count=0,
            blocked_count=0,
            reason_codes=("calibration_gate_empty",),
            rows=(),
        )
    with pytest.raises(ValueError, match="max_brier_score"):
        config(max_brier_score=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="recommendation_score"):
        source_row(recommendation_score=d("0.0100001"))
    with pytest.raises(ValueError, match="net_probability_edge"):
        source_row(net_probability_edge=d("0.0100001"))
    with pytest.raises(ValueError, match="brier_score"):
        metric(brier_score=d("0.2500001"))
    with pytest.raises(ValueError, match="log_loss"):
        metric(log_loss=d("0.6000001"))
    with pytest.raises(ValueError, match="fail_penalty_per_share"):
        config(fail_penalty_per_share=d("0.0500001"))
    with pytest.raises(ValueError, match="min_sample_count"):
        config(min_sample_count=_IntSubclass(30))


def test_calibration_gate_validates_hard_safety_flags():
    with pytest.raises(ValueError, match="source row must be paper_only"):
        source_row(paper_only=False)
    with pytest.raises(ValueError, match="source row must be report_only"):
        source_row(report_only=False)
    with pytest.raises(ValueError, match="source row must be readonly"):
        source_row(readonly=False)
    with pytest.raises(ValueError, match="metric must be paper_only"):
        metric(paper_only=False)
    with pytest.raises(ValueError, match="metric must be report_only"):
        metric(report_only=False)
    with pytest.raises(ValueError, match="metric must be readonly"):
        metric(readonly=False)
    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="config must be report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="config must be readonly"):
        config(readonly=False)


def test_calibration_gate_constructor_rejects_inconsistent_report_and_rows():
    valid = report((source_row(),), (metric(),))

    with pytest.raises(ValueError, match="row_count"):
        replace(valid, row_count=2)
    with pytest.raises(ValueError, match="pass_count"):
        replace(valid, pass_count=0)
    with pytest.raises(ValueError, match="watch_count"):
        replace(valid, watch_count=1)
    with pytest.raises(ValueError, match="blocked_count"):
        replace(valid, blocked_count=1)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(valid, reason_codes=("missing_calibration_metrics",))
    with pytest.raises(ValueError, match="rows"):
        replace(valid, rows=(valid.rows[0], valid.rows[0]))

    with pytest.raises(ValueError, match="adjusted_net_probability_edge"):
        replace(valid.rows[0], adjusted_net_probability_edge=d("0.110000"))
    with pytest.raises(ValueError, match="calibration_cost_per_share"):
        replace(valid.rows[0], calibration_cost_per_share=d("0.010000"))


def test_calibration_gate_accepts_supplied_row_and_metric_shapes_without_exact_types():
    @dataclass(frozen=True)
    class SuppliedRow:
        market_slug: str = "shape-row"
        side: str = "no"
        action: str = "recommend"
        recommendation_score: Decimal = d("0.080000")
        net_probability_edge: Decimal = d("0.080000")
        forecaster_id: str = "shape-model"
        reason_codes: tuple[str, ...] = ("positive_net_probability_edge",)
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    @dataclass(frozen=True)
    class SuppliedMetric:
        forecaster_id: str = "shape-model"
        sample_count: int = 40
        brier_score: Decimal = d("0.190000")
        log_loss: Decimal | None = None
        calibration_status: str = "watch"
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    result = report(
        (SuppliedRow(),),
        (SuppliedMetric(),),
        cfg=config(watch_penalty_per_share=d("0.015000")),
    )

    row = result.rows[0]
    assert row.market_slug == "shape-row"
    assert row.side == "no"
    assert row.calibration_gate_status == "watch"
    assert row.calibration_cost_per_share == d("0.015000")
    assert row.adjusted_net_probability_edge == d("0.065000")
    assert row.reason_codes == (
        "positive_net_probability_edge",
        "calibration_status_watch",
    )

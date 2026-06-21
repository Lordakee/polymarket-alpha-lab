from __future__ import annotations

import ast
import importlib
from pathlib import Path
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_recommendation_queue import (
    PaperStrategyRecommendationQueueRow,
    PaperStrategyRecommendationQueueSummaryReport,
)


GENERATED_AT = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
T1 = datetime(2026, 6, 21, 10, 0, tzinfo=UTC)
T2 = datetime(2026, 6, 21, 11, 0, tzinfo=UTC)
T3 = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def _module():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_rank_stability",
    )


def _config(
    *,
    min_snapshot_count: int = 2,
    max_rank_movement: int = 1,
    max_score_delta: Decimal = d("0.050000"),
):
    module = _module()
    return module.PaperStrategyRecommendationRankStabilityConfig(
        config_version="strategy-recommendation-rank-stability-v0",
        min_snapshot_count=min_snapshot_count,
        max_rank_movement=max_rank_movement,
        max_score_delta=max_score_delta,
    )


def _ready_row(
    rank: int,
    market_slug: str,
    *,
    selected_side: str = "yes",
    recommendation_score: Decimal,
    suggested_notional: Decimal = d("10.000000"),
    primary_reason_code: str = "selected_by_policy",
) -> PaperStrategyRecommendationQueueRow:
    return PaperStrategyRecommendationQueueRow(
        rank=rank,
        market_slug=market_slug,
        selected_side=selected_side,
        action="recommend",
        decision="selected",
        recommendation_score=recommendation_score,
        suggested_notional=suggested_notional,
        primary_reason_code=primary_reason_code,
        queue_status="ready",
    )


def _watch_row(
    rank: int,
    market_slug: str,
    *,
    selected_side: str = "yes",
    recommendation_score: Decimal,
    suggested_notional: Decimal = d("0.000000"),
    primary_reason_code: str = "below_policy_cutoff",
) -> PaperStrategyRecommendationQueueRow:
    return PaperStrategyRecommendationQueueRow(
        rank=rank,
        market_slug=market_slug,
        selected_side=selected_side,
        action="recommend",
        decision="skipped",
        recommendation_score=recommendation_score,
        suggested_notional=suggested_notional,
        primary_reason_code=primary_reason_code,
        queue_status="watch",
    )


def _blocked_row(
    rank: int,
    market_slug: str,
    *,
    recommendation_score: Decimal = ZERO,
    primary_reason_code: str = "candidate_blocked",
) -> PaperStrategyRecommendationQueueRow:
    return PaperStrategyRecommendationQueueRow(
        rank=rank,
        market_slug=market_slug,
        selected_side="none",
        action="reject",
        decision="not_selected",
        recommendation_score=recommendation_score,
        suggested_notional=ZERO,
        primary_reason_code=primary_reason_code,
        queue_status="blocked",
    )


def _summary(
    generated_at: datetime,
    rows: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> PaperStrategyRecommendationQueueSummaryReport:
    ready_rows = tuple(row for row in rows if row.queue_status == "ready")
    return PaperStrategyRecommendationQueueSummaryReport(
        generated_at=generated_at,
        source_config_version="strategy-recommendation-bundle-v1",
        queue_count=len(rows),
        ready_count=len(ready_rows),
        watch_count=sum(1 for row in rows if row.queue_status == "watch"),
        blocked_count=sum(1 for row in rows if row.queue_status == "blocked"),
        total_ready_notional=sum((row.suggested_notional for row in ready_rows), ZERO),
        top_score=rows[0].recommendation_score if rows else ZERO,
        average_ready_score=(
            sum((row.recommendation_score for row in ready_rows), ZERO)
            / Decimal(len(ready_rows))
            if ready_rows
            else ZERO
        ),
        primary_reason_code_counts=_reason_counts(rows),
        queue_rows=rows,
    )


def _reason_counts(
    rows: tuple[PaperStrategyRecommendationQueueRow, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.primary_reason_code] = counts.get(row.primary_reason_code, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _build(reports, *, generated_at=GENERATED_AT, config=None):
    module = _module()
    return module.build_paper_strategy_recommendation_rank_stability_report(
        reports,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_empty_history_yields_watch_report_without_rows():
    report = _build(())

    module = _module()
    assert isinstance(report, module.PaperStrategyRecommendationRankStabilityReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-recommendation-rank-stability-v0"
    assert report.source_report_count == 0
    assert report.candidate_count == 0
    assert report.stability_status == "watch"
    assert report.stable_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.stable_ready_count == 0
    assert report.unstable_ready_count == 0
    assert report.selected_side_changed_count == 0
    assert report.queue_status_changed_count == 0
    assert report.latest_generated_at is None
    assert report.top_stable_market_slug is None
    assert report.rows == ()
    assert report.reason_codes == ("no_latest_candidates",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_two_snapshot_ready_candidate_is_stable_when_rank_score_and_side_hold():
    report = _build(
        (
            _summary(T1, (_ready_row(1, "alpha", recommendation_score=d("0.700000")),)),
            _summary(T2, (_ready_row(1, "alpha", recommendation_score=d("0.720000")),)),
        ),
    )

    assert report.stability_status == "stable"
    assert report.source_report_count == 2
    assert report.candidate_count == 1
    assert report.stable_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.stable_ready_count == 1
    assert report.unstable_ready_count == 0
    assert report.top_stable_market_slug == "alpha"
    assert report.latest_generated_at == T2
    assert report.reason_codes == ("stable_ready_candidates_present",)

    row = report.rows[0]
    assert row.market_slug == "alpha"
    assert row.stability_status == "stable"
    assert row.latest_selected_side == "yes"
    assert row.latest_queue_status == "ready"
    assert row.present_snapshot_count == 2
    assert row.ready_snapshot_count == 2
    assert row.first_rank == 1
    assert row.latest_rank == 1
    assert row.rank_delta == 0
    assert row.max_rank_movement == 0
    assert row.first_score == d("0.700000")
    assert row.latest_score == d("0.720000")
    assert row.score_delta == d("0.020000")
    assert row.max_score_delta == d("0.020000")
    assert row.first_notional == d("10.000000")
    assert row.latest_notional == d("10.000000")
    assert row.notional_delta == ZERO
    assert row.selected_side_changed is False
    assert row.queue_status_changed is False
    assert row.reason_codes == ("stable_ready",)


def test_single_snapshot_ready_candidate_stays_watch_until_history_is_sufficient():
    report = _build(
        (_summary(T1, (_ready_row(1, "alpha", recommendation_score=d("0.700000")),)),),
    )

    assert report.stability_status == "watch"
    assert report.watch_count == 1
    assert report.unstable_ready_count == 1
    assert report.rows[0].stability_status == "watch"
    assert report.rows[0].reason_codes == ("insufficient_history",)


def test_rank_and_score_churn_block_latest_ready_candidate():
    report = _build(
        (
            _summary(
                T1,
                (
                    _ready_row(1, "alpha", recommendation_score=d("0.900000")),
                    _watch_row(2, "beta", recommendation_score=d("0.500000")),
                    _watch_row(3, "gamma", recommendation_score=d("0.400000")),
                ),
            ),
            _summary(
                T2,
                (
                    _ready_row(1, "gamma", recommendation_score=d("0.920000")),
                    _ready_row(2, "beta", recommendation_score=d("0.880000")),
                    _ready_row(3, "alpha", recommendation_score=d("0.760000")),
                ),
            ),
        ),
        config=_config(max_rank_movement=1, max_score_delta=d("0.050000")),
    )

    alpha = next(row for row in report.rows if row.market_slug == "alpha")
    assert report.stability_status == "blocked"
    assert alpha.stability_status == "blocked"
    assert alpha.rank_delta == 2
    assert alpha.max_rank_movement == 2
    assert alpha.score_delta == d("-0.140000")
    assert alpha.max_score_delta == d("0.140000")
    assert alpha.reason_codes == (
        "rank_movement_exceeds_threshold",
        "score_delta_exceeds_threshold",
    )


def test_side_flip_or_ready_to_blocked_transition_blocks_candidate():
    side_flip = _build(
        (
            _summary(T1, (_ready_row(1, "alpha", selected_side="yes", recommendation_score=d("0.700000")),)),
            _summary(T2, (_ready_row(1, "alpha", selected_side="no", recommendation_score=d("0.710000")),)),
        ),
    )
    assert side_flip.stability_status == "blocked"
    assert side_flip.selected_side_changed_count == 1
    assert side_flip.rows[0].selected_side_changed is True
    assert side_flip.rows[0].reason_codes == ("selected_side_changed",)

    status_flip = _build(
        (
            _summary(T1, (_ready_row(1, "alpha", recommendation_score=d("0.700000")),)),
            _summary(T2, (_blocked_row(1, "alpha"),)),
        ),
    )
    assert status_flip.stability_status == "blocked"
    assert status_flip.queue_status_changed_count == 1
    assert status_flip.rows[0].queue_status_changed is True
    assert status_flip.rows[0].reason_codes == (
        "latest_candidate_blocked",
        "ready_to_blocked_transition",
    )


def test_report_rows_are_ordered_for_automation_review():
    report = _build(
        (
            _summary(
                T1,
                (
                    _ready_row(1, "alpha", recommendation_score=d("0.900000")),
                    _watch_row(2, "beta", recommendation_score=d("0.600000")),
                ),
            ),
            _summary(
                T2,
                (
                    _ready_row(1, "gamma", recommendation_score=d("0.910000")),
                    _ready_row(2, "alpha", recommendation_score=d("0.880000")),
                    _watch_row(3, "beta", recommendation_score=d("0.610000")),
                ),
            ),
        ),
        config=_config(max_rank_movement=3),
    )

    assert tuple(row.market_slug for row in report.rows) == (
        "alpha",
        "gamma",
        "beta",
    )
    assert tuple(row.stability_status for row in report.rows) == (
        "stable",
        "watch",
        "watch",
    )


def test_config_rows_and_reports_validate_decimal_precision_and_are_frozen():
    module = _module()
    config = _config(max_score_delta=d("0.050000"))
    with pytest.raises(FrozenInstanceError):
        config.max_rank_movement = 10
    with pytest.raises(ValueError, match="max_score_delta"):
        module.PaperStrategyRecommendationRankStabilityConfig(
            config_version="strategy-recommendation-rank-stability-v0",
            min_snapshot_count=2,
            max_rank_movement=1,
            max_score_delta=d("0.0500001"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.PaperStrategyRecommendationRankStabilityConfig(
            config_version="strategy-recommendation-rank-stability-v0",
            min_snapshot_count=2,
            max_rank_movement=1,
            max_score_delta=d("0.050000"),
            paper_only=False,
        )

    report = _build(
        (
            _summary(T1, (_ready_row(1, "alpha", recommendation_score=d("0.700000")),)),
            _summary(T2, (_ready_row(1, "alpha", recommendation_score=d("0.710000")),)),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        report.rows[0].market_slug = "mutated"


def test_direct_rows_and_reports_enforce_hard_flags_and_consistency():
    module = _module()
    valid_row = module.PaperStrategyRecommendationRankStabilityRow(
        market_slug="alpha",
        stability_status="stable",
        latest_selected_side="yes",
        latest_queue_status="ready",
        present_snapshot_count=2,
        ready_snapshot_count=2,
        first_rank=1,
        latest_rank=1,
        rank_delta=0,
        max_rank_movement=0,
        first_score=d("0.700000"),
        latest_score=d("0.700000"),
        score_delta=ZERO,
        max_score_delta=ZERO,
        first_notional=d("10.000000"),
        latest_notional=d("10.000000"),
        notional_delta=ZERO,
        selected_side_changed=False,
        queue_status_changed=False,
        reason_codes=("stable_ready",),
    )

    with pytest.raises(ValueError, match="report_only"):
        replace(valid_row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.PaperStrategyRecommendationRankStabilityReport(
            generated_at=GENERATED_AT,
            config_version="strategy-recommendation-rank-stability-v0",
            source_report_count=1,
            candidate_count=1,
            stability_status="stable",
            stable_count=1,
            watch_count=0,
            blocked_count=0,
            stable_ready_count=1,
            unstable_ready_count=0,
            selected_side_changed_count=0,
            queue_status_changed_count=0,
            latest_generated_at=T2,
            top_stable_market_slug="alpha",
            reason_codes=("stable_ready_candidates_present",),
            rows=(valid_row,),
            readonly=False,
        )

    bypassed_row = object.__new__(module.PaperStrategyRecommendationRankStabilityRow)
    for field_name, value in valid_row.__dict__.items():
        object.__setattr__(bypassed_row, field_name, value)
    object.__setattr__(bypassed_row, "score_delta", d("0.500000"))

    with pytest.raises(ValueError, match="score_delta"):
        module.PaperStrategyRecommendationRankStabilityReport(
            generated_at=GENERATED_AT,
            config_version="strategy-recommendation-rank-stability-v0",
            source_report_count=1,
            candidate_count=1,
            stability_status="stable",
            stable_count=1,
            watch_count=0,
            blocked_count=0,
            stable_ready_count=1,
            unstable_ready_count=0,
            selected_side_changed_count=0,
            queue_status_changed_count=0,
            latest_generated_at=T2,
            top_stable_market_slug="alpha",
            reason_codes=("stable_ready_candidates_present",),
            rows=(bypassed_row,),
        )


def test_decimal_values_are_canonicalized_to_six_places():
    module = _module()
    row = module.PaperStrategyRecommendationRankStabilityRow(
        market_slug="alpha",
        stability_status="stable",
        latest_selected_side="yes",
        latest_queue_status="ready",
        present_snapshot_count=2,
        ready_snapshot_count=2,
        first_rank=1,
        latest_rank=1,
        rank_delta=0,
        max_rank_movement=0,
        first_score=Decimal("0.7"),
        latest_score=Decimal("0.7"),
        score_delta=Decimal("0"),
        max_score_delta=Decimal("0"),
        first_notional=Decimal("10"),
        latest_notional=Decimal("10"),
        notional_delta=Decimal("0"),
        selected_side_changed=False,
        queue_status_changed=False,
        reason_codes=("stable_ready",),
    )

    assert row.first_score == d("0.700000")
    assert row.first_score.as_tuple().exponent == -6
    assert row.first_notional == d("10.000000")
    assert row.first_notional.as_tuple().exponent == -6


def test_threshold_boundaries_are_inclusive_for_stable_candidates():
    report = _build(
        (
            _summary(
                T1,
                (
                    _ready_row(1, "alpha", recommendation_score=d("0.700000")),
                    _watch_row(2, "beta", recommendation_score=d("0.500000")),
                ),
            ),
            _summary(
                T2,
                (
                    _ready_row(1, "beta", recommendation_score=d("0.900000")),
                    _ready_row(2, "alpha", recommendation_score=d("0.650000")),
                ),
            ),
        ),
        config=_config(max_rank_movement=1, max_score_delta=d("0.050000")),
    )

    alpha = next(row for row in report.rows if row.market_slug == "alpha")
    assert alpha.max_rank_movement == 1
    assert alpha.max_score_delta == d("0.050000")
    assert alpha.stability_status == "stable"


def test_nonempty_sources_with_empty_latest_queue_keep_latest_timestamp():
    report = _build((_summary(T1, ()),))

    assert report.source_report_count == 1
    assert report.latest_generated_at == T1
    assert report.candidate_count == 0
    assert report.stability_status == "watch"
    assert report.reason_codes == ("no_latest_candidates",)


def test_builder_rejects_unsafe_or_non_exact_source_reports():
    safe_report = _summary(
        T1,
        (_ready_row(1, "alpha", recommendation_score=d("0.700000")),),
    )

    unsafe_report = object.__new__(PaperStrategyRecommendationQueueSummaryReport)
    for field_name, value in safe_report.__dict__.items():
        object.__setattr__(unsafe_report, field_name, value)
    object.__setattr__(unsafe_report, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        _build((unsafe_report,))

    class QueueSummarySubclass(PaperStrategyRecommendationQueueSummaryReport):
        pass

    subclass_report = QueueSummarySubclass(**safe_report.__dict__)
    with pytest.raises(ValueError, match="PaperStrategyRecommendationQueueSummaryReport"):
        _build((subclass_report,))


def test_module_import_scope_stays_paper_only_and_readonly():
    spec = importlib.util.find_spec(
        "polymarket_alpha_lab.strategy_recommendation_rank_stability",
    )
    assert spec is not None
    assert spec.origin is not None
    tree = ast.parse(Path(spec.origin).read_text(encoding="utf-8"))

    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "typing",
        "polymarket_alpha_lab",
    }

import ast
import inspect
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    build_paper_recommendation_artifact_index_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_review import (
    PaperRecommendationCycleReviewConfig,
    PaperRecommendationCycleReviewReasonCodeCount,
    build_paper_recommendation_cycle_review_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
    build_paper_recommendation_cycle_snapshot_report,
)
from polymarket_alpha_lab.paper_recommendation_pipeline import (
    PaperRecommendationPipelineStage,
    build_paper_recommendation_pipeline_report,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "paper-recommendation-cycle-review-v0"


class SnapshotReportSubclass(PaperRecommendationCycleSnapshotReport):
    pass


@dataclass(frozen=True)
class FakeArtifact:
    artifact_name: str
    status: str
    item_count: int
    reason_codes: tuple[str, ...] = ()
    generated_at: datetime = GENERATED_AT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _config(stale_after_hours: Decimal = Decimal("6.000000")):
    return PaperRecommendationCycleReviewConfig(
        config_version=CONFIG_VERSION,
        stale_after_hours=stale_after_hours,
    )


def _stage(
    status: str,
    *,
    generated_at: datetime,
) -> PaperRecommendationPipelineStage:
    return PaperRecommendationPipelineStage(
        stage_name=f"{status}_stage",
        status=status,
        message=f"{status} stage",
        input_count=1,
        output_count=1,
    )


def _snapshot(
    *,
    final_status: str,
    generated_at: datetime,
    artifacts: tuple[FakeArtifact, ...] | None = None,
    artifact_status: str | None = None,
    reason_codes: tuple[str, ...] = (),
) -> PaperRecommendationCycleSnapshotReport:
    if artifacts is None:
        status = artifact_status or final_status
        artifacts = (
            FakeArtifact(
                "strategy_cycle_blocked_counts",
                status,
                1,
                reason_codes,
                generated_at=generated_at,
            ),
            FakeArtifact(
                "strategy_cycle_screening_report",
                "pass",
                1,
                (),
                generated_at=generated_at,
            ),
        )
    return build_paper_recommendation_cycle_snapshot_report(
        generated_at=generated_at,
        config_version="paper-recommendation-cycle-snapshot-v0",
        pipeline_report=build_paper_recommendation_pipeline_report(
            generated_at=generated_at,
            config_version="paper-recommendation-pipeline-v0",
            stages=(_stage(final_status, generated_at=generated_at),),
        ),
        artifact_index_report=build_paper_recommendation_artifact_index_report(
            generated_at=generated_at,
            config_version="paper-recommendation-artifact-index-v0",
            artifacts=artifacts,
        ),
    )


def test_cycle_review_summarizes_latest_snapshot_and_reason_counts():
    blocked_snapshot = _snapshot(
        final_status="blocked",
        generated_at=GENERATED_AT - timedelta(hours=3),
        artifact_status="blocked",
        reason_codes=("blocked_liquidity", "shared_reason"),
    )
    watch_snapshot = _snapshot(
        final_status="watch",
        generated_at=GENERATED_AT - timedelta(hours=2),
        artifact_status="watch",
        reason_codes=("watch_spread", "shared_reason"),
    )
    pass_snapshot = _snapshot(
        final_status="pass",
        generated_at=GENERATED_AT - timedelta(hours=1),
        artifact_status="pass",
        reason_codes=("shared_reason",),
    )

    report = build_paper_recommendation_cycle_review_report(
        [blocked_snapshot, watch_snapshot, pass_snapshot],
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.snapshot_count == 3
    assert report.latest_generated_at == GENERATED_AT - timedelta(hours=1)
    assert report.latest_final_status == "pass"
    assert report.blocked_snapshot_count == 1
    assert report.watch_snapshot_count == 1
    assert report.pass_snapshot_count == 1
    assert report.blocked_artifact_count == 1
    assert report.watch_artifact_count == 1
    assert report.missing_required_artifact_names == ()
    assert report.reason_code_counts == (
        PaperRecommendationCycleReviewReasonCodeCount(
            reason_code="artifact_index_blocked",
            count=1,
        ),
        PaperRecommendationCycleReviewReasonCodeCount(
            reason_code="artifact_index_pass",
            count=1,
        ),
        PaperRecommendationCycleReviewReasonCodeCount(
            reason_code="artifact_index_watch",
            count=1,
        ),
        PaperRecommendationCycleReviewReasonCodeCount(
            reason_code="blocked_liquidity",
            count=1,
        ),
        PaperRecommendationCycleReviewReasonCodeCount(
            reason_code="pipeline_final_status_blocked",
            count=1,
        ),
        PaperRecommendationCycleReviewReasonCodeCount(
            reason_code="pipeline_final_status_pass",
            count=1,
        ),
        PaperRecommendationCycleReviewReasonCodeCount(
            reason_code="pipeline_final_status_watch",
            count=1,
        ),
        PaperRecommendationCycleReviewReasonCodeCount(
            reason_code="shared_reason",
            count=3,
        ),
        PaperRecommendationCycleReviewReasonCodeCount(
            reason_code="watch_spread",
            count=1,
        ),
    )
    assert report.review_status == "watch"
    assert report.stale_history is False
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_cycle_review_blocks_empty_history_and_missing_required_artifacts():
    empty_report = build_paper_recommendation_cycle_review_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert empty_report.snapshot_count == 0
    assert empty_report.latest_generated_at is None
    assert empty_report.latest_final_status is None
    assert empty_report.missing_required_artifact_names == (
        "strategy_cycle_blocked_counts",
        "strategy_cycle_screening_report",
    )
    assert empty_report.review_status == "blocked"
    assert empty_report.stale_history is False

    latest_missing_screening = _snapshot(
        final_status="pass",
        generated_at=GENERATED_AT,
        artifacts=(
            FakeArtifact(
                "strategy_cycle_blocked_counts",
                "pass",
                1,
                generated_at=GENERATED_AT,
            ),
        ),
    )
    missing_artifact_report = build_paper_recommendation_cycle_review_report(
        (latest_missing_screening,),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert missing_artifact_report.missing_required_artifact_names == (
        "strategy_cycle_screening_report",
    )
    assert missing_artifact_report.review_status == "blocked"


def test_cycle_review_status_precedence_handles_blocked_watch_and_stale_history():
    latest_blocked = build_paper_recommendation_cycle_review_report(
        (
            _snapshot(
                final_status="pass",
                generated_at=GENERATED_AT - timedelta(hours=1),
            ),
            _snapshot(
                final_status="blocked",
                generated_at=GENERATED_AT,
                artifact_status="blocked",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    latest_watch = build_paper_recommendation_cycle_review_report(
        (
            _snapshot(
                final_status="watch",
                generated_at=GENERATED_AT,
                artifact_status="pass",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    watch_artifact = build_paper_recommendation_cycle_review_report(
        (
            _snapshot(
                final_status="pass",
                generated_at=GENERATED_AT,
                artifact_status="watch",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    stale_report = build_paper_recommendation_cycle_review_report(
        (
            _snapshot(
                final_status="pass",
                generated_at=GENERATED_AT - timedelta(hours=7),
            ),
        ),
        config=_config(stale_after_hours=Decimal("6.000000")),
        generated_at=GENERATED_AT,
    )

    assert latest_blocked.review_status == "blocked"
    assert latest_watch.review_status == "watch"
    assert watch_artifact.review_status == "watch"
    assert stale_report.stale_history is True
    assert stale_report.review_status == "watch"


def test_cycle_review_stale_history_uses_decimal_hour_threshold_exactly():
    exactly_threshold = build_paper_recommendation_cycle_review_report(
        (
            _snapshot(
                final_status="pass",
                generated_at=GENERATED_AT - timedelta(hours=6),
            ),
        ),
        config=_config(stale_after_hours=Decimal("6.000000")),
        generated_at=GENERATED_AT,
    )
    just_over_threshold = build_paper_recommendation_cycle_review_report(
        (
            _snapshot(
                final_status="pass",
                generated_at=GENERATED_AT - timedelta(hours=6, microseconds=1),
            ),
        ),
        config=_config(stale_after_hours=Decimal("6.000000")),
        generated_at=GENERATED_AT,
    )

    assert exactly_threshold.stale_history is False
    assert exactly_threshold.review_status == "pass"
    assert just_over_threshold.stale_history is True
    assert just_over_threshold.review_status == "watch"


def test_cycle_review_rejects_non_snapshot_inputs_and_subclasses():
    snapshot = _snapshot(final_status="pass", generated_at=GENERATED_AT)

    with pytest.raises(ValueError, match="snapshots must be an iterable"):
        build_paper_recommendation_cycle_review_report(
            "not snapshots",
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperRecommendationCycleSnapshotReport"):
        build_paper_recommendation_cycle_review_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperRecommendationCycleSnapshotReport"):
        build_paper_recommendation_cycle_review_report(
            (SnapshotReportSubclass(**snapshot.__dict__),),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_cycle_review_config_requires_decimal_hours_and_safety_flags():
    with pytest.raises(ValueError, match="config_version"):
        PaperRecommendationCycleReviewConfig(
            config_version=" paper-recommendation-cycle-review-v0",
            stale_after_hours=Decimal("6.000000"),
        )
    with pytest.raises(ValueError, match="stale_after_hours must be a Decimal"):
        PaperRecommendationCycleReviewConfig(
            config_version=CONFIG_VERSION,
            stale_after_hours=6,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="stale_after_hours must be nonnegative"):
        PaperRecommendationCycleReviewConfig(
            config_version=CONFIG_VERSION,
            stale_after_hours=Decimal("-0.000001"),
        )
    with pytest.raises(ValueError, match="stale_after_hours must be quantized"):
        PaperRecommendationCycleReviewConfig(
            config_version=CONFIG_VERSION,
            stale_after_hours=Decimal("6.0000001"),
        )

    report = build_paper_recommendation_cycle_review_report(
        (_snapshot(final_status="pass", generated_at=GENERATED_AT),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="snapshot status counts"):
        replace(report, pass_snapshot_count=0)
    with pytest.raises(ValueError, match="latest_generated_at"):
        replace(report, snapshot_count=0, pass_snapshot_count=0)


def test_cycle_review_dataclasses_are_frozen_and_generated_at_is_utc():
    report = build_paper_recommendation_cycle_review_report(
        (
            _snapshot(
                final_status="pass",
                generated_at=datetime(
                    2026,
                    6,
                    20,
                    5,
                    0,
                    tzinfo=timezone(timedelta(hours=-7)),
                ),
            ),
        ),
        config=_config(),
        generated_at=datetime(
            2026,
            6,
            20,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC

    with pytest.raises(FrozenInstanceError):
        report.review_status = "blocked"  # type: ignore[misc]


def test_cycle_review_module_uses_decimal_not_float_for_hour_math():
    from polymarket_alpha_lab import paper_recommendation_cycle_review as module

    tree = ast.parse(inspect.getsource(module))
    assert not any(isinstance(node, ast.Constant) and type(node.value) is float for node in ast.walk(tree))
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "total_seconds"
        for node in ast.walk(tree)
    )

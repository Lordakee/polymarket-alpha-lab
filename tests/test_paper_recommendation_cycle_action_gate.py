import ast
import inspect
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timezone, timedelta

import pytest

from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateConfig,
    PaperRecommendationCycleActionGateReasonCodeCount,
    build_paper_recommendation_cycle_action_gate_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_review import (
    PaperRecommendationCycleReviewReasonCodeCount,
    PaperRecommendationCycleReviewReport,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "paper-recommendation-cycle-action-gate-v0"
SOURCE_CONFIG_VERSION = "paper-recommendation-cycle-review-v0"


class CycleReviewReportSubclass(PaperRecommendationCycleReviewReport):
    pass


@dataclass(frozen=True)
class FakeReviewReport:
    generated_at: datetime = GENERATED_AT
    config_version: str = SOURCE_CONFIG_VERSION
    snapshot_count: int = 1
    latest_generated_at: datetime | None = GENERATED_AT
    latest_final_status: str | None = "pass"
    blocked_snapshot_count: int = 0
    watch_snapshot_count: int = 0
    pass_snapshot_count: int = 1
    blocked_artifact_count: int = 0
    watch_artifact_count: int = 0
    missing_required_artifact_names: tuple[str, ...] = ()
    reason_code_counts: tuple[PaperRecommendationCycleReviewReasonCodeCount, ...] = ()
    review_status: str = "pass"
    stale_history: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _config() -> PaperRecommendationCycleActionGateConfig:
    return PaperRecommendationCycleActionGateConfig(config_version=CONFIG_VERSION)


def _review_report(
    *,
    review_status: str,
    latest_final_status: str | None = "pass",
    missing_required_artifact_names: tuple[str, ...] = (),
    reason_code_counts: tuple[PaperRecommendationCycleReviewReasonCodeCount, ...] = (),
    stale_history: bool = False,
) -> PaperRecommendationCycleReviewReport:
    blocked_snapshot_count = 1 if latest_final_status == "blocked" else 0
    watch_snapshot_count = 1 if latest_final_status == "watch" else 0
    pass_snapshot_count = 1 if latest_final_status == "pass" else 0
    snapshot_count = (
        blocked_snapshot_count + watch_snapshot_count + pass_snapshot_count
    )
    return PaperRecommendationCycleReviewReport(
        generated_at=GENERATED_AT,
        config_version=SOURCE_CONFIG_VERSION,
        snapshot_count=snapshot_count,
        latest_generated_at=GENERATED_AT if snapshot_count else None,
        latest_final_status=latest_final_status,
        blocked_snapshot_count=blocked_snapshot_count,
        watch_snapshot_count=watch_snapshot_count,
        pass_snapshot_count=pass_snapshot_count,
        blocked_artifact_count=blocked_snapshot_count,
        watch_artifact_count=watch_snapshot_count,
        missing_required_artifact_names=missing_required_artifact_names,
        reason_code_counts=reason_code_counts,
        review_status=review_status,
        stale_history=stale_history,
    )


def test_cycle_action_gate_allows_research_review_when_cycle_review_passes():
    review = _review_report(review_status="pass", latest_final_status="pass")

    report = build_paper_recommendation_cycle_action_gate_report(
        review,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.source_config_version == SOURCE_CONFIG_VERSION
    assert report.review_status == "pass"
    assert report.latest_final_status == "pass"
    assert report.action_status == "research_ready"
    assert report.recommended_next_step == "build_candidate_research_queue"
    assert report.missing_required_artifact_count == 0
    assert report.blocked_reason_count == 0
    assert report.watch_reason_count == 0
    assert report.reason_code_counts == (
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="cycle_review_pass",
            count=1,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_cycle_action_gate_watches_when_cycle_review_waits_for_fresh_evidence():
    review = _review_report(
        review_status="watch",
        latest_final_status="watch",
        reason_code_counts=(
            PaperRecommendationCycleReviewReasonCodeCount(
                reason_code="artifact_index_watch",
                count=2,
            ),
        ),
    )

    report = build_paper_recommendation_cycle_action_gate_report(
        review,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.action_status == "watch"
    assert report.recommended_next_step == "await_fresh_cycle_evidence"
    assert report.blocked_reason_count == 0
    assert report.watch_reason_count == 3
    assert report.reason_code_counts == (
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="artifact_index_watch",
            count=2,
        ),
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="cycle_review_watch",
            count=1,
        ),
    )


def test_cycle_action_gate_blocks_when_review_blocks_or_artifacts_are_missing():
    blocked_review = _review_report(
        review_status="blocked",
        latest_final_status="blocked",
        reason_code_counts=(
            PaperRecommendationCycleReviewReasonCodeCount(
                reason_code="pipeline_final_status_blocked",
                count=1,
            ),
        ),
    )
    missing_artifact_review = _review_report(
        review_status="watch",
        latest_final_status="pass",
        missing_required_artifact_names=("strategy_cycle_screening_report",),
    )

    blocked_report = build_paper_recommendation_cycle_action_gate_report(
        blocked_review,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    missing_artifact_report = build_paper_recommendation_cycle_action_gate_report(
        missing_artifact_review,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert blocked_report.action_status == "blocked"
    assert blocked_report.recommended_next_step == "repair_cycle_evidence"
    assert blocked_report.blocked_reason_count == 2
    assert blocked_report.watch_reason_count == 0
    assert blocked_report.reason_code_counts == (
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="cycle_review_blocked",
            count=1,
        ),
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="pipeline_final_status_blocked",
            count=1,
        ),
    )

    assert missing_artifact_report.action_status == "blocked"
    assert missing_artifact_report.recommended_next_step == "repair_cycle_evidence"
    assert missing_artifact_report.missing_required_artifact_count == 1
    assert missing_artifact_report.blocked_reason_count == 1
    assert missing_artifact_report.watch_reason_count == 1
    assert missing_artifact_report.reason_code_counts == (
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="cycle_review_watch",
            count=1,
        ),
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="missing_required_artifacts",
            count=1,
        ),
    )


def test_cycle_action_gate_watches_stale_history_and_marks_reason():
    review = _review_report(
        review_status="watch",
        latest_final_status="pass",
        stale_history=True,
    )

    report = build_paper_recommendation_cycle_action_gate_report(
        review,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.action_status == "watch"
    assert report.recommended_next_step == "await_fresh_cycle_evidence"
    assert report.blocked_reason_count == 0
    assert report.watch_reason_count == 2
    assert report.reason_code_counts == (
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="cycle_history_stale",
            count=1,
        ),
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="cycle_review_watch",
            count=1,
        ),
    )


def test_cycle_action_gate_reason_counts_are_copied_and_sorted_deterministically():
    review = _review_report(
        review_status="pass",
        latest_final_status="pass",
        reason_code_counts=(
            PaperRecommendationCycleReviewReasonCodeCount(
                reason_code="artifact_index_pass",
                count=2,
            ),
            PaperRecommendationCycleReviewReasonCodeCount(
                reason_code="shared_reason",
                count=3,
            ),
        ),
    )

    report = build_paper_recommendation_cycle_action_gate_report(
        review,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.reason_code_counts == (
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="artifact_index_pass",
            count=2,
        ),
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="cycle_review_pass",
            count=1,
        ),
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code="shared_reason",
            count=3,
        ),
    )


def test_cycle_action_gate_rejects_non_review_inputs_and_subclasses():
    review = _review_report(review_status="pass")

    with pytest.raises(ValueError, match="PaperRecommendationCycleReviewReport"):
        build_paper_recommendation_cycle_action_gate_report(
            FakeReviewReport(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperRecommendationCycleReviewReport"):
        build_paper_recommendation_cycle_action_gate_report(
            CycleReviewReportSubclass(**review.__dict__),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_cycle_action_gate_config_and_report_require_safe_values():
    with pytest.raises(ValueError, match="config_version"):
        PaperRecommendationCycleActionGateConfig(config_version="")
    with pytest.raises(ValueError, match="config"):
        build_paper_recommendation_cycle_action_gate_report(
            _review_report(review_status="pass"),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    report = build_paper_recommendation_cycle_action_gate_report(
        _review_report(review_status="pass"),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="missing_required_artifact_count"):
        replace(report, missing_required_artifact_count=1)
    with pytest.raises(ValueError, match="reason counts"):
        replace(report, blocked_reason_count=1)


def test_cycle_action_gate_dataclasses_are_frozen_and_generated_at_is_utc():
    report = build_paper_recommendation_cycle_action_gate_report(
        _review_report(review_status="pass"),
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
        report.action_status = "blocked"  # type: ignore[misc]


def test_cycle_action_gate_module_uses_no_float_literals():
    from polymarket_alpha_lab import paper_recommendation_cycle_action_gate as module

    tree = ast.parse(inspect.getsource(module))

    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(tree)
    )

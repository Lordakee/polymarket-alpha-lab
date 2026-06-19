import ast
import inspect
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    PaperRecommendationArtifactIndexReport,
    PaperRecommendationArtifactIndexRow,
    build_paper_recommendation_artifact_index_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
    build_paper_recommendation_cycle_snapshot_report,
)
from polymarket_alpha_lab.paper_recommendation_pipeline import (
    PaperRecommendationPipelineReport,
    PaperRecommendationPipelineStage,
    build_paper_recommendation_pipeline_report,
)


GENERATED_AT = datetime(2026, 6, 19, 17, 45, tzinfo=UTC)
CONFIG_VERSION = "paper-recommendation-cycle-snapshot-v0"


class PipelineReportSubclass(PaperRecommendationPipelineReport):
    pass


class ArtifactIndexReportSubclass(PaperRecommendationArtifactIndexReport):
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


def _stage(
    stage_name: str,
    status: str,
) -> PaperRecommendationPipelineStage:
    return PaperRecommendationPipelineStage(
        stage_name=stage_name,
        status=status,
        message=f"{stage_name} {status}",
        input_count=1,
        output_count=1,
    )


def _pipeline(
    *statuses: str,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationPipelineReport:
    return build_paper_recommendation_pipeline_report(
        generated_at=generated_at,
        config_version="paper-recommendation-pipeline-v0",
        stages=tuple(
            _stage(f"stage_{index}", status)
            for index, status in enumerate(statuses, start=1)
        ),
    )


def _artifact_index(
    *artifacts: FakeArtifact,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationArtifactIndexReport:
    return build_paper_recommendation_artifact_index_report(
        generated_at=generated_at,
        config_version="paper-recommendation-artifact-index-v0",
        artifacts=artifacts,
    )


def _snapshot(
    *,
    generated_at: datetime = GENERATED_AT,
    pipeline_report: PaperRecommendationPipelineReport | None = None,
    artifact_index_report: PaperRecommendationArtifactIndexReport | None = None,
) -> PaperRecommendationCycleSnapshotReport:
    return build_paper_recommendation_cycle_snapshot_report(
        generated_at=generated_at,
        config_version=CONFIG_VERSION,
        pipeline_report=pipeline_report or _pipeline("pass"),
        artifact_index_report=artifact_index_report
        or _artifact_index(FakeArtifact("alpha", "pass", 1)),
    )


def test_cycle_snapshot_summarizes_counts_reasons_and_status_precedence():
    pass_snapshot = _snapshot(
        pipeline_report=_pipeline("pass", "pass"),
        artifact_index_report=_artifact_index(
            FakeArtifact("alpha", "pass", 3, ("dup_reason",)),
            FakeArtifact("beta", "pass", 2, ("alpha_reason", "dup_reason")),
        ),
    )
    watch_snapshot = _snapshot(
        pipeline_report=_pipeline("pass"),
        artifact_index_report=_artifact_index(
            FakeArtifact("alpha", "watch", 1, ("watch_gate",)),
        ),
    )
    blocked_snapshot = _snapshot(
        pipeline_report=_pipeline("watch"),
        artifact_index_report=_artifact_index(
            FakeArtifact("alpha", "blocked", 1, ("missing_report",)),
        ),
    )

    assert pass_snapshot.generated_at == GENERATED_AT
    assert pass_snapshot.generated_at.tzinfo is UTC
    assert pass_snapshot.config_version == CONFIG_VERSION
    assert pass_snapshot.stage_count == 2
    assert pass_snapshot.artifact_count == 2
    assert pass_snapshot.blocked_artifact_count == 0
    assert pass_snapshot.watch_artifact_count == 0
    assert pass_snapshot.final_status == "pass"
    assert pass_snapshot.reason_codes == (
        "pipeline_final_status_pass",
        "artifact_index_pass",
        "alpha_reason",
        "dup_reason",
    )
    assert pass_snapshot.paper_only is True
    assert pass_snapshot.report_only is True
    assert pass_snapshot.readonly is True

    assert watch_snapshot.final_status == "watch"
    assert watch_snapshot.watch_artifact_count == 1
    assert watch_snapshot.reason_codes == (
        "pipeline_final_status_pass",
        "artifact_index_watch",
        "watch_gate",
    )

    assert blocked_snapshot.final_status == "blocked"
    assert blocked_snapshot.blocked_artifact_count == 1
    assert blocked_snapshot.reason_codes == (
        "pipeline_final_status_watch",
        "artifact_index_blocked",
        "missing_report",
    )


def test_cycle_snapshot_rejects_generated_at_mismatch_and_wrong_nested_types():
    with pytest.raises(ValueError, match="pipeline_report"):
        _snapshot(pipeline_report=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="artifact_index_report"):
        _snapshot(artifact_index_report=object())  # type: ignore[arg-type]

    pipeline = _pipeline("pass")
    artifact_index = _artifact_index(FakeArtifact("alpha", "pass", 1))
    with pytest.raises(ValueError, match="pipeline_report"):
        _snapshot(
            pipeline_report=PipelineReportSubclass(**pipeline.__dict__),
            artifact_index_report=artifact_index,
        )
    with pytest.raises(ValueError, match="artifact_index_report"):
        _snapshot(
            pipeline_report=pipeline,
            artifact_index_report=ArtifactIndexReportSubclass(**artifact_index.__dict__),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _snapshot(
            generated_at=GENERATED_AT + timedelta(minutes=1),
            pipeline_report=pipeline,
            artifact_index_report=artifact_index,
        )


def test_cycle_snapshot_rejects_unsafe_flags_and_inconsistent_replacements():
    snapshot = _snapshot(
        pipeline_report=_pipeline("pass", "watch"),
        artifact_index_report=_artifact_index(
            FakeArtifact("alpha", "pass", 1),
            FakeArtifact("beta", "watch", 2),
        ),
    )

    with pytest.raises(ValueError, match="paper_only"):
        replace(snapshot, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(snapshot, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(snapshot, readonly=False)
    with pytest.raises(ValueError, match="stage_count"):
        replace(snapshot, stage_count=99)
    with pytest.raises(ValueError, match="artifact_count"):
        replace(snapshot, artifact_count=99)
    with pytest.raises(ValueError, match="blocked_artifact_count"):
        replace(snapshot, blocked_artifact_count=1)
    with pytest.raises(ValueError, match="watch_artifact_count"):
        replace(snapshot, watch_artifact_count=0)
    with pytest.raises(ValueError, match="final_status"):
        replace(snapshot, final_status="pass")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(snapshot, reason_codes=("artifact_index_watch",))

    object.__setattr__(snapshot.pipeline_report, "paper_only", False)
    with pytest.raises(ValueError, match="pipeline report must be paper_only"):
        replace(snapshot)


def test_cycle_snapshot_dataclass_is_frozen_and_normalizes_generated_at_to_utc():
    generated_at = datetime(2026, 6, 19, 10, 45, tzinfo=timezone(timedelta(hours=-7)))
    snapshot = _snapshot(generated_at=generated_at)

    assert snapshot.generated_at == GENERATED_AT
    assert snapshot.generated_at.tzinfo is UTC

    with pytest.raises(FrozenInstanceError):
        snapshot.final_status = "blocked"  # type: ignore[misc]


def test_cycle_snapshot_constructor_rejects_invalid_counts_status_and_rows():
    row = PaperRecommendationArtifactIndexRow(
        artifact_name="beta",
        config_version="paper-recommendation-artifact-index-v0",
        generated_at=GENERATED_AT,
        status="pass",
        item_count=1,
        reason_codes=(),
        flags=("paper_only", "report_only", "readonly"),
    )
    unsorted_index = PaperRecommendationArtifactIndexReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-artifact-index-v0",
        row_count=1,
        pass_count=1,
        watch_count=0,
        blocked_count=0,
        index_status="pass",
        rows=(row,),
        flags=("paper_only", "report_only", "readonly"),
    )
    snapshot = PaperRecommendationCycleSnapshotReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        pipeline_report=_pipeline("pass"),
        artifact_index_report=unsorted_index,
        final_status="pass",
        stage_count=1,
        artifact_count=1,
        blocked_artifact_count=0,
        watch_artifact_count=0,
        reason_codes=("pipeline_final_status_pass", "artifact_index_pass"),
    )

    with pytest.raises(ValueError, match="stage_count"):
        replace(snapshot, stage_count=-1)
    with pytest.raises(ValueError, match="final_status"):
        replace(snapshot, final_status="hold")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(snapshot, reason_codes=("bad code",))


def test_cycle_snapshot_has_no_live_auth_order_network_imports():
    from polymarket_alpha_lab import paper_recommendation_cycle_snapshot as module

    tree = ast.parse(inspect.getsource(module))
    forbidden_import_roots = {
        "aiohttp",
        "eth_account",
        "httpx",
        "polymarket",
        "polymarket_clob_client",
        "py_clob_client",
        "requests",
        "web3",
        "websocket",
        "websockets",
    }
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", maxsplit=1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert called_names.isdisjoint(
        {
            "authenticate",
            "cancel_order",
            "create_order",
            "delete",
            "login",
            "patch",
            "post",
            "put",
            "request",
            "sign",
            "sign_message",
            "submit_order",
        },
    )

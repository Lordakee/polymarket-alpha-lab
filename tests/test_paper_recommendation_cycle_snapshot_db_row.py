from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    build_paper_recommendation_artifact_index_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
    build_paper_recommendation_cycle_snapshot_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_db_row import (
    PaperRecommendationCycleSnapshotDbRow,
    paper_recommendation_cycle_snapshot_from_db_row,
    paper_recommendation_cycle_snapshot_to_db_row,
)
from polymarket_alpha_lab.paper_recommendation_pipeline import (
    PaperRecommendationPipelineStage,
    build_paper_recommendation_pipeline_report,
)


GENERATED_AT = datetime(2026, 6, 19, 17, 45, tzinfo=UTC)
CONFIG_VERSION = "paper-recommendation-cycle-snapshot-v0"


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


class SnapshotSubclass(PaperRecommendationCycleSnapshotReport):
    pass


def _stage(stage_name: str, status: str) -> PaperRecommendationPipelineStage:
    return PaperRecommendationPipelineStage(
        stage_name=stage_name,
        status=status,
        message=f"{stage_name} {status}",
        input_count=1,
        output_count=1,
    )


def _snapshot() -> PaperRecommendationCycleSnapshotReport:
    pipeline_report = build_paper_recommendation_pipeline_report(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-pipeline-v0",
        stages=(_stage("stage_1", "pass"), _stage("stage_2", "watch")),
    )
    artifact_index_report = build_paper_recommendation_artifact_index_report(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-artifact-index-v0",
        artifacts=(
            FakeArtifact("alpha", "pass", 3, ("alpha_clear",)),
            FakeArtifact("beta", "blocked", 2, ("beta_missing",)),
        ),
    )
    return build_paper_recommendation_cycle_snapshot_report(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        pipeline_report=pipeline_report,
        artifact_index_report=artifact_index_report,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_cycle_snapshot_db_row_serializes_canonical_payload_and_round_trips():
    report = _snapshot()

    row = paper_recommendation_cycle_snapshot_to_db_row(report)

    assert type(row) is PaperRecommendationCycleSnapshotDbRow
    assert len(row.snapshot_sha256) == 64
    assert row.snapshot_sha256 == row.snapshot_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.final_status == "blocked"
    assert row.stage_count == 2
    assert row.artifact_count == 2
    assert row.blocked_artifact_count == 1
    assert row.watch_artifact_count == 0
    assert row.reason_codes == (
        "pipeline_final_status_watch",
        "artifact_index_blocked",
        "alpha_clear",
        "beta_missing",
    )
    assert row.stage_counts_json == {
        "stage_count": 2,
        "pass_count": 1,
        "watch_count": 1,
        "blocked_count": 0,
    }
    assert row.artifact_counts_json == {
        "artifact_count": 2,
        "pass_count": 1,
        "watch_count": 0,
        "blocked_count": 1,
    }
    assert row.payload_json["generated_at"] == "2026-06-19T17:45:00+00:00"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.payload_json["pipeline_report"]["readonly"] is True
    assert row.payload_json["artifact_index_report"]["readonly"] is True
    _assert_no_floats(row.payload_json)

    assert paper_recommendation_cycle_snapshot_from_db_row(row) == report


def test_cycle_snapshot_db_row_hash_is_deterministic_for_equivalent_reports():
    report = _snapshot()
    same_report = PaperRecommendationCycleSnapshotReport(**report.__dict__)

    first = paper_recommendation_cycle_snapshot_to_db_row(report)
    second = paper_recommendation_cycle_snapshot_to_db_row(same_report)

    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.payload_json == second.payload_json


def test_cycle_snapshot_db_row_rejects_wrong_report_type_and_subclasses():
    with pytest.raises(ValueError, match="PaperRecommendationCycleSnapshotReport"):
        paper_recommendation_cycle_snapshot_to_db_row(object())

    report = _snapshot()
    subclass = SnapshotSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperRecommendationCycleSnapshotReport"):
        paper_recommendation_cycle_snapshot_to_db_row(subclass)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_cycle_snapshot_db_row_rejects_false_report_flags(flag_name: str):
    report = _snapshot()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        paper_recommendation_cycle_snapshot_to_db_row(report)


def test_cycle_snapshot_db_row_rejects_malformed_stored_payload():
    report = _snapshot()
    row = paper_recommendation_cycle_snapshot_to_db_row(report)
    malformed = PaperRecommendationCycleSnapshotDbRow(
        snapshot_sha256="a" * 64,
        generated_at=row.generated_at,
        config_version=row.config_version,
        final_status=row.final_status,
        stage_count=row.stage_count,
        artifact_count=row.artifact_count,
        blocked_artifact_count=row.blocked_artifact_count,
        watch_artifact_count=row.watch_artifact_count,
        reason_codes=row.reason_codes,
        stage_counts_json=row.stage_counts_json,
        artifact_counts_json=row.artifact_counts_json,
        payload_json={**row.payload_json, "readonly": False},
    )

    with pytest.raises(ValueError, match="readonly"):
        paper_recommendation_cycle_snapshot_from_db_row(malformed)


def test_cycle_snapshot_db_row_wraps_payload_recovery_errors_as_value_error():
    report = _snapshot()
    row = paper_recommendation_cycle_snapshot_to_db_row(report)
    malformed = PaperRecommendationCycleSnapshotDbRow(
        snapshot_sha256="a" * 64,
        generated_at=row.generated_at,
        config_version=row.config_version,
        final_status=row.final_status,
        stage_count=row.stage_count,
        artifact_count=row.artifact_count,
        blocked_artifact_count=row.blocked_artifact_count,
        watch_artifact_count=row.watch_artifact_count,
        reason_codes=row.reason_codes,
        stage_counts_json=row.stage_counts_json,
        artifact_counts_json=row.artifact_counts_json,
        payload_json={
            key: value
            for key, value in row.payload_json.items()
            if key != "pipeline_report"
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        paper_recommendation_cycle_snapshot_from_db_row(malformed)


def test_cycle_snapshot_db_row_validates_row_shape():
    row = paper_recommendation_cycle_snapshot_to_db_row(_snapshot())

    with pytest.raises(ValueError, match="snapshot_sha256"):
        PaperRecommendationCycleSnapshotDbRow(
            snapshot_sha256="bad",
            generated_at=row.generated_at,
            config_version=row.config_version,
            final_status=row.final_status,
            stage_count=row.stage_count,
            artifact_count=row.artifact_count,
            blocked_artifact_count=row.blocked_artifact_count,
            watch_artifact_count=row.watch_artifact_count,
            reason_codes=row.reason_codes,
            stage_counts_json=row.stage_counts_json,
            artifact_counts_json=row.artifact_counts_json,
            payload_json=row.payload_json,
        )

    with pytest.raises(ValueError, match="payload_json"):
        PaperRecommendationCycleSnapshotDbRow(
            snapshot_sha256="a" * 64,
            generated_at=row.generated_at,
            config_version=row.config_version,
            final_status=row.final_status,
            stage_count=row.stage_count,
            artifact_count=row.artifact_count,
            blocked_artifact_count=row.blocked_artifact_count,
            watch_artifact_count=row.watch_artifact_count,
            reason_codes=row.reason_codes,
            stage_counts_json=row.stage_counts_json,
            artifact_counts_json=row.artifact_counts_json,
            payload_json={**row.payload_json, "bad_float": 0.1},
        )

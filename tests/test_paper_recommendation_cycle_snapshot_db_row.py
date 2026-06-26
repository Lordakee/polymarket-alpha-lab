from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
import hashlib
import json

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


def _snapshot_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_copy(payload_json: dict[str, object]) -> dict[str, object]:
    return json.loads(json.dumps(payload_json))


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

    with pytest.raises(ValueError, match="readonly"):
        replace(row, payload_json={**row.payload_json, "readonly": False})


def test_cycle_snapshot_db_row_wraps_payload_recovery_errors_as_value_error():
    report = _snapshot()
    row = paper_recommendation_cycle_snapshot_to_db_row(report)
    malformed = object.__new__(PaperRecommendationCycleSnapshotDbRow)
    for field_name, value in row.__dict__.items():
        object.__setattr__(malformed, field_name, value)
    object.__setattr__(
        malformed,
        "payload_json",
        {key: value for key, value in row.payload_json.items() if key != "pipeline_report"},
    )

    with pytest.raises(ValueError, match="payload_json"):
        paper_recommendation_cycle_snapshot_from_db_row(malformed)


@pytest.mark.parametrize(
    ("replacements", "message"),
    (
        ({"snapshot_sha256": "a" * 64}, "snapshot_sha256"),
        (
            {"generated_at": datetime(2026, 6, 19, 18, 45, tzinfo=UTC)},
            "generated_at",
        ),
        ({"config_version": "paper-recommendation-cycle-snapshot-v1"}, "config_version"),
        ({"final_status": "watch"}, "final_status"),
        (
            {
                "stage_count": 3,
                "stage_counts_json": {
                    "stage_count": 3,
                    "pass_count": 1,
                    "watch_count": 2,
                    "blocked_count": 0,
                },
            },
            "stage_count",
        ),
        (
            {
                "artifact_count": 3,
                "artifact_counts_json": {
                    "artifact_count": 3,
                    "pass_count": 1,
                    "watch_count": 1,
                    "blocked_count": 1,
                },
            },
            "artifact_count",
        ),
        (
            {
                "blocked_artifact_count": 2,
                "artifact_counts_json": {
                    "artifact_count": 2,
                    "pass_count": 0,
                    "watch_count": 0,
                    "blocked_count": 2,
                },
            },
            "blocked_artifact_count",
        ),
        (
            {
                "watch_artifact_count": 1,
                "artifact_counts_json": {
                    "artifact_count": 2,
                    "pass_count": 0,
                    "watch_count": 1,
                    "blocked_count": 1,
                },
            },
            "watch_artifact_count",
        ),
        ({"reason_codes": ("pipeline_final_status_watch",)}, "reason_codes"),
        (
            {
                "stage_counts_json": {
                    "stage_count": 2,
                    "pass_count": 2,
                    "watch_count": 0,
                    "blocked_count": 0,
                },
            },
            "stage_counts_json",
        ),
        (
            {
                "artifact_counts_json": {
                    "artifact_count": 2,
                    "pass_count": 2,
                    "watch_count": 0,
                    "blocked_count": 0,
                },
            },
            "artifact_counts_json",
        ),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
    ),
)
def test_cycle_snapshot_db_row_constructor_rejects_payload_mismatches(
    replacements: dict[str, object],
    message: str,
):
    row = paper_recommendation_cycle_snapshot_to_db_row(_snapshot())

    with pytest.raises(ValueError, match=message):
        replace(row, **replacements)


def test_cycle_snapshot_db_row_constructor_rejects_rehashed_boolean_count_payload():
    row = paper_recommendation_cycle_snapshot_to_db_row(_snapshot())
    payload_json = _payload_copy(row.payload_json)
    pipeline_report = payload_json["pipeline_report"]
    artifact_index_report = payload_json["artifact_index_report"]
    assert isinstance(pipeline_report, dict)
    assert isinstance(artifact_index_report, dict)
    payload_json["blocked_artifact_count"] = True
    pipeline_report["pass_count"] = True
    pipeline_report["watch_count"] = True
    stages = pipeline_report["stages"]
    assert isinstance(stages, list)
    first_stage = stages[0]
    assert isinstance(first_stage, dict)
    first_stage["input_count"] = True
    first_stage["output_count"] = True
    artifact_index_report["pass_count"] = True
    artifact_index_report["blocked_count"] = True
    rows = artifact_index_report["rows"]
    assert isinstance(rows, list)
    first_row = rows[0]
    assert isinstance(first_row, dict)
    first_row["item_count"] = True

    with pytest.raises(ValueError, match="count"):
        replace(
            row,
            snapshot_sha256=_snapshot_sha256(payload_json),
            payload_json=payload_json,
        )


@pytest.mark.parametrize(
    "mutate_payload",
    (
        lambda payload_json: payload_json.__setitem__("stage_count", True),
        lambda payload_json: payload_json["pipeline_report"].__setitem__(
            "pass_count",
            True,
        ),
        lambda payload_json: payload_json["pipeline_report"]["stages"][0].__setitem__(
            "input_count",
            True,
        ),
        lambda payload_json: payload_json["artifact_index_report"]["rows"][0].__setitem__(
            "item_count",
            True,
        ),
    ),
)
def test_cycle_snapshot_db_row_constructor_rejects_boolean_json_integer_fields(
    mutate_payload,
):
    row = paper_recommendation_cycle_snapshot_to_db_row(_snapshot())
    payload_json = _payload_copy(row.payload_json)
    mutate_payload(payload_json)

    with pytest.raises(ValueError, match="count"):
        replace(
            row,
            snapshot_sha256=_snapshot_sha256(payload_json),
            payload_json=payload_json,
        )


def test_cycle_snapshot_db_row_constructor_rejects_rehashed_nested_payload_missing_hard_flags():
    row = paper_recommendation_cycle_snapshot_to_db_row(_snapshot())
    payload_json = _payload_copy(row.payload_json)
    for nested_name in ("pipeline_report", "artifact_index_report"):
        nested_value = payload_json[nested_name]
        assert isinstance(nested_value, dict)
        for flag_name in ("paper_only", "report_only", "readonly"):
            nested_value.pop(flag_name)

    with pytest.raises(ValueError, match="paper_only"):
        replace(
            row,
            snapshot_sha256=_snapshot_sha256(payload_json),
            payload_json=payload_json,
        )


def test_cycle_snapshot_db_row_constructor_rejects_rehashed_nonrecoverable_payload():
    row = paper_recommendation_cycle_snapshot_to_db_row(_snapshot())
    payload_json = _payload_copy(row.payload_json)
    pipeline_report = payload_json["pipeline_report"]
    assert isinstance(pipeline_report, dict)
    pipeline_report["stages"] = []

    with pytest.raises(ValueError, match="payload_json"):
        replace(
            row,
            snapshot_sha256=_snapshot_sha256(payload_json),
            payload_json=payload_json,
        )


@pytest.mark.parametrize(
    ("mutate_row", "message"),
    (
        (
            lambda malformed: object.__setattr__(
                malformed,
                "blocked_artifact_count",
                True,
            ),
            "blocked_artifact_count",
        ),
        (
            lambda malformed: object.__setattr__(
                malformed,
                "stage_counts_json",
                {**malformed.stage_counts_json, "pass_count": True},
            ),
            "stage_counts_json",
        ),
        (
            lambda malformed: object.__setattr__(
                malformed,
                "artifact_counts_json",
                {**malformed.artifact_counts_json, "pass_count": True},
            ),
            "artifact_counts_json",
        ),
    ),
)
def test_cycle_snapshot_from_db_row_rejects_bypassed_boolean_materialized_counts(
    mutate_row,
    message: str,
):
    row = paper_recommendation_cycle_snapshot_to_db_row(_snapshot())
    malformed = object.__new__(PaperRecommendationCycleSnapshotDbRow)
    for field_name, value in row.__dict__.items():
        object.__setattr__(malformed, field_name, value)
    mutate_row(malformed)

    with pytest.raises(ValueError, match=message):
        paper_recommendation_cycle_snapshot_from_db_row(malformed)


def test_cycle_snapshot_from_db_row_rejects_bypassed_noncanonical_payload_json():
    row = paper_recommendation_cycle_snapshot_to_db_row(_snapshot())
    payload_json = _payload_copy(row.payload_json)
    reason_codes = payload_json["reason_codes"]
    assert isinstance(reason_codes, list)
    payload_json["reason_codes"] = tuple(reason_codes)
    malformed = object.__new__(PaperRecommendationCycleSnapshotDbRow)
    for field_name, value in row.__dict__.items():
        object.__setattr__(malformed, field_name, value)
    object.__setattr__(malformed, "payload_json", payload_json)

    with pytest.raises(ValueError, match="canonical"):
        paper_recommendation_cycle_snapshot_from_db_row(malformed)


def test_cycle_snapshot_from_db_row_defends_against_bypassed_payload_mismatch():
    row = paper_recommendation_cycle_snapshot_to_db_row(_snapshot())
    malformed = object.__new__(PaperRecommendationCycleSnapshotDbRow)
    for field_name, value in row.__dict__.items():
        object.__setattr__(malformed, field_name, value)
    object.__setattr__(
        malformed,
        "config_version",
        "paper-recommendation-cycle-snapshot-v1",
    )

    with pytest.raises(ValueError, match="config_version"):
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

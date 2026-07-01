from __future__ import annotations

import os
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
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_psycopg import (
    insert_paper_recommendation_cycle_snapshot_with_psycopg,
    load_paper_recommendation_cycle_snapshots_with_psycopg,
)
from polymarket_alpha_lab.paper_recommendation_pipeline import (
    PaperRecommendationPipelineStage,
    build_paper_recommendation_pipeline_report,
)
from polymarket_alpha_lab.supabase_cycle_snapshot_config import (
    CYCLE_SNAPSHOT_DB_DSN_ENV_VAR,
)
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn


RUN_SMOKE_ENV_VAR = "POLYMARKET_ALPHA_LAB_RUN_SUPABASE_SMOKE"
CONFIG_VERSION = "paper-recommendation-cycle-snapshot-smoke-v0"
GENERATED_AT = datetime(2026, 6, 19, 18, 30, tzinfo=UTC)
TABLE_NAME = "paper_recommendation_cycle_snapshots"


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


def test_paper_recommendation_cycle_snapshot_psycopg_supabase_smoke() -> None:
    dsn = _smoke_dsn()
    report = _snapshot_report()
    inserted_hash: str | None = None

    try:
        inserted = insert_paper_recommendation_cycle_snapshot_with_psycopg(
            dsn,
            report,
        )
        inserted_hash = inserted.snapshot_sha256

        duplicate = insert_paper_recommendation_cycle_snapshot_with_psycopg(
            dsn,
            report,
        )
        loaded = load_paper_recommendation_cycle_snapshots_with_psycopg(
            dsn,
            config_version=CONFIG_VERSION,
        )

        matching_reports = tuple(item for item in loaded if item == report)
        assert duplicate.snapshot_sha256 == inserted.snapshot_sha256
        assert matching_reports == (report,)
        assert matching_reports[0].paper_only is True
        assert matching_reports[0].report_only is True
        assert matching_reports[0].readonly is True
    finally:
        if inserted_hash is not None:
            _delete_snapshot(dsn, inserted_hash)


def _smoke_dsn() -> str:
    if os.environ.get(RUN_SMOKE_ENV_VAR) != "1":
        pytest.skip(f"set {RUN_SMOKE_ENV_VAR}=1 to run local Supabase smoke")
    dsn = os.environ.get(CYCLE_SNAPSHOT_DB_DSN_ENV_VAR)
    if not dsn:
        pytest.skip(f"set {CYCLE_SNAPSHOT_DB_DSN_ENV_VAR} to run local Supabase smoke")
    try:
        validate_local_postgres_dsn(
            dsn,
            env_var_name=CYCLE_SNAPSHOT_DB_DSN_ENV_VAR,
        )
    except ValueError:
        pytest.skip(
            f"{CYCLE_SNAPSHOT_DB_DSN_ENV_VAR} must point to local Supabase/Postgres",
        )
    return dsn


def test_smoke_dsn_rejects_remote_dsn_without_leaking_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    remote_dsn = "postgresql://postgres:super-secret-token@db.remote.example.com:5432/postgres"
    monkeypatch.setenv(RUN_SMOKE_ENV_VAR, "1")
    monkeypatch.setenv(CYCLE_SNAPSHOT_DB_DSN_ENV_VAR, remote_dsn)

    with pytest.raises(pytest.skip.Exception) as exc_info:
        _smoke_dsn()

    message = str(exc_info.value)
    assert CYCLE_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert "local Supabase/Postgres" in message
    assert "super-secret-token" not in message
    assert "db.remote.example.com" not in message


def _snapshot_report() -> PaperRecommendationCycleSnapshotReport:
    pipeline_report = build_paper_recommendation_pipeline_report(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-pipeline-smoke-v0",
        stages=(
            PaperRecommendationPipelineStage(
                stage_name="supabase_smoke_stage",
                status="pass",
                message="supabase smoke stage passed",
                input_count=1,
                output_count=1,
            ),
        ),
    )
    artifact_index_report = build_paper_recommendation_artifact_index_report(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-artifact-index-smoke-v0",
        artifacts=(
            FakeArtifact(
                artifact_name="supabase_smoke_artifact",
                status="pass",
                item_count=1,
                reason_codes=("supabase_smoke_artifact_pass",),
            ),
        ),
    )
    return build_paper_recommendation_cycle_snapshot_report(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        pipeline_report=pipeline_report,
        artifact_index_report=artifact_index_report,
    )


def _delete_snapshot(dsn: str, snapshot_sha256: str) -> None:
    import psycopg

    connection = psycopg.connect(dsn)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"DELETE FROM {TABLE_NAME} WHERE snapshot_sha256 = %s",
                (snapshot_sha256,),
            )
        finally:
            cursor.close()
        connection.commit()
    finally:
        connection.close()

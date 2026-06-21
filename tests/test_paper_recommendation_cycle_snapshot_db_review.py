import ast
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.paper_recommendation_cycle_snapshot_db_review as db_review
from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    build_paper_recommendation_artifact_index_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_review import (
    PaperRecommendationCycleReviewConfig,
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
REVIEW_CONFIG_VERSION = "paper-recommendation-cycle-review-v0"
SOURCE_CONFIG_VERSION = "paper-recommendation-cycle-snapshot-v0"


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


def _config() -> PaperRecommendationCycleReviewConfig:
    return PaperRecommendationCycleReviewConfig(
        config_version=REVIEW_CONFIG_VERSION,
        stale_after_hours=Decimal("6.000000"),
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
    artifact_status: str | None = None,
    reason_codes: tuple[str, ...] = (),
) -> PaperRecommendationCycleSnapshotReport:
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
        config_version=SOURCE_CONFIG_VERSION,
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


def test_load_cycle_snapshot_db_review_filters_limits_and_builds_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    calls: list[tuple[Any, str | None, int | None, str]] = []

    def load_snapshots(
        connection_arg: object,
        *,
        config_version: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_cycle_snapshots",
    ) -> tuple[PaperRecommendationCycleSnapshotReport, ...]:
        calls.append((connection_arg, config_version, limit, table_name))
        return (
            _snapshot(
                final_status="blocked",
                artifact_status="blocked",
                reason_codes=("blocked_liquidity",),
                generated_at=GENERATED_AT - timedelta(hours=1),
            ),
            _snapshot(
                final_status="watch",
                artifact_status="watch",
                reason_codes=("watch_spread",),
                generated_at=GENERATED_AT - timedelta(hours=2),
            ),
            _snapshot(
                final_status="pass",
                generated_at=GENERATED_AT - timedelta(hours=3),
            ),
        )

    monkeypatch.setattr(
        db_review.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )

    report = db_review.load_paper_recommendation_cycle_review_report(
        generated_at=GENERATED_AT,
        config=_config(),
        connection=connection,
        source_config_version=SOURCE_CONFIG_VERSION,
        limit=25,
        table_name="cycle_snapshot_archive",
    )

    assert calls == [(connection, SOURCE_CONFIG_VERSION, 25, "cycle_snapshot_archive")]
    assert report.generated_at == GENERATED_AT
    assert report.config_version == REVIEW_CONFIG_VERSION
    assert report.snapshot_count == 3
    assert report.pass_snapshot_count == 1
    assert report.watch_snapshot_count == 1
    assert report.blocked_snapshot_count == 1
    assert report.latest_generated_at == GENERATED_AT - timedelta(hours=1)
    assert report.latest_final_status == "blocked"
    assert report.blocked_artifact_count == 1
    assert report.watch_artifact_count == 1
    assert report.missing_required_artifact_names == ()
    assert report.review_status == "blocked"
    assert report.stale_history is False
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_load_cycle_snapshot_db_review_reverses_store_desc_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    newest_snapshot = _snapshot(
        final_status="pass",
        generated_at=GENERATED_AT - timedelta(hours=1),
    )
    older_snapshot = _snapshot(
        final_status="watch",
        artifact_status="watch",
        generated_at=GENERATED_AT - timedelta(hours=2),
    )

    def load_snapshots(
        connection_arg: object,
        *,
        config_version: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_cycle_snapshots",
    ) -> tuple[PaperRecommendationCycleSnapshotReport, ...]:
        return (newest_snapshot, older_snapshot)

    config = _config()
    expected_report = object()
    build_calls: list[
        tuple[
            tuple[PaperRecommendationCycleSnapshotReport, ...],
            PaperRecommendationCycleReviewConfig,
            datetime,
        ]
    ] = []

    def build_review(
        snapshots: tuple[PaperRecommendationCycleSnapshotReport, ...],
        *,
        config: PaperRecommendationCycleReviewConfig,
        generated_at: datetime,
    ) -> object:
        build_calls.append((tuple(snapshots), config, generated_at))
        return expected_report

    monkeypatch.setattr(
        db_review.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )
    monkeypatch.setattr(
        db_review,
        "build_paper_recommendation_cycle_review_report",
        build_review,
    )

    report = db_review.load_paper_recommendation_cycle_review_report(
        generated_at=GENERATED_AT,
        config=config,
        connection=object(),
    )

    assert report is expected_report
    assert build_calls == [
        (
            (older_snapshot, newest_snapshot),
            config,
            GENERATED_AT,
        ),
    ]


def test_load_cycle_snapshot_db_review_allows_empty_snapshot_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_snapshots(
        connection_arg: object,
        *,
        config_version: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_cycle_snapshots",
    ) -> tuple[PaperRecommendationCycleSnapshotReport, ...]:
        return ()

    monkeypatch.setattr(
        db_review.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )

    report = db_review.load_paper_recommendation_cycle_review_report(
        generated_at=GENERATED_AT,
        config=_config(),
        connection=object(),
    )

    assert report.snapshot_count == 0
    assert report.latest_generated_at is None
    assert report.latest_final_status is None
    assert report.missing_required_artifact_names == (
        "strategy_cycle_blocked_counts",
        "strategy_cycle_screening_report",
    )
    assert report.review_status == "blocked"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("flag_name", "message"),
    (
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
        ("readonly", "readonly"),
    ),
)
def test_load_cycle_snapshot_db_review_rejects_unsafe_loaded_snapshot_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
    message: str,
) -> None:
    unsafe_snapshot = _snapshot(
        final_status="pass",
        generated_at=GENERATED_AT - timedelta(hours=1),
    )
    object.__setattr__(unsafe_snapshot, flag_name, False)

    def load_snapshots(
        connection_arg: object,
        *,
        config_version: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_cycle_snapshots",
    ) -> tuple[PaperRecommendationCycleSnapshotReport, ...]:
        return (unsafe_snapshot,)

    monkeypatch.setattr(
        db_review.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )

    with pytest.raises(ValueError, match=message):
        db_review.load_paper_recommendation_cycle_review_report(
            generated_at=GENERATED_AT,
            config=_config(),
            connection=object(),
        )


def test_cycle_snapshot_db_review_module_has_no_live_driver_or_network_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_recommendation_cycle_snapshot_db_review.py"
    )
    module = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "argparse",
        "eth_account",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sys",
        "urllib",
        "websocket",
        "websockets",
    }

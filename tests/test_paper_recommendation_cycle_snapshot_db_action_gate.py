import ast
import importlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    build_paper_recommendation_artifact_index_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateConfig,
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
ACTION_GATE_CONFIG_VERSION = "paper-recommendation-cycle-action-gate-v0"
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


def _db_action_gate() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.paper_recommendation_cycle_snapshot_db_action_gate",
    )


def _review_config() -> PaperRecommendationCycleReviewConfig:
    return PaperRecommendationCycleReviewConfig(
        config_version=REVIEW_CONFIG_VERSION,
        stale_after_hours=Decimal("6.000000"),
    )


def _action_gate_config() -> PaperRecommendationCycleActionGateConfig:
    return PaperRecommendationCycleActionGateConfig(
        config_version=ACTION_GATE_CONFIG_VERSION,
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


def test_load_cycle_snapshot_db_action_gate_filters_limits_and_builds_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_action_gate = _db_action_gate()
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
                final_status="pass",
                generated_at=GENERATED_AT - timedelta(hours=1),
            ),
            _snapshot(
                final_status="pass",
                generated_at=GENERATED_AT - timedelta(hours=2),
            ),
        )

    monkeypatch.setattr(
        db_action_gate.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )

    report = db_action_gate.load_paper_recommendation_cycle_action_gate_report(
        generated_at=GENERATED_AT,
        review_config=_review_config(),
        action_gate_config=_action_gate_config(),
        connection=connection,
        source_config_version=SOURCE_CONFIG_VERSION,
        limit=25,
        table_name="cycle_snapshot_archive",
    )

    assert calls == [(connection, SOURCE_CONFIG_VERSION, 25, "cycle_snapshot_archive")]
    assert report.generated_at == GENERATED_AT
    assert report.config_version == ACTION_GATE_CONFIG_VERSION
    assert report.source_config_version == REVIEW_CONFIG_VERSION
    assert report.review_status == "pass"
    assert report.latest_final_status == "pass"
    assert report.action_status == "research_ready"
    assert report.recommended_next_step == "build_candidate_research_queue"
    assert report.missing_required_artifact_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_load_cycle_snapshot_db_action_gate_reverses_store_desc_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_action_gate = _db_action_gate()
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

    expected_review_report = object()
    expected_action_gate_report = object()
    review_build_calls: list[
        tuple[
            tuple[PaperRecommendationCycleSnapshotReport, ...],
            PaperRecommendationCycleReviewConfig,
            datetime,
        ]
    ] = []
    action_gate_build_calls: list[
        tuple[
            object,
            PaperRecommendationCycleActionGateConfig,
            datetime,
        ]
    ] = []

    def build_review(
        snapshots: tuple[PaperRecommendationCycleSnapshotReport, ...],
        *,
        config: PaperRecommendationCycleReviewConfig,
        generated_at: datetime,
    ) -> object:
        review_build_calls.append((tuple(snapshots), config, generated_at))
        return expected_review_report

    def build_action_gate(
        review_report: object,
        *,
        config: PaperRecommendationCycleActionGateConfig,
        generated_at: datetime,
    ) -> object:
        action_gate_build_calls.append((review_report, config, generated_at))
        return expected_action_gate_report

    review_config = _review_config()
    action_gate_config = _action_gate_config()
    monkeypatch.setattr(
        db_action_gate.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )
    monkeypatch.setattr(
        db_action_gate,
        "build_paper_recommendation_cycle_review_report",
        build_review,
    )
    monkeypatch.setattr(
        db_action_gate,
        "build_paper_recommendation_cycle_action_gate_report",
        build_action_gate,
    )

    report = db_action_gate.load_paper_recommendation_cycle_action_gate_report(
        generated_at=GENERATED_AT,
        review_config=review_config,
        action_gate_config=action_gate_config,
        connection=object(),
    )

    assert report is expected_action_gate_report
    assert review_build_calls == [
        (
            (older_snapshot, newest_snapshot),
            review_config,
            GENERATED_AT,
        ),
    ]
    assert action_gate_build_calls == [
        (expected_review_report, action_gate_config, GENERATED_AT),
    ]


def test_load_cycle_snapshot_db_action_gate_allows_empty_snapshot_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_action_gate = _db_action_gate()

    def load_snapshots(
        connection_arg: object,
        *,
        config_version: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_cycle_snapshots",
    ) -> tuple[PaperRecommendationCycleSnapshotReport, ...]:
        return ()

    monkeypatch.setattr(
        db_action_gate.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )

    report = db_action_gate.load_paper_recommendation_cycle_action_gate_report(
        generated_at=GENERATED_AT,
        review_config=_review_config(),
        action_gate_config=_action_gate_config(),
        connection=object(),
    )

    assert report.review_status == "blocked"
    assert report.latest_final_status is None
    assert report.action_status == "blocked"
    assert report.recommended_next_step == "repair_cycle_evidence"
    assert report.missing_required_artifact_count == 2
    assert report.blocked_reason_count == 3
    assert report.watch_reason_count == 0
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
def test_load_cycle_snapshot_db_action_gate_rejects_unsafe_loaded_snapshot_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
    message: str,
) -> None:
    db_action_gate = _db_action_gate()
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
        db_action_gate.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )

    with pytest.raises(ValueError, match=message):
        db_action_gate.load_paper_recommendation_cycle_action_gate_report(
            generated_at=GENERATED_AT,
            review_config=_review_config(),
            action_gate_config=_action_gate_config(),
            connection=object(),
        )


def test_cycle_snapshot_db_action_gate_module_has_no_live_driver_or_network_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_recommendation_cycle_snapshot_db_action_gate.py"
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
        "auth",
        "eth_account",
        "http",
        "httpx",
        "live",
        "network",
        "order",
        "psycopg",
        "requests",
        "socket",
        "sys",
        "urllib",
        "wallet",
        "websocket",
        "websockets",
        "write",
    }

import ast
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_recommendation_pipeline_trend import (
    PaperRecommendationPipelineTrendReport,
    build_paper_recommendation_pipeline_trend_report,
)


GENERATED_AT = datetime(2026, 6, 19, 18, 0, tzinfo=UTC)
CONFIG_VERSION = "paper-recommendation-pipeline-trend-v0"


@dataclass(frozen=True)
class PipelineReportShape:
    generated_at: datetime
    final_status: str
    stage_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class ArtifactReportShape:
    generated_at: datetime
    final_status: str
    artifact_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class _DatetimeSubclass(datetime):
    pass


class _IntSubclass(int):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def pipeline_report(
    generated_at: datetime = datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    *,
    final_status: str = "pass",
    stage_count: int = 1,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PipelineReportShape:
    return PipelineReportShape(
        generated_at=generated_at,
        final_status=final_status,
        stage_count=stage_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def artifact_report(
    generated_at: datetime = datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    *,
    final_status: str = "pass",
    artifact_count: int = 1,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ArtifactReportShape:
    return ArtifactReportShape(
        generated_at=generated_at,
        final_status=final_status,
        artifact_count=artifact_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def trend_report(
    reports: tuple[object, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = CONFIG_VERSION,
) -> PaperRecommendationPipelineTrendReport:
    return build_paper_recommendation_pipeline_trend_report(
        generated_at=generated_at,
        config_version=config_version,
        reports=reports,
    )


def test_trend_report_computes_counts_rates_date_range_and_latest_status():
    summary = trend_report(
        (
            pipeline_report(
                datetime(2026, 6, 19, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
                final_status="pass",
                stage_count=3,
            ),
            pipeline_report(
                datetime(2026, 6, 19, 14, 30, tzinfo=UTC),
                final_status="watch",
                stage_count=5,
            ),
            pipeline_report(
                datetime(2026, 6, 19, 15, 0, tzinfo=UTC),
                final_status="blocked",
                stage_count=7,
            ),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == CONFIG_VERSION
    assert summary.source_report_count == 3
    assert summary.pass_count == 1
    assert summary.watch_count == 1
    assert summary.blocked_count == 1
    assert summary.first_generated_at == datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
    assert summary.first_generated_at.tzinfo is UTC
    assert summary.last_generated_at == datetime(2026, 6, 19, 15, 0, tzinfo=UTC)
    assert summary.last_generated_at.tzinfo is UTC
    assert summary.average_stage_count == d("5.000000")
    assert summary.blocked_share == d("0.333333")
    assert summary.latest_status == "blocked"
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_trend_report_accepts_artifact_count_when_stage_count_is_absent():
    summary = trend_report(
        (
            artifact_report(
                datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
                final_status="pass",
                artifact_count=2,
            ),
            artifact_report(
                datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
                final_status="pass",
                artifact_count=5,
            ),
        ),
    )

    assert summary.source_report_count == 2
    assert summary.pass_count == 2
    assert summary.watch_count == 0
    assert summary.blocked_count == 0
    assert summary.first_generated_at == datetime(2026, 6, 19, 11, 0, tzinfo=UTC)
    assert summary.last_generated_at == datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
    assert summary.average_stage_count == d("3.500000")
    assert summary.blocked_share == d("0.000000")
    assert summary.latest_status == "pass"


def test_trend_report_rejects_empty_reports_or_unsafe_flags():
    with pytest.raises(ValueError, match="reports"):
        trend_report(())
    with pytest.raises(ValueError, match="paper_only"):
        trend_report((pipeline_report(paper_only=False),))
    with pytest.raises(ValueError, match="report_only"):
        trend_report((pipeline_report(report_only=False),))
    with pytest.raises(ValueError, match="readonly"):
        trend_report((pipeline_report(readonly=False),))


def test_trend_report_normalizes_aware_datetimes_to_utc_and_rejects_non_datetimes():
    summary = trend_report(
        (
            pipeline_report(
                datetime(2026, 6, 19, 8, 0, tzinfo=timezone(timedelta(hours=-7))),
                stage_count=2,
            ),
        ),
        generated_at=datetime(2026, 6, 19, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.first_generated_at == datetime(2026, 6, 19, 15, 0, tzinfo=UTC)
    assert summary.last_generated_at == datetime(2026, 6, 19, 15, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at"):
        trend_report((pipeline_report(),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        trend_report((pipeline_report(generated_at="bad"),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        trend_report(
            (
                pipeline_report(
                    generated_at=_DatetimeSubclass(2026, 6, 19, 18, 0, tzinfo=UTC),
                ),
            ),
        )


def test_trend_report_quantization_is_deterministic_and_public_types_are_strict():
    summary = trend_report(
        (
            pipeline_report(stage_count=1, final_status="pass"),
            pipeline_report(stage_count=1, final_status="blocked"),
            pipeline_report(stage_count=2, final_status="watch"),
        ),
    )

    assert summary.average_stage_count == d("1.333333")
    assert summary.blocked_share == d("0.333333")

    with pytest.raises(ValueError, match="config_version"):
        trend_report((pipeline_report(),), config_version=" trend-v0")
    with pytest.raises(ValueError, match="config_version"):
        trend_report((pipeline_report(),), config_version=_StringSubclass("trend-v0"))
    with pytest.raises(ValueError, match="final_status"):
        trend_report((pipeline_report(final_status="skip"),))
    with pytest.raises(ValueError, match="stage_count"):
        trend_report((pipeline_report(stage_count=-1),))
    with pytest.raises(ValueError, match="stage_count"):
        trend_report((pipeline_report(stage_count=_IntSubclass(1)),))
    with pytest.raises(ValueError, match="stage_count"):
        trend_report((object(),))
    with pytest.raises(FrozenInstanceError):
        summary.latest_status = "blocked"  # type: ignore[misc]


def test_trend_report_constructor_rejects_inconsistent_summaries():
    summary = trend_report(
        (
            pipeline_report(
                datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
                final_status="pass",
                stage_count=3,
            ),
            pipeline_report(
                datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
                final_status="blocked",
                stage_count=4,
            ),
        ),
    )

    with pytest.raises(ValueError, match="source_report_count"):
        replace(summary, source_report_count=3)
    with pytest.raises(ValueError, match="first_generated_at"):
        replace(
            summary,
            first_generated_at=datetime(2026, 6, 19, 13, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="average_stage_count"):
        replace(summary, average_stage_count=d("-0.000001"))
    with pytest.raises(ValueError, match="blocked_share"):
        replace(summary, blocked_share=d("0.000000"))
    with pytest.raises(ValueError, match="latest_status"):
        replace(summary, latest_status="skip")
    with pytest.raises(ValueError, match="trend report must be paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="trend report must be report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="trend report must be readonly"):
        replace(summary, readonly=False)


def test_trend_module_has_no_live_auth_order_or_network_imports():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_recommendation_pipeline_trend.py"
    )
    module = ast.parse(module_path.read_text())
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {"dataclasses", "datetime", "decimal"}

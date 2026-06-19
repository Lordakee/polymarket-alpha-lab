import ast
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_trend import (
    PaperRecommendationCycleSnapshotTrendReport,
    build_paper_recommendation_cycle_snapshot_trend_report,
)


GENERATED_AT = datetime(2026, 6, 19, 18, 0, tzinfo=UTC)
CONFIG_VERSION = "paper-recommendation-cycle-snapshot-trend-v0"


@dataclass(frozen=True)
class CycleSnapshotShape:
    generated_at: datetime
    final_status: str
    stage_count: int
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


def snapshot(
    generated_at: datetime = datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    *,
    final_status: str = "pass",
    stage_count: int = 1,
    artifact_count: int = 1,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> CycleSnapshotShape:
    return CycleSnapshotShape(
        generated_at=generated_at,
        final_status=final_status,
        stage_count=stage_count,
        artifact_count=artifact_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def trend_report(
    snapshots: tuple[object, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = CONFIG_VERSION,
) -> PaperRecommendationCycleSnapshotTrendReport:
    return build_paper_recommendation_cycle_snapshot_trend_report(
        generated_at=generated_at,
        config_version=config_version,
        snapshots=snapshots,
    )


def test_cycle_snapshot_trend_computes_counts_shares_averages_and_latest_status():
    summary = trend_report(
        (
            snapshot(
                datetime(2026, 6, 19, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
                final_status="pass",
                stage_count=2,
                artifact_count=5,
            ),
            snapshot(
                datetime(2026, 6, 19, 14, 30, tzinfo=UTC),
                final_status="watch",
                stage_count=4,
                artifact_count=7,
            ),
            snapshot(
                datetime(2026, 6, 19, 15, 0, tzinfo=UTC),
                final_status="blocked",
                stage_count=6,
                artifact_count=9,
            ),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == CONFIG_VERSION
    assert summary.snapshot_count == 3
    assert summary.pass_count == 1
    assert summary.watch_count == 1
    assert summary.blocked_count == 1
    assert summary.first_generated_at == datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
    assert summary.first_generated_at.tzinfo is UTC
    assert summary.last_generated_at == datetime(2026, 6, 19, 15, 0, tzinfo=UTC)
    assert summary.last_generated_at.tzinfo is UTC
    assert summary.latest_status == "blocked"
    assert summary.blocked_share == d("0.333333")
    assert summary.watch_share == d("0.333333")
    assert summary.average_stage_count == d("4.000000")
    assert summary.average_artifact_count == d("7.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_cycle_snapshot_trend_uses_last_input_on_generated_at_tie_for_latest_status():
    summary = trend_report(
        (
            snapshot(final_status="watch", stage_count=1, artifact_count=2),
            snapshot(final_status="blocked", stage_count=3, artifact_count=4),
        ),
    )

    assert summary.snapshot_count == 2
    assert summary.first_generated_at == datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
    assert summary.last_generated_at == datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
    assert summary.latest_status == "blocked"
    assert summary.blocked_share == d("0.500000")
    assert summary.watch_share == d("0.500000")
    assert summary.average_stage_count == d("2.000000")
    assert summary.average_artifact_count == d("3.000000")


def test_cycle_snapshot_trend_rejects_empty_snapshots_or_unsafe_flags():
    with pytest.raises(ValueError, match="snapshots"):
        trend_report(())
    with pytest.raises(ValueError, match="paper_only"):
        trend_report((snapshot(paper_only=False),))
    with pytest.raises(ValueError, match="report_only"):
        trend_report((snapshot(report_only=False),))
    with pytest.raises(ValueError, match="readonly"):
        trend_report((snapshot(readonly=False),))


def test_cycle_snapshot_trend_rejects_invalid_status_and_missing_counts():
    with pytest.raises(ValueError, match="final_status"):
        trend_report((snapshot(final_status="skip"),))
    with pytest.raises(ValueError, match="stage_count"):
        trend_report((snapshot(stage_count=-1),))
    with pytest.raises(ValueError, match="artifact_count"):
        trend_report((snapshot(artifact_count=-1),))
    with pytest.raises(ValueError, match="stage_count"):
        trend_report((snapshot(stage_count=_IntSubclass(1)),))
    with pytest.raises(ValueError, match="artifact_count"):
        trend_report((snapshot(artifact_count=_IntSubclass(1)),))
    with pytest.raises(ValueError, match="stage_count"):
        trend_report((object(),))


def test_cycle_snapshot_trend_is_frozen_and_normalizes_datetimes_to_utc():
    summary = trend_report(
        (
            snapshot(
                datetime(2026, 6, 19, 8, 0, tzinfo=timezone(timedelta(hours=-7))),
                final_status="watch",
                stage_count=1,
                artifact_count=2,
            ),
        ),
        generated_at=datetime(2026, 6, 19, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.first_generated_at == datetime(2026, 6, 19, 15, 0, tzinfo=UTC)
    assert summary.last_generated_at == datetime(2026, 6, 19, 15, 0, tzinfo=UTC)
    assert summary.latest_status == "watch"
    with pytest.raises(FrozenInstanceError):
        summary.latest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        trend_report((snapshot(),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        trend_report((snapshot(generated_at="bad"),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        trend_report(
            (
                snapshot(
                    generated_at=_DatetimeSubclass(2026, 6, 19, 18, 0, tzinfo=UTC),
                ),
            ),
        )


def test_cycle_snapshot_trend_quantization_and_public_types_are_strict():
    summary = trend_report(
        (
            snapshot(stage_count=1, artifact_count=2, final_status="pass"),
            snapshot(stage_count=1, artifact_count=2, final_status="blocked"),
            snapshot(stage_count=2, artifact_count=3, final_status="watch"),
        ),
    )

    assert summary.average_stage_count == d("1.333333")
    assert summary.average_artifact_count == d("2.333333")
    assert summary.blocked_share == d("0.333333")
    assert summary.watch_share == d("0.333333")

    with pytest.raises(ValueError, match="config_version"):
        trend_report((snapshot(),), config_version=" trend-v0")
    with pytest.raises(ValueError, match="config_version"):
        trend_report((snapshot(),), config_version=_StringSubclass("trend-v0"))


def test_cycle_snapshot_trend_constructor_rejects_bad_replacement():
    summary = trend_report(
        (
            snapshot(
                datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
                final_status="pass",
                stage_count=3,
                artifact_count=4,
            ),
            snapshot(
                datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
                final_status="blocked",
                stage_count=5,
                artifact_count=6,
            ),
        ),
    )

    with pytest.raises(ValueError, match="snapshot_count"):
        replace(summary, snapshot_count=3)
    with pytest.raises(ValueError, match="first_generated_at"):
        replace(
            summary,
            first_generated_at=datetime(2026, 6, 19, 13, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="average_stage_count"):
        replace(summary, average_stage_count=d("-0.000001"))
    with pytest.raises(ValueError, match="average_artifact_count"):
        replace(summary, average_artifact_count=d("-0.000001"))
    with pytest.raises(ValueError, match="average_stage_count"):
        replace(summary, average_stage_count=d("3.999999"))
    with pytest.raises(ValueError, match="average_artifact_count"):
        replace(summary, average_artifact_count=d("4.999999"))
    with pytest.raises(ValueError, match="blocked_share"):
        replace(summary, blocked_share=d("0.000000"))
    with pytest.raises(ValueError, match="watch_share"):
        replace(summary, watch_share=d("0.500000"))
    with pytest.raises(ValueError, match="latest_status"):
        replace(summary, latest_status="skip")
    with pytest.raises(ValueError, match="trend report must be paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="trend report must be report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="trend report must be readonly"):
        replace(summary, readonly=False)


def test_cycle_snapshot_trend_module_has_no_live_auth_order_or_network_imports():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_recommendation_cycle_snapshot_trend.py"
    )
    module = ast.parse(module_path.read_text())
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {"dataclasses", "datetime", "decimal"}

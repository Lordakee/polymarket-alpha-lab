import ast
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.paper_recommendation_cycle_snapshot_db_trend as db_trend


GENERATED_AT = datetime(2026, 6, 19, 18, 0, tzinfo=UTC)
TREND_CONFIG_VERSION = "paper-recommendation-cycle-snapshot-db-trend-v0"
SOURCE_CONFIG_VERSION = "paper-recommendation-cycle-snapshot-v0"


@dataclass(frozen=True)
class SnapshotShape:
    generated_at: datetime
    final_status: str
    stage_count: int
    artifact_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def snapshot(
    generated_at: datetime,
    *,
    final_status: str,
    stage_count: int,
    artifact_count: int,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SnapshotShape:
    return SnapshotShape(
        generated_at=generated_at,
        final_status=final_status,
        stage_count=stage_count,
        artifact_count=artifact_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_load_cycle_snapshot_db_trend_filters_limits_and_builds_report(
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
    ) -> tuple[SnapshotShape, ...]:
        calls.append((connection_arg, config_version, limit, table_name))
        return (
            snapshot(
                datetime(2026, 6, 19, 14, 0, tzinfo=UTC),
                final_status="blocked",
                stage_count=6,
                artifact_count=9,
            ),
            snapshot(
                datetime(2026, 6, 19, 13, 0, tzinfo=UTC),
                final_status="watch",
                stage_count=4,
                artifact_count=7,
            ),
            snapshot(
                datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
                final_status="pass",
                stage_count=2,
                artifact_count=5,
            ),
        )

    monkeypatch.setattr(
        db_trend.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )

    report = db_trend.load_paper_recommendation_cycle_snapshot_trend_report(
        generated_at=GENERATED_AT,
        config_version=TREND_CONFIG_VERSION,
        connection=connection,
        source_config_version=SOURCE_CONFIG_VERSION,
        limit=25,
        table_name="cycle_snapshot_archive",
    )

    assert calls == [(connection, SOURCE_CONFIG_VERSION, 25, "cycle_snapshot_archive")]
    assert report.generated_at == GENERATED_AT
    assert report.config_version == TREND_CONFIG_VERSION
    assert report.snapshot_count == 3
    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.first_generated_at == datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
    assert report.last_generated_at == datetime(2026, 6, 19, 14, 0, tzinfo=UTC)
    assert report.latest_status == "blocked"
    assert report.blocked_share == d("0.333333")
    assert report.watch_share == d("0.333333")
    assert report.average_stage_count == d("4.000000")
    assert report.average_artifact_count == d("7.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_load_cycle_snapshot_db_trend_reverses_store_desc_rows_for_tie_latest_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    same_generated_at = datetime(2026, 6, 19, 14, 0, tzinfo=UTC)

    def load_snapshots(
        connection_arg: object,
        *,
        config_version: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_cycle_snapshots",
    ) -> tuple[SnapshotShape, ...]:
        return (
            snapshot(
                same_generated_at,
                final_status="blocked",
                stage_count=3,
                artifact_count=5,
            ),
            snapshot(
                same_generated_at,
                final_status="watch",
                stage_count=1,
                artifact_count=3,
            ),
        )

    monkeypatch.setattr(
        db_trend.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )

    report = db_trend.load_paper_recommendation_cycle_snapshot_trend_report(
        generated_at=GENERATED_AT,
        config_version=TREND_CONFIG_VERSION,
        connection=object(),
    )

    assert report.snapshot_count == 2
    assert report.first_generated_at == same_generated_at
    assert report.last_generated_at == same_generated_at
    assert report.latest_status == "blocked"
    assert report.blocked_share == d("0.500000")
    assert report.watch_share == d("0.500000")


def test_load_cycle_snapshot_db_trend_rejects_empty_snapshot_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_snapshots(
        connection_arg: object,
        *,
        config_version: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_cycle_snapshots",
    ) -> tuple[SnapshotShape, ...]:
        return ()

    monkeypatch.setattr(
        db_trend.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )

    with pytest.raises(ValueError, match="no paper recommendation cycle snapshots"):
        db_trend.load_paper_recommendation_cycle_snapshot_trend_report(
            generated_at=GENERATED_AT,
            config_version=TREND_CONFIG_VERSION,
            connection=object(),
        )


@pytest.mark.parametrize(
    ("flag_name", "message"),
    (
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
        ("readonly", "readonly"),
    ),
)
def test_load_cycle_snapshot_db_trend_rejects_unsafe_loaded_snapshot_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
    message: str,
) -> None:
    def load_snapshots(
        connection_arg: object,
        *,
        config_version: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_recommendation_cycle_snapshots",
    ) -> tuple[SnapshotShape, ...]:
        kwargs = {flag_name: False}
        return (
            snapshot(
                datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
                final_status="pass",
                stage_count=2,
                artifact_count=5,
                **kwargs,
            ),
        )

    monkeypatch.setattr(
        db_trend.paper_recommendation_cycle_snapshot_store,
        "load_paper_recommendation_cycle_snapshots",
        load_snapshots,
    )

    with pytest.raises(ValueError, match=message):
        db_trend.load_paper_recommendation_cycle_snapshot_trend_report(
            generated_at=GENERATED_AT,
            config_version=TREND_CONFIG_VERSION,
            connection=object(),
        )


def test_cycle_snapshot_db_trend_module_has_no_live_driver_or_network_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_recommendation_cycle_snapshot_db_trend.py"
    )
    module = ast.parse(module_path.read_text())
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "eth_account",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "websocket",
        "websockets",
    }

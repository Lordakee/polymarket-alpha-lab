"""Read-only DB helper for persisted paper NAV snapshot trend reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_nav_snapshot_store
from polymarket_alpha_lab.nav_risk_metrics import (
    PaperNavRiskMetricsConfig,
    PaperNavRiskMetricsReport,
    build_paper_nav_risk_metrics_report,
)
from polymarket_alpha_lab.nav_risk_trend import (
    PaperNavRiskTrendConfig,
    PaperNavRiskTrendReport,
    build_paper_nav_risk_trend_report,
)
from polymarket_alpha_lab.positions import PaperNavSnapshot


def load_paper_nav_snapshot_db_trend_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    limit: int | None = None,
    table_name: str = paper_nav_snapshot_store._DEFAULT_TABLE_NAME,
) -> PaperNavRiskTrendReport:
    snapshots = paper_nav_snapshot_store.load_paper_nav_snapshots(
        connection,
        limit=limit,
        table_name=table_name,
    )
    append_order_snapshots = tuple(reversed(snapshots))
    _require_safe_snapshots(append_order_snapshots)
    report_history = _build_nav_risk_report_history(
        append_order_snapshots,
        generated_at=generated_at,
    )
    return build_paper_nav_risk_trend_report(
        report_history,
        config=PaperNavRiskTrendConfig(config_version=config_version),
        generated_at=generated_at,
    )


def _build_nav_risk_report_history(
    nav_snapshots: tuple[PaperNavSnapshot, ...],
    *,
    generated_at: datetime,
) -> tuple[PaperNavRiskMetricsReport, ...]:
    return tuple(
        _build_append_order_nav_risk_metrics_report(
            nav_snapshots[:prefix_size],
            generated_at=generated_at,
        )
        for prefix_size in range(1, len(nav_snapshots) + 1)
    )


def _build_append_order_nav_risk_metrics_report(
    nav_snapshots: tuple[PaperNavSnapshot, ...],
    *,
    generated_at: datetime,
) -> PaperNavRiskMetricsReport:
    return build_paper_nav_risk_metrics_report(
        nav_snapshots,
        config=PaperNavRiskMetricsConfig(
            config_version="nav-risk-metrics-v0",
            preserve_input_order=True,
        ),
        generated_at=generated_at,
    )


def _require_safe_snapshots(
    snapshots: tuple[PaperNavSnapshot, ...],
) -> None:
    for snapshot in snapshots:
        if type(snapshot) is not PaperNavSnapshot:
            raise ValueError(
                "loaded snapshots must contain only PaperNavSnapshot values",
            )
        if getattr(snapshot, "paper_only", None) is not True:
            raise ValueError("paper_only must be True")


__all__ = ("load_paper_nav_snapshot_db_trend_report",)

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_nav_snapshot_store
from polymarket_alpha_lab.paper_nav_liquidity_risk import (
    PaperNavLiquidityRiskConfig,
    PaperNavLiquidityRiskReport,
    build_paper_nav_liquidity_risk_report,
)
from polymarket_alpha_lab.positions import PaperNavSnapshot


_DEFAULT_TABLE_NAME = paper_nav_snapshot_store._DEFAULT_TABLE_NAME


def load_paper_nav_snapshot_db_liquidity_risk_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperNavLiquidityRiskReport:
    snapshots = paper_nav_snapshot_store.load_paper_nav_snapshots(
        connection,
        limit=limit,
        table_name=table_name,
    )
    chronological_snapshots = tuple(reversed(snapshots))
    _require_safe_snapshots(chronological_snapshots)
    return build_paper_nav_liquidity_risk_report(
        chronological_snapshots,
        config=PaperNavLiquidityRiskConfig(config_version=config_version),
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
        if getattr(snapshot, "report_only", True) is not True:
            raise ValueError("report_only must be True")
        if getattr(snapshot, "readonly", True) is not True:
            raise ValueError("readonly must be True")


__all__ = ("load_paper_nav_snapshot_db_liquidity_risk_report",)

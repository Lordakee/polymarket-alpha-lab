"""Read-only load helper for persisted paper order lifecycle history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab.paper_order_lifecycle_db_history import (
    PaperOrderLifecycleDbHistoryConfig,
    PaperOrderLifecycleDbHistoryReport,
    build_paper_order_lifecycle_db_history_report,
)
from polymarket_alpha_lab.paper_order_lifecycle_store import (
    DEFAULT_PAPER_ORDER_LIFECYCLE_RECORDS_TABLE,
    load_paper_order_lifecycle_records,
)


__all__ = ("load_paper_order_lifecycle_db_history_report",)


def load_paper_order_lifecycle_db_history_report(
    connection: object,
    *,
    lifecycle_status: str | None = None,
    limit: int | None,
    table_name: str = DEFAULT_PAPER_ORDER_LIFECYCLE_RECORDS_TABLE,
    config: PaperOrderLifecycleDbHistoryConfig,
    generated_at: datetime,
    loader: Any = load_paper_order_lifecycle_records,
) -> PaperOrderLifecycleDbHistoryReport:
    if type(config) is not PaperOrderLifecycleDbHistoryConfig:
        raise ValueError("config must be a PaperOrderLifecycleDbHistoryConfig")
    if not callable(loader):
        raise ValueError("loader must be callable")

    loaded_records = loader(
        connection,
        lifecycle_status=lifecycle_status,
        limit=limit,
        table_name=table_name,
    )
    chronological_records = tuple(reversed(tuple(loaded_records)))
    return build_paper_order_lifecycle_db_history_report(
        chronological_records,
        config=config,
        generated_at=generated_at,
    )

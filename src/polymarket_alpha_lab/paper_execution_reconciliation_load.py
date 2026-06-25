"""Read-only loader composition for paper execution reconciliation."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from polymarket_alpha_lab.paper_execution_reconciliation import (
    PaperExecutionReconciliationConfig,
    PaperExecutionReconciliationReport,
    build_paper_execution_reconciliation_report,
)
from polymarket_alpha_lab.paper_order_lifecycle import PaperOrderLifecycleRecord
from polymarket_alpha_lab.paper_order_lifecycle_store import (
    load_paper_order_lifecycle_records,
)


__all__ = ("load_paper_execution_reconciliation_report_from_lifecycle",)


def load_paper_execution_reconciliation_report_from_lifecycle(
    connection: object,
    *,
    generated_at: datetime,
    config: PaperExecutionReconciliationConfig,
    lifecycle_status: str | None = None,
    lifecycle_limit: int | None = None,
    lifecycle_table_name: str,
    lifecycle_loader: Callable[..., object] = load_paper_order_lifecycle_records,
    reconciliation_report_builder: Callable[..., object] = (
        build_paper_execution_reconciliation_report
    ),
) -> PaperExecutionReconciliationReport:
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if type(config) is not PaperExecutionReconciliationConfig:
        raise ValueError("config must be exactly PaperExecutionReconciliationConfig")
    _validate_hard_flags("config", config)

    loaded_records = tuple(
        lifecycle_loader(
            connection,
            lifecycle_status=lifecycle_status,
            limit=lifecycle_limit,
            table_name=lifecycle_table_name,
        ),
    )
    _validate_lifecycle_records(loaded_records)

    report = reconciliation_report_builder(
        lifecycle_records=loaded_records,
        config=config,
        generated_at=generated_at,
    )
    _validate_report_output(report)
    return report


def _validate_lifecycle_records(records: tuple[object, ...]) -> None:
    for index, record in enumerate(records):
        label = f"lifecycle_records.{index}"
        if type(record) is not PaperOrderLifecycleRecord:
            raise ValueError(f"{label} must be exactly PaperOrderLifecycleRecord")
        _validate_hard_flags(label, record)


def _validate_report_output(report: object) -> None:
    if type(report) is not PaperExecutionReconciliationReport:
        raise ValueError(
            "reconciliation report must be a PaperExecutionReconciliationReport",
        )
    _validate_hard_flags("reconciliation report", report)


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")

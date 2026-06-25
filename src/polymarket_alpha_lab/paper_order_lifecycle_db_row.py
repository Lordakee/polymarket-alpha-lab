"""DB row codec for paper order lifecycle records."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_order_lifecycle import (
        PaperOrderLifecycleRecord,
    )


__all__ = (
    "PaperOrderLifecycleDbRow",
    "paper_order_lifecycle_record_from_db_row",
    "paper_order_lifecycle_record_to_db_row",
)


@dataclass(frozen=True)
class PaperOrderLifecycleDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    lifecycle_status: str
    recommended_next_step: str
    source_execution_status: str
    source_execution_notional: Decimal
    fill_notional: Decimal
    is_terminal: bool
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool
    report_only: bool
    readonly: bool

    def __post_init__(self) -> None:
        if type(self.report_sha256) is not str or len(self.report_sha256) != 64:
            raise ValueError("report_sha256 must be a 64-char hex string")
        if type(self.generated_at) is not datetime:
            raise ValueError("generated_at must be a datetime")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware")
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("lifecycle_status", self.lifecycle_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_canonical_string("source_execution_status", self.source_execution_status)
        if not isinstance(self.source_execution_notional, Decimal):
            raise ValueError("source_execution_notional must be a Decimal")
        if not isinstance(self.fill_notional, Decimal):
            raise ValueError("fill_notional must be a Decimal")
        if type(self.is_terminal) is not bool:
            raise ValueError("is_terminal must be a bool")
        if type(self.reason_codes_json) is not list:
            raise ValueError("reason_codes_json must be a list")
        if type(self.payload_json) is not dict:
            raise ValueError("payload_json must be a dict")
        if type(self.paper_only) is not bool:
            raise ValueError("paper_only must be a bool")
        if type(self.report_only) is not bool:
            raise ValueError("report_only must be a bool")
        if type(self.readonly) is not bool:
            raise ValueError("readonly must be a bool")


def paper_order_lifecycle_record_to_db_row(
    record: PaperOrderLifecycleRecord,
) -> PaperOrderLifecycleDbRow:
    from polymarket_alpha_lab.paper_order_lifecycle import (
        PaperOrderLifecycleRecord,
    )
    if type(record) is not PaperOrderLifecycleRecord:
        raise ValueError("record must be a PaperOrderLifecycleRecord")
    payload = {
        "generated_at": record.generated_at.isoformat(),
        "config_version": record.config_version,
        "lifecycle_status": record.lifecycle_status,
        "recommended_next_step": record.recommended_next_step,
        "source_execution_status": record.source_execution_status,
        "source_execution_notional": str(record.source_execution_notional),
        "fill_notional": str(record.fill_notional),
        "is_terminal": record.is_terminal,
        "reason_codes": list(record.reason_codes),
        "paper_only": record.paper_only,
        "report_only": record.report_only,
        "readonly": record.readonly,
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    report_sha256 = hashlib.sha256(payload_json.encode()).hexdigest()
    return PaperOrderLifecycleDbRow(
        report_sha256=report_sha256,
        generated_at=record.generated_at,
        config_version=record.config_version,
        lifecycle_status=record.lifecycle_status,
        recommended_next_step=record.recommended_next_step,
        source_execution_status=record.source_execution_status,
        source_execution_notional=record.source_execution_notional,
        fill_notional=record.fill_notional,
        is_terminal=record.is_terminal,
        reason_codes_json=list(record.reason_codes),
        payload_json=payload,
        paper_only=record.paper_only,
        report_only=record.report_only,
        readonly=record.readonly,
    )


def paper_order_lifecycle_record_from_db_row(
    row: PaperOrderLifecycleDbRow,
) -> PaperOrderLifecycleRecord:
    from polymarket_alpha_lab.paper_order_lifecycle import (
        PaperOrderLifecycleRecord,
    )
    if type(row) is not PaperOrderLifecycleDbRow:
        raise ValueError("row must be a PaperOrderLifecycleDbRow")
    return PaperOrderLifecycleRecord(
        generated_at=row.generated_at,
        config_version=row.config_version,
        lifecycle_status=row.lifecycle_status,
        recommended_next_step=row.recommended_next_step,
        source_execution_status=row.source_execution_status,
        source_execution_notional=row.source_execution_notional,
        fill_notional=row.fill_notional,
        is_terminal=row.is_terminal,
        reason_codes=tuple(row.reason_codes_json),
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")

"""Dependency-injected loader composition for readiness digest reports."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_readiness_digest import (
    PaperAutonomousReadinessDigestConfig,
    PaperAutonomousReadinessDigestReport,
    build_paper_autonomous_readiness_digest_report,
)


ReportLoader = Callable[..., object]

__all__ = ("load_paper_autonomous_readiness_digest_report",)


def load_paper_autonomous_readiness_digest_report(
    connection: object,
    *,
    readiness_loader: ReportLoader | None,
    readiness_table_name: str,
    limit: int | None,
    config: PaperAutonomousReadinessDigestConfig,
    generated_at: datetime,
    screening_loader: ReportLoader | None = None,
    screening_table_name: str | None = None,
    transition_loader: ReportLoader | None = None,
    transition_table_name: str | None = None,
    allocation_loader: ReportLoader | None = None,
    allocation_table_name: str | None = None,
    ledger_loader: ReportLoader | None = None,
    ledger_table_name: str | None = None,
) -> PaperAutonomousReadinessDigestReport:
    if type(config) is not PaperAutonomousReadinessDigestConfig:
        raise ValueError("config must be a PaperAutonomousReadinessDigestConfig")
    if readiness_loader is None:
        raise ValueError("readiness_loader is required")

    readiness_report = readiness_loader(
        connection,
        table_name=readiness_table_name,
        limit=limit,
        generated_at=generated_at,
    )
    screening_report = _load_optional_report(
        connection,
        loader=screening_loader,
        table_name=screening_table_name,
        limit=limit,
        generated_at=generated_at,
    )
    transition_report = _load_optional_report(
        connection,
        loader=transition_loader,
        table_name=transition_table_name,
        limit=limit,
        generated_at=generated_at,
    )
    allocation_report = _load_optional_report(
        connection,
        loader=allocation_loader,
        table_name=allocation_table_name,
        limit=limit,
        generated_at=generated_at,
    )
    ledger_report = _load_optional_report(
        connection,
        loader=ledger_loader,
        table_name=ledger_table_name,
        limit=limit,
        generated_at=generated_at,
    )

    return build_paper_autonomous_readiness_digest_report(
        readiness_report,
        screening_report=screening_report,
        transition_report=transition_report,
        allocation_report=allocation_report,
        ledger_report=ledger_report,
        config=config,
        generated_at=generated_at,
    )


def _load_optional_report(
    connection: object,
    *,
    loader: ReportLoader | None,
    table_name: str | None,
    limit: int | None,
    generated_at: datetime,
) -> object | None:
    if loader is None:
        return None
    if table_name is None:
        raise ValueError("optional loader table_name is required")
    return loader(
        connection,
        table_name=table_name,
        limit=limit,
        generated_at=generated_at,
    )

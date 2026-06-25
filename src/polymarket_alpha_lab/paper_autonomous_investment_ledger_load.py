"""Read-only source loader composition for paper autonomous investment ledgers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_investment_ledger import (
    PaperAutonomousInvestmentLedgerConfig,
    PaperAutonomousInvestmentLedgerReport,
    build_paper_autonomous_investment_ledger_report,
)
from polymarket_alpha_lab.paper_broker import PaperBrokerExecutionRecord
from polymarket_alpha_lab.paper_broker_load import load_paper_broker_execution_records


__all__ = ("load_paper_autonomous_investment_ledger_report_from_broker",)


def load_paper_autonomous_investment_ledger_report_from_broker(
    connection: object,
    *,
    generated_at: datetime,
    config: PaperAutonomousInvestmentLedgerConfig,
    broker_execution_status: str | None = None,
    broker_config_version: str | None = None,
    broker_limit: int | None = None,
    broker_table_name: str,
    broker_execution_loader: Callable[..., object] = load_paper_broker_execution_records,
    ledger_report_builder: Callable[..., object] = (
        build_paper_autonomous_investment_ledger_report
    ),
) -> PaperAutonomousInvestmentLedgerReport:
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if type(config) is not PaperAutonomousInvestmentLedgerConfig:
        raise ValueError("config must be exactly PaperAutonomousInvestmentLedgerConfig")
    _validate_hard_flags("config", config)

    loaded_records = tuple(
        broker_execution_loader(
            connection,
            execution_status=broker_execution_status,
            config_version=broker_config_version,
            limit=broker_limit,
            table_name=broker_table_name,
        ),
    )
    _validate_broker_execution_records(loaded_records)

    report = ledger_report_builder(
        broker_execution_records=loaded_records,
        config=config,
        generated_at=generated_at,
    )
    _validate_report_output(report)
    return report


def _validate_broker_execution_records(records: tuple[object, ...]) -> None:
    for index, record in enumerate(records):
        label = f"broker_execution_records.{index}"
        if type(record) is not PaperBrokerExecutionRecord:
            raise ValueError(f"{label} must be exactly PaperBrokerExecutionRecord")
        _validate_hard_flags(label, record)


def _validate_report_output(report: object) -> None:
    if type(report) is not PaperAutonomousInvestmentLedgerReport:
        raise ValueError("ledger report must be a PaperAutonomousInvestmentLedgerReport")
    _validate_hard_flags("ledger report", report)


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")

"""Tests for the investment ledger paper broker source loader."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.paper_autonomous_investment_ledger import (
    PaperAutonomousInvestmentLedgerConfig,
    PaperAutonomousInvestmentLedgerReport,
    build_paper_autonomous_investment_ledger_report,
)
from polymarket_alpha_lab.paper_broker import (
    NEXT_STEP_BY_STATUS,
    PaperBrokerExecutionRecord,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 5, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)


class NoSqlConnection:
    cursor_count = 0
    commit_count = 0
    rollback_count = 0
    close_count = 0
    write_count = 0

    def cursor(self) -> object:
        self.cursor_count += 1
        raise AssertionError("loader node must not open cursors directly")

    def commit(self) -> None:
        self.commit_count += 1
        raise AssertionError("loader node must not commit")

    def rollback(self) -> None:
        self.rollback_count += 1
        raise AssertionError("loader node must not rollback")

    def close(self) -> None:
        self.close_count += 1
        raise AssertionError("loader node must not close the injected connection")

    def write(self, *_args: object, **_kwargs: object) -> None:
        self.write_count += 1
        raise AssertionError("loader node must not write")


def _execution_record(
    *,
    execution_status: str = "paper_submitted",
    source_gate_status: str = "pass",
    source_proposal_total_notional: Decimal = Decimal("12.500000"),
    execution_notional: Decimal = Decimal("12.500000"),
    reason_codes: tuple[str, ...] = ("paper_broker_execution_submitted",),
) -> PaperBrokerExecutionRecord:
    return PaperBrokerExecutionRecord(
        generated_at=SOURCE_GENERATED_AT,
        config_version="paper-broker-v0",
        execution_status=execution_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[execution_status],
        source_gate_status=source_gate_status,
        source_proposal_count=1,
        source_proposal_total_notional=source_proposal_total_notional,
        execution_notional=execution_notional,
        reason_codes=reason_codes,
    )


def _unsafe_execution_record(**overrides: object) -> PaperBrokerExecutionRecord:
    values: dict[str, object] = {
        "generated_at": SOURCE_GENERATED_AT,
        "config_version": "paper-broker-v0",
        "execution_status": "paper_submitted",
        "recommended_next_step": NEXT_STEP_BY_STATUS["paper_submitted"],
        "source_gate_status": "pass",
        "source_proposal_count": 1,
        "source_proposal_total_notional": Decimal("12.500000"),
        "execution_notional": Decimal("12.500000"),
        "reason_codes": ("paper_broker_execution_submitted",),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    record = object.__new__(PaperBrokerExecutionRecord)
    for field_name, value in values.items():
        object.__setattr__(record, field_name, value)
    return record


def test_load_ledger_reads_broker_execution_records_and_calls_reducer() -> None:
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_load import (
        load_paper_autonomous_investment_ledger_report_from_broker,
    )

    connection = NoSqlConnection()
    record = _execution_record()
    config = PaperAutonomousInvestmentLedgerConfig(
        config_version="paper-autonomous-investment-ledger-test-v0",
    )
    calls: list[tuple[str, dict[str, Any]]] = []

    def broker_loader(received_connection: object, **kwargs: Any) -> tuple[object, ...]:
        calls.append(("loader", {"connection": received_connection, **kwargs}))
        return (record,)

    def ledger_builder(**kwargs: Any) -> PaperAutonomousInvestmentLedgerReport:
        calls.append(("builder", dict(kwargs)))
        return build_paper_autonomous_investment_ledger_report(**kwargs)

    report = load_paper_autonomous_investment_ledger_report_from_broker(
        connection,
        broker_execution_status="paper_submitted",
        broker_config_version="paper-broker-v0",
        broker_limit=25,
        broker_table_name="paper_broker_execution_records",
        generated_at=GENERATED_AT,
        config=config,
        broker_execution_loader=broker_loader,
        ledger_report_builder=ledger_builder,
    )

    assert type(report) is PaperAutonomousInvestmentLedgerReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-autonomous-investment-ledger-test-v0"
    assert report.source_record_count == 1
    assert report.submitted_count == 1
    assert report.total_submitted_notional == Decimal("12.500000")
    assert report.reason_codes == ("paper_autonomous_investment_ledger_passed",)
    assert calls == [
        (
            "loader",
            {
                "connection": connection,
                "execution_status": "paper_submitted",
                "config_version": "paper-broker-v0",
                "limit": 25,
                "table_name": "paper_broker_execution_records",
            },
        ),
        (
            "builder",
            {
                "broker_execution_records": (record,),
                "config": config,
                "generated_at": GENERATED_AT,
            },
        ),
    ]
    assert connection.cursor_count == 0
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.write_count == 0


def test_load_ledger_rejects_duck_typed_broker_records_before_reducer() -> None:
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_load import (
        load_paper_autonomous_investment_ledger_report_from_broker,
    )

    builder_calls = 0
    duck_typed_record = SimpleNamespace(
        execution_status="paper_submitted",
        source_gate_status="pass",
        execution_notional=Decimal("12.500000"),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    def ledger_builder(**_kwargs: Any) -> object:
        nonlocal builder_calls
        builder_calls += 1
        raise AssertionError("reducer must not run after broker record type rejection")

    with pytest.raises(
        ValueError,
        match="broker_execution_records.0 must be exactly PaperBrokerExecutionRecord",
    ):
        load_paper_autonomous_investment_ledger_report_from_broker(
            NoSqlConnection(),
            broker_limit=1,
            broker_table_name="paper_broker_execution_records",
            generated_at=GENERATED_AT,
            config=PaperAutonomousInvestmentLedgerConfig(),
            broker_execution_loader=lambda _connection, **_kwargs: (duck_typed_record,),
            ledger_report_builder=ledger_builder,
        )

    assert builder_calls == 0


def test_load_ledger_rejects_non_hard_flagged_broker_records() -> None:
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_load import (
        load_paper_autonomous_investment_ledger_report_from_broker,
    )

    builder_calls = 0
    bad_record = _unsafe_execution_record(readonly=False)

    def ledger_builder(**_kwargs: Any) -> object:
        nonlocal builder_calls
        builder_calls += 1
        raise AssertionError("reducer must not run after hard-flag rejection")

    with pytest.raises(ValueError, match="broker_execution_records.0 must be readonly"):
        load_paper_autonomous_investment_ledger_report_from_broker(
            NoSqlConnection(),
            broker_limit=1,
            broker_table_name="paper_broker_execution_records",
            generated_at=GENERATED_AT,
            config=PaperAutonomousInvestmentLedgerConfig(),
            broker_execution_loader=lambda _connection, **_kwargs: (bad_record,),
            ledger_report_builder=ledger_builder,
        )

    assert builder_calls == 0


def test_load_ledger_rejects_bad_reducer_return_type() -> None:
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_load import (
        load_paper_autonomous_investment_ledger_report_from_broker,
    )

    with pytest.raises(
        ValueError,
        match="ledger report must be a PaperAutonomousInvestmentLedgerReport",
    ):
        load_paper_autonomous_investment_ledger_report_from_broker(
            NoSqlConnection(),
            broker_limit=1,
            broker_table_name="paper_broker_execution_records",
            generated_at=GENERATED_AT,
            config=PaperAutonomousInvestmentLedgerConfig(),
            broker_execution_loader=lambda _connection, **_kwargs: (_execution_record(),),
            ledger_report_builder=lambda **_kwargs: SimpleNamespace(
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
        )


def test_load_ledger_requires_exact_config_type() -> None:
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_load import (
        load_paper_autonomous_investment_ledger_report_from_broker,
    )

    with pytest.raises(
        ValueError,
        match="config must be exactly PaperAutonomousInvestmentLedgerConfig",
    ):
        load_paper_autonomous_investment_ledger_report_from_broker(
            NoSqlConnection(),
            broker_limit=1,
            broker_table_name="paper_broker_execution_records",
            generated_at=GENERATED_AT,
            config=SimpleNamespace(
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
            broker_execution_loader=lambda _connection, **_kwargs: (),
        )

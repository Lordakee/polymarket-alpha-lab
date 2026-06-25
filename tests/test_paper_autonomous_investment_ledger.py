from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_autonomous_investment_ledger import (
    DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_CONFIG_VERSION,
    PaperAutonomousInvestmentLedgerConfig,
    PaperAutonomousInvestmentLedgerEntry,
    PaperAutonomousInvestmentLedgerReport,
    build_paper_autonomous_investment_ledger_report,
)
from polymarket_alpha_lab.paper_broker import PaperBrokerExecutionRecord


ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value).quantize(Decimal("0.000001"))


def _source_record(
    *,
    generated_at: datetime = datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
    execution_status: str = "paper_submitted",
    source_gate_status: str = "pass",
    source_proposal_count: int = 1,
    source_proposal_total_notional: Decimal = d("7.500000"),
    execution_notional: Decimal = d("7.500000"),
    reason_codes: tuple[str, ...] = ("paper_broker_execution_submitted",),
) -> PaperBrokerExecutionRecord:
    return PaperBrokerExecutionRecord(
        generated_at=generated_at,
        config_version="paper-broker-v0",
        execution_status=execution_status,
        recommended_next_step={
            "paper_submitted": "route_to_paper_order_lifecycle",
            "paper_held": "hold_for_broker_review",
            "paper_blocked": "block_paper_execution_pending_repair",
        }[execution_status],
        source_gate_status=source_gate_status,
        source_proposal_count=source_proposal_count,
        source_proposal_total_notional=source_proposal_total_notional,
        execution_notional=execution_notional,
        reason_codes=reason_codes,
    )


def test_ledger_replays_broker_execution_records_into_deterministic_audit_report() -> None:
    earlier_blocked = _source_record(
        generated_at=datetime(2026, 6, 25, 11, 0, tzinfo=UTC),
        execution_status="paper_blocked",
        source_gate_status="blocked",
        source_proposal_total_notional=d("5.000000"),
        execution_notional=ZERO,
        reason_codes=("paper_broker_gate_blocked",),
    )
    latest_submitted = _source_record(
        generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
        execution_status="paper_submitted",
        source_gate_status="pass",
        source_proposal_total_notional=d("7.500000"),
        execution_notional=d("7.500000"),
        reason_codes=("paper_broker_execution_submitted",),
    )
    held = _source_record(
        generated_at=datetime(2026, 6, 25, 10, 30, tzinfo=UTC),
        execution_status="paper_held",
        source_gate_status="watch",
        source_proposal_total_notional=d("3.250000"),
        execution_notional=ZERO,
        reason_codes=("paper_broker_gate_held",),
    )

    report = build_paper_autonomous_investment_ledger_report(
        broker_execution_records=(latest_submitted, held, earlier_blocked),
        generated_at=datetime(2026, 6, 25, 12, 5, tzinfo=UTC),
    )

    assert isinstance(report, PaperAutonomousInvestmentLedgerReport)
    assert report.config_version == DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_CONFIG_VERSION
    assert report.source_record_count == 3
    assert report.submitted_count == 1
    assert report.held_count == 1
    assert report.blocked_count == 1
    assert report.total_submitted_notional == d("7.500000")
    assert report.held_zero_notional_count == 1
    assert report.blocked_zero_notional_count == 1
    assert report.latest_generated_at == datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
    assert report.latest_age_seconds == 300
    assert report.ledger_status == "blocked"
    assert report.recommended_next_step == "block_paper_autonomous_investment_ledger"
    assert report.reason_codes == (
        "paper_autonomous_investment_ledger_blocked_records_present",
        "paper_autonomous_investment_ledger_held_records_present",
    )
    assert tuple(row.reason_code for row in report.reason_code_counts) == (
        "paper_broker_execution_submitted",
        "paper_broker_gate_blocked",
        "paper_broker_gate_held",
    )
    assert tuple(row.source_record_count for row in report.reason_code_counts) == (1, 1, 1)
    assert tuple(
        (
            entry.entry_rank,
            entry.source_generated_at,
            entry.execution_status,
            entry.execution_notional,
        )
        for entry in report.entries
    ) == (
        (1, datetime(2026, 6, 25, 10, 30, tzinfo=UTC), "paper_held", ZERO),
        (2, datetime(2026, 6, 25, 11, 0, tzinfo=UTC), "paper_blocked", ZERO),
        (3, datetime(2026, 6, 25, 12, 0, tzinfo=UTC), "paper_submitted", d("7.500000")),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(isinstance(entry, PaperAutonomousInvestmentLedgerEntry) for entry in report.entries)


def test_ledger_blocks_empty_source_records() -> None:
    report = build_paper_autonomous_investment_ledger_report(
        broker_execution_records=(),
        generated_at=datetime(2026, 6, 25, 12, 5, tzinfo=UTC),
    )

    assert report.source_record_count == 0
    assert report.ledger_status == "blocked"
    assert report.recommended_next_step == "block_paper_autonomous_investment_ledger"
    assert report.latest_generated_at is None
    assert report.latest_age_seconds is None
    assert report.reason_codes == ("paper_autonomous_investment_ledger_no_source_records",)
    assert report.reason_code_counts == ()
    assert report.entries == ()


def test_ledger_watches_stale_source_records() -> None:
    report = build_paper_autonomous_investment_ledger_report(
        broker_execution_records=(
            _source_record(generated_at=datetime(2026, 6, 25, 11, 0, tzinfo=UTC)),
        ),
        config=PaperAutonomousInvestmentLedgerConfig(
            max_latest_source_age_seconds=60,
        ),
        generated_at=datetime(2026, 6, 25, 12, 5, tzinfo=UTC),
    )

    assert report.ledger_status == "watch"
    assert report.recommended_next_step == "review_paper_autonomous_investment_ledger"
    assert report.latest_age_seconds == 3900
    assert report.reason_codes == ("paper_autonomous_investment_ledger_stale_source_records",)


def test_ledger_passes_fresh_submitted_records() -> None:
    report = build_paper_autonomous_investment_ledger_report(
        broker_execution_records=(
            _source_record(generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=UTC)),
        ),
        generated_at=datetime(2026, 6, 25, 12, 5, tzinfo=UTC),
    )

    assert report.ledger_status == "pass"
    assert report.recommended_next_step == "archive_paper_autonomous_investment_ledger"
    assert report.reason_codes == ("paper_autonomous_investment_ledger_passed",)


def test_ledger_rejects_non_tuple_or_duck_typed_source_records() -> None:
    record = _source_record()
    with pytest.raises(ValueError, match="broker_execution_records must be a tuple"):
        build_paper_autonomous_investment_ledger_report(
            broker_execution_records=[record],  # type: ignore[arg-type]
            generated_at=datetime(2026, 6, 25, 12, 5, tzinfo=UTC),
        )

    class DuckRecord:
        pass

    duck_typed = DuckRecord()
    for field_name in (
        "generated_at",
        "config_version",
        "execution_status",
        "recommended_next_step",
        "source_gate_status",
        "source_proposal_count",
        "source_proposal_total_notional",
        "execution_notional",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ):
        setattr(duck_typed, field_name, getattr(record, field_name))

    with pytest.raises(ValueError, match="exact PaperBrokerExecutionRecord"):
        build_paper_autonomous_investment_ledger_report(
            broker_execution_records=(duck_typed,),
            generated_at=datetime(2026, 6, 25, 12, 5, tzinfo=UTC),
        )


def test_ledger_rejects_non_hard_flagged_source_records() -> None:
    record = _source_record()
    object.__setattr__(record, "readonly", False)

    with pytest.raises(ValueError, match="readonly must be True"):
        build_paper_autonomous_investment_ledger_report(
            broker_execution_records=(record,),
            generated_at=datetime(2026, 6, 25, 12, 5, tzinfo=UTC),
        )


def test_ledger_rejects_source_records_newer_than_generated_at() -> None:
    with pytest.raises(ValueError, match="source records must not be newer than generated_at"):
        build_paper_autonomous_investment_ledger_report(
            broker_execution_records=(
                _source_record(generated_at=datetime(2026, 6, 25, 12, 6, tzinfo=UTC)),
            ),
            generated_at=datetime(2026, 6, 25, 12, 5, tzinfo=UTC),
        )


def test_ledger_rejects_naive_generated_at() -> None:
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_paper_autonomous_investment_ledger_report(
            broker_execution_records=(),
            generated_at=datetime(2026, 6, 25, 12, 5),
        )


def test_ledger_config_rejects_subclassing() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):
        class SubConfig(PaperAutonomousInvestmentLedgerConfig):
            pass

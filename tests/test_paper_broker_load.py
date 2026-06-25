"""Tests for paper broker DB-API load helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.paper_broker import (
    NEXT_STEP_BY_STATUS,
    PaperBrokerExecutionRecord,
)
from polymarket_alpha_lab.paper_broker_db_row import (
    PaperBrokerExecutionDbRow,
    to_db_row,
)
from polymarket_alpha_lab.paper_broker_load import (
    DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE,
    load_paper_broker_execution_records,
)


def _record(
    execution_status: str,
    *,
    minute: int,
    execution_notional: Decimal = Decimal("0.000000"),
    source_proposal_count: int = 1,
) -> PaperBrokerExecutionRecord:
    return PaperBrokerExecutionRecord(
        generated_at=datetime(2026, 6, 25, 10, minute, tzinfo=UTC),
        config_version="paper-broker-v0",
        execution_status=execution_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[execution_status],
        source_gate_status={
            "paper_submitted": "pass",
            "paper_blocked": "blocked",
            "paper_held": "watch",
        }[execution_status],
        source_proposal_count=source_proposal_count,
        source_proposal_total_notional=execution_notional,
        execution_notional=execution_notional,
        reason_codes=(f"{execution_status}_reason",),
    )


def _row_tuple(row: PaperBrokerExecutionDbRow) -> tuple[Any, ...]:
    return (
        row.record_sha256,
        row.generated_at,
        row.config_version,
        row.execution_status,
        row.recommended_next_step,
        row.source_gate_status,
        row.source_proposal_count,
        row.source_proposal_total_notional,
        row.execution_notional,
        row.reason_codes_json,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _row_mapping(row: PaperBrokerExecutionDbRow) -> dict[str, Any]:
    return {
        "record_sha256": row.record_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "execution_status": row.execution_status,
        "recommended_next_step": row.recommended_next_step,
        "source_gate_status": row.source_gate_status,
        "source_proposal_count": row.source_proposal_count,
        "source_proposal_total_notional": row.source_proposal_total_notional,
        "execution_notional": row.execution_notional,
        "reason_codes": row.reason_codes_json,
        "payload": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


class FakeCursor:
    def __init__(self, rows: tuple[Any, ...]) -> None:
        self.rows = rows
        self.executed: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.executed.append((sql, params))

    def fetchall(self) -> tuple[Any, ...]:
        return self.rows

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.cursor_instance = cursor

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def commit(self) -> None:
        raise AssertionError("load helper must not commit")

    def rollback(self) -> None:
        raise AssertionError("load helper must not rollback")

    def close(self) -> None:
        raise AssertionError("load helper must not close")


def test_default_table_name() -> None:
    assert DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE == "paper_broker_execution_records"


def test_load_helper_reads_desc_rows_converts_via_db_row_codec_and_does_not_own_connection() -> None:
    newest = _record(
        "paper_submitted",
        minute=3,
        execution_notional=Decimal("3.000000"),
    )
    oldest = _record("paper_blocked", minute=1)
    cursor = FakeCursor(
        (
            _row_tuple(to_db_row(newest)),
            to_db_row(oldest),
        ),
    )
    connection = FakeConnection(cursor)

    loaded = load_paper_broker_execution_records(
        connection,
        execution_status="paper_submitted",
        config_version="paper-broker-v0",
        limit=25,
        table_name="paper_broker_execution_records",
    )

    assert loaded == (newest, oldest)
    assert cursor.closed is True
    assert len(cursor.executed) == 1
    sql, params = cursor.executed[0]
    assert "reason_codes," in sql
    assert "payload," in sql
    assert "reason_codes_json" not in sql
    assert "payload_json" not in sql
    assert "FROM paper_broker_execution_records" in sql
    assert "WHERE execution_status = %s AND config_version = %s" in sql
    assert "ORDER BY generated_at DESC, inserted_at DESC, record_sha256 DESC" in sql
    assert "LIMIT %s" in sql
    assert params == ("paper_submitted", "paper-broker-v0", 25)


def test_load_helper_accepts_mapping_rows_and_validates_query_inputs() -> None:
    record = _record(
        "paper_submitted",
        minute=1,
        execution_notional=Decimal("1.000000"),
    )
    cursor = FakeCursor((_row_mapping(to_db_row(record)),))

    assert load_paper_broker_execution_records(FakeConnection(cursor)) == (record,)

    with pytest.raises(ValueError, match="simple lowercase identifier"):
        load_paper_broker_execution_records(
            FakeConnection(FakeCursor(())),
            table_name="bad;drop",
        )
    with pytest.raises(ValueError, match="canonical nonblank"):
        load_paper_broker_execution_records(
            FakeConnection(FakeCursor(())),
            execution_status="",
        )
    with pytest.raises(ValueError, match="canonical nonblank"):
        load_paper_broker_execution_records(
            FakeConnection(FakeCursor(())),
            config_version=" paper-broker-v0",
        )
    with pytest.raises(ValueError, match="must be positive"):
        load_paper_broker_execution_records(FakeConnection(FakeCursor(())), limit=0)


def test_load_helper_rejects_rows_that_do_not_match_selected_columns() -> None:
    with pytest.raises(ValueError, match="selected paper broker columns"):
        load_paper_broker_execution_records(FakeConnection(FakeCursor((("too-short",),))))

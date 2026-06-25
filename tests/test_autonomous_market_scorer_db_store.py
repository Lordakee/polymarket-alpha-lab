"""Tests for autonomous market scorer DB-API persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.autonomous_market_scorer import (
    AutonomousMarketScorerReport,
    AutonomousMarketScoreRow,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def _report(
    *,
    generated_at: datetime = datetime(2026, 6, 25, 14, 30, tzinfo=UTC),
    config_version: str = "autonomous-market-scorer-v0",
    gate_status: str = "pass",
) -> AutonomousMarketScorerReport:
    score_rows = ()
    if gate_status == "pass":
        score_rows = (
            AutonomousMarketScoreRow(
                condition_id="condition-alpha",
                market_slug="alpha-market",
                question="Will alpha happen?",
                scoring_side="yes",
                confidence_score=d("0.800000"),
                liquidity_score=d("0.700000"),
                spread_score=d("0.600000"),
                edge_score=d("0.500000"),
                cost_score=d("0.900000"),
                risk_score=d("0.300000"),
                total_score=d("0.650000"),
                score_status="scored",
                recommended_notional=d("10.000000"),
                estimated_edge=d("0.050000"),
                reason_codes=("alpha_scored",),
            ),
        )
    return AutonomousMarketScorerReport(
        generated_at=generated_at,
        config_version=config_version,
        gate_status=gate_status,
        markets_scored=1 if gate_status == "pass" else 0,
        markets_skipped=1 if gate_status == "watch" else 0,
        markets_blocked=1 if gate_status == "blocked" else 0,
        top_total_score=d("0.650000") if gate_status == "pass" else d("0.000000"),
        average_total_score=d("0.650000") if gate_status == "pass" else d("0.000000"),
        total_recommended_notional=(
            d("10.000000") if gate_status == "pass" else d("0.000000")
        ),
        score_rows=score_rows,
        reason_codes=(f"autonomous_market_scorer_{gate_status}",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


class FakeCursor:
    def __init__(
        self,
        *,
        rowcount: int = 1,
        records: list[Any] | None = None,
    ) -> None:
        self.rowcount = rowcount
        self.records = [] if records is None else records
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchall(self) -> list[Any]:
        return self.records

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(
        self,
        *,
        rowcount: int = 1,
        records: list[Any] | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(rowcount=rowcount, records=records)
        self.cursor_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance


def test_default_table_name() -> None:
    from polymarket_alpha_lab.autonomous_market_scorer_store import (
        DEFAULT_AUTONOMOUS_MARKET_SCORER_REPORTS_TABLE,
    )

    assert (
        DEFAULT_AUTONOMOUS_MARKET_SCORER_REPORTS_TABLE
        == "autonomous_market_scorer_reports"
    )


def test_insert_uses_db_api_insert_with_on_conflict_do_nothing() -> None:
    from polymarket_alpha_lab.autonomous_market_scorer_db_row import to_db_row
    from polymarket_alpha_lab.autonomous_market_scorer_store import (
        AutonomousMarketScorerInsertResult,
        insert_autonomous_market_scorer_report_with_result,
    )

    report = _report()
    expected_row = to_db_row(report)
    conn = FakeConnection(rowcount=1)

    result = insert_autonomous_market_scorer_report_with_result(
        conn,
        report,
        table_name="autonomous_market_scorer_archive",
    )

    assert result == AutonomousMarketScorerInsertResult(
        row=expected_row,
        inserted=True,
    )
    assert conn.cursor_count == 1
    assert conn.cursor_instance.closed is True
    sql, params = conn.cursor_instance.calls[0]
    assert "INSERT INTO autonomous_market_scorer_archive" in sql
    assert "ON CONFLICT (report_sha256) DO NOTHING" in sql
    assert params[0] == expected_row.report_sha256
    assert params[13] == expected_row.reason_codes_json
    assert params[14] == expected_row.score_rows_json
    assert params[15] == expected_row.payload_json


def test_insert_convenience_returns_row_and_dedup_result_reports_false() -> None:
    from polymarket_alpha_lab.autonomous_market_scorer_db_row import (
        AutonomousMarketScorerDbRow,
    )
    from polymarket_alpha_lab.autonomous_market_scorer_store import (
        insert_autonomous_market_scorer_report,
        insert_autonomous_market_scorer_report_with_result,
    )

    report = _report()

    assert isinstance(
        insert_autonomous_market_scorer_report(FakeConnection(rowcount=1), report),
        AutonomousMarketScorerDbRow,
    )
    assert (
        insert_autonomous_market_scorer_report_with_result(
            FakeConnection(rowcount=0),
            report,
        ).inserted
        is False
    )


def test_insert_result_validates_shape() -> None:
    from polymarket_alpha_lab.autonomous_market_scorer_db_row import to_db_row
    from polymarket_alpha_lab.autonomous_market_scorer_store import (
        AutonomousMarketScorerInsertResult,
    )

    row = to_db_row(_report())
    with pytest.raises(ValueError, match="AutonomousMarketScorerDbRow"):
        AutonomousMarketScorerInsertResult(row="bad", inserted=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="inserted must be a bool"):
        AutonomousMarketScorerInsertResult(row=row, inserted=1)  # type: ignore[arg-type]


def test_insert_rejects_unexpected_rowcount() -> None:
    from polymarket_alpha_lab.autonomous_market_scorer_store import (
        insert_autonomous_market_scorer_report_with_result,
    )

    with pytest.raises(ValueError, match="rowcount must be 0 or 1"):
        insert_autonomous_market_scorer_report_with_result(
            FakeConnection(rowcount=2),
            _report(),
        )


def test_load_orders_by_generated_inserted_and_hash_and_reconstructs_reports() -> None:
    from polymarket_alpha_lab.autonomous_market_scorer_db_row import to_db_row
    from polymarket_alpha_lab.autonomous_market_scorer_store import (
        load_autonomous_market_scorer_reports,
    )

    first = _report(
        generated_at=datetime(2026, 6, 25, 14, 30, tzinfo=UTC),
        config_version="autonomous-market-scorer-v0",
        gate_status="pass",
    )
    second = _report(
        generated_at=datetime(2026, 6, 25, 14, 29, tzinfo=UTC),
        config_version="autonomous-market-scorer-v1",
        gate_status="blocked",
    )
    records = [to_db_row(first), to_db_row(second)]
    conn = FakeConnection(records=records)

    loaded = load_autonomous_market_scorer_reports(
        conn,
        config_version="autonomous-market-scorer-v0",
        gate_status="pass",
        limit=5,
        table_name="autonomous_market_scorer_archive",
    )

    assert loaded == (first, second)
    sql, params = conn.cursor_instance.calls[0]
    assert "FROM autonomous_market_scorer_archive" in sql
    assert "WHERE config_version = %s AND gate_status = %s" in sql
    assert "ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC" in sql
    assert "LIMIT %s" in sql
    assert params == ("autonomous-market-scorer-v0", "pass", 5)
    assert conn.cursor_instance.closed is True


def test_load_accepts_mapping_and_tuple_records() -> None:
    from polymarket_alpha_lab.autonomous_market_scorer_db_row import to_db_row
    from polymarket_alpha_lab.autonomous_market_scorer_store import (
        SELECT_COLUMNS,
        load_autonomous_market_scorer_reports,
    )

    report = _report()
    row = to_db_row(report)
    mapping = {
        "reason_codes": row.reason_codes_json,
        "score_rows": row.score_rows_json,
        "payload": row.payload_json,
    }
    mapping.update(
        {
            column: getattr(row, column)
            for column in SELECT_COLUMNS
            if column not in ("reason_codes", "score_rows", "payload")
        },
    )
    tuple_record = tuple(mapping[column] for column in SELECT_COLUMNS)

    assert load_autonomous_market_scorer_reports(
        FakeConnection(records=[mapping, tuple_record]),
    ) == (report, report)


@pytest.mark.parametrize("table_name", ("DROP TABLE scorer", "bad-name", "_bad", "bad_"))
def test_store_rejects_bad_table_name(table_name: str) -> None:
    from polymarket_alpha_lab.autonomous_market_scorer_store import (
        insert_autonomous_market_scorer_report,
    )

    with pytest.raises(ValueError, match="simple lowercase identifier"):
        insert_autonomous_market_scorer_report(
            FakeConnection(),
            _report(),
            table_name=table_name,
        )


def test_load_rejects_bad_filters_and_limit() -> None:
    from polymarket_alpha_lab.autonomous_market_scorer_store import (
        load_autonomous_market_scorer_reports,
    )

    with pytest.raises(ValueError, match="gate_status must be pass, watch, or blocked"):
        load_autonomous_market_scorer_reports(FakeConnection(), gate_status="paused")
    with pytest.raises(ValueError, match="canonical nonblank"):
        load_autonomous_market_scorer_reports(FakeConnection(), config_version="")
    with pytest.raises(ValueError, match="must be positive"):
        load_autonomous_market_scorer_reports(FakeConnection(), limit=0)


def test_store_module_has_no_forbidden_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/autonomous_market_scorer_store.py",
    ).read_text(encoding="utf-8")

    for token in (
        "psycopg",
        "supabase",
        "os.environ",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "socket",
        "asyncio",
        "private_key",
        "wallet",
        "account",
        "submit_order",
        "cancel_order",
        "replace_order",
        "approve",
        "open(",
        "print(",
    ):
        assert token not in source, f"forbidden token found: {token}"

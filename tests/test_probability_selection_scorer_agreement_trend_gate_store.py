"""Tests for probability selection/scorer agreement trend-gate persistence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate import (
    ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount,
    ProbabilitySelectionScorerAgreementTrendGateReport,
)


GENERATED_AT = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)


def _report(
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "probability-selection-scorer-agreement-trend-gate-v0",
    gate_status: str = "watch",
) -> ProbabilitySelectionScorerAgreementTrendGateReport:
    reason_codes = _reason_codes(gate_status)
    return ProbabilitySelectionScorerAgreementTrendGateReport(
        generated_at=generated_at,
        config_version=config_version,
        source_config_version="probability-selection-scorer-agreement-trend-v0",
        source_generated_at=generated_at - timedelta(minutes=1),
        trend_report_age_seconds=60,
        gate_status=gate_status,
        recommended_next_step=_next_step(gate_status),
        reason_code_counts=tuple(
            ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount(
                reason_code=reason_code,
                report_count=1,
            )
            for reason_code in reason_codes
        ),
        source_report_count=4,
        source_trend_status="watch",
        source_recommended_next_step="review_selection_scorer_disagreement",
        latest_agreement_status="low_overlap",
        latest_agreement_status_streak=2,
        aligned_report_count=2,
        low_overlap_report_count=2,
        gate_blocked_report_count=0,
        missing_inputs_report_count=0,
        insufficient_identifiers_report_count=0,
        average_selected_count=Decimal("2.500000"),
        average_scorer_candidate_count=Decimal("3.250000"),
        latest_source_reason_codes=("latest_agreement_low_overlap",),
        recurring_source_reason_code_counts=(("low_selection_scorer_overlap", 2),),
        reason_codes=reason_codes,
    )


def _reason_codes(gate_status: str) -> tuple[str, ...]:
    if gate_status == "pass":
        return ("probability_selection_scorer_agreement_trend_gate_passed",)
    if gate_status == "blocked":
        return ("latest_probability_selection_scorer_agreement_trend_blocked",)
    return ("latest_probability_selection_scorer_agreement_trend_watch",)


def _next_step(gate_status: str) -> str:
    return {
        "pass": "allow_probability_selection_scorer_agreement_trend_review",
        "watch": "throttle_probability_selection_scorer_agreement_trend_review",
        "blocked": "block_probability_selection_scorer_agreement_trend_review",
    }[gate_status]


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
        self.execute_error: BaseException | None = None
        self.close_error: BaseException | None = None

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> list[Any]:
        return self.records

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(
        self,
        *,
        rowcount: int = 1,
        records: list[Any] | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(rowcount=rowcount, records=records)
        self.cursor_count = 0
        self.commit_count = 0
        self.rollback_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def test_default_table_name() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_REPORTS_TABLE,
    )

    assert (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_REPORTS_TABLE
        == "probability_selection_scorer_agreement_trend_gate_reports"
    )


def test_insert_uses_parameterized_insert_with_on_conflict_do_nothing() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row import (
        to_db_row,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
        ProbabilitySelectionScorerAgreementTrendGateInsertResult,
        insert_probability_selection_scorer_agreement_trend_gate_report_with_result,
    )

    report = _report()
    expected_row = to_db_row(report)
    conn = FakeConnection(rowcount=1)

    result = insert_probability_selection_scorer_agreement_trend_gate_report_with_result(
        conn,
        report,
        table_name="probability_selection_scorer_agreement_trend_gate_archive",
    )

    assert result == ProbabilitySelectionScorerAgreementTrendGateInsertResult(
        row=expected_row,
        inserted=True,
    )
    assert conn.cursor_count == 1
    assert conn.commit_count == 0
    assert conn.rollback_count == 0
    assert conn.cursor_instance.closed is True
    sql, params = conn.cursor_instance.calls[0]
    assert "INSERT INTO probability_selection_scorer_agreement_trend_gate_archive" in sql
    assert "ON CONFLICT (report_sha256) DO NOTHING" in sql
    assert "%s" in sql
    assert params[0] == expected_row.report_sha256
    assert params[8] == expected_row.reason_code_counts_json
    assert params[21] == expected_row.latest_source_reason_codes_json
    assert params[22] == expected_row.recurring_source_reason_code_counts_json
    assert params[23] == expected_row.reason_codes_json
    assert params[24] == expected_row.payload_json


def test_insert_convenience_returns_row_and_dedup_result_reports_false() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row import (
        ProbabilitySelectionScorerAgreementTrendGateDbRow,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
        insert_probability_selection_scorer_agreement_trend_gate_report,
        insert_probability_selection_scorer_agreement_trend_gate_report_with_result,
    )

    report = _report()

    assert isinstance(
        insert_probability_selection_scorer_agreement_trend_gate_report(
            FakeConnection(rowcount=1),
            report,
        ),
        ProbabilitySelectionScorerAgreementTrendGateDbRow,
    )
    assert (
        insert_probability_selection_scorer_agreement_trend_gate_report_with_result(
            FakeConnection(rowcount=0),
            report,
        ).inserted
        is False
    )


def test_insert_preserves_execute_error_when_cursor_close_also_fails() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
        insert_probability_selection_scorer_agreement_trend_gate_report_with_result,
    )

    connection = FakeConnection()
    execute_error = RuntimeError("execute failed")
    connection.cursor_instance.execute_error = execute_error
    connection.cursor_instance.close_error = RuntimeError("close failed")

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        insert_probability_selection_scorer_agreement_trend_gate_report_with_result(
            connection,
            _report(),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


def test_insert_propagates_cursor_close_error_after_success() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
        insert_probability_selection_scorer_agreement_trend_gate_report_with_result,
    )

    connection = FakeConnection()
    close_error = RuntimeError("close failed")
    connection.cursor_instance.close_error = close_error

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        insert_probability_selection_scorer_agreement_trend_gate_report_with_result(
            connection,
            _report(),
        )

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_filters_orders_and_reconstructs_reports() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row import (
        to_db_row,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
        load_probability_selection_scorer_agreement_trend_gate_reports,
    )

    first = _report()
    second = _report(
        generated_at=datetime(2026, 6, 30, 11, 59, tzinfo=UTC),
        config_version="probability-selection-scorer-agreement-trend-gate-v1",
        gate_status="blocked",
    )
    records = [to_db_row(first), to_db_row(second)]
    conn = FakeConnection(records=records)

    loaded = load_probability_selection_scorer_agreement_trend_gate_reports(
        conn,
        config_version="probability-selection-scorer-agreement-trend-gate-v0",
        gate_status="watch",
        limit=5,
        table_name="probability_selection_scorer_agreement_trend_gate_archive",
    )

    assert loaded == (first, second)
    assert conn.commit_count == 0
    assert conn.rollback_count == 0
    assert conn.cursor_instance.closed is True
    sql, params = conn.cursor_instance.calls[0]
    assert "FROM probability_selection_scorer_agreement_trend_gate_archive" in sql
    assert "WHERE config_version = %s AND gate_status = %s" in sql
    assert "ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC" in sql
    assert "LIMIT %s" in sql
    assert params == (
        "probability-selection-scorer-agreement-trend-gate-v0",
        "watch",
        5,
    )


def test_load_preserves_execute_error_when_cursor_close_also_fails() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
        load_probability_selection_scorer_agreement_trend_gate_reports,
    )

    connection = FakeConnection()
    execute_error = RuntimeError("execute failed")
    connection.cursor_instance.execute_error = execute_error
    connection.cursor_instance.close_error = RuntimeError("close failed")

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        load_probability_selection_scorer_agreement_trend_gate_reports(connection)

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


def test_load_propagates_cursor_close_error_after_success() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
        load_probability_selection_scorer_agreement_trend_gate_reports,
    )

    connection = FakeConnection()
    close_error = RuntimeError("close failed")
    connection.cursor_instance.close_error = close_error

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        load_probability_selection_scorer_agreement_trend_gate_reports(connection)

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_accepts_mapping_and_tuple_records() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row import (
        to_db_row,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
        SELECT_COLUMNS,
        load_probability_selection_scorer_agreement_trend_gate_reports,
    )

    report = _report()
    row = to_db_row(report)
    mapping = {
        "reason_code_counts": row.reason_code_counts_json,
        "latest_source_reason_codes": row.latest_source_reason_codes_json,
        "recurring_source_reason_code_counts": (
            row.recurring_source_reason_code_counts_json
        ),
        "reason_codes": row.reason_codes_json,
        "payload": row.payload_json,
    }
    mapping.update(
        {
            column: getattr(row, column)
            for column in SELECT_COLUMNS
            if column
            not in (
                "reason_code_counts",
                "latest_source_reason_codes",
                "recurring_source_reason_code_counts",
                "reason_codes",
                "payload",
            )
        },
    )
    tuple_record = tuple(mapping[column] for column in SELECT_COLUMNS)

    assert load_probability_selection_scorer_agreement_trend_gate_reports(
        FakeConnection(records=[mapping, tuple_record]),
    ) == (report, report)


def test_store_rejects_bad_table_filters_and_limit_without_sql() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
        insert_probability_selection_scorer_agreement_trend_gate_report,
        load_probability_selection_scorer_agreement_trend_gate_reports,
    )

    for table_name in ("DROP TABLE gate", "bad-name", "_bad", "bad_"):
        connection = FakeConnection()
        with pytest.raises(ValueError, match="simple lowercase identifier"):
            insert_probability_selection_scorer_agreement_trend_gate_report(
                connection,
                _report(),
                table_name=table_name,
            )
        assert connection.cursor_count == 0
        assert connection.commit_count == 0
        assert connection.rollback_count == 0

    for kwargs, message in (
        ({"gate_status": "paused"}, "gate_status"),
        ({"config_version": ""}, "config_version"),
        ({"limit": 0}, "limit"),
    ):
        connection = FakeConnection()
        with pytest.raises(ValueError, match=message):
            load_probability_selection_scorer_agreement_trend_gate_reports(
                connection,
                **kwargs,
            )
        assert connection.cursor_count == 0
        assert connection.commit_count == 0
        assert connection.rollback_count == 0


def test_store_module_has_no_forbidden_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "probability_selection_scorer_agreement_trend_gate_store.py",
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
        "commit(",
        "rollback(",
    ):
        assert token not in source, f"forbidden token found: {token}"

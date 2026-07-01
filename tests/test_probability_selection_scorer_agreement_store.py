"""Tests for probability selection/scorer agreement DB-API persistence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_selection_scorer_agreement import (
    ProbabilitySelectionScorerAgreementReport,
)


GENERATED_AT = datetime(2026, 6, 27, 12, 0, tzinfo=UTC)


def _report(
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "probability-selection-scorer-agreement-v0",
    agreement_status: str = "aligned",
) -> ProbabilitySelectionScorerAgreementReport:
    return ProbabilitySelectionScorerAgreementReport(
        generated_at=generated_at,
        config_version=config_version,
        selection_generated_at=generated_at - timedelta(minutes=2),
        scorer_generated_at=generated_at - timedelta(minutes=1),
        selected_count=2,
        scorer_candidate_count=3,
        selected_market_overlap_count=2,
        selected_condition_overlap_count=2,
        rejected_but_scored_count=0,
        scored_but_unselected_count=1,
        scorer_gate_status="pass" if agreement_status != "gate_blocked" else "blocked",
        agreement_status=agreement_status,
        recommended_next_step=_next_step(agreement_status),
        reason_codes=_reason_codes(agreement_status),
        reason_code_divergence_counts=(("model_passed", 1),),
    )


def _next_step(agreement_status: str) -> str:
    if agreement_status == "gate_blocked":
        return "review_scorer_gate"
    if agreement_status == "low_overlap":
        return "review_selection_scorer_disagreement"
    if agreement_status in ("missing_inputs", "insufficient_identifiers"):
        return "enrich_inputs"
    return "continue_monitoring"


def _reason_codes(agreement_status: str) -> tuple[str, ...]:
    if agreement_status == "gate_blocked":
        return ("scorer_gate_blocked",)
    if agreement_status == "low_overlap":
        return ("low_selection_scorer_overlap",)
    if agreement_status == "missing_inputs":
        return ("missing_inputs",)
    if agreement_status == "insufficient_identifiers":
        return ("insufficient_identifiers",)
    return ("scored_but_unselected", "selection_scorer_aligned")


class FakeCursor:
    def __init__(
        self,
        *,
        rowcount: int = 1,
        records: list[Any] | None = None,
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.rowcount = rowcount
        self.records = [] if records is None else records
        self.execute_error = execute_error
        self.fetchall_error = fetchall_error
        self.close_error = close_error
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> list[Any]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
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
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rowcount=rowcount,
            records=records,
            execute_error=execute_error,
            fetchall_error=fetchall_error,
            close_error=close_error,
        )
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
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_REPORTS_TABLE,
    )

    assert (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_REPORTS_TABLE
        == "probability_selection_scorer_agreement_reports"
    )


def test_insert_uses_parameterized_insert_with_on_conflict_do_nothing() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_db_row import (
        to_db_row,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        ProbabilitySelectionScorerAgreementInsertResult,
        insert_probability_selection_scorer_agreement_report_with_result,
    )

    report = _report()
    expected_row = to_db_row(report)
    conn = FakeConnection(rowcount=1)

    result = insert_probability_selection_scorer_agreement_report_with_result(
        conn,
        report,
        table_name="probability_selection_scorer_agreement_archive",
    )

    assert result == ProbabilitySelectionScorerAgreementInsertResult(
        row=expected_row,
        inserted=True,
    )
    assert conn.cursor_count == 1
    assert conn.commit_count == 0
    assert conn.rollback_count == 0
    assert conn.cursor_instance.closed is True
    sql, params = conn.cursor_instance.calls[0]
    assert "INSERT INTO probability_selection_scorer_agreement_archive" in sql
    assert "ON CONFLICT (report_sha256) DO NOTHING" in sql
    assert params[0] == expected_row.report_sha256
    assert params[14] == expected_row.reason_codes_json
    assert params[15] == expected_row.reason_code_divergence_counts_json
    assert params[16] == expected_row.payload_json


def test_insert_convenience_returns_row_and_dedup_result_reports_false() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_db_row import (
        ProbabilitySelectionScorerAgreementDbRow,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        insert_probability_selection_scorer_agreement_report,
        insert_probability_selection_scorer_agreement_report_with_result,
    )

    report = _report()

    assert isinstance(
        insert_probability_selection_scorer_agreement_report(
            FakeConnection(rowcount=1),
            report,
        ),
        ProbabilitySelectionScorerAgreementDbRow,
    )
    assert (
        insert_probability_selection_scorer_agreement_report_with_result(
            FakeConnection(rowcount=0),
            report,
        ).inserted
        is False
    )


def test_insert_result_validates_shape() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_db_row import (
        to_db_row,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        ProbabilitySelectionScorerAgreementInsertResult,
    )

    row = to_db_row(_report())
    with pytest.raises(ValueError, match="ProbabilitySelectionScorerAgreementDbRow"):
        ProbabilitySelectionScorerAgreementInsertResult(row="bad", inserted=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="inserted must be a bool"):
        ProbabilitySelectionScorerAgreementInsertResult(row=row, inserted=1)  # type: ignore[arg-type]


def test_insert_rejects_unexpected_rowcount() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        insert_probability_selection_scorer_agreement_report_with_result,
    )

    with pytest.raises(ValueError, match="rowcount must be 0 or 1"):
        insert_probability_selection_scorer_agreement_report_with_result(
            FakeConnection(rowcount=2),
            _report(),
        )


def test_load_filters_orders_and_reconstructs_reports() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_db_row import (
        to_db_row,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        load_probability_selection_scorer_agreement_reports,
    )

    first = _report(
        generated_at=datetime(2026, 6, 27, 12, 0, tzinfo=UTC),
        config_version="probability-selection-scorer-agreement-v0",
        agreement_status="aligned",
    )
    second = _report(
        generated_at=datetime(2026, 6, 27, 11, 59, tzinfo=UTC),
        config_version="probability-selection-scorer-agreement-v1",
        agreement_status="gate_blocked",
    )
    records = [to_db_row(first), to_db_row(second)]
    conn = FakeConnection(records=records)

    loaded = load_probability_selection_scorer_agreement_reports(
        conn,
        config_version="probability-selection-scorer-agreement-v0",
        agreement_status="aligned",
        limit=5,
        table_name="probability_selection_scorer_agreement_archive",
    )

    assert loaded == (first, second)
    assert conn.commit_count == 0
    assert conn.rollback_count == 0
    assert conn.cursor_instance.closed is True
    sql, params = conn.cursor_instance.calls[0]
    assert "FROM probability_selection_scorer_agreement_archive" in sql
    assert "WHERE config_version = %s AND agreement_status = %s" in sql
    assert "ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC" in sql
    assert "LIMIT %s" in sql
    assert params == ("probability-selection-scorer-agreement-v0", "aligned", 5)


def test_load_accepts_mapping_and_tuple_records() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_db_row import (
        to_db_row,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        SELECT_COLUMNS,
        load_probability_selection_scorer_agreement_reports,
    )

    report = _report()
    row = to_db_row(report)
    mapping = {
        "reason_codes": row.reason_codes_json,
        "reason_code_divergence_counts": row.reason_code_divergence_counts_json,
        "payload": row.payload_json,
    }
    mapping.update(
        {
            column: getattr(row, column)
            for column in SELECT_COLUMNS
            if column
            not in ("reason_codes", "reason_code_divergence_counts", "payload")
        },
    )
    tuple_record = tuple(mapping[column] for column in SELECT_COLUMNS)

    assert load_probability_selection_scorer_agreement_reports(
        FakeConnection(records=[mapping, tuple_record]),
    ) == (report, report)


@pytest.mark.parametrize("operation", ("insert", "load"))
def test_cursor_close_error_after_success_is_propagated(operation: str) -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        insert_probability_selection_scorer_agreement_report,
        load_probability_selection_scorer_agreement_reports,
    )

    connection = FakeConnection(close_error=RuntimeError("cursor close failed"))

    with pytest.raises(RuntimeError, match="cursor close failed") as exc_info:
        if operation == "insert":
            insert_probability_selection_scorer_agreement_report(
                connection,
                _report(),
            )
        else:
            load_probability_selection_scorer_agreement_reports(connection)

    assert exc_info.value is connection.cursor_instance.close_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("operation", "operation_error_name"),
    (("insert", "execute_error"), ("load", "fetchall_error")),
)
def test_operation_error_wins_when_cursor_close_also_fails(
    operation: str,
    operation_error_name: str,
) -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        insert_probability_selection_scorer_agreement_report,
        load_probability_selection_scorer_agreement_reports,
    )

    operation_error = RuntimeError("db operation failed")
    close_error = RuntimeError("cursor close failed")
    connection = FakeConnection(
        **{
            operation_error_name: operation_error,
            "close_error": close_error,
        },
    )

    with pytest.raises(RuntimeError, match="db operation failed") as exc_info:
        if operation == "insert":
            insert_probability_selection_scorer_agreement_report(
                connection,
                _report(),
            )
        else:
            load_probability_selection_scorer_agreement_reports(connection)

    assert exc_info.value is operation_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("operation", "operation_error_name"),
    (("insert", "execute_error"), ("load", "fetchall_error")),
)
def test_base_exception_operation_error_still_closes_cursor(
    operation: str,
    operation_error_name: str,
) -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        insert_probability_selection_scorer_agreement_report,
        load_probability_selection_scorer_agreement_reports,
    )

    class NonExceptionOperationFailure(BaseException):
        pass

    operation_error = NonExceptionOperationFailure("operation interrupted")
    connection = FakeConnection(**{operation_error_name: operation_error})

    with pytest.raises(NonExceptionOperationFailure) as exc_info:
        if operation == "insert":
            insert_probability_selection_scorer_agreement_report(connection, _report())
        else:
            load_probability_selection_scorer_agreement_reports(connection)

    assert exc_info.value is operation_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    "table_name",
    ("DROP TABLE agreement", "bad-name", "_bad", "bad_"),
)
def test_store_rejects_bad_table_name(table_name: str) -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        insert_probability_selection_scorer_agreement_report,
    )

    connection = FakeConnection()
    with pytest.raises(ValueError, match="simple lowercase identifier"):
        insert_probability_selection_scorer_agreement_report(
            connection,
            _report(),
            table_name=table_name,
        )
    assert connection.cursor_count == 0
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_rejects_bad_filters_and_limit_without_sql() -> None:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        load_probability_selection_scorer_agreement_reports,
    )

    for kwargs, message in (
        ({"agreement_status": "paused"}, "agreement_status"),
        ({"config_version": ""}, "config_version"),
        ({"limit": 0}, "limit"),
    ):
        connection = FakeConnection()
        with pytest.raises(ValueError, match=message):
            load_probability_selection_scorer_agreement_reports(
                connection,
                **kwargs,
            )
        assert connection.cursor_count == 0
        assert connection.commit_count == 0
        assert connection.rollback_count == 0


def test_store_module_has_no_forbidden_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/probability_selection_scorer_agreement_store.py",
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

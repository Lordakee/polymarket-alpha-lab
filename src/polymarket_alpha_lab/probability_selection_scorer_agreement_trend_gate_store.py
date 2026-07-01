"""DB-API repository for probability selection/scorer agreement trend-gate reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row import (
    ProbabilitySelectionScorerAgreementTrendGateDbRow,
    probability_selection_scorer_agreement_trend_gate_report_from_db_row,
    probability_selection_scorer_agreement_trend_gate_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate import (
        ProbabilitySelectionScorerAgreementTrendGateReport,
    )


__all__ = (
    "DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_REPORTS_TABLE",
    "SELECT_COLUMNS",
    "ProbabilitySelectionScorerAgreementTrendGateInsertResult",
    "insert_probability_selection_scorer_agreement_trend_gate_report",
    "insert_probability_selection_scorer_agreement_trend_gate_report_with_result",
    "load_probability_selection_scorer_agreement_trend_gate_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_GATE_STATUSES = ("pass", "watch", "blocked")
DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_REPORTS_TABLE = (
    "probability_selection_scorer_agreement_trend_gate_reports"
)
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_config_version",
    "source_generated_at",
    "trend_report_age_seconds",
    "gate_status",
    "recommended_next_step",
    "reason_code_counts",
    "source_report_count",
    "source_trend_status",
    "source_recommended_next_step",
    "latest_agreement_status",
    "latest_agreement_status_streak",
    "aligned_report_count",
    "low_overlap_report_count",
    "gate_blocked_report_count",
    "missing_inputs_report_count",
    "insufficient_identifiers_report_count",
    "average_selected_count",
    "average_scorer_candidate_count",
    "latest_source_reason_codes",
    "recurring_source_reason_code_counts",
    "reason_codes",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementTrendGateInsertResult:
    row: ProbabilitySelectionScorerAgreementTrendGateDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not ProbabilitySelectionScorerAgreementTrendGateDbRow:
            raise ValueError(
                "row must be a ProbabilitySelectionScorerAgreementTrendGateDbRow",
            )
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_probability_selection_scorer_agreement_trend_gate_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_REPORTS_TABLE
    ),
) -> ProbabilitySelectionScorerAgreementTrendGateDbRow:
    return insert_probability_selection_scorer_agreement_trend_gate_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_probability_selection_scorer_agreement_trend_gate_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_REPORTS_TABLE
    ),
) -> ProbabilitySelectionScorerAgreementTrendGateInsertResult:
    table_name = _validate_table_name(table_name)
    row = probability_selection_scorer_agreement_trend_gate_report_to_db_row(report)
    columns = ",\n            ".join(SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _ in SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = tuple(_param_for_column(row, column) for column in SELECT_COLUMNS)
    cursor = connection.cursor()
    operation_error: BaseException | None = None
    try:
        cursor.execute(sql, params)
        rowcount = cursor.rowcount
        if rowcount not in (0, 1):
            raise ValueError("insert rowcount must be 0 or 1; rowcount must be 0 or 1")
    except BaseException as exc:
        operation_error = exc
        raise
    finally:
        _close_cursor(cursor, operation_error)
    return ProbabilitySelectionScorerAgreementTrendGateInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_probability_selection_scorer_agreement_trend_gate_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    gate_status: str | None = None,
    limit: int | None = None,
    table_name: str = (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_REPORTS_TABLE
    ),
) -> tuple["ProbabilitySelectionScorerAgreementTrendGateReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if gate_status is not None:
        _require_gate_status("gate_status", gate_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if gate_status is not None:
        conditions.append("gate_status = %s")
        params.append(gate_status)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT %s"
        params.append(limit)

    columns = ",\n            ".join(SELECT_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {table_name}
        {where_clause}
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        {limit_clause}
        """
    cursor = connection.cursor()
    operation_error: BaseException | None = None
    try:
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
        rows = tuple(_db_row_from_record(record) for record in records)
        reports = tuple(
            probability_selection_scorer_agreement_trend_gate_report_from_db_row(row)
            for row in rows
        )
    except BaseException as exc:
        operation_error = exc
        raise
    finally:
        _close_cursor(cursor, operation_error)
    return reports


def _close_cursor(cursor: Any, operation_error: BaseException | None) -> None:
    if operation_error is None:
        cursor.close()
        return
    try:
        cursor.close()
    except BaseException:
        pass


def _param_for_column(
    row: ProbabilitySelectionScorerAgreementTrendGateDbRow,
    column: str,
) -> Any:
    if column == "reason_code_counts":
        return row.reason_code_counts_json
    if column == "latest_source_reason_codes":
        return row.latest_source_reason_codes_json
    if column == "recurring_source_reason_code_counts":
        return row.recurring_source_reason_code_counts_json
    if column == "reason_codes":
        return row.reason_codes_json
    if column == "payload":
        return row.payload_json
    return getattr(row, column)


def _db_row_from_record(record: Any) -> ProbabilitySelectionScorerAgreementTrendGateDbRow:
    if isinstance(record, ProbabilitySelectionScorerAgreementTrendGateDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(SELECT_COLUMNS):
        raise ValueError("DB row must contain selected trend-gate columns")
    return ProbabilitySelectionScorerAgreementTrendGateDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        source_config_version=values[3],
        source_generated_at=values[4],
        trend_report_age_seconds=values[5],
        gate_status=values[6],
        recommended_next_step=values[7],
        reason_code_counts_json=_normalize_json_array("reason_code_counts", values[8]),
        source_report_count=values[9],
        source_trend_status=values[10],
        source_recommended_next_step=values[11],
        latest_agreement_status=values[12],
        latest_agreement_status_streak=values[13],
        aligned_report_count=values[14],
        low_overlap_report_count=values[15],
        gate_blocked_report_count=values[16],
        missing_inputs_report_count=values[17],
        insufficient_identifiers_report_count=values[18],
        average_selected_count=values[19],
        average_scorer_candidate_count=values[20],
        latest_source_reason_codes_json=_normalize_json_array(
            "latest_source_reason_codes",
            values[21],
        ),
        recurring_source_reason_code_counts_json=_normalize_json_array(
            "recurring_source_reason_code_counts",
            values[22],
        ),
        reason_codes_json=_normalize_json_array("reason_codes", values[23]),
        payload_json=_normalize_json_object("payload", values[24]),
        paper_only=values[25],
        report_only=values[26],
        readonly=values[27],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")

"""DB-API repository for probability selection/scorer agreement reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.probability_selection_scorer_agreement_db_row import (
    ProbabilitySelectionScorerAgreementDbRow,
    probability_selection_scorer_agreement_report_from_db_row,
    probability_selection_scorer_agreement_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.probability_selection_scorer_agreement import (
        ProbabilitySelectionScorerAgreementReport,
    )


__all__ = (
    "DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_REPORTS_TABLE",
    "SELECT_COLUMNS",
    "ProbabilitySelectionScorerAgreementInsertResult",
    "insert_probability_selection_scorer_agreement_report",
    "insert_probability_selection_scorer_agreement_report_with_result",
    "load_probability_selection_scorer_agreement_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_REPORTS_TABLE = (
    "probability_selection_scorer_agreement_reports"
)
_AGREEMENT_STATUSES = (
    "aligned",
    "gate_blocked",
    "insufficient_identifiers",
    "low_overlap",
    "missing_inputs",
)
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "selection_generated_at",
    "scorer_generated_at",
    "selected_count",
    "scorer_candidate_count",
    "selected_market_overlap_count",
    "selected_condition_overlap_count",
    "rejected_but_scored_count",
    "scored_but_unselected_count",
    "scorer_gate_status",
    "agreement_status",
    "recommended_next_step",
    "reason_codes",
    "reason_code_divergence_counts",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementInsertResult:
    row: ProbabilitySelectionScorerAgreementDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not ProbabilitySelectionScorerAgreementDbRow:
            raise ValueError(
                "row must be a ProbabilitySelectionScorerAgreementDbRow",
            )
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_probability_selection_scorer_agreement_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_REPORTS_TABLE,
) -> ProbabilitySelectionScorerAgreementDbRow:
    return insert_probability_selection_scorer_agreement_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_probability_selection_scorer_agreement_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_REPORTS_TABLE,
) -> ProbabilitySelectionScorerAgreementInsertResult:
    table_name = _validate_table_name(table_name)
    row = probability_selection_scorer_agreement_report_to_db_row(report)
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
    try:
        cursor.execute(sql, params)
        rowcount = cursor.rowcount
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    if rowcount not in (0, 1):
        raise ValueError("insert rowcount must be 0 or 1; rowcount must be 0 or 1")
    return ProbabilitySelectionScorerAgreementInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_probability_selection_scorer_agreement_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    agreement_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_REPORTS_TABLE,
) -> tuple["ProbabilitySelectionScorerAgreementReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if agreement_status is not None:
        _require_agreement_status("agreement_status", agreement_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if agreement_status is not None:
        conditions.append("agreement_status = %s")
        params.append(agreement_status)

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
    try:
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(
        probability_selection_scorer_agreement_report_from_db_row(row)
        for row in rows
    )


def _param_for_column(
    row: ProbabilitySelectionScorerAgreementDbRow,
    column: str,
) -> Any:
    if column == "reason_codes":
        return row.reason_codes_json
    if column == "reason_code_divergence_counts":
        return row.reason_code_divergence_counts_json
    if column == "payload":
        return row.payload_json
    return getattr(row, column)


def _close_cursor_after_operation_error(cursor: Any) -> None:
    try:
        cursor.close()
    except BaseException:
        pass


def _db_row_from_record(record: Any) -> ProbabilitySelectionScorerAgreementDbRow:
    if isinstance(record, ProbabilitySelectionScorerAgreementDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(SELECT_COLUMNS):
        raise ValueError("DB row must contain selected agreement columns")
    return ProbabilitySelectionScorerAgreementDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        selection_generated_at=values[3],
        scorer_generated_at=values[4],
        selected_count=values[5],
        scorer_candidate_count=values[6],
        selected_market_overlap_count=values[7],
        selected_condition_overlap_count=values[8],
        rejected_but_scored_count=values[9],
        scored_but_unselected_count=values[10],
        scorer_gate_status=values[11],
        agreement_status=values[12],
        recommended_next_step=values[13],
        reason_codes_json=_normalize_json_array("reason_codes", values[14]),
        reason_code_divergence_counts_json=_normalize_json_array(
            "reason_code_divergence_counts",
            values[15],
        ),
        payload_json=_normalize_json_object("payload", values[16]),
        paper_only=values[17],
        report_only=values[18],
        readonly=values[19],
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


def _require_agreement_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _AGREEMENT_STATUSES:
        raise ValueError(f"{field_name} must be a known agreement status")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")

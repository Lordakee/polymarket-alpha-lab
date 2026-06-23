"""DB-API repository for paper autonomous screening decision-support gate reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row import (
    PaperAutonomousScreeningDecisionSupportGateDbRow,
    paper_autonomous_screening_decision_support_gate_report_from_db_row,
    paper_autonomous_screening_decision_support_gate_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
        PaperAutonomousScreeningDecisionSupportGateReport,
    )


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE",
    "PaperAutonomousScreeningDecisionSupportGateInsertResult",
    "insert_paper_autonomous_screening_decision_support_gate_report",
    "insert_paper_autonomous_screening_decision_support_gate_report_with_result",
    "load_paper_autonomous_screening_decision_support_gate_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
_GATE_STATUSES = ("pass", "watch", "blocked")
DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE = (
    "paper_autonomous_screening_decision_support_gate_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "gate_status",
    "recommended_next_step",
    "reason_codes_json",
    "reason_code_counts_json",
    "operator_flow_gate_config_version",
    "operator_flow_gate_generated_at",
    "operator_flow_gate_status",
    "operator_flow_recommended_next_step",
    "queue_priority_generated_at",
    "queue_risk_generated_at",
    "queue_risk_config_version",
    "queue_risk_status",
    "queue_risk_recommended_next_step",
    "queue_source_report_count",
    "queue_research_ready_count",
    "queue_watch_count",
    "queue_blocked_count",
    "queue_candidate_count",
    "queue_ready_count",
    "queue_candidate_watch_count",
    "queue_candidate_blocked_count",
    "queue_total_ready_notional",
    "queue_largest_ready_notional",
    "queue_top_research_priority_score",
    "queue_average_research_priority_score",
    "trend_source_snapshot_count",
    "trend_latest_risk_status",
    "trend_consecutive_latest_watch_count",
    "trend_consecutive_latest_blocked_count",
    "trend_duplicate_generated_at_count",
    "rank_stability_status",
    "rank_stable_ready_count",
    "rank_unstable_ready_count",
    "rank_blocked_count",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateInsertResult:
    row: PaperAutonomousScreeningDecisionSupportGateDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperAutonomousScreeningDecisionSupportGateDbRow:
            raise ValueError(
                "row must be a PaperAutonomousScreeningDecisionSupportGateDbRow",
            )
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_autonomous_screening_decision_support_gate_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE
    ),
) -> PaperAutonomousScreeningDecisionSupportGateDbRow:
    return insert_paper_autonomous_screening_decision_support_gate_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_autonomous_screening_decision_support_gate_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE
    ),
) -> PaperAutonomousScreeningDecisionSupportGateInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_autonomous_screening_decision_support_gate_report_to_db_row(report)
    columns = ",\n            ".join(_SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _ in _SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = tuple(getattr(row, column) for column in _SELECT_COLUMNS)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        rowcount = cursor.rowcount
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    if rowcount not in (0, 1):
        raise ValueError("insert rowcount must be 0 or 1")
    return PaperAutonomousScreeningDecisionSupportGateInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_autonomous_screening_decision_support_gate_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    gate_status: str | None = None,
    queue_risk_config_version: str | None = None,
    operator_flow_gate_status: str | None = None,
    limit: int | None = None,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE
    ),
) -> tuple["PaperAutonomousScreeningDecisionSupportGateReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if gate_status is not None:
        _require_gate_status("gate_status", gate_status)
    if queue_risk_config_version is not None:
        _require_canonical_string(
            "queue_risk_config_version",
            queue_risk_config_version,
        )
    if operator_flow_gate_status is not None:
        _require_gate_status("operator_flow_gate_status", operator_flow_gate_status)
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
    if queue_risk_config_version is not None:
        conditions.append("queue_risk_config_version = %s")
        params.append(queue_risk_config_version)
    if operator_flow_gate_status is not None:
        conditions.append("operator_flow_gate_status = %s")
        params.append(operator_flow_gate_status)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT %s"
        params.append(limit)

    columns = ",\n            ".join(_SELECT_COLUMNS)
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
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(
        paper_autonomous_screening_decision_support_gate_report_from_db_row(row)
        for row in rows
    )


def _db_row_from_record(
    record: Any,
) -> PaperAutonomousScreeningDecisionSupportGateDbRow:
    if isinstance(record, PaperAutonomousScreeningDecisionSupportGateDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected autonomous screening gate columns")
    return PaperAutonomousScreeningDecisionSupportGateDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        gate_status=values[3],
        recommended_next_step=values[4],
        reason_codes_json=_normalize_json_array("reason_codes_json", values[5]),
        reason_code_counts_json=_normalize_json_array(
            "reason_code_counts_json",
            values[6],
        ),
        operator_flow_gate_config_version=values[7],
        operator_flow_gate_generated_at=values[8],
        operator_flow_gate_status=values[9],
        operator_flow_recommended_next_step=values[10],
        queue_priority_generated_at=values[11],
        queue_risk_generated_at=values[12],
        queue_risk_config_version=values[13],
        queue_risk_status=values[14],
        queue_risk_recommended_next_step=values[15],
        queue_source_report_count=values[16],
        queue_research_ready_count=values[17],
        queue_watch_count=values[18],
        queue_blocked_count=values[19],
        queue_candidate_count=values[20],
        queue_ready_count=values[21],
        queue_candidate_watch_count=values[22],
        queue_candidate_blocked_count=values[23],
        queue_total_ready_notional=values[24],
        queue_largest_ready_notional=values[25],
        queue_top_research_priority_score=values[26],
        queue_average_research_priority_score=values[27],
        trend_source_snapshot_count=values[28],
        trend_latest_risk_status=values[29],
        trend_consecutive_latest_watch_count=values[30],
        trend_consecutive_latest_blocked_count=values[31],
        trend_duplicate_generated_at_count=values[32],
        rank_stability_status=values[33],
        rank_stable_ready_count=values[34],
        rank_unstable_ready_count=values[35],
        rank_blocked_count=values[36],
        payload_json=_normalize_json_object("payload_json", values[37]),
        paper_only=values[38],
        report_only=values[39],
        readonly=values[40],
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
        raise ValueError(_TABLE_NAME_ERROR)
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

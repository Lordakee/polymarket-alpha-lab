"""DB-API repository for strategy recommendation rank stability reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.strategy_recommendation_rank_stability_db_row import (
    PaperStrategyRecommendationRankStabilityDbRow,
    strategy_recommendation_rank_stability_report_from_db_row,
    strategy_recommendation_rank_stability_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.strategy_recommendation_rank_stability import (
        PaperStrategyRecommendationRankStabilityReport,
    )


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_RANK_STABILITY_REPORTS_TABLE",
    "StrategyRecommendationRankStabilityInsertResult",
    "insert_strategy_recommendation_rank_stability_report",
    "insert_strategy_recommendation_rank_stability_report_with_result",
    "load_strategy_recommendation_rank_stability_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
_STABILITY_STATUSES = ("stable", "watch", "blocked")
DEFAULT_STRATEGY_RECOMMENDATION_RANK_STABILITY_REPORTS_TABLE = (
    "strategy_recommendation_rank_stability_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "stability_status",
    "reason_codes_json",
    "source_report_count",
    "candidate_count",
    "stable_count",
    "watch_count",
    "blocked_count",
    "stable_ready_count",
    "unstable_ready_count",
    "selected_side_changed_count",
    "queue_status_changed_count",
    "latest_generated_at",
    "top_stable_market_slug",
    "rows_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class StrategyRecommendationRankStabilityInsertResult:
    row: PaperStrategyRecommendationRankStabilityDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperStrategyRecommendationRankStabilityDbRow:
            raise ValueError(
                "row must be a PaperStrategyRecommendationRankStabilityDbRow",
            )
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_strategy_recommendation_rank_stability_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_STRATEGY_RECOMMENDATION_RANK_STABILITY_REPORTS_TABLE,
) -> PaperStrategyRecommendationRankStabilityDbRow:
    return insert_strategy_recommendation_rank_stability_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_strategy_recommendation_rank_stability_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_STRATEGY_RECOMMENDATION_RANK_STABILITY_REPORTS_TABLE,
) -> StrategyRecommendationRankStabilityInsertResult:
    table_name = _validate_table_name(table_name)
    row = strategy_recommendation_rank_stability_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            stability_status,
            reason_codes_json,
            source_report_count,
            candidate_count,
            stable_count,
            watch_count,
            blocked_count,
            stable_ready_count,
            unstable_ready_count,
            selected_side_changed_count,
            queue_status_changed_count,
            latest_generated_at,
            top_stable_market_slug,
            rows_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = tuple(getattr(row, column) for column in _SELECT_COLUMNS)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        rowcount = cursor.rowcount
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    if rowcount not in (0, 1):
        raise ValueError("insert rowcount must be 0 or 1")
    return StrategyRecommendationRankStabilityInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_strategy_recommendation_rank_stability_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    stability_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_STRATEGY_RECOMMENDATION_RANK_STABILITY_REPORTS_TABLE,
) -> tuple["PaperStrategyRecommendationRankStabilityReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if stability_status is not None:
        _require_stability_status("stability_status", stability_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if stability_status is not None:
        conditions.append("stability_status = %s")
        params.append(stability_status)

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
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(strategy_recommendation_rank_stability_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperStrategyRecommendationRankStabilityDbRow:
    if isinstance(record, PaperStrategyRecommendationRankStabilityDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected rank stability columns")
    return PaperStrategyRecommendationRankStabilityDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        stability_status=values[3],
        reason_codes_json=_normalize_json_array("reason_codes_json", values[4]),
        source_report_count=values[5],
        candidate_count=values[6],
        stable_count=values[7],
        watch_count=values[8],
        blocked_count=values[9],
        stable_ready_count=values[10],
        unstable_ready_count=values[11],
        selected_side_changed_count=values[12],
        queue_status_changed_count=values[13],
        latest_generated_at=values[14],
        top_stable_market_slug=values[15],
        rows_json=_normalize_json_array("rows_json", values[16]),
        payload_json=_normalize_json_object("payload_json", values[17]),
        paper_only=values[18],
        report_only=values[19],
        readonly=values[20],
    )


def _close_cursor_after_operation_error(cursor: Any) -> None:
    try:
        cursor.close()
    except BaseException:
        pass


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


def _require_stability_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STABILITY_STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")

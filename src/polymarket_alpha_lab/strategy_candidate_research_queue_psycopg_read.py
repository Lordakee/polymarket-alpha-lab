"""Read-only psycopg query layer for strategy candidate research queue reports."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re
from typing import Any, TypeVar

from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
)
from polymarket_alpha_lab.strategy_candidate_research_queue_db_row import (
    PaperStrategyCandidateResearchQueueDbRow,
    paper_strategy_candidate_research_queue_report_from_db_row,
)
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config import (
    STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR,
)


DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_TABLE = (
    "paper_strategy_candidate_research_queue_reports"
)
MAX_STRATEGY_CANDIDATE_RESEARCH_QUEUE_READ_LIMIT = 500

_ACTION_STATUSES = ("research_ready", "watch", "blocked")
_RESEARCH_STATUSES = ("ready", "watch", "blocked")
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_config_version",
    "action_status",
    "recommended_next_step",
    "research_status",
    "candidate_count",
    "research_ready_count",
    "watch_count",
    "blocked_count",
    "selected_count",
    "skipped_count",
    "not_selected_count",
    "total_ready_notional",
    "total_selected_notional",
    "total_suggested_notional",
    "top_research_priority_score",
    "average_research_ready_score",
    "source_reason_code_counts",
    "primary_reason_code_counts",
    "reason_codes",
    "rows",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)
_T = TypeVar("_T")


@dataclass(frozen=True)
class PaperStrategyCandidateResearchQueueReadOptions:
    source_config_version: str | None = None
    action_status: str | None = None
    research_status: str | None = None
    limit: int = 100
    table_name: str = DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_TABLE

    def __post_init__(self) -> None:
        if self.source_config_version is not None:
            _require_canonical_string(
                "source_config_version",
                self.source_config_version,
            )
        if self.action_status is not None:
            _require_action_status("action_status", self.action_status)
        if self.research_status is not None:
            _require_research_status("research_status", self.research_status)
        _require_bounded_limit("limit", self.limit)
        object.__setattr__(self, "table_name", _validate_table_name(self.table_name))


def load_paper_strategy_candidate_research_queue_reports(
    connection: Any,
    *,
    options: PaperStrategyCandidateResearchQueueReadOptions | None = None,
) -> tuple[PaperStrategyCandidateResearchQueueReport, ...]:
    read_options = (
        options if options is not None else PaperStrategyCandidateResearchQueueReadOptions()
    )
    if type(read_options) is not PaperStrategyCandidateResearchQueueReadOptions:
        raise ValueError("options must be a PaperStrategyCandidateResearchQueueReadOptions")

    where_parts: list[str] = []
    params: list[Any] = []
    if read_options.source_config_version is not None:
        where_parts.append("source_config_version = %s")
        params.append(read_options.source_config_version)
    if read_options.action_status is not None:
        where_parts.append("action_status = %s")
        params.append(read_options.action_status)
    if read_options.research_status is not None:
        where_parts.append("research_status = %s")
        params.append(read_options.research_status)
    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    columns = ",\n            ".join(_SELECT_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {read_options.table_name}
        {where_clause}
        ORDER BY generated_at DESC, report_sha256 DESC
        LIMIT %s
        """
    params.append(read_options.limit)

    cursor = connection.cursor()
    try:
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
    finally:
        cursor.close()

    return tuple(
        paper_strategy_candidate_research_queue_report_from_db_row(
            _db_row_from_record(record),
        )
        for record in records
    )


def load_paper_strategy_candidate_research_queue_reports_with_psycopg(
    dsn: str,
    *,
    options: PaperStrategyCandidateResearchQueueReadOptions | None = None,
) -> tuple[PaperStrategyCandidateResearchQueueReport, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_paper_strategy_candidate_research_queue_reports(
            connection,
            options=options,
        ),
    )


def _with_owned_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN_ENV_VAR,
    )
    connection = _connect(dsn)
    try:
        result = operation(connection)
    except BaseException:
        try:
            connection.close()
        except Exception:
            pass
        raise
    connection.close()
    return result


def _connect(dsn: str) -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the strategy candidate research queue "
            "read adapter; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the strategy candidate research queue read database",
        ) from None


def _db_row_from_record(record: Any) -> PaperStrategyCandidateResearchQueueDbRow:
    if isinstance(record, PaperStrategyCandidateResearchQueueDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError(
            "DB row must contain selected strategy candidate research queue columns",
        )
    return PaperStrategyCandidateResearchQueueDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        source_config_version=values[3],
        action_status=values[4],
        recommended_next_step=values[5],
        research_status=values[6],
        candidate_count=values[7],
        research_ready_count=values[8],
        watch_count=values[9],
        blocked_count=values[10],
        selected_count=values[11],
        skipped_count=values[12],
        not_selected_count=values[13],
        total_ready_notional=values[14],
        total_selected_notional=values[15],
        total_suggested_notional=values[16],
        top_research_priority_score=values[17],
        average_research_ready_score=values[18],
        source_reason_code_counts_json=_normalize_json_object(
            "source_reason_code_counts",
            values[19],
        ),
        primary_reason_code_counts_json=_normalize_json_object(
            "primary_reason_code_counts",
            values[20],
        ),
        reason_codes_json=values[21],
        rows_json=values[22],
        payload_json=_normalize_json_object("payload", values[23]),
        paper_only=values[24],
        report_only=values[25],
        readonly=values[26],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str:
        raise ValueError(
            "table_name must be a lowercase identifier with optional schema prefix",
        )
    parts = value.split(".")
    if not 1 <= len(parts) <= 2:
        raise ValueError(
            "table_name must be a lowercase identifier with optional schema prefix",
        )
    if any(_IDENTIFIER_PATTERN.fullmatch(part) is None for part in parts):
        raise ValueError(
            "table_name must be a lowercase identifier with optional schema prefix",
        )
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_action_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _require_research_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _RESEARCH_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_bounded_limit(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    if value > MAX_STRATEGY_CANDIDATE_RESEARCH_QUEUE_READ_LIMIT:
        raise ValueError(
            f"{field_name} must be less than or equal to "
            f"{MAX_STRATEGY_CANDIDATE_RESEARCH_QUEUE_READ_LIMIT}",
        )


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_TABLE",
    "MAX_STRATEGY_CANDIDATE_RESEARCH_QUEUE_READ_LIMIT",
    "PaperStrategyCandidateResearchQueueReadOptions",
    "load_paper_strategy_candidate_research_queue_reports",
    "load_paper_strategy_candidate_research_queue_reports_with_psycopg",
)

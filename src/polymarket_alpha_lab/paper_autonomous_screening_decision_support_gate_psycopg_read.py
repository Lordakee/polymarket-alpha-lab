"""Read-only psycopg boundary for paper autonomous screening gate reports."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re
from typing import Any, TypeVar

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReport,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
    DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE,
    load_paper_autonomous_screening_decision_support_gate_reports as _load_store_reports,
)
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_config import (
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR,
)


DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TABLE = (
    DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE
)
MAX_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_READ_LIMIT = 500

_GATE_STATUSES = ("pass", "watch", "blocked")
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_T = TypeVar("_T")


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateReadOptions:
    config_version: str | None = None
    gate_status: str | None = None
    queue_risk_config_version: str | None = None
    operator_flow_gate_status: str | None = None
    limit: int = 100
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TABLE

    def __post_init__(self) -> None:
        if self.config_version is not None:
            _require_canonical_string("config_version", self.config_version)
        if self.gate_status is not None:
            _require_gate_status("gate_status", self.gate_status)
        if self.queue_risk_config_version is not None:
            _require_canonical_string(
                "queue_risk_config_version",
                self.queue_risk_config_version,
            )
        if self.operator_flow_gate_status is not None:
            _require_gate_status(
                "operator_flow_gate_status",
                self.operator_flow_gate_status,
            )
        _require_bounded_limit("limit", self.limit)
        object.__setattr__(self, "table_name", _validate_table_name(self.table_name))


def load_paper_autonomous_screening_decision_support_gate_reports(
    connection: Any,
    *,
    options: PaperAutonomousScreeningDecisionSupportGateReadOptions | None = None,
) -> tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...]:
    read_options = (
        options
        if options is not None
        else PaperAutonomousScreeningDecisionSupportGateReadOptions()
    )
    if type(read_options) is not PaperAutonomousScreeningDecisionSupportGateReadOptions:
        raise ValueError(
            "options must be a "
            "PaperAutonomousScreeningDecisionSupportGateReadOptions",
        )
    return _load_store_reports(
        connection,
        config_version=read_options.config_version,
        gate_status=read_options.gate_status,
        queue_risk_config_version=read_options.queue_risk_config_version,
        operator_flow_gate_status=read_options.operator_flow_gate_status,
        limit=read_options.limit,
        table_name=read_options.table_name,
    )


def load_paper_autonomous_screening_decision_support_gate_reports_with_psycopg(
    dsn: str,
    *,
    options: PaperAutonomousScreeningDecisionSupportGateReadOptions | None = None,
) -> tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_paper_autonomous_screening_decision_support_gate_reports(
            connection,
            options=options,
        ),
    )


def _with_owned_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR,
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
            "psycopg is required to use the paper autonomous screening "
            "decision-support gate read adapter; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous screening "
            "decision-support gate read database",
        ) from None


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


def _require_bounded_limit(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    if value > MAX_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_READ_LIMIT:
        raise ValueError(
            f"{field_name} must be less than or equal to "
            f"{MAX_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_READ_LIMIT}",
        )


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TABLE",
    "MAX_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_READ_LIMIT",
    "PaperAutonomousScreeningDecisionSupportGateReadOptions",
    "load_paper_autonomous_screening_decision_support_gate_reports",
    "load_paper_autonomous_screening_decision_support_gate_reports_with_psycopg",
)

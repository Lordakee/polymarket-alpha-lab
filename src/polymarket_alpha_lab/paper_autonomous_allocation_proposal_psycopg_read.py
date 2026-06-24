"""Read-only psycopg boundary for paper autonomous allocation proposals."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Any, TypeVar

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_store import (
    DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_TABLE,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_store import (
    DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_DECISION_SUPPORT_TABLE,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_load import (
    load_paper_autonomous_allocation_proposal_report as _load_paper_autonomous_allocation_proposal_report,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_psycopg_read import (
    DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TABLE,
)


DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_SCREENING_GATE_TABLE = (
    DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TABLE
)
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DECISION_SUPPORT_TABLE = (
    DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_DECISION_SUPPORT_TABLE
)
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_SOURCE_QUEUE_TABLE = (
    DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_TABLE
)
MAX_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_READ_LIMIT = 500

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_POSTGRES_IDENTIFIER_MAX_LENGTH = 63
_T = TypeVar("_T")


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalReadOptions:
    limit: int = 25
    screening_gate_table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_SCREENING_GATE_TABLE
    )
    action_gated_queue_decision_support_table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DECISION_SUPPORT_TABLE
    )
    source_queue_table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_SOURCE_QUEUE_TABLE
    )

    def __post_init__(self) -> None:
        _require_bounded_limit("limit", self.limit)
        object.__setattr__(
            self,
            "screening_gate_table_name",
            _validate_table_name(self.screening_gate_table_name),
        )
        object.__setattr__(
            self,
            "action_gated_queue_decision_support_table_name",
            _validate_table_name(
                self.action_gated_queue_decision_support_table_name,
            ),
        )
        object.__setattr__(
            self,
            "source_queue_table_name",
            _validate_table_name(self.source_queue_table_name),
        )


def load_paper_autonomous_allocation_proposal_report(
    connection: Any,
    *,
    options: PaperAutonomousAllocationProposalReadOptions | None = None,
    generated_at: datetime | None = None,
) -> object:
    read_options = (
        options if options is not None else PaperAutonomousAllocationProposalReadOptions()
    )
    if type(read_options) is not PaperAutonomousAllocationProposalReadOptions:
        raise ValueError("options must be a PaperAutonomousAllocationProposalReadOptions")
    resolved_generated_at = (
        datetime.now(UTC) if generated_at is None else generated_at
    )
    if type(resolved_generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    return _load_paper_autonomous_allocation_proposal_report(
        connection,
        screening_gate_limit=read_options.limit,
        screening_gate_table_name=read_options.screening_gate_table_name,
        action_gated_queue_decision_support_limit=read_options.limit,
        action_gated_queue_decision_support_table_name=(
            read_options.action_gated_queue_decision_support_table_name
        ),
        source_queue_limit=read_options.limit,
        source_queue_table_name=read_options.source_queue_table_name,
        generated_at=resolved_generated_at,
    )


def load_paper_autonomous_allocation_proposal_report_with_psycopg(
    dsn: str,
    *,
    options: PaperAutonomousAllocationProposalReadOptions | None = None,
    generated_at: datetime | None = None,
) -> object:
    return _with_owned_connection(
        dsn,
        lambda connection: load_paper_autonomous_allocation_proposal_report(
            connection,
            options=options,
            generated_at=generated_at,
        ),
    )


def _with_owned_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
    connection = _connect(dsn)
    try:
        return operation(connection)
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _connect(dsn: str) -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "read adapter; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous allocation proposal "
            "read database",
        ) from None


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
    for part in parts:
        if _IDENTIFIER_PATTERN.fullmatch(part) is None:
            raise ValueError(
                "table_name must be a lowercase identifier with optional schema prefix",
            )
        if len(part) > _POSTGRES_IDENTIFIER_MAX_LENGTH:
            raise ValueError(
                "table_name must be a lowercase identifier with optional schema prefix",
            )
    return value


def _require_bounded_limit(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    if value > MAX_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_READ_LIMIT:
        raise ValueError(
            f"{field_name} must be less than or equal to "
            f"{MAX_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_READ_LIMIT}",
        )


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DECISION_SUPPORT_TABLE",
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_SCREENING_GATE_TABLE",
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_SOURCE_QUEUE_TABLE",
    "MAX_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_READ_LIMIT",
    "PaperAutonomousAllocationProposalReadOptions",
    "load_paper_autonomous_allocation_proposal_report",
    "load_paper_autonomous_allocation_proposal_report_with_psycopg",
)

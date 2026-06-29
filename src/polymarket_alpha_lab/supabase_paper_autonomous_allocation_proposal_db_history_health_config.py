"""Environment boundary for DB-history health report persistence."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
import re
from typing import Mapping

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE,
)
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn


PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_"
    "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED"
)
PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_"
    "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN"
)
PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_"
    "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE"
)
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE = (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_POSTGRES_IDENTIFIER_MAX_LENGTH = 63
_TRUE_VALUES = frozenset(("1", "true"))
_FALSE_VALUES = frozenset(("", "0", "false"))
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"


@dataclass(frozen=True)
class SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig:
    enabled: bool
    dsn: str | None
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE
    )

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a bool")
        object.__setattr__(self, "dsn", _normalize_optional_dsn(self.dsn))
        object.__setattr__(self, "table_name", _validate_table_name(self.table_name))
        if self.dsn is not None:
            validate_local_postgres_dsn(
                self.dsn,
                env_var_name=(
                    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR
                ),
            )
        if self.enabled and self.dsn is None:
            raise ValueError(
                f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR} "
                "must be set when DB-history health DB is enabled",
            )

    def __repr__(self) -> str:
        dsn = "<redacted>" if self.dsn is not None else "None"
        return (
            f"{type(self).__name__}("
            f"enabled={self.enabled!r}, "
            f"dsn={dsn}, "
            f"table_name={self.table_name!r}"
            ")"
        )


def from_paper_autonomous_allocation_proposal_db_history_health_db_env(
    env: Mapping[str, str] | None = None,
) -> SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig:
    source = environ if env is None else env
    enabled = _parse_enabled(
        source.get(
            PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
            "",
        ),
    )
    dsn = source.get(PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR)
    table_name = source.get(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR,
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE,
    )
    try:
        return SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig(
            enabled=enabled,
            dsn=dsn,
            table_name=table_name,
        )
    except ValueError as exc:
        if str(exc) == _TABLE_NAME_ERROR:
            raise ValueError(
                f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR} "
                "must be a lowercase identifier with optional schema prefix",
            ) from exc
        raise


def _parse_enabled(value: object) -> bool:
    if type(value) is not str:
        raise ValueError(
            f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR} "
            "must be true or false",
        )
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR} "
        "must be true or false",
    )


def _normalize_optional_dsn(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(
            f"{PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR} "
            "must be a string",
        )
    if not value or value.strip() != value:
        return None
    return value


def _validate_table_name(value: object) -> str:
    if type(value) is not str:
        raise ValueError(_TABLE_NAME_ERROR)
    parts = value.split(".")
    if not 1 <= len(parts) <= 2:
        raise ValueError(_TABLE_NAME_ERROR)
    for part in parts:
        if (
            len(part.encode("utf-8")) > _POSTGRES_IDENTIFIER_MAX_LENGTH
            or _IDENTIFIER_PATTERN.fullmatch(part) is None
        ):
            raise ValueError(_TABLE_NAME_ERROR)
    return value


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE",
    "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR",
    "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR",
    "PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR",
    "SupabasePaperAutonomousAllocationProposalDbHistoryHealthConfig",
    "from_paper_autonomous_allocation_proposal_db_history_health_db_env",
)

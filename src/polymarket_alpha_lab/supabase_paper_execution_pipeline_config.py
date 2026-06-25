"""Environment configuration for paper execution pipeline DB persistence."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
import re
from typing import Mapping

from polymarket_alpha_lab.paper_order_lifecycle_store import (
    DEFAULT_PAPER_ORDER_LIFECYCLE_RECORDS_TABLE,
)


__all__ = (
    "SupabasePaperExecutionPipelineConfig",
    "from_paper_execution_pipeline_db_env",
)


PAPER_EXECUTION_PIPELINE_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_EXECUTION_PIPELINE_DB_ENABLED"
)
PAPER_EXECUTION_PIPELINE_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_EXECUTION_PIPELINE_DB_DSN"
)
PAPER_EXECUTION_PIPELINE_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_EXECUTION_PIPELINE_DB_TABLE"
)
DEFAULT_PAPER_EXECUTION_PIPELINE_DB_TABLE = (
    DEFAULT_PAPER_ORDER_LIFECYCLE_RECORDS_TABLE
)
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")

_TRUE_VALUES = frozenset({"true", "1", "yes"})
_FALSE_VALUES = frozenset({"false", "0", "no", ""})


@dataclass(frozen=True)
class SupabasePaperExecutionPipelineConfig:
    enabled: bool
    dsn: str | None
    table_name: str

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a bool")
        if self.dsn is not None and (type(self.dsn) is not str or not self.dsn):
            raise ValueError("dsn must be a nonblank string or None")
        if (
            type(self.table_name) is not str
            or _IDENTIFIER_PATTERN.fullmatch(self.table_name) is None
        ):
            raise ValueError("table_name must be a simple lowercase identifier")
        if self.enabled and self.dsn is None:
            raise ValueError("dsn is required when enabled is True")

    def __repr__(self) -> str:
        dsn_display = "***" if self.dsn else None
        return (
            f"SupabasePaperExecutionPipelineConfig("
            f"enabled={self.enabled}, "
            f"dsn={dsn_display}, "
            f"table_name={self.table_name!r}"
            ")"
        )


def from_paper_execution_pipeline_db_env(
    env: Mapping[str, str] | None = None,
) -> SupabasePaperExecutionPipelineConfig:
    source = environ if env is None else env
    enabled = _parse_enabled(
        source.get(PAPER_EXECUTION_PIPELINE_DB_ENABLED_ENV_VAR, ""),
    )
    dsn = source.get(PAPER_EXECUTION_PIPELINE_DB_DSN_ENV_VAR)
    table_name = source.get(
        PAPER_EXECUTION_PIPELINE_DB_TABLE_ENV_VAR,
        DEFAULT_PAPER_EXECUTION_PIPELINE_DB_TABLE,
    )
    try:
        return SupabasePaperExecutionPipelineConfig(
            enabled=enabled,
            dsn=dsn,
            table_name=table_name,
        )
    except ValueError as exc:
        if str(exc) == "table_name must be a simple lowercase identifier":
            raise ValueError(
                f"{PAPER_EXECUTION_PIPELINE_DB_TABLE_ENV_VAR} "
                "must be a simple lowercase identifier",
            ) from exc
        raise


def _parse_enabled(value: object) -> bool:
    if type(value) is not str:
        raise ValueError(
            f"{PAPER_EXECUTION_PIPELINE_DB_ENABLED_ENV_VAR} "
            "must be true or false",
        )
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{PAPER_EXECUTION_PIPELINE_DB_ENABLED_ENV_VAR} "
        "must be true or false",
    )

"""Environment boundary for paper trade cost audit DB persistence."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
import re
from typing import Mapping

from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn


PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_TRADE_COST_AUDIT_DB_ENABLED"
)
PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_TRADE_COST_AUDIT_DB_DSN"
)
PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_TRADE_COST_AUDIT_DB_TABLE"
)
DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE = "paper_trade_cost_audit_reports"

_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TRUE_VALUES = frozenset(("1", "true"))
_FALSE_VALUES = frozenset(("", "0", "false"))
_TABLE_NAME_ERROR = (
    "table_name must be a lowercase identifier with optional schema prefix "
    "and each identifier part length <= 63"
)


@dataclass(frozen=True)
class SupabasePaperTradeCostAuditConfig:
    enabled: bool
    dsn: str | None
    table_name: str = DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a bool")
        object.__setattr__(self, "dsn", _normalize_optional_dsn(self.dsn))
        object.__setattr__(
            self,
            "table_name",
            _validate_table_name("table_name", self.table_name),
        )
        if self.dsn is not None:
            validate_local_postgres_dsn(
                self.dsn,
                env_var_name=PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR,
            )
        if self.enabled and self.dsn is None:
            raise ValueError(
                f"{PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR} must be set when DB is enabled",
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


def from_paper_trade_cost_audit_db_env(
    env: Mapping[str, str] | None = None,
) -> SupabasePaperTradeCostAuditConfig:
    source = environ if env is None else env
    enabled = _parse_enabled(source.get(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, ""))
    dsn = source.get(PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR)
    table_name = source.get(
        PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR,
        DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE,
    )
    try:
        return SupabasePaperTradeCostAuditConfig(
            enabled=enabled,
            dsn=dsn,
            table_name=table_name,
        )
    except ValueError as exc:
        message = str(exc)
        if message.startswith("table_name "):
            raise ValueError(
                f"{PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR} {message}",
            ) from exc
        raise


def _parse_enabled(value: object) -> bool:
    if type(value) is not str:
        raise ValueError(
            f"{PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR} must be true or false",
        )
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR} must be true or false",
    )


def _normalize_optional_dsn(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR} must be a string")
    if not value or value.strip() != value:
        return None
    return value


def _validate_table_name(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} {_TABLE_NAME_ERROR}")
    parts = value.split(".")
    if len(parts) not in (1, 2):
        raise ValueError(f"{field_name} {_TABLE_NAME_ERROR}")
    for part in parts:
        if len(part.encode("utf-8")) > 63:
            raise ValueError(f"{field_name} {_TABLE_NAME_ERROR}")
        if _IDENTIFIER_PATTERN.fullmatch(part) is None:
            raise ValueError(f"{field_name} {_TABLE_NAME_ERROR}")
    return value


__all__ = (
    "PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR",
    "PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR",
    "PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR",
    "DEFAULT_PAPER_TRADE_COST_AUDIT_DB_TABLE",
    "SupabasePaperTradeCostAuditConfig",
    "from_paper_trade_cost_audit_db_env",
)

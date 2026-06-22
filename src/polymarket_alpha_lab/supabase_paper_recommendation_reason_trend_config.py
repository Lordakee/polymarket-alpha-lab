"""Environment boundary for paper recommendation reason trend DB persistence."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
import re
from typing import Mapping


PAPER_RECOMMENDATION_REASON_TREND_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_REASON_TREND_DB_ENABLED"
)
PAPER_RECOMMENDATION_REASON_TREND_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_REASON_TREND_DB_DSN"
)
PAPER_RECOMMENDATION_REASON_TREND_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_REASON_TREND_DB_TABLE"
)
DEFAULT_PAPER_RECOMMENDATION_REASON_TREND_DB_TABLE = (
    "paper_recommendation_reason_trend_reports"
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TRUE_VALUES = frozenset(("1", "true"))
_FALSE_VALUES = frozenset(("", "0", "false"))


@dataclass(frozen=True)
class SupabasePaperRecommendationReasonTrendConfig:
    enabled: bool
    dsn: str | None
    table_name: str = DEFAULT_PAPER_RECOMMENDATION_REASON_TREND_DB_TABLE

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a bool")
        object.__setattr__(self, "dsn", _normalize_optional_dsn(self.dsn))
        object.__setattr__(self, "table_name", _validate_table_name(self.table_name))
        if self.enabled and self.dsn is None:
            raise ValueError(
                f"{PAPER_RECOMMENDATION_REASON_TREND_DB_DSN_ENV_VAR} must be set when DB is enabled",
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


def from_paper_recommendation_reason_trend_db_env(
    env: Mapping[str, str] | None = None,
) -> SupabasePaperRecommendationReasonTrendConfig:
    source = environ if env is None else env
    enabled = _parse_enabled(
        source.get(PAPER_RECOMMENDATION_REASON_TREND_DB_ENABLED_ENV_VAR, ""),
    )
    dsn = source.get(PAPER_RECOMMENDATION_REASON_TREND_DB_DSN_ENV_VAR)
    table_name = source.get(
        PAPER_RECOMMENDATION_REASON_TREND_DB_TABLE_ENV_VAR,
        DEFAULT_PAPER_RECOMMENDATION_REASON_TREND_DB_TABLE,
    )
    try:
        return SupabasePaperRecommendationReasonTrendConfig(
            enabled=enabled,
            dsn=dsn,
            table_name=table_name,
        )
    except ValueError as exc:
        if str(exc) == "table_name must be a simple lowercase identifier":
            raise ValueError(
                f"{PAPER_RECOMMENDATION_REASON_TREND_DB_TABLE_ENV_VAR} must be a simple lowercase identifier",
            ) from exc
        raise


def _parse_enabled(value: object) -> bool:
    if type(value) is not str:
        raise ValueError(
            f"{PAPER_RECOMMENDATION_REASON_TREND_DB_ENABLED_ENV_VAR} must be true or false",
        )
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{PAPER_RECOMMENDATION_REASON_TREND_DB_ENABLED_ENV_VAR} must be true or false",
    )


def _normalize_optional_dsn(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(
            f"{PAPER_RECOMMENDATION_REASON_TREND_DB_DSN_ENV_VAR} must be a string",
        )
    if not value or value.strip() != value:
        return None
    return value


def _validate_table_name(value: object) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
    return value


__all__ = (
    "DEFAULT_PAPER_RECOMMENDATION_REASON_TREND_DB_TABLE",
    "PAPER_RECOMMENDATION_REASON_TREND_DB_DSN_ENV_VAR",
    "PAPER_RECOMMENDATION_REASON_TREND_DB_ENABLED_ENV_VAR",
    "PAPER_RECOMMENDATION_REASON_TREND_DB_TABLE_ENV_VAR",
    "SupabasePaperRecommendationReasonTrendConfig",
    "from_paper_recommendation_reason_trend_db_env",
)

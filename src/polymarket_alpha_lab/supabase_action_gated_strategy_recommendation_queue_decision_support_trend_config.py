"""Environment boundary for action-gated queue decision-support trend DB persistence."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
import re
from typing import Mapping


ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED"
)
ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN"
)
ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE"
)
ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE"
)
DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE = (
    "paper_action_gated_queue_decision_support_trend_reports"
)
DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE = (
    "paper_action_gated_queue_decision_support_trend_sources"
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TRUE_VALUES = frozenset(("1", "true"))
_FALSE_VALUES = frozenset(("", "0", "false"))
_TABLE_NAME_ERROR = (
    "must be a lowercase identifier with optional schema prefix and each "
    "identifier part length <= 63"
)


@dataclass(frozen=True)
class SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig:
    enabled: bool
    dsn: str | None
    reports_table_name: str = (
        DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE
    )
    sources_table_name: str = (
        DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE
    )

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a bool")
        object.__setattr__(self, "dsn", _normalize_optional_dsn(self.dsn))
        object.__setattr__(
            self,
            "reports_table_name",
            _validate_table_name("reports_table_name", self.reports_table_name),
        )
        object.__setattr__(
            self,
            "sources_table_name",
            _validate_table_name("sources_table_name", self.sources_table_name),
        )
        if self.enabled and self.dsn is None:
            raise ValueError(
                f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR} "
                "must be set when DB is enabled",
            )

    def __repr__(self) -> str:
        dsn = "<redacted>" if self.dsn is not None else "None"
        return (
            f"{type(self).__name__}("
            f"enabled={self.enabled!r}, "
            f"dsn={dsn}, "
            f"reports_table_name={self.reports_table_name!r}, "
            f"sources_table_name={self.sources_table_name!r}"
            ")"
        )


def from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env(
    env: Mapping[str, str] | None = None,
) -> SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig:
    source = environ if env is None else env
    enabled = _parse_enabled(
        source.get(ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR, ""),
    )
    dsn = source.get(ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR)
    reports_table_name = source.get(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR,
        DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE,
    )
    sources_table_name = source.get(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR,
        DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE,
    )
    try:
        return SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig(
            enabled=enabled,
            dsn=dsn,
            reports_table_name=reports_table_name,
            sources_table_name=sources_table_name,
        )
    except ValueError as exc:
        message = str(exc)
        if message.startswith("reports_table_name "):
            raise ValueError(
                f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR} "
                f"{message}",
            ) from exc
        if message.startswith("sources_table_name "):
            raise ValueError(
                f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR} "
                f"{message}",
            ) from exc
        raise


def _parse_enabled(value: object) -> bool:
    if type(value) is not str:
        raise ValueError(
            f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR} "
            "must be true or false",
        )
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR} "
        "must be true or false",
    )


def _normalize_optional_dsn(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(
            f"{ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR} "
            "must be a string",
        )
    if not value:
        return None
    if value.strip() != value:
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
    "ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR",
    "ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR",
    "ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR",
    "ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR",
    "DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE",
    "DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE",
    "SupabaseActionGatedStrategyRecommendationQueueDecisionSupportTrendConfig",
    "from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env",
)

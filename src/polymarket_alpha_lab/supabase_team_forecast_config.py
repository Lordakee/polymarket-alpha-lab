"""Environment boundary for team forecast DB persistence."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
import re
from typing import Mapping

from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn


TEAM_FORECAST_DB_ENABLED_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_ENABLED"
TEAM_FORECAST_DB_DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN"
TEAM_PROFILE_DB_TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_PROFILE_DB_TABLE"
TEAM_ROUTE_DB_TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_ROUTE_DB_TABLE"
TEAM_FORECAST_DB_TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_TABLE"
TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_EVIDENCE_DB_TABLE"
)
TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_OUTCOME_DB_TABLE"
)

DEFAULT_TEAM_PROFILE_DB_TABLE = "team_profiles"
DEFAULT_TEAM_ROUTE_DB_TABLE = "team_market_routes"
DEFAULT_TEAM_FORECAST_DB_TABLE = "team_forecasts"
DEFAULT_TEAM_FORECAST_EVIDENCE_DB_TABLE = "team_forecast_evidence"
DEFAULT_TEAM_FORECAST_OUTCOME_DB_TABLE = "team_forecast_outcomes"

_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = (
    "must be a lowercase identifier with optional schema prefix "
    "and each identifier part length <= 63"
)
_TRUE_VALUES = frozenset(("1", "true"))
_FALSE_VALUES = frozenset(("", "0", "false"))


@dataclass(frozen=True)
class SupabaseTeamForecastConfig:
    enabled: bool
    dsn: str | None
    team_profile_table_name: str = DEFAULT_TEAM_PROFILE_DB_TABLE
    team_route_table_name: str = DEFAULT_TEAM_ROUTE_DB_TABLE
    team_forecast_table_name: str = DEFAULT_TEAM_FORECAST_DB_TABLE
    team_forecast_evidence_table_name: str = DEFAULT_TEAM_FORECAST_EVIDENCE_DB_TABLE
    team_forecast_outcome_table_name: str = DEFAULT_TEAM_FORECAST_OUTCOME_DB_TABLE

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a bool")
        object.__setattr__(self, "dsn", _normalize_optional_dsn(self.dsn))
        for field_name in _TABLE_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _validate_table_name(field_name, getattr(self, field_name)),
            )
        if self.dsn is not None:
            validate_local_postgres_dsn(
                self.dsn,
                env_var_name=TEAM_FORECAST_DB_DSN_ENV_VAR,
            )
        if self.enabled and self.dsn is None:
            raise ValueError(
                f"{TEAM_FORECAST_DB_DSN_ENV_VAR} must be set when DB is enabled",
            )

    def __repr__(self) -> str:
        dsn = "<redacted>" if self.dsn is not None else "None"
        return (
            f"{type(self).__name__}("
            f"enabled={self.enabled!r}, "
            f"dsn={dsn}, "
            f"team_profile_table_name={self.team_profile_table_name!r}, "
            f"team_route_table_name={self.team_route_table_name!r}, "
            f"team_forecast_table_name={self.team_forecast_table_name!r}, "
            "team_forecast_evidence_table_name="
            f"{self.team_forecast_evidence_table_name!r}, "
            "team_forecast_outcome_table_name="
            f"{self.team_forecast_outcome_table_name!r}"
            ")"
        )


def from_team_forecast_db_env(
    env: Mapping[str, str] | None = None,
) -> SupabaseTeamForecastConfig:
    source = environ if env is None else env
    table_env_vars = (
        (
            "team_profile_table_name",
            TEAM_PROFILE_DB_TABLE_ENV_VAR,
            DEFAULT_TEAM_PROFILE_DB_TABLE,
        ),
        (
            "team_route_table_name",
            TEAM_ROUTE_DB_TABLE_ENV_VAR,
            DEFAULT_TEAM_ROUTE_DB_TABLE,
        ),
        (
            "team_forecast_table_name",
            TEAM_FORECAST_DB_TABLE_ENV_VAR,
            DEFAULT_TEAM_FORECAST_DB_TABLE,
        ),
        (
            "team_forecast_evidence_table_name",
            TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR,
            DEFAULT_TEAM_FORECAST_EVIDENCE_DB_TABLE,
        ),
        (
            "team_forecast_outcome_table_name",
            TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR,
            DEFAULT_TEAM_FORECAST_OUTCOME_DB_TABLE,
        ),
    )
    try:
        return SupabaseTeamForecastConfig(
            enabled=_parse_enabled(source.get(TEAM_FORECAST_DB_ENABLED_ENV_VAR, "")),
            dsn=source.get(TEAM_FORECAST_DB_DSN_ENV_VAR),
            **{
                field_name: source.get(env_var_name, default)
                for field_name, env_var_name, default in table_env_vars
            },
        )
    except ValueError as exc:
        message = str(exc)
        for field_name, env_var_name, _default in table_env_vars:
            if message.startswith(f"{field_name} "):
                raise ValueError(f"{env_var_name} {message.removeprefix(f'{field_name} ')}") from exc
        raise


def _parse_enabled(value: object) -> bool:
    if type(value) is not str:
        raise ValueError(f"{TEAM_FORECAST_DB_ENABLED_ENV_VAR} must be true or false")
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(f"{TEAM_FORECAST_DB_ENABLED_ENV_VAR} must be true or false")


def _normalize_optional_dsn(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{TEAM_FORECAST_DB_DSN_ENV_VAR} must be a string")
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


_TABLE_FIELD_NAMES = (
    "team_profile_table_name",
    "team_route_table_name",
    "team_forecast_table_name",
    "team_forecast_evidence_table_name",
    "team_forecast_outcome_table_name",
)


__all__ = (
    "TEAM_FORECAST_DB_ENABLED_ENV_VAR",
    "TEAM_FORECAST_DB_DSN_ENV_VAR",
    "TEAM_PROFILE_DB_TABLE_ENV_VAR",
    "TEAM_ROUTE_DB_TABLE_ENV_VAR",
    "TEAM_FORECAST_DB_TABLE_ENV_VAR",
    "TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR",
    "TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR",
    "DEFAULT_TEAM_PROFILE_DB_TABLE",
    "DEFAULT_TEAM_ROUTE_DB_TABLE",
    "DEFAULT_TEAM_FORECAST_DB_TABLE",
    "DEFAULT_TEAM_FORECAST_EVIDENCE_DB_TABLE",
    "DEFAULT_TEAM_FORECAST_OUTCOME_DB_TABLE",
    "SupabaseTeamForecastConfig",
    "from_team_forecast_db_env",
)

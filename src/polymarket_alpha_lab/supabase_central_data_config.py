"""Environment-only configuration for the local central evidence store."""

from __future__ import annotations

from dataclasses import dataclass
import os
import shlex
from typing import Mapping
from urllib.parse import parse_qsl, urlsplit

from .supabase_local_dsn import validate_local_postgres_dsn as _validate_local_dsn


CENTRAL_DATA_PERSISTENCE_ENABLED_ENV_VAR = "POLYMARKET_ALPHA_LAB_CENTRAL_DATA_PERSISTENCE_ENABLED"
CENTRAL_DATA_PERSISTENCE_DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_CENTRAL_DATA_PERSISTENCE_DSN"


def _error() -> ValueError:
    return ValueError("central data persistence requires a local postgres DSN with user=postgres")


def _has_explicit_postgres_user(dsn: str) -> bool:
    if dsn.startswith(("postgresql://", "postgres://")):
        try:
            parsed = urlsplit(dsn)
            username = parsed.username
            if username is None or username != "postgres" or "%" in username:
                return False
            if any(key == "user" for key, _value in parse_qsl(parsed.query, keep_blank_values=True)):
                return False
            return True
        except (ValueError, UnicodeError):
            return False
    try:
        tokens = shlex.split(dsn)
    except ValueError:
        return False
    values: dict[str, str] = {}
    for token in tokens:
        if "=" not in token:
            return False
        key, value = token.split("=", 1)
        key = key.lower()
        if key in values or "%" in value:
            return False
        values[key] = value
    return values.get("user") == "postgres"


def validate_local_postgres_dsn(dsn: str) -> None:
    """Validate local-only target and require the trusted ``postgres`` role."""

    if type(dsn) is not str or not dsn or dsn.strip() != dsn:
        raise _error()
    try:
        _validate_local_dsn(dsn, env_var_name=CENTRAL_DATA_PERSISTENCE_DSN_ENV_VAR)
    except ValueError:
        raise _error() from None
    if not _has_explicit_postgres_user(dsn):
        raise _error()


def _normalize_optional(value: object) -> str | None:
    if value is None or value == "":
        return None
    if type(value) is not str or value.strip() != value:
        raise _error()
    return value


@dataclass(frozen=True, repr=False)
class SupabaseCentralDataConfig:
    enabled: bool
    dsn: str | None

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a bool")
        dsn = _normalize_optional(self.dsn)
        if dsn is not None:
            validate_local_postgres_dsn(dsn)
        if self.enabled and dsn is None:
            raise ValueError(f"{CENTRAL_DATA_PERSISTENCE_DSN_ENV_VAR} must be set when enabled")
        object.__setattr__(self, "dsn", dsn)

    def __repr__(self) -> str:
        return f"SupabaseCentralDataConfig(enabled={self.enabled!r}, dsn={'<redacted>' if self.dsn else None})"


def _parse_enabled(value: object) -> bool:
    if type(value) is not str:
        raise ValueError(f"{CENTRAL_DATA_PERSISTENCE_ENABLED_ENV_VAR} must be true or false")
    normalized = value.strip().lower()
    if normalized in {"1", "true"}:
        return True
    if normalized in {"", "0", "false"}:
        return False
    raise ValueError(f"{CENTRAL_DATA_PERSISTENCE_ENABLED_ENV_VAR} must be true or false")


def from_central_data_env(env: Mapping[str, str] | None = None) -> SupabaseCentralDataConfig:
    source = os.environ if env is None else env
    enabled = _parse_enabled(source.get(CENTRAL_DATA_PERSISTENCE_ENABLED_ENV_VAR, ""))
    dsn = source.get(CENTRAL_DATA_PERSISTENCE_DSN_ENV_VAR)
    if dsn not in (None, ""):
        validate_local_postgres_dsn(dsn)
    return SupabaseCentralDataConfig(enabled=enabled, dsn=dsn if enabled else None)


def get_central_dsn() -> str | None:
    config = from_central_data_env()
    return config.dsn if config.enabled else None


__all__ = (
    "CENTRAL_DATA_PERSISTENCE_DSN_ENV_VAR",
    "CENTRAL_DATA_PERSISTENCE_ENABLED_ENV_VAR",
    "SupabaseCentralDataConfig",
    "from_central_data_env",
    "get_central_dsn",
    "validate_local_postgres_dsn",
)

"""Environment boundary for paper autonomous readiness digest DB persistence."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
import re
import shlex
from typing import Mapping
from urllib.parse import parse_qs, urlsplit


PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED"
)
PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN"
)
PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE"
)
DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE = (
    "paper_autonomous_readiness_digest_reports"
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TRUE_VALUES = frozenset(("1", "true"))
_FALSE_VALUES = frozenset(("", "0", "false"))
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
_LOCAL_DSN_ERROR = (
    f"{PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN_ENV_VAR} must point to local "
    "Postgres/Supabase on localhost, 127.0.0.1, ::1, or an explicit Unix "
    "socket path"
)
_LOCAL_HOSTS = frozenset(("localhost", "127.0.0.1", "::1"))


@dataclass(frozen=True)
class SupabasePaperAutonomousReadinessDigestConfig:
    enabled: bool
    dsn: str | None
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a bool")
        object.__setattr__(self, "dsn", _normalize_optional_dsn(self.dsn))
        object.__setattr__(self, "table_name", _validate_table_name(self.table_name))
        if self.dsn is not None:
            _validate_local_postgres_dsn(self.dsn)
        if self.enabled and self.dsn is None:
            raise ValueError(
                f"{PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN_ENV_VAR} "
                "must be set when DB is enabled",
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


def from_paper_autonomous_readiness_digest_db_env(
    env: Mapping[str, str | None] | None = None,
) -> SupabasePaperAutonomousReadinessDigestConfig:
    source = environ if env is None else env
    enabled = _parse_enabled(
        source.get(PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED_ENV_VAR, ""),
    )
    dsn = source.get(PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN_ENV_VAR)
    table_name = source.get(
        PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE_ENV_VAR,
        DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE,
    )
    try:
        return SupabasePaperAutonomousReadinessDigestConfig(
            enabled=enabled,
            dsn=dsn,
            table_name=table_name,
        )
    except ValueError as exc:
        if str(exc) == _TABLE_NAME_ERROR:
            raise ValueError(
                f"{PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE_ENV_VAR} "
                f"{_TABLE_NAME_ERROR}",
            ) from exc
        raise


def _parse_enabled(value: object) -> bool:
    if type(value) is not str:
        raise ValueError(
            f"{PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED_ENV_VAR} "
            "must be true or false",
        )
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED_ENV_VAR} "
        "must be true or false",
    )


def _normalize_optional_dsn(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(
            f"{PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN_ENV_VAR} must be a string",
        )
    if not value or value.strip() != value:
        return None
    return value


def _validate_local_postgres_dsn(value: str) -> None:
    if value.startswith("postgresql://"):
        if _is_local_postgresql_uri(value):
            return
        raise ValueError(_LOCAL_DSN_ERROR)
    if _is_simple_keyword_dsn(value):
        if _is_local_keyword_dsn(value):
            return
        raise ValueError(_LOCAL_DSN_ERROR)
    raise ValueError(_LOCAL_DSN_ERROR)


def _is_local_postgresql_uri(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme != "postgresql":
        return False
    if port is not None and not _is_valid_port(port):
        return False
    query = parse_qs(parsed.query, keep_blank_values=True)
    if "hostaddr" in query or "service" in query:
        return False
    query_hosts = query.get("host", ())
    if len(query_hosts) > 1:
        return False
    hostname = parsed.hostname
    if hostname:
        if query_hosts:
            return False
        return _is_local_host(hostname)
    if not query_hosts:
        return False
    return _is_local_query_host(query_hosts[0])


def _is_simple_keyword_dsn(value: str) -> bool:
    return "=" in value and "://" not in value


def _is_local_keyword_dsn(value: str) -> bool:
    try:
        tokens = shlex.split(value)
    except ValueError:
        return False
    params: dict[str, str] = {}
    for token in tokens:
        if "=" not in token:
            return False
        key, field_value = token.split("=", 1)
        if not key:
            return False
        params[key.lower()] = field_value
    if "hostaddr" in params or "service" in params:
        return False
    host = params.get("host")
    if host is None or host == "":
        return False
    port = params.get("port")
    if port is not None:
        if not port.isdecimal() or not _is_valid_port(int(port)):
            return False
    return _is_local_query_host(host)


def _is_local_query_host(value: str) -> bool:
    if "," in value or not value:
        return False
    if value.startswith("/"):
        return True
    return _is_local_host(value)


def _is_local_host(value: str) -> bool:
    if "," in value:
        return False
    return value.lower() in _LOCAL_HOSTS


def _is_valid_port(value: int) -> bool:
    return 1 <= value <= 65535


def _validate_table_name(value: object) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError(_TABLE_NAME_ERROR)
    return value


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE",
    "PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN_ENV_VAR",
    "PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED_ENV_VAR",
    "PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE_ENV_VAR",
    "SupabasePaperAutonomousReadinessDigestConfig",
    "from_paper_autonomous_readiness_digest_db_env",
)

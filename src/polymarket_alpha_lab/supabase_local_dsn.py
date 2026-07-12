"""Shared validation for local Supabase/Postgres DSNs."""

from __future__ import annotations

import shlex
from urllib.parse import parse_qs, urlsplit


_LOCAL_HOSTS = frozenset(("localhost", "127.0.0.1", "::1"))
_POSTGRES_URI_SCHEMES = frozenset(("postgresql", "postgres"))


def validate_local_postgres_dsn(value: str, *, env_var_name: str) -> None:
    """Require a DSN to target this host's local Postgres/Supabase instance."""

    error_message = (
        f"{env_var_name} must point to local Postgres/Supabase on localhost, "
        "127.0.0.1, ::1, or an explicit Unix socket path"
    )
    if not value:
        raise ValueError(error_message)
    if _is_postgres_uri(value):
        if _is_local_postgres_uri(value):
            return
        raise ValueError(error_message)
    if _is_simple_keyword_dsn(value):
        if _is_local_keyword_dsn(value):
            return
        raise ValueError(error_message)
    raise ValueError(error_message)


def _is_postgres_uri(value: str) -> bool:
    return value.startswith("postgresql://") or value.startswith("postgres://")


def _is_local_postgres_uri(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme not in _POSTGRES_URI_SCHEMES:
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
    return _is_local_socket_or_host(query_hosts[0])


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
        normalized_key = key.lower()
        if normalized_key in params:
            return False
        params[normalized_key] = field_value
    if "hostaddr" in params or "service" in params:
        return False
    host = params.get("host")
    if host is None or host == "":
        return False
    port = params.get("port")
    if port is not None and (not port.isdecimal() or not _is_valid_port(int(port))):
        return False
    return _is_local_socket_or_host(host)


def _is_local_socket_or_host(value: str) -> bool:
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


__all__ = ("validate_local_postgres_dsn",)

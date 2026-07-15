"""Shared validation for local Supabase/Postgres DSNs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import shlex
from urllib.parse import parse_qs, urlsplit


_ALLOWED_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")
_LOCAL_HOSTS = frozenset(_ALLOWED_LOCAL_HOSTS)
_POSTGRES_URI_SCHEMES = frozenset(("postgresql", "postgres"))
_READINESS_COUNT = Decimal("4.000000")
_ZERO_COUNT = Decimal("0.000000")
_READY_REASON_CODE = "local_supabase_postgres_dsn_ready"
_BLOCKER_REASON_CODES = frozenset(
    (
        "hosted_database_dsn_rejected_blocker",
        "jsonl_file_dsn_rejected_blocker",
        "local_supabase_postgres_dsn_invalid_blocker",
        "sqlite_dsn_rejected_blocker",
    )
)
_BLOCKER_REASON_CODE_TUPLES = (
    ("local_supabase_postgres_dsn_invalid_blocker",),
    (
        "hosted_database_dsn_rejected_blocker",
        "local_supabase_postgres_dsn_invalid_blocker",
    ),
    (
        "jsonl_file_dsn_rejected_blocker",
        "local_supabase_postgres_dsn_invalid_blocker",
    ),
    (
        "sqlite_dsn_rejected_blocker",
        "local_supabase_postgres_dsn_invalid_blocker",
    ),
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class LocalPostgresDsnReadiness(_FinalDataclass):
    env_var_name: str
    status: str
    validator_name: str
    durable_persistence_target: str
    allowed_local_hosts: tuple[str, ...]
    checked_dsn: str
    local_supabase_postgres_only: bool
    rejects_jsonl_file_fallback: bool
    rejects_sqlite_fallback: bool
    rejects_hosted_database_fallback: bool
    ready_check_count: Decimal
    blocker_count: Decimal
    required_check_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_name("env_var_name", self.env_var_name)
        if self.status not in {"ready", "blocker"}:
            raise ValueError("status must be ready or blocker")
        if self.validator_name != validate_local_postgres_dsn.__name__:
            raise ValueError("validator_name must be validate_local_postgres_dsn")
        if self.durable_persistence_target != "local_supabase_postgres":
            raise ValueError("durable_persistence_target must be local_supabase_postgres")
        if self.allowed_local_hosts != _ALLOWED_LOCAL_HOSTS:
            raise ValueError("allowed_local_hosts must match local Postgres hosts")
        if self.checked_dsn != "<redacted-dsn>":
            raise ValueError("checked_dsn must be redacted")
        for field_name in (
            "local_supabase_postgres_only",
            "rejects_jsonl_file_fallback",
            "rejects_sqlite_fallback",
            "rejects_hosted_database_fallback",
            "paper_only",
            "report_only",
            "readonly",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")
        for field_name in (
            "ready_check_count",
            "blocker_count",
            "required_check_count",
        ):
            _require_nonnegative_whole_decimal(field_name, getattr(self, field_name))
        if self.required_check_count != _READINESS_COUNT:
            raise ValueError("required_check_count must be 4.000000")
        if self.ready_check_count + self.blocker_count != self.required_check_count:
            raise ValueError("readiness counts must tie")
        if self.status == "ready" and (
            self.ready_check_count != self.required_check_count
            or self.blocker_count != _ZERO_COUNT
        ):
            raise ValueError("ready status must have all required checks ready")
        if self.status == "blocker" and self.blocker_count <= _ZERO_COUNT:
            raise ValueError("blocker_count must be positive for blocker status")
        if type(self.reason_codes) is not tuple:
            raise ValueError("reason_codes must be a tuple")
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        for reason_code in self.reason_codes:
            _require_public_name("reason_code", reason_code)
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason_codes must not contain duplicates")
        if self.status == "ready" and self.reason_codes != (
            _READY_REASON_CODE,
        ):
            raise ValueError("ready status must use the ready reason code")
        if self.status == "blocker" and any(
            reason_code not in _BLOCKER_REASON_CODES for reason_code in self.reason_codes
        ):
            raise ValueError("blocker status must use known blocker reason codes")
        if self.status == "blocker" and (
            self.ready_check_count != Decimal("3.000000")
            or self.blocker_count != Decimal("1.000000")
        ):
            raise ValueError("blocker status counts must be 3.000000 ready and 1.000000 blocker")
        if (
            self.status == "blocker"
            and self.reason_codes not in _BLOCKER_REASON_CODE_TUPLES
        ):
            raise ValueError("blocker status must use an exact ordered blocker reason tuple")


def validate_local_postgres_dsn(value: str, *, env_var_name: str) -> None:
    """Require a DSN to target this host's local Postgres/Supabase instance."""

    _require_public_name("env_var_name", env_var_name)
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


def local_postgres_dsn_readiness(
    value: str,
    *,
    env_var_name: str,
) -> LocalPostgresDsnReadiness:
    """Report whether a DSN satisfies the local-only durable persistence contract."""

    _require_public_name("env_var_name", env_var_name)
    reason_codes = _readiness_reason_codes(value)
    status = "ready" if reason_codes == (_READY_REASON_CODE,) else "blocker"
    blocker_count = _ZERO_COUNT if status == "ready" else Decimal("1.000000")
    return LocalPostgresDsnReadiness(
        env_var_name=env_var_name,
        status=status,
        validator_name=validate_local_postgres_dsn.__name__,
        durable_persistence_target="local_supabase_postgres",
        allowed_local_hosts=_ALLOWED_LOCAL_HOSTS,
        checked_dsn="<redacted-dsn>",
        local_supabase_postgres_only=True,
        rejects_jsonl_file_fallback=True,
        rejects_sqlite_fallback=True,
        rejects_hosted_database_fallback=True,
        ready_check_count=_READINESS_COUNT - blocker_count,
        blocker_count=blocker_count,
        required_check_count=_READINESS_COUNT,
        reason_codes=reason_codes,
    )


def _readiness_reason_codes(value: str) -> tuple[str, ...]:
    if _is_jsonl_file_dsn(value):
        return (
            "jsonl_file_dsn_rejected_blocker",
            "local_supabase_postgres_dsn_invalid_blocker",
        )
    if _is_sqlite_dsn(value):
        return (
            "sqlite_dsn_rejected_blocker",
            "local_supabase_postgres_dsn_invalid_blocker",
        )
    try:
        validate_local_postgres_dsn(value, env_var_name="LOCAL_POSTGRES_DSN_READINESS")
    except ValueError:
        if _is_hosted_database_dsn(value):
            return (
                "hosted_database_dsn_rejected_blocker",
                "local_supabase_postgres_dsn_invalid_blocker",
            )
        return ("local_supabase_postgres_dsn_invalid_blocker",)
    return (_READY_REASON_CODE,)


def _is_jsonl_file_dsn(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith("jsonl://") or lowered.endswith(".jsonl")


def _is_sqlite_dsn(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith("sqlite:") or lowered.startswith("sqlite3:")


def _is_hosted_database_dsn(value: str) -> bool:
    if _is_postgres_uri(value):
        try:
            parsed = urlsplit(value)
        except ValueError:
            return True
        return bool(parsed.hostname and not _is_local_host(parsed.hostname))
    if not _is_simple_keyword_dsn(value):
        return False
    try:
        tokens = shlex.split(value)
    except ValueError:
        return False
    for token in tokens:
        if "=" not in token:
            return False
        key, field_value = token.split("=", 1)
        if key.lower() == "host":
            return not _is_local_socket_or_host(field_value)
    return False


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


def _require_public_name(name: str, value: object) -> None:
    if type(value) is not str or not value or any(char.isspace() for char in value):
        raise ValueError(f"{name} must be a nonempty public string")


def _require_nonnegative_whole_decimal(name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be whole")


__all__ = (
    "LocalPostgresDsnReadiness",
    "local_postgres_dsn_readiness",
    "validate_local_postgres_dsn",
)

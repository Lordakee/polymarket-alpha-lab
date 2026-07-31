"""Pure contracts for centrally acquired public research data.

This module deliberately has no network, environment, database, or filesystem
dependency. Raw payload identity is based on bytes; normalized JSON is a
separate, no-float representation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
import hashlib
import ipaddress
import json
import re
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import urlsplit


MAX_RESPONSE_BYTES = 2 * 1024 * 1024
DEFAULT_PARSER_VERSION = "central-data-v1"
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_MIME_RE = re.compile(r"[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+\Z")
_DNS_LABEL_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


class ParseState(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    UNKNOWN = "unknown"


class FailureStatus(str, Enum):
    NONE = "none"
    NETWORK_ERROR = "network_error"
    RESOLVER_ERROR = "resolver_error"
    CONNECT_ERROR = "connect_error"
    TIMEOUT = "timeout"
    STREAM_ERROR = "stream_error"
    SIZE_LIMIT = "size_limit"
    REDIRECT = "redirect"
    HTTP_ERROR = "http_error"
    UNSUPPORTED_CONTENT_TYPE = "unsupported_content_type"
    UNSUPPORTED_CONTENT_ENCODING = "unsupported_content_encoding"
    INVALID_REQUEST = "invalid_request"
    UNKNOWN = "unknown"


class Freshness(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


class ObservationValueState(str, Enum):
    PRESENT = "present"
    NULL = "null"
    ZERO = "zero"
    UNKNOWN = "unknown"


def _canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _validate_public_host(host: str) -> str:
    host = _canonical_string("host", host).lower()
    if host == "localhost" or host.endswith(".local"):
        raise ValueError("host must be public")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("IP literal hosts are not allowed")
    if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-." for char in host):
        raise ValueError("host must be a canonical DNS name")
    labels = host.split(".")
    if len(host) > 253 or any(_DNS_LABEL_RE.fullmatch(label) is None for label in labels):
        raise ValueError("host must be a canonical DNS name")
    return host


def _validate_url_template(value: str) -> str:
    value = _canonical_string("url_template", value)
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https":
        raise ValueError("url_template must use HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("url_template must not contain credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("url_template must not contain query or fragment")
    try:
        explicit_port = parsed.port
    except ValueError as exc:
        raise ValueError("url_template must not contain an explicit port") from exc
    if explicit_port is not None:
        raise ValueError("url_template must not contain an explicit port")
    if not parsed.hostname:
        raise ValueError("url_template must contain a host")
    _validate_public_host(parsed.hostname)
    if parsed.path and not parsed.path.startswith("/"):
        raise ValueError("url_template path must start with /")
    if any(char.isspace() for char in value) or "{" in value or "}" in value:
        raise ValueError("url_template must be a concrete endpoint without placeholders")
    return value


@dataclass(frozen=True)
class SourceDefinition:
    source_id: str
    source_family: str
    url_template: str
    content_type: str
    freshness_policy_seconds: int
    is_official: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _canonical_string("source_id", self.source_id))
        object.__setattr__(
            self,
            "source_family",
            _canonical_string("source_family", self.source_family),
        )
        object.__setattr__(self, "url_template", _validate_url_template(self.url_template))
        content_type = _canonical_string("content_type", self.content_type).lower()
        if content_type != "*/*" and _MIME_RE.fullmatch(content_type) is None:
            raise ValueError("content_type must be a MIME type or */*")
        object.__setattr__(self, "content_type", content_type)
        if type(self.freshness_policy_seconds) is not int or self.freshness_policy_seconds < 0:
            raise ValueError("freshness_policy_seconds must be a nonnegative int")
        if type(self.is_official) is not bool:
            raise ValueError("is_official must be a bool")
        for field_name in ("paper_only", "report_only", "readonly"):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")

    @property
    def host(self) -> str:
        parsed = urlsplit(self.url_template)
        if parsed.hostname is None:
            raise ValueError("url_template must contain a host")
        return parsed.hostname.lower()


@dataclass(frozen=True)
class CentralDataRequest:
    source_id: str
    url: str
    headers: Mapping[str, str] = field(default_factory=dict)
    method: str = "GET"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _canonical_string("source_id", self.source_id))
        object.__setattr__(self, "url", _validate_url_template(self.url))
        if self.method != "GET":
            raise ValueError("method must be GET")
        normalized_headers: dict[str, str] = {}
        for key, value in dict(self.headers).items():
            key = _canonical_string("request header name", key).lower()
            value = _canonical_string("request header value", value)
            if key in {"authorization", "cookie", "proxy-authorization"}:
                raise ValueError("request credentials are not allowed")
            if any(char in value for char in "\r\n"):
                raise ValueError("request header values must not contain newlines")
            normalized_headers[key] = value
        object.__setattr__(self, "headers", MappingProxyType(normalized_headers))
        for field_name in ("paper_only", "report_only", "readonly"):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")


@dataclass(frozen=True)
class RawResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes
    url: str
    retrieval_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    request_url: str | None = None
    failure_status: FailureStatus = FailureStatus.NONE
    content_type: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.status_code) is not int or not 100 <= self.status_code <= 599:
            raise ValueError("status_code must be an HTTP status integer")
        if type(self.body) is not bytes:
            raise ValueError("body must be bytes")
        if len(self.body) > MAX_RESPONSE_BYTES:
            raise ValueError("body exceeds the maximum response size")
        headers: dict[str, str] = {}
        for key, value in dict(self.headers).items():
            headers[_canonical_string("header name", key).lower()] = _canonical_string(
                "header value",
                value,
            )
        object.__setattr__(self, "headers", MappingProxyType(headers))
        object.__setattr__(self, "url", _validate_url_template(self.url))
        object.__setattr__(self, "retrieval_time", _as_utc("retrieval_time", self.retrieval_time))
        if self.request_url is not None:
            object.__setattr__(self, "request_url", _validate_url_template(self.request_url))
        if type(self.failure_status) is not FailureStatus:
            raise ValueError("failure_status must be a FailureStatus")
        if self.content_type is not None:
            content_type = _canonical_string("content_type", self.content_type).lower()
            if content_type != "*/*" and _MIME_RE.fullmatch(content_type) is None:
                raise ValueError("content_type must be a MIME type or */*")
            object.__setattr__(
                self,
                "content_type",
                content_type,
            )
        for field_name in ("paper_only", "report_only", "readonly"):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")

    @property
    def payload_hash(self) -> str:
        return sha256_hash(self.body)

    @property
    def raw_payload_sha256(self) -> str:
        return self.payload_hash


@dataclass(frozen=True)
class EvidenceReference:
    source_id: str
    retrieval_time: datetime
    observation_time: datetime
    payload_hash: str
    parser_version: str = DEFAULT_PARSER_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _canonical_string("source_id", self.source_id))
        object.__setattr__(self, "retrieval_time", _as_utc("retrieval_time", self.retrieval_time))
        object.__setattr__(self, "observation_time", _as_utc("observation_time", self.observation_time))
        if type(self.payload_hash) is not str or _SHA256_RE.fullmatch(self.payload_hash) is None:
            raise ValueError("payload_hash must be a lowercase SHA-256 hex string")
        object.__setattr__(self, "parser_version", _canonical_string("parser_version", self.parser_version))
        for field_name in ("paper_only", "report_only", "readonly"):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")


def _is_numeric_zero(value: object) -> bool:
    return type(value) is Decimal and value.is_finite() and value == Decimal("0")


def _freeze_value(value: object) -> object:
    if isinstance(value, Mapping):
        frozen = {
            _canonical_string("observation key", key): _freeze_value(item)
            for key, item in value.items()
        }
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _validate_value(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("observation Decimal values must be finite")
        return
    if isinstance(value, datetime):
        return
    if type(value) is int or type(value) is float:
        raise ValueError("observation numeric values must be Decimal")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("observation object keys must be strings")
            _validate_value(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_value(item)
        return
    raise ValueError(f"unsupported observation value type: {type(value).__name__}")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for item in items:
        _canonical_string("reason_code", item)
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must not contain duplicates")
    return items


@dataclass(frozen=True)
class NormalizedObservation:
    source_id: str
    observation_time: datetime
    value: Any
    freshness: Freshness
    parse_state: ParseState
    evidence_reference: EvidenceReference
    value_state: ObservationValueState = ObservationValueState.PRESENT
    failure_status: FailureStatus = FailureStatus.NONE
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _canonical_string("source_id", self.source_id))
        object.__setattr__(self, "observation_time", _as_utc("observation_time", self.observation_time))
        if type(self.freshness) is not Freshness:
            raise ValueError("freshness must be a Freshness")
        if type(self.parse_state) is not ParseState:
            raise ValueError("parse_state must be a ParseState")
        if type(self.value_state) is not ObservationValueState:
            raise ValueError("value_state must be an ObservationValueState")
        if type(self.failure_status) is not FailureStatus:
            raise ValueError("failure_status must be a FailureStatus")
        if type(self.evidence_reference) is not EvidenceReference:
            raise ValueError("evidence_reference must be an EvidenceReference")
        if self.source_id != self.evidence_reference.source_id:
            raise ValueError("source_id must match evidence_reference.source_id")
        if self.observation_time != self.evidence_reference.observation_time:
            raise ValueError("observation_time must match evidence_reference.observation_time")
        _validate_value(self.value)
        object.__setattr__(self, "value", _freeze_value(self.value))
        state = self.value_state
        if state is ObservationValueState.PRESENT:
            if self.value is None:
                state = ObservationValueState.NULL
            elif _is_numeric_zero(self.value):
                state = ObservationValueState.ZERO
        elif state in (ObservationValueState.NULL, ObservationValueState.UNKNOWN):
            if self.value is not None:
                raise ValueError(f"value must be None for {state.value} observations")
        elif state is ObservationValueState.ZERO and not _is_numeric_zero(self.value):
            raise ValueError("zero observations must carry numeric zero")
        object.__setattr__(self, "value_state", state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        for field_name in ("paper_only", "report_only", "readonly"):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "observation_time": self.observation_time,
            "value": self.value,
            "value_state": self.value_state,
            "freshness": self.freshness,
            "parse_state": self.parse_state,
            "failure_status": self.failure_status,
            "evidence_reference": self.evidence_reference,
            "reason_codes": self.reason_codes,
            "paper_only": self.paper_only,
            "report_only": self.report_only,
            "readonly": self.readonly,
        }


def _json_ready(value: object) -> object:
    if value is None or type(value) is bool or type(value) is int or type(value) is str:
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, bytes):
        raise ValueError("raw bytes are not JSON payload values")
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _json_ready(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        keys = tuple(value)
        if any(type(key) is not str for key in keys):
            raise ValueError("JSON object keys must be strings")
        for key in sorted(keys):
            result[key] = _json_ready(value[key])
        return result
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        _json_ready(value),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hash(data: bytes) -> str:
    if type(data) is not bytes:
        raise ValueError("sha256_hash input must be bytes")
    return hashlib.sha256(data).hexdigest()


__all__ = (
    "CentralDataRequest",
    "DEFAULT_PARSER_VERSION",
    "MAX_RESPONSE_BYTES",
    "EvidenceReference",
    "FailureStatus",
    "Freshness",
    "NormalizedObservation",
    "ObservationValueState",
    "ParseState",
    "RawResponse",
    "SourceDefinition",
    "canonical_json_bytes",
    "sha256_hash",
)

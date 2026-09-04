"""Validated, deterministic codecs for central evidence rows.

The public transport contracts live in :mod:`central_data_contracts`.  This
module only binds those contracts to the internal persistence representation;
it does not infer an acquisition event from an ``EvidenceReference``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Mapping

from .central_data_contracts import (
    EvidenceReference,
    FailureStatus,
    Freshness,
    NormalizedObservation,
    ObservationValueState,
    ParseState,
    RawResponse,
    SourceDefinition,
    _as_utc,
    sha256_hash,
)
from .central_data_persistence_policy import (
    CentralDataPersistencePolicy,
    MAX_RESPONSE_BYTES,
)


RAW_RETENTION = timedelta(days=29)
TYPED_ENVELOPE_VERSION = "central_typed_value_v1"
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_FLAGS = {"paper_only": True, "report_only": True, "readonly": True}


def _utc(value: object, field_name: str) -> datetime:
    return _as_utc(field_name, value)


def _require_sha(value: object, field_name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _require_enum_storage_value(
    value: object,
    enum_type: type[Any],
    field_name: str,
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} has an invalid state")
    try:
        enum_type(value)
    except ValueError:
        raise ValueError(f"{field_name} has an invalid state") from None
    return value


def _require_canonical_content_type(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or value != value.lower()
        or ";" in value
    ):
        raise ValueError(f"{field_name} must be a canonical response media type")
    return value


def _safe_repr(_name: str) -> str:
    return "<redacted>"


def _raw_identity_id(
    *,
    source_id: str,
    source_family: str,
    endpoint_url: str,
    official_source: bool,
    request_url: str,
    final_url: str,
    retrieval_time: datetime,
    status_code: int,
    content_type: str,
    safe_headers: Mapping[str, str],
    failure_status: str,
    raw_payload_sha256: str,
) -> str:
    payload = {
        "source_id": source_id,
        "source_family": source_family,
        "endpoint_url": endpoint_url,
        "official_source": official_source,
        "request_url": request_url,
        "final_url": final_url,
        "retrieval_time": _utc(retrieval_time, "retrieval_time").isoformat(),
        "status_code": status_code,
        "content_type": content_type,
        "safe_headers": dict(sorted(safe_headers.items())),
        "failure_status": failure_status,
        "raw_payload_sha256": raw_payload_sha256,
        **_SAFE_FLAGS,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, repr=False)
class RawEventIdentity:
    """Frozen identity and provenance for one accepted acquisition event."""

    raw_event_id: str
    source_id: str
    source_family: str
    endpoint_url: str
    request_url: str
    final_url: str
    official_source: bool
    retrieval_time: datetime
    status_code: int
    content_type: str
    safe_headers: Mapping[str, str] = field(repr=False)
    failure_status: str
    raw_payload_sha256: str

    def __post_init__(self) -> None:
        _require_sha(self.raw_event_id, "raw_event_id")
        _require_sha(self.raw_payload_sha256, "raw_payload_sha256")
        for name in ("source_id", "source_family", "endpoint_url"):
            value = getattr(self, name)
            if type(value) is not str or not value or value.strip() != value:
                raise ValueError(f"{name} must be a canonical nonblank string")
        if self.request_url != self.endpoint_url or self.final_url != self.endpoint_url:
            raise ValueError("raw event URLs must match the registered endpoint")
        if type(self.official_source) is not bool:
            raise ValueError("official_source must be a bool")
        object.__setattr__(self, "retrieval_time", _utc(self.retrieval_time, "retrieval_time"))
        if type(self.status_code) is not int or not 100 <= self.status_code <= 599:
            raise ValueError("status_code must be an HTTP status integer")
        if not isinstance(self.safe_headers, Mapping):
            raise ValueError("safe_headers must be a mapping")
        headers = dict(self.safe_headers)
        content_type = _require_canonical_content_type(self.content_type, "content_type")
        failure_status = _require_enum_storage_value(
            self.failure_status,
            FailureStatus,
            "failure_status",
        )
        rejection = CentralDataPersistencePolicy().evaluate_raw_response(
            {
                "body": b"",
                "content_type": content_type,
                "headers": headers,
                "request_url": self.request_url,
                "final_url": self.final_url,
                "status_code": self.status_code,
            }
        )
        if rejection is not None:
            raise ValueError("raw event identity failed the persistence policy")
        normalized_headers = {
            key.lower(): value
            for key, value in sorted(headers.items(), key=lambda item: item[0])
        }
        object.__setattr__(self, "safe_headers", MappingProxyType(normalized_headers))
        object.__setattr__(self, "content_type", content_type)
        object.__setattr__(self, "failure_status", failure_status)
        expected_id = _raw_identity_id(
            source_id=self.source_id,
            source_family=self.source_family,
            endpoint_url=self.endpoint_url,
            official_source=self.official_source,
            request_url=self.request_url,
            final_url=self.final_url,
            retrieval_time=self.retrieval_time,
            status_code=self.status_code,
            content_type=content_type,
            safe_headers=normalized_headers,
            failure_status=failure_status,
            raw_payload_sha256=self.raw_payload_sha256,
        )
        if self.raw_event_id != expected_id:
            raise ValueError("raw_event_id does not match the immutable event identity")

    def __repr__(self) -> str:
        return "RawEventIdentity(<redacted>)"


@dataclass(frozen=True, repr=False)
class RawEventRow:
    """Validated internal row.  ``raw_body`` and headers never appear in repr."""

    raw_event_id: str
    source_id: str
    source_family: str
    endpoint_url: str
    official_source: bool
    request_url: str
    final_url: str
    retrieval_time: datetime
    status_code: int
    content_type: str
    safe_headers: Mapping[str, str] = field(repr=False)
    failure_status: str = "none"
    raw_body: bytes = field(repr=False, default=b"")
    body_length: int = 0
    raw_payload_sha256: str = ""
    expires_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha(self.raw_event_id, "raw_event_id")
        _require_sha(self.raw_payload_sha256, "raw_payload_sha256")
        for name in (
            "source_id",
            "source_family",
            "endpoint_url",
            "request_url",
            "final_url",
        ):
            value = getattr(self, name)
            if type(value) is not str or not value or value.strip() != value:
                raise ValueError(f"{name} must be a canonical nonblank string")
        if self.request_url != self.final_url or self.request_url != self.endpoint_url:
            raise ValueError("request_url, final_url, and endpoint_url must match")
        if type(self.official_source) is not bool:
            raise ValueError("official_source must be a bool")
        if type(self.raw_body) is not bytes:
            raise ValueError("raw_body must be bytes")
        if len(self.raw_body) > MAX_RESPONSE_BYTES:
            raise ValueError("raw_body exceeds maximum size")
        if not isinstance(self.safe_headers, Mapping):
            raise ValueError("safe_headers must be a mapping")
        headers = dict(self.safe_headers)
        content_type = _require_canonical_content_type(self.content_type, "content_type")
        failure_status = _require_enum_storage_value(
            self.failure_status,
            FailureStatus,
            "failure_status",
        )
        rejection = CentralDataPersistencePolicy().evaluate_raw_response(
            {
                "body": self.raw_body,
                "content_type": content_type,
                "headers": headers,
                "request_url": self.request_url,
                "final_url": self.final_url,
                "status_code": self.status_code,
            }
        )
        if rejection is not None:
            raise ValueError("raw event rejected by persistence policy")
        if self.body_length != len(self.raw_body):
            raise ValueError("body_length must match raw_body")
        if sha256_hash(self.raw_body) != self.raw_payload_sha256:
            raise ValueError("raw_payload_sha256 does not match raw_body")
        object.__setattr__(self, "retrieval_time", _utc(self.retrieval_time, "retrieval_time"))
        expires_at = self.expires_at or (self.retrieval_time + RAW_RETENTION)
        expires_at = _utc(expires_at, "expires_at")
        if expires_at - self.retrieval_time != RAW_RETENTION:
            raise ValueError("expires_at must be exactly 29 days after retrieval_time")
        object.__setattr__(self, "expires_at", expires_at)
        if any(getattr(self, name) is not True for name in ("paper_only", "report_only", "readonly")):
            raise ValueError("central evidence rows must be paper-only, report-only, and readonly")
        normalized_headers = {
            key.lower(): value
            for key, value in sorted(headers.items(), key=lambda item: item[0])
        }
        object.__setattr__(self, "safe_headers", MappingProxyType(normalized_headers))
        object.__setattr__(self, "content_type", content_type)
        object.__setattr__(self, "failure_status", failure_status)
        expected_id = _raw_identity_id(
            source_id=self.source_id,
            source_family=self.source_family,
            endpoint_url=self.endpoint_url,
            official_source=self.official_source,
            request_url=self.request_url,
            final_url=self.final_url,
            retrieval_time=self.retrieval_time,
            status_code=self.status_code,
            content_type=content_type,
            safe_headers=normalized_headers,
            failure_status=failure_status,
            raw_payload_sha256=self.raw_payload_sha256,
        )
        if self.raw_event_id != expected_id:
            raise ValueError("raw_event_id does not match the immutable event identity")

    def __repr__(self) -> str:
        return "RawEventRow(<redacted>)"

    @property
    def identity(self) -> RawEventIdentity:
        return RawEventIdentity(
            raw_event_id=self.raw_event_id,
            source_id=self.source_id,
            source_family=self.source_family,
            endpoint_url=self.endpoint_url,
            request_url=self.request_url,
            final_url=self.final_url,
            official_source=self.official_source,
            retrieval_time=self.retrieval_time,
            status_code=self.status_code,
            content_type=self.content_type,
            safe_headers=self.safe_headers,
            failure_status=self.failure_status,
            raw_payload_sha256=self.raw_payload_sha256,
        )

    @classmethod
    def from_contracts(
        cls,
        source_definition: SourceDefinition,
        raw_response: RawResponse,
        *,
        policy: CentralDataPersistencePolicy | None = None,
    ) -> "RawEventRow":
        if type(source_definition) is not SourceDefinition or type(raw_response) is not RawResponse:
            raise ValueError("source_definition and raw_response must be central contracts")
        (policy or CentralDataPersistencePolicy()).require_raw_response(
            raw_response, source_definition=source_definition
        )
        request_url = raw_response.request_url or raw_response.url
        final_url = raw_response.url
        endpoint = source_definition.url_template
        if request_url != endpoint or final_url != endpoint:
            raise ValueError("raw response endpoint does not match registered source")
        content_type = (raw_response.content_type or source_definition.content_type or "*/*").split(";", 1)[0].lower()
        if source_definition.content_type != "*/*" and content_type != source_definition.content_type:
            raise ValueError("raw response content type does not match source")
        headers = {key.lower(): value for key, value in raw_response.headers.items()}
        failure_status = raw_response.failure_status.value
        payload_hash = raw_response.raw_payload_sha256
        raw_event_id = _raw_identity_id(
            source_id=source_definition.source_id,
            source_family=source_definition.source_family,
            endpoint_url=endpoint,
            official_source=source_definition.is_official,
            request_url=request_url,
            final_url=final_url,
            retrieval_time=raw_response.retrieval_time,
            status_code=raw_response.status_code,
            content_type=content_type,
            safe_headers=headers,
            failure_status=failure_status,
            raw_payload_sha256=payload_hash,
        )
        return cls(
            raw_event_id=raw_event_id,
            source_id=source_definition.source_id,
            source_family=source_definition.source_family,
            endpoint_url=endpoint,
            official_source=source_definition.is_official,
            request_url=request_url,
            final_url=final_url,
            retrieval_time=raw_response.retrieval_time,
            status_code=raw_response.status_code,
            content_type=content_type,
            safe_headers=headers,
            failure_status=failure_status,
            raw_body=raw_response.body,
            body_length=len(raw_response.body),
            raw_payload_sha256=payload_hash,
        )

    def _as_parameters(self) -> tuple[Any, ...]:
        return (
            self.raw_event_id,
            self.source_id,
            self.source_family,
            self.endpoint_url,
            self.official_source,
            self.request_url,
            self.final_url,
            self.retrieval_time,
            self.status_code,
            self.content_type,
            dict(self.safe_headers),
            self.failure_status,
            self.raw_body,
            self.body_length,
            self.raw_payload_sha256,
            self.expires_at,
            True,
            True,
            True,
        )

    # Kept as a narrow compatibility alias for the DB-API store; callers
    # should treat this as an internal binding projection, never a result.
    as_parameters = _as_parameters

    def to_contracts(self) -> RawResponse:
        return RawResponse(
            status_code=self.status_code,
            headers=dict(self.safe_headers),
            body=self.raw_body,
            url=self.final_url,
            retrieval_time=self.retrieval_time,
            request_url=self.request_url,
            failure_status=FailureStatus(self.failure_status),
            content_type=self.content_type,
        )


class TypedEnvelope:
    """Strict recursive ``central_typed_value_v1`` codec."""

    @staticmethod
    def encode(value: Any) -> dict[str, Any]:
        if value is None:
            return {"type": "null"}
        if type(value) is bool:
            return {"type": "bool", "value": value}
        if isinstance(value, Decimal):
            if not value.is_finite():
                raise ValueError("non-finite Decimal rejected")
            return {"type": "decimal", "value": str(value)}
        if type(value) is str:
            return {"type": "string", "value": value}
        if type(value) is int or type(value) is float:
            raise ValueError("integer and float values must be represented by Decimal")
        if isinstance(value, datetime):
            value = _utc(value, "datetime")
            return {"type": "datetime", "value": value.isoformat(timespec="microseconds")}
        if isinstance(value, Mapping):
            keys = tuple(value)
            if any(type(key) is not str or not key or key.strip() != key for key in keys):
                raise ValueError("object keys must be canonical strings")
            items: list[dict[str, Any]] = []
            for key in sorted(keys):
                items.append({"key": key, "value": TypedEnvelope.encode(value[key])})
            return {"type": "object", "items": items}
        if isinstance(value, (list, tuple)):
            return {"type": "sequence", "items": [TypedEnvelope.encode(item) for item in value]}
        raise ValueError("unsupported typed value")

    @staticmethod
    def decode(value: Any) -> Any:
        if type(value) is not dict or set(value) - {"type", "value", "items"}:
            raise ValueError("tampered typed envelope")
        tag = value.get("type")
        if type(tag) is not str:
            raise ValueError("typed envelope tag is required")
        if tag == "null":
            if set(value) != {"type"}:
                raise ValueError("null envelope cannot carry a value")
            return None
        if tag == "bool":
            if set(value) != {"type", "value"} or type(value.get("value")) is not bool:
                raise ValueError("invalid bool envelope")
            return value["value"]
        if tag == "decimal":
            if set(value) != {"type", "value"} or type(value.get("value")) is not str:
                raise ValueError("invalid Decimal envelope")
            try:
                result = Decimal(value["value"])
            except Exception as exc:
                raise ValueError("invalid Decimal envelope") from None
            if not result.is_finite():
                raise ValueError("invalid Decimal envelope")
            return result
        if tag == "string":
            if set(value) != {"type", "value"} or type(value.get("value")) is not str:
                raise ValueError("invalid string envelope")
            return value["value"]
        if tag == "datetime":
            if set(value) != {"type", "value"} or type(value.get("value")) is not str:
                raise ValueError("invalid datetime envelope")
            try:
                return _utc(datetime.fromisoformat(value["value"]), "datetime")
            except Exception:
                raise ValueError("invalid datetime envelope") from None
        if tag in {"object", "sequence"}:
            if set(value) != {"type", "items"} or type(value.get("items")) is not list:
                raise ValueError("invalid container envelope")
            items = value["items"]
            if tag == "sequence":
                return [TypedEnvelope.decode(item) for item in items]
            result: dict[str, Any] = {}
            previous: str | None = None
            for item in items:
                if type(item) is not dict or set(item) != {"key", "value"}:
                    raise ValueError("invalid object envelope item")
                key = item["key"]
                if type(key) is not str or not key or key.strip() != key or key in result:
                    raise ValueError("invalid object envelope key")
                if previous is not None and key <= previous:
                    raise ValueError("object envelope keys must be sorted")
                previous = key
                result[key] = TypedEnvelope.decode(item["value"])
            return result
        raise ValueError("unknown typed envelope tag")


def _normalized_row_id(
    *,
    raw_event_id: str,
    source_id: str,
    source_family: str,
    endpoint_url: str,
    official_source: bool,
    observation_time: datetime,
    retrieval_time: datetime,
    raw_payload_sha256: str,
    parser_version: str,
    parse_state: str,
    freshness_state: str,
    failure_status: str,
    value_state: str,
    reason_codes: tuple[str, ...],
    typed_value: Mapping[str, Any],
) -> str:
    payload = {
        "raw_event_id": raw_event_id,
        "source_id": source_id,
        "source_family": source_family,
        "endpoint_url": endpoint_url,
        "official_source": official_source,
        "observation_time": _utc(observation_time, "observation_time").isoformat(),
        "retrieval_time": _utc(retrieval_time, "retrieval_time").isoformat(),
        "raw_payload_sha256": raw_payload_sha256,
        "parser_version": parser_version,
        "parse_state": parse_state,
        "freshness_state": freshness_state,
        "failure_status": failure_status,
        "value_state": value_state,
        "reason_codes": list(reason_codes),
        "typed_value": dict(typed_value),
        **_SAFE_FLAGS,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, repr=False)
class NormalizedObservationRow:
    normalized_observation_id: str
    raw_event_id: str
    source_id: str
    source_family: str
    endpoint_url: str
    official_source: bool
    observation_time: datetime
    retrieval_time: datetime
    raw_payload_sha256: str
    parser_version: str
    parse_state: str
    freshness_state: str
    failure_status: str
    value_state: str
    reason_codes: tuple[str, ...]
    typed_value: Mapping[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for name in ("normalized_observation_id", "raw_event_id", "raw_payload_sha256"):
            _require_sha(getattr(self, name), name)
        for name in (
            "source_id", "source_family", "endpoint_url", "parser_version",
        ):
            value = getattr(self, name)
            if type(value) is not str or not value or value.strip() != value:
                raise ValueError(f"{name} must be a canonical nonblank string")
        parse_state = _require_enum_storage_value(
            self.parse_state,
            ParseState,
            "parse_state",
        )
        freshness_state = _require_enum_storage_value(
            self.freshness_state,
            Freshness,
            "freshness_state",
        )
        failure_status = _require_enum_storage_value(
            self.failure_status,
            FailureStatus,
            "failure_status",
        )
        value_state = _require_enum_storage_value(
            self.value_state,
            ObservationValueState,
            "value_state",
        )
        for name in ("observation_time", "retrieval_time"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        if type(self.official_source) is not bool:
            raise ValueError("official_source must be a bool")
        if type(self.reason_codes) is not tuple or any(
            type(item) is not str or not item or item.strip() != item
            for item in self.reason_codes
        ):
            raise ValueError("reason_codes must be a tuple of strings")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason_codes must not contain duplicates")
        decoded = TypedEnvelope.decode(dict(self.typed_value))
        encoded = TypedEnvelope.encode(decoded)
        object.__setattr__(self, "typed_value", MappingProxyType(encoded))
        object.__setattr__(self, "parse_state", parse_state)
        object.__setattr__(self, "freshness_state", freshness_state)
        object.__setattr__(self, "failure_status", failure_status)
        object.__setattr__(self, "value_state", value_state)
        if any(getattr(self, name) is not True for name in ("paper_only", "report_only", "readonly")):
            raise ValueError("central evidence rows must be paper-only, report-only, and readonly")
        expected_id = _normalized_row_id(
            raw_event_id=self.raw_event_id,
            source_id=self.source_id,
            source_family=self.source_family,
            endpoint_url=self.endpoint_url,
            official_source=self.official_source,
            observation_time=self.observation_time,
            retrieval_time=self.retrieval_time,
            raw_payload_sha256=self.raw_payload_sha256,
            parser_version=self.parser_version,
            parse_state=parse_state,
            freshness_state=freshness_state,
            failure_status=failure_status,
            value_state=value_state,
            reason_codes=self.reason_codes,
            typed_value=encoded,
        )
        if self.normalized_observation_id != expected_id:
            raise ValueError("normalized_observation_id does not match row identity")

    def __repr__(self) -> str:
        return "NormalizedObservationRow(<redacted>)"

    @classmethod
    def from_contracts(
        cls,
        source_definition: SourceDefinition,
        observation: NormalizedObservation,
        raw_identity: RawEventIdentity,
    ) -> "NormalizedObservationRow":
        if type(source_definition) is not SourceDefinition or type(observation) is not NormalizedObservation:
            raise ValueError("source_definition and observation must be central contracts")
        if type(raw_identity) is not RawEventIdentity:
            raise ValueError("raw_identity is required; EvidenceReference alone is insufficient")
        evidence = observation.evidence_reference
        if evidence.source_id != source_definition.source_id or observation.source_id != source_definition.source_id:
            raise ValueError("observation source does not match source definition")
        if raw_identity.source_id != source_definition.source_id:
            raise ValueError("raw event source does not match source definition")
        if evidence.payload_hash != raw_identity.raw_payload_sha256:
            raise ValueError("observation evidence hash does not match raw event")
        if evidence.retrieval_time != raw_identity.retrieval_time:
            raise ValueError("observation retrieval time does not match raw event")
        if raw_identity.endpoint_url != source_definition.url_template:
            raise ValueError("raw event source snapshot does not match source definition")
        if raw_identity.source_family != source_definition.source_family:
            raise ValueError("raw event source family does not match source definition")
        if raw_identity.official_source != source_definition.is_official:
            raise ValueError("raw event authority does not match source definition")
        typed_value = TypedEnvelope.encode(observation.value)
        base = {
            "raw_event_id": raw_identity.raw_event_id,
            "source_id": observation.source_id,
            "source_family": source_definition.source_family,
            "endpoint_url": source_definition.url_template,
            "official_source": source_definition.is_official,
            "observation_time": _utc(observation.observation_time, "observation_time").isoformat(),
            "retrieval_time": raw_identity.retrieval_time.isoformat(),
            "raw_payload_sha256": raw_identity.raw_payload_sha256,
            "parser_version": evidence.parser_version,
            "parse_state": observation.parse_state.value,
            "freshness_state": observation.freshness.value,
            "failure_status": observation.failure_status.value,
            "value_state": observation.value_state.value,
            "reason_codes": list(observation.reason_codes),
            "typed_value": typed_value,
            **_SAFE_FLAGS,
        }
        normalized_id = _normalized_row_id(
            raw_event_id=raw_identity.raw_event_id,
            source_id=observation.source_id,
            source_family=source_definition.source_family,
            endpoint_url=source_definition.url_template,
            official_source=source_definition.is_official,
            observation_time=observation.observation_time,
            retrieval_time=raw_identity.retrieval_time,
            raw_payload_sha256=raw_identity.raw_payload_sha256,
            parser_version=evidence.parser_version,
            parse_state=observation.parse_state.value,
            freshness_state=observation.freshness.value,
            failure_status=observation.failure_status.value,
            value_state=observation.value_state.value,
            reason_codes=tuple(observation.reason_codes),
            typed_value=typed_value,
        )
        return cls(
            normalized_observation_id=normalized_id,
            raw_event_id=raw_identity.raw_event_id,
            source_id=observation.source_id,
            source_family=source_definition.source_family,
            endpoint_url=source_definition.url_template,
            official_source=source_definition.is_official,
            observation_time=observation.observation_time,
            retrieval_time=raw_identity.retrieval_time,
            raw_payload_sha256=raw_identity.raw_payload_sha256,
            parser_version=evidence.parser_version,
            parse_state=observation.parse_state.value,
            freshness_state=observation.freshness.value,
            failure_status=observation.failure_status.value,
            value_state=observation.value_state.value,
            reason_codes=tuple(observation.reason_codes),
            typed_value=typed_value,
        )

    def as_parameters(self) -> tuple[Any, ...]:
        return (
            self.normalized_observation_id,
            self.raw_event_id,
            self.source_id,
            self.source_family,
            self.endpoint_url,
            self.official_source,
            self.observation_time,
            self.retrieval_time,
            self.raw_payload_sha256,
            self.parser_version,
            self.parse_state,
            self.freshness_state,
            self.failure_status,
            self.value_state,
            list(self.reason_codes),
            dict(self.typed_value),
            True,
            True,
            True,
        )

    def to_contracts(
        self,
        source_definition: SourceDefinition,
        raw_identity: RawEventIdentity,
    ) -> NormalizedObservation:
        if raw_identity.raw_event_id != self.raw_event_id:
            raise ValueError("raw identity does not match normalized row")
        if source_definition.source_id != self.source_id or source_definition.source_family != self.source_family:
            raise ValueError("source definition does not match normalized row")
        if source_definition.url_template != self.endpoint_url or source_definition.is_official != self.official_source:
            raise ValueError("source snapshot does not match normalized row")
        evidence = EvidenceReference(
            source_id=self.source_id,
            retrieval_time=self.retrieval_time,
            observation_time=self.observation_time,
            payload_hash=self.raw_payload_sha256,
            parser_version=self.parser_version,
        )
        return NormalizedObservation(
            source_id=self.source_id,
            observation_time=self.observation_time,
            value=TypedEnvelope.decode(dict(self.typed_value)),
            freshness=Freshness(self.freshness_state),
            parse_state=ParseState(self.parse_state),
            evidence_reference=evidence,
            value_state=ObservationValueState(self.value_state),
            failure_status=FailureStatus(self.failure_status),
            reason_codes=self.reason_codes,
        )


__all__ = (
    "EvidenceReference",
    "FailureStatus",
    "Freshness",
    "MAX_RESPONSE_BYTES",
    "NormalizedObservation",
    "NormalizedObservationRow",
    "ObservationValueState",
    "ParseState",
    "RAW_RETENTION",
    "RawEventIdentity",
    "RawEventRow",
    "RawResponse",
    "SourceDefinition",
    "TYPED_ENVELOPE_VERSION",
    "TypedEnvelope",
)

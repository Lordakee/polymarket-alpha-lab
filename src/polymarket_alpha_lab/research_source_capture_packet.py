from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from ipaddress import ip_address
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit


FetchText = Callable[[str], str]

COUNT_QUANTUM = Decimal("0.000000")
ZERO = Decimal("0.000000")
DEFAULT_MAX_SOURCE_AGE_SECONDS = Decimal("86400.000000")
DECIMAL_CONTEXT = Context(prec=28)

FRESHNESS_STATUSES = ("fresh", "stale", "unavailable")
EXTRACTION_STATUSES = ("extracted", "empty", "unavailable")
HOST_CLASSIFICATIONS = ("government", "education", "organization", "public_web")
REASON_CODE_SEQUENCE = (
    "source_text_extracted",
    "source_empty",
    "fetch_exception",
    "source_fresh",
    "source_stale",
    "source_unavailable",
    "safe_public_payload",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
BOUNDARY_FLAG_FIELDS = (
    "no_durable_writes",
    "no_raw_text_retention",
    "no_live_trading",
    "no_wallet_access",
    "no_exchange_mutation",
)
RAW_TEXT_FIELD_NAMES = {
    "body",
    "captured_text",
    "content",
    "extracted_text",
    "full_text",
    "html",
    "raw_text",
    "source_text",
    "text",
}
INTERNAL_SOURCE_LOCATOR_FIELD_NAMES = {"url", "url_host"}
INTERNAL_ONLY_PAYLOAD_FIELD_NAMES = INTERNAL_SOURCE_LOCATOR_FIELD_NAMES | set(
    BOUNDARY_FLAG_FIELDS,
)
PUBLIC_SOURCE_LOCATOR_FIELD_NAMES = {
    "href",
    "link",
    "source_href",
    "source_link",
    "source_uri",
    "source_url",
    "uri",
    "url",
    "url_host",
}
PUBLIC_MARKET_CONTEXT_FIELD_NAMES = {
    "market_id",
    "market_question",
    "market_slug",
    "question",
    "slug",
}
PUBLIC_SOURCE_REFERENCE_FIELD_NAMES = {
    "source_ref",
    "source_reference",
    "source_references",
    "source_refs",
}
PUBLIC_STORAGE_FIELD_NAMES = {
    "connection_string",
    "database_url",
    "db_url",
    "dsn",
    "schema_name",
    "table",
    "table_name",
    "tablename",
}
SAFE_HARD_FLAG_NAMES = set(PHASE_FLAG_FIELDS)
UNSAFE_PUBLIC_FRAGMENTS = (
    "account",
    "api_key",
    "apikey",
    "auth",
    "cancel",
    "credential",
    "database_url",
    "db_url",
    "dsn",
    "exchange_mutation",
    "livetrading",
    "live_trading",
    "market_id",
    "market_question",
    "market_slug",
    "mnemonic",
    "mutation",
    "order",
    "password",
    "private_key",
    "privatekey",
    "replace",
    "secret",
    "seed_phrase",
    "signing",
    "signature",
    "source_ref",
    "source_reference",
    "token",
    "trade",
    "trading",
    "wallet",
)


@dataclass(frozen=True)
class ResearchSourceCapturePacket:
    url: str
    url_host: str
    host_classification: str
    fetched_at: datetime
    content_length: Decimal
    source_age_seconds: Decimal
    freshness_status: str
    extraction_status: str
    reason_codes: tuple[str, ...]
    content_sha256: str | None = None
    extractor_name: str = "injected_fetch_text"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    no_durable_writes: bool = True
    no_raw_text_retention: bool = True
    no_live_trading: bool = True
    no_wallet_access: bool = True
    no_exchange_mutation: bool = True

    def __post_init__(self) -> None:
        normalized_url, host = _normalize_url("url", self.url)
        object.__setattr__(self, "url", normalized_url)
        object.__setattr__(self, "url_host", _normalize_host("url_host", self.url_host))
        if self.url_host != host:
            raise ValueError("url_host must match url")
        object.__setattr__(
            self,
            "host_classification",
            _normalize_member(
                "host_classification",
                self.host_classification,
                HOST_CLASSIFICATIONS,
            ),
        )
        if self.host_classification != _classify_host(host):
            raise ValueError("host_classification must match url_host")
        object.__setattr__(self, "fetched_at", _as_utc("fetched_at", self.fetched_at))
        object.__setattr__(
            self,
            "content_length",
            _normalize_count("content_length", self.content_length),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "freshness_status",
            _normalize_member("freshness_status", self.freshness_status, FRESHNESS_STATUSES),
        )
        object.__setattr__(
            self,
            "extraction_status",
            _normalize_member(
                "extraction_status",
                self.extraction_status,
                EXTRACTION_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "content_sha256",
            _normalize_content_sha256("content_sha256", self.content_sha256),
        )
        object.__setattr__(
            self,
            "extractor_name",
            _require_public_string("extractor_name", self.extractor_name),
        )
        _require_hard_flags("packet", self)
        _require_boundary_flags("packet", self)
        _validate_status_consistency(self)
        _reject_unsafe_public_payload("packet", self)
        assert_research_source_capture_pure_boundary(self)


def capture_research_source_packet(
    url: str,
    *,
    fetch_text: FetchText,
    fetched_at: datetime,
    as_of: datetime | None = None,
    max_source_age_seconds: Decimal = DEFAULT_MAX_SOURCE_AGE_SECONDS,
) -> ResearchSourceCapturePacket:
    normalized_url, host = _normalize_url("url", url)
    if not callable(fetch_text):
        raise ValueError("fetch_text must be an injected callable")
    fetched_at_utc = _as_utc("fetched_at", fetched_at)
    as_of_utc = fetched_at_utc if as_of is None else _as_utc("as_of", as_of)
    source_age_seconds = _age_seconds("source_age_seconds", fetched_at_utc, as_of_utc)
    freshness_threshold = _normalize_nonnegative_decimal(
        "max_source_age_seconds",
        max_source_age_seconds,
    )

    try:
        fetched_text = fetch_text(normalized_url)
    except Exception:
        extraction_status = "unavailable"
        freshness_status = "unavailable"
        content_length = ZERO
        content_sha256 = None
        reason_codes = (
            "fetch_exception",
            "source_unavailable",
            "safe_public_payload",
        )
    else:
        if type(fetched_text) is not str:
            raise ValueError("fetch_text must return str")
        normalized_text = fetched_text.strip()
        content_length = _normalize_count("content_length", Decimal(len(normalized_text)))
        if normalized_text:
            extraction_status = "extracted"
            freshness_status = (
                "fresh" if source_age_seconds <= freshness_threshold else "stale"
            )
            content_sha256 = sha256(normalized_text.encode("utf-8")).hexdigest()
            reason_codes = (
                "source_text_extracted",
                "source_fresh" if freshness_status == "fresh" else "source_stale",
                "safe_public_payload",
            )
        else:
            extraction_status = "empty"
            freshness_status = "unavailable"
            content_sha256 = None
            reason_codes = (
                "source_empty",
                "source_unavailable",
                "safe_public_payload",
            )

    return ResearchSourceCapturePacket(
        url=normalized_url,
        url_host=host,
        host_classification=_classify_host(host),
        fetched_at=fetched_at_utc,
        content_length=content_length,
        source_age_seconds=source_age_seconds,
        freshness_status=freshness_status,
        extraction_status=extraction_status,
        reason_codes=reason_codes,
        content_sha256=content_sha256,
    )


def research_source_capture_packet_payload(
    packet: ResearchSourceCapturePacket | dict[str, Any],
) -> dict[str, Any]:
    if type(packet) is ResearchSourceCapturePacket:
        _require_hard_flags("packet", packet)
        _require_boundary_flags("packet", packet)
        _reject_unsafe_public_payload("packet", packet)
        payload = _payload_value(packet)
    elif type(packet) is dict:
        payload = packet
    else:
        raise ValueError("packet must be a ResearchSourceCapturePacket")

    _require_hard_flags("payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("packet payload must be a JSON object")
    _require_hard_flags("payload", ready)
    _reject_unsafe_public_payload("payload", ready)
    assert_research_source_capture_pure_boundary(ready)
    return ready


def assert_research_source_capture_pure_boundary(
    packet: ResearchSourceCapturePacket | dict[str, Any],
) -> None:
    if type(packet) is ResearchSourceCapturePacket:
        _require_hard_flags("packet", packet)
        _require_boundary_flags("packet", packet)
        _reject_raw_text_surface("packet", packet)
        _reject_unsafe_public_payload("packet", packet)
        payload = _payload_value(packet)
    elif type(packet) is dict:
        payload = packet
    else:
        raise ValueError("packet must be a ResearchSourceCapturePacket")
    if type(payload) is not dict:
        raise ValueError("packet payload must be a JSON object")
    _require_hard_flags("payload", payload)
    _reject_raw_text_surface("payload", payload)
    _reject_unsafe_public_payload("payload", payload)


def scrapling_style_text_fetcher(extractor: Callable[[str], Any]) -> FetchText:
    if not callable(extractor):
        raise ValueError("extractor must be callable")

    def fetch_text(url: str) -> str:
        normalized_url, _host = _normalize_url("url", url)
        result = extractor(normalized_url)
        return _extract_text_from_scrapling_style_result(result)

    return fetch_text


def _extract_text_from_scrapling_style_result(value: object) -> str:
    if type(value) is str:
        return value
    for method_name in ("get_text", "text_content"):
        method = getattr(value, method_name, None)
        if callable(method):
            extracted = method()
            if type(extracted) is str:
                return extracted
    for attribute_name in ("text", "html"):
        extracted = getattr(value, attribute_name, None)
        if type(extracted) is str:
            return extracted
    raise ValueError("extractor must return text or a Scrapling-style text object")


def _normalize_url(field_name: str, value: object) -> tuple[str, str]:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} has unsafe public value")
    parts = urlsplit(value)
    if parts.scheme != "https":
        raise ValueError(f"{field_name} must use https")
    if not parts.netloc or parts.hostname is None:
        raise ValueError(f"{field_name} must include a host")
    if parts.username is not None or parts.password is not None:
        raise ValueError(f"{field_name} must not include credentials")
    if parts.query or parts.fragment:
        raise ValueError(f"{field_name} has unsafe public value")
    try:
        if parts.port is not None:
            raise ValueError(f"{field_name} must not include an explicit port")
    except ValueError as exc:
        if "Port could not be cast" in str(exc):
            raise ValueError(f"{field_name} has unsafe public value") from exc
        raise

    host = _normalize_host(f"{field_name}.host", parts.hostname)
    if _host_is_ip_address(host):
        raise ValueError(f"{field_name} host must be a public DNS name")
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError(f"{field_name} host has unsafe public value")

    path = parts.path or "/"
    if not path.startswith("/"):
        raise ValueError(f"{field_name} path has unsafe public value")
    normalized = urlunsplit(("https", host, path, "", ""))
    return normalized, host


def _normalize_host(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} has unsafe public value")
    host = value.lower().rstrip(".")
    if not host or ".." in host:
        raise ValueError(f"{field_name} has unsafe public value")
    labels = host.split(".")
    for label in labels:
        if not label or label.startswith("-") or label.endswith("-"):
            raise ValueError(f"{field_name} has unsafe public value")
        if not all(character.isalnum() or character == "-" for character in label):
            raise ValueError(f"{field_name} has unsafe public value")
    return host


def _host_is_ip_address(host: str) -> bool:
    try:
        ip_address(host)
    except ValueError:
        return False
    return True


def _classify_host(host: str) -> str:
    if host.endswith(".gov"):
        return "government"
    if host.endswith(".edu"):
        return "education"
    if host.endswith(".org"):
        return "organization"
    return "public_web"


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(field_name: str, fetched_at: datetime, as_of: datetime) -> Decimal:
    delta = as_of - fetched_at
    total_microseconds = (
        (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds
    )
    if total_microseconds < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        value = Decimal(total_microseconds) / Decimal(1_000_000)
    return value.quantize(COUNT_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(COUNT_QUANTUM)


def _normalize_member(
    field_name: str,
    value: object,
    supported_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_text(field_name, value)
    if value not in supported_values:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: object,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if _has_unsafe_public_fragment(reason_code):
            raise ValueError(f"{field_name} has unsafe public value")
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} must contain supported reason codes")
        if reason_code in seen:
            raise ValueError(f"{field_name} must contain unique reason codes")
        seen.add(reason_code)
    expected = tuple(code for code in REASON_CODE_SEQUENCE if code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _normalize_content_sha256(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if not all(character in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} has unsafe public value")
    _reject_unsafe_text(field_name, value)
    return value


def _validate_status_consistency(packet: ResearchSourceCapturePacket) -> None:
    if packet.extraction_status == "extracted":
        if packet.content_length <= ZERO:
            raise ValueError("content_length must be positive when extracted")
        if packet.content_sha256 is None:
            raise ValueError("content_sha256 must be present when extracted")
        if "source_text_extracted" not in packet.reason_codes:
            raise ValueError("reason_codes must include source_text_extracted")
        if packet.freshness_status == "fresh" and "source_fresh" not in packet.reason_codes:
            raise ValueError("reason_codes must include source_fresh")
        if packet.freshness_status == "stale" and "source_stale" not in packet.reason_codes:
            raise ValueError("reason_codes must include source_stale")
        if packet.freshness_status == "unavailable":
            raise ValueError("freshness_status cannot be unavailable when extracted")
    elif packet.extraction_status == "empty":
        if packet.content_length != ZERO:
            raise ValueError("content_length must be zero when empty")
        if packet.content_sha256 is not None:
            raise ValueError("content_sha256 must be absent when empty")
        if packet.freshness_status != "unavailable":
            raise ValueError("freshness_status must be unavailable when empty")
        if set(packet.reason_codes) != {"source_empty", "source_unavailable", "safe_public_payload"}:
            raise ValueError("reason_codes must explain empty source")
    elif packet.extraction_status == "unavailable":
        if packet.content_length != ZERO:
            raise ValueError("content_length must be zero when unavailable")
        if packet.content_sha256 is not None:
            raise ValueError("content_sha256 must be absent when unavailable")
        if packet.freshness_status != "unavailable":
            raise ValueError("freshness_status must be unavailable")
        if set(packet.reason_codes) != {
            "fetch_exception",
            "source_unavailable",
            "safe_public_payload",
        }:
            raise ValueError("reason_codes must explain unavailable source")
    if "safe_public_payload" not in packet.reason_codes:
        raise ValueError("reason_codes must include safe_public_payload")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_boundary_flags(label: str, value: object) -> None:
    for field_name in BOUNDARY_FLAG_FIELDS:
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _field_value(value: object, field_name: str) -> object:
    if type(value) is dict:
        return value.get(field_name)
    return getattr(value, field_name, None)


def _payload_value(value: object) -> Any:
    if type(value) is ResearchSourceCapturePacket:
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
            if field.name not in INTERNAL_ONLY_PAYLOAD_FIELD_NAMES
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload decimal value must be exact")
        if not value.is_finite():
            raise ValueError("payload decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {
            str(key): _payload_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float) or type(value) is int:
        raise ValueError("payload numeric value must use Decimal-derived strings")
    raise ValueError("payload value is not supported")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is ResearchSourceCapturePacket:
        return _json_ready(_payload_value(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) is not ResearchSourceCapturePacket:
            raise ValueError(f"{current_path} must be a supported public dataclass")
        _validate_internal_source_locator(value)
        for field in fields(value):
            if field.name in INTERNAL_ONLY_PAYLOAD_FIELD_NAMES:
                continue
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_public_key(field.name, field_path)
            _reject_unsafe_public_payload(label, getattr(value, field.name), field_path)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_public_key(key, item_path)
            if key in PHASE_FLAG_FIELDS + BOUNDARY_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is str:
        _reject_unsafe_text(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _reject_public_key(key: str, path: str) -> None:
    normalized = _normalize_public_name(key)
    if normalized in RAW_TEXT_FIELD_NAMES:
        raise ValueError(f"{path} raw text is not allowed in public payload")
    if normalized in SAFE_HARD_FLAG_NAMES:
        return
    if (
        normalized in PUBLIC_SOURCE_LOCATOR_FIELD_NAMES
        or normalized.endswith("_url")
        or normalized.endswith("_uri")
        or normalized.endswith("_href")
        or normalized.endswith("_link")
    ):
        raise ValueError(f"{path} raw URL/source locator is not allowed")
    if normalized in PUBLIC_MARKET_CONTEXT_FIELD_NAMES or normalized.startswith("market_"):
        raise ValueError(f"{path} market surface is not allowed")
    if normalized in PUBLIC_SOURCE_REFERENCE_FIELD_NAMES:
        raise ValueError(f"{path} source reference is not allowed")
    if normalized in PUBLIC_STORAGE_FIELD_NAMES:
        raise ValueError(f"{path} dsn/table surface is not allowed")
    if _has_unsafe_public_fragment(key):
        raise ValueError(f"{path} has unsafe public field")


def _reject_raw_text_surface(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_raw_text_surface(label, getattr(value, field.name), field_path)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _normalize_public_name(key) in RAW_TEXT_FIELD_NAMES:
                raise ValueError(f"{item_path} raw text is not allowed in public payload")
            _reject_raw_text_surface(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_raw_text_surface(label, item, f"{current_path}[{index}]")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    if value.strip() != value:
        raise ValueError(f"{field_name} has unsafe public value")
    if _looks_like_raw_url(value):
        raise ValueError(f"{field_name} raw URL is not allowed")
    if "?" in value:
        raise ValueError(f"{field_name} has unsafe public value")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _validate_internal_source_locator(packet: ResearchSourceCapturePacket) -> None:
    normalized_url, host = _normalize_url("url", packet.url)
    if packet.url != normalized_url:
        raise ValueError("url must be normalized")
    if _normalize_host("url_host", packet.url_host) != host:
        raise ValueError("url_host must match url")


def _looks_like_raw_url(value: str) -> bool:
    normalized = value.lower()
    return "://" in normalized or normalized.startswith("www.")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = _normalize_public_name(value)
    compact = "".join(character for character in normalized if character.isalnum())
    return any(
        fragment in normalized or fragment in compact
        for fragment in UNSAFE_PUBLIC_FRAGMENTS
    )


def _normalize_public_name(value: str) -> str:
    return value.lower().replace("-", "_").replace(" ", "_")


__all__ = (
    "FetchText",
    "ResearchSourceCapturePacket",
    "assert_research_source_capture_pure_boundary",
    "capture_research_source_packet",
    "research_source_capture_packet_payload",
    "scrapling_style_text_fetcher",
)

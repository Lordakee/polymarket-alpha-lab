"""Fail-closed, GET-only transport for registered public sources."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import ipaddress
import re
import socket
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    OpenerDirector,
    ProxyHandler,
    Request,
    build_opener,
)

from .central_data_contracts import (
    CentralDataRequest,
    MAX_RESPONSE_BYTES,
    FailureStatus,
    RawResponse,
    SourceDefinition,
)


_DNS_LABEL_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
_ASCII_DECIMAL_RE = re.compile(r"[0-9]+\Z")
_READ_CHUNK_SIZE = 64 * 1024


class CentralTransportError(ValueError):
    """A redacted, typed transport failure."""

    def __init__(self, status: FailureStatus, message: str) -> None:
        self.status = status
        super().__init__(message)


class Resolver(Protocol):
    def resolve(self, host: str) -> tuple[str, ...]:
        """Return all candidate addresses for a host."""


class HTTPResponse(Protocol):
    code: int
    headers: Mapping[str, str]
    connected_ip: str | None

    def read(self, size: int = -1) -> bytes: ...

    def close(self) -> None: ...


class HTTPClient(Protocol):
    def open(self, request: Request, *, timeout: float) -> HTTPResponse: ...


class SourceCatalog(Protocol):
    def get(self, source_id: str) -> SourceDefinition:
        """Return the immutable registered source definition."""


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Mapping[str, str], newurl: str) -> None:
        return None


def _normalize_ip(value: str) -> str:
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise CentralTransportError(FailureStatus.RESOLVER_ERROR, "resolver returned an invalid address") from exc
    mapped = getattr(address, "ipv4_mapped", None)
    if mapped is not None:
        address = mapped
    return str(address)


def _is_public_address(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return bool(
        address.is_global
        and not address.is_loopback
        and not address.is_private
        and not address.is_link_local
        and not address.is_multicast
        and not address.is_reserved
        and not address.is_unspecified
    )


def _default_resolve(host: str) -> tuple[str, ...]:
    try:
        results = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise CentralTransportError(FailureStatus.RESOLVER_ERROR, "public host resolution failed") from exc
    addresses = tuple(dict.fromkeys(_normalize_ip(result[4][0]) for result in results))
    if not addresses or not all(_is_public_address(address) for address in addresses):
        raise CentralTransportError(FailureStatus.RESOLVER_ERROR, "host resolved to a non-public address")
    return addresses


def _peer_ip(response: Any) -> str | None:
    connected_ip = getattr(response, "connected_ip", None)
    if connected_ip is not None:
        return _normalize_ip(connected_ip)
    candidates = [response]
    for attribute in ("fp", "raw", "_sock"):
        candidates.extend(getattr(item, attribute, None) for item in tuple(candidates) if item is not None)
    for candidate in candidates:
        sock = getattr(candidate, "_sock", candidate)
        getpeername = getattr(sock, "getpeername", None)
        if getpeername is None:
            continue
        try:
            peer = getpeername()[0]
        except (OSError, TypeError, IndexError):
            continue
        return _normalize_ip(peer)
    return None


class _UrlLibResponse:
    def __init__(self, response: Any) -> None:
        self._response = response
        self.code = int(getattr(response, "status", getattr(response, "code", 0)))
        self.headers = dict(getattr(response, "headers", {}))
        self.connected_ip = _peer_ip(response)

    def read(self, size: int = -1) -> bytes:
        return self._response.read(size)

    def close(self) -> None:
        self._response.close()


class _UrlLibHTTPClient:
    """Private opener used only after SafeGETTransport validation."""

    def __init__(self, *, allowed_hosts: frozenset[str]) -> None:
        self.allowed_hosts = allowed_hosts
        self._opener: OpenerDirector = build_opener(
            ProxyHandler({}),
            _NoRedirectHandler(),
        )

    def open(self, request: Request, *, timeout: float) -> HTTPResponse:
        if request.get_method() != "GET" or request.data is not None:
            raise CentralTransportError(FailureStatus.INVALID_REQUEST, "only GET requests without a body are allowed")
        for key, _value in request.header_items():
            if key.lower() in {"authorization", "cookie", "proxy-authorization"}:
                raise CentralTransportError(FailureStatus.INVALID_REQUEST, "credentials are not allowed")
        _validate_request_url(request.full_url, self.allowed_hosts)
        try:
            return _UrlLibResponse(self._opener.open(request, timeout=timeout))
        except HTTPError as exc:
            return _UrlLibResponse(exc)
        except URLError:
            raise


def _validate_request_url(url: str, allowed_hosts: frozenset[str]) -> tuple[str, str]:
    if type(url) is not str or not url or any(char.isspace() for char in url) or "{" in url or "}" in url:
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "invalid public source URL")
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "only HTTPS sources are allowed")
    if parsed.username is not None or parsed.password is not None:
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "source URL credentials are not allowed")
    if parsed.query or parsed.fragment:
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "source URL query and fragment are not allowed")
    try:
        port = parsed.port
    except ValueError as exc:
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "explicit source ports are not allowed") from exc
    if port is not None:
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "explicit source ports are not allowed")
    host = parsed.hostname
    if host is None:
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "source URL host is required")
    host = host.lower()
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "IP literal source hosts are not allowed")
    if host == "localhost" or host.endswith(".local"):
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "local source hosts are not allowed")
    if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-." for char in host):
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "source host is not canonical")
    labels = host.split(".")
    if len(host) > 253 or any(_DNS_LABEL_RE.fullmatch(label) is None for label in labels):
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "source host is not canonical")
    if host not in allowed_hosts:
        raise CentralTransportError(FailureStatus.INVALID_REQUEST, "source host is not allowlisted")
    return url, host


def _validate_allowed_host(host: str) -> str:
    if type(host) is not str or not host or host.strip() != host:
        raise ValueError("allowed_hosts must contain canonical hosts")
    host = host.lower()
    if host == "localhost" or host.endswith(".local"):
        raise ValueError("allowed_hosts must contain public hosts")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("allowed_hosts must not contain IP literals")
    if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-." for char in host):
        raise ValueError("allowed_hosts must contain DNS names")
    labels = host.split(".")
    if len(host) > 253 or any(_DNS_LABEL_RE.fullmatch(label) is None for label in labels):
        raise ValueError("allowed_hosts must contain DNS names")
    return host


def _safe_headers(headers: Mapping[str, Any]) -> dict[str, str]:
    allowed = {
        "cache-control",
        "content-encoding",
        "content-length",
        "content-type",
        "date",
        "etag",
        "last-modified",
        "retry-after",
    }
    result: dict[str, str] = {}
    for key, value in headers.items():
        if type(key) is not str:
            raise CentralTransportError(FailureStatus.STREAM_ERROR, "response headers are invalid")
        lowered = key.lower()
        if lowered in allowed:
            result[lowered] = str(value)
    return result


def _media_type(value: str | None) -> str | None:
    if value is None:
        return None
    return value.split(";", 1)[0].strip().lower() or None


def _read_bounded_body(
    response: HTTPResponse,
    *,
    max_bytes: int,
    declared_length: int | None,
) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(min(_READ_CHUNK_SIZE, max_bytes - total + 1))
        if type(chunk) is not bytes:
            raise CentralTransportError(FailureStatus.STREAM_ERROR, "response stream did not return bytes")
        if not chunk:
            break
        if len(chunk) > max_bytes - total:
            raise CentralTransportError(FailureStatus.SIZE_LIMIT, "response exceeds the size limit")
        chunks.append(chunk)
        total += len(chunk)
    if declared_length is not None and total != declared_length:
        raise CentralTransportError(FailureStatus.STREAM_ERROR, "response content length does not match body")
    return b"".join(chunks)


class SafeGETTransport:
    """GET-only transport for pre-registered, public HTTPS hosts."""

    def __init__(
        self,
        *,
        allowed_hosts: Iterable[str],
        source_catalog: SourceCatalog,
        resolver: Resolver | None = None,
        http: HTTPClient | None = None,
        timeout_seconds: float = 15.0,
        max_response_bytes: int = MAX_RESPONSE_BYTES,
        max_attempts: int = 1,
        user_agent: str = "polymarket-alpha-lab/1.0",
    ) -> None:
        hosts = tuple(_validate_allowed_host(host) for host in allowed_hosts)
        if not hosts:
            raise ValueError("allowed_hosts must contain canonical hosts")
        if len(set(hosts)) != len(hosts):
            raise ValueError("allowed_hosts must not contain duplicates")
        if type(timeout_seconds) is not float or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if type(max_response_bytes) is not int or not 1 <= max_response_bytes <= MAX_RESPONSE_BYTES:
            raise ValueError("max_response_bytes must be between 1 and 2 MiB")
        if type(max_attempts) is not int or not 1 <= max_attempts <= 3:
            raise ValueError("max_attempts must be between 1 and 3")
        if source_catalog is None or not hasattr(source_catalog, "get"):
            raise ValueError("source_catalog is required")
        if type(user_agent) is not str or not user_agent or any(char in user_agent for char in "\r\n"):
            raise ValueError("user_agent must be a nonblank header-safe string")
        self.allowed_hosts = frozenset(hosts)
        self.source_catalog = source_catalog
        self.resolver = resolver or _DefaultResolver()
        self._requires_peer_ip = http is None
        self.http = http or _UrlLibHTTPClient(allowed_hosts=self.allowed_hosts)
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.max_attempts = max_attempts
        self.user_agent = user_agent

    def fetch(
        self,
        source_def: SourceDefinition,
        request: CentralDataRequest | None = None,
    ) -> RawResponse:
        if type(source_def) is not SourceDefinition:
            raise ValueError("source_def must be a SourceDefinition")
        try:
            registered = self.source_catalog.get(source_def.source_id)
        except (KeyError, ValueError) as exc:
            raise CentralTransportError(FailureStatus.INVALID_REQUEST, "source definition is not registered") from exc
        if type(registered) is not SourceDefinition or registered != source_def:
            raise CentralTransportError(FailureStatus.INVALID_REQUEST, "source definition is not registered")
        request_url, host = _validate_request_url(source_def.url_template, self.allowed_hosts)
        if request is None:
            request = CentralDataRequest(
                source_id=source_def.source_id,
                url=request_url,
                headers={"accept": source_def.content_type, "user-agent": self.user_agent},
            )
        elif type(request) is not CentralDataRequest:
            raise ValueError("request must be a CentralDataRequest")
        elif request.source_id != source_def.source_id or request.url != request_url:
            raise CentralTransportError(FailureStatus.INVALID_REQUEST, "request does not match source definition")
        raw_addresses = self.resolver.resolve(host)
        if isinstance(raw_addresses, str):
            raw_addresses = (raw_addresses,)
        resolved = tuple(dict.fromkeys(_normalize_ip(address) for address in raw_addresses))
        if not resolved or not all(_is_public_address(address) for address in resolved):
            raise CentralTransportError(FailureStatus.RESOLVER_ERROR, "host resolved to a non-public address")
        request = Request(
            request.url,
            method=request.method,
            headers=dict(request.headers),
        )
        last_error: CentralTransportError | None = None
        for _attempt in range(self.max_attempts):
            response: HTTPResponse | None = None
            try:
                response = self.http.open(request, timeout=self.timeout_seconds)
                peer = _peer_ip(response)
                if self._requires_peer_ip and peer is None:
                    raise CentralTransportError(FailureStatus.CONNECT_ERROR, "connected peer was unavailable")
                if peer is not None and peer not in resolved:
                    raise CentralTransportError(FailureStatus.CONNECT_ERROR, "connected peer was not resolved")
                headers = _safe_headers(response.headers)
                status_code = int(response.code)
                content_type = _media_type(headers.get("content-type"))
                if status_code in range(300, 400):
                    return RawResponse(
                        status_code=status_code,
                        headers=headers,
                        body=b"",
                        url=request_url,
                        request_url=request_url,
                        retrieval_time=datetime.now(UTC),
                        failure_status=FailureStatus.REDIRECT,
                        content_type=content_type,
                    )
                if not 200 <= status_code < 300:
                    return RawResponse(
                        status_code=status_code,
                        headers=headers,
                        body=b"",
                        url=request_url,
                        request_url=request_url,
                        retrieval_time=datetime.now(UTC),
                        failure_status=FailureStatus.HTTP_ERROR,
                        content_type=content_type,
                    )
                expected = source_def.content_type
                if expected != "*/*" and content_type != expected:
                    return RawResponse(
                        status_code=status_code,
                        headers=headers,
                        body=b"",
                        url=request_url,
                        request_url=request_url,
                        retrieval_time=datetime.now(UTC),
                        failure_status=FailureStatus.UNSUPPORTED_CONTENT_TYPE,
                        content_type=content_type,
                    )
                content_encoding = headers.get("content-encoding", "identity").strip().lower()
                if content_encoding not in ("", "identity"):
                    return RawResponse(
                        status_code=status_code,
                        headers=headers,
                        body=b"",
                        url=request_url,
                        request_url=request_url,
                        retrieval_time=datetime.now(UTC),
                        failure_status=FailureStatus.UNSUPPORTED_CONTENT_ENCODING,
                        content_type=content_type,
                    )
                content_length = headers.get("content-length")
                if content_length is not None:
                    if _ASCII_DECIMAL_RE.fullmatch(content_length.strip()) is None:
                        raise CentralTransportError(
                            FailureStatus.STREAM_ERROR,
                            "response content length is invalid",
                        )
                    declared_length = int(content_length)
                    if declared_length < 0:
                        raise CentralTransportError(
                            FailureStatus.STREAM_ERROR,
                            "response content length is invalid",
                        )
                    if declared_length > self.max_response_bytes:
                        raise CentralTransportError(FailureStatus.SIZE_LIMIT, "response exceeds the size limit")
                else:
                    declared_length = None
                body = _read_bounded_body(
                    response,
                    max_bytes=self.max_response_bytes,
                    declared_length=declared_length,
                )
                return RawResponse(
                    status_code=status_code,
                    headers=headers,
                    body=body,
                    url=request_url,
                    request_url=request_url,
                    retrieval_time=datetime.now(UTC),
                    failure_status=FailureStatus.NONE,
                    content_type=content_type,
                )
            except CentralTransportError as exc:
                last_error = exc
                if exc.status in (FailureStatus.SIZE_LIMIT, FailureStatus.CONNECT_ERROR, FailureStatus.INVALID_REQUEST):
                    raise
            except TimeoutError as exc:
                last_error = CentralTransportError(FailureStatus.TIMEOUT, "public source request timed out")
                if _attempt + 1 == self.max_attempts:
                    raise last_error from exc
            except HTTPError as exc:
                try:
                    peer = _peer_ip(exc)
                    if self._requires_peer_ip and peer is None:
                        raise CentralTransportError(FailureStatus.CONNECT_ERROR, "connected peer was unavailable")
                    if peer is not None and peer not in resolved:
                        raise CentralTransportError(FailureStatus.CONNECT_ERROR, "connected peer was not resolved")
                    headers = _safe_headers(exc.headers or {})
                    status = int(exc.code)
                    failure = FailureStatus.REDIRECT if 300 <= status < 400 else FailureStatus.HTTP_ERROR
                    return RawResponse(
                        status_code=status,
                        headers=headers,
                        body=b"",
                        url=request_url,
                        request_url=request_url,
                        retrieval_time=datetime.now(UTC),
                        failure_status=failure,
                        content_type=_media_type(headers.get("content-type")),
                    )
                finally:
                    exc.close()
            except URLError as exc:
                if isinstance(getattr(exc, "reason", None), TimeoutError):
                    last_error = CentralTransportError(FailureStatus.TIMEOUT, "public source request timed out")
                    if _attempt + 1 == self.max_attempts:
                        raise last_error from exc
                    continue
                last_error = CentralTransportError(FailureStatus.NETWORK_ERROR, "public source request failed")
                if _attempt + 1 == self.max_attempts:
                    raise last_error from exc
            except OSError as exc:
                last_error = CentralTransportError(FailureStatus.NETWORK_ERROR, "public source request failed")
                if _attempt + 1 == self.max_attempts:
                    raise last_error from exc
            finally:
                if response is not None:
                    response.close()
        raise last_error or CentralTransportError(FailureStatus.UNKNOWN, "public source request failed")


class _DefaultResolver:
    def resolve(self, host: str) -> tuple[str, ...]:
        return _default_resolve(host)


__all__ = (
    "CentralTransportError",
    "HTTPClient",
    "HTTPResponse",
    "Resolver",
    "SourceCatalog",
    "SafeGETTransport",
)

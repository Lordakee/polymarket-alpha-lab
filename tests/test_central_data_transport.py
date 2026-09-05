from collections.abc import Mapping
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from polymarket_alpha_lab.central_data_contracts import (
    MAX_RESPONSE_BYTES,
    CentralDataRequest,
    FailureStatus,
    RequestParamSpec,
    SourceDefinition,
)
from polymarket_alpha_lab.central_data_registry import SourceRegistry
from polymarket_alpha_lab.central_data_transport import (
    CentralTransportError,
    SafeGETTransport,
    _UrlLibHTTPClient,
    _UrlLibResponse,
)


class FakeResolver:
    def __init__(self, addresses: tuple[str, ...] = ("93.184.216.34",)) -> None:
        self.addresses = addresses
        self.hosts: list[str] = []

    def resolve(self, host: str) -> tuple[str, ...]:
        self.hosts.append(host)
        return self.addresses


class FakeResponse:
    def __init__(
        self,
        *,
        code: int = 200,
        headers: Mapping[str, str] | None = None,
        body: bytes = b'{"ok":true}',
        connected_ip: str | None = "93.184.216.34",
    ) -> None:
        self.code = code
        self.headers = dict(headers) if headers is not None else {"content-type": "application/json"}
        self.body = body
        self.position = 0
        self.connected_ip = connected_ip
        self.read_sizes: list[int] = []
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        if size < 0:
            size = len(self.body) - self.position
        chunk = self.body[self.position : self.position + size]
        self.position += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True


class FakeHTTP:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.requests = []
        self.timeouts: list[float] = []

    def open(self, request, *, timeout: float):
        self.requests.append(request)
        self.timeouts.append(timeout)
        return self.response


class PeerSocket:
    def __init__(self, address: str) -> None:
        self.address = address
        self.closed = False

    def getpeername(self):
        return (self.address, 443)

    def close(self) -> None:
        self.closed = True


class PeerFile:
    def __init__(self, address: str) -> None:
        self.raw = type("Raw", (), {"_sock": PeerSocket(address)})()

    def close(self) -> None:
        self.raw._sock.close()


def source() -> SourceDefinition:
    return SourceDefinition(
        source_id="test_source",
        source_family="test_family",
        url_template="https://example.com/data",
        content_type="application/json",
        freshness_policy_seconds=300,
    )


def catalog() -> SourceRegistry:
    registry = SourceRegistry()
    registry.register(source())
    return registry


def transport(
    *,
    resolver: FakeResolver | None = None,
    response: FakeResponse | None = None,
) -> tuple[SafeGETTransport, FakeHTTP, FakeResolver]:
    chosen_resolver = resolver or FakeResolver()
    chosen_http = FakeHTTP(response or FakeResponse())
    source_catalog = catalog()
    return (
        SafeGETTransport(
            allowed_hosts=("example.com",),
            source_catalog=source_catalog,
            resolver=chosen_resolver,
            http=chosen_http,
            timeout_seconds=3.0,
        ),
        chosen_http,
        chosen_resolver,
    )


def test_safe_get_transport_is_get_only_and_preserves_raw_bytes():
    response = FakeResponse()
    safe, http, resolver = transport(response=response)
    result = safe.fetch(source())
    request = http.requests[0]
    assert request.get_method() == "GET"
    assert request.data is None
    assert "authorization" not in {key.lower() for key in request.headers}
    assert "cookie" not in {key.lower() for key in request.headers}
    assert result.body == b'{"ok":true}'
    assert result.failure_status is FailureStatus.NONE
    assert resolver.hosts == ["example.com"]
    assert response.closed is True
    assert response.read_sizes[-1] == 65536


def test_transport_rejects_non_allowlisted_host():
    safe, _http, _resolver = transport()
    item = SourceDefinition(
        source_id="other",
        source_family="other",
        url_template="https://other.example/data",
        content_type="application/json",
        freshness_policy_seconds=300,
    )
    with pytest.raises(CentralTransportError, match="registered"):
        safe.fetch(item)


@pytest.mark.parametrize(
    "addresses",
    (
        ("127.0.0.1",),
        ("10.0.0.4",),
        ("169.254.169.254",),
        ("fc00::1",),
        ("::ffff:10.0.0.4",),
    ),
)
def test_transport_rejects_private_and_mapped_private_resolution(addresses):
    safe, _http, _resolver = transport(resolver=FakeResolver(addresses))
    with pytest.raises(CentralTransportError) as error:
        safe.fetch(source())
    assert error.value.status is FailureStatus.RESOLVER_ERROR


def test_transport_rejects_peer_address_mismatch():
    safe, _http, _resolver = transport(response=FakeResponse(connected_ip="93.184.216.35"))
    with pytest.raises(CentralTransportError) as error:
        safe.fetch(source())
    assert error.value.status is FailureStatus.CONNECT_ERROR


def test_transport_returns_redirect_without_following():
    safe, _http, _resolver = transport(
        response=FakeResponse(
            code=302,
            headers={"location": "https://internal.example/data"},
            body=b"redirect body must not be retained",
        ),
    )
    result = safe.fetch(source())
    assert result.failure_status is FailureStatus.REDIRECT
    assert result.body == b""


def test_transport_rejects_oversized_stream_instead_of_truncating():
    safe, _http, _resolver = transport(response=FakeResponse(body=b"x" * (MAX_RESPONSE_BYTES + 1)))
    with pytest.raises(CentralTransportError) as error:
        safe.fetch(source())
    assert error.value.status is FailureStatus.SIZE_LIMIT


def test_transport_rejects_content_type_mismatch():
    safe, _http, _resolver = transport(
        response=FakeResponse(headers={"content-type": "text/html"}),
    )
    result = safe.fetch(source())
    assert result.failure_status is FailureStatus.UNSUPPORTED_CONTENT_TYPE
    assert result.body == b""


def test_transport_rejects_missing_content_type_and_non_identity_encoding():
    safe, _http, _resolver = transport(response=FakeResponse(headers={"content-encoding": "gzip"}))
    result = safe.fetch(source())
    assert result.failure_status is FailureStatus.UNSUPPORTED_CONTENT_TYPE

    safe, _http, _resolver = transport(
        response=FakeResponse(headers={"content-type": "application/json", "content-encoding": "gzip"}),
    )
    result = safe.fetch(source())
    assert result.failure_status is FailureStatus.UNSUPPORTED_CONTENT_ENCODING


@pytest.mark.parametrize("content_length", ("+1", "abc", "-1"))
def test_transport_rejects_invalid_content_length(content_length: str):
    safe, _http, _resolver = transport(
        response=FakeResponse(
            headers={"content-type": "application/json", "content-length": content_length},
            body=b"x",
        ),
    )
    with pytest.raises(CentralTransportError) as error:
        safe.fetch(source())
    assert error.value.status is FailureStatus.STREAM_ERROR


def test_transport_rejects_content_length_mismatch_and_accepts_exact_length():
    safe, _http, _resolver = transport(
        response=FakeResponse(
            headers={"content-type": "application/json", "content-length": "2"},
            body=b"x",
        ),
    )
    with pytest.raises(CentralTransportError) as error:
        safe.fetch(source())
    assert error.value.status is FailureStatus.STREAM_ERROR

    safe, _http, _resolver = transport(
        response=FakeResponse(
            headers={"content-type": "application/json", "content-length": "2"},
            body=b"xy",
        ),
    )
    assert safe.fetch(source()).body == b"xy"


def test_transport_binds_source_definition_to_registry():
    safe, _http, _resolver = transport()
    different_path = SourceDefinition(
        source_id="test_source",
        source_family="test_family",
        url_template="https://example.com/other",
        content_type="application/json",
        freshness_policy_seconds=300,
    )
    with pytest.raises(CentralTransportError, match="registered"):
        safe.fetch(different_path)


def test_http_error_peer_mismatch_fails_closed_and_closes_response():
    peer_file = PeerFile("127.0.0.1")
    error = HTTPError(
        "https://example.com/data",
        302,
        "redirect",
        {"location": "https://other.example"},
        peer_file,
    )

    class RaisingHTTP:
        def open(self, request, *, timeout: float):
            raise error

    safe = SafeGETTransport(
        allowed_hosts=("example.com",),
        source_catalog=catalog(),
        resolver=FakeResolver(),
        http=RaisingHTTP(),
    )
    with pytest.raises(CentralTransportError) as raised:
        safe.fetch(source())
    assert raised.value.status is FailureStatus.CONNECT_ERROR
    assert peer_file.raw._sock.closed is True


def test_private_urllib_client_rejects_unsafe_requests_before_network():
    client = _UrlLibHTTPClient(allowed_hosts=frozenset(("example.com",)))
    with pytest.raises(CentralTransportError):
        client.open(Request("http://example.com/data", method="GET"), timeout=1.0)
    with pytest.raises(CentralTransportError):
        client.open(Request("https://example.com/data", method="POST", data=b"x"), timeout=1.0)


def test_urllib_response_extracts_nested_peer_without_network():
    peer_file = PeerFile("93.184.216.34")
    response = type(
        "Response",
        (),
        {
            "status": 200,
            "headers": {"content-type": "application/json"},
            "fp": peer_file,
            "read": lambda self, size=-1: b"{}",
            "close": lambda self: peer_file.close(),
        },
    )()
    wrapped = _UrlLibResponse(response)
    assert wrapped.connected_ip == "93.184.216.34"


def test_transport_rejects_unsafe_allowlist_entries():
    with pytest.raises(ValueError):
        SafeGETTransport(allowed_hosts=("127.0.0.1",), source_catalog=SourceRegistry())
    with pytest.raises(ValueError):
        SafeGETTransport(allowed_hosts=("service.local",), source_catalog=SourceRegistry())


def test_default_client_fails_closed_when_peer_address_is_unavailable():
    safe = SafeGETTransport(
        allowed_hosts=("example.com",),
        source_catalog=catalog(),
        resolver=FakeResolver(),
        http=FakeHTTP(FakeResponse(connected_ip=None)),
    )
    safe._requires_peer_ip = True
    with pytest.raises(CentralTransportError) as error:
        safe.fetch(source())
    assert error.value.status is FailureStatus.CONNECT_ERROR


class TimeoutHTTP:
    def __init__(self) -> None:
        self.calls = 0

    def open(self, request, *, timeout: float):
        self.calls += 1
        raise TimeoutError


def test_transport_timeout_attempt_budget_is_bounded():
    http = TimeoutHTTP()
    safe = SafeGETTransport(
        allowed_hosts=("example.com",),
        source_catalog=catalog(),
        resolver=FakeResolver(),
        http=http,
        max_attempts=2,
    )
    with pytest.raises(CentralTransportError) as error:
        safe.fetch(source())
    assert error.value.status is FailureStatus.TIMEOUT
    assert http.calls == 2


def param_source():
    return SourceDefinition(
        source_id="param_source",
        source_family="param_family",
        url_template="https://example.com/data",
        content_type="application/json",
        freshness_policy_seconds=60,
        query_params=(
            RequestParamSpec("limit", "int_range", min_value=1, max_value=100),
            RequestParamSpec("condition_id", "pattern", pattern=r"[0-9a-fA-Fx]{1,66}"),
        ),
    )


def param_catalog() -> SourceRegistry:
    registry = SourceRegistry()
    registry.register(param_source())
    return registry


def param_transport(response: FakeResponse | None = None) -> tuple[SafeGETTransport, FakeHTTP]:
    http = FakeHTTP(response or FakeResponse())
    return (
        SafeGETTransport(
            allowed_hosts=("example.com",),
            source_catalog=param_catalog(),
            resolver=FakeResolver(),
            http=http,
        ),
        http,
    )


def test_transport_fetches_template_with_canonical_query():
    safe, http = param_transport(FakeResponse(body=b'{"page":[]}'))
    request = CentralDataRequest(
        source_id="param_source",
        url="https://example.com/data",
        headers={"accept": "application/json", "user-agent": "t"},
        query={"condition_id": "0xAbC", "limit": "25"},
    )
    response = safe.fetch(param_source(), request)
    assert response.failure_status is FailureStatus.NONE
    sent = http.requests[0]
    assert sent.full_url == "https://example.com/data?condition_id=0xAbC&limit=25"
    assert response.url == "https://example.com/data"
    assert response.request_url == "https://example.com/data"


def test_transport_rejects_unregistered_and_offspec_query_parameters():
    safe, _http = param_transport(FakeResponse(body=b"[]"))
    with pytest.raises(CentralTransportError) as error:
        safe.fetch(
            param_source(),
            CentralDataRequest(
                source_id="param_source",
                url="https://example.com/data",
                query={"pair": "XBTUSD"},
            ),
        )
    assert error.value.status is FailureStatus.INVALID_REQUEST
    with pytest.raises(CentralTransportError) as error:
        safe.fetch(
            param_source(),
            CentralDataRequest(
                source_id="param_source",
                url="https://example.com/data",
                query={"limit": "101"},
            ),
        )
    assert error.value.status is FailureStatus.INVALID_REQUEST


def test_transport_rejects_query_on_sources_without_specs():
    plain = SafeGETTransport(
        allowed_hosts=("example.com",),
        source_catalog=catalog(),
        resolver=FakeResolver(),
        http=FakeHTTP(FakeResponse(body=b"[]")),
    )
    with pytest.raises(CentralTransportError) as error:
        plain.fetch(
            source(),
            CentralDataRequest(
                source_id="test_source",
                url="https://example.com/data",
                query={"limit": "5"},
            ),
        )
    assert error.value.status is FailureStatus.INVALID_REQUEST


def test_private_client_rejects_non_canonical_query_urls():
    client = _UrlLibHTTPClient(allowed_hosts=frozenset({"example.com"}))
    smuggled = Request("https://example.com/data?limit=%31%30%30", method="GET")
    with pytest.raises(CentralTransportError) as error:
        client.open(smuggled, timeout=1.0)
    assert error.value.status is FailureStatus.INVALID_REQUEST
    plus_encoded = Request("https://example.com/data?condition=a+b", method="GET")
    with pytest.raises(CentralTransportError) as error:
        client.open(plus_encoded, timeout=1.0)
    assert error.value.status is FailureStatus.INVALID_REQUEST

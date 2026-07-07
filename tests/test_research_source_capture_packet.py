import ast
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_source_capture_packet import (
    ResearchSourceCapturePacket,
    assert_research_source_capture_pure_boundary,
    capture_research_source_packet,
    research_source_capture_packet_payload,
    scrapling_style_text_fetcher,
)
import polymarket_alpha_lab.research_source_capture_packet as source_capture_module


COUNT_QUANTUM = Decimal("0.000000")


def d_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def fixed_at() -> datetime:
    return datetime(2026, 7, 7, 12, 0, 0, tzinfo=UTC)


def test_successful_capture_normalizes_safe_evidence_metadata() -> None:
    text = "Federal Reserve release text for downstream evidence review."
    calls: list[str] = []

    def fetch_text(url: str) -> str:
        calls.append(url)
        return text

    fetched_at = fixed_at()
    packet = capture_research_source_packet(
        "https://www.federalreserve.gov/releases/h15/",
        fetch_text=fetch_text,
        fetched_at=fetched_at,
        as_of=fetched_at + timedelta(minutes=5),
        max_source_age_seconds=Decimal("3600.000000"),
    )

    assert type(packet) is ResearchSourceCapturePacket
    assert is_dataclass(packet)
    assert packet.url == "https://www.federalreserve.gov/releases/h15/"
    assert packet.url_host == "www.federalreserve.gov"
    assert packet.host_classification == "government"
    assert packet.fetched_at == fetched_at
    assert packet.content_length == d_count(len(text))
    assert packet.source_age_seconds == Decimal("300.000000")
    assert packet.freshness_status == "fresh"
    assert packet.extraction_status == "extracted"
    assert packet.reason_codes == (
        "source_text_extracted",
        "source_fresh",
        "safe_public_payload",
    )
    assert packet.paper_only is True
    assert packet.report_only is True
    assert packet.readonly is True
    assert packet.no_durable_writes is True
    assert packet.no_raw_text_retention is True
    assert packet.no_live_trading is True
    assert packet.no_wallet_access is True
    assert packet.no_exchange_mutation is True
    assert calls == ["https://www.federalreserve.gov/releases/h15/"]

    with pytest.raises(FrozenInstanceError):
        packet.readonly = False  # type: ignore[misc]

    payload = research_source_capture_packet_payload(packet)
    assert "url" not in payload
    assert "url_host" not in payload
    assert payload["fetched_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["content_length"] == str(d_count(len(text)))
    assert payload["source_age_seconds"] == "300.000000"
    assert payload["reason_codes"] == list(packet.reason_codes)
    payload_json = json.dumps(payload, sort_keys=True)
    payload_text = payload_json.lower()
    assert packet.url not in payload_json
    assert packet.url_host not in payload_json
    assert "/releases/h15/" not in payload_json
    assert "wallet" not in payload_text
    assert "auth" not in payload_text
    assert "order" not in payload_text
    assert "trade" not in payload_text
    assert "trading" not in payload_text
    assert "dsn" not in payload_text
    assert "table" not in payload_text
    assert "market_id" not in payload_text
    assert "market_slug" not in payload_text
    assert "question" not in payload_text


def test_stale_source_sets_stale_freshness_reason() -> None:
    fetched_at = fixed_at()
    packet = capture_research_source_packet(
        "https://example.org/research-note",
        fetch_text=lambda url: "published source text",
        fetched_at=fetched_at,
        as_of=fetched_at + timedelta(days=2),
        max_source_age_seconds=Decimal("86400.000000"),
    )

    assert packet.url_host == "example.org"
    assert packet.host_classification == "organization"
    assert packet.content_length == d_count(len("published source text"))
    assert packet.source_age_seconds == Decimal("172800.000000")
    assert packet.freshness_status == "stale"
    assert packet.extraction_status == "extracted"
    assert packet.reason_codes == (
        "source_text_extracted",
        "source_stale",
        "safe_public_payload",
    )


def test_unavailable_empty_source_sets_unavailable_reason() -> None:
    fetched_at = fixed_at()
    packet = capture_research_source_packet(
        "https://example.com/blank",
        fetch_text=lambda url: " \n\t ",
        fetched_at=fetched_at,
        as_of=fetched_at,
        max_source_age_seconds=Decimal("86400.000000"),
    )

    assert packet.content_length == Decimal("0.000000")
    assert packet.content_sha256 is None
    assert packet.freshness_status == "unavailable"
    assert packet.extraction_status == "empty"
    assert packet.reason_codes == (
        "source_empty",
        "source_unavailable",
        "safe_public_payload",
    )


def test_injected_fetcher_exception_becomes_unavailable_without_message_leak() -> None:
    def failing_fetcher(url: str) -> str:
        raise TimeoutError("wallet token should not leak")

    fetched_at = fixed_at()
    packet = capture_research_source_packet(
        "https://example.com/source",
        fetch_text=failing_fetcher,
        fetched_at=fetched_at,
        as_of=fetched_at,
        max_source_age_seconds=Decimal("86400.000000"),
    )

    payload = research_source_capture_packet_payload(packet)
    payload_json = json.dumps(payload, sort_keys=True)

    assert packet.content_length == Decimal("0.000000")
    assert packet.content_sha256 is None
    assert packet.freshness_status == "unavailable"
    assert packet.extraction_status == "unavailable"
    assert packet.reason_codes == (
        "fetch_exception",
        "source_unavailable",
        "safe_public_payload",
    )
    assert "TimeoutError" not in payload_json
    assert "wallet token should not leak" not in payload_json


def test_unsafe_url_and_value_rejection() -> None:
    fetched_at = fixed_at()

    with pytest.raises(ValueError, match="https"):
        capture_research_source_packet(
            "http://example.com/source",
            fetch_text=lambda url: "text",
            fetched_at=fetched_at,
        )
    with pytest.raises(ValueError, match="credentials"):
        capture_research_source_packet(
            "https://user:pass@example.com/source",
            fetch_text=lambda url: "text",
            fetched_at=fetched_at,
        )
    with pytest.raises(ValueError, match="unsafe"):
        capture_research_source_packet(
            "https://example.com/source?token=abc",
            fetch_text=lambda url: "text",
            fetched_at=fetched_at,
        )

    packet = capture_research_source_packet(
        "https://example.com/source",
        fetch_text=lambda url: "text",
        fetched_at=fetched_at,
    )
    with pytest.raises(ValueError, match="unsafe"):
        replace(packet, reason_codes=("wallet_access",))
    with pytest.raises(ValueError, match="readonly"):
        replace(packet, readonly=False)
    with pytest.raises(ValueError, match="Decimal"):
        replace(packet, content_length=1)  # type: ignore[arg-type]


def test_public_payload_never_contains_raw_full_text() -> None:
    raw_text = "alpha source sentence. " * 20
    packet = capture_research_source_packet(
        "https://example.com/report",
        fetch_text=lambda url: raw_text,
        fetched_at=fixed_at(),
    )

    payload = research_source_capture_packet_payload(packet)
    payload_json = json.dumps(payload, sort_keys=True)

    assert "raw_text" not in payload
    assert "text" not in payload
    assert raw_text not in payload_json
    assert "alpha source sentence" not in payload_json
    assert packet.content_sha256 is not None

    with pytest.raises(ValueError, match="raw text"):
        research_source_capture_packet_payload({**payload, "raw_text": raw_text})


def test_public_payload_rejects_source_identifiers_and_market_surfaces() -> None:
    packet = capture_research_source_packet(
        "https://example.com/report",
        fetch_text=lambda url: "local evidence",
        fetched_at=fixed_at(),
    )
    payload = research_source_capture_packet_payload(packet)

    unsafe_payloads = (
        {**payload, "url": "https://example.com/report"},
        {**payload, "source_url": "https://example.com/report"},
        {**payload, "source_ref": "vendor-report-123"},
        {**payload, "source_reference": "vendor-report-123"},
        {**payload, "market_id": "12345"},
        {**payload, "market_slug": "will-fed-cut-rates"},
        {**payload, "question": "Will the Fed cut rates?"},
        {**payload, "dsn": "postgresql://user:pass@db/internal"},
        {**payload, "table_name": "research_packets"},
        {**payload, "note": "https://example.com/raw-source"},
    )

    for unsafe_payload in unsafe_payloads:
        with pytest.raises(
            ValueError,
            match="unsafe|raw URL|source|market|table|dsn",
        ):
            research_source_capture_packet_payload(unsafe_payload)


def test_capture_requires_injected_fetcher_and_does_not_use_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import socket

    def fail_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("network must not be used by capture boundary")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    calls: list[str] = []

    def fake_fetcher(url: str) -> str:
        calls.append(url)
        return "local fixture text"

    packet = capture_research_source_packet(
        "https://example.com/local-fixture",
        fetch_text=fake_fetcher,
        fetched_at=fixed_at(),
    )

    assert packet.extraction_status == "extracted"
    assert calls == ["https://example.com/local-fixture"]
    with pytest.raises(ValueError, match="fetch_text"):
        capture_research_source_packet(
            "https://example.com/no-fetcher",
            fetch_text=None,  # type: ignore[arg-type]
            fetched_at=fixed_at(),
        )


def test_scrapling_style_adapter_is_lazy_and_uses_only_injected_extractor() -> None:
    calls: list[str] = []

    class ScraplingLikeResult:
        def get_text(self) -> str:
            return "local fixture text"

    def extractor(url: str) -> ScraplingLikeResult:
        calls.append(url)
        return ScraplingLikeResult()

    fetch_text = scrapling_style_text_fetcher(extractor)

    assert calls == []
    assert fetch_text("https://example.com/local-fixture") == "local fixture text"
    assert calls == ["https://example.com/local-fixture"]


def test_pure_boundary_guard_rejects_durable_or_mutating_surfaces() -> None:
    packet = capture_research_source_packet(
        "https://example.com/report",
        fetch_text=lambda url: "local evidence",
        fetched_at=fixed_at(),
    )
    payload = research_source_capture_packet_payload(packet)

    assert_research_source_capture_pure_boundary(packet)
    assert_research_source_capture_pure_boundary(payload)

    with pytest.raises(ValueError, match="no_durable_writes"):
        assert_research_source_capture_pure_boundary(
            {**payload, "no_durable_writes": False}
        )
    with pytest.raises(ValueError, match="raw text"):
        assert_research_source_capture_pure_boundary(
            {**payload, "captured_text": "local evidence"}
        )
    with pytest.raises(ValueError, match="exchange"):
        assert_research_source_capture_pure_boundary(
            {**payload, "no_exchange_mutation": False}
        )


def test_module_scope_is_phase1_readonly_and_has_no_implicit_io_surfaces() -> None:
    source = inspect.getsource(source_capture_module)
    tree = ast.parse(source)

    assert source_capture_module.__all__ == (
        "FetchText",
        "ResearchSourceCapturePacket",
        "assert_research_source_capture_pure_boundary",
        "capture_research_source_packet",
        "research_source_capture_packet_payload",
        "scrapling_style_text_fetcher",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "ipaddress",
        "typing",
        "urllib",
    }

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "getenv",
        "open",
        "read_bytes",
        "read_text",
        "request",
        "send",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names

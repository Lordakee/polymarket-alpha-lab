from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_packet_public_source_redundancy_gate_v2 as api
from polymarket_alpha_lab.research_packet_public_source_redundancy_gate_v2 import (
    ResearchPacketPublicSourceRedundancyGateConfig,
    ResearchPacketPublicSourceRedundancyGateInput,
    ResearchPacketPublicSourceRedundancyGateReasonCodeCount,
    ResearchPacketPublicSourceRedundancyGateReport,
    ResearchPacketPublicSourceRedundancyGateRow,
    build_research_packet_public_source_redundancy_gate_v2_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def packet(
    packet_id: str = "packet_pass",
    *,
    event_slug: str = "event_a",
    category: str = "politics",
    public_source_count: Decimal = d("3.000000"),
    independent_source_family_count: Decimal = d("2.000000"),
    duplicate_source_count: Decimal = d("0.000000"),
    official_source_count: Decimal = d("1.000000"),
    proxy_source_count: Decimal = d("0.000000"),
) -> ResearchPacketPublicSourceRedundancyGateInput:
    return ResearchPacketPublicSourceRedundancyGateInput(
        packet_id=packet_id,
        event_slug=event_slug,
        category=category,
        public_source_count=public_source_count,
        independent_source_family_count=independent_source_family_count,
        duplicate_source_count=duplicate_source_count,
        official_source_count=official_source_count,
        proxy_source_count=proxy_source_count,
    )


def report(
    *rows: ResearchPacketPublicSourceRedundancyGateInput,
    generated_at: datetime = NOW,
    config: ResearchPacketPublicSourceRedundancyGateConfig | None = None,
) -> ResearchPacketPublicSourceRedundancyGateReport:
    return build_research_packet_public_source_redundancy_gate_v2_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def test_rows_compute_redundancy_independence_status_and_sorted_rollups() -> None:
    result = report(
        packet(
            "packet_watch_duplicate",
            event_slug="event_b",
            category="sports",
            public_source_count=d("4.000000"),
            independent_source_family_count=d("3.000000"),
            duplicate_source_count=d("2.000000"),
            official_source_count=d("1.000000"),
            proxy_source_count=d("1.000000"),
        ),
        packet(
            "packet_block_sources",
            event_slug="event_a",
            category="economics",
            public_source_count=d("2.000000"),
            independent_source_family_count=d("1.000000"),
            duplicate_source_count=d("0.000000"),
            official_source_count=d("1.000000"),
            proxy_source_count=d("0.000000"),
        ),
        packet(),
    )

    assert tuple(row.packet_id for row in result.rows) == (
        "packet_block_sources",
        "packet_pass",
        "packet_watch_duplicate",
    )

    blocked, passed, watched = result.rows
    assert blocked.redundancy_score == d("0.666667")
    assert blocked.independence_ratio == d("0.500000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "insufficient_public_sources",
        "low_independence",
    )

    assert passed.redundancy_score == d("1.000000")
    assert passed.independence_ratio == d("0.666667")
    assert passed.status == "pass"
    assert passed.reason_codes == ("public_source_redundancy_pass",)

    assert watched.redundancy_score == d("0.666667")
    assert watched.independence_ratio == d("0.750000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "duplicate_sources_present",
        "proxy_sources_present",
    )

    assert result.report_status == "block"
    assert result.packet_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.insufficient_public_source_count == d("1.000000")
    assert result.low_independence_count == d("1.000000")
    assert result.duplicate_source_count == d("2.000000")
    assert result.min_redundancy_score == d("0.666667")
    assert result.reason_code_counts == (
        ResearchPacketPublicSourceRedundancyGateReasonCodeCount(
            "insufficient_public_sources",
            d("1.000000"),
        ),
        ResearchPacketPublicSourceRedundancyGateReasonCodeCount(
            "low_independence",
            d("1.000000"),
        ),
        ResearchPacketPublicSourceRedundancyGateReasonCodeCount(
            "duplicate_sources_present",
            d("1.000000"),
        ),
        ResearchPacketPublicSourceRedundancyGateReasonCodeCount(
            "proxy_sources_present",
            d("1.000000"),
        ),
        ResearchPacketPublicSourceRedundancyGateReasonCodeCount(
            "public_source_redundancy_pass",
            d("1.000000"),
        ),
    )


def test_empty_input_returns_empty_status_and_zero_decimal_rollups() -> None:
    result = report()

    assert result.report_status == "empty"
    assert result.rows == ()
    assert result.reason_code_counts == ()
    assert result.packet_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.insufficient_public_source_count == d("0.000000")
    assert result.low_independence_count == d("0.000000")
    assert result.duplicate_source_count == d("0.000000")
    assert result.min_redundancy_score == d("0.000000")


def test_payload_is_safe_json_with_decimal_strings_and_digest() -> None:
    result = report(packet())

    payload = result.payload
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["packet_count"] == "1.000000"
    assert payload["min_redundancy_score"] == "1.000000"
    assert payload["rows"][0]["public_source_count"] == "3.000000"
    assert payload["rows"][0]["redundancy_score"] == "1.000000"
    assert payload["rows"][0]["independence_ratio"] == "0.666667"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert len(result.derived_validation_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(result)


def test_frozen_dataclasses_decimal_only_and_digest_tamper_checks() -> None:
    result = report(packet())

    for value in (
        ResearchPacketPublicSourceRedundancyGateConfig(),
        packet(),
        result.rows[0],
        result.reason_code_counts[0],
        result,
    ):
        assert hasattr(value, "__dataclass_fields__")
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="public_source_count"):
        packet(public_source_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_source_count"):
        packet(public_source_count=d("3.0000004"))
    with pytest.raises(ValueError, match="independent_source_family_count"):
        packet(independent_source_family_count=d("1.500000"))
    with pytest.raises(ValueError, match="duplicate_source_count"):
        packet(duplicate_source_count=d("-1.000000"))
    with pytest.raises(ValueError, match="official_source_count"):
        packet(official_source_count=d("4.000000"))
    with pytest.raises(ValueError, match="proxy_source_count"):
        packet(proxy_source_count=d("4.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        ResearchPacketPublicSourceRedundancyGateConfig(paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=())


def test_unsafe_surfaces_and_runtime_io_are_not_exposed() -> None:
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchPacketPublicSourceRedundancyGateConfig,
        ResearchPacketPublicSourceRedundancyGateInput,
        ResearchPacketPublicSourceRedundancyGateRow,
        ResearchPacketPublicSourceRedundancyGateReasonCodeCount,
        ResearchPacketPublicSourceRedundancyGateReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    with pytest.raises(ValueError, match="unsafe public"):
        packet(packet_id="wallet_packet")


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))

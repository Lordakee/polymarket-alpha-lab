from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.market_research_packet_version_readiness_report as api
from polymarket_alpha_lab.market_research_packet_version_readiness_report import (
    DEFAULT_MARKET_RESEARCH_PACKET_VERSION_READINESS_REPORT_CONFIG_VERSION,
    MARKET_RESEARCH_PACKET_VERSION_READINESS_BANDS,
    MarketResearchPacketVersionReadinessConfig,
    MarketResearchPacketVersionReadinessInput,
    MarketResearchPacketVersionReadinessReport,
    MarketResearchPacketVersionReadinessRow,
    build_market_research_packet_version_readiness_report,
    market_research_packet_version_readiness_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 8, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_packet_version_readiness_report.py",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchPacketVersionReadinessConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_PACKET_VERSION_READINESS_REPORT_CONFIG_VERSION
        ),
        "attention_revision_gap_threshold": d("1.000000"),
        "blocker_revision_gap_threshold": d("3.000000"),
        "attention_stale_section_threshold": d("1.000000"),
        "blocker_stale_section_threshold": d("3.000000"),
    }
    values.update(overrides)
    return MarketResearchPacketVersionReadinessConfig(**values)


def packet(
    market_key: str = "market-alpha",
    *,
    packet_revision: Decimal = d("7.000000"),
    latest_source_revision: Decimal = d("7.000000"),
    stale_section_count: Decimal = ZERO,
    missing_required_section_count: Decimal = ZERO,
    changed_after_forecast: bool = False,
    manual_ack_required: bool = False,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPacketVersionReadinessInput:
    return MarketResearchPacketVersionReadinessInput(
        market_key=market_key,
        packet_revision=packet_revision,
        latest_source_revision=latest_source_revision,
        stale_section_count=stale_section_count,
        missing_required_section_count=missing_required_section_count,
        changed_after_forecast=changed_after_forecast,
        manual_ack_required=manual_ack_required,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *packets: MarketResearchPacketVersionReadinessInput,
    cfg: MarketResearchPacketVersionReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPacketVersionReadinessReport:
    return build_market_research_packet_version_readiness_report(
        packets,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_readiness_band_vocabulary_is_exact() -> None:
    assert MARKET_RESEARCH_PACKET_VERSION_READINESS_BANDS == (
        "ready",
        "attention",
        "blocker",
    )


def test_ready_attention_blocker_rows_and_aggregate_ratios_are_deterministic() -> None:
    ready_packet = packet(
        "ready-market",
        packet_revision=d("9.000000"),
        latest_source_revision=d("9.000000"),
    )
    attention_packet = packet(
        "attention-market",
        packet_revision=d("8.000000"),
        latest_source_revision=d("9.000000"),
        stale_section_count=ONE,
        changed_after_forecast=True,
    )
    blocker_packet = packet(
        "blocker-market",
        packet_revision=d("5.000000"),
        latest_source_revision=d("9.000000"),
        stale_section_count=d("4.000000"),
        missing_required_section_count=ONE,
        manual_ack_required=True,
    )

    first = report(attention_packet, blocker_packet, ready_packet)
    second = report(ready_packet, attention_packet, blocker_packet)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_MARKET_RESEARCH_PACKET_VERSION_READINESS_REPORT_CONFIG_VERSION
    )
    assert first.market_count == d("3.000000")
    assert first.ready_market_count == ONE
    assert first.attention_market_count == ONE
    assert first.blocker_market_count == ONE
    assert first.packet_current_market_count == ONE
    assert first.stale_packet_market_count == d("2.000000")
    assert first.missing_required_section_market_count == ONE
    assert first.changed_after_forecast_market_count == ONE
    assert first.manual_ack_required_market_count == ONE
    assert first.packet_current_ratio == d("0.333333")
    assert first.ready_ratio == d("0.333333")
    assert first.attention_ratio == d("0.333333")
    assert first.blocker_ratio == d("0.333333")
    assert first.manual_ack_required_ratio == d("0.333333")
    assert first.max_revision_gap == d("4.000000")
    assert first.max_stale_section_count == d("4.000000")
    assert first.report_band == "blocker"
    assert first.reason_codes == (
        "market_research_packet_version_readiness_blocker",
        "packet_revision_gap_blocker",
        "missing_required_section_blocker",
        "stale_section_count_blocker",
        "manual_ack_required_blocker",
        "packet_revision_gap_attention",
        "stale_section_count_attention",
        "changed_after_forecast_attention",
    )
    assert tuple(row.market_key for row in first.rows) == (
        "blocker-market",
        "attention-market",
        "ready-market",
    )
    assert tuple(row.readiness_band for row in first.rows) == (
        "blocker",
        "attention",
        "ready",
    )

    blocker = first.rows[0]
    assert blocker.packet_current is False
    assert blocker.revision_gap == d("4.000000")
    assert blocker.reason_codes == (
        "packet_revision_gap_blocker",
        "missing_required_section_blocker",
        "stale_section_count_blocker",
        "manual_ack_required_blocker",
    )
    assert blocker.completeness_ratio == d("0.250000")

    attention = first.rows[1]
    assert attention.packet_current is False
    assert attention.revision_gap == ONE
    assert attention.reason_codes == (
        "packet_revision_gap_attention",
        "stale_section_count_attention",
        "changed_after_forecast_attention",
    )

    ready = first.rows[2]
    assert ready.packet_current is True
    assert ready.revision_gap == ZERO
    assert ready.reason_codes == ("market_research_packet_version_readiness_ready",)

    assert first == second
    payload = market_research_packet_version_readiness_payload(first)
    assert payload["market_count"] == "3.000000"
    assert payload["rows"][0]["revision_gap"] == "4.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)


def test_empty_report_is_attention_and_ratios_are_zero() -> None:
    readiness = report()

    assert readiness.market_count == ZERO
    assert readiness.report_band == "attention"
    assert readiness.reason_codes == (
        "market_research_packet_version_readiness_no_markets",
    )
    assert readiness.packet_current_ratio == ZERO
    assert readiness.ready_ratio == ZERO
    assert readiness.attention_ratio == ZERO
    assert readiness.blocker_ratio == ZERO
    assert readiness.rows == ()


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    readiness = report(packet())

    with pytest.raises(FrozenInstanceError):
        readiness.report_band = "ready"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadPacket(MarketResearchPacketVersionReadinessInput):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        MarketResearchPacketVersionReadinessConfig(paper_only=False)

    with pytest.raises(ValueError, match="packet_revision must be a Decimal"):
        packet(packet_revision=7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="packet_revision must be an integer"):
        packet(packet_revision=d("7.500000"))

    with pytest.raises(ValueError, match="latest_source_revision must be greater than or equal"):
        packet(packet_revision=d("10.000000"), latest_source_revision=d("9.000000"))

    with pytest.raises(ValueError, match="changed_after_forecast must be a bool"):
        packet(changed_after_forecast=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="readonly"):
        packet(readonly=False)

    with pytest.raises(ValueError, match="rows must contain"):
        MarketResearchPacketVersionReadinessReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_PACKET_VERSION_READINESS_REPORT_CONFIG_VERSION
            ),
            report_band="ready",
            reason_codes=("market_research_packet_version_readiness_ready",),
            market_count=ONE,
            ready_market_count=ONE,
            attention_market_count=ZERO,
            blocker_market_count=ZERO,
            packet_current_market_count=ONE,
            stale_packet_market_count=ZERO,
            missing_required_section_market_count=ZERO,
            changed_after_forecast_market_count=ZERO,
            manual_ack_required_market_count=ZERO,
            packet_current_ratio=ONE,
            ready_ratio=ONE,
            attention_ratio=ZERO,
            blocker_ratio=ZERO,
            manual_ack_required_ratio=ZERO,
            max_revision_gap=ZERO,
            max_stale_section_count=ZERO,
            rows=("not-a-row",),  # type: ignore[arg-type]
        )


def test_public_api_excludes_live_trading_auth_wallet_database_and_network_surfaces() -> None:
    forbidden_fragments = (
        "auth",
        "wallet",
        "order",
        "trade",
        "broker",
        "position",
        "database",
        "db",
        "network",
        "http",
        "socket",
        "request",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        MarketResearchPacketVersionReadinessConfig,
        MarketResearchPacketVersionReadinessInput,
        MarketResearchPacketVersionReadinessRow,
        MarketResearchPacketVersionReadinessReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

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

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "web3",
            "ccxt",
        },
    )

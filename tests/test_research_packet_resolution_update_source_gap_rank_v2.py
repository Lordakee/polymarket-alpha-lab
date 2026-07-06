from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 21, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_packet_resolution_update_source_gap_rank_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def ago(seconds: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds)


def config(**overrides: object):
    values = {
        "config_version": "research-packet-resolution-update-source-gap-rank-v2",
        "stale_update_watch_after_seconds": d("3600.000000"),
        "stale_update_block_after_seconds": d("7200.000000"),
        "recent_official_update_boost_seconds": d("1800.000000"),
        "missing_update_penalty_score": d("0.500000"),
        "stale_update_watch_penalty_score": d("0.200000"),
        "stale_update_block_penalty_score": d("0.350000"),
        "missing_official_update_penalty_score": d("0.100000"),
        "low_source_count_penalty_score": d("0.150000"),
        "official_update_boost_score": d("0.100000"),
        "blocked_gap_score": d("0.700000"),
        "watch_gap_score": d("0.100000"),
    }
    values.update(overrides)
    return api().ResearchPacketResolutionUpdateSourceGapRankV2Config(**values)


def packet(
    packet_id: str,
    *,
    market_id: str = "market-alpha",
    update_source_id: str = "source-alpha",
    latest_resolution_update_at: datetime | None = None,
    latest_official_resolution_update_at: datetime | None = None,
    source_count: str = "2",
    required_source_count: str = "2",
    update_relevance_score: str = "0.900000",
):
    return api().ResearchPacketResolutionUpdateSourceGapRankV2Input(
        packet_id=packet_id,
        market_id=market_id,
        update_source_id=update_source_id,
        latest_resolution_update_at=latest_resolution_update_at,
        latest_official_resolution_update_at=latest_official_resolution_update_at,
        source_count=d(source_count),
        required_source_count=d(required_source_count),
        update_relevance_score=d(update_relevance_score),
    )


def report(*rows: object, generated_at: datetime = GENERATED_AT, **overrides: object):
    return api().build_research_packet_resolution_update_source_gap_rank_v2_report(
        rows,
        config=config(**overrides),
        generated_at=generated_at,
    )


def test_resolution_update_source_gap_rows_rank_deterministically() -> None:
    ranked = report(
        packet(
            "packet-pass",
            latest_resolution_update_at=ago(300),
            latest_official_resolution_update_at=ago(240),
            update_relevance_score="0.950000",
        ),
        packet(
            "packet-stale",
            latest_resolution_update_at=ago(7200),
            source_count="2",
            required_source_count="2",
            update_relevance_score="0.800000",
        ),
        packet(
            "packet-missing",
            latest_resolution_update_at=None,
            source_count="0",
            required_source_count="2",
            update_relevance_score="0.800000",
        ),
        packet(
            "packet-low-source",
            latest_resolution_update_at=ago(1200),
            source_count="1",
            required_source_count="2",
            update_relevance_score="0.820000",
        ),
    )

    assert tuple(row.packet_id for row in ranked.rows) == (
        "packet-missing",
        "packet-stale",
        "packet-low-source",
        "packet-pass",
    )
    assert tuple(row.gap_rank for row in ranked.rows) == (
        d("1"),
        d("2"),
        d("3"),
        d("4"),
    )
    assert ranked.report_status == "blocked"
    assert ranked.blocked_count == d("2")
    assert ranked.watch_count == d("1")
    assert ranked.pass_count == d("1")
    assert ranked.max_source_gap_score == d("0.950000")
    assert ranked.reason_codes == (
        "source_gap_blocked_packets_present",
        "resolution_updates_missing",
        "resolution_updates_stale",
        "official_resolution_updates_missing",
        "source_counts_below_required",
        "official_resolution_updates_recent",
    )


def test_stale_update_penalties_and_official_update_boosts() -> None:
    ranked = report(
        packet(
            "packet-unofficial-stale",
            latest_resolution_update_at=ago(3600),
            latest_official_resolution_update_at=None,
            update_relevance_score="0.900000",
        ),
        packet(
            "packet-official-stale",
            latest_resolution_update_at=ago(3600),
            latest_official_resolution_update_at=ago(600),
            update_relevance_score="0.900000",
        ),
    )
    rows = {row.packet_id: row for row in ranked.rows}

    assert rows["packet-unofficial-stale"].stale_update_penalty_score == d("0.200000")
    assert rows["packet-unofficial-stale"].unofficial_update_penalty_score == d("0.100000")
    assert rows["packet-unofficial-stale"].official_update_boost_score == d("0.000000")
    assert rows["packet-unofficial-stale"].source_gap_score == d("0.400000")
    assert rows["packet-unofficial-stale"].gap_rank == d("1")

    assert rows["packet-official-stale"].stale_update_penalty_score == d("0.200000")
    assert rows["packet-official-stale"].unofficial_update_penalty_score == d("0.000000")
    assert rows["packet-official-stale"].official_update_boost_score == d("0.100000")
    assert rows["packet-official-stale"].source_gap_score == d("0.200000")
    assert rows["packet-official-stale"].gap_rank == d("2")
    assert "official_resolution_update_recent" in rows["packet-official-stale"].reason_codes


def test_payload_serializes_decimals_as_strings_and_validates_digest() -> None:
    module = api()
    ranked = report(
        packet(
            "packet-a",
            latest_resolution_update_at=ago(3600),
            latest_official_resolution_update_at=ago(600),
            update_relevance_score="0.900000",
        ),
    )

    payload = module.research_packet_resolution_update_source_gap_rank_v2_payload(ranked)

    assert payload["packet_count"] == "1"
    assert payload["rows"][0]["source_gap_score"] == "0.200000"
    assert payload["rows"][0]["gap_rank"] == "1"
    assert type(payload["rows"][0]["source_gap_score"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert len(payload["rows"][0]["derived_validation_digest"]) == 64
    assert not _contains_float(payload)
    json.dumps(payload, sort_keys=True)
    assert module.research_packet_resolution_update_source_gap_rank_v2_payload(payload) == payload

    tampered = dict(payload)
    tampered["rows"] = [dict(payload["rows"][0])]
    tampered["rows"][0]["source_gap_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        module.research_packet_resolution_update_source_gap_rank_v2_payload(tampered)


def test_frozen_dataclasses_hard_flags_and_decimal_only_public_numbers() -> None:
    module = api()
    cfg = config()
    row = packet(
        "packet-a",
        latest_resolution_update_at=ago(60),
        latest_official_resolution_update_at=ago(30),
    )
    ranked = report(row)

    for value in (cfg, row, ranked, *ranked.rows):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        _assert_public_numbers_are_decimal_only(value)

    with pytest.raises(ValueError, match="readonly"):
        replace(cfg, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(ranked, report_only=False)
    with pytest.raises(ValueError, match="source_count"):
        module.ResearchPacketResolutionUpdateSourceGapRankV2Input(
            packet_id="packet-int-count",
            market_id="market-alpha",
            update_source_id="source-alpha",
            latest_resolution_update_at=ago(60),
            latest_official_resolution_update_at=ago(30),
            source_count=1,  # type: ignore[arg-type]
            required_source_count=d("1"),
            update_relevance_score=d("0.900000"),
        )
    with pytest.raises(ValueError, match="update_relevance_score"):
        module.ResearchPacketResolutionUpdateSourceGapRankV2Input(
            packet_id="packet-decimal-subclass",
            market_id="market-alpha",
            update_source_id="source-alpha",
            latest_resolution_update_at=ago(60),
            latest_official_resolution_update_at=ago(30),
            source_count=d("1"),
            required_source_count=d("1"),
            update_relevance_score=_DecimalSubclass("0.900000"),
        )


def test_derived_validation_digest_rejects_dataclass_tampering() -> None:
    ranked = report(
        packet(
            "packet-a",
            latest_resolution_update_at=ago(3600),
            latest_official_resolution_update_at=ago(600),
            update_relevance_score="0.900000",
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(ranked, generated_at=GENERATED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(ranked.rows[0], source_gap_score=d("0.999999"))


def test_unsafe_public_values_and_payload_keys_are_rejected() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public value"):
        packet("packet-wallet", latest_resolution_update_at=ago(60))
    with pytest.raises(ValueError, match="unsafe public value"):
        packet(
            "packet-safe",
            update_source_id="source-needs-signing",
            latest_resolution_update_at=ago(60),
        )
    with pytest.raises(ValueError, match="unsafe public key"):
        module.research_packet_resolution_update_source_gap_rank_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "network_hint": "none",
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_packet_resolution_update_source_gap_rank_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "safe_hint": "requires live path",
                "derived_validation_digest": "0" * 64,
            },
        )


def test_static_module_surface_is_readonly_report_only_paper_only() -> None:
    module = api()
    assert module.UNSAFE_PUBLIC_TERMS == (
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

    source = Path(
        "src/polymarket_alpha_lab/research_packet_resolution_update_source_gap_rank_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "execute",
        "executemany",
        "request",
        "post",
        "put",
        "patch",
        "delete",
        "place_order",
        "create_order",
        "sign",
    }
    forbidden_string_fragments = (
        "http://",
        "https://",
        "private_key",
        "api_key",
        "secret",
        "token",
        "live_trading",
        "place_order",
        "create_order",
    )

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            for name in names:
                assert name.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_call_names
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_call_names
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
            if isinstance(node.value, str):
                lowered = node.value.lower()
                assert not any(fragment in lowered for fragment in forbidden_string_fragments)


def _assert_public_numbers_are_decimal_only(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool or item is None:
            continue
        if type(item) in (int, float):
            raise AssertionError(f"{field.name} is not Decimal-only")
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    _assert_public_numbers_are_decimal_only(nested)


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False

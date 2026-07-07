from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_packet_market_context_source_gap_v2 import (
    DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_SOURCE_GAP_V2_CONFIG_VERSION,
    ResearchPacketMarketContextSourceGapV2Config,
    ResearchPacketMarketContextSourceGapV2Packet,
    ResearchPacketMarketContextSourceGapV2Report,
    ResearchPacketMarketContextSourceGapV2Row,
    build_research_packet_market_context_source_gap_v2_report,
    research_packet_market_context_source_gap_v2_payload,
    validate_research_packet_market_context_source_gap_v2_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _unsafe(*parts: str) -> str:
    return "".join(parts)


def _packet(packet_id: str, **overrides: object) -> ResearchPacketMarketContextSourceGapV2Packet:
    values: dict[str, object] = {
        "event_id": f"event_{packet_id}",
        "packet_id": packet_id,
        "event_category": "macro_cpi",
        "captured_at": GENERATED_AT - timedelta(minutes=30),
        "required_macro_source_count": d("2"),
        "present_macro_source_count": d("2"),
        "required_context_source_count": d("2"),
        "present_context_source_count": d("2"),
        "official_anchor_checked_at": GENERATED_AT - timedelta(minutes=20),
        "independent_source_family_count": d("3"),
        "contradiction_severity": d("0"),
        "probability_move_abs": d("0.010000"),
        "movement_explanation": None,
        "resolution_at": GENERATED_AT + timedelta(days=7),
    }
    values.update(overrides)
    return ResearchPacketMarketContextSourceGapV2Packet(**values)


def _report() -> ResearchPacketMarketContextSourceGapV2Report:
    return build_research_packet_market_context_source_gap_v2_report(
        (
            _packet(
                "gap_packet",
                present_macro_source_count=d("1"),
                present_context_source_count=d("0"),
                official_anchor_checked_at=GENERATED_AT - timedelta(hours=3),
                independent_source_family_count=d("1"),
                contradiction_severity=d("0.800000"),
                probability_move_abs=d("0.120000"),
                resolution_at=GENERATED_AT + timedelta(hours=6),
            ),
            _packet(
                "watch_packet",
                independent_source_family_count=d("1"),
                contradiction_severity=d("0.200000"),
                probability_move_abs=d("0.020000"),
                resolution_at=GENERATED_AT + timedelta(hours=12),
            ),
            _packet("pass_packet"),
        ),
        config=ResearchPacketMarketContextSourceGapV2Config(),
        generated_at=GENERATED_AT,
    )


def test_report_flags_market_context_source_gap_dimensions_with_decimal_counts() -> None:
    report = _report()

    assert isinstance(report, ResearchPacketMarketContextSourceGapV2Report)
    assert report.config_version == DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_SOURCE_GAP_V2_CONFIG_VERSION
    assert report.report_status == "blocked"
    assert report.packet_count == d("3.000000")
    assert report.pass_packet_count == d("1.000000")
    assert report.watch_packet_count == d("1.000000")
    assert report.blocked_packet_count == d("1.000000")
    assert report.attention_packet_count == d("2.000000")
    assert report.attention_packet_ratio == d("0.666667")
    assert report.missing_macro_source_packet_count == d("1.000000")
    assert report.missing_context_source_packet_count == d("1.000000")
    assert report.stale_official_anchor_packet_count == d("1.000000")
    assert report.weak_source_family_packet_count == d("2.000000")
    assert report.contradiction_packet_count == d("2.000000")
    assert report.severe_contradiction_packet_count == d("1.000000")
    assert report.unexplained_probability_movement_packet_count == d("1.000000")
    assert report.near_resolution_horizon_packet_count == d("2.000000")
    assert report.max_contradiction_severity == d("0.800000")
    assert report.max_probability_move_abs == d("0.120000")
    assert report.min_resolution_horizon_seconds == d("21600.000000")
    assert tuple((row.packet_id, row.gap_status) for row in report.rows) == (
        ("gap_packet", "blocked"),
        ("watch_packet", "watch"),
        ("pass_packet", "pass"),
    )
    assert report.rows[0] == ResearchPacketMarketContextSourceGapV2Row(
        event_id="event_gap_packet",
        packet_id="gap_packet",
        event_category="macro_cpi",
        captured_at=GENERATED_AT - timedelta(minutes=30),
        official_anchor_checked_at=GENERATED_AT - timedelta(hours=3),
        official_anchor_age_seconds=d("10800.000000"),
        resolution_at=GENERATED_AT + timedelta(hours=6),
        resolution_horizon_seconds=d("21600.000000"),
        required_macro_source_count=d("2.000000"),
        present_macro_source_count=d("1.000000"),
        missing_macro_source_count=d("1.000000"),
        required_context_source_count=d("2.000000"),
        present_context_source_count=d("0.000000"),
        missing_context_source_count=d("2.000000"),
        independent_source_family_count=d("1.000000"),
        contradiction_severity=d("0.800000"),
        probability_move_abs=d("0.120000"),
        movement_explanation_present=False,
        gap_status="blocked",
        reason_codes=(
            "research_packet_market_context_source_gap_v2_missing_macro_source",
            "research_packet_market_context_source_gap_v2_missing_context_source",
            "research_packet_market_context_source_gap_v2_stale_official_anchor",
            "research_packet_market_context_source_gap_v2_weak_source_family_independence",
            "research_packet_market_context_source_gap_v2_contradiction_severe",
            "research_packet_market_context_source_gap_v2_unexplained_probability_movement",
            "research_packet_market_context_source_gap_v2_near_resolution_horizon",
        ),
        derived_validation_digest=report.rows[0].derived_validation_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)


def test_payload_serializes_decimal_strings_and_rejects_public_tampering() -> None:
    report = build_research_packet_market_context_source_gap_v2_report(
        (
            _packet(
                "offset_packet",
                captured_at=datetime(2026, 7, 6, 7, 30, tzinfo=timezone(timedelta(hours=-4))),
                official_anchor_checked_at=datetime(
                    2026,
                    7,
                    6,
                    7,
                    45,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                resolution_at=datetime(2026, 7, 7, 7, 30, tzinfo=timezone(timedelta(hours=-4))),
            ),
        ),
        config=ResearchPacketMarketContextSourceGapV2Config(
            near_resolution_horizon_seconds=d("3600"),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = research_packet_market_context_source_gap_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["packet_count"] == "1.000000"
    assert payload["attention_packet_ratio"] == "0.000000"
    assert payload["max_probability_move_abs"] == "0.010000"
    assert payload["rows"][0]["captured_at"] == "2026-07-06T11:30:00+00:00"
    assert payload["rows"][0]["official_anchor_age_seconds"] == "900.000000"
    assert payload["rows"][0]["resolution_horizon_seconds"] == "84600.000000"
    assert payload["rows"][0]["present_macro_source_count"] == "2.000000"
    assert payload["rows"][0]["derived_validation_digest"] == report.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert validate_research_packet_market_context_source_gap_v2_public_payload(payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_packet_market_context_source_gap_v2_public_payload(missing_digest)

    tampered_payload = dict(payload)
    tampered_payload["packet_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_market_context_source_gap_v2_payload(tampered_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload[_unsafe("wal", "let", "_id")] = "redacted"
    with pytest.raises(ValueError, match="public"):
        research_packet_market_context_source_gap_v2_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["operator_note"] = _unsafe("needs_", "tra", "de", "_desk")
    with pytest.raises(ValueError, match="public"):
        research_packet_market_context_source_gap_v2_payload(unsafe_value_payload)


def test_frozen_decimal_only_inputs_flags_and_dataclass_tamper_revalidation() -> None:
    with pytest.raises(ValueError, match="config_version"):
        ResearchPacketMarketContextSourceGapV2Config(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_SOURCE_GAP_V2_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="max_official_anchor_age_seconds"):
        ResearchPacketMarketContextSourceGapV2Config(max_official_anchor_age_seconds=3600)
    with pytest.raises(ValueError, match="min_independent_source_family_count"):
        ResearchPacketMarketContextSourceGapV2Config(
            min_independent_source_family_count=_DecimalSubclass("2"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(ResearchPacketMarketContextSourceGapV2Config(), paper_only=False)
    with pytest.raises(ValueError, match="event_id"):
        _packet("unsafe_packet", event_id=_unsafe("au", "th", "_reference"))
    with pytest.raises(ValueError, match="required_macro_source_count"):
        _packet("numeric_packet", required_macro_source_count=2)
    with pytest.raises(ValueError, match="probability_move_abs"):
        _packet("float_packet", probability_move_abs=0.1)
    with pytest.raises(ValueError, match="captured_at"):
        _packet("naive_packet", captured_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_packet_market_context_source_gap_v2_report(
            (_packet("packet"),),
            config=ResearchPacketMarketContextSourceGapV2Config(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )

    report = _report()
    with pytest.raises(FrozenInstanceError):
        report.report_status = "pass"
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)

    tampered_report = _report()
    object.__setattr__(tampered_report.rows[0], "contradiction_severity", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest|reason_codes"):
        research_packet_market_context_source_gap_v2_payload(tampered_report)


def test_module_scope_is_readonly_report_only_and_has_no_external_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_packet_market_context_source_gap_v2",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered_source = source.lower()

    forbidden_surface_tokens = (
        _unsafe("li", "ve"),
        _unsafe("au", "th"),
        _unsafe("wal", "let"),
        _unsafe("ord", "er"),
        _unsafe("net", "work"),
        _unsafe("data", "base"),
        _unsafe("per", "sist"),
        _unsafe("sign", "ing"),
        _unsafe("muta", "tion"),
        _unsafe("bu", "y"),
        _unsafe("se", "ll"),
        _unsafe("tra", "de"),
    )
    assert not any(token in lowered_source for token in forbidden_surface_tokens)
    assert not hasattr(module, "client")
    assert not hasattr(module, "session")

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "asyncio",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

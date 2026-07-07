from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from numbers import Number
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.research_packet_market_moving_news_gap_v2",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"expected detector module to be importable: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def _unsafe(*parts: str) -> str:
    return "".join(parts)


def _contains_number(value: object) -> bool:
    if type(value) is dict:
        return any(_contains_number(item) for item in value.values())
    if type(value) is list:
        return any(_contains_number(item) for item in value)
    return isinstance(value, Number) and type(value) is not bool


def _packet(packet_id: str, **overrides: object):
    gap = api()
    values: dict[str, object] = {
        "market_id": f"market_{packet_id}",
        "packet_id": packet_id,
        "event_category": "macro_cpi",
        "captured_at": GENERATED_AT - timedelta(minutes=5),
        "latest_update_at": GENERATED_AT - timedelta(minutes=10),
        "official_source_count": d("1"),
        "independent_source_count": d("3"),
        "contradiction_severity": d("0.000000"),
        "probability_move_abs": d("0.010000"),
        "market_close_at": GENERATED_AT + timedelta(days=7),
    }
    values.update(overrides)
    return gap.ResearchPacketMarketMovingNewsGapV2Packet(**values)


def _report():
    gap = api()
    return gap.build_research_packet_market_moving_news_gap_v2_report(
        (
            _packet(
                "gap_packet",
                latest_update_at=GENERATED_AT - timedelta(hours=2),
                official_source_count=d("0"),
                independent_source_count=d("1"),
                contradiction_severity=d("0.800000"),
                probability_move_abs=d("0.120000"),
                market_close_at=GENERATED_AT + timedelta(hours=3),
            ),
            _packet(
                "watch_packet",
                independent_source_count=d("1"),
                contradiction_severity=d("0.200000"),
                probability_move_abs=d("0.020000"),
                market_close_at=GENERATED_AT + timedelta(hours=4),
            ),
            _packet("pass_packet"),
        ),
        config=gap.ResearchPacketMarketMovingNewsGapV2Config(),
        generated_at=GENERATED_AT,
    )


def test_report_flags_market_moving_news_gap_dimensions_with_decimal_counts() -> None:
    gap = api()
    report = _report()

    assert is_dataclass(report)
    assert report.config_version == (
        gap.DEFAULT_RESEARCH_PACKET_MARKET_MOVING_NEWS_GAP_V2_CONFIG_VERSION
    )
    assert report.report_status == "blocked"
    assert report.packet_count == d("3.000000")
    assert report.pass_packet_count == d("1.000000")
    assert report.watch_packet_count == d("1.000000")
    assert report.blocked_packet_count == d("1.000000")
    assert report.attention_packet_count == d("2.000000")
    assert report.attention_packet_ratio == d("0.666667")
    assert report.missing_latest_update_packet_count == d("0.000000")
    assert report.stale_latest_update_packet_count == d("1.000000")
    assert report.missing_official_source_packet_count == d("1.000000")
    assert report.weak_independent_source_packet_count == d("2.000000")
    assert report.contradiction_packet_count == d("2.000000")
    assert report.severe_contradiction_packet_count == d("1.000000")
    assert report.probability_movement_packet_count == d("1.000000")
    assert report.market_close_urgent_packet_count == d("2.000000")
    assert report.max_latest_update_age_seconds == d("7200.000000")
    assert report.max_contradiction_severity == d("0.800000")
    assert report.max_probability_move_abs == d("0.120000")
    assert report.min_market_close_horizon_seconds == d("10800.000000")
    assert tuple((row.packet_id, row.gap_status) for row in report.rows) == (
        ("gap_packet", "blocked"),
        ("watch_packet", "watch"),
        ("pass_packet", "pass"),
    )
    assert report.rows[0] == gap.ResearchPacketMarketMovingNewsGapV2Row(
        market_id="market_gap_packet",
        packet_id="gap_packet",
        event_category="macro_cpi",
        captured_at=GENERATED_AT - timedelta(minutes=5),
        latest_update_at=GENERATED_AT - timedelta(hours=2),
        latest_update_age_seconds=d("7200.000000"),
        official_source_count=d("0.000000"),
        independent_source_count=d("1.000000"),
        contradiction_severity=d("0.800000"),
        probability_move_abs=d("0.120000"),
        market_close_at=GENERATED_AT + timedelta(hours=3),
        market_close_horizon_seconds=d("10800.000000"),
        gap_status="blocked",
        reason_codes=(
            "research_packet_market_moving_news_gap_v2_latest_update_stale",
            "research_packet_market_moving_news_gap_v2_official_source_missing",
            "research_packet_market_moving_news_gap_v2_weak_independent_sources",
            "research_packet_market_moving_news_gap_v2_contradiction_severe",
            "research_packet_market_moving_news_gap_v2_probability_move_large",
            "research_packet_market_moving_news_gap_v2_market_close_near",
        ),
        derived_validation_digest=report.rows[0].derived_validation_digest,
    )
    assert report.rows[1].reason_codes == (
        "research_packet_market_moving_news_gap_v2_weak_independent_sources",
        "research_packet_market_moving_news_gap_v2_contradiction_elevated",
        "research_packet_market_moving_news_gap_v2_market_close_near",
    )
    assert report.reason_codes == (
        "research_packet_market_moving_news_gap_v2_latest_update_stale",
        "research_packet_market_moving_news_gap_v2_official_source_missing",
        "research_packet_market_moving_news_gap_v2_weak_independent_sources",
        "research_packet_market_moving_news_gap_v2_contradiction_elevated",
        "research_packet_market_moving_news_gap_v2_contradiction_severe",
        "research_packet_market_moving_news_gap_v2_probability_move_large",
        "research_packet_market_moving_news_gap_v2_market_close_near",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)


def test_payload_serializes_decimal_strings_and_rejects_public_tampering() -> None:
    gap = api()
    report = gap.build_research_packet_market_moving_news_gap_v2_report(
        (
            _packet(
                "offset_packet",
                captured_at=datetime(
                    2026,
                    7,
                    6,
                    7,
                    50,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                latest_update_at=datetime(
                    2026,
                    7,
                    6,
                    7,
                    45,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                market_close_at=datetime(
                    2026,
                    7,
                    7,
                    7,
                    30,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
        ),
        config=gap.ResearchPacketMarketMovingNewsGapV2Config(
            urgent_market_close_horizon_seconds=d("3600"),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = gap.research_packet_market_moving_news_gap_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["packet_count"] == "1.000000"
    assert payload["attention_packet_ratio"] == "0.000000"
    assert payload["max_probability_move_abs"] == "0.010000"
    assert payload["rows"][0]["captured_at"] == "2026-07-06T11:50:00+00:00"
    assert payload["rows"][0]["latest_update_age_seconds"] == "900.000000"
    assert payload["rows"][0]["market_close_horizon_seconds"] == "84600.000000"
    assert payload["rows"][0]["official_source_count"] == "1.000000"
    assert payload["rows"][0]["derived_validation_digest"] == (
        report.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _contains_number(payload)
    assert gap.validate_research_packet_market_moving_news_gap_v2_public_payload(payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        gap.validate_research_packet_market_moving_news_gap_v2_public_payload(
            missing_digest,
        )

    tampered_payload = dict(payload)
    tampered_payload["packet_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        gap.research_packet_market_moving_news_gap_v2_payload(tampered_payload)

    numeric_payload = dict(payload)
    numeric_payload["packet_count"] = 1
    with pytest.raises(ValueError, match="decimal strings"):
        gap.validate_research_packet_market_moving_news_gap_v2_public_payload(
            numeric_payload,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload[_unsafe("wal", "let", "_id")] = "redacted"
    with pytest.raises(ValueError, match="public"):
        gap.research_packet_market_moving_news_gap_v2_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["operator_note"] = _unsafe("needs_", "tra", "de", "_desk")
    with pytest.raises(ValueError, match="public"):
        gap.research_packet_market_moving_news_gap_v2_payload(unsafe_value_payload)


def test_frozen_decimal_only_inputs_flags_and_dataclass_tamper_revalidation() -> None:
    gap = api()
    with pytest.raises(ValueError, match="config_version"):
        gap.ResearchPacketMarketMovingNewsGapV2Config(
            config_version=_StringSubclass(
                gap.DEFAULT_RESEARCH_PACKET_MARKET_MOVING_NEWS_GAP_V2_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="max_latest_update_age_seconds"):
        gap.ResearchPacketMarketMovingNewsGapV2Config(max_latest_update_age_seconds=1800)
    with pytest.raises(ValueError, match="min_independent_source_count"):
        gap.ResearchPacketMarketMovingNewsGapV2Config(
            min_independent_source_count=_DecimalSubclass("2"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(gap.ResearchPacketMarketMovingNewsGapV2Config(), paper_only=False)
    with pytest.raises(ValueError, match="market_id"):
        _packet("unsafe_packet", market_id=_unsafe("au", "th", "_reference"))
    with pytest.raises(ValueError, match="official_source_count"):
        _packet("numeric_packet", official_source_count=1)
    with pytest.raises(ValueError, match="probability_move_abs"):
        _packet("float_packet", probability_move_abs=0.1)
    with pytest.raises(ValueError, match="captured_at"):
        _packet("naive_packet", captured_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        gap.build_research_packet_market_moving_news_gap_v2_report(
            (_packet("packet"),),
            config=gap.ResearchPacketMarketMovingNewsGapV2Config(),
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
        gap.research_packet_market_moving_news_gap_v2_payload(tampered_report)


def test_module_scope_is_readonly_report_only_and_has_no_external_surface() -> None:
    module = api()
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
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "connect",
                "execute",
                "open",
                "post",
                "put",
                "request",
                "send",
                "sign",
                "float",
            }

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

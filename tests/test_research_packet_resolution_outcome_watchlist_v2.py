from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_resolution_outcome_watchlist_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _unsafe(*parts: str) -> str:
    return "".join(parts)


def _config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "close_watch_window_seconds": d("86400"),
        "watch_ambiguity_score": d("0.250000"),
        "blocked_ambiguity_score": d("0.750000"),
        "blocked_contradiction_count": d("3"),
        "watch_settlement_lag_seconds": d("900"),
        "blocked_settlement_lag_seconds": d("3600"),
        "min_evidence_completeness_ratio": d("1.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketResolutionOutcomeWatchlistV2Config(**values)


def _market(packet_id: str = "packet_alpha", **overrides: object):
    module = api()
    values: dict[str, object] = {
        "packet_id": packet_id,
        "market_id": f"market_{packet_id}",
        "event_slug": f"event_{packet_id}",
        "close_time": GENERATED_AT + timedelta(days=3),
        "official_outcome_source_count": d("2"),
        "ready_official_outcome_source_count": d("2"),
        "ambiguity_score": d("0.050000"),
        "unresolved_contradiction_count": d("0"),
        "settlement_lag_seconds": d("60"),
        "evidence_completeness_ratio": d("1.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketResolutionOutcomeWatchlistV2Market(**values)


def _report(markets: tuple[object, ...], *, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_packet_resolution_outcome_watchlist_v2_report(
        markets,
        config=_config(),
        generated_at=generated_at,
    )


def _assert_no_float_or_int(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_or_int(item)
    if isinstance(value, list | tuple):
        for item in value:
            _assert_no_float_or_int(item)


def test_phase1_watchlist_scores_resolution_outcome_readiness_dimensions() -> None:
    module = api()
    report = _report(
        (
            _market("ready_packet"),
            _market(
                "watch_packet",
                close_time=GENERATED_AT + timedelta(hours=2),
                ready_official_outcome_source_count=d("1"),
                ambiguity_score=d("0.500000"),
                unresolved_contradiction_count=d("1"),
                settlement_lag_seconds=d("1200"),
                evidence_completeness_ratio=d("0.750000"),
            ),
            _market(
                "blocked_packet",
                close_time=GENERATED_AT - timedelta(minutes=5),
                ready_official_outcome_source_count=d("0"),
                ambiguity_score=d("0.900000"),
                unresolved_contradiction_count=d("3"),
                settlement_lag_seconds=d("4800"),
                evidence_completeness_ratio=d("0.000000"),
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.report_status == "blocked"
    assert report.recommended_next_step == "escalate_phase1_resolution_outcome_review"
    assert report.market_count == d("3.000000")
    assert report.ready_market_count == d("1.000000")
    assert report.watch_market_count == d("1.000000")
    assert report.blocked_market_count == d("1.000000")
    assert report.attention_market_count == d("2.000000")
    assert report.official_source_gap_market_count == d("2.000000")
    assert report.ambiguity_watch_market_count == d("2.000000")
    assert report.contradiction_market_count == d("2.000000")
    assert report.settlement_lag_market_count == d("2.000000")
    assert report.evidence_gap_market_count == d("2.000000")
    assert report.near_close_market_count == d("2.000000")
    assert tuple((row.packet_id, row.phase1_status) for row in report.rows) == (
        ("blocked_packet", "blocked"),
        ("watch_packet", "watch"),
        ("ready_packet", "ready"),
    )
    assert report.rows[0].seconds_until_close == d("-300.000000")
    assert report.rows[0].official_outcome_source_readiness_ratio == d("0.000000")
    assert report.rows[0].reason_codes == (
        "official_outcome_source_absent",
        "resolution_ambiguity_blocked",
        "unresolved_contradictions_blocking",
        "settlement_lag_blocked",
        "resolution_evidence_absent",
        "close_time_elapsed",
    )
    assert report.rows[1].reason_codes == (
        "official_outcome_source_partial",
        "resolution_ambiguity_watch",
        "unresolved_contradictions_present",
        "settlement_lag_watch",
        "resolution_evidence_incomplete",
        "close_time_near",
    )
    assert report.rows[2].reason_codes == (
        "official_outcome_source_ready",
        "resolution_ambiguity_clear",
        "unresolved_contradictions_absent",
        "settlement_lag_clear",
        "resolution_evidence_complete",
        "close_time_clear",
    )
    assert report.reason_code_counts == tuple(
        sorted(report.reason_code_counts, key=lambda item: item.reason_code),
    )
    assert len(report.derived_validation_digest) == 64
    assert len(report.rows[0].derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(type(getattr(report, name)) is Decimal for name in module.REPORT_DECIMAL_FIELDS)


def test_payload_serializes_decimal_strings_and_rejects_public_tampering() -> None:
    module = api()
    report = _report(
        (
            _market(
                "offset_packet",
                close_time=datetime(
                    2026,
                    7,
                    7,
                    10,
                    30,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
        ),
        generated_at=datetime(2026, 7, 7, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.research_packet_resolution_outcome_watchlist_v2_payload(report)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["rows"][0]["close_time"] == "2026-07-07T14:30:00+00:00"
    assert payload["rows"][0]["seconds_until_close"] == "9000.000000"
    assert payload["rows"][0]["official_outcome_source_readiness_ratio"] == "1.000000"
    assert payload["rows"][0]["derived_validation_digest"] == report.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_or_int(payload)

    validated = module.validate_research_packet_resolution_outcome_watchlist_v2_public_payload(
        payload,
    )
    assert validated == payload

    tampered_report_payload = dict(payload)
    tampered_report_payload["market_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_packet_resolution_outcome_watchlist_v2_public_payload(
            tampered_report_payload,
        )

    tampered_row_payload = dict(payload)
    tampered_row_payload["rows"] = [dict(payload["rows"][0])]
    tampered_row_payload["rows"][0]["phase1_status"] = "blocked"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_packet_resolution_outcome_watchlist_v2_public_payload(
            tampered_row_payload,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload[_unsafe("wal", "let", "_id")] = "redacted"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.validate_research_packet_resolution_outcome_watchlist_v2_public_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["operator_note"] = _unsafe("place_", "or", "der")
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_research_packet_resolution_outcome_watchlist_v2_public_payload(
            unsafe_value_payload,
        )


def test_frozen_decimal_exact_flags_and_constructor_validation() -> None:
    module = api()

    with pytest.raises(ValueError, match="close_watch_window_seconds must be a Decimal"):
        _config(close_watch_window_seconds=86400)

    with pytest.raises(ValueError, match="watch_ambiguity_score must be exactly Decimal"):
        _config(watch_ambiguity_score=_DecimalSubclass("0.250000"))

    with pytest.raises(ValueError, match="close_time must be exactly datetime"):
        _market(
            "datetime_subclass_packet",
            close_time=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="close_time must be timezone-aware"):
        _market("naive_packet", close_time=datetime(2026, 7, 7, 12, 0))

    with pytest.raises(ValueError, match="ready_official_outcome_source_count"):
        _market(
            "source_count_packet",
            official_outcome_source_count=d("1"),
            ready_official_outcome_source_count=d("2"),
        )

    with pytest.raises(ValueError, match="evidence_completeness_ratio"):
        _market("bad_ratio_packet", evidence_completeness_ratio=d("1.000001"))

    with pytest.raises(ValueError, match="packet_id values must be unique"):
        _report((_market("duplicate_packet"), _market("duplicate_packet")))

    market = _market("frozen_packet")
    with pytest.raises(FrozenInstanceError):
        market.packet_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(market, paper_only=False)

    report = _report((_market("valid_packet"),))
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="report_only must be True"):
        module.ResearchPacketResolutionOutcomeWatchlistV2Config(report_only=False)


def test_deterministic_sorting_counts_and_digests_for_unsorted_inputs() -> None:
    markets = (
        _market("packet_b", close_time=GENERATED_AT + timedelta(minutes=20)),
        _market("packet_c", ambiguity_score=d("0.800000")),
        _market("packet_a", close_time=GENERATED_AT + timedelta(minutes=20)),
    )

    first = _report(markets)
    second = _report(tuple(reversed(markets)))

    assert first == second
    assert tuple(row.packet_id for row in first.rows) == (
        "packet_c",
        "packet_a",
        "packet_b",
    )
    assert first.derived_validation_digest == second.derived_validation_digest
    assert tuple((item.reason_code, item.market_count) for item in first.reason_code_counts) == tuple(
        (item.reason_code, item.market_count) for item in second.reason_code_counts
    )


def test_static_scope_excludes_io_network_auth_order_trading_or_db_surfaces() -> None:
    module = api()
    source_path = Path(module.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    banned_import_roots = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    banned_call_names = {
        "connect",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "remove",
        "request",
        "send",
        "submit",
        "trade",
        "unlink",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(banned_import_roots)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names

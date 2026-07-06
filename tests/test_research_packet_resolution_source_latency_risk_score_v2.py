from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_packet_resolution_source_latency_risk_score_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_resolution_source_latency_risk_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observed_at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 7, 6, hour, minute, tzinfo=UTC)


def observation(**overrides: object):
    module = api()
    values = {
        "packet_id": "packet_fast",
        "resolution_source_name": "official_press_room",
        "source_kind": "official",
        "resolution_event_at": observed_at(11, 30),
        "source_last_refreshed_at": observed_at(11, 50),
        "checked_at": observed_at(12),
    }
    values.update(overrides)
    return module.ResearchPacketResolutionSourceLatencyObservationV2(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop("generated_at", observed_at(12))
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            observation(packet_id="packet_fast"),
            observation(
                packet_id="packet_watch",
                resolution_source_name="secondary_status_page",
                source_kind="secondary",
                resolution_event_at=observed_at(10),
                source_last_refreshed_at=observed_at(11),
            ),
            observation(
                packet_id="packet_stale",
                resolution_event_at=observed_at(9),
                source_last_refreshed_at=observed_at(6),
            ),
        )
    return module.build_research_packet_resolution_source_latency_risk_score_v2(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_resolution_source_latency_risk_rollup_and_ranking() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.report_status == "blocked"
    assert report.source_count == d("3")
    assert report.official_source_count == d("2")
    assert report.stale_official_source_count == d("1")
    assert report.fast_refresh_source_count == d("1")
    assert report.average_resolution_source_latency_risk_score == d("0.508333")
    assert report.top_resolution_source_latency_risk_score == d("1.000000")
    assert report.bottom_resolution_source_latency_risk_score == d("0.025000")
    assert report.reason_codes == (
        "resolution_source_latency_risk_report_blocked_rows",
        "official_source_stale_penalty_rows",
        "fast_refresh_boost_rows",
    )

    assert tuple(row.packet_id for row in report.rows) == (
        "packet_stale",
        "packet_watch",
        "packet_fast",
    )
    assert tuple(row.rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.resolution_source_latency_risk_score for row in report.rows) == (
        d("1.000000"),
        d("0.500000"),
        d("0.025000"),
    )
    assert tuple(row.risk_status for row in report.rows) == (
        "blocked",
        "watch",
        "pass",
    )


def test_stale_official_source_penalty_blocks_old_resolution_source() -> None:
    report = build_report(
        observation(
            packet_id="packet_stale",
            resolution_event_at=observed_at(9),
            source_last_refreshed_at=observed_at(6),
        ),
    )
    row = report.rows[0]

    assert row.source_latency_minutes == d("180.000000")
    assert row.source_refresh_age_minutes == d("360.000000")
    assert row.base_latency_risk_score == d("0.750000")
    assert row.official_source_stale_penalty_score == d("0.250000")
    assert row.fast_refresh_boost_score == d("0.000000")
    assert row.resolution_source_latency_risk_score == d("1.000000")
    assert row.risk_status == "blocked"
    assert "official_source_stale_penalty" in row.reason_codes


def test_fast_refresh_boost_reduces_recent_official_source_risk() -> None:
    report = build_report(observation(packet_id="packet_fast"))
    row = report.rows[0]

    assert row.source_latency_minutes == d("30.000000")
    assert row.source_refresh_age_minutes == d("10.000000")
    assert row.base_latency_risk_score == d("0.125000")
    assert row.fast_refresh_boost_score == d("0.100000")
    assert row.official_source_stale_penalty_score == d("0.000000")
    assert row.resolution_source_latency_risk_score == d("0.025000")
    assert row.risk_status == "pass"
    assert "fast_refresh_boost_applied" in row.reason_codes


def test_payload_serializes_decimal_values_as_strings() -> None:
    report = build_report()
    payload = report.payload

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["source_count"] == "3"
    assert payload["average_resolution_source_latency_risk_score"] == "0.508333"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["source_latency_minutes"] == "180.000000"
    assert payload["rows"][0]["resolution_source_latency_risk_score"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.ResearchPacketResolutionSourceLatencyRiskScoreV2Config()
    sample = observation()
    report = build_report(sample)
    row = report.rows[0]
    decimal_fields = {
        "max_latency_minutes",
        "official_stale_after_minutes",
        "fast_refresh_window_minutes",
        "official_source_stale_penalty_score",
        "fast_refresh_boost_score",
        "pass_risk_ceiling",
        "watch_risk_ceiling",
        "rank",
        "source_latency_minutes",
        "source_refresh_age_minutes",
        "base_latency_risk_score",
        "resolution_source_latency_risk_score",
        "source_count",
        "official_source_count",
        "stale_official_source_count",
        "fast_refresh_source_count",
        "average_resolution_source_latency_risk_score",
        "top_resolution_source_latency_risk_score",
        "bottom_resolution_source_latency_risk_score",
    }

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in decimal_fields:
                assert type(value) is Decimal


def test_config_validation_rejects_non_decimal_values_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="max_latency_minutes must be exactly Decimal"):
        module.ResearchPacketResolutionSourceLatencyRiskScoreV2Config(
            max_latency_minutes=240,
        )
    with pytest.raises(
        ValueError,
        match="official_stale_after_minutes must be exactly Decimal",
    ):
        module.ResearchPacketResolutionSourceLatencyRiskScoreV2Config(
            official_stale_after_minutes=_DecimalSubclass("120"),
        )
    with pytest.raises(ValueError, match="watch_risk_ceiling must not be below"):
        module.ResearchPacketResolutionSourceLatencyRiskScoreV2Config(
            pass_risk_ceiling=d("0.500000"),
            watch_risk_ceiling=d("0.250000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchPacketResolutionSourceLatencyRiskScoreV2Config(
            paper_only=False,
        )


def test_build_validation_rejects_wrong_types_and_bad_times() -> None:
    module = api()

    with pytest.raises(ValueError, match="observations must be an iterable"):
        module.build_research_packet_resolution_source_latency_risk_score_v2(
            object(),
            generated_at=observed_at(12),
        )
    with pytest.raises(
        ValueError,
        match="items must be ResearchPacketResolutionSourceLatencyObservationV2",
    ):
        module.build_research_packet_resolution_source_latency_risk_score_v2(
            [object()],
            generated_at=observed_at(12),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_packet_resolution_source_latency_risk_score_v2(
            [observation()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="checked_at must be on or after"):
        observation(checked_at=observed_at(11), resolution_event_at=observed_at(12))


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, config_version="changed")


def test_rejects_unsafe_public_payload_keys_and_values() -> None:
    module = api()
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

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public payload"):
            observation(packet_id=f"{term}_packet")
        with pytest.raises(ValueError, match="unsafe public payload"):
            module._reject_unsafe_public_payload("example", {f"{term}_field": "ok"})
        with pytest.raises(ValueError, match="unsafe public payload"):
            module._reject_unsafe_public_payload("example", {"safe_field": term})


def test_report_revalidates_row_sort_counts_reason_codes_and_digest() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by risk and rank"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="source counts must match rows"):
        replace(report, source_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match report_status"):
        replace(
            report,
            reason_codes=("resolution_source_latency_risk_report_passed",),
        )


def test_module_has_no_unsafe_trading_or_persistence_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])

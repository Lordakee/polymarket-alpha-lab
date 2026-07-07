from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_official_resolution_monitor_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "required_official_source_count": d("1.000000"),
        "required_rule_criteria_count": d("3.000000"),
        "max_official_update_age_seconds": d("3600.000000"),
        "max_contradiction_count": d("0.000000"),
        "required_evidence_chain_link_count": d("4.000000"),
        "max_seconds_until_settlement": d("86400.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketOfficialResolutionMonitorV2Config(**values)


def packet(packet_id: str = "packet-ready", **overrides: object):
    module = api()
    values = {
        "packet_id": packet_id,
        "market_id": f"market-{packet_id}",
        "official_source_count": d("1.000000"),
        "rule_criteria_covered_count": d("3.000000"),
        "last_official_update_age_seconds": d("600.000000"),
        "contradiction_count": d("0.000000"),
        "evidence_chain_complete_count": d("4.000000"),
        "seconds_until_settlement": d("3600.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketOfficialResolutionMonitorV2Input(**values)


def report(*packets: object, **overrides: object):
    return api().build_research_packet_official_resolution_monitor_v2_report(
        packets,
        config=config(**overrides),
        generated_at=GENERATED_AT,
    )


def assert_no_public_number(value: Any) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise AssertionError("public numeric value found")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_number(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_public_number(item)


def assert_dataclass_numbers_are_decimal(value: object) -> None:
    fields = getattr(value, "__dataclass_fields__", {})
    for field_name in fields:
        item = getattr(value, field_name)
        if type(item) in (int, float):
            raise AssertionError(f"{field_name} is not Decimal")
        if type(item) is tuple:
            for row in item:
                assert_dataclass_numbers_are_decimal(row)


def test_official_resolution_monitor_scores_all_readiness_dimensions() -> None:
    ready = packet("packet-ready")
    watch = packet(
        "packet-watch",
        seconds_until_settlement=d("172800.000000"),
    )
    blocked = packet(
        "packet-blocked",
        official_source_count=d("0.000000"),
        rule_criteria_covered_count=d("2.000000"),
        last_official_update_age_seconds=d("7200.000000"),
        contradiction_count=d("1.000000"),
        evidence_chain_complete_count=d("3.000000"),
    )

    first = report(ready, watch, blocked)
    second = report(blocked, watch, ready)

    assert first == second
    assert first.status == "blocked"
    assert first.packet_count == d("3.000000")
    assert first.ready_count == d("1.000000")
    assert first.watch_count == d("1.000000")
    assert first.blocked_count == d("1.000000")
    assert first.official_source_gap_count == d("1.000000")
    assert first.rule_criteria_gap_count == d("1.000000")
    assert first.stale_update_count == d("1.000000")
    assert first.contradiction_packet_count == d("1.000000")
    assert first.evidence_chain_gap_count == d("1.000000")
    assert first.settlement_proximity_gap_count == d("1.000000")
    assert tuple((row.packet_id, row.readiness_status) for row in first.rows) == (
        ("packet-blocked", "blocked"),
        ("packet-watch", "watch"),
        ("packet-ready", "ready"),
    )
    assert first.rows[0].gap_count == d("5.000000")
    assert first.rows[0].reason_codes == (
        "official_source_missing",
        "rule_criteria_coverage_gap",
        "official_update_stale",
        "official_resolution_contradictions_present",
        "evidence_chain_incomplete",
    )
    assert first.rows[1].reason_codes == ("settlement_proximity_not_met",)
    assert first.rows[2].reason_codes == ("official_resolution_ready",)
    assert first.reason_codes == (
        "official_source_missing",
        "rule_criteria_coverage_gap",
        "official_update_stale",
        "official_resolution_contradictions_present",
        "evidence_chain_incomplete",
        "settlement_proximity_not_met",
    )
    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)
    assert_dataclass_numbers_are_decimal(first)


def test_payload_serializes_decimal_strings_and_revalidates_digest() -> None:
    module = api()
    readiness_report = report(packet("packet-json"))

    payload = module.research_packet_official_resolution_monitor_v2_payload(
        readiness_report,
    )

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["packet_count"] == "1.000000"
    assert payload["ready_count"] == "1.000000"
    assert payload["rows"][0]["official_source_count"] == "1.000000"
    assert payload["rows"][0]["required_rule_criteria_count"] == "3.000000"
    assert payload["rows"][0]["readiness_status"] == "ready"
    assert payload["rows"][0]["derived_validation_digest"] == (
        readiness_report.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == readiness_report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_number(payload)
    assert module.research_packet_official_resolution_monitor_v2_payload(payload) == payload

    tampered = dict(payload)
    tampered["ready_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_official_resolution_monitor_v2_payload(tampered)


def test_frozen_hard_flags_and_decimal_only_inputs_are_enforced() -> None:
    module = api()
    readiness_report = report(packet())

    for value in (config(), packet(), readiness_report.rows[0], readiness_report):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(packet(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(readiness_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="official_source_count"):
        module.ResearchPacketOfficialResolutionMonitorV2Input(
            packet_id="packet-int",
            market_id="market-int",
            official_source_count=1,
            rule_criteria_covered_count=d("3.000000"),
            last_official_update_age_seconds=d("600.000000"),
            contradiction_count=d("0.000000"),
            evidence_chain_complete_count=d("4.000000"),
            seconds_until_settlement=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="required_rule_criteria_count"):
        config(required_rule_criteria_count=d("1.500000"))


def test_dataclass_tampering_is_rejected_by_digest_validation() -> None:
    module = api()
    readiness_report = report(packet("packet-tamper"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(readiness_report.rows[0], official_source_count=d("2.000000"))

    tampered_report = report(packet("packet-report-tamper"))
    object.__setattr__(tampered_report, "ready_count", d("2.000000"))
    with pytest.raises(ValueError, match="ready_count|derived_validation_digest"):
        module.research_packet_official_resolution_monitor_v2_payload(tampered_report)


def test_empty_input_is_blocked_with_deterministic_reason() -> None:
    empty_report = report()

    assert empty_report.status == "blocked"
    assert empty_report.packet_count == d("0.000000")
    assert empty_report.reason_codes == ("official_resolution_monitor_no_packets",)
    assert empty_report.rows == ()


def test_module_has_no_external_or_runtime_side_effect_surface() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])

    assert imported_roots.isdisjoint(
        {
            "asyncio",
            "httpx",
            "pathlib",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "urllib",
            "web3",
        },
    )
    assert not hasattr(module, "client")
    assert not hasattr(module, "session")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "print", "__import__"}
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)

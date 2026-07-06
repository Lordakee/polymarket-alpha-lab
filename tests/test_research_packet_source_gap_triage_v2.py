from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.research_packet_source_gap_triage_v2",
    )


def gap_input(**overrides: Any):
    values: dict[str, Any] = {
        "packet_ref": "packet-alpha",
        "question_ref": "question-alpha",
        "specialist_ref": "specialist-alpha",
        "official_anchor_count": d("1.000000"),
        "source_family_count": d("3.000000"),
        "freshest_evidence_age_hours": d("2.000000"),
        "contradiction_severity_score": d("0.000000"),
        "unattributed_probability_move": d("0.000000"),
        "hours_to_resolution": d("200.000000"),
        "specialist_uncertainty_score": d("0.000000"),
    }
    values.update(overrides)
    return api().ResearchPacketSourceGapTriageV2Input(**values)


def build(*rows: object):
    module = api()
    return module.build_research_packet_source_gap_triage_v2_report(
        rows or (gap_input(),),
        config=module.ResearchPacketSourceGapTriageV2Config(),
    )


def assert_payload_has_no_numeric_values(value: Any) -> None:
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_numeric_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_has_no_numeric_values(item)


def test_prioritizes_source_gaps_from_all_decimal_triage_drivers() -> None:
    module = api()
    report = build(
        gap_input(packet_ref="packet-clear"),
        gap_input(
            packet_ref="packet-urgent",
            official_anchor_count=d("0.000000"),
            source_family_count=d("1.000000"),
            freshest_evidence_age_hours=d("72.000000"),
            contradiction_severity_score=d("0.800000"),
            unattributed_probability_move=d("0.600000"),
            hours_to_resolution=d("12.000000"),
            specialist_uncertainty_score=d("0.900000"),
        ),
        gap_input(
            packet_ref="packet-watch",
            official_anchor_count=d("1.000000"),
            source_family_count=d("2.000000"),
            freshest_evidence_age_hours=d("39.000000"),
            contradiction_severity_score=d("0.100000"),
            unattributed_probability_move=d("0.200000"),
            hours_to_resolution=d("96.000000"),
            specialist_uncertainty_score=d("0.400000"),
        ),
    )

    assert report == module.ResearchPacketSourceGapTriageV2Report(
        config_version=module.DEFAULT_RESEARCH_PACKET_SOURCE_GAP_TRIAGE_V2_CONFIG_VERSION,
        status="blocked",
        recommended_next_step="collect_source_gap_evidence_for_paper_report",
        input_count=d("3.000000"),
        blocked_count=d("1.000000"),
        watch_count=d("1.000000"),
        pass_count=d("1.000000"),
        missing_official_anchor_count=d("1.000000"),
        weak_source_family_independence_count=d("2.000000"),
        stale_evidence_count=d("2.000000"),
        contradiction_severity_count=d("2.000000"),
        unattributed_probability_move_count=d("2.000000"),
        near_resolution_horizon_count=d("2.000000"),
        specialist_uncertainty_count=d("2.000000"),
        highest_priority_score=d("0.975000"),
        rows=report.rows,
        reason_codes=(
            "source_gap_triage_status_blocked",
            "missing_official_anchor",
            "weak_source_family_independence",
            "stale_evidence",
            "contradiction_severity",
            "unattributed_probability_move",
            "near_resolution_horizon",
            "specialist_uncertainty",
        ),
        derived_validation_digest=report.derived_validation_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert tuple(row.packet_ref for row in report.rows) == (
        "packet-urgent",
        "packet-watch",
        "packet-clear",
    )
    urgent, watch, clear = report.rows
    assert urgent.priority_rank == d("1.000000")
    assert urgent.priority_score == d("0.975000")
    assert urgent.source_family_independence_gap_score == d("0.666667")
    assert urgent.stale_evidence_score == d("1.000000")
    assert urgent.resolution_horizon_score == d("1.000000")
    assert urgent.triage_status == "blocked"
    assert urgent.recommended_research_action == "source_gap_research_first"
    assert urgent.reason_codes == (
        "source_gap_triage_status_blocked",
        "missing_official_anchor",
        "weak_source_family_independence",
        "stale_evidence",
        "contradiction_severity",
        "unattributed_probability_move",
        "near_resolution_horizon",
        "specialist_uncertainty",
    )
    assert watch.priority_rank == d("2.000000")
    assert watch.priority_score == d("0.341667")
    assert watch.triage_status == "watch"
    assert clear.priority_rank == d("3.000000")
    assert clear.priority_score == d("0.000000")
    assert clear.triage_status == "pass"
    for row in report.rows:
        assert type(row.priority_score) is Decimal
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True


def test_empty_report_is_blocked_readonly_and_decimal_zeroed() -> None:
    report = build()
    empty = api().build_research_packet_source_gap_triage_v2_report(
        (),
        config=api().ResearchPacketSourceGapTriageV2Config(),
    )

    assert report.input_count == d("1.000000")
    assert empty.status == "blocked"
    assert empty.recommended_next_step == "collect_source_gap_evidence_for_paper_report"
    assert empty.input_count == d("0.000000")
    assert empty.highest_priority_score == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("source_gap_triage_no_inputs",)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_public_payload_serializes_decimal_strings_and_rejects_tampering() -> None:
    module = api()
    report = build(
        gap_input(
            official_anchor_count=d("0.000000"),
            source_family_count=d("1.000000"),
            freshest_evidence_age_hours=d("72.000000"),
            contradiction_severity_score=d("0.800000"),
            unattributed_probability_move=d("0.600000"),
            hours_to_resolution=d("12.000000"),
            specialist_uncertainty_score=d("0.900000"),
        ),
    )

    payload = module.research_packet_source_gap_triage_v2_payload(report)

    assert payload == report.payload
    assert payload["input_count"] == "1.000000"
    assert payload["highest_priority_score"] == "0.975000"
    assert payload["rows"][0]["priority_score"] == "0.975000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])
    assert_payload_has_no_numeric_values(payload)

    restored = module.ResearchPacketSourceGapTriageV2Report.from_payload(payload)
    assert restored == report

    tampered = dict(payload)
    tampered["highest_priority_score"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.ResearchPacketSourceGapTriageV2Report.from_payload(tampered)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, status="watch")
    mutated = build(gap_input())
    object.__setattr__(mutated.rows[0], "priority_score", d("0.500000"))
    with pytest.raises(ValueError, match="priority_score must match"):
        module.research_packet_source_gap_triage_v2_payload(mutated)


def test_rejects_unsafe_public_keys_values_bad_flags_and_wrong_types() -> None:
    module = api()
    subject = gap_input()
    report = build(subject)

    class InputSubclass(module.ResearchPacketSourceGapTriageV2Input):
        pass

    class ReportSubclass(module.ResearchPacketSourceGapTriageV2Report):
        pass

    with pytest.raises(FrozenInstanceError):
        subject.packet_ref = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="subject must be"):
        InputSubclass(**subject.__dict__)
    with pytest.raises(ValueError, match="report must be"):
        ReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="official_anchor_count must be a Decimal"):
        gap_input(official_anchor_count="0.000000")
    with pytest.raises(ValueError, match="source_family_count must be nonnegative"):
        gap_input(source_family_count=d("-1.000000"))
    with pytest.raises(ValueError, match="contradiction_severity_score must be between"):
        gap_input(contradiction_severity_score=d("1.000001"))
    with pytest.raises(ValueError, match="specialist_uncertainty_score must not exceed six"):
        gap_input(specialist_uncertainty_score=d("0.1234567"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        gap_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_packet_source_gap_triage_v2_report((), config=object())
    with pytest.raises(ValueError, match="rows must be"):
        module.build_research_packet_source_gap_triage_v2_report(object())
    with pytest.raises(ValueError, match="report must be"):
        module.research_packet_source_gap_triage_v2_payload(object())

    for forbidden_value in (
        "live surface",
        "auth callback",
        "wallet field",
        "order detail",
        "network call",
        "database row",
        "persist record",
        "signing request",
        "mutation path",
        "buy button",
        "sell action",
        "trade route",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            gap_input(question_ref=forbidden_value)

    for forbidden_key in (
        "live_ref",
        "auth_ref",
        "wallet_ref",
        "order_ref",
        "network_ref",
        "database_ref",
        "persist_ref",
        "signing_ref",
        "mutation_ref",
        "buy_ref",
        "sell_ref",
        "trade_ref",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            module._reject_unsafe_public_payload("payload", {forbidden_key: "safe"})


def test_module_is_isolated_decimal_only_report_only_and_unwired() -> None:
    module = api()
    source = inspect.getsource(module)

    assert module.ResearchPacketSourceGapTriageV2Config.__dataclass_params__.frozen
    assert module.ResearchPacketSourceGapTriageV2Input.__dataclass_params__.frozen
    assert module.ResearchPacketSourceGapTriageV2Row.__dataclass_params__.frozen
    assert module.ResearchPacketSourceGapTriageV2Report.__dataclass_params__.frozen
    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_GAP_TRIAGE_V2_CONFIG_VERSION",
        "REASON_CODES",
        "ResearchPacketSourceGapTriageV2Config",
        "ResearchPacketSourceGapTriageV2Input",
        "ResearchPacketSourceGapTriageV2Report",
        "ResearchPacketSourceGapTriageV2Row",
        "STATUSES",
        "build_research_packet_source_gap_triage_v2_report",
        "research_packet_source_gap_triage_v2_payload",
    )

    forbidden_import_roots = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    )
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "create_order",
        "open",
        "place_order",
        "read_text",
        "submit_order",
        "write_text",
    }

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert {name.split(".", 1)[0] for name in imported_modules}.isdisjoint(
        forbidden_import_roots,
    )
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }

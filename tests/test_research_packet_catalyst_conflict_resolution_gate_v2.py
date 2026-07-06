from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.research_packet_catalyst_conflict_resolution_gate_v2",
    )


def catalyst(**overrides: Any):
    values: dict[str, Any] = {
        "packet_ref": "packet-alpha",
        "question_ref": "question-alpha",
        "catalyst_ref": "catalyst-alpha",
        "supporting_source_count": d("3.000000"),
        "contradicting_source_count": d("1.000000"),
        "independent_source_count": d("3.000000"),
        "resolved_contradiction_count": d("1.000000"),
        "unresolved_contradiction_count": ZERO,
        "reason_codes": ("source_packet_input",),
    }
    values.update(overrides)
    return api().ResearchPacketCatalystConflictResolutionGateV2Input(**values)


def build(*rows: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_packet_catalyst_conflict_resolution_gate_v2_report(
        rows,
        config=(
            cfg
            if cfg is not None
            else module.ResearchPacketCatalystConflictResolutionGateV2Config()
        ),
        generated_at=generated_at,
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


def test_catalyst_conflict_scoring_unresolved_penalties_and_independent_boosts() -> None:
    module = api()
    report = build(
        catalyst(
            packet_ref="packet-pass",
            question_ref="question-pass",
            catalyst_ref="catalyst-pass",
            supporting_source_count=d("3.000000"),
            contradicting_source_count=d("1.000000"),
            independent_source_count=d("3.000000"),
            resolved_contradiction_count=d("1.000000"),
            unresolved_contradiction_count=ZERO,
        ),
        catalyst(
            packet_ref="packet-watch",
            question_ref="question-watch",
            catalyst_ref="catalyst-watch",
            supporting_source_count=d("2.000000"),
            contradicting_source_count=d("2.000000"),
            independent_source_count=d("1.000000"),
            resolved_contradiction_count=d("1.000000"),
            unresolved_contradiction_count=d("1.000000"),
        ),
        catalyst(
            packet_ref="packet-block",
            question_ref="question-block",
            catalyst_ref="catalyst-block",
            supporting_source_count=d("1.000000"),
            contradicting_source_count=d("2.000000"),
            independent_source_count=ZERO,
            resolved_contradiction_count=ZERO,
            unresolved_contradiction_count=d("3.000000"),
        ),
    )

    assert report == module.ResearchPacketCatalystConflictResolutionGateV2Report(
        generated_at=GENERATED_AT,
        config_version=(
            module.DEFAULT_RESEARCH_PACKET_CATALYST_CONFLICT_RESOLUTION_GATE_V2_CONFIG_VERSION
        ),
        status="blocked",
        recommended_next_step="resolve_catalyst_conflicts_before_paper_report",
        input_count=d("3.000000"),
        blocked_count=d("1.000000"),
        watch_count=d("1.000000"),
        pass_count=d("1.000000"),
        unresolved_contradiction_count=d("4.000000"),
        independent_source_boost_count=d("1.000000"),
        highest_conflict_risk_score=d("0.800000"),
        average_conflict_risk_score=d("0.383333"),
        max_unresolved_contradiction_count=d("3.000000"),
        rows=report.rows,
        reason_codes=(
            "catalyst_conflict_resolution_gate_status_blocked",
            "unresolved_contradiction_watch",
            "unresolved_contradiction_blocked",
            "contradicting_source_pressure_watch",
            "contradicting_source_pressure_blocked",
            "weak_independent_source_quorum",
            "independent_source_boost_applied",
        ),
        derived_validation_digest=report.derived_validation_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert tuple(row.conflict_status for row in report.rows) == ("blocked", "watch", "pass")

    blocked, watched, passed = report.rows
    assert blocked.packet_ref == "packet-block"
    assert blocked.total_source_count == d("3.000000")
    assert blocked.contradiction_ratio == d("0.666667")
    assert blocked.unresolved_contradiction_ratio == d("1.000000")
    assert blocked.independent_source_ratio == ZERO
    assert blocked.independent_source_boost == ZERO
    assert blocked.conflict_risk_score == d("0.800000")
    assert blocked.recommended_research_action == "resolve_catalyst_conflict_before_paper_report"
    assert blocked.reason_codes == (
        "source_packet_input",
        "catalyst_conflict_resolution_gate_status_blocked",
        "unresolved_contradiction_blocked",
        "contradicting_source_pressure_blocked",
        "weak_independent_source_quorum",
    )

    assert watched.conflict_status == "watch"
    assert watched.contradiction_ratio == d("0.500000")
    assert watched.unresolved_contradiction_ratio == d("0.500000")
    assert watched.independent_source_ratio == d("0.250000")
    assert watched.conflict_risk_score == d("0.400000")
    assert watched.reason_codes == (
        "source_packet_input",
        "catalyst_conflict_resolution_gate_status_watch",
        "unresolved_contradiction_watch",
        "contradicting_source_pressure_watch",
        "weak_independent_source_quorum",
    )

    assert passed.conflict_status == "pass"
    assert passed.contradiction_ratio == d("0.250000")
    assert passed.independent_source_ratio == d("0.750000")
    assert passed.independent_source_boost == d("0.200000")
    assert passed.conflict_risk_score == ZERO
    assert passed.reason_codes == (
        "source_packet_input",
        "catalyst_conflict_resolution_gate_status_pass",
        "independent_source_boost_applied",
    )


def test_serialization_decimal_strings_and_digest_tamper_rejection() -> None:
    module = api()
    report = build(catalyst())
    payload = module.research_packet_catalyst_conflict_resolution_gate_v2_payload(report)

    assert payload == report.payload
    assert payload["input_count"] == "1.000000"
    assert payload["highest_conflict_risk_score"] == "0.000000"
    assert payload["rows"][0]["independent_source_boost"] == "0.200000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])
    assert_payload_has_no_numeric_values(payload)

    restored = module.ResearchPacketCatalystConflictResolutionGateV2Report.from_payload(payload)
    assert restored == report

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)
    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="status must match rows"):
        module.ResearchPacketCatalystConflictResolutionGateV2Report.from_payload(tampered)
    tampered_digest = dict(payload)
    tampered_digest["generated_at"] = datetime(2026, 7, 6, 19, 0, tzinfo=UTC).isoformat()
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.ResearchPacketCatalystConflictResolutionGateV2Report.from_payload(
            tampered_digest,
        )
    mutated = build(catalyst())
    object.__setattr__(mutated.rows[0], "conflict_risk_score", d("0.500000"))
    with pytest.raises(ValueError, match="conflict_risk_score must match"):
        module.research_packet_catalyst_conflict_resolution_gate_v2_payload(mutated)


def test_frozen_dataclasses_hard_flags_and_decimal_only_public_inputs() -> None:
    module = api()
    subject = catalyst()
    report = build(subject)

    class InputSubclass(module.ResearchPacketCatalystConflictResolutionGateV2Input):
        pass

    class ReportSubclass(module.ResearchPacketCatalystConflictResolutionGateV2Report):
        pass

    assert module.ResearchPacketCatalystConflictResolutionGateV2Config.__dataclass_params__.frozen
    assert module.ResearchPacketCatalystConflictResolutionGateV2Input.__dataclass_params__.frozen
    assert module.ResearchPacketCatalystConflictResolutionGateV2Row.__dataclass_params__.frozen
    assert module.ResearchPacketCatalystConflictResolutionGateV2Report.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        subject.packet_ref = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="subject must be"):
        InputSubclass(**subject.__dict__)
    with pytest.raises(ValueError, match="report must be"):
        ReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="supporting_source_count must be a Decimal"):
        catalyst(supporting_source_count="3.000000")
    with pytest.raises(ValueError, match="unresolved_contradiction_count must be integral"):
        catalyst(unresolved_contradiction_count=d("1.500000"))
    with pytest.raises(ValueError, match="independent_source_count must be at most total_source_count"):
        catalyst(independent_source_count=d("5.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        catalyst(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_packet_catalyst_conflict_resolution_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="subjects must be"):
        module.build_research_packet_catalyst_conflict_resolution_gate_v2_report(
            object(),
            config=module.ResearchPacketCatalystConflictResolutionGateV2Config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report must be"):
        module.research_packet_catalyst_conflict_resolution_gate_v2_payload(object())


def test_unsafe_payload_rejection_for_keys_and_values() -> None:
    module = api()
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
            catalyst(packet_ref=forbidden_value)

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


def test_module_has_no_unsafe_runtime_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_CATALYST_CONFLICT_RESOLUTION_GATE_V2_CONFIG_VERSION",
        "REASON_CODES",
        "ResearchPacketCatalystConflictResolutionGateV2Config",
        "ResearchPacketCatalystConflictResolutionGateV2Input",
        "ResearchPacketCatalystConflictResolutionGateV2Report",
        "ResearchPacketCatalystConflictResolutionGateV2Row",
        "STATUSES",
        "build_research_packet_catalyst_conflict_resolution_gate_v2_report",
        "research_packet_catalyst_conflict_resolution_gate_v2_payload",
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

    assert not any(
        imported_module.split(".")[0] in forbidden_import_roots
        for imported_module in imported_modules
    )

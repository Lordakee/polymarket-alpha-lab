from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.specialist_team_cross_domain_handoff_packet_report as api
from polymarket_alpha_lab.specialist_team_cross_domain_handoff_packet_report import (
    SpecialistTeamCrossDomainHandoffPacketInput,
    SpecialistTeamCrossDomainHandoffPacketReport,
    build_specialist_team_cross_domain_handoff_packet_report,
    specialist_team_cross_domain_handoff_packet_report_digest,
    specialist_team_cross_domain_handoff_packet_report_to_payload,
    validate_specialist_team_cross_domain_handoff_packet_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_cross_domain_handoff_packet_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def handoff_input(
    **overrides: object,
) -> SpecialistTeamCrossDomainHandoffPacketInput:
    values = {
        "primary_team_id": "market-research",
        "secondary_team_id": "policy-review",
        "handoff_reason_count": d("2.000000"),
        "evidence_digest_present": True,
        "recipient_capacity_score": d("0.750000"),
        "deadline_hours": d("24.000000"),
    }
    values.update(overrides)
    return SpecialistTeamCrossDomainHandoffPacketInput(**values)


def report(**overrides: object) -> SpecialistTeamCrossDomainHandoffPacketReport:
    return build_specialist_team_cross_domain_handoff_packet_report(
        handoff_input(**overrides),
    )


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_ready_handoff_emits_readonly_public_payload_and_digest() -> None:
    first = report()
    second = report()

    assert type(first) is SpecialistTeamCrossDomainHandoffPacketReport
    assert is_dataclass(first)
    assert first.handoff_status == "ready"
    assert first.reason_codes == (
        "specialist_team_cross_domain_handoff_ready",
    )
    assert first.manual_next_step == "send_public_handoff_packet"
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = specialist_team_cross_domain_handoff_packet_report_to_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "primary_team_id": "market-research",
        "secondary_team_id": "policy-review",
        "handoff_reason_count": "2.000000",
        "evidence_digest_present": True,
        "recipient_capacity_score": "0.750000",
        "deadline_hours": "24.000000",
        "handoff_status": "ready",
        "reason_codes": [
            "specialist_team_cross_domain_handoff_ready",
        ],
        "manual_next_step": "send_public_handoff_packet",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert first.payload_digest == second.payload_digest
    assert specialist_team_cross_domain_handoff_packet_report_digest(first) == (
        expected_digest
    )
    assert validate_specialist_team_cross_domain_handoff_packet_public_payload(
        payload,
    ) == payload
    assert_no_runtime_numbers(payload)


def test_attention_and_blocked_status_reason_codes_are_deterministic() -> None:
    capacity_watch = report(recipient_capacity_score=d("0.250000"))

    assert capacity_watch.handoff_status == "attention"
    assert capacity_watch.reason_codes == (
        "recipient_capacity_below_handoff_threshold",
    )
    assert capacity_watch.manual_next_step == "confirm_recipient_capacity"

    deadline_watch = report(deadline_hours=d("2.000000"))
    assert deadline_watch.handoff_status == "attention"
    assert deadline_watch.reason_codes == (
        "handoff_deadline_inside_manual_review_window",
    )
    assert deadline_watch.manual_next_step == "confirm_handoff_deadline"

    blocked = report(
        primary_team_id="market-research",
        secondary_team_id="market-research",
        handoff_reason_count=d("0.000000"),
        evidence_digest_present=False,
        recipient_capacity_score=d("0.250000"),
        deadline_hours=d("0.000000"),
    )
    assert blocked.handoff_status == "blocked"
    assert blocked.reason_codes == (
        "handoff_requires_distinct_team_ids",
        "handoff_reason_count_missing",
        "evidence_digest_missing",
        "deadline_hours_missing",
        "recipient_capacity_below_handoff_threshold",
    )
    assert blocked.manual_next_step == "prepare_manual_handoff_packet"


def test_dataclasses_are_frozen_and_decimal_only() -> None:
    source = handoff_input()
    result = report()

    assert is_dataclass(SpecialistTeamCrossDomainHandoffPacketInput)
    assert is_dataclass(SpecialistTeamCrossDomainHandoffPacketReport)
    assert source.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.handoff_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(SpecialistTeamCrossDomainHandoffPacketInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(SpecialistTeamCrossDomainHandoffPacketReport):
            pass

    with pytest.raises(ValueError, match="handoff_reason_count"):
        handoff_input(handoff_reason_count=1)
    with pytest.raises(ValueError, match="recipient_capacity_score"):
        handoff_input(recipient_capacity_score=0.75)
    with pytest.raises(ValueError, match="deadline_hours"):
        handoff_input(deadline_hours=_DecimalSubclass("24.000000"))
    with pytest.raises(ValueError, match="evidence_digest_present"):
        handoff_input(evidence_digest_present=Decimal("1.000000"))
    with pytest.raises(ValueError, match="payload_digest"):
        replace(result, payload_digest="not-canonical")

    hints = get_type_hints(SpecialistTeamCrossDomainHandoffPacketReport)
    assert hints["handoff_reason_count"] is Decimal
    assert hints["recipient_capacity_score"] is Decimal
    assert hints["deadline_hours"] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name in {
            "handoff_reason_count",
            "recipient_capacity_score",
            "deadline_hours",
        }:
            assert type(value) is Decimal


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        SpecialistTeamCrossDomainHandoffPacketReport(
            primary_team_id="market-research",
            secondary_team_id="policy-review",
            handoff_reason_count=d("2.000000"),
            evidence_digest_present=True,
            recipient_capacity_score=d("0.750000"),
            deadline_hours=d("24.000000"),
            handoff_status="ready",
            reason_codes=("recipient_capacity_below_handoff_threshold",),
            manual_next_step="send_public_handoff_packet",
        )


def test_public_payload_tamper_checks_and_no_live_or_durable_io_surface() -> None:
    payload = dict(report().public_payload)

    with pytest.raises(ValueError, match="recipient_capacity_score"):
        validate_specialist_team_cross_domain_handoff_packet_public_payload(
            {**payload, "recipient_capacity_score": "0.250000"},
        )
    with pytest.raises(ValueError, match="handoff_status"):
        validate_specialist_team_cross_domain_handoff_packet_public_payload(
            {**payload, "handoff_status": "blocked"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_specialist_team_cross_domain_handoff_packet_public_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="public payload"):
        validate_specialist_team_cross_domain_handoff_packet_public_payload(
            {**payload, "primary_team_id": "service_role"},
        )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "secret",
        "signature",
        "signing",
        "submit",
        "execute",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr.lower())

    assert not float_constants
    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "psycopg",
            "supabase",
            "web3",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "cursor",
            "delete",
            "executemany",
            "fetch",
            "insert",
            "open",
            "post",
            "put",
            "rollback",
            "send",
            "sign",
            "submit",
            "upsert",
            "write",
            "write_text",
            "write_bytes",
        },
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "live" not in lowered
        assert "auth" not in lowered
        assert "wallet" not in lowered
        assert "order" not in lowered
        assert "key" not in lowered
        assert "sign" not in lowered


def test_digest_changes_when_handoff_inputs_change() -> None:
    ready = report()
    capacity_watch = report(recipient_capacity_score=d("0.250000"))
    blocked = report(evidence_digest_present=False)

    assert ready.payload_digest != capacity_watch.payload_digest
    assert ready.payload_digest != blocked.payload_digest
    assert ready.public_payload != capacity_watch.public_payload

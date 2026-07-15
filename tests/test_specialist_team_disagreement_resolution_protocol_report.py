from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.specialist_team_disagreement_resolution_protocol_report import (
    SPECIALIST_TEAM_DISAGREEMENT_RESOLUTION_PROTOCOL_STATUSES,
    SpecialistTeamDisagreementResolutionProtocolReport,
    build_specialist_team_disagreement_resolution_protocol_report,
    specialist_team_disagreement_resolution_protocol_report_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_disagreement_resolution_protocol_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: Any) -> SpecialistTeamDisagreementResolutionProtocolReport:
    values: dict[str, Any] = {
        "dissenting_team_count": d("2.000000"),
        "unresolved_claim_count": d("1.000000"),
        "mediator_assigned": True,
        "evidence_packet_digest_present": True,
        "resolution_sla_hours": d("24.000000"),
    }
    values.update(overrides)
    return build_specialist_team_disagreement_resolution_protocol_report(**values)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_no_unsafe_runtime_surface(value: Any) -> None:
    forbidden = (
        "live",
        "auth",
        "wallet",
        "key",
        "signature",
        "signing",
        "execute",
        "execution",
        "order",
        "trade",
        "database",
        "table",
        "dsn",
        "jsonl",
        "file",
        "persist",
        "http://",
        "https://",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            lowered_key = key.casefold()
            assert not any(term in lowered_key for term in forbidden), lowered_key
            assert_no_unsafe_runtime_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_unsafe_runtime_surface(item)
        return
    if isinstance(value, float):
        raise AssertionError(f"unexpected float {value!r}")
    if type(value) is int:
        raise AssertionError(f"unexpected int {value!r}")
    if type(value) is str:
        lowered = value.casefold()
        assert not any(term in lowered for term in forbidden), lowered


def test_ready_protocol_reports_manual_review_readiness_without_runtime_surface() -> None:
    report = build_report()
    payload = specialist_team_disagreement_resolution_protocol_report_payload(report)

    assert SPECIALIST_TEAM_DISAGREEMENT_RESOLUTION_PROTOCOL_STATUSES == (
        "ready",
        "watch",
        "blocked",
    )
    assert report.protocol_status == "ready"
    assert report.reason_codes == ("resolution_protocol_ready",)
    assert report.manual_next_step == "manual_review_resolution_packet"
    assert report.dissenting_team_count == d("2.000000")
    assert report.unresolved_claim_count == d("1.000000")
    assert report.resolution_sla_hours == d("24.000000")
    assert report.mediator_assigned is True
    assert report.evidence_packet_digest_present is True
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.public_payload == payload
    assert payload["dissenting_team_count"] == "2.000000"
    assert payload["resolution_sla_hours"] == "24.000000"
    assert type(report.payload_digest) is str
    assert len(report.payload_digest) == 64
    assert payload["payload_digest"] == report.payload_digest
    assert_no_unsafe_runtime_surface(payload)
    json.dumps(payload, sort_keys=True)


def test_watch_when_no_active_disagreement_or_no_unresolved_claims() -> None:
    no_dissent = build_report(dissenting_team_count=d("0.000000"))
    no_claims = build_report(unresolved_claim_count=d("0.000000"))

    assert no_dissent.protocol_status == "watch"
    assert no_dissent.reason_codes == ("no_dissenting_teams",)
    assert no_dissent.manual_next_step == "monitor_for_specialist_disagreement"
    assert no_claims.protocol_status == "watch"
    assert no_claims.reason_codes == ("no_unresolved_claims",)
    assert no_claims.manual_next_step == "monitor_for_unresolved_claims"


def test_blocked_protocol_reports_missing_mediator_evidence_and_sla() -> None:
    report = build_report(
        mediator_assigned=False,
        evidence_packet_digest_present=False,
        resolution_sla_hours=d("0.000000"),
    )

    assert report.protocol_status == "blocked"
    assert report.reason_codes == (
        "mediator_not_assigned",
        "evidence_packet_digest_missing",
        "resolution_sla_missing",
    )
    assert report.manual_next_step == "assign_mediator_and_prepare_evidence_packet"
    assert_no_unsafe_runtime_surface(report.public_payload)


def test_dataclass_is_frozen_exact_decimal_only_and_strictly_validated() -> None:
    report = build_report()

    assert SpecialistTeamDisagreementResolutionProtocolReport.__dataclass_params__.frozen
    assert_public_numeric_values_are_decimal(report)
    with pytest.raises(FrozenInstanceError):
        report.protocol_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="dissenting_team_count must be exactly Decimal"):
        build_report(dissenting_team_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unresolved_claim_count must be exactly Decimal"):
        build_report(unresolved_claim_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="resolution_sla_hours must be integral"):
        build_report(resolution_sla_hours=d("1.500000"))
    with pytest.raises(ValueError, match="mediator_assigned must be bool"):
        build_report(mediator_assigned=Decimal("1.000000"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="0" * 64)


def test_public_payload_rejects_flag_downgrades_digest_tampering_and_unsafe_terms() -> None:
    report = build_report()
    payload = dict(report.public_payload)

    payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        specialist_team_disagreement_resolution_protocol_report_payload(payload)

    payload = dict(report.public_payload)
    payload["protocol_status"] = "watch"
    with pytest.raises(ValueError, match="payload_digest"):
        specialist_team_disagreement_resolution_protocol_report_payload(payload)

    payload = dict(report.public_payload)
    payload["dissenting_team_count"] = 2
    with pytest.raises(ValueError, match="Decimal-derived"):
        specialist_team_disagreement_resolution_protocol_report_payload(payload)

    payload = dict(report.public_payload)
    payload["note"] = "live order execution"
    with pytest.raises(ValueError, match="unsafe public value"):
        specialist_team_disagreement_resolution_protocol_report_payload(payload)


def test_module_is_report_only_and_external_io_free() -> None:
    report = build_report()
    assert report == build_report()
    assert report.public_payload == build_report().public_payload

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module.split(".")[0])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert imported_names.isdisjoint(
        {
            "httpx",
            "requests",
            "socket",
            "urllib",
            "psycopg",
            "psycopg2",
            "supabase",
            "sqlalchemy",
        },
    )
    assert call_names.isdisjoint({"open", "connect", "request", "post", "put", "delete"})
    assert_no_unsafe_runtime_surface(report.public_payload)

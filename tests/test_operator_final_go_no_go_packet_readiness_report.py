from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.operator_final_go_no_go_packet_readiness_report import (
    OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION,
    OperatorFinalGoNoGoPacketReadinessInput,
    OperatorFinalGoNoGoPacketReadinessReport,
    build_operator_final_go_no_go_packet_readiness_report,
    operator_final_go_no_go_packet_readiness_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/operator_final_go_no_go_packet_readiness_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def digest_payload(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def audit_entry_digest(
    *,
    entry_id: str,
    previous_entry_digest: str,
    decision_log_digest: str,
    reviewer_attestation_digest: str,
    source_packet_digest: str,
    public_payload_digest: str,
) -> str:
    return digest_payload(
        {
            "decision_log_digest": decision_log_digest,
            "entry_id": entry_id,
            "previous_entry_digest": previous_entry_digest,
            "public_payload_digest": public_payload_digest,
            "reviewer_attestation_digest": reviewer_attestation_digest,
            "source_packet_digest": source_packet_digest,
        },
    )


def audit_entry(
    *,
    entry_id: str,
    previous_entry_digest: str,
    decision_log_digest: str,
    reviewer_attestation_digest: str,
    source_packet_digest: str,
    public_payload_digest: str,
) -> dict[str, str]:
    return {
        "entry_id": entry_id,
        "previous_entry_digest": previous_entry_digest,
        "decision_log_digest": decision_log_digest,
        "reviewer_attestation_digest": reviewer_attestation_digest,
        "source_packet_digest": source_packet_digest,
        "public_payload_digest": public_payload_digest,
        "entry_digest": audit_entry_digest(
            entry_id=entry_id,
            previous_entry_digest=previous_entry_digest,
            decision_log_digest=decision_log_digest,
            reviewer_attestation_digest=reviewer_attestation_digest,
            source_packet_digest=source_packet_digest,
            public_payload_digest=public_payload_digest,
        ),
    }


def default_audit_entry() -> dict[str, str]:
    return audit_entry(
        entry_id="operator_journal_decision_001",
        previous_entry_digest="0" * 64,
        decision_log_digest="1" * 64,
        reviewer_attestation_digest="2" * 64,
        source_packet_digest="3" * 64,
        public_payload_digest="4" * 64,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    values: list[Any] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def build(
    *,
    all_required_gates_passed: bool = True,
    manual_attestation_present: bool = True,
    latest_packet_digest_present: bool = True,
    cost_recheck_passed: bool = True,
    source_freshness_passed: bool = True,
    memory_policy_passed: bool = True,
    audit_chain_entries: tuple[dict[str, str], ...] = (default_audit_entry(),),
    expected_source_packet_digest: str = "3" * 64,
    expected_public_payload_digest: str = "4" * 64,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> OperatorFinalGoNoGoPacketReadinessReport:
    return build_operator_final_go_no_go_packet_readiness_report(
        OperatorFinalGoNoGoPacketReadinessInput(
            all_required_gates_passed=all_required_gates_passed,
            manual_attestation_present=manual_attestation_present,
            latest_packet_digest_present=latest_packet_digest_present,
            cost_recheck_passed=cost_recheck_passed,
            source_freshness_passed=source_freshness_passed,
            memory_policy_passed=memory_policy_passed,
            audit_chain_entries=audit_chain_entries,
            expected_source_packet_digest=expected_source_packet_digest,
            expected_public_payload_digest=expected_public_payload_digest,
            paper_only=paper_only,
            report_only=report_only,
            readonly=readonly,
        ),
    )


def test_all_phase_1_gates_ready_emit_human_review_go_packet() -> None:
    report = build()
    payload = operator_final_go_no_go_packet_readiness_report_payload(report)
    json.dumps(payload, sort_keys=True)

    assert type(report) is OperatorFinalGoNoGoPacketReadinessReport
    assert is_dataclass(report)
    assert report.config_version == OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION
    assert report.go_no_go_status == "go"
    assert report.reason_codes == ("operator_final_go_no_go_packet_ready",)
    assert report.manual_next_step == "human_final_review_required"
    assert report.ready_gate_count == d("6.000000")
    assert report.blocked_gate_count == ZERO
    assert report.ready_ratio == ONE
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.public_payload == payload
    assert payload["ready_gate_count"] == "6.000000"
    assert payload["blocked_gate_count"] == "0.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["audit_chain_entry_count"] == "1.000000"
    assert payload["audit_chain_tip_digest"] == default_audit_entry()["entry_digest"]
    assert payload["expected_source_packet_digest"] == "3" * 64
    assert payload["expected_public_payload_digest"] == "4" * 64
    assert payload["payload_digest"] == report.payload_digest
    assert all(type(value) is not Decimal for value in walk_values(payload))
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "order" not in json.dumps(payload, sort_keys=True).lower()


def test_missing_manual_attestation_blocks_final_go_without_execution_path() -> None:
    report = build(manual_attestation_present=False)

    assert report.go_no_go_status == "no_go"
    assert report.reason_codes == ("manual_attestation_missing",)
    assert report.manual_next_step == "collect_manual_attestation_before_final_review"
    assert report.ready_gate_count == d("5.000000")
    assert report.blocked_gate_count == d("1.000000")
    assert report.ready_ratio == d("0.833333")


def test_multiple_failed_packet_readiness_checks_preserve_reason_priority() -> None:
    report = build(
        all_required_gates_passed=False,
        latest_packet_digest_present=False,
        cost_recheck_passed=False,
        source_freshness_passed=False,
        memory_policy_passed=False,
    )

    assert report.go_no_go_status == "no_go"
    assert report.reason_codes == (
        "required_gates_failed",
        "latest_packet_digest_missing",
        "cost_recheck_failed",
        "source_freshness_failed",
        "memory_policy_failed",
    )
    assert report.manual_next_step == "resolve_blockers_before_final_review"
    assert report.ready_gate_count == d("1.000000")
    assert report.blocked_gate_count == d("5.000000")
    assert report.ready_ratio == d("0.166667")


def test_contract_is_frozen_decimal_only_and_strictly_readonly() -> None:
    report = build()

    with pytest.raises(FrozenInstanceError):
        report.go_no_go_status = "no_go"  # type: ignore[misc]
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(report, ready_ratio=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="ready_gate_count"):
        replace(report, ready_gate_count=6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        build(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        build(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build(readonly=False)
    with pytest.raises(ValueError, match="all_required_gates_passed"):
        build_operator_final_go_no_go_packet_readiness_report(
            OperatorFinalGoNoGoPacketReadinessInput(
                all_required_gates_passed=1,  # type: ignore[arg-type]
                manual_attestation_present=True,
                latest_packet_digest_present=True,
                cost_recheck_passed=True,
                source_freshness_passed=True,
                memory_policy_passed=True,
                audit_chain_entries=(default_audit_entry(),),
                expected_source_packet_digest="3" * 64,
                expected_public_payload_digest="4" * 64,
            ),
        )
    for field in fields(report):
        value = getattr(report, field.name)
        if field.name in {"ready_gate_count", "blocked_gate_count", "ready_ratio"}:
            assert type(value) is Decimal


def test_payload_rejects_mutated_digest_and_numeric_public_values() -> None:
    report = build()
    payload = operator_final_go_no_go_packet_readiness_report_payload(report)

    tampered = dict(payload)
    tampered["ready_ratio"] = "0.500000"
    with pytest.raises(ValueError, match="payload_digest"):
        operator_final_go_no_go_packet_readiness_report_payload(tampered)

    with pytest.raises(ValueError, match="public payload numerics"):
        operator_final_go_no_go_packet_readiness_report_payload(
            {
                **payload,
                "ready_gate_count": 6,
            },
        )


def test_audit_chain_readiness_requires_linked_digest_chain_attestation_and_hashes() -> None:
    first = audit_entry(
        entry_id="operator_journal_decision_001",
        previous_entry_digest="0" * 64,
        decision_log_digest="a" * 64,
        reviewer_attestation_digest="b" * 64,
        source_packet_digest="c" * 64,
        public_payload_digest="d" * 64,
    )
    second = audit_entry(
        entry_id="operator_journal_decision_002",
        previous_entry_digest=first["entry_digest"],
        decision_log_digest="e" * 64,
        reviewer_attestation_digest="f" * 64,
        source_packet_digest="c" * 64,
        public_payload_digest="d" * 64,
    )

    report = build(
        audit_chain_entries=(first, second),
        expected_source_packet_digest="c" * 64,
        expected_public_payload_digest="d" * 64,
    )
    payload = operator_final_go_no_go_packet_readiness_report_payload(report)

    assert report.go_no_go_status == "go"
    assert report.audit_chain_entry_count == d("2.000000")
    assert report.audit_chain_tip_digest == second["entry_digest"]
    assert payload["audit_chain_entry_count"] == "2.000000"
    assert payload["audit_chain_tip_digest"] == second["entry_digest"]
    assert payload["expected_source_packet_digest"] == "c" * 64
    assert payload["expected_public_payload_digest"] == "d" * 64

    forged_link = dict(second)
    forged_link["previous_entry_digest"] = "9" * 64
    with pytest.raises(ValueError, match="digest chain"):
        build(
            audit_chain_entries=(first, forged_link),
            expected_source_packet_digest="c" * 64,
            expected_public_payload_digest="d" * 64,
        )

    forged_attestation = dict(first)
    forged_attestation["reviewer_attestation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="reviewer attestation"):
        build(
            audit_chain_entries=(forged_attestation,),
            expected_source_packet_digest="c" * 64,
            expected_public_payload_digest="d" * 64,
        )

    forged_source = dict(first)
    forged_source["source_packet_digest"] = "5" * 64
    with pytest.raises(ValueError, match="source packet hash"):
        build(
            audit_chain_entries=(forged_source,),
            expected_source_packet_digest="c" * 64,
            expected_public_payload_digest="d" * 64,
        )

    forged_public_output = dict(first)
    forged_public_output["public_payload_digest"] = "6" * 64
    with pytest.raises(ValueError, match="public payload hash"):
        build(
            audit_chain_entries=(forged_public_output,),
            expected_source_packet_digest="c" * 64,
            expected_public_payload_digest="d" * 64,
        )


def test_public_payload_rejects_forged_safe_output_even_with_recomputed_digest() -> None:
    report = build()
    payload = dict(operator_final_go_no_go_packet_readiness_report_payload(report))
    payload["expected_public_payload_digest"] = "8" * 64
    digest_source = dict(payload)
    digest_source["payload_digest"] = ""
    payload["payload_digest"] = digest_payload(digest_source)

    with pytest.raises(ValueError, match="public payload hash"):
        operator_final_go_no_go_packet_readiness_report_payload(payload)


def test_owned_module_has_no_live_storage_auth_wallet_order_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden_text in (
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "secret_key",
        "sign",
        "auto",
        "execute",
        "jsonl",
        "open(",
        "write(",
        "path(",
    ):
        assert forbidden_text not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    call_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
        "pathlib",
    }
    assert not (forbidden_import_roots & {name.split(".", 1)[0] for name in imported_modules})

    forbidden_call_names = {
        "connect",
        "executemany",
        "post",
        "put",
        "patch",
        "delete",
        "request",
        "urlopen",
    }
    assert not (forbidden_call_names & set(call_names))


def _recompute_report_payload_digest(payload: dict[str, object]) -> None:
    digest_source = dict(payload)
    digest_source["payload_digest"] = ""
    payload["payload_digest"] = digest_payload(digest_source)


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("all_required_gates_passed", False, "ready_gate_count"),
        ("ready_gate_count", "5.000000", "ready_gate_count"),
        ("reason_codes", ["required_gates_failed"], "reason_codes"),
        ("go_no_go_status", "no_go", "go_no_go_status"),
        ("manual_next_step", "resolve_blockers_before_final_review", "manual_next_step"),
        ("config_version", "unsupported-report-version", "config_version"),
    ),
)
def test_mapping_replays_all_report_derivations_with_recomputed_digest(
    field_name: str,
    value: object,
    message: str,
) -> None:
    payload = json.loads(json.dumps(operator_final_go_no_go_packet_readiness_report_payload(build())))
    payload[field_name] = value
    _recompute_report_payload_digest(payload)

    with pytest.raises(ValueError, match=message):
        operator_final_go_no_go_packet_readiness_report_payload(payload)


def test_report_object_export_rejects_noncanonical_quantum_tuple_and_scalar_types() -> None:
    report = build()
    object.__setattr__(report, "ready_gate_count", Decimal("6"))
    with pytest.raises(ValueError, match="ready_gate_count.*six decimal places"):
        operator_final_go_no_go_packet_readiness_report_payload(report)

    report = build()
    object.__setattr__(report, "audit_chain_entries", list(report.audit_chain_entries))
    with pytest.raises(ValueError, match="audit_chain_entries.*tuple"):
        operator_final_go_no_go_packet_readiness_report_payload(report)

    class StringSubclass(str):
        pass

    report = build()
    object.__setattr__(
        report,
        "config_version",
        StringSubclass(OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION),
    )
    with pytest.raises(ValueError, match="config_version.*exactly str"):
        operator_final_go_no_go_packet_readiness_report_payload(report)


def test_builder_revalidates_mutated_input_object_graph() -> None:
    inputs = OperatorFinalGoNoGoPacketReadinessInput(
        all_required_gates_passed=True,
        manual_attestation_present=True,
        latest_packet_digest_present=True,
        cost_recheck_passed=True,
        source_freshness_passed=True,
        memory_policy_passed=True,
        audit_chain_entries=(default_audit_entry(),),
        expected_source_packet_digest="3" * 64,
        expected_public_payload_digest="4" * 64,
    )
    object.__setattr__(inputs, "audit_chain_entries", list(inputs.audit_chain_entries))

    with pytest.raises(ValueError, match="audit_chain_entries.*tuple"):
        build_operator_final_go_no_go_packet_readiness_report(inputs)


def test_readonly_report_payload_blocks_in_place_union_at_every_depth() -> None:
    payload = operator_final_go_no_go_packet_readiness_report_payload(build())

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload.__ior__({"extra": "value"})
    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["audit_chain_entries"][0].__ior__({"extra": "value"})
    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload.__init__({"extra": "value"})
    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["audit_chain_entries"][0].__init__({"extra": "value"})

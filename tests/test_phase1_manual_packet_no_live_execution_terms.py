from __future__ import annotations

import ast
import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.manual_operator_decision_packet import (
    ManualOperatorDecisionFact,
    build_manual_operator_decision_packet,
    build_manual_operator_go_no_go_packet,
    manual_operator_decision_packet_payload,
    manual_operator_go_no_go_packet_payload,
)
from polymarket_alpha_lab.operator_final_go_no_go_packet_readiness_report import (
    OperatorFinalGoNoGoPacketReadinessInput,
    build_operator_final_go_no_go_packet_readiness_report,
    operator_final_go_no_go_packet_readiness_report_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "polymarket_alpha_lab"

MANUAL_OPERATOR_SOURCE_MODULES = (
    SOURCE_ROOT / "manual_operator_decision_packet.py",
    SOURCE_ROOT / "operator_final_go_no_go_packet_readiness_report.py",
)
MANUAL_OPERATOR_TEST_MODULES = (
    REPO_ROOT / "tests" / "test_manual_operator_decision_packet.py",
    REPO_ROOT / "tests" / "test_operator_final_go_no_go_packet_readiness_report.py",
    REPO_ROOT / "tests" / "test_phase1_manual_packet_no_live_execution_terms.py",
)

ACTION_FIELD_NAMES = {
    "action",
    "next_action",
    "next_manual_review_action",
    "next_step",
    "manual_next_step",
    "recommended_action",
    "recommended_next_step",
}
ACTION_FIELD_NAME_STRINGS = ACTION_FIELD_NAMES | {"next_manual_review_action"}
ACTION_VALIDATION_MESSAGE_PREFIXES = (
    "manual_next_step must ",
    "next_manual_review_action must ",
)
ALLOWED_ACTION_PREFIXES = (
    "manual_review_",
    "collect_manual_attestation_before_final_review",
    "human_final_review_required",
    "resolve_blockers_before_final_review",
)
ALLOWED_REPORT_ONLY_VALUES = {
    "go",
    "no_go",
    "pass",
    "watch",
    "block",
    "blocked",
    "ready",
    "manual_operator_go_no_go_ready",
    "manual_operator_go_no_go_manual_packet_not_ready",
    "manual_operator_go_no_go_ready_queue_not_ready",
    "manual_operator_go_no_go_audit_trail_not_ready",
    "manual_operator_go_no_go_public_output_not_safe",
    "operator_final_go_no_go_packet_ready",
    "human_final_review",
    "required_gates_failed",
    "manual_attestation_missing",
    "latest_packet_digest_missing",
    "cost_recheck_failed",
    "source_freshness_failed",
    "memory_policy_failed",
}
FORBIDDEN_EXECUTION_TERMS = {
    "submit_order",
    "execute_trade",
    "live trading",
    "wallet signing",
    "wallet_signing",
    "place_order",
    "create_order",
    "sign_order",
    "route_order",
    "order mutation",
    "live_execution",
}


def _fact(
    checklist_area: str,
    support_status: str,
    reason_summary: str,
    *,
    blocker_summary: str | None = None,
) -> ManualOperatorDecisionFact:
    return ManualOperatorDecisionFact(
        checklist_area=checklist_area,
        support_status=support_status,
        reason_summary=reason_summary,
        blocker_summary=blocker_summary,
    )


def _manual_packet_payloads() -> tuple[Mapping[str, object], ...]:
    generated_at = datetime(2026, 7, 12, 10, 0, tzinfo=UTC)
    ready_packet = build_manual_operator_decision_packet(
        (
            _fact("research", "pass", "research support packet complete"),
            _fact("evidence", "pass", "evidence bundle redacted"),
            _fact("source_authority", "pass", "source crosscheck complete"),
            _fact("microstructure", "pass", "microstructure summary complete"),
            _fact("cost", "pass", "cost support complete"),
            _fact("timing", "pass", "timing support complete"),
            _fact("team_memory", "pass", "team memory scan clear"),
        ),
        generated_at=generated_at,
    )
    blocked_packet = build_manual_operator_decision_packet(
        (
            _fact("research", "watch", "research recency requires manual check"),
            _fact("evidence", "pass", "evidence bundle redacted"),
            _fact("source_authority", "pass", "source crosscheck complete"),
            _fact("microstructure", "pass", "microstructure summary complete"),
            _fact(
                "cost",
                "block",
                "cost model support incomplete",
                blocker_summary="fee assumptions unresolved",
            ),
            _fact("timing", "pass", "timing support complete"),
            _fact("team_memory", "pass", "team memory scan clear"),
        ),
        generated_at=generated_at,
    )
    go_no_go_ready = build_manual_operator_go_no_go_packet(
        manual_packet=ready_packet,
        ready_queue_status="ready",
        ready_queue_payload_digest="1" * 64,
        audit_trail_status="pass",
        audit_trail_payload_digest="2" * 64,
        public_output_safe_for_operator_display=True,
        public_output_payload_digest="3" * 64,
    )
    go_no_go_blocked = build_manual_operator_go_no_go_packet(
        manual_packet=blocked_packet,
        ready_queue_status="blocked",
        ready_queue_payload_digest="4" * 64,
        audit_trail_status="blocked",
        audit_trail_payload_digest="5" * 64,
        public_output_safe_for_operator_display=False,
        public_output_payload_digest="6" * 64,
    )
    return (
        manual_operator_decision_packet_payload(ready_packet),
        manual_operator_decision_packet_payload(blocked_packet),
        manual_operator_go_no_go_packet_payload(go_no_go_ready),
        manual_operator_go_no_go_packet_payload(go_no_go_blocked),
    )


def _digest_entry(
    *,
    entry_id: str,
    previous_entry_digest: str,
    source_packet_digest: str,
    public_payload_digest: str,
) -> dict[str, str]:
    import hashlib

    entry = {
        "entry_id": entry_id,
        "previous_entry_digest": previous_entry_digest,
        "decision_log_digest": "a" * 64,
        "reviewer_attestation_digest": "b" * 64,
        "source_packet_digest": source_packet_digest,
        "public_payload_digest": public_payload_digest,
    }
    entry["entry_digest"] = hashlib.sha256(
        json.dumps(
            entry,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return entry


def _operator_final_payloads() -> tuple[Mapping[str, object], ...]:
    source_digest = "c" * 64
    public_digest = "d" * 64
    audit_entry = _digest_entry(
        entry_id="operator_journal_decision_001",
        previous_entry_digest="0" * 64,
        source_packet_digest=source_digest,
        public_payload_digest=public_digest,
    )
    ready = build_operator_final_go_no_go_packet_readiness_report(
        OperatorFinalGoNoGoPacketReadinessInput(
            all_required_gates_passed=True,
            manual_attestation_present=True,
            latest_packet_digest_present=True,
            cost_recheck_passed=True,
            source_freshness_passed=True,
            memory_policy_passed=True,
            audit_chain_entries=(audit_entry,),
            expected_source_packet_digest=source_digest,
            expected_public_payload_digest=public_digest,
        ),
    )
    blocked = build_operator_final_go_no_go_packet_readiness_report(
        OperatorFinalGoNoGoPacketReadinessInput(
            all_required_gates_passed=False,
            manual_attestation_present=False,
            latest_packet_digest_present=False,
            cost_recheck_passed=False,
            source_freshness_passed=False,
            memory_policy_passed=False,
            audit_chain_entries=(audit_entry,),
            expected_source_packet_digest=source_digest,
            expected_public_payload_digest=public_digest,
        ),
    )
    return (
        operator_final_go_no_go_packet_readiness_report_payload(ready),
        operator_final_go_no_go_packet_readiness_report_payload(blocked),
    )


def _walk_mapping_values(value: object) -> Iterable[object]:
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _walk_mapping_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_mapping_values(item)
    else:
        yield value


def _action_values_from_payload(payload: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(
        str(value)
        for field_name, value in payload.items()
        if field_name in ACTION_FIELD_NAMES and isinstance(value, str)
    )


def _assert_manual_or_report_only(value: str) -> None:
    assert value in ALLOWED_REPORT_ONLY_VALUES or value.startswith(
        ALLOWED_ACTION_PREFIXES,
    ), value


def _is_validation_message(value: str) -> bool:
    return value.startswith(ACTION_VALIDATION_MESSAGE_PREFIXES)


def _forbidden_terms(value: str) -> set[str]:
    normalized = value.lower().replace("-", "_")
    spaced = value.lower().replace("_", " ")
    return {
        term
        for term in FORBIDDEN_EXECUTION_TERMS
        if term in normalized or term in spaced
    }


def _is_self_guard_allowlist_literal(path: Path, value: str) -> bool:
    return (
        path.name == "test_phase1_manual_packet_no_live_execution_terms.py"
        and (
            value in FORBIDDEN_EXECUTION_TERMS
            or value == "test_phase1_manual_packet_no_live_execution_terms.py"
        )
    )


def test_manual_operator_public_action_outputs_are_manual_review_only() -> None:
    payloads = _manual_packet_payloads() + _operator_final_payloads()
    action_values = tuple(
        value
        for payload in payloads
        for value in _action_values_from_payload(payload)
    )

    assert action_values
    assert all(value.startswith(ALLOWED_ACTION_PREFIXES) for value in action_values)
    for value in action_values:
        assert not _forbidden_terms(value), value


def test_manual_operator_public_payloads_do_not_emit_live_execution_terms() -> None:
    for payload in _manual_packet_payloads() + _operator_final_payloads():
        serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        assert not _forbidden_terms(serialized), serialized


def test_manual_operator_source_constants_keep_actions_report_only() -> None:
    for path in MANUAL_OPERATOR_SOURCE_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            value = node.value
            if _is_self_guard_allowlist_literal(path, value):
                continue
            if _forbidden_terms(value):
                raise AssertionError((path, node.lineno, value))
            if value in ACTION_FIELD_NAME_STRINGS:
                continue
            if (
                "action" in value
                or "next_step" in value
                or value.startswith(("manual_review_", "human_final_review"))
            ):
                if _is_validation_message(value):
                    continue
                _assert_manual_or_report_only(value)


def test_manual_operator_tests_do_not_expect_live_execution_actions() -> None:
    for path in MANUAL_OPERATOR_TEST_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            value = node.value
            if _is_self_guard_allowlist_literal(path, value):
                continue
            if _forbidden_terms(value):
                raise AssertionError((path, node.lineno, value))
            if value in ACTION_FIELD_NAME_STRINGS:
                continue
            if (
                "manual_next_step" in value
                or "next_manual_review_action" in value
                or value.startswith(("manual_review_", "human_final_review"))
            ):
                if _is_validation_message(value):
                    continue
                _assert_manual_or_report_only(value)

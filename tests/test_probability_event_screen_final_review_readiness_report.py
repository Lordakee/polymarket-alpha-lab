from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_screen_final_review_readiness_report as api
from polymarket_alpha_lab.probability_event_screen_final_review_readiness_report import (
    FINAL_REVIEW_BANDS,
    ProbabilityEventScreenFinalReviewReadinessInput,
    ProbabilityEventScreenFinalReviewReadinessReport,
    build_probability_event_screen_final_review_readiness_report,
    probability_event_screen_final_review_readiness_report_digest,
    probability_event_screen_final_review_readiness_report_to_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_final_review_readiness_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness_input(
    *,
    screen_contract_ready: bool = True,
    quality_index_ready: bool = True,
    decision_memo_ready: bool = True,
    go_no_go_ready: bool = True,
    review_packet_index_ready: bool = True,
    audit_summary_ready: bool = True,
    operating_review_ready: bool = True,
    operator_public_output_safe: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenFinalReviewReadinessInput:
    return ProbabilityEventScreenFinalReviewReadinessInput(
        screen_contract_ready=screen_contract_ready,
        quality_index_ready=quality_index_ready,
        decision_memo_ready=decision_memo_ready,
        go_no_go_ready=go_no_go_ready,
        review_packet_index_ready=review_packet_index_ready,
        audit_summary_ready=audit_summary_ready,
        operating_review_ready=operating_review_ready,
        operator_public_output_safe=operator_public_output_safe,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    source: ProbabilityEventScreenFinalReviewReadinessInput,
) -> ProbabilityEventScreenFinalReviewReadinessReport:
    return build_probability_event_screen_final_review_readiness_report(source)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_final_review_band_vocabulary_is_exact() -> None:
    assert FINAL_REVIEW_BANDS == ("ready", "attention", "blocked")


def test_all_upstream_artifacts_ready_emits_final_review_payload_and_digest() -> None:
    report = build_report(readiness_input())

    assert is_dataclass(report)
    assert report.final_review_ready is True
    assert report.final_review_band == "ready"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "probability_event_screen_final_review_ready",
    )
    assert report.ready_ratio == ONE
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = probability_event_screen_final_review_readiness_report_to_payload(report)
    assert report.public_payload == payload
    assert payload == {
        "screen_contract_ready": True,
        "quality_index_ready": True,
        "decision_memo_ready": True,
        "go_no_go_ready": True,
        "review_packet_index_ready": True,
        "audit_summary_ready": True,
        "operating_review_ready": True,
        "operator_public_output_safe": True,
        "final_review_ready": True,
        "final_review_band": "ready",
        "blocked_reason_codes": [],
        "attention_reason_codes": [
            "probability_event_screen_final_review_ready",
        ],
        "ready_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert report.digest == expected_digest
    assert probability_event_screen_final_review_readiness_report_digest(report) == expected_digest
    assert_no_runtime_numbers(payload)


def test_missing_required_artifacts_block_final_review_in_deterministic_order() -> None:
    report = build_report(
        readiness_input(
            screen_contract_ready=False,
            quality_index_ready=False,
            decision_memo_ready=False,
            go_no_go_ready=False,
            review_packet_index_ready=False,
            audit_summary_ready=False,
            operating_review_ready=False,
        ),
    )

    assert report.final_review_ready is False
    assert report.final_review_band == "blocked"
    assert report.ready_ratio == d("0.125000")
    assert report.blocked_reason_codes == (
        "final_review_screen_contract_not_ready",
        "final_review_quality_index_not_ready",
        "final_review_decision_memo_not_ready",
        "final_review_go_no_go_not_ready",
        "final_review_review_packet_index_not_ready",
        "final_review_audit_summary_not_ready",
        "final_review_operating_review_not_ready",
    )
    assert report.attention_reason_codes == ()
    assert report.public_payload["ready_ratio"] == "0.125000"


def test_operator_public_output_safety_attention_blocks_final_ready_flag() -> None:
    report = build_report(readiness_input(operator_public_output_safe=False))

    assert report.final_review_ready is False
    assert report.final_review_band == "attention"
    assert report.ready_ratio == d("0.875000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "final_review_operator_public_output_not_safe",
    )


def test_dataclasses_are_frozen_decimal_only_and_flags_are_enforced() -> None:
    source = readiness_input()
    report = build_report(source)

    assert is_dataclass(ProbabilityEventScreenFinalReviewReadinessInput)
    assert is_dataclass(ProbabilityEventScreenFinalReviewReadinessReport)
    assert source.__dataclass_params__.frozen
    assert report.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        report.final_review_band = "blocked"  # type: ignore[misc]

    for field in fields(report):
        value = getattr(report, field.name)
        if field.name == "ready_ratio":
            assert type(value) is Decimal

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenFinalReviewReadinessInput):
            pass

    with pytest.raises(ValueError, match="screen_contract_ready must be a bool"):
        readiness_input(screen_contract_ready=ONE)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="operator_public_output_safe must be a bool"):
        readiness_input(operator_public_output_safe=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        readiness_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        readiness_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ready_ratio must be a Decimal"):
        replace(report, ready_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio must be a Decimal"):
        replace(report, ready_ratio=_DecimalSubclass("1.000000"))


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="blocked_reason_codes"):
        ProbabilityEventScreenFinalReviewReadinessReport(
            screen_contract_ready=False,
            quality_index_ready=True,
            decision_memo_ready=True,
            go_no_go_ready=True,
            review_packet_index_ready=True,
            audit_summary_ready=True,
            operating_review_ready=True,
            operator_public_output_safe=True,
            final_review_ready=False,
            final_review_band="blocked",
            blocked_reason_codes=(),
            attention_reason_codes=(),
            ready_ratio=d("0.875000"),
        )


def test_public_api_stays_readonly_report_only_paper_only_and_side_effect_free() -> None:
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "database",
        "network",
        "request",
        "http",
        "broker",
        "private_key",
        "api_key",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ProbabilityEventScreenFinalReviewReadinessInput,
        ProbabilityEventScreenFinalReviewReadinessReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in forbidden_fragments + (
        "urlopen",
        "connect(",
        "execute(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr.lower())

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
            "request",
            "urlopen",
            "send",
            "submit",
            "place_order",
            "cancel_order",
            "sign",
            "write",
            "write_text",
            "write_bytes",
        },
    )


def test_digest_changes_when_readiness_inputs_change() -> None:
    ready = build_report(readiness_input())
    attention = build_report(readiness_input(operator_public_output_safe=False))

    assert ready.digest != attention.digest
    assert ready.public_payload != attention.public_payload

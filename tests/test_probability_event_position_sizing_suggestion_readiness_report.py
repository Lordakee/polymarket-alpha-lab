from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_position_sizing_suggestion_readiness_report as api
from polymarket_alpha_lab.probability_event_position_sizing_suggestion_readiness_report import (
    ProbabilityEventPositionSizingSuggestionReadinessInput,
    ProbabilityEventPositionSizingSuggestionReadinessReport,
    build_probability_event_position_sizing_suggestion_readiness_report,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "probability_event_position_sizing_suggestion_readiness_report.py",
)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def sizing_input(
    *,
    net_edge_probability: Decimal = d("0.080000"),
    confidence_probability: Decimal = d("0.750000"),
    liquidity_score_probability: Decimal = d("0.800000"),
    correlation_risk_probability: Decimal = d("0.200000"),
    max_manual_size_probability: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventPositionSizingSuggestionReadinessInput:
    return ProbabilityEventPositionSizingSuggestionReadinessInput(
        net_edge_probability=net_edge_probability,
        confidence_probability=confidence_probability,
        liquidity_score_probability=liquidity_score_probability,
        correlation_risk_probability=correlation_risk_probability,
        max_manual_size_probability=max_manual_size_probability,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    readiness_input: ProbabilityEventPositionSizingSuggestionReadinessInput,
) -> ProbabilityEventPositionSizingSuggestionReadinessReport:
    return build_probability_event_position_sizing_suggestion_readiness_report(
        readiness_input,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def expected_digest(payload: dict[str, object]) -> str:
    values = dict(payload)
    values.pop("payload_digest")
    encoded = json.dumps(
        values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_ready_report_suggests_manual_size_payload_and_digest() -> None:
    report = build_report(sizing_input())

    assert is_dataclass(report)
    assert report.sizing_status == "ready"
    assert report.suggested_manual_size_probability == d("0.038400")
    assert report.reason_codes == (
        "manual_sizing_suggestion_ready_for_human_review",
    )
    assert report.manual_next_step == (
        "manual_reviewer_verify_packet_before_any_submission"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == {
        "sizing_status": "ready",
        "suggested_manual_size_probability": "0.038400",
        "reason_codes": ["manual_sizing_suggestion_ready_for_human_review"],
        "manual_next_step": "manual_reviewer_verify_packet_before_any_submission",
        "net_edge_probability": "0.080000",
        "confidence_probability": "0.750000",
        "liquidity_score_probability": "0.800000",
        "correlation_risk_probability": "0.200000",
        "max_manual_size_probability": "0.050000",
        "report_notice": "manual_review_suggestion_only_not_submittable",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": report.payload_digest,
    }
    assert report.payload_digest == expected_digest(payload)
    assert_no_float_or_int_values(payload)


def test_review_status_reduces_size_and_lists_attention_reasons() -> None:
    report = build_report(
        sizing_input(
            net_edge_probability=d("0.030000"),
            confidence_probability=d("0.600000"),
            liquidity_score_probability=d("0.500000"),
            correlation_risk_probability=d("0.350000"),
            max_manual_size_probability=d("0.040000"),
        ),
    )

    assert report.sizing_status == "review"
    assert report.suggested_manual_size_probability == d("0.005850")
    assert report.reason_codes == (
        "net_edge_probability_below_ready_floor",
        "confidence_probability_below_ready_floor",
        "liquidity_score_probability_below_ready_floor",
        "correlation_risk_probability_above_ready_ceiling",
    )
    assert report.manual_next_step == (
        "manual_reviewer_resolve_reason_codes_before_sizing"
    )
    assert report.public_payload["payload_digest"] == report.payload_digest


def test_blocked_status_zeroes_size_and_requires_manual_blocker_clearance() -> None:
    report = build_report(
        sizing_input(
            net_edge_probability=d("0.010000"),
            confidence_probability=d("0.400000"),
            liquidity_score_probability=d("0.300000"),
            correlation_risk_probability=d("0.600000"),
            max_manual_size_probability=ZERO,
        ),
    )

    assert report.sizing_status == "blocked"
    assert report.suggested_manual_size_probability == ZERO
    assert report.reason_codes == (
        "net_edge_probability_below_review_floor",
        "confidence_probability_below_review_floor",
        "liquidity_score_probability_below_review_floor",
        "correlation_risk_probability_above_review_ceiling",
        "max_manual_size_probability_zero",
    )
    assert report.manual_next_step == (
        "manual_reviewer_do_not_size_until_blockers_clear"
    )
    assert report.public_payload["suggested_manual_size_probability"] == "0.000000"


def test_dataclasses_are_frozen_decimal_only_and_phase_flags_are_enforced() -> None:
    readiness_input = sizing_input()
    report = build_report(readiness_input)

    with pytest.raises(FrozenInstanceError):
        report.sizing_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventPositionSizingSuggestionReadinessInput):
            pass

    with pytest.raises(ValueError, match="net_edge_probability must be a Decimal"):
        sizing_input(net_edge_probability=0.08)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="confidence_probability must be between"):
        sizing_input(confidence_probability=d("1.100000"))

    with pytest.raises(ValueError, match="paper_only"):
        sizing_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        sizing_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="payload_digest must match public payload"):
        replace(report, payload_digest="0" * 64)


def test_public_api_excludes_execution_surfaces_and_file_persistence() -> None:
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "private_key",
        "api_key",
        "signature",
        "signing",
        "auto_submit",
        "jsonl",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ProbabilityEventPositionSizingSuggestionReadinessInput,
        ProbabilityEventPositionSizingSuggestionReadinessReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "subprocess",
    ):
        assert not hasattr(api, forbidden_name)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "web3",
            "ccxt",
            "subprocess",
            "pathlib",
        },
    )

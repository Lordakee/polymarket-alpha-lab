from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_packet_resolution_criteria_conflict_index_v2"
)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def conflict_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "packet_id": "packet-resolution-criteria-conflict-v2",
        "market_slug": "market-resolution-criteria-conflict-v2",
        "market_question": "Alpha wins title",
        "resolution_criteria": "Alpha loses title",
        "official_source_count": d("0"),
        "minimum_official_source_count": d("1"),
        "observed_evidence_count": d("3"),
        "conflicting_evidence_count": d("2"),
        "watch_conflict_index_bps": d("100.000000"),
        "blocked_conflict_index_bps": d("300.000000"),
        "reason_codes": ("research_packet_present",),
    }
    values.update(overrides)
    return module.ResearchPacketResolutionCriteriaConflictIndexV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_research_packet_resolution_criteria_conflict_index_v2(
        conflict_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_conflict_index_combines_wording_source_gap_and_observed_evidence() -> None:
    result = score()

    assert result.question_only_term_count == d("1")
    assert result.criteria_only_term_count == d("1")
    assert result.shared_resolution_term_count == d("2")
    assert result.wording_conflict_term_count == d("2")
    assert result.wording_conflict_bps == d("80.000000")
    assert result.official_source_gap_count == d("1")
    assert result.official_source_gap_penalty_bps == d("125.000000")
    assert result.observed_support_evidence_count == d("1")
    assert result.observed_conflict_evidence_penalty_bps == d("180.000000")
    assert result.observed_support_evidence_credit_bps == d("25.000000")
    assert result.raw_conflict_index_bps == d("385.000000")
    assert result.paper_conflict_index_bps == d("360.000000")
    assert result.conflict_status == "blocked"
    assert result.conflict_decision == "reject"
    assert result.reason_codes == (
        "research_packet_present",
        "research_packet_resolution_criteria_conflict_index_v2",
        "conflict_status_blocked",
        "wording_conflict_detected",
        "official_source_gap_detected",
        "observed_conflict_evidence_detected",
        "observed_support_evidence_credit_applied",
        "conflict_index_blocked",
    )
    assert type(result.paper_conflict_index_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64


def test_supported_resolution_packet_clears_conflict_index() -> None:
    result = score(
        conflict_input(
            market_question="Alpha wins title",
            resolution_criteria="Alpha wins title",
            official_source_count=d("2"),
            minimum_official_source_count=d("1"),
            observed_evidence_count=d("4"),
            conflicting_evidence_count=d("0"),
            reason_codes=(),
        ),
    )

    assert result.question_only_term_count == d("0")
    assert result.criteria_only_term_count == d("0")
    assert result.shared_resolution_term_count == d("3")
    assert result.wording_conflict_bps == d("0.000000")
    assert result.official_source_gap_count == d("0")
    assert result.observed_support_evidence_count == d("4")
    assert result.observed_support_evidence_credit_bps == d("100.000000")
    assert result.raw_conflict_index_bps == d("0.000000")
    assert result.paper_conflict_index_bps == d("0.000000")
    assert result.conflict_status == "clear"
    assert result.conflict_decision == "paper_clear"
    assert result.reason_codes == (
        "research_packet_resolution_criteria_conflict_index_v2",
        "conflict_status_clear",
        "observed_support_evidence_credit_applied",
        "no_conflict_index_detected",
    )


def test_watch_when_conflict_index_is_positive_but_below_blocked_threshold() -> None:
    result = score(
        conflict_input(
            market_question="Alpha wins title",
            resolution_criteria="Alpha wins title",
            official_source_count=d("0"),
            minimum_official_source_count=d("1"),
            observed_evidence_count=d("0"),
            conflicting_evidence_count=d("0"),
            reason_codes=(),
        ),
    )

    assert result.paper_conflict_index_bps == d("125.000000")
    assert result.conflict_status == "watch"
    assert result.conflict_decision == "manual_review"
    assert "conflict_index_positive_below_blocked" in result.reason_codes


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.research_packet_resolution_criteria_conflict_index_v2_payload(
        result,
    )
    assert payload["paper_conflict_index_bps"] == "360.000000"
    assert payload["question_only_term_count"] == "1"
    assert payload["shared_resolution_term_count"] == "2"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_resolution_criteria_conflict_index_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = conflict_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert (
        module.ResearchPacketResolutionCriteriaConflictIndexV2Input
        .__dataclass_params__
        .frozen
    )
    assert (
        module.ResearchPacketResolutionCriteriaConflictIndexV2Result
        .__dataclass_params__
        .frozen
    )

    with pytest.raises(FrozenInstanceError):
        subject.packet_id = "other-packet"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.conflict_status = "clear"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="official_source_count must be a Decimal"):
        conflict_input(official_source_count=0)
    with pytest.raises(ValueError, match="packet_id must be a canonical"):
        conflict_input(packet_id=" packet-resolution-criteria-conflict-v2")
    with pytest.raises(ValueError, match="official_source_count must be integral"):
        conflict_input(official_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="observed evidence"):
        conflict_input(
            observed_evidence_count=d("1"),
            conflicting_evidence_count=d("2"),
        )
    with pytest.raises(ValueError, match="blocked_conflict_index_bps"):
        conflict_input(blocked_conflict_index_bps=d("99.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        conflict_input(reason_codes=["research_packet_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        conflict_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.ResearchPacketResolutionCriteriaConflictIndexV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchPacketResolutionCriteriaConflictIndexV2Result(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )

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
        with pytest.raises(ValueError, match="unsafe"):
            conflict_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_research_packet_resolution_criteria_conflict_index_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_research_packet_resolution_criteria_conflict_index_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/research_packet_resolution_criteria_conflict_index_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "live",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "wallet",
        " auth",
        "order",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.__all__ == (
        "CONFLICT_STATUSES",
        "CONFLICT_DECISIONS",
        "ResearchPacketResolutionCriteriaConflictIndexV2Input",
        "ResearchPacketResolutionCriteriaConflictIndexV2Result",
        "estimate_research_packet_resolution_criteria_conflict_index_v2",
        "research_packet_resolution_criteria_conflict_index_v2_payload",
        "reject_research_packet_resolution_criteria_conflict_index_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "research_packet_resolution_criteria_conflict_index_v2" not in getattr(
        root,
        "__all__",
        (),
    )

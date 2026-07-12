from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.probability_event_resolution_source_confidence_weight_report as api
from polymarket_alpha_lab.probability_event_resolution_source_confidence_weight_report import (
    CONFIDENCE_WEIGHT_STATUSES,
    ProbabilityEventResolutionSourceConfidenceWeightInput,
    ProbabilityEventResolutionSourceConfidenceWeightReport,
    build_probability_event_resolution_source_confidence_weight_report,
    probability_event_resolution_source_confidence_weight_report_to_payload,
    validate_probability_event_resolution_source_confidence_weight_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_resolution_source_confidence_weight_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def source_input(
    **overrides: object,
) -> ProbabilityEventResolutionSourceConfidenceWeightInput:
    values = {
        "official_source_weight_probability": d("0.700000"),
        "independent_source_weight_probability": d("0.600000"),
        "market_signal_weight_probability": d("0.400000"),
        "source_conflict_probability": d("0.100000"),
        "freshness_penalty_probability": d("0.050000"),
    }
    values.update(overrides)
    return ProbabilityEventResolutionSourceConfidenceWeightInput(**values)


def report(
    **overrides: object,
) -> ProbabilityEventResolutionSourceConfidenceWeightReport:
    return build_probability_event_resolution_source_confidence_weight_report(
        source_input(**overrides),
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


def test_confidence_status_vocabulary_is_exact() -> None:
    assert CONFIDENCE_WEIGHT_STATUSES == ("high_confidence", "review", "blocked")


def test_weighted_confidence_report_is_readonly_payload_digest_bound() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventResolutionSourceConfidenceWeightReport
    assert is_dataclass(first)
    assert first.confidence_weight_status == "high_confidence"
    assert first.weighted_confidence_probability == d("0.515000")
    assert first.reason_codes == ("resolution_source_confidence_weight_high",)
    assert first.manual_next_step == (
        "Manual review: compare official resolution source, independent confirmation, "
        "and market signal before any separate decision process."
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_resolution_source_confidence_weight_report_to_payload(
        first,
    )
    assert first.public_payload == payload
    assert payload == {
        "official_source_weight_probability": "0.700000",
        "independent_source_weight_probability": "0.600000",
        "market_signal_weight_probability": "0.400000",
        "source_conflict_probability": "0.100000",
        "freshness_penalty_probability": "0.050000",
        "confidence_weight_status": "high_confidence",
        "weighted_confidence_probability": "0.515000",
        "reason_codes": ["resolution_source_confidence_weight_high"],
        "manual_next_step": (
            "Manual review: compare official resolution source, independent confirmation, "
            "and market signal before any separate decision process."
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert first.payload_digest == second.payload_digest
    assert (
        validate_probability_event_resolution_source_confidence_weight_public_payload(
            payload,
        )
        == payload
    )
    assert_no_runtime_numbers(payload)


def test_review_and_blocked_reason_codes_are_deterministic() -> None:
    review = report(
        official_source_weight_probability=d("0.500000"),
        independent_source_weight_probability=d("0.500000"),
        market_signal_weight_probability=d("0.200000"),
        source_conflict_probability=d("0.250000"),
        freshness_penalty_probability=d("0.100000"),
    )
    blocked = report(
        official_source_weight_probability=d("0.300000"),
        independent_source_weight_probability=d("0.200000"),
        market_signal_weight_probability=d("0.100000"),
        source_conflict_probability=d("0.800000"),
        freshness_penalty_probability=d("0.500000"),
    )

    assert review.confidence_weight_status == "review"
    assert review.weighted_confidence_probability == d("0.205000")
    assert review.reason_codes == (
        "resolution_source_confidence_weight_review",
        "resolution_source_conflict_material",
    )
    assert blocked.confidence_weight_status == "blocked"
    assert blocked.weighted_confidence_probability == d("0.000000")
    assert blocked.reason_codes == (
        "resolution_source_confidence_weight_blocked",
        "resolution_source_conflict_critical",
        "resolution_source_freshness_penalty_critical",
    )


def test_dataclasses_are_frozen_flags_enforced_and_decimal_only() -> None:
    source = source_input()
    result = report()

    assert is_dataclass(ProbabilityEventResolutionSourceConfidenceWeightInput)
    assert is_dataclass(ProbabilityEventResolutionSourceConfidenceWeightReport)
    assert source.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.confidence_weight_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventResolutionSourceConfidenceWeightInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventResolutionSourceConfidenceWeightReport):
            pass

    with pytest.raises(ValueError, match="official_source_weight_probability"):
        source_input(official_source_weight_probability=1)
    with pytest.raises(ValueError, match="market_signal_weight_probability"):
        source_input(market_signal_weight_probability=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="source_conflict_probability"):
        source_input(source_conflict_probability=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        source_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="weighted_confidence_probability"):
        replace(result, weighted_confidence_probability=1)  # type: ignore[arg-type]

    hints = get_type_hints(ProbabilityEventResolutionSourceConfidenceWeightReport)
    assert hints["weighted_confidence_probability"] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name.endswith("_probability"):
            assert type(value) is Decimal


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        ProbabilityEventResolutionSourceConfidenceWeightReport(
            official_source_weight_probability=d("0.700000"),
            independent_source_weight_probability=d("0.600000"),
            market_signal_weight_probability=d("0.400000"),
            source_conflict_probability=d("0.100000"),
            freshness_penalty_probability=d("0.050000"),
            confidence_weight_status="high_confidence",
            weighted_confidence_probability=d("0.515000"),
            reason_codes=(),
            manual_next_step=(
                "Manual review: compare official resolution source, independent "
                "confirmation, and market signal before any separate decision process."
            ),
        )


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)

    with pytest.raises(ValueError, match="weighted_confidence_probability"):
        validate_probability_event_resolution_source_confidence_weight_public_payload(
            {**payload, "weighted_confidence_probability": "0.100000"},
        )
    with pytest.raises(ValueError, match="confidence_weight_status"):
        validate_probability_event_resolution_source_confidence_weight_public_payload(
            {**payload, "confidence_weight_status": "blocked"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_probability_event_resolution_source_confidence_weight_public_payload(
            {**payload, "paper_only": False},
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
        "private_key",
        "wallet",
        "live",
        "auth",
        "signature",
        "signed_transaction",
        "submit_order",
        "cancel_order",
        "write_text",
        "write_bytes",
        "jsonl",
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
            "execute",
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
        assert "wallet" not in lowered
        assert "auth" not in lowered
        assert "order" not in lowered
        assert "trade" not in lowered


def test_payload_digest_changes_when_source_confidence_inputs_change() -> None:
    ready = report()
    review = report(source_conflict_probability=d("0.400000"))
    stale = report(freshness_penalty_probability=d("0.500000"))

    assert ready.payload_digest != review.payload_digest
    assert ready.payload_digest != stale.payload_digest
    assert ready.public_payload != review.public_payload

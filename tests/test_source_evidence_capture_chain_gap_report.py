from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.source_evidence_capture_chain_gap_report as api
from polymarket_alpha_lab.source_evidence_capture_chain_gap_report import (
    CAPTURE_CHAIN_STATUSES,
    SourceEvidenceCaptureChainGapInput,
    SourceEvidenceCaptureChainGapReport,
    build_source_evidence_capture_chain_gap_report,
    source_evidence_capture_chain_gap_report_digest,
    source_evidence_capture_chain_gap_report_to_payload,
    validate_source_evidence_capture_chain_gap_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "source_evidence_capture_chain_gap_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def capture_input(**overrides: object) -> SourceEvidenceCaptureChainGapInput:
    values = {
        "expected_source_count": d("4.000000"),
        "captured_source_count": d("4.000000"),
        "digest_gap_count": d("0.000000"),
        "timestamp_gap_count": d("0.000000"),
        "official_anchor_present": True,
    }
    values.update(overrides)
    return SourceEvidenceCaptureChainGapInput(**values)


def report(**overrides: object) -> SourceEvidenceCaptureChainGapReport:
    return build_source_evidence_capture_chain_gap_report(capture_input(**overrides))


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_capture_chain_status_vocabulary_is_exact() -> None:
    assert CAPTURE_CHAIN_STATUSES == ("complete", "incomplete", "blocked")


def test_complete_capture_chain_emits_readonly_payload_and_digest() -> None:
    first = report()
    second = report()

    assert type(first) is SourceEvidenceCaptureChainGapReport
    assert is_dataclass(first)
    assert first.capture_chain_status == "complete"
    assert first.reason_codes == ("source_evidence_capture_chain_complete",)
    assert first.manual_next_step == "continue_manual_review_with_captured_evidence"
    assert first.expected_source_count == d("4.000000")
    assert first.captured_source_count == d("4.000000")
    assert first.digest_gap_count == d("0.000000")
    assert first.timestamp_gap_count == d("0.000000")
    assert first.official_anchor_present is True
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = source_evidence_capture_chain_gap_report_to_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "expected_source_count": "4.000000",
        "captured_source_count": "4.000000",
        "digest_gap_count": "0.000000",
        "timestamp_gap_count": "0.000000",
        "official_anchor_present": True,
        "capture_chain_status": "complete",
        "reason_codes": ["source_evidence_capture_chain_complete"],
        "manual_next_step": "continue_manual_review_with_captured_evidence",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert first.payload_digest == second.payload_digest
    assert source_evidence_capture_chain_gap_report_digest(first) == expected_digest
    assert validate_source_evidence_capture_chain_gap_public_payload(payload) == payload
    assert_no_runtime_numbers(payload)


def test_capture_chain_gaps_are_incomplete_in_deterministic_order() -> None:
    result = report(
        expected_source_count=d("5.000000"),
        captured_source_count=d("3.000000"),
        digest_gap_count=d("2.000000"),
        timestamp_gap_count=d("1.000000"),
    )

    assert result.capture_chain_status == "incomplete"
    assert result.reason_codes == (
        "source_evidence_captured_count_below_expected",
        "source_evidence_digest_gap_detected",
        "source_evidence_timestamp_gap_detected",
    )
    assert result.manual_next_step == "manually_reconcile_missing_source_evidence"
    assert result.public_payload["reason_codes"] == list(result.reason_codes)


def test_missing_official_anchor_blocks_capture_chain() -> None:
    result = report(
        expected_source_count=d("3.000000"),
        captured_source_count=d("3.000000"),
        official_anchor_present=False,
    )

    assert result.capture_chain_status == "blocked"
    assert result.reason_codes == ("source_evidence_official_anchor_missing",)
    assert result.manual_next_step == "manually_capture_official_source_anchor"


def test_dataclasses_are_frozen_and_decimal_only() -> None:
    source = capture_input()
    result = report()

    assert is_dataclass(SourceEvidenceCaptureChainGapInput)
    assert is_dataclass(SourceEvidenceCaptureChainGapReport)
    assert source.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.capture_chain_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(SourceEvidenceCaptureChainGapInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(SourceEvidenceCaptureChainGapReport):
            pass

    with pytest.raises(ValueError, match="expected_source_count"):
        capture_input(expected_source_count=4)
    with pytest.raises(ValueError, match="captured_source_count"):
        capture_input(captured_source_count=_DecimalSubclass("4.000000"))
    with pytest.raises(ValueError, match="digest_gap_count"):
        capture_input(digest_gap_count=d("-1.000000"))
    with pytest.raises(ValueError, match="official_anchor_present"):
        capture_input(official_anchor_present=1)
    with pytest.raises(ValueError, match="expected_source_count"):
        capture_input(expected_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="captured_source_count"):
        capture_input(
            expected_source_count=d("1.000000"),
            captured_source_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(result, manual_next_step="submit_live_order")

    hints = get_type_hints(SourceEvidenceCaptureChainGapReport)
    for name in (
        "expected_source_count",
        "captured_source_count",
        "digest_gap_count",
        "timestamp_gap_count",
    ):
        assert hints[name] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name.endswith("_count"):
            assert type(value) is Decimal


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        SourceEvidenceCaptureChainGapReport(
            expected_source_count=d("4.000000"),
            captured_source_count=d("3.000000"),
            digest_gap_count=d("0.000000"),
            timestamp_gap_count=d("0.000000"),
            official_anchor_present=True,
            capture_chain_status="incomplete",
            reason_codes=(),
            manual_next_step="manually_reconcile_missing_source_evidence",
        )


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)

    with pytest.raises(ValueError, match="captured_source_count"):
        validate_source_evidence_capture_chain_gap_public_payload(
            {**payload, "captured_source_count": "3.000000"},
        )
    with pytest.raises(ValueError, match="capture_chain_status"):
        validate_source_evidence_capture_chain_gap_public_payload(
            {**payload, "capture_chain_status": "blocked"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_source_evidence_capture_chain_gap_public_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="private"):
        validate_source_evidence_capture_chain_gap_public_payload(
            {
                **payload,
                "manual_next_step": "bearer private token",
            },
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
        "web3",
            "private_key",
            "api_key",
            "secret_key",
            "live",
            "auth",
            "wallet",
            "signing",
        "execution",
        "submit_order",
        "cancel_order",
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


def test_payload_digest_changes_when_capture_inputs_change() -> None:
    complete = report()
    incomplete = report(captured_source_count=d("3.000000"))
    blocked = report(official_anchor_present=False)

    assert complete.payload_digest != incomplete.payload_digest
    assert complete.payload_digest != blocked.payload_digest
    assert complete.public_payload != incomplete.public_payload

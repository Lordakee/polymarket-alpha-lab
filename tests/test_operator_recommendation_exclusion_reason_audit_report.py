from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.operator_recommendation_exclusion_reason_audit_report import (
    OperatorRecommendationExclusionReasonAuditReport,
    build_operator_recommendation_exclusion_reason_audit_report,
    operator_recommendation_exclusion_reason_audit_report_payload_digest,
    validate_operator_recommendation_exclusion_reason_audit_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "operator_recommendation_exclusion_reason_audit_report.py"
)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def report(
    **overrides: Decimal,
) -> OperatorRecommendationExclusionReasonAuditReport:
    values = {
        "excluded_candidate_count": d("6.000000"),
        "missing_reason_count": d("0.000000"),
        "cost_block_count": d("2.000000"),
        "source_block_count": d("3.000000"),
        "risk_block_count": d("1.000000"),
    }
    values.update(overrides)
    return build_operator_recommendation_exclusion_reason_audit_report(**values)


def payload_without_digest(payload: dict[str, object]) -> dict[str, object]:
    copy = dict(payload)
    copy.pop("payload_digest", None)
    return copy


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in walk(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in walk(child))
    return (value,)


def test_complete_exclusion_reasons_emit_ready_readonly_payload_and_digest() -> None:
    audit = report()

    assert is_dataclass(audit)
    assert audit.exclusion_audit_status == "exclusion_reasons_complete"
    assert audit.reason_codes == (
        "cost_block_reasons_present",
        "source_block_reasons_present",
        "risk_block_reasons_present",
    )
    assert audit.manual_next_step == "manual_review_excluded_candidates_before_queue_changes"
    assert audit.excluded_candidate_count == d("6.000000")
    assert audit.missing_reason_count == ZERO
    assert audit.paper_only is True
    assert audit.report_only is True
    assert audit.readonly is True

    payload = audit.public_payload
    assert payload["exclusion_audit_status"] == "exclusion_reasons_complete"
    assert payload["manual_next_step"] == (
        "manual_review_excluded_candidates_before_queue_changes"
    )
    assert payload["excluded_candidate_count"] == "6.000000"
    assert payload["missing_reason_count"] == "0.000000"
    assert payload["cost_block_count"] == "2.000000"
    assert payload["source_block_count"] == "3.000000"
    assert payload["risk_block_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == audit.payload_digest
    assert not any(type(value) in (Decimal, float, int) for value in walk(payload))
    assert validate_operator_recommendation_exclusion_reason_audit_public_payload(
        payload,
    ) is True
    assert operator_recommendation_exclusion_reason_audit_report_payload_digest(
        audit,
    ) == hashlib.sha256(
        json.dumps(
            payload_without_digest(payload),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    (
        ({"excluded_candidate_count": d("0.000000")}, "no_excluded_candidates_to_audit"),
        ({"missing_reason_count": d("1.000000")}, "excluded_candidates_missing_reasons"),
        ({"cost_block_count": d("0.000000")}, "no_cost_block_exclusions_recorded"),
        ({"source_block_count": d("0.000000")}, "no_source_block_exclusions_recorded"),
        ({"risk_block_count": d("0.000000")}, "no_risk_block_exclusions_recorded"),
    ),
)
def test_incomplete_reason_coverage_reports_specific_audit_reasons(
    overrides: dict[str, Decimal],
    expected_reason: str,
) -> None:
    audit = report(**overrides)

    assert audit.exclusion_audit_status == "exclusion_reasons_need_manual_attention"
    assert expected_reason in audit.reason_codes
    assert audit.manual_next_step == "fill_missing_exclusion_reasons_before_any_queue_change"


def test_multiple_incomplete_findings_use_canonical_order() -> None:
    audit = report(
        excluded_candidate_count=d("0.000000"),
        missing_reason_count=d("2.000000"),
        cost_block_count=d("0.000000"),
        risk_block_count=d("0.000000"),
    )

    assert audit.reason_codes == (
        "no_excluded_candidates_to_audit",
        "excluded_candidates_missing_reasons",
        "no_cost_block_exclusions_recorded",
        "no_risk_block_exclusions_recorded",
    )


@pytest.mark.parametrize(
    ("overrides", "match"),
    (
        ({"excluded_candidate_count": 6}, "excluded_candidate_count"),
        ({"missing_reason_count": "0.000000"}, "missing_reason_count"),
        ({"cost_block_count": Decimal("2.000001")}, "cost_block_count"),
        ({"source_block_count": Decimal("-1.000000")}, "source_block_count"),
        ({"risk_block_count": Decimal("NaN")}, "risk_block_count"),
    ),
)
def test_inputs_are_decimal_only_nonnegative_and_six_decimal(
    overrides: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        report(**overrides)  # type: ignore[arg-type]


def test_report_dataclass_is_frozen_and_revalidates_tampering() -> None:
    audit = report(missing_reason_count=d("1.000000"))

    with pytest.raises(FrozenInstanceError):
        audit.exclusion_audit_status = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(audit, paper_only=False)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(audit, reason_codes=())
    with pytest.raises(ValueError, match="payload_digest"):
        replace(audit, payload_digest="0" * 64)

    assert all("float" not in str(field.type) for field in fields(audit))
    assert all(
        "int" not in str(field.type) and field.type is not int for field in fields(audit)
    )


def test_public_payload_rejects_numeric_and_status_tampering() -> None:
    payload = report().public_payload

    numeric_tampered = dict(payload)
    numeric_tampered["excluded_candidate_count"] = 6
    with pytest.raises(ValueError, match="excluded_candidate_count"):
        validate_operator_recommendation_exclusion_reason_audit_public_payload(
            numeric_tampered,
        )

    status_tampered = dict(payload)
    status_tampered["missing_reason_count"] = "2.000000"
    status_tampered["payload_digest"] = hashlib.sha256(
        json.dumps(
            payload_without_digest(status_tampered),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    with pytest.raises(ValueError, match="exclusion_audit_status|reason_codes"):
        validate_operator_recommendation_exclusion_reason_audit_public_payload(
            status_tampered,
        )


def test_public_dataclass_rejects_subclassing() -> None:
    with pytest.raises(TypeError, match="subclass"):

        class UnsafeReport(OperatorRecommendationExclusionReasonAuditReport):
            pass


def test_module_is_readonly_report_only_without_execution_or_file_persistence_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "private_key",
        "api_key",
        "secret_key",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "connect(",
        "fetch(",
        "insert",
        "upsert",
        "delete",
        "database",
        "network",
        "live trading",
        "jsonl",
        "persist",
        "auto_execute",
        "execute(",
        "sign",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "float",
        "int",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names

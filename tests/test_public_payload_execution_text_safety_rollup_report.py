from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.public_payload_execution_text_safety_rollup_report import (
    PublicPayloadExecutionTextSafetyInput,
    PublicPayloadExecutionTextSafetyRollupReport,
    PublicPayloadExecutionTextSafetyRow,
    build_public_payload_execution_text_safety_rollup_report,
    public_payload_execution_text_safety_rollup_report_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 8, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


def candidate(
    candidate_id: str = "candidate-alpha",
    payload: dict[str, Any] | None = None,
    *,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PublicPayloadExecutionTextSafetyInput:
    return PublicPayloadExecutionTextSafetyInput(
        candidate_id=candidate_id,
        payload=payload
        or {
            "title": "public market research digest",
            "summary": "paper-only probability rationale for review",
            "metadata": {"source": "public news summary"},
        },
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def test_rollup_flags_execution_and_sensitive_text_fields() -> None:
    report = build_public_payload_execution_text_safety_rollup_report(
        [
            candidate(
                "candidate-safe",
                {
                    "headline": "public election forecast note",
                    "details": ["readonly research summary", "paper-only report"],
                },
            ),
            candidate(
                "candidate-unsafe",
                {
                    "account_id": "acct_123",
                    "instructions": "submit the live order after wallet sign",
                    "nested": {"private-key": "redacted"},
                },
            ),
        ],
        generated_at=GENERATED_AT,
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.safety_status == "unsafe"
    assert report.candidate_count == Decimal("2.000000")
    assert report.unsafe_field_count == Decimal("4.000000")
    assert report.redaction_required is True
    assert report.reason_codes == (
        "execution_text_safety_unsafe",
        "unsafe_account_text",
        "unsafe_key_text",
        "unsafe_live_text",
        "unsafe_order_text",
        "unsafe_private_key_text",
        "unsafe_sign_text",
        "unsafe_submit_text",
        "unsafe_wallet_text",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    safe, unsafe = report.rows
    assert safe.candidate_id == "candidate-safe"
    assert safe.safety_status == "safe"
    assert safe.unsafe_field_count == ZERO
    assert safe.reason_codes == ("execution_text_safety_clear",)
    assert safe.redaction_required is False

    assert unsafe.candidate_id == "candidate-unsafe"
    assert unsafe.safety_status == "unsafe"
    assert unsafe.unsafe_field_count == Decimal("4.000000")
    assert unsafe.redaction_required is True
    assert unsafe.unsafe_fields == (
        "account_id",
        "instructions",
        "nested.private-key",
        "nested.private-key",
    )
    assert unsafe.reason_codes == (
        "unsafe_account_text",
        "unsafe_key_text",
        "unsafe_live_text",
        "unsafe_order_text",
        "unsafe_private_key_text",
        "unsafe_sign_text",
        "unsafe_submit_text",
        "unsafe_wallet_text",
    )


def test_empty_and_safe_reports_are_readonly_and_frozen() -> None:
    empty = build_public_payload_execution_text_safety_rollup_report(
        [],
        generated_at=GENERATED_AT,
    )
    safe = build_public_payload_execution_text_safety_rollup_report(
        [candidate()],
        generated_at=GENERATED_AT,
    )

    assert empty.safety_status == "safe"
    assert empty.candidate_count == ZERO
    assert empty.unsafe_field_count == ZERO
    assert empty.reason_codes == ("execution_text_safety_empty",)
    assert empty.redaction_required is False
    assert empty.rows == ()

    assert safe.safety_status == "safe"
    assert safe.reason_codes == ("execution_text_safety_clear",)

    for value in (empty, safe, *safe.rows):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name.endswith("_count"):
                assert type(item_value) is Decimal

    frozen = candidate()
    with pytest.raises(FrozenInstanceError):
        frozen.candidate_id = "changed"  # type: ignore[misc]


def test_public_payload_uses_decimal_strings_and_requires_readonly_flags() -> None:
    report = build_public_payload_execution_text_safety_rollup_report(
        [candidate("candidate-safe")],
        generated_at=GENERATED_AT,
    )

    payload = public_payload_execution_text_safety_rollup_report_payload(report)

    assert payload["generated_at"] == "2026-07-12T08:45:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["unsafe_field_count"] == "0.000000"
    assert payload["safety_status"] == "safe"
    assert payload["redaction_required"] is False
    assert payload["rows"][0]["candidate_id"] == "candidate-safe"
    assert payload["rows"][0]["unsafe_field_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_values(payload)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        public_payload_execution_text_safety_rollup_report_payload(downgraded)


def test_validation_rejects_non_public_inputs_and_inconsistent_materialized_fields() -> None:
    with pytest.raises(ValueError, match="candidate_id"):
        candidate("")

    with pytest.raises(ValueError, match="JSON object"):
        candidate(payload=["not", "an", "object"])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)

    with pytest.raises(ValueError, match="generated_at"):
        build_public_payload_execution_text_safety_rollup_report(
            [candidate()],
            generated_at=datetime(2026, 7, 12, 8, 45),
        )

    report = build_public_payload_execution_text_safety_rollup_report(
        [candidate()],
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="unsafe_field_count"):
        PublicPayloadExecutionTextSafetyRow(
            **{
                **report.rows[0].__dict__,
                "unsafe_field_count": Decimal("1.000000"),
            },
        )
    with pytest.raises(ValueError, match="safety_status"):
        PublicPayloadExecutionTextSafetyRollupReport(
            **{
                **report.__dict__,
                "safety_status": "unsafe",
            },
        )


def test_module_exposes_no_execution_network_db_or_persistence_surface() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "public_payload_execution_text_safety_rollup_report.py"
    )
    tree = ast.parse(module_path.read_text())
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "submit",
        "urlopen",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names

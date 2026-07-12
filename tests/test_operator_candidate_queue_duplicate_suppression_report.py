from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.operator_candidate_queue_duplicate_suppression_report import (
    DEFAULT_OPERATOR_CANDIDATE_QUEUE_DUPLICATE_SUPPRESSION_REPORT_CONFIG_VERSION,
    OperatorCandidateQueueDuplicateSuppressionInput,
    OperatorCandidateQueueDuplicateSuppressionReport,
    build_operator_candidate_queue_duplicate_suppression_report,
    operator_candidate_queue_duplicate_suppression_report_digest,
    operator_candidate_queue_duplicate_suppression_report_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/operator_candidate_queue_duplicate_suppression_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(
    *,
    candidate_count: Decimal = d("10.000000"),
    duplicate_market_count: Decimal = d("2.000000"),
    same_resolution_family_count: Decimal = d("1.000000"),
    same_source_digest_count: Decimal = d("1.000000"),
    suppression_rule_count: Decimal = d("3.000000"),
    generated_at: datetime = GENERATED_AT,
) -> OperatorCandidateQueueDuplicateSuppressionReport:
    inputs = OperatorCandidateQueueDuplicateSuppressionInput(
        candidate_count=candidate_count,
        duplicate_market_count=duplicate_market_count,
        same_resolution_family_count=same_resolution_family_count,
        same_source_digest_count=same_source_digest_count,
        suppression_rule_count=suppression_rule_count,
    )
    return build_operator_candidate_queue_duplicate_suppression_report(
        inputs,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_ready_report_confirms_duplicate_suppression_controls_are_clear() -> None:
    report = build_report(
        candidate_count=d("6.000000"),
        duplicate_market_count=ZERO,
        same_resolution_family_count=ZERO,
        same_source_digest_count=ZERO,
        suppression_rule_count=d("4.000000"),
    )

    assert report.config_version == (
        DEFAULT_OPERATOR_CANDIDATE_QUEUE_DUPLICATE_SUPPRESSION_REPORT_CONFIG_VERSION
    )
    assert report.suppression_status == "ready"
    assert report.reason_codes == ("candidate_queue_duplicate_suppression_ready",)
    assert report.manual_next_step == "continue_manual_candidate_queue_review"
    assert report.candidate_count == d("6.000000")
    assert report.duplicate_market_count == ZERO
    assert report.same_resolution_family_count == ZERO
    assert report.same_source_digest_count == ZERO
    assert report.suppression_rule_count == d("4.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == operator_candidate_queue_duplicate_suppression_report_payload(report)
    assert payload["candidate_count"] == "6.000000"
    assert payload["duplicate_market_count"] == "0.000000"
    assert payload["same_resolution_family_count"] == "0.000000"
    assert payload["same_source_digest_count"] == "0.000000"
    assert payload["suppression_rule_count"] == "4.000000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["payload_digest"] == (
        operator_candidate_queue_duplicate_suppression_report_digest(report)
    )
    assert report.payload_digest == payload["payload_digest"]
    assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_blocked_report_requires_manual_duplicate_resolution_before_review() -> None:
    report = build_report(
        candidate_count=d("12.000000"),
        duplicate_market_count=d("3.000000"),
        same_resolution_family_count=d("2.000000"),
        same_source_digest_count=d("1.000000"),
        suppression_rule_count=d("5.000000"),
    )

    assert report.suppression_status == "blocked"
    assert report.reason_codes == (
        "candidate_queue_duplicate_market_collision",
        "candidate_queue_same_resolution_family_collision",
        "candidate_queue_same_source_digest_collision",
    )
    assert report.manual_next_step == "resolve_duplicate_markets_before_candidate_review"


def test_watch_report_flags_related_duplicates_and_missing_rules() -> None:
    related_report = build_report(
        candidate_count=d("7.000000"),
        duplicate_market_count=ZERO,
        same_resolution_family_count=d("2.000000"),
        same_source_digest_count=ZERO,
        suppression_rule_count=d("3.000000"),
    )
    missing_rules_report = build_report(
        candidate_count=d("7.000000"),
        duplicate_market_count=ZERO,
        same_resolution_family_count=ZERO,
        same_source_digest_count=ZERO,
        suppression_rule_count=ZERO,
    )

    assert related_report.suppression_status == "watch"
    assert related_report.reason_codes == (
        "candidate_queue_same_resolution_family_collision",
    )
    assert related_report.manual_next_step == (
        "compare_resolution_families_before_candidate_review"
    )

    assert missing_rules_report.suppression_status == "watch"
    assert missing_rules_report.reason_codes == (
        "candidate_queue_suppression_rules_missing",
    )
    assert missing_rules_report.manual_next_step == (
        "define_manual_suppression_rules_before_queue_review"
    )


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    for dataclass_type in (
        OperatorCandidateQueueDuplicateSuppressionInput,
        OperatorCandidateQueueDuplicateSuppressionReport,
    ):
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True
        for field in fields(dataclass_type):
            assert "float" not in str(field.type)
            assert "int" not in str(field.type)

    inputs = OperatorCandidateQueueDuplicateSuppressionInput(
        candidate_count=d("1.000000"),
        duplicate_market_count=ZERO,
        same_resolution_family_count=ZERO,
        same_source_digest_count=ZERO,
        suppression_rule_count=d("1.000000"),
    )
    with pytest.raises(FrozenInstanceError):
        inputs.candidate_count = d("2.000000")  # type: ignore[misc]


def test_validates_decimal_counts_flags_digest_and_payload_surface() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        build_report(candidate_count=1.0)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="plain Decimal"):
        build_report(duplicate_market_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="nonnegative"):
        build_report(same_source_digest_count=d("-1.000000"))

    with pytest.raises(ValueError, match="cannot exceed candidate_count"):
        build_report(candidate_count=d("1.000000"), duplicate_market_count=d("2.000000"))

    with pytest.raises(ValueError, match="cannot exceed candidate_count"):
        build_report(
            candidate_count=d("1.000000"),
            same_resolution_family_count=d("2.000000"),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        build_report(generated_at=datetime(2026, 7, 12, 11, 30))

    with pytest.raises(ValueError, match="paper_only"):
        replace(
            OperatorCandidateQueueDuplicateSuppressionInput(
                candidate_count=d("1.000000"),
                duplicate_market_count=ZERO,
                same_resolution_family_count=ZERO,
                same_source_digest_count=ZERO,
                suppression_rule_count=d("1.000000"),
            ),
            paper_only=False,
        )

    report = build_report()
    tampered = dict(report.public_payload)
    tampered["payload_digest"] = "0" * 64
    with pytest.raises(ValueError, match="payload_digest must match"):
        operator_candidate_queue_duplicate_suppression_report_payload(tampered)

    with pytest.raises(ValueError, match="unsafe public"):
        operator_candidate_queue_duplicate_suppression_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_path": "redacted",
            },
        )


def test_module_scope_has_no_live_auth_wallet_order_keys_signing_execution_or_persistence() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    forbidden_import_roots = {
        "builtins",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
    }
    forbidden_text = (
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "secret_key",
        "sign",
        "execute",
        "execution",
        "live",
        "jsonl",
        "persist",
        "open(",
        "write_text",
        "write_bytes",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots

    lowered_source = source.lower()
    for term in forbidden_text:
        assert term not in lowered_source

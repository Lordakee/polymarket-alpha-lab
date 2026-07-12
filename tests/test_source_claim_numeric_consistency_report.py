from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.source_claim_numeric_consistency_report as api
from polymarket_alpha_lab.source_claim_numeric_consistency_report import (
    SourceClaimNumericConsistencyReport,
    build_source_claim_numeric_consistency_report,
    source_claim_numeric_consistency_report_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def test_builds_pass_report_when_all_numeric_claims_match_official_sources() -> None:
    report = build_source_claim_numeric_consistency_report(
        numeric_claim_count=d("4.000000"),
        matched_claim_count=d("4.000000"),
        conflicting_claim_count=d("0.000000"),
        missing_source_digest_count=d("0.000000"),
        official_claim_count=d("2.000000"),
    )

    assert report == SourceClaimNumericConsistencyReport(
        numeric_claim_count=d("4.000000"),
        matched_claim_count=d("4.000000"),
        conflicting_claim_count=d("0.000000"),
        missing_source_digest_count=d("0.000000"),
        official_claim_count=d("2.000000"),
        consistency_status="pass",
        reason_codes=("source_claim_numeric_consistency_pass",),
        manual_next_step="document_numeric_claim_consistency",
        payload_digest=report.payload_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_conflicts_block_and_missing_digest_or_no_official_claims_watch() -> None:
    conflict_report = build_source_claim_numeric_consistency_report(
        numeric_claim_count=d("5.000000"),
        matched_claim_count=d("3.000000"),
        conflicting_claim_count=d("1.000000"),
        missing_source_digest_count=d("1.000000"),
        official_claim_count=d("1.000000"),
    )
    assert conflict_report.consistency_status == "block"
    assert conflict_report.reason_codes == (
        "numeric_claim_conflict_detected",
        "source_digest_missing",
    )
    assert conflict_report.manual_next_step == "manual_numeric_claim_reconciliation"

    missing_digest_report = build_source_claim_numeric_consistency_report(
        numeric_claim_count=d("2.000000"),
        matched_claim_count=d("2.000000"),
        conflicting_claim_count=d("0.000000"),
        missing_source_digest_count=d("1.000000"),
        official_claim_count=d("1.000000"),
    )
    assert missing_digest_report.consistency_status == "watch"
    assert missing_digest_report.reason_codes == ("source_digest_missing",)
    assert missing_digest_report.manual_next_step == "refresh_source_digest_evidence"

    no_official_report = build_source_claim_numeric_consistency_report(
        numeric_claim_count=d("2.000000"),
        matched_claim_count=d("2.000000"),
        conflicting_claim_count=d("0.000000"),
        missing_source_digest_count=d("0.000000"),
        official_claim_count=d("0.000000"),
    )
    assert no_official_report.consistency_status == "watch"
    assert no_official_report.reason_codes == ("official_numeric_claim_missing",)
    assert no_official_report.manual_next_step == "collect_official_numeric_claim_source"


def test_payload_is_json_ready_deterministic_and_digest_validates() -> None:
    report = build_source_claim_numeric_consistency_report(
        numeric_claim_count=d("3"),
        matched_claim_count=d("2"),
        conflicting_claim_count=d("0"),
        missing_source_digest_count=d("0"),
        official_claim_count=d("1"),
    )

    payload = source_claim_numeric_consistency_report_payload(report)

    json.dumps(payload, sort_keys=True)
    assert payload == report.public_payload
    assert payload["numeric_claim_count"] == "3.000000"
    assert payload["matched_claim_count"] == "2.000000"
    assert payload["conflicting_claim_count"] == "0.000000"
    assert payload["missing_source_digest_count"] == "0.000000"
    assert payload["official_claim_count"] == "1.000000"
    assert payload["consistency_status"] == "watch"
    assert payload["reason_codes"] == ("numeric_claim_unmatched",)
    assert payload["manual_next_step"] == "review_unmatched_numeric_claims"
    assert payload["payload_digest"] == report.payload_digest
    assert len(report.payload_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["matched_claim_count"] = "3.000000"
    with pytest.raises(ValueError, match="payload_digest"):
        source_claim_numeric_consistency_report_payload(tampered_payload)


def test_rejects_non_decimal_inconsistent_counts_flags_and_subclassing() -> None:
    with pytest.raises(ValueError, match="numeric_claim_count"):
        build_source_claim_numeric_consistency_report(
            numeric_claim_count=1,
            matched_claim_count=d("1.000000"),
            conflicting_claim_count=d("0.000000"),
            missing_source_digest_count=d("0.000000"),
            official_claim_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="matched_claim_count"):
        build_source_claim_numeric_consistency_report(
            numeric_claim_count=d("1.000000"),
            matched_claim_count=_DecimalSubclass("1.000000"),
            conflicting_claim_count=d("0.000000"),
            missing_source_digest_count=d("0.000000"),
            official_claim_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="claim counts"):
        build_source_claim_numeric_consistency_report(
            numeric_claim_count=d("1.000000"),
            matched_claim_count=d("1.000000"),
            conflicting_claim_count=d("1.000000"),
            missing_source_digest_count=d("0.000000"),
            official_claim_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="official_claim_count"):
        build_source_claim_numeric_consistency_report(
            numeric_claim_count=d("1.000000"),
            matched_claim_count=d("1.000000"),
            conflicting_claim_count=d("0.000000"),
            missing_source_digest_count=d("0.000000"),
            official_claim_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="readonly"):
        build_source_claim_numeric_consistency_report(
            numeric_claim_count=d("1.000000"),
            matched_claim_count=d("1.000000"),
            conflicting_claim_count=d("0.000000"),
            missing_source_digest_count=d("0.000000"),
            official_claim_count=d("1.000000"),
            readonly=False,
        )

    report = build_source_claim_numeric_consistency_report(
        numeric_claim_count=d("1.000000"),
        matched_claim_count=d("1.000000"),
        conflicting_claim_count=d("0.000000"),
        missing_source_digest_count=d("0.000000"),
        official_claim_count=d("1.000000"),
    )
    with pytest.raises(FrozenInstanceError):
        report.consistency_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(SourceClaimNumericConsistencyReport):
            pass


def test_module_has_no_network_persistence_or_action_surfaces() -> None:
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert "float(" not in source
    assert "jsonl" not in source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "delete",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    unsafe_terms = (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("key", "s"),
        _join_parts("sign", "ature"),
        _join_parts("execute"),
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(token in lowered for token in unsafe_terms)
    for field in fields(SourceClaimNumericConsistencyReport):
        lowered = field.name.lower()
        assert not any(token in lowered for token in unsafe_terms)


def _walk_public_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            values.extend(_walk_public_values(getattr(value, field.name)))
        return tuple(values)
    if isinstance(value, tuple):
        for item in value:
            values.extend(_walk_public_values(item))
        return tuple(values)
    values.append(value)
    return tuple(values)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    for item in _walk_public_values(value):
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if type(item) is bool or item is None or isinstance(item, str):
            continue
        if type(item) is int or isinstance(item, float):
            raise AssertionError(f"public numeric value is not Decimal: {item!r}")

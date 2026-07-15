from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.source_event_timeline_reconciliation_report as api
from polymarket_alpha_lab.source_event_timeline_reconciliation_report import (
    SourceEventTimelineReconciliationReport,
    build_source_event_timeline_reconciliation_report,
    source_event_timeline_reconciliation_report_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def test_builds_pass_report_when_timeline_counts_match_and_anchor_is_present() -> None:
    report = build_source_event_timeline_reconciliation_report(
        expected_timeline_point_count=d("4.000000"),
        captured_timeline_point_count=d("4.000000"),
        conflicting_timestamp_count=d("0.000000"),
        missing_digest_count=d("0.000000"),
        official_anchor_present=True,
    )

    assert report == SourceEventTimelineReconciliationReport(
        expected_timeline_point_count=d("4.000000"),
        captured_timeline_point_count=d("4.000000"),
        conflicting_timestamp_count=d("0.000000"),
        missing_digest_count=d("0.000000"),
        official_anchor_present=True,
        reconciliation_status="pass",
        reason_codes=("source_event_timeline_reconciliation_pass",),
        manual_next_step="document_timeline_reconciliation",
        payload_digest=report.payload_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_conflicts_block_and_missing_or_unanchored_timeline_evidence_watches() -> None:
    conflict_report = build_source_event_timeline_reconciliation_report(
        expected_timeline_point_count=d("5.000000"),
        captured_timeline_point_count=d("5.000000"),
        conflicting_timestamp_count=d("1.000000"),
        missing_digest_count=d("1.000000"),
        official_anchor_present=True,
    )
    assert conflict_report.reconciliation_status == "block"
    assert conflict_report.reason_codes == (
        "timeline_timestamp_conflict_detected",
        "timeline_digest_missing",
    )
    assert conflict_report.manual_next_step == "manual_timeline_timestamp_reconciliation"

    missing_digest_report = build_source_event_timeline_reconciliation_report(
        expected_timeline_point_count=d("3.000000"),
        captured_timeline_point_count=d("3.000000"),
        conflicting_timestamp_count=d("0.000000"),
        missing_digest_count=d("1.000000"),
        official_anchor_present=True,
    )
    assert missing_digest_report.reconciliation_status == "watch"
    assert missing_digest_report.reason_codes == ("timeline_digest_missing",)
    assert missing_digest_report.manual_next_step == "refresh_timeline_digest_evidence"

    unanchored_report = build_source_event_timeline_reconciliation_report(
        expected_timeline_point_count=d("2.000000"),
        captured_timeline_point_count=d("2.000000"),
        conflicting_timestamp_count=d("0.000000"),
        missing_digest_count=d("0.000000"),
        official_anchor_present=False,
    )
    assert unanchored_report.reconciliation_status == "watch"
    assert unanchored_report.reason_codes == ("official_timeline_anchor_missing",)
    assert unanchored_report.manual_next_step == "collect_official_timeline_anchor"


def test_captured_timeline_gap_watches_without_executing_any_action() -> None:
    report = build_source_event_timeline_reconciliation_report(
        expected_timeline_point_count=d("4"),
        captured_timeline_point_count=d("2"),
        conflicting_timestamp_count=d("0"),
        missing_digest_count=d("0"),
        official_anchor_present=True,
    )

    assert report.reconciliation_status == "watch"
    assert report.reason_codes == ("timeline_point_capture_gap",)
    assert report.manual_next_step == "review_missing_timeline_points"


def test_payload_is_json_ready_deterministic_and_digest_validates() -> None:
    report = build_source_event_timeline_reconciliation_report(
        expected_timeline_point_count=d("3"),
        captured_timeline_point_count=d("2"),
        conflicting_timestamp_count=d("0"),
        missing_digest_count=d("1"),
        official_anchor_present=False,
    )

    payload = source_event_timeline_reconciliation_report_payload(report)

    json.dumps(payload, sort_keys=True)
    assert payload == report.public_payload
    assert payload["expected_timeline_point_count"] == "3.000000"
    assert payload["captured_timeline_point_count"] == "2.000000"
    assert payload["conflicting_timestamp_count"] == "0.000000"
    assert payload["missing_digest_count"] == "1.000000"
    assert payload["official_anchor_present"] is False
    assert payload["reconciliation_status"] == "watch"
    assert payload["reason_codes"] == (
        "timeline_digest_missing",
        "official_timeline_anchor_missing",
        "timeline_point_capture_gap",
    )
    assert payload["manual_next_step"] == "refresh_timeline_digest_evidence"
    assert payload["payload_digest"] == report.payload_digest
    assert len(report.payload_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["captured_timeline_point_count"] = "3.000000"
    with pytest.raises(ValueError, match="payload_digest"):
        source_event_timeline_reconciliation_report_payload(tampered_payload)


def test_rejects_non_decimal_inconsistent_counts_flags_and_subclassing() -> None:
    with pytest.raises(ValueError, match="expected_timeline_point_count"):
        build_source_event_timeline_reconciliation_report(
            expected_timeline_point_count=1,
            captured_timeline_point_count=d("1.000000"),
            conflicting_timestamp_count=d("0.000000"),
            missing_digest_count=d("0.000000"),
            official_anchor_present=True,
        )
    with pytest.raises(ValueError, match="captured_timeline_point_count"):
        build_source_event_timeline_reconciliation_report(
            expected_timeline_point_count=d("1.000000"),
            captured_timeline_point_count=_DecimalSubclass("1.000000"),
            conflicting_timestamp_count=d("0.000000"),
            missing_digest_count=d("0.000000"),
            official_anchor_present=True,
        )
    with pytest.raises(ValueError, match="timeline point counts"):
        build_source_event_timeline_reconciliation_report(
            expected_timeline_point_count=d("1.000000"),
            captured_timeline_point_count=d("2.000000"),
            conflicting_timestamp_count=d("0.000000"),
            missing_digest_count=d("0.000000"),
            official_anchor_present=True,
        )
    with pytest.raises(ValueError, match="conflicting_timestamp_count"):
        build_source_event_timeline_reconciliation_report(
            expected_timeline_point_count=d("1.000000"),
            captured_timeline_point_count=d("1.000000"),
            conflicting_timestamp_count=d("2.000000"),
            missing_digest_count=d("0.000000"),
            official_anchor_present=True,
        )
    with pytest.raises(ValueError, match="official_anchor_present"):
        build_source_event_timeline_reconciliation_report(
            expected_timeline_point_count=d("1.000000"),
            captured_timeline_point_count=d("1.000000"),
            conflicting_timestamp_count=d("0.000000"),
            missing_digest_count=d("0.000000"),
            official_anchor_present=1,
        )
    with pytest.raises(ValueError, match="readonly"):
        build_source_event_timeline_reconciliation_report(
            expected_timeline_point_count=d("1.000000"),
            captured_timeline_point_count=d("1.000000"),
            conflicting_timestamp_count=d("0.000000"),
            missing_digest_count=d("0.000000"),
            official_anchor_present=True,
            readonly=False,
        )

    report = build_source_event_timeline_reconciliation_report(
        expected_timeline_point_count=d("1.000000"),
        captured_timeline_point_count=d("1.000000"),
        conflicting_timestamp_count=d("0.000000"),
        missing_digest_count=d("0.000000"),
        official_anchor_present=True,
    )
    with pytest.raises(FrozenInstanceError):
        report.reconciliation_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(SourceEventTimelineReconciliationReport):
            pass


def test_module_has_no_network_persistence_or_execution_surfaces() -> None:
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
        _join_parts("key", "s"),
        _join_parts("sign", "ing"),
        _join_parts("execution"),
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(token in lowered for token in unsafe_terms)
    for field in fields(SourceEventTimelineReconciliationReport):
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

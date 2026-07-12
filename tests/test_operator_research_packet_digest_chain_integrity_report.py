from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.operator_research_packet_digest_chain_integrity_report import (
    OperatorResearchPacketDigestChainIntegrityReport,
    build_operator_research_packet_digest_chain_integrity_report,
    operator_research_packet_digest_chain_integrity_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/operator_research_packet_digest_chain_integrity_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def test_complete_digest_chain_is_report_only_with_stable_public_payload() -> None:
    report = build_operator_research_packet_digest_chain_integrity_report(
        packet_digest_present=True,
        source_digest_count=d("4"),
        missing_source_digest_count=d("0"),
        operator_note_digest_present=True,
        tamper_check_passed=True,
    )
    payload = operator_research_packet_digest_chain_integrity_report_payload(report)
    json.dumps(payload, sort_keys=True)

    assert type(report) is OperatorResearchPacketDigestChainIntegrityReport
    assert report.chain_status == "pass"
    assert report.reason_codes == (
        "operator_research_packet_digest_chain_integrity_pass",
    )
    assert report.manual_next_step == "manual_review_digest_chain_complete"
    assert report.payload_digest == report.public_payload["payload_digest"]
    assert len(report.payload_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload == report.public_payload
    assert payload["source_digest_count"] == "4"
    assert payload["missing_source_digest_count"] == "0"
    assert payload["chain_status"] == "pass"
    assert not any(type(value) is float for value in walk_values(payload))


def test_missing_chain_components_block_manual_research_packet_use() -> None:
    report = build_operator_research_packet_digest_chain_integrity_report(
        packet_digest_present=False,
        source_digest_count=d("3"),
        missing_source_digest_count=d("2"),
        operator_note_digest_present=False,
        tamper_check_passed=False,
    )

    assert report.chain_status == "block"
    assert report.reason_codes == (
        "operator_research_packet_digest_chain_integrity_packet_digest_missing",
        "operator_research_packet_digest_chain_integrity_source_digest_missing",
        "operator_research_packet_digest_chain_integrity_operator_note_digest_missing",
        "operator_research_packet_digest_chain_integrity_tamper_check_failed",
    )
    assert report.manual_next_step == "manual_review_rebuild_digest_chain"
    assert report.public_payload["missing_source_digest_count"] == "2"


def test_incomplete_non_tampered_chain_stays_watch_only() -> None:
    report = build_operator_research_packet_digest_chain_integrity_report(
        packet_digest_present=True,
        source_digest_count=d("0"),
        missing_source_digest_count=d("0"),
        operator_note_digest_present=False,
        tamper_check_passed=True,
    )

    assert report.chain_status == "watch"
    assert report.reason_codes == (
        "operator_research_packet_digest_chain_integrity_source_digest_absent",
        "operator_research_packet_digest_chain_integrity_operator_note_digest_missing",
    )
    assert report.manual_next_step == "manual_review_attach_missing_digests"


def test_report_contract_is_frozen_strict_and_requires_readonly_flags() -> None:
    report = build_operator_research_packet_digest_chain_integrity_report(
        packet_digest_present=True,
        source_digest_count=d("1"),
        missing_source_digest_count=d("0"),
        operator_note_digest_present=True,
        tamper_check_passed=True,
    )

    with pytest.raises(FrozenInstanceError):
        report.chain_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="packet_digest_present"):
        replace(report, packet_digest_present=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_digest_count"):
        replace(report, source_digest_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="missing_source_digest_count"):
        replace(report, missing_source_digest_count=_DecimalSubclass("0"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_payload_rejects_mutated_digest_and_public_numeric_values() -> None:
    report = build_operator_research_packet_digest_chain_integrity_report(
        packet_digest_present=True,
        source_digest_count=d("2"),
        missing_source_digest_count=d("0"),
        operator_note_digest_present=True,
        tamper_check_passed=True,
    )
    payload = operator_research_packet_digest_chain_integrity_report_payload(report)

    tampered = dict(payload)
    tampered["chain_status"] = "watch"
    with pytest.raises(ValueError, match="payload_digest"):
        operator_research_packet_digest_chain_integrity_report_payload(tampered)

    with pytest.raises(ValueError, match="public payload numerics"):
        operator_research_packet_digest_chain_integrity_report_payload(
            {
                **payload,
                "source_digest_count": 2,
            },
        )


def test_owned_module_has_no_runtime_side_effect_or_private_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "live",
        "au" + "th",
        "wallet",
        "order",
        "private" + "_" + "key",
        "api" + "_" + "key",
        "secret" + "_" + "key",
        "sign" + "ature",
        "jsonl",
        "auto" + "matic",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered

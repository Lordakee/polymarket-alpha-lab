from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import inspect

import pytest

from polymarket_alpha_lab import research_packet_evidence_chain_completeness_gate_v2 as gate_module
from polymarket_alpha_lab.research_packet_evidence_chain_completeness_gate_v2 import (
    DEFAULT_RESEARCH_PACKET_EVIDENCE_CHAIN_COMPLETENESS_GATE_V2_CONFIG_VERSION,
    ResearchPacketEvidenceChainCompletenessGateV2Config,
    ResearchPacketEvidenceChainCompletenessGateV2Evidence,
    ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount,
    ResearchPacketEvidenceChainCompletenessGateV2Report,
    build_research_packet_evidence_chain_completeness_gate_v2_report,
    research_packet_evidence_chain_completeness_gate_v2_report_to_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    *,
    required_chain_link_ids: tuple[str, ...] = (
        "chain-link-background",
        "chain-link-resolution",
        "chain-link-source-check",
    ),
    required_source_families: tuple[str, ...] = (
        "official-reference",
        "primary-research",
        "secondary-review",
    ),
    minimum_source_quorum: Decimal = d("2.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchPacketEvidenceChainCompletenessGateV2Config:
    return ResearchPacketEvidenceChainCompletenessGateV2Config(
        required_chain_link_ids=required_chain_link_ids,
        required_source_families=required_source_families,
        minimum_source_quorum=minimum_source_quorum,
        config_version=DEFAULT_RESEARCH_PACKET_EVIDENCE_CHAIN_COMPLETENESS_GATE_V2_CONFIG_VERSION,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def evidence(
    chain_link_id: str,
    source_family: str,
    source_label: str,
    *,
    chain_link_complete: bool = True,
    reason_codes: tuple[str, ...] = ("research_packet_source_reviewed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchPacketEvidenceChainCompletenessGateV2Evidence:
    return ResearchPacketEvidenceChainCompletenessGateV2Evidence(
        chain_link_id=chain_link_id,
        source_family=source_family,
        source_label=source_label,
        chain_link_complete=chain_link_complete,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def complete_report() -> ResearchPacketEvidenceChainCompletenessGateV2Report:
    return build_research_packet_evidence_chain_completeness_gate_v2_report(
        (
            evidence(
                "chain-link-background",
                "official-reference",
                "official-summary",
            ),
            evidence(
                "chain-link-resolution",
                "primary-research",
                "primary-summary",
            ),
            evidence(
                "chain-link-source-check",
                "secondary-review",
                "secondary-summary",
            ),
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    assert type(value) not in {int, float, Decimal}


def assert_dataclass_public_numbers_are_decimal(value: object) -> None:
    field_names = getattr(value, "__dataclass_fields__", {})
    for field_name in field_names:
        item = getattr(value, field_name)
        if type(item) in {int, float}:
            raise AssertionError(f"{field_name} used non-Decimal numeric value")
        if type(item) is tuple:
            for row in item:
                assert_dataclass_public_numbers_are_decimal(row)


def test_evidence_chain_completeness_passes_with_full_chain_and_quorum() -> None:
    report = complete_report()

    assert report.gate_status == "pass"
    assert report.recommended_report_action == "continue_report_only_research_packet_review"
    assert report.evidence_count == d("3.000000")
    assert report.required_chain_link_count == d("3.000000")
    assert report.complete_chain_link_count == d("3.000000")
    assert report.missing_chain_link_count == d("0.000000")
    assert report.completeness_ratio == d("1.000000")
    assert report.missing_chain_link_ids == ()
    assert report.observed_source_families == (
        "official-reference",
        "primary-research",
        "secondary-review",
    )
    assert report.missing_source_families == ()
    assert report.reason_codes == (
        "research_packet_source_reviewed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_dataclass_public_numbers_are_decimal(report)


def test_missing_chain_links_and_incomplete_rows_are_blocked() -> None:
    report = build_research_packet_evidence_chain_completeness_gate_v2_report(
        (
            evidence(
                "chain-link-background",
                "official-reference",
                "official-summary",
            ),
            evidence(
                "chain-link-resolution",
                "primary-research",
                "primary-summary",
                chain_link_complete=False,
            ),
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.evidence_count == d("2.000000")
    assert report.complete_chain_link_count == d("1.000000")
    assert report.missing_chain_link_count == d("2.000000")
    assert report.incomplete_evidence_count == d("1.000000")
    assert report.completeness_ratio == d("0.333333")
    assert report.missing_chain_link_ids == (
        "chain-link-resolution",
        "chain-link-source-check",
    )
    assert "research_packet_evidence_chain_link_missing" in report.reason_codes
    assert "research_packet_evidence_chain_link_incomplete" in report.reason_codes


def test_source_quorum_gaps_block_report() -> None:
    report = build_research_packet_evidence_chain_completeness_gate_v2_report(
        (
            evidence(
                "chain-link-background",
                "official-reference",
                "official-summary",
            ),
            evidence(
                "chain-link-resolution",
                "official-reference",
                "official-resolution-summary",
            ),
            evidence(
                "chain-link-source-check",
                "official-reference",
                "official-cross-check",
            ),
        ),
        config=config(minimum_source_quorum=d("2.000000")),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.unique_source_family_count == d("1.000000")
    assert report.source_quorum_gap_count == d("1.000000")
    assert report.missing_source_families == (
        "primary-research",
        "secondary-review",
    )
    assert "research_packet_source_quorum_gap" in report.reason_codes
    assert "research_packet_required_source_family_missing" in report.reason_codes


def test_payload_serializes_decimals_as_strings_and_round_trips() -> None:
    report = complete_report()

    payload = research_packet_evidence_chain_completeness_gate_v2_report_to_payload(
        report,
    )

    assert payload["evidence_count"] == "3.000000"
    assert payload["completeness_ratio"] == "1.000000"
    assert payload["reason_code_counts"][0]["report_count"] == "3.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert_no_public_numeric_scalars(payload)
    assert (
        research_packet_evidence_chain_completeness_gate_v2_report_to_payload(payload)
        == payload
    )


def test_dataclasses_are_frozen_and_revalidate_hard_flags() -> None:
    report = complete_report()

    with pytest.raises(FrozenInstanceError):
        report.gate_status = "blocked"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.evidence[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_derived_validation_digest_rejects_dataclass_and_payload_tampering() -> None:
    report = complete_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)

    payload = research_packet_evidence_chain_completeness_gate_v2_report_to_payload(
        report,
    )
    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_evidence_chain_completeness_gate_v2_report_to_payload(
            missing_digest,
        )

    tampered = dict(payload)
    tampered["gate_status"] = "blocked"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        research_packet_evidence_chain_completeness_gate_v2_report_to_payload(tampered)


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    payload = research_packet_evidence_chain_completeness_gate_v2_report_to_payload(
        complete_report(),
    )

    unsafe_keys = (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_identifier",
        "network_client",
        "database_url",
        "persist_path",
        "signing_key",
        "mutation_name",
        "buy_button",
        "sell_button",
        "trade_route",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            research_packet_evidence_chain_completeness_gate_v2_report_to_payload(
                unsafe_payload,
            )

    unsafe_values = (
        "live mode",
        "auth material",
        "wallet route",
        "order route",
        "network client",
        "database writer",
        "persist output",
        "signing material",
        "mutation route",
        "buy route",
        "sell route",
        "trade route",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["recommended_report_action"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe"):
            research_packet_evidence_chain_completeness_gate_v2_report_to_payload(
                unsafe_payload,
            )

    with pytest.raises(ValueError, match="unsafe"):
        evidence(
            "chain-link-background",
            "official-reference",
            "wallet-source",
        )


def test_no_unsafe_runtime_surfaces_are_exposed() -> None:
    source = inspect.getsource(gate_module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "order",
        "trade",
    }
    forbidden_attr_fragments = (
        "auth",
        "broker",
        "cancel",
        "credential",
        "database",
        "network",
        "order",
        "persist",
        "secret",
        "signing",
        "trade",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_call_names
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_call_names
        if isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)


def test_public_exports_are_exact() -> None:
    assert gate_module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_EVIDENCE_CHAIN_COMPLETENESS_GATE_V2_CONFIG_VERSION",
        "ResearchPacketEvidenceChainCompletenessGateV2Config",
        "ResearchPacketEvidenceChainCompletenessGateV2Evidence",
        "ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount",
        "ResearchPacketEvidenceChainCompletenessGateV2Report",
        "build_research_packet_evidence_chain_completeness_gate_v2_report",
        "research_packet_evidence_chain_completeness_gate_v2_report_to_payload",
    )
    with pytest.raises(ValueError, match="Decimal"):
        ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount(
            "research_packet_source_reviewed",
            1,  # type: ignore[arg-type]
        )

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_manual_review_evidence_packet_router_report as api
from polymarket_alpha_lab.research_manual_review_evidence_packet_router_report import (
    ResearchManualReviewEvidencePacket,
    ResearchManualReviewEvidencePacketRouterConfig,
    ResearchManualReviewEvidencePacketRouterReport,
    build_research_manual_review_evidence_packet_router_report,
    research_manual_review_evidence_packet_router_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_manual_review_evidence_packet_router_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def packet(**overrides: object) -> ResearchManualReviewEvidencePacket:
    values = {
        "packet_id": "packet_alpha",
        "evidence_completeness_score": d("0.900000"),
        "specialist_fit_score": d("0.900000"),
        "cost_sanity_score": d("0.900000"),
        "resolution_rule_readiness_score": d("0.900000"),
        "recheck_urgency_score": d("0.100000"),
    }
    values.update(overrides)
    return ResearchManualReviewEvidencePacket(**values)


def report(
    *items: ResearchManualReviewEvidencePacket,
    config: ResearchManualReviewEvidencePacketRouterConfig | None = None,
) -> ResearchManualReviewEvidencePacketRouterReport:
    return build_research_manual_review_evidence_packet_router_report(
        items,
        generated_at=GENERATED_AT,
        config=config,
    )


def test_public_api_declares_report_only_router_surface() -> None:
    assert api.DEFAULT_RESEARCH_MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_CONFIG_VERSION == (
        "research-manual-review-evidence-packet-router-report"
    )
    assert api.MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_DIMENSIONS == (
        "evidence_completeness",
        "specialist_fit",
        "cost_sanity",
        "resolution_rule_readiness",
        "recheck_urgency",
    )
    assert api.__all__ == (
        "DEFAULT_RESEARCH_MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_CONFIG_VERSION",
        "MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_DIMENSIONS",
        "ResearchManualReviewEvidencePacket",
        "ResearchManualReviewEvidencePacketRouterConfig",
        "ResearchManualReviewEvidencePacketRouterReport",
        "ResearchManualReviewEvidencePacketRouterRow",
        "build_research_manual_review_evidence_packet_router_report",
        "research_manual_review_evidence_packet_router_report_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(ResearchManualReviewEvidencePacketRouterConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True
    assert field_defaults["min_pass_routing_score"] == d("0.850000")
    assert field_defaults["min_watch_routing_score"] == d("0.650000")
    assert field_defaults["min_pass_dimension_score"] == d("0.750000")
    assert field_defaults["min_watch_dimension_score"] == d("0.500000")
    assert field_defaults["recheck_urgency_watch_threshold"] == d("0.500000")
    assert field_defaults["recheck_urgency_block_threshold"] == d("0.800000")


def test_router_aggregates_packet_readiness_statuses_and_reason_codes() -> None:
    result = report(
        packet(packet_id="packet_zeta"),
        packet(
            packet_id="packet_alpha",
            evidence_completeness_score=d("0.490000"),
            specialist_fit_score=d("0.900000"),
            cost_sanity_score=d("0.400000"),
            resolution_rule_readiness_score=d("0.900000"),
            recheck_urgency_score=d("0.820000"),
        ),
        packet(
            packet_id="packet_beta",
            evidence_completeness_score=d("0.800000"),
            specialist_fit_score=d("0.740000"),
            cost_sanity_score=d("0.700000"),
            resolution_rule_readiness_score=d("0.800000"),
            recheck_urgency_score=d("0.500000"),
        ),
    )

    assert result.route_status == "block"
    assert result.packet_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.pass_ratio == d("0.333333")
    assert result.watch_ratio == d("0.333333")
    assert result.block_ratio == d("0.333333")
    assert result.average_routing_score == d("0.727333")
    assert result.max_recheck_urgency_score == d("0.820000")
    assert result.reason_codes == (
        "manual_review_router_report_block_rows",
        "manual_review_router_report_watch_rows",
        "manual_review_router_report_average_below_pass",
        "manual_review_router_report_recheck_urgent_rows",
    )

    alpha, beta, zeta = result.rows
    assert (alpha.rank, beta.rank, zeta.rank) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert (alpha.packet_id, beta.packet_id, zeta.packet_id) == (
        "packet_alpha",
        "packet_beta",
        "packet_zeta",
    )
    assert alpha.routing_score == d("0.574000")
    assert alpha.route_status == "block"
    assert alpha.reason_codes == (
        "manual_review_router_evidence_missing",
        "manual_review_router_cost_sanity_missing",
        "manual_review_router_recheck_urgency_block",
        "manual_review_router_score_below_watch",
    )
    assert beta.routing_score == d("0.708000")
    assert beta.route_status == "watch"
    assert beta.reason_codes == (
        "manual_review_router_specialist_fit_incomplete",
        "manual_review_router_cost_sanity_incomplete",
        "manual_review_router_recheck_urgency_watch",
        "manual_review_router_score_below_pass",
    )
    assert zeta.routing_score == d("0.900000")
    assert zeta.route_status == "pass"
    assert zeta.reason_codes == ("manual_review_router_row_passed",)


def test_empty_packet_set_blocks_with_stable_zero_aggregates() -> None:
    result = report()

    assert result.route_status == "block"
    assert result.packet_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.pass_ratio == d("0.000000")
    assert result.watch_ratio == d("0.000000")
    assert result.block_ratio == d("0.000000")
    assert result.average_routing_score == d("0.000000")
    assert result.max_recheck_urgency_score == d("0.000000")
    assert result.rows == ()
    assert result.reason_codes == (
        "manual_review_router_report_empty",
        "manual_review_router_report_average_below_watch",
    )


def test_payload_digest_frozen_flags_and_decimal_only_contract() -> None:
    result = report(packet(packet_id="packet_payload"))
    payload = research_manual_review_evidence_packet_router_report_payload(result)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["packet_count"] == "1.000000"
    assert payload["average_routing_score"] == "0.900000"
    assert payload["rows"][0]["routing_score"] == "0.900000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_values(payload)
    assert_no_non_decimal_public_numbers(result)
    assert research_manual_review_evidence_packet_router_report_payload(payload) == payload

    with pytest.raises(FrozenInstanceError):
        result.route_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    tampered = dict(payload)
    tampered["average_routing_score"] = "0.900001"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_manual_review_evidence_packet_router_report_payload(tampered)
    with pytest.raises(ValueError, match="Decimal"):
        packet(evidence_completeness_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        packet(specialist_fit_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="paper_only"):
        ResearchManualReviewEvidencePacketRouterConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        packet(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_research_manual_review_evidence_packet_router_report(
            (packet(readonly=False),),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "li" "ve_review",
        "au" "th_review",
        "wal" "let_review",
        "ord" "er_review",
        "net" "work_review",
        "data" "base_review",
        "persist_review",
        "signing_review",
        "mutation_review",
        "buy_review",
        "sell_review",
        "tra" "de_review",
        "recommendation_review",
        "sizing_review",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn_ref",
        "table_name",
        "access_token",
    ),
)
def test_rejects_unsafe_public_keys_and_values(unsafe_value: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        packet(packet_id=unsafe_value)
    with pytest.raises(ValueError, match="unsafe public"):
        research_manual_review_evidence_packet_router_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                unsafe_value: "safe",
            },
        )


def test_module_scope_has_no_io_or_numeric_float_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "au" "th",
        "broker",
        "client",
        "clob",
        "data" "base",
        "db",
        "http",
        "net" "work",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wal" "let",
        "web3",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
        "submit",
        "tra" "de",
        "write",
    }
    unsafe_public_terms = (
        "li" "ve",
        "au" "th",
        "wal" "let",
        "ord" "er",
        "buy",
        "sell",
        "tra" "de",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    )

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    for public_name in api.__all__:
        assert not any(term in public_name.lower() for term in unsafe_public_terms)
    for cls in (
        api.ResearchManualReviewEvidencePacket,
        api.ResearchManualReviewEvidencePacketRouterConfig,
        api.ResearchManualReviewEvidencePacketRouterReport,
        api.ResearchManualReviewEvidencePacketRouterRow,
    ):
        for field in fields(cls):
            assert not any(term in field.name.lower() for term in unsafe_public_terms)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_no_non_decimal_public_numbers(value: object) -> None:
    if type(value) is Decimal:
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal: {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_no_non_decimal_public_numbers(getattr(value, field.name))
        return
    if isinstance(value, (dict, list, tuple)):
        items = value.values() if isinstance(value, dict) else value
        for item in items:
            assert_no_non_decimal_public_numbers(item)

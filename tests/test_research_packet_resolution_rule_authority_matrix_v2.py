from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


class _TaggedDecimal(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_resolution_rule_authority_matrix_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(
    packet_id: str,
    *,
    market_id: str = "market-main",
    event_slug: str = "event-main",
    category: str = "politics",
    polymarket_rule_source_count: str = "1",
    official_primary_source_count: str = "1",
    official_secondary_source_count: str = "1",
    proxy_source_count: str = "0",
    conflicting_rule_source_count: str = "0",
):
    return api().ResearchPacketResolutionRuleAuthorityMatrixV2Input(
        packet_id=packet_id,
        market_id=market_id,
        event_slug=event_slug,
        category=category,
        polymarket_rule_source_count=d(polymarket_rule_source_count),
        official_primary_source_count=d(official_primary_source_count),
        official_secondary_source_count=d(official_secondary_source_count),
        proxy_source_count=d(proxy_source_count),
        conflicting_rule_source_count=d(conflicting_rule_source_count),
    )


def default_inputs():
    return (
        evidence(
            "packet-blocked",
            market_id="market-3",
            event_slug="event-c",
            category="macro",
            polymarket_rule_source_count="0",
            official_primary_source_count="0",
            official_secondary_source_count="1",
            proxy_source_count="3",
            conflicting_rule_source_count="1",
        ),
        evidence(
            "packet-watch",
            market_id="market-2",
            event_slug="event-b",
            category="sports",
            official_primary_source_count="1",
            official_secondary_source_count="0",
            proxy_source_count="2",
        ),
        evidence(
            "packet-pass",
            market_id="market-1",
            event_slug="event-a",
            category="politics",
            polymarket_rule_source_count="2",
            official_primary_source_count="1",
            official_secondary_source_count="1",
            proxy_source_count="0",
        ),
    )


def build(rows=None):
    return api().build_research_packet_resolution_rule_authority_matrix_v2_report(
        default_inputs() if rows is None else rows,
    )


def assert_payload_has_no_decimal_float_or_int(value: Any) -> None:
    assert type(value) is not Decimal
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_decimal_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_decimal_float_or_int(item)


def test_builds_authority_rows_deterministically_with_scores_statuses_and_rollups() -> None:
    module = api()

    report = build(tuple(reversed(default_inputs())))

    assert is_dataclass(report)
    assert report.config_version == (
        "research-packet-resolution-rule-authority-matrix-v2"
    )
    assert report.packet_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.missing_polymarket_rule_count == d("1")
    assert report.missing_official_primary_count == d("1")
    assert report.conflicting_rule_count == d("1")
    assert report.min_authority_coverage_score == d("0.400000")
    assert report.report_status == "block"
    assert report.reason_codes == (
        "report_status_block",
        "polymarket_rule_missing",
        "official_primary_missing",
        "conflicting_rules_present",
        "proxy_dependency_present",
    )
    assert report.reason_code_counts == (
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="authority_row_pass",
            count=d("1"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="authority_row_watch",
            count=d("1"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="authority_row_block",
            count=d("1"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="conflicting_rules_absent",
            count=d("2"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="conflicting_rules_present",
            count=d("1"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="official_primary_available",
            count=d("2"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="official_primary_missing",
            count=d("1"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="polymarket_rule_available",
            count=d("2"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="polymarket_rule_missing",
            count=d("1"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="proxy_dependency_absent",
            count=d("1"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="proxy_dependency_high",
            count=d("1"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="proxy_dependency_present",
            count=d("1"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="secondary_official_missing",
            count=d("1"),
        ),
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code="secondary_official_present",
            count=d("2"),
        ),
    )
    assert tuple(row.packet_id for row in report.authority_rows) == (
        "packet-blocked",
        "packet-pass",
        "packet-watch",
    )
    assert tuple(row.status for row in report.authority_rows) == (
        "block",
        "pass",
        "watch",
    )

    blocked = report.authority_rows[0]
    assert blocked == module.ResearchPacketResolutionRuleAuthorityMatrixV2Row(
        packet_id="packet-blocked",
        market_id="market-3",
        event_slug="event-c",
        category="macro",
        polymarket_rule_source_count=d("0"),
        official_primary_source_count=d("0"),
        official_secondary_source_count=d("1"),
        proxy_source_count=d("3"),
        conflicting_rule_source_count=d("1"),
        authority_coverage_score=d("0.400000"),
        proxy_dependency_ratio=d("0.750000"),
        status="block",
        reason_codes=(
            "polymarket_rule_missing",
            "official_primary_missing",
            "secondary_official_present",
            "conflicting_rules_present",
            "proxy_dependency_high",
            "authority_row_block",
        ),
        derived_validation_digest=blocked.derived_validation_digest,
    )

    passed = report.authority_rows[1]
    assert passed.authority_coverage_score == d("1.000000")
    assert passed.proxy_dependency_ratio == d("0.000000")
    assert passed.reason_codes == (
        "polymarket_rule_available",
        "official_primary_available",
        "secondary_official_present",
        "conflicting_rules_absent",
        "proxy_dependency_absent",
        "authority_row_pass",
    )

    watched = report.authority_rows[2]
    assert watched.authority_coverage_score == d("0.800000")
    assert watched.proxy_dependency_ratio == d("0.500000")
    assert watched.reason_codes == (
        "polymarket_rule_available",
        "official_primary_available",
        "secondary_official_missing",
        "conflicting_rules_absent",
        "proxy_dependency_present",
        "authority_row_watch",
    )
    assert len({row.derived_validation_digest for row in report.authority_rows}) == 3


def test_payload_is_safe_json_decimal_stringified_and_digest_validated() -> None:
    module = api()
    report = build()

    payload = module.research_packet_resolution_rule_authority_matrix_v2_payload(report)

    assert payload["packet_count"] == "3"
    assert payload["min_authority_coverage_score"] == "0.400000"
    assert payload["authority_rows"][0]["authority_coverage_score"] == "0.400000"
    assert payload["authority_rows"][0]["proxy_dependency_ratio"] == "0.750000"
    assert payload["reason_code_counts"][0] == {
        "reason_code": "authority_row_pass",
        "count": "1",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert len(payload["authority_rows"][0]["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert_payload_has_no_decimal_float_or_int(payload)
    assert (
        module.validate_research_packet_resolution_rule_authority_matrix_v2_payload(
            payload,
        )
        == payload
    )

    tampered = dict(payload)
    tampered["authority_rows"] = [dict(row) for row in payload["authority_rows"]]
    tampered["authority_rows"][0]["proxy_dependency_ratio"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.validate_research_packet_resolution_rule_authority_matrix_v2_payload(
            tampered,
        )
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, report_status="pass")


def test_empty_input_returns_empty_status_and_zero_decimal_rollups() -> None:
    report = build(())

    assert report.packet_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.missing_polymarket_rule_count == d("0")
    assert report.missing_official_primary_count == d("0")
    assert report.conflicting_rule_count == d("0")
    assert report.min_authority_coverage_score == d("0.000000")
    assert report.report_status == "empty"
    assert report.reason_codes == ("report_status_empty",)
    assert report.reason_code_counts == ()
    assert report.authority_rows == ()


def test_frozen_decimal_only_hard_flags_and_validation_invariants() -> None:
    source = evidence("packet-alpha")
    report = build()
    reason_count = report.reason_code_counts[0]

    for value in (source, report, reason_count, *report.authority_rows):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(source, readonly=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(reason_count, paper_only=False)
    with pytest.raises(ValueError, match="polymarket_rule_source_count must be a Decimal"):
        source.__class__(
            packet_id="packet-int",
            market_id="market-main",
            event_slug="event-main",
            category="politics",
            polymarket_rule_source_count=1,  # type: ignore[arg-type]
            official_primary_source_count=d("1"),
            official_secondary_source_count=d("1"),
            proxy_source_count=d("0"),
            conflicting_rule_source_count=d("0"),
        )
    with pytest.raises(ValueError, match="official_primary_source_count must be a Decimal"):
        source.__class__(
            packet_id="packet-subclass",
            market_id="market-main",
            event_slug="event-main",
            category="politics",
            polymarket_rule_source_count=d("1"),
            official_primary_source_count=_TaggedDecimal("1"),
            official_secondary_source_count=d("1"),
            proxy_source_count=d("0"),
            conflicting_rule_source_count=d("0"),
        )
    with pytest.raises(ValueError, match="proxy_source_count must be nonnegative"):
        evidence("packet-negative", proxy_source_count="-1")
    with pytest.raises(ValueError, match="authority rows must contain exact"):
        build((object(),))
    with pytest.raises(ValueError, match="reason_codes must be canonical"):
        replace(
            report.authority_rows[0],
            reason_codes=tuple(reversed(report.authority_rows[0].reason_codes)),
        )


def test_rejects_unsafe_public_payload_terms() -> None:
    module = api()
    payload = module.research_packet_resolution_rule_authority_matrix_v2_payload(build())

    unsafe_keys = (
        "li" "ve_mode",
        "au" "th_token",
        "wa" "llet_address",
        "or" "der_id",
        "net" "work_client",
        "data" "base_url",
        "per" "sist_path",
        "sign" "ing_key",
        "muta" "tion_endpoint",
        "bu" "y_flag",
        "se" "ll_flag",
        "tra" "de_path",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public field"):
            module.validate_research_packet_resolution_rule_authority_matrix_v2_payload(
                unsafe_payload,
            )

    unsafe_values = (
        "li" "ve mode",
        "au" "th token",
        "wa" "llet field",
        "or" "der detail",
        "net" "work call",
        "data" "base field",
        "per" "sist record",
        "sign" "ing request",
        "muta" "tion path",
        "bu" "y button",
        "se" "ll action",
        "tra" "de route",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_rows = [dict(row) for row in payload["authority_rows"]]
        unsafe_rows[0]["event_slug"] = unsafe_value
        unsafe_payload["authority_rows"] = unsafe_rows
        with pytest.raises(ValueError, match="unsafe public value"):
            module.validate_research_packet_resolution_rule_authority_matrix_v2_payload(
                unsafe_payload,
            )

    with pytest.raises(ValueError, match="unsafe public value"):
        evidence("packet-unsafe", event_slug="wa" "llet-feed")


def test_module_is_phase1_readonly_report_only_and_unwired_from_side_effects() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert (
        module.ResearchPacketResolutionRuleAuthorityMatrixV2Input.__dataclass_params__.frozen
    )
    assert (
        module.ResearchPacketResolutionRuleAuthorityMatrixV2Row.__dataclass_params__.frozen
    )
    assert (
        module.ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert (
        module.ResearchPacketResolutionRuleAuthorityMatrixV2Report.__dataclass_params__
        .frozen
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_RESOLUTION_RULE_AUTHORITY_MATRIX_V2_CONFIG_VERSION",
        "AUTHORITY_MATRIX_STATUSES",
        "ROW_REASON_CODES",
        "REPORT_REASON_CODES",
        "ResearchPacketResolutionRuleAuthorityMatrixV2Input",
        "ResearchPacketResolutionRuleAuthorityMatrixV2Row",
        "ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount",
        "ResearchPacketResolutionRuleAuthorityMatrixV2Report",
        "build_research_packet_resolution_rule_authority_matrix_v2_report",
        "research_packet_resolution_rule_authority_matrix_v2_payload",
        "validate_research_packet_resolution_rule_authority_matrix_v2_payload",
    )

    forbidden_import_roots = {
        "asyncio",
        "http",
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "commit",
        "connect",
        "create_order",
        "execute",
        "open",
        "place_order",
        "read_text",
        "request",
        "rollback",
        "submit_order",
        "write_text",
    }
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert {name.split(".", 1)[0] for name in imported_modules}.isdisjoint(
        forbidden_import_roots,
    )
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

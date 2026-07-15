from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.probability_event_evidence_freshness_quorum_rollup_report as api
from polymarket_alpha_lab.probability_event_evidence_freshness_quorum_rollup_report import (
    ProbabilityEventEvidenceFreshnessQuorumRollupReport,
    build_probability_event_evidence_freshness_quorum_rollup_report,
    probability_event_evidence_freshness_quorum_rollup_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_evidence_freshness_quorum_rollup_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventEvidenceFreshnessQuorumRollupReport:
    values = {
        "official_anchor_age_hours": d("1.000000"),
        "independent_source_count": d("3.000000"),
        "fresh_independent_source_count": d("3.000000"),
        "required_quorum_count": d("2.000000"),
        "contradiction_status": "none",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return build_probability_event_evidence_freshness_quorum_rollup_report(**values)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) is int or type(value) is float or type(value) is Decimal:
        pytest.fail(f"payload contains runtime numeric value: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for forbidden in (
                "live",
                "auth",
                "wallet",
                "position",
                "database",
                "network",
                "order",
            ):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_fresh_quorum_report_passes_with_decimal_payload_and_digest() -> None:
    result = report()

    assert is_dataclass(result)
    assert result.quorum_freshness_status == "pass"
    assert result.reason_codes == ("evidence_freshness_quorum_pass",)
    assert result.manual_next_step == "proceed_with_readonly_evidence_packet"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.digest) == 64

    payload = probability_event_evidence_freshness_quorum_rollup_report_payload(
        result,
    )
    assert payload == result.public_payload
    assert payload["official_anchor_age_hours"] == "1.000000"
    assert payload["independent_source_count"] == "3.000000"
    assert payload["fresh_independent_source_count"] == "3.000000"
    assert payload["required_quorum_count"] == "2.000000"
    assert payload["contradiction_status"] == "none"
    assert payload["quorum_freshness_status"] == "pass"
    assert payload["reason_codes"] == ["evidence_freshness_quorum_pass"]
    assert payload["manual_next_step"] == "proceed_with_readonly_evidence_packet"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["digest"] == result.digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_stale_official_anchor_cannot_pass_even_with_quorum() -> None:
    result = report(official_anchor_age_hours=d("7.000000"))

    assert result.quorum_freshness_status == "watch"
    assert result.reason_codes == ("official_anchor_age_watch_stale",)
    assert result.manual_next_step == "refresh_official_anchor_before_packet_use"


def test_expired_official_anchor_blocks_even_with_fresh_sources() -> None:
    result = report(official_anchor_age_hours=d("25.000000"))

    assert result.quorum_freshness_status == "block"
    assert result.reason_codes == ("official_anchor_age_expired",)
    assert result.manual_next_step == "refresh_evidence_and_rebuild_packet_before_reuse"


def test_insufficient_fresh_quorum_cannot_pass() -> None:
    result = report(
        independent_source_count=d("3.000000"),
        fresh_independent_source_count=d("1.000000"),
        required_quorum_count=d("2.000000"),
    )

    assert result.quorum_freshness_status == "block"
    assert result.reason_codes == ("fresh_independent_source_quorum_gap",)
    assert result.manual_next_step == "add_fresh_independent_sources_before_packet_use"


def test_contradictions_force_manual_review_or_block() -> None:
    minor = report(contradiction_status="minor")

    assert minor.quorum_freshness_status == "watch"
    assert minor.reason_codes == ("minor_contradiction_present",)
    assert minor.manual_next_step == "manual_review_contradictions_before_packet_use"

    unresolved = report(contradiction_status="unresolved")
    assert unresolved.quorum_freshness_status == "block"
    assert unresolved.reason_codes == ("unresolved_contradiction_present",)
    assert unresolved.manual_next_step == "resolve_contradictions_before_packet_use"


def test_combined_failures_preserve_reason_priority() -> None:
    result = report(
        official_anchor_age_hours=d("8.000000"),
        independent_source_count=d("1.000000"),
        fresh_independent_source_count=d("0.000000"),
        required_quorum_count=d("2.000000"),
        contradiction_status="unresolved",
    )

    assert result.quorum_freshness_status == "block"
    assert result.reason_codes == (
        "official_anchor_age_watch_stale",
        "independent_source_quorum_gap",
        "fresh_independent_source_quorum_gap",
        "unresolved_contradiction_present",
    )
    assert result.manual_next_step == "resolve_contradictions_before_packet_use"


def test_frozen_flags_decimal_validation_and_report_consistency() -> None:
    result = report()

    assert result.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        result.quorum_freshness_status = "block"  # type: ignore[misc]

    hints = get_type_hints(ProbabilityEventEvidenceFreshnessQuorumRollupReport)
    for item in fields(result):
        if item.name.endswith("_hours") or item.name.endswith("_count"):
            assert hints[item.name] is Decimal
            assert type(getattr(result, item.name)) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="official_anchor_age_hours"):
        report(official_anchor_age_hours=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="independent_source_count"):
        report(independent_source_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fresh_independent_source_count"):
        report(fresh_independent_source_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="required_quorum_count"):
        report(required_quorum_count=d("1.500000"))
    with pytest.raises(ValueError, match="fresh_independent_source_count"):
        report(
            independent_source_count=d("1.000000"),
            fresh_independent_source_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="contradiction_status"):
        report(contradiction_status="needs review")
    with pytest.raises(ValueError, match="quorum_freshness_status"):
        replace(result, quorum_freshness_status="ready")
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(result, manual_next_step="continue_monitoring")


def test_public_payload_rejects_tampered_reason_and_numeric_values() -> None:
    result = report()

    object.__setattr__(result, "reason_codes", ("unsupported_reason",))
    with pytest.raises(ValueError, match="reason_code"):
        probability_event_evidence_freshness_quorum_rollup_report_payload(result)

    rebuilt = report()
    object.__setattr__(rebuilt, "required_quorum_count", 2)
    with pytest.raises(ValueError, match="numeric payload values"):
        probability_event_evidence_freshness_quorum_rollup_report_payload(rebuilt)


def test_pure_readonly_report_only_module_has_no_io_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "wallet",
        "private_key",
        "authentication",
        "database",
        "network",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "urlopen",
        "connect(",
        "execute(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "__import__",
        "open",
        "connect",
        "execute",
        "request",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def test_public_api_excludes_forbidden_surfaces() -> None:
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "database",
        "persist",
        "store",
        "order",
        "trade",
        "request",
        "http",
        "broker",
        "private_key",
        "api_key",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for item in fields(ProbabilityEventEvidenceFreshnessQuorumRollupReport):
        lowered = item.name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

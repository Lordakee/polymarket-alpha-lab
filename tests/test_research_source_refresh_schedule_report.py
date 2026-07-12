from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_refresh_schedule_report"
GENERATED_AT = datetime(2026, 7, 11, 18, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "official_api_refresh_ready": True,
        "agent_reach_refresh_ready": True,
        "scrapling_refresh_ready": True,
        "source_freshness_sla_ready": True,
        "manual_fallback_ready": True,
        "redaction_ready": True,
        "operator_safety_ready": True,
        "supabase_persistence_ready": True,
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_research_source_refresh_schedule_report(**values)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_all_required_sources_ready_returns_pass_band_and_digest_payload() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceRefreshScheduleReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.source_refresh_ready is True
    assert report.refresh_band == "ready"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "research_source_refresh_schedule_all_sources_ready",
    )
    assert report.ready_ratio == d("1.000000")
    assert report.ready_source_count == d("8.000000")
    assert report.required_source_count == d("8.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == module.research_source_refresh_schedule_report_payload(report)
    assert report.digest == report.derived_validation_digest
    assert payload["source_refresh_ready"] is True
    assert payload["refresh_band"] == "ready"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["ready_source_count"] == "8.000000"
    assert payload["required_source_count"] == "8.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["derived_validation_digest"] == report.digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_values(payload)
    assert_payload_has_no_leaked_values(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)
    module.validate_research_source_refresh_schedule_public_payload(payload)


def test_partial_readiness_separates_blockers_from_attention_reasons() -> None:
    report = build_report(
        official_api_refresh_ready=False,
        scrapling_refresh_ready=False,
        source_freshness_sla_ready=False,
        manual_fallback_ready=False,
        redaction_ready=False,
        supabase_persistence_ready=False,
    )

    assert report.source_refresh_ready is False
    assert report.refresh_band == "blocked"
    assert report.ready_ratio == d("0.250000")
    assert report.ready_source_count == d("2.000000")
    assert report.required_source_count == d("8.000000")
    assert report.blocked_reason_codes == (
        "research_source_refresh_schedule_official_api_blocked",
        "research_source_refresh_schedule_source_freshness_sla_blocked",
        "research_source_refresh_schedule_manual_fallback_blocked",
        "research_source_refresh_schedule_redaction_blocked",
        "research_source_refresh_schedule_supabase_persistence_blocked",
    )
    assert report.attention_reason_codes == (
        "research_source_refresh_schedule_scrapling_attention",
        "research_source_refresh_schedule_ready_ratio_blocked",
    )

    payload = report.public_payload
    assert payload["source_readiness"] == {
        "official_api_refresh_ready": False,
        "agent_reach_refresh_ready": True,
        "scrapling_refresh_ready": False,
        "source_freshness_sla_ready": False,
        "manual_fallback_ready": False,
        "redaction_ready": False,
        "operator_safety_ready": True,
        "supabase_persistence_ready": False,
    }
    assert payload["blocked_reason_codes"] == list(report.blocked_reason_codes)
    assert payload["attention_reason_codes"] == list(report.attention_reason_codes)


def test_watch_band_allows_optional_research_tool_gaps() -> None:
    report = build_report(
        agent_reach_refresh_ready=False,
        scrapling_refresh_ready=False,
    )

    assert report.source_refresh_ready is False
    assert report.refresh_band == "watch"
    assert report.ready_ratio == d("0.750000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "research_source_refresh_schedule_agent_reach_attention",
        "research_source_refresh_schedule_scrapling_attention",
        "research_source_refresh_schedule_ready_ratio_watch",
    )


def test_flags_decimal_inputs_and_frozen_digest_validation_are_enforced() -> None:
    module = api()
    report = build_report()

    with pytest.raises(FrozenInstanceError):
        report.refresh_band = "blocked"
    with pytest.raises(ValueError, match="paper_only"):
        build_report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        build_report(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at=datetime(2026, 7, 11, 18, 30))
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(report, ready_ratio=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="required_source_count"):
        replace(report, required_source_count=8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_REFRESH_SCHEDULE_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_REFRESH_SCHEDULE_REFRESH_BANDS",
        "ResearchSourceRefreshScheduleReport",
        "build_research_source_refresh_schedule_report",
        "research_source_refresh_schedule_report_digest",
        "research_source_refresh_schedule_report_payload",
        "validate_research_source_refresh_schedule_public_payload",
        "validate_research_source_refresh_schedule_report_digest",
    )


def test_public_payload_rejects_tampering_numerics_and_unsafe_surfaces() -> None:
    module = api()
    report = build_report()
    payload = report.public_payload

    tampered = dict(payload)
    tampered["refresh_band"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_refresh_schedule_public_payload(tampered)

    numeric_payload = dict(payload)
    numeric_payload["ready_ratio"] = Decimal("1.000000")
    with pytest.raises(ValueError, match="numeric"):
        module.validate_research_source_refresh_schedule_public_payload(numeric_payload)

    unsafe_keys = {
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
        "recommendation",
    }
    report_fields = {field.name for field in fields(type(report))}
    assert unsafe_keys.isdisjoint(report_fields)
    for unsafe_payload in (
        {"candidate_id": "safe"},
        {"safe": "https://example.invalid/source"},
        {"safe": "wallet token"},
        {"safe": "live order trade recommendation"},
        {"table_name": "public_summary"},
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_source_refresh_schedule_public_payload(
                {
                    **payload,
                    **unsafe_payload,
                    "derived_validation_digest": payload["derived_validation_digest"],
                },
            )


def test_module_scope_is_pure_report_only_without_external_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
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
                "submit_order",
                "place_order",
                "recommend",
                "size_position",
            }

    forbidden_import_fragments = (
        "auth",
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "wallet",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    forbidden_source_fragments = (
        "private_key",
        "wallet",
        "place_order",
        "submit_order",
        "cancel_order",
        "auth",
        "requests.",
        "httpx.",
        "psycopg",
        "supabase.create",
        "live trading",
    )
    lowered_source = source.lower()
    assert not any(fragment in lowered_source for fragment in forbidden_source_fragments)


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_numeric_values(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_public_numeric_values(child)
    else:
        assert type(value) not in (int, float, Decimal)


def assert_payload_has_no_leaked_values(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert isinstance(key, str)
            assert_payload_has_no_leaked_values(key)
            assert_payload_has_no_leaked_values(child)
    elif isinstance(value, list):
        for child in value:
            assert_payload_has_no_leaked_values(child)
    elif isinstance(value, str):
        lowered = value.lower()
        forbidden = (
            "candidate-",
            "candidate_id",
            "market_id",
            "market_slug",
            "question",
            "source_url",
            "source_text",
            "http://",
            "https://",
            "postgres://",
            "token",
            "wallet",
            "order",
            "trade",
            "live_surface",
            "recommendation",
        )
        assert not any(fragment in lowered for fragment in forbidden)

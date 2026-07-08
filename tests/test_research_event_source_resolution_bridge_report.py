from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_source_resolution_bridge_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_source_resolution_bridge_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_BRIDGE_REPORT_CONFIG_VERSION
        ),
        "min_source_quorum_ratio": d("0.800000"),
        "block_source_quorum_ratio": d("0.500000"),
        "min_rule_linkage_completeness_ratio": d("1.000000"),
        "block_rule_linkage_completeness_ratio": d("0.500000"),
        "min_freshness_ratio": d("0.800000"),
        "block_freshness_ratio": d("0.500000"),
        "watch_ambiguity_pressure_ratio": d("0.250000"),
        "block_ambiguity_pressure_ratio": d("0.600000"),
        "watch_manual_escalation_urgency_ratio": d("0.350000"),
        "block_manual_escalation_urgency_ratio": d("0.700000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchEventSourceResolutionBridgeConfig(**values)


def bridge_scope(
    scope: str,
    *,
    required_sources: str,
    bridged_sources: str,
    required_rule_links: str,
    bridged_rule_links: str,
    evidence_items: str,
    fresh_evidence: str,
    ambiguous_evidence: str = "0.000000",
    manual_escalations: str = "0.000000",
):
    module = api()
    return module.ResearchEventSourceResolutionBridgeAggregate(
        event_scope=scope,
        required_source_count=d(required_sources),
        bridged_source_count=d(bridged_sources),
        required_rule_link_count=d(required_rule_links),
        bridged_rule_link_count=d(bridged_rule_links),
        evidence_item_count=d(evidence_items),
        fresh_evidence_count=d(fresh_evidence),
        ambiguous_evidence_count=d(ambiguous_evidence),
        manual_escalation_count=d(manual_escalations),
    )


def report(*aggregates: object, cfg: object | None = None):
    module = api()
    return module.build_research_event_source_resolution_bridge_report(
        aggregates,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_blocks_with_zero_pressure_and_hard_flags() -> None:
    module = api()
    bridge_report = report()

    assert type(bridge_report) is module.ResearchEventSourceResolutionBridgeReport
    assert is_dataclass(bridge_report)
    assert bridge_report.__dataclass_params__.frozen is True
    assert bridge_report.generated_at == GENERATED_AT
    assert bridge_report.config_version == (
        module.DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_BRIDGE_REPORT_CONFIG_VERSION
    )
    assert bridge_report.event_scope_count == ZERO
    assert bridge_report.required_source_count == ZERO
    assert bridge_report.bridged_source_count == ZERO
    assert bridge_report.required_rule_link_count == ZERO
    assert bridge_report.bridged_rule_link_count == ZERO
    assert bridge_report.evidence_item_count == ZERO
    assert bridge_report.fresh_evidence_count == ZERO
    assert bridge_report.ambiguous_evidence_count == ZERO
    assert bridge_report.manual_escalation_count == ZERO
    assert bridge_report.pass_count == ZERO
    assert bridge_report.watch_count == ZERO
    assert bridge_report.block_count == ZERO
    assert bridge_report.source_quorum_ratio == ZERO
    assert bridge_report.rule_linkage_completeness_ratio == ZERO
    assert bridge_report.freshness_ratio == ZERO
    assert bridge_report.ambiguity_pressure_ratio == ZERO
    assert bridge_report.manual_escalation_urgency_ratio == ZERO
    assert bridge_report.status == "block"
    assert bridge_report.reason_codes == (
        "no_event_source_resolution_bridge_scopes",
    )
    assert bridge_report.rows == ()
    assert bridge_report.paper_only is True
    assert bridge_report.report_only is True
    assert bridge_report.readonly is True
    assert len(bridge_report.derived_validation_digest) == 64


def test_complete_quorum_rule_linkage_and_fresh_evidence_pass_deterministically() -> None:
    module = api()
    bridge_report = report(
        bridge_scope(
            "event-bridge-alpha",
            required_sources="3.000000",
            bridged_sources="3.000000",
            required_rule_links="4.000000",
            bridged_rule_links="4.000000",
            evidence_items="4.000000",
            fresh_evidence="4.000000",
        ),
        bridge_scope(
            "event-bridge-beta",
            required_sources="2.000000",
            bridged_sources="2.000000",
            required_rule_links="2.000000",
            bridged_rule_links="2.000000",
            evidence_items="2.000000",
            fresh_evidence="2.000000",
        ),
    )

    payload = module.research_event_source_resolution_bridge_report_payload(
        bridge_report,
    )
    repeat_payload = module.research_event_source_resolution_bridge_report_payload(
        bridge_report,
    )

    assert bridge_report.status == "pass"
    assert bridge_report.event_scope_count == d("2.000000")
    assert bridge_report.required_source_count == d("5.000000")
    assert bridge_report.bridged_source_count == d("5.000000")
    assert bridge_report.required_rule_link_count == d("6.000000")
    assert bridge_report.bridged_rule_link_count == d("6.000000")
    assert bridge_report.evidence_item_count == d("6.000000")
    assert bridge_report.fresh_evidence_count == d("6.000000")
    assert bridge_report.pass_count == d("2.000000")
    assert bridge_report.watch_count == ZERO
    assert bridge_report.block_count == ZERO
    assert bridge_report.source_quorum_ratio == ONE
    assert bridge_report.rule_linkage_completeness_ratio == ONE
    assert bridge_report.freshness_ratio == ONE
    assert bridge_report.reason_codes == ("event_source_resolution_bridge_pass",)
    assert tuple(row.event_scope for row in bridge_report.rows) == (
        "event-bridge-alpha",
        "event-bridge-beta",
    )
    assert all(
        type(row) is module.ResearchEventSourceResolutionBridgeRow
        for row in bridge_report.rows
    )
    assert all(row.status == "pass" for row in bridge_report.rows)
    assert payload == repeat_payload
    assert payload["derived_validation_digest"] == (
        bridge_report.derived_validation_digest
    )
    assert payload["rows"][0]["source_quorum_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _has_forbidden_public_surface(payload)
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))
    assert json.dumps(payload, sort_keys=True) == json.dumps(repeat_payload, sort_keys=True)
    assert module.validate_research_event_source_resolution_bridge_report_payload(payload)


def test_bridge_pressures_roll_up_to_watch_metrics_and_block_scope() -> None:
    bridge_report = report(
        bridge_scope(
            "event-bridge-watch",
            required_sources="4.000000",
            bridged_sources="3.000000",
            required_rule_links="4.000000",
            bridged_rule_links="3.000000",
            evidence_items="4.000000",
            fresh_evidence="3.000000",
            ambiguous_evidence="1.000000",
            manual_escalations="2.000000",
        ),
        bridge_scope(
            "event-bridge-block",
            required_sources="5.000000",
            bridged_sources="2.000000",
            required_rule_links="5.000000",
            bridged_rule_links="2.000000",
            evidence_items="5.000000",
            fresh_evidence="2.000000",
            ambiguous_evidence="4.000000",
            manual_escalations="4.000000",
        ),
    )

    assert bridge_report.status == "block"
    assert bridge_report.event_scope_count == d("2.000000")
    assert bridge_report.required_source_count == d("9.000000")
    assert bridge_report.bridged_source_count == d("5.000000")
    assert bridge_report.required_rule_link_count == d("9.000000")
    assert bridge_report.bridged_rule_link_count == d("5.000000")
    assert bridge_report.evidence_item_count == d("9.000000")
    assert bridge_report.fresh_evidence_count == d("5.000000")
    assert bridge_report.ambiguous_evidence_count == d("5.000000")
    assert bridge_report.manual_escalation_count == d("6.000000")
    assert bridge_report.pass_count == ZERO
    assert bridge_report.watch_count == ONE
    assert bridge_report.block_count == ONE
    assert bridge_report.source_quorum_ratio == d("0.555556")
    assert bridge_report.rule_linkage_completeness_ratio == d("0.555556")
    assert bridge_report.freshness_ratio == d("0.555556")
    assert bridge_report.ambiguity_pressure_ratio == d("0.555556")
    assert bridge_report.manual_escalation_urgency_ratio == d("0.666667")
    assert bridge_report.reason_codes == (
        "source_quorum_watch",
        "rule_linkage_completeness_watch",
        "freshness_watch",
        "ambiguity_pressure_watch",
        "manual_escalation_urgency_watch",
        "event_source_resolution_bridge_scope_block",
    )

    block_scope, watch_scope = bridge_report.rows
    assert (block_scope.event_scope, block_scope.status) == (
        "event-bridge-block",
        "block",
    )
    assert (watch_scope.event_scope, watch_scope.status) == (
        "event-bridge-watch",
        "watch",
    )
    assert watch_scope.reason_codes == (
        "source_quorum_watch",
        "rule_linkage_completeness_watch",
        "freshness_watch",
        "ambiguity_pressure_watch",
        "manual_escalation_urgency_watch",
    )
    assert block_scope.reason_codes == (
        "source_quorum_block",
        "rule_linkage_completeness_block",
        "freshness_block",
        "ambiguity_pressure_block",
        "manual_escalation_urgency_block",
    )


def test_validation_rejects_bad_numerics_counts_flags_and_payloads() -> None:
    module = api()
    with pytest.raises(ValueError, match="min_source_quorum_ratio"):
        config(min_source_quorum_ratio=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_ambiguity_pressure_ratio"):
        config(watch_ambiguity_pressure_ratio=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="block_source_quorum_ratio"):
        config(block_source_quorum_ratio=d("0.800000"))
    with pytest.raises(ValueError, match="event_scope"):
        bridge_scope(
            "market-slug-leak",
            required_sources="1.000000",
            bridged_sources="1.000000",
            required_rule_links="1.000000",
            bridged_rule_links="1.000000",
            evidence_items="1.000000",
            fresh_evidence="1.000000",
        )
    with pytest.raises(ValueError, match="required_source_count"):
        bridge_scope(
            "scope",
            required_sources="0.000000",
            bridged_sources="0.000000",
            required_rule_links="1.000000",
            bridged_rule_links="1.000000",
            evidence_items="1.000000",
            fresh_evidence="1.000000",
        )
    with pytest.raises(ValueError, match="bridged_source_count"):
        bridge_scope(
            "scope",
            required_sources="1.000000",
            bridged_sources="2.000000",
            required_rule_links="1.000000",
            bridged_rule_links="1.000000",
            evidence_items="1.000000",
            fresh_evidence="1.000000",
        )
    with pytest.raises(ValueError, match="bridged_rule_link_count"):
        bridge_scope(
            "scope",
            required_sources="1.000000",
            bridged_sources="1.000000",
            required_rule_links="1.000000",
            bridged_rule_links="2.000000",
            evidence_items="1.000000",
            fresh_evidence="1.000000",
        )
    with pytest.raises(ValueError, match="fresh_evidence_count"):
        bridge_scope(
            "scope",
            required_sources="1.000000",
            bridged_sources="1.000000",
            required_rule_links="1.000000",
            bridged_rule_links="1.000000",
            evidence_items="1.000000",
            fresh_evidence="2.000000",
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            bridge_scope(
                "scope",
                required_sources="1.000000",
                bridged_sources="1.000000",
                required_rule_links="1.000000",
                bridged_rule_links="1.000000",
                evidence_items="1.000000",
                fresh_evidence="1.000000",
            ),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_research_event_source_resolution_bridge_report_payload(
            {
                "source_" + "url": "blocked",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_public_dataclasses_are_frozen_exact_and_source_has_no_unsafe_surfaces() -> None:
    module = api()
    bridge_report = report(
        bridge_scope(
            "scope",
            required_sources="1.000000",
            bridged_sources="1.000000",
            required_rule_links="1.000000",
            bridged_rule_links="1.000000",
            evidence_items="1.000000",
            fresh_evidence="1.000000",
        ),
    )

    public_classes = (
        module.ResearchEventSourceResolutionBridgeConfig,
        module.ResearchEventSourceResolutionBridgeAggregate,
        module.ResearchEventSourceResolutionBridgeRow,
        module.ResearchEventSourceResolutionBridgeReport,
    )
    assert all(is_dataclass(public_class) for public_class in public_classes)
    assert all(public_class.__dataclass_params__.frozen is True for public_class in public_classes)
    for public_class in public_classes:
        for field in fields(public_class):
            if field.name.endswith("_count") or field.name.endswith("_ratio"):
                assert field.type in (Decimal, "Decimal")

    with pytest.raises(FrozenInstanceError):
        bridge_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        bridge_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(bridge_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="pass_count"):
        replace(bridge_report, pass_count=ZERO)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(bridge_report, derived_validation_digest="0" * 64)

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "raw_" + "url",
        "source_" + "url",
        "source_" + "text",
        "market_" + "id",
        "market_" + "slug",
        "candidate_" + "id",
        "ques" + "tion",
        "dsn",
        "table_name",
        "database",
        "private_token",
        "network",
        "wallet",
        "order",
        "live",
        "sizing",
        "recommendation",
        "trade",
        "trading",
    )
    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _has_forbidden_public_surface(value: Any) -> bool:
    forbidden = (
        "raw_" + "url",
        "source_" + "url",
        "source_" + "text",
        "market_" + "id",
        "market_" + "slug",
        "candidate_" + "id",
        "ques" + "tion",
        "dsn",
        "table_name",
        "private_token",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).lower() for term in forbidden):
                return True
            if _has_forbidden_public_surface(item):
                return True
    if isinstance(value, list):
        return any(_has_forbidden_public_surface(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(term in lowered for term in forbidden)
    return False

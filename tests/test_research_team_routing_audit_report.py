from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_event_type_router import (
    ResearchMarketEventTypeInput,
    route_research_market_event_type,
)
from polymarket_alpha_lab.research_team_capacity_planner import (
    ResearchTeamCapacityPlannerConfig,
    ResearchTeamCapacityPlannerInput,
    build_research_team_capacity_plan,
)
from polymarket_alpha_lab.research_team_domain_memory_summary import (
    ResearchTeamDomainMemoryObservation,
    ResearchTeamDomainMemorySummaryConfig,
    build_research_team_domain_memory_summary,
)
from polymarket_alpha_lab.research_team_domain_playbook import (
    ResearchTeamDomainPlaybookConfig,
    build_default_research_team_domain_playbook_report,
)
from polymarket_alpha_lab.research_team_routing_audit_report import (
    DEFAULT_RESEARCH_TEAM_ROUTING_AUDIT_CONFIG_VERSION,
    ROUTING_AUDIT_COMPONENT_CODES,
    ROUTING_AUDIT_STATUSES,
    ResearchTeamRoutingAuditComponent,
    ResearchTeamRoutingAuditConfig,
    ResearchTeamRoutingAuditReport,
    build_research_team_routing_audit_report,
    research_team_routing_audit_report_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_routing_audit_report.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def event_route(
    *,
    public_event_type: str = "bitcoin_etf_flow",
    public_category_hint: str = "finance.crypto",
    public_feature_tags: tuple[str, ...] = ("bitcoin", "etf"),
):
    return route_research_market_event_type(
        ResearchMarketEventTypeInput(
            public_event_type=public_event_type,
            public_category_hint=public_category_hint,
            public_feature_tags=public_feature_tags,
        ),
    )


def playbook_report(*, domain_ids=None):
    return build_default_research_team_domain_playbook_report(
        config=ResearchTeamDomainPlaybookConfig(
            required_domain_ids=(
                domain_ids
                if domain_ids is not None
                else (
                    "politics",
                    "macro",
                    "crypto",
                    "equity_index",
                    "gold",
                    "soccer",
                    "basketball",
                )
            ),
        ),
    )


def capacity_input(**overrides: object) -> ResearchTeamCapacityPlannerInput:
    values = {
        "team_code": "crypto_research_team",
        "domain_code": "crypto",
        "specialist_role_code": "domain_research",
        "queued_item_count": d("1"),
        "active_item_count": d("1"),
        "capacity_item_count": d("6"),
        "sla_breach_count": d("0"),
        "required_domain_count": d("1"),
        "covered_domain_count": d("1"),
        "required_specialist_count": d("1"),
        "staffed_specialist_count": d("1"),
    }
    values.update(overrides)
    return ResearchTeamCapacityPlannerInput(**values)


def capacity_report(*items: ResearchTeamCapacityPlannerInput):
    return build_research_team_capacity_plan(
        items,
        generated_at=GENERATED_AT,
        config=ResearchTeamCapacityPlannerConfig(),
    )


def memory_observation(**overrides: object) -> ResearchTeamDomainMemoryObservation:
    values = {
        "domain_id": "crypto",
        "team_id": "crypto_research_team",
        "experience_count": d("30"),
        "error_pattern_count": d("2"),
        "postmortem_count": d("10"),
        "high_quality_postmortem_count": d("9"),
        "memory_quality_score": d("0.800000"),
    }
    values.update(overrides)
    return ResearchTeamDomainMemoryObservation(**values)


def memory_report(*items: ResearchTeamDomainMemoryObservation, domain_ids=("crypto",)):
    return build_research_team_domain_memory_summary(
        items,
        generated_at=GENERATED_AT,
        config=ResearchTeamDomainMemorySummaryConfig(domain_ids=domain_ids),
    )


def audit_report(
    *,
    route=None,
    p_report=None,
    c_report=None,
    m_report=None,
) -> ResearchTeamRoutingAuditReport:
    return build_research_team_routing_audit_report(
        event_route=route if route is not None else event_route(),
        playbook_report=p_report if p_report is not None else playbook_report(),
        capacity_report=c_report if c_report is not None else capacity_report(capacity_input()),
        memory_report=m_report if m_report is not None else memory_report(memory_observation()),
        config=ResearchTeamRoutingAuditConfig(),
    )


def assert_no_float_int_or_unsafe_surface(value: Any) -> None:
    forbidden = (
        "raw",
        "candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "market question",
        "market_question",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "source ref",
        "source url",
        "source text",
        "http://",
        "https://",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "recommendation",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            lowered_key = key.casefold()
            assert not any(term in lowered_key for term in forbidden), lowered_key
            assert_no_float_int_or_unsafe_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_int_or_unsafe_surface(item)
        return
    if isinstance(value, float):
        raise AssertionError(f"unexpected float {value!r}")
    if type(value) is int:
        raise AssertionError(f"unexpected int {value!r}")
    if type(value) is str:
        lowered = value.casefold()
        assert not any(term in lowered for term in forbidden), lowered


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_passes_when_sanitized_route_playbook_capacity_and_memory_align() -> None:
    report = audit_report()
    payload = research_team_routing_audit_report_payload(report)

    assert report.config_version == DEFAULT_RESEARCH_TEAM_ROUTING_AUDIT_CONFIG_VERSION
    assert ROUTING_AUDIT_STATUSES == ("pass", "watch", "block")
    assert ROUTING_AUDIT_COMPONENT_CODES == (
        "sanitized_event_type",
        "domain_playbook",
        "team_capacity",
        "domain_memory",
    )
    assert report.audit_status == "pass"
    assert report.routed_domain_code == "crypto"
    assert report.audited_component_count == d("4.000000")
    assert report.pass_count == d("4.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.reason_codes == ("routing_audit_pass",)
    assert tuple(component.component_code for component in report.components) == ROUTING_AUDIT_COMPONENT_CODES
    assert tuple(component.component_status for component in report.components) == (
        "pass",
        "pass",
        "pass",
        "pass",
    )
    assert payload["audited_component_count"] == "4.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_int_or_unsafe_surface(payload)
    json.dumps(payload, sort_keys=True)


def test_maps_router_queue_aliases_to_playbook_memory_and_capacity_domains() -> None:
    route = event_route(
        public_event_type="index_close",
        public_category_hint="finance.equity.indices",
        public_feature_tags=("spx",),
    )
    report = audit_report(
        route=route,
        c_report=capacity_report(
            capacity_input(
                team_code="equity_index_research_team",
                domain_code="equities",
            ),
        ),
        m_report=memory_report(
            memory_observation(
                domain_id="equity_index",
                team_id="equity_index_research_team",
            ),
            domain_ids=("equity_index",),
        ),
    )

    assert report.audit_status == "pass"
    assert report.routed_domain_code == "equity_index"
    assert tuple(component.audited_domain_code for component in report.components) == (
        "equity_index",
        "equity_index",
        "equity_index",
        "equity_index",
    )


def test_missing_or_blocked_component_blocks_audit_without_live_surface() -> None:
    report = audit_report(
        route=event_route(
            public_event_type="nba_finals_result",
            public_category_hint="sports.basketball",
            public_feature_tags=("nba",),
        ),
        c_report=capacity_report(),
        m_report=memory_report(domain_ids=("basketball",)),
    )

    assert report.audit_status == "block"
    assert report.routed_domain_code == "basketball"
    assert report.pass_count == d("2.000000")
    assert report.block_count == d("2.000000")
    assert report.reason_codes == ("routing_audit_block_components",)

    by_component = {component.component_code: component for component in report.components}
    assert by_component["team_capacity"].component_status == "block"
    assert by_component["team_capacity"].reason_codes == ("team_capacity_missing",)
    assert by_component["domain_memory"].component_status == "block"
    assert by_component["domain_memory"].reason_codes == ("domain_memory_block",)
    assert_no_float_int_or_unsafe_surface(report.payload)


def test_ambiguous_sanitized_event_routes_to_watch_without_assignment() -> None:
    route = event_route(
        public_event_type="inflation_bitcoin_cross_signal",
        public_category_hint="public.unspecified",
        public_feature_tags=("bitcoin", "inflation"),
    )
    report = audit_report(
        route=route,
        c_report=capacity_report(capacity_input()),
        m_report=memory_report(memory_observation()),
    )

    assert report.audit_status == "watch"
    assert report.routed_domain_code is None
    assert report.watch_count == d("4.000000")
    assert tuple(component.observed_status for component in report.components) == (
        "watch",
        None,
        None,
        None,
    )
    assert report.components[0].reason_codes == (
        "sanitized_event_type_watch",
        "routed_domain_unassigned",
    )
    assert report.components[1].reason_codes == ("domain_playbook_unassigned_domain",)
    assert report.components[2].reason_codes == ("team_capacity_unassigned_domain",)
    assert report.components[3].reason_codes == ("domain_memory_unassigned_domain",)


def test_dataclasses_are_frozen_strictly_typed_and_decimal_only() -> None:
    cfg = ResearchTeamRoutingAuditConfig()
    component = audit_report().components[0]
    report = audit_report()

    for value in (cfg, component, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="row_count must be exactly Decimal"):
        replace(component, row_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="row_count must be exactly Decimal"):
        replace(component, row_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="component_code"):
        replace(component, component_code="unknown_component")
    with pytest.raises(ValueError, match="audit_status must match components"):
        replace(report, audit_status="watch")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(cfg, paper_only=False)
    with pytest.raises(ValueError, match="event_route"):
        build_research_team_routing_audit_report(
            event_route="crypto",  # type: ignore[arg-type]
            playbook_report=playbook_report(),
            capacity_report=capacity_report(capacity_input()),
            memory_report=memory_report(memory_observation()),
        )


def test_public_payload_rejects_leaks_flag_downgrades_and_digest_tampering() -> None:
    report = audit_report()
    payload = dict(report.payload)

    payload["raw_candidate_id"] = "abc"
    with pytest.raises(ValueError, match="unsafe public field"):
        research_team_routing_audit_report_payload(payload)

    payload = dict(report.payload)
    payload["note"] = "buy recommendation"
    with pytest.raises(ValueError, match="unsafe public value"):
        research_team_routing_audit_report_payload(payload)

    payload = dict(report.payload)
    payload["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        research_team_routing_audit_report_payload(payload)

    payload = dict(report.payload)
    payload["audit_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_routing_audit_report_payload(payload)

    payload = dict(report.payload)
    payload["pass_count"] = 4
    with pytest.raises(ValueError, match="Decimal-derived"):
        research_team_routing_audit_report_payload(payload)


def test_public_models_include_hard_flags_and_exclude_sensitive_field_names() -> None:
    forbidden_fields = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    }
    for cls in (
        ResearchTeamRoutingAuditConfig,
        ResearchTeamRoutingAuditComponent,
        ResearchTeamRoutingAuditReport,
    ):
        field_names = {field.name for field in fields(cls)}
        assert {"paper_only", "report_only", "readonly"}.issubset(field_names)
        assert not forbidden_fields.intersection(field_names)


def test_output_is_deterministic_and_module_is_isolated_report_only() -> None:
    first = audit_report()
    second = audit_report()

    assert first == second
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module.split(".")[0])

    assert imported_names.isdisjoint(
        {
            "httpx",
            "requests",
            "socket",
            "urllib",
            "psycopg",
            "psycopg2",
            "supabase",
            "sqlalchemy",
        },
    )

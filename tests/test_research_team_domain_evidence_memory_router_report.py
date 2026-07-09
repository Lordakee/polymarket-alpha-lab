from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = "src/polymarket_alpha_lab/research_team_domain_evidence_memory_router_report.py"


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def _api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_evidence_memory_router_report",
    )


def _route(
    api: Any,
    domain_label: str,
    team_label: str,
    *,
    memory_match_count: Decimal,
    evidence_item_count: Decimal,
    independent_evidence_count: Decimal,
    required_independent_evidence_count: Decimal,
    stale_memory_count: Decimal,
    memory_item_count: Decimal,
    unresolved_conflict_count: Decimal,
) -> Any:
    return api.ResearchTeamDomainEvidenceMemoryRouterInput(
        domain_label=domain_label,
        team_label=team_label,
        memory_match_count=memory_match_count,
        evidence_item_count=evidence_item_count,
        independent_evidence_count=independent_evidence_count,
        required_independent_evidence_count=required_independent_evidence_count,
        stale_memory_count=stale_memory_count,
        memory_item_count=memory_item_count,
        unresolved_conflict_count=unresolved_conflict_count,
    )


def test_builds_team_domain_evidence_memory_router_report() -> None:
    api = _api()

    report = api.build_research_team_domain_evidence_memory_router_report(
        (
            _route(
                api,
                "politics",
                "resolution_research",
                memory_match_count=Decimal("4"),
                evidence_item_count=Decimal("4"),
                independent_evidence_count=Decimal("3"),
                required_independent_evidence_count=Decimal("3"),
                stale_memory_count=Decimal("0"),
                memory_item_count=Decimal("4"),
                unresolved_conflict_count=Decimal("0"),
            ),
            _route(
                api,
                "crypto_btc",
                "onchain_research",
                memory_match_count=Decimal("2"),
                evidence_item_count=Decimal("4"),
                independent_evidence_count=Decimal("1"),
                required_independent_evidence_count=Decimal("3"),
                stale_memory_count=Decimal("3"),
                memory_item_count=Decimal("4"),
                unresolved_conflict_count=Decimal("2"),
            ),
            _route(
                api,
                "sports",
                "injury_research",
                memory_match_count=Decimal("3"),
                evidence_item_count=Decimal("4"),
                independent_evidence_count=Decimal("2"),
                required_independent_evidence_count=Decimal("3"),
                stale_memory_count=Decimal("1"),
                memory_item_count=Decimal("4"),
                unresolved_conflict_count=Decimal("1"),
            ),
        ),
        config=api.ResearchTeamDomainEvidenceMemoryRouterReportConfig(),
        generated_at=GENERATED_AT,
    )

    assert type(report) is api.ResearchTeamDomainEvidenceMemoryRouterReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_ROUTER_REPORT_CONFIG_VERSION
    )
    assert report.router_status == "block"
    assert report.route_count == Decimal("3.000000")
    assert report.pass_route_count == Decimal("1.000000")
    assert report.watch_route_count == Decimal("1.000000")
    assert report.block_route_count == Decimal("1.000000")
    assert report.average_readiness_score == Decimal("0.708333")
    assert report.lowest_readiness_score == Decimal("0.395833")
    assert report.lowest_memory_match_ratio == Decimal("0.500000")
    assert report.lowest_independence_ratio == Decimal("0.333333")
    assert report.max_stale_memory_ratio == Decimal("0.750000")
    assert report.max_conflict_pressure_ratio == Decimal("0.500000")
    assert report.reason_codes == (
        "research_team_domain_evidence_memory_router_block_routes_present",
        "research_team_domain_evidence_memory_router_watch_routes_present",
    )
    assert report.reason_code_counts == (
        api.ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
            reason_code="research_team_domain_evidence_memory_router_memory_match_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
            reason_code="research_team_domain_evidence_memory_router_independence_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
            reason_code="research_team_domain_evidence_memory_router_stale_memory_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
            reason_code="research_team_domain_evidence_memory_router_conflict_pressure_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
            reason_code="research_team_domain_evidence_memory_router_memory_match_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
            reason_code="research_team_domain_evidence_memory_router_independence_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
            reason_code="research_team_domain_evidence_memory_router_stale_memory_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
            reason_code="research_team_domain_evidence_memory_router_conflict_pressure_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
            reason_code="research_team_domain_evidence_memory_router_ready",
            count=Decimal("1.000000"),
        ),
    )
    assert tuple((row.domain_label, row.team_label, row.router_status) for row in report.rows) == (
        ("crypto_btc", "onchain_research", "block"),
        ("politics", "resolution_research", "pass"),
        ("sports", "injury_research", "watch"),
    )

    crypto = report.rows[0]
    assert crypto.memory_match_ratio == Decimal("0.500000")
    assert crypto.independence_ratio == Decimal("0.333333")
    assert crypto.stale_memory_ratio == Decimal("0.750000")
    assert crypto.conflict_pressure_ratio == Decimal("0.500000")
    assert crypto.readiness_score == Decimal("0.395833")
    assert crypto.reason_codes == (
        "research_team_domain_evidence_memory_router_memory_match_block",
        "research_team_domain_evidence_memory_router_independence_block",
        "research_team_domain_evidence_memory_router_stale_memory_block",
        "research_team_domain_evidence_memory_router_conflict_pressure_block",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_digest_is_deterministic_decimal_only_and_public_safe() -> None:
    api = _api()
    first_rows = (
        _route(
            api,
            "sports",
            "injury_research",
            memory_match_count=Decimal("3"),
            evidence_item_count=Decimal("4"),
            independent_evidence_count=Decimal("2"),
            required_independent_evidence_count=Decimal("3"),
            stale_memory_count=Decimal("1"),
            memory_item_count=Decimal("4"),
            unresolved_conflict_count=Decimal("1"),
        ),
        _route(
            api,
            "politics",
            "resolution_research",
            memory_match_count=Decimal("4"),
            evidence_item_count=Decimal("4"),
            independent_evidence_count=Decimal("3"),
            required_independent_evidence_count=Decimal("3"),
            stale_memory_count=Decimal("0"),
            memory_item_count=Decimal("4"),
            unresolved_conflict_count=Decimal("0"),
        ),
    )
    second_rows = tuple(reversed(first_rows))

    report = api.build_research_team_domain_evidence_memory_router_report(
        first_rows,
        config=api.ResearchTeamDomainEvidenceMemoryRouterReportConfig(),
        generated_at=GENERATED_AT,
    )
    rebuilt = api.build_research_team_domain_evidence_memory_router_report(
        second_rows,
        config=api.ResearchTeamDomainEvidenceMemoryRouterReportConfig(),
        generated_at=GENERATED_AT,
    )

    assert rebuilt.derived_validation_digest == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    payload = api.research_team_domain_evidence_memory_router_report_payload(report)
    assert api.research_team_domain_evidence_memory_router_report_payload(payload) == payload
    assert api.validate_research_team_domain_evidence_memory_router_public_payload(payload) is True
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["route_count"] == "2.000000"
    assert payload["average_readiness_score"] == "0.864584"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["domain_label"] == "politics"
    assert payload["rows"][0]["team_label"] == "resolution_research"
    assert payload["rows"][0]["memory_match_count"] == "4.000000"
    assert payload["rows"][0]["paper_only"] is True
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in encoded.lower()
    _assert_no_float_values(payload)

    tampered = dict(payload)
    tampered["average_readiness_score"] = "0.500000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_team_domain_evidence_memory_router_report_payload(tampered)

    internally_inconsistent = json.loads(json.dumps(payload))
    internally_inconsistent["route_count"] = "99.000000"
    internally_inconsistent["derived_validation_digest"] = api._report_digest_from_values(
        api._payload_without_digest(internally_inconsistent),
    )
    with pytest.raises(ValueError, match="route_count must match rows"):
        api.validate_research_team_domain_evidence_memory_router_public_payload(
            internally_inconsistent,
        )


def test_validates_decimal_inputs_status_consistency_flags_and_safe_labels() -> None:
    api = _api()
    report = api.build_research_team_domain_evidence_memory_router_report(
        (
            _route(
                api,
                "politics",
                "resolution_research",
                memory_match_count=Decimal("1"),
                evidence_item_count=Decimal("1"),
                independent_evidence_count=Decimal("1"),
                required_independent_evidence_count=Decimal("1"),
                stale_memory_count=Decimal("0"),
                memory_item_count=Decimal("1"),
                unresolved_conflict_count=Decimal("0"),
            ),
        ),
        config=api.ResearchTeamDomainEvidenceMemoryRouterReportConfig(),
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert {row.router_status for row in report.rows} <= {"pass", "watch", "block"}
    with pytest.raises(FrozenInstanceError):
        report.router_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="memory_match_count must be a Decimal"):
        replace(report.rows[0], memory_match_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_match_count must not exceed"):
        replace(report.rows[0], memory_match_count=Decimal("2.000000"))
    with pytest.raises(ValueError, match="router_status must be pass, watch, or block"):
        replace(report.rows[0], router_status="hold")
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_research_team_domain_evidence_memory_router_report(
            (),
            config=api.ResearchTeamDomainEvidenceMemoryRouterReportConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="memory_match_watch_threshold must be a Decimal"):
        api.ResearchTeamDomainEvidenceMemoryRouterReportConfig(
            memory_match_watch_threshold=_DecimalSubclass("0.800000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(api.ResearchTeamDomainEvidenceMemoryRouterReportConfig(), paper_only=False)
    with pytest.raises(ValueError, match="team_label must be public"):
        _route(
            api,
            "politics",
            "tok" "en_review",
            memory_match_count=Decimal("1"),
            evidence_item_count=Decimal("1"),
            independent_evidence_count=Decimal("1"),
            required_independent_evidence_count=Decimal("1"),
            stale_memory_count=Decimal("0"),
            memory_item_count=Decimal("1"),
            unresolved_conflict_count=Decimal("0"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, average_readiness_score=Decimal("0.500000"))
    with pytest.raises(ValueError, match="readonly"):
        api.research_team_domain_evidence_memory_router_report_payload(
            {**report.payload, "readonly": False},
        )


def test_public_contract_is_frozen_decimal_only_report_only_and_in_memory() -> None:
    api = _api()
    public_types = {
        "ResearchTeamDomainEvidenceMemoryRouterReportConfig",
        "ResearchTeamDomainEvidenceMemoryRouterInput",
        "ResearchTeamDomainEvidenceMemoryRouterRow",
        "ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount",
        "ResearchTeamDomainEvidenceMemoryRouterReport",
    }
    for name in public_types:
        cls = getattr(api, name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    report = api.build_research_team_domain_evidence_memory_router_report(
        (
            _route(
                api,
                "politics",
                "resolution_research",
                memory_match_count=Decimal("1"),
                evidence_item_count=Decimal("1"),
                independent_evidence_count=Decimal("1"),
                required_independent_evidence_count=Decimal("1"),
                stale_memory_count=Decimal("0"),
                memory_item_count=Decimal("1"),
                unresolved_conflict_count=Decimal("0"),
            ),
        ),
        config=api.ResearchTeamDomainEvidenceMemoryRouterReportConfig(),
        generated_at=GENERATED_AT,
    )
    decimal_fields = {
        "route_count",
        "pass_route_count",
        "watch_route_count",
        "block_route_count",
        "average_readiness_score",
        "lowest_readiness_score",
        "lowest_memory_match_ratio",
        "lowest_independence_ratio",
        "max_stale_memory_ratio",
        "max_conflict_pressure_ratio",
    }
    for field_name in decimal_fields:
        assert type(getattr(report, field_name)) is Decimal
    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if field.name.endswith("_count") or field.name.endswith("_ratio"):
                assert type(value) is Decimal

    tree = ast.parse(open(MODULE_PATH, encoding="utf-8").read())
    forbidden_import_roots = {
        "asyncio",
        "httpx",
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
    forbidden_call_names = {"__import__", "eval", "exec", "open", "print"}
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name is not None:
                calls.add(name)
    assert not (imports & forbidden_import_roots)
    assert not (calls & forbidden_call_names)

    text = open(MODULE_PATH, encoding="utf-8").read().lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "credential",
        "private_key",
        "secret",
        "order",
        "live",
        "trade",
        "broker",
        "buy",
        "sell",
        "request",
        "submit",
        "supabase",
        "sqlite",
        "postgres",
        "insert",
        "update",
        "delete",
        "commit",
        "cursor",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in text
    assert api.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_ROUTER_REPORT_CONFIG_VERSION",
        "ResearchTeamDomainEvidenceMemoryRouterReportConfig",
        "ResearchTeamDomainEvidenceMemoryRouterInput",
        "ResearchTeamDomainEvidenceMemoryRouterRow",
        "ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount",
        "ResearchTeamDomainEvidenceMemoryRouterReport",
        "build_research_team_domain_evidence_memory_router_report",
        "research_team_domain_evidence_memory_router_report_payload",
        "validate_research_team_domain_evidence_memory_router_public_payload",
    )


def _assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for nested_value in value.values():
            _assert_no_float_values(nested_value)
    elif isinstance(value, (list, tuple)):
        for nested_value in value:
            _assert_no_float_values(nested_value)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None

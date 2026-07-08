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
MODULE_PATH = "src/polymarket_alpha_lab/research_domain_team_memory_router_report.py"


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def _api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_team_memory_router_report",
    )


def _domain(
    api: Any,
    domain_label: str,
    *,
    memory_fresh_team_count: Decimal,
    memory_team_count: Decimal,
    review_queue_count: Decimal,
    review_capacity_count: Decimal,
    evidence_gap_count: Decimal,
    evidence_target_count: Decimal,
    escalation_fit_count: Decimal,
    escalation_candidate_count: Decimal,
) -> Any:
    return api.ResearchDomainTeamMemoryRouterDomainInput(
        domain_label=domain_label,
        memory_fresh_team_count=memory_fresh_team_count,
        memory_team_count=memory_team_count,
        review_queue_count=review_queue_count,
        review_capacity_count=review_capacity_count,
        evidence_gap_count=evidence_gap_count,
        evidence_target_count=evidence_target_count,
        escalation_fit_count=escalation_fit_count,
        escalation_candidate_count=escalation_candidate_count,
    )


def test_builds_aggregate_domain_router_report_for_memory_review_evidence_and_fit() -> None:
    api = _api()

    report = api.build_research_domain_team_memory_router_report(
        (
            _domain(
                api,
                "politics",
                memory_fresh_team_count=Decimal("3"),
                memory_team_count=Decimal("3"),
                review_queue_count=Decimal("1"),
                review_capacity_count=Decimal("4"),
                evidence_gap_count=Decimal("0"),
                evidence_target_count=Decimal("4"),
                escalation_fit_count=Decimal("3"),
                escalation_candidate_count=Decimal("3"),
            ),
            _domain(
                api,
                "crypto_btc",
                memory_fresh_team_count=Decimal("2"),
                memory_team_count=Decimal("4"),
                review_queue_count=Decimal("4"),
                review_capacity_count=Decimal("4"),
                evidence_gap_count=Decimal("2"),
                evidence_target_count=Decimal("4"),
                escalation_fit_count=Decimal("1"),
                escalation_candidate_count=Decimal("4"),
            ),
            _domain(
                api,
                "sports",
                memory_fresh_team_count=Decimal("3"),
                memory_team_count=Decimal("4"),
                review_queue_count=Decimal("3"),
                review_capacity_count=Decimal("4"),
                evidence_gap_count=Decimal("1"),
                evidence_target_count=Decimal("4"),
                escalation_fit_count=Decimal("3"),
                escalation_candidate_count=Decimal("4"),
            ),
        ),
        config=api.ResearchDomainTeamMemoryRouterReportConfig(),
        generated_at=GENERATED_AT,
    )

    assert type(report) is api.ResearchDomainTeamMemoryRouterReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_RESEARCH_DOMAIN_TEAM_MEMORY_ROUTER_REPORT_CONFIG_VERSION
    )
    assert report.router_status == "block"
    assert report.domain_count == Decimal("3.000000")
    assert report.pass_domain_count == Decimal("1.000000")
    assert report.watch_domain_count == Decimal("1.000000")
    assert report.block_domain_count == Decimal("1.000000")
    assert report.average_readiness_score == Decimal("0.625000")
    assert report.lowest_readiness_score == Decimal("0.312500")
    assert report.lowest_memory_freshness_ratio == Decimal("0.500000")
    assert report.max_review_load_ratio == Decimal("1.000000")
    assert report.max_evidence_gap_pressure == Decimal("0.500000")
    assert report.lowest_escalation_fit_ratio == Decimal("0.250000")
    assert report.reason_codes == (
        "research_domain_team_memory_router_block_domains_present",
        "research_domain_team_memory_router_watch_domains_present",
    )
    assert report.reason_code_counts == (
        api.ResearchDomainTeamMemoryRouterReasonCodeCount(
            reason_code="research_domain_team_memory_router_memory_freshness_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchDomainTeamMemoryRouterReasonCodeCount(
            reason_code="research_domain_team_memory_router_review_load_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchDomainTeamMemoryRouterReasonCodeCount(
            reason_code="research_domain_team_memory_router_evidence_gap_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchDomainTeamMemoryRouterReasonCodeCount(
            reason_code="research_domain_team_memory_router_escalation_fit_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchDomainTeamMemoryRouterReasonCodeCount(
            reason_code="research_domain_team_memory_router_review_load_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchDomainTeamMemoryRouterReasonCodeCount(
            reason_code="research_domain_team_memory_router_evidence_gap_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchDomainTeamMemoryRouterReasonCodeCount(
            reason_code="research_domain_team_memory_router_ready",
            count=Decimal("1.000000"),
        ),
    )
    assert tuple((row.domain_label, row.router_status) for row in report.rows) == (
        ("crypto_btc", "block"),
        ("politics", "pass"),
        ("sports", "watch"),
    )

    crypto = report.rows[0]
    assert crypto.memory_freshness_ratio == Decimal("0.500000")
    assert crypto.review_load_ratio == Decimal("1.000000")
    assert crypto.evidence_gap_pressure == Decimal("0.500000")
    assert crypto.escalation_fit_ratio == Decimal("0.250000")
    assert crypto.readiness_score == Decimal("0.312500")
    assert crypto.reason_codes == (
        "research_domain_team_memory_router_memory_freshness_block",
        "research_domain_team_memory_router_review_load_block",
        "research_domain_team_memory_router_evidence_gap_block",
        "research_domain_team_memory_router_escalation_fit_block",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_digest_is_deterministic_decimal_only_and_public_safe() -> None:
    api = _api()
    first_rows = (
        _domain(
            api,
            "sports",
            memory_fresh_team_count=Decimal("3"),
            memory_team_count=Decimal("4"),
            review_queue_count=Decimal("3"),
            review_capacity_count=Decimal("4"),
            evidence_gap_count=Decimal("1"),
            evidence_target_count=Decimal("4"),
            escalation_fit_count=Decimal("3"),
            escalation_candidate_count=Decimal("4"),
        ),
        _domain(
            api,
            "politics",
            memory_fresh_team_count=Decimal("3"),
            memory_team_count=Decimal("3"),
            review_queue_count=Decimal("1"),
            review_capacity_count=Decimal("4"),
            evidence_gap_count=Decimal("0"),
            evidence_target_count=Decimal("4"),
            escalation_fit_count=Decimal("3"),
            escalation_candidate_count=Decimal("3"),
        ),
    )
    second_rows = tuple(reversed(first_rows))

    report = api.build_research_domain_team_memory_router_report(
        first_rows,
        config=api.ResearchDomainTeamMemoryRouterReportConfig(),
        generated_at=GENERATED_AT,
    )
    rebuilt = api.build_research_domain_team_memory_router_report(
        second_rows,
        config=api.ResearchDomainTeamMemoryRouterReportConfig(),
        generated_at=GENERATED_AT,
    )

    assert rebuilt.derived_validation_digest == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    payload = api.research_domain_team_memory_router_report_payload(report)
    assert api.research_domain_team_memory_router_report_payload(payload) == payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["domain_count"] == "2.000000"
    assert payload["average_readiness_score"] == "0.781250"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["domain_label"] == "politics"
    assert payload["rows"][0]["memory_fresh_team_count"] == "3.000000"
    assert payload["rows"][0]["paper_only"] is True
    encoded = json.dumps(payload, sort_keys=True)
    assert "team_id" not in encoded
    assert "source_key" not in encoded
    _assert_no_float_values(payload)


def test_validates_decimal_inputs_status_consistency_flags_and_safe_labels() -> None:
    api = _api()
    report = api.build_research_domain_team_memory_router_report(
        (
            _domain(
                api,
                "politics",
                memory_fresh_team_count=Decimal("1"),
                memory_team_count=Decimal("1"),
                review_queue_count=Decimal("0"),
                review_capacity_count=Decimal("1"),
                evidence_gap_count=Decimal("0"),
                evidence_target_count=Decimal("1"),
                escalation_fit_count=Decimal("1"),
                escalation_candidate_count=Decimal("1"),
            ),
        ),
        config=api.ResearchDomainTeamMemoryRouterReportConfig(),
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert {row.router_status for row in report.rows} <= {"pass", "watch", "block"}
    with pytest.raises(FrozenInstanceError):
        report.router_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="memory_fresh_team_count must be a Decimal"):
        replace(report.rows[0], memory_fresh_team_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_fresh_team_count must not exceed"):
        replace(report.rows[0], memory_fresh_team_count=Decimal("2.000000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_research_domain_team_memory_router_report(
            (),
            config=api.ResearchDomainTeamMemoryRouterReportConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="review_load_watch_threshold must be a Decimal"):
        api.ResearchDomainTeamMemoryRouterReportConfig(
            review_load_watch_threshold=_DecimalSubclass("0.750000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(api.ResearchDomainTeamMemoryRouterReportConfig(), paper_only=False)
    with pytest.raises(ValueError, match="domain_label must be public"):
        _domain(
            api,
            "wal" "let-domain",
            memory_fresh_team_count=Decimal("1"),
            memory_team_count=Decimal("1"),
            review_queue_count=Decimal("0"),
            review_capacity_count=Decimal("1"),
            evidence_gap_count=Decimal("0"),
            evidence_target_count=Decimal("1"),
            escalation_fit_count=Decimal("1"),
            escalation_candidate_count=Decimal("1"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, average_readiness_score=Decimal("0.500000"))
    with pytest.raises(ValueError, match="readonly"):
        api.research_domain_team_memory_router_report_payload(
            {**report.payload, "readonly": False},
        )


def test_public_contract_is_frozen_decimal_only_report_only_and_in_memory() -> None:
    api = _api()
    public_types = {
        "ResearchDomainTeamMemoryRouterReportConfig",
        "ResearchDomainTeamMemoryRouterDomainInput",
        "ResearchDomainTeamMemoryRouterDomainRow",
        "ResearchDomainTeamMemoryRouterReasonCodeCount",
        "ResearchDomainTeamMemoryRouterReport",
    }
    for name in public_types:
        cls = getattr(api, name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    report = api.build_research_domain_team_memory_router_report(
        (
            _domain(
                api,
                "politics",
                memory_fresh_team_count=Decimal("1"),
                memory_team_count=Decimal("1"),
                review_queue_count=Decimal("0"),
                review_capacity_count=Decimal("1"),
                evidence_gap_count=Decimal("0"),
                evidence_target_count=Decimal("1"),
                escalation_fit_count=Decimal("1"),
                escalation_candidate_count=Decimal("1"),
            ),
        ),
        config=api.ResearchDomainTeamMemoryRouterReportConfig(),
        generated_at=GENERATED_AT,
    )
    decimal_fields = {
        "domain_count",
        "pass_domain_count",
        "watch_domain_count",
        "block_domain_count",
        "average_readiness_score",
        "lowest_readiness_score",
        "lowest_memory_freshness_ratio",
        "max_review_load_ratio",
        "max_evidence_gap_pressure",
        "lowest_escalation_fit_ratio",
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
    ):
        assert forbidden not in text
    assert api.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_TEAM_MEMORY_ROUTER_REPORT_CONFIG_VERSION",
        "ResearchDomainTeamMemoryRouterReportConfig",
        "ResearchDomainTeamMemoryRouterDomainInput",
        "ResearchDomainTeamMemoryRouterDomainRow",
        "ResearchDomainTeamMemoryRouterReasonCodeCount",
        "ResearchDomainTeamMemoryRouterReport",
        "build_research_domain_team_memory_router_report",
        "research_domain_team_memory_router_report_payload",
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

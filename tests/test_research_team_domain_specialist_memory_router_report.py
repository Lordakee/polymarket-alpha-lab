from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 0, tzinfo=UTC)
MODULE_PATH = (
    "src/polymarket_alpha_lab/"
    "research_team_domain_specialist_memory_router_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_specialist_memory_router_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def memory(
    memory_key: str,
    *,
    team_label: str = "team_alpha",
    domain_label: str = "politics",
    specialist_label: str = "specialist_alpha",
    specialist_memory_score: Decimal = d("0.900000"),
    domain_fit_score: Decimal = d("0.900000"),
    conflict_score: Decimal = d("0.100000"),
    review_pressure_score: Decimal = d("0.200000"),
    observed_at: datetime = OBSERVED_AT,
) -> Any:
    return api().ResearchTeamDomainSpecialistMemoryRouterInput(
        memory_key=memory_key,
        team_label=team_label,
        domain_label=domain_label,
        specialist_label=specialist_label,
        specialist_memory_score=specialist_memory_score,
        domain_fit_score=domain_fit_score,
        conflict_score=conflict_score,
        review_pressure_score=review_pressure_score,
        observed_at=observed_at,
    )


def build_report(*items: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_specialist_memory_router_report(
        items,
        config=module.ResearchTeamDomainSpecialistMemoryRouterConfig()
        if cfg is None
        else cfg,
        generated_at=generated_at,
    )


def test_routes_domain_specialist_memories_and_validates_digest() -> None:
    rows = (
        memory("memory-alpha-private-key", domain_label="politics"),
        memory(
            "memory-beta-private-key",
            team_label="team_beta",
            domain_label="crypto",
            specialist_label="specialist_beta",
            specialist_memory_score=d("0.650000"),
            domain_fit_score=d("0.650000"),
            conflict_score=d("0.300000"),
            review_pressure_score=d("0.800000"),
            observed_at=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
        ),
        memory(
            "memory-gamma-private-key",
            team_label="team_gamma",
            domain_label="macro.rates",
            specialist_label="specialist_gamma",
            specialist_memory_score=d("0.300000"),
            domain_fit_score=d("0.400000"),
            conflict_score=d("0.700000"),
            review_pressure_score=d("0.950000"),
            observed_at=datetime(2025, 12, 1, 12, 0, tzinfo=UTC),
        ),
    )

    report = build_report(*rows)
    rebuilt = build_report(*reversed(rows))

    assert api().TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "block"
    assert report.paper_route_action == "paper_memory_route_block"
    assert report.memory_count == d("3.000000")
    assert report.routed_memory_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.max_router_priority_score == d("0.837500")
    assert report.avg_router_priority_score == d("0.436389")
    assert report.min_specialist_memory_score == d("0.300000")
    assert report.min_domain_fit_score == d("0.400000")
    assert report.max_conflict_score == d("0.700000")
    assert report.max_review_pressure_score == d("0.950000")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.route_rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    blocked, watched, passed = report.rows
    assert blocked.memory_age_seconds == d("18921600.000000")
    assert blocked.router_priority_score == d("0.837500")
    assert blocked.reason_codes == (
        "team_domain_specialist_memory_router_specialist_memory_block",
        "team_domain_specialist_memory_router_domain_fit_block",
        "team_domain_specialist_memory_router_memory_age_block",
        "team_domain_specialist_memory_router_conflict_block",
        "team_domain_specialist_memory_router_review_pressure_block",
    )
    assert watched.router_priority_score == d("0.376667")
    assert watched.reason_codes == (
        "team_domain_specialist_memory_router_specialist_memory_watch",
        "team_domain_specialist_memory_router_domain_fit_watch",
        "team_domain_specialist_memory_router_memory_age_watch",
        "team_domain_specialist_memory_router_conflict_watch",
        "team_domain_specialist_memory_router_review_pressure_watch",
    )
    assert passed.router_priority_score == d("0.095000")
    assert passed.reason_codes == ("team_domain_specialist_memory_router_clear",)

    payload = api().research_team_domain_specialist_memory_router_report_payload(report)
    assert payload == api().research_team_domain_specialist_memory_router_report_payload(
        rebuilt,
    )
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert api().research_team_domain_specialist_memory_router_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["memory_ref"].startswith("memory_ref_")
    assert payload["rows"][0]["router_priority_score"] == "0.837500"
    assert _float_paths(payload) == ()
    public = repr(payload).lower()
    for hidden in (
        "memory-alpha-private-key",
        "memory-beta-private-key",
        "memory-gamma-private-key",
        "candidate",
        "market",
        "slug",
        "question",
        "https://",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    ):
        assert hidden not in public


def test_report_contract_is_frozen_decimal_only_report_only_and_public_safe() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION",
        "TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_STATUSES",
        "ResearchTeamDomainSpecialistMemoryRouterConfig",
        "ResearchTeamDomainSpecialistMemoryRouterInput",
        "ResearchTeamDomainSpecialistMemoryRouterReasonCodeCount",
        "ResearchTeamDomainSpecialistMemoryRouterReport",
        "ResearchTeamDomainSpecialistMemoryRouterRow",
        "build_research_team_domain_specialist_memory_router_report",
        "research_team_domain_specialist_memory_router_report_digest",
        "research_team_domain_specialist_memory_router_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    empty = build_report()
    assert empty.status == "pass"
    assert empty.paper_route_action == "paper_memory_route_pass"
    assert empty.reason_codes == ("team_domain_specialist_memory_router_empty",)
    assert empty.rows == ()
    assert empty.reason_code_counts == ()
    assert empty.memory_count == d("0.000000")

    report = build_report(memory("memory-safe-private-key"))
    for value in (
        module.ResearchTeamDomainSpecialistMemoryRouterConfig(),
        memory("memory-other-private-key", domain_label="weather"),
        report,
        *report.rows,
        *report.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_ratio", "_score", "_rank", "_seconds")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="specialist_memory_score must be a Decimal"):
        memory("memory-key", specialist_memory_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="specialist_memory_score must be a Decimal"):
        memory("memory-key", specialist_memory_score=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        memory(
            "memory-key",
            observed_at=_DateTimeSubclass(2026, 7, 8, 10, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(
            memory("memory-key", observed_at=datetime(2026, 7, 8, 13, 0, tzinfo=UTC)),
        )
    with pytest.raises(ValueError, match="memory_key values must be unique"):
        build_report(memory("memory-key"), memory("memory-key", domain_label="crypto"))
    with pytest.raises(ValueError, match="domain_label must be public"):
        memory("memory-key", domain_label="market_slug")
    with pytest.raises(ValueError, match="min_watch_specialist_memory_score"):
        module.ResearchTeamDomainSpecialistMemoryRouterConfig(
            min_pass_specialist_memory_score=d("0.600000"),
            min_watch_specialist_memory_score=d("0.700000"),
        )


def test_rejects_payload_leaks_tampering_and_forbidden_capabilities() -> None:
    module = api()
    report = build_report(
        memory(
            "sensitive-memory-private-key",
            domain_label="weather",
            specialist_memory_score=d("0.600000"),
            domain_fit_score=d("0.600000"),
        ),
    )
    payload = module.research_team_domain_specialist_memory_router_report_payload(report)
    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_specialist_memory_router_report_payload(tampered)

    for unsafe_key, unsafe_value in (
        ("candidate_id", "opaque"),
        ("market_slug", "will-fed-cut-rates"),
        ("question", "Will this resolve yes?"),
        ("source_url", "https://example.test/item"),
        ("dsn", "postgres://example"),
        ("wallet", "0xabc"),
        ("order_ticket", "abc"),
        ("trade", "abc"),
        ("sizing", "100"),
        ("recommendation", "buy"),
    ):
        leaked = dict(payload)
        leaked[unsafe_key] = unsafe_value
        leaked["derived_validation_digest"] = canonical_digest(leaked)
        with pytest.raises(ValueError, match="unsafe"):
            module.research_team_domain_specialist_memory_router_report_payload(leaked)

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
        "auth",
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
        "sizing",
        "recommendation",
    ):
        assert forbidden not in text


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) is float:
        return (path or "<root>",)
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None

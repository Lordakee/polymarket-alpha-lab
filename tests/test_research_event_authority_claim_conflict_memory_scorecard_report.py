from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_authority_claim_conflict_memory_scorecard_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_event_authority_claim_conflict_memory_scorecard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def event_input(event_key: str = "event_alpha", **overrides: object):
    module = api()
    values: dict[str, object] = {
        "event_key": event_key,
        "authority_key": f"authority_{event_key}",
        "claim_key": f"claim_{event_key}",
        "observed_at": GENERATED_AT,
        "authority_claim_count": d("4"),
        "conflicting_claim_count": d("0"),
        "memory_observation_count": d("4"),
        "conflicting_memory_count": d("0"),
        "stale_memory_count": d("0"),
        "unresolved_conflict_age_days": d("0.000000"),
        "independent_evidence_count": d("3"),
        "reason_codes": ("initial_parse_review",),
    }
    values.update(overrides)
    return module.ResearchEventAuthorityClaimConflictMemoryScorecardInput(**values)


def scorecard_report(*items: object, **overrides: object):
    module = api()
    config = overrides.pop("config", None)
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    return module.build_research_event_authority_claim_conflict_memory_scorecard_report(
        list(items),
        config=config,
        generated_at=generated_at,
    )


def assert_no_number_scalars(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_number_scalars(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_number_scalars(item)


def assert_no_raw_leak_keys(value: Any) -> None:
    forbidden = {
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            assert not any(word in key.lower() for word in forbidden)
            assert_no_raw_leak_keys(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_raw_leak_keys(item)


def test_scorecard_scoring_rollup_and_statuses_are_deterministic() -> None:
    report = scorecard_report(
        event_input("event_pass"),
        event_input(
            "event_watch",
            conflicting_claim_count=d("2"),
            conflicting_memory_count=d("1"),
            stale_memory_count=d("1"),
            unresolved_conflict_age_days=d("2.000000"),
            independent_evidence_count=d("2"),
        ),
        event_input(
            "event_block",
            conflicting_claim_count=d("4"),
            conflicting_memory_count=d("3"),
            stale_memory_count=d("2"),
            unresolved_conflict_age_days=d("7.000000"),
            independent_evidence_count=d("0"),
        ),
    )

    assert is_dataclass(report)
    assert report.event_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.max_conflict_memory_score == d("0.900000")
    assert report.average_conflict_memory_score == d("0.394048")
    assert report.status == "block"
    assert report.reason_codes == (
        "authority_claim_conflict_memory_report_block",
        "authority_claim_conflict_memory_block",
        "authority_claim_conflict_memory_watch",
        "authority_claim_conflict_memory_pass",
    )

    blocked, watched, passed = report.rows
    assert blocked.event_key == "event_block"
    assert blocked.conflict_ratio == d("1.000000")
    assert blocked.memory_conflict_ratio == d("0.750000")
    assert blocked.stale_memory_ratio == d("0.500000")
    assert blocked.age_pressure_score == d("1.000000")
    assert blocked.evidence_relief_score == d("0.000000")
    assert blocked.conflict_memory_score == d("0.900000")
    assert blocked.status == "block"

    assert watched.event_key == "event_watch"
    assert watched.conflict_memory_score == d("0.282143")
    assert watched.status == "watch"
    assert passed.event_key == "event_pass"
    assert passed.conflict_memory_score == d("0.000000")
    assert passed.status == "pass"


def test_public_payload_is_decimal_string_only_stable_and_digest_checked() -> None:
    module = api()
    report = scorecard_report(
        event_input(
            "event_watch",
            conflicting_claim_count=d("2"),
            conflicting_memory_count=d("1"),
            stale_memory_count=d("1"),
            unresolved_conflict_age_days=d("2.000000"),
            independent_evidence_count=d("2"),
        ),
    )

    payload = (
        module.research_event_authority_claim_conflict_memory_scorecard_report_payload(
            report,
        )
    )
    repeated_payload = (
        module.research_event_authority_claim_conflict_memory_scorecard_report_payload(
            report,
        )
    )

    assert payload == repeated_payload
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        repeated_payload,
        sort_keys=True,
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["event_count"] == "1"
    assert payload["rows"][0]["conflict_memory_score"] == "0.282143"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert len(payload["rows"][0]["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    int(payload["rows"][0]["derived_validation_digest"], 16)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_number_scalars(payload)
    assert_no_raw_leak_keys(payload)

    readonly_payload = (
        module.research_event_authority_claim_conflict_memory_scorecard_report_payload(
            {
                "event_count": d("1"),
                "rows": (
                    {
                        "conflict_memory_score": d("0.250000"),
                        "paper_only": True,
                        "report_only": True,
                        "readonly": True,
                    },
                ),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    )
    assert readonly_payload["event_count"] == "1"
    assert readonly_payload["rows"][0]["conflict_memory_score"] == "0.250000"

    object.__setattr__(report.rows[0], "conflict_memory_score", d("0.010000"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.research_event_authority_claim_conflict_memory_scorecard_report_payload(
            report,
        )


def test_public_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.ResearchEventAuthorityClaimConflictMemoryScorecardConfig()
    sample = event_input()
    report = scorecard_report(sample)
    row = report.rows[0]

    public_decimal_fields = {
        "watch_conflict_memory_score",
        "block_conflict_memory_score",
        "max_unresolved_conflict_age_days",
        "conflict_weight",
        "memory_weight",
        "age_weight",
        "stale_memory_weight",
        "evidence_relief_per_item",
        "max_evidence_relief_score",
        "min_independent_evidence_count",
        "authority_claim_count",
        "conflicting_claim_count",
        "memory_observation_count",
        "conflicting_memory_count",
        "stale_memory_count",
        "unresolved_conflict_age_days",
        "independent_evidence_count",
        "conflict_ratio",
        "memory_conflict_ratio",
        "stale_memory_ratio",
        "age_pressure_score",
        "evidence_relief_score",
        "conflict_memory_score",
        "event_count",
        "pass_count",
        "watch_count",
        "block_count",
        "conflicting_event_count",
        "stale_memory_event_count",
        "sparse_evidence_event_count",
        "max_conflict_memory_score",
        "average_conflict_memory_score",
    }
    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in public_decimal_fields:
                assert type(getattr(item, field.name)) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchEventAuthorityClaimConflictMemoryScorecardConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        event_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        event_input(readonly=False)
    with pytest.raises(ValueError, match="Decimal"):
        event_input(authority_claim_count=1)
    with pytest.raises(ValueError, match="Decimal"):
        module.ResearchEventAuthorityClaimConflictMemoryScorecardConfig(
            watch_conflict_memory_score=DecimalSubclass("0.250000"),
        )
    with pytest.raises(ValueError, match="six decimal places"):
        event_input(unresolved_conflict_age_days=d("1.0000001"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        event_input(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")


def test_public_payload_rejects_unsafe_terms_and_raw_leak_fields() -> None:
    module = api()
    unsafe_public_terms = (
        "candidate_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "raw_text",
        "dsn",
        "table",
        "token",
        "db",
        "wallet",
        "network",
        "order",
        "trade",
        "live",
        "trading",
        "sizing",
        "recommendation",
    )

    for term in unsafe_public_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_event_authority_claim_conflict_memory_scorecard_report_payload(
                {
                    term: "redacted",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_event_authority_claim_conflict_memory_scorecard_report_payload(
                {
                    "note": f"{term} leak",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )

    with pytest.raises(ValueError, match="unsafe public"):
        event_input(event_key="source_url")
    with pytest.raises(ValueError, match="canonical public identifier"):
        event_input(event_key="Will this event resolve yes?")
    with pytest.raises(ValueError, match="unsafe public"):
        event_input(event_key="event_slug")
    with pytest.raises(ValueError, match="reason_codes"):
        event_input(reason_codes=("token_leak",))
    with pytest.raises(ValueError, match="float"):
        module.research_event_authority_claim_conflict_memory_scorecard_report_payload(
            {"score": 0.1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="Decimal"):
        module.research_event_authority_claim_conflict_memory_scorecard_report_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )


def test_module_scope_is_pure_report_only_without_runtime_surfaces() -> None:
    module = api()
    module_source = inspect.getsource(module)
    source_lower = module_source.lower()
    tree = ast.parse(module_source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_AUTHORITY_CLAIM_CONFLICT_MEMORY_SCORECARD_CONFIG_VERSION",
        "ROW_STATUSES",
        "REPORT_STATUSES",
        "ResearchEventAuthorityClaimConflictMemoryScorecardConfig",
        "ResearchEventAuthorityClaimConflictMemoryScorecardInput",
        "ResearchEventAuthorityClaimConflictMemoryScorecardRow",
        "ResearchEventAuthorityClaimConflictMemoryScorecardReport",
        "build_research_event_authority_claim_conflict_memory_scorecard_report",
        "research_event_authority_claim_conflict_memory_scorecard_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
    }

    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "database",
        "wallet",
        "network",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
        "broker",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "write_text",
        "write_bytes",
    )
    assert all(term not in source_lower for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names

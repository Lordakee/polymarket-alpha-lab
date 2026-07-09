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
    / "research_source_authority_claim_memory_guard_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_source_authority_claim_memory_guard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def guard_input(authority_key: str = "authority_alpha", **overrides: object):
    module = api()
    values: dict[str, object] = {
        "authority_key": authority_key,
        "claim_key": f"claim_{authority_key}",
        "memory_key": f"memory_{authority_key}",
        "observed_at": GENERATED_AT,
        "authority_record_count": d("4"),
        "conflicting_record_count": d("0"),
        "remembered_claim_count": d("4"),
        "stale_memory_count": d("0"),
        "unverified_memory_count": d("0"),
        "reason_codes": ("initial_guard_review",),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityClaimMemoryGuardInput(**values)


def guard_report(*items: object, **overrides: object):
    module = api()
    config = overrides.pop("config", None)
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    return module.build_research_source_authority_claim_memory_guard_report(
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
    elif isinstance(value, list):
        for item in value:
            assert_no_number_scalars(item)


def assert_no_raw_leak_keys_or_values(value: Any) -> None:
    forbidden = {
        "".join(parts)
        for parts in (
            ("can", "didate"),
            ("mar", "ket"),
            ("sou", "rce"),
            ("u", "rl"),
            ("te", "xt"),
            ("d", "sn"),
            ("ta", "ble"),
            ("to", "ken"),
        )
    }
    if isinstance(value, dict):
        for key, item in value.items():
            assert not any(word in key.lower() for word in forbidden)
            assert_no_raw_leak_keys_or_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_raw_leak_keys_or_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(word in lowered for word in forbidden)


def test_guard_rollup_statuses_and_scores_are_deterministic() -> None:
    report = guard_report(
        guard_input("authority_pass"),
        guard_input(
            "authority_watch",
            conflicting_record_count=d("2"),
            stale_memory_count=d("1"),
            unverified_memory_count=d("1"),
        ),
        guard_input(
            "authority_block",
            authority_record_count=d("1"),
            conflicting_record_count=d("1"),
            stale_memory_count=d("2"),
            unverified_memory_count=d("4"),
        ),
    )

    assert is_dataclass(report)
    assert report.record_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.conflict_record_count == d("2")
    assert report.stale_memory_record_count == d("2")
    assert report.authority_floor_gap_count == d("1")
    assert report.max_guard_pressure_score == d("0.800000")
    assert report.average_guard_pressure_score == d("0.366667")
    assert report.status == "block"
    assert report.reason_codes == (
        "authority_memory_guard_report_block",
        "authority_memory_guard_block",
        "authority_memory_guard_watch",
        "authority_memory_guard_pass",
    )

    blocked, watched, passed = report.rows
    assert blocked.authority_key == "authority_block"
    assert blocked.conflict_ratio == d("1.000000")
    assert blocked.stale_memory_ratio == d("0.500000")
    assert blocked.unverified_memory_ratio == d("1.000000")
    assert blocked.authority_floor_gap_ratio == d("0.500000")
    assert blocked.guard_pressure_score == d("0.800000")
    assert blocked.status == "block"

    assert watched.authority_key == "authority_watch"
    assert watched.guard_pressure_score == d("0.300000")
    assert watched.status == "watch"
    assert passed.authority_key == "authority_pass"
    assert passed.guard_pressure_score == d("0.000000")
    assert passed.status == "pass"


def test_public_payload_is_decimal_string_only_stable_and_digest_checked() -> None:
    module = api()
    report = guard_report(
        guard_input(
            "authority_watch",
            conflicting_record_count=d("2"),
            stale_memory_count=d("1"),
            unverified_memory_count=d("1"),
        ),
    )

    payload = module.research_source_authority_claim_memory_guard_report_payload(report)
    repeated_payload = module.research_source_authority_claim_memory_guard_report_payload(
        report,
    )

    assert payload == repeated_payload
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        repeated_payload,
        sort_keys=True,
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["record_count"] == "1"
    assert payload["rows"][0]["guard_pressure_score"] == "0.300000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["derived_validation_digest"].startswith("rsacmg-v0:")
    assert payload["rows"][0]["derived_validation_digest"].startswith("rsacmg-v0:")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_number_scalars(payload)
    assert_no_raw_leak_keys_or_values(payload)

    readonly_payload = module.research_source_authority_claim_memory_guard_report_payload(
        {
            "record_count": d("1"),
            "rows": (
                {
                    "guard_pressure_score": d("0.250000"),
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
    assert readonly_payload["record_count"] == "1"
    assert readonly_payload["rows"][0]["guard_pressure_score"] == "0.250000"

    object.__setattr__(report.rows[0], "guard_pressure_score", d("0.010000"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.research_source_authority_claim_memory_guard_report_payload(report)


def test_public_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.ResearchSourceAuthorityClaimMemoryGuardConfig()
    sample = guard_input()
    report = guard_report(sample)
    row = report.rows[0]

    public_decimal_fields = {
        "watch_guard_pressure_score",
        "block_guard_pressure_score",
        "minimum_authority_record_count",
        "conflict_weight",
        "stale_memory_weight",
        "unverified_memory_weight",
        "authority_floor_gap_weight",
        "authority_record_count",
        "conflicting_record_count",
        "remembered_claim_count",
        "stale_memory_count",
        "unverified_memory_count",
        "conflict_ratio",
        "stale_memory_ratio",
        "unverified_memory_ratio",
        "authority_floor_gap_ratio",
        "guard_pressure_score",
        "record_count",
        "pass_count",
        "watch_count",
        "block_count",
        "conflict_record_count",
        "stale_memory_record_count",
        "unverified_memory_record_count",
        "authority_floor_gap_count",
        "max_guard_pressure_score",
        "average_guard_pressure_score",
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
        module.ResearchSourceAuthorityClaimMemoryGuardConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        guard_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        guard_input(readonly=False)
    with pytest.raises(ValueError, match="Decimal"):
        guard_input(authority_record_count=1)
    with pytest.raises(ValueError, match="Decimal"):
        module.ResearchSourceAuthorityClaimMemoryGuardConfig(
            watch_guard_pressure_score=DecimalSubclass("0.250000"),
        )
    with pytest.raises(ValueError, match="six decimal places"):
        guard_input(stale_memory_count=d("1.0000001"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        guard_input(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")
    assert module.STATUSES == ("pass", "watch", "block")


def test_public_payload_rejects_unsafe_terms_and_raw_leak_fields() -> None:
    module = api()
    unsafe_public_terms = (
        "".join(parts)
        for parts in (
            ("can", "didate_id"),
            ("mar", "ket_slug"),
            ("sou", "rce_url"),
            ("raw_", "text"),
            ("d", "sn"),
            ("ta", "ble"),
            ("to", "ken"),
        )
    )

    for term in unsafe_public_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_source_authority_claim_memory_guard_report_payload(
                {
                    term: "redacted",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_source_authority_claim_memory_guard_report_payload(
                {
                    "note": f"{term} leak",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )

    with pytest.raises(ValueError, match="unsafe public"):
        guard_input(authority_key="source_url")
    with pytest.raises(ValueError, match="reason_codes"):
        guard_input(reason_codes=("token_leak",))
    with pytest.raises(ValueError, match="float"):
        module.research_source_authority_claim_memory_guard_report_payload(
            {"score": 0.1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="Decimal"):
        module.research_source_authority_claim_memory_guard_report_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )


def test_module_scope_is_pure_report_only_without_runtime_surfaces() -> None:
    module = api()
    module_source = inspect.getsource(module)
    source_lower = module_source.lower()
    tree = ast.parse(module_source)

    assert MODULE_PATH.exists()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CLAIM_MEMORY_GUARD_CONFIG_VERSION",
        "STATUSES",
        "ResearchSourceAuthorityClaimMemoryGuardConfig",
        "ResearchSourceAuthorityClaimMemoryGuardInput",
        "ResearchSourceAuthorityClaimMemoryGuardRow",
        "ResearchSourceAuthorityClaimMemoryGuardReport",
        "build_research_source_authority_claim_memory_guard_report",
        "research_source_authority_claim_memory_guard_report_payload",
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
        "".join(("data", "base")),
        "".join(("wal", "let")),
        "".join(("net", "work")),
        "".join(("or", "der")),
        "".join(("l", "ive")),
        "".join(("tra", "ding")),
        "".join(("si", "zing")),
        "".join(("recomm", "endation")),
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

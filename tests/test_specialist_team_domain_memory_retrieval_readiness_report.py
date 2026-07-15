from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "specialist_team_domain_memory_retrieval_readiness_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab.specialist_team_domain_memory_retrieval_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_memory_exists": True,
        "similar_market_count": d("5.000000"),
        "recent_calibration_count": d("3.000000"),
        "source_family_history_count": d("2.000000"),
        "retrieval_latency_ms": d("125.000000"),
        "schema_version_present": True,
    }
    values.update(overrides)
    return module.SpecialistTeamDomainMemoryRetrievalReadinessInput(**values)


def build(**overrides: object) -> Any:
    module = api()
    return module.build_specialist_team_domain_memory_retrieval_readiness_report(
        readiness(**overrides),
    )


def test_ready_report_derives_public_payload_manual_step_and_digest() -> None:
    module = api()
    report = build()

    assert type(report) is module.SpecialistTeamDomainMemoryRetrievalReadinessReport
    assert is_dataclass(report)
    assert report.retrieval_status == "ready"
    assert report.reason_codes == (
        "team_memory_retrieval_ready",
    )
    assert report.manual_next_step == (
        "Proceed with manual read-only retrieval review using public payload."
    )
    assert report.team_memory_exists is True
    assert report.similar_market_count == d("5.000000")
    assert report.recent_calibration_count == d("3.000000")
    assert report.source_family_history_count == d("2.000000")
    assert report.retrieval_latency_ms == d("125.000000")
    assert report.schema_version_present is True
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.specialist_team_domain_memory_retrieval_readiness_report_payload(
        report,
    )
    assert payload == report.public_payload
    assert payload["retrieval_status"] == "ready"
    assert payload["similar_market_count"] == "5.000000"
    assert payload["recent_calibration_count"] == "3.000000"
    assert payload["source_family_history_count"] == "2.000000"
    assert payload["retrieval_latency_ms"] == "125.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == report.payload_digest
    assert len(report.payload_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.payload_digest)
    _assert_no_floats(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_attention_and_blocked_reason_codes_are_deterministic() -> None:
    attention = build(similar_market_count=d("1.000000"), retrieval_latency_ms=d("900.000000"))
    blocked = build(
        team_memory_exists=False,
        similar_market_count=d("0.000000"),
        recent_calibration_count=d("0.000000"),
        source_family_history_count=d("0.000000"),
        retrieval_latency_ms=d("2500.000000"),
        schema_version_present=False,
    )

    assert attention.retrieval_status == "attention"
    assert attention.reason_codes == (
        "similar_market_count_below_ready",
        "retrieval_latency_watch",
    )
    assert attention.manual_next_step == (
        "Manually review retrieval gaps before relying on team memory context."
    )

    assert blocked.retrieval_status == "blocked"
    assert blocked.reason_codes == (
        "team_memory_missing",
        "similar_market_count_missing",
        "recent_calibration_missing",
        "source_family_history_missing",
        "retrieval_latency_blocked",
        "schema_version_missing",
    )
    assert blocked.manual_next_step == (
        "Pause and manually collect or verify read-only team memory evidence."
    )


def test_input_and_report_are_frozen_decimal_only_and_validate_flags() -> None:
    module = api()
    input_value = readiness()
    report = build()

    assert module.__all__ == (
        "SPECIALIST_TEAM_DOMAIN_MEMORY_RETRIEVAL_READINESS_STATUSES",
        "SPECIALIST_TEAM_DOMAIN_MEMORY_RETRIEVAL_READINESS_REASON_CODES",
        "SpecialistTeamDomainMemoryRetrievalReadinessInput",
        "SpecialistTeamDomainMemoryRetrievalReadinessReport",
        "build_specialist_team_domain_memory_retrieval_readiness_report",
        "specialist_team_domain_memory_retrieval_readiness_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    for value in (input_value, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name.endswith(("_count", "_ms")):
                assert type(item) is Decimal
            assert type(item) is not int
            assert type(item) is not float

    with pytest.raises(TypeError, match="subclassing"):

        class BadInput(module.SpecialistTeamDomainMemoryRetrievalReadinessInput):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class BadReport(module.SpecialistTeamDomainMemoryRetrievalReadinessReport):
            pass

    with pytest.raises(ValueError, match="similar_market_count must be a Decimal"):
        readiness(similar_market_count=5)
    with pytest.raises(ValueError, match="recent_calibration_count must be exactly Decimal"):
        readiness(recent_calibration_count=_DecimalSubclass("3.000000"))
    with pytest.raises(ValueError, match="source_family_history_count must be a whole Decimal"):
        readiness(source_family_history_count=d("2.500000"))
    with pytest.raises(ValueError, match="retrieval_latency_ms must be >= 0.000000"):
        readiness(retrieval_latency_ms=d("-1.000000"))
    with pytest.raises(ValueError, match="schema_version_present must be a bool"):
        readiness(schema_version_present=1)
    with pytest.raises(ValueError, match="paper_only must be True"):
        readiness(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="payload_digest must match report payload"):
        replace(report, payload_digest="0" * 64)
    with pytest.raises(ValueError, match="readiness must be"):
        module.build_specialist_team_domain_memory_retrieval_readiness_report(object())
    with pytest.raises(ValueError, match="report must be"):
        module.specialist_team_domain_memory_retrieval_readiness_report_payload(object())


def test_module_is_readonly_report_only_and_has_no_forbidden_runtime_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
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
        "db",
        "connect",
        "connection",
        "client",
        "session",
        "credential",
        "secret",
        "token",
        "private_key",
        "api_key",
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "secret_key",
        "sign",
        "execute",
        "execution",
        "submit",
        "cancel",
        "buy",
        "sell",
        "trade",
        "open(",
        "pathlib",
        "subprocess",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
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
        "decimal",
        "hashlib",
        "json",
        "typing",
    }


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)

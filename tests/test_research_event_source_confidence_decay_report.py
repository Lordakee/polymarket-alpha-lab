from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_source_confidence_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def domain_input(event_domain: str = "weather", **overrides: object):
    module = api()
    values: dict[str, object] = {
        "event_domain": event_domain,
        "aggregate_source_age_hours": d("6.000000"),
        "reliability_memory_score": d("0.900000"),
        "contradiction_pressure": d("0.050000"),
        "catalyst_pressure": d("0.050000"),
        "team_capacity_score": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchEventSourceConfidenceDecayInput(**values)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_EVENT_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION
        ),
        "max_source_age_hours": d("72.000000"),
        "max_pass_confidence_decay_score": d("0.350000"),
        "max_watch_confidence_decay_score": d("0.650000"),
        "watch_source_age_pressure": d("0.300000"),
        "block_source_age_pressure": d("0.750000"),
        "watch_reliability_decay": d("0.300000"),
        "block_reliability_decay": d("0.600000"),
        "watch_contradiction_pressure": d("0.250000"),
        "block_contradiction_pressure": d("0.600000"),
        "watch_catalyst_pressure": d("0.350000"),
        "block_catalyst_pressure": d("0.600000"),
        "watch_team_capacity_pressure": d("0.350000"),
        "block_team_capacity_pressure": d("0.600000"),
        "source_age_weight": d("0.250000"),
        "reliability_memory_weight": d("0.250000"),
        "contradiction_weight": d("0.200000"),
        "catalyst_weight": d("0.150000"),
        "team_capacity_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchEventSourceConfidenceDecayConfig(**values)


def report(*rows: object, cfg: object | None = None):
    return api().build_research_event_source_confidence_decay_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def payload_digest(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def walk_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for child in value.values():
            walk_public_payload(child)
    elif isinstance(value, list):
        for child in value:
            walk_public_payload(child)
    else:
        assert type(value) not in (Decimal, datetime, float, int)
        if type(value) is str:
            assert value not in {"ready", "blocked", "matched", "supported"}


def test_empty_input_returns_block_report_only_zeroed_report() -> None:
    module = api()
    decay_report = report()

    assert type(decay_report) is module.ResearchEventSourceConfidenceDecayReport
    assert decay_report.generated_at == GENERATED_AT
    assert decay_report.status == "block"
    assert decay_report.domain_count == d("0.000000")
    assert decay_report.pass_count == d("0.000000")
    assert decay_report.watch_count == d("0.000000")
    assert decay_report.block_count == d("0.000000")
    assert decay_report.average_confidence_decay_score == d("0.000000")
    assert decay_report.max_confidence_decay_score == d("0.000000")
    assert decay_report.reason_codes == ("confidence_decay_no_event_domains",)
    assert decay_report.rows == ()
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True


def test_domain_confidence_decay_statuses_are_pass_watch_and_block() -> None:
    decay_report = report(
        domain_input(
            "sports",
            aggregate_source_age_hours=d("60.000000"),
            reliability_memory_score=d("0.350000"),
            contradiction_pressure=d("0.700000"),
            catalyst_pressure=d("0.700000"),
            team_capacity_score=d("0.300000"),
        ),
        domain_input(
            "macro",
            aggregate_source_age_hours=d("24.000000"),
            reliability_memory_score=d("0.650000"),
            contradiction_pressure=d("0.300000"),
            catalyst_pressure=d("0.400000"),
            team_capacity_score=d("0.600000"),
        ),
        domain_input("weather"),
    )

    assert decay_report.status == "block"
    assert decay_report.domain_count == d("3.000000")
    assert decay_report.pass_count == d("1.000000")
    assert decay_report.watch_count == d("1.000000")
    assert decay_report.block_count == d("1.000000")
    assert decay_report.average_confidence_decay_score == d("0.383333")
    assert decay_report.max_confidence_decay_score == d("0.720833")

    assert tuple(row.event_domain for row in decay_report.rows) == (
        "macro",
        "sports",
        "weather",
    )
    assert tuple(row.status for row in decay_report.rows) == (
        "watch",
        "block",
        "pass",
    )
    assert tuple(row.confidence_decay_score for row in decay_report.rows) == (
        d("0.350833"),
        d("0.720833"),
        d("0.078333"),
    )
    assert decay_report.rows[1].reason_codes == (
        "source_age_pressure_block",
        "reliability_memory_decay_block",
        "contradiction_pressure_block",
        "catalyst_pressure_block",
        "team_capacity_pressure_block",
        "confidence_decay_block",
    )
    assert set(decay_report.reason_codes) >= {
        "confidence_decay_pass",
        "confidence_decay_watch",
        "confidence_decay_block",
    }


def test_payload_is_deterministic_decimal_stringed_and_digest_checked() -> None:
    module = api()
    first = report(
        domain_input("weather"),
        domain_input("macro", aggregate_source_age_hours=d("24.000000")),
    )
    second = report(
        domain_input("macro", aggregate_source_age_hours=d("24.000000")),
        domain_input("weather"),
    )

    payload = module.research_event_source_confidence_decay_report_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert first == second
    assert payload == module.research_event_source_confidence_decay_report_payload(second)
    assert payload["derived_validation_digest"] == payload_digest(payload)
    assert first.derived_validation_digest == payload_digest(payload)
    assert payload["domain_count"] == "2.000000"
    assert payload["rows"][0]["confidence_decay_score"] == "0.140833"
    assert "event_id" not in encoded
    assert "market_slug" not in encoded
    assert "source_id" not in encoded
    walk_public_payload(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first.rows[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(first, pass_count=d("0.000000"))


def test_decimal_exact_types_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    module = api()
    decay_report = report(domain_input())

    with pytest.raises(FrozenInstanceError):
        decay_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        decay_report.rows[0].confidence_decay_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="aggregate_source_age_hours must be a Decimal"):
        domain_input(aggregate_source_age_hours=6)
    with pytest.raises(ValueError, match="reliability_memory_score must be a Decimal"):
        domain_input(reliability_memory_score=0.9)
    with pytest.raises(ValueError, match="team_capacity_score must be a Decimal"):
        domain_input(team_capacity_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(team_capacity_weight=d("0.250000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        domain_input(report_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(decay_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="readonly must be True"):
        module.ResearchEventSourceConfidenceDecayReport(
            generated_at=GENERATED_AT,
            config_version=(
                module.DEFAULT_RESEARCH_EVENT_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION
            ),
            domain_count=d("0.000000"),
            pass_count=d("0.000000"),
            watch_count=d("0.000000"),
            block_count=d("0.000000"),
            average_confidence_decay_score=d("0.000000"),
            max_confidence_decay_score=d("0.000000"),
            status="block",
            reason_codes=("confidence_decay_no_event_domains",),
            reason_code_counts=(),
            rows=(),
            readonly=False,
        )


def test_public_payload_rejects_raw_identifiers_execution_terms_and_numeric_leaks() -> None:
    module = api()
    valid_payload = module.research_event_source_confidence_decay_report_payload(
        report(domain_input()),
    )
    assert module.validate_research_event_source_confidence_decay_public_payload(
        valid_payload,
    )

    unsafe_payloads = (
        ({"event_id": "evt-123"}, "event identifier"),
        ({"raw_event_id": "evt-123"}, "event identifier"),
        ({"market_slug": "will-x-happen"}, "market identifier"),
        ({"source_id": "src-123"}, "source identifier"),
        ({"source_url": "https://example.test"}, "source identifier"),
        ({"safe_key": "https://example.test"}, "source reference"),
        ({"wallet_ref": "redacted"}, "execution surface"),
        ({"safe_key": "buy now"}, "execution surface"),
        ({"safe_key": "live execution enabled"}, "execution surface"),
        ({"status": "blocked"}, "status"),
        ({"domain_count": 1}, "decimal strings"),
        ({"confidence_decay_score": 0.1}, "decimal strings"),
    )
    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_research_event_source_confidence_decay_public_payload(
                payload,
            )


def test_module_has_no_network_db_wallet_or_trade_execution_surface() -> None:
    source = inspect.getsource(api())
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "commit",
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "send",
        "urlopen",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls

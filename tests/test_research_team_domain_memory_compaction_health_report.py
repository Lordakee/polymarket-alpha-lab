from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_domain_memory_compaction_health_report.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_team_domain_memory_compaction_health_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def domain_item(team_domain: str, **overrides: object):
    module = api()
    values = {
        "team_domain": team_domain,
        "compacted_memory_count": d("8"),
        "latest_compacted_memory_at": GENERATED_AT - timedelta(days=1),
        "carry_forward_conflict_count": d("0"),
        "calibration_feedback_score": d("0.900000"),
        "retrieval_coverage_ratio": d("0.950000"),
        "redaction_confirmed": True,
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemoryCompactionHealthInput(**values)


def report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_domain_memory_compaction_health_report(
        items,
        config=cfg or module.ResearchTeamDomainMemoryCompactionHealthConfig(),
        generated_at=generated_at,
    )


def test_compaction_health_scores_domains_and_builds_deterministic_digest() -> None:
    module = api()
    blocked = domain_item(
        "politics-research",
        compacted_memory_count=d("2"),
        latest_compacted_memory_at=GENERATED_AT - timedelta(days=45),
        carry_forward_conflict_count=d("4"),
        calibration_feedback_score=d("0.350000"),
        retrieval_coverage_ratio=d("0.200000"),
    )
    watched = domain_item(
        "sports-research",
        compacted_memory_count=d("5"),
        latest_compacted_memory_at=GENERATED_AT - timedelta(days=14),
        carry_forward_conflict_count=d("1"),
        calibration_feedback_score=d("0.650000"),
        retrieval_coverage_ratio=d("0.700000"),
    )
    passing = domain_item("macro-research")

    health = report(passing, blocked, watched)
    rebuilt = report(watched, passing, blocked)
    changed = report(
        passing,
        watched,
        domain_item(
            "politics-research",
            compacted_memory_count=d("2"),
            latest_compacted_memory_at=GENERATED_AT - timedelta(days=45),
            carry_forward_conflict_count=d("4"),
            calibration_feedback_score=d("0.450000"),
            retrieval_coverage_ratio=d("0.200000"),
        ),
    )

    assert type(health) is module.ResearchTeamDomainMemoryCompactionHealthReport
    assert is_dataclass(health)
    assert module.DOMAIN_MEMORY_COMPACTION_HEALTH_STATUSES == ("pass", "watch", "block")
    assert health.status == "block"
    assert health.row_count == d("3")
    assert health.domain_count == d("3")
    assert health.pass_count == d("1")
    assert health.watch_count == d("1")
    assert health.block_count == d("1")
    assert health.fresh_domain_count == d("1")
    assert health.conflict_free_domain_count == d("1")
    assert health.calibrated_domain_count == d("2")
    assert health.retrieval_ready_domain_count == d("2")
    assert health.average_domain_compaction_health_score == d("0.586111")
    assert health.reason_codes == (
        "calibration_feedback_block",
        "domain_memory_compaction_health_block",
        "domain_memory_compaction_health_watch",
        "memory_compaction_stale_block",
        "memory_compaction_watch_age",
        "memory_conflict_carry_forward_block",
        "memory_conflict_carry_forward_watch",
        "memory_retrieval_coverage_block",
        "memory_retrieval_coverage_watch",
    )
    assert health.paper_only is True
    assert health.report_only is True
    assert health.readonly is True

    assert tuple(row.row_status for row in health.rows) == ("block", "watch", "pass")
    assert health.rows[0] == module.ResearchTeamDomainMemoryCompactionHealthRow(
        team_domain="politics-research",
        compacted_memory_count=d("2"),
        latest_compacted_memory_at=GENERATED_AT - timedelta(days=45),
        memory_age_seconds=d("3888000.000000"),
        freshness_score=d("0.000000"),
        carry_forward_conflict_count=d("4"),
        conflict_carry_forward_score=d("0.000000"),
        calibration_feedback_score=d("0.350000"),
        retrieval_coverage_ratio=d("0.200000"),
        domain_compaction_health_score=d("0.137500"),
        row_status="block",
        reason_codes=(
            "calibration_feedback_block",
            "domain_memory_compaction_health_block",
            "memory_compaction_stale_block",
            "memory_conflict_carry_forward_block",
            "memory_retrieval_coverage_block",
        ),
    )
    assert health.rows[1].freshness_score == d("0.533333")
    assert health.rows[1].conflict_carry_forward_score == d("0.750000")
    assert health.rows[1].domain_compaction_health_score == d("0.658333")

    payload = module.research_team_domain_memory_compaction_health_report_payload(health)
    assert payload == health.payload
    assert payload["rows"][0]["domain_compaction_health_score"] == "0.137500"
    assert payload["rows"][0]["memory_age_seconds"] == "3888000.000000"
    assert payload["derived_validation_digest"] == health.derived_validation_digest
    assert len(health.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in health.derived_validation_digest)
    assert health.derived_validation_digest == rebuilt.derived_validation_digest
    assert health.derived_validation_digest != changed.derived_validation_digest
    _assert_no_floats(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_input_blocks_without_raw_public_identifiers() -> None:
    module = api()
    health = report()

    assert health.status == "block"
    assert health.row_count == d("0")
    assert health.domain_count == d("0")
    assert health.pass_count == d("0")
    assert health.watch_count == d("0")
    assert health.block_count == d("0")
    assert health.average_domain_compaction_health_score == d("0.000000")
    assert health.reason_codes == ("no_domain_memory_compaction_health_inputs",)
    assert health.rows == ()

    payload_text = repr(health.payload).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "auth",
        "order",
        "recommend",
        "sizing",
        "trade",
    ):
        assert forbidden not in payload_text


def test_frozen_decimal_only_flags_and_input_validation() -> None:
    module = api()
    health = report(domain_item("macro-research"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_COMPACTION_HEALTH_REPORT_CONFIG_VERSION",
        "DOMAIN_MEMORY_COMPACTION_HEALTH_STATUSES",
        "DOMAIN_MEMORY_COMPACTION_HEALTH_REASON_CODES",
        "ResearchTeamDomainMemoryCompactionHealthConfig",
        "ResearchTeamDomainMemoryCompactionHealthInput",
        "ResearchTeamDomainMemoryCompactionHealthReport",
        "ResearchTeamDomainMemoryCompactionHealthRow",
        "build_research_team_domain_memory_compaction_health_report",
        "research_team_domain_memory_compaction_health_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
    with pytest.raises(FrozenInstanceError):
        health.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="compacted_memory_count must be a Decimal"):
        domain_item("macro-research", compacted_memory_count=8)
    with pytest.raises(ValueError, match="compacted_memory_count must be a whole Decimal"):
        domain_item("macro-research", compacted_memory_count=d("8.500000"))
    with pytest.raises(ValueError, match="calibration_feedback_score must be a Decimal"):
        domain_item(
            "macro-research",
            calibration_feedback_score=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="latest_compacted_memory_at"):
        domain_item(
            "macro-research",
            latest_compacted_memory_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="latest_compacted_memory_at"):
        domain_item(
            "macro-research",
            latest_compacted_memory_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_domain"):
        domain_item(_StringSubclass("macro-research"))
    with pytest.raises(ValueError, match="public-safe"):
        domain_item("wallet")
    with pytest.raises(ValueError, match="redaction_confirmed"):
        domain_item("macro-research", redaction_confirmed=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(
            domain_item(
                "macro-research",
                latest_compacted_memory_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(health, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(health, status="blocked")


def test_payload_digest_rejects_tampering_and_static_surface_is_pure() -> None:
    module = api()
    health = report(domain_item("macro-research"))
    payload = module.research_team_domain_memory_compaction_health_report_payload(health)

    assert module.research_team_domain_memory_compaction_health_report_payload(payload) == payload
    tampered = json.loads(json.dumps(payload))
    tampered["rows"][0]["retrieval_coverage_ratio"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_memory_compaction_health_report_payload(tampered)

    object.__setattr__(health, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_memory_compaction_health_report_payload(health)

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "sizing",
        "recommend",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", "asdict"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(alias.name != "asdict" for alias in node.names)


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_floats(item)

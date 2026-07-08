from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_team_memory_retrieval_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def item(team_label: str, retrieval_lane: str, **overrides: object):
    module = api()
    values = {
        "team_label": team_label,
        "retrieval_lane": retrieval_lane,
        "retrieved_memory_count": d("4"),
        "required_memory_count": d("3"),
        "latest_retrieved_memory_at": GENERATED_AT - timedelta(seconds=3600),
        "semantic_relevance_score": d("0.900000"),
        "conflict_count": d("0"),
        "redaction_confirmed": True,
    }
    values.update(overrides)
    return module.ResearchTeamMemoryRetrievalQualityInput(**values)


def report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_memory_retrieval_quality_report(
        items,
        config=cfg or module.ResearchTeamMemoryRetrievalQualityConfig(),
        generated_at=generated_at,
    )


def test_quality_report_scores_recency_relevance_conflicts_and_sufficiency() -> None:
    module = api()
    blocked = item(
        "macro-research",
        "policy-memory",
        retrieved_memory_count=d("1"),
        required_memory_count=d("4"),
        latest_retrieved_memory_at=GENERATED_AT - timedelta(days=45),
        semantic_relevance_score=d("0.300000"),
        conflict_count=d("1"),
    )
    watched = item(
        "event-research",
        "similar-history",
        retrieved_memory_count=d("2"),
        required_memory_count=d("3"),
        latest_retrieved_memory_at=GENERATED_AT - timedelta(days=10),
        semantic_relevance_score=d("0.650000"),
        conflict_count=d("0"),
    )
    passing = item("ops-research", "decision-brief")

    quality = report(passing, blocked, watched)
    rebuilt = report(watched, passing, blocked)
    changed = report(
        passing,
        watched,
        item(
            "macro-research",
            "policy-memory",
            retrieved_memory_count=d("1"),
            required_memory_count=d("4"),
            latest_retrieved_memory_at=GENERATED_AT - timedelta(days=45),
            semantic_relevance_score=d("0.350000"),
            conflict_count=d("1"),
        ),
    )

    assert type(quality) is module.ResearchTeamMemoryRetrievalQualityReport
    assert is_dataclass(quality)
    assert quality.status == "block"
    assert quality.input_count == d("3")
    assert quality.pass_count == d("1")
    assert quality.watch_count == d("1")
    assert quality.block_count == d("1")
    assert quality.recent_count == d("1")
    assert quality.relevant_count == d("2")
    assert quality.non_conflicting_count == d("2")
    assert quality.sufficient_count == d("1")
    assert quality.average_decision_research_quality_score == d("0.619445")
    assert quality.reason_codes == (
        "memory_retrieval_conflicts_present",
        "memory_retrieval_insufficient",
        "memory_retrieval_low_relevance",
        "memory_retrieval_stale",
        "memory_retrieval_watch_age",
        "memory_retrieval_watch_sufficiency",
        "memory_retrieval_watch_relevance",
        "team_memory_retrieval_quality_block",
        "team_memory_retrieval_quality_watch",
    )
    assert quality.paper_only is True
    assert quality.report_only is True
    assert quality.readonly is True

    assert tuple(row.row_status for row in quality.rows) == ("block", "watch", "pass")
    assert quality.rows[0] == module.ResearchTeamMemoryRetrievalQualityRow(
        team_label="macro-research",
        retrieval_lane="policy-memory",
        retrieved_memory_count=d("1"),
        required_memory_count=d("4"),
        retrieval_coverage_ratio=d("0.250000"),
        memory_age_seconds=d("3888000.000000"),
        recency_score=d("0.000000"),
        semantic_relevance_score=d("0.300000"),
        conflict_count=d("1"),
        non_conflict_score=d("0.000000"),
        sufficiency_score=d("0.250000"),
        decision_research_quality_score=d("0.137500"),
        row_status="block",
        reason_codes=(
            "memory_retrieval_conflicts_present",
            "memory_retrieval_insufficient",
            "memory_retrieval_low_relevance",
            "memory_retrieval_stale",
            "team_memory_retrieval_quality_block",
        ),
    )

    payload = module.research_team_memory_retrieval_quality_report_payload(quality)
    assert payload == quality.payload
    assert payload["rows"][0]["decision_research_quality_score"] == "0.137500"
    assert payload["rows"][0]["memory_age_seconds"] == "3888000.000000"
    assert payload["derived_validation_digest"] == quality.derived_validation_digest
    assert len(quality.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in quality.derived_validation_digest)
    assert quality.derived_validation_digest == rebuilt.derived_validation_digest
    assert quality.derived_validation_digest != changed.derived_validation_digest
    _assert_no_floats(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_input_blocks_without_raw_public_identifiers() -> None:
    module = api()
    quality = report()

    assert quality.status == "block"
    assert quality.input_count == d("0")
    assert quality.row_count == d("0")
    assert quality.pass_count == d("0")
    assert quality.watch_count == d("0")
    assert quality.block_count == d("0")
    assert quality.average_decision_research_quality_score == d("0.000000")
    assert quality.reason_codes == ("no_memory_retrieval_quality_inputs",)
    assert quality.rows == ()

    payload_text = repr(quality.payload).lower()
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


def test_quality_report_is_frozen_decimal_only_public_safe_and_readonly() -> None:
    module = api()
    quality = report(item("ops-research", "decision-brief"))

    assert module.MEMORY_RETRIEVAL_QUALITY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_QUALITY_REPORT_CONFIG_VERSION",
        "MEMORY_RETRIEVAL_QUALITY_STATUSES",
        "MEMORY_RETRIEVAL_QUALITY_REASON_CODES",
        "ResearchTeamMemoryRetrievalQualityConfig",
        "ResearchTeamMemoryRetrievalQualityInput",
        "ResearchTeamMemoryRetrievalQualityReport",
        "ResearchTeamMemoryRetrievalQualityRow",
        "build_research_team_memory_retrieval_quality_report",
        "research_team_memory_retrieval_quality_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        quality.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="retrieved_memory_count must be a Decimal"):
        item("ops-research", "decision-brief", retrieved_memory_count=4)
    with pytest.raises(ValueError, match="retrieved_memory_count must be a whole Decimal"):
        item("ops-research", "decision-brief", retrieved_memory_count=d("4.500000"))
    with pytest.raises(ValueError, match="semantic_relevance_score must be a Decimal"):
        item(
            "ops-research",
            "decision-brief",
            semantic_relevance_score=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="latest_retrieved_memory_at"):
        item(
            "ops-research",
            "decision-brief",
            latest_retrieved_memory_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="latest_retrieved_memory_at"):
        item(
            "ops-research",
            "decision-brief",
            latest_retrieved_memory_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_label"):
        item(_StringSubclass("ops-research"), "decision-brief")
    with pytest.raises(ValueError, match="public-safe"):
        item("wallet", "decision-brief")
    with pytest.raises(ValueError, match="redaction_confirmed"):
        item("ops-research", "decision-brief", redaction_confirmed=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(
            item(
                "ops-research",
                "decision-brief",
                latest_retrieved_memory_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.ResearchTeamMemoryRetrievalQualityConfig(), paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(quality, derived_validation_digest="0" * 64)
    assert (
        report(
            item("ops-research", "decision-brief"),
            generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        ).generated_at
        == GENERATED_AT
    )

    _assert_public_numeric_values_are_decimal(quality)
    _assert_no_floats(quality.payload)


def test_module_scope_has_no_external_or_decision_action_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_team_memory_retrieval_quality_report.py",
    ).read_text(encoding="utf-8")
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
        "wallet",
        "account",
        "private_key",
        "api_key",
        "secret",
        "clob",
        "submit",
        "cancel",
        "signing",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
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
        "datetime",
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


def _assert_public_numeric_values_are_decimal(value: Any) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:
            _assert_public_numeric_values_are_decimal(getattr(value, field_name))
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_numeric_values_are_decimal(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_numeric_values_are_decimal(item)

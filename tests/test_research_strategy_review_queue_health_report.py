from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_review_queue_health_report import (
    DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_HEALTH_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_REVIEW_QUEUE_HEALTH_REPORT_STATUSES,
    ResearchStrategyReviewQueueHealthConfig,
    ResearchStrategyReviewQueueHealthInput,
    ResearchStrategyReviewQueueHealthReport,
    ResearchStrategyReviewQueueHealthRow,
    build_research_strategy_review_queue_health_report,
    research_strategy_review_queue_health_report_digest,
    research_strategy_review_queue_health_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_review_queue_health_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyReviewQueueHealthConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_HEALTH_REPORT_CONFIG_VERSION
        ),
        "quality_watch_floor": d("0.700000"),
        "quality_block_floor": d("0.500000"),
        "pressure_watch_threshold": d("0.300000"),
        "pressure_block_threshold": d("0.650000"),
    }
    values.update(overrides)
    return ResearchStrategyReviewQueueHealthConfig(**values)


def review_item(
    internal_review_ref: str = (
        "raw-candidate-id:alpha|market-id:m-1|market-slug:alpha|"
        "question:will-alpha|source-url:https://example.invalid/a|"
        "source-text:private note|dsn:postgres://x|table:events|token:t|"
        "wallet:0xabc|order:paper|trade:none"
    ),
    *,
    observed_at: datetime = datetime(2026, 7, 8, 15, 30, tzinfo=UTC),
    source_readiness_score: Decimal = d("0.900000"),
    cost_sanity_score: Decimal = d("0.850000"),
    resolution_ambiguity_score: Decimal = d("0.100000"),
    team_capacity_pressure_score: Decimal = d("0.200000"),
    stale_memory_pressure_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyReviewQueueHealthInput:
    return ResearchStrategyReviewQueueHealthInput(
        internal_review_ref=internal_review_ref,
        observed_at=observed_at,
        source_readiness_score=source_readiness_score,
        cost_sanity_score=cost_sanity_score,
        resolution_ambiguity_score=resolution_ambiguity_score,
        team_capacity_pressure_score=team_capacity_pressure_score,
        stale_memory_pressure_score=stale_memory_pressure_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *review_items: ResearchStrategyReviewQueueHealthInput,
    cfg: ResearchStrategyReviewQueueHealthConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyReviewQueueHealthReport:
    return build_research_strategy_review_queue_health_report(
        review_items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_report_scores_review_queue_health_for_analyst_review() -> None:
    passed = review_item("private-ref-pass")
    watched = review_item(
        "private-ref-watch",
        source_readiness_score=d("0.650000"),
        cost_sanity_score=d("0.720000"),
        resolution_ambiguity_score=d("0.350000"),
        team_capacity_pressure_score=d("0.250000"),
        stale_memory_pressure_score=d("0.200000"),
    )
    blocked = review_item(
        "private-ref-block",
        observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=timezone(timedelta(hours=-4))),
        source_readiness_score=d("0.450000"),
        cost_sanity_score=d("0.400000"),
        resolution_ambiguity_score=d("0.700000"),
        team_capacity_pressure_score=d("0.600000"),
        stale_memory_pressure_score=d("0.800000"),
    )

    first = report(watched, blocked, passed)
    second = report(passed, watched, blocked)

    assert is_dataclass(first)
    assert type(first) is ResearchStrategyReviewQueueHealthReport
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_HEALTH_REPORT_CONFIG_VERSION
    )
    assert first.review_item_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.average_queue_health_score == d("0.644667")
    assert first.minimum_quality_score == d("0.400000")
    assert first.maximum_pressure_score == d("0.800000")
    assert first.status == "block"
    assert first.analyst_review_state == "analyst_review_block"
    assert first.reason_codes == (
        "review_queue_health_report_block",
        "source_readiness_review",
        "cost_sanity_review",
        "resolution_ambiguity_review",
        "team_capacity_pressure_review",
        "stale_memory_pressure_review",
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert_digest(first.validation_digest)
    assert tuple(row.row_number for row in first.rows) == (
        ONE,
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first == second

    block_row = first.rows[0]
    assert type(block_row) is ResearchStrategyReviewQueueHealthRow
    assert block_row.observed_at == datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
    assert block_row.queue_health_score == d("0.350000")
    assert block_row.minimum_quality_score == d("0.400000")
    assert block_row.maximum_pressure_score == d("0.800000")
    assert block_row.analyst_review_state == "analyst_review_block"
    assert block_row.reason_codes == (
        "source_readiness_block",
        "cost_sanity_block",
        "resolution_ambiguity_block",
        "stale_memory_pressure_block",
        "team_capacity_pressure_watch",
    )
    assert_digest(block_row.validation_digest)

    watch_row = first.rows[1]
    assert watch_row.queue_health_score == d("0.714000")
    assert watch_row.minimum_quality_score == d("0.650000")
    assert watch_row.maximum_pressure_score == d("0.350000")
    assert watch_row.analyst_review_state == "analyst_review_watch"
    assert watch_row.reason_codes == (
        "source_readiness_watch",
        "resolution_ambiguity_watch",
    )

    pass_row = first.rows[2]
    assert pass_row.queue_health_score == d("0.870000")
    assert pass_row.minimum_quality_score == d("0.850000")
    assert pass_row.maximum_pressure_score == d("0.200000")
    assert pass_row.analyst_review_state == "analyst_review_ready"
    assert pass_row.reason_codes == ("review_queue_health_pass",)


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 12, 0, tzinfo=timezone(timedelta(hours=-4)))
    summary = report(review_item(), generated_at=generated_at)
    first_payload = research_strategy_review_queue_health_report_payload(summary)
    second_payload = research_strategy_review_queue_health_report_payload(summary)

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T16:00:00+00:00"
    assert first_payload["review_item_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["queue_health_score"] == "0.870000"
    assert first_payload["rows"][0]["minimum_quality_score"] == "0.850000"
    assert first_payload["rows"][0]["maximum_pressure_score"] == "0.200000"
    assert first_payload["rows"][0]["public_review_item_hash"].startswith("sha256:")
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "raw-candidate-id",
        "internal_review_ref",
        "market-id",
        "market_slug",
        "market-slug",
        "will-alpha",
        "source-url",
        "source-text",
        "postgres",
        "table:events",
        "token:t",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden not in payload_text

    digest = research_strategy_review_queue_health_report_digest(summary)
    assert "rows" not in digest
    assert digest["review_item_count"] == first_payload["review_item_count"]
    assert digest["status"] == "pass"
    assert digest["validation_digest"] == first_payload["validation_digest"]
    assert not any(type(value) in (int, float, Decimal) for value in walk_payload_values(digest))

    assert research_strategy_review_queue_health_report_payload(first_payload) == first_payload

    tampered = dict(first_payload)
    tampered_rows = [dict(first_payload["rows"][0])]
    tampered_rows[0]["source_readiness_score"] = "0.000001"
    tampered["rows"] = tampered_rows
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_review_queue_health_report_payload(tampered)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_review_queue_health_report_payload(
            {
                "market_id": "m-1",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_empty_report_blocks_analyst_review() -> None:
    empty = report()

    assert empty.review_item_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.average_queue_health_score is None
    assert empty.minimum_quality_score is None
    assert empty.maximum_pressure_score is None
    assert empty.status == "block"
    assert empty.analyst_review_state == "analyst_review_block"
    assert empty.reason_codes == ("review_queue_health_report_empty",)
    assert empty.rows == ()
    assert_digest(empty.validation_digest)


def test_validation_rejects_non_decimal_bad_flags_bad_times_and_duplicates() -> None:
    summary = report(review_item("private-ref-frozen"))
    row = summary.rows[0]

    assert is_dataclass(ResearchStrategyReviewQueueHealthConfig)
    assert is_dataclass(ResearchStrategyReviewQueueHealthInput)
    assert is_dataclass(ResearchStrategyReviewQueueHealthRow)
    assert is_dataclass(ResearchStrategyReviewQueueHealthReport)
    assert RESEARCH_STRATEGY_REVIEW_QUEUE_HEALTH_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadConfig(ResearchStrategyReviewQueueHealthConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        review_item(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="source_readiness_score"):
        review_item(source_readiness_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_sanity_score"):
        review_item(cost_sanity_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_ambiguity_score"):
        review_item(resolution_ambiguity_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="team_capacity_pressure_score"):
        review_item(team_capacity_pressure_score=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        review_item(observed_at=datetime(2026, 7, 8, 15, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            review_item("private-ref-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(
            review_item(
                "private-ref-future",
                observed_at=datetime(2026, 7, 8, 16, 1, tzinfo=UTC),
            ),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(review_item("private-ref-dupe"), review_item("private-ref-dupe"))
    with pytest.raises(ValueError, match="quality_watch_floor"):
        config(quality_watch_floor=d("0.400000"), quality_block_floor=d("0.500000"))
    with pytest.raises(ValueError, match="pressure_block_threshold"):
        config(
            pressure_watch_threshold=d("0.700000"),
            pressure_block_threshold=d("0.600000"),
        )

    with pytest.raises(ValueError, match="queue_health_score must match"):
        replace(row, queue_health_score=row.queue_health_score - d("0.000001"))
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="validation_digest"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(summary, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="validation_digest"):
        replace(summary, validation_digest="0" * 64)

    for value in (config(), review_item(), row, summary):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "reason_codes",
                "rows",
                "config_version",
                "internal_review_ref",
                "public_review_item_hash",
                "status",
                "analyst_review_state",
                "validation_digest",
            } or item_value is None:
                continue
            if type(item_value) is datetime:
                continue
            assert type(item_value) is Decimal, item.name


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_review_queue_health_report as module

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_HEALTH_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_REVIEW_QUEUE_HEALTH_REPORT_STATUSES",
        "ResearchStrategyReviewQueueHealthConfig",
        "ResearchStrategyReviewQueueHealthInput",
        "ResearchStrategyReviewQueueHealthReport",
        "ResearchStrategyReviewQueueHealthRow",
        "build_research_strategy_review_queue_health_report",
        "research_strategy_review_queue_health_report_digest",
        "research_strategy_review_queue_health_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "private_key",
        "api_key",
        "secret",
        "position",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "database",
        "network",
        "requests",
        "http",
        "socket",
        "subprocess",
        "trade",
        "open(",
    )
    assert [term for term in forbidden_terms if term in lowered] == []

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
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "float",
        "open",
        "send",
        "submit",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
                assert func.id != "__import__"
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

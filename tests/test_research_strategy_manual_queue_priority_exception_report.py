from __future__ import annotations

import ast
import hashlib
import inspect
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_manual_queue_priority_exception_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_REPORT_CONFIG_VERSION
        ),
        "min_pass_evidence_maturity_score": d("0.800000"),
        "min_watch_evidence_maturity_score": d("0.600000"),
        "min_pass_cost_freshness_score": d("0.800000"),
        "min_watch_cost_freshness_score": d("0.600000"),
        "min_pass_specialist_consensus_score": d("0.750000"),
        "min_watch_specialist_consensus_score": d("0.500000"),
        "max_pass_source_conflict_pressure": d("0.300000"),
        "max_watch_source_conflict_pressure": d("0.700000"),
        "max_pass_queue_age_seconds": d("86400.000000"),
        "max_watch_queue_age_seconds": d("259200.000000"),
        "max_pass_manual_escalation_urgency": d("0.300000"),
        "max_watch_manual_escalation_urgency": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchStrategyManualQueuePriorityExceptionConfig(**values)


def queue_input(
    aggregation_key: str = "queue-row-alpha",
    *,
    evidence_maturity_score: Decimal = d("0.900000"),
    cost_freshness_score: Decimal = d("0.900000"),
    specialist_consensus_score: Decimal = d("0.800000"),
    source_conflict_pressure: Decimal = d("0.100000"),
    queue_age_seconds: Decimal = d("3600.000000"),
    manual_escalation_urgency: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyManualQueuePriorityExceptionInput(
        aggregation_key=aggregation_key,
        evidence_maturity_score=evidence_maturity_score,
        cost_freshness_score=cost_freshness_score,
        specialist_consensus_score=specialist_consensus_score,
        source_conflict_pressure=source_conflict_pressure,
        queue_age_seconds=queue_age_seconds,
        manual_escalation_urgency=manual_escalation_urgency,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_strategy_manual_queue_priority_exception_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_manual_priority_review_without_side_effect_surfaces() -> None:
    module = api()
    summary = report()

    assert module.RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_STATUSES",
        "ResearchStrategyManualQueuePriorityExceptionConfig",
        "ResearchStrategyManualQueuePriorityExceptionInput",
        "ResearchStrategyManualQueuePriorityExceptionReasonCodeCount",
        "ResearchStrategyManualQueuePriorityExceptionRow",
        "ResearchStrategyManualQueuePriorityExceptionReport",
        "build_research_strategy_manual_queue_priority_exception_report",
        "research_strategy_manual_queue_priority_exception_report_payload",
        "research_strategy_manual_queue_priority_exception_report_digest",
    )
    assert type(summary) is module.ResearchStrategyManualQueuePriorityExceptionReport
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == (
        "research-strategy-manual-queue-priority-exception-report-v0"
    )
    assert summary.input_row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.mean_evidence_maturity_score == ZERO
    assert summary.mean_cost_freshness_score == ZERO
    assert summary.mean_specialist_consensus_score == ZERO
    assert summary.max_source_conflict_pressure == ZERO
    assert summary.mean_queue_age_seconds == ZERO
    assert summary.max_queue_age_seconds == ZERO
    assert summary.max_manual_escalation_urgency == ZERO
    assert summary.mean_priority_exception_score == ZERO
    assert summary.status == "block"
    assert summary.reason_codes == ("manual_queue_priority_exception_report_empty",)
    assert summary.reason_code_counts == ()
    assert summary.rows == ()
    assert len(summary.derived_validation_digest) == 64
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_report_aggregates_all_manual_queue_priority_exception_dimensions() -> None:
    summary = report(
        queue_input(
            "raw-candidate-id-only-visible-through-hash",
            evidence_maturity_score=d("0.500000"),
            cost_freshness_score=d("0.500000"),
            specialist_consensus_score=d("0.400000"),
            source_conflict_pressure=d("0.900000"),
            queue_age_seconds=d("400000.000000"),
            manual_escalation_urgency=d("0.900000"),
        ),
        queue_input("queue-row-pass"),
        queue_input(
            "queue-row-watch",
            evidence_maturity_score=d("0.700000"),
            cost_freshness_score=d("0.700000"),
            specialist_consensus_score=d("0.600000"),
            source_conflict_pressure=d("0.500000"),
            queue_age_seconds=d("172800.000000"),
            manual_escalation_urgency=d("0.500000"),
        ),
    )

    assert summary.input_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_evidence_maturity_score == d("0.700000")
    assert summary.mean_cost_freshness_score == d("0.700000")
    assert summary.mean_specialist_consensus_score == d("0.600000")
    assert summary.max_source_conflict_pressure == d("0.900000")
    assert summary.mean_queue_age_seconds == d("192133.333333")
    assert summary.max_queue_age_seconds == d("400000.000000")
    assert summary.max_manual_escalation_urgency == d("0.900000")
    assert summary.mean_priority_exception_score == d("0.505556")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "manual_queue_priority_exception_report_block",
        "evidence_maturity_exception",
        "cost_freshness_exception",
        "specialist_consensus_exception",
        "source_conflict_pressure_exception",
        "queue_age_exception",
        "manual_escalation_urgency_exception",
    )

    blocked, watched, passed = summary.rows
    assert tuple(row.aggregate_row_number for row in summary.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")
    assert blocked.aggregate_hash == hashlib.sha256(
        b"raw-candidate-id-only-visible-through-hash",
    ).hexdigest()
    assert blocked.priority_exception_score == d("1.000000")
    assert blocked.reason_codes == (
        "manual_queue_priority_exception_block",
        "evidence_maturity_block",
        "cost_freshness_block",
        "specialist_consensus_block",
        "source_conflict_pressure_block",
        "queue_age_block",
        "manual_escalation_urgency_block",
    )
    assert watched.priority_exception_score == d("0.516667")
    assert watched.reason_codes == (
        "manual_queue_priority_exception_watch",
        "evidence_maturity_watch",
        "cost_freshness_watch",
        "specialist_consensus_watch",
        "source_conflict_pressure_watch",
        "queue_age_watch",
        "manual_escalation_urgency_watch",
    )
    assert passed.priority_exception_score == ZERO
    assert passed.reason_codes == ("manual_queue_priority_exception_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["evidence_maturity_block"] == (
        api().ResearchStrategyManualQueuePriorityExceptionReasonCodeCount(
            reason_code="evidence_maturity_block",
            count=d("1.000000"),
            input_ratio=d("0.333333"),
        )
    )


def test_payload_is_deterministic_redacted_decimal_stringed_and_digest_guarded() -> None:
    module = api()
    first = report(
        queue_input("queue-row-z"),
        queue_input("queue-row-a"),
    )
    second = report(
        queue_input("queue-row-a"),
        queue_input("queue-row-z"),
    )

    first_payload = module.research_strategy_manual_queue_priority_exception_report_payload(
        first,
    )
    second_payload = module.research_strategy_manual_queue_priority_exception_report_payload(
        second,
    )

    assert first_payload == second_payload
    assert module.research_strategy_manual_queue_priority_exception_report_digest(first) == (
        module.research_strategy_manual_queue_priority_exception_report_digest(second)
    )
    assert len(module.research_strategy_manual_queue_priority_exception_report_digest(first)) == 64
    assert first_payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert first_payload["input_row_count"] == "2.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["aggregate_hash"]) == 64
    assert "aggregation_key" not in first_payload["rows"][0]
    assert first_payload["rows"][0]["priority_exception_score"] == "0.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(
        type(value) in (int, float, Decimal)
        for value in _walk_payload_values(first_payload)
    )

    payload_text = repr(first_payload).lower()
    forbidden_public_fragments = (
        "queue-row",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
    )
    assert all(fragment not in payload_text for fragment in forbidden_public_fragments)

    tampered_payload = module.research_strategy_manual_queue_priority_exception_report_payload(
        report(queue_input()),
    )
    tampered_payload["rows"][0]["queue_age_seconds"] = "999999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_manual_queue_priority_exception_report_payload(
            tampered_payload,
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_manual_queue_priority_exception_report_payload(
            {
                "market_id": "hidden",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_bad_flags_bad_times_and_duplicates() -> None:
    module = api()
    summary = report(queue_input())
    row = summary.rows[0]

    for value in (config(), queue_input(), row, summary, *summary.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "aggregation_key",
                "aggregate_hash",
                "config_version",
                "derived_validation_digest",
                "paper_only",
                "reason_codes",
                "reason_code_counts",
                "readonly",
                "report_only",
                "rows",
                "status",
            }:
                continue
            if any(
                token in item.name
                for token in ("age", "count", "number", "pressure", "ratio", "score", "urgency")
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="evidence_maturity_score"):
        queue_input(evidence_maturity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_freshness_score"):
        queue_input(cost_freshness_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="source_conflict_pressure"):
        queue_input(source_conflict_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="queue_age_seconds"):
        queue_input(queue_age_seconds=-d("1.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(queue_input(), generated_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            queue_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(queue_input("same"), queue_input("same"))
    with pytest.raises(ValueError, match="min_watch_evidence_maturity_score"):
        config(min_watch_evidence_maturity_score=d("0.900000"))
    with pytest.raises(ValueError, match="paper_only"):
        queue_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            priority_exception_score=d("0.100000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_row_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="report"):
        module.research_strategy_manual_queue_priority_exception_report_payload(object())


def test_rejects_private_identifier_surfaces_without_leaking_input_text() -> None:
    blocked_value = "raw_" + "candidate" + "_id:abc123"

    with pytest.raises(ValueError, match="unsafe") as exc_info:
        queue_input(blocked_value)

    assert blocked_value not in str(exc_info.value)


def test_owned_module_has_no_external_execution_or_private_public_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

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
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "wal" + "let",
        "or" + "der",
        "li" + "ve",
        "trad" + "ing",
        "data" + "base",
        "net" + "work",
        "request",
        "socket",
        "subprocess",
        "open(",
        "connect(",
    )
    assert all(term not in source.lower() for term in forbidden_terms)

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


def _walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(_walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_payload_values(item))
        return tuple(values)
    return (value,)

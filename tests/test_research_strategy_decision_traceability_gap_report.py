from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 19, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_decision_traceability_gap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_REPORT_CONFIG_VERSION
        ),
        "min_pass_research_evidence_link_ratio": d("0.950000"),
        "min_watch_research_evidence_link_ratio": d("0.800000"),
        "min_pass_forecast_rationale_link_ratio": d("0.950000"),
        "min_watch_forecast_rationale_link_ratio": d("0.800000"),
        "min_pass_cost_context_link_ratio": d("0.950000"),
        "min_watch_cost_context_link_ratio": d("0.800000"),
        "min_pass_settlement_rule_note_link_ratio": d("0.950000"),
        "min_watch_settlement_rule_note_link_ratio": d("0.800000"),
        "max_pass_trace_gap_pressure": d("0.050000"),
        "max_watch_trace_gap_pressure": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDecisionTraceabilityGapConfig(**values)


def trace_input(
    trace_key: str = "private-trace-pass",
    *,
    research_evidence_expected_links: Decimal = d("10"),
    research_evidence_linked_count: Decimal = d("10"),
    forecast_rationale_expected_links: Decimal = d("10"),
    forecast_rationale_linked_count: Decimal = d("10"),
    cost_context_expected_links: Decimal = d("10"),
    cost_context_linked_count: Decimal = d("10"),
    settlement_rule_note_expected_links: Decimal = d("10"),
    settlement_rule_note_linked_count: Decimal = d("10"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyDecisionTraceabilityGapInput(
        trace_key=trace_key,
        research_evidence_expected_links=research_evidence_expected_links,
        research_evidence_linked_count=research_evidence_linked_count,
        forecast_rationale_expected_links=forecast_rationale_expected_links,
        forecast_rationale_linked_count=forecast_rationale_linked_count,
        cost_context_expected_links=cost_context_expected_links,
        cost_context_linked_count=cost_context_linked_count,
        settlement_rule_note_expected_links=settlement_rule_note_expected_links,
        settlement_rule_note_linked_count=settlement_rule_note_linked_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_strategy_decision_traceability_gap_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_report_blocks_without_traceability_inputs() -> None:
    module = api()
    summary = report()

    assert module.RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_STATUSES",
        "ResearchStrategyDecisionTraceabilityGapConfig",
        "ResearchStrategyDecisionTraceabilityGapInput",
        "ResearchStrategyDecisionTraceabilityGapReasonCodeCount",
        "ResearchStrategyDecisionTraceabilityGapRow",
        "ResearchStrategyDecisionTraceabilityGapReport",
        "build_research_strategy_decision_traceability_gap_report",
        "research_strategy_decision_traceability_gap_report_payload",
        "research_strategy_decision_traceability_gap_report_digest",
    )
    assert type(summary) is module.ResearchStrategyDecisionTraceabilityGapReport
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == (
        "research-strategy-decision-traceability-gap-report-v0"
    )
    assert summary.input_row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.total_expected_links == ZERO
    assert summary.total_missing_links == ZERO
    assert summary.research_evidence_missing_links == ZERO
    assert summary.forecast_rationale_missing_links == ZERO
    assert summary.cost_context_missing_links == ZERO
    assert summary.settlement_rule_note_missing_links == ZERO
    assert summary.mean_trace_gap_pressure == ZERO
    assert summary.max_trace_gap_pressure == ZERO
    assert summary.status == "block"
    assert summary.reason_codes == ("decision_traceability_gap_report_empty",)
    assert summary.reason_code_counts == ()
    assert summary.rows == ()
    assert len(summary.derived_validation_digest) == 64
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_report_aggregates_sanitized_traceability_gaps() -> None:
    summary = report(
        trace_input(
            "raw-candidate-id-market-slug-question-source-url",
            research_evidence_expected_links=d("4"),
            research_evidence_linked_count=d("1"),
            forecast_rationale_expected_links=d("2"),
            forecast_rationale_linked_count=d("1"),
            cost_context_expected_links=d("2"),
            cost_context_linked_count=d("0"),
            settlement_rule_note_expected_links=d("1"),
            settlement_rule_note_linked_count=d("0"),
        ),
        trace_input(
            "private-trace-watch",
            research_evidence_expected_links=d("10"),
            research_evidence_linked_count=d("9"),
            forecast_rationale_expected_links=d("10"),
            forecast_rationale_linked_count=d("9"),
            cost_context_expected_links=d("10"),
            cost_context_linked_count=d("9"),
            settlement_rule_note_expected_links=d("10"),
            settlement_rule_note_linked_count=d("9"),
        ),
        trace_input("private-trace-pass"),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.input_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.total_expected_links == d("89.000000")
    assert summary.total_missing_links == d("11.000000")
    assert summary.research_evidence_missing_links == d("4.000000")
    assert summary.forecast_rationale_missing_links == d("2.000000")
    assert summary.cost_context_missing_links == d("3.000000")
    assert summary.settlement_rule_note_missing_links == d("2.000000")
    assert summary.mean_trace_gap_pressure == d("0.292593")
    assert summary.max_trace_gap_pressure == d("0.777778")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "decision_traceability_gap_report_block",
        "research_evidence_traceability_gap_exception",
        "forecast_rationale_traceability_gap_exception",
        "cost_context_traceability_gap_exception",
        "settlement_rule_note_traceability_gap_exception",
        "trace_gap_pressure_exception",
    )

    blocked, watched, passed = summary.rows
    assert tuple(row.aggregate_row_number for row in summary.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")
    assert blocked.trace_hash == hashlib.sha256(
        b"raw-candidate-id-market-slug-question-source-url",
    ).hexdigest()
    assert blocked.research_evidence_link_ratio == d("0.250000")
    assert blocked.forecast_rationale_link_ratio == d("0.500000")
    assert blocked.cost_context_link_ratio == ZERO
    assert blocked.settlement_rule_note_link_ratio == ZERO
    assert blocked.trace_gap_pressure == d("0.777778")
    assert blocked.reason_codes == (
        "decision_traceability_gap_block",
        "research_evidence_traceability_gap_block",
        "forecast_rationale_traceability_gap_block",
        "cost_context_traceability_gap_block",
        "settlement_rule_note_traceability_gap_block",
        "trace_gap_pressure_block",
    )
    assert watched.trace_gap_pressure == d("0.100000")
    assert watched.reason_codes == (
        "decision_traceability_gap_watch",
        "research_evidence_traceability_gap_watch",
        "forecast_rationale_traceability_gap_watch",
        "cost_context_traceability_gap_watch",
        "settlement_rule_note_traceability_gap_watch",
        "trace_gap_pressure_watch",
    )
    assert passed.trace_gap_pressure == ZERO
    assert passed.reason_codes == ("decision_traceability_gap_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["trace_gap_pressure_block"] == (
        api().ResearchStrategyDecisionTraceabilityGapReasonCodeCount(
            reason_code="trace_gap_pressure_block",
            count=d("1.000000"),
            input_ratio=d("0.333333"),
        )
    )


def test_payload_is_deterministic_public_safe_decimal_stringed_and_digest_guarded() -> None:
    module = api()
    first = report(trace_input("private-trace-z"), trace_input("private-trace-a"))
    second = report(trace_input("private-trace-a"), trace_input("private-trace-z"))

    first_payload = module.research_strategy_decision_traceability_gap_report_payload(first)
    second_payload = module.research_strategy_decision_traceability_gap_report_payload(
        second,
    )

    assert first_payload == second_payload
    assert module.research_strategy_decision_traceability_gap_report_digest(first) == (
        module.research_strategy_decision_traceability_gap_report_digest(second)
    )
    assert len(module.research_strategy_decision_traceability_gap_report_digest(first)) == 64
    assert first_payload["generated_at"] == "2026-07-08T19:00:00+00:00"
    assert first_payload["input_row_count"] == "2.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["trace_hash"]) == 64
    assert first_payload["rows"][0]["trace_gap_pressure"] == "0.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in _walk_payload_values(first_payload)
    )

    payload_text = repr(first_payload).lower()
    forbidden_public_fragments = (
        "private-trace",
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
        "order",
        "trade",
        "recommendation",
        "sizing",
    )
    assert all(fragment not in payload_text for fragment in forbidden_public_fragments)

    tampered_payload = module.research_strategy_decision_traceability_gap_report_payload(
        report(trace_input()),
    )
    tampered_payload["rows"][0]["total_missing_links"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_decision_traceability_gap_report_payload(
            tampered_payload,
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_decision_traceability_gap_report_payload(
            {
                "market_id": "hidden",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_bad_flags_bad_times_and_duplicates() -> None:
    module = api()
    summary = report(trace_input())
    row = summary.rows[0]

    for value in (config(), trace_input(), row, summary, *summary.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "config_version",
                "derived_validation_digest",
                "paper_only",
                "readonly",
                "reason_codes",
                "reason_code_counts",
                "report_only",
                "rows",
                "status",
                "trace_hash",
                "trace_key",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "links",
                    "number",
                    "pressure",
                    "ratio",
                )
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="research_evidence_expected_links"):
        trace_input(research_evidence_expected_links=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_context_linked_count"):
        trace_input(cost_context_linked_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="settlement_rule_note_linked_count"):
        trace_input(
            settlement_rule_note_expected_links=d("1"),
            settlement_rule_note_linked_count=d("2"),
        )
    with pytest.raises(ValueError, match="forecast_rationale_linked_count"):
        trace_input(forecast_rationale_linked_count=-d("1"))
    with pytest.raises(ValueError, match="generated_at"):
        report(trace_input(), generated_at=datetime(2026, 7, 8, 19, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            trace_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 19, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(trace_input("same"), trace_input("same"))
    with pytest.raises(ValueError, match="min_pass_research_evidence_link_ratio"):
        config(min_pass_research_evidence_link_ratio=d("0.700000"))
    with pytest.raises(ValueError, match="paper_only"):
        trace_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            total_missing_links=d("9.000000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_row_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="report"):
        module.research_strategy_decision_traceability_gap_report_payload(object())


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

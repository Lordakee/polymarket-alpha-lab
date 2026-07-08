from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_signal_to_decision_trace_report import (
    DEFAULT_RESEARCH_SIGNAL_TO_DECISION_TRACE_REPORT_CONFIG_VERSION,
    ResearchSignalToDecisionTraceConfig,
    ResearchSignalToDecisionTraceInputRow,
    ResearchSignalToDecisionTraceReasonCodeCount,
    ResearchSignalToDecisionTraceReport,
    ResearchSignalToDecisionTraceRow,
    build_research_signal_to_decision_trace_report,
    research_signal_to_decision_trace_digest,
    research_signal_to_decision_trace_report_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_signal_to_decision_trace_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSignalToDecisionTraceConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_SIGNAL_TO_DECISION_TRACE_REPORT_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("86400.000000"),
        "min_signal_strength": d("0.600000"),
        "watch_signal_strength": d("0.500000"),
        "min_evidence_count": d("2"),
        "min_evidence_quality": d("0.700000"),
        "watch_evidence_quality": d("0.500000"),
        "min_model_count": d("2"),
        "max_model_disagreement_watch": d("0.200000"),
        "max_model_disagreement_block": d("0.400000"),
        "max_cost_drag_watch": d("0.020000"),
        "max_cost_drag_block": d("0.050000"),
    }
    values.update(overrides)
    return ResearchSignalToDecisionTraceConfig(**values)


def input_row(
    trace_key: str = "trace.frontier.rules",
    *,
    signal_label: str = "frontier_rules_delta",
    observed_at: datetime | None = None,
    signal_strength: Decimal = d("0.800000"),
    evidence_count: Decimal = d("3"),
    evidence_quality: Decimal = d("0.820000"),
    model_count: Decimal = d("2"),
    model_disagreement: Decimal = d("0.100000"),
    cost_drag: Decimal = d("0.010000"),
    human_review_ready: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSignalToDecisionTraceInputRow:
    return ResearchSignalToDecisionTraceInputRow(
        trace_key=trace_key,
        signal_label=signal_label,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
        signal_strength=signal_strength,
        evidence_count=evidence_count,
        evidence_quality=evidence_quality,
        model_count=model_count,
        model_disagreement=model_disagreement,
        cost_drag=cost_drag,
        human_review_ready=human_review_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSignalToDecisionTraceConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSignalToDecisionTraceReport:
    return build_research_signal_to_decision_trace_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_score", "_seconds", "_strength")):
            assert type(item) is Decimal
        if field.name in {"model_disagreement", "cost_drag", "evidence_quality"}:
            assert type(item) is Decimal


def test_signal_to_decision_trace_reduces_pass_watch_block_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "trace.ready",
                signal_label="ready_trace",
                observed_at=GENERATED_AT - timedelta(minutes=30),
            ),
            input_row(
                "trace.watch",
                signal_label="watch_trace",
                signal_strength=d("0.550000"),
                evidence_quality=d("0.600000"),
                model_disagreement=d("0.300000"),
                cost_drag=d("0.030000"),
            ),
            input_row(
                "trace.block",
                signal_label="blocked_trace",
                evidence_count=d("0"),
                model_count=d("0"),
                model_disagreement=d("0.500000"),
                cost_drag=d("0.060000"),
                human_review_ready=False,
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_SIGNAL_TO_DECISION_TRACE_REPORT_CONFIG_VERSION
    )
    assert summary.report_status == "block"
    assert summary.trace_count == d("3.000000")
    assert summary.pass_trace_count == d("1.000000")
    assert summary.watch_trace_count == d("1.000000")
    assert summary.block_trace_count == d("1.000000")
    assert summary.evidence_gap_count == d("2.000000")
    assert summary.model_disagreement_count == d("2.000000")
    assert summary.cost_drag_count == d("2.000000")
    assert summary.human_review_block_count == d("1.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.decision_status, row.signal_label) for row in summary.rows) == (
        ("block", "blocked_trace"),
        ("watch", "watch_trace"),
        ("pass", "ready_trace"),
    )
    assert summary.rows[0].reason_codes == (
        "research_signal_to_decision_trace_cost_drag_block",
        "research_signal_to_decision_trace_evidence_missing_block",
        "research_signal_to_decision_trace_human_review_block",
        "research_signal_to_decision_trace_model_disagreement_block",
        "research_signal_to_decision_trace_model_missing_block",
    )
    assert summary.rows[1].reason_codes == (
        "research_signal_to_decision_trace_cost_drag_watch",
        "research_signal_to_decision_trace_evidence_quality_watch",
        "research_signal_to_decision_trace_model_disagreement_watch",
        "research_signal_to_decision_trace_signal_strength_watch",
    )
    assert summary.rows[2].reason_codes == (
        "research_signal_to_decision_trace_pass",
    )


def test_empty_signal_to_decision_trace_report_blocks_without_inputs() -> None:
    summary = report(())

    assert summary.report_status == "block"
    assert summary.trace_count == ZERO
    assert summary.pass_trace_count == ZERO
    assert summary.watch_trace_count == ZERO
    assert summary.block_trace_count == ZERO
    assert summary.average_audit_score == ZERO
    assert summary.minimum_audit_score == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchSignalToDecisionTraceReasonCodeCount(
            reason_code="research_signal_to_decision_trace_no_inputs",
            count=d("1.000000"),
            trace_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == ("research_signal_to_decision_trace_no_inputs",)


def test_signal_to_decision_trace_payload_is_deterministic_and_decimal_only() -> None:
    rows = (
        input_row("trace.z", signal_label="zeta_trace", cost_drag=d("0.030000")),
        input_row("trace.a", signal_label="alpha_trace"),
        input_row(
            "trace.m",
            signal_label="middle_trace",
            model_disagreement=d("0.500000"),
        ),
    )
    first = research_signal_to_decision_trace_report_payload(report(rows))
    second = research_signal_to_decision_trace_report_payload(report(tuple(reversed(rows))))

    assert first == second
    assert json.dumps(first, sort_keys=True)
    assert first["trace_count"] == "3.000000"
    assert first["rows"][0]["decision_status"] == "block"
    assert first["rows"][0]["model_disagreement"] == "0.500000"
    assert first["paper_only"] is True
    assert first["report_only"] is True
    assert first["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(first))


def test_signal_to_decision_trace_digest_is_consistent_with_report_payload() -> None:
    summary = report(
        (
            input_row("trace.ready", signal_label="ready_trace"),
            input_row(
                "trace.block",
                signal_label="blocked_trace",
                evidence_count=d("0"),
                human_review_ready=False,
            ),
        ),
    )

    payload = research_signal_to_decision_trace_report_payload(summary)
    digest = research_signal_to_decision_trace_digest(summary)

    assert digest == {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "report_status": payload["report_status"],
        "trace_count": payload["trace_count"],
        "pass_trace_count": payload["pass_trace_count"],
        "watch_trace_count": payload["watch_trace_count"],
        "block_trace_count": payload["block_trace_count"],
        "average_audit_score": payload["average_audit_score"],
        "minimum_audit_score": payload["minimum_audit_score"],
        "reason_codes": payload["reason_codes"],
        "rows": [
            {
                "trace_key": row["trace_key"],
                "signal_label": row["signal_label"],
                "decision_status": row["decision_status"],
                "audit_score": row["audit_score"],
                "reason_codes": row["reason_codes"],
            }
            for row in payload["rows"]
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    json.dumps(digest, sort_keys=True)


def test_signal_to_decision_trace_rejects_decimal_type_and_config_drift() -> None:
    assert is_dataclass(ResearchSignalToDecisionTraceConfig)
    assert is_dataclass(ResearchSignalToDecisionTraceInputRow)
    assert is_dataclass(ResearchSignalToDecisionTraceRow)
    assert is_dataclass(ResearchSignalToDecisionTraceReasonCodeCount)
    assert is_dataclass(ResearchSignalToDecisionTraceReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.cost_drag = d("0.020000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].audit_score = d("0.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("trace-v0"))
    with pytest.raises(ValueError, match="max_signal_age_seconds"):
        config(max_signal_age_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_evidence_count"):
        config(min_evidence_count=d("1.5"))
    with pytest.raises(ValueError, match="signal_strength"):
        input_row(signal_strength=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality"):
        input_row(evidence_quality=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="model_disagreement"):
        input_row(model_disagreement=Decimal("NaN"))
    with pytest.raises(ValueError, match="cost_drag"):
        input_row(cost_drag=d("-0.000001"))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_signal_to_decision_trace_public_leak_rejection() -> None:
    for field_name, bad_value in (
        ("trace_key", "candidate-alpha"),
        ("trace_key", "market-id-alpha"),
        ("signal_label", "market_question_text"),
        ("signal_label", "source_ref_link"),
        ("signal_label", "db_dsn_token"),
        ("signal_label", "wallet_order_ticket"),
        ("signal_label", "buy_sell_recommendation"),
    ):
        kwargs = {field_name: bad_value}
        with pytest.raises(ValueError, match=field_name):
            input_row(**kwargs)  # type: ignore[arg-type]

    summary = report((input_row(),))
    public = repr(asdict(summary)).lower()
    for forbidden in (
        "candidate-alpha",
        "market-id-alpha",
        "market_question_text",
        "source_ref_link",
        "db_dsn_token",
        "wallet_order_ticket",
        "buy_sell_recommendation",
    ):
        assert forbidden not in public

    object.__setattr__(summary.rows[0], "signal_label", "source_ref_link")
    with pytest.raises(ValueError, match="unsafe"):
        research_signal_to_decision_trace_report_payload(summary)


def test_signal_to_decision_trace_hard_flags_and_consistency() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)

    summary = report((input_row(),))
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="pass_trace_count"):
        replace(summary, pass_trace_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("trace.z", signal_label="zeta_trace"),
                input_row("trace.a", signal_label="alpha_trace"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="decision_status"):
        replace(summary.rows[0], decision_status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            summary.rows[0],
            reason_codes=(
                "research_signal_to_decision_trace_pass",
                "research_signal_to_decision_trace_cost_drag_watch",
            ),
        )


def test_signal_to_decision_trace_public_numeric_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_public_numbers(config())
    assert_decimal_public_numbers(input_row())
    assert_decimal_public_numbers(summary)
    assert_decimal_public_numbers(summary.rows[0])
    assert_decimal_public_numbers(summary.reason_code_counts[0])


def test_signal_to_decision_trace_public_exports_are_exact() -> None:
    import polymarket_alpha_lab.research_signal_to_decision_trace_report as trace

    assert trace.__all__ == (
        "DEFAULT_RESEARCH_SIGNAL_TO_DECISION_TRACE_REPORT_CONFIG_VERSION",
        "ResearchSignalToDecisionTraceConfig",
        "ResearchSignalToDecisionTraceInputRow",
        "ResearchSignalToDecisionTraceReasonCodeCount",
        "ResearchSignalToDecisionTraceReport",
        "ResearchSignalToDecisionTraceRow",
        "build_research_signal_to_decision_trace_report",
        "research_signal_to_decision_trace_digest",
        "research_signal_to_decision_trace_report_payload",
    )


def test_signal_to_decision_trace_module_has_no_io_or_execution_surface() -> None:
    module_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = module_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "requests",
        "http",
        "socket",
        "subprocess",
        "sqlite3",
        "psycopg",
        "supabase",
        "pathlib",
        "open(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered

    tree = ast.parse(module_text)
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

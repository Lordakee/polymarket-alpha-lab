from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_candidate_research_readiness_gate_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_candidate_research_readiness_gate_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def load_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_CANDIDATE_RESEARCH_READINESS_GATE_REPORT_CONFIG_VERSION
        ),
        "source_sufficiency_pass_floor": d("0.800000"),
        "source_sufficiency_watch_floor": d("0.600000"),
        "update_recency_pass_floor": d("0.800000"),
        "update_recency_watch_floor": d("0.600000"),
        "cost_drag_watch_ceiling": d("0.200000"),
        "cost_drag_block_ceiling": d("0.400000"),
        "liquidity_reliability_pass_floor": d("0.800000"),
        "liquidity_reliability_watch_floor": d("0.600000"),
        "resolution_clarity_pass_floor": d("0.800000"),
        "resolution_clarity_watch_floor": d("0.600000"),
        "specialist_memory_coverage_pass_floor": d("0.800000"),
        "specialist_memory_coverage_watch_floor": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCandidateResearchReadinessGateConfig(**values)


def gate_input(
    module: Any,
    research_key: str = "research-alpha",
    *,
    source_sufficiency_score: Decimal = d("0.900000"),
    update_recency_score: Decimal = d("0.900000"),
    cost_drag_pressure: Decimal = d("0.050000"),
    liquidity_reliability_score: Decimal = d("0.900000"),
    resolution_clarity_score: Decimal = d("0.900000"),
    specialist_memory_coverage_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.ResearchStrategyCandidateResearchReadinessGateInput(
        research_key=research_key,
        source_sufficiency_score=source_sufficiency_score,
        update_recency_score=update_recency_score,
        cost_drag_pressure=cost_drag_pressure,
        liquidity_reliability_score=liquidity_reliability_score,
        resolution_clarity_score=resolution_clarity_score,
        specialist_memory_coverage_score=specialist_memory_coverage_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    module: Any,
    *rows: Any,
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_candidate_research_readiness_gate_report(
        rows,
        config=cfg(module) if config is None else config,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_candidate_research_readiness_gate_payload_digest_and_statuses() -> None:
    module = load_module()
    pass_item = gate_input(module, "research-pass")
    watch_item = gate_input(
        module,
        "research-watch",
        source_sufficiency_score=d("0.700000"),
        update_recency_score=d("0.650000"),
        cost_drag_pressure=d("0.250000"),
        liquidity_reliability_score=d("0.700000"),
        resolution_clarity_score=d("0.650000"),
        specialist_memory_coverage_score=d("0.700000"),
    )
    block_item = gate_input(
        module,
        "research-block",
        source_sufficiency_score=d("0.500000"),
        update_recency_score=d("0.550000"),
        cost_drag_pressure=d("0.450000"),
        liquidity_reliability_score=d("0.400000"),
        resolution_clarity_score=d("0.500000"),
        specialist_memory_coverage_score=d("0.450000"),
    )

    first = report(module, watch_item, block_item, pass_item)
    second = report(module, pass_item, watch_item, block_item)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_CANDIDATE_RESEARCH_READINESS_GATE_REPORT_CONFIG_VERSION
    )
    assert first.candidate_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.source_sufficiency_attention_count == d("2.000000")
    assert first.update_recency_attention_count == d("2.000000")
    assert first.cost_drag_attention_count == d("2.000000")
    assert first.liquidity_reliability_attention_count == d("2.000000")
    assert first.resolution_clarity_attention_count == d("2.000000")
    assert first.specialist_memory_coverage_attention_count == d("2.000000")
    assert first.mean_source_sufficiency_score == d("0.700000")
    assert first.mean_update_recency_score == d("0.700000")
    assert first.mean_cost_drag_pressure == d("0.250000")
    assert first.mean_liquidity_reliability_score == d("0.666667")
    assert first.mean_resolution_clarity_score == d("0.683333")
    assert first.mean_specialist_memory_coverage_score == d("0.683333")
    assert first.mean_research_readiness_score == d("0.697222")
    assert first.max_cost_drag_pressure == d("0.450000")
    assert first.reason_codes == (
        "candidate_research_readiness_block",
        "cost_drag_block",
        "cost_drag_watch",
        "liquidity_reliability_block",
        "liquidity_reliability_watch",
        "resolution_clarity_block",
        "resolution_clarity_watch",
        "source_sufficiency_block",
        "source_sufficiency_watch",
        "specialist_memory_coverage_block",
        "specialist_memory_coverage_watch",
        "update_recency_block",
        "update_recency_watch",
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    assert tuple(row.aggregate_row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first.rows[0].aggregate_row_hash == hashlib.sha256(
        b"research-block",
    ).hexdigest()
    assert first.rows[0].research_readiness_score == d("0.491667")
    assert first.rows[0].reason_codes == (
        "cost_drag_block",
        "liquidity_reliability_block",
        "resolution_clarity_block",
        "source_sufficiency_block",
        "specialist_memory_coverage_block",
        "update_recency_block",
    )
    assert first.rows[2].reason_codes == ("research_readiness_clear",)
    assert not hasattr(first.rows[0], "research_key")

    payload = module.research_strategy_candidate_research_readiness_gate_report_payload(
        first,
    )
    assert payload == (
        module.research_strategy_candidate_research_readiness_gate_report_payload(second)
    )
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["candidate_count"] == "3.000000"
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["research_readiness_score"] == "0.491667"
    assert payload["public_digest"] == first.public_digest
    payload_text = json.dumps(payload, sort_keys=True)
    assert "research_key" not in payload_text
    assert "research-block" not in payload_text
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = module.research_strategy_candidate_research_readiness_gate_report_digest(
        first,
    )
    assert digest == first.public_digest
    assert_digest(digest)


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    module = load_module()

    readiness = report(module)

    assert readiness.status == "block"
    assert readiness.candidate_count == ZERO
    assert readiness.pass_count == ZERO
    assert readiness.watch_count == ZERO
    assert readiness.block_count == ZERO
    assert readiness.mean_research_readiness_score == ZERO
    assert readiness.max_cost_drag_pressure == ZERO
    assert readiness.reason_codes == ("candidate_research_readiness_no_inputs",)
    assert readiness.reason_code_counts == (
        module.ResearchStrategyCandidateResearchReadinessGateReasonCodeCount(
            reason_code="candidate_research_readiness_no_inputs",
            count=ONE,
        ),
    )
    assert readiness.rows == ()


def test_decimal_datetime_and_public_boundary_validation() -> None:
    module = load_module()

    readiness = report(
        module,
        gate_input(module),
        generated_at=datetime(
            2026,
            7,
            8,
            10,
            30,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert readiness.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="source_sufficiency_pass_floor"):
        cfg(module, source_sufficiency_pass_floor=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_sufficiency_score"):
        gate_input(module, source_sufficiency_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="update_recency_score"):
        gate_input(module, update_recency_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="cost_drag_watch_ceiling"):
        cfg(module, cost_drag_watch_ceiling=d("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(module, gate_input(module), generated_at=datetime(2026, 7, 8, 14, 30))
    with pytest.raises(ValueError, match="duplicate research_key"):
        report(
            module,
            gate_input(module, "duplicate-key"),
            gate_input(module, "duplicate-key"),
        )

    for public_value in (readiness, *readiness.rows, *readiness.reason_code_counts):
        for field in fields(public_value):
            value = getattr(public_value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_public_leak_rejection_at_construction_and_payload_boundary() -> None:
    module = load_module()
    for unsafe_value in (
        "raw_candidate_id:abc",
        "market_id:123",
        "market_slug:event",
        "question:will-it-happen",
        "source_url:https://example.invalid",
        "source_text:verbatim",
        "dsn=postgres://example",
        "table_name:research",
        "private_token=secret",
        "wallet-address",
        "order-ticket",
        "trade-ticket",
        "recommendation-note",
        "sizing-note",
        "auth-note",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            gate_input(module, research_key=unsafe_value)

    readiness = report(module, gate_input(module, "safe-research-key"))
    object.__setattr__(readiness.rows[0], "aggregate_row_hash", "source_url:https")
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_candidate_research_readiness_gate_report_payload(
            readiness,
        )


def test_hard_flags_frozen_dataclasses_and_payload_revalidation() -> None:
    module = load_module()
    readiness = report(module, gate_input(module, "frozen-research"))

    assert is_dataclass(module.ResearchStrategyCandidateResearchReadinessGateConfig)
    assert is_dataclass(module.ResearchStrategyCandidateResearchReadinessGateInput)
    assert is_dataclass(module.ResearchStrategyCandidateResearchReadinessGateRow)
    assert is_dataclass(
        module.ResearchStrategyCandidateResearchReadinessGateReasonCodeCount,
    )
    assert is_dataclass(module.ResearchStrategyCandidateResearchReadinessGateReport)
    with pytest.raises(FrozenInstanceError):
        readiness.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness.rows[0].research_readiness_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        gate_input(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        cfg(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)

    object.__setattr__(readiness.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.research_strategy_candidate_research_readiness_gate_report_payload(
            readiness,
        )


def test_unknown_reason_codes_are_rejected_from_public_diagnostics() -> None:
    module = load_module()
    readiness = report(module, gate_input(module, "known-diagnostics"))

    with pytest.raises(ValueError, match="reason_codes"):
        replace(readiness.rows[0], reason_codes=("unknown_diagnostic",))
    with pytest.raises(ValueError, match="reason_code"):
        module.ResearchStrategyCandidateResearchReadinessGateReasonCodeCount(
            reason_code="unknown_diagnostic",
            count=ONE,
        )


def test_reason_counts_public_exports_and_digest_validation() -> None:
    module = load_module()

    readiness = report(
        module,
        gate_input(
            module,
            "watch-one",
            source_sufficiency_score=d("0.700000"),
            specialist_memory_coverage_score=d("0.700000"),
        ),
        gate_input(
            module,
            "watch-two",
            update_recency_score=d("0.700000"),
            specialist_memory_coverage_score=d("0.700000"),
        ),
        gate_input(module, "pass-one"),
    )

    assert tuple(row.status for row in readiness.rows) == ("watch", "watch", "pass")
    assert readiness.status == "watch"
    assert readiness.reason_code_counts == (
        module.ResearchStrategyCandidateResearchReadinessGateReasonCodeCount(
            reason_code="specialist_memory_coverage_watch",
            count=d("2.000000"),
        ),
        module.ResearchStrategyCandidateResearchReadinessGateReasonCodeCount(
            reason_code="research_readiness_clear",
            count=ONE,
        ),
        module.ResearchStrategyCandidateResearchReadinessGateReasonCodeCount(
            reason_code="source_sufficiency_watch",
            count=ONE,
        ),
        module.ResearchStrategyCandidateResearchReadinessGateReasonCodeCount(
            reason_code="update_recency_watch",
            count=ONE,
        ),
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_RESEARCH_READINESS_GATE_REPORT_CONFIG_VERSION",
        "ResearchStrategyCandidateResearchReadinessGateConfig",
        "ResearchStrategyCandidateResearchReadinessGateInput",
        "ResearchStrategyCandidateResearchReadinessGateReasonCodeCount",
        "ResearchStrategyCandidateResearchReadinessGateReport",
        "ResearchStrategyCandidateResearchReadinessGateRow",
        "build_research_strategy_candidate_research_readiness_gate_report",
        "research_strategy_candidate_research_readiness_gate_report_digest",
        "research_strategy_candidate_research_readiness_gate_report_payload",
    )

    with pytest.raises(ValueError, match="public_digest"):
        replace(readiness, public_digest="0" * 64)
    with pytest.raises(ValueError, match="candidate_count"):
        replace(readiness, candidate_count=d("9.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(readiness, status="pass")
    with pytest.raises(ValueError, match="status"):
        replace(readiness.rows[0], status="review")


def test_static_forbidden_public_surfaces_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "raw_candidate_id",
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
        "trading",
        "position_size",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "auth",
        "database",
        "network",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
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

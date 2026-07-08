from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_decision_readiness_gate_report import (
    DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_GATE_REPORT_CONFIG_VERSION,
    ResearchStrategyDecisionReadinessGateCandidate,
    ResearchStrategyDecisionReadinessGateConfig,
    ResearchStrategyDecisionReadinessGateReport,
    ResearchStrategyDecisionReadinessGateRow,
    build_research_strategy_decision_readiness_gate_report,
    research_strategy_decision_readiness_gate_report_digest,
    research_strategy_decision_readiness_gate_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_decision_readiness_gate_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyDecisionReadinessGateConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_GATE_REPORT_CONFIG_VERSION
        ),
        "min_evidence_item_count": d("3.000000"),
        "evidence_item_count_pass_floor": d("4.000000"),
        "min_independent_source_count": d("2.000000"),
        "independent_source_count_pass_floor": d("3.000000"),
        "source_agreement_watch_floor": d("0.750000"),
        "source_agreement_block_floor": d("0.500000"),
        "source_conflict_watch_ceiling": d("0.300000"),
        "source_conflict_block_ceiling": d("0.600000"),
        "liquidity_sanity_watch_floor": d("0.700000"),
        "liquidity_sanity_block_floor": d("0.400000"),
        "cost_sanity_watch_floor": d("0.700000"),
        "cost_sanity_block_floor": d("0.400000"),
        "review_coverage_watch_floor": d("0.750000"),
        "review_coverage_block_floor": d("0.500000"),
        "unresolved_review_watch_ceiling": d("0.000000"),
        "unresolved_review_block_ceiling": d("2.000000"),
    }
    values.update(overrides)
    return ResearchStrategyDecisionReadinessGateConfig(**values)


def candidate(
    candidate_ref: str = "slot-alpha",
    *,
    evidence_item_count: Decimal = d("5.000000"),
    independent_source_count: Decimal = d("3.000000"),
    source_agreement_score: Decimal = d("0.900000"),
    source_conflict_score: Decimal = d("0.050000"),
    liquidity_sanity_score: Decimal = d("0.850000"),
    cost_sanity_score: Decimal = d("0.900000"),
    review_coverage_score: Decimal = d("0.900000"),
    unresolved_review_count: Decimal = ZERO,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyDecisionReadinessGateCandidate:
    return ResearchStrategyDecisionReadinessGateCandidate(
        candidate_ref=candidate_ref,
        evidence_item_count=evidence_item_count,
        independent_source_count=independent_source_count,
        source_agreement_score=source_agreement_score,
        source_conflict_score=source_conflict_score,
        liquidity_sanity_score=liquidity_sanity_score,
        cost_sanity_score=cost_sanity_score,
        review_coverage_score=review_coverage_score,
        unresolved_review_count=unresolved_review_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchStrategyDecisionReadinessGateCandidate,
    cfg: ResearchStrategyDecisionReadinessGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyDecisionReadinessGateReport:
    return build_research_strategy_decision_readiness_gate_report(
        rows,
        config=config() if cfg is None else cfg,
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


def test_pass_watch_block_readiness_gate_and_deterministic_payload() -> None:
    inputs = (
        candidate("slot-pass"),
        candidate(
            "slot-watch",
            evidence_item_count=d("3.000000"),
            independent_source_count=d("2.000000"),
            liquidity_sanity_score=d("0.650000"),
            review_coverage_score=d("0.700000"),
        ),
        candidate(
            "slot-block",
            evidence_item_count=d("1.000000"),
            independent_source_count=ZERO,
            source_agreement_score=d("0.400000"),
            source_conflict_score=d("0.700000"),
            liquidity_sanity_score=d("0.200000"),
            cost_sanity_score=d("0.300000"),
            review_coverage_score=d("0.200000"),
            unresolved_review_count=d("2.000000"),
        ),
    )
    first = report(*inputs)
    second = report(*reversed(inputs))

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_GATE_REPORT_CONFIG_VERSION
    )
    assert first.candidate_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.gate_status == "block"
    assert first.manual_decision_review_state == "manual_decision_review_block"
    assert first.reason_codes == (
        "evidence_item_count_block",
        "independent_source_count_block",
        "source_agreement_block",
        "source_conflict_block",
        "liquidity_sanity_block",
        "cost_sanity_block",
        "review_coverage_block",
        "unresolved_review_block",
        "decision_readiness_gate_block",
        "evidence_item_count_watch",
        "independent_source_count_watch",
        "liquidity_sanity_watch",
        "review_coverage_watch",
    )
    assert tuple(row.candidate_ref for row in first.rows) == (
        "slot-block",
        "slot-watch",
        "slot-pass",
    )
    assert tuple(row.gate_status for row in first.rows) == ("block", "watch", "pass")

    blocked = first.rows[0]
    assert blocked.evidence_coverage_ratio == d("0.250000")
    assert blocked.independent_source_ratio == ZERO
    assert blocked.source_consensus_score == d("0.350000")
    assert blocked.readiness_score == d("0.235714")
    assert blocked.reason_codes == (
        "evidence_item_count_block",
        "independent_source_count_block",
        "source_agreement_block",
        "source_conflict_block",
        "liquidity_sanity_block",
        "cost_sanity_block",
        "review_coverage_block",
        "unresolved_review_block",
    )
    assert_digest(blocked.validation_digest)
    assert_digest(first.validation_digest)

    payload = research_strategy_decision_readiness_gate_report_payload(first)
    assert payload == research_strategy_decision_readiness_gate_report_payload(second)
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["candidate_count"] == "3.000000"
    assert payload["rows"][0]["readiness_score"] == "0.235714"
    assert payload["rows"][0]["validation_digest"] == blocked.validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = research_strategy_decision_readiness_gate_report_digest(first)
    assert "rows" not in digest
    assert digest["candidate_count"] == payload["candidate_count"]
    assert digest["gate_status"] == "block"
    assert digest["validation_digest"] == first.validation_digest
    assert_no_float_or_int_values(digest)


def test_empty_report_blocks_before_manual_decision_review() -> None:
    gate = report()

    assert gate.candidate_count == ZERO
    assert gate.pass_count == ZERO
    assert gate.watch_count == ZERO
    assert gate.block_count == ZERO
    assert gate.min_readiness_score is None
    assert gate.gate_status == "block"
    assert gate.manual_decision_review_state == "manual_decision_review_block"
    assert gate.reason_codes == ("decision_readiness_gate_no_candidates",)
    assert gate.rows == ()
    assert gate.paper_only is True
    assert gate.report_only is True
    assert gate.readonly is True
    assert_digest(gate.validation_digest)


def test_decimal_only_frozen_flags_and_input_validation() -> None:
    gate = report(candidate("slot-frozen"))

    assert is_dataclass(ResearchStrategyDecisionReadinessGateConfig)
    assert is_dataclass(ResearchStrategyDecisionReadinessGateCandidate)
    assert is_dataclass(ResearchStrategyDecisionReadinessGateRow)
    assert is_dataclass(ResearchStrategyDecisionReadinessGateReport)
    with pytest.raises(FrozenInstanceError):
        gate.gate_status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gate.rows[0].readiness_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(gate, readonly=False)

    with pytest.raises(ValueError, match="evidence_item_count"):
        candidate(evidence_item_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_agreement_score"):
        candidate(source_agreement_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_sanity_score"):
        candidate(cost_sanity_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="independent_source_count"):
        candidate(
            evidence_item_count=d("1.000000"),
            independent_source_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="candidate_ref"):
        report(candidate("slot-dupe"), candidate("slot-dupe"))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("slot-time"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="evidence_item_count_pass_floor"):
        config(
            min_evidence_item_count=d("4.000000"),
            evidence_item_count_pass_floor=d("3.000000"),
        )
    with pytest.raises(ValueError, match="source_conflict_watch_ceiling"):
        config(
            source_conflict_watch_ceiling=d("0.700000"),
            source_conflict_block_ceiling=d("0.600000"),
        )

    for item in (gate, *gate.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, tuple):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_validation_digest_and_payload_reject_tampering() -> None:
    gate = report(candidate("slot-consistent"))
    row = gate.rows[0]

    with pytest.raises(ValueError, match="readiness_score must match"):
        replace(row, readiness_score=row.readiness_score - d("0.000001"))
    with pytest.raises(ValueError, match="gate_status must match"):
        replace(row, gate_status="block")
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(gate, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(gate, rows=(report(candidate("slot-zeta")).rows[0], row))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(gate, validation_digest="0" * 64)

    payload = research_strategy_decision_readiness_gate_report_payload(gate)
    assert research_strategy_decision_readiness_gate_report_payload(payload) == payload
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_decision_readiness_gate_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_decision_readiness_gate_report_payload(
            {**payload, "wal" "let": {"address": "0x0"}},
        )
    with pytest.raises(ValueError, match="numeric"):
        research_strategy_decision_readiness_gate_report_payload(
            {**payload, "candidate_count": 1},
        )


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_decision_readiness_gate_report as gate

    assert gate.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DECISION_READINESS_GATE_REPORT_CONFIG_VERSION",
        "ResearchStrategyDecisionReadinessGateCandidate",
        "ResearchStrategyDecisionReadinessGateConfig",
        "ResearchStrategyDecisionReadinessGateReport",
        "ResearchStrategyDecisionReadinessGateRow",
        "build_research_strategy_decision_readiness_gate_report",
        "research_strategy_decision_readiness_gate_report_digest",
        "research_strategy_decision_readiness_gate_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "live",
        "auth",
        "wal" "let",
        "broker",
        "or" "der",
        "cancel",
        "replace",
        "exchange",
        "private_key",
        "api_key",
        "sec" "ret",
        "position",
        "b" "uy",
        "se" "ll",
        "reco" "mmend",
        "sizing",
        "database",
        "network",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
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
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports

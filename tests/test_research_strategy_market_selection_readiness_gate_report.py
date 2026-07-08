from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_market_selection_readiness_gate_report import (
    DEFAULT_RESEARCH_STRATEGY_MARKET_SELECTION_READINESS_GATE_REPORT_CONFIG_VERSION,
    ResearchStrategyMarketSelectionReadinessGateCandidate,
    ResearchStrategyMarketSelectionReadinessGateConfig,
    ResearchStrategyMarketSelectionReadinessGateReasonCodeCount,
    ResearchStrategyMarketSelectionReadinessGateReport,
    ResearchStrategyMarketSelectionReadinessGateRow,
    build_research_strategy_market_selection_readiness_gate_report,
    research_strategy_market_selection_readiness_gate_report_digest,
    research_strategy_market_selection_readiness_gate_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_market_selection_readiness_gate_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyMarketSelectionReadinessGateConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_MARKET_SELECTION_READINESS_GATE_REPORT_CONFIG_VERSION
        ),
        "evidence_maturity_pass_floor": d("0.800000"),
        "evidence_maturity_watch_floor": d("0.600000"),
        "liquidity_cost_freshness_pass_floor": d("0.800000"),
        "liquidity_cost_freshness_watch_floor": d("0.600000"),
        "settlement_clarity_pass_floor": d("0.800000"),
        "settlement_clarity_watch_floor": d("0.600000"),
        "domain_memory_quality_pass_floor": d("0.750000"),
        "domain_memory_quality_watch_floor": d("0.550000"),
        "conflict_pressure_watch_ceiling": d("0.250000"),
        "conflict_pressure_block_ceiling": d("0.600000"),
    }
    values.update(overrides)
    return ResearchStrategyMarketSelectionReadinessGateConfig(**values)


def candidate(
    screening_key: str = "internal-candidate-pass",
    *,
    evidence_maturity_score: Decimal = d("0.900000"),
    liquidity_cost_freshness_score: Decimal = d("0.850000"),
    settlement_clarity_score: Decimal = d("0.880000"),
    domain_memory_quality_score: Decimal = d("0.800000"),
    conflict_pressure_score: Decimal = d("0.100000"),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=5),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyMarketSelectionReadinessGateCandidate:
    return ResearchStrategyMarketSelectionReadinessGateCandidate(
        screening_key=screening_key,
        evidence_maturity_score=evidence_maturity_score,
        liquidity_cost_freshness_score=liquidity_cost_freshness_score,
        settlement_clarity_score=settlement_clarity_score,
        domain_memory_quality_score=domain_memory_quality_score,
        conflict_pressure_score=conflict_pressure_score,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchStrategyMarketSelectionReadinessGateCandidate,
    cfg: ResearchStrategyMarketSelectionReadinessGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyMarketSelectionReadinessGateReport:
    return build_research_strategy_market_selection_readiness_gate_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, bool):
        return
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


def test_readiness_gate_aggregates_pass_watch_block_rows_deterministically() -> None:
    pass_item = candidate("internal-candidate-pass")
    watch_item = candidate(
        "internal-candidate-watch",
        evidence_maturity_score=d("0.700000"),
        liquidity_cost_freshness_score=d("0.650000"),
        settlement_clarity_score=d("0.700000"),
        domain_memory_quality_score=d("0.600000"),
        conflict_pressure_score=d("0.300000"),
    )
    block_item = candidate(
        "internal-candidate-block",
        evidence_maturity_score=d("0.500000"),
        liquidity_cost_freshness_score=d("0.400000"),
        settlement_clarity_score=d("0.550000"),
        domain_memory_quality_score=d("0.400000"),
        conflict_pressure_score=d("0.700000"),
    )

    first = report(watch_item, block_item, pass_item)
    second = report(pass_item, watch_item, block_item)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_MARKET_SELECTION_READINESS_GATE_REPORT_CONFIG_VERSION
    )
    assert first.candidate_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.average_readiness_score == d("0.655333")
    assert first.min_readiness_score == d("0.430000")
    assert first.max_conflict_pressure_score == d("0.700000")
    assert tuple(row.row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert len({row.public_candidate_hash for row in first.rows}) == 3
    assert all(row.public_candidate_hash.startswith("sha256:") for row in first.rows)
    assert all("internal-candidate" not in row.public_candidate_hash for row in first.rows)

    blocked = first.rows[0]
    assert blocked.conflict_clearance_score == d("0.300000")
    assert blocked.market_selection_readiness_score == d("0.430000")
    assert blocked.reason_codes == (
        "evidence_maturity_block",
        "liquidity_cost_freshness_block",
        "settlement_clarity_block",
        "domain_memory_quality_block",
        "conflict_pressure_block",
    )
    assert_digest(blocked.validation_digest)
    assert_digest(first.validation_digest)

    payload = research_strategy_market_selection_readiness_gate_report_payload(first)
    assert payload == research_strategy_market_selection_readiness_gate_report_payload(
        second,
    )
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["candidate_count"] == "3.000000"
    assert payload["average_readiness_score"] == "0.655333"
    assert payload["rows"][0]["row_number"] == "1.000000"
    assert payload["rows"][0]["market_selection_readiness_score"] == "0.430000"
    assert payload["rows"][0]["validation_digest"] == blocked.validation_digest
    serialized = json.dumps(payload, sort_keys=True)
    assert "internal-candidate" not in serialized
    assert "screening_key" not in serialized
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = research_strategy_market_selection_readiness_gate_report_digest(first)
    assert digest == first.validation_digest
    assert digest == payload["validation_digest"]


def test_empty_report_blocks_with_reason_count() -> None:
    gate = report()

    assert gate.candidate_count == ZERO
    assert gate.pass_count == ZERO
    assert gate.watch_count == ZERO
    assert gate.block_count == ZERO
    assert gate.average_readiness_score == ZERO
    assert gate.min_readiness_score == ZERO
    assert gate.max_conflict_pressure_score == ZERO
    assert gate.status == "block"
    assert gate.reason_codes == ("market_selection_readiness_no_candidates",)
    assert gate.reason_code_counts == (
        ResearchStrategyMarketSelectionReadinessGateReasonCodeCount(
            reason_code="market_selection_readiness_no_candidates",
            count=d("1.000000"),
        ),
    )
    assert gate.rows == ()
    assert gate.paper_only is True
    assert gate.report_only is True
    assert gate.readonly is True
    assert_digest(gate.validation_digest)


def test_decimal_only_frozen_flags_and_validation() -> None:
    gate = report(candidate("internal-candidate-frozen"))

    assert is_dataclass(ResearchStrategyMarketSelectionReadinessGateConfig)
    assert is_dataclass(ResearchStrategyMarketSelectionReadinessGateCandidate)
    assert is_dataclass(ResearchStrategyMarketSelectionReadinessGateRow)
    assert is_dataclass(ResearchStrategyMarketSelectionReadinessGateReasonCodeCount)
    assert is_dataclass(ResearchStrategyMarketSelectionReadinessGateReport)
    with pytest.raises(FrozenInstanceError):
        gate.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gate.rows[0].market_selection_readiness_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(gate, readonly=False)

    with pytest.raises(ValueError, match="evidence_maturity_score"):
        candidate(evidence_maturity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_cost_freshness_score"):
        candidate(liquidity_cost_freshness_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="settlement_clarity_score"):
        candidate(settlement_clarity_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=datetime(2026, 7, 8, 15, 55))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=datetime(2026, 7, 8, 15, 55, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate(
                "internal-candidate-time",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("internal-candidate-aware"),
            generated_at=datetime(2026, 7, 8, 16, 0),
        )
    with pytest.raises(ValueError, match="screening_key"):
        report(
            candidate("internal-candidate-dupe"),
            candidate("internal-candidate-dupe"),
        )
    with pytest.raises(ValueError, match="evidence_maturity_pass_floor"):
        config(
            evidence_maturity_pass_floor=d("0.500000"),
            evidence_maturity_watch_floor=d("0.600000"),
        )
    with pytest.raises(ValueError, match="conflict_pressure_watch_ceiling"):
        config(
            conflict_pressure_watch_ceiling=d("0.700000"),
            conflict_pressure_block_ceiling=d("0.600000"),
        )

    for item in (gate, *gate.rows, *gate.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, tuple):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_payload_rejects_tampering_and_unsafe_public_leaks() -> None:
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
        "order-id",
        "trade-id",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            candidate(screening_key=unsafe_value)

    gate = report(candidate("internal-candidate-consistent"))
    row = gate.rows[0]

    with pytest.raises(ValueError, match="market_selection_readiness_score must match"):
        replace(
            row,
            market_selection_readiness_score=(
                row.market_selection_readiness_score - d("0.000001")
            ),
        )
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(gate, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(gate, rows=(report(candidate("internal-candidate-zeta")).rows[0], row))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(gate, validation_digest="0" * 64)

    payload = research_strategy_market_selection_readiness_gate_report_payload(gate)
    assert research_strategy_market_selection_readiness_gate_report_payload(payload) == payload
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_market_selection_readiness_gate_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_market_selection_readiness_gate_report_payload(
            {**payload, "wal" "let": {"address": "0x0"}},
        )
    with pytest.raises(ValueError, match="numeric"):
        research_strategy_market_selection_readiness_gate_report_payload(
            {**payload, "candidate_count": 1},
        )
    tampered = dict(payload)
    tampered["average_readiness_score"] = "0.655334"
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_market_selection_readiness_gate_report_payload(tampered)

    object.__setattr__(gate.rows[0], "public_candidate_hash", "source_url:https")
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_market_selection_readiness_gate_report_payload(gate)


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_market_selection_readiness_gate_report as gate

    assert gate.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_MARKET_SELECTION_READINESS_GATE_REPORT_CONFIG_VERSION",
        "ResearchStrategyMarketSelectionReadinessGateCandidate",
        "ResearchStrategyMarketSelectionReadinessGateConfig",
        "ResearchStrategyMarketSelectionReadinessGateReasonCodeCount",
        "ResearchStrategyMarketSelectionReadinessGateReport",
        "ResearchStrategyMarketSelectionReadinessGateRow",
        "build_research_strategy_market_selection_readiness_gate_report",
        "research_strategy_market_selection_readiness_gate_report_digest",
        "research_strategy_market_selection_readiness_gate_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "slug",
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

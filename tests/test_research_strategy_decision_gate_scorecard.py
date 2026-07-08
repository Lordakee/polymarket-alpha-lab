from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_decision_gate_scorecard import (
    DEFAULT_RESEARCH_STRATEGY_DECISION_GATE_SCORECARD_CONFIG_VERSION,
    ResearchStrategyDecisionGateScorecardCandidate,
    ResearchStrategyDecisionGateScorecardConfig,
    ResearchStrategyDecisionGateScorecardReasonCodeCount,
    ResearchStrategyDecisionGateScorecardReport,
    ResearchStrategyDecisionGateScorecardRow,
    build_research_strategy_decision_gate_scorecard_report,
    research_strategy_decision_gate_scorecard_digest,
    research_strategy_decision_gate_scorecard_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_decision_gate_scorecard.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyDecisionGateScorecardConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_STRATEGY_DECISION_GATE_SCORECARD_CONFIG_VERSION,
        "evidence_watch_floor": d("0.700000"),
        "evidence_block_floor": d("0.400000"),
        "freshness_watch_floor": d("0.600000"),
        "freshness_block_floor": d("0.300000"),
        "scope_fit_watch_floor": d("0.700000"),
        "scope_fit_block_floor": d("0.500000"),
        "contradiction_watch_ceiling": d("0.300000"),
        "contradiction_block_ceiling": d("0.600000"),
        "complexity_watch_ceiling": d("0.700000"),
    }
    values.update(overrides)
    return ResearchStrategyDecisionGateScorecardConfig(**values)


def candidate(
    decision_slot: str = "slot-alpha",
    *,
    evidence_score: Decimal = d("0.900000"),
    freshness_score: Decimal = d("0.900000"),
    scope_fit_score: Decimal = d("0.900000"),
    contradiction_score: Decimal = d("0.050000"),
    complexity_score: Decimal = d("0.200000"),
    hard_flags: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyDecisionGateScorecardCandidate:
    return ResearchStrategyDecisionGateScorecardCandidate(
        decision_slot=decision_slot,
        evidence_score=evidence_score,
        freshness_score=freshness_score,
        scope_fit_score=scope_fit_score,
        contradiction_score=contradiction_score,
        complexity_score=complexity_score,
        hard_flags=hard_flags,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchStrategyDecisionGateScorecardCandidate,
    cfg: ResearchStrategyDecisionGateScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyDecisionGateScorecardReport:
    return build_research_strategy_decision_gate_scorecard_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def assert_public_statuses_only(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "public_status":
                assert item in {"pass", "watch", "block"}
            assert_public_statuses_only(item)
    elif isinstance(value, list):
        for item in value:
            assert_public_statuses_only(item)


def test_pass_watch_block_scorecard_uses_decimal_public_payload_strings() -> None:
    gate = report(
        candidate("slot-pass"),
        candidate("slot-watch", evidence_score=d("0.650000")),
        candidate("slot-block", contradiction_score=d("0.700000")),
    )

    assert is_dataclass(gate)
    assert gate.generated_at == GENERATED_AT
    assert gate.config_version == (
        DEFAULT_RESEARCH_STRATEGY_DECISION_GATE_SCORECARD_CONFIG_VERSION
    )
    assert gate.candidate_count == d("3.000000")
    assert gate.pass_count == d("1.000000")
    assert gate.watch_count == d("1.000000")
    assert gate.block_count == d("1.000000")
    assert gate.hard_flag_count == ZERO
    assert gate.public_status == "block"
    assert gate.manual_research_state == "manual_research_block"
    assert gate.reason_codes == (
        "contradiction_high_block",
        "decision_gate_scorecard_block",
        "evidence_low_watch",
    )
    assert tuple(row.decision_slot for row in gate.candidate_rows) == (
        "slot-block",
        "slot-watch",
        "slot-pass",
    )
    assert tuple(row.public_status for row in gate.candidate_rows) == (
        "block",
        "watch",
        "pass",
    )

    payload = research_strategy_decision_gate_scorecard_payload(gate)
    assert payload["candidate_count"] == "3.000000"
    assert payload["candidate_rows"][0]["gate_score"] == "0.610000"
    assert payload["candidate_rows"][0]["public_status"] == "block"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)
    assert_public_statuses_only(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_inputs_block_before_manual_research() -> None:
    gate = report()

    assert gate.public_status == "block"
    assert gate.manual_research_state == "manual_research_block"
    assert gate.candidate_count == ZERO
    assert gate.pass_count == ZERO
    assert gate.watch_count == ZERO
    assert gate.block_count == ZERO
    assert gate.mean_gate_score == ZERO
    assert gate.min_gate_score == ZERO
    assert gate.reason_codes == ("decision_gate_scorecard_no_inputs",)
    assert gate.reason_code_counts == (
        ResearchStrategyDecisionGateScorecardReasonCodeCount(
            reason_code="decision_gate_scorecard_no_inputs",
            count=ONE,
        ),
    )
    assert gate.candidate_rows == ()


def test_decimal_type_rejection_frozen_dataclasses_and_exact_public_types() -> None:
    gate = report(candidate("slot-frozen"))

    assert is_dataclass(ResearchStrategyDecisionGateScorecardConfig)
    assert is_dataclass(ResearchStrategyDecisionGateScorecardCandidate)
    assert is_dataclass(ResearchStrategyDecisionGateScorecardRow)
    assert is_dataclass(ResearchStrategyDecisionGateScorecardReasonCodeCount)
    assert is_dataclass(ResearchStrategyDecisionGateScorecardReport)
    with pytest.raises(FrozenInstanceError):
        gate.public_status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gate.candidate_rows[0].gate_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(gate, readonly=False)

    with pytest.raises(ValueError, match="evidence_score"):
        candidate(evidence_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="freshness_score"):
        candidate(freshness_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="scope_fit_score"):
        candidate(scope_fit_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="evidence_watch_floor"):
        config(evidence_watch_floor=d("0.300000"))
    with pytest.raises(ValueError, match="complexity_watch_ceiling"):
        config(complexity_watch_ceiling=d("1.000001"))

    for item in (gate, *gate.candidate_rows, *gate.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_public_leak_rejection_for_constructor_and_tampered_report() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        candidate(decision_slot="raw_candidate_id_123")
    with pytest.raises(ValueError, match="unsafe"):
        candidate(decision_slot="market_slug_binary")
    with pytest.raises(ValueError, match="hard_flags"):
        candidate(hard_flags=("source_url_present",))

    gate = report(candidate("slot-safe"))
    object.__setattr__(gate.candidate_rows[0], "decision_slot", "market_id_abc")
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_decision_gate_scorecard_payload(gate)

    gate = report(candidate("slot-state"))
    object.__setattr__(gate.candidate_rows[0], "manual_research_state", "recommend_buy")
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_decision_gate_scorecard_payload(gate)


def test_hard_flags_force_block_and_roll_up_reason_counts() -> None:
    gate = report(
        candidate(
            "slot-hard-flag",
            hard_flags=("resolution_ambiguous", "restricted_dependency"),
        ),
        candidate("slot-pass"),
    )

    assert gate.public_status == "block"
    assert gate.block_count == d("1.000000")
    assert gate.hard_flag_count == d("1.000000")
    blocked_row = gate.candidate_rows[0]
    assert blocked_row.decision_slot == "slot-hard-flag"
    assert blocked_row.public_status == "block"
    assert blocked_row.manual_research_state == "manual_research_block"
    assert blocked_row.reason_codes == (
        "hard_flag_resolution_ambiguous",
        "hard_flag_restricted_dependency",
    )
    assert gate.reason_codes == (
        "decision_gate_scorecard_block",
        "hard_flag_resolution_ambiguous",
        "hard_flag_restricted_dependency",
    )
    assert gate.reason_code_counts[:2] == (
        ResearchStrategyDecisionGateScorecardReasonCodeCount(
            reason_code="decision_gate_clear",
            count=ONE,
        ),
        ResearchStrategyDecisionGateScorecardReasonCodeCount(
            reason_code="hard_flag_resolution_ambiguous",
            count=ONE,
        ),
    )


def test_deterministic_payload_and_digest_are_consistent() -> None:
    rows = (
        candidate("slot-zeta", evidence_score=d("0.650000")),
        candidate("slot-beta", contradiction_score=d("0.700000")),
        candidate("slot-alpha"),
    )

    first = report(*rows)
    second = report(*reversed(rows))
    first_payload = research_strategy_decision_gate_scorecard_payload(first)
    second_payload = research_strategy_decision_gate_scorecard_payload(second)
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )

    digest = research_strategy_decision_gate_scorecard_digest(first)
    assert "candidate_rows" not in digest
    for key in (
        "generated_at",
        "config_version",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "hard_flag_count",
        "mean_gate_score",
        "min_gate_score",
        "public_status",
        "manual_research_state",
        "reason_codes",
        "reason_code_counts",
        "paper_only",
        "report_only",
        "readonly",
    ):
        assert digest[key] == first_payload[key]
    assert_no_float(digest)
    assert_public_statuses_only(digest)


def test_report_revalidates_digest_consistency_and_tampered_public_values() -> None:
    gate = report(candidate("slot-consistent"))

    with pytest.raises(ValueError, match="candidate_count"):
        replace(gate, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="public_status"):
        replace(gate, public_status="watch")
    with pytest.raises(ValueError, match="mean_gate_score"):
        replace(gate, mean_gate_score=d("0.000000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(gate, reason_code_counts=())

    object.__setattr__(gate.candidate_rows[0], "gate_score", d("0.9000000"))
    with pytest.raises(ValueError, match="six decimal"):
        research_strategy_decision_gate_scorecard_payload(gate)

    with pytest.raises(
        ValueError,
        match="ResearchStrategyDecisionGateScorecardReport",
    ):
        research_strategy_decision_gate_scorecard_digest(
            {"paper_only": True, "report_only": True, "readonly": True},  # type: ignore[arg-type]
        )


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_decision_gate_scorecard as scorecard

    assert scorecard.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DECISION_GATE_SCORECARD_CONFIG_VERSION",
        "ResearchStrategyDecisionGateScorecardCandidate",
        "ResearchStrategyDecisionGateScorecardConfig",
        "ResearchStrategyDecisionGateScorecardReasonCodeCount",
        "ResearchStrategyDecisionGateScorecardReport",
        "ResearchStrategyDecisionGateScorecardRow",
        "build_research_strategy_decision_gate_scorecard_report",
        "research_strategy_decision_gate_scorecard_digest",
        "research_strategy_decision_gate_scorecard_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "position",
        "buy",
        "sell",
        "recommend",
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

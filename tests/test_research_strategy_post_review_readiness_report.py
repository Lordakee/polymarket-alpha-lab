from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_post_review_readiness_report import (
    DEFAULT_RESEARCH_STRATEGY_POST_REVIEW_READINESS_REPORT_CONFIG_VERSION,
    ResearchStrategyPostReviewReadinessCandidate,
    ResearchStrategyPostReviewReadinessConfig,
    ResearchStrategyPostReviewReadinessReport,
    ResearchStrategyPostReviewReadinessRow,
    build_research_strategy_post_review_readiness_report,
    research_strategy_post_review_readiness_report_digest,
    research_strategy_post_review_readiness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_post_review_readiness_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyPostReviewReadinessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_POST_REVIEW_READINESS_REPORT_CONFIG_VERSION
        ),
        "evidence_maturity_pass_floor": d("0.800000"),
        "evidence_maturity_watch_floor": d("0.600000"),
        "source_corroboration_pass_floor": d("0.800000"),
        "source_corroboration_watch_floor": d("0.600000"),
        "cost_freshness_pass_floor": d("0.800000"),
        "cost_freshness_watch_floor": d("0.600000"),
        "specialist_consensus_pass_floor": d("0.800000"),
        "specialist_consensus_watch_floor": d("0.600000"),
        "unresolved_blocker_pressure_watch_ceiling": d("0.250000"),
        "unresolved_blocker_pressure_block_ceiling": d("0.600000"),
        "manual_review_urgency_pass_floor": d("0.700000"),
        "manual_review_urgency_watch_floor": d("0.400000"),
    }
    values.update(overrides)
    return ResearchStrategyPostReviewReadinessConfig(**values)


def candidate(
    reviewed_candidate_key: str = "private-candidate-alpha",
    *,
    evidence_maturity_score: Decimal = d("0.900000"),
    source_corroboration_score: Decimal = d("0.850000"),
    cost_freshness_score: Decimal = d("0.900000"),
    specialist_consensus_score: Decimal = d("0.875000"),
    unresolved_blocker_pressure: Decimal = d("0.100000"),
    manual_review_urgency_score: Decimal = d("0.800000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyPostReviewReadinessCandidate:
    return ResearchStrategyPostReviewReadinessCandidate(
        reviewed_candidate_key=reviewed_candidate_key,
        evidence_maturity_score=evidence_maturity_score,
        source_corroboration_score=source_corroboration_score,
        cost_freshness_score=cost_freshness_score,
        specialist_consensus_score=specialist_consensus_score,
        unresolved_blocker_pressure=unresolved_blocker_pressure,
        manual_review_urgency_score=manual_review_urgency_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchStrategyPostReviewReadinessCandidate,
    cfg: ResearchStrategyPostReviewReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyPostReviewReadinessReport:
    return build_research_strategy_post_review_readiness_report(
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


def test_post_review_handoff_aggregates_pass_watch_block_rows() -> None:
    pass_item = candidate(
        "private-candidate-pass",
        evidence_maturity_score=d("0.900000"),
        source_corroboration_score=d("0.850000"),
        cost_freshness_score=d("0.900000"),
        specialist_consensus_score=d("0.875000"),
        unresolved_blocker_pressure=d("0.100000"),
        manual_review_urgency_score=d("0.800000"),
    )
    watch_item = candidate(
        "private-candidate-watch",
        evidence_maturity_score=d("0.700000"),
        source_corroboration_score=d("0.650000"),
        cost_freshness_score=d("0.650000"),
        specialist_consensus_score=d("0.700000"),
        unresolved_blocker_pressure=d("0.300000"),
        manual_review_urgency_score=d("0.500000"),
    )
    block_item = candidate(
        "private-candidate-block",
        evidence_maturity_score=d("0.500000"),
        source_corroboration_score=d("0.400000"),
        cost_freshness_score=d("0.550000"),
        specialist_consensus_score=d("0.450000"),
        unresolved_blocker_pressure=d("0.750000"),
        manual_review_urgency_score=d("0.200000"),
    )

    first = report(watch_item, block_item, pass_item)
    second = report(pass_item, watch_item, block_item)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.candidate_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.handoff_status == "block"
    assert first.manual_decision_queue_state == "manual_decision_queue_block"
    assert first.average_readiness_score == d("0.637500")
    assert first.max_manual_review_urgency_score == d("0.800000")
    assert tuple(row.row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.readiness_status for row in first.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert len({row.public_candidate_hash for row in first.rows}) == 3
    assert all(row.public_candidate_hash.startswith("sha256:") for row in first.rows)
    assert all("private-candidate" not in row.public_candidate_hash for row in first.rows)

    blocked = first.rows[0]
    assert blocked.blocker_clearance_score == d("0.250000")
    assert blocked.post_review_readiness_score == d("0.391667")
    assert blocked.reason_codes == (
        "evidence_maturity_block",
        "source_corroboration_block",
        "cost_freshness_block",
        "specialist_consensus_block",
        "unresolved_blocker_pressure_block",
        "manual_review_urgency_block",
    )
    assert_digest(blocked.validation_digest)
    assert_digest(first.validation_digest)

    payload = research_strategy_post_review_readiness_report_payload(first)
    assert payload == research_strategy_post_review_readiness_report_payload(second)
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["candidate_count"] == "3.000000"
    assert payload["average_readiness_score"] == "0.637500"
    assert payload["rows"][0]["row_number"] == "1.000000"
    assert payload["rows"][0]["post_review_readiness_score"] == "0.391667"
    assert payload["rows"][0]["validation_digest"] == blocked.validation_digest
    assert "private-candidate" not in json.dumps(payload, sort_keys=True)
    assert "reviewed_candidate_key" not in json.dumps(payload, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = research_strategy_post_review_readiness_report_digest(first)
    assert "rows" not in digest
    assert digest["candidate_count"] == payload["candidate_count"]
    assert digest["handoff_status"] == "block"
    assert digest["validation_digest"] == first.validation_digest
    assert_no_float_or_int_values(digest)


def test_empty_report_blocks_manual_queue_handoff() -> None:
    gate = report()

    assert gate.candidate_count == ZERO
    assert gate.pass_count == ZERO
    assert gate.watch_count == ZERO
    assert gate.block_count == ZERO
    assert gate.average_readiness_score is None
    assert gate.min_readiness_score is None
    assert gate.max_manual_review_urgency_score is None
    assert gate.handoff_status == "block"
    assert gate.manual_decision_queue_state == "manual_decision_queue_block"
    assert gate.reason_codes == ("post_review_readiness_no_candidates",)
    assert gate.rows == ()
    assert gate.paper_only is True
    assert gate.report_only is True
    assert gate.readonly is True
    assert_digest(gate.validation_digest)


def test_decimal_only_frozen_flags_and_validation() -> None:
    gate = report(candidate("private-candidate-frozen"))

    assert is_dataclass(ResearchStrategyPostReviewReadinessConfig)
    assert is_dataclass(ResearchStrategyPostReviewReadinessCandidate)
    assert is_dataclass(ResearchStrategyPostReviewReadinessRow)
    assert is_dataclass(ResearchStrategyPostReviewReadinessReport)
    with pytest.raises(FrozenInstanceError):
        gate.handoff_status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gate.rows[0].post_review_readiness_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(gate, readonly=False)

    with pytest.raises(ValueError, match="evidence_maturity_score"):
        candidate(evidence_maturity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_corroboration_score"):
        candidate(source_corroboration_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_freshness_score"):
        candidate(cost_freshness_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="reviewed_candidate_key"):
        report(candidate("private-candidate-dupe"), candidate("private-candidate-dupe"))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("private-candidate-time"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="evidence_maturity_pass_floor"):
        config(
            evidence_maturity_pass_floor=d("0.500000"),
            evidence_maturity_watch_floor=d("0.600000"),
        )
    with pytest.raises(ValueError, match="unresolved_blocker_pressure_watch_ceiling"):
        config(
            unresolved_blocker_pressure_watch_ceiling=d("0.700000"),
            unresolved_blocker_pressure_block_ceiling=d("0.600000"),
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
    gate = report(candidate("private-candidate-consistent"))
    row = gate.rows[0]

    with pytest.raises(ValueError, match="post_review_readiness_score must match"):
        replace(row, post_review_readiness_score=row.post_review_readiness_score - d("0.000001"))
    with pytest.raises(ValueError, match="readiness_status must match"):
        replace(row, readiness_status="block")
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(gate, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(gate, rows=(report(candidate("private-candidate-zeta")).rows[0], row))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(gate, validation_digest="0" * 64)

    payload = research_strategy_post_review_readiness_report_payload(gate)
    assert research_strategy_post_review_readiness_report_payload(payload) == payload
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_post_review_readiness_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_post_review_readiness_report_payload(
            {**payload, "wal" "let": {"address": "0x0"}},
        )
    with pytest.raises(ValueError, match="numeric"):
        research_strategy_post_review_readiness_report_payload(
            {**payload, "candidate_count": 1},
        )
    tampered = dict(payload)
    tampered["average_readiness_score"] = "0.637501"
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_post_review_readiness_report_payload(tampered)


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_post_review_readiness_report as gate

    assert gate.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_POST_REVIEW_READINESS_REPORT_CONFIG_VERSION",
        "ResearchStrategyPostReviewReadinessCandidate",
        "ResearchStrategyPostReviewReadinessConfig",
        "ResearchStrategyPostReviewReadinessReport",
        "ResearchStrategyPostReviewReadinessRow",
        "build_research_strategy_post_review_readiness_report",
        "research_strategy_post_review_readiness_report_digest",
        "research_strategy_post_review_readiness_report_payload",
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
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
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

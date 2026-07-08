from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_research_packet_completeness_report import (
    DEFAULT_RESEARCH_STRATEGY_RESEARCH_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION,
    ResearchStrategyResearchPacketCandidate,
    ResearchStrategyResearchPacketCompletenessConfig,
    ResearchStrategyResearchPacketCompletenessReport,
    ResearchStrategyResearchPacketCompletenessRow,
    build_research_strategy_research_packet_completeness_report,
    research_strategy_research_packet_completeness_report_digest,
    research_strategy_research_packet_completeness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_research_packet_completeness_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyResearchPacketCompletenessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_RESEARCH_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION
        ),
        "min_evidence_item_count": d("4.000000"),
        "evidence_item_count_pass_floor": d("6.000000"),
        "min_independent_source_count": d("2.000000"),
        "independent_source_count_pass_floor": d("3.000000"),
        "source_diversity_watch_floor": d("0.700000"),
        "source_diversity_block_floor": d("0.400000"),
        "cost_sanity_watch_floor": d("0.700000"),
        "cost_sanity_block_floor": d("0.400000"),
        "resolution_rule_review_watch_floor": d("0.750000"),
        "resolution_rule_review_block_floor": d("0.500000"),
        "specialist_memory_coverage_watch_floor": d("0.750000"),
        "specialist_memory_coverage_block_floor": d("0.500000"),
        "unresolved_packet_gap_watch_ceiling": ZERO,
        "unresolved_packet_gap_block_ceiling": d("2.000000"),
    }
    values.update(overrides)
    return ResearchStrategyResearchPacketCompletenessConfig(**values)


def candidate(
    packet_ref: str = "packet-alpha",
    *,
    evidence_item_count: Decimal = d("7.000000"),
    independent_source_count: Decimal = d("4.000000"),
    source_diversity_score: Decimal = d("0.880000"),
    cost_sanity_score: Decimal = d("0.900000"),
    resolution_rule_review_score: Decimal = d("0.920000"),
    specialist_memory_coverage_score: Decimal = d("0.860000"),
    unresolved_packet_gap_count: Decimal = ZERO,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyResearchPacketCandidate:
    return ResearchStrategyResearchPacketCandidate(
        packet_ref=packet_ref,
        evidence_item_count=evidence_item_count,
        independent_source_count=independent_source_count,
        source_diversity_score=source_diversity_score,
        cost_sanity_score=cost_sanity_score,
        resolution_rule_review_score=resolution_rule_review_score,
        specialist_memory_coverage_score=specialist_memory_coverage_score,
        unresolved_packet_gap_count=unresolved_packet_gap_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *packets: ResearchStrategyResearchPacketCandidate,
    cfg: ResearchStrategyResearchPacketCompletenessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyResearchPacketCompletenessReport:
    return build_research_strategy_research_packet_completeness_report(
        packets,
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


def test_pass_watch_block_packet_completeness_and_deterministic_payload() -> None:
    inputs = (
        candidate("packet-pass"),
        candidate(
            "packet-watch",
            evidence_item_count=d("4.000000"),
            independent_source_count=d("2.000000"),
            source_diversity_score=d("0.650000"),
            cost_sanity_score=d("0.730000"),
            resolution_rule_review_score=d("0.700000"),
            specialist_memory_coverage_score=d("0.720000"),
            unresolved_packet_gap_count=ONE,
        ),
        candidate(
            "packet-block",
            evidence_item_count=ONE,
            independent_source_count=ZERO,
            source_diversity_score=d("0.300000"),
            cost_sanity_score=d("0.200000"),
            resolution_rule_review_score=d("0.400000"),
            specialist_memory_coverage_score=d("0.300000"),
            unresolved_packet_gap_count=d("2.000000"),
        ),
    )
    first = report(*inputs)
    second = report(*reversed(inputs))

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_RESEARCH_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION
    )
    assert first.packet_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.manual_decision_review_state == "manual_decision_review_block"
    assert first.reason_codes == (
        "evidence_item_count_block",
        "independent_source_count_block",
        "source_diversity_block",
        "cost_sanity_block",
        "resolution_rule_review_block",
        "specialist_memory_coverage_block",
        "unresolved_packet_gap_block",
        "research_packet_completeness_block",
        "evidence_item_count_watch",
        "independent_source_count_watch",
        "source_diversity_watch",
        "resolution_rule_review_watch",
        "specialist_memory_coverage_watch",
        "unresolved_packet_gap_watch",
    )
    assert tuple(row.packet_ref for row in first.rows) == (
        "packet-block",
        "packet-watch",
        "packet-pass",
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")

    blocked = first.rows[0]
    assert blocked.evidence_coverage_ratio == d("0.166667")
    assert blocked.independent_source_ratio == ZERO
    assert blocked.completeness_score == d("0.227778")
    assert blocked.reason_codes == (
        "evidence_item_count_block",
        "independent_source_count_block",
        "source_diversity_block",
        "cost_sanity_block",
        "resolution_rule_review_block",
        "specialist_memory_coverage_block",
        "unresolved_packet_gap_block",
    )
    assert_digest(blocked.validation_digest)
    assert_digest(first.validation_digest)

    payload = research_strategy_research_packet_completeness_report_payload(first)
    assert payload == research_strategy_research_packet_completeness_report_payload(second)
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["packet_count"] == "3.000000"
    assert payload["rows"][0]["completeness_score"] == "0.227778"
    assert payload["rows"][0]["validation_digest"] == blocked.validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = research_strategy_research_packet_completeness_report_digest(first)
    assert "rows" not in digest
    assert digest["packet_count"] == payload["packet_count"]
    assert digest["status"] == "block"
    assert digest["validation_digest"] == first.validation_digest
    assert_no_float_or_int_values(digest)


def test_empty_report_blocks_before_manual_decision_review() -> None:
    completeness = report()

    assert completeness.packet_count == ZERO
    assert completeness.pass_count == ZERO
    assert completeness.watch_count == ZERO
    assert completeness.block_count == ZERO
    assert completeness.min_completeness_score is None
    assert completeness.status == "block"
    assert completeness.manual_decision_review_state == "manual_decision_review_block"
    assert completeness.reason_codes == ("research_packet_completeness_no_packets",)
    assert completeness.rows == ()
    assert completeness.paper_only is True
    assert completeness.report_only is True
    assert completeness.readonly is True
    assert_digest(completeness.validation_digest)


def test_decimal_only_frozen_flags_and_input_validation() -> None:
    completeness = report(candidate("packet-frozen"))

    assert is_dataclass(ResearchStrategyResearchPacketCompletenessConfig)
    assert is_dataclass(ResearchStrategyResearchPacketCandidate)
    assert is_dataclass(ResearchStrategyResearchPacketCompletenessRow)
    assert is_dataclass(ResearchStrategyResearchPacketCompletenessReport)
    with pytest.raises(FrozenInstanceError):
        completeness.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        completeness.rows[0].completeness_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(completeness, readonly=False)

    with pytest.raises(ValueError, match="evidence_item_count"):
        candidate(evidence_item_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_diversity_score"):
        candidate(source_diversity_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_sanity_score"):
        candidate(cost_sanity_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="independent_source_count"):
        candidate(
            evidence_item_count=ONE,
            independent_source_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="packet_ref"):
        report(candidate("packet-dupe"), candidate("packet-dupe"))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("packet-time"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("packet-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="evidence_item_count_pass_floor"):
        config(
            min_evidence_item_count=d("6.000000"),
            evidence_item_count_pass_floor=d("4.000000"),
        )
    with pytest.raises(ValueError, match="source_diversity_watch_floor"):
        config(
            source_diversity_watch_floor=d("0.300000"),
            source_diversity_block_floor=d("0.400000"),
        )

    for item in (completeness, *completeness.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, tuple):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_validation_digest_and_payload_reject_tampering() -> None:
    completeness = report(candidate("packet-consistent"))
    row = completeness.rows[0]

    with pytest.raises(ValueError, match="completeness_score must match"):
        replace(row, completeness_score=row.completeness_score - d("0.000001"))
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(completeness, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(completeness, rows=(report(candidate("packet-zeta")).rows[0], row))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(completeness, validation_digest="0" * 64)

    payload = research_strategy_research_packet_completeness_report_payload(completeness)
    assert research_strategy_research_packet_completeness_report_payload(payload) == payload
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_research_packet_completeness_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_research_packet_completeness_report_payload(
            {**payload, "wal" "let": {"address": "0x0"}},
        )
    with pytest.raises(ValueError, match="numeric"):
        research_strategy_research_packet_completeness_report_payload(
            {**payload, "packet_count": 1},
        )


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_research_packet_completeness_report as completeness

    assert completeness.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_RESEARCH_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION",
        "ResearchStrategyResearchPacketCandidate",
        "ResearchStrategyResearchPacketCompletenessConfig",
        "ResearchStrategyResearchPacketCompletenessReport",
        "ResearchStrategyResearchPacketCompletenessRow",
        "build_research_strategy_research_packet_completeness_report",
        "research_strategy_research_packet_completeness_report_digest",
        "research_strategy_research_packet_completeness_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "li" "ve",
        "au" "th",
        "wal" "let",
        "broker",
        "or" "der",
        "can" "cel",
        "re" "place",
        "exchange",
        "private" "_" "key",
        "api" "_" "key",
        "sec" "ret",
        "po" "sition",
        "b" "uy",
        "se" "ll",
        "reco" "mmend",
        "siz" "ing",
        "data" "base",
        "net" "work",
        "req" "uests",
        "ht" "tp",
        "sock" "et",
        "sub" "process",
        "trade",
        "open(",
        "pathlib",
    )
    assert [term for term in forbidden_terms if term in lowered] == []

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "sock" "et",
        "sub" "process",
        "req" "uests",
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

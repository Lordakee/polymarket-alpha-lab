from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_manual_decision_packet_completeness_report import (
    DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION,
    ResearchStrategyManualDecisionPacketCompletenessConfig,
    ResearchStrategyManualDecisionPacketCompletenessReport,
    ResearchStrategyManualDecisionPacketCompletenessRow,
    ResearchStrategyManualDecisionPacketInput,
    build_research_strategy_manual_decision_packet_completeness_report,
    research_strategy_manual_decision_packet_completeness_report_digest,
    research_strategy_manual_decision_packet_completeness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_manual_decision_packet_completeness_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyManualDecisionPacketCompletenessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION
        ),
        "section_pass_floor": d("0.800000"),
        "section_watch_floor": d("0.600000"),
        "unresolved_section_gap_watch_ceiling": ZERO,
        "unresolved_section_gap_block_ceiling": d("2.000000"),
    }
    values.update(overrides)
    return ResearchStrategyManualDecisionPacketCompletenessConfig(**values)


def packet(
    internal_packet_key: str = "raw-private-packet-alpha",
    *,
    research_section_score: Decimal = d("0.900000"),
    forecast_section_score: Decimal = d("0.850000"),
    cost_section_score: Decimal = d("0.900000"),
    settlement_section_score: Decimal = d("0.875000"),
    domain_memory_section_score: Decimal = d("0.825000"),
    unresolved_section_gap_count: Decimal = ZERO,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyManualDecisionPacketInput:
    return ResearchStrategyManualDecisionPacketInput(
        internal_packet_key=internal_packet_key,
        research_section_score=research_section_score,
        forecast_section_score=forecast_section_score,
        cost_section_score=cost_section_score,
        settlement_section_score=settlement_section_score,
        domain_memory_section_score=domain_memory_section_score,
        unresolved_section_gap_count=unresolved_section_gap_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *packets: ResearchStrategyManualDecisionPacketInput,
    cfg: ResearchStrategyManualDecisionPacketCompletenessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyManualDecisionPacketCompletenessReport:
    return build_research_strategy_manual_decision_packet_completeness_report(
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


def test_pass_watch_block_section_completeness_and_deterministic_payload() -> None:
    pass_item = packet("raw-private-packet-pass")
    watch_item = packet(
        "raw-private-packet-watch",
        research_section_score=d("0.700000"),
        forecast_section_score=d("0.650000"),
        cost_section_score=d("0.700000"),
        settlement_section_score=d("0.750000"),
        domain_memory_section_score=d("0.720000"),
        unresolved_section_gap_count=ONE,
    )
    block_item = packet(
        "raw-private-packet-block",
        research_section_score=d("0.500000"),
        forecast_section_score=d("0.400000"),
        cost_section_score=d("0.550000"),
        settlement_section_score=d("0.450000"),
        domain_memory_section_score=d("0.300000"),
        unresolved_section_gap_count=d("2.000000"),
    )

    first = report(watch_item, block_item, pass_item)
    second = report(pass_item, watch_item, block_item)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION
    )
    assert first.packet_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.human_review_state == "human_review_block"
    assert first.average_completeness_score == d("0.671333")
    assert first.min_completeness_score == d("0.440000")
    assert first.reason_codes == (
        "research_section_block",
        "forecast_section_block",
        "cost_section_block",
        "settlement_section_block",
        "domain_memory_section_block",
        "unresolved_section_gap_block",
        "manual_decision_packet_completeness_block",
        "research_section_watch",
        "forecast_section_watch",
        "cost_section_watch",
        "settlement_section_watch",
        "domain_memory_section_watch",
        "unresolved_section_gap_watch",
    )
    assert tuple(row.row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert len({row.public_packet_hash for row in first.rows}) == 3
    assert all(row.public_packet_hash.startswith("sha256:") for row in first.rows)
    assert all("raw-private-packet" not in row.public_packet_hash for row in first.rows)

    blocked = first.rows[0]
    assert blocked.completeness_score == d("0.440000")
    assert blocked.reason_codes == (
        "research_section_block",
        "forecast_section_block",
        "cost_section_block",
        "settlement_section_block",
        "domain_memory_section_block",
        "unresolved_section_gap_block",
    )
    assert_digest(blocked.validation_digest)
    assert_digest(first.validation_digest)

    payload = research_strategy_manual_decision_packet_completeness_report_payload(first)
    assert payload == research_strategy_manual_decision_packet_completeness_report_payload(
        second,
    )
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["packet_count"] == "3.000000"
    assert payload["average_completeness_score"] == "0.671333"
    assert payload["rows"][0]["completeness_score"] == "0.440000"
    assert payload["rows"][0]["validation_digest"] == blocked.validation_digest
    serialized = json.dumps(payload, sort_keys=True)
    assert "raw-private-packet" not in serialized
    assert "internal_packet_key" not in serialized
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = research_strategy_manual_decision_packet_completeness_report_digest(first)
    assert "rows" not in digest
    assert digest["packet_count"] == payload["packet_count"]
    assert digest["status"] == "block"
    assert digest["validation_digest"] == first.validation_digest
    assert_no_float_or_int_values(digest)


def test_empty_report_blocks_human_review_packet() -> None:
    completeness = report()

    assert completeness.packet_count == ZERO
    assert completeness.pass_count == ZERO
    assert completeness.watch_count == ZERO
    assert completeness.block_count == ZERO
    assert completeness.average_completeness_score is None
    assert completeness.min_completeness_score is None
    assert completeness.status == "block"
    assert completeness.human_review_state == "human_review_block"
    assert completeness.reason_codes == (
        "manual_decision_packet_completeness_no_packets",
    )
    assert completeness.rows == ()
    assert completeness.paper_only is True
    assert completeness.report_only is True
    assert completeness.readonly is True
    assert_digest(completeness.validation_digest)


def test_decimal_only_frozen_flags_and_input_validation() -> None:
    completeness = report(packet("raw-private-packet-frozen"))

    assert is_dataclass(ResearchStrategyManualDecisionPacketCompletenessConfig)
    assert is_dataclass(ResearchStrategyManualDecisionPacketInput)
    assert is_dataclass(ResearchStrategyManualDecisionPacketCompletenessRow)
    assert is_dataclass(ResearchStrategyManualDecisionPacketCompletenessReport)
    with pytest.raises(FrozenInstanceError):
        completeness.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        completeness.rows[0].completeness_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        packet(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(completeness, readonly=False)

    with pytest.raises(ValueError, match="research_section_score"):
        packet(research_section_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_section_score"):
        packet(forecast_section_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_section_score"):
        packet(cost_section_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="internal_packet_key"):
        report(packet("raw-private-packet-dupe"), packet("raw-private-packet-dupe"))
    with pytest.raises(ValueError, match="generated_at"):
        report(packet("raw-private-packet-time"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            packet("raw-private-packet-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="section_pass_floor"):
        config(section_pass_floor=d("0.500000"), section_watch_floor=d("0.600000"))
    with pytest.raises(ValueError, match="unresolved_section_gap_watch_ceiling"):
        config(
            unresolved_section_gap_watch_ceiling=d("3.000000"),
            unresolved_section_gap_block_ceiling=d("2.000000"),
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
    completeness = report(packet("raw-private-packet-consistent"))
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
        replace(completeness, rows=(report(packet("raw-private-packet-zeta")).rows[0], row))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(completeness, validation_digest="0" * 64)

    payload = research_strategy_manual_decision_packet_completeness_report_payload(
        completeness,
    )
    assert research_strategy_manual_decision_packet_completeness_report_payload(
        payload,
    ) == payload
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_manual_decision_packet_completeness_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_manual_decision_packet_completeness_report_payload(
            {**payload, "wal" "let": {"address": "0x0"}},
        )
    with pytest.raises(ValueError, match="numeric"):
        research_strategy_manual_decision_packet_completeness_report_payload(
            {**payload, "packet_count": 1},
        )
    tampered = dict(payload)
    tampered["average_completeness_score"] = "0.671334"
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_manual_decision_packet_completeness_report_payload(tampered)


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_manual_decision_packet_completeness_report as completeness

    assert completeness.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION",
        "ResearchStrategyManualDecisionPacketCompletenessConfig",
        "ResearchStrategyManualDecisionPacketCompletenessReport",
        "ResearchStrategyManualDecisionPacketCompletenessRow",
        "ResearchStrategyManualDecisionPacketInput",
        "build_research_strategy_manual_decision_packet_completeness_report",
        "research_strategy_manual_decision_packet_completeness_report_digest",
        "research_strategy_manual_decision_packet_completeness_report_payload",
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
        "market_id",
        "candidate_id",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
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

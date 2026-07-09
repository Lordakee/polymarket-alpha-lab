from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_strategy_manual_decision_packet_completeness_report as api
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


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyManualDecisionPacketCompletenessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION
        ),
        "min_evidence_item_count": d("4.000000"),
        "evidence_item_count_pass_floor": d("6.000000"),
        "min_independent_source_count": d("2.000000"),
        "independent_source_count_pass_floor": d("3.000000"),
        "summary_watch_floor": d("0.700000"),
        "summary_block_floor": d("0.500000"),
        "unresolved_summary_gap_watch_ceiling": ZERO,
        "unresolved_summary_gap_block_ceiling": d("2.000000"),
    }
    values.update(overrides)
    return ResearchStrategyManualDecisionPacketCompletenessConfig(**values)


def packet(
    internal_packet_key: str = (
        "candidate_id=abc market_slug=private-question "
        "source_url=https://private.example/token"
    ),
    *,
    evidence_item_count: Decimal = d("6.000000"),
    independent_source_count: Decimal = d("3.000000"),
    evidence_summary_score: Decimal = d("0.900000"),
    cost_summary_score: Decimal = d("0.850000"),
    risk_summary_score: Decimal = d("0.900000"),
    resolution_summary_score: Decimal = d("0.875000"),
    team_memory_summary_score: Decimal = d("0.825000"),
    update_trigger_summary_score: Decimal = d("0.880000"),
    unresolved_summary_gap_count: Decimal = ZERO,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyManualDecisionPacketInput:
    return ResearchStrategyManualDecisionPacketInput(
        internal_packet_key=internal_packet_key,
        evidence_item_count=evidence_item_count,
        independent_source_count=independent_source_count,
        evidence_summary_score=evidence_summary_score,
        cost_summary_score=cost_summary_score,
        risk_summary_score=risk_summary_score,
        resolution_summary_score=resolution_summary_score,
        team_memory_summary_score=team_memory_summary_score,
        update_trigger_summary_score=update_trigger_summary_score,
        unresolved_summary_gap_count=unresolved_summary_gap_count,
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


def test_status_vocabulary_is_exact() -> None:
    assert api.RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_STATUSES == (
        "pass",
        "watch",
        "block",
    )


def test_pass_watch_block_manual_decision_packet_completeness_without_raw_leakage() -> None:
    pass_item = packet("candidate_id=pass market_slug=hidden source_url=https://private/pass")
    watch_item = packet(
        "candidate_id=watch market_slug=hidden source_url=https://private/watch",
        evidence_item_count=d("5.000000"),
        independent_source_count=d("2.000000"),
        evidence_summary_score=d("0.700000"),
        cost_summary_score=d("0.700000"),
        risk_summary_score=d("0.700000"),
        resolution_summary_score=d("0.700000"),
        team_memory_summary_score=d("0.700000"),
        update_trigger_summary_score=d("0.700000"),
        unresolved_summary_gap_count=ONE,
    )
    block_item = packet(
        "candidate_id=block market_slug=hidden source_url=https://private/block",
        evidence_item_count=ONE,
        independent_source_count=ONE,
        evidence_summary_score=d("0.400000"),
        cost_summary_score=d("0.300000"),
        risk_summary_score=d("0.200000"),
        resolution_summary_score=d("0.450000"),
        team_memory_summary_score=d("0.400000"),
        update_trigger_summary_score=d("0.300000"),
        unresolved_summary_gap_count=d("2.000000"),
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
    assert first.manual_decision_review_state == "manual_decision_review_block"
    assert first.average_completeness_score == d("0.645000")
    assert first.min_completeness_score == d("0.318750")
    assert first.reason_codes == (
        "evidence_item_count_block",
        "independent_source_count_block",
        "evidence_summary_block",
        "cost_summary_block",
        "risk_summary_block",
        "resolution_summary_block",
        "team_memory_summary_block",
        "update_trigger_summary_block",
        "unresolved_summary_gap_block",
        "manual_decision_packet_completeness_block",
        "evidence_item_count_watch",
        "independent_source_count_watch",
        "unresolved_summary_gap_watch",
    )
    assert tuple(row.row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert len({row.public_packet_hash for row in first.rows}) == 3
    assert all(row.public_packet_hash.startswith("sha256:") for row in first.rows)
    assert all("candidate_id" not in row.public_packet_hash for row in first.rows)

    blocked = first.rows[0]
    assert blocked.completeness_score == d("0.318750")
    assert blocked.reason_codes == (
        "evidence_item_count_block",
        "independent_source_count_block",
        "evidence_summary_block",
        "cost_summary_block",
        "risk_summary_block",
        "resolution_summary_block",
        "team_memory_summary_block",
        "update_trigger_summary_block",
        "unresolved_summary_gap_block",
    )
    assert_digest(blocked.validation_digest)
    assert_digest(first.validation_digest)

    payload = research_strategy_manual_decision_packet_completeness_report_payload(first)
    assert payload == research_strategy_manual_decision_packet_completeness_report_payload(
        second,
    )
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["packet_count"] == "3.000000"
    assert payload["average_completeness_score"] == "0.645000"
    assert payload["rows"][0]["completeness_score"] == "0.318750"
    assert payload["rows"][0]["validation_digest"] == blocked.validation_digest
    serialized = json.dumps(payload, sort_keys=True)
    for raw_fragment in (
        "candidate_id",
        "market_slug",
        "private-question",
        "source_url",
        "https://private",
        "internal_packet_key",
    ):
        assert raw_fragment not in serialized
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


def test_empty_report_blocks_manual_decision_review_without_rows() -> None:
    completeness = report()

    assert completeness.packet_count == ZERO
    assert completeness.pass_count == ZERO
    assert completeness.watch_count == ZERO
    assert completeness.block_count == ZERO
    assert completeness.average_completeness_score is None
    assert completeness.min_completeness_score is None
    assert completeness.status == "block"
    assert completeness.manual_decision_review_state == "manual_decision_review_block"
    assert completeness.reason_codes == (
        "manual_decision_packet_completeness_no_packets",
    )
    assert completeness.rows == ()
    payload = research_strategy_manual_decision_packet_completeness_report_payload(
        completeness,
    )
    assert payload["rows"] == []
    assert payload["average_completeness_score"] is None


def test_update_trigger_summary_gap_prevents_pass_status() -> None:
    completeness = report(
        packet(
            update_trigger_summary_score=d("0.650000"),
            unresolved_summary_gap_count=ONE,
        ),
    )

    assert completeness.status == "watch"
    assert completeness.manual_decision_review_state == "manual_decision_review_watch"
    assert completeness.rows[0].status == "watch"
    assert completeness.rows[0].reason_codes == (
        "update_trigger_summary_watch",
        "unresolved_summary_gap_watch",
    )


def test_validation_digest_rejects_report_and_row_tampering() -> None:
    completeness = report(packet())

    with pytest.raises(ValueError, match="validation_digest"):
        replace(completeness, validation_digest="0" * 64)

    with pytest.raises(ValueError, match="validation_digest"):
        replace(completeness, packet_count=d("2.000000"))

    with pytest.raises(ValueError, match="validation_digest"):
        replace(completeness.rows[0], cost_summary_score=d("0.700000"))

    payload = research_strategy_manual_decision_packet_completeness_report_payload(
        completeness,
    )
    tampered_report_payload = dict(payload)
    tampered_report_payload["average_completeness_score"] = "0.000000"
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_manual_decision_packet_completeness_report_payload(
            tampered_report_payload,
        )

    tampered_row_payload = dict(payload)
    tampered_row_payload["rows"] = [dict(payload["rows"][0])]
    tampered_row_payload["rows"][0]["cost_summary_score"] = "0.700000"
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_manual_decision_packet_completeness_report_payload(
            tampered_row_payload,
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    completeness = report(packet())

    with pytest.raises(FrozenInstanceError):
        completeness.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadPacket(ResearchStrategyManualDecisionPacketInput):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategyManualDecisionPacketCompletenessConfig(paper_only=False)

    with pytest.raises(ValueError, match="evidence_item_count must be a Decimal"):
        packet(evidence_item_count=6)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="evidence_item_count must be an integer"):
        packet(evidence_item_count=d("5.500000"))

    with pytest.raises(ValueError, match="independent_source_count must not exceed"):
        packet(independent_source_count=d("7.000000"))

    with pytest.raises(ValueError, match="report_only"):
        packet(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(completeness.rows[0], readonly=False)


def test_public_api_and_payload_exclude_live_trading_private_data_surfaces() -> None:
    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "recommendation",
        "sizing",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ResearchStrategyManualDecisionPacketCompletenessConfig,
        ResearchStrategyManualDecisionPacketInput,
        ResearchStrategyManualDecisionPacketCompletenessRow,
        ResearchStrategyManualDecisionPacketCompletenessReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "web3",
            "ccxt",
        },
    )

from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab.research_packet_resolution_source_recheck_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_RECHECK_GATE_V2_CONFIG_VERSION
        ),
        "official_stale_after_seconds": d("86400.000000"),
        "market_close_watch_window_seconds": d("86400.000000"),
        "market_close_block_window_seconds": d("3600.000000"),
        "watch_score_threshold": d("0.250000"),
        "blocked_score_threshold": d("0.650000"),
        "contradiction_watch_threshold": d("0.300000"),
        "contradiction_block_threshold": d("0.800000"),
        "rule_ambiguity_watch_threshold": d("0.500000"),
        "evidence_chain_min_completeness": d("0.800000"),
        "official_age_weight": d("0.250000"),
        "contradiction_weight": d("0.300000"),
        "rule_ambiguity_weight": d("0.200000"),
        "market_close_weight": d("0.150000"),
        "evidence_chain_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchPacketResolutionSourceRecheckGateV2Config(**values)


def gate_input(**overrides: object) -> Any:
    module = api()
    values = {
        "packet_id": "packet-alpha",
        "market_id": "market-alpha",
        "official_source_checked_at": GENERATED_AT - timedelta(minutes=5),
        "market_closes_at": GENERATED_AT + timedelta(days=7),
        "contradiction_severity_score": d("0.000000"),
        "rule_ambiguity_score": d("0.000000"),
        "evidence_chain_completeness_ratio": d("1.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchPacketResolutionSourceRecheckGateV2Input(**values)


def decision(row: object, *, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.evaluate_research_packet_resolution_source_recheck_gate_v2(
        row,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_gate_blocks_when_sources_are_stale_contradictory_near_close_and_incomplete() -> None:
    module = api()
    row = gate_input(
        official_source_checked_at=GENERATED_AT - timedelta(days=3),
        market_closes_at=GENERATED_AT + timedelta(minutes=30),
        contradiction_severity_score=d("0.900000"),
        rule_ambiguity_score=d("0.700000"),
        evidence_chain_completeness_ratio=d("0.400000"),
    )

    gate_decision = decision(row)
    repeated_decision = decision(row)

    assert type(gate_decision) is module.ResearchPacketResolutionSourceRecheckGateV2Decision
    assert is_dataclass(gate_decision)
    assert gate_decision.generated_at == GENERATED_AT
    assert gate_decision.gate_status == "blocked"
    assert gate_decision.recheck_required is True
    assert gate_decision.official_source_age_seconds == d("259200.000000")
    assert gate_decision.seconds_until_market_close == d("1800.000000")
    assert gate_decision.official_source_age_score == d("1.000000")
    assert gate_decision.contradiction_severity_score == d("0.900000")
    assert gate_decision.rule_ambiguity_score == d("0.700000")
    assert gate_decision.market_close_proximity_score == d("0.979167")
    assert gate_decision.evidence_chain_missing_score == d("0.600000")
    assert gate_decision.risk_score == d("0.866875")
    assert gate_decision.reason_codes == (
        "resolution_source_recheck_gate_blocked",
        "official_resolution_source_stale",
        "high_resolution_source_contradiction",
        "ambiguous_resolution_rule",
        "market_close_recheck_window",
        "incomplete_evidence_chain",
        "recheck_risk_score_blocked",
    )
    assert gate_decision.decision_digest == repeated_decision.decision_digest
    assert len(gate_decision.decision_digest) == 64
    assert all(character in "0123456789abcdef" for character in gate_decision.decision_digest)
    assert gate_decision.paper_only is True
    assert gate_decision.report_only is True
    assert gate_decision.readonly is True


def test_gate_passes_for_fresh_unambiguous_complete_evidence_and_json_payload() -> None:
    module = api()
    gate_decision = decision(
        gate_input(
            official_source_checked_at=GENERATED_AT,
            market_closes_at=datetime(
                2026,
                7,
                9,
                8,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
    )

    assert gate_decision.gate_status == "pass"
    assert gate_decision.recheck_required is False
    assert gate_decision.official_source_age_seconds == d("0.000000")
    assert gate_decision.seconds_until_market_close == d("604800.000000")
    assert gate_decision.risk_score == d("0.000000")
    assert gate_decision.reason_codes == ("resolution_source_recheck_gate_pass",)

    payload = module.research_packet_resolution_source_recheck_gate_v2_payload(gate_decision)
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["official_source_age_seconds"] == "0.000000"
    assert payload["risk_score"] == "0.000000"
    assert payload["reason_codes"] == ["resolution_source_recheck_gate_pass"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_gate_watches_medium_risk_with_deterministic_reason_codes() -> None:
    gate_decision = decision(
        gate_input(
            contradiction_severity_score=d("0.400000"),
            rule_ambiguity_score=d("0.600000"),
            evidence_chain_completeness_ratio=d("0.700000"),
        ),
    )

    assert gate_decision.gate_status == "watch"
    assert gate_decision.recheck_required is True
    assert gate_decision.evidence_chain_missing_score == d("0.300000")
    assert gate_decision.risk_score == d("0.270868")
    assert gate_decision.reason_codes == (
        "resolution_source_recheck_gate_watch",
        "medium_resolution_source_contradiction",
        "ambiguous_resolution_rule",
        "incomplete_evidence_chain",
        "recheck_risk_score_watch",
    )


def test_gate_validation_is_frozen_strict_decimal_only_and_paper_only() -> None:
    module = api()
    row = gate_input()
    gate_decision = decision(row)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_RECHECK_GATE_V2_CONFIG_VERSION",
        "ResearchPacketResolutionSourceRecheckGateV2Config",
        "ResearchPacketResolutionSourceRecheckGateV2Input",
        "ResearchPacketResolutionSourceRecheckGateV2Decision",
        "evaluate_research_packet_resolution_source_recheck_gate_v2",
        "research_packet_resolution_source_recheck_gate_v2_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    with pytest.raises(FrozenInstanceError):
        row.packet_id = "packet-mutated"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                "research-packet-resolution-source-recheck-gate-v2-v0",
            ),
        )
    with pytest.raises(ValueError, match="official_stale_after_seconds"):
        config(official_stale_after_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_severity_score"):
        gate_input(contradiction_severity_score=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="generated_at"):
        decision(row, generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="official_source_checked_at"):
        gate_input(official_source_checked_at=datetime(2026, 7, 2, 11, 55))
    with pytest.raises(ValueError, match="official_source_checked_at"):
        decision(
            gate_input(official_source_checked_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="risk_score"):
        replace(gate_decision, risk_score=d("9.000000"))


def test_missing_official_source_is_blocked_and_changes_digest() -> None:
    missing_official = decision(
        gate_input(
            official_source_checked_at=None,
            market_id="market-missing-official",
        ),
    )
    fresh_official = decision(
        gate_input(
            official_source_checked_at=GENERATED_AT,
            market_id="market-missing-official",
        ),
    )

    assert missing_official.gate_status == "blocked"
    assert missing_official.official_source_age_seconds is None
    assert missing_official.official_source_age_score == d("1.000000")
    assert missing_official.reason_codes == (
        "resolution_source_recheck_gate_blocked",
        "missing_official_resolution_source",
    )
    assert missing_official.decision_digest != fresh_official.decision_digest


def test_source_file_exposes_no_live_capability_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_packet_resolution_source_recheck_gate_v2.py"
    )
    tree = ast.parse(source_path.read_text())
    banned_fragments = (
        "network",
        "socket",
        "requests",
        "http",
        "auth",
        "wallet",
        "account",
        "broker",
        "trade",
        "trading",
        "order",
        "database",
        "db",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in banned_fragments)
        if isinstance(node, ast.arg):
            lowered = node.arg.lower()
            assert not any(fragment in lowered for fragment in banned_fragments)

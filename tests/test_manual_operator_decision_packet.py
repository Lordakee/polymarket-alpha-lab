from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.manual_operator_decision_packet import (
    CHECKLIST_AREAS,
    DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION,
    ManualOperatorDecisionFact,
    ManualOperatorDecisionPacket,
    ManualOperatorDecisionPacketConfig,
    ManualOperatorDecisionReasonSummary,
    SUPPORT_STATUSES,
    build_manual_operator_decision_packet,
    manual_operator_decision_packet_payload,
)


def _fact(
    checklist_area: str,
    support_status: str,
    reason_summary: str,
    *,
    blocker_summary: str | None = None,
    support_weight: Decimal = Decimal("1"),
) -> ManualOperatorDecisionFact:
    return ManualOperatorDecisionFact(
        checklist_area=checklist_area,
        support_status=support_status,
        reason_summary=reason_summary,
        blocker_summary=blocker_summary,
        support_weight=support_weight,
    )


def test_build_packet_reduces_redacted_facts_to_manual_checklist_payload() -> None:
    generated_at = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    facts = (
        _fact("research", "pass", "research support packet complete"),
        _fact("evidence", "pass", "evidence bundle redacted"),
        _fact("evidence", "watch", "evidence recency requires manual check"),
        _fact(
            "source_authority",
            "pass",
            "official-source family crosscheck complete",
        ),
        _fact("microstructure", "pass", "book quality status redacted"),
        _fact(
            "cost",
            "block",
            "cost model support incomplete",
            blocker_summary="fee and slippage assumptions unresolved",
        ),
        _fact("team_memory", "pass", "team memory conflict scan clear"),
    )

    packet = build_manual_operator_decision_packet(
        facts,
        generated_at=generated_at,
        config=ManualOperatorDecisionPacketConfig(),
    )

    assert SUPPORT_STATUSES == ("pass", "watch", "block")
    assert packet.research_status == "pass"
    assert packet.evidence_status == "watch"
    assert packet.source_authority_status == "pass"
    assert packet.microstructure_status == "pass"
    assert packet.cost_status == "block"
    assert packet.timing_status == "block"
    assert packet.team_memory_status == "pass"
    assert packet.unresolved_blockers == (
        "cost: fee and slippage assumptions unresolved",
        "timing: no redacted support fact provided",
    )
    assert packet.next_manual_review_action == "manual_review_resolve_blockers"
    assert packet.paper_only is True
    assert packet.report_only is True
    assert packet.readonly is True

    payload = manual_operator_decision_packet_payload(packet)

    assert payload == {
        "generated_at": "2026-07-07T12:00:00+00:00",
        "config_version": DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION,
        "research_status": "pass",
        "evidence_status": "watch",
        "source_authority_status": "pass",
        "microstructure_status": "pass",
        "cost_status": "block",
        "timing_status": "block",
        "team_memory_status": "pass",
        "reason_summaries": [
            {
                "checklist_area": "research",
                "support_status": "pass",
                "reason_summary": "research support packet complete",
            },
            {
                "checklist_area": "evidence",
                "support_status": "watch",
                "reason_summary": (
                    "evidence bundle redacted; "
                    "evidence recency requires manual check"
                ),
            },
            {
                "checklist_area": "source_authority",
                "support_status": "pass",
                "reason_summary": "official-source family crosscheck complete",
            },
            {
                "checklist_area": "microstructure",
                "support_status": "pass",
                "reason_summary": "book quality status redacted",
            },
            {
                "checklist_area": "cost",
                "support_status": "block",
                "reason_summary": "cost model support incomplete",
            },
            {
                "checklist_area": "timing",
                "support_status": "block",
                "reason_summary": "no redacted support fact provided",
            },
            {
                "checklist_area": "team_memory",
                "support_status": "pass",
                "reason_summary": "team memory conflict scan clear",
            },
        ],
        "unresolved_blockers": [
            "cost: fee and slippage assumptions unresolved",
            "timing: no redacted support fact provided",
        ],
        "next_manual_review_action": "manual_review_resolve_blockers",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    json_payload = json.dumps(payload, allow_nan=False, sort_keys=True)
    assert "wallet" not in json_payload
    assert "account" not in json_payload
    assert "order" not in json_payload
    assert "buy" not in json_payload
    assert "sell" not in json_payload
    assert "position" not in json_payload
    assert "recommend" not in json_payload
    assert "blocked" not in json_payload
    assert "supported" not in json_payload
    assert "needs_review" not in json_payload
    assert "missing" not in json_payload
    assert "support_weight" not in json_payload


def test_packet_rejects_live_trading_language_and_non_decimal_numeric_inputs() -> None:
    with pytest.raises(ValueError, match="unsafe manual operator packet text"):
        _fact(
            "research",
            "pass",
            "place buy order after review",
        )

    with pytest.raises(ValueError, match="unsafe manual operator packet text"):
        _fact(
            "research",
            "block",
            "credential material absent",
            blocker_summary="wallet access missing",
        )

    with pytest.raises(ValueError, match="support_weight must be exactly Decimal"):
        _fact(
            "research",
            "pass",
            "research support packet complete",
            support_weight=1.0,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "submit after manual review",
        "cancel stale checklist handoff",
        "replace checklist handoff",
        "execute trade handoff",
        "candidate id abc123",
        "market slug election-2026",
        "market question redacted",
        "source url redacted",
        "source ref redacted",
        "source text redacted",
        "raw source archive path",
        "postgres dsn redacted",
        "paper packets table redacted",
    ),
)
def test_packet_rejects_operator_verbs_and_raw_identifier_surfaces(
    unsafe_text: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe manual operator packet text"):
        _fact("research", "pass", unsafe_text)


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "recommended checklist handoff",
        "ordering checklist handoff",
        "buying checklist handoff",
        "sold checklist handoff",
        "api secret redacted",
        "bearer token redacted",
        "seed phrase redacted",
        "privkey redacted",
    ),
)
def test_packet_rejects_inflected_operator_and_secret_surfaces(
    unsafe_text: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe manual operator packet text"):
        _fact("research", "pass", unsafe_text)


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "candidate reference abc123",
        "market url polymarket.com/event/redacted",
        "source archive path /tmp/raw-source.json",
        "source record 0x1234567890abcdef",
        "candidate digest abcdef0123456789abcdef0123456789",
    ),
)
def test_packet_rejects_raw_candidate_market_and_source_details(
    unsafe_text: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe manual operator packet text"):
        _fact("research", "pass", unsafe_text)


def test_packet_allows_safe_words_that_share_forbidden_prefixes() -> None:
    fact = _fact(
        "research",
        "pass",
        "significant traditional research support complete",
    )

    assert fact.reason_summary == "significant traditional research support complete"


def test_public_dataclasses_reject_subclass_surfaces() -> None:
    @dataclass(frozen=True)
    class ConfigSubclass(ManualOperatorDecisionPacketConfig):
        wallet_surface: str = "redacted"

    @dataclass(frozen=True)
    class FactSubclass(ManualOperatorDecisionFact):
        wallet_surface: str = "redacted"

    @dataclass(frozen=True)
    class ReasonSummarySubclass(ManualOperatorDecisionReasonSummary):
        wallet_surface: str = "redacted"

    @dataclass(frozen=True)
    class PacketSubclass(ManualOperatorDecisionPacket):
        wallet_surface: str = "redacted"

    with pytest.raises(ValueError, match="config must be exactly"):
        ConfigSubclass()

    with pytest.raises(ValueError, match="fact must be exactly"):
        FactSubclass(
            checklist_area="research",
            support_status="pass",
            reason_summary="research support packet complete",
        )

    with pytest.raises(ValueError, match="reason summary must be exactly"):
        ReasonSummarySubclass(
            checklist_area="research",
            support_status="pass",
            reason_summary="research support packet complete",
        )

    with pytest.raises(ValueError, match="packet must be exactly"):
        PacketSubclass(
            generated_at=datetime(2026, 7, 7, 13, 0, tzinfo=UTC),
            config_version=DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION,
            research_status="pass",
            evidence_status="pass",
            source_authority_status="pass",
            microstructure_status="pass",
            cost_status="pass",
            timing_status="pass",
            team_memory_status="pass",
            reason_summaries=tuple(
                ManualOperatorDecisionReasonSummary(
                    checklist_area=area,
                    support_status="pass",
                    reason_summary=f"{area} support complete",
                )
                for area in CHECKLIST_AREAS
            ),
            unresolved_blockers=(),
            next_manual_review_action="manual_review_read_packet",
        )


def test_packet_consistency_rejects_block_status_without_blocker_action() -> None:
    with pytest.raises(ValueError, match="unresolved_blockers"):
        ManualOperatorDecisionPacket(
            generated_at=datetime(2026, 7, 7, 13, 30, tzinfo=UTC),
            config_version=DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION,
            research_status="pass",
            evidence_status="pass",
            source_authority_status="pass",
            microstructure_status="pass",
            cost_status="pass",
            timing_status="block",
            team_memory_status="pass",
            reason_summaries=tuple(
                ManualOperatorDecisionReasonSummary(
                    checklist_area=area,
                    support_status="block" if area == "timing" else "pass",
                    reason_summary=(
                        "no redacted support fact provided"
                        if area == "timing"
                        else f"{area} support complete"
                    ),
                )
                for area in CHECKLIST_AREAS
            ),
            unresolved_blockers=(),
            next_manual_review_action="manual_review_read_packet",
        )


def test_packet_consistency_requires_next_action_to_match_review_state() -> None:
    with pytest.raises(ValueError, match="next_manual_review_action must match"):
        ManualOperatorDecisionPacket(
            generated_at=datetime(2026, 7, 7, 14, 0, tzinfo=UTC),
            config_version=DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION,
            research_status="watch",
            evidence_status="pass",
            source_authority_status="pass",
            microstructure_status="pass",
            cost_status="pass",
            timing_status="pass",
            team_memory_status="pass",
            reason_summaries=tuple(
                ManualOperatorDecisionReasonSummary(
                    checklist_area=area,
                    support_status=(
                        "watch" if area == "research" else "pass"
                    ),
                    reason_summary=f"{area} support complete",
                )
                for area in CHECKLIST_AREAS
            ),
            unresolved_blockers=(),
            next_manual_review_action="manual_review_read_packet",
        )


def test_fact_and_packet_dataclasses_are_frozen_and_payload_is_readonly_public() -> None:
    packet = build_manual_operator_decision_packet(
        (
            _fact("research", "pass", "research support packet complete"),
            _fact("evidence", "pass", "evidence bundle redacted"),
            _fact("source_authority", "pass", "source crosscheck complete"),
            _fact("microstructure", "pass", "microstructure summary complete"),
            _fact("cost", "pass", "cost support complete"),
            _fact("timing", "pass", "timing support complete"),
            _fact("team_memory", "pass", "team memory scan clear"),
        ),
        generated_at=datetime(2026, 7, 7, 12, 30, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        packet.research_status = "block"  # type: ignore[misc]

    payload = manual_operator_decision_packet_payload(packet)
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["research_status"] = "block"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["reason_summaries"].append(  # type: ignore[attr-defined]
            {
                "checklist_area": "research",
                "support_status": "block",
                "reason_summary": "late mutation",
            },
        )


def test_packet_requires_paper_report_readonly_flags() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        ManualOperatorDecisionPacketConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        _fact(
            "research",
            "pass",
            "research support packet complete",
        ).__class__(
            checklist_area="research",
            support_status="pass",
            reason_summary="research support packet complete",
            report_only=False,
        )

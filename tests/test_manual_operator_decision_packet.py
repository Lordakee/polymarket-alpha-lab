from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
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
    ManualOperatorGoNoGoPacket,
    SUPPORT_STATUSES,
    build_manual_operator_decision_packet,
    build_manual_operator_go_no_go_packet,
    manual_operator_decision_packet_payload,
    manual_operator_decision_packet_payload_digest,
    manual_operator_go_no_go_packet_payload,
    manual_operator_go_no_go_packet_payload_digest,
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
    for base in (
        ManualOperatorDecisionPacketConfig,
        ManualOperatorDecisionFact,
        ManualOperatorDecisionReasonSummary,
        ManualOperatorDecisionPacket,
        ManualOperatorGoNoGoPacket,
    ):
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"Unsafe{base.__name__}", (base,), {"__post_init__": lambda self: None})


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


def test_go_no_go_packet_wraps_readonly_screening_results_with_digest_chain() -> None:
    manual_packet = build_manual_operator_decision_packet(
        (
            _fact("research", "pass", "research support packet complete"),
            _fact("evidence", "pass", "evidence bundle redacted"),
            _fact("source_authority", "pass", "source crosscheck complete"),
            _fact("microstructure", "pass", "microstructure summary complete"),
            _fact("cost", "pass", "cost support complete"),
            _fact("timing", "pass", "timing support complete"),
            _fact("team_memory", "pass", "team memory scan clear"),
        ),
        generated_at=datetime(2026, 7, 7, 15, 0, tzinfo=UTC),
    )
    packet = build_manual_operator_go_no_go_packet(
        manual_packet=manual_packet,
        ready_queue_status="ready",
        ready_queue_payload_digest="1" * 64,
        audit_trail_status="pass",
        audit_trail_payload_digest="2" * 64,
        public_output_safe_for_operator_display=True,
        public_output_payload_digest="3" * 64,
    )

    assert packet.go_no_go_status == "go"
    assert packet.manual_next_step == "manual_review_read_packet"
    assert packet.reason_codes == ("manual_operator_go_no_go_ready",)
    assert packet.manual_packet_payload_digest == (
        manual_operator_decision_packet_payload_digest(manual_packet)
    )
    assert len(packet.payload_digest) == 64

    payload = manual_operator_go_no_go_packet_payload(packet)
    assert payload["go_no_go_status"] == "go"
    assert payload["ready_queue_review_status"] == "pass"
    assert payload["audit_trail_review_status"] == "pass"
    assert payload["public_output_safety_review_status"] == "pass"
    assert payload["payload_digest"] == packet.payload_digest
    assert manual_operator_go_no_go_packet_payload_digest(payload) == packet.payload_digest
    assert payload["source_payload_digests"] == [
        {
            "source_name": "manual_decision_packet",
            "payload_digest": manual_operator_decision_packet_payload_digest(manual_packet),
        },
        {"source_name": "ready_queue_rollup", "payload_digest": "1" * 64},
        {"source_name": "audit_trail", "payload_digest": "2" * 64},
        {"source_name": "public_output_safety", "payload_digest": "3" * 64},
    ]
    assert not _contains_runtime_number(payload)

    json_payload = json.dumps(payload, allow_nan=False, sort_keys=True)
    forbidden_public_terms = (
        "account",
        "auth",
        "buy",
        "cancel",
        "credential",
        "execute",
        "execution",
        "key",
        "order",
        "place",
        "sell",
        "submit",
        "trade",
        "wallet",
    )
    assert all(term not in json_payload for term in forbidden_public_terms)


def test_go_no_go_packet_is_no_go_until_queue_audit_and_public_output_are_safe() -> None:
    manual_packet = build_manual_operator_decision_packet(
        (
            _fact("research", "pass", "research support packet complete"),
            _fact("evidence", "pass", "evidence bundle redacted"),
            _fact("source_authority", "pass", "source crosscheck complete"),
            _fact("microstructure", "pass", "microstructure summary complete"),
            _fact("cost", "pass", "cost support complete"),
            _fact("timing", "pass", "timing support complete"),
            _fact("team_memory", "pass", "team memory scan clear"),
        ),
        generated_at=datetime(2026, 7, 7, 15, 30, tzinfo=UTC),
    )

    packet = build_manual_operator_go_no_go_packet(
        manual_packet=manual_packet,
        ready_queue_status="blocked",
        ready_queue_payload_digest="4" * 64,
        audit_trail_status="watch",
        audit_trail_payload_digest="5" * 64,
        public_output_safe_for_operator_display=False,
        public_output_payload_digest="6" * 64,
    )

    assert packet.go_no_go_status == "no_go"
    assert packet.ready_queue_review_status == "block"
    assert packet.audit_trail_review_status == "watch"
    assert packet.public_output_safety_review_status == "block"
    assert packet.reason_codes == (
        "manual_operator_go_no_go_ready_queue_not_ready",
        "manual_operator_go_no_go_audit_trail_not_ready",
        "manual_operator_go_no_go_public_output_not_safe",
    )
    assert packet.manual_next_step == "manual_review_resolve_public_output_safety"

    payload = manual_operator_go_no_go_packet_payload(packet)
    assert payload["go_no_go_status"] == "no_go"
    assert "blocked" not in json.dumps(payload, sort_keys=True)


def test_go_no_go_public_payload_rejects_tampering_even_with_recomputed_digest() -> None:
    manual_packet = build_manual_operator_decision_packet(
        (
            _fact("research", "pass", "research support packet complete"),
            _fact("evidence", "pass", "evidence bundle redacted"),
            _fact("source_authority", "pass", "source crosscheck complete"),
            _fact("microstructure", "pass", "microstructure summary complete"),
            _fact("cost", "pass", "cost support complete"),
            _fact("timing", "pass", "timing support complete"),
            _fact("team_memory", "pass", "team memory scan clear"),
        ),
        generated_at=datetime(2026, 7, 7, 16, 0, tzinfo=UTC),
    )
    packet = build_manual_operator_go_no_go_packet(
        manual_packet=manual_packet,
        ready_queue_status="watch",
        ready_queue_payload_digest="7" * 64,
        audit_trail_status="pass",
        audit_trail_payload_digest="8" * 64,
        public_output_safe_for_operator_display=True,
        public_output_payload_digest="9" * 64,
    )
    payload = dict(manual_operator_go_no_go_packet_payload(packet))

    payload["go_no_go_status"] = "go"
    payload["payload_digest"] = _canonical_payload_digest(payload)

    with pytest.raises(ValueError, match="go_no_go_status"):
        manual_operator_go_no_go_packet_payload(payload)


def test_go_no_go_packet_rejects_bad_digest_and_unsafe_source_names() -> None:
    manual_packet = build_manual_operator_decision_packet(
        (
            _fact("research", "pass", "research support packet complete"),
            _fact("evidence", "pass", "evidence bundle redacted"),
            _fact("source_authority", "pass", "source crosscheck complete"),
            _fact("microstructure", "pass", "microstructure summary complete"),
            _fact("cost", "pass", "cost support complete"),
            _fact("timing", "pass", "timing support complete"),
            _fact("team_memory", "pass", "team memory scan clear"),
        ),
        generated_at=datetime(2026, 7, 7, 16, 30, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="payload_digest"):
        build_manual_operator_go_no_go_packet(
            manual_packet=manual_packet,
            ready_queue_status="ready",
            ready_queue_payload_digest="not-a-digest",
            audit_trail_status="pass",
            audit_trail_payload_digest="2" * 64,
            public_output_safe_for_operator_display=True,
            public_output_payload_digest="3" * 64,
        )
    with pytest.raises(ValueError, match="source_name"):
        ManualOperatorGoNoGoPacket(
            generated_at=datetime(2026, 7, 7, 16, 30, tzinfo=UTC),
            go_no_go_status="go",
            manual_next_step="manual_review_read_packet",
            reason_codes=("manual_operator_go_no_go_ready",),
            manual_packet_review_status="pass",
            ready_queue_review_status="pass",
            audit_trail_review_status="pass",
            public_output_safety_review_status="pass",
            source_payload_digests=(
                {"source_name": "wallet", "payload_digest": "1" * 64},
            ),
            manual_packet_payload_digest="1" * 64,
            ready_queue_payload_digest="2" * 64,
            audit_trail_payload_digest="3" * 64,
            public_output_payload_digest="4" * 64,
            payload_digest="0" * 64,
        )


def _contains_runtime_number(value: object) -> bool:
    if type(value) in {int, float}:
        return True
    if isinstance(value, dict):
        return any(_contains_runtime_number(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_runtime_number(item) for item in value)
    return False


def _canonical_payload_digest(payload: dict[str, object]) -> str:
    digest_source = dict(payload)
    digest_source["payload_digest"] = ""
    return hashlib.sha256(
        json.dumps(
            digest_source,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def _ready_manual_packet() -> ManualOperatorDecisionPacket:
    return build_manual_operator_decision_packet(
        tuple(
            _fact(area, "pass", f"{area} support complete")
            for area in CHECKLIST_AREAS
        ),
        generated_at=datetime(2026, 7, 7, 17, 0, tzinfo=UTC),
    )


def _ready_go_no_go_packet() -> ManualOperatorGoNoGoPacket:
    return build_manual_operator_go_no_go_packet(
        manual_packet=_ready_manual_packet(),
        ready_queue_status="ready",
        ready_queue_payload_digest="a" * 64,
        audit_trail_status="pass",
        audit_trail_payload_digest="b" * 64,
        public_output_safe_for_operator_display=True,
        public_output_payload_digest="c" * 64,
    )


def test_decision_object_export_revalidates_utc_exact_types_and_nested_graph() -> None:
    packet = _ready_manual_packet()
    object.__setattr__(packet, "generated_at", datetime(2026, 7, 7, 17, 0))
    with pytest.raises(ValueError, match="generated_at"):
        manual_operator_decision_packet_payload(packet)

    packet = _ready_manual_packet()
    object.__setattr__(packet, "reason_summaries", list(packet.reason_summaries))
    with pytest.raises(ValueError, match="reason_summaries.*tuple"):
        manual_operator_decision_packet_payload(packet)

    packet = _ready_manual_packet()
    object.__setattr__(packet.reason_summaries[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        manual_operator_decision_packet_payload(packet)

    packet = _ready_manual_packet()
    object.__setattr__(packet.reason_summaries[0], "support_status", "block")
    with pytest.raises(ValueError, match="research_status"):
        manual_operator_decision_packet_payload(packet)
    with pytest.raises(ValueError, match="research_status"):
        build_manual_operator_go_no_go_packet(
            manual_packet=packet,
            ready_queue_status="ready",
            ready_queue_payload_digest="a" * 64,
            audit_trail_status="pass",
            audit_trail_payload_digest="b" * 64,
            public_output_safe_for_operator_display=True,
            public_output_payload_digest="c" * 64,
        )


def test_decision_digest_rejects_invalid_object_and_mapping_payloads() -> None:
    packet = _ready_manual_packet()
    expected_digest = manual_operator_decision_packet_payload_digest(packet)
    payload = json.loads(json.dumps(manual_operator_decision_packet_payload(packet)))
    assert manual_operator_decision_packet_payload_digest(payload) == expected_digest

    object.__setattr__(packet.reason_summaries[0], "support_status", "block")
    with pytest.raises(ValueError, match="research_status"):
        manual_operator_decision_packet_payload_digest(packet)
    with pytest.raises(ValueError, match="supported public schema"):
        manual_operator_decision_packet_payload_digest({"anything": "safe"})

    payload["research_status"] = "watch"
    with pytest.raises(ValueError, match="research_status"):
        manual_operator_decision_packet_payload_digest(payload)


def test_go_no_go_object_export_and_digest_reject_noncanonical_or_stale_state() -> None:
    packet = _ready_go_no_go_packet()
    object.__setattr__(packet, "reason_codes", list(packet.reason_codes))
    with pytest.raises(ValueError, match="reason_codes.*tuple"):
        manual_operator_go_no_go_packet_payload(packet)

    packet = _ready_go_no_go_packet()
    object.__setattr__(packet, "manual_next_step", "manual_review_resolve_blockers")
    with pytest.raises(ValueError, match="manual_next_step"):
        manual_operator_go_no_go_packet_payload(packet)
    with pytest.raises(ValueError, match="manual_next_step"):
        manual_operator_go_no_go_packet_payload_digest(packet)

    with pytest.raises(ValueError, match="supported public schema"):
        manual_operator_go_no_go_packet_payload_digest({"anything": "safe"})


def test_go_no_go_mapping_replays_utc_next_step_and_exact_json_containers() -> None:
    payload = json.loads(json.dumps(manual_operator_go_no_go_packet_payload(_ready_go_no_go_packet())))
    payload["generated_at"] = "not-a-timestamp"
    payload["payload_digest"] = _canonical_payload_digest(payload)
    with pytest.raises(ValueError, match="generated_at.*UTC"):
        manual_operator_go_no_go_packet_payload(payload)

    payload = json.loads(json.dumps(manual_operator_go_no_go_packet_payload(_ready_go_no_go_packet())))
    payload["manual_next_step"] = "manual_review_resolve_blockers"
    payload["payload_digest"] = _canonical_payload_digest(payload)
    with pytest.raises(ValueError, match="manual_next_step"):
        manual_operator_go_no_go_packet_payload(payload)

    payload = json.loads(json.dumps(manual_operator_go_no_go_packet_payload(_ready_go_no_go_packet())))
    payload["reason_codes"] = tuple(payload["reason_codes"])
    payload["payload_digest"] = _canonical_payload_digest(payload)
    with pytest.raises(ValueError, match="reason_codes.*JSON array"):
        manual_operator_go_no_go_packet_payload(payload)


def test_go_no_go_mapping_payload_is_deeply_readonly() -> None:
    source = json.loads(json.dumps(manual_operator_go_no_go_packet_payload(_ready_go_no_go_packet())))
    payload = manual_operator_go_no_go_packet_payload(source)

    with pytest.raises(TypeError, match="payload is immutable"):
        payload.__ior__({"extra": "value"})
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["reason_codes"].append("late mutation")
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["source_payload_digests"][0].__ior__({"extra": "value"})
    with pytest.raises(TypeError, match="payload is immutable"):
        payload.__init__({"extra": "value"})
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["source_payload_digests"][0].__init__({"extra": "value"})

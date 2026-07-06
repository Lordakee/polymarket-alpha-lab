from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_research_assignment import (
    TeamResearchAssignmentReport,
    TeamResearchAssignmentRow,
    TeamResearchAssignmentTeamSummary,
)
from polymarket_alpha_lab.team_research_work_packet import (
    TeamResearchWorkPacketConfig,
    build_team_research_work_packet_report,
    team_research_work_packet_payload,
)


GENERATED_AT = datetime(2026, 7, 1, 14, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(walk_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return tuple(values)
    return (value,)


def assert_no_public_numeric_scalars(payload: dict[str, object]) -> None:
    for value in walk_values(payload):
        if type(value) in (int, float, Decimal):
            raise AssertionError(f"public payload exposed numeric scalar {value!r}")


def assignment_row(
    *,
    research_rank: int,
    market_slug: str,
    team_id: str,
    category_id: str,
    assignment_status: str = "assigned",
    memory_readiness_status: str = "pass",
    memory_use_policy: str = "allow",
    queue_research_status: str = "ready",
    assignment_reason_codes: tuple[str, ...] = ("team_research_assignment_assigned",),
    evidence_gap_codes: tuple[str, ...] = (),
    source_reason_codes: tuple[str, ...] = ("candidate_research_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamResearchAssignmentRow:
    return TeamResearchAssignmentRow(
        research_rank=research_rank,
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        selected_side="yes",
        scoring_side="yes",
        team_id=team_id,
        category_id=category_id,
        routing_confidence=d("0.900000"),
        secondary_team_ids=(),
        queue_research_status=queue_research_status,
        queue_research_bucket="ready_bucket",
        queue_readiness_status="pass",
        memory_readiness_status=memory_readiness_status,
        memory_use_policy=memory_use_policy,
        assignment_status=assignment_status,
        assignment_reason_codes=assignment_reason_codes,
        evidence_gap_codes=evidence_gap_codes,
        source_reason_codes=source_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def assignment_report(
    rows: tuple[TeamResearchAssignmentRow, ...],
    *,
    assignment_status: str = "watch",
) -> TeamResearchAssignmentReport:
    team_ids = tuple(sorted({row.team_id for row in rows}))
    summaries = tuple(
        TeamResearchAssignmentTeamSummary(
            team_id=team_id,
            assignment_count=sum(1 for row in rows if row.team_id == team_id),
            assigned_count=sum(
                1
                for row in rows
                if row.team_id == team_id and row.assignment_status == "assigned"
            ),
            watch_count=sum(
                1
                for row in rows
                if row.team_id == team_id and row.assignment_status == "watch"
            ),
            blocked_count=sum(
                1
                for row in rows
                if row.team_id == team_id and row.assignment_status == "blocked"
            ),
            memory_readiness_status=(
                "blocked"
                if any(
                    row.team_id == team_id and row.memory_readiness_status == "blocked"
                    for row in rows
                )
                else "missing"
                if any(
                    row.team_id == team_id and row.memory_readiness_status == "missing"
                    for row in rows
                )
                else "watch"
                if any(
                    row.team_id == team_id and row.memory_readiness_status == "watch"
                    for row in rows
                )
                else "pass"
            ),
            memory_use_policy=(
                "block"
                if any(
                    row.team_id == team_id and row.memory_use_policy == "block"
                    for row in rows
                )
                else "throttle"
                if any(
                    row.team_id == team_id and row.memory_use_policy == "throttle"
                    for row in rows
                )
                else "allow"
            ),
        )
        for team_id in team_ids
    )
    return TeamResearchAssignmentReport(
        generated_at=GENERATED_AT,
        config_version="team-research-assignment-test-v0",
        source_queue_config_version="queue-test-v0",
        source_route_config_version="route-test-v0",
        source_memory_config_version="memory-test-v0",
        assignment_status=assignment_status,
        recommended_next_step={
            "ready": "assign_team_research_work",
            "watch": "review_team_research_assignments",
            "blocked": "block_team_research_assignment",
        }[assignment_status],
        assignment_count=len(rows),
        assigned_count=sum(1 for row in rows if row.assignment_status == "assigned"),
        watch_count=sum(1 for row in rows if row.assignment_status == "watch"),
        blocked_count=sum(1 for row in rows if row.assignment_status == "blocked"),
        team_summaries=summaries,
        rows=rows,
        reason_codes=(f"team_research_assignment_{assignment_status}",),
    )


def test_build_groups_assignment_rows_by_team_and_preserves_queue_order() -> None:
    report = assignment_report(
        (
            assignment_row(
                research_rank=1,
                market_slug="btc-alpha",
                team_id="crypto_btc",
                category_id="finance.crypto.btc",
                evidence_gap_codes=("thin_segment_probability_samples",),
                source_reason_codes=("candidate_research_ready", "fresh_evidence"),
            ),
            assignment_row(
                research_rank=2,
                market_slug="politics-alpha",
                team_id="politics",
                category_id="politics",
            ),
            assignment_row(
                research_rank=3,
                market_slug="btc-beta",
                team_id="crypto_btc",
                category_id="finance.crypto.btc",
                assignment_status="watch",
                memory_readiness_status="watch",
                memory_use_policy="throttle",
                queue_research_status="watch",
                assignment_reason_codes=(
                    "source_queue_research_status_watch",
                    "team_memory_readiness_watch",
                ),
                evidence_gap_codes=("missing_calibration_report",),
                source_reason_codes=("readiness_watch",),
            ),
        ),
    )

    packet = build_team_research_work_packet_report(
        report,
        config=TeamResearchWorkPacketConfig(),
        generated_at=GENERATED_AT,
    )

    assert packet.packet_status == "watch"
    assert packet.research_assignment_count == 3
    assert packet.team_packet_count == 2
    assert tuple(team.team_id for team in packet.team_packets) == (
        "crypto_btc",
        "politics",
    )
    assert tuple(row.research_rank for row in packet.team_packets[0].rows) == (1, 3)
    assert tuple(row.market_slug for row in packet.team_packets[0].rows) == (
        "btc-alpha",
        "btc-beta",
    )
    assert packet.team_packets[0].memory_use_policy == "throttle"
    assert packet.team_packets[0].evidence_gap_codes == (
        "thin_segment_probability_samples",
        "missing_calibration_report",
    )
    assert packet.team_packets[0].assignment_reason_codes == (
        "team_research_assignment_assigned",
        "source_queue_research_status_watch",
        "team_memory_readiness_watch",
    )
    assert packet.team_packets[0].source_reason_codes == (
        "candidate_research_ready",
        "fresh_evidence",
        "readiness_watch",
    )
    assert packet.team_packets[0].rows[1].memory_use_policy == "throttle"
    assert packet.team_packets[0].rows[1].assignment_reason_codes == (
        "source_queue_research_status_watch",
        "team_memory_readiness_watch",
    )
    assert packet.source_assignment_config_version == "team-research-assignment-test-v0"
    assert not hasattr(packet, "operator_next_step")
    assert packet.paper_only is True
    assert packet.report_only is True
    assert packet.readonly is True


def test_build_adds_long_term_domain_research_brief_fields() -> None:
    packet = build_team_research_work_packet_report(
        assignment_report(
            (
                assignment_row(
                    research_rank=1,
                    market_slug="election-calendar-alpha",
                    team_id="politics",
                    category_id="politics.elections.us",
                ),
                assignment_row(
                    research_rank=2,
                    market_slug="rates-path-alpha",
                    team_id="macro_finance",
                    category_id="finance.macro.rates",
                ),
                assignment_row(
                    research_rank=3,
                    market_slug="nba-finals-alpha",
                    team_id="sports_nba",
                    category_id="sports.basketball.nba",
                ),
            ),
            assignment_status="ready",
        ),
        config=TeamResearchWorkPacketConfig(),
        generated_at=GENERATED_AT,
    )

    rows = tuple(row for team in packet.team_packets for row in team.rows)

    assert tuple(row.research_domain for row in rows) == (
        "finance",
        "politics",
        "sports",
    )
    assert {row.research_horizon for row in rows} == {"long_term"}
    assert {row.research_mode for row in rows} == {"phase_1_report_only"}
    assert all(
        {
            "resolution_criteria_review",
            "source_map_update",
            "base_rate_context",
            "uncertainty_log",
            "counterevidence_scan",
        }.issubset(row.research_task_codes)
        for row in rows
    )
    assert "polling_method_review" in packet.team_packets[1].research_task_codes
    assert "filing_calendar_scan" in packet.team_packets[0].research_task_codes
    assert "availability_report_review" in packet.team_packets[2].research_task_codes


def test_payload_redacts_market_details_and_keeps_stable_public_ids() -> None:
    packet = build_team_research_work_packet_report(
        assignment_report(
            (
                assignment_row(
                    research_rank=1,
                    market_slug="btc-alpha",
                    team_id="crypto_btc",
                    category_id="finance.crypto.btc",
                ),
            ),
            assignment_status="ready",
        ),
        config=TeamResearchWorkPacketConfig(),
        generated_at=GENERATED_AT,
    )

    payload = team_research_work_packet_payload(packet)
    rendered_payload = repr(payload)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "operator_next_step" not in payload
    assert "research_rank" not in repr(payload)
    assert "selected_side" not in repr(payload)
    assert "scoring_side" not in repr(payload)
    assert "market_slug" not in rendered_payload
    assert "question" not in rendered_payload
    assert "btc-alpha" not in rendered_payload
    assert "Will btc-alpha resolve yes?" not in rendered_payload
    assert payload["team_packets"][0]["team_id"] == "crypto_btc"
    public_id = payload["team_packets"][0]["rows"][0]["public_id"]
    assert public_id.startswith("work-packet-row-")

    reranked_packet = build_team_research_work_packet_report(
        assignment_report(
            (
                assignment_row(
                    research_rank=9,
                    market_slug="btc-alpha",
                    team_id="crypto_btc",
                    category_id="finance.crypto.btc",
                ),
            ),
            assignment_status="ready",
        ),
        config=TeamResearchWorkPacketConfig(),
        generated_at=GENERATED_AT,
    )
    reranked_payload = team_research_work_packet_payload(reranked_packet)
    assert reranked_payload["team_packets"][0]["rows"][0]["public_id"] == public_id

    false_flag_payload = dict(payload)
    false_flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        team_research_work_packet_payload(false_flag_payload)

    missing_flag_payload = dict(payload)
    missing_flag_payload.pop("readonly")
    with pytest.raises(ValueError, match="readonly"):
        team_research_work_packet_payload(missing_flag_payload)

    unsafe_payload = dict(payload)
    unsafe_payload["order_submission"] = "not allowed"
    with pytest.raises(ValueError, match="unsafe live surface field"):
        team_research_work_packet_payload(unsafe_payload)

    unsafe_string_payload = dict(payload)
    unsafe_string_payload["safe_key"] = "submit order now"
    with pytest.raises(ValueError, match="unsafe live surface value"):
        team_research_work_packet_payload(unsafe_string_payload)

    unsafe_action_payload = dict(payload)
    unsafe_action_payload["position_sizing"] = "blocked"
    with pytest.raises(ValueError, match="unsafe live surface field"):
        team_research_work_packet_payload(unsafe_action_payload)

    unsafe_phrase_payload = dict(payload)
    unsafe_phrase_payload["safe_key"] = "open position after research"
    with pytest.raises(ValueError, match="unsafe live surface value"):
        team_research_work_packet_payload(unsafe_phrase_payload)


def test_payload_uses_decimal_strings_and_tamper_evident_validation_digest() -> None:
    packet = build_team_research_work_packet_report(
        assignment_report(
            (
                assignment_row(
                    research_rank=1,
                    market_slug="btc-alpha",
                    team_id="crypto_btc",
                    category_id="finance.crypto.btc",
                ),
            ),
            assignment_status="ready",
        ),
        config=TeamResearchWorkPacketConfig(),
        generated_at=GENERATED_AT,
    )

    assert len(packet.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in packet.derived_validation_digest
    )

    payload = team_research_work_packet_payload(packet)

    assert payload["derived_validation_digest"] == packet.derived_validation_digest
    assert payload["team_packet_count"] == "1"
    assert payload["research_assignment_count"] == "1"
    assert payload["team_packets"][0]["assignment_count"] == "1"
    assert_no_public_numeric_scalars(payload)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(packet, source_assignment_config_version="tampered-assignment-v0")

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        team_research_work_packet_payload(missing_digest)

    tampered = dict(payload)
    tampered["packet_status"] = "blocked"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        team_research_work_packet_payload(tampered)


def test_public_payload_rejects_missing_nested_readonly_flag() -> None:
    packet = build_team_research_work_packet_report(
        assignment_report(
            (
                assignment_row(
                    research_rank=1,
                    market_slug="btc-alpha",
                    team_id="crypto_btc",
                    category_id="finance.crypto.btc",
                ),
            ),
            assignment_status="ready",
        ),
        config=TeamResearchWorkPacketConfig(),
        generated_at=GENERATED_AT,
    )
    payload = team_research_work_packet_payload(packet)
    packet_payload = dict(payload["team_packets"][0])
    row_payload = dict(packet_payload["rows"][0])
    row_payload.pop("readonly")
    packet_payload["rows"] = [row_payload]
    missing_nested_flag = dict(payload)
    missing_nested_flag["team_packets"] = [packet_payload]

    with pytest.raises(ValueError, match="readonly"):
        team_research_work_packet_payload(missing_nested_flag)


def test_payload_redacts_sensitive_public_id_seed_material_from_json_values() -> None:
    payload = team_research_work_packet_payload(
        {
            "generated_at": GENERATED_AT,
            "config_version": "team-research-work-packet-test-v0",
            "source_assignment_config_version": "team-research-assignment-test-v0",
            "packet_status": "assigned",
            "team_packet_count": 1,
            "research_assignment_count": 1,
            "assigned_count": 1,
            "watch_count": 0,
            "blocked_count": 0,
            "team_packets": [
                {
                    "team_id": "crypto_btc",
                    "packet_status": "assigned",
                    "memory_readiness_status": "pass",
                    "memory_use_policy": "allow",
                    "assignment_count": 1,
                    "assigned_count": 1,
                    "watch_count": 0,
                    "blocked_count": 0,
                    "evidence_gap_codes": [],
                    "assignment_reason_codes": ["team_research_assignment_assigned"],
                    "source_reason_codes": ["candidate_research_ready"],
                    "research_domains": ["finance"],
                    "research_horizons": ["long_term"],
                    "research_modes": ["phase_1_report_only"],
                    "research_task_codes": ["resolution_criteria_review"],
                    "rows": [
                        {
                            "research_rank": 1,
                            "market_slug": "btc-alpha",
                            "question": "Will btc-alpha resolve yes?",
                            "selected_side": "yes",
                            "scoring_side": "yes",
                            "category_id": "finance.crypto.btc",
                            "queue_research_status": "ready",
                            "queue_research_bucket": "ready_bucket",
                            "queue_readiness_status": "pass",
                            "memory_readiness_status": "pass",
                            "memory_use_policy": "allow",
                            "research_domain": "finance",
                            "research_horizon": "long_term",
                            "research_mode": "phase_1_report_only",
                            "research_task_codes": ["resolution_criteria_review"],
                            "assignment_status": "assigned",
                            "assignment_reason_codes": [
                                "team_research_assignment_assigned",
                            ],
                            "evidence_gap_codes": [],
                            "source_reason_codes": ["candidate_research_ready"],
                            "paper_only": True,
                            "report_only": True,
                            "readonly": True,
                        },
                    ],
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            ],
            "reason_codes": ["team_research_work_packet_assigned"],
            "diagnostic_note": "database_url=postgresql://user:secret@localhost/db",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    rendered_payload = repr(payload)

    assert "postgresql://" not in rendered_payload
    assert "secret" not in rendered_payload
    assert payload["diagnostic_note"] == "<redacted-sensitive>"
    assert payload["team_packets"][0]["rows"][0]["public_id"].startswith(
        "work-packet-row-",
    )
    assert "market_slug" not in rendered_payload
    assert "question" not in rendered_payload


def test_payload_allows_public_domain_terms_without_live_actions() -> None:
    packet = build_team_research_work_packet_report(
        assignment_report(
            (
                assignment_row(
                    research_rank=1,
                    market_slug="executive-order-alpha",
                    team_id="politics",
                    category_id="politics.executive",
                ),
                assignment_row(
                    research_rank=2,
                    market_slug="batting-order-alpha",
                    team_id="sports_mlb",
                    category_id="sports.baseball.mlb",
                ),
            ),
            assignment_status="ready",
        ),
        config=TeamResearchWorkPacketConfig(),
        generated_at=GENERATED_AT,
    )

    payload = team_research_work_packet_payload(packet)
    rendered_payload = repr(payload)

    assert "executive-order-alpha" not in rendered_payload
    assert "batting-order-alpha" not in rendered_payload
    assert "politics" in rendered_payload
    assert "sports" in rendered_payload


def test_work_packet_dataclasses_are_frozen_and_reject_false_hard_flags() -> None:
    packet = build_team_research_work_packet_report(
        assignment_report(
            (
                assignment_row(
                    research_rank=1,
                    market_slug="btc-alpha",
                    team_id="crypto_btc",
                    category_id="finance.crypto.btc",
                ),
            ),
            assignment_status="ready",
        ),
        config=TeamResearchWorkPacketConfig(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        packet.packet_status = "blocked"
    with pytest.raises(ValueError, match="paper_only"):
        replace(packet, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(packet.team_packets[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(packet.team_packets[0].rows[0], readonly=False)


def test_memory_block_policy_forces_report_only_blocked_packets() -> None:
    packet = build_team_research_work_packet_report(
        assignment_report(
            (
                assignment_row(
                    research_rank=1,
                    market_slug="btc-alpha",
                    team_id="crypto_btc",
                    category_id="finance.crypto.btc",
                    memory_readiness_status="blocked",
                    memory_use_policy="block",
                    assignment_status="blocked",
                    assignment_reason_codes=("team_memory_readiness_blocked",),
                ),
            ),
            assignment_status="blocked",
        ),
        config=TeamResearchWorkPacketConfig(),
        generated_at=GENERATED_AT,
    )

    assert packet.packet_status == "blocked"
    assert packet.assigned_count == 0
    assert packet.blocked_count == 1
    assert packet.team_packets[0].packet_status == "blocked"
    assert packet.team_packets[0].assigned_count == 0
    assert packet.team_packets[0].blocked_count == 1
    assert packet.team_packets[0].rows[0].assignment_status == "blocked"
    assert "team_memory_readiness_blocked" in packet.team_packets[0].rows[0].assignment_reason_codes

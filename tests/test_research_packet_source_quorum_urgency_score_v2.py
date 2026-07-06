from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
DEADLINE_AT = GENERATED_AT + timedelta(days=3)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_source_quorum_urgency_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object):
    score_module = module()
    values = {
        "config_version": "research-packet-source-quorum-urgency-score-test-v2",
        "required_source_family_count": d("3.000000"),
        "required_current_source_count": d("3.000000"),
        "max_source_age_seconds": d("86400.000000"),
        "urgent_deadline_seconds": d("21600.000000"),
        "watch_deadline_seconds": d("86400.000000"),
        "source_gap_weight": d("0.600000"),
        "deadline_pressure_weight": d("0.400000"),
        "watch_score_threshold": d("0.250000"),
        "block_score_threshold": d("0.750000"),
    }
    values.update(overrides)
    return score_module.ResearchPacketSourceQuorumUrgencyScoreV2Config(**values)


def observed(
    packet_id: str,
    source_id: str,
    source_family: str,
    *,
    deadline_at: datetime = DEADLINE_AT,
    observed_at: datetime | None = GENERATED_AT - timedelta(hours=1),
    source_blocked: bool = False,
    supports_research_packet: bool = True,
    reason_codes: tuple[str, ...] = ("research_packet_source_observed",),
):
    score_module = module()
    return score_module.ResearchPacketSourceQuorumUrgencyScoreV2Observation(
        packet_id=packet_id,
        source_id=source_id,
        source_family=source_family,
        deadline_at=deadline_at,
        observed_at=observed_at,
        source_blocked=source_blocked,
        supports_research_packet=supports_research_packet,
        reason_codes=reason_codes,
    )


def build_report(*items, config=None, generated_at: datetime = GENERATED_AT):
    score_module = module()
    return score_module.build_research_packet_source_quorum_urgency_score_v2(
        items,
        config=config or cfg(),
        generated_at=generated_at,
    )


def test_quorum_urgency_scoring_groups_packets_and_sorts_by_risk() -> None:
    report = build_report(
        observed("packet-pass", "source-a", "official"),
        observed("packet-pass", "source-b", "media"),
        observed("packet-pass", "source-c", "filing"),
        observed("packet-watch", "source-d", "official"),
        observed("packet-watch", "source-e", "media"),
        observed(
            "packet-blocked",
            "source-f",
            "official",
            deadline_at=GENERATED_AT + timedelta(hours=2),
        ),
    )

    assert report.digest_status == "blocked"
    assert report.packet_count == d("3.000000")
    assert report.pass_packet_count == d("1.000000")
    assert report.watch_packet_count == d("1.000000")
    assert report.blocked_packet_count == d("1.000000")
    assert report.max_quorum_urgency_score == d("0.800000")
    assert report.avg_quorum_urgency_score == d("0.333333")
    assert tuple(row.packet_id for row in report.rows) == (
        "packet-blocked",
        "packet-watch",
        "packet-pass",
    )

    blocked, watched, passing = report.rows
    assert blocked.digest_status == "blocked"
    assert blocked.current_source_count == d("1.000000")
    assert blocked.current_source_family_count == d("1.000000")
    assert blocked.source_family_gap_count == d("2.000000")
    assert blocked.current_source_gap_count == d("2.000000")
    assert blocked.deadline_pressure_score == d("1.000000")
    assert blocked.source_gap_score == d("0.666667")
    assert blocked.quorum_urgency_score == d("0.800000")
    assert blocked.reason_codes == (
        "current_source_gap",
        "deadline_block",
        "family_gap",
        "research_packet_source_observed",
    )

    assert watched.digest_status == "watch"
    assert watched.quorum_urgency_score == d("0.200000")
    assert watched.reason_codes == (
        "current_source_gap",
        "family_gap",
        "research_packet_source_observed",
    )

    assert passing.digest_status == "pass"
    assert passing.quorum_urgency_score == d("0.000000")
    assert passing.reason_codes == ("research_packet_source_observed",)


def test_source_family_gaps_count_unique_current_families() -> None:
    report = build_report(
        observed("packet-family-gap", "source-a", "official"),
        observed("packet-family-gap", "source-b", "official"),
        observed("packet-family-gap", "source-c", "official"),
    )

    row = report.rows[0]
    assert row.current_source_count == d("3.000000")
    assert row.current_source_family_count == d("1.000000")
    assert row.current_source_gap_count == d("0.000000")
    assert row.source_family_gap_count == d("2.000000")
    assert row.source_gap_score == d("0.666667")
    assert row.quorum_urgency_score == d("0.400000")
    assert row.digest_status == "watch"
    assert "family_gap" in row.reason_codes


def test_deadline_pressure_increases_score_without_source_gap() -> None:
    report = build_report(
        observed(
            "packet-deadline-watch",
            "source-a",
            "official",
            deadline_at=GENERATED_AT + timedelta(hours=12),
        ),
        observed(
            "packet-deadline-watch",
            "source-b",
            "media",
            deadline_at=GENERATED_AT + timedelta(hours=12),
        ),
        observed(
            "packet-deadline-watch",
            "source-c",
            "filing",
            deadline_at=GENERATED_AT + timedelta(hours=12),
        ),
    )

    row = report.rows[0]
    assert row.seconds_until_deadline == d("43200.000000")
    assert row.deadline_pressure_score == d("0.666667")
    assert row.source_gap_score == d("0.000000")
    assert row.quorum_urgency_score == d("0.266667")
    assert row.digest_status == "watch"
    assert "deadline_watch" in row.reason_codes


def test_payload_serializes_decimal_values_as_strings_and_hard_flags() -> None:
    score_module = module()
    report = build_report(
        observed("packet-pass", "source-a", "official"),
        observed("packet-pass", "source-b", "media"),
        observed("packet-pass", "source-c", "filing"),
    )

    payload = score_module.research_packet_source_quorum_urgency_score_v2_payload(
        report,
    )

    json.dumps(payload, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["packet_count"] == "1.000000"
    assert payload["rows"][0]["current_source_count"] == "3.000000"
    assert payload["rows"][0]["quorum_urgency_score"] == "0.000000"
    assert payload["derived_validation_digest"].startswith("rpsqusv2:")
    assert payload["rows"][0]["derived_validation_digest"].startswith("rpsqusv2:")
    assert_no_float(payload)


def test_dataclasses_are_frozen_and_public_numeric_values_are_decimal_only() -> None:
    score_module = module()

    assert score_module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_QUORUM_URGENCY_SCORE_V2_CONFIG_VERSION",
        "ResearchPacketSourceQuorumUrgencyScoreV2Config",
        "ResearchPacketSourceQuorumUrgencyScoreV2Observation",
        "ResearchPacketSourceQuorumUrgencyScoreV2Row",
        "ResearchPacketSourceQuorumUrgencyScoreV2Report",
        "build_research_packet_source_quorum_urgency_score_v2",
        "research_packet_source_quorum_urgency_score_v2_payload",
    )
    for exported_name in score_module.__all__:
        value = getattr(score_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(
        observed("packet-pass", "source-a", "official"),
        observed("packet-pass", "source-b", "media"),
        observed("packet-pass", "source-c", "filing"),
    )

    for value in (
        cfg(),
        observed("packet-freeze", "source-a", "official"),
        report.rows[0],
        report,
    ):
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    for field in fields(report):
        value = getattr(report, field.name)
        if field.name.endswith(("_count", "_score", "_seconds", "_ratio")):
            assert type(value) is Decimal
    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if field.name.endswith(("_count", "_score", "_seconds", "_ratio")):
                assert type(value) is Decimal


def test_hard_flags_and_digest_tampering_are_rejected() -> None:
    score_module = module()
    report = build_report(
        observed("packet-pass", "source-a", "official"),
        observed("packet-pass", "source-b", "media"),
        observed("packet-pass", "source-c", "filing"),
    )

    assert cfg().derived_validation_digest.startswith("rpsqusv2:")
    assert report.derived_validation_digest.startswith("rpsqusv2:")

    with pytest.raises(ValueError, match="paper_only must be True"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(cfg(), derived_validation_digest="rpsqusv2:tampered")

    object.__setattr__(report.rows[0], "packet_id", "packet-tampered")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        score_module.research_packet_source_quorum_urgency_score_v2_payload(report)


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    score_module = module()
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            observed(f"packet-{term}", "source-a", "official")
        with pytest.raises(ValueError, match="unsafe public"):
            score_module.research_packet_source_quorum_urgency_score_v2_payload(
                {"paper_only": True, "report_only": True, "readonly": True, term: "x"},
            )
        with pytest.raises(ValueError, match="unsafe public"):
            score_module.research_packet_source_quorum_urgency_score_v2_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    "safe_key": term,
                },
            )


def test_module_omits_unsafe_runtime_surfaces() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)

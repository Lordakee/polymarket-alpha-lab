from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_research_packet_completeness_gate_report as api
from polymarket_alpha_lab.research_research_packet_completeness_gate_report import (
    ResearchResearchPacketCompletenessGateConfig,
    ResearchResearchPacketCompletenessGateInput,
    ResearchResearchPacketCompletenessGateReport,
    build_research_research_packet_completeness_gate_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _inputs(
    *,
    aggregate_evidence_count: Decimal = Decimal("6.000000"),
    source_diversity_count: Decimal = Decimal("3.000000"),
    fresh_evidence_count: Decimal = Decimal("5.000000"),
    rule_clarity_score: Decimal = Decimal("0.850000"),
    team_signoff_count: Decimal = Decimal("2.000000"),
    estimated_review_cost: Decimal = Decimal("500.000000"),
) -> ResearchResearchPacketCompletenessGateInput:
    return ResearchResearchPacketCompletenessGateInput(
        aggregate_evidence_count=aggregate_evidence_count,
        source_diversity_count=source_diversity_count,
        fresh_evidence_count=fresh_evidence_count,
        rule_clarity_score=rule_clarity_score,
        team_signoff_count=team_signoff_count,
        estimated_review_cost=estimated_review_cost,
    )


def _report(
    inputs: ResearchResearchPacketCompletenessGateInput | None = None,
    *,
    config: ResearchResearchPacketCompletenessGateConfig | None = None,
) -> ResearchResearchPacketCompletenessGateReport:
    return build_research_research_packet_completeness_gate_report(
        inputs or _inputs(),
        generated_at=NOW,
        config=config,
    )


def test_status_vocabulary_is_exact() -> None:
    assert api.RESEARCH_RESEARCH_PACKET_COMPLETENESS_GATE_STATUSES == (
        "pass",
        "watch",
        "block",
    )


def test_completeness_gate_passes_complete_packet_for_manual_review() -> None:
    report = _report()

    assert report.gate_status == "pass"
    assert report.check_count == Decimal("6.000000")
    assert report.passed_check_count == Decimal("6.000000")
    assert report.watch_check_count == Decimal("0.000000")
    assert report.blocked_check_count == Decimal("0.000000")
    assert report.fresh_evidence_ratio == Decimal("0.833333")
    assert report.stale_evidence_count == Decimal("1.000000")
    assert report.reason_codes == (
        "evidence_count_pass",
        "source_diversity_pass",
        "freshness_pass",
        "rule_clarity_pass",
        "team_signoff_pass",
        "review_cost_pass",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_gate_watches_near_misses_without_blocking_review() -> None:
    report = _report(
        _inputs(
            aggregate_evidence_count=Decimal("5.000000"),
            source_diversity_count=Decimal("2.000000"),
            fresh_evidence_count=Decimal("3.000000"),
            rule_clarity_score=Decimal("0.700000"),
            team_signoff_count=Decimal("1.000000"),
            estimated_review_cost=Decimal("900.000000"),
        ),
    )

    assert report.gate_status == "watch"
    assert report.passed_check_count == Decimal("0.000000")
    assert report.watch_check_count == Decimal("6.000000")
    assert report.blocked_check_count == Decimal("0.000000")
    assert report.fresh_evidence_ratio == Decimal("0.600000")
    assert "source_diversity_watch" in report.reason_codes
    assert "freshness_watch" in report.reason_codes
    assert "rule_clarity_watch" in report.reason_codes
    assert "team_signoff_watch" in report.reason_codes
    assert "review_cost_watch" in report.reason_codes


def test_gate_blocks_packets_not_complete_enough_for_review() -> None:
    report = _report(
        _inputs(
            aggregate_evidence_count=Decimal("0.000000"),
            source_diversity_count=Decimal("0.000000"),
            fresh_evidence_count=Decimal("0.000000"),
            rule_clarity_score=Decimal("0.300000"),
            team_signoff_count=Decimal("0.000000"),
            estimated_review_cost=Decimal("1600.000000"),
        ),
    )

    assert report.gate_status == "block"
    assert report.passed_check_count == Decimal("0.000000")
    assert report.watch_check_count == Decimal("0.000000")
    assert report.blocked_check_count == Decimal("6.000000")
    assert report.reason_codes == (
        "evidence_count_block",
        "source_diversity_block",
        "freshness_block",
        "rule_clarity_block",
        "team_signoff_block",
        "review_cost_block",
    )


def test_payload_is_deterministic_json_ready_and_decimal_only() -> None:
    first = _report()
    second = _report()

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    json.dumps(first.payload, sort_keys=True)
    assert first.payload["aggregate_evidence_count"] == "6.000000"
    assert first.payload["source_diversity_count"] == "3.000000"
    assert first.payload["fresh_evidence_ratio"] == "0.833333"
    assert first.payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest
    assert isinstance(first.derived_validation_digest, str)
    assert len(first.derived_validation_digest) == 64
    _assert_no_non_decimal_public_numbers(first)
    _assert_no_decimal_objects(first.payload)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, estimated_review_cost=Decimal("501.000000"))


def test_dataclasses_are_frozen_and_hard_flags_are_enforced() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.gate_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ResearchResearchPacketCompletenessGateInput):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchResearchPacketCompletenessGateConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        ResearchResearchPacketCompletenessGateInput(
            aggregate_evidence_count=Decimal("6.000000"),
            source_diversity_count=Decimal("3.000000"),
            fresh_evidence_count=Decimal("5.000000"),
            rule_clarity_score=Decimal("0.850000"),
            team_signoff_count=Decimal("2.000000"),
            estimated_review_cost=Decimal("500.000000"),
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_numeric_inputs_must_be_decimal_and_counts_must_be_whole() -> None:
    with pytest.raises(ValueError, match="aggregate_evidence_count must be a Decimal"):
        ResearchResearchPacketCompletenessGateInput(
            aggregate_evidence_count=6,  # type: ignore[arg-type]
            source_diversity_count=Decimal("3.000000"),
            fresh_evidence_count=Decimal("5.000000"),
            rule_clarity_score=Decimal("0.850000"),
            team_signoff_count=Decimal("2.000000"),
            estimated_review_cost=Decimal("500.000000"),
        )

    with pytest.raises(ValueError, match="estimated_review_cost must be a Decimal"):
        ResearchResearchPacketCompletenessGateInput(
            aggregate_evidence_count=Decimal("6.000000"),
            source_diversity_count=Decimal("3.000000"),
            fresh_evidence_count=Decimal("5.000000"),
            rule_clarity_score=Decimal("0.850000"),
            team_signoff_count=Decimal("2.000000"),
            estimated_review_cost=500.0,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="source_diversity_count must be a whole number"):
        _inputs(source_diversity_count=Decimal("2.500000"))


def test_aggregate_relationships_are_validated() -> None:
    with pytest.raises(ValueError, match="fresh_evidence_count cannot exceed"):
        _inputs(fresh_evidence_count=Decimal("7.000000"))

    with pytest.raises(ValueError, match="source_diversity_count cannot exceed"):
        _inputs(source_diversity_count=Decimal("7.000000"))


def test_no_raw_identifiers_or_action_surfaces_are_exposed() -> None:
    forbidden_fragments = (
        "candidate_id",
        "candidate_slug",
        "market_id",
        "market_slug",
        "source_id",
        "source_url",
        "source_reference",
        "recommendation",
        "sizing",
        "order",
        "wallet",
        "auth",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ResearchResearchPacketCompletenessGateConfig,
        ResearchResearchPacketCompletenessGateInput,
        ResearchResearchPacketCompletenessGateReport,
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


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))

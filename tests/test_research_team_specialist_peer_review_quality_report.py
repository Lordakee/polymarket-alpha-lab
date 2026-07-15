from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal, localcontext
import importlib
import inspect
import json
from types import MappingProxyType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
REVIEW_A = "sha256:" + ("a" * 64)
REVIEW_B = "sha256:" + ("b" * 64)
REVIEW_C = "sha256:" + ("c" * 64)
OUTPUT_A = "sha256:" + ("1" * 64)
OUTPUT_B = "sha256:" + ("2" * 64)
OUTPUT_C = "sha256:" + ("3" * 64)
EVIDENCE_A = "sha256:" + ("4" * 64)
EVIDENCE_B = "sha256:" + ("5" * 64)
EVIDENCE_C = "sha256:" + ("6" * 64)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_peer_review_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "disagreement_watch_gap_ratio": d("0.250000"),
        "disagreement_block_gap_ratio": d("0.500000"),
        "evidence_watch_gap_ratio": d("0.250000"),
        "evidence_block_gap_ratio": d("0.500000"),
        "correction_watch_gap_ratio": d("0.250000"),
        "correction_block_gap_ratio": d("0.500000"),
        "stale_memory_watch_seconds": d("86400.000000"),
        "stale_memory_block_seconds": d("259200.000000"),
        "reviewer_latency_watch_seconds": d("3600.000000"),
        "reviewer_latency_block_seconds": d("7200.000000"),
        "disagreement_weight": d("0.250000"),
        "evidence_weight": d("0.200000"),
        "correction_weight": d("0.200000"),
        "stale_memory_weight": d("0.150000"),
        "reviewer_latency_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistPeerReviewQualityReportConfig(**values)


def peer_review_snapshot(
    team_ref: str,
    reviewer_ref: str,
    review_digest: str,
    output_digest: str,
    evidence_digest: str,
    *,
    disagreement_total: str,
    disagreement_resolved: str,
    evidence_required: str,
    evidence_covered: str,
    correction_required: str,
    correction_completed: str,
    memory_age_seconds: int,
    reviewer_latency_seconds: int,
):
    module = api()
    return module.ResearchTeamSpecialistPeerReviewQualitySnapshot(
        team_ref=team_ref,
        reviewer_ref=reviewer_ref,
        review_artifact_digest=review_digest,
        reviewed_output_digest=output_digest,
        evidence_bundle_digest=evidence_digest,
        review_due_at=GENERATED_AT - timedelta(seconds=reviewer_latency_seconds),
        reviewed_at=GENERATED_AT,
        memory_refreshed_at=GENERATED_AT - timedelta(seconds=memory_age_seconds),
        disagreement_total_count=d(disagreement_total),
        disagreement_resolved_count=d(disagreement_resolved),
        required_evidence_count=d(evidence_required),
        covered_evidence_count=d(evidence_covered),
        correction_required_count=d(correction_required),
        correction_completed_count=d(correction_completed),
    )


def build_report(
    *snapshots: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_specialist_peer_review_quality_report(
        snapshots,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_decimal_only_numerics(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_numerics(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_decimal_only_numerics(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_decimal_only_numerics(item)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_values(item)


def resign_payload(payload: dict[str, Any]) -> None:
    module = api()
    rows = payload.get("rows", [])
    if type(rows) is list:
        for row in rows:
            if type(row) is dict:
                row["derived_validation_digest"] = module._payload_digest(row)
    payload["derived_validation_digest"] = module._payload_digest(payload)


def one_row_payload() -> dict[str, Any]:
    module = api()
    report = build_report(
        peer_review_snapshot(
            "team-alpha",
            "reviewer-macro",
            REVIEW_A,
            OUTPUT_A,
            EVIDENCE_A,
            disagreement_total="2",
            disagreement_resolved="2",
            evidence_required="4",
            evidence_covered="4",
            correction_required="1",
            correction_completed="1",
            memory_age_seconds=600,
            reviewer_latency_seconds=600,
        ),
    )
    return deepcopy(
        module.research_team_specialist_peer_review_quality_report_payload(report),
    )


def test_scores_peer_review_quality_and_rolls_up_statuses() -> None:
    module = api()

    report = build_report(
        peer_review_snapshot(
            "team-beta",
            "reviewer-weather",
            REVIEW_C,
            OUTPUT_C,
            EVIDENCE_C,
            disagreement_total="4",
            disagreement_resolved="1",
            evidence_required="4",
            evidence_covered="1",
            correction_required="4",
            correction_completed="1",
            memory_age_seconds=300_000,
            reviewer_latency_seconds=8_000,
        ),
        peer_review_snapshot(
            "team-alpha",
            "reviewer-macro",
            REVIEW_A,
            OUTPUT_A,
            EVIDENCE_A,
            disagreement_total="2",
            disagreement_resolved="2",
            evidence_required="4",
            evidence_covered="4",
            correction_required="1",
            correction_completed="1",
            memory_age_seconds=600,
            reviewer_latency_seconds=600,
        ),
        peer_review_snapshot(
            "team-alpha",
            "reviewer-rates",
            REVIEW_B,
            OUTPUT_B,
            EVIDENCE_B,
            disagreement_total="4",
            disagreement_resolved="3",
            evidence_required="4",
            evidence_covered="3",
            correction_required="4",
            correction_completed="3",
            memory_age_seconds=90_000,
            reviewer_latency_seconds=4_000,
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.review_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.unresolved_disagreement_count == d("2")
    assert report.evidence_gap_count == d("2")
    assert report.correction_gap_count == d("2")
    assert report.stale_memory_count == d("2")
    assert report.delayed_reviewer_count == d("2")
    assert report.max_peer_review_risk_score == d("0.837500")
    assert report.average_peer_review_risk_score == d("0.393403")
    assert report.reason_codes == (
        "peer_review_correction_follow_through_block",
        "peer_review_correction_follow_through_watch",
        "peer_review_disagreement_handling_block",
        "peer_review_disagreement_handling_watch",
        "peer_review_evidence_coverage_block",
        "peer_review_evidence_coverage_watch",
        "peer_review_reviewer_latency_block",
        "peer_review_reviewer_latency_watch",
        "peer_review_stale_memory_block",
        "peer_review_stale_memory_watch",
    )

    passed, watched, blocked = report.rows
    assert (passed.team_ref, passed.reviewer_ref) == ("team-alpha", "reviewer-macro")
    assert passed.disagreement_gap_ratio == d("0.000000")
    assert passed.evidence_coverage_gap_ratio == d("0.000000")
    assert passed.correction_follow_through_gap_ratio == d("0.000000")
    assert passed.stale_memory_component == d("0.002315")
    assert passed.reviewer_latency_component == d("0.083333")
    assert passed.peer_review_risk_score == d("0.017014")
    assert passed.status == "pass"
    assert passed.reason_codes == ("peer_review_quality_pass",)

    assert (watched.team_ref, watched.reviewer_ref) == ("team-alpha", "reviewer-rates")
    assert watched.peer_review_risk_score == d("0.325695")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "peer_review_correction_follow_through_watch",
        "peer_review_disagreement_handling_watch",
        "peer_review_evidence_coverage_watch",
        "peer_review_reviewer_latency_watch",
        "peer_review_stale_memory_watch",
    )

    assert (blocked.team_ref, blocked.reviewer_ref) == ("team-beta", "reviewer-weather")
    assert blocked.peer_review_risk_score == d("0.837500")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "peer_review_correction_follow_through_block",
        "peer_review_disagreement_handling_block",
        "peer_review_evidence_coverage_block",
        "peer_review_reviewer_latency_block",
        "peer_review_stale_memory_block",
    )
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_only_numerics(report)


def test_empty_report_blocks_without_sensitive_public_surface() -> None:
    module = api()

    report = build_report()

    assert report.status == "block"
    assert report.review_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.rows == ()
    assert report.max_peer_review_risk_score == d("0.000000")
    assert report.average_peer_review_risk_score == d("0.000000")
    assert report.reason_codes == ("peer_review_quality_empty",)
    assert report.reason_code_counts == (
        module.ResearchTeamSpecialistPeerReviewQualityReasonCodeCount(
            reason_code="peer_review_quality_empty",
            count=d("1"),
        ),
    )
    assert_decimal_only_numerics(report)


def test_payload_serialization_is_deterministic_tamper_evident_and_redacted() -> None:
    module = api()
    first = peer_review_snapshot(
        "team-alpha",
        "reviewer-rates",
        REVIEW_B,
        OUTPUT_B,
        EVIDENCE_B,
        disagreement_total="4",
        disagreement_resolved="3",
        evidence_required="4",
        evidence_covered="3",
        correction_required="4",
        correction_completed="3",
        memory_age_seconds=90_000,
        reviewer_latency_seconds=4_000,
    )
    second = peer_review_snapshot(
        "team-alpha",
        "reviewer-macro",
        REVIEW_A,
        OUTPUT_A,
        EVIDENCE_A,
        disagreement_total="2",
        disagreement_resolved="2",
        evidence_required="4",
        evidence_covered="4",
        correction_required="1",
        correction_completed="1",
        memory_age_seconds=600,
        reviewer_latency_seconds=600,
    )

    report_a = build_report(first, second)
    report_b = build_report(second, first)
    payload = module.research_team_specialist_peer_review_quality_report_payload(report_a)
    encoded = json.dumps(payload, sort_keys=True)

    assert report_a.rows == report_b.rows
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["review_count"] == "2"
    assert payload["rows"][0]["peer_review_risk_score"] == "0.017014"
    assert payload["rows"][0]["review_artifact_digest"] == REVIEW_A
    assert payload["rows"][0]["derived_validation_digest"] == (
        report_a.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    json.loads(encoded)

    leaked_fragments = (
        "candidate-raw-123",
        "market-slug",
        "will-this-happen",
        "https://example.test/source",
        "postgres://",
        "secret-token",
        "wallet",
        "order",
        "trade",
    )
    assert not any(fragment in encoded for fragment in leaked_fragments)

    tampered = dict(payload)
    tampered["block_count"] = "7"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_peer_review_quality_report_payload(tampered)

    object.__setattr__(report_a.rows[0], "peer_review_risk_score", d("0.000001"))
    with pytest.raises(
        ValueError,
        match="derived_validation_digest|tamper|peer_review_risk_score",
    ):
        module.research_team_specialist_peer_review_quality_report_payload(report_a)

    with pytest.raises(ValueError, match="Decimal"):
        module.research_team_specialist_peer_review_quality_report_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="float"):
        module.research_team_specialist_peer_review_quality_report_payload(
            {"score": 0.5, "paper_only": True, "report_only": True, "readonly": True},
        )


def test_validation_rejects_bad_types_dates_counts_flags_and_unsafe_public_payloads() -> None:
    module = api()
    snapshot = peer_review_snapshot(
        "team-alpha",
        "reviewer-rates",
        REVIEW_A,
        OUTPUT_A,
        EVIDENCE_A,
        disagreement_total="4",
        disagreement_resolved="3",
        evidence_required="4",
        evidence_covered="3",
        correction_required="4",
        correction_completed="3",
        memory_age_seconds=90_000,
        reviewer_latency_seconds=4_000,
    )
    report = build_report(snapshot)

    for value in (config(), snapshot, report.rows[0], report.reason_code_counts[0], report):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(snapshot, paper_only=False)
    with pytest.raises(ValueError, match="disagreement_total_count"):
        replace(snapshot, disagreement_total_count=_DecimalSubclass("4"))
    with pytest.raises(ValueError, match="review_artifact_digest"):
        replace(snapshot, review_artifact_digest="candidate-raw-123")
    with pytest.raises(ValueError, match="disagreement_resolved_count"):
        replace(snapshot, disagreement_resolved_count=d("5"))
    with pytest.raises(ValueError, match="covered_evidence_count"):
        replace(snapshot, covered_evidence_count=d("5"))
    with pytest.raises(ValueError, match="correction_completed_count"):
        replace(snapshot, correction_completed_count=d("5"))
    with pytest.raises(ValueError, match="reviewed_at"):
        module.ResearchTeamSpecialistPeerReviewQualitySnapshot(
            team_ref="team-alpha",
            reviewer_ref="reviewer-rates",
            review_artifact_digest=REVIEW_A,
            reviewed_output_digest=OUTPUT_A,
            evidence_bundle_digest=EVIDENCE_A,
            review_due_at=GENERATED_AT,
            reviewed_at=GENERATED_AT - timedelta(seconds=1),
            memory_refreshed_at=GENERATED_AT,
            disagreement_total_count=d("1"),
            disagreement_resolved_count=d("1"),
            required_evidence_count=d("1"),
            covered_evidence_count=d("1"),
            correction_required_count=d("1"),
            correction_completed_count=d("1"),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(snapshot, cfg=config(), generated_at=datetime(2026, 7, 8, 12, 0))

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(
            snapshot,
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=MissingOffsetTz()),
        )
    with pytest.raises(ValueError, match="reviewed_at must not be in the future"):
        build_report(
            module.ResearchTeamSpecialistPeerReviewQualitySnapshot(
                team_ref="team-alpha",
                reviewer_ref="reviewer-rates",
                review_artifact_digest=REVIEW_A,
                reviewed_output_digest=OUTPUT_A,
                evidence_bundle_digest=EVIDENCE_A,
                review_due_at=GENERATED_AT,
                reviewed_at=GENERATED_AT + timedelta(seconds=1),
                memory_refreshed_at=GENERATED_AT,
                disagreement_total_count=d("1"),
                disagreement_resolved_count=d("1"),
                required_evidence_count=d("1"),
                covered_evidence_count=d("1"),
                correction_required_count=d("1"),
                correction_completed_count=d("1"),
            ),
        )

    for field_name in (
        "unresolved_disagreement_count",
        "evidence_gap_count",
        "correction_gap_count",
        "stale_memory_count",
        "delayed_reviewer_count",
    ):
        with pytest.raises(ValueError, match=field_name):
            replace(report, **{field_name: d("0"), "derived_validation_digest": ""})

    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_peer_review_quality_report_payload(
            {
                "candidate_id": "candidate-raw-123",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_peer_review_quality_report_payload(
            {"note": "https://example.test/source", "paper_only": True, "report_only": True, "readonly": True},
        )


def test_public_dataclass_and_payload_schemas_are_exact_and_canonical() -> None:
    module = api()

    for dataclass_type in (
        module.ResearchTeamSpecialistPeerReviewQualityReportConfig,
        module.ResearchTeamSpecialistPeerReviewQualitySnapshot,
        module.ResearchTeamSpecialistPeerReviewQualityRow,
        module.ResearchTeamSpecialistPeerReviewQualityReasonCodeCount,
        module.ResearchTeamSpecialistPeerReviewQualityReport,
    ):
        assert dataclass_type.__final__ is True

    assert tuple(
        field.name
        for field in fields(module.ResearchTeamSpecialistPeerReviewQualityReportConfig)
    ) == (
        "config_version",
        "disagreement_watch_gap_ratio",
        "disagreement_block_gap_ratio",
        "evidence_watch_gap_ratio",
        "evidence_block_gap_ratio",
        "correction_watch_gap_ratio",
        "correction_block_gap_ratio",
        "stale_memory_watch_seconds",
        "stale_memory_block_seconds",
        "reviewer_latency_watch_seconds",
        "reviewer_latency_block_seconds",
        "disagreement_weight",
        "evidence_weight",
        "correction_weight",
        "stale_memory_weight",
        "reviewer_latency_weight",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(
        field.name
        for field in fields(module.ResearchTeamSpecialistPeerReviewQualitySnapshot)
    ) == (
        "team_ref",
        "reviewer_ref",
        "review_artifact_digest",
        "reviewed_output_digest",
        "evidence_bundle_digest",
        "review_due_at",
        "reviewed_at",
        "memory_refreshed_at",
        "disagreement_total_count",
        "disagreement_resolved_count",
        "required_evidence_count",
        "covered_evidence_count",
        "correction_required_count",
        "correction_completed_count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(
        field.name
        for field in fields(module.ResearchTeamSpecialistPeerReviewQualityRow)
    ) == (
        "team_ref",
        "reviewer_ref",
        "review_artifact_digest",
        "reviewed_output_digest",
        "evidence_bundle_digest",
        "review_due_at",
        "reviewed_at",
        "memory_refreshed_at",
        "reviewer_latency_seconds",
        "memory_age_seconds",
        "disagreement_total_count",
        "disagreement_resolved_count",
        "disagreement_gap_ratio",
        "required_evidence_count",
        "covered_evidence_count",
        "evidence_coverage_gap_ratio",
        "correction_required_count",
        "correction_completed_count",
        "correction_follow_through_gap_ratio",
        "stale_memory_component",
        "reviewer_latency_component",
        "peer_review_risk_score",
        "status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(
        field.name
        for field in fields(
            module.ResearchTeamSpecialistPeerReviewQualityReasonCodeCount,
        )
    ) == (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(
        field.name
        for field in fields(module.ResearchTeamSpecialistPeerReviewQualityReport)
    ) == (
        "generated_at",
        "config_version",
        "review_count",
        "pass_count",
        "watch_count",
        "block_count",
        "unresolved_disagreement_count",
        "evidence_gap_count",
        "correction_gap_count",
        "stale_memory_count",
        "delayed_reviewer_count",
        "max_peer_review_risk_score",
        "average_peer_review_risk_score",
        "status",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )

    payload = one_row_payload()
    assert tuple(payload) == tuple(
        field.name
        for field in fields(module.ResearchTeamSpecialistPeerReviewQualityReport)
    )
    assert tuple(payload["rows"][0]) == tuple(
        field.name
        for field in fields(module.ResearchTeamSpecialistPeerReviewQualityRow)
    )
    assert tuple(payload["reason_code_counts"][0]) == tuple(
        field.name
        for field in fields(
            module.ResearchTeamSpecialistPeerReviewQualityReasonCodeCount,
        )
    )


def test_mapping_payload_rebuilds_a_complete_typed_report() -> None:
    module = api()
    payload = one_row_payload()

    rebuilt = module.research_team_specialist_peer_review_quality_report_payload(
        MappingProxyType(payload),
    )

    assert type(rebuilt) is dict
    assert rebuilt == payload
    assert rebuilt is not payload


@pytest.mark.parametrize("target", ("report", "row", "reason_code_count"))
def test_mapping_payload_requires_exact_canonical_schema_and_order(
    target: str,
) -> None:
    module = api()
    payload = one_row_payload()

    if target == "report":
        payload = dict(reversed(tuple(payload.items())))
    elif target == "row":
        payload["rows"][0] = dict(
            reversed(tuple(payload["rows"][0].items())),
        )
    else:
        payload["reason_code_counts"][0] = dict(
            reversed(tuple(payload["reason_code_counts"][0].items())),
        )
    resign_payload(payload)

    with pytest.raises(ValueError, match="schema|sequence"):
        module.research_team_specialist_peer_review_quality_report_payload(payload)


@pytest.mark.parametrize("target", ("report", "row", "reason_code_count"))
def test_mapping_payload_rejects_missing_and_extra_schema_fields(
    target: str,
) -> None:
    module = api()
    payload = one_row_payload()
    if target == "report":
        mapping = payload
    elif target == "row":
        mapping = payload["rows"][0]
    else:
        mapping = payload["reason_code_counts"][0]

    missing = deepcopy(payload)
    if target == "report":
        missing.pop("status")
    elif target == "row":
        missing["rows"][0].pop("status")
    else:
        missing["reason_code_counts"][0].pop("count")
    resign_payload(missing)
    with pytest.raises(ValueError, match="schema"):
        module.research_team_specialist_peer_review_quality_report_payload(missing)

    mapping["unexpected_safe_field"] = "safe"
    resign_payload(payload)
    with pytest.raises(ValueError, match="schema"):
        module.research_team_specialist_peer_review_quality_report_payload(payload)


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error_match"),
    (
        ("reviewer_latency_seconds", "601.000000", "reviewer_latency_seconds"),
        ("memory_age_seconds", "601.000000", "memory_age_seconds"),
        ("disagreement_gap_ratio", "0.100000", "disagreement_gap_ratio"),
        (
            "evidence_coverage_gap_ratio",
            "0.100000",
            "evidence_coverage_gap_ratio",
        ),
        (
            "correction_follow_through_gap_ratio",
            "0.100000",
            "correction_follow_through_gap_ratio",
        ),
        ("stale_memory_component", "0.100000", "stale_memory_component"),
        ("reviewer_latency_component", "0.100000", "reviewer_latency_component"),
        ("peer_review_risk_score", "0.100000", "peer_review_risk_score"),
        ("status", "watch", "status"),
        (
            "reason_codes",
            ["peer_review_disagreement_handling_watch"],
            "reason_codes|status",
        ),
    ),
)
def test_mapping_payload_recomputes_every_row_derived_field(
    field_name: str,
    forged_value: object,
    error_match: str,
) -> None:
    module = api()
    payload = one_row_payload()
    payload["rows"][0][field_name] = forged_value
    resign_payload(payload)

    with pytest.raises(ValueError, match=error_match):
        module.research_team_specialist_peer_review_quality_report_payload(payload)


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error_match"),
    (
        ("review_count", "2", "review_count"),
        ("pass_count", "0", "pass_count"),
        ("watch_count", "1", "watch_count"),
        ("block_count", "1", "block_count"),
        (
            "unresolved_disagreement_count",
            "1",
            "unresolved_disagreement_count",
        ),
        ("evidence_gap_count", "1", "evidence_gap_count"),
        ("correction_gap_count", "1", "correction_gap_count"),
        ("stale_memory_count", "1", "stale_memory_count"),
        ("delayed_reviewer_count", "1", "delayed_reviewer_count"),
        ("max_peer_review_risk_score", "0.500000", "max_peer_review_risk_score"),
        (
            "average_peer_review_risk_score",
            "0.500000",
            "average_peer_review_risk_score",
        ),
        ("status", "watch", "status"),
        (
            "reason_code_counts",
            [
                {
                    "reason_code": "peer_review_quality_pass",
                    "count": "2",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            ],
            "reason_code_counts",
        ),
        (
            "reason_codes",
            ["peer_review_disagreement_handling_watch"],
            "reason_codes",
        ),
    ),
)
def test_mapping_payload_recomputes_every_report_derived_field(
    field_name: str,
    forged_value: object,
    error_match: str,
) -> None:
    module = api()
    payload = one_row_payload()
    payload[field_name] = forged_value
    resign_payload(payload)

    with pytest.raises(ValueError, match=error_match):
        module.research_team_specialist_peer_review_quality_report_payload(payload)


def test_config_version_uniquely_pins_thresholds_and_weights() -> None:
    with pytest.raises(ValueError, match="supported config version"):
        config(config_version="peer-review-quality-custom-v1")
    with pytest.raises(ValueError, match="supported default"):
        config(
            disagreement_watch_gap_ratio=d("0.200000"),
            disagreement_block_gap_ratio=d("0.600000"),
        )
    with pytest.raises(ValueError, match="supported default"):
        config(
            disagreement_weight=d("0.200000"),
            evidence_weight=d("0.250000"),
        )


def test_raw_decimal_bounds_are_checked_before_quantization() -> None:
    with pytest.raises(ValueError, match="disagreement_watch_gap_ratio.*between"):
        config(disagreement_watch_gap_ratio=d("-0.0000004"))
    with pytest.raises(ValueError, match="disagreement_block_gap_ratio.*between"):
        config(disagreement_block_gap_ratio=d("1.0000004"))
    with pytest.raises(ValueError, match="disagreement_total_count.*nonnegative"):
        peer_review_snapshot(
            "team-alpha",
            "reviewer-macro",
            REVIEW_A,
            OUTPUT_A,
            EVIDENCE_A,
            disagreement_total="-0.0000004",
            disagreement_resolved="0",
            evidence_required="1",
            evidence_covered="1",
            correction_required="1",
            correction_completed="1",
            memory_age_seconds=0,
            reviewer_latency_seconds=0,
        )


def test_decimal_validation_rejects_signed_zero_nonfinite_and_oversized_values() -> None:
    with pytest.raises(ValueError, match="disagreement_watch_gap_ratio.*signed zero"):
        config(disagreement_watch_gap_ratio=d("-0.000000"))
    with pytest.raises(ValueError, match="reviewer_latency_watch_seconds.*signed zero"):
        config(reviewer_latency_watch_seconds=d("-0.000000"))
    with pytest.raises(ValueError, match="disagreement_total_count.*signed zero"):
        peer_review_snapshot(
            "team-alpha",
            "reviewer-macro",
            REVIEW_A,
            OUTPUT_A,
            EVIDENCE_A,
            disagreement_total="-0",
            disagreement_resolved="0",
            evidence_required="1",
            evidence_covered="1",
            correction_required="1",
            correction_completed="1",
            memory_age_seconds=0,
            reviewer_latency_seconds=0,
        )
    for value in ("NaN", "sNaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="finite"):
            config(disagreement_watch_gap_ratio=d(value))
    with pytest.raises(ValueError):
        config(disagreement_watch_gap_ratio=d(f"{'9' * 1000}.000000"))

    payload = one_row_payload()
    payload["rows"][0]["disagreement_total_count"] = "-0.0000004"
    resign_payload(payload)
    with pytest.raises(ValueError, match="disagreement_total_count.*nonnegative"):
        api().research_team_specialist_peer_review_quality_report_payload(payload)

    payload = one_row_payload()
    payload["rows"][0]["disagreement_gap_ratio"] = "-0.000000"
    resign_payload(payload)
    with pytest.raises(ValueError, match="disagreement_gap_ratio.*signed zero"):
        api().research_team_specialist_peer_review_quality_report_payload(payload)

    payload = one_row_payload()
    payload["rows"][0]["disagreement_gap_ratio"] = "NaN"
    resign_payload(payload)
    with pytest.raises(ValueError, match="disagreement_gap_ratio.*finite"):
        api().research_team_specialist_peer_review_quality_report_payload(payload)


def test_object_setattr_tampering_revalidates_config_snapshot_row_and_reason_counts() -> None:
    module = api()
    snapshot = peer_review_snapshot(
        "team-alpha",
        "reviewer-macro",
        REVIEW_A,
        OUTPUT_A,
        EVIDENCE_A,
        disagreement_total="1",
        disagreement_resolved="1",
        evidence_required="1",
        evidence_covered="1",
        correction_required="1",
        correction_completed="1",
        memory_age_seconds=0,
        reviewer_latency_seconds=0,
    )

    forged_config = config()
    object.__setattr__(
        forged_config,
        "disagreement_watch_gap_ratio",
        d("-0.000000"),
    )
    with pytest.raises(ValueError, match="disagreement_watch_gap_ratio.*signed zero"):
        build_report(snapshot, cfg=forged_config)

    forged_snapshot = peer_review_snapshot(
        "team-alpha",
        "reviewer-macro",
        REVIEW_A,
        OUTPUT_A,
        EVIDENCE_A,
        disagreement_total="1",
        disagreement_resolved="1",
        evidence_required="1",
        evidence_covered="1",
        correction_required="1",
        correction_completed="1",
        memory_age_seconds=0,
        reviewer_latency_seconds=0,
    )
    object.__setattr__(
        forged_snapshot,
        "disagreement_total_count",
        d("-0.000000"),
    )
    with pytest.raises(ValueError, match="disagreement_total_count.*signed zero"):
        build_report(forged_snapshot)

    report = build_report(snapshot)
    object.__setattr__(report.rows[0], "status", "watch")
    object.__setattr__(
        report.rows[0],
        "derived_validation_digest",
        module._digest_value(report.rows[0]),
    )
    object.__setattr__(report, "derived_validation_digest", module._digest_value(report))
    with pytest.raises(ValueError, match="status"):
        module.research_team_specialist_peer_review_quality_report_payload(report)

    report = build_report(snapshot)
    object.__setattr__(report.reason_code_counts[0], "count", d("2"))
    object.__setattr__(report, "derived_validation_digest", module._digest_value(report))
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_team_specialist_peer_review_quality_report_payload(report)


def test_decimal_results_do_not_depend_on_the_callers_global_context() -> None:
    snapshot = peer_review_snapshot(
        "team-alpha",
        "reviewer-macro",
        REVIEW_A,
        OUTPUT_A,
        EVIDENCE_A,
        disagreement_total="6",
        disagreement_resolved="5",
        evidence_required="1",
        evidence_covered="1",
        correction_required="1",
        correction_completed="1",
        memory_age_seconds=0,
        reviewer_latency_seconds=0,
    )

    with localcontext() as caller_context:
        caller_context.prec = 2
        report = build_report(snapshot)

    assert report.rows[0].disagreement_gap_ratio == d("0.166667")
    assert report.rows[0].peer_review_risk_score == d("0.041667")


def test_module_scope_has_no_db_network_wallet_order_trade_or_live_surface() -> None:
    module = api()
    source_text = inspect.getsource(module)
    tree = ast.parse(source_text)

    assert module.RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_REPORT_CONFIG_VERSION",
        "RESEARCH_TEAM_SPECIALIST_PEER_REVIEW_QUALITY_STATUSES",
        "ResearchTeamSpecialistPeerReviewQualityReportConfig",
        "ResearchTeamSpecialistPeerReviewQualitySnapshot",
        "ResearchTeamSpecialistPeerReviewQualityReasonCodeCount",
        "ResearchTeamSpecialistPeerReviewQualityRow",
        "ResearchTeamSpecialistPeerReviewQualityReport",
        "build_research_team_specialist_peer_review_quality_report",
        "research_team_specialist_peer_review_quality_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "private_key",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth",
        "live",
        "network",
        "connect(",
        "open(",
        "subprocess",
        "pathlib",
    )
    lowered = source_text.lower()
    assert all(term not in lowered for term in forbidden_source_terms)

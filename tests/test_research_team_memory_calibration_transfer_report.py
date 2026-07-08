from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import importlib
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
TRANSFER_A = "sha256:" + ("a" * 64)
TRANSFER_B = "sha256:" + ("b" * 64)
TRANSFER_C = "sha256:" + ("c" * 64)
PRECEDENT_A = "sha256:" + ("1" * 64)
PRECEDENT_B = "sha256:" + ("2" * 64)
PRECEDENT_C = "sha256:" + ("3" * 64)
CORRECTION_A = "sha256:" + ("4" * 64)
CORRECTION_B = "sha256:" + ("5" * 64)
CORRECTION_C = "sha256:" + ("6" * 64)
MEMORY_A = "sha256:" + ("7" * 64)
MEMORY_B = "sha256:" + ("8" * 64)
MEMORY_C = "sha256:" + ("9" * 64)
EVIDENCE_A = "sha256:" + ("d" * 64)
EVIDENCE_B = "sha256:" + ("e" * 64)
EVIDENCE_C = "sha256:" + ("f" * 64)
REVIEW_A = "sha256:" + ("0" * 64)
REVIEW_B = "sha256:" + ("b" * 64)
REVIEW_C = "sha256:" + ("c" * 64)


class _DecimalSubclass(Decimal):
    pass


class _TzInfoSubclass(tzinfo):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_memory_calibration_transfer_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "min_pass_precedent_relevance_score": d("0.750000"),
        "min_watch_precedent_relevance_score": d("0.500000"),
        "min_pass_correction_follow_through_score": d("0.700000"),
        "min_watch_correction_follow_through_score": d("0.450000"),
        "memory_watch_age_seconds": d("86400.000000"),
        "memory_block_age_seconds": d("259200.000000"),
        "min_pass_evidence_reuse_quality_score": d("0.700000"),
        "min_watch_evidence_reuse_quality_score": d("0.450000"),
        "peer_review_watch_gap_ratio": d("0.250000"),
        "peer_review_block_gap_ratio": d("0.500000"),
        "review_latency_watch_seconds": d("86400.000000"),
        "review_latency_block_seconds": d("172800.000000"),
        "precedent_relevance_weight": d("0.200000"),
        "correction_follow_through_weight": d("0.200000"),
        "stale_memory_penalty_weight": d("0.200000"),
        "evidence_reuse_quality_weight": d("0.150000"),
        "peer_review_coverage_weight": d("0.150000"),
        "review_latency_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchTeamMemoryCalibrationTransferReportConfig(**values)


def transfer_record(
    team_ref: str,
    source_domain_ref: str,
    target_domain_ref: str,
    transfer_digest: str,
    precedent_digest: str,
    correction_digest: str,
    memory_digest: str,
    evidence_digest: str,
    peer_review_digest: str,
    *,
    precedent_relevance_score: str,
    correction_follow_through_score: str,
    memory_age_seconds: int,
    evidence_reuse_quality_score: str,
    peer_review_required: str,
    peer_review_completed: str,
    review_latency_seconds: int,
) -> Any:
    module = api()
    return module.ResearchTeamMemoryCalibrationTransferRecord(
        team_ref=team_ref,
        source_domain_ref=source_domain_ref,
        target_domain_ref=target_domain_ref,
        transfer_digest=transfer_digest,
        precedent_bundle_digest=precedent_digest,
        correction_bundle_digest=correction_digest,
        memory_snapshot_digest=memory_digest,
        evidence_reuse_digest=evidence_digest,
        peer_review_digest=peer_review_digest,
        observed_at=GENERATED_AT - timedelta(seconds=300),
        memory_refreshed_at=GENERATED_AT - timedelta(seconds=memory_age_seconds),
        review_requested_at=GENERATED_AT - timedelta(seconds=review_latency_seconds + 60),
        review_completed_at=GENERATED_AT - timedelta(seconds=60),
        precedent_relevance_score=d(precedent_relevance_score),
        correction_follow_through_score=d(correction_follow_through_score),
        evidence_reuse_quality_score=d(evidence_reuse_quality_score),
        peer_review_required_count=d(peer_review_required),
        peer_review_completed_count=d(peer_review_completed),
    )


def build_report(
    *records: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_team_memory_calibration_transfer_report(
        records,
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


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected primitive numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_or_int_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_or_int_values(item)


def test_scores_memory_calibration_transfer_across_related_domains() -> None:
    module = api()

    report = build_report(
        transfer_record(
            "team-beta",
            "macro-rates",
            "crypto-flows",
            TRANSFER_C,
            PRECEDENT_C,
            CORRECTION_C,
            MEMORY_C,
            EVIDENCE_C,
            REVIEW_C,
            precedent_relevance_score="0.300000",
            correction_follow_through_score="0.300000",
            memory_age_seconds=300_000,
            evidence_reuse_quality_score="0.300000",
            peer_review_required="4",
            peer_review_completed="1",
            review_latency_seconds=200_000,
        ),
        transfer_record(
            "team-alpha",
            "macro-rates",
            "policy-rates",
            TRANSFER_A,
            PRECEDENT_A,
            CORRECTION_A,
            MEMORY_A,
            EVIDENCE_A,
            REVIEW_A,
            precedent_relevance_score="0.900000",
            correction_follow_through_score="0.850000",
            memory_age_seconds=600,
            evidence_reuse_quality_score="0.900000",
            peer_review_required="2",
            peer_review_completed="2",
            review_latency_seconds=3600,
        ),
        transfer_record(
            "team-alpha",
            "sports-injuries",
            "sports-weather",
            TRANSFER_B,
            PRECEDENT_B,
            CORRECTION_B,
            MEMORY_B,
            EVIDENCE_B,
            REVIEW_B,
            precedent_relevance_score="0.650000",
            correction_follow_through_score="0.600000",
            memory_age_seconds=90_000,
            evidence_reuse_quality_score="0.600000",
            peer_review_required="4",
            peer_review_completed="3",
            review_latency_seconds=90_000,
        ),
    )

    assert is_dataclass(report)
    assert module.RESEARCH_TEAM_MEMORY_CALIBRATION_TRANSFER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_RESEARCH_TEAM_MEMORY_CALIBRATION_TRANSFER_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.transfer_record_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.low_precedent_relevance_count == d("2")
    assert report.correction_follow_through_gap_count == d("2")
    assert report.stale_memory_penalty_count == d("2")
    assert report.evidence_reuse_quality_gap_count == d("2")
    assert report.peer_review_gap_count == d("2")
    assert report.review_latency_gap_count == d("2")
    assert report.max_transfer_risk_score == d("0.797500")
    assert report.average_transfer_risk_score == d("0.411358")
    assert report.reason_codes == (
        "precedent_relevance_block",
        "precedent_relevance_watch",
        "correction_follow_through_block",
        "correction_follow_through_watch",
        "stale_memory_penalty_block",
        "stale_memory_penalty_watch",
        "evidence_reuse_quality_block",
        "evidence_reuse_quality_watch",
        "peer_review_coverage_block",
        "peer_review_coverage_watch",
        "review_latency_block",
        "review_latency_watch",
    )

    passed, watched, blocked = report.rows
    assert (passed.team_ref, passed.source_domain_ref, passed.target_domain_ref) == (
        "team-alpha",
        "macro-rates",
        "policy-rates",
    )
    assert passed.precedent_relevance_gap == d("0.100000")
    assert passed.correction_follow_through_gap == d("0.150000")
    assert passed.stale_memory_component == d("0.002315")
    assert passed.evidence_reuse_quality_gap == d("0.100000")
    assert passed.peer_review_coverage_gap_ratio == d("0.000000")
    assert passed.review_latency_component == d("0.020833")
    assert passed.transfer_risk_score == d("0.067546")
    assert passed.status == "pass"
    assert passed.reason_codes == ("memory_calibration_transfer_pass",)

    assert (watched.team_ref, watched.source_domain_ref, watched.target_domain_ref) == (
        "team-alpha",
        "sports-injuries",
        "sports-weather",
    )
    assert watched.transfer_risk_score == d("0.369028")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "precedent_relevance_watch",
        "correction_follow_through_watch",
        "stale_memory_penalty_watch",
        "evidence_reuse_quality_watch",
        "peer_review_coverage_watch",
        "review_latency_watch",
    )

    assert (blocked.team_ref, blocked.source_domain_ref, blocked.target_domain_ref) == (
        "team-beta",
        "macro-rates",
        "crypto-flows",
    )
    assert blocked.transfer_risk_score == d("0.797500")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "precedent_relevance_block",
        "correction_follow_through_block",
        "stale_memory_penalty_block",
        "evidence_reuse_quality_block",
        "peer_review_coverage_block",
        "review_latency_block",
    )
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_only_numerics(report)


def test_empty_report_blocks_with_decimal_zeroes_and_hard_flags() -> None:
    module = api()

    report = build_report()

    assert report.status == "block"
    assert report.transfer_record_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.rows == ()
    assert report.max_transfer_risk_score == d("0.000000")
    assert report.average_transfer_risk_score == d("0.000000")
    assert report.reason_codes == ("memory_calibration_transfer_empty",)
    assert report.reason_code_counts == (
        module.ResearchTeamMemoryCalibrationTransferReasonCodeCount(
            reason_code="memory_calibration_transfer_empty",
            count=d("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_only_numerics(report)


def test_payload_is_deterministic_digest_bound_and_excludes_live_surfaces() -> None:
    module = api()
    first = transfer_record(
        "team-alpha",
        "sports-injuries",
        "sports-weather",
        TRANSFER_B,
        PRECEDENT_B,
        CORRECTION_B,
        MEMORY_B,
        EVIDENCE_B,
        REVIEW_B,
        precedent_relevance_score="0.650000",
        correction_follow_through_score="0.600000",
        memory_age_seconds=90_000,
        evidence_reuse_quality_score="0.600000",
        peer_review_required="4",
        peer_review_completed="3",
        review_latency_seconds=90_000,
    )
    second = transfer_record(
        "team-alpha",
        "macro-rates",
        "policy-rates",
        TRANSFER_A,
        PRECEDENT_A,
        CORRECTION_A,
        MEMORY_A,
        EVIDENCE_A,
        REVIEW_A,
        precedent_relevance_score="0.900000",
        correction_follow_through_score="0.850000",
        memory_age_seconds=600,
        evidence_reuse_quality_score="0.900000",
        peer_review_required="2",
        peer_review_completed="2",
        review_latency_seconds=3600,
    )

    report_a = build_report(first, second)
    report_b = build_report(second, first)
    payload = module.research_team_memory_calibration_transfer_report_payload(report_a)
    encoded = json.dumps(payload, sort_keys=True)

    assert report_a.rows == report_b.rows
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["transfer_record_count"] == "2"
    assert payload["rows"][0]["transfer_risk_score"] == "0.067546"
    assert payload["rows"][0]["transfer_digest"] == TRANSFER_A
    assert payload["rows"][0]["derived_validation_digest"] == (
        report_a.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    json.loads(encoded)

    forbidden_fragments = (
        "candidate-raw-123",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "https://example.test/source",
        "source_text",
        "postgres://",
        "table_name",
        "secret-token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    assert not any(fragment in encoded.lower() for fragment in forbidden_fragments)

    tampered = dict(payload)
    tampered["block_count"] = "7"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_memory_calibration_transfer_report_payload(tampered)

    object.__setattr__(report_a.rows[0], "transfer_risk_score", d("0.000001"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.research_team_memory_calibration_transfer_report_payload(report_a)

    with pytest.raises(ValueError, match="Decimal"):
        module.research_team_memory_calibration_transfer_report_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="float"):
        module.research_team_memory_calibration_transfer_report_payload(
            {"score": 0.5, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_memory_calibration_transfer_report_payload(
            {
                "market_id": "raw-market",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_enforces_exact_types_flags_sorting_and_relationships() -> None:
    module = api()

    with pytest.raises(ValueError, match="precedent_relevance_weight"):
        config(precedent_relevance_weight=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="correction_follow_through_weight"):
        config(correction_follow_through_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(review_latency_weight=d("0.090000"))
    with pytest.raises(ValueError, match="memory_block_age_seconds"):
        config(memory_block_age_seconds=d("86400.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)

    record = transfer_record(
        "team-alpha",
        "macro-rates",
        "policy-rates",
        TRANSFER_A,
        PRECEDENT_A,
        CORRECTION_A,
        MEMORY_A,
        EVIDENCE_A,
        REVIEW_A,
        precedent_relevance_score="0.900000",
        correction_follow_through_score="0.850000",
        memory_age_seconds=600,
        evidence_reuse_quality_score="0.900000",
        peer_review_required="2",
        peer_review_completed="2",
        review_latency_seconds=3600,
    )
    report = build_report(record)

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(record, readonly=False)
    with pytest.raises(ValueError, match="unsafe public"):
        replace(record, team_ref="candidate-raw-123")
    with pytest.raises(ValueError, match="must not exceed required"):
        replace(record, peer_review_completed_count=d("3"))
    with pytest.raises(ValueError, match="review_completed_at must not be before"):
        replace(
            record,
            review_completed_at=record.review_requested_at - timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="must not be in the future"):
        build_report(replace(record, memory_refreshed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="timezone-aware"):
        build_report(record, generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="datetime"):
        build_report(record, generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_TzInfoSubclass()))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
FEEDBACK_A = "sha256:" + ("a" * 64)
FEEDBACK_B = "sha256:" + ("b" * 64)
FEEDBACK_C = "sha256:" + ("c" * 64)
CORRECTION_A = "sha256:" + ("1" * 64)
CORRECTION_B = "sha256:" + ("2" * 64)
CORRECTION_C = "sha256:" + ("3" * 64)
MEMORY_A = "sha256:" + ("4" * 64)
MEMORY_B = "sha256:" + ("5" * 64)
MEMORY_C = "sha256:" + ("6" * 64)
CALIBRATION_A = "sha256:" + ("7" * 64)
CALIBRATION_B = "sha256:" + ("8" * 64)
CALIBRATION_C = "sha256:" + ("9" * 64)
EVIDENCE_A = "sha256:" + ("d" * 64)
EVIDENCE_B = "sha256:" + ("e" * 64)
EVIDENCE_C = "sha256:" + ("f" * 64)
PEER_A = "sha256:" + ("0" * 64)
PEER_B = "sha256:" + ("b" * 64)
PEER_C = "sha256:" + ("c" * 64)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_review_feedback_absorption_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _TzInfoSubclass(tzinfo):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_review_feedback_absorption_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "min_pass_correction_follow_through_ratio": d("0.900000"),
        "min_watch_correction_follow_through_ratio": d("0.750000"),
        "min_pass_stale_memory_reduction_ratio": d("0.750000"),
        "min_watch_stale_memory_reduction_ratio": d("0.500000"),
        "min_pass_calibration_movement_ratio": d("0.600000"),
        "min_watch_calibration_movement_ratio": d("0.300000"),
        "min_pass_evidence_reuse_quality_score": d("0.800000"),
        "min_watch_evidence_reuse_quality_score": d("0.600000"),
        "min_pass_peer_review_coverage_ratio": d("0.900000"),
        "min_watch_peer_review_coverage_ratio": d("0.750000"),
        "review_latency_watch_seconds": d("86400.000000"),
        "review_latency_block_seconds": d("259200.000000"),
        "correction_follow_through_weight": d("0.200000"),
        "stale_memory_reduction_weight": d("0.150000"),
        "calibration_movement_weight": d("0.200000"),
        "evidence_reuse_quality_weight": d("0.150000"),
        "peer_review_coverage_weight": d("0.150000"),
        "review_latency_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchTeamReviewFeedbackAbsorptionReportConfig(**values)


def feedback_record(
    team_ref: str,
    review_stream_ref: str,
    feedback_cycle_digest: str,
    correction_batch_digest: str,
    memory_snapshot_digest: str,
    calibration_snapshot_digest: str,
    evidence_bundle_digest: str,
    peer_review_digest: str,
    *,
    review_latency_seconds: int,
    correction_required: str,
    correction_completed: str,
    stale_memory_before: str,
    stale_memory_after: str,
    calibration_error_before: str,
    calibration_error_after: str,
    evidence_reuse_quality_score: str,
    peer_review_required: str,
    peer_review_completed: str,
):
    module = api()
    return module.ResearchTeamReviewFeedbackAbsorptionRecord(
        team_ref=team_ref,
        review_stream_ref=review_stream_ref,
        feedback_cycle_digest=feedback_cycle_digest,
        correction_batch_digest=correction_batch_digest,
        memory_snapshot_digest=memory_snapshot_digest,
        calibration_snapshot_digest=calibration_snapshot_digest,
        evidence_bundle_digest=evidence_bundle_digest,
        peer_review_digest=peer_review_digest,
        review_requested_at=GENERATED_AT - timedelta(seconds=review_latency_seconds),
        review_completed_at=GENERATED_AT,
        correction_required_count=d(correction_required),
        correction_completed_count=d(correction_completed),
        stale_memory_before_count=d(stale_memory_before),
        stale_memory_after_count=d(stale_memory_after),
        calibration_error_before=d(calibration_error_before),
        calibration_error_after=d(calibration_error_after),
        evidence_reuse_quality_score=d(evidence_reuse_quality_score),
        peer_review_required_count=d(peer_review_required),
        peer_review_completed_count=d(peer_review_completed),
    )


def build_report(
    *records: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_review_feedback_absorption_report(
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


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_values(item)


def canonical_digest(value: object) -> str:
    def unsigned(item: object) -> object:
        if type(item) is dict:
            return {
                key: unsigned(nested)
                for key, nested in item.items()
                if key != "derived_validation_digest"
            }
        if type(item) is list:
            return [unsigned(nested) for nested in item]
        return item

    canonical = json.dumps(
        unsigned(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_scores_review_feedback_absorption_from_required_dimensions() -> None:
    module = api()

    report = build_report(
        feedback_record(
            "team-beta",
            "review-stream-red",
            FEEDBACK_C,
            CORRECTION_C,
            MEMORY_C,
            CALIBRATION_C,
            EVIDENCE_C,
            PEER_C,
            review_latency_seconds=300_000,
            correction_required="10",
            correction_completed="5",
            stale_memory_before="10",
            stale_memory_after="6",
            calibration_error_before="0.200000",
            calibration_error_after="0.180000",
            evidence_reuse_quality_score="0.400000",
            peer_review_required="4",
            peer_review_completed="1",
        ),
        feedback_record(
            "team-alpha",
            "review-stream-green",
            FEEDBACK_A,
            CORRECTION_A,
            MEMORY_A,
            CALIBRATION_A,
            EVIDENCE_A,
            PEER_A,
            review_latency_seconds=3600,
            correction_required="10",
            correction_completed="10",
            stale_memory_before="4",
            stale_memory_after="1",
            calibration_error_before="0.200000",
            calibration_error_after="0.050000",
            evidence_reuse_quality_score="0.900000",
            peer_review_required="2",
            peer_review_completed="2",
        ),
        feedback_record(
            "team-alpha",
            "review-stream-yellow",
            FEEDBACK_B,
            CORRECTION_B,
            MEMORY_B,
            CALIBRATION_B,
            EVIDENCE_B,
            PEER_B,
            review_latency_seconds=90_000,
            correction_required="10",
            correction_completed="8",
            stale_memory_before="10",
            stale_memory_after="4",
            calibration_error_before="0.200000",
            calibration_error_after="0.120000",
            evidence_reuse_quality_score="0.700000",
            peer_review_required="4",
            peer_review_completed="3",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_RESEARCH_TEAM_REVIEW_FEEDBACK_ABSORPTION_REPORT_CONFIG_VERSION
    )
    assert module.RESEARCH_TEAM_REVIEW_FEEDBACK_ABSORPTION_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "block"
    assert report.feedback_record_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.correction_gap_count == d("2")
    assert report.stale_memory_reduction_gap_count == d("2")
    assert report.calibration_movement_gap_count == d("2")
    assert report.low_evidence_reuse_quality_count == d("2")
    assert report.peer_review_gap_count == d("2")
    assert report.review_latency_gap_count == d("2")
    assert report.max_feedback_absorption_risk_score == d("0.722500")
    assert report.average_feedback_absorption_risk_score == d("0.393889")
    assert report.reason_codes == (
        "correction_follow_through_block",
        "correction_follow_through_watch",
        "stale_memory_reduction_block",
        "stale_memory_reduction_watch",
        "calibration_movement_block",
        "calibration_movement_watch",
        "evidence_reuse_quality_block",
        "evidence_reuse_quality_watch",
        "peer_review_coverage_block",
        "peer_review_coverage_watch",
        "review_latency_block",
        "review_latency_watch",
    )

    passed, watched, blocked = report.rows
    assert (passed.team_ref, passed.review_stream_ref) == (
        "team-alpha",
        "review-stream-green",
    )
    assert passed.correction_follow_through_ratio == d("1.000000")
    assert passed.stale_memory_reduction_ratio == d("0.750000")
    assert passed.calibration_movement_ratio == d("0.750000")
    assert passed.evidence_reuse_quality_gap == d("0.100000")
    assert passed.peer_review_coverage_ratio == d("1.000000")
    assert passed.review_latency_seconds == d("3600.000000")
    assert passed.feedback_absorption_risk_score == d("0.104583")
    assert passed.status == "pass"
    assert passed.reason_codes == ("review_feedback_absorption_pass",)

    assert (watched.team_ref, watched.review_stream_ref) == (
        "team-alpha",
        "review-stream-yellow",
    )
    assert watched.feedback_absorption_risk_score == d("0.354583")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "correction_follow_through_watch",
        "stale_memory_reduction_watch",
        "calibration_movement_watch",
        "evidence_reuse_quality_watch",
        "peer_review_coverage_watch",
        "review_latency_watch",
    )

    assert (blocked.team_ref, blocked.review_stream_ref) == (
        "team-beta",
        "review-stream-red",
    )
    assert blocked.feedback_absorption_risk_score == d("0.722500")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "correction_follow_through_block",
        "stale_memory_reduction_block",
        "calibration_movement_block",
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


def test_empty_report_blocks_without_live_or_identifier_surface() -> None:
    module = api()

    report = build_report()

    assert report.status == "block"
    assert report.feedback_record_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.rows == ()
    assert report.max_feedback_absorption_risk_score == d("0.000000")
    assert report.average_feedback_absorption_risk_score == d("0.000000")
    assert report.reason_codes == ("review_feedback_absorption_empty",)
    assert report.reason_code_counts == (
        module.ResearchTeamReviewFeedbackAbsorptionReasonCodeCount(
            reason_code="review_feedback_absorption_empty",
            count=d("1"),
        ),
    )
    assert_decimal_only_numerics(report)


def test_payload_serialization_is_deterministic_tamper_evident_and_redacted() -> None:
    module = api()
    first = feedback_record(
        "team-alpha",
        "review-stream-yellow",
        FEEDBACK_B,
        CORRECTION_B,
        MEMORY_B,
        CALIBRATION_B,
        EVIDENCE_B,
        PEER_B,
        review_latency_seconds=90_000,
        correction_required="10",
        correction_completed="8",
        stale_memory_before="10",
        stale_memory_after="4",
        calibration_error_before="0.200000",
        calibration_error_after="0.120000",
        evidence_reuse_quality_score="0.700000",
        peer_review_required="4",
        peer_review_completed="3",
    )
    second = feedback_record(
        "team-alpha",
        "review-stream-green",
        FEEDBACK_A,
        CORRECTION_A,
        MEMORY_A,
        CALIBRATION_A,
        EVIDENCE_A,
        PEER_A,
        review_latency_seconds=3600,
        correction_required="10",
        correction_completed="10",
        stale_memory_before="4",
        stale_memory_after="1",
        calibration_error_before="0.200000",
        calibration_error_after="0.050000",
        evidence_reuse_quality_score="0.900000",
        peer_review_required="2",
        peer_review_completed="2",
    )

    report_a = build_report(first, second)
    report_b = build_report(second, first)
    payload = module.research_team_review_feedback_absorption_report_payload(report_a)
    encoded = json.dumps(payload, sort_keys=True)

    assert report_a.rows == report_b.rows
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["feedback_record_count"] == "2"
    assert payload["rows"][0]["feedback_absorption_risk_score"] == "0.104583"
    assert payload["rows"][0]["feedback_cycle_digest"] == FEEDBACK_A
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
        "market_id",
        "market-slug",
        "will-this-happen",
        "https://example.test/source",
        "postgres://",
        "secret-token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    assert not any(fragment in encoded for fragment in leaked_fragments)

    tampered = dict(payload)
    tampered["block_count"] = "7"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_review_feedback_absorption_report_payload(tampered)

    object.__setattr__(report_a.rows[0], "feedback_absorption_risk_score", d("0.000001"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.research_team_review_feedback_absorption_report_payload(report_a)

    with pytest.raises(ValueError, match="Decimal"):
        module.research_team_review_feedback_absorption_report_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="float"):
        module.research_team_review_feedback_absorption_report_payload(
            {"score": 0.5, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_review_feedback_absorption_report_payload(
            {
                "market_id": "raw-market",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_enforces_exact_decimal_types_hard_flags_and_safe_refs() -> None:
    with pytest.raises(ValueError, match="correction_follow_through_weight"):
        config(correction_follow_through_weight=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_memory_reduction_weight"):
        config(stale_memory_reduction_weight=_DecimalSubclass("0.150000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(review_latency_weight=d("0.140000"))
    with pytest.raises(ValueError, match="review_latency_block_seconds"):
        config(review_latency_block_seconds=d("86400.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)

    record = feedback_record(
        "team-alpha",
        "review-stream-green",
        FEEDBACK_A,
        CORRECTION_A,
        MEMORY_A,
        CALIBRATION_A,
        EVIDENCE_A,
        PEER_A,
        review_latency_seconds=3600,
        correction_required="10",
        correction_completed="10",
        stale_memory_before="4",
        stale_memory_after="1",
        calibration_error_before="0.200000",
        calibration_error_after="0.050000",
        evidence_reuse_quality_score="0.900000",
        peer_review_required="2",
        peer_review_completed="2",
    )
    report = build_report(record)

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(record, readonly=False)
    with pytest.raises(ValueError, match="unsafe public"):
        replace(record, team_ref="candidate-raw-123")
    with pytest.raises(ValueError, match="must not exceed required"):
        replace(record, correction_completed_count=d("11"))
    with pytest.raises(ValueError, match="review_completed_at"):
        replace(record, review_completed_at=record.review_requested_at - timedelta(seconds=1))
    with pytest.raises(ValueError, match="must not be in the future"):
        build_report(replace(record, review_completed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="timezone-aware"):
        build_report(record, generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        build_report(record, generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_TzInfoSubclass()))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_payload_schema_is_exact_canonical_and_tamper_evident() -> None:
    module = api()
    report = build_report(
        feedback_record(
            "team-alpha",
            "review-stream-green",
            FEEDBACK_A,
            CORRECTION_A,
            MEMORY_A,
            CALIBRATION_A,
            EVIDENCE_A,
            PEER_A,
            review_latency_seconds=3600,
            correction_required="10",
            correction_completed="10",
            stale_memory_before="4",
            stale_memory_after="1",
            calibration_error_before="0.200000",
            calibration_error_after="0.050000",
            evidence_reuse_quality_score="0.900000",
            peer_review_required="2",
            peer_review_completed="2",
        ),
    )
    payload = module.research_team_review_feedback_absorption_report_payload(report)

    assert module.validate_research_team_review_feedback_absorption_public_payload(payload)
    assert module.research_team_review_feedback_absorption_report_digest(report) == (
        report.derived_validation_digest
    )
    assert module.research_team_review_feedback_absorption_report_digest(payload) == (
        report.derived_validation_digest
    )

    invalid_payloads: list[dict[str, Any]] = []

    extra_top_level = deepcopy(payload)
    extra_top_level["harmless_note"] = "unexpected"
    extra_top_level["derived_validation_digest"] = canonical_digest(extra_top_level)
    invalid_payloads.append(extra_top_level)

    missing_top_level = deepcopy(payload)
    missing_top_level.pop("status")
    missing_top_level["derived_validation_digest"] = canonical_digest(missing_top_level)
    invalid_payloads.append(missing_top_level)

    noncanonical_decimal = deepcopy(payload)
    noncanonical_decimal["feedback_record_count"] = "1.0"
    noncanonical_decimal["derived_validation_digest"] = canonical_digest(noncanonical_decimal)
    invalid_payloads.append(noncanonical_decimal)

    noncanonical_datetime = deepcopy(payload)
    noncanonical_datetime["generated_at"] = "2026-07-08T08:00:00-04:00"
    noncanonical_datetime["derived_validation_digest"] = canonical_digest(noncanonical_datetime)
    invalid_payloads.append(noncanonical_datetime)

    extra_nested = deepcopy(payload)
    extra_nested["rows"][0]["harmless_note"] = "unexpected"
    extra_nested["rows"][0]["derived_validation_digest"] = canonical_digest(
        extra_nested["rows"][0],
    )
    extra_nested["derived_validation_digest"] = canonical_digest(extra_nested)
    invalid_payloads.append(extra_nested)

    missing_nested = deepcopy(payload)
    missing_nested["reason_code_counts"][0].pop("count")
    missing_nested["derived_validation_digest"] = canonical_digest(missing_nested)
    invalid_payloads.append(missing_nested)

    wrong_nested_container = deepcopy(payload)
    wrong_nested_container["rows"] = tuple(wrong_nested_container["rows"])
    invalid_payloads.append(wrong_nested_container)

    false_hard_flag = deepcopy(payload)
    false_hard_flag["readonly"] = False
    false_hard_flag["derived_validation_digest"] = canonical_digest(false_hard_flag)
    invalid_payloads.append(false_hard_flag)

    for invalid in invalid_payloads:
        assert not module.validate_research_team_review_feedback_absorption_public_payload(
            invalid,
        )
        with pytest.raises(ValueError):
            module.research_team_review_feedback_absorption_report_payload(invalid)


def test_direct_rows_reject_forged_derived_metrics_before_digesting() -> None:
    report = build_report(
        feedback_record(
            "team-alpha",
            "review-stream-green",
            FEEDBACK_A,
            CORRECTION_A,
            MEMORY_A,
            CALIBRATION_A,
            EVIDENCE_A,
            PEER_A,
            review_latency_seconds=3600,
            correction_required="10",
            correction_completed="10",
            stale_memory_before="4",
            stale_memory_after="1",
            calibration_error_before="0.200000",
            calibration_error_after="0.050000",
            evidence_reuse_quality_score="0.900000",
            peer_review_required="2",
            peer_review_completed="2",
        ),
    )
    row = report.rows[0]

    forged_values = {
        "review_latency_seconds": d("3601.000000"),
        "correction_follow_through_ratio": d("0.999999"),
        "stale_memory_reduction_ratio": d("0.700000"),
        "calibration_movement_ratio": d("0.700000"),
        "evidence_reuse_quality_gap": d("0.200000"),
        "peer_review_coverage_ratio": d("0.900000"),
    }
    for field_name, forged_value in forged_values.items():
        with pytest.raises(ValueError, match=field_name):
            replace(
                row,
                **{
                    field_name: forged_value,
                    "derived_validation_digest": "",
                },
            )


def test_public_dataclasses_are_frozen_final_and_decimal_strict() -> None:
    module = api()
    public_classes = (
        module.ResearchTeamReviewFeedbackAbsorptionReportConfig,
        module.ResearchTeamReviewFeedbackAbsorptionRecord,
        module.ResearchTeamReviewFeedbackAbsorptionRow,
        module.ResearchTeamReviewFeedbackAbsorptionReasonCodeCount,
        module.ResearchTeamReviewFeedbackAbsorptionReport,
    )

    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True
        with pytest.raises(TypeError):
            type(f"Bad{public_class.__name__}", (public_class,), {})

    with pytest.raises(ValueError, match="correction_required_count"):
        module.ResearchTeamReviewFeedbackAbsorptionRecord(
            team_ref="team-alpha",
            review_stream_ref="review-stream-green",
            feedback_cycle_digest=FEEDBACK_A,
            correction_batch_digest=CORRECTION_A,
            memory_snapshot_digest=MEMORY_A,
            calibration_snapshot_digest=CALIBRATION_A,
            evidence_bundle_digest=EVIDENCE_A,
            peer_review_digest=PEER_A,
            review_requested_at=GENERATED_AT - timedelta(hours=1),
            review_completed_at=GENERATED_AT,
            correction_required_count=_DecimalSubclass("10"),
            correction_completed_count=d("10"),
            stale_memory_before_count=d("4"),
            stale_memory_after_count=d("1"),
            calibration_error_before=d("0.200000"),
            calibration_error_after=d("0.050000"),
            evidence_reuse_quality_score=d("0.900000"),
            peer_review_required_count=d("2"),
            peer_review_completed_count=d("2"),
        )


def test_module_has_no_io_execution_recommendation_or_sizing_surface() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "aiohttp",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    unsafe_surface_terms = (
        "auth",
        "client",
        "database",
        "execution",
        "live",
        "network",
        "order",
        "persist",
        "recommendation",
        "sizing",
        "trade",
        "wallet",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_surface_terms)
    for public_class in (
        module.ResearchTeamReviewFeedbackAbsorptionReportConfig,
        module.ResearchTeamReviewFeedbackAbsorptionRecord,
        module.ResearchTeamReviewFeedbackAbsorptionRow,
        module.ResearchTeamReviewFeedbackAbsorptionReasonCodeCount,
        module.ResearchTeamReviewFeedbackAbsorptionReport,
    ):
        for field in fields(public_class):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_surface_terms)

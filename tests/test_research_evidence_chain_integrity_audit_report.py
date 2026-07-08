from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_evidence_chain_integrity_audit_report import (
    ResearchEvidenceChainIntegrityAuditConfig,
    ResearchEvidenceChainIntegrityAuditMetrics,
    ResearchEvidenceChainIntegrityAuditReport,
    build_research_evidence_chain_integrity_audit_report,
    research_evidence_chain_integrity_audit_public_payload,
    validate_research_evidence_chain_integrity_audit_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def metrics(
    *,
    aggregate_evidence_count: Decimal = d("6"),
    fresh_evidence_count: Decimal = d("6"),
    contradiction_count: Decimal = d("0"),
    source_class_count: Decimal = d("3"),
    rule_clarity_score: Decimal = d("0.920000"),
    custody_completeness_score: Decimal = d("0.950000"),
) -> ResearchEvidenceChainIntegrityAuditMetrics:
    return ResearchEvidenceChainIntegrityAuditMetrics(
        aggregate_evidence_count=aggregate_evidence_count,
        fresh_evidence_count=fresh_evidence_count,
        contradiction_count=contradiction_count,
        source_class_count=source_class_count,
        rule_clarity_score=rule_clarity_score,
        custody_completeness_score=custody_completeness_score,
    )


def build_report(
    metric_values: ResearchEvidenceChainIntegrityAuditMetrics = metrics(),
    *,
    config: ResearchEvidenceChainIntegrityAuditConfig | None = None,
) -> ResearchEvidenceChainIntegrityAuditReport:
    return build_research_evidence_chain_integrity_audit_report(
        metric_values,
        config=config or ResearchEvidenceChainIntegrityAuditConfig(),
        generated_at=GENERATED_AT,
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, (int, float, Decimal)):
        raise AssertionError(f"public payload contains numeric scalar: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")


def test_complete_aggregate_chain_passes_with_public_decimal_payload() -> None:
    report = build_report()

    assert report.audit_status == "pass"
    assert report.reason_codes == ("evidence_chain_integrity_pass",)
    assert report.aggregate_evidence_count == d("6")
    assert report.freshness_ratio == d("1.000000")
    assert report.source_class_count == d("3")
    assert report.audit_next_step == "continue_public_research_review"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.payload_digest) == 64
    int(report.payload_digest, 16)

    payload = research_evidence_chain_integrity_audit_public_payload(report)

    assert payload["audit_status"] == "pass"
    assert payload["aggregate_evidence_count"] == "6"
    assert payload["freshness_ratio"] == "1.000000"
    assert payload["payload_digest"] == report.payload_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_scalars(payload)
    assert validate_research_evidence_chain_integrity_audit_public_payload(payload)


def test_watch_status_for_degraded_but_not_blocking_evidence_chain() -> None:
    report = build_report(
        metrics(
            aggregate_evidence_count=d("4"),
            fresh_evidence_count=d("3"),
            contradiction_count=d("1"),
            source_class_count=d("2"),
            rule_clarity_score=d("0.760000"),
            custody_completeness_score=d("0.850000"),
        ),
    )

    assert report.audit_status == "watch"
    assert report.reason_codes == (
        "freshness_watch",
        "contradiction_watch",
        "rule_clarity_watch",
        "custody_completeness_watch",
    )
    assert report.audit_next_step == "refresh_public_evidence_chain"
    assert report.freshness_ratio == d("0.750000")


def test_block_status_for_missing_aggregate_evidence_or_custody_failures() -> None:
    report = build_report(
        metrics(
            aggregate_evidence_count=d("1"),
            fresh_evidence_count=d("0"),
            contradiction_count=d("3"),
            source_class_count=d("1"),
            rule_clarity_score=d("0.500000"),
            custody_completeness_score=d("0.400000"),
        ),
    )

    assert report.audit_status == "block"
    assert report.reason_codes == (
        "insufficient_aggregate_evidence",
        "freshness_block",
        "contradiction_block",
        "insufficient_source_class_diversity",
        "rule_clarity_block",
        "custody_completeness_block",
    )
    assert report.audit_next_step == "repair_public_evidence_chain"


def test_status_values_are_exactly_pass_watch_block() -> None:
    pass_report = build_report()
    watch_report = build_report(metrics(fresh_evidence_count=d("5")))
    block_report = build_report(
        metrics(aggregate_evidence_count=d("0"), fresh_evidence_count=d("0")),
    )

    assert {pass_report.audit_status, watch_report.audit_status, block_report.audit_status} == {
        "pass",
        "watch",
        "block",
    }

    with pytest.raises(ValueError, match="audit_status"):
        replace(pass_report, audit_status="blocked")


def test_digest_is_deterministic_and_rejects_report_and_payload_tampering() -> None:
    report = build_report()
    same_report = build_report()

    assert same_report.payload_digest == report.payload_digest
    assert same_report.payload == report.payload

    with pytest.raises(ValueError, match="payload_digest must match"):
        replace(report, payload_digest="0" * 64)

    payload = research_evidence_chain_integrity_audit_public_payload(report)
    tampered = dict(payload)
    tampered["config_version"] = "research-evidence-chain-integrity-audit-report-v2"
    with pytest.raises(ValueError, match="payload_digest must match"):
        research_evidence_chain_integrity_audit_public_payload(tampered)


def test_public_payload_rejects_raw_sources_identifiers_and_execution_language() -> None:
    payload = research_evidence_chain_integrity_audit_public_payload(build_report())

    unsafe_keys = (
        "source_url",
        "source_text",
        "source_ref",
        "candidate_id",
        "market_slug",
        "wallet_address",
        "auth_token",
        "order_id",
        "trade_id",
        "private_key",
        "live_execution",
        "position_size",
    )
    for key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_evidence_chain_integrity_audit_public_payload(unsafe_payload)

    unsafe_values = (
        "https://example.invalid/source",
        "raw source text",
        "candidate identifier",
        "market identifier",
        "recommend action",
        "size allocation",
    )
    for value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["config_version"] = value
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_evidence_chain_integrity_audit_public_payload(unsafe_payload)


def test_public_payload_rejects_numeric_scalars_and_false_flags() -> None:
    payload = research_evidence_chain_integrity_audit_public_payload(build_report())

    numeric_payload = dict(payload)
    numeric_payload["aggregate_evidence_count"] = 6
    with pytest.raises(ValueError, match="Decimal strings"):
        research_evidence_chain_integrity_audit_public_payload(numeric_payload)

    false_flag_payload = dict(payload)
    false_flag_payload["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        research_evidence_chain_integrity_audit_public_payload(false_flag_payload)


def test_decimal_only_validation_rejects_float_and_integer_inputs() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        ResearchEvidenceChainIntegrityAuditMetrics(
            aggregate_evidence_count=6,  # type: ignore[arg-type]
            fresh_evidence_count=d("6"),
            contradiction_count=d("0"),
            source_class_count=d("3"),
            rule_clarity_score=d("0.920000"),
            custody_completeness_score=d("0.950000"),
        )

    with pytest.raises(ValueError, match="Decimal"):
        ResearchEvidenceChainIntegrityAuditConfig(
            min_aggregate_evidence_count=3,  # type: ignore[arg-type]
        )


def test_rejects_inconsistent_metrics_and_bad_hard_flags() -> None:
    with pytest.raises(ValueError, match="fresh_evidence_count"):
        metrics(aggregate_evidence_count=d("2"), fresh_evidence_count=d("3"))

    with pytest.raises(ValueError, match="config"):
        build_research_evidence_chain_integrity_audit_report(
            metrics(),
            config="not config",  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="paper_only"):
        replace(metrics(), paper_only=False)


def test_report_consistency_rejects_manual_mismatches() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="freshness_ratio"):
        replace(report, freshness_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="audit_status"):
        replace(report, audit_status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("freshness_watch",))


def test_dataclasses_are_frozen() -> None:
    config = ResearchEvidenceChainIntegrityAuditConfig()
    metric_values = metrics()
    report = build_report()

    frozen_values: tuple[Any, ...] = (config, metric_values, report)
    for value in frozen_values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

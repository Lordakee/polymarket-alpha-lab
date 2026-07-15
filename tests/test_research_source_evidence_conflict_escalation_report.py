from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
import json

import pytest

import polymarket_alpha_lab.research_source_evidence_conflict_escalation_report as api
from polymarket_alpha_lab.research_source_evidence_conflict_escalation_report import (
    EvidenceConflictSignal,
    ResearchSourceEvidenceConflictEscalationConfig,
    ResearchSourceEvidenceConflictEscalationReport,
    ResearchSourceEvidenceConflictEscalationRow,
    build_research_source_evidence_conflict_escalation_report,
)


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _signal(
    *,
    case_key: str = "case_a",
    evidence_ref_digest: str = "a" * 64,
    counter_ref_digest: str = "b" * 64,
    observed_at: datetime = NOW - timedelta(minutes=10),
    deadline_at: datetime | None = NOW + timedelta(minutes=15),
    contradiction_severity: Decimal = Decimal("0.800000"),
    primary_authority_score: Decimal = Decimal("0.900000"),
    counter_authority_score: Decimal = Decimal("0.750000"),
    freshness_gap_seconds: Decimal = Decimal("3600.000000"),
    corroborating_group_count: Decimal = Decimal("1.000000"),
    conflicting_group_count: Decimal = Decimal("3.000000"),
    extraction_confidence: Decimal = Decimal("0.350000"),
) -> EvidenceConflictSignal:
    return EvidenceConflictSignal(
        case_key=case_key,
        evidence_ref_digest=evidence_ref_digest,
        counter_ref_digest=counter_ref_digest,
        observed_at=observed_at,
        deadline_at=deadline_at,
        contradiction_severity=contradiction_severity,
        primary_authority_score=primary_authority_score,
        counter_authority_score=counter_authority_score,
        freshness_gap_seconds=freshness_gap_seconds,
        corroborating_group_count=corroborating_group_count,
        conflicting_group_count=conflicting_group_count,
        extraction_confidence=extraction_confidence,
    )


def _report(
    signals: tuple[EvidenceConflictSignal, ...],
    *,
    config: ResearchSourceEvidenceConflictEscalationConfig | None = None,
) -> ResearchSourceEvidenceConflictEscalationReport:
    return build_research_source_evidence_conflict_escalation_report(
        signals,
        generated_at=NOW,
        config=config,
    )


def test_high_severity_authoritative_stale_uncorroborated_conflict_blocks() -> None:
    report = _report((_signal(),))

    row = report.rows[0]
    assert report.escalation_status == "block"
    assert report.case_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert row.escalation_status == "block"
    assert row.contradiction_pressure == Decimal("0.800000")
    assert row.authority_pressure == Decimal("0.900000")
    assert row.freshness_pressure == Decimal("1.000000")
    assert row.corroboration_gap_pressure == Decimal("1.000000")
    assert row.extraction_uncertainty_pressure == Decimal("0.650000")
    assert row.deadline_pressure == Decimal("0.750000")
    assert row.escalation_score == Decimal("0.815000")
    assert row.manual_review_required is True
    assert "manual_review_block" in row.reason_codes
    assert "high_authority_conflict" in row.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_watch_status_uses_deadline_and_corroboration_gap_pressure() -> None:
    report = _report(
        (
            _signal(
                contradiction_severity=Decimal("0.300000"),
                primary_authority_score=Decimal("0.400000"),
                counter_authority_score=Decimal("0.300000"),
                freshness_gap_seconds=Decimal("0.000000"),
                corroborating_group_count=Decimal("0.000000"),
                conflicting_group_count=Decimal("2.000000"),
                extraction_confidence=Decimal("0.850000"),
                deadline_at=NOW + timedelta(minutes=5),
            ),
        ),
    )

    row = report.rows[0]
    assert report.escalation_status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert row.escalation_status == "watch"
    assert row.deadline_pressure == Decimal("0.916667")
    assert row.corroboration_gap_pressure == Decimal("1.000000")
    assert row.escalation_score == Decimal("0.430000")
    assert row.manual_review_required is True
    assert "deadline_proximity" in row.reason_codes
    assert "manual_review_watch" in row.reason_codes


def test_low_pressure_conflict_passes_without_manual_review() -> None:
    report = _report(
        (
            _signal(
                contradiction_severity=Decimal("0.050000"),
                primary_authority_score=Decimal("0.100000"),
                counter_authority_score=Decimal("0.200000"),
                freshness_gap_seconds=Decimal("0.000000"),
                corroborating_group_count=Decimal("3.000000"),
                conflicting_group_count=Decimal("1.000000"),
                extraction_confidence=Decimal("0.950000"),
                deadline_at=None,
            ),
        ),
    )

    row = report.rows[0]
    assert report.escalation_status == "pass"
    assert report.pass_count == Decimal("1.000000")
    assert row.escalation_status == "pass"
    assert row.escalation_score == Decimal("0.075000")
    assert row.manual_review_required is False
    assert row.reason_codes == ("evidence_conflict_pass",)


def test_threshold_reason_escalates_below_weighted_watch_score() -> None:
    report = _report(
        (
            _signal(
                contradiction_severity=Decimal("0.700000"),
                primary_authority_score=Decimal("0.000000"),
                counter_authority_score=Decimal("0.000000"),
                freshness_gap_seconds=Decimal("0.000000"),
                corroborating_group_count=Decimal("1.000000"),
                conflicting_group_count=Decimal("1.000000"),
                extraction_confidence=Decimal("1.000000"),
                deadline_at=None,
            ),
        ),
    )

    row = report.rows[0]
    assert report.escalation_status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert row.escalation_score == Decimal("0.175000")
    assert row.escalation_status == "watch"
    assert row.manual_review_required is True
    assert row.reason_codes == ("high_contradiction", "manual_review_watch")


def test_payload_serializes_decimals_deterministically_and_validates_digest() -> None:
    report = _report((_signal(),))

    payload = report.payload
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    assert json.loads(encoded)["derived_validation_digest"] == report.derived_validation_digest
    assert payload["case_count"] == "1.000000"
    assert payload["rows"][0]["escalation_score"] == "0.815000"
    assert payload["generated_at"] == "2026-01-01T12:00:00+00:00"
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, generated_at=NOW + timedelta(seconds=1))


def test_inputs_require_decimals_frozen_dataclasses_and_hard_flags() -> None:
    signal = _signal()

    with pytest.raises(FrozenInstanceError):
        signal.case_key = "case_b"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadSignal(EvidenceConflictSignal):
            pass

    with pytest.raises(ValueError, match="Decimal"):
        EvidenceConflictSignal(
            case_key="case_a",
            evidence_ref_digest="a" * 64,
            counter_ref_digest="b" * 64,
            observed_at=NOW,
            deadline_at=None,
            contradiction_severity=1,  # type: ignore[arg-type]
            primary_authority_score=Decimal("0.100000"),
            counter_authority_score=Decimal("0.100000"),
            freshness_gap_seconds=Decimal("0.000000"),
            corroborating_group_count=Decimal("1.000000"),
            conflicting_group_count=Decimal("1.000000"),
            extraction_confidence=Decimal("0.900000"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceEvidenceConflictEscalationConfig(paper_only=False)

    report = _report((signal,))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_decimal_edges_reject_raw_bounds_and_canonicalize_signed_zero() -> None:
    with pytest.raises(ValueError, match="contradiction_severity"):
        _signal(contradiction_severity=Decimal("1.0000004"))

    with pytest.raises(ValueError, match="freshness_gap_seconds"):
        _signal(freshness_gap_seconds=Decimal("-0.0000004"))

    signal = _signal(
        contradiction_severity=Decimal("-0.000000"),
        primary_authority_score=Decimal("-0.000000"),
        counter_authority_score=Decimal("-0.000000"),
        freshness_gap_seconds=Decimal("-0.000000"),
        corroborating_group_count=Decimal("-0.000000"),
        conflicting_group_count=Decimal("-0.000000"),
        extraction_confidence=Decimal("1.000000"),
        deadline_at=None,
    )
    assert signal.contradiction_severity == Decimal("0.000000")
    assert not signal.contradiction_severity.is_signed()
    assert signal.freshness_gap_seconds == Decimal("0.000000")
    assert not signal.freshness_gap_seconds.is_signed()

    report = _report((signal,))
    payload = report.payload
    assert "-0.000000" not in json.dumps(payload, sort_keys=True)


def test_scoring_uses_fixed_local_decimal_context() -> None:
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN

        report = _report((_signal(),))

    row = report.rows[0]
    assert row.deadline_pressure == Decimal("0.750000")
    assert row.escalation_score == Decimal("0.815000")
    assert report.average_escalation_score == Decimal("0.815000")


def test_payload_revalidates_after_object_setattr_tampering() -> None:
    report = _report((_signal(),))
    object.__setattr__(report, "block_count", Decimal("0.000000"))

    with pytest.raises(ValueError, match="block_count|derived_validation_digest"):
        _ = report.payload


def test_count_fields_must_be_whole_decimals() -> None:
    with pytest.raises(ValueError, match="corroborating_group_count"):
        _signal(corroborating_group_count=Decimal("1.500000"))

    report = _report((_signal(),))
    values = api._report_values_without_digest(report)
    values["case_count"] = Decimal("1.500000")

    with pytest.raises(ValueError, match="case_count"):
        ResearchSourceEvidenceConflictEscalationReport(
            **values,
            derived_validation_digest=api._report_digest_from_values(values),
        )


def test_duplicate_case_digest_rows_have_complete_deterministic_tie_breaks() -> None:
    earlier = _signal(
        case_key="case_same",
        observed_at=NOW - timedelta(minutes=20),
        deadline_at=NOW + timedelta(minutes=30),
        contradiction_severity=Decimal("0.200000"),
        primary_authority_score=Decimal("0.300000"),
        counter_authority_score=Decimal("0.400000"),
        freshness_gap_seconds=Decimal("0.000000"),
        corroborating_group_count=Decimal("2.000000"),
        conflicting_group_count=Decimal("1.000000"),
        extraction_confidence=Decimal("0.900000"),
    )
    later = _signal(
        case_key="case_same",
        observed_at=NOW - timedelta(minutes=5),
        deadline_at=NOW + timedelta(minutes=45),
        contradiction_severity=Decimal("0.100000"),
        primary_authority_score=Decimal("0.200000"),
        counter_authority_score=Decimal("0.300000"),
        freshness_gap_seconds=Decimal("0.000000"),
        corroborating_group_count=Decimal("2.000000"),
        conflicting_group_count=Decimal("1.000000"),
        extraction_confidence=Decimal("0.950000"),
    )

    forward = _report((later, earlier))
    reversed_report = _report((earlier, later))

    assert tuple(row.observed_at for row in forward.rows) == (
        earlier.observed_at,
        later.observed_at,
    )
    assert forward.rows == reversed_report.rows
    assert forward.derived_validation_digest == reversed_report.derived_validation_digest


def test_public_payload_excludes_sensitive_surfaces_and_runtime_capabilities() -> None:
    report = _report((_signal(case_key="case-public-safe"),))
    payload = report.payload

    _assert_public_payload_is_safe(payload)
    for public_name in api.__all__:
        _assert_safe_fragment(public_name)

    for cls in (
        EvidenceConflictSignal,
        ResearchSourceEvidenceConflictEscalationConfig,
        ResearchSourceEvidenceConflictEscalationRow,
        ResearchSourceEvidenceConflictEscalationReport,
    ):
        for field in fields(cls):
            _assert_safe_fragment(field.name)

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
        "scrapy",
        "bs4",
    ):
        assert not hasattr(api, forbidden_name)

    for unsafe_key in (
        "candidate_a",
        "market_a",
        "slug_a",
        "question_a",
        "url_a",
        "dsn_a",
        "table_a",
        "token_a",
        "wallet_a",
        "order_a",
        "trade_a",
        "live_a",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            EvidenceConflictSignal(
                case_key=unsafe_key,
                evidence_ref_digest="a" * 64,
                counter_ref_digest="b" * 64,
                observed_at=NOW,
                deadline_at=None,
                contradiction_severity=Decimal("0.100000"),
                primary_authority_score=Decimal("0.100000"),
                counter_authority_score=Decimal("0.100000"),
                freshness_gap_seconds=Decimal("0.000000"),
                corroborating_group_count=Decimal("1.000000"),
                conflicting_group_count=Decimal("1.000000"),
                extraction_confidence=Decimal("0.900000"),
            )


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


def _assert_public_payload_is_safe(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_safe_fragment(key)
            _assert_public_payload_is_safe(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_public_payload_is_safe(item)
        return
    if isinstance(value, str):
        _assert_safe_fragment(value)


def _assert_safe_fragment(value: str) -> None:
    lowered = value.lower()
    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "http",
        "://",
    )
    assert not any(fragment in lowered for fragment in forbidden_fragments), value

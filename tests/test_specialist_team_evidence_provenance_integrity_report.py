from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.specialist_team_evidence_provenance_integrity_report as api
from polymarket_alpha_lab.specialist_team_evidence_provenance_integrity_report import (
    SpecialistTeamEvidenceProvenanceIntegrityEvidence,
    SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem,
    SpecialistTeamEvidenceProvenanceIntegrityReport,
    SpecialistTeamEvidenceProvenanceIntegrityRow,
    build_specialist_team_evidence_provenance_integrity_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _evidence(
    *,
    evidence_source_id: str = "source_a",
    source_family_id: str = "official",
    team_id: str = "team_alpha",
    official_anchor_flag: bool = True,
    captured_at: datetime = NOW - timedelta(hours=6),
    content_hash_present: bool = True,
    analyst_note_present: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SpecialistTeamEvidenceProvenanceIntegrityEvidence:
    return SpecialistTeamEvidenceProvenanceIntegrityEvidence(
        evidence_source_id=evidence_source_id,
        source_family_id=source_family_id,
        official_anchor_flag=official_anchor_flag,
        captured_at=captured_at,
        content_hash_present=content_hash_present,
        analyst_note_present=analyst_note_present,
        team_id=team_id,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    evidence: tuple[SpecialistTeamEvidenceProvenanceIntegrityEvidence, ...],
    *,
    public_payload: tuple[SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem, ...] = (),
) -> SpecialistTeamEvidenceProvenanceIntegrityReport:
    return build_specialist_team_evidence_provenance_integrity_report(
        evidence,
        generated_at=NOW,
        public_payload=public_payload,
    )


def test_complete_official_anchored_evidence_passes_with_archive_next_step() -> None:
    report = _report(
        (
            _evidence(evidence_source_id="source_a", source_family_id="official"),
            _evidence(
                evidence_source_id="source_b",
                source_family_id="primary",
                official_anchor_flag=False,
            ),
        ),
    )

    assert report.provenance_status == "pass"
    assert report.evidence_source_count == Decimal("2.000000")
    assert report.pass_count == Decimal("2.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.team_count == Decimal("1.000000")
    assert report.reason_codes == ("provenance_integrity_pass",)
    assert report.manual_next_step == "archive_evidence_provenance_snapshot"

    first_row = report.rows[0]
    assert first_row.evidence_source_id == "source_a"
    assert first_row.source_family_id == "official"
    assert first_row.team_id == "team_alpha"
    assert first_row.provenance_status == "pass"
    assert first_row.reason_codes == ("provenance_integrity_pass",)
    assert first_row.manual_next_step == "archive_evidence_provenance_snapshot"
    assert first_row.paper_only is True
    assert first_row.report_only is True
    assert first_row.readonly is True


def test_missing_hash_or_note_is_watch_and_manual_annotation_step() -> None:
    report = _report(
        (
            _evidence(
                evidence_source_id="source_missing_hash",
                content_hash_present=False,
            ),
            _evidence(
                evidence_source_id="source_missing_note",
                analyst_note_present=False,
            ),
        ),
    )

    assert report.provenance_status == "watch"
    assert report.watch_count == Decimal("2.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.reason_codes == (
        "missing_content_hash",
        "missing_analyst_note",
    )
    assert report.manual_next_step == "complete_evidence_hash_and_note_review"
    assert report.rows[0].provenance_status == "watch"
    assert report.rows[0].reason_codes == ("missing_content_hash",)
    assert report.rows[0].manual_next_step == "attach_content_hash"
    assert report.rows[1].reason_codes == ("missing_analyst_note",)
    assert report.rows[1].manual_next_step == "add_analyst_note"


def test_missing_identifier_family_team_or_timestamp_blocks_manual_source_review() -> None:
    report = _report(
        (
            _evidence(evidence_source_id="missing", source_family_id="missing"),
            _evidence(evidence_source_id="source_no_time", captured_at=None),
            _evidence(evidence_source_id="source_no_team", team_id="missing"),
        ),
    )

    assert report.provenance_status == "block"
    assert report.block_count == Decimal("3.000000")
    assert report.reason_codes == (
        "missing_evidence_source_id",
        "missing_source_family_id",
        "missing_captured_at",
        "missing_team_id",
        "missing_official_anchor",
    )
    assert report.manual_next_step == "manual_source_provenance_review"
    assert report.rows[0].provenance_status == "block"
    assert report.rows[0].reason_codes == (
        "missing_evidence_source_id",
        "missing_source_family_id",
        "missing_official_anchor",
    )
    assert report.rows[1].reason_codes == ("missing_captured_at",)
    assert report.rows[2].reason_codes == ("missing_team_id",)


def test_payload_serializes_decimal_datetimes_and_digest_without_decimal_objects() -> None:
    report = _report(
        (_evidence(),),
        public_payload=(
            SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem(
                "safe_summary",
                "source provenance reviewed",
            ),
        ),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["evidence_source_count"] == "1.000000"
    assert payload["rows"][0]["captured_at"] == "2025-12-31T18:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_dataclasses_are_frozen_decimal_strict_and_hard_flagged() -> None:
    report = _report((_evidence(),))

    with pytest.raises(FrozenInstanceError):
        report.provenance_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadEvidence(SpecialistTeamEvidenceProvenanceIntegrityEvidence):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        _evidence(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="Decimal"):
        replace(report, evidence_source_count=1)  # type: ignore[arg-type]


def test_input_validation_rejects_unsafe_surfaces_duplicates_and_future_capture() -> None:
    with pytest.raises(ValueError, match="sequence"):
        build_specialist_team_evidence_provenance_integrity_report(
            "not evidence",  # type: ignore[arg-type]
            generated_at=NOW,
        )

    with pytest.raises(ValueError, match="duplicate"):
        _report(
            (
                _evidence(evidence_source_id="source_dup"),
                _evidence(evidence_source_id="source_dup"),
            ),
        )

    with pytest.raises(ValueError, match="after generated_at"):
        _report((_evidence(captured_at=NOW + timedelta(seconds=1)),))

    for term in ("live", "auth", "wallet", "order", "trade"):
        with pytest.raises(ValueError, match="unsafe public"):
            SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem(
                "safe_key",
                f"{term} surface",
            )
        with pytest.raises(ValueError, match="unsafe public"):
            _evidence(evidence_source_id=f"{term}_source")

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in ("auth", "wallet", "order", "live"))

    for cls in (
        SpecialistTeamEvidenceProvenanceIntegrityEvidence,
        SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem,
        SpecialistTeamEvidenceProvenanceIntegrityRow,
        SpecialistTeamEvidenceProvenanceIntegrityReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in ("auth", "wallet", "order", "live"))

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


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report((_evidence(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem(
                    "safe_summary",
                    "changed summary",
                ),
            ),
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

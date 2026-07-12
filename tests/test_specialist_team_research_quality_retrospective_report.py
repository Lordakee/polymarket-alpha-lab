from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.specialist_team_research_quality_retrospective_report import (
    CALIBRATION_ISSUES_REASON,
    MISSING_RETROSPECTIVE_NOTES_REASON,
    MISSED_RESOLUTIONS_REASON,
    NO_REVIEWED_MARKETS_REASON,
    READY_REASON,
    SOURCE_QUALITY_ISSUES_REASON,
    SpecialistTeamResearchQualityRetrospectiveReport,
    build_specialist_team_research_quality_retrospective_report,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("payload_digest")
    encoded = json.dumps(
        unsigned_payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def ready_report() -> SpecialistTeamResearchQualityRetrospectiveReport:
    return build_specialist_team_research_quality_retrospective_report(
        reviewed_market_count=d("12.000000"),
        missed_resolution_count=d("0.000000"),
        source_quality_issue_count=d("0.000000"),
        calibration_issue_count=d("0.000000"),
        retrospective_note_count=d("4.000000"),
    )


def test_ready_retrospective_report_exposes_public_payload_and_digest() -> None:
    report = ready_report()

    assert isinstance(report, SpecialistTeamResearchQualityRetrospectiveReport)
    assert is_dataclass(report)
    assert report.retrospective_status == "ready"
    assert report.reason_codes == (READY_REASON,)
    assert report.manual_next_step == (
        "Continue the paper-only research quality retrospective with the prepared "
        "evidence packet."
    )
    assert report.reviewed_market_count == d("12.000000")
    assert report.missed_resolution_count == d("0.000000")
    assert report.source_quality_issue_count == d("0.000000")
    assert report.calibration_issue_count == d("0.000000")
    assert report.retrospective_note_count == d("4.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == {
        "retrospective_status": "ready",
        "reason_codes": [READY_REASON],
        "manual_next_step": (
            "Continue the paper-only research quality retrospective with the prepared "
            "evidence packet."
        ),
        "reviewed_market_count": "12.000000",
        "missed_resolution_count": "0.000000",
        "source_quality_issue_count": "0.000000",
        "calibration_issue_count": "0.000000",
        "retrospective_note_count": "4.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": report.payload_digest,
    }
    assert report.payload_digest == canonical_digest(payload)


def test_retrospective_status_blocks_empty_review_inputs_and_surfaces_manual_step() -> None:
    report = build_specialist_team_research_quality_retrospective_report(
        reviewed_market_count=d("0.000000"),
        missed_resolution_count=d("0.000000"),
        source_quality_issue_count=d("0.000000"),
        calibration_issue_count=d("0.000000"),
        retrospective_note_count=d("0.000000"),
    )

    assert report.retrospective_status == "blocked"
    assert report.reason_codes == (
        NO_REVIEWED_MARKETS_REASON,
        MISSING_RETROSPECTIVE_NOTES_REASON,
    )
    assert report.manual_next_step == (
        "Review at least one resolved market before preparing the retrospective."
    )
    assert report.public_payload["payload_digest"] == report.payload_digest


def test_retrospective_status_requires_manual_review_for_quality_gaps() -> None:
    report = build_specialist_team_research_quality_retrospective_report(
        reviewed_market_count=d("7.000000"),
        missed_resolution_count=d("2.000000"),
        source_quality_issue_count=d("1.000000"),
        calibration_issue_count=d("3.000000"),
        retrospective_note_count=d("1.000000"),
    )

    assert report.retrospective_status == "needs_manual_review"
    assert report.reason_codes == (
        MISSED_RESOLUTIONS_REASON,
        SOURCE_QUALITY_ISSUES_REASON,
        CALIBRATION_ISSUES_REASON,
    )
    assert report.manual_next_step == (
        "Manually reconcile missed resolutions before marking the retrospective ready."
    )
    assert report.public_payload["reason_codes"] == list(report.reason_codes)


def test_retrospective_report_rejects_non_decimal_counts_flags_and_mutation() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        build_specialist_team_research_quality_retrospective_report(
            reviewed_market_count=1,  # type: ignore[arg-type]
            missed_resolution_count=d("0.000000"),
            source_quality_issue_count=d("0.000000"),
            calibration_issue_count=d("0.000000"),
            retrospective_note_count=d("1.000000"),
        )

    with pytest.raises(ValueError, match="whole"):
        build_specialist_team_research_quality_retrospective_report(
            reviewed_market_count=d("1.500000"),
            missed_resolution_count=d("0.000000"),
            source_quality_issue_count=d("0.000000"),
            calibration_issue_count=d("0.000000"),
            retrospective_note_count=d("1.000000"),
        )

    with pytest.raises(ValueError, match="nonnegative"):
        build_specialist_team_research_quality_retrospective_report(
            reviewed_market_count=d("1.000000"),
            missed_resolution_count=d("-1.000000"),
            source_quality_issue_count=d("0.000000"),
            calibration_issue_count=d("0.000000"),
            retrospective_note_count=d("1.000000"),
        )

    report = ready_report()
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="not-the-digest")
    with pytest.raises(FrozenInstanceError):
        report.retrospective_status = "blocked"  # type: ignore[misc]
    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReport(SpecialistTeamResearchQualityRetrospectiveReport):
            pass


def test_retrospective_module_is_report_only_and_has_no_blocked_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/specialist_team_research_quality_retrospective_report.py",
    ).read_text()
    lowered = source.lower()

    for blocked_fragment in (
        "psycopg",
        "supabase",
        "sqlite",
        "requests",
        "urllib",
        "socket",
        "open(",
        "write_text",
        "append",
        "live",
        "auth",
        "wallet",
        "signing",
        "execution",
    ):
        assert blocked_fragment not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    assert imported_modules <= {"dataclasses", "decimal", "hashlib", "json", "typing"}

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.specialist_team_category_playbook_readiness_report import (
    SpecialistTeamCategoryPlaybookReadinessInput,
    SpecialistTeamCategoryPlaybookReadinessReport,
    build_specialist_team_category_playbook_readiness_report,
    specialist_team_category_playbook_readiness_payload,
)


def _ready_input() -> SpecialistTeamCategoryPlaybookReadinessInput:
    return SpecialistTeamCategoryPlaybookReadinessInput(
        category_id="category-politics",
        playbook_exists=True,
        settled_example_count=Decimal("8"),
        source_family_coverage_count=Decimal("3"),
        calibration_note_count=Decimal("2"),
        last_updated_age_hours=Decimal("12.000000"),
    )


def test_builds_ready_report_payload_and_digest() -> None:
    report = build_specialist_team_category_playbook_readiness_report(_ready_input())

    assert report.playbook_status == "ready"
    assert report.reason_codes == (
        "category_playbook_exists",
        "settled_examples_ready",
        "source_family_coverage_ready",
        "calibration_notes_ready",
        "playbook_recent",
        "category_playbook_ready",
    )
    assert report.manual_next_step == "reuse_category_playbook_for_paper_research"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.playbook_status = "blocked"  # type: ignore[misc]

    payload = specialist_team_category_playbook_readiness_payload(report)

    assert payload == report.public_payload
    assert payload["category_id"] == "category-politics"
    assert payload["playbook_status"] == "ready"
    assert payload["settled_example_count"] == "8"
    assert payload["last_updated_age_hours"] == "12.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.payload_digest) == 64


def test_blocks_missing_playbook_and_incomplete_evidence() -> None:
    report = build_specialist_team_category_playbook_readiness_report(
        SpecialistTeamCategoryPlaybookReadinessInput(
            category_id="category-sports",
            playbook_exists=False,
            settled_example_count=Decimal("0"),
            source_family_coverage_count=Decimal("1"),
            calibration_note_count=Decimal("0"),
            last_updated_age_hours=Decimal("240.000000"),
        ),
    )

    assert report.playbook_status == "blocked"
    assert report.reason_codes == (
        "category_playbook_missing",
        "settled_examples_missing",
        "source_family_coverage_thin",
        "calibration_notes_missing",
        "playbook_stale",
        "category_playbook_blocked",
    )
    assert report.manual_next_step == "create_category_playbook_before_paper_research"


def test_marks_watch_when_evidence_is_thin_but_not_blocked() -> None:
    report = build_specialist_team_category_playbook_readiness_report(
        SpecialistTeamCategoryPlaybookReadinessInput(
            category_id="category-elections",
            playbook_exists=True,
            settled_example_count=Decimal("3"),
            source_family_coverage_count=Decimal("2"),
            calibration_note_count=Decimal("1"),
            last_updated_age_hours=Decimal("72.000000"),
        ),
    )

    assert report.playbook_status == "watch"
    assert report.reason_codes == (
        "category_playbook_exists",
        "settled_examples_thin",
        "source_family_coverage_partial",
        "calibration_notes_ready",
        "playbook_recency_watch",
        "category_playbook_watch",
    )
    assert report.manual_next_step == "refresh_category_playbook_evidence_before_reuse"


def test_rejects_non_decimal_inputs_non_readonly_flags_and_subclasses() -> None:
    with pytest.raises(ValueError, match="settled_example_count must be exactly Decimal"):
        SpecialistTeamCategoryPlaybookReadinessInput(
            category_id="category-politics",
            playbook_exists=True,
            settled_example_count=8,  # type: ignore[arg-type]
            source_family_coverage_count=Decimal("3"),
            calibration_note_count=Decimal("2"),
            last_updated_age_hours=Decimal("12.000000"),
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        SpecialistTeamCategoryPlaybookReadinessInput(
            category_id="category-politics",
            playbook_exists=True,
            settled_example_count=Decimal("8"),
            source_family_coverage_count=Decimal("3"),
            calibration_note_count=Decimal("2"),
            last_updated_age_hours=Decimal("12.000000"),
            readonly=False,
        )

    with pytest.raises(TypeError):

        class ReadinessInputSubclass(SpecialistTeamCategoryPlaybookReadinessInput):
            pass

    with pytest.raises(TypeError):

        class ReadinessReportSubclass(SpecialistTeamCategoryPlaybookReadinessReport):
            pass


def test_rejects_execution_surface_text_in_public_fields() -> None:
    with pytest.raises(ValueError, match="unsafe public payload"):
        SpecialistTeamCategoryPlaybookReadinessInput(
            category_id="wal" "let-category",
            playbook_exists=True,
            settled_example_count=Decimal("8"),
            source_family_coverage_count=Decimal("3"),
            calibration_note_count=Decimal("2"),
            last_updated_age_hours=Decimal("12.000000"),
        )

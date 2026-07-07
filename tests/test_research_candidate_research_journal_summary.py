from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from json import dumps

import pytest

import polymarket_alpha_lab.research_candidate_research_journal_summary as summary_module
from polymarket_alpha_lab.research_candidate_research_journal_summary import (
    ResearchCandidateResearchJournalSummaryConfig,
    ResearchCandidateResearchJournalSummaryInput,
    ResearchCandidateResearchJournalSummaryResult,
    research_candidate_research_journal_summary_payload,
    summarize_research_candidate_research_journal,
)


ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def journal(
    **overrides: object,
) -> ResearchCandidateResearchJournalSummaryInput:
    values = {
        "research_ref": "research-2026-07-07-a",
        "evidence_added_count": d("3"),
        "evidence_revised_count": d("1"),
        "evidence_retired_count": d("0"),
        "evidence_confidence_delta": d("0.500000"),
        "team_view_change_count": d("1"),
        "team_alignment_delta": d("0.400000"),
        "unresolved_conflict_count": d("0"),
        "resolved_conflict_count": d("2"),
        "refresh_record_count": d("2"),
        "stale_refresh_count": d("0"),
        "open_retro_todo_count": d("0"),
        "completed_retro_todo_count": d("2"),
    }
    values.update(overrides)
    return ResearchCandidateResearchJournalSummaryInput(**values)


def summarize(
    item: ResearchCandidateResearchJournalSummaryInput,
    *,
    cfg: ResearchCandidateResearchJournalSummaryConfig | None = None,
) -> ResearchCandidateResearchJournalSummaryResult:
    return summarize_research_candidate_research_journal(
        item,
        config=cfg or ResearchCandidateResearchJournalSummaryConfig(),
    )


def test_research_journal_summary_passes_complete_report_journal() -> None:
    result = summarize(journal())

    assert result == ResearchCandidateResearchJournalSummaryResult(
        config_version="research-journal-summary-v1",
        research_ref="research-2026-07-07-a",
        evidence_added_count=d("3"),
        evidence_revised_count=d("1"),
        evidence_retired_count=d("0"),
        evidence_confidence_delta=d("0.500000"),
        team_view_change_count=d("1"),
        team_alignment_delta=d("0.400000"),
        unresolved_conflict_count=d("0"),
        resolved_conflict_count=d("2"),
        refresh_record_count=d("2"),
        stale_refresh_count=d("0"),
        open_retro_todo_count=d("0"),
        completed_retro_todo_count=d("2"),
        evidence_change_score=d("0.900000"),
        team_view_score=d("0.700000"),
        conflict_handling_score=d("1.000000"),
        refresh_record_score=d("1.000000"),
        retrospective_todo_score=d("1.000000"),
        journal_summary_score=d("0.910000"),
        summary_status="pass",
        follow_up_required=False,
        reason_codes=("journal_summary_passed",),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_research_journal_summary_watches_mixed_updates_and_open_work() -> None:
    result = summarize(
        journal(
            evidence_added_count=d("1"),
            evidence_revised_count=d("0"),
            evidence_retired_count=d("1"),
            evidence_confidence_delta=d("-0.200000"),
            team_view_change_count=d("3"),
            team_alignment_delta=d("-0.100000"),
            resolved_conflict_count=d("1"),
            refresh_record_count=d("2"),
            stale_refresh_count=d("1"),
            open_retro_todo_count=d("2"),
            completed_retro_todo_count=d("1"),
        ),
    )

    assert result.evidence_change_score == d("0.460000")
    assert result.team_view_score == d("0.450000")
    assert result.refresh_record_score == d("0.500000")
    assert result.retrospective_todo_score == d("0.333333")
    assert result.journal_summary_score == d("0.553000")
    assert result.summary_status == "watch"
    assert result.follow_up_required is True
    assert result.reason_codes == (
        "evidence_confidence_weakened",
        "evidence_change_score_low",
        "team_view_alignment_weakened",
        "team_view_score_low",
        "stale_refresh_records_present",
        "retrospective_todos_open",
        "journal_summary_watch_score",
    )


def test_research_journal_summary_blocks_unresolved_conflicts() -> None:
    result = summarize(
        journal(
            unresolved_conflict_count=d("1"),
            resolved_conflict_count=d("1"),
        ),
    )

    assert result.conflict_handling_score == d("0.500000")
    assert result.journal_summary_score == d("0.810000")
    assert result.summary_status == "block"
    assert result.follow_up_required is True
    assert result.reason_codes == ("unresolved_conflicts_present",)


def test_research_journal_summary_payload_is_json_ready_and_sanitized() -> None:
    result = summarize(journal())
    payload = research_candidate_research_journal_summary_payload(result)

    dumps(payload, sort_keys=True)
    assert result.payload == payload
    assert payload["research_ref"] == "research-2026-07-07-a"
    assert payload["evidence_added_count"] == "3"
    assert payload["evidence_confidence_delta"] == "0.500000"
    assert payload["journal_summary_score"] == "0.910000"
    assert payload["summary_status"] == "pass"
    assert payload["follow_up_required"] is False
    assert payload["reason_codes"] == ["journal_summary_passed"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_or_int(payload)
    _assert_public_payload_safe(payload)


def test_research_journal_summary_validates_types_ranges_counts_and_flags() -> None:
    result = summarize(journal())

    with pytest.raises(FrozenInstanceError):
        result.summary_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="evidence_added_count must be a Decimal"):
        journal(evidence_added_count=3)
    with pytest.raises(ValueError, match="evidence_confidence_delta must be a Decimal"):
        journal(evidence_confidence_delta=0.1)
    with pytest.raises(ValueError, match="team_alignment_delta must be a Decimal"):
        journal(team_alignment_delta=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="evidence_revised_count must be a whole"):
        journal(evidence_revised_count=d("1.500000"))
    with pytest.raises(ValueError, match="team_alignment_delta must be between"):
        journal(team_alignment_delta=d("1.000001"))
    with pytest.raises(ValueError, match="stale_refresh_count must not exceed"):
        journal(refresh_record_count=d("1"), stale_refresh_count=d("2"))
    with pytest.raises(ValueError, match="research_ref must not expose"):
        journal(research_ref="raw-candidate-42")
    with pytest.raises(ValueError, match="paper_only must be True"):
        journal(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        ResearchCandidateResearchJournalSummaryConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_research_journal_summary_rejects_manual_inconsistent_outputs() -> None:
    valid = summarize(journal())

    with pytest.raises(ValueError, match="journal_summary_score must match"):
        replace(valid, journal_summary_score=ZERO)
    with pytest.raises(ValueError, match="summary_status must match"):
        replace(
            valid,
            summary_status="watch",
            follow_up_required=True,
            reason_codes=("journal_summary_watch_score",),
        )
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(valid, reason_codes=("evidence_change_missing",))
    with pytest.raises(ValueError, match="follow_up_required must match"):
        replace(valid, follow_up_required=True)


def test_research_journal_summary_accepts_only_exact_input_and_config_types() -> None:
    with pytest.raises(
        ValueError,
        match="journal must be a ResearchCandidateResearchJournalSummaryInput",
    ):
        summarize_research_candidate_research_journal(object())  # type: ignore[arg-type]
    with pytest.raises(
        ValueError,
        match="config must be a ResearchCandidateResearchJournalSummaryConfig",
    ):
        summarize_research_candidate_research_journal(
            journal(),
            config=object(),  # type: ignore[arg-type]
        )


def test_research_journal_summary_public_numeric_annotations_are_decimal() -> None:
    decimal_fields = {
        "ResearchCandidateResearchJournalSummaryConfig": {
            "minimum_evidence_change_score",
            "minimum_team_view_score",
            "minimum_refresh_record_count",
            "maximum_unresolved_conflict_count",
            "maximum_stale_refresh_count",
            "maximum_open_retro_todo_count",
            "pass_score_threshold",
            "watch_score_threshold",
            "evidence_change_weight",
            "team_view_weight",
            "conflict_handling_weight",
            "refresh_record_weight",
            "retrospective_todo_weight",
        },
        "ResearchCandidateResearchJournalSummaryInput": {
            "evidence_added_count",
            "evidence_revised_count",
            "evidence_retired_count",
            "evidence_confidence_delta",
            "team_view_change_count",
            "team_alignment_delta",
            "unresolved_conflict_count",
            "resolved_conflict_count",
            "refresh_record_count",
            "stale_refresh_count",
            "open_retro_todo_count",
            "completed_retro_todo_count",
        },
        "ResearchCandidateResearchJournalSummaryResult": {
            "evidence_added_count",
            "evidence_revised_count",
            "evidence_retired_count",
            "evidence_confidence_delta",
            "team_view_change_count",
            "team_alignment_delta",
            "unresolved_conflict_count",
            "resolved_conflict_count",
            "refresh_record_count",
            "stale_refresh_count",
            "open_retro_todo_count",
            "completed_retro_todo_count",
            "evidence_change_score",
            "team_view_score",
            "conflict_handling_score",
            "refresh_record_score",
            "retrospective_todo_score",
            "journal_summary_score",
        },
    }

    for class_name, field_names in decimal_fields.items():
        annotations = getattr(summary_module, class_name).__annotations__
        for field_name in field_names:
            assert annotations[field_name] == "Decimal"


def test_research_journal_summary_has_no_live_side_effect_surface() -> None:
    source = inspect.getsource(summary_module)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "urllib",
        "web3",
    }
    forbidden_calls = {"open", "connect", "request", "urlopen"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls

    lowered = source.lower()
    for forbidden in (
        "place_order",
        "wallet",
        "private_key",
        "auth_token",
        "live trading",
    ):
        assert forbidden not in lowered


def _assert_no_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected concrete numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_float_or_int(item)


def _assert_public_payload_safe(value: object) -> None:
    forbidden_fragments = {
        "raw",
        "candidate",
        "market",
        "source",
        "url",
        "uri",
        "dsn",
        "table",
        "token",
        "text",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in forbidden_fragments)
            _assert_public_payload_safe(item)
    elif isinstance(value, list):
        for item in value:
            _assert_public_payload_safe(item)
    elif isinstance(value, str):
        lowered_value = value.lower()
        assert "://" not in lowered_value
        assert "raw_" not in lowered_value
        assert "candidate_" not in lowered_value
        assert "market_" not in lowered_value
        assert "dsn" not in lowered_value
        assert "token" not in lowered_value

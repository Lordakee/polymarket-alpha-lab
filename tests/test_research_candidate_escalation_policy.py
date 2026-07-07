from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_candidate_escalation_policy import (
    ResearchCandidateEscalationConfig,
    ResearchCandidateEscalationReasonCodeCount,
    ResearchCandidateEscalationReport,
    ResearchCandidateEscalationRow,
    ResearchCandidateObservation,
    build_research_candidate_escalation_report,
    research_candidate_escalation_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchCandidateEscalationConfig:
    values = {
        "config_version": "research-candidate-escalation-policy-v0",
        "pass_min_evidence_support_score": d("0.750000"),
        "pass_min_quality_support_score": d("0.700000"),
        "continuation_min_evidence_support_score": d("0.300000"),
        "continuation_min_quality_support_score": d("0.300000"),
        "team_review_conflict_signal_score": d("0.250000"),
        "expert_review_conflict_signal_score": d("0.550000"),
        "watch_sensitivity_signal_score": d("0.300000"),
        "block_sensitivity_signal_score": d("0.650000"),
        "max_pass_unresolved_issue_count": d("0"),
        "max_watch_unresolved_issue_count": d("2"),
    }
    values.update(overrides)
    return ResearchCandidateEscalationConfig(**values)


def observation(
    raw_candidate_id: str,
    *,
    raw_market_ref: str = "raw-market-ref",
    raw_source_ref: str | None = "raw-source-ref",
    observed_at: datetime | None = None,
    review_stage: str = "ordinary_observation",
    evidence_support_score: Decimal = d("0.900000"),
    quality_support_score: Decimal = d("0.900000"),
    conflict_signal_score: Decimal = d("0.000000"),
    sensitivity_signal_score: Decimal = d("0.000000"),
    unresolved_issue_count: Decimal = d("0"),
    team_review_count: Decimal = d("0"),
    expert_review_count: Decimal = d("0"),
    pause_requested: bool = False,
) -> ResearchCandidateObservation:
    return ResearchCandidateObservation(
        raw_candidate_id=raw_candidate_id,
        raw_market_ref=raw_market_ref,
        raw_source_ref=raw_source_ref,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=5)
        ),
        review_stage=review_stage,
        evidence_support_score=evidence_support_score,
        quality_support_score=quality_support_score,
        conflict_signal_score=conflict_signal_score,
        sensitivity_signal_score=sensitivity_signal_score,
        unresolved_issue_count=unresolved_issue_count,
        team_review_count=team_review_count,
        expert_review_count=expert_review_count,
        pause_requested=pause_requested,
    )


def report(
    rows: tuple[ResearchCandidateObservation, ...],
    *,
    cfg: ResearchCandidateEscalationConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchCandidateEscalationReport:
    return build_research_candidate_escalation_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_with_non_sensitive_reason() -> None:
    escalation_report = report(())

    assert type(escalation_report) is ResearchCandidateEscalationReport
    assert escalation_report.generated_at == GENERATED_AT
    assert escalation_report.config_version == "research-candidate-escalation-policy-v0"
    assert escalation_report.input_count == d("0")
    assert escalation_report.row_count == d("0")
    assert escalation_report.pass_count == d("0")
    assert escalation_report.watch_count == d("0")
    assert escalation_report.block_count == d("0")
    assert escalation_report.status == "block"
    assert escalation_report.next_review_step == "collect_candidate_observations"
    assert escalation_report.rows == ()
    assert escalation_report.reason_codes == ("no_candidate_events",)
    assert escalation_report.reason_code_counts == (
        ResearchCandidateEscalationReasonCodeCount(
            reason_code="no_candidate_events",
            count=d("1"),
        ),
    )
    assert escalation_report.paper_only is True
    assert escalation_report.report_only is True
    assert escalation_report.readonly is True


def test_pass_watch_block_rows_are_deterministic_and_payload_is_sanitized() -> None:
    escalation_report = report(
        (
            observation(
                "z-pass-secret-id",
                raw_market_ref="raw-market-election-secret",
                raw_source_ref="https://private.example/source?token=alpha",
            ),
            observation(
                "a-team-secret-id",
                evidence_support_score=d("0.600000"),
                conflict_signal_score=d("0.300000"),
                unresolved_issue_count=d("1"),
            ),
            observation(
                "m-expert-secret-id",
                conflict_signal_score=d("0.600000"),
                sensitivity_signal_score=d("0.350000"),
            ),
            observation(
                "p-pause-secret-id",
                raw_market_ref="dsn://private/table/events",
                raw_source_ref="raw text token beta source",
                pause_requested=True,
            ),
        ),
    )

    assert escalation_report.status == "block"
    assert escalation_report.input_count == d("4")
    assert escalation_report.row_count == d("4")
    assert escalation_report.pass_count == d("1")
    assert escalation_report.watch_count == d("2")
    assert escalation_report.block_count == d("1")
    assert escalation_report.next_review_step == "pause_research_until_resolved"
    assert tuple(row.redacted_candidate_ref for row in escalation_report.rows) == (
        "candidate-001",
        "candidate-002",
        "candidate-003",
        "candidate-004",
    )
    assert tuple(row.status for row in escalation_report.rows) == (
        "watch",
        "watch",
        "block",
        "pass",
    )
    assert tuple(row.escalation_stage for row in escalation_report.rows) == (
        "team_review",
        "expert_review",
        "pause_research",
        "ordinary_observation",
    )
    assert escalation_report.rows[0].reason_codes == (
        "candidate_escalation_watch",
        "team_review_required",
        "evidence_support_below_pass",
        "open_review_issue",
        "conflict_signal_present",
    )
    assert escalation_report.rows[1].reason_codes == (
        "candidate_escalation_watch",
        "expert_review_required",
        "material_conflict_signal",
        "sensitive_signal_present",
    )
    assert escalation_report.rows[2].reason_codes == (
        "candidate_escalation_block",
        "research_paused",
        "research_pause_requested",
    )
    assert escalation_report.rows[3].reason_codes == (
        "candidate_escalation_pass",
        "routine_observation_clear",
    )

    payload = research_candidate_escalation_report_payload(escalation_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["evidence_support_score"] == "0.600000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    for forbidden in (
        "z-pass-secret-id",
        "a-team-secret-id",
        "m-expert-secret-id",
        "p-pause-secret-id",
        "raw-market-election-secret",
        "https://private.example",
        "dsn://private/table/events",
        "raw text token beta source",
        "buy",
        "sell",
        "position",
        "recommend",
    ):
        assert forbidden not in encoded.lower()


def test_validation_rejects_non_decimal_values_bad_enums_future_times_and_flags() -> None:
    with pytest.raises(ValueError, match="pass_min_evidence_support_score"):
        config(pass_min_evidence_support_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="team_review_conflict_signal_score"):
        config(team_review_conflict_signal_score=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation("candidate-a"),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation("candidate-a"),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="raw_candidate_id"):
        observation(" candidate-a")
    with pytest.raises(ValueError, match="review_stage"):
        observation("candidate-a", review_stage="desk_review")
    with pytest.raises(ValueError, match="observed_at"):
        observation("candidate-a", observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation("candidate-a", observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="evidence_support_score"):
        observation("candidate-a", evidence_support_score=Decimal("1.1"))
    with pytest.raises(ValueError, match="unresolved_issue_count"):
        observation("candidate-a", unresolved_issue_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="pause_requested"):
        replace(observation("candidate-a"), pause_requested=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation("candidate-a"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    escalation_report = report((observation("candidate-a"),))
    row = escalation_report.rows[0]

    assert type(row) is ResearchCandidateEscalationRow
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        escalation_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="pass_count"):
        replace(escalation_report, pass_count=d("0"))
    with pytest.raises(ValueError, match="rows"):
        replace(escalation_report, rows=(row, row))


def test_payload_rejects_manual_sensitive_public_strings_and_module_has_no_io_surface() -> None:
    escalation_report = report((observation("candidate-a"),))

    sensitive_row = replace(
        escalation_report.rows[0],
        redacted_candidate_ref="https://private.example/raw-market-token",
    )
    with pytest.raises(ValueError, match="public payload"):
        research_candidate_escalation_report_payload(
            replace(escalation_report, rows=(sensitive_row,)),
        )

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_candidate_escalation_policy.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "execute(",
        "commit(",
        "insert ",
        "update ",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for key, item in value.items():
            values.append(key)
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)

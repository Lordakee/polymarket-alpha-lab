from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_human_approval_gate_report import (
    ResearchHumanApprovalGateConfig,
    ResearchHumanApprovalGateInput,
    ResearchHumanApprovalGateReasonCodeCount,
    ResearchHumanApprovalGateReport,
    ResearchHumanApprovalGateRow,
    build_research_human_approval_gate_report,
    research_human_approval_gate_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedCandidateShape:
    candidate_id: str
    evidence_count: Decimal
    primary_source_count: Decimal
    evidence_quality_score: Decimal
    estimated_cost_amount: Decimal
    cost_uncertainty_score: Decimal
    settlement_clarity_score: Decimal
    settlement_window_hours: Decimal
    team_agreement_ratio: Decimal
    team_disagreement_count: Decimal
    safety_boundary_flags: tuple[str, ...]
    public_notes: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def _chars(*values: int) -> str:
    return "".join(chr(value) for value in values)


def config(**overrides: object) -> ResearchHumanApprovalGateConfig:
    values = {
        "config_version": "research-human-approval-gate-report-v0",
        "min_evidence_count": d("2"),
        "min_primary_source_count": d("1"),
        "pass_evidence_quality_score": d("0.700000"),
        "watch_evidence_quality_score": d("0.500000"),
        "watch_cost_amount": d("0.030000"),
        "block_cost_amount": d("0.100000"),
        "watch_cost_uncertainty_score": d("0.400000"),
        "block_cost_uncertainty_score": d("0.750000"),
        "pass_settlement_clarity_score": d("0.700000"),
        "block_settlement_clarity_score": d("0.400000"),
        "pass_settlement_window_hours": d("168"),
        "block_settlement_window_hours": d("720"),
        "pass_team_agreement_ratio": d("0.666667"),
        "block_team_agreement_ratio": d("0.500000"),
        "block_team_disagreement_count": d("2"),
    }
    values.update(overrides)
    return ResearchHumanApprovalGateConfig(**values)


def candidate(
    candidate_id: str = "candidate-alpha",
    *,
    evidence_count: Decimal = d("3"),
    primary_source_count: Decimal = d("2"),
    evidence_quality_score: Decimal = d("0.820000"),
    estimated_cost_amount: Decimal = d("0.010000"),
    cost_uncertainty_score: Decimal = d("0.100000"),
    settlement_clarity_score: Decimal = d("0.900000"),
    settlement_window_hours: Decimal = d("48"),
    team_agreement_ratio: Decimal = d("0.800000"),
    team_disagreement_count: Decimal = d("0"),
    safety_boundary_flags: tuple[str, ...] = (),
    public_notes: str = "evidence reviewed",
    reason_codes: tuple[str, ...] = (),
) -> ResearchHumanApprovalGateInput:
    return ResearchHumanApprovalGateInput(
        candidate_id=candidate_id,
        evidence_count=evidence_count,
        primary_source_count=primary_source_count,
        evidence_quality_score=evidence_quality_score,
        estimated_cost_amount=estimated_cost_amount,
        cost_uncertainty_score=cost_uncertainty_score,
        settlement_clarity_score=settlement_clarity_score,
        settlement_window_hours=settlement_window_hours,
        team_agreement_ratio=team_agreement_ratio,
        team_disagreement_count=team_disagreement_count,
        safety_boundary_flags=safety_boundary_flags,
        public_notes=public_notes,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchHumanApprovalGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchHumanApprovalGateReport:
    return build_research_human_approval_gate_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_gate_report() -> None:
    gate_report = report(())

    assert type(gate_report) is ResearchHumanApprovalGateReport
    assert gate_report.generated_at == GENERATED_AT
    assert gate_report.config_version == "research-human-approval-gate-report-v0"
    assert gate_report.candidate_count == d("0")
    assert gate_report.pass_count == d("0")
    assert gate_report.watch_count == d("0")
    assert gate_report.block_count == d("0")
    assert gate_report.gate_status == "block"
    assert gate_report.rows == ()
    assert gate_report.reason_codes == ("no_human_approval_gate_candidates",)
    assert gate_report.reason_code_counts == (
        ResearchHumanApprovalGateReasonCodeCount(
            reason_code="no_human_approval_gate_candidates",
            count=d("1"),
        ),
    )
    assert gate_report.paper_only is True
    assert gate_report.report_only is True
    assert gate_report.readonly is True


def test_complete_evidence_low_cost_clear_settlement_and_consensus_pass() -> None:
    gate_report = report(
        (
            candidate(
                "candidate-pass",
                reason_codes=("manual_reviewed",),
            ),
        ),
    )

    row = gate_report.rows[0]
    assert gate_report.gate_status == "pass"
    assert gate_report.candidate_count == d("1")
    assert gate_report.pass_count == d("1")
    assert gate_report.watch_count == d("0")
    assert gate_report.block_count == d("0")
    assert gate_report.reason_codes == ("human_approval_gate_pass",)
    assert type(row) is ResearchHumanApprovalGateRow
    assert row.candidate_id == "candidate-pass"
    assert row.evidence_status == "pass"
    assert row.cost_status == "pass"
    assert row.settlement_status == "pass"
    assert row.consensus_status == "pass"
    assert row.safety_status == "pass"
    assert row.gate_status == "pass"
    assert row.reason_codes == (
        "consensus_pass",
        "cost_pass",
        "evidence_pass",
        "human_approval_gate_pass",
        "input_manual_reviewed",
        "safety_boundary_pass",
        "settlement_pass",
    )


def test_cost_settlement_and_consensus_gaps_create_watch_report() -> None:
    gate_report = report(
        (
            candidate(
                "candidate-watch",
                evidence_quality_score=d("0.650000"),
                estimated_cost_amount=d("0.050000"),
                cost_uncertainty_score=d("0.450000"),
                settlement_clarity_score=d("0.600000"),
                settlement_window_hours=d("240"),
                team_agreement_ratio=d("0.600000"),
                team_disagreement_count=d("1"),
            ),
        ),
    )

    row = gate_report.rows[0]
    assert gate_report.gate_status == "watch"
    assert gate_report.watch_count == d("1")
    assert row.evidence_status == "watch"
    assert row.cost_status == "watch"
    assert row.settlement_status == "watch"
    assert row.consensus_status == "watch"
    assert row.safety_status == "pass"
    assert row.gate_status == "watch"
    assert row.reason_codes == (
        "consensus_watch",
        "cost_amount_above_watch_level",
        "cost_uncertainty_above_watch_level",
        "cost_watch",
        "evidence_quality_below_pass_level",
        "evidence_watch",
        "human_approval_gate_watch",
        "safety_boundary_pass",
        "settlement_clarity_below_pass_level",
        "settlement_watch",
        "settlement_window_above_watch_level",
        "team_agreement_below_pass_level",
        "team_disagreement_present",
    )


def test_missing_evidence_and_safety_boundary_flags_create_block_report() -> None:
    gate_report = report(
        (
            candidate(
                "candidate-block",
                evidence_count=d("0"),
                primary_source_count=d("0"),
                evidence_quality_score=d("0.300000"),
                settlement_clarity_score=d("0.300000"),
                team_agreement_ratio=d("0.400000"),
                team_disagreement_count=d("3"),
                safety_boundary_flags=("manual_boundary_review",),
            ),
        ),
    )

    row = gate_report.rows[0]
    assert gate_report.gate_status == "block"
    assert gate_report.block_count == d("1")
    assert row.evidence_status == "block"
    assert row.settlement_status == "block"
    assert row.consensus_status == "block"
    assert row.safety_status == "block"
    assert row.safety_boundary_flag_count == d("1")
    assert "safety_boundary_flag_present" in row.reason_codes
    assert "human_approval_gate_block" in gate_report.reason_codes


def test_rows_reason_counts_and_payload_are_deterministic_without_numeric_leaks() -> None:
    supplied = SuppliedCandidateShape(
        candidate_id="a-candidate",
        evidence_count=d("3"),
        primary_source_count=d("2"),
        evidence_quality_score=d("0.800000"),
        estimated_cost_amount=d("0.010000"),
        cost_uncertainty_score=d("0.100000"),
        settlement_clarity_score=d("0.900000"),
        settlement_window_hours=d("48"),
        team_agreement_ratio=d("0.900000"),
        team_disagreement_count=d("0"),
        safety_boundary_flags=(),
        public_notes="shape accepted",
        reason_codes=("zeta", "alpha"),
    )
    gate_report = report((candidate("z-candidate"), supplied))

    payload = research_human_approval_gate_payload(gate_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.candidate_id for row in gate_report.rows) == (
        "a-candidate",
        "z-candidate",
    )
    assert tuple(
        (count.reason_code, count.count)
        for count in gate_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "2"
    assert payload["rows"][0]["evidence_quality_score"] == "0.800000"
    assert not any(type(value) is float for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded


def test_validation_rejects_bad_types_bad_flags_and_unsafe_public_payload() -> None:
    with pytest.raises(ValueError, match="pass_evidence_quality_score"):
        config(pass_evidence_quality_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_cost_amount"):
        config(watch_cost_amount=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((candidate(),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((candidate(),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(candidate_id=" candidate-alpha")
    with pytest.raises(ValueError, match="evidence_count"):
        candidate(evidence_count=d("1.5"))
    with pytest.raises(ValueError, match="evidence_quality_score"):
        candidate(evidence_quality_score=d("1.1"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="unsafe public text"):
        candidate(public_notes=_chars(98, 117, 121))
    with pytest.raises(ValueError, match="unsafe field"):
        research_human_approval_gate_payload(
            {_chars(119, 97, 108, 108, 101, 116): "masked", "paper_only": True},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        research_human_approval_gate_payload({"count": 1, "paper_only": True})


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    gate_report = report((candidate(),))

    with pytest.raises(FrozenInstanceError):
        gate_report.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gate_report.rows[0].gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="gate_status"):
        replace(gate_report.rows[0], gate_status="watch")
    with pytest.raises(ValueError, match="gate_status"):
        replace(gate_report, gate_status="watch")


def test_owned_module_has_no_io_surface_or_prohibited_plaintext_terms() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_human_approval_gate_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "execute",
        _chars(97, 117, 116, 104),
        _chars(98, 117, 121),
        _chars(111, 114, 100, 101, 114),
        _chars(112, 111, 115, 105, 116, 105, 111, 110),
        _chars(114, 101, 99, 111, 109, 109, 101, 110, 100),
        _chars(115, 101, 108, 108),
        _chars(116, 114, 97, 100, 101),
        _chars(119, 97, 108, 108, 101, 116),
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)

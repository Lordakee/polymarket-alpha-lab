from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_strategy_readiness_score_report as readiness_module
from polymarket_alpha_lab.research_strategy_readiness_score_report import (
    ResearchStrategyReadinessCandidate,
    ResearchStrategyReadinessReasonCodeCount,
    ResearchStrategyReadinessScoreConfig,
    ResearchStrategyReadinessScoreReport,
    ResearchStrategyReadinessScoreRow,
    build_research_strategy_readiness_score_report,
    research_strategy_readiness_score_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedCandidateShape:
    candidate_id: str
    evidence_quality_score: Decimal
    probability_calibration_score: Decimal
    cost_friction_score: Decimal
    settlement_ambiguity_score: Decimal
    team_consensus_score: Decimal
    memory_coverage_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyReadinessScoreConfig:
    values = {
        "config_version": "research-strategy-readiness-score-report-v0",
        "pass_readiness_score": d("0.750000"),
        "watch_readiness_score": d("0.500000"),
        "evidence_quality_weight": d("0.250000"),
        "probability_calibration_weight": d("0.200000"),
        "cost_friction_weight": d("0.150000"),
        "settlement_ambiguity_weight": d("0.150000"),
        "team_consensus_weight": d("0.150000"),
        "memory_coverage_weight": d("0.100000"),
        "cost_friction_watch": d("0.500000"),
        "cost_friction_block": d("0.800000"),
        "settlement_ambiguity_watch": d("0.400000"),
        "settlement_ambiguity_block": d("0.700000"),
        "team_consensus_watch": d("0.500000"),
        "memory_coverage_watch": d("0.500000"),
    }
    values.update(overrides)
    return ResearchStrategyReadinessScoreConfig(**values)


def candidate(
    candidate_id: str = "market-alpha",
    *,
    evidence_quality_score: Decimal = d("0.900000"),
    probability_calibration_score: Decimal = d("0.850000"),
    cost_friction_score: Decimal = d("0.100000"),
    settlement_ambiguity_score: Decimal = d("0.050000"),
    team_consensus_score: Decimal = d("0.800000"),
    memory_coverage_score: Decimal = d("0.900000"),
    observed_at: datetime = GENERATED_AT,
    reason_codes: tuple[str, ...] = (),
) -> ResearchStrategyReadinessCandidate:
    return ResearchStrategyReadinessCandidate(
        candidate_id=candidate_id,
        evidence_quality_score=evidence_quality_score,
        probability_calibration_score=probability_calibration_score,
        cost_friction_score=cost_friction_score,
        settlement_ambiguity_score=settlement_ambiguity_score,
        team_consensus_score=team_consensus_score,
        memory_coverage_score=memory_coverage_score,
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategyReadinessScoreConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyReadinessScoreReport:
    return build_research_strategy_readiness_score_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_for_manual_research_queue() -> None:
    readiness_report = report(())

    assert type(readiness_report) is ResearchStrategyReadinessScoreReport
    assert readiness_report.generated_at == GENERATED_AT
    assert readiness_report.config_version == "research-strategy-readiness-score-report-v0"
    assert readiness_report.candidate_count == d("0")
    assert readiness_report.pass_count == d("0")
    assert readiness_report.watch_count == d("0")
    assert readiness_report.block_count == d("0")
    assert readiness_report.average_readiness_score is None
    assert readiness_report.status == "block"
    assert readiness_report.reason_codes == ("no_research_candidates",)
    assert readiness_report.reason_code_counts == (
        ResearchStrategyReadinessReasonCodeCount(
            reason_code="no_research_candidates",
            count=d("1"),
        ),
    )
    assert readiness_report.rows == ()
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True


def test_high_quality_candidate_passes_with_deterministic_decimal_score() -> None:
    readiness_report = report(
        (
            candidate(
                reason_codes=("manual_reviewed",),
            ),
        ),
    )

    row = readiness_report.rows[0]
    assert readiness_report.status == "pass"
    assert readiness_report.candidate_count == d("1")
    assert readiness_report.pass_count == d("1")
    assert readiness_report.watch_count == d("0")
    assert readiness_report.block_count == d("0")
    assert readiness_report.average_readiness_score == d("0.882500")
    assert readiness_report.reason_codes == ("strategy_readiness_pass",)
    assert type(row) is ResearchStrategyReadinessScoreRow
    assert row.candidate_id == "market-alpha"
    assert row.readiness_score == d("0.882500")
    assert row.status == "pass"
    assert row.reason_codes == (
        "evidence_quality_strong",
        "input_manual_reviewed",
        "low_cost_friction",
        "low_settlement_ambiguity",
        "memory_coverage_strong",
        "probability_calibration_strong",
        "strategy_readiness_pass",
        "team_consensus_strong",
    )


def test_custom_readiness_thresholds_drive_row_consistency_without_defaults() -> None:
    readiness_report = report(
        (
            candidate(
                evidence_quality_score=d("0.650000"),
                probability_calibration_score=d("0.650000"),
                cost_friction_score=d("0.350000"),
                settlement_ambiguity_score=d("0.350000"),
                team_consensus_score=d("0.650000"),
                memory_coverage_score=d("0.650000"),
            ),
        ),
        cfg=config(
            pass_readiness_score=d("0.650000"),
            watch_readiness_score=d("0.400000"),
        ),
    )

    row = readiness_report.rows[0]
    assert row.readiness_score == d("0.650000")
    assert row.readiness_score < d("0.750000")
    assert row.status == "pass"
    assert readiness_report.status == "pass"


def test_rows_reason_counts_and_payload_are_deterministic_without_float_values() -> None:
    readiness_report = report(
        (
            candidate(
                "z-block",
                settlement_ambiguity_score=d("0.850000"),
                reason_codes=("settlement_needs_review",),
            ),
            SuppliedCandidateShape(
                candidate_id="a-pass",
                evidence_quality_score=d("0.950000"),
                probability_calibration_score=d("0.900000"),
                cost_friction_score=d("0.050000"),
                settlement_ambiguity_score=d("0.050000"),
                team_consensus_score=d("0.900000"),
                memory_coverage_score=d("0.950000"),
                observed_at=GENERATED_AT,
                reason_codes=("alpha", "zeta"),
            ),
            candidate(
                "m-watch",
                cost_friction_score=d("0.600000"),
            ),
        ),
    )

    payload = research_strategy_readiness_score_report_payload(readiness_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.candidate_id for row in readiness_report.rows) == (
        "a-pass",
        "m-watch",
        "z-block",
    )
    assert tuple(row.status for row in readiness_report.rows) == ("pass", "watch", "block")
    assert readiness_report.status == "block"
    assert readiness_report.pass_count == d("1")
    assert readiness_report.watch_count == d("1")
    assert readiness_report.block_count == d("1")
    assert tuple(
        (count.reason_code, count.count)
        for count in readiness_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (
        ("input_alpha", d("1")),
        ("input_settlement_needs_review", d("1")),
        ("input_zeta", d("1")),
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert all("candidate_id" not in row_payload for row_payload in payload["rows"])
    assert payload["rows"][0]["readiness_score"] == str(
        readiness_report.rows[0].readiness_score,
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded


def test_public_payload_rejects_candidate_id_leakage() -> None:
    with pytest.raises(ValueError, match="candidate_id"):
        readiness_module._reject_unsafe_public_payload(
            "report payload",
            {"rows": [{"candidate_id": "market-alpha"}]},
        )


def test_validation_rejects_bad_types_unknown_values_future_times_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="weight"):
        config(evidence_quality_weight=d("0.200000"))
    with pytest.raises(ValueError, match="pass_readiness_score"):
        config(pass_readiness_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_friction_score"):
        candidate(cost_friction_score=d("1.000001"))
    with pytest.raises(ValueError, match="memory_coverage_score"):
        candidate(memory_coverage_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((candidate(),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((candidate(),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(" market-alpha")
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((candidate(observed_at=datetime(2026, 7, 6, 12, 0, 1, tzinfo=UTC)),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    readiness_report = report((candidate(),))

    with pytest.raises(FrozenInstanceError):
        readiness_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness_report.rows[0].readiness_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="readiness_score"):
        replace(readiness_report.rows[0], readiness_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(readiness_report, status="watch")


def test_public_constructors_reject_noncanonical_sorting() -> None:
    rows = report((candidate("z-candidate"), candidate("a-candidate"))).rows

    with pytest.raises(ValueError, match="rows"):
        replace(report(rows), rows=tuple(reversed(rows)))

    counts = report(rows).reason_code_counts
    if len(counts) > 1:
        with pytest.raises(ValueError, match="reason_code_counts"):
            replace(report(rows), reason_code_counts=tuple(reversed(counts)))


def test_owned_module_has_no_execution_network_storage_or_action_language_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_readiness_score_report.py"
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
        "sqlite",
        "postgres",
        "mysql",
        "mongodb",
        "wallet",
        "auth",
        "live trading",
        "trading",
        "trade",
        "buy",
        "sell",
        "position",
        "recommend",
        "order",
        "mutation",
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

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_counter_thesis_matrix import (
    ResearchCounterThesisConfig,
    ResearchCounterThesisEvidence,
    ResearchCounterThesisMatrixReport,
    ResearchCounterThesisMatrixRow,
    ResearchCounterThesisReasonCodeCount,
    build_research_counter_thesis_matrix_report,
    research_counter_thesis_matrix_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedEvidenceShape:
    candidate_key: str
    counter_thesis_code: str
    evidence_key: str
    source_family: str
    counter_evidence_strength: Decimal
    source_independence: Decimal
    unresolved_conflict: Decimal
    source_ref: str
    source_url: str | None = None
    source_text: str | None = None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchCounterThesisConfig:
    values = {
        "config_version": "research-counter-thesis-matrix-v0",
        "watch_score_threshold": d("0.350000"),
        "block_score_threshold": d("0.750000"),
        "min_independent_source_families": d("2"),
        "strong_counter_evidence_threshold": d("0.700000"),
        "unresolved_conflict_threshold": d("0.500000"),
        "counter_evidence_strength_weight": d("0.500000"),
        "source_independence_weight": d("0.300000"),
        "unresolved_conflict_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchCounterThesisConfig(**values)


def evidence(
    index: int,
    *,
    candidate_key: str = "candidate-alpha",
    counter_thesis_code: str = "resolution_delay",
    source_family: str = "official",
    counter_evidence_strength: Decimal = d("0.900000"),
    source_independence: Decimal = d("0.900000"),
    unresolved_conflict: Decimal = d("0.800000"),
    source_ref: str | None = None,
    source_url: str | None = "https://private.example/source",
    source_text: str | None = "private source text must stay out of payload",
    reason_codes: tuple[str, ...] = (),
) -> ResearchCounterThesisEvidence:
    return ResearchCounterThesisEvidence(
        candidate_key=candidate_key,
        counter_thesis_code=counter_thesis_code,
        evidence_key=f"evidence-{index:03d}",
        source_family=source_family,
        counter_evidence_strength=counter_evidence_strength,
        source_independence=source_independence,
        unresolved_conflict=unresolved_conflict,
        source_ref=source_ref or f"private-ref-{index:03d}",
        source_url=source_url,
        source_text=source_text,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchCounterThesisConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchCounterThesisMatrixReport:
    return build_research_counter_thesis_matrix_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_pass_report_without_matrix_rows() -> None:
    matrix_report = report(())

    assert type(matrix_report) is ResearchCounterThesisMatrixReport
    assert matrix_report.generated_at == GENERATED_AT
    assert matrix_report.config_version == "research-counter-thesis-matrix-v0"
    assert matrix_report.candidate_count == d("0")
    assert matrix_report.matrix_row_count == d("0")
    assert matrix_report.evidence_count == d("0")
    assert matrix_report.pass_count == d("0")
    assert matrix_report.watch_count == d("0")
    assert matrix_report.block_count == d("0")
    assert matrix_report.average_counter_thesis_score is None
    assert matrix_report.status == "pass"
    assert matrix_report.reason_codes == ("no_counter_thesis_evidence",)
    assert matrix_report.reason_code_counts == (
        ResearchCounterThesisReasonCodeCount(
            reason_code="no_counter_thesis_evidence",
            count=d("1"),
        ),
    )
    assert matrix_report.rows == ()
    assert matrix_report.paper_only is True
    assert matrix_report.report_only is True
    assert matrix_report.readonly is True


def test_strong_independent_unresolved_counter_thesis_blocks_candidate() -> None:
    matrix_report = report(
        (
            evidence(
                3,
                source_family="analysis",
                counter_evidence_strength=d("0.950000"),
                source_independence=d("0.950000"),
                unresolved_conflict=d("0.850000"),
            ),
            evidence(
                1,
                source_family="official",
                counter_evidence_strength=d("0.850000"),
                source_independence=d("0.800000"),
                unresolved_conflict=d("0.700000"),
                reason_codes=("manual_reviewed",),
            ),
            evidence(
                2,
                source_family="venue",
                counter_evidence_strength=d("0.900000"),
                source_independence=d("0.900000"),
                unresolved_conflict=d("0.800000"),
            ),
        ),
    )

    assert matrix_report.status == "block"
    assert matrix_report.candidate_count == d("1")
    assert matrix_report.matrix_row_count == d("1")
    assert matrix_report.evidence_count == d("3")
    assert matrix_report.pass_count == d("0")
    assert matrix_report.watch_count == d("0")
    assert matrix_report.block_count == d("1")
    assert matrix_report.average_counter_thesis_score == d("0.871666")

    row = matrix_report.rows[0]
    assert type(row) is ResearchCounterThesisMatrixRow
    assert row.candidate_key == "candidate-alpha"
    assert row.counter_thesis_code == "resolution_delay"
    assert row.evidence_count == d("3")
    assert row.source_family_count == d("3")
    assert row.average_counter_evidence_strength == d("0.900000")
    assert row.source_independence_score == d("0.883333")
    assert row.unresolved_conflict_score == d("0.783333")
    assert row.counter_thesis_score == d("0.871666")
    assert row.status == "block"
    assert row.reason_codes == (
        "counter_thesis_block",
        "independent_sources",
        "input_manual_reviewed",
        "strong_counter_evidence",
        "unresolved_conflicts_present",
    )


def test_rows_reason_counts_and_payload_are_deterministic_and_public_only() -> None:
    matrix_report = report(
        (
            SuppliedEvidenceShape(
                candidate_key="candidate-zeta",
                counter_thesis_code="weak_turnout",
                evidence_key="shape-002",
                source_family="commentary",
                counter_evidence_strength=d("0.300000"),
                source_independence=d("0.600000"),
                unresolved_conflict=d("0.200000"),
                source_ref="private-shape-ref",
                source_url="https://private.example/shape",
                source_text="shape source text should not be serialized",
                reason_codes=("needs_follow_up",),
            ),
            evidence(
                2,
                candidate_key="candidate-alpha",
                counter_thesis_code="late_report",
                source_family="independent",
                counter_evidence_strength=d("0.600000"),
                source_independence=d("0.700000"),
                unresolved_conflict=d("0.500000"),
            ),
            evidence(
                1,
                candidate_key="candidate-alpha",
                counter_thesis_code="late_report",
                source_family="official",
                counter_evidence_strength=d("0.500000"),
                source_independence=d("0.700000"),
                unresolved_conflict=d("0.400000"),
                reason_codes=("zeta", "alpha"),
            ),
        ),
    )

    payload = research_counter_thesis_matrix_report_payload(matrix_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(
        (row.candidate_key, row.counter_thesis_code, row.status)
        for row in matrix_report.rows
    ) == (
        ("candidate-alpha", "late_report", "watch"),
        ("candidate-zeta", "weak_turnout", "pass"),
    )
    assert tuple(
        (count.reason_code, count.count)
        for count in matrix_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (
        ("input_alpha", d("1")),
        ("input_needs_follow_up", d("1")),
        ("input_zeta", d("1")),
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["counter_thesis_score"] == str(
        matrix_report.rows[0].counter_thesis_score,
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert "private-ref" not in encoded
    assert "private-shape-ref" not in encoded
    assert "https://" not in encoded
    assert "source_text" not in encoded
    assert "source_url" not in encoded
    assert "source_ref" not in encoded


def test_validation_rejects_bad_types_unsafe_public_values_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="counter_evidence_strength_weight"):
        config(counter_evidence_strength_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_score_threshold"):
        config(block_score_threshold=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_independence_weight"):
        config(source_independence_weight=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (evidence(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="candidate_key"):
        evidence(1, candidate_key=" candidate-alpha")
    with pytest.raises(ValueError, match="candidate_key"):
        evidence(1, candidate_key="market-alpha")
    with pytest.raises(ValueError, match="counter_thesis_code"):
        evidence(1, counter_thesis_code="Late Report")
    with pytest.raises(ValueError, match="counter_evidence_strength"):
        evidence(1, counter_evidence_strength=Decimal("1.000001"))
    with pytest.raises(ValueError, match="source_independence"):
        evidence(1, source_independence=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    matrix_report = report((evidence(1),))

    with pytest.raises(FrozenInstanceError):
        matrix_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        matrix_report.rows[0].counter_thesis_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="counter_thesis_score"):
        replace(matrix_report.rows[0], counter_thesis_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(matrix_report, status="pass")


def test_owned_module_has_no_network_database_trading_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_counter_thesis_matrix.py"
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
        "psycopg",
        "supabase",
        "web3",
        "place_order",
        "submit_order",
        "trade(",
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

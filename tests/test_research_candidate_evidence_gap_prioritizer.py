from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_candidate_evidence_gap_prioritizer import (
    ResearchCandidateEvidenceGapItem,
    ResearchCandidateEvidenceGapPrioritizerConfig,
    ResearchCandidateEvidenceGapPrioritizerReport,
    ResearchCandidateEvidenceGapPriorityRow,
    build_research_candidate_evidence_gap_prioritizer_report,
    research_candidate_evidence_gap_prioritizer_public_digest,
    research_candidate_evidence_gap_prioritizer_public_payload,
    validate_research_candidate_evidence_gap_prioritizer_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchCandidateEvidenceGapPrioritizerConfig:
    values = {
        "config_version": "research-candidate-evidence-gap-prioritizer-v0",
        "min_evidence_item_count": d("2.000000"),
        "min_source_family_count": d("2.000000"),
        "fresh_age_seconds": d("3600.000000"),
        "stale_age_seconds": d("86400.000000"),
        "min_coverage_score": d("0.750000"),
        "min_reliability_score": d("0.700000"),
        "pass_gap_priority_score": d("0.250000"),
        "block_gap_priority_score": d("0.650000"),
        "coverage_gap_weight": d("0.400000"),
        "conflict_weight": d("0.250000"),
        "recency_gap_weight": d("0.200000"),
        "reliability_gap_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchCandidateEvidenceGapPrioritizerConfig(**values)


def item(
    index: int,
    *,
    candidate_key: str = "candidate-alpha",
    source_family: str | None = None,
    observed_at: datetime | None = None,
    evidence_coverage_score: Decimal = d("0.950000"),
    source_reliability_score: Decimal = d("0.950000"),
    conflict_flag: bool = False,
    hard_gap_flag: bool = False,
) -> ResearchCandidateEvidenceGapItem:
    return ResearchCandidateEvidenceGapItem(
        candidate_key=candidate_key,
        evidence_key=f"evidence-{index:03d}",
        source_family=source_family or f"family-{index:03d}",
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        evidence_coverage_score=evidence_coverage_score,
        source_reliability_score=source_reliability_score,
        conflict_flag=conflict_flag,
        hard_gap_flag=hard_gap_flag,
    )


def report(
    items: tuple[ResearchCandidateEvidenceGapItem, ...],
    *,
    cfg: ResearchCandidateEvidenceGapPrioritizerConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchCandidateEvidenceGapPrioritizerReport:
    return build_research_candidate_evidence_gap_prioritizer_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_pass_watch_and_block_rows_prioritize_human_collection_gaps() -> None:
    gap_report = report(
        (
            item(4, candidate_key="watch-candidate", conflict_flag=True),
            item(2, candidate_key="pass-candidate", source_family="official"),
            item(5, candidate_key="watch-candidate"),
            item(6, candidate_key="block-candidate", hard_gap_flag=True),
            item(3, candidate_key="pass-candidate", source_family="archive"),
            item(7, candidate_key="block-candidate"),
        ),
    )

    assert type(gap_report) is ResearchCandidateEvidenceGapPrioritizerReport
    assert gap_report.status == "block"
    assert gap_report.candidate_count == d("3.000000")
    assert gap_report.evidence_item_count == d("6.000000")
    assert gap_report.pass_count == d("1.000000")
    assert gap_report.watch_count == d("1.000000")
    assert gap_report.block_count == d("1.000000")

    rows_by_status = {row.manual_collection_status: row for row in gap_report.rows}
    assert rows_by_status["pass"].event_slot == "event-002"
    assert rows_by_status["pass"].gap_priority_score == d("0.027500")
    assert rows_by_status["pass"].reason_codes == (
        "evidence_gap_priority_pass",
        "manual_collection_ready",
    )
    assert rows_by_status["watch"].conflict_item_count == d("1.000000")
    assert rows_by_status["watch"].gap_priority_score == d("0.152500")
    assert rows_by_status["watch"].reason_codes == (
        "conflict_present",
        "evidence_gap_priority_watch",
    )
    assert rows_by_status["block"].hard_gap_flag_count == d("1.000000")
    assert rows_by_status["block"].reason_codes == (
        "evidence_gap_priority_block",
        "manual_hard_gap_flag",
    )
    assert gap_report.reason_codes == (
        "conflict_present",
        "evidence_gap_priority_block",
        "manual_collection_ready",
        "manual_hard_gap_flag",
    )


def test_empty_input_returns_block_public_status_without_private_identifiers() -> None:
    gap_report = report(())
    payload = research_candidate_evidence_gap_prioritizer_public_payload(gap_report)

    assert gap_report.status == "block"
    assert gap_report.rows == ()
    assert gap_report.reason_codes == ("no_candidate_evidence",)
    assert gap_report.reason_code_counts[0].reason_code == "no_candidate_evidence"
    assert payload["status"] == "block"
    assert "blocked" not in json.dumps(payload, sort_keys=True)


def test_decimal_only_exact_types_and_frozen_outputs_are_enforced() -> None:
    gap_report = report((item(1), item(2)))

    with pytest.raises(FrozenInstanceError):
        gap_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gap_report.rows[0].gap_priority_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="pass_gap_priority_score"):
        config(pass_gap_priority_score=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_coverage_score"):
        config(min_coverage_score=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="evidence_coverage_score"):
        item(1, evidence_coverage_score=d("1.000001"))
    with pytest.raises(ValueError, match="source_reliability_score"):
        item(1, source_reliability_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        item(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((item(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="conflict_flag"):
        replace(item(1), conflict_flag=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="readonly"):
        replace(gap_report, readonly=False)


def test_public_payload_rejects_private_market_source_and_trading_leaks() -> None:
    gap_report = report(
        (
            item(2, candidate_key="candidate-zeta", source_family="official"),
            item(1, candidate_key="candidate-zeta", source_family="analysis"),
        ),
    )
    payload = gap_report.payload
    encoded = json.dumps(payload, sort_keys=True)

    assert "candidate-zeta" not in encoded
    assert "evidence-001" not in encoded
    assert "official" not in encoded
    assert all(key not in encoded for key in ("candidate_id", "market_id", "source_url"))
    assert not any(
        isinstance(value, float | int | Decimal) and type(value) is not bool
        for value in _walk_values(payload)
    )

    leak_cases = (
        {"candidate_id": "candidate-zeta"},
        {"rows": [{"event_slot": "market-alpha"}]},
        {"rows": [{"source_url": "https://example.invalid/source"}]},
        {"rows": [{"status": "blocked"}]},
        {"paper_only": True, "report_only": True, "readonly": True, "score": 0.1},
        {"paper_only": True, "report_only": True, "readonly": False},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "buy now"},
    )
    for leak_payload in leak_cases:
        with pytest.raises(ValueError):
            validate_research_candidate_evidence_gap_prioritizer_public_payload(
                leak_payload,  # type: ignore[arg-type]
            )


def test_stale_low_reliability_and_hard_flags_drive_reason_codes() -> None:
    gap_report = report(
        (
            item(
                1,
                candidate_key="risk-candidate",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(days=2),
                evidence_coverage_score=d("0.500000"),
                source_reliability_score=d("0.600000"),
            ),
            item(
                2,
                candidate_key="risk-candidate",
                source_family="analysis",
                observed_at=GENERATED_AT - timedelta(days=2),
                evidence_coverage_score=d("0.500000"),
                source_reliability_score=d("0.600000"),
                conflict_flag=True,
                hard_gap_flag=True,
            ),
        ),
    )

    row = gap_report.rows[0]
    assert row.manual_collection_status == "block"
    assert row.stale_item_count == d("2.000000")
    assert row.low_reliability_item_count == d("2.000000")
    assert row.conflict_item_count == d("1.000000")
    assert row.hard_gap_flag_count == d("1.000000")
    assert row.reason_codes == (
        "conflict_present",
        "coverage_gap_present",
        "evidence_gap_priority_block",
        "low_reliability_present",
        "manual_hard_gap_flag",
        "stale_evidence_present",
    )


def test_payload_digest_and_ordering_are_deterministic_and_consistent() -> None:
    items = (
        item(3, candidate_key="z-candidate", source_family="secondary"),
        item(1, candidate_key="a-candidate", source_family="official"),
        item(4, candidate_key="z-candidate", source_family="official"),
        item(2, candidate_key="a-candidate", source_family="archive"),
    )
    first_report = report(items)
    second_report = report(tuple(reversed(items)))
    first_payload = research_candidate_evidence_gap_prioritizer_public_payload(first_report)
    second_payload = research_candidate_evidence_gap_prioritizer_public_payload(second_report)

    assert first_payload == second_payload
    assert tuple(row.event_slot for row in first_report.rows) == ("event-001", "event-002")
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == (
        research_candidate_evidence_gap_prioritizer_public_digest(first_report)
    )
    assert first_payload["derived_validation_digest"] == (
        research_candidate_evidence_gap_prioritizer_public_digest(first_payload)
    )
    assert validate_research_candidate_evidence_gap_prioritizer_public_payload(first_payload)
    json.dumps(first_payload, sort_keys=True)

    tampered_payload = dict(first_payload)
    tampered_payload["status"] = "watch"
    with pytest.raises(ValueError, match="digest"):
        research_candidate_evidence_gap_prioritizer_public_payload(tampered_payload)


def test_manual_rows_validate_consistency() -> None:
    gap_report = report((item(1), item(2)))
    row = gap_report.rows[0]

    assert type(row) is ResearchCandidateEvidenceGapPriorityRow
    with pytest.raises(ValueError, match="manual_collection_status"):
        replace(row, manual_collection_status="block")
    with pytest.raises(ValueError, match="source_family_count"):
        replace(row, source_family_count=d("3.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(gap_report, status="watch")


def test_owned_module_has_no_network_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_candidate_evidence_gap_prioritizer.py"
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
        "create_order",
        "sign_order",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_values(item))
    else:
        values.append(value)
    return tuple(values)

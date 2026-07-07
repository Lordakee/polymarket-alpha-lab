from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_evidence_confidence_calibrator import (
    ResearchEvidenceConfidenceCalibratedRow,
    ResearchEvidenceConfidenceCalibratorConfig,
    ResearchEvidenceConfidenceEvidence,
    ResearchEvidenceConfidenceReasonCodeCount,
    ResearchEvidenceConfidenceReport,
    build_research_evidence_confidence_report,
    research_evidence_confidence_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEvidenceConfidenceCalibratorConfig:
    values = {
        "config_version": "research-evidence-confidence-calibrator-v0",
        "pass_confidence_score": d("0.700000"),
        "watch_confidence_score": d("0.400000"),
        "source_quality_weight": d("0.350000"),
        "freshness_weight": d("0.250000"),
        "consistency_weight": d("0.250000"),
        "counterevidence_resistance_weight": d("0.150000"),
        "min_pass_consistency_score": d("0.650000"),
        "watch_counterevidence_strength": d("0.500000"),
        "block_counterevidence_strength": d("0.850000"),
        "base_band_half_width": d("0.050000"),
        "consistency_uncertainty_weight": d("0.100000"),
        "counterevidence_uncertainty_weight": d("0.100000"),
        "max_band_half_width": d("0.300000"),
    }
    values.update(overrides)
    return ResearchEvidenceConfidenceCalibratorConfig(**values)


def evidence(
    index: int,
    *,
    claim_id: str = "market-alpha",
    source_id: str = "official-resolution",
    source_family: str = "official",
    observed_at: datetime | None = None,
    source_quality_score: Decimal = d("0.950000"),
    freshness_score: Decimal = d("0.900000"),
    consistency_score: Decimal = d("0.900000"),
    counterevidence_strength: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchEvidenceConfidenceEvidence:
    return ResearchEvidenceConfidenceEvidence(
        claim_id=claim_id,
        evidence_id=f"evidence-{index:03d}",
        source_id=source_id,
        source_family=source_family,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        source_quality_score=source_quality_score,
        freshness_score=freshness_score,
        consistency_score=consistency_score,
        counterevidence_strength=counterevidence_strength,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchEvidenceConfidenceEvidence, ...],
    *,
    cfg: ResearchEvidenceConfidenceCalibratorConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEvidenceConfidenceReport:
    return build_research_evidence_confidence_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_zero_confidence_report() -> None:
    confidence_report = report(())

    assert type(confidence_report) is ResearchEvidenceConfidenceReport
    assert confidence_report.generated_at == GENERATED_AT
    assert confidence_report.config_version == "research-evidence-confidence-calibrator-v0"
    assert confidence_report.claim_count == d("0")
    assert confidence_report.evidence_count == d("0")
    assert confidence_report.pass_count == d("0")
    assert confidence_report.watch_count == d("0")
    assert confidence_report.blocked_count == d("0")
    assert confidence_report.average_confidence_score is None
    assert confidence_report.status == "blocked"
    assert confidence_report.reason_codes == ("no_research_evidence",)
    assert confidence_report.reason_code_counts == (
        ResearchEvidenceConfidenceReasonCodeCount(
            reason_code="no_research_evidence",
            count=d("1"),
        ),
    )
    assert confidence_report.rows == ()
    assert confidence_report.paper_only is True
    assert confidence_report.report_only is True
    assert confidence_report.readonly is True


def test_maps_source_quality_freshness_consistency_and_counterevidence_to_band() -> None:
    confidence_report = report(
        (
            evidence(
                2,
                source_id="analysis-note",
                source_family="analysis",
                source_quality_score=d("0.850000"),
                freshness_score=d("0.800000"),
                consistency_score=d("0.700000"),
                counterevidence_strength=d("0.200000"),
                reason_codes=("manual_reviewed",),
            ),
            evidence(1),
        ),
    )

    assert confidence_report.status == "pass"
    assert confidence_report.claim_count == d("1")
    assert confidence_report.evidence_count == d("2")
    assert confidence_report.pass_count == d("1")
    assert confidence_report.watch_count == d("0")
    assert confidence_report.blocked_count == d("0")
    assert confidence_report.average_confidence_score == d("0.847500")
    assert confidence_report.reason_codes == ("research_evidence_confidence_pass",)

    row = confidence_report.rows[0]
    assert type(row) is ResearchEvidenceConfidenceCalibratedRow
    assert row.claim_id == "market-alpha"
    assert row.evidence_count == d("2")
    assert row.latest_observed_at == GENERATED_AT - timedelta(minutes=30)
    assert row.source_quality_score == d("0.900000")
    assert row.freshness_score == d("0.850000")
    assert row.consistency_score == d("0.800000")
    assert row.counterevidence_strength == d("0.200000")
    assert row.confidence_score == d("0.847500")
    assert row.band_half_width == d("0.090000")
    assert row.confidence_band_low == d("0.757500")
    assert row.confidence_band_high == d("0.937500")
    assert row.evidence_ids == ("evidence-001", "evidence-002")
    assert row.source_ids == ("analysis-note", "official-resolution")
    assert row.source_families == ("analysis", "official")
    assert row.status == "pass"
    assert row.reason_codes == (
        "fresh_evidence",
        "low_counterevidence",
        "public_reason_input_manual_reviewed",
        "research_evidence_confidence_pass",
        "source_quality_support",
    )


def test_payload_is_deterministic_public_and_decimal_only() -> None:
    confidence_report = report(
        (
            evidence(3, claim_id="z-claim", counterevidence_strength=d("0.900000")),
            evidence(1, claim_id="a-claim", reason_codes=("zeta", "alpha")),
            evidence(2, claim_id="z-claim", consistency_score=d("0.400000")),
        ),
    )

    payload = research_evidence_confidence_report_payload(confidence_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.claim_id for row in confidence_report.rows) == ("a-claim", "z-claim")
    assert confidence_report.rows[0].reason_codes == (
        "fresh_evidence",
        "low_counterevidence",
        "public_reason_input_alpha",
        "public_reason_input_zeta",
        "research_evidence_confidence_pass",
        "source_quality_support",
    )
    assert tuple(
        (count.reason_code, count.count)
        for count in confidence_report.reason_code_counts
        if count.reason_code.startswith("public_reason_input_")
    ) == (
        ("public_reason_input_alpha", d("1")),
        ("public_reason_input_zeta", d("1")),
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["confidence_score"] == "0.917500"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert "secret" not in encoded.lower()


def test_validation_rejects_bad_types_future_times_flags_and_public_leaks() -> None:
    with pytest.raises(ValueError, match="source_quality_weight"):
        config(source_quality_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_confidence_score"):
        config(pass_confidence_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="freshness_weight"):
        config(freshness_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="claim_id"):
        evidence(1, claim_id=" market-alpha")
    with pytest.raises(ValueError, match="source_id"):
        evidence(1, source_id="https://example.invalid/private")
    with pytest.raises(ValueError, match="source_family"):
        evidence(1, source_family="secret_feed")
    with pytest.raises(ValueError, match="observed_at"):
        evidence(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((evidence(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="source_quality_score"):
        evidence(1, source_quality_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="freshness_score"):
        evidence(1, freshness_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="counterevidence_strength"):
        evidence(1, counterevidence_strength=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("api_key_seen",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(1), paper_only=False)


def test_status_boundaries_are_inclusive_and_counterevidence_can_block() -> None:
    boundary_config = config(
        source_quality_weight=d("1.000000"),
        freshness_weight=d("0.000000"),
        consistency_weight=d("0.000000"),
        counterevidence_resistance_weight=d("0.000000"),
        min_pass_consistency_score=d("0.000000"),
        watch_counterevidence_strength=d("0.500000"),
        block_counterevidence_strength=d("0.850000"),
    )

    passing = report(
        (
            evidence(
                1,
                source_quality_score=d("0.700000"),
                freshness_score=d("0.000000"),
                consistency_score=d("0.000000"),
                counterevidence_strength=d("0.000000"),
            ),
        ),
        cfg=boundary_config,
    )
    watched = report(
        (
            evidence(
                1,
                source_quality_score=d("0.699999"),
                freshness_score=d("0.000000"),
                consistency_score=d("0.000000"),
                counterevidence_strength=d("0.000000"),
            ),
        ),
        cfg=boundary_config,
    )
    watched_floor = report(
        (
            evidence(
                1,
                source_quality_score=d("0.400000"),
                freshness_score=d("0.000000"),
                consistency_score=d("0.000000"),
                counterevidence_strength=d("0.000000"),
            ),
        ),
        cfg=boundary_config,
    )
    blocked = report(
        (
            evidence(
                1,
                source_quality_score=d("0.399999"),
                freshness_score=d("0.000000"),
                consistency_score=d("0.000000"),
                counterevidence_strength=d("0.000000"),
            ),
        ),
        cfg=boundary_config,
    )
    counterevidence_blocked = report(
        (
            evidence(
                1,
                source_quality_score=d("1.000000"),
                freshness_score=d("1.000000"),
                consistency_score=d("1.000000"),
                counterevidence_strength=d("0.850000"),
            ),
        ),
        cfg=boundary_config,
    )

    assert passing.rows[0].status == "pass"
    assert watched.rows[0].status == "watch"
    assert watched_floor.rows[0].status == "watch"
    assert blocked.rows[0].status == "blocked"
    assert counterevidence_blocked.rows[0].status == "blocked"


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    confidence_report = report((evidence(1),))

    with pytest.raises(FrozenInstanceError):
        confidence_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        confidence_report.rows[0].confidence_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="confidence_band"):
        replace(confidence_report.rows[0], confidence_band_low=d("0.950000"))
    with pytest.raises(ValueError, match="status"):
        replace(confidence_report, status="watch")


def test_owned_module_has_no_network_filesystem_execution_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_evidence_confidence_calibrator.py"
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
        "place_order",
        "submit_order",
        "private_key",
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

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_quality_policy import (
    ResearchSourceQualityConfig,
    ResearchSourceQualityEvidenceRow,
    ResearchSourceQualityReasonCodeCount,
    ResearchSourceQualityReport,
    ResearchSourceQualityScoreRow,
    build_research_source_quality_report,
    research_source_quality_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedEvidenceShape:
    claim_id: str
    evidence_id: str
    source_id: str | None
    source_family: str | None
    source_type: str
    directness: str
    observed_at: datetime
    conflict_flag: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


_DEFAULT_SOURCE_ID = object()


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceQualityConfig:
    values = {
        "config_version": "research-source-quality-policy-v0",
        "fresh_age_seconds": d("3600"),
        "stale_age_seconds": d("86400"),
        "min_source_count": d("2"),
        "min_source_family_count": d("2"),
        "pass_quality_score": d("0.700000"),
        "watch_quality_score": d("0.400000"),
        "recency_weight": d("0.350000"),
        "diversity_weight": d("0.250000"),
        "directness_weight": d("0.200000"),
        "primary_source_weight": d("0.200000"),
        "missing_source_penalty": d("0.250000"),
        "conflict_flag_penalty": d("0.150000"),
    }
    values.update(overrides)
    return ResearchSourceQualityConfig(**values)


def evidence(
    index: int,
    *,
    claim_id: str = "market-alpha",
    source_id: str | None | object = _DEFAULT_SOURCE_ID,
    source_family: str | None = "official",
    source_type: str = "primary",
    directness: str = "direct",
    observed_at: datetime | None = None,
    conflict_flag: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceQualityEvidenceRow:
    return ResearchSourceQualityEvidenceRow(
        claim_id=claim_id,
        evidence_id=f"evidence-{index:03d}",
        source_id=(
            f"source-{index:03d}" if source_id is _DEFAULT_SOURCE_ID else source_id
        ),
        source_family=source_family,
        source_type=source_type,
        directness=directness,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        conflict_flag=conflict_flag,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceQualityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceQualityReport:
    return build_research_source_quality_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_zero_quality_report() -> None:
    quality_report = report(())

    assert type(quality_report) is ResearchSourceQualityReport
    assert quality_report.generated_at == GENERATED_AT
    assert quality_report.config_version == "research-source-quality-policy-v0"
    assert quality_report.claim_count == d("0")
    assert quality_report.evidence_count == d("0")
    assert quality_report.pass_count == d("0")
    assert quality_report.watch_count == d("0")
    assert quality_report.blocked_count == d("0")
    assert quality_report.average_quality_score is None
    assert quality_report.status == "blocked"
    assert quality_report.reason_codes == ("no_research_evidence",)
    assert quality_report.reason_code_counts == (
        ResearchSourceQualityReasonCodeCount(
            reason_code="no_research_evidence",
            count=d("1"),
        ),
    )
    assert quality_report.rows == ()
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True


def test_fresh_diverse_direct_primary_sources_pass_with_deterministic_score() -> None:
    quality_report = report(
        (
            evidence(
                2,
                source_id="venue-notice",
                source_family="venue",
                observed_at=GENERATED_AT - timedelta(hours=2),
            ),
            evidence(
                3,
                source_id="analysis-note",
                source_family="analysis",
                source_type="secondary",
                directness="indirect",
                observed_at=GENERATED_AT - timedelta(hours=3),
                reason_codes=("manual_reviewed",),
            ),
            evidence(
                1,
                source_id="official-resolution",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(minutes=30),
            ),
        ),
    )

    assert quality_report.status == "pass"
    assert quality_report.claim_count == d("1")
    assert quality_report.evidence_count == d("3")
    assert quality_report.pass_count == d("1")
    assert quality_report.watch_count == d("0")
    assert quality_report.blocked_count == d("0")
    assert quality_report.average_quality_score == d("0.882361")
    assert quality_report.reason_codes == ("research_source_quality_pass",)

    row = quality_report.rows[0]
    assert type(row) is ResearchSourceQualityScoreRow
    assert row.claim_id == "market-alpha"
    assert row.evidence_count == d("3")
    assert row.source_count == d("3")
    assert row.source_family_count == d("3")
    assert row.latest_observed_at == GENERATED_AT - timedelta(minutes=30)
    assert row.latest_source_age_seconds == d("1800")
    assert row.recency_score == d("0.930556")
    assert row.diversity_score == d("1.000000")
    assert row.directness_score == d("0.866667")
    assert row.primary_source_score == d("0.666667")
    assert row.missing_source_count == d("0")
    assert row.conflict_flag_count == d("0")
    assert row.missing_source_penalty_score == d("0.000000")
    assert row.conflict_flag_penalty_score == d("0.000000")
    assert row.quality_score == d("0.882361")
    assert row.status == "pass"
    assert row.evidence_ids == ("evidence-001", "evidence-002", "evidence-003")
    assert row.source_ids == ("analysis-note", "official-resolution", "venue-notice")
    assert row.source_families == ("analysis", "official", "venue")
    assert row.reason_codes == (
        "direct_source_support",
        "diverse_sources",
        "fresh_sources",
        "input_manual_reviewed",
        "primary_source_support",
        "research_source_quality_pass",
    )


def test_missing_sources_conflicts_staleness_and_secondary_only_block_claim() -> None:
    quality_report = report(
        (
            evidence(
                1,
                claim_id="market-risk",
                source_id=None,
                source_family=None,
                source_type="secondary",
                directness="indirect",
                observed_at=GENERATED_AT - timedelta(days=2),
                conflict_flag=True,
                reason_codes=("needs_resolution",),
            ),
        ),
    )

    row = quality_report.rows[0]
    assert quality_report.status == "blocked"
    assert quality_report.blocked_count == d("1")
    assert quality_report.average_quality_score == d("0.000000")
    assert row.claim_id == "market-risk"
    assert row.evidence_count == d("1")
    assert row.source_count == d("0")
    assert row.source_family_count == d("0")
    assert row.recency_score == d("0.000000")
    assert row.diversity_score == d("0.000000")
    assert row.directness_score == d("0.600000")
    assert row.primary_source_score == d("0.000000")
    assert row.missing_source_count == d("1")
    assert row.conflict_flag_count == d("1")
    assert row.missing_source_penalty_score == d("0.250000")
    assert row.conflict_flag_penalty_score == d("0.150000")
    assert row.quality_score == d("0.000000")
    assert row.status == "blocked"
    assert row.reason_codes == (
        "conflict_flags_present",
        "input_needs_resolution",
        "missing_sources_present",
        "not_enough_source_diversity",
        "research_source_quality_blocked",
        "secondary_or_missing_primary_sources",
        "stale_sources",
    )


def test_rows_reason_counts_and_payload_are_deterministic_without_float_values() -> None:
    quality_report = report(
        (
            evidence(
                3,
                claim_id="z-claim",
                source_id=None,
                source_family=None,
                source_type="secondary",
                directness="context",
                observed_at=GENERATED_AT - timedelta(days=2),
                conflict_flag=True,
            ),
            evidence(
                1,
                claim_id="a-claim",
                source_id="a-official",
                source_family="official",
                reason_codes=("zeta", "alpha"),
            ),
            evidence(
                2,
                claim_id="z-claim",
                source_id="z-official",
                source_family="official",
                source_type="primary",
                directness="direct",
            ),
        ),
    )

    payload = research_source_quality_report_payload(quality_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.claim_id for row in quality_report.rows) == ("a-claim", "z-claim")
    assert quality_report.rows[0].reason_codes == (
        "fresh_sources",
        "input_alpha",
        "input_zeta",
        "not_enough_source_diversity",
        "primary_source_support",
        "research_source_quality_watch",
    )
    assert tuple(
        (count.reason_code, count.count)
        for count in quality_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["quality_score"] == str(quality_report.rows[0].quality_score)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded


def test_validation_rejects_bad_types_unknown_enums_future_times_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="recency_weight"):
        config(recency_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_quality_score"):
        config(pass_quality_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="missing_source_penalty"):
        config(missing_source_penalty=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="claim_id"):
        evidence(1, claim_id=" market-alpha")
    with pytest.raises(ValueError, match="source_type"):
        evidence(1, source_type="tertiary")
    with pytest.raises(ValueError, match="directness"):
        evidence(1, directness="hearsay")
    with pytest.raises(ValueError, match="observed_at"):
        evidence(1, observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((evidence(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="conflict_flag"):
        replace(evidence(1), conflict_flag=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        evidence(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    quality_report = report((evidence(1),))

    with pytest.raises(FrozenInstanceError):
        quality_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        quality_report.rows[0].quality_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="quality_score"):
        replace(quality_report.rows[0], quality_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(quality_report, status="pass")


def test_owned_module_has_no_network_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_quality_policy.py"
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

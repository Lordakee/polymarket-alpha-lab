from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
import inspect
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_candidate_duplicate_exposure_report import (
    ResearchCandidateDuplicateExposureConfig,
    ResearchCandidateExposureAggregate,
    build_research_candidate_duplicate_exposure_report,
    research_candidate_duplicate_exposure_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def aggregate(
    candidate_label: str,
    *,
    catalyst_classes: tuple[str, ...],
    domain_classes: tuple[str, ...],
    source_classes: tuple[str, ...],
    settlement_linkage_classes: tuple[str, ...],
    liquidity_pressure_score: Decimal = Decimal("0.100000"),
    cost_pressure_score: Decimal = Decimal("0.100000"),
) -> ResearchCandidateExposureAggregate:
    return ResearchCandidateExposureAggregate(
        candidate_label=candidate_label,
        catalyst_classes=catalyst_classes,
        domain_classes=domain_classes,
        source_classes=source_classes,
        settlement_linkage_classes=settlement_linkage_classes,
        liquidity_pressure_score=liquidity_pressure_score,
        cost_pressure_score=cost_pressure_score,
    )


def test_build_report_blocks_candidate_pairs_with_full_overlap_and_pressure() -> None:
    report = build_research_candidate_duplicate_exposure_report(
        (
            aggregate(
                "candidate-alpha",
                catalyst_classes=("central-bank", "inflation-print"),
                domain_classes=("macro",),
                source_classes=("official-release", "market-depth"),
                settlement_linkage_classes=("same-resolution-rule",),
                liquidity_pressure_score=Decimal("0.900000"),
                cost_pressure_score=Decimal("0.700000"),
            ),
            aggregate(
                "candidate-beta",
                catalyst_classes=("central-bank", "inflation-print"),
                domain_classes=("macro",),
                source_classes=("official-release", "market-depth"),
                settlement_linkage_classes=("same-resolution-rule",),
                liquidity_pressure_score=Decimal("0.800000"),
                cost_pressure_score=Decimal("0.900000"),
            ),
            aggregate(
                "candidate-gamma",
                catalyst_classes=("weather",),
                domain_classes=("sports",),
                source_classes=("venue-status",),
                settlement_linkage_classes=("independent-resolution-rule",),
            ),
        ),
        config=ResearchCandidateDuplicateExposureConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.status == "block"
    assert report.candidate_count == Decimal("3")
    assert report.pair_count == Decimal("3")
    assert report.block_count == Decimal("1")
    assert report.watch_count == Decimal("0")
    assert report.pass_count == Decimal("2")
    assert report.max_duplicate_exposure_score == Decimal("0.970000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    top_row = report.rows[0]
    assert top_row.candidate_a_label == "candidate-alpha"
    assert top_row.candidate_b_label == "candidate-beta"
    assert top_row.status == "block"
    assert top_row.catalyst_overlap_ratio == Decimal("1.000000")
    assert top_row.domain_overlap_ratio == Decimal("1.000000")
    assert top_row.source_class_overlap_ratio == Decimal("1.000000")
    assert top_row.settlement_linkage_ratio == Decimal("1.000000")
    assert top_row.liquidity_cost_pressure_score == Decimal("0.850000")
    assert top_row.reason_codes == (
        "aggregate_catalyst_overlap_block",
        "domain_overlap_block",
        "duplicate_exposure_block",
        "liquidity_cost_pressure_watch",
        "settlement_linkage_block",
        "source_class_overlap_block",
    )


def test_build_report_watches_partial_overlap_without_block_level_duplication() -> None:
    report = build_research_candidate_duplicate_exposure_report(
        (
            aggregate(
                "candidate-alpha",
                catalyst_classes=("central-bank", "inflation-print"),
                domain_classes=("macro",),
                source_classes=("official-release", "market-depth"),
                settlement_linkage_classes=("same-resolution-rule",),
                liquidity_pressure_score=Decimal("0.500000"),
                cost_pressure_score=Decimal("0.400000"),
            ),
            aggregate(
                "candidate-beta",
                catalyst_classes=("central-bank", "growth-print"),
                domain_classes=("macro",),
                source_classes=("official-release", "polling-average"),
                settlement_linkage_classes=("separate-resolution-rule",),
                liquidity_pressure_score=Decimal("0.600000"),
                cost_pressure_score=Decimal("0.500000"),
            ),
        ),
        config=ResearchCandidateDuplicateExposureConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.status == "watch"
    assert report.watch_count == Decimal("1")
    assert report.rows[0].status == "watch"
    assert report.rows[0].duplicate_exposure_score == Decimal("0.485000")
    assert report.rows[0].reason_codes == (
        "aggregate_catalyst_overlap_watch",
        "domain_overlap_block",
        "duplicate_exposure_watch",
        "source_class_overlap_watch",
    )


def test_payload_and_digest_are_deterministic_and_public_safe() -> None:
    rows = (
        aggregate(
            "candidate-beta",
            catalyst_classes=("central-bank", "inflation-print"),
            domain_classes=("macro",),
            source_classes=("official-release", "market-depth"),
            settlement_linkage_classes=("same-resolution-rule",),
            liquidity_pressure_score=Decimal("0.800000"),
            cost_pressure_score=Decimal("0.900000"),
        ),
        aggregate(
            "candidate-alpha",
            catalyst_classes=("inflation-print", "central-bank"),
            domain_classes=("macro",),
            source_classes=("market-depth", "official-release"),
            settlement_linkage_classes=("same-resolution-rule",),
            liquidity_pressure_score=Decimal("0.900000"),
            cost_pressure_score=Decimal("0.700000"),
        ),
    )
    config = ResearchCandidateDuplicateExposureConfig()

    report_a = build_research_candidate_duplicate_exposure_report(
        rows,
        config=config,
        generated_at=GENERATED_AT,
    )
    report_b = build_research_candidate_duplicate_exposure_report(
        tuple(reversed(rows)),
        config=config,
        generated_at=GENERATED_AT,
    )

    payload_a = research_candidate_duplicate_exposure_report_payload(report_a)
    payload_b = research_candidate_duplicate_exposure_report_payload(report_b)

    assert payload_a == payload_b
    assert report_a.report_digest == report_b.report_digest
    assert len(report_a.report_digest) == 64
    assert payload_a["report_digest"] == report_a.report_digest
    assert payload_a["rows"][0]["candidate_a_label"] == "candidate-alpha"
    assert payload_a["rows"][0]["candidate_b_label"] == "candidate-beta"

    payload_text = repr(payload_a).lower()
    forbidden_payload_fragments = (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "wallet",
        "auth",
        "order",
        "trade",
    )
    for fragment in forbidden_payload_fragments:
        assert fragment not in payload_text


def test_empty_report_passes_without_rows() -> None:
    report = build_research_candidate_duplicate_exposure_report(
        (),
        config=ResearchCandidateDuplicateExposureConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.status == "pass"
    assert report.reason_codes == ("no_candidate_overlap_pairs",)
    assert report.candidate_count == Decimal("0")
    assert report.pair_count == Decimal("0")
    assert report.max_duplicate_exposure_score == Decimal("0.000000")
    assert report.rows == ()


def test_rejects_non_decimal_numeric_inputs_and_unsafe_public_identifiers() -> None:
    with pytest.raises(ValueError, match="liquidity_pressure_score must be a Decimal"):
        aggregate(
            "candidate-alpha",
            catalyst_classes=("central-bank",),
            domain_classes=("macro",),
            source_classes=("official-release",),
            settlement_linkage_classes=("same-resolution-rule",),
            liquidity_pressure_score=0.5,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="raw public identifiers"):
        aggregate(
            "event_id:abc123",
            catalyst_classes=("central-bank",),
            domain_classes=("macro",),
            source_classes=("official-release",),
            settlement_linkage_classes=("same-resolution-rule",),
        )


def test_dataclasses_are_frozen_and_require_hard_report_only_flags() -> None:
    row = aggregate(
        "candidate-alpha",
        catalyst_classes=("central-bank",),
        domain_classes=("macro",),
        source_classes=("official-release",),
        settlement_linkage_classes=("same-resolution-rule",),
    )

    with pytest.raises(FrozenInstanceError):
        row.candidate_label = "candidate-beta"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        ResearchCandidateExposureAggregate(
            candidate_label="candidate-alpha",
            catalyst_classes=("central-bank",),
            domain_classes=("macro",),
            source_classes=("official-release",),
            settlement_linkage_classes=("same-resolution-rule",),
            liquidity_pressure_score=Decimal("0.100000"),
            cost_pressure_score=Decimal("0.100000"),
            paper_only=False,
        )


def test_module_has_no_execution_or_persistence_surface() -> None:
    module = __import__(
        "polymarket_alpha_lab.research_candidate_duplicate_exposure_report",
        fromlist=["unused"],
    )
    source = Path(inspect.getsourcefile(module) or "").read_text(encoding="utf-8").lower()

    forbidden_fragments = (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "psycopg",
        "sqlite3",
        "supabase",
        "wallet",
        "auth",
        "order",
        "trade",
        "execute",
        "buy",
        "sell",
        "recommend",
        "position_size",
        "position sizing",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

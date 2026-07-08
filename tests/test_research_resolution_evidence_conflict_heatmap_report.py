from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_evidence_conflict_heatmap_report import (
    PUBLIC_STATUSES,
    ResearchResolutionEvidenceConflictHeatmapCell,
    ResearchResolutionEvidenceConflictHeatmapConfig,
    ResearchResolutionEvidenceConflictHeatmapObservation,
    ResearchResolutionEvidenceConflictHeatmapReasonCodeCount,
    ResearchResolutionEvidenceConflictHeatmapReport,
    build_research_resolution_evidence_conflict_heatmap_report,
    research_resolution_evidence_conflict_heatmap_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionEvidenceConflictHeatmapConfig:
    values = {
        "config_version": "research-resolution-evidence-conflict-heatmap-v0",
        "watch_conflict_heat_score": d("0.250000"),
        "block_conflict_heat_score": d("0.600000"),
        "low_confidence_floor": d("0.500000"),
        "high_confidence_floor": d("0.750000"),
    }
    values.update(overrides)
    return ResearchResolutionEvidenceConflictHeatmapConfig(**values)


def observation(
    *,
    event_category: str = "weather",
    resolution_evidence_category: str = "official_notice",
    team_confidence_score: Decimal = d("0.900000"),
    evidence_conflict_score: Decimal = d("0.050000"),
    evidence_item_count: Decimal = d("10"),
    disputed_evidence_count: Decimal = d("0"),
    stale_evidence_count: Decimal = d("0"),
    team_review_count: Decimal = d("2"),
    observed_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
) -> ResearchResolutionEvidenceConflictHeatmapObservation:
    return ResearchResolutionEvidenceConflictHeatmapObservation(
        event_category=event_category,
        resolution_evidence_category=resolution_evidence_category,
        team_confidence_score=team_confidence_score,
        evidence_conflict_score=evidence_conflict_score,
        evidence_item_count=evidence_item_count,
        disputed_evidence_count=disputed_evidence_count,
        stale_evidence_count=stale_evidence_count,
        team_review_count=team_review_count,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        reason_codes=reason_codes,
    )


def report(
    observations: tuple[object, ...],
    *,
    cfg: ResearchResolutionEvidenceConflictHeatmapConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionEvidenceConflictHeatmapReport:
    return build_research_resolution_evidence_conflict_heatmap_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_heatmap() -> None:
    heatmap_report = report(())

    assert type(heatmap_report) is ResearchResolutionEvidenceConflictHeatmapReport
    assert heatmap_report.generated_at == GENERATED_AT
    assert heatmap_report.config_version == "research-resolution-evidence-conflict-heatmap-v0"
    assert heatmap_report.cell_count == d("0")
    assert heatmap_report.observation_count == d("0")
    assert heatmap_report.event_category_count == d("0")
    assert heatmap_report.resolution_evidence_category_count == d("0")
    assert heatmap_report.confidence_band_count == d("0")
    assert heatmap_report.pass_count == d("0")
    assert heatmap_report.watch_count == d("0")
    assert heatmap_report.block_count == d("0")
    assert heatmap_report.total_evidence_item_count == d("0")
    assert heatmap_report.total_disputed_evidence_count == d("0")
    assert heatmap_report.total_stale_evidence_count == d("0")
    assert heatmap_report.average_team_confidence_score is None
    assert heatmap_report.average_conflict_heat_score is None
    assert heatmap_report.status == "block"
    assert heatmap_report.reason_codes == (
        "no_resolution_evidence_conflict_observations",
    )
    assert heatmap_report.reason_code_counts == (
        ResearchResolutionEvidenceConflictHeatmapReasonCodeCount(
            reason_code="no_resolution_evidence_conflict_observations",
            count=d("1"),
        ),
    )
    assert heatmap_report.cells == ()
    assert heatmap_report.paper_only is True
    assert heatmap_report.report_only is True
    assert heatmap_report.readonly is True
    assert len(heatmap_report.derived_validation_digest) == 64


def test_heatmap_cells_statuses_counts_and_scores_are_deterministic() -> None:
    heatmap_report = report(
        (
            observation(
                event_category="weather",
                resolution_evidence_category="news_summary",
                team_confidence_score=d("0.600000"),
                evidence_conflict_score=d("0.300000"),
                evidence_item_count=d("5"),
                disputed_evidence_count=d("1"),
                stale_evidence_count=d("0"),
                team_review_count=d("1"),
                reason_codes=("manual_review",),
            ),
            observation(
                event_category="weather",
                resolution_evidence_category="official_notice",
                team_confidence_score=d("0.900000"),
                evidence_conflict_score=d("0.050000"),
                evidence_item_count=d("10"),
                disputed_evidence_count=d("0"),
                stale_evidence_count=d("0"),
                team_review_count=d("2"),
            ),
            observation(
                event_category="sports",
                resolution_evidence_category="contradictory_notice",
                team_confidence_score=d("0.350000"),
                evidence_conflict_score=d("0.700000"),
                evidence_item_count=d("4"),
                disputed_evidence_count=d("3"),
                stale_evidence_count=d("2"),
                team_review_count=d("3"),
                reason_codes=("needs_resolution",),
            ),
        ),
    )

    assert PUBLIC_STATUSES == ("pass", "watch", "block")
    assert heatmap_report.status == "block"
    assert heatmap_report.cell_count == d("3")
    assert heatmap_report.observation_count == d("3")
    assert heatmap_report.event_category_count == d("2")
    assert heatmap_report.resolution_evidence_category_count == d("3")
    assert heatmap_report.confidence_band_count == d("3")
    assert heatmap_report.pass_count == d("1")
    assert heatmap_report.watch_count == d("1")
    assert heatmap_report.block_count == d("1")
    assert heatmap_report.total_evidence_item_count == d("19")
    assert heatmap_report.total_disputed_evidence_count == d("4")
    assert heatmap_report.total_stale_evidence_count == d("2")
    assert heatmap_report.average_team_confidence_score == d("0.616667")
    assert heatmap_report.average_conflict_heat_score == d("0.366667")

    assert tuple(
        (
            cell.event_category,
            cell.resolution_evidence_category,
            cell.team_confidence_band,
            cell.status,
            cell.conflict_heat_score,
        )
        for cell in heatmap_report.cells
    ) == (
        ("sports", "contradictory_notice", "low_confidence", "block", d("0.750000")),
        ("weather", "news_summary", "medium_confidence", "watch", d("0.300000")),
        ("weather", "official_notice", "high_confidence", "pass", d("0.050000")),
    )

    block_cell = heatmap_report.cells[0]
    assert type(block_cell) is ResearchResolutionEvidenceConflictHeatmapCell
    assert block_cell.observation_count == d("1")
    assert block_cell.evidence_item_count == d("4")
    assert block_cell.disputed_evidence_count == d("3")
    assert block_cell.stale_evidence_count == d("2")
    assert block_cell.team_review_count == d("3")
    assert block_cell.average_team_confidence_score == d("0.350000")
    assert block_cell.average_evidence_conflict_score == d("0.700000")
    assert block_cell.disputed_evidence_share == d("0.750000")
    assert block_cell.stale_evidence_share == d("0.500000")
    assert block_cell.reason_codes == (
        "evidence_dispute_share_block",
        "input_needs_resolution",
        "low_team_confidence",
        "resolution_evidence_conflict_heatmap_block",
        "stale_resolution_evidence_present",
    )


def test_public_payload_digest_is_stable_and_contains_no_raw_identifiers_or_floats() -> None:
    observations = (
        observation(
            event_category="weather",
            resolution_evidence_category="official_notice",
            team_confidence_score=d("0.900000"),
        ),
        observation(
            event_category="sports",
            resolution_evidence_category="contradictory_notice",
            team_confidence_score=d("0.350000"),
            evidence_conflict_score=d("0.700000"),
            evidence_item_count=d("4"),
            disputed_evidence_count=d("3"),
            stale_evidence_count=d("2"),
            team_review_count=d("3"),
        ),
    )
    first = report(observations)
    second = report(tuple(reversed(observations)))

    first_payload = research_resolution_evidence_conflict_heatmap_report_payload(first)
    second_payload = research_resolution_evidence_conflict_heatmap_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload == second_payload
    assert research_resolution_evidence_conflict_heatmap_report_payload(first_payload) == first_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["cells"][0]["conflict_heat_score"] == "0.750000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in encoded
    for leaked in ("event_id", "source_id", "market_slug", "market_id"):
        assert leaked not in encoded


def test_validation_rejects_non_decimal_inputs_leakage_statuses_future_times_and_flags() -> None:
    with pytest.raises(ValueError, match="watch_conflict_heat_score"):
        config(watch_conflict_heat_score=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="team_confidence_score"):
        observation(team_confidence_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_item_count"):
        observation(evidence_item_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="event_category"):
        observation(event_category="event_id:abc123")
    with pytest.raises(ValueError, match="resolution_evidence_category"):
        observation(resolution_evidence_category="wallet_auth")
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(), paper_only=False)

    heatmap_report = report((observation(),))
    with pytest.raises(ValueError, match="status"):
        replace(heatmap_report.cells[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(heatmap_report, status="blocked")
    for unsafe_value in (
        "trade-order",
        "private-key",
        "auth_token",
        "source_id:secret",
        "market_slug:hidden",
    ):
        with pytest.raises(ValueError):
            research_resolution_evidence_conflict_heatmap_report_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    "status": "pass",
                    "unsafe_value": unsafe_value,
                },
            )


def test_public_dataclasses_are_frozen_and_manual_consistency_is_enforced() -> None:
    heatmap_report = report(
        (
            observation(
                event_category="sports",
                resolution_evidence_category="contradictory_notice",
                team_confidence_score=d("0.350000"),
                evidence_conflict_score=d("0.700000"),
                evidence_item_count=d("4"),
                disputed_evidence_count=d("3"),
                stale_evidence_count=d("2"),
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        heatmap_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        heatmap_report.cells[0].conflict_heat_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(heatmap_report.cells[0], status="pass")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(heatmap_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report_only"):
        research_resolution_evidence_conflict_heatmap_report_payload(
            {"paper_only": True, "report_only": False, "readonly": True},
        )
    with pytest.raises(ValueError, match="numeric"):
        research_resolution_evidence_conflict_heatmap_report_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "count": 1},
        )


def test_owned_module_has_no_live_execution_network_or_database_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_evidence_conflict_heatmap_report.py"
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
        "sqlalchemy",
        "psycopg",
        "mysql",
        "redis",
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

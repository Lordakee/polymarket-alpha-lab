from __future__ import annotations

import ast
import dataclasses
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.team_research_calibration_snapshot import (
    DEFAULT_TEAM_RESEARCH_CALIBRATION_SNAPSHOT_CONFIG_VERSION,
    TeamResearchCalibrationConfidenceBand,
    TeamResearchCalibrationOutcome,
    TeamResearchCalibrationSnapshotConfig,
    TeamResearchCalibrationSnapshotReport,
    TeamResearchCalibrationStaleUnresolvedItem,
    TeamResearchCalibrationTeamSnapshot,
    build_team_research_calibration_snapshot,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> TeamResearchCalibrationSnapshotConfig:
    values = {
        "config_version": DEFAULT_TEAM_RESEARCH_CALIBRATION_SNAPSHOT_CONFIG_VERSION,
        "stale_after_seconds": 86_400,
    }
    values.update(overrides)
    return TeamResearchCalibrationSnapshotConfig(**values)


def _outcome(
    outcome_id: str,
    *,
    status: str = "pending",
    team_id: str = "politics",
    observed_at: datetime | None = None,
    resolved_at: datetime | None = None,
    actual_outcome: str | None = None,
    predicted_yes_probability: Decimal | None = None,
    confidence: Decimal | None = None,
) -> TeamResearchCalibrationOutcome:
    observed = observed_at if observed_at is not None else GENERATED_AT - timedelta(hours=1)
    return TeamResearchCalibrationOutcome(
        outcome_id=outcome_id,
        team_id=team_id,
        outcome_status=status,
        observed_at=observed,
        resolved_at=resolved_at,
        actual_outcome=actual_outcome,
        predicted_yes_probability=predicted_yes_probability,
        confidence=confidence,
    )


def test_snapshot_summarizes_resolved_pending_brier_and_confidence_bands() -> None:
    stale_pending = _outcome(
        "politics-stale",
        observed_at=GENERATED_AT - timedelta(days=2),
        confidence=d("0.40"),
    )
    fresh_pending = _outcome(
        "crypto-fresh",
        team_id="crypto_btc",
        observed_at=GENERATED_AT - timedelta(hours=2),
        confidence=d("0.80"),
    )
    scored_yes = _outcome(
        "politics-yes",
        status="resolved",
        observed_at=GENERATED_AT - timedelta(days=3),
        resolved_at=GENERATED_AT - timedelta(hours=6),
        actual_outcome="yes",
        predicted_yes_probability=d("0.800000"),
        confidence=d("0.900000"),
    )
    scored_no = _outcome(
        "politics-no",
        status="resolved",
        observed_at=GENERATED_AT - timedelta(days=4),
        resolved_at=GENERATED_AT - timedelta(hours=5),
        actual_outcome="no",
        predicted_yes_probability=d("0.300000"),
        confidence=d("0.600000"),
    )
    unscored = _outcome(
        "macro-unscored",
        team_id="macro_rates",
        status="resolved",
        observed_at=GENERATED_AT - timedelta(days=5),
        resolved_at=GENERATED_AT - timedelta(hours=4),
        actual_outcome="yes",
        predicted_yes_probability=None,
        confidence=None,
    )

    report = build_team_research_calibration_snapshot(
        (fresh_pending, unscored, scored_no, stale_pending, scored_yes),
        config=_config(stale_after_seconds=86_400),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, TeamResearchCalibrationSnapshotReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_TEAM_RESEARCH_CALIBRATION_SNAPSHOT_CONFIG_VERSION
    assert report.outcome_count == 5
    assert report.resolved_count == 3
    assert report.pending_count == 2
    assert report.scored_resolved_count == 2
    assert report.unscored_resolved_count == 1
    assert report.pending_ratio == d("0.400000")
    assert report.average_brier_like_score == d("0.065000")
    assert report.stale_after_seconds == 86_400
    assert report.latest_observed_at == GENERATED_AT - timedelta(hours=2)
    assert report.latest_resolved_at == GENERATED_AT - timedelta(hours=4)
    assert report.stale_unresolved_count == 1
    assert report.confidence_band_count == 3
    assert report.unbanded_confidence_count == 1
    assert report.team_count == 3
    assert report.scored_team_count == 1
    assert report.stale_unresolved_team_count == 1
    assert report.team_snapshots == (
        TeamResearchCalibrationTeamSnapshot(
            team_id="crypto_btc",
            outcome_count=1,
            resolved_count=0,
            pending_count=1,
            scored_resolved_count=0,
            unscored_resolved_count=0,
            stale_unresolved_count=0,
            pending_ratio=d("1.000000"),
            average_brier_like_score=None,
        ),
        TeamResearchCalibrationTeamSnapshot(
            team_id="macro_rates",
            outcome_count=1,
            resolved_count=1,
            pending_count=0,
            scored_resolved_count=0,
            unscored_resolved_count=1,
            stale_unresolved_count=0,
            pending_ratio=d("0.000000"),
            average_brier_like_score=None,
        ),
        TeamResearchCalibrationTeamSnapshot(
            team_id="politics",
            outcome_count=3,
            resolved_count=2,
            pending_count=1,
            scored_resolved_count=2,
            unscored_resolved_count=0,
            stale_unresolved_count=1,
            pending_ratio=d("0.333333"),
            average_brier_like_score=d("0.065000"),
        ),
    )
    assert report.stale_unresolved_items == (
        TeamResearchCalibrationStaleUnresolvedItem(
            outcome_id="politics-stale",
            team_id="politics",
            observed_at=GENERATED_AT - timedelta(days=2),
            unresolved_age_seconds=172_800,
        ),
    )
    assert report.confidence_bands == (
        TeamResearchCalibrationConfidenceBand(
            band_label="low",
            lower_confidence=d("0.000000"),
            upper_confidence=d("0.500000"),
            outcome_count=1,
            resolved_count=0,
            pending_count=1,
            scored_resolved_count=0,
            average_brier_like_score=None,
        ),
        TeamResearchCalibrationConfidenceBand(
            band_label="medium",
            lower_confidence=d("0.500000"),
            upper_confidence=d("0.750000"),
            outcome_count=1,
            resolved_count=1,
            pending_count=0,
            scored_resolved_count=1,
            average_brier_like_score=d("0.090000"),
        ),
        TeamResearchCalibrationConfidenceBand(
            band_label="high",
            lower_confidence=d("0.750000"),
            upper_confidence=d("1.000000"),
            outcome_count=2,
            resolved_count=1,
            pending_count=1,
            scored_resolved_count=1,
            average_brier_like_score=d("0.040000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    _assert_no_recommendation_or_execution_payload(report)


def test_snapshot_preserves_whole_seconds_across_the_full_datetime_range() -> None:
    generated_at = datetime.max.replace(tzinfo=UTC)
    observed_at = datetime.min.replace(tzinfo=UTC)

    report = build_team_research_calibration_snapshot(
        (_outcome("long-range-pending", observed_at=observed_at),),
        config=_config(stale_after_seconds=0),
        generated_at=generated_at,
    )

    delta = generated_at - observed_at
    expected_whole_seconds = delta.days * 86_400 + delta.seconds
    assert report.stale_unresolved_items[0].unresolved_age_seconds == (
        expected_whole_seconds
    )


def test_snapshot_omits_brier_like_values_when_forecast_probability_is_absent() -> None:
    report = build_team_research_calibration_snapshot(
        (
            _outcome(
                "resolved-unscored",
                status="resolved",
                resolved_at=GENERATED_AT - timedelta(minutes=5),
                actual_outcome="yes",
                confidence=d("0.80"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.resolved_count == 1
    assert report.scored_resolved_count == 0
    assert report.unscored_resolved_count == 1
    assert report.pending_ratio == d("0.000000")
    assert report.average_brier_like_score is None
    assert report.confidence_bands[2].average_brier_like_score is None


def test_empty_snapshot_is_report_only_with_no_synthetic_ratios_or_scores() -> None:
    report = build_team_research_calibration_snapshot(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.outcome_count == 0
    assert report.resolved_count == 0
    assert report.pending_count == 0
    assert report.pending_ratio is None
    assert report.average_brier_like_score is None
    assert report.stale_unresolved_items == ()
    assert tuple(row.outcome_count for row in report.confidence_bands) == (0, 0, 0)
    assert report.team_count == 0
    assert report.team_snapshots == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_snapshot_normalizes_offset_datetimes_to_utc_and_rejects_naive_or_future_times() -> None:
    report = build_team_research_calibration_snapshot(
        (
            _outcome(
                "offset-pending",
                observed_at=datetime(
                    2026,
                    7,
                    2,
                    13,
                    30,
                    tzinfo=timezone(timedelta(hours=2)),
                ),
                confidence=d("0.50"),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.stale_unresolved_items == ()
    assert report.confidence_bands[1].outcome_count == 1

    with pytest.raises(ValueError, match="timezone-aware"):
        build_team_research_calibration_snapshot(
            (_outcome("naive", observed_at=datetime(2026, 7, 2, 11, 0)),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        build_team_research_calibration_snapshot(
            (
                _outcome(
                    "future",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_team_research_calibration_snapshot(
            (),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )


def test_snapshot_validates_exact_types_statuses_probabilities_and_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        TeamResearchCalibrationSnapshotConfig(
            config_version=_StringSubclass(
                DEFAULT_TEAM_RESEARCH_CALIBRATION_SNAPSHOT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="stale_after_seconds"):
        TeamResearchCalibrationSnapshotConfig(stale_after_seconds=_IntSubclass(86_400))
    with pytest.raises(ValueError, match="outcome_status"):
        _outcome("bad-status", status="unknown")
    with pytest.raises(ValueError, match="actual_outcome"):
        _outcome(
            "missing-actual",
            status="resolved",
            resolved_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="resolved_at"):
        _outcome(
            "pending-resolved-at",
            status="pending",
            resolved_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="predicted_yes_probability"):
        _outcome(
            "bad-probability",
            predicted_yes_probability=d("1.000001"),
        )
    with pytest.raises(ValueError, match="confidence"):
        _outcome("bad-confidence", confidence=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_outcome("not-paper"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_outcome("not-report"), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_outcome("not-readonly"), readonly=False)
    with pytest.raises(ValueError, match="outcomes"):
        build_team_research_calibration_snapshot(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_snapshot_rejects_duplicate_outcomes_and_inconsistent_manual_reports() -> None:
    first = _outcome("duplicate")
    duplicate = _outcome("duplicate", team_id="crypto_btc")

    with pytest.raises(ValueError, match="outcome_id"):
        build_team_research_calibration_snapshot(
            (first, duplicate),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="pending_count"):
        TeamResearchCalibrationSnapshotReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_TEAM_RESEARCH_CALIBRATION_SNAPSHOT_CONFIG_VERSION,
            outcome_count=1,
            resolved_count=1,
            pending_count=1,
            scored_resolved_count=0,
            unscored_resolved_count=1,
            pending_ratio=d("1.000000"),
            average_brier_like_score=None,
            stale_unresolved_count=0,
            stale_unresolved_items=(),
            confidence_bands=(),
            unbanded_confidence_count=0,
        )


def test_snapshot_dataclasses_are_frozen() -> None:
    values = (
        _config(),
        _outcome("pending"),
        TeamResearchCalibrationStaleUnresolvedItem(
            outcome_id="pending",
            team_id="politics",
            observed_at=GENERATED_AT - timedelta(days=2),
            unresolved_age_seconds=172_800,
        ),
        TeamResearchCalibrationConfidenceBand(
            band_label="low",
            lower_confidence=d("0.000000"),
            upper_confidence=d("0.500000"),
            outcome_count=0,
            resolved_count=0,
            pending_count=0,
            scored_resolved_count=0,
            average_brier_like_score=None,
        ),
        build_team_research_calibration_snapshot(
            (),
            config=_config(),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]


def test_snapshot_module_public_exports_and_scope_are_report_only() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "team_research_calibration_snapshot.py"
    )
    imported_roots: set[str] = set()
    module = ast.parse(module_path.read_text())
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "eth_account",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "websocket",
        "websockets",
    }

    import polymarket_alpha_lab.team_research_calibration_snapshot as api

    assert api.__all__ == (
        "DEFAULT_TEAM_RESEARCH_CALIBRATION_SNAPSHOT_CONFIG_VERSION",
        "TeamResearchCalibrationConfidenceBand",
        "TeamResearchCalibrationOutcome",
        "TeamResearchCalibrationSnapshotConfig",
        "TeamResearchCalibrationSnapshotReport",
        "TeamResearchCalibrationStaleUnresolvedItem",
        "TeamResearchCalibrationTeamSnapshot",
        "build_team_research_calibration_snapshot",
    )


def _assert_no_recommendation_or_execution_payload(
    report: TeamResearchCalibrationSnapshotReport,
) -> None:
    blocked_fragments = (
        "recommend",
        "rank",
        "execution",
        "order",
        "wallet",
        "private",
    )
    payload = dataclasses.asdict(report)
    keys: list[str] = []

    def collect(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                keys.append(str(key))
                collect(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                collect(item)

    collect(payload)
    assert not any(
        fragment in key.lower()
        for key in keys
        for fragment in blocked_fragments
    )

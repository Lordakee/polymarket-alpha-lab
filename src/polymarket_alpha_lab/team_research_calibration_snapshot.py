"""Report-only calibration snapshots for Phase 1 team research outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_TEAM_RESEARCH_CALIBRATION_SNAPSHOT_CONFIG_VERSION = (
    "team-research-calibration-snapshot-v0"
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
OUTCOME_STATUSES = ("pending", "resolved")
ACTUAL_OUTCOMES = ("no", "yes")
CONFIDENCE_BAND_BOUNDS = (
    ("low", ZERO, Decimal("0.500000")),
    ("medium", Decimal("0.500000"), Decimal("0.750000")),
    ("high", Decimal("0.750000"), ONE),
)

__all__ = (
    "DEFAULT_TEAM_RESEARCH_CALIBRATION_SNAPSHOT_CONFIG_VERSION",
    "TeamResearchCalibrationConfidenceBand",
    "TeamResearchCalibrationOutcome",
    "TeamResearchCalibrationSnapshotConfig",
    "TeamResearchCalibrationSnapshotReport",
    "TeamResearchCalibrationStaleUnresolvedItem",
    "TeamResearchCalibrationTeamSnapshot",
    "build_team_research_calibration_snapshot",
)


@dataclass(frozen=True)
class TeamResearchCalibrationSnapshotConfig:
    config_version: str = DEFAULT_TEAM_RESEARCH_CALIBRATION_SNAPSHOT_CONFIG_VERSION
    stale_after_seconds: int = 86_400
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("stale_after_seconds", self.stale_after_seconds)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamResearchCalibrationOutcome:
    outcome_id: str
    team_id: str
    outcome_status: str
    observed_at: datetime
    resolved_at: datetime | None = None
    actual_outcome: str | None = None
    predicted_yes_probability: Decimal | None = None
    confidence: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("outcome_id", self.outcome_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_outcome_status("outcome_status", self.outcome_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolved_at",
            _as_optional_utc("resolved_at", self.resolved_at),
        )
        object.__setattr__(
            self,
            "actual_outcome",
            _normalize_optional_actual_outcome("actual_outcome", self.actual_outcome),
        )
        object.__setattr__(
            self,
            "predicted_yes_probability",
            _normalize_optional_probability(
                "predicted_yes_probability",
                self.predicted_yes_probability,
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_optional_probability("confidence", self.confidence),
        )
        _validate_outcome_shape(self)
        _require_hard_flags("outcome", self)


@dataclass(frozen=True)
class TeamResearchCalibrationStaleUnresolvedItem:
    outcome_id: str
    team_id: str
    observed_at: datetime
    unresolved_age_seconds: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("outcome_id", self.outcome_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_nonnegative_int("unresolved_age_seconds", self.unresolved_age_seconds)
        _require_hard_flags("stale_unresolved_item", self)


@dataclass(frozen=True)
class TeamResearchCalibrationConfidenceBand:
    band_label: str
    lower_confidence: Decimal
    upper_confidence: Decimal
    outcome_count: int
    resolved_count: int
    pending_count: int
    scored_resolved_count: int
    average_brier_like_score: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("band_label", self.band_label)
        object.__setattr__(
            self,
            "lower_confidence",
            _normalize_probability("lower_confidence", self.lower_confidence),
        )
        object.__setattr__(
            self,
            "upper_confidence",
            _normalize_probability("upper_confidence", self.upper_confidence),
        )
        if self.upper_confidence <= self.lower_confidence:
            raise ValueError("upper_confidence must be greater than lower_confidence")
        _require_nonnegative_int("outcome_count", self.outcome_count)
        _require_nonnegative_int("resolved_count", self.resolved_count)
        _require_nonnegative_int("pending_count", self.pending_count)
        _require_nonnegative_int("scored_resolved_count", self.scored_resolved_count)
        object.__setattr__(
            self,
            "average_brier_like_score",
            _normalize_optional_probability(
                "average_brier_like_score",
                self.average_brier_like_score,
            ),
        )
        _validate_confidence_band_consistency(self)
        _require_hard_flags("confidence_band", self)


@dataclass(frozen=True)
class TeamResearchCalibrationTeamSnapshot:
    team_id: str
    outcome_count: int
    resolved_count: int
    pending_count: int
    scored_resolved_count: int
    unscored_resolved_count: int
    stale_unresolved_count: int
    pending_ratio: Decimal | None
    average_brier_like_score: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        for field_name in (
            "outcome_count",
            "resolved_count",
            "pending_count",
            "scored_resolved_count",
            "unscored_resolved_count",
            "stale_unresolved_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "pending_ratio",
            _normalize_optional_probability("pending_ratio", self.pending_ratio),
        )
        object.__setattr__(
            self,
            "average_brier_like_score",
            _normalize_optional_probability(
                "average_brier_like_score",
                self.average_brier_like_score,
            ),
        )
        _validate_team_snapshot_consistency(self)
        _require_hard_flags("team_snapshot", self)


@dataclass(frozen=True)
class TeamResearchCalibrationSnapshotReport:
    generated_at: datetime
    config_version: str
    outcome_count: int
    resolved_count: int
    pending_count: int
    scored_resolved_count: int
    unscored_resolved_count: int
    pending_ratio: Decimal | None
    average_brier_like_score: Decimal | None
    stale_unresolved_count: int
    stale_unresolved_items: tuple[TeamResearchCalibrationStaleUnresolvedItem, ...]
    confidence_bands: tuple[TeamResearchCalibrationConfidenceBand, ...]
    unbanded_confidence_count: int
    team_count: int = 0
    scored_team_count: int = 0
    stale_unresolved_team_count: int = 0
    team_snapshots: tuple[TeamResearchCalibrationTeamSnapshot, ...] = ()
    stale_after_seconds: int = 0
    latest_observed_at: datetime | None = None
    latest_resolved_at: datetime | None = None
    confidence_band_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "outcome_count",
            "resolved_count",
            "pending_count",
            "scored_resolved_count",
            "unscored_resolved_count",
            "stale_unresolved_count",
            "team_count",
            "scored_team_count",
            "stale_unresolved_team_count",
            "unbanded_confidence_count",
            "stale_after_seconds",
            "confidence_band_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_resolved_at",
            _as_optional_utc("latest_resolved_at", self.latest_resolved_at),
        )
        object.__setattr__(
            self,
            "pending_ratio",
            _normalize_optional_probability("pending_ratio", self.pending_ratio),
        )
        object.__setattr__(
            self,
            "average_brier_like_score",
            _normalize_optional_probability(
                "average_brier_like_score",
                self.average_brier_like_score,
            ),
        )
        object.__setattr__(
            self,
            "team_snapshots",
            _normalize_team_snapshots(self.team_snapshots),
        )
        object.__setattr__(
            self,
            "stale_unresolved_items",
            _normalize_stale_unresolved_items(self.stale_unresolved_items),
        )
        object.__setattr__(
            self,
            "confidence_bands",
            _normalize_confidence_bands(self.confidence_bands),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_team_research_calibration_snapshot(
    outcomes: list[TeamResearchCalibrationOutcome]
    | tuple[TeamResearchCalibrationOutcome, ...],
    *,
    config: TeamResearchCalibrationSnapshotConfig,
    generated_at: datetime,
) -> TeamResearchCalibrationSnapshotReport:
    if type(config) is not TeamResearchCalibrationSnapshotConfig:
        raise ValueError("config must be a TeamResearchCalibrationSnapshotConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_outcomes = _normalize_outcomes(outcomes)
    _validate_outcome_timing(normalized_outcomes, generated_at=generated_at_utc)
    ordered_outcomes = tuple(sorted(normalized_outcomes, key=_outcome_sort_key))
    resolved = tuple(row for row in ordered_outcomes if row.outcome_status == "resolved")
    pending = tuple(row for row in ordered_outcomes if row.outcome_status == "pending")
    scored_resolved = tuple(row for row in resolved if _has_brier_inputs(row))
    unscored_resolved_count = len(resolved) - len(scored_resolved)
    stale_items = _stale_unresolved_items(
        pending,
        generated_at=generated_at_utc,
        stale_after_seconds=config.stale_after_seconds,
    )
    team_snapshots = _team_snapshot_rows(ordered_outcomes, stale_items)
    confidence_bands, unbanded_confidence_count = _confidence_band_rows(ordered_outcomes)

    return TeamResearchCalibrationSnapshotReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        outcome_count=len(ordered_outcomes),
        stale_after_seconds=config.stale_after_seconds,
        latest_observed_at=_latest_datetime_or_none(
            tuple(row.observed_at for row in ordered_outcomes),
        ),
        latest_resolved_at=_latest_datetime_or_none(
            tuple(row.resolved_at for row in resolved if row.resolved_at is not None),
        ),
        resolved_count=len(resolved),
        pending_count=len(pending),
        scored_resolved_count=len(scored_resolved),
        unscored_resolved_count=unscored_resolved_count,
        pending_ratio=_ratio_or_none(len(pending), len(ordered_outcomes)),
        average_brier_like_score=_average_brier_like_score(scored_resolved),
        stale_unresolved_count=len(stale_items),
        team_count=len(team_snapshots),
        scored_team_count=sum(1 for row in team_snapshots if row.scored_resolved_count > 0),
        stale_unresolved_team_count=sum(
            1 for row in team_snapshots if row.stale_unresolved_count > 0
        ),
        team_snapshots=team_snapshots,
        stale_unresolved_items=stale_items,
        confidence_bands=confidence_bands,
        confidence_band_count=len(confidence_bands),
        unbanded_confidence_count=unbanded_confidence_count,
    )


def _team_snapshot_rows(
    outcomes: tuple[TeamResearchCalibrationOutcome, ...],
    stale_items: tuple[TeamResearchCalibrationStaleUnresolvedItem, ...],
) -> tuple[TeamResearchCalibrationTeamSnapshot, ...]:
    team_ids = tuple(sorted({row.team_id for row in outcomes}))
    stale_counts = {
        team_id: sum(1 for item in stale_items if item.team_id == team_id)
        for team_id in team_ids
    }
    rows = []
    for team_id in team_ids:
        team_outcomes = tuple(row for row in outcomes if row.team_id == team_id)
        resolved = tuple(row for row in team_outcomes if row.outcome_status == "resolved")
        pending = tuple(row for row in team_outcomes if row.outcome_status == "pending")
        scored_resolved = tuple(row for row in resolved if _has_brier_inputs(row))
        rows.append(
            TeamResearchCalibrationTeamSnapshot(
                team_id=team_id,
                outcome_count=len(team_outcomes),
                resolved_count=len(resolved),
                pending_count=len(pending),
                scored_resolved_count=len(scored_resolved),
                unscored_resolved_count=len(resolved) - len(scored_resolved),
                stale_unresolved_count=stale_counts.get(team_id, 0),
                pending_ratio=_ratio_or_none(len(pending), len(team_outcomes)),
                average_brier_like_score=_average_brier_like_score(scored_resolved),
            ),
        )
    return tuple(rows)


def _stale_unresolved_items(
    pending: tuple[TeamResearchCalibrationOutcome, ...],
    *,
    generated_at: datetime,
    stale_after_seconds: int,
) -> tuple[TeamResearchCalibrationStaleUnresolvedItem, ...]:
    stale_items = []
    for outcome in pending:
        age_seconds = _age_seconds(generated_at, outcome.observed_at)
        if age_seconds > stale_after_seconds:
            stale_items.append(
                TeamResearchCalibrationStaleUnresolvedItem(
                    outcome_id=outcome.outcome_id,
                    team_id=outcome.team_id,
                    observed_at=outcome.observed_at,
                    unresolved_age_seconds=age_seconds,
                ),
            )
    return tuple(
        sorted(
            stale_items,
            key=lambda row: (-row.unresolved_age_seconds, row.team_id, row.outcome_id),
        ),
    )


def _confidence_band_rows(
    outcomes: tuple[TeamResearchCalibrationOutcome, ...],
) -> tuple[tuple[TeamResearchCalibrationConfidenceBand, ...], int]:
    bands: list[TeamResearchCalibrationConfidenceBand] = []
    unbanded_count = sum(1 for row in outcomes if row.confidence is None)
    for label, lower, upper in CONFIDENCE_BAND_BOUNDS:
        band_outcomes = tuple(
            row for row in outcomes if row.confidence is not None and _in_band(row.confidence, lower, upper)
        )
        resolved = tuple(row for row in band_outcomes if row.outcome_status == "resolved")
        pending = tuple(row for row in band_outcomes if row.outcome_status == "pending")
        scored_resolved = tuple(row for row in resolved if _has_brier_inputs(row))
        bands.append(
            TeamResearchCalibrationConfidenceBand(
                band_label=label,
                lower_confidence=lower,
                upper_confidence=upper,
                outcome_count=len(band_outcomes),
                resolved_count=len(resolved),
                pending_count=len(pending),
                scored_resolved_count=len(scored_resolved),
                average_brier_like_score=_average_brier_like_score(scored_resolved),
            ),
        )
    return tuple(bands), unbanded_count


def _in_band(value: Decimal, lower: Decimal, upper: Decimal) -> bool:
    if upper == ONE:
        return lower <= value <= upper
    return lower <= value < upper


def _normalize_outcomes(
    outcomes: list[TeamResearchCalibrationOutcome]
    | tuple[TeamResearchCalibrationOutcome, ...],
) -> tuple[TeamResearchCalibrationOutcome, ...]:
    if type(outcomes) not in (list, tuple):
        raise ValueError("outcomes must be a list or tuple")
    normalized = tuple(outcomes)
    seen_outcome_ids: set[str] = set()
    for outcome in normalized:
        if type(outcome) is not TeamResearchCalibrationOutcome:
            raise ValueError("outcomes must contain TeamResearchCalibrationOutcome")
        _require_hard_flags("outcome", outcome)
        if outcome.outcome_id in seen_outcome_ids:
            raise ValueError("outcome_id values must be unique")
        seen_outcome_ids.add(outcome.outcome_id)
    return normalized


def _validate_outcome_timing(
    outcomes: tuple[TeamResearchCalibrationOutcome, ...],
    *,
    generated_at: datetime,
) -> None:
    for outcome in outcomes:
        if outcome.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        if outcome.resolved_at is not None:
            if outcome.resolved_at > generated_at:
                raise ValueError("resolved_at must not be in the future")
            if outcome.resolved_at < outcome.observed_at:
                raise ValueError("resolved_at must not be before observed_at")


def _validate_outcome_shape(outcome: TeamResearchCalibrationOutcome) -> None:
    if outcome.outcome_status == "resolved":
        if outcome.resolved_at is None:
            raise ValueError("resolved_at is required for resolved outcomes")
        if outcome.actual_outcome is None:
            raise ValueError("actual_outcome is required for resolved outcomes")
    else:
        if outcome.resolved_at is not None:
            raise ValueError("resolved_at must be absent for pending outcomes")
        if outcome.actual_outcome is not None:
            raise ValueError("actual_outcome must be absent for pending outcomes")


def _validate_confidence_band_consistency(
    band: TeamResearchCalibrationConfidenceBand,
) -> None:
    if band.resolved_count + band.pending_count != band.outcome_count:
        raise ValueError("confidence band counts must reconcile")
    if band.scored_resolved_count > band.resolved_count:
        raise ValueError("scored_resolved_count must not exceed resolved_count")
    if band.scored_resolved_count == 0 and band.average_brier_like_score is not None:
        raise ValueError("average_brier_like_score must be absent without scored outcomes")
    if band.scored_resolved_count > 0 and band.average_brier_like_score is None:
        raise ValueError("average_brier_like_score is required for scored outcomes")


def _validate_team_snapshot_consistency(
    snapshot: TeamResearchCalibrationTeamSnapshot,
) -> None:
    if snapshot.resolved_count + snapshot.pending_count != snapshot.outcome_count:
        raise ValueError("team snapshot counts must reconcile")
    if snapshot.scored_resolved_count + snapshot.unscored_resolved_count != snapshot.resolved_count:
        raise ValueError("team snapshot scored resolved counts must reconcile")
    if snapshot.scored_resolved_count == 0 and snapshot.average_brier_like_score is not None:
        raise ValueError("average_brier_like_score must be absent without scored outcomes")
    if snapshot.scored_resolved_count > 0 and snapshot.average_brier_like_score is None:
        raise ValueError("average_brier_like_score is required for scored outcomes")
    if snapshot.outcome_count == 0:
        if snapshot.pending_ratio is not None:
            raise ValueError("pending_ratio must be absent without outcomes")
    elif snapshot.pending_ratio != _ratio_or_none(
        snapshot.pending_count,
        snapshot.outcome_count,
    ):
        raise ValueError("pending_ratio must match pending_count over outcome_count")


def _validate_report_consistency(report: TeamResearchCalibrationSnapshotReport) -> None:
    if report.resolved_count + report.pending_count != report.outcome_count:
        raise ValueError("pending_count and resolved_count must match outcome_count")
    if report.scored_resolved_count + report.unscored_resolved_count != report.resolved_count:
        raise ValueError("scored resolved counts must match resolved_count")
    if report.outcome_count == 0:
        if report.pending_ratio is not None:
            raise ValueError("pending_ratio must be absent without outcomes")
    elif report.pending_ratio != _ratio_or_none(report.pending_count, report.outcome_count):
        raise ValueError("pending_ratio must match pending_count over outcome_count")
    if report.scored_resolved_count == 0 and report.average_brier_like_score is not None:
        raise ValueError("average_brier_like_score must be absent without scored outcomes")
    if report.scored_resolved_count > 0 and report.average_brier_like_score is None:
        raise ValueError("average_brier_like_score is required for scored outcomes")
    if report.stale_unresolved_count != len(report.stale_unresolved_items):
        raise ValueError("stale_unresolved_count must match stale_unresolved_items")
    if report.confidence_band_count != len(report.confidence_bands):
        raise ValueError("confidence_band_count must match confidence_bands")
    if report.outcome_count == 0:
        if report.latest_observed_at is not None:
            raise ValueError("latest_observed_at must be absent without outcomes")
    elif report.latest_observed_at is None:
        raise ValueError("latest_observed_at is required with outcomes")
    if report.resolved_count == 0:
        if report.latest_resolved_at is not None:
            raise ValueError("latest_resolved_at must be absent without resolved outcomes")
    elif report.latest_resolved_at is None:
        raise ValueError("latest_resolved_at is required with resolved outcomes")
    if report.outcome_count != (
        sum(row.outcome_count for row in report.confidence_bands)
        + report.unbanded_confidence_count
    ):
        raise ValueError("confidence band counts must match outcome_count")
    if report.team_count != len(report.team_snapshots):
        raise ValueError("team_count must match team_snapshots")
    if report.scored_team_count != sum(
        1 for row in report.team_snapshots if row.scored_resolved_count > 0
    ):
        raise ValueError("scored_team_count must match team_snapshots")
    if report.stale_unresolved_team_count != sum(
        1 for row in report.team_snapshots if row.stale_unresolved_count > 0
    ):
        raise ValueError("stale_unresolved_team_count must match team_snapshots")
    if report.outcome_count != sum(row.outcome_count for row in report.team_snapshots):
        raise ValueError("team snapshot counts must match outcome_count")


def _normalize_stale_unresolved_items(
    items: tuple[TeamResearchCalibrationStaleUnresolvedItem, ...],
) -> tuple[TeamResearchCalibrationStaleUnresolvedItem, ...]:
    if type(items) is not tuple:
        raise ValueError("stale_unresolved_items must be a tuple")
    for item in items:
        if type(item) is not TeamResearchCalibrationStaleUnresolvedItem:
            raise ValueError(
                "stale_unresolved_items must contain TeamResearchCalibrationStaleUnresolvedItem",
            )
        _require_hard_flags("stale_unresolved_item", item)
    return tuple(sorted(items, key=lambda row: (-row.unresolved_age_seconds, row.team_id, row.outcome_id)))


def _normalize_team_snapshots(
    snapshots: tuple[TeamResearchCalibrationTeamSnapshot, ...],
) -> tuple[TeamResearchCalibrationTeamSnapshot, ...]:
    if type(snapshots) is not tuple:
        raise ValueError("team_snapshots must be a tuple")
    seen_team_ids: set[str] = set()
    for snapshot in snapshots:
        if type(snapshot) is not TeamResearchCalibrationTeamSnapshot:
            raise ValueError(
                "team_snapshots must contain TeamResearchCalibrationTeamSnapshot",
            )
        _require_hard_flags("team_snapshot", snapshot)
        if snapshot.team_id in seen_team_ids:
            raise ValueError("team_id values must be unique")
        seen_team_ids.add(snapshot.team_id)
    return tuple(sorted(snapshots, key=lambda row: row.team_id))


def _normalize_confidence_bands(
    bands: tuple[TeamResearchCalibrationConfidenceBand, ...],
) -> tuple[TeamResearchCalibrationConfidenceBand, ...]:
    if type(bands) is not tuple:
        raise ValueError("confidence_bands must be a tuple")
    for band in bands:
        if type(band) is not TeamResearchCalibrationConfidenceBand:
            raise ValueError(
                "confidence_bands must contain TeamResearchCalibrationConfidenceBand",
            )
        _require_hard_flags("confidence_band", band)
    return tuple(sorted(bands, key=lambda row: row.lower_confidence))


def _has_brier_inputs(outcome: TeamResearchCalibrationOutcome) -> bool:
    return (
        outcome.outcome_status == "resolved"
        and outcome.actual_outcome is not None
        and outcome.predicted_yes_probability is not None
    )


def _average_brier_like_score(
    outcomes: tuple[TeamResearchCalibrationOutcome, ...],
) -> Decimal | None:
    if not outcomes:
        return None
    scores = tuple(_brier_like_score(row) for row in outcomes)
    return _quantize_ratio(sum(scores, ZERO) / Decimal(len(scores)))


def _brier_like_score(outcome: TeamResearchCalibrationOutcome) -> Decimal:
    if outcome.actual_outcome is None or outcome.predicted_yes_probability is None:
        raise ValueError("brier-like inputs are required")
    actual_value = ONE if outcome.actual_outcome == "yes" else ZERO
    with localcontext(DECIMAL_CONTEXT):
        forecast_error = outcome.predicted_yes_probability - actual_value
        return forecast_error * forecast_error


def _ratio_or_none(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _quantize_ratio(Decimal(numerator) / Decimal(denominator))


def _latest_datetime_or_none(values: tuple[datetime, ...]) -> datetime | None:
    if not values:
        return None
    return max(_as_utc("datetime", value) for value in values)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(value)


def _normalize_optional_actual_outcome(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str or value not in ACTUAL_OUTCOMES:
        raise ValueError(f"{field_name} must be yes or no")
    return value


def _require_outcome_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in OUTCOME_STATUSES:
        raise ValueError(f"{field_name} must be pending or resolved")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> int:
    delta = generated_at - observed_at
    return delta.days * 86_400 + delta.seconds


def _outcome_sort_key(
    outcome: TeamResearchCalibrationOutcome,
) -> tuple[datetime, str, str]:
    return (outcome.observed_at, outcome.team_id, outcome.outcome_id)

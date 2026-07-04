"""Pure reducer for report-only tennis altitude ball-speed shift digests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_TENNIS_ALTITUDE_BALL_SPEED_SHIFT_DIGEST_CONFIG_VERSION = (
    "market-research-tennis-altitude-ball-speed-shift-digest-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
SIX_PLACES = Decimal("0.000001")

READY_REASON = "market_research_tennis_altitude_ball_speed_shift_digest_ready"
NO_INPUTS_REASON = "market_research_tennis_altitude_ball_speed_shift_digest_no_inputs"
HIGH_ALTITUDE_REASON = (
    "market_research_tennis_altitude_ball_speed_shift_digest_high_altitude"
)
BALL_SPEED_ACCELERATION_REASON = (
    "market_research_tennis_altitude_ball_speed_shift_digest_ball_speed_acceleration"
)
PRESSURE_WATCH_REASON = (
    "market_research_tennis_altitude_ball_speed_shift_digest_pressure_watch"
)
PRESSURE_BLOCKED_REASON = (
    "market_research_tennis_altitude_ball_speed_shift_digest_pressure_blocked"
)
STALE_OBSERVATION_REASON = (
    "market_research_tennis_altitude_ball_speed_shift_digest_stale_observation"
)
SOURCE_DEPTH_GAP_REASON = (
    "market_research_tennis_altitude_ball_speed_shift_digest_source_depth_gap"
)
CONFLICTING_SOURCES_REASON = (
    "market_research_tennis_altitude_ball_speed_shift_digest_conflicting_sources"
)
LOW_CONFIDENCE_REASON = (
    "market_research_tennis_altitude_ball_speed_shift_digest_low_confidence"
)

REASON_CODES = (
    BALL_SPEED_ACCELERATION_REASON,
    CONFLICTING_SOURCES_REASON,
    HIGH_ALTITUDE_REASON,
    LOW_CONFIDENCE_REASON,
    NO_INPUTS_REASON,
    PRESSURE_BLOCKED_REASON,
    PRESSURE_WATCH_REASON,
    READY_REASON,
    SOURCE_DEPTH_GAP_REASON,
    STALE_OBSERVATION_REASON,
)
NEXT_STEPS = {
    "ready": "allow_report_only_market_research_tennis_altitude_ball_speed_shift_digest",
    "watch": "watch_report_only_market_research_tennis_altitude_ball_speed_shift_digest",
    "blocked": "block_report_only_market_research_tennis_altitude_ball_speed_shift_digest",
}
SAFE_PUBLIC_REFERENCE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "-_.",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_TENNIS_ALTITUDE_BALL_SPEED_SHIFT_DIGEST_CONFIG_VERSION",
    "MarketResearchTennisAltitudeBallSpeedShiftDigestConfig",
    "MarketResearchTennisAltitudeBallSpeedShiftObservation",
    "MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount",
    "MarketResearchTennisAltitudeBallSpeedShiftReport",
    "MarketResearchTennisAltitudeBallSpeedShiftRow",
    "build_market_research_tennis_altitude_ball_speed_shift_digest",
    "market_research_tennis_altitude_ball_speed_shift_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchTennisAltitudeBallSpeedShiftDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_TENNIS_ALTITUDE_BALL_SPEED_SHIFT_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("86400.000000")
    high_altitude_meters_threshold: Decimal = Decimal("1000.000000")
    ball_speed_shift_ratio_watch_threshold: Decimal = Decimal("0.060000")
    altitude_ball_speed_pressure_watch_threshold: Decimal = Decimal("0.650000")
    altitude_ball_speed_pressure_blocked_threshold: Decimal = Decimal("0.850000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_confidence_score: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_ALTITUDE_BALL_SPEED_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_observation_age_seconds",
            "high_altitude_meters_threshold",
            "ball_speed_shift_ratio_watch_threshold",
            "min_source_count",
            "min_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "altitude_ball_speed_pressure_watch_threshold",
            "altitude_ball_speed_pressure_blocked_threshold",
            "min_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.altitude_ball_speed_pressure_blocked_threshold
            < self.altitude_ball_speed_pressure_watch_threshold
        ):
            raise ValueError(
                "altitude_ball_speed_pressure_blocked_threshold must be at least "
                "watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchTennisAltitudeBallSpeedShiftObservation(_NoSubclass):
    market_id: str
    tournament_key: str
    match_key: str
    venue_key: str
    public_evidence_reference: str
    observed_at: datetime
    match_start_at: datetime
    venue_altitude_meters: Decimal
    baseline_ball_speed_kph: Decimal
    current_ball_speed_kph: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    conflicting_source_count: Decimal
    confidence_score: Decimal
    observation_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "market_id",
            "tournament_key",
            "match_key",
            "venue_key",
            "observation_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_public_evidence_reference(
            "public_evidence_reference",
            self.public_evidence_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "match_start_at",
            _as_utc("match_start_at", self.match_start_at),
        )
        object.__setattr__(
            self,
            "venue_altitude_meters",
            _normalize_nonnegative_decimal(
                "venue_altitude_meters",
                self.venue_altitude_meters,
            ),
        )
        for field_name in ("baseline_ball_speed_kph", "current_ball_speed_kph"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_count",
            "independent_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_score",
            _normalize_ratio_decimal("confidence_score", self.confidence_score),
        )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        if self.conflicting_source_count > self.source_count:
            raise ValueError("conflicting_source_count must not exceed source_count")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchTennisAltitudeBallSpeedShiftRow(_NoSubclass):
    market_id: str
    tournament_key: str
    match_key: str
    venue_key: str
    digest_status: str
    observed_at: datetime
    match_start_at: datetime
    observation_age_seconds: Decimal
    venue_altitude_meters: Decimal
    baseline_ball_speed_kph: Decimal
    current_ball_speed_kph: Decimal
    ball_speed_shift_kph: Decimal
    ball_speed_shift_ratio: Decimal
    altitude_pressure_ratio: Decimal
    ball_speed_pressure_ratio: Decimal
    altitude_ball_speed_pressure_index: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    conflicting_source_count: Decimal
    confidence_score: Decimal
    redacted_public_evidence_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "tournament_key", "match_key", "venue_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "match_start_at",
            _as_utc("match_start_at", self.match_start_at),
        )
        for field_name in (
            "observation_age_seconds",
            "venue_altitude_meters",
            "source_count",
            "independent_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("baseline_ball_speed_kph", "current_ball_speed_kph"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("ball_speed_shift_kph", "ball_speed_shift_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "altitude_pressure_ratio",
            "ball_speed_pressure_ratio",
            "altitude_ball_speed_pressure_index",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_canonical_string(
            "redacted_public_evidence_reference",
            self.redacted_public_evidence_reference,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        if self.conflicting_source_count > self.source_count:
            raise ValueError("conflicting_source_count must not exceed source_count")
        if self.digest_status != _status_for_reason_codes(self.reason_codes):
            raise ValueError("digest_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "observation_ratio",
            _normalize_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchTennisAltitudeBallSpeedShiftReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    high_altitude_observation_count: Decimal
    ball_speed_shift_observation_count: Decimal
    pressure_watch_observation_count: Decimal
    pressure_blocked_observation_count: Decimal
    stale_observation_count: Decimal
    source_depth_gap_observation_count: Decimal
    conflict_observation_count: Decimal
    low_confidence_observation_count: Decimal
    average_ball_speed_shift_ratio: Decimal
    max_absolute_ball_speed_shift_ratio: Decimal
    average_confidence_score: Decimal
    max_altitude_ball_speed_pressure_index: Decimal
    max_observation_age_seconds: Decimal
    high_altitude_meters_threshold: Decimal
    ball_speed_shift_ratio_watch_threshold: Decimal
    altitude_ball_speed_pressure_watch_threshold: Decimal
    altitude_ball_speed_pressure_blocked_threshold: Decimal
    min_source_count: Decimal
    min_independent_source_count: Decimal
    min_confidence_score: Decimal
    rows: tuple[MarketResearchTennisAltitudeBallSpeedShiftRow, ...]
    observation_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "high_altitude_observation_count",
            "ball_speed_shift_observation_count",
            "pressure_watch_observation_count",
            "pressure_blocked_observation_count",
            "stale_observation_count",
            "source_depth_gap_observation_count",
            "conflict_observation_count",
            "low_confidence_observation_count",
            "average_ball_speed_shift_ratio",
            "max_absolute_ball_speed_shift_ratio",
            "max_altitude_ball_speed_pressure_index",
            "max_observation_age_seconds",
            "high_altitude_meters_threshold",
            "ball_speed_shift_ratio_watch_threshold",
            "altitude_ball_speed_pressure_watch_threshold",
            "altitude_ball_speed_pressure_blocked_threshold",
            "min_source_count",
            "min_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_confidence_score", "min_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "observation_config_versions",
            _normalize_observation_config_versions(self.observation_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_market_research_tennis_altitude_ball_speed_shift_digest(
    observations: list[MarketResearchTennisAltitudeBallSpeedShiftObservation]
    | tuple[MarketResearchTennisAltitudeBallSpeedShiftObservation, ...],
    *,
    config: MarketResearchTennisAltitudeBallSpeedShiftDigestConfig,
    generated_at: datetime,
) -> MarketResearchTennisAltitudeBallSpeedShiftReport:
    if type(config) is not MarketResearchTennisAltitudeBallSpeedShiftDigestConfig:
        raise ValueError(
            "config must be a MarketResearchTennisAltitudeBallSpeedShiftDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _observation_row(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    digest_status = _report_status(rows)
    return MarketResearchTennisAltitudeBallSpeedShiftReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        observation_count=_count(len(rows)),
        ready_observation_count=_row_status_count(rows, "ready"),
        watch_observation_count=_row_status_count(rows, "watch"),
        blocked_observation_count=_row_status_count(rows, "blocked"),
        high_altitude_observation_count=_reason_count(rows, HIGH_ALTITUDE_REASON),
        ball_speed_shift_observation_count=_reason_count(
            rows,
            BALL_SPEED_ACCELERATION_REASON,
        ),
        pressure_watch_observation_count=_reason_count(rows, PRESSURE_WATCH_REASON),
        pressure_blocked_observation_count=_reason_count(rows, PRESSURE_BLOCKED_REASON),
        stale_observation_count=_reason_count(rows, STALE_OBSERVATION_REASON),
        source_depth_gap_observation_count=_reason_count(rows, SOURCE_DEPTH_GAP_REASON),
        conflict_observation_count=_reason_count(rows, CONFLICTING_SOURCES_REASON),
        low_confidence_observation_count=_reason_count(rows, LOW_CONFIDENCE_REASON),
        average_ball_speed_shift_ratio=_average(
            tuple(abs(row.ball_speed_shift_ratio) for row in rows),
        ),
        max_absolute_ball_speed_shift_ratio=_max_absolute_ball_speed_shift_ratio(rows),
        average_confidence_score=_average(tuple(row.confidence_score for row in rows)),
        max_altitude_ball_speed_pressure_index=_max_pressure_index(rows),
        max_observation_age_seconds=config.max_observation_age_seconds,
        high_altitude_meters_threshold=config.high_altitude_meters_threshold,
        ball_speed_shift_ratio_watch_threshold=(
            config.ball_speed_shift_ratio_watch_threshold
        ),
        altitude_ball_speed_pressure_watch_threshold=(
            config.altitude_ball_speed_pressure_watch_threshold
        ),
        altitude_ball_speed_pressure_blocked_threshold=(
            config.altitude_ball_speed_pressure_blocked_threshold
        ),
        min_source_count=config.min_source_count,
        min_independent_source_count=config.min_independent_source_count,
        min_confidence_score=config.min_confidence_score,
        rows=rows,
        observation_config_versions=_observation_config_versions(normalized_observations),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_tennis_altitude_ball_speed_shift_digest_payload(
    report: MarketResearchTennisAltitudeBallSpeedShiftReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchTennisAltitudeBallSpeedShiftReport:
        raise ValueError(
            "report must be a MarketResearchTennisAltitudeBallSpeedShiftReport",
        )
    _require_hard_flags("report", report)
    return _stringify_decimals(asdict(report))


def _normalize_observations(
    observations: list[MarketResearchTennisAltitudeBallSpeedShiftObservation]
    | tuple[MarketResearchTennisAltitudeBallSpeedShiftObservation, ...],
) -> tuple[MarketResearchTennisAltitudeBallSpeedShiftObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchTennisAltitudeBallSpeedShiftObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchTennisAltitudeBallSpeedShiftObservation values",
            )
        _require_hard_flags("observation", item)
        if item.market_id in seen:
            raise ValueError("market_id values must be unique")
        seen.add(item.market_id)
    return normalized


def _observation_row(
    item: MarketResearchTennisAltitudeBallSpeedShiftObservation,
    *,
    config: MarketResearchTennisAltitudeBallSpeedShiftDigestConfig,
    generated_at: datetime,
) -> MarketResearchTennisAltitudeBallSpeedShiftRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    ball_speed_shift_kph = _quantize(
        item.current_ball_speed_kph - item.baseline_ball_speed_kph,
    )
    ball_speed_shift_ratio = _ratio(ball_speed_shift_kph, item.baseline_ball_speed_kph)
    altitude_pressure_ratio = _capped_ratio(
        item.venue_altitude_meters,
        config.high_altitude_meters_threshold,
    )
    ball_speed_pressure_ratio = _positive_shift_pressure_ratio(
        ball_speed_shift_ratio,
        config.ball_speed_shift_ratio_watch_threshold,
    )
    altitude_ball_speed_pressure_index = _ratio(
        altitude_pressure_ratio + ball_speed_pressure_ratio,
        TWO,
    )
    observation_age_seconds = _seconds_between(generated_at, item.observed_at)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        observation_age_seconds=observation_age_seconds,
        ball_speed_shift_ratio=ball_speed_shift_ratio,
        altitude_ball_speed_pressure_index=altitude_ball_speed_pressure_index,
    )
    return MarketResearchTennisAltitudeBallSpeedShiftRow(
        market_id=item.market_id,
        tournament_key=item.tournament_key,
        match_key=item.match_key,
        venue_key=item.venue_key,
        digest_status=_status_for_reason_codes(reason_codes),
        observed_at=item.observed_at,
        match_start_at=item.match_start_at,
        observation_age_seconds=observation_age_seconds,
        venue_altitude_meters=item.venue_altitude_meters,
        baseline_ball_speed_kph=item.baseline_ball_speed_kph,
        current_ball_speed_kph=item.current_ball_speed_kph,
        ball_speed_shift_kph=ball_speed_shift_kph,
        ball_speed_shift_ratio=ball_speed_shift_ratio,
        altitude_pressure_ratio=altitude_pressure_ratio,
        ball_speed_pressure_ratio=ball_speed_pressure_ratio,
        altitude_ball_speed_pressure_index=altitude_ball_speed_pressure_index,
        source_count=item.source_count,
        independent_source_count=item.independent_source_count,
        conflicting_source_count=item.conflicting_source_count,
        confidence_score=item.confidence_score,
        redacted_public_evidence_reference=_redacted_public_evidence_reference(
            item.public_evidence_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: MarketResearchTennisAltitudeBallSpeedShiftObservation,
    *,
    config: MarketResearchTennisAltitudeBallSpeedShiftDigestConfig,
    observation_age_seconds: Decimal,
    ball_speed_shift_ratio: Decimal,
    altitude_ball_speed_pressure_index: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.venue_altitude_meters >= config.high_altitude_meters_threshold:
        reason_codes.append(HIGH_ALTITUDE_REASON)
    if ball_speed_shift_ratio >= config.ball_speed_shift_ratio_watch_threshold:
        reason_codes.append(BALL_SPEED_ACCELERATION_REASON)
    if (
        altitude_ball_speed_pressure_index
        >= config.altitude_ball_speed_pressure_blocked_threshold
    ):
        reason_codes.append(PRESSURE_BLOCKED_REASON)
    elif (
        altitude_ball_speed_pressure_index
        >= config.altitude_ball_speed_pressure_watch_threshold
    ):
        reason_codes.append(PRESSURE_WATCH_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reason_codes.append(STALE_OBSERVATION_REASON)
    if (
        item.source_count < config.min_source_count
        or item.independent_source_count < config.min_independent_source_count
    ):
        reason_codes.append(SOURCE_DEPTH_GAP_REASON)
    if item.conflicting_source_count > ZERO:
        reason_codes.append(CONFLICTING_SOURCES_REASON)
    if item.confidence_score < config.min_confidence_score:
        reason_codes.append(LOW_CONFIDENCE_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return tuple(sorted(reason_codes))


def _row_sort_key(
    row: MarketResearchTennisAltitudeBallSpeedShiftRow,
) -> tuple[Decimal, Decimal, datetime, str]:
    return (
        _status_rank(row.digest_status),
        -row.altitude_ball_speed_pressure_index,
        row.match_start_at,
        row.market_id,
    )


def _status_rank(digest_status: str) -> Decimal:
    if digest_status == "blocked":
        return Decimal("0.000000")
    if digest_status == "watch":
        return Decimal("1.000000")
    return Decimal("2.000000")


def _report_status(
    rows: tuple[MarketResearchTennisAltitudeBallSpeedShiftRow, ...],
) -> str:
    if not rows or any(row.digest_status == "blocked" for row in rows):
        return "blocked"
    if any(row.digest_status == "watch" for row in rows):
        return "watch"
    return "ready"


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return "ready"
    blocked_reasons = {
        NO_INPUTS_REASON,
        PRESSURE_BLOCKED_REASON,
        STALE_OBSERVATION_REASON,
        SOURCE_DEPTH_GAP_REASON,
        CONFLICTING_SOURCES_REASON,
        LOW_CONFIDENCE_REASON,
    }
    if any(reason_code in blocked_reasons for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _reason_code_counts(
    rows: tuple[MarketResearchTennisAltitudeBallSpeedShiftRow, ...],
) -> tuple[MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    observation_count = _count(len(rows))
    return tuple(
        MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount(
            reason_code=reason_code,
            count=count,
            observation_ratio=_ratio(count, observation_count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _observation_config_versions(
    observations: tuple[MarketResearchTennisAltitudeBallSpeedShiftObservation, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (
                item.market_id,
                item.observation_config_version,
            )
            for item in observations
        ),
    )


def _row_status_count(
    rows: tuple[MarketResearchTennisAltitudeBallSpeedShiftRow, ...],
    digest_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.digest_status == digest_status))


def _reason_count(
    rows: tuple[MarketResearchTennisAltitudeBallSpeedShiftRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_absolute_ball_speed_shift_ratio(
    rows: tuple[MarketResearchTennisAltitudeBallSpeedShiftRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(abs(row.ball_speed_shift_ratio) for row in rows)


def _max_pressure_index(
    rows: tuple[MarketResearchTennisAltitudeBallSpeedShiftRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.altitude_ball_speed_pressure_index for row in rows)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(sum(values, ZERO), _count(len(values)))


def _normalize_rows(
    rows: tuple[MarketResearchTennisAltitudeBallSpeedShiftRow, ...],
) -> tuple[MarketResearchTennisAltitudeBallSpeedShiftRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchTennisAltitudeBallSpeedShiftRow:
            raise ValueError(
                "rows must contain MarketResearchTennisAltitudeBallSpeedShiftRow values",
            )
        _require_hard_flags("row", row)
        if row.market_id in seen:
            raise ValueError("row market_id values must be unique")
        seen.add(row.market_id)
    if tuple(sorted(normalized, key=_row_sort_key)) != normalized:
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_observation_config_versions(
    versions: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(versions) not in (list, tuple):
        raise ValueError("observation_config_versions must be a list or tuple")
    normalized = tuple(versions)
    for item in normalized:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("observation_config_versions must contain pairs")
        _require_canonical_string("market_id", item[0])
        _require_canonical_string("observation_config_version", item[1])
    if tuple(sorted(normalized)) != normalized:
        raise ValueError("observation_config_versions must be sorted")
    if len({item[0] for item in normalized}) != len(normalized):
        raise ValueError("observation_config_versions market_id values must be unique")
    return normalized


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(reason_code_counts)
    for item in normalized:
        if type(item) is not MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchTennisAltitudeBallSpeedShiftReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
    if tuple(sorted(normalized, key=lambda item: item.reason_code)) != normalized:
        raise ValueError("reason_code_counts must be sorted")
    if len({item.reason_code for item in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    if tuple(sorted(normalized)) != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _validate_report_consistency(
    report: MarketResearchTennisAltitudeBallSpeedShiftReport,
) -> None:
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.ready_observation_count != _row_status_count(report.rows, "ready"):
        raise ValueError("ready_observation_count must match rows")
    if report.watch_observation_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_observation_count must match rows")
    if report.blocked_observation_count != _row_status_count(report.rows, "blocked"):
        raise ValueError("blocked_observation_count must match rows")
    if report.high_altitude_observation_count != _reason_count(
        report.rows,
        HIGH_ALTITUDE_REASON,
    ):
        raise ValueError("high_altitude_observation_count must match rows")
    if report.ball_speed_shift_observation_count != _reason_count(
        report.rows,
        BALL_SPEED_ACCELERATION_REASON,
    ):
        raise ValueError("ball_speed_shift_observation_count must match rows")
    if report.pressure_watch_observation_count != _reason_count(
        report.rows,
        PRESSURE_WATCH_REASON,
    ):
        raise ValueError("pressure_watch_observation_count must match rows")
    if report.pressure_blocked_observation_count != _reason_count(
        report.rows,
        PRESSURE_BLOCKED_REASON,
    ):
        raise ValueError("pressure_blocked_observation_count must match rows")
    if report.stale_observation_count != _reason_count(
        report.rows,
        STALE_OBSERVATION_REASON,
    ):
        raise ValueError("stale_observation_count must match rows")
    if report.source_depth_gap_observation_count != _reason_count(
        report.rows,
        SOURCE_DEPTH_GAP_REASON,
    ):
        raise ValueError("source_depth_gap_observation_count must match rows")
    if report.conflict_observation_count != _reason_count(
        report.rows,
        CONFLICTING_SOURCES_REASON,
    ):
        raise ValueError("conflict_observation_count must match rows")
    if report.low_confidence_observation_count != _reason_count(
        report.rows,
        LOW_CONFIDENCE_REASON,
    ):
        raise ValueError("low_confidence_observation_count must match rows")
    if report.average_ball_speed_shift_ratio != _average(
        tuple(abs(row.ball_speed_shift_ratio) for row in report.rows),
    ):
        raise ValueError("average_ball_speed_shift_ratio must match rows")
    if (
        report.max_absolute_ball_speed_shift_ratio
        != _max_absolute_ball_speed_shift_ratio(report.rows)
    ):
        raise ValueError("max_absolute_ball_speed_shift_ratio must match rows")
    if report.average_confidence_score != _average(
        tuple(row.confidence_score for row in report.rows),
    ):
        raise ValueError("average_confidence_score must match rows")
    if report.max_altitude_ball_speed_pressure_index != _max_pressure_index(report.rows):
        raise ValueError("max_altitude_ball_speed_pressure_index must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _redacted_public_evidence_reference(value: str) -> str:
    if value and all(character in SAFE_PUBLIC_REFERENCE_CHARS for character in value):
        return value
    digest = sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _stringify_decimals(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_stringify_decimals(item) for item in value]
    if isinstance(value, list):
        return [_stringify_decimals(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _stringify_decimals(item) for key, item in value.items()}
    return value


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    return _quantize(Decimal(str((later - earlier).total_seconds())))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(SIX_PLACES)


def _ratio(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ZERO
    return (value / total).quantize(SIX_PLACES, rounding=ROUND_DOWN)


def _capped_ratio(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ONE
    ratio = value / total
    if ratio > ONE:
        return ONE
    if ratio < ZERO:
        return ZERO
    return ratio.quantize(SIX_PLACES, rounding=ROUND_DOWN)


def _positive_shift_pressure_ratio(value: Decimal, total: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    return _capped_ratio(value, total)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(SIX_PLACES, rounding=ROUND_DOWN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_public_evidence_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(_require_finite_decimal(field_name, value))


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in NEXT_STEPS:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} contains an unknown reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")

"""Pure Phase 1 tennis court speed-mismatch digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_TENNIS_COURT_SPEED_MISMATCH_DIGEST_CONFIG_VERSION = (
    "market-research-tennis-court-speed-mismatch-digest-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX_PLACES = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")

PASS_REASON = "market_research_tennis_court_speed_mismatch_digest_pass"
NO_INPUTS_REASON = "market_research_tennis_court_speed_mismatch_digest_no_inputs"
ABOVE_MARKET_SPEED_MISMATCH_REASON = (
    "market_research_tennis_court_speed_mismatch_digest_above_market_speed_mismatch"
)
BELOW_MARKET_SPEED_MISMATCH_REASON = (
    "market_research_tennis_court_speed_mismatch_digest_below_market_speed_mismatch"
)
BLOCKED_MISMATCH_REASON = (
    "market_research_tennis_court_speed_mismatch_digest_blocked_mismatch"
)
LOW_CONFIDENCE_REASON = (
    "market_research_tennis_court_speed_mismatch_digest_low_confidence"
)
SOURCE_DEPTH_GAP_REASON = (
    "market_research_tennis_court_speed_mismatch_digest_source_depth_gap"
)
STALE_OBSERVATION_REASON = (
    "market_research_tennis_court_speed_mismatch_digest_stale_observation"
)
SURFACE_HISTORY_GAP_REASON = (
    "market_research_tennis_court_speed_mismatch_digest_surface_history_gap"
)
WATCH_MISMATCH_REASON = (
    "market_research_tennis_court_speed_mismatch_digest_watch_mismatch"
)

REASON_CODES = (
    PASS_REASON,
    NO_INPUTS_REASON,
    ABOVE_MARKET_SPEED_MISMATCH_REASON,
    BELOW_MARKET_SPEED_MISMATCH_REASON,
    BLOCKED_MISMATCH_REASON,
    LOW_CONFIDENCE_REASON,
    SOURCE_DEPTH_GAP_REASON,
    STALE_OBSERVATION_REASON,
    SURFACE_HISTORY_GAP_REASON,
    WATCH_MISMATCH_REASON,
)
NEXT_STEPS = {
    "pass": "allow_report_only_market_research_tennis_court_speed_mismatch_digest",
    "watch": "watch_report_only_market_research_tennis_court_speed_mismatch_digest",
    "blocked": "block_report_only_market_research_tennis_court_speed_mismatch_digest",
}
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
COURT_SURFACES = ("clay", "grass", "hard")
PROBABILITY_EVENT_TYPES = ("match_probability", "set_probability")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_TENNIS_COURT_SPEED_MISMATCH_DIGEST_CONFIG_VERSION",
    "MarketResearchTennisCourtSpeedMismatchDigestConfig",
    "MarketResearchTennisCourtSpeedMismatchObservation",
    "MarketResearchTennisCourtSpeedMismatchReasonCodeCount",
    "MarketResearchTennisCourtSpeedMismatchReport",
    "MarketResearchTennisCourtSpeedMismatchRow",
    "build_market_research_tennis_court_speed_mismatch_digest",
    "market_research_tennis_court_speed_mismatch_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchTennisCourtSpeedMismatchDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_TENNIS_COURT_SPEED_MISMATCH_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("86400.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_surface_history_sample_count: Decimal = Decimal("3.000000")
    min_confidence_score: Decimal = Decimal("0.600000")
    watch_mismatch_ratio_threshold: Decimal = Decimal("0.030000")
    blocked_mismatch_ratio_threshold: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_COURT_SPEED_MISMATCH_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_observation_age_seconds",
            "min_source_count",
            "min_independent_source_count",
            "min_surface_history_sample_count",
            "watch_mismatch_ratio_threshold",
            "blocked_mismatch_ratio_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_confidence_score",
            _require_probability("min_confidence_score", self.min_confidence_score),
        )
        if self.watch_mismatch_ratio_threshold > self.blocked_mismatch_ratio_threshold:
            raise ValueError(
                "watch_mismatch_ratio_threshold must not exceed "
                "blocked_mismatch_ratio_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchTennisCourtSpeedMismatchObservation(_NoSubclass):
    market_id: str
    tournament_key: str
    match_key: str
    probability_event_type: str
    court_key: str
    court_surface: str
    public_evidence_reference: str
    observed_at: datetime
    match_start_at: datetime
    market_implied_court_speed_index: Decimal
    observed_court_speed_index: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    surface_history_sample_count: Decimal
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
            "court_key",
            "observation_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_probability_event_type("probability_event_type", self.probability_event_type)
        _require_court_surface("court_surface", self.court_surface)
        _require_text("public_evidence_reference", self.public_evidence_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "match_start_at",
            _as_utc("match_start_at", self.match_start_at),
        )
        for field_name in (
            "market_implied_court_speed_index",
            "observed_court_speed_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_count",
            "independent_source_count",
            "surface_history_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_score",
            _require_probability("confidence_score", self.confidence_score),
        )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchTennisCourtSpeedMismatchRow(_NoSubclass):
    market_id: str
    tournament_key: str
    match_key: str
    probability_event_type: str
    court_key: str
    court_surface: str
    digest_status: str
    observed_at: datetime
    match_start_at: datetime
    observation_age_seconds: Decimal
    market_implied_court_speed_index: Decimal
    observed_court_speed_index: Decimal
    speed_mismatch_points: Decimal
    speed_mismatch_ratio: Decimal
    absolute_speed_mismatch_ratio: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    surface_history_sample_count: Decimal
    confidence_score: Decimal
    redacted_public_evidence_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "market_id",
            "tournament_key",
            "match_key",
            "court_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_probability_event_type("probability_event_type", self.probability_event_type)
        _require_court_surface("court_surface", self.court_surface)
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "match_start_at",
            _as_utc("match_start_at", self.match_start_at),
        )
        for field_name in (
            "market_implied_court_speed_index",
            "observed_court_speed_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "observation_age_seconds",
            "absolute_speed_mismatch_ratio",
            "source_count",
            "independent_source_count",
            "surface_history_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("speed_mismatch_points", "speed_mismatch_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_score",
            _require_probability("confidence_score", self.confidence_score),
        )
        _require_text(
            "redacted_public_evidence_reference",
            self.redacted_public_evidence_reference,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchTennisCourtSpeedMismatchReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_probability("row_ratio", self.row_ratio))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchTennisCourtSpeedMismatchReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    above_market_speed_mismatch_count: Decimal
    below_market_speed_mismatch_count: Decimal
    watch_mismatch_count: Decimal
    blocked_mismatch_count: Decimal
    stale_observation_count: Decimal
    source_depth_gap_count: Decimal
    surface_history_gap_count: Decimal
    low_confidence_count: Decimal
    average_absolute_speed_mismatch_ratio: Decimal
    max_absolute_speed_mismatch_ratio: Decimal
    average_confidence_score: Decimal
    max_observation_age_seconds: Decimal
    min_source_count: Decimal
    min_independent_source_count: Decimal
    min_surface_history_sample_count: Decimal
    min_confidence_score: Decimal
    watch_mismatch_ratio_threshold: Decimal
    blocked_mismatch_ratio_threshold: Decimal
    rows: tuple[MarketResearchTennisCourtSpeedMismatchRow, ...]
    observation_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchTennisCourtSpeedMismatchReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TENNIS_COURT_SPEED_MISMATCH_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "above_market_speed_mismatch_count",
            "below_market_speed_mismatch_count",
            "watch_mismatch_count",
            "blocked_mismatch_count",
            "stale_observation_count",
            "source_depth_gap_count",
            "surface_history_gap_count",
            "low_confidence_count",
            "average_absolute_speed_mismatch_ratio",
            "max_absolute_speed_mismatch_ratio",
            "max_observation_age_seconds",
            "min_source_count",
            "min_independent_source_count",
            "min_surface_history_sample_count",
            "watch_mismatch_ratio_threshold",
            "blocked_mismatch_ratio_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_confidence_score",
            _require_probability("average_confidence_score", self.average_confidence_score),
        )
        object.__setattr__(
            self,
            "min_confidence_score",
            _require_probability("min_confidence_score", self.min_confidence_score),
        )
        if self.watch_mismatch_ratio_threshold > self.blocked_mismatch_ratio_threshold:
            raise ValueError(
                "watch_mismatch_ratio_threshold must not exceed "
                "blocked_mismatch_ratio_threshold",
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


def build_market_research_tennis_court_speed_mismatch_digest(
    observations: (
        list[MarketResearchTennisCourtSpeedMismatchObservation]
        | tuple[MarketResearchTennisCourtSpeedMismatchObservation, ...]
    ),
    *,
    config: MarketResearchTennisCourtSpeedMismatchDigestConfig,
    generated_at: datetime,
) -> MarketResearchTennisCourtSpeedMismatchReport:
    if type(config) is not MarketResearchTennisCourtSpeedMismatchDigestConfig:
        raise ValueError(
            "config must be a MarketResearchTennisCourtSpeedMismatchDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _observation_row(item, config=config, generated_at=generated_at_utc)
                for item in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    digest_status = _report_status(rows)
    return MarketResearchTennisCourtSpeedMismatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        observation_count=_count(len(rows)),
        pass_count=_row_status_count(rows, "pass"),
        watch_count=_row_status_count(rows, "watch"),
        blocked_count=_row_status_count(rows, "blocked"),
        above_market_speed_mismatch_count=_reason_count(
            rows,
            ABOVE_MARKET_SPEED_MISMATCH_REASON,
        ),
        below_market_speed_mismatch_count=_reason_count(
            rows,
            BELOW_MARKET_SPEED_MISMATCH_REASON,
        ),
        watch_mismatch_count=_reason_count(rows, WATCH_MISMATCH_REASON),
        blocked_mismatch_count=_reason_count(rows, BLOCKED_MISMATCH_REASON),
        stale_observation_count=_reason_count(rows, STALE_OBSERVATION_REASON),
        source_depth_gap_count=_reason_count(rows, SOURCE_DEPTH_GAP_REASON),
        surface_history_gap_count=_reason_count(rows, SURFACE_HISTORY_GAP_REASON),
        low_confidence_count=_reason_count(rows, LOW_CONFIDENCE_REASON),
        average_absolute_speed_mismatch_ratio=_average(
            tuple(row.absolute_speed_mismatch_ratio for row in rows),
        ),
        max_absolute_speed_mismatch_ratio=_max_row_decimal(
            rows,
            "absolute_speed_mismatch_ratio",
        ),
        average_confidence_score=_average(tuple(row.confidence_score for row in rows)),
        max_observation_age_seconds=config.max_observation_age_seconds,
        min_source_count=config.min_source_count,
        min_independent_source_count=config.min_independent_source_count,
        min_surface_history_sample_count=config.min_surface_history_sample_count,
        min_confidence_score=config.min_confidence_score,
        watch_mismatch_ratio_threshold=config.watch_mismatch_ratio_threshold,
        blocked_mismatch_ratio_threshold=config.blocked_mismatch_ratio_threshold,
        rows=rows,
        observation_config_versions=_observation_config_versions(normalized_observations),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_tennis_court_speed_mismatch_digest_payload(
    report: MarketResearchTennisCourtSpeedMismatchReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchTennisCourtSpeedMismatchReport:
        raise ValueError("report must be a MarketResearchTennisCourtSpeedMismatchReport")
    _require_hard_flags("report", report)
    return _payload_value(report)


def _normalize_observations(
    observations: (
        list[MarketResearchTennisCourtSpeedMismatchObservation]
        | tuple[MarketResearchTennisCourtSpeedMismatchObservation, ...]
    ),
) -> tuple[MarketResearchTennisCourtSpeedMismatchObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen_market_ids: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchTennisCourtSpeedMismatchObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchTennisCourtSpeedMismatchObservation values",
            )
        _require_hard_flags("observation", item)
        if item.market_id in seen_market_ids:
            raise ValueError("market_id values must be unique")
        seen_market_ids.add(item.market_id)
    return normalized


def _observation_row(
    item: MarketResearchTennisCourtSpeedMismatchObservation,
    *,
    config: MarketResearchTennisCourtSpeedMismatchDigestConfig,
    generated_at: datetime,
) -> MarketResearchTennisCourtSpeedMismatchRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    speed_mismatch_points = _quantize(
        item.observed_court_speed_index - item.market_implied_court_speed_index,
    )
    speed_mismatch_ratio = _ratio(
        speed_mismatch_points,
        item.market_implied_court_speed_index,
    )
    absolute_speed_mismatch_ratio = _quantize(abs(speed_mismatch_ratio))
    observation_age_seconds = _seconds_between(generated_at, item.observed_at)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        observation_age_seconds=observation_age_seconds,
        speed_mismatch_ratio=speed_mismatch_ratio,
        absolute_speed_mismatch_ratio=absolute_speed_mismatch_ratio,
    )
    return MarketResearchTennisCourtSpeedMismatchRow(
        market_id=item.market_id,
        tournament_key=item.tournament_key,
        match_key=item.match_key,
        probability_event_type=item.probability_event_type,
        court_key=item.court_key,
        court_surface=item.court_surface,
        digest_status=_status_for_reason_codes(reason_codes),
        observed_at=item.observed_at,
        match_start_at=item.match_start_at,
        observation_age_seconds=observation_age_seconds,
        market_implied_court_speed_index=item.market_implied_court_speed_index,
        observed_court_speed_index=item.observed_court_speed_index,
        speed_mismatch_points=speed_mismatch_points,
        speed_mismatch_ratio=speed_mismatch_ratio,
        absolute_speed_mismatch_ratio=absolute_speed_mismatch_ratio,
        source_count=item.source_count,
        independent_source_count=item.independent_source_count,
        surface_history_sample_count=item.surface_history_sample_count,
        confidence_score=item.confidence_score,
        redacted_public_evidence_reference=_redacted_public_evidence_reference(
            item.public_evidence_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: MarketResearchTennisCourtSpeedMismatchObservation,
    *,
    config: MarketResearchTennisCourtSpeedMismatchDigestConfig,
    observation_age_seconds: Decimal,
    speed_mismatch_ratio: Decimal,
    absolute_speed_mismatch_ratio: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if observation_age_seconds > config.max_observation_age_seconds:
        codes.append(STALE_OBSERVATION_REASON)
    if (
        item.source_count < config.min_source_count
        or item.independent_source_count < config.min_independent_source_count
    ):
        codes.append(SOURCE_DEPTH_GAP_REASON)
    if item.surface_history_sample_count < config.min_surface_history_sample_count:
        codes.append(SURFACE_HISTORY_GAP_REASON)
    if item.confidence_score < config.min_confidence_score:
        codes.append(LOW_CONFIDENCE_REASON)
    if (
        absolute_speed_mismatch_ratio > ZERO
        and absolute_speed_mismatch_ratio >= config.watch_mismatch_ratio_threshold
    ):
        if speed_mismatch_ratio > ZERO:
            codes.append(ABOVE_MARKET_SPEED_MISMATCH_REASON)
        elif speed_mismatch_ratio < ZERO:
            codes.append(BELOW_MARKET_SPEED_MISMATCH_REASON)
        if absolute_speed_mismatch_ratio >= config.blocked_mismatch_ratio_threshold:
            codes.append(BLOCKED_MISMATCH_REASON)
        else:
            codes.append(WATCH_MISMATCH_REASON)
    if not codes:
        codes.append(PASS_REASON)
    return tuple(sorted(codes))


def _reason_code_counts(
    rows: tuple[MarketResearchTennisCourtSpeedMismatchRow, ...],
) -> tuple[MarketResearchTennisCourtSpeedMismatchReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    row_count = _count(len(rows))
    return tuple(
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code=reason_code,
            count=count,
            row_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _observation_config_versions(
    observations: tuple[MarketResearchTennisCourtSpeedMismatchObservation, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (item.market_id, item.observation_config_version)
            for item in observations
        ),
    )


def _report_status(rows: tuple[MarketResearchTennisCourtSpeedMismatchRow, ...]) -> str:
    if not rows or any(row.digest_status == "blocked" for row in rows):
        return "blocked"
    if any(row.digest_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    blocked_reasons = {
        BLOCKED_MISMATCH_REASON,
        LOW_CONFIDENCE_REASON,
        SOURCE_DEPTH_GAP_REASON,
        STALE_OBSERVATION_REASON,
        SURFACE_HISTORY_GAP_REASON,
    }
    if any(reason_code in blocked_reasons for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _row_sort_key(
    row: MarketResearchTennisCourtSpeedMismatchRow,
) -> tuple[int, Decimal, datetime, str]:
    return (
        STATUS_RANK[row.digest_status],
        -row.absolute_speed_mismatch_ratio,
        row.match_start_at,
        row.market_id,
    )


def _row_status_count(
    rows: tuple[MarketResearchTennisCourtSpeedMismatchRow, ...],
    digest_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.digest_status == digest_status))


def _reason_count(
    rows: tuple[MarketResearchTennisCourtSpeedMismatchRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MarketResearchTennisCourtSpeedMismatchRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _ratio(total, _count(len(values)))


def _normalize_rows(
    rows: tuple[MarketResearchTennisCourtSpeedMismatchRow, ...],
) -> tuple[MarketResearchTennisCourtSpeedMismatchRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_market_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchTennisCourtSpeedMismatchRow:
            raise ValueError(
                "rows must contain MarketResearchTennisCourtSpeedMismatchRow values",
            )
        _require_hard_flags("row", row)
        if row.market_id in seen_market_ids:
            raise ValueError("row market_id values must be unique")
        seen_market_ids.add(row.market_id)
    return tuple(sorted(normalized, key=_row_sort_key))


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
    if len({item[0] for item in normalized}) != len(normalized):
        raise ValueError("observation_config_versions market_id values must be unique")
    return tuple(sorted(normalized))


def _normalize_reason_code_counts(
    reason_code_counts: tuple[MarketResearchTennisCourtSpeedMismatchReasonCodeCount, ...],
) -> tuple[MarketResearchTennisCourtSpeedMismatchReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(reason_code_counts)
    for item in normalized:
        if type(item) is not MarketResearchTennisCourtSpeedMismatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchTennisCourtSpeedMismatchReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
    if len({item.reason_code for item in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(normalized))


def _validate_row_consistency(row: MarketResearchTennisCourtSpeedMismatchRow) -> None:
    if row.speed_mismatch_points != _quantize(
        row.observed_court_speed_index - row.market_implied_court_speed_index,
    ):
        raise ValueError("speed_mismatch_points must match speed index inputs")
    if row.speed_mismatch_ratio != _ratio(
        row.speed_mismatch_points,
        row.market_implied_court_speed_index,
    ):
        raise ValueError("speed_mismatch_ratio must match speed_mismatch_points")
    if row.absolute_speed_mismatch_ratio != _quantize(abs(row.speed_mismatch_ratio)):
        raise ValueError("absolute_speed_mismatch_ratio must match speed_mismatch_ratio")
    if row.digest_status != _status_for_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must match digest_status")


def _validate_report_consistency(
    report: MarketResearchTennisCourtSpeedMismatchReport,
) -> None:
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _row_status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.above_market_speed_mismatch_count != _reason_count(
        report.rows,
        ABOVE_MARKET_SPEED_MISMATCH_REASON,
    ):
        raise ValueError("above_market_speed_mismatch_count must match rows")
    if report.below_market_speed_mismatch_count != _reason_count(
        report.rows,
        BELOW_MARKET_SPEED_MISMATCH_REASON,
    ):
        raise ValueError("below_market_speed_mismatch_count must match rows")
    if report.watch_mismatch_count != _reason_count(report.rows, WATCH_MISMATCH_REASON):
        raise ValueError("watch_mismatch_count must match rows")
    if report.blocked_mismatch_count != _reason_count(
        report.rows,
        BLOCKED_MISMATCH_REASON,
    ):
        raise ValueError("blocked_mismatch_count must match rows")
    if report.stale_observation_count != _reason_count(report.rows, STALE_OBSERVATION_REASON):
        raise ValueError("stale_observation_count must match rows")
    if report.source_depth_gap_count != _reason_count(report.rows, SOURCE_DEPTH_GAP_REASON):
        raise ValueError("source_depth_gap_count must match rows")
    if report.surface_history_gap_count != _reason_count(
        report.rows,
        SURFACE_HISTORY_GAP_REASON,
    ):
        raise ValueError("surface_history_gap_count must match rows")
    if report.low_confidence_count != _reason_count(report.rows, LOW_CONFIDENCE_REASON):
        raise ValueError("low_confidence_count must match rows")
    if report.average_absolute_speed_mismatch_ratio != _average(
        tuple(row.absolute_speed_mismatch_ratio for row in report.rows),
    ):
        raise ValueError("average_absolute_speed_mismatch_ratio must match rows")
    if report.max_absolute_speed_mismatch_ratio != _max_row_decimal(
        report.rows,
        "absolute_speed_mismatch_ratio",
    ):
        raise ValueError("max_absolute_speed_mismatch_ratio must match rows")
    if report.average_confidence_score != _average(
        tuple(row.confidence_score for row in report.rows),
    ):
        raise ValueError("average_confidence_score must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if tuple(item[0] for item in report.observation_config_versions) != tuple(
        sorted(row.market_id for row in report.rows),
    ):
        raise ValueError("observation_config_versions must match rows")


def _redacted_public_evidence_reference(value: str) -> str:
    if all(character.isalnum() or character in "-_." for character in value):
        return value
    digest = sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_microseconds = (
        ((delta.days * 86400) + delta.seconds) * 1000000
    ) + delta.microseconds
    return _quantize(Decimal(total_microseconds) / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ZERO
    return _quantize(value / total)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(SIX_PLACES, rounding=ROUND_DOWN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty text")


def _require_probability_event_type(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in PROBABILITY_EVENT_TYPES:
        raise ValueError(f"{field_name} must be match_probability or set_probability")


def _require_court_surface(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in COURT_SURFACES:
        raise ValueError(f"{field_name} must be clay, grass, or hard")


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in NEXT_STEPS:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} contains an unknown reason code")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")

"""Pure in-memory baseball bullpen back-to-back fatigue digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_BACK_TO_BACK_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-bullpen-back-to-back-digest-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"

CLEAR_FATIGUE_STATUS = "clear"
WATCH_FATIGUE_STATUS = "watch"
HIGH_RISK_FATIGUE_STATUS = "high_risk"
BLOCKED_FATIGUE_STATUS = "blocked"

BACK_TO_BACK_GAME_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_back_to_back_game"
)
BULLPEN_AVAILABILITY_GAP_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_bullpen_availability_gap"
)
FATIGUE_BLOCKED_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_fatigue_blocked"
)
FATIGUE_CLEAR_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_fatigue_clear"
)
FATIGUE_HIGH_RISK_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_fatigue_high_risk"
)
FATIGUE_WATCH_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_fatigue_watch"
)
HEAVY_BULLPEN_WORKLOAD_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_heavy_bullpen_workload"
)
LEVERAGE_PITCH_SPIKE_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_leverage_pitch_spike"
)
NO_INPUTS_REASON = "market_research_baseball_bullpen_back_to_back_digest_no_inputs"
RELIEVER_REUSE_PRESSURE_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_reliever_reuse_pressure"
)
CONFIRMATION_GAP_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_confirmation_gap"
)
CONFLICTING_SOURCES_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_conflicting_sources"
)
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_source_diversity_gap"
)
STALE_OBSERVATION_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_stale_observation"
)
THIN_SOURCES_REASON = (
    "market_research_baseball_bullpen_back_to_back_digest_thin_sources"
)

ROW_REASON_CODES = (
    BACK_TO_BACK_GAME_REASON,
    BULLPEN_AVAILABILITY_GAP_REASON,
    FATIGUE_BLOCKED_REASON,
    FATIGUE_CLEAR_REASON,
    FATIGUE_HIGH_RISK_REASON,
    FATIGUE_WATCH_REASON,
    HEAVY_BULLPEN_WORKLOAD_REASON,
    LEVERAGE_PITCH_SPIKE_REASON,
    RELIEVER_REUSE_PRESSURE_REASON,
    CONFIRMATION_GAP_REASON,
    CONFLICTING_SOURCES_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
)
DIGEST_REASON_CODES = (
    BACK_TO_BACK_GAME_REASON,
    BULLPEN_AVAILABILITY_GAP_REASON,
    FATIGUE_BLOCKED_REASON,
    FATIGUE_CLEAR_REASON,
    FATIGUE_HIGH_RISK_REASON,
    FATIGUE_WATCH_REASON,
    HEAVY_BULLPEN_WORKLOAD_REASON,
    LEVERAGE_PITCH_SPIKE_REASON,
    NO_INPUTS_REASON,
    RELIEVER_REUSE_PRESSURE_REASON,
    CONFIRMATION_GAP_REASON,
    CONFLICTING_SOURCES_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEP_BY_DIGEST_STATUS = {
    PASS_STATUS: (
        "allow_report_only_market_research_baseball_bullpen_back_to_back_digest"
    ),
    WATCH_STATUS: (
        "review_report_only_market_research_baseball_bullpen_back_to_back_digest"
    ),
    BLOCKED_STATUS: (
        "block_report_only_market_research_baseball_bullpen_back_to_back_digest"
    ),
}
FATIGUE_STATUS_RANK = {
    BLOCKED_FATIGUE_STATUS: Decimal("0.000000"),
    HIGH_RISK_FATIGUE_STATUS: Decimal("1.000000"),
    WATCH_FATIGUE_STATUS: Decimal("2.000000"),
    CLEAR_FATIGUE_STATUS: Decimal("3.000000"),
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


def _j(*parts: str) -> str:
    return "".join(parts)


UNSAFE_REFERENCE_FRAGMENTS = frozenset(
    (
        _j("a", "pi", "_", "key"),
        _j("au", "th"),
        _j("b", "uy"),
        _j("can", "cel"),
        _j("ord", "er"),
        _j("pri", "vate"),
        _j("s", "ell"),
        _j("sec", "ret"),
        _j("to", "ken"),
        _j("tr", "ade"),
        _j("wa", "llet"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_BACK_TO_BACK_DIGEST_CONFIG_VERSION",
    "MarketResearchBaseballBullpenBackToBackDigestConfig",
    "MarketResearchBaseballBullpenBackToBackDigestObservation",
    "MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount",
    "MarketResearchBaseballBullpenBackToBackDigestReport",
    "MarketResearchBaseballBullpenBackToBackDigestRow",
    "build_market_research_baseball_bullpen_back_to_back_digest",
    "market_research_baseball_bullpen_back_to_back_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBaseballBullpenBackToBackDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_BACK_TO_BACK_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("3600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_confirmation_ratio: Decimal = Decimal("0.666667")
    max_back_to_back_rest_hours: Decimal = Decimal("24.000000")
    watch_bullpen_innings_last_game: Decimal = Decimal("3.000000")
    high_bullpen_innings_last_game: Decimal = Decimal("4.500000")
    high_bullpen_innings_last_2_days: Decimal = Decimal("7.000000")
    watch_high_leverage_pitch_count: Decimal = Decimal("35.000000")
    high_high_leverage_pitch_count: Decimal = Decimal("55.000000")
    watch_reliever_back_to_back_count: Decimal = Decimal("2.000000")
    watch_unavailable_reliever_count: Decimal = Decimal("1.000000")
    confidence_decay_per_stale_observation: Decimal = Decimal("0.150000")
    confidence_decay_per_source_gap: Decimal = Decimal("0.100000")
    confidence_decay_per_source_diversity_gap: Decimal = Decimal("0.080000")
    confidence_decay_per_confirmation_gap: Decimal = Decimal("0.100000")
    confidence_decay_per_conflicting_sources: Decimal = Decimal("0.120000")
    confidence_decay_per_back_to_back_game: Decimal = Decimal("0.050000")
    confidence_decay_per_heavy_bullpen_workload: Decimal = Decimal("0.100000")
    confidence_decay_per_leverage_pitch_spike: Decimal = Decimal("0.080000")
    confidence_decay_per_reliever_reuse_pressure: Decimal = Decimal("0.070000")
    confidence_decay_per_bullpen_availability_gap: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _normalize_positive_whole_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        for field_name in ("min_source_count", "min_independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_back_to_back_rest_hours",
            "watch_bullpen_innings_last_game",
            "high_bullpen_innings_last_game",
            "high_bullpen_innings_last_2_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_high_leverage_pitch_count",
            "high_high_leverage_pitch_count",
            "watch_reliever_back_to_back_count",
            "watch_unavailable_reliever_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_confirmation_ratio",
            "confidence_decay_per_stale_observation",
            "confidence_decay_per_source_gap",
            "confidence_decay_per_source_diversity_gap",
            "confidence_decay_per_confirmation_gap",
            "confidence_decay_per_conflicting_sources",
            "confidence_decay_per_back_to_back_game",
            "confidence_decay_per_heavy_bullpen_workload",
            "confidence_decay_per_leverage_pitch_spike",
            "confidence_decay_per_reliever_reuse_pressure",
            "confidence_decay_per_bullpen_availability_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.high_bullpen_innings_last_game < self.watch_bullpen_innings_last_game:
            raise ValueError(
                "high_bullpen_innings_last_game must be at least watch_bullpen_innings_last_game",
            )
        if self.high_high_leverage_pitch_count < self.watch_high_leverage_pitch_count:
            raise ValueError(
                "high_high_leverage_pitch_count must be at least watch_high_leverage_pitch_count",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenBackToBackDigestObservation(_NoSubclass):
    research_key: str
    condition_id: str
    game_id: str
    team_key: str
    market_id: str
    public_source_reference: str
    observed_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    confirming_source_count: Decimal
    conflicting_source_count: Decimal
    rest_hours_since_last_game: Decimal
    bullpen_innings_last_game: Decimal
    bullpen_innings_last_2_days: Decimal
    high_leverage_pitch_count_last_game: Decimal
    reliever_back_to_back_count: Decimal
    unavailable_reliever_count: Decimal
    base_confidence_score: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "research_key",
            "condition_id",
            "game_id",
            "team_key",
            "market_id",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_reference("public_source_reference", self.public_source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_count",
            "independent_source_count",
            "confirming_source_count",
            "conflicting_source_count",
            "high_leverage_pitch_count_last_game",
            "reliever_back_to_back_count",
            "unavailable_reliever_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "rest_hours_since_last_game",
            "bullpen_innings_last_game",
            "bullpen_innings_last_2_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "base_confidence_score",
            _normalize_ratio_decimal(
                "base_confidence_score",
                self.base_confidence_score,
            ),
        )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        if self.confirming_source_count > self.source_count:
            raise ValueError("confirming_source_count must not exceed source_count")
        if self.conflicting_source_count > self.source_count:
            raise ValueError("conflicting_source_count must not exceed source_count")
        _require_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    observation_count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, DIGEST_REASON_CODES)
        object.__setattr__(
            self,
            "observation_count",
            _normalize_nonnegative_whole_decimal(
                "observation_count",
                self.observation_count,
            ),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _normalize_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenBackToBackDigestRow(_NoSubclass):
    research_key: str
    condition_id: str
    game_id: str
    team_key: str
    market_id: str
    fatigue_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    confirming_source_count: Decimal
    conflicting_source_count: Decimal
    source_diversity_ratio: Decimal
    source_confirmation_ratio: Decimal
    rest_hours_since_last_game: Decimal
    bullpen_innings_last_game: Decimal
    bullpen_innings_last_2_days: Decimal
    high_leverage_pitch_count_last_game: Decimal
    reliever_back_to_back_count: Decimal
    unavailable_reliever_count: Decimal
    back_to_back_game_flag: bool
    heavy_bullpen_workload_flag: bool
    leverage_pitch_spike_flag: bool
    reliever_reuse_pressure_flag: bool
    bullpen_availability_gap_flag: bool
    base_confidence_score: Decimal
    confidence_decay_score: Decimal
    confidence_score: Decimal
    redacted_public_source_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "research_key",
            "condition_id",
            "game_id",
            "team_key",
            "market_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member(
            "fatigue_status",
            self.fatigue_status,
            (
                CLEAR_FATIGUE_STATUS,
                WATCH_FATIGUE_STATUS,
                HIGH_RISK_FATIGUE_STATUS,
                BLOCKED_FATIGUE_STATUS,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "rest_hours_since_last_game",
            "bullpen_innings_last_game",
            "bullpen_innings_last_2_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_count",
            "independent_source_count",
            "confirming_source_count",
            "conflicting_source_count",
            "high_leverage_pitch_count_last_game",
            "reliever_back_to_back_count",
            "unavailable_reliever_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "source_diversity_ratio",
            "source_confirmation_ratio",
            "base_confidence_score",
            "confidence_decay_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "back_to_back_game_flag",
            "heavy_bullpen_workload_flag",
            "leverage_pitch_spike_flag",
            "reliever_reuse_pressure_flag",
            "bullpen_availability_gap_flag",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _require_reference(
            "redacted_public_source_reference",
            self.redacted_public_source_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenBackToBackDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    clear_observation_count: Decimal
    watch_observation_count: Decimal
    high_risk_observation_count: Decimal
    blocked_observation_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    source_diversity_gap_count: Decimal
    confirmation_gap_count: Decimal
    conflicting_source_count: Decimal
    back_to_back_game_count: Decimal
    heavy_bullpen_workload_count: Decimal
    leverage_pitch_spike_count: Decimal
    reliever_reuse_pressure_count: Decimal
    bullpen_availability_gap_count: Decimal
    average_confidence_score: Decimal
    max_observation_age_seconds: Decimal
    min_rest_hours_since_last_game: Decimal
    max_bullpen_innings_last_2_days: Decimal
    rows: tuple[MarketResearchBaseballBullpenBackToBackDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member(
            "digest_status",
            self.digest_status,
            (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS),
        )
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "clear_observation_count",
            "watch_observation_count",
            "high_risk_observation_count",
            "blocked_observation_count",
            "stale_observation_count",
            "thin_source_count",
            "source_diversity_gap_count",
            "confirmation_gap_count",
            "conflicting_source_count",
            "back_to_back_game_count",
            "heavy_bullpen_workload_count",
            "leverage_pitch_spike_count",
            "reliever_reuse_pressure_count",
            "bullpen_availability_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_confidence_score",
            "max_observation_age_seconds",
            "min_rest_hours_since_last_game",
            "max_bullpen_innings_last_2_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                DIGEST_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_baseball_bullpen_back_to_back_digest(
    observations: Iterable[MarketResearchBaseballBullpenBackToBackDigestObservation],
    *,
    config: MarketResearchBaseballBullpenBackToBackDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballBullpenBackToBackDigestReport:
    if type(config) is not MarketResearchBaseballBullpenBackToBackDigestConfig:
        raise ValueError(
            "config must be a MarketResearchBaseballBullpenBackToBackDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _reject_future_observations(normalized, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    observation_count = _count(len(rows))
    reason_code_counts = _reason_code_counts(rows, observation_count)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                observation_count=ONE,
                observation_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _digest_status(rows)
    return MarketResearchBaseballBullpenBackToBackDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_DIGEST_STATUS[digest_status],
        observation_count=observation_count,
        clear_observation_count=_status_count(rows, CLEAR_FATIGUE_STATUS),
        watch_observation_count=_status_count(rows, WATCH_FATIGUE_STATUS),
        high_risk_observation_count=_status_count(rows, HIGH_RISK_FATIGUE_STATUS),
        blocked_observation_count=_status_count(rows, BLOCKED_FATIGUE_STATUS),
        stale_observation_count=_reason_count(rows, STALE_OBSERVATION_REASON),
        thin_source_count=_reason_count(rows, THIN_SOURCES_REASON),
        source_diversity_gap_count=_reason_count(rows, SOURCE_DIVERSITY_GAP_REASON),
        confirmation_gap_count=_reason_count(rows, CONFIRMATION_GAP_REASON),
        conflicting_source_count=_reason_count(rows, CONFLICTING_SOURCES_REASON),
        back_to_back_game_count=_reason_count(rows, BACK_TO_BACK_GAME_REASON),
        heavy_bullpen_workload_count=_reason_count(rows, HEAVY_BULLPEN_WORKLOAD_REASON),
        leverage_pitch_spike_count=_reason_count(rows, LEVERAGE_PITCH_SPIKE_REASON),
        reliever_reuse_pressure_count=_reason_count(
            rows,
            RELIEVER_REUSE_PRESSURE_REASON,
        ),
        bullpen_availability_gap_count=_reason_count(
            rows,
            BULLPEN_AVAILABILITY_GAP_REASON,
        ),
        average_confidence_score=_average(
            tuple(row.confidence_score for row in rows),
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in rows),
            default=ZERO,
        ),
        min_rest_hours_since_last_game=min(
            (row.rest_hours_since_last_game for row in rows),
            default=ZERO,
        ),
        max_bullpen_innings_last_2_days=max(
            (row.bullpen_innings_last_2_days for row in rows),
            default=ZERO,
        ),
        rows=rows,
        source_config_versions=_source_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_baseball_bullpen_back_to_back_digest_payload(
    report: MarketResearchBaseballBullpenBackToBackDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBaseballBullpenBackToBackDigestReport:
        raise ValueError("report must be a MarketResearchBaseballBullpenBackToBackDigestReport")
    value = _json_ready(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _row_from_observation(
    observation: MarketResearchBaseballBullpenBackToBackDigestObservation,
    *,
    config: MarketResearchBaseballBullpenBackToBackDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballBullpenBackToBackDigestRow:
    observation_age_seconds = _seconds_between(
        generated_at,
        observation.observed_at,
        "observed_at",
    )
    source_confirmation_ratio = _ratio(
        observation.confirming_source_count,
        observation.source_count,
    )
    source_diversity_ratio = _ratio(
        observation.independent_source_count,
        observation.source_count,
    )
    stale_observation = observation_age_seconds > config.max_observation_age_seconds
    thin_sources = observation.source_count < config.min_source_count
    source_diversity_gap = (
        observation.independent_source_count < config.min_independent_source_count
    )
    confirmation_gap = source_confirmation_ratio < config.min_confirmation_ratio
    conflicting_sources = observation.conflicting_source_count > ZERO
    back_to_back_game = (
        observation.rest_hours_since_last_game <= config.max_back_to_back_rest_hours
    )
    heavy_bullpen_workload = (
        observation.bullpen_innings_last_game >= config.watch_bullpen_innings_last_game
        or observation.bullpen_innings_last_2_days
        >= config.high_bullpen_innings_last_2_days
    )
    leverage_pitch_spike = (
        observation.high_leverage_pitch_count_last_game
        >= config.watch_high_leverage_pitch_count
    )
    reliever_reuse_pressure = (
        observation.reliever_back_to_back_count
        >= config.watch_reliever_back_to_back_count
    )
    bullpen_availability_gap = (
        observation.unavailable_reliever_count
        >= config.watch_unavailable_reliever_count
    )
    has_blocker = any(
        (
            stale_observation,
            thin_sources,
            source_diversity_gap,
            confirmation_gap,
            conflicting_sources,
        ),
    )
    high_risk = (
        back_to_back_game
        and (
            observation.bullpen_innings_last_game
            >= config.high_bullpen_innings_last_game
            or observation.bullpen_innings_last_2_days
            >= config.high_bullpen_innings_last_2_days
            or observation.high_leverage_pitch_count_last_game
            >= config.high_high_leverage_pitch_count
            or reliever_reuse_pressure
            or bullpen_availability_gap
        )
    )
    has_watch_risk = any(
        (
            back_to_back_game,
            heavy_bullpen_workload,
            leverage_pitch_spike,
            reliever_reuse_pressure,
            bullpen_availability_gap,
        ),
    )
    if has_blocker:
        fatigue_status = BLOCKED_FATIGUE_STATUS
    elif high_risk:
        fatigue_status = HIGH_RISK_FATIGUE_STATUS
    elif has_watch_risk:
        fatigue_status = WATCH_FATIGUE_STATUS
    else:
        fatigue_status = CLEAR_FATIGUE_STATUS
    reason_codes = _row_reasons(
        fatigue_status=fatigue_status,
        stale_observation=stale_observation,
        thin_sources=thin_sources,
        source_diversity_gap=source_diversity_gap,
        confirmation_gap=confirmation_gap,
        conflicting_sources=conflicting_sources,
        back_to_back_game=back_to_back_game,
        heavy_bullpen_workload=heavy_bullpen_workload,
        leverage_pitch_spike=leverage_pitch_spike,
        reliever_reuse_pressure=reliever_reuse_pressure,
        bullpen_availability_gap=bullpen_availability_gap,
    )
    confidence_decay_score = _confidence_decay_score(reason_codes, config)
    confidence_score = _clamp_ratio(observation.base_confidence_score - confidence_decay_score)
    return MarketResearchBaseballBullpenBackToBackDigestRow(
        research_key=observation.research_key,
        condition_id=observation.condition_id,
        game_id=observation.game_id,
        team_key=observation.team_key,
        market_id=observation.market_id,
        fatigue_status=fatigue_status,
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        source_count=observation.source_count,
        independent_source_count=observation.independent_source_count,
        confirming_source_count=observation.confirming_source_count,
        conflicting_source_count=observation.conflicting_source_count,
        source_diversity_ratio=source_diversity_ratio,
        source_confirmation_ratio=source_confirmation_ratio,
        rest_hours_since_last_game=observation.rest_hours_since_last_game,
        bullpen_innings_last_game=observation.bullpen_innings_last_game,
        bullpen_innings_last_2_days=observation.bullpen_innings_last_2_days,
        high_leverage_pitch_count_last_game=(
            observation.high_leverage_pitch_count_last_game
        ),
        reliever_back_to_back_count=observation.reliever_back_to_back_count,
        unavailable_reliever_count=observation.unavailable_reliever_count,
        back_to_back_game_flag=back_to_back_game,
        heavy_bullpen_workload_flag=heavy_bullpen_workload,
        leverage_pitch_spike_flag=leverage_pitch_spike,
        reliever_reuse_pressure_flag=reliever_reuse_pressure,
        bullpen_availability_gap_flag=bullpen_availability_gap,
        base_confidence_score=observation.base_confidence_score,
        confidence_decay_score=confidence_decay_score,
        confidence_score=confidence_score,
        redacted_public_source_reference=_redact_reference(
            observation.public_source_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reasons(
    *,
    fatigue_status: str,
    stale_observation: bool,
    thin_sources: bool,
    source_diversity_gap: bool,
    confirmation_gap: bool,
    conflicting_sources: bool,
    back_to_back_game: bool,
    heavy_bullpen_workload: bool,
    leverage_pitch_spike: bool,
    reliever_reuse_pressure: bool,
    bullpen_availability_gap: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if fatigue_status == BLOCKED_FATIGUE_STATUS:
        reasons.append(FATIGUE_BLOCKED_REASON)
    elif fatigue_status == HIGH_RISK_FATIGUE_STATUS:
        reasons.append(FATIGUE_HIGH_RISK_REASON)
    elif fatigue_status == WATCH_FATIGUE_STATUS:
        reasons.append(FATIGUE_WATCH_REASON)
    else:
        reasons.append(FATIGUE_CLEAR_REASON)
    if stale_observation:
        reasons.append(STALE_OBSERVATION_REASON)
    if thin_sources:
        reasons.append(THIN_SOURCES_REASON)
    if source_diversity_gap:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if confirmation_gap:
        reasons.append(CONFIRMATION_GAP_REASON)
    if conflicting_sources:
        reasons.append(CONFLICTING_SOURCES_REASON)
    if back_to_back_game:
        reasons.append(BACK_TO_BACK_GAME_REASON)
    if heavy_bullpen_workload:
        reasons.append(HEAVY_BULLPEN_WORKLOAD_REASON)
    if leverage_pitch_spike:
        reasons.append(LEVERAGE_PITCH_SPIKE_REASON)
    if reliever_reuse_pressure:
        reasons.append(RELIEVER_REUSE_PRESSURE_REASON)
    if bullpen_availability_gap:
        reasons.append(BULLPEN_AVAILABILITY_GAP_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _confidence_decay_score(
    reason_codes: tuple[str, ...],
    config: MarketResearchBaseballBullpenBackToBackDigestConfig,
) -> Decimal:
    decay = ZERO
    if STALE_OBSERVATION_REASON in reason_codes:
        decay += config.confidence_decay_per_stale_observation
    if THIN_SOURCES_REASON in reason_codes:
        decay += config.confidence_decay_per_source_gap
    if SOURCE_DIVERSITY_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_source_diversity_gap
    if CONFIRMATION_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_confirmation_gap
    if CONFLICTING_SOURCES_REASON in reason_codes:
        decay += config.confidence_decay_per_conflicting_sources
    if BACK_TO_BACK_GAME_REASON in reason_codes:
        decay += config.confidence_decay_per_back_to_back_game
    if HEAVY_BULLPEN_WORKLOAD_REASON in reason_codes:
        decay += config.confidence_decay_per_heavy_bullpen_workload
    if LEVERAGE_PITCH_SPIKE_REASON in reason_codes:
        decay += config.confidence_decay_per_leverage_pitch_spike
    if RELIEVER_REUSE_PRESSURE_REASON in reason_codes:
        decay += config.confidence_decay_per_reliever_reuse_pressure
    if BULLPEN_AVAILABILITY_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_bullpen_availability_gap
    return _clamp_ratio(decay)


def _digest_status(
    rows: tuple[MarketResearchBaseballBullpenBackToBackDigestRow, ...],
) -> str:
    if any(row.fatigue_status == BLOCKED_FATIGUE_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(
        row.fatigue_status in (WATCH_FATIGUE_STATUS, HIGH_RISK_FATIGUE_STATUS)
        for row in rows
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _reason_code_counts(
    rows: tuple[MarketResearchBaseballBullpenBackToBackDigestRow, ...],
    observation_count: Decimal,
) -> tuple[MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount, ...]:
    present_reasons = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason in DIGEST_REASON_CODES
    }
    return tuple(
        MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount(
            reason_code=reason,
            observation_count=_count(
                sum(ONE for row in rows if reason in row.reason_codes),
            ),
            observation_ratio=_ratio(
                _count(sum(ONE for row in rows if reason in row.reason_codes)),
                observation_count,
            ),
        )
        for reason in DIGEST_REASON_CODES
        if reason in present_reasons
    )


def _status_count(
    rows: tuple[MarketResearchBaseballBullpenBackToBackDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(ONE for row in rows if row.fatigue_status == status))


def _reason_count(
    rows: tuple[MarketResearchBaseballBullpenBackToBackDigestRow, ...],
    reason: str,
) -> Decimal:
    return _count(sum(ONE for row in rows if reason in row.reason_codes))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / _count(len(values))).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _count(value: object) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _seconds_between(later: datetime, earlier: datetime, field_name: str) -> Decimal:
    delta = later - earlier
    total = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if total < ZERO:
        raise ValueError(f"{field_name} must not be after generated_at")
    return total.quantize(QUANTUM)


def _normalize_observations(
    observations: Iterable[MarketResearchBaseballBullpenBackToBackDigestObservation],
) -> tuple[MarketResearchBaseballBullpenBackToBackDigestObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError(
            "observations must contain MarketResearchBaseballBullpenBackToBackDigestObservation",
        )
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError(
            "observations must contain MarketResearchBaseballBullpenBackToBackDigestObservation",
        ) from exc
    seen_research_keys: set[str] = set()
    for observation in normalized:
        if type(observation) is not MarketResearchBaseballBullpenBackToBackDigestObservation:
            raise ValueError(
                "observations must contain MarketResearchBaseballBullpenBackToBackDigestObservation",
            )
        _require_flags("observation", observation)
        if observation.research_key in seen_research_keys:
            raise ValueError("observations must not contain duplicate research_key values")
        seen_research_keys.add(observation.research_key)
    return normalized


def _reject_future_observations(
    observations: tuple[MarketResearchBaseballBullpenBackToBackDigestObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _source_config_versions(
    observations: tuple[MarketResearchBaseballBullpenBackToBackDigestObservation, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (observation.team_key, observation.source_config_version)
                for observation in observations
            },
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchBaseballBullpenBackToBackDigestRow, ...]:
    if not isinstance(value, tuple):
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not MarketResearchBaseballBullpenBackToBackDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBaseballBullpenBackToBackDigestRow",
            )
        _require_flags("row", row)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.research_key for row in value}) != len(value):
        raise ValueError("rows must not contain duplicate research_key values")
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for row in value:
        if type(row) is not MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketResearchBaseballBullpenBackToBackDigestReasonCodeCount",
            )
        _require_flags("reason_code_count", row)
    if value != tuple(sorted(value, key=lambda row: DIGEST_REASON_CODES.index(row.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return value


def _normalize_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, tuple):
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("source_config_versions must contain team/version tuples")
        team_key, source_config_version = item
        _require_canonical_string("team_key", team_key)
        _require_canonical_string("source_config_version", source_config_version)
        normalized.append((team_key, source_config_version))
    result = tuple(normalized)
    if result != tuple(sorted(result)):
        raise ValueError("source_config_versions must be sorted deterministically")
    return result


def _row_sort_key(
    row: MarketResearchBaseballBullpenBackToBackDigestRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        FATIGUE_STATUS_RANK[row.fatigue_status],
        -row.confidence_decay_score,
        row.game_id,
        row.team_key,
        row.research_key,
    )


def _validate_row(row: MarketResearchBaseballBullpenBackToBackDigestRow) -> None:
    expected_reason_by_status = {
        BLOCKED_FATIGUE_STATUS: FATIGUE_BLOCKED_REASON,
        HIGH_RISK_FATIGUE_STATUS: FATIGUE_HIGH_RISK_REASON,
        WATCH_FATIGUE_STATUS: FATIGUE_WATCH_REASON,
        CLEAR_FATIGUE_STATUS: FATIGUE_CLEAR_REASON,
    }
    expected_reason = expected_reason_by_status[row.fatigue_status]
    if expected_reason not in row.reason_codes:
        raise ValueError("fatigue_status must match reason_codes")
    if row.independent_source_count > row.source_count:
        raise ValueError("independent_source_count must not exceed source_count")
    if row.confirming_source_count > row.source_count:
        raise ValueError("confirming_source_count must not exceed source_count")
    if row.conflicting_source_count > row.source_count:
        raise ValueError("conflicting_source_count must not exceed source_count")
    if row.confidence_score > row.base_confidence_score:
        raise ValueError("confidence_score must not exceed base_confidence_score")


def _validate_report(report: MarketResearchBaseballBullpenBackToBackDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_DIGEST_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    rows = report.rows
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match rows")
    expected_counts = {
        "clear_observation_count": _status_count(rows, CLEAR_FATIGUE_STATUS),
        "watch_observation_count": _status_count(rows, WATCH_FATIGUE_STATUS),
        "high_risk_observation_count": _status_count(rows, HIGH_RISK_FATIGUE_STATUS),
        "blocked_observation_count": _status_count(rows, BLOCKED_FATIGUE_STATUS),
        "stale_observation_count": _reason_count(rows, STALE_OBSERVATION_REASON),
        "thin_source_count": _reason_count(rows, THIN_SOURCES_REASON),
        "source_diversity_gap_count": _reason_count(rows, SOURCE_DIVERSITY_GAP_REASON),
        "confirmation_gap_count": _reason_count(rows, CONFIRMATION_GAP_REASON),
        "conflicting_source_count": _reason_count(rows, CONFLICTING_SOURCES_REASON),
        "back_to_back_game_count": _reason_count(rows, BACK_TO_BACK_GAME_REASON),
        "heavy_bullpen_workload_count": _reason_count(
            rows,
            HEAVY_BULLPEN_WORKLOAD_REASON,
        ),
        "leverage_pitch_spike_count": _reason_count(rows, LEVERAGE_PITCH_SPIKE_REASON),
        "reliever_reuse_pressure_count": _reason_count(
            rows,
            RELIEVER_REUSE_PRESSURE_REASON,
        ),
        "bullpen_availability_gap_count": _reason_count(
            rows,
            BULLPEN_AVAILABILITY_GAP_REASON,
        ),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.average_confidence_score != _average(
        tuple(row.confidence_score for row in rows),
    ):
        raise ValueError("average_confidence_score must match rows")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds must match rows")
    if report.min_rest_hours_since_last_game != min(
        (row.rest_hours_since_last_game for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_rest_hours_since_last_game must match rows")
    if report.max_bullpen_innings_last_2_days != max(
        (row.bullpen_innings_last_2_days for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_bullpen_innings_last_2_days must match rows")
    if report.reason_codes != tuple(row.reason_code for row in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _digest_status(rows)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_member(field_name, reason_code, allowed)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in allowed if reason_code in seen)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of the supported values")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    return value


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a probability Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _normalize_ratio_decimal("ratio", value)


def _require_flags(context: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if type(getattr(value, flag_name)) is not bool or getattr(value, flag_name) is not True:
            raise ValueError(f"{context} {flag_name} must be True")


def _redact_reference(value: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_REFERENCE_FRAGMENTS):
        return "sha256:" + sha256(value.encode()).hexdigest()[:12]
    return value


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, Any] = {}
        for field in fields(value):
            key = field.name
            if key == "redacted_public_source_reference":
                key = "public_source_reference"
            payload[key] = _json_ready(getattr(value, field.name))
        return payload
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value

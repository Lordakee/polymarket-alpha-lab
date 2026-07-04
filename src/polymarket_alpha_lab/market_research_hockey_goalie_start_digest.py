"""Pure in-memory reducer for hockey goalie start digest reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from hashlib import sha256


DEFAULT_MARKET_RESEARCH_HOCKEY_GOALIE_START_DIGEST_CONFIG_VERSION = (
    "market-research-hockey-goalie-start-digest-v0"
)

PASS_STATUS = "pass"
READY_STATUS = "ready"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"

READY_REASON = "market_research_hockey_goalie_start_digest_ready"
NO_INPUTS_REASON = "market_research_hockey_goalie_start_digest_no_inputs"
MISSING_START_REPORT_REASON = (
    "market_research_hockey_goalie_start_digest_missing_start_report"
)
STALE_START_REPORT_REASON = (
    "market_research_hockey_goalie_start_digest_stale_start_report"
)
STALE_OBSERVATION_REASON = (
    "market_research_hockey_goalie_start_digest_stale_observation"
)
THIN_SOURCES_REASON = "market_research_hockey_goalie_start_digest_thin_sources"
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_hockey_goalie_start_digest_source_diversity_gap"
)
CONFIRMATION_GAP_REASON = (
    "market_research_hockey_goalie_start_digest_confirmation_gap"
)
CONFLICTING_SOURCES_REASON = (
    "market_research_hockey_goalie_start_digest_conflicting_sources"
)
BACK_TO_BACK_START_REASON = (
    "market_research_hockey_goalie_start_digest_back_to_back_start"
)
WORKLOAD_FATIGUE_REASON = (
    "market_research_hockey_goalie_start_digest_workload_fatigue"
)
LATE_SCRATCH_RISK_REASON = (
    "market_research_hockey_goalie_start_digest_late_scratch_risk"
)
PASSED_REASON = "market_research_hockey_goalie_start_digest_passed"

ROW_REASON_CODES = (
    BACK_TO_BACK_START_REASON,
    CONFIRMATION_GAP_REASON,
    CONFLICTING_SOURCES_REASON,
    LATE_SCRATCH_RISK_REASON,
    MISSING_START_REPORT_REASON,
    READY_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    STALE_START_REPORT_REASON,
    THIN_SOURCES_REASON,
    WORKLOAD_FATIGUE_REASON,
)
DIGEST_REASON_CODES = (
    BACK_TO_BACK_START_REASON,
    CONFIRMATION_GAP_REASON,
    CONFLICTING_SOURCES_REASON,
    LATE_SCRATCH_RISK_REASON,
    MISSING_START_REPORT_REASON,
    NO_INPUTS_REASON,
    PASSED_REASON,
    READY_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    STALE_START_REPORT_REASON,
    THIN_SOURCES_REASON,
    WORKLOAD_FATIGUE_REASON,
)
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "allow_report_only_market_research_hockey_goalie_start_digest",
    WATCH_STATUS: "watch_report_only_market_research_hockey_goalie_start_digest",
    BLOCKED_STATUS: "block_report_only_market_research_hockey_goalie_start_digest",
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_HOCKEY_GOALIE_START_DIGEST_CONFIG_VERSION",
    "MarketResearchHockeyGoalieStartDigestConfig",
    "MarketResearchHockeyGoalieStartDigestObservation",
    "MarketResearchHockeyGoalieStartDigestReasonCodeCount",
    "MarketResearchHockeyGoalieStartDigestRow",
    "MarketResearchHockeyGoalieStartDigestReport",
    "build_market_research_hockey_goalie_start_digest",
    "market_research_hockey_goalie_start_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchHockeyGoalieStartDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_HOCKEY_GOALIE_START_DIGEST_CONFIG_VERSION
    )
    max_start_report_age_seconds: Decimal = Decimal("3600.000000")
    max_observation_age_seconds: Decimal = Decimal("5400.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_confirmation_ratio: Decimal = Decimal("0.666667")
    fatigue_watch_threshold: Decimal = Decimal("0.600000")
    late_scratch_watch_threshold: Decimal = Decimal("0.300000")
    confidence_decay_per_stale_start: Decimal = Decimal("0.150000")
    confidence_decay_per_source_gap: Decimal = Decimal("0.100000")
    confidence_decay_per_confirmation_gap: Decimal = Decimal("0.100000")
    confidence_decay_per_fatigue: Decimal = Decimal("0.050000")
    confidence_decay_per_late_scratch: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_start_report_age_seconds",
            "max_observation_age_seconds",
            "min_source_count",
            "min_independent_source_count",
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
            "min_confirmation_ratio",
            "fatigue_watch_threshold",
            "late_scratch_watch_threshold",
            "confidence_decay_per_stale_start",
            "confidence_decay_per_source_gap",
            "confidence_decay_per_confirmation_gap",
            "confidence_decay_per_fatigue",
            "confidence_decay_per_late_scratch",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_confirmation_ratio > ONE:
            raise ValueError("min_confirmation_ratio must not exceed 1")
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchHockeyGoalieStartDigestObservation(_NoSubclass):
    research_key: str
    condition_id: str
    game_key: str
    team_key: str
    goalie_key: str
    public_source_reference: str
    observed_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    confirming_source_count: Decimal
    conflicting_source_count: Decimal
    back_to_back_start_flag: bool
    recent_workload_score: Decimal
    late_scratch_risk_score: Decimal
    base_confidence_score: Decimal
    source_config_version: str
    start_reported_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "research_key",
            "condition_id",
            "game_key",
            "team_key",
            "goalie_key",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_reference("public_source_reference", self.public_source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.start_reported_at is not None:
            object.__setattr__(
                self,
                "start_reported_at",
                _as_utc("start_reported_at", self.start_reported_at),
            )
        for field_name in (
            "source_count",
            "independent_source_count",
            "confirming_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recent_workload_score",
            "late_scratch_risk_score",
            "base_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.back_to_back_start_flag) is not bool:
            raise ValueError("back_to_back_start_flag must be a bool")
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        if self.confirming_source_count > self.source_count:
            raise ValueError("confirming_source_count must not exceed source_count")
        if self.conflicting_source_count > self.source_count:
            raise ValueError("conflicting_source_count must not exceed source_count")
        _require_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchHockeyGoalieStartDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    observation_count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code, DIGEST_REASON_CODES)
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
class MarketResearchHockeyGoalieStartDigestRow(_NoSubclass):
    research_key: str
    condition_id: str
    game_key: str
    team_key: str
    goalie_key: str
    start_status: str
    observed_at: datetime
    start_reported_at: datetime | None
    observation_age_seconds: Decimal
    start_report_age_seconds: Decimal | None
    source_count: Decimal
    independent_source_count: Decimal
    confirming_source_count: Decimal
    conflicting_source_count: Decimal
    source_diversity_ratio: Decimal
    source_confirmation_ratio: Decimal
    back_to_back_start_flag: bool
    recent_workload_score: Decimal
    late_scratch_risk_score: Decimal
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
            "game_key",
            "team_key",
            "goalie_key",
            "redacted_public_source_reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("start_status", self.start_status, (READY_STATUS, WATCH_STATUS, BLOCKED_STATUS))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.start_reported_at is not None:
            object.__setattr__(
                self,
                "start_reported_at",
                _as_utc("start_reported_at", self.start_reported_at),
            )
        for field_name in (
            "observation_age_seconds",
            "source_count",
            "independent_source_count",
            "confirming_source_count",
            "conflicting_source_count",
            "source_diversity_ratio",
            "source_confirmation_ratio",
            "recent_workload_score",
            "late_scratch_risk_score",
            "base_confidence_score",
            "confidence_decay_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.start_report_age_seconds is not None:
            object.__setattr__(
                self,
                "start_report_age_seconds",
                _normalize_nonnegative_decimal(
                    "start_report_age_seconds",
                    self.start_report_age_seconds,
                ),
            )
        if type(self.back_to_back_start_flag) is not bool:
            raise ValueError("back_to_back_start_flag must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchHockeyGoalieStartDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    stale_start_report_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    source_diversity_gap_count: Decimal
    confirmation_gap_count: Decimal
    conflicting_source_count: Decimal
    back_to_back_start_count: Decimal
    workload_fatigue_count: Decimal
    late_scratch_risk_count: Decimal
    average_confidence_score: Decimal
    max_start_report_age_seconds: Decimal | None
    max_observation_age_seconds: Decimal | None
    average_source_count: Decimal
    rows: tuple[MarketResearchHockeyGoalieStartDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchHockeyGoalieStartDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS))
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "stale_start_report_count",
            "stale_observation_count",
            "thin_source_count",
            "source_diversity_gap_count",
            "confirmation_gap_count",
            "conflicting_source_count",
            "back_to_back_start_count",
            "workload_fatigue_count",
            "late_scratch_risk_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_confidence_score", "average_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_start_report_age_seconds",
            "max_observation_age_seconds",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_nonnegative_decimal(field_name, value),
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


def build_market_research_hockey_goalie_start_digest(
    observations: list[MarketResearchHockeyGoalieStartDigestObservation]
    | tuple[MarketResearchHockeyGoalieStartDigestObservation, ...],
    *,
    config: MarketResearchHockeyGoalieStartDigestConfig,
    generated_at: datetime,
) -> MarketResearchHockeyGoalieStartDigestReport:
    if type(config) is not MarketResearchHockeyGoalieStartDigestConfig:
        raise ValueError(
            "config must be a MarketResearchHockeyGoalieStartDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _reject_future_observations(normalized, generated_at_utc)
    rows = _rows(normalized, config, generated_at_utc)
    blocked_count = _decimal_count(
        sum(1 for row in rows if row.start_status == BLOCKED_STATUS),
    )
    watch_count = _decimal_count(sum(1 for row in rows if row.start_status == WATCH_STATUS))
    if blocked_count > ZERO:
        digest_status = BLOCKED_STATUS
    elif watch_count > ZERO:
        digest_status = WATCH_STATUS
    else:
        digest_status = PASS_STATUS
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchHockeyGoalieStartDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                observation_count=ONE,
                observation_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    elif digest_status == PASS_STATUS:
        reason_codes = tuple(sorted((*reason_codes, PASSED_REASON)))

    return MarketResearchHockeyGoalieStartDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        observation_count=_decimal_count(len(rows)),
        ready_observation_count=_status_count(rows, READY_STATUS),
        watch_observation_count=watch_count,
        blocked_observation_count=blocked_count,
        stale_start_report_count=_reason_observation_count(rows, STALE_START_REPORT_REASON),
        stale_observation_count=_reason_observation_count(rows, STALE_OBSERVATION_REASON),
        thin_source_count=_reason_observation_count(rows, THIN_SOURCES_REASON),
        source_diversity_gap_count=_reason_observation_count(
            rows,
            SOURCE_DIVERSITY_GAP_REASON,
        ),
        confirmation_gap_count=_reason_observation_count(rows, CONFIRMATION_GAP_REASON),
        conflicting_source_count=_reason_observation_count(rows, CONFLICTING_SOURCES_REASON),
        back_to_back_start_count=_reason_observation_count(rows, BACK_TO_BACK_START_REASON),
        workload_fatigue_count=_reason_observation_count(rows, WORKLOAD_FATIGUE_REASON),
        late_scratch_risk_count=_reason_observation_count(rows, LATE_SCRATCH_RISK_REASON),
        average_confidence_score=_average(row.confidence_score for row in rows),
        max_start_report_age_seconds=_max_or_none(
            row.start_report_age_seconds for row in rows if row.start_report_age_seconds is not None
        ),
        max_observation_age_seconds=_max_or_none(row.observation_age_seconds for row in rows),
        average_source_count=_average(row.source_count for row in rows),
        rows=rows,
        source_config_versions=_source_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_hockey_goalie_start_digest_payload(
    report: MarketResearchHockeyGoalieStartDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchHockeyGoalieStartDigestReport:
        raise ValueError(
            "report must be a MarketResearchHockeyGoalieStartDigestReport",
        )
    _require_flags("report", report)
    return _payload_value(asdict(report))  # type: ignore[return-value]


def _rows(
    observations: tuple[MarketResearchHockeyGoalieStartDigestObservation, ...],
    config: MarketResearchHockeyGoalieStartDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchHockeyGoalieStartDigestRow, ...]:
    rows = [_row(observation, config, generated_at) for observation in observations]
    return tuple(sorted(rows, key=lambda row: (row.start_status != BLOCKED_STATUS, row.game_key, row.goalie_key, row.research_key)))


def _row(
    observation: MarketResearchHockeyGoalieStartDigestObservation,
    config: MarketResearchHockeyGoalieStartDigestConfig,
    generated_at: datetime,
) -> MarketResearchHockeyGoalieStartDigestRow:
    observation_age = _seconds_between(observation.observed_at, generated_at)
    start_age = (
        None
        if observation.start_reported_at is None
        else _seconds_between(observation.start_reported_at, generated_at)
    )
    diversity_ratio = _safe_ratio(observation.independent_source_count, observation.source_count)
    confirmation_ratio = _safe_ratio(observation.confirming_source_count, observation.source_count)
    reasons: list[str] = []
    if observation.start_reported_at is None:
        reasons.append(MISSING_START_REPORT_REASON)
    elif start_age is not None and start_age > config.max_start_report_age_seconds:
        reasons.append(STALE_START_REPORT_REASON)
    if observation_age > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if observation.independent_source_count < config.min_independent_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if confirmation_ratio < config.min_confirmation_ratio:
        reasons.append(CONFIRMATION_GAP_REASON)
    if observation.conflicting_source_count > ZERO:
        reasons.append(CONFLICTING_SOURCES_REASON)
    if observation.back_to_back_start_flag:
        reasons.append(BACK_TO_BACK_START_REASON)
    if observation.recent_workload_score >= config.fatigue_watch_threshold:
        reasons.append(WORKLOAD_FATIGUE_REASON)
    if observation.late_scratch_risk_score >= config.late_scratch_watch_threshold:
        reasons.append(LATE_SCRATCH_RISK_REASON)
    if not reasons:
        reasons.append(READY_REASON)

    start_status = _row_status(tuple(reasons))
    decay = _confidence_decay(tuple(reasons), config)
    confidence_score = _quantize(max(ZERO, observation.base_confidence_score - decay))
    return MarketResearchHockeyGoalieStartDigestRow(
        research_key=observation.research_key,
        condition_id=observation.condition_id,
        game_key=observation.game_key,
        team_key=observation.team_key,
        goalie_key=observation.goalie_key,
        start_status=start_status,
        observed_at=observation.observed_at,
        start_reported_at=observation.start_reported_at,
        observation_age_seconds=observation_age,
        start_report_age_seconds=start_age,
        source_count=observation.source_count,
        independent_source_count=observation.independent_source_count,
        confirming_source_count=observation.confirming_source_count,
        conflicting_source_count=observation.conflicting_source_count,
        source_diversity_ratio=diversity_ratio,
        source_confirmation_ratio=confirmation_ratio,
        back_to_back_start_flag=observation.back_to_back_start_flag,
        recent_workload_score=observation.recent_workload_score,
        late_scratch_risk_score=observation.late_scratch_risk_score,
        base_confidence_score=observation.base_confidence_score,
        confidence_decay_score=decay,
        confidence_score=confidence_score,
        redacted_public_source_reference=_redacted_reference(observation.public_source_reference),
        reason_codes=tuple(sorted(reasons)),
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if CONFLICTING_SOURCES_REASON in reason_codes:
        return BLOCKED_STATUS
    if (
        THIN_SOURCES_REASON in reason_codes
        and CONFIRMATION_GAP_REASON in reason_codes
        and STALE_START_REPORT_REASON in reason_codes
    ):
        return BLOCKED_STATUS
    if reason_codes == (READY_REASON,):
        return READY_STATUS
    return WATCH_STATUS


def _confidence_decay(
    reason_codes: tuple[str, ...],
    config: MarketResearchHockeyGoalieStartDigestConfig,
) -> Decimal:
    decay = ZERO
    if STALE_START_REPORT_REASON in reason_codes or STALE_OBSERVATION_REASON in reason_codes:
        decay += config.confidence_decay_per_stale_start
    if THIN_SOURCES_REASON in reason_codes or SOURCE_DIVERSITY_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_source_gap
    if CONFIRMATION_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_confirmation_gap
    if CONFLICTING_SOURCES_REASON in reason_codes:
        decay += config.confidence_decay_per_confirmation_gap
    if BACK_TO_BACK_START_REASON in reason_codes or WORKLOAD_FATIGUE_REASON in reason_codes:
        decay += config.confidence_decay_per_fatigue
    if LATE_SCRATCH_RISK_REASON in reason_codes:
        decay += config.confidence_decay_per_late_scratch
    return _quantize(decay)


def _reason_code_counts(
    rows: tuple[MarketResearchHockeyGoalieStartDigestRow, ...],
) -> tuple[MarketResearchHockeyGoalieStartDigestReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    total = _decimal_count(len(rows))
    return tuple(
        MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code=reason_code,
            observation_count=count,
            observation_ratio=_safe_ratio(count, total),
        )
        for reason_code, count in sorted(counts.items())
    )


def _status_count(
    rows: tuple[MarketResearchHockeyGoalieStartDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.start_status == status))


def _reason_observation_count(
    rows: tuple[MarketResearchHockeyGoalieStartDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    observations: tuple[MarketResearchHockeyGoalieStartDigestObservation, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (observation.goalie_key, observation.source_config_version)
                for observation in observations
            },
        ),
    )


def _normalize_observations(
    observations: list[MarketResearchHockeyGoalieStartDigestObservation]
    | tuple[MarketResearchHockeyGoalieStartDigestObservation, ...],
) -> tuple[MarketResearchHockeyGoalieStartDigestObservation, ...]:
    if not isinstance(observations, (list, tuple)):
        raise ValueError("observations must be a list or tuple")
    normalized: list[MarketResearchHockeyGoalieStartDigestObservation] = []
    seen: set[tuple[str, str, datetime]] = set()
    for observation in observations:
        if type(observation) is not MarketResearchHockeyGoalieStartDigestObservation:
            raise ValueError(
                "observations must contain MarketResearchHockeyGoalieStartDigestObservation",
            )
        _require_flags("observation", observation)
        key = (observation.research_key, observation.goalie_key, observation.observed_at)
        if key in seen:
            raise ValueError("observations must not contain duplicate research goalie observation")
        seen.add(key)
        normalized.append(observation)
    return tuple(sorted(normalized, key=lambda item: (item.observed_at, item.game_key, item.goalie_key, item.research_key)))


def _reject_future_observations(
    observations: tuple[MarketResearchHockeyGoalieStartDigestObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if observation.start_reported_at is not None and observation.start_reported_at > generated_at:
            raise ValueError("start_reported_at must not be after generated_at")


def _normalize_rows(
    rows: tuple[MarketResearchHockeyGoalieStartDigestRow, ...],
) -> tuple[MarketResearchHockeyGoalieStartDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchHockeyGoalieStartDigestRow:
            raise ValueError("rows must contain MarketResearchHockeyGoalieStartDigestRow")
        key = (row.research_key, row.goalie_key)
        if key in seen:
            raise ValueError("rows must not contain duplicate research goalie row")
        seen.add(key)
        _require_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchHockeyGoalieStartDigestReasonCodeCount, ...],
) -> tuple[MarketResearchHockeyGoalieStartDigestReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for count in counts:
        if type(count) is not MarketResearchHockeyGoalieStartDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketResearchHockeyGoalieStartDigestReasonCodeCount",
            )
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason_code")
        seen.add(count.reason_code)
        _require_flags("reason_code_count", count)
    if tuple(item.reason_code for item in counts) != tuple(sorted(seen)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _normalize_source_config_versions(
    versions: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if not isinstance(versions, tuple):
        raise ValueError("source_config_versions must be a tuple")
    previous: tuple[str, str] | None = None
    normalized: list[tuple[str, str]] = []
    for item in versions:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        goalie_key, config_version = item
        _require_canonical_string("source_config_versions goalie_key", goalie_key)
        _require_canonical_string("source_config_versions config_version", config_version)
        if previous is not None and item <= previous:
            raise ValueError("source_config_versions must be sorted and unique")
        previous = item
        normalized.append(item)
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    previous = ""
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code, allowed)
        if reason_code <= previous:
            raise ValueError(f"{field_name} must be sorted and unique")
        previous = reason_code
    return reason_codes


def _validate_row(row: MarketResearchHockeyGoalieStartDigestRow) -> None:
    if row.independent_source_count > row.source_count:
        raise ValueError("independent_source_count must not exceed source_count")
    if row.confirming_source_count > row.source_count:
        raise ValueError("confirming_source_count must not exceed source_count")
    if row.conflicting_source_count > row.source_count:
        raise ValueError("conflicting_source_count must not exceed source_count")
    expected_diversity = _safe_ratio(row.independent_source_count, row.source_count)
    if row.source_diversity_ratio != expected_diversity:
        raise ValueError("source_diversity_ratio is inconsistent with source counts")
    expected_confirmation = _safe_ratio(row.confirming_source_count, row.source_count)
    if row.source_confirmation_ratio != expected_confirmation:
        raise ValueError("source_confirmation_ratio is inconsistent with source counts")
    if row.start_status == READY_STATUS and row.reason_codes != (READY_REASON,):
        raise ValueError("ready rows must use ready reason")
    if row.start_status != READY_STATUS and row.reason_codes == (READY_REASON,):
        raise ValueError("non-ready rows must not use ready reason")


def _validate_report(report: MarketResearchHockeyGoalieStartDigestReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count must equal rows length")
    expected_counts = {
        "ready_observation_count": _status_count(report.rows, READY_STATUS),
        "watch_observation_count": _status_count(report.rows, WATCH_STATUS),
        "blocked_observation_count": _status_count(report.rows, BLOCKED_STATUS),
        "stale_start_report_count": _reason_observation_count(
            report.rows,
            STALE_START_REPORT_REASON,
        ),
        "stale_observation_count": _reason_observation_count(
            report.rows,
            STALE_OBSERVATION_REASON,
        ),
        "thin_source_count": _reason_observation_count(report.rows, THIN_SOURCES_REASON),
        "source_diversity_gap_count": _reason_observation_count(
            report.rows,
            SOURCE_DIVERSITY_GAP_REASON,
        ),
        "confirmation_gap_count": _reason_observation_count(
            report.rows,
            CONFIRMATION_GAP_REASON,
        ),
        "conflicting_source_count": _reason_observation_count(
            report.rows,
            CONFLICTING_SOURCES_REASON,
        ),
        "back_to_back_start_count": _reason_observation_count(
            report.rows,
            BACK_TO_BACK_START_REASON,
        ),
        "workload_fatigue_count": _reason_observation_count(
            report.rows,
            WORKLOAD_FATIGUE_REASON,
        ),
        "late_scratch_risk_count": _reason_observation_count(
            report.rows,
            LATE_SCRATCH_RISK_REASON,
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")
    if report.average_confidence_score != _average(row.confidence_score for row in report.rows):
        raise ValueError("average_confidence_score is inconsistent with rows")
    if report.average_source_count != _average(row.source_count for row in report.rows):
        raise ValueError("average_source_count is inconsistent with rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        if report.rows or report.reason_codes != (NO_INPUTS_REASON,):
            raise ValueError("reason_code_counts are inconsistent with rows")
    counted_reason_codes = tuple(item.reason_code for item in report.reason_code_counts)
    if report.reason_codes != counted_reason_codes:
        if report.digest_status != PASS_STATUS or report.reason_codes != tuple(
            sorted((*counted_reason_codes, PASSED_REASON)),
        ):
            raise ValueError("reason_codes are inconsistent with reason_code_counts")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty stripped string")


def _require_reference(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_reason_code(
    field_name: str,
    value: str,
    allowed: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} contains unknown reason_code")


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_DOWN)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    microseconds = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(microseconds / MICROSECONDS_PER_SECOND)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _average(values) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(sum(normalized, ZERO) / _decimal_count(len(normalized)))


def _max_or_none(values) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return max(normalized)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_DOWN).normalize()


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM, rounding=ROUND_DOWN)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _redacted_reference(value: str) -> str:
    if value.startswith("nhl-official-"):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) is float:
        raise ValueError("payload value must not be a float")
    return value

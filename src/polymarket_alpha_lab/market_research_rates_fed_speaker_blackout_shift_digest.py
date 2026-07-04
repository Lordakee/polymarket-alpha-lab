"""Pure Phase 1 rates Fed speaker blackout shift digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_FED_SPEAKER_BLACKOUT_SHIFT_DIGEST_CONFIG_VERSION",
    "RatesFedSpeakerBlackoutShiftDigestConfig",
    "RatesFedSpeakerBlackoutShiftObservation",
    "RatesFedSpeakerBlackoutShiftDigestRow",
    "RatesFedSpeakerBlackoutShiftReasonCodeCount",
    "RatesFedSpeakerBlackoutShiftDigestReport",
    "build_market_research_rates_fed_speaker_blackout_shift_digest",
    "market_research_rates_fed_speaker_blackout_shift_digest_payload",
)


DEFAULT_MARKET_RESEARCH_RATES_FED_SPEAKER_BLACKOUT_SHIFT_DIGEST_CONFIG_VERSION = (
    "market-research-rates-fed-speaker-blackout-shift-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
SECONDS_PER_HOUR = Decimal("3600.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SCHEDULE_RISK_WEIGHT = Decimal("0.300000")
TONE_RISK_WEIGHT = Decimal("0.250000")
MARKET_MOVE_RISK_WEIGHT = Decimal("0.300000")
BLACKOUT_RISK_WEIGHT = Decimal("0.150000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
SIGNAL_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: (
        "block_report_only_market_research_rates_fed_speaker_blackout_shift_digest"
    ),
    WATCH_STATUS: (
        "watch_report_only_market_research_rates_fed_speaker_blackout_shift_digest"
    ),
    PASS_STATUS: (
        "allow_report_only_market_research_rates_fed_speaker_blackout_shift_digest"
    ),
}

EMPTY_REASON = "rates_fed_speaker_blackout_shift_digest_empty"
SCHEDULE_UNCHANGED_REASON = "rates_fed_speaker_blackout_shift_schedule_unchanged"
SCHEDULE_WATCH_REASON = "rates_fed_speaker_blackout_shift_schedule_moved_watch"
SCHEDULE_BLOCKED_REASON = "rates_fed_speaker_blackout_shift_schedule_moved_blocked"
BLACKOUT_WATCH_REASON = "rates_fed_speaker_blackout_shift_blackout_proximity_watch"
BLACKOUT_BLOCKED_REASON = (
    "rates_fed_speaker_blackout_shift_blackout_proximity_blocked"
)
BLACKOUT_WINDOW_REASON = "rates_fed_speaker_blackout_shift_blackout_window_violation"
TONE_NONE_REASON = "rates_fed_speaker_blackout_shift_tone_none"
TONE_WATCH_REASON = "rates_fed_speaker_blackout_shift_tone_shift_watch"
TONE_BLOCKED_REASON = "rates_fed_speaker_blackout_shift_tone_shift_blocked"
TONE_HAWKISH_REASON = "rates_fed_speaker_blackout_shift_tone_hawkish"
TONE_DOVISH_REASON = "rates_fed_speaker_blackout_shift_tone_dovish"
TONE_BALANCED_REASON = "rates_fed_speaker_blackout_shift_tone_balanced"
MARKET_MOVE_WATCH_REASON = "rates_fed_speaker_blackout_shift_market_move_watch"
MARKET_MOVE_BLOCKED_REASON = "rates_fed_speaker_blackout_shift_market_move_blocked"
SOURCE_FRESH_REASON = "rates_fed_speaker_blackout_shift_source_fresh"
SOURCE_STALE_REASON = "rates_fed_speaker_blackout_shift_source_stale"
COMMUNICATION_CALM_REASON = (
    "rates_fed_speaker_blackout_shift_communication_risk_calm"
)
COMMUNICATION_WATCH_REASON = (
    "rates_fed_speaker_blackout_shift_communication_risk_watch"
)
COMMUNICATION_HIGH_REASON = "rates_fed_speaker_blackout_shift_communication_risk_high"

_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


@dataclass(frozen=True)
class RatesFedSpeakerBlackoutShiftDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_FED_SPEAKER_BLACKOUT_SHIFT_DIGEST_CONFIG_VERSION
    )
    watch_schedule_shift_hours: Decimal = Decimal("12.000000")
    blocked_schedule_shift_hours: Decimal = Decimal("24.000000")
    watch_blackout_proximity_hours: Decimal = Decimal("72.000000")
    blocked_blackout_proximity_hours: Decimal = Decimal("24.000000")
    watch_tone_shift_count: Decimal = Decimal("1.000000")
    blocked_tone_shift_count: Decimal = Decimal("2.000000")
    watch_market_move_score: Decimal = Decimal("0.250000")
    blocked_market_move_score: Decimal = Decimal("0.600000")
    watch_communication_risk_score: Decimal = Decimal("0.350000")
    blocked_communication_risk_score: Decimal = Decimal("0.650000")
    max_source_age_seconds: Decimal = Decimal("600.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    watch_confidence_cap: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFedSpeakerBlackoutShiftDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_FED_SPEAKER_BLACKOUT_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_schedule_shift_hours",
            "blocked_schedule_shift_hours",
            "watch_blackout_proximity_hours",
            "blocked_blackout_proximity_hours",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_tone_shift_count", "blocked_tone_shift_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_market_move_score",
            "blocked_market_move_score",
            "watch_communication_risk_score",
            "blocked_communication_risk_score",
            "stale_confidence_cap",
            "watch_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_schedule_shift_hours > self.blocked_schedule_shift_hours:
            raise ValueError(
                "watch_schedule_shift_hours must not exceed "
                "blocked_schedule_shift_hours",
            )
        if self.blocked_blackout_proximity_hours > self.watch_blackout_proximity_hours:
            raise ValueError(
                "blocked_blackout_proximity_hours must not exceed "
                "watch_blackout_proximity_hours",
            )
        if self.watch_tone_shift_count > self.blocked_tone_shift_count:
            raise ValueError(
                "watch_tone_shift_count must not exceed blocked_tone_shift_count",
            )
        if self.watch_market_move_score > self.blocked_market_move_score:
            raise ValueError(
                "watch_market_move_score must not exceed blocked_market_move_score",
            )
        if self.watch_communication_risk_score > self.blocked_communication_risk_score:
            raise ValueError(
                "watch_communication_risk_score must not exceed "
                "blocked_communication_risk_score",
            )
        if self.stale_confidence_cap > self.watch_confidence_cap:
            raise ValueError("stale_confidence_cap must not exceed watch_confidence_cap")
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFedSpeakerBlackoutShiftObservation:
    source_id: str
    market_slug: str
    meeting_id: str
    speaker_key: str
    scheduled_at: datetime
    previous_scheduled_at: datetime | None
    blackout_start_at: datetime
    blackout_end_at: datetime
    observed_at: datetime
    tone_shift_count: Decimal
    hawkish_tone_shift_count: Decimal
    dovish_tone_shift_count: Decimal
    market_move_score: Decimal
    base_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFedSpeakerBlackoutShiftObservation, "observation")
        for field_name in ("source_id", "market_slug", "meeting_id", "speaker_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "scheduled_at", _as_utc("scheduled_at", self.scheduled_at))
        object.__setattr__(
            self,
            "previous_scheduled_at",
            _as_optional_utc("previous_scheduled_at", self.previous_scheduled_at),
        )
        object.__setattr__(
            self,
            "blackout_start_at",
            _as_utc("blackout_start_at", self.blackout_start_at),
        )
        object.__setattr__(
            self,
            "blackout_end_at",
            _as_utc("blackout_end_at", self.blackout_end_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "tone_shift_count",
            "hawkish_tone_shift_count",
            "dovish_tone_shift_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_move_score", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        if self.blackout_end_at <= self.blackout_start_at:
            raise ValueError("blackout_end_at must be after blackout_start_at")
        _validate_tone_balance(
            tone_shift_count=self.tone_shift_count,
            hawkish_tone_shift_count=self.hawkish_tone_shift_count,
            dovish_tone_shift_count=self.dovish_tone_shift_count,
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFedSpeakerBlackoutShiftDigestRow:
    source_id: str
    market_slug: str
    meeting_id: str
    speaker_key: str
    scheduled_at: datetime
    previous_scheduled_at: datetime | None
    blackout_start_at: datetime
    blackout_end_at: datetime
    observed_at: datetime
    schedule_shift_hours: Decimal
    blackout_proximity_hours: Decimal
    tone_shift_count: Decimal
    hawkish_tone_shift_count: Decimal
    dovish_tone_shift_count: Decimal
    market_move_score: Decimal
    communication_risk_score: Decimal
    source_age_seconds: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    signal_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFedSpeakerBlackoutShiftDigestRow, "row")
        for field_name in ("source_id", "market_slug", "meeting_id", "speaker_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "scheduled_at", _as_utc("scheduled_at", self.scheduled_at))
        object.__setattr__(
            self,
            "previous_scheduled_at",
            _as_optional_utc("previous_scheduled_at", self.previous_scheduled_at),
        )
        object.__setattr__(
            self,
            "blackout_start_at",
            _as_utc("blackout_start_at", self.blackout_start_at),
        )
        object.__setattr__(
            self,
            "blackout_end_at",
            _as_utc("blackout_end_at", self.blackout_end_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "schedule_shift_hours",
            "blackout_proximity_hours",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "tone_shift_count",
            "hawkish_tone_shift_count",
            "dovish_tone_shift_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "market_move_score",
            "communication_risk_score",
            "base_confidence",
            "confidence_cap",
            "capped_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("signal_status", self.signal_status, SIGNAL_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFedSpeakerBlackoutShiftReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFedSpeakerBlackoutShiftReasonCodeCount, "reason")
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class RatesFedSpeakerBlackoutShiftDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_signal_count: Decimal
    watch_signal_count: Decimal
    pass_count: Decimal
    schedule_shift_count: Decimal
    blackout_proximity_count: Decimal
    tone_shift_event_count: Decimal
    total_tone_shift_count: Decimal
    hawkish_tone_shift_count: Decimal
    dovish_tone_shift_count: Decimal
    market_move_count: Decimal
    stale_source_count: Decimal
    max_schedule_shift_hours: Decimal
    min_blackout_proximity_hours: Decimal
    max_communication_risk_score: Decimal
    average_communication_risk_score: Decimal
    average_market_move_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[RatesFedSpeakerBlackoutShiftDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[RatesFedSpeakerBlackoutShiftReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesFedSpeakerBlackoutShiftDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_FED_SPEAKER_BLACKOUT_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_signal_count",
            "watch_signal_count",
            "pass_count",
            "schedule_shift_count",
            "blackout_proximity_count",
            "tone_shift_event_count",
            "total_tone_shift_count",
            "hawkish_tone_shift_count",
            "dovish_tone_shift_count",
            "market_move_count",
            "stale_source_count",
            "max_schedule_shift_hours",
            "min_blackout_proximity_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_communication_risk_score",
            "average_communication_risk_score",
            "average_market_move_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, SIGNAL_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self)


def build_market_research_rates_fed_speaker_blackout_shift_digest(
    observations: Iterable[RatesFedSpeakerBlackoutShiftObservation],
    *,
    config: RatesFedSpeakerBlackoutShiftDigestConfig,
    generated_at: datetime,
) -> RatesFedSpeakerBlackoutShiftDigestReport:
    if type(config) is not RatesFedSpeakerBlackoutShiftDigestConfig:
        raise ValueError("config must be exactly RatesFedSpeakerBlackoutShiftDigestConfig")
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations, generated_at=generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at,
                )
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    status = _digest_status(rows)
    return RatesFedSpeakerBlackoutShiftDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_signal_count=_status_count(rows, BLOCKED_STATUS),
        watch_signal_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        schedule_shift_count=_count_decimal(
            sum(1 for row in rows if row.schedule_shift_hours > ZERO),
        ),
        blackout_proximity_count=_blackout_proximity_count(rows),
        tone_shift_event_count=_count_decimal(
            sum(1 for row in rows if row.tone_shift_count > ZERO),
        ),
        total_tone_shift_count=_sum_decimal(row.tone_shift_count for row in rows),
        hawkish_tone_shift_count=_reason_count(rows, TONE_HAWKISH_REASON),
        dovish_tone_shift_count=_reason_count(rows, TONE_DOVISH_REASON),
        market_move_count=_count_decimal(
            sum(1 for row in rows if _has_market_move_reason(row)),
        ),
        stale_source_count=_reason_count(rows, SOURCE_STALE_REASON),
        max_schedule_shift_hours=_max_row_decimal(rows, "schedule_shift_hours"),
        min_blackout_proximity_hours=_min_row_decimal(rows, "blackout_proximity_hours"),
        max_communication_risk_score=_max_row_decimal(rows, "communication_risk_score"),
        average_communication_risk_score=_ratio(
            _sum_decimal(row.communication_risk_score for row in rows),
            row_count,
        ),
        average_market_move_score=_ratio(
            _sum_decimal(row.market_move_score for row in rows),
            row_count,
        ),
        digest_status=status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_rates_fed_speaker_blackout_shift_digest_payload(
    report: RatesFedSpeakerBlackoutShiftDigestReport,
) -> dict[str, Any]:
    if type(report) is not RatesFedSpeakerBlackoutShiftDigestReport:
        raise ValueError(
            "report must be exactly RatesFedSpeakerBlackoutShiftDigestReport",
        )
    return _payload_value(report)


def _row_from_observation(
    observation: RatesFedSpeakerBlackoutShiftObservation,
    *,
    config: RatesFedSpeakerBlackoutShiftDigestConfig,
    generated_at: datetime,
) -> RatesFedSpeakerBlackoutShiftDigestRow:
    schedule_shift_hours = _schedule_shift_hours(observation)
    blackout_proximity_hours = _blackout_proximity_hours(
        scheduled_at=observation.scheduled_at,
        blackout_start_at=observation.blackout_start_at,
        blackout_end_at=observation.blackout_end_at,
    )
    source_age_seconds = _seconds_between(generated_at, observation.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    communication_risk_score = _communication_risk_score(
        schedule_shift_hours=schedule_shift_hours,
        blackout_proximity_hours=blackout_proximity_hours,
        scheduled_at=observation.scheduled_at,
        blackout_start_at=observation.blackout_start_at,
        blackout_end_at=observation.blackout_end_at,
        tone_shift_count=observation.tone_shift_count,
        market_move_score=observation.market_move_score,
        config=config,
    )
    status = _signal_status(
        schedule_shift_hours=schedule_shift_hours,
        blackout_proximity_hours=blackout_proximity_hours,
        scheduled_at=observation.scheduled_at,
        blackout_start_at=observation.blackout_start_at,
        blackout_end_at=observation.blackout_end_at,
        tone_shift_count=observation.tone_shift_count,
        market_move_score=observation.market_move_score,
        communication_risk_score=communication_risk_score,
        config=config,
    )
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    return RatesFedSpeakerBlackoutShiftDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        meeting_id=observation.meeting_id,
        speaker_key=observation.speaker_key,
        scheduled_at=observation.scheduled_at,
        previous_scheduled_at=observation.previous_scheduled_at,
        blackout_start_at=observation.blackout_start_at,
        blackout_end_at=observation.blackout_end_at,
        observed_at=observation.observed_at,
        schedule_shift_hours=schedule_shift_hours,
        blackout_proximity_hours=blackout_proximity_hours,
        tone_shift_count=observation.tone_shift_count,
        hawkish_tone_shift_count=observation.hawkish_tone_shift_count,
        dovish_tone_shift_count=observation.dovish_tone_shift_count,
        market_move_score=observation.market_move_score,
        communication_risk_score=communication_risk_score,
        source_age_seconds=source_age_seconds,
        base_confidence=observation.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=_quantize_decimal(min(observation.base_confidence, confidence_cap)),
        signal_status=status,
        reason_codes=_row_reason_codes(
            observation.upstream_reason_codes,
            schedule_shift_hours=schedule_shift_hours,
            blackout_proximity_hours=blackout_proximity_hours,
            scheduled_at=observation.scheduled_at,
            blackout_start_at=observation.blackout_start_at,
            blackout_end_at=observation.blackout_end_at,
            tone_shift_count=observation.tone_shift_count,
            hawkish_tone_shift_count=observation.hawkish_tone_shift_count,
            dovish_tone_shift_count=observation.dovish_tone_shift_count,
            market_move_score=observation.market_move_score,
            source_fresh=source_fresh,
            status=status,
            config=config,
        ),
    )


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    schedule_shift_hours: Decimal,
    blackout_proximity_hours: Decimal,
    scheduled_at: datetime,
    blackout_start_at: datetime,
    blackout_end_at: datetime,
    tone_shift_count: Decimal,
    hawkish_tone_shift_count: Decimal,
    dovish_tone_shift_count: Decimal,
    market_move_score: Decimal,
    source_fresh: bool,
    status: str,
    config: RatesFedSpeakerBlackoutShiftDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if schedule_shift_hours >= config.blocked_schedule_shift_hours:
        reason_codes.append(SCHEDULE_BLOCKED_REASON)
    elif schedule_shift_hours >= config.watch_schedule_shift_hours:
        reason_codes.append(SCHEDULE_WATCH_REASON)
    else:
        reason_codes.append(SCHEDULE_UNCHANGED_REASON)

    if _scheduled_inside_blackout(
        scheduled_at=scheduled_at,
        blackout_start_at=blackout_start_at,
        blackout_end_at=blackout_end_at,
    ):
        reason_codes.append(BLACKOUT_WINDOW_REASON)
    elif scheduled_at < blackout_start_at:
        if blackout_proximity_hours <= config.blocked_blackout_proximity_hours:
            reason_codes.append(BLACKOUT_BLOCKED_REASON)
        elif blackout_proximity_hours <= config.watch_blackout_proximity_hours:
            reason_codes.append(BLACKOUT_WATCH_REASON)

    if tone_shift_count == ZERO:
        reason_codes.append(TONE_NONE_REASON)
    else:
        if tone_shift_count >= config.blocked_tone_shift_count:
            reason_codes.append(TONE_BLOCKED_REASON)
        elif tone_shift_count >= config.watch_tone_shift_count:
            reason_codes.append(TONE_WATCH_REASON)
        if hawkish_tone_shift_count > dovish_tone_shift_count:
            reason_codes.append(TONE_HAWKISH_REASON)
        elif dovish_tone_shift_count > hawkish_tone_shift_count:
            reason_codes.append(TONE_DOVISH_REASON)
        else:
            reason_codes.append(TONE_BALANCED_REASON)

    if market_move_score >= config.blocked_market_move_score:
        reason_codes.append(MARKET_MOVE_BLOCKED_REASON)
    elif market_move_score >= config.watch_market_move_score:
        reason_codes.append(MARKET_MOVE_WATCH_REASON)

    reason_codes.append(SOURCE_FRESH_REASON if source_fresh else SOURCE_STALE_REASON)
    if status == BLOCKED_STATUS:
        reason_codes.append(COMMUNICATION_HIGH_REASON)
    elif status == WATCH_STATUS:
        reason_codes.append(COMMUNICATION_WATCH_REASON)
    else:
        reason_codes.append(COMMUNICATION_CALM_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _signal_status(
    *,
    schedule_shift_hours: Decimal,
    blackout_proximity_hours: Decimal,
    scheduled_at: datetime,
    blackout_start_at: datetime,
    blackout_end_at: datetime,
    tone_shift_count: Decimal,
    market_move_score: Decimal,
    communication_risk_score: Decimal,
    config: RatesFedSpeakerBlackoutShiftDigestConfig,
) -> str:
    if (
        schedule_shift_hours >= config.blocked_schedule_shift_hours
        or _scheduled_inside_blackout(
            scheduled_at=scheduled_at,
            blackout_start_at=blackout_start_at,
            blackout_end_at=blackout_end_at,
        )
        or (
            scheduled_at < blackout_start_at
            and blackout_proximity_hours <= config.blocked_blackout_proximity_hours
        )
        or tone_shift_count >= config.blocked_tone_shift_count
        or market_move_score >= config.blocked_market_move_score
        or communication_risk_score >= config.blocked_communication_risk_score
    ):
        return BLOCKED_STATUS
    if (
        schedule_shift_hours >= config.watch_schedule_shift_hours
        or (
            scheduled_at < blackout_start_at
            and blackout_proximity_hours <= config.watch_blackout_proximity_hours
        )
        or tone_shift_count >= config.watch_tone_shift_count
        or market_move_score >= config.watch_market_move_score
        or communication_risk_score >= config.watch_communication_risk_score
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _communication_risk_score(
    *,
    schedule_shift_hours: Decimal,
    blackout_proximity_hours: Decimal,
    scheduled_at: datetime,
    blackout_start_at: datetime,
    blackout_end_at: datetime,
    tone_shift_count: Decimal,
    market_move_score: Decimal,
    config: RatesFedSpeakerBlackoutShiftDigestConfig,
) -> Decimal:
    schedule_component = min(
        ONE,
        _ratio(schedule_shift_hours, config.blocked_schedule_shift_hours),
    )
    tone_component = min(ONE, _ratio(tone_shift_count, config.blocked_tone_shift_count))
    blackout_component = _blackout_component(
        scheduled_at=scheduled_at,
        blackout_start_at=blackout_start_at,
        blackout_end_at=blackout_end_at,
        blackout_proximity_hours=blackout_proximity_hours,
        config=config,
    )
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            schedule_component * SCHEDULE_RISK_WEIGHT
            + tone_component * TONE_RISK_WEIGHT
            + market_move_score * MARKET_MOVE_RISK_WEIGHT
            + blackout_component * BLACKOUT_RISK_WEIGHT,
        )


def _blackout_component(
    *,
    scheduled_at: datetime,
    blackout_start_at: datetime,
    blackout_end_at: datetime,
    blackout_proximity_hours: Decimal,
    config: RatesFedSpeakerBlackoutShiftDigestConfig,
) -> Decimal:
    if _scheduled_inside_blackout(
        scheduled_at=scheduled_at,
        blackout_start_at=blackout_start_at,
        blackout_end_at=blackout_end_at,
    ):
        return ONE
    if scheduled_at >= blackout_start_at:
        return ZERO
    if blackout_proximity_hours <= config.blocked_blackout_proximity_hours:
        return ONE
    if blackout_proximity_hours <= config.watch_blackout_proximity_hours:
        return HALF
    return ZERO


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: RatesFedSpeakerBlackoutShiftDigestConfig,
) -> Decimal:
    caps = [ONE]
    if status in (BLOCKED_STATUS, WATCH_STATUS):
        caps.append(config.watch_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _digest_status(rows: tuple[RatesFedSpeakerBlackoutShiftDigestRow, ...]) -> str:
    if not rows or any(row.signal_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.signal_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[RatesFedSpeakerBlackoutShiftDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[RatesFedSpeakerBlackoutShiftDigestRow, ...],
) -> tuple[RatesFedSpeakerBlackoutShiftReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (EMPTY_REASON,):
        return (
            RatesFedSpeakerBlackoutShiftReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        RatesFedSpeakerBlackoutShiftReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[RatesFedSpeakerBlackoutShiftObservation],
    *,
    generated_at: datetime,
) -> tuple[RatesFedSpeakerBlackoutShiftObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not RatesFedSpeakerBlackoutShiftObservation:
            raise ValueError(
                "observations must contain RatesFedSpeakerBlackoutShiftObservation",
            )
        _require_hard_flags(observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return normalized


def _normalize_rows(
    rows: Iterable[RatesFedSpeakerBlackoutShiftDigestRow],
) -> tuple[RatesFedSpeakerBlackoutShiftDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not RatesFedSpeakerBlackoutShiftDigestRow:
            raise ValueError("rows must contain RatesFedSpeakerBlackoutShiftDigestRow")
        _require_hard_flags(row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[RatesFedSpeakerBlackoutShiftReasonCodeCount],
) -> tuple[RatesFedSpeakerBlackoutShiftReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    seen_reason_codes: set[str] = set()
    for value in normalized:
        if type(value) is not RatesFedSpeakerBlackoutShiftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "RatesFedSpeakerBlackoutShiftReasonCodeCount",
            )
        _require_hard_flags(value)
        if value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code")
        seen_reason_codes.add(value.reason_code)
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _normalize_reason_codes(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("reason_code", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _row_sort_key(
    row: RatesFedSpeakerBlackoutShiftDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.signal_status],
        -row.communication_risk_score,
        -row.schedule_shift_hours,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[RatesFedSpeakerBlackoutShiftDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.signal_status == status))


def _reason_count(
    rows: tuple[RatesFedSpeakerBlackoutShiftDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _blackout_proximity_count(
    rows: tuple[RatesFedSpeakerBlackoutShiftDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if (
                BLACKOUT_WATCH_REASON in row.reason_codes
                or BLACKOUT_BLOCKED_REASON in row.reason_codes
                or BLACKOUT_WINDOW_REASON in row.reason_codes
            )
        ),
    )


def _has_market_move_reason(row: RatesFedSpeakerBlackoutShiftDigestRow) -> bool:
    return (
        MARKET_MOVE_WATCH_REASON in row.reason_codes
        or MARKET_MOVE_BLOCKED_REASON in row.reason_codes
    )


def _max_row_decimal(
    rows: tuple[RatesFedSpeakerBlackoutShiftDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[RatesFedSpeakerBlackoutShiftDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _schedule_shift_hours(observation: RatesFedSpeakerBlackoutShiftObservation) -> Decimal:
    if observation.previous_scheduled_at is None:
        return ZERO
    earlier, later = sorted((observation.previous_scheduled_at, observation.scheduled_at))
    return _hours_between(later, earlier)


def _blackout_proximity_hours(
    *,
    scheduled_at: datetime,
    blackout_start_at: datetime,
    blackout_end_at: datetime,
) -> Decimal:
    if scheduled_at < blackout_start_at:
        return _hours_between(blackout_start_at, scheduled_at)
    if scheduled_at <= blackout_end_at:
        return ZERO
    return _hours_between(scheduled_at, blackout_end_at)


def _scheduled_inside_blackout(
    *,
    scheduled_at: datetime,
    blackout_start_at: datetime,
    blackout_end_at: datetime,
) -> bool:
    return blackout_start_at <= scheduled_at <= blackout_end_at


def _validate_tone_balance(
    *,
    tone_shift_count: Decimal,
    hawkish_tone_shift_count: Decimal,
    dovish_tone_shift_count: Decimal,
) -> None:
    if tone_shift_count != _quantize_decimal(
        hawkish_tone_shift_count + dovish_tone_shift_count,
    ):
        raise ValueError("tone_shift_count must equal hawkish plus dovish tone shifts")


def _validate_row(row: RatesFedSpeakerBlackoutShiftDigestRow) -> None:
    if row.blackout_end_at <= row.blackout_start_at:
        raise ValueError("blackout_end_at must be after blackout_start_at")
    _validate_tone_balance(
        tone_shift_count=row.tone_shift_count,
        hawkish_tone_shift_count=row.hawkish_tone_shift_count,
        dovish_tone_shift_count=row.dovish_tone_shift_count,
    )
    if row.schedule_shift_hours != _schedule_shift_hours_from_row(row):
        raise ValueError("schedule_shift_hours must match scheduled_at values")
    if row.blackout_proximity_hours != _blackout_proximity_hours(
        scheduled_at=row.scheduled_at,
        blackout_start_at=row.blackout_start_at,
        blackout_end_at=row.blackout_end_at,
    ):
        raise ValueError("blackout_proximity_hours must match blackout window")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    if row.signal_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("signal_status must match reason_codes")


def _schedule_shift_hours_from_row(row: RatesFedSpeakerBlackoutShiftDigestRow) -> Decimal:
    if row.previous_scheduled_at is None:
        return ZERO
    earlier, later = sorted((row.previous_scheduled_at, row.scheduled_at))
    return _hours_between(later, earlier)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if COMMUNICATION_HIGH_REASON in reason_codes:
        return BLOCKED_STATUS
    if COMMUNICATION_WATCH_REASON in reason_codes:
        return WATCH_STATUS
    return PASS_STATUS


def _validate_report(report: RatesFedSpeakerBlackoutShiftDigestReport) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_signal_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_signal_count must match rows")
    if report.watch_signal_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_signal_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.schedule_shift_count != _count_decimal(
        sum(1 for row in report.rows if row.schedule_shift_hours > ZERO),
    ):
        raise ValueError("schedule_shift_count must match rows")
    if report.blackout_proximity_count != _blackout_proximity_count(report.rows):
        raise ValueError("blackout_proximity_count must match rows")
    if report.tone_shift_event_count != _count_decimal(
        sum(1 for row in report.rows if row.tone_shift_count > ZERO),
    ):
        raise ValueError("tone_shift_event_count must match rows")
    if report.total_tone_shift_count != _sum_decimal(
        (row.tone_shift_count for row in report.rows),
    ):
        raise ValueError("total_tone_shift_count must match rows")
    if report.hawkish_tone_shift_count != _reason_count(
        report.rows,
        TONE_HAWKISH_REASON,
    ):
        raise ValueError("hawkish_tone_shift_count must match rows")
    if report.dovish_tone_shift_count != _reason_count(report.rows, TONE_DOVISH_REASON):
        raise ValueError("dovish_tone_shift_count must match rows")
    if report.market_move_count != _count_decimal(
        sum(1 for row in report.rows if _has_market_move_reason(row)),
    ):
        raise ValueError("market_move_count must match rows")
    if report.stale_source_count != _reason_count(report.rows, SOURCE_STALE_REASON):
        raise ValueError("stale_source_count must match rows")
    if report.max_schedule_shift_hours != _max_row_decimal(
        report.rows,
        "schedule_shift_hours",
    ):
        raise ValueError("max_schedule_shift_hours must match rows")
    if report.min_blackout_proximity_hours != _min_row_decimal(
        report.rows,
        "blackout_proximity_hours",
    ):
        raise ValueError("min_blackout_proximity_hours must match rows")
    if report.max_communication_risk_score != _max_row_decimal(
        report.rows,
        "communication_risk_score",
    ):
        raise ValueError("max_communication_risk_score must match rows")
    if report.average_communication_risk_score != _ratio(
        _sum_decimal(row.communication_risk_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_communication_risk_score must match rows")
    if report.average_market_move_score != _ratio(
        _sum_decimal(row.market_move_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_market_move_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize_decimal(seconds + microseconds)


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    return _ratio(_seconds_between(later, earlier), SECONDS_PER_HOUR)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_whole_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
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
    return value

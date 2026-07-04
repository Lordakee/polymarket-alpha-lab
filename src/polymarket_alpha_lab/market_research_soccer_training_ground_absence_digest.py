"""Pure Phase 1 reducer for soccer training-ground absence research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_SOCCER_TRAINING_GROUND_ABSENCE_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-training-ground-absence-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal("3600")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = 86400
MICROSECONDS_PER_WHOLE_SECOND = 1000000

ABSENCE_COUNT_WEIGHT = Decimal("0.250000")
ROLE_IMPORTANCE_WEIGHT = Decimal("0.200000")
MATCH_PROXIMITY_WEIGHT = Decimal("0.150000")
LINEUP_DEPENDENCY_WEIGHT = Decimal("0.200000")
SOURCE_STALENESS_WEIGHT = Decimal("0.100000")
SOURCE_DISAGREEMENT_WEIGHT = Decimal("0.100000")

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_STATUSES = DIGEST_STATUSES

SOURCE_DISAGREEMENT_REASON = "soccer_training_ground_absence_source_disagreement"
RISK_BLOCKED_REASON = "soccer_training_ground_absence_risk_score_blocked"
ABSENCE_BLOCKED_REASON = "soccer_training_ground_absence_absence_count_blocked"
MATCH_PROXIMITY_BLOCKED_REASON = (
    "soccer_training_ground_absence_match_proximity_blocked"
)
RISK_WATCH_REASON = "soccer_training_ground_absence_risk_score_watch"
ABSENCE_WATCH_REASON = "soccer_training_ground_absence_absence_count_watch"
ROLE_IMPORTANCE_REASON = "soccer_training_ground_absence_role_importance_high"
LINEUP_DEPENDENCY_REASON = "soccer_training_ground_absence_lineup_dependency_high"
SOURCE_STALE_REASON = "soccer_training_ground_absence_source_stale"
UPSTREAM_REASON = "soccer_training_ground_absence_upstream_reason_present"
CLEAR_REASON = "soccer_training_ground_absence_clear"
PASSED_REASON = "soccer_training_ground_absence_passed"
EMPTY_REASON = "soccer_training_ground_absence_empty"

ROW_REASON_CODES = (
    SOURCE_DISAGREEMENT_REASON,
    RISK_BLOCKED_REASON,
    ABSENCE_BLOCKED_REASON,
    MATCH_PROXIMITY_BLOCKED_REASON,
    RISK_WATCH_REASON,
    ABSENCE_WATCH_REASON,
    ROLE_IMPORTANCE_REASON,
    LINEUP_DEPENDENCY_REASON,
    SOURCE_STALE_REASON,
    UPSTREAM_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    SOURCE_DISAGREEMENT_REASON,
    RISK_BLOCKED_REASON,
    ABSENCE_BLOCKED_REASON,
    MATCH_PROXIMITY_BLOCKED_REASON,
    RISK_WATCH_REASON,
    ABSENCE_WATCH_REASON,
    ROLE_IMPORTANCE_REASON,
    LINEUP_DEPENDENCY_REASON,
    SOURCE_STALE_REASON,
    UPSTREAM_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))
BLOCKED_ROW_REASONS = (
    SOURCE_DISAGREEMENT_REASON,
    RISK_BLOCKED_REASON,
    ABSENCE_BLOCKED_REASON,
    MATCH_PROXIMITY_BLOCKED_REASON,
)

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_soccer_training_ground_absence_monitoring",
    WATCH_STATUS: "review_report_only_soccer_training_ground_absence_watchlist",
    BLOCKED_STATUS: "block_report_only_soccer_training_ground_absence_review",
}

_BLOCKED_WORDS = (
    "wal" "let",
    "bro" "ker",
    "ord" "er",
    "acc" "ount",
    "ad" "vice",
    "au" "th",
    "cred" "ential",
    "sign" "ing",
    "sub" "mit",
    "can" "cel",
    "rep" "lace",
    "ex" "change",
    "sec" "ret",
    "priv" "ate",
    "mut" "ation",
    "data" "base",
    "per" "sist",
    "pay" "load_" "json",
    "net" "work",
    "sock" "et",
    "ht" "tp",
    "psy" "copg",
    "supa" "base",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_SOCCER_TRAINING_GROUND_ABSENCE_DIGEST_CONFIG_VERSION",
    "MarketResearchSoccerTrainingGroundAbsenceDigestConfig",
    "MarketResearchSoccerTrainingGroundAbsenceDigestSignal",
    "MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount",
    "MarketResearchSoccerTrainingGroundAbsenceDigestRow",
    "MarketResearchSoccerTrainingGroundAbsenceDigestReport",
    "build_market_research_soccer_training_ground_absence_digest",
    "market_research_soccer_training_ground_absence_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchSoccerTrainingGroundAbsenceDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_TRAINING_GROUND_ABSENCE_DIGEST_CONFIG_VERSION
    )
    blocked_risk_score_threshold: Decimal = Decimal("0.700000")
    watch_risk_score_threshold: Decimal = Decimal("0.400000")
    blocked_absence_count: Decimal = Decimal("2.000000")
    watch_absence_count: Decimal = Decimal("1.000000")
    high_role_importance_threshold: Decimal = Decimal("0.700000")
    high_lineup_dependency_threshold: Decimal = Decimal("0.600000")
    match_proximity_blocked_hours: Decimal = Decimal("6.000000")
    match_proximity_watch_hours: Decimal = Decimal("36.000000")
    max_source_age_hours: Decimal = Decimal("6.000000")
    max_source_disagreement_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerTrainingGroundAbsenceDigestConfig:
            raise TypeError(
                "MarketResearchSoccerTrainingGroundAbsenceDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerTrainingGroundAbsenceDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchSoccerTrainingGroundAbsenceDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "blocked_risk_score_threshold",
            "watch_risk_score_threshold",
            "high_role_importance_threshold",
            "high_lineup_dependency_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "blocked_absence_count",
            "watch_absence_count",
            "max_source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "match_proximity_blocked_hours",
            "match_proximity_watch_hours",
            "max_source_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_risk_score_threshold > self.blocked_risk_score_threshold:
            raise ValueError(
                "watch_risk_score_threshold must not exceed "
                "blocked_risk_score_threshold",
            )
        if self.watch_absence_count > self.blocked_absence_count:
            raise ValueError("watch_absence_count must not exceed blocked_absence_count")
        if self.blocked_absence_count == ZERO:
            raise ValueError("blocked_absence_count must be positive")
        if self.match_proximity_blocked_hours > self.match_proximity_watch_hours:
            raise ValueError(
                "match_proximity_blocked_hours must not exceed "
                "match_proximity_watch_hours",
            )
        if self.match_proximity_watch_hours == ZERO:
            raise ValueError("match_proximity_watch_hours must be positive")
        if self.max_source_age_hours == ZERO:
            raise ValueError("max_source_age_hours must be positive")
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchSoccerTrainingGroundAbsenceDigestSignal:
    condition_id: str
    market_slug: str
    club: str
    player: str
    opponent: str
    match_ref: str
    match_start_at: datetime
    observed_at: datetime
    absence_count: Decimal
    role_importance_score: Decimal
    lineup_dependency_score: Decimal
    source_disagreement_count: Decimal
    upstream_reason_codes: tuple[str, ...]
    signal_ref: str
    signal_config_version: str = "soccer-training-ground-absence-feed-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerTrainingGroundAbsenceDigestSignal:
            raise TypeError(
                "MarketResearchSoccerTrainingGroundAbsenceDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerTrainingGroundAbsenceDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchSoccerTrainingGroundAbsenceDigestSignal",
            )
        for field_name in (
            "condition_id",
            "market_slug",
            "club",
            "player",
            "opponent",
            "match_ref",
            "signal_ref",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "match_start_at",
            _as_utc("match_start_at", self.match_start_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "absence_count",
            _normalize_nonnegative_whole_decimal("absence_count", self.absence_count),
        )
        for field_name in (
            "role_importance_score",
            "lineup_dependency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_disagreement_count",
            _normalize_nonnegative_whole_decimal(
                "source_disagreement_count",
                self.source_disagreement_count,
            ),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount:
    reason_code: str
    signal_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount
        ):
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "signal_count",
            _normalize_nonnegative_whole_decimal("signal_count", self.signal_count),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchSoccerTrainingGroundAbsenceDigestRow:
    condition_id: str
    market_slug: str
    club: str
    player: str
    opponent: str
    match_ref: str
    match_start_at: datetime
    observed_at: datetime
    absence_count: Decimal
    role_importance_score: Decimal
    lineup_dependency_score: Decimal
    source_disagreement_count: Decimal
    match_proximity_hours: Decimal
    source_age_hours: Decimal
    risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    signal_ref: str
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerTrainingGroundAbsenceDigestRow:
            raise TypeError(
                "MarketResearchSoccerTrainingGroundAbsenceDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerTrainingGroundAbsenceDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchSoccerTrainingGroundAbsenceDigestRow",
            )
        for field_name in (
            "condition_id",
            "market_slug",
            "club",
            "player",
            "opponent",
            "match_ref",
            "signal_ref",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "match_start_at",
            _as_utc("match_start_at", self.match_start_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "absence_count",
            "source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "role_importance_score",
            "lineup_dependency_score",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "match_proximity_hours",
            "source_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchSoccerTrainingGroundAbsenceDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    pass_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    source_disagreement_signal_count: Decimal
    blocked_risk_signal_count: Decimal
    watch_risk_signal_count: Decimal
    blocked_absence_signal_count: Decimal
    watch_absence_signal_count: Decimal
    high_role_importance_signal_count: Decimal
    high_lineup_dependency_signal_count: Decimal
    close_match_signal_count: Decimal
    stale_source_signal_count: Decimal
    upstream_reason_signal_count: Decimal
    blocked_risk_score_threshold: Decimal
    watch_risk_score_threshold: Decimal
    blocked_absence_count: Decimal
    watch_absence_count: Decimal
    high_role_importance_threshold: Decimal
    high_lineup_dependency_threshold: Decimal
    match_proximity_blocked_hours: Decimal
    match_proximity_watch_hours: Decimal
    max_source_age_hours: Decimal
    max_source_disagreement_count: Decimal
    max_risk_score: Decimal
    average_risk_score: Decimal
    rows: tuple[MarketResearchSoccerTrainingGroundAbsenceDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str, str, str], ...]
    reason_code_counts: tuple[
        MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerTrainingGroundAbsenceDigestReport:
            raise TypeError(
                "MarketResearchSoccerTrainingGroundAbsenceDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerTrainingGroundAbsenceDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchSoccerTrainingGroundAbsenceDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "pass_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "source_disagreement_signal_count",
            "blocked_risk_signal_count",
            "watch_risk_signal_count",
            "blocked_absence_signal_count",
            "watch_absence_signal_count",
            "high_role_importance_signal_count",
            "high_lineup_dependency_signal_count",
            "close_match_signal_count",
            "stale_source_signal_count",
            "upstream_reason_signal_count",
            "blocked_absence_count",
            "watch_absence_count",
            "max_source_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "blocked_risk_score_threshold",
            "watch_risk_score_threshold",
            "high_role_importance_threshold",
            "high_lineup_dependency_threshold",
            "max_risk_score",
            "average_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "match_proximity_blocked_hours",
            "match_proximity_watch_hours",
            "max_source_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "signal_config_versions",
            _normalize_signal_config_versions(self.signal_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, DIGEST_REASON_CODES),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_soccer_training_ground_absence_digest(
    signals: Iterable[MarketResearchSoccerTrainingGroundAbsenceDigestSignal],
    *,
    config: MarketResearchSoccerTrainingGroundAbsenceDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerTrainingGroundAbsenceDigestReport:
    if type(config) is not MarketResearchSoccerTrainingGroundAbsenceDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchSoccerTrainingGroundAbsenceDigestConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be exactly datetime")
    generated_at_utc = _as_utc("generated_at", generated_at)
    signal_items = _normalize_signals(signals)
    for signal in signal_items:
        if signal.match_start_at < generated_at_utc:
            raise ValueError("match_start_at must not be in the past")
        if signal.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    rows = tuple(
        sorted(
            (
                _row_for_signal(
                    signal,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for signal in signal_items
            ),
            key=_row_sort_rank,
        ),
    )
    row_reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        digest_status = BLOCKED_STATUS
    elif any(row.digest_status == WATCH_STATUS for row in rows):
        digest_status = WATCH_STATUS
    else:
        digest_status = PASS_STATUS
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    return MarketResearchSoccerTrainingGroundAbsenceDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        signal_count=_whole(len(rows)),
        pass_signal_count=_count_rows(rows, PASS_STATUS),
        watch_signal_count=_count_rows(rows, WATCH_STATUS),
        blocked_signal_count=_count_rows(rows, BLOCKED_STATUS),
        source_disagreement_signal_count=_count_reason(
            rows,
            SOURCE_DISAGREEMENT_REASON,
        ),
        blocked_risk_signal_count=_count_reason(rows, RISK_BLOCKED_REASON),
        watch_risk_signal_count=_count_reason(rows, RISK_WATCH_REASON),
        blocked_absence_signal_count=_count_reason(rows, ABSENCE_BLOCKED_REASON),
        watch_absence_signal_count=_count_reason(rows, ABSENCE_WATCH_REASON),
        high_role_importance_signal_count=_count_reason(rows, ROLE_IMPORTANCE_REASON),
        high_lineup_dependency_signal_count=_count_reason(
            rows,
            LINEUP_DEPENDENCY_REASON,
        ),
        close_match_signal_count=_count_reason(rows, MATCH_PROXIMITY_BLOCKED_REASON),
        stale_source_signal_count=_count_reason(rows, SOURCE_STALE_REASON),
        upstream_reason_signal_count=_count_reason(rows, UPSTREAM_REASON),
        blocked_risk_score_threshold=config.blocked_risk_score_threshold,
        watch_risk_score_threshold=config.watch_risk_score_threshold,
        blocked_absence_count=config.blocked_absence_count,
        watch_absence_count=config.watch_absence_count,
        high_role_importance_threshold=config.high_role_importance_threshold,
        high_lineup_dependency_threshold=config.high_lineup_dependency_threshold,
        match_proximity_blocked_hours=config.match_proximity_blocked_hours,
        match_proximity_watch_hours=config.match_proximity_watch_hours,
        max_source_age_hours=config.max_source_age_hours,
        max_source_disagreement_count=config.max_source_disagreement_count,
        max_risk_score=_max_or_zero(row.risk_score for row in rows),
        average_risk_score=_average(row.risk_score for row in rows),
        rows=rows,
        signal_config_versions=tuple(
            sorted(
                {
                    (
                        signal.match_ref,
                        signal.club,
                        signal.player,
                        signal.signal_config_version,
                    )
                    for signal in signal_items
                },
            ),
        ),
        reason_code_counts=_reason_code_counts(row_reason_codes),
        reason_codes=reason_codes,
    )


def market_research_soccer_training_ground_absence_digest_payload(
    report: MarketResearchSoccerTrainingGroundAbsenceDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchSoccerTrainingGroundAbsenceDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchSoccerTrainingGroundAbsenceDigestReport",
        )
    _require_flags("report", report)
    return _to_plain(report)


def _row_for_signal(
    signal: MarketResearchSoccerTrainingGroundAbsenceDigestSignal,
    *,
    config: MarketResearchSoccerTrainingGroundAbsenceDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerTrainingGroundAbsenceDigestRow:
    match_proximity_hours = _duration_hours(generated_at, signal.match_start_at)
    source_age_hours = _duration_hours(signal.observed_at, generated_at)
    risk_score = _risk_score(
        signal,
        config=config,
        match_proximity_hours=match_proximity_hours,
        source_age_hours=source_age_hours,
    )

    reason_codes = []
    if signal.source_disagreement_count > config.max_source_disagreement_count:
        reason_codes.append(SOURCE_DISAGREEMENT_REASON)
    if risk_score >= config.blocked_risk_score_threshold:
        reason_codes.append(RISK_BLOCKED_REASON)
    elif risk_score >= config.watch_risk_score_threshold:
        reason_codes.append(RISK_WATCH_REASON)
    if signal.absence_count >= config.blocked_absence_count:
        reason_codes.append(ABSENCE_BLOCKED_REASON)
    elif signal.absence_count >= config.watch_absence_count:
        reason_codes.append(ABSENCE_WATCH_REASON)
    if match_proximity_hours <= config.match_proximity_blocked_hours:
        reason_codes.append(MATCH_PROXIMITY_BLOCKED_REASON)
    if signal.role_importance_score >= config.high_role_importance_threshold:
        reason_codes.append(ROLE_IMPORTANCE_REASON)
    if signal.lineup_dependency_score >= config.high_lineup_dependency_threshold:
        reason_codes.append(LINEUP_DEPENDENCY_REASON)
    if source_age_hours > config.max_source_age_hours:
        reason_codes.append(SOURCE_STALE_REASON)
    if signal.upstream_reason_codes:
        reason_codes.append(UPSTREAM_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    sorted_reason_codes = _sort_reason_codes(reason_codes, ROW_REASON_CODES)

    return MarketResearchSoccerTrainingGroundAbsenceDigestRow(
        condition_id=signal.condition_id,
        market_slug=signal.market_slug,
        club=signal.club,
        player=signal.player,
        opponent=signal.opponent,
        match_ref=signal.match_ref,
        match_start_at=signal.match_start_at,
        observed_at=signal.observed_at,
        absence_count=signal.absence_count,
        role_importance_score=signal.role_importance_score,
        lineup_dependency_score=signal.lineup_dependency_score,
        source_disagreement_count=signal.source_disagreement_count,
        match_proximity_hours=match_proximity_hours,
        source_age_hours=source_age_hours,
        risk_score=risk_score,
        upstream_reason_codes=signal.upstream_reason_codes,
        signal_ref=signal.signal_ref,
        digest_status=_row_status(sorted_reason_codes),
        reason_codes=sorted_reason_codes,
    )


def _risk_score(
    signal: MarketResearchSoccerTrainingGroundAbsenceDigestSignal,
    *,
    config: MarketResearchSoccerTrainingGroundAbsenceDigestConfig,
    match_proximity_hours: Decimal,
    source_age_hours: Decimal,
) -> Decimal:
    absence_pressure = _capped_ratio(signal.absence_count, config.blocked_absence_count)
    match_pressure = ZERO
    if match_proximity_hours < config.match_proximity_watch_hours:
        match_pressure = _capped_ratio(
            config.match_proximity_watch_hours - match_proximity_hours,
            config.match_proximity_watch_hours,
        )
    source_pressure = _capped_ratio(source_age_hours, config.max_source_age_hours)
    disagreement_pressure = _capped_ratio(
        signal.source_disagreement_count,
        config.max_source_disagreement_count + ONE,
    )
    return _quantize(
        (absence_pressure * ABSENCE_COUNT_WEIGHT)
        + (signal.role_importance_score * ROLE_IMPORTANCE_WEIGHT)
        + (match_pressure * MATCH_PROXIMITY_WEIGHT)
        + (signal.lineup_dependency_score * LINEUP_DEPENDENCY_WEIGHT)
        + (source_pressure * SOURCE_STALENESS_WEIGHT)
        + (disagreement_pressure * SOURCE_DISAGREEMENT_WEIGHT),
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code=reason_code,
            signal_count=_whole(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_signals(
    signals: Iterable[MarketResearchSoccerTrainingGroundAbsenceDigestSignal],
) -> tuple[MarketResearchSoccerTrainingGroundAbsenceDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must contain soccer training-ground absence items")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError(
            "signals must contain soccer training-ground absence items",
        ) from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        if type(signal) is not MarketResearchSoccerTrainingGroundAbsenceDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchSoccerTrainingGroundAbsenceDigestSignal items",
            )
        _require_flags("signal", signal)
        identifier = (signal.match_ref, signal.club, signal.player)
        if identifier in seen:
            raise ValueError("signals must not contain duplicate match/club/player values")
        seen.add(identifier)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchSoccerTrainingGroundAbsenceDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchSoccerTrainingGroundAbsenceDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchSoccerTrainingGroundAbsenceDigestRow items",
            )
        _require_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_rank)):
        raise ValueError("rows must be sorted deterministically")
    identifiers = tuple((row.match_ref, row.club, row.player) for row in normalized)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("rows must not contain duplicate match/club/player values")
    return normalized


def _normalize_signal_config_versions(
    value: object,
) -> tuple[tuple[str, str, str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("signal_config_versions must be a tuple or list")
    normalized = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    for item in normalized:
        if type(item) not in (tuple, list) or len(item) != 4:
            raise ValueError(
                "signal_config_versions entries must be match/club/player/version items",
            )
        match_ref, club, player, config_version = item
        _require_canonical_string("signal_config_versions match_ref", match_ref)
        _require_canonical_string("signal_config_versions club", club)
        _require_canonical_string("signal_config_versions player", player)
        _require_canonical_string(
            "signal_config_versions config_version",
            config_version,
        )
        _reject_sensitive_text("signal_config_versions match_ref", match_ref)
        _reject_sensitive_text("signal_config_versions club", club)
        _reject_sensitive_text("signal_config_versions player", player)
        _reject_sensitive_text(
            "signal_config_versions config_version",
            config_version,
        )
        identifier = (match_ref, club, player)
        if identifier in seen:
            raise ValueError("signal_config_versions match/club/player values must be unique")
        seen.add(identifier)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount items",
            )
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda item: DIGEST_REASON_CODES.index(item.reason_code),
        ),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    codes = tuple(item.reason_code for item in normalized)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _validate_row(row: MarketResearchSoccerTrainingGroundAbsenceDigestRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.digest_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.digest_status == PASS_STATUS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use the clear reason")
    if CLEAR_REASON in row.reason_codes and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason must stand alone")


def _validate_report(report: MarketResearchSoccerTrainingGroundAbsenceDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.signal_count != _whole(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_signal_count != _count_rows(report.rows, PASS_STATUS):
        raise ValueError("pass_signal_count must match rows")
    if report.watch_signal_count != _count_rows(report.rows, WATCH_STATUS):
        raise ValueError("watch_signal_count must match rows")
    if report.blocked_signal_count != _count_rows(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_signal_count must match rows")
    if (
        report.signal_count
        != report.pass_signal_count
        + report.watch_signal_count
        + report.blocked_signal_count
    ):
        raise ValueError("signal counts must reconcile")
    expected_reason_counts = (
        (SOURCE_DISAGREEMENT_REASON, report.source_disagreement_signal_count),
        (RISK_BLOCKED_REASON, report.blocked_risk_signal_count),
        (ABSENCE_BLOCKED_REASON, report.blocked_absence_signal_count),
        (MATCH_PROXIMITY_BLOCKED_REASON, report.close_match_signal_count),
        (RISK_WATCH_REASON, report.watch_risk_signal_count),
        (ABSENCE_WATCH_REASON, report.watch_absence_signal_count),
        (ROLE_IMPORTANCE_REASON, report.high_role_importance_signal_count),
        (LINEUP_DEPENDENCY_REASON, report.high_lineup_dependency_signal_count),
        (SOURCE_STALE_REASON, report.stale_source_signal_count),
        (UPSTREAM_REASON, report.upstream_reason_signal_count),
    )
    for reason_code, field_value in expected_reason_counts:
        if field_value != _count_reason(report.rows, reason_code):
            raise ValueError("reason count fields must match rows")
    if report.max_risk_score != _max_or_zero(row.risk_score for row in report.rows):
        raise ValueError("max_risk_score must match rows")
    if report.average_risk_score != _average(row.risk_score for row in report.rows):
        raise ValueError("average_risk_score must match rows")
    row_reason_codes = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    if report.reason_code_counts != _reason_code_counts(row_reason_codes):
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not report.rows else PASSED_REASON,)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = (
        BLOCKED_STATUS
        if any(row.digest_status == BLOCKED_STATUS for row in report.rows)
        else WATCH_STATUS
        if any(row.digest_status == WATCH_STATUS for row in report.rows)
        else PASS_STATUS
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _to_plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(_quantize(value))
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value):
        return {field.name: _to_plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    return value


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{name} contains invalid reason code for this field")
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError(f"{name} must not contain duplicates")
    sorted_codes = _sort_reason_codes(reason_codes, allowed)
    if reason_codes != sorted_codes:
        raise ValueError(f"{name} must be sorted by reason code rank")
    return reason_codes


def _normalize_upstream_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_canonical_string(name, reason_code)
        _reject_sensitive_text(name, reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError(f"{name} must not contain duplicates")
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{name} must be sorted")
    return reason_codes


def _sort_reason_codes(
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda item: allowed.index(item)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in reason_codes for reason_code in BLOCKED_ROW_REASONS):
        return BLOCKED_STATUS
    if reason_codes == (CLEAR_REASON,):
        return PASS_STATUS
    return WATCH_STATUS


def _row_sort_rank(
    row: MarketResearchSoccerTrainingGroundAbsenceDigestRow,
) -> tuple[object, ...]:
    status_rank = {
        BLOCKED_STATUS: 0,
        WATCH_STATUS: 1,
        PASS_STATUS: 2,
    }[row.digest_status]
    return (
        status_rank,
        -row.risk_score,
        row.match_proximity_hours,
        row.market_slug,
        row.club,
        row.player,
        row.opponent,
        row.condition_id,
    )


def _count_rows(
    rows: tuple[MarketResearchSoccerTrainingGroundAbsenceDigestRow, ...],
    status: str,
) -> Decimal:
    return _whole(sum(1 for row in rows if row.digest_status == status))


def _count_reason(
    rows: tuple[MarketResearchSoccerTrainingGroundAbsenceDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _whole(sum(1 for row in rows if reason_code in row.reason_codes))


def _require_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{name} must be a known reason code")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _whole(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _max_or_zero(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO.quantize(QUANTUM)
    return _quantize(max(items))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO.quantize(QUANTUM)
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _duration_hours(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        (delta.days * SECONDS_PER_DAY + delta.seconds)
        * MICROSECONDS_PER_WHOLE_SECOND
        + delta.microseconds
    )
    return _quantize(
        Decimal(total_microseconds) / MICROSECONDS_PER_SECOND / SECONDS_PER_HOUR,
    )


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    ratio = numerator / denominator
    if ratio > ONE:
        return ONE
    return _quantize(ratio)


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _reject_sensitive_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(word in lowered for word in _BLOCKED_WORDS):
        raise ValueError(f"{name} contains unsafe source detail")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")

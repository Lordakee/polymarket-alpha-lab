"""Pure Phase 1 reducer for soccer referee assignment bias signals."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_SOCCER_REFEREE_ASSIGNMENT_BIAS_DIGEST_CONFIG_VERSION = (
    "market-research-soccer-referee-assignment-bias-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

HOME_BIAS_WEIGHT = Decimal("0.500000")
PENALTY_BIAS_WEIGHT = Decimal("0.200000")
CARD_BIAS_WEIGHT = Decimal("0.200000")
VAR_BIAS_WEIGHT = Decimal("0.100000")

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
ROW_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
DIGEST_STATUSES = ROW_STATUSES
BIAS_DIRECTIONS = ("home_favoring", "away_favoring", "inline")

STALE_OBSERVATION_REASON = "soccer_referee_assignment_bias_stale_observation"
HOME_BIAS_BLOCKED_REASON = "soccer_referee_assignment_bias_home_blocked"
AWAY_BIAS_BLOCKED_REASON = "soccer_referee_assignment_bias_away_blocked"
HOME_BIAS_WATCH_REASON = "soccer_referee_assignment_bias_home_watch"
AWAY_BIAS_WATCH_REASON = "soccer_referee_assignment_bias_away_watch"
THIN_SAMPLE_REASON = "soccer_referee_assignment_bias_thin_sample"
LOW_CONFIDENCE_REASON = "soccer_referee_assignment_bias_low_confidence"
PASS_REASON = "soccer_referee_assignment_bias_pass"
PASSED_REASON = "soccer_referee_assignment_bias_passed"
EMPTY_REASON = "soccer_referee_assignment_bias_empty"

ROW_REASON_CODES = (
    STALE_OBSERVATION_REASON,
    HOME_BIAS_BLOCKED_REASON,
    AWAY_BIAS_BLOCKED_REASON,
    HOME_BIAS_WATCH_REASON,
    AWAY_BIAS_WATCH_REASON,
    THIN_SAMPLE_REASON,
    LOW_CONFIDENCE_REASON,
    PASS_REASON,
)
DIGEST_REASON_CODES = (
    STALE_OBSERVATION_REASON,
    HOME_BIAS_BLOCKED_REASON,
    AWAY_BIAS_BLOCKED_REASON,
    HOME_BIAS_WATCH_REASON,
    AWAY_BIAS_WATCH_REASON,
    THIN_SAMPLE_REASON,
    LOW_CONFIDENCE_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
KNOWN_REASON_CODES = ROW_REASON_CODES + (PASSED_REASON, EMPTY_REASON)

NEXT_STEP_BY_STATUS = {
    BLOCKED_STATUS: "block_report_only_soccer_referee_assignment_bias_review",
    WATCH_STATUS: "watch_report_only_soccer_referee_assignment_bias_review",
    PASS_STATUS: "continue_report_only_soccer_referee_assignment_bias_monitoring",
}
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

_BLOCKED_TEXT = (
    "wal" "let",
    "bro" "ker",
    "ord" "er",
    "au" "th",
    "se" "cret",
    "pri" "vate",
    "can" "cel",
    "re" "place",
    "ex" "change",
    "tra" "de",
    "tok" "en",
    "k" "ey",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_SOCCER_REFEREE_ASSIGNMENT_BIAS_DIGEST_CONFIG_VERSION",
    "MarketResearchSoccerRefereeAssignmentBiasDigestConfig",
    "MarketResearchSoccerRefereeAssignmentBiasDigestSignal",
    "MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount",
    "MarketResearchSoccerRefereeAssignmentBiasDigestRow",
    "MarketResearchSoccerRefereeAssignmentBiasDigestReport",
    "build_market_research_soccer_referee_assignment_bias_digest",
    "market_research_soccer_referee_assignment_bias_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchSoccerRefereeAssignmentBiasDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_REFEREE_ASSIGNMENT_BIAS_DIGEST_CONFIG_VERSION
    )
    blocked_abs_bias_score_threshold: Decimal = Decimal("0.060000")
    watch_abs_bias_score_threshold: Decimal = Decimal("0.030000")
    minimum_historical_match_sample_threshold: Decimal = Decimal("8.000000")
    low_confidence_threshold: Decimal = Decimal("0.600000")
    stale_observation_seconds_threshold: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerRefereeAssignmentBiasDigestConfig:
            raise TypeError(
                "MarketResearchSoccerRefereeAssignmentBiasDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerRefereeAssignmentBiasDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchSoccerRefereeAssignmentBiasDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "blocked_abs_bias_score_threshold",
            "watch_abs_bias_score_threshold",
            "minimum_historical_match_sample_threshold",
            "low_confidence_threshold",
            "stale_observation_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_maximum_one_decimal(
            "blocked_abs_bias_score_threshold",
            self.blocked_abs_bias_score_threshold,
        )
        _require_maximum_one_decimal(
            "watch_abs_bias_score_threshold",
            self.watch_abs_bias_score_threshold,
        )
        _require_maximum_one_decimal(
            "low_confidence_threshold",
            self.low_confidence_threshold,
        )
        if self.blocked_abs_bias_score_threshold < self.watch_abs_bias_score_threshold:
            raise ValueError(
                "blocked_abs_bias_score_threshold must be at least watch threshold",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchSoccerRefereeAssignmentBiasDigestSignal:
    fixture_id: str
    referee_id: str
    competition_id: str
    home_team_id: str
    away_team_id: str
    source_ref: str
    observed_at: datetime
    home_favorable_call_delta: Decimal
    away_favorable_call_delta: Decimal
    penalty_bias_delta: Decimal
    card_bias_delta: Decimal
    var_review_bias_delta: Decimal
    historical_match_sample: Decimal
    assignment_confidence: Decimal
    signal_config_version: str = (
        DEFAULT_MARKET_RESEARCH_SOCCER_REFEREE_ASSIGNMENT_BIAS_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerRefereeAssignmentBiasDigestSignal:
            raise TypeError(
                "MarketResearchSoccerRefereeAssignmentBiasDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerRefereeAssignmentBiasDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchSoccerRefereeAssignmentBiasDigestSignal",
            )
        for field_name in (
            "fixture_id",
            "referee_id",
            "competition_id",
            "home_team_id",
            "away_team_id",
            "source_ref",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "home_favorable_call_delta",
            "away_favorable_call_delta",
            "penalty_bias_delta",
            "card_bias_delta",
            "var_review_bias_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "historical_match_sample",
            _normalize_nonnegative_decimal(
                "historical_match_sample",
                self.historical_match_sample,
            ),
        )
        object.__setattr__(
            self,
            "assignment_confidence",
            _normalize_ratio_decimal("assignment_confidence", self.assignment_confidence),
        )
        _require_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount:
    reason_code: str
    fixture_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "fixture_count",
            _normalize_nonnegative_decimal("fixture_count", self.fixture_count),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchSoccerRefereeAssignmentBiasDigestRow:
    fixture_id: str
    referee_id: str
    competition_id: str
    home_team_id: str
    away_team_id: str
    signal_count: Decimal
    observed_at_latest: datetime
    observation_age_seconds: Decimal
    historical_match_sample_max: Decimal
    assignment_confidence_min: Decimal
    assignment_confidence_max: Decimal
    net_home_bias_score: Decimal
    abs_assignment_bias_score: Decimal
    screening_priority_score: Decimal
    bias_direction: str
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerRefereeAssignmentBiasDigestRow:
            raise TypeError(
                "MarketResearchSoccerRefereeAssignmentBiasDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerRefereeAssignmentBiasDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchSoccerRefereeAssignmentBiasDigestRow",
            )
        for field_name in (
            "fixture_id",
            "referee_id",
            "competition_id",
            "home_team_id",
            "away_team_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_sensitive_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "signal_count",
            _normalize_nonnegative_decimal("signal_count", self.signal_count),
        )
        object.__setattr__(
            self,
            "observed_at_latest",
            _as_utc("observed_at_latest", self.observed_at_latest),
        )
        for field_name in (
            "observation_age_seconds",
            "historical_match_sample_max",
            "assignment_confidence_min",
            "assignment_confidence_max",
            "abs_assignment_bias_score",
            "screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "assignment_confidence_min",
            "assignment_confidence_max",
            "abs_assignment_bias_score",
            "screening_priority_score",
        ):
            _require_maximum_one_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "net_home_bias_score",
            _normalize_signed_decimal("net_home_bias_score", self.net_home_bias_score),
        )
        _require_member("bias_direction", self.bias_direction, BIAS_DIRECTIONS)
        _require_member("row_status", self.row_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchSoccerRefereeAssignmentBiasDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    fixture_count: Decimal
    signal_count: Decimal
    blocked_fixture_count: Decimal
    watch_fixture_count: Decimal
    pass_fixture_count: Decimal
    stale_observation_fixture_count: Decimal
    home_bias_fixture_count: Decimal
    away_bias_fixture_count: Decimal
    thin_sample_fixture_count: Decimal
    low_confidence_fixture_count: Decimal
    blocked_abs_bias_score_threshold: Decimal
    watch_abs_bias_score_threshold: Decimal
    minimum_historical_match_sample_threshold: Decimal
    low_confidence_threshold: Decimal
    stale_observation_seconds_threshold: Decimal
    max_observation_age_seconds: Decimal | None
    max_abs_assignment_bias_score: Decimal | None
    max_screening_priority_score: Decimal | None
    rows: tuple[MarketResearchSoccerRefereeAssignmentBiasDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchSoccerRefereeAssignmentBiasDigestReport:
            raise TypeError(
                "MarketResearchSoccerRefereeAssignmentBiasDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchSoccerRefereeAssignmentBiasDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchSoccerRefereeAssignmentBiasDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "fixture_count",
            "signal_count",
            "blocked_fixture_count",
            "watch_fixture_count",
            "pass_fixture_count",
            "stale_observation_fixture_count",
            "home_bias_fixture_count",
            "away_bias_fixture_count",
            "thin_sample_fixture_count",
            "low_confidence_fixture_count",
            "blocked_abs_bias_score_threshold",
            "watch_abs_bias_score_threshold",
            "minimum_historical_match_sample_threshold",
            "low_confidence_threshold",
            "stale_observation_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "blocked_abs_bias_score_threshold",
            "watch_abs_bias_score_threshold",
            "low_confidence_threshold",
        ):
            _require_maximum_one_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "max_observation_age_seconds",
            "max_abs_assignment_bias_score",
            "max_screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_abs_assignment_bias_score",
            "max_screening_priority_score",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _require_maximum_one_decimal(field_name, value)
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                DIGEST_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_soccer_referee_assignment_bias_digest(
    signals: Iterable[MarketResearchSoccerRefereeAssignmentBiasDigestSignal],
    *,
    config: MarketResearchSoccerRefereeAssignmentBiasDigestConfig,
    generated_at: datetime,
) -> MarketResearchSoccerRefereeAssignmentBiasDigestReport:
    if type(config) is not MarketResearchSoccerRefereeAssignmentBiasDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchSoccerRefereeAssignmentBiasDigestConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be exactly datetime")
    generated_at_utc = _as_utc("generated_at", generated_at)
    signal_items = _normalize_signals(signals)
    rows = _build_rows(signal_items, config=config, generated_at=generated_at_utc)
    row_reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    )
    digest_status = _digest_status(rows)
    reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not rows else PASSED_REASON,)
    )

    return MarketResearchSoccerRefereeAssignmentBiasDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        fixture_count=_decimal_count(len(rows)),
        signal_count=_decimal_count(len(signal_items)),
        blocked_fixture_count=_decimal_count(
            sum(Decimal("1") for row in rows if row.row_status == BLOCKED_STATUS),
        ),
        watch_fixture_count=_decimal_count(
            sum(Decimal("1") for row in rows if row.row_status == WATCH_STATUS),
        ),
        pass_fixture_count=_decimal_count(
            sum(Decimal("1") for row in rows if row.row_status == PASS_STATUS),
        ),
        stale_observation_fixture_count=_reason_count(rows, STALE_OBSERVATION_REASON),
        home_bias_fixture_count=_decimal_count(
            sum(
                Decimal("1")
                for row in rows
                if (
                    HOME_BIAS_BLOCKED_REASON in row.reason_codes
                    or HOME_BIAS_WATCH_REASON in row.reason_codes
                )
            ),
        ),
        away_bias_fixture_count=_decimal_count(
            sum(
                Decimal("1")
                for row in rows
                if (
                    AWAY_BIAS_BLOCKED_REASON in row.reason_codes
                    or AWAY_BIAS_WATCH_REASON in row.reason_codes
                )
            ),
        ),
        thin_sample_fixture_count=_reason_count(rows, THIN_SAMPLE_REASON),
        low_confidence_fixture_count=_reason_count(rows, LOW_CONFIDENCE_REASON),
        blocked_abs_bias_score_threshold=config.blocked_abs_bias_score_threshold,
        watch_abs_bias_score_threshold=config.watch_abs_bias_score_threshold,
        minimum_historical_match_sample_threshold=(
            config.minimum_historical_match_sample_threshold
        ),
        low_confidence_threshold=config.low_confidence_threshold,
        stale_observation_seconds_threshold=config.stale_observation_seconds_threshold,
        max_observation_age_seconds=_max_or_none(row.observation_age_seconds for row in rows),
        max_abs_assignment_bias_score=_max_or_none(
            row.abs_assignment_bias_score for row in rows
        ),
        max_screening_priority_score=_max_or_none(
            row.screening_priority_score for row in rows
        ),
        rows=rows,
        signal_config_versions=tuple(
            sorted(
                {
                    (signal.source_ref, signal.signal_config_version)
                    for signal in signal_items
                },
            ),
        ),
        reason_code_counts=_reason_code_counts(row_reason_codes),
        reason_codes=reason_codes,
    )


def market_research_soccer_referee_assignment_bias_digest_payload(
    report: MarketResearchSoccerRefereeAssignmentBiasDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchSoccerRefereeAssignmentBiasDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchSoccerRefereeAssignmentBiasDigestReport",
        )
    _require_flags("report", report)
    return _to_plain(report)


def _build_rows(
    signals: tuple[MarketResearchSoccerRefereeAssignmentBiasDigestSignal, ...],
    *,
    config: MarketResearchSoccerRefereeAssignmentBiasDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchSoccerRefereeAssignmentBiasDigestRow, ...]:
    grouped: dict[
        tuple[str, str, str, str, str],
        list[MarketResearchSoccerRefereeAssignmentBiasDigestSignal],
    ] = {}
    for signal in signals:
        group_id = (
            signal.fixture_id,
            signal.referee_id,
            signal.competition_id,
            signal.home_team_id,
            signal.away_team_id,
        )
        grouped.setdefault(group_id, []).append(signal)

    rows: list[MarketResearchSoccerRefereeAssignmentBiasDigestRow] = []
    for group_id, fixture_signals in grouped.items():
        fixture_id, referee_id, competition_id, home_team_id, away_team_id = group_id
        sorted_signals = tuple(
            sorted(fixture_signals, key=lambda item: (item.observed_at, item.source_ref)),
        )
        observed_at_latest = max(item.observed_at for item in sorted_signals)
        observation_age_seconds = _duration_seconds(generated_at, observed_at_latest)
        if observation_age_seconds < ZERO:
            raise ValueError("observed_at values must be at or before generated_at")

        confidence_values = tuple(item.assignment_confidence for item in sorted_signals)
        bias_candidates = tuple(
            (_net_home_bias_score(signal), signal) for signal in sorted_signals
        )
        net_home_bias_score, _source_signal = max(
            bias_candidates,
            key=lambda item: (abs(item[0]), item[1].observed_at, item[1].source_ref),
        )
        abs_assignment_bias_score = abs(net_home_bias_score).quantize(QUANTUM)
        historical_match_sample_max = max(
            item.historical_match_sample for item in sorted_signals
        )
        assignment_confidence_min = min(confidence_values)
        assignment_confidence_max = max(confidence_values)
        reason_codes = _row_reason_codes(
            net_home_bias_score=net_home_bias_score,
            observation_age_seconds=observation_age_seconds,
            historical_match_sample_max=historical_match_sample_max,
            assignment_confidence_min=assignment_confidence_min,
            config=config,
        )
        row_status = _row_status_from_reason_codes(reason_codes)
        if not reason_codes:
            reason_codes = (PASS_REASON,)
        else:
            reason_codes = _sort_reason_codes(reason_codes, ROW_REASON_CODES)

        rows.append(
            MarketResearchSoccerRefereeAssignmentBiasDigestRow(
                fixture_id=fixture_id,
                referee_id=referee_id,
                competition_id=competition_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                signal_count=_decimal_count(len(sorted_signals)),
                observed_at_latest=observed_at_latest,
                observation_age_seconds=observation_age_seconds,
                historical_match_sample_max=historical_match_sample_max,
                assignment_confidence_min=assignment_confidence_min,
                assignment_confidence_max=assignment_confidence_max,
                net_home_bias_score=net_home_bias_score,
                abs_assignment_bias_score=abs_assignment_bias_score,
                screening_priority_score=_screening_priority_score(
                    abs_assignment_bias_score,
                    config.blocked_abs_bias_score_threshold,
                ),
                bias_direction=_bias_direction(net_home_bias_score),
                row_status=row_status,
                reason_codes=reason_codes,
            ),
        )

    return tuple(sorted(rows, key=_row_sort_value))


def _row_reason_codes(
    *,
    net_home_bias_score: Decimal,
    observation_age_seconds: Decimal,
    historical_match_sample_max: Decimal,
    assignment_confidence_min: Decimal,
    config: MarketResearchSoccerRefereeAssignmentBiasDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    abs_bias_score = abs(net_home_bias_score).quantize(QUANTUM)
    if observation_age_seconds >= config.stale_observation_seconds_threshold:
        reason_codes.append(STALE_OBSERVATION_REASON)
    if abs_bias_score >= config.blocked_abs_bias_score_threshold:
        if net_home_bias_score >= ZERO:
            reason_codes.append(HOME_BIAS_BLOCKED_REASON)
        else:
            reason_codes.append(AWAY_BIAS_BLOCKED_REASON)
    elif abs_bias_score >= config.watch_abs_bias_score_threshold:
        if net_home_bias_score >= ZERO:
            reason_codes.append(HOME_BIAS_WATCH_REASON)
        else:
            reason_codes.append(AWAY_BIAS_WATCH_REASON)
    if historical_match_sample_max < config.minimum_historical_match_sample_threshold:
        reason_codes.append(THIN_SAMPLE_REASON)
    if assignment_confidence_min < config.low_confidence_threshold:
        reason_codes.append(LOW_CONFIDENCE_REASON)
    return tuple(reason_codes)


def _net_home_bias_score(
    signal: MarketResearchSoccerRefereeAssignmentBiasDigestSignal,
) -> Decimal:
    with localcontext():
        return (
            (
                signal.home_favorable_call_delta
                - signal.away_favorable_call_delta
            )
            * HOME_BIAS_WEIGHT
            + signal.penalty_bias_delta * PENALTY_BIAS_WEIGHT
            + signal.card_bias_delta * CARD_BIAS_WEIGHT
            + signal.var_review_bias_delta * VAR_BIAS_WEIGHT
        ).quantize(QUANTUM)


def _screening_priority_score(
    abs_assignment_bias_score: Decimal,
    blocked_abs_bias_score_threshold: Decimal,
) -> Decimal:
    if blocked_abs_bias_score_threshold <= ZERO:
        return ONE
    with localcontext():
        score = abs_assignment_bias_score / blocked_abs_bias_score_threshold
    if score > ONE:
        return ONE
    return score.quantize(QUANTUM)


def _bias_direction(net_home_bias_score: Decimal) -> str:
    if net_home_bias_score > ZERO:
        return "home_favoring"
    if net_home_bias_score < ZERO:
        return "away_favoring"
    return "inline"


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in (HOME_BIAS_BLOCKED_REASON, AWAY_BIAS_BLOCKED_REASON)
        for reason_code in reason_codes
    ):
        return BLOCKED_STATUS
    if reason_codes:
        return WATCH_STATUS
    return PASS_STATUS


def _digest_status(
    rows: tuple[MarketResearchSoccerRefereeAssignmentBiasDigestRow, ...],
) -> str:
    if any(row.row_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.row_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount(
            reason_code=reason_code,
            fixture_count=_decimal_count(
                sum(Decimal("1") for item in reason_codes if item == reason_code),
            ),
        )
        for reason_code in _sort_reason_codes(set(reason_codes), DIGEST_REASON_CODES)
    )


def _normalize_signals(
    signals: Iterable[MarketResearchSoccerRefereeAssignmentBiasDigestSignal],
) -> tuple[MarketResearchSoccerRefereeAssignmentBiasDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of signal records")
    try:
        signal_items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of signal records") from exc
    seen: set[tuple[str, str, str]] = set()
    for signal in signal_items:
        if type(signal) is not MarketResearchSoccerRefereeAssignmentBiasDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchSoccerRefereeAssignmentBiasDigestSignal records",
            )
        _require_flags("signal", signal)
        unique_ref = (signal.fixture_id, signal.referee_id, signal.source_ref)
        if unique_ref in seen:
            raise ValueError("signals must not contain duplicate fixture/referee/source triples")
        seen.add(unique_ref)
    return signal_items


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchSoccerRefereeAssignmentBiasDigestRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchSoccerRefereeAssignmentBiasDigestRow:
            raise ValueError(
                "rows must contain MarketResearchSoccerRefereeAssignmentBiasDigestRow records",
            )
        _require_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_value)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("signal_config_versions must be a tuple or list")
    normalized = tuple(value)
    seen_refs: set[str] = set()
    for item in normalized:
        try:
            source_ref, config_version = item
        except (TypeError, ValueError) as exc:
            raise ValueError("signal_config_versions entries must be pairs") from exc
        _require_canonical_string("signal_config_versions source_ref", source_ref)
        _require_canonical_string("signal_config_versions config_version", config_version)
        _reject_sensitive_text("signal_config_versions source_ref", source_ref)
        _reject_sensitive_text("signal_config_versions config_version", config_version)
        if source_ref in seen_refs:
            raise ValueError("signal_config_versions source_ref values must be unique")
        seen_refs.add(source_ref)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchSoccerRefereeAssignmentBiasDigestReasonCodeCount records",
            )
    if normalized != tuple(
        sorted(normalized, key=lambda item: DIGEST_REASON_CODES.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    return normalized


def _validate_row(row: MarketResearchSoccerRefereeAssignmentBiasDigestRow) -> None:
    expected_status = _row_status_from_reason_codes(
        tuple(reason_code for reason_code in row.reason_codes if reason_code != PASS_REASON),
    )
    if row.row_status != expected_status:
        raise ValueError("row status must match reason codes")
    if row.row_status == PASS_STATUS and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use the pass reason")
    if row.row_status != PASS_STATUS and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not use the pass reason")
    if row.abs_assignment_bias_score != abs(row.net_home_bias_score).quantize(QUANTUM):
        raise ValueError("abs_assignment_bias_score must match net_home_bias_score")
    if row.bias_direction != _bias_direction(row.net_home_bias_score):
        raise ValueError("bias_direction must match net_home_bias_score")
    if row.assignment_confidence_max < row.assignment_confidence_min:
        raise ValueError("assignment_confidence_max must be greater than or equal to minimum")


def _validate_report(
    report: MarketResearchSoccerRefereeAssignmentBiasDigestReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.fixture_count != _decimal_count(len(report.rows)):
        raise ValueError("fixture_count must match rows")
    if report.signal_count != _quantize(sum((row.signal_count for row in report.rows), ZERO)):
        raise ValueError("signal_count must match rows")
    if report.blocked_fixture_count != _decimal_count(
        sum(Decimal("1") for row in report.rows if row.row_status == BLOCKED_STATUS),
    ):
        raise ValueError("blocked_fixture_count must match rows")
    if report.watch_fixture_count != _decimal_count(
        sum(Decimal("1") for row in report.rows if row.row_status == WATCH_STATUS),
    ):
        raise ValueError("watch_fixture_count must match rows")
    if report.pass_fixture_count != _decimal_count(
        sum(Decimal("1") for row in report.rows if row.row_status == PASS_STATUS),
    ):
        raise ValueError("pass_fixture_count must match rows")
    if (
        report.fixture_count
        != report.blocked_fixture_count
        + report.watch_fixture_count
        + report.pass_fixture_count
    ):
        raise ValueError("fixture status counts must reconcile")
    if report.stale_observation_fixture_count != _reason_count(
        report.rows,
        STALE_OBSERVATION_REASON,
    ):
        raise ValueError("stale_observation_fixture_count must match rows")
    if report.home_bias_fixture_count != _decimal_count(
        sum(
            Decimal("1")
            for row in report.rows
            if (
                HOME_BIAS_BLOCKED_REASON in row.reason_codes
                or HOME_BIAS_WATCH_REASON in row.reason_codes
            )
        ),
    ):
        raise ValueError("home_bias_fixture_count must match rows")
    if report.away_bias_fixture_count != _decimal_count(
        sum(
            Decimal("1")
            for row in report.rows
            if (
                AWAY_BIAS_BLOCKED_REASON in row.reason_codes
                or AWAY_BIAS_WATCH_REASON in row.reason_codes
            )
        ),
    ):
        raise ValueError("away_bias_fixture_count must match rows")
    if report.thin_sample_fixture_count != _reason_count(report.rows, THIN_SAMPLE_REASON):
        raise ValueError("thin_sample_fixture_count must match rows")
    if report.low_confidence_fixture_count != _reason_count(report.rows, LOW_CONFIDENCE_REASON):
        raise ValueError("low_confidence_fixture_count must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.digest_status == PASS_STATUS and any(
        reason_code not in (PASSED_REASON, EMPTY_REASON)
        for reason_code in report.reason_codes
    ):
        raise ValueError("pass reports must not include watch reasons")
    if report.digest_status != PASS_STATUS and not report.reason_code_counts:
        raise ValueError("non-pass reports require reason counts")
    row_reason_codes = tuple(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    )
    expected_reason_codes = (
        _sort_reason_codes(set(row_reason_codes), DIGEST_REASON_CODES)
        if row_reason_codes
        else (EMPTY_REASON if not report.rows else PASSED_REASON,)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(row_reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.max_observation_age_seconds != _max_or_none(
        row.observation_age_seconds for row in report.rows
    ):
        raise ValueError("max_observation_age_seconds must match rows")
    if report.max_abs_assignment_bias_score != _max_or_none(
        row.abs_assignment_bias_score for row in report.rows
    ):
        raise ValueError("max_abs_assignment_bias_score must match rows")
    if report.max_screening_priority_score != _max_or_none(
        row.screening_priority_score for row in report.rows
    ):
        raise ValueError("max_screening_priority_score must match rows")


def _to_plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _to_plain(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return format(value.quantize(QUANTUM), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    if type(value) is bool or value is None or type(value) is str:
        return value
    raise ValueError("value is not a supported report field")


def _row_sort_value(
    row: MarketResearchSoccerRefereeAssignmentBiasDigestRow,
) -> tuple[object, ...]:
    return (
        STATUS_RANK[row.row_status],
        -row.screening_priority_score,
        -row.abs_assignment_bias_score,
        -row.observation_age_seconds,
        row.fixture_id,
        row.referee_id,
    )


def _sort_reason_codes(
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda item: allowed.index(item)))


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


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _quantize(_require_decimal(name, value))
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(name, value)


def _normalize_signed_decimal(name: str, value: object) -> Decimal:
    return _quantize(_require_decimal(name, value))


def _normalize_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    _require_maximum_one_decimal(name, normalized)
    return normalized


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be finite") from exc


def _require_maximum_one_decimal(name: str, value: Decimal) -> None:
    if value > ONE:
        raise ValueError(f"{name} must be at most one")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _decimal_count(value: object) -> Decimal:
    return Decimal(str(value)).quantize(QUANTUM)


def _duration_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext():
        seconds = Decimal(str(delta.days)) * SECONDS_PER_DAY
        seconds += Decimal(str(delta.seconds))
        seconds += Decimal(str(delta.microseconds)) / MICROSECONDS_PER_SECOND
    return seconds.quantize(QUANTUM)


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return max(normalized).quantize(QUANTUM)


def _reason_count(
    rows: tuple[MarketResearchSoccerRefereeAssignmentBiasDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(
        sum(Decimal("1") for row in rows if reason_code in row.reason_codes),
    )


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be non-empty canonical text")
    if value.lower() != value:
        raise ValueError(f"{name} must be lowercase canonical text")
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789_.-"
    if not all(character in allowed_chars for character in value):
        raise ValueError(f"{name} must be lowercase canonical text")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must contain strings")
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{name} contains unknown reason code")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} must be a known value")


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_sensitive_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _BLOCKED_TEXT):
        raise ValueError(f"{name} contains unsafe source detail")

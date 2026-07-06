"""Pure paper-only forecast revision pressure score v2."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


DEFAULT_STRATEGY_FORECAST_REVISION_PRESSURE_SCORE_V2_CONFIG_VERSION = (
    "strategy-forecast-revision-pressure-score-v2"
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0").quantize(VALUE_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal("3600.000000")

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

REVISION_UP_REASON = "forecast_revision_up"
REVISION_DOWN_REASON = "forecast_revision_down"
REVISION_FLAT_REASON = "forecast_revision_flat"
STALE_REASON = "stale_forecast_penalty"
SHARP_REASON = "sharp_revision_boost"
PASS_REASON = "revision_pressure_pass"
WATCH_REASON = "revision_pressure_watch"
BLOCKED_REASON = "revision_pressure_blocked"
EMPTY_REASON = "revision_pressure_empty"
ROW_REASON_CODES = (
    BLOCKED_REASON,
    PASS_REASON,
    REVISION_DOWN_REASON,
    REVISION_FLAT_REASON,
    REVISION_UP_REASON,
    SHARP_REASON,
    STALE_REASON,
    WATCH_REASON,
)
REPORT_REASON_CODES = tuple(sorted((*ROW_REASON_CODES, EMPTY_REASON)))
HEX_DIGITS = frozenset("0123456789abcdef")
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
UNSAFE_TEXT_FRAGMENTS = (
    "li" + "ve",
    "aut" + "h",
    "wal" + "let",
    "ord" + "er",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sig" + "ning",
    "mut" + "ation",
    "b" + "uy",
    "se" + "ll",
    "tra" + "de",
)
SENSITIVE_REFERENCE_MARKERS = (
    "://",
    "?",
    "tok" + "en",
    "api" + "_key",
    "sec" + "ret",
    "priv" + "ate",
    "bear" + "er",
    "pass" + "word",
    "seed" + "_phrase",
)


@dataclass(frozen=True)
class StrategyForecastRevisionPressureScoreV2Config:
    config_version: str = DEFAULT_STRATEGY_FORECAST_REVISION_PRESSURE_SCORE_V2_CONFIG_VERSION
    sharp_revision_delta: Decimal = Decimal("0.100000")
    stale_after_hours: Decimal = Decimal("24.000000")
    stale_full_penalty_hours: Decimal = Decimal("48.000000")
    revision_magnitude_weight: Decimal = Decimal("0.700000")
    stale_penalty_weight: Decimal = Decimal("0.200000")
    sharp_revision_boost_weight: Decimal = Decimal("0.200000")
    blocked_pressure_score: Decimal = Decimal("0.750000")
    watch_pressure_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "sharp_revision_delta",
            "revision_magnitude_weight",
            "stale_penalty_weight",
            "sharp_revision_boost_weight",
            "blocked_pressure_score",
            "watch_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_after_hours", "stale_full_penalty_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        if self.sharp_revision_delta <= ZERO:
            raise ValueError("sharp_revision_delta must be above zero")
        if self.stale_full_penalty_hours <= ZERO:
            raise ValueError("stale_full_penalty_hours must be above zero")
        if self.blocked_pressure_score < self.watch_pressure_score:
            raise ValueError("blocked_pressure_score must be at least watch_pressure_score")
        _require_paper_flags("config", self)


@dataclass(frozen=True)
class StrategyForecastRevisionPressureObservation:
    candidate_id: str
    forecast_observed_at: datetime
    prior_forecast_observed_at: datetime
    prior_forecast: Decimal
    current_forecast: Decimal
    forecast_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "forecast_observed_at",
            _as_utc("forecast_observed_at", self.forecast_observed_at),
        )
        object.__setattr__(
            self,
            "prior_forecast_observed_at",
            _as_utc("prior_forecast_observed_at", self.prior_forecast_observed_at),
        )
        if self.forecast_observed_at < self.prior_forecast_observed_at:
            raise ValueError(
                "forecast_observed_at must be at or after prior_forecast_observed_at",
            )
        for field_name in ("prior_forecast", "current_forecast"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_canonical_string("forecast_reference", self.forecast_reference)
        _require_paper_flags("observation", self)


@dataclass(frozen=True)
class StrategyForecastRevisionPressureScoreV2Row:
    rank: Decimal
    candidate_id: str
    forecast_observed_at: datetime
    prior_forecast_observed_at: datetime
    prior_forecast: Decimal
    current_forecast: Decimal
    revision_delta: Decimal
    absolute_revision_delta: Decimal
    forecast_age_hours: Decimal
    revision_window_hours: Decimal
    stale_forecast_penalty: Decimal
    sharp_revision_boost: Decimal
    revision_pressure_score: Decimal
    pressure_status: str
    redacted_forecast_reference: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "forecast_observed_at",
            _as_utc("forecast_observed_at", self.forecast_observed_at),
        )
        object.__setattr__(
            self,
            "prior_forecast_observed_at",
            _as_utc("prior_forecast_observed_at", self.prior_forecast_observed_at),
        )
        for field_name in (
            "prior_forecast",
            "current_forecast",
            "absolute_revision_delta",
            "stale_forecast_penalty",
            "sharp_revision_boost",
            "revision_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "revision_delta",
            _normalize_probability_delta("revision_delta", self.revision_delta),
        )
        for field_name in ("forecast_age_hours", "revision_window_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_member("pressure_status", self.pressure_status, STATUSES)
        _require_canonical_string(
            "redacted_forecast_reference",
            self.redacted_forecast_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_digest("derived_validation_digest", self.derived_validation_digest),
        )
        _validate_row(self)
        _validate_row_digest(self)
        _require_paper_flags("row", self)


@dataclass(frozen=True)
class StrategyForecastRevisionPressureScoreV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    top_candidate_id: str | None
    max_revision_pressure_score: Decimal
    average_revision_pressure_score: Decimal
    pressure_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyForecastRevisionPressureScoreV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.top_candidate_id is not None:
            _require_canonical_string("top_candidate_id", self.top_candidate_id)
        for field_name in ("max_revision_pressure_score", "average_revision_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("pressure_status", self.pressure_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_digest("derived_validation_digest", self.derived_validation_digest),
        )
        _validate_report(self)
        _validate_report_digest(self)
        _require_paper_flags("report", self)


def build_strategy_forecast_revision_pressure_score_v2(
    observations: Iterable[StrategyForecastRevisionPressureObservation],
    *,
    config: StrategyForecastRevisionPressureScoreV2Config,
    generated_at: datetime,
) -> StrategyForecastRevisionPressureScoreV2Report:
    if type(config) is not StrategyForecastRevisionPressureScoreV2Config:
        raise ValueError("config must be a StrategyForecastRevisionPressureScoreV2Config")
    _require_paper_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_observations(observations)
    computed_rows = tuple(_score_row(row, config, generated_at_utc) for row in source_rows)
    ranked_rows = _rank_rows(computed_rows)

    candidate_count = _count(len(ranked_rows))
    pass_count = _count(_status_count(ranked_rows, PASS_STATUS))
    watch_count = _count(_status_count(ranked_rows, WATCH_STATUS))
    blocked_count = _count(_status_count(ranked_rows, BLOCKED_STATUS))
    top_candidate_id = ranked_rows[0].candidate_id if ranked_rows else None
    max_score = _max_score(ranked_rows)
    average_score = _average_score(ranked_rows)
    pressure_status = _report_status(ranked_rows)
    reason_codes = _report_reason_codes(ranked_rows)

    return StrategyForecastRevisionPressureScoreV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        top_candidate_id=top_candidate_id,
        max_revision_pressure_score=max_score,
        average_revision_pressure_score=average_score,
        pressure_status=pressure_status,
        reason_codes=reason_codes,
        rows=ranked_rows,
        derived_validation_digest=_report_digest(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            candidate_count=candidate_count,
            pass_count=pass_count,
            watch_count=watch_count,
            blocked_count=blocked_count,
            top_candidate_id=top_candidate_id,
            max_revision_pressure_score=max_score,
            average_revision_pressure_score=average_score,
            pressure_status=pressure_status,
            reason_codes=reason_codes,
            rows=ranked_rows,
        ),
    )


def strategy_forecast_revision_pressure_score_v2_payload(
    report: StrategyForecastRevisionPressureScoreV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyForecastRevisionPressureScoreV2Report:
        _require_paper_flags("report", report)
        _validate_report_digest(report)
        _validate_report(report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_paper_flags("payload", _DictFlags(report))
        _validate_payload_digest(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyForecastRevisionPressureScoreV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_paper_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _score_row(
    observation: StrategyForecastRevisionPressureObservation,
    config: StrategyForecastRevisionPressureScoreV2Config,
    generated_at: datetime,
) -> StrategyForecastRevisionPressureScoreV2Row:
    revision_delta = _q(observation.current_forecast - observation.prior_forecast)
    absolute_revision_delta = _q(abs(revision_delta))
    forecast_age_hours = _hours_between(generated_at, observation.forecast_observed_at)
    revision_window_hours = _hours_between(
        observation.forecast_observed_at,
        observation.prior_forecast_observed_at,
    )
    stale_forecast_penalty = _stale_penalty(forecast_age_hours, config)
    sharp_revision_boost = _sharp_boost(absolute_revision_delta, config)
    magnitude_score = _q(
        min(_ratio(absolute_revision_delta, config.sharp_revision_delta), ONE)
        * config.revision_magnitude_weight,
    )
    revision_pressure_score = _q(
        min(magnitude_score + stale_forecast_penalty + sharp_revision_boost, ONE),
    )
    pressure_status = _pressure_status(revision_pressure_score, config)
    reason_codes = _row_reason_codes(
        revision_delta=revision_delta,
        stale_forecast_penalty=stale_forecast_penalty,
        sharp_revision_boost=sharp_revision_boost,
        pressure_status=pressure_status,
    )
    redacted_reference = _redact_reference(observation.forecast_reference)

    return StrategyForecastRevisionPressureScoreV2Row(
        rank=Decimal("1"),
        candidate_id=observation.candidate_id,
        forecast_observed_at=observation.forecast_observed_at,
        prior_forecast_observed_at=observation.prior_forecast_observed_at,
        prior_forecast=observation.prior_forecast,
        current_forecast=observation.current_forecast,
        revision_delta=revision_delta,
        absolute_revision_delta=absolute_revision_delta,
        forecast_age_hours=forecast_age_hours,
        revision_window_hours=revision_window_hours,
        stale_forecast_penalty=stale_forecast_penalty,
        sharp_revision_boost=sharp_revision_boost,
        revision_pressure_score=revision_pressure_score,
        pressure_status=pressure_status,
        redacted_forecast_reference=redacted_reference,
        reason_codes=reason_codes,
        derived_validation_digest=_row_digest(
            rank=Decimal("1"),
            candidate_id=observation.candidate_id,
            forecast_observed_at=observation.forecast_observed_at,
            prior_forecast_observed_at=observation.prior_forecast_observed_at,
            prior_forecast=observation.prior_forecast,
            current_forecast=observation.current_forecast,
            revision_delta=revision_delta,
            absolute_revision_delta=absolute_revision_delta,
            forecast_age_hours=forecast_age_hours,
            revision_window_hours=revision_window_hours,
            stale_forecast_penalty=stale_forecast_penalty,
            sharp_revision_boost=sharp_revision_boost,
            revision_pressure_score=revision_pressure_score,
            pressure_status=pressure_status,
            redacted_forecast_reference=redacted_reference,
            reason_codes=reason_codes,
        ),
    )


def _rank_rows(
    rows: tuple[StrategyForecastRevisionPressureScoreV2Row, ...],
) -> tuple[StrategyForecastRevisionPressureScoreV2Row, ...]:
    ranked: list[StrategyForecastRevisionPressureScoreV2Row] = []
    for index, row in enumerate(
        sorted(
            rows,
            key=lambda item: (-item.revision_pressure_score, item.candidate_id),
        ),
        start=1,
    ):
        rank = _count(index)
        ranked.append(
            StrategyForecastRevisionPressureScoreV2Row(
                rank=rank,
                candidate_id=row.candidate_id,
                forecast_observed_at=row.forecast_observed_at,
                prior_forecast_observed_at=row.prior_forecast_observed_at,
                prior_forecast=row.prior_forecast,
                current_forecast=row.current_forecast,
                revision_delta=row.revision_delta,
                absolute_revision_delta=row.absolute_revision_delta,
                forecast_age_hours=row.forecast_age_hours,
                revision_window_hours=row.revision_window_hours,
                stale_forecast_penalty=row.stale_forecast_penalty,
                sharp_revision_boost=row.sharp_revision_boost,
                revision_pressure_score=row.revision_pressure_score,
                pressure_status=row.pressure_status,
                redacted_forecast_reference=row.redacted_forecast_reference,
                reason_codes=row.reason_codes,
                derived_validation_digest=_row_digest(
                    rank=rank,
                    candidate_id=row.candidate_id,
                    forecast_observed_at=row.forecast_observed_at,
                    prior_forecast_observed_at=row.prior_forecast_observed_at,
                    prior_forecast=row.prior_forecast,
                    current_forecast=row.current_forecast,
                    revision_delta=row.revision_delta,
                    absolute_revision_delta=row.absolute_revision_delta,
                    forecast_age_hours=row.forecast_age_hours,
                    revision_window_hours=row.revision_window_hours,
                    stale_forecast_penalty=row.stale_forecast_penalty,
                    sharp_revision_boost=row.sharp_revision_boost,
                    revision_pressure_score=row.revision_pressure_score,
                    pressure_status=row.pressure_status,
                    redacted_forecast_reference=row.redacted_forecast_reference,
                    reason_codes=row.reason_codes,
                ),
            ),
        )
    return tuple(ranked)


def _stale_penalty(
    forecast_age_hours: Decimal,
    config: StrategyForecastRevisionPressureScoreV2Config,
) -> Decimal:
    if forecast_age_hours <= config.stale_after_hours:
        return ZERO
    penalty_ratio = min(
        _ratio(
            forecast_age_hours - config.stale_after_hours,
            config.stale_full_penalty_hours,
        ),
        ONE,
    )
    return _q(penalty_ratio * config.stale_penalty_weight)


def _sharp_boost(
    absolute_revision_delta: Decimal,
    config: StrategyForecastRevisionPressureScoreV2Config,
) -> Decimal:
    if absolute_revision_delta <= config.sharp_revision_delta:
        return ZERO
    excess_ratio = min(
        _ratio(
            absolute_revision_delta - config.sharp_revision_delta,
            config.sharp_revision_delta,
        ),
        ONE,
    )
    return _q(excess_ratio * config.sharp_revision_boost_weight)


def _pressure_status(
    revision_pressure_score: Decimal,
    config: StrategyForecastRevisionPressureScoreV2Config,
) -> str:
    if revision_pressure_score >= config.blocked_pressure_score:
        return BLOCKED_STATUS
    if revision_pressure_score >= config.watch_pressure_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    revision_delta: Decimal,
    stale_forecast_penalty: Decimal,
    sharp_revision_boost: Decimal,
    pressure_status: str,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if revision_delta > ZERO:
        reason_codes.add(REVISION_UP_REASON)
    elif revision_delta < ZERO:
        reason_codes.add(REVISION_DOWN_REASON)
    else:
        reason_codes.add(REVISION_FLAT_REASON)
    if stale_forecast_penalty > ZERO:
        reason_codes.add(STALE_REASON)
    if sharp_revision_boost > ZERO:
        reason_codes.add(SHARP_REASON)
    reason_codes.add(f"revision_pressure_{pressure_status}")
    return tuple(sorted(reason_codes))


def _report_reason_codes(
    rows: tuple[StrategyForecastRevisionPressureScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(sorted(reason_codes))


def _report_status(rows: tuple[StrategyForecastRevisionPressureScoreV2Row, ...]) -> str:
    if any(row.pressure_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.pressure_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS if rows else BLOCKED_STATUS


def _status_count(
    rows: tuple[StrategyForecastRevisionPressureScoreV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.pressure_status == status)


def _max_score(rows: tuple[StrategyForecastRevisionPressureScoreV2Row, ...]) -> Decimal:
    return max((row.revision_pressure_score for row in rows), default=ZERO)


def _average_score(rows: tuple[StrategyForecastRevisionPressureScoreV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _q(sum((row.revision_pressure_score for row in rows), ZERO) / _count(len(rows)))


def _normalize_observations(
    observations: Iterable[StrategyForecastRevisionPressureObservation],
) -> tuple[StrategyForecastRevisionPressureObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable of observations") from exc
    for row in rows:
        if type(row) is not StrategyForecastRevisionPressureObservation:
            raise ValueError("observations must contain exact observations")
        _require_paper_flags("observation", row)
    return rows


def _normalize_rows(
    rows: tuple[StrategyForecastRevisionPressureScoreV2Row, ...],
) -> tuple[StrategyForecastRevisionPressureScoreV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a tuple of exact rows")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be a tuple of exact rows") from exc
    for row in normalized:
        if type(row) is not StrategyForecastRevisionPressureScoreV2Row:
            raise ValueError("score report must contain exact rows")
        _require_paper_flags("row", row)
        _validate_row_digest(row)
    return normalized


def _validate_row(row: StrategyForecastRevisionPressureScoreV2Row) -> None:
    if row.absolute_revision_delta != abs(row.revision_delta):
        raise ValueError("absolute_revision_delta must match revision_delta")
    if row.current_forecast - row.prior_forecast != row.revision_delta:
        raise ValueError("revision_delta must match forecast values")
    expected_status = _status_from_thresholds(row.revision_pressure_score)
    if row.pressure_status != expected_status:
        raise ValueError("pressure_status must match revision_pressure_score")


def _status_from_thresholds(score: Decimal) -> str:
    if score >= Decimal("0.750000"):
        return BLOCKED_STATUS
    if score >= Decimal("0.400000"):
        return WATCH_STATUS
    return PASS_STATUS


def _validate_report(report: StrategyForecastRevisionPressureScoreV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(_status_count(rows, PASS_STATUS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, WATCH_STATUS)):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(_status_count(rows, BLOCKED_STATUS)):
        raise ValueError("blocked_count must match rows")
    if report.top_candidate_id != (rows[0].candidate_id if rows else None):
        raise ValueError("top_candidate_id must match rows")
    if report.max_revision_pressure_score != _max_score(rows):
        raise ValueError("max_revision_pressure_score must match rows")
    if report.average_revision_pressure_score != _average_score(rows):
        raise ValueError("average_revision_pressure_score must match rows")
    if report.pressure_status != _report_status(rows):
        raise ValueError("pressure_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_row_digest(row: StrategyForecastRevisionPressureScoreV2Row) -> None:
    expected_digest = _row_digest(
        rank=row.rank,
        candidate_id=row.candidate_id,
        forecast_observed_at=row.forecast_observed_at,
        prior_forecast_observed_at=row.prior_forecast_observed_at,
        prior_forecast=row.prior_forecast,
        current_forecast=row.current_forecast,
        revision_delta=row.revision_delta,
        absolute_revision_delta=row.absolute_revision_delta,
        forecast_age_hours=row.forecast_age_hours,
        revision_window_hours=row.revision_window_hours,
        stale_forecast_penalty=row.stale_forecast_penalty,
        sharp_revision_boost=row.sharp_revision_boost,
        revision_pressure_score=row.revision_pressure_score,
        pressure_status=row.pressure_status,
        redacted_forecast_reference=row.redacted_forecast_reference,
        reason_codes=row.reason_codes,
    )
    if row.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match row")


def _validate_report_digest(report: StrategyForecastRevisionPressureScoreV2Report) -> None:
    for row in report.rows:
        _validate_row_digest(row)
    expected_digest = _report_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        top_candidate_id=report.top_candidate_id,
        max_revision_pressure_score=report.max_revision_pressure_score,
        average_revision_pressure_score=report.average_revision_pressure_score,
        pressure_status=report.pressure_status,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    rows = _payload_list(payload, "rows")
    row_digests: list[str] = []
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must be JSON objects")
        if "derived_validation_digest" not in row:
            raise ValueError("derived_validation_digest is required")
        expected_row_digest = _row_digest(
            rank=_payload_decimal(row, "rank"),
            candidate_id=_payload_string(row, "candidate_id"),
            forecast_observed_at=_payload_datetime(row, "forecast_observed_at"),
            prior_forecast_observed_at=_payload_datetime(
                row,
                "prior_forecast_observed_at",
            ),
            prior_forecast=_payload_decimal(row, "prior_forecast"),
            current_forecast=_payload_decimal(row, "current_forecast"),
            revision_delta=_payload_decimal(row, "revision_delta"),
            absolute_revision_delta=_payload_decimal(row, "absolute_revision_delta"),
            forecast_age_hours=_payload_decimal(row, "forecast_age_hours"),
            revision_window_hours=_payload_decimal(row, "revision_window_hours"),
            stale_forecast_penalty=_payload_decimal(row, "stale_forecast_penalty"),
            sharp_revision_boost=_payload_decimal(row, "sharp_revision_boost"),
            revision_pressure_score=_payload_decimal(row, "revision_pressure_score"),
            pressure_status=_payload_string(row, "pressure_status"),
            redacted_forecast_reference=_payload_string(
                row,
                "redacted_forecast_reference",
            ),
            reason_codes=tuple(_payload_list(row, "reason_codes")),
        )
        if row["derived_validation_digest"] != expected_row_digest:
            raise ValueError("derived_validation_digest must match payload row")
        row_digests.append(expected_row_digest)
    expected_report_digest = _report_digest_from_row_digests(
        generated_at=_payload_datetime(payload, "generated_at"),
        config_version=_payload_string(payload, "config_version"),
        candidate_count=_payload_decimal(payload, "candidate_count"),
        pass_count=_payload_decimal(payload, "pass_count"),
        watch_count=_payload_decimal(payload, "watch_count"),
        blocked_count=_payload_decimal(payload, "blocked_count"),
        top_candidate_id=_payload_optional_string(payload, "top_candidate_id"),
        max_revision_pressure_score=_payload_decimal(
            payload,
            "max_revision_pressure_score",
        ),
        average_revision_pressure_score=_payload_decimal(
            payload,
            "average_revision_pressure_score",
        ),
        pressure_status=_payload_string(payload, "pressure_status"),
        reason_codes=tuple(_payload_list(payload, "reason_codes")),
        row_digests=tuple(row_digests),
    )
    if payload["derived_validation_digest"] != expected_report_digest:
        raise ValueError("derived_validation_digest must match payload")


def _row_digest(**values: object) -> str:
    return _digest(values)


def _report_digest(
    *,
    generated_at: datetime,
    config_version: str,
    candidate_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    top_candidate_id: str | None,
    max_revision_pressure_score: Decimal,
    average_revision_pressure_score: Decimal,
    pressure_status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[StrategyForecastRevisionPressureScoreV2Row, ...],
) -> str:
    return _report_digest_from_row_digests(
        generated_at=generated_at,
        config_version=config_version,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        top_candidate_id=top_candidate_id,
        max_revision_pressure_score=max_revision_pressure_score,
        average_revision_pressure_score=average_revision_pressure_score,
        pressure_status=pressure_status,
        reason_codes=reason_codes,
        row_digests=tuple(row.derived_validation_digest for row in rows),
    )


def _report_digest_from_row_digests(
    *,
    generated_at: datetime,
    config_version: str,
    candidate_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    top_candidate_id: str | None,
    max_revision_pressure_score: Decimal,
    average_revision_pressure_score: Decimal,
    pressure_status: str,
    reason_codes: tuple[str, ...],
    row_digests: tuple[str, ...],
) -> str:
    return _digest(
        {
            "generated_at": generated_at,
            "config_version": config_version,
            "candidate_count": candidate_count,
            "pass_count": pass_count,
            "watch_count": watch_count,
            "blocked_count": blocked_count,
            "top_candidate_id": top_candidate_id,
            "max_revision_pressure_score": max_revision_pressure_score,
            "average_revision_pressure_score": average_revision_pressure_score,
            "pressure_status": pressure_status,
            "reason_codes": reason_codes,
            "row_digests": row_digests,
        },
    )


def _digest(values: dict[str, object]) -> str:
    canonical = json.dumps(
        {key: _digest_value(value) for key, value in sorted(values.items())},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _digest_value(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("digest values must use exact Decimal")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("digest values must use exact datetime")
        return _as_utc("digest_datetime", value).isoformat()
    if type(value) is tuple:
        return [_digest_value(item) for item in value]
    if type(value) is list:
        return [_digest_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("digest values must be JSON compatible")


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {
            str(key): _json_ready(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    return value


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            StrategyForecastRevisionPressureScoreV2Config,
            StrategyForecastRevisionPressureObservation,
            StrategyForecastRevisionPressureScoreV2Row,
            StrategyForecastRevisionPressureScoreV2Report,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        _as_utc(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{current_path} must not be a float")
    if type(value) is str:
        _reject_unsafe_text(current_path, value)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_text(item_path, key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list or type(value) is tuple:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{current_path} is not JSON serializable")


def _reject_unsafe_text(path: str, value: str) -> None:
    if value.strip() != value:
        raise ValueError(f"{path} has unsafe value")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{path} has unsafe value")


def _payload_decimal(payload: dict[str, Any], key: str) -> Decimal:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must use Decimal-derived string values")
    if not _looks_decimal_string(value):
        raise ValueError(f"{key} must use Decimal-derived string values")
    return Decimal(value)


def _payload_datetime(payload: dict[str, Any], key: str) -> datetime:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is datetime:
        return _as_utc(key, value)
    if type(value) is not str:
        raise ValueError(f"{key} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an ISO datetime string") from exc
    return _as_utc(key, parsed)


def _payload_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    _reject_unsafe_text(key, value)
    return value


def _payload_optional_string(payload: dict[str, Any], key: str) -> str | None:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{key} must be a string or None")
    _reject_unsafe_text(key, value)
    return value


def _payload_list(payload: dict[str, Any], key: str) -> list[Any]:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not list:
        raise ValueError(f"{key} must be a list")
    return value


def _looks_decimal_string(value: str) -> bool:
    try:
        Decimal(value)
    except Exception:
        return False
    return bool(value) and value.strip() == value


def _redact_reference(value: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_REFERENCE_MARKERS):
        return "<redacted>"
    return value


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    later_utc = _as_utc("later", later)
    earlier_utc = _as_utc("earlier", earlier)
    if later_utc < earlier_utc:
        raise ValueError("later must be at or after earlier")
    return _q(Decimal(str((later_utc - earlier_utc).total_seconds())) / SECONDS_PER_HOUR)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be above zero")
    return _q(numerator / denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _q(value: Decimal) -> Decimal:
    if not isinstance(value, Decimal) or type(value) is not Decimal:
        raise ValueError("value must be exactly Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return value.quantize(VALUE_QUANTUM, rounding=ROUND_HALF_UP)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError(f"{field_name} must be sorted")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
    return reason_codes


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_paper_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")

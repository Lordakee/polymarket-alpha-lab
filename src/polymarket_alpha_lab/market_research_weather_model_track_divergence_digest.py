"""Pure Phase 1 weather model track divergence digest reducer.

The reducer only transforms caller-supplied observations into a public
screening report. It performs no IO, external access, durable storage, custody
action, or execution action.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re


DEFAULT_WEATHER_MODEL_TRACK_DIVERGENCE_DIGEST_CONFIG_VERSION = (
    "weather-model-track-divergence-digest-v0"
)

ROW_REASON_CODES = (
    "weather_model_track_divergence_blocked_spread",
    "weather_model_track_divergence_blocked_shift",
    "weather_model_track_divergence_watch_spread",
    "weather_model_track_divergence_watch_shift",
    "weather_model_track_divergence_stale_model_run",
    "weather_model_track_divergence_observed_stable",
)
REPORT_REASON_CODES = (
    "weather_model_track_divergence_blocked_risk_present",
    "weather_model_track_divergence_watch_risk_present",
    "weather_model_track_divergence_source_family_gap",
    "weather_model_track_divergence_digest_clear",
    "weather_model_track_divergence_digest_empty",
)
RISK_STATUSES = ("pass", "watch", "blocked")

VALUE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DEFAULT_WATCH_TRACK_SPREAD_KM = Decimal("75.000000")
DEFAULT_BLOCKED_TRACK_SPREAD_KM = Decimal("150.000000")
DEFAULT_WATCH_TRACK_SHIFT_KM = Decimal("50.000000")
DEFAULT_BLOCKED_TRACK_SHIFT_KM = Decimal("100.000000")
DEFAULT_MAX_MODEL_AGE_SECONDS = Decimal("21600.000000")
DEFAULT_MIN_SOURCE_FAMILY_COUNT = Decimal("2.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_FORBIDDEN_TEXT_TOKENS = (
    "mar" "ket",
    "slug",
    "ques" "tion",
    "pay" "load",
    "d" "s" "n",
    "li" "ve",
    "wal" "let",
    "acc" "ount",
    "ord" "er",
    "au" "th",
    "private",
    "key",
    "tra" "de",
    "invest" "ment",
    "recom" "mend",
    "se" "cret",
    "tok" "en",
    "b" "uy",
    "se" "ll",
    "pos" "ition",
    "bro" "ker",
    "sign" "ing",
)
_FORBIDDEN_TEXT_PHRASES = (
    "mar" "ket_" "slug",
    "private" "_" "key",
)

__all__ = (
    "DEFAULT_WEATHER_MODEL_TRACK_DIVERGENCE_DIGEST_CONFIG_VERSION",
    "WeatherModelTrackDivergenceConfig",
    "WeatherModelTrackDivergenceObservation",
    "WeatherModelTrackDivergenceReasonCodeCount",
    "WeatherModelTrackDivergenceReport",
    "WeatherModelTrackDivergenceRow",
    "build_market_research_weather_model_track_divergence_digest",
)


@dataclass(frozen=True)
class WeatherModelTrackDivergenceConfig:
    config_version: str = DEFAULT_WEATHER_MODEL_TRACK_DIVERGENCE_DIGEST_CONFIG_VERSION
    watch_track_spread_km: Decimal = DEFAULT_WATCH_TRACK_SPREAD_KM
    blocked_track_spread_km: Decimal = DEFAULT_BLOCKED_TRACK_SPREAD_KM
    watch_track_shift_km: Decimal = DEFAULT_WATCH_TRACK_SHIFT_KM
    blocked_track_shift_km: Decimal = DEFAULT_BLOCKED_TRACK_SHIFT_KM
    max_model_age_seconds: Decimal = DEFAULT_MAX_MODEL_AGE_SECONDS
    min_source_family_count: Decimal = DEFAULT_MIN_SOURCE_FAMILY_COUNT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherModelTrackDivergenceConfig:
            raise TypeError("WeatherModelTrackDivergenceConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not WeatherModelTrackDivergenceConfig:
            raise ValueError(
                "config must be exactly WeatherModelTrackDivergenceConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_WEATHER_MODEL_TRACK_DIVERGENCE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_track_spread_km",
            "blocked_track_spread_km",
            "watch_track_shift_km",
            "blocked_track_shift_km",
            "max_model_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_family_count",
            _require_whole_nonnegative_decimal(
                "min_source_family_count",
                self.min_source_family_count,
            ),
        )
        _validate_thresholds(
            watch_track_spread_km=self.watch_track_spread_km,
            blocked_track_spread_km=self.blocked_track_spread_km,
            watch_track_shift_km=self.watch_track_shift_km,
            blocked_track_shift_km=self.blocked_track_shift_km,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class WeatherModelTrackDivergenceObservation:
    observation_id: str
    event_id: str
    source_family: str
    model_run_at: datetime
    forecast_hour: Decimal
    track_spread_km: Decimal
    track_shift_km: Decimal
    source_row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherModelTrackDivergenceObservation:
            raise TypeError(
                "WeatherModelTrackDivergenceObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherModelTrackDivergenceObservation:
            raise ValueError(
                "observation must be exactly WeatherModelTrackDivergenceObservation",
            )
        for field_name in ("observation_id", "event_id", "source_family"):
            object.__setattr__(
                self,
                field_name,
                _require_canonical_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "model_run_at",
            _as_utc("model_run_at", self.model_run_at),
        )
        for field_name in ("forecast_hour", "track_spread_km", "track_shift_km"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_row_count",
            _require_positive_whole_decimal("source_row_count", self.source_row_count),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class WeatherModelTrackDivergenceRow:
    observation_id: str
    event_id: str
    source_family: str
    model_run_at: datetime
    model_age_seconds: Decimal
    forecast_hour: Decimal
    track_spread_km: Decimal
    track_shift_km: Decimal
    source_row_count: Decimal
    risk_score: Decimal
    risk_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherModelTrackDivergenceRow:
            raise TypeError("WeatherModelTrackDivergenceRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not WeatherModelTrackDivergenceRow:
            raise ValueError("row must be exactly WeatherModelTrackDivergenceRow")
        for field_name in ("observation_id", "event_id", "source_family"):
            object.__setattr__(
                self,
                field_name,
                _require_canonical_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "model_run_at",
            _as_utc("model_run_at", self.model_run_at),
        )
        for field_name in (
            "model_age_seconds",
            "forecast_hour",
            "track_spread_km",
            "track_shift_km",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_row_count",
            _require_positive_whole_decimal("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "risk_score",
            _require_probability("risk_score", self.risk_score),
        )
        _require_member("risk_status", self.risk_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_shape(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class WeatherModelTrackDivergenceReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherModelTrackDivergenceReasonCodeCount:
            raise TypeError(
                "WeatherModelTrackDivergenceReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherModelTrackDivergenceReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "WeatherModelTrackDivergenceReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES + REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_probability("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class WeatherModelTrackDivergenceReport:
    generated_at: datetime
    config_version: str
    watch_track_spread_km: Decimal
    blocked_track_spread_km: Decimal
    watch_track_shift_km: Decimal
    blocked_track_shift_km: Decimal
    max_model_age_seconds: Decimal
    min_source_family_count: Decimal
    observation_count: Decimal
    source_row_count: Decimal
    blocked_observation_count: Decimal
    watch_observation_count: Decimal
    pass_observation_count: Decimal
    source_family_count: Decimal
    stale_model_run_count: Decimal
    max_track_spread_km: Decimal
    max_track_shift_km: Decimal
    max_risk_score: Decimal
    average_risk_score: Decimal
    blocked_observation_ratio: Decimal
    digest_status: str
    screening_next_step: str
    divergence_rows: tuple[WeatherModelTrackDivergenceRow, ...]
    reason_code_counts: tuple[WeatherModelTrackDivergenceReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherModelTrackDivergenceReport:
            raise TypeError("WeatherModelTrackDivergenceReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not WeatherModelTrackDivergenceReport:
            raise ValueError("report must be exactly WeatherModelTrackDivergenceReport")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_WEATHER_MODEL_TRACK_DIVERGENCE_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_track_spread_km",
            "blocked_track_spread_km",
            "watch_track_shift_km",
            "blocked_track_shift_km",
            "max_model_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_family_count",
            _require_whole_nonnegative_decimal(
                "min_source_family_count",
                self.min_source_family_count,
            ),
        )
        _validate_thresholds(
            watch_track_spread_km=self.watch_track_spread_km,
            blocked_track_spread_km=self.blocked_track_spread_km,
            watch_track_shift_km=self.watch_track_shift_km,
            blocked_track_shift_km=self.blocked_track_shift_km,
        )
        for field_name in (
            "observation_count",
            "source_row_count",
            "blocked_observation_count",
            "watch_observation_count",
            "pass_observation_count",
            "source_family_count",
            "stale_model_run_count",
            "max_track_spread_km",
            "max_track_shift_km",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_risk_score",
            "average_risk_score",
            "blocked_observation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "screening_next_step",
            _require_canonical_string("screening_next_step", self.screening_next_step),
        )
        object.__setattr__(
            self,
            "divergence_rows",
            _normalize_rows(self.divergence_rows),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_weather_model_track_divergence_digest(
    observations: Iterable[WeatherModelTrackDivergenceObservation],
    *,
    config: WeatherModelTrackDivergenceConfig,
    generated_at: datetime,
) -> WeatherModelTrackDivergenceReport:
    if type(config) is not WeatherModelTrackDivergenceConfig:
        raise ValueError("config must be exactly WeatherModelTrackDivergenceConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_inputs(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _row_for_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    observation_count = _count_decimal(len(rows))
    blocked_count = _count_decimal(
        sum(1 for row in rows if row.risk_status == "blocked"),
    )
    source_family_count = _count_decimal(len({row.source_family for row in rows}))
    reason_codes = _report_reason_codes(
        rows,
        source_family_count=source_family_count,
        min_source_family_count=config.min_source_family_count,
    )
    digest_status = _digest_status(reason_codes)
    row_reason_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)

    return WeatherModelTrackDivergenceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        watch_track_spread_km=config.watch_track_spread_km,
        blocked_track_spread_km=config.blocked_track_spread_km,
        watch_track_shift_km=config.watch_track_shift_km,
        blocked_track_shift_km=config.blocked_track_shift_km,
        max_model_age_seconds=config.max_model_age_seconds,
        min_source_family_count=config.min_source_family_count,
        observation_count=observation_count,
        source_row_count=_sum_decimal(row.source_row_count for row in rows),
        blocked_observation_count=blocked_count,
        watch_observation_count=_count_decimal(
            sum(1 for row in rows if row.risk_status == "watch"),
        ),
        pass_observation_count=_count_decimal(
            sum(1 for row in rows if row.risk_status == "pass"),
        ),
        source_family_count=source_family_count,
        stale_model_run_count=_count_decimal(
            sum(
                1
                for row in rows
                if "weather_model_track_divergence_stale_model_run" in row.reason_codes
            ),
        ),
        max_track_spread_km=max((row.track_spread_km for row in rows), default=ZERO),
        max_track_shift_km=max((row.track_shift_km for row in rows), default=ZERO),
        max_risk_score=max((row.risk_score for row in rows), default=ZERO),
        average_risk_score=_ratio(_sum_decimal(row.risk_score for row in rows), observation_count),
        blocked_observation_ratio=_ratio(blocked_count, observation_count),
        digest_status=digest_status,
        screening_next_step=_screening_next_step(digest_status),
        divergence_rows=rows,
        reason_code_counts=_reason_code_counts(row_reason_codes, observation_count),
        reason_codes=reason_codes,
    )


def _row_for_observation(
    observation: WeatherModelTrackDivergenceObservation,
    *,
    config: WeatherModelTrackDivergenceConfig,
    generated_at: datetime,
) -> WeatherModelTrackDivergenceRow:
    model_age_seconds = _age_seconds(generated_at, observation.model_run_at)
    reason_codes = _metric_reason_codes(
        track_spread_km=observation.track_spread_km,
        track_shift_km=observation.track_shift_km,
        model_age_seconds=model_age_seconds,
        watch_track_spread_km=config.watch_track_spread_km,
        blocked_track_spread_km=config.blocked_track_spread_km,
        watch_track_shift_km=config.watch_track_shift_km,
        blocked_track_shift_km=config.blocked_track_shift_km,
        max_model_age_seconds=config.max_model_age_seconds,
    )
    risk_status = _risk_status_from_reason_codes(reason_codes)
    return WeatherModelTrackDivergenceRow(
        observation_id=observation.observation_id,
        event_id=observation.event_id,
        source_family=observation.source_family,
        model_run_at=observation.model_run_at,
        model_age_seconds=model_age_seconds,
        forecast_hour=observation.forecast_hour,
        track_spread_km=observation.track_spread_km,
        track_shift_km=observation.track_shift_km,
        source_row_count=observation.source_row_count,
        risk_score=_risk_score(
            track_spread_km=observation.track_spread_km,
            track_shift_km=observation.track_shift_km,
            model_age_seconds=model_age_seconds,
            reason_codes=reason_codes,
            blocked_track_spread_km=config.blocked_track_spread_km,
            blocked_track_shift_km=config.blocked_track_shift_km,
            max_model_age_seconds=config.max_model_age_seconds,
        ),
        risk_status=risk_status,
        reason_codes=reason_codes,
    )


def _metric_reason_codes(
    *,
    track_spread_km: Decimal,
    track_shift_km: Decimal,
    model_age_seconds: Decimal,
    watch_track_spread_km: Decimal,
    blocked_track_spread_km: Decimal,
    watch_track_shift_km: Decimal,
    blocked_track_shift_km: Decimal,
    max_model_age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if track_spread_km >= blocked_track_spread_km:
        reasons.append("weather_model_track_divergence_blocked_spread")
    elif track_spread_km >= watch_track_spread_km:
        reasons.append("weather_model_track_divergence_watch_spread")
    if track_shift_km >= blocked_track_shift_km:
        reasons.append("weather_model_track_divergence_blocked_shift")
    elif track_shift_km >= watch_track_shift_km:
        reasons.append("weather_model_track_divergence_watch_shift")
    if model_age_seconds > max_model_age_seconds:
        reasons.append("weather_model_track_divergence_stale_model_run")
    if not reasons:
        reasons.append("weather_model_track_divergence_observed_stable")
    return _sort_reason_codes(tuple(dict.fromkeys(reasons)), allowed=ROW_REASON_CODES)


def _risk_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        "weather_model_track_divergence_blocked_spread" in reason_codes
        or "weather_model_track_divergence_blocked_shift" in reason_codes
    ):
        return "blocked"
    if reason_codes == ("weather_model_track_divergence_observed_stable",):
        return "pass"
    return "watch"


def _risk_score(
    *,
    track_spread_km: Decimal,
    track_shift_km: Decimal,
    model_age_seconds: Decimal,
    reason_codes: tuple[str, ...],
    blocked_track_spread_km: Decimal,
    blocked_track_shift_km: Decimal,
    max_model_age_seconds: Decimal,
) -> Decimal:
    if reason_codes == ("weather_model_track_divergence_observed_stable",):
        return ZERO
    components: list[Decimal] = []
    if (
        "weather_model_track_divergence_blocked_spread" in reason_codes
        or "weather_model_track_divergence_watch_spread" in reason_codes
    ):
        components.append(_ratio(track_spread_km, blocked_track_spread_km))
    if (
        "weather_model_track_divergence_blocked_shift" in reason_codes
        or "weather_model_track_divergence_watch_shift" in reason_codes
    ):
        components.append(_ratio(track_shift_km, blocked_track_shift_km))
    if "weather_model_track_divergence_stale_model_run" in reason_codes:
        components.append(_ratio(model_age_seconds, max_model_age_seconds))
    return min(max(components, default=ZERO), ONE)


def _report_reason_codes(
    rows: tuple[WeatherModelTrackDivergenceRow, ...],
    *,
    source_family_count: Decimal,
    min_source_family_count: Decimal,
) -> tuple[str, ...]:
    if not rows:
        return ("weather_model_track_divergence_digest_empty",)
    reasons: list[str] = []
    if any(row.risk_status == "blocked" for row in rows):
        reasons.append("weather_model_track_divergence_blocked_risk_present")
    if any(row.risk_status == "watch" for row in rows):
        reasons.append("weather_model_track_divergence_watch_risk_present")
    if source_family_count < min_source_family_count:
        reasons.append("weather_model_track_divergence_source_family_gap")
    if not reasons:
        reasons.append("weather_model_track_divergence_digest_clear")
    return _sort_reason_codes(tuple(dict.fromkeys(reasons)), allowed=REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    observation_count: Decimal,
) -> tuple[WeatherModelTrackDivergenceReasonCodeCount, ...]:
    if not reason_codes:
        return (
            WeatherModelTrackDivergenceReasonCodeCount(
                reason_code="weather_model_track_divergence_digest_empty",
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    return tuple(
        WeatherModelTrackDivergenceReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(sum(1 for item in reason_codes if item == reason_code)),
            observation_ratio=_ratio(
                _count_decimal(sum(1 for item in reason_codes if item == reason_code)),
                observation_count,
            ),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in reason_codes
    )


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if "weather_model_track_divergence_digest_empty" in reason_codes:
        return "blocked"
    if "weather_model_track_divergence_blocked_risk_present" in reason_codes:
        return "blocked"
    if "weather_model_track_divergence_source_family_gap" in reason_codes:
        return "blocked"
    if "weather_model_track_divergence_watch_risk_present" in reason_codes:
        return "watch"
    return "pass"


def _screening_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_weather_model_track_divergence_screen"
    if status == "watch":
        return "monitor_report_only_weather_model_track_divergence_screen"
    return "block_report_only_weather_model_track_divergence_screen"


def _validate_thresholds(
    *,
    watch_track_spread_km: Decimal,
    blocked_track_spread_km: Decimal,
    watch_track_shift_km: Decimal,
    blocked_track_shift_km: Decimal,
) -> None:
    if blocked_track_spread_km < watch_track_spread_km:
        raise ValueError("blocked_track_spread_km must be at least watch threshold")
    if blocked_track_shift_km < watch_track_shift_km:
        raise ValueError("blocked_track_shift_km must be at least watch threshold")


def _validate_row_shape(row: WeatherModelTrackDivergenceRow) -> None:
    if row.risk_status == "pass" and row.reason_codes != (
        "weather_model_track_divergence_observed_stable",
    ):
        raise ValueError("pass rows must only contain stable reason code")
    if row.risk_status == "blocked" and not (
        "weather_model_track_divergence_blocked_spread" in row.reason_codes
        or "weather_model_track_divergence_blocked_shift" in row.reason_codes
    ):
        raise ValueError("blocked rows must include blocked divergence reason code")
    if row.risk_status == "watch" and any(
        reason_code
        in (
            "weather_model_track_divergence_blocked_spread",
            "weather_model_track_divergence_blocked_shift",
            "weather_model_track_divergence_observed_stable",
        )
        for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows must only contain watch reason codes")


def _validate_report(report: WeatherModelTrackDivergenceReport) -> None:
    if report.observation_count != _count_decimal(len(report.divergence_rows)):
        raise ValueError("observation_count must match divergence_rows")
    if report.source_row_count != _sum_decimal(
        row.source_row_count for row in report.divergence_rows
    ):
        raise ValueError("source_row_count must match divergence_rows")
    if report.blocked_observation_count != _count_decimal(
        sum(1 for row in report.divergence_rows if row.risk_status == "blocked"),
    ):
        raise ValueError("blocked_observation_count must match divergence_rows")
    if report.watch_observation_count != _count_decimal(
        sum(1 for row in report.divergence_rows if row.risk_status == "watch"),
    ):
        raise ValueError("watch_observation_count must match divergence_rows")
    if report.pass_observation_count != _count_decimal(
        sum(1 for row in report.divergence_rows if row.risk_status == "pass"),
    ):
        raise ValueError("pass_observation_count must match divergence_rows")
    if report.source_family_count != _count_decimal(
        len({row.source_family for row in report.divergence_rows}),
    ):
        raise ValueError("source_family_count must match divergence_rows")
    if report.stale_model_run_count != _count_decimal(
        sum(
            1
            for row in report.divergence_rows
            if "weather_model_track_divergence_stale_model_run" in row.reason_codes
        ),
    ):
        raise ValueError("stale_model_run_count must match divergence_rows")
    if report.max_track_spread_km != max(
        (row.track_spread_km for row in report.divergence_rows),
        default=ZERO,
    ):
        raise ValueError("max_track_spread_km must match divergence_rows")
    if report.max_track_shift_km != max(
        (row.track_shift_km for row in report.divergence_rows),
        default=ZERO,
    ):
        raise ValueError("max_track_shift_km must match divergence_rows")
    if report.max_risk_score != max(
        (row.risk_score for row in report.divergence_rows),
        default=ZERO,
    ):
        raise ValueError("max_risk_score must match divergence_rows")
    if report.average_risk_score != _ratio(
        _sum_decimal(row.risk_score for row in report.divergence_rows),
        report.observation_count,
    ):
        raise ValueError("average_risk_score must match divergence_rows")
    if report.blocked_observation_ratio != _ratio(
        report.blocked_observation_count,
        report.observation_count,
    ):
        raise ValueError("blocked_observation_ratio must match divergence_rows")
    for row in report.divergence_rows:
        expected_reason_codes = _metric_reason_codes(
            track_spread_km=row.track_spread_km,
            track_shift_km=row.track_shift_km,
            model_age_seconds=row.model_age_seconds,
            watch_track_spread_km=report.watch_track_spread_km,
            blocked_track_spread_km=report.blocked_track_spread_km,
            watch_track_shift_km=report.watch_track_shift_km,
            blocked_track_shift_km=report.blocked_track_shift_km,
            max_model_age_seconds=report.max_model_age_seconds,
        )
        if row.reason_codes != expected_reason_codes:
            raise ValueError("row reason_codes must match report thresholds")
        if row.risk_status != _risk_status_from_reason_codes(expected_reason_codes):
            raise ValueError("row risk_status must match report thresholds")
        if row.risk_score != _risk_score(
            track_spread_km=row.track_spread_km,
            track_shift_km=row.track_shift_km,
            model_age_seconds=row.model_age_seconds,
            reason_codes=expected_reason_codes,
            blocked_track_spread_km=report.blocked_track_spread_km,
            blocked_track_shift_km=report.blocked_track_shift_km,
            max_model_age_seconds=report.max_model_age_seconds,
        ):
            raise ValueError("row risk_score must match report thresholds")
    expected_report_reasons = _report_reason_codes(
        report.divergence_rows,
        source_family_count=report.source_family_count,
        min_source_family_count=report.min_source_family_count,
    )
    if report.reason_codes != expected_report_reasons:
        raise ValueError("reason_codes must match divergence_rows")
    if report.digest_status != _digest_status(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if report.screening_next_step != _screening_next_step(report.digest_status):
        raise ValueError("screening_next_step must match digest_status")
    row_reason_codes = tuple(
        reason_code for row in report.divergence_rows for reason_code in row.reason_codes
    )
    if report.reason_code_counts != _reason_code_counts(
        row_reason_codes,
        report.observation_count,
    ):
        raise ValueError("reason_code_counts must match divergence_rows")


def _normalize_inputs(
    observations: Iterable[WeatherModelTrackDivergenceObservation],
    *,
    generated_at: datetime,
) -> tuple[WeatherModelTrackDivergenceObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must contain weather model track observations")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must contain weather model track observations") from exc
    seen_observation_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not WeatherModelTrackDivergenceObservation:
            raise ValueError(
                "observations must contain WeatherModelTrackDivergenceObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.model_run_at > generated_at:
            raise ValueError("model_run_at must not be in the future")
        if observation.observation_id in seen_observation_ids:
            raise ValueError("observations must not contain duplicate observation_id values")
        seen_observation_ids.add(observation.observation_id)
    return normalized


def _normalize_rows(value: object) -> tuple[WeatherModelTrackDivergenceRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("divergence_rows must contain weather model track rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("divergence_rows must contain weather model track rows") from exc
    seen_observation_ids: set[str] = set()
    for row in rows:
        if type(row) is not WeatherModelTrackDivergenceRow:
            raise ValueError("divergence_rows must contain WeatherModelTrackDivergenceRow")
        _require_hard_flags("row", row)
        if row.observation_id in seen_observation_ids:
            raise ValueError("divergence_rows must not contain duplicate observation_id values")
        seen_observation_ids.add(row.observation_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("divergence_rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[WeatherModelTrackDivergenceReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in counts:
        if type(item) is not WeatherModelTrackDivergenceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain WeatherModelTrackDivergenceReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    allowed = ROW_REASON_CODES + REPORT_REASON_CODES
    if counts != tuple(sorted(counts, key=lambda item: allowed.index(item.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must contain at least one reason code")
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if reason_codes != _sort_reason_codes(reason_codes, allowed=allowed):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return reason_codes


def _sort_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=lambda reason_code: allowed.index(reason_code)))


def _row_sort_key(row: WeatherModelTrackDivergenceRow) -> tuple[int, Decimal, str, str]:
    return (STATUS_RANK[row.risk_status], -row.risk_score, row.event_id, row.observation_id)


def _age_seconds(generated_at: datetime, model_run_at: datetime) -> Decimal:
    delta = generated_at - model_run_at
    return _quantize(
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _contains_forbidden_text(value):
        raise ValueError(f"{field_name} contains unsafe weather model track detail")
    return value


def _contains_forbidden_text(value: str) -> bool:
    lowered = value.lower()
    tokens = tuple(token for token in re.split(r"[^a-z0-9]+", lowered) if token)
    joined_tokens = "_".join(tokens)
    return any(token in _FORBIDDEN_TEXT_TOKENS for token in tokens) or any(
        phrase in joined_tokens for phrase in _FORBIDDEN_TEXT_PHRASES
    )


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(VALUE_QUANT)
    except InvalidOperation as exc:
        raise ValueError("decimal value could not be quantized") from exc


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")

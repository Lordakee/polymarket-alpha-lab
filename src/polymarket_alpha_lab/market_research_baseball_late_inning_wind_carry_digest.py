"""Pure Phase 1 baseball late inning wind carry digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_INNING_WIND_CARRY_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-late-inning-wind-carry-digest-v0"
)
REDACTED_SOURCE_REF_VALUE = "[redacted-ref]"

CLEAR_REASON = "baseball_late_inning_wind_carry_clear"
STALE_INPUT_REASON = "baseball_late_inning_wind_carry_stale_input"
WIND_CARRY_SHIFT_REASON = "baseball_late_inning_wind_carry_wind_carry_shift"
GUST_CARRY_SHIFT_REASON = "baseball_late_inning_wind_carry_gust_carry_shift"
TEMPERATURE_BOOST_REASON = "baseball_late_inning_wind_carry_temperature_boost"
HUMIDITY_CHANGE_REASON = "baseball_late_inning_wind_carry_humidity_change"
OPEN_ROOF_REASON = "baseball_late_inning_wind_carry_open_roof"
TOTALS_MARKET_REASON = "baseball_late_inning_wind_carry_totals_market"
HOME_RUN_MARKET_REASON = "baseball_late_inning_wind_carry_home_run_market"
DIGEST_CLEAR_REASON = "baseball_late_inning_wind_carry_digest_clear"
DIGEST_EMPTY_REASON = "baseball_late_inning_wind_carry_digest_empty"

ROW_REASON_CODES = (
    CLEAR_REASON,
    STALE_INPUT_REASON,
    WIND_CARRY_SHIFT_REASON,
    GUST_CARRY_SHIFT_REASON,
    TEMPERATURE_BOOST_REASON,
    HUMIDITY_CHANGE_REASON,
    OPEN_ROOF_REASON,
    TOTALS_MARKET_REASON,
    HOME_RUN_MARKET_REASON,
)
REPORT_REASON_CODES = (
    STALE_INPUT_REASON,
    WIND_CARRY_SHIFT_REASON,
    GUST_CARRY_SHIFT_REASON,
    TEMPERATURE_BOOST_REASON,
    HUMIDITY_CHANGE_REASON,
    OPEN_ROOF_REASON,
    TOTALS_MARKET_REASON,
    HOME_RUN_MARKET_REASON,
    DIGEST_CLEAR_REASON,
    DIGEST_EMPTY_REASON,
)

STATUSES = ("pass", "watch", "blocked")
MARKET_TYPES = ("game_total", "home_run")
ROOF_STATUSES = ("closed", "open", "unknown")
WIND_DIRECTIONS = ("inbound", "neutral", "outbound", "crosswind")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
ONE_HUNDRED = Decimal("100.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
CANONICAL_TEXT_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("cre", "dential"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("ex", "change"),
        _join_parts("sign", "ing"),
    ),
)
SOURCE_REF_REDACTION_FRAGMENTS = frozenset(
    (
        _join_parts("api", "_", "key"),
        _join_parts("bear", "er"),
        _join_parts("cre", "dential"),
        _join_parts("pass", "word"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
    ),
)


@dataclass(frozen=True)
class MarketResearchBaseballLateInningWindCarryDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_INNING_WIND_CARRY_DIGEST_CONFIG_VERSION
    )
    watch_wind_carry_shift_mph: Decimal = Decimal("6.000000")
    blocked_wind_carry_shift_mph: Decimal = Decimal("16.000000")
    watch_gust_carry_shift_mph: Decimal = Decimal("10.000000")
    blocked_gust_carry_shift_mph: Decimal = Decimal("24.000000")
    min_temperature_increase_f: Decimal = Decimal("7.000000")
    min_humidity_change_pct: Decimal = Decimal("12.000000")
    min_late_inning: Decimal = Decimal("7.000000")
    max_input_age_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballLateInningWindCarryDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_INNING_WIND_CARRY_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_wind_carry_shift_mph",
            "blocked_wind_carry_shift_mph",
            "watch_gust_carry_shift_mph",
            "blocked_gust_carry_shift_mph",
            "min_temperature_increase_f",
            "min_humidity_change_pct",
            "min_late_inning",
            "max_input_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_wind_carry_shift_mph > self.blocked_wind_carry_shift_mph:
            raise ValueError(
                "watch_wind_carry_shift_mph must not exceed "
                "blocked_wind_carry_shift_mph",
            )
        if self.watch_gust_carry_shift_mph > self.blocked_gust_carry_shift_mph:
            raise ValueError(
                "watch_gust_carry_shift_mph must not exceed "
                "blocked_gust_carry_shift_mph",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBaseballLateInningWindCarryObservation:
    source_id: str
    market_slug: str
    event_slug: str
    market_type: str
    current_inning: Decimal
    scheduled_start_at: datetime
    observed_at: datetime
    prior_observed_at: datetime
    prior_wind_direction: str
    current_wind_direction: str
    prior_sustained_wind_mph: Decimal
    current_sustained_wind_mph: Decimal
    prior_gust_wind_mph: Decimal
    current_gust_wind_mph: Decimal
    prior_temperature_f: Decimal
    current_temperature_f: Decimal
    prior_humidity_pct: Decimal
    current_humidity_pct: Decimal
    roof_status: str
    roof_status_confirmed: bool
    source_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballLateInningWindCarryObservation,
            "observation",
        )
        for field_name in ("source_id", "market_slug", "event_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("market_type", self.market_type, MARKET_TYPES)
        object.__setattr__(
            self,
            "current_inning",
            _require_positive_decimal("current_inning", self.current_inning),
        )
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "prior_observed_at",
            _as_utc("prior_observed_at", self.prior_observed_at),
        )
        _require_member("prior_wind_direction", self.prior_wind_direction, WIND_DIRECTIONS)
        _require_member(
            "current_wind_direction",
            self.current_wind_direction,
            WIND_DIRECTIONS,
        )
        for field_name in (
            "prior_sustained_wind_mph",
            "current_sustained_wind_mph",
            "prior_gust_wind_mph",
            "current_gust_wind_mph",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("prior_temperature_f", "current_temperature_f"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("prior_humidity_pct", "current_humidity_pct"):
            object.__setattr__(
                self,
                field_name,
                _require_percentage(field_name, getattr(self, field_name)),
            )
        _require_member("roof_status", self.roof_status, ROOF_STATUSES)
        _require_bool("roof_status_confirmed", self.roof_status_confirmed)
        object.__setattr__(
            self,
            "source_refs",
            _normalize_source_refs("source_refs", self.source_refs),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchBaseballLateInningWindCarryDigestRow:
    source_id: str
    market_slug: str
    event_slug: str
    market_type: str
    row_status: str
    current_inning: Decimal
    scheduled_start_at: datetime
    observed_at: datetime
    prior_observed_at: datetime
    input_age_seconds: Decimal
    prior_wind_direction: str
    current_wind_direction: str
    prior_sustained_wind_mph: Decimal
    current_sustained_wind_mph: Decimal
    prior_gust_wind_mph: Decimal
    current_gust_wind_mph: Decimal
    wind_carry_shift_mph: Decimal
    gust_carry_shift_mph: Decimal
    prior_temperature_f: Decimal
    current_temperature_f: Decimal
    temperature_increase_f: Decimal
    prior_humidity_pct: Decimal
    current_humidity_pct: Decimal
    humidity_change_pct: Decimal
    roof_status: str
    roof_status_confirmed: bool
    source_ref_count: Decimal
    redacted_source_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballLateInningWindCarryDigestRow,
            "row",
        )
        for field_name in ("source_id", "market_slug", "event_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("market_type", self.market_type, MARKET_TYPES)
        _require_member("row_status", self.row_status, STATUSES)
        object.__setattr__(
            self,
            "current_inning",
            _require_positive_decimal("current_inning", self.current_inning),
        )
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "prior_observed_at",
            _as_utc("prior_observed_at", self.prior_observed_at),
        )
        for field_name in (
            "input_age_seconds",
            "prior_sustained_wind_mph",
            "current_sustained_wind_mph",
            "prior_gust_wind_mph",
            "current_gust_wind_mph",
            "source_ref_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "wind_carry_shift_mph",
            "gust_carry_shift_mph",
            "prior_temperature_f",
            "current_temperature_f",
            "temperature_increase_f",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("prior_humidity_pct", "current_humidity_pct"):
            object.__setattr__(
                self,
                field_name,
                _require_percentage(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "humidity_change_pct",
            _require_nonnegative_decimal("humidity_change_pct", self.humidity_change_pct),
        )
        _require_member("prior_wind_direction", self.prior_wind_direction, WIND_DIRECTIONS)
        _require_member(
            "current_wind_direction",
            self.current_wind_direction,
            WIND_DIRECTIONS,
        )
        _require_member("roof_status", self.roof_status, ROOF_STATUSES)
        _require_bool("roof_status_confirmed", self.roof_status_confirmed)
        object.__setattr__(
            self,
            "redacted_source_refs",
            _normalize_source_refs("redacted_source_refs", self.redacted_source_refs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBaseballLateInningWindCarryReasonCodeCount:
    reason_code: str
    market_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballLateInningWindCarryReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "market_count",
            _require_nonnegative_decimal("market_count", self.market_count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchBaseballLateInningWindCarryDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_input_count: Decimal
    late_inning_risk_count: Decimal
    wind_carry_shift_count: Decimal
    gust_carry_shift_count: Decimal
    temperature_shift_count: Decimal
    humidity_shift_count: Decimal
    open_roof_count: Decimal
    totals_market_count: Decimal
    home_run_market_count: Decimal
    max_input_age_seconds: Decimal
    max_wind_carry_shift_mph: Decimal
    max_gust_carry_shift_mph: Decimal
    max_temperature_increase_f: Decimal
    max_humidity_change_pct: Decimal
    carry_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MarketResearchBaseballLateInningWindCarryDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchBaseballLateInningWindCarryReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballLateInningWindCarryDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_INNING_WIND_CARRY_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_input_count",
            "late_inning_risk_count",
            "wind_carry_shift_count",
            "gust_carry_shift_count",
            "temperature_shift_count",
            "humidity_shift_count",
            "open_roof_count",
            "totals_market_count",
            "home_run_market_count",
            "max_input_age_seconds",
            "max_humidity_change_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_wind_carry_shift_mph",
            "max_gust_carry_shift_mph",
            "max_temperature_increase_f",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "carry_risk_score",
            _require_ratio("carry_risk_score", self.carry_risk_score),
        )
        _require_member("digest_status", self.digest_status, STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
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
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        reject_unsafe_surface_fields(
            "baseball_late_inning_wind_carry_digest",
            self,
        )


def build_market_research_baseball_late_inning_wind_carry_digest(
    observations: Iterable[MarketResearchBaseballLateInningWindCarryObservation],
    *,
    config: MarketResearchBaseballLateInningWindCarryDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballLateInningWindCarryDigestReport:
    if type(config) is not MarketResearchBaseballLateInningWindCarryDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchBaseballLateInningWindCarryDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations, generated_at=generated_at_utc)
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
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)

    return MarketResearchBaseballLateInningWindCarryDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        stale_input_count=_reason_count(rows, STALE_INPUT_REASON),
        late_inning_risk_count=_late_inning_risk_count(rows),
        wind_carry_shift_count=_reason_count(rows, WIND_CARRY_SHIFT_REASON),
        gust_carry_shift_count=_reason_count(rows, GUST_CARRY_SHIFT_REASON),
        temperature_shift_count=_reason_count(rows, TEMPERATURE_BOOST_REASON),
        humidity_shift_count=_reason_count(rows, HUMIDITY_CHANGE_REASON),
        open_roof_count=_reason_count(rows, OPEN_ROOF_REASON),
        totals_market_count=_reason_count(rows, TOTALS_MARKET_REASON),
        home_run_market_count=_reason_count(rows, HOME_RUN_MARKET_REASON),
        max_input_age_seconds=_max_row_decimal(rows, "input_age_seconds"),
        max_wind_carry_shift_mph=_max_row_decimal(rows, "wind_carry_shift_mph"),
        max_gust_carry_shift_mph=_max_row_decimal(rows, "gust_carry_shift_mph"),
        max_temperature_increase_f=_max_row_decimal(rows, "temperature_increase_f"),
        max_humidity_change_pct=_max_row_decimal(rows, "humidity_change_pct"),
        carry_risk_score=_risk_score(digest_status, rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_baseball_late_inning_wind_carry_digest_payload(
    report: MarketResearchBaseballLateInningWindCarryDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBaseballLateInningWindCarryDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchBaseballLateInningWindCarryDigestReport",
        )
    _require_hard_flags("report", report)
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report must reduce to a JSON object")
    reject_unsafe_surface_fields(
        "baseball_late_inning_wind_carry_digest",
        ready,
    )
    return ready


def _row_from_observation(
    observation: MarketResearchBaseballLateInningWindCarryObservation,
    *,
    config: MarketResearchBaseballLateInningWindCarryDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballLateInningWindCarryDigestRow:
    input_age_seconds = _age_seconds(generated_at, observation.observed_at)
    wind_carry_shift_mph = _carry_shift(
        prior_direction=observation.prior_wind_direction,
        current_direction=observation.current_wind_direction,
        prior_value=observation.prior_sustained_wind_mph,
        current_value=observation.current_sustained_wind_mph,
    )
    gust_carry_shift_mph = _carry_shift(
        prior_direction=observation.prior_wind_direction,
        current_direction=observation.current_wind_direction,
        prior_value=observation.prior_gust_wind_mph,
        current_value=observation.current_gust_wind_mph,
    )
    temperature_increase_f = _quantize_decimal(
        observation.current_temperature_f - observation.prior_temperature_f,
    )
    humidity_change_pct = _quantize_decimal(
        abs(observation.current_humidity_pct - observation.prior_humidity_pct),
    )
    reason_codes = _row_reason_codes(
        observation,
        config=config,
        input_age_seconds=input_age_seconds,
        wind_carry_shift_mph=wind_carry_shift_mph,
        gust_carry_shift_mph=gust_carry_shift_mph,
        temperature_increase_f=temperature_increase_f,
        humidity_change_pct=humidity_change_pct,
    )
    return MarketResearchBaseballLateInningWindCarryDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        event_slug=observation.event_slug,
        market_type=observation.market_type,
        row_status=_row_status_from_values(
            reason_codes,
            config=config,
            wind_carry_shift_mph=wind_carry_shift_mph,
            gust_carry_shift_mph=gust_carry_shift_mph,
        ),
        current_inning=observation.current_inning,
        scheduled_start_at=observation.scheduled_start_at,
        observed_at=observation.observed_at,
        prior_observed_at=observation.prior_observed_at,
        input_age_seconds=input_age_seconds,
        prior_wind_direction=observation.prior_wind_direction,
        current_wind_direction=observation.current_wind_direction,
        prior_sustained_wind_mph=observation.prior_sustained_wind_mph,
        current_sustained_wind_mph=observation.current_sustained_wind_mph,
        prior_gust_wind_mph=observation.prior_gust_wind_mph,
        current_gust_wind_mph=observation.current_gust_wind_mph,
        wind_carry_shift_mph=wind_carry_shift_mph,
        gust_carry_shift_mph=gust_carry_shift_mph,
        prior_temperature_f=observation.prior_temperature_f,
        current_temperature_f=observation.current_temperature_f,
        temperature_increase_f=temperature_increase_f,
        prior_humidity_pct=observation.prior_humidity_pct,
        current_humidity_pct=observation.current_humidity_pct,
        humidity_change_pct=humidity_change_pct,
        roof_status=observation.roof_status,
        roof_status_confirmed=observation.roof_status_confirmed,
        source_ref_count=_count_decimal(len(observation.source_refs)),
        redacted_source_refs=observation.source_refs,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: MarketResearchBaseballLateInningWindCarryObservation,
    *,
    config: MarketResearchBaseballLateInningWindCarryDigestConfig,
    input_age_seconds: Decimal,
    wind_carry_shift_mph: Decimal,
    gust_carry_shift_mph: Decimal,
    temperature_increase_f: Decimal,
    humidity_change_pct: Decimal,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if input_age_seconds > config.max_input_age_seconds:
        reasons.add(STALE_INPUT_REASON)
    late_inning = observation.current_inning >= config.min_late_inning
    if late_inning:
        if wind_carry_shift_mph >= config.watch_wind_carry_shift_mph:
            reasons.add(WIND_CARRY_SHIFT_REASON)
        if gust_carry_shift_mph >= config.watch_gust_carry_shift_mph:
            reasons.add(GUST_CARRY_SHIFT_REASON)
        if temperature_increase_f >= config.min_temperature_increase_f:
            reasons.add(TEMPERATURE_BOOST_REASON)
        if humidity_change_pct >= config.min_humidity_change_pct:
            reasons.add(HUMIDITY_CHANGE_REASON)
        if observation.roof_status == "open" and _has_carry_weather_reason(reasons):
            reasons.add(OPEN_ROOF_REASON)
        if _has_carry_weather_reason(reasons):
            if observation.market_type == "game_total":
                reasons.add(TOTALS_MARKET_REASON)
            if observation.market_type == "home_run":
                reasons.add(HOME_RUN_MARKET_REASON)
    return _ranked_row_reason_codes(reasons)


def _ranked_row_reason_codes(reason_codes: set[str]) -> tuple[str, ...]:
    if not reason_codes:
        return (CLEAR_REASON,)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODES
        if reason_code in reason_codes and reason_code != CLEAR_REASON
    )


def _has_carry_weather_reason(reason_codes: set[str]) -> bool:
    return bool(
        reason_codes
        & {
            WIND_CARRY_SHIFT_REASON,
            GUST_CARRY_SHIFT_REASON,
            TEMPERATURE_BOOST_REASON,
            HUMIDITY_CHANGE_REASON,
        },
    )


def _report_reason_codes(
    rows: tuple[MarketResearchBaseballLateInningWindCarryDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    report_reasons: set[str] = set()
    for row in rows:
        report_reasons.update(code for code in row.reason_codes if code != CLEAR_REASON)
    if not report_reasons:
        return (DIGEST_CLEAR_REASON,)
    return tuple(reason for reason in REPORT_REASON_CODES if reason in report_reasons)


def _row_status_from_values(
    reason_codes: tuple[str, ...],
    *,
    config: MarketResearchBaseballLateInningWindCarryDigestConfig,
    wind_carry_shift_mph: Decimal,
    gust_carry_shift_mph: Decimal,
) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if (
        STALE_INPUT_REASON in reason_codes
        or wind_carry_shift_mph >= config.blocked_wind_carry_shift_mph
        or gust_carry_shift_mph >= config.blocked_gust_carry_shift_mph
    ):
        return "blocked"
    return "watch"


def _digest_status(
    rows: tuple[MarketResearchBaseballLateInningWindCarryDigestRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_baseball_late_inning_wind_carry_screening"
    if status == "watch":
        return "monitor_report_only_baseball_late_inning_wind_carry_screening"
    return "block_report_only_baseball_late_inning_wind_carry_screening"


def _risk_score(
    status: str,
    rows: tuple[MarketResearchBaseballLateInningWindCarryDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    if status == "blocked":
        return ONE
    if status == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchBaseballLateInningWindCarryDigestRow, ...],
) -> tuple[MarketResearchBaseballLateInningWindCarryReasonCodeCount, ...]:
    if reason_codes == (DIGEST_EMPTY_REASON,):
        return (
            MarketResearchBaseballLateInningWindCarryReasonCodeCount(
                reason_code=DIGEST_EMPTY_REASON,
                market_count=ZERO,
            ),
        )
    return tuple(
        MarketResearchBaseballLateInningWindCarryReasonCodeCount(
            reason_code=reason_code,
            market_count=_reason_count(rows, reason_code),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[MarketResearchBaseballLateInningWindCarryObservation],
    *,
    generated_at: datetime,
) -> tuple[MarketResearchBaseballLateInningWindCarryObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain "
            "MarketResearchBaseballLateInningWindCarryObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not MarketResearchBaseballLateInningWindCarryObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchBaseballLateInningWindCarryObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketResearchBaseballLateInningWindCarryDigestRow],
) -> tuple[MarketResearchBaseballLateInningWindCarryDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain MarketResearchBaseballLateInningWindCarryDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchBaseballLateInningWindCarryDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBaseballLateInningWindCarryDigestRow",
            )
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[MarketResearchBaseballLateInningWindCarryReasonCodeCount],
) -> tuple[MarketResearchBaseballLateInningWindCarryReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not MarketResearchBaseballLateInningWindCarryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballLateInningWindCarryReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in allowed if reason in normalized) != normalized:
        raise ValueError(f"{field_name} must be deterministic")
    if allowed is ROW_REASON_CODES and CLEAR_REASON in normalized and len(normalized) != 1:
        raise ValueError(f"{field_name} must match row status")
    if allowed is REPORT_REASON_CODES:
        if DIGEST_EMPTY_REASON in normalized and len(normalized) != 1:
            raise ValueError(f"{field_name} must match report status")
        if DIGEST_CLEAR_REASON in normalized and len(normalized) != 1:
            raise ValueError(f"{field_name} must match report status")
    return normalized


def _normalize_source_refs(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    return tuple(sorted(_redact_source_ref(field_name, value) for value in values))


def _redact_source_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if _is_blank(value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    lowered = value.lower()
    if any(fragment in lowered for fragment in SOURCE_REF_REDACTION_FRAGMENTS):
        return REDACTED_SOURCE_REF_VALUE
    if value == REDACTED_SOURCE_REF_VALUE:
        return value
    _require_canonical_string(field_name, value)
    return value


def _row_sort_key(
    row: MarketResearchBaseballLateInningWindCarryDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.row_status],
        -row.wind_carry_shift_mph,
        -row.gust_carry_shift_mph,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[MarketResearchBaseballLateInningWindCarryDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.row_status == status))


def _reason_count(
    rows: tuple[MarketResearchBaseballLateInningWindCarryDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _late_inning_risk_count(
    rows: tuple[MarketResearchBaseballLateInningWindCarryDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if any(
                reason_code
                not in (
                    CLEAR_REASON,
                    STALE_INPUT_REASON,
                )
                for reason_code in row.reason_codes
            )
        ),
    )


def _max_row_decimal(
    rows: tuple[MarketResearchBaseballLateInningWindCarryDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _require_nonnegative_decimal(
        "input_age_seconds",
        whole_seconds + fractional_seconds,
    )


def _carry_shift(
    *,
    prior_direction: str,
    current_direction: str,
    prior_value: Decimal,
    current_value: Decimal,
) -> Decimal:
    return _quantize_decimal(
        _carry_component(current_direction, current_value)
        - _carry_component(prior_direction, prior_value),
    )


def _carry_component(direction: str, value: Decimal) -> Decimal:
    if direction == "outbound":
        return value
    if direction == "inbound":
        return -value
    return ZERO


def _validate_observation(
    observation: MarketResearchBaseballLateInningWindCarryObservation,
) -> None:
    if observation.prior_observed_at > observation.observed_at:
        raise ValueError("prior_observed_at must not exceed observed_at")
    if observation.observed_at < observation.scheduled_start_at:
        raise ValueError("observed_at must be at or after scheduled_start_at")
    if observation.prior_gust_wind_mph < observation.prior_sustained_wind_mph:
        raise ValueError("prior_gust_wind_mph must be at least prior_sustained_wind_mph")
    if observation.current_gust_wind_mph < observation.current_sustained_wind_mph:
        raise ValueError(
            "current_gust_wind_mph must be at least current_sustained_wind_mph",
        )


def _validate_row(row: MarketResearchBaseballLateInningWindCarryDigestRow) -> None:
    expected_wind_carry_shift = _carry_shift(
        prior_direction=row.prior_wind_direction,
        current_direction=row.current_wind_direction,
        prior_value=row.prior_sustained_wind_mph,
        current_value=row.current_sustained_wind_mph,
    )
    if row.wind_carry_shift_mph != expected_wind_carry_shift:
        raise ValueError("wind_carry_shift_mph must match wind direction and speed inputs")
    expected_gust_carry_shift = _carry_shift(
        prior_direction=row.prior_wind_direction,
        current_direction=row.current_wind_direction,
        prior_value=row.prior_gust_wind_mph,
        current_value=row.current_gust_wind_mph,
    )
    if row.gust_carry_shift_mph != expected_gust_carry_shift:
        raise ValueError("gust_carry_shift_mph must match wind direction and gust inputs")
    if row.temperature_increase_f != _quantize_decimal(
        row.current_temperature_f - row.prior_temperature_f,
    ):
        raise ValueError("temperature_increase_f must match temperature inputs")
    if row.humidity_change_pct != _quantize_decimal(
        abs(row.current_humidity_pct - row.prior_humidity_pct),
    ):
        raise ValueError("humidity_change_pct must match humidity inputs")
    if row.source_ref_count != _count_decimal(len(row.redacted_source_refs)):
        raise ValueError("source_ref_count must match redacted_source_refs")
    if row.prior_observed_at > row.observed_at:
        raise ValueError("prior_observed_at must not exceed observed_at")
    if row.observed_at < row.scheduled_start_at:
        raise ValueError("observed_at must be at or after scheduled_start_at")
    if row.prior_gust_wind_mph < row.prior_sustained_wind_mph:
        raise ValueError("prior_gust_wind_mph must be at least prior_sustained_wind_mph")
    if row.current_gust_wind_mph < row.current_sustained_wind_mph:
        raise ValueError(
            "current_gust_wind_mph must be at least current_sustained_wind_mph",
        )
    _validate_row_reason_state(row)


def _validate_row_reason_state(
    row: MarketResearchBaseballLateInningWindCarryDigestRow,
) -> None:
    if row.row_status == "pass":
        if row.reason_codes != (CLEAR_REASON,):
            raise ValueError("reason_codes must match row status")
        return
    if CLEAR_REASON in row.reason_codes:
        raise ValueError("reason_codes must match row status")
    if STALE_INPUT_REASON in row.reason_codes and row.row_status != "blocked":
        raise ValueError("reason_codes must match row status")
    if row.market_type == "game_total":
        if _has_row_carry_weather_reason(row) != (TOTALS_MARKET_REASON in row.reason_codes):
            raise ValueError("reason_codes must match market type state")
        if HOME_RUN_MARKET_REASON in row.reason_codes:
            raise ValueError("reason_codes must match market type state")
    if row.market_type == "home_run":
        if _has_row_carry_weather_reason(row) != (HOME_RUN_MARKET_REASON in row.reason_codes):
            raise ValueError("reason_codes must match market type state")
        if TOTALS_MARKET_REASON in row.reason_codes:
            raise ValueError("reason_codes must match market type state")
    if (row.roof_status == "open" and _has_row_carry_weather_reason(row)) != (
        OPEN_ROOF_REASON in row.reason_codes
    ):
        raise ValueError("reason_codes must match roof state")


def _has_row_carry_weather_reason(
    row: MarketResearchBaseballLateInningWindCarryDigestRow,
) -> bool:
    return any(
        reason_code in row.reason_codes
        for reason_code in (
            WIND_CARRY_SHIFT_REASON,
            GUST_CARRY_SHIFT_REASON,
            TEMPERATURE_BOOST_REASON,
            HUMIDITY_CHANGE_REASON,
        )
    )


def _validate_report(report: MarketResearchBaseballLateInningWindCarryDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.stale_input_count != _reason_count(report.rows, STALE_INPUT_REASON):
        raise ValueError("stale_input_count must match rows")
    if report.late_inning_risk_count != _late_inning_risk_count(report.rows):
        raise ValueError("late_inning_risk_count must match rows")
    if report.wind_carry_shift_count != _reason_count(report.rows, WIND_CARRY_SHIFT_REASON):
        raise ValueError("wind_carry_shift_count must match rows")
    if report.gust_carry_shift_count != _reason_count(report.rows, GUST_CARRY_SHIFT_REASON):
        raise ValueError("gust_carry_shift_count must match rows")
    if report.temperature_shift_count != _reason_count(
        report.rows,
        TEMPERATURE_BOOST_REASON,
    ):
        raise ValueError("temperature_shift_count must match rows")
    if report.humidity_shift_count != _reason_count(report.rows, HUMIDITY_CHANGE_REASON):
        raise ValueError("humidity_shift_count must match rows")
    if report.open_roof_count != _reason_count(report.rows, OPEN_ROOF_REASON):
        raise ValueError("open_roof_count must match rows")
    if report.totals_market_count != _reason_count(report.rows, TOTALS_MARKET_REASON):
        raise ValueError("totals_market_count must match rows")
    if report.home_run_market_count != _reason_count(report.rows, HOME_RUN_MARKET_REASON):
        raise ValueError("home_run_market_count must match rows")
    if report.max_input_age_seconds != _max_row_decimal(report.rows, "input_age_seconds"):
        raise ValueError("max_input_age_seconds must match rows")
    if report.max_wind_carry_shift_mph != _max_row_decimal(
        report.rows,
        "wind_carry_shift_mph",
    ):
        raise ValueError("max_wind_carry_shift_mph must match rows")
    if report.max_gust_carry_shift_mph != _max_row_decimal(
        report.rows,
        "gust_carry_shift_mph",
    ):
        raise ValueError("max_gust_carry_shift_mph must match rows")
    if report.max_temperature_increase_f != _max_row_decimal(
        report.rows,
        "temperature_increase_f",
    ):
        raise ValueError("max_temperature_increase_f must match rows")
    if report.max_humidity_change_pct != _max_row_decimal(
        report.rows,
        "humidity_change_pct",
    ):
        raise ValueError("max_humidity_change_pct must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.carry_risk_score != _risk_score(report.digest_status, report.rows):
        raise ValueError("carry_risk_score must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_percentage(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE_HUNDRED:
        raise ValueError(f"{field_name} must be between zero and one hundred")
    return decimal_value


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


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("decimal value must fit precision") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_public_string(field_name: str, value: object) -> None:
    text = _require_canonical_string(field_name, value)
    lowered = text.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be safe public text")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or CANONICAL_TEXT_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    try:
        require_paper_only_flags(field_name, value)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _is_blank(value: object) -> bool:
    return type(value) is not str or not value.strip()


__all__ = (
    "CLEAR_REASON",
    "DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_INNING_WIND_CARRY_DIGEST_CONFIG_VERSION",
    "DIGEST_CLEAR_REASON",
    "DIGEST_EMPTY_REASON",
    "GUST_CARRY_SHIFT_REASON",
    "HOME_RUN_MARKET_REASON",
    "HUMIDITY_CHANGE_REASON",
    "MarketResearchBaseballLateInningWindCarryDigestConfig",
    "MarketResearchBaseballLateInningWindCarryDigestReport",
    "MarketResearchBaseballLateInningWindCarryDigestRow",
    "MarketResearchBaseballLateInningWindCarryObservation",
    "MarketResearchBaseballLateInningWindCarryReasonCodeCount",
    "OPEN_ROOF_REASON",
    "REDACTED_SOURCE_REF_VALUE",
    "STALE_INPUT_REASON",
    "TEMPERATURE_BOOST_REASON",
    "TOTALS_MARKET_REASON",
    "WIND_CARRY_SHIFT_REASON",
    "build_market_research_baseball_late_inning_wind_carry_digest",
    "market_research_baseball_late_inning_wind_carry_digest_payload",
)

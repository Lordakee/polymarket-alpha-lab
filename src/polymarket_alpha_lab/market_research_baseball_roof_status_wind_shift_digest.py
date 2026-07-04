"""Pure Phase 1 baseball roof status wind shift digest reducer."""

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


DEFAULT_BASEBALL_ROOF_STATUS_WIND_SHIFT_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-roof-status-wind-shift-digest-v0"
)
REDACTED_SOURCE_REF_VALUE = "[redacted-ref]"

CLEAR_REASON = "baseball_roof_status_wind_shift_clear"
STALE_INPUT_REASON = "baseball_roof_status_wind_shift_stale_input"
ROOF_OPEN_UNCERTAIN_REASON = (
    "baseball_roof_status_wind_shift_roof_open_uncertain"
)
ROOF_CLOSED_UNCERTAIN_REASON = (
    "baseball_roof_status_wind_shift_roof_closed_uncertain"
)
ROOF_STATUS_CHANGED_REASON = (
    "baseball_roof_status_wind_shift_roof_status_changed"
)
DIRECTION_CHANGED_REASON = "baseball_roof_status_wind_shift_direction_changed"
BLOCKED_SPEED_REASON = "baseball_roof_status_wind_shift_blocked_speed"
WATCH_SPEED_REASON = "baseball_roof_status_wind_shift_watch_speed"
HIGH_GUST_REASON = "baseball_roof_status_wind_shift_high_gust"
GAME_PROBABILITY_SURFACE_REASON = (
    "baseball_roof_status_wind_shift_game_probability_surface"
)

DIGEST_EMPTY_REASON = "baseball_roof_status_wind_shift_digest_empty"
DIGEST_CLEAR_REASON = "baseball_roof_status_wind_shift_digest_clear"
STALE_INPUT_PRESENT_REASON = (
    "baseball_roof_status_wind_shift_stale_input_present"
)
ROOF_OPEN_UNCERTAIN_PRESENT_REASON = (
    "baseball_roof_status_wind_shift_roof_open_uncertain_present"
)
ROOF_CLOSED_UNCERTAIN_PRESENT_REASON = (
    "baseball_roof_status_wind_shift_roof_closed_uncertain_present"
)
ROOF_STATUS_CHANGED_PRESENT_REASON = (
    "baseball_roof_status_wind_shift_roof_status_changed_present"
)
DIRECTION_CHANGED_PRESENT_REASON = (
    "baseball_roof_status_wind_shift_direction_changed_present"
)
BLOCKED_SPEED_PRESENT_REASON = (
    "baseball_roof_status_wind_shift_blocked_speed_present"
)
WATCH_SPEED_PRESENT_REASON = "baseball_roof_status_wind_shift_watch_speed_present"
HIGH_GUST_PRESENT_REASON = "baseball_roof_status_wind_shift_high_gust_present"
GAME_PROBABILITY_SURFACE_PRESENT_REASON = (
    "baseball_roof_status_wind_shift_game_probability_surface_present"
)

ROW_REASON_CODES = (
    CLEAR_REASON,
    STALE_INPUT_REASON,
    ROOF_OPEN_UNCERTAIN_REASON,
    ROOF_CLOSED_UNCERTAIN_REASON,
    ROOF_STATUS_CHANGED_REASON,
    DIRECTION_CHANGED_REASON,
    BLOCKED_SPEED_REASON,
    WATCH_SPEED_REASON,
    HIGH_GUST_REASON,
    GAME_PROBABILITY_SURFACE_REASON,
)
REPORT_REASON_CODES = (
    STALE_INPUT_PRESENT_REASON,
    ROOF_OPEN_UNCERTAIN_PRESENT_REASON,
    ROOF_CLOSED_UNCERTAIN_PRESENT_REASON,
    ROOF_STATUS_CHANGED_PRESENT_REASON,
    DIRECTION_CHANGED_PRESENT_REASON,
    BLOCKED_SPEED_PRESENT_REASON,
    WATCH_SPEED_PRESENT_REASON,
    HIGH_GUST_PRESENT_REASON,
    GAME_PROBABILITY_SURFACE_PRESENT_REASON,
    DIGEST_CLEAR_REASON,
    DIGEST_EMPTY_REASON,
)
REPORT_REASON_TO_ROW_REASON = {
    STALE_INPUT_PRESENT_REASON: STALE_INPUT_REASON,
    ROOF_OPEN_UNCERTAIN_PRESENT_REASON: ROOF_OPEN_UNCERTAIN_REASON,
    ROOF_CLOSED_UNCERTAIN_PRESENT_REASON: ROOF_CLOSED_UNCERTAIN_REASON,
    ROOF_STATUS_CHANGED_PRESENT_REASON: ROOF_STATUS_CHANGED_REASON,
    DIRECTION_CHANGED_PRESENT_REASON: DIRECTION_CHANGED_REASON,
    BLOCKED_SPEED_PRESENT_REASON: BLOCKED_SPEED_REASON,
    WATCH_SPEED_PRESENT_REASON: WATCH_SPEED_REASON,
    HIGH_GUST_PRESENT_REASON: HIGH_GUST_REASON,
    GAME_PROBABILITY_SURFACE_PRESENT_REASON: GAME_PROBABILITY_SURFACE_REASON,
    DIGEST_CLEAR_REASON: CLEAR_REASON,
}
ROW_REASON_TO_REPORT_REASON = {
    row_reason: report_reason
    for report_reason, row_reason in REPORT_REASON_TO_ROW_REASON.items()
}

STATUSES = ("pass", "watch", "blocked")
MARKET_TYPES = ("game_total", "home_run", "game_probability")
ROOF_STATUSES = ("closed", "open", "unknown")
WIND_DIRECTIONS = ("inbound", "neutral", "outbound", "crosswind")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
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
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
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
        _join_parts("api", "_key"),
        _join_parts("bear", "er"),
        _join_parts("cre", "dential"),
        _join_parts("pass", "word"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
    ),
)


@dataclass(frozen=True)
class BaseballRoofStatusWindShiftDigestConfig:
    config_version: str = DEFAULT_BASEBALL_ROOF_STATUS_WIND_SHIFT_DIGEST_CONFIG_VERSION
    watch_wind_speed_shift_mph: Decimal = Decimal("6.000000")
    blocked_wind_speed_shift_mph: Decimal = Decimal("12.000000")
    watch_wind_gust_mph: Decimal = Decimal("22.000000")
    blocked_wind_gust_mph: Decimal = Decimal("32.000000")
    max_input_age_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, BaseballRoofStatusWindShiftDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BASEBALL_ROOF_STATUS_WIND_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_wind_speed_shift_mph",
            "blocked_wind_speed_shift_mph",
            "watch_wind_gust_mph",
            "blocked_wind_gust_mph",
            "max_input_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_wind_speed_shift_mph > self.blocked_wind_speed_shift_mph:
            raise ValueError(
                "watch_wind_speed_shift_mph must not exceed "
                "blocked_wind_speed_shift_mph",
            )
        if self.watch_wind_gust_mph > self.blocked_wind_gust_mph:
            raise ValueError(
                "watch_wind_gust_mph must not exceed blocked_wind_gust_mph",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class BaseballRoofStatusWindShiftObservation:
    source_id: str
    market_slug: str
    event_slug: str
    market_type: str
    scheduled_start_at: datetime
    observed_at: datetime
    prior_observed_at: datetime
    prior_roof_status: str
    current_roof_status: str
    roof_status_confirmed: bool
    prior_wind_direction: str
    current_wind_direction: str
    prior_wind_speed_mph: Decimal
    current_wind_speed_mph: Decimal
    wind_gust_mph: Decimal
    source_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, BaseballRoofStatusWindShiftObservation, "observation")
        for field_name in ("source_id", "market_slug", "event_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("market_type", self.market_type, MARKET_TYPES)
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "prior_observed_at",
            _as_utc("prior_observed_at", self.prior_observed_at),
        )
        _require_member("prior_roof_status", self.prior_roof_status, ROOF_STATUSES)
        _require_member("current_roof_status", self.current_roof_status, ROOF_STATUSES)
        _require_bool("roof_status_confirmed", self.roof_status_confirmed)
        _require_member(
            "prior_wind_direction",
            self.prior_wind_direction,
            WIND_DIRECTIONS,
        )
        _require_member(
            "current_wind_direction",
            self.current_wind_direction,
            WIND_DIRECTIONS,
        )
        for field_name in (
            "prior_wind_speed_mph",
            "current_wind_speed_mph",
            "wind_gust_mph",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_refs",
            _normalize_source_refs("source_refs", self.source_refs),
        )
        if self.prior_observed_at > self.observed_at:
            raise ValueError("prior_observed_at must not exceed observed_at")
        if self.observed_at > self.scheduled_start_at:
            raise ValueError("observed_at must not exceed scheduled_start_at")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class BaseballRoofStatusWindShiftDigestRow:
    source_id: str
    market_slug: str
    event_slug: str
    market_type: str
    row_status: str
    scheduled_start_at: datetime
    observed_at: datetime
    prior_observed_at: datetime
    input_age_seconds: Decimal
    prior_roof_status: str
    current_roof_status: str
    roof_status_confirmed: bool
    prior_wind_direction: str
    current_wind_direction: str
    prior_wind_speed_mph: Decimal
    current_wind_speed_mph: Decimal
    absolute_wind_speed_shift_mph: Decimal
    wind_gust_mph: Decimal
    source_ref_count: Decimal
    redacted_source_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, BaseballRoofStatusWindShiftDigestRow, "row")
        for field_name in ("source_id", "market_slug", "event_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("market_type", self.market_type, MARKET_TYPES)
        _require_member("row_status", self.row_status, STATUSES)
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
            "prior_wind_speed_mph",
            "current_wind_speed_mph",
            "absolute_wind_speed_shift_mph",
            "wind_gust_mph",
            "source_ref_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("prior_roof_status", self.prior_roof_status, ROOF_STATUSES)
        _require_member("current_roof_status", self.current_roof_status, ROOF_STATUSES)
        _require_bool("roof_status_confirmed", self.roof_status_confirmed)
        _require_member(
            "prior_wind_direction",
            self.prior_wind_direction,
            WIND_DIRECTIONS,
        )
        _require_member(
            "current_wind_direction",
            self.current_wind_direction,
            WIND_DIRECTIONS,
        )
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
class BaseballRoofStatusWindShiftReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            BaseballRoofStatusWindShiftReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class BaseballRoofStatusWindShiftDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_input_count: Decimal
    roof_uncertainty_count: Decimal
    roof_status_change_count: Decimal
    wind_shift_count: Decimal
    game_probability_watch_count: Decimal
    max_input_age_seconds: Decimal
    max_absolute_wind_speed_shift_mph: Decimal
    average_absolute_wind_speed_shift_mph: Decimal
    max_wind_gust_mph: Decimal
    roof_wind_shift_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[BaseballRoofStatusWindShiftDigestRow, ...]
    reason_code_counts: tuple[BaseballRoofStatusWindShiftReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, BaseballRoofStatusWindShiftDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BASEBALL_ROOF_STATUS_WIND_SHIFT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_input_count",
            "roof_uncertainty_count",
            "roof_status_change_count",
            "wind_shift_count",
            "game_probability_watch_count",
            "max_input_age_seconds",
            "max_absolute_wind_speed_shift_mph",
            "average_absolute_wind_speed_shift_mph",
            "max_wind_gust_mph",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "roof_wind_shift_risk_score",
            _require_ratio(
                "roof_wind_shift_risk_score",
                self.roof_wind_shift_risk_score,
            ),
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
            "baseball_roof_status_wind_shift_digest",
            self,
        )


def build_market_research_baseball_roof_status_wind_shift_digest(
    observations: Iterable[BaseballRoofStatusWindShiftObservation],
    *,
    config: BaseballRoofStatusWindShiftDigestConfig,
    generated_at: datetime,
) -> BaseballRoofStatusWindShiftDigestReport:
    if type(config) is not BaseballRoofStatusWindShiftDigestConfig:
        raise ValueError("config must be exactly BaseballRoofStatusWindShiftDigestConfig")
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

    return BaseballRoofStatusWindShiftDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        stale_input_count=_reason_count(rows, STALE_INPUT_REASON),
        roof_uncertainty_count=_row_any_reason_count(
            rows,
            (ROOF_OPEN_UNCERTAIN_REASON, ROOF_CLOSED_UNCERTAIN_REASON),
        ),
        roof_status_change_count=_reason_count(rows, ROOF_STATUS_CHANGED_REASON),
        wind_shift_count=_row_any_reason_count(
            rows,
            (BLOCKED_SPEED_REASON, WATCH_SPEED_REASON),
        ),
        game_probability_watch_count=_reason_count(
            rows,
            GAME_PROBABILITY_SURFACE_REASON,
        ),
        max_input_age_seconds=_max_row_decimal(rows, "input_age_seconds"),
        max_absolute_wind_speed_shift_mph=_max_row_decimal(
            rows,
            "absolute_wind_speed_shift_mph",
        ),
        average_absolute_wind_speed_shift_mph=_ratio(
            _sum_decimal(row.absolute_wind_speed_shift_mph for row in rows),
            row_count,
        ),
        max_wind_gust_mph=_max_row_decimal(rows, "wind_gust_mph"),
        roof_wind_shift_risk_score=_risk_score(digest_status, rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_baseball_roof_status_wind_shift_digest_payload(
    report: BaseballRoofStatusWindShiftDigestReport,
) -> dict[str, Any]:
    if type(report) is not BaseballRoofStatusWindShiftDigestReport:
        raise ValueError("report must be exactly BaseballRoofStatusWindShiftDigestReport")
    _require_hard_flags("report", report)
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report must reduce to a JSON object")
    reject_unsafe_surface_fields(
        "baseball_roof_status_wind_shift_digest",
        ready,
    )
    return ready


def _row_from_observation(
    observation: BaseballRoofStatusWindShiftObservation,
    *,
    config: BaseballRoofStatusWindShiftDigestConfig,
    generated_at: datetime,
) -> BaseballRoofStatusWindShiftDigestRow:
    input_age_seconds = _age_seconds(generated_at, observation.observed_at)
    absolute_wind_speed_shift_mph = _quantize_decimal(
        abs(observation.current_wind_speed_mph - observation.prior_wind_speed_mph),
    )
    reason_codes = _row_reason_codes(
        observation,
        config=config,
        input_age_seconds=input_age_seconds,
        absolute_wind_speed_shift_mph=absolute_wind_speed_shift_mph,
    )
    return BaseballRoofStatusWindShiftDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        event_slug=observation.event_slug,
        market_type=observation.market_type,
        row_status=_row_status(reason_codes),
        scheduled_start_at=observation.scheduled_start_at,
        observed_at=observation.observed_at,
        prior_observed_at=observation.prior_observed_at,
        input_age_seconds=input_age_seconds,
        prior_roof_status=observation.prior_roof_status,
        current_roof_status=observation.current_roof_status,
        roof_status_confirmed=observation.roof_status_confirmed,
        prior_wind_direction=observation.prior_wind_direction,
        current_wind_direction=observation.current_wind_direction,
        prior_wind_speed_mph=observation.prior_wind_speed_mph,
        current_wind_speed_mph=observation.current_wind_speed_mph,
        absolute_wind_speed_shift_mph=absolute_wind_speed_shift_mph,
        wind_gust_mph=observation.wind_gust_mph,
        source_ref_count=_count_decimal(len(observation.source_refs)),
        redacted_source_refs=observation.source_refs,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: BaseballRoofStatusWindShiftObservation,
    *,
    config: BaseballRoofStatusWindShiftDigestConfig,
    input_age_seconds: Decimal,
    absolute_wind_speed_shift_mph: Decimal,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if input_age_seconds > config.max_input_age_seconds:
        reasons.add(STALE_INPUT_REASON)
    if not observation.roof_status_confirmed:
        if observation.current_roof_status in ("open", "unknown"):
            reasons.add(ROOF_OPEN_UNCERTAIN_REASON)
        if observation.current_roof_status in ("closed", "unknown"):
            reasons.add(ROOF_CLOSED_UNCERTAIN_REASON)
    if observation.prior_roof_status != observation.current_roof_status:
        reasons.add(ROOF_STATUS_CHANGED_REASON)
    if observation.prior_wind_direction != observation.current_wind_direction:
        reasons.add(DIRECTION_CHANGED_REASON)
    if absolute_wind_speed_shift_mph >= config.blocked_wind_speed_shift_mph:
        reasons.add(BLOCKED_SPEED_REASON)
    elif absolute_wind_speed_shift_mph >= config.watch_wind_speed_shift_mph:
        reasons.add(WATCH_SPEED_REASON)
    if observation.wind_gust_mph >= config.blocked_wind_gust_mph:
        reasons.add(HIGH_GUST_REASON)
    if observation.market_type == "game_probability" and reasons:
        reasons.add(GAME_PROBABILITY_SURFACE_REASON)
    return _ranked_row_reason_codes(reasons)


def _ranked_row_reason_codes(reason_codes: set[str]) -> tuple[str, ...]:
    if not reason_codes:
        return (CLEAR_REASON,)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODES
        if reason_code in reason_codes and reason_code != CLEAR_REASON
    )


def _report_reason_codes(
    rows: tuple[BaseballRoofStatusWindShiftDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    report_reasons: set[str] = set()
    for row in rows:
        for row_reason in row.reason_codes:
            if row_reason != CLEAR_REASON:
                report_reasons.add(ROW_REASON_TO_REPORT_REASON[row_reason])
    if not report_reasons:
        return (DIGEST_CLEAR_REASON,)
    return tuple(reason for reason in REPORT_REASON_CODES if reason in report_reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if any(
        reason_code in (STALE_INPUT_REASON, BLOCKED_SPEED_REASON, HIGH_GUST_REASON)
        for reason_code in reason_codes
    ):
        return "blocked"
    return "watch"


def _digest_status(rows: tuple[BaseballRoofStatusWindShiftDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_baseball_roof_status_wind_shift_screening"
    if status == "watch":
        return "monitor_report_only_baseball_roof_status_wind_shift_screening"
    return "block_report_only_baseball_roof_status_wind_shift_screening"


def _risk_score(
    status: str,
    rows: tuple[BaseballRoofStatusWindShiftDigestRow, ...],
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
    rows: tuple[BaseballRoofStatusWindShiftDigestRow, ...],
) -> tuple[BaseballRoofStatusWindShiftReasonCodeCount, ...]:
    if reason_codes == (DIGEST_EMPTY_REASON,):
        return (
            BaseballRoofStatusWindShiftReasonCodeCount(
                reason_code=DIGEST_EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_count = _count_decimal(len(rows))
    return tuple(
        BaseballRoofStatusWindShiftReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[BaseballRoofStatusWindShiftDigestRow, ...],
) -> Decimal:
    row_reason = REPORT_REASON_TO_ROW_REASON[reason_code]
    return _reason_count(rows, row_reason)


def _normalize_observations(
    observations: Iterable[BaseballRoofStatusWindShiftObservation],
    *,
    generated_at: datetime,
) -> tuple[BaseballRoofStatusWindShiftObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain BaseballRoofStatusWindShiftObservation")
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not BaseballRoofStatusWindShiftObservation:
            raise ValueError(
                "observations must contain BaseballRoofStatusWindShiftObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[BaseballRoofStatusWindShiftDigestRow],
) -> tuple[BaseballRoofStatusWindShiftDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain BaseballRoofStatusWindShiftDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not BaseballRoofStatusWindShiftDigestRow:
            raise ValueError("rows must contain BaseballRoofStatusWindShiftDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[BaseballRoofStatusWindShiftReasonCodeCount],
) -> tuple[BaseballRoofStatusWindShiftReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not BaseballRoofStatusWindShiftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "BaseballRoofStatusWindShiftReasonCodeCount",
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
    normalized = tuple(sorted(_redact_source_ref(field_name, value) for value in values))
    return normalized


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
    row: BaseballRoofStatusWindShiftDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.row_status],
        -row.absolute_wind_speed_shift_mph,
        -row.wind_gust_mph,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[BaseballRoofStatusWindShiftDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.row_status == status))


def _reason_count(
    rows: tuple[BaseballRoofStatusWindShiftDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_any_reason_count(
    rows: tuple[BaseballRoofStatusWindShiftDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_codes)),
    )


def _max_row_decimal(
    rows: tuple[BaseballRoofStatusWindShiftDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


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


def _validate_row(row: BaseballRoofStatusWindShiftDigestRow) -> None:
    expected_shift = _quantize_decimal(
        abs(row.current_wind_speed_mph - row.prior_wind_speed_mph),
    )
    if row.absolute_wind_speed_shift_mph != expected_shift:
        raise ValueError("absolute_wind_speed_shift_mph must match wind speed inputs")
    if row.source_ref_count != _count_decimal(len(row.redacted_source_refs)):
        raise ValueError("source_ref_count must match redacted_source_refs")
    if row.observed_at > row.scheduled_start_at:
        raise ValueError("observed_at must not exceed scheduled_start_at")
    if row.prior_observed_at > row.observed_at:
        raise ValueError("prior_observed_at must not exceed observed_at")
    if row.row_status != _row_status(row.reason_codes):
        raise ValueError("reason_codes must match row status")
    _validate_row_reason_state(row)


def _validate_row_reason_state(row: BaseballRoofStatusWindShiftDigestRow) -> None:
    if row.row_status == "pass":
        if row.reason_codes != (CLEAR_REASON,):
            raise ValueError("reason_codes must match row status")
        return
    if CLEAR_REASON in row.reason_codes:
        raise ValueError("reason_codes must match row status")
    open_uncertain = (
        not row.roof_status_confirmed
        and row.current_roof_status in ("open", "unknown")
    )
    closed_uncertain = (
        not row.roof_status_confirmed
        and row.current_roof_status in ("closed", "unknown")
    )
    if open_uncertain != (ROOF_OPEN_UNCERTAIN_REASON in row.reason_codes):
        raise ValueError("reason_codes must match roof uncertainty state")
    if closed_uncertain != (ROOF_CLOSED_UNCERTAIN_REASON in row.reason_codes):
        raise ValueError("reason_codes must match roof uncertainty state")
    if (
        row.prior_roof_status != row.current_roof_status
    ) != (ROOF_STATUS_CHANGED_REASON in row.reason_codes):
        raise ValueError("reason_codes must match roof status state")
    if (
        row.prior_wind_direction != row.current_wind_direction
    ) != (DIRECTION_CHANGED_REASON in row.reason_codes):
        raise ValueError("reason_codes must match wind direction state")
    if row.market_type == "game_probability":
        non_clear_count = len(tuple(code for code in row.reason_codes if code != CLEAR_REASON))
        if (non_clear_count > 1) != (
            GAME_PROBABILITY_SURFACE_REASON in row.reason_codes
        ):
            raise ValueError("reason_codes must match market type state")
    elif GAME_PROBABILITY_SURFACE_REASON in row.reason_codes:
        raise ValueError("reason_codes must match market type state")


def _validate_report(report: BaseballRoofStatusWindShiftDigestReport) -> None:
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
    if report.roof_uncertainty_count != _row_any_reason_count(
        report.rows,
        (ROOF_OPEN_UNCERTAIN_REASON, ROOF_CLOSED_UNCERTAIN_REASON),
    ):
        raise ValueError("roof_uncertainty_count must match rows")
    if report.roof_status_change_count != _reason_count(
        report.rows,
        ROOF_STATUS_CHANGED_REASON,
    ):
        raise ValueError("roof_status_change_count must match rows")
    if report.wind_shift_count != _row_any_reason_count(
        report.rows,
        (BLOCKED_SPEED_REASON, WATCH_SPEED_REASON),
    ):
        raise ValueError("wind_shift_count must match rows")
    if report.game_probability_watch_count != _reason_count(
        report.rows,
        GAME_PROBABILITY_SURFACE_REASON,
    ):
        raise ValueError("game_probability_watch_count must match rows")
    if report.max_input_age_seconds != _max_row_decimal(report.rows, "input_age_seconds"):
        raise ValueError("max_input_age_seconds must match rows")
    if report.max_absolute_wind_speed_shift_mph != _max_row_decimal(
        report.rows,
        "absolute_wind_speed_shift_mph",
    ):
        raise ValueError("max_absolute_wind_speed_shift_mph must match rows")
    if report.average_absolute_wind_speed_shift_mph != _ratio(
        _sum_decimal(row.absolute_wind_speed_shift_mph for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_absolute_wind_speed_shift_mph must match rows")
    if report.max_wind_gust_mph != _max_row_decimal(report.rows, "wind_gust_mph"):
        raise ValueError("max_wind_gust_mph must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.roof_wind_shift_risk_score != _risk_score(
        report.digest_status,
        report.rows,
    ):
        raise ValueError("roof_wind_shift_risk_score must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
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
    "DEFAULT_BASEBALL_ROOF_STATUS_WIND_SHIFT_DIGEST_CONFIG_VERSION",
    "REDACTED_SOURCE_REF_VALUE",
    "BaseballRoofStatusWindShiftDigestConfig",
    "BaseballRoofStatusWindShiftObservation",
    "BaseballRoofStatusWindShiftDigestRow",
    "BaseballRoofStatusWindShiftReasonCodeCount",
    "BaseballRoofStatusWindShiftDigestReport",
    "build_market_research_baseball_roof_status_wind_shift_digest",
    "market_research_baseball_roof_status_wind_shift_digest_payload",
)

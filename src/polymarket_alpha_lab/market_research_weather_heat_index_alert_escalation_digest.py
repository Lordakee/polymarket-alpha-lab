"""Pure Phase 1 heat index alert escalation digest reducer."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_WEATHER_HEAT_INDEX_ALERT_ESCALATION_DIGEST_CONFIG_VERSION = (
    "market-research-weather-heat-index-alert-escalation-digest-v0"
)

REASON_CODES = (
    "market_research_weather_heat_index_alert_escalation_digest_no_inputs",
    "market_research_weather_heat_index_alert_escalation_digest_heat_index_block",
    "market_research_weather_heat_index_alert_escalation_digest_alert_level_warning",
    "market_research_weather_heat_index_alert_escalation_digest_heat_index_watch",
    "market_research_weather_heat_index_alert_escalation_digest_alert_level_watch",
    "market_research_weather_heat_index_alert_escalation_digest_rapid_heat_rise",
    "market_research_weather_heat_index_alert_escalation_digest_near_term_peak",
    "market_research_weather_heat_index_alert_escalation_digest_stale_snapshot",
    "market_research_weather_heat_index_alert_escalation_digest_thin_sources",
    "market_research_weather_heat_index_alert_escalation_digest_high_exposure",
    "market_research_weather_heat_index_alert_escalation_digest_probability_shift",
    "market_research_weather_heat_index_alert_escalation_digest_clear",
)
ROW_REASON_CODES = REASON_CODES[1:]
ESCALATION_STATUSES = ("blocked", "watch", "clear")
NEXT_STEPS = {
    "blocked": (
        "block_report_only_market_research_weather_heat_index_alert_escalation_digest"
    ),
    "watch": (
        "monitor_report_only_market_research_weather_heat_index_alert_escalation_digest"
    ),
    "clear": (
        "continue_report_only_market_research_weather_heat_index_alert_escalation_digest"
    ),
}
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "clear": Decimal("2.000000"),
}
ALERT_LEVELS = (
    "none",
    "heat_advisory",
    "excessive_heat_watch",
    "excessive_heat_warning",
)
ALERT_LEVEL_WATCH_VALUES = ("heat_advisory", "excessive_heat_watch")
ALERT_LEVEL_WARNING_VALUES = ("excessive_heat_warning",)
KEY_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789._-")

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
MICROSECONDS_PER_SECOND = Decimal("1000000")
PROBABILITY_SHIFT_THRESHOLD = Decimal("0.050000")


@dataclass(frozen=True)
class MarketResearchWeatherHeatIndexAlertEscalationDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_WEATHER_HEAT_INDEX_ALERT_ESCALATION_DIGEST_CONFIG_VERSION
    )
    fresh_snapshot_max_age_seconds: Decimal = Decimal("21600.000000")
    watch_heat_index_f: Decimal = Decimal("100.000000")
    block_heat_index_f: Decimal = Decimal("108.000000")
    rapid_heat_rise_f: Decimal = Decimal("8.000000")
    near_term_peak_hours: Decimal = Decimal("24.000000")
    high_exposure_population_millions: Decimal = Decimal("1.000000")
    min_public_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchWeatherHeatIndexAlertEscalationDigestConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_WEATHER_HEAT_INDEX_ALERT_ESCALATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "fresh_snapshot_max_age_seconds",
            _require_positive_decimal(
                "fresh_snapshot_max_age_seconds",
                self.fresh_snapshot_max_age_seconds,
            ),
        )
        for field_name in (
            "watch_heat_index_f",
            "block_heat_index_f",
            "rapid_heat_rise_f",
            "high_exposure_population_millions",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "near_term_peak_hours",
            _require_positive_decimal(
                "near_term_peak_hours",
                self.near_term_peak_hours,
            ),
        )
        object.__setattr__(
            self,
            "min_public_source_count",
            _require_whole_positive_decimal(
                "min_public_source_count",
                self.min_public_source_count,
            ),
        )
        if self.block_heat_index_f < self.watch_heat_index_f:
            raise ValueError("block_heat_index_f must be at least watch_heat_index_f")
        _require_hard_flags("heat index alert escalation config", self)


@dataclass(frozen=True)
class MarketResearchWeatherHeatIndexAlertEscalationInputRow:
    region_id: str
    market_slug: str
    condition_id: str
    source_id: str
    snapshot_at: datetime
    current_alert_level: str
    forecast_heat_index_f: Decimal
    prior_heat_index_f: Decimal
    forecast_hours_until_peak: Decimal
    exposed_population_millions: Decimal
    public_source_count: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchWeatherHeatIndexAlertEscalationInputRow,
            "input row",
        )
        for field_name in ("region_id", "market_slug", "condition_id", "source_id"):
            object.__setattr__(
                self,
                field_name,
                _require_key(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "snapshot_at",
            _as_utc("snapshot_at", self.snapshot_at),
        )
        object.__setattr__(
            self,
            "current_alert_level",
            _require_member(
                "current_alert_level",
                self.current_alert_level,
                ALERT_LEVELS,
            ),
        )
        for field_name in (
            "forecast_heat_index_f",
            "prior_heat_index_f",
            "forecast_hours_until_peak",
            "exposed_population_millions",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_source_count",
            _require_whole_nonnegative_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("heat index alert escalation input row", self)


@dataclass(frozen=True)
class MarketResearchWeatherHeatIndexAlertEscalationDigestRow:
    region_id: str
    market_slug: str
    condition_id: str
    source_id: str
    snapshot_at: datetime
    snapshot_age_seconds: Decimal
    current_alert_level: str
    forecast_heat_index_f: Decimal
    prior_heat_index_f: Decimal
    heat_index_rise_f: Decimal
    forecast_hours_until_peak: Decimal
    exposed_population_millions: Decimal
    public_source_count: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_change: Decimal
    escalation_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchWeatherHeatIndexAlertEscalationDigestRow,
            "digest row",
        )
        for field_name in ("region_id", "market_slug", "condition_id", "source_id"):
            object.__setattr__(
                self,
                field_name,
                _require_key(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "snapshot_at",
            _as_utc("snapshot_at", self.snapshot_at),
        )
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _require_nonnegative_decimal(
                "snapshot_age_seconds",
                self.snapshot_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "current_alert_level",
            _require_member(
                "current_alert_level",
                self.current_alert_level,
                ALERT_LEVELS,
            ),
        )
        for field_name in (
            "forecast_heat_index_f",
            "prior_heat_index_f",
            "forecast_hours_until_peak",
            "exposed_population_millions",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "heat_index_rise_f",
            _require_signed_decimal("heat_index_rise_f", self.heat_index_rise_f),
        )
        object.__setattr__(
            self,
            "public_source_count",
            _require_whole_nonnegative_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_change",
            _require_signed_ratio("probability_change", self.probability_change),
        )
        object.__setattr__(
            self,
            "escalation_status",
            _require_member(
                "escalation_status",
                self.escalation_status,
                ESCALATION_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("heat index alert escalation digest row", self)


@dataclass(frozen=True)
class MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount:
    reason_code: str
    count: Decimal
    region_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount,
            "reason code count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, REASON_CODES),
        )
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "region_ratio",
            _require_ratio("region_ratio", self.region_ratio),
        )
        _require_hard_flags("heat index alert escalation reason code count", self)


@dataclass(frozen=True)
class MarketResearchWeatherHeatIndexAlertEscalationDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    region_count: Decimal
    clear_region_count: Decimal
    watch_region_count: Decimal
    blocked_region_count: Decimal
    fresh_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    thin_source_count: Decimal
    active_alert_count: Decimal
    high_heat_index_count: Decimal
    rapid_heat_rise_count: Decimal
    near_term_peak_count: Decimal
    high_exposure_count: Decimal
    probability_shift_count: Decimal
    max_forecast_heat_index_f: Decimal
    max_heat_index_rise_f: Decimal
    min_forecast_hours_until_peak: Decimal
    max_exposed_population_millions: Decimal
    max_snapshot_age_seconds: Decimal
    average_public_source_count: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[MarketResearchWeatherHeatIndexAlertEscalationDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchWeatherHeatIndexAlertEscalationDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_WEATHER_HEAT_INDEX_ALERT_ESCALATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "digest_status",
            _require_member("digest_status", self.digest_status, ESCALATION_STATUSES),
        )
        object.__setattr__(self, "next_step", _require_text("next_step", self.next_step))
        for field_name in (
            "region_count",
            "clear_region_count",
            "watch_region_count",
            "blocked_region_count",
            "fresh_snapshot_count",
            "stale_snapshot_count",
            "thin_source_count",
            "active_alert_count",
            "high_heat_index_count",
            "rapid_heat_rise_count",
            "near_term_peak_count",
            "high_exposure_count",
            "probability_shift_count",
            "max_forecast_heat_index_f",
            "max_heat_index_rise_f",
            "min_forecast_hours_until_peak",
            "max_exposed_population_millions",
            "max_snapshot_age_seconds",
            "average_public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("heat index alert escalation digest report", self)


def build_market_research_weather_heat_index_alert_escalation_digest(
    rows: Iterable[MarketResearchWeatherHeatIndexAlertEscalationInputRow],
    *,
    config: MarketResearchWeatherHeatIndexAlertEscalationDigestConfig,
    generated_at: datetime,
) -> MarketResearchWeatherHeatIndexAlertEscalationDigestReport:
    if type(config) is not MarketResearchWeatherHeatIndexAlertEscalationDigestConfig:
        raise ValueError(
            "config must be a MarketResearchWeatherHeatIndexAlertEscalationDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("heat index alert escalation config", config)
    input_rows = _normalize_inputs(rows)
    if not input_rows:
        return _empty_report(config=config, generated_at=generated_at_utc)

    digest_rows = tuple(
        sorted(
            (
                _row_from_input(input_row, config=config, generated_at=generated_at_utc)
                for input_row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    region_count = _count(len(digest_rows))
    reason_codes = _report_reason_codes(digest_rows)
    reason_code_counts = _reason_code_counts(digest_rows, reason_codes, region_count)
    digest_status = _report_status(digest_rows)
    return MarketResearchWeatherHeatIndexAlertEscalationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        region_count=region_count,
        clear_region_count=_row_count(
            digest_rows,
            lambda row: row.escalation_status == "clear",
        ),
        watch_region_count=_row_count(
            digest_rows,
            lambda row: row.escalation_status == "watch",
        ),
        blocked_region_count=_row_count(
            digest_rows,
            lambda row: row.escalation_status == "blocked",
        ),
        fresh_snapshot_count=_row_count(
            digest_rows,
            lambda row: not _has_reason(row, "stale_snapshot"),
        ),
        stale_snapshot_count=_row_count(
            digest_rows,
            lambda row: _has_reason(row, "stale_snapshot"),
        ),
        thin_source_count=_row_count(
            digest_rows,
            lambda row: _has_reason(row, "thin_sources"),
        ),
        active_alert_count=_row_count(
            digest_rows,
            lambda row: row.current_alert_level != "none",
        ),
        high_heat_index_count=_row_count(
            digest_rows,
            lambda row: _has_reason(row, "heat_index_block")
            or _has_reason(row, "heat_index_watch"),
        ),
        rapid_heat_rise_count=_row_count(
            digest_rows,
            lambda row: _has_reason(row, "rapid_heat_rise"),
        ),
        near_term_peak_count=_row_count(
            digest_rows,
            lambda row: _has_reason(row, "near_term_peak"),
        ),
        high_exposure_count=_row_count(
            digest_rows,
            lambda row: _has_reason(row, "high_exposure"),
        ),
        probability_shift_count=_row_count(
            digest_rows,
            lambda row: _has_reason(row, "probability_shift"),
        ),
        max_forecast_heat_index_f=max(
            (row.forecast_heat_index_f for row in digest_rows),
            default=ZERO,
        ),
        max_heat_index_rise_f=_max_nonnegative(
            row.heat_index_rise_f for row in digest_rows
        ),
        min_forecast_hours_until_peak=min(
            (row.forecast_hours_until_peak for row in digest_rows),
            default=ZERO,
        ),
        max_exposed_population_millions=max(
            (row.exposed_population_millions for row in digest_rows),
            default=ZERO,
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in digest_rows),
            default=ZERO,
        ),
        average_public_source_count=_ratio(
            _sum_decimal(row.public_source_count for row in digest_rows),
            region_count,
        ),
        reason_codes=reason_codes,
        rows=digest_rows,
        reason_code_counts=reason_code_counts,
    )


def market_research_weather_heat_index_alert_escalation_digest_json(
    report: MarketResearchWeatherHeatIndexAlertEscalationDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchWeatherHeatIndexAlertEscalationDigestReport:
        raise ValueError(
            "report must be a MarketResearchWeatherHeatIndexAlertEscalationDigestReport",
        )
    _require_hard_flags("heat index alert escalation digest report", report)
    reject_unsafe_surface_fields("heat index alert escalation digest report", report)
    return json_ready_no_floats(report)


def market_research_weather_heat_index_alert_escalation_digest_payload(
    report: MarketResearchWeatherHeatIndexAlertEscalationDigestReport,
) -> dict[str, Any]:
    return market_research_weather_heat_index_alert_escalation_digest_json(report)


def _empty_report(
    *,
    config: MarketResearchWeatherHeatIndexAlertEscalationDigestConfig,
    generated_at: datetime,
) -> MarketResearchWeatherHeatIndexAlertEscalationDigestReport:
    reason_code = "market_research_weather_heat_index_alert_escalation_digest_no_inputs"
    return MarketResearchWeatherHeatIndexAlertEscalationDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        digest_status="blocked",
        next_step=NEXT_STEPS["blocked"],
        region_count=ZERO,
        clear_region_count=ZERO,
        watch_region_count=ZERO,
        blocked_region_count=ZERO,
        fresh_snapshot_count=ZERO,
        stale_snapshot_count=ZERO,
        thin_source_count=ZERO,
        active_alert_count=ZERO,
        high_heat_index_count=ZERO,
        rapid_heat_rise_count=ZERO,
        near_term_peak_count=ZERO,
        high_exposure_count=ZERO,
        probability_shift_count=ZERO,
        max_forecast_heat_index_f=ZERO,
        max_heat_index_rise_f=ZERO,
        min_forecast_hours_until_peak=ZERO,
        max_exposed_population_millions=ZERO,
        max_snapshot_age_seconds=ZERO,
        average_public_source_count=ZERO,
        reason_codes=(reason_code,),
        rows=(),
        reason_code_counts=(
            MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
                reason_code=reason_code,
                count=ONE,
                region_ratio=ONE,
            ),
        ),
    )


def _row_from_input(
    row: MarketResearchWeatherHeatIndexAlertEscalationInputRow,
    *,
    config: MarketResearchWeatherHeatIndexAlertEscalationDigestConfig,
    generated_at: datetime,
) -> MarketResearchWeatherHeatIndexAlertEscalationDigestRow:
    if row.snapshot_at > generated_at:
        raise ValueError("snapshot_at must not be after generated_at")
    snapshot_age_seconds = _seconds_between(generated_at, row.snapshot_at)
    heat_index_rise_f = _quantize(row.forecast_heat_index_f - row.prior_heat_index_f)
    probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        row,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        heat_index_rise_f=heat_index_rise_f,
        probability_change=probability_change,
    )
    return MarketResearchWeatherHeatIndexAlertEscalationDigestRow(
        region_id=row.region_id,
        market_slug=row.market_slug,
        condition_id=row.condition_id,
        source_id=row.source_id,
        snapshot_at=row.snapshot_at,
        snapshot_age_seconds=snapshot_age_seconds,
        current_alert_level=row.current_alert_level,
        forecast_heat_index_f=row.forecast_heat_index_f,
        prior_heat_index_f=row.prior_heat_index_f,
        heat_index_rise_f=heat_index_rise_f,
        forecast_hours_until_peak=row.forecast_hours_until_peak,
        exposed_population_millions=row.exposed_population_millions,
        public_source_count=row.public_source_count,
        market_probability_before=row.market_probability_before,
        market_probability_after=row.market_probability_after,
        probability_change=probability_change,
        escalation_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchWeatherHeatIndexAlertEscalationInputRow,
    *,
    config: MarketResearchWeatherHeatIndexAlertEscalationDigestConfig,
    snapshot_age_seconds: Decimal,
    heat_index_rise_f: Decimal,
    probability_change: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if row.forecast_heat_index_f >= config.block_heat_index_f:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_heat_index_block",
        )
    elif row.forecast_heat_index_f >= config.watch_heat_index_f:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_heat_index_watch",
        )
    if row.current_alert_level in ALERT_LEVEL_WARNING_VALUES:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_alert_level_warning",
        )
    elif row.current_alert_level in ALERT_LEVEL_WATCH_VALUES:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_alert_level_watch",
        )
    if heat_index_rise_f >= config.rapid_heat_rise_f:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_rapid_heat_rise",
        )
    if row.forecast_hours_until_peak <= config.near_term_peak_hours:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_near_term_peak",
        )
    if snapshot_age_seconds > config.fresh_snapshot_max_age_seconds:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_stale_snapshot",
        )
    if row.public_source_count < config.min_public_source_count:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_thin_sources",
        )
    if row.exposed_population_millions >= config.high_exposure_population_millions:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_high_exposure",
        )
    if probability_change.copy_abs() >= PROBABILITY_SHIFT_THRESHOLD:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_probability_shift",
        )
    if not reason_codes:
        reason_codes.append(
            "market_research_weather_heat_index_alert_escalation_digest_clear",
        )
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    blocked_reasons = (
        "market_research_weather_heat_index_alert_escalation_digest_heat_index_block",
        "market_research_weather_heat_index_alert_escalation_digest_alert_level_warning",
    )
    if any(reason_code in reason_codes for reason_code in blocked_reasons):
        return "blocked"
    if reason_codes == (
        "market_research_weather_heat_index_alert_escalation_digest_clear",
    ):
        return "clear"
    return "watch"


def _report_status(
    rows: tuple[MarketResearchWeatherHeatIndexAlertEscalationDigestRow, ...],
) -> str:
    if any(row.escalation_status == "blocked" for row in rows):
        return "blocked"
    if any(row.escalation_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketResearchWeatherHeatIndexAlertEscalationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_research_weather_heat_index_alert_escalation_digest_no_inputs",)
    found = {code for row in rows for code in row.reason_codes}
    return tuple(code for code in REASON_CODES if code in found)


def _reason_code_counts(
    rows: tuple[MarketResearchWeatherHeatIndexAlertEscalationDigestRow, ...],
    reason_codes: tuple[str, ...],
    region_count: Decimal,
) -> tuple[MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount, ...]:
    return tuple(
        MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=reason_code,
            count=_row_count(
                rows,
                lambda row, code=reason_code: code in row.reason_codes,
            ),
            region_ratio=_ratio(
                _row_count(
                    rows,
                    lambda row, code=reason_code: code in row.reason_codes,
                ),
                region_count,
            ),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    rows: Iterable[MarketResearchWeatherHeatIndexAlertEscalationInputRow],
) -> tuple[MarketResearchWeatherHeatIndexAlertEscalationInputRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable of input rows")
    normalized: list[MarketResearchWeatherHeatIndexAlertEscalationInputRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchWeatherHeatIndexAlertEscalationInputRow:
            raise ValueError(
                "rows must contain MarketResearchWeatherHeatIndexAlertEscalationInputRow",
            )
        _require_hard_flags("heat index alert escalation input row", row)
        key = (row.region_id, row.market_slug)
        if key in seen:
            raise ValueError("rows must be unique by region_id and market_slug")
        seen.add(key)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[MarketResearchWeatherHeatIndexAlertEscalationDigestRow, ...],
) -> tuple[MarketResearchWeatherHeatIndexAlertEscalationDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchWeatherHeatIndexAlertEscalationDigestRow:
            raise ValueError(
                "rows must contain MarketResearchWeatherHeatIndexAlertEscalationDigestRow",
            )
        _require_hard_flags("heat index alert escalation digest row", row)
        key = (row.region_id, row.market_slug)
        if key in seen:
            raise ValueError("rows must be unique by region_id and market_slug")
        seen.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic heat index alert sorting")
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount, ...],
) -> tuple[MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount, ...]:
    if not isinstance(items, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in items:
        if type(item) is not MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount",
            )
        _require_hard_flags("heat index alert escalation reason code count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(item.reason_code)
    expected = tuple(sorted(items, key=lambda item: REASON_CODES.index(item.reason_code)))
    if items != expected:
        raise ValueError("reason_code_counts must use deterministic reason code sequence")
    return items


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        code = _require_member(field_name, item, allowed)
        if code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(code)
        normalized.append(code)
    if tuple(normalized) != tuple(code for code in allowed if code in seen):
        raise ValueError(f"{field_name} must use deterministic reason code sequence")
    if (
        allowed is ROW_REASON_CODES
        and "market_research_weather_heat_index_alert_escalation_digest_clear" in seen
        and len(normalized) != 1
    ):
        raise ValueError("clear reason must be isolated")
    if (
        "market_research_weather_heat_index_alert_escalation_digest_no_inputs" in seen
        and len(normalized) != 1
    ):
        raise ValueError("missing input reason must be isolated")
    return tuple(normalized)


def _validate_row(row: MarketResearchWeatherHeatIndexAlertEscalationDigestRow) -> None:
    if row.escalation_status != _row_status(row.reason_codes):
        raise ValueError("escalation_status must match reason_codes")
    if row.heat_index_rise_f != _quantize(
        row.forecast_heat_index_f - row.prior_heat_index_f,
    ):
        raise ValueError("heat_index_rise_f must match heat index values")
    if row.probability_change != _quantize(
        row.market_probability_after - row.market_probability_before,
    ):
        raise ValueError("probability_change must match market probability values")


def _validate_report(
    report: MarketResearchWeatherHeatIndexAlertEscalationDigestReport,
) -> None:
    if report.next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("next_step must match digest_status")
    if report.region_count != _count(len(report.rows)):
        raise ValueError("region_count must match rows")
    if report.clear_region_count != _row_count(
        report.rows,
        lambda row: row.escalation_status == "clear",
    ):
        raise ValueError("clear_region_count must match rows")
    if report.watch_region_count != _row_count(
        report.rows,
        lambda row: row.escalation_status == "watch",
    ):
        raise ValueError("watch_region_count must match rows")
    if report.blocked_region_count != _row_count(
        report.rows,
        lambda row: row.escalation_status == "blocked",
    ):
        raise ValueError("blocked_region_count must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_counts = (
        _empty_reason_code_counts()
        if not report.rows
        else _reason_code_counts(report.rows, report.reason_codes, report.region_count)
    )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.rows and report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if not report.rows and report.digest_status != "blocked":
        raise ValueError("digest_status must match empty input policy")
    _validate_report_counts(report)
    _validate_report_extremes(report)


def _validate_report_counts(
    report: MarketResearchWeatherHeatIndexAlertEscalationDigestReport,
) -> None:
    expected_counts: tuple[tuple[str, Decimal], ...] = (
        (
            "fresh_snapshot_count",
            _row_count(report.rows, lambda row: not _has_reason(row, "stale_snapshot")),
        ),
        (
            "stale_snapshot_count",
            _row_count(report.rows, lambda row: _has_reason(row, "stale_snapshot")),
        ),
        (
            "thin_source_count",
            _row_count(report.rows, lambda row: _has_reason(row, "thin_sources")),
        ),
        (
            "active_alert_count",
            _row_count(report.rows, lambda row: row.current_alert_level != "none"),
        ),
        (
            "high_heat_index_count",
            _row_count(
                report.rows,
                lambda row: _has_reason(row, "heat_index_block")
                or _has_reason(row, "heat_index_watch"),
            ),
        ),
        (
            "rapid_heat_rise_count",
            _row_count(report.rows, lambda row: _has_reason(row, "rapid_heat_rise")),
        ),
        (
            "near_term_peak_count",
            _row_count(report.rows, lambda row: _has_reason(row, "near_term_peak")),
        ),
        (
            "high_exposure_count",
            _row_count(report.rows, lambda row: _has_reason(row, "high_exposure")),
        ),
        (
            "probability_shift_count",
            _row_count(report.rows, lambda row: _has_reason(row, "probability_shift")),
        ),
    )
    for field_name, expected in expected_counts:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")


def _validate_report_extremes(
    report: MarketResearchWeatherHeatIndexAlertEscalationDigestReport,
) -> None:
    expectations = (
        (
            "max_forecast_heat_index_f",
            max((row.forecast_heat_index_f for row in report.rows), default=ZERO),
        ),
        (
            "max_heat_index_rise_f",
            _max_nonnegative(row.heat_index_rise_f for row in report.rows),
        ),
        (
            "min_forecast_hours_until_peak",
            min((row.forecast_hours_until_peak for row in report.rows), default=ZERO),
        ),
        (
            "max_exposed_population_millions",
            max((row.exposed_population_millions for row in report.rows), default=ZERO),
        ),
        (
            "max_snapshot_age_seconds",
            max((row.snapshot_age_seconds for row in report.rows), default=ZERO),
        ),
        (
            "average_public_source_count",
            _ratio(
                _sum_decimal(row.public_source_count for row in report.rows),
                report.region_count,
            ),
        ),
    )
    for field_name, expected in expectations:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")


def _empty_reason_code_counts() -> tuple[
    MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount,
    ...,
]:
    reason_code = "market_research_weather_heat_index_alert_escalation_digest_no_inputs"
    return (
        MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=reason_code,
            count=ONE,
            region_ratio=ONE,
        ),
    )


def _row_sort_key(
    row: MarketResearchWeatherHeatIndexAlertEscalationDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.escalation_status],
        -row.forecast_heat_index_f,
        -row.exposed_population_millions,
        row.region_id,
        row.market_slug,
    )


def _has_reason(
    row: MarketResearchWeatherHeatIndexAlertEscalationDigestRow,
    suffix: str,
) -> bool:
    return any(reason_code.endswith(f"_{suffix}") for reason_code in row.reason_codes)


def _row_count(
    rows: tuple[MarketResearchWeatherHeatIndexAlertEscalationDigestRow, ...],
    predicate: Callable[[MarketResearchWeatherHeatIndexAlertEscalationDigestRow], bool],
) -> Decimal:
    return _count(sum(1 for row in rows if predicate(row)))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _max_nonnegative(values: Iterable[Decimal]) -> Decimal:
    return max((max(value, ZERO) for value in values), default=ZERO)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("snapshot_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(whole_seconds + fractional_seconds)


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_signed_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_signed_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_signed_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value)


def _require_whole_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_whole_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_key(field_name: str, value: object) -> str:
    text = _require_text(field_name, value)
    if not all(char in KEY_CHARS for char in text):
        raise ValueError(f"{field_name} must be a lowercase public key")
    return text


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_WEATHER_HEAT_INDEX_ALERT_ESCALATION_DIGEST_CONFIG_VERSION",
    "MarketResearchWeatherHeatIndexAlertEscalationDigestConfig",
    "MarketResearchWeatherHeatIndexAlertEscalationDigestReport",
    "MarketResearchWeatherHeatIndexAlertEscalationDigestRow",
    "MarketResearchWeatherHeatIndexAlertEscalationInputRow",
    "MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount",
    "build_market_research_weather_heat_index_alert_escalation_digest",
    "market_research_weather_heat_index_alert_escalation_digest_json",
    "market_research_weather_heat_index_alert_escalation_digest_payload",
)

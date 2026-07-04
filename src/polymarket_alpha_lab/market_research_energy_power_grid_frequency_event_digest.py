"""Pure Phase 1 power-grid frequency-event digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_ENERGY_POWER_GRID_FREQUENCY_EVENT_DIGEST_CONFIG_VERSION = (
    "market-research-energy-power-grid-frequency-event-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
FREQUENCY_EVENT_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)

FREQUENCY_DEVIATION_BLOCKED_REASON = (
    "energy_power_grid_frequency_deviation_blocked"
)
FREQUENCY_DEVIATION_WATCH_REASON = "energy_power_grid_frequency_deviation_watch"
UNDER_FREQUENCY_DURATION_BLOCKED_REASON = (
    "energy_power_grid_under_frequency_duration_blocked"
)
UNDER_FREQUENCY_DURATION_WATCH_REASON = (
    "energy_power_grid_under_frequency_duration_watch"
)
LOW_RESERVE_MARGIN_BLOCKED_REASON = "energy_power_grid_low_reserve_margin_blocked"
LOW_RESERVE_MARGIN_WATCH_REASON = "energy_power_grid_low_reserve_margin_watch"
FORCED_OUTAGE_BLOCKED_REASON = "energy_power_grid_forced_outage_blocked"
FORCED_OUTAGE_WATCH_REASON = "energy_power_grid_forced_outage_watch"
LOAD_FORECAST_ERROR_BLOCKED_REASON = "energy_power_grid_load_forecast_error_blocked"
LOAD_FORECAST_ERROR_WATCH_REASON = "energy_power_grid_load_forecast_error_watch"
STALE_TELEMETRY_REASON = "energy_power_grid_stale_telemetry"
THIN_SOURCE_QUORUM_REASON = "energy_power_grid_thin_source_quorum"
SOURCE_DISAGREEMENT_BLOCKED_REASON = (
    "energy_power_grid_source_disagreement_blocked"
)
SOURCE_DISAGREEMENT_WATCH_REASON = "energy_power_grid_source_disagreement_watch"
PASS_REASON = "energy_power_grid_frequency_event_passed"
WATCH_PRESENT_REASON = "energy_power_grid_frequency_event_watch_present"
CLEAR_REASON = "energy_power_grid_frequency_event_clear"
EMPTY_REASON = "energy_power_grid_frequency_event_empty"

ROW_REASON_CODE_SEQUENCE = (
    FREQUENCY_DEVIATION_BLOCKED_REASON,
    FREQUENCY_DEVIATION_WATCH_REASON,
    UNDER_FREQUENCY_DURATION_BLOCKED_REASON,
    UNDER_FREQUENCY_DURATION_WATCH_REASON,
    LOW_RESERVE_MARGIN_BLOCKED_REASON,
    LOW_RESERVE_MARGIN_WATCH_REASON,
    FORCED_OUTAGE_BLOCKED_REASON,
    FORCED_OUTAGE_WATCH_REASON,
    LOAD_FORECAST_ERROR_BLOCKED_REASON,
    LOAD_FORECAST_ERROR_WATCH_REASON,
    STALE_TELEMETRY_REASON,
    THIN_SOURCE_QUORUM_REASON,
    SOURCE_DISAGREEMENT_BLOCKED_REASON,
    SOURCE_DISAGREEMENT_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    FREQUENCY_DEVIATION_BLOCKED_REASON,
    FREQUENCY_DEVIATION_WATCH_REASON,
    UNDER_FREQUENCY_DURATION_BLOCKED_REASON,
    UNDER_FREQUENCY_DURATION_WATCH_REASON,
    LOW_RESERVE_MARGIN_BLOCKED_REASON,
    LOW_RESERVE_MARGIN_WATCH_REASON,
    FORCED_OUTAGE_BLOCKED_REASON,
    FORCED_OUTAGE_WATCH_REASON,
    LOAD_FORECAST_ERROR_BLOCKED_REASON,
    LOAD_FORECAST_ERROR_WATCH_REASON,
    STALE_TELEMETRY_REASON,
    THIN_SOURCE_QUORUM_REASON,
    SOURCE_DISAGREEMENT_BLOCKED_REASON,
    SOURCE_DISAGREEMENT_WATCH_REASON,
    WATCH_PRESENT_REASON,
    CLEAR_REASON,
    EMPTY_REASON,
)
BLOCKED_REASON_CODES = (
    FREQUENCY_DEVIATION_BLOCKED_REASON,
    UNDER_FREQUENCY_DURATION_BLOCKED_REASON,
    LOW_RESERVE_MARGIN_BLOCKED_REASON,
    FORCED_OUTAGE_BLOCKED_REASON,
    LOAD_FORECAST_ERROR_BLOCKED_REASON,
    THIN_SOURCE_QUORUM_REASON,
    SOURCE_DISAGREEMENT_BLOCKED_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "allow_report_only_energy_power_grid_frequency_event_digest",
    STATUS_WATCH: "watch_report_only_energy_power_grid_frequency_event_digest",
    STATUS_BLOCKED: "block_report_only_energy_power_grid_frequency_event_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_ENERGY_POWER_GRID_FREQUENCY_EVENT_DIGEST_CONFIG_VERSION",
    "MarketResearchEnergyPowerGridFrequencyEventDigestConfig",
    "MarketResearchEnergyPowerGridFrequencyEventDigestInput",
    "MarketResearchEnergyPowerGridFrequencyEventDigestRow",
    "MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount",
    "MarketResearchEnergyPowerGridFrequencyEventDigestReport",
    "build_market_research_energy_power_grid_frequency_event_digest",
    "market_research_energy_power_grid_frequency_event_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEnergyPowerGridFrequencyEventDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_POWER_GRID_FREQUENCY_EVENT_DIGEST_CONFIG_VERSION
    )
    watch_frequency_deviation_mhz: Decimal = Decimal("25.000000")
    blocked_frequency_deviation_mhz: Decimal = Decimal("60.000000")
    watch_under_frequency_duration_seconds: Decimal = Decimal("30.000000")
    blocked_under_frequency_duration_seconds: Decimal = Decimal("300.000000")
    watch_reserve_margin_percentage: Decimal = Decimal("8.000000")
    blocked_reserve_margin_percentage: Decimal = Decimal("3.000000")
    watch_forced_outage_mw: Decimal = Decimal("500.000000")
    blocked_forced_outage_mw: Decimal = Decimal("1500.000000")
    watch_load_forecast_error_mw: Decimal = Decimal("750.000000")
    blocked_load_forecast_error_mw: Decimal = Decimal("2000.000000")
    max_telemetry_age_seconds: Decimal = Decimal("600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    watch_source_disagreement_ratio: Decimal = Decimal("0.200000")
    blocked_source_disagreement_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyPowerGridFrequencyEventDigestConfig:
            raise TypeError(
                "MarketResearchEnergyPowerGridFrequencyEventDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyPowerGridFrequencyEventDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_POWER_GRID_FREQUENCY_EVENT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_frequency_deviation_mhz",
            "blocked_frequency_deviation_mhz",
            "watch_under_frequency_duration_seconds",
            "blocked_under_frequency_duration_seconds",
            "watch_reserve_margin_percentage",
            "blocked_reserve_margin_percentage",
            "watch_forced_outage_mw",
            "blocked_forced_outage_mw",
            "watch_load_forecast_error_mw",
            "blocked_load_forecast_error_mw",
            "max_telemetry_age_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_source_disagreement_ratio",
            "blocked_source_disagreement_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_not_above_blocked(
            "watch_frequency_deviation_mhz",
            self.watch_frequency_deviation_mhz,
            "blocked_frequency_deviation_mhz",
            self.blocked_frequency_deviation_mhz,
        )
        _require_watch_not_above_blocked(
            "watch_under_frequency_duration_seconds",
            self.watch_under_frequency_duration_seconds,
            "blocked_under_frequency_duration_seconds",
            self.blocked_under_frequency_duration_seconds,
        )
        _require_watch_not_above_blocked(
            "watch_forced_outage_mw",
            self.watch_forced_outage_mw,
            "blocked_forced_outage_mw",
            self.blocked_forced_outage_mw,
        )
        _require_watch_not_above_blocked(
            "watch_load_forecast_error_mw",
            self.watch_load_forecast_error_mw,
            "blocked_load_forecast_error_mw",
            self.blocked_load_forecast_error_mw,
        )
        _require_watch_not_above_blocked(
            "watch_source_disagreement_ratio",
            self.watch_source_disagreement_ratio,
            "blocked_source_disagreement_ratio",
            self.blocked_source_disagreement_ratio,
        )
        if self.blocked_reserve_margin_percentage > self.watch_reserve_margin_percentage:
            raise ValueError(
                "blocked_reserve_margin_percentage must not exceed "
                "watch_reserve_margin_percentage",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerGridFrequencyEventDigestInput:
    source_id: str
    grid_region: str
    balancing_authority: str
    market_slug: str
    observed_at: datetime
    frequency_deviation_mhz: Decimal
    under_frequency_duration_seconds: Decimal
    reserve_margin_percentage: Decimal
    forced_outage_mw: Decimal
    load_forecast_error_mw: Decimal
    telemetry_age_seconds: Decimal
    source_count: Decimal
    source_disagreement_ratio: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyPowerGridFrequencyEventDigestInput:
            raise TypeError(
                "MarketResearchEnergyPowerGridFrequencyEventDigestInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyPowerGridFrequencyEventDigestInput,
            "input",
        )
        for field_name in (
            "source_id",
            "grid_region",
            "balancing_authority",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "frequency_deviation_mhz",
            "load_forecast_error_mw",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "under_frequency_duration_seconds",
            "reserve_margin_percentage",
            "forced_outage_mw",
            "telemetry_age_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_disagreement_ratio",
            _require_ratio_decimal(
                "source_disagreement_ratio",
                self.source_disagreement_ratio,
            ),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerGridFrequencyEventDigestRow:
    source_id: str
    grid_region: str
    balancing_authority: str
    market_slug: str
    observed_at: datetime
    frequency_deviation_mhz: Decimal
    absolute_frequency_deviation_mhz: Decimal
    under_frequency_duration_seconds: Decimal
    reserve_margin_percentage: Decimal
    forced_outage_mw: Decimal
    load_forecast_error_mw: Decimal
    absolute_load_forecast_error_mw: Decimal
    telemetry_age_seconds: Decimal
    source_count: Decimal
    source_disagreement_ratio: Decimal
    frequency_event_status: str
    risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyPowerGridFrequencyEventDigestRow:
            raise TypeError(
                "MarketResearchEnergyPowerGridFrequencyEventDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyPowerGridFrequencyEventDigestRow,
            "row",
        )
        for field_name in (
            "source_id",
            "grid_region",
            "balancing_authority",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "frequency_deviation_mhz",
            "load_forecast_error_mw",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "absolute_frequency_deviation_mhz",
            "under_frequency_duration_seconds",
            "reserve_margin_percentage",
            "forced_outage_mw",
            "absolute_load_forecast_error_mw",
            "telemetry_age_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_disagreement_ratio",
            _require_ratio_decimal(
                "source_disagreement_ratio",
                self.source_disagreement_ratio,
            ),
        )
        _require_member(
            "frequency_event_status",
            self.frequency_event_status,
            FREQUENCY_EVENT_STATUSES,
        )
        object.__setattr__(self, "risk_score", _require_ratio_decimal("risk_score", self.risk_score))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerGridFrequencyEventDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    frequency_deviation_event_count: Decimal
    under_frequency_event_count: Decimal
    low_reserve_margin_count: Decimal
    forced_outage_count: Decimal
    load_forecast_error_count: Decimal
    stale_telemetry_count: Decimal
    thin_source_quorum_count: Decimal
    source_disagreement_count: Decimal
    total_forced_outage_mw: Decimal
    max_absolute_frequency_deviation_mhz: Decimal
    max_under_frequency_duration_seconds: Decimal
    min_reserve_margin_percentage: Decimal
    max_absolute_load_forecast_error_mw: Decimal
    max_telemetry_age_seconds: Decimal
    frequency_event_risk_score: Decimal
    rows: tuple[MarketResearchEnergyPowerGridFrequencyEventDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyPowerGridFrequencyEventDigestReport:
            raise TypeError(
                "MarketResearchEnergyPowerGridFrequencyEventDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyPowerGridFrequencyEventDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_POWER_GRID_FREQUENCY_EVENT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("digest_status", self.digest_status, FREQUENCY_EVENT_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "frequency_deviation_event_count",
            "under_frequency_event_count",
            "low_reserve_margin_count",
            "forced_outage_count",
            "load_forecast_error_count",
            "stale_telemetry_count",
            "thin_source_quorum_count",
            "source_disagreement_count",
            "total_forced_outage_mw",
            "max_absolute_frequency_deviation_mhz",
            "max_under_frequency_duration_seconds",
            "min_reserve_margin_percentage",
            "max_absolute_load_forecast_error_mw",
            "max_telemetry_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "frequency_event_risk_score",
            _require_ratio_decimal(
                "frequency_event_risk_score",
                self.frequency_event_risk_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_energy_power_grid_frequency_event_digest(
    inputs: tuple[object, ...],
    *,
    config: MarketResearchEnergyPowerGridFrequencyEventDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchEnergyPowerGridFrequencyEventDigestReport:
    cfg = config or MarketResearchEnergyPowerGridFrequencyEventDigestConfig()
    if type(cfg) is not MarketResearchEnergyPowerGridFrequencyEventDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchEnergyPowerGridFrequencyEventDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for row in normalized_inputs:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at cannot be after generated_at")
    rows = tuple(
        sorted(
            (
                _build_row(row, config=cfg)
                for row in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _report_status(rows)
    return MarketResearchEnergyPowerGridFrequencyEventDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        blocked_count=_status_count(rows, STATUS_BLOCKED),
        frequency_deviation_event_count=(
            _reason_count(FREQUENCY_DEVIATION_BLOCKED_REASON, rows)
            + _reason_count(FREQUENCY_DEVIATION_WATCH_REASON, rows)
        ),
        under_frequency_event_count=(
            _reason_count(UNDER_FREQUENCY_DURATION_BLOCKED_REASON, rows)
            + _reason_count(UNDER_FREQUENCY_DURATION_WATCH_REASON, rows)
        ),
        low_reserve_margin_count=(
            _reason_count(LOW_RESERVE_MARGIN_BLOCKED_REASON, rows)
            + _reason_count(LOW_RESERVE_MARGIN_WATCH_REASON, rows)
        ),
        forced_outage_count=(
            _reason_count(FORCED_OUTAGE_BLOCKED_REASON, rows)
            + _reason_count(FORCED_OUTAGE_WATCH_REASON, rows)
        ),
        load_forecast_error_count=(
            _reason_count(LOAD_FORECAST_ERROR_BLOCKED_REASON, rows)
            + _reason_count(LOAD_FORECAST_ERROR_WATCH_REASON, rows)
        ),
        stale_telemetry_count=_reason_count(STALE_TELEMETRY_REASON, rows),
        thin_source_quorum_count=_reason_count(THIN_SOURCE_QUORUM_REASON, rows),
        source_disagreement_count=(
            _reason_count(SOURCE_DISAGREEMENT_BLOCKED_REASON, rows)
            + _reason_count(SOURCE_DISAGREEMENT_WATCH_REASON, rows)
        ),
        total_forced_outage_mw=_sum_decimal(row.forced_outage_mw for row in rows),
        max_absolute_frequency_deviation_mhz=_max_decimal(
            (row.absolute_frequency_deviation_mhz for row in rows),
            default=ZERO,
        ),
        max_under_frequency_duration_seconds=_max_decimal(
            (row.under_frequency_duration_seconds for row in rows),
            default=ZERO,
        ),
        min_reserve_margin_percentage=_min_decimal(
            (row.reserve_margin_percentage for row in rows),
            default=ZERO,
        ),
        max_absolute_load_forecast_error_mw=_max_decimal(
            (row.absolute_load_forecast_error_mw for row in rows),
            default=ZERO,
        ),
        max_telemetry_age_seconds=_max_decimal(
            (row.telemetry_age_seconds for row in rows),
            default=ZERO,
        ),
        frequency_event_risk_score=_report_risk_score(rows),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_energy_power_grid_frequency_event_digest_payload(
    report: MarketResearchEnergyPowerGridFrequencyEventDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEnergyPowerGridFrequencyEventDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchEnergyPowerGridFrequencyEventDigestReport",
        )
    _validate_report_consistency(report)
    return _payload_value(report)


def _build_row(
    row: MarketResearchEnergyPowerGridFrequencyEventDigestInput,
    *,
    config: MarketResearchEnergyPowerGridFrequencyEventDigestConfig,
) -> MarketResearchEnergyPowerGridFrequencyEventDigestRow:
    absolute_frequency_deviation_mhz = _quantize(abs(row.frequency_deviation_mhz))
    absolute_load_forecast_error_mw = _quantize(abs(row.load_forecast_error_mw))
    reason_codes = _row_reason_codes(
        row,
        absolute_frequency_deviation_mhz=absolute_frequency_deviation_mhz,
        absolute_load_forecast_error_mw=absolute_load_forecast_error_mw,
        config=config,
    )
    frequency_event_status = _row_status(reason_codes)
    return MarketResearchEnergyPowerGridFrequencyEventDigestRow(
        source_id=row.source_id,
        grid_region=row.grid_region,
        balancing_authority=row.balancing_authority,
        market_slug=row.market_slug,
        observed_at=row.observed_at,
        frequency_deviation_mhz=row.frequency_deviation_mhz,
        absolute_frequency_deviation_mhz=absolute_frequency_deviation_mhz,
        under_frequency_duration_seconds=row.under_frequency_duration_seconds,
        reserve_margin_percentage=row.reserve_margin_percentage,
        forced_outage_mw=row.forced_outage_mw,
        load_forecast_error_mw=row.load_forecast_error_mw,
        absolute_load_forecast_error_mw=absolute_load_forecast_error_mw,
        telemetry_age_seconds=row.telemetry_age_seconds,
        source_count=row.source_count,
        source_disagreement_ratio=row.source_disagreement_ratio,
        frequency_event_status=frequency_event_status,
        risk_score=_status_risk_score(frequency_event_status),
        upstream_reason_codes=row.upstream_reason_codes,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchEnergyPowerGridFrequencyEventDigestInput,
    *,
    absolute_frequency_deviation_mhz: Decimal,
    absolute_load_forecast_error_mw: Decimal,
    config: MarketResearchEnergyPowerGridFrequencyEventDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if absolute_frequency_deviation_mhz >= config.blocked_frequency_deviation_mhz:
        reasons.append(FREQUENCY_DEVIATION_BLOCKED_REASON)
    elif absolute_frequency_deviation_mhz >= config.watch_frequency_deviation_mhz:
        reasons.append(FREQUENCY_DEVIATION_WATCH_REASON)
    if row.under_frequency_duration_seconds >= config.blocked_under_frequency_duration_seconds:
        reasons.append(UNDER_FREQUENCY_DURATION_BLOCKED_REASON)
    elif row.under_frequency_duration_seconds >= config.watch_under_frequency_duration_seconds:
        reasons.append(UNDER_FREQUENCY_DURATION_WATCH_REASON)
    if row.reserve_margin_percentage <= config.blocked_reserve_margin_percentage:
        reasons.append(LOW_RESERVE_MARGIN_BLOCKED_REASON)
    elif row.reserve_margin_percentage <= config.watch_reserve_margin_percentage:
        reasons.append(LOW_RESERVE_MARGIN_WATCH_REASON)
    if row.forced_outage_mw >= config.blocked_forced_outage_mw:
        reasons.append(FORCED_OUTAGE_BLOCKED_REASON)
    elif row.forced_outage_mw >= config.watch_forced_outage_mw:
        reasons.append(FORCED_OUTAGE_WATCH_REASON)
    if absolute_load_forecast_error_mw >= config.blocked_load_forecast_error_mw:
        reasons.append(LOAD_FORECAST_ERROR_BLOCKED_REASON)
    elif absolute_load_forecast_error_mw >= config.watch_load_forecast_error_mw:
        reasons.append(LOAD_FORECAST_ERROR_WATCH_REASON)
    if row.telemetry_age_seconds > config.max_telemetry_age_seconds:
        reasons.append(STALE_TELEMETRY_REASON)
    if row.source_count < config.min_source_count:
        reasons.append(THIN_SOURCE_QUORUM_REASON)
    if row.source_disagreement_ratio >= config.blocked_source_disagreement_ratio:
        reasons.append(SOURCE_DISAGREEMENT_BLOCKED_REASON)
    elif row.source_disagreement_ratio >= config.watch_source_disagreement_ratio:
        reasons.append(SOURCE_DISAGREEMENT_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        ROW_REASON_CODE_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCKED_REASON_CODES for reason in reason_codes):
        return STATUS_BLOCKED
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _status_risk_score(status: str) -> Decimal:
    if status == STATUS_BLOCKED:
        return ONE
    if status == STATUS_WATCH:
        return WATCH_RISK_SCORE
    return ZERO


def _report_reason_codes(
    rows: tuple[MarketResearchEnergyPowerGridFrequencyEventDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {reason for row in rows for reason in row.reason_codes if reason != PASS_REASON}
    reasons = [
        reason
        for reason in REPORT_REASON_CODE_SEQUENCE
        if reason in present
    ]
    if any(row.frequency_event_status == STATUS_WATCH for row in rows):
        reasons.append(WATCH_PRESENT_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        REPORT_REASON_CODE_SEQUENCE,
    )


def _report_status(
    rows: tuple[MarketResearchEnergyPowerGridFrequencyEventDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.frequency_event_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.frequency_event_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchEnergyPowerGridFrequencyEventDigestRow, ...],
) -> tuple[MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount, ...]:
    row_count = _decimal_count(len(rows))
    if reason_codes == (EMPTY_REASON,):
        return (
            MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_count(
    reason_code: str,
    rows: tuple[MarketResearchEnergyPowerGridFrequencyEventDigestRow, ...],
) -> Decimal:
    if reason_code == WATCH_PRESENT_REASON:
        return _status_count(rows, STATUS_WATCH)
    if reason_code == CLEAR_REASON:
        return _status_count(rows, STATUS_PASS)
    return _reason_count(reason_code, rows)


def _reason_count(
    reason_code: str,
    rows: tuple[MarketResearchEnergyPowerGridFrequencyEventDigestRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[MarketResearchEnergyPowerGridFrequencyEventDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.frequency_event_status == status))


def _report_risk_score(
    rows: tuple[MarketResearchEnergyPowerGridFrequencyEventDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    weighted = _status_count(rows, STATUS_BLOCKED) + (
        _status_count(rows, STATUS_WATCH) * WATCH_RISK_SCORE
    )
    return _ratio(weighted, _decimal_count(len(rows)))


def _validate_row_consistency(
    row: MarketResearchEnergyPowerGridFrequencyEventDigestRow,
) -> None:
    if row.absolute_frequency_deviation_mhz != abs(row.frequency_deviation_mhz):
        raise ValueError(
            "absolute_frequency_deviation_mhz must match frequency_deviation_mhz",
        )
    if row.absolute_load_forecast_error_mw != abs(row.load_forecast_error_mw):
        raise ValueError(
            "absolute_load_forecast_error_mw must match load_forecast_error_mw",
        )
    if row.frequency_event_status != _row_status(row.reason_codes):
        raise ValueError("reason_codes must match frequency_event_status")
    if row.risk_score != _status_risk_score(row.frequency_event_status):
        raise ValueError("risk_score must match frequency_event_status")
    if row.frequency_event_status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("reason_codes must match frequency_event_status")
    if row.frequency_event_status != STATUS_PASS and PASS_REASON in row.reason_codes:
        raise ValueError("reason_codes must match frequency_event_status")


def _validate_report_consistency(
    report: MarketResearchEnergyPowerGridFrequencyEventDigestReport,
) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_count must match rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.frequency_deviation_event_count != (
        _reason_count(FREQUENCY_DEVIATION_BLOCKED_REASON, report.rows)
        + _reason_count(FREQUENCY_DEVIATION_WATCH_REASON, report.rows)
    ):
        raise ValueError("frequency_deviation_event_count must match rows")
    if report.under_frequency_event_count != (
        _reason_count(UNDER_FREQUENCY_DURATION_BLOCKED_REASON, report.rows)
        + _reason_count(UNDER_FREQUENCY_DURATION_WATCH_REASON, report.rows)
    ):
        raise ValueError("under_frequency_event_count must match rows")
    if report.low_reserve_margin_count != (
        _reason_count(LOW_RESERVE_MARGIN_BLOCKED_REASON, report.rows)
        + _reason_count(LOW_RESERVE_MARGIN_WATCH_REASON, report.rows)
    ):
        raise ValueError("low_reserve_margin_count must match rows")
    if report.forced_outage_count != (
        _reason_count(FORCED_OUTAGE_BLOCKED_REASON, report.rows)
        + _reason_count(FORCED_OUTAGE_WATCH_REASON, report.rows)
    ):
        raise ValueError("forced_outage_count must match rows")
    if report.load_forecast_error_count != (
        _reason_count(LOAD_FORECAST_ERROR_BLOCKED_REASON, report.rows)
        + _reason_count(LOAD_FORECAST_ERROR_WATCH_REASON, report.rows)
    ):
        raise ValueError("load_forecast_error_count must match rows")
    if report.stale_telemetry_count != _reason_count(STALE_TELEMETRY_REASON, report.rows):
        raise ValueError("stale_telemetry_count must match rows")
    if report.thin_source_quorum_count != _reason_count(
        THIN_SOURCE_QUORUM_REASON,
        report.rows,
    ):
        raise ValueError("thin_source_quorum_count must match rows")
    if report.source_disagreement_count != (
        _reason_count(SOURCE_DISAGREEMENT_BLOCKED_REASON, report.rows)
        + _reason_count(SOURCE_DISAGREEMENT_WATCH_REASON, report.rows)
    ):
        raise ValueError("source_disagreement_count must match rows")
    if report.total_forced_outage_mw != _sum_decimal(
        row.forced_outage_mw for row in report.rows
    ):
        raise ValueError("total_forced_outage_mw must match rows")
    if report.max_absolute_frequency_deviation_mhz != _max_decimal(
        (row.absolute_frequency_deviation_mhz for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_absolute_frequency_deviation_mhz must match rows")
    if report.max_under_frequency_duration_seconds != _max_decimal(
        (row.under_frequency_duration_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_under_frequency_duration_seconds must match rows")
    if report.min_reserve_margin_percentage != _min_decimal(
        (row.reserve_margin_percentage for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_reserve_margin_percentage must match rows")
    if report.max_absolute_load_forecast_error_mw != _max_decimal(
        (row.absolute_load_forecast_error_mw for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_absolute_load_forecast_error_mw must match rows")
    if report.max_telemetry_age_seconds != _max_decimal(
        (row.telemetry_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_telemetry_age_seconds must match rows")
    if report.frequency_event_risk_score != _report_risk_score(report.rows):
        raise ValueError("frequency_event_risk_score must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_inputs(
    inputs: tuple[object, ...],
) -> tuple[MarketResearchEnergyPowerGridFrequencyEventDigestInput, ...]:
    if type(inputs) is not tuple:
        raise ValueError("inputs must be a tuple")
    seen_source_ids: set[str] = set()
    normalized: list[MarketResearchEnergyPowerGridFrequencyEventDigestInput] = []
    for row in inputs:
        if type(row) is not MarketResearchEnergyPowerGridFrequencyEventDigestInput:
            raise ValueError(
                "inputs must contain "
                "MarketResearchEnergyPowerGridFrequencyEventDigestInput",
            )
        _require_hard_flags("input", row)
        if row.source_id in seen_source_ids:
            raise ValueError("inputs must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[MarketResearchEnergyPowerGridFrequencyEventDigestRow, ...],
) -> tuple[MarketResearchEnergyPowerGridFrequencyEventDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchEnergyPowerGridFrequencyEventDigestRow:
            raise ValueError(
                "rows must contain MarketResearchEnergyPowerGridFrequencyEventDigestRow",
            )
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    rows: tuple[
        MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
    return tuple(
        sorted(rows, key=lambda row: REPORT_REASON_CODE_SEQUENCE.index(row.reason_code)),
    )


def _normalize_open_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Iterable[str],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(reason_codes)
    seen: set[str] = set()
    for reason_code in normalized:
        _require_member("reason_code", reason_code, sequence)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in sequence if reason_code in seen)


def _row_sort_key(
    row: MarketResearchEnergyPowerGridFrequencyEventDigestRow,
) -> tuple[int, Decimal, str, str, str, str]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_PASS: 2,
    }
    return (
        status_rank[row.frequency_event_status],
        -row.risk_score,
        row.market_slug,
        row.grid_region,
        row.balancing_authority,
        row.source_id,
    )


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize(total)


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return default
    for value in normalized:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
    return _quantize(max(normalized))


def _min_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return default
    for value in normalized:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
    return _quantize(min(normalized))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_watch_not_above_blocked(
    watch_field_name: str,
    watch_value: Decimal,
    blocked_field_name: str,
    blocked_value: Decimal,
) -> None:
    if watch_value > blocked_value:
        raise ValueError(f"{watch_field_name} must not exceed {blocked_field_name}")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
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
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


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

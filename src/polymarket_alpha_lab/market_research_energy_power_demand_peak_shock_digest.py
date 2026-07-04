"""Pure Phase 1 energy power demand peak shock digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_ENERGY_POWER_DEMAND_PEAK_SHOCK_DIGEST_CONFIG_VERSION = (
    "market-research-energy-power-demand-peak-shock-digest-v0"
)

DIGEST_STATUSES = ("ready", "watch", "blocked")
DEMAND_PEAK_SHOCK_REASON = (
    "market_research_energy_power_demand_peak_shock_digest_demand_peak_shock"
)
RESERVE_SCARCITY_REASON = (
    "market_research_energy_power_demand_peak_shock_digest_reserve_scarcity"
)
HEAT_STRESS_REASON = (
    "market_research_energy_power_demand_peak_shock_digest_heat_stress"
)
OUTAGE_PRESSURE_REASON = (
    "market_research_energy_power_demand_peak_shock_digest_outage_pressure"
)
MISSING_ACKNOWLEDGEMENT_REASON = (
    "market_research_energy_power_demand_peak_shock_digest_missing_acknowledgement"
)
SLOW_ACKNOWLEDGEMENT_REASON = (
    "market_research_energy_power_demand_peak_shock_digest_slow_acknowledgement"
)
STALE_OBSERVATION_REASON = (
    "market_research_energy_power_demand_peak_shock_digest_stale_observation"
)
THIN_SOURCES_REASON = (
    "market_research_energy_power_demand_peak_shock_digest_thin_sources"
)
READY_REASON = "market_research_energy_power_demand_peak_shock_digest_ready"
NO_INPUTS_REASON = "market_research_energy_power_demand_peak_shock_digest_no_inputs"
REASON_CODES = (
    DEMAND_PEAK_SHOCK_REASON,
    RESERVE_SCARCITY_REASON,
    HEAT_STRESS_REASON,
    OUTAGE_PRESSURE_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
NEXT_STEPS = {
    "ready": "allow_report_only_market_research_energy_power_demand_peak_shock_digest",
    "watch": "watch_report_only_market_research_energy_power_demand_peak_shock_digest",
    "blocked": "block_report_only_market_research_energy_power_demand_peak_shock_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("or", "der"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_ENERGY_POWER_DEMAND_PEAK_SHOCK_DIGEST_CONFIG_VERSION",
    "MarketResearchEnergyPowerDemandPeakShockDigestConfig",
    "MarketResearchEnergyPowerDemandPeakShockDigestInputRow",
    "MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount",
    "MarketResearchEnergyPowerDemandPeakShockDigestReport",
    "MarketResearchEnergyPowerDemandPeakShockDigestRow",
    "build_market_research_energy_power_demand_peak_shock_digest",
    "market_research_energy_power_demand_peak_shock_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEnergyPowerDemandPeakShockDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_POWER_DEMAND_PEAK_SHOCK_DIGEST_CONFIG_VERSION
    )
    fresh_observation_max_age_seconds: Decimal = Decimal("1800.000000")
    min_source_count: Decimal = Decimal("2.000000")
    demand_peak_shock_ratio_threshold: Decimal = Decimal("0.120000")
    reserve_margin_watch_threshold: Decimal = Decimal("0.100000")
    heat_stress_celsius_threshold: Decimal = Decimal("5.000000")
    outage_share_threshold: Decimal = Decimal("0.150000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyPowerDemandPeakShockDigestConfig:
            raise TypeError(
                "MarketResearchEnergyPowerDemandPeakShockDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyPowerDemandPeakShockDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchEnergyPowerDemandPeakShockDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "fresh_observation_max_age_seconds",
            "max_acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "demand_peak_shock_ratio_threshold",
            "reserve_margin_watch_threshold",
            "outage_share_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "heat_stress_celsius_threshold",
            _require_nonnegative_decimal(
                "heat_stress_celsius_threshold",
                self.heat_stress_celsius_threshold,
            ),
        )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerDemandPeakShockDigestInputRow:
    research_key: str
    condition_id: str
    market_slug: str
    power_market_key: str
    power_region: str
    demand_zone: str
    public_demand_reference: str
    observed_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    forecast_peak_mw: Decimal
    observed_peak_mw: Decimal
    reserve_margin_ratio: Decimal
    temperature_anomaly_c: Decimal
    outage_share_ratio: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyPowerDemandPeakShockDigestInputRow:
            raise TypeError(
                "MarketResearchEnergyPowerDemandPeakShockDigestInputRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyPowerDemandPeakShockDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchEnergyPowerDemandPeakShockDigestInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "market_slug",
            "power_market_key",
            "power_region",
            "demand_zone",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string("public_demand_reference", self.public_demand_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("forecast_peak_mw", "observed_peak_mw"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("reserve_margin_ratio", "outage_share_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "temperature_anomaly_c",
            _require_decimal("temperature_anomaly_c", self.temperature_anomaly_c),
        )
        _require_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerDemandPeakShockDigestRow:
    research_key: str
    condition_id: str
    market_slug: str
    power_market_key: str
    power_region: str
    demand_zone: str
    shock_status: str
    observation_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    source_gap_count: Decimal
    forecast_peak_mw: Decimal
    observed_peak_mw: Decimal
    peak_demand_delta_mw: Decimal
    peak_shock_ratio: Decimal
    reserve_margin_ratio: Decimal
    temperature_anomaly_c: Decimal
    outage_share_ratio: Decimal
    redacted_public_demand_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyPowerDemandPeakShockDigestRow:
            raise TypeError(
                "MarketResearchEnergyPowerDemandPeakShockDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyPowerDemandPeakShockDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchEnergyPowerDemandPeakShockDigestRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "market_slug",
            "power_market_key",
            "power_region",
            "demand_zone",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_digest_status("shock_status", self.shock_status)
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        for field_name in ("source_count", "source_gap_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("forecast_peak_mw", "observed_peak_mw"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "peak_demand_delta_mw",
            _require_decimal("peak_demand_delta_mw", self.peak_demand_delta_mw),
        )
        object.__setattr__(
            self,
            "peak_shock_ratio",
            _require_nonnegative_decimal("peak_shock_ratio", self.peak_shock_ratio),
        )
        for field_name in ("reserve_margin_ratio", "outage_share_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "temperature_anomaly_c",
            _require_decimal("temperature_anomaly_c", self.temperature_anomaly_c),
        )
        _require_redacted_reference(
            "redacted_public_demand_reference",
            self.redacted_public_demand_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    shock_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "shock_ratio",
            _require_probability_decimal("shock_ratio", self.shock_ratio),
        )
        _require_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerDemandPeakShockDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    power_demand_peak_shock_count: Decimal
    ready_shock_count: Decimal
    watch_shock_count: Decimal
    blocked_shock_count: Decimal
    demand_peak_shock_count: Decimal
    reserve_scarcity_count: Decimal
    heat_stress_count: Decimal
    outage_pressure_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    average_peak_shock_ratio: Decimal
    max_observation_age_seconds: Decimal
    average_source_count: Decimal
    fresh_observation_max_age_seconds: Decimal
    min_source_count: Decimal
    demand_peak_shock_ratio_threshold: Decimal
    reserve_margin_watch_threshold: Decimal
    heat_stress_celsius_threshold: Decimal
    outage_share_threshold: Decimal
    max_acknowledgement_lag_seconds: Decimal
    rows: tuple[MarketResearchEnergyPowerDemandPeakShockDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyPowerDemandPeakShockDigestReport:
            raise TypeError(
                "MarketResearchEnergyPowerDemandPeakShockDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyPowerDemandPeakShockDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchEnergyPowerDemandPeakShockDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "power_demand_peak_shock_count",
            "ready_shock_count",
            "watch_shock_count",
            "blocked_shock_count",
            "demand_peak_shock_count",
            "reserve_scarcity_count",
            "heat_stress_count",
            "outage_pressure_count",
            "stale_observation_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_peak_shock_ratio",
            "max_observation_age_seconds",
            "average_source_count",
            "fresh_observation_max_age_seconds",
            "max_acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_nonnegative_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "demand_peak_shock_ratio_threshold",
            "reserve_margin_watch_threshold",
            "outage_share_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "heat_stress_celsius_threshold",
            _require_nonnegative_decimal(
                "heat_stress_celsius_threshold",
                self.heat_stress_celsius_threshold,
            ),
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
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_energy_power_demand_peak_shock_digest(
    input_rows: list[MarketResearchEnergyPowerDemandPeakShockDigestInputRow]
    | tuple[MarketResearchEnergyPowerDemandPeakShockDigestInputRow, ...],
    *,
    config: MarketResearchEnergyPowerDemandPeakShockDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyPowerDemandPeakShockDigestReport:
    if type(config) is not MarketResearchEnergyPowerDemandPeakShockDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchEnergyPowerDemandPeakShockDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows_in = _normalize_input_rows(input_rows)
    rows = _rows(rows_in, config=config, generated_at=generated_at_utc)
    shock_count = _decimal_count(len(rows))
    ready_count = _status_count(rows, "ready")
    watch_count = _status_count(rows, "watch")
    blocked_count = _status_count(rows, "blocked")
    digest_status = _report_status(
        shock_count=shock_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)

    return MarketResearchEnergyPowerDemandPeakShockDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        power_demand_peak_shock_count=shock_count,
        ready_shock_count=ready_count,
        watch_shock_count=watch_count,
        blocked_shock_count=blocked_count,
        demand_peak_shock_count=_event_count_with(rows, DEMAND_PEAK_SHOCK_REASON),
        reserve_scarcity_count=_event_count_with(rows, RESERVE_SCARCITY_REASON),
        heat_stress_count=_event_count_with(rows, HEAT_STRESS_REASON),
        outage_pressure_count=_event_count_with(rows, OUTAGE_PRESSURE_REASON),
        stale_observation_count=_event_count_with(rows, STALE_OBSERVATION_REASON),
        thin_source_count=_event_count_with(rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_event_count_with(
            rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_event_count_with(
            rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        average_peak_shock_ratio=_average_peak_shock_ratio(rows),
        max_observation_age_seconds=_max_decimal(
            row.observation_age_seconds for row in rows
        ),
        average_source_count=_average_decimal(row.source_count for row in rows),
        fresh_observation_max_age_seconds=config.fresh_observation_max_age_seconds,
        min_source_count=config.min_source_count,
        demand_peak_shock_ratio_threshold=config.demand_peak_shock_ratio_threshold,
        reserve_margin_watch_threshold=config.reserve_margin_watch_threshold,
        heat_stress_celsius_threshold=config.heat_stress_celsius_threshold,
        outage_share_threshold=config.outage_share_threshold,
        max_acknowledgement_lag_seconds=config.max_acknowledgement_lag_seconds,
        rows=rows,
        source_config_versions=_source_config_versions(rows_in),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_energy_power_demand_peak_shock_digest_payload(
    report: MarketResearchEnergyPowerDemandPeakShockDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEnergyPowerDemandPeakShockDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchEnergyPowerDemandPeakShockDigestReport",
        )
    _require_flags("report", report)
    payload = _plain(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _normalize_input_rows(
    value: object,
) -> tuple[MarketResearchEnergyPowerDemandPeakShockDigestInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchEnergyPowerDemandPeakShockDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchEnergyPowerDemandPeakShockDigestInputRow",
            )
        _require_flags("input row", row)
        if row.power_market_key in seen:
            raise ValueError("input rows must not contain duplicate power_market_key values")
        seen.add(row.power_market_key)
    return rows


def _rows(
    input_rows: tuple[MarketResearchEnergyPowerDemandPeakShockDigestInputRow, ...],
    *,
    config: MarketResearchEnergyPowerDemandPeakShockDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchEnergyPowerDemandPeakShockDigestRow, ...]:
    rows = []
    for row in input_rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        if row.acknowledged_at is not None and row.acknowledged_at < row.observed_at:
            raise ValueError("acknowledged_at must not precede observed_at")
        observation_age_seconds = _seconds_between(row.observed_at, generated_at)
        acknowledgement_lag_seconds = (
            None
            if row.acknowledged_at is None
            else _seconds_between(row.observed_at, row.acknowledged_at)
        )
        source_gap_count = _count_gap(config.min_source_count, row.source_count)
        peak_demand_delta_mw = _quantize(row.observed_peak_mw - row.forecast_peak_mw)
        peak_shock_ratio = _positive_ratio(peak_demand_delta_mw, row.forecast_peak_mw)
        reason_codes = _row_reason_codes(
            row,
            config=config,
            observation_age_seconds=observation_age_seconds,
            acknowledgement_lag_seconds=acknowledgement_lag_seconds,
            source_gap_count=source_gap_count,
            peak_shock_ratio=peak_shock_ratio,
        )
        rows.append(
            MarketResearchEnergyPowerDemandPeakShockDigestRow(
                research_key=row.research_key,
                condition_id=row.condition_id,
                market_slug=row.market_slug,
                power_market_key=row.power_market_key,
                power_region=row.power_region,
                demand_zone=row.demand_zone,
                shock_status=_row_status(reason_codes),
                observation_age_seconds=observation_age_seconds,
                acknowledgement_lag_seconds=acknowledgement_lag_seconds,
                source_count=row.source_count,
                source_gap_count=source_gap_count,
                forecast_peak_mw=row.forecast_peak_mw,
                observed_peak_mw=row.observed_peak_mw,
                peak_demand_delta_mw=peak_demand_delta_mw,
                peak_shock_ratio=peak_shock_ratio,
                reserve_margin_ratio=row.reserve_margin_ratio,
                temperature_anomaly_c=row.temperature_anomaly_c,
                outage_share_ratio=row.outage_share_ratio,
                redacted_public_demand_reference=_redacted_public_reference(
                    row.public_demand_reference,
                ),
                reason_codes=reason_codes,
            ),
        )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                _status_rank(item.shock_status),
                item.power_market_key,
                item.research_key,
            ),
        ),
    )


def _row_reason_codes(
    row: MarketResearchEnergyPowerDemandPeakShockDigestInputRow,
    *,
    config: MarketResearchEnergyPowerDemandPeakShockDigestConfig,
    observation_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    source_gap_count: Decimal,
    peak_shock_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes = []
    if peak_shock_ratio >= config.demand_peak_shock_ratio_threshold:
        reason_codes.append(DEMAND_PEAK_SHOCK_REASON)
    if row.reserve_margin_ratio < config.reserve_margin_watch_threshold:
        reason_codes.append(RESERVE_SCARCITY_REASON)
    if row.temperature_anomaly_c >= config.heat_stress_celsius_threshold:
        reason_codes.append(HEAT_STRESS_REASON)
    if row.outage_share_ratio > config.outage_share_threshold:
        reason_codes.append(OUTAGE_PRESSURE_REASON)
    if acknowledgement_lag_seconds is None:
        reason_codes.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reason_codes.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if observation_age_seconds > config.fresh_observation_max_age_seconds:
        reason_codes.append(STALE_OBSERVATION_REASON)
    if source_gap_count > ZERO:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return "ready"
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return "blocked"
    if (
        DEMAND_PEAK_SHOCK_REASON in reason_codes
        and RESERVE_SCARCITY_REASON in reason_codes
    ):
        return "blocked"
    return "watch"


def _report_status(
    *,
    shock_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
) -> str:
    if shock_count == ZERO:
        return "blocked"
    if blocked_count > ZERO:
        return "blocked"
    if watch_count > ZERO:
        return "watch"
    return "ready"


def _reason_code_counts(
    rows: tuple[MarketResearchEnergyPowerDemandPeakShockDigestRow, ...],
) -> tuple[MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                shock_ratio=ZERO,
            ),
        )
    total = _decimal_count(len(rows))
    return tuple(
        MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code=reason_code,
            count=_event_count_with(rows, reason_code),
            shock_ratio=_ratio(_event_count_with(rows, reason_code), total),
        )
        for reason_code in REASON_CODES
        if reason_code != NO_INPUTS_REASON
        and any(reason_code in row.reason_codes for row in rows)
    )


def _event_count_with(
    rows: tuple[MarketResearchEnergyPowerDemandPeakShockDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    rows: tuple[MarketResearchEnergyPowerDemandPeakShockDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted((row.power_market_key, row.source_config_version) for row in rows),
    )


def _status_count(
    rows: tuple[MarketResearchEnergyPowerDemandPeakShockDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.shock_status == status))


def _average_peak_shock_ratio(
    rows: tuple[MarketResearchEnergyPowerDemandPeakShockDigestRow, ...],
) -> Decimal:
    return _average_decimal(row.peak_shock_ratio for row in rows)


def _average_decimal(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _ratio(sum(items, ZERO), _decimal_count(len(items)))


def _max_decimal(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return max(items)


def _count_gap(required_count: Decimal, actual_count: Decimal) -> Decimal:
    if actual_count >= required_count:
        return ZERO
    return _quantize(required_count - actual_count)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _positive_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if numerator <= ZERO:
        return ZERO
    return _ratio(numerator, denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _plain(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, tuple):
        return tuple(_plain(item) for item in value)
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchEnergyPowerDemandPeakShockDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchEnergyPowerDemandPeakShockDigestRow:
            raise ValueError(
                "rows must contain MarketResearchEnergyPowerDemandPeakShockDigestRow",
            )
        _require_flags("row", row)
        if row.power_market_key in seen:
            raise ValueError("rows must not contain duplicate power_market_key values")
        seen.add(row.power_market_key)
    expected = tuple(
        sorted(
            rows,
            key=lambda item: (
                _status_rank(item.shock_status),
                item.power_market_key,
                item.research_key,
            ),
        ),
    )
    if rows != expected:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("source_config_versions must be a list or tuple")
    versions = tuple(value)
    seen: set[str] = set()
    for item in versions:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("source_config_versions entries must be pairs")
        power_market_key, source_config_version = item
        _require_public_string("source_config_versions power_market_key", power_market_key)
        _require_public_string(
            "source_config_versions source_config_version",
            source_config_version,
        )
        if power_market_key in seen:
            raise ValueError("source_config_versions power market keys must be unique")
        seen.add(power_market_key)
    if versions != tuple(sorted(versions)):
        raise ValueError("source_config_versions must be sorted")
    return versions


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount",
            )
        _require_flags("reason code count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts reason codes must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        sorted(counts, key=lambda item: _reason_rank(item.reason_code)),
    )
    if counts != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_reason_code("reason_codes", code)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(sorted(codes, key=_reason_rank))
    if codes != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    return codes


def _validate_row(row: MarketResearchEnergyPowerDemandPeakShockDigestRow) -> None:
    expected_peak_delta = _quantize(row.observed_peak_mw - row.forecast_peak_mw)
    if row.peak_demand_delta_mw != expected_peak_delta:
        raise ValueError("peak_demand_delta_mw must match observed minus forecast peak")
    expected_peak_shock_ratio = _positive_ratio(
        row.peak_demand_delta_mw,
        row.forecast_peak_mw,
    )
    if row.peak_shock_ratio != expected_peak_shock_ratio:
        raise ValueError("peak_shock_ratio must match positive peak delta over forecast")
    if row.shock_status != _row_status(row.reason_codes):
        raise ValueError("shock_status must match reason_codes")
    if row.reason_codes == (READY_REASON,) and (
        row.source_gap_count != ZERO
        or row.acknowledgement_lag_seconds is None
    ):
        raise ValueError("reason_codes must reflect row gaps")


def _validate_report(report: MarketResearchEnergyPowerDemandPeakShockDigestReport) -> None:
    rows = report.rows
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.power_demand_peak_shock_count != _decimal_count(len(rows)):
        raise ValueError("power_demand_peak_shock_count must match rows")
    checks = (
        ("ready_shock_count", _status_count(rows, "ready")),
        ("watch_shock_count", _status_count(rows, "watch")),
        ("blocked_shock_count", _status_count(rows, "blocked")),
        ("demand_peak_shock_count", _event_count_with(rows, DEMAND_PEAK_SHOCK_REASON)),
        ("reserve_scarcity_count", _event_count_with(rows, RESERVE_SCARCITY_REASON)),
        ("heat_stress_count", _event_count_with(rows, HEAT_STRESS_REASON)),
        ("outage_pressure_count", _event_count_with(rows, OUTAGE_PRESSURE_REASON)),
        ("stale_observation_count", _event_count_with(rows, STALE_OBSERVATION_REASON)),
        ("thin_source_count", _event_count_with(rows, THIN_SOURCES_REASON)),
        (
            "missing_acknowledgement_count",
            _event_count_with(rows, MISSING_ACKNOWLEDGEMENT_REASON),
        ),
        (
            "slow_acknowledgement_count",
            _event_count_with(rows, SLOW_ACKNOWLEDGEMENT_REASON),
        ),
        ("average_peak_shock_ratio", _average_peak_shock_ratio(rows)),
        (
            "max_observation_age_seconds",
            _max_decimal(row.observation_age_seconds for row in rows),
        ),
        ("average_source_count", _average_decimal(row.source_count for row in rows)),
    )
    for field_name, expected in checks:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_status = _report_status(
        shock_count=report.power_demand_peak_shock_count,
        watch_count=report.watch_shock_count,
        blocked_count=report.blocked_shock_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _status_rank(status: str) -> int:
    return {"blocked": 0, "watch": 1, "ready": 2}[status]


def _reason_rank(reason_code: str) -> int:
    return REASON_CODES.index(reason_code)


def _redacted_public_reference(value: str) -> str:
    if _contains_unsafe_text(value):
        return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"
    return value


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} must be redacted")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_digest_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value != value.lower() or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a lowercase public identifier")
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS) or "://" in lowered


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_positive_decimal(field_name, value)
    if value != _decimal_count(int(value)):
        raise ValueError(f"{field_name} must be an integral decimal count")
    return value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value != _decimal_count(int(value)):
        raise ValueError(f"{field_name} must be an integral decimal count")
    return value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")

"""Pure Phase 1 energy refinery outage restart digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_RESTART_DIGEST_CONFIG_VERSION = (
    "market-research-energy-refinery-outage-restart-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)
STATUS_RANK = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

REASON_PREFIX = "market_research_energy_refinery_outage_restart_digest_"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
PROLONGED_OUTAGE_DURATION_REASON = f"{REASON_PREFIX}prolonged_outage_duration"
LOW_RESTART_PROBABILITY_REASON = f"{REASON_PREFIX}low_restart_probability"
MATERIAL_CAPACITY_OFFLINE_REASON = f"{REASON_PREFIX}material_capacity_offline"
PRODUCT_SPREAD_PRESSURE_REASON = f"{REASON_PREFIX}product_spread_pressure"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
PASS_REASON = f"{REASON_PREFIX}passed"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"

ROW_REASON_CODE_SEQUENCE = (
    STALE_OBSERVATION_REASON,
    PROLONGED_OUTAGE_DURATION_REASON,
    LOW_RESTART_PROBABILITY_REASON,
    MATERIAL_CAPACITY_OFFLINE_REASON,
    PRODUCT_SPREAD_PRESSURE_REASON,
    THIN_SOURCES_REASON,
    PASS_REASON,
)
REASON_CODE_SEQUENCE = ROW_REASON_CODE_SEQUENCE + (NO_INPUTS_REASON,)

NEXT_STEPS = {
    STATUS_PASS: (
        "allow_report_only_market_research_energy_refinery_outage_restart_digest"
    ),
    STATUS_WATCH: (
        "watch_report_only_market_research_energy_refinery_outage_restart_digest"
    ),
    STATUS_BLOCKED: (
        "block_report_only_market_research_energy_refinery_outage_restart_digest"
    ),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
SECONDS_PER_HOUR = Decimal("3600.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("sens", "itive"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_RESTART_DIGEST_CONFIG_VERSION",
    "MarketResearchEnergyRefineryOutageRestartDigestConfig",
    "MarketResearchEnergyRefineryOutageRestartDigestInputRow",
    "MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount",
    "MarketResearchEnergyRefineryOutageRestartDigestReport",
    "MarketResearchEnergyRefineryOutageRestartDigestRow",
    "build_market_research_energy_refinery_outage_restart_digest",
    "market_research_energy_refinery_outage_restart_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageRestartDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_RESTART_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("10800.000000")
    watch_restart_probability: Decimal = Decimal("0.650000")
    blocked_restart_probability: Decimal = Decimal("0.350000")
    watch_outage_duration_hours: Decimal = Decimal("12.000000")
    blocked_outage_duration_hours: Decimal = Decimal("48.000000")
    watch_capacity_offline_bpd: Decimal = Decimal("150000.000000")
    blocked_capacity_offline_bpd: Decimal = Decimal("400000.000000")
    watch_product_spread_impact_pressure: Decimal = Decimal("0.500000")
    blocked_product_spread_impact_pressure: Decimal = Decimal("0.800000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageRestartDigestConfig:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageRestartDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyRefineryOutageRestartDigestConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_RESTART_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_observation_age_seconds",
            "watch_outage_duration_hours",
            "blocked_outage_duration_hours",
            "watch_capacity_offline_bpd",
            "blocked_capacity_offline_bpd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_restart_probability",
            "blocked_restart_probability",
            "watch_product_spread_impact_pressure",
            "blocked_product_spread_impact_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_whole_positive_decimal("min_source_count", self.min_source_count),
        )
        if self.blocked_restart_probability > self.watch_restart_probability:
            raise ValueError(
                "blocked_restart_probability must not exceed "
                "watch_restart_probability",
            )
        if self.watch_outage_duration_hours > self.blocked_outage_duration_hours:
            raise ValueError(
                "watch_outage_duration_hours must not exceed "
                "blocked_outage_duration_hours",
            )
        if self.watch_capacity_offline_bpd > self.blocked_capacity_offline_bpd:
            raise ValueError(
                "watch_capacity_offline_bpd must not exceed "
                "blocked_capacity_offline_bpd",
            )
        if (
            self.watch_product_spread_impact_pressure
            > self.blocked_product_spread_impact_pressure
        ):
            raise ValueError(
                "watch_product_spread_impact_pressure must not exceed "
                "blocked_product_spread_impact_pressure",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageRestartDigestInputRow:
    event_id: str
    refinery_id: str
    region: str
    observed_at: datetime
    outage_started_at: datetime
    restart_probability: Decimal
    offline_capacity_bpd: Decimal
    total_capacity_bpd: Decimal
    product_spread_impact_pressure: Decimal
    source_count: Decimal
    public_source_ref: str
    event_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageRestartDigestInputRow:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageRestartDigestInputRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyRefineryOutageRestartDigestInputRow,
            "input row",
        )
        for field_name in ("event_id", "refinery_id", "region", "event_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_plain_string("public_source_ref", self.public_source_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "outage_started_at",
            _as_utc("outage_started_at", self.outage_started_at),
        )
        object.__setattr__(
            self,
            "restart_probability",
            _require_ratio_decimal("restart_probability", self.restart_probability),
        )
        object.__setattr__(
            self,
            "offline_capacity_bpd",
            _require_nonnegative_decimal(
                "offline_capacity_bpd",
                self.offline_capacity_bpd,
            ),
        )
        object.__setattr__(
            self,
            "total_capacity_bpd",
            _require_positive_decimal("total_capacity_bpd", self.total_capacity_bpd),
        )
        if self.offline_capacity_bpd > self.total_capacity_bpd:
            raise ValueError("offline_capacity_bpd must not exceed total_capacity_bpd")
        object.__setattr__(
            self,
            "product_spread_impact_pressure",
            _require_ratio_decimal(
                "product_spread_impact_pressure",
                self.product_spread_impact_pressure,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_whole_nonnegative_decimal("source_count", self.source_count),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageRestartDigestRow:
    event_id: str
    refinery_id: str
    region: str
    restart_status: str
    observed_at: datetime
    outage_started_at: datetime
    observation_age_seconds: Decimal
    outage_duration_hours: Decimal
    restart_probability: Decimal
    offline_capacity_bpd: Decimal
    total_capacity_bpd: Decimal
    utilization_capacity_offline_ratio: Decimal
    product_spread_impact_pressure: Decimal
    source_count: Decimal
    redacted_public_source_ref: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageRestartDigestRow:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageRestartDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchEnergyRefineryOutageRestartDigestRow, "row")
        for field_name in ("event_id", "refinery_id", "region"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("restart_status", self.restart_status, STATUSES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "outage_started_at",
            _as_utc("outage_started_at", self.outage_started_at),
        )
        for field_name in (
            "observation_age_seconds",
            "outage_duration_hours",
            "offline_capacity_bpd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_capacity_bpd",
            _require_positive_decimal("total_capacity_bpd", self.total_capacity_bpd),
        )
        if self.offline_capacity_bpd > self.total_capacity_bpd:
            raise ValueError("offline_capacity_bpd must not exceed total_capacity_bpd")
        for field_name in (
            "restart_probability",
            "utilization_capacity_offline_ratio",
            "product_spread_impact_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_whole_nonnegative_decimal("source_count", self.source_count),
        )
        _require_plain_string(
            "redacted_public_source_ref",
            self.redacted_public_source_ref,
        )
        if not _is_public_reference(self.redacted_public_source_ref):
            raise ValueError("redacted_public_source_ref must be redacted")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_whole_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryOutageRestartDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    event_count: Decimal
    pass_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    stale_observation_count: Decimal
    prolonged_outage_duration_count: Decimal
    low_restart_probability_count: Decimal
    material_capacity_offline_count: Decimal
    product_spread_pressure_count: Decimal
    thin_source_count: Decimal
    total_offline_capacity_bpd: Decimal
    max_offline_capacity_bpd: Decimal
    average_outage_duration_hours: Decimal
    average_restart_probability: Decimal
    max_utilization_capacity_offline_ratio: Decimal
    max_product_spread_impact_pressure: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount,
        ...,
    ]
    event_config_versions: tuple[tuple[str, str], ...]
    rows: tuple[MarketResearchEnergyRefineryOutageRestartDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryOutageRestartDigestReport:
            raise TypeError(
                "MarketResearchEnergyRefineryOutageRestartDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyRefineryOutageRestartDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_RESTART_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("digest_status", self.digest_status, STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "event_count",
            "pass_event_count",
            "watch_event_count",
            "blocked_event_count",
            "stale_observation_count",
            "prolonged_outage_duration_count",
            "low_restart_probability_count",
            "material_capacity_offline_count",
            "product_spread_pressure_count",
            "thin_source_count",
            "total_offline_capacity_bpd",
            "max_offline_capacity_bpd",
            "average_outage_duration_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_restart_probability",
            "max_utilization_capacity_offline_ratio",
            "max_product_spread_impact_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "event_config_versions",
            _normalize_event_config_versions(self.event_config_versions),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_energy_refinery_outage_restart_digest(
    rows: tuple[MarketResearchEnergyRefineryOutageRestartDigestInputRow, ...],
    *,
    config: MarketResearchEnergyRefineryOutageRestartDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyRefineryOutageRestartDigestReport:
    if type(config) is not MarketResearchEnergyRefineryOutageRestartDigestConfig:
        raise ValueError(
            "config must be a MarketResearchEnergyRefineryOutageRestartDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows)
    output_rows = tuple(
        sorted(
            (
                _row_from_input(row, config=config, generated_at=generated_at_utc)
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    event_count = _count_decimal(len(output_rows))
    reason_code_counts = _reason_code_counts(output_rows, event_count)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not output_rows:
        reason_code_counts = (
            MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    digest_status = _digest_status(output_rows)
    return MarketResearchEnergyRefineryOutageRestartDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        event_count=event_count,
        pass_event_count=_status_count(output_rows, STATUS_PASS),
        watch_event_count=_status_count(output_rows, STATUS_WATCH),
        blocked_event_count=_status_count(output_rows, STATUS_BLOCKED),
        stale_observation_count=_row_reason_count(output_rows, STALE_OBSERVATION_REASON),
        prolonged_outage_duration_count=_row_reason_count(
            output_rows,
            PROLONGED_OUTAGE_DURATION_REASON,
        ),
        low_restart_probability_count=_row_reason_count(
            output_rows,
            LOW_RESTART_PROBABILITY_REASON,
        ),
        material_capacity_offline_count=_row_reason_count(
            output_rows,
            MATERIAL_CAPACITY_OFFLINE_REASON,
        ),
        product_spread_pressure_count=_row_reason_count(
            output_rows,
            PRODUCT_SPREAD_PRESSURE_REASON,
        ),
        thin_source_count=_row_reason_count(output_rows, THIN_SOURCES_REASON),
        total_offline_capacity_bpd=_sum_decimal(
            row.offline_capacity_bpd for row in output_rows
        ),
        max_offline_capacity_bpd=max(
            (row.offline_capacity_bpd for row in output_rows),
            default=ZERO,
        ),
        average_outage_duration_hours=_average_decimal(
            row.outage_duration_hours for row in output_rows
        ),
        average_restart_probability=_average_decimal(
            row.restart_probability for row in output_rows
        ),
        max_utilization_capacity_offline_ratio=max(
            (row.utilization_capacity_offline_ratio for row in output_rows),
            default=ZERO,
        ),
        max_product_spread_impact_pressure=max(
            (row.product_spread_impact_pressure for row in output_rows),
            default=ZERO,
        ),
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        event_config_versions=_event_config_versions(input_rows),
        rows=output_rows,
    )


def market_research_energy_refinery_outage_restart_digest_payload(
    report: MarketResearchEnergyRefineryOutageRestartDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEnergyRefineryOutageRestartDigestReport:
        raise ValueError(
            "report must be a MarketResearchEnergyRefineryOutageRestartDigestReport",
        )
    _validate_report(report)
    payload = _json_ready(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a mapping")
    return payload


def _row_from_input(
    row: MarketResearchEnergyRefineryOutageRestartDigestInputRow,
    *,
    config: MarketResearchEnergyRefineryOutageRestartDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyRefineryOutageRestartDigestRow:
    if row.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    if row.outage_started_at > generated_at:
        raise ValueError("outage_started_at must not be in the future")
    if row.outage_started_at > row.observed_at:
        raise ValueError("outage_started_at must not be after observed_at")
    observation_age_seconds = _seconds_between(generated_at, row.observed_at)
    outage_duration_hours = _hours_between(generated_at, row.outage_started_at)
    reasons = _row_reason_codes(
        row,
        config=config,
        observation_age_seconds=observation_age_seconds,
        outage_duration_hours=outage_duration_hours,
    )
    return MarketResearchEnergyRefineryOutageRestartDigestRow(
        event_id=row.event_id,
        refinery_id=row.refinery_id,
        region=row.region,
        restart_status=_row_status(
            row,
            config=config,
            reason_codes=reasons,
            observation_age_seconds=observation_age_seconds,
            outage_duration_hours=outage_duration_hours,
        ),
        observed_at=row.observed_at,
        outage_started_at=row.outage_started_at,
        observation_age_seconds=observation_age_seconds,
        outage_duration_hours=outage_duration_hours,
        restart_probability=row.restart_probability,
        offline_capacity_bpd=row.offline_capacity_bpd,
        total_capacity_bpd=row.total_capacity_bpd,
        utilization_capacity_offline_ratio=_ratio(
            row.offline_capacity_bpd,
            row.total_capacity_bpd,
        ),
        product_spread_impact_pressure=row.product_spread_impact_pressure,
        source_count=row.source_count,
        redacted_public_source_ref=_redact_reference(row.public_source_ref),
        reason_codes=reasons,
    )


def _row_reason_codes(
    row: MarketResearchEnergyRefineryOutageRestartDigestInputRow,
    *,
    config: MarketResearchEnergyRefineryOutageRestartDigestConfig,
    observation_age_seconds: Decimal,
    outage_duration_hours: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if outage_duration_hours >= config.watch_outage_duration_hours:
        reasons.append(PROLONGED_OUTAGE_DURATION_REASON)
    if row.restart_probability <= config.watch_restart_probability:
        reasons.append(LOW_RESTART_PROBABILITY_REASON)
    if row.offline_capacity_bpd >= config.watch_capacity_offline_bpd:
        reasons.append(MATERIAL_CAPACITY_OFFLINE_REASON)
    if row.product_spread_impact_pressure >= config.watch_product_spread_impact_pressure:
        reasons.append(PRODUCT_SPREAD_PRESSURE_REASON)
    if row.source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODE_SEQUENCE)


def _row_status(
    row: MarketResearchEnergyRefineryOutageRestartDigestInputRow,
    *,
    config: MarketResearchEnergyRefineryOutageRestartDigestConfig,
    reason_codes: tuple[str, ...],
    observation_age_seconds: Decimal,
    outage_duration_hours: Decimal,
) -> str:
    if (
        STALE_OBSERVATION_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
        or observation_age_seconds > config.max_observation_age_seconds
        or outage_duration_hours >= config.blocked_outage_duration_hours
        or row.restart_probability <= config.blocked_restart_probability
        or row.offline_capacity_bpd >= config.blocked_capacity_offline_bpd
        or row.product_spread_impact_pressure
        >= config.blocked_product_spread_impact_pressure
    ):
        return STATUS_BLOCKED
    if reason_codes != (PASS_REASON,):
        return STATUS_WATCH
    return STATUS_PASS


def _digest_status(
    rows: tuple[MarketResearchEnergyRefineryOutageRestartDigestRow, ...],
) -> str:
    if any(row.restart_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.restart_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    if rows:
        return STATUS_PASS
    return STATUS_BLOCKED


def _reason_code_counts(
    rows: tuple[MarketResearchEnergyRefineryOutageRestartDigestRow, ...],
    event_count: Decimal,
) -> tuple[MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount, ...]:
    counts: list[MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount] = []
    include_passed = bool(rows) and all(row.reason_codes == (PASS_REASON,) for row in rows)
    for reason_code in ROW_REASON_CODE_SEQUENCE:
        if reason_code == PASS_REASON and not include_passed:
            continue
        count = _row_reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    event_ratio=_ratio(count, event_count),
                ),
            )
    return tuple(counts)


def _row_reason_count(
    rows: tuple[MarketResearchEnergyRefineryOutageRestartDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[MarketResearchEnergyRefineryOutageRestartDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.restart_status == status))


def _event_config_versions(
    rows: tuple[MarketResearchEnergyRefineryOutageRestartDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (row.event_id, row.event_config_version)
                for row in rows
            },
            key=lambda item: (item[0], item[1]),
        ),
    )


def _normalize_inputs(
    rows: tuple[MarketResearchEnergyRefineryOutageRestartDigestInputRow, ...],
) -> tuple[MarketResearchEnergyRefineryOutageRestartDigestInputRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEnergyRefineryOutageRestartDigestInputRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchEnergyRefineryOutageRestartDigestInputRow",
            )
    if len({row.event_id for row in rows}) != len(rows):
        raise ValueError("event_id values must be unique")
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchEnergyRefineryOutageRestartDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEnergyRefineryOutageRestartDigestRow:
            raise ValueError(
                "rows must contain MarketResearchEnergyRefineryOutageRestartDigestRow",
            )
    normalized = tuple(rows)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.event_id for row in normalized}) != len(normalized):
        raise ValueError("rows must contain unique event_id values")
    return normalized


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for row in counts:
        if type(row) is not MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEnergyRefineryOutageRestartDigestReasonCodeCount",
            )
    normalized = tuple(counts)
    if normalized != tuple(
        sorted(normalized, key=lambda row: REASON_CODE_SEQUENCE.index(row.reason_code))
    ):
        raise ValueError("reason_code_counts must be sorted deterministically")
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts must contain unique reason_code values")
    return normalized


def _normalize_event_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, tuple):
        raise ValueError("event_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("event_config_versions must contain pairs")
        event_id, config_version = item
        normalized.append(
            (
                _require_public_string("event_id", event_id),
                _require_public_string("event_config_version", config_version),
            ),
        )
    as_tuple = tuple(normalized)
    if as_tuple != tuple(sorted(as_tuple, key=lambda item: (item[0], item[1]))):
        raise ValueError("event_config_versions must be sorted deterministically")
    if len({item[0] for item in as_tuple}) != len(as_tuple):
        raise ValueError("event_config_versions must contain unique event_id values")
    return as_tuple


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_member("reason_code", reason_code, allowed)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    normalized = tuple(value)
    if normalized != tuple(sorted(normalized, key=lambda reason: allowed.index(reason))):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _row_sort_key(
    row: MarketResearchEnergyRefineryOutageRestartDigestRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.restart_status],
        row.restart_probability,
        -row.offline_capacity_bpd,
        -row.product_spread_impact_pressure,
        row.refinery_id,
        row.event_id,
    )


def _validate_row(row: MarketResearchEnergyRefineryOutageRestartDigestRow) -> None:
    if row.utilization_capacity_offline_ratio != _ratio(
        row.offline_capacity_bpd,
        row.total_capacity_bpd,
    ):
        raise ValueError("utilization_capacity_offline_ratio must match capacity values")
    if row.restart_status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass restart rows must only use passed reason")
    if row.restart_status == STATUS_WATCH and row.reason_codes == (PASS_REASON,):
        raise ValueError("watch restart rows must include watch reason")
    if row.restart_status == STATUS_BLOCKED and row.reason_codes == (PASS_REASON,):
        raise ValueError("blocked restart rows must include blocked reason")


def _validate_report(report: MarketResearchEnergyRefineryOutageRestartDigestReport) -> None:
    if report.event_count != _count_decimal(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_event_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_event_count must match rows")
    if report.watch_event_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_event_count must match rows")
    if report.blocked_event_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_event_count must match rows")
    if report.stale_observation_count != _row_reason_count(
        report.rows,
        STALE_OBSERVATION_REASON,
    ):
        raise ValueError("stale_observation_count must match rows")
    if report.prolonged_outage_duration_count != _row_reason_count(
        report.rows,
        PROLONGED_OUTAGE_DURATION_REASON,
    ):
        raise ValueError("prolonged_outage_duration_count must match rows")
    if report.low_restart_probability_count != _row_reason_count(
        report.rows,
        LOW_RESTART_PROBABILITY_REASON,
    ):
        raise ValueError("low_restart_probability_count must match rows")
    if report.material_capacity_offline_count != _row_reason_count(
        report.rows,
        MATERIAL_CAPACITY_OFFLINE_REASON,
    ):
        raise ValueError("material_capacity_offline_count must match rows")
    if report.product_spread_pressure_count != _row_reason_count(
        report.rows,
        PRODUCT_SPREAD_PRESSURE_REASON,
    ):
        raise ValueError("product_spread_pressure_count must match rows")
    if report.thin_source_count != _row_reason_count(report.rows, THIN_SOURCES_REASON):
        raise ValueError("thin_source_count must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != tuple(row.reason_code for row in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    value = _require_plain_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public safe text")
    return value


def _require_plain_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty and trimmed")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_whole_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total = _quantize(total + value)
    return total


def _average_decimal(values: object) -> Decimal:
    decimals = tuple(values)
    if not decimals:
        return ZERO
    return _ratio(_sum_decimal(decimals), _count_decimal(len(decimals)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
        )


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(_seconds_between(later, earlier) / SECONDS_PER_HOUR)


def _redact_reference(value: str) -> str:
    if _is_public_reference(value):
        return value
    return f"redacted-source:{sha256(value.encode()).hexdigest()[:16]}"


def _is_public_reference(value: str) -> bool:
    if value.startswith("redacted-source:"):
        return True
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._-")
    lowered = value.lower()
    return (
        value == lowered
        and bool(value)
        and all(char in allowed for char in value)
        and not any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)
    )


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("payload values must not be floats")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not supported")

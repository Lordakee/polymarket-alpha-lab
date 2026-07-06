"""Pure Phase 1 energy gas storage weather beta digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from types import MappingProxyType
from typing import Any


DEFAULT_ENERGY_GAS_STORAGE_WEATHER_BETA_DIGEST_CONFIG_VERSION = (
    "market-research-energy-gas-storage-weather-beta-digest-v0"
)

INPUT_REASON_CODES = (
    "gas_storage_weather_beta_storage_reported",
    "gas_storage_weather_beta_weather_revision",
    "gas_storage_weather_beta_source_latency_gap",
)
ROW_REASON_CODES = (
    "gas_storage_weather_beta_draw_blocked",
    "gas_storage_weather_beta_draw_watch",
    "gas_storage_weather_beta_hdd_blocked",
    "gas_storage_weather_beta_hdd_watch",
    "gas_storage_weather_beta_freeze_blocked",
    "gas_storage_weather_beta_freeze_watch",
    "gas_storage_weather_beta_low_confidence",
    "gas_storage_weather_beta_revision_present",
    "gas_storage_weather_beta_inline",
)
REPORT_REASON_CODES = (
    "gas_storage_weather_beta_blocked_present",
    "gas_storage_weather_beta_watch_present",
    "gas_storage_weather_beta_draw_pressure_present",
    "gas_storage_weather_beta_weather_pressure_present",
    "gas_storage_weather_beta_freeze_risk_present",
    "gas_storage_weather_beta_low_confidence_present",
    "gas_storage_weather_beta_revision_present",
    "gas_storage_weather_beta_clear",
    "gas_storage_weather_beta_digest_empty",
)
STORAGE_STATUSES = ("pass", "watch", "blocked")
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_ENERGY_GAS_STORAGE_WEATHER_BETA_DIGEST_CONFIG_VERSION",
    "EnergyGasStorageWeatherBetaDigestConfig",
    "EnergyGasStorageWeatherBetaObservation",
    "EnergyGasStorageWeatherBetaDigestRow",
    "EnergyGasStorageWeatherBetaReasonCodeCount",
    "EnergyGasStorageWeatherBetaDigestReport",
    "build_market_research_energy_gas_storage_weather_beta_digest",
    "market_research_energy_gas_storage_weather_beta_digest_payload",
)


@dataclass(frozen=True)
class EnergyGasStorageWeatherBetaDigestConfig:
    config_version: str = DEFAULT_ENERGY_GAS_STORAGE_WEATHER_BETA_DIGEST_CONFIG_VERSION
    watch_draw_surprise_bcf: Decimal = Decimal("20.000000")
    blocked_draw_surprise_bcf: Decimal = Decimal("50.000000")
    watch_hdd_anomaly: Decimal = Decimal("5.000000")
    blocked_hdd_anomaly: Decimal = Decimal("12.000000")
    watch_pipeline_freeze_risk: Decimal = Decimal("0.500000")
    blocked_pipeline_freeze_risk: Decimal = Decimal("0.650000")
    min_weather_confidence: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EnergyGasStorageWeatherBetaDigestConfig:
            raise TypeError(
                "EnergyGasStorageWeatherBetaDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, EnergyGasStorageWeatherBetaDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_ENERGY_GAS_STORAGE_WEATHER_BETA_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_draw_surprise_bcf",
            "blocked_draw_surprise_bcf",
            "watch_hdd_anomaly",
            "blocked_hdd_anomaly",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_pipeline_freeze_risk",
            "blocked_pipeline_freeze_risk",
            "min_weather_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_draw_surprise_bcf > self.blocked_draw_surprise_bcf:
            raise ValueError(
                "watch_draw_surprise_bcf must not exceed blocked_draw_surprise_bcf",
            )
        if self.watch_hdd_anomaly > self.blocked_hdd_anomaly:
            raise ValueError("watch_hdd_anomaly must not exceed blocked_hdd_anomaly")
        if self.watch_pipeline_freeze_risk > self.blocked_pipeline_freeze_risk:
            raise ValueError(
                "watch_pipeline_freeze_risk must not exceed blocked_pipeline_freeze_risk",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class EnergyGasStorageWeatherBetaObservation:
    source_id: str
    region_id: str
    storage_hub_id: str
    storage_draw_bcf: Decimal
    normal_draw_bcf: Decimal
    hdd_anomaly: Decimal
    weather_confidence: Decimal
    pipeline_freeze_risk: Decimal
    source_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EnergyGasStorageWeatherBetaObservation:
            raise TypeError(
                "EnergyGasStorageWeatherBetaObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, EnergyGasStorageWeatherBetaObservation, "observation")
        for field_name in ("source_id", "region_id", "storage_hub_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("storage_draw_bcf", "normal_draw_bcf", "hdd_anomaly"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("weather_confidence", "pipeline_freeze_risk"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class EnergyGasStorageWeatherBetaDigestRow:
    source_id: str
    region_id: str
    storage_hub_id: str
    storage_draw_bcf: Decimal
    normal_draw_bcf: Decimal
    draw_surprise_bcf: Decimal
    draw_pressure_bcf: Decimal
    hdd_anomaly: Decimal
    weather_confidence: Decimal
    pipeline_freeze_risk: Decimal
    source_timestamp: datetime
    storage_status: str
    weather_beta_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EnergyGasStorageWeatherBetaDigestRow:
            raise TypeError(
                "EnergyGasStorageWeatherBetaDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, EnergyGasStorageWeatherBetaDigestRow, "row")
        for field_name in ("source_id", "region_id", "storage_hub_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "storage_draw_bcf",
            "normal_draw_bcf",
            "draw_pressure_bcf",
            "hdd_anomaly",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "draw_surprise_bcf",
            _require_decimal("draw_surprise_bcf", self.draw_surprise_bcf),
        )
        for field_name in (
            "weather_confidence",
            "pipeline_freeze_risk",
            "weather_beta_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        _require_member("storage_status", self.storage_status, STORAGE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class EnergyGasStorageWeatherBetaReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EnergyGasStorageWeatherBetaReasonCodeCount:
            raise TypeError(
                "EnergyGasStorageWeatherBetaReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            EnergyGasStorageWeatherBetaReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class EnergyGasStorageWeatherBetaDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    max_draw_surprise_bcf: Decimal
    average_draw_surprise_bcf: Decimal
    max_hdd_anomaly: Decimal
    max_pipeline_freeze_risk: Decimal
    weather_beta_pressure_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[EnergyGasStorageWeatherBetaDigestRow, ...]
    reason_code_counts: tuple[EnergyGasStorageWeatherBetaReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EnergyGasStorageWeatherBetaDigestReport:
            raise TypeError(
                "EnergyGasStorageWeatherBetaDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, EnergyGasStorageWeatherBetaDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_ENERGY_GAS_STORAGE_WEATHER_BETA_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "max_draw_surprise_bcf",
            "max_hdd_anomaly",
            "max_pipeline_freeze_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_draw_surprise_bcf",
            _require_decimal("average_draw_surprise_bcf", self.average_draw_surprise_bcf),
        )
        object.__setattr__(
            self,
            "weather_beta_pressure_score",
            _require_ratio(
                "weather_beta_pressure_score",
                self.weather_beta_pressure_score,
            ),
        )
        _require_member("digest_status", self.digest_status, STORAGE_STATUSES)
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


def build_market_research_energy_gas_storage_weather_beta_digest(
    observations: tuple[EnergyGasStorageWeatherBetaObservation, ...],
    *,
    config: EnergyGasStorageWeatherBetaDigestConfig,
    generated_at: datetime,
) -> EnergyGasStorageWeatherBetaDigestReport:
    if type(config) is not EnergyGasStorageWeatherBetaDigestConfig:
        raise ValueError("config must be exactly EnergyGasStorageWeatherBetaDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    for observation in normalized:
        if observation.source_timestamp > generated_at_utc:
            raise ValueError("source_timestamp must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    return EnergyGasStorageWeatherBetaDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        max_draw_surprise_bcf=_max_decimal(
            tuple(row.draw_pressure_bcf for row in rows),
        ),
        average_draw_surprise_bcf=_ratio(
            _sum_decimal(tuple(row.draw_surprise_bcf for row in rows)),
            row_count,
        ),
        max_hdd_anomaly=_max_decimal(tuple(row.hdd_anomaly for row in rows)),
        max_pipeline_freeze_risk=_max_decimal(
            tuple(row.pipeline_freeze_risk for row in rows),
        ),
        weather_beta_pressure_score=_max_decimal(
            tuple(row.weather_beta_pressure_score for row in rows),
        ),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_energy_gas_storage_weather_beta_digest_payload(
    report: EnergyGasStorageWeatherBetaDigestReport,
) -> MappingProxyType:
    if type(report) is not EnergyGasStorageWeatherBetaDigestReport:
        raise ValueError("report must be exactly EnergyGasStorageWeatherBetaDigestReport")
    revalidated = _revalidate_payload_value(report, "report")
    return _payload_value(revalidated)


def _row_from_observation(
    observation: EnergyGasStorageWeatherBetaObservation,
    *,
    config: EnergyGasStorageWeatherBetaDigestConfig,
) -> EnergyGasStorageWeatherBetaDigestRow:
    draw_surprise_bcf = _quantize_decimal(
        observation.storage_draw_bcf - observation.normal_draw_bcf,
    )
    draw_pressure_bcf = _positive_part(draw_surprise_bcf)
    storage_status = _row_status(
        draw_pressure_bcf=draw_pressure_bcf,
        hdd_anomaly=observation.hdd_anomaly,
        pipeline_freeze_risk=observation.pipeline_freeze_risk,
        weather_confidence=observation.weather_confidence,
        config=config,
    )
    return EnergyGasStorageWeatherBetaDigestRow(
        source_id=observation.source_id,
        region_id=observation.region_id,
        storage_hub_id=observation.storage_hub_id,
        storage_draw_bcf=observation.storage_draw_bcf,
        normal_draw_bcf=observation.normal_draw_bcf,
        draw_surprise_bcf=draw_surprise_bcf,
        draw_pressure_bcf=draw_pressure_bcf,
        hdd_anomaly=observation.hdd_anomaly,
        weather_confidence=observation.weather_confidence,
        pipeline_freeze_risk=observation.pipeline_freeze_risk,
        source_timestamp=observation.source_timestamp,
        storage_status=storage_status,
        weather_beta_pressure_score=_row_pressure_score(
            draw_pressure_bcf=draw_pressure_bcf,
            hdd_anomaly=observation.hdd_anomaly,
            pipeline_freeze_risk=observation.pipeline_freeze_risk,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            observation,
            storage_status=storage_status,
            draw_pressure_bcf=draw_pressure_bcf,
            config=config,
        ),
    )


def _row_status(
    *,
    draw_pressure_bcf: Decimal,
    hdd_anomaly: Decimal,
    pipeline_freeze_risk: Decimal,
    weather_confidence: Decimal,
    config: EnergyGasStorageWeatherBetaDigestConfig,
) -> str:
    if (
        draw_pressure_bcf >= config.blocked_draw_surprise_bcf
        or hdd_anomaly >= config.blocked_hdd_anomaly
        or pipeline_freeze_risk >= config.blocked_pipeline_freeze_risk
    ):
        return "blocked"
    if (
        draw_pressure_bcf >= config.watch_draw_surprise_bcf
        or hdd_anomaly >= config.watch_hdd_anomaly
        or pipeline_freeze_risk >= config.watch_pipeline_freeze_risk
        or weather_confidence < config.min_weather_confidence
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: EnergyGasStorageWeatherBetaObservation,
    *,
    storage_status: str,
    draw_pressure_bcf: Decimal,
    config: EnergyGasStorageWeatherBetaDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if draw_pressure_bcf >= config.blocked_draw_surprise_bcf:
        reason_codes.append("gas_storage_weather_beta_draw_blocked")
    elif draw_pressure_bcf >= config.watch_draw_surprise_bcf:
        reason_codes.append("gas_storage_weather_beta_draw_watch")

    if observation.hdd_anomaly >= config.blocked_hdd_anomaly:
        reason_codes.append("gas_storage_weather_beta_hdd_blocked")
    elif observation.hdd_anomaly >= config.watch_hdd_anomaly:
        reason_codes.append("gas_storage_weather_beta_hdd_watch")

    if observation.pipeline_freeze_risk >= config.blocked_pipeline_freeze_risk:
        reason_codes.append("gas_storage_weather_beta_freeze_blocked")
    elif observation.pipeline_freeze_risk >= config.watch_pipeline_freeze_risk:
        reason_codes.append("gas_storage_weather_beta_freeze_watch")

    if observation.weather_confidence < config.min_weather_confidence:
        reason_codes.append("gas_storage_weather_beta_low_confidence")
    if "gas_storage_weather_beta_weather_revision" in observation.upstream_reason_codes:
        reason_codes.append("gas_storage_weather_beta_revision_present")
    if not reason_codes and storage_status == "pass":
        reason_codes.append("gas_storage_weather_beta_inline")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[EnergyGasStorageWeatherBetaDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("gas_storage_weather_beta_digest_empty",)
    reason_codes: list[str] = []
    if any(row.storage_status == "blocked" for row in rows):
        reason_codes.append("gas_storage_weather_beta_blocked_present")
    if any(row.storage_status == "watch" for row in rows):
        reason_codes.append("gas_storage_weather_beta_watch_present")
    if any(
        _row_has_any(
            row,
            (
                "gas_storage_weather_beta_draw_blocked",
                "gas_storage_weather_beta_draw_watch",
            ),
        )
        for row in rows
    ):
        reason_codes.append("gas_storage_weather_beta_draw_pressure_present")
    if any(
        _row_has_any(
            row,
            (
                "gas_storage_weather_beta_hdd_blocked",
                "gas_storage_weather_beta_hdd_watch",
            ),
        )
        for row in rows
    ):
        reason_codes.append("gas_storage_weather_beta_weather_pressure_present")
    if any(
        _row_has_any(
            row,
            (
                "gas_storage_weather_beta_freeze_blocked",
                "gas_storage_weather_beta_freeze_watch",
            ),
        )
        for row in rows
    ):
        reason_codes.append("gas_storage_weather_beta_freeze_risk_present")
    if any("gas_storage_weather_beta_low_confidence" in row.reason_codes for row in rows):
        reason_codes.append("gas_storage_weather_beta_low_confidence_present")
    if any("gas_storage_weather_beta_revision_present" in row.reason_codes for row in rows):
        reason_codes.append("gas_storage_weather_beta_revision_present")
    if not reason_codes:
        reason_codes.append("gas_storage_weather_beta_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[EnergyGasStorageWeatherBetaDigestRow, ...],
) -> tuple[EnergyGasStorageWeatherBetaReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("gas_storage_weather_beta_digest_empty",):
        return (
            EnergyGasStorageWeatherBetaReasonCodeCount(
                reason_code="gas_storage_weather_beta_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        EnergyGasStorageWeatherBetaReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[EnergyGasStorageWeatherBetaDigestRow, ...],
) -> Decimal:
    if reason_code == "gas_storage_weather_beta_blocked_present":
        return _status_count(rows, "blocked")
    if reason_code == "gas_storage_weather_beta_watch_present":
        return _status_count(rows, "watch")
    if reason_code == "gas_storage_weather_beta_draw_pressure_present":
        return _row_reason_count(
            rows,
            (
                "gas_storage_weather_beta_draw_blocked",
                "gas_storage_weather_beta_draw_watch",
            ),
        )
    if reason_code == "gas_storage_weather_beta_weather_pressure_present":
        return _row_reason_count(
            rows,
            (
                "gas_storage_weather_beta_hdd_blocked",
                "gas_storage_weather_beta_hdd_watch",
            ),
        )
    if reason_code == "gas_storage_weather_beta_freeze_risk_present":
        return _row_reason_count(
            rows,
            (
                "gas_storage_weather_beta_freeze_blocked",
                "gas_storage_weather_beta_freeze_watch",
            ),
        )
    if reason_code == "gas_storage_weather_beta_low_confidence_present":
        return _row_reason_count(rows, ("gas_storage_weather_beta_low_confidence",))
    if reason_code == "gas_storage_weather_beta_revision_present":
        return _row_reason_count(rows, ("gas_storage_weather_beta_revision_present",))
    if reason_code == "gas_storage_weather_beta_clear":
        return _status_count(rows, "pass")
    if reason_code == "gas_storage_weather_beta_digest_empty":
        return ONE
    raise ValueError("reason_code must be supported")


def _digest_status(rows: tuple[EnergyGasStorageWeatherBetaDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.storage_status == "blocked" for row in rows):
        return "blocked"
    if any(row.storage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_energy_gas_storage_weather_beta_screening"
    if status == "watch":
        return "monitor_report_only_energy_gas_storage_weather_beta_screening"
    return "block_report_only_energy_gas_storage_weather_beta_screening"


def _row_pressure_score(
    *,
    draw_pressure_bcf: Decimal,
    hdd_anomaly: Decimal,
    pipeline_freeze_risk: Decimal,
    config: EnergyGasStorageWeatherBetaDigestConfig,
) -> Decimal:
    return _max_decimal(
        (
            _capped_ratio(draw_pressure_bcf, config.blocked_draw_surprise_bcf),
            _capped_ratio(hdd_anomaly, config.blocked_hdd_anomaly),
            pipeline_freeze_risk,
        ),
    )


def _validate_row(row: EnergyGasStorageWeatherBetaDigestRow) -> None:
    expected_draw_surprise = _quantize_decimal(
        row.storage_draw_bcf - row.normal_draw_bcf,
    )
    if row.draw_surprise_bcf != expected_draw_surprise:
        raise ValueError("draw_surprise_bcf must match storage_draw_bcf and normal_draw_bcf")
    if row.draw_pressure_bcf != _positive_part(row.draw_surprise_bcf):
        raise ValueError("draw_pressure_bcf must match draw_surprise_bcf")
    _validate_row_reason_shape(row)


def _validate_row_reason_shape(row: EnergyGasStorageWeatherBetaDigestRow) -> None:
    blocked_reasons = (
        "gas_storage_weather_beta_draw_blocked",
        "gas_storage_weather_beta_hdd_blocked",
        "gas_storage_weather_beta_freeze_blocked",
    )
    watch_reasons = (
        "gas_storage_weather_beta_draw_watch",
        "gas_storage_weather_beta_hdd_watch",
        "gas_storage_weather_beta_freeze_watch",
        "gas_storage_weather_beta_low_confidence",
    )
    has_blocked_reason = _row_has_any(row, blocked_reasons)
    has_watch_reason = _row_has_any(row, watch_reasons)
    has_inline_reason = "gas_storage_weather_beta_inline" in row.reason_codes
    has_revision_reason = "gas_storage_weather_beta_revision_present" in row.reason_codes
    if has_inline_reason and len(row.reason_codes) != 1:
        raise ValueError("reason_codes must match row fields")
    if row.storage_status == "pass":
        allowed_pass_shapes = (
            ("gas_storage_weather_beta_inline",),
            ("gas_storage_weather_beta_revision_present",),
        )
        if row.reason_codes not in allowed_pass_shapes:
            raise ValueError("reason_codes must match row fields")
        return
    if row.storage_status == "watch":
        if has_blocked_reason or has_inline_reason or not has_watch_reason:
            raise ValueError("reason_codes must match row fields")
        return
    if not has_blocked_reason or has_inline_reason:
        raise ValueError("reason_codes must match row fields")
    if has_revision_reason and len(row.reason_codes) == 1:
        raise ValueError("reason_codes must match row fields")


def _validate_report(report: EnergyGasStorageWeatherBetaDigestReport) -> None:
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
    if report.max_draw_surprise_bcf != _max_decimal(
        tuple(row.draw_pressure_bcf for row in report.rows),
    ):
        raise ValueError("max_draw_surprise_bcf must match rows")
    if report.average_draw_surprise_bcf != _ratio(
        _sum_decimal(tuple(row.draw_surprise_bcf for row in report.rows)),
        report.row_count,
    ):
        raise ValueError("average_draw_surprise_bcf must match rows")
    if report.max_hdd_anomaly != _max_decimal(tuple(row.hdd_anomaly for row in report.rows)):
        raise ValueError("max_hdd_anomaly must match rows")
    if report.max_pipeline_freeze_risk != _max_decimal(
        tuple(row.pipeline_freeze_risk for row in report.rows),
    ):
        raise ValueError("max_pipeline_freeze_risk must match rows")
    if report.weather_beta_pressure_score != _max_decimal(
        tuple(row.weather_beta_pressure_score for row in report.rows),
    ):
        raise ValueError("weather_beta_pressure_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: object,
) -> tuple[EnergyGasStorageWeatherBetaObservation, ...]:
    if type(observations) is not tuple:
        raise ValueError("observations must be a tuple")
    seen_source_ids: set[str] = set()
    normalized: list[EnergyGasStorageWeatherBetaObservation] = []
    for observation in observations:
        if type(observation) is not EnergyGasStorageWeatherBetaObservation:
            raise ValueError(
                "observations must contain EnergyGasStorageWeatherBetaObservation",
            )
        revalidated = _revalidate_payload_value(observation, "observation")
        if type(revalidated) is not EnergyGasStorageWeatherBetaObservation:
            raise ValueError(
                "observations must contain EnergyGasStorageWeatherBetaObservation",
            )
        if revalidated.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(revalidated.source_id)
        normalized.append(revalidated)
    return tuple(normalized)


def _normalize_rows(value: object) -> tuple[EnergyGasStorageWeatherBetaDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_source_ids: set[str] = set()
    for row in value:
        if type(row) is not EnergyGasStorageWeatherBetaDigestRow:
            raise ValueError("rows must contain EnergyGasStorageWeatherBetaDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[EnergyGasStorageWeatherBetaReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not EnergyGasStorageWeatherBetaReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain EnergyGasStorageWeatherBetaReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    if value != tuple(sorted(value, key=lambda item: REPORT_REASON_CODES.index(item.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_member("reason_code", item, allowed)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    deterministic = tuple(sorted(value, key=lambda item: allowed.index(item)))
    if value != deterministic:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return value


def _row_sort_key(
    row: EnergyGasStorageWeatherBetaDigestRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.storage_status],
        -row.weather_beta_pressure_score,
        row.region_id,
        row.storage_hub_id,
        row.source_id,
    )


def _status_count(
    rows: tuple[EnergyGasStorageWeatherBetaDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.storage_status == status))


def _row_reason_count(
    rows: tuple[EnergyGasStorageWeatherBetaDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if _row_has_any(row, reason_codes)))


def _row_has_any(
    row: EnergyGasStorageWeatherBetaDigestRow,
    reason_codes: tuple[str, ...],
) -> bool:
    return any(reason_code in row.reason_codes for reason_code in reason_codes)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
    return _quantize_decimal(max(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _ratio(numerator, denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _positive_part(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    return _quantize_decimal(value)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


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


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
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
    if value.as_tuple().exponent != -6 or (value.is_zero() and value.is_signed()):
        raise ValueError(f"{field_name} must use exactly six decimal places")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        result = value.quantize(QUANTUM)
    if result.is_zero():
        return ZERO
    return result


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_payload_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must already be UTC")
    return value


ZERO_TIME_OFFSET = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
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


def _revalidate_payload_value(value: object, field_name: str) -> object:
    if _is_known_dataclass_instance(value):
        kwargs = {
            field.name: _revalidate_payload_value(getattr(value, field.name), field.name)
            for field in fields(value)
        }
        return type(value)(**kwargs)
    if type(value) is tuple:
        return tuple(_revalidate_payload_value(item, field_name) for item in value)
    if type(value) is Decimal:
        return _require_decimal(field_name, value)
    if type(value) is datetime:
        return _require_payload_utc(field_name, value)
    if type(value) in (str, bool):
        return value
    raise ValueError(f"{field_name} has unsupported payload value")


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return MappingProxyType(
            {
                field.name: _payload_value(getattr(value, field.name))
                for field in fields(value)
            },
        )
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        _require_payload_utc("datetime", value)
        return value.isoformat()
    if type(value) is tuple:
        return tuple(_payload_value(item) for item in value)
    return value


def _is_known_dataclass_instance(value: object) -> bool:
    return type(value) in (
        EnergyGasStorageWeatherBetaDigestConfig,
        EnergyGasStorageWeatherBetaObservation,
        EnergyGasStorageWeatherBetaDigestRow,
        EnergyGasStorageWeatherBetaReasonCodeCount,
        EnergyGasStorageWeatherBetaDigestReport,
    )

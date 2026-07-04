from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_CONFIG_VERSION = "energy_pipeline_pressure_drop_digest.v1"
PHASE_NAME = "phase_1_market_research"

_ZERO = Decimal("0")
_ONE = Decimal("1")
_SCORE_QUANT = Decimal("0.000001")

_PRESSURE_WEIGHT = Decimal("0.400000")
_FLOW_WEIGHT = Decimal("0.200000")
_CAPACITY_WEIGHT = Decimal("0.200000")
_REPAIR_WEIGHT = Decimal("0.100000")
_CONFIDENCE_WEIGHT = Decimal("0.100000")

_REASON_CODE_ORDER = (
    "no_pressure_drop_observations",
    "pressure_drop_severe",
    "pressure_drop_elevated",
    "throughput_drop_elevated",
    "capacity_at_risk",
    "prolonged_repair_window",
    "multi_source_confirmation",
    "low_source_confidence",
)
_SIGNAL_REASON_CODES = frozenset(
    {
        "pressure_drop_severe",
        "pressure_drop_elevated",
        "throughput_drop_elevated",
        "capacity_at_risk",
        "prolonged_repair_window",
    },
)
_PHASE_FLAG_FIELDS = frozenset({"paper_only", "report_only", "readonly"})
_UNSAFE_LIVE_SURFACE_FRAGMENTS = (
    "wall" "et",
    "order",
    "cancel",
    "replace",
    "exchange_mutation",
    "auth",
)
_SENSITIVE_TEXT_FRAGMENTS = (
    "api_key",
    "apikey",
    "secret",
    "private" "_key",
    "private key",
    "authorization",
    "bearer ",
    "mnemonic",
    "seed phrase",
    "password",
    "token=",
)


@dataclass(frozen=True)
class EnergyPipelinePressureDropDigestThresholds:
    elevated_pressure_drop_ratio: Decimal = Decimal("0.100000")
    severe_pressure_drop_ratio: Decimal = Decimal("0.250000")
    elevated_flow_reduction_ratio: Decimal = Decimal("0.100000")
    capacity_at_risk_mmcfd: Decimal = Decimal("250.000000")
    prolonged_repair_eta_hours: Decimal = Decimal("24.000000")
    multi_source_confirmation_count: Decimal = Decimal("2")
    minimum_source_confidence: Decimal = Decimal("0.600000")
    elevated_risk_score: Decimal = Decimal("0.500000")
    high_risk_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "elevated_pressure_drop_ratio",
            "severe_pressure_drop_ratio",
            "elevated_flow_reduction_ratio",
            "capacity_at_risk_mmcfd",
            "prolonged_repair_eta_hours",
            "minimum_source_confidence",
            "elevated_risk_score",
            "high_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_or_positive_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "multi_source_confirmation_count",
            _normalize_positive_integer_decimal(
                "multi_source_confirmation_count",
                self.multi_source_confirmation_count,
            ),
        )
        if self.severe_pressure_drop_ratio < self.elevated_pressure_drop_ratio:
            raise ValueError(
                "severe_pressure_drop_ratio must be greater than or equal to "
                "elevated_pressure_drop_ratio",
            )
        if self.high_risk_score < self.elevated_risk_score:
            raise ValueError(
                "high_risk_score must be greater than or equal to elevated_risk_score",
            )
        if self.minimum_source_confidence > _ONE:
            raise ValueError("minimum_source_confidence must be less than or equal to 1")
        if self.elevated_risk_score > _ONE or self.high_risk_score > _ONE:
            raise ValueError("risk score thresholds must be less than or equal to 1")
        _require_hard_flags("thresholds", self)


@dataclass(frozen=True)
class EnergyPipelinePressureDropObservation:
    pipeline_id: str
    market_slug: str
    region: str
    observed_at: datetime
    pressure_drop_ratio: Decimal
    flow_reduction_ratio: Decimal
    affected_capacity_mmcfd: Decimal
    repair_eta_hours: Decimal
    source_count: Decimal
    source_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("pipeline_id", "market_slug", "region"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc_datetime("observed_at", self.observed_at),
        )
        for field_name in (
            "pressure_drop_ratio",
            "flow_reduction_ratio",
            "source_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("affected_capacity_mmcfd", "repair_eta_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_integer_decimal("source_count", self.source_count),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class EnergyPipelinePressureDropDigestRow:
    pipeline_id: str
    market_slug: str
    region: str
    observed_at: datetime
    pressure_drop_ratio: Decimal
    flow_reduction_ratio: Decimal
    affected_capacity_mmcfd: Decimal
    repair_eta_hours: Decimal
    source_count: Decimal
    source_confidence: Decimal
    risk_score: Decimal
    screening_status: str
    reason_codes: tuple[str, ...]
    phase: str = PHASE_NAME
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("pipeline_id", "market_slug", "region", "phase"):
            _require_public_string(field_name, getattr(self, field_name))
        if self.phase != PHASE_NAME:
            raise ValueError(f"phase must be {PHASE_NAME}")
        object.__setattr__(
            self,
            "observed_at",
            _as_utc_datetime("observed_at", self.observed_at),
        )
        for field_name in (
            "pressure_drop_ratio",
            "flow_reduction_ratio",
            "source_confidence",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("affected_capacity_mmcfd", "repair_eta_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_integer_decimal("source_count", self.source_count),
        )
        _require_screening_status(self.screening_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("digest row", self)


@dataclass(frozen=True)
class EnergyPipelinePressureDropDigestReport:
    generated_at: datetime
    config_version: str
    thresholds: EnergyPipelinePressureDropDigestThresholds
    observation_count: Decimal
    high_risk_count: Decimal
    elevated_risk_count: Decimal
    watch_count: Decimal
    total_capacity_at_risk_mmcfd: Decimal
    max_pressure_drop_ratio: Decimal
    max_risk_score: Decimal
    average_risk_score: Decimal
    status: str
    top_market_slug: str | None
    reason_codes: tuple[str, ...]
    rows: tuple[EnergyPipelinePressureDropDigestRow, ...]
    phase: str = PHASE_NAME
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc_datetime("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if type(self.thresholds) is not EnergyPipelinePressureDropDigestThresholds:
            raise ValueError("thresholds must be an EnergyPipelinePressureDropDigestThresholds")
        for field_name in (
            "observation_count",
            "high_risk_count",
            "elevated_risk_count",
            "watch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integer_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "total_capacity_at_risk_mmcfd",
            "max_pressure_drop_ratio",
            "max_risk_score",
            "average_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_report_status(self.status)
        if self.top_market_slug is not None:
            _require_public_string("top_market_slug", self.top_market_slug)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_public_string("phase", self.phase)
        if self.phase != PHASE_NAME:
            raise ValueError(f"phase must be {PHASE_NAME}")
        _validate_report_consistency(self)
        _require_hard_flags("digest report", self)


def build_market_research_energy_pipeline_pressure_drop_digest_report(
    observations: Iterable[EnergyPipelinePressureDropObservation],
    *,
    generated_at: datetime,
    thresholds: EnergyPipelinePressureDropDigestThresholds | None = None,
    config_version: str = DEFAULT_CONFIG_VERSION,
) -> EnergyPipelinePressureDropDigestReport:
    generated_at = _as_utc_datetime("generated_at", generated_at)
    _require_public_string("config_version", config_version)
    if thresholds is None:
        thresholds = EnergyPipelinePressureDropDigestThresholds()
    elif type(thresholds) is not EnergyPipelinePressureDropDigestThresholds:
        raise ValueError("thresholds must be an EnergyPipelinePressureDropDigestThresholds")

    observations_tuple = _normalize_observations(observations)
    rows = tuple(_row_from_observation(observation, thresholds) for observation in observations_tuple)
    sorted_rows = _sort_rows(rows)

    if not sorted_rows:
        return EnergyPipelinePressureDropDigestReport(
            generated_at=generated_at,
            config_version=config_version,
            thresholds=thresholds,
            observation_count=Decimal("0"),
            high_risk_count=Decimal("0"),
            elevated_risk_count=Decimal("0"),
            watch_count=Decimal("0"),
            total_capacity_at_risk_mmcfd=Decimal("0"),
            max_pressure_drop_ratio=Decimal("0"),
            max_risk_score=Decimal("0"),
            average_risk_score=Decimal("0"),
            status="no_observations",
            top_market_slug=None,
            reason_codes=("no_pressure_drop_observations",),
            rows=(),
        )

    high_risk_count = _count_rows_with_status(sorted_rows, "high_risk")
    elevated_risk_count = _count_rows_with_status(sorted_rows, "elevated")
    watch_count = _count_rows_with_status(sorted_rows, "watch")
    total_capacity = sum(
        (row.affected_capacity_mmcfd for row in sorted_rows),
        Decimal("0"),
    )
    max_pressure_drop = max(row.pressure_drop_ratio for row in sorted_rows)
    max_risk_score = max(row.risk_score for row in sorted_rows)
    average_risk_score = _quantize_score(
        sum((row.risk_score for row in sorted_rows), Decimal("0"))
        / Decimal(len(sorted_rows)),
    )
    reason_codes = _ordered_reason_codes(
        code for row in sorted_rows for code in row.reason_codes
    )

    return EnergyPipelinePressureDropDigestReport(
        generated_at=generated_at,
        config_version=config_version,
        thresholds=thresholds,
        observation_count=Decimal(len(sorted_rows)),
        high_risk_count=high_risk_count,
        elevated_risk_count=elevated_risk_count,
        watch_count=watch_count,
        total_capacity_at_risk_mmcfd=total_capacity,
        max_pressure_drop_ratio=max_pressure_drop,
        max_risk_score=max_risk_score,
        average_risk_score=average_risk_score,
        status=_report_status(high_risk_count, elevated_risk_count),
        top_market_slug=sorted_rows[0].market_slug,
        reason_codes=reason_codes,
        rows=sorted_rows,
    )


def market_research_energy_pipeline_pressure_drop_digest_payload(
    report: EnergyPipelinePressureDropDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is EnergyPipelinePressureDropDigestReport:
        _require_hard_flags("report", report)
        _reject_unsafe_payload_keys("energy pipeline pressure-drop digest", report)
        _reject_sensitive_public_strings("energy pipeline pressure-drop digest", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_payload_keys("energy pipeline pressure-drop digest payload", report)
        _reject_flag_downgrades("energy pipeline pressure-drop digest payload", report)
        _reject_sensitive_public_strings(
            "energy pipeline pressure-drop digest payload",
            report,
        )
        payload = _json_ready(report)
    else:
        raise ValueError("report must be an EnergyPipelinePressureDropDigestReport")

    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload_keys("energy pipeline pressure-drop digest payload", payload)
    _reject_flag_downgrades("energy pipeline pressure-drop digest payload", payload)
    _reject_sensitive_public_strings(
        "energy pipeline pressure-drop digest payload",
        payload,
    )
    _require_hard_flags("payload", _DictFlags(payload))
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


def _row_from_observation(
    observation: EnergyPipelinePressureDropObservation,
    thresholds: EnergyPipelinePressureDropDigestThresholds,
) -> EnergyPipelinePressureDropDigestRow:
    reason_codes = _row_reason_codes(observation, thresholds)
    risk_score = _risk_score(observation, thresholds)
    return EnergyPipelinePressureDropDigestRow(
        pipeline_id=observation.pipeline_id,
        market_slug=observation.market_slug,
        region=observation.region,
        observed_at=observation.observed_at,
        pressure_drop_ratio=observation.pressure_drop_ratio,
        flow_reduction_ratio=observation.flow_reduction_ratio,
        affected_capacity_mmcfd=observation.affected_capacity_mmcfd,
        repair_eta_hours=observation.repair_eta_hours,
        source_count=observation.source_count,
        source_confidence=observation.source_confidence,
        risk_score=risk_score,
        screening_status=_screening_status(risk_score, reason_codes, thresholds),
        reason_codes=reason_codes,
    )


def _risk_score(
    observation: EnergyPipelinePressureDropObservation,
    thresholds: EnergyPipelinePressureDropDigestThresholds,
) -> Decimal:
    score = (
        _weighted_component(
            observation.pressure_drop_ratio,
            thresholds.severe_pressure_drop_ratio,
            _PRESSURE_WEIGHT,
        )
        + _weighted_component(
            observation.flow_reduction_ratio,
            thresholds.elevated_flow_reduction_ratio,
            _FLOW_WEIGHT,
        )
        + _weighted_component(
            observation.affected_capacity_mmcfd,
            thresholds.capacity_at_risk_mmcfd,
            _CAPACITY_WEIGHT,
        )
        + _weighted_component(
            observation.repair_eta_hours,
            thresholds.prolonged_repair_eta_hours,
            _REPAIR_WEIGHT,
        )
        + (_bounded_unit(observation.source_confidence) * _CONFIDENCE_WEIGHT)
    )
    return _quantize_score(min(score, _ONE))


def _weighted_component(value: Decimal, threshold: Decimal, weight: Decimal) -> Decimal:
    if value <= _ZERO:
        return _ZERO
    return min(value / threshold, _ONE) * weight


def _row_reason_codes(
    observation: EnergyPipelinePressureDropObservation,
    thresholds: EnergyPipelinePressureDropDigestThresholds,
) -> tuple[str, ...]:
    codes: list[str] = []
    if observation.pressure_drop_ratio >= thresholds.severe_pressure_drop_ratio:
        codes.append("pressure_drop_severe")
    elif observation.pressure_drop_ratio >= thresholds.elevated_pressure_drop_ratio:
        codes.append("pressure_drop_elevated")
    if observation.flow_reduction_ratio >= thresholds.elevated_flow_reduction_ratio:
        codes.append("throughput_drop_elevated")
    if observation.affected_capacity_mmcfd >= thresholds.capacity_at_risk_mmcfd:
        codes.append("capacity_at_risk")
    if observation.repair_eta_hours >= thresholds.prolonged_repair_eta_hours:
        codes.append("prolonged_repair_window")
    if observation.source_count >= thresholds.multi_source_confirmation_count:
        codes.append("multi_source_confirmation")
    if observation.source_confidence < thresholds.minimum_source_confidence:
        codes.append("low_source_confidence")
    return _ordered_reason_codes(codes)


def _screening_status(
    risk_score: Decimal,
    reason_codes: tuple[str, ...],
    thresholds: EnergyPipelinePressureDropDigestThresholds,
) -> str:
    if risk_score >= thresholds.high_risk_score:
        return "high_risk"
    if risk_score >= thresholds.elevated_risk_score:
        return "elevated"
    if any(code in _SIGNAL_REASON_CODES for code in reason_codes):
        return "elevated"
    return "watch"


def _report_status(high_risk_count: Decimal, elevated_risk_count: Decimal) -> str:
    if high_risk_count > _ZERO:
        return "high_risk"
    if elevated_risk_count > _ZERO:
        return "elevated"
    return "watch"


def _count_rows_with_status(
    rows: tuple[EnergyPipelinePressureDropDigestRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.screening_status == status))


def _sort_rows(
    rows: tuple[EnergyPipelinePressureDropDigestRow, ...],
) -> tuple[EnergyPipelinePressureDropDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.risk_score,
                -row.pressure_drop_ratio,
                -row.affected_capacity_mmcfd,
                row.observed_at.isoformat(),
                row.pipeline_id,
                row.market_slug,
            ),
        ),
    )


def _normalize_observations(
    observations: Iterable[EnergyPipelinePressureDropObservation],
) -> tuple[EnergyPipelinePressureDropObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized: list[EnergyPipelinePressureDropObservation] = []
    for observation in observations:
        if type(observation) is not EnergyPipelinePressureDropObservation:
            raise ValueError(
                "observations must contain EnergyPipelinePressureDropObservation items",
            )
        normalized.append(observation)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[EnergyPipelinePressureDropDigestRow, ...],
) -> tuple[EnergyPipelinePressureDropDigestRow, ...]:
    if not isinstance(rows, (tuple, list)):
        raise ValueError("rows must be a tuple")
    normalized: list[EnergyPipelinePressureDropDigestRow] = []
    for row in rows:
        if type(row) is not EnergyPipelinePressureDropDigestRow:
            raise ValueError("rows must contain EnergyPipelinePressureDropDigestRow items")
        normalized.append(row)
    return _sort_rows(tuple(normalized))


def _validate_report_consistency(report: EnergyPipelinePressureDropDigestReport) -> None:
    row_count = Decimal(len(report.rows))
    high_risk_count = _count_rows_with_status(report.rows, "high_risk")
    elevated_risk_count = _count_rows_with_status(report.rows, "elevated")
    watch_count = _count_rows_with_status(report.rows, "watch")
    if report.observation_count != row_count:
        raise ValueError("observation_count must match rows")
    if report.high_risk_count != high_risk_count:
        raise ValueError("high_risk_count must match rows")
    if report.elevated_risk_count != elevated_risk_count:
        raise ValueError("elevated_risk_count must match rows")
    if report.watch_count != watch_count:
        raise ValueError("watch_count must match rows")
    if report.observation_count != (
        report.high_risk_count + report.elevated_risk_count + report.watch_count
    ):
        raise ValueError("status counts must sum to observation_count")

    if not report.rows:
        if report.status != "no_observations":
            raise ValueError("empty report status must be no_observations")
        if report.top_market_slug is not None:
            raise ValueError("empty report top_market_slug must be None")
        if report.reason_codes != ("no_pressure_drop_observations",):
            raise ValueError("empty report reason_codes must mark no observations")
        return

    if report.status != _report_status(high_risk_count, elevated_risk_count):
        raise ValueError("report status must match row statuses")
    if report.top_market_slug != report.rows[0].market_slug:
        raise ValueError("top_market_slug must match highest-risk row")
    if report.total_capacity_at_risk_mmcfd != sum(
        (row.affected_capacity_mmcfd for row in report.rows),
        Decimal("0"),
    ):
        raise ValueError("total_capacity_at_risk_mmcfd must match rows")
    if report.max_pressure_drop_ratio != max(
        row.pressure_drop_ratio for row in report.rows
    ):
        raise ValueError("max_pressure_drop_ratio must match rows")
    if report.max_risk_score != max(row.risk_score for row in report.rows):
        raise ValueError("max_risk_score must match rows")
    expected_average = _quantize_score(
        sum((row.risk_score for row in report.rows), Decimal("0"))
        / Decimal(len(report.rows)),
    )
    if report.average_risk_score != expected_average:
        raise ValueError("average_risk_score must match rows")
    expected_reasons = _ordered_reason_codes(
        code for row in report.rows for code in row.reason_codes
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row reason codes")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(reason_codes, (tuple, list)):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for code in reason_codes:
        if type(code) is not str or not code:
            raise ValueError("reason_codes must contain non-empty strings")
        _reject_sensitive_text("reason_code", code)
        normalized.append(code)
    return _ordered_reason_codes(normalized)


def _ordered_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    seen = set(reason_codes)
    order = {code: index for index, code in enumerate(_REASON_CODE_ORDER)}
    return tuple(sorted(seen, key=lambda code: (order.get(code, len(order)), code)))


def _normalize_probability_or_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_integer_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_positive_integer_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_integer_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_score(value: Decimal) -> Decimal:
    return value.quantize(_SCORE_QUANT)


def _bounded_unit(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value


def _as_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    _reject_sensitive_text(field_name, value)


def _require_screening_status(value: object) -> None:
    if value not in {"watch", "elevated", "high_risk"}:
        raise ValueError("screening_status must be watch, elevated, or high_risk")


def _require_report_status(value: object) -> None:
    if value not in {"no_observations", "watch", "elevated", "high_risk"}:
        raise ValueError(
            "status must be no_observations, watch, elevated, or high_risk",
        )


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload_keys(label: str, value: object) -> None:
    for key in _iter_payload_keys(value):
        if _has_unsafe_live_surface_fragment(key):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys: list[str] = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _reject_flag_downgrades(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_flag_downgrades(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True in {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_sensitive_public_strings(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_sensitive_public_strings(label, asdict(value))
        return
    if type(value) is str:
        _reject_sensitive_text(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_sensitive_text(label, key)
            _reject_sensitive_public_strings(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_sensitive_public_strings(label, item)


def _reject_sensitive_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _SENSITIVE_TEXT_FRAGMENTS):
        raise ValueError(f"sensitive value in {field_name}")


def _has_unsafe_live_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_LIVE_SURFACE_FRAGMENTS)


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "PHASE_NAME",
    "EnergyPipelinePressureDropDigestReport",
    "EnergyPipelinePressureDropDigestRow",
    "EnergyPipelinePressureDropDigestThresholds",
    "EnergyPipelinePressureDropObservation",
    "build_market_research_energy_pipeline_pressure_drop_digest_report",
    "market_research_energy_pipeline_pressure_drop_digest_payload",
)

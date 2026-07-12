"""Report-only forecast calibration residual snapshot for probability events."""

from __future__ import annotations

from dataclasses import dataclass, fields
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from re import Pattern, compile
from typing import Any, Mapping


__all__ = (
    "PROBABILITY_EVENT_FORECAST_CALIBRATION_RESIDUAL_REPORT_VERSION",
    "ProbabilityEventForecastCalibrationResidualConfig",
    "ProbabilityEventForecastCalibrationResidualReport",
    "build_probability_event_forecast_calibration_residual_report",
    "probability_event_forecast_calibration_residual_report_payload",
    "probability_event_forecast_calibration_residual_report_digest",
)


PROBABILITY_EVENT_FORECAST_CALIBRATION_RESIDUAL_REPORT_VERSION = (
    "probability-event-forecast-calibration-residual-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DIGEST_RE: Pattern[str] = compile(r"^[0-9a-f]{64}$")

RESIDUAL_STATUSES = ("pass", "watch", "block")
REASON_CODE_SEQUENCE = (
    "forecast_historical_gap_above_block",
    "forecast_historical_gap_above_watch",
    "calibration_error_above_block",
    "calibration_error_above_watch",
    "sample_count_below_minimum",
    "adjusted_forecast_probability_at_boundary",
    "recency_penalty_present",
    "forecast_calibration_residual_pass",
)
MANUAL_NEXT_STEPS = (
    "continue_readonly_paper_probability_review",
    "manually_review_forecast_calibration_residual",
    "pause_paper_probability_review_until_calibration_residual_is_resolved",
)


@dataclass(frozen=True)
class ProbabilityEventForecastCalibrationResidualConfig:
    config_version: str = PROBABILITY_EVENT_FORECAST_CALIBRATION_RESIDUAL_REPORT_VERSION
    forecast_historical_gap_watch_threshold: Decimal = Decimal("0.100000")
    forecast_historical_gap_block_threshold: Decimal = Decimal("0.350000")
    calibration_error_watch_threshold: Decimal = Decimal("0.040000")
    calibration_error_block_threshold: Decimal = Decimal("0.120000")
    recency_penalty_watch_threshold: Decimal = Decimal("0.030000")
    minimum_sample_count: Decimal = Decimal("30.000000")
    boundary_probability: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventForecastCalibrationResidualConfig:
            raise TypeError(
                "ProbabilityEventForecastCalibrationResidualConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventForecastCalibrationResidualConfig:
            raise ValueError(
                "config must be exactly ProbabilityEventForecastCalibrationResidualConfig",
            )
        _require_config_version(self.config_version)
        for field_name in (
            "forecast_historical_gap_watch_threshold",
            "forecast_historical_gap_block_threshold",
            "calibration_error_watch_threshold",
            "calibration_error_block_threshold",
            "recency_penalty_watch_threshold",
            "boundary_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_sample_count",
            _require_nonnegative_count_decimal(
                "minimum_sample_count",
                self.minimum_sample_count,
            ),
        )
        if (
            self.forecast_historical_gap_watch_threshold
            > self.forecast_historical_gap_block_threshold
        ):
            raise ValueError(
                "forecast_historical_gap_watch_threshold must not exceed block threshold",
            )
        if self.calibration_error_watch_threshold > self.calibration_error_block_threshold:
            raise ValueError(
                "calibration_error_watch_threshold must not exceed block threshold",
            )
        if self.boundary_probability != ZERO:
            raise ValueError("boundary_probability must be 0.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilityEventForecastCalibrationResidualReport:
    config_version: str
    forecast_probability: Decimal
    historical_calibrated_probability: Decimal
    calibration_error_probability: Decimal
    sample_count: Decimal
    recency_penalty_probability: Decimal
    calibration_residual_probability: Decimal
    adjusted_forecast_probability: Decimal
    calibration_residual_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventForecastCalibrationResidualReport:
            raise TypeError(
                "ProbabilityEventForecastCalibrationResidualReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventForecastCalibrationResidualReport:
            raise ValueError(
                "report must be exactly ProbabilityEventForecastCalibrationResidualReport",
            )
        _require_config_version(self.config_version)
        for field_name in (
            "forecast_probability",
            "historical_calibrated_probability",
            "calibration_error_probability",
            "recency_penalty_probability",
            "calibration_residual_probability",
            "adjusted_forecast_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_count",
            _require_nonnegative_count_decimal("sample_count", self.sample_count),
        )
        _require_enum(
            "calibration_residual_status",
            self.calibration_residual_status,
            RESIDUAL_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest(_payload_items(self, payload_digest=""))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def status(self) -> str:
        return self.calibration_residual_status

    @property
    def public_payload(self) -> dict[str, Any]:
        return probability_event_forecast_calibration_residual_report_payload(self)


def build_probability_event_forecast_calibration_residual_report(
    *,
    forecast_probability: Decimal,
    historical_calibrated_probability: Decimal,
    calibration_error_probability: Decimal,
    sample_count: Decimal,
    recency_penalty_probability: Decimal,
    config: ProbabilityEventForecastCalibrationResidualConfig,
) -> ProbabilityEventForecastCalibrationResidualReport:
    """Build a deterministic read-only calibration residual report."""

    if type(config) is not ProbabilityEventForecastCalibrationResidualConfig:
        raise ValueError(
            "config must be a ProbabilityEventForecastCalibrationResidualConfig",
        )
    _require_hard_flags("config", config)
    forecast = _require_ratio_decimal("forecast_probability", forecast_probability)
    historical = _require_ratio_decimal(
        "historical_calibrated_probability",
        historical_calibrated_probability,
    )
    calibration_error = _require_ratio_decimal(
        "calibration_error_probability",
        calibration_error_probability,
    )
    samples = _require_nonnegative_count_decimal("sample_count", sample_count)
    recency_penalty = _require_ratio_decimal(
        "recency_penalty_probability",
        recency_penalty_probability,
    )
    forecast_gap = _abs_decimal(forecast - historical)
    residual = _bounded_probability(forecast_gap + calibration_error + recency_penalty)
    adjusted_forecast = _bounded_probability(forecast - calibration_error - recency_penalty)
    reason_codes = _reason_codes(
        forecast_gap=forecast_gap,
        calibration_error_probability=calibration_error,
        sample_count=samples,
        recency_penalty_probability=recency_penalty,
        adjusted_forecast_probability=adjusted_forecast,
        config=config,
    )
    status = _calibration_residual_status(reason_codes)
    values: dict[str, object] = {
        "config_version": config.config_version,
        "forecast_probability": forecast,
        "historical_calibrated_probability": historical,
        "calibration_error_probability": calibration_error,
        "sample_count": samples,
        "recency_penalty_probability": recency_penalty,
        "calibration_residual_probability": residual,
        "adjusted_forecast_probability": adjusted_forecast,
        "calibration_residual_status": status,
        "reason_codes": reason_codes,
        "manual_next_step": _manual_next_step(status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventForecastCalibrationResidualReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def probability_event_forecast_calibration_residual_report_payload(
    report: ProbabilityEventForecastCalibrationResidualReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventForecastCalibrationResidualReport:
        raise ValueError(
            "report must be a ProbabilityEventForecastCalibrationResidualReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    expected_digest = probability_event_forecast_calibration_residual_report_digest(report)
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match public payload")
    return _payload_items(report, payload_digest=report.payload_digest)


def probability_event_forecast_calibration_residual_report_digest(
    report: ProbabilityEventForecastCalibrationResidualReport,
) -> str:
    if type(report) is not ProbabilityEventForecastCalibrationResidualReport:
        raise ValueError(
            "report must be a ProbabilityEventForecastCalibrationResidualReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    return _payload_digest(_payload_items(report, payload_digest=""))


def _reason_codes(
    *,
    forecast_gap: Decimal,
    calibration_error_probability: Decimal,
    sample_count: Decimal,
    recency_penalty_probability: Decimal,
    adjusted_forecast_probability: Decimal,
    config: ProbabilityEventForecastCalibrationResidualConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if forecast_gap >= config.forecast_historical_gap_block_threshold:
        reason_codes.append("forecast_historical_gap_above_block")
    elif forecast_gap >= config.forecast_historical_gap_watch_threshold:
        reason_codes.append("forecast_historical_gap_above_watch")
    if calibration_error_probability >= config.calibration_error_block_threshold:
        reason_codes.append("calibration_error_above_block")
    elif calibration_error_probability >= config.calibration_error_watch_threshold:
        reason_codes.append("calibration_error_above_watch")
    if sample_count < config.minimum_sample_count:
        reason_codes.append("sample_count_below_minimum")
    if adjusted_forecast_probability in (ZERO, ONE):
        reason_codes.append("adjusted_forecast_probability_at_boundary")
    if recency_penalty_probability >= config.recency_penalty_watch_threshold:
        reason_codes.append("recency_penalty_present")
    if not reason_codes:
        reason_codes.append("forecast_calibration_residual_pass")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _calibration_residual_status(reason_codes: tuple[str, ...]) -> str:
    if "forecast_historical_gap_above_block" in reason_codes:
        return "block"
    if "calibration_error_above_block" in reason_codes:
        return "block"
    if "adjusted_forecast_probability_at_boundary" in reason_codes:
        return "block"
    if reason_codes == ("forecast_calibration_residual_pass",):
        return "pass"
    return "watch"


def _manual_next_step(status: str) -> str:
    if status == "block":
        return "pause_paper_probability_review_until_calibration_residual_is_resolved"
    if status == "watch":
        return "manually_review_forecast_calibration_residual"
    return "continue_readonly_paper_probability_review"


def _validate_report_consistency(
    report: ProbabilityEventForecastCalibrationResidualReport,
) -> None:
    forecast_gap = _abs_decimal(
        report.forecast_probability - report.historical_calibrated_probability,
    )
    expected_residual = _bounded_probability(
        forecast_gap
        + report.calibration_error_probability
        + report.recency_penalty_probability,
    )
    if report.calibration_residual_probability != expected_residual:
        raise ValueError("calibration_residual_probability must match report inputs")
    expected_adjusted = _bounded_probability(
        report.forecast_probability
        - report.calibration_error_probability
        - report.recency_penalty_probability,
    )
    if report.adjusted_forecast_probability != expected_adjusted:
        raise ValueError("adjusted_forecast_probability must match report inputs")
    status = _calibration_residual_status(report.reason_codes)
    if report.calibration_residual_status != status:
        raise ValueError("reason_codes must match calibration_residual_status")
    if report.manual_next_step != _manual_next_step(status):
        raise ValueError("manual_next_step must match calibration_residual_status")


def _payload_items(
    report: ProbabilityEventForecastCalibrationResidualReport,
    *,
    payload_digest: str,
) -> dict[str, Any]:
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["payload_digest"] = payload_digest
    return _payload_values(values, payload_digest=payload_digest)


def _payload_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, Any]:
    return {
        "config_version": values["config_version"],
        "forecast_probability": _decimal_text(values["forecast_probability"]),
        "historical_calibrated_probability": _decimal_text(
            values["historical_calibrated_probability"],
        ),
        "calibration_error_probability": _decimal_text(
            values["calibration_error_probability"],
        ),
        "sample_count": _decimal_text(values["sample_count"]),
        "recency_penalty_probability": _decimal_text(
            values["recency_penalty_probability"],
        ),
        "calibration_residual_probability": _decimal_text(
            values["calibration_residual_probability"],
        ),
        "adjusted_forecast_probability": _decimal_text(
            values["adjusted_forecast_probability"],
        ),
        "calibration_residual_status": values["calibration_residual_status"],
        "reason_codes": [
            reason_code for reason_code in values["reason_codes"]  # type: ignore[index]
        ],
        "manual_next_step": values["manual_next_step"],
        "payload_digest": payload_digest,
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
    }


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize(-value)
    return _quantize(value)


def _bounded_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _require_config_version(value: object) -> str:
    if (
        type(value) is not str
        or value != PROBABILITY_EVENT_FORECAST_CALIBRATION_RESIDUAL_REPORT_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    return value


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a supported value")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} must contain supported reason codes")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)


def _require_manual_next_step(value: object) -> str:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError("manual_next_step must be a supported value")
    return value


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric value must be Decimal")
    return format(_quantize(value), "f")


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()

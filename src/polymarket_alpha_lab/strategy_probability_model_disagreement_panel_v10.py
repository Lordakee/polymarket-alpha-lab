from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, localcontext
from typing import Any


__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_MODEL_DISAGREEMENT_PANEL_CONFIG_VERSION",
    "ProbabilityModelDisagreementPanel",
    "ProbabilityModelForecastInput",
    "StrategyProbabilityModelDisagreementPanelConfig",
    "StrategyProbabilityModelDisagreementPanelModelRow",
    "StrategyProbabilityModelDisagreementPanelReport",
    "StrategyProbabilityModelForecast",
    "build_strategy_probability_model_disagreement_panel",
    "strategy_probability_model_disagreement_panel_payload",
)


DEFAULT_STRATEGY_PROBABILITY_MODEL_DISAGREEMENT_PANEL_CONFIG_VERSION = (
    "strategy-probability-model-disagreement-panel-v10"
)
DECIMAL_CONTEXT = Context(prec=64)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX_PLACES = Decimal("0.000001")
STATUSES = ("pass", "watch", "blocked")
READY_REASON_CODE = "probability_model_panel_ready"
ROW_READY_REASON_CODE = "probability_model_row_ready"


@dataclass(frozen=True)
class StrategyProbabilityModelDisagreementPanelConfig:
    config_version: str = (
        DEFAULT_STRATEGY_PROBABILITY_MODEL_DISAGREEMENT_PANEL_CONFIG_VERSION
    )
    min_model_count: Decimal = Decimal("2")
    min_component_score: Decimal = Decimal("0.500000")
    min_model_weight: Decimal = Decimal("0.500000")
    watch_disagreement_gap: Decimal = Decimal("0.100000")
    blocked_disagreement_gap: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyProbabilityModelDisagreementPanelConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityModelDisagreementPanelConfig:
            raise ValueError(
                "config must be exactly StrategyProbabilityModelDisagreementPanelConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_model_count",
            _require_positive_integral_decimal("min_model_count", self.min_model_count),
        )
        for field_name in (
            "min_component_score",
            "min_model_weight",
            "watch_disagreement_gap",
            "blocked_disagreement_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_disagreement_gap > self.blocked_disagreement_gap:
            raise ValueError(
                "watch_disagreement_gap must be less than or equal to "
                "blocked_disagreement_gap",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyProbabilityModelForecast:
    model_id: str
    forecast_probability: Decimal
    calibration_score: Decimal
    recency_weight: Decimal
    source_coverage_score: Decimal
    rationale_quality_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyProbabilityModelForecast does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityModelForecast:
            raise ValueError("forecast must be exactly StrategyProbabilityModelForecast")
        _require_canonical_string("model_id", self.model_id)
        for field_name in (
            "forecast_probability",
            "calibration_score",
            "recency_weight",
            "source_coverage_score",
            "rationale_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("forecast", self)


@dataclass(frozen=True)
class StrategyProbabilityModelDisagreementPanelModelRow:
    model_id: str
    forecast_probability: Decimal
    calibration_score: Decimal
    recency_weight: Decimal
    source_coverage_score: Decimal
    rationale_quality_score: Decimal
    model_weight: Decimal
    consensus_gap: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyProbabilityModelDisagreementPanelModelRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityModelDisagreementPanelModelRow:
            raise ValueError(
                "model row must be exactly "
                "StrategyProbabilityModelDisagreementPanelModelRow",
            )
        _require_canonical_string("model_id", self.model_id)
        for field_name in (
            "forecast_probability",
            "calibration_score",
            "recency_weight",
            "source_coverage_score",
            "rationale_quality_score",
            "model_weight",
            "consensus_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.row_status != _row_status(self.reason_codes):
            raise ValueError("row_status must match reason_codes")
        _require_hard_flags("model row", self)


@dataclass(frozen=True)
class StrategyProbabilityModelDisagreementPanelReport:
    consensus_probability: Decimal
    disagreement_status: str
    model_rows: tuple[StrategyProbabilityModelDisagreementPanelModelRow, ...]
    confidence_penalty: Decimal
    reason_codes: tuple[str, ...]
    config_version: str = (
        DEFAULT_STRATEGY_PROBABILITY_MODEL_DISAGREEMENT_PANEL_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyProbabilityModelDisagreementPanelReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityModelDisagreementPanelReport:
            raise ValueError(
                "report must be exactly StrategyProbabilityModelDisagreementPanelReport",
            )
        object.__setattr__(
            self,
            "consensus_probability",
            _require_probability("consensus_probability", self.consensus_probability),
        )
        _require_status("disagreement_status", self.disagreement_status)
        object.__setattr__(self, "model_rows", _normalize_model_rows(self.model_rows))
        object.__setattr__(
            self,
            "confidence_penalty",
            _require_probability("confidence_penalty", self.confidence_penalty),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_canonical_string("config_version", self.config_version)
        _validate_report(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_probability_model_disagreement_panel_payload(self)


ProbabilityModelForecastInput = StrategyProbabilityModelForecast
ProbabilityModelDisagreementPanel = StrategyProbabilityModelDisagreementPanelReport


def build_strategy_probability_model_disagreement_panel(
    forecasts: object,
    *,
    config: StrategyProbabilityModelDisagreementPanelConfig | None = None,
) -> StrategyProbabilityModelDisagreementPanelReport:
    if config is None:
        config = StrategyProbabilityModelDisagreementPanelConfig()
    if type(config) is not StrategyProbabilityModelDisagreementPanelConfig:
        raise ValueError(
            "config must be exactly StrategyProbabilityModelDisagreementPanelConfig",
        )
    _require_hard_flags("config", config)
    source_rows = _normalize_forecasts(forecasts)
    consensus_probability = _consensus_probability(source_rows)
    model_rows = tuple(
        _build_model_row(
            forecast,
            consensus_probability=consensus_probability,
            config=config,
        )
        for forecast in source_rows
    )
    reason_codes = _panel_reason_codes(model_rows, config=config)
    return StrategyProbabilityModelDisagreementPanelReport(
        consensus_probability=consensus_probability,
        disagreement_status=_panel_status(reason_codes),
        model_rows=model_rows,
        confidence_penalty=_confidence_penalty(model_rows, config=config),
        reason_codes=reason_codes,
        config_version=config.config_version,
    )


def strategy_probability_model_disagreement_panel_payload(
    report: StrategyProbabilityModelDisagreementPanelReport,
) -> dict[str, Any]:
    if type(report) is not StrategyProbabilityModelDisagreementPanelReport:
        raise ValueError(
            "report must be exactly StrategyProbabilityModelDisagreementPanelReport",
        )
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a dict")
    return payload


def _build_model_row(
    forecast: StrategyProbabilityModelForecast,
    *,
    consensus_probability: Decimal,
    config: StrategyProbabilityModelDisagreementPanelConfig,
) -> StrategyProbabilityModelDisagreementPanelModelRow:
    model_weight = _model_weight(forecast)
    consensus_gap = _abs_decimal(forecast.forecast_probability - consensus_probability)
    reason_codes = _row_reason_codes(
        forecast,
        model_weight=model_weight,
        consensus_gap=consensus_gap,
        config=config,
    )
    return StrategyProbabilityModelDisagreementPanelModelRow(
        model_id=forecast.model_id,
        forecast_probability=forecast.forecast_probability,
        calibration_score=forecast.calibration_score,
        recency_weight=forecast.recency_weight,
        source_coverage_score=forecast.source_coverage_score,
        rationale_quality_score=forecast.rationale_quality_score,
        model_weight=model_weight,
        consensus_gap=consensus_gap,
        row_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _model_weight(forecast: StrategyProbabilityModelForecast) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _six_places(
            (
                forecast.calibration_score
                + forecast.recency_weight
                + forecast.source_coverage_score
                + forecast.rationale_quality_score
            )
            / Decimal("4"),
        )


def _consensus_probability(
    forecasts: tuple[StrategyProbabilityModelForecast, ...],
) -> Decimal:
    if not forecasts:
        return ZERO
    weighted_rows = tuple((forecast, _model_weight(forecast)) for forecast in forecasts)
    total_weight = sum((weight for _, weight in weighted_rows), ZERO)
    with localcontext(DECIMAL_CONTEXT):
        if total_weight == ZERO:
            return _six_places(
                sum((forecast.forecast_probability for forecast in forecasts), ZERO)
                / Decimal(len(forecasts)),
            )
        return _six_places(
            sum(
                (
                    forecast.forecast_probability * weight
                    for forecast, weight in weighted_rows
                ),
                ZERO,
            )
            / total_weight,
        )


def _row_reason_codes(
    forecast: StrategyProbabilityModelForecast,
    *,
    model_weight: Decimal,
    consensus_gap: Decimal,
    config: StrategyProbabilityModelDisagreementPanelConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if forecast.calibration_score < config.min_component_score:
        codes.append("low_calibration_score")
    if forecast.recency_weight < config.min_component_score:
        codes.append("low_recency_weight")
    if forecast.source_coverage_score < config.min_component_score:
        codes.append("low_source_coverage_score")
    if forecast.rationale_quality_score < config.min_component_score:
        codes.append("low_rationale_quality_score")
    if model_weight < config.min_model_weight:
        codes.append("low_model_weight")
    if consensus_gap >= config.blocked_disagreement_gap:
        codes.append("model_consensus_gap_blocked")
    elif consensus_gap >= config.watch_disagreement_gap:
        codes.append("model_consensus_gap_watch")
    if not codes:
        codes.append(ROW_READY_REASON_CODE)
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "model_consensus_gap_blocked" in reason_codes:
        return "blocked"
    if any(reason_code != ROW_READY_REASON_CODE for reason_code in reason_codes):
        return "watch"
    return "pass"


def _panel_reason_codes(
    model_rows: tuple[StrategyProbabilityModelDisagreementPanelModelRow, ...],
    *,
    config: StrategyProbabilityModelDisagreementPanelConfig,
) -> tuple[str, ...]:
    if not model_rows:
        return ("missing_models",)
    codes: list[str] = []
    if Decimal(len(model_rows)) < config.min_model_count:
        codes.append("insufficient_model_count")
    if sum((row.model_weight for row in model_rows), ZERO) == ZERO:
        codes.append("zero_total_model_weight")
    dispersion = _forecast_dispersion(model_rows)
    if dispersion >= config.blocked_disagreement_gap:
        codes.append("model_probability_dispersion_blocked")
    elif dispersion >= config.watch_disagreement_gap:
        codes.append("model_probability_dispersion_watch")
    if any(row.row_status == "blocked" for row in model_rows):
        codes.append("model_consensus_gap_blocked")
    elif any("model_consensus_gap_watch" in row.reason_codes for row in model_rows):
        codes.append("model_consensus_gap_watch")
    if any(
        any(
            reason_code
            in (
                "low_calibration_score",
                "low_model_weight",
                "low_rationale_quality_score",
                "low_recency_weight",
                "low_source_coverage_score",
            )
            for reason_code in row.reason_codes
        )
        for row in model_rows
    ):
        codes.append("low_quality_model_input")
    if not codes:
        codes.append(READY_REASON_CODE)
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _panel_status(reason_codes: tuple[str, ...]) -> str:
    blocked_codes = (
        "insufficient_model_count",
        "missing_models",
        "model_consensus_gap_blocked",
        "model_probability_dispersion_blocked",
        "zero_total_model_weight",
    )
    if any(reason_code in blocked_codes for reason_code in reason_codes):
        return "blocked"
    if reason_codes != (READY_REASON_CODE,):
        return "watch"
    return "pass"


def _confidence_penalty(
    model_rows: tuple[StrategyProbabilityModelDisagreementPanelModelRow, ...],
    *,
    config: StrategyProbabilityModelDisagreementPanelConfig,
) -> Decimal:
    if not model_rows:
        return ONE
    if sum((row.model_weight for row in model_rows), ZERO) == ZERO:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        average_weight = _six_places(
            sum((row.model_weight for row in model_rows), ZERO)
            / Decimal(len(model_rows)),
        )
        penalty = _forecast_dispersion(model_rows) + ((ONE - average_weight) / Decimal("4"))
        if Decimal(len(model_rows)) < config.min_model_count:
            penalty += Decimal("0.250000")
        return _clamp_probability(penalty)


def _forecast_dispersion(
    model_rows: tuple[StrategyProbabilityModelDisagreementPanelModelRow, ...],
) -> Decimal:
    if not model_rows:
        return ZERO
    probabilities = tuple(row.forecast_probability for row in model_rows)
    return _six_places(max(probabilities) - min(probabilities))


def _normalize_forecasts(
    forecasts: object,
) -> tuple[StrategyProbabilityModelForecast, ...]:
    _reject_float_tree("forecasts", forecasts)
    if not isinstance(forecasts, (list, tuple)):
        raise ValueError("forecasts must be a list or tuple")
    normalized = tuple(forecasts)
    seen: set[str] = set()
    for forecast in normalized:
        if type(forecast) is not StrategyProbabilityModelForecast:
            raise ValueError("forecasts must contain exact model forecast rows")
        if forecast.model_id in seen:
            raise ValueError("model_id values must be unique")
        seen.add(forecast.model_id)
    return tuple(sorted(normalized, key=lambda row: row.model_id))


def _normalize_model_rows(
    model_rows: object,
) -> tuple[StrategyProbabilityModelDisagreementPanelModelRow, ...]:
    if type(model_rows) is not tuple:
        raise ValueError("model_rows must be a tuple")
    normalized = tuple(model_rows)
    previous_model_id: str | None = None
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyProbabilityModelDisagreementPanelModelRow:
            raise ValueError("model_rows must contain exact model rows")
        if row.model_id in seen:
            raise ValueError("model_rows must have unique model_id values")
        if previous_model_id is not None and previous_model_id > row.model_id:
            raise ValueError("model_rows must be sorted by model_id")
        previous_model_id = row.model_id
        seen.add(row.model_id)
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(sorted(normalized))


def _validate_report(report: StrategyProbabilityModelDisagreementPanelReport) -> None:
    if report.disagreement_status != _panel_status(report.reason_codes):
        raise ValueError("disagreement_status must match reason_codes")
    if report.reason_codes == (READY_REASON_CODE,) and not report.model_rows:
        raise ValueError("ready report requires model rows")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "__dataclass_fields__"):
        return _payload_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    return value


def _reject_float_tree(label: str, value: object) -> None:
    if isinstance(value, float):
        raise ValueError(f"{label} must not contain float values")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_float_tree(f"{label}.{key}", item)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_float_tree(f"{label}.{index}", item)
    elif hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:
            _reject_float_tree(f"{label}.{field_name}", getattr(value, field_name))
    elif hasattr(value, "__dict__"):
        for key, item in vars(value).items():
            _reject_float_tree(f"{label}.{key}", item)


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= 0 or decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a positive integral Decimal")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six_places(value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_hard_flags(label: str, value: object) -> None:
    if _optional_attr(value, "paper_only") is not True:
        raise ValueError(f"{label} must be paper_only")
    if _optional_attr(value, "report_only") is not True:
        raise ValueError(f"{label} must be report_only")
    if _optional_attr(value, "readonly") is not True:
        raise ValueError(f"{label} must be readonly")


def _optional_attr(value: object, name: str) -> object:
    try:
        return object.__getattribute__(value, name)
    except AttributeError:
        return None


def _six_places(value: Decimal) -> Decimal:
    return value.quantize(SIX_PLACES)


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return -value
    return value


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _six_places(value)

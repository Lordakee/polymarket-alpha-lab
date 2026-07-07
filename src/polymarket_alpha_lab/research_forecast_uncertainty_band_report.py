"""Pure report reducer for probability forecast uncertainty bands."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any


__all__ = (
    "ResearchForecastUncertaintyBandConfig",
    "ResearchForecastUncertaintyBandInputRow",
    "ResearchForecastUncertaintyBandReasonCodeCount",
    "ResearchForecastUncertaintyBandReport",
    "ResearchForecastUncertaintyBandReportRow",
    "build_research_forecast_uncertainty_band_report",
    "research_forecast_uncertainty_band_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-forecast-uncertainty-band-report-v0"
STATUSES = ("pass", "watch", "block")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
WORKING_PRECISION = 28

NO_INPUTS_REASON = "forecast_uncertainty_band_no_inputs"
ROW_REASON_PREFIX = "forecast_uncertainty_band_"
REPORT_REASON_PREFIX = "research_forecast_uncertainty_band_"

_UNSAFE_PUBLIC_TEXT = (
    "ad" + "vice",
    "a" + "uth",
    "b" + "uy",
    "credential",
    "live_" + "tra" + "ding",
    "or" + "der",
    "pos" + "ition",
    "private",
    "recom" + "mend",
    "s" + "ell",
    "secret",
    "submit_" + "or" + "der",
    "token",
    "tra" + "de",
    "wal" + "let",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchForecastUncertaintyBandConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_max_uncertainty_score: Decimal = Decimal("0.150000")
    watch_max_uncertainty_score: Decimal = Decimal("0.450000")
    min_interval_half_width: Decimal = Decimal("0.020000")
    max_interval_half_width: Decimal = Decimal("0.250000")
    evidence_quality_weight: Decimal = Decimal("0.400000")
    model_disagreement_weight: Decimal = Decimal("0.250000")
    market_noise_weight: Decimal = Decimal("0.200000")
    settlement_ambiguity_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchForecastUncertaintyBandConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_max_uncertainty_score",
            "watch_max_uncertainty_score",
            "min_interval_half_width",
            "max_interval_half_width",
            "evidence_quality_weight",
            "model_disagreement_weight",
            "market_noise_weight",
            "settlement_ambiguity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_max_uncertainty_score > self.watch_max_uncertainty_score:
            raise ValueError("pass_max_uncertainty_score must be <= watch_max_uncertainty_score")
        if self.min_interval_half_width > self.max_interval_half_width:
            raise ValueError("min_interval_half_width must be <= max_interval_half_width")
        _require_weights_total_one(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchForecastUncertaintyBandInputRow(_FinalPublicDataclass):
    event_ref: str
    forecast_ref: str
    probability: Decimal
    observed_at: datetime
    evidence_quality_score: Decimal
    model_disagreement_score: Decimal
    market_noise_score: Decimal
    settlement_ambiguity_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchForecastUncertaintyBandInputRow, "input")
        _require_canonical_string("event_ref", self.event_ref)
        _require_canonical_string("forecast_ref", self.forecast_ref)
        for field_name in (
            "probability",
            "evidence_quality_score",
            "model_disagreement_score",
            "market_noise_score",
            "settlement_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchForecastUncertaintyBandReportRow(_FinalPublicDataclass):
    event_ref: str
    forecast_count: Decimal
    average_probability: Decimal
    minimum_probability: Decimal
    maximum_probability: Decimal
    average_evidence_quality_score: Decimal
    evidence_uncertainty_score: Decimal
    model_disagreement_score: Decimal
    market_noise_score: Decimal
    settlement_ambiguity_score: Decimal
    uncertainty_score: Decimal
    interval_lower_probability: Decimal
    interval_upper_probability: Decimal
    interval_width: Decimal
    status: str
    forecast_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchForecastUncertaintyBandReportRow, "row")
        _require_canonical_string("event_ref", self.event_ref)
        object.__setattr__(
            self,
            "forecast_count",
            _normalize_nonnegative_whole_decimal("forecast_count", self.forecast_count),
        )
        for field_name in (
            "average_probability",
            "minimum_probability",
            "maximum_probability",
            "average_evidence_quality_score",
            "evidence_uncertainty_score",
            "model_disagreement_score",
            "market_noise_score",
            "settlement_ambiguity_score",
            "uncertainty_score",
            "interval_lower_probability",
            "interval_upper_probability",
            "interval_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "forecast_refs",
            _normalize_string_tuple("forecast_refs", self.forecast_refs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchForecastUncertaintyBandReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchForecastUncertaintyBandReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _normalize_probability_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchForecastUncertaintyBandReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    event_count: Decimal
    forecast_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_uncertainty_score: Decimal
    max_uncertainty_score: Decimal
    average_interval_width: Decimal
    status: str
    rows: tuple[ResearchForecastUncertaintyBandReportRow, ...]
    reason_code_counts: tuple[ResearchForecastUncertaintyBandReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchForecastUncertaintyBandReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "forecast_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_uncertainty_score",
            "max_uncertainty_score",
            "average_interval_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchForecastUncertaintyBandConfig,
    ResearchForecastUncertaintyBandInputRow,
    ResearchForecastUncertaintyBandReportRow,
    ResearchForecastUncertaintyBandReasonCodeCount,
    ResearchForecastUncertaintyBandReport,
)


def build_research_forecast_uncertainty_band_report(
    forecasts: Iterable[ResearchForecastUncertaintyBandInputRow],
    *,
    config: ResearchForecastUncertaintyBandConfig,
    generated_at: datetime,
) -> ResearchForecastUncertaintyBandReport:
    if type(config) is not ResearchForecastUncertaintyBandConfig:
        raise ValueError("config must be a ResearchForecastUncertaintyBandConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(forecasts, generated_at_utc)
    grouped: dict[str, list[ResearchForecastUncertaintyBandInputRow]] = {}
    for row in input_rows:
        grouped.setdefault(row.event_ref, []).append(row)
    rows = tuple(
        _build_event_row(
            event_ref=event_ref,
            forecasts=tuple(grouped[event_ref]),
            config=config,
        )
        for event_ref in sorted(grouped)
    )
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = _report_reason_codes(rows, status)
    return ResearchForecastUncertaintyBandReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_count(len(rows)),
        forecast_count=sum((row.forecast_count for row in rows), ZERO),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_uncertainty_score=_mean(tuple(row.uncertainty_score for row in rows)),
        max_uncertainty_score=_max_decimal(tuple(row.uncertainty_score for row in rows)),
        average_interval_width=_mean(tuple(row.interval_width for row in rows)),
        status=status,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def research_forecast_uncertainty_band_report_payload(
    report: ResearchForecastUncertaintyBandReport,
) -> dict[str, Any]:
    if type(report) is not ResearchForecastUncertaintyBandReport:
        raise ValueError("report must be a ResearchForecastUncertaintyBandReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    _reject_unsafe_public_payload("payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_event_row(
    *,
    event_ref: str,
    forecasts: tuple[ResearchForecastUncertaintyBandInputRow, ...],
    config: ResearchForecastUncertaintyBandConfig,
) -> ResearchForecastUncertaintyBandReportRow:
    sorted_forecasts = tuple(sorted(forecasts, key=lambda row: row.forecast_ref))
    probabilities = tuple(row.probability for row in sorted_forecasts)
    forecast_count = _count(len(sorted_forecasts))
    average_probability = _mean(probabilities)
    minimum_probability = min(probabilities)
    maximum_probability = max(probabilities)
    average_evidence_quality_score = _mean(
        tuple(row.evidence_quality_score for row in sorted_forecasts),
    )
    evidence_uncertainty_score = _quantize(ONE - average_evidence_quality_score)
    model_disagreement_score = _max_decimal(
        tuple(row.model_disagreement_score for row in sorted_forecasts),
    )
    market_noise_score = _max_decimal(tuple(row.market_noise_score for row in sorted_forecasts))
    settlement_ambiguity_score = _max_decimal(
        tuple(row.settlement_ambiguity_score for row in sorted_forecasts),
    )
    uncertainty_score = _weighted_uncertainty_score(
        evidence_uncertainty_score=evidence_uncertainty_score,
        model_disagreement_score=model_disagreement_score,
        market_noise_score=market_noise_score,
        settlement_ambiguity_score=settlement_ambiguity_score,
        config=config,
    )
    half_width = _interval_half_width(uncertainty_score, config)
    lower_probability = _clamp_probability(average_probability - half_width)
    upper_probability = _clamp_probability(average_probability + half_width)
    status = _row_status(uncertainty_score, config)
    reason_codes = _row_reason_codes(
        sorted_forecasts,
        evidence_uncertainty_score=evidence_uncertainty_score,
        model_disagreement_score=model_disagreement_score,
        market_noise_score=market_noise_score,
        settlement_ambiguity_score=settlement_ambiguity_score,
        status=status,
    )
    return ResearchForecastUncertaintyBandReportRow(
        event_ref=event_ref,
        forecast_count=forecast_count,
        average_probability=average_probability,
        minimum_probability=minimum_probability,
        maximum_probability=maximum_probability,
        average_evidence_quality_score=average_evidence_quality_score,
        evidence_uncertainty_score=evidence_uncertainty_score,
        model_disagreement_score=model_disagreement_score,
        market_noise_score=market_noise_score,
        settlement_ambiguity_score=settlement_ambiguity_score,
        uncertainty_score=uncertainty_score,
        interval_lower_probability=lower_probability,
        interval_upper_probability=upper_probability,
        interval_width=_quantize(upper_probability - lower_probability),
        status=status,
        forecast_refs=tuple(row.forecast_ref for row in sorted_forecasts),
        reason_codes=reason_codes,
    )


def _weighted_uncertainty_score(
    *,
    evidence_uncertainty_score: Decimal,
    model_disagreement_score: Decimal,
    market_noise_score: Decimal,
    settlement_ambiguity_score: Decimal,
    config: ResearchForecastUncertaintyBandConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = WORKING_PRECISION
        score = (
            evidence_uncertainty_score * config.evidence_quality_weight
            + model_disagreement_score * config.model_disagreement_weight
            + market_noise_score * config.market_noise_weight
            + settlement_ambiguity_score * config.settlement_ambiguity_weight
        )
    return _normalize_probability_decimal("uncertainty_score", score)


def _interval_half_width(
    uncertainty_score: Decimal,
    config: ResearchForecastUncertaintyBandConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = WORKING_PRECISION
        width = config.min_interval_half_width + uncertainty_score * (
            config.max_interval_half_width - config.min_interval_half_width
        )
    return _normalize_probability_decimal("interval_half_width", width)


def _row_reason_codes(
    forecasts: tuple[ResearchForecastUncertaintyBandInputRow, ...],
    *,
    evidence_uncertainty_score: Decimal,
    model_disagreement_score: Decimal,
    market_noise_score: Decimal,
    settlement_ambiguity_score: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes = [
        _band_reason(
            evidence_uncertainty_score,
            low="evidence_quality_strong",
            watch="evidence_quality_watch",
            high="evidence_quality_weak",
        ),
        _band_reason(
            model_disagreement_score,
            low="model_disagreement_low",
            watch="model_disagreement_watch",
            high="model_disagreement_high",
        ),
        _band_reason(
            market_noise_score,
            low="market_noise_low",
            watch="market_noise_watch",
            high="market_noise_high",
        ),
        _band_reason(
            settlement_ambiguity_score,
            low="settlement_ambiguity_low",
            watch="settlement_ambiguity_watch",
            high="settlement_ambiguity_high",
        ),
        f"{ROW_REASON_PREFIX}{status}",
    ]
    for row in forecasts:
        reason_codes.extend(f"input_{reason_code}" for reason_code in row.reason_codes)
    return tuple(sorted(set(reason_codes)))


def _band_reason(value: Decimal, *, low: str, watch: str, high: str) -> str:
    if value <= Decimal("0.250000"):
        return low
    if value >= Decimal("0.650000"):
        return high
    return watch


def _row_status(
    uncertainty_score: Decimal,
    config: ResearchForecastUncertaintyBandConfig,
) -> str:
    if uncertainty_score <= config.pass_max_uncertainty_score:
        return "pass"
    if uncertainty_score <= config.watch_max_uncertainty_score:
        return "watch"
    return "block"


def _report_reason_codes(
    rows: tuple[ResearchForecastUncertaintyBandReportRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return (f"{REPORT_REASON_PREFIX}{status}",)


def _reason_code_counts(
    rows: tuple[ResearchForecastUncertaintyBandReportRow, ...],
) -> tuple[ResearchForecastUncertaintyBandReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchForecastUncertaintyBandReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    event_count = _count(len(rows))
    return tuple(
        ResearchForecastUncertaintyBandReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            event_ratio=_ratio(_count(count), event_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_inputs(
    forecasts: Iterable[ResearchForecastUncertaintyBandInputRow],
    generated_at: datetime,
) -> tuple[ResearchForecastUncertaintyBandInputRow, ...]:
    if isinstance(forecasts, (str, bytes)):
        raise ValueError("forecasts must be an iterable")
    try:
        rows = tuple(forecasts)
    except TypeError as exc:
        raise ValueError("forecasts must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchForecastUncertaintyBandInputRow:
            raise ValueError(
                "forecasts must contain ResearchForecastUncertaintyBandInputRow values",
            )
        _require_hard_flags("input", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.event_ref, row.forecast_ref)
        if key in seen:
            raise ValueError("forecasts must not contain duplicate event_ref and forecast_ref")
        seen.add(key)
    return rows


def _normalize_rows(rows: object) -> tuple[ResearchForecastUncertaintyBandReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchForecastUncertaintyBandReportRow:
            raise ValueError("rows must contain ResearchForecastUncertaintyBandReportRow values")
        if row.event_ref in seen:
            raise ValueError("rows must not contain duplicate event_ref values")
        seen.add(row.event_ref)
    expected = tuple(sorted(rows, key=lambda row: row.event_ref))
    if rows != expected:
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchForecastUncertaintyBandReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchForecastUncertaintyBandReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchForecastUncertaintyBandReasonCodeCount values",
            )
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(row.reason_code)
    expected = tuple(sorted(rows, key=lambda row: (-row.count, row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return rows


def _validate_row(row: ResearchForecastUncertaintyBandReportRow) -> None:
    if row.forecast_count != _count(len(row.forecast_refs)):
        raise ValueError("forecast_count must match forecast_refs")
    if row.minimum_probability > row.maximum_probability:
        raise ValueError("minimum_probability must be <= maximum_probability")
    if not (row.minimum_probability <= row.average_probability <= row.maximum_probability):
        raise ValueError("average_probability must stay within row probabilities")
    if row.evidence_uncertainty_score != _quantize(ONE - row.average_evidence_quality_score):
        raise ValueError("evidence_uncertainty_score must match evidence quality")
    if row.interval_lower_probability > row.interval_upper_probability:
        raise ValueError("interval_lower_probability must be <= interval_upper_probability")
    if row.interval_width != _quantize(
        row.interval_upper_probability - row.interval_lower_probability,
    ):
        raise ValueError("interval_width must match interval endpoints")


def _validate_report(report: ResearchForecastUncertaintyBandReport) -> None:
    rows = report.rows
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    if report.forecast_count != sum((row.forecast_count for row in rows), ZERO):
        raise ValueError("forecast_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_uncertainty_score != _mean(
        tuple(row.uncertainty_score for row in rows),
    ):
        raise ValueError("average_uncertainty_score must match rows")
    if report.max_uncertainty_score != _max_decimal(
        tuple(row.uncertainty_score for row in rows),
    ):
        raise ValueError("max_uncertainty_score must match rows")
    if report.average_interval_width != _mean(tuple(row.interval_width for row in rows)):
        raise ValueError("average_interval_width must match rows")
    expected_status = _rollup_status(tuple(row.status for row in rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchForecastUncertaintyBandReportRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(sum(values, ZERO), _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload contains unsupported dataclass")
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (bool, str):
        return value
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_text(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) is Decimal:
        _require_decimal(path or label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_text(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list or type(value) is tuple:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_TEXT)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(+value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_text(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _normalize_string_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        normalized.append(value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    normalized_tuple = tuple(sorted(set(normalized)))
    if len(normalized_tuple) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized_tuple


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_weights_total_one(config: ResearchForecastUncertaintyBandConfig) -> None:
    total = _quantize(
        config.evidence_quality_weight
        + config.model_disagreement_weight
        + config.market_noise_weight
        + config.settlement_ambiguity_weight,
    )
    if total != ONE:
        raise ValueError("weights must total 1.000000")

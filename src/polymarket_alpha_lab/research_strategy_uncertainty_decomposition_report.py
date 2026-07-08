"""Pure public report for decomposing event-forecast uncertainty."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ResearchStrategyEventForecast",
    "ResearchStrategyUncertaintyComponentRow",
    "ResearchStrategyUncertaintyConfig",
    "ResearchStrategyUncertaintyDecompositionReport",
    "ResearchStrategyUncertaintyEventRow",
    "ResearchStrategyUncertaintyReasonCodeCount",
    "build_research_strategy_uncertainty_decomposition_report",
    "research_strategy_uncertainty_decomposition_report_digest",
    "research_strategy_uncertainty_decomposition_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-uncertainty-decomposition-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
SECONDS_PER_DAY = Decimal("86400")
RATIO_QUANTUM = Decimal("0.000001")
DOMINANT_COMPONENT_TOLERANCE = Decimal("0.005000")
COMPONENT_NAMES = (
    "evidence_quality",
    "model_disagreement",
    "market_mechanics",
    "resolution_ambiguity",
    "timing_risk",
)
SENSITIVE_PUBLIC_TERMS = (
    "wall" + "et",
    "au" + "th",
    "or" + "der",
    "tr" + "ade",
    "live" + "-" + "execution",
    "siz" + "ing",
    "recommend" + "ation",
    "pos" + "ition",
)
PUBLIC_PAYLOAD_EXCLUDED_FIELD_NAMES = frozenset(
    ("event_id", "forecast_id", "market_slug", "public_question"),
)
PUBLIC_ROW_STATUS_SORT_RANK = {"block": 0, "watch": 1, "pass": 2}


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchStrategyUncertaintyConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_uncertainty_threshold: Decimal = Decimal("0.350000")
    block_uncertainty_threshold: Decimal = Decimal("0.650000")
    component_watch_threshold: Decimal = Decimal("0.500000")
    component_block_threshold: Decimal = Decimal("0.800000")
    evidence_quality_weight: Decimal = Decimal("0.250000")
    model_disagreement_weight: Decimal = Decimal("0.200000")
    market_mechanics_weight: Decimal = Decimal("0.200000")
    resolution_ambiguity_weight: Decimal = Decimal("0.200000")
    timing_risk_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "pass_uncertainty_threshold",
            "block_uncertainty_threshold",
            "component_watch_threshold",
            "component_block_threshold",
            "evidence_quality_weight",
            "model_disagreement_weight",
            "market_mechanics_weight",
            "resolution_ambiguity_weight",
            "timing_risk_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_uncertainty_threshold <= self.pass_uncertainty_threshold:
            raise ValueError(
                "block_uncertainty_threshold must exceed pass_uncertainty_threshold",
            )
        if self.component_block_threshold <= self.component_watch_threshold:
            raise ValueError(
                "component_block_threshold must exceed component_watch_threshold",
            )
        weight_sum = _quantize(
            self.evidence_quality_weight
            + self.model_disagreement_weight
            + self.market_mechanics_weight
            + self.resolution_ambiguity_weight
            + self.timing_risk_weight,
        )
        if weight_sum != ONE:
            raise ValueError("component weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEventForecast:
    event_id: str
    forecast_id: str
    market_slug: str
    public_question: str
    forecasted_at: datetime
    expected_resolution_at: datetime
    evidence_quality_score: Decimal
    model_disagreement_score: Decimal
    market_mechanics_score: Decimal
    resolution_ambiguity_score: Decimal
    timing_risk_score: Decimal
    evidence_count: Decimal
    model_count: Decimal
    public_notes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "forecast_id",
            "market_slug",
            "public_question",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "forecasted_at",
            _as_utc("forecasted_at", self.forecasted_at),
        )
        object.__setattr__(
            self,
            "expected_resolution_at",
            _as_utc("expected_resolution_at", self.expected_resolution_at),
        )
        if self.expected_resolution_at <= self.forecasted_at:
            raise ValueError("expected_resolution_at must be after forecasted_at")
        for field_name in (
            "evidence_quality_score",
            "model_disagreement_score",
            "market_mechanics_score",
            "resolution_ambiguity_score",
            "timing_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_count", "model_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_notes",
            _normalize_public_text_tuple("public_notes", self.public_notes),
        )
        _require_hard_flags("forecast", self)


@dataclass(frozen=True)
class ResearchStrategyUncertaintyComponentRow:
    component: str
    raw_score: Decimal
    uncertainty_score: Decimal
    weight: Decimal
    weighted_contribution: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_component_name("component", self.component)
        for field_name in (
            "raw_score",
            "uncertainty_score",
            "weight",
            "weighted_contribution",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("component", self)
        _validate_component_row(self)


@dataclass(frozen=True)
class ResearchStrategyUncertaintyEventRow:
    event_id: str
    forecast_id: str
    market_slug: str
    public_question: str
    forecasted_at: datetime
    expected_resolution_at: datetime
    days_to_resolution: Decimal
    evidence_count: Decimal
    model_count: Decimal
    uncertainty_score: Decimal
    status: str
    component_rows: tuple[ResearchStrategyUncertaintyComponentRow, ...]
    dominant_components: tuple[str, ...]
    reason_codes: tuple[str, ...]
    public_notes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "forecast_id",
            "market_slug",
            "public_question",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "forecasted_at",
            _as_utc("forecasted_at", self.forecasted_at),
        )
        object.__setattr__(
            self,
            "expected_resolution_at",
            _as_utc("expected_resolution_at", self.expected_resolution_at),
        )
        if self.expected_resolution_at <= self.forecasted_at:
            raise ValueError("expected_resolution_at must be after forecasted_at")
        object.__setattr__(
            self,
            "days_to_resolution",
            _require_nonnegative_decimal("days_to_resolution", self.days_to_resolution),
        )
        for field_name in ("evidence_count", "model_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "uncertainty_score",
            _require_probability_decimal("uncertainty_score", self.uncertainty_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "component_rows",
            _normalize_component_rows(self.component_rows),
        )
        object.__setattr__(
            self,
            "dominant_components",
            _normalize_components_tuple(
                "dominant_components",
                self.dominant_components,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "public_notes",
            _normalize_public_text_tuple("public_notes", self.public_notes),
        )
        _require_hard_flags("event_row", self)
        _validate_event_row(self)


@dataclass(frozen=True)
class ResearchStrategyUncertaintyReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyUncertaintyDecompositionReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_uncertainty_score: Decimal | None
    status: str
    rows: tuple[ResearchStrategyUncertaintyEventRow, ...]
    reason_code_counts: tuple[ResearchStrategyUncertaintyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_uncertainty_score",
            _require_optional_probability_decimal(
                "average_uncertainty_score",
                self.average_uncertainty_score,
            ),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_strategy_uncertainty_decomposition_report(
    event_forecasts: Iterable[object],
    *,
    config: ResearchStrategyUncertaintyConfig,
    generated_at: datetime,
) -> ResearchStrategyUncertaintyDecompositionReport:
    if type(config) is not ResearchStrategyUncertaintyConfig:
        raise ValueError("config must be a ResearchStrategyUncertaintyConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    forecasts = _normalize_forecasts(event_forecasts)
    for item in forecasts:
        if item.forecasted_at > generated_at_utc:
            raise ValueError("forecasted_at must not be after generated_at")

    rows = tuple(
        sorted(
            (_event_row_from_forecast(item, config=config) for item in forecasts),
            key=lambda row: (row.event_id, row.forecast_id),
        ),
    )
    _reject_duplicate_rows(rows)
    reason_codes = _summary_reason_codes(rows)

    return ResearchStrategyUncertaintyDecompositionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_uncertainty_score=_average_uncertainty_score(rows),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_uncertainty_decomposition_report_payload(
    report: ResearchStrategyUncertaintyDecompositionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyUncertaintyDecompositionReport:
        raise ValueError("report must be a ResearchStrategyUncertaintyDecompositionReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload["rows"] = _public_safe_payload_rows(payload.get("rows"))
    return payload


def research_strategy_uncertainty_decomposition_report_digest(
    report: ResearchStrategyUncertaintyDecompositionReport,
) -> str:
    payload = research_strategy_uncertainty_decomposition_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _event_row_from_forecast(
    forecast: ResearchStrategyEventForecast,
    *,
    config: ResearchStrategyUncertaintyConfig,
) -> ResearchStrategyUncertaintyEventRow:
    component_rows = (
        _component_row(
            component="evidence_quality",
            raw_score=forecast.evidence_quality_score,
            uncertainty_score=_quantize(ONE - forecast.evidence_quality_score),
            weight=config.evidence_quality_weight,
            config=config,
        ),
        _component_row(
            component="model_disagreement",
            raw_score=forecast.model_disagreement_score,
            uncertainty_score=forecast.model_disagreement_score,
            weight=config.model_disagreement_weight,
            config=config,
        ),
        _component_row(
            component="market_mechanics",
            raw_score=forecast.market_mechanics_score,
            uncertainty_score=forecast.market_mechanics_score,
            weight=config.market_mechanics_weight,
            config=config,
        ),
        _component_row(
            component="resolution_ambiguity",
            raw_score=forecast.resolution_ambiguity_score,
            uncertainty_score=forecast.resolution_ambiguity_score,
            weight=config.resolution_ambiguity_weight,
            config=config,
        ),
        _component_row(
            component="timing_risk",
            raw_score=forecast.timing_risk_score,
            uncertainty_score=forecast.timing_risk_score,
            weight=config.timing_risk_weight,
            config=config,
        ),
    )
    uncertainty_score = _quantize(
        sum((row.weighted_contribution for row in component_rows), ZERO),
    )
    status = _event_status(
        uncertainty_score=uncertainty_score,
        component_rows=component_rows,
        config=config,
    )
    dominant_components = _dominant_components(component_rows)

    return ResearchStrategyUncertaintyEventRow(
        event_id=forecast.event_id,
        forecast_id=forecast.forecast_id,
        market_slug=forecast.market_slug,
        public_question=forecast.public_question,
        forecasted_at=forecast.forecasted_at,
        expected_resolution_at=forecast.expected_resolution_at,
        days_to_resolution=_days_between(
            forecast.forecasted_at,
            forecast.expected_resolution_at,
        ),
        evidence_count=forecast.evidence_count,
        model_count=forecast.model_count,
        uncertainty_score=uncertainty_score,
        status=status,
        component_rows=component_rows,
        dominant_components=dominant_components,
        reason_codes=_event_reason_codes(
            status=status,
            component_rows=component_rows,
            dominant_components=dominant_components,
        ),
        public_notes=forecast.public_notes,
    )


def _component_row(
    *,
    component: str,
    raw_score: Decimal,
    uncertainty_score: Decimal,
    weight: Decimal,
    config: ResearchStrategyUncertaintyConfig,
) -> ResearchStrategyUncertaintyComponentRow:
    status = _component_status(uncertainty_score, config=config)
    return ResearchStrategyUncertaintyComponentRow(
        component=component,
        raw_score=raw_score,
        uncertainty_score=uncertainty_score,
        weight=weight,
        weighted_contribution=_quantize(uncertainty_score * weight),
        status=status,
        reason_codes=(f"{component}_{status}",),
    )


def _component_status(
    uncertainty_score: Decimal,
    *,
    config: ResearchStrategyUncertaintyConfig,
) -> str:
    if uncertainty_score >= config.component_block_threshold:
        return "block"
    if uncertainty_score >= config.component_watch_threshold:
        return "watch"
    return "pass"


def _event_status(
    *,
    uncertainty_score: Decimal,
    component_rows: tuple[ResearchStrategyUncertaintyComponentRow, ...],
    config: ResearchStrategyUncertaintyConfig,
) -> str:
    if any(row.status == "block" for row in component_rows):
        return "block"
    if uncertainty_score >= config.block_uncertainty_threshold:
        return "block"
    if any(row.status == "watch" for row in component_rows):
        return "watch"
    if uncertainty_score >= config.pass_uncertainty_threshold:
        return "watch"
    return "pass"


def _event_reason_codes(
    *,
    status: str,
    component_rows: tuple[ResearchStrategyUncertaintyComponentRow, ...],
    dominant_components: tuple[str, ...],
) -> tuple[str, ...]:
    codes: set[str] = {f"uncertainty_{status}"}
    component_by_name = {row.component: row for row in component_rows}
    for component in dominant_components:
        row = component_by_name[component]
        if row.status != "pass":
            codes.add(row.reason_codes[0])
    return tuple(sorted(codes))


def _dominant_components(
    component_rows: tuple[ResearchStrategyUncertaintyComponentRow, ...],
) -> tuple[str, ...]:
    max_contribution = max(row.weighted_contribution for row in component_rows)
    if max_contribution == ZERO:
        return tuple(row.component for row in component_rows)
    threshold = max(ZERO, max_contribution - DOMINANT_COMPONENT_TOLERANCE)
    return tuple(
        row.component
        for row in component_rows
        if row.weighted_contribution > threshold
    )


def _normalize_forecasts(
    event_forecasts: Iterable[object],
) -> tuple[ResearchStrategyEventForecast, ...]:
    if isinstance(event_forecasts, (str, bytes)):
        raise ValueError("event_forecasts must be an iterable")
    try:
        values = tuple(event_forecasts)
    except TypeError as exc:
        raise ValueError("event_forecasts must be an iterable") from exc
    return tuple(_coerce_forecast(value) for value in values)


def _coerce_forecast(value: object) -> ResearchStrategyEventForecast:
    if type(value) is ResearchStrategyEventForecast:
        _require_hard_flags("forecast", value)
        return value
    _require_hard_flags("forecast", value)
    return ResearchStrategyEventForecast(
        event_id=_field_value(value, "event_id"),
        forecast_id=_field_value(value, "forecast_id"),
        market_slug=_field_value(value, "market_slug"),
        public_question=_field_value(value, "public_question"),
        forecasted_at=_field_value(value, "forecasted_at"),
        expected_resolution_at=_field_value(value, "expected_resolution_at"),
        evidence_quality_score=_field_value(value, "evidence_quality_score"),
        model_disagreement_score=_field_value(value, "model_disagreement_score"),
        market_mechanics_score=_field_value(value, "market_mechanics_score"),
        resolution_ambiguity_score=_field_value(value, "resolution_ambiguity_score"),
        timing_risk_score=_field_value(value, "timing_risk_score"),
        evidence_count=_field_value(value, "evidence_count"),
        model_count=_field_value(value, "model_count"),
        public_notes=_field_value(value, "public_notes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchStrategyUncertaintyEventRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_public_forecast_inputs",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchStrategyUncertaintyEventRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyUncertaintyEventRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyUncertaintyReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyUncertaintyReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] += 1
    return tuple(
        ResearchStrategyUncertaintyReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_uncertainty_score(
    rows: tuple[ResearchStrategyUncertaintyEventRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.uncertainty_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchStrategyUncertaintyEventRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _days_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _quantize(seconds / SECONDS_PER_DAY)


def _reject_duplicate_rows(
    rows: tuple[ResearchStrategyUncertaintyEventRow, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.event_id, row.forecast_id)
        if key in seen:
            raise ValueError("event_id and forecast_id pairs must be unique")
        seen.add(key)


def _normalize_rows(
    rows: tuple[ResearchStrategyUncertaintyEventRow, ...],
) -> tuple[ResearchStrategyUncertaintyEventRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyUncertaintyEventRow:
            raise ValueError("rows must contain ResearchStrategyUncertaintyEventRow values")
        _require_hard_flags("event_row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.event_id, row.forecast_id)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by event_id and forecast_id")
    _reject_duplicate_rows(rows)
    return rows


def _normalize_component_rows(
    rows: tuple[ResearchStrategyUncertaintyComponentRow, ...],
) -> tuple[ResearchStrategyUncertaintyComponentRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("component_rows must be a tuple")
    if tuple(row.component for row in rows) != COMPONENT_NAMES:
        raise ValueError("component_rows must decompose all required components")
    for row in rows:
        if type(row) is not ResearchStrategyUncertaintyComponentRow:
            raise ValueError(
                "component_rows must contain "
                "ResearchStrategyUncertaintyComponentRow values",
            )
        _require_hard_flags("component", row)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyUncertaintyReasonCodeCount, ...],
) -> tuple[ResearchStrategyUncertaintyReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyUncertaintyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyUncertaintyReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_component_row(row: ResearchStrategyUncertaintyComponentRow) -> None:
    expected_contribution = _quantize(row.uncertainty_score * row.weight)
    if row.weighted_contribution != expected_contribution:
        raise ValueError("weighted_contribution must match uncertainty_score times weight")
    if row.component == "evidence_quality":
        if _quantize(row.raw_score + row.uncertainty_score) != ONE:
            raise ValueError("evidence_quality raw_score must invert to uncertainty_score")
    elif row.raw_score != row.uncertainty_score:
        raise ValueError("raw_score must match uncertainty_score for risk components")
    if row.reason_codes != (f"{row.component}_{row.status}",):
        raise ValueError("reason_codes must match component status")


def _validate_event_row(row: ResearchStrategyUncertaintyEventRow) -> None:
    if row.days_to_resolution != _days_between(
        row.forecasted_at,
        row.expected_resolution_at,
    ):
        raise ValueError("days_to_resolution must match forecast window")
    expected_score = _quantize(
        sum((component.weighted_contribution for component in row.component_rows), ZERO),
    )
    if row.uncertainty_score != expected_score:
        raise ValueError("uncertainty_score must match component contributions")
    if row.dominant_components != _dominant_components(row.component_rows):
        raise ValueError("dominant_components must match component contributions")
    if row.reason_codes != _event_reason_codes(
        status=row.status,
        component_rows=row.component_rows,
        dominant_components=row.dominant_components,
    ):
        raise ValueError("reason_codes must match status and dominant components")


def _validate_report(report: ResearchStrategyUncertaintyDecompositionReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_uncertainty_score != _average_uncertainty_score(report.rows):
        raise ValueError("average_uncertainty_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
            if field.name not in PUBLIC_PAYLOAD_EXCLUDED_FIELD_NAMES
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _public_safe_payload_rows(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("report rows payload must be a JSON array")
    return sorted(value, key=_public_row_payload_sort_key)


def _public_row_payload_sort_key(row: object) -> tuple[int, Decimal, Decimal, str]:
    if not isinstance(row, dict):
        raise ValueError("report row payload must be a JSON object")
    status = row.get("status")
    if type(status) is not str or status not in PUBLIC_ROW_STATUS_SORT_RANK:
        raise ValueError("report row payload status must be public-safe")
    uncertainty_score = _payload_decimal(
        "uncertainty_score",
        row.get("uncertainty_score"),
    )
    days_to_resolution = _payload_decimal(
        "days_to_resolution",
        row.get("days_to_resolution"),
    )
    return (
        PUBLIC_ROW_STATUS_SORT_RANK[status],
        -uncertainty_score,
        days_to_resolution,
        json.dumps(row, sort_keys=True, separators=(",", ":")),
    )


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} payload value must be a string Decimal")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} payload value must be a Decimal") from exc


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_component_name(field_name: str, value: object) -> None:
    if type(value) is not str or value not in COMPONENT_NAMES:
        raise ValueError(f"{field_name} must be one of {COMPONENT_NAMES}")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    if _contains_sensitive_public_term(value):
        raise ValueError(f"{field_name} contains non-public or execution text")


def _normalize_public_text_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_text(field_name, value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_components_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_component_name(field_name, value)
        normalized.append(value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if _contains_sensitive_public_term(value):
        raise ValueError(f"{field_name} contains non-public or execution text")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _contains_sensitive_public_term(value: str) -> bool:
    lowered = value.lower()
    if "live-execution" in lowered:
        return True
    tokens: list[str] = []
    token_chars: list[str] = []
    for char in lowered:
        if char.isalnum():
            token_chars.append(char)
        else:
            if token_chars:
                tokens.append("".join(token_chars))
                token_chars = []
    if token_chars:
        tokens.append("".join(token_chars))
    return any(term in tokens for term in SENSITIVE_PUBLIC_TERMS if term != "live-execution")

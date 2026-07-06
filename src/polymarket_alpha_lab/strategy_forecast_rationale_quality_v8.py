"""Report-only forecast rationale quality checks for v8 strategy forecasts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_FORECAST_RATIONALE_QUALITY_V8_CONFIG_VERSION = (
    "strategy-forecast-rationale-quality-v8"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
REQUIRED_RATIONALE_SECTIONS = (
    "base_rate",
    "current_evidence",
    "counter_evidence",
    "resolution_mechanics",
    "cost_ev_sensitivity",
)
RATIONALE_QUALITY_STATUSES = ("pass", "blocked")
REASON_CODES = (
    "forecast_rationale_complete",
    "missing_base_rate",
    "missing_current_evidence",
    "missing_counter_evidence",
    "missing_resolution_mechanics",
    "missing_cost_ev_sensitivity",
    "forecast_rationale_quality_empty",
)


@dataclass(frozen=True)
class StrategyForecastRationaleQualityV8Config:
    config_version: str = DEFAULT_STRATEGY_FORECAST_RATIONALE_QUALITY_V8_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("StrategyForecastRationaleQualityV8Config", self)


@dataclass(frozen=True)
class StrategyForecastRationaleQualityV8Forecast:
    forecast_id: str
    market_slug: str
    team_id: str
    rationale_text: str
    covers_base_rate: bool
    covers_current_evidence: bool
    covers_counter_evidence: bool
    covers_resolution_mechanics: bool
    covers_cost_ev_sensitivity: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("forecast_id", "market_slug", "team_id", "rationale_text"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in _COVERAGE_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        require_paper_only_flags("StrategyForecastRationaleQualityV8Forecast", self)


@dataclass(frozen=True)
class StrategyForecastRationaleQualityV8Row:
    forecast_id: str
    market_slug: str
    team_id: str
    covered_section_count: Decimal
    missing_section_count: Decimal
    rationale_quality_status: str
    missing_sections: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("forecast_id", "market_slug", "team_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "covered_section_count",
            _require_nonnegative_whole_decimal(
                "covered_section_count",
                self.covered_section_count,
            ),
        )
        object.__setattr__(
            self,
            "missing_section_count",
            _require_nonnegative_whole_decimal(
                "missing_section_count",
                self.missing_section_count,
            ),
        )
        _require_status("rationale_quality_status", self.rationale_quality_status)
        object.__setattr__(
            self,
            "missing_sections",
            _normalize_missing_sections(self.missing_sections),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("StrategyForecastRationaleQualityV8Row", self)


@dataclass(frozen=True)
class StrategyForecastRationaleQualityV8Report:
    generated_at: datetime
    config_version: str
    forecast_count: Decimal
    pass_count: Decimal
    blocked_count: Decimal
    rationale_quality_status: str
    missing_sections: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyForecastRationaleQualityV8Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("forecast_count", "pass_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("rationale_quality_status", self.rationale_quality_status)
        object.__setattr__(
            self,
            "missing_sections",
            _normalize_missing_sections(self.missing_sections),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        require_paper_only_flags("StrategyForecastRationaleQualityV8Report", self)


def build_strategy_forecast_rationale_quality_v8_report(
    forecasts: list[StrategyForecastRationaleQualityV8Forecast]
    | tuple[StrategyForecastRationaleQualityV8Forecast, ...],
    *,
    config: StrategyForecastRationaleQualityV8Config,
    generated_at: datetime,
) -> StrategyForecastRationaleQualityV8Report:
    if type(config) is not StrategyForecastRationaleQualityV8Config:
        raise ValueError("config must be a StrategyForecastRationaleQualityV8Config")
    require_paper_only_flags("StrategyForecastRationaleQualityV8Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_forecasts = _normalize_forecasts(forecasts)
    rows = tuple(_row_for_forecast(forecast) for forecast in normalized_forecasts)
    missing_sections = _report_missing_sections(rows)
    reason_codes = _report_reason_codes(rows)

    return StrategyForecastRationaleQualityV8Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        forecast_count=_count(len(rows)),
        pass_count=_count(
            sum(1 for row in rows if row.rationale_quality_status == "pass"),
        ),
        blocked_count=_count(
            sum(1 for row in rows if row.rationale_quality_status == "blocked"),
        ),
        rationale_quality_status=(
            "blocked"
            if any(row.rationale_quality_status == "blocked" for row in rows)
            else "pass"
        ),
        missing_sections=missing_sections,
        reason_codes=reason_codes,
        rows=rows,
    )


def strategy_forecast_rationale_quality_v8_report_payload(
    report: StrategyForecastRationaleQualityV8Report,
) -> dict[str, object]:
    if type(report) is not StrategyForecastRationaleQualityV8Report:
        raise ValueError("report must be a StrategyForecastRationaleQualityV8Report")
    require_paper_only_flags("StrategyForecastRationaleQualityV8Report", report)
    payload = json_ready_no_floats(report)
    reject_unsafe_surface_fields(
        "StrategyForecastRationaleQualityV8Report payload",
        payload,
    )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


_COVERAGE_FIELDS = (
    "covers_base_rate",
    "covers_current_evidence",
    "covers_counter_evidence",
    "covers_resolution_mechanics",
    "covers_cost_ev_sensitivity",
)
_SECTION_BY_FIELD = dict(zip(_COVERAGE_FIELDS, REQUIRED_RATIONALE_SECTIONS))
_REASON_BY_SECTION = {
    "base_rate": "missing_base_rate",
    "current_evidence": "missing_current_evidence",
    "counter_evidence": "missing_counter_evidence",
    "resolution_mechanics": "missing_resolution_mechanics",
    "cost_ev_sensitivity": "missing_cost_ev_sensitivity",
}


def _row_for_forecast(
    forecast: StrategyForecastRationaleQualityV8Forecast,
) -> StrategyForecastRationaleQualityV8Row:
    missing_sections = tuple(
        _SECTION_BY_FIELD[field_name]
        for field_name in _COVERAGE_FIELDS
        if not getattr(forecast, field_name)
    )
    covered_section_count = len(REQUIRED_RATIONALE_SECTIONS) - len(missing_sections)
    return StrategyForecastRationaleQualityV8Row(
        forecast_id=forecast.forecast_id,
        market_slug=forecast.market_slug,
        team_id=forecast.team_id,
        covered_section_count=_count(covered_section_count),
        missing_section_count=_count(len(missing_sections)),
        rationale_quality_status="blocked" if missing_sections else "pass",
        missing_sections=missing_sections,
        reason_codes=_reason_codes_for_missing_sections(missing_sections),
    )


def _normalize_forecasts(
    forecasts: list[StrategyForecastRationaleQualityV8Forecast]
    | tuple[StrategyForecastRationaleQualityV8Forecast, ...],
) -> tuple[StrategyForecastRationaleQualityV8Forecast, ...]:
    if type(forecasts) not in (list, tuple):
        raise ValueError("forecasts must be a list or tuple")
    normalized = tuple(forecasts)
    for forecast in normalized:
        if type(forecast) is not StrategyForecastRationaleQualityV8Forecast:
            raise ValueError(
                "forecasts must contain "
                "StrategyForecastRationaleQualityV8Forecast values",
            )
        require_paper_only_flags("StrategyForecastRationaleQualityV8Forecast", forecast)
    return normalized


def _normalize_rows(
    rows: list[StrategyForecastRationaleQualityV8Row]
    | tuple[StrategyForecastRationaleQualityV8Row, ...],
) -> tuple[StrategyForecastRationaleQualityV8Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyForecastRationaleQualityV8Row:
            raise ValueError(
                "rows must contain StrategyForecastRationaleQualityV8Row values",
            )
        require_paper_only_flags("StrategyForecastRationaleQualityV8Row", row)
    return normalized


def _validate_row_consistency(row: StrategyForecastRationaleQualityV8Row) -> None:
    expected_reason_codes = _reason_codes_for_missing_sections(row.missing_sections)
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match missing_sections")
    expected_status = "blocked" if row.missing_sections else "pass"
    if row.rationale_quality_status != expected_status:
        raise ValueError("rationale_quality_status must match missing_sections")
    if row.missing_section_count != _count(len(row.missing_sections)):
        raise ValueError("missing_section_count must match missing_sections")
    if row.covered_section_count != _count(
        len(REQUIRED_RATIONALE_SECTIONS) - len(row.missing_sections),
    ):
        raise ValueError("covered_section_count must match missing_sections")
    if row.covered_section_count + row.missing_section_count != _count(
        len(REQUIRED_RATIONALE_SECTIONS),
    ):
        raise ValueError("section counts must match required rationale sections")


def _validate_report_consistency(report: StrategyForecastRationaleQualityV8Report) -> None:
    rows = report.rows
    if report.forecast_count != _count(len(rows)):
        raise ValueError("forecast_count must match rows")
    if report.pass_count != _count(
        sum(1 for row in rows if row.rationale_quality_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.blocked_count != _count(
        sum(1 for row in rows if row.rationale_quality_status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    if report.missing_sections != _report_missing_sections(rows):
        raise ValueError("missing_sections must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    expected_status = "blocked" if report.blocked_count > ZERO else "pass"
    if report.rationale_quality_status != expected_status:
        raise ValueError("rationale_quality_status must match rows")


def _report_missing_sections(
    rows: tuple[StrategyForecastRationaleQualityV8Row, ...],
) -> tuple[str, ...]:
    seen = {section for row in rows for section in row.missing_sections}
    return tuple(section for section in REQUIRED_RATIONALE_SECTIONS if section in seen)


def _report_reason_codes(
    rows: tuple[StrategyForecastRationaleQualityV8Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("forecast_rationale_quality_empty",)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)


def _reason_codes_for_missing_sections(
    missing_sections: tuple[str, ...],
) -> tuple[str, ...]:
    if not missing_sections:
        return ("forecast_rationale_complete",)
    return tuple(_REASON_BY_SECTION[section] for section in missing_sections)


def _normalize_missing_sections(
    missing_sections: tuple[str, ...],
) -> tuple[str, ...]:
    if type(missing_sections) not in (list, tuple):
        raise ValueError("missing_sections must be a list or tuple")
    normalized = tuple(missing_sections)
    for section in normalized:
        _require_canonical_string("missing_sections", section)
        if section not in REQUIRED_RATIONALE_SECTIONS:
            raise ValueError("missing_sections must be required rationale sections")
    if len(set(normalized)) != len(normalized):
        raise ValueError("missing_sections must be unique")
    expected_order = tuple(
        section for section in REQUIRED_RATIONALE_SECTIONS if section in normalized
    )
    if normalized != expected_order:
        raise ValueError("missing_sections must be deterministic")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must be known forecast rationale reasons")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    expected_order = tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)
    if normalized != expected_order:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in RATIONALE_QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be one of {RATIONALE_QUALITY_STATUSES!r}")


__all__ = (
    "DEFAULT_STRATEGY_FORECAST_RATIONALE_QUALITY_V8_CONFIG_VERSION",
    "REQUIRED_RATIONALE_SECTIONS",
    "StrategyForecastRationaleQualityV8Config",
    "StrategyForecastRationaleQualityV8Forecast",
    "StrategyForecastRationaleQualityV8Report",
    "StrategyForecastRationaleQualityV8Row",
    "build_strategy_forecast_rationale_quality_v8_report",
    "strategy_forecast_rationale_quality_v8_report_payload",
)

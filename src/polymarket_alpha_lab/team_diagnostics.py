"""Public Phase 1 facade for team diagnostics reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module
from typing import Any, Callable

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_TEAM_DIAGNOSTICS_CONFIG_VERSION = "team-diagnostics-v0"

_BUNDLE_COUNT_FIELDS = (
    "forecast_row_count",
    "evidence_row_count",
    "outcome_row_count",
)
_NESTED_REPORT_FIELDS = (
    ("memory_synthesis", "memory_synthesis_report"),
    ("forecast_calibration", "forecast_calibration_report"),
    ("event_template_performance", "event_template_performance_report"),
    ("source_reliability", "source_reliability_report"),
    ("evidence_quality", "evidence_quality_report"),
)
_NESTED_SUMMARY_FIELDS = (
    "config_version",
    "forecast_row_count",
    "evidence_row_count",
    "outcome_row_count",
    "reference_count",
    "forecast_count",
    "settled_count",
    "row_count",
    "total_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "status",
)

BundleBuilder = Callable[..., object]


@dataclass(frozen=True)
class TeamDiagnosticsRow:
    section: str
    label: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("section", self.section)
        _require_canonical_string("label", self.label)
        _require_canonical_string("value", self.value)
        require_paper_only_flags("TeamDiagnosticsRow", self)


@dataclass(frozen=True)
class TeamDiagnosticsConfig:
    config_version: str = DEFAULT_TEAM_DIAGNOSTICS_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("TeamDiagnosticsConfig", self)


@dataclass(frozen=True)
class TeamDiagnosticsReport:
    generated_at: datetime
    config_version: str
    rows: tuple[TeamDiagnosticsRow, ...]
    row_count: int
    bundle_report: object | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_nonnegative_int("row_count", self.row_count)
        if self.row_count != len(self.rows):
            raise ValueError("row_count must match rows")
        if self.bundle_report is not None:
            require_paper_only_flags("bundle_report", self.bundle_report)
        require_paper_only_flags("TeamDiagnosticsReport", self)


def build_team_diagnostics_report(
    forecasts: object,
    evidence: object,
    outcomes: object,
    *,
    config: TeamDiagnosticsConfig,
    generated_at: datetime,
    bundle_builder: BundleBuilder | None = None,
) -> TeamDiagnosticsReport:
    if type(config) is not TeamDiagnosticsConfig:
        raise ValueError("config must be a TeamDiagnosticsConfig")
    require_paper_only_flags("TeamDiagnosticsConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)

    forecast_rows = _normalize_iterable("forecasts", forecasts)
    evidence_rows = _normalize_iterable("evidence", evidence)
    outcome_rows = _normalize_iterable("outcomes", outcomes)
    bundle_report = _build_bundle_report(
        forecast_rows,
        evidence_rows,
        outcome_rows,
        generated_at=generated_at_utc,
        bundle_builder=bundle_builder,
    )
    rows = _input_rows(forecast_rows, evidence_rows, outcome_rows) + _bundle_rows(
        bundle_report,
    )
    return TeamDiagnosticsReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
        row_count=len(rows),
        bundle_report=bundle_report,
    )


def _build_bundle_report(
    forecasts: tuple[object, ...],
    evidence: tuple[object, ...],
    outcomes: tuple[object, ...],
    *,
    generated_at: datetime,
    bundle_builder: BundleBuilder | None,
) -> object | None:
    builder = bundle_builder if bundle_builder is not None else _default_bundle_builder()
    if builder is None:
        return None
    try:
        report = builder(
            forecasts,
            evidence,
            outcomes,
            generated_at=generated_at,
        )
    except TypeError as exc:
        if bundle_builder is None:
            return None
        raise exc
    if report is None:
        return None
    require_paper_only_flags("bundle_report", report)
    return report


def _default_bundle_builder() -> BundleBuilder | None:
    try:
        module = import_module("polymarket_alpha_lab.team_diagnostics_bundle")
    except (ImportError, ModuleNotFoundError):
        return None

    build_report = getattr(module, "build_team_diagnostics_bundle_report", None)
    bundle_config_type = getattr(module, "TeamDiagnosticsBundleConfig", None)
    if build_report is None or bundle_config_type is None:
        return None

    def build_with_default_config(
        forecasts: object,
        evidence: object,
        outcomes: object,
        *,
        generated_at: datetime,
    ) -> object:
        return build_report(
            forecasts,
            evidence,
            outcomes,
            config=bundle_config_type(),
            generated_at=generated_at,
        )

    return build_with_default_config


def _input_rows(
    forecasts: tuple[object, ...],
    evidence: tuple[object, ...],
    outcomes: tuple[object, ...],
) -> tuple[TeamDiagnosticsRow, ...]:
    return (
        TeamDiagnosticsRow("input", "forecast_row_count", str(len(forecasts))),
        TeamDiagnosticsRow("input", "evidence_row_count", str(len(evidence))),
        TeamDiagnosticsRow("input", "outcome_row_count", str(len(outcomes))),
    )


def _bundle_rows(bundle_report: object | None) -> tuple[TeamDiagnosticsRow, ...]:
    if bundle_report is None:
        return ()

    rows: list[TeamDiagnosticsRow] = []
    _append_row_from_attr(rows, "bundle", bundle_report, "config_version")
    for field_name in _BUNDLE_COUNT_FIELDS:
        _append_row_from_attr(rows, "bundle", bundle_report, field_name)

    for section, field_name in _NESTED_REPORT_FIELDS:
        nested_report = getattr(bundle_report, field_name, None)
        if nested_report is None:
            continue
        require_paper_only_flags(field_name, nested_report)
        for summary_field_name in _NESTED_SUMMARY_FIELDS:
            _append_row_from_attr(rows, section, nested_report, summary_field_name)
    return tuple(rows)


def _append_row_from_attr(
    rows: list[TeamDiagnosticsRow],
    section: str,
    value_source: object,
    field_name: str,
) -> None:
    if not hasattr(value_source, field_name):
        return
    rows.append(
        TeamDiagnosticsRow(
            section,
            field_name,
            _canonical_value(getattr(value_source, field_name)),
        ),
    )


def _canonical_value(value: object) -> str:
    if isinstance(value, float):
        raise ValueError("diagnostics rows must not contain float values")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("diagnostics Decimal values must be finite")
        return str(value)
    if type(value) in (str, int, bool):
        return str(value)
    if value is None:
        return "None"
    raise ValueError("diagnostics row values must be scalar")


def _normalize_iterable(field_name: str, value: object) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc


def _normalize_rows(rows: object) -> tuple[TeamDiagnosticsRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not TeamDiagnosticsRow:
            raise ValueError("rows must contain TeamDiagnosticsRow values")
        require_paper_only_flags("TeamDiagnosticsRow", row)
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


__all__ = (
    "TeamDiagnosticsConfig",
    "TeamDiagnosticsReport",
    "TeamDiagnosticsRow",
    "build_team_diagnostics_report",
)

"""Pure compact snapshot reducer for team diagnostics bundles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_diagnostics_bundle import TeamDiagnosticsBundleReport
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_CONFIG_VERSION = "team-diagnostics-snapshot-v0"
_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FILTER_NAMES = ("team_id", "market_slug", "forecast_id")


@dataclass(frozen=True)
class TeamDiagnosticsSnapshotConfig:
    config_version: str = DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("team diagnostics snapshot config", self)


@dataclass(frozen=True)
class TeamDiagnosticsSnapshotReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    filters: tuple[tuple[str, str], ...]
    forecast_row_count: int
    evidence_row_count: int
    outcome_row_count: int
    memory_eligible_reference_count: int
    calibration_status: str
    calibration_settled_count: int
    calibration_group_count: int
    event_template_row_count: int
    event_template_status: str
    source_reliability_row_count: int
    source_reliability_missing_source_evidence_count: int
    evidence_quality_status: str
    evidence_quality_pass_count: int
    evidence_quality_watch_count: int
    evidence_quality_blocked_count: int
    evidence_quality_average_quality_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        object.__setattr__(self, "filters", _normalize_filters(self.filters))
        for field_name in (
            "forecast_row_count",
            "evidence_row_count",
            "outcome_row_count",
            "memory_eligible_reference_count",
            "calibration_settled_count",
            "calibration_group_count",
            "event_template_row_count",
            "source_reliability_row_count",
            "source_reliability_missing_source_evidence_count",
            "evidence_quality_pass_count",
            "evidence_quality_watch_count",
            "evidence_quality_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_canonical_string("calibration_status", self.calibration_status)
        _require_canonical_string("event_template_status", self.event_template_status)
        _require_canonical_string("evidence_quality_status", self.evidence_quality_status)
        object.__setattr__(
            self,
            "evidence_quality_average_quality_score",
            _normalize_probability(
                "evidence_quality_average_quality_score",
                self.evidence_quality_average_quality_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_count_alignment(self)
        require_paper_only_flags("team diagnostics snapshot report", self)


def build_team_diagnostics_snapshot_report(
    bundle_report: TeamDiagnosticsBundleReport,
    *,
    config: TeamDiagnosticsSnapshotConfig,
    team_id: str | None = None,
    market_slug: str | None = None,
    forecast_id: str | None = None,
) -> TeamDiagnosticsSnapshotReport:
    if type(config) is not TeamDiagnosticsSnapshotConfig:
        raise ValueError("config must be a TeamDiagnosticsSnapshotConfig")
    require_paper_only_flags("team diagnostics snapshot config", config)
    if type(bundle_report) is not TeamDiagnosticsBundleReport:
        raise ValueError("bundle_report must be a TeamDiagnosticsBundleReport")
    require_paper_only_flags("team diagnostics bundle report", bundle_report)

    return TeamDiagnosticsSnapshotReport(
        generated_at=bundle_report.generated_at,
        config_version=config.config_version,
        source_config_version=bundle_report.config_version,
        filters=_build_filters(
            team_id=team_id,
            market_slug=market_slug,
            forecast_id=forecast_id,
        ),
        forecast_row_count=bundle_report.forecast_row_count,
        evidence_row_count=bundle_report.evidence_row_count,
        outcome_row_count=bundle_report.outcome_row_count,
        memory_eligible_reference_count=(
            bundle_report.memory_synthesis_report.eligible_reference_count
        ),
        calibration_status=bundle_report.forecast_calibration_report.status,
        calibration_settled_count=(
            bundle_report.forecast_calibration_report.settled_count
        ),
        calibration_group_count=len(bundle_report.forecast_calibration_report.groups),
        event_template_row_count=(
            bundle_report.event_template_performance_report.row_count
        ),
        event_template_status=bundle_report.event_template_performance_report.status,
        source_reliability_row_count=bundle_report.source_reliability_report.row_count,
        source_reliability_missing_source_evidence_count=(
            bundle_report.source_reliability_report.missing_source_evidence_count
        ),
        evidence_quality_status=bundle_report.evidence_quality_report.status,
        evidence_quality_pass_count=bundle_report.evidence_quality_report.pass_count,
        evidence_quality_watch_count=bundle_report.evidence_quality_report.watch_count,
        evidence_quality_blocked_count=bundle_report.evidence_quality_report.blocked_count,
        evidence_quality_average_quality_score=(
            bundle_report.evidence_quality_report.average_quality_score
        ),
        reason_codes=_bundle_reason_codes(bundle_report),
    )


def _build_filters(
    *,
    team_id: str | None,
    market_slug: str | None,
    forecast_id: str | None,
) -> tuple[tuple[str, str], ...]:
    values = {
        "team_id": team_id,
        "market_slug": market_slug,
        "forecast_id": forecast_id,
    }
    filters: list[tuple[str, str]] = []
    for name in _FILTER_NAMES:
        value = values[name]
        if value is None:
            continue
        _require_canonical_string(name, value)
        filters.append((name, value))
    return tuple(filters)


def _bundle_reason_codes(
    bundle_report: TeamDiagnosticsBundleReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    reason_codes.extend(bundle_report.forecast_calibration_report.reason_codes)
    reason_codes.extend(bundle_report.event_template_performance_report.reason_codes)
    reason_codes.extend(bundle_report.evidence_quality_report.reason_code_counts)
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_filters(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, dict):
        raw_items = tuple(value.items())
    elif isinstance(value, (str, bytes)):
        raise ValueError("filters must be filter pairs")
    else:
        try:
            raw_items = tuple(value)  # type: ignore[arg-type]
        except TypeError as exc:
            raise ValueError("filters must be filter pairs") from exc

    values_by_name: dict[str, str] = {}
    for item in raw_items:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("filters must be filter pairs")
        name, filter_value = item
        if name not in _FILTER_NAMES:
            raise ValueError("filters must use known filter names")
        if name in values_by_name:
            raise ValueError("filters must not contain duplicate names")
        _require_canonical_string(name, filter_value)
        values_by_name[name] = filter_value
    return tuple(
        (name, values_by_name[name])
        for name in _FILTER_NAMES
        if name in values_by_name
    )


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain canonical strings") from exc
    for item in items:
        _require_canonical_string("reason_codes", item)
    return tuple(sorted(set(items)))


def _validate_count_alignment(report: TeamDiagnosticsSnapshotReport) -> None:
    quality_count = (
        report.evidence_quality_pass_count
        + report.evidence_quality_watch_count
        + report.evidence_quality_blocked_count
    )
    if quality_count != report.evidence_row_count:
        raise ValueError("evidence quality counts must match evidence_row_count")
    if report.calibration_settled_count > report.forecast_row_count:
        raise ValueError("calibration_settled_count must not exceed forecast_row_count")
    if report.source_reliability_missing_source_evidence_count > report.evidence_row_count:
        raise ValueError(
            "source_reliability_missing_source_evidence_count must not exceed evidence_row_count",
        )


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_QUANTUM)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
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
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


__all__ = (
    "DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_CONFIG_VERSION",
    "TeamDiagnosticsSnapshotConfig",
    "TeamDiagnosticsSnapshotReport",
    "build_team_diagnostics_snapshot_report",
)

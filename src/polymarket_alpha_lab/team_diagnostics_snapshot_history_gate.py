"""Pure gate reducer for team diagnostics snapshot history reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryReport,
)


DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_HISTORY_GATE_CONFIG_VERSION = (
    "team-diagnostics-snapshot-history-gate-v0"
)

QUANTUM = Decimal("0.000001")

PASS_REASON = "team_diagnostics_snapshot_history_gate_passed"
INSUFFICIENT_HISTORY_REASON = "insufficient_team_diagnostics_snapshot_history_samples"
STALE_HISTORY_REASON = "stale_team_diagnostics_snapshot_history"
DUPLICATE_LATEST_REASON = (
    "duplicate_latest_team_diagnostics_snapshot_history_generated_at"
)
EVIDENCE_QUALITY_REASON = (
    "team_diagnostics_snapshot_history_evidence_quality_deteriorated"
)
MEMORY_COVERAGE_REASON = (
    "team_diagnostics_snapshot_history_memory_coverage_deteriorated"
)
SETTLED_CALIBRATION_REASON = (
    "team_diagnostics_snapshot_history_settled_calibration_deteriorated"
)
SOURCE_REASON_CODES_REASON = (
    "team_diagnostics_snapshot_history_source_reason_codes_present"
)

BLOCKED_REASONS = (
    INSUFFICIENT_HISTORY_REASON,
    STALE_HISTORY_REASON,
    DUPLICATE_LATEST_REASON,
)
WATCH_REASONS = (
    EVIDENCE_QUALITY_REASON,
    MEMORY_COVERAGE_REASON,
    SETTLED_CALIBRATION_REASON,
    SOURCE_REASON_CODES_REASON,
)
GATE_REASONS = (PASS_REASON,) + BLOCKED_REASONS + WATCH_REASONS

NEXT_STEPS = {
    "pass": "allow_team_diagnostics_snapshot_history_memory_use",
    "watch": "throttle_team_diagnostics_snapshot_history_memory_use",
    "blocked": "block_team_diagnostics_snapshot_history_memory_use",
}

__all__ = (
    "DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_HISTORY_GATE_CONFIG_VERSION",
    "TeamDiagnosticsSnapshotHistoryGateConfig",
    "TeamDiagnosticsSnapshotHistoryGateReasonCodeCount",
    "TeamDiagnosticsSnapshotHistoryGateReport",
    "build_team_diagnostics_snapshot_history_gate_report",
)


@dataclass(frozen=True)
class TeamDiagnosticsSnapshotHistoryGateConfig:
    config_version: str = (
        DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_HISTORY_GATE_CONFIG_VERSION
    )
    min_source_snapshot_count: int = 3
    max_latest_snapshot_age_seconds: int = 86_400
    min_evidence_quality_average_delta: Decimal = Decimal("-0.050000")
    min_memory_eligible_delta: int = 0
    min_settled_calibration_delta: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_source_snapshot_count", self.min_source_snapshot_count)
        _require_nonnegative_int(
            "max_latest_snapshot_age_seconds",
            self.max_latest_snapshot_age_seconds,
        )
        object.__setattr__(
            self,
            "min_evidence_quality_average_delta",
            _normalize_decimal(
                "min_evidence_quality_average_delta",
                self.min_evidence_quality_average_delta,
            ),
        )
        _require_int("min_memory_eligible_delta", self.min_memory_eligible_delta)
        _require_int(
            "min_settled_calibration_delta",
            self.min_settled_calibration_delta,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamDiagnosticsSnapshotHistoryGateReasonCodeCount:
    reason_code: str
    count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("count", self.count)
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class TeamDiagnosticsSnapshotHistoryGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime | None
    latest_snapshot_age_seconds: int | None
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[TeamDiagnosticsSnapshotHistoryGateReasonCodeCount, ...]
    source_snapshot_count: int
    source_required_snapshot_count: int
    source_status: str
    source_span_seconds: int
    source_status_counts: tuple[tuple[str, int], ...]
    source_reason_codes: tuple[str, ...]
    evidence_quality_average_delta: Decimal
    memory_eligible_delta: int
    settled_calibration_delta: int
    duplicate_latest_generated_at: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        if self.source_generated_at is not None:
            object.__setattr__(
                self,
                "source_generated_at",
                _as_utc("source_generated_at", self.source_generated_at),
            )
        if self.latest_snapshot_age_seconds is not None:
            _require_nonnegative_int(
                "latest_snapshot_age_seconds",
                self.latest_snapshot_age_seconds,
            )
        _require_gate_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_nonnegative_int("source_snapshot_count", self.source_snapshot_count)
        _require_positive_int(
            "source_required_snapshot_count",
            self.source_required_snapshot_count,
        )
        _require_canonical_string("source_status", self.source_status)
        _require_nonnegative_int("source_span_seconds", self.source_span_seconds)
        object.__setattr__(
            self,
            "source_status_counts",
            _normalize_status_counts(self.source_status_counts),
        )
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_reason_codes(
                "source_reason_codes",
                self.source_reason_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "evidence_quality_average_delta",
            _normalize_decimal(
                "evidence_quality_average_delta",
                self.evidence_quality_average_delta,
            ),
        )
        _require_int("memory_eligible_delta", self.memory_eligible_delta)
        _require_int("settled_calibration_delta", self.settled_calibration_delta)
        if type(self.duplicate_latest_generated_at) is not bool:
            raise ValueError("duplicate_latest_generated_at must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_gate_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_team_diagnostics_snapshot_history_gate_report(
    source_report: TeamDiagnosticsSnapshotHistoryReport,
    *,
    config: TeamDiagnosticsSnapshotHistoryGateConfig,
    generated_at: datetime,
) -> TeamDiagnosticsSnapshotHistoryGateReport:
    if type(source_report) is not TeamDiagnosticsSnapshotHistoryReport:
        raise ValueError("source_report must be a TeamDiagnosticsSnapshotHistoryReport")
    if type(config) is not TeamDiagnosticsSnapshotHistoryGateConfig:
        raise ValueError("config must be a TeamDiagnosticsSnapshotHistoryGateConfig")

    _require_hard_flags("source_report", source_report)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_generated_at = _optional_as_utc(
        "source_generated_at",
        source_report.latest_generated_at,
    )
    source_required_snapshot_count = _effective_source_required_snapshot_count(
        source_report,
        config,
    )
    latest_snapshot_age_seconds = _latest_snapshot_age_seconds(
        generated_at_utc,
        source_generated_at,
    )

    reason_codes = _gate_reason_codes(
        source_report,
        config=config,
        latest_snapshot_age_seconds=latest_snapshot_age_seconds,
    )
    gate_status = _expected_gate_status(reason_codes)

    return TeamDiagnosticsSnapshotHistoryGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_config_version=source_report.config_version,
        source_generated_at=source_generated_at,
        latest_snapshot_age_seconds=latest_snapshot_age_seconds,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEPS[gate_status],
        reason_code_counts=_reason_code_counts(reason_codes),
        source_snapshot_count=source_report.snapshot_count,
        source_required_snapshot_count=source_required_snapshot_count,
        source_status=source_report.status,
        source_span_seconds=source_report.span_seconds,
        source_status_counts=source_report.status_counts,
        source_reason_codes=source_report.reason_codes,
        evidence_quality_average_delta=source_report.evidence_quality_average_delta,
        memory_eligible_delta=source_report.memory_eligible_delta,
        settled_calibration_delta=source_report.settled_calibration_delta,
        duplicate_latest_generated_at=source_report.duplicate_latest_generated_at,
        reason_codes=reason_codes,
    )


def _gate_reason_codes(
    source_report: TeamDiagnosticsSnapshotHistoryReport,
    *,
    config: TeamDiagnosticsSnapshotHistoryGateConfig,
    latest_snapshot_age_seconds: int | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if (
        source_report.snapshot_count
        < _effective_source_required_snapshot_count(source_report, config)
        or source_report.status == "insufficient_history"
    ):
        reasons.append(INSUFFICIENT_HISTORY_REASON)
    if (
        source_report.latest_generated_at is None
        or latest_snapshot_age_seconds is None
        or latest_snapshot_age_seconds > config.max_latest_snapshot_age_seconds
    ):
        reasons.append(STALE_HISTORY_REASON)
    if source_report.duplicate_latest_generated_at:
        reasons.append(DUPLICATE_LATEST_REASON)

    if reasons:
        return tuple(reasons)

    if (
        _normalize_decimal(
            "evidence_quality_average_delta",
            source_report.evidence_quality_average_delta,
        )
        < config.min_evidence_quality_average_delta
    ):
        reasons.append(EVIDENCE_QUALITY_REASON)
    if source_report.memory_eligible_delta < config.min_memory_eligible_delta:
        reasons.append(MEMORY_COVERAGE_REASON)
    if source_report.settled_calibration_delta < config.min_settled_calibration_delta:
        reasons.append(SETTLED_CALIBRATION_REASON)
    if source_report.reason_codes:
        reasons.append(SOURCE_REASON_CODES_REASON)

    return tuple(reasons) if reasons else (PASS_REASON,)


def _effective_source_required_snapshot_count(
    source_report: TeamDiagnosticsSnapshotHistoryReport,
    config: TeamDiagnosticsSnapshotHistoryGateConfig,
) -> int:
    return max(source_report.required_snapshot_count, config.min_source_snapshot_count)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[TeamDiagnosticsSnapshotHistoryGateReasonCodeCount, ...]:
    return tuple(
        TeamDiagnosticsSnapshotHistoryGateReasonCodeCount(
            reason_code=reason_code,
            count=1,
        )
        for reason_code in reason_codes
    )


def _latest_snapshot_age_seconds(
    generated_at: datetime,
    source_generated_at: datetime | None,
) -> int | None:
    if source_generated_at is None:
        return None
    age_seconds = int((generated_at - source_generated_at).total_seconds())
    if age_seconds < 0:
        raise ValueError("latest_snapshot_age_seconds must be nonnegative")
    return age_seconds


def _validate_report_consistency(
    report: TeamDiagnosticsSnapshotHistoryGateReport,
) -> None:
    expected_gate_status = _expected_gate_status(report.reason_codes)
    if report.gate_status != expected_gate_status:
        raise ValueError("gate_status must match reason_codes")
    if report.recommended_next_step != NEXT_STEPS[report.gate_status]:
        raise ValueError("recommended_next_step must match gate_status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must summarize reason_codes in order")
    if report.source_generated_at is None:
        if report.latest_snapshot_age_seconds is not None:
            raise ValueError("latest_snapshot_age_seconds must be None without source")
        if STALE_HISTORY_REASON not in report.reason_codes:
            raise ValueError("reason_codes must include stale history")
    elif report.latest_snapshot_age_seconds != _latest_snapshot_age_seconds(
        report.generated_at,
        report.source_generated_at,
    ):
        raise ValueError("latest_snapshot_age_seconds must match source age")
    if (
        report.source_snapshot_count < report.source_required_snapshot_count
        or report.source_status == "insufficient_history"
    ) and INSUFFICIENT_HISTORY_REASON not in report.reason_codes:
        raise ValueError("reason_codes must include insufficient history")
    if report.duplicate_latest_generated_at and DUPLICATE_LATEST_REASON not in (
        report.reason_codes
    ):
        raise ValueError("reason_codes must include duplicate latest generated_at")
    has_blocked_reason = any(reason in BLOCKED_REASONS for reason in report.reason_codes)
    if (
        report.source_reason_codes
        and not has_blocked_reason
        and SOURCE_REASON_CODES_REASON not in report.reason_codes
    ):
        raise ValueError("reason_codes must include source reason codes")


def _expected_gate_status(reason_codes: tuple[str, ...]) -> str:
    if PASS_REASON in reason_codes:
        if reason_codes != (PASS_REASON,):
            raise ValueError("reason_codes must not combine pass and non-pass reasons")
        return "pass"
    if any(reason in BLOCKED_REASONS for reason in reason_codes):
        return "blocked"
    if any(reason in WATCH_REASONS for reason in reason_codes):
        return "watch"
    raise ValueError("reason_codes must contain known gate reasons")


def _normalize_gate_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    items = _normalize_reason_codes("reason_codes", reason_codes, allow_empty=False)
    for reason_code in items:
        if reason_code not in GATE_REASONS:
            raise ValueError("reason_codes must contain known gate reasons")
    return items


def _normalize_reason_code_counts(
    reason_code_counts: tuple[TeamDiagnosticsSnapshotHistoryGateReasonCodeCount, ...],
) -> tuple[TeamDiagnosticsSnapshotHistoryGateReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    items = tuple(reason_code_counts)
    for item in items:
        if type(item) is not TeamDiagnosticsSnapshotHistoryGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", item)
    return items


def _normalize_status_counts(
    status_counts: tuple[tuple[str, int], ...],
) -> tuple[tuple[str, int], ...]:
    if type(status_counts) not in (list, tuple):
        raise ValueError("source_status_counts must be a list or tuple")
    normalized = tuple(status_counts)
    seen_statuses: set[str] = set()
    for item in normalized:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("source_status_counts entries must be status/count pairs")
        status, count = item
        _require_canonical_string("source_status_counts status", status)
        _require_nonnegative_int("source_status_counts count", count)
        if status in seen_statuses:
            raise ValueError("source_status_counts statuses must be unique")
        seen_statuses.add(status)
    return normalized


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(reason_codes)
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for reason_code in items:
        _require_canonical_string(field_name, reason_code)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    return items


def _optional_as_utc(name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(name, value)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(QUANTUM)


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_gate_status(name: str, value: object) -> None:
    if type(value) is not str or value not in NEXT_STEPS:
        raise ValueError(f"{name} must be pass, watch, or blocked")


def _require_int(name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{name} must be an int")


def _require_nonnegative_int(name: str, value: object) -> None:
    _require_int(name, value)
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")


def _require_positive_int(name: str, value: object) -> None:
    _require_int(name, value)
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")

"""Pure Phase 2 state streak reducer over observability state reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from polymarket_alpha_lab.phase_2_observability_state import (
    BLOCKING_REASON_NAMES,
    PaperPhase2ObservabilityStateReport,
)


@dataclass(frozen=True)
class PaperPhase2ReadinessStreakConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2ReadinessStreakReport:
    generated_at: datetime
    config_version: str
    state_report_count: int
    latest_phase_2_ready: bool | None
    consecutive_ready_count: int
    consecutive_not_ready_count: int
    ready_report_count: int
    not_ready_report_count: int
    latest_blocking_reason_names: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("state_report_count", self.state_report_count)
        _require_nonnegative_int(
            "consecutive_ready_count",
            self.consecutive_ready_count,
        )
        _require_nonnegative_int(
            "consecutive_not_ready_count",
            self.consecutive_not_ready_count,
        )
        _require_nonnegative_int("ready_report_count", self.ready_report_count)
        _require_nonnegative_int(
            "not_ready_report_count",
            self.not_ready_report_count,
        )
        if (
            self.latest_phase_2_ready is not None
            and type(self.latest_phase_2_ready) is not bool
        ):
            raise ValueError("latest_phase_2_ready must be a bool or None")
        object.__setattr__(
            self,
            "latest_blocking_reason_names",
            _normalize_reason_names(self.latest_blocking_reason_names),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_readiness_streak_report(
    state_reports: list[PaperPhase2ObservabilityStateReport]
    | tuple[PaperPhase2ObservabilityStateReport, ...],
    *,
    config: PaperPhase2ReadinessStreakConfig,
    generated_at: datetime,
) -> PaperPhase2ReadinessStreakReport:
    if type(config) is not PaperPhase2ReadinessStreakConfig:
        raise ValueError("config must be a PaperPhase2ReadinessStreakConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_state_reports(state_reports)
    latest_report = reports[-1] if reports else None
    ready_report_count = sum(1 for report in reports if report.phase_2_ready)
    not_ready_report_count = len(reports) - ready_report_count

    return PaperPhase2ReadinessStreakReport(
        generated_at=generated_at,
        config_version=config.config_version,
        state_report_count=len(reports),
        latest_phase_2_ready=(
            None if latest_report is None else latest_report.phase_2_ready
        ),
        consecutive_ready_count=_latest_streak_count(reports, True),
        consecutive_not_ready_count=_latest_streak_count(reports, False),
        ready_report_count=ready_report_count,
        not_ready_report_count=not_ready_report_count,
        latest_blocking_reason_names=(
            ()
            if latest_report is None
            else latest_report.blocking_reason_names
        ),
    )


def _normalize_state_reports(
    state_reports: list[PaperPhase2ObservabilityStateReport]
    | tuple[PaperPhase2ObservabilityStateReport, ...],
) -> tuple[PaperPhase2ObservabilityStateReport, ...]:
    if type(state_reports) not in (list, tuple):
        raise ValueError("state_reports must be a list or tuple")
    reports = tuple(state_reports)
    for report in reports:
        if type(report) is not PaperPhase2ObservabilityStateReport:
            raise ValueError(
                "state_reports must contain PaperPhase2ObservabilityStateReport values",
            )
        if report.paper_only is not True:
            raise ValueError("state_reports must contain paper_only reports")
        if report.report_only is not True:
            raise ValueError("state_reports must contain report_only reports")
        if report.readonly is not True:
            raise ValueError("state_reports must contain readonly reports")
    return reports


def _latest_streak_count(
    reports: tuple[PaperPhase2ObservabilityStateReport, ...],
    expected_ready: bool,
) -> int:
    count = 0
    for index in range(len(reports) - 1, -1, -1):
        if reports[index].phase_2_ready != expected_ready:
            break
        count += 1
    return count


def _validate_report_consistency(
    report: PaperPhase2ReadinessStreakReport,
) -> None:
    if (
        report.ready_report_count + report.not_ready_report_count
        != report.state_report_count
    ):
        raise ValueError("state_report_count must match ready and not-ready counts")
    if report.state_report_count == 0:
        if report.latest_phase_2_ready is not None:
            raise ValueError("latest_phase_2_ready must be absent without state reports")
        if report.latest_blocking_reason_names:
            raise ValueError(
                "latest_blocking_reason_names must be absent without state reports",
            )
        if (
            report.consecutive_ready_count != 0
            or report.consecutive_not_ready_count != 0
        ):
            raise ValueError("consecutive streaks must be zero without state reports")
        return

    if report.latest_phase_2_ready is None:
        raise ValueError("latest_phase_2_ready is required with state reports")
    if report.latest_phase_2_ready is True:
        if report.consecutive_ready_count == 0:
            raise ValueError("ready latest report must have a ready streak")
        if report.consecutive_not_ready_count != 0:
            raise ValueError("ready latest report must not have a not-ready streak")
        if report.latest_blocking_reason_names:
            raise ValueError("ready latest report must not have blocking reasons")
    else:
        if report.consecutive_not_ready_count == 0:
            raise ValueError("not-ready latest report must have a not-ready streak")
        if report.consecutive_ready_count != 0:
            raise ValueError("not-ready latest report must not have a ready streak")
        if not report.latest_blocking_reason_names:
            raise ValueError("not-ready latest report must have blocking reasons")
    if report.consecutive_ready_count > report.ready_report_count:
        raise ValueError("consecutive_ready_count must not exceed ready_report_count")
    if report.consecutive_not_ready_count > report.not_ready_report_count:
        raise ValueError(
            "consecutive_not_ready_count must not exceed not_ready_report_count",
        )


def _normalize_reason_names(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("latest_blocking_reason_names must be an iterable")
    try:
        names = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "latest_blocking_reason_names must be an iterable",
        ) from exc
    for name in names:
        if type(name) is not str:
            raise ValueError("latest_blocking_reason_names must contain strings")
    if len(set(names)) != len(names):
        raise ValueError(
            "latest_blocking_reason_names must not contain duplicates",
        )
    for name in names:
        if name not in BLOCKING_REASON_NAMES:
            raise ValueError("latest_blocking_reason_names must contain known names")
    expected_names = tuple(name for name in BLOCKING_REASON_NAMES if name in names)
    if names != expected_names:
        raise ValueError(
            "latest_blocking_reason_names must use deterministic sequence",
        )
    return names


def _as_utc(value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


__all__ = (
    "PaperPhase2ReadinessStreakConfig",
    "PaperPhase2ReadinessStreakReport",
    "build_paper_phase_2_readiness_streak_report",
)

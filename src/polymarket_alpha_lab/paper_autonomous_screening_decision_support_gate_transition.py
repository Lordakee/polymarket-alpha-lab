"""Pure adjacent transition reducer for autonomous screening gate reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    GATE_STATUSES,
    PaperAutonomousScreeningDecisionSupportGateReport,
)


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_CONFIG_VERSION",
    "PaperAutonomousScreeningDecisionSupportGateTransitionReasonChangeRow",
    "PaperAutonomousScreeningDecisionSupportGateTransitionStatusRow",
    "PaperAutonomousScreeningDecisionSupportGateTransitionReport",
    "build_paper_autonomous_screening_decision_support_gate_transition_report",
)


DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_CONFIG_VERSION = (
    "paper-autonomous-screening-decision-support-gate-transition-v0"
)


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateTransitionStatusRow:
    from_gate_status: str
    to_gate_status: str
    transition_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if self.from_gate_status not in GATE_STATUSES:
            raise ValueError("from_gate_status must be a known gate status")
        if self.to_gate_status not in GATE_STATUSES:
            raise ValueError("to_gate_status must be a known gate status")
        if self.transition_count < 0:
            raise ValueError("transition_count must be nonnegative")
        if self.paper_only is not True or self.report_only is not True or self.readonly is not True:
            raise ValueError("row must remain paper-only/report-only/readonly")


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateTransitionReasonChangeRow:
    reason_code: str
    introduced_count: int
    cleared_count: int
    persistent_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.reason_code, str) or not self.reason_code or self.reason_code.strip() != self.reason_code:
            raise ValueError("reason_code must be a canonical nonblank string")
        if self.introduced_count < 0 or self.cleared_count < 0 or self.persistent_count < 0:
            raise ValueError("reason change counts must be nonnegative")
        if self.paper_only is not True or self.report_only is not True or self.readonly is not True:
            raise ValueError("row must remain paper-only/report-only/readonly")


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateTransitionReport:
    generated_at: datetime
    config_version: str
    gate_report_count: int
    transition_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_from_gate_status: str | None
    latest_to_gate_status: str | None
    latest_introduced_reason_codes: tuple[str, ...]
    latest_cleared_reason_codes: tuple[str, ...]
    latest_persistent_reason_codes: tuple[str, ...]
    status_transition_rows: tuple[PaperAutonomousScreeningDecisionSupportGateTransitionStatusRow, ...] | None
    reason_change_rows: tuple[PaperAutonomousScreeningDecisionSupportGateTransitionReasonChangeRow, ...] | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(self, "first_report_generated_at", _as_optional_utc(self.first_report_generated_at))
        object.__setattr__(self, "latest_report_generated_at", _as_optional_utc(self.latest_report_generated_at))
        if not isinstance(self.config_version, str) or not self.config_version or self.config_version.strip() != self.config_version:
            raise ValueError("config_version must be a canonical nonblank string")
        if self.gate_report_count < 0:
            raise ValueError("gate_report_count must be nonnegative")
        if self.transition_count < 0:
            raise ValueError("transition_count must be nonnegative")
        if self.gate_report_count == 0 and self.transition_count != 0:
            raise ValueError("transition_count must be zero when there are no reports")
        if self.latest_from_gate_status is not None and self.latest_from_gate_status not in GATE_STATUSES:
            raise ValueError("latest_from_gate_status must be a known gate status")
        if self.latest_to_gate_status is not None and self.latest_to_gate_status not in GATE_STATUSES:
            raise ValueError("latest_to_gate_status must be a known gate status")
        object.__setattr__(self, "latest_introduced_reason_codes", _normalize_reason_sequence(self.latest_introduced_reason_codes))
        object.__setattr__(self, "latest_cleared_reason_codes", _normalize_reason_sequence(self.latest_cleared_reason_codes))
        object.__setattr__(self, "latest_persistent_reason_codes", _normalize_reason_sequence(self.latest_persistent_reason_codes))
        if self.gate_report_count == 0 and self.transition_count == 0:
            if self.status_transition_rows is not None:
                raise ValueError("status_transition_rows must be None for empty transition report")
            if self.reason_change_rows is not None:
                raise ValueError("reason_change_rows must be None for empty transition report")
        else:
            object.__setattr__(self, "status_transition_rows", _normalize_status_rows(self.status_transition_rows))
            object.__setattr__(self, "reason_change_rows", _normalize_reason_change_rows(self.reason_change_rows))
        if self.paper_only is not True or self.report_only is not True or self.readonly is not True:
            raise ValueError("report must remain paper-only/report-only/readonly")


def build_paper_autonomous_screening_decision_support_gate_transition_report(
    gate_reports: list[PaperAutonomousScreeningDecisionSupportGateReport]
    | tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...],
    *,
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_CONFIG_VERSION,
    generated_at: datetime,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionReport:
    if not isinstance(config_version, str) or not config_version or config_version.strip() != config_version:
        raise ValueError("config_version must be a canonical nonblank string")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    normalized_reports = _normalize_gate_reports(gate_reports)
    pairs = tuple(zip(normalized_reports, normalized_reports[1:], strict=False))
    latest_pair = pairs[-1] if pairs else None
    latest_introduced, latest_cleared, latest_persistent = _pair_reason_change(latest_pair) if latest_pair is not None else ((), (), ())
    return PaperAutonomousScreeningDecisionSupportGateTransitionReport(
        generated_at=generated_at,
        config_version=config_version,
        gate_report_count=len(normalized_reports),
        transition_count=len(pairs),
        first_report_generated_at=normalized_reports[0].generated_at if normalized_reports else None,
        latest_report_generated_at=normalized_reports[-1].generated_at if normalized_reports else None,
        latest_from_gate_status=latest_pair[0].gate_status if latest_pair is not None else None,
        latest_to_gate_status=latest_pair[1].gate_status if latest_pair is not None else None,
        latest_introduced_reason_codes=latest_introduced,
        latest_cleared_reason_codes=latest_cleared,
        latest_persistent_reason_codes=latest_persistent,
        status_transition_rows=None if not pairs else _build_status_transition_rows(pairs),
        reason_change_rows=None if not pairs else _build_reason_change_rows(pairs),
    )


def _normalize_gate_reports(
    gate_reports: list[PaperAutonomousScreeningDecisionSupportGateReport]
    | tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...],
) -> tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...]:
    if type(gate_reports) not in (list, tuple):
        raise ValueError("gate_reports must be a list or tuple")
    normalized = tuple(gate_reports)
    for report in normalized:
        if type(report) is not PaperAutonomousScreeningDecisionSupportGateReport:
            raise ValueError("gate_reports must contain exact PaperAutonomousScreeningDecisionSupportGateReport values")
        if report.paper_only is not True or report.report_only is not True or report.readonly is not True:
            raise ValueError("gate_reports must contain paper-only/report-only/readonly reports")
    return normalized


def _pair_reason_change(
    pair: tuple[PaperAutonomousScreeningDecisionSupportGateReport, PaperAutonomousScreeningDecisionSupportGateReport],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    previous_codes = set(pair[0].reason_codes)
    next_codes = set(pair[1].reason_codes)
    introduced = tuple(sorted(next_codes - previous_codes))
    cleared = tuple(sorted(previous_codes - next_codes))
    persistent = tuple(sorted(previous_codes & next_codes))
    return introduced, cleared, persistent


def _build_status_transition_rows(
    pairs: tuple[
        tuple[PaperAutonomousScreeningDecisionSupportGateReport, PaperAutonomousScreeningDecisionSupportGateReport],
        ...,
    ],
) -> tuple[PaperAutonomousScreeningDecisionSupportGateTransitionStatusRow, ...]:
    counts = {(from_status, to_status): 0 for from_status in GATE_STATUSES for to_status in GATE_STATUSES}
    for previous_report, next_report in pairs:
        counts[(previous_report.gate_status, next_report.gate_status)] += 1
    return tuple(
        PaperAutonomousScreeningDecisionSupportGateTransitionStatusRow(
            from_gate_status=from_status,
            to_gate_status=to_status,
            transition_count=counts[(from_status, to_status)],
        )
        for from_status in GATE_STATUSES
        for to_status in GATE_STATUSES
    )


def _build_reason_change_rows(
    pairs: tuple[
        tuple[PaperAutonomousScreeningDecisionSupportGateReport, PaperAutonomousScreeningDecisionSupportGateReport],
        ...,
    ],
) -> tuple[PaperAutonomousScreeningDecisionSupportGateTransitionReasonChangeRow, ...]:
    counts: dict[str, dict[str, int]] = {}
    for previous_report, next_report in pairs:
        previous_codes = set(previous_report.reason_codes)
        next_codes = set(next_report.reason_codes)
        introduced = next_codes - previous_codes
        cleared = previous_codes - next_codes
        persistent = previous_codes & next_codes
        for reason_code in introduced:
            counts.setdefault(reason_code, {"introduced_count": 0, "cleared_count": 0, "persistent_count": 0})
            counts[reason_code]["introduced_count"] += 1
        for reason_code in cleared:
            counts.setdefault(reason_code, {"introduced_count": 0, "cleared_count": 0, "persistent_count": 0})
            counts[reason_code]["cleared_count"] += 1
        for reason_code in persistent:
            counts.setdefault(reason_code, {"introduced_count": 0, "cleared_count": 0, "persistent_count": 0})
            counts[reason_code]["persistent_count"] += 1
    return tuple(
        PaperAutonomousScreeningDecisionSupportGateTransitionReasonChangeRow(
            reason_code=reason_code,
            introduced_count=counts[reason_code]["introduced_count"],
            cleared_count=counts[reason_code]["cleared_count"],
            persistent_count=counts[reason_code]["persistent_count"],
        )
        for reason_code in sorted(counts)
    )


def _normalize_reason_sequence(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason sequence must be a tuple")
    previous: str | None = None
    for value in values:
        if not isinstance(value, str) or not value or value.strip() != value:
            raise ValueError("reason sequence entries must be canonical nonblank strings")
        if previous is not None and previous >= value:
            raise ValueError("reason sequence must be sorted and unique")
        previous = value
    return values


def _normalize_status_rows(
    rows: object,
) -> tuple[PaperAutonomousScreeningDecisionSupportGateTransitionStatusRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("status_transition_rows must be a tuple")
    for row in rows:
        if type(row) is not PaperAutonomousScreeningDecisionSupportGateTransitionStatusRow:
            raise ValueError("status_transition_rows must contain exact transition status rows")
    return rows


def _normalize_reason_change_rows(
    rows: object,
) -> tuple[PaperAutonomousScreeningDecisionSupportGateTransitionReasonChangeRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_change_rows must be a tuple")
    previous_code: str | None = None
    for row in rows:
        if type(row) is not PaperAutonomousScreeningDecisionSupportGateTransitionReasonChangeRow:
            raise ValueError("reason_change_rows must contain exact reason change rows")
        if previous_code is not None and previous_code >= row.reason_code:
            raise ValueError("reason_change_rows must be sorted by reason_code")
        previous_code = row.reason_code
    return rows


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(value)

"""Read-only probability event manual research checklist coverage report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterable


COUNT_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0.000000")
COVERAGE_STATUSES = ("covered", "missing")
REQUIRED_CHECKLIST_ITEMS = (
    "probability_screen",
    "source_anchor",
    "independent_sources",
    "resolution_rules",
    "team_route",
    "memory_policy",
    "cost_gate",
    "manual_operator_packet",
)
_CHECKLIST_FLAG_FIELDS = {
    "probability_screen": "probability_screen_present",
    "source_anchor": "source_anchor_present",
    "independent_sources": "independent_sources_present",
    "resolution_rules": "resolution_rules_present",
    "team_route": "team_route_present",
    "memory_policy": "memory_policy_present",
    "cost_gate": "cost_gate_present",
    "manual_operator_packet": "manual_operator_packet_present",
}
_REPORT_REASON_CODES = (
    "cost_gate_missing",
    "independent_sources_missing",
    "manual_operator_packet_missing",
    "memory_policy_missing",
    "probability_event_manual_research_checklist_covered",
    "probability_event_manual_research_checklist_missing",
    "probability_event_manual_research_checklist_no_inputs",
    "probability_screen_missing",
    "resolution_rules_missing",
    "source_anchor_missing",
    "team_route_missing",
)


@dataclass(frozen=True)
class ProbabilityEventManualResearchChecklistCoverage:
    checklist_ref: str
    observed_at: datetime
    probability_screen_present: bool
    source_anchor_present: bool
    independent_sources_present: bool
    resolution_rules_present: bool
    team_route_present: bool
    memory_policy_present: bool
    cost_gate_present: bool
    manual_operator_packet_present: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError(
            "ProbabilityEventManualResearchChecklistCoverage does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventManualResearchChecklistCoverage:
            raise ValueError(
                "checklist must be exactly ProbabilityEventManualResearchChecklistCoverage",
            )
        _require_ref("checklist_ref", self.checklist_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in _CHECKLIST_FLAG_FIELDS.values():
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("checklist", self)


@dataclass(frozen=True)
class ProbabilityEventManualResearchChecklistCoverageReport:
    generated_at: datetime
    checklist_count: Decimal
    covered_checklist_count: Decimal
    incomplete_checklist_count: Decimal
    coverage_status: str
    missing_checklist_items: tuple[str, ...]
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError(
            "ProbabilityEventManualResearchChecklistCoverageReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventManualResearchChecklistCoverageReport:
            raise TypeError(
                "report must be exactly "
                "ProbabilityEventManualResearchChecklistCoverageReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "checklist_count",
            "covered_checklist_count",
            "incomplete_checklist_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "coverage_status",
            _normalize_coverage_status(self.coverage_status),
        )
        object.__setattr__(
            self,
            "missing_checklist_items",
            _normalize_missing_items(self.missing_checklist_items),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_probability_event_manual_research_checklist_coverage_report(
    checklist_items: Iterable[ProbabilityEventManualResearchChecklistCoverage],
    *,
    generated_at: datetime,
) -> ProbabilityEventManualResearchChecklistCoverageReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_checklist_items(checklist_items)
    for item in normalized_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    missing_items = _missing_checklist_items(normalized_items)
    checklist_count = _count(len(normalized_items))
    covered_count = _count(
        sum(1 for item in normalized_items if not _missing_checklist_items((item,))),
    )
    incomplete_count = _subtract_count(checklist_count, covered_count)

    return ProbabilityEventManualResearchChecklistCoverageReport(
        generated_at=generated_at_utc,
        checklist_count=checklist_count,
        covered_checklist_count=covered_count,
        incomplete_checklist_count=incomplete_count,
        coverage_status="covered" if normalized_items and not missing_items else "missing",
        missing_checklist_items=missing_items,
        reason_codes=_report_reason_codes(normalized_items, missing_items),
        manual_next_step=_manual_next_step(normalized_items, missing_items),
    )


def probability_event_manual_research_checklist_coverage_report_payload(
    report: ProbabilityEventManualResearchChecklistCoverageReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventManualResearchChecklistCoverageReport:
        raise ValueError(
            "report must be a ProbabilityEventManualResearchChecklistCoverageReport",
        )
    _require_hard_flags("report", report)
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "checklist_count": _decimal_payload(report.checklist_count),
        "covered_checklist_count": _decimal_payload(report.covered_checklist_count),
        "incomplete_checklist_count": _decimal_payload(report.incomplete_checklist_count),
        "coverage_status": report.coverage_status,
        "missing_checklist_items": list(report.missing_checklist_items),
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_checklist_items(
    checklist_items: Iterable[ProbabilityEventManualResearchChecklistCoverage],
) -> tuple[ProbabilityEventManualResearchChecklistCoverage, ...]:
    if isinstance(checklist_items, (str, bytes)):
        raise ValueError("checklist_items must be an iterable of checklist records")
    try:
        values = tuple(checklist_items)
    except TypeError as exc:
        raise ValueError("checklist_items must be an iterable of checklist records") from exc
    for value in values:
        if type(value) is not ProbabilityEventManualResearchChecklistCoverage:
            raise ValueError(
                "checklist_items must contain "
                "ProbabilityEventManualResearchChecklistCoverage records",
            )
        _require_hard_flags("checklist", value)
    return values


def _missing_checklist_items(
    checklist_items: tuple[ProbabilityEventManualResearchChecklistCoverage, ...],
) -> tuple[str, ...]:
    if not checklist_items:
        return REQUIRED_CHECKLIST_ITEMS
    missing: list[str] = []
    for item_name in REQUIRED_CHECKLIST_ITEMS:
        flag_name = _CHECKLIST_FLAG_FIELDS[item_name]
        if any(getattr(item, flag_name) is not True for item in checklist_items):
            missing.append(item_name)
    return tuple(missing)


def _report_reason_codes(
    checklist_items: tuple[ProbabilityEventManualResearchChecklistCoverage, ...],
    missing_items: tuple[str, ...],
) -> tuple[str, ...]:
    if not checklist_items:
        return ("probability_event_manual_research_checklist_no_inputs",)
    if not missing_items:
        return ("probability_event_manual_research_checklist_covered",)
    reason_codes = [f"{item_name}_missing" for item_name in missing_items]
    reason_codes.append("probability_event_manual_research_checklist_missing")
    return tuple(sorted(reason_codes))


def _manual_next_step(
    checklist_items: tuple[ProbabilityEventManualResearchChecklistCoverage, ...],
    missing_items: tuple[str, ...],
) -> str:
    if not checklist_items:
        return "collect_all_manual_research_checklist_items"
    if missing_items:
        return "collect_missing_manual_research_checklist_items_before_any_operator_decision"
    return "manual_research_checklist_complete_continue_readonly_review"


def _validate_report_consistency(
    report: ProbabilityEventManualResearchChecklistCoverageReport,
) -> None:
    if report.checklist_count != (
        report.covered_checklist_count + report.incomplete_checklist_count
    ):
        raise ValueError("checklist counts must reconcile")
    if report.checklist_count == ZERO_COUNT:
        if report.coverage_status != "missing":
            raise ValueError("empty reports must be missing")
        if report.missing_checklist_items != REQUIRED_CHECKLIST_ITEMS:
            raise ValueError("empty reports must require all checklist items")
        if report.reason_codes != ("probability_event_manual_research_checklist_no_inputs",):
            raise ValueError("empty reports must use no-input reason code")
        return
    if report.coverage_status == "covered":
        if report.missing_checklist_items:
            raise ValueError("covered reports must not have missing checklist items")
        if report.reason_codes != ("probability_event_manual_research_checklist_covered",):
            raise ValueError("covered reports must use covered reason code")
    if report.coverage_status == "missing" and not report.missing_checklist_items:
        raise ValueError("missing reports require missing checklist items")


def _normalize_missing_items(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("missing_checklist_items must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("missing_checklist_items must be an iterable") from exc
    unknown = [item for item in items if item not in REQUIRED_CHECKLIST_ITEMS]
    if unknown:
        raise ValueError("missing_checklist_items contains unknown item")
    if tuple(dict.fromkeys(items)) != items:
        raise ValueError("missing_checklist_items must not contain duplicates")
    return items


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    unknown = [
        reason_code
        for reason_code in reason_codes
        if reason_code not in _REPORT_REASON_CODES
    ]
    if unknown:
        raise ValueError("reason_codes contains unknown reason code")
    if tuple(sorted(dict.fromkeys(reason_codes))) != reason_codes:
        raise ValueError("reason_codes must be sorted and unique")
    return reason_codes


def _normalize_coverage_status(value: object) -> str:
    if type(value) is not str or value not in COVERAGE_STATUSES:
        raise ValueError("coverage_status must be covered or missing")
    return value


def _require_manual_next_step(value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError("manual_next_step must be a non-empty string")


def _require_ref(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be non-negative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _subtract_count(left: Decimal, right: Decimal) -> Decimal:
    return (left - right).quantize(COUNT_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(value.quantize(COUNT_QUANTUM), "f")


def _datetime_payload(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


__all__ = (
    "COVERAGE_STATUSES",
    "REQUIRED_CHECKLIST_ITEMS",
    "ProbabilityEventManualResearchChecklistCoverage",
    "ProbabilityEventManualResearchChecklistCoverageReport",
    "build_probability_event_manual_research_checklist_coverage_report",
    "probability_event_manual_research_checklist_coverage_report_payload",
)

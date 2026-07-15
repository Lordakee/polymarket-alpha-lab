"""Read-only probability event operator decision evidence completeness report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterable


COUNT_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0.000000")
COMPLETENESS_STATUSES = ("complete", "incomplete")
REQUIRED_EVIDENCE_SECTIONS = (
    "probability_screen",
    "team_route",
    "source_quality",
    "memory_policy",
    "cost_gate",
    "operator_packet",
    "manual_attestation",
)
_SECTION_FLAG_FIELDS = {
    "probability_screen": "probability_screen_present",
    "team_route": "team_route_present",
    "source_quality": "source_quality_present",
    "memory_policy": "memory_policy_present",
    "cost_gate": "cost_gate_present",
    "operator_packet": "operator_packet_present",
    "manual_attestation": "manual_attestation_present",
}
_REPORT_REASON_CODES = (
    "cost_gate_missing",
    "manual_attestation_missing",
    "memory_policy_missing",
    "operator_packet_missing",
    "probability_event_operator_decision_evidence_complete",
    "probability_event_operator_decision_evidence_incomplete",
    "probability_event_operator_decision_evidence_no_inputs",
    "probability_screen_missing",
    "source_quality_missing",
    "team_route_missing",
)


@dataclass(frozen=True)
class ProbabilityEventOperatorDecisionEvidence:
    evidence_ref: str
    observed_at: datetime
    probability_screen_present: bool
    team_route_present: bool
    source_quality_present: bool
    memory_policy_present: bool
    cost_gate_present: bool
    operator_packet_present: bool
    manual_attestation_present: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ProbabilityEventOperatorDecisionEvidence does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventOperatorDecisionEvidence:
            raise ValueError("evidence must be exactly ProbabilityEventOperatorDecisionEvidence")
        _require_ref("evidence_ref", self.evidence_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in _SECTION_FLAG_FIELDS.values():
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ProbabilityEventOperatorDecisionEvidenceCompletenessReport:
    generated_at: datetime
    evidence_count: Decimal
    complete_evidence_count: Decimal
    incomplete_evidence_count: Decimal
    completeness_status: str
    missing_evidence_sections: tuple[str, ...]
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError(
            "ProbabilityEventOperatorDecisionEvidenceCompletenessReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventOperatorDecisionEvidenceCompletenessReport:
            raise TypeError(
                "report must be exactly "
                "ProbabilityEventOperatorDecisionEvidenceCompletenessReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "evidence_count",
            "complete_evidence_count",
            "incomplete_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "completeness_status",
            _normalize_completeness_status(self.completeness_status),
        )
        object.__setattr__(
            self,
            "missing_evidence_sections",
            _normalize_missing_sections(self.missing_evidence_sections),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_probability_event_operator_decision_evidence_completeness_report(
    evidence_items: Iterable[ProbabilityEventOperatorDecisionEvidence],
    *,
    generated_at: datetime,
) -> ProbabilityEventOperatorDecisionEvidenceCompletenessReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_evidence_items(evidence_items)
    for item in normalized_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    missing_sections = _missing_sections(normalized_items)
    evidence_count = _count(len(normalized_items))
    complete_count = _count(
        sum(1 for item in normalized_items if not _missing_sections((item,))),
    )
    incomplete_count = _subtract_count(evidence_count, complete_count)

    return ProbabilityEventOperatorDecisionEvidenceCompletenessReport(
        generated_at=generated_at_utc,
        evidence_count=evidence_count,
        complete_evidence_count=complete_count,
        incomplete_evidence_count=incomplete_count,
        completeness_status="complete" if normalized_items and not missing_sections else "incomplete",
        missing_evidence_sections=missing_sections,
        reason_codes=_report_reason_codes(normalized_items, missing_sections),
        manual_next_step=_manual_next_step(normalized_items, missing_sections),
    )


def probability_event_operator_decision_evidence_completeness_report_payload(
    report: ProbabilityEventOperatorDecisionEvidenceCompletenessReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventOperatorDecisionEvidenceCompletenessReport:
        raise ValueError(
            "report must be a "
            "ProbabilityEventOperatorDecisionEvidenceCompletenessReport",
        )
    _require_hard_flags("report", report)
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "evidence_count": _decimal_payload(report.evidence_count),
        "complete_evidence_count": _decimal_payload(report.complete_evidence_count),
        "incomplete_evidence_count": _decimal_payload(report.incomplete_evidence_count),
        "completeness_status": report.completeness_status,
        "missing_evidence_sections": list(report.missing_evidence_sections),
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_evidence_items(
    evidence_items: Iterable[ProbabilityEventOperatorDecisionEvidence],
) -> tuple[ProbabilityEventOperatorDecisionEvidence, ...]:
    if isinstance(evidence_items, (str, bytes)):
        raise ValueError("evidence_items must be an iterable of evidence records")
    try:
        values = tuple(evidence_items)
    except TypeError as exc:
        raise ValueError("evidence_items must be an iterable of evidence records") from exc
    for value in values:
        if type(value) is not ProbabilityEventOperatorDecisionEvidence:
            raise ValueError(
                "evidence_items must contain "
                "ProbabilityEventOperatorDecisionEvidence records",
            )
        _require_hard_flags("evidence", value)
    return values


def _missing_sections(
    evidence_items: tuple[ProbabilityEventOperatorDecisionEvidence, ...],
) -> tuple[str, ...]:
    if not evidence_items:
        return REQUIRED_EVIDENCE_SECTIONS
    missing: list[str] = []
    for section in REQUIRED_EVIDENCE_SECTIONS:
        flag_name = _SECTION_FLAG_FIELDS[section]
        if any(getattr(item, flag_name) is not True for item in evidence_items):
            missing.append(section)
    return tuple(missing)


def _report_reason_codes(
    evidence_items: tuple[ProbabilityEventOperatorDecisionEvidence, ...],
    missing_sections: tuple[str, ...],
) -> tuple[str, ...]:
    if not evidence_items:
        return ("probability_event_operator_decision_evidence_no_inputs",)
    if not missing_sections:
        return ("probability_event_operator_decision_evidence_complete",)
    reason_codes = [f"{section}_missing" for section in missing_sections]
    reason_codes.append("probability_event_operator_decision_evidence_incomplete")
    return tuple(sorted(reason_codes))


def _manual_next_step(
    evidence_items: tuple[ProbabilityEventOperatorDecisionEvidence, ...],
    missing_sections: tuple[str, ...],
) -> str:
    if not evidence_items:
        return "collect_all_required_evidence_sections"
    if missing_sections:
        return "collect_missing_evidence_sections_before_any_operator_decision"
    return "manual_attestation_complete_continue_readonly_review"


def _validate_report_consistency(
    report: ProbabilityEventOperatorDecisionEvidenceCompletenessReport,
) -> None:
    if report.evidence_count != (
        report.complete_evidence_count + report.incomplete_evidence_count
    ):
        raise ValueError("evidence counts must reconcile")
    if report.evidence_count == ZERO_COUNT:
        if report.completeness_status != "incomplete":
            raise ValueError("empty reports must be incomplete")
        if report.missing_evidence_sections != REQUIRED_EVIDENCE_SECTIONS:
            raise ValueError("empty reports must require all evidence sections")
        if report.reason_codes != ("probability_event_operator_decision_evidence_no_inputs",):
            raise ValueError("empty reports must use no-input reason code")
        return
    if report.completeness_status == "complete":
        if report.missing_evidence_sections:
            raise ValueError("complete reports must not have missing evidence sections")
        if report.reason_codes != ("probability_event_operator_decision_evidence_complete",):
            raise ValueError("complete reports must use complete reason code")
    if report.completeness_status == "incomplete" and not report.missing_evidence_sections:
        raise ValueError("incomplete reports require missing evidence sections")


def _normalize_missing_sections(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("missing_evidence_sections must be an iterable")
    try:
        sections = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("missing_evidence_sections must be an iterable") from exc
    unknown = [section for section in sections if section not in REQUIRED_EVIDENCE_SECTIONS]
    if unknown:
        raise ValueError("missing_evidence_sections contains unknown section")
    if tuple(dict.fromkeys(sections)) != sections:
        raise ValueError("missing_evidence_sections must not contain duplicates")
    return sections


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


def _normalize_completeness_status(value: object) -> str:
    if type(value) is not str or value not in COMPLETENESS_STATUSES:
        raise ValueError("completeness_status must be complete or incomplete")
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
    "COMPLETENESS_STATUSES",
    "REQUIRED_EVIDENCE_SECTIONS",
    "ProbabilityEventOperatorDecisionEvidence",
    "ProbabilityEventOperatorDecisionEvidenceCompletenessReport",
    "build_probability_event_operator_decision_evidence_completeness_report",
    "probability_event_operator_decision_evidence_completeness_report_payload",
)

"""Read-only probability event manual blocker resolution checklist report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


RESOLUTION_CHECKLIST_STATUSES = ("resolved", "blocked")
REQUIRED_RESOLUTION_ITEMS = (
    "owner_assigned",
    "resolution_note",
    "source_refresh",
    "cost_recheck",
    "memory_policy_recheck",
)
_BOOLEAN_FIELDS = (
    "owner_assigned",
    "resolution_note_present",
    "source_refreshed",
    "cost_rechecked",
    "memory_policy_rechecked",
)
_FIELD_TO_MISSING_ITEM = {
    "owner_assigned": "owner_assigned",
    "resolution_note_present": "resolution_note",
    "source_refreshed": "source_refresh",
    "cost_rechecked": "cost_recheck",
    "memory_policy_rechecked": "memory_policy_recheck",
}


@dataclass(frozen=True)
class ProbabilityEventManualBlockerResolutionChecklistReport:
    blocker_reason_codes: tuple[str, ...]
    resolution_checklist_status: str
    missing_resolution_items: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError(
            "ProbabilityEventManualBlockerResolutionChecklistReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventManualBlockerResolutionChecklistReport:
            raise TypeError(
                "report must be exactly "
                "ProbabilityEventManualBlockerResolutionChecklistReport",
            )
        object.__setattr__(
            self,
            "blocker_reason_codes",
            _normalize_blocker_reason_codes(self.blocker_reason_codes),
        )
        object.__setattr__(
            self,
            "resolution_checklist_status",
            _normalize_status(self.resolution_checklist_status),
        )
        object.__setattr__(
            self,
            "missing_resolution_items",
            _normalize_missing_resolution_items(self.missing_resolution_items),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_probability_event_manual_blocker_resolution_checklist_report(
    *,
    blocker_reason_codes: Iterable[str],
    owner_assigned: bool,
    resolution_note_present: bool,
    source_refreshed: bool,
    cost_rechecked: bool,
    memory_policy_rechecked: bool,
) -> ProbabilityEventManualBlockerResolutionChecklistReport:
    normalized_codes = _normalize_blocker_reason_codes(blocker_reason_codes)
    inputs = {
        "owner_assigned": owner_assigned,
        "resolution_note_present": resolution_note_present,
        "source_refreshed": source_refreshed,
        "cost_rechecked": cost_rechecked,
        "memory_policy_rechecked": memory_policy_rechecked,
    }
    for field_name, value in inputs.items():
        _require_bool(field_name, value)

    missing_items = _missing_resolution_items(normalized_codes, inputs)
    return ProbabilityEventManualBlockerResolutionChecklistReport(
        blocker_reason_codes=normalized_codes,
        resolution_checklist_status="resolved" if not missing_items else "blocked",
        missing_resolution_items=missing_items,
        manual_next_step=_manual_next_step(normalized_codes, missing_items),
    )


def probability_event_manual_blocker_resolution_checklist_report_payload(
    report: ProbabilityEventManualBlockerResolutionChecklistReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventManualBlockerResolutionChecklistReport:
        raise ValueError(
            "report must be a ProbabilityEventManualBlockerResolutionChecklistReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    return {
        "blocker_reason_codes": list(report.blocker_reason_codes),
        "resolution_checklist_status": report.resolution_checklist_status,
        "missing_resolution_items": list(report.missing_resolution_items),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_blocker_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("blocker_reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("blocker_reason_codes must be an iterable") from exc
    for reason_code in normalized:
        if type(reason_code) is not str:
            raise ValueError("blocker_reason_codes must contain text")
        if not reason_code:
            raise ValueError("blocker_reason_codes must not contain blank text")
        if reason_code.strip() != reason_code:
            raise ValueError("blocker_reason_codes must be canonical")
    return normalized


def _normalize_status(status: str) -> str:
    if type(status) is not str or status not in RESOLUTION_CHECKLIST_STATUSES:
        raise ValueError(
            "resolution_checklist_status must be one of "
            f"{RESOLUTION_CHECKLIST_STATUSES}",
        )
    return status


def _normalize_missing_resolution_items(
    missing_resolution_items: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(missing_resolution_items, (str, bytes)):
        raise ValueError("missing_resolution_items must be an iterable")
    try:
        normalized = tuple(missing_resolution_items)
    except TypeError as exc:
        raise ValueError("missing_resolution_items must be an iterable") from exc
    allowed = ("blocker_reason_codes",) + REQUIRED_RESOLUTION_ITEMS
    for item in normalized:
        if type(item) is not str or item not in allowed:
            raise ValueError("missing_resolution_items must contain known items")
    expected = tuple(item for item in allowed if item in set(normalized))
    if normalized != expected:
        raise ValueError("missing_resolution_items must be canonical")
    return normalized


def _missing_resolution_items(
    blocker_reason_codes: tuple[str, ...],
    inputs: dict[str, bool],
) -> tuple[str, ...]:
    if not blocker_reason_codes:
        return ("blocker_reason_codes",)
    return tuple(
        _FIELD_TO_MISSING_ITEM[field_name]
        for field_name in _BOOLEAN_FIELDS
        if inputs[field_name] is not True
    )


def _manual_next_step(
    blocker_reason_codes: tuple[str, ...],
    missing_resolution_items: tuple[str, ...],
) -> str:
    if not blocker_reason_codes:
        return "capture_manual_blocker_reason_codes_before_resolution_review"
    if missing_resolution_items:
        return "assign_owner_and_complete_manual_blocker_resolution_items_before_review"
    return "manual_blocker_resolution_checklist_complete_continue_readonly_review"


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_manual_next_step(manual_next_step: str) -> None:
    allowed_steps = (
        "assign_owner_and_complete_manual_blocker_resolution_items_before_review",
        "capture_manual_blocker_reason_codes_before_resolution_review",
        "manual_blocker_resolution_checklist_complete_continue_readonly_review",
    )
    if type(manual_next_step) is not str or manual_next_step not in allowed_steps:
        raise ValueError("manual_next_step must be a known manual checklist step")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _validate_report_consistency(
    report: ProbabilityEventManualBlockerResolutionChecklistReport,
) -> None:
    expected_missing = (
        ("blocker_reason_codes",)
        if not report.blocker_reason_codes
        else report.missing_resolution_items
    )
    if report.missing_resolution_items != expected_missing:
        raise ValueError("missing_resolution_items must match blocker context")
    expected_status = "resolved" if not report.missing_resolution_items else "blocked"
    if report.resolution_checklist_status != expected_status:
        raise ValueError(
            "resolution_checklist_status must match missing_resolution_items",
        )
    if report.manual_next_step != _manual_next_step(
        report.blocker_reason_codes,
        report.missing_resolution_items,
    ):
        raise ValueError("manual_next_step must match checklist state")

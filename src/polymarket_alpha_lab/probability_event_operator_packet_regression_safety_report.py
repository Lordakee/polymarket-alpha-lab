"""Read-only probability event operator packet regression safety report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PACKET_STATUSES = ("pass", "watch", "blocked")
REGRESSION_STATUSES = ("pass", "flagged")
PACKET_CHECK_FIELDS = ("status", "source_quality", "memory_policy", "cost_gate")
PASS_REASON = "probability_event_operator_packet_regression_safety_pass"
FLAGGED_REASON = "probability_event_operator_packet_regression_safety_flagged"
PASS_MANUAL_NEXT_STEP = "paper_review_continue_operator_packet_review"
GENERAL_FLAGGED_MANUAL_NEXT_STEP = (
    "paper_review_investigate_operator_packet_regression_before_any_pass"
)
REASON_LOSS_MANUAL_NEXT_STEP = "paper_review_restore_lost_operator_packet_reason_codes"


@dataclass(frozen=True)
class ProbabilityEventOperatorPacketSnapshot:
    packet_ref: str
    status: str
    reason_codes: tuple[str, ...]
    source_quality: str
    memory_policy: str
    cost_gate: str
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ProbabilityEventOperatorPacketSnapshot does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventOperatorPacketSnapshot:
            raise ValueError("packet must be exactly ProbabilityEventOperatorPacketSnapshot")
        _require_ref("packet_ref", self.packet_ref)
        for field_name in PACKET_CHECK_FIELDS:
            _require_status(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_hard_flags("packet", self)


@dataclass(frozen=True)
class ProbabilityEventOperatorPacketRegressionSafetyReport:
    regression_status: str
    regression_reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError(
            "ProbabilityEventOperatorPacketRegressionSafetyReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventOperatorPacketRegressionSafetyReport:
            raise ValueError(
                "report must be exactly "
                "ProbabilityEventOperatorPacketRegressionSafetyReport",
            )
        if type(self.regression_status) is not str or (
            self.regression_status not in REGRESSION_STATUSES
        ):
            raise ValueError("regression_status must be pass or flagged")
        object.__setattr__(
            self,
            "regression_reason_codes",
            _normalize_reason_codes(
                "regression_reason_codes",
                self.regression_reason_codes,
            ),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report(self)


def build_probability_event_operator_packet_regression_safety_report(
    *,
    current_packet: ProbabilityEventOperatorPacketSnapshot,
    previous_packet: ProbabilityEventOperatorPacketSnapshot,
) -> ProbabilityEventOperatorPacketRegressionSafetyReport:
    if type(current_packet) is not ProbabilityEventOperatorPacketSnapshot:
        raise ValueError(
            "current_packet must be a ProbabilityEventOperatorPacketSnapshot",
        )
    if type(previous_packet) is not ProbabilityEventOperatorPacketSnapshot:
        raise ValueError(
            "previous_packet must be a ProbabilityEventOperatorPacketSnapshot",
        )
    _require_hard_flags("current_packet", current_packet)
    _require_hard_flags("previous_packet", previous_packet)

    reasons = _regression_reasons(current_packet, previous_packet)
    regression_status = "flagged" if reasons else "pass"
    if regression_status == "pass":
        regression_reason_codes = (PASS_REASON,)
        manual_next_step = PASS_MANUAL_NEXT_STEP
    else:
        regression_reason_codes = (*reasons, FLAGGED_REASON)
        manual_next_step = _flagged_manual_next_step(reasons)

    return ProbabilityEventOperatorPacketRegressionSafetyReport(
        regression_status=regression_status,
        regression_reason_codes=regression_reason_codes,
        manual_next_step=manual_next_step,
    )


def probability_event_operator_packet_regression_safety_report_payload(
    report: ProbabilityEventOperatorPacketRegressionSafetyReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventOperatorPacketRegressionSafetyReport:
        raise ValueError(
            "report must be a ProbabilityEventOperatorPacketRegressionSafetyReport",
        )
    _require_hard_flags("report", report)
    return {
        "regression_status": report.regression_status,
        "regression_reason_codes": list(report.regression_reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _regression_reasons(
    current_packet: ProbabilityEventOperatorPacketSnapshot,
    previous_packet: ProbabilityEventOperatorPacketSnapshot,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for field_name in PACKET_CHECK_FIELDS:
        previous_value = getattr(previous_packet, field_name)
        current_value = getattr(current_packet, field_name)
        if previous_value in ("blocked", "watch") and current_value == "pass":
            reasons.append(f"{field_name}_silent_{previous_value}_to_pass")

    current_reason_codes = set(current_packet.reason_codes)
    lost_reason_codes = tuple(
        sorted(
            reason_code
            for reason_code in previous_packet.reason_codes
            if reason_code not in current_reason_codes
        ),
    )
    for reason_code in lost_reason_codes:
        reasons.append(f"reason_code_lost_{reason_code}")

    if previous_packet.manual_next_step != current_packet.manual_next_step:
        reasons.append("manual_next_step_changed")
    return tuple(dict.fromkeys(reasons))


def _flagged_manual_next_step(reason_codes: tuple[str, ...]) -> str:
    non_status_reasons = tuple(
        reason_code
        for reason_code in reason_codes
        if not reason_code.startswith("reason_code_lost_")
    )
    if not non_status_reasons:
        return REASON_LOSS_MANUAL_NEXT_STEP
    return GENERAL_FLAGGED_MANUAL_NEXT_STEP


def _validate_report(
    report: ProbabilityEventOperatorPacketRegressionSafetyReport,
) -> None:
    if report.regression_status == "pass":
        if report.regression_reason_codes != (PASS_REASON,):
            raise ValueError("pass reports must use pass reason code")
        if report.manual_next_step != PASS_MANUAL_NEXT_STEP:
            raise ValueError("pass reports must use pass manual_next_step")
        return
    if report.regression_reason_codes[-1:] != (FLAGGED_REASON,):
        raise ValueError("flagged reports must include flagged reason code")
    if report.manual_next_step not in (
        GENERAL_FLAGGED_MANUAL_NEXT_STEP,
        REASON_LOSS_MANUAL_NEXT_STEP,
    ):
        raise ValueError("flagged reports must use review manual_next_step")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or not item or item.strip() != item:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if item.lower() != item:
            raise ValueError(f"{field_name} must contain canonical strings")
        normalized.append(item)
    if tuple(dict.fromkeys(normalized)) != tuple(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(normalized)


def _require_ref(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PACKET_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_manual_next_step(value: object) -> None:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or not value.startswith("paper_review_")
    ):
        raise ValueError("manual_next_step must be a paper_review step")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


__all__ = (
    "PACKET_STATUSES",
    "REGRESSION_STATUSES",
    "ProbabilityEventOperatorPacketSnapshot",
    "ProbabilityEventOperatorPacketRegressionSafetyReport",
    "build_probability_event_operator_packet_regression_safety_report",
    "probability_event_operator_packet_regression_safety_report_payload",
)

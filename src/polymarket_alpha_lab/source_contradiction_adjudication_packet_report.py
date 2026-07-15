"""Pure read-only source contradiction adjudication packet report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


__all__ = (
    "SourceContradictionAdjudicationPacketInput",
    "SourceContradictionAdjudicationPacketReport",
    "build_source_contradiction_adjudication_packet_report",
    "source_contradiction_adjudication_packet_report_to_payload",
)


SUPPORTED_POSITIONS = frozenset(
    {
        "supports_yes",
        "supports_no",
        "mixed",
        "unknown",
        "not_applicable",
    },
)
PASS_REASON = "source_contradiction_adjudication_pass"
DETECTED_REASON = "source_contradiction_detected"
UNRESOLVED_REASON = "source_contradiction_unresolved"
DIVERGENT_REASON = "source_positions_diverge"
UNKNOWN_REASON = "source_position_unknown"
NOTE_PRESENT_REASON = "source_contradiction_adjudication_note_present"
NOTE_MISSING_REASON = "source_contradiction_adjudication_note_missing"

PASS_STEP = "proceed_with_documented_source_packet"
WATCH_STEP = "review_documented_adjudication_before_packet_use"
UNRESOLVED_STEP = "resolve_source_contradictions_before_packet_use"
NOTE_STEP = "add_manual_adjudication_note_before_packet_use"
CLARIFY_STEP = "clarify_source_positions_before_packet_use"

REPORT_STATUS_VALUES = frozenset({"pass", "watch", "block"})
REPORT_STEP_BY_STATUS = {
    "pass": PASS_STEP,
    "watch": WATCH_STEP,
}
REASON_CODE_SEQUENCE = (
    PASS_REASON,
    DETECTED_REASON,
    UNRESOLVED_REASON,
    UNKNOWN_REASON,
    DIVERGENT_REASON,
    NOTE_PRESENT_REASON,
    NOTE_MISSING_REASON,
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class SourceContradictionAdjudicationPacketInput(_FinalDataclass):
    contradiction_count: int
    unresolved_contradiction_count: int
    official_source_position: str
    independent_source_positions: tuple[str, ...]
    adjudication_note_present: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SourceContradictionAdjudicationPacketInput,
            "adjudication packet input",
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_count("contradiction_count", self.contradiction_count),
        )
        object.__setattr__(
            self,
            "unresolved_contradiction_count",
            _normalize_count(
                "unresolved_contradiction_count",
                self.unresolved_contradiction_count,
            ),
        )
        if self.unresolved_contradiction_count > self.contradiction_count:
            raise ValueError(
                "unresolved_contradiction_count must not exceed contradiction_count",
            )
        object.__setattr__(
            self,
            "official_source_position",
            _normalize_position("official_source_position", self.official_source_position),
        )
        object.__setattr__(
            self,
            "independent_source_positions",
            _normalize_positions(
                "independent_source_positions",
                self.independent_source_positions,
            ),
        )
        if type(self.adjudication_note_present) is not bool:
            raise ValueError("adjudication_note_present must be a bool")
        _require_hard_flags("adjudication packet input", self)


@dataclass(frozen=True)
class SourceContradictionAdjudicationPacketReport(_FinalDataclass):
    adjudication_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SourceContradictionAdjudicationPacketReport,
            "adjudication packet report",
        )
        if type(self.adjudication_status) is not str:
            raise ValueError("adjudication_status must be a string")
        if self.adjudication_status not in REPORT_STATUS_VALUES:
            raise ValueError("adjudication_status must be pass, watch, or block")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if type(self.manual_next_step) is not str or not self.manual_next_step:
            raise ValueError("manual_next_step must be a non-empty string")
        _validate_report(self)
        _require_hard_flags("adjudication packet report", self)


def build_source_contradiction_adjudication_packet_report(
    packet: SourceContradictionAdjudicationPacketInput,
) -> SourceContradictionAdjudicationPacketReport:
    if type(packet) is not SourceContradictionAdjudicationPacketInput:
        raise ValueError(
            "packet must be a SourceContradictionAdjudicationPacketInput",
        )
    _require_hard_flags("adjudication packet input", packet)

    reason_codes = _reason_codes(packet)
    return SourceContradictionAdjudicationPacketReport(
        adjudication_status=_adjudication_status(reason_codes),
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(reason_codes),
        paper_only=packet.paper_only,
        report_only=packet.report_only,
        readonly=packet.readonly,
    )


def source_contradiction_adjudication_packet_report_to_payload(
    report: SourceContradictionAdjudicationPacketReport,
) -> dict[str, object]:
    if type(report) is not SourceContradictionAdjudicationPacketReport:
        raise ValueError(
            "report must be a SourceContradictionAdjudicationPacketReport",
        )
    _require_hard_flags("adjudication packet report", report)
    _validate_report(report)
    return {
        "adjudication_status": report.adjudication_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _reason_codes(
    packet: SourceContradictionAdjudicationPacketInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    all_positions = (packet.official_source_position,) + packet.independent_source_positions
    if packet.contradiction_count > 0:
        reasons.append(DETECTED_REASON)
    if packet.unresolved_contradiction_count > 0:
        reasons.append(UNRESOLVED_REASON)
    if "unknown" in all_positions:
        reasons.append(UNKNOWN_REASON)
    if len(set(all_positions)) > 1:
        reasons.append(DIVERGENT_REASON)
    if packet.contradiction_count > 0:
        if packet.adjudication_note_present:
            reasons.append(NOTE_PRESENT_REASON)
        else:
            reasons.append(NOTE_MISSING_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reasons))


def _adjudication_status(reason_codes: tuple[str, ...]) -> str:
    if (
        UNRESOLVED_REASON in reason_codes
        or NOTE_MISSING_REASON in reason_codes
        or UNKNOWN_REASON in reason_codes
    ):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if UNRESOLVED_REASON in reason_codes:
        return UNRESOLVED_STEP
    if NOTE_MISSING_REASON in reason_codes:
        return NOTE_STEP
    if UNKNOWN_REASON in reason_codes:
        return CLARIFY_STEP
    if reason_codes == (PASS_REASON,):
        return PASS_STEP
    return WATCH_STEP


def _normalize_count(field_name: str, value: object) -> int:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_position(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    if value not in SUPPORTED_POSITIONS:
        raise ValueError(f"{field_name} must contain a supported source position")
    return value


def _normalize_positions(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(_normalize_position(field_name, item) for item in value)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str or not reason_code:
            raise ValueError("reason_codes must contain non-empty strings")
        if reason_code != reason_code.strip():
            raise ValueError("reason_codes must be stripped")
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain supported reason codes")
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    ordered = tuple(reason for reason in REASON_CODE_SEQUENCE if reason in normalized)
    if tuple(normalized) != ordered:
        raise ValueError("reason_codes must use deterministic ordering")
    return ordered


def _validate_report(report: SourceContradictionAdjudicationPacketReport) -> None:
    expected_status = _adjudication_status(report.reason_codes)
    if report.adjudication_status != expected_status:
        if UNRESOLVED_REASON in report.reason_codes:
            raise ValueError("unresolved contradictions must not pass")
        raise ValueError("adjudication_status must match reason_codes")
    expected_step = _manual_next_step(report.reason_codes)
    if report.manual_next_step != expected_step:
        raise ValueError("manual_next_step must match reason_codes")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: Any) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must keep {field_name}=True")

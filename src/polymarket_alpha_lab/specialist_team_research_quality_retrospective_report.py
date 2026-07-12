import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


READY_REASON = "specialist_team_research_quality_retrospective_ready"
NO_REVIEWED_MARKETS_REASON = (
    "specialist_team_research_quality_retrospective_no_reviewed_markets"
)
MISSED_RESOLUTIONS_REASON = (
    "specialist_team_research_quality_retrospective_missed_resolutions"
)
SOURCE_QUALITY_ISSUES_REASON = (
    "specialist_team_research_quality_retrospective_source_quality_issues"
)
CALIBRATION_ISSUES_REASON = (
    "specialist_team_research_quality_retrospective_calibration_issues"
)
MISSING_RETROSPECTIVE_NOTES_REASON = (
    "specialist_team_research_quality_retrospective_missing_notes"
)

_ZERO = Decimal("0.000000")
_QUANT = Decimal("0.000001")

_REASON_PRIORITY = (
    NO_REVIEWED_MARKETS_REASON,
    MISSED_RESOLUTIONS_REASON,
    SOURCE_QUALITY_ISSUES_REASON,
    CALIBRATION_ISSUES_REASON,
    MISSING_RETROSPECTIVE_NOTES_REASON,
    READY_REASON,
)


@dataclass(frozen=True)
class SpecialistTeamResearchQualityRetrospectiveReport:
    retrospective_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    reviewed_market_count: Decimal
    missed_resolution_count: Decimal
    source_quality_issue_count: Decimal
    calibration_issue_count: Decimal
    retrospective_note_count: Decimal
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "SpecialistTeamResearchQualityRetrospectiveReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamResearchQualityRetrospectiveReport:
            raise ValueError(
                "report must be exactly SpecialistTeamResearchQualityRetrospectiveReport",
            )
        _require_status(self.retrospective_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        for field_name in (
            "reviewed_market_count",
            "missed_resolution_count",
            "source_quality_issue_count",
            "calibration_issue_count",
            "retrospective_note_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)
        expected_status = _status_from_reason_codes(self.reason_codes)
        if self.retrospective_status != expected_status:
            raise ValueError("retrospective_status must match reason_codes")
        expected_step = _manual_next_step(self.reason_codes)
        if self.manual_next_step != expected_step:
            raise ValueError("manual_next_step must match reason_codes")
        if type(self.payload_digest) is not str or not self.payload_digest:
            raise ValueError("payload_digest must be a public string")
        if self.payload_digest != _payload_digest_for_report(self):
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        _require_hard_flags(self)
        payload = _payload_without_digest(self)
        payload["payload_digest"] = self.payload_digest
        return payload


def build_specialist_team_research_quality_retrospective_report(
    *,
    reviewed_market_count: Decimal,
    missed_resolution_count: Decimal,
    source_quality_issue_count: Decimal,
    calibration_issue_count: Decimal,
    retrospective_note_count: Decimal,
) -> SpecialistTeamResearchQualityRetrospectiveReport:
    counts = {
        "reviewed_market_count": _require_nonnegative_whole_decimal(
            "reviewed_market_count",
            reviewed_market_count,
        ),
        "missed_resolution_count": _require_nonnegative_whole_decimal(
            "missed_resolution_count",
            missed_resolution_count,
        ),
        "source_quality_issue_count": _require_nonnegative_whole_decimal(
            "source_quality_issue_count",
            source_quality_issue_count,
        ),
        "calibration_issue_count": _require_nonnegative_whole_decimal(
            "calibration_issue_count",
            calibration_issue_count,
        ),
        "retrospective_note_count": _require_nonnegative_whole_decimal(
            "retrospective_note_count",
            retrospective_note_count,
        ),
    }
    reason_codes = _reason_codes_for_counts(**counts)
    retrospective_status = _status_from_reason_codes(reason_codes)
    manual_next_step = _manual_next_step(reason_codes)
    payload_digest = _digest_payload(
        _payload_for_values(
            retrospective_status=retrospective_status,
            reason_codes=reason_codes,
            manual_next_step=manual_next_step,
            reviewed_market_count=counts["reviewed_market_count"],
            missed_resolution_count=counts["missed_resolution_count"],
            source_quality_issue_count=counts["source_quality_issue_count"],
            calibration_issue_count=counts["calibration_issue_count"],
            retrospective_note_count=counts["retrospective_note_count"],
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )
    return SpecialistTeamResearchQualityRetrospectiveReport(
        retrospective_status=retrospective_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        reviewed_market_count=counts["reviewed_market_count"],
        missed_resolution_count=counts["missed_resolution_count"],
        source_quality_issue_count=counts["source_quality_issue_count"],
        calibration_issue_count=counts["calibration_issue_count"],
        retrospective_note_count=counts["retrospective_note_count"],
        payload_digest=payload_digest,
    )


def _reason_codes_for_counts(
    *,
    reviewed_market_count: Decimal,
    missed_resolution_count: Decimal,
    source_quality_issue_count: Decimal,
    calibration_issue_count: Decimal,
    retrospective_note_count: Decimal,
) -> tuple[str, ...]:
    reason_codes = (
        *((NO_REVIEWED_MARKETS_REASON,) if reviewed_market_count == _ZERO else ()),
        *((MISSED_RESOLUTIONS_REASON,) if missed_resolution_count > _ZERO else ()),
        *((SOURCE_QUALITY_ISSUES_REASON,) if source_quality_issue_count > _ZERO else ()),
        *((CALIBRATION_ISSUES_REASON,) if calibration_issue_count > _ZERO else ()),
        *(
            (MISSING_RETROSPECTIVE_NOTES_REASON,)
            if retrospective_note_count == _ZERO
            else ()
        ),
    )
    if not reason_codes:
        reason_codes = (READY_REASON,)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if NO_REVIEWED_MARKETS_REASON in reason_codes:
        return "blocked"
    if MISSING_RETROSPECTIVE_NOTES_REASON in reason_codes:
        return "blocked"
    if reason_codes == (READY_REASON,):
        return "ready"
    return "needs_manual_review"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if NO_REVIEWED_MARKETS_REASON in reason_codes:
        return "Review at least one resolved market before preparing the retrospective."
    if MISSED_RESOLUTIONS_REASON in reason_codes:
        return "Manually reconcile missed resolutions before marking the retrospective ready."
    if SOURCE_QUALITY_ISSUES_REASON in reason_codes:
        return "Manually verify source quality issues before marking the retrospective ready."
    if CALIBRATION_ISSUES_REASON in reason_codes:
        return "Manually review calibration issues before marking the retrospective ready."
    if MISSING_RETROSPECTIVE_NOTES_REASON in reason_codes:
        return "Add retrospective notes before marking the research quality packet ready."
    return (
        "Continue the paper-only research quality retrospective with the prepared "
        "evidence packet."
    )


def _payload_digest_for_report(
    report: SpecialistTeamResearchQualityRetrospectiveReport,
) -> str:
    return _digest_payload(_payload_without_digest(report))


def _payload_without_digest(
    report: SpecialistTeamResearchQualityRetrospectiveReport,
) -> dict[str, Any]:
    return _payload_for_values(
        retrospective_status=report.retrospective_status,
        reason_codes=report.reason_codes,
        manual_next_step=report.manual_next_step,
        reviewed_market_count=report.reviewed_market_count,
        missed_resolution_count=report.missed_resolution_count,
        source_quality_issue_count=report.source_quality_issue_count,
        calibration_issue_count=report.calibration_issue_count,
        retrospective_note_count=report.retrospective_note_count,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _payload_for_values(
    *,
    retrospective_status: str,
    reason_codes: tuple[str, ...],
    manual_next_step: str,
    reviewed_market_count: Decimal,
    missed_resolution_count: Decimal,
    source_quality_issue_count: Decimal,
    calibration_issue_count: Decimal,
    retrospective_note_count: Decimal,
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, Any]:
    return {
        "retrospective_status": retrospective_status,
        "reason_codes": list(reason_codes),
        "manual_next_step": manual_next_step,
        "reviewed_market_count": _decimal_string(reviewed_market_count),
        "missed_resolution_count": _decimal_string(missed_resolution_count),
        "source_quality_issue_count": _decimal_string(source_quality_issue_count),
        "calibration_issue_count": _decimal_string(calibration_issue_count),
        "retrospective_note_count": _decimal_string(retrospective_note_count),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be a Decimal")
    normalized = value.quantize(_QUANT)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value().quantize(_QUANT):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise TypeError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in _REASON_PRIORITY:
            raise ValueError("reason_codes must contain supported public reason codes")
        seen.add(reason_code)
    normalized = tuple(reason for reason in _REASON_PRIORITY if reason in seen)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    if READY_REASON in normalized and normalized != (READY_REASON,):
        raise ValueError("ready reason must not be combined with blockers")
    return normalized


def _require_status(value: str) -> None:
    if type(value) is not str or value not in {"ready", "needs_manual_review", "blocked"}:
        raise ValueError("retrospective_status must be supported")


def _require_manual_next_step(value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError("manual_next_step must be a public string")


def _require_hard_flags(
    report: SpecialistTeamResearchQualityRetrospectiveReport,
) -> None:
    if report.paper_only is not True:
        raise ValueError("paper_only must be True")
    if report.report_only is not True:
        raise ValueError("report_only must be True")
    if report.readonly is not True:
        raise ValueError("readonly must be True")


def _decimal_string(value: Decimal) -> str:
    return f"{value.quantize(_QUANT):f}"

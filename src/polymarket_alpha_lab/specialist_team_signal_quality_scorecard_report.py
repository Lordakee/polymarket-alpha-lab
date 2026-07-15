from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_SPECIALIST_TEAM_SIGNAL_QUALITY_SCORECARD_REPORT_CONFIG_VERSION = (
    "specialist-team-signal-quality-scorecard-report-v0"
)

_SIX = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_DIGEST_FIELD = "payload_digest"
_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_TEAM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

_QUALITY_BANDS = frozenset(
    (
        "strong_signal_quality",
        "manual_review_signal_quality",
        "insufficient_signal_quality",
    ),
)
_MANUAL_NEXT_STEPS = frozenset(
    (
        "continue_readonly_paper_review",
        "manually_review_team_signal_inputs",
        "manually_rebuild_team_signal_evidence",
    ),
)
_REASON_CODES = frozenset(
    (
        "source_quorum_low",
        "source_quorum_watch",
        "forecast_track_record_low",
        "forecast_track_record_watch",
        "calibration_low",
        "calibration_watch",
        "recency_low",
        "recency_watch",
        "contradiction_penalty_high",
        "contradiction_penalty_watch",
        "weighted_score_low",
        "weighted_score_watch",
        "signal_quality_strong",
    ),
)


@dataclass(frozen=True)
class SpecialistTeamSignalQualityScorecardInput:
    team: str
    source_quorum_score: Decimal
    forecast_track_record_score: Decimal
    calibration_score: Decimal
    recency_score: Decimal
    contradiction_penalty: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact("input", self, SpecialistTeamSignalQualityScorecardInput)
        object.__setattr__(self, "team", _require_team(self.team))
        for name in (
            "source_quorum_score",
            "forecast_track_record_score",
            "calibration_score",
            "recency_score",
            "contradiction_penalty",
        ):
            object.__setattr__(self, name, _require_unit_decimal(name, getattr(self, name)))
        _require_flags(self)


@dataclass(frozen=True)
class SpecialistTeamSignalQualityScorecardReport:
    config_version: str
    team: str
    source_quorum_score: Decimal
    forecast_track_record_score: Decimal
    calibration_score: Decimal
    recency_score: Decimal
    contradiction_penalty: Decimal
    weighted_score: Decimal
    quality_band: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact("report", self, SpecialistTeamSignalQualityScorecardReport)
        if self.config_version != DEFAULT_SPECIALIST_TEAM_SIGNAL_QUALITY_SCORECARD_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(self, "team", _require_team(self.team))
        for name in (
            "source_quorum_score",
            "forecast_track_record_score",
            "calibration_score",
            "recency_score",
            "contradiction_penalty",
            "weighted_score",
        ):
            object.__setattr__(self, name, _require_unit_decimal(name, getattr(self, name)))
        if self.quality_band not in _QUALITY_BANDS:
            raise ValueError("quality_band must be supported")
        if self.manual_next_step not in _MANUAL_NEXT_STEPS:
            raise ValueError("manual_next_step must be supported")
        object.__setattr__(self, "reason_codes", _require_reason_codes(self.reason_codes))
        _require_flags(self)
        _validate_report(self)
        if self.payload_digest:
            if not _HEX_RE.fullmatch(self.payload_digest):
                raise ValueError("payload_digest must be sha256 hex")
            if self.payload_digest != _digest(_public_payload(self, include_digest=False)):
                raise ValueError("payload_digest must match public payload")
        else:
            object.__setattr__(
                self,
                "payload_digest",
                _digest(_public_payload(self, include_digest=False)),
            )

    @property
    def public_payload(self) -> dict[str, Any]:
        payload = _public_payload(self, include_digest=True)
        if not validate_specialist_team_signal_quality_scorecard_public_payload(payload):
            raise ValueError("public_payload must validate")
        return payload


def build_specialist_team_signal_quality_scorecard_report(
    scorecard_input: SpecialistTeamSignalQualityScorecardInput,
) -> SpecialistTeamSignalQualityScorecardReport:
    _require_exact("input", scorecard_input, SpecialistTeamSignalQualityScorecardInput)
    _require_flags(scorecard_input)
    weighted_score = _score(scorecard_input)
    quality_band, manual_next_step, reason_codes = _decision(scorecard_input, weighted_score)
    return SpecialistTeamSignalQualityScorecardReport(
        config_version=DEFAULT_SPECIALIST_TEAM_SIGNAL_QUALITY_SCORECARD_REPORT_CONFIG_VERSION,
        team=scorecard_input.team,
        source_quorum_score=scorecard_input.source_quorum_score,
        forecast_track_record_score=scorecard_input.forecast_track_record_score,
        calibration_score=scorecard_input.calibration_score,
        recency_score=scorecard_input.recency_score,
        contradiction_penalty=scorecard_input.contradiction_penalty,
        weighted_score=weighted_score,
        quality_band=quality_band,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
    )


def validate_specialist_team_signal_quality_scorecard_public_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        return False
    required_names = {
        "config_version",
        "team",
        "source_quorum_score",
        "forecast_track_record_score",
        "calibration_score",
        "recency_score",
        "contradiction_penalty",
        "weighted_score",
        "quality_band",
        "reason_codes",
        "manual_next_step",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(payload) != required_names:
        return False
    if payload.get("config_version") != DEFAULT_SPECIALIST_TEAM_SIGNAL_QUALITY_SCORECARD_REPORT_CONFIG_VERSION:
        return False
    if not _safe_public_team(payload.get("team")):
        return False
    for name in (
        "source_quorum_score",
        "forecast_track_record_score",
        "calibration_score",
        "recency_score",
        "contradiction_penalty",
        "weighted_score",
    ):
        if type(payload.get(name)) is not str:
            return False
        try:
            if _require_unit_decimal(name, Decimal(payload[name])) != Decimal(payload[name]):
                return False
        except (InvalidOperation, ValueError):
            return False
        if payload[name] != str(Decimal(payload[name]).quantize(_SIX)):
            return False
    if payload.get("quality_band") not in _QUALITY_BANDS:
        return False
    if payload.get("manual_next_step") not in _MANUAL_NEXT_STEPS:
        return False
    if type(payload.get("reason_codes")) is not list:
        return False
    if not payload["reason_codes"]:
        return False
    if len(set(payload["reason_codes"])) != len(payload["reason_codes"]):
        return False
    for reason_code in payload["reason_codes"]:
        if type(reason_code) is not str or reason_code not in _REASON_CODES:
            return False
    if (
        payload.get("paper_only") is not True
        or payload.get("report_only") is not True
        or payload.get("readonly") is not True
    ):
        return False
    value = payload.get(_DIGEST_FIELD)
    if type(value) is not str or not _HEX_RE.fullmatch(value):
        return False
    unsigned = dict(payload)
    unsigned.pop(_DIGEST_FIELD, None)
    return value == _digest(unsigned)


def _score(scorecard_input: SpecialistTeamSignalQualityScorecardInput) -> Decimal:
    return _six(
        scorecard_input.source_quorum_score * Decimal("0.250000")
        + scorecard_input.forecast_track_record_score * Decimal("0.250000")
        + scorecard_input.calibration_score * Decimal("0.200000")
        + scorecard_input.recency_score * Decimal("0.200000")
        + (_ONE - scorecard_input.contradiction_penalty) * Decimal("0.100000"),
    )


def _decision(
    scorecard_input: SpecialistTeamSignalQualityScorecardInput,
    weighted_score: Decimal,
) -> tuple[str, str, tuple[str, ...]]:
    reasons: list[str] = []
    if scorecard_input.source_quorum_score < Decimal("0.600000"):
        reasons.append("source_quorum_low")
    elif scorecard_input.source_quorum_score < Decimal("0.750000"):
        reasons.append("source_quorum_watch")
    if scorecard_input.forecast_track_record_score < Decimal("0.600000"):
        reasons.append("forecast_track_record_low")
    elif scorecard_input.forecast_track_record_score < Decimal("0.750000"):
        reasons.append("forecast_track_record_watch")
    if scorecard_input.calibration_score < Decimal("0.600000"):
        reasons.append("calibration_low")
    elif scorecard_input.calibration_score < Decimal("0.750000"):
        reasons.append("calibration_watch")
    if scorecard_input.recency_score < Decimal("0.600000"):
        reasons.append("recency_low")
    elif scorecard_input.recency_score < Decimal("0.750000"):
        reasons.append("recency_watch")
    if scorecard_input.contradiction_penalty > Decimal("0.500000"):
        reasons.append("contradiction_penalty_high")
    elif scorecard_input.contradiction_penalty >= Decimal("0.250000"):
        reasons.append("contradiction_penalty_watch")
    if weighted_score < Decimal("0.600000"):
        reasons.append("weighted_score_low")
    elif weighted_score < Decimal("0.750000"):
        reasons.append("weighted_score_watch")

    if any(reason.endswith("_low") or reason.endswith("_high") for reason in reasons):
        return (
            "insufficient_signal_quality",
            "manually_rebuild_team_signal_evidence",
            tuple(reasons),
        )
    if reasons:
        return (
            "manual_review_signal_quality",
            "manually_review_team_signal_inputs",
            tuple(reasons),
        )
    return (
        "strong_signal_quality",
        "continue_readonly_paper_review",
        ("signal_quality_strong",),
    )


def _public_payload(
    report: SpecialistTeamSignalQualityScorecardReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "config_version": report.config_version,
        "team": report.team,
        "source_quorum_score": str(report.source_quorum_score),
        "forecast_track_record_score": str(report.forecast_track_record_score),
        "calibration_score": str(report.calibration_score),
        "recency_score": str(report.recency_score),
        "contradiction_penalty": str(report.contradiction_penalty),
        "weighted_score": str(report.weighted_score),
        "quality_band": report.quality_band,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload[_DIGEST_FIELD] = report.payload_digest
    return payload


def _digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        _canonical(payload),
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical(value: object) -> object:
    if type(value) is dict:
        return {name: _canonical(value[name]) for name in sorted(value)}
    if type(value) is list:
        return [_canonical(item) for item in value]
    return value


def _validate_report(report: SpecialistTeamSignalQualityScorecardReport) -> None:
    expected_score = _score(
        SpecialistTeamSignalQualityScorecardInput(
            team=report.team,
            source_quorum_score=report.source_quorum_score,
            forecast_track_record_score=report.forecast_track_record_score,
            calibration_score=report.calibration_score,
            recency_score=report.recency_score,
            contradiction_penalty=report.contradiction_penalty,
        ),
    )
    if report.weighted_score != expected_score:
        raise ValueError("weighted_score must match input scores")
    expected_band, expected_step, expected_reasons = _decision(report, report.weighted_score)
    if report.quality_band != expected_band:
        raise ValueError("quality_band must match scorecard")
    if report.manual_next_step != expected_step:
        raise ValueError("manual_next_step must match scorecard")
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match scorecard")


def _require_unit_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be Decimal")
    with localcontext(_CONTEXT):
        result = value.quantize(_SIX)
    if value != result:
        raise ValueError(f"{name} must use six decimal places")
    if result < _ZERO or result > _ONE:
        raise ValueError(f"{name} must be a unit score")
    return result


def _six(value: Decimal) -> Decimal:
    with localcontext(_CONTEXT):
        return value.quantize(_SIX)


def _require_team(value: object) -> str:
    if type(value) is not str or not _TEAM_RE.fullmatch(value):
        raise ValueError("team must be a public identifier")
    return value


def _safe_public_team(value: object) -> bool:
    return type(value) is str and _TEAM_RE.fullmatch(value) is not None


def _require_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in _REASON_CODES:
            raise ValueError("reason_codes must be supported")
    return value


def _require_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _require_exact(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exact type")

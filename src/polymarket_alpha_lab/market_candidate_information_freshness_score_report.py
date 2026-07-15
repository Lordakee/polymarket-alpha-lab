"""Readonly market candidate information freshness score report reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
OFFICIAL_WATCH_HOURS = Decimal("6.000000")
OFFICIAL_BLOCK_HOURS = Decimal("10.000000")
INDEPENDENT_WATCH_HOURS = Decimal("8.000000")
INDEPENDENT_BLOCK_HOURS = Decimal("12.000000")
FORECAST_WATCH_HOURS = Decimal("4.000000")
FORECAST_BLOCK_HOURS = Decimal("8.000000")
MOVE_WATCH_PROBABILITY = Decimal("0.500000")
MOVE_BLOCK_PROBABILITY = Decimal("0.650000")
PENALTY_WATCH_PROBABILITY = Decimal("0.200000")
PENALTY_BLOCK_PROBABILITY = Decimal("0.250000")
WATCH_SCORE_FLOOR = Decimal("0.500000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

PASS_REASON = "candidate_information_fresh_enough"
OFFICIAL_AGE_HIGH_REASON = "official_source_age_high"
INDEPENDENT_AGE_HIGH_REASON = "independent_source_age_high"
FORECAST_AGE_HIGH_REASON = "forecast_age_high"
MOVE_PROBABILITY_HIGH_REASON = "market_price_move_probability_high"
PENALTY_PROBABILITY_HIGH_REASON = "freshness_penalty_probability_high"
REASON_CODES = (
    OFFICIAL_AGE_HIGH_REASON,
    INDEPENDENT_AGE_HIGH_REASON,
    FORECAST_AGE_HIGH_REASON,
    MOVE_PROBABILITY_HIGH_REASON,
    PENALTY_PROBABILITY_HIGH_REASON,
    PASS_REASON,
)

STEP_CONTINUE = "continue_manual_candidate_review"
STEP_REFRESH = "manually_refresh_candidate_information"
STEP_PAUSE_REFRESH = "pause_candidate_review_until_public_information_refresh"
MANUAL_STEPS = (STEP_CONTINUE, STEP_REFRESH, STEP_PAUSE_REFRESH)

__all__ = (
    "MarketCandidateInformationFreshnessScoreReport",
    "build_market_candidate_information_freshness_score_report",
    "market_candidate_information_freshness_score_report_digest",
    "market_candidate_information_freshness_score_report_to_public_payload",
    "validate_market_candidate_information_freshness_score_report_payload",
)


@dataclass(frozen=True)
class MarketCandidateInformationFreshnessScoreReport:
    official_source_age_hours: Decimal
    independent_source_age_hours: Decimal
    forecast_age_hours: Decimal
    market_price_move_probability: Decimal
    freshness_penalty_probability: Decimal
    freshness_status: str
    freshness_score_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketCandidateInformationFreshnessScoreReport:
            raise TypeError(
                "MarketCandidateInformationFreshnessScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketCandidateInformationFreshnessScoreReport,
            "report",
        )
        for name in (
            "official_source_age_hours",
            "independent_source_age_hours",
            "forecast_age_hours",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "market_price_move_probability",
            "freshness_penalty_probability",
            "freshness_score_probability",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        _require_status("freshness_status", self.freshness_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.payload_digest == "":
            object.__setattr__(
                self,
                "payload_digest",
                _payload_digest(_payload_value(self, include_digest=False)),
            )
        else:
            _require_sha256("payload_digest", self.payload_digest)
            _require_matching_digest(_payload_value(self, include_digest=True))

    @property
    def public_payload(self) -> dict[str, Any]:
        return market_candidate_information_freshness_score_report_to_public_payload(
            self,
        )


def build_market_candidate_information_freshness_score_report(
    *,
    official_source_age_hours: Decimal,
    independent_source_age_hours: Decimal,
    forecast_age_hours: Decimal,
    market_price_move_probability: Decimal,
    freshness_penalty_probability: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketCandidateInformationFreshnessScoreReport:
    values = {
        "official_source_age_hours": _require_nonnegative_decimal(
            "official_source_age_hours",
            official_source_age_hours,
        ),
        "independent_source_age_hours": _require_nonnegative_decimal(
            "independent_source_age_hours",
            independent_source_age_hours,
        ),
        "forecast_age_hours": _require_nonnegative_decimal(
            "forecast_age_hours",
            forecast_age_hours,
        ),
        "market_price_move_probability": _require_ratio_decimal(
            "market_price_move_probability",
            market_price_move_probability,
        ),
        "freshness_penalty_probability": _require_ratio_decimal(
            "freshness_penalty_probability",
            freshness_penalty_probability,
        ),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    _require_hard_flags("input", _FlagView(paper_only, report_only, readonly))
    reasons = _reason_codes(
        official_source_age_hours=values["official_source_age_hours"],
        independent_source_age_hours=values["independent_source_age_hours"],
        forecast_age_hours=values["forecast_age_hours"],
        market_price_move_probability=values["market_price_move_probability"],
        freshness_penalty_probability=values["freshness_penalty_probability"],
    )
    status = _freshness_status(reasons)
    report_values = {
        **values,
        "freshness_status": status,
        "freshness_score_probability": _freshness_score_probability(
            market_price_move_probability=values["market_price_move_probability"],
            freshness_penalty_probability=values["freshness_penalty_probability"],
        ),
        "reason_codes": reasons,
        "manual_next_step": _manual_next_step(status),
        "payload_digest": "",
    }
    return MarketCandidateInformationFreshnessScoreReport(**report_values)


def market_candidate_information_freshness_score_report_digest(
    report: MarketCandidateInformationFreshnessScoreReport,
) -> str:
    _require_exact_type(
        report,
        MarketCandidateInformationFreshnessScoreReport,
        "report",
    )
    _require_hard_flags("report", report)
    payload = _payload_value(report, include_digest=True)
    _require_matching_digest(payload)
    return report.payload_digest


def market_candidate_information_freshness_score_report_to_public_payload(
    report: MarketCandidateInformationFreshnessScoreReport,
) -> dict[str, Any]:
    _require_exact_type(
        report,
        MarketCandidateInformationFreshnessScoreReport,
        "report",
    )
    _require_hard_flags("report", report)
    payload = _payload_value(report, include_digest=True)
    _require_matching_digest(payload)
    return payload


def validate_market_candidate_information_freshness_score_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_payload_numeric_objects(payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    _require_payload_report_shape(payload)
    return True


@dataclass(frozen=True)
class _FlagView:
    paper_only: bool
    report_only: bool
    readonly: bool


def _reason_codes(
    *,
    official_source_age_hours: Decimal,
    independent_source_age_hours: Decimal,
    forecast_age_hours: Decimal,
    market_price_move_probability: Decimal,
    freshness_penalty_probability: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if official_source_age_hours >= OFFICIAL_WATCH_HOURS:
        reasons.append(OFFICIAL_AGE_HIGH_REASON)
    if independent_source_age_hours >= INDEPENDENT_BLOCK_HOURS:
        reasons.append(INDEPENDENT_AGE_HIGH_REASON)
    if forecast_age_hours >= FORECAST_WATCH_HOURS:
        reasons.append(FORECAST_AGE_HIGH_REASON)
    if market_price_move_probability >= MOVE_BLOCK_PROBABILITY:
        reasons.append(MOVE_PROBABILITY_HIGH_REASON)
    if freshness_penalty_probability >= PENALTY_WATCH_PROBABILITY:
        reasons.append(PENALTY_PROBABILITY_HIGH_REASON)
    if not reasons:
        return (PASS_REASON,)
    return tuple(reasons)


def _freshness_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    if (
        INDEPENDENT_AGE_HIGH_REASON in reason_codes
        or MOVE_PROBABILITY_HIGH_REASON in reason_codes
        or PENALTY_PROBABILITY_HIGH_REASON in reason_codes
    ):
        return STATUS_BLOCK
    return STATUS_WATCH


def _freshness_score_probability(
    *,
    market_price_move_probability: Decimal,
    freshness_penalty_probability: Decimal,
) -> Decimal:
    return _quantize_ratio(
        ONE - market_price_move_probability - freshness_penalty_probability,
    )


def _manual_next_step(status: str) -> str:
    if status == STATUS_PASS:
        return STEP_CONTINUE
    if status == STATUS_WATCH:
        return STEP_REFRESH
    if status == STATUS_BLOCK:
        return STEP_PAUSE_REFRESH
    raise ValueError("freshness_status must be supported")


def _validate_report(report: MarketCandidateInformationFreshnessScoreReport) -> None:
    expected_reasons = _reason_codes(
        official_source_age_hours=report.official_source_age_hours,
        independent_source_age_hours=report.independent_source_age_hours,
        forecast_age_hours=report.forecast_age_hours,
        market_price_move_probability=report.market_price_move_probability,
        freshness_penalty_probability=report.freshness_penalty_probability,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes do not match freshness inputs")
    expected_status = _freshness_status(report.reason_codes)
    if report.freshness_status != expected_status:
        raise ValueError("freshness_status does not match reason_codes")
    expected_score = _freshness_score_probability(
        market_price_move_probability=report.market_price_move_probability,
        freshness_penalty_probability=report.freshness_penalty_probability,
    )
    if report.freshness_score_probability != expected_score:
        raise ValueError("freshness_score_probability does not match inputs")
    if report.freshness_status == STATUS_PASS and (
        report.freshness_score_probability < WATCH_SCORE_FLOOR
    ):
        raise ValueError("pass report freshness_score_probability is too low")
    if report.manual_next_step != _manual_next_step(report.freshness_status):
        raise ValueError("manual_next_step does not match freshness_status")


def _payload_value(
    report: MarketCandidateInformationFreshnessScoreReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "official_source_age_hours": _decimal_text(report.official_source_age_hours),
        "independent_source_age_hours": _decimal_text(
            report.independent_source_age_hours,
        ),
        "forecast_age_hours": _decimal_text(report.forecast_age_hours),
        "market_price_move_probability": _decimal_text(
            report.market_price_move_probability,
        ),
        "freshness_penalty_probability": _decimal_text(
            report.freshness_penalty_probability,
        ),
        "freshness_status": report.freshness_status,
        "freshness_score_probability": _decimal_text(
            report.freshness_score_probability,
        ),
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["payload_digest"] = report.payload_digest
    return payload


def _require_payload_report_shape(payload: dict[str, Any]) -> None:
    report = MarketCandidateInformationFreshnessScoreReport(
        official_source_age_hours=_decimal_from_payload(
            "official_source_age_hours",
            payload.get("official_source_age_hours"),
        ),
        independent_source_age_hours=_decimal_from_payload(
            "independent_source_age_hours",
            payload.get("independent_source_age_hours"),
        ),
        forecast_age_hours=_decimal_from_payload(
            "forecast_age_hours",
            payload.get("forecast_age_hours"),
        ),
        market_price_move_probability=_decimal_from_payload(
            "market_price_move_probability",
            payload.get("market_price_move_probability"),
        ),
        freshness_penalty_probability=_decimal_from_payload(
            "freshness_penalty_probability",
            payload.get("freshness_penalty_probability"),
        ),
        freshness_status=_string_from_payload(
            "freshness_status",
            payload.get("freshness_status"),
        ),
        freshness_score_probability=_decimal_from_payload(
            "freshness_score_probability",
            payload.get("freshness_score_probability"),
        ),
        reason_codes=_reason_codes_from_payload(payload.get("reason_codes")),
        manual_next_step=_string_from_payload(
            "manual_next_step",
            payload.get("manual_next_step"),
        ),
        payload_digest=_string_from_payload(
            "payload_digest",
            payload.get("payload_digest"),
        ),
        paper_only=payload.get("paper_only"),
        report_only=payload.get("report_only"),
        readonly=payload.get("readonly"),
    )
    if _payload_value(report, include_digest=True) != payload:
        raise ValueError("public payload does not match canonical report shape")


def _payload_digest(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(_canonical_payload(payload), separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _canonical_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {name: payload[name] for name in sorted(payload)}


def _require_matching_digest(payload: dict[str, Any]) -> None:
    if "payload_digest" not in payload:
        raise ValueError("payload_digest is required")
    expected_payload = dict(payload)
    claimed_digest = expected_payload.pop("payload_digest")
    if type(claimed_digest) is not str:
        raise ValueError("payload_digest must be a string")
    if claimed_digest != _payload_digest(expected_payload):
        raise ValueError("payload_digest does not match public payload")


def _reject_payload_numeric_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_payload_numeric_objects(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_payload_numeric_objects(item)
        return
    if type(value) in (Decimal, float, int):
        raise ValueError("public payload must not contain numeric objects")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if payload.get(name) is not True:
            raise ValueError(f"payload {name} must be True")


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"public payload {field_name} must be a string")
    try:
        return _quantize_ratio(Decimal(value))
    except Exception as exc:
        raise ValueError(f"public payload {field_name} must be a decimal string") from exc


def _string_from_payload(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"public payload {field_name} must be a string")
    return value


def _reason_codes_from_payload(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("public payload reason_codes must be a list")
    codes: list[str] = []
    for item in value:
        if type(item) is not str:
            raise ValueError("public payload reason_codes must contain strings")
        codes.append(item)
    return tuple(codes)


def _require_exact_type(value: object, expected_type: type, field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    result = _require_decimal(field_name, value)
    if result < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return result


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    result = _require_decimal(field_name, value)
    if result < ZERO or result > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return result


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize_ratio(value)


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(SIX)


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be supported")


def _require_manual_step(field_name: str, value: object) -> None:
    if value not in MANUAL_STEPS:
        raise ValueError(f"{field_name} must be supported")


def _require_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    for item in value:
        if item not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unsupported reason code")
    if PASS_REASON in value and value != (PASS_REASON,):
        raise ValueError(f"{field_name} pass reason cannot mix with blockers")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if getattr(value, name) is not True:
            raise ValueError(f"{name} must be True")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc


def _decimal_text(value: Decimal) -> str:
    return f"{value.quantize(SIX):f}"

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
RESEARCH_AGE_DECAY_RATE = Decimal("0.005000")
RESEARCH_AGE_DECAY_CAP_HOURS = Decimal("20.000000")
SOURCE_STALENESS_DECAY_RATE = Decimal("0.010000")
DECAY_STATUSES = ("current", "decayed")
CURRENT_REASON = "research_confidence_current"
REASON_CODES = (
    "research_age_confidence_decay",
    "source_staleness_confidence_decay",
    "market_move_confidence_decay",
    "confidence_decay_threshold_breached",
    CURRENT_REASON,
)
MANUAL_REFRESH_STEP = "manual_research_refresh_required"
MANUAL_OPTIONAL_STEP = "manual_review_optional"
HEX_CHARS = frozenset("0123456789abcdef")

__all__ = (
    "ProbabilityEventResearchConfidenceDecayReport",
    "build_probability_event_research_confidence_decay_report",
    "probability_event_research_confidence_decay_report_payload",
)


@dataclass(frozen=True)
class ProbabilityEventResearchConfidenceDecayReport:
    initial_confidence_probability: Decimal
    research_age_hours: Decimal
    source_staleness_hours: Decimal
    market_move_probability: Decimal
    decay_threshold_probability: Decimal
    decay_status: str
    decayed_confidence_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    public_payload: dict[str, Any]
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "initial_confidence_probability",
            "market_move_probability",
            "decay_threshold_probability",
            "decayed_confidence_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("research_age_hours", "source_staleness_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("decay_status", self.decay_status, DECAY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.decay_status, self.manual_next_step)
        _require_hard_flags("report", self)
        expected_payload = _payload_without_digest(self)
        expected_digest = _payload_digest(expected_payload)
        if self.payload_digest:
            _require_digest("payload_digest", self.payload_digest)
            if self.payload_digest != expected_digest:
                raise ValueError("payload_digest must match public_payload")
        if self.public_payload:
            _validate_public_payload(self.public_payload)
            supplied_payload_without_digest = dict(self.public_payload)
            supplied_payload_without_digest.pop("payload_digest", None)
            if supplied_payload_without_digest != expected_payload:
                raise ValueError("public_payload must match report fields")
        expected_probability = _decayed_confidence_probability(
            self.initial_confidence_probability,
            self.research_age_hours,
            self.source_staleness_hours,
            self.market_move_probability,
        )
        if self.decayed_confidence_probability != expected_probability:
            raise ValueError("decayed_confidence_probability must match inputs")
        expected_status = _decay_status(
            self.initial_confidence_probability,
            self.decayed_confidence_probability,
            self.decay_threshold_probability,
        )
        if self.decay_status != expected_status:
            raise ValueError("decay_status must match inputs")
        expected_reasons = _reason_codes(
            self.initial_confidence_probability,
            self.research_age_hours,
            self.source_staleness_hours,
            self.market_move_probability,
            self.decayed_confidence_probability,
            self.decay_threshold_probability,
        )
        if self.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match inputs")
        expected_step = _manual_next_step(self.decay_status)
        if self.manual_next_step != expected_step:
            raise ValueError("manual_next_step must match decay_status")
        object.__setattr__(self, "payload_digest", expected_digest)
        final_payload = dict(expected_payload)
        final_payload["payload_digest"] = expected_digest
        object.__setattr__(self, "public_payload", final_payload)


def build_probability_event_research_confidence_decay_report(
    *,
    initial_confidence_probability: Decimal,
    research_age_hours: Decimal,
    source_staleness_hours: Decimal,
    market_move_probability: Decimal,
    decay_threshold_probability: Decimal,
) -> ProbabilityEventResearchConfidenceDecayReport:
    initial_confidence_probability = _normalize_probability(
        "initial_confidence_probability",
        initial_confidence_probability,
    )
    research_age_hours = _normalize_nonnegative_decimal(
        "research_age_hours",
        research_age_hours,
    )
    source_staleness_hours = _normalize_nonnegative_decimal(
        "source_staleness_hours",
        source_staleness_hours,
    )
    market_move_probability = _normalize_probability(
        "market_move_probability",
        market_move_probability,
    )
    decay_threshold_probability = _normalize_probability(
        "decay_threshold_probability",
        decay_threshold_probability,
    )
    decayed_confidence_probability = _decayed_confidence_probability(
        initial_confidence_probability,
        research_age_hours,
        source_staleness_hours,
        market_move_probability,
    )
    decay_status = _decay_status(
        initial_confidence_probability,
        decayed_confidence_probability,
        decay_threshold_probability,
    )
    return ProbabilityEventResearchConfidenceDecayReport(
        initial_confidence_probability=initial_confidence_probability,
        research_age_hours=research_age_hours,
        source_staleness_hours=source_staleness_hours,
        market_move_probability=market_move_probability,
        decay_threshold_probability=decay_threshold_probability,
        decay_status=decay_status,
        decayed_confidence_probability=decayed_confidence_probability,
        reason_codes=_reason_codes(
            initial_confidence_probability,
            research_age_hours,
            source_staleness_hours,
            market_move_probability,
            decayed_confidence_probability,
            decay_threshold_probability,
        ),
        manual_next_step=_manual_next_step(decay_status),
        public_payload={},
        payload_digest="",
    )


def probability_event_research_confidence_decay_report_payload(
    report: ProbabilityEventResearchConfidenceDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ProbabilityEventResearchConfidenceDecayReport:
        _require_hard_flags("report", report)
        payload = dict(report.public_payload)
    elif type(report) is dict:
        payload = dict(report)
        _validate_public_payload(payload)
    else:
        raise ValueError(
            "report must be a ProbabilityEventResearchConfidenceDecayReport",
        )
    _validate_public_payload(payload)
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _decayed_confidence_probability(
    initial_confidence_probability: Decimal,
    research_age_hours: Decimal,
    source_staleness_hours: Decimal,
    market_move_probability: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        research_age_for_decay = research_age_hours
        if research_age_for_decay > RESEARCH_AGE_DECAY_CAP_HOURS:
            research_age_for_decay = RESEARCH_AGE_DECAY_CAP_HOURS
        total_decay = (
            research_age_for_decay * RESEARCH_AGE_DECAY_RATE
            + source_staleness_hours * SOURCE_STALENESS_DECAY_RATE
            + market_move_probability
        )
        return _clamp_probability(_quantize(initial_confidence_probability - total_decay))


def _decay_status(
    initial_confidence_probability: Decimal,
    decayed_confidence_probability: Decimal,
    decay_threshold_probability: Decimal,
) -> str:
    with localcontext(DECIMAL_CONTEXT):
        if _quantize(initial_confidence_probability - decayed_confidence_probability) > (
            decay_threshold_probability
        ):
            return "decayed"
    return "current"


def _reason_codes(
    initial_confidence_probability: Decimal,
    research_age_hours: Decimal,
    source_staleness_hours: Decimal,
    market_move_probability: Decimal,
    decayed_confidence_probability: Decimal,
    decay_threshold_probability: Decimal,
) -> tuple[str, ...]:
    with localcontext(DECIMAL_CONTEXT):
        confidence_loss = _quantize(
            initial_confidence_probability - decayed_confidence_probability,
        )
    if confidence_loss <= decay_threshold_probability:
        return (CURRENT_REASON,)
    reasons: list[str] = []
    if research_age_hours > ZERO:
        reasons.append("research_age_confidence_decay")
    if source_staleness_hours > ZERO:
        reasons.append("source_staleness_confidence_decay")
    if market_move_probability > ZERO:
        reasons.append("market_move_confidence_decay")
    reasons.append("confidence_decay_threshold_breached")
    return tuple(reasons)


def _manual_next_step(decay_status: str) -> str:
    if decay_status == "decayed":
        return MANUAL_REFRESH_STEP
    return MANUAL_OPTIONAL_STEP


def _payload_without_digest(
    report: ProbabilityEventResearchConfidenceDecayReport,
) -> dict[str, Any]:
    return {
        "initial_confidence_probability": _decimal_payload(
            report.initial_confidence_probability,
        ),
        "research_age_hours": _decimal_payload(report.research_age_hours),
        "source_staleness_hours": _decimal_payload(report.source_staleness_hours),
        "market_move_probability": _decimal_payload(report.market_move_probability),
        "decay_threshold_probability": _decimal_payload(
            report.decay_threshold_probability,
        ),
        "decay_status": report.decay_status,
        "decayed_confidence_probability": _decimal_payload(
            report.decayed_confidence_probability,
        ),
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_public_payload(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("public_payload must be a JSON object")
    _require_hard_flags("payload", _PayloadFlags(payload))
    _reject_public_numbers(payload)
    digest = payload.get("payload_digest")
    _require_digest("payload_digest", digest)
    digest_input = dict(payload)
    digest_input.pop("payload_digest", None)
    if digest != _payload_digest(digest_input):
        raise ValueError("payload_digest must match public_payload")


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    if value > ONE:
        return ONE.quantize(RATIO_QUANTUM)
    return value


def _decimal_payload(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_member("reason_code", reason_code, REASON_CODES)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be supported")


def _require_manual_next_step(decay_status: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError("manual_next_step must be supported")
    if value != _manual_next_step(decay_status):
        raise ValueError("manual_next_step must match decay_status")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex string")


def _reject_public_numbers(value: object) -> None:
    if type(value) in (Decimal, int, float):
        raise ValueError("public_payload values must not be numeric")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numbers(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numbers(item)

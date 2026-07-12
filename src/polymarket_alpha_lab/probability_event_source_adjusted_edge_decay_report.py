from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

_SOURCE_QUALITY_WATCH_MIN = Decimal("0.600000")
_SOURCE_QUALITY_BLOCK_MIN = Decimal("0.400000")
_SOURCE_AGE_STALE_HOURS = Decimal("24.000000")
_SOURCE_AGE_EXPIRED_HOURS = Decimal("48.000000")
_MARKET_MOVE_WATCH_MIN = Decimal("0.050000")
_MARKET_MOVE_BLOCK_MIN = Decimal("0.100000")
_DECAY_PENALTY_WATCH_MIN = Decimal("0.050000")
_DECAY_PENALTY_BLOCK_MIN = Decimal("0.150000")

_STATUSES = frozenset(("ready_for_manual_review", "watch", "blocked"))
_MANUAL_NEXT_STEPS = frozenset(
    (
        "review_source_adjusted_edge",
        "refresh_source_and_recompute_edge",
        "do_not_trade_refresh_primary_source",
    ),
)
_REASON_CODE_SEQUENCE = (
    "source_adjusted_edge_ready",
    "source_adjusted_edge_nonpositive",
    "source_quality_probability_watch",
    "source_quality_probability_block",
    "source_age_hours_stale",
    "source_age_hours_expired",
    "market_move_probability_watch",
    "market_move_probability_block",
    "decay_penalty_probability_watch",
    "decay_penalty_probability_block",
)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))


@dataclass(frozen=True)
class ProbabilityEventSourceAdjustedEdgeDecayReport:
    raw_edge_probability: Decimal
    source_age_hours: Decimal
    source_quality_probability: Decimal
    market_move_probability: Decimal
    decay_penalty_probability: Decimal
    edge_decay_status: str
    source_adjusted_edge_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventSourceAdjustedEdgeDecayReport:
            raise ValueError(
                "report must be a ProbabilityEventSourceAdjustedEdgeDecayReport",
            )
        object.__setattr__(
            self,
            "raw_edge_probability",
            _require_signed_probability(
                "raw_edge_probability",
                self.raw_edge_probability,
            ),
        )
        object.__setattr__(
            self,
            "source_age_hours",
            _require_nonnegative_decimal("source_age_hours", self.source_age_hours),
        )
        for field_name in (
            "source_quality_probability",
            "market_move_probability",
            "decay_penalty_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_adjusted_edge_probability",
            _require_finite_decimal(
                "source_adjusted_edge_probability",
                self.source_adjusted_edge_probability,
            ),
        )
        _require_status("edge_decay_status", self.edge_decay_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        derived_digest = _payload_digest(_payload_items(self, payload_digest=""))
        object.__setattr__(
            self,
            "payload_digest",
            _resolve_digest(self.payload_digest, derived_digest),
        )

    @property
    def public_payload(self) -> dict[str, Any]:
        return probability_event_source_adjusted_edge_decay_report_payload(self)


def build_probability_event_source_adjusted_edge_decay_report(
    *,
    raw_edge_probability: Decimal,
    source_age_hours: Decimal,
    source_quality_probability: Decimal,
    market_move_probability: Decimal,
    decay_penalty_probability: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventSourceAdjustedEdgeDecayReport:
    raw_edge = _require_signed_probability("raw_edge_probability", raw_edge_probability)
    source_age = _require_nonnegative_decimal("source_age_hours", source_age_hours)
    source_quality = _require_probability_decimal(
        "source_quality_probability",
        source_quality_probability,
    )
    market_move = _require_probability_decimal(
        "market_move_probability",
        market_move_probability,
    )
    decay_penalty = _require_probability_decimal(
        "decay_penalty_probability",
        decay_penalty_probability,
    )
    flags = _PhaseFlags(
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )
    _require_hard_flags("builder", flags)

    adjusted_edge = _source_adjusted_edge_probability(
        raw_edge_probability=raw_edge,
        source_quality_probability=source_quality,
        market_move_probability=market_move,
        decay_penalty_probability=decay_penalty,
    )
    reason_codes = _reason_codes_for(
        source_adjusted_edge_probability=adjusted_edge,
        source_age_hours=source_age,
        source_quality_probability=source_quality,
        market_move_probability=market_move,
        decay_penalty_probability=decay_penalty,
    )
    status = _status_for(reason_codes)
    return ProbabilityEventSourceAdjustedEdgeDecayReport(
        raw_edge_probability=raw_edge,
        source_age_hours=source_age,
        source_quality_probability=source_quality,
        market_move_probability=market_move,
        decay_penalty_probability=decay_penalty,
        edge_decay_status=status,
        source_adjusted_edge_probability=adjusted_edge,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step_for(status),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_source_adjusted_edge_decay_report_payload(
    report: ProbabilityEventSourceAdjustedEdgeDecayReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventSourceAdjustedEdgeDecayReport:
        raise ValueError(
            "report must be a ProbabilityEventSourceAdjustedEdgeDecayReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    return _payload_items(report, payload_digest=report.payload_digest)


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _source_adjusted_edge_probability(
    *,
    raw_edge_probability: Decimal,
    source_quality_probability: Decimal,
    market_move_probability: Decimal,
    decay_penalty_probability: Decimal,
) -> Decimal:
    return _quantize(
        (raw_edge_probability * source_quality_probability)
        - market_move_probability
        - decay_penalty_probability,
    )


def _reason_codes_for(
    *,
    source_adjusted_edge_probability: Decimal,
    source_age_hours: Decimal,
    source_quality_probability: Decimal,
    market_move_probability: Decimal,
    decay_penalty_probability: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_adjusted_edge_probability <= _ZERO:
        reason_codes.append("source_adjusted_edge_nonpositive")
    if source_quality_probability < _SOURCE_QUALITY_BLOCK_MIN:
        reason_codes.append("source_quality_probability_block")
    elif source_quality_probability < _SOURCE_QUALITY_WATCH_MIN:
        reason_codes.append("source_quality_probability_watch")
    if source_age_hours >= _SOURCE_AGE_EXPIRED_HOURS:
        reason_codes.append("source_age_hours_expired")
    elif source_age_hours >= _SOURCE_AGE_STALE_HOURS:
        reason_codes.append("source_age_hours_stale")
    if market_move_probability >= _MARKET_MOVE_BLOCK_MIN:
        reason_codes.append("market_move_probability_block")
    elif market_move_probability >= _MARKET_MOVE_WATCH_MIN:
        reason_codes.append("market_move_probability_watch")
    if decay_penalty_probability >= _DECAY_PENALTY_BLOCK_MIN:
        reason_codes.append("decay_penalty_probability_block")
    elif decay_penalty_probability >= _DECAY_PENALTY_WATCH_MIN:
        reason_codes.append("decay_penalty_probability_watch")
    if not reason_codes:
        reason_codes.append("source_adjusted_edge_ready")
    return _normalize_reason_codes(reason_codes)


def _status_for(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") or reason_code.endswith("_expired") for reason_code in reason_codes):
        return "blocked"
    if reason_codes == ("source_adjusted_edge_ready",):
        return "ready_for_manual_review"
    return "watch"


def _manual_next_step_for(status: str) -> str:
    if status == "blocked":
        return "do_not_trade_refresh_primary_source"
    if status == "watch":
        return "refresh_source_and_recompute_edge"
    return "review_source_adjusted_edge"


def _validate_report_consistency(
    report: ProbabilityEventSourceAdjustedEdgeDecayReport,
) -> None:
    expected_adjusted_edge = _source_adjusted_edge_probability(
        raw_edge_probability=report.raw_edge_probability,
        source_quality_probability=report.source_quality_probability,
        market_move_probability=report.market_move_probability,
        decay_penalty_probability=report.decay_penalty_probability,
    )
    if report.source_adjusted_edge_probability != expected_adjusted_edge:
        raise ValueError(
            "source_adjusted_edge_probability must match report inputs",
        )
    expected_reasons = _reason_codes_for(
        source_adjusted_edge_probability=expected_adjusted_edge,
        source_age_hours=report.source_age_hours,
        source_quality_probability=report.source_quality_probability,
        market_move_probability=report.market_move_probability,
        decay_penalty_probability=report.decay_penalty_probability,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report inputs")
    expected_status = _status_for(expected_reasons)
    if report.edge_decay_status != expected_status:
        raise ValueError("edge_decay_status must match report inputs")
    expected_next_step = _manual_next_step_for(expected_status)
    if report.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match report inputs")
    if report.payload_digest:
        expected_digest = _payload_digest(_payload_items(report, payload_digest=""))
        if report.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a supported manual step")


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_signed_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < -_ONE or normalized > _ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain supported values")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _resolve_digest(provided: str, derived: str) -> str:
    if provided == "":
        return derived
    if type(provided) is not str or len(provided) != 64:
        raise ValueError("payload_digest must be a sha256 hex string")
    for character in provided:
        if character not in "0123456789abcdef":
            raise ValueError("payload_digest must be a sha256 hex string")
    if provided != derived:
        raise ValueError("payload_digest must match public payload")
    return provided


def _payload_items(
    report: ProbabilityEventSourceAdjustedEdgeDecayReport,
    *,
    payload_digest: str,
) -> dict[str, Any]:
    return {
        "raw_edge_probability": _decimal_text(report.raw_edge_probability),
        "source_age_hours": _decimal_text(report.source_age_hours),
        "source_quality_probability": _decimal_text(
            report.source_quality_probability,
        ),
        "market_move_probability": _decimal_text(report.market_move_probability),
        "decay_penalty_probability": _decimal_text(
            report.decay_penalty_probability,
        ),
        "source_adjusted_edge_probability": _decimal_text(
            report.source_adjusted_edge_probability,
        ),
        "edge_decay_status": report.edge_decay_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "payload_digest": payload_digest,
    }


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(_QUANT, rounding=ROUND_HALF_UP), "f")


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_default(value: object) -> object:
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"unsupported public payload value: {value!r}")


__all__ = (
    "ProbabilityEventSourceAdjustedEdgeDecayReport",
    "build_probability_event_source_adjusted_edge_decay_report",
    "probability_event_source_adjusted_edge_decay_report_payload",
)
